# -*- coding: utf-8 -*-
"""Easy Noorani Qaida কোর্সের লেকচার প্ল্যান ও সিলেবাস লোড করে।

ব্যবহার:
    python manage.py load_easy_qaida_plan

কী করে:
  ১. Easy Noorani Qaida কোর্স খোঁজে (নামে "qaida"/"noorani" থাকতে হবে)
  ২. CourseSyllabusSheet — ৩০ দিনের সামগ্রিক ছক তৈরি করে
  ③. SyllabusItem — ৫টি ক্যাটাগরিতে সিলেবাস আইটেম যোগ করে
  ④. Lecture + LessonSection + LectureTopic — ৩০ দিনের প্ল্যান বানায়

⚠️ বারবার চললেও নিরাপদ — আগে থেকে থাকলে নতুন করে বানায় না।
⚠️ পরিচালকের হাতে লেখা কিছুতে হাত দেয় না।
"""

from django.core.management.base import BaseCommand, CommandError


# ── ৩০ দিনের পাঠ পরিকল্পনা ──────────────────────────────────────────────────
# প্রতিটি দিন: (সূরা, কায়দা হরফ, হাদিস#, দুআ, গল্প)
DAYS = [
    # Day, Surah,                       Qaida,  Hadith, Dua,                    Story
    ( 1, "Al-Fatiha v.1 — Bismillah",   "أ Alif",   1,  "Bismillah (before eating)",   "Who made us? — Intro to Allah"),
    ( 2, "Al-Fatiha v.2 — Alhamdulillah","ب Ba",    2,  "Alhamdulillah (after eating)","Allah made Adam (AS)"),
    ( 3, "Al-Fatiha v.3 — Ar-Rahman",   "ت Ta",     3,  "Dua for waking up",           "Adam (AS) in Jannah"),
    ( 4, "Al-Fatiha v.4 — Maaliki",     "ث Tha",    4,  "Dua for going to sleep",      "Hawa (AS) & the garden"),
    ( 5, "Al-Fatiha v.5 — Iyyaka",      "ج Jim",    5,  "Dua entering the home",       "Adam (AS) comes to Earth"),
    ( 6, "Al-Fatiha v.6–7 — Sirat",     "ح Ha",     6,  "Dua leaving the home",        "Adam (AS) — lessons learnt"),
    ( 7, "Al-Fatiha — full review",      "خ Kha",    7,  "Duas review: days 1–6",       "Who was Nuh (AS)?"),
    ( 8, "Al-Ikhlas v.1 — Qul",         "د Dal",    8,  "Dua entering the masjid",     "The big flood (Nuh AS)"),
    ( 9, "Al-Ikhlas v.2 — Allahu Samad","ذ Dhal",   9,  "Dua leaving the masjid",      "The ark & the animals"),
    (10, "Al-Ikhlas v.3–4",             "ر Ra",    10,  "Duas review: days 7–9",       "Allah saved the believers — Nuh"),
    (11, "Al-Ikhlas — full review",      "ز Zay",   11,  "Dua for entering toilet",     "Who was Ibrahim (AS)?"),
    (12, "Al-Kawthar v.1",              "س Sin",   12,  "Dua for leaving toilet",      "Ibrahim (AS) & the fire"),
    (13, "Al-Kawthar v.2",              "ش Shin",  13,  "Dua before wudu",             "Ibrahim (AS) breaks the idols"),
    (14, "Al-Kawthar v.3 + review",     "ص Sad",   14,  "Dua after wudu",              "Ibrahim (AS) — lessons learnt"),
    (15, "Al-Asr v.1",                  "ض Dad",   15,  "Dua for eating at others",    "Who was Musa (AS)?"),
    (16, "Al-Asr v.2",                  "ط Ta",    16,  "Dua for sneezing",            "Baby Musa (AS) in the river"),
    (17, "Al-Asr v.3 + review",         "ظ Dha",   17,  "Reply to sneezing",           "Musa (AS) & Firawn"),
    (18, "An-Nasr v.1",                 "ع Ain",   18,  "Dua when it rains",           "Musa (AS) crosses the sea"),
    (19, "An-Nasr v.2",                 "غ Ghain", 19,  "Dua for travelling",          "Musa (AS) — lessons learnt"),
    (20, "An-Nasr v.3 + review",        "ف Fa",    20,  "Dua for returning home",      "Who was Eesa (AS)?"),
    (21, "Al-Falaq v.1",                "ق Qaf",   21,  "Dua before studying",         "Eesa (AS) born without a father"),
    (22, "Al-Falaq v.2",                "ك Kaf",   22,  "Dua after studying",          "Eesa (AS) heals the sick"),
    (23, "Al-Falaq v.3",                "ل Lam",   23,  "Dua for the parents",         "Eesa (AS) — lessons learnt"),
    (24, "Al-Falaq v.4–5 + review",     "م Mim",   24,  "Duas review: days 20–23",     "Big review: 5 prophets"),
    (25, "An-Nas v.1–2",                "ن Nun",   25,  "Dua for a good day",          "Stories of Prophets — quiz"),
    (26, "An-Nas v.3–4",                "و Waw",   26,  "Dua for starting anything",   "Stories of Prophets — quiz 2"),
    (27, "An-Nas v.5–6 + review",       "ه Ha",    27,  "Dua for the community",       "We are Muslims — what it means"),
    (28, "Al-Masad v.1–3",              "ي Ya",    28,  "Duas review: all 27 duas",    "Pillars of Islam — intro"),
    (29, "Al-Masad v.4–5 + review",     "— Harakaat: Fathah (َ )", 29, "Dua for Jannah",     "Pillars of Iman — intro"),
    (30, "Grand review — all 8 surahs", "— Harakaat: Kasrah & Dammah (ِ ُ)", 30, "Grand review — all duas", "Grand review: what did we learn?"),
]

