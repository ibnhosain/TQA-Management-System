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
        # সাময়িক অতিথি — ভর্তি হওয়ার আগে কয়েক দিনের জন্য। ইচ্ছা করেই আলাদা
        # ভূমিকা: ফি, বকেয়া, বেতন, মাসিক রিপোর্ট, স্টুডেন্ট তালিকা — সব
        # জায়গার কোয়েরি role="student" ধরে চলে, তাই ট্রায়াল সেখানে
        # আপনাআপনিই ঢোকে না, আলাদা করে কিছু বাদ দিতে হয় না।
        TRIAL = "trial", "ট্রায়াল শিক্ষার্থী"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    name_bn = models.CharField("নাম (বাংলা)", max_length=120)
    sub_title = models.CharField("পরিচিতি/বিষয়", max_length=120, blank=True)
    phone = models.CharField("WhatsApp নম্বর (কান্ট্রি কোডসহ)", max_length=20, blank=True)
    country = models.CharField(max_length=60, blank=True)
    guardian = models.CharField("অভিভাবকের নাম", max_length=120, blank=True)
    # স্টুডেন্ট আইডি — নাম+বাবার নাম+দেশ+সিরিয়াল মিলিয়ে অটো তৈরি (SH-LC-US-007),
    # পরিচালক চাইলে নিজে বদলেও দিতে পারেন। কেবল স্টুডেন্টদের জন্য প্রযোজ্য।
    student_id = models.CharField("স্টুডেন্ট আইডি", max_length=32, blank=True,
                                  default="", db_index=True)
    # শিক্ষার্থী কার কাছে পড়ে — নিজস্ব উস্তাদ।
    # আগে উস্তাদ বাঁধা ছিল কেবল কোর্সের সাথে (Course.teacher), তাই এক
    # শিক্ষার্থীর উস্তাদ বদলাতে গেলে ওই কোর্সের সবারই বদলে যেত। এখন প্রতিটি
    # শিক্ষার্থীর আলাদা উস্তাদ থাকতে পারে, আর একই কোর্সে একাধিক উস্তাদও।
    # ⚠️ Course.teacher মোছা হয়নি — খালি থাকলে কোর্সের উস্তাদই প্রযোজ্য ধরা
    # হয়, তাই পুরনো কোনো হিসাব হারায় না।
    teacher = models.ForeignKey("self", on_delete=models.SET_NULL, null=True,
                                blank=True, limit_choices_to={"role": "teacher"},
                                related_name="my_students",
                                verbose_name="কার কাছে পড়ে")
    monthly_fee = models.PositiveIntegerField(default=0)      # স্টুডেন্ট হলে
    monthly_salary = models.PositiveIntegerField(default=0)   # টিচার হলে
    # স্টুডেন্ট সপ্তাহে কোন কোন বার পড়বে — [0..6] JS getDay() ক্রম (০=রবিবার); ফি ও রুটিনে ব্যবহৃত
    class_days = models.JSONField(default=list, blank=True)
    # পরিচালকের জন্য পাসওয়ার্ডের দেখা-যায় কপি (কেবল director সিরিয়ালাইজারে ফেরত যায়)
    plain_password = models.CharField(max_length=128, blank=True, default="")
    can_fix_cross = models.BooleanField(default=False)  # পরিচালকের দেওয়া লাল-ক্রস ঠিক করার অনুমতি

    # ─────────── ট্রায়াল (সাময়িক অতিথি) — কেবল role="trial" হলে প্রযোজ্য ───────────
    # অন্য সব ভূমিকায় ঘরগুলো খালি পড়ে থাকে, কোনো প্রভাব নেই।
    trial_until = models.DateField(
        "ট্রায়ালের মেয়াদ", null=True, blank=True,
        help_text="এই তারিখ পর্যন্ত ট্রায়াল চলবে")
    # যে কোর্সের সিলেবাস, দারস পরিকল্পনা ও বই তিনি দেখতে পাবেন।
    # ⚠️ Course.students-এ যোগ করা হয় না — তাহলে কোর্সের শিক্ষার্থী তালিকায়
    # ট্রায়াল ঢুকে যেত। তাই আলাদা সংযোগ।
    trial_course = models.ForeignKey(
        "Course", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="trial_students", verbose_name="ট্রায়ালের কোর্স")
    # কোন আবেদন থেকে এসেছেন — পরে ভর্তিতে রূপান্তরের সময় কাজে লাগবে
    trial_admission = models.ForeignKey(
        "Admission", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="trial_users", verbose_name="যে আবেদন থেকে")

    @property
    def trial_expired(self):
        """মেয়াদ ফুরিয়েছে কিনা। তারিখ না দেওয়া থাকলে কখনো ফুরায় না।"""
        if self.role != "trial" or not self.trial_until:
            return False
        from django.utils import timezone
        return self.trial_until < timezone.localtime().date()

    @property
    def trial_days_left(self):
        """আজ ধরে আর কত দিন বাকি (আজ শেষ দিন হলে ০)। মেয়াদ না থাকলে None।"""
        if self.role != "trial" or not self.trial_until:
            return None
        from django.utils import timezone
        return (self.trial_until - timezone.localtime().date()).days

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
    books = models.ManyToManyField(AcademicBook, blank=True)  # সংখ্যায় কোনো সীমা নেই
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

    def __str__(self):
        return f"[{self.get_category_display()}] {self.label}"


