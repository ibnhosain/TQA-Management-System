"""প্রতিটি শিক্ষার্থীর নিজস্ব "কার কাছে পড়ে" ঘরে এখনকার উস্তাদকে বসিয়ে দিই।

এতদিন উস্তাদ বাঁধা ছিল কোর্সের সাথে। নতুন ঘরটি খালি রেখে দিলে পর্দায় কিছু
বদলাত না ঠিকই (খালি হলে কোর্সের উস্তাদই ধরা হয়), কিন্তু পরিচালক একজনের
উস্তাদ বদলাতে গেলে বাকিদের ঘর খালিই থেকে যেত — বিভ্রান্তিকর। তাই একবারেই
সবার ঘরে বর্তমান উস্তাদকে বসিয়ে দেওয়া হচ্ছে।

⚠️ কারও উস্তাদ বদলায় না — যে যার কোর্সের উস্তাদের কাছেই থাকেন। কেবল তথ্যটা
এখন শিক্ষার্থীর নিজের ঘরেও লেখা থাকে।

একাধিক কোর্সে থাকলে প্রথম কোর্সের (আইডি অনুযায়ী) উস্তাদ বসে। আগে থেকেই
কারও ঘরে কিছু থাকলে তাতে হাত দেওয়া হয় না।
"""
from django.db import migrations


def backfill(apps, schema_editor):
    User = apps.get_model("core", "User")
    Course = apps.get_model("core", "Course")

    by_student = {}
    for c in Course.objects.filter(teacher__isnull=False).order_by("id"):
        for sid in c.students.values_list("id", flat=True):
            by_student.setdefault(sid, c.teacher_id)

    changed = []
    for u in User.objects.filter(role="student", teacher__isnull=True):
        tid = by_student.get(u.id)
        if tid:
            u.teacher_id = tid
            changed.append(u)
    if changed:
        User.objects.bulk_update(changed, ["teacher"])


def unbackfill(apps, schema_editor):
    # ফিরিয়ে নিলে ঘরটা খালি করে দিই — কোর্সের উস্তাদ তো অক্ষতই আছে
    User = apps.get_model("core", "User")
    User.objects.filter(role="student").update(teacher=None)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_student_own_teacher"),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
