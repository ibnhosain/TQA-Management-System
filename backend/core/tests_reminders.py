# -*- coding: utf-8 -*-
"""📲 ক্লাসের ১০ মিনিট আগের WhatsApp রিমাইন্ডার — শিক্ষার্থী ও উস্তাদ দুজনকেই,
প্রত্যেকের নিজের সময়বলয়ে, ইংরেজিতে; API-তে অনুমোদিত template হিসেবে।
"""
import json
import os
from datetime import datetime, time as T
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase

BD = ZoneInfo("Asia/Dhaka")
SIGN = "Please join on time. — Tarbiyatul Quran Academy"


class TenMinutesBefore(TestCase):
    def setUp(self):
        from core.models import Course, User
        self.t = User.objects.create(username="t", role="teacher", name_bn="Ustadh Karim",
                                     phone="8801711111111")
        self.lon = User.objects.create(username="s1", role="student", name_bn="Saif",
                                       phone="447700900001", timezone="Europe/London")
        self.bd = User.objects.create(username="s2", role="student", name_bn="Ayra",
                                      phone="8801700000002")
        self.c = Course.objects.create(name="Noorani Qaida", teacher=self.t)
        for target, kw in (("core.tasks.dispatch_whatsapp", {}),
                           ("core.tasks.whatsapp_configured", {"return_value": True})):
            p = mock.patch(target, **kw)
            p.start()
            self.addCleanup(p.stop)

    def klass(self, date, hhmm):
        from core.models import ClassSession
        k = ClassSession.objects.create(course=self.c, teacher=self.t, date=date,
                                        time=T(*hhmm), duration_min=60, kind="regular")
        k.students.set([self.lon, self.bd])
        return k

    def run_at(self, now):
        from core.tasks import queue_class_reminders
        with mock.patch("core.tasks.timezone.localtime", return_value=now):
            return queue_class_reminders()

    def texts(self):
        from core.models import WaMessage
        return {m.to_name: m for m in WaMessage.objects.all()}

    def test_waits_until_ten_minutes(self):
        self.klass(datetime(2026, 11, 20).date(), (14, 10))
        self.assertEqual(self.run_at(datetime(2026, 11, 20, 13, 59, tzinfo=BD)), 0)  # ১১ মিনিট
        self.assertEqual(self.run_at(datetime(2026, 11, 20, 14, 0, tzinfo=BD)), 1)   # ১০ মিনিট

    def test_students_and_teacher_each_in_their_own_time(self):
        self.klass(datetime(2026, 11, 20).date(), (14, 10))
        self.run_at(datetime(2026, 11, 20, 14, 0, tzinfo=BD))
        msgs = self.texts()
        self.assertEqual(set(msgs), {"Saif", "Ayra", "Ustadh Karim"})
        self.assertEqual(
            msgs["Saif"].text,
            "Assalamu Alaikum Saif, your Noorani Qaida class starts in 10 minutes, "
            f"at 8:10 AM London time. {SIGN}")
        self.assertIn("at 2:10 PM Bangladesh time", msgs["Ayra"].text)
        self.assertIn("at 2:10 PM Bangladesh time", msgs["Ustadh Karim"].text)
        self.assertEqual(msgs["Saif"].template_params,
                         ["Saif", "Noorani Qaida", "10", "8:10 AM London time"])
        self.assertEqual(msgs["Saif"].student_id, self.lon.id)
        self.assertIsNone(msgs["Ustadh Karim"].student_id)  # উস্তাদের মেসেজ — শিক্ষার্থী নয়
        self.assertEqual(msgs["Saif"].phone, "447700900001")

    def test_in_app_notification_has_no_clock_time(self):
        from core.models import Notification
        self.klass(datetime(2026, 11, 20).date(), (14, 10))
        self.run_at(datetime(2026, 11, 20, 14, 0, tzinfo=BD))
        n = Notification.objects.get()
        self.assertEqual(n.text, "⏰ Your Noorani Qaida class starts in 10 minutes — please join on time.")
        self.assertEqual(set(n.recipients.values_list("username", flat=True)), {"s1", "s2", "t"})

    def test_late_server_still_sends_with_real_minutes(self):
        self.klass(datetime(2026, 11, 20).date(), (14, 10))
        self.run_at(datetime(2026, 11, 20, 14, 7, tzinfo=BD))
        self.assertIn("starts in 3 minutes", self.texts()["Ayra"].text)

    def test_started_class_gets_no_reminder(self):
        self.klass(datetime(2026, 11, 20).date(), (14, 10))
        self.assertEqual(self.run_at(datetime(2026, 11, 20, 14, 10, tzinfo=BD)), 0)

    def test_just_after_midnight_class_is_reminded_before_midnight(self):
        self.klass(datetime(2026, 11, 21).date(), (0, 5))
        self.assertEqual(self.run_at(datetime(2026, 11, 20, 23, 55, tzinfo=BD)), 1)
        self.assertIn("at 12:05 AM Bangladesh time", self.texts()["Ayra"].text)


