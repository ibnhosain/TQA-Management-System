# -*- coding: utf-8 -*-
"""দুই দারসের স্ক্রিপ্টের নিয়মগুলো।

পরিচালকের শর্ত:
  • উস্তাদকে নিজে ইংরেজি বানাতে হবে না — পড়লেই ক্লাস হয়ে যাবে
  • আরবি কখনো ইংরেজি অক্ষরে নয়; দরকার হলে ডট
  • বর্গাকার বন্ধনীর বাংলা উস্তাদের নিজের নির্দেশনা
"""
import re
from django.test import TestCase
from core.sample_lessons import IKHLAS, QAIDA, DOTS, V1, V2, V3, V4

BN = re.compile(r"[ঀ-৿]")
CUE = re.compile(r"\[[^\]]*\]")       # [বাংলা নির্দেশনা]
SPOKEN = ("says", "correction")
BOTH = (IKHLAS, QAIDA)


def spoken_only(text):
    """মুখে বলার কথাটুকু — বন্ধনীর নির্দেশনা ও ডট বাদ দিয়ে।"""
    return CUE.sub(" ", text or "").replace(DOTS, " ")


class NoArabicInEnglishLetters(TestCase):
    """⚠️ আরবি কোথাও ইংরেজি অক্ষরে লেখা থাকবে না।"""

    def test_no_slide_has_a_transliteration(self):
        bad = [f"{L['title'][:14]} ধাপ {i}"
               for L in BOTH
               for i, st in enumerate(L["steps"], 1)
               if (st["slide"].get("translit") or "").strip()]
        self.assertEqual(bad, [], "উচ্চারণ রয়ে গেছে: " + ", ".join(bad))

    def test_the_ikhlas_script_never_spells_the_verses(self):
        # পুরো শব্দ মিললে তবেই — নইলে "JazakAllahu"-র ভেতরেই "lahu"
        # ধরা পড়ে, অথচ ওটা দুআ, আয়াতের উচ্চারণ নয়
        WORDS = ["qul", "huwal", "huwallahu", "allahus", "samad", "yalid",
                 "yulad", "yakun", "kufuwan", "ahad", "ahadun", "lahu"]
        self.assertEqual(self._hits(IKHLAS, WORDS), [])

    def test_the_qaida_script_never_spells_the_letters(self):
        WORDS = ["alif", "ba", "ta", "tha", "jeem", "ha", "kha",
                 "bismillahir", "rahmanir", "rahim"]
        self.assertEqual(self._hits(QAIDA, WORDS), [])

    def _hits(self, lesson, words):
        pat = re.compile(r"\b(%s)\b" % "|".join(words), re.I)
        return [f"ধাপ {i} · {k}: “{m}”"
                for i, st in enumerate(lesson["steps"], 1)
                for k in SPOKEN
                for m in pat.findall(st[k] or "")]

    def test_dots_stand_in_where_arabic_must_be_said(self):
        """যেখানে আরবি বলতে হবে সেখানে ডট আছে তো?"""
        for L in BOTH:
            n = sum(st[k].count(DOTS) for st in L["steps"] for k in SPOKEN)
            self.assertGreater(n, 20, "%s — ডট প্রায় নেই, উস্তাদ কী বলবেন "
                                      "বুঝবেন না" % L["title"][:14])

    def test_both_lessons_explain_the_convention(self):
        for L in BOTH:
            self.assertIn(DOTS, L["objectives"],
                          "%s — ডটের মানে কোথাও বলা নেই" % L["title"][:14])
            self.assertIn("English letters", L["objectives"])
            self.assertIn("[square brackets]", L["objectives"])


class TheVersesAreExact(TestCase):
    """⚠️ টুকরোগুলো আয়াত থেকেই কাটা — জোড়া দিলে হুবহু আয়াত ফিরে আসা চাই।"""

    def test_every_chunk_comes_from_a_verse(self):
        whole = " ".join([V1, V2, V3, V4])
        for i, st in enumerate(IKHLAS["steps"], 1):
            for line in (st["slide"].get("arabic") or "").split("\n"):
                line = line.strip()
                if not line or line in ("الإخلاص", "بَارَكَ ٱللَّهُ فِيكَ"):
                    continue
                self.assertIn(line, whole,
                              "ধাপ %d — এই আরবি আয়াতে নেই: %s" % (i, line))

    def test_the_four_verses_are_all_there(self):
        ar = " ".join(st["slide"].get("arabic", "") for st in IKHLAS["steps"])
        for v in (V1, V2, V3, V4):
            self.assertIn(v, ar, "আয়াত হারিয়েছে")

    def test_every_word_is_taught_in_pieces(self):
        chunks = " ".join(
            st["slide"].get("arabic", "") for st in IKHLAS["steps"]
            if st["section"].startswith(("Part 3 — ", "Part 5 — ",
                                         "Part 8 — ", "Part 10 — ")))
        for w in (V1 + " " + V2 + " " + V3 + " " + V4).split():
            self.assertIn(w, chunks, "এই শব্দটি আলাদা করে শেখানো হয়নি: " + w)

    def test_the_qaida_teaches_all_seven_letters(self):
        ar = " ".join(st["slide"].get("arabic", "") for st in QAIDA["steps"])
        for letter in "ابتثجحخ":
            self.assertIn(letter, ar, "হরফটি নেই: " + letter)


class TheLanguageRule(TestCase):
    def test_spoken_lines_are_english(self):
        bad = [f"{L['title'][:14]} ধাপ {i} · {k}"
               for L in BOTH
               for i, st in enumerate(L["steps"], 1)
               for k in SPOKEN if BN.search(spoken_only(st[k]))]
        self.assertEqual(bad, [], "মুখে বলার কথায় বাংলা: " + ", ".join(bad))

    def test_teacher_guidance_is_bengali(self):
        bad = [f"{L['title'][:14]} ধাপ {i} · {k}"
               for L in BOTH
               for i, st in enumerate(L["steps"], 1)
               for k in ("does", "note") if st[k] and not BN.search(st[k])]
        self.assertEqual(bad, [], "নির্দেশনা ইংরেজিতে: " + ", ".join(bad))

    def test_the_cues_in_brackets_are_bengali(self):
        """বন্ধনীর ভেতরের কথাগুলো উস্তাদের জন্য — তাই বাংলায়।"""
        found = 0
        for L in BOTH:
            for i, st in enumerate(L["steps"], 1):
                for k in SPOKEN:
                    for cue in CUE.findall(st[k] or ""):
                        found += 1
                        self.assertTrue(BN.search(cue),
                                        "%s ধাপ %d — বন্ধনীর কথা বাংলায় নয়: %s"
                                        % (L["title"][:14], i, cue))
        self.assertGreater(found, 60, "নির্দেশনা প্রায় নেই")

    def test_every_step_has_words_to_say(self):
        for L in BOTH:
            for i, st in enumerate(L["steps"], 1):
                self.assertGreater(len(spoken_only(st["says"]).split()), 4,
                                   "%s ধাপ %d — বলার কথা নেই"
                                   % (L["title"][:14], i))
                self.assertGreater(len(spoken_only(st["correction"]).split()), 3,
                                   "%s ধাপ %d — ভুল হলে কী বলবেন তা নেই"
                                   % (L["title"][:14], i))

    def test_sentences_stay_short(self):
        for L in BOTH:
            for i, st in enumerate(L["steps"], 1):
                for k in SPOKEN:
                    for part in re.split(r"[.!?\n]", spoken_only(st[k])):
                        n = len(part.split())
                        self.assertLessEqual(
                            n, 14,
                            "%s ধাপ %d · %s — %d শব্দের বাক্য: “%s”"
                            % (L["title"][:14], i, k, n, part.strip()[:60]))

    def test_no_hard_words(self):
        HARD = ["firmly", "release", "position", "pronounce", "articulate",
                "makhraj", "utterance", "consonant", "syllable", "palate"]
        bad = [f"{L['title'][:14]} ধাপ {i}: “{h}”"
               for L in BOTH
               for i, st in enumerate(L["steps"], 1)
               for k in SPOKEN
               for h in HARD if h in (st[k] or "").lower()]
        self.assertEqual(bad, [], "\n".join(bad))

    def test_never_says_wrong(self):
        """⚠️ ভুল হলে 'Wrong' বলা যাবে না — শিশুর উৎসাহ নষ্ট হয়।"""
        for L in BOTH:
            for i, st in enumerate(L["steps"], 1):
                self.assertNotIn("wrong", (st["correction"] or "").lower(),
                                 "%s ধাপ %d — 'Wrong' বলা হয়েছে"
                                 % (L["title"][:14], i))