# ── সেকশন হেডিং ── LessonSection (অনুরোধ ছাড়াই একবারই বানায়)
SECTIONS = [
    ("🕌 Surah Memorization",    "memorized_surah"),
    ("🔤 Arabic Letters (Qaida)","qirat"),
    ("📖 Hadith",                "memorized_hadith"),
    ("🤲 Dua & Manners",        "dua_masala"),
    ("📚 Story & Values",       "moral_story"),
]

# ── সিলেবাসের ৩০-দিনের টেবিল হেডার ──
SHEET_HEADERS = ["Day", "🕌 Surah", "🔤 Qaida", "📖 Hadith", "🤲 Dua", "📚 Story"]


def _qaida_course(Course):
    for w in ("qaida", "noorani", "নূরানী", "নুরানি", "easy"):
        c = Course.objects.filter(is_active=True, name__icontains=w).first()
        if c:
            return c
    return None


class Command(BaseCommand):
    help = "Easy Noorani Qaida কোর্সের ৩০-দিনের লেকচার প্ল্যান ও সিলেবাস লোড করে।"

    def handle(self, *args, **options):
        from django.apps import apps
        Course            = apps.get_model("core", "Course")
        AcademicBook      = apps.get_model("core", "AcademicBook")
        SyllabusItem      = apps.get_model("core", "SyllabusItem")
        CourseSyllabusSheet = apps.get_model("core", "CourseSyllabusSheet")
        Lecture           = apps.get_model("core", "Lecture")
        LessonSection     = apps.get_model("core", "LessonSection")
        LectureTopic      = apps.get_model("core", "LectureTopic")

        course = _qaida_course(Course)
        if course is None:
            raise CommandError(
                "Easy Noorani Qaida কোর্স পাওয়া যায়নি। "
                "আগে অ্যাডমিন প্যানেল থেকে 'Easy Noorani Qaida' নামে একটি কোর্স তৈরি করুন।"
            )

        self.stdout.write(f"কোর্স পাওয়া গেছে: {course.name}")

        # ── ১. AcademicBook — Lecture Sheet Book ──────────────────────────────
        book, created = AcademicBook.objects.get_or_create(
            name="Easy Noorani Qaida — Lecture Sheet Book",
            defaults={"file": "Books/Lecture Sheets/Easy Noorani Qaida/index.html"},
        )
        if created:
            course.books.add(book)
            self.stdout.write("  ✔ AcademicBook তৈরি হয়েছে এবং কোর্সে যুক্ত হয়েছে।")
        else:
            self.stdout.write("  · AcademicBook আগে থেকেই আছে।")

        # ── ২. CourseSyllabusSheet — ৩০-দিনের টেবিল ─────────────────────────
        sheet_rows = [
            [str(d), surah, qaida, f"#{hadith}", dua, story]
            for d, surah, qaida, hadith, dua, story in DAYS
        ]
        sheet, created = CourseSyllabusSheet.objects.get_or_create(
            course=course,
            defaults={"headers": SHEET_HEADERS, "rows": sheet_rows},
        )
        if created:
            self.stdout.write(f"  ✔ CourseSyllabusSheet তৈরি হয়েছে ({len(sheet_rows)} সারি)।")
        else:
            self.stdout.write("  · CourseSyllabusSheet আগে থেকেই আছে।")

        # ── ৩. SyllabusItem — ৫টি বিভাগ ──────────────────────────────────────
        SURAH_LIST = [
            "Al-Fatiha (7 verses)", "Al-Ikhlas (4 verses)",
            "Al-Kawthar (3 verses)", "Al-Asr (3 verses)", "An-Nasr (3 verses)",
            "Al-Falaq (5 verses)", "An-Nas (6 verses)", "Al-Masad (5 verses)",
        ]
        HADITH_LIST = [f"Hadith #{i}" for i in range(1, 31)]
        DUA_LIST = [
            "Bismillah", "Alhamdulillah", "Dua waking up", "Dua sleeping",
            "Dua entering home", "Dua leaving home", "Dua masjid (enter/leave)",
            "Dua wudu", "Dua toilet", "Dua travel", "Dua parents", "Dua Jannah",
        ]
        STORY_LIST = [
            "Introduction to Allah (Al-Khaliq, Ar-Rahman)",
            "Story of Adam (AS)",
            "Story of Nuh (AS)",
            "Story of Ibrahim (AS)",
            "Story of Musa (AS)",
            "Story of Eesa (AS)",
            "Pillars of Islam & Iman (intro)",
        ]
        QAIDA_LIST = [
            "28 Arabic Letters (Alif → Ya)",
            "Short vowels: Fathah, Kasrah, Dammah",
        ]

        SYLLABUS_SEEDS = [
            (SyllabusItem.Category.SURAH,  SURAH_LIST),
            (SyllabusItem.Category.HADITH, HADITH_LIST),
            (SyllabusItem.Category.DUA,    DUA_LIST),
            (SyllabusItem.Category.MORAL,  STORY_LIST),
            (SyllabusItem.Category.QIRAT,  QAIDA_LIST),
        ]
        added_items = 0
        for cat, items in SYLLABUS_SEEDS:
            for i, lesson in enumerate(items, start=1):
                _, created = SyllabusItem.objects.get_or_create(
                    course=course,
                    category=cat,
                    lesson=lesson,
                    defaults={"book": book, "order": i},
                )
                if created:
                    added_items += 1
        self.stdout.write(f"  ✔ SyllabusItem: {added_items} নতুন আইটেম যুক্ত হয়েছে।")

        # ── ৪. Lecture + LessonSection + LectureTopic ─────────────────────────
        added_lec = 0
        for day_no, surah, qaida, hadith_num, dua, story in DAYS:
            lecture, lec_created = Lecture.objects.get_or_create(
                course=course,
                no=day_no,
                defaults={"title": f"Day {day_no}"},
            )
            if lec_created:
                added_lec += 1

            # প্রতিটি লেকচারে ৫টি সেকশন
            topic_data = [
                ("🕌 Surah Memorization",     surah),
                ("🔤 Arabic Letters (Qaida)", qaida),
                (f"📖 Hadith #{hadith_num}",  dua),  # hadith শিরোনামে নং
                ("🤲 Dua & Manners",          dua),
                ("📚 Story & Values",         story),
            ]
            # সেকশনগুলো ঠিক করি — সব লেকচারের জন্য কোর্স-লেভেল
            for sec_order, (sec_name, _) in enumerate(topic_data, start=1):
                section, _ = LessonSection.objects.get_or_create(
                    course=course,
                    name=sec_name,
                    defaults={"order": sec_order},
                )
                # এই লেকচারে টপিক আছে কিনা চেক
                topic_text_map = {
                    "🕌 Surah Memorization":     surah,
                    "🔤 Arabic Letters (Qaida)": qaida,
                    f"📖 Hadith #{hadith_num}":  f"Hadith #{hadith_num} — learn & discuss",
                    "🤲 Dua & Manners":          dua,
                    "📚 Story & Values":         story,
                }
                topic_text = topic_text_map.get(sec_name, sec_name)
                LectureTopic.objects.get_or_create(
                    lecture=lecture,
                    section=section,
                    text=topic_text,
                    defaults={"order": sec_order},
                )

        self.stdout.write(f"  ✔ Lecture: {added_lec} নতুন লেকচার তৈরি হয়েছে।")
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ সম্পন্ন! '{course.name}' কোর্সে ৩০-দিনের পরিকল্পনা যুক্ত হয়েছে।\n"
            "এখন অ্যাপের Lecture Plan ও Syllabus ভিউতে এই তথ্য দেখা যাবে।"
        ))
