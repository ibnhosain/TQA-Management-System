"""
তারবিয়াতুল কুরআন একাডেমি ম্যানেজমেন্ট সিস্টেম — Django মডেল
ফ্রন্টএন্ড (tqa-management-system.jsx) এর প্রতিটি ডেটা-কাঠামোর সাথে ১:১ ম্যাপ করা।
অ্যাপের নাম ধরা হয়েছে: core
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


# ─────────────────────────── ব্যবহারকারী (৪ রোল) ───────────────────────────
class User(AbstractUser):
    class Role(models.TextChoices):
        DIRECTOR = "director", "পরিচালক"
        ADMIN = "admin", "এডমিন"
        TEACHER = "teacher", "উস্তাদ/উস্তাদা"
        STUDENT = "student", "স্টুডেন্ট"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    name_bn = models.CharField("নাম (বাংলা)", max_length=120)
    sub_title = models.CharField("পরিচিতি/বিষয়", max_length=120, blank=True)
    phone = models.CharField("WhatsApp নম্বর (কান্ট্রি কোডসহ)", max_length=20, blank=True)
    country = models.CharField(max_length=60, blank=True)
    guardian = models.CharField("অভিভাবকের নাম", max_length=120, blank=True)
    monthly_fee = models.PositiveIntegerField(default=0)      # স্টুডেন্ট হলে
    monthly_salary = models.PositiveIntegerField(default=0)   # টিচার হলে
    can_fix_cross = models.BooleanField(default=False)  # পরিচালকের দেওয়া লাল-ক্রস ঠিক করার অনুমতি

    def __str__(self):
        return f"{self.name_bn} ({self.get_role_display()})"


# ─────────────────────────── একাডেমিক বই ও কোর্স ───────────────────────────
class AcademicBook(models.Model):
    name = models.CharField(max_length=200)
    file = models.CharField(max_length=500, blank=True)  # Cloudinary URL বা local path
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=150)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                limit_choices_to={"role": "teacher"}, related_name="courses_taught")
    students = models.ManyToManyField(User, blank=True, related_name="courses_enrolled",
                                      limit_choices_to={"role": "student"})
    books = models.ManyToManyField(AcademicBook, blank=True)  # সর্বোচ্চ ৬টি — serializer-এ যাচাই
    color = models.CharField(max_length=9, default="#1a5c3a")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ─────────────────── সিলেবাস (কোর্স→বই→লেসন→পৃষ্ঠা→লাইন→মন্তব্য) ───────────────────
class SyllabusItem(models.Model):
    # দৈনিক পাঠ পরিকল্পনা / সিলেবাসের ৫টি বিভাগ
    class Category(models.TextChoices):
        SURAH  = "memorized_surah",  "মুখস্থ সূরা"
        HADITH = "memorized_hadith", "মুখস্থ হাদিস"
        QIRAT  = "qirat",            "কিরাত"
        DUA    = "dua_masala",       "দুআ/মাসআলা"
        MORAL  = "moral_story",      "নৈতিক শিক্ষা/হাদিসের গল্প"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="syllabus")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.QIRAT)
    book = models.ForeignKey(AcademicBook, on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.CharField(max_length=300)  # মূল বিষয়বস্তু (যেমন: সূরা ইখলাস / কায়দা — লেসন ৪)
    pages = models.CharField(max_length=50, blank=True)
    lines = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "id"]

    @property
    def label(self):  # ফ্রন্টএন্ডের sylLabel() এর সমতুল্য
        prefix = f"{self.book.name} — " if self.book else ""
        if self.category == self.Category.QIRAT:
            parts = [prefix, self.lesson]
            if self.pages: parts.append(f", পৃষ্ঠা: {self.pages}")
            if self.lines: parts.append(f", লাইন: {self.lines}")
            return "".join(parts)
        return f"{prefix}{self.lesson}"


# ─────────────────────────── লেকচার প্ল্যান ও টপিক কভারেজ ───────────────────────────
class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lectures")
    no = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["course", "no"]
        unique_together = [("course", "no")]


class LectureTopic(models.Model):
    class Covered(models.TextChoices):
        PENDING = "pending", "বাকি"
        COVERED = "covered", "কভার ✔"
        MISSED = "missed", "বাদ ✘"

    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name="topics")
    syllabus_item = models.ForeignKey(SyllabusItem, on_delete=models.SET_NULL, null=True)
    text = models.CharField(max_length=300)  # sylLabel স্ন্যাপশট
    covered = models.CharField(max_length=8, choices=Covered.choices, default=Covered.PENDING)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(null=True, blank=True)


# ─────────────────────────── রুটিন ও ক্লাস সেশন ───────────────────────────
class Routine(models.Model):
    """স্থায়ী সাপ্তাহিক রুটিন — কে, কার কাছে, কোন বারে, কোন সময়ে"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="routines",
                                limit_choices_to={"role": "teacher"})
    students = models.ManyToManyField(User, related_name="student_routines")
    days = models.JSONField(default=list)  # [0..6] — JS getDay() ক্রম (০=রবিবার)
    time = models.TimeField()
    duration_min = models.PositiveIntegerField(default=60)
    zoom_link = models.URLField()
    is_active = models.BooleanField(default=True)


