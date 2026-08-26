"""
TQA-MS — Celery টাস্ক (core/tasks.py)
১) ক্লাস শুরুর ৫ মিনিট আগে অভিভাবকের WhatsApp রিমাইন্ডার (অটো)
২) WhatsApp পাঠানো — Twilio বা Meta Cloud API (Python সংস্করণ)
৩) মাসের ১ তারিখে সবার DueMonth অটো তৈরি
"""
import os
import requests as http
from datetime import date, datetime, timedelta
from celery import shared_task
from django.db import IntegrityError
from django.utils import timezone


# ─────────────────── WhatsApp পাঠানো (Twilio / Meta) ───────────────────
def _clean(phone):
    return "".join(ch for ch in str(phone) if ch.isdigit())


# Celery ছাড়া এই কলগুলো request-এর মূল প্রসেসেই (synchronous) চলে — মাত্র ২টা
# gunicorn worker থাকায় WhatsApp API ধীর/আটকে গেলে একটা worker দীর্ঘক্ষণ বন্দী হয়ে
# বাকি সব ব্যবহারকারীর (লগইন/ক্লাস লোড) জন্য সার্ভার এলোমেলো ধীর হয়ে যেতে পারে —
# তাই timeout ছোট রাখা হলো (২০s → ৮s, স্বাভাবিক API রেসপন্সের জন্য যথেষ্ট)
_WA_TIMEOUT = 8


def _send_twilio(to, text):
    sid, token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]
    r = http.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, token),
        data={"From": f"whatsapp:{os.environ['TWILIO_WHATSAPP_FROM']}",
              "To": f"whatsapp:+{_clean(to)}", "Body": text}, timeout=_WA_TIMEOUT)
    r.raise_for_status()
    return r.json().get("sid", "")


def _send_meta(to, text):
    r = http.post(
        f"https://graph.facebook.com/v19.0/{os.environ['META_PHONE_NUMBER_ID']}/messages",
        headers={"Authorization": f"Bearer {os.environ['META_ACCESS_TOKEN']}"},
        json={"messaging_product": "whatsapp", "to": _clean(to),
              "type": "text", "text": {"body": text}}, timeout=_WA_TIMEOUT)
    r.raise_for_status()
    return (r.json().get("messages") or [{}])[0].get("id", "")


# Celery ব্যবহার হবে কিনা (Render free plan এ worker নেই → False রাখুন)
USE_CELERY = os.environ.get("USE_CELERY", "False").lower() in ("true", "1", "yes")


def send_whatsapp_now(msg_id, raise_on_fail=False):
    """একটি WaMessage এখনই পাঠানো (synchronous — Celery লাগে না)"""
    from .models import WaMessage
    msg = WaMessage.objects.get(pk=msg_id)
    msg.status = "sending"
    msg.save(update_fields=["status"])
    try:
        provider = os.environ.get("WHATSAPP_PROVIDER", "meta").lower()
        ref = _send_twilio(msg.phone, msg.text) if provider == "twilio" else _send_meta(msg.phone, msg.text)
        msg.status, msg.provider_ref = "sent", ref
        msg.save(update_fields=["status", "provider_ref"])
    except Exception as exc:
        msg.status = "failed"
        msg.save(update_fields=["status"])
        if raise_on_fail:
            raise exc


def dispatch_whatsapp(msg_id):
    """Celery থাকলে queue তে দেয়, না থাকলে সরাসরি পাঠায়"""
    if USE_CELERY:
        send_whatsapp.delay(msg_id)
    else:
        send_whatsapp_now(msg_id)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_whatsapp(self, msg_id):
    """Celery ভার্সন — ব্যর্থ হলে ৩ বার রিট্রাই"""
    try:
        send_whatsapp_now(msg_id, raise_on_fail=True)
    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────── ক্লাস-শুরুর রিমাইন্ডার (cron প্রতি ~১৫ মিনিটে চালান) ───────────────────
