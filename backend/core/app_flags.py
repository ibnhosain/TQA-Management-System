"""পরিচালকের Settings পাতার চালু/বন্ধ বোতাম — কী, ডিফল্ট আর পর্দার নাম। ডেটাবেজে সারি না থাকলে ডিফল্ট।"""
FLAGS = {
    "lecture_lock": (True, "Lectures unlock only after approval",
                     "All lectures are shown, but each one stays locked (🔒) until the teacher ticks every topic of the previous lecture AND a director or admin approves it in Lecture Approvals."),
    "student_slides": (True, "Student practice slides",
                       "Students can open their practice slides by clicking a topic in the Lesson Plan."),
    "homework_notes": (True, "Homework notes",
                       "Students see the notes of the lectures they were taught in their Homework page."),
    "auto_cover_panel": (True, "Tick panel at the end of the slides",
                         "When a topic's slides finish, the panel for ticking covered topics opens by itself (the ✓ Topics button always works)."),
}


def flag(key):
    from .models import AppSetting
    default = FLAGS[key][0]
    row = AppSetting.objects.filter(key=key).values_list("enabled", flat=True).first()
    return default if row is None else row


def all_flags():
    from .models import AppSetting
    saved = dict(AppSetting.objects.values_list("key", "enabled"))
    return {k: saved.get(k, v[0]) for k, v in FLAGS.items()}
