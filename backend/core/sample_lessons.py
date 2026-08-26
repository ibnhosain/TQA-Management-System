# -*- coding: utf-8 -*-
"""নমুনা দারস — উস্তাদের স্ক্রিপ্ট ও শিক্ষার্থীর পর্দা।

⚠️ এখানকার লেখাগুলো নমুনা হলেও সত্যিকারের পড়ানোর উপযোগী — পরিচালক
পড়ে দেখে নিজের মতো করে সম্পাদনা করতে পারবেন।

কাঠামো — প্রতিটি ধাপে দুটি অংশ:
    উস্তাদের অংশ : says / does / student_does / expected / correction / note
    পর্দার অংশ   : slide (kind, heading, arabic, translit, text)
শিক্ষার্থী কেবল slide-টুকুই দেখেন।

⚠️ ভাষার নিয়ম — `says` মানে উস্তাদ যা **মুখে বলবেন**, অর্থাৎ ৫ বছরের
বাচ্চা যা কানে শুনবে। তাই এখানে:
    • ছোট ছোট বাক্য (৫–৮ শব্দ), কঠিন শব্দ নেই
    • শরীরের চেনা শব্দ — মুখ, জিভ, ঠোঁট, দাঁত, গলা
    • খেলার ঢঙে — "চলো খেলি", "তুমি পারবে!"
`does` / `expected` / `correction` / `note` উস্তাদের নিজের জন্য নির্দেশনা,
বাচ্চা এগুলো শোনে না — তাই সেগুলো স্বাভাবিক পেশাদার ভাষাতেই লেখা।

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
V1 = "قُلْ هُوَ ٱللَّهُ أَحَدٌ"
V2 = "ٱللَّهُ ٱلصَّمَدُ"
V3 = "لَمْ يَلِدْ وَلَمْ يُولَدْ"
V4 = "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ"

IKHLAS = {
    "title": "Surah Al-Ikhlas",
    "title_ar": "الإخلاص",
    "kind": "memorization",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 25,
    "objectives": (
        "<p><b>Learning objectives</b> — by the end of this lesson the student "
        "should be able to:</p>"
        "<ul>"
        "<li>Recite all four verses of Surah Al-Ikhlas correctly</li>"
        "<li>Say the whole Surah from memory, without looking</li>"
        "<li>Keep the four verses in the right order</li>"
        "<li>Say in one simple sentence what the Surah teaches — Allah is One</li>"
        "<li>Pronounce <b>أَحَدٌ</b> and <b>ٱلصَّمَدُ</b> clearly</li>"
        "</ul>"
        "<p><b>Mastery</b> — the child has mastered this when they can recite all "
        "four verses alone, in order, with no missing or swapped word, recovering "
        "after at most a one-word prompt, and can say what the Surah is about. "
        "Repeating it several times with the teacher is <i>not</i> mastery.</p>"
        "<p><b>Revision plan</b> — same day: one recall from memory. Next class: "
        "recite before the new lesson begins. Then once a week for four weeks.</p>"
        "<p><b>Teacher preparation</b> — check your own recitation of verse 4 "
        "beforehand; it carries the two hardest joins of this Surah.</p>"
    ),
    "steps": [
        {
            "section": "Welcome",
            "says": "Assalamu alaikum! How are you today? I am so happy to see you!",
            "does": "Smile. Wait for the reply. Say the child's name once — it settles them.",
            "student": "Returns the salam and answers.",
            "expected": "Wa alaikumus salam.",
            "correction": "If the child is shy, say the salam again slowly and give a thumbs-up when they reply.",
            "note": "Keep this warm and short. Do not start teaching yet.",
            "seconds": 45,
            "slide": {"kind": "title", "heading": "Surah Al-Ikhlas",
                      "arabic": "الإخلاص",
                      "text": "Assalamu alaikum!"},
        },
        {
            "section": "Introduction",
            "says": "Today we will learn a very special Surah. It is small. Only four little lines! It tells us about Allah.",
            "does": "Hold up four fingers. Keep your voice bright.",
            "student": "Listens.",
            "expected": "Attention on the screen.",
            "correction": "",
            "note": "Surah 112, four verses, Makki. Four fingers here sets up the memory game later — use the same hand each time.",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Four Little Lines",
                      "arabic": "الإخلاص",
                      "text": "A Surah about Allah."},
        },
        {
            "section": "Ta'awwudh",
            "says": "Before we read the Qur'an, we always say this. Say it with me!",
            "does": "Say A'udhu billahi minash-shaitanir-rajim, then Bismillahir-Rahmanir-Rahim — slowly, then again together with the child.",
            "student": "Repeats after the teacher.",
            "expected": "The child says both phrases, even if imperfectly.",
            "correction": "Do not correct pronunciation here. The habit matters more than perfection today.",
            "note": "",
            "seconds": 50,
            "slide": {"kind": "repeat", "heading": "Say With Me",
                      "arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                      "translit": "Bismillahir-Rahmanir-Rahim",
                      "text": "🤲 We always start with this."},
        },
        {
            "section": "Teacher Recitation",
            "says": "First, just listen. Close your mouth and open your ears! Ready?",
            "does": "Recite the whole Surah once, slowly and beautifully. Do not rush.",
            "student": "Listens quietly.",
            "expected": "Quiet attention. Some children move their lips — that is good.",
            "correction": "If the child tries to join in, gently say: 'Just listen this time. Your turn is next!'",
            "note": "This first hearing shapes the melody in the child's memory. Recite it well — the child will copy exactly what you give.",
            "seconds": 60,
            "slide": {"kind": "listen", "heading": "Listen",
                      "arabic": V1 + "\n" + V2 + "\n" + V3 + "\n" + V4,
                      "text": "👂 Just listen."},
        },
        {
            "section": "Verse 1 — Listen",
            "says": "Now line one. Listen to me!",
            "does": "Recite verse 1 slowly, twice.",
            "student": "Listens.",
            "expected": "Quiet attention.",
            "correction": "",
            "note": "",
            "seconds": 40,
            "slide": {"kind": "listen", "heading": "Line 1 — Listen",
                      "arabic": V1, "translit": "Qul huwal-lahu ahad",
                      "text": "👂"},
        },
        {
            "section": "Verse 1 — Repeat",
            "says": "Now your turn! Say it with me.",
            "does": "Say it together three times, then let the child say it alone once.",
            "student": "Repeats the verse.",
            "expected": "CHECK — the child says Qul huwal-lahu ahad alone, all four words, in order.",
            "correction": "If 'ahad' loses its ending, say only that word three times slowly, then the whole verse again.",
            "note": "Three times together, once alone. Do not go past four repetitions — young working memory tires fast.",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V1, "translit": "Qul huwal-lahu ahad",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "Verse 1 — Meaning",
            "says": "This line says: Allah is One. Just one! Not two, not three. One!",
            "does": "Hold up one finger. Say 'One!' clearly and happily.",
            "student": "Listens, may repeat 'One'.",
            "expected": "The child understands 'One'.",
            "correction": "",
            "note": "Translation: 'Say, He is Allah, [who is] One.' The line above is the child-friendly explanation, not the translation itself — keep the two apart if the child asks.",
            "seconds": 40,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V1,
                      "text": "Allah is One. Just One! ☝️"},
        },
        {
            "section": "Verse 2 — Listen",
            "says": "Here is line two. Listen!",
            "does": "Recite verse 2 slowly, twice. Stretch the 'ṣa' of As-Samad gently.",
            "student": "Listens.",
            "expected": "Quiet attention.",
            "correction": "",
            "note": "",
            "seconds": 40,
            "slide": {"kind": "listen", "heading": "Line 2 — Listen",
                      "arabic": V2, "translit": "Allahus-Samad", "text": "👂"},
        },
        {
            "section": "Verse 2 — Repeat",
            "says": "Now you say it with me!",
            "does": "Together three times, then the child alone once.",
            "student": "Repeats the verse.",
            "expected": "CHECK — Allahus-Samad, said alone, with a heavy ṣad.",
            "correction": "The ṣad (ص) is a heavy letter. If it sounds like a light 's', say 'ṣa-ṣa-ṣa' with a full round mouth, then the word again.",
            "note": "Pronunciation point: ص is one of the heavy letters. This is the most common slip in this Surah. Do not name the rule for a five-year-old — just model it.",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V2, "translit": "Allahus-Samad",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "Verse 2 — Meaning",
            "says": "This line says: we ask Allah for everything. Food, water, everything! Allah gives it all.",
            "does": "Ask: 'Who gives you your food?'",
            "student": "Answers.",
            "expected": "'Allah' — or a simple answer you can guide to Allah.",
            "correction": "If the child says a parent's name, smile and say: 'And who gives your mummy and daddy everything? Allah!'",
            "note": "Translation: 'Allah, the Eternal Refuge.' Everything needs Him; He needs nothing. Keep only the first half at this age.",
            "seconds": 50,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V2,
                      "text": "We ask Allah for everything. 🤲"},
        },
        {
            "section": "Connect 1 + 2",
            "says": "Now let us put line one and line two together!",
            "does": "Recite verses 1 and 2 as one flow, then together with the child twice.",
            "student": "Recites both verses.",
            "expected": "CHECK — the two verses joined without a long pause.",
            "correction": "If the child stops after verse 1, give only the first word of verse 2 as a hint — never the whole verse.",
            "note": "Joining early prevents 'island' memorisation, where each verse is known alone but the child cannot move from one to the next.",
            "seconds": 60,
            "slide": {"kind": "repeat", "heading": "Both Lines Together",
                      "arabic": V1 + "\n" + V2, "text": "🎤 Together now."},
        },
        {
            "section": "Verse 3 — Listen",
            "says": "Line three. Listen!",
            "does": "Recite verse 3 slowly, twice.",
            "student": "Listens.",
            "expected": "Quiet attention.",
            "correction": "",
            "note": "",
            "seconds": 40,
            "slide": {"kind": "listen", "heading": "Line 3 — Listen",
                      "arabic": V3, "translit": "Lam yalid wa lam yulad",
                      "text": "👂"},
        },
        {
            "section": "Verse 3 — Repeat",
            "says": "Your turn! Say it with me.",
            "does": "Together three times, then alone once.",
            "student": "Repeats the verse.",
            "expected": "CHECK — Lam yalid wa lam yulad, in that order.",
            "correction": "Children often swap 'yalid' and 'yulad'. Clap once on 'yalid' and twice on 'yulad' so the order sticks.",
            "note": "Reversing these two words is the single most common mistake in this Surah. Fix it now, not at the end.",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V3, "translit": "Lam yalid wa lam yulad",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "Verse 3 — Meaning",
            "says": "This line says: Allah has no mummy and no daddy. Allah has no baby. Allah was always here!",
            "does": "Keep it simple. Do not go further at this age.",
            "student": "Listens.",
            "expected": "The child understands 'always here'.",
            "correction": "",
            "note": "Translation: 'He neither begets nor is born.' Avoid deeper theology here — one clear picture is enough for a five-year-old.",
            "seconds": 40,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V3,
                      "text": "Allah was always here. ✨"},
        },
        {
            "section": "Verse 4 — Listen",
            "says": "The last line! It is a bit long. Listen!",
            "does": "Recite verse 4 slowly, twice.",
            "student": "Listens.",
            "expected": "Quiet attention.",
            "correction": "",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "listen", "heading": "Line 4 — Listen",
                      "arabic": V4, "translit": "Wa lam yakul-lahu kufuwan ahad",
                      "text": "👂"},
        },
        {
            "section": "Verse 4 — Repeat",
            "says": "Your turn! We will do it in two little pieces. Ready?",
            "does": "Say 'Wa lam yakul-lahu' — repeat. Then 'kufuwan ahad' — repeat. Then join the two pieces.",
            "student": "Repeats each piece, then the whole verse.",
            "expected": "CHECK — Wa lam yakul-lahu kufuwan ahad, joined into one line.",
            "correction": "If the child struggles, stay on the two pieces. Do not force the full verse today — half mastered is better than all forgotten.",
            "note": "Chunking is the key for this verse; it is the longest and carries the heaviest load of the lesson.",
            "seconds": 90,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V4, "translit": "Wa lam yakul-lahu kufuwan ahad",
                      "text": "🎤 Piece by piece."},
        },
        {
            "section": "Verse 4 — Meaning",
            "says": "This line says: nobody is like Allah. Nobody! Not one.",
            "does": "Shake your head slowly on 'nobody'.",
            "student": "Listens.",
            "expected": "The child understands 'nobody is like Allah'.",
            "correction": "",
            "note": "Translation: 'Nor is there to Him any equivalent.'",
            "seconds": 35,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V4,
                      "text": "Nobody is like Allah. 💚"},
        },
        {
            "section": "Activity",
            "says": "Let us play a game! Show me four fingers, like this. One finger for one line!",
            "does": "Touch a finger for each verse as you recite. Then let the child do it.",
            "student": "Touches a finger for each verse while reciting.",
            "expected": "Four verses, four fingers, in the right order.",
            "correction": "If a verse is skipped, hold that finger and give the first word only.",
            "note": "Movement fixes order in memory better than repetition alone — the hand becomes the child's own reminder.",
            "seconds": 90,
            "slide": {"kind": "activity", "heading": "Four-Finger Game",
                      "text": "✋ One finger for one line."},
        },
        {
            "section": "Activity",
            "says": "Now the words will hide! Can you still say it? I know you can!",
            "does": "Move to the blank screen. Wait patiently — do not fill the silence too soon.",
            "student": "Recites from memory.",
            "expected": "The Surah from memory, with small hesitations.",
            "correction": "Give only the first word of a verse as a hint, never the whole verse.",
            "note": "Look–Hide–Recall. Retrieving it from memory builds it far more strongly than reading it again. Count to five before helping.",
            "seconds": 90,
            "slide": {"kind": "blank", "heading": "Look & Hide",
                      "text": "🙈 Can you say it by heart?"},
        },
        {
            "section": "Practice",
            "says": "Let us say the whole Surah together, from the start. Nice and slow.",
            "does": "Recite together twice at a calm pace.",
            "student": "Recites along.",
            "expected": "The full Surah with the teacher.",
            "correction": "Slow down rather than stopping for small slips.",
            "note": "",
            "seconds": 80,
            "slide": {"kind": "repeat", "heading": "All Together",
                      "arabic": V1 + "\n" + V2 + "\n" + V3 + "\n" + V4,
                      "text": "🎤 From the start."},
        },
        {
            "section": "Assessment",
            "says": "Now all by yourself! I will just listen. Take your time.",
            "does": "Stay completely quiet. Note in your mind where the child hesitates.",
            "student": "Recites alone.",
            "expected": "CHECK — all four verses alone, in order, recovering after at most a one-word prompt. That is mastery for today.",
            "correction": "Do not correct during the recitation. Wait until the end, then mention one thing only.",
            "note": "One correction only. More than one discourages a young child and they remember the correction, not the Surah.",
            "seconds": 90,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "text": "🎤 I am listening."},
        },
        {
            "section": "Virtue",
            "says": "Do you know a secret? This little Surah is very big with Allah! Our Prophet ﷺ told us something amazing. Saying it is like reading a third of the Qur'an!",
            "does": "Say it with wonder. Hold up the four fingers again — such a small Surah, such a big reward.",
            "student": "Listens.",
            "expected": "Delight — a reason to keep reading it at home.",
            "correction": "",
            "note": "Authentic: the Prophet ﷺ said that Qul huwa Allahu ahad equals a third of the Qur'an — Sahih al-Bukhari 5013, Sahih Muslim 811. Do not add to this virtue or exaggerate it, and do not add any virtue without a verified source.",
            "seconds": 45,
            "slide": {"kind": "reminder", "heading": "A Big Secret!",
                      "text": "This little Surah is like reading a third of the Qur'an. 🌙"},
        },
        {
            "section": "Review",
            "says": "Mashaa Allah! You learned a whole Surah today! Tell me — is Allah one, or many?",
            "does": "Praise sincerely and specifically: name what got better today.",
            "student": "Answers.",
            "expected": "'One!'",
            "correction": "If the child cannot answer, hold up one finger and say 'One!' — then ask again.",
            "note": "Islamic lesson of this Surah: Tawheed — Allah is One, needs nothing, and nothing is like Him.",
            "seconds": 50,
            "slide": {"kind": "praise", "heading": "Mashaa Allah!",
                      "text": "You learned a whole Surah today! 🌟"},
        },
        {
            "section": "Homework",
            "says": "Before I see you again, say this Surah three times every day. And say it in your Salah too!",
            "does": "Say it slowly so a parent listening can note it down.",
            "student": "Listens.",
            "expected": "The child understands the task.",
            "correction": "",
            "note": "Parent note — please just listen and smile. Short and daily beats long and once. No drilling, no raised voices; if the child slips, say the first word and let them carry on.",
            "seconds": 40,
            "slide": {"kind": "homework", "heading": "Until Next Time",
                      "text": "📖 Say it 3 times every day.\n🤲 And in your Salah too."},
        },
        {
            "section": "Closing",
            "says": "Well done today! Baraka Allahu fik. Assalamu alaikum wa rahmatullah!",
            "does": "Smile. End warmly, never abruptly.",
            "student": "Returns the salam.",
            "expected": "Wa alaikumus salam.",
            "correction": "",
            "note": "Before you close, confirm: recitation demonstrated · child listened · all four verses chunked · verses connected · ṣad checked · recited without looking · meaning said · homework given.",
            "seconds": 25,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "See you next time, in shaa Allah. 👋"},
        },
    ],
}


# ──────────────────── Easy Noorani Qaida · দারস ১ · ৫–৭ বছর ────────────────────
QAIDA = {
    "title": "Easy Noorani Qaida — Lesson 1: The First Seven Letters",
    "title_ar": "الحروف المفردة",
    "kind": "qaida",
    "age_from": 5,
    "age_to": 7,
    "duration_min": 25,
    "objectives": (
        "<p><b>Learning objectives</b> — by the end of this lesson the student "
        "should be able to:</p>"
        "<ul>"
        "<li>Recognise the letters <b>ا ب ت ث ج ح خ</b> on sight, in any order</li>"
        "<li>Say each letter with the correct makhraj</li>"
        "<li>Tell <b>ت</b> apart from <b>ث</b>, and <b>ح</b> apart from <b>خ</b></li>"
        "<li>Read all seven letters in order without help</li>"
        "</ul>"
        "<p><b>Mastery</b> — the child names all seven letters when pointed at in "
        "random order, not only when read down the list, and keeps ت/ث and ح/خ "
        "apart. Saying the list from memory is <i>not</i> mastery.</p>"
        "<p><b>Revision plan</b> — same day: the point-and-say game once more. "
        "Next class: all seven before the new letters. Then once a week.</p>"
        "<p><b>Teacher preparation</b> — sit where your mouth is clearly visible "
        "on camera and well lit; this whole lesson is taught by imitation.</p>"
    ),
    "steps": [
        {
            "section": "Welcome",
            "says": "Assalamu alaikum! Are you ready to learn today? Let us go!",
            "does": "Smile. Wait for the reply. Use the child's name once.",
            "student": "Returns the salam.",
            "expected": "Wa alaikumus salam.",
            "correction": "If the child is quiet, repeat the salam slowly and wave.",
            "note": "Warm start. No teaching yet.",
            "seconds": 45,
            "slide": {"kind": "title", "heading": "Noorani Qaida — Lesson 1",
                      "arabic": "الحروف المفردة",
                      "text": "Assalamu alaikum!"},
        },
        {
            "section": "Introduction",
            "says": "The Qur'an is made of letters. Today we will learn seven letters. Show me seven fingers!",
            "does": "Hold up seven fingers and count them with the child.",
            "student": "Holds up seven fingers.",
            "expected": "Seven fingers up.",
            "correction": "",
            "note": "Seven is enough for one lesson at this age. Do not add more, even if the child seems quick — the next lesson continues the list.",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Our First Seven Letters",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "The Qur'an is made of letters."},
        },
        {
            "section": "Ta'awwudh",
            "says": "We always start with Bismillah. Say it with me!",
            "does": "Say it slowly, then together.",
            "student": "Repeats.",
            "expected": "Bismillahir-Rahmanir-Rahim.",
            "correction": "Do not correct pronunciation here — the habit matters more today.",
            "note": "",
            "seconds": 40,
            "slide": {"kind": "repeat", "heading": "Say With Me",
                      "arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                      "translit": "Bismillahir-Rahmanir-Rahim",
                      "text": "🤲 We always start with this."},
        },
        {
            "section": "Alif — Listen",
            "says": "This is our first letter. Its name is Alif. Listen — Alif!",
            "does": "Say it twice, clearly. Point at the letter on the screen.",
            "student": "Listens and looks at the letter.",
            "expected": "Eyes on the letter.",
            "correction": "",
            "note": "Makhraj: deep in the throat — an open, empty sound.",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Alif — Listen",
                      "arabic": "ا", "translit": "Alif", "text": "👂"},
        },
        {
            "section": "Alif — Repeat",
            "says": "Now your turn! Open your mouth big and say Alif.",
            "does": "Together three times, then the child alone once.",
            "student": "Says the letter.",
            "expected": "CHECK — Alif, a clean open sound, said alone.",
            "correction": "If the child adds a hum at the end, ask them to open the mouth and stop cleanly.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ا", "translit": "Alif", "text": "🎤"},
        },
        {
            "section": "Ba — Listen",
            "says": "Next letter — Ba. Watch my lips. They close together. Ba!",
            "does": "Say it twice. Point clearly at your lips so the child sees the makhraj.",
            "student": "Watches and listens.",
            "expected": "Eyes on your lips.",
            "correction": "",
            "note": "Makhraj: the two lips. Show it, do not only say it — this lesson is taught by imitation.",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Ba — Listen",
                      "arabic": "ب", "translit": "Ba",
                      "text": "👄 Watch the lips."},
        },
        {
            "section": "Ba — Repeat",
            "says": "Your turn! Close your lips and say Ba.",
            "does": "Together three times, then alone. Check that the lips truly close.",
            "student": "Says the letter.",
            "expected": "CHECK — Ba, with the lips meeting fully.",
            "correction": "If the lips do not close, ask the child to press them together and pop them open.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ب", "translit": "Ba", "text": "🎤"},
        },
        {
            "section": "Ta — Listen",
            "says": "Next letter — Ta. My tongue goes up and touches my top teeth. Ta!",
            "does": "Say it twice. Show the tongue position slowly.",
            "student": "Watches and listens.",
            "expected": "Attention on your mouth.",
            "correction": "",
            "note": "Makhraj: tip of the tongue on the gum behind the upper front teeth — tongue stays inside.",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Ta — Listen",
                      "arabic": "ت", "translit": "Ta",
                      "text": "👅 Tongue up, inside."},
        },
        {
            "section": "Ta — Repeat",
            "says": "Your turn! Tongue up, and keep it inside. Say Ta.",
            "does": "Together three times, then alone.",
            "student": "Says the letter.",
            "expected": "CHECK — Ta, crisp, tongue inside the mouth.",
            "correction": "If the tongue comes out between the teeth, that is Tha, not Ta. Show both and let the child hear the difference.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ت", "translit": "Ta", "text": "🎤"},
        },
        {
            "section": "Tha — Listen",
            "says": "Now Tha. This time my tongue peeks out, like this! Tha.",
            "does": "Say it twice. Let the child clearly see the tongue between the teeth.",
            "student": "Watches and listens.",
            "expected": "Attention on your mouth.",
            "correction": "",
            "note": "Makhraj: tongue tip between the upper and lower front teeth.",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Tha — Listen",
                      "arabic": "ث", "translit": "Tha",
                      "text": "👅 Tongue peeks out."},
        },
        {
            "section": "Tha — Repeat",
            "says": "Your turn! Let your tongue peek out. Say Tha.",
            "does": "Together three times, then alone. Watch for the tongue coming out.",
            "student": "Says the letter.",
            "expected": "CHECK — Tha, with the tongue tip visible.",
            "correction": "If it sounds like Ta or Sa, ask the child to let the tongue peek out and blow softly.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ث", "translit": "Tha", "text": "🎤"},
        },
        {
            "section": "Compare ت / ث",
            "says": "Listen! Ta … Tha. One tongue hides inside. One tongue peeks out. Which one is this?",
            "does": "Say them one after the other, then point at one letter and ask.",
            "student": "Names the letter.",
            "expected": "CHECK — the child names the letter you pointed at, not the one you said last.",
            "correction": "If the child confuses them, say them again with your mouth close to the camera and let them copy.",
            "note": "Common mistake #1 of this lesson. Spend time here — a ت/ث confusion left today follows the child into whole words later.",
            "seconds": 70,
            "slide": {"kind": "question", "heading": "Which One?",
                      "arabic": "ت      ث",
                      "text": "❓ One hides. One peeks out."},
        },
        {
            "section": "Jeem — Listen",
            "says": "Next letter — Jeem. The middle of my tongue pushes up. Jeem!",
            "does": "Say it twice, clearly.",
            "student": "Listens.",
            "expected": "Attention on the letter.",
            "correction": "",
            "note": "Makhraj: middle of the tongue against the hard palate.",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Jeem — Listen",
                      "arabic": "ج", "translit": "Jeem", "text": "👂"},
        },
        {
            "section": "Jeem — Repeat",
            "says": "Your turn! Push your tongue up and say Jeem.",
            "does": "Together three times, then alone.",
            "student": "Says the letter.",
            "expected": "CHECK — Jeem, full, not soft like a 'zh'.",
            "correction": "If it sounds soft, ask the child to press the tongue up firmly and release.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ج", "translit": "Jeem", "text": "🎤"},
        },
        {
            "section": "Ḥa — Listen",
            "says": "Now Ḥa. This one comes from here — my throat. It is like warm breath on your hand. Ḥa!",
            "does": "Say it twice. Put your hand on your throat so the child copies the gesture.",
            "student": "Listens and copies the gesture.",
            "expected": "Attention on the throat.",
            "correction": "",
            "note": "Makhraj: middle of the throat. Smooth and warm — no scraping.",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Ḥa — Listen",
                      "arabic": "ح", "translit": "Ḥa",
                      "text": "🌬️ Warm breath."},
        },
        {
            "section": "Ḥa — Repeat",
            "says": "Your turn! Warm breath from your throat. Say Ḥa.",
            "does": "Together three times, then alone.",
            "student": "Says the letter.",
            "expected": "CHECK — Ḥa, smooth, from mid-throat.",
            "correction": "If it sounds like the English 'h', ask the child to breathe out harder with the throat a little tighter.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ح", "translit": "Ḥa", "text": "🎤"},
        },
        {
            "section": "Kha — Listen",
            "says": "Our last letter — Kha! This one is a bit scratchy. Listen. Kha!",
            "does": "Say it twice. Exaggerate slightly so the difference from Ḥa is obvious.",
            "student": "Listens.",
            "expected": "Attention on the letter.",
            "correction": "",
            "note": "Makhraj: upper throat, with a light scraping quality.",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Kha — Listen",
                      "arabic": "خ", "translit": "Kha",
                      "text": "👂 A bit scratchy."},
        },
        {
            "section": "Kha — Repeat",
            "says": "Your turn! Make it scratchy. Say Kha.",
            "does": "Together three times, then alone.",
            "student": "Says the letter.",
            "expected": "CHECK — Kha, from the upper throat.",
            "correction": "If the child cannot make it, ask them to pretend to fog up a cold window, then tighten it.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "خ", "translit": "Kha", "text": "🎤"},
        },
        {
            "section": "Compare ح / خ",
            "says": "Listen! Ḥa … Kha. One is soft. One is scratchy. Say them after me!",
            "does": "Say the pair three times, then let the child say the pair alone.",
            "student": "Says both letters.",
            "expected": "CHECK — two clearly different sounds, not one sound twice.",
            "correction": "If both sound the same, go back to Ḥa alone and rebuild it before pairing again.",
            "note": "Common mistake #2 of this lesson.",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Smooth or Rough?",
                      "arabic": "ح      خ",
                      "text": "❓ One is soft. One is scratchy."},
        },
        {
            "section": "Practice",
            "says": "Now all seven letters together, from the start!",
            "does": "Point at each letter as you both say it. Twice through, calmly.",
            "student": "Reads along.",
            "expected": "All seven letters in order.",
            "correction": "Slow down rather than stopping for a single slip.",
            "note": "",
            "seconds": 70,
            "slide": {"kind": "letters", "heading": "All Together",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "🎤 From the start."},
        },
        {
            "section": "Activity",
            "says": "Game time! I will point. You say the letter's name. Fast as you can!",
            "does": "Point in random order, six or seven times. Speed up gently.",
            "student": "Names each letter.",
            "expected": "Correct names, faster each round.",
            "correction": "If a letter is missed, say its name once and point at it again a moment later.",
            "note": "Random order proves recognition; in-order proves only that the child memorised the list. This game is the real test of the lesson.",
            "seconds": 90,
            "slide": {"kind": "activity", "heading": "Point & Say",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "👉 Say the letter I point at!"},
        },
        {
            "section": "Assessment",
            "says": "Now all by yourself! I will just listen.",
            "does": "Stay quiet. Note where the child hesitates.",
            "student": "Reads all seven alone.",
            "expected": "CHECK — all seven alone, ت/ث and ح/خ kept apart. That is mastery for today.",
            "correction": "Do not interrupt. At the end mention one thing only.",
            "note": "One correction only — more discourages a young child.",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "🎤 I am listening."},
        },
        {
            "section": "Homework",
            "says": "Mashaa Allah! You did it! Now a little homework. Say these seven letters five times every day.",
            "does": "Praise specifically — name what got better today. Say the homework slowly for any parent listening.",
            "student": "Listens.",
            "expected": "The child understands the task.",
            "correction": "",
            "note": "Parent note — please just listen and smile. Five times a day takes one minute. No drilling; if a letter is wrong, leave it for the teacher rather than correcting the makhraj at home.",
            "seconds": 45,
            "slide": {"kind": "homework", "heading": "Until Next Time",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "📖 Say them 5 times every day."},
        },
        {
            "section": "Closing",
            "says": "Well done today! Baraka Allahu fik. Assalamu alaikum wa rahmatullah!",
            "does": "Smile. End warmly.",
            "student": "Returns the salam.",
            "expected": "Wa alaikumus salam.",
            "correction": "",
            "note": "Before you close, confirm: every letter demonstrated · child watched your mouth · each letter said alone · ت/ث compared · ح/خ compared · random-order game done · homework given.",
            "seconds": 25,
            "slide": {"kind": "end", "heading": "Jazakumullahu Khairan",
                      "arabic": "بَارَكَ ٱللَّهُ فِيكَ",
                      "text": "See you next time, in shaa Allah. 👋"},
        },
    ],
}

SAMPLES = {"ikhlas": IKHLAS, "qaida": QAIDA}


def create_sample(Lesson, LessonStep, StepSlide, course, key, status="published"):
    """নমুনা দারসটি ওই কোর্সে তৈরি করে ফেরত দেয়।

    মডেলগুলো বাইরে থেকে নেওয়া হয় — মাইগ্রেশন ঐতিহাসিক মডেল পাঠায়, ভিউ
    আসলটা। তাই ভবিষ্যতে মডেল বদলালেও পুরনো মাইগ্রেশন ভাঙে না।

    একই কোর্সে একই শিরোনামের দারস আগে থেকে থাকলে নতুন করে বানানো হয় না —
    তাই বারবার ডাকা নিরাপদ।
    """
    data = SAMPLES[key]
    existing = Lesson.objects.filter(course=course, title=data["title"]).first()
    if existing:
        return existing

    last = Lesson.objects.filter(course=course).order_by("-order").first()
    lesson = Lesson.objects.create(
        course=course, title=data["title"], title_ar=data["title_ar"],
        kind=data["kind"], age_from=data["age_from"], age_to=data["age_to"],
        duration_min=data["duration_min"], objectives=data["objectives"],
        status=status, order=(last.order + 1) if last else 0,
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
            translit=sl.get("translit", ""), text=sl.get("text", ""),
        )
    return lesson
