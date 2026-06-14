from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_librarybook"),
    ]

    operations = [
        migrations.AlterField(
            model_name="academicbook",
            name="file",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
