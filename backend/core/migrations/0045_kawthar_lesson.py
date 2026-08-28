# -*- coding: utf-8 -*-
"""সূরা আল-কাউসারের দারস — পরিচালকের নিজের টপিকে বসানো।

⚠️ এই টপিকের নামে কোনো নম্বর নেই ("Al-Kawthar-الكوثر"), তাই
topic_number() এখানে কাজে আসে না। বদলে সূরার নাম ধরে খোঁজা হয় — আরবি
নাম (الكوثر) বা ইংরেজি নাম (kawthar), যেটিই টপিকের লেখায় থাকুক।

⚠️ যে টপিকে আগে থেকেই স্ক্রিপ্ট আছে, সেটি ছোঁয়া হয় না — পরিচালকের লেখা
কিছুর উপরে কখনো বসবে না। মানানসই টপিক না পেলে চুপচাপ কিছুই করা হয় না।

⚠️ দারসের নাম টপিকের নাম থেকেই নেওয়া হয়, তাই পরিচালকের নামকরণ অটুট
থাকে। চেনার স্থির চাবি আরবি শিরোনাম (الكوثر)।

বারবার চললেও নিরাপদ।
"""
from django.db import migrations

KEY = "kawthar"
# টপিকের লেখায় এর যেকোনোটি থাকলেই সেটিই কাউসারের টপিক
# ⚠️ বানান নানা রকম হতে পারে — পরিচালক যেভাবেই লিখুন যেন মিলে যায়।
# আরবি নামটি সবচেয়ে নির্ভরযোগ্য, তবু ইংরেজি ও বাংলার চলতি বানানগুলোও রাখা।
MARKS = ("الكوثر", "kawthar", "kawsar", "kausar", "kauthar", "kaosar",
         "কাউসার", "কাওসার", "কাউছার", "কাওছার")


def seed(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    LectureTopic = apps.get_model("core", "LectureTopic")

    data = SAMPLES[KEY]
    if Lesson.objects.filter(title_ar=data["title_ar"]).exists():
        return                      # আগেই বসানো হয়েছে

    topic = None
    for t in LectureTopic.objects.all().order_by("lecture__no", "order", "id"):
        low = (t.text or "").lower()
        if not any(m.lower() in low for m in MARKS):
            continue
        if Lesson.objects.filter(topic=t).exists():
            continue                # পরিচালকের স্ক্রিপ্ট আছে — হাত দেব না
        topic = t
        break
    if topic is None:
        return                      # মানানসই খালি টপিক নেই

    lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                              topic.lecture.course, KEY, topic=topic)
    # ⚠️ পরিচালকের দেওয়া নামটাই থাকুক
    lesson.title = topic.text
    lesson.save(update_fields=["title"])

    if not (topic.content or "").strip():
        html = summary_html(lesson)
        if html:
            topic.content = html
            topic.save(update_fields=["content"])


def unseed(apps, schema_editor):
    """পিছিয়ে গেলে কেবল এই দারসটিই সরে — পরিচালকের টপিক বা লেখা নয়।"""
    from core.sample_lessons import SAMPLES
    Lesson = apps.get_model("core", "Lesson")
    Lesson.objects.filter(title_ar=SAMPLES[KEY]["title_ar"]).delete()


class Migration(migrations.Migration):

    dependencies = [("core", "0044_move_qaida_4_5_to_right_heading")]

    operations = [migrations.RunPython(seed, unseed)]
