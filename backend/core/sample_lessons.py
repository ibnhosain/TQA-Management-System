# -*- coding: utf-8 -*-
"""দারসের স্ক্রিপ্ট — উস্তাদের কথা ও শিক্ষার্থীর পর্দা।

⚠️ এগুলো "নমুনা" নয়, আসল দারস। কোর্স তৈরির সময় (মাইগ্রেশন ০০৩৬) সরাসরি
বসে যায়, আর পরিচালক ইচ্ছামতো সম্পাদনা করতে পারেন — প্রতিটি ধাপ, প্রতিটি
পর্দা। ফাইল ও ফাংশনের পুরনো নাম (sample) রয়ে গেছে কেবল মাইগ্রেশনের
সাথে সংগতি রাখতে; নাম বদলালে পুরনো মাইগ্রেশন ভেঙে পড়ত।

⚠️ সবচেয়ে জরুরি নিয়ম — উস্তাদকে নিজে থেকে একটি ইংরেজি বাক্যও বানাতে
হবে না। স্ক্রিপ্টটা শুধু পড়ে শোনালেই পুরো ক্লাস হয়ে যাবে। তাই:

    says       → উস্তাদ হুবহু যা বলবেন (পড়ে ফেলার মতো)
    correction → ভুল হলে উস্তাদ হুবহু যা বলবেন — "শিশুকে বলুন…" নয়,
                 সরাসরি সেই কথাগুলোই
    does       → হাতে-মুখে যা করবেন (বলার নয়, করার) — খুব ছোট
    student    → শিক্ষার্থী যা করবে
    expected   → শিক্ষার্থীর মুখে যা শোনা যাবে (এটাই যাচাই)
    note       → উস্তাদের নিজের জন্য টীকা — মাখরাজ, সূত্র, অভিভাবকের কথা

⚠️ আরবির পাশে ইংরেজি উচ্চারণ কখনো লেখা হয় না — পরিচালকের নির্দেশ।
যেখানে উস্তাদকে আরবিটা মুখে বলতে হবে সেখানে ডট (…………) বসানো থাকে; তিনি
পর্দার আরবি দেখেই পড়বেন।

⚠️ বর্গাকার বন্ধনীর বাংলা কথাগুলো উস্তাদের নিজের জন্য — ওখানে থামতে হবে
বা কিছু করতে হবে, পড়ে শোনাতে হবে না।

⚠️ ভাষা — ৫ বছরের বাচ্চা যা বুঝবে:
    • খুব ছোট বাক্য, সহজ শব্দ (big, small, open, close, out, in)
    • শরীরের চেনা শব্দ — mouth, tongue, lips, teeth, throat
    • কঠিন শব্দ নয় (firmly, release, position, pronounce — এসব বাদ)
    • খেলার ঢঙে, প্রশংসা মিশিয়ে

কাঠামো — প্রতিটি ধাপে দুটি অংশ:
    উস্তাদের অংশ : উপরের ঘরগুলো
    পর্দার অংশ   : slide (kind, heading, arabic, translit, text)
শিক্ষার্থী কেবল slide-টুকুই দেখেন।

⚠️ কুরআনের আরবি `locked=True` দিয়ে রাখা — উসমানী রসম, হাফস 'আন 'আসিম,
যাচাই করা লেখা। সাধারণ সম্পাদনায় বদলানো যাবে না; যের-যবর-তানভীন ও ওয়াক্ফ
চিহ্ন হুবহু সংরক্ষিত।

⚠️ ফাযীলত/হাদীস কেবল সহীহ সূত্রসহ — `note`-এ সূত্র লেখা থাকে। সূত্র ছাড়া
কোনো ফাযীলত এখানে যোগ করা যাবে না।

মডেলগুলো বাইরে থেকে দেওয়া হয় (মাইগ্রেশন ঐতিহাসিক মডেল পাঠায়, ভিউ আসলটা)
— তাই ভবিষ্যতে মডেল বদলালেও পুরনো মাইগ্রেশন ভাঙে না।
"""

import re

# ─────────────────────────── সূরা আল-ইখলাস · ৫–৭ বছর ───────────────────────────
# উসমানী রসম, হাফস 'আন 'আসিম — সূরা ১১২, আয়াত ১–৪
# ⚠️ আয়াতের শেষে মুসহাফের গোল নকশা — ۝ (U+06DD) আর তার সাথে আরবি
# সংখ্যা। Amiri Quran ফন্ট এদুটো মিলিয়ে ঠিক মুসহাফের মতো গোল চিহ্নের
# ভেতরে সংখ্যাটি বসিয়ে দেয়।
#
# ⚠️ ওয়াকফ চিহ্ন (ۖ ۗ ۘ ۙ ۚ) ইচ্ছা করেই দেওয়া হয়নি — সূরা ইখলাসের
# মুসহাফে কোনো ওয়াকফ চিহ্ন নেই। আয়াতগুলো ছোট, প্রতিটি শেষ হয়
# আয়াত-চিহ্নেই। না থাকা চিহ্ন বসালে কুরআনের পাঠ বিকৃত হতো।
V1 = "قُلْ هُوَ ٱللَّهُ أَحَدٌ ۝١"
V2 = "ٱللَّهُ ٱلصَّمَدُ ۝٢"
V3 = "لَمْ يَلِدْ وَلَمْ يُولَدْ ۝٣"
V4 = "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ ۝٤"

# ⚠️ আয়াতের টুকরোগুলো হাতে লেখা হয়নি — যাচাই করা আয়াত থেকেই কেটে নেওয়া।
# তাই একটি যের-যবর-শাদ্দাও এদিক-ওদিক হওয়ার সুযোগ নেই।
_W1, _W2, _W3, _W4 = V1.split(), V2.split(), V3.split(), V4.split()
C_QUL = _W1[0]                       # قُلْ
C_HUWALLAH = " ".join(_W1[1:3])      # هُوَ ٱللَّهُ
C_AHAD = _W1[3]                      # أَحَدٌ
C_ALLAH = _W2[0]                     # ٱللَّهُ
C_SAMAD = _W2[1]                     # ٱلصَّمَدُ
C_YALID = " ".join(_W3[0:2])         # لَمْ يَلِدْ
C_YULAD = " ".join(_W3[2:4])         # وَلَمْ يُولَدْ
C_YAKUN = " ".join(_W4[0:2])         # وَلَمْ يَكُن
C_LAHU = _W4[2]                      # لَّهُۥ
C_KUFUWAN = _W4[3]                   # كُفُوًا
C_AHADUN = _W4[4]                    # أَحَدٌۢ

ALL_FOUR = V1 + "\n" + V2 + "\n" + V3 + "\n" + V4

# ⚠️ আরবির পাশে ইংরেজি উচ্চারণ কখনো লেখা হয় না। যেখানে উস্তাদকে আরবিটা
# মুখে বলতে হবে সেখানে এই ডটগুলো — তিনি পর্দার আরবি দেখে পড়বেন।
DOTS = "…………"


def _chunk(section, arabic, lead, correction, note="", seconds=50):
    """একটি ছোট টুকরো শেখানোর ধাপ — শোনা, বলা, আবার বলা।

    উস্তাদ শুধু পড়ে যাবেন। বর্গাকার বন্ধনীর বাংলা কথাগুলো তাঁর নিজের
    জন্য — ওখানে থামতে হবে, বলতে হবে না। আর ডটের জায়গায় পর্দার আরবিটাই
    মুখে পড়তে হবে।
    """
    return {
        "section": section,
        "says": (
            lead + "\n"
            "Listen carefully.\n"
            + DOTS + "\n"
            "[পর্দার আরবি টুকরোটি ধীরে ও স্পষ্ট করে পড়ুন]\n\n"
            "Now you say it.\n"
            "[অপেক্ষা করুন — শিশু বলবে]\n\n"
            "MashaAllah! Very good.\n"
            "Let's do it one more time.\n"
            + DOTS + "\n"
            "[আবার পড়ুন, তারপর অপেক্ষা করুন]\n\n"
            "Excellent! ⭐"
        ),
        "does": "পর্দার টুকরোটি দেখিয়ে ধীরে পড়ুন। শিশু না বলা পর্যন্ত "
                "অপেক্ষা করুন — তাড়া দেবেন না।",
        "student": "টুকরোটি বলে, তারপর আবার বলে।",
        "expected": arabic,
        "correction": correction,
        "note": note,
        "seconds": seconds,
        "slide": {"kind": "verse", "heading": "Say it with me",
                  "arabic": arabic, "text": "🎤"},
    }


IKHLAS = {
    "title": "Surah Al-Ikhlas",
    "title_ar": "الإخلاص",
    "kind": "memorization",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 30,
    "objectives": (
        "<p><b>Surah Al-Ikhlas — Complete Teacher Script</b><br>"
        "Age 5–7 · about 30 minutes · Qur'an Memorization<br>"
        "Listen → Repeat → Connect → Recall → Recite</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause and wait.</li>"
        "<li>Where you see <b>…………</b>, recite the Arabic shown on the "
        "screen. Arabic is never written in English letters.</li>"
        "<li>If the child gets tired, stop after the four-finger game "
        "(Part 12) and do the rest next class. Two short happy classes "
        "beat one long tired one.</li>"
        "</ul>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Say all four verses of Surah Al-Ikhlas</li>"
        "<li>Say the whole Surah from memory, without looking</li>"
        "<li>Keep the four verses in the right order</li>"
        "<li>Answer: Is Allah One? Do we need Allah? Is anyone like Allah?</li>"
        "</ul>"
        "<p><b>Mastery</b> — all four verses alone, in order, no missing or "
        "swapped word, recovering after at most a one-word hint. Saying it "
        "a few times with you is <i>not</i> mastery.</p>"
        "<p><b>Revision</b> — same day: one recall from memory. Next class: "
        "say it before the new lesson. Then once a week for four weeks.</p>"
    ),
    "steps": [
        # ═══════════════ PART 1 — WELCOME ═══════════════
        {
            "section": "Part 1 — Welcome",
            "says": "Assalamu alaikum, my dear student!\n"
                    "How are you today?\n"
                    "[অপেক্ষা করুন — শিশু উত্তর দেবে]\n\n"
                    "MashaAllah! I'm very happy to see you today.",
            "does": "হাসুন, হাত নাড়ুন। নাম ধরে একবার ডাকুন। উত্তরের জন্য "
                    "অপেক্ষা করুন — এই সময়টুকুই শিশুকে সহজ করে দেয়।",
            "student": "সালামের জবাব দেয় ও উত্তর দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": "That's okay! Listen to me.\n"
                          "Assalamu alaikum.\n"
                          "Now you say it back to me.\n"
                          "[অপেক্ষা করুন]\n\n"
                          "MashaAllah! Very good.",
            "note": "শুরুটা উষ্ণ ও ছোট রাখুন। এখনই পড়ানো শুরু নয়।",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Surah Al-Ikhlas",
                      "arabic": "الإخلاص", "text": "Assalamu alaikum! 🌙"},
        },
        {
            "section": "Part 1 — Ready?",
            "says": "Are you ready to learn a beautiful Surah from the "
                    "Qur'an?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Wonderful!\n"
                    "Today, inshaAllah, we'll learn Surah Al-Ikhlas.\n"
                    "It's a very short Surah.\n"
                    "It has only four verses.\n"
                    "Look at my hand. One, two, three, four!",
            "does": "চারটি আঙুল তুলে একসাথে গুনুন। এই চার আঙুলই পরে স্মৃতির "
                    "খেলায় কাজে লাগবে — একই হাত ব্যবহার করুন।",
            "student": "উত্তর দেয়, চারটি আঙুল দেখে।",
            "expected": "Yes! — আর চারটি আঙুলের দিকে তাকায়।",
            "correction": "Show me four fingers. Like this.\n"
                          "One, two, three, four.\n"
                          "Well done!",
            "note": "সূরা ১১২, চার আয়াত, মাক্কী।",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Only Four Verses",
                      "arabic": "الإخلاص", "text": "1️⃣  2️⃣  3️⃣  4️⃣"},
        },
        {
            "section": "Part 1 — How we'll learn",
            "says": "Don't worry if you can't remember everything today.\n"
                    "I'll say it first.\n"
                    "You'll listen.\n"
                    "Then you'll say it after me.\n"
                    "We'll practise together.\n"
                    "And then you'll try by yourself.\n"
                    "Are you ready?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Excellent! Let's begin. 🌟",
            "does": "শান্ত ও উৎসাহী গলায় বলুন। শিশুর ভয় কাটানোই এই ধাপের কাজ।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes! / মাথা নাড়ে।",
            "correction": "It's very easy. I'll help you.\n"
                          "We'll do it together.\n"
                          "Ready? Let's begin!",
            "note": "",
            "seconds": 35,
            "slide": {"kind": "title", "heading": "Let's begin!",
                      "text": "👂 Listen\n🎤 Say it\n🌟 Try alone"},
        },

        # ═══════════════ PART 2 — LISTEN ═══════════════
        {
            "section": "Part 2 — Just listen",
            "says": "Before we start, I want you to do one thing.\n"
                    "Just listen to me.\n"
                    "Don't repeat yet.\n"
                    "Sit nicely and listen carefully.\n"
                    + DOTS + "\n"
                    "[পুরো সূরাটি একবার ধীরে ও সুন্দর করে পড়ুন]",
            "does": "পুরো সূরাটি একবার ধীরে ও সুন্দর করে পড়ুন। তাড়াহুড়ো নয়।",
            "student": "চুপ করে শোনে।",
            "expected": "চুপ করে শোনা। ঠোঁট নড়লে সেটা ভালো লক্ষণ।",
            "correction": "Sshh — just listen this time.\n"
                          "Your turn is coming. I promise!\n"
                          "Listen again.",
            "note": "এই প্রথম শোনাটাই বাচ্চার মনে সুরটা বসিয়ে দেয় — যেভাবে "
                    "পড়বেন, সে হুবহু সেভাবেই শিখবে। ভালো করে পড়ুন।",
            "seconds": 65,
            "slide": {"kind": "listen", "heading": "Listen",
                      "arabic": ALL_FOUR, "text": "👂 Just listen."},
        },

        # ═══════════════ PART 3 — VERSE 1 ═══════════════
        _chunk(
            "Part 3 — قُلْ", C_QUL,
            "MashaAllah.\n"
            "Now we'll learn it one little part at a time.\n"
            "Let's start with the first verse.",
            "So close! Watch my mouth.\n"
            + DOTS + "\n"
            "[টুকরোটি আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "MashaAllah! That's it.",
            seconds=55,
        ),
        _chunk(
            "Part 3 — هُوَ ٱللَّهُ", C_HUWALLAH,
            "Now the next part.",
            "Nearly! Let's go very slowly.\n"
            + DOTS + "\n"
            "[শব্দ দুটি আলাদা আলাদা করে পড়ুন, তারপর জোড়া লাগান]\n\n"
            "Now you say it.\n"
            "[অপেক্ষা করুন]\n\n"
            "Excellent!",
        ),
        _chunk(
            "Part 3 — أَحَدٌ", C_AHAD,
            "Now the last part of this verse.",
            "Listen to the end of the word.\n"
            + DOTS + "\n"
            "[শেষের অংশটা একটু টেনে স্পষ্ট করে পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "MashaAllah!",
            note="শেষের তানভীনটা যেন হারিয়ে না যায় — শব্দটা আলাদা করে "
                 "তিনবার বলান।",
        ),
        {
            "section": "Part 3 — Join verse 1",
            "says": "Now we'll put our little pieces together.\n"
                    "Listen to me first.\n"
                    + DOTS + "\n"
                    "[পুরো ১ম আয়াতটি ধীরে পড়ুন]\n\n"
                    "Now you try.\n"
                    "[অপেক্ষা করুন — শিশু বলবে]\n\n"
                    "MashaAllah! 🌟\n"
                    "Let's say it together one more time.\n"
                    "[শিশুর সাথে একসাথে পড়ুন]",
            "does": "প্রথমে একা পড়ুন, তারপর শিশু একা, তারপর দুজনে একসাথে।",
            "student": "পুরো আয়াতটি বলে।",
            "expected": V1,
            "correction": "You're doing so well!\n"
                          "Here's a little help.\n"
                          + DOTS + "\n"
                          "[কেবল প্রথম শব্দটুকু বলুন, বাকিটা শিশু বলবে]\n\n"
                          "MashaAllah! You did it!",
            "note": "ইশারা দিন কেবল প্রথম শব্দটুকু — পুরো আয়াত বলে দেবেন না।",
            "seconds": 65,
            "slide": {"kind": "verse", "heading": "Verse 1",
                      "arabic": V1, "text": "🎤 All together now"},
        },
        {
            "section": "Part 4 — Meaning of verse 1",
            "says": "Now let's learn what this verse means.\n"
                    "It says — Allah is One.\n"
                    "Tell me, how many Allah?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! Yes.\n"
                    "Allah is One.\n"
                    "Not two. Not three. Just One!",
            "does": "একটি আঙুল তুলে ধরুন। উত্তরের জন্য অপেক্ষা করুন।",
            "student": "উত্তর দেয়।",
            "expected": "One!",
            "correction": "Look at my hand. One finger.\n"
                          "Just one!\n"
                          "Now you tell me — how many Allah?\n"
                          "[অপেক্ষা করুন]\n\n"
                          "Well done!",
            "note": "অনুবাদ: 'বলো, তিনি আল্লাহ, এক।' উপরের কথাগুলো বাচ্চার "
                    "জন্য সহজ ব্যাখ্যা, অনুবাদ নয়।",
            "seconds": 45,
            "slide": {"kind": "meaning", "heading": "Allah is One",
                      "arabic": V1, "text": "1️⃣\nAllah is One. ☝️"},
        },

        # ═══════════════ PART 5 — VERSE 2 ═══════════════
        _chunk(
            "Part 5 — ٱللَّهُ", C_ALLAH,
            "Excellent! Now the second verse.",
            "Listen again.\n"
            + DOTS + "\n"
            "[আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "Very good!",
        ),
        _chunk(
            "Part 5 — ٱلصَّمَدُ", C_SAMAD,
            "Now listen to this one.",
            "Nearly! This one has a big fat sound.\n"
            "Make your mouth round, like this.\n"
            + DOTS + "\n"
            "[কেবল ভারী হরফটুকু তিনবার বলুন, তারপর পুরো শব্দ]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "MashaAllah!",
            note="ص একটি ভারী হরফ — এই সূরার সবচেয়ে বেশি ভুল হওয়া জায়গা। "
                 "নিয়মের নাম বলবেন না, শুধু করে দেখান।",
            seconds=55,
        ),
        {
            "section": "Part 5 — Join verse 2",
            "says": "Now let's put them together.\n"
                    + DOTS + "\n"
                    "[২য় আয়াতটি ধীরে পড়ুন]\n\n"
                    "Now you try.\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Excellent! 🌟\n"
                    "One more time, together.\n"
                    "[একসাথে পড়ুন]",
            "does": "একা, তারপর শিশু, তারপর একসাথে।",
            "student": "পুরো ২য় আয়াতটি বলে।",
            "expected": V2,
            "correction": "Let's try again slowly.\n"
                          + DOTS + "\n"
                          "[কেবল প্রথম শব্দটুকু বলুন]\n\n"
                          "MashaAllah!",
            "note": "",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 2",
                      "arabic": V2, "text": "🎤 All together now"},
        },
        {
            "section": "Part 6 — Meaning of verse 2",
            "says": "Now let's understand this verse.\n"
                    "It means we need Allah.\n"
                    "Tell me — do we need Allah?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Very good!\n"
                    "Now tell me — does Allah need us?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah!\n"
                    "We need Allah.\n"
                    "Allah doesn't need anyone.",
            "does": "দুটি প্রশ্নেই আলাদা করে অপেক্ষা করুন। তাড়াহুড়ো করবেন না।",
            "student": "দুটি প্রশ্নের উত্তর দেয়।",
            "expected": "Yes! … No!",
            "correction": "Who gives you your food?\n"
                          "[অপেক্ষা করুন]\n\n"
                          "Yes — Allah gives us everything.\n"
                          "So we need Allah.\n"
                          "Say it with me — we need Allah.",
            "note": "অনুবাদ: 'আল্লাহ অমুখাপেক্ষী।' এই বয়সে প্রথম অংশটুকুই যথেষ্ট।",
            "seconds": 55,
            "slide": {"kind": "question", "heading": "Do we need Allah?",
                      "arabic": V2,
                      "text": "We need Allah. 🤲\nAllah needs no one."},
        },
        {
            "section": "Part 7 — Connect verse 1 + 2",
            "says": "Now let's see if you remember the first two verses "
                    "together.\n"
                    "I'll help you.\n"
                    + DOTS + "\n"
                    "[১ম ও ২য় আয়াত একসাথে ধীরে পড়ুন]\n\n"
                    "Now you try.\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! Excellent!\n"
                    "You're doing a great job!",
            "does": "দুই আয়াত একসাথে পড়ুন, তারপর শিশুকে একা বলতে দিন।",
            "student": "দুই আয়াত একসাথে বলে।",
            "expected": V1 + " " + V2,
            "correction": "You said verse one — lovely!\n"
                          "Verse two comes next.\n"
                          + DOTS + "\n"
                          "[কেবল ২য় আয়াতের প্রথম শব্দটুকু বলুন]\n\n"
                          "Off you go!",
            "note": "শুরুতেই জোড়া লাগানো জরুরি — নইলে প্রতিটি আয়াত আলাদা "
                    "দ্বীপের মতো মুখস্থ হয়, এক আয়াত থেকে পরেরটায় যেতে পারে না।",
            "seconds": 55,
            "slide": {"kind": "repeat", "heading": "Verses 1 and 2",
                      "arabic": V1 + "\n" + V2, "text": "🎤 Together now"},
        },

        # ═══════════════ PART 8 — VERSE 3 ═══════════════
        {
            "section": "Part 8 — Verse 3 begins",
            "says": "Now we're ready for verse number three.\n"
                    "This verse is a little different.\n"
                    "So listen very carefully.\n"
                    "Don't worry. We'll learn it slowly.",
            "does": "শিশুকে একটু সোজা হয়ে বসতে বলুন। এই আয়াতে মনোযোগ বেশি লাগে।",
            "student": "শোনে।",
            "expected": "মনোযোগ ফিরে এসেছে।",
            "correction": "Look at me. Are you ready?\n"
                          "It's easy. I'll help you.",
            "note": "",
            "seconds": 25,
            "slide": {"kind": "title", "heading": "Verse 3",
                      "arabic": V3, "text": "👂 Listen very carefully"},
        },
        _chunk(
            "Part 8 — لَمْ يَلِدْ", C_YALID,
            "Listen to the first part.",
            "Almost! Listen once more.\n"
            + DOTS + "\n"
            "[আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "MashaAllah!",
        ),
        _chunk(
            "Part 8 — وَلَمْ يُولَدْ", C_YULAD,
            "Now the second part.\n"
            "Careful — this one sounds a little like the first one.",
            "Listen to the two together.\n"
            + DOTS + "\n"
            "[দুই টুকরো পরপর পড়ুন — প্রথমটায় একবার তালি, দ্বিতীয়টায় দুবার]\n\n"
            "Did you hear the difference?\n"
            "Now you say the second one.\n"
            "[অপেক্ষা করুন]\n\n"
            "Excellent!",
            note="এই দুটি শব্দ উল্টে ফেলাই এই সূরার সবচেয়ে সাধারণ ভুল। "
                 "তালির ছন্দে ক্রমটা মনে থাকে।",
            seconds=60,
        ),
        {
            "section": "Part 8 — Join verse 3",
            "says": "Now listen to the whole verse.\n"
                    + DOTS + "\n"
                    "[৩য় আয়াতটি ধীরে পড়ুন]\n\n"
                    "Now you try.\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! 🌟",
            "does": "একা পড়ুন, তারপর শিশু একা।",
            "student": "পুরো ৩য় আয়াতটি বলে।",
            "expected": V3,
            "correction": "Let's clap.\n"
                          "One clap for the first part.\n"
                          "Two claps for the second part.\n"
                          + DOTS + "\n"
                          "[তালির সাথে আয়াতটি পড়ুন]\n\n"
                          "Now you say it with the claps.\n"
                          "You did it!",
            "note": "",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 3",
                      "arabic": V3, "text": "🎤 All together now"},
        },
        {
            "section": "Part 9 — Meaning of verse 3",
            "says": "Now let's understand this verse.\n"
                    "Allah doesn't have children.\n"
                    "And Allah wasn't born.\n"
                    "Tell me — does Allah have children?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Very good!\n"
                    "Was Allah born?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! Allah was always here.",
            "does": "দুটি প্রশ্নেই আলাদা করে অপেক্ষা করুন।",
            "student": "দুটি প্রশ্নের উত্তর দেয়।",
            "expected": "No! … No!",
            "correction": "Listen again.\n"
                          "Allah has no mummy. No daddy. No baby.\n"
                          "Allah was always here.\n"
                          "Now you tell me — was Allah born?\n"
                          "[অপেক্ষা করুন]\n\n"
                          "Well done!",
            "note": "অনুবাদ: 'তিনি কাউকে জন্ম দেননি, তাঁকেও জন্ম দেওয়া হয়নি।' "
                    "গভীর আলোচনায় যাবেন না।",
            "seconds": 50,
            "slide": {"kind": "question", "heading": "Was Allah born?",
                      "arabic": V3, "text": "No! ✨\nAllah was always here."},
        },

        # ═══════════════ PART 10 — VERSE 4 ═══════════════
        {
            "section": "Part 10 — The last verse",
            "says": "We're now at the last verse.\n"
                    "It's a little long.\n"
                    "So we'll learn it in very small pieces.\n"
                    "Listen carefully.",
            "does": "শিশুকে উৎসাহ দিন — শেষ আয়াত, প্রায় হয়েই গেছে।",
            "student": "শোনে।",
            "expected": "মনোযোগ আছে।",
            "correction": "You have done three verses already!\n"
                          "Only one more. You can do it!",
            "note": "এটি সবচেয়ে লম্বা আয়াত — টুকরো করাই এর চাবি।",
            "seconds": 25,
            "slide": {"kind": "title", "heading": "The Last Verse",
                      "arabic": V4, "text": "🌟 Almost done!"},
        },
        _chunk(
            "Part 10 — وَلَمْ يَكُن", C_YAKUN, "Listen.",
            "Listen once more.\n"
            + DOTS + "\n"
            "[আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "Very good!",
            seconds=45,
        ),
        _chunk(
            "Part 10 — لَّهُۥ", C_LAHU, "Now this small one.",
            "It's a tiny word.\n"
            + DOTS + "\n"
            "[আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "Excellent!",
            seconds=40,
        ),
        _chunk(
            "Part 10 — كُفُوًا", C_KUFUWAN, "Now listen.",
            "Let's go slowly, piece by piece.\n"
            + DOTS + "\n"
            "[শব্দটি ভেঙে ধীরে পড়ুন, তারপর একসাথে]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "Very good!",
            seconds=45,
        ),
        _chunk(
            "Part 10 — أَحَدٌۢ", C_AHADUN,
            "And the last one.\nYou know this word already!",
            "Yes — we said this word in verse one!\n"
            + DOTS + "\n"
            "[আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "MashaAllah!",
            seconds=40,
        ),
        {
            "section": "Part 10 — Join verse 4",
            "says": "Now listen carefully to the whole verse.\n"
                    + DOTS + "\n"
                    "[৪র্থ আয়াতটি ধীরে পড়ুন]\n\n"
                    "Now you try.\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! You did it!",
            "does": "প্রথমে দুই টুকরোয় ভেঙে দিন, তারপর জোড়া লাগান।",
            "student": "পুরো ৪র্থ আয়াতটি বলে।",
            "expected": V4,
            "correction": "That's a long one!\n"
                          "Let's do just the first half.\n"
                          + DOTS + "\n"
                          "[কেবল প্রথম অর্ধেকটা পড়ুন]\n\n"
                          "Good! We'll do the rest next time.",
            "note": "শিশু না পারলে জোর করবেন না — অর্ধেক মুখস্থ হওয়া, "
                    "পুরোটা ভুলে যাওয়ার চেয়ে অনেক ভালো।",
            "seconds": 70,
            "slide": {"kind": "verse", "heading": "Verse 4",
                      "arabic": V4, "text": "🎤 All together now"},
        },
        {
            "section": "Part 11 — Meaning of verse 4",
            "says": "This verse teaches us something very important.\n"
                    "Nobody is like Allah.\n"
                    "Tell me — is anyone like Allah?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah!\n"
                    "Nobody is like Allah.\n"
                    "Allah is the greatest.",
            "does": "'nobody' বলার সময় ধীরে মাথা নাড়ুন।",
            "student": "উত্তর দেয়।",
            "expected": "No!",
            "correction": "Is anyone as big as Allah? No!\n"
                          "Is anyone like Allah? No!\n"
                          "Say it with me — nobody is like Allah.",
            "note": "অনুবাদ: 'আর তাঁর সমকক্ষ কেউ নেই।'",
            "seconds": 45,
            "slide": {"kind": "question", "heading": "Is anyone like Allah?",
                      "arabic": V4, "text": "No! 💚\nNobody is like Allah."},
        },

        # ═══════════════ PART 12 — খেলা ═══════════════
        {
            "section": "Part 12 — Four-finger memory game",
            "says": "Now let's play a little memory game.\n"
                    "Show me your fingers!\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Great!\n"
                    "Number one! Allah is…\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah!\n"
                    "Number two! We need…\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Excellent!\n"
                    "Number three! Was Allah born?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Very good!\n"
                    "Number four! Is anyone like Allah?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! 🌟",
            "does": "প্রতিটি প্রশ্নে একটি করে আঙুল তুলুন — এক, দুই, তিন, চার।",
            "student": "প্রতিটি প্রশ্নের উত্তর দেয়।",
            "expected": "One! … Allah! … No! … No!",
            "correction": "Look at my finger. Number one.\n"
                          "Allah is… One!\n"
                          "Say it with me — One!\n"
                          "Well done!",
            "note": "নড়াচড়া ক্রম মনে রাখতে সাহায্য করে — শুধু বারবার বলার "
                    "চেয়ে বেশি। হাতটাই বাচ্চার নিজের মনে করিয়ে দেওয়ার যন্ত্র।",
            "seconds": 80,
            "slide": {"kind": "activity", "heading": "Four-Finger Game",
                      "text": "1️⃣ Allah is One\n2️⃣ We need Allah\n"
                              "3️⃣ Allah wasn't born\n"
                              "4️⃣ Nobody is like Allah"},
        },
        {
            "section": "Part 13 — Look and hide",
            "says": "Now let's see how much you remember.\n"
                    "Look at the screen. Read it with me.\n"
                    "[একসাথে পড়ুন]\n\n"
                    "Excellent!\n"
                    "Now I'm going to hide it.\n"
                    "[পর্দা খালি করুন]\n\n"
                    "Can you say it?\n"
                    "[অপেক্ষা করুন — পাঁচ পর্যন্ত গুনুন]\n\n"
                    "MashaAllah!",
            "does": "প্রথমে আয়াত দেখিয়ে একসাথে পড়ুন, তারপর খালি পর্দায় যান। "
                    "চুপ থাকুন — নীরবতাতেই স্মৃতি তৈরি হয়।",
            "student": "মুখস্থ থেকে বলে।",
            "expected": "আয়াতগুলো, ছোটখাটো থামা চলবে।",
            "correction": "You're doing so well!\n"
                          "Here's a little hint.\n"
                          + DOTS + "\n"
                          "[কেবল প্রথম শব্দটুকু বলুন]\n\n"
                          "MashaAllah!",
            "note": "শিশু ক্লান্ত হলে জোর করবেন না। ইশারা দিন কেবল এক শব্দের।",
            "seconds": 80,
            "slide": {"kind": "blank", "heading": "Look & Hide",
                      "text": "🙈 Can you say it by heart?"},
        },

        # ═══════════════ PART 14–17 ═══════════════
        {
            "section": "Part 14 — The whole Surah",
            "says": "We have learned all four verses!\n"
                    "Now let's recite the whole Surah together.\n"
                    + DOTS + "\n"
                    "[শিশুর সাথে একসাথে পুরো সূরা পড়ুন]\n\n"
                    "MashaAllah! 🌟\n"
                    "You did a wonderful job!",
            "does": "শান্ত গতিতে একসাথে পড়ুন। ছোটখাটো ভুলে থামবেন না।",
            "student": "সাথে পুরো সূরা বলে।",
            "expected": "পুরো সূরা উস্তাদের সাথে।",
            "correction": "Let's go a bit slower.\n"
                          "Slow and beautiful. From the start again.",
            "note": "",
            "seconds": 70,
            "slide": {"kind": "repeat", "heading": "All Four Verses",
                      "arabic": ALL_FOUR,
                      "text": "🎤 Together, from the start"},
        },
        {
            "section": "Part 15 — All by yourself",
            "says": "Now I want you to try by yourself.\n"
                    "You can do it.\n"
                    "Take your time.\n"
                    "If you forget something, don't worry. I'll help you.\n"
                    "[একদম চুপ থাকুন — শিশু একা পড়বে]",
            "does": "একদম চুপ থাকুন। কোথায় থেমে যাচ্ছে তা মনে রাখুন, কিন্তু "
                    "পড়ার মাঝে থামাবেন না।",
            "student": "একা পুরো সূরা বলে।",
            "expected": "চার আয়াত একা, ঠিক ক্রমে, এক শব্দের ইশারাতেই সামলে "
                        "নেওয়া — আজকের জন্য এটাই মুখস্থ হওয়া।",
            "correction": "That's okay. Let's try that part again.\n"
                          + DOTS + "\n"
                          "[কেবল প্রথম শব্দটুকু বলুন, বাকিটা শিশু বলবে]\n\n"
                          "MashaAllah! You remembered!",
            "note": "⚠️ ভুল হলে কখনোই 'Wrong' বলবেন না। বলুন 'That's okay' — "
                    "তারপর সবচেয়ে ছোট ইশারাটুকু দিন। শেষে কেবল একটি জিনিস "
                    "শুধরে দিন, একের বেশি নয়।",
            "seconds": 80,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "text": "🎤 I'm listening.\nTake your time."},
        },
        {
            "section": "Part 16 — Final review",
            "says": "Before we finish, let's remember what our Surah "
                    "teaches us.\n"
                    "Is Allah One?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Do we need Allah?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Does Allah need anyone?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Was Allah born?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Does Allah have children?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Is anyone like Allah?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! 🌟 You remembered very well!",
            "does": "প্রতিটি প্রশ্নের পরেই থামুন। দ্রুত জিজ্ঞেস করবেন না।",
            "student": "ছয়টি প্রশ্নের উত্তর দেয়।",
            "expected": "Yes! … Yes! … No! … No! … No! … No!",
            "correction": "Let's do that one again.\n"
                          "Allah is… One!\n"
                          "Now you say it.\n"
                          "[অপেক্ষা করুন]\n\n"
                          "Well done!",
            "note": "এই সূরার শিক্ষা: তাওহীদ — আল্লাহ এক, তিনি কারও "
                    "মুখাপেক্ষী নন, আর কেউ তাঁর মতো নয়।",
            "seconds": 70,
            "slide": {"kind": "review", "heading": "What did we learn?",
                      "text": "☝️ Allah is One\n🤲 We need Allah\n"
                              "✨ Allah was always here\n"
                              "💚 Nobody is like Allah"},
        },
        {
            "section": "Part 16 — A big secret",
            "says": "Do you know a secret?\n"
                    "This little Surah is very big with Allah!\n"
                    "Our Prophet ﷺ told us something amazing.\n"
                    "Saying it's like reading a third of the Qur'an!",
            "does": "বিস্ময় নিয়ে বলুন। আবার চার আঙুল দেখান — এত ছোট সূরা, "
                    "এত বড় পুরস্কার।",
            "student": "শোনে।",
            "expected": "খুশি — বাড়িতেও পড়ার আগ্রহ।",
            "correction": "It's a small Surah, right?\n"
                          "But Allah loves it so much.\n"
                          "Say it lots at home!",
            "note": "সহীহ: নবী ﷺ বলেছেন কুল হুওয়াল্লাহু আহাদ কুরআনের এক "
                    "তৃতীয়াংশের সমান — সহীহ বুখারী ৫০১৩, সহীহ মুসলিম ৮১১। "
                    "এর বেশি বাড়াবেন না, সূত্রহীন কোনো ফাযীলত যোগ করবেন না।",
            "seconds": 40,
            "slide": {"kind": "reminder", "heading": "A Big Secret!",
                      "text": "This little Surah is like reading\n"
                              "a third of the Qur'an. 🌙"},
        },
        {
            "section": "Part 17 — Homework",
            "says": "Today you learned Surah Al-Ikhlas.\n"
                    "You learned that Allah is One.\n"
                    "You learned that we need Allah.\n"
                    "You learned that Allah wasn't born.\n"
                    "And nobody is like Allah.\n"
                    "Now a little homework.\n"
                    "Practise this Surah with your parents every day.\n"
                    "Just a few minutes. Can you do that?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah!",
            "does": "ধীরে বলুন — পাশে অভিভাবক থাকলে তিনিও যেন শুনে নিতে পারেন।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": "Just a few minutes a day.\n"
                          "That's very small, right?\n"
                          "You can do it!",
            "note": "অভিভাবকের জন্য — শুধু শুনুন আর হাসুন। রোজ অল্প করে "
                    "শোনাই একবারে অনেকক্ষণের চেয়ে ভালো। জোর করা বা বকা নয়; "
                    "আটকে গেলে প্রথম শব্দটা বলে দিন, বাকিটা সে করবে।",
            "seconds": 50,
            "slide": {"kind": "homework", "heading": "Until Next Time",
                      "text": "📖 Practise every day\n🤲 And say it in Salah"},
        },
        {
            "section": "Part 17 — Closing",
            "says": "Now let's recite it one more time together.\n"
                    + DOTS + "\n"
                    "[শিশুর সাথে একসাথে পুরো সূরা পড়ুন]\n\n"
                    "MashaAllah! Excellent work today! 🌟\n"
                    "May Allah help you memorise the Qur'an.\n"
                    "And may Allah make you love the Qur'an.\n"
                    "JazakAllahu khairan.\n"
                    "Assalamu alaikum wa rahmatullah!",
            "does": "হাসুন। উষ্ণভাবে শেষ করুন, হঠাৎ নয়।",
            "student": "সাথে পড়ে, তারপর সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": "Assalamu alaikum!\n"
                          "Say it back to me.\n"
                          "[অপেক্ষা করুন]\n\n"
                          "See you next time!",
            "note": "শেষ করার আগে মিলিয়ে নিন: পড়ে শুনিয়েছেন · শিশু শুনেছে · "
                    "চার আয়াতই টুকরো করে করানো হয়েছে · আয়াত জোড়া লাগানো "
                    "হয়েছে · ভারী হরফ দেখা হয়েছে · ৩য় আয়াতের দুই শব্দ আলাদা "
                    "হয়েছে · না দেখে বলেছে · অর্থ বলেছে · বাড়ির কাজ দেওয়া হয়েছে।",
            "seconds": 65,
            "slide": {"kind": "end", "heading": "JazakAllahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "See you next time, in shaa Allah. 👋"},
        },
    ],
}


