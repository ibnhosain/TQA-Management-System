"""
"মাস" ফিল্ড আগে ফ্রি-টেক্সট ছিল বলে "যেকোনো মাসের পেমেন্ট সরাসরি সম্পন্ন করুন" টুল
দিয়ে টেস্ট করার সময় ভুল ফরম্যাটে (যেমন: "August-2026", "জুলাই" — বছর ছাড়া)
মাসের নাম লেখা হয়ে গিয়েছিল। ফলে FeePayment রেকর্ড "ভেরিফাইড" হিসেবে তৈরি হলেও
আসল বকেয়ার (DueMonth, যার লেবেল সবসময় "জুলাই ২০২৬" ফরম্যাটে) সাথে না মেলায়
বকেয়া কখনো সরেনি — এই রেকর্ডগুলো তাই সম্পূর্ণ অর্থহীন (পরিশোধিত দেখাচ্ছে অথচ
বকেয়া ঠিকই থেকে গেছে)।

এখন মাস-ফিল্ড ক্যালেন্ডার পিকারে বদলানো হয়েছে (ভবিষ্যতে আর এই ভুল হবে না) —
এই কমান্ড শুধু আগে ভুলভাবে তৈরি হওয়া এই নির্দিষ্ট রেকর্ডগুলো মুছে ফেলে।

মোছা হবে: FeePayment যার month_label ঠিক "August-2026" বা "জুলাই" (বছরবিহীন) —
এই দুটো ফরম্যাটই কাঠামোগতভাবে অবৈধ (আসল লেবেল সবসময় "<বাংলা মাস> <বাংলা সাল>"),
তাই এগুলো নিশ্চিতভাবেই টেস্ট ডেটা, অন্য কোনো আসল পেমেন্ট রেকর্ডে হাত পড়বে না।

ব্যবহার:
    python manage.py remove_bad_month_label_payments            # ড্রাই-রান
    python manage.py remove_bad_month_label_payments --confirm   # আসলেই মুছে
"""
from django.core.management.base import BaseCommand
from core.models import FeePayment

BAD_LABELS = ["August-2026", "জুলাই"]


class Command(BaseCommand):
    help = "ভুল ফরম্যাটের (বছরবিহীন/ইংরেজি) month_label সহ টেস্ট FeePayment রেকর্ড মুছে ফেলে"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm", action="store_true",
            help="আসলেই মুছে ফেলার জন্য এই ফ্ল্যাগ দিন — নইলে শুধু কী মুছা হবে তা দেখাবে",
        )

    def handle(self, *args, **opts):
        qs = FeePayment.objects.filter(month_label__in=BAD_LABELS).select_related("student")

        self.stdout.write(self.style.WARNING(f"যা মোছা হবে ({qs.count()}):\n"))
        for p in qs:
            self.stdout.write(
                f"  pk={p.pk}  {p.student.name_bn!r}  month_label={p.month_label!r}  "
                f"৳{p.amount}  status={p.status}"
            )

        if not opts["confirm"]:
            self.stdout.write(self.style.NOTICE(
                "\n(এটা শুধু ড্রাই-রান — কিছুই মোছা হয়নি। আসলেই মুছতে "
                "--confirm ফ্ল্যাগসহ আবার চালান।)"
            ))
            return

        n, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"\nমোছা হয়েছে — FeePayment: {n}টি।"))
