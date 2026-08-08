"""
ভর্তি আবেদনের তালিকায় তিনটা স্পষ্ট ফেক/টেস্ট এন্ট্রি ধরা পড়েছিল (পরিচালক
একে একে শনাক্ত করে মুছে দিতে বলেছেন):

1. নাম ";rthrtkhrkhyl;kh" — নাম/ফোন ("hhhdh")/মেসেজ ("hhdhrfhr") সবই এলোমেলো
   কীবোর্ড-চাপা অক্ষর, কোনো বাস্তব তথ্য নেই।
2. নাম "mustakim" — ফোন নম্বর 01402499027 আসলে একাডেমির নিজের WhatsApp নম্বর
   (সাইট/পোর্টাল জুড়ে ব্যবহৃত), তাই এটাও টেস্ট/ভুল সাবমিশন।
3. নাম "MH Mahdi" — ফোন ০১৩২২০৩৭৫৬৩, মেসেজ শুধু "হ্যা" (ইতিমধ্যে "বাতিল"),
   পরিচালক নিশ্চিত করেছেন এটাও ফেক।

id দিয়ে নয়, name+contact মিলিয়ে নির্দিষ্ট করা হয়েছে যাতে অন্য কোনো
ভবিষ্যতের বৈধ আবেদনে ভুলবশত হাত না পড়ে।

ব্যবহার:
    python manage.py remove_fake_admissions            # ড্রাই-রান
    python manage.py remove_fake_admissions --confirm   # আসলেই মুছে
"""
from django.core.management.base import BaseCommand
from core.models import Admission

TARGETS = [
    {"name": ";rthrtkhrkhyl;kh", "contact": "hhhdh"},
    {"name": "mustakim", "contact": "01402499027"},
    {"name": "MH Mahdi", "contact": "০১৩২২০৩৭৫৬৩"},
]


class Command(BaseCommand):
    help = "স্পষ্টভাবে শনাক্ত করা ৩টা ফেক/টেস্ট Admission এন্ট্রি মুছে ফেলে"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm", action="store_true",
            help="আসলেই মুছে ফেলার জন্য এই ফ্ল্যাগ দিন — নইলে শুধু কী মুছা হবে তা দেখাবে",
        )

    def handle(self, *args, **opts):
        matches = []
        for t in TARGETS:
            matches += list(Admission.objects.filter(name=t["name"], contact=t["contact"]))

        if not matches:
            self.stdout.write(self.style.WARNING(
                "কোনো মিল পাওয়া যায়নি — সম্ভবত এই এন্ট্রিগুলো আগেই মুছে ফেলা হয়েছে "
                "অথবা ডেটা ইতিমধ্যে বদলে গেছে। কিছুই মোছা হয়নি।"
            ))
            return

        self.stdout.write(self.style.WARNING(f"যা মোছা হবে ({len(matches)}):\n"))
        for a in matches:
            self.stdout.write(
                f"  pk={a.pk}  নাম={a.name!r}  ফোন={a.contact!r}  "
                f"কোর্স={a.course_name!r}  status={a.status}  আবেদনের তারিখ={a.applied_at}"
            )

        if not opts["confirm"]:
            self.stdout.write(self.style.NOTICE(
                "\n(এটা শুধু ড্রাই-রান — কিছুই মোছা হয়নি। আসলেই মুছতে "
                "--confirm ফ্ল্যাগসহ আবার চালান।)"
            ))
            return

        ids = [a.pk for a in matches]
        n, _ = Admission.objects.filter(pk__in=ids).delete()
        self.stdout.write(self.style.SUCCESS(f"\nমোছা হয়েছে — Admission: {n}টি।"))
