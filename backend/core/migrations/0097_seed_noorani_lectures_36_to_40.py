"""Noorani Qaida Course — লেকচার ৩৬–৪০-এর স্লাইড (উস্তাদ + শিক্ষার্থী), deck_seed/ থেকে।
নতুন: লেখার রিভিশন (৩৮ থেকে, প্রতিদিন বইয়ের এক তালিকার ৫টি শব্দ না দেখে লেখা) ও সূরার রিভিশন (৩৯ থেকে, প্রতিদিন এক ধাপ)।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, range(36, 41))


class Migration(migrations.Migration):
    dependencies = [("core", "0096_seed_noorani_lectures_31_to_35")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
