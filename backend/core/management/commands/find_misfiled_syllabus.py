"""
মাইগ্রেশন 0004-এর আগে তৈরি হওয়া SyllabusItem রো-গুলোতে category কলাম ছিল না,
ফলে সবগুলো ডিফল্টভাবে "qirat" হয়ে গেছে — even যদি সেগুলো মূলত
মুখস্থ সূরা / মুখস্থ হাদিস / দুআ-মাসআলা / নৈতিক শিক্ষা বিভাগে যোগ করা হয়েছিল।

এই কমান্ড কোনো ডাটা স্বয়ংক্রিয়ভাবে পরিবর্তন করে না (free-text lesson থেকে সঠিক
category অনুমান করা নিরাপদ নয়) — শুধু সন্দেহজনক রো-গুলো তালিকা করে দেখায়,
যাতে পরিচালক ফ্রন্টএন্ডের নতুন "✏️ এডিট" ফর্মের category ড্রপডাউন দিয়ে
প্রতিটি রো নিজ নিজ সঠিক কলামে (মুখস্থ সূরা/হাদিস/দুআ/নৈতিক শিক্ষা) সরিয়ে নিতে পারেন।

ব্যবহার:
    python manage.py find_misfiled_syllabus
    python manage.py find_misfiled_syllabus --course=3
"""
from django.core.management.base import BaseCommand
from core.models import SyllabusItem, Course


class Command(BaseCommand):
    help = "মাইগ্রেশন 0004-এর কারণে ভুলভাবে 'qirat'-এ ডিফল্ট হওয়া সিলেবাস আইটেম খুঁজে দেখায়"

    def add_arguments(self, parser):
        parser.add_argument("--course", type=int, default=None, help="শুধু এই course id-তে সীমিত করুন")

    def handle(self, *args, **opts):
        qs = SyllabusItem.objects.filter(category="qirat").order_by("course_id", "order", "id")
        if opts["course"]:
            qs = qs.filter(course_id=opts["course"])

        if not qs.exists():
            self.stdout.write(self.style.SUCCESS("'qirat'-এ কোনো আইটেম পাওয়া যায়নি।"))
            return

        by_course = {}
        for item in qs:
            by_course.setdefault(item.course_id, []).append(item)

        total = 0
        for cid, items in by_course.items():
            course = Course.objects.filter(pk=cid).first()
            name = course.name if course else f"(course #{cid} — মুছে ফেলা হয়েছে)"
            self.stdout.write(self.style.WARNING(f"\nকোর্স: {name}  —  {len(items)} টি আইটেম 'কিরাত'-এ"))
            self.stdout.write("  id   order  lesson")
            for it in items:
                self.stdout.write(f"  {it.id:<5}{it.order:<7}{it.lesson}")
                total += 1

        self.stdout.write(self.style.NOTICE(
            f"\nমোট {total} টি আইটেম সব 'কিরাত' কলামে — এর মধ্যে যেগুলো আসলে অন্য "
            f"বিভাগের (মুখস্থ সূরা/হাদিস/দুআ/নৈতিক শিক্ষা), সেগুলো 'কোর্স সিলেবাস' পেজে "
            f"✏️ চেপে নতুন বিভাগ-ড্রপডাউন থেকে সঠিক কলামে সরিয়ে নিন।"
        ))
