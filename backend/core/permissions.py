"""TQA-MS — রোলভিত্তিক অনুমতি (RBAC) — ফ্রন্টএন্ডের isDir/isAdm এর সার্ভার সংস্করণ"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsDirector(BasePermission):
    """কেবল পরিচালক — ম্যানেজ সেটিংস, হিসাব-নিকাশ, কোর্স, ফি ভেরিফাই, ভর্তি গ্রহণ"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "director"


class IsAdminLevel(BasePermission):
    """পরিচালক + এডমিন — একাডেমিক নিয়ন্ত্রণ"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("director", "admin")


class IsTeacherOrAdminLevel(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("director", "admin", "teacher")


class ReadAllWriteAdmin(BasePermission):
    """সবাই পড়তে পারবে; লেখা কেবল এডমিন-লেভেল"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in ("director", "admin")


class ReadAllWriteDirector(BasePermission):
    """সবাই পড়তে পারবে; লেখা কেবল পরিচালক (কোর্স, সিলেবাস, লেকচার তৈরি, একাডেমিক বই)"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == "director"
