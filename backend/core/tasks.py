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
from django.utils import timezone


# ─────────────────── WhatsApp পাঠানো (Twilio / Meta) ───────────────────
def _clean(phone):
    return "".join(ch for ch in str(phone) if ch.isdigit())


def _send_twilio(to, text):
    sid, token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]
    r = http.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, token),
        data={"From": f"whatsapp:{os.environ['TWILIO_WHATSAPP_FROM']}",
              "To": f"whatsapp:+{_clean(to)}", "Body": text}, timeout=20)
    r.raise_for_status()
    return r.json().get("sid", "")


def _send_meta(to, text):
    r = http.post(
        f"https://graph.facebook.com/v19.0/{os.environ['META_PHONE_NUMBER_ID']}/messages",
        headers={"Authorization": f"Bearer {os.environ['META_ACCESS_TOKEN']}"},
        json={"messaging_product": "whatsapp", "to": _clean(to),
              "type": "text", "text": {"body": text}}, timeout=20)
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


# ─────────────────── ৫-মিনিট রিমাইন্ডার (প্রতি মিনিটে beat চালায়) ───────────────────
@shared_task
def queue_class_reminders():
    from .models import ClassSession, WaMessage, Notification
    now = timezone.localtime()
    today = now.date()
    sessions = ClassSession.objects.filter(date=today, status="upcoming", reminder_sent=False)
    for s in sessions:
        start = timezone.make_aware(datetime.combine(today, s.time))
        if not (timedelta(0) <= start - now <= timedelta(minutes=5)):
            continue  # ঠিক ৫ মিনিটের জানালায় নয়
        students = list(s.students.all())
        # ইন-অ্যাপ নোটিফিকেশন
        n = Notification.objects.create(
            text=f"⏰ {s.course.name} ক্লাস {s.time.strftime('%H:%M')}-এ শুরু হচ্ছে (৫ মিনিটের মধ্যে)! "
                 f"ড্যাশবোর্ড থেকে জয়েন করুন।")
        n.recipients.set(students + ([s.teacher] if s.teacher else []))
        # অভিভাবকের WhatsApp
        for st in students:
            if not st.phone:
                continue
            text = (f"আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম {st.guardian or 'অভিভাবক'}, "
                    f"{st.name_bn}-এর \"{s.course.name}\" ক্লাস আজ {s.time.strftime('%H:%M')}-এ "
                    f"(আর ৫ মিনিটের মধ্যে) শুরু হচ্ছে ইনশাআল্লাহ। অনুগ্রহ করে ক্লাসে যুক্ত হতে সহায়তা করুন। "
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
def generate_monthly_dues():
    from .models import User, DueMonth
    t = date.today()
    label = f"{BN_MONTHS[t.month - 1]} {str(t.year).translate(BN_DIGITS)}"
    for u in User.objects.filter(role__in=["student", "teacher"], is_active=True):
        DueMonth.objects.get_or_create(user=u, month_label=label)


# ─────────────────── সাপ্তাহিক রুটিন → সামনের সপ্তাহের ক্লাস অটো তৈরি ───────────────────
@shared_task
def generate_routine_sessions():
    """প্রতিদিন রাতে: প্রতিটি সক্রিয় রুটিনের আগামী ৭ দিনের ক্লাস নিশ্চিত করা"""
    from .models import Routine, ClassSession
    today = date.today()
    for r in Routine.objects.filter(is_active=True):
        for off in range(7):
            d = today + timedelta(days=off)
            if d.weekday() not in _js_to_py(r.days):
                continue
            exists = ClassSession.objects.filter(routine=r, date=d).exists()
            if not exists:
                s = ClassSession.objects.create(
                    routine=r, course=r.course, teacher=r.teacher, date=d, time=r.time,
                    duration_min=r.duration_min, zoom_link=r.zoom_link, kind="regular")
                s.students.set(r.students.all())


def _js_to_py(js_days):
    """JS getDay() (০=রবি) → Python weekday() (০=সোম)"""
    return {(d - 1) % 7 for d in js_days}
