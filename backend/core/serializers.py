"""TQA-MS — DRF Serializers (অ্যাপ: core)"""
from rest_framework import serializers
from .models import (User, AcademicBook, Course, SyllabusItem, Lecture, LectureTopic,
                     Routine, ClassSession, Attendance, Question, Assignment, Exam,
                     Submission, ExamResult, FeePayment, DueMonth, TeacherPayment,
                     SentReceipt, Admission, LeaveRequest, Rating, Notice, Notification,
                     WaMessage, LibraryBook)


class UserSerializer(serializers.ModelSerializer):
    # Frontend "name" ও "sub" নামে খোঁজে — তাই name_bn/sub_title এর alias:
    name = serializers.CharField(source="name_bn", required=False)
    sub = serializers.CharField(source="sub_title", required=False, allow_blank=True)
    due_months = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "role", "name", "name_bn", "sub", "sub_title",
                  "phone", "country", "guardian", "email", "monthly_fee",
                  "monthly_salary", "class_days", "can_fix_cross", "due_months"]

    def get_due_months(self, obj):
        # .values_list()-এর বদলে .all() ইটারেট — prefetch_related("due_months") এর ক্যাশ
        # ব্যবহার হয়, নইলে প্রতি ব্যবহারকারীতে আলাদা কোয়েরি হতো (N+1)
        return [d.month_label for d in obj.due_months.all()]


class UserAdminSerializer(UserSerializer):
    """কেবল পরিচালকের জন্য — পাসওয়ার্ড সেট/রিসেট + দেখা-যায় কপি (কিছুই আড়াল নয়)"""
    password = serializers.CharField(write_only=True, required=False)
    plain_password = serializers.CharField(read_only=True)  # পরিচালক দেখতে পারবেন

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["password", "plain_password"]

    def create(self, validated):
        from .utils import make_password_str
        pwd = validated.pop("password", None) or make_password_str(8)
        user = User(**validated)
        user.set_password(pwd)
        user.plain_password = pwd  # পরিচালকের দেখার জন্য দেখা-যায় কপি
        user.save()
        return user

    def update(self, instance, validated):
        pwd = validated.pop("password", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
            instance.plain_password = pwd  # নতুন পাসওয়ার্ড → দেখা-যায় কপিও আপডেট
        instance.save()
        return instance


class AcademicBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicBook
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.name_bn", read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "name", "teacher", "teacher_name", "students", "books",
                  "color", "is_active", "student_count"]
    # কোর্সে বই সংখ্যায় কোনো সীমা নেই — যত খুশি যোগ করা যাবে

    def get_student_count(self, obj):
        # source="students.count" প্রতিবার নতুন COUNT কোয়েরি করত (prefetch_related উপেক্ষা করে)।
        # .all() ইটারেট করলে queryset-এর prefetch_related("students") ব্যবহার হয় — বাড়তি কোয়েরি নেই।
        return len(obj.students.all())


class SyllabusItemSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)
    book_name = serializers.SerializerMethodField()  # রিড: বইয়ের নাম
    # explicitly required — "__all__" এ model default থাকলে DRF required=False করে দেয়, ফলে qirat-এ চলে যায়
    category = serializers.ChoiceField(choices=SyllabusItem.Category.choices)

    class Meta:
        model = SyllabusItem
        fields = "__all__"

    def get_book_name(self, obj):
        return obj.book.name if obj.book_id else ""

    def to_internal_value(self, data):
        # ফ্রন্টএন্ড book_name (স্ট্রিং) পাঠায় → AcademicBook FK-তে রূপান্তর (বই সেভ নিশ্চিত)
        ret = super().to_internal_value(data)
        if hasattr(data, "keys") and "book_name" in data:
            name = (data.get("book_name") or "").strip()
            if name and name != "অন্যান্য":
                book, _ = AcademicBook.objects.get_or_create(name=name)
                ret["book"] = book
            else:
                ret["book"] = None
        return ret


class LectureTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = LectureTopic
        fields = ["id", "syllabus_item", "text", "covered"]


