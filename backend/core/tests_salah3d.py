"""নামাজ শিক্ষার 3D মডেল: লগইন ছাড়া/ট্রায়ালে বন্ধ, শিক্ষার্থী-উস্তাদ-এডমিন-পরিচালক পান।"""
from django.test import TestCase
from rest_framework.test import APIClient
from .models import User


class Salah3DModelTests(TestCase):
    def setUp(self):
        self.c = APIClient()

    def _user(self, role):
        return User.objects.create_user(username="u_" + role, password="x12345678", role=role)

    def test_no_login_blocked(self):
        self.assertEqual(self.c.get("/api/salah3d/boy/").status_code, 401)

    def test_trial_blocked(self):
        self.c.force_authenticate(self._user("trial"))
        self.assertEqual(self.c.get("/api/salah3d/boy/").status_code, 403)

    def test_roles_get_model(self):
        for role in ("student", "teacher", "admin", "director"):
            self.c.force_authenticate(self._user(role))
            r = self.c.get("/api/salah3d/girl/")
            self.assertEqual(r.status_code, 200, role)
            self.assertEqual(r["Content-Type"], "model/gltf-binary")
            self.assertTrue(b"".join(r.streaming_content)[:4] == b"glTF")

    def test_unknown_kind(self):
        self.c.force_authenticate(self._user("student"))
        self.assertEqual(self.c.get("/api/salah3d/../settings/").status_code, 404)
