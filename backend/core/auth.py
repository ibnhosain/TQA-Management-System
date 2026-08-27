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

        """⚠️ আগে সবসময় নিজেরা একবার ব্যবহারকারী খুঁজতাম, তারপর JWT আবার
        খুঁজত — অর্থাৎ প্রতিটি লগইনে দুবার ডাটাবেজে যাওয়া। ডাটাবেজ দূরে
        (ভার্জিনিয়া) বলে প্রতিটি যাওয়া-আসায় ~২৩০ মিলিসেকেন্ড, তাই একটি
        বাড়তি প্রশ্ন মানেই লগইনে বাড়তি দেরি।

        বেশিরভাগ মানুষ নিজের আইডি দিয়েই লগইন করেন। তাই এখন আগে সোজা
        পথেই চেষ্টা হয় — সফল হলে একটিমাত্র খোঁজা। ব্যর্থ হলে তবেই
        ইমেইল/মোবাইল ধরে খুঁজি, ঠিক আগের মতোই।

        ⚠️ যাচাইয়ের নিয়ম এক বিন্দুও বদলায়নি — পাসওয়ার্ড মেলানো আগের
        মতোই super().validate() করে। এখানে কেবল ক্রম বদলেছে।"""
        if ident:
            try:
                return super().validate(attrs)
            except Exception:
                pass                 # আইডি দিয়ে হলো না — ইমেইল/মোবাইল দেখি

            from .models import User
            candidates = list(User.objects.filter(
                Q(username__iexact=ident) | Q(email__iexact=ident)
                | Q(phone=ident)
            ))
            # একটিমাত্র মিল (সাধারণ ক্ষেত্র) → সরাসরি সেটি; check_password
            # এখানে চালাই না, super().validate() একবারই হ্যাশ যাচাই করবে।
            # আগে এখানেও check_password চলত → মোট দুইবার হ্যাশ → দুর্বল
            # CPU-তে লগইন দ্বিগুণ ধীর হতো।
            if len(candidates) == 1:
                attrs[self.username_field] = candidates[0].username
            elif candidates:
                # একই আইডি/ইমেইল/নম্বর একাধিক অ্যাকাউন্টে — যার পাসওয়ার্ড
                # মেলে তাকে বেছে নিই
                chosen = next((u for u in candidates if u.check_password(pwd)),
                              candidates[0])
                attrs[self.username_field] = chosen.username
        data = super().validate(attrs)
        # ⚠️ মেয়াদ ফুরালেও ট্রায়াল অতিথি ঢুকতে পারেন — দরজা বন্ধ করে দেওয়া
        # সবচেয়ে সহজ, কিন্তু সবচেয়ে খারাপ ব্যবহার। তাঁর ক্লাস ও দারস
        # পরিকল্পনা সার্ভারেই সরে যায় (get_queryset), কিন্তু নিজের রিপোর্ট ও
        # ভর্তির প্রস্তাব থেকে যায় — কেউ ছয় মাস পরে ফিরে এলেও।
        return data


class FlexTokenObtainPairView(TokenObtainPairView):
    serializer_class = FlexTokenObtainPairSerializer
