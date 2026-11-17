"""Easy Noorani Qaida — লেকচার ২-এর স্লাইড ও শিক্ষার্থীর নোট (মালিকের Drive-এর ফাইলের হুবহু কপি, deck_seed/)।
পরিচালক আগে নিজে লেকচার ২ আপলোড করে থাকলে তাঁর ফাইল বদলানো হয় না — শুধু নোট খালি থাকলে নোট বসে।"""
import os

from django.db import migrations

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deck_seed")
DECK = os.path.join(SEED, "easy-noorani-qaida-lecture-02.pptx")
NOTE = os.path.join(SEED, "easy-noorani-qaida-lecture-02-note.txt")
TOPICS = """Qaida — Open my heart dua + row 2: Haa, Kha, Dal, Dhal, Ra
Surah — Al-Fatihah verse 2
Duas & Manners — If I forget Bismillah + after eating
Salah Duas — Thana, first half
Writing — Warm-up: tall lines, boats, cups"""


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    LectureDeck = apps.get_model("core", "LectureDeck")
    course = Course.objects.filter(name__iexact="Easy Noorani Qaida").first() or Course.objects.filter(name__icontains="easy").first()
    if course is None or not os.path.exists(DECK):
        return
    note = open(NOTE, encoding="utf-8").read().strip() if os.path.exists(NOTE) else ""
    d = LectureDeck.objects.filter(course=course, no=2).first()
    if d is None:
        data = open(DECK, "rb").read()
        LectureDeck.objects.create(course=course, no=2, title="Day 2", filename="Lecture 02 - Easy Noorani Qaida.pptx",
                                   size=len(data), data=data, note=note, topics=TOPICS)
    elif not d.note:
        d.note = note
        d.save(update_fields=["note"])


class Migration(migrations.Migration):
    dependencies = [("core", "0060_easy_qaida_course_plan")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
