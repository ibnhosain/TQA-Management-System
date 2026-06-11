"""
TQA-MS — Celery কনফিগ
১) এই ফাইলটি tqa_backend/celery.py নামে প্রজেক্ট ফোল্ডারে রাখুন
২) tqa_backend/__init__.py-তে:  from .celery import app as celery_app
৩) চালু:  celery -A tqa_backend worker -B -l info     (Redis লাগবে: redis-server)
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tqa_backend.settings")

app = Celery("tqa_backend")
app.conf.broker_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
app.conf.timezone = "Asia/Dhaka"
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # প্রতি মিনিটে: ক্লাস শুরুর ৫ মিনিট আগের WhatsApp রিমাইন্ডার
    "class-reminders": {"task": "core.tasks.queue_class_reminders", "schedule": 60.0},
    # প্রতিদিন রাত ২টা: রুটিন থেকে সামনের ৭ দিনের ক্লাস
    "routine-sessions": {"task": "core.tasks.generate_routine_sessions",
                         "schedule": crontab(hour=2, minute=0)},
    # মাসের ১ তারিখ ভোর ৫টা: সবার বকেয়া মাস তৈরি
    "monthly-dues": {"task": "core.tasks.generate_monthly_dues",
                     "schedule": crontab(day_of_month=1, hour=5, minute=0)},
}
