# -*- coding: utf-8 -*-
"""📤 WhatsApp Messages (আউটবক্স) — হাতে পাঠানো সংরক্ষণ, API না থাকলে পরিষ্কার
বার্তা, আর শুধু শেষ ৩০ দিনের মেসেজ।"""
import os
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone


class Outbox(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import User, WaMessage
        self.W = WaMessage
        self.c = APIClient()
        self.c.force_authenticate(User.objects.create(username="d", role="director", name_bn="D"))
        self.m = WaMessage.objects.create(to_name="Saif", phone="8801700000001",
                                          text="hi", reason="reminder")

    def test_manual_send_is_remembered(self):
        r = self.c.post(f"/api/wa-messages/{self.m.id}/mark_sent/")
        self.assertEqual(r.status_code, 200)
        self.m.refresh_from_db()
        self.assertEqual((self.m.status, self.m.provider_ref), ("sent", "manual"))
        # রিফ্রেশের পরেও (নতুন করে তালিকা আনলে) পাঠানো দেখায়
        row = next(x for x in self.c.get("/api/wa-messages/").json() if x["id"] == self.m.id)
        self.assertEqual(row["status"], "sent")

    def test_api_send_without_keys_is_refused_not_failed(self):
        with mock.patch("core.tasks.whatsapp_configured", return_value=False):
            r = self.c.post(f"/api/wa-messages/{self.m.id}/send_now/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("not connected", r.json()["error"])
        self.m.refresh_from_db()
        self.assertEqual(self.m.status, "queued")  # লাল "failed" হয় না

    def test_api_send_rejected_by_whatsapp_reports_error(self):
        def fail(pk):
            self.W.objects.filter(pk=pk).update(status="failed")
        with mock.patch("core.tasks.whatsapp_configured", return_value=True), \
                mock.patch("core.tasks.dispatch_whatsapp", side_effect=fail):
            r = self.c.post(f"/api/wa-messages/{self.m.id}/send_now/")
        self.assertEqual(r.status_code, 502)

    def test_api_send_success(self):
        def ok(pk):
            self.W.objects.filter(pk=pk).update(status="sent", provider_ref="wamid.1")
        with mock.patch("core.tasks.whatsapp_configured", return_value=True), \
                mock.patch("core.tasks.dispatch_whatsapp", side_effect=ok):
            r = self.c.post(f"/api/wa-messages/{self.m.id}/send_now/")
        self.assertEqual((r.status_code, r.json()["status"]), (200, "sent"))

    def test_config_reports_connection(self):
        with mock.patch("core.tasks.whatsapp_configured", return_value=False):
            self.assertIs(self.c.get("/api/wa-messages/config/").json()["whatsapp_configured"], False)

    def test_only_last_30_days_listed(self):
        old = self.W.objects.create(to_name="Old", phone="1", text="x", reason="reminder")
        self.W.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=31))
        names = [x["to_name"] for x in self.c.get("/api/wa-messages/").json()]
        self.assertEqual(names, ["Saif"])

    def test_teacher_and_student_cannot_see_outbox(self):
        from core.models import User
        for role in ("teacher", "student"):
            self.c.force_authenticate(User.objects.create(username=role, role=role, name_bn=role))
            self.assertEqual(self.c.get("/api/wa-messages/").status_code, 403)