# ──────────────────── Easy Noorani Qaida · দারস ১ · ৫–৭ বছর ────────────────────
def S(*lines):
    """স্ক্রিপ্টের কয়েকটি লাইন জোড়া দেয় — খালি স্ট্রিং দিলে ফাঁকা লাইন।

    উস্তাদ পর্দায় লাইনগুলো আলাদা আলাদা দেখেন, তাই পড়তে সুবিধা হয়।
    """
    return "\n".join(lines)


QAIDA = {
    "title": "Easy Noorani Qaida — Lesson 1: The First Seven Letters",
    "title_ar": "الحروف المفردة",
    "lesson_no": 1,
    "kind": "qaida",
    "age_from": 5,
    "age_to": 7,
    # ⚠️ খাতায় লেখার পাঁচটি ধাপ যোগ হওয়ায় সময় বেড়েছে (২০ → ২৪)।
    # গায়ে লেখা সময় আর ধাপগুলোর যোগফল সবসময় মিলতে হবে — নইলে উস্তাদ
    # রুটিন সাজাতে গিয়ে ঠকে যান। একটি পরীক্ষা সেটা পাহারা দেয়।
    "duration_min": 24,
    "objectives": (
        "<p><b>Noorani Qaida — Lesson 1 · Teacher Script</b><br>"
        "Age 5–7 · about 24 minutes · The first seven letters<br>"
        "Listen → Watch the mouth → Say → Compare → Write → Play</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause, what to show, and which letter to name.</li>"
        "<li>Where you see <b>…………</b>, say the name of the letter shown "
        "on the screen. Arabic is never written in English letters.</li>"
        "</ul>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Know the letters <b>ا ب ت ث ج ح خ</b> on sight, in any order</li>"
        "<li>Say each letter with the right sound</li>"
        "<li>Tell <b>ت</b> from <b>ث</b>, and <b>ح</b> from <b>خ</b></li>"
        "<li>Write all seven in their own notebook, right to left, "
        "and show the page to the teacher</li>"
        "<li>Read all seven letters in order without help</li>"
        "</ul>"
        "<p><b>Mastery</b> — the child names all seven letters when you point "
        "at them in any order, not only down the list, and keeps ت/ث and ح/خ "
        "apart. Saying the list from memory is <i>not</i> mastery.</p>"
        "<p><b>Revision plan</b> — same day: the point-and-say game once more. "
        "Next class: all seven before the new letters. Then once a week.</p>"
    ),
    "steps": [
        {
            "section": "Welcome",
            "says": S(
                "Assalamu alaikum! How are you today?",
                "I'm so happy to see you!",
                "[অপেক্ষা করুন — শিশু সালামের জবাব দেবে]",
                "",
                "Are you ready to learn? Let's go!",
            ),
            "does": "হাসুন, হাত নাড়ুন। নাম ধরে একবার ডাকুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "That's okay! Listen.",
                "Assalamu alaikum.",
                "Now you say it back to me.",
                "[অপেক্ষা করুন]",
                "",
                "Lovely!",
            ),
            "note": "উষ্ণ শুরু। এখনই পড়ানো নয়।",
            "seconds": 45,
            "slide": {"kind": "title", "heading": "Noorani Qaida — Lesson 1",
                      "arabic": "الحروف المفردة",
                      "text": "Assalamu alaikum!"},
        },
        {
            "section": "Introduction",
            "says": S(
                "The Qur'an is made of letters.",
                "Today we'll learn seven letters.",
                "Seven! Show me seven fingers.",
                "[অপেক্ষা করুন — শিশু আঙুল দেখাবে]",
                "",
                "Let's count them together.",
                "One, two, three, four, five, six, seven!",
            ),
            "does": "সাতটি আঙুল তুলে একসাথে গুনুন।",
            "student": "সাতটি আঙুল দেখায়, সাথে গোনে।",
            "expected": "সাতটি আঙুল উপরে।",
            "correction": S(
                "Let's count together.",
                "One, two, three, four, five, six, seven.",
                "Well done!",
            ),
            "note": "এই বয়সে এক দারসে সাতটিই যথেষ্ট। শিশু দ্রুত পারলেও আর "
                    "বাড়াবেন না — পরের দারসে বাকিগুলো আছে।",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Our First Seven Letters",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "The Qur'an is made of letters."},
        },
        {
            "section": "Ta'awwudh",
            "says": S(
                "We always start with Bismillah.",
                "Listen to me first.",
                DOTS,
                "[পর্দার আরবিটি ধীরে ও স্পষ্ট করে পড়ুন]",
                "",
                "Now say it with me!",
                DOTS,
                "[একসাথে পড়ুন]",
                "",
                "Beautiful!",
            ),
            "does": "প্রথমে একা, তারপর একসাথে।",
            "student": "সাথে বলে।",
            "expected": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            "correction": S(
                "Good try! Just the small bit first.",
                "[শুধু প্রথম শব্দটি পড়ুন]",
                "",
                "Again — with me.",
                DOTS,
                "[আবার পুরোটা একসাথে]",
                "",
                "MashaAllah!",
            ),
            "note": "এখানে উচ্চারণ শোধরাবেন না — অভ্যাসটাই আজ বড়।",
            "seconds": 40,
            "slide": {"kind": "repeat", "heading": "Say With Me",
                      "arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                      "text": "🤲 We always start with this."},
        },
        {
            "section": "ا — Listen",
            "says": S(
                "Look at the screen.",
                "This is our first letter.",
                "Its name is …………",
                "[ا হরফটি দেখিয়ে তার নাম বলুন]",
                "",
                "Listen to me. Say nothing yet.",
                DOTS,
                "[আবার নাম বলুন — ধীরে, স্পষ্ট]",
            ),
            "does": "পর্দার হরফটি দেখিয়ে দুবার স্পষ্ট করে বলুন।",
            "student": "হরফটির দিকে তাকায়, শোনে।",
            "expected": "ا — হরফের দিকে চোখ।",
            "correction": S(
                "Look here — at this letter on the screen.",
                "Now listen again.",
                DOTS,
                "[আবার নাম বলুন]",
                "",
                "Did you hear it?",
            ),
            "note": "মাখরাজ: গলার গভীর থেকে — খোলা, ফাঁকা শব্দ।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ا", "text": "👂"},
        },
        {
            "section": "ا — Repeat",
            "says": S(
                "Now your turn!",
                "Open your mouth big, like me.",
                DOTS,
                "[হরফের নাম বলুন — শিশু সাথে বলবে]",
                "",
                "Again!",
                DOTS,
                "One more time!",
                DOTS,
                "[প্রতিবার একসাথে বলুন]",
                "",
                "Now all by yourself!",
                "[অপেক্ষা করুন — শিশু একা বলবে]",
                "",
                "MashaAllah! ⭐",
            ),
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "ا — খোলা, পরিষ্কার শব্দ।",
            "correction": S(
                "Nearly! Open your mouth big, like me.",
                "Watch.",
                DOTS,
                "[মুখ বড় করে খুলে নাম বলুন, তারপর থামুন]",
                "",
                "Then stop. Now you.",
                "[অপেক্ষা করুন]",
                "",
                "Lovely!",
            ),
            "note": "শেষে গুনগুন এলে বলুন মুখ খুলে থামতে।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ا", "text": "🎤"},
        },
        {
            "section": "ب — Listen",
            "says": S(
                "Next letter. Look at the screen.",
                "Watch my lips. They close together — like this.",
                DOTS,
                "[ب হরফটি দেখিয়ে তার নাম বলুন, ঠোঁট স্পষ্ট দেখান]",
                "",
                "Again — watch my lips.",
                DOTS,
                "[আবার বলুন]",
            ),
            "does": "ঠোঁট দেখিয়ে দুবার বলুন, ক্যামেরার কাছে মুখ আনুন।",
            "student": "ঠোঁটের দিকে তাকায়, শোনে।",
            "expected": "ب — ঠোঁটের দিকে চোখ।",
            "correction": S(
                "Look at my lips. Closed! Now open.",
                DOTS,
                "[ঠোঁট বন্ধ করে খুলে নাম বলুন]",
                "",
                "Watch again.",
            ),
            "note": "মাখরাজ: দুই ঠোঁট। শুধু বলবেন না — করে দেখান, এই দারসটা "
                    "নকল করেই শেখা হয়।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ب",
                      "text": "👄 Watch the lips."},
        },
        {
            "section": "ب — Repeat",
            "says": S(
                "Your turn! Close your lips.",
                "Now say it with me.",
                DOTS,
                "Again!",
                DOTS,
                "One more time!",
                DOTS,
                "[তিনবার একসাথে বলুন]",
                "",
                "Now all by yourself!",
                "[অপেক্ষা করুন]",
                "",
                "Excellent! ⭐",
            ),
            "does": "তিনবার একসাথে, তারপর একা। ঠোঁট সত্যিই বন্ধ হচ্ছে কিনা দেখুন।",
            "student": "হরফটি বলে।",
            "expected": "ب — ঠোঁট পুরোপুরি মিলছে।",
            "correction": S(
                "Almost! Your lips must touch.",
                "Press them together, like this.",
                "Now pop them open.",
                DOTS,
                "[ঠোঁট চেপে ধরে ছেড়ে দিয়ে নাম বলুন]",
                "",
                "Try again with me.",
                DOTS,
                "MashaAllah!",
            ),
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ب", "text": "🎤"},
        },
        {
            "section": "ت — Listen",
            "says": S(
                "Next letter. Look at the screen.",
                "Watch my tongue.",
                "It goes up and touches my top teeth.",
                "It stays inside my mouth.",
                DOTS,
                "[ت হরফটি দেখিয়ে তার নাম বলুন, জিভ ভেতরে রাখুন]",
                "",
                "Again — watch carefully.",
                DOTS,
            ),
            "does": "ধীরে জিভের অবস্থান দেখান।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "ت — মুখের দিকে মনোযোগ।",
            "correction": S(
                "Watch my tongue. Up! And inside.",
                "Listen again.",
                DOTS,
                "[আবার বলুন — জিভ ভেতরেই]",
            ),
            "note": "মাখরাজ: জিভের ডগা উপরের দাঁতের পেছনের মাড়িতে — জিভ "
                    "মুখের ভেতরেই থাকে।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ت",
                      "text": "👅 Tongue up, inside."},
        },
        {
            "section": "ت — Repeat",
            "says": S(
                "Your turn! Tongue up.",
                "Keep it inside your mouth.",
                "Say it with me.",
                DOTS,
                "Again!",
                DOTS,
                "One more time!",
                DOTS,
                "[তিনবার একসাথে বলুন]",
                "",
                "Now all by yourself!",
                "[অপেক্ষা করুন]",
                "",
                "Very good! ⭐",
            ),
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "ت — পরিষ্কার, জিভ মুখের ভেতরে।",
            "correction": S(
                "Oh, your tongue came out!",
                "That one is a different letter.",
                "For this letter, keep your tongue inside.",
                "Watch me.",
                DOTS,
                "[জিভ ভেতরে রেখে নাম বলুন]",
                "",
                "Now you.",
                "[অপেক্ষা করুন]",
                "",
                "That's it!",
            ),
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ت", "text": "🎤"},
        },
        {
            "section": "ث — Listen",
            "says": S(
                "Now a new one. Look at the screen.",
                "This time my tongue comes out a little.",
                "Look — you can see it!",
                DOTS,
                "[ث হরফটি দেখিয়ে তার নাম বলুন, জিভের ডগা দাঁতের ফাঁকে]",
                "",
                "Again — can you see my tongue?",
                DOTS,
            ),
            "does": "দাঁতের ফাঁকে জিভ স্পষ্ট করে দেখান।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "ث — মুখের দিকে মনোযোগ।",
            "correction": S(
                "Look — my tongue is out.",
                "Can you see it?",
                "Listen again.",
                DOTS,
                "[আবার বলুন — জিভ বাইরে]",
            ),
            "note": "মাখরাজ: জিভের ডগা উপরের ও নিচের সামনের দাঁতের মাঝে।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ث",
                      "text": "👅 Tongue comes out."},
        },
        {
            "section": "ث — Repeat",
            "says": S(
                "Your turn!",
                "Let your tongue come out a little.",
                "Now blow softly. Say it with me.",
                DOTS,
                "Again!",
                DOTS,
                "One more time!",
                DOTS,
                "[তিনবার একসাথে বলুন]",
                "",
                "Now all by yourself!",
                "[অপেক্ষা করুন]",
                "",
                "MashaAllah! ⭐",
            ),
            "does": "তিনবার একসাথে, তারপর একা। জিভ বেরোচ্ছে কিনা দেখুন।",
            "student": "হরফটি বলে।",
            "expected": "ث — জিভের ডগা দেখা যাচ্ছে।",
            "correction": S(
                "Nearly! Your tongue is still inside.",
                "Let it come out — like this.",
                "Now blow softly.",
                DOTS,
                "[জিভ বের করে নাম বলুন]",
                "",
                "Try again with me.",
                DOTS,
                "MashaAllah!",
            ),
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ث", "text": "🎤"},
        },
        {
            "section": "Compare ت / ث",
            "says": S(
                "Listen very carefully. Two letters.",
                DOTS,
                "[ت হরফটি দেখিয়ে তার নাম বলুন]",
                "",
                DOTS,
                "[ث হরফটি দেখিয়ে তার নাম বলুন]",
                "",
                "One hides the tongue inside.",
                "One lets the tongue peek out.",
                "Now look at the screen.",
                "I'm pointing at this one. Which one is it?",
                "[একটিতে আঙুল রেখে অপেক্ষা করুন]",
                "",
                "MashaAllah! 🌟",
            ),
            "does": "দুটো পরপর বলুন, তারপর একটিতে আঙুল রেখে জিজ্ঞেস করুন।",
            "student": "হরফের নাম বলে।",
            "expected": "যেটিতে আঙুল রেখেছেন, তার নাম।",
            "correction": S(
                "Look again.",
                "Is the tongue hiding, or coming out?",
                "Watch my mouth.",
                DOTS,
                "[ت বলুন — জিভ ভেতরে]",
                "",
                DOTS,
                "[ث বলুন — জিভ বাইরে]",
                "",
                "Now you tell me. Which one?",
                "[অপেক্ষা করুন]",
                "",
                "Well done!",
            ),
            "note": "এই জোড়াটাই এই দারসের সবচেয়ে বড় গোলমাল। এখানে সময় দিন — "
                    "আজ ঠিক না হলে পরে গোটা শব্দেও ভুল হতে থাকবে।",
            "seconds": 70,
            "slide": {"kind": "question", "heading": "Which One?",
                      "arabic": "ت      ث",
                      "text": "❓ One hides. One comes out."},
        },
        {
            "section": "ج — Listen",
            "says": S(
                "Next letter. Look at the screen.",
                "The middle of my tongue pushes up.",
                DOTS,
                "[ج হরফটি দেখিয়ে তার নাম বলুন]",
                "",
                "Again — listen to the strong sound.",
                DOTS,
            ),
            "does": "স্পষ্ট করে দুবার বলুন।",
            "student": "শোনে।",
            "expected": "ج — হরফের দিকে মনোযোগ।",
            "correction": S(
                "Watch my mouth.",
                "My tongue goes up in the middle.",
                "Listen once more.",
                DOTS,
                "[আবার বলুন]",
                "",
                "Did you hear it?",
            ),
            "note": "মাখরাজ: জিভের মাঝখান তালুর শক্ত অংশে।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ج", "text": "👂"},
        },
        {
            "section": "ج — Repeat",
            "says": S(
                "Your turn! Push your tongue up.",
                "Now say it with me.",
                DOTS,
                "Again!",
                DOTS,
                "One more time!",
                DOTS,
                "[তিনবার একসাথে বলুন]",
                "",
                "Now all by yourself!",
                "[অপেক্ষা করুন]",
                "",
                "Excellent! ⭐",
            ),
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "ج — ভরাট, নরম 'ঝ'-এর মতো নয়।",
            "correction": S(
                "Almost! Make it a big strong sound.",
                "Push your tongue up hard. Now let it go.",
                DOTS,
                "[জোর দিয়ে নাম বলুন]",
                "",
                "Try again with me.",
                DOTS,
                "That's much better!",
            ),
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ج", "text": "🎤"},
        },
        {
            "section": "ح — Listen",
            "says": S(
                "Next letter. Look at the screen.",
                "This one comes from here — my throat.",
                "Put your hand on your throat, like me.",
                "[অপেক্ষা করুন — শিশু গলায় হাত রাখবে]",
                "",
                "It's like warm breath on your hand.",
                DOTS,
                "[ح হরফটি দেখিয়ে তার নাম বলুন]",
                "",
                "Again — feel the warm air.",
                DOTS,
            ),
            "does": "গলায় হাত রাখুন, শিশুও যেন একই কাজ করে।",
            "student": "শোনে, গলায় হাত রাখে।",
            "expected": "ح — গলার দিকে মনোযোগ।",
            "correction": S(
                "Put your hand here, on your throat.",
                "Feel it? Listen again.",
                DOTS,
                "[আবার বলুন]",
            ),
            "note": "মাখরাজ: গলার মাঝখান। মসৃণ ও উষ্ণ — খসখসে নয়।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ح",
                      "text": "🌬️ Warm breath."},
        },
        {
            "section": "ح — Repeat",
            "says": S(
                "Your turn! Warm breath from your throat.",
                "Say it with me.",
                DOTS,
                "Again!",
                DOTS,
                "One more time!",
                DOTS,
                "[তিনবার একসাথে বলুন]",
                "",
                "Now all by yourself!",
                "[অপেক্ষা করুন]",
                "",
                "MashaAllah! ⭐",
            ),
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "ح — মসৃণ, গলার মাঝ থেকে।",
            "correction": S(
                "Nearly! That was a small breath.",
                "Make it warmer and stronger.",
                "Blow on your hand — like this.",
                DOTS,
                "[হাতে গরম নিঃশ্বাস দিয়ে নাম বলুন]",
                "",
                "Now you.",
                "[অপেক্ষা করুন]",
                "",
                "MashaAllah!",
            ),
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ح", "text": "🎤"},
        },
        {
            "section": "خ — Listen",
            "says": S(
                "Our last letter today! Look at the screen.",
                "This one is a bit scratchy.",
                "Listen.",
                DOTS,
                "[خ হরফটি দেখিয়ে তার নাম বলুন]",
                "",
                "Again — hear the scratchy sound.",
                DOTS,
            ),
            "does": "একটু বাড়িয়ে বলুন যাতে ح-এর সাথে পার্থক্য স্পষ্ট হয়।",
            "student": "শোনে।",
            "expected": "خ — হরফের দিকে মনোযোগ।",
            "correction": S(
                "Listen again.",
                "It's scratchy — like this.",
                DOTS,
                "[আবার বলুন — খসখসে ভাব স্পষ্ট করুন]",
            ),
            "note": "মাখরাজ: গলার উপরের অংশ, হালকা খসখসে ভাব।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "خ",
                      "text": "👂 A bit scratchy."},
        },
        {
            "section": "خ — Repeat",
            "says": S(
                "Your turn! Make it scratchy.",
                "Say it with me.",
                DOTS,
                "Again!",
                DOTS,
                "One more time!",
                DOTS,
                "[তিনবার একসাথে বলুন]",
                "",
                "Now all by yourself!",
                "[অপেক্ষা করুন]",
                "",
                "Well done! ⭐",
            ),
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "خ — গলার উপর থেকে।",
            "correction": S(
                "Let's try a game.",
                "Pretend the window is cold.",
                "Now blow on it — haaa.",
                "[অপেক্ষা করুন — শিশু ফুঁ দেবে]",
                "",
                "Good! Now make it scratchy at the back.",
                DOTS,
                "[খসখসে করে নাম বলুন]",
                "",
                "You did it!",
            ),
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "خ", "text": "🎤"},
        },
        {
            "section": "Compare ح / خ",
            "says": S(
                "Listen very carefully. Two letters.",
                DOTS,
                "[ح হরফটির নাম বলুন — নরম ও উষ্ণ]",
                "",
                DOTS,
                "[خ হরফটির নাম বলুন — খসখসে]",
                "",
                "One is soft. One is scratchy.",
                "Now say them after me.",
                DOTS,
                DOTS,
                "[দুটো পরপর বলুন, শিশু সাথে বলবে]",
                "",
                "Again!",
                DOTS,
                DOTS,
                "",
                "Now you say both, all by yourself.",
                "[অপেক্ষা করুন]",
                "",
                "MashaAllah! 🌟",
            ),
            "does": "জোড়াটি তিনবার বলুন, তারপর শিশুকে একা বলতে দিন।",
            "student": "দুটি হরফই বলে।",
            "expected": "ح ও خ — দুটি স্পষ্টভাবে আলাদা শব্দ।",
            "correction": S(
                "They sounded the same! Let's do just one.",
                DOTS,
                "[ح বলুন — নরম ও উষ্ণ]",
                "",
                "Say it.",
                "[অপেক্ষা করুন]",
                "",
                "Lovely! Now the scratchy one.",
                DOTS,
                "[خ বলুন]",
                "",
                "Now both together.",
                DOTS,
                DOTS,
                "MashaAllah!",
            ),
            "note": "এই দারসের দ্বিতীয় বড় গোলমাল। দুটো এক শোনালে ح-তে ফিরে "
                    "গিয়ে সেটা আগে ঠিক করুন।",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Soft or Scratchy?",
                      "arabic": "ح      خ",
                      "text": "❓ One is soft. One is scratchy."},
        },
        {
            "section": "Practice",
            "says": S(
                "Now all seven letters together. From the start!",
                "I'll point, and we say them together. Ready?",
                DOTS,
                "[পর্দার সাতটি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "Beautiful! One more time.",
                DOTS,
                "[আবার শুরু থেকে, শান্তভাবে]",
                "",
                "MashaAllah! 🌟",
            ),
            "does": "প্রতিটি হরফে আঙুল রাখুন, একসাথে বলুন। দুবার, শান্তভাবে।",
            "student": "সাথে পড়ে।",
            "expected": "ا ب ت ث ج ح خ — সাতটি হরফ ঠিক ক্রমে।",
            "correction": S(
                "Let's go a bit slower. From the start.",
                DOTS,
                "[প্রথম দুটি হরফের নাম ধীরে বলুন]",
                "",
                "Good, carry on!",
            ),
            "note": "একটি ভুলে থামবেন না — বরং গতি কমান।",
            "seconds": 70,
            "slide": {"kind": "letters", "heading": "All Together",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "🎤 From the start."},
        },
        # ───────── ✏️ খাতায় লেখা ─────────
        # কায়দায় শুধু পড়া নয়, লেখাও শেখা হয়। বাচ্চা নিজের খাতায় পেনসিল
        # দিয়ে লেখে, তারপর ক্যামেরায় উস্তাদকে দেখায়। জুমে এটাই একমাত্র
        # উপায় যাতে উস্তাদ হাতের লেখা দেখতে পান।
        #
        # ⚠️ পাঁচ বছরের শিশুর হাত এখনো শক্ত হয়নি — সুন্দর হওয়ার চেয়ে
        # চেষ্টা করাটাই বড়। তাই কোথাও "ঠিক হয়নি" বলা হয় না।
        {
            "section": "Writing — get ready",
            "says": S(
                "Now we write! Get your notebook.",
                "And your pencil.",
                "[অপেক্ষা করুন — খাতা ও পেনসিল আনতে সময় দিন]",
                "",
                "Ready? Show me your pencil!",
                "[শিশু পেনসিল দেখালে হাসুন]",
                "",
                "MashaAllah! Now sit up straight.",
            ),
            "does": "তাড়া দেবেন না — খাতা-পেনসিল আনতে সময় দিন। নিজেও একটি "
                    "পেনসিল হাতে নিন, শিশু দেখে উৎসাহ পায়। বসার ভঙ্গি "
                    "ঠিক আছে কিনা দেখুন।",
            "student": "খাতা ও পেনসিল আনে, দেখায়।",
            "expected": "খাতা খোলা, পেনসিল হাতে।",
            "correction": S(
                "No notebook? Any paper is fine.",
                "Even one page. Go and get it.",
                "[অপেক্ষা করুন]",
                "",
                "Good! Now we can start.",
            ),
            "note": "খাতা না থাকলে যেকোনো কাগজেই চলবে — শিশু যেন বাদ না পড়ে। "
                    "অভিভাবককে পরে বলে দিন একটি খাতা রাখতে।",
            "seconds": 45,
            "slide": {"kind": "write", "heading": "Notebook Time",
                      "text": "✏️ Pencil ready?"},
        },
        {
            "section": "Writing — watch me",
            "says": S(
                "Watch my finger. I write in the air.",
                DOTS,
                "[বাতাসে হরফটি বড় করে আঁকুন — ডান থেকে বাঁয়ে]",
                "",
                "See? We start from the right.",
                "Now you do it in the air with me.",
                "[একসাথে বাতাসে আঁকুন]",
                "",
                "Lovely!",
            ),
            "does": "⚠️ আরবি ডান থেকে বাঁয়ে লেখা হয় — এটি প্রথম দিনেই "
                    "শেখানো জরুরি, নইলে অভ্যাস উল্টো হয়ে যায়। বাতাসে বড় "
                    "করে আঁকুন যাতে ক্যামেরায় দেখা যায়। ধীরে।",
            "student": "বাতাসে হরফটি আঁকে।",
            "expected": "ডান থেকে বাঁয়ে আঙুল চালায়।",
            "correction": S(
                "Start over here — on this side.",
                "[ডান দিকটা দেখিয়ে দিন]",
                "",
                "That way. Try again with me.",
                DOTS,
            ),
            "note": "হাত ধরে দেখানো যায় না বলে বাতাসে আঁকা-ই সবচেয়ে কাজের। "
                    "শিশু ভুল দিকে গেলে বকবেন না, শুধু আবার দেখান।",
            "seconds": 55,
            "slide": {"kind": "write", "heading": "Right to Left",
                      "arabic": "ا",
                      "text": "✏️ Watch, then write in the air."},
        },
        {
            "section": "Writing — ا ب ت ث",
            "says": S(
                "Now write in your notebook.",
                "Four letters. One line each.",
                DOTS,
                "[পর্দার চারটি হরফ একে একে নাম বলুন]",
                "",
                "Take your time. I'm waiting.",
                "[অপেক্ষা করুন — তাড়া দেবেন না]",
                "",
                "Done? Hold your notebook up to the camera!",
            ),
            "does": "লেখার সময় চুপ থাকুন — শিশুকে মন দিতে দিন। ৪০-৫০ সেকেন্ড "
                    "সময় দিন। তারপর খাতা ক্যামেরায় দেখাতে বলুন, আর যা "
                    "ভালো হয়েছে তার নাম ধরে প্রশংসা করুন।",
            "student": "চারটি হরফ খাতায় লেখে, তারপর ক্যামেরায় দেখায়।",
            "expected": "খাতায় ا ب ت ث — যতটা পারে।",
            "correction": S(
                "That's a good try!",
                "Look at mine, then try one more.",
                "[পর্দার হরফটি দেখান]",
                "",
                "Better! Keep going.",
            ),
            "note": "⚠️ হাতের লেখা এখন সুন্দর হবে না — হবেও না। এই বয়সে "
                    "লক্ষ্য কেবল আকৃতিটা চেনা ও পেনসিল ধরা। বিন্দু (নুকতা) "
                    "কয়টা তা মিলিয়ে দিন — ب এক, ت দুই, ث তিন।",
            "seconds": 90,
            "slide": {"kind": "write", "heading": "Write These Four",
                      "arabic": "ا  ب  ت  ث",
                      "text": "✏️ One line each."},
        },
        {
            "section": "Writing — ج ح خ",
            "says": S(
                "Three more. Same way.",
                DOTS,
                "[পর্দার তিনটি হরফ একে একে নাম বলুন]",
                "",
                "Look — these three are brothers.",
                "Same shape. Only the dot moves.",
                "Write them now.",
                "[অপেক্ষা করুন]",
                "",
                "Show me!",
            ),
            "does": "তিনটি হরফের মিলটা দেখিয়ে দিন — একই আকৃতি, শুধু বিন্দু "
                    "আলাদা: ج-এর ভেতরে, ح-এর কোথাও নেই, خ-এর উপরে। এতে "
                    "মনে রাখা সহজ হয়।",
            "student": "তিনটি হরফ লেখে, দেখায়।",
            "expected": "খাতায় ج ح خ — বিন্দু আলাদা আলাদা।",
            "correction": S(
                "Almost! Where does the dot go?",
                "[পর্দায় বিন্দুটি দেখিয়ে দিন]",
                "",
                "Yes! Try that one again.",
            ),
            "note": "বিন্দুর জায়গাই এখানে আসল শিক্ষা — আকৃতি এক, বিন্দুতেই "
                    "পার্থক্য। এটি ধরতে পারলে পরের দারস অনেক সহজ হবে।",
            "seconds": 85,
            "slide": {"kind": "write", "heading": "The Three Brothers",
                      "arabic": "ج  ح  خ",
                      "text": "✏️ Same shape — the dot moves."},
        },
        {
            "section": "Writing — show the teacher",
            "says": S(
                "Now hold up your whole page.",
                "Let me see all seven!",
                "[খাতাটি ক্যামেরার সামনে ধরতে বলুন, একটু অপেক্ষা করুন]",
                "",
                "MashaAllah! Look at that! 🌟",
                "You wrote Arabic today.",
                "Your very first time!",
            ),
            "does": "⚠️ এই ধাপটি বাদ দেবেন না — নিজের লেখা উস্তাদকে দেখানোর "
                    "আনন্দেই শিশু পরের দিন আবার লিখতে চায়। খাতার দিকে "
                    "সত্যিই তাকান, আর অন্তত একটি হরফের নাম ধরে প্রশংসা করুন। "
                    "অভিভাবক পাশে থাকলে তাঁকেও দেখান।",
            "student": "পুরো পাতা ক্যামেরায় দেখায়।",
            "expected": "সাতটি হরফ লেখা একটি পাতা।",
            "correction": S(
                "Even two letters is wonderful.",
                "You started today. That's the big thing.",
                "Next time we write more.",
            ),
            "note": "কম লিখলেও প্রশংসা করুন। প্রথম দিনে দুটি হরফও যথেষ্ট — "
                    "উদ্দেশ্য পেনসিল ধরা শুরু করা, পাতা ভরানো নয়।",
            "seconds": 50,
            "slide": {"kind": "write", "heading": "Show Me Your Page",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "📓 Hold it up to the camera!"},
        },
        {
            "section": "Activity",
            "says": S(
                "Game time!",
                "I'll point at a letter. You say its name.",
                "As fast as you can! Ready? Go!",
                "[এলোমেলো ক্রমে ছয়-সাতবার আঙুল রাখুন — প্রতিবার অপেক্ষা করুন]",
                "",
                "Faster! 🌟",
                "[গতি বাড়ান]",
                "",
                "MashaAllah! You know them all!",
            ),
            "does": "এলোমেলো ক্রমে ছয়-সাতবার আঙুল রাখুন, ধীরে ধীরে গতি বাড়ান।",
            "student": "প্রতিটি হরফের নাম বলে।",
            "expected": "সঠিক নাম, প্রতি দফায় আরও দ্রুত।",
            "correction": S(
                "Ooh, nearly! This one is …………",
                "[যে হরফে আঙুল, তার নাম বলুন]",
                "",
                "Say it with me.",
                DOTS,
                "[একসাথে বলুন]",
                "",
                "Good! Now watch, I'm pointing again…",
                "Which one?",
                "[অপেক্ষা করুন]",
            ),
            "note": "এলোমেলো ক্রমে জিজ্ঞেস করলেই বোঝা যায় সত্যিই চিনেছে "
                    "কিনা; সাজানো ক্রমে কেবল তালিকা মুখস্থ হয়েছে বোঝায়। "
                    "এই খেলাটাই আজকের আসল পরীক্ষা।",
            "seconds": 90,
            "slide": {"kind": "activity", "heading": "Point & Say",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "👉 Say the letter I point at!"},
        },
        {
            "section": "Assessment",
            "says": S(
                "Now all by yourself!",
                "I'll just listen. Take your time.",
                "Off you go!",
                "[চুপ থাকুন — শিশু সাতটি হরফ একা পড়বে]",
                "",
                "MashaAllah! 🌟",
            ),
            "does": "চুপ থাকুন। কোথায় থেমে যাচ্ছে মনে রাখুন।",
            "student": "সাতটি হরফ একা পড়ে।",
            "expected": "সাতটি একা, ت/ث আর ح/خ আলাদা — আজকের জন্য এটাই "
                        "মুখস্থ হওয়া।",
            "correction": S(
                "MashaAllah, that was lovely!",
                "One tiny thing. This letter —",
                DOTS,
                "[যে হরফে ভুল হয়েছে, তার নাম বলুন]",
                "",
                "Say it after me.",
                "[অপেক্ষা করুন]",
                "",
                "Now you know it!",
            ),
            "note": "পড়ার মাঝে থামাবেন না। শেষে কেবল একটি জিনিস বলুন।",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "🎤 I'm listening."},
        },
        {
            "section": "Homework",
            "says": S(
                "MashaAllah! You did it!",
                "I'm so proud of you.",
                "Now a little homework.",
                "Before I see you again,",
                "say these seven letters five times every day.",
                "And write them once a day in your notebook.",
                "Can you do that?",
                "[অপেক্ষা করুন]",
                "",
                "Lovely!",
            ),
            "does": "মন থেকে প্রশংসা করুন — আজ কোনটা ভালো হয়েছে নাম ধরে বলুন। "
                    "বাড়ির কাজটা ধীরে বলুন, অভিভাবক শুনলে যেন লিখে নিতে পারেন।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": S(
                "Just five times a day.",
                "It only takes one minute.",
                "You can do it!",
            ),
            "note": "অভিভাবকের জন্য — শুধু শুনুন আর হাসুন। দিনে এক মিনিটই "
                    "যথেষ্ট। কোনো হরফ ভুল হলে বাড়িতে ঠিক করতে যাবেন না, "
                    "উস্তাদের জন্য রেখে দিন। লেখার সময় শুধু খেয়াল রাখুন "
                    "যেন ডান দিক থেকে শুরু করে — বাকিটা ক্লাসে দেখা হবে।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Until Next Time",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "📖 Say them 5 times every day.\n"
                              "✏️ Write them once a day."},
        },
        {
            "section": "Closing",
            "says": S(
                "Well done today! You worked so hard.",
                "Baraka Allahu fik.",
                "Assalamu alaikum wa rahmatullah!",
            ),
            "does": "হাসুন। উষ্ণভাবে শেষ করুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "Assalamu alaikum!",
                "Say it back to me.",
                "[অপেক্ষা করুন]",
                "",
                "See you next time!",
            ),
            "note": "শেষ করার আগে মিলিয়ে নিন: প্রতিটি হরফ করে দেখানো হয়েছে · "
                    "শিশু মুখের দিকে তাকিয়েছে · প্রতিটি হরফ একা বলেছে · "
                    "ت/ث মেলানো হয়েছে · ح/خ মেলানো হয়েছে · খাতায় লিখেছে ও "
                    "ক্যামেরায় দেখিয়েছে · এলোমেলো ক্রমের খেলা হয়েছে · "
                    "বাড়ির কাজ দেওয়া হয়েছে।",
            "seconds": 25,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "See you next time, in shaa Allah. 👋"},
        },
    ],
}


