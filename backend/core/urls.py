"""TQA-MS — API রাউটিং (core/urls.py)
প্রজেক্টের মূল urls.py-তে: path("api/", include("core.urls"))
লগইন (JWT): POST /api/auth/login {username, password} → {access, refresh}
"""
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .auth import FlexTokenObtainPairView
from . import cron
from . import push

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="users")
router.register("books", views.AcademicBookViewSet, basename="books")
router.register("courses", views.CourseViewSet, basename="courses")
router.register("syllabus", views.SyllabusViewSet)
router.register("lectures", views.LectureViewSet)
router.register("routines", views.RoutineViewSet, basename="routines")
router.register("classes", views.ClassSessionViewSet, basename="classes")
router.register("attendance", views.AttendanceViewSet, basename="attendance")
router.register("assignments", views.AssignmentViewSet, basename="assignments")
router.register("exams", views.ExamViewSet, basename="exams")
router.register("fees", views.FeePaymentViewSet, basename="fees")
router.register("salaries", views.TeacherPaymentViewSet, basename="salaries")
router.register("receipts", views.SentReceiptViewSet, basename="receipts")
router.register("trials", views.TrialViewSet, basename="trials")
router.register("trial-reports", views.TrialReportViewSet, basename="trial-reports")
router.register("trial-score-items", views.TrialScoreItemViewSet, basename="trial-score-items")
router.register("lessons", views.LessonViewSet, basename="lessons")
router.register("lesson-steps", views.LessonStepViewSet, basename="lesson-steps")
router.register("lesson-progress", views.LessonProgressViewSet, basename="lesson-progress")
router.register("admissions", views.AdmissionViewSet)
router.register("leaves", views.LeaveRequestViewSet, basename="leaves")
router.register("ratings", views.RatingViewSet, basename="ratings")
router.register("remarks", views.StudentRemarkViewSet, basename="remarks")
router.register("notices", views.NoticeViewSet)
router.register("notifications", views.NotificationViewSet, basename="notifications")
router.register("wa-messages", views.WaMessageViewSet)
router.register("library-books", views.LibraryBookViewSet)
router.register("lesson-sections", views.LessonSectionViewSet, basename="lesson-sections")
router.register("push-subscriptions", views.PushSubscriptionViewSet, basename="push-subscriptions")

def _version(request):
    """সার্ভারে কোন মাইগ্রেশন পর্যন্ত চলেছে — নির্ণয়ের জন্য।

    ⚠️ কেন দরকার — "নতুন দারস বসেনি" বলার পর প্রতিবার অনুমান করতে হতো:
    ডিপ্লয় হয়েছে কি হয়নি, মাইগ্রেশন চলেছে কি চলেনি। বাইরে থেকে দেখার
    কোনো উপায় ছিল না। এই পথটি এক ডাকেই উত্তর দেয়।

    ⚠️ কোনো তথ্য ফাঁস হয় না — কেবল শেষ মাইগ্রেশনের নাম ও সংখ্যা।
    ⚠️ ফ্রন্টএন্ড এটি কখনো ডাকে না। আগে "ডাটাবেজ জাগানোর" একটি পথ
    প্রতি পাতা-লোডে ডাকা হতো, আর তাতে ভিড়ের সময় অ্যাপ আটকে গিয়েছিল।
    এটি কেবল হাতে ডাকার জন্য — কোনো স্বয়ংক্রিয় ডাক নেই।
    """
    try:
        from django.db.migrations.recorder import MigrationRecorder
        rows = MigrationRecorder.Migration.objects.filter(app="core")
        last = rows.order_by("-id").first()
        return JsonResponse({"core_last": last.name if last else None,
                             "core_count": rows.count()})
    except Exception as e:
        return JsonResponse({"error": str(e)[:120]}, status=500)


urlpatterns = [
    path("auth/login", FlexTokenObtainPairView.as_view()),  # আইডি/ইমেইল/ফোন — যেকোনোটা দিয়ে
    path("auth/refresh", TokenRefreshView.as_view()),
    # Render free tier ঘুম ভাঙানো — cron-job.org প্রতি ১৪ মিনিটে পিং করে
    path("ping/", lambda r: JsonResponse({"ok": True, "service": "TQA-MS"})),
    # ⚠️ নির্ণয়ের পথ — সার্ভারে কোন মাইগ্রেশন পর্যন্ত চলেছে
    path("version/", _version),
    # Cron endpoints (cron-job.org থেকে ডাকা হয় — Celery ছাড়া scheduled কাজ)
    path("cron/reminders/", cron.cron_reminders),
    path("cron/daily/", cron.cron_daily),
    path("cron/monthly/", cron.cron_monthly),
    # পরিচালক সব ডেটা ডাউনলোড করতে পারবেন — JSON ব্যাকআপ
    path("export/", views.export_all_data),
    # Web Push পাবলিক কী — ফ্রন্টএন্ড PushManager.subscribe()-এ ব্যবহার করে
    # দারসের টগলে বসানোর ছবি/PDF আপলোড (কেবল পরিচালক)
    path("lesson-media/", views.LessonMediaView.as_view()),
    path("push/vapid-public-key/", lambda r: JsonResponse({"key": push.public_key_b64()})),
    path("", include(router.urls)),
]