class CourseSyllabusSheet(models.Model):
    """পরিচালকের নিজের হাতে লেখা কোর্স-সিলেবাসের টেবিল।

    ⚠️ উপরের SyllabusItem-এ কোনো হাত দেওয়া হয়নি — সেটা আগের মতোই আছে,
    কোনো তথ্য মোছেওনি। এই টেবিলটা সম্পূর্ণ আলাদাভাবে যোগ হলো।

    প্রতিটি কোর্সে একটাই শিট (OneToOne):
      headers — কলামের শিরোনাম, যেমন ["মুখস্থ সূরা", "কিরাত", …]
      rows    — প্রতিটি সারি ওই কলামগুলোর ঘরের লেখার তালিকা

    কেন ছক-বাঁধা কলাম নয়: পরিচালক নিজের ইচ্ছামতো কলাম যোগ/বাদ ও শিরোনাম
    বদলাতে পারবেন, তাই কলামগুলো আগে থেকে ঠিক করে রাখা যায় না।
    """
    course = models.OneToOneField(Course, on_delete=models.CASCADE,
                                  related_name="syllabus_sheet")
    headers = models.JSONField(default=list, blank=True)
    rows = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"সিলেবাস টেবিল — {self.course.name}"


# ─────────────────────────── লেকচার প্ল্যান ও টপিক কভারেজ ───────────────────────────
class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lectures")
    no = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["course", "no"]
        unique_together = [("course", "no")]


