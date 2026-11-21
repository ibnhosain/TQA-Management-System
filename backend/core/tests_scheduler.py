# -*- coding: utf-8 -*-
"""⏰ সার্ভারের নিজের পাহারাদার (core/scheduler.py)।

যা রক্ষা করা হচ্ছে:
- কোনো কাজ একই সময়কালে দুবার চলে না — পাহারাদারের সব worker আর
  cron-job.org একই লক ভাগ করে।
- ব্যর্থ হলে দাবি ছেড়ে দেয়, ত্রুটি লিখে রাখে, পরের বার আবার চেষ্টা করে।
- মাসিক বকেয়া ১ তারিখে ফসকালেও মাসের পরের দিনগুলোতে ধরে নেয় — আগে
  একবার ফসকালে সে মাসের বকেয়া কখনোই তৈরি হতো না।
- কাজ শেষ জানা থাকলে প্রতি মিনিটের টিকে ডাটাবেসে যায় না।
"""
import importlib
import os
from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone

from core import scheduler
from core.models import ScheduledJob

BD = ZoneInfo("Asia/Dhaka")


def bd(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=BD)


class ExactlyOnce(TestCase):
    def setUp(self):
        self.calls = 0

    def work(self):
        self.calls += 1
        return {"created": self.calls}

    def test_runs_once_per_key(self):
        self.assertEqual(scheduler.run_job("daily", "2026-11-20", self.work, "t")[0], "ran")
        self.assertEqual(scheduler.run_job("daily", "2026-11-20", self.work, "t")[0], "done")
        self.assertEqual(self.calls, 1)
        job = ScheduledJob.objects.get(name="daily")
        self.assertEqual(job.done_key, "2026-11-20")
        self.assertEqual(job.last_result, {"created": 1})
        self.assertEqual(job.claimed_key, "")

    def test_next_period_runs_again(self):
        scheduler.run_job("daily", "2026-11-20", self.work, "t")
        self.assertEqual(scheduler.run_job("daily", "2026-11-21", self.work, "t")[0], "ran")
        self.assertEqual(self.calls, 2)

    def test_someone_else_running_is_busy(self):
        ScheduledJob.objects.create(name="daily", claimed_key="2026-11-20",
                                    claimed_at=timezone.now())
        self.assertEqual(scheduler.run_job("daily", "2026-11-20", self.work, "t")[0], "busy")
        self.assertEqual(self.calls, 0)

    def test_stale_claim_from_dead_process_is_retried(self):
        ScheduledJob.objects.create(name="daily", claimed_key="2026-11-20",
                                    claimed_at=timezone.now() - timedelta(hours=1))
        self.assertEqual(scheduler.run_job("daily", "2026-11-20", self.work, "t")[0], "ran")
        self.assertEqual(self.calls, 1)


class FailureIsRetried(TestCase):
    def test_failure_releases_claim_and_records_error(self):
        def boom():
            raise RuntimeError("db is down")

        with self.assertRaises(RuntimeError):
            scheduler.run_job("monthly", "2026-11", boom, "t")
        job = ScheduledJob.objects.get(name="monthly")
        self.assertEqual(job.done_key, "")
        self.assertEqual(job.claimed_key, "")
        self.assertIn("db is down", job.last_error)
        self.assertIsNotNone(job.last_error_at)

        # পরের বার আবার চেষ্টা — সফল হলে পুরনো ত্রুটি মুছে যায়
        self.assertEqual(scheduler.run_job("monthly", "2026-11", lambda: {"created": 3}, "t")[0], "ran")
        job.refresh_from_db()
        self.assertEqual(job.done_key, "2026-11")
        self.assertEqual(job.last_error, "")
        self.assertIsNone(job.last_error_at)


