# -*- coding: utf-8 -*-
"""Easy Noorani Qaida কোর্সের বই বদল (মালিকের নির্দেশ, ২০২৬-১১-১১)।

- AcademicBook-এ নতুন ঘর `staff_only`: True হলে বইটি কেবল পরিচালক, এডমিন ও উস্তাদ দেখেন।
- কোর্স থেকে আগের সব একাডেমিক বই সরানো হয় (বইগুলো মোছা হয় না — অন্য কোর্সেও আছে)।
- একাডেমির নিজস্ব ৪টি বই আর ২টি শিক্ষক নির্দেশিকা (staff_only) Google Drive লিংকসহ যোগ হয়।
"""
from django.db import migrations, models

D = "https://drive.google.com/file/d/{}/view?usp=sharing"
BOOKS = [  # (নাম, Drive ফাইল আইডি, কেবল শিক্ষকদের জন্য)
    ("Easy Noorani Qaida — Step One (Ages 4-6)", "1HVw52fbLNw4efomhzQs6Mega2Z_9ikAh", False),
    ("Memorized Surah — My First Surahs (Ages 4-6)", "14DMrHdz0JkHwXeJ_zMc5518-isP9Aldb", False),
    ("Islamic Duas, Manners and Values (Ages 4-6)", "1jC3Kg4et2fBquOxJDA7alG_Mcy1RMwXO", False),
    ("My First Arabic Writing Book (Ages 4-6) — print on A4", "1iUjpFQtn8WBXT4SKXrXMPL1c75imYymd", False),
    ("Teacher Guide — Memorized Surah Techniques (Teachers only)", "1BAg3q20mRs7dobWcLQvTvn2w9WjdVoi0", True),
    ("Teacher Guide — Teaching Arabic Writing on Zoom (Teachers only)", "1FZaPRyRHYVryBDFKsJVEgoqDHMB_tqx4", True),
]


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    AcademicBook = apps.get_model("core", "AcademicBook")
    course = Course.objects.filter(name__iexact="Easy Noorani Qaida").first() \
        or Course.objects.filter(name__icontains="easy").first()
    if course is None:          # নতুন/খালি ডেটাবেজ — কিছু করার নেই
        return
    course.books.clear()
    for name, fid, staff in BOOKS:
        book, _ = AcademicBook.objects.get_or_create(name=name, defaults={"file": D.format(fid), "staff_only": staff})
        book.file, book.staff_only = D.format(fid), staff
        book.save()
        course.books.add(book)


class Migration(migrations.Migration):
    dependencies = [("core", "0049_nas_piece_order")]
    operations = [
        migrations.AddField(model_name="academicbook", name="staff_only",
                            field=models.BooleanField(default=False, verbose_name="কেবল শিক্ষক ও পরিচালকের জন্য")),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
