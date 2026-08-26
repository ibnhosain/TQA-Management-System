"""এখনকার চারটি মূল্যায়ন-মাপকাঠি তালিকায় বসিয়ে দেওয়া।

আগে এগুলো কোডেই লেখা ছিল, আর উস্তাদের দেওয়া নম্বর TrialReport.scores-এ
{"letters": 4, ...} আকারে জমা হতো। তাই এখানে হুবহু সেই key-গুলোই ব্যবহার
করা হচ্ছে — নইলে আগে লেখা রিপোর্টগুলোর নম্বর আর মিলত না।

তালিকায় আগে থেকে কিছু থাকলে কিছুই করা হয় না, তাই বারবার চললেও নিরাপদ।
"""
from django.db import migrations

DEFAULTS = [
    ("letters", "হরফ চেনা", "Recognising letters"),
    ("makhraj", "মাখরাজ ও উচ্চারণ", "Makhraj & pronunciation"),
    ("fluency", "তিলাওয়াতের সাবলীলতা", "Fluency"),
    ("attentiveness", "মনোযোগ", "Attentiveness"),
]


def seed(apps, schema_editor):
    Item = apps.get_model("core", "TrialScoreItem")
    if Item.objects.exists():
        return
    Item.objects.bulk_create([
        Item(key=k, label_bn=bn, label_en=en, order=i)
        for i, (k, bn, en) in enumerate(DEFAULTS)
    ])


def unseed(apps, schema_editor):
    """পিছিয়ে গেলে কেবল এই চারটিই সরে — পরিচালকের যোগ করা কিছু নয়।"""
    Item = apps.get_model("core", "TrialScoreItem")
    Item.objects.filter(key__in=[k for k, _, _ in DEFAULTS]).delete()


class Migration(migrations.Migration):

    dependencies = [("core", "0032_trial_score_items")]

    operations = [migrations.RunPython(seed, unseed)]
