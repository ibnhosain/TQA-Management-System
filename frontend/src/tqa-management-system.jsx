import React, { useState, useEffect, useMemo, useRef } from "react";

/* ═══════════════════════════════════════════════════════════
   তারবিয়াতুল কুরআন একাডেমি — ম্যানেজমেন্ট সিস্টেম (TQA-MS)
   Roles: admin | teacher | student   —  Demo (in-memory) build
   ═══════════════════════════════════════════════════════════ */

const C = {
  emerald: "#1a5c3a", emeraldD: "#123f28", emeraldL: "#2a7a50",
  gold: "#c9962a", goldL: "#f0c355", cream: "#f4f6f4",
  text: "#1a1f2e", muted: "#6b7280", line: "#e5e9e5",
  red: "#c2410c", redBg: "#fef2ee", green: "#1a7a44", greenBg: "#eafaf1",
  blue: "#2e6fa3", blueBg: "#eef5fb", amberBg: "#fdf6e7",
};

const bn = (n) => String(n).replace(/\d/g, (d) => "০১২৩৪৫৬৭৮৯"[d]);
const todayISO = () => new Date().toISOString().slice(0, 10);
const fmtDate = (iso) => {
  const d = new Date(iso + "T00:00:00");
  const m = ["জানুয়ারি","ফেব্রুয়ারি","মার্চ","এপ্রিল","মে","জুন","জুলাই","আগস্ট","সেপ্টেম্বর","অক্টোবর","নভেম্বর","ডিসেম্বর"];
  return `${bn(d.getDate())} ${m[d.getMonth()]} ${bn(d.getFullYear())}`;
};
const addDays = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
const uid = () => Math.random().toString(36).slice(2, 9);
const genPass = () => { // অক্ষর ও সংখ্যা মিশ্রিত পাসওয়ার্ড (যেমন: t7q2m9k4)
  const a = "abcdefghjkmnpqrstuvwxyz", d = "23456789"; let s = "";
  for (let i = 0; i < 4; i++) s += a[Math.floor(Math.random() * a.length)] + d[Math.floor(Math.random() * d.length)];
  return s;
};

/* 🧾 পেমেন্ট রিসিট / বেতন ভাউচার — ইন-অ্যাপ প্রিভিউ মডাল থেকে প্রিন্ট/PDF (স্যান্ডবক্সে window.open ব্লক থাকে) */
const receiptHTML = (p, person, kind, no) => `<!DOCTYPE html><html lang="bn"><head><meta charset="utf-8"><title>${kind} — TQA-${no}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&display=swap');
body{font-family:'Hind Siliguri',sans-serif;margin:0;padding:28px;background:#f4f6f4;color:#1a1f2e}
.v{max-width:520px;margin:0 auto;background:#fff;border:2px solid #1a5c3a;border-radius:16px;overflow:hidden}
.h{background:linear-gradient(135deg,#123f28,#1a5c3a);color:#fff;padding:20px 24px;text-align:center}
.h .ar{color:#f0c355;font-size:13px;letter-spacing:3px}.h h1{margin:4px 0 2px;font-size:19px}.h .s{font-size:11.5px;color:#cfe6d8}
.k{background:#c9962a;color:#fff;text-align:center;font-weight:700;padding:7px;font-size:14.5px;letter-spacing:1px}
.b{padding:20px 26px}
.r{display:flex;justify-content:space-between;gap:10px;padding:9px 2px;border-bottom:1px dashed #e5e9e5;font-size:14px}
.r span{color:#6b7280}.r b{text-align:right}
.amt{background:#eafaf1;border:1.5px solid #1a7a44;border-radius:12px;text-align:center;padding:14px;margin:16px 0}
.amt .t{font-size:12px;color:#6b7280}.amt .n{font-size:26px;font-weight:800;color:#1a5c3a}
.sg{display:flex;justify-content:space-between;margin-top:38px;font-size:12px;color:#6b7280}
.sg div{border-top:1.5px dashed #9ca3af;padding-top:6px;width:140px;text-align:center}
.f{text-align:center;font-size:11px;color:#9ca3af;padding:10px;border-top:1px solid #eef0ee}
.pr{display:block;margin:16px auto 0;background:#1a5c3a;color:#fff;border:none;padding:11px 26px;border-radius:10px;font-family:inherit;font-size:14px;font-weight:700;cursor:pointer}
@media print{.pr{display:none}body{background:#fff;padding:0}}
</style></head><body>
<div class="v">
<div class="h"><div class="ar">تربية القرآن</div><h1>তারবিয়াতুল কুরআন একাডেমি</h1><div class="s">tarbiyatulquran.org · WhatsApp: +880 140 249 9027</div></div>
<div class="k">${kind}</div>
<div class="b">
<div class="r"><span>রিসিট নং</span><b>TQA-${no}</b></div>
<div class="r"><span>${kind.includes("বেতন") ? "উস্তাদ/উস্তাদা" : "নাম"}</span><b>${person.name || ""}</b></div>
<div class="r"><span>মাস / বিবরণ</span><b>${p.month || "—"}</b></div>
<div class="r"><span>পরিশোধের তারিখ</span><b>${p.date || ""}</b></div>
<div class="r"><span>মাধ্যম</span><b>${p.method || "—"}</b></div>
<div class="r"><span>অবস্থা</span><b>${p.status === "pending" ? "যাচাইয়ের অপেক্ষায়" : "পরিশোধিত ✔"}</b></div>
<div class="amt"><div class="t">পরিমাণ</div><div class="n">৳ ${Number(p.amount || 0).toLocaleString("en")}</div></div>
<div class="sg"><div>গ্রহীতার স্বাক্ষর</div><div>পরিচালক / হিসাবরক্ষক</div></div>
</div>
<div class="f">এটি কম্পিউটারে তৈরি রসিদ — জাযাকুমুল্লাহু খাইরান</div>
</div>
<button class="pr" onclick="window.print()">🖨️ প্রিন্ট / PDF সেভ করুন</button>
</body></html>`;

/* স্যান্ডবক্সে window.confirm/alert ব্লক থাকে — তাই নিজস্ব কনফার্ম-মডাল ও টোস্ট */
let confirmHandler = null;
const askConfirm = (message, onYes) => { confirmHandler ? confirmHandler({ message, onYes }) : onYes(); };
let toastHandler = null;
const notice = (msg) => { if (toastHandler) toastHandler(msg); else try { window.alert(msg); } catch (e) {} };

let receiptHandler = null;
const printReceipt = (p, person, kind) => {
  if (receiptHandler) receiptHandler({ p, person, kind });
};

function ReceiptModal({ r, onClose, db, setDb, sender }) {
  const [ask, setAsk] = useState(false);
  const [done, setDone] = useState(false);
  if (!r) return null;
  const { p, person, kind } = r;
  const canSend = !!person.id && !p.noSend;
  const doDownload = () => {
    const no2 = (p.id || uid()).slice(0, 6).toUpperCase();
    const blob = new Blob([receiptHTML(p, person, kind, no2)], { type: "text/html;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `TQA-receipt-${no2}.html`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    setAsk(false);
  };
  const doSend = () => {
    if (!canSend) return;
    setDb((d) => ({ ...d,
      sentReceipts: [{ id: uid(), toUserId: person.id, kind, month: p.month, amount: p.amount, method: p.method, date: p.date, status: p.status || "verified", sentBy: sender ? `${sender.name}` : "", sentDate: todayISO() }, ...(d.sentReceipts || [])],
      notifications: [{ id: uid(), for: [person.id], text: `🧾 আপনার পোর্টালে একটি "${kind}" পাঠানো হয়েছে — "ভাউচার/রিসিট" মেনুতে দেখুন।`, date: todayISO(), read: false }, ...d.notifications] }));
    setAsk(false); setDone(true);
  };
  const no = (p.id || uid()).slice(0, 6).toUpperCase();
  const row = (k, v) => (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, padding: "9px 2px", borderBottom: "1px dashed #e5e9e5", fontSize: 14 }}>
      <span style={{ color: C.muted }}>{k}</span><b style={{ textAlign: "right" }}>{v}</b>
    </div>
  );
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 150, background: "rgba(18,63,40,.55)", display: "grid", placeItems: "center", padding: 14, overflowY: "auto" }} className="tqa-receipt-overlay">
      <div style={{ width: "100%", maxWidth: 480 }}>
        <div id="tqa-receipt" style={{ background: "#fff", border: `2px solid ${C.emerald}`, borderRadius: 16, overflow: "hidden", fontFamily: "'Hind Siliguri', sans-serif" }}>
          <div style={{ background: `linear-gradient(135deg, ${C.emeraldD}, ${C.emerald})`, color: "#fff", padding: "20px 24px", textAlign: "center" }}>
            <div style={{ color: C.goldL, fontSize: 13, letterSpacing: 3, fontFamily: "'Amiri', serif" }}>تربية القرآن</div>
            <div style={{ fontSize: 19, fontWeight: 800, margin: "4px 0 2px" }}>তারবিয়াতুল কুরআন একাডেমি</div>
            <div style={{ fontSize: 11.5, color: "#cfe6d8" }}>tarbiyatulquran.org · WhatsApp: +880 140 249 9027</div>
          </div>
          <div style={{ background: C.gold, color: "#fff", textAlign: "center", fontWeight: 800, padding: "7px 4px", fontSize: 14.5, letterSpacing: 1 }}>{kind}</div>
          <div style={{ padding: "20px 26px" }}>
            {row("রিসিট নং", `TQA-${no}`)}
            {row(kind.includes("বেতন") ? "উস্তাদ/উস্তাদা" : "নাম", person.name || "")}
            {row("মাস / বিবরণ", p.month || "—")}
            {row("পরিশোধের তারিখ", p.date || "")}
            {row("মাধ্যম", p.method || "—")}
            {row("অবস্থা", p.status === "pending" ? "যাচাইয়ের অপেক্ষায় ⏳" : "পরিশোধিত ✔")}
            <div style={{ background: C.greenBg, border: `1.5px solid ${C.green}`, borderRadius: 12, textAlign: "center", padding: 14, margin: "16px 0" }}>
              <div style={{ fontSize: 12, color: C.muted }}>পরিমাণ</div>
              <div style={{ fontSize: 26, fontWeight: 800, color: C.emerald }}>৳ {bn(Number(p.amount || 0).toLocaleString("en"))}</div>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 38, fontSize: 12, color: C.muted }}>
              <div style={{ borderTop: "1.5px dashed #9ca3af", paddingTop: 6, width: 140, textAlign: "center" }}>গ্রহীতার স্বাক্ষর</div>
              <div style={{ borderTop: "1.5px dashed #9ca3af", paddingTop: 6, width: 140, textAlign: "center" }}>পরিচালক / হিসাবরক্ষক</div>
            </div>
          </div>
          <div style={{ textAlign: "center", fontSize: 11, color: "#9ca3af", padding: "10px 6px", borderTop: `1px solid ${C.line}` }}>এটি কম্পিউটারে তৈরি রসিদ — জাযাকুমুল্লাহু খাইরান</div>
        </div>
        <div className="tqa-receipt-actions" style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <Btn style={{ flex: 1.4, justifyContent: "center" }} onClick={() => setAsk(true)}>⬇️ ডাউনলোড / সেন্ড</Btn>
          <Btn kind="soft" style={{ flex: 1, justifyContent: "center" }} onClick={onClose}>বন্ধ করুন</Btn>
        </div>
        <div style={{ textAlign: "center", fontSize: 11.5, color: "#d7e9de", marginTop: 8 }}>⬇️ ডাউনলোড করলে রিসিট ফাইলটি সেভ হবে — ফাইলটি খুললেই PDF হিসেবে সেভ করা যাবে</div>
      </div>
      {ask && (
        <div onClick={() => setAsk(false)} style={{ position: "fixed", inset: 0, zIndex: 170, background: "rgba(18,63,40,.6)", display: "grid", placeItems: "center", padding: 16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: "#fff", borderRadius: 18, maxWidth: 360, width: "100%", padding: 24, textAlign: "center" }}>
            <div style={{ fontSize: 34 }}>🧾</div>
            <div style={{ fontWeight: 800, fontSize: 16, margin: "6px 0 4px" }}>কী করতে চান?</div>
            <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 16 }}>ডাউনলোড করবেন, নাকি {person.name ? <b>{person.name}</b> : "প্রাপকের"}-এর পোর্টালে পাঠাবেন?</div>
            <div style={{ display: "grid", gap: 8 }}>
              <Btn style={{ justifyContent: "center" }} onClick={doDownload}>⬇️ ডাউনলোড — রিসিট ফাইল সেভ হবে</Btn>
              <Btn kind="gold" style={{ justifyContent: "center", opacity: canSend ? 1 : 0.5 }} onClick={doSend}>📨 সেন্ড — তার পোর্টালের "ভাউচার/রিসিট"-এ যোগ হবে</Btn>
              {!canSend && <div style={{ fontSize: 11.5, color: C.red }}>{p.noSend ? "এই রিসিটটি ইতিমধ্যে পোর্টালে আছে" : "নিবন্ধিত ব্যবহারকারী নয় — কেবল ডাউনলোড করা যাবে"}</div>}
              <Btn kind="soft" sm style={{ justifyContent: "center" }} onClick={() => setAsk(false)}>বাতিল</Btn>
            </div>
          </div>
        </div>
      )}
      {done && (
        <div style={{ position: "fixed", inset: 0, zIndex: 170, background: "rgba(18,63,40,.6)", display: "grid", placeItems: "center", padding: 16 }}>
          <div style={{ background: "#fff", borderRadius: 18, maxWidth: 360, width: "100%", padding: 26, textAlign: "center" }}>
            <div style={{ fontSize: 40 }}>✅</div>
            <div style={{ fontWeight: 800, fontSize: 16, margin: "8px 0 4px" }}>সেন্ড হয়েছে!</div>
            <div style={{ fontSize: 13, color: C.muted, marginBottom: 14 }}>রিসিটটি <b>{person.name}</b>-এর পোর্টালের "🧾 ভাউচার/রিসিট" মেনুতে যোগ হয়েছে এবং নোটিফিকেশন পাঠানো হয়েছে।</div>
            <Btn style={{ width: "100%", justifyContent: "center" }} onClick={() => { setDone(false); onClose(); }}>আলহামদুলিল্লাহ, ঠিক আছে</Btn>
          </div>
        </div>
      )}
      <style>{`@media print {
        body * { visibility: hidden !important; }
        #tqa-receipt, #tqa-receipt * { visibility: visible !important; }
        #tqa-receipt { position: fixed !important; left: 0 !important; top: 0 !important; right: 0 !important; margin: 12mm auto !important; max-width: 480px !important; border-radius: 0 !important; box-shadow: none !important; }
        .tqa-receipt-actions { display: none !important; }
      }`}</style>
    </div>
  );
}

/* ─────────────── seed data ─────────────── */
const USERS = [
  { id: "dir1", role: "director", name: "উস্তাদ ফরিদুর রহমান", sub: "পরিচালক", user: "director", pass: "1234" },
  { id: "admin1", role: "admin", name: "মাওলানা সাঈদ আহমদ", sub: "একাডেমিক এডমিন", user: "admin", pass: "1234" },
  { id: "t1", role: "teacher", name: "উস্তাদ আবদুল্লাহ", sub: "তাজবীদ ও হিফজ", user: "ustad1", pass: "1234", salary: 12000 },
  { id: "t2", role: "teacher", name: "উস্তাদা মারইয়াম", sub: "নুরানী কায়দা", user: "ustada1", pass: "1234", salary: 10000 },
  { id: "s1", role: "student", name: "আহমাদ (লন্ডন)", sub: "নুরানী কায়দা", user: "student1", pass: "1234", fee: 4500, guardian: "জনাব ইউসুফ", country: "যুক্তরাজ্য", phone: "447911123456", email: "yusuf.family@gmail.com" },
  { id: "s2", role: "student", name: "ফাতিমা (টরন্টো)", sub: "তাজবীদসহ কুরআন", user: "student2", pass: "1234", fee: 5000, guardian: "জনাব ইমরান", country: "কানাডা", phone: "14165550182", email: "imran.toronto@gmail.com" },
  { id: "s3", role: "student", name: "ইউনুস (নিউইয়র্ক)", sub: "হিফজ সহায়তা", user: "student3", pass: "1234", fee: 6000, guardian: "জনাব সালেহ", country: "যুক্তরাষ্ট্র", phone: "12125550147", email: "saleh.ny@gmail.com" },
  { id: "s4", role: "student", name: "যায়নাব (দুবাই)", sub: "দ্বীন ও আদব", user: "student4", pass: "1234", fee: 4000, guardian: "জনাব হামযা", country: "আমিরাত", phone: "971501234567", email: "hamza.dubai@gmail.com" },
];


const COURSES = [
  { id: "c1", name: "নুরানী কায়দা", teacherId: "t2", studentIds: ["s1", "s4"], color: C.emerald,
    lectures: [] },
  { id: "c2", name: "তাজবীদসহ কুরআন", teacherId: "t1", studentIds: ["s2"], color: C.gold,
    lectures: [] },
  { id: "c3", name: "হিফজ সহায়তা", teacherId: "t1", studentIds: ["s3"], color: C.blue,
    lectures: [] },
  { id: "c4", name: "দ্বীন, আদব ও চরিত্র গঠন", teacherId: "t2", studentIds: ["s4", "s1"], color: C.red,
    lectures: [] },
];

const seedDB = () => {
  const t = todayISO();
  const nw = new Date(Date.now() - 5 * 60000); // 5 min ago - running class for popup demo
  const nowHM = `${String(nw.getHours()).padStart(2, "0")}:${String(nw.getMinutes()).padStart(2, "0")}`;
  return {
    classes: [
      { id: "know", courseId: "c1", date: t, time: nowHM, dur: 60, zoom: "https://zoom.us/j/8801402499027", status: "upcoming", lectureNo: 4 },
      { id: "k1", courseId: "c1", date: t, time: "17:00", dur: 60, zoom: "https://zoom.us/j/8801402499027", status: "upcoming", lectureNo: 3 },
      { id: "k2", courseId: "c2", date: t, time: "19:00", dur: 60, zoom: "https://zoom.us/j/8801402499028", status: "upcoming", lectureNo: 2 },
      { id: "k3", courseId: "c3", date: addDays(1), time: "18:00", dur: 60, zoom: "https://zoom.us/j/8801402499029", status: "upcoming", lectureNo: 1 },
      { id: "k0", courseId: "c1", date: addDays(-2), time: "17:00", dur: 60, zoom: "https://zoom.us/j/8801402499027", status: "done", lectureNo: 2 },
      { id: "k01", courseId: "c2", date: addDays(-1), time: "19:00", dur: 60, zoom: "https://zoom.us/j/8801402499028", status: "done", lectureNo: 1 },
    ],
    attendance: [
      { id: uid(), classId: "k0", userId: "s1", minutes: 55 },
      { id: uid(), classId: "k0", userId: "s4", minutes: 25 },
      { id: uid(), classId: "k0", userId: "t2", minutes: 60 },
      { id: uid(), classId: "k01", userId: "s2", minutes: 58 },
      { id: uid(), classId: "k01", userId: "t1", minutes: 60 },
    ],
    assignments: [
      { id: "a1", courseId: "c1", teacherId: "t2", title: "হরফ লিখে ছবি জমা দাও", desc: "আলিফ থেকে খা পর্যন্ত প্রতিটি হরফ ৫ বার করে লিখে খাতার ছবি তুলে জমা দেবে।", due: addDays(3), mode: "photo", total: 10, questions: [],
        subs: [{ id: uid(), studentId: "s1", date: t, answers: null, image: null, note: "খাতার ছবি জমা দিয়েছি, উস্তাদা। (ডেমো)", mark: 8 }] },
      { id: "a2", courseId: "c2", teacherId: "t1", title: "নুন সাকিন ও তানভীনের নিয়ম", desc: "নিচের প্রশ্নগুলোর উত্তর ফরমে লিখে জমা দাও।", due: addDays(2), mode: "form", total: 10,
        questions: [
          { id: "q1", q: "ইযহারের হরফ কয়টি ও কী কী?", type: "text" },
          { id: "q2", q: "ইকলাব কাকে বলে? একটি উদাহরণ দাও।", type: "text" },
        ], subs: [] },
    ],
    exams: [
      { id: "e1", type: "mcq", title: "মাসিক MCQ — মে ২০২৬", courseId: "c1", total: 30, date: addDays(-12), marks: { s1: 26, s4: 22 }, mode: "photo", questions: [], subs: [] },
      { id: "e2", type: "live", title: "লাইভ তিলাওয়াত টেস্ট — মে", courseId: "c2", total: 50, date: addDays(-10), marks: { s2: 44 }, mode: "photo", questions: [], subs: [] },
      { id: "e3", type: "mcq", title: "মাসিক MCQ — জুন ২০২৬", courseId: "c1", total: 30, date: addDays(5), marks: {}, mode: "form",
        questions: [
          { id: "x1", q: "মাদের মূল হরফ কয়টি?", type: "mcq", options: ["২টি", "৩টি", "৪টি", "৫টি"], correct: 1 },
          { id: "x2", q: "'যবর'-এর আরবি নাম কী?", type: "mcq", options: ["কাসরা", "দাম্মা", "ফাতহা", "সুকুন"], correct: 2 },
          { id: "x3", q: "নুরানী কায়দা শেখা কেন জরুরি — নিজের ভাষায় লেখো।", type: "text" },
        ], subs: [] },
    ],
    feePayments: [
      { id: uid(), studentId: "s1", amount: 4500, month: "এপ্রিল ২০২৬", date: addDays(-40), method: "bKash", status: "verified" },
      { id: uid(), studentId: "s1", amount: 4500, month: "মে ২০২৬", date: addDays(-10), method: "bKash", status: "verified" },
      { id: uid(), studentId: "s2", amount: 5000, month: "মে ২০২৬", date: addDays(-8), method: "Wise", status: "verified" },
      { id: uid(), studentId: "s2", amount: 5000, month: "জুন ২০২৬", date: t, method: "বিকাশ (Trx: 9HX2K7QM)", status: "pending" },
      { id: uid(), studentId: "s3", amount: 6000, month: "এপ্রিল ২০২৬", date: addDays(-35), method: "PayPal", status: "verified" },
    ],
    teacherPayments: [
      { id: uid(), teacherId: "t1", amount: 12000, month: "মে ২০২৬", date: addDays(-5), method: "ব্যাংক" },
      { id: uid(), teacherId: "t2", amount: 10000, month: "এপ্রিল ২০২৬", date: addDays(-32), method: "bKash", status: "verified" },
    ],
    dueMonths: { s1: ["জুন ২০২৬"], s2: [], s3: ["মে ২০২৬", "জুন ২০২৬"], s4: ["মে ২০২৬", "জুন ২০২৬"], t1: ["জুন ২০২৬"], t2: ["মে ২০২৬", "জুন ২০২৬"] },
    admissions: [
      { id: uid(), name: "হামজা ইবনে উমর", age: 9, guardian: "জনাব উমর ফারুক", country: "অস্ট্রেলিয়া", contact: "+61 4 1234 5678", course: "নুরানী কায়দা", msg: "সিডনি সময় সকালে ক্লাস চাই।", date: addDays(-1), status: "pending" },
      { id: uid(), name: "সুমাইয়া বিনতে রশিদ", age: 11, guardian: "জনাব রশিদ", country: "জার্মানি", contact: "+49 151 2345678", course: "তাজবীদসহ কুরআন", msg: "আগে ১ বছর কায়দা পড়েছে।", date: addDays(-3), status: "pending" },
    ],
    permissions: { fixCross: { t1: false, t2: false } },
    ratings: [
      { id: uid(), classId: "k0", courseId: "c1", teacherId: "t2", studentId: "s1", stars: 5, comment: "উস্তাদা খুব সুন্দর করে বুঝিয়েছেন, আলহামদুলিল্লাহ।", date: addDays(-2) },
      { id: uid(), classId: "k01", courseId: "c2", teacherId: "t1", studentId: "s2", stars: 4, comment: "", date: addDays(-1) },
    ],
    forms: [
      { id: uid(), type: "ফ্রি ট্রায়াল", name: "উম্মে হাবিবা", contact: "+44 7911 123456", msg: "আমার ৭ বছরের মেয়ের জন্য নুরানী কায়দা ট্রায়াল চাই, লন্ডন সময় বিকেল।", date: addDays(-1), status: "new" },
      { id: uid(), type: "যোগাযোগ", name: "আবু বকর সিদ্দিক", contact: "abubakr@mail.com", msg: "হিফজ সহায়তা কোর্সের ফি ও সময়সূচি জানতে চাই।", date: addDays(-3), status: "replied" },
      { id: uid(), type: "ফ্রি ট্রায়াল", name: "মুহাম্মাদ আলী", contact: "+1 416 555 0182", msg: "টরন্টো থেকে, দুই ভাইয়ের জন্য তাজবীদ কোর্স।", date: t, status: "new" },
    ],
    books: [
      { id: uid(), cls: "নুরানী কায়দা", title: "নুরানী কায়দা (সংশোধিত)", author: "তারবিয়াতুল কুরআন একাডেমি", link: "#", type: "PDF" },
      { id: uid(), cls: "তাজবীদ", title: "আত-তাজবীদুল মুসাওয়ার", author: "ড. আইমান সুওয়াইদ", link: "#", type: "PDF" },
      { id: uid(), cls: "তাজবীদ", title: "তাজবীদ শিক্ষা (বাংলা)", author: "একাডেমি সংকলন", link: "#", type: "PDF" },
      { id: uid(), cls: "হিফজ", title: "১৫ লাইনের হাফেজি মুসহাফ", author: "—", link: "#", type: "PDF" },
      { id: uid(), cls: "দ্বীন ও আদব", title: "ইয়াহুল মুসলিম (নির্বাচিত অংশ)", author: "একাডেমি সংকলন", link: "#", type: "DOCX" },
      { id: uid(), cls: "দ্বীন ও আদব", title: "দৈনন্দিন দুআ সংকলন", author: "একাডেমি", link: "#", type: "PDF" },
    ],
    notices: [
      { id: uid(), title: "জুন মাসের MCQ পরীক্ষা", body: "আগামী সপ্তাহে সকল কোর্সের মাসিক MCQ অনুষ্ঠিত হবে ইনশাআল্লাহ। সিলেবাস: চলতি মাসের কভার করা টপিক।", date: t },
      { id: uid(), title: "ঈদুল আজহার ছুটি", body: "ঈদ উপলক্ষে ৩ দিন ক্লাস বন্ধ থাকবে। মেকআপ ক্লাসের সময়সূচি পরে জানানো হবে।", date: addDays(-4) },
    ],
    makeups: [
      { id: uid(), courseId: "c1", studentId: "s4", reason: "গত ক্লাসে ২৫ মিনিট উপস্থিতি (অনুপস্থিত গণ্য)", date: addDays(2), time: "16:00", status: "scheduled" },
    ],
    syllabus: [], // পরিচালক নিজে তৈরি করবেন
    academicBooks: [], // পরিচালক ডিভাইস থেকে আপলোড করবেন
    waOutbox: [],
    waConfig: { backendUrl: "", autoSend: false }, // WhatsApp Business API (Twilio/Meta) ব্যাকএন্ড
    sentReceipts: [
      { id: uid(), toUserId: "s1", kind: "ফি পরিশোধ রিসিট", month: "মে ২০২৬", amount: 4500, method: "bKash", date: fmtDate(addDays(-9)), status: "verified", sentBy: "উস্তাদ ফরিদুর রহমান (পরিচালক)", sentDate: addDays(-9) },
    ],
    routine: [
      { id: uid(), courseId: "c1", days: [0, 2], time: "17:00", dur: 60, zoom: "https://zoom.us/j/8801402499027", kind: "নিয়মিত ক্লাস", teacherId: "t2", studentIds: ["s1", "s4"] },
    ],
    leaves: [
      { id: uid(), userId: "s3", type: "সফর", from: addDays(4), to: addDays(6), reason: "পারিবারিক প্রয়োজনে দেশের বাইরে সফরে থাকব, তাই উক্ত দিনগুলোতে ক্লাসে উপস্থিত হতে পারব না।", date: todayISO(), status: "pending_admin" },
      { id: uid(), userId: "t2", type: "অসুস্থতা", from: addDays(-3), to: addDays(-2), reason: "জ্বরের কারণে বিশ্রামে ছিলাম।", date: addDays(-4), status: "approved" },
    ],
    notifications: [
      { id: uid(), for: ["s1", "s4", "t2", "admin1", "dir1"], text: "আজ বিকেল ৫টায় নুরানী কায়দা ক্লাস — লেকচার ৩", date: t, read: false },
      { id: uid(), for: ["s2", "t1", "admin1", "dir1"], text: "আজ সন্ধ্যা ৭টায় তাজবীদ ক্লাস — লেকচার ২", date: t, read: false },
    ],
  };
};


/* ─────────────── UI primitives ─────────────── */
const S = {
  card: { background: "#fff", border: `1px solid ${C.line}`, borderRadius: 16, padding: 20, boxShadow: "0 2px 8px rgba(26,92,58,.06)" },
  h2: { fontSize: 20, fontWeight: 700, color: C.text, margin: 0 },
  sub: { fontSize: 13, color: C.muted },
  input: { width: "100%", padding: "10px 12px", border: `1.5px solid ${C.line}`, borderRadius: 10, fontSize: 14, fontFamily: "inherit", outline: "none", background: "#fff", color: C.text, boxSizing: "border-box" },
  label: { fontSize: 12.5, fontWeight: 600, color: C.muted, display: "block", marginBottom: 5 },
};

const Btn = ({ children, kind = "primary", sm, style, ...p }) => {
  const base = { border: "none", cursor: "pointer", fontFamily: "inherit", fontWeight: 600, borderRadius: 10, fontSize: sm ? 12.5 : 14, padding: sm ? "6px 12px" : "10px 18px", transition: "all .15s", display: "inline-flex", alignItems: "center", gap: 6 };
  const kinds = {
    primary: { background: C.emerald, color: "#fff" },
    gold: { background: C.gold, color: "#fff" },
    ghost: { background: "transparent", color: C.emerald, border: `1.5px solid ${C.emerald}` },
    danger: { background: C.redBg, color: C.red, border: `1.5px solid #f3c9b8` },
    soft: { background: C.cream, color: C.text, border: `1px solid ${C.line}` },
  };
  return <button style={{ ...base, ...kinds[kind], ...style }} {...p}>{children}</button>;
};

const Tag = ({ children, color = C.emerald, bg = C.greenBg }) => (
  <span style={{ background: bg, color, fontSize: 11.5, fontWeight: 700, padding: "3px 10px", borderRadius: 99, whiteSpace: "nowrap" }}>{children}</span>
);

const Stat = ({ icon, label, value, accent = C.emerald, note }) => (
  <div style={{ ...S.card, display: "flex", gap: 14, alignItems: "center", padding: 16 }}>
    <div style={{ width: 46, height: 46, borderRadius: 12, background: accent + "14", display: "grid", placeItems: "center", fontSize: 22 }}>{icon}</div>
    <div style={{ minWidth: 0 }}>
      <div style={{ fontSize: 12, color: C.muted, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 21, fontWeight: 800, color: C.text, lineHeight: 1.2 }}>{value}</div>
      {note && <div style={{ fontSize: 11.5, color: C.muted }}>{note}</div>}
    </div>
  </div>
);

