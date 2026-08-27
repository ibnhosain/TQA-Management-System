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
        self.assertEqual(len(QAIDA["steps"]), 24)
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
        self.assertEqual(len(new_steps), 24)
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
        self.assertEqual(self.lesson.steps.count(), 24, "অন্য কোর্সের "
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

    LABELS = ("What we learned today", "Practise", "At home")

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

    def test_all_three_sections_are_there(self):
        for les in (self.ikhlas, self.qaida):
            h = self.html(les)
            for label in self.LABELS:
                self.assertIn(label, h, "“%s” অংশটি নেই" % label)

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
