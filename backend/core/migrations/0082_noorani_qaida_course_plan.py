"""Noorani Qaida Course (৭–১২ বছর) — Lecture Plan, Syllabus ও কভার-টিকের তালিকা কোর্সের ৫টি বই অনুযায়ী,
Easy Noorani Qaida-র (0060) হুবহু একই ফরম্যাটে (মালিকের নির্দেশ, ২০২৬-১১-১৯; অনুমতি: "পুরনো মুছে নতুন বসাও")।

• পুরনো নিয়মিত পরিকল্পনা মোছা হয়: নিয়মিত হেডিং, তাদের টপিক (সাথে শিক্ষার্থীর টিক), হেডিংহীন টপিক আর এই কোর্সের SyllabusItem।
  ট্রায়ালের পরিকল্পনায় হাত দেওয়া হয় না।
• নতুন: প্রতিটি লেকচার একটি হেডিং ("Lecture 1" … "Lecture 45"), নিচে ৫টি বই থেকে সেদিনের পড়া (৫টি টপিক)।
• Syllabus টেবিল: Lecture | ৫টি বই — প্রতি লেকচারে এক সারি।
তালিকার উৎস: Books/_একাডেমিক-বই-টুলস/slides/course_plan_noorani.py → plan_seed/noorani_qaida_plan.json
কোর্স খোঁজা: "Easy" ছাড়া — নাম "Noorani Qaida" / "Noorani Qaida Course", না পেলে নামে noorani/nurani/নূরানী/নুরানী।
"""
import html
import json
import os

from django.db import migrations

FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plan_seed", "noorani_qaida_plan.json")


def noorani_course(Course):
    qs = Course.objects.exclude(name__icontains="easy")
    for n in ("Noorani Qaida", "Noorani Qaida Course"):
        c = qs.filter(name__iexact=n).first()
        if c:
            return c
    for w in ("noorani", "nurani", "নূরানী", "নুরানী", "নূরানি", "নুরানি"):
        c = qs.filter(name__icontains=w).first()
        if c:
            return c
    return None


def forwards(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    Lecture = apps.get_model("core", "Lecture")
    LectureTopic = apps.get_model("core", "LectureTopic")
    LessonSection = apps.get_model("core", "LessonSection")
    SyllabusItem = apps.get_model("core", "SyllabusItem")
    Sheet = apps.get_model("core", "CourseSyllabusSheet")
    course = noorani_course(Course)
    if course is None or not os.path.exists(FILE):
        return
    plan = json.load(open(FILE, encoding="utf-8"))

    # ── পুরনো নিয়মিত পরিকল্পনা ──
    LectureTopic.objects.filter(lecture__course=course).exclude(section__is_trial=True).delete()
    LessonSection.objects.filter(course=course, is_trial=False).delete()
    SyllabusItem.objects.filter(course=course).delete()
    holder = Lecture.objects.filter(course=course).order_by("id").first()
    Lecture.objects.filter(course=course).exclude(pk=getattr(holder, "pk", None)).filter(topics__isnull=True).delete()
    if holder is None:
        holder = Lecture.objects.create(course=course, no=1, title="দারস তালিকা")

    # ── নতুন: প্রতি লেকচারে একটি হেডিং, ৫টি বইয়ের টপিক ──
    rows = []
    for L in plan["lectures"]:
        sec = LessonSection.objects.create(course=course, name=f"Lecture {L['no']}", order=L["no"], is_trial=False)
        for k, t in enumerate(L["topics"]):
            body = "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in t["items"]) + "</ul>"
            LectureTopic.objects.create(lecture=holder, section=sec, text=t["text"][:300], content=body, order=k)
        rows.append([f"Lecture {L['no']}"] + [t["text"].split(" — ", 1)[1] for t in L["topics"]])
    Sheet.objects.update_or_create(course=course, defaults={"headers": ["Lecture"] + plan["books"], "rows": rows})


class Migration(migrations.Migration):
    dependencies = [("core", "0081_seed_easy_qaida_lectures_61_to_67")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
