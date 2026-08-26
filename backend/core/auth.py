"""
TQA-MS — নমনীয় লগইন (core/auth.py)

ব্যবহারকারী আইডি (username), ইমেইল বা মোবাইল নম্বর — যেকোনোটা দিয়েই
লগইন করতে পারবে। যা-ই লিখুক, আমরা আগে user টা খুঁজে বের করি,
তারপর তার আসল username দিয়ে স্বাভাবিক JWT যাচাই চালাই।
"""
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class FlexTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        ident = (attrs.get(self.username_field) or "").strip()
        pwd = attrs.get("password") or ""
        if ident:
            from .models import User
            candidates = list(User.objects.filter(
                Q(username__iexact=ident) | Q(email__iexact=ident) | Q(phone=ident)
            ))
            # একটিমাত্র মিল (সাধারণ ক্ষেত্র) → সরাসরি সেটি; check_password এখানে চালাই না,
            # super().validate() একবারই হ্যাশ যাচাই করবে। আগে এখানেও check_password চলত →
            # মোট দুইবার হ্যাশ → Render ফ্রি-র দুর্বল CPU-তে লগইন দ্বিগুণ ধীর হতো।
            if len(candidates) == 1:
                attrs[self.username_field] = candidates[0].username
            elif candidates:
                # একই আইডি/ইমেইল/নম্বর একাধিক অ্যাকাউন্টে — যার পাসওয়ার্ড মেলে তাকে বেছে নিই
                chosen = next((u for u in candidates if u.check_password(pwd)), candidates[0])
                attrs[self.username_field] = chosen.username
        data = super().validate(attrs)
        # ট্রায়ালের মেয়াদ ফুরালে আর ঢোকা যাবে না। পাসওয়ার্ড যাচাইয়ের পরে
        # দেখা হয়, তাই ভুল পাসওয়ার্ড দিয়ে কেউ বুঝতে পারবেন না কোন আইডি
        # ট্রায়ালের আর কোনটা নয়।
        # ⚠️ পরে (ধাপ ৫) এটি বদলে যাবে — তখন মেয়াদ শেষ হলেও ঢোকা যাবে,
        # তবে শুধু নিজের রিপোর্ট ও ভর্তির প্রস্তাব দেখার জন্য।
        if getattr(self.user, "trial_expired", False):
            from rest_framework_simplejwt.exceptions import AuthenticationFailed
            raise AuthenticationFailed(
                "আপনার ট্রায়ালের মেয়াদ শেষ হয়েছে। ভর্তির ব্যাপারে জানতে "
                "একাডেমিতে যোগাযোগ করুন।")
        return data


class FlexTokenObtainPairView(TokenObtainPairView):
    serializer_class = FlexTokenObtainPairSerializer
