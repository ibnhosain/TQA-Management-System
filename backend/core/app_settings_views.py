"""পরিচালকের Settings (চালু/বন্ধ) আর স্লাইড চালানোর সময়।

২০২৬-১১-২৬: লেকচারের তালা আর "Lecture Approvals" (অনুমোদন দিলে পরের লেকচার খোলা) পুরো সরানো হয়েছে —
মালিকের নির্দেশ: "এই এপ্রুভাল সিস্টেমটাই বাদ দাও"। এখন সব লেকচার সবার জন্য সবসময় খোলা।
পুরনো অনুমোদনের রেকর্ড (LectureApproval টেবিল) ডাটাবেসে রেখে দেওয়া — কোথাও ব্যবহার হয় না।
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .app_flags import FLAGS, all_flags
from .models import AppSetting, Course, DeckPlay, User


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
