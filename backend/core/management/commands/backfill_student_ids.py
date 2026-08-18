"""
আগে থেকে থাকা স্টুডেন্টদের জন্য স্টুডেন্ট আইডি তৈরি করে দেয়
(ফরম্যাট: SH-LC-US-007 — নাম · বাবার নাম · দেশ · সিরিয়াল)।

যাদের ইতিমধ্যে আইডি আছে তাদের কিছুই বদলায় না। ভর্তির ক্রম ঠিক রাখতে
পুরনো স্টুডেন্ট থেকে নতুনের দিকে (id অনুসারে) সিরিয়াল দেওয়া হয়।

ব্যবহার:
    python manage.py backfill_student_ids            # ড্রাই-রান (কিছুই বদলাবে না)
    python manage.py backfill_student_ids --confirm  # আসলেই সেভ করে
"""
from django.core.management.base import BaseCommand

from core.models import User
from core.student_id import backfill_all


class Command(BaseCommand):
    help = "পুরনো স্টুডেন্টদের জন্য স্টুডেন্ট আইডি তৈরি করে (ড্রাই-রান ডিফল্ট)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm", action="store_true",
            help="আসলেই সেভ করার জন্য এই ফ্ল্যাগ দিন — নইলে শুধু কী হবে তা দেখাবে",
        )

    def handle(self, *args, **opts):
        already = User.objects.filter(role="student").exclude(student_id="").count()
        # commit=False → শুধু পরিকল্পনা; --confirm দিলে নিচে আবার commit=True তে চালাই
        plan = backfill_all(User, commit=False)

        if not plan:
            self.stdout.write(self.style.SUCCESS(
                f"✔ সব স্টুডেন্টেরই আইডি আছে ({already} জন) — নতুন করে কিছু তৈরির দরকার নেই।"
            ))
            return

        self.stdout.write(self.style.WARNING(
            f"যাদের আইডি তৈরি হবে ({len(plan)} জন; আগে থেকে আছে {already} জনের):\n"
        ))
        for u, sid in plan:
            self.stdout.write(
                f"  {sid:<18} ← {u.name_bn}  (বাবা/অভিভাবক: {u.guardian or '—'}, "
                f"দেশ: {u.country or '—'})"
            )

        if not opts["confirm"]:
            self.stdout.write(self.style.NOTICE(
                "\n(এটা শুধু ড্রাই-রান — কিছুই সেভ হয়নি। আসলেই তৈরি করতে "
                "--confirm ফ্ল্যাগসহ আবার চালান।)"
            ))
            return

        saved = backfill_all(User, commit=True)
        self.stdout.write(self.style.SUCCESS(
            f"\n✔ {len(saved)} জন স্টুডেন্টের আইডি তৈরি ও সংরক্ষণ হয়েছে।"
        ))
