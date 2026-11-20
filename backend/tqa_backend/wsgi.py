import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tqa_backend.settings')

application = get_wsgi_application()

# সার্ভারের নিজের পাহারাদার — রোজের ক্লাস ও মাসিক বকেয়া (core/scheduler.py)
from core.scheduler import start as _start_scheduler  # noqa: E402

_start_scheduler()
