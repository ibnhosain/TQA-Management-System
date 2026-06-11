"""TQA-MS — DRF ViewSets ও workflow actions (অ্যাপ: core)"""
from datetime import date
from django.db.models import Q, Avg, Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (User, AcademicBook, Course, SyllabusItem, Lecture, LectureTopic,
                     Routine, ClassSession, Attendance, Assignment, Exam, Submission,
                     ExamResult, FeePayment, DueMonth, TeacherPayment, SentReceipt,
                     Admission, LeaveRequest, Rating, Notice, Notification, WaMessage)
from .serializers import *
from .permissions import (IsDirector, IsAdminLevel, IsTeacherOrAdminLevel,
                          ReadAllWriteAdmin, ReadAllWriteDirector)


def notify(text, users):
    n = Notification.objects.create(text=text)
    n.recipients.set(users)
    return n


def admins():
    return User.objects.filter(role__in=["director", "admin"])


# ─────────────────────────── ব্যবহারকারী ───────────────────────────
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.exclude(is_superuser=True)
    permission_classes = [IsDirector]  # যোগ/মুছা/পাসওয়ার্ড — কেবল পরিচালক
    serializer_class = UserAdminSerializer

    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, permission_classes=[IsAdminLevel])
    def students(self, request):  # "সকল স্টুডেন্ট" পেজ — এডমিনও দেখতে পারে
        qs = User.objects.filter(role="student")
        ser = UserAdminSerializer if request.user.role == "director" else UserSerializer
        return Response(ser(qs, many=True).data)

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

    def get_queryset(self):  # রোল অনুযায়ী: এডমিন-লেভেল সব; বাকিরা নিজের কোর্সের বই
        u = self.request.user
        if u.role in ("director", "admin"):
            return AcademicBook.objects.all()
        if u.role == "teacher":
            return AcademicBook.objects.filter(course__teacher=u).distinct()
        return AcademicBook.objects.filter(course__students=u).distinct()


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [ReadAllWriteDirector]  # তৈরি/এডিট/বাদ — কেবল পরিচালক

    def get_queryset(self):
        u = self.request.user
        qs = Course.objects.filter(is_active=True)
        if u.role == "teacher":
            return qs.filter(teacher=u)
        if u.role == "student":
            return qs.filter(students=u)
        return qs


class SyllabusViewSet(viewsets.ModelViewSet):
    queryset = SyllabusItem.objects.all()
    serializer_class = SyllabusItemSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["course"]


class LectureViewSet(viewsets.ModelViewSet):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [ReadAllWriteDirector]
    filterset_fields = ["course"]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_topic(self, request):
        """টপিক ✔/✘ — উস্তাদ নিজের কোর্সে; লাল-ক্রস ঠিক করা কেবল এডমিন-লেভেল বা অনুমতিপ্রাপ্ত"""
        topic = LectureTopic.objects.get(pk=request.data["topic_id"])
        new = request.data["covered"]  # covered | missed | pending
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
            topic.lecture.date = date.today()
            topic.lecture.save()
        return Response(LectureTopicSerializer(topic).data)


# ─────────────────────────── রুটিন ও ক্লাস ───────────────────────────
class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer
    permission_classes = [ReadAllWriteAdmin]

    def get_queryset(self):
        u = self.request.user
        qs = Routine.objects.filter(is_active=True)
        if u.role == "teacher":
            return qs.filter(teacher=u)
        if u.role == "student":
            return qs.filter(students=u)
        return qs


class ClassSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSessionSerializer
    permission_classes = [ReadAllWriteAdmin]

    def get_queryset(self):
        u = self.request.user
        qs = ClassSession.objects.all()
        if u.role == "teacher":
            return qs.filter(Q(teacher=u) | Q(course__teacher=u)).distinct()
        if u.role == "student":
            return qs.filter(students=u)
        return qs

    @action(detail=False, permission_classes=[IsAuthenticated])
    def today(self, request):  # লাইভ পপআপ + "আজকের ক্লাস"
        qs = self.get_queryset().filter(date=date.today(), status="upcoming")
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):  # জুমে জয়েন → হাজিরা শুরু
        att, _ = Attendance.objects.get_or_create(session=self.get_object(), user=request.user)
        return Response(AttendanceSerializer(att).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):  # ক্লাস ত্যাগ → মিনিট হিসাব (৪০-মিনিট নিয়ম)
        att = Attendance.objects.get(session=self.get_object(), user=request.user)
        att.left_at = timezone.now()
        att.minutes = max(att.minutes, int((att.left_at - att.joined_at).total_seconds() // 60))
        att.save()
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
        notify(msg, studs + [s.teacher] + list(admins()))
        for st in studs:  # অভিভাবকের WhatsApp — Celery টাস্ক পাঠাবে
            if st.phone:
                WaMessage.objects.create(to_name=st.guardian or st.name_bn, student=st,
                                         phone=st.phone, text=msg, reason="postpone")
        return Response({"status": "postponed"})


# ─────────────────────────── অ্যাসাইনমেন্ট ও পরীক্ষা ───────────────────────────
class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course"]

    def get_queryset(self):
        u = self.request.user
        if u.role == "student":
            return Assignment.objects.filter(course__students=u)
        if u.role == "teacher":
            return Assignment.objects.filter(course__teacher=u)
        return Assignment.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role == "student":
            raise PermissionError("স্টুডেন্ট অ্যাসাইনমেন্ট বানাতে পারে না")
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
        if u.role == "student":
            return Exam.objects.filter(course__students=u)
        if u.role == "teacher":
            return Exam.objects.filter(course__teacher=u)
        return Exam.objects.all()

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
        if u.role == "student":
            return FeePayment.objects.filter(student=u)
        if u.role in ("director", "admin"):
            return FeePayment.objects.all()
        return FeePayment.objects.none()

    def perform_create(self, serializer):  # স্টুডেন্টের "এখনই পেমেন্ট" → pending
        pay = serializer.save(student=self.request.user, status="pending")
        DueMonth.objects.filter(user=pay.student, month_label=pay.month_label).delete()
        notify(f"{pay.student.name_bn} — {pay.month_label} মাসের ফি পরিশোধ করেছে, "
               f"পরিচালকের ভেরিফাই বাকি।", admins())

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
        if u.role == "teacher":
            return TeacherPayment.objects.filter(teacher=u)
        if u.role == "director":
            return TeacherPayment.objects.all()
        return TeacherPayment.objects.none()

    def get_permissions(self):
        return [IsDirector()] if self.action in ("create", "update", "destroy") else [IsAuthenticated()]


class SentReceiptViewSet(viewsets.ModelViewSet):
    serializer_class = SentReceiptSerializer

    def get_queryset(self):
        u = self.request.user
        if u.role in ("director", "admin"):
            return SentReceipt.objects.all()
        return SentReceipt.objects.filter(to_user=u)  # নিজের ভাউচার/রিসিট

    def get_permissions(self):
        return [IsAdminLevel()] if self.action == "create" else [IsAuthenticated()]

    def perform_create(self, serializer):
        r = serializer.save(sent_by=self.request.user)
        notify(f"🧾 আপনার পোর্টালে একটি \"{r.kind}\" পাঠানো হয়েছে — ভাউচার/রিসিট মেনুতে দেখুন।",
               [r.to_user])


# ─────────────────────────── ভর্তি, ছুটি, মূল্যায়ন ───────────────────────────
class AdmissionViewSet(viewsets.ModelViewSet):
    queryset = Admission.objects.all().order_by("-applied_at")
    serializer_class = AdmissionSerializer

    def get_permissions(self):
        if self.action == "create":
            return []  # ওয়েবসাইটের পাবলিক ভর্তি ফরম
        if self.action == "accept":
            return [IsDirector()]  # গ্রহণ কেবল পরিচালক
        return [IsAdminLevel()]

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
        pwd = User.objects.make_random_password(8)
        username = request.data.get("username") or f"student{User.objects.filter(role='student').count() + 1}"
        student = User.objects.create_user(
            username=username, password=pwd, role="student",
            name_bn=f"{a.name} ({a.country})" if a.country else a.name,
            guardian=a.guardian, country=a.country, phone=a.contact,
            monthly_fee=request.data.get("fee", 4500))
        course = Course.objects.filter(name=a.course_name).first()
        if course:
            course.students.add(student)
        a.status = "accepted"
        a.created_student = student
        a.save()
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
        if u.role in ("director", "admin"):
            return LeaveRequest.objects.all().order_by("-applied_at")
        return LeaveRequest.objects.filter(applicant=u)

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


# ─────────────────────────── নোটিশ, নোটিফিকেশন, WhatsApp ───────────────────────────
class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [ReadAllWriteAdmin]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.all()

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        for n in self.get_queryset():
            n.read_by.add(request.user)
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