class ClassSession(models.Model):
    class Status(models.TextChoices):
        UPCOMING = "upcoming", "আসন্ন"
        DONE = "done", "সম্পন্ন"
        POSTPONED = "postponed", "স্থগিত"

    KINDS = [("regular", "নিয়মিত ক্লাস"), ("makeup", "মেকআপ ক্লাস"), ("support", "সাপোর্ট ক্লাস"),
             ("recovery", "রিকভারি ক্লাস"), ("trial", "ট্রায়াল ক্লাস"), ("other", "অন্যান্য")]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sessions_taught")
    students = models.ManyToManyField(User, related_name="sessions_enrolled")
    routine = models.ForeignKey(Routine, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    duration_min = models.PositiveIntegerField(default=60)
    zoom_link = models.URLField()
    lecture_no = models.PositiveIntegerField(default=1)
    kind = models.CharField(max_length=10, choices=KINDS, default="regular")
    guardian_requirement = models.TextField(blank=True)  # অভিভাবকের রিকোয়ারমেন্ট
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)
    reminder_sent = models.BooleanField(default=False)  # ৫-মিনিট WhatsApp রিমাইন্ডার (Celery টাস্ক)

    class Meta:
        ordering = ["date", "time"]


class Attendance(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="attendance")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    minutes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("session", "user")]

    @property
    def present(self):  # ৪০-মিনিট নিয়ম
        return self.minutes >= 40


# ─────────────────────────── অ্যাসাইনমেন্ট ও পরীক্ষা ───────────────────────────
class Question(models.Model):
    """অ্যাসাইনমেন্ট/পরীক্ষা — দুটোর প্রশ্নই এখানে"""
    class QType(models.TextChoices):
        TEXT = "text", "লিখিত"
        MCQ = "mcq", "MCQ"

    text = models.CharField(max_length=400)
    qtype = models.CharField(max_length=4, choices=QType.choices, default=QType.TEXT)
    options = models.JSONField(default=list, blank=True)   # MCQ: ৪ অপশন
    correct_index = models.PositiveIntegerField(null=True, blank=True)
    assignment = models.ForeignKey("Assignment", on_delete=models.CASCADE, null=True, blank=True, related_name="questions")
    exam = models.ForeignKey("Exam", on_delete=models.CASCADE, null=True, blank=True, related_name="questions")


class Assignment(models.Model):
    MODES = [("form", "ফরম"), ("photo", "ছবি/ফাইল")]
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    mode = models.CharField(max_length=5, choices=MODES, default="form")
    total_marks = models.PositiveIntegerField(default=10)


