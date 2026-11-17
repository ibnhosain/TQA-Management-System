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


class Salah3DTurnTests(TestCase):
    def setUp(self):
        self.c = APIClient()

    def test_turn_protected(self):
        self.assertEqual(self.c.get("/api/salah3d/turn/boy-10-ruku/").status_code, 401)
        self.c.force_authenticate(User.objects.create_user(username="tt", password="x12345678", role="trial"))
        self.assertEqual(self.c.get("/api/salah3d/turn/boy-10-ruku/").status_code, 403)

    def test_turn_student(self):
        self.c.force_authenticate(User.objects.create_user(username="ts", password="x12345678", role="student"))
        r = self.c.get("/api/salah3d/turn/boy-10-ruku/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/jpeg")
        self.assertEqual(self.c.get("/api/salah3d/turn/..%2Fsettings/").status_code, 404)


class Salah3DFocusTests(TestCase):
    def test_focus_protected(self):
        c = APIClient()
        self.assertEqual(c.get("/api/salah3d/focus/boy-10-ruku/").status_code, 401)
        c.force_authenticate(User.objects.create_user(username="ft", password="x12345678", role="trial"))
        self.assertEqual(c.get("/api/salah3d/focus/boy-10-ruku/").status_code, 403)


class LectureDeckTests(TestCase):
    def test_upload_play_delete(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Course
        c = APIClient()
        course = Course.objects.create(name="Easy Noorani Qaida")
        pptx = SimpleUploadedFile("l1.pptx", b"PK\x03\x04fake", content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        self.assertEqual(c.post("/api/decks/", {"course": course.id, "no": 1, "file": pptx}).status_code, 401)
        c.force_authenticate(User.objects.create_user(username="t1", password="x12345678", role="teacher"))
        self.assertEqual(c.post("/api/decks/", {"course": course.id, "no": 1, "file": pptx}).status_code, 403)
        c.force_authenticate(User.objects.create_user(username="d1", password="x12345678", role="director"))
        pptx.seek(0)
        r = c.post("/api/decks/", {"course": course.id, "no": 1, "title": "Day 1", "file": pptx})
        self.assertEqual(r.status_code, 201)
        did = r.json()["id"]
        self.assertEqual(c.get(f"/api/decks/{did}/").content, b"PK\x03\x04fake")
        c.force_authenticate(User.objects.create_user(username="s1", password="x12345678", role="student"))
        self.assertEqual(c.get(f"/api/decks/{did}/").status_code, 403)
        self.assertEqual(c.get(f"/api/decks/?course={course.id}").json(), [])


class LectureDeckAccessNotesCoverTests(TestCase):
    """উস্তাদ শুধু নিজের কোর্স; শিক্ষার্থী স্লাইড পায় না, পড়ানো হলে নোট পায়; স্লাইড শেষে টপিক টিক।"""
    def test_flow(self):
        from .models import Course, LectureDeck, Lecture, LectureTopic, LessonSection, TopicCoverage
        mk = lambda n, r, **k: User.objects.create_user(username=n, password="x12345678", role=r, name_bn=n, **k)
        d, t1, t2 = mk("dir", "director"), mk("t1", "teacher"), mk("t2", "teacher")
        s1, s2 = mk("s1", "student", teacher=t1), mk("s2", "student", teacher=t2)
        mine, other = Course.objects.create(name="Easy Noorani Qaida", teacher=t1), Course.objects.create(name="Other")
        mine.students.add(s1, s2)
        a = LectureDeck.objects.create(course=mine, no=1, data=b"PK1", note="Note one", topics="Topic A\nTopic B")
        b = LectureDeck.objects.create(course=other, no=1, data=b"PK2")
        c = APIClient()
        c.force_authenticate(t1)
        self.assertEqual([x["id"] for x in c.get("/api/decks/").json()], [a.id])
        self.assertEqual(c.get(f"/api/decks/{b.id}/").status_code, 403)
        self.assertEqual(c.get(f"/api/decks/{a.id}/").content, b"PK1")
        self.assertEqual(c.patch(f"/api/decks/{a.id}/", {"note": "x"}, format="json").status_code, 403)
        # কোনো Lecture Plan নেই → স্লাইডের নিজের টপিক; উস্তাদ শুধু নিজের শিক্ষার্থী পান
        g = c.get(f"/api/decks/{a.id}/cover/").json()
        self.assertEqual(g["deck_topics"], ["Topic A", "Topic B"])
        self.assertEqual([s["id"] for s in g["students"]], [s1.id])
        r = c.post(f"/api/decks/{a.id}/cover/", {"student_ids": [s1.id, s2.id], "deck_topics": ["Topic A"]}, format="json")
        self.assertEqual(r.json()["students"], 1)
        c.force_authenticate(s1)
        self.assertEqual(c.get(f"/api/decks/{a.id}/").status_code, 403)
        self.assertEqual(c.get("/api/decks/").json(), [])
        n = c.get("/api/decks/notes/").json()
        self.assertEqual((n[0]["note"], n[0]["topics"]), ("Note one", ["Topic A"]))
        c.force_authenticate(s2)
        self.assertEqual(c.get("/api/decks/notes/").json(), [])
        # Lecture Plan-এর টপিক থাকলে সেখানেই কভার বসে
        lec = Lecture.objects.create(course=mine, no=1, title="holder")
        sec = LessonSection.objects.create(course=mine, name="Lecture 1")
        LectureTopic.objects.create(lecture=lec, section=LessonSection.objects.create(course=mine, name="Lecture 12"), text="Not today")
        tp = LectureTopic.objects.create(lecture=lec, section=sec, text="Alif to Jeem")
        c.force_authenticate(d)
        self.assertEqual(c.get(f"/api/decks/{b.id}/").content, b"PK2")
        g = c.get(f"/api/decks/{a.id}/cover/").json()
        self.assertEqual(([t["id"] for t in g["plan_topics"]], g["deck_topics"], len(g["students"])), ([tp.id], [], 2))
        c.post(f"/api/decks/{a.id}/cover/", {"student_ids": [s2.id], "topic_ids": [tp.id]}, format="json")
        self.assertEqual(TopicCoverage.objects.get(topic=tp, student=s2).covered, "covered")
        self.assertEqual(c.patch(f"/api/decks/{a.id}/", {"note": "New"}, format="json").json()["note"], "New")


class EasyQaidaPlanSeedTests(TestCase):
    def test_seed_replaces_regular_plan_keeps_trial(self):
        import importlib
        from django.apps import apps
        from .models import Course, Lecture, LectureTopic, LessonSection, SyllabusItem, CourseSyllabusSheet
        c = Course.objects.create(name="Easy Noorani Qaida")
        lec = Lecture.objects.create(course=c, no=1, title="holder")
        old = LessonSection.objects.create(course=c, name="Old heading")
        LectureTopic.objects.create(lecture=lec, section=old, text="old")
        tr = LessonSection.objects.create(course=c, name="Trial", is_trial=True)
        LectureTopic.objects.create(lecture=lec, section=tr, text="trial topic")
        SyllabusItem.objects.create(course=c, lesson="old item")
        importlib.import_module("core.migrations.0060_easy_qaida_course_plan").forwards(apps, None)
        self.assertFalse(LessonSection.objects.filter(pk=old.pk).exists())
        self.assertTrue(LectureTopic.objects.filter(text="trial topic").exists())
        self.assertEqual(SyllabusItem.objects.filter(course=c).count(), 0)
        secs = LessonSection.objects.filter(course=c, is_trial=False)
        self.assertEqual(secs.count(), 67)
        self.assertEqual(LectureTopic.objects.filter(section__name="Lecture 1").count(), 5)
        self.assertEqual(len(CourseSyllabusSheet.objects.get(course=c).rows), 67)


class LectureDeckFindTests(TestCase):
    """টপিকে ক্লিক: উস্তাদ পান উস্তাদের স্লাইড, শিক্ষার্থী পায় নিজের স্লাইড; অন্য কোর্সের শিক্ষার্থী কিছুই পায় না।"""
    def test_find(self):
        from .models import Course, LectureDeck
        mk = lambda n, r, **k: User.objects.create_user(username=n, password="x12345678", role=r, name_bn=n, **k)
        t, s, x = mk("t", "teacher"), mk("s", "student"), mk("x", "student")
        c = Course.objects.create(name="Easy Noorani Qaida", teacher=t)
        c.students.add(s)
        td = LectureDeck.objects.create(course=c, no=3, data=b"PKT")
        sd = LectureDeck.objects.create(course=c, no=3, data=b"PKS", audience="student")
        a = APIClient()
        a.force_authenticate(t)
        self.assertEqual(a.get(f"/api/decks/find/?course={c.id}&no=3").json()["id"], td.id)
        self.assertEqual(a.get(f"/api/decks/find/?course={c.id}&no=4").status_code, 404)
        a.force_authenticate(s)
        r = a.get(f"/api/decks/find/?course={c.id}&no=3").json()
        self.assertEqual(r["id"], sd.id)
        self.assertEqual(a.get(f"/api/decks/{sd.id}/").content, b"PKS")
        self.assertEqual(a.get(f"/api/decks/{td.id}/").status_code, 403)
        a.force_authenticate(x)
        self.assertEqual(a.get(f"/api/decks/find/?course={c.id}&no=3").status_code, 403)
        self.assertEqual(a.get(f"/api/decks/{sd.id}/").status_code, 403)
