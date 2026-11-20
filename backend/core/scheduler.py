"""TQA-MS — সার্ভারের নিজের পাহারাদার (core/scheduler.py)

রোজের ক্লাস তৈরি আর মাসিক বকেয়া আগে চলত কেবল cron-job.org (বাইরের ফ্রি
সার্ভিস) ডাকলে। সেটা বন্ধ হলে কেউ টের পেতেন না — ৭ দিনের মধ্যে সবার
ক্লাস উধাও হতো। আর মাসের ১ তারিখের একমাত্র ডাকটি ব্যর্থ হলে সে মাসের
বকেয়া কখনোই তৈরি হতো না (কাজটি কেবল চলতি মাস দেখে, পরে আর ধরে না)।

এখন সার্ভার নিজেই প্রতি মিনিটে দেখে কোন কাজ "বাকি" — সময় হয়ে গেছে অথচ
এই সময়কালের জন্য এখনো হয়নি — আর থাকলে চালায়। ব্যর্থ হলে পরের মিনিটে
আবার চেষ্টা। cron-job.org ব্যাকআপ হিসেবে থাকে; দুজনই run_job() দিয়ে ঢোকে,
তাই কোনো কাজ দুবার হয় না।
"""
import logging
import os
import threading
import time
from datetime import timedelta

from django.db import connection
from django.db.models import Q
from django.utils import timezone

log = logging.getLogger("tqa.scheduler")

# প্রসেস মাঝপথে মরে গেলে (ডিপ্লয়/রিস্টার্ট) দাবিটা এতক্ষণ পর বাসি ধরা হয়।
# কাজগুলো কয়েক সেকেন্ডের, তাই ৩০ মিনিট যথেষ্ট উদার।
STALE_CLAIM = timedelta(minutes=30)
TICK_SECONDS = 60
# রাত ২টা — মধ্যরাত পেরোনো ক্লাস শেষ হওয়ার সময় দিতে (cron-এর আগের সময়ই)
DAILY_AT = (2, 0)
# মাসের ১ তারিখ ভোর ৫টা (cron-এর আগের সময়ই); এর পরে মাসের যেকোনো দিনে ধরে নেয়
MONTHLY_AT = (5, 0)


def run_job(name, key, fn, trigger):
    """`key` সময়কালের জন্য কাজটি ঠিক একবার চালায়।

    ফেরত (status, result):
      ("ran", fn-এর ফল)  — এইমাত্র চালানো হলো
      ("done", None)     — এই সময়কালের জন্য আগেই হয়ে গেছে
      ("busy", None)     — অন্য কেউ এই মুহূর্তে চালাচ্ছে
    fn() ব্যর্থ হলে দাবি ছেড়ে দেয় (পরের বার আবার চেষ্টা হবে), ত্রুটি লিখে
    রাখে এবং exception আবার ছুড়ে দেয়।
    """
    from .models import ScheduledJob

    ScheduledJob.objects.get_or_create(name=name)
    now = timezone.now()
    # ⚠️ দাবিটা একটিমাত্র UPDATE। দুজন একই মুহূর্তে এলে ডাটাবেস সারিটি লক
    # করে; দ্বিতীয়জন প্রথমজনের পরে শর্তটি নতুন করে মেলায় এবং ০ সারি পায়।
    # তাই পাহারাদারের সব worker আর cron-job.org একসাথে ডাকলেও কাজ একবারই।
    won = (
        ScheduledJob.objects.filter(name=name)
        .exclude(done_key=key)
        .filter(~Q(claimed_key=key) | Q(claimed_at__lt=now - STALE_CLAIM))
        .update(claimed_key=key, claimed_at=now)
    )
    if not won:
        done = ScheduledJob.objects.filter(name=name, done_key=key).exists()
        return ("done" if done else "busy"), None
    try:
        result = fn()
    except Exception as exc:
        ScheduledJob.objects.filter(name=name, claimed_key=key).update(
            claimed_key="",
            claimed_at=None,
            last_error=f"{type(exc).__name__}: {exc}"[:2000],
            last_error_at=timezone.now(),
        )
        log.exception("scheduled job %s (%s) failed via %s", name, key, trigger)
        raise
    ScheduledJob.objects.filter(name=name).update(
        done_key=key,
        claimed_key="",
        claimed_at=None,
        last_run_at=timezone.now(),
        last_trigger=trigger,
        last_result=result if isinstance(result, dict) else {"result": result},
        last_error="",
        last_error_at=None,
    )
    log.info("scheduled job %s (%s) done via %s: %s", name, key, trigger, result)
    return "ran", result


def daily_work():
    from .tasks import (auto_postpone_missed_classes, cleanup_old_classes,
                        generate_routine_sessions)
    return {
        "created": generate_routine_sessions(),
        "auto_postponed": auto_postpone_missed_classes(),
        "deleted_old_classes": cleanup_old_classes(),
    }


def monthly_work():
    from .tasks import generate_monthly_dues
    return {"created": generate_monthly_dues()}


def daily_key(now_bd):
    return now_bd.date().isoformat()


def monthly_key(now_bd):
    return now_bd.strftime("%Y-%m")


