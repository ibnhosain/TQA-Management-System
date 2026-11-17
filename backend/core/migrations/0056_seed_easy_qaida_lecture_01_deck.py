# -*- coding: utf-8 -*-
"""Easy Noorani Qaida — লেকচার ১-এর স্লাইড (.pptx) Lecture Slides-এ বসানো (মালিকের নির্দেশ, ২০২৬-১১-১৭)।
ফাইল: core/deck_seed/ (মালিকের Drive-এর "Lecture 01 - Easy Noorani Qaida.pptx"-এর হুবহু কপি)।
একই কোর্স ও লেকচার নম্বরে আগে কিছু থাকলে বদলে যায়।"""
import os
from django.db import migrations

FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deck_seed", "easy-noorani-qaida-lecture-01.pptx")


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    LectureDeck = apps.get_model("core", "LectureDeck")
    course = Course.objects.filter(name__iexact="Easy Noorani Qaida").first() or Course.objects.filter(name__icontains="easy").first()
    if course is None or not os.path.exists(FILE):
        return
    data = open(FILE, "rb").read()
    LectureDeck.objects.update_or_create(course=course, no=1, defaults={
        "title": "Day 1", "filename": "Lecture 01 - Easy Noorani Qaida.pptx", "size": len(data), "data": data})


class Migration(migrations.Migration):
    dependencies = [("core", "0055_lecture_deck")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
