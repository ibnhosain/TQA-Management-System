"""সংরক্ষিত সিলেবাস টেবিলের নমুনা শিরোনামগুলো বাংলা → ইংরেজি।

⚠️ কেবল সেই শিরোনামগুলোই বদলায় যেগুলো হুবহু পাঁচটি নমুনা নামের একটি —
অর্থাৎ যেগুলোতে পরিচালক এখনো হাত দেননি। তিনি নিজে যা লিখেছেন তা অক্ষত
থাকে। ঘরের ভেতরের কোনো লেখাতেই (rows) হাত পড়ে না।

একবারই চলে (মাইগ্রেশন), তাই পরে কেউ ইচ্ছা করে বাংলায় শিরোনাম লিখলে সেটা
আর কখনো বদলে যাবে না।
"""
from django.db import migrations

BN_TO_EN = {
    "মুখস্থ সূরা": "Memorized Surah",
    "মুখস্থ হাদিস": "Memorized Hadith",
    "কিরাত": "Qirat",
    "দুআ/মাসআলা": "Dua/Masala",
    "নৈতিক শিক্ষা/হাদিসের গল্প": "Moral Lesson/Hadith Story",
}
EN_TO_BN = {v: k for k, v in BN_TO_EN.items()}


def _swap(apps, mapping):
    Sheet = apps.get_model("core", "CourseSyllabusSheet")
    changed = []
    for sheet in Sheet.objects.all():
        headers = sheet.headers or []
        new = [mapping.get(h, h) for h in headers]
        if new != headers:
            sheet.headers = new
            changed.append(sheet)
    if changed:
        Sheet.objects.bulk_update(changed, ["headers"])


def to_english(apps, schema_editor):
    _swap(apps, BN_TO_EN)


def to_bengali(apps, schema_editor):
    _swap(apps, EN_TO_BN)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_coursesyllabussheet"),
    ]

    operations = [
        migrations.RunPython(to_english, to_bengali),
    ]
