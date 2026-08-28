# -*- coding: utf-8 -*-
"""যে দারসগুলো এখনো বসেনি, কেবল সেগুলোই বসিয়ে দেওয়া।

⚠️ কেন দরকার — ডাটাবেজ বদলানোর একটি ফাঁদ। নতুন খালি ডাটাবেজে `migrate`
চালালে দারস-বসানোর মাইগ্রেশনগুলো চলে যায়, কিন্তু কিছুই বসায় না (তখন
কোর্স-টপিক কিছুই নেই)। তারপর `loaddata` পুরনো তথ্য আনে। ফল — ওই
মাইগ্রেশনগুলো "হয়ে গেছে" চিহ্নিত হয়ে যায় আর কখনো চলে না, তাই ব্যাকআপে
যা ছিল না তা আর কখনো বসে না।

এই মাইগ্রেশনটি সেই ফাঁক পূরণ করে — কোন মাইগ্রেশন আগে চলেছে তা না দেখে,
সরাসরি ডাটাবেজে দেখে নেয় কোন দারসটি নেই, আর কেবল সেটিই বসায়।

⚠️ নিরাপত্তা — তিনটি নিয়ম কখনো ভাঙে না:
  • যে দারস আগে থেকেই আছে (আরবি শিরোনাম মিলিয়ে), তাতে হাত পড়ে না
  • যে টপিকে আগে থেকেই স্ক্রিপ্ট আছে, সেটি এড়িয়ে যায়
  • টগলে পরিচালকের নিজের লেখা থাকলে তা বদলানো হয় না

মানানসই টপিক না পেলে চুপচাপ বাদ — ভুল জায়গায় বসানোর চেয়ে না বসানোই ভালো।
বারবার চললেও নিরাপদ।
"""
from django.db import migrations

# কোন দারস কোথায় বসবে — নম্বর ধরে, নাকি নাম ধরে
BY_NUMBER = ["qaida2", "qaida3", "qaida4", "qaida5"]
NAS_MARKS = ("الناس", "an-nas", "an nas", "annas",
             "আন-নাস", "আন নাস", "আননাস")
KAWTHAR_MARKS = ("الكوثر", "kawthar", "kawsar", "kausar", "kauthar",
                 "kaosar", "কাউসার", "কাওসার", "কাউছার", "কাওছার")


def _topic_by_name(LectureTopic, Lesson, marks):
    """নামে ওই সূরার উল্লেখ আছে এমন খালি টপিক।"""
    for t in LectureTopic.objects.all().order_by("lecture__no", "order", "id"):
        low = (t.text or "").lower()
        if not any(m.lower() in low for m in marks):
            continue
        if Lesson.objects.filter(topic=t).exists():
            continue                # পরিচালকের স্ক্রিপ্ট আছে
        return t
    return None


def fill(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample, topic_for_number
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    LectureTopic = apps.get_model("core", "LectureTopic")

    def place(key, topic):
        """একটি দারস ওই টপিকে বসিয়ে টগলের কাগজও তৈরি করে।"""
        lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                  topic.lecture.course, key, topic=topic)
        # ⚠️ পরিচালকের দেওয়া নামটাই থাকুক
        if lesson.title != topic.text:
            lesson.title = topic.text
            lesson.save(update_fields=["title"])
        if not (topic.content or "").strip():
            html = summary_html(lesson)
            if html:
                topic.content = html
                topic.save(update_fields=["content"])

    def missing(key):
        return not Lesson.objects.filter(
            title_ar=SAMPLES[key]["title_ar"]).exists()

    # ── কায়দার দারস ২–৫, নম্বর ধরে ──
    d1 = SAMPLES["qaida"]
    first = (Lesson.objects.filter(title=d1["title"]).first()
             or Lesson.objects.filter(title_ar=d1["title_ar"]).first())
    if first is not None:
        near = first.topic if first.topic_id else None
        for key in BY_NUMBER:
            if not missing(key):
                continue
            t = topic_for_number(LectureTopic, Lesson, first.course,
                                 SAMPLES[key]["lesson_no"], near=near)
            if t is not None:
                place(key, t)

    # ── মুখস্থ সূরাগুলো, নাম ধরে ──
    for key, marks in (("kawthar", KAWTHAR_MARKS), ("nas", NAS_MARKS)):
        if not missing(key):
            continue
        t = _topic_by_name(LectureTopic, Lesson, marks)
        if t is not None:
            place(key, t)


class Migration(migrations.Migration):

    dependencies = [("core", "0045_kawthar_lesson")]

    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
