# -*- coding: utf-8 -*-
"""স্ক্রিপ্ট থেকে শিক্ষার্থীর অনুশীলনের কাগজ তৈরি।

উদ্দেশ্য — পরিচালককে যেন টগলের ভেতরের লেখা আলাদা করে লিখতে না হয়।

⚠️ এটি স্লাইডগুলোর হুবহু নকল নয়। স্লাইড হলো পড়ানোর ধাপ — "Say it with
me" বারবার, খেলা, শাবাশ, খালি পর্দা। সেগুলো টগলে ঢাললে শিক্ষার্থীর
কাজে লাগে না। তাই এখানে ধাপগুলো থেকে **অনুশীলনের কাগজ** বানানো হয়:

  📖 আজ যা শেখা হয়েছে   — পুরোটা একসাথে (লেকচার প্ল্যানের চেহারা)
  🎤 এভাবে অনুশীলন করো   — টুকরো → পুরো → অর্থ (অনুশীলনের চেহারা)
  📌 বাড়িতে              — বাড়ির কাজ

⚠️ সবচেয়ে জরুরি নিয়ম — এই লেখাটি **শিক্ষার্থী পড়বেন**। তাই এটি তৈরি হয়
কেবল স্লাইড থেকে, অর্থাৎ ক্লাসে বাচ্চার পর্দায় যা ছিল সেটুকু থেকেই।
উস্তাদের স্ক্রিপ্টের কোনো ঘর (teacher_says / teacher_does / student_does
/ expected / correction / note) এখানে ছোঁয়াও হয় না — পুরো ব্যবস্থার
দেয়ালটা এখানেও অটুট।

⚠️ কোনো দারসের গড়নের উপর ভরসা করা হয়নি। ইখলাসে ভাগগুলো "Part 3 — …",
কায়দায় "ا — Listen" — সম্পূর্ণ আলাদা। তাই শিরোনাম বা ভাগের নাম না দেখে
আরবি লেখাগুলোর নিজেদের সম্পর্ক দেখা হয়: যে লেখা অন্য লেখাকে নিজের
ভেতরে ধারণ করে সেটিই "পুরোটা", আর ছোটগুলো তার "টুকরো"। ফলে পরিচালক
নতুন যে দারসই লিখুন, কাজ করবে।

⚠️ বসানোর পরেও পরিচালক লেখাটি নিজের মতো করে সম্পাদনা করতে পারেন —
লেকচার প্ল্যানের টগলে, আগের মতোই। এটি কেবল শুরুটা করে দেয়।

⚠️ লেখাগুলো ইংরেজিতে — শিক্ষার্থীর পোর্টাল ইংরেজিতেই চলে, বেশিরভাগ
শিক্ষার্থী বাংলা বোঝে না।
"""
import re
from html import escape

from .safe_html import clean_html

# যেগুলো অনুশীলনের বিষয় নয় — ফাঁকা পর্দা, সূরার নামের পাতা, আর
# শেষের দুআ। এগুলো ক্লাসের সাজসজ্জা; বাচ্চা এগুলো মুখস্থ করে না।
# ⚠️ title-এ কখনো আয়াতও থাকে, কিন্তু সেই আয়াত verse-পর্দাতেও আসে,
# তাই কিছুই হারায় না।
SKIP_KINDS = {"blank", "title", "end"}

# অর্থ/ব্যাখ্যা যে স্লাইডগুলোয় থাকে
MEANING_KINDS = {"meaning", "question"}

# বাড়ির কাজ ও শেষের কথা
HOME_KINDS = {"homework"}

# ✏️ খাতায় লেখার ধাপ — কায়দায় পড়ার পাশাপাশি লেখাও শেখা হয়। শিশু নিজের
# খাতায় পেনসিল দিয়ে লিখে উস্তাদকে দেখায়, তাই বাড়িতেও অনুশীলনটা জানা
# দরকার — নইলে অভিভাবক বুঝতেন না কী লেখাতে হবে।
WRITE_KINDS = {"write"}