# আগে জানালা ছিল ৫ মিনিট আর cron চলত প্রতি মিনিটে — কিন্তু এতে ডেটাবেস (Neon) কখনো
# অলস হয়ে "ঘুমাতে" পারত না, ফলে ফ্রি compute-quota কয়েক দিনেই শেষ হয়ে যেত (লগইন 500)।
# এখন cron কম ঘন ঘন চলার কথা (~১৫ মিনিট পরপর) — তাই জানালা ১৮ মিনিট রাখা হলো (কিছুটা
# মার্জিনসহ) যাতে কোনো ক্লাস রিমাইন্ডার ছাড়া বাদ না পড়ে। বার্তায় প্রকৃত বাকি-মিনিট দেখানো হয়।
REMINDER_WINDOW_MINUTES = 18


@shared_task
def queue_class_reminders():
    from .models import ClassSession, WaMessage, Notification
    now = timezone.localtime()
    today = now.date()
    sessions = ClassSession.objects.filter(date=today, status="upcoming", reminder_sent=False)
    for s in sessions:
        start = timezone.make_aware(datetime.combine(today, s.time))
        mins_left = int((start - now).total_seconds() // 60)
        if not (0 <= mins_left <= REMINDER_WINDOW_MINUTES):
            continue  # জানালার বাইরে
        mins_bn = str(mins_left).translate(BN_DIGITS)
        students = list(s.students.all())
        # ইন-অ্যাপ নোটিফিকেশন
        n = Notification.objects.create(
            text=f"⏰ {s.course.name} ক্লাস {s.time.strftime('%H:%M')}-এ শুরু হচ্ছে (আর {mins_bn} মিনিটের মধ্যে)! "
                 f"ড্যাশবোর্ড থেকে জয়েন করুন।")
        n.recipients.set(students + ([s.teacher] if s.teacher else []))
        # অভিভাবকের WhatsApp
        for st in students:
            if not st.phone:
                continue
            text = (f"আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম {st.guardian or 'অভিভাবক'}, "
                    f"{st.name_bn}-এর \"{s.course.name}\" ক্লাস আজ {s.time.strftime('%H:%M')}-এ "
                    f"(আর {mins_bn} মিনিটের মধ্যে) শুরু হচ্ছে ইনশাআল্লাহ। অনুগ্রহ করে ক্লাসে যুক্ত হতে সহায়তা করুন। "
                    f"জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি")
            m = WaMessage.objects.create(to_name=st.guardian or st.name_bn, student=st,
                                         phone=st.phone, text=text, reason="reminder")
            dispatch_whatsapp(m.id)
        s.reminder_sent = True
        s.save(update_fields=["reminder_sent"])


# ─────────────────── মাসিক বকেয়া অটো-জেনারেশন (১ তারিখ) ───────────────────
BN_MONTHS = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
             "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


@shared_task
def generate_monthly_dues(roles=None):
    """চলতি মাসের বকেয়া তৈরি (idempotent) — কতগুলো নতুন তৈরি হলো তা ফেরত দেয়।
    roles না দিলে ডিফল্টে student+teacher দুটোই (cron/হিসাব-নিকাশের বাটন);
    "স্টুডেন্ট পেমেন্ট" পেজের বাটন শুধু roles=["student"] দিয়ে কল করে।"""
    from django.db.models import Sum

    from .models import (User, DueMonth, FeePayment, TeacherPayment,
                         LeaveRequest)
    # date.today() সার্ভারের (UTC) তারিখ দেয়, বাংলাদেশ সময়ের নয় — মাসের শুরুর
    # দিকে মধ্যরাত-থেকে-ভোর৬টার মধ্যে চললে ভুল মাসও ধরে ফেলতে পারত
    t = timezone.localtime().date()
    label = f"{BN_MONTHS[t.month - 1]} {str(t.year).translate(BN_DIGITS)}"

    # ⚠️ যাঁরা এই মাসের টাকা আগেই দিয়ে ফেলেছেন তাঁদের বকেয়া বানানো যাবে না।
    # অনেক অভিভাবক ১-২ মাসের ফি অগ্রিম দিয়ে দেন — আগে সেটা দেখা হতো না,
    # তাই পরের মাসের ৫ তারিখে তাঁদের নামেও বকেয়া বসে যেত এবং রিমাইন্ডারের
    # তালিকায় চলে আসতেন, যদিও টাকা আগেই দেওয়া।
    paid_students = set(
        FeePayment.objects.filter(month_label=label, status="verified")
        .values_list("student_id", flat=True)
    )
    # উস্তাদের বেলায় পূর্ণ বেতন পেলে তবেই বাদ — আংশিক দিলে বকেয়া থাকা উচিত
    # (perform_destroy/verify-এর নিয়মের সাথে মিলিয়ে)
    salary_of = dict(
        User.objects.filter(role="teacher").values_list("id", "monthly_salary")
    )
    paid_teachers = {
        row["teacher_id"]
        for row in TeacherPayment.objects.filter(month_label=label)
        .values("teacher_id")
        .annotate(total=Sum("amount"))
        if (row["total"] or 0) >= (salary_of.get(row["teacher_id"]) or 0) > 0
    }

    # ⚠️ মঞ্জুর হওয়া ছুটি পুরো মাসটা ঢেকে রাখলে সে মাসের বকেয়া তৈরি হয় না।
    # শর্তটা ইচ্ছাকৃতভাবে কড়া — ছুটি মাসের ১ তারিখের আগে (বা সেদিনই) শুরু
    # হয়ে শেষ তারিখের পরে (বা সেদিনই) শেষ হতে হবে। কয়েক দিনের অসুস্থতার
    # ছুটিতে পুরো মাসের ফি মাফ হয়ে যাওয়াটা ঠিক হতো না।
    import calendar

    first = t.replace(day=1)
    last = t.replace(day=calendar.monthrange(t.year, t.month)[1])
    on_leave = set(
        LeaveRequest.objects.filter(
            status="approved", from_date__lte=first, to_date__gte=last
        ).values_list("applicant_id", flat=True)
    )

    created = 0
    for u in User.objects.filter(role__in=(roles or ["student", "teacher"]), is_active=True):
        # ⚠️ যে মাসে ভর্তি হয়েছেন, সে মাসের বকেয়া বসে না — পরিচালকের
        # সিদ্ধান্ত। আগে মাসের ২৫ তারিখে ভর্তি হলেও ওই মাসের পুরো ফি
        # বকেয়া হয়ে যেত। ভর্তি ফি এর বাইরে, আগের মতোই আলাদা।
        # ⚠️ কেবল শিক্ষার্থীর জন্য — উস্তাদের বেতনের হিসাব ছোঁয়া হয়নি।
        # ⚠️ আগে তৈরি হয়ে যাওয়া কোনো বকেয়া এতে মুছে যায় না; এটি কেবল
        # এরপর থেকে নতুন বকেয়া বসানোর সময় খাটে।
        if (u.role == "student" and u.date_joined
                and timezone.localtime(u.date_joined).date() >= first):
            continue
        if u.role == "student" and u.id in paid_students:
            continue
        if u.role == "teacher" and u.id in paid_teachers:
            continue
        if u.id in on_leave:
            continue
        # মওকুফ করা মাস আবার বকেয়া হিসেবে ফিরে আসে না — get_or_create
        # পুরনো (মওকুফ চিহ্নিত) সারিটাই পায়, নতুন বানায় না
        _, is_new = DueMonth.objects.get_or_create(user=u, month_label=label)
        if is_new:
            created += 1
    return created


# ─────────────────── সাপ্তাহিক রুটিন → সামনের সপ্তাহের ক্লাস অটো তৈরি ───────────────────
def generate_for_routine(r):
    """একটি রুটিনের আগামী ৭ দিনের ক্লাস নিশ্চিত করা (idempotent) — রুটিন যোগ করলেই ডাকা হয়।
    কতটি নতুন ক্লাস তৈরি হলো তা ফেরত দেয়।"""
    from .models import ClassSession
    if not r.teacher_id or not r.course_id:
        return 0  # উস্তাদ/কোর্স ছাড়া ক্লাস তৈরি সম্ভব নয়
    # date.today() সার্ভারের (UTC) তারিখ দেয়, বাংলাদেশ সময়ের নয় — মধ্যরাত থেকে
    # ভোর ৬টার মধ্যে cron চললে এটা "গতকাল" ধরে ক্লাস তৈরি করত (UTC তখনও আগের
    # দিন), ফলে "আজকের ক্লাস" ভুল তারিখে তৈরি হয়ে টিচার/স্টুডেন্টের পোর্টালে দেখাত না
    today = timezone.localtime().date()
    created = 0
    for off in range(7):
        d = today + timedelta(days=off)
        if d.weekday() not in _js_to_py(r.days or []):
            continue
        if not ClassSession.objects.filter(routine=r, date=d).exists():
            try:
                s = ClassSession.objects.create(
                    routine=r, course=r.course, teacher=r.teacher, date=d, time=r.time,
                    duration_min=r.duration_min, zoom_link=r.zoom_link,
                    zoom_link_2=r.zoom_link_2, kind="regular")
                s.students.set(r.students.all())
                created += 1
            except IntegrityError:
                # রেস কন্ডিশন — দৈনিক cron আর ম্যানুয়াল "সব রুটিনের ক্লাস তৈরি
                # করুন" বাটন একইসাথে চললে দুটোই "নেই" দেখে ফেলতে পারত; DB-এর
                # unique constraint একটাকে আটকে দেয় — এখানে চুপচাপ স্কিপ করাই
                # ঠিক (অন্য রিকোয়েস্টটা ততক্ষণে সফলভাবে তৈরি করে ফেলেছে)
                continue
    return created


@shared_task
def generate_routine_sessions():
    """প্রতিটি সক্রিয় রুটিনের আগামী ৭ দিনের ক্লাস নিশ্চিত করা (দৈনিক ক্রন + ম্যানুয়াল বাটন)।
    একটি রুটিনে সমস্যা হলেও বাকিগুলো যাতে থেমে না যায় — প্রতিটি আলাদা try তে। মোট নতুন ক্লাস ফেরত।"""
    from .models import Routine
    total = 0
    for r in Routine.objects.filter(is_active=True):
        try:
            total += generate_for_routine(r) or 0
        except Exception:
            continue
    return total


def _js_to_py(js_days):
    """JS getDay() (০=রবি) → Python weekday() (০=সোম)"""
    return {(d - 1) % 7 for d in js_days}


# ─────────────────── পুরনো ক্লাস-শিডিউল ৬০ দিন পর মোছা (হাজিরা কখনো মোছা হয় না) ───────────────────
@shared_task
def cleanup_old_classes():
    """৬০ দিনের বেশি পুরনো ClassSession মুছে ফেলা (প্রতিদিন QA Daily-এর সাথে চলে)।
    Attendance.session-এ on_delete=SET_NULL থাকায় হাজিরার রেকর্ড কখনো মোছে না —
    course_name/teacher_name/class_date আগে থেকেই আলাদাভাবে সংরক্ষিত (migration 0008),
    তাই মাসিক হাজিরা রিপোর্ট সবসময় সম্পূর্ণ থাকে। কতগুলো ClassSession মুছল তা ফেরত দেয়।"""
    from .models import ClassSession
    cutoff = timezone.localtime().date() - timedelta(days=60)
    deleted, _ = ClassSession.objects.filter(date__lt=cutoff).delete()
    return deleted
