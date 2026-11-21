# -*- coding: utf-8 -*-
"""🪔 Little Mu'min Library — একাডেমিক বই থেকে আলাদা তালিকা।
পরিচালক/এডমিন বই দেন ও তাক বসান; যেকোনো ভূমিকার যে কেউ সব বই পড়ে।"""
from django.test import TestCase
from rest_framework.test import APIClient

DRIVE = "https://drive.google.com/file/d/abc/view?usp=sharing"


class LibraryBooks(TestCase):
    def setUp(self):
        from core.models import User
        mk = lambda u, r: User.objects.create(username=u, role=r, name_bn=u)
        self.director, self.admin = mk("d", "director"), mk("a", "admin")
        self.teacher, self.student, self.trial = mk("t", "teacher"), mk("s", "student"), mk("g", "trial")

    def as_(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def add(self, user, **kw):
        body = {"title": "Allah — Aqeedah for Little Ones (Ages 5-8)", "link": DRIVE, "cls": "aqeedah", **kw}
        return self.as_(user).post("/api/library-books/", body, format="json")

    def test_director_and_admin_add_books_onto_a_shelf(self):
        for u in (self.director, self.admin):
            r = self.add(u)
            self.assertEqual(r.status_code, 201, r.data)
            self.assertEqual((r.data["cls"], r.data["link"]), ("aqeedah", DRIVE))

    def test_shelf_must_be_a_real_library_shelf(self):
        self.assertEqual(self.add(self.director, cls="Tajweed").status_code, 400)
        self.assertEqual(self.add(self.director, cls="").status_code, 400)

    def test_everyone_reads_every_book_whatever_role_or_course(self):
        self.add(self.director)
        for u in (self.teacher, self.student, self.trial):
            data = self.as_(u).get("/api/library-books/").data
            self.assertEqual([b["cls"] for b in data], ["aqeedah"], u.role)

    def test_only_director_and_admin_change_the_library(self):
        bid = self.add(self.director).data["id"]
        for u in (self.teacher, self.student, self.trial):
            self.assertEqual(self.add(u).status_code, 403, u.role)
            self.assertEqual(self.as_(u).patch(f"/api/library-books/{bid}/", {"cls": "more"},
                                               format="json").status_code, 403)
        r = self.as_(self.director).patch(f"/api/library-books/{bid}/", {"cls": "stories"}, format="json")
        self.assertEqual((r.status_code, r.data["cls"]), (200, "stories"))
        self.assertEqual(self.as_(self.admin).delete(f"/api/library-books/{bid}/").status_code, 204)

    def test_academic_books_are_not_in_the_library(self):
        from core.models import AcademicBook
        AcademicBook.objects.create(name="Noorani Qaida", file=DRIVE)
        self.assertEqual(self.as_(self.student).get("/api/library-books/").data, [])
