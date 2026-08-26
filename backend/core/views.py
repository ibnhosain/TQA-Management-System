"""TQA-MS — DRF ViewSets ও workflow actions (অ্যাপ: core)"""
import json
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, Avg, Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes as pc
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (IsAuthenticated, BasePermission,
                                        SAFE_METHODS)
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (User, AcademicBook, Course, SyllabusItem, Lecture, LectureTopic,
                     Routine, RoutineStudentSchedule, ClassSession, Attendance, Assignment, Exam, Submission,
                     ExamResult, FeePayment, DueMonth, TeacherPayment, SentReceipt,
                     Admission, LeaveRequest, Rating, StudentRemark, Notice, Notification,
                     PushSubscription, WaMessage, LibraryBook,
                     CourseSyllabusSheet, TopicCoverage, LessonSection)
from .safe_html import clean_html
from .serializers import *
from .permissions import (IsDirector, IsAdminLevel, IsTeacherOrAdminLevel,
                          ReadAllWriteAdmin, ReadAllWriteDirector)


# নতুন স্টুডেন্টের মাসিক ফি ডিফল্ট — পরিচালক পরে প্রতিটি স্টুডেন্টের জন্য
# আলাদা করে বদলাতে পারেন (ফ্রন্টএন্ডের DEFAULT_FEE-এর সাথে মিল রাখা)
DEFAULT_STUDENT_FEE = 3500


def notify(text, users):
    n = Notification.objects.create(text=text)
    n.recipients.set(users)
    from .push import send_push
    try:
        send_push(users, "তারবিয়াতুল কুরআন একাডেমি", text)
    except Exception:
        pass  # পুশ ব্যর্থ হলেও ইন-অ্যাপ নোটিফিকেশন যেন আটকে না যায়
    return n


def admins():
    return User.objects.filter(role__in=["director", "admin"])