# কুরআনের আরবির সাজ। Amiri Quran কুরআনের জন্যই বানানো মুসহাফ-ধাঁচের
# নাসখ ফন্ট — যের-যবর-শাদ্দা-তানভীন মুসহাফের মতোই বসে।
# ⚠️ মাপ উদার — ৫-৭ বছরের শিশু যের-যবর-শাদ্দা আলাদা করে চিনতে পারা চাই
ARABIC_STYLE = (
    "font-family:'Amiri Quran','Amiri',serif;"
    "font-size:26px;line-height:2"
)

# টুকরোগুলো একটু ছোট করে — চোখেই বোঝা যায় কোনটা অংশ, কোনটা পুরোটা
PIECE_STYLE = (
    "font-family:'Amiri Quran','Amiri',serif;"
    "font-size:20px;line-height:1.9"
)

# ───── সাজসজ্জা ─────
# ⚠️ সবই ইনলাইন style, কারণ টগলের লেখা HTML হিসেবেই সংরক্ষিত হয় — আলাদা
# CSS ফাইল সেখানে পৌঁছায় না। আর safe_html-এর অনুমোদিত তালিকায় নেই এমন
# কিছু ব্যবহার করা হয়নি (box-shadow, gap, border-left — কোনোটিই নয়),
# নইলে সংরক্ষণের সময় সাজটুকু নিঃশব্দে মুছে যেত।
# রংগুলো অ্যাপের নিজের তালিকা থেকেই, যাতে বেমানান না লাগে।
CARD = (
    "border:1px solid %s;background-color:%s;border-radius:14px;"
    "padding:14px 16px;margin:0 0 12px 0"
)
HEAD = (
    "font-size:15px;font-weight:700;color:%s;margin:0 0 10px 0"
)
NUM = (
    "font-size:12px;font-weight:700;color:#8a7a55;"
    "margin:0 0 6px 0"
)
# ⚠️ dir="rtl" কেবল <span>-এ দিলে হয় না। টুকরোগুলো পাশাপাশি বসে
# বাইরের বাক্সের দিক ধরে — বাক্স বাঁ-থেকে-ডান হলে "قُلْ · هُوَ ٱللَّهُ ·
# أَحَدٌ" বাঁ দিক থেকে সাজে, অথচ আরবি পড়া হয় ডান থেকে। ফলে শেষ
# টুকরোটাই আগে পড়ে ফেলতেন। তাই বাক্সগুলোতেই দিক বসাতে হয়।
PIECE_ROW = (
    "background-color:#faf7ef;border-radius:10px;padding:8px 10px;"
    "margin:0 0 8px 0;text-align:center;direction:rtl"
)
WHOLE_ROW = "text-align:center;margin:0 0 6px 0;direction:rtl"
MEAN_ROW = (
    "font-size:13.5px;color:#4b5563;font-style:italic;"
    "text-align:center;margin:0"
)

# পর্দায় যা কেবল ছবি/ইমোজি — অনুশীলনে কাজে লাগে না
EMOJI_ONLY = re.compile(r"^[\W\d_]+$", re.UNICODE)


def _norm(v):
    """তুলনার জন্য — বাড়তি ফাঁক সরিয়ে এক লাইনে।"""
    return re.sub(r"\s+", " ", str(v or "")).strip()


def _lines(v):
    """একাধিক লাইনের লেখা → <br> দিয়ে জোড়া, নিরাপদে escape করে।"""
    return "<br>".join(escape(x) for x in str(v or "").split("\n") if x.strip())


def _ar(text, style=ARABIC_STYLE):
    # dir="rtl" — আরবি যেন ডান থেকে বাঁয়ে ঠিকভাবে বসে।
    # ফন্টও বসানো হয় — শিক্ষার্থী টগলেই অনুশীলন করেন, তাই সেখানেও
    # কুরআনের ফন্টে দেখা চাই। না নামলে Amiri, তারপর সিস্টেমের serif।
    return '<span dir="rtl" style="%s">%s</span>' % (style, _lines(text))


def _useful(text):
    """মুখে বলার মতো কিছু আছে কি — নাকি কেবল ইমোজি?"""
    t = _norm(text)
    return bool(t) and not EMOJI_ONLY.match(t)


