# -*- coding: utf-8 -*-
"""🔒 এক উস্তাদ যেন আরেক উস্তাদের ক্লাস ও শিক্ষার্থী না দেখেন।

পরিচালকের নিয়ম: **কোন শিক্ষার্থী কোন উস্তাদের কাছে পড়ে — হিসাব কেবল
সেটাই।** এক কোর্সে দুজন উস্তাদ পড়ালেও একজন আরেকজনের রুটিন, ক্লাস বা
শিক্ষার্থীর নাম দেখতে পাবেন না।

⚠️ দুটি আলাদা ফাঁক ছিল —

১. ক্লাসের তালিকা কোর্স ধরে ছাঁকা হতো: Q(course__teacher=u)। কোর্সের
   নির্ধারিত উস্তাদ হলেই ওই কোর্সের *সব* ক্লাস দেখা যেত, অন্য উস্তাদের
   ক্লাসসহ। রুটিনে এই শর্তটি ছিল না — তাই দুটোর আচরণও আলাদা ছিল।

২. নামের তালিকা কখনোই ছাঁকা হতো না। নিজের একজন শিক্ষার্থী আছে বলে
   কোনো রুটিন দেখতে পেলে, সেই রুটিনের *সব* শিক্ষার্থীর নাম চলে আসত —
   অন্য উস্তাদের শিক্ষার্থীদের নামও।
"""
from django.test import TestCase