# ─────────────────────────── ব্যবহারকারী ───────────────────────────
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsDirector]  # যোগ/মুছা/পাসওয়ার্ড — কেবল পরিচালক
    serializer_class = UserAdminSerializer

    def get_queryset(self):
        # prefetch_related("due_months") → UserAdminSerializer.get_due_months প্রতি
        # ব্যবহারকারীতে আলাদা কোয়েরি না করে prefetch cache ব্যবহার করে (N+1 এড়ায়)
        return User.objects.exclude(is_superuser=True).prefetch_related("due_months")

    def perform_destroy(self, instance):
        # নিজেকে বা শেষ পরিচালককে মুছে ফেললে সিস্টেমে কেউ আর ইউজার ম্যানেজ
        # করতে পারবেন না (যোগ/মুছা/পাসওয়ার্ড — কেবল পরিচালকের এখতিয়ার) —
        # রিকভারি করতে তখন সার্ভারে ম্যানুয়ালি কমান্ড চালাতে হতো
        if instance.id == self.request.user.id:
            raise PermissionDenied("নিজের অ্যাকাউন্ট নিজে মুছে ফেলা যাবে না")
        if instance.role == "director" and User.objects.filter(
            role="director"
        ).exclude(pk=instance.pk).count() == 0:
            raise PermissionDenied("শেষ পরিচালকের অ্যাকাউন্ট মুছে ফেলা যাবে না")
        instance.delete()

    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, permission_classes=[IsAdminLevel])
    def students(self, request):  # "সকল স্টুডেন্ট" পেজ — এডমিনও দেখতে পারে
        qs = User.objects.filter(role="student").prefetch_related("due_months")
        ser = UserAdminSerializer if request.user.role == "director" else UserSerializer
        return Response(ser(qs, many=True).data)

    @action(detail=False, permission_classes=[IsAdminLevel])
    def teachers(self, request):  # ক্লাস/রুটিনে উস্তাদ assign করতে — এডমিনও দরকার (পাসওয়ার্ড ছাড়া)
        # prefetch_related("due_months") → UserSerializer.get_due_months প্রতি উস্তাদে
        # আলাদা কোয়েরি না করে prefetch cache ব্যবহার করে (N+1 এড়ায়)
        qs = User.objects.filter(role="teacher").prefetch_related("due_months")
        return Response(UserSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def backfill_student_ids(self, request):
        """যেসব স্টুডেন্টের এখনো স্টুডেন্ট আইডি নেই তাদের সবার জন্য তৈরি করে দেয় —
        পরিচালক "সকল স্টুডেন্ট" পেজের বাটন থেকে এক ক্লিকে চালাতে পারেন
        (idempotent — যাদের আইডি আছে তাদের কিছুই বদলায় না)"""
        from .student_id import backfill_all
        plan = backfill_all(User, commit=True)
        return Response({"created": len(plan)})

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def toggle_fix_cross(self, request, pk=None):  # লাল-ক্রস ঠিক করার অনুমতি
        u = self.get_object()
        u.can_fix_cross = not u.can_fix_cross
        u.save()
        return Response({"can_fix_cross": u.can_fix_cross})


# ─────────────────────────── বই, কোর্স, সিলেবাস, লেকচার ───────────────────────────
class AcademicBookViewSet(viewsets.ModelViewSet):
    serializer_class = AcademicBookSerializer
    permission_classes = [ReadAllWriteDirector]

    def get_queryset(self):
        return AcademicBook.objects.all()

    def create(self, request, *args, **kwargs):
        import os, traceback as tb
        name = request.data.get("name", "").strip()
        if not name:
            return Response({"error": "নাম দিন"}, status=400)
        link = (request.data.get("link") or "").strip()
        uploaded = request.FILES.get("file")
        if not uploaded and not link:
            return Response({"error": "বইয়ের ফাইল যুক্ত করুন অথবা একটি লিংক দিন"}, status=400)
        # লিংক দিলে সরাসরি সেটাই সংরক্ষণ — Cloudinary-র সাইজ সীমা লাগে না, ফাইল রিস্টার্টে হারায় না
        file_url = link
        if uploaded:
            cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
            if cloudinary_url:
                try:
                    import cloudinary.uploader
                    res = cloudinary.uploader.upload(
                        uploaded,
                        folder="tqa-books",
                        resource_type="raw",
                        use_filename=True,
                        unique_filename=True,
                    )
                    file_url = res["secure_url"]
                except Exception as e:
                    tb.print_exc()
                    return Response({"error": f"Cloudinary: {e}"}, status=500)
            else:
                # Local fallback (development)
                from django.core.files.storage import default_storage
                saved = default_storage.save(f"books/{uploaded.name}", uploaded)
                file_url = request.build_absolute_uri(f"/media/{saved}")
        book = AcademicBook.objects.create(name=name, file=file_url)
        return Response(AcademicBookSerializer(book).data, status=201)


# সিলেবাসের ৫টি বিভাগ — ফ্রন্টএন্ডের SYL_CATEGORIES-এর হুবহু একই ক্রম, আর
# নাম হিসেবে সেখানকার labelEn (ইংরেজি) ব্যবহার করা হয়। কারণ শিক্ষার্থীদের
# পুরো পোর্টালই ইংরেজিতে, আর সিলেবাসের টেবিলটা তারাই সবচেয়ে বেশি দেখে।
# এগুলো নিছক নমুনা — পরিচালক ইচ্ছামতো বদলে নিতে পারবেন।
_SYL_COLUMNS = [
    ("memorized_surah", "Memorized Surah"),
    ("memorized_hadith", "Memorized Hadith"),
    ("qirat", "Qirat"),
    ("dua_masala", "Dua/Masala"),
    ("moral_story", "Moral Lesson/Hadith Story"),
]


def _sheet_from_syllabus(course):
    """পুরনো SyllabusItem গুলো থেকে টেবিলের হেডার ও সারি বানায় (read-only)।

    প্রতিটি বিভাগ একটি কলাম; ওই বিভাগের এন্ট্রিগুলো ওই কলামে উপর থেকে নিচে।

    কোনো এন্ট্রি না থাকলেও খালি টেবিল দেওয়া হয় না — পাঁচটি বিভাগের নামই
    কলামের শিরোনাম হিসেবে বসিয়ে একটি ফাঁকা সারি দেওয়া হয়, যাতে পরিচালক
    সাথে সাথেই লিখতে শুরু করতে পারেন। শিরোনামগুলো নিছক নমুনা — ইচ্ছামতো
    বদলানো, বাদ দেওয়া বা নতুন কলাম যোগ করা যাবে।
    """
    headers_default = [label for _, label in _SYL_COLUMNS]
    items = list(course.syllabus.select_related("book").all())
    if not items:
        return headers_default, [[""] * len(headers_default)]
    by_cat = {key: [] for key, _ in _SYL_COLUMNS}
    for it in items:
        by_cat.setdefault(it.category, []).append(it)
    headers = [label for _, label in _SYL_COLUMNS]
    depth = max((len(by_cat.get(k, [])) for k, _ in _SYL_COLUMNS), default=0)
    rows = []
    for i in range(depth):
        row = []
        for key, _ in _SYL_COLUMNS:
            col = by_cat.get(key, [])
            row.append(col[i].label if i < len(col) else "")
        rows.append(row)
    return headers, rows


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [ReadAllWriteDirector]  # তৈরি/এডিট/বাদ — কেবল পরিচালক

    def get_queryset(self):
        u = self.request.user
        # select_related/prefetch → teacher_name/students/books/student_count আনতে
        # প্রতি কোর্সে বাড়তি কোয়েরি (N+1) এড়ায় — কোর্স সব জায়গায় ব্যবহৃত হয় বলে এটা জরুরি
        qs = Course.objects.filter(is_active=True).select_related(
            "teacher"
        ).prefetch_related("students", "books")
        if u.role == "teacher":
            # কোর্সের নির্ধারিত উস্তাদ হলে, অথবা এই কোর্সে তাঁর নিজের কোনো
            # শিক্ষার্থী থাকলে — দুটোর যেকোনোটিতেই কোর্সটি দেখতে পান।
            # ফলে একই কোর্সে একাধিক উস্তাদ থাকতে পারেন, প্রত্যেকে নিজের
            # শিক্ষার্থীদের সূত্রে কোর্সটি দেখেন।
            return qs.filter(Q(teacher=u) | Q(students__teacher=u)).distinct()
        if u.role == "student":
            return qs.filter(students=u)
        # ⚠️ ট্রায়াল অতিথিকে আলাদা করে ধরতেই হবে। নিচের শেষ "return qs"
        # পরিচালক/এডমিনের জন্য — কোনো ছাঁকনি ছাড়া সব। নতুন ভূমিকা যোগ করার
        # পর ট্রায়ালও সেখানে গিয়ে পড়ত, অর্থাৎ একজন সাময়িক অতিথি একাডেমির
        # সবকিছু দেখে ফেলতেন।
        if u.role == "trial":
            # অতিথি কেবল যে কোর্সটি দেখার জন্য তাঁকে ডাকা হয়েছে সেটিই
            return qs.filter(pk=u.trial_course_id) if u.trial_course_id else qs.none()
        return qs

    def perform_update(self, serializer):
        old_teacher_id = serializer.instance.teacher_id
        course = serializer.save()
        if course.teacher_id != old_teacher_id:
            # কোর্সের টিচার বদলালে এই কোর্সের ওপর তৈরি রুটিন ও আগে থেকে জেনারেট
            # হওয়া আসন্ন ক্লাস-সেশনেও নতুন টিচার সিঙ্ক করা হয় — নইলে Routine
            # এডিটের ক্ষেত্রে যেমন ছিল, এখানেও পুরনো টিচারই থেকে যেত এবং নতুন
            # টিচার নিজের পোর্টালে ক্লাসটা দেখতেই পেতেন না
            try:
                today = timezone.localtime().date()
                Routine.objects.filter(course=course, is_active=True).update(
                    teacher=course.teacher
                )
                ClassSession.objects.filter(
                    course=course, date__gte=today, status="upcoming",
                ).update(teacher=course.teacher)
            except Exception:
                pass

    @action(detail=True, permission_classes=[IsTeacherOrAdminLevel])
    def students(self, request, pk=None):
        """কোর্সের শিক্ষার্থীদের নাম ও আইডি।

        লেকচার প্ল্যানে "কার জন্য টিক দিচ্ছি" বাছাই করতে লাগে। পুরো
        ব্যবহারকারী-তালিকা (/users/) কেবল পরিচালক দেখতে পান, তাই উস্তাদের
        জন্য এই ছোট ও সীমিত পথটা আলাদা করে রাখা হলো — কেবল নিজের কোর্সের
        শিক্ষার্থী, কেবল নাম ও আইডি।
        """
        course = self.get_object()
        qs = course.students.all()
        # উস্তাদ কেবল নিজের শিক্ষার্থীদেরই দেখেন — নইলে ভুল করে অন্য উস্তাদের
        # শিক্ষার্থী বেছে তার হিসাবে টিক দিয়ে ফেলা যেত।
        # ⚠️ কারও নিজস্ব উস্তাদ বসানো না থাকলে (পুরনো তথ্য) তিনি কোর্সের
        # উস্তাদের অধীনেই ধরা হন, নইলে সেই শিক্ষার্থীরা কারও তালিকাতেই আসতেন না।
        if request.user.role == "teacher":
            own = Q(teacher=request.user)
            if course.teacher_id == request.user.id:
                own = own | Q(teacher__isnull=True)
            qs = qs.filter(own)
        rows = [
            {"id": u.id, "name": u.name_bn, "student_id": u.student_id}
            for u in qs.order_by("name_bn")
        ]
        return Response(rows)

    @action(detail=True, methods=["get", "put"], permission_classes=[IsAuthenticated])
    def syllabus_sheet(self, request, pk=None):
        """কোর্সের সিলেবাস টেবিল — পরিচালকের নিজের হাতে লেখা।

        GET  — যে কেউ (get_queryset নিজেই রোল অনুযায়ী ফিল্টার করে, তাই
               শিক্ষার্থী কেবল নিজের কোর্সেরটাই পান)।
        PUT  — কেবল পরিচালক।

        শিট প্রথমবার চাওয়া হলে খালি না দিয়ে পুরনো সিলেবাসের তথ্য থেকেই
        সাজিয়ে দেওয়া হয় — পরিচালকের কিছু নতুন করে লিখতে হয় না, আর পুরনো
        তথ্যের একটাও হারায় না (SyllabusItem-এ হাত পড়ে না, শুধু পড়া হয়)।
        """
        course = self.get_object()
        sheet, _ = CourseSyllabusSheet.objects.get_or_create(course=course)
        if request.method == "GET":
            if not sheet.headers and not sheet.rows:
                h, r = _sheet_from_syllabus(course)
                if h:
                    sheet.headers, sheet.rows = h, r
                    sheet.save(update_fields=["headers", "rows"])
            return Response(CourseSyllabusSheetSerializer(sheet).data)
        if request.user.role != "director":
            raise PermissionDenied("কেবল পরিচালক সিলেবাস টেবিল বদলাতে পারবেন")
        ser = CourseSyllabusSheetSerializer(sheet, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class SyllabusViewSet(viewsets.ModelViewSet):
    # select_related("book") → get_book_name প্রতি আইটেমে আলাদা কোয়েরি না করে (N+1 এড়ায়)
    queryset = SyllabusItem.objects.select_related("book").all()
    serializer_class = SyllabusItemSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["course"]

    def perform_create(self, serializer):
        cat = self.request.data.get("category", "qirat")
        valid = [c[0] for c in SyllabusItem.Category.choices]
        serializer.save(category=cat if cat in valid else "qirat")

    def perform_update(self, serializer):
        valid = [c[0] for c in SyllabusItem.Category.choices]
        cat = self.request.data.get("category")
        if cat in valid:
            serializer.save(category=cat)
        else:
            serializer.save()


# দারসের টগলে বসানোর জন্য ছবি/PDF — ডাটাবেসে কিছু জমে না, শুধু ফাইলটা
# Cloudinary-তে গিয়ে তার ঠিকানা ফেরত আসে, আর সেটাই লেখার ভেতরে বসে।
_IMG_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_DOC_TYPES = {"application/pdf"}
_MAX_UPLOAD_MB = 10


class LessonMediaView(APIView):
    """POST /api/lesson-media/ — ছবি বা PDF আপলোড করে ঠিকানা ফেরত দেয়।

    কেবল পরিচালক, কারণ টগলের ভেতরের লেখা কেবল তিনিই লেখেন। ধরনও যাচাই
    করা হয় — যেকোনো ফাইল আপলোড করতে দিলে তা অপব্যবহারের পথ খুলে দিত।
    """
    permission_classes = [IsDirector]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        import os, traceback as tb

        f = request.FILES.get("file")
        if not f:
            return Response({"error": "ফাইল দিন"}, status=400)
        ctype = (getattr(f, "content_type", "") or "").lower()
        if ctype not in _IMG_TYPES | _DOC_TYPES:
            return Response(
                {"error": "কেবল ছবি (JPG/PNG/GIF/WebP) বা PDF দেওয়া যাবে"},
                status=400,
            )
        if f.size > _MAX_UPLOAD_MB * 1024 * 1024:
            return Response(
                {"error": f"ফাইলটি {_MAX_UPLOAD_MB} MB-র বেশি বড়"}, status=400
            )
        is_image = ctype in _IMG_TYPES
        cloud = os.environ.get("CLOUDINARY_URL", "")
        if cloud:
            try:
                import cloudinary.uploader
                res = cloudinary.uploader.upload(
                    f,
                    folder="tqa-lessons",
                    resource_type="image" if is_image else "raw",
                    use_filename=True,
                    unique_filename=True,
                )
                url = res["secure_url"]
            except Exception as e:
                tb.print_exc()
                return Response({"error": f"Cloudinary: {e}"}, status=500)
        else:
            # ডেভেলপমেন্টে — লোকাল ফাইল
            from django.core.files.storage import default_storage
            saved = default_storage.save(f"lessons/{f.name}", f)
            url = request.build_absolute_uri(f"/media/{saved}")
        return Response({"url": url, "kind": "image" if is_image else "pdf",
                         "name": f.name}, status=201)


# পরিচালকের দেওয়া ক্রমেই নতুন কোর্সে হেডিংগুলো বসে
DEFAULT_SECTIONS = [
    "Memorized Surah", "Memorized Hadith", "Qirat", "Dua", "Masala",
    "Moral Lesson", "Hadith Story",
]


class LessonSectionViewSet(viewsets.ModelViewSet):
    """দারস পরিকল্পনার হেডিং — তৈরি, নাম বদলানো, ক্রম, মুছে ফেলা।

    পড়তে পারেন সবাই (নিজের কোর্সের), লিখতে কেবল পরিচালক।
    """
    serializer_class = LessonSectionSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["course"]

    def get_queryset(self):
        u = self.request.user
        qs = LessonSection.objects.prefetch_related(
            "topics", "topics__coverages"
        ).select_related("course")
        # ⚠️ নিয়মিত ও ট্রায়াল — দুটি আলাদা পরিকল্পনা। কোনটি চাওয়া হচ্ছে তা
        # ?is_trial=1 দিয়ে বলতে হয়। না বললে নিয়মিতটাই, অর্থাৎ পুরনো সব কল
        # অবিকল আগের মতোই কাজ করে — ট্রায়ালের হেডিং ভুল করে সেখানে ঢোকে না।
        # ⚠️ ছাঁকনিটা কেবল তালিকা দেখানোর সময় — আইডি ধরে সম্পাদনা/মোছার
        # সময় নয়। নইলে ট্রায়ালের হেডিং সম্পাদনা করতে গেলেই "খুঁজে পাওয়া
        # যায়নি" আসত, কারণ ওই কলে ?is_trial=1 থাকে না।
        want_trial = str(
            self.request.query_params.get("is_trial") or ""
        ).lower() in ("1", "true", "yes")
        list_only = self.action in ("list", "ensure")
        if u.role == "trial":
            # ট্রায়াল অতিথি কেবল নিজের কোর্সের ট্রায়াল-পরিকল্পনাই দেখেন —
            # নিয়মিত পরিকল্পনা তাঁর জন্য নয়, অন্য কোর্সও নয়
            if not u.trial_course_id or u.trial_expired:
                return qs.none()  # মেয়াদ ফুরালে দারস পরিকল্পনাও সরে যায়
            return qs.filter(course_id=u.trial_course_id, is_trial=True)
        if u.role == "student":
            # ⚠️ ভর্তি হওয়া শিক্ষার্থী সবসময় নিয়মিত পরিকল্পনাই দেখেন। ?is_trial=1
            # চেয়েও পাবেন না — ট্রায়ালের পরিকল্পনা অতিথিদের জন্য সাজানো
            # (একাডেমির প্রথম পরিচয়), নিয়মিত পাঠ্যসূচি নয়।
            return qs.filter(is_trial=False, course__students=u).distinct()
        if list_only:
            qs = qs.filter(is_trial=want_trial)
        if u.role == "teacher":
            return qs.filter(
                Q(course__teacher=u) | Q(course__students__teacher=u)
            ).distinct()
        return qs

    def _student_id(self):
        """কোন শিক্ষার্থীর টিক দেখানো হবে — LectureViewSet-এর মতোই নিয়ম।"""
        u = self.request.user
        if u.role == "student":
            return u.id
        raw = self.request.query_params.get("student")
        try:
            return int(raw) if raw else None
        except (TypeError, ValueError):
            return None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["student_id"] = self._student_id()
        return ctx

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def ensure(self, request):
        """কোর্সে হেডিং না থাকলে সাতটি ডিফল্ট বানিয়ে দেয়।

        নতুন কোর্সে পরিচালককে একটা একটা করে হেডিং লিখতে না হয়, সেজন্য।
        আগে থেকে হেডিং থাকলে কিছুই করে না — তাই বারবার ডাকা নিরাপদ।
        """
        cid = request.data.get("course")
        course = Course.objects.filter(pk=cid).first()
        if not course:
            return Response({"error": "কোর্স খুঁজে পাওয়া যায়নি"}, status=400)
        # নিয়মিত ও ট্রায়াল — দুটোর হেডিং আলাদাভাবে গোনা হয়, তাই একটির
        # হেডিং থাকলেও অন্যটির ডিফল্টগুলো ঠিকই তৈরি হবে
        trial = bool(request.data.get("is_trial"))
        if not LessonSection.objects.filter(course=course, is_trial=trial).exists():
            LessonSection.objects.bulk_create([
                LessonSection(course=course, name=n, order=i, is_trial=trial)
                for i, n in enumerate(DEFAULT_SECTIONS)
            ])
        rows = LessonSection.objects.filter(
            course=course, is_trial=trial
        ).prefetch_related("topics", "topics__coverages").select_related("course")
        return Response(self.get_serializer(rows, many=True).data)

    @action(detail=True, methods=["put"], permission_classes=[IsDirector])
    def topics(self, request, pk=None):
        """হেডিংয়ের নিচের টপিকগুলো একবারে সংরক্ষণ — [{id?, text, content}, …]

        দারস (Lecture) আর ব্যবহার হয় না; টপিক সরাসরি হেডিংয়ের নিচে বসে।
        তবু LectureTopic.lecture ঘরটি বাধ্যতামূলক, তাই কোর্স-প্রতি একটি
        লুকানো "ধারক" দারস রাখা হয় — পর্দায় কোথাও দেখানো হয় না।

        ⚠️ আইডি মিলিয়ে পুরনো টপিকই হালনাগাদ হয়, নতুন করে বানানো হয় না —
        নইলে প্রতিবার সংরক্ষণে কভারের টিক (প্রতি শিক্ষার্থীর) হারিয়ে যেত।
        """
        section = self.get_object()
        blocks = request.data.get("topics")
        if not isinstance(blocks, list):
            return Response({"error": "topics তালিকা দিন"}, status=400)
        if len(blocks) > 200:
            return Response({"error": "একটি হেডিংয়ে সর্বোচ্চ ২০০টি টপিক"},
                            status=400)

        holder = Lecture.objects.filter(course=section.course).order_by("id").first()
        if not holder:
            holder = Lecture.objects.create(
                course=section.course, no=1, title="দারস তালিকা")

        existing = {t.id: t for t in section.topics.all()}
        kept, order = set(), 0
        for b in blocks:
            if not isinstance(b, dict):
                continue
            text = str(b.get("text") or "").strip()[:300]
            if not text:
                continue  # শিরোনামহীন টগল রাখার মানে নেই
            content = clean_html(str(b.get("content") or "")[:100000])
            t = existing.get(b.get("id"))
            if t:
                t.text, t.content, t.order = text, content, order
                t.save(update_fields=["text", "content", "order"])
                kept.add(t.id)
            else:
                LectureTopic.objects.create(
                    lecture=holder, section=section, text=text,
                    content=content, order=order)
            order += 1
        for tid, t in existing.items():
            if tid not in kept:
                t.delete()  # পরিচালক নিজে সরিয়ে দিয়েছেন
        section.refresh_from_db()
        return Response(self.get_serializer(section).data)

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def reorder(self, request):
        """হেডিংগুলোর ক্রম — [id, id, ...] যে ক্রমে পাঠানো হয় সেই ক্রমেই বসে।"""
        ids = request.data.get("ids") or []
        rows = {x.id: x for x in LessonSection.objects.filter(id__in=ids)}
        changed = []
        for i, sid in enumerate(ids):
            r = rows.get(sid)
            if r and r.order != i:
                r.order = i
                changed.append(r)
        if changed:
            LessonSection.objects.bulk_update(changed, ["order"])
        return Response({"ok": True})


class LectureViewSet(viewsets.ModelViewSet):
    # prefetch_related("topics") → নেস্টেড topics প্রতি লেকচারে আলাদা কোয়েরি না করে
    # prefetch cache ব্যবহার করে (N+1 এড়ায়) — লেকচার প্ল্যান পেজে সব দারসের টপিক দেখায়
    queryset = Lecture.objects.prefetch_related(
        "topics", "topics__coverages", "topics__section"
    ).all()
    serializer_class = LectureSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["course"]

    def get_queryset(self):
        """⚠️ ট্রায়াল অতিথির জন্য এই পুরনো পথটি বন্ধ। বাকি সবার জন্য আগের
        মতোই — এখানে ভূমিকা দেখে কোনো ছাঁকনি ছিল না, নতুন করেও বসানো হয়নি,
        যাতে কারও কিছু বদলে না যায়।"""
        if self.request.user.role == "trial":
            return Lecture.objects.none()
        return super().get_queryset()

    def _student_id(self):
        """কোন শিক্ষার্থীর টিক দেখানো হবে।

        শিক্ষার্থী নিজে দেখলে সবসময় নিজেরটাই — অন্য কারও টিক সে দেখতে
        পাবে না। উস্তাদ/এডমিন ?student=<id> দিয়ে বেছে নেন।
        """
        u = self.request.user
        if u.role == "student":
            return u.id
        raw = self.request.query_params.get("student")
        try:
            return int(raw) if raw else None
        except (TypeError, ValueError):
            return None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["student_id"] = self._student_id()
        return ctx

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_topic(self, request):
        """টপিক ✔/✘ — উস্তাদ নিজের কোর্সে; লাল-ক্রস ঠিক করা কেবল এডমিন-লেভেল বা অনুমতিপ্রাপ্ত"""
        topic = LectureTopic.objects.get(pk=request.data["topic_id"])
        new = request.data.get("covered")  # covered | missed | pending
        valid = [c[0] for c in LectureTopic.Covered.choices]
        if new not in valid:  # boolean/অবৈধ মান CharField-এ সেভ হয়ে ডেটা নষ্ট হওয়া ঠেকাতে
            return Response({"detail": "covered মান অবৈধ — covered/missed/pending হতে হবে।"}, status=400)
        u = request.user
        is_admin = u.role in ("director", "admin") or u.can_fix_cross
        is_course_teacher = topic.lecture.course.teacher_id == u.id
        # কোর্সের উস্তাদ না হয়েও এই কোর্সে নিজের শিক্ষার্থী থাকলে টিক দিতে পারেন
        has_own_student = topic.lecture.course.students.filter(teacher=u).exists()
        if not (is_admin or is_course_teacher or has_own_student):
            return Response({"detail": "অনুমতি নেই"}, status=403)

        # ── কোন শিক্ষার্থীর জন্য? ──
        # student_id দিলে টিকটা কেবল সেই শিক্ষার্থীর জন্য বসে — অন্য কারও
        # পোর্টালে দেখাবে না। না দিলে আগের মতোই সবার জন্য একটাই মান বসে
        # (পুরনো ক্লায়েন্ট বা পরিচালকের সাধারণ সংশোধনের জন্য)।
        sid = request.data.get("student_id")
        if sid:
            try:
                sid = int(sid)
            except (TypeError, ValueError):
                return Response({"detail": "student_id অবৈধ"}, status=400)
            if not topic.lecture.course.students.filter(pk=sid).exists():
                return Response(
                    {"detail": "এই শিক্ষার্থী এই কোর্সে নেই"}, status=400)
            # ⚠️ উস্তাদ কেবল নিজের শিক্ষার্থীর জন্যই টিক দিতে পারবেন। এক
            # কোর্সে একাধিক উস্তাদ থাকায় এটা না থাকলে একজন উস্তাদ অন্যজনের
            # শিক্ষার্থীর হিসাবে টিক দিয়ে ফেলতে পারতেন।
            if not is_admin and not User.objects.filter(
                pk=sid, teacher_id=u.id
            ).exists():
                return Response(
                    {"detail": "এই শিক্ষার্থী আপনার কাছে পড়ে না"}, status=403)
            row, _ = TopicCoverage.objects.get_or_create(topic=topic, student_id=sid)
            if row.covered == "missed" and not is_admin:
                return Response(
                    {"detail": "লাল ক্রস কেবল এডমিন/পরিচালক ঠিক করতে পারবেন।"},
                    status=403)
            row.covered = new
            row.marked_by = u
            row.save()
            if not topic.lecture.date:
                topic.lecture.date = timezone.localtime().date()
                topic.lecture.save()
            return Response(
                LectureTopicSerializer(topic, context={"student_id": sid}).data)

        if topic.covered == "missed" and not is_admin:
            return Response({"detail": "লাল ক্রস কেবল এডমিন/পরিচালক ঠিক করতে পারবেন।"}, status=403)
        topic.covered = new
        topic.marked_by = u
        topic.marked_at = timezone.now()
        topic.save()
        if not topic.lecture.date:
            topic.lecture.date = timezone.localtime().date()
            topic.lecture.save()
        return Response(LectureTopicSerializer(topic).data)


# ─────────────────────────── রুটিন ও ক্লাস ───────────────────────────
class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer
    permission_classes = [ReadAllWriteAdmin]

    def get_queryset(self):
        u = self.request.user
        # select_related/prefetch → course_name/teacher_name/student_names আনতে
        # প্রতি সারিতে বাড়তি কোয়েরি (N+1) এড়ায় — তালিকা দ্রুত লোড হয়
        qs = (
            Routine.objects.filter(is_active=True)
            .select_related("course", "teacher")
            .prefetch_related("students", "student_schedules")
        )
        if u.role == "teacher":
            # রুটিনের নির্ধারিত উস্তাদ, অথবা রুটিনে তাঁর নিজের শিক্ষার্থী আছে
            return qs.filter(Q(teacher=u) | Q(students__teacher=u)).distinct()
        if u.role == "student":
            return qs.filter(students=u)
        # ⚠️ ট্রায়াল অতিথিকে আলাদা করে ধরতেই হবে। নিচের শেষ "return qs"
        # পরিচালক/এডমিনের জন্য — কোনো ছাঁকনি ছাড়া সব। নতুন ভূমিকা যোগ করার
        # পর ট্রায়ালও সেখানে গিয়ে পড়ত, অর্থাৎ একজন সাময়িক অতিথি একাডেমির
        # সবকিছু দেখে ফেলতেন।
        if u.role == "trial":
            return qs.none()  # অতিথির নিজের রুটিন নেই, ক্লাসের সময় বলে দেওয়া হয়
        return qs

    def _generate_now(self, routine):
        # রুটিন যোগ/এডিটের সাথে সাথেই ওই রুটিনের আগামী ৭ দিনের ক্লাস তৈরি (দৈনিক ক্রনের অপেক্ষা না করে)
        # → উস্তাদ ও শিক্ষার্থীর পোর্টালে তখনই দেখা যায় (idempotent — ডুপ্লিকেট হয় না)
        try:
            from .tasks import generate_for_routine
            generate_for_routine(routine)
        except Exception:
            pass

    def _sync_upcoming_sessions(self, routine):
        # রুটিন এডিট করলে আগে শুধু *নতুন* তারিখের জন্য ক্লাস তৈরি হতো — যেসব
        # তারিখের ক্লাস-সেশন এই এডিটের আগেই তৈরি হয়ে গিয়েছিল (আগামী ৭ দিনের
        # মধ্যে), সেগুলো পুরনো মানেই থেকে যেত, তাই টিচার-স্টুডেন্ট পোর্টালে
        # পরিবর্তন দেখাই যেত না। এখন এডিটের সাথে সাথে "আজ বা পরে, এখনো শুরু
        # হয়নি" এমন সেশনগুলোকেও নতুন মান দিয়ে হালনাগাদ করে দেওয়া হয় — সময়/
        # সময়কাল/জুম লিংকের পাশাপাশি এখন কোর্স, উস্তাদ ও স্টুডেন্ট তালিকাও।
        try:
            today = timezone.localtime().date()
            # বার বদলালে আগে যে তারিখগুলোতে ক্লাস তৈরি হয়ে গিয়েছিল সেগুলো রুটিনে
            # আর না থাকলেও রয়ে যেত (শুধু নতুন সময় বসত), আর নতুন বারেও ক্লাস তৈরি
            # হতো — ফলে দুই বারেই ক্লাস দেখাত। তাই আগে বাতিল-হয়ে-যাওয়া বারের
            # আসন্ন সেশনগুলো সরিয়ে ফেলা হয়। যেখানে কেউ ইতিমধ্যে জয়েন করে ফেলেছেন
            # সেগুলো রাখা হয় — সেই ক্লাস বাস্তবে হয়ে গেছে, হাজিরা হারানো যাবে না
            from .tasks import _js_to_py
            valid_weekdays = _js_to_py(routine.days or [])
            for s in ClassSession.objects.filter(
                routine=routine, date__gte=today, status="upcoming",
            ):
                if s.date.weekday() not in valid_weekdays and not s.attendance.exists():
                    s.delete()
            qs = ClassSession.objects.filter(
                routine=routine, date__gte=today, status="upcoming",
            )
            qs.update(
                time=routine.time,
                duration_min=routine.duration_min,
                zoom_link=routine.zoom_link,
                zoom_link_2=routine.zoom_link_2,
                course=routine.course,
                teacher=routine.teacher,
            )
            # students ManyToMany — bulk .update() দিয়ে হয় না, প্রতিটা সেশনে
            # আলাদাভাবে .set() করতে হয়
            new_students = list(routine.students.all())
            for s in qs:
                s.students.set(new_students)
        except Exception:
            pass

    def _save_student_schedules(self, routine):
        # "student_schedules": [{student, days, time}, ...] — পরিচালক প্রতিটি
        # শিক্ষার্থীর জন্য ম্যানুয়ালি বসানো তাদের নিজের সময়ের বার+সময় (কোনো
        # স্বয়ংক্রিয় টাইমজোন-হিসাব নয়) — key দেওয়া থাকলে সম্পূর্ণ প্রতিস্থাপন
        # করা হয় (আগের এন্ট্রি মুছে নতুন করে বসানো), যাতে বাদ পড়া/সরানো
        # স্টুডেন্টের পুরনো এন্ট্রি থেকে না যায়। কিন্তু payload-এ এই key-ই না
        # থাকলে (যেমন ভবিষ্যতে কোনো আংশিক PATCH যা শুধু সময়/দিন বদলাতে চায়)
        # বিদ্যমান override মুছে ফেলা হবে না — শুধু "খালি তালিকা পাঠানো" মানেই
        # ইচ্ছাকৃতভাবে সব সাফ করা, key অনুপস্থিত থাকা মানে অস্পৃশ্য রাখা
        if "student_schedules" not in self.request.data:
            return
        try:
            payload = self.request.data.get("student_schedules") or []
            routine.student_schedules.all().delete()
            objs = []
            valid_student_ids = set(routine.students.values_list("id", flat=True))
            for item in payload:
                sid = item.get("student")
                if sid not in valid_student_ids:
                    continue
                objs.append(RoutineStudentSchedule(
                    routine=routine, student_id=sid,
                    days=item.get("days") or [], time=item.get("time") or None,
                ))
            if objs:
                RoutineStudentSchedule.objects.bulk_create(objs)
        except Exception:
            pass

    def perform_create(self, serializer):
        routine = serializer.save()
        self._save_student_schedules(routine)
        self._generate_now(routine)

    def perform_update(self, serializer):
        routine = serializer.save()
        self._save_student_schedules(routine)
        self._sync_upcoming_sessions(routine)
        self._generate_now(routine)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminLevel])
    def generate(self, request):
        """সব সক্রিয় রুটিনের আগামী ৭ দিনের ক্লাস তৈরি/নিশ্চিত করা — পরিচালক/এডমিন এক ক্লিকে
        পুরোনো রুটিনগুলোরও ক্লাস পোর্টালে আনতে পারবেন (idempotent)"""
        from .tasks import generate_routine_sessions
        created = generate_routine_sessions()
        return Response({"created": created})


