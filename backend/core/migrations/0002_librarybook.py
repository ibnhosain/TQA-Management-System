from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LibraryBook",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cls", models.CharField(max_length=100, verbose_name="শ্রেণি / ক্যাটাগরি")),
                ("title", models.CharField(max_length=200, verbose_name="বইয়ের নাম")),
                ("author", models.CharField(blank=True, max_length=150, verbose_name="লেখক")),
                ("link", models.URLField(blank=True, default="#", verbose_name="ডাউনলোড লিংক")),
                ("file_type", models.CharField(default="PDF", max_length=20, verbose_name="ফরম্যাট")),
                ("created_at", models.DateField(auto_now_add=True)),
            ],
            options={
                "ordering": ["cls", "title"],
            },
        ),
    ]