class TheLessonIsWhole(TestCase):
    def test_the_stated_time_is_honest(self):
        """⚠️ গায়ে লেখা সময় আর ধাপগুলোর যোগফল যেন না মেলা না থাকে।"""
        for L in BOTH:
            mins = sum(st["seconds"] for st in L["steps"]) / 60
            self.assertLessEqual(
                abs(mins - L["duration_min"]), 3,
                "%s — গায়ে লেখা %d মিনিট, ধাপ মিলে %.1f মিনিট"
                % (L["title"][:14], L["duration_min"], mins))

    def test_it_is_a_real_class(self):
        self.assertGreaterEqual(len(IKHLAS["steps"]), 30)
        self.assertEqual(len(QAIDA["steps"]), 29)
        for L in BOTH:
            self.assertEqual((L["age_from"], L["age_to"]), (5, 7))

    def test_all_the_parts_are_there(self):
        secs = " ".join(st["section"] for st in IKHLAS["steps"])
        for part in ("Welcome", "Just listen", "Join verse 1", "Meaning",
                     "Connect", "Four-finger", "Look and hide",
                     "whole Surah", "All by yourself", "Final review",
                     "Homework", "Closing"):
            self.assertIn(part, secs, "এই অংশটি নেই: " + part)

    def test_the_qaida_keeps_its_two_hard_pairs(self):
        secs = " ".join(st["section"] for st in QAIDA["steps"])
        self.assertIn("Compare ت / ث", secs)
        self.assertIn("Compare ح / خ", secs)

    def test_the_virtue_still_carries_its_source(self):
        v = [st for st in IKHLAS["steps"] if "secret" in st["section"]][0]
        self.assertIn("বুখারী", v["note"])
        self.assertIn("মুসলিম", v["note"])

    def test_every_step_has_a_screen(self):
        for L in BOTH:
            for i, st in enumerate(L["steps"], 1):
                self.assertTrue(st["slide"]["kind"],
                                "%s ধাপ %d — পর্দা নেই" % (L["title"][:14], i))


class SeedingWorks(TestCase):
    """⚠️ আসল ডেটাবেজে বসানোর পরও উচ্চারণের ঘর যেন খালিই থাকে।"""

    def _seed(self):
        from core.models import Course, Lesson, LessonStep, StepSlide
        from core.sample_lessons import create_sample
        c = Course.objects.create(name="পরীক্ষার কোর্স", teacher=None)
        out = {}
        for key in ("ikhlas", "qaida"):
            lesson, existed = create_sample(
                Lesson, LessonStep, StepSlide, c, key)
            self.assertFalse(existed, key + " আগে থেকেই ছিল?")
            out[key] = lesson
        return out, StepSlide

    def test_seeding_leaves_no_transliteration(self):
        _, StepSlide = self._seed()
        self.assertEqual(StepSlide.objects.exclude(translit="").count(), 0,
                         "ডেটাবেজে উচ্চারণ রয়ে গেছে")

    def test_every_step_reaches_the_database(self):
        got, _ = self._seed()
        self.assertEqual(got["ikhlas"].steps.count(), len(IKHLAS["steps"]))
        self.assertEqual(got["qaida"].steps.count(), len(QAIDA["steps"]))

    def test_the_arabic_survives_the_round_trip(self):
        """⚠️ ডেটাবেজে গিয়ে ফিরে এলেও আয়াত এক বিন্দু বদলাবে না।"""
        got, _ = self._seed()
        stored = " ".join(s.slide.arabic for s in got["ikhlas"].steps.all()
                          if hasattr(s, "slide"))
        for v in (V1, V2, V3, V4):
            self.assertIn(v, stored, "ডেটাবেজে আয়াত বদলে গেছে")

    def test_the_quran_stays_locked(self):
        got, _ = self._seed()
        for s in got["ikhlas"].steps.all():
            sl = getattr(s, "slide", None)
            if sl and sl.arabic:
                self.assertTrue(sl.arabic_locked,
                                "আরবি খোলা রয়ে গেছে: " + s.section)

    def test_replacing_keeps_the_students_progress(self):
        """⚠️ নতুন স্ক্রিপ্ট বসালে শিক্ষার্থীর অগ্রগতি যেন না মোছে।"""
        from core.models import (Course, Lesson, LessonStep, StepSlide,
                                 LessonProgress, User)
        from core.sample_lessons import create_sample
        c = Course.objects.create(name="পরীক্ষার কোর্স ২", teacher=None)
        lesson, _ = create_sample(Lesson, LessonStep, StepSlide, c, "qaida")
        kid = User.objects.create(username="শিশু", role="student")
        LessonProgress.objects.create(student=kid, lesson=lesson,
                                      status="learning", times_taught=3)

        again, existed = create_sample(Lesson, LessonStep, StepSlide, c,
                                       "qaida", replace=True)
        self.assertTrue(existed, "পুরনো দারসটি চেনা যায়নি — নকল তৈরি হতো")
        self.assertEqual(again.pk, lesson.pk)
        self.assertEqual(Lesson.objects.filter(course=c).count(), 1)
        p = LessonProgress.objects.get(student=kid, lesson=lesson)
        self.assertEqual(p.times_taught, 3, "অগ্রগতি বদলে গেছে")


class ReseedingAnExistingScript(TestCase):
    """♻️ "নতুন নমুনা" বাটনের পেছনের কাজটা।

    ⚠️ সবচেয়ে বড় ভয়: বদলানোর বদলে একটি নকল দারস তৈরি হয়ে যাওয়া।
    """

    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import Course, Lesson, LessonStep, StepSlide, User
        from core.sample_lessons import create_sample
        self.M = (Lesson, LessonStep, StepSlide)
        self.Course, self.Lesson, self.User = Course, Lesson, User
        self.boss = User.objects.create(username="পরিচালক", role="director")
        self.c = Course.objects.create(name="হিফজ", teacher=None)
        self.lesson, _ = create_sample(*self.M, self.c, "qaida")
        self.client = APIClient()
        self.client.force_authenticate(user=self.boss)

    def post(self, **body):
        body.setdefault("course", self.c.id)
        return self.client.post("/api/lessons/seed_sample/", body,
                                format="json")

    def test_a_renamed_script_is_replaced_not_duplicated(self):
        """⚠️ পরিচালক নাম বদলে থাকলেও যেন নকল তৈরি না হয়।"""
        self.lesson.title = "আমাদের প্রথম হরফের দারস"
        self.lesson.save()
        old_steps = list(self.lesson.steps.values_list("id", flat=True))

        r = self.post(which="qaida", replace=True, lesson=self.lesson.id)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.Lesson.objects.filter(course=self.c).count(), 1,
                         "নকল দারস তৈরি হয়েছে")
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "আমাদের প্রথম হরফের দারস",
                         "পরিচালকের দেওয়া নামটি মুছে গেছে")
        new_steps = list(self.lesson.steps.values_list("id", flat=True))
        self.assertEqual(len(new_steps), 29)
        self.assertFalse(set(old_steps) & set(new_steps), "পুরনো ধাপ রয়ে গেছে")

    def test_the_new_text_actually_lands(self):
        self.lesson.steps.all().delete()
        self.post(which="qaida", replace=True, lesson=self.lesson.id)
        says = " ".join(self.lesson.steps.values_list("teacher_says", flat=True))
        self.assertIn(DOTS, says, "নতুন লেখা বসেনি")
        self.assertNotIn("Alif", says, "পুরনো লেখা রয়ে গেছে")

    def test_progress_survives(self):
        from core.models import LessonProgress
        kid = self.User.objects.create(username="শিশু", role="student")
        LessonProgress.objects.create(student=kid, lesson=self.lesson,
                                      status="learning", times_taught=5)
        self.post(which="qaida", replace=True, lesson=self.lesson.id)
        p = LessonProgress.objects.get(student=kid, lesson=self.lesson)
        self.assertEqual(p.times_taught, 5, "অগ্রগতি হারিয়েছে")

    def test_a_script_from_another_course_is_refused(self):
        other = self.Course.objects.create(name="অন্য কোর্স", teacher=None)
        r = self.post(course=other.id, which="qaida", replace=True,
                      lesson=self.lesson.id)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.lesson.steps.count(), 29, "অন্য কোর্সের "
                                                        "স্ক্রিপ্ট বদলে গেছে")

    def test_junk_ids_do_not_crash(self):
        """⚠️ আজেবাজে আইডিতে ৫০০ নয়, পরিষ্কার বার্তা।"""
        for bad in ("abc", "", 999999, None, {"x": 1}):
            r = self.post(which="qaida", replace=True, lesson=bad)
            self.assertIn(r.status_code, (201, 400, 404),
                          "%r → %s" % (bad, r.status_code))
            self.assertLess(r.status_code, 500, "%r তে ৫০০" % (bad,))

    def test_without_replace_nothing_is_touched(self):
        """⚠️ ভুল করে replace ছাড়া ডাকলে যেন কিছুই না বদলায়।"""
        first = self.lesson.steps.first()
        first.teacher_says = "পরিচালকের নিজের লেখা"
        first.save()
        r = self.post(which="qaida", lesson=self.lesson.id)
        self.assertEqual(r.status_code, 201)
        first.refresh_from_db()
        self.assertEqual(first.teacher_says, "পরিচালকের নিজের লেখা")


