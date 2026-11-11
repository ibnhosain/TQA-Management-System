"""
Migration 0052 — guardian_phone ফিল্ড যোগ এবং দৈনিক আমলের মডেল
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0051_lecturetopic_today_plan"),
    ]

    operations = [
        # ১. User মডেলে guardian_phone ফিল্ড — ভাই-বোন সংযুক্ত করতে
        migrations.AddField(
            model_name="user",
            name="guardian_phone",
            field=models.CharField(
                blank=True, default="",
                max_length=20,
                verbose_name="অভিভাবকের WhatsApp নম্বর",
            ),
        ),
        # ২. দৈনিক আমলের আইটেম তালিকা
        migrations.CreateModel(
            name="DailyAmalItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, verbose_name="নাম")),
                ("kind", models.CharField(
                    choices=[("prayer", "নামাজ"), ("check", "চেকবক্স")],
                    default="check", max_length=8,
                )),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["order", "id"]},
        ),
        # ৩. দৈনিক আমলের রেকর্ড
        migrations.CreateModel(
            name="DailyAmalEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("value", models.CharField(default="not_done", max_length=12)),
                ("item", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="entries", to="core.dailyamalitem",
                )),
                ("student", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="amal_entries", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ["-date"]},
        ),
        migrations.AddConstraint(
            model_name="dailyamalentry",
            constraint=models.UniqueConstraint(
                fields=["student", "item", "date"],
                name="unique_student_item_date_amal",
            ),
        ),
        # ৪. ডিফল্ট আমল আইটেম — ৫ ওয়াক্ত নামাজ + কুরআন + দুআ
        migrations.RunSQL(
            sql="""
            INSERT INTO core_dailyamalitem (name, kind, "order", is_active) VALUES
            ('ফজর', 'prayer', 1, true),
            ('জোহর', 'prayer', 2, true),
            ('আসর', 'prayer', 3, true),
            ('মাগরিব', 'prayer', 4, true),
            ('ইশা', 'prayer', 5, true),
            ('কুরআন তিলাওয়াত', 'check', 6, true),
            ('সকালের দুআ ও আযকার', 'check', 7, true),
            ('রাতের দুআ ও আযকার', 'check', 8, true);
            """,
            reverse_sql="DELETE FROM core_dailyamalitem;",
        ),
    ]