# ═══════════════ কায়দা — দারস ২ ═══════════════
# ⚠️ ইচ্ছা করেই দারস ১-এর নকল নয়। আসল উস্তাদ প্রতিদিন একই কথায় ক্লাস
# শুরু করেন না — তাই শুরু, মাঝপথের জোড়া আর শেষ, তিনটাই আলাদা। শেখানো ও
# লেখানোর ছক এক, কিন্তু কথা, খেলা ও পর্দার সাজ আলাদা।
QAIDA2 = {
    "title": "Easy Noorani Qaida — Lesson 2: The Dot Detective",
    "title_ar": "الحروف المفردة ٢",
    "lesson_no": 2,
    "kind": "qaida",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 20,
    "objectives": (
        "<p><b>Noorani Qaida — Lesson 2 · Teacher Script</b><br>"
        "Age 5-7 · about 20 minutes · Six new letters<br>"
        "Remember &rarr; Listen &rarr; Say &rarr; Compare &rarr; Write</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause, what to show, and which letter to name.</li>"
        "<li>Where you see <b>…………</b>, say the name of the letter shown "
        "on the screen. Arabic is never written in English letters.</li>"
        "</ul>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Know <b>د ذ ر ز س ش</b> on sight, in any order</li>"
        "<li>Tell each pair apart — the dot is the only difference</li>"
        "<li>Write all six in their own notebook, right to left</li>"
        "</ul>"
    ),
    "steps": [
        {
            "section": "Welcome back",
            "says": S(
                "Assalamu alaikum! Come a bit closer to the screen.",
                "[অপেক্ষা করুন — শিশু কাছে আসবে]",
                "",
                "Good! Today we meet six new friends.",
                "But first, a little game.",
            ),
            "does": "আজ খেলা দিয়ে শুরু — গতকালের মতো একই কথায় নয়। হাসুন, "
                    "গলা একটু নরম রাখুন যাতে শিশু মন দেয়।",
            "student": "কাছে আসে, শোনে।",
            "expected": "Wa alaikumus salam!",
            "correction": S(
                "Say it back to me. Assalamu alaikum!",
                "[অপেক্ষা করুন]",
                "",
                "Lovely.",
            ),
            "note": "প্রতিটি ক্লাস আলাদাভাবে শুরু করলে শিশু আগ্রহ হারায় না।",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Assalamu Alaikum!",
                      "arabic": "الحروف المفردة ٢",
                      "text": "🎈 A game first!"},
        },
        {
            "section": "Game — our seven friends",
            "says": S(
                "Look at the screen. Our seven old friends!",
                "I'll point. You say the name. Fast!",
                DOTS,
                "[সাতটি হরফে এলোমেলো ক্রমে আঙুল রাখুন]",
                "",
                "MashaAllah! You remembered them all.",
            ),
            "does": "⚠️ ক্রম এলোমেলো করুন — সোজা ক্রমে দিলে মুখস্থ সুরে বলে "
                    "ফেলে, চেনা হয় না। দ্রুত করুন, খেলার মতো।",
            "student": "আঙুল যেখানে, সেই হরফের নাম বলে।",
            "expected": "ا ب ت ث ج ح خ — এলোমেলো ক্রমেও ঠিক।",
            "correction": S(
                "Take your time. Look at the shape.",
                DOTS,
                "[হরফটির নাম ধীরে বলুন]",
                "",
                "Yes! Now the next one.",
            ),
            "note": "ভুলে গেলে মনে করিয়ে এগিয়ে যান। আজকের লক্ষ্য নতুন ছয়টি, "
                    "পুরনোটা কেবল ঝালাই।",
            "seconds": 50,
            "slide": {"kind": "review", "heading": "Do You Remember?",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "👉 Say the one I point at!"},
        },
        {
            "section": "Today's six",
            "says": S(
                "Now look. Six new letters.",
                "Three pairs. Each pair looks almost the same.",
                "Only a tiny dot tells them apart.",
                "You'll be a dot detective today!",
            ),
            "does": "ছয়টি হরফ একসাথে দেখান। জোড়াগুলো আঙুল দিয়ে দেখিয়ে দিন — "
                    "د ذ, তারপর ر ز, তারপর س ش।",
            "student": "পর্দার দিকে তাকায়।",
            "expected": "আগ্রহ নিয়ে তাকায়।",
            "correction": S(
                "Look here, at the screen.",
                "Six letters. Can you count them?",
                "[অপেক্ষা করুন]",
            ),
            "note": "'বিন্দু গোয়েন্দা' কথাটাই আজকের সুতো — বারবার ফিরে আসবে।",
            "seconds": 35,
            "slide": {"kind": "title", "heading": "Six New Friends",
                      "arabic": "د  ذ  ر  ز  س  ش",
                      "text": "🔍 Find the dot!"},
        },
        {
            "section": "د — Listen",
            "says": S(
                "Ready for the next one? Watch closely.",
                "Watch my tongue. It taps, then stops.",
                DOTS,
                "[د হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট দেখান]",
                "",
                "Let me say it again.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন। দুবার বলুন — the tip of your tongue taps the roof। "
                    "শিশু যেন মুখের নড়াচড়া দেখতে পায়।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "د — মুখের দিকে চোখ।",
            "correction": S(
                "Look here. See how my mouth moves.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Good. Now listen again.",
            ),
            "note": "মাখরাজ: জিহ্বার ডগা উপরের মাড়িতে ছোঁয়, একবারই।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "د",
                      "text": "👅 Tongue taps up top."},
        },
        {
            "section": "د — Your turn",
            "says": S(
                "Your turn now. Let me hear it.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Once more, nice and clear.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Lovely! Just like that.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন — অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না। শুনে হাসুন।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "د — নিজে বলে, দুবার।",
            "correction": S(
                "Tap once. Just once — not twice.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! Try once more.",
            ),
            "note": "এই বয়সে নিখুঁত না হলেও চলে — চেষ্টা করাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "د",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "ذ — Listen",
            "says": S(
                "A new friend is coming. Look here.",
                "Now the tongue comes out to say hello.",
                DOTS,
                "[ذ হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট দেখান]",
                "",
                "Listen once more, a bit slower.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন। দুবার বলুন — the tongue peeks out, just a little। "
                    "শিশু যেন মুখের নড়াচড়া দেখতে পায়।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "ذ — মুখের দিকে চোখ।",
            "correction": S(
                "Eyes on my lips. Here it comes.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Good. Now listen again.",
            ),
            "note": "মাখরাজ: জিহ্বার ডগা দাঁতের ফাঁকে সামান্য বেরোয়।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ذ",
                      "text": "👅 Tongue peeks out."},
        },
        {
            "section": "ذ — Your turn",
            "says": S(
                "You try it. Roll it gently.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Again — a bit softer this time.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Beautiful rolling!",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন — অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না। শুনে হাসুন।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ذ — নিজে বলে, দুবার।",
            "correction": S(
                "Let your tongue peek out a tiny bit.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! Try once more.",
            ),
            "note": "এই বয়সে নিখুঁত না হলেও চলে — চেষ্টা করাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ذ",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "ر — Listen",
            "says": S(
                "This one is fun. Listen well.",
                "Listen — my tongue rolls a little. Soft.",
                DOTS,
                "[ر হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট দেখান]",
                "",
                "Again — catch it this time.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন। দুবার বলুন — the tongue rolls, soft and quick। "
                    "শিশু যেন মুখের নড়াচড়া দেখতে পায়।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "ر — মুখের দিকে চোখ।",
            "correction": S(
                "Watch again. Slowly this time.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Good. Now listen again.",
            ),
            "note": "মাখরাজ: জিহ্বার ডগা কেঁপে ওঠে — নরম, ছোট কম্পন।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ر",
                      "text": "🌀 A little roll."},
        },
        {
            "section": "ر — Your turn",
            "says": S(
                "Now buzz it yourself.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "One more buzz, a long one!",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! I heard the bee.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন — অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না। শুনে হাসুন।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ر — নিজে বলে, দুবার।",
            "correction": S(
                "Roll it gently. Not too hard.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! Try once more.",
            ),
            "note": "এই বয়সে নিখুঁত না হলেও চলে — চেষ্টা করাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ر",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "ز — Listen",
            "says": S(
                "Only two left. Eyes up!",
                "This one buzzes. Like a small bee.",
                DOTS,
                "[ز হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট দেখান]",
                "",
                "One more, then it's your turn.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন। দুবার বলুন — a buzz, like a tiny bee। "
                    "শিশু যেন মুখের নড়াচড়া দেখতে পায়।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "ز — মুখের দিকে চোখ।",
            "correction": S(
                "Look carefully. Just my mouth.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Good. Now listen again.",
            ),
            "note": "মাখরাজ: দাঁতের ফাঁক দিয়ে শিসের মতো — কম্পন নেই।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ز",
                      "text": "🐝 A little buzz."},
        },
        {
            "section": "ز — Your turn",
            "says": S(
                "Your turn. Long and smooth.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Again, keep the air soft.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Perfect hissing!",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন — অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না। শুনে হাসুন।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ز — নিজে বলে, দুবার।",
            "correction": S(
                "Make it buzz. Feel it in your teeth.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! Try once more.",
            ),
            "note": "এই বয়সে নিখুঁত না হলেও চলে — চেষ্টা করাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ز",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "س — Listen",
            "says": S(
                "The last one for today. Here it comes.",
                "Hear the hiss? Very soft air.",
                DOTS,
                "[س হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট দেখান]",
                "",
                "Last time. Listen well.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন। দুবার বলুন — a soft hiss, like air escaping। "
                    "শিশু যেন মুখের নড়াচড়া দেখতে পায়।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "س — মুখের দিকে চোখ।",
            "correction": S(
                "One more look. Ready?",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Good. Now listen again.",
            ),
            "note": "মাখরাজ: দাঁতের কাছে সরু ফাঁক, শিসের মতো শব্দ।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "س",
                      "text": "💨 A soft hiss."},
        },
        {
            "section": "س — Your turn",
            "says": S(
                "You say it. Wide and quiet.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Once more, like a big hush.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Excellent! So gentle.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন — অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না। শুনে হাসুন।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "س — নিজে বলে, দুবার।",
            "correction": S(
                "Keep it smooth. Long and soft.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! Try once more.",
            ),
            "note": "এই বয়সে নিখুঁত না হলেও চলে — চেষ্টা করাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "س",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "ش — Listen",
            "says": S(
                "Here comes a new one. Eyes on me.",
                "This one is wider. Like saying hush.",
                DOTS,
                "[ش হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট দেখান]",
                "",
                "One more time. Ready?",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন। দুবার বলুন — a wide hush, like asking for quiet। "
                    "শিশু যেন মুখের নড়াচড়া দেখতে পায়।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "ش — মুখের দিকে চোখ।",
            "correction": S(
                "Watch me once more. Look at my mouth.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Good. Now listen again.",
            ),
            "note": "মাখরাজ: জিহ্বা চ্যাপ্টা, বাতাস ছড়িয়ে পড়ে।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Listen",
                      "arabic": "ش",
                      "text": "🤫 A wide hush."},
        },
        {
            "section": "ش — Your turn",
            "says": S(
                "Now you. Say it after me.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Again, a little louder.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "That's it! Well done.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন — অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না। শুনে হাসুন।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ش — নিজে বলে, দুবার।",
            "correction": S(
                "Spread it wide. Feel the air spread.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! Try once more.",
            ),
            "note": "এই বয়সে নিখুঁত না হলেও চলে — চেষ্টা করাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ش",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "Detective — د or ذ",
            "says": S(
                "Dot detective time! Look carefully.",
                "One taps. One peeks out.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "Which one has the dot? Point to it!",
                "[অপেক্ষা করুন — শিশু আঙুল দেখাবে]",
                "",
                "Yes! You found it.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান। দুবার করে বলুন, তারপর শিশুকে "
                    "বিন্দুওয়ালাটি দেখাতে বলুন। د-এ কোনো বিন্দু নেই, ذ-এ উপরে একটি।",
            "student": "বিন্দুওয়ালা হরফটি দেখায়।",
            "expected": "সঠিক হরফটিতে আঙুল।",
            "correction": S(
                "Look at the top. Do you see a dot?",
                "[বিন্দুটি আঙুল দিয়ে দেখিয়ে দিন]",
                "",
                "There it is! Now which one is it?",
            ),
            "note": "د-এ কোনো বিন্দু নেই, ذ-এ উপরে একটি। আকৃতি এক, বিন্দুতেই পার্থক্য — এটাই আজকের মূল কথা।",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Which One?",
                      "arabic": "د      ذ",
                      "text": "🔍 One dot or none?"},
        },
        {
            "section": "Detective — ر or ز",
            "says": S(
                "Dot detective time! Look carefully.",
                "One rolls. One buzzes.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "Which one has the dot? Point to it!",
                "[অপেক্ষা করুন — শিশু আঙুল দেখাবে]",
                "",
                "Yes! You found it.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান। দুবার করে বলুন, তারপর শিশুকে "
                    "বিন্দুওয়ালাটি দেখাতে বলুন। ر-এ বিন্দু নেই, ز-এ উপরে একটি।",
            "student": "বিন্দুওয়ালা হরফটি দেখায়।",
            "expected": "সঠিক হরফটিতে আঙুল।",
            "correction": S(
                "Look at the top. Do you see a dot?",
                "[বিন্দুটি আঙুল দিয়ে দেখিয়ে দিন]",
                "",
                "There it is! Now which one is it?",
            ),
            "note": "ر-এ বিন্দু নেই, ز-এ উপরে একটি। আকৃতি এক, বিন্দুতেই পার্থক্য — এটাই আজকের মূল কথা।",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Which One?",
                      "arabic": "ر      ز",
                      "text": "🔍 Look on top!"},
        },
        {
            "section": "Detective — س or ش",
            "says": S(
                "Dot detective time! Look carefully.",
                "One hisses. One hushes.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "Which one has the dot? Point to it!",
                "[অপেক্ষা করুন — শিশু আঙুল দেখাবে]",
                "",
                "Yes! You found it.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান। দুবার করে বলুন, তারপর শিশুকে "
                    "বিন্দুওয়ালাটি দেখাতে বলুন। س-এ বিন্দু নেই, ش-এ উপরে তিনটি।",
            "student": "বিন্দুওয়ালা হরফটি দেখায়।",
            "expected": "সঠিক হরফটিতে আঙুল।",
            "correction": S(
                "Look at the top. Do you see a dot?",
                "[বিন্দুটি আঙুল দিয়ে দেখিয়ে দিন]",
                "",
                "There it is! Now which one is it?",
            ),
            "note": "س-এ বিন্দু নেই, ش-এ উপরে তিনটি। আকৃতি এক, বিন্দুতেই পার্থক্য — এটাই আজকের মূল কথা।",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Which One?",
                      "arabic": "س      ش",
                      "text": "🔍 Count the dots!"},
        },
        {
            "section": "All six together",
            "says": S(
                "All six now. From the top.",
                DOTS,
                "[ছয়টি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "Once more, and a bit quicker.",
                DOTS,
                "[আবার, একটু দ্রুত]",
                "",
                "MashaAllah! Beautiful.",
            ),
            "does": "প্রতিটি হরফে আঙুল রাখুন। দুবার — প্রথমে ধীরে, পরে একটু "
                    "দ্রুত। একটা ভুলে থামবেন না, বরং গতি কমান।",
            "student": "সাথে পড়ে।",
            "expected": "د ذ ر ز س ش — ছয়টি ঠিক ক্রমে।",
            "correction": S(
                "Slower. Let's start again from the first one.",
                DOTS,
                "[প্রথম দুটির নাম ধীরে বলুন]",
                "",
                "Good, keep going!",
            ),
            "note": "ভুল হলে ওই হরফে ফিরে যাবেন না — পুরোটা শেষ করে তারপর।",
            "seconds": 60,
            "slide": {"kind": "repeat", "heading": "All Six",
                      "arabic": "د  ذ  ر  ز  س  ش",
                      "text": "🎤 Together now."},
        },
        {
            "section": "Thirteen in a row",
            "says": S(
                "Now something big. Thirteen letters!",
                "Seven old friends, and six new ones.",
                "Let's do it together. Slowly.",
                DOTS,
                "[তেরোটি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "You did thirteen! I'm so proud.",
            ),
            "does": "⚠️ এটাই আজকের সবচেয়ে বড় কাজ — তাড়াহুড়ো নয়। থেমে থেমে "
                    "যান; শিশু ক্লান্ত হলে সাতটির পর একটু দম নিন।",
            "student": "তেরোটি হরফ সাথে পড়ে।",
            "expected": "ا থেকে ش পর্যন্ত তেরোটি।",
            "correction": S(
                "That's a lot! Let's take it in two halves.",
                DOTS,
                "[প্রথমে সাতটি, তারপর ছয়টি]",
                "",
                "See? Easier that way.",
            ),
            "note": "দুই ভাগে ভাগ করে নিলে ছোট শিশুর জন্য অনেক সহজ হয়।",
            "seconds": 70,
            "slide": {"kind": "review", "heading": "Thirteen Letters!",
                      "arabic": "ا ب ت ث ج ح خ\nد ذ ر ز س ش",
                      "text": "🌟 All together now."},
        },
        {
            "section": "Writing — get ready",
            "says": S(
                "Notebook time! You know what to do.",
                "[অপেক্ষা করুন — খাতা ও পেনসিল আনতে দিন]",
                "",
                "Show me your pencil!",
                "[শিশু পেনসিল দেখালে হাসুন]",
                "",
                "Perfect. Remember, we start from the right.",
            ),
            "does": "আজ আর বিস্তারিত বলতে হবে না, গতদিনেই শেখা হয়েছে। শুধু "
                    "ডান দিক থেকে শুরুর কথাটা মনে করিয়ে দিন।",
            "student": "খাতা ও পেনসিল আনে।",
            "expected": "খাতা খোলা, পেনসিল হাতে।",
            "correction": S(
                "No notebook? Any paper will do.",
                "Go and get it. I'll wait.",
                "[অপেক্ষা করুন]",
            ),
            "note": "খাতা না থাকলে যেকোনো কাগজেই চলবে — শিশু যেন বাদ না পড়ে।",
            "seconds": 40,
            "slide": {"kind": "write", "heading": "Notebook Time",
                      "arabic": "د  ذ  ر  ز  س  ش",
                      "text": "✏️ Right to left, remember!"},
        },
        {
            "section": "Writing — د ذ ر ز",
            "says": S(
                "Four letters first. One line each.",
                DOTS,
                "[পর্দার চারটি হরফ একে একে নাম বলুন]",
                "",
                "Two of them have a dot. Don't forget it!",
                "Take your time. I'm here.",
                "[অপেক্ষা করুন — ৪০-৫০ সেকেন্ড সময় দিন]",
                "",
                "Hold it up! Let me see.",
            ),
            "does": "লেখার সময় চুপ থাকুন। বিন্দুর কথাটা আগেই মনে করিয়ে দিন — "
                    "ذ ও ز-এ বিন্দু আছে, د ও ر-এ নেই।",
            "student": "চারটি হরফ লেখে, ক্যামেরায় দেখায়।",
            "expected": "খাতায় د ذ ر ز — বিন্দু ঠিক জায়গায়।",
            "correction": S(
                "Nice try! Where does the dot go?",
                "[পর্দায় বিন্দুটি দেখিয়ে দিন]",
                "",
                "On top. Try that one again.",
            ),
            "note": "⚠️ হাতের লেখা সুন্দর হবে না, হওয়ারও কথা নয়। বিন্দুর "
                    "জায়গাটাই দেখুন — ওটাই আজকের শিক্ষা।",
            "seconds": 85,
            "slide": {"kind": "write", "heading": "Write These Four",
                      "arabic": "د  ذ  ر  ز",
                      "text": "✏️ Watch the dots!"},
        },
        {
            "section": "Writing — س ش",
            "says": S(
                "Two more. These have little teeth!",
                DOTS,
                "[দুটি হরফের নাম বলুন]",
                "",
                "Count the teeth. Three little bumps.",
                "One has three dots on top. Which one?",
                "[অপেক্ষা করুন]",
                "",
                "Yes! Now write them both.",
            ),
            "does": "'দাঁত' কথাটা কাজে লাগে — س ও ش-এর তিনটি খাঁজকে দাঁত বলুন, "
                    "শিশু সহজে মনে রাখে। তারপর লিখতে দিন।",
            "student": "দুটি হরফ লেখে।",
            "expected": "খাতায় س ش — ش-এ তিনটি বিন্দু।",
            "correction": S(
                "Three dots, like a little hat.",
                "[পর্দায় তিনটি বিন্দু দেখান]",
                "",
                "That's better!",
            ),
            "note": "তিনটি খাঁজ ও তিনটি বিন্দু — সংখ্যাটা মিলিয়ে বললে মনে থাকে।",
            "seconds": 70,
            "slide": {"kind": "write", "heading": "Little Teeth",
                      "arabic": "س  ش",
                      "text": "✏️ Three bumps, three dots."},
        },
        {
            "section": "Writing — show the teacher",
            "says": S(
                "Whole page up, please! Let me see all six.",
                "[খাতাটি ক্যামেরার সামনে ধরতে বলুন]",
                "",
                "MashaAllah! Look at those dots.",
                "You really are a dot detective.",
            ),
            "does": "⚠️ এই ধাপটি বাদ দেবেন না। খাতার দিকে সত্যিই তাকান, আর "
                    "অন্তত একটি হরফের নাম ধরে প্রশংসা করুন।",
            "student": "পুরো পাতা ক্যামেরায় দেখায়।",
            "expected": "ছয়টি হরফ লেখা একটি পাতা।",
            "correction": S(
                "Even three letters is great work.",
                "You wrote today. That's what matters.",
                "Next time we'll do more.",
            ),
            "note": "কম লিখলেও প্রশংসা করুন — উদ্দেশ্য পেনসিল চালানো, পাতা "
                    "ভরানো নয়।",
            "seconds": 45,
            "slide": {"kind": "write", "heading": "Show Me Your Page",
                      "arabic": "د  ذ  ر  ز  س  ش",
                      "text": "📓 Hold it up!"},
        },
        {
            "section": "Homework",
            "says": S(
                "Small homework before I see you again.",
                "Say the thirteen letters once every day.",
                "And write today's six, one line each.",
                "Can you promise me that?",
                "[অপেক্ষা করুন]",
                "",
                "Shukran! I trust you.",
            ),
            "does": "বাড়ির কাজটা ধীরে বলুন, অভিভাবক শুনলে যেন লিখে নিতে "
                    "পারেন। 'প্রতিজ্ঞা' কথাটা শিশুকে দায়িত্ববোধ দেয়।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": S(
                "Just once a day. That's all.",
                "One minute, no more.",
                "You can do it!",
            ),
            "note": "অভিভাবকের জন্য — শুধু শুনুন আর হাসুন। ভুল হলে বাড়িতে "
                    "ঠিক করতে যাবেন না, উস্তাদের জন্য রেখে দিন।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Your Promise",
                      "arabic": "د  ذ  ر  ز  س  ش",
                      "text": "📖 Say them daily.\n✏️ One line each."},
        },
        {
            "section": "Closing",
            "says": S(
                "You worked so hard today, mashaAllah.",
                "Thirteen letters, and six new friends.",
                "Baraka Allahu fik. See you soon!",
                "Assalamu alaikum wa rahmatullah!",
            ),
            "does": "হাসুন, হাত নাড়ুন। উষ্ণভাবে শেষ করুন — শেষ মুহূর্তটাই "
                    "শিশু বাড়ি নিয়ে যায়।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "Assalamu alaikum! Say it back to me.",
                "[অপেক্ষা করুন]",
                "",
                "See you next time!",
            ),
            "note": "মিলিয়ে নিন: পুরনো সাতটি ঝালাই হয়েছে · ছয়টি নতুন হরফ শোনা "
                    "ও বলা হয়েছে · তিনটি জোড়া মেলানো হয়েছে · তেরোটি একসাথে "
                    "বলা হয়েছে · খাতায় লিখেছে ও ক্যামেরায় দেখিয়েছে।",
            "seconds": 30,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "👋 See you soon, in shaa Allah."},
        },
    ],
}


# ═══════════════ কায়দা — দারস ৩ ═══════════════
# ⚠️ আবারও নতুন চেহারা। দারস ১ শুরু হয়েছিল সালাম ও পরিচয় দিয়ে, দারস ২
# খেলা দিয়ে — এটি শুরু হয় ভূমিকা বদলে: শিশু নিজেই উস্তাদ সাজে। আজকের
# হরফগুলো "ভারী", তাই সুতোটাও আলাদা: হালকা বনাম ভারী।
QAIDA3 = {
    "title": "Easy Noorani Qaida — Lesson 3: Light and Heavy",
    "title_ar": "الحروف المفردة ٣",
    "lesson_no": 3,
    "kind": "qaida",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 23,
    "objectives": (
        "<p><b>Noorani Qaida — Lesson 3 · Teacher Script</b><br>"
        "Age 5-7 · about 24 minutes · Six heavy letters<br>"
        "You teach me &rarr; Listen &rarr; Say &rarr; Sort &rarr; Write</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause, what to show, and which letter to name.</li>"
        "<li>Where you see <b>…………</b>, say the name of the letter shown "
        "on the screen. Arabic is never written in English letters.</li>"
        "</ul>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Know <b>ص ض ط ظ ع غ</b> on sight, in any order</li>"
        "<li>Feel the difference between a light letter and a heavy one</li>"
        "<li>Write all six in their own notebook, right to left</li>"
        "<li>Say all nineteen letters learned so far</li>"
        "</ul>"
    ),
    "steps": [
        {
            "section": "You be the teacher",
            "says": S(
                "Assalamu alaikum! Today we swap places.",
                "You be the teacher first. I'll be the student.",
                "Teach me three letters. Any three you like!",
                "[অপেক্ষা করুন — শিশু হরফ বলবে, আপনি ছাত্রের মতো বলবেন]",
                "",
                "Shukran, teacher! You taught me well.",
            ),
            "does": "⚠️ সত্যিই ছাত্র সাজুন — শিশুর দিকে তাকিয়ে শুনুন, তার "
                    "পরে বলুন। ভূমিকা বদল শিশুকে হঠাৎ সজাগ করে তোলে, আর "
                    "কতটুকু মনে আছে তাও বোঝা যায়।",
            "student": "তিনটি হরফ শেখায়।",
            "expected": "যেকোনো তিনটি হরফ, নিজে থেকে।",
            "correction": S(
                "Any letter you remember. Just one to start.",
                "[অপেক্ষা করুন, তাড়া দেবেন না]",
                "",
                "There you go, teacher!",
            ),
            "note": "একটাও মনে না থাকলে পর্দায় পুরনো হরফ দেখিয়ে দিন — "
                    "লজ্জা দেওয়া চলবে না।",
            "seconds": 60,
            "slide": {"kind": "activity", "heading": "You Be The Teacher",
                      "arabic": "ا ب ت ث ج ح خ\nد ذ ر ز س ش",
                      "text": "🎓 Teach me three!"},
        },
        {
            "section": "Light and heavy",
            "says": S(
                "Now listen. Two letters, one after the other.",
                DOTS,
                "[একটি হালকা হরফ বলুন, যেমন س]",
                DOTS,
                "[একটি ভারী হরফ বলুন, যেমন ص]",
                "",
                "Did you hear? One is light. One is heavy.",
                "The heavy one fills your whole mouth.",
                "Today all six are heavy ones!",
            ),
            "does": "দুটি হরফ পরপর বলুন — পার্থক্যটা কানে ধরিয়ে দিন। হালকাটা "
                    "সরু করে, ভারীটা মুখ ভরে। এটাই আজকের মূল ধারণা।",
            "student": "শোনে, পার্থক্য ধরার চেষ্টা করে।",
            "expected": "মন দিয়ে শোনে।",
            "correction": S(
                "Listen once more. Light first.",
                DOTS,
                "[হালকাটি বলুন]",
                "",
                "Now heavy.",
                DOTS,
                "[ভারীটি বলুন]",
            ),
            "note": "তাফখীম-তারকীকের ভিত্তি এখানেই বসছে — নাম বলার দরকার "
                    "নেই, কানে ধরিয়ে দিলেই যথেষ্ট।",
            "seconds": 55,
            "slide": {"kind": "meaning", "heading": "Light or Heavy?",
                      "arabic": "س      ص",
                      "text": "🪶 Light  ·  🪨 Heavy"},
        },
        {
            "section": "Today's six",
            "says": S(
                "Here they are. Six heavy letters.",
                "Say them with a big, round mouth.",
                "Like you have a warm ball inside!",
                "Ready to meet them?",
            ),
            "does": "'মুখে গরম বল' — এই ছবিটা কাজে লাগে, শিশু সহজে মুখ ভরে "
                    "বলতে শেখে। নিজে করে দেখান।",
            "student": "পর্দার দিকে তাকায়।",
            "expected": "আগ্রহ নিয়ে তাকায়।",
            "correction": S(
                "Open wide, like this.",
                "[মুখ গোল করে দেখান]",
                "",
                "That's the shape!",
            ),
            "note": "মুখের আকৃতিটাই আজকের সবচেয়ে বড় শিক্ষা।",
            "seconds": 35,
            "slide": {"kind": "title", "heading": "Six Heavy Letters",
                      "arabic": "ص  ض  ط  ظ  ع  غ",
                      "text": "🪨 Big, round mouth!"},
        },
        {
            "section": "ص — Feel it",
            "says": S(
                "Next one. Keep your hand right there.",
                "This one hisses, but heavy and round.",
                DOTS,
                "[ص হরফটি দেখিয়ে তার নাম বলুন, ধীরে ও ভারীভাবে]",
                "",
                "Did you feel the shake? Again.",
                DOTS,
                "[আবার বলুন]",
            ),
            "does": "শিশুকে গলায় হাত রাখতে বলুন — ভারী হরফে কাঁপুনি টের পায়। "
                    "নিজেও হাত রেখে দেখান। the heavy sister of a soft hiss.",
            "student": "গলায় হাত রেখে শোনে।",
            "expected": "ص — গলায় হাত, মন দিয়ে শোনে।",
            "correction": S(
                "Try the hand again. Feel for the shake.",
                DOTS,
                "[ধীরে, ভারীভাবে বলুন]",
                "",
                "Did you feel it that time?",
            ),
            "note": "মাখরাজ: س-এর মতো জায়গা, কিন্তু মুখ ভরে — ভারী।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Feel It",
                      "arabic": "ص",
                      "text": "🪨 Heavy hiss."},
        },
        {
            "section": "ص — Say it big",
            "says": S(
                "Now you. Press that side.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Again — push a little harder.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Well done! I felt that.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। ভারী হরফে "
                    "শিশুর সময় লাগে — তাড়া দিলে হালকা করে বলে ফেলে।",
            "student": "হরফটি নিজে বলে, মুখ ভরে।",
            "expected": "ص — নিজে বলে, দুবার।",
            "correction": S(
                "Round your mouth more. Feel it fill up.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! One more go.",
            ),
            "note": "প্রথম দিনে নিখুঁত হবে না — ভারী ভাব আসাটাই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Say It Big",
                      "arabic": "ص",
                      "text": "🎤 Fill your mouth!"},
        },
        {
            "section": "ض — Feel it",
            "says": S(
                "Here comes another. Feel it this time.",
                "Press your tongue against the side teeth.",
                DOTS,
                "[ض হরফটি দেখিয়ে তার নাম বলুন, ধীরে ও ভারীভাবে]",
                "",
                "That's the heavy sound. Listen again.",
                DOTS,
                "[আবার বলুন]",
            ),
            "does": "শিশুকে গলায় হাত রাখতে বলুন — ভারী হরফে কাঁপুনি টের পায়। "
                    "নিজেও হাত রেখে দেখান। the heavy one that presses the side.",
            "student": "গলায় হাত রেখে শোনে।",
            "expected": "ض — গলায় হাত, মন দিয়ে শোনে।",
            "correction": S(
                "Keep your hand there. Listen once more.",
                DOTS,
                "[ধীরে, ভারীভাবে বলুন]",
                "",
                "Did you feel it that time?",
            ),
            "note": "মাখরাজ: জিহ্বার পাশ উপরের মাড়িতে চাপে — আরবির নিজস্ব হরফ।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Feel It",
                      "arabic": "ض",
                      "text": "🫓 Press the side."},
        },
        {
            "section": "ض — Say it big",
            "says": S(
                "You try. Tap it strong.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Again, one firm tap.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Excellent tapping!",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। ভারী হরফে "
                    "শিশুর সময় লাগে — তাড়া দিলে হালকা করে বলে ফেলে।",
            "student": "হরফটি নিজে বলে, মুখ ভরে।",
            "expected": "ض — নিজে বলে, দুবার।",
            "correction": S(
                "Push the side, then let go slowly.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! One more go.",
            ),
            "note": "প্রথম দিনে নিখুঁত হবে না — ভারী ভাব আসাটাই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Say It Big",
                      "arabic": "ض",
                      "text": "🎤 Fill your mouth!"},
        },
        {
            "section": "ط — Feel it",
            "says": S(
                "This one is special. Listen close.",
                "A tap again, but heavy this time.",
                DOTS,
                "[ط হরফটি দেখিয়ে তার নাম বলুন, ধীরে ও ভারীভাবে]",
                "",
                "Feel it in your throat? Once more.",
                DOTS,
                "[আবার বলুন]",
            ),
            "does": "শিশুকে গলায় হাত রাখতে বলুন — ভারী হরফে কাঁপুনি টের পায়। "
                    "নিজেও হাত রেখে দেখান। a heavy tap, strong and short.",
            "student": "গলায় হাত রেখে শোনে।",
            "expected": "ط — গলায় হাত, মন দিয়ে শোনে।",
            "correction": S(
                "Press a little. Now hear it.",
                DOTS,
                "[ধীরে, ভারীভাবে বলুন]",
                "",
                "Did you feel it that time?",
            ),
            "note": "মাখরাজ: د-এর মতো জায়গা, কিন্তু জোরালো ও ভারী।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Feel It",
                      "arabic": "ط",
                      "text": "🥁 A strong tap."},
        },
        {
            "section": "ط — Say it big",
            "says": S(
                "Your turn. Peek and round it.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Once more, fill your mouth.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Beautiful! So full.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। ভারী হরফে "
                    "শিশুর সময় লাগে — তাড়া দিলে হালকা করে বলে ফেলে।",
            "student": "হরফটি নিজে বলে, মুখ ভরে।",
            "expected": "ط — নিজে বলে, দুবার।",
            "correction": S(
                "Tap harder. Make it strong.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! One more go.",
            ),
            "note": "প্রথম দিনে নিখুঁত হবে না — ভারী ভাব আসাটাই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Say It Big",
                      "arabic": "ط",
                      "text": "🎤 Fill your mouth!"},
        },
        {
            "section": "ظ — Feel it",
            "says": S(
                "Two left. Hand on your throat again.",
                "The tongue peeks out, heavy and full.",
                DOTS,
                "[ظ হরফটি দেখিয়ে তার নাম বলুন, ধীরে ও ভারীভাবে]",
                "",
                "Good. One more listen.",
                DOTS,
                "[আবার বলুন]",
            ),
            "does": "শিশুকে গলায় হাত রাখতে বলুন — ভারী হরফে কাঁপুনি টের পায়। "
                    "নিজেও হাত রেখে দেখান। the heavy one where the tongue peeks.",
            "student": "গলায় হাত রেখে শোনে।",
            "expected": "ظ — গলায় হাত, মন দিয়ে শোনে।",
            "correction": S(
                "Hand on. Eyes on me too.",
                DOTS,
                "[ধীরে, ভারীভাবে বলুন]",
                "",
                "Did you feel it that time?",
            ),
            "note": "মাখরাজ: ذ-এর মতো, কিন্তু মুখ ভরে বলা।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Feel It",
                      "arabic": "ظ",
                      "text": "👅 Heavy peek."},
        },
        {
            "section": "ظ — Say it big",
            "says": S(
                "Now you. From deep inside.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Again — open your throat wide.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! That was deep.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। ভারী হরফে "
                    "শিশুর সময় লাগে — তাড়া দিলে হালকা করে বলে ফেলে।",
            "student": "হরফটি নিজে বলে, মুখ ভরে।",
            "expected": "ظ — নিজে বলে, দুবার।",
            "correction": S(
                "Let it peek, then make it round.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! One more go.",
            ),
            "note": "প্রথম দিনে নিখুঁত হবে না — ভারী ভাব আসাটাই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Say It Big",
                      "arabic": "ظ",
                      "text": "🎤 Fill your mouth!"},
        },
        {
            "section": "ع — Feel it",
            "says": S(
                "The last heavy one. Are you ready?",
                "This comes from deep down. Open your throat.",
                DOTS,
                "[ع হরফটি দেখিয়ে তার নাম বলুন, ধীরে ও ভারীভাবে]",
                "",
                "Last one. Feel it well.",
                DOTS,
                "[আবার বলুন]",
            ),
            "does": "শিশুকে গলায় হাত রাখতে বলুন — ভারী হরফে কাঁপুনি টের পায়। "
                    "নিজেও হাত রেখে দেখান। from deep in the throat, open and warm.",
            "student": "গলায় হাত রেখে শোনে।",
            "expected": "ع — গলায় হাত, মন দিয়ে শোনে।",
            "correction": S(
                "One more feel. Ready?",
                DOTS,
                "[ধীরে, ভারীভাবে বলুন]",
                "",
                "Did you feel it that time?",
            ),
            "note": "মাখরাজ: গলার মাঝখান — শিশুর জন্য কঠিন, ধৈর্য ধরুন।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Feel It",
                      "arabic": "ع",
                      "text": "🫁 Deep and warm."},
        },
        {
            "section": "ع — Say it big",
            "says": S(
                "You say it. Add the gargle.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Once more, very soft.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "Lovely! Just right.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। ভারী হরফে "
                    "শিশুর সময় লাগে — তাড়া দিলে হালকা করে বলে ফেলে।",
            "student": "হরফটি নিজে বলে, মুখ ভরে।",
            "expected": "ع — নিজে বলে, দুবার।",
            "correction": S(
                "Deeper. Like a warm sound from inside.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! One more go.",
            ),
            "note": "প্রথম দিনে নিখুঁত হবে না — ভারী ভাব আসাটাই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Say It Big",
                      "arabic": "ع",
                      "text": "🎤 Fill your mouth!"},
        },
        {
            "section": "غ — Feel it",
            "says": S(
                "New letter. Put your hand on your throat.",
                "Same deep place, but it gargles a little.",
                DOTS,
                "[غ হরফটি দেখিয়ে তার নাম বলুন, ধীরে ও ভারীভাবে]",
                "",
                "Feel that? Now once more.",
                DOTS,
                "[আবার বলুন]",
            ),
            "does": "শিশুকে গলায় হাত রাখতে বলুন — ভারী হরফে কাঁপুনি টের পায়। "
                    "নিজেও হাত রেখে দেখান। deep too, with a soft gargle.",
            "student": "গলায় হাত রেখে শোনে।",
            "expected": "غ — গলায় হাত, মন দিয়ে শোনে।",
            "correction": S(
                "Hand here, on your throat. Now listen.",
                DOTS,
                "[ধীরে, ভারীভাবে বলুন]",
                "",
                "Did you feel it that time?",
            ),
            "note": "মাখরাজ: গলার উপরের অংশ — হালকা ঘড়ঘড়ে শব্দ।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Feel It",
                      "arabic": "غ",
                      "text": "💧 A soft gargle."},
        },
        {
            "section": "غ — Say it big",
            "says": S(
                "Your turn. Big, round mouth!",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Once more, even bigger.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! That was heavy.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। ভারী হরফে "
                    "শিশুর সময় লাগে — তাড়া দিলে হালকা করে বলে ফেলে।",
            "student": "হরফটি নিজে বলে, মুখ ভরে।",
            "expected": "غ — নিজে বলে, দুবার।",
            "correction": S(
                "Add a little gargle. Very soft.",
                DOTS,
                "[আবার করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Better! One more go.",
            ),
            "note": "প্রথম দিনে নিখুঁত হবে না — ভারী ভাব আসাটাই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Say It Big",
                      "arabic": "غ",
                      "text": "🎤 Fill your mouth!"},
        },
        {
            "section": "Compare ص / ض",
            "says": S(
                "Two heavy friends. Listen closely.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "Both heavy. One hisses, one presses.",
                "Now you try both.",
                "[অপেক্ষা করুন — শিশু দুটোই বলবে]",
                "",
                "Well done! You heard the difference.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান, দুবার করে বলুন। তারপর শিশুকে "
                    "দুটোই বলতে দিন। পার্থক্যটা মুখের নড়াচড়ায় দেখিয়ে দিন।",
            "student": "দুটি হরফই বলে।",
            "expected": "দুটির উচ্চারণে পার্থক্য বোঝা যায়।",
            "correction": S(
                "Let's do one at a time. This one first.",
                DOTS,
                "[প্রথমটি ধীরে বলুন]",
                "",
                "Good. Now the other one.",
            ),
            "note": "দুটোই ভারী — পার্থক্য সূক্ষ্ম। কাছাকাছি হলেই প্রশংসা "
                    "করুন, নিখুঁত হওয়ার অপেক্ষা করবেন না।",
            "seconds": 65,
            "slide": {"kind": "question", "heading": "Hear The Difference",
                      "arabic": "ص      ض",
                      "text": "🤔 Feel your tongue."},
        },
        {
            "section": "Compare ط / ظ",
            "says": S(
                "Two heavy friends. Listen closely.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "One taps. One peeks out.",
                "Now you try both.",
                "[অপেক্ষা করুন — শিশু দুটোই বলবে]",
                "",
                "Well done! You heard the difference.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান, দুবার করে বলুন। তারপর শিশুকে "
                    "দুটোই বলতে দিন। পার্থক্যটা মুখের নড়াচড়ায় দেখিয়ে দিন।",
            "student": "দুটি হরফই বলে।",
            "expected": "দুটির উচ্চারণে পার্থক্য বোঝা যায়।",
            "correction": S(
                "Let's do one at a time. This one first.",
                DOTS,
                "[প্রথমটি ধীরে বলুন]",
                "",
                "Good. Now the other one.",
            ),
            "note": "দুটোই ভারী — পার্থক্য সূক্ষ্ম। কাছাকাছি হলেই প্রশংসা "
                    "করুন, নিখুঁত হওয়ার অপেক্ষা করবেন না।",
            "seconds": 65,
            "slide": {"kind": "question", "heading": "Hear The Difference",
                      "arabic": "ط      ظ",
                      "text": "🤔 Tap or peek?"},
        },
        {
            "section": "Compare ع / غ",
            "says": S(
                "Two heavy friends. Listen closely.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "Both deep. One gargles.",
                "Now you try both.",
                "[অপেক্ষা করুন — শিশু দুটোই বলবে]",
                "",
                "Well done! You heard the difference.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান, দুবার করে বলুন। তারপর শিশুকে "
                    "দুটোই বলতে দিন। পার্থক্যটা মুখের নড়াচড়ায় দেখিয়ে দিন।",
            "student": "দুটি হরফই বলে।",
            "expected": "দুটির উচ্চারণে পার্থক্য বোঝা যায়।",
            "correction": S(
                "Let's do one at a time. This one first.",
                DOTS,
                "[প্রথমটি ধীরে বলুন]",
                "",
                "Good. Now the other one.",
            ),
            "note": "দুটোই ভারী — পার্থক্য সূক্ষ্ম। কাছাকাছি হলেই প্রশংসা "
                    "করুন, নিখুঁত হওয়ার অপেক্ষা করবেন না।",
            "seconds": 65,
            "slide": {"kind": "question", "heading": "Hear The Difference",
                      "arabic": "ع      غ",
                      "text": "🤔 Listen to the throat."},
        },
        {
            "section": "Sorting game",
            "says": S(
                "Sorting game! I'll say a letter.",
                "Light one — put your hands up high.",
                "Heavy one — put your hands down low.",
                "Ready? Here we go.",
                DOTS,
                "[একটি হালকা হরফ বলুন]",
                DOTS,
                "[একটি ভারী হরফ বলুন]",
                DOTS,
                "[আরও কয়েকটি, এলোমেলো ক্রমে]",
                "",
                "You got them all! Amazing.",
            ),
            "does": "⚠️ হালকা ও ভারী মিশিয়ে বলুন, ক্রম আন্দাজ করা যেন না যায়। "
                    "শরীর নাড়ানোর খেলা — এই বয়সে বসে থাকার একঘেয়েমি কাটে, "
                    "আর কান দিয়ে চেনা পাকা হয়।",
            "student": "হাত উপরে বা নিচে তোলে।",
            "expected": "হালকায় উপরে, ভারীতে নিচে।",
            "correction": S(
                "Listen again. Is it light or heavy?",
                DOTS,
                "[হরফটি আবার বলুন, ধীরে]",
                "",
                "Heavy! So hands go down.",
            ),
            "note": "ভুল হলে হেসে এগিয়ে যান — এটা খেলা, পরীক্ষা নয়।",
            "seconds": 75,
            "slide": {"kind": "activity", "heading": "Up or Down?",
                      "arabic": "س ص      ت ط      ذ ظ",
                      "text": "🙌 Light up  ·  👇 Heavy down"},
        },
        {
            "section": "Nineteen letters",
            "says": S(
                "Look how far you've come. Nineteen letters!",
                "Let's say them all. I'll go slowly.",
                DOTS,
                "[উনিশটি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "SubhanAllah! Nineteen letters.",
                "You started with none. Look at you now.",
            ),
            "does": "⚠️ ধীরে যান, থেমে থেমে। ক্লান্ত হলে তেরোটির পর দম নিন। "
                    "শেষে কতদূর এসেছে সেটা মনে করিয়ে দিন — আত্মবিশ্বাস বাড়ে।",
            "student": "উনিশটি হরফ সাথে পড়ে।",
            "expected": "ا থেকে غ পর্যন্ত উনিশটি।",
            "correction": S(
                "That's a big list! Let's take it in three parts.",
                DOTS,
                "[সাত, তারপর ছয়, তারপর ছয়]",
                "",
                "See? Three small bites.",
            ),
            "note": "তিন ভাগে ভাগ করলে ছোট শিশুর জন্য অনেক সহজ হয়।",
            "seconds": 80,
            "slide": {"kind": "review", "heading": "Nineteen Letters!",
                      "arabic": "ا ب ت ث ج ح خ\nد ذ ر ز س ش\nص ض ط ظ ع غ",
                      "text": "🌟 Look how far you've come."},
        },
        {
            "section": "Writing — warm up",
            "says": S(
                "Notebook out! But wait — fingers first.",
                "Shake your hands. Wiggle your fingers.",
                "[একসাথে হাত ঝাঁকান]",
                "",
                "Now they're ready. Pencil, please!",
                "[অপেক্ষা করুন]",
            ),
            "does": "হাত ঝাঁকানোর ছোট ব্যায়ামটা কাজে লাগে — আঙুল আলগা হয়, "
                    "লেখা সহজ হয়। নিজেও করুন, শিশু নকল করবে।",
            "student": "হাত ঝাঁকায়, খাতা ও পেনসিল আনে।",
            "expected": "খাতা খোলা, পেনসিল হাতে।",
            "correction": S(
                "No notebook? Any paper is fine.",
                "Go and get it. I'll wait here.",
                "[অপেক্ষা করুন]",
            ),
            "note": "খাতা না থাকলে যেকোনো কাগজেই চলবে — শিশু যেন বাদ না পড়ে।",
            "seconds": 40,
            "slide": {"kind": "write", "heading": "Fingers Ready",
                      "arabic": "ص  ض  ط  ظ  ع  غ",
                      "text": "🤲 Shake, then write!"},
        },
        {
            "section": "Writing — ص ض ط ظ",
            "says": S(
                "Four letters. One line each.",
                DOTS,
                "[পর্দার চারটি হরফ একে একে নাম বলুন]",
                "",
                "Two of them wear a dot. Find them!",
                "Right to left, always.",
                "[অপেক্ষা করুন — ৪৫ সেকেন্ড সময় দিন]",
                "",
                "Show me your line!",
            ),
            "does": "লেখার সময় চুপ থাকুন। ض ও ظ-এ বিন্দু আছে, ص ও ط-এ নেই — "
                    "শিশুকে নিজে খুঁজে বের করতে দিন, বলে দেবেন না।",
            "student": "চারটি হরফ লেখে, দেখায়।",
            "expected": "খাতায় ص ض ط ظ — বিন্দু ঠিক জায়গায়।",
            "correction": S(
                "Good start! Look at the top again.",
                "[পর্দায় বিন্দুটি দেখিয়ে দিন]",
                "",
                "There. Try that one once more.",
            ),
            "note": "⚠️ নিজে খুঁজে পাওয়া শেখা অনেক গভীর হয় — উত্তরটা আগেই "
                    "বলে দেবেন না, একটু অপেক্ষা করুন।",
            "seconds": 90,
            "slide": {"kind": "write", "heading": "Write These Four",
                      "arabic": "ص  ض  ط  ظ",
                      "text": "✏️ Who wears a dot?"},
        },
        {
            "section": "Writing — ع غ",
            "says": S(
                "Two left. These two are cousins.",
                DOTS,
                "[দুটি হরফের নাম বলুন]",
                "",
                "Same shape. One has a dot on top.",
                "Write them side by side. Then compare.",
                "[অপেক্ষা করুন]",
                "",
                "Beautiful work!",
            ),
            "does": "'কাজিন' কথাটা কাজে লাগে — একই আকৃতি, শুধু বিন্দু আলাদা। "
                    "পাশাপাশি লিখতে বললে পার্থক্যটা নিজের চোখেই ধরা পড়ে।",
            "student": "দুটি হরফ পাশাপাশি লেখে।",
            "expected": "খাতায় ع غ — غ-এ উপরে একটি বিন্দু।",
            "correction": S(
                "One dot, right on top.",
                "[পর্দায় বিন্দুটি দেখান]",
                "",
                "Yes, that's it!",
            ),
            "note": "পাশাপাশি লেখালে তুলনাটা শিশু নিজেই করে ফেলে।",
            "seconds": 75,
            "slide": {"kind": "write", "heading": "The Cousins",
                      "arabic": "ع  غ",
                      "text": "✏️ Same shape, one dot."},
        },
        {
            "section": "Writing — show the teacher",
            "says": S(
                "Page up! Let me see all six heavy ones.",
                "[খাতাটি ক্যামেরার সামনে ধরতে বলুন]",
                "",
                "MashaAllah! These are hard letters.",
                "And you wrote every one.",
            ),
            "does": "⚠️ এই ধাপটি বাদ দেবেন না। খাতার দিকে সত্যিই তাকান, আর "
                    "অন্তত একটি হরফের নাম ধরে প্রশংসা করুন। আজকের হরফগুলো "
                    "কঠিন — সেটা বলে দিলে শিশু গর্ব পায়।",
            "student": "পুরো পাতা ক্যামেরায় দেখায়।",
            "expected": "ছয়টি হরফ লেখা একটি পাতা।",
            "correction": S(
                "Even two is good work today.",
                "These letters are hard. You tried.",
                "That's what a good student does.",
            ),
            "note": "কম লিখলেও প্রশংসা করুন — উদ্দেশ্য চেষ্টা, পাতা ভরানো নয়।",
            "seconds": 50,
            "slide": {"kind": "write", "heading": "Show Me Your Page",
                      "arabic": "ص  ض  ط  ظ  ع  غ",
                      "text": "📓 Hold it up!"},
        },
        {
            "section": "Well done",
            "says": S(
                "Come closer. I want to tell you something.",
                "[অপেক্ষা করুন]",
                "",
                "These six were the hardest so far.",
                "And you did them. All six.",
                "I'm really proud of you today.",
            ),
            "does": "⚠️ এই ধাপটি কেবল প্রশংসার — কোনো শেখানো নেই। কঠিন দারসের "
                    "পর শিশুর এটা দরকার হয়। চোখে তাকিয়ে, ধীরে বলুন।",
            "student": "শোনে, হাসে।",
            "expected": "খুশি হয়, আত্মবিশ্বাস পায়।",
            "correction": S(
                "You worked hard today. I saw it.",
                "That matters more than being perfect.",
            ),
            "note": "কঠিন দিনের পর আলাদা করে প্রশংসা করলে শিশু পরের দিন "
                    "ভয় পায় না।",
            "seconds": 35,
            "slide": {"kind": "praise", "heading": "You Did It!",
                      "arabic": "أَحْسَنْتَ",
                      "text": "🌟 The hardest six — done."},
        },
        {
            "section": "Homework",
            "says": S(
                "Tiny homework. Just two things.",
                "Say today's six letters, twice a day.",
                "And write them once, with a big round mouth.",
                "Deal?",
                "[অপেক্ষা করুন]",
                "",
                "Shukran! I'll ask you next time.",
            ),
            "does": "বাড়ির কাজটা ধীরে বলুন, অভিভাবক শুনলে যেন লিখে নিতে "
                    "পারেন। 'Deal?' কথাটা খেলার মতো, শিশু সহজে রাজি হয়।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Deal!",
            "correction": S(
                "Only two minutes a day.",
                "You have done harder things today!",
            ),
            "note": "অভিভাবকের জন্য — ভারী হরফ বাড়িতে ঠিক করতে যাবেন না। "
                    "শুধু বলতে দিন, বাকিটা ক্লাসে দেখা হবে।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Our Deal",
                      "arabic": "ص  ض  ط  ظ  ع  غ",
                      "text": "📖 Twice a day.\n✏️ Write once."},
        },
        {
            "section": "Closing",
            "says": S(
                "Nineteen letters, and six heavy ones today.",
                "Baraka Allahu fik, my clever student.",
                "Next time, six more!",
                "Assalamu alaikum wa rahmatullah!",
            ),
            "does": "হাসুন, হাত নাড়ুন। পরের দারসের কথা বলে শেষ করুন — "
                    "শিশু অপেক্ষা করতে শেখে।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "Assalamu alaikum! Say it back to me.",
                "[অপেক্ষা করুন]",
                "",
                "See you next time!",
            ),
            "note": "মিলিয়ে নিন: শিশু নিজে উস্তাদ সেজেছে · হালকা-ভারী পার্থক্য "
                    "শুনেছে · ছয়টি হরফ শোনা ও বলা হয়েছে · তিনটি জোড়া মেলানো "
                    "হয়েছে · বাছাইয়ের খেলা হয়েছে · উনিশটি একসাথে বলা হয়েছে · "
                    "খাতায় লিখেছে ও দেখিয়েছে।",
            "seconds": 30,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "👋 Six more next time!"},
        },
    ],
}




