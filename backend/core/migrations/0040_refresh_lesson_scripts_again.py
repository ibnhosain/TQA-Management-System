# -*- coding: utf-8 -*-
"""দারস ও প্ল্যান আবার হালনাগাদ — ০০৩৯-এর সংশোধিত নিয়মে।

কেন আবার: ০০৩৯-এ দারস খোঁজার একটি ফলব্যাক ছিল যা "একই ধরনের যেকোনো
দারস" ধরত — তাতে পরিচালকের নিজের হাতে লেখা দারসও মুছে যেতে পারত।
সেটি সরানো হয়েছে। কিন্তু ০০৩৯ একবার চলে গেলে আর চলে না, তাই সংশোধিত
নিয়মে আরেকবার চালানো দরকার।

⚠️ বারবার চললেও নিরাপদ — একই লেখাই আবার বসে, আর দারসের সারি না মোছায়
শিক্ষার্থীদের অগ্রগতি অক্ষত থাকে।
"""
from django.db import migrations

def again(apps, schema_editor):
    import importlib
    m = importlib.import_module(
        "core.migrations.0039_refresh_lesson_scripts")
    m.refresh(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [("core", "0039_refresh_lesson_scripts")]

    operations = [migrations.RunPython(again, migrations.RunPython.noop)]
