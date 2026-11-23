"""Noorani Qaida Course — লেকচার ২৬–৩০-এর স্লাইড (উস্তাদ + শিক্ষার্থী), deck_seed/ থেকে।
লেকচার ৩০ থেকে তাজভীদ অংশ রিভিশন (প্রতিদিন বইয়ের একটি লেসন)। একই লেকচারের পুরনো স্লাইড নতুনটা দিয়ে বদলায়।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, range(26, 31))


class Migration(migrations.Migration):
    dependencies = [("core", "0094_seed_noorani_lectures_21_to_25")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
