# -*- coding: utf-8 -*-
"""Easy Noorani Qaida কোর্সে নতুন বই: My Salah Duas — Hanafi (Ages 4-6)
(মালিক Drive-এ রেখেছেন, লিংকে খোলা; মালিকের নির্দেশ, ২০২৬-১১-১৭)। সবাই দেখবে (staff_only নয়)।"""
from django.db import migrations

NAME = "My Salah Duas — Hanafi (Ages 4-6)"
LINK = "https://drive.google.com/file/d/1wxvJEa6kMib0FfwCC0rTDxYz8CbuPfJx/view?usp=sharing"


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    AcademicBook = apps.get_model("core", "AcademicBook")
    course = Course.objects.filter(name__iexact="Easy Noorani Qaida").first() \
        or Course.objects.filter(name__icontains="easy").first()
    book, _ = AcademicBook.objects.get_or_create(name=NAME, defaults={"file": LINK, "staff_only": False})
    book.file, book.staff_only = LINK, False
    book.save()
    if course is not None:
        course.books.add(book)


def backwards(apps, schema_editor):
    apps.get_model("core", "AcademicBook").objects.filter(name=NAME).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0053_easy_qaida_books_owner_drive")]
    operations = [migrations.RunPython(forwards, backwards)]