const Modal = ({ title, onClose, children, wide }) => (
  <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(18,63,40,.45)", zIndex: 90, display: "grid", placeItems: "center", padding: 16 }}>
    <div onClick={(e) => e.stopPropagation()} style={{ background: "#fff", borderRadius: 18, width: "100%", maxWidth: wide ? 720 : 480, maxHeight: "88vh", overflowY: "auto", padding: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <h3 style={{ ...S.h2, fontSize: 17 }}>{title}</h3>
        <button onClick={onClose} style={{ border: "none", background: C.cream, borderRadius: 8, width: 30, height: 30, cursor: "pointer", fontSize: 15 }}>✕</button>
      </div>
      {children}
    </div>
  </div>
);

const Table = ({ head, rows, empty = "কোনো তথ্য নেই" }) => (
  <div style={{ overflowX: "auto", borderRadius: 12, border: `1px solid ${C.line}` }}>
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13.5, minWidth: 540 }}>
      <thead><tr>{head.map((h, i) => <th key={i} style={{ textAlign: "left", padding: "10px 12px", background: C.cream, color: C.muted, fontSize: 12, fontWeight: 700, whiteSpace: "nowrap" }}>{h}</th>)}</tr></thead>
      <tbody>
        {rows.length === 0 && <tr><td colSpan={head.length} style={{ padding: 18, textAlign: "center", color: C.muted }}>{empty}</td></tr>}
        {rows.map((r, i) => <tr key={i} style={{ borderTop: `1px solid ${C.line}` }}>{r.map((c, j) => <td key={j} style={{ padding: "10px 12px", color: C.text }}>{c}</td>)}</tr>)}
      </tbody>
    </table>
  </div>
);

const Section = ({ title, sub, action, children }) => (
  <div style={{ marginBottom: 22 }}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 12, gap: 10, flexWrap: "wrap" }}>
      <div><h2 style={S.h2}>{title}</h2>{sub && <div style={S.sub}>{sub}</div>}</div>
      {action}
    </div>
    {children}
  </div>
);

/* ─────────────── helper selectors ─────────────── */
const userById = (id) => USERS.find((u) => u.id === id) || {};
const isDir = (u) => u.role === "director";
const isAdm = (u) => u.role === "admin" || u.role === "director"; // পরিচালক = সর্বোচ্চ ক্ষমতা
const courseById = (cs, id) => cs.find((c) => c.id === id) || {};
const myCourses = (cs, u) => isAdm(u) ? cs : u.role === "teacher" ? cs.filter((c) => c.teacherId === u.id) : cs.filter((c) => c.studentIds.includes(u.id));
/* অভিভাবকের WhatsApp-এ পাঠানোর মেসেজ তৈরি — আউটবক্সে জমা হয়, এক ট্যাপে পাঠানো যায় */
const waGuardianMsgs = (k, course, reason) => {
  const studs = (k.studentIds && k.studentIds.length ? k.studentIds : course.studentIds) || [];
  return studs.map((sid) => {
    const s = userById(sid);
    if (!s.phone) return null;
    const text = reason === "reminder"
      ? `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম ${s.guardian || "অভিভাবক"}, ${s.name}-এর "${course.name}" ক্লাস আজ ${k.time}-এ (আর ৫ মিনিটের মধ্যে) শুরু হচ্ছে ইনশাআল্লাহ। অনুগ্রহ করে ক্লাসে যুক্ত হতে সহায়তা করুন। জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি`
      : `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম ${s.guardian || "অভিভাবক"}, ${s.name}-এর "${course.name}" ক্লাসটি (${fmtDate(k.date)}, ${k.time}) অনিবার্য কারণে / উস্তাদ-উস্তাদা অসুস্থ থাকার দরুন স্থগিত করা হয়েছে। ক্লাসটি পরবর্তীতে শিডিউল করে মেকআপ করা হবে ইনশাআল্লাহ। জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি`;
    return { id: uid(), toName: s.guardian || s.name, student: s.name, phone: s.phone, text, reason: reason === "reminder" ? "৫ মিনিট রিমাইন্ডার" : "ক্লাস স্থগিত", date: todayISO(), sent: false };
  }).filter(Boolean);
};

/* সিলেবাস এন্ট্রি → পাঠযোগ্য লেবেল (লেকচারের টপিক হিসেবে ব্যবহৃত) */
/* dataURL → blob URL (বই ডিভাইসের ডিফল্ট রিডারে খোলার জন্য) */
const dataUrlToBlobUrl = (dataUrl) => {
  try {
    const [head, b64] = dataUrl.split(",");
    const mime = (head.match(/data:(.*?);/) || [])[1] || "application/octet-stream";
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return { url: URL.createObjectURL(new Blob([arr], { type: mime })), mime };
  } catch (e) { return { url: dataUrl, mime: "application/octet-stream" }; }
};
const bookExt = (n) => (n || "").split(".").pop().toUpperCase().slice(0, 5);

const sylLabel = (e) => `${e.book && e.book !== "অন্যান্য" ? e.book + " — " : ""}${e.lesson}${e.pages ? `, পৃষ্ঠা: ${e.pages}` : ""}${e.lines ? `, লাইন: ${e.lines}` : ""}`;

const CLASS_KINDS = ["মেকআপ ক্লাস", "সাপোর্ট ক্লাস", "রিকভারি ক্লাস", "ট্রায়াল ক্লাস", "নিয়মিত ক্লাস", "অন্যান্য"];
/* ক্লাস/রুটিন কার পোর্টালে দেখাবে — নির্দিষ্ট উস্তাদ/স্টুডেন্ট দেওয়া থাকলে নাম অনুযায়ী, নইলে কোর্স অনুযায়ী */
const itemVisible = (it, user) => {
  if (isAdm(user)) return true;
  const c = courseById(COURSES, it.courseId);
  if (user.role === "teacher") return it.teacherId ? it.teacherId === user.id : c.teacherId === user.id;
  if (user.role === "student") return (it.studentIds && it.studentIds.length) ? it.studentIds.includes(user.id) : (c.studentIds || []).includes(user.id);
  return false;
};
/* সব স্টুডেন্টের নামের তালিকা — চেকবক্সে এক এক করে বাছাই */
function StudentPicker({ selected, onToggle }) {
  return (
    <div style={{ maxHeight: 150, overflowY: "auto", border: `1.5px solid ${C.line}`, borderRadius: 10, padding: 6, background: "#fff" }}>
      {USERS.filter((u) => u.role === "student").map((s) => (
        <label key={s.id} style={{ display: "flex", gap: 8, alignItems: "center", padding: "6px 8px", fontSize: 13, cursor: "pointer", borderRadius: 8, background: selected.includes(s.id) ? C.greenBg : "transparent" }}>
          <input type="checkbox" checked={selected.includes(s.id)} onChange={() => onToggle(s.id)} />
          <b>{s.name}</b> <span style={{ color: C.muted, fontSize: 11.5 }}>({s.sub})</span>
        </label>
      ))}
    </div>
  );
}

const coverageOf = (course) => {
  const all = course.lectures.flatMap((l) => l.topics);
  const done = all.filter((t) => t.covered === true).length;
  return { done, total: all.length, pct: all.length ? Math.round((done / all.length) * 100) : 0 };
};

/* ═══════════════ লগইন ═══════════════ */
function Login({ onLogin, onAdmission }) {
  /* ভূমিকার তালিকা — কার্ড হিসেবে দেখানো হয় */
  const ROLES = [
    { key: "director", label: "পরিচালক", icon: "👑", desc: "সার্বিক তত্ত্বাবধান — ফি, বেতন, রিপোর্ট ও সকল ক্ষমতা" },
    { key: "admin", label: "এডমিন", icon: "🛡️", desc: "শিক্ষার্থী, উস্তাদ, ক্লাস ও পেমেন্ট ব্যবস্থাপনা" },
    { key: "teacher", label: "উস্তাদ / উস্তাদা", icon: "📖", desc: "ক্লাস, হাজিরা, পড়ানো ও শিক্ষার্থীর অগ্রগতি" },
    { key: "student", label: "স্টুডেন্ট", icon: "🎓", desc: "রুটিন, পড়া, পরীক্ষা ও ফি-এর হিসাব" },
  ];
  /* ওয়েবসাইটের login.html থেকে ?role=admin দিয়ে এলে সরাসরি ফর্মে */
  const initRole = (() => {
    try { const r = new URLSearchParams(window.location.search).get("role"); return ROLES.some((x) => x.key === r) ? r : null; } catch { return null; }
  })();
  const [role, setRole] = useState(initRole);
  const [u, setU] = useState(""); const [p, setP] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const go = async () => {
    if (!u.trim() || !p) { setErr("আইডি ও পাসওয়ার্ড দুটোই লিখুন"); return; }
    setBusy(true); setErr("");
    try {
      const { login } = await import("./api");
      const me = await login(u.trim(), p);
      onLogin(me);
    } catch (err) {
      // ব্যাকএন্ড না থাকলে বা নেটওয়ার্ক এরর হলে — mock USERS দিয়ে fallback
      const found = USERS.find(
        (x) => (x.user === u.trim() || x.email === u.trim() || x.phone === u.trim()) && x.pass === p
      );
      if (found) {
        onLogin({ ...found, name_bn: found.name, sub_title: found.sub });
      } else {
        setErr("ভুল আইডি বা পাসওয়ার্ড!");
      }
    } finally { setBusy(false); }
  };
  const [apply, setApply] = useState(false);
  const [ok, setOk] = useState(false);
  const [af, setAf] = useState({ name: "", age: "", guardian: "", country: "", contact: "", course: "নুরানী কায়দা", msg: "" });
  const sendApply = () => {
    if (!af.name || !af.guardian || !af.contact) return;
    onAdmission(af); setApply(false); setOk(true); setTimeout(() => setOk(false), 5000);
  };
  return (
    <div style={{ minHeight: "100vh", background: `linear-gradient(160deg, ${C.emeraldD}, ${C.emerald} 60%, ${C.emeraldL})`, display: "grid", placeItems: "center", padding: 16 }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 22 }}>
          <div style={{ fontSize: 42 }}>🕌</div>
          <div style={{ color: C.goldL, fontSize: 13, letterSpacing: 2, fontWeight: 700 }}>تربية القرآن</div>
          <h1 style={{ color: "#fff", fontSize: 24, margin: "4px 0 2px", fontWeight: 800 }}>তারবিয়াতুল কুরআন একাডেমি</h1>
          <div style={{ color: "#cfe6d8", fontSize: 13 }}>ম্যানেজমেন্ট সিস্টেম — এডমিন · উস্তাদ/উস্তাদা · স্টুডেন্ট</div>
        </div>
        <div style={{ ...S.card, borderRadius: 20, padding: 22 }}>
          {!role ? (
            <>
              {/* ── ধাপ ১: ভূমিকা বাছাই ── */}
              <div style={{ fontWeight: 800, fontSize: 16, textAlign: "center", marginBottom: 4 }}>আপনি কে হিসেবে লগইন করবেন?</div>
              <div style={{ fontSize: 12.5, color: C.muted, textAlign: "center", marginBottom: 14 }}>আপনার ভূমিকা বাছাই করুন</div>
              <div style={{ display: "grid", gap: 10 }}>
                {ROLES.map((r) => (
                  <button key={r.key} onClick={() => { setRole(r.key); setErr(""); }}
                    style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", borderRadius: 14, border: `1.5px solid ${C.line}`, background: "#fff", cursor: "pointer", textAlign: "left", width: "100%", fontFamily: "inherit" }}>
                    <span style={{ fontSize: 26, flexShrink: 0 }}>{r.icon}</span>
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ display: "block", fontWeight: 800, fontSize: 14.5, color: C.text }}>{r.label}</span>
                      <span style={{ display: "block", fontSize: 11.5, color: C.muted, marginTop: 2 }}>{r.desc}</span>
                    </span>
                    <span style={{ color: C.emerald, fontWeight: 800, flexShrink: 0 }}>→</span>
                  </button>
                ))}
              </div>
              <Btn kind="ghost" style={{ width: "100%", justifyContent: "center", marginTop: 14 }} onClick={() => setApply(true)}>🎓 নতুন শিক্ষার্থী? ভর্তি আবেদন করুন</Btn>
              {ok && <div style={{ marginTop: 10, padding: "10px 12px", borderRadius: 10, background: C.greenBg, color: C.green, fontSize: 12.5, fontWeight: 700, textAlign: "center" }}>✔ আবেদন জমা হয়েছে! এডমিন গ্রহণ করলে লগইন তথ্য জানানো হবে ইনশাআল্লাহ।</div>}
            </>
          ) : (
            <>
              {/* ── ধাপ ২: আইডি ও পাসওয়ার্ড ── */}
              <button onClick={() => { setRole(null); setErr(""); }}
                style={{ background: "none", border: "none", color: C.muted, fontSize: 12.5, cursor: "pointer", padding: 0, marginBottom: 12, fontFamily: "inherit" }}>← ভূমিকা বদলান</button>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                <span style={{ fontSize: 30 }}>{ROLES.find((r) => r.key === role).icon}</span>
                <div>
                  <div style={{ fontWeight: 800, fontSize: 15, color: C.text }}>{ROLES.find((r) => r.key === role).label} লগইন</div>
                  <div style={{ fontSize: 11.5, color: C.muted }}>আপনার আইডি ও পাসওয়ার্ড দিন</div>
                </div>
              </div>
              <label style={S.label}>আইডি</label>
              <input style={{ ...S.input, width: "100%", boxSizing: "border-box" }} value={u} onChange={(e) => setU(e.target.value)} placeholder="আইডি / ইমেইল / মোবাইল নম্বর" autoFocus />
              <div style={{ height: 12 }} />
              <label style={S.label}>পাসওয়ার্ড</label>
              <div style={{ position: "relative" }}>
                <input style={{ ...S.input, width: "100%", boxSizing: "border-box", paddingRight: 44 }} type={showPass ? "text" : "password"} value={p}
                  onChange={(e) => setP(e.target.value)} placeholder="••••••••" onKeyDown={(e) => e.key === "Enter" && go()} />
                <button onClick={() => setShowPass((s) => !s)} title={showPass ? "পাসওয়ার্ড লুকান" : "পাসওয়ার্ড দেখুন"} aria-label={showPass ? "পাসওয়ার্ড লুকান" : "পাসওয়ার্ড দেখুন"}
                  style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 17, padding: 2, lineHeight: 1 }}>{showPass ? "🙈" : "👁️"}</button>
              </div>
              {err && <div style={{ color: C.red, fontSize: 12.5, marginTop: 8 }}>{err}</div>}
              <Btn style={{ width: "100%", justifyContent: "center", marginTop: 16, opacity: busy ? 0.7 : 1 }} onClick={go}>{busy ? "যাচাই হচ্ছে…" : "লগ ইন করুন"}</Btn>
            </>
          )}
        </div>
      </div>
      {apply && (
        <Modal title="ভর্তি আবেদন ফরম" onClose={() => setApply(false)}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><label style={S.label}>শিক্ষার্থীর নাম *</label><input style={S.input} value={af.name} onChange={(e) => setAf({ ...af, name: e.target.value })} /></div>
            <div><label style={S.label}>বয়স</label><input type="number" style={S.input} value={af.age} onChange={(e) => setAf({ ...af, age: e.target.value })} /></div>
            <div><label style={S.label}>অভিভাবকের নাম *</label><input style={S.input} value={af.guardian} onChange={(e) => setAf({ ...af, guardian: e.target.value })} /></div>
            <div><label style={S.label}>দেশ</label><input style={S.input} value={af.country} onChange={(e) => setAf({ ...af, country: e.target.value })} /></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>যোগাযোগ (WhatsApp/ইমেইল) *</label><input style={S.input} value={af.contact} onChange={(e) => setAf({ ...af, contact: e.target.value })} /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>কাঙ্ক্ষিত কোর্স</label>
            <select style={S.input} value={af.course} onChange={(e) => setAf({ ...af, course: e.target.value })}>
              {COURSES.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
            </select></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>বার্তা (ঐচ্ছিক)</label><textarea rows={2} style={{ ...S.input, resize: "vertical" }} value={af.msg} onChange={(e) => setAf({ ...af, msg: e.target.value })} /></div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={sendApply}>আবেদন জমা দিন</Btn>
        </Modal>
      )}
    </div>
  );
}

/* ═══════════════ ক্লাস ও জুম জয়েন (ফিচার ২ ও ৪) ═══════════════ */
function LiveTimer({ start, demoFast }) {
  const [, tick] = useState(0);
  useEffect(() => { const t = setInterval(() => tick((x) => x + 1), 1000); return () => clearInterval(t); }, []);
  const mins = Math.floor((Date.now() - start) / (demoFast ? 1000 : 60000));
  return <span style={{ fontWeight: 800, color: mins >= 40 ? C.green : C.gold }}>{bn(mins)} মিনিট {mins >= 40 ? "✓ হাজিরা নিশ্চিত" : `(হাজিরার জন্য ${bn(40 - mins)} মিনিট বাকি)`}</span>;
}

function ClassesView({ db, setDb, user, courses, autoJoinId, onAutoJoinConsumed }) {
  const [show, setShow] = useState(false);
  const blankSched = () => ({ courseId: courses[0]?.id, date: todayISO(), time: "17:00", dur: 60, lectureNo: 1, zoom: "https://zoom.us/j/", kind: "মেকআপ ক্লাস", teacherId: USERS.find((u) => u.role === "teacher")?.id, studentIds: [], req: "" });
  const [f, setF] = useState(blankSched);
  const [editId, setEditId] = useState(null); // এডিট — কেবল এডমিন/পরিচালক
  const [joined, setJoined] = useState(null); // {classId, start}
  const [rate, setRate] = useState(null); // ক্লাস শেষে মূল্যায়ন পপআপ
  useEffect(() => { // লাইভ পপআপ থেকে এলে হাজিরা টাইমার অটো চালু
    if (autoJoinId) { setJoined({ classId: autoJoinId, start: Date.now() }); onAutoJoinConsumed && onAutoJoinConsumed(); }
  }, [autoJoinId]);
  const [demoFast, setDemoFast] = useState(true);
  const mine = db.classes.filter((k) => itemVisible(k, user)).sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time)); // উস্তাদ ও স্টুডেন্টের নাম অনুযায়ী তার পোর্টালে
  const today = mine.filter((k) => k.date === todayISO() && k.status !== "done");
  const upcoming = mine.filter((k) => k.date > todayISO());
  const past = mine.filter((k) => k.status === "done" || k.date < todayISO());

  const join = (k) => { // জুম খোলে অ্যাংকর লিংকে (নিচে <a>); এখানে কেবল হাজিরা টাইমার চালু হয়
    setJoined({ classId: k.id, start: Date.now() });
  };
  const leave = () => {
    const mins = Math.floor((Date.now() - joined.start) / (demoFast ? 1000 : 60000));
    const k = db.classes.find((x) => x.id === joined.classId);
    setDb((d) => ({ ...d, attendance: [...d.attendance, { id: uid(), classId: joined.classId, userId: user.id, minutes: mins }] }));
    setJoined(null);
    if (user.role === "student" && k) {
      const c = courseById(courses, k.courseId);
      setRate({ classId: k.id, courseId: c.id, teacherId: c.teacherId, courseName: c.name }); // জুমের মতো মূল্যায়ন পপআপ (অপশনাল)
    }
  };
  const submitRating = (stars, comment) => {
    setDb((d) => ({ ...d, ratings: [...d.ratings, { id: uid(), ...rate, studentId: user.id, stars, comment, date: todayISO() }] }));
    setRate(null);
  };
  const delClass = (id) => setDb((d) => ({ ...d, classes: d.classes.filter((k) => k.id !== id) }));
  const addClass = () => {
    const c = courseById(courses, f.courseId);
    const students = f.studentIds.length ? f.studentIds : (c.studentIds || []); // কাউকে না বাছলে কোর্সের সবাই
    if (editId) { // ✏️ এডিট — কেবল এডমিন/পরিচালক; তারিখ-সময় বদলালে পোর্টালের জয়েন অপশনও অটো বদলায়
      setDb((d) => ({ ...d, classes: d.classes.map((x) => x.id === editId ? { ...x, ...f, studentIds: students, dur: +f.dur, lectureNo: +f.lectureNo } : x),
        notifications: [{ id: uid(), for: [f.teacherId, ...students, "admin1", "dir1"], text: `✏️ [${f.kind}] ক্লাসটি আপডেট হয়েছে: ${c.name} — ${fmtDate(f.date)} ${f.time}।`, date: todayISO(), read: false }, ...d.notifications] }));
    } else {
      const k = { id: uid(), ...f, studentIds: students, dur: +f.dur, lectureNo: +f.lectureNo, status: "upcoming" };
      setDb((d) => ({ ...d, classes: [...d.classes, k],
        notifications: [{ id: uid(), for: [f.teacherId, ...students, "admin1", "dir1"], text: `${f.kind !== "নিয়মিত ক্লাস" ? `[${f.kind}] ` : ""}${fmtDate(f.date)} ${f.time} — ${c.name} ক্লাস নির্ধারিত হয়েছে (উস্তাদ: ${userById(f.teacherId).name})। শিক্ষার্থী: ${students.map((s) => userById(s).name).join(", ")}। সময় হলে ড্যাশবোর্ড থেকে জয়েন করুন।`, date: todayISO(), read: false }, ...d.notifications] }));
    }
    setShow(false); setEditId(null); setF(blankSched());
  };
  const startEdit = (k) => { // ক্লাস এডিট — মডাল প্রি-ফিল
    setF({ courseId: k.courseId, date: k.date, time: k.time, dur: k.dur, lectureNo: k.lectureNo, zoom: k.zoom, kind: k.kind || "নিয়মিত ক্লাস", teacherId: k.teacherId || courseById(COURSES, k.courseId).teacherId, studentIds: k.studentIds || [], req: k.req || "" });
    setEditId(k.id); setShow(true);
  };
  const Row = (k, joinable) => {
    const c = courseById(COURSES, k.courseId);
    const lec = c.lectures?.[k.lectureNo - 1];
    const kStudents = (k.studentIds && k.studentIds.length) ? k.studentIds : c.studentIds || [];
    const isJoined = joined?.classId === k.id;
    return (
      <div key={k.id} style={{ ...S.card, padding: 16, display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap", borderLeft: `4px solid ${c.color || C.emerald}` }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontWeight: 800, fontSize: 15 }}>{c.name} <span style={{ color: C.muted, fontWeight: 600, fontSize: 12.5 }}>· লেকচার {bn(k.lectureNo)}</span> {k.kind && k.kind !== "নিয়মিত ক্লাস" && <Tag color={C.red} bg={C.redBg}>{k.kind}</Tag>}</div>
          <div style={{ fontSize: 12.5, color: C.muted }}>{lec?.title} · উস্তাদ: {userById(k.teacherId || c.teacherId).name}</div>
          {user.role !== "student" && <div style={{ fontSize: 12, color: C.muted }}>👥 শিক্ষার্থী: {kStudents.map((s) => userById(s).name).join(", ") || "—"}</div>}
          {k.req && user.role !== "student" && <div style={{ fontSize: 12, color: "#a16207", marginTop: 2 }}>📌 অভিভাবকের রিকোয়ারমেন্ট: {k.req}</div>}
          {k.status === "postponed" && <div style={{ fontSize: 12.5, color: C.red, marginTop: 4, background: C.redBg, padding: "6px 10px", borderRadius: 8 }}>⛔ ক্লাসটি অনিবার্য কারণে / উস্তাদ-উস্তাদা অসুস্থ থাকার দরুন স্থগিত করা হয়েছে। পরবর্তীতে শিডিউল করে মেকআপ করা হবে ইনশাআল্লাহ।</div>}
          <div style={{ fontSize: 12.5, color: C.text, marginTop: 2 }}>📅 {fmtDate(k.date)} · 🕐 {k.time} · {bn(k.dur)} মিনিট</div>
          {isJoined && <div style={{ fontSize: 13, marginTop: 6 }}>⏱️ ক্লাসে আছেন: <LiveTimer start={joined.start} demoFast={demoFast} /></div>}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {joinable && !isJoined && k.status !== "postponed" && <a href={k.zoom} target="_blank" rel="noreferrer" onClick={() => join(k)} style={{ textDecoration: "none" }}><Btn kind="gold">🎥 জুমে জয়েন করুন</Btn></a>}
          {isJoined && <Btn kind="danger" onClick={leave}>ক্লাস ত্যাগ ও হাজিরা জমা</Btn>}
          {isAdm(user) && <Btn sm kind="soft" onClick={() => startEdit(k)}>✏️ এডিট</Btn>}
          {isDir(user) && <Btn sm kind="danger" onClick={() => delClass(k.id)}>মুছুন</Btn>}
          {k.status === "postponed" && <Tag color={C.red} bg={C.redBg}>⛔ স্থগিত</Tag>}
          {!joinable && k.status !== "postponed" && <Tag color={k.status === "done" ? C.green : C.blue} bg={k.status === "done" ? C.greenBg : C.blueBg}>{k.status === "done" ? "সম্পন্ন" : "আসন্ন"}</Tag>}
        </div>
      </div>
    );
  };
  return (
    <>
      <Section title="আজকের ক্লাস" sub="সময় হলে এক ক্লিকে জুম মিটিং খুলে যাবে — ৪০ মিনিটের কম থাকলে হাজিরা গণ্য হবে না"
        action={<div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label style={{ fontSize: 12, color: C.muted, display: "flex", alignItems: "center", gap: 5, cursor: "pointer" }}>
            <input type="checkbox" checked={demoFast} onChange={(e) => setDemoFast(e.target.checked)} /> ডেমো মোড (১ সেকেন্ড = ১ মিনিট)
          </label>
          {isAdm(user) && <Btn onClick={() => setShow(true)}>+ ক্লাস শিডিউল</Btn>}
        </div>}>
        <div style={{ display: "grid", gap: 10 }}>
          {today.length === 0 && <div style={{ ...S.card, textAlign: "center", color: C.muted }}>আজ কোনো ক্লাস নেই।</div>}
          {today.map((k) => Row(k, user.role !== "admin" || true))}
        </div>
      </Section>
      <Section title="আসন্ন ক্লাস"><div style={{ display: "grid", gap: 10 }}>{upcoming.length === 0 ? <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>কিছু নেই</div> : upcoming.map((k) => Row(k, false))}</div></Section>
      <Section title="বিগত ক্লাস"><div style={{ display: "grid", gap: 10 }}>{past.map((k) => Row(k, false))}</div></Section>
      {rate && <RatingPopup courseName={rate.courseName} onSubmit={submitRating} onSkip={() => setRate(null)} />}
      {show && (
        <Modal title={editId ? "✏️ ক্লাস শিডিউল এডিট করুন" : "নতুন ক্লাস শিডিউল করুন"} onClose={() => { setShow(false); setEditId(null); setF(blankSched()); }} wide>
          <div style={{ padding: "9px 12px", borderRadius: 10, background: C.amberBg, fontSize: 12, color: "#a16207", marginBottom: 12 }}>💡 অসুস্থতা বা অন্য কারণে ক্লাস ছুটে গেলে এখান থেকে মেকআপ/সাপোর্ট/রিকভারি/ট্রায়াল ক্লাস বানিয়ে দিন — তারিখ-সময় অনুযায়ী স্টুডেন্ট ও উস্তাদের পোর্টালে জয়েন অপশন অটো চলে যাবে।</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><label style={S.label}>ক্লাসের ধরন</label>
              <select style={S.input} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>{CLASS_KINDS.map((x) => <option key={x}>{x}</option>)}</select></div>
            <div><label style={S.label}>কোর্স</label>
              <select style={S.input} value={f.courseId} onChange={(e) => { const c = courseById(courses, e.target.value); setF({ ...f, courseId: e.target.value, teacherId: c.teacherId || f.teacherId }); }}>{courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>উস্তাদ/উস্তাদা — কার কাছে পড়বে</label>
            <select style={S.input} value={f.teacherId} onChange={(e) => setF({ ...f, teacherId: e.target.value })}>{USERS.filter((u) => u.role === "teacher").map((t) => <option key={t.id} value={t.id}>{t.name} ({t.sub})</option>)}</select></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>শিক্ষার্থী বাছাই করুন — এক এক করে ({bn(f.studentIds.length)} জন নির্বাচিত; কাউকে না বাছলে কোর্সের সবাই)</label>
            <StudentPicker selected={f.studentIds} onToggle={(id) => setF({ ...f, studentIds: f.studentIds.includes(id) ? f.studentIds.filter((x) => x !== id) : [...f.studentIds, id] })} /></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 10 }}>
            <div><label style={S.label}>তারিখ</label><input type="date" style={S.input} value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} /></div>
            <div><label style={S.label}>সময়</label><input type="time" style={S.input} value={f.time} onChange={(e) => setF({ ...f, time: e.target.value })} /></div>
            <div><label style={S.label}>সময়কাল (মিনিট)</label><input type="number" style={S.input} value={f.dur} onChange={(e) => setF({ ...f, dur: e.target.value })} /></div>
            <div><label style={S.label}>লেকচার নং</label><input type="number" min="1" style={S.input} value={f.lectureNo} onChange={(e) => setF({ ...f, lectureNo: e.target.value })} /></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>জুম লিংক</label><input style={S.input} value={f.zoom} onChange={(e) => setF({ ...f, zoom: e.target.value })} /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>অভিভাবকের রিকোয়ারমেন্ট (ঐচ্ছিক)</label>
            <textarea rows={2} style={{ ...S.input, resize: "vertical" }} value={f.req} onChange={(e) => setF({ ...f, req: e.target.value })} placeholder="যেমন: তিলাওয়াতের ভুলগুলোতে বেশি জোর দেবেন, লন্ডন সময় সন্ধ্যার পর..." /></div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={addClass}>{editId ? "✏️ আপডেট করুন" : "শিডিউল করুন ও সবাইকে নোটিফিকেশন পাঠান"}</Btn>
        </Modal>
      )}
    </>
  );
}

