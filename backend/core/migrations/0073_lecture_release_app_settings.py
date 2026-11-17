"""লেকচার অনুমোদন (Course.lectures_released) আর পরিচালকের Settings পাতার চালু/বন্ধ বোতাম (AppSetting)।
Easy Noorani Qaida-য় লেকচার ১–৩০ অনুমোদিত (মালিকের নির্দেশ, ২০২৬-১১-১৭)।"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def release(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    for c in Course.objects.filter(name__iexact="Easy Noorani Qaida"):
        c.lectures_released = 30
        c.save(update_fields=["lectures_released"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0072_easy_qaida_lectures_bigger_text"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(model_name="course", name="lectures_released",
                            field=models.PositiveIntegerField(default=0, verbose_name="অনুমোদিত লেকচার")),
        migrations.CreateModel(
            name="AppSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=60, unique=True)),
                ("enabled", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(release, migrations.RunPython.noop),
    ]
