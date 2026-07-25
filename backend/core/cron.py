"""
TQA-MS — Cron Endpoints (core/cron.py)

Celery/Redis ছাড়া ফ্রি hosting এ scheduled কাজ চালানোর ব্যবস্থা।
cron-job.org (ফ্রি) থেকে এই URL গুলোতে নির্দিষ্ট সময়ে request আসবে:

  প্রতি মিনিটে:        GET /api/cron/reminders/?key=<CRON_SECRET>
  প্রতিদিন রাত ২টায়:   GET /api/cron/daily/?key=<CRON_SECRET>
  মাসের ১ তারিখ ৫টায়:  GET /api/cron/monthly/?key=<CRON_SECRET>

CRON_SECRET টা environment variable এ রাখুন — না মিললে 403।
"""
import os
import secrets

from django.http import JsonResponse
from django.views.decorators.http import require_GET


def _authorized(request):
    expected = os.environ.get("CRON_SECRET", "")
    given = request.GET.get("key", "") or request.headers.get("X-Cron-Key", "")
    # secrets.compare_digest → timing attack থেকে নিরাপদ
    return bool(expected) and secrets.compare_digest(given, expected)


def _run(request, fn, name):
    if not _authorized(request):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    try:
        result = fn()  # Celery task কে সরাসরি ডাকলে synchronous চলে
        return JsonResponse({"ok": True, "task": name, "result": result})
    except Exception as exc:
        return JsonResponse({"ok": False, "task": name, "error": str(exc)}, status=500)


@require_GET
def cron_reminders(request):
    """ক্লাস শুরুর ৫ মিনিট আগের WhatsApp রিমাইন্ডার (প্রতি মিনিটে ডাকুন)"""
    from .tasks import queue_class_reminders
    return _run(request, queue_class_reminders, "reminders")


@require_GET
def cron_daily(request):
    """রুটিন থেকে সামনের ৭ দিনের ক্লাস তৈরি + ৬০ দিনের বেশি পুরনো ক্লাস-শিডিউল মোছা
    (হাজিরার তথ্য কখনো মোছে না — dennormalized স্ন্যাপশট থেকে যায়, প্রতিদিন একবার)"""
    from .tasks import generate_routine_sessions, cleanup_old_classes

    def _both():
        return {"created": generate_routine_sessions(), "deleted_old_classes": cleanup_old_classes()}

    return _run(request, _both, "daily")


@require_GET
def cron_monthly(request):
    """সবার মাসিক বকেয়া তৈরি (মাসের ১ তারিখে একবার)"""
    from .tasks import generate_monthly_dues
    return _run(request, generate_monthly_dues, "monthly")
