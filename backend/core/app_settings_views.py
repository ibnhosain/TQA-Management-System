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


def _done_lectures(course, sid, cache=None):
    """এই শিক্ষার্থীর কোন লেকচারগুলো এখনো পুরো টিক হয়নি (ফেরত দেয় অসম্পূর্ণগুলো) ("Lecture N"-এর সব টপিক ✔ বা ✘)। cache: একই অনুরোধে বারবার না গোনা।"""
    from .models import LectureTopic, TopicCoverage
    key = (course.id, sid)
    if cache is not None and key in cache:
        return cache[key]
    rows = {}
    for t in LectureTopic.objects.filter(section__course=course, section__is_trial=False).select_related("section"):
        n = lecture_no(t.section.name)
        if n is not None:
            rows.setdefault(n, []).append(t)
    marked = dict(TopicCoverage.objects.filter(topic__section__course=course, student_id=sid).values_list("topic_id", "covered")) if sid else {}
    done = {n for n, ts in rows.items() if all(marked.get(t.id, t.covered) in ("covered", "missed") for t in ts)}
    pending = set(rows) - done          # প্ল্যানে আছে কিন্তু পুরো টিক হয়নি — টপিকই নেই এমন লেকচার আটকায় না
    if cache is not None:
        cache[key] = pending
    return pending


def lecture_lock(user, course, no, student_id=None, cache=None):
    """তালার কারণ (লেখা) বা None। পরিচালক/এডমিনের জন্য কখনো তালা নেই।
    ১) লেকচার অনুমোদন চালু আর no > অনুমোদিত সংখ্যা → এখনো খোলা হয়নি।
    ২) ধারাবাহিক তালা চালু আর আগের লেকচারের সব টপিক এই শিক্ষার্থীর জন্য টিক হয়নি → আগেরটা শেষ করো।"""
    from .app_flags import flag
    if getattr(user, "role", None) in ADMINS or no is None:
        return None
    if flag("lecture_approval") and no > (course.lectures_released or 0):
        return f"Lecture {no} is not open yet"
    if no > 1 and flag("sequential_unlock"):
        sid = user.id if user.role == "student" else student_id
        if sid and (no - 1) in _done_lectures(course, sid, cache):
            return f"Finish Lecture {no - 1} first — tick all its topics"
    return None
