# -*- coding: utf-8 -*-
"""নমুনা দারস — উস্তাদের স্ক্রিপ্ট ও শিক্ষার্থীর পর্দা।

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
            "Let us do it one more time.\n"
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
                    "MashaAllah! I am very happy to see you today.",
            "does": "হাসুন, হাত নাড়ুন। নাম ধরে একবার ডাকুন। উত্তরের জন্য "
                    "অপেক্ষা করুন — এই সময়টুকুই শিশুকে সহজ করে দেয়।",
            "student": "সালামের জবাব দেয় ও উত্তর দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": "That is okay! Listen to me.\n"
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
                    "Today, inshaAllah, we will learn Surah Al-Ikhlas.\n"
                    "It is a very short Surah.\n"
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
            "section": "Part 1 — How we will learn",
            "says": "Do not worry if you cannot remember everything today.\n"
                    "I will say it first.\n"
                    "You will listen.\n"
                    "Then you will say it after me.\n"
                    "We will practise together.\n"
                    "And then you will try by yourself.\n"
                    "Are you ready?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Excellent! Let us begin. 🌟",
            "does": "শান্ত ও উৎসাহী গলায় বলুন। শিশুর ভয় কাটানোই এই ধাপের কাজ।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes! / মাথা নাড়ে।",
            "correction": "It is very easy. I will help you.\n"
                          "We will do it together.\n"
                          "Ready? Let us begin!",
            "note": "",
            "seconds": 35,
            "slide": {"kind": "title", "heading": "Let us begin!",
                      "text": "👂 Listen\n🎤 Say it\n🌟 Try alone"},
        },

        # ═══════════════ PART 2 — LISTEN ═══════════════
        {
            "section": "Part 2 — Just listen",
            "says": "Before we start, I want you to do one thing.\n"
                    "Just listen to me.\n"
                    "Do not repeat yet.\n"
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
            "Now we will learn it one little part at a time.\n"
            "Let us start with the first verse.",
            "So close! Watch my mouth.\n"
            + DOTS + "\n"
            "[টুকরোটি আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "MashaAllah! That is it.",
            seconds=55,
        ),
        _chunk(
            "Part 3 — هُوَ ٱللَّهُ", C_HUWALLAH,
            "Now the next part.",
            "Nearly! Let us go very slowly.\n"
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
            "says": "Now we will put our little pieces together.\n"
                    "Listen to me first.\n"
                    + DOTS + "\n"
                    "[পুরো ১ম আয়াতটি ধীরে পড়ুন]\n\n"
                    "Now you try.\n"
                    "[অপেক্ষা করুন — শিশু বলবে]\n\n"
                    "MashaAllah! 🌟\n"
                    "Let us say it together one more time.\n"
                    "[শিশুর সাথে একসাথে পড়ুন]",
            "does": "প্রথমে একা পড়ুন, তারপর শিশু একা, তারপর দুজনে একসাথে।",
            "student": "পুরো আয়াতটি বলে।",
            "expected": V1,
            "correction": "You are doing so well!\n"
                          "Here is a little help.\n"
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
            "says": "Now let us learn what this verse means.\n"
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
            "says": "Now let us put them together.\n"
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
            "correction": "Let us try again slowly.\n"
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
            "says": "Now let us understand this verse.\n"
                    "It means we need Allah.\n"
                    "Tell me — do we need Allah?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "Very good!\n"
                    "Now tell me — does Allah need us?\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah!\n"
                    "We need Allah.\n"
                    "Allah does not need anyone.",
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
            "says": "Now let us see if you remember the first two verses "
                    "together.\n"
                    "I will help you.\n"
                    + DOTS + "\n"
                    "[১ম ও ২য় আয়াত একসাথে ধীরে পড়ুন]\n\n"
                    "Now you try.\n"
                    "[অপেক্ষা করুন]\n\n"
                    "MashaAllah! Excellent!\n"
                    "You are doing a great job!",
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
            "says": "Now we are ready for verse number three.\n"
                    "This verse is a little different.\n"
                    "So listen very carefully.\n"
                    "Do not worry. We will learn it slowly.",
            "does": "শিশুকে একটু সোজা হয়ে বসতে বলুন। এই আয়াতে মনোযোগ বেশি লাগে।",
            "student": "শোনে।",
            "expected": "মনোযোগ ফিরে এসেছে।",
            "correction": "Look at me. Are you ready?\n"
                          "It is easy. I will help you.",
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
            "correction": "Let us clap.\n"
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
            "says": "Now let us understand this verse.\n"
                    "Allah does not have children.\n"
                    "And Allah was not born.\n"
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
            "says": "We are now at the last verse.\n"
                    "It is a little long.\n"
                    "So we will learn it in very small pieces.\n"
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
            "It is a tiny word.\n"
            + DOTS + "\n"
            "[আবার পড়ুন]\n\n"
            "Now you.\n"
            "[অপেক্ষা করুন]\n\n"
            "Excellent!",
            seconds=40,
        ),
        _chunk(
            "Part 10 — كُفُوًا", C_KUFUWAN, "Now listen.",
            "Let us go slowly, piece by piece.\n"
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
            "correction": "That is a long one!\n"
                          "Let us do just the first half.\n"
                          + DOTS + "\n"
                          "[কেবল প্রথম অর্ধেকটা পড়ুন]\n\n"
                          "Good! We will do the rest next time.",
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
            "says": "Now let us play a little memory game.\n"
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
                              "3️⃣ Allah was not born\n"
                              "4️⃣ Nobody is like Allah"},
        },
        {
            "section": "Part 13 — Look and hide",
            "says": "Now let us see how much you remember.\n"
                    "Look at the screen. Read it with me.\n"
                    "[একসাথে পড়ুন]\n\n"
                    "Excellent!\n"
                    "Now I am going to hide it.\n"
                    "[পর্দা খালি করুন]\n\n"
                    "Can you say it?\n"
                    "[অপেক্ষা করুন — পাঁচ পর্যন্ত গুনুন]\n\n"
                    "MashaAllah!",
            "does": "প্রথমে আয়াত দেখিয়ে একসাথে পড়ুন, তারপর খালি পর্দায় যান। "
                    "চুপ থাকুন — নীরবতাতেই স্মৃতি তৈরি হয়।",
            "student": "মুখস্থ থেকে বলে।",
            "expected": "আয়াতগুলো, ছোটখাটো থামা চলবে।",
            "correction": "You are doing so well!\n"
                          "Here is a little hint.\n"
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
                    "Now let us recite the whole Surah together.\n"
                    + DOTS + "\n"
                    "[শিশুর সাথে একসাথে পুরো সূরা পড়ুন]\n\n"
                    "MashaAllah! 🌟\n"
                    "You did a wonderful job!",
            "does": "শান্ত গতিতে একসাথে পড়ুন। ছোটখাটো ভুলে থামবেন না।",
            "student": "সাথে পুরো সূরা বলে।",
            "expected": "পুরো সূরা উস্তাদের সাথে।",
            "correction": "Let us go a bit slower.\n"
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
                    "If you forget something, do not worry. I will help you.\n"
                    "[একদম চুপ থাকুন — শিশু একা পড়বে]",
            "does": "একদম চুপ থাকুন। কোথায় থেমে যাচ্ছে তা মনে রাখুন, কিন্তু "
                    "পড়ার মাঝে থামাবেন না।",
            "student": "একা পুরো সূরা বলে।",
            "expected": "চার আয়াত একা, ঠিক ক্রমে, এক শব্দের ইশারাতেই সামলে "
                        "নেওয়া — আজকের জন্য এটাই মুখস্থ হওয়া।",
            "correction": "That is okay. Let us try that part again.\n"
                          + DOTS + "\n"
                          "[কেবল প্রথম শব্দটুকু বলুন, বাকিটা শিশু বলবে]\n\n"
                          "MashaAllah! You remembered!",
            "note": "⚠️ ভুল হলে কখনোই 'Wrong' বলবেন না। বলুন 'That is okay' — "
                    "তারপর সবচেয়ে ছোট ইশারাটুকু দিন। শেষে কেবল একটি জিনিস "
                    "শুধরে দিন, একের বেশি নয়।",
            "seconds": 80,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "text": "🎤 I am listening.\nTake your time."},
        },
        {
            "section": "Part 16 — Final review",
            "says": "Before we finish, let us remember what our Surah "
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
            "correction": "Let us do that one again.\n"
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
                    "Saying it is like reading a third of the Qur'an!",
            "does": "বিস্ময় নিয়ে বলুন। আবার চার আঙুল দেখান — এত ছোট সূরা, "
                    "এত বড় পুরস্কার।",
            "student": "শোনে।",
            "expected": "খুশি — বাড়িতেও পড়ার আগ্রহ।",
            "correction": "It is a small Surah, right?\n"
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
                    "You learned that Allah was not born.\n"
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
                          "That is very small, right?\n"
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
            "says": "Now let us recite it one more time together.\n"
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
    "kind": "qaida",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 20,
    "objectives": (
        "<p><b>Noorani Qaida — Lesson 1 · Teacher Script</b><br>"
        "Age 5–7 · about 20 minutes · The first seven letters<br>"
        "Listen → Watch the mouth → Say → Compare → Play</p>"
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
                "I am so happy to see you!",
                "[অপেক্ষা করুন — শিশু সালামের জবাব দেবে]",
                "",
                "Are you ready to learn? Let us go!",
            ),
            "does": "হাসুন, হাত নাড়ুন। নাম ধরে একবার ডাকুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": S(
                "That is okay! Listen.",
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
                "Today we will learn seven letters.",
                "Seven! Show me seven fingers.",
                "[অপেক্ষা করুন — শিশু আঙুল দেখাবে]",
                "",
                "Let us count them together.",
                "One, two, three, four, five, six, seven!",
            ),
            "does": "সাতটি আঙুল তুলে একসাথে গুনুন।",
            "student": "সাতটি আঙুল দেখায়, সাথে গোনে।",
            "expected": "সাতটি আঙুল উপরে।",
            "correction": S(
                "Let us count together.",
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
                "That is it!",
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
                "I am pointing at this one. Which one is it?",
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
                "That is much better!",
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
                "It is like warm breath on your hand.",
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
                "It is scratchy — like this.",
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
                "Let us try a game.",
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
                "They sounded the same! Let us do just one.",
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
                "I will point, and we say them together. Ready?",
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
                "Let us go a bit slower. From the start.",
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
        {
            "section": "Activity",
            "says": S(
                "Game time!",
                "I will point at a letter. You say its name.",
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
                "Good! Now watch, I am pointing again…",
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
                "I will just listen. Take your time.",
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
                      "text": "🎤 I am listening."},
        },
        {
            "section": "Homework",
            "says": S(
                "MashaAllah! You did it!",
                "I am so proud of you.",
                "Now a little homework.",
                "Before I see you again,",
                "say these seven letters five times every day.",
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
                    "উস্তাদের জন্য রেখে দিন।",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Until Next Time",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "📖 Say them 5 times every day."},
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
                    "ت/ث মেলানো হয়েছে · ح/خ মেলানো হয়েছে · এলোমেলো ক্রমের "
                    "খেলা হয়েছে · বাড়ির কাজ দেওয়া হয়েছে।",
            "seconds": 25,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "See you next time, in shaa Allah. 👋"},
        },
    ],
}


SAMPLES = {"ikhlas": IKHLAS, "qaida": QAIDA}


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
    if target is not None:
        existing = target
    elif topic is not None:
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
            topic=topic,
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
