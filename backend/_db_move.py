"""ডেটাবেজ ভার্জিনিয়া → সিঙ্গাপুর সরানোর চালক।

DB-MIGRATION-PLAN.md-এর ধাপগুলোই এখানে, তবে ঠিকানা দুটো (OLD/NEW) কখনো
পর্দায় ছাপা হয় না — .env থেকে নিজে পড়ে নেয়।

    python _db_move.py backup    # ধাপ ১+২ — পুরনো থেকে শুধু পড়া
    python _db_move.py load      # ধাপ ৩   — নতুনে টেবিল ও তথ্য
    python _db_move.py verify    # ধাপ ৪+৫ — গুনে ও ভেতরের লেখা মেলানো

নিরাপত্তা: পুরনো ডেটাবেজে কেবল পড়ার আদেশই চালানো হয়। নতুনটি খালি না
হলে `load` নিজে থেকেই থেমে যায় (ডুপ্লিকেট ঠেকাতে)।
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
BACKUP = BASE / "backup.json"
BEFORE = BASE / "_before.json"


def read_env():
    """.env থেকে OLD/NEW পড়ে — মান কখনো ছাপা হয় না।"""
    env_file = BASE / ".env"
    if not env_file.exists() and not os.environ.get("OLD_DATABASE_URL"):
        sys.exit("backend/.env ফাইলটাই নেই।")
    vals = {}
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")

    # পরিবেশ-চলক দেওয়া থাকলে সেটাই আগে (মহড়া চালানোর জন্য)
    for k in ("OLD_DATABASE_URL", "NEW_DATABASE_URL"):
        if os.environ.get(k):
            vals[k] = os.environ[k]

    missing = [k for k in ("OLD_DATABASE_URL", "NEW_DATABASE_URL")
               if not vals.get(k)]
    if missing:
        sys.exit("backend/.env-এ এই লাইনগুলো নেই: " + ", ".join(missing))
    old, new = vals["OLD_DATABASE_URL"], vals["NEW_DATABASE_URL"]
    if old == new:
        sys.exit("OLD আর NEW একই ঠিকানা — থামা হলো।")
    return old, new


def region(url):
    """ঠিকানার শুধু অঞ্চলটুকু — পরিচয় বা পাসওয়ার্ড নয়।"""
    host = url.split("@")[-1].split("/")[0].split(":")[0]
    parts = host.split(".")
    return ".".join(parts[1:]) if len(parts) > 2 else "?"


def run(args, url, capture=False):
    """manage.py চালায় নির্দিষ্ট ডেটাবেজের দিকে তাক করে।"""
    env = dict(os.environ, DATABASE_URL=url)
    cmd = [sys.executable, str(BASE / "manage.py")] + args
    if capture:
        r = subprocess.run(cmd, env=env, cwd=BASE, capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode:
            sys.exit(f"থেমে গেল:\n{r.stdout}\n{r.stderr}")
        return r.stdout.strip()
    if subprocess.run(cmd, env=env, cwd=BASE).returncode:
        sys.exit("থেমে গেল।")
    return ""


COUNT_SNIPPET = (
    "from django.apps import apps; import json; "
    "print(json.dumps({m.__name__: m.objects.count() "
    "for m in apps.get_app_config('core').get_models()}))"
)


def counts(url):
    out = run(["shell", "-c", COUNT_SNIPPET], url, capture=True)
    return json.loads(out.splitlines()[-1])


def cmd_backup(old, new):
    print("পুরনো ডেটাবেজ (" + region(old) + ") — শুধু পড়া হচ্ছে।")
    run(["dumpdata", "--natural-foreign", "--natural-primary",
         "--exclude", "contenttypes", "--exclude", "auth.permission",
         "--exclude", "sessions", "--exclude", "admin.logentry",
         "--indent", "1", "-o", str(BACKUP)], old)
    before = counts(old)
    BEFORE.write_text(json.dumps(before, indent=1), encoding="utf-8")
    size = BACKUP.stat().st_size
    print(f"ব্যাকআপ হয়েছে: {sum(before.values())} সারি, "
          f"{len(before)} টেবিল, {size:,} বাইট → backup.json")


def cmd_load(old, new):
    if not BACKUP.exists():
        sys.exit("backup.json নেই — আগে `backup` চালান।")
    print("নতুন ডেটাবেজ (" + region(new) + ")।")
    existing = counts(new) if _has_tables(new) else {}
    if sum(existing.values()):
        sys.exit("নতুন ডেটাবেজ খালি নয় — ডুপ্লিকেট ঠেকাতে থামা হলো: "
                 + str({k: v for k, v in existing.items() if v}))
    print("টেবিল তৈরি হচ্ছে…")
    run(["migrate"], new)
    print("তথ্য বসছে…")
    run(["loaddata", str(BACKUP)], new)


def _has_tables(url):
    out = run(["shell", "-c",
               "from django.db import connection; "
               "print(len(connection.introspection.table_names()))"],
              url, capture=True)
    return int(out.splitlines()[-1]) > 0


# পুরনো ও নতুন — দুদিকেই একই হিসাব কষে মেলানো হয়। নির্দিষ্ট একটি আয়াত
# খুঁজে দেখার চেয়ে এটি শক্ত: একই title_ar-এ একাধিক দারস (৫–৭, ৭–৯ বয়সের
# আলাদা সংস্করণ) থাকলেও ভুল হয় না, আর প্রতিটি অক্ষর মিলছে কি না বলে দেয়।
CONTENT_SNIPPET = (
    "import hashlib, json; from core import models as M; "
    "sl=list(M.StepSlide.objects.values_list("
    "'arabic','heading','text','translit').order_by('step_id')); "
    "st=list(M.LessonStep.objects.values_list("
    "'teacher_says','student_does','expected','correction','note')"
    ".order_by('lesson_id','order')); "
    "h=lambda rows: hashlib.sha256("
    "chr(31).join(chr(30).join(c or '' for c in r) for r in rows)"
    ".encode('utf-8')).hexdigest()[:16]; "
    "print(json.dumps({"
    "'দারস': M.Lesson.objects.count(), "
    "'ধাপ': M.LessonStep.objects.count(), "
    "'স্লাইড': len(sl), "
    "'আরবি আছে এমন স্লাইড': sum(1 for r in sl if r[0]), "
    "'আরবির ছাপ': h(sl), "
    "'উস্তাদের লেখার ছাপ': h(st), "
    "'অগ্রগতি': M.LessonProgress.objects.count(), "
    "'টপিক': M.LectureTopic.objects.count(), "
    "'শিক্ষার্থী': M.User.objects.count(), "
    "}, ensure_ascii=False))"
)


def content(url):
    out = run(["shell", "-c", CONTENT_SNIPPET], url, capture=True)
    return json.loads(out.splitlines()[-1])


def cmd_verify(old, new):
    if not BEFORE.exists():
        sys.exit("_before.json নেই — আগে `backup` চালান।")
    before = json.load(open(BEFORE, encoding="utf-8"))
    after = counts(new)
    bad = [(k, before.get(k, 0), after.get(k, 0))
           for k in set(before) | set(after)
           if before.get(k, 0) != after.get(k, 0)]
    if bad:
        print("❌ সারি মেলেনি (টেবিল, আগে, পরে):")
        for row in sorted(bad):
            print("   ", row)
        sys.exit("⛔ থামুন — পরিচালককে Render বদলাতে বলা যাবে না।")
    print(f"✅ সারি মিলেছে — {len(after)} টেবিল, {sum(after.values())} সারি।")

    print()
    print("--- ভেতরের লেখা মেলানো (পুরনো → নতুন) ---")
    co, cn = content(old), content(new)
    width = max(len(k) for k in co)
    ok = True
    for k in co:
        same = co[k] == cn[k]
        ok = ok and same
        line = f"  {'✅' if same else '❌'} {k.ljust(width)}  {co[k]}"
        if not same:
            line += f"   →  {cn[k]}"
        print(line)
    if not ok:
        sys.exit("⛔ থামুন — ভেতরের লেখা মেলেনি।")
    print()
    print("✅ সব মিলেছে — পরিচালক এখন Render-এ ঠিকানা বদলাতে পারেন।")


PHASES = {"backup": cmd_backup, "load": cmd_load, "verify": cmd_verify}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PHASES:
        sys.exit("ব্যবহার: python _db_move.py backup|load|verify")
    PHASES[sys.argv[1]](*read_env())
