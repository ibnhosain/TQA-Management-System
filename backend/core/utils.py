"""TQA-MS — সহায়ক ফাংশন (core/utils.py)"""
from django.utils.crypto import get_random_string

# বিভ্রান্তিকর অক্ষর বাদ (0/O, 1/l/I) — WhatsApp এ পাঠানো ও টাইপ করা সহজ হয়
_PW_CHARS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def make_password_str(length=8):
    """র‍্যান্ডম পাসওয়ার্ড — Django 5.1+ এ সরিয়ে দেওয়া User.objects.make_random_password() এর বিকল্প"""
    return get_random_string(length, _PW_CHARS)


def make_trial_username(User):
    """ট্রায়ালের সাময়িক আইডি — TQ-TRIAL-0007 ধাঁচে।

    সংখ্যাটা বর্তমান ট্রায়াল সংখ্যার পরেরটা থেকে শুরু, আর ওই নামে কেউ থাকলে
    (পুরনো ট্রায়াল মুছে গেলে বা নাম বদলালে) এগিয়ে গিয়ে পরের খালি নম্বর নেয় —
    তাই দুজনের আইডি কখনো এক হবে না।
    """
    n = User.objects.filter(role="trial").count() + 1
    for _ in range(1000):
        name = f"TQ-TRIAL-{n:04d}"
        if not User.objects.filter(username__iexact=name).exists():
            return name
        n += 1
    raise RuntimeError("ট্রায়াল আইডি তৈরি করা যায়নি")