class Exam(models.Model):
    TYPES = [("mcq", "মাসিক MCQ"), ("live", "লাইভ টেস্ট")]
    MODES = [("form", "ফরম"), ("photo", "খাতার ছবি")]
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=4, choices=TYPES, default="mcq")
    mode = models.CharField(max_length=5, choices=MODES, default="form")
    date = models.DateField()
    total_marks = models.PositiveIntegerField(default=30)


class Submission(models.Model):
    """অ্যাসাইনমেন্ট বা পরীক্ষার জমা — মার্ক দিলেই স্টুডেন্ট পোর্টালে"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True, blank=True, related_name="submissions")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, null=True, blank=True, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    answers = models.JSONField(null=True, blank=True)       # {question_id: উত্তর}
    file = models.FileField(upload_to="submissions/", null=True, blank=True)
    note = models.CharField(max_length=300, blank=True)
    mark = models.PositiveIntegerField(null=True, blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="uniq_assignment_sub",
                                    condition=models.Q(assignment__isnull=False)),
            models.UniqueConstraint(fields=["exam", "student"], name="uniq_exam_sub",
                                    condition=models.Q(exam__isnull=False)),
        ]


class ExamResult(models.Model):
    """লাইভ টেস্টের মতো সরাসরি মার্ক এন্ট্রি"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    mark = models.PositiveIntegerField()

    class Meta:
        unique_together = [("exam", "student")]


