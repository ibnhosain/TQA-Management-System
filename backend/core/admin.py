"""TQA-MS — Django অ্যাডমিন প্যানেল রেজিস্ট্রেশন (core/admin.py)"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (User, AcademicBook, Course, SyllabusItem, Lecture, LectureTopic,
                     Routine, ClassSession, Attendance, Question, Assignment, Exam,
                     Submission, ExamResult, FeePayment, DueMonth, TeacherPayment,
                     SentReceipt, Admission, LeaveRequest, Rating, Notice,
                     Notification, WaMessage)


@admin.register(User)
class TQAUserAdmin(UserAdmin):
    list_display = ["username", "name_bn", "role", "phone", "country", "can_fix_cross"]
    list_filter = ["role"]
    fieldsets = UserAdmin.fieldsets + (
        ("TQA তথ্য", {"fields": ("role", "name_bn", "sub_title", "phone", "country",
                                  "guardian", "monthly_fee", "monthly_salary", "can_fix_cross")}),
    )


@admin.register(SyllabusItem)
class SyllabusItemAdmin(admin.ModelAdmin):
    """ফ্রন্টএন্ডের মতো — বিভাগ/বই/বিষয়বস্তু/পৃষ্ঠা/লাইন সব কলাম একসাথে দেখায়"""
    # list_display-এ choice ফিল্ড (category) আপনাআপনি বাংলা লেবেল দেখায়
    list_display = ["course", "category", "book", "lesson", "pages", "lines", "note", "order"]
    list_filter = ["course", "category", "book"]
    search_fields = ["lesson", "note"]
    list_select_related = ["course", "book"]
    list_editable = ["order"]
    ordering = ["course", "category", "order", "id"]
    autocomplete_fields = ["book"]
    fieldsets = (
        (None, {
            "fields": ("course", "category", "book"),
            "description": "বিভাগ (category) — মুখস্থ সূরা · মুখস্থ হাদিস · কিরাত · দুআ/মাসআলা · নৈতিক শিক্ষা — এই ৫টি থেকে বেছে নিন; ফ্রন্টএন্ডের ৫ কলামের সাথে মিলে।",
        }),
        ("বিষয়বস্তু", {"fields": ("lesson", "pages", "lines", "note", "order")}),
    )


@admin.register(AcademicBook)
class AcademicBookAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]   # SyllabusItem.autocomplete_fields=["book"] এর জন্য দরকার


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "teacher", "color", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    filter_horizontal = ["students", "books"]


for m in [Lecture, LectureTopic, Routine,
          ClassSession, Attendance, Question, Assignment, Exam, Submission, ExamResult,
          FeePayment, DueMonth, TeacherPayment, SentReceipt, Admission, LeaveRequest,
          Rating, Notice, Notification, WaMessage]:
    admin.site.register(m)