def due_jobs(now_bd):
    """এই মুহূর্তে যে কাজগুলোর সময় হয়েছে — [(name, key, fn)]।

    ⚠️ মাসিক কাজ ১ তারিখের পরে মাসের যেকোনো দিনেই "বাকি" ধরা হয় — ১ তারিখে
    ব্যর্থ হলে বা সার্ভার বন্ধ থাকলে পরের দিনগুলোতে নিজেই ধরে নেয়। তবু
    মাসে ঠিক একবারই চলে (key = মাস), তাই মাঝমাসে ভর্তি হওয়া বা পরে টাকা
    দেওয়া কারও হিসাব বদলায় না।
    """
    hm = (now_bd.hour, now_bd.minute)
    jobs = []
    if hm >= DAILY_AT:
        jobs.append(("daily", daily_key(now_bd), daily_work))
    if now_bd.day > 1 or hm >= MONTHLY_AT:
        jobs.append(("monthly", monthly_key(now_bd), monthly_work))
    return jobs


def _expected(name, now_bd):
    """এই মুহূর্তে কোন সময়কালের কাজ হয়ে থাকার কথা, আর সেটা কখন থেকে বাকি।
    যেমন রাত ১টায় দৈনিকের প্রত্যাশা গতকালের (আজকেরটার সময় হয়নি)।"""
    if name == "daily":
        due = now_bd.replace(hour=DAILY_AT[0], minute=DAILY_AT[1], second=0, microsecond=0)
        if now_bd < due:
            due -= timedelta(days=1)
        return daily_key(due), due
    due = now_bd.replace(day=1, hour=MONTHLY_AT[0], minute=MONTHLY_AT[1],
                         second=0, microsecond=0)
    if now_bd < due:
        due = (due - timedelta(days=1)).replace(day=1)  # আগের মাসের ১ তারিখ
    return monthly_key(due), due


# এর বেশি দেরি হলে "late" — পাহারাদার প্রতি মিনিটে দেখে, তাই ১৫ মিনিট উদার
LATE_AFTER_MIN = 15


def job_status(now=None):
    """পরিচালকের স্বাস্থ্য কার্ডের জন্য — প্রতিটি কাজের অবস্থা।
    state: ok (হয়ে গেছে) · pending (সবে সময় হলো) · error (ব্যর্থ, আবার
    চেষ্টা চলছে) · late (অনেকক্ষণ বাকি — পাহারাদার সম্ভবত চলছে না)"""
    from .models import ScheduledJob

    now_bd = timezone.localtime(now) if now else timezone.localtime()
    rows = {j.name: j for j in ScheduledJob.objects.all()}
    out = []
    for name in ("daily", "monthly"):
        key, due = _expected(name, now_bd)
        j = rows.get(name)
        done = bool(j and j.done_key == key)
        overdue = 0 if done else int((now_bd - due).total_seconds() // 60)
        if done:
            state = "ok"
        elif j and j.last_error:
            state = "error"
        else:
            state = "pending" if overdue <= LATE_AFTER_MIN else "late"
        out.append({
            "name": name,
            "state": state,
            "expected_key": key,
            "overdue_minutes": overdue,
            "done_key": j.done_key if j else "",
            "last_run_at": j.last_run_at if j else None,
            "last_trigger": j.last_trigger if j else "",
            "last_result": j.last_result if j else {},
            "last_error": j.last_error if j else "",
            "last_error_at": j.last_error_at if j else None,
        })
    return out


# এই প্রসেসে কোন কাজ কোন সময়কালের জন্য হয়ে গেছে বলে জানা — তাহলে প্রতি
# মিনিটে ডাটাবেসে যেতে হয় না (Neon-কে অকারণে জাগিয়ে রাখে না)
_known_done = {}


def run_due_jobs(trigger="scheduler", now=None):
    now_bd = timezone.localtime(now) if now else timezone.localtime()
    for name, key, fn in due_jobs(now_bd):
        if _known_done.get(name) == key:
            continue
        try:
            status, _ = run_job(name, key, fn, trigger)
        except Exception:
            continue  # ত্রুটি লেখা হয়ে গেছে; পরের টিকে আবার চেষ্টা
        if status in ("ran", "done"):
            _known_done[name] = key


_started = False
_start_lock = threading.Lock()


def start():
    """প্রতিটি ওয়েব worker-এ একবার — wsgi.py থেকে ডাকা হয়।

    ⚠️ wsgi.py থেকে, AppConfig.ready() থেকে নয়: Render-এর বিল্ডে যে
    migrate/collectstatic চলে সেখানেও ready() চলে — তখন চালু হলে বিল্ডের
    মাঝেই কাজ শুরু করে দিত।
    চালু হয় কেবল Render-এ (সেখানে RENDER=true নিজে থেকেই থাকে); অন্য
    কোথাও চালাতে TQA_SCHEDULER=1, Render-এ বন্ধ রাখতে TQA_SCHEDULER=0।
    """
    global _started
    default = "1" if os.environ.get("RENDER") else "0"
    if os.environ.get("TQA_SCHEDULER", default) != "1":
        return
    with _start_lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_loop, name="tqa-scheduler", daemon=True).start()
    log.info("scheduler started")


def _loop():
    time.sleep(20)  # worker পুরোপুরি চালু হওয়ার সময়
    while True:
        try:
            run_due_jobs("scheduler")
        except Exception:
            log.exception("scheduler tick failed")
        finally:
            # দীর্ঘজীবী থ্রেড — প্রতি টিকে সংযোগ বন্ধ। নইলে ডাটাবেস নিষ্ক্রিয়
            # সংযোগ কেটে দেওয়ার পর পুরনো সংযোগে পরের কোয়েরি ব্যর্থ হতো।
            connection.close()
        time.sleep(TICK_SECONDS)