def _att_defaults(s):
    """session থেকে denormalized স্ন্যাপশট — ৬০ দিন পর পুরনো ClassSession মুছে
    গেলেও (SET_NULL) হাজিরা রেকর্ড কোন কোর্স/উস্তাদ/তারিখের ছিল তা ধরে রাখে"""
    teacher = s.teacher or (s.course.teacher if s.course_id else None)
    return {
        "class_date": s.date,
        "course_name": s.course.name if s.course_id else "",
        "teacher_id": teacher.id if teacher else None,
        "teacher_name": teacher.name_bn if teacher else "",
    }


# ─────────── উস্তাদের এখতিয়ার — কার উপর তাঁর নিয়ন্ত্রণ ───────────
# নিয়মটা এক জায়গাতেই লেখা, সব ভিউ এখান থেকেই ব্যবহার করে। ছড়িয়ে থাকলে
# এক জায়গায় বদলে অন্য জায়গায় ভুলে যাওয়ার ঝুঁকি থাকত।
#
# উস্তাদ নিয়ন্ত্রণ করেন —
#   (১) যে শিক্ষার্থীরা তাঁর কাছে পড়ে (User.teacher = তিনি), এবং
#   (২) যে কোর্স/ক্লাসের তিনি নির্ধারিত উস্তাদ (পুরনো ব্যবস্থা, যাতে কারও
#       নিজস্ব উস্তাদ বসানো না থাকলেও কিছু হারিয়ে না যায়)।
def teacher_owns_student(user, student):
    """এই শিক্ষার্থী কি এই উস্তাদের?"""
    if not student:
        return False
    return getattr(student, "teacher_id", None) == user.id


def _q_teacher_course(u):
    """উস্তাদের কোর্স — নিজে কোর্সের উস্তাদ, অথবা কোর্সে তাঁর শিক্ষার্থী আছে।"""
    return Q(teacher=u) | Q(students__teacher=u)


def _q_course_teacher_or_own_lesson(u):
    """ধাপ → দারস → কোর্স — উস্তাদ নিজের কোর্সের ধাপগুলোই দেখেন।"""
    return (Q(lesson__course__teacher=u)
            | Q(lesson__course__students__teacher=u))


def _q_course_teacher_or_own(u):
    """একই নিয়ম, কিন্তু course-এর মধ্য দিয়ে (assignment/exam ইত্যাদির জন্য)।"""
    return Q(course__teacher=u) | Q(course__students__teacher=u)


def _assert_session_participant(s, user):
    """join/leave/checkpoint শুধু ওই নির্দিষ্ট ক্লাসের আসল উস্তাদ বা তালিকাভুক্ত
    স্টুডেন্টই করতে পারবেন। এডমিন/পরিচালকের get_queryset() কোনো ফিল্টার ছাড়াই
    সব ক্লাস দেখায় (রিপোর্টের জন্য দরকার), তাই সেই queryset-এর ওপর ভিত্তি করে
    get_object() সফল হয়ে গেলেও এখানে আলাদাভাবে আটকানো না হলে এডমিন/পরিচালক
    কোনো ক্লাসে "জয়েন" করে ফেললে _sync_mutual_presence তাকে ভুলবশত স্টুডেন্ট
    ধরে নিয়ে আসল স্টুডেন্ট না এলেও হাজিরা 'নিশ্চিত' করে ফেলতে পারত"""
    if user.role == "teacher":
        # get_queryset() উস্তাদকে ক্লাসটা দেখায় যদি তিনি সেশনের উস্তাদ *অথবা*
        # কোর্সের উস্তাদ হন — জয়েনের নিয়মও ঠিক একই রাখতে হবে। আগে শুধু সেশনের
        # উস্তাদকেই অনুমতি দেওয়া হতো, ফলে কোর্সের উস্তাদ ক্লাসটা তালিকায় দেখেও
        # জয়েন করতে গেলে আটকে যেতেন (স্টুডেন্ট জয়েন করে বসে থাকতেন, উস্তাদ
        # ঢুকতেই পারতেন না)
        allowed = {s.teacher_id, s.course.teacher_id if s.course_id else None}
        # নিজের কোনো শিক্ষার্থী এই ক্লাসে থাকলেও তিনি এই ক্লাসের উস্তাদ —
        # এক কোর্সে একাধিক উস্তাদ থাকলে এটাই আসল সূত্র
        if user.id not in allowed and not s.students.filter(teacher=user).exists():
            raise PermissionDenied("এই ক্লাসের উস্তাদ আপনি নন")
    elif user.role in ("student", "trial"):
        if user.role == "trial" and user.trial_expired:
            raise PermissionDenied("আপনার ট্রায়ালের মেয়াদ শেষ হয়েছে")
        # ট্রায়াল অতিথিও ঠিক শিক্ষার্থীর মতোই — এই ক্লাসের তালিকায় থাকলে
        # জয়েন করতে পারবেন, না থাকলে নয়
        if not s.students.filter(pk=user.id).exists():
            raise PermissionDenied("এই ক্লাসে আপনি যুক্ত নন")
    else:
        raise PermissionDenied("শুধু ক্লাসের উস্তাদ বা শিক্ষার্থীই জয়েন করতে পারবেন")


# হাজিরার হিসাবে যাঁদের "শিক্ষার্থী" ধরা হয়। ট্রায়াল অতিথিও ক্লাসে বসেন,
# তাই তাঁকেও গুনতে হয় — কিন্তু ফি/বকেয়া/রিপোর্টের কোয়েরিগুলো আগের মতোই
# শুধু role="student" ধরে চলে, সেখানে ট্রায়াল ঢোকে না।
STUDENT_LIKE_ROLES = ("student", "trial")