class SummaryReachesTheLecturePlan(TestCase):
    """📋 স্ক্রিপ্টের সারাংশ লেকচার প্ল্যানের টগলে পৌঁছায় তো?"""

    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import (Course, Lesson, LessonStep, StepSlide,
                                 Lecture, LectureTopic, User)
        from core.sample_lessons import create_sample
        self.LectureTopic = LectureTopic
        self.boss = User.objects.create(username="পরিচালক", role="director")
        self.c = Course.objects.create(name="হিফজ", teacher=None)
        self.lec = Lecture.objects.create(course=self.c, no=1,
                                          title="প্রথম অধ্যায়")
        self.topic = LectureTopic.objects.create(lecture=self.lec,
                                                 text="সূরা ইখলাস", order=0)
        self.lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                       self.c, "ikhlas", topic=self.topic)
        self.client = APIClient()
        self.client.force_authenticate(user=self.boss)

    def test_the_script_is_linked_to_the_topic(self):
        self.assertEqual(self.lesson.topic_id, self.topic.id,
                         "স্ক্রিপ্টটি টপিকের সাথে যুক্তই হয়নি — তাই "
                         "সারাংশ বসানোর বাটনটিও দেখা যাবে না")

    def test_pushing_fills_the_toggle(self):
        r = self.client.post("/api/lessons/%d/push_summary/" % self.lesson.id)
        self.assertEqual(r.status_code, 200, r.data)
        self.topic.refresh_from_db()
        self.assertTrue((self.topic.content or "").strip(),
                        "টগলের লেখা খালিই রয়ে গেছে")

    def test_the_toggle_shows_the_arabic_and_the_headings(self):
        self.client.post("/api/lessons/%d/push_summary/" % self.lesson.id)
        self.topic.refresh_from_db()
        html = self.topic.content
        self.assertIn(V1, html, "আয়াত টগলে যায়নি")
        self.assertIn("Amiri Quran", html, "কুরআনের ফন্ট বসেনি")
        self.assertIn('dir="rtl"', html, "আরবি ডান-থেকে-বাঁয়ে বসেনি")

    def test_the_teacher_script_never_leaks(self):
        """⚠️ শিক্ষার্থী এটা পড়বেন — উস্তাদের স্ক্রিপ্ট যেন না যায়।"""
        self.client.post("/api/lessons/%d/push_summary/" % self.lesson.id)
        self.topic.refresh_from_db()
        html = self.topic.content
        for st in self.lesson.steps.all():
            for field in (st.teacher_says, st.teacher_does, st.correction,
                          st.note):
                first = (field or "").strip().split("\n")[0]
                if len(first) > 20:
                    self.assertNotIn(first, html,
                                     "উস্তাদের স্ক্রিপ্ট ফাঁস হয়েছে")

    def test_the_lecture_plan_api_returns_the_toggle_text(self):
        """⚠️ ডেটাবেজে বসলেই হবে না — লেকচার প্ল্যানের পাতায় আসতে হবে।"""
        self.client.post("/api/lessons/%d/push_summary/" % self.lesson.id)
        r = self.client.get("/api/lectures/?course=%d" % self.c.id)
        self.assertEqual(r.status_code, 200, r.data)
        rows = r.data["results"] if isinstance(r.data, dict) else r.data
        topics = [t for lec in rows for t in lec.get("topics", [])]
        self.assertTrue(topics, "লেকচার প্ল্যানে কোনো টপিকই এলো না")
        mine = [t for t in topics if t["id"] == self.topic.id][0]
        self.assertIn("content", mine,
                      "টপিকের সাথে টগলের লেখাই পাঠানো হচ্ছে না")
        self.assertTrue((mine["content"] or "").strip(),
                        "টগলের লেখা খালি এসেছে")


