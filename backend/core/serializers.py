"""TQA-MS — DRF Serializers (অ্যাপ: core)"""
from rest_framework import serializers
from django.utils import timezone
from .safe_html import clean_html
from .models import (User, AcademicBook, Course, SyllabusItem, Lecture, LectureTopic,
                     Routine, ClassSession, Attendance, Question, Assignment, Exam,
                     Submission, ExamResult, FeePayment, DueMonth, TeacherPayment,
                     SentReceipt, Admission, LeaveRequest, Rating, StudentRemark, Notice,
                     Notification, PushSubscription, WaMessage, LibraryBook,
                     CourseSyllabusSheet, LessonSection)


class UserSerializer(serializers.ModelSerializer):
    # Frontend "name" ও "sub" নামে খোঁজে — তাই name_bn/sub_title এর alias:
    name = serializers.CharField(source="name_bn", required=False)
    sub = serializers.CharField(source="sub_title", required=False, allow_blank=True)
    due_months = serializers.SerializerMethodField()
    # শিক্ষার্থীর নিজস্ব উস্তাদ — "কার কাছে পড়ে"
    teacher_name = serializers.CharField(source="teacher.name_bn", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "role", "name", "name_bn", "sub", "sub_title",
                  "phone", "country", "guardian", "email", "monthly_fee",
                  "monthly_salary", "class_days", "can_fix_cross", "due_months",
                  "student_id", "teacher", "teacher_name"]

    def get_due_months(self, obj):
        # .values_list()-এর বদলে .all() ইটারেট — prefetch_related("due_months") এর ক্যাশ
        # ব্যবহার হয়, নইলে প্রতি ব্যবহারকারীতে আলাদা কোয়েরি হতো (N+1)
        return [d.month_label for d in obj.due_months.all()]


class TrialSerializer(serializers.ModelSerializer):
    """ট্রায়াল (সাময়িক অতিথি) অ্যাকাউন্ট — কেবল পরিচালক/এডমিন দেখেন।

    plain_password এখানে দেখানো হয় কারণ পরিচালককেই পরিবারের কাছে আইডি-পাসওয়ার্ড
    পাঠাতে হয় — ভর্তি গ্রহণের সময় ঠিক যেভাবে হয়, সেভাবেই।
    """
    name = serializers.CharField(source="name_bn", required=False)
    course_name = serializers.CharField(source="trial_course.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.name_bn", read_only=True)
    days_left = serializers.IntegerField(source="trial_days_left", read_only=True)
    expired = serializers.BooleanField(source="trial_expired", read_only=True)
    plain_password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "name", "name_bn", "guardian", "country",
                  "phone", "email", "trial_until", "trial_course", "course_name",
                  "teacher", "teacher_name", "trial_admission", "plain_password",
                  "days_left", "expired", "date_joined"]
        read_only_fields = ["username", "plain_password", "date_joined"]


