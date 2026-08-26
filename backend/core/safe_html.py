"""পরিচালকের লেখা সাজানো টেক্সট (HTML) নিরাপদ করে নেওয়ার ছাঁকনি।

কেন দরকার: টগলের ভেতরের লেখা HTML হিসেবে সংরক্ষণ হয় আর উস্তাদ-শিক্ষার্থীর
পর্দায় HTML হিসেবেই দেখানো হয়। কোনোভাবে <script>, onclick=, javascript:
ইত্যাদি ঢুকে গেলে তা সবার ব্রাউজারে চলে যেত। তাই সার্ভারে ঢোকার মুখেই
অনুমোদিত-তালিকা (allowlist) ধরে ছেঁকে নেওয়া হয় — তালিকায় নেই এমন সবকিছু
বাদ, শুধু ভেতরের লেখাটুকু থাকে।

নতুন কোনো লাইব্রেরি যোগ করা হয়নি — পাইথনের নিজের HTMLParser দিয়েই।
"""
import re
from html import escape
from html.parser import HTMLParser

# যে ট্যাগগুলো থাকতে পারে
ALLOWED_TAGS = {
    "b", "strong", "i", "em", "u", "s", "strike", "br", "p", "div", "span",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "blockquote", "pre", "code",
    "table", "thead", "tbody", "tr", "td", "th", "a", "img", "figure",
    "figcaption", "hr",
    # ⚠️ ব্রাউজার সাজসজ্জা দুইভাবে লিখতে পারে — <span style="..."> অথবা
    # পুরনো ধাঁচের <font face size color>। আমরা এডিটরে প্রথমটাই চালু করে
    # রেখেছি (styleWithCSS), তবু কোনো ব্রাউজার সেটা না মানলে যেন লেখার সাজ
    # নিঃশব্দে মুছে না যায় — তাই <font>-ও গ্রহণ করা হয়। এটি নিছক
    # সাজসজ্জার ট্যাগ, কোনো স্ক্রিপ্ট চালাতে পারে না।
    "font",
}
# যে ট্যাগগুলোর বন্ধ-ট্যাগ লাগে না
VOID_TAGS = {"br", "img", "hr"}
# ট্যাগ-প্রতি অনুমোদিত অ্যাট্রিবিউট
ALLOWED_ATTRS = {
    "*": {"style", "dir"},
    "a": {"href", "target", "rel"},
    "img": {"src", "alt", "width", "height"},
    "font": {"face", "size", "color"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}
# style-এ যে বৈশিষ্ট্যগুলো থাকতে পারে
ALLOWED_STYLES = {
    "color", "background-color", "font-size", "font-family", "font-weight",
    "font-style", "text-decoration", "text-align", "direction", "line-height",
    "margin", "padding", "width", "height", "max-width", "border",
    "border-collapse", "vertical-align", "white-space",
    # ছবি সাজানোর জন্য — বাঁয়ে/ডানে ভাসানো, মাঝবরাবর বসানো, আকার ও কোণ।
    # সবগুলোই কেবল সাজসজ্জার, কোনোটিতেই স্ক্রিপ্ট চালানোর সুযোগ নেই।
    # ⚠️ এগুলো অনুমোদিত না থাকায় সংরক্ষণের সময় ছবির সাজ মুছে যেত, তাই
    # ছবি বসানোর পর আর নাড়াচাড়া করা যেত না।
    "float", "clear", "display", "border-radius",
    "margin-left", "margin-right", "margin-top", "margin-bottom",
    "object-fit",
}
# style-এর মানে যা কখনোই থাকতে পারবে না (url(), expression() দিয়ে আক্রমণ হয়)
_BAD_VALUE = re.compile(r"(expression|javascript:|url\s*\(|@import|/\*)", re.I)
_SAFE_URL = re.compile(r"^(https?:|mailto:|/|data:image/(png|jpe?g|gif|webp);base64,)", re.I)


def _clean_style(value):
    out = []
    for part in (value or "").split(";"):
        if ":" not in part:
            continue
        name, _, val = part.partition(":")
        name, val = name.strip().lower(), val.strip()
        if name in ALLOWED_STYLES and val and not _BAD_VALUE.search(val):
            out.append(f"{name}: {val}")
    return "; ".join(out)


class _Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.open_stack = []

    def _attrs(self, tag, attrs):
        allowed = ALLOWED_ATTRS.get("*", set()) | ALLOWED_ATTRS.get(tag, set())
        out = []
        for name, value in attrs:
            name = (name or "").lower()
            if name not in allowed or value is None:
                continue
            if name == "style":
                value = _clean_style(value)
                if not value:
                    continue
            elif name in ("href", "src"):
                if not _SAFE_URL.match(value.strip()):
                    continue
            elif _BAD_VALUE.search(value):
                continue
            out.append(f' {name}="{escape(value, quote=True)}"')
        # বাইরের লিংক নতুন ট্যাবে, আর opener ফাঁস ঠেকাতে
        if tag == "a":
            out.append(' target="_blank" rel="noopener noreferrer"')
        return "".join(out)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            return  # ট্যাগটা বাদ, ভেতরের লেখা থেকে যাবে
        if tag in VOID_TAGS:
            self.parts.append(f"<{tag}{self._attrs(tag, attrs)}>")
        else:
            self.parts.append(f"<{tag}{self._attrs(tag, attrs)}>")
            self.open_stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if tag in ALLOWED_TAGS:
            self.parts.append(f"<{tag}{self._attrs(tag, attrs)}>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ALLOWED_TAGS and tag not in VOID_TAGS and tag in self.open_stack:
            # শেষ যেটা খোলা হয়েছিল সেটা পর্যন্ত বন্ধ করি
            while self.open_stack:
                t = self.open_stack.pop()
                self.parts.append(f"</{t}>")
                if t == tag:
                    break

    def handle_data(self, data):
        self.parts.append(escape(data, quote=False))

    def result(self):
        while self.open_stack:  # খোলা রয়ে যাওয়া ট্যাগ বন্ধ করে দিই
            self.parts.append(f"</{self.open_stack.pop()}>")
        return "".join(self.parts)


def clean_html(value):
    """অনুমোদিত-তালিকা ধরে ছেঁকে নিরাপদ HTML ফেরত দেয়।"""
    if not value:
        return ""
    # <script>/<style> এর ভেতরের লেখাটুকুও যেন না থাকে — HTMLParser ওগুলোর
    # ভেতরটা data হিসেবে দিয়ে দেয়, তাই আগেই পুরোটা তুলে ফেলি
    value = re.sub(r"(?is)<(script|style|iframe|object|embed)\b.*?</\1\s*>", "", value)
    value = re.sub(r"(?is)<(script|style|iframe|object|embed)\b[^>]*>", "", value)
    c = _Cleaner()
    c.feed(value)
    c.close()
    return c.result()
