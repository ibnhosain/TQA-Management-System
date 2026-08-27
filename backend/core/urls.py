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

def _warmup(request):
    """ডাটাবেজ ঘুমিয়ে থাকলে জাগিয়ে তোলে।

    ⚠️ কেন দরকার — Neon নিষ্ক্রিয় থাকলে কম্পিউট বন্ধ করে দেয়। পরের
    প্রথম প্রশ্নটি তখন ডাটাবেজ জাগা পর্যন্ত অপেক্ষা করে, আর সেটা
    ১০-২০ সেকেন্ডও হতে পারে। ঠিক তখনই পরিচালক "দারস আনা যায়নি"
    দেখতেন — অথচ সার্ভার বা কোডে কোনো সমস্যা ছিল না।

    অ্যাপ খোলার সাথে সাথেই এটি ডাকা হয়, তাই তিনি যখন সত্যিই কোনো
    দারস খোলেন তখন ডাটাবেজ জেগেই থাকে।

    ⚠️ এটি ক্রন নয় — কেউ অ্যাপ খুললে তবেই চলে। আগে প্রতি মিনিটের একটি
    ক্রন Neon-এর কম্পিউট-কোটা পুড়িয়ে ফেলেছিল; এখানে সেই ঝুঁকি নেই,
    কারণ ব্যবহার না হলে একবারও চলে না।

    ⚠️ লগইন লাগে না — ঘুম ভাঙানোর জন্য টোকেনের অপেক্ষা করলে দেরিটাই
    থেকে যেত। কোনো তথ্য ফেরত যায় না, কেবল "জেগেছে কি না"।
    """
    import time
    t0 = time.time()
    ok = True
    try:
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception:
        ok = False
    return JsonResponse({"ok": ok, "ms": int((time.time() - t0) * 1000)})


urlpatterns = [
    path("auth/login", FlexTokenObtainPairView.as_view()),  # আইডি/ইমেইল/ফোন — যেকোনোটা দিয়ে
    path("auth/refresh", TokenRefreshView.as_view()),
    # Render free tier ঘুম ভাঙানো — cron-job.org প্রতি ১৪ মিনিটে পিং করে
    path("ping/", lambda r: JsonResponse({"ok": True, "service": "TQA-MS"})),
    # ⚠️ ডাটাবেজ জাগানো — ping/ ডাটাবেজ ছোঁয় না, তাই ঘুমন্ত Neon জাগত না
    path("warmup/", _warmup),
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
