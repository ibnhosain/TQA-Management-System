# -*- coding: utf-8 -*-
"""কায়দার দারস ৪ ও ৫ — পরিচালকের নম্বর ধরে ঠিক টপিকে বসানো।

⚠️ এবার আর ক্রম (order) ধরে খোঁজা হয় না। আগেরবার তাতেই দারস ২ ও ৩ গিয়ে
বসেছিল পরিচালকের ৯ ও ১০ নম্বর টপিকে — কারণ order-এর মান আর তাঁর দেওয়া
নম্বর এক নয়। এখন topic_number() দিয়ে নামের ভেতরের নম্বরটাই পড়া হয়:
"Lesson-04" → ৪, "দারস ৫" → ৫।

⚠️ ওই নম্বরের টপিক না পেলে, বা তাতে আগে থেকেই স্ক্রিপ্ট থাকলে, কিছুই
করা হয় না। ভুল জায়গায় বসানোর চেয়ে না বসানোই ভালো — পরিচালক তখন নিজে
টপিক বেছে দিতে পারবেন।

⚠️ দারসের নাম টপিকের নাম থেকেই নেওয়া হয়, তাই তাঁর নামকরণ অটুট থাকে।
বারবার চললেও নিরাপদ।
"""
from django.db import migrations

NEW = ["qaida4", "qaida5"]


def seed(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample, topic_for_number
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    LectureTopic = apps.get_model("core", "LectureTopic")

    # কায়দার দারস ১ যেখানে, সেই কোর্সেই বাকিগুলো
    d1 = SAMPLES["qaida"]
    first = (Lesson.objects.filter(title=d1["title"]).first()
             or Lesson.objects.filter(title_ar=d1["title_ar"]).first())
    if first is None:
        return
    course = first.course

    for key in NEW:
        data = SAMPLES[key]
        if Lesson.objects.filter(title_ar=data["title_ar"]).exists():
            continue                # আগেই বসানো হয়েছে
        topic = topic_for_number(LectureTopic, Lesson, course,
                                 data["lesson_no"],
                                 near=first.topic if first.topic_id else None)
        if topic is None:
            continue                # ওই নম্বরের খালি টপিক নেই

        lesson, _ = create_sample(Lesson, LessonStep, StepSlide, course, key,
                                  topic=topic)
        # ⚠️ পরিচালকের দেওয়া নামটাই থাকুক
        lesson.title = topic.text
        lesson.save(update_fields=["title"])

        if not (topic.content or "").strip():
            html = summary_html(lesson)
            if html:
                topic.content = html
                topic.save(update_fields=["content"])


def unseed(apps, schema_editor):
    """পিছিয়ে গেলে কেবল এই দুটিই সরে — পরিচালকের টপিক বা লেখা নয়।"""
    from core.sample_lessons import SAMPLES
    Lesson = apps.get_model("core", "Lesson")
    Lesson.objects.filter(
        title_ar__in=[SAMPLES[k]["title_ar"] for k in NEW]).delete()


class Migration(migrations.Migration):

    dependencies = [("core", "0042_qaida_2_3_into_director_topics")]

    operations = [migrations.RunPython(seed, unseed)]
