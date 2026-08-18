"""
Student ID তৈরি — ফরম্যাট:  <নামের আদ্যাক্ষর>-<বাবার নামের আদ্যাক্ষর>-<দেশ>-<সিরিয়াল>
উদাহরণ:  SH-LC-US-007   (Saif Hossain · Lupa Choudhury · United States · ৭ নম্বর)

সব অংশই ইংরেজি অক্ষরে — নাম বাংলায় লেখা থাকলেও আদ্যাক্ষর ইংরেজিতে রূপান্তর
করা হয় (মুহাম্মদ রিয়াদ → MR), যাতে সব স্টুডেন্টের আইডি একই রকম দেখায় এবং
ইংরেজি কি-বোর্ডেই টাইপ/খোঁজা যায়।
"""
import re

from ._country_iso import COUNTRY_ISO

# বাংলা অক্ষরের প্রথম বর্ণ → ইংরেজি অনুমান (শুধু আদ্যাক্ষরের জন্য, তাই এক অক্ষরই যথেষ্ট)
BN_TO_EN = {
    "অ": "A", "আ": "A", "ই": "I", "ঈ": "I", "উ": "U", "ঊ": "U", "ঋ": "R",
    "এ": "E", "ঐ": "O", "ও": "O", "ঔ": "O",
    "ক": "K", "খ": "K", "গ": "G", "ঘ": "G", "ঙ": "N",
    "চ": "C", "ছ": "C", "জ": "J", "ঝ": "J", "ঞ": "N",
    "ট": "T", "ঠ": "T", "ড": "D", "ঢ": "D", "ণ": "N",
    "ত": "T", "থ": "T", "দ": "D", "ধ": "D", "ন": "N",
    "প": "P", "ফ": "F", "ব": "B", "ভ": "V", "ম": "M",
    "য": "J", "র": "R", "ল": "L", "শ": "S", "ষ": "S", "স": "S",
    "হ": "H", "ড়": "R", "ঢ়": "R", "য়": "Y", "ৎ": "T",
}

def _initial(word):
    """একটি শব্দের প্রথম অক্ষরকে ইংরেজি বড় হাতের এক অক্ষরে রূপান্তর"""
    if not word:
        return ""
    ch = word[0]
    if ch in BN_TO_EN:
        return BN_TO_EN[ch]
    if ch.isascii() and ch.isalpha():
        return ch.upper()
    # অন্য কোনো লিপি/চিহ্ন — বাদ
    return ""


def initials(full_name, count=2):
    """নাম থেকে সর্বোচ্চ `count` টি ইংরেজি আদ্যাক্ষর — 'Saif Hossain' → 'SH'"""
    words = [w for w in re.split(r"[\s.\-_]+", (full_name or "").strip()) if w]
    out = "".join(_initial(w) for w in words)[:count]
    return out or "X"


def country_code(country):
    """দেশের নাম → ২-অক্ষরের কোড। '(USA)'-এর মতো বাড়তি অংশ থাকলেও মিলিয়ে নেয়।"""
    c = (country or "").strip()
    if not c:
        return "XX"
    if c in COUNTRY_ISO:
        return COUNTRY_ISO[c]
    # "United States (USA)" → "United States" ধরে আবার চেষ্টা
    base = re.sub(r"\s*\(.*?\)\s*", "", c).strip()
    if base in COUNTRY_ISO:
        return COUNTRY_ISO[base]
    # বড়/ছোট হাতের পার্থক্য উপেক্ষা করে
    for name, iso in COUNTRY_ISO.items():
        if name.lower() == base.lower():
            return iso
    # তালিকায় না থাকলে (যেমন "অন্যান্য") — প্রথম দুই ইংরেজি অক্ষর, নইলে XX
    letters = "".join(ch for ch in base if ch.isascii() and ch.isalpha())
    return (letters[:2].upper() or "XX")


def build_student_id(name, guardian, country, serial):
    """চারটি অংশ মিলিয়ে চূড়ান্ত আইডি — SH-LC-US-007"""
    return "-".join([
        initials(name),
        initials(guardian),
        country_code(country),
        f"{int(serial):03d}",
    ])


def next_serial(User):
    """পরবর্তী সিরিয়াল — ইতিমধ্যে দেওয়া আইডিগুলোর শেষ সংখ্যার চেয়ে এক বেশি।
    কেউ মুছে গেলেও পুরনো সিরিয়াল আর ব্যবহার হয় না (ডুপ্লিকেট এড়াতে)।"""
    used = User.objects.filter(role="student").exclude(student_id="").values_list(
        "student_id", flat=True
    )
    top = 0
    for sid in used:
        m = re.search(r"(\d+)\s*$", sid or "")
        if m:
            top = max(top, int(m.group(1)))
    return top + 1


def assign_student_id(user, User=None):
    """একজন স্টুডেন্টের জন্য আইডি তৈরি করে বসিয়ে দেয় (আগে থেকে থাকলে কিছু করে না)।
    একই আইডি অন্য কারো থাকলে সিরিয়াল বাড়িয়ে অনন্য করা হয়।"""
    if user.student_id:
        return user.student_id
    User = User or type(user)
    serial = next_serial(User)
    for _ in range(100):  # নিরাপত্তা-সীমা, বাস্তবে প্রথমবারেই মিলে যায়
        sid = build_student_id(user.name_bn, user.guardian, user.country, serial)
        if not User.objects.filter(student_id=sid).exists():
            user.student_id = sid
            return sid
        serial += 1
    return ""
