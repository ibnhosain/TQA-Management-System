"""
রুটিন থেকে তৈরি হওয়া ক্লাস-সেশনের মধ্যে ডুপ্লিকেট (একই রুটিন + একই তারিখ) আছে
কিনা যাচাই — সম্পূর্ণ read-only, কিছুই মোছে/বদলায় না। একটা নতুন
unique_together constraint (routine, date) যোগ করার migration চালানোর আগে
নিশ্চিত হতে ব্যবহার করা হয় — ডুপ্লিকেট থাকলে migrate ব্যর্থ হবে।

ব্যবহার:
    python manage.py find_duplicate_class_sessions
"""
from collections import defaultdict

from django.core.management.base import BaseCommand

from core.models import ClassSession


class Command(BaseCommand):
    help = "ডুপ্লিকেট (routine, date) ক্লাস-সেশন খুঁজে দেখায় (read-only)"

    def handle(self, *args, **opts):
        groups = defaultdict(list)
        qs = ClassSession.objects.filter(routine__isnull=False).select_related(
            "routine", "course", "teacher"
        )
        for s in qs:
            groups[(s.routine_id, s.date)].append(s)

        dupes = {k: v for k, v in groups.items() if len(v) > 1}
        if not dupes:
            self.stdout.write(self.style.SUCCESS(
                "✔ কোনো ডুপ্লিকেট (routine, date) ক্লাস-সেশন পাওয়া যায়নি — migration নিরাপদে চালানো যাবে।"
            ))
            return

        self.stdout.write(self.style.WARNING(
            f"⚠️ {len(dupes)}টা রুটিন+তারিখের জোড়ায় একাধিক ক্লাস-সেশন পাওয়া গেছে:\n"
        ))
        for (routine_id, date), sessions in dupes.items():
            self.stdout.write(
                f"রুটিন #{routine_id} · তারিখ {date} · {len(sessions)}টা সেশন:"
            )
            for s in sessions:
                self.stdout.write(
                    f"  pk={s.pk}  কোর্স={s.course.name if s.course_id else '—'}  "
                    f"উস্তাদ={s.teacher.name_bn if s.teacher_id else '—'}  status={s.status}  "
                    f"স্টুডেন্ট={list(s.students.values_list('name_bn', flat=True))}"
                )
        self.stdout.write(self.style.WARNING(
            "\n(এগুলো ম্যানুয়ালি পর্যালোচনা করে ঠিক করা দরকার — এই কমান্ড কিছু মোছেনি)"
        ))
