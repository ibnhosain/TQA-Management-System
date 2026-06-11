# 🕌 TQA — WhatsApp Business API সেটআপ গাইড (Twilio / Meta)

ম্যানেজমেন্ট অ্যাপের "📤 WhatsApp মেসেজ" পেজ থেকে অভিভাবকের কাছে **সত্যিকারের অটো-সেন্ড** চালু করার ধাপগুলো।

---

## ধাপ ১ — প্রোভাইডার বাছাই করুন (যেকোনো একটা)

### পথ ক: Meta WhatsApp Cloud API (সরাসরি, ফ্রি টিয়ার আছে — সুপারিশকৃত)
1. https://developers.facebook.com → নতুন App বানান (Type: **Business**)
2. App-এ **WhatsApp** প্রোডাক্ট যোগ করুন → একটা টেস্ট নম্বর ফ্রি পাবেন
3. **API Setup** পেজ থেকে নিন:
   - `META_ACCESS_TOKEN` (System User দিয়ে permanent token বানানো ভালো)
   - `META_PHONE_NUMBER_ID`
4. নিজের আসল বিজনেস নম্বর যুক্ত করতে Meta Business ভেরিফিকেশন করুন
5. ⚠️ নিয়ম: ব্যবহারকারী আগে মেসেজ না দিলে (২৪ ঘণ্টার উইন্ডোর বাইরে) **approved template** লাগে — Manager-এ "class_reminder" নামে একটা টেমপ্লেট approve করিয়ে নিন

### পথ খ: Twilio (সেটআপ সহজ, পে-অ্যাজ-ইউ-গো)
1. https://www.twilio.com → অ্যাকাউন্ট → **Messaging → Try WhatsApp** (Sandbox দিয়ে শুরু)
2. Console থেকে নিন: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, WhatsApp নম্বর (`TWILIO_WHATSAPP_FROM`)
3. প্রোডাকশনে নিজের নম্বরের জন্য WhatsApp Sender অনুমোদন নিন

---

## ধাপ ২ — সার্ভার চালু করুন

```bash
# এই ৩টা ফাইল এক ফোল্ডারে রাখুন: whatsapp-server.js, package.json, .env
npm install

# .env ফাইল বানান (নমুনা whatsapp-server.js-এর ওপরের কমেন্টে আছে), যেমন:
# WHATSAPP_PROVIDER=meta
# META_ACCESS_TOKEN=EAAG...
# META_PHONE_NUMBER_ID=1234567890

npm start          # → http://localhost:3001
```

ব্রাউজারে `http://localhost:3001` খুললে `{ ok: true, ... }` দেখালেই সার্ভার ঠিক আছে।

**টেস্ট:**
```bash
curl -X POST http://localhost:3001/api/send-whatsapp \
  -H "Content-Type: application/json" \
  -d '{"to":"8801XXXXXXXXX","text":"আসসালামু আলাইকুম — TQA টেস্ট মেসেজ"}'
```

---

## ধাপ ৩ — ডেপ্লয় (ফ্রি)

**Render.com** (সুপারিশকৃত): New → Web Service → GitHub রিপো যুক্ত করুন → Build: `npm install`, Start: `npm start` → Environment ট্যাবে .env-এর ভেরিয়েবলগুলো বসান → ডেপ্লয় শেষে URL পাবেন, যেমন `https://tqa-whatsapp.onrender.com`

Railway.app বা VPS-ও চলবে। ⚠️ `.env` কখনো GitHub-এ push করবেন না (`.gitignore`-এ রাখুন)।

---

## ধাপ ৪ — অ্যাপের সাথে যুক্ত করুন

1. পরিচালক হিসেবে লগইন → **📤 WhatsApp মেসেজ** → ⚙️ API সংযোগ
2. ব্যাকএন্ড URL বসান (যেমন `https://tqa-whatsapp.onrender.com`)
3. **⚡ অটো-সেন্ড চালু** করুন

ব্যস! এরপর ক্লাস শুরুর ৫ মিনিট আগের রিমাইন্ডার আর ক্লাস স্থগিতের মেসেজ তৈরি হওয়ামাত্র সার্ভার সরাসরি অভিভাবকের WhatsApp-এ পাঠিয়ে দেবে। প্রতিটি মেসেজের পাশে স্ট্যাটাস দেখাবে: ⏳ যাচ্ছে → ✔ পাঠানো হয়েছে (API), আর ব্যর্থ হলে লাল ট্যাগ + ম্যানুয়াল wa.me বাটন তো আছেই।

---

## সমস্যা হলে
- **API ব্যর্থ ট্যাগ**: সার্ভারের লগ দেখুন (Render → Logs)। সাধারণ কারণ: ভুল token, নম্বরে কান্ট্রি কোড নেই, Meta-র ২৪-ঘণ্টা উইন্ডো (template লাগবে)
- **CORS এরর**: .env-এ `ALLOWED_ORIGIN=https://আপনার-সাইট` দিন বা খালি রাখুন (সব origin)
- নম্বর ফরম্যাট: কান্ট্রি কোডসহ, + ছাড়া হলেও চলবে — সার্ভার নিজেই পরিষ্কার করে নেয়