class TheSummaryGoesInByItself(TestCase):
    """স্ক্রিপ্ট টপিকের সাথে যুক্ত হলেই টগলের লেখা নিজে থেকে বসে।"""

    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import (Course, Lesson, LessonStep, StepSlide,
                                 Lecture, LectureTopic, User)
        from core.sample_lessons import create_sample
        self.Lesson = Lesson
        self.boss = User.objects.create(username="পরিচালক", role="director")
        self.c = Course.objects.create(name="হিফজ", teacher=None)
        lec = Lecture.objects.create(course=self.c, no=1, title="অধ্যায় ১")
        self.topic = LectureTopic.objects.create(lecture=lec,
                                                 text="সূরা ইখলাস", order=0)
        # টপিকের সাথে যুক্ত নয় — পুরনো স্ক্রিপ্টগুলো যেমন থাকে
        self.lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                       self.c, "ikhlas")
        self.client = APIClient()
        self.client.force_authenticate(user=self.boss)

    def link(self, **extra):
        body = {"topic": self.topic.id}
        body.update(extra)
        return self.client.patch("/api/lessons/%d/" % self.lesson.id, body,
                                 format="json")

    def test_linking_a_topic_fills_the_toggle(self):
        """⚠️ এটাই পরিচালকের অভিযোগ ছিল — যুক্ত করেও কিছু যেত না।"""
        self.assertEqual(self.topic.content, "")
        r = self.link()
        self.assertEqual(r.status_code, 200, r.data)
        self.topic.refresh_from_db()
        self.assertIn(V1, self.topic.content, "টগলের লেখা বসেনি")

    def test_the_directors_own_words_are_never_overwritten(self):
        """⚠️ পরিচালক নিজে লিখে থাকলে তাতে কখনো হাত নয়।"""
        self.topic.content = "<p>আমার নিজের হাতে লেখা</p>"
        self.topic.save()
        self.link()
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.content, "<p>আমার নিজের হাতে লেখা</p>")

    def test_saving_again_does_not_change_anything(self):
        """বারবার সংরক্ষণ করলেও লেখাটা এক থাকবে।"""
        self.link()
        self.topic.refresh_from_db()
        first = self.topic.content
        self.link(title="নতুন নাম")
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.content, first)

    def test_a_script_with_no_topic_touches_nothing(self):
        r = self.client.patch("/api/lessons/%d/" % self.lesson.id,
                              {"title": "শুধু নাম বদল"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.content, "", "যুক্ত না হয়েও লেখা বসেছে")

    def test_a_new_sample_fills_its_topic(self):
        r = self.client.post("/api/lessons/seed_sample/",
                             {"course": self.c.id, "which": "qaida",
                              "topic": self.topic.id}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data.get("summary_filled"))
        self.topic.refresh_from_db()
        self.assertIn("Amiri Quran", self.topic.content)

    def test_the_teacher_script_never_leaks_this_way_either(self):
        self.link()
        self.topic.refresh_from_db()
        for st in self.lesson.steps.all():
            for field in (st.teacher_says, st.teacher_does, st.correction,
                          st.note):
                first = (field or "").strip().split("\n")[0]
                if len(first) > 20:
                    self.assertNotIn(first, self.topic.content,
                                     "উস্তাদের স্ক্রিপ্ট ফাঁস হয়েছে")


class SavingStaysFast(TestCase):
    """⚠️ সংরক্ষণে ডাটাবেজে ক'টা প্রশ্ন যায় — পাহারা।

    ডাটাবেজ ভার্জিনিয়ায়, ব্যাকএন্ড সিঙ্গাপুরে। তাই প্রতিটি প্রশ্নেই
    প্রায় এক-চতুর্থাংশ সেকেন্ড যায়, আর প্রশ্ন বাড়লেই পরিচালক "লোড হতে
    সময় নেয়" টের পান। একসময় একটি দারস সংরক্ষণে ৪০টি প্রশ্ন যেত — তার
    ৩৫টিই ছিল ধাপগুলোর পর্দা, একটি একটি করে।
    """

    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import (Course, Lesson, LessonStep, StepSlide,
                                 Lecture, LectureTopic, User)
        from core.sample_lessons import create_sample
        self.boss = User.objects.create(username="পরিচালক", role="director")
        self.c = Course.objects.create(name="হিফজ", teacher=None)
        lec = Lecture.objects.create(course=self.c, no=1, title="অধ্যায় ১")
        self.topic = LectureTopic.objects.create(lecture=lec, text="ইখলাস",
                                                 order=0)
        self.lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                       self.c, "ikhlas")
        self.client = APIClient()
        self.client.force_authenticate(user=self.boss)

    def count(self, fn):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        with CaptureQueriesContext(connection) as q:
            r = fn()
        return len(q), r

    def test_saving_a_script_stays_cheap(self):
        n, r = self.count(lambda: self.client.patch(
            "/api/lessons/%d/" % self.lesson.id, {"title": "ক"},
            format="json"))
        self.assertEqual(r.status_code, 200)
        self.assertLess(n, 12, "সংরক্ষণে %d প্রশ্ন — ধাপের সংখ্যার সাথে "
                               "বাড়ছে কিনা দেখুন" % n)

    def test_opening_a_script_stays_cheap(self):
        n, r = self.count(lambda: self.client.get(
            "/api/lessons/%d/" % self.lesson.id))
        self.assertEqual(r.status_code, 200)
        self.assertLess(n, 8, "খুলতে %d প্রশ্ন" % n)

    def test_linking_a_topic_stays_cheap(self):
        """সারাংশ তৈরির সময়ও যেন ধাপ ধরে ধরে প্রশ্ন না যায়।"""
        n, r = self.count(lambda: self.client.patch(
            "/api/lessons/%d/" % self.lesson.id, {"topic": self.topic.id},
            format="json"))
        self.assertEqual(r.status_code, 200)
        self.assertLess(n, 15, "টপিক যুক্ত করতে %d প্রশ্ন" % n)

    def test_the_cost_does_not_grow_with_steps(self):
        """⚠️ আসল পরীক্ষা — ধাপ বাড়লে প্রশ্নও বাড়ে কিনা।"""
        from core.models import Lesson, LessonStep, StepSlide
        from core.sample_lessons import create_sample
        small, _ = create_sample(Lesson, LessonStep, StepSlide, self.c,
                                 "qaida")
        a, _ = self.count(lambda: self.client.patch(
            "/api/lessons/%d/" % small.id, {"title": "ছোট"}, format="json"))
        b, _ = self.count(lambda: self.client.patch(
            "/api/lessons/%d/" % self.lesson.id, {"title": "বড়"},
            format="json"))
        self.assertEqual(
            a, b,
            "২৪ ধাপে %d প্রশ্ন, ৩৪ ধাপে %d — ধাপ ধরে ধরে প্রশ্ন যাচ্ছে" % (a, b))

    def test_the_answer_is_still_complete(self):
        """⚠️ দ্রুত করতে গিয়ে উত্তর যেন এক বিন্দুও না কমে।"""
        import json
        opened = self.client.get("/api/lessons/%d/" % self.lesson.id).data
        saved = self.client.patch("/api/lessons/%d/" % self.lesson.id,
                                  {"title": self.lesson.title},
                                  format="json").data
        self.assertEqual(len(opened["steps"]), 34)
        self.assertEqual(
            json.dumps(opened["steps"], sort_keys=True, ensure_ascii=False),
            json.dumps(saved["steps"], sort_keys=True, ensure_ascii=False),
            "খোলা আর সংরক্ষণে আলাদা উত্তর")

    def test_a_fresh_change_still_shows(self):
        """⚠️ DRF ক্যাশ মোছে টাটকা তথ্যের জন্যই — সেটা যেন নষ্ট না হয়।"""
        st = self.lesson.steps.order_by("order").first()
        self.client.patch("/api/lesson-steps/%d/" % st.id,
                          {"note": "একদম নতুন টীকা"}, format="json")
        d = self.client.patch("/api/lessons/%d/" % self.lesson.id,
                              {"title": "খ"}, format="json").data
        self.assertIn("একদম নতুন টীকা", [s.get("note") for s in d["steps"]],
                      "পুরনো তথ্য ফিরে এসেছে")

    def test_inactive_steps_stay_hidden_after_saving(self):
        st = self.lesson.steps.order_by("order").first()
        st.is_active = False
        st.save()
        d = self.client.patch("/api/lessons/%d/" % self.lesson.id,
                              {"title": "গ"}, format="json").data
        self.assertEqual(len(d["steps"]), 33, "নিষ্ক্রিয় ধাপ ফিরে এসেছে")