/* ═══════════════ লেকচার প্ল্যান — টিক/ক্রস (ফিচার ৩) ═══════════════ */
function LecturePlan({ db, courses, user, refresh }) {
  const [sel, setSel] = useState(courses[0]?.id);
  const [form, setForm] = useState(null); // পরিচালকের বিল্ডার: {mode:"new"} বা {mode:"edit", lec}
  const sylList = (db.syllabus || []).filter((s) => s.courseId === sel); // এ কোর্সের সিলেবাস
  const openNew = () => setForm({ mode: "new", title: "", selIds: [] });
  const openEdit = (lec) => setForm({ mode: "edit", lecId: lec.id, title: lec.title, selIds: lec.topics.map((t) => t.syllabusId).filter(Boolean) });
  const toggleSyl = (id) => setForm({ ...form, selIds: form.selIds.includes(id) ? form.selIds.filter((x) => x !== id) : [...form.selIds, id] });
  const saveForm = () => {
    const c = courseById(courses, sel);
    if (!form.title.trim()) return notice("লেকচারের শিরোনাম দিন।");
    if (!form.selIds.length) return notice("সিলেবাস থেকে অন্তত একটি টপিক বাছাই করুন।");
    const picked = sylList.filter((s) => form.selIds.includes(s.id));
    if (form.mode === "new") {
      const topics = picked.map((s) => ({ id: uid(), syllabusId: s.id, text: sylLabel(s), covered: null }));
      c.lectures.push({ id: uid(), no: c.lectures.length + 1, title: form.title.trim(), topics, date: null });
    } else {
      const lec = c.lectures.find((l) => l.id === form.lecId);
      if (lec) {
        lec.title = form.title.trim();
        lec.topics = picked.map((s) => { // আগের টিক/ক্রস অক্ষত থাকে
          const old = lec.topics.find((t) => t.syllabusId === s.id);
          return old ? { ...old, text: sylLabel(s) } : { id: uid(), syllabusId: s.id, text: sylLabel(s), covered: null };
        });
      }
    }
    setForm(null); refresh();
  };
  const delLecture = (lec) => askConfirm(`"লেকচার ${bn(lec.no)}: ${lec.title}" মুছে ফেলবেন?`, () => {
    const c = courseById(courses, sel);
    const i = c.lectures.findIndex((l) => l.id === lec.id);
    if (i > -1) c.lectures.splice(i, 1);
    c.lectures.forEach((l, j) => (l.no = j + 1)); // নম্বর পুনর্বিন্যাস
    refresh();
  });
  const course = courseById(courses, sel);
  const canMark = user.role === "teacher" && course.teacherId === user.id;
  const hasGrant = user.role === "teacher" && db.permissions?.fixCross?.[user.id]; // পরিচালকের দেওয়া বিশেষ অনুমতি
  const isAdmin = isAdm(user) || hasGrant;
  const mark = (lec, topic, val) => {
    // টিচার শুধু চিহ্নিত করতে পারবে; লাল ক্রস ঠিক করতে পারবে কেবল এডমিন
    if (!canMark && !isAdmin) return;
    if (canMark && !isAdmin && topic.covered === false) return notice("লাল ক্রস কেবল এডমিন/পরিচালক ঠিক করতে পারবেন — অথবা পরিচালক আপনাকে অনুমতি দিলে।");
    topic.covered = val;
    if (!lec.date) lec.date = todayISO();
    refresh();
  };
  const cov = coverageOf(course);
  return (
    <Section title="লেকচার প্ল্যান ও টপিক কভারেজ" sub="পরিচালক লেকচার প্ল্যান তৈরি করবেন · কভার করা টপিক ✔ সবুজ · বাদ পড়া ✘ লাল — লাল ক্রস কেবল এডমিন/পরিচালক ঠিক করবেন"
      action={isDir(user) && <Btn onClick={openNew}>+ লেকচার যোগ করুন</Btn>}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
        {courses.map((c) => <Btn key={c.id} sm kind={sel === c.id ? "primary" : "soft"} onClick={() => setSel(c.id)}>{c.name}</Btn>)}
      </div>
      <div style={{ ...S.card, marginBottom: 12, display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 180 }}>
          <div style={{ fontWeight: 800 }}>{course.name}</div>
          <div style={S.sub}>উস্তাদ: {userById(course.teacherId).name} · মোট লেকচার: {bn(course.lectures?.length || 0)}</div>
        </div>
        <div style={{ minWidth: 200, flex: 1 }}>
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 4 }}>সিলেবাস অগ্রগতি — {bn(cov.pct)}% ({bn(cov.done)}/{bn(cov.total)} টপিক)</div>
          <div style={{ height: 10, background: C.cream, borderRadius: 99 }}><div style={{ width: cov.pct + "%", height: "100%", background: `linear-gradient(90deg, ${C.emerald}, ${C.gold})`, borderRadius: 99, transition: "width .4s" }} /></div>
        </div>
      </div>
      {(canMark || isAdmin) && <div style={{ padding: "10px 14px", borderRadius: 12, background: C.amberBg, border: `1px solid ${C.goldL}`, fontSize: 12.5, marginBottom: 10 }}>💡 প্রতিটি টপিকের পাশের <b style={{ color: C.green }}>"✔ কভার হয়েছে"</b> বা <b style={{ color: C.red }}>"✘ বাদ পড়েছে"</b> বাটনে ক্লিক করে মার্ক করুন — অথবা এক ক্লিকে "পুরো লেকচার কভার" করুন। মার্ক করলেই স্টুডেন্ট ও এডমিন ড্যাশবোর্ডে সবুজ/লাল হয়ে দেখাবে।</div>}
      {(course.lectures || []).length === 0 && (
        <div style={{ ...S.card, textAlign: "center", color: C.muted, padding: 28 }}>
          📋 এই কোর্সের লেকচার প্ল্যান এখনো তৈরি হয়নি।{isDir(user) ? " ওপরের \"+ লেকচার যোগ করুন\" বাটন দিয়ে শুরু করুন।" : " পরিচালক তৈরি করলে এখানে দেখা যাবে ইনশাআল্লাহ।"}
        </div>
      )}
      <div style={{ display: "grid", gap: 10 }}>
        {course.lectures?.map((lec) => {
          const st = lec.topics.every((t) => t.covered === true) ? "done" : lec.topics.some((t) => t.covered === false) ? "missed" : lec.topics.some((t) => t.covered) ? "partial" : "pending";
          return (
            <div key={lec.id} style={{ ...S.card, padding: 16, borderLeft: `4px solid ${st === "done" ? C.green : st === "missed" ? C.red : st === "partial" ? C.gold : C.line}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", marginBottom: 8 }}>
                <div style={{ fontWeight: 800 }}>লেকচার {bn(lec.no)}: {lec.title}</div>
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  {lec.date && <span style={{ fontSize: 11.5, color: C.muted }}>{fmtDate(lec.date)}</span>}
                  {isDir(user) && <><Btn sm kind="soft" onClick={() => openEdit(lec)}>✏️</Btn><Btn sm kind="danger" onClick={() => delLecture(lec)}>🗑</Btn></>}
                  {(canMark || isAdmin) && st !== "done" && <Btn sm kind="ghost" onClick={() => { lec.topics.forEach((tp) => { if (tp.covered !== false || isAdmin) tp.covered = true; }); if (!lec.date) lec.date = todayISO(); refresh(); }}>✔ পুরো লেকচার কভার</Btn>}
                  {st === "done" && <Tag>সম্পূর্ণ কভার ✔</Tag>}
                  {st === "missed" && <Tag color={C.red} bg={C.redBg}>টপিক বাদ পড়েছে ✘</Tag>}
                  {st === "partial" && <Tag color={C.gold} bg={C.amberBg}>আংশিক</Tag>}
                </div>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                {lec.topics.map((tp) => (
                  <div key={tp.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 10px", borderRadius: 10, flexWrap: "wrap", background: tp.covered === true ? C.greenBg : tp.covered === false ? C.redBg : C.cream }}>
                    <span style={{ width: 22, height: 22, borderRadius: 6, display: "grid", placeItems: "center", fontWeight: 900, fontSize: 13, background: "#fff", color: tp.covered === true ? C.green : tp.covered === false ? C.red : C.muted, border: `1.5px solid ${C.line}` }}>{tp.covered === true ? "✔" : tp.covered === false ? "✘" : "–"}</span>
                    <span style={{ flex: 1, fontSize: 13.5, color: tp.covered === false ? C.red : C.text }}>{tp.text}</span>
                    {(canMark || isAdmin) && (
                      <span style={{ display: "flex", gap: 5, flexWrap: "wrap", justifyContent: "flex-end" }}>
                        <Btn sm style={{ background: tp.covered === true ? C.green : "#fff", color: tp.covered === true ? "#fff" : C.green, border: `1.5px solid ${C.green}` }} onClick={() => mark(lec, tp, true)}>✔ কভার হয়েছে</Btn>
                        <Btn sm style={{ background: tp.covered === false ? C.red : "#fff", color: tp.covered === false ? "#fff" : C.red, border: `1.5px solid ${C.red}` }} onClick={() => mark(lec, tp, false)}>✘ বাদ পড়েছে</Btn>
                        {isAdmin && <Btn sm kind="soft" onClick={() => mark(lec, tp, null)}>রিসেট</Btn>}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      {form && (
        <Modal title={form.mode === "new" ? `+ নতুন লেকচার — ${course.name}` : `✏️ লেকচার এডিট (টিক/ক্রস অক্ষত থাকবে)`} onClose={() => setForm(null)} wide>
          <label style={S.label}>লেকচারের শিরোনাম</label>
          <input style={S.input} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="যেমন: হরকত — যবর, যের, পেশ" />
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>সিলেবাস থেকে টপিক বাছাই করুন — {bn(form.selIds.length)}টি নির্বাচিত (আলাদা লেখার দরকার নেই)</label>
            {sylList.length === 0 ? (
              <div style={{ padding: "14px 12px", borderRadius: 10, background: C.amberBg, fontSize: 12.5, color: "#a16207" }}>
                ⚠️ "{course.name}" কোর্সের সিলেবাস এখনো তৈরি হয়নি — আগে 📜 সিলেবাস মেনুতে গিয়ে বই/লেসন/পৃষ্ঠা/লাইন যোগ করুন, তারপর এখানে বাছাই করতে পারবেন।
              </div>
            ) : (
              <div style={{ maxHeight: 220, overflowY: "auto", border: `1.5px solid ${C.line}`, borderRadius: 10, padding: 6, background: "#fff" }}>
                {sylList.map((s) => (
                  <label key={s.id} style={{ display: "flex", gap: 8, alignItems: "flex-start", padding: "7px 8px", fontSize: 13, cursor: "pointer", borderRadius: 8, background: form.selIds.includes(s.id) ? C.greenBg : "transparent" }}>
                    <input type="checkbox" checked={form.selIds.includes(s.id)} onChange={() => toggleSyl(s.id)} style={{ marginTop: 3 }} />
                    <span><b>{s.book && s.book !== "অন্যান্য" ? s.book + " — " : ""}{s.lesson}</b>{s.pages && <span style={{ color: C.muted }}> · পৃষ্ঠা: {s.pages}</span>}{s.lines && <span style={{ color: C.muted }}> · লাইন: {s.lines}</span>}{s.note && <div style={{ fontSize: 11.5, color: C.muted }}>💬 {s.note}</div>}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={saveForm}>{form.mode === "new" ? "+ লেকচার যোগ করুন" : "✏️ সংরক্ষণ করুন"}</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ হাজিরা রিপোর্ট (ফিচার ৪) ═══════════════ */
function AttendanceView({ db, courses, user }) {
  const rows = db.attendance
    .map((a) => ({ a, k: db.classes.find((k) => k.id === a.classId) }))
    .filter(({ k }) => k && courseById(courses, k.courseId).id)
    .filter(({ a }) => (user.role === "student" ? a.userId === user.id : user.role === "teacher" ? true : true))
    .map(({ a, k }) => {
      const c = courseById(courses, k.courseId);
      const ok = a.minutes >= 40;
      return [userById(a.userId).name, c.name, fmtDate(k.date), `${bn(a.minutes)} মিনিট`, ok ? <Tag key="t">উপস্থিত ✔</Tag> : <Tag key="t" color={C.red} bg={C.redBg}>অনুপস্থিত (৪০ মিনিটের কম)</Tag>];
    });
  return (
    <Section title="হাজিরা রিপোর্ট" sub="ন্যূনতম ৪০ মিনিট ক্লাসে থাকলে তবেই হাজিরা গণ্য হয়">
      <Table head={["নাম", "কোর্স", "তারিখ", "উপস্থিতি", "অবস্থা"]} rows={rows} />
    </Section>
  );
}

/* ═══════════════ ভাগ করা টুল: প্রশ্ন বিল্ডার, জমা দেওয়া, মূল্যায়ন ═══════════════ */

/* প্রশ্ন বানানোর বিল্ডার — লিখিত প্রশ্ন বা MCQ */
function QBuilder({ qs, setQs, allowMcq }) {
  const upd = (id, patch) => setQs(qs.map((q) => (q.id === id ? { ...q, ...patch } : q)));
  return (
    <div style={{ marginTop: 10 }}>
      <label style={S.label}>প্রশ্নসমূহ</label>
      {qs.map((q, i) => (
        <div key={q.id} style={{ border: `1px solid ${C.line}`, borderRadius: 12, padding: 10, marginBottom: 8, background: C.cream }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <b style={{ fontSize: 13 }}>{bn(i + 1)}.</b>
            <input style={{ ...S.input, flex: 1 }} value={q.q} onChange={(e) => upd(q.id, { q: e.target.value })} placeholder="প্রশ্ন লিখুন..." />
            <Btn sm kind="danger" onClick={() => setQs(qs.filter((x) => x.id !== q.id))}>✕</Btn>
          </div>
          {q.type === "mcq" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginTop: 8 }}>
              {q.options.map((op, oi) => (
                <div key={oi} style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input type="radio" checked={q.correct === oi} onChange={() => upd(q.id, { correct: oi })} title="সঠিক উত্তর" />
                  <input style={{ ...S.input, padding: "7px 10px", fontSize: 13 }} value={op} placeholder={`অপশন ${bn(oi + 1)}`}
                    onChange={(e) => upd(q.id, { options: q.options.map((o, j) => (j === oi ? e.target.value : o)) })} />
                </div>
              ))}
              <div style={{ gridColumn: "1/-1", fontSize: 11, color: C.muted }}>⭕ রেডিও বাটনে সঠিক উত্তর নির্বাচন করুন — মূল্যায়নের সময় অটো-হিসাব দেখাবে</div>
            </div>
          )}
        </div>
      ))}
      <div style={{ display: "flex", gap: 8 }}>
        <Btn sm kind="ghost" onClick={() => setQs([...qs, { id: uid(), q: "", type: "text" }])}>+ লিখিত প্রশ্ন</Btn>
        {allowMcq && <Btn sm kind="ghost" onClick={() => setQs([...qs, { id: uid(), q: "", type: "mcq", options: ["", "", "", ""], correct: 0 }])}>+ MCQ প্রশ্ন</Btn>}
      </div>
    </div>
  );
}

/* স্টুডেন্টের জমা — ফরম পূরণ বা ছবি/PDF আপলোড */
function SubmitWork({ item, kind, onClose, onDone }) {
  const [ans, setAns] = useState({});
  const [img, setImg] = useState(null);
  const [note, setNote] = useState("");
  const [tab, setTab] = useState(item.mode === "form" && item.questions?.length ? "form" : "photo");
  const pickFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => setImg({ data: r.result, name: f.name, isPdf: f.type === "application/pdf" });
    r.readAsDataURL(f);
  };
  const submit = () => {
    if (tab === "form" && item.questions.some((q) => !ans[q.id] && ans[q.id] !== 0)) return notice("সব প্রশ্নের উত্তর দিন।");
    if (tab === "photo" && !img) return notice("ছবি বা PDF নির্বাচন করুন।");
    onDone({ answers: tab === "form" ? ans : null, image: tab === "photo" ? img : null, note: note.trim() });
  };
  return (
    <Modal title={`${kind} জমা — ${item.title}`} onClose={onClose} wide>
      {item.mode === "form" && item.questions?.length > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <Btn sm kind={tab === "form" ? "primary" : "soft"} onClick={() => setTab("form")}>📋 ফরম পূরণ করে</Btn>
          <Btn sm kind={tab === "photo" ? "primary" : "soft"} onClick={() => setTab("photo")}>📷 ছবি তুলে</Btn>
        </div>
      )}
      {tab === "form" ? (
        <div>
          {item.questions.map((q, i) => (
            <div key={q.id} style={{ marginBottom: 14 }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 6 }}>{bn(i + 1)}. {q.q}</div>
              {q.type === "mcq" ? (
                <div style={{ display: "grid", gap: 6 }}>
                  {q.options.map((op, oi) => (
                    <label key={oi} style={{ display: "flex", gap: 8, alignItems: "center", padding: "8px 12px", borderRadius: 10, cursor: "pointer", border: `1.5px solid ${ans[q.id] === oi ? C.emerald : C.line}`, background: ans[q.id] === oi ? C.greenBg : "#fff", fontSize: 13.5 }}>
                      <input type="radio" name={q.id} checked={ans[q.id] === oi} onChange={() => setAns({ ...ans, [q.id]: oi })} /> {op}
                    </label>
                  ))}
                </div>
              ) : (
                <textarea rows={2} style={{ ...S.input, resize: "vertical" }} value={ans[q.id] || ""} onChange={(e) => setAns({ ...ans, [q.id]: e.target.value })} placeholder="উত্তর লিখুন..." />
              )}
            </div>
          ))}
        </div>
      ) : (
        <div>
          <div style={{ fontSize: 13, color: C.muted, marginBottom: 8 }}>{item.desc}</div>
          <label style={{ display: "grid", placeItems: "center", gap: 6, padding: "26px 14px", border: `2px dashed ${img ? C.emerald : C.line}`, borderRadius: 14, cursor: "pointer", background: img ? C.greenBg : C.cream, textAlign: "center" }}>
            <span style={{ fontSize: 30 }}>{img ? "✅" : "📷"}</span>
            <span style={{ fontSize: 13.5, fontWeight: 700 }}>{img ? img.name : "ছবি তুলুন বা ফাইল বেছে নিন (ছবি / PDF)"}</span>
            <input type="file" accept="image/*,application/pdf" capture="environment" style={{ display: "none" }} onChange={pickFile} />
          </label>
          {img && !img.isPdf && <img src={img.data} alt="জমা" style={{ width: "100%", borderRadius: 12, marginTop: 10, border: `1px solid ${C.line}` }} />}
        </div>
      )}
      <div style={{ marginTop: 8 }}><label style={S.label}>মন্তব্য (ঐচ্ছিক)</label><input style={S.input} value={note} onChange={(e) => setNote(e.target.value)} placeholder="উস্তাদের জন্য কোনো কথা..." /></div>
      <Btn style={{ marginTop: 14, width: "100%", justifyContent: "center" }} onClick={submit}>জমা দিন</Btn>
    </Modal>
  );
}

/* মূল্যায়ন প্যানেল — জমা দেওয়া ফরম/ছবি খুলে সেখানেই মার্ক, সাথে সাথে স্টুডেন্ট পোর্টালে */
function EvalWork({ item, onClose, onMark }) {
  const [open, setOpen] = useState(item.subs[0]?.id || null);
  const mcqScore = (sub) => {
    if (!sub.answers) return null;
    const mcqs = (item.questions || []).filter((q) => q.type === "mcq");
    if (!mcqs.length) return null;
    return { ok: mcqs.filter((q) => sub.answers[q.id] === q.correct).length, total: mcqs.length };
  };
  return (
    <Modal title={`মূল্যায়ন — ${item.title} (পূর্ণমান ${bn(item.total)})`} onClose={onClose} wide>
      {item.subs.length === 0 && <div style={{ textAlign: "center", color: C.muted, padding: 16 }}>এখনো কেউ জমা দেয়নি।</div>}
      {item.subs.map((sub) => {
        const auto = mcqScore(sub);
        const isOpen = open === sub.id;
        return (
          <div key={sub.id} style={{ border: `1.5px solid ${sub.mark != null ? C.green : C.line}`, borderRadius: 14, marginBottom: 10, overflow: "hidden" }}>
            <div onClick={() => setOpen(isOpen ? null : sub.id)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "11px 14px", cursor: "pointer", background: sub.mark != null ? C.greenBg : C.cream, flexWrap: "wrap" }}>
              <b style={{ flex: 1, fontSize: 14, minWidth: 140 }}>{userById(sub.studentId).name}</b>
              <span style={{ fontSize: 12, color: C.muted }}>{fmtDate(sub.date)}</span>
              {sub.mark != null ? <Tag>মার্ক: {bn(sub.mark)}/{bn(item.total)} ✔</Tag> : <Tag color={C.gold} bg={C.amberBg}>মূল্যায়ন বাকি</Tag>}
              <span style={{ fontSize: 13 }}>{isOpen ? "▲" : "▼ মূল্যায়ন করুন"}</span>
            </div>
            {isOpen && (
              <div style={{ padding: 14 }}>
                {sub.answers ? (
                  <div style={{ marginBottom: 10 }}>
                    {(item.questions || []).map((q, i) => (
                      <div key={q.id} style={{ marginBottom: 10, padding: "9px 12px", borderRadius: 10, background: C.cream }}>
                        <div style={{ fontWeight: 700, fontSize: 13 }}>{bn(i + 1)}. {q.q}</div>
                        {q.type === "mcq" ? (
                          <div style={{ fontSize: 13, marginTop: 3 }}>
                            উত্তর: <b style={{ color: sub.answers[q.id] === q.correct ? C.green : C.red }}>{q.options[sub.answers[q.id]] ?? "—"} {sub.answers[q.id] === q.correct ? "✔" : "✘"}</b>
                            {sub.answers[q.id] !== q.correct && <span style={{ color: C.muted }}> · সঠিক: {q.options[q.correct]}</span>}
                          </div>
                        ) : (
                          <div style={{ fontSize: 13.5, marginTop: 3, whiteSpace: "pre-wrap" }}>{sub.answers[q.id] || "—"}</div>
                        )}
                      </div>
                    ))}
                    {auto && <div style={{ fontSize: 12.5, fontWeight: 700, color: C.blue }}>🤖 MCQ অটো-হিসাব: {bn(auto.ok)}/{bn(auto.total)} সঠিক</div>}
                  </div>
                ) : sub.image ? (
                  <div style={{ marginBottom: 10 }}>
                    {sub.image.isPdf ? (
                      <a href={sub.image.data} download={sub.image.name} style={{ display: "inline-flex", gap: 8, alignItems: "center", padding: "12px 16px", borderRadius: 12, background: C.redBg, color: C.red, fontWeight: 700, textDecoration: "none", fontSize: 13.5 }}>📄 {sub.image.name} — খুলুন/ডাউনলোড</a>
                    ) : (
                      <a href={sub.image.data} target="_blank" rel="noreferrer"><img src={sub.image.data} alt="জমা" style={{ width: "100%", borderRadius: 12, border: `1px solid ${C.line}`, cursor: "zoom-in" }} /></a>
                    )}
                  </div>
                ) : (
                  <div style={{ fontSize: 13, color: C.muted, marginBottom: 10 }}>📎 ফাইল সংযুক্ত নেই (পুরোনো/ডেমো জমা)</div>
                )}
                {sub.note && <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>💬 স্টুডেন্টের মন্তব্য: “{sub.note}”</div>}
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", borderTop: `1px dashed ${C.line}`, paddingTop: 10 }}>
                  <label style={{ fontSize: 13, fontWeight: 700 }}>মার্ক দিন:</label>
                  <input type="number" min="0" max={item.total} defaultValue={sub.mark ?? ""} style={{ ...S.input, width: 90 }} id={"mk-" + sub.id} placeholder={`/${item.total}`} />
                  <Btn sm onClick={() => { const v = document.getElementById("mk-" + sub.id).value; if (v === "") return; onMark(sub, Math.min(+v, item.total)); }}>✔ মার্ক জমা দিন</Btn>
                  <span style={{ fontSize: 11.5, color: C.muted }}>মার্ক দিলেই সাথে সাথে স্টুডেন্ট পোর্টালে চলে যাবে</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </Modal>
  );
}

/* ═══════════════ অ্যাসাইনমেন্ট (ফিচার ৫) — ফরম বা ছবি, মূল্যায়নসহ ═══════════════ */
function AssignmentsView({ db, setDb, courses, user }) {
  const [show, setShow] = useState(false);
  const [doSub, setDoSub] = useState(null);
  const [evalFor, setEvalFor] = useState(null);
  const [f, setF] = useState({ courseId: courses[0]?.id, title: "", desc: "", due: addDays(3), mode: "form", total: 10 });
  const [qs, setQs] = useState([]);
  const list = db.assignments.filter((a) => courseById(courses, a.courseId).id);
  const canCreate = user.role === "teacher" || isAdm(user);
  const add = () => {
    if (!f.title) return notice("শিরোনাম দিন।");
    if (f.mode === "form" && qs.length === 0) return notice("ফরম মোডে অন্তত একটি প্রশ্ন যোগ করুন।");
    setDb((d) => ({ ...d, assignments: [{ id: uid(), ...f, total: +f.total, teacherId: user.id, questions: f.mode === "form" ? qs : [], subs: [] }, ...d.assignments] }));
    setShow(false); setQs([]);
  };
  const del = (id) => setDb((d) => ({ ...d, assignments: d.assignments.filter((a) => a.id !== id) }));
  const submitWork = (a, payload) => {
    setDb((d) => ({ ...d, assignments: d.assignments.map((x) => x.id === a.id ? { ...x, subs: [...x.subs, { id: uid(), studentId: user.id, date: todayISO(), mark: null, ...payload }] } : x) }));
    setDoSub(null);
  };
  const giveMark = (a, sub, mark) => setDb((d) => ({ ...d, assignments: d.assignments.map((x) => x.id === a.id ? { ...x, subs: x.subs.map((s) => s.id === sub.id ? { ...s, mark } : s) } : x) }));
  return (
    <Section title="অ্যাসাইনমেন্ট" sub="ফরম বানিয়ে বা ছবি জমার নির্দেশনা দিয়ে — মূল্যায়ন করলেই মার্ক স্টুডেন্ট পোর্টালে"
      action={canCreate && <Btn onClick={() => setShow(true)}>+ নতুন অ্যাসাইনমেন্ট</Btn>}>
      <div style={{ display: "grid", gap: 10 }}>
        {list.length === 0 && <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>এখনো কোনো অ্যাসাইনমেন্ট নেই।</div>}
        {list.map((a) => {
          const c = courseById(courses, a.courseId);
          const mySub = a.subs.find((s) => s.studentId === user.id);
          const pendingEval = a.subs.filter((s) => s.mark == null).length;
          return (
            <div key={a.id} style={{ ...S.card, padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: 220 }}>
                  <div style={{ fontWeight: 800 }}>{a.title} <Tag color={C.blue} bg={C.blueBg}>{c.name}</Tag> <Tag color={a.mode === "form" ? C.emerald : C.gold} bg={a.mode === "form" ? C.greenBg : C.amberBg}>{a.mode === "form" ? "📋 ফরম" : "📷 ছবি জমা"}</Tag></div>
                  <div style={{ fontSize: 13, color: C.muted, margin: "5px 0" }}>{a.desc}</div>
                  <div style={{ fontSize: 12 }}>📅 শেষ তারিখ: <b>{fmtDate(a.due)}</b> · পূর্ণমান: <b>{bn(a.total)}</b> · জমা: <b>{bn(a.subs.length)}</b> জন{canCreate && pendingEval > 0 && <span style={{ color: C.red }}> · মূল্যায়ন বাকি: {bn(pendingEval)}</span>}</div>
                </div>
                <div style={{ display: "flex", gap: 6, alignItems: "flex-start", flexWrap: "wrap" }}>
                  {user.role === "student" && (mySub
                    ? (mySub.mark != null ? <Tag>প্রাপ্ত মার্ক: {bn(mySub.mark)}/{bn(a.total)} ✔</Tag> : <Tag color={C.gold} bg={C.amberBg}>জমা হয়েছে — মূল্যায়নের অপেক্ষায়</Tag>)
                    : <Btn sm kind="gold" onClick={() => setDoSub(a)}>{a.mode === "form" ? "📋 ফরম পূরণ করে জমা দিন" : "📷 ছবি তুলে জমা দিন"}</Btn>)}
                  {canCreate && <Btn sm kind="ghost" onClick={() => setEvalFor(a)}>🔍 মূল্যায়ন করুন ({bn(a.subs.length)})</Btn>}
                  {isAdm(user) && <Btn sm kind="danger" onClick={() => del(a.id)}>মুছুন</Btn>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {doSub && <SubmitWork item={doSub} kind="অ্যাসাইনমেন্ট" onClose={() => setDoSub(null)} onDone={(p) => submitWork(doSub, p)} />}
      {evalFor && <EvalWork item={db.assignments.find((x) => x.id === evalFor.id)} onClose={() => setEvalFor(null)} onMark={(sub, m) => giveMark(evalFor, sub, m)} />}
      {show && (
        <Modal title="নতুন অ্যাসাইনমেন্ট বানান" onClose={() => setShow(false)} wide>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><label style={S.label}>কোর্স</label><select style={S.input} value={f.courseId} onChange={(e) => setF({ ...f, courseId: e.target.value })}>{courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
            <div><label style={S.label}>পূর্ণমান</label><input type="number" style={S.input} value={f.total} onChange={(e) => setF({ ...f, total: e.target.value })} /></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>শিরোনাম</label><input style={S.input} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>নির্দেশনা / বিবরণ</label><textarea rows={2} style={{ ...S.input, resize: "vertical" }} value={f.desc} onChange={(e) => setF({ ...f, desc: e.target.value })} /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>জমা দেওয়ার ধরন — যেটা ইচ্ছা বানান</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <button onClick={() => setF({ ...f, mode: "form" })} style={{ padding: "12px", borderRadius: 12, cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 13, border: `2px solid ${f.mode === "form" ? C.emerald : C.line}`, background: f.mode === "form" ? C.greenBg : "#fff" }}>📋 ফরম — প্রশ্ন বানিয়ে দিন</button>
              <button onClick={() => setF({ ...f, mode: "photo" })} style={{ padding: "12px", borderRadius: 12, cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 13, border: `2px solid ${f.mode === "photo" ? C.emerald : C.line}`, background: f.mode === "photo" ? C.greenBg : "#fff" }}>📷 ছবি/PDF জমা</button>
            </div></div>
          {f.mode === "form" && <QBuilder qs={qs} setQs={setQs} allowMcq={false} />}
          <div style={{ marginTop: 10 }}><label style={S.label}>শেষ তারিখ</label><input type="date" style={S.input} value={f.due} onChange={(e) => setF({ ...f, due: e.target.value })} /></div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={add}>প্রকাশ করুন</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ পরীক্ষা (ফিচার ৬) — ফরম (MCQ/লিখিত) বা ছবি, মূল্যায়নসহ ═══════════════ */
function ExamsView({ db, setDb, courses, user }) {
  const [show, setShow] = useState(false);
  const [marksFor, setMarksFor] = useState(null);
  const [doSub, setDoSub] = useState(null);
  const [evalFor, setEvalFor] = useState(null);
  const [f, setF] = useState({ type: "mcq", title: "", courseId: courses[0]?.id, total: 30, date: addDays(7), mode: "form" });
  const [qs, setQs] = useState([]);
  const list = db.exams.filter((e) => courseById(courses, e.courseId).id);
  const canCreate = isAdm(user) || user.role === "teacher";
  const add = () => {
    if (!f.title) return notice("শিরোনাম দিন।");
    if (f.mode === "form" && qs.length === 0) return notice("ফরম মোডে অন্তত একটি প্রশ্ন যোগ করুন।");
    setDb((d) => ({ ...d, exams: [{ id: uid(), ...f, total: +f.total, marks: {}, questions: f.mode === "form" ? qs : [], subs: [] }, ...d.exams] }));
    setShow(false); setQs([]);
  };
  const saveMark = (ex, sid, val) => setDb((d) => ({ ...d, exams: d.exams.map((x) => x.id === ex.id ? { ...x, marks: { ...x.marks, [sid]: +val } } : x) }));
  const submitWork = (ex, payload) => {
    setDb((d) => ({ ...d, exams: d.exams.map((x) => x.id === ex.id ? { ...x, subs: [...x.subs, { id: uid(), studentId: user.id, date: todayISO(), mark: null, ...payload }] } : x) }));
    setDoSub(null);
  };
  const giveMark = (ex, sub, mark) => setDb((d) => ({ ...d, exams: d.exams.map((x) => x.id === ex.id
    ? { ...x, subs: x.subs.map((s) => s.id === sub.id ? { ...s, mark } : s), marks: { ...x.marks, [sub.studentId]: mark } } : x) })); // মার্ক দিলেই অটো স্টুডেন্ট পোর্টালে
  return (
    <Section title="পরীক্ষা — মাসিক MCQ ও লাইভ টেস্ট" sub="ফরমে (MCQ/লিখিত) বা ছবিতে — মূল্যায়ন করলেই ফলাফল অটো স্টুডেন্ট পোর্টালে"
      action={canCreate && <Btn onClick={() => setShow(true)}>+ নতুন পরীক্ষা বানান</Btn>}>
      <div style={{ display: "grid", gap: 10 }}>
        {list.map((ex) => {
          const c = courseById(courses, ex.courseId);
          const myMark = ex.marks[user.id];
          const mySub = ex.subs?.find((s) => s.studentId === user.id);
          const pendingEval = (ex.subs || []).filter((s) => s.mark == null).length;
          return (
            <div key={ex.id} style={{ ...S.card, padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontWeight: 800 }}>{ex.title} {ex.type === "mcq" ? <Tag color={C.blue} bg={C.blueBg}>MCQ</Tag> : <Tag color={C.gold} bg={C.amberBg}>লাইভ টেস্ট</Tag>} <Tag color={ex.mode === "form" ? C.emerald : C.gold} bg={ex.mode === "form" ? C.greenBg : C.amberBg}>{ex.mode === "form" ? "📋 ফরম" : "📷 ছবি/খাতা"}</Tag></div>
                  <div style={{ fontSize: 12.5, color: C.muted }}>{c.name} · {fmtDate(ex.date)} · পূর্ণমান {bn(ex.total)}{canCreate && pendingEval > 0 && <span style={{ color: C.red }}> · মূল্যায়ন বাকি: {bn(pendingEval)}</span>}</div>
                </div>
                <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                  {user.role === "student" && (myMark != null
                    ? <div style={{ textAlign: "right" }}><div style={{ fontSize: 22, fontWeight: 900, color: C.emerald }}>{bn(myMark)}<span style={{ fontSize: 13, color: C.muted }}>/{bn(ex.total)}</span></div><Tag color={myMark / ex.total >= 0.8 ? C.green : C.gold} bg={myMark / ex.total >= 0.8 ? C.greenBg : C.amberBg}>{myMark / ex.total >= 0.8 ? "মুমতায" : "জায়্যিদ"}</Tag></div>
                    : mySub
                      ? <Tag color={C.gold} bg={C.amberBg}>জমা হয়েছে — ফলাফলের অপেক্ষায়</Tag>
                      : <Btn sm kind="gold" onClick={() => setDoSub(ex)}>{ex.mode === "form" ? "📋 পরীক্ষা দিন" : "📷 খাতার ছবি জমা দিন"}</Btn>)}
                  {canCreate && <Btn sm kind="ghost" onClick={() => setEvalFor(ex)}>🔍 মূল্যায়ন ({bn((ex.subs || []).length)})</Btn>}
                  {canCreate && <Btn sm kind="soft" onClick={() => setMarksFor(ex)}>সরাসরি মার্ক এন্ট্রি</Btn>}
                  {isDir(user) && <Btn sm kind="danger" onClick={() => setDb((d) => ({ ...d, exams: d.exams.filter((x) => x.id !== ex.id) }))}>মুছুন</Btn>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {doSub && <SubmitWork item={doSub} kind="পরীক্ষা" onClose={() => setDoSub(null)} onDone={(p) => submitWork(doSub, p)} />}
      {evalFor && <EvalWork item={db.exams.find((x) => x.id === evalFor.id)} onClose={() => setEvalFor(null)} onMark={(sub, m) => giveMark(evalFor, sub, m)} />}
      {show && (
        <Modal title="নতুন পরীক্ষা বানান" onClose={() => setShow(false)} wide>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><label style={S.label}>ধরন</label><select style={S.input} value={f.type} onChange={(e) => setF({ ...f, type: e.target.value })}><option value="mcq">মাসিক MCQ</option><option value="live">লাইভ টেস্ট</option></select></div>
            <div><label style={S.label}>কোর্স</label><select style={S.input} value={f.courseId} onChange={(e) => setF({ ...f, courseId: e.target.value })}>{courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
            <div><label style={S.label}>পূর্ণমান</label><input type="number" style={S.input} value={f.total} onChange={(e) => setF({ ...f, total: e.target.value })} /></div>
            <div><label style={S.label}>তারিখ</label><input type="date" style={S.input} value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} /></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>শিরোনাম</label><input style={S.input} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} placeholder="যেমন: মাসিক MCQ — জুলাই ২০২৬" /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>পরীক্ষার ধরন — যেটা ইচ্ছা বানান</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <button onClick={() => setF({ ...f, mode: "form" })} style={{ padding: "12px", borderRadius: 12, cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 13, border: `2px solid ${f.mode === "form" ? C.emerald : C.line}`, background: f.mode === "form" ? C.greenBg : "#fff" }}>📋 ফরম — MCQ/লিখিত প্রশ্ন বানান</button>
              <button onClick={() => setF({ ...f, mode: "photo" })} style={{ padding: "12px", borderRadius: 12, cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 13, border: `2px solid ${f.mode === "photo" ? C.emerald : C.line}`, background: f.mode === "photo" ? C.greenBg : "#fff" }}>📷 খাতার ছবি/PDF জমা</button>
            </div></div>
          {f.mode === "form" && <QBuilder qs={qs} setQs={setQs} allowMcq={true} />}
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={add}>তৈরি করুন</Btn>
        </Modal>
      )}
      {marksFor && (
        <Modal title={`সরাসরি মার্ক এন্ট্রি — ${marksFor.title}`} onClose={() => setMarksFor(null)}>
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>লাইভ টেস্টের মতো জমা ছাড়া পরীক্ষার জন্য — মার্ক দিলেই স্টুডেন্ট পোর্টালে দেখাবে।</div>
          {courseById(courses, marksFor.courseId).studentIds.map((sid) => (
            <div key={sid} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span style={{ flex: 1, fontSize: 14 }}>{userById(sid).name}</span>
              <input type="number" min="0" max={marksFor.total} style={{ ...S.input, width: 90 }} defaultValue={db.exams.find((x) => x.id === marksFor.id)?.marks[sid] ?? ""} onBlur={(e) => e.target.value !== "" && saveMark(marksFor, sid, e.target.value)} placeholder={`/${marksFor.total}`} />
            </div>
          ))}
          <div style={{ fontSize: 12, color: C.muted }}>ঘর থেকে বের হলেই মার্ক সংরক্ষিত হবে।</div>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ স্টুডেন্ট প্রোফাইল ও অগ্রগতি রিপোর্ট (ফিচার ৭) ═══════════════ */
function ProgressView({ db, setDb, courses, user }) {
  const students = user.role === "student" ? [user] : USERS.filter((u) => u.role === "student");
  const [pay, setPay] = useState(false);
  const [maker, setMaker] = useState(false);
  const [pf, setPf] = useState({ method: "বিকাশ", trx: "" });
  const [sel, setSel] = useState(students[0]?.id);
  const st = userById(sel);
  const stCourses = courses.filter((c) => c.studentIds.includes(sel));
  const att = db.attendance.filter((a) => a.userId === sel);
  const present = att.filter((a) => a.minutes >= 40).length;
  const missed = att.filter((a) => a.minutes < 40).length;
  const paid = db.feePayments.filter((p) => p.studentId === sel).reduce((s, p) => s + p.amount, 0);
  const due = (db.dueMonths[sel] || []).length * (st.fee || 0);
  const makeups = db.makeups.filter((m) => m.studentId === sel);
  const exams = db.exams.filter((e) => e.marks[sel] != null);
  const recordPay = () => {
    const month = (db.dueMonths[sel] || [])[0];
    if (!month) return;
    setDb((d) => ({ ...d,
      feePayments: [...d.feePayments, { id: uid(), studentId: sel, amount: st.fee, month, date: todayISO(), method: "নগদ গ্রহণ (অফিস)", status: "verified" }],
      dueMonths: { ...d.dueMonths, [sel]: d.dueMonths[sel].slice(1) } }));
  };
  const studentPay = () => {
    const month = (db.dueMonths[sel] || [])[0];
    if (!month) return;
    setDb((d) => ({ ...d,
      feePayments: [...d.feePayments, { id: uid(), studentId: sel, amount: st.fee, month, date: todayISO(), method: pf.method + (pf.trx ? ` (Trx: ${pf.trx})` : ""), status: "pending" }],
      dueMonths: { ...d.dueMonths, [sel]: d.dueMonths[sel].slice(1) },
      notifications: [{ id: uid(), for: ["admin1", "dir1"], text: `${st.name} — ${month} মাসের ফি ${pf.method}-এ পরিশোধ করেছে, পরিচালকের ভেরিফাই বাকি।`, date: todayISO(), read: false }, ...d.notifications] }));
    setPay(false); setPf({ method: "বিকাশ", trx: "" });
  };
  const verifyPay = (pid) => setDb((d) => ({ ...d, feePayments: d.feePayments.map((p) => p.id === pid ? { ...p, status: "verified" } : p) }));
  return (
    <Section title="শিক্ষার্থীর অগ্রগতি ও রিপোর্ট" sub="অগ্রগতি · ফি · মিসিং ক্লাস · মেকআপ ক্লাস — সব এক জায়গায়" action={isAdm(user) && <Btn kind="gold" sm onClick={() => setMaker(true)}>🧾 রিসিট বানান</Btn>}>
      {maker && <ReceiptMaker user={user} onClose={() => setMaker(false)} />}
      {user.role !== "student" && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
          {students.map((s) => <Btn key={s.id} sm kind={sel === s.id ? "primary" : "soft"} onClick={() => setSel(s.id)}>{s.name}</Btn>)}
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, marginBottom: 14 }}>
        <Stat icon="✅" label="উপস্থিত ক্লাস" value={bn(present)} />
        <Stat icon="❌" label="মিসিং ক্লাস" value={bn(missed)} accent={C.red} note="৪০ মিনিটের কম উপস্থিতিসহ" />
        <Stat icon="💰" label="পরিশোধিত ফি" value={`৳${bn(paid.toLocaleString("en"))}`} accent={C.gold} />
        <Stat icon="⏳" label="বকেয়া" value={`৳${bn(due.toLocaleString("en"))}`} accent={C.red} note={(db.dueMonths[sel] || []).join(", ") || "নেই"} />
      </div>
      <div style={{ display: "grid", gap: 14 }}>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>📈 কোর্সভিত্তিক সিলেবাস অগ্রগতি</div>
          {stCourses.map((c) => { const cv = coverageOf(c); return (
            <div key={c.id} style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}><span>{c.name}</span><b>{bn(cv.pct)}%</b></div>
              <div style={{ height: 9, background: C.cream, borderRadius: 99 }}><div style={{ width: cv.pct + "%", height: "100%", background: c.color, borderRadius: 99 }} /></div>
            </div>
          ); })}
        </div>
        <div style={{ ...S.card }}>
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
            <div style={{ fontWeight: 800 }}>💳 ফি পরিশোধের ইতিহাস</div>
            <span style={{ display: "flex", gap: 8 }}>{user.role === "student" && due > 0 && <Btn sm kind="gold" onClick={() => setPay(true)}>💳 ফি পরিশোধ করুন</Btn>}{isAdm(user) && due > 0 && <Btn sm kind="gold" onClick={recordPay}>+ এক মাসের পেমেন্ট রেকর্ড করুন</Btn>}</span>
          </div>
          <Table head={["মাস", "পরিমাণ", "তারিখ", "মাধ্যম", "অবস্থা", "রিসিট"]} rows={db.feePayments.filter((p) => p.studentId === sel).map((p) => [p.month, `৳${bn(p.amount.toLocaleString("en"))}`, fmtDate(p.date), p.method,
            p.status === "pending"
              ? (isDir(user) ? <Btn key="v" sm kind="gold" onClick={() => verifyPay(p.id)}>✔ ভেরিফাই করুন</Btn> : <Tag key="t" color={C.gold} bg={C.amberBg}>⏳ পেন্ডিং</Tag>)
              : <Tag key="t">যাচাইকৃত ✔</Tag>,
            <Btn key="r" sm kind="soft" onClick={() => printReceipt({ ...p, date: fmtDate(p.date) }, st, "ফি পরিশোধ রিসিট")}>🧾 PDF</Btn>])} />
          {pay && (
            <Modal title={`ফি পরিশোধ — ${(db.dueMonths[sel] || [])[0] || ""}`} onClose={() => setPay(false)}>
              <div style={{ ...S.card, padding: 12, background: C.amberBg, border: "none", marginBottom: 12, fontSize: 13 }}>পরিমাণ: <b>৳{bn((st.fee || 0).toLocaleString("en"))}</b> · পরিশোধের পর এডমিন যাচাই করলে নিশ্চিত হবে।</div>
              <label style={S.label}>পেমেন্ট মাধ্যম</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 12 }}>
                {["বিকাশ", "নগদ", "ব্যাংক ট্রান্সফার"].map((m) => (
                  <button key={m} onClick={() => setPf({ ...pf, method: m })} style={{ padding: "12px 6px", borderRadius: 10, cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 13, border: `2px solid ${pf.method === m ? C.emerald : C.line}`, background: pf.method === m ? C.greenBg : "#fff", color: pf.method === m ? C.emerald : C.text }}>
                    {m === "বিকাশ" ? "📱" : m === "নগদ" ? "🟠" : "🏦"}<br />{m}
                  </button>
                ))}
              </div>
              <label style={S.label}>ট্রানজেকশন আইডি / রেফারেন্স (ঐচ্ছিক)</label>
              <input style={S.input} value={pf.trx} onChange={(e) => setPf({ ...pf, trx: e.target.value })} placeholder="যেমন: 9HX2K7..." />
              <Btn style={{ marginTop: 14, width: "100%", justifyContent: "center" }} onClick={studentPay}>পরিশোধ সম্পন্ন করুন</Btn>
            </Modal>
          )}
        </div>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>📝 পরীক্ষার ফলাফল</div>
          <Table head={["পরীক্ষা", "তারিখ", "প্রাপ্ত মার্ক"]} rows={exams.map((e) => [e.title, fmtDate(e.date), `${bn(e.marks[sel])}/${bn(e.total)}`])} empty="এখনো কোনো ফল নেই" />
        </div>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>🔁 মেকআপ ক্লাস</div>
          <Table head={["কোর্স", "কারণ", "তারিখ ও সময়", "অবস্থা"]} rows={makeups.map((m) => [courseById(courses, m.courseId).name, m.reason, `${fmtDate(m.date)} · ${m.time}`, <Tag key="t" color={C.blue} bg={C.blueBg}>{m.status === "scheduled" ? "নির্ধারিত" : "সম্পন্ন"}</Tag>])} empty="কোনো মেকআপ ক্লাস নেই" />
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════ হিসাব-নিকাশ (ফিচার ৯) ═══════════════ */
function AccountsView({ db, setDb, user }) {
  const [maker, setMaker] = useState(false);
  const income = db.feePayments.reduce((s, p) => s + p.amount, 0);
  const expense = db.teacherPayments.reduce((s, p) => s + p.amount, 0);
  const teachers = USERS.filter((u) => u.role === "teacher");
  const payTeacher = (t) => {
    const month = (db.dueMonths[t.id] || [])[0];
    if (!month) return;
    setDb((d) => ({ ...d,
      teacherPayments: [...d.teacherPayments, { id: uid(), teacherId: t.id, amount: t.salary, month, date: todayISO(), method: "ব্যাংক" }],
      dueMonths: { ...d.dueMonths, [t.id]: d.dueMonths[t.id].slice(1) } }));
  };
  return (
    <Section title="হিসাব-নিকাশ" sub="আয় (স্টুডেন্ট ফি) · ব্যয় (উস্তাদদের বেতন) · বকেয়া" action={<Btn kind="gold" onClick={() => setMaker(true)}>🧾 রিসিট বানান</Btn>}>
      {maker && <ReceiptMaker user={user} onClose={() => setMaker(false)} />}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginBottom: 16 }}>
        <Stat icon="📥" label="মোট আয় (ফি)" value={`৳${bn(income.toLocaleString("en"))}`} />
        <Stat icon="📤" label="মোট ব্যয় (বেতন)" value={`৳${bn(expense.toLocaleString("en"))}`} accent={C.red} />
        <Stat icon="🏦" label="ব্যালেন্স" value={`৳${bn((income - expense).toLocaleString("en"))}`} accent={C.gold} />
      </div>
      <div style={{ ...S.card, marginBottom: 14 }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>👳 উস্তাদদের বেতন</div>
        <Table head={["নাম", "মাসিক বেতন", "বকেয়া মাস", "অ্যাকশন"]}
          rows={teachers.map((t) => {
            const dues = db.dueMonths[t.id] || [];
            return [t.name, `৳${bn(t.salary.toLocaleString("en"))}`, dues.length ? <Tag key="d" color={C.red} bg={C.redBg}>{dues.join(", ")}</Tag> : <Tag key="d">পরিশোধিত ✔</Tag>, dues.length ? <Btn key="b" sm kind="gold" onClick={() => payTeacher(t)}>পেমেন্ট দিন</Btn> : "—"];
          })} />
      </div>
      <div style={{ ...S.card, marginBottom: 14 }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>📤 বেতন পরিশোধের ইতিহাস</div>
        <Table head={["উস্তাদ", "মাস", "পরিমাণ", "তারিখ", "মাধ্যম", "ভাউচার"]} rows={db.teacherPayments.map((p) => [userById(p.teacherId).name, p.month, `৳${bn(p.amount.toLocaleString("en"))}`, fmtDate(p.date), p.method, <Btn key="r" sm kind="soft" onClick={() => printReceipt({ ...p, date: fmtDate(p.date) }, userById(p.teacherId), "বেতন পরিশোধ ভাউচার")}>🧾 PDF</Btn>])} />
      </div>
      <div style={{ ...S.card }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>📥 স্টুডেন্ট ফি বকেয়া</div>
        <Table head={["স্টুডেন্ট", "মাসিক ফি", "বকেয়া মাস", "বকেয়া টাকা"]}
          rows={USERS.filter((u) => u.role === "student").map((s) => {
            const dues = db.dueMonths[s.id] || [];
            return [s.name, `৳${bn(s.fee.toLocaleString("en"))}`, dues.join(", ") || "—", dues.length ? <Tag key="t" color={C.red} bg={C.redBg}>৳{bn((dues.length * s.fee).toLocaleString("en"))}</Tag> : <Tag key="t">পরিশোধিত ✔</Tag>];
          })} />
      </div>
    </Section>
  );
}

/* ═══════════════ ওয়েবসাইট ফর্ম সাবমিশন (ফিচার ৮) ═══════════════ */
function FormsView({ db, setDb }) {
  const toggle = (id) => setDb((d) => ({ ...d, forms: d.forms.map((f) => f.id === id ? { ...f, status: f.status === "new" ? "replied" : "new" } : f) }));
  return (
    <Section title="ওয়েবসাইট ফর্ম সাবমিশন" sub="tarbiyatulquran.org-এর যোগাযোগ ও ফ্রি ট্রায়াল ফর্ম থেকে আসা তথ্য">
      <div style={{ display: "grid", gap: 10 }}>
        {db.forms.map((f) => (
          <div key={f.id} style={{ ...S.card, padding: 16, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-start", borderLeft: `4px solid ${f.status === "new" ? C.gold : C.line}` }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <div style={{ fontWeight: 800 }}>{f.name} <Tag color={C.blue} bg={C.blueBg}>{f.type}</Tag> {f.status === "new" && <Tag color={C.gold} bg={C.amberBg}>নতুন</Tag>}</div>
              <div style={{ fontSize: 12.5, color: C.muted, margin: "3px 0" }}>📞 {f.contact} · {fmtDate(f.date)}</div>
              <div style={{ fontSize: 13.5 }}>{f.msg}</div>
            </div>
            <Btn sm kind={f.status === "new" ? "primary" : "soft"} onClick={() => toggle(f.id)}>{f.status === "new" ? "রিপ্লাই করা হয়েছে চিহ্নিত করুন" : "✔ রিপ্লাই হয়েছে"}</Btn>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ═══════════════ বই লাইব্রেরি (ফিচার ১০) ═══════════════ */
function BooksView({ db, setDb, user }) {
  const [show, setShow] = useState(false);
  const [f, setF] = useState({ cls: "", title: "", author: "", link: "#", type: "PDF" });
  const groups = [...new Set(db.books.map((b) => b.cls))];
  return (
    <Section title="বই লাইব্রেরি" sub="সকল শ্রেণির পাঠ্যবই ও সহায়ক বই — ডাউনলোডযোগ্য"
      action={isAdm(user) && <Btn onClick={() => setShow(true)}>+ বই যোগ করুন</Btn>}>
      {groups.map((g) => (
        <div key={g} style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 800, fontSize: 14.5, marginBottom: 8, color: C.emerald }}>📗 {g}</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))", gap: 10 }}>
            {db.books.filter((b) => b.cls === g).map((b) => (
              <div key={b.id} style={{ ...S.card, padding: 14 }}>
                <div style={{ fontWeight: 700, fontSize: 13.5 }}>{b.title}</div>
                <div style={{ fontSize: 12, color: C.muted, margin: "3px 0 8px" }}>{b.author}</div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Tag color={C.blue} bg={C.blueBg}>{b.type}</Tag>
                  <span style={{ display: "flex", gap: 8, alignItems: "center" }}><a href={b.link} style={{ fontSize: 12.5, fontWeight: 700, color: C.emerald, textDecoration: "none" }}>⬇ ডাউনলোড</a>{isDir(user) && <Btn sm kind="danger" onClick={() => setDb((d) => ({ ...d, books: d.books.filter((x) => x.id !== b.id) }))}>✕</Btn>}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      {show && (
        <Modal title="নতুন বই যোগ করুন" onClose={() => setShow(false)}>
          <label style={S.label}>শ্রেণি / কোর্স</label><input style={S.input} value={f.cls} onChange={(e) => setF({ ...f, cls: e.target.value })} placeholder="যেমন: তাজবীদ" />
          <div style={{ marginTop: 10 }}><label style={S.label}>বইয়ের নাম</label><input style={S.input} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>লেখক</label><input style={S.input} value={f.author} onChange={(e) => setF({ ...f, author: e.target.value })} /></div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={() => { setDb((d) => ({ ...d, books: [...d.books, { id: uid(), ...f }] })); setShow(false); }}>যোগ করুন</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ নোটিশ বোর্ড (অতিরিক্ত প্রফেশনাল ফিচার) ═══════════════ */
function NoticesView({ db, setDb, user }) {
  const [show, setShow] = useState(false);
  const [f, setF] = useState({ title: "", body: "" });
  return (
    <Section title="নোটিশ বোর্ড" action={isAdm(user) && <Btn onClick={() => setShow(true)}>+ নোটিশ দিন</Btn>}>
      <div style={{ display: "grid", gap: 10 }}>
        {db.notices.map((n) => (
          <div key={n.id} style={{ ...S.card, padding: 16, borderLeft: `4px solid ${C.gold}` }}>
            <div style={{ fontWeight: 800, display: "flex", justifyContent: "space-between", gap: 8 }}><span>📌 {n.title}</span>{isDir(user) && <Btn sm kind="danger" onClick={() => setDb((d) => ({ ...d, notices: d.notices.filter((x) => x.id !== n.id) }))}>মুছুন</Btn>}</div>
            <div style={{ fontSize: 12, color: C.muted, margin: "2px 0 6px" }}>{fmtDate(n.date)}</div>
            <div style={{ fontSize: 13.5 }}>{n.body}</div>
          </div>
        ))}
      </div>
      {show && (
        <Modal title="নতুন নোটিশ" onClose={() => setShow(false)}>
          <label style={S.label}>শিরোনাম</label><input style={S.input} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} />
          <div style={{ marginTop: 10 }}><label style={S.label}>বিস্তারিত</label><textarea rows={4} style={{ ...S.input, resize: "vertical" }} value={f.body} onChange={(e) => setF({ ...f, body: e.target.value })} /></div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={() => { setDb((d) => ({ ...d, notices: [{ id: uid(), ...f, date: todayISO() }, ...d.notices] })); setShow(false); }}>প্রকাশ করুন</Btn>
        </Modal>
      )}
    </Section>
  );
}


/* ═══════════════ ক্লাস শেষে মূল্যায়ন পপআপ (জুমের মতো, অপশনাল) ═══════════════ */
function RatingPopup({ courseName, onSubmit, onSkip }) {
  const [stars, setStars] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState("");
  const labels = ["", "উন্নতি দরকার", "মোটামুটি", "ভালো", "খুব ভালো", "অসাধারণ"];
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(18,63,40,.5)", zIndex: 95, display: "grid", placeItems: "center", padding: 16 }}>
      <div style={{ background: "#fff", borderRadius: 20, width: "100%", maxWidth: 400, padding: 26, textAlign: "center" }}>
        <div style={{ fontSize: 38 }}>🌟</div>
        <h3 style={{ margin: "6px 0 2px", fontSize: 17, fontWeight: 800, color: C.text }}>আজকের ক্লাসটি কেমন লাগলো?</h3>
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 14 }}>{courseName} — আপনার মূল্যায়ন একাডেমির মান উন্নয়নে সাহায্য করবে (ঐচ্ছিক)</div>
        <div style={{ display: "flex", justifyContent: "center", gap: 6, marginBottom: 4 }}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} onClick={() => setStars(n)} onMouseEnter={() => setHover(n)} onMouseLeave={() => setHover(0)}
              style={{ border: "none", background: "transparent", cursor: "pointer", fontSize: 32, lineHeight: 1, filter: (hover || stars) >= n ? "none" : "grayscale(1) opacity(.35)", transform: (hover || stars) >= n ? "scale(1.08)" : "none", transition: "all .12s" }}>⭐</button>
          ))}
        </div>
        <div style={{ height: 18, fontSize: 12.5, fontWeight: 700, color: C.gold }}>{labels[hover || stars]}</div>
        <textarea rows={2} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="কোনো মন্তব্য থাকলে লিখুন (ঐচ্ছিক)..."
          style={{ ...S.input, resize: "vertical", marginTop: 8, fontSize: 13 }} />
        <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
          <Btn kind="soft" style={{ flex: 1, justifyContent: "center" }} onClick={onSkip}>এড়িয়ে যান</Btn>
          <Btn kind="gold" style={{ flex: 1.4, justifyContent: "center", opacity: stars ? 1 : 0.5 }} onClick={() => stars && onSubmit(stars, comment.trim())}>মূল্যায়ন জমা দিন</Btn>
        </div>
        <div style={{ fontSize: 11, color: C.muted, marginTop: 10 }}>আপনার নাম ও মন্তব্য কেবল এডমিন দেখতে পাবেন — উস্তাদ শুধু গড় রেটিং দেখবেন।</div>
      </div>
    </div>
  );
}

/* ═══════════════ টিচার রিপোর্ট — উপস্থিতি · ক্লাসের মান · পেমেন্ট ═══════════════ */
function TeacherReportView({ db, setDb, courses, user }) {
  const teachers = USERS.filter((u) => u.role === "teacher");
  const [sel, setSel] = useState(user.role === "teacher" ? user.id : teachers[0]?.id);
  const tid = user.role === "teacher" ? user.id : sel;
  const t = userById(tid);
  const tCourses = COURSES.filter((c) => c.teacherId === tid);
  const att = db.attendance.filter((a) => a.userId === tid);
  const present = att.filter((a) => a.minutes >= 40).length;
  const short = att.filter((a) => a.minutes < 40).length;
  const taken = db.classes.filter((k) => tCourses.some((c) => c.id === k.courseId) && (k.status === "done" || k.date < todayISO())).length;
  const ratings = db.ratings.filter((r) => r.teacherId === tid);
  const avg = ratings.length ? ratings.reduce((s, r) => s + r.stars, 0) / ratings.length : 0;
  const quality = !ratings.length ? ["—", C.muted, C.cream] : avg >= 4.5 ? ["অসাধারণ", C.green, C.greenBg] : avg >= 4 ? ["খুব ভালো", C.emerald, C.greenBg] : avg >= 3 ? ["ভালো", C.gold, C.amberBg] : ["উন্নতি প্রয়োজন", C.red, C.redBg];
  const dist = [5, 4, 3, 2, 1].map((n) => ({ n, c: ratings.filter((r) => r.stars === n).length }));
  const pays = db.teacherPayments.filter((p) => p.teacherId === tid);
  const dues = db.dueMonths[tid] || [];
  return (
    <Section title="টিচার রিপোর্ট ও পেমেন্ট" sub="উপস্থিতি · ক্লাসের মান (স্টুডেন্ট মূল্যায়ন) · বেতন — চিহ্নিত করে দেখানো হয়েছে">
      {isAdm(user) && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
          {teachers.map((x) => <Btn key={x.id} sm kind={tid === x.id ? "primary" : "soft"} onClick={() => setSel(x.id)}>{x.name}</Btn>)}
        </div>
      )}
      <div style={{ ...S.card, display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap", marginBottom: 14, borderLeft: `4px solid ${quality[1]}` }}>
        <div style={{ width: 52, height: 52, borderRadius: 14, background: C.greenBg, display: "grid", placeItems: "center", fontSize: 26 }}>👳</div>
        <div style={{ flex: 1, minWidth: 180 }}>
          <div style={{ fontWeight: 800, fontSize: 16 }}>{t.name}</div>
          <div style={S.sub}>{t.sub} · কোর্স: {tCourses.map((c) => c.name).join(", ") || "—"}</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 24, fontWeight: 900, color: quality[1] }}>{ratings.length ? "★ " + bn(avg.toFixed(1)) : "★ —"}</div>
          <Tag color={quality[1]} bg={quality[2]}>ক্লাসের মান: {quality[0]}</Tag>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, marginBottom: 14 }}>
        <Stat icon="🎥" label="ক্লাস নিয়েছেন" value={bn(taken)} />
        <Stat icon="✅" label="পূর্ণ উপস্থিতি" value={bn(present)} note="৪০+ মিনিট" />
        <Stat icon="⚠️" label="অসম্পূর্ণ উপস্থিতি" value={bn(short)} accent={C.red} note="৪০ মিনিটের কম" />
        <Stat icon="🌟" label="মোট মূল্যায়ন" value={bn(ratings.length)} accent={C.gold} />
      </div>
      <div style={{ display: "grid", gap: 14 }}>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>🌟 ক্লাসের মান — স্টুডেন্ট মূল্যায়ন</div>
          {dist.map(({ n, c }) => (
            <div key={n} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, fontSize: 12.5 }}>
              <span style={{ width: 34, fontWeight: 700 }}>{bn(n)} ★</span>
              <div style={{ flex: 1, height: 9, background: C.cream, borderRadius: 99 }}>
                <div style={{ width: ratings.length ? (c / ratings.length) * 100 + "%" : 0, height: "100%", background: C.gold, borderRadius: 99 }} />
              </div>
              <span style={{ width: 26, textAlign: "right", color: C.muted }}>{bn(c)}</span>
            </div>
          ))}
          {isAdm(user) ? (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: C.muted, marginBottom: 6 }}>কে কী মূল্যায়ন করেছে (কেবল এডমিন/পরিচালক দেখছেন):</div>
              <Table head={["স্টুডেন্ট", "কোর্স", "রেটিং", "মন্তব্য", "তারিখ"]}
                rows={ratings.map((r) => [userById(r.studentId).name, courseById(COURSES, r.courseId).name, "★".repeat(r.stars), r.comment || "—", fmtDate(r.date)])}
                empty="এখনো কোনো মূল্যায়ন নেই" />
            </div>
          ) : (
            <div style={{ marginTop: 10, padding: "10px 12px", borderRadius: 10, background: C.cream, fontSize: 12, color: C.muted }}>
              🔒 কোন স্টুডেন্ট কী মূল্যায়ন বা মন্তব্য করেছে তা গোপন — কেবল এডমিন দেখতে পারেন। আপনি শুধু সামগ্রিক রিপোর্ট দেখছেন।
            </div>
          )}
        </div>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>🗓️ আমার উপস্থিতি রেকর্ড</div>
          <Table head={["কোর্স", "তারিখ", "উপস্থিতি", "অবস্থা"]}
            rows={att.map((a) => { const k = db.classes.find((x) => x.id === a.classId); const c = k ? courseById(COURSES, k.courseId) : {};
              return [c.name || "—", k ? fmtDate(k.date) : "—", `${bn(a.minutes)} মিনিট`, a.minutes >= 40 ? <Tag key="t">উপস্থিত ✔</Tag> : <Tag key="t" color={C.red} bg={C.redBg}>অসম্পূর্ণ ✘</Tag>]; })}
            empty="কোনো রেকর্ড নেই" />
        </div>
        <div style={{ ...S.card }}>
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
            <div style={{ fontWeight: 800 }}>💰 আমার বেতন ও পেমেন্ট</div>
            <div style={{ fontSize: 13 }}>মাসিক বেতন: <b>৳{bn((t.salary || 0).toLocaleString("en"))}</b> · বকেয়া: {dues.length ? <Tag color={C.red} bg={C.redBg}>{dues.join(", ")}</Tag> : <Tag>নেই ✔</Tag>}</div>
          </div>
          <Table head={["মাস", "পরিমাণ", "তারিখ", "মাধ্যম", "ভাউচার"]} rows={pays.map((p) => [p.month, `৳${bn(p.amount.toLocaleString("en"))}`, fmtDate(p.date), p.method, <Btn key="r" sm kind="soft" onClick={() => printReceipt({ ...p, date: fmtDate(p.date) }, t, "বেতন পরিশোধ ভাউচার")}>🧾 PDF</Btn>])} empty="এখনো কোনো পেমেন্ট হয়নি" />
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════ ভর্তি আবেদন — এপ্রুভ করলে তবেই স্টুডেন্ট তালিকায় ═══════════════ */
function AdmissionsView({ db, setDb, user, refresh }) {
  const accept = (a) => {
    const sNo = USERS.filter((u) => u.role === "student").length + 1;
    const id = "s" + uid();
    const newPass = genPass();
    USERS.push({ id, role: "student", name: `${a.name} (${a.country})`, sub: a.course, user: "student" + sNo, pass: newPass, fee: 4500, guardian: a.guardian, country: a.country });
    const c = COURSES.find((x) => x.name === a.course);
    if (c) c.studentIds.push(id);
    const m = ["জানুয়ারি","ফেব্রুয়ারি","মার্চ","এপ্রিল","মে","জুন","জুলাই","আগস্ট","সেপ্টেম্বর","অক্টোবর","নভেম্বর","ডিসেম্বর"][new Date().getMonth()];
    setDb((d) => ({ ...d,
      admissions: d.admissions.map((x) => x.id === a.id ? { ...x, status: "accepted", newLogin: "student" + sNo, newPass } : x),
      dueMonths: { ...d.dueMonths, [id]: [`${m} ${bn(new Date().getFullYear())}`] },
      notifications: [{ id: uid(), for: ["admin1", "dir1", c?.teacherId].filter(Boolean), text: `নতুন স্টুডেন্ট ভর্তি হয়েছে: ${a.name} — ${a.course} (লগইন: student${sNo})`, date: todayISO(), read: false }, ...d.notifications] }));
    refresh();
  };
  const reject = (a) => setDb((d) => ({ ...d, admissions: d.admissions.map((x) => x.id === a.id ? { ...x, status: "rejected" } : x) }));
  const forward = (a) => setDb((d) => ({ ...d,
    admissions: d.admissions.map((x) => x.id === a.id ? { ...x, forwarded: true } : x),
    notifications: [{ id: uid(), for: ["dir1"], text: `এডমিন একটি ভর্তি আবেদন পরিচালক বরাবর পাঠিয়েছেন: ${a.name} (${a.course})`, date: todayISO(), read: false }, ...d.notifications] }));
  const pending = db.admissions.filter((a) => a.status === "pending");
  const decided = db.admissions.filter((a) => a.status !== "pending");
  const Card = (a) => (
    <div key={a.id} style={{ ...S.card, padding: 16, borderLeft: `4px solid ${a.status === "pending" ? C.gold : a.status === "accepted" ? C.green : C.red}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ fontWeight: 800 }}>{a.name}, {bn(a.age)} বছর <Tag color={C.blue} bg={C.blueBg}>{a.course}</Tag></div>
          <div style={{ fontSize: 12.5, color: C.muted, margin: "3px 0" }}>অভিভাবক: {a.guardian} · {a.country} · 📞 {a.contact} · {fmtDate(a.date)}</div>
          <div style={{ fontSize: 13 }}>{a.msg}</div>
          {a.status === "accepted" && <div style={{ fontSize: 12, color: C.green, marginTop: 4 }}>✔ গৃহীত — লগইন আইডি: <b>{a.newLogin}</b> · পাসওয়ার্ড: <b>{a.newPass}</b> (পরিচালক/এডমিন অভিভাবককে জানিয়ে দেবেন)</div>}
        </div>
        {a.status === "pending" ? (
          isDir(user) ? (
            <div style={{ display: "flex", gap: 6, alignItems: "flex-end", flexDirection: "column" }}>
              {a.forwarded && <Tag color={C.blue} bg={C.blueBg}>📤 এডমিন পাঠিয়েছেন</Tag>}
              <div style={{ display: "flex", gap: 6 }}>
                <Btn sm onClick={() => accept(a)}>✔ গ্রহণ করুন</Btn>
                <Btn sm kind="danger" onClick={() => reject(a)}>✘ বাতিল</Btn>
              </div>
            </div>
          ) : (
            a.forwarded
              ? <Tag color={C.blue} bg={C.blueBg}>পরিচালকের কাছে পাঠানো হয়েছে ✔</Tag>
              : <Btn sm kind="gold" onClick={() => forward(a)}>📤 পরিচালক বরাবর পাঠান</Btn>
          )
        ) : a.status === "accepted" ? <Tag>গৃহীত ✔</Tag> : <Tag color={C.red} bg={C.redBg}>বাতিল ✘</Tag>}
      </div>
    </div>
  );
  return (
    <Section title="ভর্তি আবেদন" sub="গ্রহণ/বাতিলের ক্ষমতা কেবল পরিচালকের — এডমিন বিস্তারিত দেখে পরিচালক বরাবর পাঠাবেন">
      <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8, color: C.gold }}>⏳ অপেক্ষমাণ ({bn(pending.length)})</div>
      <div style={{ display: "grid", gap: 10, marginBottom: 18 }}>{pending.length === 0 ? <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>নতুন আবেদন নেই</div> : pending.map(Card)}</div>
      <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8, color: C.muted }}>সিদ্ধান্ত হয়েছে</div>
      <div style={{ display: "grid", gap: 10 }}>{decided.map(Card)}</div>
    </Section>
  );
}

