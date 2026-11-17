"""স্লাইড চালানোর সময় (DeckPlay) আর এডমিনের লেকচার অনুমোদন (LectureApproval) — অনুমোদন দিলে তবেই পরের লেকচার খোলে।
(আগের "কয়টা লেকচার খোলা" সংখ্যা আর ব্যবহার হয় না — মালিকের নির্দেশ; ঘরটা মোছা হয়নি।)"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0073_lecture_release_app_settings"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="DeckPlay", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("no", models.PositiveIntegerField()),
            ("part", models.CharField(blank=True, default="", max_length=40)),
            ("started_at", models.DateTimeField(auto_now_add=True)),
            ("seconds", models.PositiveIntegerField(default=0)),
            ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deck_plays", to="core.course")),
            ("student", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
            ("teacher", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="deck_plays", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-started_at"]}),
        migrations.CreateModel(name="LectureApproval", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("no", models.PositiveIntegerField()),
            ("approved_at", models.DateTimeField(auto_now_add=True)),
            ("approved_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
            ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lecture_approvals", to="core.course")),
            ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lecture_approvals", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-approved_at"], "unique_together": {("course", "student", "no")}}),
    ]