def _collect(lesson):
    """স্লাইডগুলো থেকে কাঁচামাল — আরবি, অর্থ, বাড়ির কাজ।"""
    arabics = []      # যে ক্রমে পর্দায় এসেছে (একবারই)
    seen = set()
    joined = set()    # যেগুলো একাধিক লাইনে ছিল = "একসাথে পড়া"
    meanings = {}     # কোন আরবির সাথে কোন ব্যাখ্যা
    home = []
    write = []        # খাতায় কী কী লিখতে হবে
    longest_multi = ""

    for st in lesson.steps.all().select_related("slide").order_by("order",
                                                                  "id"):
        if not st.is_active:
            continue
        sl = getattr(st, "slide", None)
        if sl is None or sl.kind in SKIP_KINDS:
            continue

        ar = _norm(sl.arabic)
        if ar and ar not in seen:
            seen.add(ar)
            arabics.append(ar)
        # একাধিক লাইনের আরবি = পুরো অংশটি একসাথে, টুকরো নয়
        if ar and (sl.arabic or "").strip().count(chr(10)) >= 1:
            joined.add(ar)
            if len(sl.arabic) > len(longest_multi):
                longest_multi = sl.arabic

        if sl.kind in MEANING_KINDS and _useful(sl.text) and ar:
            meanings.setdefault(ar, sl.text)
        if sl.kind in HOME_KINDS and _useful(sl.text):
            home.append(sl.text)
        # লেখার ধাপে আরবিটাই আসল — কী লিখতে হবে। সাথে ছোট নির্দেশনা।
        if sl.kind in WRITE_KINDS and ar:
            write.append((ar, sl.text if _useful(sl.text) else ""))

    return arabics, joined, meanings, home, write, longest_multi


def _inside(small, big):
    """small-এর শব্দগুলো big-এর ভেতরে পরপর বসে আছে কি?

    ⚠️ অক্ষর ধরে মেলানো যায় না — কায়দার হরফ "ا" প্রায় প্রতিটি আরবি
    শব্দের ভেতরেই থাকে (যেমন "الحروف")। তাতে সব গুলিয়ে যেত: একটিমাত্র
    হরফ সূরার টুকরো হয়ে বসত। তাই শব্দ ধরে মেলানো, আর পরপর বসা শব্দ
    হলেই কেবল।
    """
    a, b = small.split(), big.split()
    if not a or len(a) >= len(b):
        return False
    return any(b[i:i + len(a)] == a for i in range(len(b) - len(a) + 1))


def _group(arabics, joined):
    """টুকরো আর পুরোটা আলাদা করা।

    গড়ন-নিরপেক্ষ নিয়ম: যে লেখাটি অন্য কোনো লেখার ভেতরে বসে না, সেটিই
    "পুরোটা"; আর যেগুলো তার ভেতরে বসে, সেগুলো তার "টুকরো"। ফলে পরিচালক
    নতুন যে দারসই লিখুন, কাজ করবে।

    ⚠️ একাধিক লাইনের আরবি (পুরো সূরা একসাথে) এই ভাগাভাগির বাইরে — সেটি
    উপরের বাক্সেই দেখানো হয়। নইলে সেটিই সবাইকে টুকরো বানিয়ে ফেলত আর
    আয়াতভিত্তিক ভাগটাই হারিয়ে যেত।
    """
    pool = [a for a in arabics if a not in joined]
    wholes = [a for a in pool if not any(_inside(a, b) for b in pool if b != a)]
    groups = []
    for w in wholes:
        pieces = [p for p in pool if p not in wholes and _inside(p, w)]
        # ⚠️ টুকরোর ভেতরের টুকরো বাদ — "هُوَ ٱللَّهُ" থাকলে আলাদা করে
        # "ٱللَّهُ" দেখানোর দরকার নেই, চোখে বাড়তি ঠেকে
        pieces = [x for x in pieces
                  if not any(_inside(x, y) for y in pieces if y != x)]
        groups.append({"whole": w, "pieces": pieces})
    return groups


