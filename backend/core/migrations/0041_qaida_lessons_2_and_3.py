# -*- coding: utf-8 -*-
"""কায়দার দারস ২ ও ৩ বসানো — স্ক্রিপ্ট, স্লাইড ও লেকচার প্ল্যানসহ।

⚠️ নতুন টপিক বানানো হয় না। পরিচালক লেকচার প্ল্যানে নিজের মতো টপিক
সাজিয়ে রেখেছেন (যেমন "Qaida for Beginners — Lesson-02")। নতুন টপিক
বানালে তাঁর তালিকায় ডুপ্লিকেট ঢুকত। তাই দারস ১-এর টপিকের পরের যে
টপিকগুলোতে এখনো স্ক্রিপ্ট নেই, সেগুলোতেই বসানো হয়।

⚠️ দারসের নাম টপিকের নাম থেকেই নেওয়া হয় — পরিচালকের নিজের নামকরণ যেন
বদলে না যায়। চেনার জন্য আরবি শিরোনামটাই স্থির চাবি
(الحروف المفردة ٢ / ٣)।

⚠️ দারস ১ খোঁজা হয় শিরোনাম, তারপর আরবি শিরোনাম ধরে — পরিচালক নাম
বদলে থাকলেও (এবং তিনি বদলেছেনও) যেন মিলে যায়।

⚠️ আগে থেকে থাকলে নতুন করে বানানো হয় না, তাই বারবার চললেও নিরাপদ।
খালি টপিক না পেলে চুপচাপ কিছুই করা হয় না — ভুল জায়গায় বসানোর চেয়ে
না বসানোই ভালো।

⚠️ দারস ১ কোনো টপিকের সাথে যুক্ত না থাকলেও কাজটা হয় — তখন ওই কোর্সের
সব টপিক ক্রম ধরে দেখা হয়।
"""
from django.db import migrations

NEW = ["qaida2", "qaida3"]


def _find_first(Lesson, data):
    """কায়দার দারস ১ — নাম বদলে থাকলেও।"""
    return (Lesson.objects.filter(title=data["title"]).first()
            or Lesson.objects.filter(title_ar=data["title_ar"]).first())


def seed(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    LectureTopic = apps.get_model("core", "LectureTopic")

    first = _find_first(Lesson, SAMPLES["qaida"])
    if first is None:
        return                      # কায়দার দারসই নেই
    course = first.course

    if first.topic_id:
        # দারস ১-এর টপিকের পরের টপিকগুলো, একই অধ্যায়ে, ক্রম ধরে
        base = first.topic
        later = LectureTopic.objects.filter(
            lecture=base.lecture,
            order__gt=base.order).order_by("order", "id")
    else:
        # ⚠️ দারস ১ কোনো টপিকের সাথে যুক্ত না থাকলেও যেন কাজটা হয় —
        # তখন ওই কোর্সের সব টপিক ক্রম ধরে দেখি
        later = LectureTopic.objects.filter(
            lecture__course=course).order_by("lecture__no", "order", "id")

    # যেগুলোতে এখনো কোনো স্ক্রিপ্ট নেই
    free = [t for t in later
            if not Lesson.objects.filter(topic=t).exists()]

    for key in NEW:
        data = SAMPLES[key]
        if Lesson.objects.filter(title_ar=data["title_ar"]).exists():
            continue                # আগেই বসানো হয়েছে
        if not free:
            return                  # খালি টপিক ফুরিয়েছে — আর এগোব না
        topic = free.pop(0)

        lesson, _ = create_sample(Lesson, LessonStep, StepSlide, course, key,
                                  topic=topic)
        # ⚠️ পরিচালকের দেওয়া নামটাই রাখি — কেবল আরবি শিরোনামে চেনা যাবে
        lesson.title = topic.text
        lesson.save(update_fields=["title"])

        # টগলের ভেতরে অনুশীলনের কাগজ — খালি থাকলেই
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

    dependencies = [("core", "0040_refresh_lesson_scripts_again")]

    operations = [migrations.RunPython(seed, unseed)]