# ═══════════════ কায়দা — দারস ৪ ═══════════════
# ⚠️ আবারও নতুন চেহারা। দারস ১ সালাম ও পরিচয়ে, ২ পুরনো হরফের খেলায়,
# ৩ ভূমিকা বদলে — এটি শুরু হয় শিশুর চেনা আয়াত দিয়ে। আজকের হরফগুলো সে
# আগেই শুনেছে সূরা ইখলাসে, তাই সুতোটা: "তুমি এগুলো আগেই চেনো"।
QAIDA4 = {
    "title": "Easy Noorani Qaida — Lesson 4: You Know These Already",
    "title_ar": "الحروف المفردة ٤",
    "kind": "qaida",
    "lesson_no": 4,
    "age_from": 5,
    "age_to": 7,
    "duration_min": 22,
    "objectives": (
        "<p><b>Noorani Qaida — Lesson 4 · Teacher Script</b><br>"
        "Age 5-7 · about 22 minutes · Six everyday letters<br>"
        "Find &rarr; Listen &rarr; Say &rarr; Compare &rarr; Write</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause, what to show, and which letter to name.</li>"
        "<li>Where you see <b>…………</b>, say the name of the letter shown "
        "on the screen. Arabic is never written in English letters.</li>"
        "</ul>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Know <b>ف ق ك ل م ن</b> on sight, in any order</li>"
        "<li>Spot these letters inside a Surah they already know</li>"
        "<li>Write all six in their own notebook, right to left</li>"
        "<li>Say all twenty-five letters learned so far</li>"
        "</ul>"
    ),
    "steps": [
        {
            "section": "A letter hunt",
            "says": S(
                "Assalamu alaikum! Look at the screen.",
                "You know this Surah, don't you?",
                "[অপেক্ষা করুন — শিশু চিনবে]",
                "",
                "Now find me a letter. Any letter you know!",
                "[অপেক্ষা করুন — শিশু আঙুল দেখাবে]",
                "",
                "MashaAllah! You found one.",
                "Today's letters are hiding right here.",
            ),
            "does": "সূরা ইখলাসের প্রথম আয়াতটি দেখান — শিশু এটি মুখস্থ করেছে। "
                    "চেনা জিনিস দিয়ে শুরু করলে নতুন হরফ কম ভয় লাগে।",
            "student": "চেনা হরফ খুঁজে দেখায়।",
            "expected": "যেকোনো চেনা হরফে আঙুল।",
            "correction": S(
                "Look here, at the first word.",
                "[প্রথম শব্দটি দেখিয়ে দিন]",
                "",
                "Do you know this one? Yes, you do!",
            ),
            "note": "আজকের ق ও ل দুটোই এই আয়াতেই আছে — শেষে সেটা মনে "
                    "করিয়ে দিলে শিশু গর্ব পায়।",
            "seconds": 55,
            "slide": {"kind": "activity", "heading": "Find A Letter",
                      "arabic": "قُلْ هُوَ ٱللَّهُ أَحَدٌ ۝١",
                      "text": "🔎 Point to one you know!"},
        },
        {
            "section": "Today's six",
            "says": S(
                "Here they are. Six everyday letters.",
                "You hear these every single day.",
                "In Salah, in duas, in the Qur'an.",
                "Let's meet them properly.",
            ),
            "does": "ছয়টি হরফ একসাথে দেখান। 'রোজ শোনো' কথাটা বলুন — শিশু "
                    "বুঝলে আগ্রহ বাড়ে যে এগুলো অচেনা নয়।",
            "student": "পর্দার দিকে তাকায়।",
            "expected": "আগ্রহ নিয়ে তাকায়।",
            "correction": S(
                "Eyes here. Six letters. Count them with me.",
                "[একসাথে গুনুন]",
            ),
            "note": "সুতো: এগুলো নতুন নয়, শিশু আগেই শুনেছে — কেবল নাম "
                    "শেখা বাকি।",
            "seconds": 35,
            "slide": {"kind": "title", "heading": "Six Everyday Letters",
                      "arabic": "ف  ق  ك  ل  م  ن",
                      "text": "🗣️ You hear these daily!"},
        },
        {
            "section": "ف — Watch",
            "says": S(
                "Top teeth touch the bottom lip. Watch.",
                DOTS,
                "[ف হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "See how I do it? Once more.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: উপরের দাঁত নিচের ঠোঁটে — শিশুকে করে দেখান।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ف — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Look at my mouth, not the screen.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Now watch one more time.",
            ),
            "note": "মাখরাজ: উপরের দাঁত নিচের ঠোঁটে — শিশুকে করে দেখান।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Watch Me",
                      "arabic": "ف",
                      "text": "🦷 Teeth on lip."},
        },
        {
            "section": "ف — You try",
            "says": S(
                "Now you. Teeth on your lip.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Good! One more, a bit clearer.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! You've got it.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ف — নিজে বলে, দুবার।",
            "correction": S(
                "Teeth down, then blow softly.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Much better! Once more.",
            ),
            "note": "নিখুঁত না হলেও চলে — চেষ্টাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "You Try",
                      "arabic": "ف",
                      "text": "🎤 Your turn now."},
        },
        {
            "section": "ق — Watch",
            "says": S(
                "This one comes from way back. Listen.",
                DOTS,
                "[ق হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "See how I do it? Once more.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: জিহ্বার পেছন উপরের তালুতে — ভারী হরফ।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ق — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Look at my mouth, not the screen.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Now watch one more time.",
            ),
            "note": "মাখরাজ: জিহ্বার পেছন উপরের তালুতে — ভারী হরফ।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Watch Me",
                      "arabic": "ق",
                      "text": "🫁 Way back."},
        },
        {
            "section": "ق — You try",
            "says": S(
                "Your turn. Push it back.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Good! One more, a bit clearer.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! You've got it.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ق — নিজে বলে, দুবার।",
            "correction": S(
                "Further back. Feel your throat.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Much better! Once more.",
            ),
            "note": "নিখুঁত না হলেও চলে — চেষ্টাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "You Try",
                      "arabic": "ق",
                      "text": "🎤 Your turn now."},
        },
        {
            "section": "ك — Watch",
            "says": S(
                "Almost the same place, but softer.",
                DOTS,
                "[ك হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "See how I do it? Once more.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: ق-এর একটু সামনে — হালকা, ক্ষীণ।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ك — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Look at my mouth, not the screen.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Now watch one more time.",
            ),
            "note": "মাখরাজ: ق-এর একটু সামনে — হালকা, ক্ষীণ।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Watch Me",
                      "arabic": "ك",
                      "text": "👋 A soft knock."},
        },
        {
            "section": "ك — You try",
            "says": S(
                "You try. A little softer.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Good! One more, a bit clearer.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! You've got it.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ك — নিজে বলে, দুবার।",
            "correction": S(
                "Softer than the last one. Try again.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Much better! Once more.",
            ),
            "note": "নিখুঁত না হলেও চলে — চেষ্টাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "You Try",
                      "arabic": "ك",
                      "text": "🎤 Your turn now."},
        },
        {
            "section": "ل — Watch",
            "says": S(
                "Tongue tip touches the roof. See?",
                DOTS,
                "[ل হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "See how I do it? Once more.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: জিহ্বার ডগা উপরের মাড়ির গোড়ায়।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ل — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Look at my mouth, not the screen.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Now watch one more time.",
            ),
            "note": "মাখরাজ: জিহ্বার ডগা উপরের মাড়ির গোড়ায়।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Watch Me",
                      "arabic": "ل",
                      "text": "👅 Tongue tip up."},
        },
        {
            "section": "ل — You try",
            "says": S(
                "Now you. Tip up, then down.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Good! One more, a bit clearer.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! You've got it.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ل — নিজে বলে, দুবার।",
            "correction": S(
                "Touch the roof, then let go.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Much better! Once more.",
            ),
            "note": "নিখুঁত না হলেও চলে — চেষ্টাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "You Try",
                      "arabic": "ل",
                      "text": "🎤 Your turn now."},
        },
        {
            "section": "م — Watch",
            "says": S(
                "Lips close tight, then open. Look.",
                DOTS,
                "[م হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "See how I do it? Once more.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: দুই ঠোঁট বন্ধ — নাক দিয়ে সামান্য বাতাস।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "م — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Look at my mouth, not the screen.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Now watch one more time.",
            ),
            "note": "মাখরাজ: দুই ঠোঁট বন্ধ — নাক দিয়ে সামান্য বাতাস।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Watch Me",
                      "arabic": "م",
                      "text": "🤐 Lips shut."},
        },
        {
            "section": "م — You try",
            "says": S(
                "Your go. Close your lips first.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Good! One more, a bit clearer.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! You've got it.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "م — নিজে বলে, দুবার।",
            "correction": S(
                "Shut them fully, then open.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Much better! Once more.",
            ),
            "note": "নিখুঁত না হলেও চলে — চেষ্টাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "You Try",
                      "arabic": "م",
                      "text": "🎤 Your turn now."},
        },
        {
            "section": "ن — Watch",
            "says": S(
                "Feel your nose for this one.",
                DOTS,
                "[ن হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "See how I do it? Once more.",
                DOTS,
                "[আবার বলুন, একটু ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: জিহ্বার ডগা ও নাক — শিশুকে নাকে হাত রাখতে বলুন।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ن — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Look at my mouth, not the screen.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "Now watch one more time.",
            ),
            "note": "মাখরাজ: জিহ্বার ডগা ও নাক — শিশুকে নাকে হাত রাখতে বলুন।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Watch Me",
                      "arabic": "ن",
                      "text": "👃 Through the nose."},
        },
        {
            "section": "ن — You try",
            "says": S(
                "You say it. Hand on your nose.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Good! One more, a bit clearer.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! You've got it.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। তাড়া দিলে "
                    "শিশু চেষ্টাই করে না।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ن — নিজে বলে, দুবার।",
            "correction": S(
                "Feel the buzz in your nose.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "Much better! Once more.",
            ),
            "note": "নিখুঁত না হলেও চলে — চেষ্টাটাই আজকের কাজ।",
            "seconds": 40,
            "slide": {"kind": "your_turn", "heading": "You Try",
                      "arabic": "ن",
                      "text": "🎤 Your turn now."},
        },
        {
            "section": "Look closely — ف / ق",
            "says": S(
                "Two letters. Look really closely.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "One dot, or two? Look up top.",
                "Now point to the first one I said.",
                "[অপেক্ষা করুন]",
                "",
                "Yes! Well spotted.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান, দুবার করে বলুন। তারপর শিশুকে "
                    "প্রথমটি দেখাতে বলুন — শোনা ও দেখা দুটোই যাচাই হয়।",
            "student": "সঠিক হরফটি দেখায়।",
            "expected": "প্রথমে বলা হরফটিতে আঙুল।",
            "correction": S(
                "Listen once more, then look.",
                DOTS,
                "[প্রথমটি আবার বলুন]",
                "",
                "That one. Can you find it?",
            ),
            "note": "একসাথে শোনা ও দেখা মেলানো — এতেই চেনা পাকা হয়।",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Look Closely",
                      "arabic": "ف      ق",
                      "text": "🔍 Count the dots!"},
        },
        {
            "section": "Look closely — م / ن",
            "says": S(
                "Two letters. Look really closely.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন]",
                DOTS,
                "[দ্বিতীয় হরফটির নাম বলুন]",
                "",
                "One shuts the lips. One uses the nose.",
                "Now point to the first one I said.",
                "[অপেক্ষা করুন]",
                "",
                "Yes! Well spotted.",
            ),
            "does": "দুটি হরফ পাশাপাশি দেখান, দুবার করে বলুন। তারপর শিশুকে "
                    "প্রথমটি দেখাতে বলুন — শোনা ও দেখা দুটোই যাচাই হয়।",
            "student": "সঠিক হরফটি দেখায়।",
            "expected": "প্রথমে বলা হরফটিতে আঙুল।",
            "correction": S(
                "Listen once more, then look.",
                DOTS,
                "[প্রথমটি আবার বলুন]",
                "",
                "That one. Can you find it?",
            ),
            "note": "একসাথে শোনা ও দেখা মেলানো — এতেই চেনা পাকা হয়।",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Look Closely",
                      "arabic": "م      ن",
                      "text": "🔍 Lips or nose?"},
        },
        {
            "section": "Back to the Surah",
            "says": S(
                "Remember the Surah from the start?",
                "Two of today's letters are hiding in it.",
                DOTS,
                "[প্রথম হরফটির নাম বলুন, আয়াতে দেখিয়ে দিন]",
                DOTS,
                "[দ্বিতীয়টির নাম বলুন, দেখিয়ে দিন]",
                "",
                "You've been saying them all along!",
                "You just didn't know their names.",
            ),
            "does": "সূরা ইখলাসের প্রথম আয়াতে ق ও ل দেখিয়ে দিন। শিশু বুঝলে "
                    "যে সে আগেই এগুলো বলেছে, আত্মবিশ্বাস অনেক বাড়ে।",
            "student": "আয়াতে হরফ দুটি দেখে।",
            "expected": "আয়াতের ভেতরে হরফ চিনতে পারে।",
            "correction": S(
                "Look at the very first word.",
                "[শব্দটি দেখিয়ে দিন]",
                "",
                "There it is! Do you see it now?",
            ),
            "note": "চেনা আয়াতের সাথে জুড়ে দেওয়া — কায়দা আর কুরআন আলাদা "
                    "নয়, এটাই বোঝানোর সহজ পথ।",
            "seconds": 55,
            "slide": {"kind": "visual", "heading": "They Were Hiding Here!",
                      "arabic": "قُلْ هُوَ ٱللَّهُ أَحَدٌ ۝١",
                      "text": "🔎 Two of today's letters!"},
        },
        {
            "section": "Letter fishing",
            "says": S(
                "Fishing time! I'll say a letter.",
                "You catch it — point to it fast!",
                DOTS,
                "[একটি হরফের নাম বলুন]",
                DOTS,
                "[আরেকটি, এলোমেলো ক্রমে]",
                DOTS,
                "[আরও কয়েকটি, দ্রুত]",
                "",
                "You caught them all! Great fishing.",
            ),
            "does": "⚠️ এলোমেলো ক্রমে বলুন, দ্রুত। খেলার মতো করুন — গলায় "
                    "উত্তেজনা রাখুন। ভুল হলে হেসে এগিয়ে যান।",
            "student": "নাম শুনে হরফটি দেখায়।",
            "expected": "যে হরফ বলা হলো, তাতেই আঙুল।",
            "correction": S(
                "Let me say it slower this time.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Now find it. Take your time.",
            ),
            "note": "শোনা থেকে চেনা — পড়ার আসল ভিত্তি এটাই।",
            "seconds": 70,
            "slide": {"kind": "activity", "heading": "Catch The Letter",
                      "arabic": "ف  ق  ك  ل  م  ن",
                      "text": "🎣 Point to the one I say!"},
        },
        {
            "section": "All six together",
            "says": S(
                "All six now, from the start.",
                DOTS,
                "[ছয়টি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "Beautiful. One more round.",
                DOTS,
                "[আবার, একটু দ্রুত]",
                "",
                "MashaAllah!",
            ),
            "does": "প্রতিটি হরফে আঙুল রাখুন। দুবার — ধীরে, তারপর একটু দ্রুত।",
            "student": "সাথে পড়ে।",
            "expected": "ف ق ك ل م ن — ছয়টি ঠিক ক্রমে।",
            "correction": S(
                "Slow down. Back to the first one.",
                DOTS,
                "[প্রথম দুটির নাম ধীরে বলুন]",
                "",
                "Good, keep going!",
            ),
            "note": "একটা ভুলে থামবেন না — গতি কমিয়ে পুরোটা শেষ করুন।",
            "seconds": 55,
            "slide": {"kind": "repeat", "heading": "All Six",
                      "arabic": "ف  ق  ك  ل  م  ن",
                      "text": "🎤 Together now."},
        },
        {
            "section": "Twenty-five!",
            "says": S(
                "Now count with me. Twenty-five letters!",
                "That's nearly all of them.",
                "Let's say them. Slowly, in three parts.",
                DOTS,
                "[পঁচিশটি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "SubhanAllah! Twenty-five.",
            ),
            "does": "⚠️ তিন ভাগে ভাগ করুন — সাত, ছয়, ছয়, তারপর ছয়। ক্লান্ত "
                    "হলে মাঝে দম নিন। কতদূর এসেছে তা বলে দিন।",
            "student": "পঁচিশটি হরফ সাথে পড়ে।",
            "expected": "ا থেকে ن পর্যন্ত পঁচিশটি।",
            "correction": S(
                "That's a long list! Small bites, then.",
                DOTS,
                "[প্রথম সাতটি আলাদা করে]",
                "",
                "See? Much easier.",
            ),
            "note": "ছোট ভাগে ভাগ করলে শিশু ভয় পায় না।",
            "seconds": 85,
            "slide": {"kind": "review", "heading": "Twenty-Five Letters!",
                      "arabic": "ا ب ت ث ج ح خ\nد ذ ر ز س ش\nص ض ط ظ ع غ\nف ق ك ل م ن",
                      "text": "🌟 Nearly all of them!"},
        },
        {
            "section": "Writing — get ready",
            "says": S(
                "Notebook, please! You know the routine.",
                "[অপেক্ষা করুন — খাতা ও পেনসিল আনতে দিন]",
                "",
                "Pencil up! Show me.",
                "[শিশু পেনসিল দেখালে হাসুন]",
                "",
                "Good. Right side first, always.",
            ),
            "does": "চতুর্থ দারস — শিশু এখন অভ্যস্ত। শুধু ডান দিক থেকে শুরুর "
                    "কথাটা মনে করিয়ে দিন, বিস্তারিত লাগবে না।",
            "student": "খাতা ও পেনসিল আনে।",
            "expected": "খাতা খোলা, পেনসিল হাতে।",
            "correction": S(
                "No notebook? Any paper is fine.",
                "Go get it. I'll wait.",
                "[অপেক্ষা করুন]",
            ),
            "note": "খাতা না থাকলে যেকোনো কাগজেই চলবে — শিশু যেন বাদ না পড়ে।",
            "seconds": 35,
            "slide": {"kind": "write", "heading": "Notebook Time",
                      "arabic": "ف  ق  ك  ل  م  ن",
                      "text": "✏️ Right side first!"},
        },
        {
            "section": "Writing — ف ق ك",
            "says": S(
                "Three letters. One line each.",
                DOTS,
                "[তিনটি হরফের নাম একে একে বলুন]",
                "",
                "One dot, two dots, and none. Watch out!",
                "Off you go. I'm right here.",
                "[অপেক্ষা করুন — ৪০ সেকেন্ড সময় দিন]",
                "",
                "Show me your line!",
            ),
            "does": "লেখার সময় চুপ থাকুন। ف-এ একটি বিন্দু, ق-এ দুটি, ك-এ "
                    "কোনোটিই নেই — সংখ্যাটা আগেই বলে দিন।",
            "student": "তিনটি হরফ লেখে, দেখায়।",
            "expected": "খাতায় ف ق ك — বিন্দু ঠিক সংখ্যায়।",
            "correction": S(
                "Good start! How many dots on this one?",
                "[পর্দায় বিন্দুগুলো গুনে দেখান]",
                "",
                "That's it. Try again.",
            ),
            "note": "⚠️ হাতের লেখা সুন্দর হওয়ার দরকার নেই। বিন্দুর সংখ্যাই "
                    "আজকের শিক্ষা।",
            "seconds": 80,
            "slide": {"kind": "write", "heading": "Count The Dots",
                      "arabic": "ف  ق  ك",
                      "text": "✏️ One, two, none."},
        },
        {
            "section": "Writing — ل م ن",
            "says": S(
                "Three more. These are tall and round.",
                DOTS,
                "[তিনটি হরফের নাম বলুন]",
                "",
                "One stands tall. Two have round tummies!",
                "Write them now.",
                "[অপেক্ষা করুন]",
                "",
                "Lovely. Hold it up!",
            ),
            "does": "'লম্বা' ও 'গোল পেট' — এই ছবিগুলো শিশুর মনে গেঁথে যায়। "
                    "ل লম্বা, م ও ن-এর গোল অংশ দেখিয়ে দিন।",
            "student": "তিনটি হরফ লেখে, দেখায়।",
            "expected": "খাতায় ل م ن।",
            "correction": S(
                "Make this one taller. Right up!",
                "[পর্দায় ل দেখান]",
                "",
                "Yes, much better.",
            ),
            "note": "আকৃতির ছবি দিয়ে বললে ছোট শিশু সহজে মনে রাখে।",
            "seconds": 75,
            "slide": {"kind": "write", "heading": "Tall And Round",
                      "arabic": "ل  م  ن",
                      "text": "✏️ One tall, two round."},
        },
        {
            "section": "Writing — show the teacher",
            "says": S(
                "Page up! All six, please.",
                "[খাতাটি ক্যামেরার সামনে ধরতে বলুন]",
                "",
                "MashaAllah! Every one of them.",
                "Your handwriting is getting better.",
            ),
            "does": "⚠️ এই ধাপটি বাদ দেবেন না। খাতার দিকে সত্যিই তাকান। "
                    "চতুর্থ দারসে উন্নতি চোখে পড়ে — সেটা বলে দিন।",
            "student": "পুরো পাতা ক্যামেরায় দেখায়।",
            "expected": "ছয়টি হরফ লেখা একটি পাতা।",
            "correction": S(
                "Even four is good work today.",
                "You're writing better each time.",
                "Next time we'll finish the rest.",
            ),
            "note": "উন্নতির কথা বললে শিশু পরের দিন আরও চেষ্টা করে।",
            "seconds": 45,
            "slide": {"kind": "write", "heading": "Show Me Your Page",
                      "arabic": "ف  ق  ك  ل  م  ن",
                      "text": "📓 Hold it up!"},
        },
        {
            "section": "Only four left",
            "says": S(
                "Do you know what? Only four letters left.",
                "Four! Then you'll know them all.",
                "Next time we finish the whole alphabet.",
                "Are you excited?",
                "[অপেক্ষা করুন]",
            ),
            "does": "⚠️ গোনার এই কথাটা শিশুকে টেনে রাখে — শেষ কতদূর তা জানলে "
                    "সে অপেক্ষা করে। উৎসাহ নিয়ে বলুন।",
            "student": "শোনে, খুশি হয়।",
            "expected": "Yes!",
            "correction": S(
                "Just four more. You can count them!",
                "[চারটি আঙুল দেখান]",
            ),
            "note": "পরের দারসের জন্য আগ্রহ তৈরি — শিশু ফিরে আসতে চায়।",
            "seconds": 40,
            "slide": {"kind": "reminder", "heading": "Almost There!",
                      "arabic": "و  ه  ء  ي",
                      "text": "4️⃣ Four letters to go!"},
        },
        {
            "section": "All by yourself",
            "says": S(
                "Now just you. I'll keep quiet.",
                "Say all six, in order. Off you go!",
                "[অপেক্ষা করুন — একবারও সাহায্য করবেন না]",
                "",
                "MashaAllah! All six, on your own.",
            ),
            "does": "⚠️ সত্যিই চুপ থাকুন। মাঝপথে বলে দিলে শিশু কখনো নিজে "
                    "চেষ্টা করতে শেখে না। আটকে গেলে পাঁচ সেকেন্ড অপেক্ষা "
                    "করে তবেই সূত্র দিন।",
            "student": "ছয়টি হরফ একা বলে।",
            "expected": "ف ق ك ل م ن — একা, ক্রম ধরে।",
            "correction": S(
                "Stuck? Here's the first one.",
                DOTS,
                "[কেবল প্রথমটির নাম বলুন]",
                "",
                "Now carry on. You know the rest.",
            ),
            "note": "নিজে বলতে পারা আর সাথে বলা এক নয় — এটাই আসল যাচাই।",
            "seconds": 55,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "arabic": "ف  ق  ك  ل  م  ن",
                      "text": "🎤 I'm listening."},
        },
        {
            "section": "Homework",
            "says": S(
                "Homework, and it's an easy one.",
                "Say today's six letters twice a day.",
                "And write them once. Just one line.",
                "Will you do it for me?",
                "[অপেক্ষা করুন]",
                "",
                "Shukran! See you next time.",
            ),
            "does": "বাড়ির কাজটা ধীরে বলুন, অভিভাবক শুনলে যেন লিখে নিতে "
                    "পারেন। ছোট রাখুন — শিশু তখনই করে।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": S(
                "Only two minutes a day.",
                "You have done much harder things!",
            ),
            "note": "অভিভাবকের জন্য — শুধু শুনুন। ভুল হলে বাড়িতে ঠিক করতে "
                    "যাবেন না, উস্তাদের জন্য রেখে দিন।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Easy Homework",
                      "arabic": "ف  ق  ك  ل  م  ن",
                      "text": "📖 Twice a day.\n✏️ One line."},
        },
        {
            "section": "Closing",
            "says": S(
                "Twenty-five letters, mashaAllah.",
                "Baraka Allahu fik, my hard-working student.",
                "Next time — the last four!",
                "Assalamu alaikum wa rahmatullah!",
            ),
            "does": "হাসুন, হাত নাড়ুন। পরের দারসের কথা বলে শেষ করুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "Assalamu alaikum! Say it back to me.",
                "[অপেক্ষা করুন]",
                "",
                "See you next time!",
            ),
            "note": "মিলিয়ে নিন: চেনা আয়াতে হরফ খুঁজেছে · ছয়টি হরফ শোনা ও "
                    "বলা হয়েছে · দুটি জোড়া মেলানো হয়েছে · ধরার খেলা হয়েছে · "
                    "পঁচিশটি একসাথে বলা হয়েছে · খাতায় লিখেছে ও দেখিয়েছে।",
            "seconds": 30,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "👋 The last four next time!"},
        },
    ],
}