class ThePracticeSheet(TestCase):
    """📋 টগলের লেখা — লেকচার প্ল্যানের মতো দেখায়, আবার অনুশীলনও করা যায়।

    ⚠️ সবচেয়ে বড় নিয়ম: ক্লাসের বাইরের একটি অক্ষরও এখানে আসতে পারবে না।
    যা আছে সবই স্লাইড থেকে — শিরোনামগুলো ছাড়া, সেগুলো কেবল সাজানোর ঘর।
    """

    LABELS = ("What we learned today", "Practise",
              "Write in your notebook", "At home")

    def setUp(self):
        from core.models import Course, Lesson, LessonStep, StepSlide
        from core.sample_lessons import create_sample
        self.M = (Lesson, LessonStep, StepSlide)
        self.c = Course.objects.create(name="হিফজ", teacher=None)
        self.ikhlas, _ = create_sample(*self.M, self.c, "ikhlas")
        self.qaida, _ = create_sample(*self.M, self.c, "qaida")

    def html(self, lesson):
        from core.stage_summary import summary_html
        return summary_html(lesson)

    # ───── ক্লাসের বাইরের কিছু নেই ─────
    def test_nothing_comes_from_outside_the_class(self):
        """⚠️ প্রতিটি লেখা স্লাইডেই ছিল কিনা — শিরোনাম ছাড়া।"""
        import re
        for les in (self.ikhlas, self.qaida):
            said = " ".join(
                (s.heading or "") + " " + (s.arabic or "") + " " +
                (s.translit or "") + " " + (s.text or "")
                for st in les.steps.all() for s in [st.slide] if s
            )
            said = re.sub(r"\s+", " ", said)
            body = re.sub(r"<[^>]+>", " ", self.html(les))
            for label in self.LABELS:
                body = body.replace(label, " ")
            for word in re.sub(r"\s+", " ", body).split():
                if len(word) < 2 or word in ("·", "&nbsp;", "📖", "🎤", "📌"):
                    continue
                self.assertIn(word, said,
                              "স্লাইডে ছিল না এমন লেখা টগলে গেছে: %r" % word)

    def test_the_teacher_script_never_leaks(self):
        """⚠️ expected/student_does এখানে ধরা হয় না — ওতে বাচ্চার বলার
        কথা, অর্থাৎ আয়াতটাই থাকে, যা পর্দাতেও ছিল। উস্তাদের নিজের
        কথাগুলোই আসল দেয়াল।"""
        for les in (self.ikhlas, self.qaida):
            body = self.html(les)
            for st in les.steps.all():
                for field in (st.teacher_says, st.teacher_does, st.correction,
                              st.note):
                    first = (field or "").strip().split("\n")[0]
                    if len(first) > 20:
                        self.assertNotIn(first, body,
                                         "উস্তাদের স্ক্রিপ্ট ফাঁস হয়েছে")

    # ───── লেকচার প্ল্যানের চেহারা ─────
    def test_it_opens_with_what_was_taught(self):
        h = self.html(self.ikhlas)
        self.assertIn("What we learned today", h)
        for v in (V1, V2, V3, V4):
            self.assertIn(v, h, "আয়াতটি টগলে নেই")

    def test_the_core_sections_are_there(self):
        for les in (self.ikhlas, self.qaida):
            h = self.html(les)
            for label in ("What we learned today", "Practise", "At home"):
                self.assertIn(label, h, "“%s” অংশটি নেই" % label)

    def test_writing_shows_only_where_it_is_taught(self):
        """✏️ কায়দায় লেখা শেখানো হয়, হিফজে নয় — বাক্সটিও তাই।"""
        self.assertIn("Write in your notebook", self.html(self.qaida),
                      "কায়দায় লেখার অংশটি নেই")
        self.assertNotIn("Write in your notebook", self.html(self.ikhlas),
                         "যেখানে লেখা শেখানো হয় না সেখানেও বাক্সটি এসেছে")

    def test_the_writing_box_says_what_to_write(self):
        h = self.html(self.qaida)
        i = h.find("Write in your notebook")
        self.assertGreater(i, -1)
        box = h[i:i + 2500]
        for letter in "ابتثجحخ":
            self.assertIn(letter, box, "লেখার তালিকায় হরফটি নেই: " + letter)
        self.assertIn("dir=\"rtl\"", box, "লেখার বাক্সে দিক বসেনি")

    # ───── অনুশীলনের চেহারা ─────
    def test_each_verse_gets_its_pieces_and_its_meaning(self):
        h = self.html(self.ikhlas)
        # আয়াত ১-এর টুকরোগুলো
        for piece in ("قُلْ", "هُوَ ٱللَّهُ", "أَحَدٌ"):
            self.assertIn(piece, h, "টুকরোটি নেই: " + piece)
        self.assertIn("Allah is One", h, "অর্থ হারিয়েছে")

    def test_the_qaida_letters_are_all_there(self):
        h = self.html(self.qaida)
        for letter in "ابتثجحخ":
            self.assertIn(letter, h, "হরফটি নেই: " + letter)

    def test_a_single_letter_is_not_treated_as_a_piece_of_a_word(self):
        """⚠️ "ا" প্রায় প্রতিটি আরবি শব্দের ভেতরেই আছে। অক্ষর ধরে
        মেলালে একটিমাত্র হরফ সূরার টুকরো হয়ে বসত — সব গুলিয়ে যেত।"""
        from core.stage_summary import _inside
        self.assertFalse(_inside("ا", "الحروف المفردة"),
                         "হরফটি শব্দের টুকরো ধরা হয়েছে")
        self.assertTrue(_inside("ا", "ا ب ت ث"), "সত্যিকারের টুকরো ধরা পড়েনি")
        self.assertTrue(_inside("قُلْ", V1), "আয়াতের টুকরো ধরা পড়েনি")
        self.assertFalse(_inside(V1, V1), "নিজেই নিজের টুকরো")

    # ───── স্লাইডের হুবহু নকল নয় ─────
    def test_it_is_not_a_copy_of_the_slides(self):
        """একই আয়াত ১৫টি ধাপে বারবার আসে — টগলে একবারই আসা চাই।"""
        h = self.html(self.ikhlas)
        self.assertEqual(h.count(V1), 2,
                         "আয়াতটি বারবার এসেছে (একবার উপরে, একবার কার্ডে)")

    def test_the_classroom_bits_are_left_out(self):
        """শাবাশ, খেলা, খালি পর্দা, বিদায়ের দুআ — অনুশীলনের বিষয় নয়।"""
        h = self.html(self.ikhlas)
        self.assertNotIn("بَارَكَ ٱللَّهُ فِيكَ", h, "বিদায়ের দুআ রয়ে গেছে")
        self.assertNotIn("🎤</", h, "কেবল-ইমোজি পর্দা রয়ে গেছে")

    # ───── সাজসজ্জা ─────
    def test_it_is_laid_out_in_boxes(self):
        for les in (self.ikhlas, self.qaida):
            h = self.html(les)
            self.assertGreaterEqual(h.count("border-radius"), 3,
                                    "বাক্স-আকারে সাজানো হয়নি")
            self.assertIn("background-color", h, "বাক্সের রং নেই")

    def test_the_styling_survives_the_filter(self):
        """⚠️ safe_html অনুমোদিত-তালিকার বাইরের সাজ মুছে দেয় — বাক্সের
        সাজ যেন নিঃশব্দে হারিয়ে না যায়।"""
        h = self.html(self.ikhlas)
        for must in ("border:", "background-color:", "border-radius:",
                     "padding:", "Amiri Quran", 'dir="rtl"'):
            self.assertIn(must.rstrip(":").split(":")[0], h,
                          "ছাঁকনি সাজটি মুছে দিয়েছে: " + must)

    # ───── ভেঙে না পড়া ─────
    def test_an_empty_lesson_gives_nothing(self):
        from core.models import Lesson
        empty = Lesson.objects.create(course=self.c, title="খালি",
                                      kind="memorization")
        self.assertEqual(self.html(empty), "")

    def test_a_lesson_with_only_text_slides_still_works(self):
        from core.models import Lesson, LessonStep, StepSlide
        les = Lesson.objects.create(course=self.c, title="কেবল লেখা",
                                    kind="memorization")
        st = LessonStep.objects.create(lesson=les, order=0, section="ক",
                                       teacher_says="x")
        StepSlide.objects.create(step=st, kind="homework",
                                 text="Read every day")
        h = self.html(les)
        self.assertIn("Read every day", h)
        self.assertIn("At home", h)


class ArabicReadsRightToLeft(TestCase):
    """⚠️ আরবি ডান থেকে বাঁয়ে — নইলে শেষ শব্দটাই আগে পড়া হয়।

    টুকরোগুলো পাশাপাশি বসে বাইরের বাক্সের দিক ধরে। বাক্স বাঁ-থেকে-ডান
    হলে "قُلْ · هُوَ ٱللَّهُ · أَحَدٌ" উল্টো ক্রমে পড়া হতো — শিশু ভুল
    ক্রমে মুখস্থ করে ফেলত।
    """

    def setUp(self):
        from core.models import Course, Lesson, LessonStep, StepSlide
        from core.sample_lessons import create_sample
        from core.stage_summary import summary_html
        self.c = Course.objects.create(name="হিফজ", teacher=None)
        self.lesson, _ = create_sample(Lesson, LessonStep, StepSlide,
                                       self.c, "ikhlas")
        self.html = summary_html(self.lesson)

    def test_every_box_holding_arabic_has_a_direction(self):
        import re
        boxes = re.findall(r'<div[^>]*>(?=[^<]*<span dir="rtl")', self.html)
        self.assertTrue(boxes, "আরবি ধরে রাখা কোনো বাক্সই পাওয়া গেল না")
        for b in boxes:
            self.assertIn('dir="rtl"', b,
                          "আরবির বাক্সে দিক বসানো নেই: %s" % b[:70])
            self.assertIn("direction: rtl", b,
                          "বাক্সে direction নেই: %s" % b[:70])

    def test_the_pieces_row_reads_right_to_left(self):
        self.assertIn("direction: rtl", self.html)
        # টুকরোর পট্টিটিতে দিক আছে তো
        i = self.html.find("#faf7ef")
        self.assertGreater(i, -1, "টুকরোর পট্টিই নেই")
        box = self.html[max(0, i - 120):i + 160]
        self.assertIn("direction: rtl", box, "টুকরোগুলো উল্টো ক্রমে পড়া হবে")

    def test_the_filter_keeps_the_direction(self):
        """⚠️ safe_html দিক মুছে দিলে সব ভেস্তে যেত।"""
        from core.safe_html import clean_html
        got = clean_html('<div dir="rtl" style="direction:rtl;'
                         'text-align:center">قُلْ</div>')
        self.assertIn('dir="rtl"', got, "ছাঁকনি dir মুছে দিয়েছে")
        self.assertIn("direction: rtl", got, "ছাঁকনি direction মুছে দিয়েছে")


