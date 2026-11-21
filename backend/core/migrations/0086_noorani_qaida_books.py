"""Noorani Qaida Course-এর বই — Easy Noorani Qaida-র (0050/0053/0054) হুবহু একই ধরনে (মালিকের নির্দেশ, ২০২৬-১১-২১)।
বইগুলো মালিকের Drive ফোল্ডার 1L4B28XlGdEjnUqbfElUkilzCkr6LBX7W-এ (লিংকে সবাই দেখতে পারে)।
- কোর্স থেকে আগের সব একাডেমিক বই সরানো হয় (বই মোছা হয় না — অন্য কোর্সে থাকতে পারে)।
- ৫টি ছাত্রের বই + ২টি শিক্ষক নির্দেশিকা (staff_only — কেবল পরিচালক, এডমিন ও উস্তাদ দেখেন)।"""
import importlib

from django.db import migrations

D = "https://drive.google.com/file/d/{}/view?usp=sharing"
BOOKS = [  # (নাম, Drive ফাইল আইডি, কেবল শিক্ষকদের জন্য)
    ("Easy Noorani Qaida — Step 02 (Ages 7-12)", "1uRLLtc8G8FSmBfNRE3jZ2lZrnmnWozZL", False),
    ("Memorized Surah — Az-Zalzalah to An-Nas (Ages 7-12)", "1g7vWJDGG5BrOKU9c4gGzDxTMsxo07ybi", False),
    ("Tajweed and Makhraj (Ages 7-12)", "1vVuWe_5W1sWXA0M7IEiaN7d8wM6O4B3e", False),
    ("Islamic Duas, Manners and Values (Ages 7-12)", "1y2D04oSyYqCotK7O3XzciyC_pFJ_PWqb", False),
    ("My Arabic Writing Book — Step 2 (Ages 7-12) — print on A4", "1ScpJKq7jiTBzBWItQSK5SPr2NKq2lzhV", False),
    ("Teacher Guide — Memorized Surah (Ages 7-12) (Teachers only)", "1xpgQ_eKcf2uuz4k0TtsWIhJ-k7sW8nOd", True),
    ("Teacher Guide — Arabic Writing Step 2 (Ages 7-12) (Teachers only)", "1E9pxtNUTjjglFmTgw2eG92-q58hmAiGO", True),
]


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    AcademicBook = apps.get_model("core", "AcademicBook")
    course = importlib.import_module("core.migrations.0082_noorani_qaida_course_plan").noorani_course(Course)
    if course is None:
        return
    course.books.clear()
    for name, fid, staff in BOOKS:
        book, _ = AcademicBook.objects.get_or_create(name=name, defaults={"file": D.format(fid), "staff_only": staff})
        book.file, book.staff_only = D.format(fid), staff
        book.save()
        course.books.add(book)


class Migration(migrations.Migration):
    dependencies = [("core", "0085_scheduledjob")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
