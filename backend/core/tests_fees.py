# -*- coding: utf-8 -*-
"""💰 মওকুফ করা মাস যেন বকেয়ার হিসাবে না গোনা হয়।

⚠️ যে বাগটি ধরা পড়েছিল: মওকুফ করলে DueMonth সারিটি মুছে ফেলা হয় না,
কেবল waived=True বসানো হয় (ইচ্ছাকৃত — "মওকুফ" আর "পরিশোধিত" আলাদা করে
দেখাতে)। কিন্তু UserSerializer.get_due_months() সব সারিই ফেরত দিত,
মওকুফসহ।

ফল: পরিচালকের "যাদের ফি বাকি" পর্দায় মওকুফ করা মাসও বকেয়া হিসেবে
থাকত, আর টাকার অঙ্কও (মাস × ফি) বেড়ে যেত। মওকুফ করার পর পাতা নতুন
করে আনলেও মাসটি তালিকা থেকে যেত না। WhatsApp রিমাইন্ডারেও ভুল অঙ্ক
চলে যেত — অভিভাবকের কাছে।
"""
from django.test import TestCase


class WaivedMonthsAreNotDue(TestCase):

    def setUp(self):
        from rest_framework.test import APIClient
        from core.models import User, DueMonth
        self.DueMonth = DueMonth
        self.boss = User.objects.create(username="পরিচালক", role="director")
        self.s = User.objects.create(username="ছাত্র", role="student",
                                     name_bn="সাইফ", monthly_fee=3500)
        DueMonth.objects.create(user=self.s, month_label="আগস্ট ২০২৬")
        DueMonth.objects.create(user=self.s, month_label="সেপ্টেম্বর ২০২৬")
        self.client = APIClient()
        self.client.force_authenticate(user=self.boss)

    def dues(self):
        r = self.client.get("/api/users/students/")
        self.assertEqual(r.status_code, 200, r.data)
        row = [x for x in r.data if x["id"] == self.s.id][0]
        return row["due_months"]

    def waive(self, month):
        return self.client.post("/api/fees/waive_due/",
                                {"user_id": self.s.id, "month_label": month},
                                format="json")

    def test_both_months_are_due_at_first(self):
        self.assertEqual(sorted(self.dues()),
                         sorted(["আগস্ট ২০২৬", "সেপ্টেম্বর ২০২৬"]))

    def test_a_waived_month_stops_being_due(self):
        """⚠️ আসল বাগ — মওকুফের পরও মাসটি বকেয়া দেখাত।"""
        r = self.waive("আগস্ট ২০২৬")
        self.assertIn(r.status_code, (200, 201), r.data)
        self.assertEqual(self.dues(), ["সেপ্টেম্বর ২০২৬"],
                         "মওকুফ করা মাস এখনো বকেয়া দেখাচ্ছে")

    def test_the_amount_drops_after_waiving(self):
        """টাকার অঙ্ক = বাকি মাস × মাসিক ফি — মওকুফের পর কমতে হবে।"""
        self.assertEqual(len(self.dues()) * self.s.monthly_fee, 7000)
        self.waive("আগস্ট ২০২৬")
        self.assertEqual(len(self.dues()) * self.s.monthly_fee, 3500,
                         "মওকুফের পরও অঙ্ক কমেনি")

    def test_waiving_everything_clears_the_list(self):
        self.waive("আগস্ট ২০২৬")
        self.waive("সেপ্টেম্বর ২০২৬")
        self.assertEqual(self.dues(), [], "সব মওকুফের পরও বকেয়া দেখাচ্ছে")

    def test_the_record_itself_is_kept(self):
        """⚠️ সারিটি মুছে ফেলা যাবে না — "মওকুফ" ও "পরিশোধিত" আলাদা
        দেখানোর জন্য, আর মাসিক কাজটি যেন আবার বকেয়া না বানায়।"""
        self.waive("আগস্ট ২০২৬")
        row = self.DueMonth.objects.get(user=self.s, month_label="আগস্ট ২০২৬")
        self.assertTrue(row.waived)
        self.assertIsNotNone(row.waived_at)

    def test_a_paid_month_is_gone_too(self):
        """পরিশোধিত মাস আগের মতোই মুছে যায় — সেটিও বকেয়া নয়।"""
        self.DueMonth.objects.filter(
            user=self.s, month_label="সেপ্টেম্বর ২০২৬").delete()
        self.assertEqual(self.dues(), ["আগস্ট ২০২৬"])

    def test_teachers_get_the_same_treatment(self):
        """⚠️ উস্তাদের বকেয়াও একই সিরিয়ালাইজারে যায়।"""
        from core.models import User, DueMonth
        t = User.objects.create(username="উস্তাদ", role="teacher",
                                name_bn="উস্তাদ", monthly_salary=9000)
        DueMonth.objects.create(user=t, month_label="আগস্ট ২০২৬")
        DueMonth.objects.create(user=t, month_label="সেপ্টেম্বর ২০২৬",
                                waived=True)
        r = self.client.get("/api/users/teachers/")
        self.assertEqual(r.status_code, 200, r.data)
        row = [x for x in r.data if x["id"] == t.id][0]
        self.assertEqual(row["due_months"], ["আগস্ট ২০২৬"],
                         "উস্তাদের মওকুফ করা মাসও বকেয়া দেখাচ্ছে")

    def test_the_student_sees_it_too(self):
        """শিক্ষার্থী নিজের পোর্টালে যেন মওকুফ করা মাস বকেয়া না দেখে।"""
        self.waive("আগস্ট ২০২৬")
        cl = self.client.__class__()
        cl.force_authenticate(user=self.s)
        r = cl.get("/api/users/me/")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["due_months"], ["সেপ্টেম্বর ২০২৬"])

    def test_it_stays_cheap(self):
        """⚠️ ছাঁকনি বসাতে গিয়ে prefetch ক্যাশ যেন ফাঁকি না দেয় (N+1)।"""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        from core.models import User, DueMonth
        for i in range(6):
            u = User.objects.create(username="ছ%d" % i, role="student",
                                    name_bn="ছ%d" % i, monthly_fee=3000)
            DueMonth.objects.create(user=u, month_label="আগস্ট ২০২৬")
            DueMonth.objects.create(user=u, month_label="জুলাই ২০২৬",
                                    waived=True)
        with CaptureQueriesContext(connection) as q:
            r = self.client.get("/api/users/students/")
        self.assertEqual(r.status_code, 200)
        self.assertLess(len(q), 12,
                        "প্রতি শিক্ষার্থীতে আলাদা কোয়েরি হচ্ছে (N+1): %d"
                        % len(q))