def summary_html(lesson):
    """দারসটির স্লাইড থেকে শিক্ষার্থীর অনুশীলনের কাগজ।"""
    arabics, joined, meanings, home, write, full = _collect(lesson)
    if not arabics and not home:
        return ""

    groups = _group(arabics, joined)
    # পুরোটা একসাথে যদি আলাদা করে না থাকে, দলগুলোর "পুরোটা" জুড়েই বানাই
    if not full and groups:
        full = "\n".join(g["whole"] for g in groups)

    out = []

    # ───── ১. আজ যা শেখা হয়েছে — লেকচার প্ল্যানের চেহারা ─────
    if full:
        out.append(
            '<div style="%s"><div style="%s">📖 What we learned today</div>'
            '<div dir="rtl" style="text-align:center;direction:rtl">'
            '%s</div></div>'
            % (CARD % ("#cfe7d8", "#f3fbf6"), HEAD % "#1a5c3a", _ar(full))
        )

    # ───── ২. এভাবে অনুশীলন করো — প্রতিটি অংশ নিজের বাক্সে ─────
    rows = []
    n = 0
    for g in groups:
        n += 1
        bits = ['<div style="%s">%d</div>' % (NUM, n)]
        # টুকরোগুলো — এক পট্টিতে, মাঝে বিন্দু দিয়ে আলাদা করা
        if g["pieces"]:
            bits.append(
                '<div dir="rtl" style="%s">%s</div>'
                % (PIECE_ROW,
                   " &nbsp;·&nbsp; ".join(_ar(p, PIECE_STYLE)
                                          for p in g["pieces"]))
            )
        bits.append('<div dir="rtl" style="%s">%s</div>'
                    % (WHOLE_ROW, _ar(g["whole"])))
        # ⚠️ ব্যাখ্যা কখনো পুরোটার সাথে, কখনো টুকরোর সাথে জড়ানো থাকে
        # (যেমন কায়দার "ت না ث?" তুলনা) — দুটোই দেখাই, নইলে হারিয়ে যেত
        notes = []
        if meanings.get(g["whole"]):
            notes.append(meanings[g["whole"]])
        for pc in g["pieces"]:
            if meanings.get(pc) and meanings[pc] not in notes:
                notes.append(meanings[pc])
        for note in notes:
            bits.append('<div style="%s">%s</div>' % (MEAN_ROW, _lines(note)))
        rows.append('<div style="%s">%s</div>'
                    % (CARD % ("#eadfc8", "#fffdf7"), "".join(bits)))

    if rows:
        # ⚠️ শিরোনামটুকুই আমাদের — ভেতরের প্রতিটি কথা স্লাইড থেকে আসা।
        # ক্লাসে যা ছিল না, তার একটি অক্ষরও এখানে আসে না।
        out.append('<div style="%s">🎤 Practise</div>' % (HEAD % "#c9962a"))
        out.extend(rows)

    # ───── ৩. খাতায় লেখা ─────
    # ⚠️ একই আরবি একাধিক ধাপে এলে একবারই দেখাই
    if write:
        seen_w = set()
        rows_w = []
        for ar, hint in write:
            if ar in seen_w:
                continue
            seen_w.add(ar)
            bits = ['<div dir="rtl" style="%s">%s</div>'
                    % (WHOLE_ROW, _ar(ar))]
            if hint:
                bits.append('<div style="%s">%s</div>'
                            % (MEAN_ROW, _lines(hint)))
            rows_w.append("".join(bits))
        out.append(
            '<div style="%s"><div style="%s">✏️ Write in your notebook</div>'
            "%s</div>"
            % (CARD % ("#cfe0ea", "#f4fafd"), HEAD % "#175066",
               "".join(rows_w))
        )

    # ───── ৪. বাড়িতে ─────
    if home:
        out.append(
            '<div style="%s"><div style="%s">📌 At home</div>'
            '<div style="font-size:14px;line-height:1.9">%s</div></div>'
            % (CARD % ("#eeddb4", "#fdf6e7"), HEAD % "#8a6d1f",
               "<br>".join(_lines(h) for h in home))
        )

    # ⚠️ শেষে ছাঁকনি — কোডবেসের বাকি রিচ-টেক্সটের মতোই, যাতে কখনো কোনো
    # অনুমোদনহীন ট্যাগ শিক্ষার্থীর পাতায় না যায়
    return clean_html("".join(out)[:100000])
