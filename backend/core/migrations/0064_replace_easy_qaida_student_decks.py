"""Easy Noorani Qaida — লেকচার ১ ও ২-এর শিক্ষার্থীর স্লাইড বদল (মালিকের নির্দেশ, ২০২৬-১১-১৭):
প্রতিটি পাতার নিচে "How to practise", কোনো অ্যানিমেশন নেই। ফাইল deck_seed/-এ (Slides ফোল্ডারের কপি)।"""
import os

from django.db import migrations

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deck_seed")
FILES = {1: "easy-noorani-qaida-lecture-01-student.pptx", 2: "easy-noorani-qaida-lecture-02-student.pptx"}


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    LectureDeck = apps.get_model("core", "LectureDeck")
    course = Course.objects.filter(name__iexact="Easy Noorani Qaida").first() or Course.objects.filter(name__icontains="easy").first()
    if course is None:
        return
    for no, name in FILES.items():
        path = os.path.join(SEED, name)
        if not os.path.exists(path):
            continue
        data = open(path, "rb").read()
        LectureDeck.objects.update_or_create(
            course=course, no=no, audience="student",
            defaults={"title": f"Day {no} · My Practice", "filename": f"Lecture {no:02d} - Easy Noorani Qaida - Student.pptx",
                      "size": len(data), "data": data})


class Migration(migrations.Migration):
    dependencies = [("core", "0063_seed_easy_qaida_student_decks")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
