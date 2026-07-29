"""
নতুন মাস-পিকার ফিচার পরীক্ষা করার সময় Saif Hossain-এর নামে সঠিক ফরম্যাটেই
("জুলাই ২০২৬") আরেকটা টেস্ট পেমেন্ট তৈরি হয়ে গিয়েছিল (৳৩,৫০০, bkash, ২৯ জুলাই
২০২৬ তারিখে) — এটা যেহেতু সঠিক ফরম্যাটে ছিল, তৈরির সময় তার জুলাই ২০২৬-এর আসল
DueMonth মুছে গিয়েছিল। তাই এই পেমেন্ট মুছে ফেলার সাথে সাথে সেই DueMonth আবার
ফিরিয়ে আনা হয় (get_or_create) — নইলে সে বাস্তবে না দিয়েও বকেয়ামুক্ত দেখাত।

ব্যবহার:
    python manage.py remove_saif_july_test_payment            # ড্রাই-রান
    python manage.py remove_saif_july_test_payment --confirm   # আসলেই মুছে
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import FeePayment, DueMonth

MONTH_LABEL = "জুলাই ২০২৬"


class Command(BaseCommand):
    help = "Saif Hossain-এর সঠিক-ফরম্যাটের জুলাই ২০২৬ টেস্ট পেমেন্ট মুছে ও বকেয়া ফিরিয়ে আনে"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm", action="store_true",
            help="আসলেই মুছে ফেলার জন্য এই ফ্ল্যাগ দিন — নইলে শুধু কী মুছা হবে তা দেখাবে",
        )

    def handle(self, *args, **opts):
        qs = FeePayment.objects.filter(
            student__name_bn__icontains="Saif",
            month_label=MONTH_LABEL,
            amount=3500,
            method="bkash",
        ).select_related("student")

        self.stdout.write(self.style.WARNING(f"যা মোছা হবে ({qs.count()}):\n"))
        students = set()
        for p in qs:
            self.stdout.write(
                f"  pk={p.pk}  {p.student.name_bn!r}  month_label={p.month_label!r}  "
                f"৳{p.amount}  {p.method}  status={p.status}"
            )
            students.add(p.student)

        if not opts["confirm"]:
            self.stdout.write(self.style.NOTICE(
                "\n(এটা শুধু ড্রাই-রান — কিছুই মোছা হয়নি। আসলেই মুছতে "
                "--confirm ফ্ল্যাগসহ আবার চালান।)"
            ))
            return

        with transaction.atomic():
            n, _ = qs.delete()
            restored = 0
            for student in students:
                _, created = DueMonth.objects.get_or_create(
                    user=student, month_label=MONTH_LABEL,
                )
                if created:
                    restored += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nমোছা হয়েছে — FeePayment: {n}টি। বকেয়া পুনরায় তৈরি: {restored}টি।"
        ))