class OneTeacherCannotSeeAnothers(TestCase):

    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import (User, Course, Routine, ClassSession)
        self.Routine, self.ClassSession = Routine, ClassSession
        self.boss = User.objects.create(username="পরিচালক", role="director",
                                        name_bn="পরিচালক")
        self.a = User.objects.create(username="ustadA", role="teacher",
                                     name_bn="উস্তাদ-ক")
        self.b = User.objects.create(username="ustadB", role="teacher",
                                     name_bn="উস্তাদ-খ")
        # ⚠️ কোর্সের নির্ধারিত উস্তাদ ক — এখান থেকেই ফাঁকটা আসত
        self.c = Course.objects.create(name="Easy Noorani Qaida",
                                       teacher=self.a)
        self.s1 = User.objects.create(username="s1", role="student",
                                      name_bn="ক-এর ছাত্র", teacher=self.a)
        self.s2 = User.objects.create(username="s2", role="student",
                                      name_bn="খ-এর ছাত্র", teacher=self.b)
        self.c.students.add(self.s1, self.s2)

        # খ-এর নিজের রুটিন ও ক্লাস — কেবল খ-এর ছাত্র
        self.rb = Routine.objects.create(course=self.c, teacher=self.b,
                                         days=[1], time="10:00",
                                         zoom_link="https://z/b")
        self.rb.students.add(self.s2)
        self.xb = ClassSession.objects.create(course=self.c, teacher=self.b,
                                              date="2026-09-14", time="10:00",
                                              zoom_link="https://z/b")
        self.xb.students.add(self.s2)
        self.cl = APIClient()

    def as_(self, u):
        self.cl.force_authenticate(user=u)
        return self.cl

    def ids(self, path, u):
        r = self.as_(u).get(path)
        self.assertEqual(r.status_code, 200, r.data)
        return {x["id"] for x in r.data}

    def row(self, path, u, rid):
        r = self.as_(u).get(path)
        self.assertEqual(r.status_code, 200, r.data)
        hits = [x for x in r.data if x["id"] == rid]
        return hits[0] if hits else None

    # ─────────── ফাঁক ১: কোর্স ধরে ছাঁকা ───────────

    def test_a_teacher_does_not_see_anothers_class(self):
        """⚠️ আসল বাগ — কোর্সের উস্তাদ হওয়ায় ক সব ক্লাস দেখে ফেলত।"""
        self.assertNotIn(self.xb.id, self.ids("/api/classes/", self.a),
                         "উস্তাদ-ক অন্যের ক্লাস দেখতে পাচ্ছেন")

    def test_a_teacher_does_not_see_anothers_routine(self):
        self.assertNotIn(self.rb.id, self.ids("/api/routines/", self.a),
                         "উস্তাদ-ক অন্যের রুটিন দেখতে পাচ্ছেন")

    def test_the_real_teacher_still_sees_their_own(self):
        """⚠️ ছাঁকনি কড়া করতে গিয়ে খ যেন নিজেরটাই না হারান।"""
        self.assertIn(self.xb.id, self.ids("/api/classes/", self.b))
        self.assertIn(self.rb.id, self.ids("/api/routines/", self.b))

    def test_the_director_still_sees_everything(self):
        self.assertIn(self.xb.id, self.ids("/api/classes/", self.boss))
        self.assertIn(self.rb.id, self.ids("/api/routines/", self.boss))

    def test_the_student_sees_only_their_own(self):
        self.assertIn(self.xb.id, self.ids("/api/classes/", self.s2))
        self.assertNotIn(self.xb.id, self.ids("/api/classes/", self.s1))

    # ─────────── ফাঁক ২: নামের তালিকা ───────────

    def _mixed(self):
        """একই রুটিনে দুই উস্তাদের ছাত্র — খ পড়ান।"""
        r = self.Routine.objects.create(course=self.c, teacher=self.b,
                                        days=[2], time="11:00",
                                        zoom_link="https://z/m")
        r.students.add(self.s1, self.s2)
        x = self.ClassSession.objects.create(course=self.c, teacher=self.b,
                                             date="2026-09-15", time="11:00",
                                             zoom_link="https://z/m")
        x.students.add(self.s1, self.s2)
        return r, x

    def test_a_teacher_sees_a_routine_holding_their_student(self):
        """নিজের ছাত্র আছে বলে রুটিনটি দেখতে পাওয়া ঠিকই আছে।"""
        r, _ = self._mixed()
        self.assertIn(r.id, self.ids("/api/routines/", self.a))

    def test_but_only_their_own_students_name_shows(self):
        """⚠️ আসল বাগ — অন্য উস্তাদের ছাত্রের নামও চলে আসত।"""
        r, _ = self._mixed()
        got = self.row("/api/routines/", self.a, r.id)["student_names"]
        self.assertEqual(got, ["ক-এর ছাত্র"],
                         "অন্য উস্তাদের ছাত্রের নাম দেখা যাচ্ছে: %s" % got)

    def test_the_same_for_classes(self):
        _, x = self._mixed()
        got = self.row("/api/classes/", self.a, x.id)["student_names"]
        self.assertEqual(got, ["ক-এর ছাত্র"],
                         "ক্লাসে অন্যের ছাত্রের নাম দেখা যাচ্ছে: %s" % got)

    def test_the_class_teacher_sees_everyone_in_their_own_class(self):
        """⚠️ যিনি নিজে ক্লাসটি নিচ্ছেন, তিনি সবার নামই দেখবেন —
        নইলে নিজের ক্লাসেই কে আছে তা জানতে পারতেন না।"""
        r, x = self._mixed()
        self.assertEqual(
            sorted(self.row("/api/routines/", self.b, r.id)["student_names"]),
            sorted(["ক-এর ছাত্র", "খ-এর ছাত্র"]))
        self.assertEqual(
            sorted(self.row("/api/classes/", self.b, x.id)["student_names"]),
            sorted(["ক-এর ছাত্র", "খ-এর ছাত্র"]))

    def test_the_director_sees_all_names(self):
        r, x = self._mixed()
        self.assertEqual(
            sorted(self.row("/api/routines/", self.boss, r.id)["student_names"]),
            sorted(["ক-এর ছাত্র", "খ-এর ছাত্র"]))

    def test_a_student_does_not_learn_classmates_names(self):
        """⚠️ শিক্ষার্থী নিজের সহপাঠীর নাম জানার দরকার নেই।"""
        r, _ = self._mixed()
        got = self.row("/api/routines/", self.s1, r.id)["student_names"]
        self.assertEqual(got, ["ক-এর ছাত্র"],
                         "শিক্ষার্থী অন্যের নাম দেখছে: %s" % got)

    def test_the_schedules_are_filtered_too(self):
        """⚠️ আলাদা সময়সূচিতেও শিক্ষার্থীর আইডি থাকে — সেটিও ছাঁকা চাই।"""
        from core.models import RoutineStudentSchedule
        r, _ = self._mixed()
        RoutineStudentSchedule.objects.create(routine=r, student=self.s1,
                                              days=[2], time="09:00")
        RoutineStudentSchedule.objects.create(routine=r, student=self.s2,
                                              days=[3], time="12:00")
        got = self.row("/api/routines/", self.a, r.id)["student_schedules"]
        self.assertEqual([g["student"] for g in got], [self.s1.id],
                         "অন্য উস্তাদের ছাত্রের সময়সূচি দেখা যাচ্ছে")

    # ─────────── ফাঁক ৩: আইডির তালিকা ───────────

    def test_the_student_id_list_is_filtered_too(self):
        """⚠️ নাম লুকিয়েও আইডি রয়ে গেলে ফাঁকটা বন্ধ হয় না।

        পর্দায় নাম আর আইডি ক্রম ধরে জোড়া লাগানো হয়
        (studentNames[i] ↔ studentIds[i])। নাম কম পাঠিয়ে আইডি পুরো
        পাঠালে দুটোর ক্রম মেলে না — এক শিক্ষার্থীর পাশে আরেকজনের নাম
        বসে যেতে পারত। আরও বড় কথা, নাম না পেলে পর্দা nameOf(sid) দিয়ে
        স্থানীয় তথ্য থেকে নামটা খুঁজে নিত — অর্থাৎ লুকানো নামই ফিরে আসত।
        """
        r, x = self._mixed()
        self.assertEqual(self.row("/api/routines/", self.a, r.id)["students"],
                         [self.s1.id], "অন্য উস্তাদের ছাত্রের আইডি যাচ্ছে")
        self.assertEqual(self.row("/api/classes/", self.a, x.id)["students"],
                         [self.s1.id], "ক্লাসেও আইডি যাচ্ছে")

    def test_names_and_ids_always_line_up(self):
        """⚠️ দুটোর সংখ্যা সমান না হলে পর্দায় ভুল নাম বসে।"""
        r, x = self._mixed()
        for who in (self.a, self.b, self.boss, self.s1):
            for path, rid in (("/api/routines/", r.id), ("/api/classes/", x.id)):
                got = self.row(path, who, rid)
                if got is None:
                    continue
                self.assertEqual(
                    len(got["students"]), len(got["student_names"]),
                    "%s — আইডি %d টি, নাম %d টি"
                    % (who.username, len(got["students"]),
                       len(got["student_names"])))

    def test_the_class_teacher_still_gets_every_id(self):
        """⚠️ যিনি ক্লাসটি নিচ্ছেন তাঁর সবার আইডিই দরকার — হাজিরা নেবেন।"""
        r, x = self._mixed()
        self.assertEqual(
            sorted(self.row("/api/routines/", self.b, r.id)["students"]),
            sorted([self.s1.id, self.s2.id]))

    def test_the_director_can_still_edit_the_student_list(self):
        """⚠️ সবচেয়ে বড় ঝুঁকি — ছাঁকনি বসাতে গিয়ে পরিচালকের সম্পাদনা
        যেন নষ্ট না হয়। তিনি রুটিনে শিক্ষার্থী যোগ-বিয়োগ করেন।"""
        r, _ = self._mixed()
        resp = self.as_(self.boss).patch(
            "/api/routines/%d/" % r.id, {"students": [self.s2.id]},
            format="json")
        self.assertIn(resp.status_code, (200, 202), resp.data)
        r.refresh_from_db()
        self.assertEqual([u.id for u in r.students.all()], [self.s2.id],
                         "পরিচালকের সম্পাদনা বসেনি")

    def test_it_stays_cheap(self):
        """⚠️ ছাঁকনি বসাতে গিয়ে prefetch ক্যাশ যেন ফাঁকি না দেয় (N+1)।"""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        for i in range(6):
            r = self.Routine.objects.create(course=self.c, teacher=self.b,
                                            days=[4], time="13:00",
                                            zoom_link="https://z/%d" % i)
            r.students.add(self.s1, self.s2)
        with CaptureQueriesContext(connection) as q:
            resp = self.as_(self.a).get("/api/routines/")
        self.assertEqual(resp.status_code, 200)
        self.assertLess(len(q), 12,
                        "প্রতি রুটিনে আলাদা কোয়েরি হচ্ছে (N+1): %d" % len(q))
