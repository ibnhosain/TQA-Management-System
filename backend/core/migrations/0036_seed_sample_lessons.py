"""দুটি নমুনা দারস বসিয়ে দেওয়া — সূরা আল-ইখলাস ও Easy Noorani Qaida।

কোন কোর্সে বসবে তা নাম দেখে অনুমান করা হয়। মানানসই কোর্স না পেলে চালু
থাকা প্রথম কোর্সেই বসে; একটিও কোর্স না থাকলে চুপচাপ কিছুই করা হয় না
(নতুন একাডেমিতে মাইগ্রেশন যেন আটকে না যায়)।

⚠️ একই কোর্সে একই শিরোনামের দারস আগে থেকে থাকলে নতুন করে বানানো হয় না,
তাই বারবার চললেও নিরাপদ। পরিচালক চাইলে পরে "নমুনা দারস আনুন" দিয়ে
যেকোনো কোর্সে নিজেও বসাতে পারবেন।
"""
from django.db import migrations

PICKS = [
    # (কোন নমুনা, কোর্সের নামে যে শব্দগুলো খুঁজব)
    ("qaida", ["qaida", "noorani", "নূরানী", "নুরানি", "nazera", "নাজেরা"]),
    ("ikhlas", ["quran", "কুরআন", "hifz", "হিফজ", "memor", "reading"]),
]


def _pick_course(Course, words):
    for w in words:
        c = Course.objects.filter(is_active=True, name__icontains=w).first()
        if c:
            return c
    return Course.objects.filter(is_active=True).first()


def seed(apps, schema_editor):
    from core.sample_lessons import create_sample
    Course = apps.get_model("core", "Course")
    Lesson = apps.get_model("core", "Lesson")
    LessonStep = apps.get_model("core", "LessonStep")
    StepSlide = apps.get_model("core", "StepSlide")
    for key, words in PICKS:
        course = _pick_course(Course, words)
        if course:
            # (দারস, আগে ছিল কিনা) ফেরত আসে — এখানে প্রথমটিই যথেষ্ট
            create_sample(Lesson, LessonStep, StepSlide, course, key)


def unseed(apps, schema_editor):
    """পিছিয়ে গেলে কেবল এই দুটি নমুনাই সরে — পরিচালকের লেখা কিছু নয়।"""
    from core.sample_lessons import SAMPLES
    Lesson = apps.get_model("core", "Lesson")
    Lesson.objects.filter(
        title__in=[d["title"] for d in SAMPLES.values()]).delete()


class Migration(migrations.Migration):

    dependencies = [("core", "0035_lesson_script")]

    operations = [migrations.RunPython(seed, unseed)]
