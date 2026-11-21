# -*- coding: utf-8 -*-
"""🌐 পরিবার ও কর্মীদের কাছে যাওয়া নোটিফিকেশন/WhatsApp ইংরেজিতে।"""
import re
from datetime import date, time as T, timedelta

from django.test import TestCase

BN = re.compile(r"[\u0980-\u09FF]")


class PostponeAndLeave(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import Course, User
        self.d = User.objects.create(username="d", role="director", name_bn="Director")
        self.t = User.objects.create(username="t", role="teacher", name_bn="Ustadh Karim")
        self.lon = User.objects.create(username="s1", role="student", name_bn="Saif",
                                       phone="447700900001", timezone="Europe/London")
        self.c = Course.objects.create(name="Noorani Qaida", teacher=self.t)
        self.api = APIClient()
        self.api.force_authenticate(self.d)

    def test_postpone_message_english_and_in_each_ones_time(self):
        from core.models import ClassSession, Notification, WaMessage
        k = ClassSession.objects.create(course=self.c, teacher=self.t, date=date(2026, 11, 20),
                                        time=T(14, 10), duration_min=60, kind="regular")
        k.students.set([self.lon])
        self.assertEqual(self.api.post(f"/api/classes/{k.id}/postpone/").status_code, 200)
        wa = WaMessage.objects.get()
        self.assertEqual(wa.text, "Assalamu Alaikum Saif, your Noorani Qaida class on "
                         "Fri 20 Nov, 8:10 AM London time has been postponed for an unavoidable "
                         "reason. A make-up class will be scheduled, insha'Allah. — Tarbiyatul Quran Academy")
        self.assertEqual(wa.reason, "postpone")
        n = Notification.objects.get()
        self.assertIn("Fri 20 Nov, 2:10 PM Bangladesh time", n.text)
        self.assertFalse(BN.search(wa.text + n.text))

    def test_leave_notifications_show_english_type(self):
        from core.models import Notification
        self.api.force_authenticate(self.lon)
        r = self.api.post("/api/leaves/", {"leave_type": "অসুস্থতা", "from_date": "2026-11-21",
                                            "to_date": "2026-11-22", "reason": "fever"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        n = Notification.objects.latest("id")
        self.assertIn("applied for leave (Sickness:", n.text)
        self.assertFalse(BN.search(n.text))
