"""Noorani Qaida Course — টপিকের নাম এখন কোর্সের বইয়ের হুবহু শিরোনাম (মালিক: "লেকচারের টপিক এ কোর্সের বই থেকে নিতে হবে",
২০২৬-১১-১৯)। plan_seed/noorani_qaida_plan.json হালনাগাদ; 0082-এর একই কাজ আবার চালানো হয় — এই কোর্সের নিয়মিত প্ল্যান মুছে নতুন বসে
(অনুমতি আগেই: "পুরনো মুছে নতুন বসাও"), ট্রায়াল ও অন্য কোর্সে হাত নেই।"""
import importlib

from django.db import migrations


def forwards(apps, schema_editor):
    importlib.import_module("core.migrations.0082_noorani_qaida_course_plan").forwards(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [("core", "0082_noorani_qaida_course_plan")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
