"""
TQA-MS — Cron Endpoints (core/cron.py)

Celery/Redis ছাড়া ফ্রি hosting এ scheduled কাজ চালানোর ব্যবস্থা।
⚠️ দৈনিক ও মাসিক কাজ এখন সার্ভার নিজেই চালায় (core/scheduler.py); এই
URL গুলো ব্যাকআপ — একই লকে চলে বলে কাজ দুবার হয় না।
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


def _run_scheduled(request, name, key_fn, work):
    """সার্ভারের নিজের পাহারাদারের সাথে একই লকে চলে (scheduler.run_job) —
    যে আগে আসে সে-ই কাজটি করে, অন্যজন দেখে "done"। এখানে সময় দেখা হয়
    না: cron ডাকলেই চলতি সময়কালের কাজ (যদি আগে না হয়ে থাকে)।"""
    from django.utils import timezone
    from .scheduler import run_job

    if not _authorized(request):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    key = key_fn(timezone.localtime())
    try:
        status, result = run_job(name, key, work, "cron")
    except Exception as exc:
        return JsonResponse({"ok": False, "task": name, "error": str(exc)}, status=500)
    return JsonResponse({"ok": True, "task": name, "key": key, "status": status, "result": result})


@require_GET
def cron_daily(request):
    """রুটিন থেকে সামনের ৭ দিনের ক্লাস তৈরি + তারিখ-পেরানো upcoming ক্লাস স্থগিত
    + ৬০ দিনের বেশি পুরনো ক্লাস-শিডিউল মোছা (হাজিরার তথ্য কখনো মোছে না, প্রতিদিন একবার)"""
    from .scheduler import daily_key, daily_work
    return _run_scheduled(request, "daily", daily_key, daily_work)


@require_GET
def cron_monthly(request):
    """সবার মাসিক বকেয়া তৈরি (মাসে একবার)"""
    from .scheduler import monthly_key, monthly_work
    return _run_scheduled(request, "monthly", monthly_key, monthly_work)