# ═══════════════ কায়দা — দারস ৫ ═══════════════
# ⚠️ শেষ দারস, তাই চেহারাটাও শেষের মতো। দারস ১ পরিচয়ে, ২ খেলায়,
# ৩ ভূমিকা বদলে, ৪ চেনা আয়াতে — এটি শুরু হয় গোনা দিয়ে: "আজ শেষ দিন"।
# সুতো: পূর্ণতা ও উদযাপন। শেষে পরের ধাপের দরজা খুলে দেওয়া হয়।
QAIDA5 = {
    "title": "Easy Noorani Qaida — Lesson 5: The Last Four",
    "title_ar": "الحروف المفردة ٥",
    "kind": "qaida",
    "lesson_no": 5,
    "age_from": 5,
    "age_to": 7,
    "duration_min": 18,
    "objectives": (
        "<p><b>Noorani Qaida — Lesson 5 · Teacher Script</b><br>"
        "Age 5-7 · about 18 minutes · The last four letters<br>"
        "Count down &rarr; Listen &rarr; Say &rarr; Write &rarr; Celebrate</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause, what to show, and which letter to name.</li>"
        "<li>Where you see <b>…………</b>, say the name of the letter shown "
        "on the screen. Arabic is never written in English letters.</li>"
        "</ul>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Know <b>و ه ء ي</b> on sight, in any order</li>"
        "<li>Say the whole alphabet — all twenty-nine letters</li>"
        "<li>Write the last four in their own notebook</li>"
        "<li>Know what comes next: joining letters into words</li>"
        "</ul>"
    ),
    "steps": [
        {
            "section": "The big day",
            "says": S(
                "Assalamu alaikum! Today is a big day.",
                "Do you remember how many are left?",
                "[অপেক্ষা করুন — শিশু বলার চেষ্টা করবে]",
                "",
                "Four! Just four letters.",
                "After today, you'll know them all.",
            ),
            "does": "⚠️ আজ শেষ দারস — গলায় উত্তেজনা রাখুন। গত দারসে চারটি "
                    "বাকি বলেছিলেন, সেটাই মনে করিয়ে দিন। শিশু নিজে বলতে "
                    "পারলে খুব খুশি হয়।",
            "student": "মনে করার চেষ্টা করে, উত্তর দেয়।",
            "expected": "Four!",
            "correction": S(
                "Show me four fingers. Count them.",
                "[একসাথে গুনুন]",
                "",
                "Yes — four letters left!",
            ),
            "note": "শেষের দিনটা আলাদা করে বোঝানো দরকার — শিশু গর্ব নিয়ে "
                    "শেষ করবে।",
            "seconds": 50,
            "slide": {"kind": "title", "heading": "The Last Four!",
                      "arabic": "و  ه  ء  ي",
                      "text": "4️⃣ Today we finish!"},
        },
        {
            "section": "Count down from twenty-five",
            "says": S(
                "First, let's count what you already know.",
                "Twenty-five letters. Ready?",
                DOTS,
                "[পঁচিশটি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "SubhanAllah. Twenty-five, all yours.",
                "Now let's collect the last four.",
            ),
            "does": "⚠️ ধীরে যান, চার ভাগে। এটি ঝালাই ও উৎসাহ দুটোই — কতদূর "
                    "এসেছে চোখে দেখলে শেষ চারটিতে মন বসে।",
            "student": "পঁচিশটি হরফ সাথে পড়ে।",
            "expected": "ا থেকে ن পর্যন্ত পঁচিশটি।",
            "correction": S(
                "Let's do it in small groups.",
                DOTS,
                "[প্রথম সাতটি আলাদা করে]",
                "",
                "That's the way. Carry on.",
            ),
            "note": "ভুল হলে থামবেন না — আজ ঝালাই মুখ্য নয়, শেষ চারটিই মুখ্য।",
            "seconds": 80,
            "slide": {"kind": "review", "heading": "Twenty-Five So Far",
                      "arabic": "ا ب ت ث ج ح خ\nد ذ ر ز س ش\nص ض ط ظ ع غ\nف ق ك ل م ن",
                      "text": "🌟 All of these are yours!"},
        },
        {
            "section": "و — Look and listen",
            "says": S(
                "Round your lips into a small circle.",
                DOTS,
                "[و হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "Watch my mouth again.",
                DOTS,
                "[আবার বলুন, ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: দুই ঠোঁট গোল করে — ছোঁয়ানো নয়।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "و — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Come closer to the screen and watch.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "One more look, then you try.",
            ),
            "note": "মাখরাজ: দুই ঠোঁট গোল করে — ছোঁয়ানো নয়।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Look And Listen",
                      "arabic": "و",
                      "text": "👄 Round lips."},
        },
        {
            "section": "و — Now you",
            "says": S(
                "Your turn. Make a little circle.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Yes! Once more, nice and clear.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! Another one done.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। আজ শেষ "
                    "দারস — শিশু উত্তেজিত, তাই ধীর রাখতে হবে।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "و — নিজে বলে, দুবার।",
            "correction": S(
                "Rounder. Like blowing a candle.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "That's it! Try once more.",
            ),
            "note": "শেষ চারটির মধ্যে ء সবচেয়ে কঠিন — কাছাকাছি হলেই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Now You",
                      "arabic": "و",
                      "text": "🎤 Your turn!"},
        },
        {
            "section": "ه — Look and listen",
            "says": S(
                "This one is only breath. Very soft.",
                DOTS,
                "[ه হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "Watch my mouth again.",
                DOTS,
                "[আবার বলুন, ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: গলার একদম গোড়া — কেবল নিঃশ্বাস।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ه — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Come closer to the screen and watch.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "One more look, then you try.",
            ),
            "note": "মাখরাজ: গলার একদম গোড়া — কেবল নিঃশ্বাস।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Look And Listen",
                      "arabic": "ه",
                      "text": "🌬️ Just breath."},
        },
        {
            "section": "ه — Now you",
            "says": S(
                "You try. Just breathe it out.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Yes! Once more, nice and clear.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! Another one done.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। আজ শেষ "
                    "দারস — শিশু উত্তেজিত, তাই ধীর রাখতে হবে।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ه — নিজে বলে, দুবার।",
            "correction": S(
                "Softer. No voice, only air.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "That's it! Try once more.",
            ),
            "note": "শেষ চারটির মধ্যে ء সবচেয়ে কঠিন — কাছাকাছি হলেই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Now You",
                      "arabic": "ه",
                      "text": "🎤 Your turn!"},
        },
        {
            "section": "ء — Look and listen",
            "says": S(
                "A little stop, right in your throat.",
                DOTS,
                "[ء হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "Watch my mouth again.",
                DOTS,
                "[আবার বলুন, ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: গলার একদম নিচে — বাতাস এক মুহূর্ত থামে।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ء — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Come closer to the screen and watch.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "One more look, then you try.",
            ),
            "note": "মাখরাজ: গলার একদম নিচে — বাতাস এক মুহূর্ত থামে।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Look And Listen",
                      "arabic": "ء",
                      "text": "✋ A tiny stop."},
        },
        {
            "section": "ء — Now you",
            "says": S(
                "Now you. Stop, then let go.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Yes! Once more, nice and clear.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! Another one done.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। আজ শেষ "
                    "দারস — শিশু উত্তেজিত, তাই ধীর রাখতে হবে।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ء — নিজে বলে, দুবার।",
            "correction": S(
                "Stop the air, then let it go.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "That's it! Try once more.",
            ),
            "note": "শেষ চারটির মধ্যে ء সবচেয়ে কঠিন — কাছাকাছি হলেই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Now You",
                      "arabic": "ء",
                      "text": "🎤 Your turn!"},
        },
        {
            "section": "ي — Look and listen",
            "says": S(
                "Smile wide for this one. Look!",
                DOTS,
                "[ي হরফটি দেখিয়ে তার নাম বলুন, মুখ স্পষ্ট রাখুন]",
                "",
                "Watch my mouth again.",
                DOTS,
                "[আবার বলুন, ধীরে]",
            ),
            "does": "ক্যামেরার কাছে মুখ আনুন, দুবার বলুন। মাখরাজ: জিহ্বার মাঝখান উপরে — ঠোঁট প্রসারিত।",
            "student": "মুখের দিকে তাকিয়ে শোনে।",
            "expected": "ي — মুখের নড়াচড়ায় চোখ।",
            "correction": S(
                "Come closer to the screen and watch.",
                DOTS,
                "[ধীরে, স্পষ্ট করে বলুন]",
                "",
                "One more look, then you try.",
            ),
            "note": "মাখরাজ: জিহ্বার মাঝখান উপরে — ঠোঁট প্রসারিত।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Look And Listen",
                      "arabic": "ي",
                      "text": "😄 A wide smile."},
        },
        {
            "section": "ي — Now you",
            "says": S(
                "Your go. Big smile first.",
                DOTS,
                "[হরফটির নাম বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Yes! Once more, nice and clear.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah! Another one done.",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, অন্তত তিন সেকেন্ড। আজ শেষ "
                    "দারস — শিশু উত্তেজিত, তাই ধীর রাখতে হবে।",
            "student": "হরফটির নাম নিজে বলে।",
            "expected": "ي — নিজে বলে, দুবার।",
            "correction": S(
                "Wider smile. Show your teeth.",
                DOTS,
                "[করে দেখান, শিশুকে নকল করতে দিন]",
                "",
                "That's it! Try once more.",
            ),
            "note": "শেষ চারটির মধ্যে ء সবচেয়ে কঠিন — কাছাকাছি হলেই যথেষ্ট।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Now You",
                      "arabic": "ي",
                      "text": "🎤 Your turn!"},
        },
        {
            "section": "The four together",
            "says": S(
                "All four now. Watch me point.",
                DOTS,
                "[চারটি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "Again, together this time.",
                DOTS,
                "[আবার, একসাথে]",
                "",
                "Lovely. That's all four.",
            ),
            "does": "চারটিতে আঙুল রাখুন, দুবার। ছোট দল বলে দ্রুত হয়ে যাবে — "
                    "তাই ধীরে ও স্পষ্ট করে বলুন।",
            "student": "সাথে পড়ে।",
            "expected": "و ه ء ي — চারটি ঠিক ক্রমে।",
            "correction": S(
                "Slower. From the first one again.",
                DOTS,
                "[প্রথমটির নাম ধীরে বলুন]",
                "",
                "Good, keep going!",
            ),
            "note": "চারটি ছোট দল — এখানেই পাকা করে নিলে পরেরটা সহজ হয়।",
            "seconds": 50,
            "slide": {"kind": "repeat", "heading": "All Four",
                      "arabic": "و  ه  ء  ي",
                      "text": "🎤 Together now."},
        },
        {
            "section": "Which one? — the last four",
            "says": S(
                "Quick test! I'll say one. You point.",
                DOTS,
                "[একটি হরফের নাম বলুন]",
                DOTS,
                "[আরেকটি, এলোমেলো ক্রমে]",
                DOTS,
                "[আরও দুটি]",
                "",
                "All correct! You know them already.",
            ),
            "does": "এলোমেলো ক্রমে দ্রুত বলুন। ভুল হলে হেসে আবার বলুন — এটা "
                    "খেলা, পরীক্ষা নয়।",
            "student": "নাম শুনে হরফটি দেখায়।",
            "expected": "চারটিতেই সঠিক আঙুল।",
            "correction": S(
                "Listen again, slowly.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Now find it. No hurry.",
            ),
            "note": "শোনা থেকে চেনা — পড়ার আসল ভিত্তি।",
            "seconds": 55,
            "slide": {"kind": "question", "heading": "Point To It",
                      "arabic": "و      ه      ء      ي",
                      "text": "👉 Which one did I say?"},
        },
        {
            "section": "All twenty-nine",
            "says": S(
                "Now the big one. Sit up straight.",
                "Twenty-nine letters. The whole alphabet.",
                "We'll go slowly, together. Ready?",
                DOTS,
                "[উনত্রিশটি হরফে একে একে আঙুল রেখে নাম বলুন]",
                "",
                "Allahu Akbar! You said them all.",
                "Every single letter of the Qur'an.",
            ),
            "does": "⚠️ আজকের সবচেয়ে বড় মুহূর্ত। ধীরে যান, পাঁচ ভাগে ভাগ "
                    "করুন। শেষে থেমে শিশুর মুখের দিকে তাকান — এই মুহূর্তটা "
                    "সে মনে রাখবে। তাড়াহুড়ো করে নষ্ট করবেন না।",
            "student": "উনত্রিশটি হরফ সাথে পড়ে।",
            "expected": "ا থেকে ي পর্যন্ত পুরো বর্ণমালা।",
            "correction": S(
                "That's a lot in one go. Let's split it.",
                DOTS,
                "[প্রথম সাতটি, তারপর ছয় ছয় করে]",
                "",
                "See? You knew them all along.",
            ),
            "note": "এক নিঃশ্বাসে না পারলেও চলে — ভাগে ভাগে পারলেই যথেষ্ট।",
            "seconds": 110,
            "slide": {"kind": "repeat", "heading": "The Whole Alphabet",
                      "arabic": "ا ب ت ث ج ح خ\nد ذ ر ز س ش\nص ض ط ظ ع غ\nف ق ك ل م ن\nو ه ء ي",
                      "text": "🏆 Twenty-nine letters!"},
        },
        {
            "section": "Celebrate",
            "says": S(
                "Stop. Look at me for a moment.",
                "[অপেক্ষা করুন]",
                "",
                "You know every letter of the Qur'an now.",
                "Every single one. Say it with me —",
                "I know all the letters!",
                "[একসাথে বলুন]",
                "",
                "Alhamdulillah. I'm so happy for you.",
            ),
            "does": "⚠️ এই ধাপে কোনো শেখানো নেই — কেবল উদযাপন। থামুন, চোখে "
                    "তাকান, ধীরে বলুন। অভিভাবক পাশে থাকলে তাঁকেও ডাকুন। "
                    "এই মুহূর্তটাই শিশু বাড়ি নিয়ে যাবে।",
            "student": "সাথে বলে, হাসে।",
            "expected": "I know all the letters!",
            "correction": S(
                "Say it loud. You earned it!",
                "[আবার একসাথে বলুন]",
            ),
            "note": "পাঁচ দারসের পরিশ্রমের স্বীকৃতি — এটা বাদ দেবেন না।",
            "seconds": 60,
            "slide": {"kind": "praise", "heading": "You Did It!",
                      "arabic": "ٱلْحَمْدُ لِلَّٰهِ",
                      "text": "🏆 All 29 letters — yours!"},
        },
        {
            "section": "Writing — last time",
            "says": S(
                "Notebook out. Last four to write!",
                "[অপেক্ষা করুন — খাতা ও পেনসিল আনতে দিন]",
                "",
                "Pencil ready? Right side first.",
                "[অপেক্ষা করুন]",
            ),
            "does": "পঞ্চম দারস — শিশু এখন অভ্যস্ত। ছোট করে বলুন, সময় নষ্ট "
                    "করবেন না; আজ লেখার পরে আরও কিছু আছে।",
            "student": "খাতা ও পেনসিল আনে।",
            "expected": "খাতা খোলা, পেনসিল হাতে।",
            "correction": S(
                "No notebook? Any paper is fine.",
                "Go get it quickly. I'll wait.",
                "[অপেক্ষা করুন]",
            ),
            "note": "খাতা না থাকলে যেকোনো কাগজেই চলবে।",
            "seconds": 35,
            "slide": {"kind": "write", "heading": "Last Four To Write",
                      "arabic": "و  ه  ء  ي",
                      "text": "✏️ Right side first!"},
        },
        {
            "section": "Writing — و ه ء ي",
            "says": S(
                "Four letters. One line each.",
                DOTS,
                "[চারটি হরফের নাম একে একে বলুন]",
                "",
                "This little one is the smallest of all.",
                "[ء হরফটি দেখিয়ে দিন]",
                "",
                "Take your time. I'm right here.",
                "[অপেক্ষা করুন — ৫০ সেকেন্ড সময় দিন]",
                "",
                "Hold it up! Let me see.",
            ),
            "does": "লেখার সময় চুপ থাকুন। ء সবচেয়ে ছোট — শিশু প্রায়ই ভুলে "
                    "যায় বা বড় করে ফেলে। আগেই দেখিয়ে দিন।",
            "student": "চারটি হরফ লেখে, দেখায়।",
            "expected": "খাতায় و ه ء ي।",
            "correction": S(
                "Nice! Make this one smaller.",
                "[ء দেখিয়ে দিন]",
                "",
                "Yes, tiny like that.",
            ),
            "note": "⚠️ হাতের লেখা নিখুঁত হওয়ার দরকার নেই। পাঁচ দারস ধরে "
                    "পেনসিল চলছে — সেটাই বড় অর্জন।",
            "seconds": 90,
            "slide": {"kind": "write", "heading": "Write The Last Four",
                      "arabic": "و  ه  ء  ي",
                      "text": "✏️ One line each."},
        },
        {
            "section": "Writing — the finished page",
            "says": S(
                "Page up, please! Let me see.",
                "[খাতাটি ক্যামেরার সামনে ধরতে বলুন]",
                "",
                "MashaAllah! Look at that page.",
                "Five lessons ago you had never written Arabic.",
                "Look at you now.",
            ),
            "does": "⚠️ শেষ দিন — খাতার দিকে সত্যিই তাকান, সময় নিন। প্রথম "
                    "দিনের কথা মনে করিয়ে দিন। অভিভাবককেও দেখান।",
            "student": "পুরো পাতা ক্যামেরায় দেখায়।",
            "expected": "চারটি হরফ লেখা একটি পাতা।",
            "correction": S(
                "Even two is fine. You wrote today.",
                "Five lessons, every single time.",
                "That's what I'm proud of.",
            ),
            "note": "কতদূর এসেছে সেটা মনে করিয়ে দিলে শিশু নিজের পরিশ্রম "
                    "বুঝতে পারে।",
            "seconds": 50,
            "slide": {"kind": "write", "heading": "Your Finished Page",
                      "arabic": "و  ه  ء  ي",
                      "text": "📓 Five lessons of writing!"},
        },
        {
            "section": "What comes next",
            "says": S(
                "So, what now? Something exciting.",
                "Letters like to hold hands!",
                "[দুই হাত জোড়া করে দেখান]",
                "",
                "Next time we join them into words.",
                "And then — you'll read the Qur'an.",
                "Really read it, by yourself.",
            ),
            "does": "⚠️ পরের ধাপের দরজা খুলে দিন। 'হাত ধরাধরি' — হরফ জোড়া "
                    "লাগানোর এই ছবিটা শিশু সহজে বোঝে। হাত দিয়ে করে দেখান।",
            "student": "শোনে, আগ্রহ পায়।",
            "expected": "উৎসাহ নিয়ে শোনে।",
            "correction": S(
                "Like this — two letters, holding hands.",
                "[হাত জোড়া করে দেখান]",
                "",
                "That makes a word!",
            ),
            "note": "শেষ দারসেই পরেরটির আগ্রহ তৈরি করা — নইলে শিশু ভাবে "
                    "সব শেষ হয়ে গেছে।",
            "seconds": 50,
            "slide": {"kind": "reminder", "heading": "Letters Hold Hands",
                      "arabic": "بَ  بِ  بُ",
                      "text": "🤝 Next: making words!"},
        },
        {
            "section": "Homework",
            "says": S(
                "One last homework. A special one.",
                "Say all twenty-nine letters, once a day.",
                "To your mother, or your father.",
                "Let them hear what you can do!",
                "[অপেক্ষা করুন]",
                "",
                "Shukran. They'll be so proud.",
            ),
            "does": "⚠️ অভিভাবককে শোনানোর কথাটা আলাদা — শিশু গর্ব পায়, আর "
                    "বাড়িতেও অনুশীলন হয়। ধীরে বলুন যাতে অভিভাবক শোনেন।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": S(
                "Just once a day. To anyone at home.",
                "They'll love hearing it.",
            ),
            "note": "অভিভাবকের জন্য — শুনুন আর প্রশংসা করুন। ভুল ধরতে "
                    "যাবেন না, উস্তাদের জন্য রেখে দিন।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Show Them At Home",
                      "arabic": "ا ب ت ث ج ح خ\nد ذ ر ز س ش\nص ض ط ظ ع غ\nف ق ك ل م ن\nو ه ء ي",
                      "text": "📖 Say all 29 to your family!"},
        },
        {
            "section": "Closing",
            "says": S(
                "Twenty-nine letters. Five lessons. One student.",
                "Baraka Allahu fik, my dear student.",
                "Next time we start joining them. Get ready!",
                "Assalamu alaikum wa rahmatullah!",
            ),
            "does": "হাসুন, হাত নাড়ুন। শেষ দারস — একটু বেশি সময় নিন বিদায়ে। "
                    "পরের দারসের কথা বলে শেষ করুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "Assalamu alaikum! Say it back to me.",
                "[অপেক্ষা করুন]",
                "",
                "See you next time, in shaa Allah!",
            ),
            "note": "মিলিয়ে নিন: পঁচিশটি ঝালাই হয়েছে · শেষ চারটি শোনা ও বলা "
                    "হয়েছে · এলোমেলো ক্রমে চেনা হয়েছে · উনত্রিশটি একসাথে বলা "
                    "হয়েছে · উদযাপন হয়েছে · খাতায় লিখেছে ও দেখিয়েছে · পরের "
                    "ধাপের কথা বলা হয়েছে।",
            "seconds": 35,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "👋 Next: joining letters!"},
        },
    ],
}


