"""Noorani Qaida Course — লেকচার ৩১–৩৫-এর স্লাইড (উস্তাদ + শিক্ষার্থী), deck_seed/ থেকে।
সাথে লেকচার ২২, ২৩ ও ৩০ নতুন করে: শিক্ষার্থীর পাতায় ঠিক নির্দেশনা, রিভিশন খেলায় সেদিনের উদাহরণ,
ছোট তাজভীদ লেসনের রিভিশনে পুরো লেসন। একই লেকচারের পুরনো স্লাইড নতুনটা দিয়ে বদলায়।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0088_seed_noorani_lectures_1_to_5").seed(apps, (22, 23, 30, 31, 32, 33, 34, 35))


class Migration(migrations.Migration):
    dependencies = [("core", "0095_seed_noorani_lectures_26_to_30")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
