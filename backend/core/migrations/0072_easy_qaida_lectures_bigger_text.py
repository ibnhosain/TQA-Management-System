"""Easy Noorani Qaida — লেকচার ১–৩০ বড় লেখায় (আরবি সর্বোচ্চ ২ গুণ, ইংরেজি ১.২৫ গুণ — মালিকের নির্দেশ): উস্তাদ ও শিক্ষার্থীর স্লাইড বদল (Slides ফোল্ডারের কপি, deck_seed/)।
একই লেকচার ও একই ধরনের স্লাইড আগে থাকলে নতুনটা দিয়ে বদলায়।"""
import os

from django.db import migrations

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deck_seed")


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    LectureDeck = apps.get_model("core", "LectureDeck")
    course = Course.objects.filter(name__iexact="Easy Noorani Qaida").first() or Course.objects.filter(name__icontains="easy").first()
    if course is None:
        return
    for no in range(1, 31):
        for aud, suffix, title in (("teacher", "", f"Day {no}"), ("student", "-student", f"Day {no} · My Practice")):
            path = os.path.join(SEED, f"easy-noorani-qaida-lecture-{no:02d}{suffix}.pptx")
            if not os.path.exists(path):
                continue
            data = open(path, "rb").read()
            fname = f"Lecture {no:02d} - Easy Noorani Qaida{' - Student' if suffix else ''}.pptx"
            LectureDeck.objects.update_or_create(course=course, no=no, audience=aud,
                                                 defaults={"title": title, "filename": fname, "size": len(data), "data": data})


class Migration(migrations.Migration):
    dependencies = [("core", "0071_seed_easy_qaida_lectures_26_to_30")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
