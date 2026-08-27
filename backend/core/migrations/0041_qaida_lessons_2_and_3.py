# -*- coding: utf-8 -*-
"""কায়দার দারস ২ ও ৩ বসানো — স্ক্রিপ্ট, স্লাইড ও লেকচার প্ল্যানসহ।

কোন কোর্সে বসবে তা নাম দেখে ঠিক হয় — যেখানে দারস ১ আছে, সেখানেই।
দারস ১ না পেলে চুপচাপ কিছুই করা হয় না (নতুন একাডেমিতে মাইগ্রেশন যেন
আটকে না যায়)।

⚠️ প্রতিটি দারসের জন্য লেকচার প্ল্যানে একটি টপিকও তৈরি হয়, আর টগলের
ভেতরে অনুশীলনের কাগজ বসে যায় — পরিচালককে কিছু চাপতে হয় না।

⚠️ আগে থেকে থাকলে নতুন করে বানানো হয় না, তাই বারবার চললেও নিরাপদ।
"""
from django.db import migrations

NEW = ["qaida2", "qaida3"]


def seed(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    Lecture = apps.get_model("core", "Lecture")
    LectureTopic = apps.get_model("core", "LectureTopic")

    # দারস ১ যেখানে আছে, সেই কোর্সেই পরের দুটি
    first = Lesson.objects.filter(
        title=SAMPLES["qaida"]["title"]).first()
    if first is None:
        first = Lesson.objects.filter(
            title_ar=SAMPLES["qaida"]["title_ar"]).first()
    if first is None:
        return                      # কায়দার কোর্সই নেই — কিছুই করার নেই
    course = first.course

    for key in NEW:
        data = SAMPLES[key]
        if Lesson.objects.filter(title=data["title"]).exists():
            continue                # আগেই আছে

        # ── লেকচার প্ল্যানে টপিক ──
        # দারস ১-এর টপিক যে অধ্যায়ে, সেখানেই পরেরগুলো বসে
        lecture = None
        if getattr(first, "topic_id", None):
            lecture = first.topic.lecture
        if lecture is None:
            lecture = Lecture.objects.filter(course=course).order_by(
                "no").first()
        if lecture is None:
            nxt = 1
            lecture = Lecture.objects.create(
                course=course, no=nxt, title="Noorani Qaida")
        last = LectureTopic.objects.filter(
            lecture=lecture).order_by("-order").first()
        topic = LectureTopic.objects.create(
            lecture=lecture, text=data["title"],
            section=getattr(first.topic, "section", None) if
            getattr(first, "topic_id", None) else None,
            order=(last.order + 1) if last else 0)

        lesson, _ = create_sample(Lesson, LessonStep, StepSlide, course, key,
                                  topic=topic)
        # ── টগলের ভেতরে অনুশীলনের কাগজ ──
        html = summary_html(lesson)
        if html:
            topic.content = html
            topic.save(update_fields=["content"])


def unseed(apps, schema_editor):
    """পিছিয়ে গেলে কেবল এই দুটিই সরে — পরিচালকের লেখা কিছু নয়।"""
    from core.sample_lessons import SAMPLES
    Lesson = apps.get_model("core", "Lesson")
    LectureTopic = apps.get_model("core", "LectureTopic")
    titles = [SAMPLES[k]["title"] for k in NEW]
    Lesson.objects.filter(title__in=titles).delete()
    LectureTopic.objects.filter(text__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [("core", "0040_refresh_lesson_scripts_again")]

    operations = [migrations.RunPython(seed, unseed)]
