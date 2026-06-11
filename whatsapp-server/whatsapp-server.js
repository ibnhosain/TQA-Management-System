/**
 * ════════════════════════════════════════════════════════════════
 * তারবিয়াতুল কুরআন একাডেমি — WhatsApp Business API ব্যাকএন্ড
 * Twilio ও Meta (WhatsApp Cloud API) — দুটোই সাপোর্ট করে
 * ════════════════════════════════════════════════════════════════
 *
 * চালানোর নিয়ম:
 *   1) npm install
 *   2) .env ফাইল বানান (নিচের নমুনা দেখুন)
 *   3) npm start            →  http://localhost:3001
 *   4) Render/Railway-তে ডেপ্লয় করে URL-টা TQA অ্যাপের
 *      "WhatsApp মেসেজ → ⚙️ API সংযোগ" ঘরে বসান, অটো-সেন্ড চালু করুন।
 *
 * ── .env নমুনা (এই ফাইলের পাশে .env নামে সেভ করুন) ──────────────
 *   PORT=3001
 *
 *   # কোন প্রোভাইডার: "twilio" অথবা "meta"
 *   WHATSAPP_PROVIDER=meta
 *
 *   # ── Twilio হলে ──
 *   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
 *   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
 *   TWILIO_WHATSAPP_FROM=+14155238886        # Twilio WhatsApp নম্বর
 *
 *   # ── Meta (WhatsApp Cloud API) হলে ──
 *   META_ACCESS_TOKEN=EAAGxxxxxxxx...         # Permanent access token
 *   META_PHONE_NUMBER_ID=123456789012345      # Business phone number ID
 *
 *   # ঐচ্ছিক: শুধু আপনার সাইট থেকে রিকোয়েস্ট নিতে
 *   ALLOWED_ORIGIN=https://tarbiyatulquran.org
 * ────────────────────────────────────────────────────────────────
 */

require("dotenv").config();
const express = require("express");
const cors = require("cors");

const app = express();
app.use(express.json());
app.use(
  cors({
    origin: process.env.ALLOWED_ORIGIN || "*", // প্রোডাকশনে নিজের ডোমেইন দিন
  })
);

const PROVIDER = (process.env.WHATSAPP_PROVIDER || "meta").toLowerCase();

/* নম্বর পরিষ্কার: +, স্পেস, ড্যাশ বাদ — শুধু ডিজিট (কান্ট্রি কোডসহ) */
const cleanPhone = (to) => String(to || "").replace(/[^\d]/g, "");

/* ── Twilio দিয়ে পাঠানো ───────────────────────────────────────── */
async function sendViaTwilio(to, text) {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;
  const from = process.env.TWILIO_WHATSAPP_FROM;
  if (!sid || !token || !from) throw new Error("Twilio env ভেরিয়েবল অনুপস্থিত");

  const body = new URLSearchParams({
    From: `whatsapp:${from}`,
    To: `whatsapp:+${cleanPhone(to)}`,
    Body: text,
  });

  const res = await fetch(
    `https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`,
    {
      method: "POST",
      headers: {
        Authorization:
          "Basic " + Buffer.from(`${sid}:${token}`).toString("base64"),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    }
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Twilio error");
  return { provider: "twilio", sid: data.sid, status: data.status };
}

/* ── Meta WhatsApp Cloud API দিয়ে পাঠানো ─────────────────────── */
async function sendViaMeta(to, text) {
  const token = process.env.META_ACCESS_TOKEN;
  const phoneId = process.env.META_PHONE_NUMBER_ID;
  if (!token || !phoneId) throw new Error("Meta env ভেরিয়েবল অনুপস্থিত");

  const res = await fetch(
    `https://graph.facebook.com/v19.0/${phoneId}/messages`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messaging_product: "whatsapp",
        to: cleanPhone(to),
        type: "text",
        text: { body: text },
      }),
    }
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Meta error");
  return { provider: "meta", id: data.messages?.[0]?.id };
}

/* ── মূল এন্ডপয়েন্ট — TQA অ্যাপ এখানেই POST করে ─────────────── */
app.post("/api/send-whatsapp", async (req, res) => {
  const { to, text } = req.body || {};
  if (!to || !text)
    return res.status(400).json({ ok: false, error: "to ও text লাগবে" });
  try {
    const result =
      PROVIDER === "twilio"
        ? await sendViaTwilio(to, text)
        : await sendViaMeta(to, text);
    console.log(`✔ পাঠানো হয়েছে → +${cleanPhone(to)} (${result.provider})`);
    res.json({ ok: true, ...result });
  } catch (err) {
    console.error("✘ ব্যর্থ:", err.message);
    res.status(502).json({ ok: false, error: err.message });
  }
});

/* হেলথ চেক — ডেপ্লয়ের পর ব্রাউজারে খুলে দেখুন */
app.get("/", (_, res) =>
  res.json({
    ok: true,
    service: "TQA WhatsApp API",
    provider: PROVIDER,
    note: "POST /api/send-whatsapp { to, text }",
  })
);

const PORT = process.env.PORT || 3001;
app.listen(PORT, () =>
  console.log(
    `🕌 TQA WhatsApp সার্ভার চালু → http://localhost:${PORT} (প্রোভাইডার: ${PROVIDER})`
  )
);
