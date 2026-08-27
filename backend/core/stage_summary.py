# -*- coding: utf-8 -*-
"""স্ক্রিপ্ট থেকে দারস পরিকল্পনার টগলের লেখা তৈরি।

উদ্দেশ্য — পরিচালককে যেন টগলের ভেতরের লেখা আলাদা করে লিখতে না হয়।
স্ক্রিপ্ট একবার লিখলেই "আজ কী কী পড়ানো হয়েছে" তৈরি হয়ে যায়, আর
শিক্ষার্থী পরে সেটা দেখে রিভিশন দিতে পারে।

⚠️ সবচেয়ে জরুরি নিয়ম — এই লেখাটি **শিক্ষার্থী পড়বেন**। তাই এটি তৈরি হয়
কেবল স্লাইড থেকে, অর্থাৎ ক্লাসে বাচ্চার পর্দায় যা ছিল ঠিক সেটুকু থেকেই।
উস্তাদের স্ক্রিপ্টের কোনো ঘর (teacher_says / teacher_does / student_does
/ expected / correction / note) এখানে ছোঁয়াও হয় না — পুরো ব্যবস্থার
দেয়ালটা এখানেও অটুট।

⚠️ বসানোর পরেও পরিচালক লেখাটি নিজের মতো করে সম্পাদনা করতে পারেন —
লেকচার প্ল্যানের টগলে, আগের মতোই। এটি কেবল শুরুটা করে দেয়।
"""
from html import escape

from .safe_html import clean_html

# যে স্লাইডগুলো কেবল ফাঁকা পর্দা — সারাংশে রাখার কিছু নেই
SKIP_KINDS = {"blank"}


def _lines(v):
    """একাধিক লাইনের লেখা → <br> দিয়ে জোড়া, নিরাপদে escape করে।"""
    return "<br>".join(escape(x) for x in str(v or "").split("\n") if x.strip())


def summary_html(lesson):
    """দারসটির স্লাইডগুলো থেকে টগলের লেখা।

    প্রতিটি ধাপ একটি অনুচ্ছেদ — শিরোনাম, আরবি, উচ্চারণ, পর্দার লেখা।
    যে ধাপে পর্দায় কিছুই ছিল না, সেটি বাদ যায়।
    """
    out = []
    for st in lesson.steps.all().order_by("order", "id"):
        if not st.is_active:
            continue
        sl = getattr(st, "slide", None)
        if sl is None or sl.kind in SKIP_KINDS:
            continue

        bits = []
        if sl.heading:
            bits.append("<b>%s</b>" % escape(sl.heading))
        if sl.arabic:
            # dir="rtl" — আরবি যেন ডান থেকে বাঁয়ে ঠিকভাবে বসে
            bits.append(
                '<span dir="rtl" style="font-size:19px;line-height:2">%s</span>'
                % _lines(sl.arabic)
            )
        if sl.translit:
            bits.append("<i>%s</i>" % escape(sl.translit))
        if sl.text:
            bits.append(_lines(sl.text))
        if sl.image:
            bits.append('<img src="%s" alt="">' % escape(sl.image))

        if bits:
            out.append("<p>%s</p>" % "<br>".join(bits))

    if not out:
        return ""
    # ⚠️ শেষে ছাঁকনি — কোডবেসের বাকি রিচ-টেক্সটের মতোই, যাতে কখনো কোনো
    # অনুমোদনহীন ট্যাগ শিক্ষার্থীর পাতায় না যায়
    return clean_html("".join(out)[:100000])
