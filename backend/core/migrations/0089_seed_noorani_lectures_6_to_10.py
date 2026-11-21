"""Noorani Qaida Course — লেকচার ৬–১০-এর স্লাইড (উস্তাদ + শিক্ষার্থী), আর লেকচার ১–৫ নতুন করে
(টেবিলে আরবির জায়গা, ছোট আয়াত বড় করে, পাতা ভাগ আরও সমান)। একই লেকচারের পুরনো স্লাইড নতুনটা দিয়ে বদলায়।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, range(1, 11))


class Migration(migrations.Migration):
    dependencies = [("core", "0088_seed_noorani_lectures_1_to_5")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