# ═══════════════ সূরা আল-কাউসার ═══════════════
# ⚠️ ইখলাসের দারসের নকল নয়। ইখলাস শুরু হয় সালাম ও পরিচয়ে, ধাপে ধাপে
# শোনা-বলা-জোড়া দিয়ে। এটি শুরু হয় একটি গল্প দিয়ে — জান্নাতের নদী।
# পাঁচ বছরের শিশু গল্পে যত মনোযোগ দেয়, নিয়মে তত নয়; তাই আজকের সুতোই
# গল্প, আর আয়াতগুলো সেই গল্পেরই অংশ হয়ে আসে।
K1 = "إِنَّآ أَعْطَيْنَٰكَ ٱلْكَوْثَرَ ۝١"
K2 = "فَصَلِّ لِرَبِّكَ وَٱنْحَرْ ۝٢"
K3 = "إِنَّ شَانِئَكَ هُوَ ٱلْأَبْتَرُ ۝٣"

KAWTHAR = {
    "title": "Surah Al-Kawthar",
    "title_ar": "الكوثر",
    "kind": "memorization",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 21,
    "objectives": (
        "<p><b>Surah Al-Kawthar — Teacher Script</b><br>"
        "Age 5-7 · about 21 minutes · The shortest Surah, only three "
        "verses<br>"
        "A story &rarr; Listen &rarr; Say &rarr; Meaning &rarr; All "
        "together</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause and what to show.</li>"
        "<li>Where you see <b>…………</b>, recite the Arabic shown on the "
        "screen. Arabic is never written in English letters.</li>"
        "</ul>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Recite all three verses of Surah Al-Kawthar from memory</li>"
        "<li>Tell you what Al-Kawthar is, in their own words</li>"
        "<li>Know that this is the shortest Surah in the Qur'an</li>"
        "<li>Say it in their own Salah</li>"
        "</ul>"
    ),
    "steps": [
        {
            "section": "Part 1 — A story first",
            "says": S(
                "Assalamu alaikum! Sit close. I have a story.",
                "[অপেক্ষা করুন — শিশু কাছে আসবে]",
                "",
                "In Jannah there's a river.",
                "Whiter than milk. Sweeter than honey.",
                "Allah gave it to our Prophet ﷺ as a gift.",
                "Would you like to know its name?",
                "[অপেক্ষা করুন]",
            ),
            "does": "⚠️ আজ গল্প দিয়েই শুরু — নিয়ম দিয়ে নয়। গলা নিচু করে, "
                    "ধীরে বলুন, যেন সত্যিই গল্প শোনাচ্ছেন। শিশু সামনে ঝুঁকে "
                    "এলে বুঝবেন ধরেছে।",
            "student": "শোনে, আগ্রহ নিয়ে তাকায়।",
            "expected": "Yes!",
            "correction": S(
                "A river in Jannah. Just for our Prophet ﷺ.",
                "Can you imagine it?",
                "[অপেক্ষা করুন]",
            ),
            "note": "কাউসার একটি নদী — হাদীসে বর্ণিত (বুখারী, মুসলিম)। "
                    "গল্পটা সত্যি, তাই বলতে দ্বিধা নেই।",
            "seconds": 60,
            "slide": {"kind": "title", "heading": "A River In Jannah",
                      "arabic": "الكوثر",
                      "text": "🌊 Whiter than milk.\n🍯 Sweeter than honey."},
        },
        {
            "section": "Part 1 — Its name",
            "says": S(
                "Its name is on the screen. Look.",
                DOTS,
                "[সূরার নামটি বলুন]",
                "",
                "Say it with me.",
                DOTS,
                "[একসাথে বলুন]",
                "",
                "Beautiful! And there's a whole Surah about it.",
            ),
            "does": "নামটি দুবার বলুন — একবার আপনি, একবার একসাথে। শিশু নাম "
                    "বলতে পারলেই গল্পটা তার নিজের হয়ে যায়।",
            "student": "সূরার নাম বলে।",
            "expected": "الكوثر — নামটি বলে।",
            "correction": S(
                "Listen once more, then you try.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Yes! That's it.",
            ),
            "note": "নাম জানা মানে সূরাটার সাথে পরিচয় হওয়া — শুধু মুখস্থ নয়।",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Its Name",
                      "arabic": "ٱلْكَوْثَر",
                      "text": "🏷️ The name of the river."},
        },
        {
            "section": "Part 1 — The shortest one",
            "says": S(
                "Now something amazing. Count with me.",
                "One… two… three.",
                "[তিনটি আঙুল দেখান]",
                "",
                "Three verses. That's all!",
                "This is the shortest Surah in the whole Qur'an.",
                "You'll learn all of it today.",
            ),
            "does": "তিনটি আঙুল দেখিয়ে গুনুন। 'সবচেয়ে ছোট' কথাটা শিশুর "
                    "আত্মবিশ্বাস বাড়ায় — কাজটা সম্ভব মনে হয়।",
            "student": "সাথে গোনে, তিনটি আঙুল দেখায়।",
            "expected": "One, two, three.",
            "correction": S(
                "Show me three fingers. Like this.",
                "[তিনটি আঙুল দেখান]",
                "",
                "Three little verses. Easy!",
            ),
            "note": "'সবচেয়ে ছোট' — সত্যি, আর শিশুর ভয় কাটানোর সবচেয়ে সহজ "
                    "কথা এটাই।",
            "seconds": 45,
            "slide": {"kind": "title", "heading": "Only Three Verses",
                      "arabic": "١  ٢  ٣",
                      "text": "🤏 The shortest Surah!"},
        },
        {
            "section": "Part 2 — Just listen",
            "says": S(
                "Now close your lips and just listen.",
                "Don't say anything yet. Only listen.",
                DOTS,
                "[পুরো সূরাটি ধীরে, সুন্দর করে তিলাওয়াত করুন]",
                "",
                "Wasn't that beautiful?",
            ),
            "does": "⚠️ শিশুকে বলতে দেবেন না এখনো। প্রথমে কানে বসুক। ধীরে ও "
                    "সুন্দর করে পড়ুন — আপনার সুরই সে নকল করবে।",
            "student": "চুপ করে শোনে।",
            "expected": "চুপ থাকে, মন দিয়ে শোনে।",
            "correction": S(
                "Shh — just listening now. Your turn comes soon.",
                DOTS,
                "[আবার পড়ুন]",
            ),
            "note": "শোনা ছাড়া নকল হয় না — এই ধাপটা তাড়াহুড়ো করবেন না।",
            "seconds": 50,
            "slide": {"kind": "listen", "heading": "Listen",
                      "arabic": K1 + "\n" + K2 + "\n" + K3,
                      "text": "👂 Just listen."},
        },
        {
            "section": "Part 3 — إِنَّآ",
            "says": S(
                "Now the first little piece. After me.",
                DOTS,
                "[টুকরোটি বলুন, তারপর অপেক্ষা করুন]",
                "",
                "Again, a little clearer.",
                DOTS,
                "[আবার — শিশুকে বলতে দিন]",
                "",
                "MashaAllah!",
            ),
            "does": "⚠️ বলার পর সত্যিই থামুন, তিন সেকেন্ড। ছোট টুকরো — তাই "
                    "শিশু সহজেই পারবে, পারলেই প্রশংসা করুন।",
            "student": "টুকরোটি বলে।",
            "expected": "إِنَّآ — নিজে বলে।",
            "correction": S(
                "Listen once more. Just this bit.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Good! Try again.",
            ),
            "note": "শাদ্দা স্পষ্ট রাখুন — إِنَّآ-তে নূনে জোর।",
            "seconds": 45,
            "slide": {"kind": "verse", "heading": "Say it with me",
                      "arabic": "إِنَّآ", "text": "🎤"},
        },
        {
            "section": "Part 3 — أَعْطَيْنَٰكَ",
            "says": S(
                "Next piece. This one is a bit longer.",
                DOTS,
                "[টুকরোটি ধীরে বলুন]",
                "",
                "Take your time. Now you.",
                DOTS,
                "[অপেক্ষা করুন]",
                "",
                "You've got it!",
            ),
            "does": "এটি আজকের সবচেয়ে লম্বা টুকরো — ধীরে বলুন, দরকার হলে "
                    "দুই ভাগে ভেঙে দিন।",
            "student": "টুকরোটি বলে।",
            "expected": "أَعْطَيْنَٰكَ — নিজে বলে।",
            "correction": S(
                "Let's take it slowly, bit by bit.",
                DOTS,
                "[ধীরে, ভেঙে ভেঙে বলুন]",
                "",
                "There! Much better.",
            ),
            "note": "লম্বা টুকরোয় আটকালে ভেঙে দিন — এক সাথে না পারলেও চলে।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Say it with me",
                      "arabic": "أَعْطَيْنَٰكَ", "text": "🎤"},
        },
        {
            "section": "Part 3 — ٱلْكَوْثَرَ",
            "says": S(
                "And now our river's name again.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "You already know this one!",
                DOTS,
                "[আবার, একসাথে]",
                "",
                "Lovely.",
            ),
            "does": "নামটা সে আগেই শিখেছে — মনে করিয়ে দিলে আত্মবিশ্বাস বাড়ে। "
                    "'তুমি তো এটা জানোই' বলুন।",
            "student": "টুকরোটি বলে।",
            "expected": "ٱلْكَوْثَرَ — নিজে বলে।",
            "correction": S(
                "Remember the river? Same word.",
                DOTS,
                "[বলুন]",
                "",
                "Yes! You knew it.",
            ),
            "note": "আগে শেখা জিনিস ফিরে এলে শিশু নিজেকে সফল মনে করে।",
            "seconds": 40,
            "slide": {"kind": "verse", "heading": "Say it with me",
                      "arabic": "ٱلْكَوْثَرَ", "text": "🎤"},
        },
        {
            "section": "Part 3 — Join verse 1",
            "says": S(
                "Three pieces. Now join them together!",
                DOTS,
                "[পুরো ১ম আয়াতটি বলুন]",
                "",
                "All together now.",
                DOTS,
                "[একসাথে বলুন]",
                "",
                "SubhanAllah! Your first verse.",
            ),
            "does": "জোড়া লাগানোর মুহূর্তটাই সবচেয়ে আনন্দের — খুশি হয়ে "
                    "প্রশংসা করুন। দুবার বলুন।",
            "student": "পুরো আয়াতটি বলে।",
            "expected": "إِنَّآ أَعْطَيْنَٰكَ ٱلْكَوْثَرَ",
            "correction": S(
                "Let's join just two pieces first.",
                DOTS,
                "[প্রথম দুটি জুড়ে বলুন]",
                "",
                "Now add the last one.",
            ),
            "note": "আটকালে দুটি টুকরো জুড়ুন, তারপর তৃতীয়টি — ভাগে ভাগে সহজ।",
            "seconds": 55,
            "slide": {"kind": "verse", "heading": "Verse 1",
                      "arabic": K1, "text": "🎤 All together now"},
        },
        {
            "section": "Part 4 — What it means",
            "says": S(
                "Now, what does it mean? Listen.",
                "Allah says: I have given you Al-Kawthar.",
                "Given! It's a gift.",
                "Allah gave our Prophet ﷺ that beautiful river.",
                "Isn't Allah kind?",
                "[অপেক্ষা করুন]",
            ),
            "does": "'উপহার' কথাটায় জোর দিন — শিশু উপহার বোঝে, আর আল্লাহর "
                    "দয়া বোঝানোর এটাই সহজ পথ।",
            "student": "শোনে, উত্তর দেয়।",
            "expected": "Yes!",
            "correction": S(
                "A gift, from Allah. Just like a present.",
                "For our Prophet ﷺ.",
            ),
            "note": "অর্থ শেখানো মুখস্থের অংশ — বুঝলে মনে থাকে বেশি।",
            "seconds": 55,
            "slide": {"kind": "meaning", "heading": "A Gift From Allah",
                      "arabic": K1,
                      "text": "🎁 I have given you Al-Kawthar."},
        },
        {
            "section": "Part 5 — فَصَلِّ لِرَبِّكَ",
            "says": S(
                "Verse two. First piece, after me.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Once more, nice and clear.",
                DOTS,
                "[অপেক্ষা করুন]",
                "",
                "Excellent!",
            ),
            "does": "লাম-এ শাদ্দা স্পষ্ট রাখুন — فَصَلِّ। ধীরে বলুন।",
            "student": "টুকরোটি বলে।",
            "expected": "فَصَلِّ لِرَبِّكَ — নিজে বলে।",
            "correction": S(
                "Listen to my mouth. Slowly.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Better! One more go.",
            ),
            "note": "শাদ্দা — জোর দিয়ে ধরে রাখা। শিশু না পারলে ছাড় দিন।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Say it with me",
                      "arabic": "فَصَلِّ لِرَبِّكَ", "text": "🎤"},
        },
        {
            "section": "Part 5 — وَٱنْحَرْ",
            "says": S(
                "And the last piece of verse two.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Your turn now.",
                DOTS,
                "[অপেক্ষা করুন]",
                "",
                "MashaAllah!",
            ),
            "does": "ছোট টুকরো — দুবার বললেই শিশু ধরে ফেলবে।",
            "student": "টুকরোটি বলে।",
            "expected": "وَٱنْحَرْ — নিজে বলে।",
            "correction": S(
                "Short one. Just after me.",
                DOTS,
                "[বলুন]",
                "",
                "That's it!",
            ),
            "note": "ছোট টুকরোয় দ্রুত সফলতা আসে — উৎসাহ ধরে রাখে।",
            "seconds": 40,
            "slide": {"kind": "verse", "heading": "Say it with me",
                      "arabic": "وَٱنْحَرْ", "text": "🎤"},
        },
        {
            "section": "Part 5 — Join verse 2",
            "says": S(
                "Join them. Two pieces make verse two.",
                DOTS,
                "[পুরো ২য় আয়াতটি বলুন]",
                "",
                "Together now.",
                DOTS,
                "[একসাথে]",
                "",
                "Two verses done!",
            ),
            "does": "দুবার বলুন। 'দুইটা হয়ে গেছে' — গোনাটা মনে করিয়ে দিন।",
            "student": "পুরো আয়াতটি বলে।",
            "expected": "فَصَلِّ لِرَبِّكَ وَٱنْحَرْ",
            "correction": S(
                "Slowly. First piece, then the second.",
                DOTS,
                "[ভেঙে বলুন]",
                "",
                "Good, now together.",
            ),
            "note": "প্রতিটি আয়াত শেষে গুনে দেখান — অগ্রগতি চোখে পড়ে।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 2",
                      "arabic": K2, "text": "🎤 All together now"},
        },
        {
            "section": "Part 6 — Pray and give",
            "says": S(
                "What does verse two mean? Two things.",
                "Pray to your Lord. That's Salah!",
                "And give. Share with others.",
                "Allah gave us so much. So we pray, and we give.",
                "Can you do those two?",
                "[অপেক্ষা করুন]",
            ),
            "does": "দুটি কাজ আঙুলে গুনে দেখান — নামায ও দান। শিশু দুটোই "
                    "চেনে, তাই বোঝা সহজ।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": S(
                "Two things. Pray… and give.",
                "[দুটি আঙুল দেখান]",
                "",
                "You can do both!",
            ),
            "note": "নাহর মানে কুরবানী — শিশুকে 'দেওয়া/ভাগ করা' বললেই যথেষ্ট।",
            "seconds": 55,
            "slide": {"kind": "question", "heading": "Two Things",
                      "arabic": K2,
                      "text": "🤲 Pray to your Lord.\n🎁 And give."},
        },
        {
            "section": "Part 7 — Verses 1 and 2",
            "says": S(
                "Let's put verse one and two together.",
                DOTS,
                "[দুটি আয়াত পরপর বলুন]",
                "",
                "Now with me.",
                DOTS,
                "[একসাথে]",
                "",
                "Beautiful. Only one left!",
            ),
            "does": "ধীরে যান। শেষে 'আর মাত্র একটা বাকি' বলুন — শিশু "
                    "শেষটুকুর জন্য উৎসাহ পায়।",
            "student": "দুটি আয়াত সাথে বলে।",
            "expected": "১ম ও ২য় আয়াত পরপর।",
            "correction": S(
                "One verse at a time. Verse one first.",
                DOTS,
                "[১ম আয়াত]",
                "",
                "Now verse two.",
            ),
            "note": "জোড়া লাগানোই মুখস্থের আসল কাজ — বারবার করুন।",
            "seconds": 55,
            "slide": {"kind": "repeat", "heading": "Verses 1 and 2",
                      "arabic": K1 + "\n" + K2, "text": "🎤 Together now"},
        },
        {
            "section": "Part 8 — إِنَّ شَانِئَكَ",
            "says": S(
                "The last verse! First piece.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Now you say it.",
                DOTS,
                "[অপেক্ষা করুন]",
                "",
                "Very good!",
            ),
            "does": "হামযা স্পষ্ট রাখুন — شَانِئَكَ। ধীরে বলুন, শিশু নকল করবে।",
            "student": "টুকরোটি বলে।",
            "expected": "إِنَّ شَانِئَكَ — নিজে বলে।",
            "correction": S(
                "Watch my mouth. Listen again.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Closer! Once more.",
            ),
            "note": "হামযা ছোট থেমে যাওয়ার মতো — কাছাকাছি হলেই যথেষ্ট।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Say it with me",
                      "arabic": "إِنَّ شَانِئَكَ", "text": "🎤"},
        },
        {
            "section": "Part 8 — هُوَ ٱلْأَبْتَرُ",
            "says": S(
                "And the very last piece of all.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Say it with me.",
                DOTS,
                "[একসাথে]",
                "",
                "That's the whole Surah, nearly!",
            ),
            "does": "'একদম শেষ টুকরো' বলুন — শিশু বুঝলে শেষ টানটা দিতে চায়।",
            "student": "টুকরোটি বলে।",
            "expected": "هُوَ ٱلْأَبْتَرُ — নিজে বলে।",
            "correction": S(
                "Almost! Listen one more time.",
                DOTS,
                "[বলুন]",
                "",
                "Yes, just like that.",
            ),
            "note": "শেষ টুকরোয় ক্লান্তি আসতে পারে — ছোট রাখুন, দ্রুত শেষ করুন।",
            "seconds": 45,
            "slide": {"kind": "verse", "heading": "Say it with me",
                      "arabic": "هُوَ ٱلْأَبْتَرُ", "text": "🎤"},
        },
        {
            "section": "Part 8 — Join verse 3",
            "says": S(
                "Join them. Your third verse!",
                DOTS,
                "[পুরো ৩য় আয়াতটি বলুন]",
                "",
                "Together.",
                DOTS,
                "[একসাথে]",
                "",
                "All three verses. MashaAllah!",
            ),
            "does": "দুবার বলুন। শেষে থেমে শিশুর মুখের দিকে তাকান — সে "
                    "বুঝুক যে বড় কিছু হয়ে গেল।",
            "student": "পুরো আয়াতটি বলে।",
            "expected": "إِنَّ شَانِئَكَ هُوَ ٱلْأَبْتَرُ",
            "correction": S(
                "Two pieces. First one, then the next.",
                DOTS,
                "[ভেঙে বলুন]",
                "",
                "Now join them.",
            ),
            "note": "তিনটি আয়াতই হয়ে গেল — এই মুহূর্তটা উদযাপন করুন।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 3",
                      "arabic": K3, "text": "🎤 All together now"},
        },
        {
            "section": "Part 9 — What it means",
            "says": S(
                "The last verse means something strong.",
                "Anyone who hates our Prophet ﷺ —",
                "that person is the one who loses.",
                "Not our Prophet ﷺ. Never him.",
                "Allah takes care of the people He loves.",
            ),
            "does": "শান্তভাবে বলুন, ভয় দেখিয়ে নয়। মূল কথা — আল্লাহ তাঁর "
                    "প্রিয়জনদের রক্ষা করেন। শিশুর মনে নিরাপত্তার অনুভূতি "
                    "থাকুক।",
            "student": "শোনে।",
            "expected": "মন দিয়ে শোনে।",
            "correction": S(
                "Allah looks after our Prophet ﷺ.",
                "Always. That's the meaning.",
            ),
            "note": "⚠️ এই আয়াতের অর্থ ভয়ের নয়, আশ্বাসের — সেভাবেই বলুন।",
            "seconds": 50,
            "slide": {"kind": "question", "heading": "Allah Protects",
                      "arabic": K3,
                      "text": "💚 Allah takes care of His Prophet ﷺ."},
        },
        {
            "section": "Part 10 — All three",
            "says": S(
                "Now the whole Surah. From the start.",
                DOTS,
                "[তিনটি আয়াত ধীরে পরপর বলুন]",
                "",
                "One more time, together.",
                DOTS,
                "[একসাথে]",
                "",
                "Allahu Akbar! You learned a Surah today.",
            ),
            "does": "⚠️ আজকের সবচেয়ে বড় মুহূর্ত। ধীরে যান, আটকালে সেই "
                    "আয়াতটুকু বলে দিয়ে এগিয়ে যান — থামবেন না।",
            "student": "তিনটি আয়াত সাথে বলে।",
            "expected": "পুরো সূরা, শুরু থেকে শেষ।",
            "correction": S(
                "One verse at a time. I'll start.",
                DOTS,
                "[১ম আয়াত বলুন]",
                "",
                "Now you carry on.",
            ),
            "note": "এক নিঃশ্বাসে না পারলেও চলে — ভাগে ভাগে পারলেই যথেষ্ট।",
            "seconds": 70,
            "slide": {"kind": "repeat", "heading": "The Whole Surah",
                      "arabic": K1 + "\n" + K2 + "\n" + K3,
                      "text": "🎤 From the start."},
        },
        {
            "section": "Part 11 — Three-finger game",
            "says": S(
                "Game time! Hold up three fingers.",
                "[একসাথে তিনটি আঙুল তুলুন]",
                "",
                "Finger one — the gift.",
                "Finger two — pray and give.",
                "Finger three — Allah protects.",
                "Now you tell me. Finger one?",
                "[অপেক্ষা করুন]",
                "",
                "MashaAllah! You remember.",
            ),
            "does": "আঙুল ধরে ধরে অর্থ মনে করানো — শরীর ব্যবহার করলে শিশুর "
                    "মনে গেঁথে যায়। এলোমেলো ক্রমে জিজ্ঞেস করুন।",
            "student": "আঙুল ধরে অর্থ বলে।",
            "expected": "তিনটি অর্থই বলতে পারে।",
            "correction": S(
                "Finger one was the gift. The river!",
                "[একটি আঙুল দেখান]",
                "",
                "Now finger two?",
            ),
            "note": "অর্থ মনে রাখার সবচেয়ে সহজ পথ — হাতের সাথে জুড়ে দেওয়া।",
            "seconds": 60,
            "slide": {"kind": "activity", "heading": "Three Fingers",
                      "arabic": "١  ٢  ٣",
                      "text": "☝️ Gift\n✌️ Pray & give\n🤟 Allah protects"},
        },
        {
            "section": "Part 12 — Look and hide",
            "says": S(
                "Now I'll hide the words. Ready?",
                "[পর্দা খালি করুন]",
                "",
                "Can you say it without looking?",
                "Take your time. I'm listening.",
                "[অপেক্ষা করুন — সাহায্য করবেন না]",
                "",
                "SubhanAllah! From your heart.",
            ),
            "does": "⚠️ পর্দা খালি করে সত্যিই চুপ থাকুন। আটকে গেলে পাঁচ "
                    "সেকেন্ড অপেক্ষা করে তবেই প্রথম শব্দটা বলুন।",
            "student": "না দেখে বলার চেষ্টা করে।",
            "expected": "যতটুকু পারে, না দেখে।",
            "correction": S(
                "Stuck? Here's the first word.",
                DOTS,
                "[কেবল প্রথম শব্দটি বলুন]",
                "",
                "Now carry on. You know it.",
            ),
            "note": "না দেখে বলাই মুখস্থের আসল পরীক্ষা — একটু আটকালেও চলে।",
            "seconds": 60,
            "slide": {"kind": "blank", "heading": "Look & Hide",
                      "text": "🙈 Can you say it by heart?"},
        },
        {
            "section": "Part 13 — Where you'll say it",
            "says": S(
                "Here's the best part. You can use it!",
                "In your Salah, after Al-Fatiha.",
                "This little Surah, in your own prayer.",
                "Will you try it today?",
                "[অপেক্ষা করুন]",
                "",
                "I'll be so happy to hear that.",
            ),
            "does": "⚠️ শেখা জিনিস কোথায় কাজে লাগবে — এটা বলা জরুরি। নইলে "
                    "শিশুর কাছে মুখস্থ কেবল একটা কাজ, জীবনের অংশ নয়।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": S(
                "After Al-Fatiha, in your Salah.",
                "Just like the grown-ups do.",
            ),
            "note": "নামাযে ব্যবহার করা মানে সূরাটা সত্যিই তার নিজের হলো।",
            "seconds": 50,
            "slide": {"kind": "reminder", "heading": "Use It In Salah",
                      "arabic": "ٱلْفَاتِحَة ← ٱلْكَوْثَر",
                      "text": "🤲 After Al-Fatiha."},
        },
        {
            "section": "Part 14 — Well done",
            "says": S(
                "Come here. Look at me a moment.",
                "[অপেক্ষা করুন]",
                "",
                "Today you learned a whole Surah.",
                "Three verses, and what they mean.",
                "And you know about the river in Jannah.",
                "I'm proud of you.",
            ),
            "does": "⚠️ এই ধাপে কোনো শেখানো নেই — কেবল প্রশংসা। থামুন, চোখে "
                    "তাকিয়ে ধীরে বলুন। এই মুহূর্তটাই শিশু বাড়ি নিয়ে যাবে।",
            "student": "শোনে, হাসে।",
            "expected": "খুশি হয়, আত্মবিশ্বাস পায়।",
            "correction": S(
                "You worked hard today. I saw it.",
                "That's what matters most.",
            ),
            "note": "আলাদা প্রশংসার ধাপ — শেষ ভালো হলে পরের দিন সে আগ্রহ "
                    "নিয়ে আসে।",
            "seconds": 40,
            "slide": {"kind": "praise", "heading": "You Learned A Surah!",
                      "arabic": "أَحْسَنْتَ",
                      "text": "🌟 Three verses, all yours."},
        },
        {
            "section": "Part 15 — Homework",
            "says": S(
                "A small homework before next time.",
                "Say Surah Al-Kawthar three times a day.",
                "Three verses, three times. Easy!",
                "And tell someone at home about the river.",
                "[অপেক্ষা করুন]",
                "",
                "Shukran! They'll love that story.",
            ),
            "does": "বাড়ির কাজটা ধীরে বলুন, অভিভাবক শুনলে যেন লিখে নিতে "
                    "পারেন। গল্পটা বলার কাজটাও দিন — তাতে অর্থ পাকা হয়।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": S(
                "Just three times a day. One minute.",
                "You've already done the hard part!",
            ),
            "note": "অভিভাবকের জন্য — শুধু শুনুন আর হাসুন। ভুল হলে বাড়িতে "
                    "ঠিক করতে যাবেন না, উস্তাদের জন্য রেখে দিন।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Until Next Time",
                      "arabic": K1 + "\n" + K2 + "\n" + K3,
                      "text": "📖 Three times a day.\n🗣️ Tell the story at home."},
        },
        {
            "section": "Part 16 — Closing",
            "says": S(
                "The shortest Surah, and you know it all.",
                "Baraka Allahu fik, my dear student.",
                "See you next time, in shaa Allah!",
                "Assalamu alaikum wa rahmatullah!",
            ),
            "does": "হাসুন, হাত নাড়ুন। উষ্ণভাবে শেষ করুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "Assalamu alaikum! Say it back to me.",
                "[অপেক্ষা করুন]",
                "",
                "See you next time!",
            ),
            "note": "মিলিয়ে নিন: গল্প শুনেছে · পুরো সূরা শুনেছে · তিনটি আয়াত "
                    "টুকরো করে ও জুড়ে বলেছে · তিনটি অর্থ জেনেছে · না দেখে "
                    "বলার চেষ্টা করেছে · নামাযে ব্যবহারের কথা জেনেছে।",
            "seconds": 35,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "👋 See you next time!"},
        },
    ],
}