class LectureSerializer(serializers.ModelSerializer):
    topics = LectureTopicSerializer(many=True, read_only=True)
    syllabus_item_ids = serializers.ListField(child=serializers.IntegerField(),
                                              write_only=True, required=False)

    class Meta:
        model = Lecture
        fields = ["id", "course", "no", "title", "date", "topics", "syllabus_item_ids"]
        extra_kwargs = {"no": {"required": False}}

    def create(self, validated):
        ids = validated.pop("syllabus_item_ids", [])
        # দারস-নং দেওয়া না থাকলে স্বয়ংক্রিয়; দেওয়া থাকলে তা-ই ব্যবহার
        if not validated.get("no"):
            validated["no"] = Lecture.objects.filter(course=validated["course"]).count() + 1
        lec = Lecture.objects.create(**validated)
        for sid in ids:  # সিলেবাস থেকে টপিক সিলেকশন
            si = SyllabusItem.objects.get(pk=sid, course=lec.course)
            LectureTopic.objects.create(lecture=lec, syllabus_item=si, text=si.label)
        return lec

    def update(self, instance, validated):
        ids = validated.pop("syllabus_item_ids", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if ids is not None:  # টপিক তালিকা হালনাগাদ — কভার-স্ট্যাটাস যথাসম্ভব অক্ষত
            keep = set(ids)
            existing = {t.syllabus_item_id: t for t in instance.topics.all()}
            for sid, t in existing.items():
                if sid not in keep:
                    t.delete()
            for sid in ids:
                if sid in existing:
                    si = SyllabusItem.objects.filter(pk=sid, course=instance.course).first()
                    if si:
                        existing[sid].text = si.label
                        existing[sid].save(update_fields=["text"])
                else:
                    si = SyllabusItem.objects.filter(pk=sid, course=instance.course).first()
                    if si:
                        LectureTopic.objects.create(lecture=instance, syllabus_item=si, text=si.label)
        return instance


class RoutineSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.name_bn", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    student_names = serializers.SerializerMethodField()

    class Meta:
        model = Routine
        fields = "__all__"

    def get_student_names(self, obj):
        # .values_list() prefetch_related-এর ক্যাশ এড়িয়ে প্রতিবার নতুন কোয়েরি করত (N+1)।
        # .all() ইটারেট করলে queryset-এ prefetch করা students-ই ব্যবহার হয় — বাড়তি কোয়েরি নেই।
        return [s.name_bn for s in obj.students.all()]


class AttendanceSerializer(serializers.ModelSerializer):
    present = serializers.BooleanField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    user_name = serializers.CharField(source="user.name_bn", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "session", "user", "user_name", "minutes", "present",
                  "active", "marked_present", "joined_at", "left_at",
                  # denormalized — session ৬০ দিন পর মুছে গেলেও (SET_NULL) এই তথ্য থেকে যায়,
                  # তাই মাসিক রিপোর্ট সবসময় সম্পূর্ণ থাকে
                  "course_name", "teacher_name", "teacher_id", "class_date"]


class ClassSessionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.name_bn", read_only=True)
    student_names = serializers.SerializerMethodField()
    attendance = AttendanceSerializer(many=True, read_only=True)

    class Meta:
        model = ClassSession
        fields = "__all__"

    def get_student_names(self, obj):
        # .values_list()-এর বদলে .all() ইটারেট — prefetch_related-এর ক্যাশ ব্যবহার হয় (N+1 নেই)
        return [s.name_bn for s in obj.students.all()]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text", "qtype", "options", "correct_index"]


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name_bn", read_only=True)

    class Meta:
        model = Submission
        fields = "__all__"
        read_only_fields = ["student", "mark", "marked_by"]


class AssignmentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    submissions = SubmissionSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        fields = "__all__"

    def create(self, validated):
        qs = validated.pop("questions", [])
        a = Assignment.objects.create(**validated)
        for q in qs:
            Question.objects.create(assignment=a, **q)
        return a


class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    submissions = SubmissionSerializer(many=True, read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = "__all__"

    def get_results(self, obj):
        return {r.student_id: r.mark for r in obj.results.all()}

    def create(self, validated):
        qs = validated.pop("questions", [])
        e = Exam.objects.create(**validated)
        for q in qs:
            Question.objects.create(exam=e, **q)
        return e


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name_bn", read_only=True)

    class Meta:
        model = FeePayment
        fields = "__all__"
        read_only_fields = ["status", "verified_by"]


class DueMonthSerializer(serializers.ModelSerializer):
    class Meta:
        model = DueMonth
        fields = "__all__"


class TeacherPaymentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.name_bn", read_only=True)

    class Meta:
        model = TeacherPayment
        fields = "__all__"


class SentReceiptSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source="sent_by.name_bn", read_only=True)

    class Meta:
        model = SentReceipt
        fields = "__all__"


class AdmissionSerializer(serializers.ModelSerializer):
    # website forms.js "payment_ref" পাঠায় → trx_id এ ম্যাপ
    payment_ref = serializers.CharField(source="trx_id", required=False, allow_blank=True)

    class Meta:
        model = Admission
        fields = "__all__"
        read_only_fields = ["status", "forwarded_to_director", "created_student"]


class LeaveRequestSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.name_bn", read_only=True)
    applicant_role = serializers.CharField(source="applicant.role", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = ["applicant", "status", "decided_by"]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"
        read_only_fields = ["student"]


class RatingAnonymousSerializer(serializers.ModelSerializer):
    """উস্তাদের জন্য — কে দিয়েছে, কী মন্তব্য করেছে তা গোপন"""
    class Meta:
        model = Rating
        fields = ["id", "stars", "rated_at", "course"]


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "text", "created_at", "is_read"]

    def get_is_read(self, obj):
        # .filter().exists() prefetch cache এড়িয়ে প্রতিবার নতুন কোয়েরি করত (N+1)।
        # .all() ইটারেট করে পাইথনে মেলানো — prefetch_related("read_by") ব্যবহার হয়।
        u = self.context["request"].user
        return any(ru.pk == u.pk for ru in obj.read_by.all())


class WaMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaMessage
        fields = "__all__"


class LibraryBookSerializer(serializers.ModelSerializer):
    # "#" বা খালি লিংককে URLField বৈধতা যাচাইয়ে আটকানো হবে না (নইলে "বৈধ URL দিন" এরর)
    link = serializers.CharField(required=False, allow_blank=True, default="#", max_length=500)

    class Meta:
        model = LibraryBook
        fields = ["id", "cls", "title", "author", "link", "file_type", "created_at"]
