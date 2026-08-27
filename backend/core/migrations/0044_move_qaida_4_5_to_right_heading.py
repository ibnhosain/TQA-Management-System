# -*- coding: utf-8 -*-
"""দারস ৪ ও ৫ ভুল হেডিং থেকে সরিয়ে ঠিক জায়গায় আনা।

⚠️ কী হয়েছিল: নম্বর পড়ার নিয়মে "নামের শেষের সংখ্যা" ধরার একটি
শেষ-ভরসা ছিল। তাতে "Memorized Hadith 4"-ও ৪ হয়ে গিয়েছিল, আর দারস ৪ ও ৫
গিয়ে বসেছিল ভুল হেডিংয়ে। নিয়মটি এখন কড়া — কেবল "Lesson 4", "দারস ৪",
"Sabaq-05" এমন স্পষ্ট লেখা হলেই ধরা হয়। সাথে দারস ১-এর হেডিংকেই
অগ্রাধিকার দেওয়া হয়।

⚠️ ০০৪৩ একবার চলে গেলে Django আর চালায় না, তাই সারাইটা এখানে।

⚠️ পরিচালকের নিজের লেখা কিছুতে হাত পড়ে না — যে টগলের লেখা আমাদেরই
বসানো (অনুশীলনের কাগজ), কেবল সেটিই সরানো হয়।
"""
from django.db import migrations

NEW = ["qaida4", "qaida5"]
MARK = "Write in your notebook"      # আমাদের বসানো কাগজের চিহ্ন


def fix(apps, schema_editor):
    from core.sample_lessons import SAMPLES, topic_for_number
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LectureTopic = apps.get_model("core", "LectureTopic")

    d1 = SAMPLES["qaida"]
    first = (Lesson.objects.filter(title=d1["title"]).first()
             or Lesson.objects.filter(title_ar=d1["title_ar"]).first())
    if first is None:
        return
    near = first.topic if first.topic_id else None

    for key in NEW:
        data = SAMPLES[key]
        lesson = Lesson.objects.filter(title_ar=data["title_ar"]).first()
        if lesson is None:
            continue
        want = topic_for_number(LectureTopic, Lesson, first.course,
                                data["lesson_no"], near=near)
        if want is None or (lesson.topic_id and lesson.topic_id == want.id):
            continue                # ঠিক জায়গাতেই আছে, বা জায়গা নেই

        old = lesson.topic if lesson.topic_id else None
        lesson.topic = want
        lesson.title = want.text
        lesson.save(update_fields=["topic", "title"])

        # ভুল টপিকের টগল থেকে আমাদের বসানো কাগজটুকু তুলে নিই
        if old is not None and MARK in (old.content or ""):
            old.content = ""
            old.save(update_fields=["content"])
        # ঠিক টপিকে বসাই — খালি থাকলেই
        if not (want.content or "").strip():
            html = summary_html(lesson)
            if html:
                want.content = html
                want.save(update_fields=["content"])


class Migration(migrations.Migration):

    dependencies = [("core", "0043_qaida_lessons_4_and_5")]

    operations = [migrations.RunPython(fix, migrations.RunPython.noop)]