def _finalize_session(s, by=None, mark_done=True):
    """ক্লাসের একটি পর্ব শেষ করা — একটাই জায়গা, সবাই এখান থেকেই ডাকে।

    এখানে যা হয় —
      ১) খোলা থাকা প্রত্যেকের সেগমেন্ট বন্ধ হয়ে জমে থাকা মিনিট হাজিরায় যোগ
         হয় (কারও তথ্য "জমা হওয়ার অপেক্ষায়" ঝুলে থাকে না),
      ২) দুজনেই এসে থাকলে হাজিরা পাকাপাকি নিশ্চিত হয়,
      ৩) mark_done=True হলে ক্লাসটি "সম্পন্ন" হিসেবে তালিকাবদ্ধ হয়।

    mark_done কেন ঐচ্ছিক — একটি ক্লাস দুই পর্বে হয় (জুমের সময়সীমার কারণে
    ১ম ও ২য় লিংক)। ১ম পর্ব শেষ হলে মিনিট-হাজিরা ঠিকই গুছিয়ে রাখতে হয়, কিন্তু
    ক্লাসটি তখনো "সম্পন্ন" নয় — ২য় পর্ব বাকি। তাই তখন mark_done=False।

    উস্তাদ শেষ পর্বে "ক্লাস শেষ করুন" চাপলে, আর পরিচালক/এডমিন ক্লাসকে
    "সম্পন্ন" চিহ্নিত করলে — দুই পথেই পুরো ক্লাস শেষ হয়। তাই উস্তাদ ভুলে গেলে
    পরিচালক চিহ্নিত করলেই ক্লাস শেষ হিসেবে গণ্য হয়।
    """
    _sync_mutual_presence(s)  # শেষ করার আগে হাজিরাটা পাকা করে নিই
    now = timezone.now()
    open_rows = list(Attendance.objects.filter(session=s, segment_start__isnull=False))
    for a in open_rows:
        a.minutes += max(0, int((now - a.segment_start).total_seconds() // 60))
        a.segment_start = None
        a.left_at = now
    if open_rows:
        Attendance.objects.bulk_update(open_rows, ["minutes", "segment_start", "left_at"])
    fields = []
    if mark_done and s.status != "done":
        s.status = "done"
        fields.append("status")
    if not s.date:
        s.date = timezone.localtime().date()
        fields.append("date")
    if fields:
        s.save(update_fields=fields)
    return s


def _sync_mutual_presence(s):
    """উস্তাদ ও অন্তত একজন স্টুডেন্ট একই সময়ে (দুজনেই) মিটিংয়ে থাকলে সাথে সাথেই
    উভয়ের হাজিরা 'সম্পন্ন' মার্ক করে — এরপর কেউ কতক্ষণ থাকলেন তা আর হাজিরার
    জন্য গুরুত্বপূর্ণ না, শুধু জয়েন হওয়াটাই যথেষ্ট (পোর্টালে সতর্কতার জন্য এখনো
    "৪৫+ মিনিট" লেখা থাকে, কিন্তু বাস্তবে এই মিনিটের হিসাব আর গণনা হয় না)"""
    teacher_id = s.teacher_id or (s.course.teacher_id if s.course_id else None)
    if not teacher_id:
        return
    rows = list(Attendance.objects.filter(session=s).select_related("user"))
    teacher_row = next((r for r in rows if r.user_id == teacher_id), None)
    teacher_active = bool(teacher_row and teacher_row.segment_start is not None)
    # ⚠️ "শিক্ষার্থী আছেন" বলতে সত্যিই শিক্ষার্থী বোঝাতে হবে। আগে শর্ত ছিল
    # শুধু "এই সারিটি উস্তাদের নয়" — ভূমিকা দেখা হতো না। ফলে দ্বিতীয় কোনো
    # উস্তাদ, এডমিন বা পরিচালক ক্লাসে ঢুকলেই তাঁকে শিক্ষার্থী ধরে নিয়ে
    # দুজনের হাজিরাই "নিশ্চিত" হয়ে যেত — একজন শিক্ষার্থীও না এসে।
    # এক কোর্সে একাধিক উস্তাদ চালু হওয়ার পর এটা আরও সহজে ঘটত।
    student_rows_active = [
        r for r in rows
        if r.user_id != teacher_id
        and r.segment_start is not None
        # ট্রায়াল শিক্ষার্থীও এখানে শিক্ষার্থীই — নইলে ট্রায়াল ক্লাসে উস্তাদ
        # চিরকাল "শিক্ষার্থীর অপেক্ষায়" দেখতেন, হাজিরাও নিশ্চিত হতো না
        and getattr(r.user, "role", None) in STUDENT_LIKE_ROLES
    ]
    if not (teacher_active and student_rows_active):
        return
    to_mark = [r.id for r in student_rows_active if not r.marked_present]
    if teacher_row and not teacher_row.marked_present:
        to_mark.append(teacher_row.id)
    if to_mark:
        Attendance.objects.filter(id__in=to_mark).update(marked_present=True)


class ClassSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSessionSerializer
    permission_classes = [ReadAllWriteAdmin]

    def get_queryset(self):
        u = self.request.user
        # select_related/prefetch → course_name/teacher_name/student_names আনতে
        # প্রতি সারিতে বাড়তি কোয়েরি (N+1) এড়ায় — "আজকের/আসন্ন ক্লাস" দ্রুত লোড হয়।
        # attendance/attendance__user prefetch না থাকলে ClassSessionSerializer-এর নেস্টেড
        # AttendanceSerializer প্রতি ক্লাসে + প্রতি হাজিরায় আলাদা কোয়েরি করত (ডাবল N+1)
        qs = ClassSession.objects.select_related(
            "course", "teacher", "course__teacher"
        ).prefetch_related("students", "attendance", "attendance__user")
        if u.role == "teacher":
            # সেশনের উস্তাদ, কোর্সের উস্তাদ, অথবা এই ক্লাসে তাঁর নিজের কোনো
            # শিক্ষার্থী আছে — যেকোনোটিতেই ক্লাসটি দেখতে পান
            return qs.filter(
                Q(teacher=u) | Q(course__teacher=u) | Q(students__teacher=u)
            ).distinct()
        if u.role == "student":
            return qs.filter(students=u)
        # ⚠️ ট্রায়াল অতিথিকে আলাদা করে ধরতেই হবে। নিচের শেষ "return qs"
        # পরিচালক/এডমিনের জন্য — কোনো ছাঁকনি ছাড়া সব। নতুন ভূমিকা যোগ করার
        # পর ট্রায়ালও সেখানে গিয়ে পড়ত, অর্থাৎ একজন সাময়িক অতিথি একাডেমির
        # সবকিছু দেখে ফেলতেন।
        if u.role == "trial":
            # মেয়াদ ফুরালে ক্লাস সরে যায় — রিপোর্ট ও প্রস্তাব থেকে যায়
            if u.trial_expired:
                return qs.none()
            return qs.filter(students=u)  # কেবল তাঁর নিজের ট্রায়াল ক্লাস
        return qs

    def perform_update(self, serializer):
        # আজকের ক্লাস "সম্পন্ন" চিহ্নিত করা এডমিন+পরিচালক দুজনেই পারবেন — কিন্তু
        # বিগত (পুরনো) ক্লাসের স্ট্যাটাস সংশোধন কেবল পরিচালকের এখতিয়ার, এডমিন না
        if "status" in self.request.data and self.request.user.role != "director":
            is_today = serializer.instance.date == timezone.localtime().date()
            if not is_today:
                raise PermissionDenied("আজকের ক্লাস ছাড়া অন্য কোনো ক্লাসের স্ট্যাটাস বদলানো কেবল পরিচালকের এখতিয়ার")
        was = serializer.instance.status
        obj = serializer.save()
        # "সম্পন্ন" চিহ্নিত করাও ক্লাস শেষ করার সমান — উস্তাদ "ক্লাস শেষ করুন"
        # চাপতে ভুলে গেলে পরিচালক/এডমিন এই পথেই সব গুছিয়ে দিতে পারেন
        # (জমে থাকা মিনিট বসে, হাজিরা পাকা হয়)
        if obj.status == "done" and was != "done":
            _finalize_session(obj, by=self.request.user)
        # উস্তাদ ভুল করে "ক্লাস শেষ করুন" চেপে ফেললে ফেরার পথ — কর্তৃপক্ষ
        # ক্লাসটিকে আবার "আসন্ন" করে দিলে যাচাই-বাকি অবস্থাও মুছে যায়, ফলে
        # জয়েন/রিজয়েন বাটন ফিরে আসে এবং ক্লাসটি আবার চালানো যায়।
        # ⚠️ কেবল স্ট্যাটাস বদলানোর অনুরোধেই — নইলে জুম লিংক বা সময় এডিট
        # করতে গেলেই যাচাই-বাকি অবস্থাটা অজান্তে মুছে যেত।
        if (
            "status" in self.request.data
            and obj.status == "upcoming"
            and obj.teacher_finished
        ):
            obj.teacher_finished = False
            obj.save(update_fields=["teacher_finished"])

    @action(detail=False, permission_classes=[IsAuthenticated])
    def today(self, request):  # লাইভ পপআপ + "আজকের ক্লাস"
        # date.today() সার্ভারের (UTC) তারিখ দেয়, বাংলাদেশ সময়ের নয় — মধ্যরাত থেকে
        # ভোর ৬টার মধ্যে এটা "গতকাল" ধরে ফেলত (UTC তখনও আগের দিন) — তাই
        # timezone.localtime() দিয়ে Asia/Dhaka অনুযায়ী প্রকৃত "আজ" বের করা হচ্ছে
        qs = self.get_queryset().filter(date=timezone.localtime().date(), status="upcoming")
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):  # জুমে জয়েন → নতুন সেগমেন্ট শুরু
        s = self.get_object()
        _assert_session_participant(s, request.user)
        att, _ = Attendance.objects.get_or_create(
            session=s, user=request.user, defaults=_att_defaults(s)
        )
        if att.segment_start is None:  # আগের সেগমেন্ট বন্ধ থাকলেই নতুন শুরু
            att.segment_start = timezone.now()
            att.save(update_fields=["segment_start"])
        _sync_mutual_presence(s)  # উস্তাদ+স্টুডেন্ট দুজনেই থাকলে সাথে সাথেই হাজিরা 'সম্পন্ন'
        att.refresh_from_db()
        return Response(AttendanceSerializer(att).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):  # সেগমেন্ট শেষ → মিনিট যোগ (সব মিলিয়ে ৪৫-মিনিট নিয়ম)
        s = self.get_object()
        _assert_session_participant(s, request.user)
        att = Attendance.objects.get(session=s, user=request.user)
        add = request.data.get("minutes")  # ক্লায়েন্টের হিসাব করা "দুজন-উপস্থিত" মিনিট (দিলে সেটাই যোগ)
        if add is not None:
            try: att.minutes += max(0, int(add))
            except (TypeError, ValueError): pass
        elif att.segment_start:
            att.minutes += max(0, int((timezone.now() - att.segment_start).total_seconds() // 60))
        att.segment_start = None
        att.left_at = timezone.now()
        att.save(update_fields=["minutes", "segment_start", "left_at"])
        return Response(AttendanceSerializer(att).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def checkpoint(self, request, pk=None):
        # প্রতি ৬০ সেকেন্ডে ব্যাকগ্রাউন্ডে হাজিরার মিনিট সেভ — leave+join (যা
        # segment_start সাময়িকভাবে None করে দিত) ব্যবহার করলে অন্যপাশের প্রেজেন্স
        # পোল সেই মুহূর্তে "চলে গেছেন" ভুল বুঝে তার কাউন্টার থামিয়ে দিতে পারত।
        # এই এন্ডপয়েন্ট শুধু মিনিট যোগ করে, segment_start/left_at স্পর্শ করে না —
        # তাই "উপস্থিত আছি" অবস্থা কখনো বিঘ্নিত হয় না
        s = self.get_object()
        _assert_session_participant(s, request.user)
        att = Attendance.objects.get(session=s, user=request.user)
        add = request.data.get("minutes")
        try:
            att.minutes += max(0, int(add))
        except (TypeError, ValueError):
            return Response({"error": "minutes আবশ্যক"}, status=400)
        att.save(update_fields=["minutes"])
        return Response(AttendanceSerializer(att).data)

    @action(detail=True, permission_classes=[IsAuthenticated])
    def presence(self, request, pk=None):  # কে এখন মিটিংয়ে আছে — দুজন-জয়েন গেটিং এর জন্য
        s = self.get_object()
        _sync_mutual_presence(s)  # নিরাপত্তা-জাল — join-এর সময় কোনোভাবে মিস হলেও এখানে ধরা পড়বে
        teacher_id = s.teacher_id or (s.course.teacher_id if s.course_id else None)
        rows = Attendance.objects.filter(session=s).select_related("user")
        return Response({
            "attendance": AttendanceSerializer(rows, many=True).data,
            "teacher_active": rows.filter(user_id=teacher_id, segment_start__isnull=False).exists() if teacher_id else False,
            # একই কারণে এখানেও ভূমিকা যাচাই — উস্তাদ/এডমিন ঢুকলে যেন
            # অন্যপাশে "শিক্ষার্থী এসে গেছেন" না দেখায়
            "any_student_active": rows.filter(
                segment_start__isnull=False, user__role__in=STUDENT_LIKE_ROLES
            ).exclude(user_id=teacher_id).exists(),
            # ⚠️ শিক্ষার্থীর পর্দার জন্য দরকারি দুটি খবর। "উস্তাদ আর নেই" দেখেই
            # আগে শিক্ষার্থীর ক্লাস শেষ করে দেওয়া হতো — কিন্তু উস্তাদের সেগমেন্ট
            # এখন তিনভাবে বন্ধ হতে পারে: ১ম পর্ব শেষ, 🔄 পুনঃসংযোগ, আর সত্যিকারের
            # ক্লাস শেষ। তিনটিকে আলাদা করতে না পারলে শিক্ষার্থী ভুল বার্তা পান।
            "rejoin_active": s.join_mode_override == "rejoin",
            # "ক্লাস আর চলছে না" — উস্তাদ শেষ করেছেন, অথবা কর্তৃপক্ষ "সম্পন্ন"
            # চিহ্নিত করেছেন। শিক্ষার্থীর পর্দা এই একটি খবরেই ক্লাস গুটিয়ে নেয়।
            "done": s.status == "done" or s.teacher_finished,
        })

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def mark_attendance(self, request, pk=None):  # পরিচালকের ম্যানুয়াল হাজিরা (৪৫ মিনিটের কম হলেও)
        s = self.get_object()
        att, _ = Attendance.objects.get_or_create(
            session=s, user_id=request.data["student_id"], defaults=_att_defaults(s)
        )
        att.marked_present = bool(request.data.get("present", True))
        att.save(update_fields=["marked_present"])
        return Response(AttendanceSerializer(att).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminLevel])
    def postpone(self, request, pk=None):  # ⛔ স্থগিত → নোটিফিকেশন + WhatsApp আউটবক্স
        s = self.get_object()
        s.status = "postponed"
        s.save()
        studs = list(s.students.all())
        msg = (f"⛔ {s.course.name} ক্লাসটি ({s.date}, {s.time}) অনিবার্য কারণে / "
               f"উস্তাদ-উস্তাদা অসুস্থ থাকার দরুন স্থগিত করা হয়েছে। "
               f"পরবর্তীতে শিডিউল করে মেকআপ করা হবে ইনশাআল্লাহ।")
        # s.teacher নাল হতে পারে (টিচারের অ্যাকাউন্ট মুছে ফেললে পুরনো ক্লাস-সেশনে
        # SET_NULL হয়ে যায়) — না ছেঁকে পাঠালে notify()-এর recipients.set() এ
        # None ঢুকে ৫০০ এরর দিত, অথচ স্ট্যাটাস ততক্ষণে সেভ হয়ে গেছে
        # s.teacher নাল হতে পারে (টিচারের অ্যাকাউন্ট মুছে ফেললে পুরনো ক্লাস-সেশনে
        # SET_NULL হয়ে যায়) — Django এমনিতেই None নিঃশব্দে বাদ দেয় (ক্র্যাশ করে
        # না), তবু স্পষ্টভাবে ছেঁকে দেওয়া বেশি নির্ভরযোগ্য ও উদ্দেশ্য-স্পষ্ট
        notify(msg, studs + ([s.teacher] if s.teacher_id else []) + list(admins()))
        for st in studs:  # অভিভাবকের WhatsApp — Celery টাস্ক পাঠাবে
            if st.phone:
                WaMessage.objects.create(to_name=st.guardian or st.name_bn, student=st,
                                         phone=st.phone, text=msg, reason="postpone")
        return Response({"status": "postponed"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdminLevel])
    def set_join_mode(self, request, pk=None):
        # স্বয়ংক্রিয় জয়েন/রিজয়েন-নির্ধারণ (দুজনের হাজিরার ওপর ভিত্তি করে) কোনো
        # কারণে ঠিকমতো না এলে, পরিচালক/এডমিন এখান থেকে জয়েন বা রিজয়েন — যেকোনো
        # একটা লিংক জোর করে চালু করতে পারবেন, বা "auto"-তে ফিরিয়ে দিতে পারবেন —
        # হাজিরার ডেটায় কোনো পরিবর্তন হয় না, শুধু বাটনের অবস্থা বদলায়
        s = self.get_object()
        mode = request.data.get("mode")
        if mode not in dict(ClassSession.JOIN_MODES):
            return Response({"error": "mode হতে হবে auto/join/rejoin"}, status=400)
        s.join_mode_override = mode
        s.save(update_fields=["join_mode_override"])
        return Response({"join_mode_override": s.join_mode_override})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def finish(self, request, pk=None):
        """উস্তাদের "ক্লাস শেষ করুন" বাটন — একটি ক্লাস দুই পর্বে হয়।

        জুমের বিনামূল্যের মিটিংয়ের সময়সীমার কারণে একটি ক্লাস দুই পর্বে হয় —
        ১ম লিংকে ১ম পর্ব, ২য় লিংকে ২য় পর্ব। দুই পর্ব মিলেই একটি পূর্ণ ক্লাস।
        তাই এই বাটনটি কোন পর্বে চাপা হলো তার উপর কাজ নির্ভর করে:

        ১ম পর্ব শেষ (রিজয়েন এখনো খোলেনি) —
          • সবার জমে থাকা মিনিট হাজিরায় বসে, হাজিরা পাকা হয়
          • শিক্ষার্থীদের কাছে রিজয়েন লিংক খুলে যায় (join_mode_override),
            ফলে তাঁদের পোর্টালে সাথে সাথেই রিজয়েন বাটন চলে আসে
          • ⚠️ ক্লাসটি "সম্পন্ন" হয় না, আজকের তালিকা থেকেও সরে না — ২য় পর্ব বাকি

        ২য় পর্ব শেষ (রিজয়েন ইতিমধ্যে খোলা) —
          • আবারও মিনিট-হাজিরা গোছানো হয়
          • teacher_finished=True বসে — ক্লাসটি আজকের তালিকাতেই "✅ ক্লাস
            সম্পন্ন" চিহ্ন নিয়ে থেকে যায়। ⚠️ status এখানে "done" করা হয় না;
            পরিচালক/এডমিন দেখে যাচাই করে "সম্পন্ন" চিহ্নিত করলে তবেই তা হয়
            এবং ক্লাসটি আজকের তালিকা থেকে সরে।

        উস্তাদ শেষ না করে লগআউট করলে ক্লাস শেষ হয় না — তথ্য জমা হওয়ার
        অপেক্ষায় থাকে, আর পরিচালক পরে "সম্পন্ন" চিহ্নিত করলেই সব গুছিয়ে যায়।
        """
        s_obj = self.get_object()
        u = request.user
        allowed = {s_obj.teacher_id,
                   s_obj.course.teacher_id if s_obj.course_id else None}
        if (
            u.role not in ("director", "admin")
            and u.id not in allowed
            and not s_obj.students.filter(teacher=u).exists()
        ):
            raise PermissionDenied("কেবল এই ক্লাসের উস্তাদ ক্লাস শেষ করতে পারবেন")
        # রিজয়েন খোলা আছে কিনা — এটাই বলে দেয় আমরা কোন পর্বে আছি
        first_part = s_obj.join_mode_override != "rejoin"
        # উস্তাদের বাটন কখনোই ক্লাসকে "সম্পন্ন" করে না — সেটা কর্তৃপক্ষের কাজ
        _finalize_session(s_obj, by=u, mark_done=False)
        fields = []
        if first_part:
            s_obj.join_mode_override = "rejoin"
            fields.append("join_mode_override")
        elif not s_obj.teacher_finished:
            s_obj.teacher_finished = True
            fields.append("teacher_finished")
        if fields:
            s_obj.save(update_fields=fields)
        data = self.get_serializer(s_obj).data
        data["part_finished"] = 1 if first_part else 2
        return Response(data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def open_rejoin(self, request, pk=None):
        """উস্তাদ নিজের "🔁 রিজয়েন" বাটনে ক্লিক করলে ডাকা হয় — এতে শিক্ষার্থীদের
        কাছেও ২য় (রিজয়েন) লিংক খুলে যায়। উস্তাদ ক্লিক না করা পর্যন্ত শিক্ষার্থী
        শুধু "Teacher is joining, please wait" দেখে, ফলে দুজন কখনো আলাদা
        মিটিংয়ে চলে যান না। এডমিন/পরিচালকও চালাতে পারেন।"""
        s = self.get_object()
        u = request.user
        allowed_teachers = {s.teacher_id, s.course.teacher_id if s.course_id else None}
        if (
            u.role not in ("director", "admin")
            and u.id not in allowed_teachers
            and not s.students.filter(teacher=u).exists()
        ):
            raise PermissionDenied("কেবল এই ক্লাসের উস্তাদ রিজয়েন চালু করতে পারবেন")
        s.join_mode_override = "rejoin"
        s.save(update_fields=["join_mode_override"])
        return Response({"rejoin_active": True})


class AttendanceViewSet(viewsets.ModelViewSet):
    """হাজিরার তালিকা (মাসভিত্তিক রিপোর্ট) — ?month=YYYY-MM দিয়ে ফিল্টার।
    উস্তাদ শুধু নিজের ক্লাসের, শিক্ষার্থী শুধু নিজের হাজিরা দেখতে পাবে;
    পরিচালক সবার দেখতে ও একমাত্র তিনিই এডিট/মুছতে পারবেন। কখনো auto-delete
    হয় না — শুধু পুরনো ClassSession (৬০ দিন) মুছলেও এই রেকর্ড টিকে থাকে।"""
    serializer_class = AttendanceSerializer
    http_method_names = ["get", "patch", "delete", "head", "options"]  # create নয় — join/mark_attendance দিয়েই হয়

    def get_queryset(self):
        u = self.request.user
        qs = Attendance.objects.select_related("user").order_by("-class_date")
        if u.role == "student":
            qs = qs.filter(user=u)
        elif u.role == "teacher":
            # নিজে যে ক্লাস নিয়েছেন, অথবা নিজের শিক্ষার্থীর হাজিরা
            qs = qs.filter(Q(teacher_id=u.id) | Q(user__teacher=u)).distinct()
        elif u.role not in ("director", "admin"):
            return qs.none()
        month = self.request.query_params.get("month")  # "2026-07" ফরম্যাট প্রত্যাশিত
        if month:
            try:
                y, m = int(month[:4]), int(month[5:7])
                qs = qs.filter(class_date__year=y, class_date__month=m)
            except (ValueError, IndexError):
                pass
        return qs

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsDirector()]
        return [IsAuthenticated()]


# ─────────────────────────── অ্যাসাইনমেন্ট ও পরীক্ষা ───────────────────────────
class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course"]

    def get_queryset(self):
        u = self.request.user
        # prefetch → নেস্টেড questions/submissions (ও submissions.student_name) প্রতি
        # অ্যাসাইনমেন্টে আলাদা কোয়েরি না করে prefetch cache ব্যবহার করে (N+1 এড়ায়)
        qs = Assignment.objects.prefetch_related("questions", "submissions__student")
        if u.role == "student":
            return qs.filter(course__students=u)
        if u.role == "teacher":
            # কোর্সের উস্তাদ, অথবা কোর্সে তাঁর নিজের শিক্ষার্থী আছে
            return qs.filter(_q_course_teacher_or_own(u)).distinct()
        # ⚠️ ট্রায়াল অতিথিকে আলাদা করে ধরতেই হবে। নিচের শেষ "return qs"
        # পরিচালক/এডমিনের জন্য — কোনো ছাঁকনি ছাড়া সব। নতুন ভূমিকা যোগ করার
        # পর ট্রায়ালও সেখানে গিয়ে পড়ত, অর্থাৎ একজন সাময়িক অতিথি একাডেমির
        # সবকিছু দেখে ফেলতেন।
        if u.role == "trial":
            return qs.none()  # ট্রায়ালে অ্যাসাইনমেন্ট নেই
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == "student":
            raise PermissionDenied("স্টুডেন্ট অ্যাসাইনমেন্ট বানাতে পারে না")
        serializer.save(teacher=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):  # স্টুডেন্ট জমা — ফরম বা ফাইল
        sub = Submission.objects.create(
            assignment=self.get_object(), student=request.user,
            answers=request.data.get("answers"), file=request.FILES.get("file"),
            note=request.data.get("note", ""))
        return Response(SubmissionSerializer(sub).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsTeacherOrAdminLevel])
    def grade(self, request, pk=None):  # মার্ক দিলেই স্টুডেন্ট পোর্টালে
        sub = Submission.objects.get(pk=request.data["submission_id"], assignment=self.get_object())
        sub.mark = min(int(request.data["mark"]), self.get_object().total_marks)
        sub.marked_by = request.user
        sub.save()
        notify(f"📝 \"{sub.assignment.title}\" অ্যাসাইনমেন্টে আপনার মার্ক: {sub.mark}/{sub.assignment.total_marks}",
               [sub.student])
        return Response(SubmissionSerializer(sub).data)


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course"]

    def get_queryset(self):
        u = self.request.user
        # prefetch → নেস্টেড questions/submissions/results প্রতি পরীক্ষায় আলাদা কোয়েরি
        # না করে prefetch cache ব্যবহার করে (N+1 এড়ায়)
        qs = Exam.objects.prefetch_related("questions", "results", "submissions__student")
        if u.role == "student":
            return qs.filter(course__students=u)
        if u.role == "teacher":
            # কোর্সের উস্তাদ, অথবা কোর্সে তাঁর নিজের শিক্ষার্থী আছে
            return qs.filter(_q_course_teacher_or_own(u)).distinct()
        # ⚠️ ট্রায়াল অতিথিকে আলাদা করে ধরতেই হবে। নিচের শেষ "return qs"
        # পরিচালক/এডমিনের জন্য — কোনো ছাঁকনি ছাড়া সব। নতুন ভূমিকা যোগ করার
        # পর ট্রায়ালও সেখানে গিয়ে পড়ত, অর্থাৎ একজন সাময়িক অতিথি একাডেমির
        # সবকিছু দেখে ফেলতেন।
        if u.role == "trial":
            return qs.none()  # ট্রায়ালে পরীক্ষা নেই
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        sub = Submission.objects.create(
            exam=self.get_object(), student=request.user,
            answers=request.data.get("answers"), file=request.FILES.get("file"),
            note=request.data.get("note", ""))
        return Response(SubmissionSerializer(sub).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsTeacherOrAdminLevel])
    def grade(self, request, pk=None):  # জমা মূল্যায়ন → ফলাফলেও অটো
        exam = self.get_object()
        sub = Submission.objects.get(pk=request.data["submission_id"], exam=exam)
        sub.mark = min(int(request.data["mark"]), exam.total_marks)
        sub.marked_by = request.user
        sub.save()
        ExamResult.objects.update_or_create(exam=exam, student=sub.student,
                                            defaults={"mark": sub.mark})
        notify(f"🏅 \"{exam.title}\" পরীক্ষায় আপনার ফলাফল: {sub.mark}/{exam.total_marks}", [sub.student])
        return Response(SubmissionSerializer(sub).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTeacherOrAdminLevel])
    def direct_mark(self, request, pk=None):  # লাইভ টেস্টের সরাসরি মার্ক এন্ট্রি
        exam = self.get_object()
        r, _ = ExamResult.objects.update_or_create(
            exam=exam, student_id=request.data["student_id"],
            defaults={"mark": min(int(request.data["mark"]), exam.total_marks)})
        return Response({"student": r.student_id, "mark": r.mark})


