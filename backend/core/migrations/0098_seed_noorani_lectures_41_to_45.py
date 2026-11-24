"""Noorani Qaida Course — লেকচার ৪১–৪৫-এর স্লাইড (উস্তাদ + শিক্ষার্থী), deck_seed/ থেকে — কোর্সের শেষ ৫টি লেকচার।
লেকচার ৪৫: কায়দা ও সূরায় শিশু নিজের সবচেয়ে কঠিন লেসন/ধাপ বেছে আবার পড়ে।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, range(41, 46))


class Migration(migrations.Migration):
    dependencies = [("core", "0097_seed_noorani_lectures_36_to_40")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