class LessonSection(models.Model):
    """দারস পরিকল্পনার হেডিং — সিলেবাসের বিষয় ধরে।

    যেমন: Memorized Surah, Memorized Hadith, Qirat, Dua, Masala,
    Moral Lesson, Hadith Story — আর পরিচালক ইচ্ছামতো নতুন নাম যোগ করতে
    বা পুরনো নাম বদলাতে পারেন।

    প্রতিটি হেডিংয়ের নিচে যত খুশি টপিক (টগল) থাকতে পারে। টপিক কভার হয়ে
    গেলেও নিজের হেডিংয়েই থাকে — জায়গা বদলায় না, কেবল রঙ বদলায়।
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name="lesson_sections")
    name = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)
    # এই হেডিংটি ট্রায়ালের পরিকল্পনার, নাকি নিয়মিত পরিকল্পনার।
    # একই কোর্সে দুটি আলাদা পরিকল্পনা পাশাপাশি থাকে — নিয়মিত শিক্ষার্থীরা
    # শুধু নিয়মিতটি দেখেন, ট্রায়াল অতিথিরা শুধু ট্রায়ালেরটি। কোনোটাই
    # অন্যটির টপিক বা কভারের টিক ছোঁয় না।
    # ⚠️ পুরনো সব হেডিং False হয়ে বসে, তাই বিদ্যমান পরিকল্পনা অবিকল আগের মতোই।
    is_trial = models.BooleanField("ট্রায়ালের পরিকল্পনা", default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.name} — {self.name}"


class LectureTopic(models.Model):
    class Covered(models.TextChoices):
        PENDING = "pending", "বাকি"
        COVERED = "covered", "কভার ✔"
        MISSED = "missed", "বাদ ✘"

    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name="topics")
    # পুরনো সিলেবাস-বাছাই ব্যবস্থার সূত্র — নতুন টপিকে খালি থাকে, কিন্তু আগে
    # তৈরি হওয়া টপিকগুলোর সংযোগ যেন না হারায় তাই ঘরটা রাখা হয়েছে
    syllabus_item = models.ForeignKey(SyllabusItem, on_delete=models.SET_NULL, null=True)
    text = models.CharField(max_length=300)  # টগলের শিরোনাম (আগে sylLabel স্ন্যাপশট ছিল)
    # কোন হেডিংয়ের নিচে। পুরনো টপিকে খালি থাকতে পারে — তখন "অন্যান্য"
    # হেডিংয়ে দেখানো হয়, যাতে একটাও চোখের আড়ালে না যায়।
    section = models.ForeignKey(LessonSection, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="topics")
    # টগলের ভেতরের লেখা — কী পড়ানো হবে। খালি হতে পারে (পুরনো টপিকগুলোর মতো)।
    order = models.PositiveIntegerField(default=0)  # হেডিংয়ের ভেতরে টগলের ক্রম
    content = models.TextField(blank=True, default="")
    covered = models.CharField(max_length=8, choices=Covered.choices, default=Covered.PENDING)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "id"]


class TopicCoverage(models.Model):
    """কোন শিক্ষার্থীর জন্য কোন টপিক কভার হয়েছে।

    আগে LectureTopic.covered একটাই মান ছিল — অর্থাৎ উস্তাদ টিক দিলে সেটা
    কোর্সের সব শিক্ষার্থীর জন্যই বসে যেত। এখন প্রতিটি শিক্ষার্থীর হিসাব
    আলাদা: এক ছাত্রের জন্য টিক দিলে কেবল তার পোর্টালেই দেখায়।

    ⚠️ পুরনো LectureTopic.covered ঘরটা মোছা হয়নি। কোনো শিক্ষার্থীর নিজস্ব
    রেকর্ড না থাকলে ওই পুরনো মানটাই দেখানো হয় — তাই আগের কোনো হিসাব
    হারায় না, শুধু নতুন টিকগুলো এখান থেকে আসে।
    """
    topic = models.ForeignKey(LectureTopic, on_delete=models.CASCADE,
                              related_name="coverages")
    student = models.ForeignKey(User, on_delete=models.CASCADE,
                                limit_choices_to={"role": "student"},
                                related_name="topic_coverages")
    covered = models.CharField(max_length=8, choices=LectureTopic.Covered.choices,
                               default=LectureTopic.Covered.PENDING)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  blank=True, related_name="+")
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("topic", "student")]

    def __str__(self):
        return f"{self.student.name_bn} — {self.topic.text}: {self.covered}"


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
    # প্রথম লিংকে দুজনেই (উস্তাদ+স্টুডেন্ট) একবার জয়েন করে ফেললে সেই লিংক ওইদিনের
    # জন্য আর দেখানো হয় না — এই দ্বিতীয় (রিজয়েন) লিংকে জয়েন হতে হয় (ঐচ্ছিক)
    zoom_link_2 = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)


class RoutineStudentSchedule(models.Model):
    """একই রুটিনের ভিন্ন ভিন্ন শিক্ষার্থী ভিন্ন ভিন্ন দেশে থাকতে পারে — তাই
    পরিচালক প্রতিটি শিক্ষার্থীর জন্য আলাদাভাবে (ম্যানুয়ালি, কোনো স্বয়ংক্রিয়
    টাইমজোন-হিসাব ছাড়াই) তাদের নিজের সময়ে বার ও সময় বসিয়ে দিতে পারেন —
    না দিলে রুটিনের মূল বার-সময়ই (বাংলাদেশ সময়) তার পোর্টালে দেখানো হয়"""
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name="student_schedules")
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    days = models.JSONField(default=list, blank=True)  # [0..6] — Routine.days-এর মতোই JS getDay() ক্রম
    time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = [("routine", "student")]


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
    zoom_link_2 = models.URLField(blank=True)  # রুটিন থেকে সিঙ্ক হওয়া রিজয়েন-লিংক (ঐচ্ছিক)
    JOIN_MODES = [
        ("auto", "স্বয়ংক্রিয়"),        # উভয়ের হাজিরা নিশ্চিত হলে অটো রিজয়েন দেখায়, নইলে জয়েন
        ("join", "জোর করে জয়েন লিংক"),   # সবসময় ১ম (জয়েন) লিংক দেখাবে
        ("rejoin", "জোর করে রিজয়েন লিংক"),  # সবসময় ২য় (রিজয়েন) লিংক দেখাবে
    ]
    # স্বয়ংক্রিয় জয়েন/রিজয়েন-নির্ধারণ (হাজিরার ওপর ভিত্তি করে) কোনো কারণে সঠিক না
    # হলে, পরিচালক/এডমিন ম্যানুয়ালি জয়েন বা রিজয়েন — যেকোনো একটা লিংক জোর করে
    # চালু করতে পারবেন, বা "auto"-তে ফিরিয়ে দিতে পারবেন — হাজিরা ডেটা স্পর্শ করে না
    join_mode_override = models.CharField(max_length=10, choices=JOIN_MODES, default="auto")
    lecture_no = models.PositiveIntegerField(default=1)
    kind = models.CharField(max_length=10, choices=KINDS, default="regular")
    guardian_requirement = models.TextField(blank=True)  # অভিভাবকের রিকোয়ারমেন্ট
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)
    # উস্তাদ নিজে "ক্লাস শেষ করুন" চেপেছেন কিনা (২য় তথা শেষ পর্ব শেষ করে)।
    # ⚠️ এটা status="done" নয় — ইচ্ছা করেই আলাদা রাখা। উস্তাদ শেষ করলে ক্লাসটি
    # আজকের তালিকাতেই "✅ ক্লাস সম্পন্ন" চিহ্ন নিয়ে থেকে যায়; পরিচালক/এডমিন
    # দেখে যাচাই করে "সম্পন্ন" চিহ্নিত করলে তবেই status="done" হয় এবং তালিকা
    # থেকে সরে। অর্থাৎ দুটি আলাদা ধাপ — উস্তাদের শেষ করা, আর কর্তৃপক্ষের যাচাই।
    teacher_finished = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)  # ৫-মিনিট WhatsApp রিমাইন্ডার (Celery টাস্ক)

    class Meta:
        ordering = ["date", "time"]
        constraints = [
            # একই রুটিন থেকে একই তারিখে দুটো ক্লাস-সেশন যেন কখনোই তৈরি না হয় —
            # আগে শুধু "আছে কিনা চেক করে তারপর তৈরি" (check-then-create) পদ্ধতি
            # ছিল, যা রেস কন্ডিশনে (দৈনিক cron আর কারো ম্যানুয়াল "সব রুটিনের
            # ক্লাস তৈরি করুন" বাটন একইসাথে চললে) দুইটা আলাদা ক্লাস-সেশন তৈরি করে
            # ফেলতে পারত — তখন টিচার ও স্টুডেন্ট ভিন্ন সেশনে জয়েন করে ফেললে কেউই
            # কাউকে "উপস্থিত" দেখতেন না, যদিও দুজনেই আসলে জয়েন করেছেন
            models.UniqueConstraint(
                fields=["routine", "date"],
                condition=models.Q(routine__isnull=False),
                name="unique_routine_date_classsession",
            ),
        ]


class Attendance(models.Model):
    # SET_NULL (CASCADE নয়) — পুরনো ক্লাস (ClassSession) ৬০ দিন পর মুছে গেলেও
    # হাজিরার রেকর্ড কখনো মুছবে না; নিচের denormalized ফিল্ডগুলো (course_name/
    # teacher_name/teacher_id/class_date) session মুছে যাওয়ার পরও রিপোর্টের জন্য
    # প্রয়োজনীয় তথ্য ধরে রাখে
    session = models.ForeignKey(ClassSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=120, blank=True, default="")
    teacher_name = models.CharField(max_length=120, blank=True, default="")
    teacher_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)  # FK নয় — session/teacher মুছে গেলেও ফিল্টারযোগ্য
    class_date = models.DateField(null=True, blank=True, db_index=True)  # মাসভিত্তিক ফিল্টার+সর্ট দ্রুত করতে
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    minutes = models.PositiveIntegerField(default=0)      # সব সেগমেন্ট মিলিয়ে মোট মিনিট
    segment_start = models.DateTimeField(null=True, blank=True)  # চলমান সেগমেন্টের শুরু (জয়েন থাকলে সেট)
    marked_present = models.BooleanField(default=False)   # পরিচালকের ম্যানুয়াল হাজিরা

    class Meta:
        unique_together = [("session", "user")]

    @property
    def active(self):     # এই মুহূর্তে মিটিংয়ে আছে কিনা
        return self.segment_start is not None

    # হাজিরা গণ্য হওয়ার ন্যূনতম সময় (মিনিট)। পর্দার লেখাগুলোও এই একই
    # সংখ্যাই বলে — আগে কোডে ২০ থাকলেও সবাইকে "৪৫ মিনিট" বলা হতো, ফলে
    # কেউ ৩০ মিনিট থেকেও "অনুপস্থিত" ভেবে বসতেন। এখন সত্যিটাই বলা হয়,
    # সাথে পুরো ৪৫ মিনিট ক্লাস করার উৎসাহ আলাদা করে লেখা থাকে।
    MIN_PRESENT_MINUTES = 20

    @property
    def present(self):    # ন্যূনতম সময়, অথবা পরিচালকের ম্যানুয়াল হাজিরা
        return self.marked_present or self.minutes >= self.MIN_PRESENT_MINUTES


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
    # ⚠️ মওকুফ করলে রেকর্ডটা মুছে ফেলা হয় না, চিহ্নিত করে রাখা হয়।
    # আগে মুছে ফেলা হতো — ফলে পরে বোঝার উপায় থাকত না কেন বকেয়া নেই, আর
    # "মওকুফ" ও "পরিশোধিত" এক দেখাত। এখন দুটো আলাদা করে দেখানো যায়।
    # বাড়তি লাভ: মাসিক কাজটি get_or_create করে, তাই মওকুফ করা মাস আর
    # নতুন করে বকেয়া হিসেবে ফিরে আসে না।
    waived = models.BooleanField(default=False, verbose_name="মওকুফ")
    waived_reason = models.CharField(max_length=120, blank=True, default="")
    waived_at = models.DateTimeField(null=True, blank=True)


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


# ═══════════════ দারস স্ক্রিপ্ট ও উপস্থাপনা ═══════════════
# "এক দারস, দুই পর্দা" — উস্তাদ পড়ানোর পুরো নির্দেশনা দেখেন, শিক্ষার্থী
# দেখেন কেবল শেখার জিনিসটুকু।
#
# ⚠️ এটি বিদ্যমান "দারস পরিকল্পনা" (LessonSection/LectureTopic)-এর বদলি নয়।
# সেটি বলে *কী পড়াব ও কার কতটুকু হয়েছে* (পাঠ্যসূচি ও কভারেজ); এটি বলে
# *কীভাবে পড়াব* (বলার স্ক্রিপ্ট, ধাপে ধাপে)। দুটো আলাদা জিনিস, তাই আলাদা
# তালিকা। তবে LessonStep.topic দিয়ে দুটো জোড়া লাগানো যায় — ধাপ শেষ করলে
# ওই টপিকটি পরিকল্পনায় নিজে থেকেই "কভার হয়েছে" হয়ে যাবে।
class Lesson(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "খসড়া"
        READY = "ready", "প্রস্তুত"
        PUBLISHED = "published", "প্রকাশিত"
        ARCHIVED = "archived", "সংরক্ষিত"

    KINDS = [
        ("memorization", "মুখস্থ (হিফজ)"),
        ("qaida", "কায়েদা"),
        ("tajweed", "তাজবীদ"),
        ("reading", "তিলাওয়াত"),
        ("islamic", "ইসলামিক শিক্ষা"),
        ("other", "অন্যান্য"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name="lessons")
    title = models.CharField("দারসের শিরোনাম", max_length=200)
    title_ar = models.CharField("আরবি শিরোনাম", max_length=120,
                                blank=True, default="")
    kind = models.CharField(max_length=14, choices=KINDS, default="memorization")
    # একই বিষয়ের আলাদা বয়সের আলাদা দারস — তাই বয়সটাই সংস্করণ আলাদা করে,
    # বাড়তি কোনো তালিকা লাগে না
    age_from = models.PositiveSmallIntegerField("বয়স — থেকে", default=5)
    age_to = models.PositiveSmallIntegerField("বয়স — পর্যন্ত", default=7)
    duration_min = models.PositiveIntegerField("আনুমানিক সময় (মিনিট)", default=25)
    objectives = models.TextField("কাঙ্ক্ষিত ফল", blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.DRAFT)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "order", "id"]

    def __str__(self):
        return f"{self.title} ({self.age_from}–{self.age_to})"


class LessonStep(models.Model):
    """একটি পড়ানোর ধাপ — উস্তাদ এখানে যা দেখেন তার কিছুই শিক্ষার্থী দেখেন না।

    ঘরগুলো আলাদা আলাদা রাখা হয়েছে (এক গাদা লেখা নয়), যাতে শিক্ষক মোডে
    প্রতিটি অংশ আলাদা করে বড় ও পড়ার উপযোগী করে দেখানো যায়।
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               related_name="steps")
    order = models.PositiveIntegerField(default=0)
    section = models.CharField("এই ধাপের অংশ", max_length=120,
                               blank=True, default="")
    teacher_says = models.TextField("উস্তাদ বলবেন", blank=True, default="")
    teacher_does = models.TextField("উস্তাদ করবেন", blank=True, default="")
    student_does = models.TextField("শিক্ষার্থী করবে", blank=True, default="")
    expected = models.TextField("প্রত্যাশিত সাড়া", blank=True, default="")
    correction = models.TextField("ভুল হলে", blank=True, default="")
    note = models.TextField("উস্তাদের টীকা", blank=True, default="")
    seconds = models.PositiveIntegerField("আনুমানিক সময় (সেকেন্ড)", default=0)
    # ঐচ্ছিক — এই ধাপ শেষ হলে দারস পরিকল্পনার কোন টপিকটি "কভার" ধরা হবে
    topic = models.ForeignKey(LectureTopic, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="lesson_steps")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.lesson.title} — ধাপ {self.order + 1}"


