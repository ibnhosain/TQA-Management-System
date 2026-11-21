"""Noorani Qaida Course-এর লেকচার প্ল্যান মাইগ্রেশন (0082) — Easy Noorani Qaida-র ফরম্যাটে।"""
import importlib

from django.apps import apps as django_apps
from django.test import TestCase

from core.models import Course, CourseSyllabusSheet, Lecture, LectureTopic, LessonSection


def run_migration():
    m = importlib.import_module("core.migrations.0082_noorani_qaida_course_plan")
    m.forwards(django_apps, None)


class NooraniPlan(TestCase):
    def setUp(self):
        self.easy = Course.objects.create(name="Easy Noorani Qaida")
        self.course = Course.objects.create(name="Noorani Qaida")
        lec = Lecture.objects.create(course=self.course, no=1, title="old")
        old = LessonSection.objects.create(course=self.course, name="Old heading", order=1, is_trial=False)
        trial = LessonSection.objects.create(course=self.course, name="Trial", order=0, is_trial=True)
        LectureTopic.objects.create(lecture=lec, section=old, text="old topic")
        LectureTopic.objects.create(lecture=lec, section=trial, text="trial topic")
        easy_sec = LessonSection.objects.create(course=self.easy, name="Lecture 1", order=1, is_trial=False)
        LectureTopic.objects.create(lecture=Lecture.objects.create(course=self.easy, no=1, title="e"), section=easy_sec, text="easy topic")

    def test_the_new_plan_replaces_the_old(self):
        run_migration()
        secs = LessonSection.objects.filter(course=self.course, is_trial=False).order_by("order")
        self.assertEqual(secs.count(), 45)
        self.assertEqual(secs.first().name, "Lecture 1")
        self.assertEqual(LectureTopic.objects.filter(section=secs.first()).count(), 5)
        self.assertFalse(LectureTopic.objects.filter(text="old topic").exists())
        self.assertTrue(LectureTopic.objects.filter(text="trial topic").exists(), "ট্রায়ালের টপিক মোছা উচিত নয়")
        sheet = CourseSyllabusSheet.objects.get(course=self.course)
        self.assertEqual(len(sheet.headers), 6)
        self.assertEqual(len(sheet.rows), 45)

    def test_easy_noorani_qaida_is_not_touched(self):
        run_migration()
        self.assertTrue(LectureTopic.objects.filter(text="easy topic").exists())
        self.assertEqual(LessonSection.objects.filter(course=self.easy).count(), 1)
        self.assertFalse(CourseSyllabusSheet.objects.filter(course=self.easy).exists())


class NooraniBooks(TestCase):
    def test_the_course_gets_its_own_books(self):
        from core.models import AcademicBook
        easy = Course.objects.create(name="Easy Noorani Qaida")
        course = Course.objects.create(name="Noorani Qaida")
        old = AcademicBook.objects.create(name="Old book", file="x")
        course.books.add(old); easy.books.add(old)
        importlib.import_module("core.migrations.0086_noorani_qaida_books").forwards(django_apps, None)
        names = sorted(b.name for b in course.books.all())
        self.assertEqual(len(names), 7)
        self.assertNotIn("Old book", names)
        self.assertEqual(course.books.filter(staff_only=True).count(), 2)
        self.assertTrue(AcademicBook.objects.filter(name="Old book").exists(), "পুরনো বই মোছা উচিত নয়")
        self.assertIn(old, easy.books.all(), "Easy কোর্সের বই বদলানো উচিত নয়")


class NooraniDecks(TestCase):
    def test_lectures_1_to_5_get_teacher_and_student_slides(self):
        from core.models import LectureDeck
        easy = Course.objects.create(name="Easy Noorani Qaida")
        course = Course.objects.create(name="Noorani Qaida")
        importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").forwards(django_apps, None)
        decks = LectureDeck.objects.filter(course=course)
        self.assertEqual(decks.count(), 10)
        self.assertEqual(sorted(set(decks.values_list("no", flat=True))), [1, 2, 3, 4, 5])
        d = decks.get(no=1, audience="student")
        self.assertEqual(d.filename, "Lecture 01 - Noorani Qaida Course - Student.pptx")
        self.assertTrue(bytes(d.data[:2]) == b"PK", "pptx (zip) হওয়া উচিত")
        self.assertFalse(LectureDeck.objects.filter(course=easy).exists(), "Easy কোর্সে স্লাইড যাওয়া উচিত নয়")
