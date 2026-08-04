"""
TQA-MS — Web Push নোটিফিকেশন (core/push.py)

ব্রাউজার/অ্যাপ বন্ধ থাকা অবস্থাতেও ফোন/পিসিতে নোটিফিকেশন পাঠাতে ব্যবহৃত হয়।
VAPID_PRIVATE_KEY environment variable এ PEM ফরম্যাটে রাখা থাকবে
(python manage.py generate_vapid_keys দিয়ে একবার তৈরি করে Render dashboard-এ বসান)।
"""
import base64
import json
import os

from py_vapid import Vapid02


def _vapid():
    pem = os.environ.get("VAPID_PRIVATE_KEY", "")
    if not pem:
        return None
    try:
        return Vapid02.from_pem(pem.encode())
    except Exception:
        return None


def public_key_b64():
    """ফ্রন্টএন্ডকে দেওয়ার জন্য পাবলিক কী (PushManager.subscribe-এ লাগে) — কোনো
    গোপনীয়তা নেই, প্রাইভেট কী থেকেই বের করা"""
    vapid = _vapid()
    if not vapid:
        return None
    from cryptography.hazmat.primitives import serialization
    raw = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def send_push(users, title, body, url="/"):
    """`users` — User queryset/list। প্রতিটার সব ডিভাইসে (একাধিক সাবস্ক্রিপশন
    থাকতে পারে) পুশ পাঠানোর চেষ্টা করে; মেয়াদোত্তীর্ণ/অকেজো সাবস্ক্রিপশন
    পাওয়া গেলে (404/410) সাথে সাথে ডাটাবেজ থেকে মুছে ফেলে।"""
    vapid = _vapid()
    if not vapid:
        return  # VAPID কনফিগার করা না থাকলে চুপচাপ কিছু করে না (ইন-অ্যাপ নোটিফিকেশন ঠিকই কাজ করবে)

    from pywebpush import webpush, WebPushException
    from .models import PushSubscription

    user_ids = [u.id for u in users] if hasattr(users, "__iter__") else [users.id]
    subs = PushSubscription.objects.filter(user_id__in=user_ids)
    payload = json.dumps({"title": title, "body": body, "url": url})
    dead_ids = []
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=vapid,
                vapid_claims={"sub": "mailto:admin@tarbiyatulquran.org"},
                timeout=10,
            )
        except WebPushException as e:
            status = getattr(e.response, "status_code", None)
            if status in (404, 410):  # সাবস্ক্রিপশন আর বৈধ নেই (আনইনস্টল/মেয়াদ শেষ)
                dead_ids.append(sub.id)
        except Exception:
            pass  # নেটওয়ার্ক/সাময়িক সমস্যা — পরের নোটিফিকেশনে আবার চেষ্টা হবে
    if dead_ids:
        PushSubscription.objects.filter(id__in=dead_ids).delete()
