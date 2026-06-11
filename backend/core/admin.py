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


for m in [AcademicBook, Course, SyllabusItem, Lecture, LectureTopic, Routine,
          ClassSession, Attendance, Question, Assignment, Exam, Submission, ExamResult,
          FeePayment, DueMonth, TeacherPayment, SentReceipt, Admission, LeaveRequest,
          Rating, Notice, Notification, WaMessage]:
    admin.site.register(m)
