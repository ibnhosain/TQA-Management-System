"""Easy Noorani Qaida — লেকচার ১ ও ২-এর শিক্ষার্থীর পড়া-প্র্যাকটিসের স্লাইড (মালিকের Drive-এর ফাইলের হুবহু কপি, deck_seed/)।
আগে থেকে শিক্ষার্থীর স্লাইড থাকলে বদলানো হয় না।"""
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
        if not os.path.exists(path) or LectureDeck.objects.filter(course=course, no=no, audience="student").exists():
            continue
        data = open(path, "rb").read()
        LectureDeck.objects.create(course=course, no=no, audience="student", title=f"Day {no} · My Practice",
                                   filename=f"Lecture {no:02d} - Easy Noorani Qaida - Student.pptx", size=len(data), data=data)


class Migration(migrations.Migration):
    dependencies = [("core", "0062_lecturedeck_audience")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
