"""প্রতিটি কোর্সে সাতটি হেডিং বানিয়ে পুরনো টপিকগুলো তার নিচে বসিয়ে দিই।

আগে টপিক বসত সরাসরি দারসের নিচে, হেডিং বলে কিছু ছিল না। এখন হেডিং ধরে
সাজানো হয় — তাই একবারেই সবগুলো ঠিক জায়গায় বসিয়ে দেওয়া হচ্ছে।

কোন টপিক কোন হেডিংয়ে যাবে তা ঠিক হয় তার পুরনো সিলেবাস-সংযোগ (category)
দেখে। সংযোগ না থাকলে "অন্যান্য" হেডিংয়ে — যাতে একটি টপিকও হারিয়ে না যায়।

⚠️ কোনো টপিক, তার ভেতরের লেখা বা কভারের টিক — কিছুই মোছে না বা বদলায় না।
কেবল "কোন হেডিংয়ের নিচে" তথ্যটা যোগ হয়।
"""
from django.db import migrations

# পরিচালকের দেওয়া ক্রম
DEFAULT_SECTIONS = [
    "Memorized Surah",
    "Memorized Hadith",
    "Qirat",
    "Dua",
    "Masala",
    "Moral Lesson",
    "Hadith Story",
]
# পুরনো সিলেবাসের বিভাগ → নতুন হেডিং
CATEGORY_TO_SECTION = {
    "memorized_surah": "Memorized Surah",
    "memorized_hadith": "Memorized Hadith",
    "qirat": "Qirat",
    "dua_masala": "Dua",
    "moral_story": "Moral Lesson",
}
OTHER = "অন্যান্য"


def backfill(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    LessonSection = apps.get_model("core", "LessonSection")
    LectureTopic = apps.get_model("core", "LectureTopic")

    for course in Course.objects.all():
        if LessonSection.objects.filter(course=course).exists():
            continue  # আগে থেকেই বানানো — হাত দিই না
        by_name = {}
        for i, name in enumerate(DEFAULT_SECTIONS):
            by_name[name] = LessonSection.objects.create(
                course=course, name=name, order=i)

        topics = list(
            LectureTopic.objects.filter(lecture__course=course, section__isnull=True)
            .select_related("syllabus_item")
        )
        if not topics:
            continue

        changed = []
        for t in topics:
            cat = getattr(t.syllabus_item, "category", None)
            name = CATEGORY_TO_SECTION.get(cat)
            if not name:
                if OTHER not in by_name:
                    by_name[OTHER] = LessonSection.objects.create(
                        course=course, name=OTHER, order=len(DEFAULT_SECTIONS))
                name = OTHER
            t.section = by_name[name]
            changed.append(t)
        if changed:
            LectureTopic.objects.bulk_update(changed, ["section"])


def unbackfill(apps, schema_editor):
    # ফিরিয়ে নিলে কেবল সংযোগ খোলা হয় — টপিক বা হেডিং কিছুই মোছে না,
    # যাতে ভুল করে ফিরিয়ে নিলেও কারও লেখা না হারায়
    LectureTopic = apps.get_model("core", "LectureTopic")
    LectureTopic.objects.update(section=None)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_lesson_sections"),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
