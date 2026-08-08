"""TQA-MS — DRF ViewSets ও workflow actions (অ্যাপ: core)"""
import json
from django.db.models import Q, Avg, Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes as pc
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response

from .models import (User, AcademicBook, Course, SyllabusItem, Lecture, LectureTopic,
                     Routine, RoutineStudentSchedule, ClassSession, Attendance, Assignment, Exam, Submission,
                     ExamResult, FeePayment, DueMonth, TeacherPayment, SentReceipt,
                     Admission, LeaveRequest, Rating, StudentRemark, Notice, Notification,
                     PushSubscription, WaMessage, LibraryBook)
from .serializers import *
from .permissions import (IsDirector, IsAdminLevel, IsTeacherOrAdminLevel,
                          ReadAllWriteAdmin, ReadAllWriteDirector)


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
            return qs.filter(teacher=u)
        if u.role == "student":
            return qs.filter(students=u)
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


class LectureViewSet(viewsets.ModelViewSet):
    # prefetch_related("topics") → নেস্টেড topics প্রতি লেকচারে আলাদা কোয়েরি না করে
    # prefetch cache ব্যবহার করে (N+1 এড়ায়) — লেকচার প্ল্যান পেজে সব দারসের টপিক দেখায়
    queryset = Lecture.objects.prefetch_related("topics").all()
    serializer_class = LectureSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["course"]

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
        if not (is_admin or is_course_teacher):
            return Response({"detail": "অনুমতি নেই"}, status=403)
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
            return qs.filter(teacher=u)
        if u.role == "student":
            return qs.filter(students=u)
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
        # স্বয়ংক্রিয় টাইমজোন-হিসাব নয়) — সবসময় সম্পূর্ণ প্রতিস্থাপন করা হয়
        # (আগের এন্ট্রি মুছে নতুন করে বসানো), যাতে বাদ পড়া/সরানো স্টুডেন্টের
        # পুরনো এন্ট্রি থেকে না যায়
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


def _sync_mutual_presence(s):
    """উস্তাদ ও অন্তত একজন স্টুডেন্ট একই সময়ে (দুজনেই) মিটিংয়ে থাকলে সাথে সাথেই
    উভয়ের হাজিরা 'সম্পন্ন' মার্ক করে — এরপর কেউ কতক্ষণ থাকলেন তা আর হাজিরার
    জন্য গুরুত্বপূর্ণ না, শুধু জয়েন হওয়াটাই যথেষ্ট (পোর্টালে সতর্কতার জন্য এখনো
    "৪৫+ মিনিট" লেখা থাকে, কিন্তু বাস্তবে এই মিনিটের হিসাব আর গণনা হয় না)"""
    teacher_id = s.teacher_id or (s.course.teacher_id if s.course_id else None)
    if not teacher_id:
        return
    rows = list(Attendance.objects.filter(session=s))
    teacher_row = next((r for r in rows if r.user_id == teacher_id), None)
    teacher_active = bool(teacher_row and teacher_row.segment_start is not None)
    student_rows_active = [
        r for r in rows if r.user_id != teacher_id and r.segment_start is not None
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
            return qs.filter(Q(teacher=u) | Q(course__teacher=u)).distinct()
        if u.role == "student":
            return qs.filter(students=u)
        return qs

    def perform_update(self, serializer):
        # আজকের ক্লাস "সম্পন্ন" চিহ্নিত করা এডমিন+পরিচালক দুজনেই পারবেন — কিন্তু
        # বিগত (পুরনো) ক্লাসের স্ট্যাটাস সংশোধন কেবল পরিচালকের এখতিয়ার, এডমিন না
        if "status" in self.request.data and self.request.user.role != "director":
            is_today = serializer.instance.date == timezone.localtime().date()
            if not is_today:
                raise PermissionDenied("আজকের ক্লাস ছাড়া অন্য কোনো ক্লাসের স্ট্যাটাস বদলানো কেবল পরিচালকের এখতিয়ার")
        serializer.save()

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
        att = Attendance.objects.get(session=self.get_object(), user=request.user)
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
        att = Attendance.objects.get(session=self.get_object(), user=request.user)
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
            "any_student_active": rows.filter(segment_start__isnull=False).exclude(user_id=teacher_id).exists(),
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
            qs = qs.filter(teacher_id=u.id)
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
            return qs.filter(course__teacher=u)
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
            return qs.filter(course__teacher=u)
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
        return [IsAuthenticated()]

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
        deleted, _ = DueMonth.objects.filter(user_id=user_id, month_label=month_label).delete()
        return Response({"deleted": deleted})

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
        if self.action == "accept":
            return [IsDirector()]  # গ্রহণ কেবল পরিচালক
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
        from .utils import make_password_str
        pwd = make_password_str(8)
        username = request.data.get("username") or f"student{User.objects.filter(role='student').count() + 1}"
        student = User.objects.create_user(
            username=username, password=pwd, role="student",
            name_bn=f"{a.name} ({a.country})" if a.country else a.name,
            guardian=a.guardian, country=a.country, phone=a.contact,
            plain_password=pwd,  # পরিচালকের দেখার জন্য দেখা-যায় কপি
            monthly_fee=request.data.get("fee", 4500))
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
class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [ReadAllWriteAdmin]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # prefetch_related("read_by") → NotificationSerializer.get_is_read প্রতি
        # নোটিফিকেশনে আলাদা কোয়েরি না করে prefetch cache ব্যবহার করে (N+1 এড়ায়) —
        # এই এন্ডপয়েন্ট প্রায় প্রতি পেজেই (নোটিফিকেশন বেল) চলে, তাই প্রভাব বড়
        return self.request.user.notifications.prefetch_related("read_by").all()

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        for n in self.get_queryset():
            n.read_by.add(request.user)
        return Response({"ok": True})


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
        """তাৎক্ষণিক পাঠানো — Celery টাস্ককে ডাকে (tasks.send_whatsapp)"""
        from .tasks import send_whatsapp  # Celery task
        send_whatsapp.delay(pk)
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
