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

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="users")
router.register("books", views.AcademicBookViewSet, basename="books")
router.register("courses", views.CourseViewSet, basename="courses")
router.register("syllabus", views.SyllabusViewSet)
router.register("lectures", views.LectureViewSet)
router.register("routines", views.RoutineViewSet, basename="routines")
router.register("classes", views.ClassSessionViewSet, basename="classes")
router.register("assignments", views.AssignmentViewSet, basename="assignments")
router.register("exams", views.ExamViewSet, basename="exams")
router.register("fees", views.FeePaymentViewSet, basename="fees")
router.register("salaries", views.TeacherPaymentViewSet, basename="salaries")
router.register("receipts", views.SentReceiptViewSet, basename="receipts")
router.register("admissions", views.AdmissionViewSet)
router.register("leaves", views.LeaveRequestViewSet, basename="leaves")
router.register("ratings", views.RatingViewSet, basename="ratings")
router.register("notices", views.NoticeViewSet)
router.register("notifications", views.NotificationViewSet, basename="notifications")
router.register("wa-messages", views.WaMessageViewSet)
router.register("library-books", views.LibraryBookViewSet)

urlpatterns = [
    path("auth/login", FlexTokenObtainPairView.as_view()),  # আইডি/ইমেইল/ফোন — যেকোনোটা দিয়ে
    path("auth/refresh", TokenRefreshView.as_view()),
    # Render free tier ঘুম ভাঙানো — cron-job.org প্রতি ১৪ মিনিটে পিং করে
    path("ping/", lambda r: JsonResponse({"ok": True, "service": "TQA-MS"})),
    # Cron endpoints (cron-job.org থেকে ডাকা হয় — Celery ছাড়া scheduled কাজ)
    path("cron/reminders/", cron.cron_reminders),
    path("cron/daily/", cron.cron_daily),
    path("cron/monthly/", cron.cron_monthly),
    # পরিচালক সব ডেটা ডাউনলোড করতে পারবেন — JSON ব্যাকআপ
    path("export/", views.export_all_data),
    path("", include(router.urls)),
]
