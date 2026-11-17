"""লেকচারের স্লাইড দুই রকম: উস্তাদের (teacher) আর শিক্ষার্থীর পড়া-প্র্যাকটিসের (student)। আগের সব স্লাইড teacher।"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0061_seed_easy_qaida_lecture_02_deck")]
    operations = [
        migrations.AddField(
            model_name="lecturedeck", name="audience",
            field=models.CharField(choices=[("teacher", "উস্তাদের স্লাইড"), ("student", "শিক্ষার্থীর স্লাইড")], default="teacher", max_length=8),
        ),
    ]
