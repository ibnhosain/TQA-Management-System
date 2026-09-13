# -*- coding: utf-8 -*-
"""আন-নাসের আয়াত ৪ — টুকরো দুটি উল্টো ক্রমে বসা সারানো।

⚠️ কী হয়েছিল: "The sneaky whisper" ধাপটি আয়াত ৪ শেখানোর **আগে** বসে,
আর তার পর্দায় আয়াতটির **দ্বিতীয়** টুকরো (ٱلْوَسْوَاسِ ٱلْخَنَّاسِ)
দেখানো হতো। অনুশীলনের কাগজে টুকরো জমা হয় স্লাইডের ক্রমে — তাই দ্বিতীয়
টুকরোটি প্রথমটির আগে বসে যেত, আর ডান-থেকে-বাঁয়ে পড়া শিশু আয়াতটি
**উল্টো ক্রমে** পড়ত।

স্ক্রিপ্টে ওই পর্দা থেকে আরবিটা তুলে নেওয়া হয়েছে। কিন্তু ০০৪৭ একবার
চলে গেছে, তাই চালু ডেটাবেজের সারিটা নিজে থেকে বদলাবে না — সারাইটা এখানে।

⚠️ যা করা হয় না:
  • দারসের ধাপ মোছা বা নতুন করে বসানো হয় না — কেবল একটি ঘর খালি করা হয়,
    তাই শিক্ষার্থীর অগ্রগতি ও পরিচালকের বাকি সম্পাদনা অক্ষত থাকে
  • পর্দাটিতে পরিচালক নিজে কিছু লিখে থাকলে (আমাদের লেখাটি আর নেই) কিছুই
    হয় না
  • টগলের লেখা কেবল তখনই নতুন করে বসে, যখন সেটি হুবহু আমাদেরই বসানো
    কাগজ — পরিচালকের নিজের লেখা কখনো মুছে যায় না

বারবার চললেও নিরাপদ।
"""
from django.db import migrations

# আয়াত ৪-এর দ্বিতীয় টুকরো — ভুল করে ভূমিকার পর্দায় বসেছিল
PIECE = "ٱلْوَسْوَاسِ ٱلْخَنَّاسِ"


def fix(apps, schema_editor):
    from core.sample_lessons import SAMPLES
    from core.stage_summary import summary_html
    Lesson = apps.get_model("core", "Lesson")

    for lesson in Lesson.objects.filter(
            title_ar=SAMPLES["nas"]["title_ar"]):
        # ভূমিকার পর্দাটি — খেলার ধরন, আর তাতেই টুকরোটি বসানো।
        # ⚠️ ধাপ ১৫-এর পর্দাতেও একই টুকরো আছে, কিন্তু সেটি "verse" ধরনের
        # আর ওটাই ঠিক জায়গা — তাই ধরন মিলিয়ে নেওয়া হয়।
        step = (lesson.steps.filter(slide__kind="activity",
                                    slide__arabic=PIECE)
                .order_by("order").first())
        if step is None:
            continue             # আগেই সারানো, বা পরিচালক বদলে ফেলেছেন

        before = summary_html(lesson)

        slide = step.slide
        slide.arabic = ""
        slide.arabic_locked = False
        slide.save(update_fields=["arabic", "arabic_locked"])

        topic = lesson.topic if getattr(lesson, "topic_id", None) else None
        if topic is None:
            continue
        # ⚠️ কেবল আমাদেরই বসানো কাগজ হলে নতুন করে লিখি
        if (topic.content or "").strip() == (before or "").strip():
            topic.content = summary_html(lesson)
            topic.save(update_fields=["content"])


class Migration(migrations.Migration):

    dependencies = [("core", "0048_falaq_lesson")]

    operations = [migrations.RunPython(fix, migrations.RunPython.noop)]