class WhenJobsAreDue(TestCase):
    def names(self, now):
        return [n for n, _, _ in scheduler.due_jobs(now)]

    def test_daily_waits_until_2am(self):
        self.assertNotIn("daily", self.names(bd(2026, 11, 20, 1, 59)))
        self.assertIn("daily", self.names(bd(2026, 11, 20, 2, 0)))

    def test_monthly_waits_until_5am_on_the_first(self):
        self.assertNotIn("monthly", self.names(bd(2026, 12, 1, 4, 59)))
        self.assertIn("monthly", self.names(bd(2026, 12, 1, 5, 0)))

    def test_monthly_catches_up_later_in_the_month(self):
        # ১ তারিখে সার্ভার বন্ধ ছিল বা কাজ ব্যর্থ হয়েছিল — ৩ তারিখ রাত ১২:৩০-এও ধরে নেয়
        self.assertIn("monthly", self.names(bd(2026, 12, 3, 0, 30)))

    def test_keys(self):
        now = bd(2026, 12, 3, 9, 0)
        keys = {n: k for n, k, _ in scheduler.due_jobs(now)}
        self.assertEqual(keys, {"daily": "2026-12-03", "monthly": "2026-12",
                                "reminders": "2026-12-03T09:00"})


class NoDbWhenAlreadyDone(TestCase):
    def setUp(self):
        scheduler._known_done.clear()

    def tearDown(self):
        scheduler._known_done.clear()

    def test_second_tick_does_not_touch_the_database(self):
        now = bd(2026, 11, 20, 9, 0)
        scheduler.run_due_jobs("t", now=now)
        self.assertEqual(ScheduledJob.objects.get(name="daily").done_key, "2026-11-20")
        with self.assertNumQueries(0):
            scheduler.run_due_jobs("t", now=now)

    def test_busy_job_is_checked_again_next_tick(self):
        ScheduledJob.objects.create(name="daily", claimed_key="2026-11-20",
                                    claimed_at=timezone.now())
        ScheduledJob.objects.create(name="monthly", done_key="2026-11")
        scheduler.run_due_jobs("t", now=bd(2026, 11, 20, 9, 0))
        self.assertNotIn("daily", scheduler._known_done)  # অন্যজন ব্যর্থ হলে আমরা যেন আবার ধরি


class MonthlyDuesEndToEnd(TestCase):
    def test_dues_created_once_and_not_duplicated(self):
        from core.models import DueMonth, User
        from core.tasks import month_label_for

        s = User.objects.create(username="stu", role="student", name_bn="S",
                                monthly_fee=3500)
        User.objects.filter(pk=s.pk).update(date_joined=timezone.now() - timedelta(days=70))
        key = scheduler.monthly_key(timezone.localtime())
        self.assertEqual(scheduler.run_job("monthly", key, scheduler.monthly_work, "t")[0], "ran")
        label = month_label_for(timezone.localtime().date())
        self.assertEqual(DueMonth.objects.filter(user=s, month_label=label).count(), 1)
        self.assertEqual(scheduler.run_job("monthly", key, scheduler.monthly_work, "t")[0], "done")
        self.assertEqual(DueMonth.objects.filter(user=s).count(), 1)