/* ═══════════════ ম্যানেজ সেটিংস — কেবল পরিচালক (পূর্ণ নিয়ন্ত্রণ, কিছুই আড়াল নয়) ═══════════════ */
function ManageView({ db, setDb, refresh }) {
  const [show, setShow] = useState(false);
  const [report, setReport] = useState(null); // কার বিস্তারিত রিপোর্ট দেখা হচ্ছে
  const [f, setF] = useState({ role: "student", name: "", user: "", pass: genPass(), fee: 4500, salary: 10000, sub: "", courseId: COURSES[0].id });
  const addUser = async () => {
    if (!f.name || !f.user || !f.pass) return notice("নাম, লগইন আইডি (জিমেইল/নম্বর) ও পাসওয়ার্ড দিন।");
    if (USERS.some((x) => x.user === f.user)) return notice("এই লগইন আইডি আগে থেকেই আছে — অন্যটি দিন।");
    // ব্যাকএন্ডে সংরক্ষণ (পাসওয়ার্ডসহ)
    try {
      const { api } = await import("./api");
      const payload = {
        username: f.user,
        name_bn: f.name,
        sub_title: f.sub || (f.role === "student" ? "নতুন স্টুডেন্ট" : f.role === "teacher" ? "উস্তাদ/উস্তাদা" : "একাডেমিক এডমিন"),
        role: f.role,
        password: f.pass,
        ...(f.role === "student" ? { monthly_fee: +f.fee } : {}),
        ...(f.role === "teacher" ? { monthly_salary: +f.salary } : {}),
      };
      await api.saveUser(payload);
    } catch {
      // ব্যাকএন্ড না থাকলে local-এ যোগ করি (mock mode)
    }
    const id = f.role[0] + uid();
    USERS.push({ id, role: f.role, name: f.name, sub: f.sub || (f.role === "student" ? "নতুন স্টুডেন্ট" : f.role === "teacher" ? "উস্তাদ/উস্তাদা" : "একাডেমিক এডমিন"), user: f.user, pass: f.pass, ...(f.role === "student" ? { fee: +f.fee } : {}), ...(f.role === "teacher" ? { salary: +f.salary } : {}) });
    if (f.role === "student") COURSES.find((c) => c.id === f.courseId)?.studentIds.push(id);
    if (f.role === "teacher") setDb((d) => ({ ...d, permissions: { ...d.permissions, fixCross: { ...d.permissions.fixCross, [id]: false } } }));
    setShow(false); setF({ ...f, name: "", user: "", pass: genPass() }); refresh();
  };
  const delUser = (u) => askConfirm(`${u.name}-কে মুছে ফেলবেন? এটি ফিরিয়ে আনা যাবে না।`, () => {
    const i = USERS.findIndex((x) => x.id === u.id);
    if (i > -1) USERS.splice(i, 1);
    COURSES.forEach((c) => { c.studentIds = c.studentIds.filter((s) => s !== u.id); });
    refresh();
  });
  const togglePerm = (tid) => setDb((d) => ({ ...d, permissions: { ...d.permissions, fixCross: { ...d.permissions.fixCross, [tid]: !d.permissions.fixCross[tid] } } }));
  const roleBn = { director: "পরিচালক", admin: "এডমিন", teacher: "উস্তাদ/উস্তাদা", student: "স্টুডেন্ট" };

  /* এক ব্যবহারকারীর বিস্তারিত রিপোর্ট — পরিচালক সব দেখেন */
  const UserReport = ({ u }) => {
    const att = db.attendance.filter((a) => a.userId === u.id);
    const present = att.filter((a) => a.minutes >= 40).length, missed = att.length - present;
    const ratingsGiven = db.ratings.filter((r) => r.studentId === u.id);
    const ratingsGot = db.ratings.filter((r) => r.teacherId === u.id);
    const avg = ratingsGot.length ? (ratingsGot.reduce((s, r) => s + r.stars, 0) / ratingsGot.length).toFixed(1) : null;
    const paid = db.feePayments.filter((p) => p.studentId === u.id);
    const tPaid = db.teacherPayments.filter((p) => p.teacherId === u.id);
    const dues = db.dueMonths[u.id] || [];
    const exams = db.exams.filter((e) => e.marks[u.id] != null);
    const cs = u.role === "teacher" ? COURSES.filter((c) => c.teacherId === u.id) : COURSES.filter((c) => c.studentIds.includes(u.id));
    return (
      <Modal title={`বিস্তারিত রিপোর্ট — ${u.name}`} onClose={() => setReport(null)} wide>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12, fontSize: 13 }}>
          <div style={{ padding: "8px 10px", background: C.cream, borderRadius: 10 }}>ভূমিকা: <b>{roleBn[u.role]}</b></div>
          <div style={{ padding: "8px 10px", background: C.cream, borderRadius: 10 }}>লগইন: <b>{u.user}</b> · পাস: <b>{u.pass}</b></div>
          {u.role !== "admin" && u.role !== "director" && <div style={{ padding: "8px 10px", background: C.cream, borderRadius: 10 }}>কোর্স: <b>{cs.map((c) => c.name).join(", ") || "—"}</b></div>}
          {u.role === "student" && <div style={{ padding: "8px 10px", background: C.cream, borderRadius: 10 }}>অভিভাবক: <b>{u.guardian || "—"}</b> · {u.country || ""}</div>}
        </div>
        {(u.role === "student" || u.role === "teacher") && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 8, marginBottom: 12 }}>
            <Stat icon="✅" label="উপস্থিত" value={bn(present)} />
            <Stat icon="❌" label="অনুপস্থিত/অসম্পূর্ণ" value={bn(missed)} accent={C.red} />
            {u.role === "teacher" && <Stat icon="🌟" label="ক্লাসের মান" value={avg ? `★ ${bn(avg)}` : "—"} accent={C.gold} note={`${bn(ratingsGot.length)}টি মূল্যায়ন`} />}
            {u.role === "student" && <Stat icon="💰" label="ফি দিয়েছে" value={`৳${bn(paid.reduce((s, p) => s + p.amount, 0).toLocaleString("en"))}`} accent={C.gold} />}
            <Stat icon="⏳" label="বকেয়া মাস" value={bn(dues.length)} accent={dues.length ? C.red : C.emerald} note={dues.join(", ") || "নেই"} />
          </div>
        )}
        {u.role === "student" && exams.length > 0 && (
          <><div style={{ fontWeight: 800, fontSize: 13.5, margin: "6px 0" }}>📝 পরীক্ষার ফল</div>
          <Table head={["পরীক্ষা", "মার্ক"]} rows={exams.map((e) => [e.title, `${bn(e.marks[u.id])}/${bn(e.total)}`])} /></>
        )}
        {u.role === "student" && ratingsGiven.length > 0 && (
          <><div style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}>🌟 সে যেসব মূল্যায়ন করেছে (কেবল পরিচালক/এডমিন দেখেন)</div>
          <Table head={["উস্তাদ", "রেটিং", "মন্তব্য", "তারিখ"]} rows={ratingsGiven.map((r) => [userById(r.teacherId).name, "★".repeat(r.stars), r.comment || "—", fmtDate(r.date)])} /></>
        )}
        {u.role === "teacher" && ratingsGot.length > 0 && (
          <><div style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}>🌟 তার সম্পর্কে স্টুডেন্টদের মূল্যায়ন (নাম-মন্তব্যসহ)</div>
          <Table head={["স্টুডেন্ট", "রেটিং", "মন্তব্য", "তারিখ"]} rows={ratingsGot.map((r) => [userById(r.studentId).name, "★".repeat(r.stars), r.comment || "—", fmtDate(r.date)])} /></>
        )}
        {u.role === "teacher" && (
          <><div style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}>💰 বেতন পরিশোধ</div>
          <Table head={["মাস", "পরিমাণ", "তারিখ"]} rows={tPaid.map((p) => [p.month, `৳${bn(p.amount.toLocaleString("en"))}`, fmtDate(p.date)])} empty="এখনো পেমেন্ট হয়নি" /></>
        )}
        {u.role === "student" && (
          <><div style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}>💳 ফি পরিশোধ</div>
          <Table head={["মাস", "পরিমাণ", "মাধ্যম", "অবস্থা"]} rows={paid.map((p) => [p.month, `৳${bn(p.amount.toLocaleString("en"))}`, p.method, p.status === "pending" ? "যাচাই বাকি" : "যাচাইকৃত ✔"])} empty="এখনো পেমেন্ট নেই" /></>
        )}
        {(u.role === "admin" || u.role === "director") && <div style={{ padding: "10px 12px", background: C.cream, borderRadius: 10, fontSize: 12.5, color: C.muted }}>{u.role === "admin" ? "একাডেমিক এডমিন — ক্লাস, লেকচার, ভর্তি, পরীক্ষা, ফি যাচাই ও ফর্ম নিয়ন্ত্রণ করেন। হিসাব-নিকাশ ও ম্যানেজ সেটিংসে প্রবেশাধিকার নেই।" : "পরিচালক — সফটওয়্যারের পূর্ণ নিয়ন্ত্রণ।"}</div>}
      </Modal>
    );
  };

  return (
    <Section title="ম্যানেজ সেটিংস" sub="পরিচালকের পূর্ণ নিয়ন্ত্রণ — সবার আইডি-পাসওয়ার্ড, বিস্তারিত রিপোর্ট; কোনো কিছুই আড়াল নয়"
      action={<Btn onClick={() => setShow(true)}>+ নতুন ব্যবহারকারী</Btn>}>
      <div style={{ ...S.card, marginBottom: 14 }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>👥 সকল ব্যবহারকারী — আইডি, পাসওয়ার্ড ও রিপোর্টসহ</div>
        <Table head={["নাম", "ভূমিকা", "লগইন আইডি", "পাসওয়ার্ড", "রিপোর্ট", "অ্যাকশন"]}
          rows={USERS.map((u) => [u.name,
            <Tag key="r" color={u.role === "director" ? C.red : u.role === "admin" ? C.emerald : u.role === "teacher" ? C.gold : C.blue} bg={C.cream}>{roleBn[u.role]}</Tag>,
            u.user,
            <code key="p" style={{ background: C.cream, padding: "2px 8px", borderRadius: 6, fontSize: 12 }}>{u.pass}</code>,
            <Btn key="rep" sm kind="ghost" onClick={() => setReport(u)}>📊 বিস্তারিত</Btn>,
            u.role === "director" ? "—" : <Btn key="d" sm kind="danger" onClick={() => delUser(u)}>মুছুন</Btn>])} />
      </div>
      <div style={{ ...S.card, marginBottom: 14 }}>
        <div style={{ fontWeight: 800, marginBottom: 4 }}>🔑 বিশেষ অনুমতি — ভুল সংশোধন</div>
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>সাধারণত লাল ক্রস (✘) কেবল এডমিন/পরিচালক ঠিক করতে পারেন। কোনো উস্তাদের ভুল হলে তাকে সাময়িক এডিটের সুযোগ দিন:</div>
        {USERS.filter((u) => u.role === "teacher").map((t) => (
          <div key={t.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 10, background: C.cream, marginBottom: 6, flexWrap: "wrap" }}>
            <span style={{ flex: 1, fontSize: 13.5, fontWeight: 600, minWidth: 140 }}>{t.name}</span>
            {db.permissions.fixCross[t.id] ? <Tag>অনুমতি চালু ✔</Tag> : <Tag color={C.muted} bg={"#fff"}>বন্ধ</Tag>}
            <Btn sm kind={db.permissions.fixCross[t.id] ? "danger" : "ghost"} onClick={() => togglePerm(t.id)}>{db.permissions.fixCross[t.id] ? "বন্ধ করুন" : "অনুমতি দিন"}</Btn>
          </div>
        ))}
      </div>
      <div style={{ ...S.card, border: `1.5px solid #f3c9b8` }}>
        <div style={{ fontWeight: 800, marginBottom: 4, color: C.red }}>⚠️ ডেঞ্জার জোন</div>
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>ক্লাস, পরীক্ষা, নোটিশ, বই — প্রতিটি পেজে পরিচালকের জন্য আলাদা "মুছুন" বাটন চালু আছে। এছাড়া:</div>
        <Btn kind="danger" sm onClick={() => askConfirm("সব নোটিফিকেশন মুছে ফেলবেন?", () => setDb((d) => ({ ...d, notifications: [] })))}>সব নোটিফিকেশন মুছুন</Btn>
      </div>
      {report && <UserReport u={report} />}
      {show && (
        <Modal title="নতুন ব্যবহারকারী যোগ করুন" onClose={() => setShow(false)}>
          <label style={S.label}>ভূমিকা</label>
          <select style={S.input} value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>
            <option value="student">স্টুডেন্ট</option><option value="teacher">উস্তাদ/উস্তাদা</option><option value="admin">এডমিন</option>
          </select>
          <div style={{ marginTop: 10 }}><label style={S.label}>নাম</label><input style={S.input} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>লগইন আইডি — জিমেইল বা মোবাইল নম্বর</label>
            <input style={S.input} value={f.user} onChange={(e) => setF({ ...f, user: e.target.value })} placeholder="যেমন: name@gmail.com বা 01712345678" /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>পাসওয়ার্ড — অক্ষর ও সংখ্যা মিশ্রিত</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input style={{ ...S.input, flex: 1 }} value={f.pass} onChange={(e) => setF({ ...f, pass: e.target.value })} />
              <Btn kind="soft" onClick={() => setF({ ...f, pass: genPass() })}>🎲 বানিয়ে দিন</Btn>
            </div></div>
          {f.role === "student" && <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 10 }}>
            <div><label style={S.label}>মাসিক ফি (৳)</label><input type="number" style={S.input} value={f.fee} onChange={(e) => setF({ ...f, fee: e.target.value })} /></div>
            <div><label style={S.label}>কোর্স</label><select style={S.input} value={f.courseId} onChange={(e) => setF({ ...f, courseId: e.target.value })}>{COURSES.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
          </div>}
          {f.role === "teacher" && <div style={{ marginTop: 10 }}><label style={S.label}>মাসিক বেতন (৳)</label><input type="number" style={S.input} value={f.salary} onChange={(e) => setF({ ...f, salary: e.target.value })} /></div>}
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={addUser}>যোগ করুন — আইডি ও পাসওয়ার্ড তৈরি হবে</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ লাইভ ক্লাস ফুল-পেজ পপআপ (স্টুডেন্ট) — আয়াতসহ ═══════════════ */
function LiveClassPopup({ k, course, onJoin, onLater }) {
  const lec = course.lectures?.[k.lectureNo - 1];
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 200, background: `linear-gradient(160deg, ${C.emeraldD} 0%, ${C.emerald} 55%, ${C.emeraldL} 100%)`, display: "grid", placeItems: "center", padding: 18, overflowY: "auto" }}>
      <div style={{ maxWidth: 520, width: "100%", textAlign: "center", color: "#fff" }}>
        <div style={{ fontSize: 46, animation: "tqaPulse 1.6s infinite" }}>🕌</div>
        <div style={{ fontFamily: "'Amiri', 'Hind Siliguri', serif", fontSize: 30, color: C.goldL, margin: "10px 0 4px", lineHeight: 1.7 }}>﴿وَقُلْ رَبِّ زِدْنِي عِلْمًا﴾</div>
        <div style={{ fontSize: 14, color: "#d7e9de", marginBottom: 4 }}>"এবং বলো: হে আমার রব! আমার জ্ঞান বৃদ্ধি করে দিন।"</div>
        <div style={{ fontSize: 11.5, color: "#9fc4ae", marginBottom: 18 }}>— সূরা ত্বহা, আয়াত ১১৪</div>
        <div style={{ background: "rgba(255,255,255,.10)", border: `1px solid rgba(240,195,85,.4)`, borderRadius: 20, padding: "22px 20px", backdropFilter: "blur(4px)" }}>
          <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 6 }}>✨ এখনই দারস শুরু হবে — জয়েন করো!</div>
          <div style={{ fontSize: 14.5, fontWeight: 700, color: C.goldL }}>{course.name} · লেকচার {bn(k.lectureNo)}</div>
          {lec && <div style={{ fontSize: 13, color: "#d7e9de", margin: "4px 0" }}>{lec.title}</div>}
          <div style={{ fontSize: 12.5, color: "#cfe6d8", marginBottom: 16 }}>🕐 {k.time} · উস্তাদ: {userById(course.teacherId).name}</div>
          <a href={k.zoom} target="_blank" rel="noreferrer" onClick={() => onJoin(k)} style={{ display: "block", textDecoration: "none", width: "100%", background: "linear-gradient(135deg, #d92626, #b91c1c)", color: "#fff", fontSize: 17, fontWeight: 800, padding: "16px 20px", borderRadius: 14, boxShadow: "0 8px 24px rgba(217,38,38,.45)", animation: "tqaPulse 1.6s infinite", textAlign: "center", boxSizing: "border-box" }}>
            🎥 এখনই জয়েন করুন — জুম খুলে যাবে
          </a>
          <div style={{ fontSize: 13, color: "#d7e9de", marginTop: 14, fontStyle: "italic" }}>জাযাকাল্লাহু খাইরান ফীদ-দ্বারাইন 🤲</div>
        </div>
        <button onClick={onLater} style={{ marginTop: 16, border: "1px solid rgba(255,255,255,.35)", background: "transparent", color: "#cfe6d8", fontFamily: "inherit", fontSize: 12.5, padding: "8px 18px", borderRadius: 99, cursor: "pointer" }}>পরে জয়েন করব</button>
      </div>
      <style>{`@keyframes tqaPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.035)}}`}</style>
    </div>
  );
}