# ═══════════════ সূরা আন-নাস ═══════════════
# ⚠️ কাউসারের ছাঁচে নয়। কাউসার শুরু হয়েছিল গল্প দিয়ে (জান্নাতের নদী),
# আর এগোয় আয়াত ধরে ধরে। আন-নাসের নিজস্ব চাবি আছে: ٱلنَّاسِ শব্দটি ছয়
# আয়াতের প্রত্যেকটির শেষে ফিরে আসে। ৫-৭ বছরের শিশুর জন্য এটি সোনার
# খনি — একটি শব্দ শিখলেই ছয় আয়াতের শেষটুকু তার জানা হয়ে যায়।
#
# তাই এই দারস শুরু হয় ধাঁধা দিয়ে: "একটি শব্দ ছয়বার লুকিয়ে আছে, খুঁজে
# পাও কি?" শিশু নিজে আবিষ্কার করে — শোনানো হয় না।
N1 = "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ ۝١"
N2 = "مَلِكِ ٱلنَّاسِ ۝٢"
N3 = "إِلَٰهِ ٱلنَّاسِ ۝٣"
N4 = "مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ ۝٤"
N5 = "ٱلَّذِى يُوَسْوِسُ فِى صُدُورِ ٱلنَّاسِ ۝٥"
N6 = "مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ ۝٦"

NAS_ALL = "\n".join((N1, N2, N3, N4, N5, N6))
NAS_123 = "\n".join((N1, N2, N3))
NAS_456 = "\n".join((N4, N5, N6))

# টুকরোগুলো — আয়াত নয়, তাই কোনোটির শেষে আয়াত-নম্বর বসে না
W_NAS = "ٱلنَّاسِ"
W_QUL = "قُلْ أَعُوذُ"
W_RABB = "بِرَبِّ ٱلنَّاسِ"
W_SHARR = "مِن شَرِّ"
W_WASWAS = "ٱلْوَسْوَاسِ ٱلْخَنَّاسِ"
W_ALLADHI = "ٱلَّذِى يُوَسْوِسُ"
W_SUDUR = "فِى صُدُورِ ٱلنَّاسِ"
W_THREE = "رَبِّ · مَلِكِ · إِلَٰهِ"

