"""পরিচালকের Settings (চালু/বন্ধ), লেকচারের তালা, এডমিনের লেকচার অনুমোদন আর স্লাইড চালানোর সময়।

তালার নিয়ম (মালিকের নির্দেশ, ২০২৬-১১-১৭): সব লেকচার উস্তাদ ও শিক্ষার্থীর সামনে থাকে, লেকচার ১ খোলা, বাকিগুলো 🔒।
লেকচার N খোলে শুধু যখন পরিচালক/এডমিন এই শিক্ষার্থীর লেকচার N-1 অনুমোদন দেন (LectureApproval)। অনুমোদনের আগে
তাঁরা দেখেন — উস্তাদ সব টপিক টিক দিয়েছেন কিনা, সেই দিনগুলোর ক্লাসে কে কত মিনিট ছিলেন, স্লাইড কত মিনিট চলেছে।
পরিচালক/এডমিনের জন্য কোনো তালা নেই।
"""
import re

from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .app_flags import FLAGS, all_flags, flag
from .models import (AppSetting, Attendance, Course, DeckPlay, LectureApproval, LectureTopic, LessonSection, TopicCoverage, User)

ADMINS = ("director", "admin")


def lecture_no(name):
    m = re.match(r"^\s*Lecture\s*(\d+)", name or "", re.I)
    return int(m.group(1)) if m else None


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


def _approved(course, sid, cache=None):
    """এই শিক্ষার্থীর কোন লেকচারগুলো অনুমোদিত (সেট)।"""
    key = ("ok", course.id, sid)
    if cache is not None and key in cache:
        return cache[key]
    s = set(LectureApproval.objects.filter(course=course, student_id=sid).values_list("no", flat=True)) if sid else set()
    if cache is not None:
        cache[key] = s
    return s


def lecture_lock(user, course, no, student_id=None, cache=None):
    """তালার কারণ (লেখা) বা None।"""
    if getattr(user, "role", None) in ADMINS or no is None or no <= 1 or not flag("lecture_lock"):
        return None
    sid = user.id if user.role == "student" else student_id
    if not sid:
        return None   # উস্তাদ কোনো শিক্ষার্থী বাছাই করেননি — তালা শিক্ষার্থী ধরে, তাই এখানে আটকানো হয় না
    if (no - 1) in _approved(course, sid, cache):
        return None
    return f"Lecture {no - 1} must be finished and approved first"


def _lecture_topics(course):
    rows = {}
    for t in LectureTopic.objects.filter(section__course=course, section__is_trial=False).select_related("section"):
        n = lecture_no(t.section.name)
        if n is not None:
            rows.setdefault(n, []).append(t)
    return rows


