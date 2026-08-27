# -*- coding: utf-8 -*-
"""কায়দার দারস ২ ও ৩ — পরিচালকের নিজের টপিকে বসানো, আর ভুল হলে সারানো।

⚠️ কেন আলাদা মাইগ্রেশন: ০০৪১-এর প্রথম সংস্করণ নতুন টপিক বানাত। সেটি
একবার চলে গেলে Django তাকে "হয়ে গেছে" ধরে রাখে — কোড শুধরালেও আর চলে
না। তাই সংশোধনটি নতুন মাইগ্রেশনে, যাতে দুই অবস্থাতেই কাজ হয়:

  ক) দারস দুটি এখনো বসেনি      → পরিচালকের খালি টপিকে বসিয়ে দেয়
  খ) আগের সংস্করণে বসে গেছে    → নিজের বানানো টপিক থেকে সরিয়ে
                                  পরিচালকের টপিকে আনে, আর নিজের
                                  বানানো টপিকটি মুছে দেয়

⚠️ পরিচালকের নিজের হাতে লেখা কিছুতে হাত পড়ে না — কেবল যে টপিকের নাম
হুবহু আমাদের দারসের শিরোনাম, সেটিকেই "নিজের বানানো" ধরা হয়।

⚠️ বারবার চললেও নিরাপদ।
"""
from django.db import migrations

NEW = ["qaida2", "qaida3"]


def _first_qaida(Lesson, data):
    return (Lesson.objects.filter(title=data["title"]).first()
            or Lesson.objects.filter(title_ar=data["title_ar"]).first())


def _free_topics(Lesson, LectureTopic, first):
    """পরিচালকের যে টপিকগুলোতে এখনো স্ক্রিপ্ট নেই — ক্রম ধরে।"""
    if first.topic_id:
        base = first.topic
        rows = LectureTopic.objects.filter(
            lecture=base.lecture,
            order__gt=base.order).order_by("order", "id")
    else:
        rows = LectureTopic.objects.filter(
            lecture__course=first.course).order_by("lecture__no", "order",
                                                   "id")
    return [t for t in rows if not Lesson.objects.filter(topic=t).exists()]


def fix(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    LectureTopic = apps.get_model("core", "LectureTopic")

    first = _first_qaida(Lesson, SAMPLES["qaida"])
    if first is None:
        return
    free = _free_topics(Lesson, LectureTopic, first)

    for key in NEW:
        data = SAMPLES[key]
        lesson = Lesson.objects.filter(title_ar=data["title_ar"]).first()

        if lesson is None:
            # ── ক) এখনো বসেনি ──
            if not free:
                return
            topic = free.pop(0)
            lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                      first.course, key, topic=topic)
        else:
            # ── খ) বসে আছে — ঠিক জায়গায় কিনা দেখি ──
            old = lesson.topic if lesson.topic_id else None
            auto = old is not None and old.text == data["title"]
            if not auto:
                continue            # পরিচালকের টপিকেই আছে, হাত দেব না
            if not free:
                continue            # সরানোর জায়গা নেই — যেমন আছে থাক
            topic = free.pop(0)
            lesson.topic = topic
            lesson.save(update_fields=["topic"])
            # নিজের বানানো টপিকটি আর দরকার নেই
            LectureTopic.objects.filter(pk=old.pk).delete()

        # ── নাম ও টগল ──
        # ⚠️ দারসের নাম পরিচালকের টপিকের নাম থেকেই
        if lesson.title != topic.text:
            lesson.title = topic.text
            lesson.save(update_fields=["title"])
        if not (topic.content or "").strip():
            html = summary_html(lesson)
            if html:
                topic.content = html
                topic.save(update_fields=["content"])


class Migration(migrations.Migration):

    dependencies = [("core", "0041_qaida_lessons_2_and_3")]

    operations = [migrations.RunPython(fix, migrations.RunPython.noop)]
