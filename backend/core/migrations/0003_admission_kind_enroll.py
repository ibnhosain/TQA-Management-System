from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_admission_email_admission_kind_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="admission",
            name="kind",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("admission", "ভর্তি"),
                    ("enroll", "ভর্তি"),
                    ("trial", "ফ্রি ট্রায়াল"),
                    ("contact", "যোগাযোগ"),
                ],
                default="admission",
            ),
        ),
    ]