class StepSlide(models.Model):
    """শিক্ষার্থীর পর্দায় এই ধাপে যা দেখা যাবে — আর কিছুই নয়।

    ⚠️ নিরাপত্তার মূল জায়গা: উপস্থাপনার এন্ডপয়েন্ট কেবল এই তালিকা থেকেই
    তথ্য পাঠায়। উস্তাদের স্ক্রিপ্ট লুকানো হয় না — পাঠানোই হয় না। যা
    পাঠানো হয় না, তার ফাঁস হওয়ার পথও নেই।
    """
    KINDS = [
        ("title", "শিরোনাম"), ("verse", "আয়াত"), ("letters", "হরফ"),
        ("listen", "শোনো"), ("repeat", "আমার সাথে বলো"),
        ("your_turn", "তুমি বলো"), ("question", "প্রশ্ন"),
        ("meaning", "অর্থ"), ("visual", "ছবি"), ("activity", "খেলা"),
        ("reminder", "মনে রেখো"), ("praise", "শাবাশ"),
        ("review", "পুনরাবৃত্তি"), ("homework", "বাড়ির কাজ"),
        ("end", "সমাপ্তি"), ("blank", "খালি পর্দা"),
    ]

    step = models.OneToOneField(LessonStep, on_delete=models.CASCADE,
                                related_name="slide")
    kind = models.CharField(max_length=12, choices=KINDS, default="title")
    heading = models.CharField(max_length=160, blank=True, default="")
    # ⚠️ কুরআনের আরবি — যাচাই করে locked করা হলে সাধারণ সম্পাদনায় আর
    # বদলানো যায় না। যের-যবর-তানভীন হুবহু যেমন লেখা হয়েছে তেমনই থাকে।
    arabic = models.TextField(blank=True, default="")
    arabic_locked = models.BooleanField("আরবি যাচাইকৃত ও সুরক্ষিত",
                                        default=False)
    translit = models.CharField(max_length=200, blank=True, default="")
    text = models.TextField(blank=True, default="")
    image = models.CharField(max_length=500, blank=True, default="")
    audio = models.CharField(max_length=500, blank=True, default="")

    def __str__(self):
        return f"{self.step} — {self.get_kind_display()}"


