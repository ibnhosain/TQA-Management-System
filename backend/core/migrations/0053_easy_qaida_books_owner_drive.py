# -*- coding: utf-8 -*-
"""Easy Noorani Qaida-র নতুন ৬টি বইয়ের লিংক মালিকের নিজের Drive ফোল্ডারের PDF-এ বদল
(ibnhosain014 → PDF ফোল্ডার 1t7dGf3JCLuYqyOVTAI2vvoqqfHvBx2XY; মালিকের নির্দেশ, ২০২৬-১১-১১)।"""
from django.db import migrations

D = "https://drive.google.com/file/d/{}/view?usp=sharing"
LINKS = {
    "Easy Noorani Qaida — Step One (Ages 4-6)": "1CptHq8Ptbxne6Trqqk-gWbeS8TzIgGeQ",
    "Memorized Surah — My First Surahs (Ages 4-6)": "1xusvBOkMC2QvY2eNjJYayc83C0y7JWE-",
    "Islamic Duas, Manners and Values (Ages 4-6)": "16tmoiwTRzMNSjb_6yKedfY6yVwNL9GgI",
    "My First Arabic Writing Book (Ages 4-6) — print on A4": "1ZDnqchmFuyHP0y4EnleL41IMn3E__2FO",
    "Teacher Guide — Memorized Surah Techniques (Teachers only)": "1Hz58G_076aBElKQVdOe6n5jOxic0av_G",
    "Teacher Guide — Teaching Arabic Writing on Zoom (Teachers only)": "1lVO38Ievd4XwA34SE85ypGwqtInyEfv_",
}


def forwards(apps, schema_editor):
    AcademicBook = apps.get_model("core", "AcademicBook")
    for name, fid in LINKS.items():
        AcademicBook.objects.filter(name=name).update(file=D.format(fid))


class Migration(migrations.Migration):
    dependencies = [("core", "0052_guardian_phone_daily_amal")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