# ─────────────────────────── আর্থিক: ফি, বেতন, রিসিট ───────────────────────────
class FeePayment(models.Model):
    METHODS = [("bkash", "বিকাশ"), ("nagad", "নগদ"), ("bank", "ব্যাংক ট্রান্সফার"),
               ("cash", "নগদ গ্রহণ (অফিস)"), ("other", "অন্যান্য")]
    STATUS = [("pending", "যাচাইয়ের অপেক্ষায়"), ("verified", "ভেরিফাইড")]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fee_payments")
    amount = models.PositiveIntegerField()
    month_label = models.CharField(max_length=40)  # "জুন ২০২৬"
    method = models.CharField(max_length=10, choices=METHODS)
    trx_id = models.CharField(max_length=60, blank=True)
    screenshot = models.ImageField(upload_to="payment_shots/", null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    paid_at = models.DateField(auto_now_add=True)


class DueMonth(models.Model):
    """স্টুডেন্ট/টিচারের বকেয়া মাস — Celery মাসিক টাস্কে অটো তৈরি হবে"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="due_months")
    month_label = models.CharField(max_length=40)

    class Meta:
        unique_together = [("user", "month_label")]


class TeacherPayment(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="salary_payments")
    amount = models.PositiveIntegerField()
    month_label = models.CharField(max_length=40)
    method = models.CharField(max_length=30, default="ব্যাংক")
    paid_at = models.DateField(auto_now_add=True)


class SentReceipt(models.Model):
    """পোর্টালে পাঠানো রিসিট/ভাউচার"""
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receipts")
    kind = models.CharField(max_length=60)
    month_label = models.CharField(max_length=60)
    amount = models.PositiveIntegerField()
    method = models.CharField(max_length=60)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    sent_at = models.DateField(auto_now_add=True)


# ─────────────────────────── ভর্তি, ছুটি, মূল্যায়ন ───────────────────────────
class Admission(models.Model):
    """ওয়েবসাইট থেকে আসা আবেদন — ভর্তি / ফ্রি ট্রায়াল / যোগাযোগ বার্তা"""
    STATUS = [("pending", "অপেক্ষমাণ"), ("accepted", "গৃহীত"), ("rejected", "বাতিল")]
    KIND = [("admission", "ভর্তি"), ("enroll", "ভর্তি"), ("trial", "ফ্রি ট্রায়াল"), ("contact", "যোগাযোগ")]
    kind = models.CharField(max_length=10, choices=KIND, default="admission")
    name = models.CharField(max_length=120)
    age = models.PositiveIntegerField(null=True, blank=True)
    guardian = models.CharField(max_length=120, blank=True, default="")
    country = models.CharField(max_length=60, blank=True)
    contact = models.CharField(max_length=80)            # WhatsApp নম্বর / ইমেইল
    email = models.CharField(max_length=120, blank=True)
    course_name = models.CharField(max_length=150, blank=True)
    preferred_time = models.CharField(max_length=120, blank=True)
    message = models.TextField(blank=True)
    # ভর্তির পেমেন্ট তথ্য ($৫ এককালীন + প্রথম মাস অগ্রিম):
    payment_method = models.CharField(max_length=30, blank=True)   # bKash/Nagad/Bank/...
    trx_id = models.CharField(max_length=80, blank=True)
    screenshot = models.FileField(upload_to="admission_proofs/", null=True, blank=True)
    # ট্রায়াল/যোগাযোগে এডমিন WhatsApp রিপ্লাই পাঠিয়েছেন কিনা:
    replied = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    forwarded_to_director = models.BooleanField(default=False)  # এডমিন → পরিচালক
    created_student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    applied_at = models.DateField(auto_now_add=True)


class LeaveRequest(models.Model):
    STATUS = [("pending_admin", "এডমিনের কাছে"), ("forwarded", "পরিচালকের কাছে"),
              ("approved", "মঞ্জুর"), ("rejected", "নামঞ্জুর")]
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leaves")
    leave_type = models.CharField(max_length=40)  # অসুস্থতা/সফর/...
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS, default="pending_admin")
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    applied_at = models.DateField(auto_now_add=True)


class Rating(models.Model):
    """ক্লাস শেষে স্টুডেন্টের মূল্যায়ন — উস্তাদ শুধু গড় দেখেন, পরিচয় কেবল এডমিন/পরিচালক"""
    session = models.ForeignKey(ClassSession, on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings_received")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings_given")
    stars = models.PositiveSmallIntegerField()  # ১–৫
    comment = models.TextField(blank=True)
    rated_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = [("session", "student")]


# ─────────────────────────── নোটিশ, নোটিফিকেশন, WhatsApp ───────────────────────────
class Notice(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Notification(models.Model):
    text = models.TextField()
    recipients = models.ManyToManyField(User, related_name="notifications")
    read_by = models.ManyToManyField(User, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class WaMessage(models.Model):
    """WhatsApp আউটবক্স — Celery টাস্ক Twilio/Meta API দিয়ে পাঠাবে"""
    REASONS = [("reminder", "৫ মিনিট রিমাইন্ডার"), ("postpone", "ক্লাস স্থগিত"), ("fee", "ফি রিমাইন্ডার")]
    STATUS = [("queued", "অপেক্ষমাণ"), ("sending", "যাচ্ছে"), ("sent", "পাঠানো হয়েছে"), ("failed", "ব্যর্থ")]
    to_name = models.CharField(max_length=120)
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20)
    text = models.TextField()
    reason = models.CharField(max_length=10, choices=REASONS)
    status = models.CharField(max_length=8, choices=STATUS, default="queued")
    provider_ref = models.CharField(max_length=120, blank=True)  # Twilio SID / Meta msg id
    created_at = models.DateTimeField(auto_now_add=True)


# ─────────────────────────── লাইব্রেরি বই (বাহ্যিক লিংক) ───────────────────────────
class LibraryBook(models.Model):
    """ওয়েবসাইট লাইব্রেরি — ডাউনলোড লিংকসহ পাঠ্যপুস্তক ও সহায়ক বই"""
    cls = models.CharField("শ্রেণি / ক্যাটাগরি", max_length=100)
    title = models.CharField("বইয়ের নাম", max_length=200)
    author = models.CharField("লেখক", max_length=150, blank=True)
    link = models.URLField("ডাউনলোড লিংক", blank=True, default="#")
    file_type = models.CharField("ফরম্যাট", max_length=20, default="PDF")
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["cls", "title"]

    def __str__(self):
        return f"{self.cls} — {self.title}"
