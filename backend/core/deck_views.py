"""লেকচারের স্লাইড (.pptx) — অ্যাপের ভেতরেই চলে।

কে কী পায়:
  • পরিচালক ও এডমিন: যেকোনো কোর্সের স্লাইড দেখেন ও চালান।
  • উস্তাদ: শুধু নিজের কোর্সের (কোর্সের উস্তাদ, বা কোর্সে নিজের শিক্ষার্থী আছে)।
  • শিক্ষার্থী: স্লাইড দেখে না — শুধু পড়ানো হয়ে যাওয়া লেকচারের নোট (Homework অংশে)।
  • আপলোড/বদল/নোট লেখা/মুছে ফেলা: শুধু পরিচালক।
স্লাইড শেষ হলে উস্তাদ টপিক টিক দেন (cover) — Lecture Plan-এর টপিক হলে সেখানেও কভার বসে,
আর শিক্ষার্থীর জন্য DeckTaught তৈরি হয়, যাতে সে নোট দেখতে পায়।
"""
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .app_flags import flag
from .app_settings_views import lecture_lock
from .models import Course, DeckTaught, LectureDeck, LectureTopic, LessonSection, TopicCoverage, User

ADMINS = ("director", "admin")


def _courses_for(u):
    """এই ব্যবহারকারী কোন কোর্সগুলোর স্লাইড দেখতে পারেন।"""
    if u.role in ADMINS:
        return Course.objects.all()
    if u.role == "teacher":
        from django.db.models import Q
        return Course.objects.filter(Q(teacher=u) | Q(students__teacher=u)).distinct()
    return Course.objects.none()


def _can_see(u, course_id):
    return _courses_for(u).filter(pk=course_id).exists()


def _students_for(u, course):
    """স্লাইড শেষে কার জন্য টিক দেওয়া যাবে — এডমিন-লেভেল: কোর্সের সবাই; উস্তাদ: নিজের শিক্ষার্থী।"""
    from django.db.models import Q
    qs = course.students.filter(role="student", is_active=True)
    if u.role not in ADMINS:   # 🔒 উস্তাদ শুধু নিজের শিক্ষার্থী (উস্তাদ বসানো নেই এমন হলে কোর্সের উস্তাদের)
        own = Q(teacher=u) | (Q(teacher__isnull=True) if course.teacher_id == u.id else Q(pk__in=[]))
        qs = qs.filter(own)
    return qs.order_by("name_bn")


def _plan_topics(deck):
    """Lecture Plan-এ "Lecture N" নামের হেডিংয়ের টপিক (প্রতিটি লেকচার একটি হেডিং; Lecture মডেল এখন শুধু লুকানো ধারক)।"""
    import re
    pat = re.compile(rf"^\s*Lecture\s*{deck.no}\b", re.I)
    secs = [s for s in LessonSection.objects.filter(course=deck.course, is_trial=False) if pat.match(s.name)]
    return list(LectureTopic.objects.filter(section__in=secs).select_related("section", "lecture").order_by("section__order", "order", "id"))


class LectureDeckViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _row(self, d, full=False):
        r = {"id": d.id, "course": d.course_id, "no": d.no, "audience": d.audience, "title": d.title,
             "filename": d.filename, "size": d.size, "uploaded_at": d.uploaded_at}
        if full:
            r.update(note=d.note, topics=d.topics)
        return r

    def _get(self, request, pk):
        d = LectureDeck.objects.defer("data").filter(pk=pk).select_related("course").first()
        if not d or not _can_see(request.user, d.course_id):
            return None
        return d

    def list(self, request):
        qs = LectureDeck.objects.defer("data").filter(course__in=_courses_for(request.user))
        c = request.query_params.get("course")
        if c:
            qs = qs.filter(course_id=c)
        return Response([self._row(d, full=True) for d in qs])

    def create(self, request):
        if request.user.role != "director":
            return Response({"error": "Only the director can upload"}, status=403)
        f = request.FILES.get("file")
        if not f or not (f.name or "").lower().endswith(".pptx"):
            return Response({"error": "Please provide a .pptx file"}, status=400)
        if f.size > 40 * 1024 * 1024:
            return Response({"error": "The file is larger than 40 MB"}, status=400)
        blob = f.read()
        if blob[:2] != b"PK":
            return Response({"error": "The file is not a valid .pptx"}, status=400)
        try:
            course = Course.objects.get(id=request.data.get("course"))
            no = int(request.data.get("no") or 1)
        except Exception:
            return Response({"error": "Please provide a course and lecture number"}, status=400)
        title = (request.data.get("title") or "").strip()[:200]
        audience = "student" if request.data.get("audience") == "student" else "teacher"
        d, _ = LectureDeck.objects.update_or_create(
            course=course, no=no, audience=audience,
            defaults={"title": title, "filename": f.name[:255], "size": len(blob), "data": blob, "uploaded_by": request.user})
        return Response(self._row(d, full=True), status=201)

    def _student_ok(self, u, d):
        """শিক্ষার্থী শুধু নিজের কোর্সের শিক্ষার্থী-স্লাইড পায়।"""
        return u.role == "student" and d.audience == "student" and d.course.students.filter(pk=u.pk).exists()

    def retrieve(self, request, pk=None):
        d = LectureDeck.objects.defer("data").filter(pk=pk).select_related("course").first()
        if not d or not (_can_see(request.user, d.course_id) or self._student_ok(request.user, d)):
            return Response({"error": "Permission denied"}, status=403)
        why = lecture_lock(request.user, d.course, d.no)
        if why:
            return Response({"error": why}, status=403)
        if request.user.role == "student" and not flag("student_slides"):
            return Response({"error": "Practice slides are turned off"}, status=403)
        d = LectureDeck.objects.get(pk=pk)
        res = HttpResponse(bytes(d.data), content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        res["Cache-Control"] = "private, no-store"
        return res

    def partial_update(self, request, pk=None):
        """পরিচালক শিরোনাম, শিক্ষার্থীর নোট আর টপিকের তালিকা লেখেন।"""
        if request.user.role != "director":
            return Response({"error": "Only the director can edit"}, status=403)
        d = self._get(request, pk)
        if not d:
            return Response({"error": "Not found"}, status=404)
        fields = []
        for k, cap in (("title", 200), ("note", 20000), ("topics", 5000)):
            if k in request.data:
                setattr(d, k, str(request.data.get(k) or "").strip()[:cap])
                fields.append(k)
        if fields:
            d.save(update_fields=fields)
        return Response(self._row(d, full=True))

    def destroy(self, request, pk=None):
        if request.user.role != "director":
            return Response({"error": "Only the director can delete"}, status=403)
        LectureDeck.objects.filter(pk=pk).delete()
        return Response(status=204)

    @action(detail=False, methods=["get"])
    def find(self, request):
        """Lesson Plan-এ টপিকে ক্লিক: এই কোর্সের লেকচার N-এর স্লাইড — উস্তাদ/এডমিন/পরিচালক পান উস্তাদের স্লাইড,
        শিক্ষার্থী পায় তার পড়া-প্র্যাকটিসের স্লাইড।"""
        u = request.user
        try:
            course_id, no = int(request.query_params.get("course")), int(request.query_params.get("no"))
        except (TypeError, ValueError):
            return Response({"error": "Please provide a course and lecture number"}, status=400)
        if u.role == "student":
            if not Course.objects.filter(pk=course_id, students=u).exists():
                return Response({"error": "Permission denied"}, status=403)
            if not flag("student_slides"):
                return Response({"error": "Practice slides are turned off"}, status=403)
            aud = "student"
        elif _can_see(u, course_id):
            aud = "teacher"
        else:
            return Response({"error": "Permission denied"}, status=403)
        try:
            sid = int(request.query_params.get("student") or 0) or None
        except ValueError:
            sid = None
        why = lecture_lock(u, Course.objects.get(pk=course_id), no, sid)
        if why:
            return Response({"error": why}, status=403)
        d = LectureDeck.objects.defer("data").filter(course_id=course_id, no=no, audience=aud).first()
        if not d:
            return Response({"error": f"No slides yet for Lecture {no}"}, status=404)
        return Response(self._row(d))

    @action(detail=True, methods=["get", "post"])
    def cover(self, request, pk=None):
        """স্লাইড শেষে: কোন টপিক কভার হলো, কোন শিক্ষার্থীর জন্য।"""
        u = request.user
        d = self._get(request, pk)
        if not d:
            return Response({"error": "Permission denied"}, status=403)
        studs = _students_for(u, d.course)
        plan = _plan_topics(d)
        extra = [t.strip() for t in (d.topics or "").splitlines() if t.strip()]
        if request.method == "GET":
            done = {r.student_id: r.topics for r in DeckTaught.objects.filter(deck=d, student__in=studs)}
            return Response({
                "lecture": d.no,
                "plan_topics": [{"id": t.id, "text": t.text, "section": t.section.name if t.section else ""} for t in plan],
                "deck_topics": [] if plan else extra,
                "students": [{"id": s.id, "name": s.name_bn, "done": s.id in done} for s in studs],
            })

        allowed = {s.id for s in studs}
        try:
            sids = [int(x) for x in request.data.get("student_ids") or []]
            tids = {int(x) for x in request.data.get("topic_ids") or []}
        except (TypeError, ValueError):
            return Response({"error": "Invalid data"}, status=400)
        texts = [str(x).strip()[:300] for x in request.data.get("deck_topics") or [] if str(x).strip()]
        sids = [s for s in sids if s in allowed]
        if not sids:
            return Response({"error": "Please choose at least one student"}, status=400)
        chosen = [t for t in plan if t.id in tids]
        is_admin = u.role in ADMINS or getattr(u, "can_fix_cross", False)   # লাল ক্রস সরানোর অনুমতি
        for sid in sids:
            for t in chosen:
                row, _ = TopicCoverage.objects.get_or_create(topic=t, student_id=sid)
                if row.covered == LectureTopic.Covered.MISSED and not is_admin:
                    continue
                row.covered = LectureTopic.Covered.COVERED
                row.marked_by = u
                row.save()
            DeckTaught.objects.update_or_create(
                deck=d, student_id=sid,
                defaults={"topics": [t.text for t in chosen] + texts, "taught_by": u})
        if chosen and not chosen[0].lecture.date:
            lec = chosen[0].lecture
            lec.date = timezone.localtime().date()
            lec.save(update_fields=["date"])
        return Response({"ok": True, "students": len(sids), "topics": len(chosen) + len(texts)})

    @action(detail=False, methods=["get"])
    def notes(self, request):
        """শিক্ষার্থীর Homework: যে লেকচারগুলো তাকে পড়ানো হয়েছে, তার নোট (নতুনটা আগে)।"""
        u = request.user
        if u.role != "student" or not flag("homework_notes"):
            return Response([])
        rows = (DeckTaught.objects.filter(student=u).select_related("deck", "deck__course")
                .defer("deck__data").order_by("-deck__no", "-taught_at"))
        return Response([{"id": r.deck_id, "course": r.deck.course.name, "no": r.deck.no, "title": r.deck.title,
                          "note": r.deck.note, "topics": r.topics, "taught_at": r.taught_at} for r in rows])
