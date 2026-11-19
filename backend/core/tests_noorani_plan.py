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
