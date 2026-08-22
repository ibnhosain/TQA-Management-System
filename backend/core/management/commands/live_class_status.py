"""
আজকের ক্লাসগুলোর আসল অবস্থা দেখায় — কে জয়েন করে আছে, কে নেই, উস্তাদ কে,
স্টুডেন্ট কারা। সম্পূর্ণ read-only, কিছুই বদলায় না।

"শিক্ষার্থী বলছে জয়েন করে আছি, উস্তাদ বলছে খুঁজে পাচ্ছি না" — এমন হলে এটা
চালালে বোঝা যায় দুজন আসলে একই ক্লাসে আছেন কিনা, নাকি দুটো আলাদা ক্লাসে।

ব্যবহার:
    python manage.py live_class_status            # আজকের
    python manage.py live_class_status --date 2026-08-09
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ClassSession, Attendance


class Command(BaseCommand):
    help = "আজকের ক্লাস ও কে কে জয়েন করে আছে তা দেখায় (read-only)"

    def add_arguments(self, parser):
        parser.add_argument("--date", help="YYYY-MM-DD (না দিলে আজ)")

    def handle(self, *args, **opts):
        if opts.get("date"):
            day = datetime.date.fromisoformat(opts["date"])
        else:
            day = timezone.localtime().date()

        sessions = (
            ClassSession.objects.filter(date=day)
            .select_related("course", "teacher", "course__teacher", "routine")
            .prefetch_related("students")
            .order_by("time", "id")
        )
        if not sessions:
            self.stdout.write(self.style.WARNING(f"{day} তারিখে কোনো ক্লাস নেই।"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"\n{day} — মোট {len(sessions)}টি ক্লাস\n" + "=" * 60
        ))
        for s in sessions:
            course_teacher = s.course.teacher if s.course_id else None
            self.stdout.write(
                f"\n▶ ক্লাস #{s.pk}  {s.course.name if s.course_id else '—'}  "
                f"{s.time.strftime('%H:%M')}  ({s.duration_min} মি)  status={s.status}"
            )
            self.stdout.write(
                f"   সেশনের উস্তাদ : {s.teacher.name_bn if s.teacher_id else '— নেই —'}"
                f"  (id={s.teacher_id})"
            )
            self.stdout.write(
                f"   কোর্সের উস্তাদ : {course_teacher.name_bn if course_teacher else '— নেই —'}"
                f"  (id={course_teacher.id if course_teacher else None})"
            )
            if s.teacher_id and course_teacher and s.teacher_id != course_teacher.id:
                self.stdout.write(self.style.WARNING(
                    "   ⚠️ সেশনের উস্তাদ ও কোর্সের উস্তাদ আলাদা"
                ))
            self.stdout.write(
                f"   রুটিন         : {'#' + str(s.routine_id) if s.routine_id else 'রুটিন ছাড়া (আলাদা ক্লাস)'}"
            )
            studs = list(s.students.all())
            self.stdout.write(
                f"   তালিকাভুক্ত স্টুডেন্ট ({len(studs)}): "
                + (", ".join(f"{u.name_bn}(id={u.id})" for u in studs) or "— কেউ নেই —")
            )

            rows = Attendance.objects.filter(session=s).select_related("user")
            if not rows:
                self.stdout.write("   হাজিরা        : কেউ এখনো জয়েন করেনি")
                continue
            self.stdout.write("   হাজিরা        :")
            for a in rows:
                live = "🟢 এখন আছে" if a.segment_start else "⚪ নেই"
                self.stdout.write(
                    f"      - {a.user.name_bn}(id={a.user_id}, {a.user.role})  {live}"
                    f"  মিনিট={a.minutes}  হাজিরা={'✔' if a.marked_present else '✘'}"
                )

        # একই দিনে একই কোর্সে একাধিক ক্লাস থাকলে সতর্ক করি — এতেই সাধারণত
        # "একজন এক ক্লাসে, আরেকজন অন্য ক্লাসে" সমস্যা হয়
        by_course = {}
        for s in sessions:
            by_course.setdefault(s.course_id, []).append(s)
        dupes = {c: v for c, v in by_course.items() if len(v) > 1}
        if dupes:
            self.stdout.write(self.style.WARNING(
                "\n⚠️ একই কোর্সে একই দিনে একাধিক ক্লাস আছে — উস্তাদ ও শিক্ষার্থী "
                "ভুল করে আলাদা ক্লাসে জয়েন করে ফেলতে পারেন:"
            ))
            for cid, v in dupes.items():
                names = ", ".join(f"#{x.pk}({x.time.strftime('%H:%M')})" for x in v)
                self.stdout.write(f"   {v[0].course.name}: {names}")
        self.stdout.write("")
