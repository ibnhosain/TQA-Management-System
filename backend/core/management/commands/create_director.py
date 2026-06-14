import os
from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = "পরিচালক অ্যাকাউন্ট তৈরি করে (না থাকলে) — Render build এ ব্যবহৃত"

    def handle(self, *args, **kwargs):
        username = os.environ.get("DIRECTOR_USERNAME", "")
        password = os.environ.get("DIRECTOR_PASSWORD", "")
        name_bn  = os.environ.get("DIRECTOR_NAME", "পরিচালক")

        if not username or not password:
            self.stdout.write("⚠️  DIRECTOR_USERNAME বা DIRECTOR_PASSWORD নেই — বাদ দেওয়া হলো।")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"✔ '{username}' আগেই আছে — নতুন করে তৈরি হয়নি।")
            return

        User.objects.create_superuser(
            username=username,
            password=password,
            role="director",
            name_bn=name_bn,
        )
        self.stdout.write(self.style.SUCCESS(f"✅ পরিচালক '{username}' সফলভাবে তৈরি হয়েছে।"))
