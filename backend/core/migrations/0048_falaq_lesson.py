# -*- coding: utf-8 -*-
"""সূরা আল-ফালাকের দারস "Memorized Surah" হেডিংয়ের টপিকে বসানো।

কাউসার ও আন-নাসের মতোই — এই টপিকের নামে কোনো দারস-নম্বর নেই, তাই নম্বর
ধরে খোঁজা যায় না। নাম ধরেই মেলাতে হয়।

⚠️ "ফালাক" শব্দটি অন্য কোনো সূরার নামের ভেতরে নেই, তাই একা মেলালেও
বিপদ নেই — আন-নাসের "nas"-এর মতো ছোট নয়। তবু আরবি "الفلق" আর পূর্ণ
রূপগুলোও ধরা হয়েছে, কারণ পরিচালক যেকোনো বানানে লিখতে পারেন।

⚠️ নিরাপত্তা — যে টপিকে আগে থেকেই স্ক্রিপ্ট আছে, সেটি এড়িয়ে যায়।
মানানসই টপিক না পেলে চুপচাপ বাদ। বারবার চললেও নিরাপদ।
"""
from django.db import migrations

MARKS = ("الفلق", "al-falaq", "al falaq", "alfalaq", "falaq", "falak",
         "আল-ফালাক", "আল ফালাক", "ফালাক", "ফালাক্ব")


def fill(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    LectureTopic = apps.get_model("core", "LectureTopic")

    if Lesson.objects.filter(title_ar=SAMPLES["falaq"]["title_ar"]).exists():
        return                       # আগেই বসে গেছে

    for t in LectureTopic.objects.all().order_by("lecture__no", "order", "id"):
        low = (t.text or "").lower()
        if not any(m.lower() in low for m in MARKS):
            continue
        if Lesson.objects.filter(topic=t).exists():
            continue                 # পরিচালকের স্ক্রিপ্ট আছে — ছোঁব না
        lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                  t.lecture.course, "falaq", topic=t)
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

    dependencies = [("core", "0047_nas_lesson")]

    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
