# -*- coding: utf-8 -*-
"""🪔 Little Mu'min Library — বইয়ের তাক পরিচালক বসান; শিক্ষার্থী শুধু দেখে।"""
from django.test import TestCase
from rest_framework.test import APIClient

DRIVE = "https://drive.google.com/file/d/abc/view?usp=sharing"


class LibraryShelf(TestCase):
    def setUp(self):
        from core.models import User
        self.director = User.objects.create(username="d", role="director", name_bn="D")
        self.student = User.objects.create(username="s", role="student", name_bn="S")

    def as_(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def test_director_adds_drive_book_straight_onto_a_shelf(self):
        r = self.as_(self.director).post(
            "/api/books/", {"name": "Allah — Aqeedah for Little Ones", "link": DRIVE,
                            "library_shelf": "aqeedah"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual((r.data["file"], r.data["library_shelf"]), (DRIVE, "aqeedah"))

    def test_shelf_is_optional_and_unknown_shelf_is_refused(self):
        c = self.as_(self.director)
        r = c.post("/api/books/", {"name": "A", "link": DRIVE}, format="json")
        self.assertEqual(r.data["library_shelf"], "")
        r = c.post("/api/books/", {"name": "B", "link": DRIVE, "library_shelf": "teachers"},
                   format="json")
        self.assertEqual(r.status_code, 400)

    def test_director_moves_a_book_but_student_cannot(self):
        from core.models import AcademicBook
        b = AcademicBook.objects.create(name="Tajweed", file=DRIVE)
        r = self.as_(self.director).patch(f"/api/books/{b.id}/", {"library_shelf": "quran"},
                                          format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(self.as_(self.director).patch(
            f"/api/books/{b.id}/", {"library_shelf": "nowhere"}, format="json").status_code, 400)
        self.assertEqual(self.as_(self.student).patch(
            f"/api/books/{b.id}/", {"library_shelf": "more"}, format="json").status_code, 403)
        b.refresh_from_db()
        self.assertEqual(b.library_shelf, "quran")

    def test_student_sees_shelf_but_not_teacher_guides(self):
        from core.models import AcademicBook
        AcademicBook.objects.create(name="Kids book", file=DRIVE, library_shelf="stories")
        AcademicBook.objects.create(name="Teacher Guide", file=DRIVE, staff_only=True)
        data = self.as_(self.student).get("/api/books/").data  # সিড-মাইগ্রেশনের বইও থাকে
        mine = [(b["name"], b["library_shelf"]) for b in data
                if b["name"] in ("Kids book", "Teacher Guide")]
        self.assertEqual(mine, [("Kids book", "stories")])