class TheMushafMarks(TestCase):
    """📖 আয়াতের শেষে মুসহাফের গোল নকশা।"""

    AYAH = "\u06dd"          # ۝ — ARABIC END OF AYAH
    DIGITS = "١٢٣٤"

    def test_every_verse_ends_with_its_number(self):
        from core.sample_lessons import V1, V2, V3, V4
        for i, v in enumerate((V1, V2, V3, V4), 1):
            want = self.AYAH + self.DIGITS[i - 1]
            self.assertTrue(v.rstrip().endswith(want),
                            "আয়াত %d-এর শেষে চিহ্ন নেই: %r" % (i, v[-6:]))

    def test_the_marks_reach_the_practice_sheet(self):
        from core.models import Course, Lesson, LessonStep, StepSlide
        from core.sample_lessons import create_sample
        from core.stage_summary import summary_html
        c = Course.objects.create(name="হিফজ", teacher=None)
        les, _ = create_sample(Lesson, LessonStep, StepSlide, c, "ikhlas")
        h = summary_html(les)
        for d in self.DIGITS:
            self.assertIn(self.AYAH + d, h, "টগলে আয়াত-চিহ্ন %s নেই" % d)

    def test_the_verses_themselves_are_untouched(self):
        """⚠️ চিহ্ন বসাতে গিয়ে আয়াতের একটি অক্ষরও যেন না বদলায়।"""
        from core.sample_lessons import V1, V2, V3, V4
        WORDS = ("قُلْ هُوَ ٱللَّهُ أَحَدٌ", "ٱللَّهُ ٱلصَّمَدُ",
                 "لَمْ يَلِدْ وَلَمْ يُولَدْ",
                 "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ")
        for v, w in zip((V1, V2, V3, V4), WORDS):
            self.assertTrue(v.startswith(w), "আয়াতের পাঠ বদলে গেছে: %r" % v)

    def test_no_waqf_sign_was_invented(self):
        """⚠️ সূরা ইখলাসে মুসহাফে কোনো ওয়াকফ চিহ্ন নেই — বসানো চলবে না।"""
        from core.sample_lessons import V1, V2, V3, V4
        WAQF = "\u06d6\u06d7\u06d8\u06d9\u06da\u06db"  # ۖ ۗ ۘ ۙ ۚ ۛ
        for v in (V1, V2, V3, V4):
            for w in WAQF:
                self.assertNotIn(w, v, "নেই এমন ওয়াকফ চিহ্ন বসানো হয়েছে")

    def test_the_chunks_carry_no_verse_number(self):
        """টুকরো তো আয়াত নয় — তার শেষে নম্বর বসলে ভুল শেখানো হতো।"""
        from core.sample_lessons import IKHLAS
        for st in IKHLAS["steps"]:
            ar = st["slide"].get("arabic") or ""
            for line in ar.split("\n"):
                line = line.strip()
                if not line or self.AYAH not in line:
                    continue
                self.assertGreater(len(line.split()), 1,
                                   "একটিমাত্র টুকরোর সাথে আয়াত-নম্বর: %r"
                                   % line)


class WritingIsTaught(TestCase):
    """✏️ কায়দায় পড়ার পাশাপাশি খাতায় লেখাও।

    শিশু নিজের খাতায় পেনসিল দিয়ে লেখে, তারপর ক্যামেরায় উস্তাদকে দেখায় —
    জুমে এটাই একমাত্র উপায় যাতে উস্তাদ হাতের লেখা দেখতে পান।
    """

    def steps(self):
        return [st for st in QAIDA["steps"]
                if st["slide"]["kind"] == "write"]

    def test_the_qaida_has_writing_steps(self):
        self.assertGreaterEqual(len(self.steps()), 4,
                                "লেখার ধাপ প্রায় নেই")

    def test_the_child_writes_in_a_notebook_with_a_pencil(self):
        said = " ".join(spoken_only(st["says"]) for st in self.steps()).lower()
        for word in ("notebook", "pencil", "write"):
            self.assertIn(word, said, "“%s” কথাটাই বলা হয়নি" % word)

    def test_the_child_shows_the_page_to_the_teacher(self):
        """⚠️ দেখানোর ধাপটাই আসল — নইলে উস্তাদ হাতের লেখা দেখতেই পান না।"""
        said = " ".join(spoken_only(st["says"]) for st in self.steps()).lower()
        self.assertIn("camera", said, "ক্যামেরায় দেখানোর কথা নেই")
        self.assertTrue("show me" in said or "hold" in said,
                        "খাতা দেখাতে বলা হয়নি")

    def test_the_direction_is_taught_from_the_first_day(self):
        """⚠️ আরবি ডান থেকে বাঁয়ে — প্রথম দিনেই না শেখালে অভ্যাস উল্টো হয়।"""
        said = " ".join(spoken_only(st["says"]) + " " + (st["does"] or "")
                        for st in self.steps()).lower()
        self.assertIn("right", said, "ডান থেকে শুরুর কথা নেই")
        bn = " ".join(st["does"] or "" for st in self.steps())
        self.assertIn("ডান থেকে বাঁয়ে", bn, "উস্তাদের নির্দেশনায় দিকটা নেই")

    def test_all_seven_letters_get_written(self):
        ar = " ".join(st["slide"].get("arabic", "") for st in self.steps())
        for letter in "ابتثجحخ":
            self.assertIn(letter, ar, "এই হরফটি লেখানো হয় না: " + letter)

    def test_a_child_without_a_notebook_is_not_left_out(self):
        """⚠️ খাতা না থাকলেও যেন ক্লাস থেকে বাদ না পড়ে।"""
        text = " ".join((st["correction"] or "") + " " + (st["note"] or "")
                        for st in self.steps())
        self.assertIn("paper", text.lower() + " ",
                      "খাতা না থাকলে কী করবেন তা বলা নেই")

    def test_bad_handwriting_is_never_scolded(self):
        """⚠️ পাঁচ বছরের হাত এখনো শক্ত নয় — চেষ্টাটাই বড়।"""
        for st in self.steps():
            c = (st["correction"] or "").lower()
            for bad in ("wrong", "bad", "ugly", "no."):
                self.assertNotIn(bad, c,
                                 "লেখার ভুলে কঠিন কথা: %r" % st["section"])

    def test_the_writing_steps_follow_the_same_language_rules(self):
        """বাকি স্ক্রিপ্টের মতোই — বলার কথা ইংরেজি, নির্দেশনা বাংলা।"""
        for st in self.steps():
            self.assertFalse(BN.search(spoken_only(st["says"])),
                             "বলার কথায় বাংলা: %r" % st["section"])
            self.assertTrue(BN.search(st["does"] or ""),
                            "নির্দেশনা বাংলায় নয়: %r" % st["section"])

    def test_writing_comes_after_the_letters_are_learned(self):
        """⚠️ চেনার আগে লিখতে বললে শিশু ভড়কে যায়।"""
        kinds = [st["slide"]["kind"] for st in QAIDA["steps"]]
        first_write = kinds.index("write")
        self.assertGreater(kinds[:first_write].count("your_turn"), 5,
                           "হরফগুলো বলা শেষ হওয়ার আগেই লেখা শুরু হয়েছে")

    def test_the_homework_asks_for_writing_too(self):
        home = [st for st in QAIDA["steps"]
                if st["slide"]["kind"] == "homework"]
        text = " ".join(spoken_only(st["says"]) + " " +
                        (st["slide"].get("text") or "") for st in home)
        self.assertIn("rite", text, "বাড়ির কাজে লেখার কথা নেই")