# ─────────────────────────── আর্থিক ───────────────────────────
class FeePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = FeePaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        # select_related("student") → student_name প্রতি পেমেন্টে আলাদা কোয়েরি এড়ায়
        qs = FeePayment.objects.select_related("student")
        if u.role == "student":
            return qs.filter(student=u)
        if u.role in ("director", "admin"):
            return qs
        return FeePayment.objects.none()

    def get_permissions(self):
        # ভুল/ডুপ্লিকেট পেমেন্ট মুছা কেবল পরিচালকের এখতিয়ার — আর্থিক রেকর্ড
        if self.action == "destroy":
            return [IsDirector()]
        # 🔒 super() ব্যবহার করতেই হবে — নইলে প্রতিটি @action-এ ঘোষিত
        # permission_classes চাপা পড়ে যায়। আগে সরাসরি [IsAuthenticated()]
        # ফেরত দেওয়া হতো, ফলে record_payment / waive_due / verify /
        # generate_dues — টাকার সাথে জড়িত চারটি কাজই যেকোনো লগইন করা
        # ব্যবহারকারীর জন্য খোলা ছিল। শিক্ষার্থী নিজেই নিজের ফি "পরিশোধিত"
        # করে ফেলতে বা বকেয়া মওকুফ করে দিতে পারত।
        # DRF অ্যাকশনের initkwargs থেকে self.permission_classes বসিয়ে দেয়,
        # তাই super() ঠিক অনুমতিটাই ফেরত দেয়।
        return super().get_permissions()

    def perform_create(self, serializer):  # স্টুডেন্টের "এখনই পেমেন্ট" → pending
        pay = serializer.save(student=self.request.user, status="pending")
        DueMonth.objects.filter(user=pay.student, month_label=pay.month_label).delete()
        notify(f"{pay.student.name_bn} — {pay.month_label} মাসের ফি পরিশোধ করেছে, "
               f"পরিচালকের ভেরিফাই বাকি।", admins())

    def perform_destroy(self, instance):
        # ভুলবশত/ডুপ্লিকেট যোগ হওয়া পেমেন্ট রেকর্ড মোছার পর, ওই মাসের আর কোনো
        # ভেরিফাইড পেমেন্ট না থাকলে বকেয়া (DueMonth) আবার সঠিকভাবে ফিরিয়ে আনা হয়
        # (একাধিক পেমেন্টের একটা ডুপ্লিকেট হলে বাকিটা থেকেই যায়, তখন বকেয়া ফেরত আসে না)
        student, month_label = instance.student, instance.month_label
        instance.delete()
        still_paid = FeePayment.objects.filter(
            student=student, month_label=month_label, status="verified",
        ).exists()
        if not still_paid:
            # get_or_create — মওকুফ করা সারি থাকলে সেটাই থাকে, মওকুফ অবস্থা
            # নষ্ট হয় না
            DueMonth.objects.get_or_create(user=student, month_label=month_label)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def dues(self, request):  # বকেয়া মাসের তালিকা — স্টুডেন্ট নিজের, পরিচালক সবার
        u = request.user
        if u.role == "student":
            qs = DueMonth.objects.filter(user=u)
        elif u.role in ("director", "admin"):
            qs = DueMonth.objects.all().select_related("user")
        else:
            qs = DueMonth.objects.none()
        # মওকুফ করা মাস আর "বকেয়া" নয় — তাই বকেয়ার তালিকা থেকে বাদ।
        # ?include_waived=1 দিলে সবগুলোই আসে (কে কোন মাস মওকুফ পেয়েছেন তা
        # দেখাতে লাগে)।
        if not self.request.query_params.get("include_waived"):
            qs = qs.filter(waived=False)
        return Response(DueMonthSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminLevel])
    def record_payment(self, request):
        # পরিচালক/এডমিন সরাসরি যেকোনো স্টুডেন্টের যেকোনো মাসের (আগের/পরের) পেমেন্ট
        # সরাসরি "পরিশোধিত" হিসেবে সেভ করতে পারেন — স্টুডেন্টের নিজে জমা দেওয়া ও
        # ভেরিফাই করার অপেক্ষা ছাড়াই
        student_id = request.data.get("student_id")
        month_label = request.data.get("month_label")
        amount = request.data.get("amount")
        method = request.data.get("method", "cash")  # FeePayment.METHODS কোড ("bkash"/"nagad"/"bank"/"cash"/"other")
        if not student_id or not month_label or not amount:
            return Response({"error": "student_id, month_label, amount আবশ্যক"}, status=400)
        try:
            student = User.objects.get(pk=student_id, role="student")
        except User.DoesNotExist:
            return Response({"error": "স্টুডেন্ট পাওয়া যায়নি"}, status=404)
        pay = FeePayment.objects.create(
            student=student, amount=amount, month_label=month_label,
            method=method, status="verified",
        )
        DueMonth.objects.filter(user=student, month_label=month_label).delete()
        return Response(FeePaymentSerializer(pay).data, status=201)

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def waive_due(self, request):  # পরিচালক কোনো নির্দিষ্ট মাসের বকেয়া মওকুফ করে সরিয়ে দিতে পারেন
        user_id = request.data.get("user_id")
        month_label = request.data.get("month_label")
        if not user_id or not month_label:
            return Response({"error": "user_id ও month_label আবশ্যক"}, status=400)
        # ⚠️ আগে .delete() করা হতো — রেকর্ডটাই মুছে যেত। ফলে পরে বোঝার কোনো
        # উপায় থাকত না কেন বকেয়া নেই, আর পর্দায় "পরিশোধিত ✔" দেখাত, যদিও
        # টাকা আসেনি। এখন চিহ্নিত করে রাখা হয় — "মওকুফ" ও "পরিশোধিত"
        # আলাদা করে দেখানো যায়, আর মাসিক কাজটিও (get_or_create) মওকুফ করা
        # মাসকে নতুন করে বকেয়া বানায় না।
        # 💰 মওকুফ কোনো পেমেন্ট নয় — FeePayment তৈরি হয় না, তাই আয়ের
        # হিসাবেও এক পয়সা যোগ হয় না।
        row, _ = DueMonth.objects.get_or_create(
            user_id=user_id, month_label=month_label)
        row.waived = True
        row.waived_reason = (request.data.get("reason") or "").strip()[:120]
        row.waived_at = timezone.now()
        row.save(update_fields=["waived", "waived_reason", "waived_at"])
        return Response(DueMonthSerializer(row).data)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminLevel])
    def generate_dues(self, request):
        """চলতি মাসের বকেয়া এখনই তৈরি/নিশ্চিত করা (idempotent) — cron বন্ধ থাকলে
        পরিচালক নিজে এক ক্লিকে চালাতে পারবেন। "স্টুডেন্ট পেমেন্ট" পেজ থেকে
        role="student" পাঠালে কেবল স্টুডেন্টদের বকেয়া তৈরি হয় (টিচারদের বাদ)।"""
        from .tasks import generate_monthly_dues
        role = request.data.get("role")
        roles = [role] if role in ("student", "teacher") else None
        created = generate_monthly_dues(roles=roles)
        return Response({"created": created})

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def verify(self, request, pk=None):  # ভেরিফাই — কেবল পরিচালক
        pay = self.get_object()
        pay.status = "verified"
        pay.verified_by = request.user
        pay.save()
        notify(f"আপনার {pay.month_label} মাসের ফি ভেরিফাই হয়েছে, জাযাকুমুল্লাহু খাইরান।", [pay.student])
        return Response({"status": "verified"})


class TeacherPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherPaymentSerializer

    def get_queryset(self):
        u = self.request.user
        # select_related("teacher") → teacher_name প্রতি পেমেন্টে আলাদা কোয়েরি এড়ায়
        qs = TeacherPayment.objects.select_related("teacher")
        if u.role == "teacher":
            return qs.filter(teacher=u)
        if u.role == "director":
            return qs
        return TeacherPayment.objects.none()

    def get_permissions(self):
        return [IsDirector()] if self.action in ("create", "update", "destroy") else [IsAuthenticated()]

    def perform_create(self, serializer):
        # আংশিক পেমেন্টও রেকর্ড করা যায় — সেই মাসের সব পেমেন্ট মিলিয়ে পূর্ণ
        # মাসিক বেতনের সমান/বেশি না হওয়া পর্যন্ত বকেয়া বাদ যাবে না, যাতে
        # "কত পেয়েছেন, কত বাকি" সঠিকভাবে দেখানো যায়
        pay = serializer.save()
        total_paid = TeacherPayment.objects.filter(
            teacher=pay.teacher, month_label=pay.month_label,
        ).aggregate(total=Sum("amount"))["total"] or 0
        if total_paid >= (pay.teacher.monthly_salary or 0):
            DueMonth.objects.filter(user=pay.teacher, month_label=pay.month_label).delete()

    def perform_destroy(self, instance):
        # ভুলবশত/ডুপ্লিকেট যোগ হওয়া বেতন-পেমেন্ট মোছার পর, ওই মাসে মোট পরিশোধ
        # আর পূর্ণ বেতনের সমান না হলে বকেয়া (DueMonth) আবার ফিরিয়ে আনা হয় —
        # FeePaymentViewSet.perform_destroy-এর সাথে সামঞ্জস্যপূর্ণ
        teacher, month_label = instance.teacher, instance.month_label
        instance.delete()
        total_paid = TeacherPayment.objects.filter(
            teacher=teacher, month_label=month_label,
        ).aggregate(total=Sum("amount"))["total"] or 0
        if total_paid < (teacher.monthly_salary or 0):
            DueMonth.objects.get_or_create(user=teacher, month_label=month_label)


class SentReceiptViewSet(viewsets.ModelViewSet):
    serializer_class = SentReceiptSerializer

    def get_queryset(self):
        u = self.request.user
        # select_related("sent_by") → sent_by_name প্রতি রিসিটে আলাদা কোয়েরি এড়ায়
        qs = SentReceipt.objects.select_related("sent_by")
        if u.role in ("director", "admin"):
            return qs
        return qs.filter(to_user=u)  # নিজের ভাউচার/রিসিট

    def get_permissions(self):
        return [IsAdminLevel()] if self.action == "create" else [IsAuthenticated()]

    def perform_create(self, serializer):
        r = serializer.save(sent_by=self.request.user)
        notify(f"🧾 আপনার পোর্টালে একটি \"{r.kind}\" পাঠানো হয়েছে — ভাউচার/রিসিট মেনুতে দেখুন।",
               [r.to_user])


# ─────────────────────────── ভর্তি, ছুটি, মূল্যায়ন ───────────────────────────
class _PublicFormThrottle(AnonRateThrottle):
    rate = "5/min"  # একই ভিজিটর মিনিটে সর্বোচ্চ ৫টি ফরম — spam ঠেকাতে


def _convert_trial_to_student(u, course=None, fee=None):
    """ট্রায়াল অতিথিকে নিয়মিত শিক্ষার্থী বানানো — একটাই জায়গা, দুই পথেই ডাকা।

    দুই পথ: পরিচালকের "🎓 ভর্তি করুন" (ট্রায়াল পর্দা), আর ভর্তি আবেদন
    গ্রহণ করা (ভর্তি আবেদন পর্দা)। দুটোই এখানে এসে মেলে, তাই একই ব্যক্তির
    দুটো অ্যাকাউন্ট কখনো তৈরি হয় না।

    ⚠️ নতুন অ্যাকাউন্ট বানানো হয় না — একই অ্যাকাউন্টেই ভূমিকা বদলায়। ফলে
    ট্রায়ালের হাজিরা ও রিপোর্ট তাঁর সাথেই থাকে, আর পরিবারকে নতুন
    আইডি-পাসওয়ার্ড পাঠাতেও হয় না।
    ⚠️ trial_until/trial_course মোছা হয় না — কবে কোন কোর্সে ট্রায়াল
    করেছিলেন সেই ইতিহাসটা থেকে যায়।
    """
    course = course or u.trial_course
    try:
        fee = int(fee) if fee is not None else DEFAULT_STUDENT_FEE
    except (TypeError, ValueError):
        fee = DEFAULT_STUDENT_FEE
    u.role = "student"
    u.monthly_fee = max(0, fee)
    u.save(update_fields=["role", "monthly_fee"])
    if course:
        course.students.add(u)
    from .student_id import assign_student_id
    if assign_student_id(u, User):
        u.save(update_fields=["student_id"])
    return u