/* ═══════════════ স্টুডেন্ট পেমেন্ট পেজ — হিস্টরি, রিসিট (চোখ), এখনই পেমেন্ট ═══════════════ */
function StudentPaymentsView({ db, setDb, user }) {
  const [payMonth, setPayMonth] = useState(null);
  const [pf, setPf] = useState({ method: "বিকাশ", trx: "", shot: null });
  const [duaMsg, setDuaMsg] = useState(false);
  const paid = db.feePayments.filter((p) => p.studentId === user.id);
  const totalPaid = paid.filter((p) => p.status !== "pending").reduce((s, p) => s + p.amount, 0);
  const dues = db.dueMonths[user.id] || [];
  const pickShot = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => setPf((x) => ({ ...x, shot: { data: r.result, name: f.name } }));
    r.readAsDataURL(f);
  };
  const submitPay = () => {
    if (!pf.trx.trim() && !pf.shot) return notice("দয়া করে স্ক্রিনশট বা ট্রানজেকশন আইডি যুক্ত করুন।");
    setDb((d) => ({ ...d,
      feePayments: [...d.feePayments, { id: uid(), studentId: user.id, amount: user.fee, month: payMonth, date: todayISO(), method: pf.method + (pf.trx ? ` (Trx: ${pf.trx})` : ""), shot: pf.shot, status: "pending" }],
      dueMonths: { ...d.dueMonths, [user.id]: (d.dueMonths[user.id] || []).filter((m) => m !== payMonth) },
      notifications: [{ id: uid(), for: ["dir1", "admin1"], text: `${user.name} — ${payMonth} মাসের ফি ${pf.method}-এ পরিশোধ করেছে, পরিচালকের ভেরিফাই বাকি।`, date: todayISO(), read: false }, ...d.notifications] }));
    setPayMonth(null); setPf({ method: "বিকাশ", trx: "", shot: null }); setDuaMsg(true);
  };
  const acct = {
    "বিকাশ": { icon: "📱", line1: "বিকাশ পার্সোনাল (Send Money)", line2: "নম্বর: 01402-499027" },
    "নগদ": { icon: "🟠", line1: "নগদ পার্সোনাল (Send Money)", line2: "নম্বর: 01402-499027" },
    "ব্যাংক ট্রান্সফার": { icon: "🏦", line1: "ইসলামী ব্যাংক বাংলাদেশ — তারবিয়াতুল কুরআন একাডেমি", line2: "হিসাব নং: 2050-1234-5678-901 (ঢাকা শাখা)" },
  };
  return (
    <Section title="পেমেন্ট" sub="শুরু থেকে সকল পেমেন্ট হিস্টরি, বকেয়া ফি ও রিসিট">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, marginBottom: 16 }}>
        <Stat icon="✅" label="মোট পরিশোধিত (ভেরিফাইড)" value={`৳${bn(totalPaid.toLocaleString("en"))}`} />
        <Stat icon="⏳" label="বকেয়া" value={`৳${bn((dues.length * (user.fee || 0)).toLocaleString("en"))}`} accent={dues.length ? C.red : C.emerald} note={dues.join(", ") || "আলহামদুলিল্লাহ, বকেয়া নেই"} />
      </div>
      {dues.length > 0 && (
        <div style={{ ...S.card, marginBottom: 14, borderLeft: `4px solid ${C.red}` }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>⏳ বকেয়া ফি</div>
          {dues.map((m) => (
            <div key={m} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 10, background: C.redBg, marginBottom: 8, flexWrap: "wrap" }}>
              <span style={{ flex: 1, fontWeight: 700, fontSize: 14, minWidth: 140 }}>{m} — ৳{bn((user.fee || 0).toLocaleString("en"))}</span>
              <Btn sm kind="gold" onClick={() => setPayMonth(m)}>⚡ এখনই পেমেন্ট করুন</Btn>
            </div>
          ))}
        </div>
      )}
      <div style={{ ...S.card }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>📜 পেমেন্ট হিস্টরি</div>
        <Table head={["মাস", "পরিমাণ", "তারিখ", "মাধ্যম", "অবস্থা", "রিসিট"]}
          rows={paid.map((p) => [p.month, `৳${bn(p.amount.toLocaleString("en"))}`, fmtDate(p.date), p.method,
            p.status === "pending"
              ? <span key="s" style={{ background: C.amberBg, color: "#a16207", border: "1.5px solid #f0c355", fontSize: 11.5, fontWeight: 800, padding: "4px 12px", borderRadius: 99, whiteSpace: "nowrap" }}>⏳ পেন্ডিং</span>
              : <span key="s" style={{ background: C.greenBg, color: C.green, border: `1.5px solid ${C.green}`, fontSize: 11.5, fontWeight: 800, padding: "4px 12px", borderRadius: 99, whiteSpace: "nowrap" }}>✔ ভেরিফাইড</span>,
            <Btn key="eye" sm kind="soft" title="রিসিট দেখুন / ডাউনলোড করুন" onClick={() => printReceipt({ ...p, date: fmtDate(p.date) }, user, "ফি পরিশোধ রিসিট")}>👁 দেখুন</Btn>])}
          empty="এখনো কোনো পেমেন্ট নেই" />
      </div>
      {payMonth && (
        <Modal title={`এখনই পেমেন্ট করুন — ${payMonth}`} onClose={() => setPayMonth(null)}>
          <div style={{ padding: "10px 12px", borderRadius: 10, background: C.greenBg, fontSize: 13.5, fontWeight: 700, marginBottom: 12 }}>পরিমাণ: ৳{bn((user.fee || 0).toLocaleString("en"))}</div>
          <label style={S.label}>পেমেন্ট মাধ্যম</label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 10 }}>
            {Object.keys(acct).map((m) => (
              <button key={m} onClick={() => setPf({ ...pf, method: m })} style={{ padding: "11px 6px", borderRadius: 10, cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 12.5, border: `2px solid ${pf.method === m ? C.emerald : C.line}`, background: pf.method === m ? C.greenBg : "#fff", color: pf.method === m ? C.emerald : C.text }}>
                {acct[m].icon}<br />{m}
              </button>
            ))}
          </div>
          <div style={{ padding: "10px 12px", borderRadius: 10, background: C.cream, fontSize: 13, marginBottom: 12 }}>
            <b>{acct[pf.method].line1}</b><br />{acct[pf.method].line2}
          </div>
          <label style={S.label}>ট্রানজেকশন আইডি</label>
          <input style={S.input} value={pf.trx} onChange={(e) => setPf({ ...pf, trx: e.target.value })} placeholder="যেমন: 9HX2K7QM" />
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>পেমেন্টের স্ক্রিনশট</label>
            <label style={{ display: "grid", placeItems: "center", gap: 4, padding: "18px 12px", border: `2px dashed ${pf.shot ? C.emerald : C.line}`, borderRadius: 12, cursor: "pointer", background: pf.shot ? C.greenBg : C.cream, textAlign: "center" }}>
              <span style={{ fontSize: 24 }}>{pf.shot ? "✅" : "🖼️"}</span>
              <span style={{ fontSize: 12.5, fontWeight: 700 }}>{pf.shot ? pf.shot.name : "স্ক্রিনশট / ছবি যোগ করুন"}</span>
              <input type="file" accept="image/*" style={{ display: "none" }} onChange={pickShot} />
            </label>
            {pf.shot && <img src={pf.shot.data} alt="স্ক্রিনশট" style={{ width: "100%", borderRadius: 10, marginTop: 8, border: `1px solid ${C.line}` }} />}
          </div>
          <div style={{ fontSize: 12.5, color: C.muted, marginTop: 10, textAlign: "center" }}>দয়া করে পেমেন্ট সম্পন্ন করে স্ক্রিনশট বা ট্রানজেকশন আইডি যুক্ত করে ভেরিফাই করুন।</div>
          <Btn style={{ marginTop: 12, width: "100%", justifyContent: "center" }} onClick={submitPay}>✔ ভেরিফাই করুন</Btn>
        </Modal>
      )}
      {duaMsg && (
        <div style={{ position: "fixed", inset: 0, zIndex: 120, background: "rgba(18,63,40,.55)", display: "grid", placeItems: "center", padding: 16 }}>
          <div style={{ background: "#fff", borderRadius: 20, maxWidth: 430, width: "100%", padding: 28, textAlign: "center" }}>
            <div style={{ fontSize: 40 }}>🤲</div>
            <div style={{ fontFamily: "'Amiri', serif", fontSize: 21, color: C.emerald, lineHeight: 2, margin: "10px 0 6px" }}>باركَ الله لك في أهلِكَ ومالِكَ، إنَّما جزاءُ السَّلفِ الوفاءُ والحمدُ</div>
            <div style={{ fontSize: 13.5, color: C.text, marginBottom: 6 }}>"আল্লাহ আপনার পরিবার ও সম্পদে বরকত দান করুন। ঋণ (প্রাপ্য) পরিশোধের প্রতিদান তো পূর্ণ আদায় ও কৃতজ্ঞতা প্রকাশই।"</div>
            <div style={{ fontSize: 11.5, color: C.muted, marginBottom: 14 }}>— সুনানে নাসাঈ ও ইবনে মাজাহ</div>
            <div style={{ padding: "10px 12px", borderRadius: 10, background: C.greenBg, color: C.green, fontWeight: 700, fontSize: 13.5 }}>✔ আপনার পেমেন্ট জমা হয়েছে! পরিচালক যাচাই করলে "ভেরিফাইড" দেখাবে ইনশাআল্লাহ।</div>
            <Btn style={{ marginTop: 14, width: "100%", justifyContent: "center" }} onClick={() => setDuaMsg(false)}>আলহামদুলিল্লাহ</Btn>
          </div>
        </div>
      )}
    </Section>
  );
}

