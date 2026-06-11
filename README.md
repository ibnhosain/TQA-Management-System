# তারবিয়াতুল কুরআন একাডেমি — ম্যানেজমেন্ট সিস্টেম

```
tqa-clean/
├── backend/          → Django REST API
├── frontend/         → React + Vite
└── whatsapp-server/  → Node.js WhatsApp Server
```

## 🔑 Environment Variable কিভাবে কাজ করে

প্রতিটা ফোল্ডারে দুটো ফাইল আছে:

| ফাইল | কাজ | GitHub এ যায়? |
|------|-----|---------------|
| `.env` | আসল secret value (local এ চলার জন্য) | ❌ না (.gitignore) |
| `.env.example` | নমুনা/template | ✅ হ্যাঁ |

**Local এ:** `.env` ফাইল আগে থেকেই বানানো আছে — শুধু value বসান।
**Hosting এ:** `.env` ফাইল লাগে না — Railway/Render dashboard এর
**Environment Variables** section এ একই নামের value গুলো বসান।

---

## 🐍 Backend চালানো (Local)

```bash
cd backend
python -m venv venv
venv\Scripts\activate              # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver         # → http://localhost:8000
```

`.env` আগে থেকেই আছে, local এ কিছু বদলাতে হবে না।

### Celery (WhatsApp reminder এর জন্য, ঐচ্ছিক)
```bash
celery -A tqa_backend worker -B -l info    # Redis চালু থাকতে হবে
```

---

## ⚛️ Frontend চালানো (Local)

```bash
cd frontend
npm install
npm run dev        # → http://localhost:5173
```

---

## 📱 WhatsApp Server (Local)

```bash
cd whatsapp-server
npm install
# .env এ আপনার META_ACCESS_TOKEN বসান (regenerate করা নতুনটা!)
npm start          # → http://localhost:3001
```

---

## 🚀 ফ্রি Hosting — সম্পূর্ণ ধাপ

**আর্কিটেকচার (সব ফ্রি, Celery/Redis লাগবে না):**

| অংশ | কোথায় | কাজ |
|------|--------|-----|
| Frontend | Vercel | tarbiyatulquran.org এর subdomain এ |
| Backend | Render | Django API |
| Database | Render PostgreSQL | ডেটা |
| Scheduled কাজ | cron-job.org | reminder/dues (Celery র বদলে) |
| Sleep ঠেকানো | UptimeRobot | প্রতি ৫ মিনিটে ping |

### ধাপ ১: Backend → Render (render.com)

1. GitHub দিয়ে sign up করুন
2. **New → PostgreSQL** → ফ্রি plan → তৈরি হলে **Internal Database URL** copy করুন
3. **New → Web Service** → আপনার repo connect → Root Directory: `backend`
4. Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
5. Start Command: `gunicorn tqa_backend.wsgi --bind 0.0.0.0:$PORT`
6. **Environment Variables** এ বসান:
   - `SECRET_KEY` → `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DEBUG` → `False`
   - `ALLOWED_HOSTS` → `আপনার-app.onrender.com,api.tarbiyatulquran.org`
   - `DATABASE_URL` → PostgreSQL এর Internal URL
   - `CORS_ALLOWED_ORIGINS` → `https://tarbiyatulquran.org` (frontend যেখানে)
   - `CRON_SECRET` → `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `USE_CELERY` → `False`
   - WhatsApp সরাসরি Django থেকে পাঠাতে: `WHATSAPP_PROVIDER`, `META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID`
7. Deploy শেষে Render এর **Shell** tab এ: `python manage.py createsuperuser`

### ধাপ ২: Frontend → Vercel (vercel.com)

1. GitHub দিয়ে sign up → repo import → Root Directory: `frontend`
2. Framework: Vite (নিজেই ধরবে)
3. **Environment Variables**: `VITE_API_URL` → `https://আপনার-app.onrender.com/api`
4. Deploy → একটা `xyz.vercel.app` URL পাবেন

### ধাপ ৩: নিজের Domain যুক্ত করা (Namecheap)

ধরা যাক ঠিক করলেন:
- `app.tarbiyatulquran.org` → ম্যানেজমেন্ট সিস্টেম (Vercel)
- `api.tarbiyatulquran.org` → Backend (Render)

**Vercel এ:** Project → Settings → Domains → `app.tarbiyatulquran.org` add করুন।
Vercel একটা CNAME value দেখাবে।

**Render এ:** Web Service → Settings → Custom Domains → `api.tarbiyatulquran.org` add।

**Namecheap এ:** Domain List → Manage → **Advanced DNS** → দুটো record:

| Type | Host | Value |
|------|------|-------|
| CNAME | app | cname.vercel-dns.com |
| CNAME | api | আপনার-app.onrender.com |

১০-৩০ মিনিটে চালু হবে। তারপর `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`,
`VITE_API_URL` এ নতুন domain গুলো আপডেট করুন।

⚠️ মূল সাইট (tarbiyatulquran.org) GitHub Pages এ যেমন আছে তেমনই থাকবে —
আমরা শুধু নতুন subdomain যোগ করছি, পুরনো কিছুতে হাত দিচ্ছি না।

### ধাপ ৪: Scheduled কাজ → cron-job.org (ফ্রি)

Sign up করে ৩টা cronjob বানান (URL এর `<SECRET>` = আপনার CRON_SECRET):

| কাজ | URL | Schedule |
|-----|-----|----------|
| ক্লাস রিমাইন্ডার | `https://api.tarbiyatulquran.org/api/cron/reminders/?key=<SECRET>` | প্রতি মিনিটে |
| রুটিন → ক্লাস | `https://api.tarbiyatulquran.org/api/cron/daily/?key=<SECRET>` | প্রতিদিন 02:00 |
| মাসিক বকেয়া | `https://api.tarbiyatulquran.org/api/cron/monthly/?key=<SECRET>` | মাসের ১ তারিখ 05:00 |

বোনাস: প্রতি-মিনিটের ping টাই server কে জাগিয়ে রাখে!

### ধাপ ৫: UptimeRobot (uptimerobot.com) — বাড়তি সুরক্ষা

Monitor বানান: `https://api.tarbiyatulquran.org/api/cron/reminders/?key=<SECRET>`
→ interval ৫ মিনিট। (cron-job.org কোনোদিন miss করলেও server জেগে থাকবে)

---

## 🔓 লগইন কিভাবে করবেন

Deploy শেষ হলে:

1. **Admin Panel:** `https://api.tarbiyatulquran.org/admin/`
   → createsuperuser দিয়ে বানানো username/password
2. এখানে গিয়ে শিক্ষক/ছাত্রদের User account বানান (role সহ)
3. **মূল অ্যাপ:** `https://app.tarbiyatulquran.org`
   → admin এ বানানো username/password দিয়ে সবাই লগইন করবে

---

## 💰 পরে টাকা দিতে চাইলে

Render Starter ($7/মাস) নিলে sleep নেই + Celery worker চালানো যায়।
তখন `USE_CELERY=True` করে worker service add করলেই Celery মোডে চলবে —
কোড বদলাতে হবে না।
