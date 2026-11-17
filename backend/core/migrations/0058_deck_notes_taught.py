"""লেকচারের স্লাইডে শিক্ষার্থীর নোট ও টপিকের তালিকা, আর কাকে পড়ানো হলো (DeckTaught)।
Easy Noorani Qaida লেকচার ১-এর নোট ও টপিক এখানেই বসে যায় (স্লাইডের বই ও ক্রম অনুযায়ী)।
⚠️ নির্ভরতা 0056-এর ওপর — একই সময়ে আরেকটি 0057 তৈরি হচ্ছিল (মাসের নাম ইংরেজি); সেটা পুশ করার আগে
   একটা merge মাইগ্রেশন (python manage.py makemigrations --merge) লাগবে।"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

NOTE_1 = """Lecture 1 · Day 1 — What we learned today

📖 Easy Noorani Qaida
• How we learn every page: 1. Look  2. Listen  3. Say  4. Practise at home.
• Arabic is read from right ← to left.
• My class manners: clean clothes, book and pencil ready, on time; say Assalamu Alaikum; sit nicely; read in a loud, clear voice.
• Duas before learning:
  اَعُوْذُ بِاللّٰهِ مِنَ الشَّيْطٰنِ الرَّجِيْمِ — I seek protection with Allah from Shaytan, the rejected one.
  بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيْمِ — In the name of Allah, the Most Kind, the Most Merciful.
  رَبِّ زِدْنِيْ عِلْمًا — My Lord, increase me in knowledge.
• Lesson 1: the Quran is written with 29 Arabic letters. Today's 5 letters:
  ا Alif · ب Ba · ت Ta · ث Tha · ج Jeem

📖 My First Surahs
• Surah Al-Fatihah — "The Opening", 7 verses, came down in Makkah. It is the greatest Surah in the Quran. (Sahih al-Bukhari)
• Verse 1: بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيْمِ — In the name of Allah, the Most Kind, the Most Merciful.

📖 Islamic Duas, Manners and Values — Lesson 1: Eating and Drinking
• Before eating and drinking: بِسْمِ اللّٰهِ — "In the name of Allah." (Sahih al-Bukhari)
• True story: the Prophet ﷺ gently told young Umar: "Say Bismillah, eat with your right hand, and eat from what is in front of you." (Sahih al-Bukhari and Sahih Muslim)
• When I eat: I wash my hands before and after · I say Bismillah · I eat with my right hand.

📖 My Salah Duas — Dua 1: Takbir
• اَللّٰهُ اَكْبَرُ — Allah is the Greatest.
• We say it to begin the salah, and every time we change position.
• Boys raise the hands to the ears; girls raise the hands to the shoulders.

✏️ My First Arabic Writing Book
• My writing steps: look and say → sky writing → finger writing → pencil writing → memory writing.
• Sit like a writer; hold the pencil with 3 fingers, like a little bird's beak; press gently.
• Warm-up: long lines — start at the green dot and go to the left ←.

🏠 Homework (5–10 minutes)
1. Say Bismillah before dinner.
2. Say verse 1 of Al-Fatihah to Ammu or Abbu.
3. Point to the first 5 letters in your book and say their names.
4. Trace the long lines with your finger.

For parents: ask your child "Which one is Jeem?" and let them point to it."""

TOPICS_1 = """Qaida — How we learn every page
Qaida — My Class Manners
Qaida — Duas Before Learning (first 3)
Qaida Lesson 1 — The 29 letters + first row (Alif to Jeem)
Surah — Before We Recite
Surah — Al-Fatihah: about the Surah + Verse 1
Duas & Manners Lesson 1 — Bismillah before eating, true story, 3 manners
Salah Duas — Dua 1: Takbir (Allahu Akbar)
Writing — My Writing Steps, Get Ready to Write, Warm-Up long lines
Review game and homework"""


def seed(apps, schema_editor):
    LectureDeck = apps.get_model("core", "LectureDeck")
    for d in LectureDeck.objects.filter(no=1, filename="Lecture 01 - Easy Noorani Qaida.pptx"):
        if not d.note:
            d.note = NOTE_1
        if not d.topics:
            d.topics = TOPICS_1
        d.save(update_fields=["note", "topics"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0056_seed_easy_qaida_lecture_01_deck"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name="lecturedeck", name="note",
                            field=models.TextField(blank=True, default="", verbose_name="শিক্ষার্থীর নোট")),
        migrations.AddField(model_name="lecturedeck", name="topics",
                            field=models.TextField(blank=True, default="", verbose_name="স্লাইডের টপিক")),
        migrations.CreateModel(
            name="DeckTaught",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("topics", models.JSONField(blank=True, default=list)),
                ("taught_at", models.DateTimeField(auto_now=True)),
                ("deck", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="taught", to="core.lecturedeck")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decks_taught", to=settings.AUTH_USER_MODEL)),
                ("taught_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-taught_at"], "unique_together": {("deck", "student")}},
        ),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