class LessonProgress(models.Model):
    """কোন শিক্ষার্থীর কোন দারস কতটা হয়েছে।

    ⚠️ সম্পূর্ণ নতুন তালিকা — পুরনো কোনো তালিকার একটি ঘরও বদলানো হয়নি।
    রেকর্ড না থাকা মানেই "এখনো শুরু হয়নি", তাই আগে থেকে কিছু বসাতে হয় না
    এবং কারও কোনো তথ্য এই কারণে নড়ে না।

    মুখস্থ হয়েছে কিনা তা উস্তাদই বলেন — কয়বার পড়ানো হলো তা দিয়ে নয়।
    মাস্টার প্রম্পটের নিয়ম: শিক্ষার্থী একা, ঠিক ক্রমে, এক শব্দের ইশারাতেই
    সামলে নিয়ে পড়তে পারলে তবেই "মুখস্থ হয়েছে"।
    """
    class Status(models.TextChoices):
        LEARNING = "learning", "শিখছে"
        REVIEW = "review", "পুনরাবৃত্তি দরকার"
        MASTERED = "mastered", "মুখস্থ হয়েছে"

    # ট্রায়াল অতিথিও দারস করেন, তাই ভূমিকা দিয়ে আটকানো হয়নি
    student = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               related_name="progress")
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.LEARNING)
    times_taught = models.PositiveIntegerField("কয় দিন পড়ানো হয়েছে", default=0)
    last_taught = models.DateField("সর্বশেষ যেদিন", null=True, blank=True)
    # কোন ধাপ পর্যন্ত এগোনো গেছে — পরের ক্লাসে সেখান থেকেই ধরা যায়
    last_step = models.PositiveIntegerField(default=0)
    note = models.TextField("উস্তাদের মন্তব্য", blank=True, default="")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # এক শিক্ষার্থীর এক দারসে একটিই রেকর্ড
        unique_together = [("student", "lesson")]
        ordering = ["-last_taught", "-updated_at"]

    def __str__(self):
        return f"{self.student.name_bn} — {self.lesson.title} ({self.get_status_display()})"


