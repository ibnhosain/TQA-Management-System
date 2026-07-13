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
            # একই আইডি/ইমেইল/নম্বর একাধিক অ্যাকাউন্টে থাকলেও —
            # যার পাসওয়ার্ড মেলে তাকেই বেছে নিই (নইলে ভুল অ্যাকাউন্ট বেছে fail করত)
            chosen = next((u for u in candidates if u.check_password(pwd)), None) \
                or (candidates[0] if candidates else None)
            if chosen:
                attrs[self.username_field] = chosen.username
        return super().validate(attrs)


class FlexTokenObtainPairView(TokenObtainPairView):
    serializer_class = FlexTokenObtainPairSerializer
