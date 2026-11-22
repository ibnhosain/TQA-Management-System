"""Noorani Qaida Course — লেকচার ১৬–২০-এর স্লাইড (উস্তাদ + শিক্ষার্থী), deck_seed/ থেকে।
একই লেকচারের পুরনো স্লাইড থাকলে নতুনটা দিয়ে বদলায়।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, range(16, 21))


class Migration(migrations.Migration):
    dependencies = [("core", "0092_seed_noorani_lectures_11_to_15")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
