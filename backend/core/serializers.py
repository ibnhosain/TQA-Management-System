"""TQA-MS — DRF Serializers (অ্যাপ: core)"""
from rest_framework import serializers
from django.utils import timezone
from .safe_html import clean_html
from .models import (User, AcademicBook, Course, SyllabusItem, Lecture, LectureTopic,
                     Routine, ClassSession, Attendance, Question, Assignment, Exam,
                     Submission, ExamResult, FeePayment, DueMonth, TeacherPayment,
                     SentReceipt, Admission, LeaveRequest, Rating, StudentRemark, Notice,
                     Notification, PushSubscription, WaMessage, LibraryBook,
                     CourseSyllabusSheet, LessonSection, TrialReport,
                     TrialScoreItem, Lesson, LessonStep, StepSlide,
                     LessonProgress)


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
                  "student_id", "teacher", "teacher_name",
                  # ট্রায়াল অতিথির নিজের পোর্টালে মেয়াদ ও কোর্স দেখাতে লাগে।
                  # অন্য সব ভূমিকায় ঘর দুটি খালি (null) যায়, তাই কারও কিছু বদলায় না।
                  "trial_until", "trial_course"]

    def get_due_months(self, obj):
        # .values_list()-এর বদলে .all() ইটারেট — prefetch_related("due_months") এর ক্যাশ
        # ব্যবহার হয়, নইলে প্রতি ব্যবহারকারীতে আলাদা কোয়েরি হতো (N+1)
        return [d.month_label for d in obj.due_months.all()]


# ═══════════ দারস স্ক্রিপ্ট ও উপস্থাপনা ═══════════
# ⚠️ এখানে দুটি সম্পূর্ণ আলাদা পথ রাখা হয়েছে, আর এটাই এই ব্যবস্থার
# নিরাপত্তার ভিত্তি:
#     উস্তাদের পথ  → LessonSerializer      (স্ক্রিপ্টসহ সব)
#     পর্দার পথ    → StageSerializer       (কেবল শিক্ষার্থী যা দেখবেন)
# উপস্থাপনার এন্ডপয়েন্ট কখনোই প্রথমটি ব্যবহার করে না। উস্তাদের স্ক্রিপ্ট
# লুকানো হয় না — পাঠানোই হয় না।
class SlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepSlide
        fields = ["kind", "heading", "arabic", "arabic_locked", "translit",
                  "text", "image", "audio"]


def _slide_of(step):
    """ধাপের স্লাইড, না থাকলে None।

    OneToOne-এর উল্টো দিকটা না থাকলে Django AttributeError তোলে, তাই
    getattr-এর ডিফল্টই যথেষ্ট — আলাদা try লাগে না।
    """
    return getattr(step, "slide", None)


class LessonStepSerializer(serializers.ModelSerializer):
    """উস্তাদের জন্য — পুরো স্ক্রিপ্ট, সাথে পর্দার স্লাইডটিও।"""
    slide = SlideSerializer(required=False)

    class Meta:
        model = LessonStep
        fields = ["id", "lesson", "order", "section", "teacher_says",
                  "teacher_does", "student_does", "expected", "correction",
                  "note", "seconds", "topic", "is_active", "slide"]

    def to_representation(self, obj):
        d = super().to_representation(obj)
        # স্লাইড না থাকলে DRF-এর নিজের পাঠ ভেঙে পড়ত — তাই নিজেই বসাই
        sl = _slide_of(obj)
        d["slide"] = SlideSerializer(sl).data if sl else None
        return d

    def _save_slide(self, step, data):
        """ধাপের সাথে তার স্লাইডটিও রাখা।

        ⚠️ যাচাই করা আরবি সুরক্ষিত — `arabic_locked` চালু থাকা অবস্থায়
        আরবির বদল চুপচাপ উপেক্ষা করা হয়। পরিচালক আগে তালা খুলবেন
        (arabic_locked=false পাঠিয়ে), তারপর বদলাতে পারবেন। এতে সম্পাদনার
        সময় ভুলবশত একটি যের-যবরও নড়ে যেতে পারে না।
        """
        sl = _slide_of(step)
        if sl is None:
            StepSlide.objects.create(step=step, **(data or {}))
            return
        if data is None:
            return
        data = dict(data)
        if sl.arabic_locked and data.get("arabic_locked", True):
            data.pop("arabic", None)
        for k, v in data.items():
            setattr(sl, k, v)
        sl.save()

    def create(self, validated):
        slide = validated.pop("slide", None) or {}
        # নতুন ধাপ সবসময় দারসের শেষে বসে, আলাদা করে ক্রম দিতে হয় না
        if "order" not in validated and validated.get("lesson"):
            last = LessonStep.objects.filter(
                lesson=validated["lesson"]).order_by("-order").first()
            validated["order"] = (last.order + 1) if last else 0
        step = super().create(validated)
        self._save_slide(step, slide)
        step.refresh_from_db()
        return step

    def update(self, instance, validated):
        slide = validated.pop("slide", None)
        step = super().update(instance, validated)
        if slide is not None:
            self._save_slide(step, slide)
        return step