class ReadOwnWriteTeacher(BasePermission):
    """পড়া সবার জন্য খোলা (get_queryset যতটুকু দেয় ততটুকুই), লেখা কেবল
    উস্তাদ/এডমিন/পরিচালকের — শিক্ষার্থী বা ট্রায়াল অতিথি নিজের অগ্রগতি
    নিজে বদলাতে পারবেন না।"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in ("director", "admin", "teacher")


class LessonProgressViewSet(viewsets.ModelViewSet):
    """কে কোন দারসের কোথায় আছে — উস্তাদ চিহ্নিত করেন, সবাই দেখেন।"""
    serializer_class = LessonProgressSerializer
    permission_classes = [ReadOwnWriteTeacher]
    filterset_fields = ["student", "lesson", "status"]

    def get_queryset(self):
        u = self.request.user
        qs = LessonProgress.objects.select_related(
            "student", "lesson", "lesson__course")
        if u.role in ("director", "admin"):
            return qs
        if u.role == "teacher":
            # ⚠️ কোর্স নয়, *শিক্ষার্থী* ধরেই ছাঁকা হয় — একই কোর্সে একাধিক
            # উস্তাদ থাকতে পারেন, তখন কোর্স ধরে ছাঁকলে একজনের শিক্ষার্থীর
            # অগ্রগতি আরেকজন দেখে ফেলতেন। নিয়মটা কোর্সের শিক্ষার্থী-তালিকার
            # সাথে হুবহু এক: নিজের শিক্ষার্থী, আর উস্তাদ বসানো নেই এমন
            # শিক্ষার্থী কেবল কোর্সের উস্তাদের জন্য।
            return qs.filter(
                Q(student__teacher=u)
                | (Q(student__teacher__isnull=True)
                   & Q(lesson__course__teacher=u))
            ).distinct()
        # ⚠️ শিক্ষার্থী ও ট্রায়াল অতিথি কেবল নিজেরটাই — অন্য কারও নয়
        return qs.filter(student=u)

    @staticmethod
    def _may_mark(u, lesson, student):
        """এই উস্তাদ কি এই দারসে এই শিক্ষার্থীর অগ্রগতি লিখতে পারেন?

        ⚠️ দুটোই লাগে — দারসটিও তাঁর, শিক্ষার্থীটিও তাঁর। আগে "অথবা" ছিল,
        ফলে নিজের কোর্সের দারসে অন্য উস্তাদের শিক্ষার্থীকে, কিংবা নিজের
        শিক্ষার্থীকে অন্য উস্তাদের দারসে চিহ্নিত করে ফেলা যেত।
        """
        if u.role in ("director", "admin"):
            return True
        if u.role != "teacher":
            return False
        own = Q(teacher=u)
        if lesson.course.teacher_id == u.id:
            own = own | Q(teacher__isnull=True)
        if lesson.course.students.filter(own).filter(pk=student.pk).exists():
            return True
        # ট্রায়াল অতিথি কোর্সের students-এ থাকেন না (ইচ্ছা করেই) — তাঁর
        # সংযোগ trial_course দিয়ে, তাই আলাদা করে দেখি
        return (student.role == "trial"
                and student.trial_course_id == lesson.course_id
                and (student.teacher_id == u.id
                     or (student.teacher_id is None
                         and lesson.course.teacher_id == u.id)))

    def perform_update(self, serializer):
        # সরাসরি PATCH করেও যেন অন্যের রেকর্ড বদলানো না যায়
        row = serializer.instance
        if not self._may_mark(self.request.user, row.lesson, row.student):
            raise PermissionDenied("এটি আপনার দারস বা শিক্ষার্থী নয়")
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if not self._may_mark(self.request.user, instance.lesson,
                              instance.student):
            raise PermissionDenied("এটি আপনার দারস বা শিক্ষার্থী নয়")
        instance.delete()

    @action(detail=False, methods=["post"])
    def mark(self, request):
        """একটি দারসে একজন শিক্ষার্থীর অবস্থা বসানো (থাকলে হালনাগাদ)।

        একই দিনে কয়েকবার সংরক্ষণ করলেও "কয় দিন পড়ানো হয়েছে" একবারই
        বাড়ে — তারিখ দেখে গোনা হয়, সংরক্ষণের সংখ্যা দিয়ে নয়।
        """
        sid = request.data.get("student")
        lid = request.data.get("lesson")
        lesson = Lesson.objects.filter(pk=lid).first()
        student = User.objects.filter(pk=sid).first()
        if not lesson or not student:
            return Response({"error": "শিক্ষার্থী বা দারসটি পাওয়া যায়নি"},
                            status=400)
        u = request.user
        if not self._may_mark(u, lesson, student):
            raise PermissionDenied("এটি আপনার দারস বা শিক্ষার্থী নয়")

        status_in = request.data.get("status")
        valid = dict(LessonProgress.Status.choices)
        if status_in and status_in not in valid:
            return Response({"error": "অবস্থাটি চেনা গেল না"}, status=400)

        row, made = LessonProgress.objects.get_or_create(
            student=student, lesson=lesson)
        today = timezone.localtime().date()
        if row.last_taught != today:
            row.times_taught += 1
            row.last_taught = today
        if status_in:
            row.status = status_in
        if "last_step" in request.data:
            row.last_step = max(0, int(request.data.get("last_step") or 0))
        if "note" in request.data:
            row.note = str(request.data.get("note") or "")[:2000]
        row.updated_by = u
        row.save()
        return Response(LessonProgressSerializer(row).data,
                        status=201 if made else 200)


class LessonViewSet(viewsets.ModelViewSet):
    """দারস স্ক্রিপ্ট — পরিচালক লেখেন, উস্তাদ পড়ান।

    দুটি আলাদা পথ, আর এটাই নিরাপত্তার ভিত্তি —
      GET /lessons/{id}/        → উস্তাদের জন্য, পুরো স্ক্রিপ্টসহ
      GET /lessons/{id}/stage/  → উপস্থাপনার জন্য, কেবল স্লাইড
    দ্বিতীয়টি StageSerializer ব্যবহার করে, যেখানে উস্তাদের ঘরগুলো নেই-ই।
    """
    serializer_class = LessonSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["course", "status", "kind"]

    def get_queryset(self):
        u = self.request.user
        qs = Lesson.objects.select_related("course").prefetch_related(
            "steps", "steps__slide")
        if u.role in ("director", "admin"):
            return qs
        if u.role == "teacher":
            # নিজের কোর্স, অথবা কোর্সে নিজের শিক্ষার্থী আছে
            return qs.filter(_q_course_teacher_or_own(u)).distinct()
        # ⚠️ শিক্ষার্থী ও ট্রায়াল অতিথি এখনো কিছুই পান না। ক্লাসের পর নিজে
        # দেখার ব্যবস্থাটি ধাপ ৫-এ ইচ্ছা করে খোলা হবে — তখন কেবল
        # প্রকাশিত দারসের stage-টুকু, স্ক্রিপ্ট নয়।
        return qs.none()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # একটিমাত্র দারস খুললেই কেবল ধাপগুলো পাঠাই — তালিকায় নয়
        ctx["with_steps"] = self.action in ("retrieve", "create", "update",
                                            "partial_update")
        return ctx

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def seed_sample(self, request):
        """নমুনা দারস কোনো কোর্সে বসিয়ে দেওয়া — পরিচালকের বাটন।

        একই কোর্সে একই শিরোনামের দারস আগে থেকে থাকলে নতুন করে বানানো হয় না,
        তাই বারবার চাপা নিরাপদ।
        """
        from .sample_lessons import SAMPLES, create_sample
        key = str(request.data.get("which") or "").strip()
        if key not in SAMPLES:
            return Response(
                {"error": "কোন নমুনা তা বেছে দিন: " + ", ".join(SAMPLES)},
                status=400)
        course = Course.objects.filter(pk=request.data.get("course")).first()
        if not course:
            return Response({"error": "কোর্সটি পাওয়া যায়নি"}, status=400)
        lesson = create_sample(Lesson, LessonStep, StepSlide, course, key)
        ctx = self.get_serializer_context()
        ctx["with_steps"] = True
        return Response(LessonSerializer(lesson, context=ctx).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def duplicate(self, request, pk=None):
        """দারসটির হুবহু নকল — ধাপ ও স্লাইডসহ।

        একই বিষয়ের আলাদা বয়সের সংস্করণ বানানোর সহজ পথ: নকল করে বয়সসীমা
        বদলে নিয়ে ভাষাটা ওই বয়সের মতো করে সাজিয়ে নিলেই হলো। নকলটি সবসময়
        খসড়া হিসেবে শুরু হয়, যাতে আধা-সম্পাদিত অবস্থায় কারও সামনে না পড়ে।
        """
        src = self.get_object()
        last = Lesson.objects.filter(
            course=src.course).order_by("-order").first()
        new = Lesson.objects.create(
            course=src.course,
            title=request.data.get("title") or (src.title + " (নকল)"),
            title_ar=src.title_ar, kind=src.kind,
            age_from=request.data.get("age_from") or src.age_from,
            age_to=request.data.get("age_to") or src.age_to,
            duration_min=src.duration_min, objectives=src.objectives,
            status=Lesson.Status.DRAFT,
            order=(last.order + 1) if last else 0,
        )
        for st in src.steps.all().order_by("order", "id"):
            copy = LessonStep.objects.create(
                lesson=new, order=st.order, section=st.section,
                teacher_says=st.teacher_says, teacher_does=st.teacher_does,
                student_does=st.student_does, expected=st.expected,
                correction=st.correction, note=st.note, seconds=st.seconds,
                topic=st.topic, is_active=st.is_active,
            )
            sl = getattr(st, "slide", None)
            if sl:
                StepSlide.objects.create(
                    step=copy, kind=sl.kind, heading=sl.heading,
                    arabic=sl.arabic, arabic_locked=sl.arabic_locked,
                    translit=sl.translit, text=sl.text,
                    image=sl.image, audio=sl.audio,
                )
        ctx = self.get_serializer_context()
        ctx["with_steps"] = True
        return Response(LessonSerializer(new, context=ctx).data, status=201)

    @action(detail=True, permission_classes=[IsAuthenticated])
    def stage(self, request, pk=None):
        """উপস্থাপনা উইন্ডোর জন্য — কেবল শিক্ষার্থী যা দেখবেন।

        ⚠️ ইচ্ছা করেই আলাদা সিরিয়ালাইজার। ভবিষ্যতে কেউ ভুল করে উস্তাদের
        কোনো ঘর যোগ করে ফেললেও যেন এই পথ দিয়ে না যায়, সেজন্য এখানে
        LessonSerializer ছোঁয়াই হয় না।
        """
        obj = self.get_object()
        return Response(StageSerializer(obj).data)


class LessonStepViewSet(viewsets.ModelViewSet):
    """দারসের ধাপ — লেখা, বদলানো, ক্রম সাজানো। কেবল পরিচালক লিখতে পারেন।"""
    serializer_class = LessonStepSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["lesson"]

    def get_queryset(self):
        u = self.request.user
        qs = LessonStep.objects.select_related("lesson", "slide")
        if u.role in ("director", "admin"):
            return qs
        if u.role == "teacher":
            return qs.filter(
                _q_course_teacher_or_own_lesson(u)).distinct()
        return qs.none()

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def reorder(self, request):
        """যে ক্রমে আইডি পাঠানো হয়, সেই ক্রমেই বসে।"""
        ids = request.data.get("ids") or []
        rows = {x.id: x for x in LessonStep.objects.filter(id__in=ids)}
        changed = []
        for i, sid in enumerate(ids):
            r = rows.get(sid)
            if r and r.order != i:
                r.order = i
                changed.append(r)
        if changed:
            LessonStep.objects.bulk_update(changed, ["order"])
        return Response({"ok": True})


# একাডেমির চারটি মূল মাপকাঠি — প্রথমবার এগুলোই বসে (মাইগ্রেশন 0033), আর
# কখনো হারিয়ে গেলে "ফিরিয়ে আনুন" দিয়ে এখান থেকেই ফেরত আসে।
DEFAULT_TRIAL_SCORES = [
    ("letters", "হরফ চেনা", "Recognising letters"),
    ("makhraj", "মাখরাজ ও উচ্চারণ", "Makhraj & pronunciation"),
    ("fluency", "তিলাওয়াতের সাবলীলতা", "Fluency"),
    ("attentiveness", "মনোযোগ", "Attentiveness"),
]


class TrialScoreItemViewSet(viewsets.ModelViewSet):
    """মূল্যায়নের মাপকাঠি — পরিচালক সাজান, বাকিরা কেবল দেখেন।

    উস্তাদের ফরম, পরিবারের রিপোর্ট ও ছাপা কাগজ — তিন জায়গাতেই এই একই
    তালিকা ব্যবহার হয়, তাই সবার পড়ার অনুমতি লাগে।
    """
    serializer_class = TrialScoreItemSerializer
    permission_classes = [ReadAllWriteDirector]

    def get_queryset(self):
        return TrialScoreItem.objects.all()

    def _make_key(self, label_en, label_bn):
        """স্থায়ী key তৈরি — ইংরেজি নাম থেকে, না থাকলে ক্রমিক নম্বরে।"""
        import re
        base = re.sub(r"[^a-z0-9]+", "_",
                      str(label_en or "").strip().lower()).strip("_")[:32]
        if not base:
            base = "point"
        key, n = base, 1
        while TrialScoreItem.objects.filter(key=key).exists():
            n += 1
            key = f"{base}_{n}"[:40]
        return key

    @staticmethod
    def _fill_en(data):
        """ইংরেজি নাম না দিলে বাংলাটাই বসে — রিপোর্টে ঘর খালি থাকা চলবে না।"""
        bn = str(data.get("label_bn") or "").strip()
        en = str(data.get("label_en") or "").strip()
        return en or bn

    def perform_create(self, serializer):
        d = self.request.data
        last = TrialScoreItem.objects.order_by("-order").first()
        serializer.save(
            key=self._make_key(d.get("label_en"), d.get("label_bn")),
            label_en=self._fill_en(d),
            order=(last.order + 1) if last else 0,
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        if not (obj.label_en or "").strip() and obj.label_bn:
            obj.label_en = obj.label_bn
            obj.save(update_fields=["label_en"])

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def restore_defaults(self, request):
        """একাডেমির চারটি মূল মাপকাঠি ফিরিয়ে আনা।

        যেগুলো তালিকায় নেই কেবল সেগুলোই যোগ হয় — পরিচালকের নিজের যোগ করা
        মাপকাঠি বা বদলানো নাম কিছুই ছোঁয়া হয় না। আগের key-ই ব্যবহার হয়, তাই
        পুরনো রিপোর্টে দেওয়া নম্বরগুলোও সাথে সাথে আবার দেখা যায়।
        """
        last = TrialScoreItem.objects.order_by("-order").first()
        order = (last.order + 1) if last else 0
        added = 0
        for key, bn, en in DEFAULT_TRIAL_SCORES:
            if not TrialScoreItem.objects.filter(key=key).exists():
                TrialScoreItem.objects.create(
                    key=key, label_bn=bn, label_en=en, order=order)
                order += 1
                added += 1
        rows = TrialScoreItem.objects.all()
        return Response({"added": added,
                         "items": self.get_serializer(rows, many=True).data})

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def reorder(self, request):
        """যে ক্রমে আইডি পাঠানো হয়, সেই ক্রমেই বসে।"""
        ids = request.data.get("ids") or []
        rows = {x.id: x for x in TrialScoreItem.objects.filter(id__in=ids)}
        changed = []
        for i, sid in enumerate(ids):
            r = rows.get(sid)
            if r and r.order != i:
                r.order = i
                changed.append(r)
        if changed:
            TrialScoreItem.objects.bulk_update(changed, ["order"])
        return Response({"ok": True})


class TrialReportViewSet(viewsets.ModelViewSet):
    """ট্রায়াল মূল্যায়ন — উস্তাদ লেখেন, কর্তৃপক্ষ যাচাই করে পাঠান।

    কে কী পারেন —
      উস্তাদ        : নিজের ট্রায়াল অতিথির রিপোর্ট লেখা ও হালনাগাদ (যাচাইয়ের আগ পর্যন্ত)
      পরিচালক/এডমিন : সব রিপোর্ট দেখা, সম্পাদনা, যাচাই ও পাঠানো
      অতিথি         : কেবল নিজেরটি, আর কেবল পাঠানোর পর
      শিক্ষার্থী     : কিছুই নয়
    """
    serializer_class = TrialReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = TrialReport.objects.select_related(
            "student", "student__trial_course", "student__teacher",
            "created_by", "reviewed_by", "recommended_course")
        if u.role in ("director", "admin"):
            return qs
        if u.role == "teacher":
            # নিজের অতিথি, অথবা নিজে যে রিপোর্টটি লিখেছেন
            return qs.filter(Q(student__teacher=u) | Q(created_by=u)).distinct()
        if u.role == "trial":
            # ⚠️ পাঠানোর আগে অতিথি নিজের রিপোর্টও দেখতে পাবেন না — খসড়া
            # অবস্থায় কারও চোখে পড়া চলবে না
            return qs.filter(student=u, sent_at__isnull=False)
        return qs.none()

    def _may_write(self, student):
        u = self.request.user
        if u.role in ("director", "admin"):
            return True
        return u.role == "teacher" and student.teacher_id == u.id

    def perform_create(self, serializer):
        student = serializer.validated_data.get("student")
        if not student or student.role != "trial":
            raise PermissionDenied("রিপোর্ট কেবল ট্রায়াল অতিথির জন্য")
        if not self._may_write(student):
            raise PermissionDenied("এই অতিথির উস্তাদ আপনি নন")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        obj = serializer.instance
        u = self.request.user
        if not self._may_write(obj.student):
            raise PermissionDenied("এই রিপোর্ট সম্পাদনার অনুমতি নেই")
        # যাচাই হয়ে যাওয়ার পর উস্তাদ আর বদলাতে পারবেন না — কর্তৃপক্ষ পারবেন
        if obj.reviewed_at and u.role not in ("director", "admin"):
            raise PermissionDenied(
                "রিপোর্টটি যাচাই হয়ে গেছে — বদলাতে হলে পরিচালককে বলুন")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role != "director":
            raise PermissionDenied("রিপোর্ট মোছা কেবল পরিচালকের এখতিয়ার")
        instance.delete()

    @action(detail=True, methods=["post"], permission_classes=[IsAdminLevel])
    def review(self, request, pk=None):
        """যাচাই সম্পন্ন — এরপর অতিথির কাছে পাঠানো যাবে।"""
        r = self.get_object()
        r.reviewed_by = request.user
        r.reviewed_at = timezone.now()
        r.save(update_fields=["reviewed_by", "reviewed_at"])
        return Response(self.get_serializer(r).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminLevel])
    def send(self, request, pk=None):
        """পরিবারের কাছে পাঠানো হলো — এরপর অতিথি নিজের পোর্টালে দেখতে পান।"""
        r = self.get_object()
        if not r.reviewed_at:
            return Response(
                {"error": "আগে যাচাই করুন — যাচাই ছাড়া রিপোর্ট পাঠানো যাবে না"},
                status=400)
        if not r.sent_at:
            r.sent_at = timezone.now()
            r.save(update_fields=["sent_at"])
        return Response(self.get_serializer(r).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminLevel])
    def offer(self, request, pk=None):
        """ভর্তির প্রস্তাব পাঠানো — এরপর অতিথি নিজের পোর্টালে দেখতে পান।

        যাচাই হওয়ার আগে প্রস্তাব যায় না — রিপোর্ট আর প্রস্তাব একসাথেই
        পরিবারের কাছে পৌঁছায়।
        """
        r = self.get_object()
        if not r.reviewed_at:
            return Response(
                {"error": "আগে মূল্যায়ন যাচাই করুন — যাচাই ছাড়া প্রস্তাব যাবে না"},
                status=400)
        if not r.recommended_course_id:
            return Response({"error": "প্রস্তাবে কোন কোর্স তা বেছে দিন"}, status=400)
        if not r.offered_at:
            r.offered_at = timezone.now()
            r.save(update_fields=["offered_at"])
        return Response(self.get_serializer(r).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        """অতিথি "Accept & apply" চাপলেন — ভর্তির আবেদন তৈরি হয়ে কর্তৃপক্ষের
        কাছে চলে যায়, তথ্য আর নতুন করে লিখতে হয় না।

        ⚠️ এখানে কাউকে ভর্তি করা হয় না — কেবল আবেদন তৈরি হয়। ভর্তির
        সিদ্ধান্ত আগের মতোই কর্তৃপক্ষের।
        """
        r = self.get_object()
        u = request.user
        if u.role != "trial" or r.student_id != u.id:
            raise PermissionDenied("এটি আপনার প্রস্তাব নয়")
        if not r.offered_at:
            return Response({"error": "এখনো কোনো প্রস্তাব পাঠানো হয়নি"}, status=400)
        if r.accepted_at:
            return Response(self.get_serializer(r).data)  # দুবার চাপলেও একটাই আবেদন
        g = r.student
        Admission.objects.create(
            # ⚠️ আবেদনটি অতিথির সাথে বেঁধে দেওয়া হয় — নইলে পরিচালক "ভর্তি
            # আবেদন" পর্দা থেকে গ্রহণ করলে একই মানুষের দ্বিতীয় একটি নতুন
            # অ্যাকাউন্ট তৈরি হয়ে যেত
            created_student=g,
            kind="admission", name=g.name_bn, guardian=g.guardian or "",
            country=g.country or "", contact=g.phone or "", email=g.email or "",
            course_name=(r.recommended_course.name if r.recommended_course_id else ""),
            preferred_time=r.offer_schedule or "",
            message=("ট্রায়াল থেকে — অতিথি প্রস্তাব গ্রহণ করেছেন। "
                     f"আইডি: {g.username}"
                     + (f" · স্তর: {r.recommended_level}" if r.recommended_level else "")),
        )
        r.accepted_at = timezone.now()
        r.save(update_fields=["accepted_at"])
        notify(f"🌱 ট্রায়াল থেকে ভর্তির আবেদন এসেছে: {g.name_bn}",
               User.objects.filter(role__in=["director", "admin"]))
        return Response(self.get_serializer(r).data)


class TrialViewSet(viewsets.ModelViewSet):
    """ট্রায়াল (সাময়িক অতিথি) অ্যাকাউন্ট — তৈরি, তালিকা, মেয়াদ/কোর্স বদল।

    কেবল পরিচালক ও এডমিন। মুছে ফেলার সুযোগ ইচ্ছা করেই রাখা হয়নি — মেয়াদ
    ফুরালে অ্যাকাউন্টটি নিজে থেকেই সংরক্ষণে চলে যায়, কিন্তু তথ্য থাকে
    (কেউ ছয় মাস পরে ফিরে এলে তাঁর পুরনো তথ্য যেন হাতে থাকে)।
    """
    serializer_class = TrialSerializer
    permission_classes = [IsAdminLevel]

    def get_queryset(self):
        return (User.objects.filter(role="trial")
                .select_related("trial_course", "teacher", "trial_admission")
                .order_by("-id"))

    def create(self, request, *args, **kwargs):
        from datetime import timedelta
        from .utils import make_password_str, make_trial_username
        d = request.data
        adm = None
        if d.get("admission"):
            adm = Admission.objects.filter(pk=d.get("admission")).first()
            if not adm:
                return Response({"error": "আবেদনটি পাওয়া যায়নি"}, status=400)
        name = str(d.get("name") or d.get("name_bn") or (adm.name if adm else "")).strip()
        if not name:
            return Response({"error": "নাম দিতে হবে"}, status=400)

        # কোর্স ও উস্তাদ — দেওয়া থাকলে সত্যিই আছে কিনা যাচাই করে নিই, নইলে
        # ভুল আইডিতে অ্যাকাউন্ট তৈরি হয়ে পরে খালি পর্দা দেখাত
        course = None
        if d.get("course"):
            course = Course.objects.filter(pk=d.get("course")).first()
            if not course:
                return Response({"error": "কোর্সটি পাওয়া যায়নি"}, status=400)
        teacher = None
        if d.get("teacher"):
            teacher = User.objects.filter(pk=d.get("teacher"), role="teacher").first()
            if not teacher:
                return Response({"error": "উস্তাদকে পাওয়া যায়নি"}, status=400)

        until = d.get("trial_until") or None
        if not until:
            try:
                days = int(d.get("days") or 7)
            except (TypeError, ValueError):
                days = 7
            days = max(1, min(days, 90))  # এক দিনের কম বা তিন মাসের বেশি নয়
            until = timezone.localtime().date() + timedelta(days=days)

        pwd = make_password_str(8)
        u = User.objects.create_user(
            username=make_trial_username(User), password=pwd, role="trial",
            name_bn=name,
            guardian=str(d.get("guardian") or (adm.guardian if adm else "")),
            country=str(d.get("country") or (adm.country if adm else "")),
            phone=str(d.get("phone") or (adm.contact if adm else "")),
            email=str(d.get("email") or (adm.email if adm else "")),
            plain_password=pwd,          # পরিচালক পরিবারকে পাঠাবেন
            trial_until=until,
            trial_course=course,
            teacher=teacher,
            trial_admission=adm,
        )
        return Response(self.get_serializer(u).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminLevel])
    def reset_password(self, request, pk=None):
        """পাসওয়ার্ড হারিয়ে গেলে নতুন একটি — পুরনোটি আর কাজ করবে না।"""
        from .utils import make_password_str
        u = self.get_object()
        pwd = make_password_str(8)
        u.set_password(pwd)
        u.plain_password = pwd
        u.save(update_fields=["password", "plain_password"])
        return Response(self.get_serializer(u).data)

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def convert(self, request, pk=None):
        """অতিথিকে নিয়মিত শিক্ষার্থী বানানো — একই অ্যাকাউন্টেই।

        নতুন অ্যাকাউন্ট তৈরি হয় না, তাই ট্রায়ালের হাজিরা, রিপোর্ট ও সব
        তথ্য তাঁর সাথেই থেকে যায় — আর পরিবারকে নতুন আইডি-পাসওয়ার্ডও
        পাঠাতে হয় না, পুরনোটাই চলতে থাকে।

        ⚠️ trial_until/trial_course মোছা হয় না — কবে কোন কোর্সে ট্রায়াল
        করেছিলেন সেই ইতিহাসটা থেকে যায়।
        """
        u = self.get_object()
        if u.role != "trial":
            return Response({"error": "ইনি ট্রায়াল অতিথি নন"}, status=400)
        course = Course.objects.filter(pk=request.data.get("course")).first() \
            or u.trial_course
        if not course:
            return Response({"error": "কোন কোর্সে ভর্তি হবেন তা বেছে দিন"}, status=400)
        _convert_trial_to_student(u, course, request.data.get("fee"))
        # তাঁর ট্রায়াল থেকে আসা আবেদনটিও (থাকলে) গৃহীত হিসেবে বন্ধ করে দিই,
        # নইলে "ভর্তি আবেদন" পর্দায় ঝুলে থেকে দ্বিতীয়বার গ্রহণের সুযোগ দিত
        Admission.objects.filter(created_student=u, status="pending").update(
            status="accepted")
        return Response(UserSerializer(u).data)

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def credentials(self, request, pk=None):
        """অতিথির আইডি ও পাসওয়ার্ড বদলানো — কেবল পরিচালক।

        দুটোর যেকোনো একটি দিলেই চলে; যেটি দেওয়া হয়নি সেটি অপরিবর্তিত থাকে।
        আইডি বদলালে পুরনো আইডিতে আর লগইন হয় না, তাই পরিবারকে নতুন আইডি
        জানিয়ে দিতে হবে — পর্দায় সেই কথাটি মনে করিয়ে দেওয়া হয়।
        """
        u = self.get_object()
        fields = []
        raw_name = request.data.get("username")
        if raw_name is not None:
            name = str(raw_name).strip()
            if not name:
                return Response({"error": "আইডি খালি রাখা যাবে না"}, status=400)
            if len(name) > 150:
                return Response({"error": "আইডি অনেক লম্বা হয়ে গেছে"}, status=400)
            # ⚠️ বড়-ছোট হাতের অক্ষর আলাদা করে দেখা হয় না — নইলে "ayesha" ও
            # "Ayesha" দুটো আলাদা অ্যাকাউন্ট হয়ে লগইনে গোলমাল বাধত
            if User.objects.filter(username__iexact=name).exclude(pk=u.pk).exists():
                return Response({"error": "এই আইডিতে আগে থেকেই একটি অ্যাকাউন্ট আছে"},
                                status=400)
            try:
                for v in User._meta.get_field("username").validators:
                    v(name)
            except DjangoValidationError:
                return Response(
                    {"error": "আইডিতে ফাঁকা জায়গা বা বিশেষ চিহ্ন চলবে না — "
                              "অক্ষর, সংখ্যা এবং @ . + - _ ব্যবহার করুন"},
                    status=400)
            u.username = name
            fields.append("username")

        raw_pw = request.data.get("password")
        if raw_pw is not None:
            pw = str(raw_pw).strip()
            if len(pw) < 4:
                return Response({"error": "পাসওয়ার্ড অন্তত ৪ অক্ষরের হতে হবে"},
                                status=400)
            u.set_password(pw)
            u.plain_password = pw  # পরিচালক পরিবারকে জানাবেন
            fields += ["password", "plain_password"]

        if not fields:
            return Response({"error": "আইডি বা পাসওয়ার্ড — অন্তত একটি দিন"},
                            status=400)
        u.save(update_fields=fields)
        return Response(self.get_serializer(u).data)

    def destroy(self, request, *args, **kwargs):
        """ট্রায়াল অ্যাকাউন্ট মুছে ফেলা — কেবল পরিচালক।

        ⚠️ এর সাথে তাঁর ট্রায়ালের হাজিরা ও মূল্যায়নের রিপোর্টও চিরতরে
        মুছে যায় (ডাটাবেসের নিয়মেই)। তাই পর্দায় স্পষ্ট করে জানিয়ে দিয়ে
        নিশ্চিত করা হয়। ভর্তি আবেদন থাকলে সেটি থেকে যায়, শুধু অ্যাকাউন্টের
        সংযোগটি খালি হয়ে যায়।
        """
        if request.user.role != "director":
            raise PermissionDenied("ট্রায়াল অ্যাকাউন্ট মোছা কেবল পরিচালকের এখতিয়ার")
        return super().destroy(request, *args, **kwargs)


class AdmissionViewSet(viewsets.ModelViewSet):
    queryset = Admission.objects.all().order_by("-applied_at")
    serializer_class = AdmissionSerializer

    def get_throttles(self):
        if self.action == "create":
            return [_PublicFormThrottle()]
        return super().get_throttles()

    def get_permissions(self):
        if self.action == "create":
            return []  # ওয়েবসাইটের পাবলিক ভর্তি/ট্রায়াল/যোগাযোগ ফরম
        # মুছে ফেলাও গ্রহণ/বাতিলের মতোই — আবেদনটি চিরতরে চলে যায়, তাই
        # এডমিন নয়, কেবল পরিচালক। অ্যাপের অন্য সব "মুছুন" বাটনেও একই নিয়ম।
        if self.action in ("accept", "reject", "destroy"):
            # গ্রহণ/বাতিলের ক্ষমতা কেবল পরিচালকের — এডমিন বিস্তারিত দেখে
            # পরিচালক বরাবর পাঠাবেন (UI-তেও এই কথাই বলা আছে)। reject অ্যাকশনের
            # @action ডেকোরেটরে permission_classes=[IsDirector] বসানো ছিল, কিন্তু
            # এই get_permissions() override সেটা কখনো পড়ত না (শুধু "accept"
            # স্পেশাল-কেস করা ছিল) — ফলে বাস্তবে এডমিনও reject করতে পারতেন
            return [IsDirector()]
        return [IsAdminLevel()]

    def perform_create(self, serializer):
        """ওয়েবসাইট থেকে নতুন আবেদন এলেই এডমিন ও পরিচালককে নোটিফিকেশন"""
        a = serializer.save()
        kind_bn = {"trial": "ফ্রি ট্রায়াল অনুরোধ", "contact": "যোগাযোগ বার্তা", "enroll": "ভর্তি আবেদন (পেমেন্টসহ)", "admission": "ভর্তি আবেদন"}.get(a.kind, "ভর্তি আবেদন")
        notify(f"🌐 ওয়েবসাইট থেকে নতুন {kind_bn}: {a.name}" + (f" ({a.course_name})" if a.course_name else ""),
               User.objects.filter(role__in=["admin", "director"]))

    @action(detail=True, methods=["post"])
    def send_reply(self, request, pk=None):
        """এক ক্লিকে প্রস্তুত WhatsApp বার্তা — ট্রায়াল/যোগাযোগের রিপ্লাই"""
        a = self.get_object()
        phone = "".join(ch for ch in a.contact if ch.isdigit())
        if len(phone) < 8:
            return Response({"error": "এই আবেদনে বৈধ WhatsApp নম্বর নেই"}, status=400)
        if a.kind == "trial":
            text = (f"আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম, তারবিয়াতুল কুরআন একাডেমিতে "
                    f"\"{a.course_name or 'কুরআন'}\" কোর্সের ফ্রি ট্রায়াল ক্লাসের জন্য {a.name}-এর অনুরোধটি "
                    f"আমরা পেয়েছি, আলহামদুলিল্লাহ। আপনার পছন্দের সময় ({a.preferred_time or 'আলোচনাসাপেক্ষ'}) "
                    f"বিবেচনায় রেখে ক্লাস শিডিউল চূড়ান্ত করতে আমরা শীঘ্রই এই নম্বরে যোগাযোগ করছি ইনশাআল্লাহ। "
                    f"জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি")
        else:
            text = (f"আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম {a.name}, আপনার বার্তাটি আমরা পেয়েছি, "
                    f"আলহামদুলিল্লাহ। আমাদের একজন প্রতিনিধি শীঘ্রই আপনার সাথে যোগাযোগ করবেন ইনশাআল্লাহ। "
                    f"জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি")
        from .tasks import dispatch_whatsapp
        m = WaMessage.objects.create(to_name=a.name, phone=phone, text=text, reason="reminder")
        try:
            dispatch_whatsapp(m.id)
        except Exception:
            pass  # WhatsApp ব্যর্থ হলেও replied চিহ্নিত হবে — আউটবক্স থেকে আবার পাঠানো যায়
        a.replied = True
        a.save(update_fields=["replied"])
        return Response({"replied": True, "wa_status": WaMessage.objects.get(pk=m.pk).status})

    @action(detail=True, methods=["post"])
    def forward(self, request, pk=None):  # এডমিন → পরিচালক বরাবর পাঠান
        a = self.get_object()
        a.forwarded_to_director = True
        a.save()
        notify(f"এডমিন একটি ভর্তি আবেদন পরিচালক বরাবর পাঠিয়েছেন: {a.name} ({a.course_name})",
               User.objects.filter(role="director"))
        return Response({"forwarded": True})

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):  # গ্রহণ → স্টুডেন্ট অটো তৈরি, কোর্সে যুক্ত
        a = self.get_object()
        if a.status != "pending":
            # ডাবল-ক্লিক/দুইবার রিকোয়েস্ট গেলে দ্বিতীয়বার আরেকটা ডুপ্লিকেট
            # স্টুডেন্ট অ্যাকাউন্ট তৈরি হওয়া ঠেকাতে — একবার গ্রহণ হয়ে গেলে
            # আর দ্বিতীয়বার গ্রহণ করা যাবে না
            return Response({"error": "এই আবেদনটি ইতিমধ্যে সিদ্ধান্ত নেওয়া হয়ে গেছে"}, status=400)
        # ট্রায়াল থেকে আসা আবেদন — ওই অতিথিকেই ভর্তি করা হয়, নতুন অ্যাকাউন্ট
        # নয়। তাই তাঁর আইডি-পাসওয়ার্ড আগেরটাই থাকে এবং ট্রায়ালের হাজিরা ও
        # রিপোর্ট হারায় না।
        guest = a.created_student
        if guest and guest.role == "trial":
            course = Course.objects.filter(name=a.course_name).first() \
                or guest.trial_course
            _convert_trial_to_student(guest, course, request.data.get("fee"))
            a.status = "accepted"
            a.save(update_fields=["status"])
            return Response({"username": guest.username, "password": None,
                             "converted": True})

        from .utils import make_password_str
        pwd = make_password_str(8)
        username = request.data.get("username") or f"student{User.objects.filter(role='student').count() + 1}"
        student = User.objects.create_user(
            username=username, password=pwd, role="student",
            name_bn=f"{a.name} ({a.country})" if a.country else a.name,
            guardian=a.guardian, country=a.country, phone=a.contact,
            plain_password=pwd,  # পরিচালকের দেখার জন্য দেখা-যায় কপি
            monthly_fee=request.data.get("fee", DEFAULT_STUDENT_FEE))
        # ভর্তি গ্রহণ করে তৈরি হওয়া স্টুডেন্টের জন্যও অটো স্টুডেন্ট আইডি
        from .student_id import assign_student_id
        if assign_student_id(student, User):
            student.save(update_fields=["student_id"])
        course = Course.objects.filter(name=a.course_name).first()
        if course:
            course.students.add(student)
        a.status = "accepted"
        a.created_student = student
        a.save()
        # গ্রহণের পর অভিভাবকের WhatsApp এ আইডি-পাসওয়ার্ডসহ স্বাগত বার্তা
        phone = "".join(ch for ch in a.contact if ch.isdigit())
        if len(phone) >= 8:
            text = (f"আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম, আলহামদুলিল্লাহ — "
                    f"তারবিয়াতুল কুরআন একাডেমিতে {a.name}-এর ভর্তি নিশ্চিত হয়েছে। "
                    f"নিয়মিত ক্লাসে যোগ দিতে আমাদের ম্যানেজমেন্ট পোর্টালে লগইন করুন:\n\n"
                    f"🔗 https://app.tarbiyatulquran.org\n"
                    f"👤 আইডি: {username}\n"
                    f"🔑 পাসওয়ার্ড: {pwd}\n\n"
                    f"প্রথমবার লগইন করে পাসওয়ার্ডটি পরিবর্তন করে নেবেন। "
                    f"জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি")
            from .tasks import dispatch_whatsapp
            m = WaMessage.objects.create(to_name=a.name, phone=phone, text=text, reason="reminder")
            try:
                dispatch_whatsapp(m.id)
            except Exception:
                pass
        return Response({"username": username, "password": pwd})  # অভিভাবককে জানানোর জন্য

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def reject(self, request, pk=None):
        a = self.get_object()
        a.status = "rejected"
        a.save()
        return Response({"status": "rejected"})


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        # select_related("applicant") → applicant_name/applicant_role প্রতি আবেদনে
        # আলাদা কোয়েরি এড়ায়
        qs = LeaveRequest.objects.select_related("applicant")
        if u.role in ("director", "admin"):
            return qs.order_by("-applied_at")
        return qs.filter(applicant=u)

    def perform_create(self, serializer):
        lv = serializer.save(applicant=self.request.user)
        notify(f"✉️ {lv.applicant.name_bn} ছুটির আবেদন করেছেন ({lv.leave_type}: "
               f"{lv.from_date} — {lv.to_date})", admins())

    @action(detail=True, methods=["post"], permission_classes=[IsAdminLevel])
    def forward(self, request, pk=None):  # এডমিন মঞ্জুর করতে পারে না — শুধু পাঠাবে
        lv = self.get_object()
        lv.status = "forwarded"
        lv.save()
        notify(f"✉️ এডমিন {lv.applicant.name_bn}-এর ছুটির আবেদন পরিচালক বরাবর পাঠিয়েছেন।",
               User.objects.filter(role="director"))
        return Response({"status": "forwarded"})

    @action(detail=True, methods=["post"], permission_classes=[IsDirector])
    def decide(self, request, pk=None):  # মঞ্জুর/নামঞ্জুর — কেবল পরিচালক
        lv = self.get_object()
        ok = bool(request.data.get("approve"))
        lv.status = "approved" if ok else "rejected"
        lv.decided_by = request.user
        lv.save()
        notify(f"আপনার ছুটির আবেদন ({lv.leave_type}) "
               f"{'মঞ্জুর হয়েছে ✔ আলহামদুলিল্লাহ' if ok else 'নামঞ্জুর হয়েছে ✘'}।", [lv.applicant])
        return Response({"status": lv.status})


class RatingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        if u.role in ("director", "admin"):
            return Rating.objects.all()  # নাম-মন্তব্যসহ
        if u.role == "teacher":
            return Rating.objects.filter(teacher=u)  # গোপনীয় serializer
        return Rating.objects.filter(student=u)

    def get_serializer_class(self):
        return RatingAnonymousSerializer if self.request.user.role == "teacher" else RatingSerializer

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def teacher_summary(self, request):  # টিচার রিপোর্ট: গড় ★ + ডিস্ট্রিবিউশন
        tid = request.query_params.get("teacher", request.user.id)
        qs = Rating.objects.filter(teacher_id=tid)
        return Response({
            "avg": qs.aggregate(a=Avg("stars"))["a"],
            "count": qs.count(),
            "distribution": {s: qs.filter(stars=s).count() for s in range(5, 0, -1)},
        })


class StudentRemarkViewSet(viewsets.ModelViewSet):
    """টিচারের মন্তব্য — স্টুডেন্টের ব্যাপারে। স্টুডেন্ট শুধু নিজেরটা দেখে, লেখা/মোছা
    কেবল টিচার-লেভেল (টিচার/এডমিন/পরিচালক)"""
    serializer_class = StudentRemarkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = StudentRemark.objects.select_related("teacher", "student")
        student_id = self.request.query_params.get("student")
        if u.role == "trial":
            # অতিথি সম্পর্কে বা অন্য কারও সম্পর্কে কোনো মন্তব্যই তাঁর দেখার নয়
            return qs.none()
        if u.role == "student":
            qs = qs.filter(student=u)
        elif u.role == "teacher":
            # টিচার শুধু নিজের লেখা মন্তব্যই দেখবে, এবং শুধু নিজের কোর্সের স্টুডেন্ট নিয়ে —
            # অন্য টিচারের ছাত্র সম্পর্কে বা অন্য টিচারের লেখা মন্তব্য নয়
            qs = qs.filter(teacher=u)
            if student_id and not Course.objects.filter(
                teacher=u, students_id=student_id
            ).exists():
                return qs.none()
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsTeacherOrAdminLevel()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        u = self.request.user
        if u.role == "teacher":
            student = serializer.validated_data.get("student")
            if not Course.objects.filter(teacher=u, students=student).exists():
                raise PermissionDenied("আপনি এই স্টুডেন্টের টিচার নন")
        serializer.save(teacher=u)


# ─────────────────────────── নোটিশ, নোটিফিকেশন, WhatsApp ───────────────────────────
def _notice_text(n):
    """নোটিশ প্রকাশের সময় যে লেখাটি নোটিফিকেশনে যায় — একটাই জায়গা।

    এই লেখাটা নোটিশ থেকেই তৈরি হয় বলে পরে নোটিশটি খুঁজে বের করা যায়:
    এডিট করলে নোটিফিকেশনের লেখাও মিলিয়ে দেওয়া যায়, আর মুছে ফেললে
    নোটিফিকেশনটাও সাথে মুছে ফেলা যায়। এজন্যই এটি ছড়িয়ে না রেখে
    এক জায়গায় রাখা।
    """
    return f"📢 {n.title} — {n.body}"


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [ReadAllWriteAdmin]

    def perform_create(self, serializer):
        """নতুন নোটিশ দিলে সবার কাছে নোটিফিকেশনও চলে যায়।

        আগে নোটিশ কেবল নোটিশ পেইজে বসে থাকত — কেউ ওই পেইজে না গেলে কোনোদিন
        জানতেই পারতেন না। এখন সবার নোটিফিকেশন ঘণ্টায় ও পুশ-চালু ডিভাইসে
        পৌঁছায়, আর পোর্টাল খুললেই পুরো পর্দা ঢেকে দেখানো হয়।

        ⚠️ কেবল নতুন নোটিশে — এডিট করলে নয় (perform_update ছোঁয়া হয়নি)।
        নইলে বানান ঠিক করলেও সবার কাছে আবার বাজত।
        """
        obj = serializer.save()
        try:
            notify(_notice_text(obj), list(User.objects.filter(is_active=True)))
        except Exception:
            # নোটিফিকেশন পাঠানো ব্যর্থ হলেও নোটিশ তৈরি হওয়াটা আটকানো যাবে না —
            # নইলে সেভ হয়ে যাওয়া নোটিশের জন্য ভুল করে ব্যর্থতা দেখিয়ে এডমিন
            # আবার পোস্ট করতেন, আর একই নোটিশ দুবার হয়ে যেত
            pass

    def perform_update(self, serializer):
        """নোটিশ সংশোধন — সবার নোটিফিকেশনের লেখাটাও মিলিয়ে দেওয়া হয়।

        ⚠️ নতুন করে কাউকে জানানো হয় না, ঘণ্টাও বাজে না — বানান ঠিক করলে
        সবার কাছে আবার বেজে ওঠা বিরক্তিকর হতো। কেবল আগের যে বার্তাটি
        গিয়েছিল সেটির লেখা হালনাগাদ হয়, যাতে নোটিশ ও নোটিফিকেশন দুই
        জায়গায় দুই কথা না থাকে।
        """
        before = _notice_text(serializer.instance)
        obj = serializer.save()
        after = _notice_text(obj)
        if after != before:
            Notification.objects.filter(text=before).update(text=after)

    def perform_destroy(self, instance):
        """নোটিশ মুছে ফেলা — সবার নোটিফিকেশন থেকেও মুছে যায়।

        নোটিশটি একটাই সারি, তাই মুছলেই সবার পাতা থেকে চলে যায়। কিন্তু
        প্রকাশের সময় পাঠানো নোটিফিকেশনটি আলাদা সারি — সেটিও একই সাথে
        মুছে ফেলা হয়, নইলে নোটিশ নেই অথচ ঘণ্টায় বার্তাটি রয়ে যেত।
        """
        Notification.objects.filter(text=_notice_text(instance)).delete()
        instance.delete()


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # prefetch_related("read_by") → NotificationSerializer.get_is_read প্রতি
        # নোটিফিকেশনে আলাদা কোয়েরি না করে prefetch cache ব্যবহার করে (N+1 এড়ায়) —
        # এই এন্ডপয়েন্ট প্রায় প্রতি পেজেই (নোটিফিকেশন বেল) চলে, তাই প্রভাব বড়
        return self.request.user.notifications.prefetch_related("read_by").all()

    # প্রত্যেকের কাছে কেবল সবশেষ এতগুলো নোটিফিকেশন থাকবে
    KEEP_NOTIFICATIONS = 3

    def list(self, request, *args, **kwargs):
        """নিজের সবশেষ ৩টি নোটিফিকেশন — পুরনোগুলো এখানেই ছেঁটে ফেলা হয়।

        ⚠️ এটি সত্যিই মুছে ফেলে, কেবল লুকায় না — পরিচালকের নির্দেশ।
        তবে ছাঁটাইটা প্রত্যেকের নিজের তালিকা ধরে: একজনের পুরনো হয়ে গেলেও
        অন্যজনের না-পড়া নোটিফিকেশন হারায় না। কোনো নোটিফিকেশনের আর একজন
        প্রাপকও বাকি না থাকলে তবেই সেটি ডাটাবেস থেকে মুছে যায়।

        তালিকাটা এমনিতেই পড়া হচ্ছে, তাই "৩টির বেশি আছে কি না" জানতে বাড়তি
        কোনো কোয়েরি লাগে না — ৩টি বা কম হলে কিছুই করা হয় না, অর্থাৎ
        স্বাভাবিক অবস্থায় ডাটাবেসে কোনো বাড়তি চাপ পড়ে না।
        """
        rows = list(self.get_queryset())
        if len(rows) > self.KEEP_NOTIFICATIONS:
            old_ids = [n.id for n in rows[self.KEEP_NOTIFICATIONS:]]
            u = request.user
            Notification.recipients.through.objects.filter(
                user_id=u.id, notification_id__in=old_ids).delete()
            Notification.read_by.through.objects.filter(
                user_id=u.id, notification_id__in=old_ids).delete()
            # আর কোনো প্রাপক নেই এমনগুলো সম্পূর্ণ মুছে ফেলি
            Notification.objects.filter(
                id__in=old_ids, recipients__isnull=True).delete()
            rows = rows[: self.KEEP_NOTIFICATIONS]
        return Response(self.get_serializer(rows, many=True).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        for n in self.get_queryset():
            n.read_by.add(request.user)
        return Response({"ok": True})

    @action(detail=False, methods=["post"], permission_classes=[IsDirector])
    def broadcast(self, request):
        """পরিচালক সবাইকে একসাথে একটা বার্তা পাঠান।

        দুই জায়গাতেই যায় — (১) সবার পোর্টালের নোটিফিকেশন ঘণ্টায় (এটা সবসময়
        পৌঁছায়), (২) যাঁরা পুশ নোটিফিকেশন চালু করেছেন তাঁদের ফোনে/ডেস্কটপে,
        অ্যাপ বন্ধ থাকলেও। পুশ ব্যর্থ হলেও ইন-অ্যাপ নোটিফিকেশন আটকায় না
        (notify() নিজেই সেটা সামলায়)।

        কেবল পাঠায় — কোনো ডাটা বদলায় বা মোছে না।
        """
        text = (request.data.get("text") or "").strip()
        if not text:
            return Response({"error": "বার্তা লিখুন"}, status=400)
        if len(text) > 500:
            return Response({"error": "বার্তা ৫০০ অক্ষরের মধ্যে রাখুন"}, status=400)
        # নিষ্ক্রিয় (ছেড়ে যাওয়া) ব্যবহারকারীদের বাদ — তাঁদের পাঠিয়ে লাভ নেই
        users = list(User.objects.filter(is_active=True))
        notify(text, users)
        return Response({"sent": len(users)})


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    """ব্রাউজার Web Push সাবস্ক্রিপশন সেভ/মুছা — অ্যাপ ইনস্টল/নোটিফিকেশন পারমিশন
    দেওয়ার সময় ফ্রন্টএন্ড থেকে ডাকা হয়"""
    serializer_class = PushSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "delete", "head", "options"]

    def get_queryset(self):
        return PushSubscription.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        endpoint = request.data.get("endpoint")
        if not endpoint:
            return Response({"error": "endpoint আবশ্যক"}, status=400)
        sub, _ = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "p256dh": request.data.get("p256dh", ""),
                "auth": request.data.get("auth", ""),
            },
        )
        return Response(PushSubscriptionSerializer(sub).data, status=201)

    @action(detail=False, methods=["post"])
    def unsubscribe(self, request):
        endpoint = request.data.get("endpoint")
        if endpoint:
            PushSubscription.objects.filter(endpoint=endpoint, user=request.user).delete()
        return Response({"ok": True})


class WaMessageViewSet(viewsets.ModelViewSet):
    queryset = WaMessage.objects.all().order_by("-created_at")
    serializer_class = WaMessageSerializer
    permission_classes = [IsAdminLevel]

    @action(detail=True, methods=["post"])
    def send_now(self, request, pk=None):
        """তাৎক্ষণিক পাঠানো/রিট্রাই — dispatch_whatsapp() ব্যবহার করে, যা USE_CELERY
        চেক করে Celery worker না থাকলে (Render-এ যেমন আছে — কোনো worker সার্ভিস
        ডিপ্লয় করা নেই) সরাসরি (synchronous) পাঠায়। আগে সরাসরি send_whatsapp.delay()
        ডাকা হতো, যা কোনো Redis/worker ছাড়া কানেকশন এরর দিয়ে ব্যর্থ হতো — director-এর
        "আউটবক্স"-এ ব্যর্থ মেসেজ রিট্রাই করার একমাত্র বাটনটাই কখনো কাজ করত না
        """
        from .tasks import dispatch_whatsapp
        try:
            dispatch_whatsapp(pk)
        except Exception as e:
            return Response({"error": str(e)}, status=502)
        return Response({"queued": True})


# ─────────────────────────── লাইব্রেরি বই (বাহ্যিক লিংক) ───────────────────────────
class LibraryBookViewSet(viewsets.ModelViewSet):
    queryset = LibraryBook.objects.all()
    serializer_class = LibraryBookSerializer
    permission_classes = [ReadAllWriteAdmin]  # সবাই দেখতে পারে, যোগ/মুছা এডমিন+


# ─────────────────────────── ডেটা এক্সপোর্ট (পরিচালক মাত্র) ───────────────────────────
@api_view(["GET"])
@pc([IsDirector])
def export_all_data(request):
    """সম্পূর্ণ ডেটাবেস JSON হিসেবে ডাউনলোড — কেবল পরিচালক"""
    from django.core import serializers as dj_ser

    def qs_to_list(qs):
        return json.loads(dj_ser.serialize("json", qs))

    payload = {
        "exported_at": timezone.now().isoformat(),
        "users": qs_to_list(User.objects.exclude(is_superuser=True)),
        "courses": qs_to_list(Course.objects.all()),
        "academic_books": qs_to_list(AcademicBook.objects.all()),
        "library_books": qs_to_list(LibraryBook.objects.all()),
        "admissions": qs_to_list(Admission.objects.all()),
        "fee_payments": qs_to_list(FeePayment.objects.all()),
        "due_months": qs_to_list(DueMonth.objects.all()),
        "teacher_payments": qs_to_list(TeacherPayment.objects.all()),
        "sent_receipts": qs_to_list(SentReceipt.objects.all()),
        "notices": qs_to_list(Notice.objects.all()),
        "leave_requests": qs_to_list(LeaveRequest.objects.all()),
        "assignments": qs_to_list(Assignment.objects.all()),
        "exams": qs_to_list(Exam.objects.all()),
        "exam_results": qs_to_list(ExamResult.objects.all()),
        "class_sessions": qs_to_list(ClassSession.objects.all()),
        "attendance": qs_to_list(Attendance.objects.all()),
        "ratings": qs_to_list(Rating.objects.all()),
    }

    content = json.dumps(payload, ensure_ascii=False, indent=2)
    filename = f"tqa-backup-{timezone.localtime().date().isoformat()}.json"
    resp = HttpResponse(content, content_type="application/json; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
