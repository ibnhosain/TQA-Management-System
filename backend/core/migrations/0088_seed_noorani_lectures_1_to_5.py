"""Noorani Qaida Course (৭–১২) — লেকচার ১–৫: উস্তাদের স্লাইড ও শিক্ষার্থীর স্লাইড (Slides ফোল্ডারের কপি, deck_seed/)।
স্লাইড কোর্সের ৫টি বই থেকে সরাসরি (Books/_একাডেমিক-বই-টুলস/slides/lectures_noorani/engine.js)।
একই লেকচার ও একই ধরনের স্লাইড আগে থাকলে নতুনটা দিয়ে বদলায়। কোর্স খোঁজা 0082-এর মতোই (Easy বাদ)।"""
import importlib
import os

from django.db import migrations

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deck_seed")
NOS = (1, 2, 3, 4, 5)


def seed(apps, nos):
    Course = apps.get_model("core", "Course")
    LectureDeck = apps.get_model("core", "LectureDeck")
    course = importlib.import_module("core.migrations.0082_noorani_qaida_course_plan").noorani_course(Course)
    if course is None:
        return
    for no in nos:
        for aud, suffix, title in (("teacher", "", f"Day {no}"), ("student", "-student", f"Day {no} · My Practice")):
            path = os.path.join(SEED, f"noorani-qaida-lecture-{no:02d}{suffix}.pptx")
            if not os.path.exists(path):
                continue
            data = open(path, "rb").read()
            fname = f"Lecture {no:02d} - Noorani Qaida Course{' - Student' if suffix else ''}.pptx"
            LectureDeck.objects.update_or_create(course=course, no=no, audience=aud,
                                                 defaults={"title": title, "filename": fname, "size": len(data), "data": data})


def forwards(apps, schema_editor):
    seed(apps, NOS)


class Migration(migrations.Migration):
    dependencies = [("core", "0087_wamessage_template_params")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