class LessonSerializer(serializers.ModelSerializer):
    """উস্তাদের জন্য — দারস ও তার সব ধাপ।"""
    course_name = serializers.CharField(source="course.name", read_only=True)
    steps = serializers.SerializerMethodField()
    step_count = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "course", "course_name", "title", "title_ar", "kind",
                  "age_from", "age_to", "duration_min", "objectives", "status",
                  "order", "step_count", "steps"]

    def get_steps(self, obj):
        # তালিকা দেখানোর সময় ধাপগুলো পাঠানো হয় না — শুধু একটি দারস খুললেই
        if not self.context.get("with_steps"):
            return None
        rows = [x for x in obj.steps.all() if x.is_active]
        return LessonStepSerializer(rows, many=True, context=self.context).data

    def get_step_count(self, obj):
        return len([x for x in obj.steps.all() if x.is_active])

    def validate_objectives(self, v):
        # এই লেখাটি HTML হিসেবেই উস্তাদের পর্দায় বসানো হয়, তাই কোডবেসের
        # বাকি রিচ-টেক্সটের মতো এখানেও অনুমোদিত ট্যাগ ছাড়া সব ছেঁকে ফেলি
        return clean_html(str(v or "")[:100000])


class StageStepSerializer(serializers.ModelSerializer):
    """⚠️ শিক্ষার্থীর পর্দার জন্য — কেবল ক্রম ও স্লাইড।

    এখানে teacher_says/teacher_does/expected/correction/note-এর একটিও নেই,
    আর কখনো যোগ করাও যাবে না।
    """
    slide = serializers.SerializerMethodField()

    class Meta:
        model = LessonStep
        fields = ["id", "order", "slide"]

    def get_slide(self, obj):
        sl = _slide_of(obj)
        return SlideSerializer(sl).data if sl else None


class StageSerializer(serializers.ModelSerializer):
    """⚠️ উপস্থাপনা উইন্ডো যা পায় — দারসের নাম আর স্লাইডগুলো, ব্যস।"""
    steps = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "title_ar", "steps"]

    def get_steps(self, obj):
        rows = [x for x in obj.steps.all() if x.is_active]
        return StageStepSerializer(rows, many=True).data


class LessonProgressSerializer(serializers.ModelSerializer):
    """কোন শিক্ষার্থীর কোন দারস কতটা হয়েছে।

    ⚠️ এখানে দারসের কোনো লেখা নেই — কেবল নাম, অবস্থা ও উস্তাদের মন্তব্য।
    শিক্ষার্থী নিজের অগ্রগতি দেখতে পান, কিন্তু স্ক্রিপ্ট নয়।
    """
    student_name = serializers.CharField(source="student.name_bn",
                                         read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    course = serializers.IntegerField(source="lesson.course_id", read_only=True)

    class Meta:
        model = LessonProgress
        fields = ["id", "student", "student_name", "lesson", "lesson_title",
                  "course", "status", "times_taught", "last_taught",
                  "last_step", "note", "updated_at"]
        # কয় দিন পড়ানো হলো তা সার্ভারই গোনে — হাতে বসানো যায় না, নইলে
        # ভুল করে একই দিনে কয়েকবার সংরক্ষণ করলেই সংখ্যাটা বেড়ে যেত
        read_only_fields = ["times_taught", "last_taught", "updated_at"]


class TrialScoreItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrialScoreItem
        fields = ["id", "key", "label_bn", "label_en", "order"]
        # key সার্ভারই বানায় ও আর বদলায় না — পুরনো রিপোর্টের নম্বর
        # এই key ধরেই রাখা, তাই বদলালে সেগুলো হারিয়ে যেত
        read_only_fields = ["key"]


class TrialReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name_bn", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)
    guardian = serializers.CharField(source="student.guardian", read_only=True)
    phone = serializers.CharField(source="student.phone", read_only=True)
    course_name = serializers.CharField(source="student.trial_course.name", read_only=True)
    teacher_name = serializers.CharField(source="student.teacher.name_bn", read_only=True)
    written_by = serializers.CharField(source="created_by.name_bn", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.name_bn", read_only=True)
    recommended_course_name = serializers.CharField(
        source="recommended_course.name", read_only=True)
    offer_teacher_name = serializers.CharField(
        source="offer_teacher.name_bn", read_only=True)

    class Meta:
        model = TrialReport
        fields = ["id", "student", "student_name", "student_username", "guardian",
                  "phone", "course_name", "teacher_name", "scores", "strengths",
                  "work_on", "advice", "recommended_course",
                  "recommended_course_name", "recommended_level", "written_by",
                  "reviewed_by_name", "created_at", "updated_at", "reviewed_at",
                  "sent_at", "offer_teacher", "offer_teacher_name",
                  "offer_schedule", "offer_fee", "offered_at", "accepted_at"]
        # এই সময়ের ঘরগুলো কেবল যাচাই/পাঠানো/প্রস্তাব/গ্রহণের অ্যাকশন দিয়েই
        # বসে — সরাসরি লেখা যায় না, তাই তারিখগুলো কখনো বানানো হয় না
        read_only_fields = ["created_at", "updated_at", "reviewed_at",
                            "sent_at", "offered_at", "accepted_at"]


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
    topics = serializers.SerializerMethodField()
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

    def get_topics(self, obj):
        """⚠️ ট্রায়াল পরিকল্পনার টপিক এখানে আসে না।

        দারস (Lecture) এখন কেবল লুকানো ধারক — নিয়মিত ও ট্রায়াল দুই
        পরিকল্পনার টপিকই একই ধারকের নিচে বসে। এই পুরনো পথটি বরাবরই নিয়মিত
        পরিকল্পনার, তাই ট্রায়ালের টপিক ছেঁকে বাদ দেওয়া হয় — নইলে
        শিক্ষার্থী বা উস্তাদ এখান দিয়ে ট্রায়ালের পরিকল্পনা দেখে ফেলতেন।
        """
        rows = [
            t for t in obj.topics.all()
            if not (t.section_id and t.section and t.section.is_trial)
        ]
        return LectureTopicSerializer(rows, many=True, context=self.context).data

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