/* ═══════════════ রিসিট বানানোর টুল — যে কারো জন্য PDF রিসিট/ভাউচার ═══════════════ */
function ReceiptMaker({ onClose, user }) {
  const people = isDir(user) ? USERS.filter((u) => u.role !== "director") : USERS.filter((u) => u.role === "student"); // এডমিন কেবল স্টুডেন্ট দেখবেন
  const [f, setF] = useState({ who: USERS.find((u) => u.role === "student")?.id || "custom", custom: "", kind: "ফি পরিশোধ রিসিট", month: "", amount: "", method: "বিকাশ", date: todayISO() });
  const make = () => {
    const person = f.who === "custom" ? { name: f.custom.trim() } : userById(f.who);
    if (!person.name) return notice("নাম দিন।");
    if (!f.amount || +f.amount <= 0) return notice("সঠিক পরিমাণ দিন।");
    printReceipt({ id: uid(), month: f.month || "—", amount: +f.amount, method: f.method, date: fmtDate(f.date), status: "verified" }, person, f.kind);
  };
  return (
    <Modal title="🧾 রিসিট বানান" onClose={onClose}>
      <label style={S.label}>রিসিটের ধরন</label>
      <select style={S.input} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>
        <option>ফি পরিশোধ রিসিট</option>{isDir(user) && <option>বেতন পরিশোধ ভাউচার</option>}<option>ভর্তি ফি রিসিট</option><option>অনুদান রিসিট</option><option>অন্যান্য পরিশোধ রিসিট</option>
      </select>
      <div style={{ marginTop: 10 }}><label style={S.label}>কার জন্য</label>
        <select style={S.input} value={f.who} onChange={(e) => setF({ ...f, who: e.target.value })}>
          {people.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.role === "student" ? "স্টুডেন্ট" : u.role === "teacher" ? "উস্তাদ" : "এডমিন"})</option>)}
          <option value="custom">✏️ অন্য কেউ — নিজে লিখুন</option>
        </select></div>
      {f.who === "custom" && <div style={{ marginTop: 10 }}><label style={S.label}>নাম</label><input style={S.input} value={f.custom} onChange={(e) => setF({ ...f, custom: e.target.value })} /></div>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 10 }}>
        <div><label style={S.label}>মাস / বিবরণ</label><input style={S.input} value={f.month} onChange={(e) => setF({ ...f, month: e.target.value })} placeholder="যেমন: জুন ২০২৬" /></div>
        <div><label style={S.label}>পরিমাণ (৳)</label><input type="number" style={S.input} value={f.amount} onChange={(e) => setF({ ...f, amount: e.target.value })} /></div>
        <div><label style={S.label}>মাধ্যম</label><select style={S.input} value={f.method} onChange={(e) => setF({ ...f, method: e.target.value })}><option>বিকাশ</option><option>নগদ</option><option>ব্যাংক ট্রান্সফার</option><option>নগদ গ্রহণ (অফিস)</option></select></div>
        <div><label style={S.label}>তারিখ</label><input type="date" style={S.input} value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} /></div>
      </div>
      <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={make}>🧾 PDF রিসিট তৈরি করুন</Btn>
      <div style={{ fontSize: 11.5, color: C.muted, textAlign: "center", marginTop: 8 }}>রিসিট প্রিভিউ খুলবে — সেখান থেকে ⬇️ ডাউনলোড বা 📨 সেন্ড করা যাবে</div>
    </Modal>
  );
}

