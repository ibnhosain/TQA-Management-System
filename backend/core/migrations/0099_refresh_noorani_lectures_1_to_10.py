"""Noorani Qaida Course — লেকচার ১–১০-এর স্লাইড (উস্তাদ + শিক্ষার্থী) নতুন করে, deck_seed/ থেকে।
এগুলো পরের সংশোধনগুলোর আগে বানানো ছিল: পড়ার লাইনের শব্দ এখন আলাদা ঘরে, রিভিশন খেলার প্রশ্ন ও উত্তর ঠিক
(লেখার উত্তরে আসল শব্দ, "Tell me"-তে গল্প/বিষয়ের নাম)।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, range(1, 11))


class Migration(migrations.Migration):
    dependencies = [("core", "0098_seed_noorani_lectures_41_to_45")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