class TrialScoreItem(models.Model):
    """মূল্যায়নের একেকটি মাপকাঠি — পরিচালক নিজে সাজাতে পারেন।

    আগে চারটি মাপকাঠি কোডেই লেখা ছিল, তাই নাম বদলাতে বা নতুন যোগ করতে
    কোড ছুঁতে হতো। এখন এটি একটি সাধারণ তালিকা।

    key কেন আলাদা: উস্তাদের দেওয়া নম্বরগুলো TrialReport.scores-এ
    {"makhraj": 4, ...} আকারে বসে। নাম বদলালেও যেন পুরনো রিপোর্টের নম্বর
    হারিয়ে না যায়, তাই নামের বদলে এই স্থায়ী key দিয়েই নম্বর রাখা হয় —
    একবার তৈরি হলে key আর বদলায় না।
    """
    key = models.CharField(max_length=40, unique=True)
    label_bn = models.CharField("বাংলা নাম (উস্তাদ দেখবেন)", max_length=80)
    # খালি রাখলে বাংলা নামটাই বসে যায় — পরিচালককে অনুবাদ করতে বাধ্য করা
    # হয় না, আবার রিপোর্টে ঘরটা খালিও থাকে না
    label_en = models.CharField("ইংরেজি নাম (পরিবার দেখবেন)", max_length=80,
                                blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.label_bn


class TrialReport(models.Model):
    """ট্রায়াল শেষে উস্তাদের মূল্যায়ন — পরিবারের হাতে যাওয়া লিখিত রিপোর্ট।

    প্রতি অতিথির একটিমাত্র রিপোর্ট (OneToOne) — উস্তাদ ১ম পর্বের পর লিখে
    রাখতে পারেন, ২য় ক্লাসের পর হালনাগাদ করতে পারেন; দুবার আলাদা রিপোর্ট
    তৈরি হয় না।

    তিনটি ধাপ, তিনটি সময়ের ঘর —
      created_at  : উস্তাদ লিখেছেন
      reviewed_at : পরিচালক/এডমিন যাচাই করেছেন
      sent_at     : পরিবারের কাছে পাঠানো হয়েছে
    যাচাই না হওয়া পর্যন্ত পরিবারের কাছে যায় না — ক্লাস "সম্পন্ন" চিহ্নিত
    করার নিয়মে যেভাবে কর্তৃপক্ষের ধাপ রাখা আছে, ঠিক সেভাবেই।
    """
    student = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name="trial_report",
                                   limit_choices_to={"role": "trial"})
    # {"letters": 4, "makhraj": 3, ...} — নামগুলো ঘরের ভেতরেই থাকে, তাই পরে
    # নতুন মাপকাঠি যোগ বা নাম বদলাতে ডাটাবেস ছুঁতে হবে না
    scores = models.JSONField(default=dict, blank=True)
    strengths = models.TextField("শক্তির দিক", blank=True, default="")
    work_on = models.TextField("যা নিয়ে কাজ করতে হবে", blank=True, default="")
    advice = models.TextField("উস্তাদের পরামর্শ", blank=True, default="")
    recommended_course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="trial_recommendations", verbose_name="উপযুক্ত কোর্স")
    recommended_level = models.CharField("উপযুক্ত স্তর", max_length=60,
                                         blank=True, default="")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name="trial_reports_written")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name="trial_reports_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # ─────────── ভর্তির প্রস্তাব ───────────
    # মূল্যায়ন থেকেই প্রস্তাব তৈরি হয়, তাই আলাদা তালিকা না বানিয়ে এখানেই।
    # খালি থাকলে বুঝতে হবে প্রস্তাব এখনো সাজানো হয়নি।
    offer_teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={"role": "teacher"},
        related_name="trial_offers", verbose_name="প্রস্তাবিত উস্তাদ")
    # "Sun, Tue, Thu · 17:00" ধাঁচে — কোর্সভেদে নিয়ম আলাদা, তাই বাঁধা ছক নয়
    offer_schedule = models.CharField("প্রস্তাবিত দিন ও সময়", max_length=160,
                                      blank=True, default="")
    offer_fee = models.PositiveIntegerField("মাসিক ফি", default=0)
    offered_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ট্রায়াল রিপোর্ট — {self.student.name_bn}"


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


class StudentRemark(models.Model):
    """টিচারের মন্তব্য — স্টুডেন্টের ব্যাপারে (পারফরম্যান্স/আচরণ ইত্যাদি), স্টুডেন্টের
    পোর্টালে সবচেয়ে সাম্প্রতিকটা দেখায়; একাধিক মন্তব্য জমা থাকে (ইতিহাস হিসেবে)"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="remarks_received")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="remarks_given")
    text = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


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


class PushSubscription(models.Model):
    """ব্রাউজার Web Push সাবস্ক্রিপশন — ফোন/পিসিতে অ্যাপ ইনস্টল/পারমিশন দিলে
    ট্যাব/ব্রাউজার বন্ধ থাকা অবস্থাতেও নোটিফিকেশন পাঠানো যায়"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


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
