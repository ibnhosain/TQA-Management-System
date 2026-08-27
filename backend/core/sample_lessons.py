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
        "<li>Say all four verses of Surah Al-Ikhlas</li>"
        "<li>Say the whole Surah from memory, without looking</li>"
        "<li>Keep the four verses in the right order</li>"
        "<li>Say what the Surah teaches — Allah is One</li>"
        "<li>Say <b>أَحَدٌ</b> and <b>ٱلصَّمَدُ</b> clearly</li>"
        "</ul>"
        "<p><b>How to use this script</b> — every line in “উস্তাদ বলবেন” and "
        "“ভুল হলে” is written to be read out loud, word for word. You do not "
        "need to make up any English yourself. Read it warmly and slowly.</p>"
        "<p><b>Mastery</b> — the child has mastered this when they can say all "
        "four verses alone, in order, with no missing or swapped word, "
        "recovering after at most a one-word hint, and can say what the Surah "
        "is about. Saying it a few times with you is <i>not</i> mastery.</p>"
        "<p><b>Revision plan</b> — same day: one recall from memory. Next "
        "class: say it before the new lesson. Then once a week for four "
        "weeks.</p>"
    ),
    "steps": [
        {
            "section": "Welcome",
            "says": "Assalamu alaikum! How are you today? I am so happy to see "
                    "you! Are you ready? Let us start!",
            "does": "হাসুন, হাত নাড়ুন। নাম ধরে একবার ডাকুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": "That is okay! Listen. Assalamu alaikum. Now you say "
                          "it back to me. Say — Wa alaikumus salam. Very good!",
            "note": "শুরুটা উষ্ণ ও ছোট রাখুন। এখনই পড়ানো শুরু নয়।",
            "seconds": 45,
            "slide": {"kind": "title", "heading": "Surah Al-Ikhlas",
                      "arabic": "الإخلاص",
                      "text": "Assalamu alaikum!"},
        },
        {
            "section": "Introduction",
            "says": "Today we learn a very special Surah. It is a small one. "
                    "Only four little lines! Look at my hand. One, two, three, "
                    "four. This Surah tells us about Allah.",
            "does": "চারটি আঙুল তুলে দেখান, একসাথে গুনুন।",
            "student": "শোনে, চাইলে আঙুল গোনে।",
            "expected": "শিশু চারটি আঙুল দেখে।",
            "correction": "Show me four fingers. Like this. One, two, three, "
                          "four. Well done!",
            "note": "সূরা ১১২, চার আয়াত, মাক্কী। এই চার আঙুলই পরে স্মৃতির "
                    "খেলায় কাজে লাগবে — একই হাত ব্যবহার করুন।",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Four Little Lines",
                      "arabic": "الإخلاص",
                      "text": "A Surah about Allah."},
        },
        {
            "section": "Ta'awwudh",
            "says": "Before we read the Qur'an, we always say this. Listen to "
                    "me first. A'udhu billahi minash-shaitanir-rajim. "
                    "Bismillahir-Rahmanir-Rahim. Now say it with me!",
            "does": "প্রথমে একা বলুন, তারপর একসাথে বলুন।",
            "student": "সাথে বলে।",
            "expected": "Bismillahir-Rahmanir-Rahim.",
            "correction": "Good try! Say the small bit with me. Bismillah. "
                          "Again — Bismillah. Now the whole thing. "
                          "Bismillahir-Rahmanir-Rahim. Mashaa Allah!",
            "note": "এখানে উচ্চারণ শোধরাবেন না — অভ্যাসটাই আজ বড়।",
            "seconds": 50,
            "slide": {"kind": "repeat", "heading": "Say With Me",
                      "arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                      "translit": "Bismillahir-Rahmanir-Rahim",
                      "text": "🤲 We always start with this."},
        },
        {
            "section": "Teacher Recitation",
            "says": "Now just listen. Do not say anything yet. Close your "
                    "mouth and open your ears! Ready? Here we go.",
            "does": "পুরো সূরাটি একবার ধীরে ও সুন্দর করে পড়ুন। তাড়াহুড়ো নয়।",
            "student": "চুপ করে শোনে।",
            "expected": "মনোযোগ দিয়ে শোনা। ঠোঁট নড়লে সেটা ভালো লক্ষণ।",
            "correction": "Sshh — just listen this time. Your turn is next. I "
                          "promise! Listen again.",
            "note": "এই প্রথম শোনাটাই বাচ্চার মনে সুরটা বসিয়ে দেয় — যেভাবে "
                    "পড়বেন, সে হুবহু সেভাবেই শিখবে।",
            "seconds": 60,
            "slide": {"kind": "listen", "heading": "Listen",
                      "arabic": V1 + "\n" + V2 + "\n" + V3 + "\n" + V4,
                      "text": "👂 Just listen."},
        },
        {
            "section": "Verse 1 — Listen",
            "says": "Now line one. Listen to me. I will say it two times.",
            "does": "১ম আয়াত ধীরে দুবার পড়ুন।",
            "student": "শোনে।",
            "expected": "চুপ করে শোনা।",
            "correction": "Look at my mouth. Watch how it moves. Listen "
                          "one more time. Qul huwal-lahu ahad. Beautiful, "
                          "isn't it?",
            "note": "",
            "seconds": 40,
            "slide": {"kind": "listen", "heading": "Line 1 — Listen",
                      "arabic": V1, "translit": "Qul huwal-lahu ahad",
                      "text": "👂"},
        },
        {
            "section": "Verse 1 — Repeat",
            "says": "Now your turn! Say it with me. Qul huwal-lahu ahad. "
                    "Again! Qul huwal-lahu ahad. One more time! Now you say "
                    "it all by yourself.",
            "does": "তিনবার একসাথে, তারপর একবার শিশু একা।",
            "student": "আয়াতটি বলে।",
            "expected": "Qul huwal-lahu ahad — চারটি শব্দই, ঠিক ক্রমে।",
            "correction": "So close! Listen to this word. Ahad. Say it — "
                          "Ahad. Again — Ahad. Lovely! Now the whole line. "
                          "Qul huwal-lahu ahad. Mashaa Allah!",
            "note": "তিনবার একসাথে, একবার একা। চারবারের বেশি নয় — এই বয়সে "
                    "মনোযোগ দ্রুত ক্লান্ত হয়।",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V1, "translit": "Qul huwal-lahu ahad",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "Verse 1 — Meaning",
            "says": "This line tells us something. Allah is One. Just one! Not "
                    "two. Not three. One! Show me one finger. Say it with me — "
                    "Allah is One.",
            "does": "একটি আঙুল তুলুন।",
            "student": "একটি আঙুল দেখায়, সাথে বলে।",
            "expected": "Allah is One.",
            "correction": "Look — one finger. Just one. Now you. Say — Allah "
                          "is One. Very good!",
            "note": "অর্থ: 'বলো, তিনি আল্লাহ, এক।' উপরের কথাগুলো বাচ্চার জন্য "
                    "সহজ ব্যাখ্যা, অনুবাদ নয় — জিজ্ঞেস করলে আলাদা করে বলুন।",
            "seconds": 40,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V1,
                      "text": "Allah is One. Just One! ☝️"},
        },
        {
            "section": "Verse 2 — Listen",
            "says": "Here is line two. Listen! I will say it two times.",
            "does": "২য় আয়াত ধীরে দুবার পড়ুন। As-Samad-এর 'ṣa' একটু টেনে বলুন।",
            "student": "শোনে।",
            "expected": "চুপ করে শোনা।",
            "correction": "Sit nice and still. Watch my mouth. Listen one "
                          "more time. Allahus-Samad. Lovely!",
            "note": "",
            "seconds": 40,
            "slide": {"kind": "listen", "heading": "Line 2 — Listen",
                      "arabic": V2, "translit": "Allahus-Samad", "text": "👂"},
        },
        {
            "section": "Verse 2 — Repeat",
            "says": "Now you say it with me. Allahus-Samad. Again! "
                    "Allahus-Samad. One more! Now all by yourself.",
            "does": "তিনবার একসাথে, তারপর একবার একা।",
            "student": "আয়াতটি বলে।",
            "expected": "Allahus-Samad — 'ṣa' মোটা ও ভরাট।",
            "correction": "Nearly! This sound is a big fat sound. Make your "
                          "mouth round, like this. Ṣa. Say it — Ṣa. Again — "
                          "Ṣa. Now the line. Allahus-Samad. Mashaa Allah!",
            "note": "ص একটি ভারী হরফ। এটাই এই সূরার সবচেয়ে বেশি ভুল হওয়া "
                    "জায়গা। বাচ্চাকে নিয়মের নাম বলবেন না — শুধু করে দেখান।",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V2, "translit": "Allahus-Samad",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "Verse 2 — Meaning",
            "says": "This line tells us — we ask Allah for everything. Food. "
                    "Water. Everything! Tell me, who gives you your food?",
            "does": "উত্তরের জন্য অপেক্ষা করুন, হাসুন।",
            "student": "উত্তর দেয়।",
            "expected": "Allah — অথবা এমন উত্তর যা আল্লাহর দিকে নেওয়া যায়।",
            "correction": "Your mummy gives you food — yes! And who gives "
                          "your mummy everything? Allah! Say it with me — "
                          "Allah gives us everything.",
            "note": "অর্থ: 'আল্লাহ অমুখাপেক্ষী।' সবকিছু তাঁর মুখাপেক্ষী, তিনি "
                    "কারও নন — এই বয়সে প্রথম অংশটুকুই যথেষ্ট।",
            "seconds": 50,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V2,
                      "text": "We ask Allah for everything. 🤲"},
        },
        {
            "section": "Connect 1 + 2",
            "says": "Now we put line one and line two together. Listen first. "
                    "Now say it with me. Well done! One more time.",
            "does": "১ ও ২ একসাথে পড়ুন, তারপর শিশুর সাথে দুবার।",
            "student": "দুই আয়াত একসাথে বলে।",
            "expected": "দুই আয়াত জোড়া লেগে, মাঝে লম্বা থামা ছাড়া।",
            "correction": "You said line one — lovely! Now line two comes "
                          "next. It starts with Allahu. Off you go!",
            "note": "শুরুতেই জোড়া লাগানো জরুরি — নইলে প্রতিটি আয়াত আলাদা "
                    "দ্বীপের মতো মুখস্থ হয়, এক আয়াত থেকে পরেরটায় যেতে পারে না।",
            "seconds": 60,
            "slide": {"kind": "repeat", "heading": "Both Lines Together",
                      "arabic": V1 + "\n" + V2, "text": "🎤 Together now."},
        },
        {
            "section": "Verse 3 — Listen",
            "says": "Line three. Listen! Two times.",
            "does": "৩য় আয়াত ধীরে দুবার পড়ুন।",
            "student": "শোনে।",
            "expected": "চুপ করে শোনা।",
            "correction": "Ears open! Eyes on me. Listen one more time. "
                          "Lam yalid wa lam yulad. Well listened!",
            "note": "",
            "seconds": 40,
            "slide": {"kind": "listen", "heading": "Line 3 — Listen",
                      "arabic": V3, "translit": "Lam yalid wa lam yulad",
                      "text": "👂"},
        },
        {
            "section": "Verse 3 — Repeat",
            "says": "Your turn! Say it with me. Lam yalid wa lam yulad. "
                    "Again! Lam yalid wa lam yulad. Now all by yourself.",
            "does": "তিনবার একসাথে, তারপর একা। 'yalid'-এ একবার তালি, "
                    "'yulad'-এ দুবার — ক্রমটা মনে থাকে।",
            "student": "আয়াতটি বলে।",
            "expected": "Lam yalid wa lam yulad — এই ক্রমেই।",
            "correction": "Almost! Listen. First one — yalid. Clap once! "
                          "Yalid. Then — yulad. Clap twice! Yulad. Now both. "
                          "Lam yalid wa lam yulad. You did it!",
            "note": "এই দুটি শব্দ উল্টে ফেলাই এই সূরার সবচেয়ে সাধারণ ভুল। "
                    "এখনই ঠিক করে নিন, শেষে নয়।",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V3, "translit": "Lam yalid wa lam yulad",
                      "text": "🎤 Now you say it."},
        },
        {
            "section": "Verse 3 — Meaning",
            "says": "This line tells us — Allah has no mummy. Allah has no "
                    "daddy. Allah has no baby. Allah was always here!",
            "does": "ধীরে ও স্পষ্ট করে বলুন। এই বয়সে এর বেশি নয়।",
            "student": "শোনে।",
            "expected": "'always here' কথাটা বুঝেছে।",
            "correction": "Listen again. No mummy. No daddy. No baby. Allah "
                          "was always here. Say it with me — always here!",
            "note": "অর্থ: 'তিনি কাউকে জন্ম দেননি, তাঁকেও জন্ম দেওয়া হয়নি।' "
                    "গভীর আলোচনায় যাবেন না — একটি স্পষ্ট ছবিই যথেষ্ট।",
            "seconds": 40,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V3,
                      "text": "Allah was always here. ✨"},
        },
        {
            "section": "Verse 4 — Listen",
            "says": "The last line! This one is a bit long. Listen carefully. "
                    "Two times.",
            "does": "৪র্থ আয়াত ধীরে দুবার পড়ুন।",
            "student": "শোনে।",
            "expected": "চুপ করে শোনা।",
            "correction": "It is a long one, isn't it? Do not worry. "
                          "Listen once more. Wa lam yakul-lahu kufuwan ahad. "
                          "We will do it in small bits.",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "listen", "heading": "Line 4 — Listen",
                      "arabic": V4, "translit": "Wa lam yakul-lahu kufuwan ahad",
                      "text": "👂"},
        },
        {
            "section": "Verse 4 — Repeat",
            "says": "Your turn! We will do it in two little bits. First bit — "
                    "Wa lam yakul-lahu. Say it! Again! Now the second bit — "
                    "kufuwan ahad. Say it! Again! Now put them together. Wa "
                    "lam yakul-lahu kufuwan ahad. Mashaa Allah!",
            "does": "দুই টুকরো আলাদা করে, তারপর জোড়া লাগান।",
            "student": "টুকরো দুটি, তারপর পুরো আয়াত বলে।",
            "expected": "Wa lam yakul-lahu kufuwan ahad — এক লাইনে জোড়া।",
            "correction": "That is a hard one! Let us do just the first bit. "
                          "Wa lam yakul-lahu. Good! Just that bit again. "
                          "Lovely. We will do the rest next time.",
            "note": "টুকরো করাই এই আয়াতের চাবি — এটি সবচেয়ে লম্বা। শিশু "
                    "না পারলে জোর করবেন না, টুকরোতেই থামুন।",
            "seconds": 90,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": V4, "translit": "Wa lam yakul-lahu kufuwan ahad",
                      "text": "🎤 Piece by piece."},
        },
        {
            "section": "Verse 4 — Meaning",
            "says": "This line tells us — nobody is like Allah. Nobody! Not "
                    "one. Allah is the best.",
            "does": "'nobody' বলার সময় ধীরে মাথা নাড়ুন।",
            "student": "শোনে।",
            "expected": "'nobody is like Allah' বুঝেছে।",
            "correction": "Listen again. Is anybody like Allah? No! Nobody. "
                          "Say it with me — nobody is like Allah.",
            "note": "অর্থ: 'আর তাঁর সমকক্ষ কেউ নেই।'",
            "seconds": 35,
            "slide": {"kind": "meaning", "heading": "What It Says",
                      "arabic": V4,
                      "text": "Nobody is like Allah. 💚"},
        },
        {
            "section": "Activity",
            "says": "Now a game! Show me four fingers, like me. This finger is "
                    "line one. This one is line two. This one is line three. "
                    "And this one is line four! Touch each finger and say the "
                    "line. Ready? Go!",
            "does": "নিজে করে দেখান, তারপর শিশুকে করতে দিন।",
            "student": "প্রতিটি আয়াতে একটি আঙুল ছুঁয়ে বলে।",
            "expected": "চার আয়াত, চার আঙুল, ঠিক ক্রমে।",
            "correction": "Wait — you are on this finger. Which line is that? "
                          "It starts with Lam. Off you go!",
            "note": "নড়াচড়া ক্রম মনে রাখতে সাহায্য করে — শুধু বারবার বলার "
                    "চেয়ে বেশি। হাতটাই বাচ্চার নিজের মনে করিয়ে দেওয়ার যন্ত্র।",
            "seconds": 90,
            "slide": {"kind": "activity", "heading": "Four-Finger Game",
                      "text": "✋ One finger for one line."},
        },
        {
            "section": "Activity",
            "says": "Now the words will hide! Look — all gone! Can you still "
                    "say it? I know you can. Take your time. Off you go!",
            "does": "খালি পর্দায় যান। ধৈর্য ধরুন — চুপ থাকুন, পাঁচ পর্যন্ত গুনুন।",
            "student": "মুখস্থ থেকে বলে।",
            "expected": "পুরো সূরা, ছোটখাটো থামা চলবে।",
            "correction": "You are doing so well! Here is a little hint. The "
                          "next line starts with Allahu. Now you carry on!",
            "note": "নীরবতাতেই স্মৃতি তৈরি হয়। সাহায্য করার আগে পাঁচ পর্যন্ত "
                    "গুনুন, আর ইশারা দিন কেবল এক শব্দের।",
            "seconds": 90,
            "slide": {"kind": "blank", "heading": "Look & Hide",
                      "text": "🙈 Can you say it by heart?"},
        },
        {
            "section": "Practice",
            "says": "Let us say the whole Surah together now. From the start. "
                    "Nice and slow. Beautiful voice! Ready?",
            "does": "শান্ত গতিতে দুবার একসাথে পড়ুন।",
            "student": "সাথে বলে।",
            "expected": "পুরো সূরা উস্তাদের সাথে।",
            "correction": "Let us go a bit slower. Slow and beautiful. From "
                          "the start again.",
            "note": "ছোটখাটো ভুলে থামবেন না — বরং গতি কমিয়ে দিন।",
            "seconds": 80,
            "slide": {"kind": "repeat", "heading": "All Together",
                      "arabic": V1 + "\n" + V2 + "\n" + V3 + "\n" + V4,
                      "text": "🎤 From the start."},
        },
        {
            "section": "Assessment",
            "says": "Now all by yourself! I will just listen. Take your time. "
                    "You can do it!",
            "does": "একদম চুপ থাকুন। কোথায় থেমে যাচ্ছে মনে রাখুন।",
            "student": "একা বলে।",
            "expected": "চার আয়াত একা, ঠিক ক্রমে, এক শব্দের ইশারাতেই সামলে "
                        "নেওয়া — আজকের জন্য এটাই মুখস্থ হওয়া।",
            "correction": "Mashaa Allah, that was lovely! One tiny thing. "
                          "This word — say it after me. Now you know it!",
            "note": "পড়ার মাঝে থামাবেন না। শেষে কেবল একটি জিনিস বলুন — "
                    "একের বেশি বললে এই বয়সে উৎসাহ নষ্ট হয়।",
            "seconds": 90,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "text": "🎤 I am listening."},
        },
        {
            "section": "Virtue",
            "says": "Do you know a secret? This little Surah is very big with "
                    "Allah! Our Prophet ﷺ told us something amazing. Saying "
                    "it is like reading a third of the Qur'an!",
            "does": "বিস্ময় নিয়ে বলুন। আবার চার আঙুল দেখান — এত ছোট সূরা, "
                    "এত বড় পুরস্কার।",
            "student": "শোনে।",
            "expected": "খুশি — বাড়িতেও পড়ার আগ্রহ।",
            "correction": "It is a small Surah, right? But Allah loves it so "
                          "much. Say it lots at home!",
            "note": "সহীহ: নবী ﷺ বলেছেন কুল হুওয়াল্লাহু আহাদ কুরআনের এক "
                    "তৃতীয়াংশের সমান — সহীহ বুখারী ৫০১৩, সহীহ মুসলিম ৮১১। "
                    "এর বেশি বাড়াবেন না, আর সূত্রহীন কোনো ফাযীলত যোগ করবেন না।",
            "seconds": 45,
            "slide": {"kind": "reminder", "heading": "A Big Secret!",
                      "text": "This little Surah is like reading a third of "
                              "the Qur'an. 🌙"},
        },
        {
            "section": "Review",
            "says": "Mashaa Allah! You learned a whole Surah today! I am so "
                    "proud of you. Now tell me — is Allah one, or many?",
            "does": "মন থেকে প্রশংসা করুন — আজ কোনটা ভালো হয়েছে তা নাম ধরে বলুন।",
            "student": "উত্তর দেয়।",
            "expected": "One!",
            "correction": "Look at my hand. One finger. Just one! Now you "
                          "tell me — how many is Allah? One! Well done!",
            "note": "এই সূরার শিক্ষা: তাওহীদ — আল্লাহ এক, তিনি কারও মুখাপেক্ষী "
                    "নন, আর কেউ তাঁর মতো নয়।",
            "seconds": 50,
            "slide": {"kind": "praise", "heading": "Mashaa Allah!",
                      "text": "You learned a whole Surah today! 🌟"},
        },
        {
            "section": "Homework",
            "says": "Now a little homework. Before I see you again, say this "
                    "Surah three times every day. And say it in your Salah "
                    "too! Can you do that for me? Mashaa Allah!",
            "does": "ধীরে বলুন — পাশে অভিভাবক থাকলে তিনিও যেন লিখে নিতে পারেন।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": "Just three times a day. That is very small, right? "
                          "You can do it!",
            "note": "অভিভাবকের জন্য — শুধু শুনুন আর হাসুন। রোজ অল্প করে "
                    "শোনাই একবারে অনেকক্ষণের চেয়ে ভালো। জোর করা বা বকা নয়; "
                    "আটকে গেলে প্রথম শব্দটা বলে দিন, বাকিটা সে করবে।",
            "seconds": 40,
            "slide": {"kind": "homework", "heading": "Until Next Time",
                      "text": "📖 Say it 3 times every day.\n"
                              "🤲 And in your Salah too."},
        },
        {
            "section": "Closing",
            "says": "Well done today! You worked so hard. Baraka Allahu fik. "
                    "Assalamu alaikum wa rahmatullah!",
            "does": "হাসুন। উষ্ণভাবে শেষ করুন, হঠাৎ নয়।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": "Assalamu alaikum! Say it back to me — Wa alaikumus "
                          "salam. See you next time!",
            "note": "শেষ করার আগে মিলিয়ে নিন: পড়ে শুনিয়েছেন · শিশু শুনেছে · "
                    "চার আয়াতই টুকরো করে করানো হয়েছে · আয়াত জোড়া লাগানো "
                    "হয়েছে · ṣad দেখা হয়েছে · না দেখে বলেছে · অর্থ বলেছে · "
                    "বাড়ির কাজ দেওয়া হয়েছে।",
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
        "<li>Know the letters <b>ا ب ت ث ج ح خ</b> on sight, in any order</li>"
        "<li>Say each letter with the right sound</li>"
        "<li>Tell <b>ت</b> from <b>ث</b>, and <b>ح</b> from <b>خ</b></li>"
        "<li>Read all seven letters in order without help</li>"
        "</ul>"
        "<p><b>How to use this script</b> — every line in “উস্তাদ বলবেন” and "
        "“ভুল হলে” is written to be read out loud, word for word. You do not "
        "need to make up any English yourself. Read it warmly and slowly.</p>"
        "<p><b>Mastery</b> — the child names all seven letters when you point "
        "at them in any order, not only down the list, and keeps ت/ث and ح/خ "
        "apart. Saying the list from memory is <i>not</i> mastery.</p>"
        "<p><b>Revision plan</b> — same day: the point-and-say game once more. "
        "Next class: all seven before the new letters. Then once a week.</p>"
    ),
    "steps": [
        {
            "section": "Welcome",
            "says": "Assalamu alaikum! How are you today? I am so happy to see "
                    "you! Are you ready to learn? Let us go!",
            "does": "হাসুন, হাত নাড়ুন। নাম ধরে একবার ডাকুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": "That is okay! Listen. Assalamu alaikum. Now you say "
                          "it back — Wa alaikumus salam. Lovely!",
            "note": "উষ্ণ শুরু। এখনই পড়ানো নয়।",
            "seconds": 45,
            "slide": {"kind": "title", "heading": "Noorani Qaida — Lesson 1",
                      "arabic": "الحروف المفردة",
                      "text": "Assalamu alaikum!"},
        },
        {
            "section": "Introduction",
            "says": "The Qur'an is made of letters. Today we will learn seven "
                    "letters. Seven! Show me seven fingers. Let us count them. "
                    "One, two, three, four, five, six, seven!",
            "does": "সাতটি আঙুল তুলে একসাথে গুনুন।",
            "student": "সাতটি আঙুল দেখায়, সাথে গোনে।",
            "expected": "সাতটি আঙুল উপরে।",
            "correction": "Let us count together. One, two, three, four, five, "
                          "six, seven. Well done!",
            "note": "এই বয়সে এক দারসে সাতটিই যথেষ্ট। শিশু দ্রুত পারলেও আর "
                    "বাড়াবেন না — পরের দারসে বাকিগুলো আছে।",
            "seconds": 40,
            "slide": {"kind": "title", "heading": "Our First Seven Letters",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "The Qur'an is made of letters."},
        },
        {
            "section": "Ta'awwudh",
            "says": "We always start with Bismillah. Listen to me first. "
                    "Bismillahir-Rahmanir-Rahim. Now say it with me!",
            "does": "প্রথমে একা, তারপর একসাথে।",
            "student": "সাথে বলে।",
            "expected": "Bismillahir-Rahmanir-Rahim.",
            "correction": "Good try! Just the small bit. Bismillah. Again — "
                          "Bismillah. Now all of it. Mashaa Allah!",
            "note": "এখানে উচ্চারণ শোধরাবেন না — অভ্যাসটাই আজ বড়।",
            "seconds": 40,
            "slide": {"kind": "repeat", "heading": "Say With Me",
                      "arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                      "translit": "Bismillahir-Rahmanir-Rahim",
                      "text": "🤲 We always start with this."},
        },
        {
            "section": "Alif — Listen",
            "says": "Look at the screen. This is our first letter. Its name is "
                    "Alif. Listen to me. Alif. Again — Alif.",
            "does": "পর্দার হরফটি দেখিয়ে দুবার স্পষ্ট করে বলুন।",
            "student": "হরফটির দিকে তাকায়, শোনে।",
            "expected": "হরফের দিকে চোখ।",
            "correction": "Look here — at this letter on the screen. Now "
                          "listen again. Alif. Did you hear it? Alif.",
            "note": "মাখরাজ: গলার গভীর থেকে — খোলা, ফাঁকা শব্দ।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Alif — Listen",
                      "arabic": "ا", "translit": "Alif", "text": "👂"},
        },
        {
            "section": "Alif — Repeat",
            "says": "Now your turn! Open your mouth big. Say Alif. Again — "
                    "Alif. One more — Alif. Now all by yourself!",
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "Alif — খোলা, পরিষ্কার শব্দ।",
            "correction": "Nearly! Open your mouth big, like me. Watch. Alif. "
                          "Then stop. Now you — Alif. Lovely!",
            "note": "শেষে গুনগুন এলে বলুন মুখ খুলে থামতে।",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ا", "translit": "Alif", "text": "🎤"},
        },
        {
            "section": "Ba — Listen",
            "says": "Next letter. Its name is Ba. Watch my lips. They close "
                    "together — like this. Ba! Again — Ba.",
            "does": "ঠোঁট দেখিয়ে দুবার বলুন, ক্যামেরার কাছে মুখ আনুন।",
            "student": "ঠোঁটের দিকে তাকায়, শোনে।",
            "expected": "ঠোঁটের দিকে চোখ।",
            "correction": "Look at my lips. Closed! Now open. Ba! Watch again.",
            "note": "মাখরাজ: দুই ঠোঁট। শুধু বলবেন না — করে দেখান, এই দারসটা "
                    "নকল করেই শেখা হয়।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Ba — Listen",
                      "arabic": "ب", "translit": "Ba",
                      "text": "👄 Watch the lips."},
        },
        {
            "section": "Ba — Repeat",
            "says": "Your turn! Close your lips. Now say Ba. Again — Ba. One "
                    "more — Ba. Now all by yourself!",
            "does": "তিনবার একসাথে, তারপর একা। ঠোঁট সত্যিই বন্ধ হচ্ছে কিনা দেখুন।",
            "student": "হরফটি বলে।",
            "expected": "Ba — ঠোঁট পুরোপুরি মিলছে।",
            "correction": "Almost! Your lips must touch. Press them together, "
                          "like this. Now pop them open. Ba! Try again — Ba. "
                          "Mashaa Allah!",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ب", "translit": "Ba", "text": "🎤"},
        },
        {
            "section": "Ta — Listen",
            "says": "Next letter. Its name is Ta. Watch my tongue. It goes up "
                    "and touches my top teeth. It stays inside. Ta! Again — Ta.",
            "does": "ধীরে জিভের অবস্থান দেখান।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "মুখের দিকে মনোযোগ।",
            "correction": "Watch my tongue. Up! And inside. Listen again. Ta.",
            "note": "মাখরাজ: জিভের ডগা উপরের দাঁতের পেছনের মাড়িতে — জিভ "
                    "মুখের ভেতরেই থাকে।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Ta — Listen",
                      "arabic": "ت", "translit": "Ta",
                      "text": "👅 Tongue up, inside."},
        },
        {
            "section": "Ta — Repeat",
            "says": "Your turn! Tongue up. Keep it inside your mouth. Say Ta. "
                    "Again — Ta. One more — Ta. Now all by yourself!",
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "Ta — পরিষ্কার, জিভ মুখের ভেতরে।",
            "correction": "Oh, your tongue came out! That one is a different "
                          "letter. For Ta, keep your tongue inside. Watch me. "
                          "Ta. Now you — Ta. That is it!",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ت", "translit": "Ta", "text": "🎤"},
        },
        {
            "section": "Tha — Listen",
            "says": "Now a new one. Its name is Tha. This time my tongue comes "
                    "out a little. Look — you can see it! Tha. Again — Tha.",
            "does": "দাঁতের ফাঁকে জিভ স্পষ্ট করে দেখান।",
            "student": "মুখের দিকে তাকায়, শোনে।",
            "expected": "মুখের দিকে মনোযোগ।",
            "correction": "Look — my tongue is out. Can you see it? Listen "
                          "again. Tha.",
            "note": "মাখরাজ: জিভের ডগা উপরের ও নিচের সামনের দাঁতের মাঝে।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Tha — Listen",
                      "arabic": "ث", "translit": "Tha",
                      "text": "👅 Tongue comes out."},
        },
        {
            "section": "Tha — Repeat",
            "says": "Your turn! Let your tongue come out a little. Now blow "
                    "softly. Tha. Again — Tha. One more — Tha. All by yourself!",
            "does": "তিনবার একসাথে, তারপর একা। জিভ বেরোচ্ছে কিনা দেখুন।",
            "student": "হরফটি বলে।",
            "expected": "Tha — জিভের ডগা দেখা যাচ্ছে।",
            "correction": "Nearly! Your tongue is still inside. Let it come "
                          "out — like this. Now blow softly. Tha. Try again — "
                          "Tha. Mashaa Allah!",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ث", "translit": "Tha", "text": "🎤"},
        },
        {
            "section": "Compare ت / ث",
            "says": "Listen carefully. Ta … Tha. Ta — the tongue hides inside. "
                    "Tha — the tongue comes out. Now look at the screen. I am "
                    "pointing at this one. Which one is it?",
            "does": "দুটো পরপর বলুন, তারপর একটিতে আঙুল রেখে জিজ্ঞেস করুন।",
            "student": "হরফের নাম বলে।",
            "expected": "যেটিতে আঙুল রেখেছেন, তার নাম।",
            "correction": "Look again. Is the tongue hiding, or coming out? "
                          "Watch my mouth. Ta … Tha. Now you tell me. Which "
                          "one? Well done!",
            "note": "এই জোড়াটাই এই দারসের সবচেয়ে বড় গোলমাল। এখানে সময় দিন — "
                    "আজ ঠিক না হলে পরে গোটা শব্দেও ভুল হতে থাকবে।",
            "seconds": 70,
            "slide": {"kind": "question", "heading": "Which One?",
                      "arabic": "ت      ث",
                      "text": "❓ One hides. One comes out."},
        },
        {
            "section": "Jeem — Listen",
            "says": "Next letter. Its name is Jeem. The middle of my tongue "
                    "pushes up. Jeem! Again — Jeem.",
            "does": "স্পষ্ট করে দুবার বলুন।",
            "student": "শোনে।",
            "expected": "হরফের দিকে মনোযোগ।",
            "correction": "Watch my mouth. My tongue goes up in the "
                          "middle. Listen once more. Jeem. Did you hear it?",
            "note": "মাখরাজ: জিভের মাঝখান তালুর শক্ত অংশে।",
            "seconds": 35,
            "slide": {"kind": "letters", "heading": "Jeem — Listen",
                      "arabic": "ج", "translit": "Jeem", "text": "👂"},
        },
        {
            "section": "Jeem — Repeat",
            "says": "Your turn! Push your tongue up. Now say Jeem. Again — "
                    "Jeem. One more — Jeem. All by yourself!",
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "Jeem — ভরাট, নরম 'ঝ'-এর মতো নয়।",
            "correction": "Almost! Make it a big strong sound. Push your "
                          "tongue up hard. Now let it go. Jeem! Try again — "
                          "Jeem. That is much better!",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ج", "translit": "Jeem", "text": "🎤"},
        },
        {
            "section": "Ḥa — Listen",
            "says": "Next letter. Its name is Ḥa. This one comes from here — "
                    "my throat. Put your hand on your throat, like me. It is "
                    "like warm breath on your hand. Ḥa! Again — Ḥa.",
            "does": "গলায় হাত রাখুন, শিশুও যেন একই কাজ করে।",
            "student": "শোনে, গলায় হাত রাখে।",
            "expected": "গলার দিকে মনোযোগ।",
            "correction": "Put your hand here, on your throat. Feel it? "
                          "Listen again. Ḥa.",
            "note": "মাখরাজ: গলার মাঝখান। মসৃণ ও উষ্ণ — খসখসে নয়।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Ḥa — Listen",
                      "arabic": "ح", "translit": "Ḥa",
                      "text": "🌬️ Warm breath."},
        },
        {
            "section": "Ḥa — Repeat",
            "says": "Your turn! Warm breath from your throat. Say Ḥa. Again — "
                    "Ḥa. One more — Ḥa. All by yourself!",
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "Ḥa — মসৃণ, গলার মাঝ থেকে।",
            "correction": "Nearly! That was a small breath. Make it warmer "
                          "and stronger. Blow on your hand — like this. Ḥa. "
                          "Now you — Ḥa. Mashaa Allah!",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "ح", "translit": "Ḥa", "text": "🎤"},
        },
        {
            "section": "Kha — Listen",
            "says": "Our last letter today! Its name is Kha. This one is a bit "
                    "scratchy. Listen. Kha! Again — Kha.",
            "does": "একটু বাড়িয়ে বলুন যাতে Ḥa-এর সাথে পার্থক্য স্পষ্ট হয়।",
            "student": "শোনে।",
            "expected": "হরফের দিকে মনোযোগ।",
            "correction": "Listen again. It is scratchy — like this. Kha.",
            "note": "মাখরাজ: গলার উপরের অংশ, হালকা খসখসে ভাব।",
            "seconds": 40,
            "slide": {"kind": "letters", "heading": "Kha — Listen",
                      "arabic": "خ", "translit": "Kha",
                      "text": "👂 A bit scratchy."},
        },
        {
            "section": "Kha — Repeat",
            "says": "Your turn! Make it scratchy. Say Kha. Again — Kha. One "
                    "more — Kha. All by yourself!",
            "does": "তিনবার একসাথে, তারপর একা।",
            "student": "হরফটি বলে।",
            "expected": "Kha — গলার উপর থেকে।",
            "correction": "Let us try a game. Pretend the window is cold. Now "
                          "blow on it — haaa. Good! Now make it scratchy at "
                          "the back. Kha! You did it!",
            "note": "",
            "seconds": 45,
            "slide": {"kind": "your_turn", "heading": "Your Turn",
                      "arabic": "خ", "translit": "Kha", "text": "🎤"},
        },
        {
            "section": "Compare ح / خ",
            "says": "Listen carefully. Ḥa … Kha. Ḥa is soft. Kha is scratchy. "
                    "Now say them after me. Ḥa … Kha. Again! Ḥa … Kha. Now you "
                    "say both, all by yourself.",
            "does": "জোড়াটি তিনবার বলুন, তারপর শিশুকে একা বলতে দিন।",
            "student": "দুটি হরফই বলে।",
            "expected": "দুটি স্পষ্টভাবে আলাদা শব্দ।",
            "correction": "They sounded the same! Let us do just one. Ḥa — "
                          "soft and warm. Say it. Lovely! Now the scratchy "
                          "one. Kha. Now both. Ḥa … Kha. Mashaa Allah!",
            "note": "এই দারসের দ্বিতীয় বড় গোলমাল। দুটো এক শোনালে Ḥa-তে ফিরে "
                    "গিয়ে সেটা আগে ঠিক করুন।",
            "seconds": 60,
            "slide": {"kind": "question", "heading": "Soft or Scratchy?",
                      "arabic": "ح      خ",
                      "text": "❓ One is soft. One is scratchy."},
        },
        {
            "section": "Practice",
            "says": "Now all seven letters together. From the start! I will "
                    "point, and we say them together. Ready? Alif, Ba, Ta, "
                    "Tha, Jeem, Ḥa, Kha. Beautiful! One more time.",
            "does": "প্রতিটি হরফে আঙুল রাখুন, একসাথে বলুন। দুবার, শান্তভাবে।",
            "student": "সাথে পড়ে।",
            "expected": "সাতটি হরফ ঠিক ক্রমে।",
            "correction": "Let us go a bit slower. From the start. Alif … Ba "
                          "… good, carry on!",
            "note": "একটি ভুলে থামবেন না — বরং গতি কমান।",
            "seconds": 70,
            "slide": {"kind": "letters", "heading": "All Together",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "🎤 From the start."},
        },
        {
            "section": "Activity",
            "says": "Game time! I will point at a letter. You say its name. "
                    "As fast as you can! Ready? Go!",
            "does": "এলোমেলো ক্রমে ছয়-সাতবার আঙুল রাখুন, ধীরে ধীরে গতি বাড়ান।",
            "student": "প্রতিটি হরফের নাম বলে।",
            "expected": "সঠিক নাম, প্রতি দফায় আরও দ্রুত।",
            "correction": "Ooh, nearly! This one is Tha. Say it — Tha. Good! "
                          "Now watch, I am pointing again… which one?",
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
            "says": "Now all by yourself! I will just listen. Take your time. "
                    "Off you go!",
            "does": "চুপ থাকুন। কোথায় থেমে যাচ্ছে মনে রাখুন।",
            "student": "সাতটি হরফ একা পড়ে।",
            "expected": "সাতটি একা, ت/ث আর ح/خ আলাদা — আজকের জন্য এটাই "
                        "মুখস্থ হওয়া।",
            "correction": "Mashaa Allah, that was lovely! One tiny thing. "
                          "This letter — say it after me. Now you know it!",
            "note": "পড়ার মাঝে থামাবেন না। শেষে কেবল একটি জিনিস বলুন।",
            "seconds": 70,
            "slide": {"kind": "your_turn", "heading": "All By Yourself",
                      "arabic": "ا  ب  ت  ث  ج  ح  خ",
                      "text": "🎤 I am listening."},
        },
        {
            "section": "Homework",
            "says": "Mashaa Allah! You did it! I am so proud of you. Now a "
                    "little homework. Before I see you again, say these seven "
                    "letters five times every day. Can you do that? Lovely!",
            "does": "মন থেকে প্রশংসা করুন — আজ কোনটা ভালো হয়েছে নাম ধরে বলুন। "
                    "বাড়ির কাজটা ধীরে বলুন, অভিভাবক শুনলে যেন লিখে নিতে পারেন।",
            "student": "শোনে, রাজি হয়।",
            "expected": "Yes!",
            "correction": "Just five times a day. It only takes one minute. "
                          "You can do it!",
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
            "says": "Well done today! You worked so hard. Baraka Allahu fik. "
                    "Assalamu alaikum wa rahmatullah!",
            "does": "হাসুন। উষ্ণভাবে শেষ করুন।",
            "student": "সালামের জবাব দেয়।",
            "expected": "Wa alaikumus salam.",
            "correction": "Assalamu alaikum! Say it back to me — Wa alaikumus "
                          "salam. See you next time!",
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
                  status="published", replace=False, topic=None):
    """নমুনা দারসটি ওই কোর্সে তৈরি করে ফেরত দেয় — (দারস, আগে থেকে ছিল কিনা)।

    মডেলগুলো বাইরে থেকে নেওয়া হয় — মাইগ্রেশন ঐতিহাসিক মডেল পাঠায়, ভিউ
    আসলটা। তাই ভবিষ্যতে মডেল বদলালেও পুরনো মাইগ্রেশন ভাঙে না।

    একই কোর্সে একই শিরোনামের দারস আগে থেকে থাকলে —
      replace=False : কিছুই বদলানো হয় না, ওটাই ফেরত যায় (বারবার ডাকা নিরাপদ)
      replace=True  : ধাপগুলো মুছে নতুন লেখা বসে

    ⚠️ replace-এ দারসের সারিটি মোছা হয় না, কেবল তার ধাপগুলো — তাই
    শিক্ষার্থীদের অগ্রগতি (LessonProgress) অক্ষত থাকে।
    """
    data = SAMPLES[key]
    # টপিক দেওয়া থাকলে "আগে থেকে আছে কিনা" ওই টপিক ধরেই দেখি — একই নমুনা
    # আলাদা আলাদা টপিকে বসাতে চাইলে যেন আটকে না যায়
    if topic is not None:
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
            translit=sl.get("translit", ""), text=sl.get("text", ""),
        )
    return lesson, bool(existing)