class CronSharesTheLock(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        patcher = mock.patch.dict(os.environ, {"CRON_SECRET": "s3cret"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_second_call_is_done_not_repeated(self):
        r1 = self.client.get("/api/cron/daily/?key=s3cret").json()
        r2 = self.client.get("/api/cron/daily/?key=s3cret").json()
        self.assertEqual((r1["ok"], r1["status"]), (True, "ran"))
        self.assertEqual((r2["ok"], r2["status"]), (True, "done"))
        self.assertEqual(ScheduledJob.objects.get(name="daily").last_trigger, "cron")

    def test_monthly_endpoint(self):
        r = self.client.get("/api/cron/monthly/?key=s3cret").json()
        self.assertEqual((r["ok"], r["status"]), (True, "ran"))

    def test_wrong_key_is_refused(self):
        self.assertEqual(self.client.get("/api/cron/daily/?key=nope").status_code, 403)
        self.assertFalse(ScheduledJob.objects.filter(name="daily").exists())


class StartsOnlyOnRender(TestCase):
    def setUp(self):
        scheduler._started = False
        self.addCleanup(setattr, scheduler, "_started", False)

    def _start(self, env):
        with mock.patch.dict(os.environ, env, clear=False), \
                mock.patch.object(scheduler.threading, "Thread") as T:
            for k in ("RENDER", "TQA_SCHEDULER"):
                if k not in env:
                    os.environ.pop(k, None)
            scheduler.start()
            scheduler.start()  # দ্বিতীয়বার ডাকলেও আরেকটি থ্রেড নয়
            return T.call_count

    def test_not_started_locally(self):
        self.assertEqual(self._start({}), 0)

    def test_started_once_on_render(self):
        self.assertEqual(self._start({"RENDER": "true"}), 1)

    def test_can_be_switched_off_on_render(self):
        self.assertEqual(self._start({"RENDER": "true", "TQA_SCHEDULER": "0"}), 0)

    def test_can_be_switched_on_elsewhere(self):
        self.assertEqual(self._start({"TQA_SCHEDULER": "1"}), 1)


class MigrationSeed(TestCase):
    """মাঝমাসে ডিপ্লয় — এ মাসের বকেয়া আগেই থাকলে মাসটা "হয়ে গেছে" ধরা হয়"""

    def seed(self):
        from django.apps import apps
        mod = importlib.import_module("core.migrations.0085_scheduledjob")
        mod.seed_monthly(apps, None)

    def test_existing_dues_mark_month_done(self):
        from core.models import DueMonth, User
        from core.tasks import month_label_for
        u = User.objects.create(username="stu", role="student", name_bn="S")
        DueMonth.objects.create(user=u, month_label=month_label_for(timezone.localtime().date()))
        self.seed()
        self.assertEqual(ScheduledJob.objects.get(name="monthly").done_key,
                         scheduler.monthly_key(timezone.localtime()))

    def test_no_dues_leaves_month_for_the_scheduler(self):
        self.seed()
        self.assertFalse(ScheduledJob.objects.filter(name="monthly").exists())


class HealthStatus(TestCase):
    """পরিচালকের স্বাস্থ্য কার্ড — কোন অবস্থায় কোন রং"""

    def state(self, now, name="daily"):
        return {j["name"]: j for j in scheduler.job_status(now)}[name]

    def test_before_2am_yesterdays_run_is_enough(self):
        ScheduledJob.objects.create(name="daily", done_key="2026-11-19")
        s = self.state(bd(2026, 11, 20, 1, 0))
        self.assertEqual((s["state"], s["expected_key"]), ("ok", "2026-11-19"))

    def test_just_due_is_pending_then_late(self):
        ScheduledJob.objects.create(name="daily", done_key="2026-11-19")
        self.assertEqual(self.state(bd(2026, 11, 20, 2, 5))["state"], "pending")
        late = self.state(bd(2026, 11, 20, 3, 0))
        self.assertEqual((late["state"], late["overdue_minutes"]), ("late", 60))

    def test_failure_shows_error(self):
        ScheduledJob.objects.create(name="daily", done_key="2026-11-19",
                                    last_error="RuntimeError: db is down",
                                    last_error_at=timezone.now())
        s = self.state(bd(2026, 11, 20, 2, 5))
        self.assertEqual(s["state"], "error")
        self.assertIn("db is down", s["last_error"])

    def test_done_today_is_ok(self):
        ScheduledJob.objects.create(name="daily", done_key="2026-11-20")
        self.assertEqual(self.state(bd(2026, 11, 20, 9, 0))["state"], "ok")

    def test_monthly_early_on_the_first_expects_last_month(self):
        ScheduledJob.objects.create(name="monthly", done_key="2026-11")
        s = self.state(bd(2026, 12, 1, 3, 0), "monthly")
        self.assertEqual((s["state"], s["expected_key"]), ("ok", "2026-11"))
        self.assertEqual(self.state(bd(2026, 12, 1, 6, 0), "monthly")["state"], "late")

    def test_never_ran_is_reported(self):
        s = self.state(bd(2026, 11, 20, 9, 0))
        self.assertEqual((s["state"], s["done_key"], s["last_run_at"]), ("late", "", None))

    def test_endpoint_permissions(self):
        from rest_framework.test import APIClient
        from core.models import User
        c = APIClient()
        for role, code in (("director", 200), ("admin", 200), ("teacher", 403), ("student", 403)):
            u = User.objects.create(username=f"u_{role}", role=role, name_bn=role)
            c.force_authenticate(u)
            r = c.get("/api/scheduler/status/")
            self.assertEqual(r.status_code, code, role)
            if code == 200:
                self.assertEqual({j["name"] for j in r.json()["jobs"]}, {"daily", "monthly", "reminders"})


class RemindersSentOnce(TestCase):
    """অভিভাবক একই রিমাইন্ডার কখনো দুবার পাবেন না"""

    def setUp(self):
        from datetime import time as T
        from core.models import ClassSession, Course, User
        self.now = bd(2026, 11, 20, 14, 0)
        t = User.objects.create(username="t", role="teacher", name_bn="T")
        self.students = [
            User.objects.create(username=f"s{i}", role="student", name_bn=f"S{i}",
                                phone=f"88017000000{i}", guardian="G")
            for i in (1, 2)
        ]
        c = Course.objects.create(name="Qaida", teacher=t)
        self.s = ClassSession.objects.create(course=c, teacher=t, date=self.now.date(),
                                             time=T(14, 10), duration_min=60, kind="regular")
        self.s.students.set(self.students)
        for target, kw in (("core.tasks.timezone.localtime", {"return_value": self.now}),
                           ("core.tasks.dispatch_whatsapp", {}),
                           ("core.tasks.whatsapp_configured", {"return_value": True})):
            p = mock.patch(target, **kw)
            setattr(self, target.rsplit(".", 1)[1], p.start())
            self.addCleanup(p.stop)

    def counts(self):
        from core.models import Notification, WaMessage
        return WaMessage.objects.count(), Notification.objects.count()

    def test_second_run_sends_nothing(self):
        from core.tasks import queue_class_reminders
        self.assertEqual(queue_class_reminders(), 1)
        self.assertEqual(queue_class_reminders(), 0)
        self.assertEqual(self.counts(), (2, 1))  # দুই অভিভাবক, একটি নোটিফিকেশন

    def test_other_worker_claims_between_read_and_send(self):
        """আসল রেস: আমরা ক্লাসটি "পাঠানো হয়নি" পড়ার পর, দাবি করার আগে
        অন্য worker দাবি করে ফেলল — আমরা যেন আর না পাঠাই"""
        from core import tasks
        from core.models import ClassSession
        real = tasks.timezone.make_aware

        def other_worker_claims_first(dt, *args, **kwargs):
            # কেবল লুপের নিজের ডাকে (এক আর্গুমেন্ট) — Django নিজেও ডাটাবেসের
            # তারিখ পড়তে দুই আর্গুমেন্টে make_aware ডাকে, সেগুলো যেমন ছিল
            if not args and not kwargs:
                ClassSession.objects.filter(pk=self.s.pk).update(reminder_sent=True)
            return real(dt, *args, **kwargs)

        with mock.patch("core.tasks.timezone.make_aware", side_effect=other_worker_claims_first):
            self.assertEqual(tasks.queue_class_reminders(), 0)
        self.assertEqual(self.counts(), (0, 0))

    def test_one_failed_send_does_not_skip_the_others(self):
        from core.tasks import queue_class_reminders
        self.dispatch_whatsapp.side_effect = [RuntimeError("provider down"), None]
        with self.assertLogs("tqa.scheduler", level="ERROR"):
            self.assertEqual(queue_class_reminders(), 1)
        self.assertEqual(self.dispatch_whatsapp.call_count, 2)
        self.assertEqual(self.counts()[0], 2)  # দুটো মেসেজই আউটবক্সে


class RemindersSchedule(TestCase):
    def test_due_every_minute_any_time(self):
        jobs = {n: k for n, k, _ in scheduler.due_jobs(bd(2026, 11, 20, 1, 7))}
        self.assertEqual(jobs["reminders"], "2026-11-20T01:07")
        self.assertNotIn("daily", jobs)  # রাত ১টা — দৈনিকের সময় হয়নি

    def test_health(self):
        now = bd(2026, 11, 20, 14, 0)
        st = lambda: {j["name"]: j for j in scheduler.job_status(now)}["reminders"]
        self.assertEqual(st()["state"], "late")  # কখনো চলেনি
        ScheduledJob.objects.create(name="reminders", last_run_at=now - timedelta(minutes=2))
        self.assertEqual(st()["state"], "ok")
        ScheduledJob.objects.filter(name="reminders").update(last_run_at=now - timedelta(minutes=10))
        self.assertEqual((st()["state"], st()["overdue_minutes"]), ("late", 10))
        ScheduledJob.objects.filter(name="reminders").update(last_error="X: boom")
        self.assertEqual(st()["state"], "error")

    def test_cron_endpoint_shares_the_minute_lock(self):
        from rest_framework.test import APIClient
        c = APIClient()
        with mock.patch.dict(os.environ, {"CRON_SECRET": "s3cret"}):
            r1 = c.get("/api/cron/reminders/?key=s3cret").json()
            r2 = c.get("/api/cron/reminders/?key=s3cret").json()
        self.assertEqual((r1["status"], r2["status"]), ("ran", "done"))


class WithoutWhatsAppApi(TestCase):
    """API বসানো না থাকলে মেসেজ তৈরি হয়, পাঠানোর চেষ্টা হয় না — "অপেক্ষমাণ"
    থাকে হাতে পাঠানোর জন্য; লাল "failed" হয়ে জমে না"""

    def test_configured_detection(self):
        from core.tasks import whatsapp_configured
        none = {k: "" for k in ("WHATSAPP_PROVIDER", "META_ACCESS_TOKEN", "META_PHONE_NUMBER_ID",
                                "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM")}
        with mock.patch.dict(os.environ, none):
            self.assertFalse(whatsapp_configured())
        with mock.patch.dict(os.environ, {**none, "META_ACCESS_TOKEN": "EAAG", "META_PHONE_NUMBER_ID": "1"}):
            self.assertTrue(whatsapp_configured())
        with mock.patch.dict(os.environ, {**none, "WHATSAPP_PROVIDER": "twilio", "TWILIO_ACCOUNT_SID": "AC"}):
            self.assertFalse(whatsapp_configured())  # তিনটির একটি মাত্র

    def test_reminder_waits_for_manual_sending(self):
        from datetime import time as T
        from core.models import ClassSession, Course, User, WaMessage
        from core.tasks import queue_class_reminders
        now = bd(2026, 11, 20, 14, 0)
        t = User.objects.create(username="t", role="teacher", name_bn="T")
        st = User.objects.create(username="s", role="student", name_bn="S", phone="8801700000001")
        c = Course.objects.create(name="Qaida", teacher=t)
        k = ClassSession.objects.create(course=c, teacher=t, date=now.date(), time=T(14, 10),
                                        duration_min=60, kind="regular")
        k.students.set([st])
        with mock.patch("core.tasks.timezone.localtime", return_value=now), \
                mock.patch("core.tasks.whatsapp_configured", return_value=False), \
                mock.patch("core.tasks.dispatch_whatsapp") as dispatch:
            self.assertEqual(queue_class_reminders(), 1)
        dispatch.assert_not_called()
        self.assertEqual(list(WaMessage.objects.values_list("status", flat=True)), ["queued"])

    def test_status_endpoint_reports_it(self):
        from rest_framework.test import APIClient
        from core.models import User
        c = APIClient()
        c.force_authenticate(User.objects.create(username="d", role="director", name_bn="D"))
        with mock.patch("core.tasks.whatsapp_configured", return_value=False):
            self.assertIs(c.get("/api/scheduler/status/").json()["whatsapp_configured"], False)