/* ═══════════════ পরিচালকের স্টুডেন্ট পেমেন্ট — ভেরিফাই (কেবল পরিচালক) + WhatsApp রিমাইন্ডার ═══════════════ */
function DirectorPaymentsView({ db, setDb, user }) {
  const [viewShot, setViewShot] = useState(null);
  const [maker, setMaker] = useState(false);
  const pending = db.feePayments.filter((p) => p.status === "pending");
  const verified = db.feePayments.filter((p) => p.status !== "pending");
  const verify = (pid) => setDb((d) => ({ ...d,
    feePayments: d.feePayments.map((p) => p.id === pid ? { ...p, status: "verified" } : p),
    notifications: [{ id: uid(), for: [d.feePayments.find((p) => p.id === pid)?.studentId], text: `আপনার ${d.feePayments.find((p) => p.id === pid)?.month} মাসের ফি ভেরিফাই হয়েছে, জাযাকুমুল্লাহু খাইরান।`, date: todayISO(), read: false }, ...d.notifications] }));
  const dueStudents = USERS.filter((u) => u.role === "student" && (db.dueMonths[u.id] || []).length > 0);
  const waMsg = (s) => {
    const dues = db.dueMonths[s.id] || [];
    return `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহি ওয়া বারাকাতুহ।\n\nমুহতারাম ${s.guardian || "অভিভাবক"},\nতারবিয়াতুল কুরআন একাডেমির পক্ষ থেকে আন্তরিক দুআ ও সালাম। আল্লাহ তাআলা আপনার সন্তানের ইলম ও আমলে বরকত দান করুন।\n\nবিনয়ের সাথে স্মরণ করিয়ে দিচ্ছি — ${s.name}-এর ${dues.join(", ")} মাসের ফি (মোট ৳${(dues.length * (s.fee || 0)).toLocaleString("en")}) এখনো অপরিশোধিত রয়েছে। আপনার সুবিধাজনক সময়ে পরিশোধ করে দিলে কৃতজ্ঞ থাকব ইনশাআল্লাহ।\n\nজাযাকুমুল্লাহু খাইরান।\n— তারবিয়াতুল কুরআন একাডেমি`;
  };
  const sendAll = () => {
    const full = dueStudents.map((s) => `• ${s.name} (${s.guardian || ""}): ${(db.dueMonths[s.id] || []).join(", ")} — ৳${((db.dueMonths[s.id] || []).length * (s.fee || 0)).toLocaleString("en")}`).join("\n");
    const msg = `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ।\nমুহতারাম অভিভাবকবৃন্দ, বিনয়ের সাথে ফি পরিশোধের কথা স্মরণ করিয়ে দিচ্ছি ইনশাআল্লাহ:\n${full}\nজাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি`;
    navigator.clipboard?.writeText(msg.replace(/\\n/g, "\n"));
    notice("সবার রিমাইন্ডার মেসেজ কপি হয়েছে ✔ — WhatsApp গ্রুপ বা ব্রডকাস্ট লিস্টে পেস্ট করে পাঠিয়ে দিন।");
  };
  return (
    <Section title="স্টুডেন্ট পেমেন্ট" sub="কে পেমেন্ট করেছে, কার বাকি — মিলিয়ে ভেরিফাই করুন (ভেরিফাই কেবল পরিচালকই করতে পারেন)" action={<Btn kind="gold" onClick={() => setMaker(true)}>🧾 রিসিট বানান</Btn>}>
      {maker && <ReceiptMaker user={user} onClose={() => setMaker(false)} />}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, marginBottom: 16 }}>
        <Stat icon="⏳" label="ভেরিফাই বাকি" value={bn(pending.length)} accent={C.gold} />
        <Stat icon="✅" label="ভেরিফাইড পেমেন্ট" value={bn(verified.length)} />
        <Stat icon="📵" label="বকেয়া আছে" value={`${bn(dueStudents.length)} জন`} accent={C.red} />
      </div>
      <div style={{ ...S.card, marginBottom: 14, borderLeft: `4px solid ${C.gold}` }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>⏳ ভেরিফাইয়ের অপেক্ষায় — মিলিয়ে দেখে ক্লিক করুন</div>
        {pending.length === 0 && <div style={{ color: C.muted, fontSize: 13, textAlign: "center", padding: 8 }}>কোনো পেন্ডিং পেমেন্ট নেই, আলহামদুলিল্লাহ।</div>}
        {pending.map((p) => {
          const s = userById(p.studentId);
          return (
            <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 12, background: C.amberBg, marginBottom: 8, flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <b style={{ fontSize: 14 }}>{s.name}</b> — {p.month} · ৳{bn(p.amount.toLocaleString("en"))}
                <div style={{ fontSize: 12, color: C.muted }}>{p.method} · {fmtDate(p.date)}</div>
              </div>
              {p.shot && <Btn sm kind="soft" onClick={() => setViewShot(p.shot)}>🖼️ স্ক্রিনশট</Btn>}
              <span style={{ background: "#fff", color: "#a16207", border: "1.5px solid #f0c355", fontSize: 11.5, fontWeight: 800, padding: "4px 12px", borderRadius: 99 }}>⏳ পেন্ডিং</span>
              <Btn sm onClick={() => verify(p.id)}>✔ ভেরিফাই করুন</Btn>
            </div>
          );
        })}
      </div>
      <div style={{ ...S.card, marginBottom: 14, borderLeft: `4px solid ${C.red}` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
          <div style={{ fontWeight: 800 }}>📵 যাদের ফি বাকি — WhatsApp রিমাইন্ডার</div>
          {dueStudents.length > 0 && <Btn sm kind="gold" onClick={sendAll}>📋 সবাইকে একসাথে (মেসেজ কপি)</Btn>}
        </div>
        {dueStudents.length === 0 && <div style={{ color: C.muted, fontSize: 13, textAlign: "center", padding: 8 }}>কারো বকেয়া নেই, আলহামদুলিল্লাহ।</div>}
        {dueStudents.map((s) => (
          <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 12, background: C.redBg, marginBottom: 8, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <b style={{ fontSize: 14 }}>{s.name}</b>
              <div style={{ fontSize: 12, color: C.muted }}>বকেয়া: {(db.dueMonths[s.id] || []).join(", ")} — ৳{bn(((db.dueMonths[s.id] || []).length * (s.fee || 0)).toLocaleString("en"))} · অভিভাবক: {s.guardian || "—"}</div>
            </div>
            {s.phone
              ? <a href={`https://wa.me/${s.phone}?text=${encodeURIComponent(waMsg(s).replace(/\\n/g, "\n"))}`} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}><Btn sm style={{ background: "#25D366", color: "#fff" }}>📱 WhatsApp রিমাইন্ডার</Btn></a>
              : <Tag color={C.muted} bg={C.cream}>নম্বর নেই</Tag>}
          </div>
        ))}
      </div>
      <div style={{ ...S.card }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>✅ ভেরিফাইড পেমেন্টসমূহ</div>
        <Table head={["স্টুডেন্ট", "মাস", "পরিমাণ", "মাধ্যম", "তারিখ", "রিসিট"]}
          rows={verified.map((p) => [userById(p.studentId).name, p.month, `৳${bn(p.amount.toLocaleString("en"))}`, p.method, fmtDate(p.date),
            <Btn key="r" sm kind="soft" onClick={() => printReceipt({ ...p, date: fmtDate(p.date) }, userById(p.studentId), "ফি পরিশোধ রিসিট")}>🧾 PDF</Btn>])} />
      </div>
      {viewShot && (
        <Modal title="পেমেন্টের স্ক্রিনশট" onClose={() => setViewShot(null)}>
          <img src={viewShot.data} alt="স্ক্রিনশট" style={{ width: "100%", borderRadius: 12, border: `1px solid #e5e9e5` }} />
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ক্লাস রুটিন (সাপ্তাহিক) — পরিচালক/এডমিন বানাবেন, অটো সবার পোর্টালে ═══════════════ */
const DAY_BN = ["রবিবার", "সোমবার", "মঙ্গলবার", "বুধবার", "বৃহস্পতিবার", "শুক্রবার", "শনিবার"]; // JS getDay() ক্রম
const WEEK_ORDER = [6, 0, 1, 2, 3, 4, 5]; // শনি → শুক্র

function RoutineView({ db, setDb, courses, user }) {
  const canEdit = isAdm(user);
  const [show, setShow] = useState(false);
  const blankR = () => ({ courseId: courses[0]?.id, days: [], time: "17:00", dur: 60, zoom: "https://zoom.us/j/8801402499027", kind: "নিয়মিত ক্লাস", teacherId: USERS.find((u) => u.role === "teacher")?.id, studentIds: [] });
  const [f, setF] = useState(blankR);
  const [editId, setEditId] = useState(null);
  const plusDays = (iso, n) => { const d = new Date(iso + "T00:00:00"); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
  const toggleDay = (i) => setF({ ...f, days: f.days.includes(i) ? f.days.filter((d) => d !== i) : [...f.days, i] });
  const nextDate = (wd) => { const d = new Date(); const diff = (wd - d.getDay() + 7) % 7; d.setDate(d.getDate() + diff); return d.toISOString().slice(0, 10); };
  const genClasses = (rid, ff, students) => ff.days.flatMap((wd) => [0, 7].map((off) => ({ // এ সপ্তাহ + পরের সপ্তাহ — স্থায়ী রুটিনের ক্লাস
    id: uid(), routineId: rid, courseId: ff.courseId, date: plusDays(nextDate(wd), off), time: ff.time, dur: +ff.dur, zoom: ff.zoom, status: "upcoming", lectureNo: 1, fromRoutine: true, kind: "নিয়মিত ক্লাস", teacherId: ff.teacherId, studentIds: students })));
  const add = () => {
    if (!f.days.length) return notice("সপ্তাহের অন্তত একটি দিন বাছাই করুন।");
    const c = courseById(courses, f.courseId);
    const students = f.studentIds.length ? f.studentIds : (c.studentIds || []); // কাউকে না বাছলে কোর্সের সবাই
    if (editId) { // ✏️ এডিট — আসন্ন ক্লাস নতুন বার-সময়ে আবার তৈরি, পোর্টাল অটো আপডেট
      const newClasses = genClasses(editId, f, students);
      setDb((d) => ({ ...d,
        routine: d.routine.map((r) => r.id === editId ? { ...r, ...f, dur: +f.dur, studentIds: students } : r),
        classes: [...d.classes.filter((k) => !(k.routineId === editId && k.date >= todayISO())), ...newClasses],
        notifications: [{ id: uid(), for: [f.teacherId, ...students, "admin1", "dir1"], text: `✏️ রুটিন আপডেট হয়েছে: ${c.name} — ${f.days.map((i) => DAY_BN[i]).join(", ")} ${f.time}। আপনার পোর্টালের ক্লাসগুলোও আপডেট হয়ে গেছে।`, date: todayISO(), read: false }, ...d.notifications] }));
    } else {
      const rid = uid();
      const newClasses = genClasses(rid, f, students);
      setDb((d) => ({ ...d,
        routine: [...(d.routine || []), { id: rid, ...f, dur: +f.dur, studentIds: students }],
        classes: [...d.classes, ...newClasses], // স্টুডেন্ট ও উস্তাদের নাম অনুযায়ী পোর্টালে অটো যোগ
        notifications: [{ id: uid(), for: [f.teacherId, ...students, "admin1", "dir1"], text: `📅 স্থায়ী সাপ্তাহিক রুটিন তৈরি হয়েছে: ${c.name} — ${f.days.map((i) => DAY_BN[i]).join(", ")} ${f.time} (উস্তাদ: ${userById(f.teacherId).name})। শিক্ষার্থী: ${students.map((s) => userById(s).name).join(", ")}। ক্লাসগুলো স্বয়ংক্রিয়ভাবে আপনার পোর্টালে যোগ হয়ে গেছে।`, date: todayISO(), read: false }, ...d.notifications] }));
    }
    setShow(false); setEditId(null); setF(blankR());
  };
  const del = (id) => setDb((d) => ({ ...d, routine: d.routine.filter((r) => r.id !== id), classes: d.classes.filter((k) => !(k.routineId === id && k.date >= todayISO())) }));
  const visible = (db.routine || []).filter((r) => itemVisible(r, user)); // নাম অনুযায়ী যার যার পোর্টালে
  return (
    <Section title="ক্লাস রুটিন (স্থায়ী সাপ্তাহিক)" sub={canEdit ? "কোন স্টুডেন্ট কোন উস্তাদের কাছে কোন বারে কোন সময়ে কোন কোর্সে পড়বে — সব সময়ের জন্য; এডিট কেবল এডমিনের হাতে" : "আপনার স্থায়ী সাপ্তাহিক ক্লাসের সময়সূচি — তারিখ-সময় অনুযায়ী জয়েন অপশন অটো আসবে"}
      action={canEdit && <Btn onClick={() => setShow(true)}>+ রুটিন তৈরি করুন</Btn>}>
      <TeacherWiseBoard db={db} setDb={setDb} user={user} />
      <div style={{ display: "grid", gap: 10 }}>
        {WEEK_ORDER.map((wd) => {
          const items = visible.filter((r) => r.days.includes(wd));
          return (
            <div key={wd} style={{ ...S.card, padding: 14, borderLeft: `4px solid ${items.length ? C.emerald : C.line}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <b style={{ width: 110, fontSize: 14, color: items.length ? C.emerald : C.muted }}>{DAY_BN[wd]}</b>
                <div style={{ flex: 1, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {items.length === 0 && <span style={{ fontSize: 12.5, color: C.muted }}>— ক্লাস নেই —</span>}
                  {items.map((r) => {
                    const c = courseById(COURSES, r.courseId);
                    return (
                      <span key={r.id} style={{ display: "inline-flex", alignItems: "center", gap: 8, background: C.greenBg, border: `1px solid ${C.line}`, borderRadius: 10, padding: "7px 12px", fontSize: 12.5 }}>
                        <b style={{ color: c.color || C.emerald }}>{c.name}</b> {r.kind && r.kind !== "নিয়মিত ক্লাস" && <Tag color={C.red} bg={C.redBg}>{r.kind}</Tag>} 🕐 {r.time} · {bn(r.dur)} মি · {userById(r.teacherId || c.teacherId).name}{canEdit && (r.studentIds || []).length > 0 && <span style={{ color: C.muted }}> · 👥 {r.studentIds.map((s) => userById(s).name.split(" ")[0]).join(", ")}</span>}
                        {canEdit && <button title="এডিট — কেবল এডমিন" onClick={() => { setF({ courseId: r.courseId, days: [...r.days], time: r.time, dur: r.dur, zoom: r.zoom, kind: "নিয়মিত ক্লাস", teacherId: r.teacherId, studentIds: r.studentIds || [] }); setEditId(r.id); setShow(true); }} style={{ border: "none", background: "transparent", cursor: "pointer" }}>✏️</button>}{canEdit && <button onClick={() => del(r.id)} style={{ border: "none", background: "transparent", color: C.red, cursor: "pointer", fontWeight: 800 }}>✕</button>}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {show && (
        <Modal title={editId ? "✏️ রুটিন এডিট করুন (কেবল এডমিন)" : "স্থায়ী সাপ্তাহিক রুটিন তৈরি করুন"} onClose={() => { setShow(false); setEditId(null); setF(blankR()); }} wide>
          <div style={{ padding: "9px 12px", borderRadius: 10, background: C.greenBg, fontSize: 12, color: C.emerald, marginBottom: 12 }}>💡 কোন স্টুডেন্ট কোন উস্তাদের কাছে সপ্তাহের কোন বারে, কোন সময়ে, কোন কোর্সে পড়বে — সব সময়ের জন্য রুটিন। ছুটে যাওয়া ক্লাসের মেকআপ/সাপোর্টের জন্য "ক্লাস ও জুম জয়েন" পেজের শিডিউল ব্যবহার করুন।</div>
          <div><label style={S.label}>কোর্স</label>
            <select style={S.input} value={f.courseId} onChange={(e) => { const c = courseById(courses, e.target.value); setF({ ...f, courseId: e.target.value, teacherId: c.teacherId || f.teacherId }); }}>{courses.map((c) => <option key={c.id} value={c.id}>{c.name} — {c.studentIds.length}জন শিক্ষার্থী</option>)}</select></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>উস্তাদ/উস্তাদা — কার কাছে পড়বে</label>
            <select style={S.input} value={f.teacherId} onChange={(e) => setF({ ...f, teacherId: e.target.value })}>{USERS.filter((u) => u.role === "teacher").map((t) => <option key={t.id} value={t.id}>{t.name} ({t.sub})</option>)}</select></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>শিক্ষার্থী বাছাই করুন — এক এক করে ({bn(f.studentIds.length)} জন নির্বাচিত; কাউকে না বাছলে কোর্সের সবাই)</label>
            <StudentPicker selected={f.studentIds} onToggle={(id) => setF({ ...f, studentIds: f.studentIds.includes(id) ? f.studentIds.filter((x) => x !== id) : [...f.studentIds, id] })} /></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>সপ্তাহের কোন কোন দিন</label>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {WEEK_ORDER.map((wd) => (
                <button key={wd} onClick={() => toggleDay(wd)} style={{ padding: "8px 12px", borderRadius: 99, cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 12.5, border: `2px solid ${f.days.includes(wd) ? C.emerald : C.line}`, background: f.days.includes(wd) ? C.greenBg : "#fff", color: f.days.includes(wd) ? C.emerald : C.text }}>{DAY_BN[wd]}</button>
              ))}
            </div></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 10 }}>
            <div><label style={S.label}>সময়</label><input type="time" style={S.input} value={f.time} onChange={(e) => setF({ ...f, time: e.target.value })} /></div>
            <div><label style={S.label}>সময়কাল (মিনিট)</label><input type="number" style={S.input} value={f.dur} onChange={(e) => setF({ ...f, dur: e.target.value })} /></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>জুম লিংক</label><input style={S.input} value={f.zoom} onChange={(e) => setF({ ...f, zoom: e.target.value })} /></div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={add}>{editId ? "✏️ রুটিন আপডেট করুন" : "রুটিন তৈরি করুন — স্টুডেন্ট ও উস্তাদের পোর্টালে অটো যোগ হবে"}</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ছুটির আবেদন — দরখাস্ত ফরমেট; এডমিন ফরওয়ার্ড, মঞ্জুর কেবল পরিচালক ═══════════════ */
function LeaveView({ db, setDb, user }) {
  const [show, setShow] = useState(false);
  const [f, setF] = useState({ type: "অসুস্থতা", from: todayISO(), to: todayISO(), reason: "" });
  const canApply = user.role !== "director";
  const list = (user.role === "student" || user.role === "teacher") ? db.leaves.filter((l) => l.userId === user.id) : db.leaves;
  const submit = () => {
    if (!f.reason.trim()) return notice("ছুটির কারণ লিখুন।");
    setDb((d) => ({ ...d,
      leaves: [{ id: uid(), userId: user.id, ...f, date: todayISO(), status: "pending_admin" }, ...d.leaves],
      notifications: [{ id: uid(), for: ["admin1", "dir1"], text: `✉️ ${user.name} ছুটির আবেদন করেছেন (${f.type}: ${fmtDate(f.from)} — ${fmtDate(f.to)})`, date: todayISO(), read: false }, ...d.notifications] }));
    setShow(false); setF({ type: "অসুস্থতা", from: todayISO(), to: todayISO(), reason: "" });
  };
  const forward = (l) => setDb((d) => ({ ...d,
    leaves: d.leaves.map((x) => x.id === l.id ? { ...x, status: "forwarded" } : x),
    notifications: [{ id: uid(), for: ["dir1"], text: `✉️ এডমিন ${userById(l.userId).name}-এর ছুটির আবেদন পরিচালক বরাবর পাঠিয়েছেন।`, date: todayISO(), read: false }, ...d.notifications] }));
  const decide = (l, ok) => setDb((d) => ({ ...d,
    leaves: d.leaves.map((x) => x.id === l.id ? { ...x, status: ok ? "approved" : "rejected" } : x),
    notifications: [{ id: uid(), for: [l.userId], text: `আপনার ছুটির আবেদন (${l.type}) ${ok ? "মঞ্জুর হয়েছে ✔ আলহামদুলিল্লাহ" : "নামঞ্জুর হয়েছে ✘"}।`, date: todayISO(), read: false }, ...d.notifications] }));
  const stTag = (s) => s === "pending_admin" ? <Tag color={"#a16207"} bg={C.amberBg}>⏳ এডমিনের কাছে</Tag>
    : s === "forwarded" ? <Tag color={C.blue} bg={C.blueBg}>📤 পরিচালকের কাছে</Tag>
    : s === "approved" ? <Tag>মঞ্জুর ✔</Tag> : <Tag color={C.red} bg={C.redBg}>নামঞ্জুর ✘</Tag>;
  return (
    <Section title="ছুটির আবেদন" sub="দরখাস্ত ফরম পূরণ করে জমা দিন — এডমিন দেখে পরিচালক বরাবর পাঠাবেন, মঞ্জুরের ক্ষমতা কেবল পরিচালকের"
      action={canApply && <Btn onClick={() => setShow(true)}>✍️ ছুটির দরখাস্ত লিখুন</Btn>}>
      <div style={{ display: "grid", gap: 10 }}>
        {list.length === 0 && <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>কোনো ছুটির আবেদন নেই।</div>}
        {list.map((l) => {
          const ap = userById(l.userId);
          return (
            <div key={l.id} style={{ ...S.card, padding: 0, overflow: "hidden", borderLeft: `4px solid ${l.status === "approved" ? C.green : l.status === "rejected" ? C.red : C.gold}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <b style={{ fontSize: 14 }}>{ap.name}</b> <Tag color={C.blue} bg={C.blueBg}>{ap.role === "student" ? "স্টুডেন্ট" : ap.role === "teacher" ? "উস্তাদ/উস্তাদা" : "এডমিন"}</Tag>
                  <div style={{ fontSize: 12.5, color: C.muted }}>{l.type} · {fmtDate(l.from)} — {fmtDate(l.to)} · আবেদন: {fmtDate(l.date)}</div>
                </div>
                {stTag(l.status)}
                {user.role === "admin" && l.status === "pending_admin" && <Btn sm kind="gold" onClick={() => forward(l)}>📤 পরিচালক বরাবর পাঠান</Btn>}
                {isDir(user) && (l.status === "pending_admin" || l.status === "forwarded") && (
                  <span style={{ display: "flex", gap: 6 }}>
                    <Btn sm onClick={() => decide(l, true)}>✔ মঞ্জুর</Btn>
                    <Btn sm kind="danger" onClick={() => decide(l, false)}>✘ নামঞ্জুর</Btn>
                  </span>
                )}
              </div>
              {/* দরখাস্ত ফরমেট */}
              <div style={{ borderTop: `1px dashed ${C.line}`, background: "#fffdf8", padding: "14px 18px", fontSize: 13, lineHeight: 1.8 }}>
                <div>তারিখ: {fmtDate(l.date)}</div>
                <div>বরাবর,<br />পরিচালক মহোদয়,<br />তারবিয়াতুল কুরআন একাডেমি</div>
                <div style={{ margin: "6px 0" }}><b>বিষয়: ছুটির আবেদন ({l.type})।</b></div>
                <div>জনাব,<br />সবিনয় নিবেদন এই যে, আমি {ap.name}, আপনার প্রতিষ্ঠানের একজন {ap.role === "student" ? "শিক্ষার্থী" : ap.role === "teacher" ? "শিক্ষক" : "এডমিন"}। {l.reason} এমতাবস্থায়, {fmtDate(l.from)} থেকে {fmtDate(l.to)} পর্যন্ত ছুটি মঞ্জুর করতে আপনার সদয় মর্জি হয়।</div>
                <div style={{ marginTop: 6 }}>নিবেদক,<br /><b>{ap.name}</b></div>
              </div>
            </div>
          );
        })}
      </div>
      {show && (
        <Modal title="✍️ ছুটির দরখাস্ত" onClose={() => setShow(false)}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><label style={S.label}>ছুটির ধরন</label><select style={S.input} value={f.type} onChange={(e) => setF({ ...f, type: e.target.value })}><option>অসুস্থতা</option><option>সফর</option><option>পারিবারিক প্রয়োজন</option><option>পরীক্ষা</option><option>অন্যান্য</option></select></div>
            <div></div>
            <div><label style={S.label}>কবে থেকে</label><input type="date" style={S.input} value={f.from} onChange={(e) => setF({ ...f, from: e.target.value })} /></div>
            <div><label style={S.label}>কবে পর্যন্ত</label><input type="date" style={S.input} value={f.to} onChange={(e) => setF({ ...f, to: e.target.value })} /></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>কারণ / বিবরণ</label>
            <textarea rows={3} style={{ ...S.input, resize: "vertical" }} value={f.reason} onChange={(e) => setF({ ...f, reason: e.target.value })} placeholder="যেমন: পারিবারিক প্রয়োজনে গ্রামের বাড়ি যেতে হবে..." /></div>
          <div style={{ marginTop: 12, borderRadius: 12, background: "#fffdf8", border: `1px dashed ${C.goldL}`, padding: "12px 14px", fontSize: 12.5, lineHeight: 1.8 }}>
            <div style={{ fontWeight: 800, marginBottom: 4, color: C.gold }}>দরখাস্তের প্রিভিউ:</div>
            বরাবর, পরিচালক মহোদয়, তারবিয়াতুল কুরআন একাডেমি<br />
            <b>বিষয়: ছুটির আবেদন ({f.type})।</b><br />
            জনাব, সবিনয় নিবেদন এই যে, আমি {user.name}। {f.reason || "..."} এমতাবস্থায়, {fmtDate(f.from)} থেকে {fmtDate(f.to)} পর্যন্ত ছুটি মঞ্জুর করতে আপনার সদয় মর্জি হয়।<br />
            নিবেদক, <b>{user.name}</b>
          </div>
          <Btn style={{ marginTop: 14, width: "100%", justifyContent: "center" }} onClick={submit}>দরখাস্ত জমা দিন</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ভাউচার/রিসিট — পাঠানো রিসিট প্রাপকের পোর্টালে ═══════════════ */
function MyReceiptsView({ db, user }) {
  const list = (db.sentReceipts || []).filter((x) => x.toUserId === user.id);
  return (
    <Section title="ভাউচার / রিসিট" sub="একাডেমি থেকে আপনার জন্য পাঠানো রিসিট ও ভাউচার — দেখুন, প্রিন্ট বা PDF সেভ করুন">
      <Table head={["ধরন", "মাস/বিবরণ", "পরিমাণ", "তারিখ", "পাঠিয়েছেন", "দেখুন"]}
        rows={list.map((x) => [x.kind, x.month, `৳${bn(Number(x.amount).toLocaleString("en"))}`, x.date, x.sentBy || "—",
          <Btn key="v" sm kind="soft" onClick={() => printReceipt({ ...x, noSend: true }, user, x.kind)}>👁 দেখুন / ডাউনলোড</Btn>])}
        empty="এখনো কোনো রিসিট পাঠানো হয়নি" />
    </Section>
  );
}

/* ═══════════════ সকল স্টুডেন্ট — তালিকা, WhatsApp, বিস্তারিত; এডিট কেবল পরিচালক ═══════════════ */
function AllStudentsView({ db, setDb, user, refresh }) {
  const [detail, setDetail] = useState(null);
  const [edit, setEdit] = useState(null); // {id?} — null=বন্ধ, {}=নতুন
  const students = USERS.filter((u) => u.role === "student");
  const waHi = (s) => `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম ${s.guardian || "অভিভাবক"}, তারবিয়াতুল কুরআন একাডেমির পক্ষ থেকে ${s.name}-এর বিষয়ে যোগাযোগ করছি।`;
  const saveEdit = async () => {
    if (!edit.name || !edit.user) return notice("নাম ও আইডি দিন।");
    // ব্যাকএন্ডে সংরক্ষণ (পাসওয়ার্ডসহ)
    try {
      const { api } = await import("./api");
      const payload = {
        username: edit.user,
        name_bn: edit.name,
        country: edit.country,
        phone: edit.phone,
        email: edit.email,
        guardian: edit.guardian,
        monthly_fee: +edit.fee,
        ...(edit.pass ? { password: edit.pass } : {}),
      };
      await api.saveUser(payload, edit.id || undefined);
    } catch {
      // ব্যাকএন্ড না থাকলে local-এ সংরক্ষণ (mock mode)
    }
    if (edit.id) { // বিদ্যমান এডিট
      const u = USERS.find((x) => x.id === edit.id);
      Object.assign(u, { name: edit.name, country: edit.country, phone: edit.phone, email: edit.email, guardian: edit.guardian, fee: +edit.fee, user: edit.user, pass: edit.pass });
    } else { // নতুন স্টুডেন্ট যোগ
      const id = "s" + uid();
      USERS.push({ id, role: "student", name: edit.name, sub: courseById(COURSES, edit.courseId)?.name || "নতুন স্টুডেন্ট", user: edit.user, pass: edit.pass || genPass(), fee: +edit.fee || 4500, guardian: edit.guardian, country: edit.country, phone: edit.phone, email: edit.email });
      COURSES.find((c) => c.id === edit.courseId)?.studentIds.push(id);
    }
    setEdit(null); refresh();
  };
  const delStudent = (s) => askConfirm(`${s.name}-কে মুছে ফেলবেন?`, () => {
    const i = USERS.findIndex((x) => x.id === s.id);
    if (i > -1) USERS.splice(i, 1);
    COURSES.forEach((c) => { c.studentIds = c.studentIds.filter((x) => x !== s.id); });
    refresh();
  });
  /* এক স্টুডেন্টের পূর্ণ চিত্র */
  const Detail = ({ s }) => {
    const cs = COURSES.filter((c) => c.studentIds.includes(s.id));
    const routines = (db.routine || []).filter((r) => (r.studentIds && r.studentIds.length ? r.studentIds.includes(s.id) : (courseById(COURSES, r.courseId).studentIds || []).includes(s.id)));
    const dues = db.dueMonths[s.id] || [];
    const inf = (k, v) => <div style={{ padding: "8px 10px", background: C.cream, borderRadius: 10, fontSize: 13 }}>{k}: <b>{v || "—"}</b></div>;
    return (
      <Modal title={`বিস্তারিত — ${s.name}`} onClose={() => setDetail(null)} wide>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
          {inf("বাবা/অভিভাবকের নাম", s.guardian)}
          {inf("ইমেইল", s.email)}
          {inf("দেশ", s.country)}
          {inf("WhatsApp", s.phone ? "+" + s.phone : "—")}
          {inf("আইডি", s.user)}
          {inf("পাসওয়ার্ড", s.pass)}
          {inf("মাসিক ফি", `৳${bn((s.fee || 0).toLocaleString("en"))}`)}
          <div style={{ padding: "8px 10px", background: C.cream, borderRadius: 10, fontSize: 13 }}>ফি স্টেটাস: {dues.length ? <Tag color={C.red} bg={C.redBg}>বকেয়া: {dues.join(", ")}</Tag> : <Tag>পরিশোধিত ✔</Tag>}</div>
        </div>
        <div style={{ fontWeight: 800, fontSize: 13.5, margin: "8px 0 6px" }}>📚 কী পড়ে, কার কাছে পড়ে</div>
        {cs.length === 0 && <div style={{ fontSize: 13, color: C.muted }}>কোনো কোর্সে যুক্ত নেই</div>}
        {cs.map((c) => (
          <div key={c.id} style={{ padding: "9px 12px", borderRadius: 10, background: C.greenBg, marginBottom: 6, fontSize: 13 }}>
            <b style={{ color: c.color || C.emerald }}>{c.name}</b> · উস্তাদ: <b>{userById(c.teacherId).name}</b>
          </div>
        ))}
        <div style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}>📅 সপ্তাহে কয়দিন, কী কী বারে, কোন সময়ে</div>
        {routines.length === 0 && <div style={{ fontSize: 13, color: C.muted }}>এখনো রুটিন তৈরি হয়নি</div>}
        {routines.map((r) => {
          const c = courseById(COURSES, r.courseId);
          return (
            <div key={r.id} style={{ padding: "9px 12px", borderRadius: 10, background: C.cream, marginBottom: 6, fontSize: 13 }}>
              <b>{c.name}</b> — সপ্তাহে {bn(r.days.length)} দিন: <b>{r.days.map((i) => DAY_BN[i]).join(", ")}</b> · 🕐 {r.time} ({bn(r.dur)} মি) · উস্তাদ: {userById(r.teacherId || c.teacherId).name}
            </div>
          );
        })}
      </Modal>
    );
  };
  return (
    <Section title="সকল স্টুডেন্ট" sub={isDir(user) ? "সম্পূর্ণ তালিকা — এডিট, যোগ ও মুছে ফেলার নিয়ন্ত্রণ কেবল পরিচালকের" : "সম্পূর্ণ তালিকা — আপনি (এডমিন) কেবল দেখতে পারবেন"}
      action={isDir(user) && <Btn onClick={() => setEdit({ name: "", country: "", phone: "", email: "", guardian: "", fee: 4500, user: "", pass: genPass(), courseId: COURSES[0].id })}>+ নতুন স্টুডেন্ট</Btn>}>
      <Table head={["স্টুডেন্ট নাম", "দেশ", "আইডি", "পাসওয়ার্ড", "WhatsApp নম্বর", "বিস্তারিত", ...(isDir(user) ? ["অ্যাকশন"] : [])]}
        rows={students.map((s) => [
          <b key="n">{s.name}</b>,
          s.country || "—",
          s.user,
          <code key="p" style={{ background: C.cream, padding: "2px 8px", borderRadius: 6, fontSize: 12 }}>{s.pass}</code>,
          <span key="w" style={{ display: "inline-flex", alignItems: "center", gap: 6, whiteSpace: "nowrap" }}>
            {s.phone ? "+" + s.phone : "—"}
            {s.phone && <a href={`https://wa.me/${s.phone}?text=${encodeURIComponent(waHi(s))}`} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}><span style={{ background: "#25D366", color: "#fff", borderRadius: 8, padding: "3px 9px", fontSize: 11.5, fontWeight: 800 }}>💬 মেসেজ</span></a>}
          </span>,
          <Btn key="d" sm kind="ghost" onClick={() => setDetail(s)}>📋 বিস্তারিত</Btn>,
          ...(isDir(user) ? [<span key="a" style={{ display: "flex", gap: 5 }}>
            <Btn sm kind="soft" onClick={() => setEdit({ id: s.id, name: s.name, country: s.country || "", phone: s.phone || "", email: s.email || "", guardian: s.guardian || "", fee: s.fee, user: s.user, pass: s.pass })}>✏️</Btn>
            <Btn sm kind="danger" onClick={() => delStudent(s)}>🗑</Btn>
          </span>] : []),
        ])} />
      {detail && <Detail s={detail} />}
      {edit && (
        <Modal title={edit.id ? `✏️ এডিট — ${edit.name}` : "+ নতুন স্টুডেন্ট যোগ করুন (কেবল পরিচালক)"} onClose={() => setEdit(null)} wide>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><label style={S.label}>নাম</label><input style={S.input} value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></div>
            <div><label style={S.label}>বাবা/অভিভাবকের নাম</label><input style={S.input} value={edit.guardian} onChange={(e) => setEdit({ ...edit, guardian: e.target.value })} /></div>
            <div><label style={S.label}>দেশ</label><input style={S.input} value={edit.country} onChange={(e) => setEdit({ ...edit, country: e.target.value })} /></div>
            <div><label style={S.label}>WhatsApp নম্বর (কান্ট্রি কোডসহ)</label><input style={S.input} value={edit.phone} onChange={(e) => setEdit({ ...edit, phone: e.target.value })} placeholder="8801XXXXXXXXX" /></div>
            <div><label style={S.label}>ইমেইল</label><input style={S.input} value={edit.email} onChange={(e) => setEdit({ ...edit, email: e.target.value })} /></div>
            <div><label style={S.label}>মাসিক ফি (৳)</label><input type="number" style={S.input} value={edit.fee} onChange={(e) => setEdit({ ...edit, fee: e.target.value })} /></div>
            <div><label style={S.label}>লগইন আইডি</label><input style={S.input} value={edit.user} onChange={(e) => setEdit({ ...edit, user: e.target.value })} /></div>
            <div><label style={S.label}>পাসওয়ার্ড</label><div style={{ display: "flex", gap: 6 }}><input style={{ ...S.input, flex: 1 }} value={edit.pass} onChange={(e) => setEdit({ ...edit, pass: e.target.value })} /><Btn kind="soft" sm onClick={() => setEdit({ ...edit, pass: genPass() })}>🎲</Btn></div></div>
          </div>
          {!edit.id && <div style={{ marginTop: 10 }}><label style={S.label}>কোর্স</label><select style={S.input} value={edit.courseId} onChange={(e) => setEdit({ ...edit, courseId: e.target.value })}>{COURSES.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>}
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={saveEdit}>{edit.id ? "✏️ সংরক্ষণ করুন" : "+ যোগ করুন"}</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ উস্তাদ-ভিত্তিক বোর্ড — কার কাছে কে পড়ে, সামনের ক্লাস, স্থগিত করার ক্ষমতা ═══════════════ */
function TeacherWiseBoard({ db, setDb, user }) {
  const teachers = USERS.filter((u) => u.role === "teacher");
  const [sel, setSel] = useState(user.role === "teacher" ? user.id : teachers[0]?.id);
  const tid = user.role === "teacher" ? user.id : sel;
  const t = userById(tid);
  const routines = (db.routine || []).filter((r) => (r.teacherId || courseById(COURSES, r.courseId).teacherId) === tid);
  const upcoming = db.classes.filter((k) => (k.teacherId || courseById(COURSES, k.courseId).teacherId) === tid && k.date >= todayISO() && k.status === "upcoming").sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time)).slice(0, 6);
  const postpone = (k) => askConfirm("ক্লাসটি স্থগিত করবেন? উস্তাদ, স্টুডেন্ট সবার পোর্টালে সাথে সাথে আপডেট হবে এবং অভিভাবকের WhatsApp মেসেজ তৈরি হবে।", () => {
    const c = courseById(COURSES, k.courseId);
    const studs = (k.studentIds && k.studentIds.length ? k.studentIds : c.studentIds) || [];
    setDb((d) => ({ ...d,
      classes: d.classes.map((x) => x.id === k.id ? { ...x, status: "postponed" } : x),
      waOutbox: [...waGuardianMsgs(k, c, "postpone"), ...(d.waOutbox || [])], // অভিভাবকের WhatsApp মেসেজ
      notifications: [{ id: uid(), for: [tid, ...studs, "admin1", "dir1"], text: `⛔ ${c.name} ক্লাসটি (${fmtDate(k.date)}, ${k.time}) অনিবার্য কারণে / উস্তাদ-উস্তাদা অসুস্থ থাকার দরুন স্থগিত করা হয়েছে। পরবর্তীতে শিডিউল করে মেকআপ করা হবে ইনশাআল্লাহ।`, date: todayISO(), read: false }, ...d.notifications] }));
  });
  if (user.role === "student") return null;
  return (
    <div style={{ ...S.card, marginBottom: 16 }}>
      <div style={{ fontWeight: 800, marginBottom: 10 }}>👳 উস্তাদ-ভিত্তিক রুটিন ও ক্লাস</div>
      {user.role !== "teacher" && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          {teachers.map((x) => <Btn key={x.id} sm kind={tid === x.id ? "primary" : "soft"} onClick={() => setSel(x.id)}>{x.name}</Btn>)}
        </div>
      )}
      <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6, color: C.emerald }}>📚 {t.name}-এর কাছে যারা পড়ে:</div>
      {routines.length === 0 && <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 8 }}>এখনো রুটিন নেই</div>}
      {routines.map((r) => {
        const c = courseById(COURSES, r.courseId);
        const studs = (r.studentIds && r.studentIds.length ? r.studentIds : c.studentIds) || [];
        return (
          <div key={r.id} style={{ padding: "8px 12px", borderRadius: 10, background: C.cream, marginBottom: 6, fontSize: 12.5 }}>
            👥 <b>{studs.map((s) => userById(s).name).join(", ") || "—"}</b> — {c.name} · {r.days.map((i) => DAY_BN[i]).join(", ")} · 🕐 {r.time}
          </div>
        );
      })}
      <div style={{ fontSize: 13, fontWeight: 700, margin: "10px 0 6px", color: C.emerald }}>📅 সামনের ক্লাস:</div>
      {upcoming.length === 0 && <div style={{ fontSize: 12.5, color: C.muted }}>আসন্ন কোনো ক্লাস নেই</div>}
      {upcoming.map((k) => {
        const c = courseById(COURSES, k.courseId);
        const studs = (k.studentIds && k.studentIds.length ? k.studentIds : c.studentIds) || [];
        return (
          <div key={k.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 10, background: C.greenBg, marginBottom: 6, fontSize: 12.5, flexWrap: "wrap" }}>
            <span style={{ flex: 1, minWidth: 200 }}><b>{c.name}</b> · {fmtDate(k.date)} · 🕐 {k.time} · 👥 {studs.map((s) => userById(s).name.split(" ")[0]).join(", ")}</span>
            {isAdm(user) && <Btn sm kind="danger" onClick={() => postpone(k)}>⛔ স্থগিত করুন</Btn>}
          </div>
        );
      })}
    </div>
  );
}

/* ═══════════════ WhatsApp মেসেজ আউটবক্স — অভিভাবকের কাছে অটো-প্রস্তুত মেসেজ ═══════════════ */
function WaOutboxView({ db, setDb, user }) {
  const list = db.waOutbox || [];
  const cfg = db.waConfig || { backendUrl: "", autoSend: false };
  const setCfg = (patch) => setDb((d) => ({ ...d, waConfig: { ...(d.waConfig || {}), ...patch } }));
  const sendViaApi = async (m) => {
    if (!cfg.backendUrl) return notice("আগে ব্যাকএন্ড URL সেট করুন (নিচের সেটিংসে)।");
    setDb((d) => ({ ...d, waOutbox: d.waOutbox.map((x) => x.id === m.id ? { ...x, apiTried: true, apiStatus: "sending" } : x) }));
    try {
      const res = await fetch(cfg.backendUrl.replace(/\/+$/, "") + "/api/send-whatsapp", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to: m.phone, text: m.text }),
      });
      setDb((d) => ({ ...d, waOutbox: d.waOutbox.map((x) => x.id === m.id ? { ...x, sent: res.ok, apiStatus: res.ok ? "sent" : "failed" } : x) }));
    } catch (e) {
      setDb((d) => ({ ...d, waOutbox: d.waOutbox.map((x) => x.id === m.id ? { ...x, apiStatus: "failed" } : x) }));
    }
  };
  const markSent = (id) => setDb((d) => ({ ...d, waOutbox: d.waOutbox.map((m) => m.id === id ? { ...m, sent: true } : m) }));
  return (
    <Section title="WhatsApp মেসেজ" sub="ক্লাস শুরুর ৫ মিনিট আগের রিমাইন্ডার ও স্থগিতের মেসেজ অভিভাবকের জন্য স্বয়ংক্রিয়ভাবে তৈরি হয় — API চালু থাকলে নিজে নিজেই চলে যায়">
      {isDir(user) && (
        <div style={{ ...S.card, marginBottom: 14, borderLeft: `4px solid #25D366` }}>
          <div style={{ fontWeight: 800, marginBottom: 4 }}>⚙️ WhatsApp Business API সংযোগ (Twilio / Meta)</div>
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>সাথে দেওয়া ব্যাকএন্ড সার্ভারটি (whatsapp-server.js) ডেপ্লয় করে তার URL এখানে দিন — তারপর অটো-সেন্ড চালু করলেই মেসেজ সরাসরি অভিভাবকের WhatsApp-এ চলে যাবে। API কী/টোকেন ব্যাকএন্ডের .env ফাইলে থাকবে, এখানে নয় (নিরাপত্তার জন্য)।</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <input style={{ ...S.input, flex: 1, minWidth: 220 }} value={cfg.backendUrl} onChange={(e) => setCfg({ backendUrl: e.target.value })} placeholder="ব্যাকএন্ড URL — যেমন: https://tqa-whatsapp.onrender.com" />
            <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 13, fontWeight: 700, cursor: "pointer", padding: "9px 14px", borderRadius: 10, background: cfg.autoSend ? C.greenBg : C.cream, border: `1.5px solid ${cfg.autoSend ? C.green : C.line}` }}>
              <input type="checkbox" checked={cfg.autoSend} onChange={(e) => setCfg({ autoSend: e.target.checked })} />
              ⚡ অটো-সেন্ড {cfg.autoSend ? "চালু" : "বন্ধ"}
            </label>
          </div>
          {cfg.autoSend && !cfg.backendUrl && <div style={{ fontSize: 12, color: C.red, marginTop: 6 }}>⚠️ অটো-সেন্ড চালু কিন্তু ব্যাকএন্ড URL দেওয়া হয়নি।</div>}
        </div>
      )}
      <div style={{ display: "grid", gap: 10 }}>
        {list.length === 0 && <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>এখনো কোনো মেসেজ তৈরি হয়নি — ক্লাস শুরুর ৫ মিনিট আগে বা ক্লাস স্থগিত করলে এখানে অটো চলে আসবে।</div>}
        {list.map((m) => (
          <div key={m.id} style={{ ...S.card, padding: 14, borderLeft: `4px solid ${m.sent ? C.green : m.reason === "ক্লাস স্থগিত" ? C.red : C.gold}` }}>
            <div style={{ display: "flex", gap: 10, alignItems: "flex-start", flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: 220 }}>
                <b style={{ fontSize: 13.5 }}>{m.toName}</b> <Tag color={m.reason === "ক্লাস স্থগিত" ? C.red : C.gold} bg={m.reason === "ক্লাস স্থগিত" ? C.redBg : C.amberBg}>{m.reason}</Tag> {m.sent && <Tag>পাঠানো হয়েছে ✔{m.apiStatus === "sent" ? " (API)" : ""}</Tag>}
                {m.apiStatus === "sending" && <Tag color={C.blue} bg={C.blueBg}>⏳ API দিয়ে যাচ্ছে...</Tag>}
                {m.apiStatus === "failed" && <Tag color={C.red} bg={C.redBg}>API ব্যর্থ — সার্ভার/নম্বর যাচাই করুন</Tag>}
                <div style={{ fontSize: 11.5, color: C.muted }}>শিক্ষার্থী: {m.student} · +{m.phone} · {fmtDate(m.date)}</div>
                <div style={{ fontSize: 12.5, marginTop: 6, background: C.cream, padding: "8px 10px", borderRadius: 8 }}>{m.text}</div>
              </div>
              <span style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {!m.sent && cfg.backendUrl && <Btn sm onClick={() => sendViaApi(m)}>🚀 API দিয়ে পাঠান</Btn>}
                <a href={`https://wa.me/${m.phone}?text=${encodeURIComponent(m.text)}`} target="_blank" rel="noreferrer" onClick={() => markSent(m.id)} style={{ textDecoration: "none" }}>
                  <Btn sm style={{ background: "#25D366", color: "#fff" }}>📱 ম্যানুয়াল (wa.me)</Btn>
                </a>
              </span>
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 12, padding: "10px 12px", borderRadius: 10, background: C.blueBg, fontSize: 12, color: C.blue }}>ℹ️ API সংযুক্ত থাকলে (উপরের সেটিংস) মেসেজ তৈরি হওয়ামাত্র সার্ভার Twilio/Meta-র মাধ্যমে সরাসরি অভিভাবকের WhatsApp-এ পাঠিয়ে দেয়। সেটআপ গাইড: whatsapp-setup.md ফাইলটি দেখুন। API ছাড়া ম্যানুয়াল (wa.me) বাটন তো আছেই।</div>
    </Section>
  );
}

/* ═══════════════ কোর্স ব্যবস্থাপনা — কেবল পরিচালক; যোগ/এডিট/বাদ এখান থেকেই সর্বত্র কার্যকর ═══════════════ */
function CourseManagerView({ db, setDb, refresh }) {
  const [edit, setEdit] = useState(null); // null=বন্ধ, {}=নতুন, {id}=এডিট
  const PALETTE = [C.emerald, C.gold, C.blue, C.red, "#7c3aed", "#0f766e"];
  const save = () => {
    if (!edit.name?.trim()) return notice("কোর্সের নাম দিন।");
    const books = edit.books || []; // একাডেমিক বই তালিকার আইডি
    if (edit.id) {
      const c = COURSES.find((x) => x.id === edit.id);
      Object.assign(c, { name: edit.name, teacherId: edit.teacherId, color: edit.color, books });
    } else {
      COURSES.push({ id: "c" + uid(), name: edit.name, teacherId: edit.teacherId, color: edit.color, books, studentIds: [], lectures: [] });
    }
    setEdit(null); refresh();
  };
  const del = (c) => askConfirm(`"${c.name}" কোর্সটি মুছে ফেলবেন? এর ক্লাস ও রুটিনও সরে যাবে এবং কোথাও আর দেখা যাবে না।`, () => {
    const i = COURSES.findIndex((x) => x.id === c.id);
    if (i > -1) COURSES.splice(i, 1);
    setDb((d) => ({ ...d, classes: d.classes.filter((k) => k.courseId !== c.id), routine: (d.routine || []).filter((r) => r.courseId !== c.id) }));
    refresh();
  });
  return (
    <Section title="কোর্স ব্যবস্থাপনা" sub="নতুন কোর্স যোগ, এডিট ও বাদ — কেবল পরিচালকের নিয়ন্ত্রণে; এখানকার তালিকাই সর্বত্র (রুটিন, শিডিউল, লেকচার প্ল্যান, ভর্তি ফরম) দেখা যায়"
      action={<Btn onClick={() => setEdit({ name: "", teacherId: USERS.find((u) => u.role === "teacher")?.id, color: PALETTE[0], books: [] })}>+ নতুন কোর্স</Btn>}>
      <div style={{ display: "grid", gap: 10 }}>
        {COURSES.map((c) => (
          <div key={c.id} style={{ ...S.card, padding: 16, borderLeft: `4px solid ${c.color || C.emerald}`, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <div style={{ fontWeight: 800, fontSize: 15 }}>{c.name}</div>
              <div style={{ fontSize: 12.5, color: C.muted }}>উস্তাদ: {userById(c.teacherId).name || "—"} · শিক্ষার্থী: {bn(c.studentIds.length)} জন · বই: {bn((c.books || []).length)}টি · লেকচার: {bn(c.lectures.length)}টি</div>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <Btn sm kind="soft" onClick={() => setEdit({ id: c.id, name: c.name, teacherId: c.teacherId, color: c.color || C.emerald, books: [...(c.books || [])] })}>✏️ এডিট</Btn>
              <Btn sm kind="danger" onClick={() => del(c)}>🗑 বাদ দিন</Btn>
            </div>
          </div>
        ))}
      </div>
      {edit && (
        <Modal title={edit.id ? `✏️ কোর্স এডিট — ${edit.name}` : "+ নতুন কোর্স যোগ করুন"} onClose={() => setEdit(null)} wide>
          <label style={S.label}>কোর্সের নাম</label>
          <input style={S.input} value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} placeholder="যেমন: সহীহ মাসনুন দুআ কোর্স" />
          <div style={{ marginTop: 10 }}><label style={S.label}>দায়িত্বপ্রাপ্ত উস্তাদ/উস্তাদা</label>
            <select style={S.input} value={edit.teacherId} onChange={(e) => setEdit({ ...edit, teacherId: e.target.value })}>{USERS.filter((u) => u.role === "teacher").map((t) => <option key={t.id} value={t.id}>{t.name} ({t.sub})</option>)}</select></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>রং</label>
            <div style={{ display: "flex", gap: 8 }}>
              {PALETTE.map((p) => <button key={p} onClick={() => setEdit({ ...edit, color: p })} style={{ width: 34, height: 34, borderRadius: 10, cursor: "pointer", background: p, border: edit.color === p ? "3px solid #1a1f2e" : "2px solid #fff", boxShadow: "0 1px 4px rgba(0,0,0,.2)" }} />)}
            </div></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>📚 কোর্সের বই — একাডেমিক বইসমূহ থেকে সিলেক্ট করুন (সর্বোচ্চ ৬টি · {bn((edit.books || []).length)}টি নির্বাচিত)</label>
            {(db.academicBooks || []).length === 0 ? (
              <div style={{ padding: "14px 12px", borderRadius: 10, background: C.amberBg, fontSize: 12.5, color: "#a16207" }}>
                ⚠️ একাডেমিক বইয়ের তালিকা খালি — আগে সাইডবারের "📚 একাডেমিক বইসমূহ" মেনুতে গিয়ে বই যোগ করুন, তারপর এখানে সিলেক্ট করতে পারবেন।
              </div>
            ) : (
              <div style={{ maxHeight: 180, overflowY: "auto", border: `1.5px solid ${C.line}`, borderRadius: 10, padding: 6, background: "#fff" }}>
                {(db.academicBooks || []).map((b) => {
                  const on = (edit.books || []).includes(b.id);
                  const full = (edit.books || []).length >= 6 && !on;
                  return (
                    <label key={b.id} style={{ display: "flex", gap: 8, alignItems: "center", padding: "6px 8px", fontSize: 13, cursor: full ? "not-allowed" : "pointer", borderRadius: 8, background: on ? C.greenBg : "transparent", opacity: full ? 0.45 : 1 }}>
                      <input type="checkbox" checked={on} disabled={full}
                        onChange={() => setEdit({ ...edit, books: on ? edit.books.filter((x) => x !== b.id) : [...edit.books, b.id] })} />
                      📖 <b>{b.name}</b> <Tag color={C.blue} bg={C.blueBg}>{bookExt(b.file?.name)}</Tag>
                    </label>
                  );
                })}
              </div>
            )}</div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={save}>{edit.id ? "✏️ সংরক্ষণ করুন" : "+ কোর্স যোগ করুন — সর্বত্র দেখা যাবে"}</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ সিলেবাস — কোর্স→বই→লেসন→পৃষ্ঠা→লাইন→মন্তব্য; কেবল পরিচালক তৈরি করবেন ═══════════════ */
function SyllabusView({ db, setDb, courses, user }) {
  const [sel, setSel] = useState(courses[0]?.id);
  const [form, setForm] = useState(null); // {id?, courseId, book, lesson, pages, lines, note}
  const course = courseById(courses, sel);
  const list = (db.syllabus || []).filter((s) => s.courseId === sel);
  const openNew = () => setForm({ courseId: sel, book: (course.books || [])[0] || "অন্যান্য", lesson: "", pages: "", lines: "", note: "" });
  const save = () => {
    if (!form.lesson.trim()) return notice("লেসন লিখে দিন।");
    const entry = { courseId: form.courseId, book: form.book, lesson: form.lesson.trim(), pages: form.pages.trim(), lines: form.lines.trim(), note: form.note.trim() };
    if (form.id) setDb((d) => ({ ...d, syllabus: d.syllabus.map((s) => s.id === form.id ? { ...s, ...entry } : s) }));
    else setDb((d) => ({ ...d, syllabus: [...(d.syllabus || []), { id: uid(), ...entry }] }));
    setForm(null);
  };
  const del = (s) => askConfirm("সিলেবাসের এই অংশটি মুছে ফেলবেন?", () => setDb((d) => ({ ...d, syllabus: d.syllabus.filter((x) => x.id !== s.id) })));
  const bookNameOf = (id) => ((db.academicBooks || []).find((b) => b.id === id) || {}).name;
  const fBooks = (courseById(courses, form?.courseId || sel).books || []).map(bookNameOf).filter(Boolean);
  return (
    <Section title="সিলেবাস" sub={isDir(user) ? "কোর্স → বই → লেসন → পৃষ্ঠা → লাইন → মন্তব্য — কেবল পরিচালক তৈরি করবেন; লেকচার প্ল্যান এখান থেকেই টপিক বাছাই করে" : "কোর্সভিত্তিক পূর্ণাঙ্গ সিলেবাস — পরিচালক কর্তৃক নির্ধারিত"}
      action={isDir(user) && <Btn onClick={openNew}>+ সিলেবাস যোগ করুন</Btn>}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
        {courses.map((c) => <Btn key={c.id} sm kind={sel === c.id ? "primary" : "soft"} onClick={() => setSel(c.id)}>{c.name}</Btn>)}
      </div>
      {list.length === 0 && (
        <div style={{ ...S.card, textAlign: "center", color: C.muted, padding: 28 }}>
          📜 "{course.name}" কোর্সের সিলেবাস এখনো তৈরি হয়নি।{isDir(user) ? " ওপরের \"+ সিলেবাস যোগ করুন\" বাটন দিয়ে শুরু করুন।" : " পরিচালক তৈরি করলে এখানে দেখা যাবে ইনশাআল্লাহ।"}
        </div>
      )}
      {list.length > 0 && (
        <Table head={["ক্রম", "বই", "লেসন", "পৃষ্ঠা", "লাইন", "মন্তব্য", ...(isDir(user) ? ["অ্যাকশন"] : [])]}
          rows={list.map((s, i) => [
            bn(i + 1),
            <b key="b">{s.book || "—"}</b>,
            s.lesson,
            s.pages || "—",
            s.lines || "—",
            <span key="n" style={{ color: C.muted, fontSize: 12.5 }}>{s.note || "—"}</span>,
            ...(isDir(user) ? [<span key="a" style={{ display: "flex", gap: 5 }}>
              <Btn sm kind="soft" onClick={() => setForm({ id: s.id, courseId: s.courseId, book: s.book, lesson: s.lesson, pages: s.pages, lines: s.lines, note: s.note })}>✏️</Btn>
              <Btn sm kind="danger" onClick={() => del(s)}>🗑</Btn>
            </span>] : []),
          ])} />
      )}
      {form && (
        <Modal title={form.id ? "✏️ সিলেবাস এডিট" : "+ সিলেবাস যোগ করুন"} onClose={() => setForm(null)} wide>
          <label style={S.label}>১. কোর্স সিলেকশন</label>
          <select style={S.input} value={form.courseId} onChange={(e) => { const c2 = courseById(courses, e.target.value); setForm({ ...form, courseId: e.target.value, book: (c2.books || [])[0] || "অন্যান্য" }); }}>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <div style={{ marginTop: 10 }}><label style={S.label}>২. বই সিলেকশন {fBooks.length === 0 && <span style={{ color: C.red }}>(এ কোর্সে বই নেই — "কোর্স" মেনুতে ✏️ এডিট করে বই যোগ করুন)</span>}</label>
            <select style={S.input} value={form.book} onChange={(e) => setForm({ ...form, book: e.target.value })}>
              {fBooks.map((b) => <option key={b} value={b}>{b}</option>)}
              <option value="অন্যান্য">অন্যান্য / বই নির্ধারিত নয়</option>
            </select></div>
          <div style={{ marginTop: 10 }}><label style={S.label}>৩. লেসন</label>
            <input style={S.input} value={form.lesson} onChange={(e) => setForm({ ...form, lesson: e.target.value })} placeholder="যেমন: লেসন ৪ — হরকত পরিচিতি" /></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 10 }}>
            <div><label style={S.label}>৪. পৃষ্ঠা</label>
              <input style={S.input} value={form.pages} onChange={(e) => setForm({ ...form, pages: e.target.value })} placeholder="যেমন: ১২–১৫" /></div>
            <div><label style={S.label}>৫. লাইন</label>
              <input style={S.input} value={form.lines} onChange={(e) => setForm({ ...form, lines: e.target.value })} placeholder="যেমন: ১–৮" /></div>
          </div>
          <div style={{ marginTop: 10 }}><label style={S.label}>৬. মন্তব্য</label>
            <textarea rows={2} style={{ ...S.input, resize: "vertical" }} value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} placeholder="যেমন: মশকসহ পড়াতে হবে, আগের পৃষ্ঠার দাওরসহ..." /></div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={save}>{form.id ? "✏️ সংরক্ষণ করুন" : "+ যোগ করুন"}</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ একাডেমিক বইসমূহ — পরিচালক আপলোড করেন; যে যার কোর্সের বই দেখে ═══════════════ */
function AcademicBooksView({ db, setDb, user, courses }) {
  const [form, setForm] = useState(null); // {name, file}
  const [viewer, setViewer] = useState(null); // ক্লিক করা বই — এখানেই খুলবে
  const all = db.academicBooks || [];
  const bookCourses = (bid) => COURSES.filter((c) => (c.books || []).includes(bid));
  // পরিচালক/এডমিন: সব বই; উস্তাদ/স্টুডেন্ট: নিজের কোর্সের বই
  const myIds = new Set(courses.flatMap((c) => c.books || []));
  const visible = isAdm(user) ? all : all.filter((b) => myIds.has(b.id));
  const pickFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => setForm((x) => ({ ...x, file: { data: r.result, name: f.name, type: f.type } }));
    r.readAsDataURL(f);
  };
  const save = () => {
    if (!form.name.trim()) return notice("বইয়ের নাম লিখুন।");
    if (!form.file) return notice("ডিভাইস থেকে বইয়ের ফাইল যুক্ত করুন।");
    setDb((d) => ({ ...d, academicBooks: [...(d.academicBooks || []), { id: "b" + uid(), name: form.name.trim(), file: form.file, date: todayISO() }] }));
    setForm(null);
  };
  const del = (b) => askConfirm(`"${b.name}" বইটি মুছে ফেলবেন? কোর্সগুলো থেকেও সরে যাবে।`, () => {
    COURSES.forEach((c) => { c.books = (c.books || []).filter((x) => x !== b.id); });
    setDb((d) => ({ ...d, academicBooks: d.academicBooks.filter((x) => x.id !== b.id) }));
  });
  /* বইয়ের নামে ক্লিক → এখানেই (ইন-অ্যাপ ভিউয়ারে) খুলবে — ডাউনলোড নয় */
  const BookLink = ({ b }) => (
    <span onClick={() => setViewer(b)}
      style={{ fontWeight: 800, fontSize: 14, color: C.emerald, cursor: "pointer", borderBottom: `1.5px dashed ${C.emerald}` }}
      title="ক্লিক করলেই এখানে খুলবে">
      📖 {b.name}
    </span>
  );
  /* ইন-অ্যাপ বই ভিউয়ার: PDF → iframe, ছবি → img, অন্য ফরমেট → বার্তা + বিকল্প */
  const BookViewer = ({ b }) => {
    const { url, mime } = useMemo(() => dataUrlToBlobUrl(b.file.data), [b.id]);
    const isPdf = mime === "application/pdf";
    const isImg = mime.startsWith("image/");
    return (
      <div onClick={() => setViewer(null)} style={{ position: "fixed", inset: 0, zIndex: 220, background: "rgba(18,63,40,.6)", display: "grid", placeItems: "center", padding: 12 }}>
        <div onClick={(e) => e.stopPropagation()} style={{ background: "#fff", borderRadius: 16, width: "100%", maxWidth: 860, maxHeight: "92vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", borderBottom: `1px solid ${C.line}` }}>
            <b style={{ flex: 1, fontSize: 14.5 }}>📖 {b.name} <Tag color={C.blue} bg={C.blueBg}>{bookExt(b.file.name)}</Tag></b>
            <button onClick={() => setViewer(null)} style={{ border: "none", background: C.cream, borderRadius: 8, width: 32, height: 32, cursor: "pointer", fontSize: 15 }}>✕</button>
          </div>
          <div style={{ flex: 1, overflow: "auto", background: "#525659", display: "grid", placeItems: isImg ? "center" : "stretch" }}>
            {isPdf && <iframe src={url} title={b.name} style={{ width: "100%", height: "78vh", border: "none", background: "#fff" }} />}
            {isImg && <img src={b.file.data} alt={b.name} style={{ maxWidth: "100%", maxHeight: "78vh", objectFit: "contain" }} />}
            {!isPdf && !isImg && (
              <div style={{ background: "#fff", padding: 34, textAlign: "center" }}>
                <div style={{ fontSize: 40 }}>📄</div>
                <div style={{ fontWeight: 800, fontSize: 15, margin: "10px 0 4px" }}>{b.file.name}</div>
                <div style={{ fontSize: 13, color: C.muted, marginBottom: 16 }}>এই ফরমেট ({bookExt(b.file.name)}) ব্রাউজারে সরাসরি প্রদর্শন করা যায় না — চাইলে ফাইলটি নিয়ে ডিভাইসের রিডারে দেখতে পারেন।</div>
                <a href={url} download={b.file.name} style={{ textDecoration: "none" }}><Btn>⬇️ ফাইলটি নিন</Btn></a>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };
  const Card = (b) => (
    <div key={b.id} style={{ ...S.card, padding: 14, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
      <div style={{ flex: 1, minWidth: 200 }}>
        <BookLink b={b} />
        <div style={{ fontSize: 11.5, color: C.muted, marginTop: 3 }}>
          <Tag color={C.blue} bg={C.blueBg}>{bookExt(b.file.name)}</Tag> {b.file.name} · যোগ: {fmtDate(b.date)}
          {isAdm(user) && <span> · কোর্স: {bookCourses(b.id).map((c) => c.name).join(", ") || "কোনো কোর্সে যুক্ত নয়"}</span>}
        </div>
      </div>
      {isDir(user) && <Btn sm kind="danger" onClick={() => del(b)}>🗑</Btn>}
    </div>
  );
  return (
    <Section title="একাডেমিক বইসমূহ" sub={isAdm(user) ? "একাডেমির সকল বইয়ের কেন্দ্রীয় তালিকা — কোর্স তৈরির সময় এখান থেকেই বই সিলেক্ট হয়" : "আপনার কোর্সের নির্ধারিত বইসমূহ — নামে ক্লিক করলেই খুলবে"}
      action={isDir(user) && <Btn onClick={() => setForm({ name: "", file: null })}>+ বই যোগ করুন</Btn>}>
      {visible.length === 0 && (
        <div style={{ ...S.card, textAlign: "center", color: C.muted, padding: 28 }}>
          📚 {isAdm(user) ? "এখনো কোনো বই যোগ হয়নি — \"+ বই যোগ করুন\" দিয়ে শুরু করুন।" : "আপনার কোর্সে এখনো কোনো বই নির্ধারিত হয়নি।"}
        </div>
      )}
      {isAdm(user) ? (
        <div style={{ display: "grid", gap: 10 }}>{visible.map(Card)}</div>
      ) : (
        /* উস্তাদ/স্টুডেন্ট: নিজের কোর্স হিসাবে ভাগ করা তালিকা */
        courses.map((c) => {
          const items = all.filter((b) => (c.books || []).includes(b.id));
          if (!items.length) return null;
          return (
            <div key={c.id} style={{ marginBottom: 16 }}>
              <div style={{ fontWeight: 800, fontSize: 14.5, marginBottom: 8, color: c.color || C.emerald }}>📗 {c.name}</div>
              <div style={{ display: "grid", gap: 10 }}>{items.map(Card)}</div>
            </div>
          );
        })
      )}
      {viewer && <BookViewer b={viewer} />}
      {form && (
        <Modal title="+ বই যোগ করুন" onClose={() => setForm(null)}>
          <label style={S.label}>বইয়ের নাম লিখুন</label>
          <input style={S.input} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="যেমন: নুরানী কায়দা (সংশোধিত)" />
          <div style={{ marginTop: 12 }}>
            <label style={S.label}>ফাইল যুক্ত করুন — যেকোনো ফরমেট (PDF, DOC, PNG, JPG...)</label>
            <label style={{ display: "grid", placeItems: "center", gap: 6, padding: "24px 14px", border: `2px dashed ${form.file ? C.emerald : C.line}`, borderRadius: 14, cursor: "pointer", background: form.file ? C.greenBg : C.cream, textAlign: "center" }}>
              <span style={{ fontSize: 30 }}>{form.file ? "✅" : "📁"}</span>
              <span style={{ fontSize: 13, fontWeight: 700 }}>{form.file ? form.file.name : "ডিভাইস থেকে ফাইল বেছে নিন"}</span>
              <input type="file" style={{ display: "none" }} onChange={pickFile} />
            </label>
          </div>
          <Btn style={{ marginTop: 16, width: "100%", justifyContent: "center" }} onClick={save}>+ তালিকায় যোগ করুন</Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ওভারভিউ ড্যাশবোর্ড ═══════════════ */
function Overview({ db, courses, user, goTo }) {
  const todayClasses = db.classes.filter((k) => k.date === todayISO() && k.status !== "done" && courseById(courses, k.courseId).id);
  const income = db.feePayments.reduce((s, p) => s + p.amount, 0);
  const newForms = db.forms.filter((f) => f.status === "new").length;
  const missedTopics = courses.flatMap((c) => c.lectures.flatMap((l) => l.topics)).filter((t) => t.covered === false).length;
  const greet = user.role === "director" ? "আসসালামু আলাইকুম, পরিচালক সাহেব" : user.role === "admin" ? `আসসালামু আলাইকুম, ${user.name} (এডমিন)` : user.role === "teacher" ? `আসসালামু আলাইকুম, ${user.name}` : `আসসালামু আলাইকুম, ${user.name.split(" ")[0]}`;
  return (
    <>
      <div style={{ background: `linear-gradient(135deg, ${C.emeraldD}, ${C.emerald})`, borderRadius: 18, padding: "22px 24px", color: "#fff", marginBottom: 18, position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", right: 18, top: 8, fontSize: 56, opacity: .18 }}>🕌</div>
        <div style={{ fontSize: 12.5, color: C.goldL, fontWeight: 700, letterSpacing: 1 }}>তারবিয়াতুল কুরআন একাডেমি</div>
        <div style={{ fontSize: 21, fontWeight: 800, margin: "4px 0" }}>{greet} 🌙</div>
        <div style={{ fontSize: 13, color: "#d7e9de" }}>{fmtDate(todayISO())} · আজ {bn(todayClasses.length)}টি ক্লাস নির্ধারিত আছে</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginBottom: 18 }}>
        <Stat icon="🎥" label="আজকের ক্লাস" value={bn(todayClasses.length)} />
        <Stat icon="📚" label="চলমান কোর্স" value={bn(courses.length)} accent={C.blue} />
        {isAdm(user) && <Stat icon="💰" label="মোট ফি আদায়" value={`৳${bn(income.toLocaleString("en"))}`} accent={C.gold} />}
        {isAdm(user) && <Stat icon="🎓" label="ভর্তি আবেদন" value={bn(db.admissions.filter((a) => a.status === "pending").length)} accent={C.gold} note="অপেক্ষমাণ" />}
        {user.role === "teacher" && (() => { const rs = db.ratings.filter((r) => r.teacherId === user.id); const av = rs.length ? (rs.reduce((s, r) => s + r.stars, 0) / rs.length).toFixed(1) : "—"; return <Stat icon="🌟" label="ক্লাসের মান" value={`★ ${bn(av)}`} accent={C.gold} note={`${bn(rs.length)}টি মূল্যায়ন`} />; })()}
        {isAdm(user) && <Stat icon="📨" label="নতুন ফর্ম" value={bn(newForms)} accent={C.red} note="উত্তর বাকি" />}
        {user.role !== "admin" && <Stat icon="📝" label="অ্যাসাইনমেন্ট" value={bn(db.assignments.filter((a) => courseById(courses, a.courseId).id).length)} accent={C.gold} />}
        {missedTopics > 0 && <Stat icon="✘" label="বাদ পড়া টপিক" value={bn(missedTopics)} accent={C.red} note="এডমিন সংশোধনযোগ্য" />}
      </div>
      <Section title="আজকের ক্লাসে ফোকাস করুন" action={<Btn sm kind="ghost" onClick={() => goTo("classes")}>সব ক্লাস দেখুন →</Btn>}>
        <div style={{ display: "grid", gap: 10 }}>
          {todayClasses.length === 0 && <div style={{ ...S.card, textAlign: "center", color: C.muted }}>আজ আর কোনো ক্লাস বাকি নেই। আলহামদুলিল্লাহ।</div>}
          {todayClasses.map((k) => {
            const c = courseById(courses, k.courseId);
            const lec = c.lectures?.[k.lectureNo - 1];
            return (
              <div key={k.id} style={{ ...S.card, padding: 16, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", border: `1.5px solid ${C.goldL}`, background: "#fffdf6" }}>
                <div style={{ fontSize: 26 }}>🕐</div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontWeight: 800 }}>{c.name} — {k.time}</div>
                  <div style={{ fontSize: 12.5, color: C.muted }}>লেকচার {bn(k.lectureNo)}: {lec?.title}</div>
                  <div style={{ fontSize: 12, color: C.muted }}>আজকের টপিক: {lec?.topics.map((t) => t.text).join(" · ")}</div>
                </div>
                <Btn kind="gold" onClick={() => goTo("classes")}>ক্লাসে যান →</Btn>
              </div>
            );
          })}
        </div>
      </Section>
      <Section title="সাম্প্রতিক নোটিশ" action={<Btn sm kind="ghost" onClick={() => goTo("notices")}>সব দেখুন →</Btn>}>
        <div style={{ display: "grid", gap: 8 }}>
          {db.notices.slice(0, 2).map((n) => <div key={n.id} style={{ ...S.card, padding: 14 }}><b style={{ fontSize: 13.5 }}>📌 {n.title}</b><div style={{ fontSize: 12.5, color: C.muted }}>{n.body}</div></div>)}
        </div>
      </Section>
    </>
  );
}

/* ═══════════════ অ্যাপ শেল ═══════════════ */
const NAV = [
  { id: "overview", icon: "🏠", label: "ড্যাশবোর্ড", roles: ["director", "admin", "teacher", "student"] },
  { id: "classes", icon: "🎥", label: "ক্লাস ও জুম জয়েন", roles: ["director", "admin", "teacher", "student"] },
  { id: "routine", icon: "📅", label: "ক্লাস রুটিন", roles: ["director", "admin", "teacher", "student"] },
  { id: "lectures", icon: "📋", label: "লেকচার প্ল্যান", roles: ["director", "admin", "teacher", "student"] },
  { id: "syllabus", icon: "📜", label: "সিলেবাস", roles: ["director", "admin", "teacher", "student"] },
  { id: "attendance", icon: "🗓️", label: "হাজিরা", roles: ["director", "admin", "teacher", "student"] },
  { id: "assignments", icon: "📝", label: "অ্যাসাইনমেন্ট", roles: ["director", "admin", "teacher", "student"] },
  { id: "exams", icon: "🏅", label: "পরীক্ষা ও ফলাফল", roles: ["director", "admin", "teacher", "student"] },
  { id: "progress", icon: "📈", label: "অগ্রগতি ও ফি রিপোর্ট", roles: ["director", "admin", "teacher", "student"] },
  { id: "payments", icon: "💳", label: "পেমেন্ট", roles: ["student"] },
  { id: "studentpayments", icon: "💵", label: "স্টুডেন্ট পেমেন্ট", roles: ["director"] },
  { id: "waoutbox", icon: "📤", label: "WhatsApp মেসেজ", roles: ["director", "admin"] },
  { id: "teacherreport", icon: "🌟", label: "টিচার রিপোর্ট ও পেমেন্ট", roles: ["director", "admin", "teacher"] },
  { id: "coursemgr", icon: "📖", label: "কোর্স", roles: ["director"] },
  { id: "allstudents", icon: "👥", label: "সকল স্টুডেন্ট", roles: ["director", "admin"] },
  { id: "admissions", icon: "🎓", label: "ভর্তি আবেদন", roles: ["director", "admin"] },
  { id: "accounts", icon: "🏦", label: "হিসাব-নিকাশ", roles: ["director"] },
  { id: "forms", icon: "📨", label: "ফর্ম সাবমিশন", roles: ["director", "admin"] },
  { id: "books", icon: "📚", label: "একাডেমিক বইসমূহ", roles: ["director", "admin", "teacher", "student"] },
  { id: "myreceipts", icon: "🧾", label: "ভাউচার/রিসিট", roles: ["admin", "teacher", "student"] },
  { id: "leaves", icon: "✉️", label: "ছুটির আবেদন", roles: ["director", "admin", "teacher", "student"] },
  { id: "notices", icon: "📌", label: "নোটিশ বোর্ড", roles: ["director", "admin", "teacher", "student"] },
  { id: "manage", icon: "⚙️", label: "ম্যানেজ সেটিংস", roles: ["director"] },
];

export default function App() {
  const [user, setUser] = useState(null);
  const [db, setDb] = useState(seedDB);
  const [view, setView] = useState("overview");
  const [menu, setMenu] = useState(false);
  const [bell, setBell] = useState(false);
  const [, force] = useState(0);
  const refresh = () => force((x) => x + 1);
  const [livePopup, setLivePopup] = useState(null);
  const [autoJoinId, setAutoJoinId] = useState(null);
  const [receipt, setReceipt] = useState(null);
  // WhatsApp Business API অটো-সেন্ড: আউটবক্সে নতুন মেসেজ এলে ব্যাকএন্ডে পাঠায়
  useEffect(() => {
    const cfg = db.waConfig || {};
    if (!cfg.autoSend || !cfg.backendUrl) return;
    const pending = (db.waOutbox || []).filter((m) => !m.sent && !m.apiTried);
    if (!pending.length) return;
    setDb((d) => ({ ...d, waOutbox: d.waOutbox.map((m) => pending.some((p) => p.id === m.id) ? { ...m, apiTried: true, apiStatus: "sending" } : m) }));
    pending.forEach(async (m) => {
      try {
        const res = await fetch(cfg.backendUrl.replace(/\/+$/, "") + "/api/send-whatsapp", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ to: m.phone, text: m.text }),
        });
        setDb((d) => ({ ...d, waOutbox: d.waOutbox.map((x) => x.id === m.id ? { ...x, sent: res.ok, apiStatus: res.ok ? "sent" : "failed" } : x) }));
      } catch (err) {
        setDb((d) => ({ ...d, waOutbox: d.waOutbox.map((x) => x.id === m.id ? { ...x, apiStatus: "failed" } : x) }));
      }
    });
  }, [db.waOutbox, db.waConfig]);
  // ক্লাস শুরুর ৫ মিনিট আগে: ইন-অ্যাপ নোটিফিকেশন + অভিভাবকের WhatsApp মেসেজ অটো-প্রস্তুত
  useEffect(() => {
    const iv = setInterval(() => {
      const now = new Date();
      const cur = now.getHours() * 60 + now.getMinutes();
      setDb((d) => {
        let changed = false;
        let outbox = d.waOutbox || [];
        let notifs = d.notifications;
        const classes = d.classes.map((k) => {
          if (k.date !== todayISO() || k.status !== "upcoming" || k.notified5) return k;
          const [h, m] = k.time.split(":").map(Number);
          const st = h * 60 + m;
          if (cur < st - 5 || cur > st + 5) return k;
          changed = true;
          const c = courseById(COURSES, k.courseId);
          const studs = (k.studentIds && k.studentIds.length ? k.studentIds : c.studentIds) || [];
          outbox = [...waGuardianMsgs(k, c, "reminder"), ...outbox];
          notifs = [{ id: uid(), for: [k.teacherId || c.teacherId, ...studs, "admin1", "dir1"], text: `⏰ ${c.name} ক্লাস ${k.time}-এ শুরু হচ্ছে (৫ মিনিটের মধ্যে)! অভিভাবকের WhatsApp মেসেজ প্রস্তুত হয়ে আউটবক্সে গেছে।`, date: todayISO(), read: false }, ...notifs];
          return { ...k, notified5: true };
        });
        return changed ? { ...d, classes, waOutbox: outbox, notifications: notifs } : d;
      });
    }, 15000);
    return () => clearInterval(iv);
  }, []);
  const [confirmReq, setConfirmReq] = useState(null);
  const [toast, setToast] = useState(null);
  useEffect(() => {
    receiptHandler = (r) => setReceipt(r);
    confirmHandler = (c) => setConfirmReq(c);
    toastHandler = (msg) => { setToast(msg); setTimeout(() => setToast(null), 3200); };
    return () => { receiptHandler = null; confirmHandler = null; toastHandler = null; };
  }, []);
  const overlays = (
    <>
      {confirmReq && (
        <div style={{ position: "fixed", inset: 0, zIndex: 300, background: "rgba(18,63,40,.55)", display: "grid", placeItems: "center", padding: 16 }}>
          <div style={{ background: "#fff", borderRadius: 18, maxWidth: 380, width: "100%", padding: 24, textAlign: "center", fontFamily: "'Hind Siliguri', sans-serif" }}>
            <div style={{ fontSize: 34 }}>⚠️</div>
            <div style={{ fontSize: 14.5, fontWeight: 700, color: C.text, margin: "10px 0 18px", lineHeight: 1.6 }}>{confirmReq.message}</div>
            <div style={{ display: "flex", gap: 8 }}>
              <Btn kind="soft" style={{ flex: 1, justifyContent: "center" }} onClick={() => setConfirmReq(null)}>না, থাক</Btn>
              <Btn kind="danger" style={{ flex: 1, justifyContent: "center" }} onClick={() => { const fn = confirmReq.onYes; setConfirmReq(null); fn(); }}>হ্যাঁ, নিশ্চিত</Btn>
            </div>
          </div>
        </div>
      )}
      {toast && (
        <div style={{ position: "fixed", bottom: 22, left: "50%", transform: "translateX(-50%)", zIndex: 310, background: C.emeraldD, color: "#fff", padding: "11px 20px", borderRadius: 99, fontSize: 13.5, fontWeight: 700, boxShadow: "0 8px 24px rgba(0,0,0,.3)", maxWidth: "90vw", fontFamily: "'Hind Siliguri', sans-serif" }}>
          {toast}
        </div>
      )}
    </>
  );

  // স্টুডেন্ট পোর্টাল খুললেই শিডিউল অনুযায়ী চলমান ক্লাসের ফুল-পেজ পপআপ
  useEffect(() => {
    if (!user || user.role !== "student") { setLivePopup(null); return; }
    const now = new Date();
    const cur = now.getHours() * 60 + now.getMinutes();
    const k = db.classes.find((kk) => {
      if (kk.date !== todayISO() || kk.status === "done" || kk.status === "postponed") return false;
      if (!itemVisible(kk, user)) return false;
      const [h, m] = kk.time.split(":").map(Number);
      const st = h * 60 + m;
      return cur >= st - 15 && cur <= st + (kk.dur || 60); // শুরুর ১৫ মিনিট আগে থেকে শেষ পর্যন্ত "চলমান"
    });
    setLivePopup(k || null);
  }, [user]);

  if (!user) return (
    <div style={{ fontFamily: "'Hind Siliguri', 'Noto Sans Bengali', sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&display=swap');`}</style>
      {overlays}
      <Login onLogin={(u) => { setUser(u); setView("overview"); }} onAdmission={(a) => setDb((d) => ({ ...d, admissions: [{ id: uid(), ...a, age: +a.age || 0, date: todayISO(), status: "pending" }, ...d.admissions] }))} />
    </div>
  );

  const courses = myCourses(COURSES, user);
  const myNotifs = db.notifications.filter((n) => n.for.includes(user.id));
  const unread = myNotifs.filter((n) => !n.read).length;
  const markRead = () => setDb((d) => ({ ...d, notifications: d.notifications.map((n) => n.for.includes(user.id) ? { ...n, read: true } : n) }));
  const roleLabel = user.role === "director" ? "পরিচালক" : user.role === "admin" ? "এডমিন" : user.role === "teacher" ? "উস্তাদ/উস্তাদা" : "স্টুডেন্ট";
  const roleColor = user.role === "director" ? C.red : user.role === "admin" ? C.emerald : user.role === "teacher" ? C.gold : C.blue;
  const nav = NAV.filter((n) => n.roles.includes(user.role));
  const props = { db, setDb, user, courses, refresh };
  const joinFromPopup = (k) => { // জুম খোলে পপআপের অ্যাংকর লিংকে; এখানে টাইমার+ভিউ
    setAutoJoinId(k.id);           // হাজিরা টাইমার অটো চালু হবে
    setView("classes");
    setLivePopup(null);
  };

  return (
    <div style={{ fontFamily: "'Hind Siliguri', 'Noto Sans Bengali', sans-serif", background: C.cream, minHeight: "100vh", color: C.text }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap');
        *{box-sizing:border-box} button:hover{filter:brightness(1.06)} ::selection{background:${C.goldL}}
        @media(max-width:900px){.tqa-side{position:fixed;left:0;top:0;bottom:0;z-index:80;transform:translateX(${menu ? "0" : "-105%"});transition:transform .25s}}`}</style>

      {/* টপবার */}
      <div style={{ position: "sticky", top: 0, zIndex: 70, background: "#fff", borderBottom: `1px solid ${C.line}`, display: "flex", alignItems: "center", gap: 12, padding: "10px 16px" }}>
        <button onClick={() => setMenu(!menu)} style={{ border: "none", background: C.cream, borderRadius: 8, width: 36, height: 36, cursor: "pointer", fontSize: 16 }}>☰</button>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 0 }}>
          <span style={{ fontSize: 20 }}>🕌</span>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 14.5, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>তারবিয়াতুল কুরআন একাডেমি</div>
            <div style={{ fontSize: 11, color: C.muted }}>ম্যানেজমেন্ট সিস্টেম</div>
          </div>
        </div>
        <div style={{ position: "relative" }}>
          <button onClick={() => { setBell(!bell); if (!bell) markRead(); }} style={{ border: "none", background: C.cream, borderRadius: 8, width: 36, height: 36, cursor: "pointer", fontSize: 16, position: "relative" }}>
            🔔{unread > 0 && <span style={{ position: "absolute", top: -4, right: -4, background: C.red, color: "#fff", fontSize: 10, fontWeight: 800, borderRadius: 99, padding: "1px 6px" }}>{bn(unread)}</span>}
          </button>
          {bell && (
            <div style={{ position: "absolute", right: 0, top: 44, width: 300, background: "#fff", border: `1px solid ${C.line}`, borderRadius: 14, boxShadow: "0 12px 32px rgba(26,92,58,.15)", padding: 10, zIndex: 99 }}>
              <div style={{ fontWeight: 800, fontSize: 13, padding: "4px 6px" }}>🔔 নোটিফিকেশন</div>
              {myNotifs.length === 0 && <div style={{ padding: 10, fontSize: 12.5, color: C.muted }}>কোনো নোটিফিকেশন নেই</div>}
              {myNotifs.slice(0, 6).map((n) => <div key={n.id} style={{ padding: "8px 6px", borderTop: `1px solid ${C.line}`, fontSize: 12.5 }}>{n.text}<div style={{ fontSize: 10.5, color: C.muted }}>{fmtDate(n.date)}</div></div>)}
            </div>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ textAlign: "right", display: window.innerWidth < 480 ? "none" : "block" }}>
            <div style={{ fontSize: 12.5, fontWeight: 700, maxWidth: 140, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{user.name}</div>
            <span style={{ fontSize: 10.5, fontWeight: 800, color: roleColor }}>{roleLabel}</span>
          </div>
          <Btn sm kind="soft" onClick={() => setUser(null)}>লগ আউট</Btn>
        </div>
      </div>

      {overlays}
      {receipt && <ReceiptModal r={receipt} onClose={() => setReceipt(null)} db={db} setDb={setDb} sender={user} />}
      {livePopup && (() => { const c = courseById(COURSES, livePopup.courseId); return c.id ? <LiveClassPopup k={livePopup} course={c} onJoin={joinFromPopup} onLater={() => setLivePopup(null)} /> : null; })()}

      <div style={{ display: "flex", maxWidth: 1280, margin: "0 auto" }}>
        {/* সাইডবার */}
        <aside className="tqa-side" style={{ width: 232, flexShrink: 0, background: `linear-gradient(180deg, ${C.emeraldD}, ${C.emerald})`, minHeight: "calc(100vh - 57px)", padding: "16px 10px" }}>
          {nav.map((n) => (
            <button key={n.id} onClick={() => { setView(n.id); setMenu(false); }}
              style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", border: "none", cursor: "pointer", textAlign: "left", fontFamily: "inherit", fontSize: 13.5, fontWeight: 600, padding: "10px 14px", borderRadius: 12, marginBottom: 4,
                background: view === n.id ? "rgba(255,255,255,.14)" : "transparent", color: view === n.id ? C.goldL : "#d7e9de", borderLeft: view === n.id ? `3px solid ${C.gold}` : "3px solid transparent" }}>
              <span>{n.icon}</span> {n.label}
            </button>
          ))}
          <div style={{ marginTop: 18, padding: "12px 14px", borderRadius: 12, background: "rgba(255,255,255,.07)", color: "#cfe6d8", fontSize: 11.5, lineHeight: 1.6 }}>
            ﴾وَرَتِّلِ الْقُرْآنَ تَرْتِيلًا﴿<br />“আর কুরআন তিলাওয়াত করো ধীরে, সুস্পষ্টভাবে।” — মুযযাম্মিল ৪
          </div>
        </aside>
        {menu && <div onClick={() => setMenu(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.3)", zIndex: 75, display: window.innerWidth > 900 ? "none" : "block" }} />}

        {/* কনটেন্ট */}
        <main style={{ flex: 1, padding: "20px 18px", minWidth: 0 }}>
          {view === "overview" && <Overview {...props} goTo={setView} />}
          {view === "classes" && <ClassesView {...props} autoJoinId={autoJoinId} onAutoJoinConsumed={() => setAutoJoinId(null)} />}
          {view === "routine" && <RoutineView {...props} />}
          {view === "lectures" && <LecturePlan {...props} />}
          {view === "syllabus" && <SyllabusView {...props} />}
          {view === "attendance" && <AttendanceView {...props} />}
          {view === "assignments" && <AssignmentsView {...props} />}
          {view === "exams" && <ExamsView {...props} />}
          {view === "progress" && <ProgressView {...props} />}
          {view === "payments" && user.role === "student" && <StudentPaymentsView {...props} />}
          {view === "studentpayments" && isDir(user) && <DirectorPaymentsView {...props} />}
          {view === "waoutbox" && isAdm(user) && <WaOutboxView {...props} />}
          {view === "teacherreport" && user.role !== "student" && <TeacherReportView {...props} />}
          {view === "coursemgr" && isDir(user) && <CourseManagerView {...props} />}
          {view === "allstudents" && isAdm(user) && <AllStudentsView {...props} />}
          {view === "admissions" && isAdm(user) && <AdmissionsView {...props} />}
          {view === "manage" && isDir(user) && <ManageView {...props} />}
          {view === "accounts" && isDir(user) && <AccountsView {...props} />}
          {view === "forms" && isAdm(user) && <FormsView {...props} />}
          {view === "books" && <AcademicBooksView {...props} />}
          {view === "myreceipts" && <MyReceiptsView {...props} />}
          {view === "leaves" && <LeaveView {...props} />}
          {view === "notices" && <NoticesView {...props} />}
        </main>
      </div>
    </div>
  );
}
