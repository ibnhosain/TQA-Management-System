# -*- coding: utf-8 -*-
"""দারস দুটির লেখা হালনাগাদ — পুরনো ধাপ মুছে সর্বশেষ স্ক্রিপ্ট বসানো।

কেন দরকার: দারসগুলো একবার ডাটাবেজে বসে যাওয়ার পর কোডের স্ক্রিপ্ট বদলালেও
নিজে থেকে বদলায় না। এর মধ্যে অনেক কিছু উন্নত হয়েছে —

  • কায়দায় আরবি আর ইংরেজি অক্ষরে নেই (৬২ জায়গায় ডট)
  • আয়াতের শেষে মুসহাফের গোল নকশা — ۝١ ۝٢ ۝٣ ۝٤
  • কায়দায় খাতায় লেখার ৫টি নতুন ধাপ
  • গায়ে লেখা সময় ধাপের যোগফলের সাথে মিলিয়ে নেওয়া

⚠️ কেবল ধাপগুলো মোছা হয়, দারসের সারিটি নয় — তাই শিক্ষার্থীদের অগ্রগতি
(LessonProgress) এক বিন্দুও হারায় না। শিরোনাম, টপিক ও প্রকাশের অবস্থাও
আগের মতোই থাকে।

⚠️ পরিচালক ওই দুটি দারসে নিজে কিছু লিখে থাকলে তা এখানে বদলে যাবে —
পরিচালক নিজেই এটি চেয়েছেন ("পুরোনো গুলো মুছে ফেল")।

⚠️ দারস খোঁজা হয় তিনভাবে — শিরোনাম, আরবি শিরোনাম, তারপর ধরন। শুধু
শিরোনাম ধরলে পরিচালক নাম বদলে থাকলে মিলত না, আর হালনাগাদটাই বাদ পড়ত।
"""
from django.db import migrations


def _find(Lesson, data, key):
    """এই দারসটি ডাটাবেজে যেখানে যেখানে আছে।"""
    rows = list(Lesson.objects.filter(title=data["title"]))
    if not rows and data.get("title_ar"):
        rows = list(Lesson.objects.filter(title_ar=data["title_ar"]))
    if not rows:
        # শেষ চেষ্টা — একই ধরনের দারস, যেটিতে ধাপ আছে
        rows = [x for x in Lesson.objects.filter(kind=data["kind"])
                if x.steps.exists()]
    return rows


def refresh(apps, schema_editor):
    from core.sample_lessons import SAMPLES, create_sample
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")

    for key, data in SAMPLES.items():
        for lesson in _find(Lesson, data, key):
            create_sample(Lesson, LessonStep, StepSlide, lesson.course, key,
                          replace=True, target=lesson)
            # লেকচার প্ল্যানের টগলের লেখাও নতুন করে বসাই — পরিচালক
            # "প্লানও বসিয়ে দাও" বলেছেন
            if lesson.topic_id:
                html = summary_html(lesson)
                if html:
                    topic = lesson.topic
                    topic.content = html
                    topic.save(update_fields=["content"])


def back(apps, schema_editor):
    """পিছিয়ে যাওয়ার কিছু নেই — পুরনো লেখা ফিরিয়ে আনা যায় না।

    ⚠️ ইচ্ছা করেই খালি: এখানে কিছু মুছলে হালনাগাদ হওয়া দারসগুলোই চলে
    যেত, অথচ পুরনোটা ফিরত না।
    """


class Migration(migrations.Migration):

    dependencies = [("core", "0038_lesson_topic_link")]

    operations = [migrations.RunPython(refresh, back)]
