"""TQA-MS — সহায়ক ফাংশন (core/utils.py)"""
from django.utils.crypto import get_random_string

# বিভ্রান্তিকর অক্ষর বাদ (0/O, 1/l/I) — WhatsApp এ পাঠানো ও টাইপ করা সহজ হয়
_PW_CHARS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def make_password_str(length=8):
    """র‍্যান্ডম পাসওয়ার্ড — Django 5.1+ এ সরিয়ে দেওয়া User.objects.make_random_password() এর বিকল্প"""
    return get_random_string(length, _PW_CHARS)