class UserAdminSerializer(UserSerializer):
    """কেবল পরিচালকের জন্য — পাসওয়ার্ড সেট/রিসেট + দেখা-যায় কপি (কিছুই আড়াল নয়)"""
    password = serializers.CharField(write_only=True, required=False)
    plain_password = serializers.CharField(read_only=True)  # পরিচালক দেখতে পারবেন

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["password", "plain_password"]

    def validate_student_id(self, value):
        """পরিচালক নিজে আইডি বসালে সেটা যেন অন্য কারো সাথে মিলে না যায়"""
        value = (value or "").strip()
        if not value:
            return ""
        qs = User.objects.filter(student_id=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "এই স্টুডেন্ট আইডি অন্য একজনের জন্য ইতিমধ্যে ব্যবহৃত হয়েছে।"
            )
        return value

    def create(self, validated):
        from .utils import make_password_str
        pwd = validated.pop("password", None) or make_password_str(8)
        user = User(**validated)
        user.set_password(pwd)
        user.plain_password = pwd  # পরিচালকের দেখার জন্য দেখা-যায় কপি
        # নতুন স্টুডেন্টের আইডি না দেওয়া থাকলে অটো তৈরি হয়
        if user.role == "student" and not user.student_id:
            from .student_id import assign_student_id
            assign_student_id(user, User)
        user.save()
        return user

    def update(self, instance, validated):
        pwd = validated.pop("password", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
            instance.plain_password = pwd  # নতুন পাসওয়ার্ড → দেখা-যায় কপিও আপডেট
        # রোল বদলে স্টুডেন্ট হলে (বা আগে আইডি না থাকলে) তখনই তৈরি করে দিই
        if instance.role == "student" and not instance.student_id:
            from .student_id import assign_student_id
            assign_student_id(instance, User)
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
    covered = serializers.SerializerMethodField()
    marked_at = serializers.SerializerMethodField()

    class Meta:
        model = LectureTopic
        fields = ["id", "syllabus_item", "text", "content", "order",
                  "section", "covered", "marked_at"]

    def _row(self, obj):
        """যে শিক্ষার্থীর জন্য দেখা হচ্ছে তার নিজের রেকর্ড (থাকলে)।"""
        sid = self.context.get("student_id")
        if sid:
            # prefetch করা coverages থেকেই পড়ি — প্রতি টপিকে আলাদা কোয়েরি হয় না
            for c in obj.coverages.all():
                if c.student_id == sid:
                    return c
        return None

    def get_covered(self, obj):
        """যে শিক্ষার্থীর জন্য দেখা হচ্ছে তার নিজের টিক।

        student_id না থাকলে (যেমন পরিচালক এখনো কাউকে বাছেননি) পুরনো
        সবার-জন্য-একটাই মানটাই ফেরত যায়। কারও নিজস্ব রেকর্ড না থাকলেও
        তাই — এতে আগের হিসাব হারায় না।
        """
        row = self._row(obj)
        return row.covered if row else obj.covered

    def get_marked_at(self, obj):
        """কখন টিকটা পড়েছে — "আজকের / বিগত" ভাগ করতে লাগে।

        Asia/Dhaka অনুযায়ী তারিখ (YYYY-MM-DD)। কখনো টিক না পড়ে থাকলে null।
        """
        row = self._row(obj)
        at = row.marked_at if row else obj.marked_at
        return timezone.localtime(at).date().isoformat() if at else None


class LessonSectionSerializer(serializers.ModelSerializer):
    """হেডিং ও তার নিচের টপিকগুলো।

    টপিকগুলো নেস্টেড করে পাঠানো হয় — ফ্রন্টএন্ডে আলাদা করে সাজাতে হয় না,
    আর প্রতি হেডিংয়ে আলাদা কল করারও দরকার পড়ে না।
    """
    topics = serializers.SerializerMethodField()

    class Meta:
        model = LessonSection
        fields = ["id", "course", "name", "order", "is_trial", "topics"]

    def get_topics(self, obj):
        # prefetch করা topics থেকেই — প্রতি হেডিংয়ে আলাদা কোয়েরি হয় না
        rows = sorted(obj.topics.all(), key=lambda t: (t.order, t.id))
        return LectureTopicSerializer(rows, many=True, context=self.context).data


class LectureSerializer(serializers.ModelSerializer):
    topics = LectureTopicSerializer(many=True, read_only=True)
    # পুরনো পথ — সিলেবাস থেকে টপিক বাছাই। ফ্রন্টএন্ড আর ব্যবহার করে না, তবু
    # রেখে দেওয়া হলো যাতে পুরনো কোনো ক্লায়েন্ট/স্ক্রিপ্ট হঠাৎ ভেঙে না পড়ে।
    syllabus_item_ids = serializers.ListField(child=serializers.IntegerField(),
                                              write_only=True, required=False)
    # নতুন পথ — পরিচালকের নিজের লেখা টগল: [{text, content}, ...]
    topic_blocks = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Lecture
        fields = ["id", "course", "no", "title", "date", "topics",
                  "syllabus_item_ids", "topic_blocks"]
        # শিরোনামের ঘরটা ফর্ম থেকে তুলে দেওয়া হয়েছে — না দিলে "দারস ৫"
        # ধাঁচে নিজে থেকেই বসে যায় (নিচে _fill_title)
        extra_kwargs = {"no": {"required": False},
                        "title": {"required": False, "allow_blank": True}}

    @staticmethod
    def _fill_title(validated):
        if not (validated.get("title") or "").strip():
            validated["title"] = f"দারস {validated.get('no') or ''}".strip()
        return validated

    def validate_topic_blocks(self, v):
        if len(v) > 100:
            raise serializers.ValidationError("একটি দারসে সর্বোচ্চ ১০০টি টপিক রাখা যাবে")
        out = []
        for b in v:
            if not isinstance(b, dict):
                raise serializers.ValidationError("প্রতিটি টপিক একটি অবজেক্ট হতে হবে")
            text = str(b.get("text") or "").strip()[:300]
            if not text:
                continue  # শিরোনামহীন টগল রাখার মানে নেই
            # ⚠️ ভেতরের লেখা HTML হিসেবে সংরক্ষিত হয় ও পর্দায় HTML হিসেবেই
            # দেখানো হয় — তাই ঢোকার মুখেই ছেঁকে নিই। অনুমোদিত-তালিকায় নেই
            # এমন সব ট্যাগ/অ্যাট্রিবিউট বাদ যায় (safe_html.clean_html)।
            out.append({
                "id": b.get("id"),
                "text": text,
                "content": clean_html(str(b.get("content") or "")[:100000]),
            })
        return out

    def create(self, validated):
        blocks = validated.pop("topic_blocks", None)
        ids = validated.pop("syllabus_item_ids", [])
        if blocks is not None:
            if not validated.get("no"):
                validated["no"] = Lecture.objects.filter(
                    course=validated["course"]).count() + 1
            lec = Lecture.objects.create(**self._fill_title(validated))
            for i, b in enumerate(blocks):
                LectureTopic.objects.create(
                    lecture=lec, text=b["text"], content=b["content"], order=i)
            return lec
        # দারস-নং দেওয়া না থাকলে স্বয়ংক্রিয়; দেওয়া থাকলে তা-ই ব্যবহার
        if not validated.get("no"):
            validated["no"] = Lecture.objects.filter(course=validated["course"]).count() + 1
        lec = Lecture.objects.create(**validated)
        for sid in ids:  # সিলেবাস থেকে টপিক সিলেকশন
            si = SyllabusItem.objects.get(pk=sid, course=lec.course)
            LectureTopic.objects.create(lecture=lec, syllabus_item=si, text=si.label)
        return lec

    def update(self, instance, validated):
        blocks = validated.pop("topic_blocks", None)
        ids = validated.pop("syllabus_item_ids", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if blocks is not None:
            # আইডি মিলিয়ে পুরনো টগলই হালনাগাদ করি — নতুন করে বানাই না।
            # কারণ টপিক নতুন করে বানালে তার কভার-স্ট্যাটাস (✔/✘) হারিয়ে যেত।
            existing = {t.id: t for t in instance.topics.all()}
            kept = set()
            for i, b in enumerate(blocks):
                t = existing.get(b.get("id"))
                if t:
                    t.text, t.content, t.order = b["text"], b["content"], i
                    t.save(update_fields=["text", "content", "order"])
                    kept.add(t.id)
                else:
                    LectureTopic.objects.create(
                        lecture=instance, text=b["text"],
                        content=b["content"], order=i)
            for tid, t in existing.items():
                if tid not in kept:
                    t.delete()  # পরিচালক নিজে সরিয়ে দিয়েছেন
            return instance
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
    student_schedules = serializers.SerializerMethodField()

    class Meta:
        model = Routine
        fields = "__all__"

    def get_student_names(self, obj):
        # .values_list() prefetch_related-এর ক্যাশ এড়িয়ে প্রতিবার নতুন কোয়েরি করত (N+1)।
        # .all() ইটারেট করলে queryset-এ prefetch করা students-ই ব্যবহার হয় — বাড়তি কোয়েরি নেই।
        return [s.name_bn for s in obj.students.all()]

    def get_student_schedules(self, obj):
        # .all() ইটারেট করলে queryset-এ prefetch করা student_schedules-ই ব্যবহার হয় (N+1 এড়ায়)
        return [
            {"student": s.student_id, "days": s.days, "time": s.time.strftime("%H:%M") if s.time else None}
            for s in obj.student_schedules.all()
        ]


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
    rejoin_active = serializers.SerializerMethodField()

    class Meta:
        model = ClassSession
        fields = "__all__"

    def get_student_names(self, obj):
        # .values_list()-এর বদলে .all() ইটারেট — prefetch_related-এর ক্যাশ ব্যবহার হয় (N+1 নেই)
        return [s.name_bn for s in obj.students.all()]

    def get_rejoin_active(self, obj):
        """শিক্ষার্থীর কাছে ২য় (রিজয়েন) লিংক খোলা হয়েছে কিনা।

        এটা কেবল তখনই সত্য হয় যখন উস্তাদ নিজে "রিজয়েন" বাটনে ক্লিক করেন
        (অথবা পরিচালক ম্যানুয়ালি চালু করেন)। আগে হাজিরা দেখে স্বয়ংক্রিয়ভাবে
        হিসাব হতো — কিন্তু সেই হিসাব প্রত্যেকের ব্রাউজারে আলাদা সময়ে হতো বলে
        একজন ১ম লিংকে আর আরেকজন ২য় লিংকে ঢুকে ভিন্ন মিটিংয়ে চলে যেতেন। এখন
        একজনই (উস্তাদ) সিদ্ধান্ত নেন, তাই দুজনের অমিল হওয়ার সুযোগ নেই।"""
        return obj.join_mode_override == "rejoin"


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
    # আগে email ঐচ্ছিক ছিল আর contact-এ যেকোনো টেক্সট (এমনকি "hhhdh"-এর মতো
    # অক্ষরও) গ্রহণযোগ্য ছিল — ফলে ফেক/স্প্যাম আবেদন জমা পড়ত। এখন সত্যিকারের
    # ইমেইল ফরম্যাট ও কমপক্ষে ৮ ডিজিটের ফোন নম্বর ছাড়া আবেদনই জমা হবে না।
    email = serializers.EmailField(required=True)

    class Meta:
        model = Admission
        fields = "__all__"
        read_only_fields = ["status", "forwarded_to_director", "created_student"]

    def validate_contact(self, value):
        digits = "".join(ch for ch in (value or "") if ch.isdigit())
        if len(digits) < 8:
            raise serializers.ValidationError(
                "সঠিক WhatsApp/ফোন নম্বর দিন (কমপক্ষে ৮ ডিজিট)।"
            )
        return value


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


class StudentRemarkSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.name_bn", read_only=True)

    class Meta:
        model = StudentRemark
        fields = ["id", "student", "teacher", "teacher_name", "text", "created_at"]
        read_only_fields = ["teacher"]


class CourseSyllabusSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSyllabusSheet
        fields = ["headers", "rows", "updated_at"]
        read_only_fields = ["updated_at"]

    def _clean(self, value, name):
        if not isinstance(value, list):
            raise serializers.ValidationError({name: "তালিকা হতে হবে"})
        return value

    def validate_headers(self, v):
        v = self._clean(v, "headers")
        if len(v) > 12:
            raise serializers.ValidationError("সর্বোচ্চ ১২টি কলাম রাখা যাবে")
        return [str(x)[:120] for x in v]

    def validate_rows(self, v):
        v = self._clean(v, "rows")
        if len(v) > 300:
            raise serializers.ValidationError("সর্বোচ্চ ৩০০টি সারি রাখা যাবে")
        out = []
        for r in v:
            if not isinstance(r, list):
                raise serializers.ValidationError("প্রতিটি সারি একটি তালিকা হতে হবে")
            out.append([str(c)[:2000] for c in r[:12]])
        return out


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


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ["id", "endpoint", "p256dh", "auth", "created_at"]


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