NAS = {
    "title": "Surah An-Nas",
    "title_ar": "الناس",
    "kind": "memorization",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 26,
    "objectives": (
        "<p><b>Surah An-Nas — Teacher Script</b><br>"
        "Age 5-7 · about 26 minutes · Six verses, and one word that comes "
        "back in five of them<br>"
        "A puzzle &rarr; Find the word &rarr; Listen &rarr; Say &rarr; "
        "Meaning &rarr; The echo game</p>"
        "<p><b>How to use this script</b> — open it and read straight "
        "through. Every English line is what you say out loud, word for "
        "word. You never have to make up any English yourself.</p>"
        "<ul>"
        "<li>Bengali lines in [square brackets] are for you only — they "
        "tell you when to pause and what to show.</li>"
        "<li>Where you see <b>…………</b>, recite the Arabic shown on the "
        "screen. Arabic is never written in English letters.</li>"
        "</ul>"
        "<p><b>What makes this lesson different</b> — don't open with a "
        "story today. Open with a puzzle and let the child find the "
        "hidden word. The whole lesson hangs on that one discovery.</p>"
        "<p><b>By the end the student should be able to:</b></p>"
        "<ul>"
        "<li>Recite all six verses of Surah An-Nas from memory</li>"
        "<li>Point out the word that ends five of the six verses</li>"
        "<li>Say what it means to run to Allah for shelter</li>"
        "<li>Say it at bedtime and whenever they feel afraid</li>"
        "</ul>"
    ),
    "steps": [
        {
            "section": "Part 1 — A puzzle, not a story",
            "says": S(
                "Assalamu alaikum! No story today. Today we've got a puzzle.",
                "[অপেক্ষা করুন — শিশু কৌতূহলী হবে]",
                "",
                "There's one word hiding in our Surah.",
                "It hides five times. Five!",
                "Here it is. Look at the screen.",
                DOTS,
                "[পর্দার শব্দটি বলুন]",
            ),
            "does": "⚠️ আজ গল্প নয় — ধাঁধা। কাউসারে গল্প দিয়ে শুরু হয়েছিল, "
                    "আজ সেটি করবেন না। রহস্যের সুরে বলুন, চোখ বড় করুন। "
                    "শিশু নিজে খুঁজে পেলে শব্দটা তার নিজের হয়ে যায়।",
            "student": "পর্দার দিকে তাকায়, শব্দটি শোনে।",
            "expected": "শব্দটির দিকে তাকায়।",
            "correction": S(
                "Look here. Just this one word.",
                DOTS,
                "[আঙুল দিয়ে দেখান]",
            ),
            "note": "একটিমাত্র শব্দ দিয়ে শুরু — ছয় আয়াতের ভার একসাথে "
                    "চাপালে শিশু ভয় পায়। একটি শব্দ সে সহজেই ধরে ফেলে।",
            "seconds": 55,
            "slide": {"kind": "title", "heading": "One Word Hides Five Times",
                      "arabic": W_NAS,
                      "text": "🔍 Can you find it five times?"},
        },
        {
            "section": "Part 1 — What the word means",
            "says": S(
                "Say it with me.",
                DOTS,
                "[একসাথে বলুন]",
                "",
                "It means people.",
                "You're people. I'm people. Your Ammu, your Abbu.",
                "Everyone in the whole world.",
                "Now say it once more.",
                DOTS,
            ),
            "does": "নিজের দিকে, শিশুর দিকে, চারদিকে হাত দেখিয়ে বলুন — "
                    "তাতে 'মানুষ' কথাটা চোখে দেখা যায়। দুবার বলান।",
            "student": "শব্দটি বলে, অর্থ বোঝে।",
            "expected": "People — মানুষ।",
            "correction": S(
                "Listen once. Then you say it.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "That's it! People.",
            ),
            "note": "অর্থ আগে, মুখস্থ পরে — অর্থ জানা থাকলে শব্দটি মনে "
                    "থাকে বেশি দিন।",
            "seconds": 45,
            "slide": {"kind": "meaning", "heading": "It Means People",
                      "arabic": W_NAS,
                      "text": "👨‍👩‍👧 You. Me. Everyone."},
        },
        {
            "section": "Part 1 — Five times, six verses",
            "says": S(
                "Our Surah has six verses. Count with me.",
                "One, two, three, four, five, six.",
                "[আঙুল গুনে দেখান]",
                "",
                "Our word hides at the end of five of them.",
                "One verse is different. We'll hunt for it later!",
            ),
            "does": "ছয়টি আঙুল তুলে গুনুন, শিশুকেও গুনতে বলুন। এই ছক "
                    "বোঝা গেলে বাকি দারস অনেক সহজ হয়ে যায়।",
            "student": "ছয় পর্যন্ত গোনে।",
            "expected": "Six!",
            "correction": S(
                "Let's count again, slowly.",
                "One, two, three, four, five, six.",
                "[আঙুল ধরে গুনুন]",
            ),
            "note": "⚠️ ছয় আয়াতের পাঁচটি ٱلنَّاسِ দিয়ে শেষ — ১, ২, ৩, ৫ ও ৬। "
                    "৪ নম্বর আয়াত শেষ হয় ٱلْخَنَّاسِ দিয়ে, শুনতে প্রায় "
                    "একরকম হলেও শব্দটি আলাদা। কখনো বলবেন না "
                    "'প্রতিটি আয়াতে আছে' — সেটা ভুল শেখানো হবে।",
            "seconds": 50,
            "slide": {"kind": "title", "heading": "Six Verses",
                      "arabic": "١ ٢ ٣ ٤ ٥ ٦",
                      "text": "🔢 One word ends five of them."},
        },
        {
            "section": "Part 2 — Listen and catch it",
            "says": S(
                "Now I'll read the whole Surah.",
                "Your job is to catch our word.",
                "Put up one finger each time you hear it.",
                "[হাত তুলে দেখিয়ে দিন]",
                "",
                "Ready? Listen.",
                DOTS,
                "[পুরো সূরা ধীরে পড়ুন]",
                "",
                "How many fingers have you got?",
            ),
            "does": "⚠️ এটি নীরব শোনা নয় — শিশু হাত তুলে অংশ নেবে। ধীরে "
                    "পড়ুন, প্রতিবার ٱلنَّاسِ-এ একটু থামুন যেন সে ধরতে পারে। "
                    "পাঁচ আঙুল উঠলে খুব প্রশংসা করুন। ⚠️ ৪ নম্বর আয়াতে "
                    "শব্দটি নেই — সেখানে থামবেন না।",
            "student": "শোনে আর প্রতিবার আঙুল তোলে।",
            "expected": "Five fingers!",
            "correction": S(
                "Nearly! Let's listen once more together.",
                DOTS,
                "[আরও ধীরে পড়ুন, প্রতিবার থামুন]",
                "",
                "There! Did you catch them all?",
            ),
            "note": "কাউসারে প্রথম শোনাটা ছিল চুপচাপ। এখানে শিশু কাজ করতে "
                    "করতে শোনে — তাই মনোযোগ ধরে রাখা সহজ।",
            "seconds": 70,
            "slide": {"kind": "listen", "heading": "Catch The Word",
                      "arabic": NAS_ALL,
                      "text": "✋ One finger each time you hear it."},
        },
        {
            "section": "Part 3 — قُلْ أَعُوذُ",
            "says": S(
                "Now we build verse one. Two pieces.",
                "Here's the first piece. Listen.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Your turn.",
                DOTS,
            ),
            "does": "টুকরোটি দুবার বলুন, তারপর শিশুকে বলতে দিন। তাড়া "
                    "দেবেন না — সে নিজের গতিতে বলুক।",
            "student": "টুকরোটি বলে।",
            "expected": "قُلْ أَعُوذُ",
            "correction": S(
                "Almost there. Listen again.",
                DOTS,
                "[আরও ধীরে বলুন]",
                "",
                "Now you.",
                DOTS,
            ),
            "note": "টুকরো করে শেখানো — একবারে পুরো আয়াত দিলে শিশু আটকে যায়।",
            "seconds": 55,
            "slide": {"kind": "verse", "heading": "Verse 1 — First Piece",
                      "arabic": W_QUL, "text": "🎤 Say it after me."},
        },
        {
            "section": "Part 3 — بِرَبِّ ٱلنَّاسِ",
            "says": S(
                "Second piece. And look who's at the end!",
                "Our hidden word.",
                "Listen.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Your turn.",
                DOTS,
            ),
            "does": "শেষের ٱلنَّاسِ শব্দটি আঙুল দিয়ে দেখান — শিশু যেন "
                    "চিনতে পারে যে এটাই তার শেখা শব্দ।",
            "student": "টুকরোটি বলে, শেষের শব্দটি চিনে ফেলে।",
            "expected": "بِرَبِّ ٱلنَّاسِ",
            "correction": S(
                "You know the last bit already. Listen.",
                DOTS,
                "[শেষের শব্দে জোর দিন]",
                "",
                "Try once more.",
                DOTS,
            ),
            "note": "চেনা শব্দ দিয়ে টুকরো শেষ হলে শিশুর আত্মবিশ্বাস বাড়ে।",
            "seconds": 55,
            "slide": {"kind": "verse", "heading": "Verse 1 — Second Piece",
                      "arabic": W_RABB, "text": "🎤 Our word is at the end!"},
        },
        {
            "section": "Part 3 — Join verse 1",
            "says": S(
                "Now stick the two pieces together.",
                "[দুই হাত জোড়া লাগিয়ে দেখান]",
                "",
                "Listen first.",
                DOTS,
                "",
                "Now you say the whole verse.",
                DOTS,
            ),
            "does": "দুই হাত জুড়ে দেখান — জোড়া লাগানোর ব্যাপারটা চোখে "
                    "দেখলে শিশু বোঝে। পুরো আয়াত একবার সে একা বলুক।",
            "student": "পুরো প্রথম আয়াত বলে।",
            "expected": "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ",
            "correction": S(
                "Let's do it together this time.",
                DOTS,
                "[একসাথে বলুন]",
                "",
                "Lovely. Now on your own.",
                DOTS,
            ),
            "note": "টুকরো → জোড়া — এই ছকটাই ছয় আয়াতে চলবে।",
            "seconds": 55,
            "slide": {"kind": "repeat", "heading": "Verse 1 Together",
                      "arabic": N1, "text": "🎤 The whole verse now."},
        },
        {
            "section": "Part 4 — Running to Allah",
            "says": S(
                "What does verse one mean? Something beautiful.",
                "It means: I run to Allah to keep me safe.",
                "[দৌড়ে গিয়ে জড়িয়ে ধরার ভঙ্গি করুন]",
                "",
                "Like running to your Ammu when you're afraid.",
                "But Allah is stronger than anyone.",
                "Say the verse once more.",
                DOTS,
            ),
            "does": "⚠️ ভঙ্গিটা করে দেখান — দৌড়ে গিয়ে আশ্রয় নেওয়া। শিশু "
                    "ভয় পেলে মায়ের কাছে ছোটে, এই তুলনাটা সে সাথে সাথে বোঝে।",
            "student": "অর্থ বোঝে, আয়াত বলে।",
            "expected": "I run to Allah.",
            "correction": S(
                "Who do you run to when you're scared?",
                "[অপেক্ষা করুন]",
                "",
                "Yes! And we run to Allah too.",
            ),
            "note": "أعوذ মানে আশ্রয় চাওয়া। শিশুর জীবনের চেনা ছবি দিয়ে "
                    "বোঝালে অর্থটা মনে গেঁথে যায়।",
            "seconds": 55,
            "slide": {"kind": "meaning", "heading": "I Run To Allah",
                      "arabic": N1,
                      "text": "🏃 Allah keeps me safe."},
        },
        {
            "section": "Part 5 — مَلِكِ ٱلنَّاسِ",
            "says": S(
                "Verse two is tiny. Only two words.",
                "And you already know the second one!",
                "Listen.",
                DOTS,
                "",
                "Your turn.",
                DOTS,
            ),
            "does": "খুব ছোট আয়াত — একবারেই পুরোটা দিন, টুকরো করার দরকার "
                    "নেই। 'তুমি তো অর্ধেকটা জানোই' বলে উৎসাহ দিন।",
            "student": "দ্বিতীয় আয়াত বলে।",
            "expected": "مَلِكِ ٱلنَّاسِ",
            "correction": S(
                "Just two words. Listen.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Now you try.",
                DOTS,
            ),
            "note": "ছোট আয়াতে দ্রুত সাফল্য আসে — তাতে বড়গুলোর সাহস জন্মায়।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 2",
                      "arabic": N2, "text": "🎤 Only two words."},
        },
        {
            "section": "Part 5 — إِلَٰهِ ٱلنَّاسِ",
            "says": S(
                "Verse three. Two words again.",
                "And guess what's at the end?",
                "[অপেক্ষা করুন]",
                "",
                "Listen.",
                DOTS,
                "",
                "Your turn.",
                DOTS,
            ),
            "does": "শেষে কোন শব্দ আসবে সেটা শিশুকেই বলতে দিন — সে "
                    "পারলে খুব খুশি হবে। তারপর পুরো আয়াত।",
            "student": "শেষের শব্দটি আগে বলে, পরে পুরো আয়াত।",
            "expected": "إِلَٰهِ ٱلنَّاسِ",
            "correction": S(
                "Our hidden word again. Listen.",
                DOTS,
                "[শেষের শব্দে জোর দিন]",
                "",
                "Now you.",
                DOTS,
            ),
            "note": "শিশু নিজে অনুমান করতে পারছে — মানে ছকটা সে ধরে ফেলেছে।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 3",
                      "arabic": N3, "text": "🎤 Guess the last word!"},
        },
        {
            "section": "Part 6 — Three names",
            "says": S(
                "Look at the screen. Three special words.",
                DOTS,
                "[তিনটি শব্দ একে একে বলুন]",
                "",
                "The One who cares for you.",
                "The King of everyone.",
                "The only God we pray to.",
                "All three are Allah.",
            ),
            "does": "তিনটি শব্দ আলাদা আলাদা দেখান, প্রতিটির অর্থ বলুন। "
                    "তাড়াহুড়ো নয় — এখানেই সূরার হৃদয়।",
            "student": "তিনটি নাম শোনে, অর্থ বোঝে।",
            "expected": "All three are Allah.",
            "correction": S(
                "One at a time. Look here.",
                DOTS,
                "[একটি একটি করে দেখান]",
                "",
                "They're all Allah. Three beautiful names.",
            ),
            "note": "রব্ব, মালিক, ইলাহ — তিনটি নামই আল্লাহর। এই তিনটি "
                    "একসাথে আসা আন-নাসের নিজস্ব বৈশিষ্ট্য।",
            "seconds": 60,
            "slide": {"kind": "meaning", "heading": "Three Names Of Allah",
                      "arabic": W_THREE,
                      "text": "💚 Your Carer. Your King. Your God."},
        },
        {
            "section": "Part 7 — Verses 1, 2 and 3",
            "says": S(
                "Half the Surah done! Let's put them together.",
                "Listen to all three.",
                DOTS,
                "",
                "Now say all three with me.",
                DOTS,
                "[একসাথে বলুন]",
            ),
            "does": "অর্ধেক হয়ে গেছে — এটা বলে দিন, শিশু নিজের অগ্রগতি "
                    "টের পেলে উৎসাহ পায়। একসাথে বলুন, একা নয়।",
            "student": "তিনটি আয়াত পরপর বলে।",
            "expected": "তিনটি আয়াত একসাথে বলে।",
            "correction": S(
                "One verse at a time. I'll start.",
                DOTS,
                "[একটি করে দিন]",
                "",
                "Now all three.",
                DOTS,
            ),
            "note": "মাঝপথে জোড়া দেওয়া — শেষে গিয়ে একসাথে ছয়টি দিলে "
                    "শিশুর উপর চাপ পড়ে।",
            "seconds": 55,
            "slide": {"kind": "review", "heading": "Half Way!",
                      "arabic": NAS_123, "text": "🎤 All three together."},
        },
        {
            "section": "Part 8 — The sneaky whisper",
            "says": S(
                "Now something sneaky. Come closer.",
                "[ফিসফিস করে বলুন]",
                "",
                "Sometimes a bad idea whispers in your heart.",
                "Take that toy. Don't listen to Ammu.",
                "But when you say this Surah, it runs away!",
                "[হাত দিয়ে পালিয়ে যাওয়া দেখান]",
            ),
            "does": "⚠️ গলা নামিয়ে ফিসফিস করে বলুন — তাতে শিশু বুঝবে "
                    "ফিসফিস কাকে বলে। ভয় দেখাবেন না, বরং মজা করুন। শেষে "
                    "জোরে বলুন 'runs away!' আর হাত দিয়ে পালানো দেখান।",
            "student": "কাছে আসে, ফিসফিস শোনে, হাসে।",
            "expected": "It runs away!",
            "correction": S(
                "It's a sneaky whisper. But it's a coward.",
                "Say the Surah and off it goes!",
                "[পালিয়ে যাওয়ার ভঙ্গি করুন]",
            ),
            "note": "الخنّاس মানে যে পিছিয়ে যায়, পালায়। শিশুকে ভয় নয়, "
                    "সাহস দিতে হবে — সে জানুক এই সূরাই তার ঢাল।",
            "seconds": 55,
            "slide": {"kind": "activity", "heading": "It Runs Away",
                      "arabic": W_WASWAS,
                      "text": "🤫 A sneaky whisper… 💨 and it's gone!"},
        },
        {
            "section": "Part 8 — مِن شَرِّ",
            "says": S(
                "Verse four. First piece. Listen.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Your turn.",
                DOTS,
            ),
            "does": "ছোট টুকরো — দুবার বলে শিশুকে দিন। এই আয়াতটি লম্বা, "
                    "তাই টুকরো করা জরুরি।",
            "student": "টুকরোটি বলে।",
            "expected": "مِن شَرِّ",
            "correction": S(
                "Short and easy. Listen.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Now you.",
                DOTS,
            ),
            "note": "লম্বা আয়াত ছোট টুকরোয় ভাগ — নইলে শিশু হাল ছেড়ে দেয়।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 4 — First Piece",
                      "arabic": W_SHARR, "text": "🎤 Say it after me."},
        },
        {
            "section": "Part 8 — ٱلْوَسْوَاسِ ٱلْخَنَّاسِ",
            "says": S(
                "Second piece. Here's the odd one!",
                "It sounds like our hidden word. But it isn't.",
                "This is the one verse that's different.",
                "Listen carefully.",
                DOTS,
                "[খুব ধীরে বলুন]",
                "",
                "Now you. Take your time.",
                DOTS,
            ),
            "does": "⚠️ এই টুকরোটাই আজকের সবচেয়ে কঠিন। খুব ধীরে বলুন, "
                    "দরকার হলে তিনবার। শিশু আটকে গেলেও চাপ দেবেন না।",
            "student": "লম্বা টুকরোটি বলার চেষ্টা করে।",
            "expected": "ٱلْوَسْوَاسِ ٱلْخَنَّاسِ",
            "correction": S(
                "It's a long one. Let's do it in two halves.",
                DOTS,
                "[দুই ভাগে ভেঙে বলুন]",
                "",
                "Now both halves together.",
                DOTS,
            ),
            "note": "⚠️ এখানেই সেই ব্যতিক্রম — ٱلْخَنَّاسِ, ٱلنَّاسِ নয়। দুটোর "
                    "মিল শিশুকে দেখান, তাতে সে দুটোকে আলাদা করে চেনে। "
                    "শব্দটি লম্বা — অর্ধেক করে দিলে সে পারে। না পারলে "
                    "পরের ক্লাসে আবার দেখা হবে, আজ জোর নয়।",
            "seconds": 55,
            "slide": {"kind": "verse", "heading": "Verse 4 — Second Piece",
                      "arabic": W_WASWAS, "text": "🎤 Sounds like our word — but it's not!"},
        },
        {
            "section": "Part 8 — Join verse 4",
            "says": S(
                "Both pieces together now.",
                "Listen.",
                DOTS,
                "",
                "Your turn. You can do it.",
                DOTS,
            ),
            "does": "উৎসাহ দিন — 'তুমি পারবে'। এই আয়াতটি পারলে বাকিটা "
                    "সহজ মনে হবে তার কাছে।",
            "student": "চতুর্থ আয়াত বলে।",
            "expected": "مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ",
            "correction": S(
                "Let's say it together first.",
                DOTS,
                "[একসাথে বলুন]",
                "",
                "Now you on your own.",
                DOTS,
            ),
            "note": "একসাথে বলা → একা বলা — এই দুই ধাপ সবসময় রাখুন।",
            "seconds": 55,
            "slide": {"kind": "repeat", "heading": "Verse 4 Together",
                      "arabic": N4, "text": "🎤 You can do it!"},
        },
        {
            "section": "Part 9 — ٱلَّذِى يُوَسْوِسُ",
            "says": S(
                "Verse five. First piece. Listen.",
                DOTS,
                "[টুকরোটি বলুন]",
                "",
                "Your turn.",
                DOTS,
            ),
            "does": "আগের আয়াতের সাথে মিল আছে — সেটা মনে করিয়ে দিন, "
                    "তাতে শিশুর কাছে চেনা ঠেকবে।",
            "student": "টুকরোটি বলে।",
            "expected": "ٱلَّذِى يُوَسْوِسُ",
            "correction": S(
                "Listen once more, then you.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "Good one!",
            ),
            "note": "এই শব্দটিও ফিসফিসের কথা বলে — আগের ধাপের ভঙ্গিটা "
                    "মনে করিয়ে দিলে অর্থ ধরা সহজ হয়।",
            "seconds": 55,
            "slide": {"kind": "verse", "heading": "Verse 5 — First Piece",
                      "arabic": W_ALLADHI, "text": "🎤 Say it after me."},
        },
        {
            "section": "Part 9 — فِى صُدُورِ ٱلنَّاسِ",
            "says": S(
                "Second piece. Our hidden word is back!",
                "[বুকে হাত রাখুন]",
                "",
                "This one talks about your heart. Listen.",
                DOTS,
                "",
                "Your turn.",
                DOTS,
            ),
            "does": "বুকে হাত রেখে বলুন — শিশুও হাত রাখবে। শরীর দিয়ে "
                    "শেখা কথা বেশি দিন মনে থাকে।",
            "student": "বুকে হাত রেখে টুকরোটি বলে।",
            "expected": "فِى صُدُورِ ٱلنَّاسِ",
            "correction": S(
                "Hand on your heart, like this.",
                "[বুকে হাত রাখুন]",
                "",
                "Now listen and say it.",
                DOTS,
            ),
            "note": "صدور মানে বুক। হাত রাখার ভঙ্গিতে অর্থটা শেখানো হয়ে যায়।",
            "seconds": 55,
            "slide": {"kind": "verse", "heading": "Verse 5 — Second Piece",
                      "arabic": W_SUDUR, "text": "🫀 In people's hearts."},
        },
        {
            "section": "Part 9 — Join verse 5",
            "says": S(
                "Put them together. Listen first.",
                DOTS,
                "",
                "Now the whole verse. Your turn.",
                DOTS,
            ),
            "does": "জোড়া লাগানোর ধাপ — আগের মতোই দুই হাত জুড়ে দেখান।",
            "student": "পঞ্চম আয়াত বলে।",
            "expected": "ٱلَّذِى يُوَسْوِسُ فِى صُدُورِ ٱلنَّاسِ",
            "correction": S(
                "Together with me first.",
                DOTS,
                "[একসাথে বলুন]",
                "",
                "Now you alone. Beautiful.",
            ),
            "note": "পাঁচটি হয়ে গেল — একটি বাকি। শিশুকে বলে দিন।",
            "seconds": 55,
            "slide": {"kind": "repeat", "heading": "Verse 5 Together",
                      "arabic": N5, "text": "🎤 One more verse to go!"},
        },
        {
            "section": "Part 10 — The last verse",
            "says": S(
                "The last one! Verse six. It's short.",
                "Listen.",
                DOTS,
                "",
                "Your turn.",
                DOTS,
                "[অপেক্ষা করুন]",
                "",
                "You've got all six now!",
            ),
            "does": "শেষ আয়াত — উৎসাহ ভরা গলায় বলুন। ছয়টিই হয়ে গেছে, "
                    "এটা বলে হাততালি দিন।",
            "student": "ষষ্ঠ আয়াত বলে।",
            "expected": "مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ",
            "correction": S(
                "Nearly! Listen once more.",
                DOTS,
                "[ধীরে বলুন]",
                "",
                "There you go. All six!",
            ),
            "note": "শেষ আয়াতেও ٱلنَّاسِ — ধাঁধার উত্তর এখানে পূর্ণ হলো।",
            "seconds": 50,
            "slide": {"kind": "verse", "heading": "Verse 6 — The Last One",
                      "arabic": N6, "text": "🎉 All six done!"},
        },
        {
            "section": "Part 11 — What verses 4 to 6 mean",
            "says": S(
                "What do these last verses mean?",
                "Keep me safe from the sneaky whisper.",
                "The one that whispers inside our hearts.",
                "[বুকে হাত রাখুন]",
                "",
                "Now say those three verses once.",
                DOTS,
            ),
            "does": "অর্থ সহজ করে বলুন, ভয় দেখাবেন না। শেষে তিনটি আয়াত "
                    "একসাথে বলান।",
            "student": "অর্থ শোনে, তিনটি আয়াত বলে।",
            "expected": "Keep me safe from the whisper.",
            "correction": S(
                "It's about staying safe. That's all.",
                "Allah keeps us safe. Say them with me.",
                DOTS,
            ),
            "note": "সূরার মূল কথা — আল্লাহর কাছে আশ্রয়। শিশু যেন ভয় নয়, "
                    "নিরাপত্তা অনুভব করে।",
            "seconds": 55,
            "slide": {"kind": "meaning", "heading": "Keep Me Safe",
                      "arabic": NAS_456,
                      "text": "🛡️ Allah keeps me safe."},
        },
        {
            "section": "Part 12 — All six together",
            "says": S(
                "Big moment. The whole Surah, start to finish.",
                "I'll say it. You listen.",
                DOTS,
                "",
                "Now together, you and me.",
                DOTS,
                "[একসাথে বলুন]",
            ),
            "does": "প্রথমে আপনি, তারপর একসাথে। এখনো একা বলতে বলবেন না — "
                    "পরের ধাপে সেটা আসবে।",
            "student": "পুরো সূরা একসাথে বলে।",
            "expected": "পুরো সূরা একসাথে বলে।",
            "correction": S(
                "Let's go slower. Verse by verse.",
                DOTS,
                "[একটি একটি করে দিন]",
                "",
                "Now all six.",
                DOTS,
            ),
            "note": "একসাথে বলা মানে ভুলের ভয় নেই — শিশু নির্ভয়ে বলে।",
            "seconds": 65,
            "slide": {"kind": "memorization", "heading": "The Whole Surah",
                      "arabic": NAS_ALL, "text": "🎤 All six, together."},
        },
        {
            "section": "Part 13 — The echo game",
            "says": S(
                "Let's play the echo game!",
                "I say the front of a verse. You say the ending.",
                "Our hidden word. Ready?",
                DOTS,
                "[একটি আয়াতের শুরুটা বলুন, থেমে যান]",
                "",
                "[অপেক্ষা করুন — শিশু শেষটুকু বলবে]",
                "",
                "Yes! Again.",
                DOTS,
            ),
            "does": "⚠️ এটি আজকের নিজস্ব খেলা। প্রতিটি আয়াতের শুরুটা বলে "
                    "থেমে যান, শিশু শেষ শব্দটি বলবে। ⚠️ পাঁচবার খেলুন — ১, ২, "
                    "৩, ৫ ও ৬ নম্বর আয়াত। ৪ নম্বর বাদ, সেখানে শব্দটি "
                    "নেই। থামার "
                    "জায়গায় সত্যিই থামুন — নইলে খেলা হয় না।",
            "student": "প্রতিবার আয়াতের শেষ শব্দটি বলে।",
            "expected": "ٱلنَّاسِ — প্রতিবার শেষ শব্দটি বলে।",
            "correction": S(
                "Remember our hidden word? Say just that bit.",
                DOTS,
                "[শব্দটি মনে করিয়ে দিন]",
                "",
                "Now let's try again.",
            ),
            "note": "প্রতিধ্বনির খেলা — এই সূরার গঠনই খেলাটা তৈরি করে "
                    "দিয়েছে। অন্য কোনো দারসে এটি নেই।",
            "seconds": 60,
            "slide": {"kind": "activity", "heading": "The Echo Game",
                      "arabic": W_NAS,
                      "text": "🔊 I start… you finish!"},
        },
        {
            "section": "Part 14 — Eyes closed",
            "says": S(
                "Now close your eyes. No screen.",
                "[পর্দা সরিয়ে দিন]",
                "",
                "Say the whole Surah on your own.",
                "Take your time. I'm right here.",
                "[অপেক্ষা করুন — তাড়া দেবেন না]",
                "",
                "Open your eyes. That was wonderful!",
            ),
            "does": "⚠️ কাউসারে পর্দা ঢেকে দেখা হয়েছিল। আজ চোখ বন্ধ — "
                    "শিশু ভেতর থেকে মনে করে বলবে। আটকে গেলে প্রথম শব্দটি "
                    "ফিসফিস করে ধরিয়ে দিন, পুরোটা বলে দেবেন না।",
            "student": "চোখ বন্ধ করে পুরো সূরা বলার চেষ্টা করে।",
            "expected": "চোখ বন্ধ করে সূরা বলে।",
            "correction": S(
                "Stuck? I'll give you the first word only.",
                DOTS,
                "[কেবল প্রথম শব্দটি ফিসফিস করে বলুন]",
                "",
                "Keep going. You've got it.",
            ),
            "note": "না দেখে বলা — এতেই বোঝা যায় সত্যিই মুখস্থ হয়েছে কিনা।",
            "seconds": 55,
            "slide": {"kind": "blank", "heading": "Eyes Closed",
                      "arabic": "",
                      "text": "😌 From your heart now."},
        },
        {
            "section": "Part 15 — At bedtime",
            "says": S(
                "Here's something our Prophet ﷺ used to do.",
                "Every night, before sleeping.",
                "He'd cup his hands, like this.",
                "[দুই হাত জোড়া করে দেখান]",
                "",
                "Then read, blow softly, and wipe over himself.",
                "[ফুঁ দিয়ে হাত বুলিয়ে দেখান]",
                "",
                "Would you like to try tonight?",
            ),
            "does": "ভঙ্গিটা ধীরে করে দেখান, শিশুকেও করতে বলুন। রাতে "
                    "মায়ের সাথে করতে বলুন — অভ্যাসটা ঘরে গড়ে উঠবে।",
            "student": "হাত জোড়া করে, ফুঁ দেয়, হাত বুলায়।",
            "expected": "Yes!",
            "correction": S(
                "Like this. Cup your hands.",
                "[হাত ধরে দেখিয়ে দিন]",
                "",
                "Now blow softly. That's it.",
            ),
            "note": "রাসূল ﷺ ঘুমানোর আগে মুআওবিযাত পড়ে হাতে ফুঁ দিয়ে "
                    "শরীরে বুলাতেন — বুখারী ৫০১৭, মুসলিম। সহীহ, তাই "
                    "নিশ্চিন্তে শেখানো যায়।",
            "seconds": 55,
            "slide": {"kind": "reminder", "heading": "Before You Sleep",
                      "arabic": NAS_ALL,
                      "text": "🌙 Cup · read · blow · wipe."},
        },
        {
            "section": "Part 16 — When you feel afraid",
            "says": S(
                "One more thing. Listen well.",
                "When you feel scared at night, say this Surah.",
                "When a bad idea whispers, say this Surah.",
                "Allah is listening. Always.",
                "Say the first verse once more.",
                DOTS,
            ),
            "does": "শান্ত গলায় বলুন। শিশু যেন বোঝে সূরাটা তার হাতিয়ার — "
                    "কেবল মুখস্থ করার জিনিস নয়।",
            "student": "শোনে, প্রথম আয়াত বলে।",
            "expected": "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ",
            "correction": S(
                "Say it and you'll feel better. Try it.",
                DOTS,
                "[একসাথে বলুন]",
            ),
            "note": "কখন কাজে লাগবে তা জানলে শিশু নিজেই পড়তে শুরু করে।",
            "seconds": 50,
            "slide": {"kind": "reminder", "heading": "Whenever You're Afraid",
                      "arabic": N1,
                      "text": "🌟 Allah is always listening."},
        },
        {
            "section": "Part 17 — Well done",
            "says": S(
                "Look what you did today!",
                "You found the hidden word. Five times.",
                "You learned all six verses.",
                "I'm so proud of you.",
            ),
            "does": "নির্দিষ্ট করে প্রশংসা করুন — কী কী পেরেছে তা বলে "
                    "দিন। শুধু 'ভালো হয়েছে' নয়।",
            "student": "হাসে, খুশি হয়।",
            "expected": "হাসিমুখে শোনে।",
            "correction": S(
                "You worked hard today. That's what counts.",
                "Well done!",
            ),
            "note": "নির্দিষ্ট প্রশংসা শিশুকে পরের ক্লাসের জন্য টেনে আনে।",
            "seconds": 40,
            "slide": {"kind": "praise", "heading": "Well Done!",
                      "arabic": "أَحْسَنْتَ",
                      "text": "⭐ You found it five times!"},
        },
        {
            "section": "Part 18 — Homework",
            "says": S(
                "Tonight, two little jobs.",
                "One: say the Surah before you sleep.",
                "Two: teach the hidden word to someone at home.",
                "Your Ammu, or your little brother.",
                "Will you do that?",
            ),
            "does": "দুটি কাজ — বেশি নয়। বাড়িতে কাউকে শেখানো মানে "
                    "শিশু নিজেই আরেকবার ঝালিয়ে নেবে।",
            "student": "কাজ দুটি মনে রাখে।",
            "expected": "Yes!",
            "correction": S(
                "Just two small things. Can you remember them?",
                "[অপেক্ষা করুন]",
            ),
            "note": "শেখানোর মধ্য দিয়ে শেখা — বাড়ির কাজটাই সবচেয়ে ভালো "
                    "পুনরাবৃত্তি।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "At Home Tonight",
                      "arabic": NAS_ALL,
                      "text": "🌙 Say it before sleeping.\n"
                              "👨‍👩‍👧 Teach the hidden word to someone."},
        },
        {
            "section": "Part 19 — Closing",
            "says": S(
                "That's our class. You did beautifully today.",
                "Don't forget your hidden word!",
                "[অপেক্ষা করুন — শিশু শব্দটি বলতে পারে]",
                "",
                "Assalamu alaikum wa rahmatullah.",
                "See you next time!",
            ),
            "does": "শেষে আরেকবার লুকানো শব্দটি জিজ্ঞেস করুন — হাসিমুখে "
                    "বিদায় দিন।",
            "student": "শব্দটি বলে, সালামের উত্তর দেয়।",
            "expected": "ٱلنَّاسِ — শব্দটি বলে।",
            "correction": S(
                "Our hidden word, remember? Say it once.",
                DOTS,
                "[মনে করিয়ে দিন]",
            ),
            "note": "মিলিয়ে নিন: ধাঁধা ধরেছে · শব্দ পাঁচবার খুঁজে পেয়েছে · "
                    "ছয় আয়াত টুকরো করে ও জুড়ে বলেছে · ব্যতিক্রম আয়াতটি "
                    "চিনেছে · তিনটি নাম জেনেছে · "
                    "চোখ বন্ধ করে বলেছে · ঘুমের আগের নিয়ম শিখেছে।",
            "seconds": 35,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": W_NAS,
                      "text": "👋 Don't forget the hidden word!"},
        },
    ],
}

# ═══════════ টপিকের নাম থেকে দারসের নম্বর ═══════════
# ⚠️ কেন দরকার — পরিচালক লেকচার প্ল্যানে নিজের নামে টপিক সাজান, যেমন
# "Qaida for Beginners — Lesson-02"। নতুন দারস বসানোর সময় আগে ক্রম ধরে
# খোঁজা হতো, তাতে দারস ২ ও ৩ গিয়ে বসেছিল ৯ ও ১০ নম্বরে। কারণ টপিকের
# order-এর মান আর পরিচালকের দেওয়া নম্বর এক নয়।
#
# তাই এখন নামের ভেতরের নম্বরটাই পড়া হয়। "Lesson-02", "Lesson - 3",
# "দারস ৪", "Sabaq 5" — সব ধরনই চলে।

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_NO_RE = re.compile(
    r"(?:lesson|sabaq|dars|লেসন|দারস|সবক|পাঠ|ক্লাস)"
    r"\s*(?:no|নং|নাম্বার)?\s*[-–—:.#]?\s*0*(\d+)", re.I)


def topic_number(text, strict=True):
    """টপিকের নামে লেখা দারস নম্বর — না পেলে None।

    strict=True (ডিফল্ট) — কেবল "Lesson 4", "দারস ৪", "Sabaq-05" এমন
    স্পষ্ট লেখা হলেই। এটাই স্ক্রিপ্ট বসানোর সময় ব্যবহার করতে হবে।

    ⚠️ strict=False দিলে নামের শেষের সংখ্যাটাও ধরা হয়। সেটি বিপজ্জনক:
    "Memorized Hadith 4"-ও ৪ হয়ে যায়, আর দারস গিয়ে বসে ভুল হেডিংয়ে।
    বাস্তবে ঠিক এই ভুলটাই হয়েছিল — তাই এখন ডিফল্ট strict।
    """
    t = str(text or "").translate(_BN_DIGITS)
    m = _NO_RE.search(t)
    if m:
        return int(m.group(1))
    if strict:
        return None
    tail = re.search(r"(\d+)\s*$", t)
    return int(tail.group(1)) if tail else None


def topic_for_number(LectureTopic, Lesson, course, no, near=None):
    """ওই নম্বরের টপিক — যেখানে এখনো কোনো স্ক্রিপ্ট নেই।

    near দিলে (যেমন দারস ১-এর টপিক) তার হেডিং ও অধ্যায়কে অগ্রাধিকার
    দেওয়া হয়। ⚠️ নইলে অন্য হেডিংয়ের কোনো টপিক আগে মিলে যেতে পারে —
    বাস্তবে দারস ৪ ও ৫ গিয়ে বসেছিল "Memorized Hadith" হেডিংয়ে।

    ⚠️ স্ক্রিপ্ট থাকা টপিক ফেরত দেওয়া হয় না — পরিচালকের লেখা কিছুর
    উপরে কখনো বসানো চলবে না।
    """
    rows = [t for t in LectureTopic.objects.filter(
        lecture__course=course).order_by("lecture__no", "order", "id")
        if topic_number(t.text) == no
        and not Lesson.objects.filter(topic=t).exists()]
    if not rows:
        return None
    if near is not None:
        # ১) একই হেডিং, ২) একই অধ্যায় — এই ক্রমে খুঁজি
        same_section = [t for t in rows
                        if t.section_id and t.section_id == near.section_id]
        if same_section:
            return same_section[0]
        same_lecture = [t for t in rows if t.lecture_id == near.lecture_id]
        if same_lecture:
            return same_lecture[0]
    return rows[0]



SAMPLES = {"ikhlas": IKHLAS, "qaida": QAIDA,
           "qaida2": QAIDA2, "qaida3": QAIDA3,
           "qaida4": QAIDA4, "qaida5": QAIDA5,
           "kawthar": KAWTHAR,
           "nas": NAS}


def create_sample(Lesson, LessonStep, StepSlide, course, key,
                  status="published", replace=False, topic=None, target=None):
    """নমুনা দারসটি ওই কোর্সে তৈরি করে ফেরত দেয় — (দারস, আগে থেকে ছিল কিনা)।

    মডেলগুলো বাইরে থেকে নেওয়া হয় — মাইগ্রেশন ঐতিহাসিক মডেল পাঠায়, ভিউ
    আসলটা। তাই ভবিষ্যতে মডেল বদলালেও পুরনো মাইগ্রেশন ভাঙে না।

    একই কোর্সে একই শিরোনামের দারস আগে থেকে থাকলে —
      replace=False : কিছুই বদলানো হয় না, ওটাই ফেরত যায় (বারবার ডাকা নিরাপদ)
      replace=True  : ধাপগুলো মুছে নতুন লেখা বসে

    target দিলে ঠিক ওই দারসটির উপরেই নতুন লেখা বসে। ⚠️ এটা না থাকলে
    পুরনো দারসটি খোঁজা হয় টপিক বা শিরোনাম মিলিয়ে — পরিচালক শিরোনাম বদলে
    থাকলে সেটি আর মিলত না, আর "বদলে দিন" চাপলে বদলানোর বদলে একটি নকল
    দারস তৈরি হয়ে যেত।

    ⚠️ replace-এ দারসের সারিটি মোছা হয় না, কেবল তার ধাপগুলো — তাই
    শিক্ষার্থীদের অগ্রগতি (LessonProgress) অক্ষত থাকে।
    """
    data = SAMPLES[key]
    # টপিক দেওয়া থাকলে "আগে থেকে আছে কিনা" ওই টপিক ধরেই দেখি — একই নমুনা
    # আলাদা আলাদা টপিকে বসাতে চাইলে যেন আটকে না যায়
    # ⚠️ মাইগ্রেশন ঐতিহাসিক মডেল পাঠায়, আর ০০৩৬-এর সময় Lesson-এ topic
    # ঘরটি ছিলই না (এসেছে ০০৩৮-এ)। ঘরটি না দেখে topic= পাঠালে একদম নতুন
    # ডাটাবেজে migrate ভেঙে পড়ত — "Lesson() got unexpected keyword
    # arguments: 'topic'"। চালু সাইটে ধরা পড়েনি, কারণ সেখানে ০০৩৬ আগেই
    # চলে গিয়েছিল। তাই ঘরটি সত্যিই আছে কিনা দেখে নিই।
    has_topic = any(f.name == "topic" for f in Lesson._meta.fields)
    if target is not None:
        existing = target
    elif topic is not None and has_topic:
        existing = Lesson.objects.filter(topic=topic).first()
    else:
        existing = Lesson.objects.filter(course=course,
                                         title=data["title"]).first()
    if existing and not replace:
        return existing, True

    if existing:
        existing.steps.all().delete()
        for f in ("title_ar", "kind", "age_from", "age_to", "duration_min",
                  "objectives"):
            setattr(existing, f, data[f])
        existing.save()
        lesson = existing
    else:
        last = Lesson.objects.filter(course=course).order_by("-order").first()
        lesson = Lesson.objects.create(
            course=course, title=data["title"], title_ar=data["title_ar"],
            kind=data["kind"], age_from=data["age_from"], age_to=data["age_to"],
            duration_min=data["duration_min"], objectives=data["objectives"],
            status=status, order=(last.order + 1) if last else 0,
            **({"topic": topic} if has_topic else {}),
        )
    for i, st in enumerate(data["steps"]):
        step = LessonStep.objects.create(
            lesson=lesson, order=i, section=st["section"],
            teacher_says=st["says"], teacher_does=st["does"],
            student_does=st["student"], expected=st["expected"],
            correction=st.get("correction", ""), note=st.get("note", ""),
            seconds=st.get("seconds", 0),
        )
        sl = st["slide"]
        StepSlide.objects.create(
            step=step, kind=sl["kind"], heading=sl.get("heading", ""),
            arabic=sl.get("arabic", ""),
            # কুরআনের আরবি ও হরফ — যাচাই করা, তাই সুরক্ষিত
            arabic_locked=bool(sl.get("arabic")),
            # ⚠️ আরবির পাশে ইংরেজি উচ্চারণ লেখা হয় না — ঘরটি
            # খালিই থাকে (পরিচালক চাইলে নিজে লিখতে পারেন)
            translit="", text=sl.get("text", ""),
        )
    return lesson, bool(existing)
