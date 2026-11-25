"""Noorani Qaida Course — বইয়ের যে অংশ আগে স্লাইডে আসেনি, সেগুলোসহ ২১টি লেকচার (উস্তাদ + শিক্ষার্থী) নতুন করে, deck_seed/ থেকে:
প্রতিটি সূরার "When do we read it?", দুআ ও আদবের লেসন ১–১২-এর "Think and Answer", আর লেসন ১৩ ও ১৫-এর "My Good Deeds"।"""
import importlib

from django.db import migrations

NOS = (3, 4, 6, 8, 10, 11, 12, 13, 16, 17, 19, 21, 23, 24, 26, 28, 30, 33, 36, 39, 44)


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, NOS)


class Migration(migrations.Migration):
    dependencies = [("core", "0099_refresh_noorani_lectures_1_to_10")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