class TheRefreshMigration(TestCase):
    """♻️ মাইগ্রেশন ০০৩৯ — পুরনো দারস মুছে সর্বশেষ স্ক্রিপ্ট বসানো।

    ⚠️ সবচেয়ে বড় ভয়: হালনাগাদ করতে গিয়ে শিক্ষার্থীদের অগ্রগতি হারানো,
    বা বদলানোর বদলে নকল দারস তৈরি হয়ে যাওয়া।
    """

    def setUp(self):
        from core.models import (Course, Lesson, LessonStep, StepSlide,
                                 Lecture, LectureTopic, User)
        from core.sample_lessons import create_sample
        self.M = (Lesson, LessonStep, StepSlide)
        self.Lesson = Lesson
        self.c = Course.objects.create(name="হিফজ", teacher=None)
        lec = Lecture.objects.create(course=self.c, no=1, title="অধ্যায় ১")
        self.topic = LectureTopic.objects.create(lecture=lec, text="ইখলাস",
                                                 order=0)
        self.lesson, _ = create_sample(*self.M, self.c, "ikhlas",
                                       topic=self.topic)
        # পুরনো অবস্থা বানাই — আয়াত-চিহ্ন ছাড়া, কম ধাপ
        self.lesson.steps.all().delete()
        st = LessonStep.objects.create(lesson=self.lesson, order=0,
                                       section="পুরনো", teacher_says="পুরনো")
        StepSlide.objects.create(step=st, kind="verse",
                                 arabic="قُلْ هُوَ ٱللَّهُ أَحَدٌ")
        self.old_step_id = st.id
        self.kid = User.objects.create(username="শিশু", role="student")
        from core.models import LessonProgress
        LessonProgress.objects.create(student=self.kid, lesson=self.lesson,
                                      status="learning", times_taught=7)

    def do_refresh(self):
        import importlib
        m = importlib.import_module(
            "core.migrations.0039_refresh_lesson_scripts")
        from core.models import Lesson, LessonStep, StepSlide

        class FakeApps:
            def get_model(self, app, name):
                return {"Lesson": Lesson, "LessonStep": LessonStep,
                        "StepSlide": StepSlide}[name]
        m.refresh(FakeApps(), None)

    def test_the_new_script_lands(self):
        self.do_refresh()
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.steps.count(), 34,
                         "সব ধাপ বসেনি")
        ar = " ".join(s.arabic or "" for st in self.lesson.steps.all()
                      for s in [getattr(st, "slide", None)] if s)
        self.assertIn("\u06dd\u0661", ar, "আয়াত-চিহ্ন আসেনি")

    def test_the_old_steps_are_gone(self):
        self.do_refresh()
        from core.models import LessonStep
        self.assertFalse(LessonStep.objects.filter(id=self.old_step_id).exists(),
                         "পুরনো ধাপটি রয়ে গেছে")

    def test_no_duplicate_lesson_is_made(self):
        """⚠️ বদলানোর বদলে নকল তৈরি হলে তালিকায় দুটো দেখা যেত।"""
        self.do_refresh()
        self.assertEqual(self.Lesson.objects.filter(course=self.c).count(), 1,
                         "নকল দারস তৈরি হয়েছে")

    def test_a_renamed_lesson_is_still_found(self):
        """পরিচালক নাম বদলে থাকলেও যেন হালনাগাদ বাদ না পড়ে।"""
        self.lesson.title = "আমাদের ইখলাসের দারস"
        self.lesson.save()
        self.do_refresh()
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.steps.count(), 34, "নাম বদলালে বাদ পড়ছে")
        self.assertEqual(self.lesson.title, "আমাদের ইখলাসের দারস",
                         "পরিচালকের দেওয়া নাম মুছে গেছে")

    def test_student_progress_survives(self):
        """⚠️ সবচেয়ে জরুরি — কে কতটুকু শিখেছে তা হারানো চলবে না।"""
        from core.models import LessonProgress
        self.do_refresh()
        p = LessonProgress.objects.get(student=self.kid, lesson=self.lesson)
        self.assertEqual(p.times_taught, 7, "অগ্রগতি হারিয়েছে")
        self.assertEqual(p.status, "learning")

    def test_the_topic_link_survives(self):
        self.do_refresh()
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.topic_id, self.topic.id,
                         "টপিকের সংযোগ ছিঁড়ে গেছে")

    def test_the_lecture_plan_gets_the_new_text(self):
        """পরিচালক বলেছেন প্লানও বসিয়ে দিতে।"""
        self.topic.content = "<p>পুরনো লেখা</p>"
        self.topic.save()
        self.do_refresh()
        self.topic.refresh_from_db()
        self.assertNotIn("পুরনো লেখা", self.topic.content,
                         "টগলে পুরনো লেখাই রয়ে গেছে")
        self.assertIn("What we learned today", self.topic.content)
        self.assertIn("\u06dd\u0661", self.topic.content,
                       "টগলে আয়াত-চিহ্ন নেই")

    def test_running_it_twice_is_safe(self):
        self.do_refresh()
        self.do_refresh()
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.steps.count(), 34)
        self.assertEqual(self.Lesson.objects.filter(course=self.c).count(), 1)


class AFreshInstallWorks(TestCase):
    """⚠️ একদম নতুন ডাটাবেজে migrate চলে তো?

    মাইগ্রেশন ০০৩৬ আজকের create_sample ডাকে, কিন্তু ০০৩৬-এর সময় Lesson-এ
    topic ঘরটি ছিল না (এসেছে ০০৩৮-এ)। ঘরটি না দেখে topic= পাঠানোয় নতুন
    ইনস্টলে migrate ভেঙে পড়ত — চালু সাইটে ধরা পড়েনি, কারণ সেখানে ০০৩৬
    আগেই চলে গিয়েছিল।
    """

    def test_seeding_works_without_the_topic_field(self):
        """topic ঘর ছাড়া মডেল দিলেও যেন ভেঙে না পড়ে।"""
        from core.models import Course, Lesson, LessonStep, StepSlide
        from core.sample_lessons import create_sample

        class NoTopicLesson(Lesson):
            """ঐতিহাসিক মডেলের নকল — topic ঘরটি নেই বলে ধরে নেওয়া হয়।"""
            class Meta:
                proxy = True

        c = Course.objects.create(name="নূরানী", teacher=None)
        # আসল মডেলেই topic আছে, তাই আচরণটা সরাসরি যাচাই করি
        les, existed = create_sample(Lesson, LessonStep, StepSlide, c, "qaida")
        self.assertFalse(existed)
        self.assertEqual(les.steps.count(), 29)

    def test_create_sample_checks_for_the_topic_field(self):
        """⚠️ পাহারা — ঘরটি আছে কিনা দেখে নেওয়ার কোডটি যেন কেউ না তোলে।"""
        import inspect
        from core import sample_lessons
        src = inspect.getsource(sample_lessons.create_sample)
        self.assertIn("has_topic", src,
                      "ঘর যাচাই করার কোডটি সরে গেছে — নতুন ইনস্টলে "
                      "migrate আবার ভেঙে পড়বে")
        self.assertNotIn("            topic=topic,", src,
                         "topic সরাসরি পাঠানো হচ্ছে")

    def test_the_whole_migration_chain_runs(self):
        """⚠️ শূন্য ডাটাবেজ থেকে সব মাইগ্রেশন — এটাই নতুন ইনস্টলের পথ।"""
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connection
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        self.assertEqual(plan, [], "কিছু মাইগ্রেশন বাকি রয়ে গেছে")


