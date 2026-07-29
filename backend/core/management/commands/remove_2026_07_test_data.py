"""
২০২৬-০৭-২৯ তারিখের ডাটা ব্যাকআপ বিশ্লেষণ করে (পরিচালকের সাথে আলোচনা করে) নিশ্চিত হওয়া
টেস্ট/স্প্যাম রেকর্ডগুলো এখানে মোছা হয় — শুধু এই নির্দিষ্ট primary key-গুলোই,
অন্য কোনো ডাটায় হাত দেওয়া হয় না।

মোছা হবে:
  Admission pk 1, 2, 4  — "Faridur Rahman" (বয়স ৭) দিয়ে একাডেমির নিজের ফোন
                           নম্বর (01402499027) ব্যবহার করে ৩ বার ফর্ম-টেস্ট
  Admission pk 3        — "আল-হিকমাহ্‌ ইনস্টিটিউট" (একই ফোন নম্বর) টেস্ট এন্ট্রি
  Admission pk 5        — "David Pavel" — ডোমেইন-বিক্রির স্প্যাম মেসেজ
  SentReceipt pk 1-11   — আজকের তারিখেই (রিসিট/পেমেন্ট ফিচার টেস্ট করার সময়)
                           বারবার তৈরি হওয়া ডুপ্লিকেট বেতন-ভাউচার নোটিফিকেশন
  TeacherPayment pk 1, 2 — উস্তাদ ৫ (হাফেজ মাওলনা মুফতী ফরীদুর রহমান) ও উস্তাদ ২
                           (আলেমা ফাহিমা তাসনীম)-এর জুলাই ২০২৬ বেতনের টেস্ট পেমেন্ট
                           (পরিচালক নিশ্চিত করেছেন — আসল পেমেন্ট নয়)

TeacherPayment মোছার পর সেই দুই উস্তাদের জুলাই ২০২৬ মাসের DueMonth আবার তৈরি করা
হয় (get_or_create) — কারণ টেস্ট পেমেন্ট মুছে ফেললে বাস্তবে তাদের বেতন এখনো
পরিশোধিত হয়নি, তাই বকেয়া তালিকায় আবার সঠিকভাবে দেখাতে হবে।

স্টুডেন্ট/টিচার অ্যাকাউন্ট, কোর্স, একাডেমিক বই, ক্লাস-সেশন/হাজিরা — এসবের
কোনোটিতেই হাত দেওয়া হয় না (ব্যাকআপ বিশ্লেষণে এগুলো সবই আসল বলে চিহ্নিত হয়েছে)।

ব্যবহার (নিরাপত্তার জন্য ডিফল্টে শুধু দেখাবে, মুছবে না):
    python manage.py remove_2026_07_test_data            # ড্রাই-রান — কী মোছা হবে দেখায়
    python manage.py remove_2026_07_test_data --confirm   # আসলেই মোছে
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Admission, SentReceipt, TeacherPayment, DueMonth, User

ADMISSION_PKS = [1, 2, 3, 4, 5]
SENT_RECEIPT_PKS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
TEACHER_PAYMENT_PKS = [1, 2]


class Command(BaseCommand):
    help = "২০২৬-০৭-২৯ ব্যাকআপ বিশ্লেষণে চিহ্নিত টেস্ট/স্প্যাম রেকর্ড (নির্দিষ্ট pk) মুছে ফেলে"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm", action="store_true",
            help="আসলেই মুছে ফেলার জন্য এই ফ্ল্যাগ দিন — নইলে শুধু কী মুছা হবে তা দেখাবে",
        )

    def handle(self, *args, **opts):
        admissions = Admission.objects.filter(pk__in=ADMISSION_PKS)
        receipts = SentReceipt.objects.filter(pk__in=SENT_RECEIPT_PKS)
        payments = TeacherPayment.objects.filter(pk__in=TEACHER_PAYMENT_PKS)

        self.stdout.write(self.style.WARNING("যা মোছা হবে:\n"))
        self.stdout.write(f"ভর্তি আবেদন ({admissions.count()}):")
        for a in admissions:
            self.stdout.write(f"  pk={a.pk}  {a.name!r}  ({a.applied_at})")
        self.stdout.write(f"\nসেন্ট রিসিট/ভাউচার ({receipts.count()}):")
        for r in receipts:
            self.stdout.write(f"  pk={r.pk}  to_user={r.to_user_id}  {r.month_label}  ৳{r.amount}")
        self.stdout.write(f"\nটিচার পেমেন্ট ({payments.count()}):")
        teacher_ids = set()
        month_labels = set()
        for p in payments:
            self.stdout.write(f"  pk={p.pk}  teacher={p.teacher_id}  {p.month_label}  ৳{p.amount}")
            teacher_ids.add(p.teacher_id)
            month_labels.add(p.month_label)

        if not opts["confirm"]:
            self.stdout.write(self.style.NOTICE(
                "\n(এটা শুধু ড্রাই-রান — কিছুই মোছা হয়নি। আসলেই মুছতে "
                "--confirm ফ্ল্যাগসহ আবার চালান।)"
            ))
            return

        with transaction.atomic():
            n1, _ = admissions.delete()
            n2, _ = receipts.delete()
            n3, _ = payments.delete()
            # টেস্ট পেমেন্ট মোছার পর ওই উস্তাদদের বেতন বাস্তবে এখনো বাকি —
            # তাই DueMonth আবার তৈরি করি যাতে বকেয়া তালিকায় সঠিকভাবে দেখায়
            restored = 0
            for tid in teacher_ids:
                for label in month_labels:
                    try:
                        user = User.objects.get(pk=tid)
                    except User.DoesNotExist:
                        continue
                    _, created = DueMonth.objects.get_or_create(user=user, month_label=label)
                    if created:
                        restored += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nমোছা হয়েছে — ভর্তি আবেদন: {n1}, রিসিট: {n2}, টিচার পেমেন্ট: {n3}। "
            f"বকেয়া পুনরায় তৈরি: {restored}টি।"
        ))
