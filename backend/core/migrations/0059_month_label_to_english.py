"""
Migration 0057 — month_label বাংলা → ইংরেজি

অ্যাপ এখন সম্পূর্ণ ইংরেজিতে চলে, তাই tasks.month_label_for() এখন
"July 2026" ধরনের লেবেল তৈরি করে ("জুলাই ২০২৬" নয়)।

⚠️ কেন মাইগ্রেশন জরুরি — month_label কেবল দেখানোর লেখা নয়, এটি ফি ও
বেতনের রেকর্ড মেলানোর কী (DueMonth-এ unique_together, আর
generate_monthly_dues() এই লেবেল দিয়েই "আগে পরিশোধ হয়েছে কি" খোঁজে)।
পুরনো রেকর্ড বাংলায় রেখে নতুন লেবেল ইংরেজি করলে একই মাসের বকেয়া দুবার
তৈরি হতো — পরিবারকে দুবার বিল করা হতো।

রূপান্তর হয় চারটি মডেলেই: FeePayment, DueMonth, TeacherPayment, SentReceipt।
"""
from django.db import migrations

BN_MONTHS = [
    "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
    "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর",
]
EN_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
BN_TO_EN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
EN_TO_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

MODELS = ["FeePayment", "DueMonth", "TeacherPayment", "SentReceipt"]


def _convert(label, months_from, months_to, digit_table):
    """"জুলাই ২০২৬" → "July 2026"। চেনা না গেলে অপরিবর্তিত ফেরত দেয় —
    হাতে লেখা/অন্য ফরম্যাটের লেবেল যেন নষ্ট না হয়।"""
    if not label:
        return label
    out = label
    for src, dst in zip(months_from, months_to):
        if src in out:
            out = out.replace(src, dst)
            break
    else:
        return label  # কোনো মাসের নাম মেলেনি — ছুঁই না
    return out.translate(digit_table)


def _apply(apps, months_from, months_to, digit_table):
    for name in MODELS:
        Model = apps.get_model("core", name)
        rows = []
        for obj in Model.objects.all().only("id", "month_label"):
            new = _convert(obj.month_label, months_from, months_to, digit_table)
            if new != obj.month_label:
                obj.month_label = new
                rows.append(obj)
        if rows:
            Model.objects.bulk_update(rows, ["month_label"], batch_size=500)


def forwards(apps, schema_editor):
    _apply(apps, BN_MONTHS, EN_MONTHS, BN_TO_EN_DIGITS)


def backwards(apps, schema_editor):
    _apply(apps, EN_MONTHS, BN_MONTHS, EN_TO_BN_DIGITS)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0058_deck_notes_taught"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