class SentAsApprovedTemplate(TestCase):
    """Meta ২৪ ঘণ্টার বাইরে সাধারণ লেখা ফিরিয়ে দেয় — রিমাইন্ডার যায় template-এ"""

    META = {"WHATSAPP_PROVIDER": "meta", "META_ACCESS_TOKEN": "EAAG-test",
            "META_PHONE_NUMBER_ID": "1234567890"}

    def msg(self, reason="reminder"):
        from core.models import WaMessage
        return WaMessage.objects.create(
            to_name="Saif", phone="+44 7700 900001", reason=reason,
            text="Assalamu Alaikum Saif, …",
            template_params=["Saif", "Noorani Qaida", "10", "8:10 AM London time"])

    def send(self, msg, env):
        from core.tasks import send_whatsapp_now
        resp = mock.Mock(**{"json.return_value": {"messages": [{"id": "wamid.X"}], "sid": "SM1"}})
        with mock.patch.dict(os.environ, env), mock.patch("core.tasks.http.post",
                                                          return_value=resp) as post:
            send_whatsapp_now(msg.id)
        msg.refresh_from_db()
        return post.call_args

    def test_meta_reminder_uses_class_reminder_template(self):
        m = self.msg()
        call = self.send(m, self.META)
        self.assertIn("/v22.0/1234567890/messages", call.args[0])
        body = call.kwargs["json"]
        self.assertEqual(body["to"], "447700900001")
        self.assertEqual(body["type"], "template")
        self.assertEqual(body["template"]["name"], "class_reminder")
        self.assertEqual(body["template"]["language"], {"code": "en"})
        self.assertEqual([p["text"] for p in body["template"]["components"][0]["parameters"]],
                         ["Saif", "Noorani Qaida", "10", "8:10 AM London time"])
        self.assertEqual((m.status, m.provider_ref), ("sent", "wamid.X"))

    def test_other_messages_stay_plain_text(self):
        body = self.send(self.msg(reason="postpone"), self.META).kwargs["json"]
        self.assertEqual((body["type"], body["text"]["body"]), ("text", "Assalamu Alaikum Saif, …"))

    def test_template_can_be_switched_off_for_testing(self):
        body = self.send(self.msg(), {**self.META, "META_REMINDER_TEMPLATE": ""}).kwargs["json"]
        self.assertEqual(body["type"], "text")

    def test_graph_version_is_configurable(self):
        call = self.send(self.msg(), {**self.META, "META_GRAPH_VERSION": "v24.0"})
        self.assertIn("/v24.0/", call.args[0])

    def test_twilio_content_template(self):
        env = {"WHATSAPP_PROVIDER": "twilio", "TWILIO_ACCOUNT_SID": "AC1",
               "TWILIO_AUTH_TOKEN": "tok", "TWILIO_WHATSAPP_FROM": "+14155238886",
               "TWILIO_REMINDER_CONTENT_SID": "HX123"}
        data = self.send(self.msg(), env).kwargs["data"]
        self.assertEqual(data["ContentSid"], "HX123")
        self.assertEqual(json.loads(data["ContentVariables"])["4"], "8:10 AM London time")
        self.assertNotIn("Body", data)
