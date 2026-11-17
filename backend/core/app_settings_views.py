"""পরিচালকের Settings পাতা: চালু/বন্ধ বোতাম (শুধু পরিচালক বদলান) আর কোর্সপ্রতি অনুমোদিত লেকচার (পরিচালক ও এডমিন)।"""
import re

from django.db.models import Max
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .app_flags import FLAGS, all_flags
from .models import AppSetting, Course, LectureDeck, LessonSection

ADMINS = ("director", "admin")


class AppSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        flags = all_flags()
        return Response({"flags": flags, "items": [{"key": k, "label": v[1], "help": v[2], "enabled": flags[k]} for k, v in FLAGS.items()]})

    def post(self, request):
        if request.user.role != "director":
            return Response({"error": "Only the director can change settings"}, status=403)
        key = request.data.get("key")
        if key not in FLAGS:
            return Response({"error": "Unknown setting"}, status=400)
        enabled = request.data.get("enabled") in (True, "true", "1", 1)
        AppSetting.objects.update_or_create(key=key, defaults={"enabled": enabled, "updated_by": request.user})
        return self.get(request)


class LectureReleaseView(APIView):
    """কোর্সপ্রতি কয়টা লেকচার খোলা — পরিচালক ও এডমিন দেখেন ও বদলান।"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ADMINS:
            return Response({"error": "Permission denied"}, status=403)
        pat = re.compile(r"^\s*Lecture\s*(\d+)", re.I)
        rows = []
        for c in Course.objects.filter(is_active=True).order_by("name"):
            plan = [int(m.group(1)) for n in LessonSection.objects.filter(course=c, is_trial=False).values_list("name", flat=True) if (m := pat.match(n))]
            decks = LectureDeck.objects.filter(course=c).aggregate(m=Max("no"))["m"] or 0
            rows.append({"id": c.id, "name": c.name, "released": c.lectures_released,
                         "plan_lectures": max(plan) if plan else 0, "slides_up_to": decks})
        return Response(rows)

    def post(self, request):
        if request.user.role not in ADMINS:
            return Response({"error": "Permission denied"}, status=403)
        try:
            c = Course.objects.get(pk=request.data.get("course"))
            n = max(0, int(request.data.get("released")))
        except Exception:
            return Response({"error": "Please give a course and a number"}, status=400)
        c.lectures_released = n
        c.save(update_fields=["lectures_released"])
        return self.get(request)


def lecture_no(name):
    m = re.match(r"^\s*Lecture\s*(\d+)", name or "", re.I)
    return int(m.group(1)) if m else None


def is_released(user, course, no):
    """এই ব্যবহারকারী কি এই কোর্সের লেকচার no দেখতে পারেন? (লেকচার অনুমোদন চালু থাকলে)"""
    from .app_flags import flag
    if getattr(user, "role", None) in ADMINS or no is None or not flag("lecture_approval"):
        return True
    return no <= (course.lectures_released or 0)