class LectureApprovalsView(APIView):
    """অনুমোদনের অপেক্ষায় থাকা লেকচার (উস্তাদ সব টপিক টিক দিয়েছেন, এখনো অনুমোদন হয়নি) আর সাম্প্রতিক অনুমোদন।"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ADMINS:
            return Response({"error": "Permission denied"}, status=403)
        pending = []
        for course in Course.objects.filter(is_active=True).order_by("name"):
            lect = _lecture_topics(course)
            if not lect:
                continue
            for st in course.students.filter(role="student", is_active=True).select_related("teacher").order_by("name_bn"):
                ok = _approved(course, st.id)
                marks = {r["topic_id"]: r for r in TopicCoverage.objects.filter(topic__section__course=course, student=st)
                         .values("topic_id", "covered", "marked_at", "marked_by__name_bn")}
                for n in sorted(lect):
                    if n in ok or (n > 1 and (n - 1) not in ok):
                        continue          # অনুমোদিত, বা এখনো খোলেইনি
                    ts = lect[n]
                    status = [(marks.get(t.id) or {}).get("covered", t.covered) for t in ts]
                    if not all(x in ("covered", "missed") for x in status):
                        break             # এই শিক্ষার্থী এখনো এই লেকচার শেষ করেনি
                    days = sorted({timezone.localtime(m["marked_at"]).date() for t in ts if (m := marks.get(t.id)) and m.get("marked_at")})
                    classes = []
                    for a in Attendance.objects.filter(user=st, class_date__in=days).select_related("session").order_by("class_date"):
                        tmin = None
                        if a.session_id and a.session.teacher_id:
                            tmin = Attendance.objects.filter(session_id=a.session_id, user_id=a.session.teacher_id).aggregate(m=Sum("minutes"))["m"]
                        classes.append({"date": a.class_date, "student_min": a.minutes, "teacher_min": tmin,
                                        "planned_min": a.session.duration_min if a.session_id else None})
                    plays = list(DeckPlay.objects.filter(course=course, no=n, student=st).values("part")
                                 .annotate(sec=Sum("seconds")).order_by("part"))
                    teacher = st.teacher if st.teacher_id else course.teacher
                    pending.append({
                        "course": course.id, "course_name": course.name, "student": st.id, "student_name": st.name_bn,
                        "teacher_name": getattr(teacher, "name_bn", ""),
                        "no": n, "topics": [{"text": t.text, "covered": s} for t, s in zip(ts, status)],
                        "ticked_by": sorted({m.get("marked_by__name_bn") for t in ts if (m := marks.get(t.id)) and m.get("marked_by__name_bn")}),
                        "days": days, "classes": classes,
                        "slides": [{"part": p["part"] or "—", "minutes": round(p["sec"] / 60, 1)} for p in plays],
                        "slides_total_min": round(sum(p["sec"] for p in plays) / 60, 1),
                    })
                    break
        recent = [{"course_name": a.course.name, "student_name": a.student.name_bn, "no": a.no, "by": getattr(a.approved_by, "name_bn", ""),
                   "at": a.approved_at} for a in LectureApproval.objects.select_related("course", "student", "approved_by")[:30]]
        return Response({"pending": pending, "recent": recent})

    def post(self, request):
        if request.user.role not in ADMINS:
            return Response({"error": "Permission denied"}, status=403)
        if request.data.get("count") not in (None, ""):
            return self._bulk(request)
        try:
            course = Course.objects.get(pk=request.data.get("course"))
            st = course.students.get(pk=request.data.get("student"))
            no = int(request.data.get("no"))
        except Exception:
            return Response({"error": "Please give the course, student and lecture"}, status=400)
        LectureApproval.objects.get_or_create(course=course, student=st, no=no, defaults={"approved_by": request.user})
        return self.get(request)

    def _bulk(self, request):
        """একসাথে অনেক লেকচার খোলা (পরিচালকের নির্দেশ, ২০২৬-১১-২৫): {course, student: id বা "all", count}।
        প্রতিটি শিক্ষার্থীর ক্ষেত্রে তার এখনো-বন্ধ পরের `count`টি লেকচার খোলে — যে যেখানে আছে সেখান থেকে।
        কোর্সের শেষ লেকচারের পরে কিছু খোলে না।"""
        try:
            course = Course.objects.get(pk=request.data.get("course"))
            count = int(request.data.get("count"))
        except Exception:
            return Response({"error": "Please give the course and how many lectures"}, status=400)
        if not 1 <= count <= 500:
            return Response({"error": "How many lectures: give a number from 1 to 500"}, status=400)
        nos = {n for n in (lecture_no(x) for x in LessonSection.objects.filter(course=course, is_trial=False)
                           .values_list("name", flat=True)) if n}
        if not nos:
            return Response({"error": "This course has no lectures yet"}, status=400)
        last = max(nos)
        studs = course.students.filter(role="student").order_by("name_bn")
        who = request.data.get("student")
        if who == "all":
            studs = studs.filter(is_active=True)
        else:
            try:
                studs = studs.filter(pk=int(who))
            except (TypeError, ValueError):
                studs = studs.none()
            if not studs.exists():
                return Response({"error": "This student is not in this course"}, status=400)
        done, new = [], []
        for st in studs:
            ok = _approved(course, st.id)
            opened = []
            for n in range(2, last + 1):          # লেকচার n খোলে যখন n-1 অনুমোদিত
                if len(opened) == count:
                    break
                if (n - 1) not in ok:
                    opened.append(n)
                    new.append(LectureApproval(course=course, student=st, no=n - 1, approved_by=request.user))
            done.append({"student": st.id, "student_name": st.name_bn, "opened": len(opened),
                         "from": opened[0] if opened else None, "to": opened[-1] if opened else None})
        LectureApproval.objects.bulk_create(new, ignore_conflicts=True)
        data = self.get(request).data
        data["unlocked"] = done
        data["last_lecture"] = last
        return Response(data)


class DeckPlayView(APIView):
    """উস্তাদ/এডমিন স্লাইড চালালে সময় রাখা: POST শুরু → {id}; PATCH {id, seconds} প্রতি আধা মিনিটে ও বন্ধ করলে।"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        u = request.user
        if u.role not in ("director", "admin", "teacher"):
            return Response({"id": None})
        try:
            course = Course.objects.get(pk=request.data.get("course"))
            no = int(request.data.get("no"))
        except Exception:
            return Response({"error": "Bad request"}, status=400)
        sid = request.data.get("student")
        st = User.objects.filter(pk=sid, role="student").first() if sid else None
        p = DeckPlay.objects.create(course=course, no=no, part=str(request.data.get("part") or "")[:40], teacher=u, student=st)
        return Response({"id": p.id}, status=201)

    def patch(self, request):
        p = DeckPlay.objects.filter(pk=request.data.get("id"), teacher=request.user).first()
        if not p:
            return Response({"error": "Not found"}, status=404)
        try:
            p.seconds = max(p.seconds, min(int(request.data.get("seconds") or 0), 4 * 3600))
        except (TypeError, ValueError):
            return Response({"error": "Bad seconds"}, status=400)
        p.save(update_fields=["seconds"])
        return Response({"ok": True})