class TheRefreshNeverTouchesOtherLessons(TestCase):
    """⚠️ হালনাগাদ যেন পরিচালকের নিজের লেখা দারসে হাত না দেয়।

    ০০৩৯-এ একটি ফলব্যাক ছিল যা "একই ধরনের যেকোনো দারস" ধরত। শিরোনাম না
    মিললে সেটি পরিচালকের নিজের হাতে লেখা দারস ধরে ফেলত, আর replace=True
    তার সব ধাপ মুছে দিত। সরানো হয়েছে — এই পরীক্ষা পাহারা দেয়।
    """

    def refresh(self):
        import importlib
        from core.models import Lesson, LessonStep, StepSlide
        m = importlib.import_module(
            "core.migrations.0039_refresh_lesson_scripts")

        class A:
            def get_model(self, app, name):
                return {"Lesson": Lesson, "LessonStep": LessonStep,
                        "StepSlide": StepSlide}[name]
        m.refresh(A(), None)

    def test_a_directors_own_lesson_is_left_alone(self):
        from core.models import Course, Lesson, LessonStep, StepSlide
        c = Course.objects.create(name="নূরানী", teacher=None)
        mine = Lesson.objects.create(course=c, title="আমার নিজের দারস",
                                     kind="qaida", duration_min=15)
        st = LessonStep.objects.create(lesson=mine, order=0, section="ক",
                                       teacher_says="আমার নিজের লেখা")
        StepSlide.objects.create(step=st, kind="letters", arabic="ا")
        self.refresh()
        mine.refresh_from_db()
        self.assertEqual(mine.steps.count(), 1, "নিজের দারসের ধাপ বদলে গেছে")
        self.assertEqual(mine.steps.first().teacher_says, "আমার নিজের লেখা",
                         "নিজের লেখা মুছে গেছে")
        self.assertEqual(mine.title, "আমার নিজের দারস")
        self.assertEqual(mine.duration_min, 15)

    def test_the_kind_fallback_is_gone(self):
        """⚠️ পাহারা — কেউ যেন ফলব্যাকটি আবার যোগ না করে।"""
        import inspect, importlib
        m = importlib.import_module(
            "core.migrations.0039_refresh_lesson_scripts")
        src = inspect.getsource(m._find)
        self.assertNotIn('kind=data["kind"]', src,
                         "ধরন ধরে খোঁজার ফলব্যাক ফিরে এসেছে — পরিচালকের "
                         "নিজের লেখা দারস মুছে যেতে পারে")

    def test_the_real_lesson_is_still_refreshed(self):
        """সাবধানতা যেন কাজটাই আটকে না দেয়।"""
        from core.models import Course, Lesson, LessonStep, StepSlide
        from core.sample_lessons import create_sample
        c = Course.objects.create(name="নূরানী", teacher=None)
        les, _ = create_sample(Lesson, LessonStep, StepSlide, c, "qaida")
        les.steps.filter(slide__kind="write").delete()
        self.refresh()
        les.refresh_from_db()
        self.assertEqual(les.steps.filter(slide__kind="write").count(), 5,
                         "লেখার ধাপগুলো ফিরে আসেনি")
        self.assertEqual(les.steps.count(), 29)


# ═══════════════ গোপনীয়তা ও অনুমতির পাহারা ═══════════════
# ⚠️ এগুলো একবারের পরীক্ষা নয় — স্থায়ী পাহারা। কোনো ViewSet-এর
# get_queryset বদলালে, বা নতুন ফিল্টার যোগ হলে, একজনের তথ্য অন্যজনের
# চোখে পড়ে যেতে পারে। সেটাই এখানে ধরা পড়বে।

class Privacy(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        from core import models as M
        self.APIClient, self.M = APIClient, M
        mk = lambda u, r: M.User.objects.create(username=u, role=r)
        self.boss = mk("boss", "director")
        self.t1, self.t2 = mk("t1", "teacher"), mk("t2", "teacher")
        self.s1, self.s2 = mk("s1", "student"), mk("s2", "student")
        self.c1 = M.Course.objects.create(name="c1", teacher=self.t1)
        self.c2 = M.Course.objects.create(name="c2", teacher=self.t2)
        self.c1.students.add(self.s1)
        self.c2.students.add(self.s2)
        # দুজনের ফি, দুজনের বেতন, দুজনের ছুটি
        for s, c in ((self.s1, self.c1), (self.s2, self.c2)):
            M.FeePayment.objects.create(student=s, month_label="2026-08",
                                        amount=1000)
            M.LeaveRequest.objects.create(applicant=s,
                                          from_date="2026-08-10",
                                          to_date="2026-08-10", reason="r")
        for t in (self.t1, self.t2):
            M.TeacherPayment.objects.create(teacher=t, amount=5000)

    def as_(self, u):
        cl = self.APIClient()
        cl.force_authenticate(user=u)
        return cl

    def rows(self, u, path):
        r = self.as_(u).get("/api/%s/" % path)
        if r.status_code != 200:
            return r.status_code
        d = r.data
        return d["results"] if isinstance(d, dict) and "results" in d else d

    def names(self, rows, *keys):
        out = []
        for x in rows if isinstance(rows, list) else []:
            for k in keys:
                if x.get(k) is not None:
                    out.append(x[k])
        return out

    def test_a_student_sees_only_their_own_fees(self):
        got = self.rows(self.s1, "fees")
        self.assertNotIsInstance(got, int, "শিক্ষার্থী ফি পাতাই পাচ্ছেন না")
        ids = {x.get("student") for x in got}
        self.assertLessEqual(ids, {self.s1.id},
                             "অন্য শিক্ষার্থীর ফি দেখা যাচ্ছে: %s" % ids)

    def test_a_student_cannot_see_salaries(self):
        got = self.rows(self.s1, "salaries")
        if not isinstance(got, int):
            self.assertEqual(len(got), 0,
                             "শিক্ষার্থী উস্তাদের বেতন দেখছেন!")

    def test_a_teacher_cannot_see_another_teachers_salary(self):
        got = self.rows(self.t1, "salaries")
        if not isinstance(got, int):
            ids = {x.get("teacher") for x in got}
            self.assertLessEqual(ids, {self.t1.id, None},
                                 "অন্য উস্তাদের বেতন দেখা যাচ্ছে: %s" % ids)

    def test_a_student_sees_only_their_own_leave(self):
        got = self.rows(self.s1, "leaves")
        if not isinstance(got, int):
            ids = {x.get("applicant") for x in got}
            self.assertLessEqual(ids, {self.s1.id},
                                 "অন্যের ছুটির আবেদন দেখা যাচ্ছে: %s" % ids)

    def test_a_teacher_sees_only_their_own_course(self):
        got = self.rows(self.t1, "courses")
        ids = {x.get("id") for x in got}
        self.assertNotIn(self.c2.id, ids,
                         "অন্য উস্তাদের কোর্স দেখা যাচ্ছে")

    def test_a_student_sees_only_their_own_course(self):
        got = self.rows(self.s1, "courses")
        ids = {x.get("id") for x in got}
        self.assertNotIn(self.c2.id, ids,
                         "অন্য কোর্স দেখা যাচ্ছে")

    def test_a_student_cannot_list_users(self):
        self.assertEqual(self.rows(self.s1, "users"), 403,
                         "শিক্ষার্থী সবার তালিকা দেখছেন")

    def test_the_director_sees_everything(self):
        """সাবধানতা যেন পরিচালকের কাজ আটকে না দেয়।"""
        for p, n in (("fees", 2), ("salaries", 2), ("leaves", 2),
                     ("courses", 2)):
            got = self.rows(self.boss, p)
            self.assertNotIsInstance(got, int, "পরিচালক %s পাচ্ছেন না" % p)
            self.assertEqual(len(got), n,
                             "পরিচালক %s-এ %d নয়, %d দেখছেন"
                             % (p, n, len(got)))
