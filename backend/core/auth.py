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
        if ident:
            from .models import User
            user = User.objects.filter(
                Q(username__iexact=ident) | Q(email__iexact=ident) | Q(phone=ident)
            ).first()
            if user:
                attrs[self.username_field] = user.username
        return super().validate(attrs)


class FlexTokenObtainPairView(TokenObtainPairView):
    serializer_class = FlexTokenObtainPairSerializer
