# -*- coding: utf-8 -*-
"""সূরা আন-নাসের দারস "Memorized Surah" হেডিংয়ের টপিকে বসানো।

কাউসারের মতোই — এই টপিকের নামে কোনো দারস-নম্বর নেই, তাই নম্বর ধরে
খোঁজা যায় না। নাম ধরেই মেলাতে হয়।

⚠️ "nas" শব্দটি খুব ছোট, একা মেলালে অন্য নামের ভেতরেও বসে যেতে পারে।
তাই কেবল পূর্ণ রূপগুলোই ধরা হয় — "an-nas", "an nas", "annas", বা আরবি
"الناس"। খালি "nas" কখনো নয়।

⚠️ নিরাপত্তা — যে টপিকে আগে থেকেই স্ক্রিপ্ট আছে, সেটি এড়িয়ে যায়।
মানানসই টপিক না পেলে চুপচাপ বাদ। বারবার চললেও নিরাপদ।
"""
from django.db import migrations

MARKS = ("الناس", "an-nas", "an nas", "annas", "an‑nas",
         "আন-নাস", "আন নাস", "আন্‌-নাস", "আননাস")


def fill(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    LectureTopic = apps.get_model("core", "LectureTopic")

    if Lesson.objects.filter(title_ar=SAMPLES["nas"]["title_ar"]).exists():
        return                       # আগেই বসে গেছে

    for t in LectureTopic.objects.all().order_by("lecture__no", "order", "id"):
        low = (t.text or "").lower()
        if not any(m.lower() in low for m in MARKS):
            continue
        if Lesson.objects.filter(topic=t).exists():
            continue                 # পরিচালকের স্ক্রিপ্ট আছে — ছোঁব না
        lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                  t.lecture.course, "nas", topic=t)
        if lesson.title != t.text:   # পরিচালকের দেওয়া নামটাই থাকুক
            lesson.title = t.text
            lesson.save(update_fields=["title"])
        if not (t.content or "").strip():
            html = summary_html(lesson)
            if html:
                t.content = html
                t.save(update_fields=["content"])
        return


class Migration(migrations.Migration):

    dependencies = [("core", "0046_seed_any_missing_lesson")]

    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
