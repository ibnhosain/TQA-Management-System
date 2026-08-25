import React, { useState, useEffect, useMemo, useRef } from "react";
import { api, login, logout, getMe, hasToken, downloadBackup, hasPendingWrites } from "./api";

/* ═══════════════════════════════════════════════════════════
   তারবিয়াতুল কুরআন একাডেমি — ম্যানেজমেন্ট সিস্টেম (TQA-MS)
   Roles: admin | teacher | student   —  Demo (in-memory) build
   ═══════════════════════════════════════════════════════════ */

const C = {
  emerald: "#1a5c3a",
  emeraldD: "#123f28",
  emeraldL: "#2a7a50",
  gold: "#c9962a",
  goldL: "#f0c355",
  cream: "#f4f6f4",
  text: "#1a1f2e",
  muted: "#6b7280",
  line: "#e5e9e5",
  red: "#c2410c",
  redBg: "#fef2ee",
  green: "#1a7a44",
  greenBg: "#eafaf1",
  blue: "#2e6fa3",
  blueBg: "#eef5fb",
  amberBg: "#fdf6e7",
};

const bn = (n) => String(n).replace(/\d/g, (d) => "০১২৩৪৫৬৭৮৯"[d]);
// toISOString() সবসময় UTC তারিখ দেয়, ব্যবহারকারীর লোকাল তারিখ নয় — মধ্যরাত থেকে
// ভোর ৬টার মধ্যে (বাংলাদেশ সময়, UTC+৬) এটা "আজ"-কে ভুলভাবে "গতকাল" ধরে ফেলত, ফলে
// ভোরের ক্লাস (যেমন ফজরের পর কুরআন ক্লাস) "আজকের ক্লাস"-এ দেখাত না — যদিও ব্যাকএন্ডে
// ক্লাসটা সঠিক তারিখেই তৈরি হয়েছিল। এখন ব্রাউজারের লোকাল তারিখ ব্যবহার করা হচ্ছে।
const todayISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
// লগইন করা ব্যবহারকারীর ভাষা — App-এর রেন্ডারের শুরুতেই সেট হয় (student → "en")।
// fmtDate ৫০+ জায়গায় ব্যবহৃত; প্রতিটি call site বদলানোর বদলে এখানেই একবার ঠিক করা হলো।
let CURRENT_LANG = "bn";
const MONTHS_BN_FULL = [
  "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
  "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর",
];
const MONTHS_EN_FULL = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const fmtDate = (iso) => {
  const d = new Date(iso + "T00:00:00");
  if (CURRENT_LANG === "en")
    return `${d.getDate()} ${MONTHS_EN_FULL[d.getMonth()]} ${d.getFullYear()}`;
  return `${bn(d.getDate())} ${MONTHS_BN_FULL[d.getMonth()]} ${bn(d.getFullYear())}`;
};
// দারস/টপিকের তারিখ — ছোট করে ২৩/০৮/২০২৬ ধাঁচে (শিক্ষার্থীর জন্য ইংরেজি অঙ্কে)
const fmtDMY = (iso) => {
  if (!iso) return "";
  const [y, m, d] = String(iso).split("-");
  if (!y || !m || !d) return String(iso);
  const t = `${d}/${m}/${y}`;
  return CURRENT_LANG === "en" ? t : bn(t);
};
// রিসিট/ভাউচার সবসময় ইংরেজিতে থাকে (যে বানাচ্ছেন তার ভাষা নির্বিশেষে) — তাই
// viewer-নির্ভর fmtDate() ব্যবহার না করে আলাদা এই হেল্পার
const fmtDateEn = (iso) => {
  const d = new Date(iso + "T00:00:00");
  return `${d.getDate()} ${MONTHS_EN_FULL[d.getMonth()]} ${d.getFullYear()}`;
};
// পেমেন্ট মাধ্যম রিসিটে সবসময় ইংরেজিতে দেখাতে — না মিললে মূল লেখাটাই ফেরত
const METHOD_EN = {
  "বিকাশ": "bKash",
  "নগদ": "Nagad",
  "ব্যাংক ট্রান্সফার": "Bank Transfer",
  "নগদ গ্রহণ (অফিস)": "Cash (Office)",
};
const methodEn = (m) => METHOD_EN[m] || m;
// CSV এক্সপোর্টের একটা সেল নিরাপদে তৈরি করে — শুধু quote-escape (CSV ফরম্যাটের
// জন্য) না, কোনো নাম/মেসেজ =, +, -, @ দিয়ে শুরু হলে Excel/Sheets সেটাকে ফর্মুলা
// হিসেবে চালানোর চেষ্টা করতে পারে (CSV/formula injection) — সামনে একটা অ্যাপস্ট্রফি
// বসিয়ে সেটা ঠেকানো হয় (Excel তখন টেক্সট হিসেবে দেখায়, ইন্ডাস্ট্রি-স্ট্যান্ডার্ড মিটিগেশন)
const csvCell = (v) => {
  let s = String(v ?? "");
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  return `"${s.replace(/"/g, '""')}"`;
};
const addDays = (n) => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
const MONTHS_BN = [
  "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
  "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর",
];
const monthLabelBn = (ym) => {  // "2026-07" → "জুলাই ২০২৬"
  const [y, m] = String(ym).split("-").map(Number);
  return `${MONTHS_BN[(m || 1) - 1]} ${bn(y || "")}`;
};
const uid = () => Math.random().toString(36).slice(2, 9);
const genPass = () => {
  // অক্ষর ও সংখ্যা মিশ্রিত পাসওয়ার্ড (যেমন: t7q2m9k4)
  const a = "abcdefghjkmnpqrstuvwxyz",
    d = "23456789";
  let s = "";
  for (let i = 0; i < 4; i++)
    s +=
      a[Math.floor(Math.random() * a.length)] +
      d[Math.floor(Math.random() * d.length)];
  return s;
};

/* 🧾 পেমেন্ট রিসিট / বেতন ভাউচার — ইন-অ্যাপ প্রিভিউ মডাল থেকে প্রিন্ট/PDF (স্যান্ডবক্সে window.open ব্লক থাকে) */
const receiptHTML = (
  p,
  person,
  kind,
  no,
) => `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>${kind} — TQA-${no}</title>
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
<div class="h"><div class="ar">تربية القرآن</div><h1>Tarbiyatul Quran Academy</h1><div class="s">tarbiyatulquran.org · WhatsApp: +880 140 249 9027</div></div>
<div class="k">${kind}</div>
<div class="b">
<div class="r"><span>Receipt No.</span><b>TQA-${no}</b></div>
<div class="r"><span>${kind.includes("বেতন") ? "Teacher" : "Name"}</span><b>${person.name || ""}</b></div>
<div class="r"><span>Month / Description</span><b>${p.month || "—"}</b></div>
<div class="r"><span>Payment Date</span><b>${p.date || ""}</b></div>
<div class="r"><span>Method</span><b>${p.method || "—"}</b></div>
<div class="r"><span>Status</span><b>${p.status === "pending" ? "Awaiting Verification" : "Paid ✔"}</b></div>
<div class="amt"><div class="t">Amount</div><div class="n">${p.currency || "৳"} ${Number(p.amount || 0).toLocaleString("en")}</div></div>
<div class="sg"><div>Recipient's Signature</div><div>Director / Accountant</div></div>
</div>
<div class="f">This is a computer-generated receipt — JazakAllahu Khairan</div>
</div>
<button class="pr" onclick="window.print()">🖨️ Print / Save as PDF</button>
</body></html>`;

/* 📜 কোর্স সিলেবাস — প্রিন্টযোগ্য ডকুমেন্ট (PDF-এর মতো পাশাপাশি ৫ কলাম, যে কেউ প্রিন্ট/PDF করতে পারবে) */
const SYL_CATS_PRINT = [
  { key: "memorized_surah", label: "মুখস্থ সূরা" },
  { key: "memorized_hadith", label: "মুখস্থ হাদিস" },
  { key: "qirat", label: "কিরাত" },
  { key: "dua_masala", label: "দুআ/মাসআলা" },
  { key: "moral_story", label: "নৈতিক শিক্ষা/হাদিসের গল্প" },
];
/* পরিচালকের নিজের হাতে লেখা সিলেবাস টেবিলের প্রিন্ট/PDF — চেহারা আগের
   syllabusHTML-এর হুবহু একই (একাডেমি হেডার, সোনালি ব্যানার, মেটা, টেবিল),
   শুধু ঘরগুলো এখন মুক্ত লেখা। পুরনো syllabusHTML মোছা হয়নি — অন্য কোথাও
   ব্যবহার হলে সেটা আগের মতোই কাজ করবে। */
const sheetHTML = (courseName, books, headers, rows, en) => {
  const esc = (x) =>
    String(x == null ? "" : x).replace(
      /[&<>]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c],
    );
  const cols = headers.length || 1;
  const w = (100 / cols).toFixed(4);
  const th = headers.map((h) => `<th style="width:${w}%">${esc(h)}</th>`).join("");
  const tr = rows.length
    ? rows
        .map(
          (r) =>
            `<tr>${headers
              .map((_, i) => `<td>${esc(r[i]).replace(/\n/g, "<br>")}</td>`)
              .join("")}</tr>`,
        )
        .join("")
    : `<tr><td class="em" colspan="${cols}">—</td></tr>`;
  return `<!DOCTYPE html><html lang="bn"><head><meta charset="utf-8"><title>কোর্স সিলেবাস — ${esc(courseName)}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700;800&display=swap');
*{box-sizing:border-box}
body{font-family:'Hind Siliguri',sans-serif;margin:0;padding:26px;background:#f4f6f4;color:#1a1f2e}
.v{max-width:1000px;margin:0 auto;background:#fff;border:2px solid #1a5c3a;border-radius:14px;overflow:hidden}
.h{background:linear-gradient(135deg,#123f28,#1a5c3a);color:#fff;padding:18px 24px;text-align:center}
.h .ar{color:#f0c355;font-size:13px;letter-spacing:3px}.h h1{margin:4px 0 2px;font-size:21px}.h .s{font-size:11.5px;color:#cfe6d8}
.k{background:#c9962a;color:#fff;text-align:center;font-weight:800;padding:12px 8px;font-size:26px;line-height:1.25;letter-spacing:1px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.cn{text-align:center;font-size:20px;font-weight:800;color:#1a5c3a;padding:14px 24px 4px;line-height:1.35}
.bw{padding:6px 24px 12px;border-bottom:1.5px solid #e5e9e5}
.bt{text-align:center;font-weight:800;font-size:13px;color:#1a5c3a;margin-bottom:6px}
.bl{margin:0;padding:0;list-style:none;columns:240px;column-gap:20px;font-size:12.5px;line-height:1.5}
.bl li{break-inside:avoid;margin-bottom:2px}
.bl .n{color:#c9962a;font-weight:800}
table{width:100%;border-collapse:collapse;table-layout:fixed}
th{background:#123f28;color:#fff;font-weight:800;font-size:13px;text-align:center;padding:9px 6px;border:1px solid #123f28;border-bottom:2px solid #c9962a;-webkit-print-color-adjust:exact;print-color-adjust:exact}
td{border:1px solid #1a5c3a;vertical-align:top;padding:9px 10px;font-size:12.5px;line-height:1.6;word-wrap:break-word}
td.em{text-align:center;color:#9ca3af}
.f{text-align:center;font-size:11px;color:#9ca3af;padding:10px;border-top:1px solid #eef0ee}
@media print{body{background:#fff;padding:0}.v{border:none;border-radius:0;max-width:100%}}
</style></head><body><div class="v">
<div class="h"><div class="ar">تربية القرآن</div><h1>তারবিয়াতুল কুরআন একাডেমী</h1>
<div class="s">tarbiyatulquran.org · WhatsApp: +880 140 249 9027</div></div>
<div class="k">কোর্স সিলেবাস</div>
<div class="cn">${en ? "Course:" : "কোর্স:"} ${esc(courseName)}</div>${
    (books || []).length
      ? `<div class="bw"><div class="bt">${
          en ? "Books selected for this course" : "কোর্সের জন্য নির্বাচিত বইসমূহ"
        }</div><ol class="bl">${books
          .map((b, i) => `<li><span class="n">${i + 1}.</span> ${esc(b)}</li>`)
          .join("")}</ol></div>`
      : ""
  }
<table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>
<div class="f">তারবিয়াতুল কুরআন একাডেমী · tarbiyatulquran.org</div>
</div></body></html>`;
};

const syllabusHTML = (courseName, booksLine, itemsByCat) => {
  const esc = (s) =>
    String(s == null ? "" : s).replace(
      /[&<>]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c],
    );
  const col = (cat) => {
    const items = itemsByCat[cat.key] || [];
    const lis = items.length
      ? items
          .map((it) => {
            const bk =
              it.book && it.book !== "অন্যান্য"
                ? `<span class="bk">${esc(it.book)} — </span>`
                : "";
            const pl =
              (it.pages ? ` · পৃষ্ঠা: ${esc(it.pages)}` : "") +
              (it.lines ? ` · লাইন: ${esc(it.lines)}` : "");
            const note = it.note
              ? `<div class="nt">💬 ${esc(it.note)}</div>`
              : "";
            return `<li>${bk}${esc(it.lesson)}${pl ? `<span class="pl">${pl}</span>` : ""}${note}</li>`;
          })
          .join("")
      : `<li class="em">—</li>`;
    return `<td><div class="ch">${cat.label}</div><ol>${lis}</ol></td>`;
  };
  return `<!DOCTYPE html><html lang="bn"><head><meta charset="utf-8"><title>কোর্স সিলেবাস — ${esc(courseName)}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700;800&display=swap');
*{box-sizing:border-box}
body{font-family:'Hind Siliguri',sans-serif;margin:0;padding:26px;background:#f4f6f4;color:#1a1f2e}
.v{max-width:1000px;margin:0 auto;background:#fff;border:2px solid #1a5c3a;border-radius:14px;overflow:hidden}
.h{background:linear-gradient(135deg,#123f28,#1a5c3a);color:#fff;padding:18px 24px;text-align:center}
.h .ar{color:#f0c355;font-size:13px;letter-spacing:3px}.h h1{margin:4px 0 2px;font-size:21px}.h .s{font-size:11.5px;color:#cfe6d8}
.k{background:#c9962a;color:#fff;text-align:center;font-weight:800;padding:8px;font-size:16px;letter-spacing:1px}
.meta{display:flex;gap:18px;flex-wrap:wrap;padding:12px 24px;border-bottom:1.5px solid #e5e9e5;font-size:13.5px}
.meta b{color:#1a5c3a}
table{width:100%;border-collapse:collapse;table-layout:fixed}
td{border:1px solid #e5e9e5;vertical-align:top;padding:0;width:20%}
.ch{background:#eafaf1;color:#1a5c3a;font-weight:800;font-size:13px;text-align:center;padding:9px 6px;border-bottom:1.5px solid #1a7a44}
ol{margin:0;padding:10px 10px 12px 26px}
li{font-size:12.5px;margin-bottom:7px;line-height:1.5}
li.em{list-style:none;margin-left:-16px;text-align:center;color:#9ca3af}
.bk{color:#1a5c3a;font-weight:700}.pl{color:#6b7280;font-size:11px}.nt{color:#6b7280;font-size:11px}
.f{text-align:center;font-size:11px;color:#9ca3af;padding:10px;border-top:1px solid #eef0ee}
.pr{display:block;margin:18px auto 0;background:#1a5c3a;color:#fff;border:none;padding:11px 26px;border-radius:10px;font-family:inherit;font-size:14px;font-weight:700;cursor:pointer}
@media print{.pr{display:none}body{background:#fff;padding:0}.v{border:none;border-radius:0;max-width:100%}}
</style></head><body>
<div class="v">
<div class="h"><div class="ar">تربية القرآن</div><h1>তারবিয়াতুল কুরআন একাডেমী</h1><div class="s">tarbiyatulquran.org · WhatsApp: +880 140 249 9027</div></div>
<div class="k">কোর্স সিলেবাস</div>
<div class="meta"><div><b>কোর্স:</b> ${esc(courseName)}</div>${booksLine ? `<div><b>বই:</b> ${esc(booksLine)}</div>` : ""}<div><b>তারিখ:</b> ${fmtDate(todayISO())}</div></div>
<table><tr>${SYL_CATS_PRINT.map(col).join("")}</tr></table>
<div class="f">এটি কম্পিউটারে তৈরি কোর্স সিলেবাস — তারবিয়াতুল কুরআন একাডেমী</div>
</div>
<button class="pr" onclick="window.print()">🖨️ প্রিন্ট / PDF সেভ করুন</button>
</body></html>`;
};

/* প্রিন্ট ডকুমেন্ট খোলা — নতুন ট্যাবে; পপআপ ব্লক হলে HTML ফাইল ডাউনলোড (fallback) */
const openPrintDoc = (html, filename) => {
  try {
    const w = window.open("", "_blank");
    if (w && w.document) {
      w.document.open();
      w.document.write(html);
      w.document.close();
      return;
    }
  } catch (e) {
    /* ignore → fallback */
  }
  try {
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  } catch (e) {
    notice("প্রিন্ট খুলতে সমস্যা হয়েছে।");
  }
};

/* স্যান্ডবক্সে window.confirm/alert ব্লক থাকে — তাই নিজস্ব কনফার্ম-মডাল ও টোস্ট */
let confirmHandler = null;
/* opts (ঐচ্ছিক) = { yes, no } — কোনো কোনো প্রশ্নে "হ্যাঁ, নিশ্চিত / না, থাক"
   যথেষ্ট স্পষ্ট নয়, সেখানে নিজের মতো লেখা বসানো যায়। না দিলে আগের লেখাই
   থাকে, তাই পুরনো সব কল অবিকল আগের মতোই চলে। */
const askConfirm = (message, onYes, opts) => {
  confirmHandler
    ? confirmHandler({ message, onYes, ...(opts || {}) })
    : onYes();
};
let toastHandler = null;
const notice = (msg) => {
  if (toastHandler) toastHandler(msg);
  else
    try {
      window.alert(msg);
    } catch (e) {}
};

/* খোলা ফর্মের অসমাপ্ত লেখা localStorage-এ রেখে দিই — মোবাইল ব্রাউজার পেইজটাকে
   ব্যাকগ্রাউন্ডে ফেলে দিয়ে পরে রিলোড করলেও যেন টাইপ করা কিছু হারিয়ে না যায়।
   useState-এর হুবহু বিকল্প, শুধু মানটা অতিরিক্তভাবে সংরক্ষিত থাকে।
   • লগআউট করলেই সব ড্রাফট মুছে যায় (api.js → logout) — তাই একজনের লেখা
     আরেকজন দেখবেন না।
   • ফাইল/ছবি ধরে রাখা ফর্মে এটা ব্যবহার করা যাবে না — File JSON হয় না। */
/* ট্যাব লুকানো থাকলে (ব্যবহারকারী অন্য অ্যাপে/ট্যাবে গেছেন) সার্ভারে বারবার
   খোঁজ নেওয়া থামিয়ে রাখি — নিষ্ক্রিয় সময়ের ডাটাবেস-খরচ প্রায় পুরোটাই বেঁচে
   যায়। ট্যাবে ফিরে এলেই সাথে সাথে একবার চালিয়ে সব হালনাগাদ করে নেওয়া হয়,
   তাই ব্যবহারকারীর কাছে কোনো পার্থক্য চোখে পড়ে না — যা দেখার কথা তা দেখার
   মুহূর্তেই তাজা হয়ে যায়।
   ⚠️ ক্লাস চলাকালীন প্রেজেন্স-পোলে (LiveClassPanel) এটা ব্যবহার করা যাবে না —
   জুমে থাকার সময় পোর্টালের ট্যাবটাই লুকানো থাকে, ওখানে থামিয়ে দিলে
   "উস্তাদ ঢুকেছেন" কখনোই ধরা পড়ত না। */
const visiblePoll = (fn, ms) => {
  const tick = () => {
    if (!document.hidden) fn();
  };
  tick();
  const iv = setInterval(tick, ms);
  const onVisible = () => {
    if (!document.hidden) fn();
  };
  document.addEventListener("visibilitychange", onVisible);
  return () => {
    clearInterval(iv);
    document.removeEventListener("visibilitychange", onVisible);
  };
};

const DRAFT_PREFIX = "tqa_draft_";
function usePersistedState(key, initial) {
  const k = DRAFT_PREFIX + key;
  const [v, setV] = useState(() => {
    try {
      const raw = window.localStorage.getItem(k);
      if (raw != null) return JSON.parse(raw);
    } catch (e) {
      /* নষ্ট বা অপঠনযোগ্য ড্রাফট — উপেক্ষা করে স্বাভাবিকভাবেই শুরু করি */
    }
    return typeof initial === "function" ? initial() : initial;
  });
  useEffect(() => {
    try {
      window.localStorage.setItem(k, JSON.stringify(v));
    } catch (e) {
      /* জায়গা শেষ ইত্যাদি — উপেক্ষা, ফর্ম আগের মতোই চলবে */
    }
  }, [k, v]);
  return [v, setV];
}

let receiptHandler = null;
const printReceipt = (p, person, kind) => {
  if (receiptHandler) receiptHandler({ p, person, kind });
};

function ReceiptModal({ r, onClose, db, setDb, sender }) {
  const [ask, setAsk] = useState(false);
  const [done, setDone] = useState(false);
  if (!r) return null;
  const { p, person, kind } = r;
  // স্টুডেন্টের ফি রিসিট আর পোর্টালে "সেন্ড" করা হয় না — স্টুডেন্ট পোর্টালে শুধু
  // পেমেন্ট হিস্টরি (কোন মাস পরিশোধ, কোনটা বাকি) দেখানো হবে, আলাদা রিসিট ফাইল না।
  // পরিচালক/এডমিন এখন শুধু ডাউনলোড করে নিজে WhatsApp-এ পাঠাবেন।
  const canSend = !!person.id && !p.noSend && kind !== "ফি পরিশোধ রিসিট";
  // PNG হিসেবে সেইভ — HTML ফাইলের বদলে, যাতে WhatsApp-এ সরাসরি ছবি হিসেবে সহজে পাঠানো যায়
  // (html2canvas শুধু এই মুহূর্তেই ডাউনলোড হয় — dynamic import, তাই মূল বান্ডেলের সাইজ বাড়ে না)
  const doDownload = async () => {
    const no2 = (p.id || uid()).slice(0, 6).toUpperCase();
    const node = document.getElementById("tqa-receipt");
    try {
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(node, {
        scale: 2,
        backgroundColor: "#ffffff",
      });
      canvas.toBlob((blob) => {
        if (!blob) {
          notice("রিসিট ছবি তৈরি করতে ব্যর্থ হয়েছে।");
          return;
        }
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `TQA-receipt-${no2}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      }, "image/png");
    } catch {
      notice("রিসিট ছবি তৈরি করতে ব্যর্থ হয়েছে — আবার চেষ্টা করুন।");
    }
    setAsk(false);
  };
  // স্টুডেন্টের/উস্তাদের ফি রিসিট বা বেতন ভাউচার পোর্টালে না পাঠিয়ে সরাসরি
  // WhatsApp বা ইমেইলে পাঠানোর অপশন — ছবি প্রথমে ডাউনলোড হবে, তারপর সেই
  // ব্যক্তির WhatsApp চ্যাট/ইমেইল কম্পোজ খুলে যাবে (নিরাপত্তা-সীমাবদ্ধতার কারণে
  // ছবিটা সয়ংক্রিয়ভাবে সংযুক্ত করা যায় না — ডাউনলোড হওয়া ছবিটা একবার নিজে
  // সংযুক্ত করে দিতে হবে)
  const isReceiptKind =
    kind === "ফি পরিশোধ রিসিট" || kind === "বেতন পরিশোধ ভাউচার";
  const canWhatsApp = isReceiptKind && !!person.phone;
  const canEmail = isReceiptKind && !!person.email;
  const confirmMessage = () => {
    const hadith =
      "بارك الله لك في أهلك ومالك، إنما جزاء السلف الوفاء والحمد\n" +
      '"May Allah bless your family and your wealth. Indeed, the reward for fulfilling an obligation is faithfulness and gratitude." — Hadith';
    return kind === "বেতন পরিশোধ ভাউচার"
      ? `Assalamu Alaikum Warahmatullahi Wabarakatuh,\n\nDear ${person.name || "Ustadh/Ustadha"},\n\nThis is to confirm that your salary payment for "${p.month || "—"}" has been completed. Please find the voucher attached below.\n\n${hadith}\n\nJazakAllahu Khairan for your dedication and service.\n— Tarbiyatul Quran Academy`
      : `Assalamu Alaikum Warahmatullahi Wabarakatuh,\n\nDear Guardian,\n\nWe are pleased to confirm that ${person.name || "your child"}'s fee payment for "${p.month || "—"}" has been received and verified. Please find the receipt attached below.\n\n${hadith}\n\nJazakAllahu Khairan for your continued trust and support.\n— Tarbiyatul Quran Academy`;
  };
  const doWhatsApp = () => {
    doDownload();
    const cleanPhone = String(person.phone).replace(/[^\d]/g, "");
    window.open(
      `https://wa.me/${cleanPhone}?text=${encodeURIComponent(confirmMessage())}`,
      "_blank",
    );
  };
  const doEmail = () => {
    doDownload();
    const subject =
      kind === "বেতন পরিশোধ ভাউচার"
        ? `Salary Voucher — ${p.month || ""}`
        : `Fee Payment Receipt — ${p.month || ""}`;
    window.open(
      `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(person.email)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(confirmMessage())}`,
      "_blank",
    );
  };
  const doSend = async () => {
    if (!canSend) return;
    try {
      await api.sendReceipt({
        to_user: person.id,
        kind,
        month_label: p.month,
        amount: p.amount,
        method: p.method,
      });
    } catch (e) {
      notice(
        "রিসিট পাঠাতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
      return;
    }
    setAsk(false);
    setDone(true);
  };
  const no = (p.id || uid()).slice(0, 6).toUpperCase();
  const row = (k, v) => (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: 10,
        padding: "9px 2px",
        borderBottom: "1px dashed #e5e9e5",
        fontSize: 14,
      }}
    >
      <span style={{ color: C.muted }}>{k}</span>
      <b style={{ textAlign: "right" }}>{v}</b>
    </div>
  );
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 150,
        background: "rgba(18,63,40,.55)",
        display: "grid",
        placeItems: "center",
        padding: 14,
        overflowY: "auto",
      }}
      className="tqa-receipt-overlay"
    >
      <div style={{ width: "100%", maxWidth: 480 }}>
        <div
          id="tqa-receipt"
          style={{
            background: "#fff",
            border: `2px solid ${C.emerald}`,
            borderRadius: 16,
            overflow: "hidden",
            fontFamily: "'Hind Siliguri', sans-serif",
          }}
        >
          <div
            style={{
              background: `linear-gradient(135deg, ${C.emeraldD}, ${C.emerald})`,
              color: "#fff",
              padding: "20px 24px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                color: C.goldL,
                fontSize: 13,
                letterSpacing: 3,
                fontFamily: "'Amiri', serif",
              }}
            >
              تربية القرآن
            </div>
            <div style={{ fontSize: 19, fontWeight: 800, margin: "4px 0 2px" }}>
              তারবিয়াতুল কুরআন একাডেমি
            </div>
            <div style={{ fontSize: 11.5, color: "#cfe6d8" }}>
              tarbiyatulquran.org · WhatsApp: +880 140 249 9027
            </div>
          </div>
          <div
            style={{
              background: C.gold,
              color: "#fff",
              textAlign: "center",
              fontWeight: 800,
              padding: "7px 4px",
              fontSize: 14.5,
              letterSpacing: 1,
            }}
          >
            {kind}
          </div>
          <div style={{ padding: "20px 26px" }}>
            {row("Receipt No.", `TQA-${no}`)}
            {row(
              kind.includes("বেতন") ? "Teacher" : "Name",
              person.name || "",
            )}
            {row("Month / Description", p.month || "—")}
            {row("Payment Date", p.date || "")}
            {row("Method", p.method || "—")}
            {row(
              "Status",
              p.status === "pending" ? "Awaiting Verification ⏳" : "Paid ✔",
            )}
            <div
              style={{
                background: C.greenBg,
                border: `1.5px solid ${C.green}`,
                borderRadius: 12,
                textAlign: "center",
                padding: 14,
                margin: "16px 0",
              }}
            >
              <div style={{ fontSize: 12, color: C.muted }}>Amount</div>
              <div style={{ fontSize: 26, fontWeight: 800, color: C.emerald }}>
                {p.currency || "৳"} {Number(p.amount || 0).toLocaleString("en")}
              </div>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 38,
                fontSize: 12,
                color: C.muted,
              }}
            >
              <div
                style={{
                  borderTop: "1.5px dashed #9ca3af",
                  paddingTop: 6,
                  width: 140,
                  textAlign: "center",
                }}
              >
                Recipient's Signature
              </div>
              <div
                style={{
                  borderTop: "1.5px dashed #9ca3af",
                  paddingTop: 6,
                  width: 140,
                  textAlign: "center",
                }}
              >
                Director / Accountant
              </div>
            </div>
          </div>
          <div
            style={{
              textAlign: "center",
              fontSize: 11,
              color: "#9ca3af",
              padding: "10px 6px",
              borderTop: `1px solid ${C.line}`,
            }}
          >
            This is a computer-generated receipt — JazakAllahu Khairan
          </div>
        </div>
        <div
          className="tqa-receipt-actions"
          style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}
        >
          <Btn
            style={{ flex: 1.2, justifyContent: "center" }}
            onClick={() => (canSend ? setAsk(true) : doDownload())}
          >
            {canSend ? "⬇️ ডাউনলোড / সেন্ড" : "⬇️ ডাউনলোড (PNG)"}
          </Btn>
          {canWhatsApp && (
            <Btn
              kind="gold"
              style={{ flex: 1.2, justifyContent: "center" }}
              onClick={doWhatsApp}
            >
              📲 WhatsApp-এ পাঠান
            </Btn>
          )}
          {canEmail && (
            <Btn
              kind="gold"
              style={{ flex: 1.2, justifyContent: "center" }}
              onClick={doEmail}
            >
              📧 ইমেইলে পাঠান
            </Btn>
          )}
          <Btn
            kind="soft"
            style={{ flex: 1, justifyContent: "center" }}
            onClick={onClose}
          >
            বন্ধ করুন
          </Btn>
        </div>
        <div
          style={{
            textAlign: "center",
            fontSize: 11.5,
            color: "#d7e9de",
            marginTop: 8,
          }}
        >
          ⬇️ ডাউনলোড করলে রিসিটটি ছবি (PNG) হিসেবে সেভ হবে — সরাসরি WhatsApp-এ
          পাঠানো যাবে
        </div>
      </div>
      {ask && (
        <div
          onClick={() => setAsk(false)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 170,
            background: "rgba(18,63,40,.6)",
            display: "grid",
            placeItems: "center",
            padding: 16,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#fff",
              borderRadius: 18,
              maxWidth: 360,
              width: "100%",
              padding: 24,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 34 }}>🧾</div>
            <div style={{ fontWeight: 800, fontSize: 16, margin: "6px 0 4px" }}>
              কী করতে চান?
            </div>
            <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 16 }}>
              ডাউনলোড করবেন, নাকি{" "}
              {person.name ? <b>{person.name}</b> : "প্রাপকের"}-এর পোর্টালে
              পাঠাবেন?
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              <Btn style={{ justifyContent: "center" }} onClick={doDownload}>
                ⬇️ ডাউনলোড — ছবি (PNG) হিসেবে সেভ হবে
              </Btn>
              <Btn
                kind="gold"
                style={{ justifyContent: "center", opacity: canSend ? 1 : 0.5 }}
                onClick={doSend}
              >
                📨 সেন্ড — তার পোর্টালের "ভাউচার/রিসিট"-এ যোগ হবে
              </Btn>
              {!canSend && (
                <div style={{ fontSize: 11.5, color: C.red }}>
                  {p.noSend
                    ? "এই রিসিটটি ইতিমধ্যে পোর্টালে আছে"
                    : "নিবন্ধিত ব্যবহারকারী নয় — কেবল ডাউনলোড করা যাবে"}
                </div>
              )}
              <Btn
                kind="soft"
                sm
                style={{ justifyContent: "center" }}
                onClick={() => setAsk(false)}
              >
                বাতিল
              </Btn>
            </div>
          </div>
        </div>
      )}
      {done && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 170,
            background: "rgba(18,63,40,.6)",
            display: "grid",
            placeItems: "center",
            padding: 16,
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 18,
              maxWidth: 360,
              width: "100%",
              padding: 26,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 40 }}>✅</div>
            <div style={{ fontWeight: 800, fontSize: 16, margin: "8px 0 4px" }}>
              সেন্ড হয়েছে!
            </div>
            <div style={{ fontSize: 13, color: C.muted, marginBottom: 14 }}>
              রিসিটটি <b>{person.name}</b>-এর পোর্টালের "🧾 ভাউচার/রিসিট" মেনুতে
              যোগ হয়েছে এবং নোটিফিকেশন পাঠানো হয়েছে।
            </div>
            <Btn
              style={{ width: "100%", justifyContent: "center" }}
              onClick={() => {
                setDone(false);
                onClose();
              }}
            >
              আলহামদুলিল্লাহ, ঠিক আছে
            </Btn>
          </div>
        </div>
      )}
      <style>{LESSON_BODY_CSS}</style>
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
const USERS = []; // ডেমো ডাটা সরানো — সব কিছু API থেকে আসে

const COURSES = [];

const seedDB = () => ({
  classes: [],
  attendance: [],
  assignments: [],
  exams: [],
  feePayments: [],
  teacherPayments: [],
  dueMonths: {},
  admissions: [],
  permissions: { fixCross: {} },
  ratings: [],
  forms: [],
  books: [],
  notices: [],
  makeups: [],
  syllabus: [],
  academicBooks: [],
  waOutbox: [],
  waConfig: { backendUrl: "", autoSend: false },
  sentReceipts: [],
  routine: [],
  leaves: [],
  notifications: [],
});
/* ─────────────── UI primitives ─────────────── */
const S = {
  card: {
    background: "#fff",
    border: `1px solid ${C.line}`,
    borderRadius: 16,
    padding: 20,
    boxShadow: "0 2px 8px rgba(26,92,58,.06)",
  },
  h2: { fontSize: 20, fontWeight: 700, color: C.text, margin: 0 },
  sub: { fontSize: 13, color: C.muted },
  input: {
    width: "100%",
    padding: "10px 12px",
    border: `1.5px solid ${C.line}`,
    borderRadius: 10,
    fontSize: 14,
    fontFamily: "inherit",
    outline: "none",
    background: "#fff",
    color: C.text,
    boxSizing: "border-box",
  },
  label: {
    fontSize: 12.5,
    fontWeight: 600,
    color: C.muted,
    display: "block",
    marginBottom: 5,
  },
};

const Btn = ({ children, kind = "primary", sm, style, ...p }) => {
  const base = {
    border: "none",
    cursor: "pointer",
    fontFamily: "inherit",
    fontWeight: 600,
    borderRadius: 10,
    fontSize: sm ? 12.5 : 14,
    padding: sm ? "6px 12px" : "10px 18px",
    transition: "all .15s",
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    // হালকা ছায়া — বাটনটা পাতার সাথে মিশে না গিয়ে একটু উঁচু দেখায়, ফলে
    // "এটা চাপা যায়" ব্যাপারটা এক নজরেই বোঝা যায়
    boxShadow: "0 1px 2px rgba(18,63,40,.18)",
  };
  /* ⚠️ আগে danger/soft/ghost — তিনটিরই পটভূমি এত হালকা ছিল যে সাদা কার্ডের
     উপর সেগুলো বাটন বলে চেনাই যেত না, নিছক লেখা মনে হতো। বিশেষ করে কনফার্ম
     পপআপে ("জুম হোস্ট অ্যাকাউন্ট" সতর্কতা ইত্যাদি) "না, থাক" ও "হ্যাঁ, নিশ্চিত"
     দুটোই ফ্যাকাসে দেখাত। এখন প্রতিটিরই স্পষ্ট রং ও কিনারা আছে। */
  const kinds = {
    primary: { background: C.emerald, color: "#fff" },
    gold: { background: C.gold, color: "#fff" },
    ghost: {
      background: "#fff",
      color: C.emeraldD,
      border: `2px solid ${C.emerald}`,
    },
    // ধ্বংসাত্মক কাজ — ভরাট লাল, সাদা লেখা। ভুল করে চাপার আগেই চোখে পড়ে।
    danger: {
      background: C.red,
      color: "#fff",
      border: `1.5px solid #9a330a`,
    },
    // পাশের/দ্বিতীয় পছন্দের বাটন — ভরাট ধূসর-সবুজ, স্পষ্ট কিনারা
    soft: {
      background: "#dde5e0",
      color: C.emeraldD,
      border: `1.5px solid #a9bcb0`,
    },
  };
  return (
    <button style={{ ...base, ...kinds[kind], ...style }} {...p}>
      {children}
    </button>
  );
};

const Tag = ({ children, color = C.emerald, bg = C.greenBg }) => (
  <span
    style={{
      background: bg,
      color,
      fontSize: 11.5,
      fontWeight: 700,
      padding: "3px 10px",
      borderRadius: 99,
      whiteSpace: "nowrap",
    }}
  >
    {children}
  </span>
);

const Stat = ({ icon, label, value, accent = C.emerald, note }) => (
  <div
    style={{
      ...S.card,
      display: "flex",
      gap: 14,
      alignItems: "center",
      padding: 16,
    }}
  >
    <div
      style={{
        width: 46,
        height: 46,
        borderRadius: 12,
        background: accent + "14",
        display: "grid",
        placeItems: "center",
        fontSize: 22,
      }}
    >
      {icon}
    </div>
    <div style={{ minWidth: 0 }}>
      <div style={{ fontSize: 12, color: C.muted, fontWeight: 600 }}>
        {label}
      </div>
      <div
        style={{
          fontSize: 21,
          fontWeight: 800,
          color: C.text,
          lineHeight: 1.2,
        }}
      >
        {value}
      </div>
      {note && <div style={{ fontSize: 11.5, color: C.muted }}>{note}</div>}
    </div>
  </div>
);

const Modal = ({ title, onClose, children, wide }) => (
  <div
    onClick={onClose}
    style={{
      position: "fixed",
      inset: 0,
      background: "rgba(18,63,40,.45)",
      zIndex: 90,
      display: "grid",
      placeItems: "center",
      padding: 16,
    }}
  >
    <div
      onClick={(e) => e.stopPropagation()}
      style={{
        background: "#fff",
        borderRadius: 18,
        width: "100%",
        maxWidth: wide ? 720 : 480,
        maxHeight: "88vh",
        overflowY: "auto",
        padding: 22,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 14,
        }}
      >
        <h3 style={{ ...S.h2, fontSize: 17 }}>{title}</h3>
        <button
          onClick={onClose}
          style={{
            border: "none",
            background: C.cream,
            borderRadius: 8,
            width: 30,
            height: 30,
            cursor: "pointer",
            fontSize: 15,
          }}
        >
          ✕
        </button>
      </div>
      {children}
    </div>
  </div>
);

// loading=true দিলে ডেটা আসার আগে "কোনো তথ্য নেই" না দেখিয়ে "লোড হচ্ছে…" দেখায় —
// নইলে প্রতিবার পেজ খোলার সময় এক ঝলক ভুল করে "কিছু নেই" দেখাত
const Table = ({ head, rows, empty = "কোনো তথ্য নেই", loading = false }) => (
  <div
    style={{
      overflowX: "auto",
      borderRadius: 12,
      border: `1px solid ${C.line}`,
    }}
  >
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
        fontSize: 13.5,
        minWidth: 540,
      }}
    >
      <thead>
        <tr>
          {head.map((h, i) => (
            <th
              key={i}
              style={{
                textAlign: "left",
                padding: "10px 12px",
                background: C.cream,
                color: C.muted,
                fontSize: 12,
                fontWeight: 700,
                whiteSpace: "nowrap",
              }}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td
              colSpan={head.length}
              style={{ padding: 18, textAlign: "center", color: C.muted }}
            >
              {loading ? "লোড হচ্ছে…" : empty}
            </td>
          </tr>
        )}
        {rows.map((r, i) => (
          <tr key={i} style={{ borderTop: `1px solid ${C.line}` }}>
            {r.map((c, j) => (
              <td key={j} style={{ padding: "10px 12px", color: C.text }}>
                {c}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const Section = ({ title, sub, action, children }) => (
  <div style={{ marginBottom: 22 }}>
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-end",
        marginBottom: 12,
        gap: 10,
        flexWrap: "wrap",
      }}
    >
      <div>
        <h2 style={S.h2}>{title}</h2>
        {sub && <div style={S.sub}>{sub}</div>}
      </div>
      {action}
    </div>
    {children}
  </div>
);

/* ইসলামিক টোনে লোডার — আরবি দুআসহ, মৃদু ভাসমান অ্যানিমেশন */
const Loader = ({ text = "একটু অপেক্ষা করুন…" }) => (
  <div
    style={{
      display: "grid",
      placeItems: "center",
      padding: "44px 16px",
      textAlign: "center",
    }}
  >
    <style>{`
      @keyframes tqaFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
      @keyframes tqaGlow{0%,100%{opacity:.4;transform:scale(.85)}50%{opacity:1;transform:scale(1)}}
    `}</style>
    <div style={{ animation: "tqaFloat 2.2s ease-in-out infinite" }}>
      <img
        src="/brand/logo-green.png"
        alt="তারবিয়াতুল কুরআন একাডেমি"
        style={{ width: 52, height: 52, borderRadius: 12 }}
      />
    </div>
    <div
      style={{
        fontFamily: "'Amiri', serif",
        fontSize: 26,
        fontWeight: 700,
        color: C.emerald,
        marginTop: 10,
        direction: "rtl",
        letterSpacing: 1,
      }}
    >
      رَبِّ زِدْنِي عِلْمًا
    </div>
    <div style={{ fontSize: 12.5, color: C.muted, marginTop: 6, lineHeight: 1.6 }}>
      {CURRENT_LANG === "en"
        ? "“My Lord, increase me in knowledge”"
        : "“হে আমার রব, আমার জ্ঞান বাড়িয়ে দিন”"}
      <br />
      {text}
    </div>
    <div
      style={{
        marginTop: 14,
        display: "flex",
        gap: 7,
        justifyContent: "center",
      }}
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: 9,
            height: 9,
            borderRadius: 99,
            background: C.gold,
            animation: `tqaGlow 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </div>
  </div>
);

/* ─────────────── helper selectors ─────────────── */
const userById = (id) => USERS.find((u) => u.id === id) || {};
// নতুন স্টুডেন্টের মাসিক ফি ডিফল্ট — পরিচালক প্রতিটি স্টুডেন্টের জন্য আলাদা
// করে বদলাতে পারেন; এখানে শুধু শুরুর মানটা ঠিক করা আছে (এক জায়গাতেই)
const DEFAULT_FEE = 3500;
const isDir = (u) => u.role === "director";
const isAdm = (u) => u.role === "admin" || u.role === "director"; // পরিচালক = সর্বোচ্চ ক্ষমতা
const courseById = (cs, id) => cs.find((c) => c.id === id) || {};
const myCourses = (cs, u) =>
  isAdm(u)
    ? cs
    : u.role === "teacher"
      /* ⚠️ এখানে আবার "কেবল কোর্সের উস্তাদ" ধরে ছাঁকা যাবে না।
         সার্ভার আগেই রোল অনুযায়ী ছেঁকে দেয় — উস্তাদ কোর্সটি পান দুই সূত্রে:
         তিনি কোর্সের নির্ধারিত উস্তাদ, অথবা কোর্সে তাঁর নিজের শিক্ষার্থী
         আছে। এখানে দ্বিতীয়বার ছাঁকলে দ্বিতীয় ধরনের কোর্সগুলো পর্দা থেকে
         হারিয়ে যেত — উস্তাদ নিজের শিক্ষার্থীর কোর্সই দেখতে পেতেন না। */
      ? cs
      : cs.filter((c) => (c.studentIds || []).includes(u.id));
/* অভিভাবকের WhatsApp-এ পাঠানোর মেসেজ তৈরি — আউটবক্সে জমা হয়, এক ট্যাপে পাঠানো যায় */
const waGuardianMsgs = (k, course, reason) => {
  const studs =
    (k.studentIds && k.studentIds.length ? k.studentIds : course.studentIds) ||
    [];
  return studs
    .map((sid) => {
      const s = userById(sid);
      if (!s.phone) return null;
      const text =
        reason === "reminder"
          ? `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম ${s.guardian || "অভিভাবক"}, ${s.name}-এর "${course.name}" ক্লাস আজ ${k.time}-এ (আর ৫ মিনিটের মধ্যে) শুরু হচ্ছে ইনশাআল্লাহ। অনুগ্রহ করে ক্লাসে যুক্ত হতে সহায়তা করুন। জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি`
          : `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ। মুহতারাম ${s.guardian || "অভিভাবক"}, ${s.name}-এর "${course.name}" ক্লাসটি (${fmtDate(k.date)}, ${k.time}) অনিবার্য কারণে / উস্তাদ-উস্তাদা অসুস্থ থাকার দরুন স্থগিত করা হয়েছে। ক্লাসটি পরবর্তীতে শিডিউল করে মেকআপ করা হবে ইনশাআল্লাহ। জাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি`;
      return {
        id: uid(),
        toName: s.guardian || s.name,
        student: s.name,
        phone: s.phone,
        text,
        reason: reason === "reminder" ? "৫ মিনিট রিমাইন্ডার" : "ক্লাস স্থগিত",
        date: todayISO(),
        sent: false,
      };
    })
    .filter(Boolean);
};

/* সিলেবাস এন্ট্রি → পাঠযোগ্য লেবেল (লেকচারের টপিক হিসেবে ব্যবহৃত) */
/* dataURL → blob URL (বই ডিভাইসের ডিফল্ট রিডারে খোলার জন্য) */
const dataUrlToBlobUrl = (dataUrl) => {
  try {
    const [head, b64] = dataUrl.split(",");
    const mime =
      (head.match(/data:(.*?);/) || [])[1] || "application/octet-stream";
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return { url: URL.createObjectURL(new Blob([arr], { type: mime })), mime };
  } catch (e) {
    return { url: dataUrl, mime: "application/octet-stream" };
  }
};
const bookExt = (n) => (n || "").split(".").pop().toUpperCase().slice(0, 5);

const sylLabel = (e) => {
  const prefix = e.book && e.book !== "অন্যান্য" ? e.book + " — " : "";
  if (e.category === "qirat" || !e.category) {
    return `${prefix}${e.lesson}${e.pages ? `, পৃষ্ঠা: ${e.pages}` : ""}${e.lines ? `, লাইন: ${e.lines}` : ""}`;
  }
  return `${prefix}${e.lesson}`;
};

/* টপিক কভারেজ — ব্যাকএন্ড LectureTopic.Covered স্ট্রিং enum ("covered"/"missed"/"pending")
   ↔ ফ্রন্টএন্ডের অভ্যন্তরীণ boolean (true=কভার / false=বাদ / null=বাকি) রূপান্তর */
const coveredToBool = (v) =>
  v === "covered" || v === true
    ? true
    : v === "missed" || v === false
      ? false
      : null;

/* API লেকচার → ফ্রন্টএন্ড shape (covered স্ট্রিং→boolean সহ)। মডিউল-লেভেল — কোর্স
   লোডার ও LecturePlan দুই জায়গায় পুনর্ব্যবহৃত, যাতে course.lectures সর্বত্র পূর্ণ থাকে */
const adaptLecture = (l) => ({
  id: l.id,
  no: l.no,
  title: l.title,
  date: l.date,
  topics: (l.topics || []).map((t) => ({
    id: t.id,
    syllabusId: t.syllabus_item || t.syllabusId,
    text: t.text,
    content: t.content || "", // টগলের ভেতরের লেখা — পুরনো টপিকে খালি
    order: t.order || 0,
    // কোন তারিখে টিক পড়েছে (YYYY-MM-DD) — "আজকের/বিগত" ভাগ করতে ও
    // "লেকচার: ২৩/০৮/২০২৬" দেখাতে লাগে। কখনো টিক না পড়লে null।
    markedAt: t.marked_at || null,
    covered: coveredToBool(t.covered),
  })),
});

/* দৈনিক পাঠ পরিকল্পনা / সিলেবাসের ৫টি বিভাগ — ব্যাকএন্ডের SyllabusItem.Category এর সাথে ১:১ */
const SYL_CATEGORIES = [
  {
    key: "memorized_surah",
    label: "মুখস্থ সূরা",
    labelEn: "Memorized Surah",
    icon: "📖",
    book: false,
    placeholder: "যেমন: সূরা ইখলাস",
  },
  {
    key: "memorized_hadith",
    label: "মুখস্থ হাদিস",
    labelEn: "Memorized Hadith",
    icon: "📜",
    book: false,
    placeholder: "যেমন: ১ম হাদিস — নিয়ত",
  },
  {
    key: "qirat",
    label: "কিরাত",
    labelEn: "Qirat",
    icon: "🕋",
    book: true,
    placeholder: "যেমন: কায়দা — লেসন ৪",
  },
  {
    key: "dua_masala",
    label: "দুআ/মাসআলা",
    labelEn: "Dua/Masala",
    icon: "🤲",
    book: true,
    placeholder: "যেমন: খাবারের দুআ",
  },
  {
    key: "moral_story",
    label: "নৈতিক শিক্ষা/হাদিসের গল্প",
    labelEn: "Moral Lesson/Hadith Story",
    icon: "🌟",
    book: true,
    placeholder: "যেমন: সততার গল্প",
  },
];
const catInfo = (k) =>
  SYL_CATEGORIES.find((c) => c.key === k) || SYL_CATEGORIES[2];

const CLASS_KINDS = [
  "মেকআপ ক্লাস",
  "সাপোর্ট ক্লাস",
  "রিকভারি ক্লাস",
  "ট্রায়াল ক্লাস",
  "নিয়মিত ক্লাস",
  "অন্যান্য",
];
/* ব্যাকএন্ড ClassSession.KINDS (ইংরেজি key) ↔ ফ্রন্টএন্ড বাংলা লেবেল */
const KIND_TO_KEY = {
  "মেকআপ ক্লাস": "makeup",
  "সাপোর্ট ক্লাস": "support",
  "রিকভারি ক্লাস": "recovery",
  "ট্রায়াল ক্লাস": "trial",
  "নিয়মিত ক্লাস": "regular",
  অন্যান্য: "other",
};
const KEY_TO_KIND = {
  makeup: "মেকআপ ক্লাস",
  support: "সাপোর্ট ক্লাস",
  recovery: "রিকভারি ক্লাস",
  trial: "ট্রায়াল ক্লাস",
  regular: "নিয়মিত ক্লাস",
  other: "অন্যান্য",
};
/* API ClassSession → ফ্রন্টএন্ড shape */
const adaptClass = (k) => ({
  id: k.id,
  courseId: k.course,
  date: k.date,
  time: (k.time || "").slice(0, 5),
  dur: k.duration_min,
  lectureNo: k.lecture_no,
  zoom: k.zoom_link,
  zoom2: k.zoom_link_2 || "",
  attendance: k.attendance || [], // উস্তাদ+স্টুডেন্ট আজ ইতিমধ্যে (দুজনেই) জয়েন করেছেন কিনা বের করতে — জয়েন/রিজয়েন বাটন ঠিক করতে ব্যবহৃত
  joinModeOverride: k.join_mode_override || "auto", // অটো ঠিক না হলে পরিচালক/এডমিনের ম্যানুয়াল ওভাররাইড (auto/join/rejoin)
  // ১ম নাকি ২য় জুম লিংক দেখাতে হবে — সার্ভারের সিদ্ধান্ত (দুজনের জন্য একই)
  rejoinActive: !!k.rejoin_active,
  kind: KEY_TO_KIND[k.kind] || "নিয়মিত ক্লাস",
  teacherId: k.teacher,
  studentIds: k.students || [],
  studentNames: k.student_names || [],
  teacherName: k.teacher_name,
  courseName: k.course_name,
  status: k.status,
  req: k.guardian_requirement || "",
  routineId: k.routine,
});
// আজকের এই ক্লাসে উস্তাদ+অন্তত একজন স্টুডেন্ট — দুজনেই ইতিমধ্যে (এই মুহূর্তে
// একসাথে না হলেও) অন্তত একবার জয়েন করে হাজিরা 'নিশ্চিত' হয়ে গেছে কিনা —
// হলে ১ম জুম লিংক আর দেখানো হবে না, ২য় (রিজয়েন) লিংক দেখাবে। পরিচালক/এডমিন
// joinModeOverride দিয়ে এই স্বয়ংক্রিয় সিদ্ধান্ত যেকোনো দিকে জোর করে বদলে
// দিতে পারেন (হাজিরার ডেটা স্পর্শ না করেই) — "join" মানে সবসময় ১ম লিংক,
// "rejoin" মানে সবসময় ২য় লিংক, "auto" মানে স্বাভাবিক (হাজিরা-ভিত্তিক) নিয়ম
const bothJoinedToday = (k) => {
  // সিদ্ধান্তটা এখন সার্ভার দেয় (rejoin_active) — উস্তাদ ও শিক্ষার্থী দুজনেই
  // একই উত্তর পান, তাই কেউ ১ম লিংকে আর কেউ ২য় লিংকে ঢুকে আলাদা মিটিংয়ে
  // চলে যাওয়ার সুযোগ নেই। ম্যানুয়াল ওভাররাইডও সার্ভারেই হিসাব হয়।
  return !!k.rejoinActive;
};
/* ফ্রন্টএন্ড ফরম → API ClassSession payload */
const classPayload = (ff, students) => ({
  course: ff.courseId,
  teacher: ff.teacherId,
  students,
  date: ff.date,
  time: ff.time,
  duration_min: +ff.dur,
  zoom_link: ff.zoom,
  zoom_link_2: ff.zoom2 || "",
  lecture_no: +ff.lectureNo,
  kind: KIND_TO_KEY[ff.kind] || "regular",
  guardian_requirement: ff.req || "",
});
const adaptPerson = (u) => ({
  id: u.id,
  name: u.name || u.name_bn,
  sub: u.sub || u.sub_title || "",
  phone: u.phone || "",
  email: u.email || "",
});
/* API Routine → ফ্রন্টএন্ড shape */
const adaptRoutine = (r) => ({
  id: r.id,
  courseId: r.course,
  teacherId: r.teacher,
  studentIds: r.students || [],
  studentNames: r.student_names || [],
  teacherName: r.teacher_name,
  courseName: r.course_name,
  days: r.days || [],
  time: (r.time || "").slice(0, 5),
  dur: r.duration_min,
  zoom: r.zoom_link,
  zoom2: r.zoom_link_2 || "",
  kind: "নিয়মিত ক্লাস",
  // প্রতি স্টুডেন্ট আলাদাভাবে ম্যানুয়ালি বসানো তাদের নিজের সময়ের বার+সময়
  // (কোনো স্বয়ংক্রিয় টাইমজোন-হিসাব নয়) — না থাকলে রুটিনের মূল বার-সময়ই প্রযোজ্য
  studentSchedule: Object.fromEntries(
    (r.student_schedules || []).map((s) => [
      String(s.student),
      { days: s.days || [], time: (s.time || "").slice(0, 5) },
    ]),
  ),
});
const routinePayload = (ff, students, studentSchedule) => ({
  course: ff.courseId,
  teacher: ff.teacherId,
  students,
  days: ff.days,
  time: ff.time,
  duration_min: +ff.dur,
  zoom_link: ff.zoom,
  zoom_link_2: ff.zoom2 || "",
  student_schedules: Object.entries(studentSchedule || {})
    .filter(([sid]) => students.includes(+sid) || students.includes(sid))
    .map(([sid, v]) => ({ student: +sid, days: v.days || [], time: v.time || null })),
});
/* ক্লাস/রুটিন কার পোর্টালে দেখাবে — নির্দিষ্ট উস্তাদ/স্টুডেন্ট দেওয়া থাকলে নাম অনুযায়ী, নইলে কোর্স অনুযায়ী */
const itemVisible = (it, user) => {
  if (isAdm(user)) return true;
  const c = courseById(COURSES, it.courseId);
  if (user.role === "teacher")
    return it.teacherId ? it.teacherId === user.id : c.teacherId === user.id;
  if (user.role === "student")
    return it.studentIds && it.studentIds.length
      ? it.studentIds.includes(user.id)
      : (c.studentIds || []).includes(user.id);
  return false;
};
/* সব স্টুডেন্টের নামের তালিকা — চেকবক্সে এক এক করে বাছাই */
function StudentPicker({ selected, onToggle, people }) {
  const list =
    people && people.length
      ? people
      : USERS.filter((u) => u.role === "student");
  return (
    <div
      style={{
        maxHeight: 150,
        overflowY: "auto",
        border: `1.5px solid ${C.line}`,
        borderRadius: 10,
        padding: 6,
        background: "#fff",
      }}
    >
      {list.map((s) => (
        <label
          key={s.id}
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            padding: "6px 8px",
            fontSize: 13,
            cursor: "pointer",
            borderRadius: 8,
            background: selected.includes(s.id) ? C.greenBg : "transparent",
          }}
        >
          <input
            type="checkbox"
            checked={selected.includes(s.id)}
            onChange={() => onToggle(s.id)}
          />
          <b>{s.name}</b>{" "}
          <span style={{ color: C.muted, fontSize: 11.5 }}>({s.sub})</span>
        </label>
      ))}
    </div>
  );
}


/* এক-ক্লিকে অ্যাপ ইনস্টল করার ব্যানার — লগইন পেজের উপরে দেখায়। Android/Windows/
   Mac-এ Chrome/Edge হলে beforeinstallprompt ইভেন্ট থাকলে সরাসরি ব্রাউজারের আসল
   "Install" পপআপ দেখায় (এক ক্লিকেই ইনস্টল)। iOS Safari-তে এই ইভেন্ট কখনো আসে না
   (Apple-এর সীমাবদ্ধতা, প্রোগ্রাম্যাটিকভাবে ইনস্টল করানোর কোনো উপায় নেই) — তাই
   সেখানে "Add to Home Screen" এর স্পষ্ট নির্দেশনা দেখানো হয়। অলরেডি ইনস্টল করা
   থাকলে (standalone mode) কিছুই দেখায় না। */
function InstallBanner({ lang }) {
  const T = (bn, en) => (lang === "en" ? en : bn);
  const [ready, setReady] = useState(!!window.__tqaInstallEvent);
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem("tqa_install_dismissed") === "1",
  );
  useEffect(() => {
    const handler = () => setReady(true);
    window.addEventListener("tqa-install-ready", handler);
    return () => window.removeEventListener("tqa-install-ready", handler);
  }, []);
  const isStandalone =
    (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) ||
    window.navigator.standalone;
  const ua = navigator.userAgent || "";
  const isIOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (ua.includes("Macintosh") && navigator.maxTouchPoints > 1);
  if (isStandalone || dismissed) return null;
  if (!ready && !isIOS) return null; // অন্য ব্রাউজারে ইনস্টল-সাপোর্ট না থাকলে কিছুই দেখাই না

  const dismiss = () => {
    sessionStorage.setItem("tqa_install_dismissed", "1");
    setDismissed(true);
  };
  const install = async () => {
    const evt = window.__tqaInstallEvent;
    if (!evt) return;
    evt.prompt();
    try {
      await evt.userChoice;
    } catch {
      /* উপেক্ষা */
    }
    window.__tqaInstallEvent = null;
    dismiss();
  };

  return (
    <div
      style={{
        ...S.card,
        marginBottom: 14,
        border: `1.5px solid ${C.gold}`,
        background: C.amberBg,
        textAlign: "center",
        padding: 18,
      }}
    >
      <div style={{ fontSize: 30 }}>📲</div>
      {ready ? (
        <>
          <div style={{ fontWeight: 800, margin: "6px 0 10px", fontSize: 15 }}>
            {T("এই ডিভাইসে অ্যাপ ইনস্টল করুন", "Install the app on this device")}
          </div>
          <Btn kind="gold" onClick={install}>
            {T("⬇️ ইনস্টল করুন", "⬇️ Install App")}
          </Btn>
        </>
      ) : (
        <>
          <div style={{ fontWeight: 800, margin: "6px 0 4px", fontSize: 15 }}>
            {T("Add to Home Screen", "Add to Home Screen")}
          </div>
          <div style={{ fontSize: 12.5, color: C.muted, lineHeight: 1.6 }}>
            {T(
              'নিচের শেয়ার বাটনে (□↑) ট্যাপ করুন, তারপর "Add to Home Screen" চাপুন',
              'Tap the Share button (□↑) below, then tap "Add to Home Screen"',
            )}
          </div>
        </>
      )}
      <div style={{ marginTop: 8 }}>
        <button
          onClick={dismiss}
          style={{
            fontSize: 11.5,
            color: C.muted,
            background: "none",
            border: "none",
            textDecoration: "underline",
            cursor: "pointer",
            fontFamily: "inherit",
          }}
        >
          {T("বাদ দিন", "Skip")}
        </button>
      </div>
    </div>
  );
}

/* ═══════════════ লগইন ═══════════════ */
function Login({ onLogin }) {
  /* ভূমিকার তালিকা — কার্ড হিসেবে দেখানো হয় */
  const ROLES = [
    {
      key: "director",
      label: "পরিচালক / Director",
      icon: "👑",
      desc: "সার্বিক তত্ত্বাবধান — ফি, বেতন, রিপোর্ট ও সকল ক্ষমতা",
      tint: "rgba(124,58,237,.10)",
    },
    {
      key: "admin",
      label: "এডমিন / Admin",
      icon: "🛡️",
      desc: "শিক্ষার্থী, উস্তাদ, ক্লাস ও পেমেন্ট ব্যবস্থাপনা",
      tint: "rgba(99,102,241,.10)",
      cardTitle: "Admin",
      cardDesc: "Full access — manage students, teachers, schedules and payments",
    },
    {
      key: "teacher",
      label: "উস্তাদ/উস্তাদা / Teacher",
      icon: "📖",
      desc: "ক্লাস, হাজিরা, পড়ানো ও শিক্ষার্থীর অগ্রগতি",
      tint: "rgba(26,92,58,.10)",
      cardTitle: "Ustadh / Ustadha",
      cardDesc: "View your schedule, student progress and lesson notes",
    },
    {
      key: "student",
      label: "স্টুডেন্ট / Student",
      icon: "🎓",
      desc: "Routine, classes, exams & fee status",
      tint: "rgba(201,150,42,.10)",
      cardTitle: "Student",
      cardDesc: "View your timetable, homework and progress reports",
    },
  ];
  // ধাপ ১ (ভূমিকা বাছাই)-এ শুধু এই ৩টা দেখানো হয় — ওয়েবসাইটের login.html-এর
  // মতোই; পরিচালক পুরো ROLES তালিকায় থেকে যান (?role=director লিংক ও
  // "Director login" এর জন্য), কিন্তু আলাদা কার্ড হিসেবে প্রকাশ্যে দেখানো হয় না
  const VISIBLE_ROLES = ROLES.filter((r) => r.key !== "director");
  /* ওয়েবসাইটের login.html থেকে ?role=admin দিয়ে এলে সরাসরি ফর্মে */
  const initRole = (() => {
    try {
      const r = new URLSearchParams(window.location.search).get("role");
      return ROLES.some((x) => x.key === r) ? r : null;
    } catch {
      return null;
    }
  })();
  const [role, setRole] = useState(initRole);
  // স্টুডেন্ট বেছে নিলে ফর্ম ইংরেজিতে দেখাবে — বেশিরভাগ শিক্ষার্থী বাংলা বোঝে না
  const T = (bnText, enText) => (role === "student" ? enText : bnText);
  // হেডার (একাডেমির নাম) — role বাছাইয়ের আগে (ওয়েবসাইটের role-card স্ক্রিনের
  // মতো) ও student-এর জন্য ইংরেজি; director/admin/teacher বেছে নেওয়ার পরই বাংলা
  const TH = (bnText, enText) => (role && role !== "student" ? bnText : enText);
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const go = async () => {
    if (!u.trim() || !p) {
      setErr(T("আইডি ও পাসওয়ার্ড দুটোই লিখুন", "Please enter both ID and password"));
      return;
    }
    setBusy(true);
    setErr("");
    const q = u.trim();
    const pw = p.trim(); // কপি-পেস্টে আসা অদৃশ্য স্পেস/নিউলাইন সরানো (পাসওয়ার্ডে স্পেস থাকে না)
    try {
      const me = await login(q, pw);
      // নিরাপত্তা: বাছাই করা স্ক্রিনের ভূমিকা (role) আর অ্যাকাউন্টের প্রকৃত
      // ভূমিকা না মিললে লগইন বাতিল করি — নইলে "স্টুডেন্ট" স্ক্রিন থেকেই
      // পরিচালকের আইডি-পাসওয়ার্ড দিয়ে পরিচালক পোর্টালে ঢুকে যাওয়া সম্ভব হতো
      // (এবং উল্টোটাও) যা নিরাপত্তার জন্য বিপজ্জনক
      if (me.role !== role) {
        logout(); // নতুন পাওয়া টোকেন সাথে সাথেই বাতিল — কোনো সেশন থেকে যাবে না
        setErr(
          T(
            "এই আইডি-পাসওয়ার্ড এই ভূমিকার (role) জন্য নয় — সঠিক ভূমিকা বেছে আবার চেষ্টা করুন।",
            "This ID/password isn't for this role — please go back and choose the correct role.",
          ),
        );
        return;
      }
      onLogin({
        ...me,
        id: me.id,
        name: me.name || me.name_bn,
        sub: me.sub || me.sub_title || "",
        user: me.username,
        pass: pw,
        fee: me.monthly_fee,
        salary: me.monthly_salary,
      });
    } catch (e) {
      if (e?.status === 401 || e?.message?.includes("401")) {
        setErr(T("ভুল আইডি বা পাসওয়ার্ড!", "Incorrect ID or password!"));
      } else if (e?.status === 429) {
        // নিরাপত্তার জন্য মিনিটে সর্বোচ্চ ২০ বার লগইন চেষ্টার সীমা (brute-force ঠেকাতে) —
        // এটা সার্ভার-ডাউন নয়, শুধু সাময়িক সীমা; আগে ভুলভাবে "সংযোগ নেই" দেখাত
        setErr(
          T(
            "অনেকবার চেষ্টা হয়েছে — নিরাপত্তার জন্য সাময়িকভাবে আটকানো হয়েছে। ১ মিনিট অপেক্ষা করে আবার চেষ্টা করুন।",
            "Too many attempts — temporarily blocked for security. Please wait 1 minute and try again.",
          ),
        );
      } else {
        setErr(
          T(
            "সার্ভার সংযোগ নেই। ব্যাকএন্ড চালু আছে কি?",
            "No server connection. Please check your internet and try again.",
          ),
        );
      }
    } finally {
      setBusy(false);
    }
  };
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#fff",
        display: "grid",
        placeItems: "center",
        padding: 16,
      }}
    >
      <style>{`
        .tqaRoleCard{transition:border-color .15s,background .15s,box-shadow .15s,transform .15s}
        .tqaRoleCard:hover{border-color:${C.emerald};background:#f2f7f4;box-shadow:0 4px 16px rgba(26,92,58,.12);transform:translateY(-2px)}
        .tqaRoleCard:hover .tqaRoleArrow{color:${C.emerald};transform:translateX(3px)}
      `}</style>
      <div style={{ width: "100%", maxWidth: 480 }}>
        <InstallBanner lang={role === "student" ? "en" : "bn"} />
        <div
          style={{
            background: "rgba(255,255,255,.97)",
            borderRadius: 24,
            padding: "44px 40px 40px",
            boxShadow: "0 24px 64px rgba(0,0,0,.25)",
            border: `1px solid ${C.line}`,
            boxSizing: "border-box",
          }}
        >
          {/* লোগো — ওয়েবসাইটের সাথে মেলানো (ফ্রেমযুক্ত আইকন + নাম পাশাপাশি) */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 12,
              marginBottom: 28,
            }}
          >
            <div
              style={{
                width: 54,
                height: 52,
                padding: 2,
                border: `3px solid ${C.emeraldL}`,
                borderRadius: 12,
                boxShadow: "0 2px 12px rgba(26,92,58,.35), 0 0 0 2px rgba(240,195,85,.25)",
                flexShrink: 0,
                boxSizing: "border-box",
              }}
            >
              <img
                src="/brand/logo-green.png"
                alt="তারবিয়াতুল কুরআন একাডেমি"
                style={{
                  width: "100%",
                  height: "100%",
                  borderRadius: 7,
                  objectFit: "cover",
                  display: "block",
                }}
              />
            </div>
            <div style={{ textAlign: "left" }}>
              <span
                style={{
                  display: "block",
                  fontSize: 16,
                  fontWeight: 800,
                  color: C.emeraldD,
                  lineHeight: 1.15,
                }}
              >
                {TH("তারবিয়াতুল কুরআন একাডেমি", "Tarbiyatul Quran Academy")}
              </span>
              <span
                style={{
                  display: "block",
                  fontSize: 12,
                  color: C.muted,
                  marginTop: 2,
                }}
              >
                {TH("ম্যানেজমেন্ট পোর্টাল", "Management Portal")}
              </span>
            </div>
          </div>
          {!role ? (
            <>
              {/* ── ধাপ ১: ভূমিকা বাছাই (এখনো কে বাছবে জানা নেই, তাই দুই ভাষাতেই) ── */}
              <h1
                style={{
                  fontFamily: "'Playfair Display', Georgia, serif",
                  fontWeight: 800,
                  fontSize: 22,
                  color: C.text,
                  textAlign: "center",
                  marginBottom: 6,
                  lineHeight: 1.3,
                }}
              >
                Who are you logging in as?
              </h1>
              <div
                style={{
                  fontSize: 13.5,
                  color: C.muted,
                  textAlign: "center",
                  marginBottom: 26,
                  lineHeight: 1.5,
                }}
              >
                Choose your role to continue to the management dashboard.
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {VISIBLE_ROLES.map((r) => (
                  <button
                    key={r.key}
                    className="tqaRoleCard"
                    onClick={() => {
                      setRole(r.key);
                      setErr("");
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 16,
                      padding: "18px 20px",
                      borderRadius: 16,
                      border: `2px solid ${C.line}`,
                      background: "#fff",
                      cursor: "pointer",
                      textAlign: "left",
                      width: "100%",
                      fontFamily: "inherit",
                      boxSizing: "border-box",
                    }}
                  >
                    <span
                      style={{
                        width: 52,
                        height: 52,
                        borderRadius: 14,
                        display: "grid",
                        placeItems: "center",
                        fontSize: 26,
                        flexShrink: 0,
                        background: r.tint,
                      }}
                    >
                      {r.icon}
                    </span>
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <span
                        style={{
                          display: "block",
                          fontWeight: 800,
                          fontSize: 16,
                          color: C.text,
                        }}
                      >
                        {r.cardTitle}
                      </span>
                      <span
                        style={{
                          display: "block",
                          fontSize: 13,
                          color: C.muted,
                          marginTop: 3,
                          lineHeight: 1.4,
                        }}
                      >
                        {r.cardDesc}
                      </span>
                    </span>
                    <span
                      className="tqaRoleArrow"
                      style={{
                        fontSize: 18,
                        color: "#9ca3af",
                        flexShrink: 0,
                        transition: "color .15s, transform .15s",
                      }}
                    >
                      →
                    </span>
                  </button>
                ))}
              </div>
              <div
                style={{
                  marginTop: 24,
                  paddingTop: 20,
                  borderTop: `1px solid ${C.line}`,
                  textAlign: "center",
                  fontSize: 12,
                  color: "#9ca3af",
                  lineHeight: 1.6,
                }}
              >
                Need an account? Contact{" "}
                <a
                  href="mailto:ibnhosain014@gmail.com"
                  style={{ color: C.emerald, fontWeight: 600 }}
                >
                  ibnhosain014@gmail.com
                </a>{" "}
                or{" "}
                <a
                  href="https://wa.me/8801402499027"
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: C.emerald, fontWeight: 600 }}
                >
                  WhatsApp
                </a>
                .
                <br />
                <button
                  onClick={() => {
                    setRole("director");
                    setErr("");
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    color: C.muted,
                    fontSize: 12,
                    cursor: "pointer",
                    padding: 0,
                    marginTop: 8,
                    fontFamily: "inherit",
                    textDecoration: "underline",
                  }}
                >
                  Director login →
                </button>
              </div>
            </>
          ) : (
            <>
              {/* ── ধাপ ২: আইডি ও পাসওয়ার্ড ── */}
              <button
                onClick={() => {
                  setRole(null);
                  setErr("");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: C.muted,
                  fontSize: 12.5,
                  cursor: "pointer",
                  padding: 0,
                  marginBottom: 12,
                  fontFamily: "inherit",
                }}
              >
                {T("← ভূমিকা বদলান", "← Change role")}
              </button>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  marginBottom: 16,
                }}
              >
                <span style={{ fontSize: 30 }}>
                  {ROLES.find((r) => r.key === role).icon}
                </span>
                <div>
                  <div
                    style={{
                      fontFamily: "'Playfair Display', Georgia, serif",
                      fontWeight: 800,
                      fontSize: 17,
                      color: C.text,
                    }}
                  >
                    {T(
                      `${ROLES.find((r) => r.key === role).label} লগইন`,
                      "Student Login",
                    )}
                  </div>
                  <div style={{ fontSize: 11.5, color: C.muted }}>
                    {T("আপনার আইডি ও পাসওয়ার্ড দিন", "Enter your ID and password")}
                  </div>
                </div>
              </div>
              <label style={S.label}>{T("আইডি", "ID")}</label>
              <input
                style={{ ...S.input, width: "100%", boxSizing: "border-box" }}
                value={u}
                onChange={(e) => setU(e.target.value)}
                placeholder={T(
                  "আইডি / ইমেইল / মোবাইল নম্বর",
                  "ID / Email / Mobile number",
                )}
                autoFocus
              />
              <div style={{ height: 12 }} />
              <label style={S.label}>{T("পাসওয়ার্ড", "Password")}</label>
              <div style={{ position: "relative" }}>
                <input
                  style={{
                    ...S.input,
                    width: "100%",
                    boxSizing: "border-box",
                    paddingRight: 44,
                  }}
                  type={showPass ? "text" : "password"}
                  value={p}
                  onChange={(e) => setP(e.target.value)}
                  placeholder="••••••••"
                  onKeyDown={(e) => e.key === "Enter" && go()}
                />
                <button
                  onClick={() => setShowPass((s) => !s)}
                  title={T(
                    showPass ? "পাসওয়ার্ড লুকান" : "পাসওয়ার্ড দেখুন",
                    showPass ? "Hide password" : "Show password",
                  )}
                  aria-label={T(
                    showPass ? "পাসওয়ার্ড লুকান" : "পাসওয়ার্ড দেখুন",
                    showPass ? "Hide password" : "Show password",
                  )}
                  style={{
                    position: "absolute",
                    right: 10,
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: 17,
                    padding: 2,
                    lineHeight: 1,
                  }}
                >
                  {showPass ? "🙈" : "👁️"}
                </button>
              </div>
              {err && (
                <div style={{ color: C.red, fontSize: 12.5, marginTop: 8 }}>
                  {err}
                </div>
              )}
              <Btn
                style={{
                  width: "100%",
                  justifyContent: "center",
                  marginTop: 16,
                  opacity: busy || !u.trim() || !p ? 0.55 : 1,
                }}
                disabled={busy || !u.trim() || !p}
                onClick={go}
              >
                {busy ? T("যাচাই হচ্ছে…", "Verifying…") : T("লগ ইন করুন", "Log In")}
              </Btn>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════ Web Push (PWA) — ব্রাউজার/ট্যাব বন্ধ থাকলেও নোটিফিকেশন ═══════════════ */
const urlBase64ToUint8Array = (base64) => {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const base64safe = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64safe);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
};
// ইউজারের সরাসরি ক্লিকে (নোটিফিকেশন-পারমিশন ব্রাউজার-গ্রেসচার ছাড়া চাইলে
// উপেক্ষা/ব্লক করে) ডাকা হয় — সার্ভিস ওয়ার্কার রেজিস্টার + পারমিশন চাওয়া +
// পুশ-সাবস্ক্রিপশন ব্যাকএন্ডে সেভ, সব এক ফাংশনে
async function enablePushNotifications(silent = false) {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    if (!silent) notice("এই ব্রাউজারে পুশ নোটিফিকেশন সাপোর্ট নেই।");
    return false;
  }
  try {
    const reg = await navigator.serviceWorker.register("/sw.js");
    // পারমিশন আগে থেকেই "granted" থাকলে (যেমন অনেক আগে "জুমে জয়েন করুন" ক্লিকের
    // সময় দেওয়া হয়েছিল) requestPermission() কোনো পপআপ ছাড়াই সাথে সাথে granted
    // ফেরত দেয় — তাই silent মোডে এটা নিরাপদে ডাকা যায়, ব্যবহারকারীর ক্লিক ছাড়াই
    const perm = await Notification.requestPermission();
    if (perm !== "granted") {
      if (!silent) notice("নোটিফিকেশনের অনুমতি দেওয়া হয়নি।");
      return false;
    }
    const { key } = await api.vapidPublicKey();
    if (!key) return false; // সার্ভারে VAPID কনফিগার করা না থাকলে চুপচাপ থেমে যায়
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(key),
      });
    }
    const raw = sub.toJSON();
    await api.subscribePush({
      endpoint: raw.endpoint,
      p256dh: raw.keys.p256dh,
      auth: raw.keys.auth,
    });
    if (!silent) notice("✔ এই ডিভাইসে নোটিফিকেশন চালু হয়েছে।");
    return true;
  } catch {
    if (!silent) notice("নোটিফিকেশন চালু করতে ব্যর্থ — একটু পর আবার চেষ্টা করুন।");
    return false;
  }
}

/* ═══════════════ ক্লাস ও জুম জয়েন (ফিচার ২ ও ৪) ═══════════════ */
/* ইন-ক্লাস প্যানেল — দুজন-জয়েন গেটিং, জয়েন করা মাত্রই হাজিরা নিশ্চিত */
function LiveClassPanel({ k, user, usingApi, onExit, onFinished }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [presence, setPresence] = useState(null);
  const [inMeeting, setInMeeting] = useState(true);
  const [showContinuePrompt, setShowContinuePrompt] = useState(false);
  // "Leave & Save" বাটনে ক্লিক ভুলে গেলে/ট্যাব বন্ধ করে ফেললেও যেন হাজিরার সময়
  // না হারায় — প্রতি ৬০ সেকেন্ডে নিঃশব্দে ব্যাকগ্রাউন্ডে যতটুকু সময় জমেছে তা
  // ব্যাকএন্ডে সেভ করে রাখি (ref ব্যবহার করছি যাতে interval-এ স্টেল ভ্যালু না আসে)
  const savedSecRef = useRef(0);
  // সময় "গুনে" (setInterval-এ প্রতি সেকেন্ডে +1) রাখার বদলে timestamp থেকে হিসাব
  // করা হয় — কারণ জুম আলাদা ট্যাবে খোলে বলে ক্লাস চলাকালীন এই ট্যাবটাই
  // ব্রাউজারে ব্যাকগ্রাউন্ডে থাকে, আর ব্রাউজার ব্যাকগ্রাউন্ড ট্যাবের টাইমার
  // নিজে থেকেই ধীর/বন্ধ করে দেয় — ফলে "গোনা" সেকেন্ড হারিয়ে/আটকে যেত। timestamp
  // থেকে হিসাব করলে টাইমার থ্রটল হলেও পরের বার চেক করা মাত্র সঠিক সময়ই বেরোয়।
  const accumulatedMsRef = useRef(0); // এই সেগমেন্টে "দুজনেই উপস্থিত" অবস্থায় ইতিমধ্যে জমে যাওয়া সময়
  const activeSinceRef = useRef(null); // এখন bothIn true হলে কখন থেকে (timestamp), নইলে null
  const computeSegSec = () => {
    const extra = activeSinceRef.current ? Date.now() - activeSinceRef.current : 0;
    return Math.floor((accumulatedMsRef.current + extra) / 1000);
  };

  const [joinError, setJoinError] = useState(false);
  // presence চেক পরপর কয়েকবার ব্যর্থ হলে (আগে সম্পূর্ণ চুপচাপ উপেক্ষা হতো, ফলে
  // নেটওয়ার্ক সমস্যায় "জয়েনের অপেক্ষায়" চিরকাল আটকে থাকলেও কিছু বোঝা যেত না)
  const presenceFailRef = useRef(0);
  const [presenceStale, setPresenceStale] = useState(false);
  const refreshPresence = async () => {
    if (!usingApi) {
      setPresence((p) => ({ ta: true, sa: true, myMin: p?.myMin || 0, myPresent: true }));
      return;
    }
    try {
      const p = await api.classPresence(k.id);
      const me = (p.attendance || []).find(
        (a) => String(a.user) === String(user.id),
      );
      setPresence({
        ta: p.teacher_active,
        sa: p.any_student_active,
        myMin: me?.minutes || 0,
        myPresent: !!me?.present, // উস্তাদ+স্টুডেন্ট দুজনেই জয়েন করা মাত্র backend এটা true করে দেয়
      });
      presenceFailRef.current = 0;
      setPresenceStale(false);
    } catch {
      presenceFailRef.current += 1;
      if (presenceFailRef.current >= 3) setPresenceStale(true); // পরপর ৩ বার (~১৫s) ব্যর্থ হলেই সতর্ক করি, একবার-দুবার সাময়িক নেটওয়ার্ক গ্লিচে যেন বিরক্ত না করে
    }
  };

  // সেগমেন্ট শুরু (মাউন্টে ও প্রতি রিজয়েনে) — আগে এই কলটা ব্যর্থ হলে চুপচাপ
  // উপেক্ষা করা হতো, ফলে কারো জয়েন কখনো ব্যাকএন্ডে রেকর্ড না হলেও (যেমন ওই
  // ক্লাসের সাথে তার অ্যাকাউন্ট ঠিকভাবে যুক্ত না থাকলে) কোনো বার্তা ছাড়াই
  // "জয়েনের অপেক্ষায়" আটকে থাকত — এখন ব্যর্থ হলে স্পষ্ট জানিয়ে দেওয়া হয়
  useEffect(() => {
    if (usingApi && inMeeting) {
      setJoinError(false);
      api.joinClass(k.id).catch(() => setJoinError(true));
    }
  }, [inMeeting]);

  // presence poll — কে এখন মিটিংয়ে আছে (৫ সেকেন্ড পরপর — আগে ১২ সেকেন্ড ছিল,
  // দ্রুত আপডেট হওয়ার জন্য কমানো হলো)
  useEffect(() => {
    refreshPresence();
    const iv = setInterval(refreshPresence, 5000);
    return () => clearInterval(iv);
  }, [k.id]);

  const bothIn = user.role === "teacher" ? !!presence?.sa : !!presence?.ta;

  // bothIn/inMeeting বদলালেই accumulatedMsRef/activeSinceRef হালনাগাদ করি —
  // এটাই "সত্যিকারের" হিসাব, টাইমার-নির্ভর নয়
  useEffect(() => {
    if (inMeeting && bothIn) {
      activeSinceRef.current = Date.now();
    } else if (activeSinceRef.current) {
      accumulatedMsRef.current += Date.now() - activeSinceRef.current;
      activeSinceRef.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inMeeting, bothIn]);

  // প্রতি ৬০ সেকেন্ডে নিঃশব্দে হাজিরার জমে-থাকা মিনিট ব্যাকএন্ডে সেভ করে রাখি —
  // "Leave & Save" বাটনে ক্লিক করতে ভুলে গেলে/ব্রাউজার ট্যাব বন্ধ হয়ে গেলেও এতে
  // সর্বোচ্চ ৬০ সেকেন্ড ছাড়া বাকি সবটুকু সময় হাজিরায় গণ্য হয়ে যাবে
  const doCheckpoint = async () => {
    if (!usingApi || !inMeetingRef.current) return;
    const deltaMin = Math.floor((computeSegSec() - savedSecRef.current) / 60);
    if (deltaMin < 1) return;
    try {
      // leave+join (আগে ব্যবহৃত হতো) সাময়িকভাবে segment_start খালি করে দিত,
      // ফলে অন্যপাশের প্রেজেন্স-পোল ঠিক তখন পড়লে ভুল করে "চলে গেছেন" ধরে
      // তার কাউন্টার থামিয়ে দিতে পারত — checkpoint শুধু মিনিট যোগ করে,
      // presence/segment_start-এ হাত দেয় না, তাই এই সমস্যা আর হবে না
      await api.checkpointClass(k.id, deltaMin);
      savedSecRef.current += deltaMin * 60;
      // presence.myMin পরের ১২-সেকেন্ড পোলে আপডেট হওয়ার জন্য অপেক্ষা না করে
      // এখনই যোগ করে দিই — নইলে savedSecRef বেড়ে যাওয়ায় "মোট" সংখ্যাটা কয়েক
      // সেকেন্ডের জন্য থমকে/পিছিয়ে যেত (দুটো কাউন্টার একসাথে না চলার মতো দেখাত)
      setPresence((p) => (p ? { ...p, myMin: (p.myMin || 0) + deltaMin } : p));
    } catch {
      /* উপেক্ষা — পরের চেকপয়েন্টে আবার চেষ্টা হবে */
    }
  };
  useEffect(() => {
    if (!usingApi) return;
    const iv = setInterval(() => {
      if (inMeeting && bothIn) doCheckpoint();
    }, 60000);
    return () => clearInterval(iv);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inMeeting, bothIn, usingApi, k.id]);

  // ট্যাব ব্যাকগ্রাউন্ডে থাকা অবস্থায় উপরের ৬০-সেকেন্ড ইন্টারভ্যালও ব্রাউজার
  // থ্রটল করতে পারে (তখন সেভও দেরিতে হয়) — তাই ট্যাবে ফিরে এলেই (টিচার/স্টুডেন্ট
  // দুজনের জন্যই) একবার সাথে সাথে চেকপয়েন্ট সেভের চেষ্টা করি
  useEffect(() => {
    let wasHidden = document.hidden;
    const iv = setInterval(() => {
      const isHidden = document.hidden;
      if (!isHidden && wasHidden) doCheckpoint();
      wasHidden = isHidden;
    }, 2000);
    return () => clearInterval(iv);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // প্যানেল হঠাৎ বন্ধ/সরিয়ে ফেললে (অন্য ভিউতে চলে গেলে) — যতটুকু সময় এখনো
  // চেকপয়েন্টে সেভ হয়নি তা শেষবারের মতো ব্যাকগ্রাউন্ডে সেভ করার চেষ্টা।
  // ⚠️ এখানে leave() ব্যবহার করা যাবে না — leave() ব্যাকএন্ডে segment_start
  // মুছে দেয়, অর্থাৎ "ইনি আর মিটিংয়ে নেই" ঘোষণা করে। ফলে উস্তাদ ক্লাস
  // চলাকালীন পোর্টালের অন্য পেইজে এক মিনিটের জন্য গেলেও অন্যপাশে তাঁকে
  // "চলে গেছেন" দেখাত এবং শিক্ষার্থীর মিনিট গণনা থেমে যেত। checkpoint()
  // শুধু মিনিট যোগ করে, উপস্থিতিতে হাত দেয় না — তাই উস্তাদ যেখানেই যান বা
  // যত নেট সমস্যাই হোক, তাঁর "উপস্থিত" অবস্থা অক্ষুণ্ণ থাকে। একমাত্র
  // "ক্লাস শেষ করুন" বাটনই (endSegment) leave() ডাকে।
  useEffect(() => {
    return () => {
      if (!usingApi) return;
      const deltaMin = Math.floor(
        (computeSegSec() - savedSecRef.current) / 60,
      );
      if (deltaMin >= 1) api.checkpointClass(k.id, deltaMin).catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // প্রতি ৬০ সেকেন্ডে যে মিনিটগুলো চেকপয়েন্টে সার্ভারে সেভ হয়ে গেছে (savedSecRef),
  // সেগুলো presence.myMin (সার্ভারের মোট)-এ ইতিমধ্যেই যুক্ত আছে — তাই সেগমেন্টের
  // পুরো সময় ফের যোগ করলে একই মিনিট দুবার গোনা (ডাবল-কাউন্ট) হয়ে যেত; শুধু
  // এখনো-সেভ-না-হওয়া অংশটুকু যোগ করি
  const notYetSavedMin = Math.max(
    0,
    Math.round((computeSegSec() - savedSecRef.current) / 60),
  );
  const total = (presence?.myMin || 0) + notYetSavedMin;
  // উস্তাদ+স্টুডেন্ট দুজনেই একসাথে জয়েন করা মাত্রই হাজিরা 'সম্পন্ন' হয়ে যায় (backend
  // থেকে present ফ্ল্যাগ আসে) — আর ৪৫ মিনিট থাকার দরকার নেই, শুধু জয়েন হলেই যথেষ্ট।
  // পোর্টালে সতর্কতার জন্য এখনো "৪৫+ মিনিট" লেখাই থাকছে যাতে কেউ ইচ্ছা করে
  // দু-মিনিট থেকেই বেরিয়ে যাওয়াকে স্বাভাবিক না ভাবেন।
  const done = !!presence?.myPresent;

  // mode: "manual" (স্টুডেন্ট/উস্তাদ নিজে "বের হন" চেপেছেন — মাঝপথে বেরোনো,
  // রেটিং পপআপ আসবে না), "finish" (ক্লাসের নির্ধারিত সময় (dur) শেষ — কোনো
  // বাটন ছাড়াই অটো বের হয়ে রেটিং পপআপ দেখাবে)
  // ক্লাস শেষ করার অনুরোধ সার্ভারে পাঠানো হয়েছে কিনা — বাটনটা দুবার চাপা ঠেকায়
  const [ending, setEnding] = useState(false);
  const endSegment = async (mode) => {
    setInMeeting(false);
    // চেকপয়েন্টে ইতিমধ্যে সেভ হওয়া মিনিট বাদ দিয়ে শুধু বাকি (এখনো সেভ না হওয়া)
    // মিনিটটুকু পাঠাই — নইলে একই মিনিট দুবার গণনা (ডাবল-কাউন্ট) হয়ে যেত
    const m = Math.max(0, Math.round((computeSegSec() - savedSecRef.current) / 60));
    activeSinceRef.current = null;
    accumulatedMsRef.current = 0;
    savedSecRef.current = 0;
    if (usingApi) {
      try {
        await api.leaveClass(k.id, m);
      } catch {
        // হাজিরা (present/না-present) জয়েন করার মুহূর্তেই নিশ্চিত হয়ে গেছে,
        // এটা শুধু শেষ কয়েক (< ৬০ সেকেন্ড) মিনিটের হিসাব সেভ করার চেষ্টা —
        // ব্যর্থ হলেও হাজিরা প্রভাবিত হয় না, তাই এখনো এক্সিট আটকানো হয় না,
        // শুধু জানিয়ে রাখা হয় যাতে "মোট মিনিট" রিপোর্টে সামান্য কম দেখালে
        // কেউ বিভ্রান্ত না হন
        notice(
          T(
            "শেষ কয়েক মিনিটের হিসাব সেভ করতে সমস্যা হয়েছে (হাজিরা প্রভাবিত হয়নি)।",
            "Trouble saving the last minute or so (your attendance is not affected).",
          ),
        );
      }
      /* ⚠️ আগে এখানে await refreshPresence() ছিল। প্যানেল তো এখনই বন্ধ হয়ে
         যাচ্ছে, তাই এই প্যানেলের presence হালনাগাদ করে কোনো লাভ নেই — শুধু
         একটা বাড়তি নেটওয়ার্ক কল শেষ হওয়ার অপেক্ষায় পর্দা আটকে থাকত। বের
         হওয়ার পর onPanelExit এমনিতেই ক্লাস-তালিকা নতুন করে আনে। */
    }
    onExit(mode === "finish");
  };

  /* ক্লাস সত্যিই শেষ করা — নিছক বেরিয়ে যাওয়া নয়। সার্ভারে জমে থাকা মিনিট
     হাজিরায় বসে, হাজিরা পাকা হয়, ক্লাসটি "সম্পন্ন" হিসেবে তালিকাবদ্ধ হয়, আর
     শিক্ষার্থীর কাছে রিজয়েন লিংক খুলে যায়।

     দেরির কারণ ছিল: leave → refreshPresence → loadClasses — তিনটি কল একের পর
     এক শেষ হওয়ার পরই কেবল পর্দা বদলাত, ধীর নেটে কয়েক সেকেন্ড ঠায় বসে থাকতে
     হতো এবং মনে হতো বাটনটাই কাজ করছে না। এখন পর্দা সাথে সাথেই বদলায়, সার্ভারের
     কাজ পেছনে চলতে থাকে। মিনিটের হিসাব প্রতি ৬০ সেকেন্ডে এমনিতেই সেভ হয়ে
     থাকে, তাই কিছু হারায় না। */
  /* জুমের বিনামূল্যের মিটিংয়ের সময়সীমার কারণে একটি ক্লাস দুই পর্বে হয় — ১ম
     লিংকে ১ম পর্ব, ২য় লিংকে ২য় পর্ব। দুই পর্ব মিলেই একটি পূর্ণ ক্লাস। রিজয়েন
     খোলা আছে কিনা, সেটাই বলে দেয় এখন কোন পর্বে আছি। */
  const lastPart = !!k.rejoinActive;
  const finishClass = () =>
    askConfirm(
      lastPart
        ? T(
            "সত্যিই কি ক্লাস শেষ করতে চান?" +
              "\n\n" +
              "এবার পুরো ক্লাসটি শেষ হবে — হাজিরা ও ক্লাসের হিসাব চূড়ান্ত হয়ে " +
              "ক্লাসটি \"সম্পন্ন\" হিসেবে তালিকাভুক্ত হবে এবং আজকের ক্লাসের " +
              "তালিকা থেকে সরে যাবে।",
            "Do you really want to end the class?" +
              "\n\n" +
              "This finishes the whole class — the attendance and class " +
              "record will be finalised, the class marked as completed and " +
              "removed from today's list.",
          )
        : T(
            "সত্যিই কি ১ম পর্ব শেষ করতে চান?" +
              "\n\n" +
              "শেষ করলে শিক্ষার্থীদের পোর্টালে সাথে সাথেই রিজয়েন বাটন চলে " +
              "যাবে। এরপর আপনি \"🔁 রিজয়েন করুন\" চেপে ২য় পর্ব শুরু করবেন।" +
              "\n\n" +
              "ক্লাসটি এখনো \"সম্পন্ন\" হবে না, আজকের তালিকাতেই থাকবে — ২য় " +
              "পর্ব শেষ করলে তবেই সম্পন্ন হবে।",
            "Do you really want to end the first part?" +
              "\n\n" +
              "Your students will get the rejoin button right away. Then " +
              "press \"🔁 Rejoin\" to start the second part." +
              "\n\n" +
              "The class will not be marked completed yet — it stays in " +
              "today's list until the second part is finished.",
          ),
      async () => {
        setEnding(true);
        setInMeeting(false);
        const min = Math.max(
          0,
          Math.round((computeSegSec() - savedSecRef.current) / 60),
        );
        activeSinceRef.current = null;
        accumulatedMsRef.current = 0;
        savedSecRef.current = 0;
        onExit(true); // পর্দা এখনই বদলায়
        if (!usingApi) return;
        try {
          if (min >= 1) await api.checkpointClass(k.id, min).catch(() => {});
          await api.finishClass(k.id);
          onFinished?.();
        } catch (e) {
          notice(
            T(
              "ক্লাস শেষ করার খবরটা সার্ভারে পৌঁছায়নি — " +
                (e?.data?.detail || e?.data?.error || e?.message || "") +
                " আবার চেষ্টা করুন, অথবা পরিচালককে ক্লাসটি \"সম্পন্ন\" " +
                "চিহ্নিত করতে বলুন।",
              "Ending the class didn't reach the server — please try again, " +
                "or ask the director to mark the class as completed.",
            ),
          );
        }
      },
      {
        yes: lastPart
          ? T("হ্যাঁ, ক্লাস শেষ করুন", "Yes, end the class")
          : T("হ্যাঁ, ১ম পর্ব শেষ করুন", "Yes, end the first part"),
        no: T("না, ক্লাসে ফিরে যান", "No, back to class"),
      },
    );

  // জুম বাইরের অ্যাপ/ট্যাব — তাই "মিটিং শেষ হলো" এমন সরাসরি কোনো সিগন্যাল ব্রাউজার
  // পায় না। তবে জুমে গেলে এই ট্যাব/উইন্ডো ব্যাকগ্রাউন্ডে চলে যায় (hidden), আর
  // জুম থেকে বের হয়ে এই ট্যাবে ফিরে এলে আবার visible হয় — এটাই সবচেয়ে নির্ভরযোগ্য
  // সংকেত যে স্টুডেন্ট জুম মিটিং কেটে দিয়েছেন। তাই কোনো বাটন চাপা ছাড়াই, জুম থেকে
  // ফিরে এলেই অটো "ক্লাস কেমন হলো" রেটিং পপআপ চলে আসবে
  const inMeetingRef = useRef(true);
  useEffect(() => {
    inMeetingRef.current = inMeeting;
  }, [inMeeting]);
  useEffect(() => {
    // শুধু স্টুডেন্টের ক্ষেত্রে — উস্তাদ ক্লাস চলাকালীন সংক্ষিপ্ত সময়ের জন্য ট্যাব
    // বদলালে (যেমন হোয়াটসঅ্যাপ চেক করতে) যেন ভুলবশত ক্লাস/উপস্থিতি ট্র্যাকিং বন্ধ
    // না হয়ে যায় — শুধু স্টুডেন্টের জুম-থেকে-ফেরার সংকেতেই রেটিং পপআপ প্রাসঙ্গিক
    if (user.role !== "student") return;
    // কিছু মোবাইল ব্রাউজার/ওয়েবভিউতে visibilitychange/blur-focus ইভেন্ট সবসময়
    // নির্ভরযোগ্যভাবে আসে না — তাই ইভেন্টের বদলে সরাসরি document.hidden প্রপার্টি
    // পোল (poll) করি, যা প্রায় সব ব্রাউজারে ঠিকভাবে কাজ করে
    let wasHidden = document.hidden;
    let hiddenAt = document.hidden ? Date.now() : null;
    const iv = setInterval(() => {
      const isHidden = document.hidden;
      if (isHidden && !wasHidden) {
        hiddenAt = Date.now();
      } else if (!isHidden && wasHidden) {
        // অন্তত ৩ সেকেন্ড আগে ট্যাবটা hidden হয়েছিল মানে সত্যিই জুমে/অন্য
        // অ্যাপে গিয়েছিলেন (হুট করে দ্রুত ট্যাব বদলালে ধরা হবে না) — কিন্তু
        // সরাসরি ক্লাস শেষ করে দিই না, বরং continue নাকি end জিজ্ঞেস করি
        if (hiddenAt && Date.now() - hiddenAt >= 3000 && inMeetingRef.current) {
          setShowContinuePrompt(true);
        }
        hiddenAt = null;
      }
      wasHidden = isHidden;
    }, 1200);
    return () => clearInterval(iv);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // উস্তাদ "ক্লাস শেষ করুন" চাপলে ব্যাকএন্ডে তাঁর segment_start মুছে যায় — অর্থাৎ
  // teacher_active মিথ্যা হয়ে যায়। এটাই একমাত্র সংকেত যাতে শিক্ষার্থীর ক্লাসও
  // নিজে থেকে শেষ হয়ে যায় (রেটিং পপআপসহ), আলাদা করে তাকে কিছু চাপতে হবে না।
  //
  // ⚠️ এটা কোনো সময়/নিষ্ক্রিয়তার অনুমান নয় — নেট সমস্যা, ট্যাব বদল, পোর্টালের
  // অন্য পেইজে যাওয়া, এমনকি ব্রাউজার বন্ধ করা — কোনোটাতেই segment_start মোছে
  // না (উপরের unmount cleanup এখন checkpoint ডাকে, leave নয়)। কেবল উস্তাদ
  // ইচ্ছা করে "ক্লাস শেষ করুন" চাপলেই এটা ঘটে। তাই এখানে কোনো টাইমআউট নেই।
  //
  // দুটি প্রহরী রাখা হয়েছে:
  //   (১) এই বসায় উস্তাদকে অন্তত একবার উপস্থিত দেখা গেছে — নইলে উস্তাদ আসার
  //       আগেই জয়েন করা শিক্ষার্থী সাথে সাথেই বেরিয়ে যেত,
  //   (২) presence চেক তখন ব্যর্থ হচ্ছে না — নেট গোলমালে পুরনো তথ্য দেখে
  //       ভুল সিদ্ধান্ত যেন না হয়।
  const teacherSeenRef = useRef(false);
  useEffect(() => {
    if (user.role !== "student" || !usingApi || !inMeeting || !presence) return;
    if (presence.ta) {
      teacherSeenRef.current = true;
      return;
    }
    if (!teacherSeenRef.current || presenceStale) return;
    notice(T("উস্তাদ ক্লাস শেষ করেছেন।", "The teacher has ended the class."));
    endSegment("finish");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [presence, presenceStale, inMeeting]);

  // স্টুডেন্ট জুম থেকে ফিরে এসেছেন — সরাসরি ক্লাস শেষ না করে জিজ্ঞেস করি
  if (showContinuePrompt)
    return (
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 250,
          background: "rgba(18,63,40,.6)",
          display: "grid",
          placeItems: "center",
          padding: 16,
        }}
      >
        <div
          style={{
            background: "#fff",
            borderRadius: 18,
            maxWidth: 380,
            width: "100%",
            padding: 26,
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 42 }}>🤔</div>
          <div
            style={{
              fontWeight: 800,
              fontSize: 18,
              color: C.emerald,
              marginTop: 6,
            }}
          >
            Have you finished today's class?
          </div>
          <div
            style={{
              fontSize: 13.5,
              color: C.text,
              margin: "8px 0 20px",
              lineHeight: 1.6,
            }}
          >
            You've come back to this tab — do you want to continue the class,
            or is it finished?
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Btn
              kind="gold"
              style={{ flex: 1, justifyContent: "center" }}
              onClick={() => setShowContinuePrompt(false)}
            >
              ▶️ Continue Class
            </Btn>
            <Btn
              kind="soft"
              style={{ flex: 1, justifyContent: "center" }}
              onClick={() => {
                setShowContinuePrompt(false);
                endSegment("finish");
              }}
            >
              ✅ End Class
            </Btn>
          </div>
        </div>
      </div>
    );

  return (
    <div style={{ marginTop: 6, fontSize: 13 }}>
      {joinError && (
        <div style={{ color: C.red, fontWeight: 700, marginBottom: 4 }}>
          {T(
            "⚠️ আপনার জয়েন ব্যাকএন্ডে সংরক্ষণ করা যায়নি — এই ক্লাসের সাথে আপনার অ্যাকাউন্ট ঠিকভাবে যুক্ত কিনা পরিচালককে জানান।",
            "⚠️ Your join couldn't be recorded — please tell the director if your account isn't properly linked to this class.",
          )}
        </div>
      )}
      {presenceStale && !joinError && (
        <div style={{ color: C.red, fontWeight: 700, marginBottom: 4 }}>
          {T(
            "⚠️ সংযোগ চেক করতে সমস্যা হচ্ছে — ইন্টারনেট সংযোগ যাচাই করুন। 🔄 বাটনে চেপে আবার চেষ্টা করুন।",
            "⚠️ Trouble checking connection status — please check your internet. Tap 🔄 to try again.",
          )}
        </div>
      )}
      {/* দুটো আলাদা তথ্য, তাই আলাদা করেই দেখাই —
          (১) হাজিরা: একবার নিশ্চিত হলে চিরকালের জন্য নিশ্চিত, কখনো ফিরিয়ে
              নেওয়া হয় না। তাই সবুজ লেখাটা থেকেই যায়।
          (২) এই মুহূর্তে অন্যজন মিটিংয়ে আছেন কিনা — এটা বদলাতে থাকে।
          আগে দুটোকে এক করে ফেলা হয়েছিল: হাজিরা নিশ্চিত হয়ে গেলে লাইভ
          অবস্থার লেখাটা চাপা পড়ে যেত, ফলে অন্যজন সত্যিই না থাকলেও
          "✓ হাজিরা নিশ্চিত" দেখে মনে হতো তিনি আছেন। */}
      {done && (
        <div style={{ fontWeight: 800, color: C.green }}>
          ✓ Teacher &amp; student join confirmed
        </div>
      )}
      {!bothIn ? (
        <span style={{ fontWeight: 700, color: C.gold }}>
          {T(
            `⏳ ${user.role === "teacher" ? "শিক্ষার্থীর" : "উস্তাদের"} জয়েনের অপেক্ষায়…`,
            `⏳ Waiting for ${user.role === "teacher" ? "student" : "teacher"} to join…`,
          )}
          <button
            onClick={refreshPresence}
            title={T("এখনই আবার চেক করুন", "Check again now")}
            style={{
              marginLeft: 8,
              border: "none",
              background: "none",
              cursor: "pointer",
              fontSize: 13,
              color: C.emerald,
              fontWeight: 700,
            }}
          >
            🔄
          </button>
        </span>
      ) : (
        !done && (
          <span style={{ fontWeight: 800, color: C.gold }}>
            Confirming join…
          </span>
        )
      )}
      {/* উস্তাদের দুটি বাটন — কাজ দুরকম, তাই আলাদা:
            ✅ ক্লাস শেষ করুন → সত্যিকারের সমাপ্তি। নিশ্চিত করার প্রশ্নের পর
               সার্ভারে হাজিরা ও মিনিট চূড়ান্ত হয়, ক্লাস "সম্পন্ন" হয়, আর
               শিক্ষার্থীর কাছে রিজয়েন লিংক খুলে যায়।
            🔄 পুনঃসংযোগ → শুধু নিজে বেরিয়ে যাওয়া (আগে এটাই "ক্লাস শেষ করুন"
               নামে ছিল)। নেট কেটে গেলে বেরিয়ে গিয়ে একই ক্লাসে ফেরার জন্য —
               ক্লাস শেষ হয় না।
          শিক্ষার্থীর কাছে কোনোটিই দেখানো হয় না — "ক্লাস শেষ" তাদের কাছে
          বিভ্রান্তিকর ছিল। উস্তাদ শেষ করলে উপরের হুক শিক্ষার্থীর ক্লাস
          আপনাআপনি শেষ করে দেয়; আর জুম থেকে ফিরলে "Have you finished today's
          class?" পপআপেই সে নিজে শেষ করতে পারে। */}
      {user.role !== "student" && (
        <div style={{ marginTop: 10 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {/* সত্যিকারের "শেষ" — হাজিরা ও ক্লাসের হিসাব চূড়ান্ত হয় */}
            <Btn
              sm
              kind="danger"
              onClick={ending ? undefined : finishClass}
              style={{ opacity: ending ? 0.6 : 1 }}
            >
              {/* কোন পর্বে আছি সেটা বাটনেই লেখা থাকে — উস্তাদ চাপার আগেই
                  বোঝেন এই চাপে ক্লাসটা পুরোপুরি শেষ হবে, নাকি ২য় পর্ব বাকি
                  থাকবে */}
              {ending
                ? T("শেষ হচ্ছে…", "Ending…")
                : lastPart
                  ? T("✅ ক্লাস শেষ করুন", "✅ End Class")
                  : T("✅ ১ম পর্ব শেষ করুন", "✅ End First Part")}
            </Btn>
            {/* নেট কেটে যাওয়া বা অন্য কারণে বেরিয়ে গিয়ে আবার একই ক্লাসে ফেরার
                দরকার হলে — এতে ক্লাস শেষ হয় না, হাজিরাও চূড়ান্ত হয় না।
                এটাই আগে "ক্লাস শেষ করুন" বাটনটা করত। */}
            <Btn sm kind="soft" onClick={() => endSegment("manual")}>
              {T("🔄 পুনঃসংযোগ", "🔄 Reconnect")}
            </Btn>
          </div>
          <div
            style={{
              fontSize: 11.5,
              color: C.muted,
              marginTop: 6,
              lineHeight: 1.55,
            }}
          >
            {T(
              "🔄 পুনঃসংযোগ — ক্লাস শেষ হবে না। নেট কেটে গেলে বা বেরিয়ে যেতে " +
                "হলে এটি চাপুন, পরে একই ক্লাসে আবার জয়েন করতে পারবেন।",
              "🔄 Reconnect — this does not end the class. Use it if your " +
                "connection drops, then rejoin the same class.",
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* পরিচালকের ম্যানুয়াল হাজিরা — ক্লাসের স্টুডেন্টদের হাজিরা দিন/সরান */
function AttnMarkModal({ k, nameOf, onClose }) {
  const [rows, setRows] = useState([]);
  const load = () =>
    api
      .classPresence(k.id)
      .then((p) => setRows(p.attendance || []))
      .catch(() => setRows([]));
  useEffect(() => {
    load();
  }, []);
  const ids = k.studentIds && k.studentIds.length ? k.studentIds : [];
  const list = ids.length ? ids : rows.map((r) => r.user);
  const rowFor = (sid) => rows.find((r) => String(r.user) === String(sid));
  const toggle = async (sid, present) => {
    try {
      await api.markAttendance(k.id, sid, present);
      await load();
    } catch {
      /* উপেক্ষা */
    }
  };
  return (
    <Modal
      title={`✋ ম্যানুয়াল হাজিরা — ${k.courseName || ""}`}
      onClose={onClose}
    >
      <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>
        ৪৫ মিনিটের কম হলেও পরিচালক এখানে হাজিরা দিতে/সরাতে পারবেন।
      </div>
      {list.length === 0 && (
        <div style={{ color: C.muted }}>এই ক্লাসে কোনো স্টুডেন্ট নেই।</div>
      )}
      {list.map((sid, i) => {
        const r = rowFor(sid);
        const present = r?.present;
        return (
          <div
            key={sid}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 10px",
              borderRadius: 10,
              background: C.cream,
              marginBottom: 6,
              flexWrap: "wrap",
            }}
          >
            <span style={{ flex: 1, fontWeight: 600, fontSize: 13.5, minWidth: 120 }}>
              {(k.studentNames && k.studentNames[i]) || nameOf(sid)}
            </span>
            <span style={{ fontSize: 12, color: C.muted }}>
              {bn(r?.minutes || 0)} মি
            </span>
            {present ? (
              <Tag>হাজির ✔</Tag>
            ) : (
              <Tag color={C.muted} bg="#fff">
                অনুপস্থিত
              </Tag>
            )}
            <Btn
              sm
              kind={present ? "danger" : "primary"}
              onClick={() => toggle(sid, !present)}
            >
              {present ? "সরান" : "হাজিরা দিন"}
            </Btn>
          </div>
        );
      })}
    </Modal>
  );
}

function ClassesView({
  db,
  setDb,
  user,
  courses,
  autoJoinId,
  onAutoJoinConsumed,
}) {
  // শিক্ষার্থী বাংলা বোঝে না বলে তাদের জন্য ইংরেজি; উস্তাদ/এডমিন/পরিচালকের জন্য বাংলাই থাকছে
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [show, setShow] = usePersistedState("cls_show", false);
  const blankSched = () => ({
    courseId: courses[0]?.id,
    date: todayISO(),
    time: "17:00",
    dur: 60,
    lectureNo: 1,
    zoom: "https://zoom.us/j/",
    zoom2: "", // রিজয়েন লিংক (ঐচ্ছিক) — উস্তাদ+স্টুডেন্ট ১ম লিংকে একবার জয়েন করার পর এই লিংকেই আবার জয়েন হবে
    kind: "মেকআপ ক্লাস",
    teacherId: courses[0]?.teacherId,
    studentIds: [],
    req: "",
  });
  const [f, setF] = usePersistedState("cls_f", blankSched);
  const [editId, setEditId] = usePersistedState("cls_editId", null); // এডিট — কেবল এডমিন/পরিচালক
  const [joined, setJoined] = useState(null); // {classId}
  const [rate, setRate] = useState(null); // ক্লাস শেষে মূল্যায়ন পপআপ
  const [attnMark, setAttnMark] = useState(null); // পরিচালকের ম্যানুয়াল হাজিরা মডাল (কোন ক্লাস)
  const [apiClasses, setApiClasses] = useState(null); // null হলে mock db.classes ব্যবহার হয়
  const [classesLoading, setClassesLoading] = useState(true);
  const [loadError, setLoadError] = useState(""); // লোড ব্যর্থ হলে কারণ
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const loadClasses = async () => {
    try {
      setApiClasses((await api.classes()).map(adaptClass));
      setLoadError("");
    } catch (e) {
      setApiClasses(null);
      // ব্যর্থ হলে কারণটা জানিয়ে দিই — নইলে শুধু ফাঁকা তালিকা দেখে মনে হতো
      // "কোনো ক্লাস নেই", অথচ আসলে সার্ভার থেকে আনাই যায়নি
      setLoadError(e?.data?.error || e?.message || "সার্ভার থেকে ক্লাস আনা যায়নি");
    } finally {
      // ব্যর্থ হলেও লোডিং শেষ — নইলে "লোড হচ্ছে" চিরকাল আটকে থাকত
      setClassesLoading(false);
    }
  };
  useEffect(() => {
    loadClasses();
  }, [user?.id]);
  useEffect(() => {
    // প্রতি ২০ সেকেন্ডে তালিকা রিফ্রেশ — সবার জন্যই। দুটো কারণে জরুরি:
    // ১) এডমিন/পরিচালকের "🔴 ক্লাস চলছে" লাইভ-স্ট্যাটাস তাজা থাকে
    // ২) কোন জুম লিংক (১ম নাকি ২য়) দেখাতে হবে তা উস্তাদ ও শিক্ষার্থীর
    //    স্ক্রিনে দ্রুত মিলে যায় — নইলে একজন পুরনো তথ্য নিয়ে বসে থেকে ভিন্ন
    //    লিংকে ঢুকে পড়তে পারতেন
    // ট্যাব লুকানো থাকলে থেমে থাকে, ফিরে এলেই সাথে সাথে একবার চলে — উপরের
    // দুটো কারণই তখনই প্রাসঙ্গিক যখন পর্দাটা সত্যিই কেউ দেখছেন
    return visiblePoll(loadClasses, 20000);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);
  useEffect(() => {
    // ক্লাস শিডিউলের জন্য আসল উস্তাদ/স্টুডেন্ট তালিকা (এডমিন/পরিচালক)
    if (!isAdm(user)) return;
    api
      .allTeachers()
      .then((d) => setTeachers(d.map(adaptPerson)))
      .catch(() => setTeachers([]));
    api
      .allStudents()
      .then((d) => setStudents(d.map(adaptPerson)))
      .catch(() => setStudents([]));
  }, [user?.id]);
  useEffect(() => {
    // লাইভ পপআপ থেকে এলে হাজিরা টাইমার অটো চালু
    if (autoJoinId) {
      setJoined({ classId: autoJoinId });
      onAutoJoinConsumed && onAutoJoinConsumed();
    }
  }, [autoJoinId]);
  const usingApi = apiClasses !== null;
  const teacherList = (() => {
    const m = new Map();
    teachers.forEach((t) => t.id != null && m.set(String(t.id), t));
    (courses || []).forEach((c) => {
      if (c.teacherId != null && !m.has(String(c.teacherId)))
        m.set(String(c.teacherId), {
          id: c.teacherId,
          name: c.teacherName || "উস্তাদ",
          sub: "",
        });
    });
    return [...m.values()];
  })();
  const nameOf = (id) =>
    (
      teachers.find((t) => t.id === id) ||
      students.find((s) => s.id === id) ||
      userById(id)
    ).name || "—";
  // ব্যাকএন্ড আগেই রোল অনুযায়ী ফিল্টার করে দেয়; লোড হওয়ার আগে খালি (লোডার দেখায়)
  // ⚠️ আগে এটা `apiClasses === null` থেকে হিসাব হতো — কিন্তু লোড ব্যর্থ হলেও
  // apiClasses null-ই থাকে, তাই "লোড হচ্ছে" কখনো শেষ হতো না (উস্তাদের পোর্টালে
  // চিরকাল ঘুরত)। এখন আলাদা স্টেট — ব্যর্থ হোক বা সফল, একবার শেষ মানে শেষ।
  const mine = (apiClasses || []).sort((a, b) =>
    (a.date + a.time).localeCompare(b.date + b.time),
  );
  const today = mine.filter(
    (k) => k.date === todayISO() && k.status !== "done",
  );
  // "আসন্ন" শুধু সামনের ৭ দিন, "বিগত" শুধু গত ৩ দিন — ডাটা মোছা হয় না (সার্ভারে/DB-তে সবই থাকে),
  // শুধু এই তালিকা দুটো ছোট-পরিষ্কার রাখতে দেখানোর সীমা টানা হলো
  const upcoming = mine.filter(
    (k) => k.date > todayISO() && k.date <= addDays(7),
  );
  const past = mine.filter(
    (k) =>
      (k.status === "done" || k.date < todayISO()) && k.date >= addDays(-3),
  );

  const join = (k) => {
    // জুম খোলে অ্যাংকর লিংকে (নিচে <a>); বাকি সব (presence/হাজিরা) LiveClassPanel সামলায়।
    // ⚠️ কিন্তু প্যানেল আগে থেকেই খোলা থাকলে (ঠিক যেমন রিজয়েনের সময়) সে আর নতুন
    // করে মাউন্ট হয় না, তাই তার ভেতরের joinClass কলটাও আর চলে না — ফলে কেউ
    // রিজয়েন চেপে ২য় লিংকে ঢুকলেও সার্ভারে "আবার ঢুকলাম" জানানো হতো না, আর
    // অন্যপাশে "জয়েনের অপেক্ষায়…" রয়ে যেত। তাই এখানে সরাসরি একবার জানিয়ে দিই।
    // ব্যাকএন্ডের join আইডেম্পোটেন্ট (segment_start আগে থেকে থাকলে হাত দেয় না),
    // তাই বাড়তি কল করলেও কোনো ক্ষতি নেই।
    setJoined({ classId: k.id });
    if (usingApi)
      api.joinClass(k.id).catch(() => {
        /* প্যানেল নিজেই তার joinClass-এর ব্যর্থতা স্পষ্ট করে জানায় — এটা
           কেবল বাড়তি নিশ্চয়তা, তাই এখানে দ্বিতীয়বার বিরক্ত করি না */
      });
  };
  // উস্তাদ "🔁 রিজয়েন" চাপলেন — জুম খোলে অ্যাংকর লিংকে, পাশাপাশি সার্ভারকে
  // জানিয়ে দিই যাতে শিক্ষার্থীদের কাছেও ২য় লিংক খুলে যায় (তার আগে তারা শুধু
  // "Teacher is joining, please wait" দেখেন — তাই কেউ আলাদা মিটিংয়ে যান না)
  const openRejoinFor = async (k) => {
    setJoined({ classId: k.id });
    try {
      await api.openRejoin(k.id);
      await loadClasses();
    } catch (e) {
      notice(
        "রিজয়েন চালু করতে ব্যর্থ — শিক্ষার্থীরা এখনো ১ম লিংকই দেখছেন। " +
          (e?.data?.error || e?.message || "আবার চেষ্টা করুন"),
      );
    }
  };
  // উস্তাদ জয়েন বা রিজয়েন — যেটাই চাপুন, আগে মনে করিয়ে দেওয়া হয় যে তাঁর
  // ডিভাইসের জুম অ্যাপে সঠিক (হোস্ট) অ্যাকাউন্টে সুইচ করা আছে কিনা। ওয়েবসাইট
  // থেকে এটা যাচাই করা প্রযুক্তিগতভাবে সম্ভব নয় (জুম আলাদা অ্যাপ), তাই ভুল
  // হওয়ার আগেই চোখে পড়ার ব্যবস্থা। "হ্যাঁ" চাপার ক্লিকটাই ব্যবহারকারীর নিজের
  // ক্লিক, তাই সেখান থেকে window.open করলে ব্রাউজার পপআপ ব্লক করে না।
  const openZoomLink = (link) => {
    let win = null;
    try {
      win = window.open(link, "_blank", "noopener");
    } catch {
      /* নিচে জানিয়ে দিচ্ছি */
    }
    if (!win) {
      notice("ব্রাউজার নতুন ট্যাব খুলতে দেয়নি — জুম লিংকটি নিজে খুলে নিন: " + link);
    }
  };
  const HOST_CHECK =
    "জুম খোলার আগে একটু নিশ্চিত হয়ে নিন — আপনার ডিভাইসের জুম অ্যাপে এই ক্লাসের " +
    "নির্ধারিত হোস্ট অ্যাকাউন্টেই সাইন-ইন করা আছে তো? অন্য কোনো অ্যাকাউন্টে সুইচ " +
    "করা থাকলে আপনি হোস্ট হিসেবে ঢুকতে পারবেন না এবং শিক্ষার্থীরা অপেক্ষায় থেকে যাবে।";
  const confirmJoin = (k) =>
    askConfirm(HOST_CHECK + "\n\nসব ঠিক থাকলে জুম খুলে দিচ্ছি।", () => {
      openZoomLink(k.zoom);
      join(k);
    });
  const confirmRejoin = (k) =>
    askConfirm(
      HOST_CHECK +
        "\n\nসব ঠিক থাকলে ২য় জুম খুলে দিচ্ছি। এরপর শিক্ষার্থীদের পোর্টাল " +
        "থেকে ১ম জয়েন বাটন সরে গিয়ে রিজয়েন বাটন চলে আসবে।",
      () => {
        openZoomLink(k.zoom2 || k.zoom);
        openRejoinFor(k);
      },
    );
  // এডমিন/পরিচালক → আজকের ক্লাসের টিচার ও শিক্ষার্থী উভয়কে জয়েন-করার রিমাইন্ডার
  // WhatsApp (ইংরেজি, ইসলামিক টোন) — একই বাটনে একসাথে দুজনকেই পাঠানো হয়
  const notifyAll = (k, c, kStudents) => {
    const teacher = teachers.find(
      (t) => String(t.id) === String(k.teacherId || c.teacherId),
    );
    const studentTargets = kStudents
      .map((id) => students.find((s) => String(s.id) === String(id)))
      .filter((s) => s && s.phone);
    const targets = [
      ...(teacher && teacher.phone ? [teacher] : []),
      ...studentTargets,
    ];
    if (!targets.length)
      return notice("এই ক্লাসের টিচার/শিক্ষার্থীর কোনো ফোন নম্বর পাওয়া যায়নি।");
    const courseName = c.name || k.courseName || "your class";
    targets.forEach((p, i) => {
      const text =
        `Assalamu Alaikum Warahmatullah,\n\n` +
        `Dear ${p.name},\n\n` +
        `This is a reminder that you have a class today — "${courseName}" at ${k.time}.\n\n` +
        `*Please join on time insaallah.*\n\n` +
        `Jazakallahu Khairan Fid-darayn.\n— Tarbiyatul Quran Academy.`;
      const phone = p.phone.replace(/[^\d]/g, "");
      setTimeout(
        () =>
          window.open(
            `https://wa.me/${phone}?text=${encodeURIComponent(text)}`,
            "_blank",
          ),
        i * 400,
      );
    });
    notice(`✔ ${bn(targets.length)} জনকে WhatsApp পাঠানো হচ্ছে`);
  };
  // প্যানেল থেকে বেরোলে (Leave & Save / End Class) — স্টুডেন্ট হলে রেটিং পপআপ
  const onPanelExit = async (finished) => {
    const cls = joined?.classId;
    const k = (usingApi ? apiClasses : db.classes).find((x) => x.id === cls);
    // ইন-ক্লাস প্যানেল বন্ধ করার আগে ক্লাস-তালিকা রিফ্রেশ করে নিই — k.attendance
    // (কে কে জয়েন করেছেন) শুধু পেজ-লোডে একবার আসত, ক্লাস চলাকালীন ব্যাকএন্ডে
    // দুজনের হাজিরা নিশ্চিত হলেও এখানে পুরনো (খালি) ডেটাই থেকে যেত। ফলে
    // বের হওয়ার পর "দুজনেই জয়েন করেছেন" বোঝা যেত না, আর "🔁 রিজয়েন করুন"-এর
    // বদলে আবার "🎥 জুমে জয়েন করুন" দেখাত
    /* ⚠️ আগে এই loadClasses()-এর জন্য await করা হতো, ফলে ধীর নেটে বাটন চাপার
       পরেও কয়েক সেকেন্ড প্যানেলটা খোলা থেকে যেত — ব্যবহারকারীর মনে হতো কিছুই
       হয়নি। এখন প্যানেল আগে বন্ধ হয়, তালিকা পেছনে হালনাগাদ হয়ে নিজে থেকেই
       "🔁 রিজয়েন করুন" দেখাতে শুরু করে। */
    setJoined(null);
    if (usingApi) loadClasses().catch(() => {});
    if (finished && user.role === "student" && k) {
      const c = courseById(courses, k.courseId);
      setRate({
        classId: k.id,
        courseId: c.id || k.courseId,
        teacherId: c.teacherId || k.teacherId,
        courseName: c.name || k.courseName,
      });
    }
  };
  const submitRating = async (stars, comment) => {
    try {
      await api.rateClass({
        session: rate.classId,
        course: rate.courseId,
        teacher: rate.teacherId,
        stars,
        comment,
      });
      notice("✔ রেটিং জমা হয়েছে, ধন্যবাদ।");
    } catch (e) {
      notice(
        "রেটিং জমা দিতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
      return;
    }
    setRate(null);
  };
  const delClass = async (id) => {
    if (usingApi) {
      try {
        await api.deleteClass(id);
        await loadClasses();
      } catch (e) {
        notice(
          "ক্লাস মুছতে ব্যর্থ — " +
            (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
        );
      }
      return;
    }
    setDb((d) => ({ ...d, classes: d.classes.filter((k) => k.id !== id) }));
  };
  // পরিচালক/এডমিন আজকের ও বিগত ক্লাসকে "সম্পন্ন" চিহ্নিত করতে পারবেন (ভবিষ্যতের
  // "আসন্ন" ক্লাস নয়) — আজকের ক্লাস "সম্পন্ন" করলে তা "আজকের ক্লাস" তালিকা থেকে
  // সরে "বিগত"-এ চলে যাবে (today ফিল্টার status!=="done")
  const setStatus = async (k, status) => {
    try {
      await api.editClass(k.id, { status });
      await loadClasses();
    } catch (e) {
      notice("আপডেট ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
    }
  };
  // অটো জয়েন/রিজয়েন-নির্ধারণ (দুজনের হাজিরার ওপর ভিত্তি করে) কোনো কারণে ঠিক
  // না এলে, পরিচালক/এডমিন এখান থেকে জয়েন বা রিজয়েন — যেকোনো একটা লিংক
  // ম্যানুয়ালি জোর করে চালু, বা "auto"-তে ফিরিয়ে দিতে পারেন — হাজিরার ডেটা বদলায় না
  const setJoinMode = async (k, mode) => {
    try {
      await api.setClassJoinMode(k.id, mode);
      await loadClasses();
    } catch (e) {
      notice("ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
    }
  };
  const postponeOne = (k) => {
    askConfirm(
      "ক্লাসটি স্থগিত করবেন? উস্তাদ, স্টুডেন্ট সবার পোর্টালে সাথে সাথে আপডেট হবে।",
      async () => {
        try {
          await api.postponeClass(k.id);
          await loadClasses();
        } catch (e) {
          notice("ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
        }
      },
    );
  };
  const saveClass = async (students) => {
    const c = courseById(courses, f.courseId);
    if (usingApi) {
      // আসল persist — দুই ডিভাইসেই দেখা যাবে, রিফ্রেশেও থাকবে
      try {
        if (editId) await api.editClass(editId, classPayload(f, students));
        else await api.scheduleClass(classPayload(f, students));
        await loadClasses();
        setShow(false);
        setEditId(null);
        setF(blankSched());
        notice(
          editId
            ? "✔ ক্লাস আপডেট হয়েছে"
            : "✔ ক্লাস শিডিউল হয়েছে — সময় হলে পোর্টালে জয়েন অপশন আসবে",
        );
      } catch (e) {
        notice(
          "ক্লাস সেভ করতে ব্যর্থ — " +
            (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
        );
      }
      return;
    }
    if (editId) {
      // ✏️ এডিট — কেবল এডমিন/পরিচালক; তারিখ-সময় বদলালে পোর্টালের জয়েন অপশনও অটো বদলায়
      setDb((d) => ({
        ...d,
        classes: d.classes.map((x) =>
          x.id === editId
            ? {
                ...x,
                ...f,
                studentIds: students,
                dur: +f.dur,
                lectureNo: +f.lectureNo,
              }
            : x,
        ),
        notifications: [
          {
            id: uid(),
            for: [f.teacherId, ...students, "admin1", "dir1"],
            text: `✏️ [${f.kind}] ক্লাসটি আপডেট হয়েছে: ${c.name} — ${fmtDate(f.date)} ${f.time}।`,
            date: todayISO(),
            read: false,
          },
          ...d.notifications,
        ],
      }));
    } else {
      const k = {
        id: uid(),
        ...f,
        studentIds: students,
        dur: +f.dur,
        lectureNo: +f.lectureNo,
        status: "upcoming",
      };
      setDb((d) => ({
        ...d,
        classes: [...d.classes, k],
        notifications: [
          {
            id: uid(),
            for: [f.teacherId, ...students, "admin1", "dir1"],
            text: `${f.kind !== "নিয়মিত ক্লাস" ? `[${f.kind}] ` : ""}${fmtDate(f.date)} ${f.time} — ${c.name} ক্লাস নির্ধারিত হয়েছে (উস্তাদ: ${userById(f.teacherId).name})। শিক্ষার্থী: ${students.map((s) => userById(s).name).join(", ")}। সময় হলে ড্যাশবোর্ড থেকে জয়েন করুন।`,
            date: todayISO(),
            read: false,
          },
          ...d.notifications,
        ],
      }));
    }
    setShow(false);
    setEditId(null);
    setF(blankSched());
  };
  const addClass = () => {
    const c = courseById(courses, f.courseId);
    if (!f.studentIds.length) {
      // কাউকে না বাছলে আগে চুপচাপ পুরো কোর্সের সবাইকে যুক্ত করে দিত — ভুলবশত
      // অপ্রাসঙ্গিক স্টুডেন্ট ক্লাসে ঢুকে যাওয়ার কারণ ছিল এটাই; এখন স্পষ্ট
      // নিশ্চিতকরণ ছাড়া এগোবে না
      const whole = c.studentIds || [];
      const names = whole.map((sid) => nameOf(sid)).join(", ") || "কেউ নেই";
      askConfirm(
        `আপনি কোনো নির্দিষ্ট স্টুডেন্ট বাছাই করেননি — তাই "${c.name || "এই কোর্সের"}" কোর্সে ভর্তি সবাই (${names}) এই ক্লাসে যুক্ত হয়ে যাবে। এগিয়ে যাবেন?`,
        () => saveClass(whole),
      );
      return;
    }
    saveClass(f.studentIds);
  };
  const startEdit = (k) => {
    // ক্লাস এডিট — মডাল প্রি-ফিল
    setF({
      courseId: k.courseId,
      date: k.date,
      time: k.time,
      dur: k.dur,
      lectureNo: k.lectureNo,
      zoom: k.zoom,
      zoom2: k.zoom2 || "",
      kind: k.kind || "নিয়মিত ক্লাস",
      teacherId: k.teacherId || courseById(courses, k.courseId).teacherId,
      studentIds: k.studentIds || [],
      req: k.req || "",
    });
    setEditId(k.id);
    setShow(true);
  };
  const Row = (k, joinable, isToday = false) => {
    const c = courseById(courses, k.courseId);
    const lec = c.lectures?.[k.lectureNo - 1];
    const kStudents =
      k.studentIds && k.studentIds.length ? k.studentIds : c.studentIds || [];
    // joined শুধু এই ট্যাবের লোকাল স্টেট — রিফ্রেশ/লগআউট-লগইনে হারিয়ে যায়, ফলে
    // আগে সত্যিই ক্লাসে "জয়েন" থাকা অবস্থাতেও রিফ্রেশ দিলে নতুন "জয়েন করুন"
    // বাটন দেখাত। এখন সার্ভারের হাজিরা-ডেটা (segment_start এখনো সেট আছে কিনা,
    // অর্থাৎ "ক্লাস শেষ করুন" এখনো চাপা হয়নি) থেকেও একই সিদ্ধান্ত নেওয়া হয় —
    // তাই রিফ্রেশ/লগআউটেও "ক্লাসে আছি" অবস্থাটা ঠিকই থেকে যায়, যতক্ষণ না
    // সত্যিই ক্লাস শেষ করা হয়
    const myActiveRow = (k.attendance || []).some(
      (a) => String(a.user) === String(user.id) && a.active,
    );
    const isJoined = joined?.classId === k.id || (joinable && myActiveRow);
    // এই ক্লাসে অন্তত একবার জয়েন করেছে কিনা (হাজিরার সারি তৈরি হয়েছে কিনা) —
    // অপেক্ষার বার্তা শুরুতেই দেখালে শিক্ষার্থী ভুল করে জয়েন না করে বসে থাকতে
    // পারে, তাই সেটা কেবল একবার জয়েন করার পরই দেখানো হয়
    const hasJoinedOnce =
      joined?.classId === k.id ||
      (k.attendance || []).some((a) => String(a.user) === String(user.id));
    const alreadyBothJoined = bothJoinedToday(k);
    // উস্তাদের সাথে দেখা হয়ে হাজিরা পাকাপাকি নিশ্চিত হয়ে গেছে কিনা। হাজিরা
    // বসে দুজনে একসাথে মিটিংয়ে থাকা মাত্রই (_sync_mutual_presence), আর তা
    // কখনো ফিরিয়ে নেওয়া হয় না — তাই এটা সত্য হওয়া মানে "উস্তাদ এসে গেছেন"।
    const meetingDone = (k.attendance || []).some(
      (a) =>
        String(a.user) === String(user.id) && (a.present || a.marked_present),
    );
    // এই ক্লাসের উস্তাদ কিনা — উস্তাদই কেবল রিজয়েন চালু করতে পারেন
    const isTeacherOf =
      user.role === "teacher" &&
      [k.teacherId, c.teacherId].some((t) => String(t) === String(user.id));
    // এডমিন/পরিচালক এখন কোন কোন ক্লাসে উস্তাদ/স্টুডেন্ট বাস্তবে এই মুহূর্তে আছেন
    // তা দেখতে পারেন — সার্ভারের হাজিরা-ডেটা (segment_start) থেকেই সরাসরি।
    // ⚠️ কিন্তু segment_start শুধু "ক্লাস শেষ করুন" চাপলেই মোছে — কেউ ট্যাব বন্ধ
    // করে/নেট চলে গিয়ে চলে গেলে সার্ভারে "আছেন" অবস্থাটাই থেকে যায়। তাই ক্লাসের
    // নির্ধারিত সময় (শুরুর ১৫ মিনিট আগে থেকে শেষের ৩০ মিনিট পর পর্যন্ত) পার
    // হয়ে গেলে আর "চলছে" ধরা হয় না — নইলে ক্লাস শেষ হওয়ার অনেক পরেও, এমনকি
    // বিগত দিনের ক্লাসেও ভুলভাবে "🔴 ক্লাস চলছে" দেখাত
    const effTeacherId = k.teacherId ?? c.teacherId;
    const withinClassWindow = (() => {
      // "সম্পন্ন" বা "স্থগিত" চিহ্নিত ক্লাসে কখনোই "চলছে" দেখাবে না — এডমিন
      // সম্পন্ন করে দেওয়া মানেই ক্লাস শেষ, কেউ "ক্লাস শেষ করুন" চাপুক বা না চাপুক
      if (!isToday || k.status !== "upcoming") return false;
      const n = new Date();
      // ক্লাসের সময় বাংলাদেশ সময়ে সংরক্ষিত — "এখন কয়টা" হিসাবও সেভাবেই
      const nowMin =
        ((n.getUTCHours() + DHAKA_OFFSET_HOURS) % 24) * 60 + n.getUTCMinutes();
      const [sh, sm] = String(k.time || "0:0").split(":").map(Number);
      const startMin = (sh || 0) * 60 + (sm || 0);
      return nowMin >= startMin - 15 && nowMin <= startMin + (+k.dur || 60) + 30;
    })();
    const teacherLive =
      withinClassWindow &&
      (k.attendance || []).some(
        (a) => String(a.user) === String(effTeacherId) && a.active,
      );
    const liveStudentCount = withinClassWindow
      ? (k.attendance || []).filter(
          (a) => String(a.user) !== String(effTeacherId) && a.active,
        ).length
      : 0;
    return (
      <div
        key={k.id}
        style={{
          ...S.card,
          padding: 16,
          display: "flex",
          gap: 14,
          alignItems: "center",
          flexWrap: "wrap",
          borderLeft: `4px solid ${c.color || C.emerald}`,
        }}
      >
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontWeight: 800, fontSize: 15 }}>
            {c.name || k.courseName}{" "}
            <span style={{ color: C.muted, fontWeight: 600, fontSize: 12.5 }}>
              · {T(`লেকচার ${bn(k.lectureNo)}`, `Lecture ${k.lectureNo}`)}
            </span>{" "}
            {k.kind && k.kind !== "নিয়মিত ক্লাস" && (
              <Tag color={C.red} bg={C.redBg}>
                {k.kind}
              </Tag>
            )}
          </div>
          <div style={{ fontSize: 12.5, color: C.muted }}>
            {lec?.title} · {T("উস্তাদ", "Teacher")}:{" "}
            {k.teacherName || nameOf(k.teacherId || c.teacherId)}
          </div>
          {user.role !== "student" && (
            <div style={{ fontSize: 12, color: C.muted }}>
              👥 শিক্ষার্থী:{" "}
              {(k.studentNames && k.studentNames.length
                ? k.studentNames
                : kStudents.map((s) => nameOf(s))
              ).join(", ") || "—"}
            </div>
          )}
          {k.req && user.role !== "student" && (
            <div style={{ fontSize: 12, color: "#a16207", marginTop: 2 }}>
              📌 অভিভাবকের রিকোয়ারমেন্ট: {k.req}
            </div>
          )}
          {k.status === "postponed" && (
            <div
              style={{
                fontSize: 12.5,
                color: C.red,
                marginTop: 4,
                background: C.redBg,
                padding: "6px 10px",
                borderRadius: 8,
              }}
            >
              {T(
                "⛔ ক্লাসটি অনিবার্য কারণে / উস্তাদ-উস্তাদা অসুস্থ থাকার দরুন স্থগিত করা হয়েছে। পরবর্তীতে শিডিউল করে মেকআপ করা হবে ইনশাআল্লাহ।",
                "⛔ This class has been postponed due to unavoidable circumstances / the teacher being unwell. A makeup class will be scheduled soon, InshaAllah.",
              )}
            </div>
          )}
          <div style={{ fontSize: 12.5, color: C.text, marginTop: 2 }}>
            📅 {fmtDate(k.date)} · 🕐 {k.time} ·{" "}
            {T(`${bn(k.dur)} মিনিট`, `${k.dur} min`)}
          </div>
          {isAdm(user) && (teacherLive || liveStudentCount > 0) && (
            <div
              style={{
                fontSize: 12.5,
                fontWeight: 800,
                color: C.green,
                marginTop: 4,
                background: C.greenBg,
                padding: "5px 10px",
                borderRadius: 8,
                display: "inline-block",
              }}
            >
              🔴 ক্লাস চলছে — {teacherLive ? "উস্তাদ আছেন" : "উস্তাদ নেই"}
              {" · "}
              {liveStudentCount > 0
                ? `${bn(liveStudentCount)} জন স্টুডেন্ট আছে`
                : "স্টুডেন্ট নেই"}
            </div>
          )}
          {isJoined && (
            <LiveClassPanel
              k={k}
              user={user}
              usingApi={usingApi}
              onExit={onPanelExit}
              /* পর্ব শেষ হওয়ার খবর সার্ভারে পৌঁছানোর পর তালিকা আবার আনি —
                 নইলে উস্তাদের কাছে "🔁 রিজয়েন করুন" অবস্থাটা পুরনোই থেকে যেত */
              onFinished={loadClasses}
            />
          )}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {/* জয়েন (লাল) ও রিজয়েন (হলুদ) — উস্তাদ সবসময় দুটোই দেখেন, তাই
              ক্লাস চলাকালীনও ২য় লিংকে সরে যেতে পারেন। শিক্ষার্থী রিজয়েন বাটন
              দেখেন কেবল উস্তাদ সেটা চালু করার পর; তার আগে অপেক্ষার বার্তা */}
          {/* ১ম (জয়েন) লিংক — উস্তাদ সবসময় দেখেন, তাই ডিভাইস/নেট সমস্যা হলে
              যতবার খুশি ১ম লিংকেই ফিরতে পারেন। শিক্ষার্থী দেখেন যতক্ষণ না উস্তাদ
              রিজয়েন চালু করেন — খুলে গেলে তাদের কাছ থেকে ১ম লিংক সরে যায়, যাতে
              কেউ ভুল করে পুরনো মিটিংয়ে ঢুকে না পড়ে */}
          {/* উস্তাদের জয়েন — আগে হোস্ট-অ্যাকাউন্ট মনে করিয়ে দেওয়ার পপআপ, তারপর
              জুম খোলে। শিক্ষার্থীর জয়েন আগের মতোই সরাসরি লিংক (তাদের হোস্ট
              অ্যাকাউন্টের ব্যাপার নেই) */}
          {joinable && k.status !== "postponed" && isTeacherOf && (
            <Btn
              style={{ background: C.red, color: "#fff" }}
              onClick={() => confirmJoin(k)}
            >
              {T("🎥 জুমে জয়েন করুন", "🎥 Join Zoom")}
            </Btn>
          )}
          {joinable && k.status !== "postponed" && !isTeacherOf &&
            !alreadyBothJoined && (
              <a
                href={k.zoom}
                target="_blank"
                rel="noreferrer"
                onClick={() => join(k)}
                style={{ textDecoration: "none" }}
              >
                <Btn style={{ background: C.red, color: "#fff" }}>
                  {T("🎥 জুমে জয়েন করুন", "🎥 Join Zoom")}
                </Btn>
              </a>
            )}
          {joinable && k.status !== "postponed" && isTeacherOf && (
            <Btn kind="gold" onClick={() => confirmRejoin(k)}>
              {T("🔁 রিজয়েন করুন", "🔁 Rejoin")}
            </Btn>
          )}
          {joinable && k.status !== "postponed" && !isTeacherOf &&
            (alreadyBothJoined ? (
              <a
                href={k.zoom2 || k.zoom}
                target="_blank"
                rel="noreferrer"
                onClick={() => join(k)}
                style={{ textDecoration: "none" }}
              >
                <Btn kind="gold">{T("🔁 রিজয়েন করুন", "🔁 Rejoin")}</Btn>
              </a>
            ) : isJoined && !meetingDone ? (
              /* এই লেখাটা রিজয়েন বাটনের জায়গা ধরে রাখে — উস্তাদ রিজয়েন চালু
                 করলে ঠিক এখানেই "🔁 Rejoin" বাটন হয়ে যায়।
                 উস্তাদের সাথে দেখা হয়ে হাজিরা নিশ্চিত হয়ে গেলে (meetingDone)
                 লেখাটা সরে যায় — তখন "Teacher is joining, please wait" পড়ে
                 শিক্ষার্থী ভাবতেন উস্তাদ এখনো আসেননি, অথচ ক্লাস চলছে।
                 তাই এটা দেখানো হয় কেবল শিক্ষার্থী ক্লাসে ঢোকার পর, যখন
                 রিজয়েনের প্রশ্নটাই প্রাসঙ্গিক। জয়েন করার আগে (অর্থাৎ যখন
                 সামনে শুধু "🎥 Join Zoom" বাটনটাই থাকার কথা) এটা আর আসবে না —
                 আগে "একবার জয়েন করেছে কিনা" দিয়ে যাচাই হতো বলে আগের দিনের/
                 আগের বারের হাজিরার সারি থাকলেই জয়েনের সময়েও দেখাত */
              <span
                style={{
                  alignSelf: "center",
                  fontSize: 12.5,
                  fontWeight: 700,
                  color: C.gold,
                  whiteSpace: "nowrap",
                }}
              >
                ⏳ Teacher is joining, please wait
              </span>
            ) : null)}
          {isToday && isAdm(user) && k.status !== "postponed" && (
            <Btn
              sm
              kind="soft"
              onClick={() => notifyAll(k, c, kStudents)}
            >
              📨 টিচার ও স্টুডেন্টকে জানান
            </Btn>
          )}
          {isToday && isAdm(user) && k.status !== "postponed" && (
            <>
              {/* পরিচালক/এডমিনের কাছে জয়েন ও রিজয়েন — দুটোই সবসময় পাশাপাশি
                  থাকে, তাই এক ক্লিকেই যেকোনোটায় যাওয়া যায়। আগে যেটা চালু
                  থাকত সেটা লুকিয়ে যেত, ফলে দুটো একসাথে দেখা যেত না। এখন
                  চালু থাকা বাটনটা সোনালি ✓ দিয়ে চেনা যায় — নইলে দুটোই একরকম
                  দেখানোয় কোনটা এখন চালু তা বোঝার উপায় থাকত না */}
              <Btn
                sm
                kind={k.joinModeOverride === "join" ? "gold" : "soft"}
                onClick={() => setJoinMode(k, "join")}
              >
                {k.joinModeOverride === "join" ? "✓ " : ""}🎥 জয়েন লিংক জোর করে চালু
              </Btn>
              <Btn
                sm
                kind={k.joinModeOverride === "rejoin" ? "gold" : "soft"}
                onClick={() => setJoinMode(k, "rejoin")}
              >
                {k.joinModeOverride === "rejoin" ? "✓ " : ""}🔁 রিজয়েন লিংক জোর করে চালু
              </Btn>
              {/* "স্বয়ংক্রিয়ে ফিরিয়ে দিন" কেবল একটা আনডু — জোর করে চালু করা
                  অবস্থাটা এই ক্লাসের জন্যই বাতিল করে। পরের দিনের ক্লাসের জন্য
                  এটা চাপার দরকার নেই: প্রতিটি ক্লাস আলাদা রেকর্ড, আর নতুন ক্লাস
                  তৈরির সময় join_mode_override পাঠানোই হয় না (tasks.py), তাই
                  মডেলের ডিফল্ট "auto"-ই বসে — নতুন দিন নিজে থেকেই স্বয়ংক্রিয় */}
              {k.joinModeOverride !== "auto" && (
                <Btn sm kind="soft" onClick={() => setJoinMode(k, "auto")}>
                  ↩️ স্বয়ংক্রিয়ে ফিরিয়ে দিন
                </Btn>
              )}
            </>
          )}
          {isDir(user) && !isJoined && (
            <Btn sm kind="soft" onClick={() => setAttnMark(k)}>
              ✋ হাজিরা
            </Btn>
          )}
          {isAdm(user) && (
            <Btn sm kind="soft" onClick={() => startEdit(k)}>
              ✏️ এডিট
            </Btn>
          )}
          {isDir(user) && (
            <Btn sm kind="danger" onClick={() => delClass(k.id)}>
              মুছুন
            </Btn>
          )}
          {k.date > todayISO() && k.status === "upcoming" && isAdm(user) && (
            <Btn sm kind="danger" onClick={() => postponeOne(k)}>
              ⛔ স্থগিত করুন
            </Btn>
          )}
          {k.status === "postponed" && (
            <Tag color={C.red} bg={C.redBg}>
              {T("⛔ স্থগিত", "⛔ Postponed")}
            </Tag>
          )}
          {(() => {
            // আজকের ক্লাস এডমিন/পরিচালক কেউ "সম্পন্ন" চিহ্নিত না করলে সময় পার হয়ে
            // "বিগত"-এ চলে যাওয়ার পরও status="upcoming"-ই থেকে যায় — তখন সেটাকে
            // "আসন্ন" (যা এখন আর সত্যি না) না বলে "অসম্পন্ন" দেখানো হচ্ছে
            const incomplete = k.status === "upcoming" && k.date < todayISO();
            // আজকের ক্লাস "সম্পন্ন" চিহ্নিত করা এডমিন+পরিচালক দুজনেই পারবেন, কিন্তু
            // বিগত (পুরনো) ক্লাসের স্ট্যাটাস সংশোধন কেবল পরিচালকের এখতিয়ার
            const canEditStatus = k.date === todayISO() ? isAdm(user) : isDir(user);
            if (!joinable && k.date <= todayISO() && canEditStatus && k.status !== "postponed") {
              return (
                <select
                  style={{ ...S.input, width: "auto", padding: "6px 10px", fontSize: 12.5 }}
                  value={k.status}
                  onChange={(e) => setStatus(k, e.target.value)}
                >
                  <option value="upcoming">
                    {incomplete ? T("অসম্পন্ন", "Incomplete") : T("আসন্ন", "Upcoming")}
                  </option>
                  <option value="done">{T("সম্পন্ন", "Done")}</option>
                </select>
              );
            }
            if (!joinable && k.status !== "postponed") {
              return (
                <Tag
                  color={k.status === "done" ? C.green : incomplete ? C.red : C.blue}
                  bg={k.status === "done" ? C.greenBg : incomplete ? C.redBg : C.blueBg}
                >
                  {k.status === "done"
                    ? T("সম্পন্ন", "Done")
                    : incomplete
                      ? T("অসম্পন্ন", "Incomplete")
                      : T("আসন্ন", "Upcoming")}
                </Tag>
              );
            }
            return null;
          })()}
        </div>
      </div>
    );
  };
  return (
    <>
      {classesLoading && (
        <Loader text={T("ক্লাস লোড হচ্ছে", "Loading classes")} />
      )}
      {!classesLoading && loadError && (
        <div
          style={{
            ...S.card,
            borderLeft: `4px solid ${C.red}`,
            color: C.red,
            fontWeight: 700,
            marginBottom: 12,
            display: "flex",
            alignItems: "center",
            gap: 10,
            flexWrap: "wrap",
          }}
        >
          <span style={{ flex: 1, minWidth: 200 }}>
            {T(
              `⚠️ ক্লাসের তালিকা আনা যায়নি — ${loadError}। নিচে কিছু না দেখালে সেটা "ক্লাস নেই" নয়।`,
              `⚠️ Couldn't load your classes — ${loadError}. An empty list below does not mean "no classes".`,
            )}
          </span>
          <Btn
            sm
            kind="soft"
            onClick={() => {
              setClassesLoading(true);
              loadClasses();
            }}
          >
            {T("🔄 আবার চেষ্টা করুন", "🔄 Retry")}
          </Btn>
        </div>
      )}
      <Section
        title={T("আজকের ক্লাস", "Today's Classes")}
        sub={T(
          "সময় হলে এক ক্লিকে জুম মিটিং খুলে যাবে — ৪৫ মিনিটের কম থাকলে হাজিরা গণ্য হবে না",
          "The Zoom meeting will open with one click when it's time — attendance is only counted if you stay 45+ minutes",
        )}
        action={
          isAdm(user) && (
            <Btn onClick={() => setShow(true)}>+ ক্লাস শিডিউল</Btn>
          )
        }
      >
        <div style={{ display: "grid", gap: 10 }}>
          {!classesLoading && today.length === 0 && (
            <div style={{ ...S.card, textAlign: "center", color: C.muted }}>
              {T("আজ কোনো ক্লাস নেই।", "No classes today.")}
            </div>
          )}
          {today.map((k) => Row(k, user.role === "teacher" || user.role === "student", true))}
        </div>
      </Section>
      <Section
        title={T("আসন্ন ক্লাস", "Upcoming Classes")}
        sub={T("সামনের ৭ দিনের ক্লাস", "Classes in the next 7 days")}
      >
        <div style={{ display: "grid", gap: 10 }}>
          {classesLoading ? (
            <Loader text={T("লোড হচ্ছে", "Loading")} />
          ) : upcoming.length === 0 ? (
            <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>
              {T("কিছু নেই", "Nothing yet")}
            </div>
          ) : (
            upcoming.map((k) => Row(k, false))
          )}
        </div>
      </Section>
      <Section
        title={T("বিগত ক্লাস", "Past Classes")}
        sub={T(
          "গত ৩ দিনের হিস্টরি — পুরনো ক্লাসের তথ্য ডাটাবেসে সংরক্ষিতই থাকে, শুধু এখানে কম দেখানো হয়",
          "Last 3 days of history — older class records stay saved in the database, just not shown here",
        )}
      >
        <div style={{ display: "grid", gap: 10 }}>
          {past.map((k) => Row(k, false))}
        </div>
      </Section>
      {rate && (
        <RatingPopup
          courseName={rate.courseName}
          onSubmit={submitRating}
          onSkip={() => setRate(null)}
        />
      )}
      {attnMark && (
        <AttnMarkModal
          k={attnMark}
          nameOf={nameOf}
          onClose={() => setAttnMark(null)}
        />
      )}
      {show && (
        <Modal
          title={
            editId ? "✏️ ক্লাস শিডিউল এডিট করুন" : "নতুন ক্লাস শিডিউল করুন"
          }
          onClose={() => {
            setShow(false);
            setEditId(null);
            setF(blankSched());
          }}
          wide
        >
          <div
            style={{
              padding: "9px 12px",
              borderRadius: 10,
              background: C.amberBg,
              fontSize: 12,
              color: "#a16207",
              marginBottom: 12,
            }}
          >
            💡 অসুস্থতা বা অন্য কারণে ক্লাস ছুটে গেলে এখান থেকে
            মেকআপ/সাপোর্ট/রিকভারি/ট্রায়াল ক্লাস বানিয়ে দিন — তারিখ-সময়
            অনুযায়ী স্টুডেন্ট ও উস্তাদের পোর্টালে জয়েন অপশন অটো চলে যাবে।
          </div>
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}
          >
            <div>
              <label style={S.label}>ক্লাসের ধরন</label>
              <select
                style={S.input}
                value={f.kind}
                onChange={(e) => setF({ ...f, kind: e.target.value })}
              >
                {CLASS_KINDS.map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={S.label}>কোর্স</label>
              <select
                style={S.input}
                value={f.courseId}
                onChange={(e) => {
                  const c = courseById(courses, e.target.value);
                  setF({
                    ...f,
                    courseId: e.target.value,
                    teacherId: c.teacherId || f.teacherId,
                  });
                }}
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>উস্তাদ/উস্তাদা — কার কাছে পড়বে</label>
            <select
              style={S.input}
              value={f.teacherId || ""}
              onChange={(e) => setF({ ...f, teacherId: e.target.value })}
            >
              {teacherList.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} {t.sub ? `(${t.sub})` : ""}
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>
              শিক্ষার্থী বাছাই করুন — এক এক করে ({bn(f.studentIds.length)} জন
              নির্বাচিত; কাউকে না বাছলে কোর্সের সবাই)
            </label>
            <StudentPicker
              selected={f.studentIds}
              people={students}
              onToggle={(id) =>
                setF({
                  ...f,
                  studentIds: f.studentIds.includes(id)
                    ? f.studentIds.filter((x) => x !== id)
                    : [...f.studentIds, id],
                })
              }
            />
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
              marginTop: 10,
            }}
          >
            <div>
              <label style={S.label}>তারিখ</label>
              <input
                type="date"
                style={S.input}
                value={f.date}
                onChange={(e) => setF({ ...f, date: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>সময়</label>
              <input
                type="time"
                style={S.input}
                value={f.time}
                onChange={(e) => setF({ ...f, time: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>সময়কাল (মিনিট)</label>
              <input
                type="number"
                style={S.input}
                value={f.dur}
                onChange={(e) => setF({ ...f, dur: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>লেকচার নং</label>
              <input
                type="number"
                min="1"
                style={S.input}
                value={f.lectureNo}
                onChange={(e) => setF({ ...f, lectureNo: e.target.value })}
              />
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>১ম জুম লিংক</label>
            <input
              style={S.input}
              value={f.zoom}
              onChange={(e) => setF({ ...f, zoom: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>২য় জুম লিংক (রিজয়েন — ঐচ্ছিক)</label>
            <input
              style={S.input}
              value={f.zoom2}
              onChange={(e) => setF({ ...f, zoom2: e.target.value })}
              placeholder="উস্তাদ+স্টুডেন্ট ১ম লিংকে একবার জয়েন করার পর, আবার জয়েন করতে চাইলে এই লিংক ব্যবহার হবে"
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>অভিভাবকের রিকোয়ারমেন্ট (ঐচ্ছিক)</label>
            <textarea
              rows={2}
              style={{ ...S.input, resize: "vertical" }}
              value={f.req}
              onChange={(e) => setF({ ...f, req: e.target.value })}
              placeholder="যেমন: তিলাওয়াতের ভুলগুলোতে বেশি জোর দেবেন, লন্ডন সময় সন্ধ্যার পর..."
            />
          </div>
          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
            onClick={addClass}
          >
            {editId ? "✏️ আপডেট করুন" : "শিডিউল করুন ও সবাইকে নোটিফিকেশন পাঠান"}
          </Btn>
        </Modal>
      )}
    </>
  );
}

/* ═══════════════ ইনস্ট্যান্ট ক্লাস — পরিচালক/এডমিন যখন-তখন এককালীন ক্লাস তৈরি করে
   সাথে সাথে টিচার ও স্টুডেন্টের পোর্টালে জয়েন অপশন পাঠাতে পারবেন ═══════════════ */
function InstantClassView({ courses, user }) {
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  useEffect(() => {
    api.allTeachers().then((d) => setTeachers(d.map(adaptPerson))).catch(() => {});
    api.allStudents().then((d) => setStudents(d.map(adaptPerson))).catch(() => {});
  }, []);

  // ইমার্জেন্সি ক্লাসের জন্য এই পেজ — তাই ডিফল্ট সময় এখন-ই (ঠিক করে দেওয়ার দরকার
  // নেই), আজকের তারিখেই তৈরি হলে জয়েন অপশন সাথে সাথেই পোর্টালে চলে যায় —
  // শিডিউল করা সময়ের জন্য অপেক্ষা করতে হয় না
  const blankForm = () => {
    const now = new Date();
    return {
      kind: "মেকআপ ক্লাস",
      courseId: courses[0]?.id,
      teacherId: courses[0]?.teacherId,
      studentIds: [],
      date: todayISO(),
      time: `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`,
      dur: 60,
      lectureNo: 1,
      zoom: "https://zoom.us/j/",
      zoom2: "", // রিজয়েন লিংক (ঐচ্ছিক) — উস্তাদ+স্টুডেন্ট ১ম লিংকে একবার জয়েন করার পর এই লিংকেই আবার জয়েন হবে
      req: "",
    };
  };
  const [f, setF] = usePersistedState("inst_f", blankForm);
  const [previewZone, setPreviewZone] = useState("");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState(null); // সদ্য তৈরি হওয়া ক্লাস — নিচে নোটিফাই বাটন দেখাতে

  const preview = previewZone ? toZoneFullDateTime(f.date, f.time, previewZone) : null;

  const doCreate = async (targetStudents) => {
    const c = courseById(courses, f.courseId);
    setBusy(true);
    try {
      const res = await api.scheduleClass(classPayload(f, targetStudents));
      setCreated({ ...res, courseName: c.name });
      setF(blankForm());
      setPreviewZone("");
      notice("✔ ক্লাস শিডিউল হয়েছে — সময় হলে টিচার ও স্টুডেন্টের পোর্টালে জয়েন অপশন আসবে।");
    } catch (e) {
      notice("ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
    }
    setBusy(false);
  };
  const create = () => {
    if (!f.courseId || !f.teacherId) return notice("কোর্স ও উস্তাদ বেছে নিন।");
    if (!f.zoom.trim()) return notice("জুম লিংক দিন।");
    const c = courseById(courses, f.courseId);
    if (!f.studentIds.length) {
      // কাউকে না বাছলে আগে চুপচাপ পুরো কোর্সের সবাইকে যুক্ত করে দিত — ভুলবশত
      // অপ্রাসঙ্গিক স্টুডেন্ট ক্লাসে ঢুকে যাওয়ার কারণ ছিল এটাই; এখন স্পষ্ট
      // নিশ্চিতকরণ ছাড়া এগোবে না
      const whole = c.studentIds || [];
      const names =
        whole.map((sid) => students.find((s) => String(s.id) === String(sid))?.name || sid).join(", ") ||
        "কেউ নেই";
      askConfirm(
        `আপনি কোনো নির্দিষ্ট স্টুডেন্ট বাছাই করেননি — তাই "${c.name || "এই কোর্সের"}" কোর্সে ভর্তি সবাই (${names}) এই ক্লাসে যুক্ত হয়ে যাবে। এগিয়ে যাবেন?`,
        () => doCreate(whole),
      );
      return;
    }
    doCreate(f.studentIds);
  };

  const notifyCreated = () => {
    if (!created) return;
    const teacher = teachers.find((t) => String(t.id) === String(created.teacher));
    const studentTargets = (created.students || [])
      .map((id) => students.find((s) => String(s.id) === String(id)))
      .filter((s) => s && s.phone);
    const targets = [...(teacher && teacher.phone ? [teacher] : []), ...studentTargets];
    if (!targets.length) return notice("এই ক্লাসের টিচার/শিক্ষার্থীর কোনো ফোন নম্বর পাওয়া যায়নি।");
    targets.forEach((p, i) => {
      const text =
        `Assalamu Alaikum Warahmatullah,\n\n` +
        `Dear ${p.name},\n\n` +
        `This is a reminder that you have a class today — "${created.courseName}" at ${(created.time || "").slice(0, 5)}.\n\n` +
        `*Please join on time insaallah.*\n\n` +
        `Jazakallahu Khairan Fid-darayn.\n— Tarbiyatul Quran Academy.`;
      const phone = p.phone.replace(/[^\d]/g, "");
      setTimeout(
        () => window.open(`https://wa.me/${phone}?text=${encodeURIComponent(text)}`, "_blank"),
        i * 400,
      );
    });
    notice(`✔ ${bn(targets.length)} জনকে WhatsApp পাঠানো হচ্ছে`);
  };

  return (
    <Section
      title="⚡ ইনস্ট্যান্ট ক্লাস"
      sub="ইমার্জেন্সি/হঠাৎ প্রয়োজনীয় ক্লাসের জন্য — আজকের তারিখে তৈরি করলে অপেক্ষা করতে হয় না, তৈরি হওয়ার সাথে সাথেই টিচার ও স্টুডেন্টের পোর্টালে জয়েন অপশন চলে যায়"
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <div>
          <label style={S.label}>ক্লাসের ধরন</label>
          <select
            style={S.input}
            value={f.kind}
            onChange={(e) => setF({ ...f, kind: e.target.value })}
          >
            {CLASS_KINDS.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={S.label}>কোর্স</label>
          <select
            style={S.input}
            value={f.courseId || ""}
            onChange={(e) => {
              const c = courseById(courses, e.target.value);
              setF({ ...f, courseId: e.target.value, teacherId: c.teacherId || f.teacherId });
            }}
          >
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div style={{ marginTop: 10 }}>
        <label style={S.label}>উস্তাদ/উস্তাদা — কার জন্য তৈরি হবে</label>
        <select
          style={S.input}
          value={f.teacherId || ""}
          onChange={(e) => setF({ ...f, teacherId: e.target.value })}
        >
          {teachers.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} {t.sub ? `(${t.sub})` : ""}
            </option>
          ))}
        </select>
      </div>
      <div style={{ marginTop: 10 }}>
        <label style={S.label}>
          শিক্ষার্থী বাছাই করুন — এক এক করে ({bn(f.studentIds.length)} জন নির্বাচিত;
          কাউকে না বাছলে কোর্সের সবাই)
        </label>
        <StudentPicker
          selected={f.studentIds}
          people={students}
          onToggle={(id) =>
            setF({
              ...f,
              studentIds: f.studentIds.includes(id)
                ? f.studentIds.filter((x) => x !== id)
                : [...f.studentIds, id],
            })
          }
        />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 10 }}>
        <div>
          <label style={S.label}>তারিখ</label>
          <input
            type="date"
            style={S.input}
            value={f.date}
            onChange={(e) => setF({ ...f, date: e.target.value })}
          />
        </div>
        <div>
          <label style={S.label}>সময় (বাংলাদেশ সময় অনুযায়ী লিখুন)</label>
          <input
            type="time"
            style={S.input}
            value={f.time}
            onChange={(e) => setF({ ...f, time: e.target.value })}
          />
        </div>
        <div>
          <label style={S.label}>সময়কাল (মিনিট)</label>
          <input
            type="number"
            style={S.input}
            value={f.dur}
            onChange={(e) => setF({ ...f, dur: e.target.value })}
          />
        </div>
        <div>
          <label style={S.label}>লেকচার নং (ঐচ্ছিক)</label>
          <input
            type="number"
            min="1"
            style={S.input}
            value={f.lectureNo}
            onChange={(e) => setF({ ...f, lectureNo: e.target.value })}
          />
        </div>
      </div>
      <div style={{ marginTop: 10 }}>
        <label style={S.label}>🌍 টাইমজোন প্রিভিউ (ঐচ্ছিক — বিদেশে থাকা কাউকে জানাতে সুবিধার জন্য)</label>
        <select
          style={S.input}
          value={previewZone}
          onChange={(e) => setPreviewZone(e.target.value)}
        >
          <option value="">— বাছাই করুন —</option>
          {COMMON_ZONES.map((z) => (
            <option key={z.zone} value={z.zone}>
              {z.label}
            </option>
          ))}
        </select>
        {preview && (
          <div style={{ marginTop: 6, fontSize: 12.5, color: C.muted }}>
            {COMMON_ZONES.find((z) => z.zone === previewZone)?.label}-এর সময় অনুযায়ী:{" "}
            <b>{fmtDate(preview.date)} · {preview.time}</b>
          </div>
        )}
      </div>
      <div style={{ marginTop: 10 }}>
        <label style={S.label}>১ম জুম লিংক</label>
        <input
          style={S.input}
          value={f.zoom}
          onChange={(e) => setF({ ...f, zoom: e.target.value })}
        />
      </div>
      <div style={{ marginTop: 10 }}>
        <label style={S.label}>২য় জুম লিংক (রিজয়েন — ঐচ্ছিক)</label>
        <input
          style={S.input}
          value={f.zoom2}
          onChange={(e) => setF({ ...f, zoom2: e.target.value })}
          placeholder="উস্তাদ+স্টুডেন্ট ১ম লিংকে একবার জয়েন করার পর, আবার জয়েন করতে চাইলে এই লিংক ব্যবহার হবে"
        />
      </div>
      <div style={{ marginTop: 10 }}>
        <label style={S.label}>অভিভাবকের রিকোয়ারমেন্ট (ঐচ্ছিক)</label>
        <textarea
          rows={2}
          style={{ ...S.input, resize: "vertical" }}
          value={f.req}
          onChange={(e) => setF({ ...f, req: e.target.value })}
          placeholder="যেমন: তিলাওয়াতের ভুলগুলোতে বেশি জোর দেবেন..."
        />
      </div>
      <Btn
        style={{ marginTop: 16, width: "100%", justifyContent: "center", opacity: busy ? 0.6 : 1 }}
        onClick={create}
      >
        {busy ? "⏳ তৈরি হচ্ছে…" : "⚡ এখনই ক্লাস তৈরি করুন"}
      </Btn>
      {created && (
        <div
          style={{
            marginTop: 14,
            padding: "12px 14px",
            borderRadius: 12,
            background: C.greenBg,
            border: `1.5px solid ${C.green}`,
          }}
        >
          <div style={{ fontWeight: 800, marginBottom: 6 }}>
            ✔ তৈরি হয়েছে — {created.courseName} · {fmtDate(created.date)} ·{" "}
            {(created.time || "").slice(0, 5)}
          </div>
          <Btn kind="gold" onClick={notifyCreated}>
            📨 টিচার ও স্টুডেন্টকে এখনই WhatsApp-এ জানান
          </Btn>
        </div>
      )}
    </Section>
  );
}

/* ═══════════════ স্থগিত ক্লাস — director/admin সব দেখেন, teacher/student শুধু
   নিজের কোর্স অনুযায়ী (backend আগেই role অনুযায়ী ফিল্টার করে) ═══════════════ */
function PostponedClassesView({ user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.classes();
      setClasses(data.filter((k) => k.status === "postponed"));
    } catch {
      setClasses([]);
    }
    setLoading(false);
  };
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const filtered = month ? classes.filter((k) => (k.date || "").startsWith(month)) : classes;
  const sorted = [...filtered].sort((a, b) => (b.date + b.time).localeCompare(a.date + a.time));

  const remove = (k) => {
    askConfirm("এই স্থগিত ক্লাসের রেকর্ডটা স্থায়ীভাবে মুছে ফেলবেন?", async () => {
      try {
        await api.deleteClass(k.id);
        await load();
      } catch (e) {
        notice("মুছতে ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
      }
    });
  };

  // ছাত্র অনুযায়ী মাসভিত্তিক এক্সেল এক্সপোর্ট — কেবল পরিচালক (এডমিনও না, অন্য কেউ না)
  const exportExcel = () => {
    if (!sorted.length) return notice("কোনো স্থগিত ক্লাস নেই।");
    const head = ["শিক্ষার্থী", "কোর্স", "উস্তাদ", "তারিখ", "সময়"];
    const body = sorted.flatMap((k) => {
      const names = k.student_names && k.student_names.length ? k.student_names : ["—"];
      return names.map((n) => [
        n,
        k.course_name || "—",
        k.teacher_name || "—",
        fmtDate(k.date),
        (k.time || "").slice(0, 5),
      ]);
    });
    const csv = [head, ...body]
      .map((row) => row.map(csvCell).join(","))
      .join("\r\n");
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }); // BOM — Excel-এ বাংলা যেন না ভাঙে
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `স্থগিত-ক্লাস-${month || "সব"}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  };

  return (
    <Section
      title={T("⛔ স্থগিত ক্লাস", "⛔ Postponed Classes")}
      sub={T(
        "অসুস্থতা বা অন্য কারণে স্থগিত হওয়া ক্লাসের তালিকা",
        "List of classes postponed due to illness or other reasons",
      )}
      action={
        isDir(user) && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              style={{ ...S.input, padding: "8px 10px", width: 160 }}
            />
            <Btn sm kind="soft" onClick={exportExcel}>
              📊 Excel
            </Btn>
          </div>
        )
      }
    >
      {loading ? (
        <Loader text={T("লোড হচ্ছে", "Loading")} />
      ) : (
        <Table
          head={[
            T("শিক্ষার্থী", "Student"),
            T("কোর্স", "Course"),
            T("উস্তাদ", "Teacher"),
            T("তারিখ", "Date"),
            T("সময়", "Time"),
            ...(isDir(user) ? [""] : []),
          ]}
          rows={sorted.map((k) => [
            (k.student_names && k.student_names.join(", ")) || "—",
            k.course_name || "—",
            k.teacher_name || "—",
            fmtDate(k.date),
            (k.time || "").slice(0, 5),
            ...(isDir(user)
              ? [
                  <Btn key="d" sm kind="danger" onClick={() => remove(k)}>
                    🗑️ মুছুন
                  </Btn>,
                ]
              : []),
          ])}
          empty={T("কোনো স্থগিত ক্লাস নেই", "No postponed classes")}
        />
      )}
    </Section>
  );
}

/* ═══════════════ লেকচার প্ল্যান — টিক/ক্রস (ফিচার ৩) ═══════════════ */
/* ═══════════════ লেখা সাজানোর ছোট এডিটর ═══════════════
   পরিচালক টগলের ভেতরে মোটা/বাঁকা/রঙ/আকার/তালিকা দিয়ে লিখতে পারেন।
   লেখা HTML হিসেবে সংরক্ষিত হয়; সার্ভারে ঢোকার মুখে ছেঁকে নেওয়া হয়
   (safe_html.py) — তাই স্ক্রিপ্ট বা বিপজ্জনক কিছু কখনো সংরক্ষিত হয় না।

   ⚠️ ভেতরের লেখা কেবল প্রথমবারই বসানো হয়। প্রতিবার বসালে টাইপ করার সময়
   কার্সর লাফিয়ে শুরুতে চলে যেত — contentEditable-এর পরিচিত সমস্যা। */
const RT_SIZES = [
  { v: "2", label: "ছোট" },
  { v: "3", label: "সাধারণ" },
  { v: "4", label: "বড়" },
  { v: "5", label: "আরও বড়" },
  { v: "6", label: "শিরোনাম" },
];
const RT_COLORS = [
  "#1a1f2e", "#1a5c3a", "#c9962a", "#d92626", "#1d4ed8", "#7c3aed", "#6b7280",
];

/* টগলের ভেতরের লেখায় বসানো ছবি ও টেবিল যেন বাক্স ছাপিয়ে না যায় —
   এডিটরে ও দেখার জায়গায় দুটোতেই এক নিয়ম। */
const LESSON_BODY_CSS = `
.tqaLessonBody img, [contenteditable] img { max-width: 100%; height: auto; border-radius: 8px; }
.tqaLessonBody table, [contenteditable] table { border-collapse: collapse; width: 100%; table-layout: fixed; }
.tqaLessonBody td, .tqaLessonBody th, [contenteditable] td, [contenteditable] th { border: 1px solid #1a5c3a; padding: 6px 8px; word-wrap: break-word; }
.tqaLessonBody th, [contenteditable] th { background: #eafaf1; }
.tqaLessonBody a { color: #1a5c3a; font-weight: 700; }
.tqaLessonBody ul, .tqaLessonBody ol, [contenteditable] ul, [contenteditable] ol { padding-left: 24px; margin: 6px 0; }
`;

function RichText({ value, onChange, placeholder }) {
  const ref = useRef(null);
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (ref.current) ref.current.innerHTML = value || "";
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const push = () => onChange(ref.current ? ref.current.innerHTML : "");
  const cmd = (c, v) => {
    ref.current?.focus();
    try {
      document.execCommand(c, false, v);
    } catch (e) {
      /* কোনো ব্রাউজারে না চললে চুপচাপ — লেখা তবু ঠিকই থাকে */
    }
    push();
  };
  // নির্বাচিত অংশকে আরবি বানাই — ডান-থেকে-বাঁ ও আমিরি ফন্ট
  const arabic = () => {
    ref.current?.focus();
    const sel = window.getSelection();
    const txt = sel && !sel.isCollapsed ? String(sel) : "";
    if (!txt) return notice("আগে যে লেখাটুকু আরবি করতে চান তা নির্বাচন করুন।");
    cmd(
      "insertHTML",
      `<span dir="rtl" style="font-family: Amiri, serif; font-size: 1.35em; line-height: 2">${txt.replace(
        /[&<>]/g,
        (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c],
      )}</span>`,
    );
  };
  // ছবি বা PDF — আপলোড করে সেটার ঠিকানা লেখার ভেতরে বসিয়ে দিই
  const pickFile = () => fileRef.current?.click();
  const onFile = async (e) => {
    const f = e.target.files && e.target.files[0];
    e.target.value = ""; // একই ফাইল আবার বাছলেও যেন কাজ করে
    if (!f) return;
    setBusy(true);
    try {
      const r = await api.uploadLessonMedia(f);
      const url = String(r.url).replace(/"/g, "&quot;");
      const name = String(r.name || "ফাইল").replace(/[&<>]/g, (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c],
      );
      cmd(
        "insertHTML",
        r.kind === "image"
          ? `<img src="${url}" alt="${name}" style="max-width: 100%; border-radius: 8px" /><br />`
          : `<p>📄 <a href="${url}">${name}</a></p>`,
      );
    } catch (err) {
      notice(
        "আপলোড ব্যর্থ — " +
          (err?.data?.error || err?.message || "আবার চেষ্টা করুন"),
      );
    } finally {
      setBusy(false);
    }
  };
  // টেবিল — সারি ও কলাম জিজ্ঞেস করে খালি ছক বসাই
  const insertTable = () => {
    const rows = parseInt(window.prompt("কয়টি সারি?", "3") || "", 10);
    const cols = parseInt(window.prompt("কয়টি কলাম?", "3") || "", 10);
    if (!rows || !cols || rows < 1 || cols < 1) return;
    if (rows > 50 || cols > 12)
      return notice("সর্বোচ্চ ৫০টি সারি ও ১২টি কলাম।");
    const td =
      '<td style="border: 1px solid #1a5c3a; padding: 6px 8px">&nbsp;</td>';
    const th =
      '<th style="border: 1px solid #1a5c3a; padding: 6px 8px; background: #eafaf1">&nbsp;</th>';
    const head = `<tr>${th.repeat(cols)}</tr>`;
    const body = `<tr>${td.repeat(cols)}</tr>`.repeat(Math.max(rows - 1, 1));
    cmd(
      "insertHTML",
      `<table style="border-collapse: collapse; width: 100%">${head}${body}</table><br />`,
    );
  };
  const tool = {
    border: `1px solid ${C.line}`,
    background: "#fff",
    borderRadius: 7,
    cursor: "pointer",
    fontSize: 12.5,
    lineHeight: 1,
    padding: "6px 9px",
    color: C.text,
  };
  return (
    <div style={{ border: `1px solid ${C.line}`, borderRadius: 10, overflow: "hidden" }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 4,
          padding: 6,
          background: C.cream,
          borderBottom: `1px solid ${C.line}`,
        }}
      >
        <button type="button" title="মোটা" style={{ ...tool, fontWeight: 900 }} onClick={() => cmd("bold")}>B</button>
        <button type="button" title="বাঁকা" style={{ ...tool, fontStyle: "italic" }} onClick={() => cmd("italic")}>I</button>
        <button type="button" title="আন্ডারলাইন" style={{ ...tool, textDecoration: "underline" }} onClick={() => cmd("underline")}>U</button>
        <select
          title="অক্ষরের আকার"
          defaultValue=""
          onChange={(e) => {
            if (e.target.value) cmd("fontSize", e.target.value);
            e.target.value = "";
          }}
          style={{ ...tool, padding: "5px 6px" }}
        >
          <option value="">আকার</option>
          {RT_SIZES.map((z) => (
            <option key={z.v} value={z.v}>{z.label}</option>
          ))}
        </select>
        <span style={{ display: "flex", gap: 3, alignItems: "center" }}>
          {RT_COLORS.map((col) => (
            <button
              key={col}
              type="button"
              title="এই রঙ দিন"
              onClick={() => cmd("foreColor", col)}
              style={{
                width: 18,
                height: 18,
                borderRadius: 5,
                border: `1px solid ${C.line}`,
                background: col,
                cursor: "pointer",
                padding: 0,
              }}
            />
          ))}
        </span>
        <button type="button" title="বুলেট তালিকা" style={tool} onClick={() => cmd("insertUnorderedList")}>• তালিকা</button>
        <button type="button" title="নম্বর তালিকা" style={tool} onClick={() => cmd("insertOrderedList")}>১. তালিকা</button>
        <button type="button" title="বাঁয়ে" style={tool} onClick={() => cmd("justifyLeft")}>⇤</button>
        <button type="button" title="মাঝবরাবর" style={tool} onClick={() => cmd("justifyCenter")}>⇔</button>
        <button type="button" title="ডানে" style={tool} onClick={() => cmd("justifyRight")}>⇥</button>
        <button
          type="button"
          title="নির্বাচিত লেখাকে আরবি করুন (ডান থেকে বাঁ)"
          style={{ ...tool, fontFamily: "Amiri, serif", fontSize: 15 }}
          onClick={arabic}
        >
          ع
        </button>
        <button type="button" title="ছবি বা PDF যোগ করুন" style={tool} onClick={busy ? undefined : pickFile}>
          {busy ? "⏳ যাচ্ছে…" : "🖼️ ছবি/PDF"}
        </button>
        <button type="button" title="টেবিল বসান" style={tool} onClick={insertTable}>▦ টেবিল</button>
        <button type="button" title="সাজসজ্জা মুছুন" style={tool} onClick={() => cmd("removeFormat")}>✕ সাজ</button>
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp,application/pdf"
          onChange={onFile}
          style={{ display: "none" }}
        />
      </div>
      <div
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        onInput={push}
        onBlur={push}
        data-ph={placeholder || ""}
        style={{
          minHeight: 110,
          maxHeight: 320,
          overflowY: "auto",
          padding: "10px 12px",
          fontSize: 13.5,
          lineHeight: 1.9,
          outline: "none",
          background: "#fff",
        }}
      />
    </div>
  );
}

function LecturePlan({ db, courses, user, refresh }) {
  /* দারস পরিকল্পনা — সিলেবাসের বিষয় ধরে হেডিং, প্রতিটির নিচে যত খুশি
     টগল-টপিক। টপিক কভার হয়ে গেলেও নিজের হেডিংয়েই থাকে, কেবল রঙ বদলায়।
     ক্রম পরিচালকের নির্ধারিত — তারিখ বা কভারের অবস্থা দেখে সরে না।
     কভারের টিক প্রতি শিক্ষার্থীর আলাদা, আগের মতোই। */
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [sel, setSel] = useState(courses[0]?.id);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openTopics, setOpenTopics] = useState({});
  const toggleOpen = (id) => setOpenTopics((o) => ({ ...o, [id]: !o[id] }));

  /* কার জন্য টিক দেওয়া/দেখা হচ্ছে। উস্তাদ ভুল করে একজনের হিসাবে অন্যজনের
     টপিকে টিক না দিয়ে ফেলেন — সেজন্য ঢোকার সাথে সাথেই পর্দা ঢেকে বাছাই। */
  const [forStudent, setForStudent] = useState(null);
  const [courseStudents, setCourseStudents] = useState([]);
  const [pickOpen, setPickOpen] = useState(false);
  const needsStudent = user.role !== "student";

  const [edit, setEdit] = useState(null); // {sectionId, blocks:[…]} — টপিক সম্পাদনা
  const [saving, setSaving] = useState(false);

  const hasGrant =
    user.role === "teacher" &&
    (user.can_fix_cross ?? db.permissions?.fixCross?.[user.id]);
  const isAdmin = isAdm(user) || hasGrant;
  const canMark = user.role === "teacher" || isAdmin;
  const course = courseById(courses, sel);

  const load = async () => {
    if (!sel) return setLoading(false);
    try {
      let rows = await api.lessonSections(sel, forStudent?.id);
      // কোর্সে এখনো হেডিং না থাকলে সাতটি ডিফল্ট বানিয়ে নিই (কেবল পরিচালক)
      if (!rows.length && isDir(user)) rows = await api.ensureSections(sel);
      setSections(rows || []);
    } catch (e) {
      setSections([]);
      notice(
        T(
          "দারস পরিকল্পনা আনা যায়নি — " +
            (e?.data?.error || e?.message || "আবার চেষ্টা করুন"),
          "Couldn't load the lesson plan — " + (e?.message || "please try again"),
        ),
      );
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel, forStudent]);

  // কোর্স বদলালে আগের শিক্ষার্থী আর প্রযোজ্য নয়
  useEffect(() => {
    if (!sel || !needsStudent) return;
    setForStudent(null);
    setCourseStudents([]);
    api
      .courseStudents(sel)
      .then((rows) => {
        setCourseStudents(rows || []);
        setPickOpen(true);
      })
      .catch(() => {
        setCourseStudents([]);
        setPickOpen(true);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel]);

  // ── কভার মার্ক ──
  const mark = async (tp, val) => {
    if (!canMark && !isAdmin) return;
    if (!forStudent) {
      setPickOpen(true);
      return notice("আগে কোন শিক্ষার্থীর জন্য টিক দিচ্ছেন তা বেছে নিন।");
    }
    if (canMark && !isAdmin && tp.covered === "missed")
      return notice("লাল ক্রস কেবল এডমিন/পরিচালক ঠিক করতে পারবেন।");
    try {
      await api.markTopic(tp.id, val, forStudent.id);
      await load();
    } catch (e) {
      notice(
        "টপিক মার্ক করতে ব্যর্থ — " +
          (e?.data?.error || e?.data?.detail || e?.message || "আবার চেষ্টা করুন"),
      );
    }
  };

  // ── হেডিং ──
  const addSection = () => {
    const name = (window.prompt("নতুন হেডিংয়ের নাম?", "") || "").trim();
    if (!name) return;
    api
      .addSection(sel, name, sections.length)
      .then(load)
      .catch((e) =>
        notice("হেডিং যোগ করা যায়নি — " + (e?.data?.error || e?.message || "")),
      );
  };
  const renameSection = (sec) => {
    const name = (window.prompt("হেডিংয়ের নাম", sec.name) || "").trim();
    if (!name || name === sec.name) return;
    api
      .renameSection(sec.id, name)
      .then(load)
      .catch((e) =>
        notice("নাম বদলানো যায়নি — " + (e?.data?.error || e?.message || "")),
      );
  };
  const delSection = (sec) =>
    askConfirm(
      `"${sec.name}" হেডিংটি মুছে ফেলবেন?` +
        (sec.topics.length
          ? `\n\nএর নিচের ${bn(sec.topics.length)}টি টপিক ও সেগুলোর কভার-টিকও মুছে যাবে।`
          : ""),
      () =>
        api
          .delSection(sec.id)
          .then(load)
          .catch((e) =>
            notice("মুছে ফেলা যায়নি — " + (e?.data?.error || e?.message || "")),
          ),
    );
  const moveSection = (i, d) => {
    const j = i + d;
    if (j < 0 || j >= sections.length) return;
    const ids = sections.map((x) => x.id);
    [ids[i], ids[j]] = [ids[j], ids[i]];
    api
      .reorderSections(ids)
      .then(load)
      .catch((e) =>
        notice("ক্রম বদলানো যায়নি — " + (e?.data?.error || e?.message || "")),
      );
  };

  // ── টপিক সম্পাদনা ──
  const uidRef = useRef(0);
  const blank = () => ({ _uid: `n${++uidRef.current}`, text: "", content: "", open: true });
  const openTopicEditor = (sec) =>
    setEdit({
      sectionId: sec.id,
      name: sec.name,
      // আইডি সাথে রাখি — নইলে সংরক্ষণে পুরনো টপিক মুছে নতুন হতো আর
      // প্রতি শিক্ষার্থীর কভার-টিক হারিয়ে যেত
      blocks: sec.topics.map((t) => ({
        _uid: `t${t.id}`,
        id: t.id,
        text: t.text || "",
        content: t.content || "",
        open: false,
      })),
    });
  const setBlock = (i, patch) =>
    setEdit((f) => ({
      ...f,
      blocks: (f.blocks || []).map((b, j) => (j === i ? { ...b, ...patch } : b)),
    }));
  const addBlock = () =>
    setEdit((f) => ({ ...f, blocks: [...(f.blocks || []), blank()] }));
  const delBlock = (i) =>
    setEdit((f) => ({ ...f, blocks: (f.blocks || []).filter((_, j) => j !== i) }));
  const moveBlock = (i, d) =>
    setEdit((f) => {
      const b = [...(f.blocks || [])];
      const j = i + d;
      if (j < 0 || j >= b.length) return f;
      [b[i], b[j]] = [b[j], b[i]];
      return { ...f, blocks: b };
    });
  const saveTopics = async () => {
    const topics = (edit.blocks || [])
      .filter((b) => (b.text || "").trim())
      .map((b) => ({
        ...(b.id ? { id: b.id } : {}),
        text: b.text.trim(),
        content: b.content || "",
      }));
    setSaving(true);
    try {
      await api.saveSectionTopics(edit.sectionId, topics);
      await load();
      setEdit(null);
      notice("✔ সংরক্ষিত হয়েছে।");
    } catch (e) {
      notice(
        "সংরক্ষণ ব্যর্থ — " + (e?.data?.error || e?.message || "আবার চেষ্টা করুন"),
      );
    } finally {
      setSaving(false);
    }
  };

  const allTopics = sections.flatMap((s) => s.topics || []);
  const done = allTopics.filter((t) => t.covered === "covered").length;
  const pct = allTopics.length ? Math.round((done / allTopics.length) * 100) : 0;

  return (
    <Section
      title={T("দৈনিক পাঠ পরিকল্পনা ও টপিক কভারেজ", "Daily Lesson Plan & Topic Coverage")}
      sub={T(
        "বিষয় অনুযায়ী হেডিং · প্রতিটির নিচে টপিক · কভার করা ✔ সবুজ · বাদ পড়া ✘ লাল",
        "Topics grouped by subject · covered ✔ green · missed ✘ red",
      )}
      action={isDir(user) && <Btn onClick={addSection}>+ হেডিং যোগ করুন</Btn>}
    >
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
        {courses.map((c) => (
          <Btn
            key={c.id}
            sm
            kind={sel === c.id ? "primary" : "soft"}
            onClick={() => setSel(c.id)}
          >
            {c.name}
          </Btn>
        ))}
      </div>

      <div
        style={{
          ...S.card,
          marginBottom: 12,
          display: "flex",
          alignItems: "center",
          gap: 14,
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: 180 }}>
          <div style={{ fontWeight: 800 }}>{course.name}</div>
          <div style={S.sub}>
            {T(`মোট টপিক: ${bn(allTopics.length)}`, `Total topics: ${allTopics.length}`)}
          </div>
        </div>
        <div style={{ minWidth: 200, flex: 1 }}>
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 4 }}>
            {T(
              `অগ্রগতি — ${bn(pct)}% (${bn(done)}/${bn(allTopics.length)})`,
              `Progress — ${pct}% (${done}/${allTopics.length})`,
            )}
          </div>
          <div style={{ height: 10, background: C.cream, borderRadius: 99 }}>
            <div
              style={{
                width: pct + "%",
                height: "100%",
                background: `linear-gradient(90deg, ${C.emerald}, ${C.gold})`,
                borderRadius: 99,
                transition: "width .4s",
              }}
            />
          </div>
        </div>
      </div>

      {/* কার জন্য টিক */}
      {needsStudent && forStudent && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            flexWrap: "wrap",
            padding: "9px 14px",
            borderRadius: 12,
            background: C.greenBg,
            border: `1.5px solid ${C.emerald}`,
            marginBottom: 10,
            fontSize: 13,
          }}
        >
          <span style={{ fontWeight: 800, color: C.emerald }}>👤 এখন টিক পড়বে:</span>
          <span style={{ fontWeight: 800 }}>{forStudent.name}</span>
          {forStudent.student_id && (
            <span style={{ color: C.muted, fontSize: 12 }}>({forStudent.student_id})</span>
          )}
          <div style={{ flex: 1 }} />
          <Btn sm kind="soft" onClick={() => setPickOpen(true)}>
            🔄 অন্য শিক্ষার্থী
          </Btn>
        </div>
      )}

      {needsStudent && pickOpen && (
        <BlockingPopup
          icon="👤"
          zIndex={306}
          title="কোন শিক্ষার্থীর জন্য?"
          footer={
            /* বের হওয়ার পথ সবসময় থাকতেই হবে — কোর্সে শিক্ষার্থী না থাকলে
               বাছার কিছু নেই, আর পরিচালক তো টপিক লিখতে আসেন */
            forStudent ? (
              <Btn
                kind="soft"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => setPickOpen(false)}
              >
                বাতিল — {forStudent.name} রেখেই চালিয়ে যাই
              </Btn>
            ) : courseStudents.length === 0 || isAdm(user) ? (
              <Btn
                kind="soft"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => setPickOpen(false)}
              >
                {courseStudents.length === 0
                  ? "ঠিক আছে"
                  : "শিক্ষার্থী না বেছেই দেখি (টিক দেওয়া যাবে না)"}
              </Btn>
            ) : null
          }
        >
          <div style={{ marginBottom: 10 }}>
            যাঁর টপিকে টিক দেবেন তাঁকে বেছে নিন। টিক কেবল{" "}
            <b>তাঁর নিজের পোর্টালেই</b> দেখাবে, অন্য কারও নয়।
          </div>
          {courseStudents.length === 0 ? (
            <div style={{ color: C.muted }}>
              আপনার কোনো শিক্ষার্থী এই কোর্সে নেই — পরিচালক যুক্ত করলে এখানে
              দেখা যাবে।
            </div>
          ) : (
            <div style={{ display: "grid", gap: 6, maxHeight: "46vh", overflowY: "auto" }}>
              {courseStudents.map((st) => (
                <button
                  key={st.id}
                  type="button"
                  onClick={() => {
                    setForStudent(st);
                    setPickOpen(false);
                  }}
                  style={{
                    textAlign: "left",
                    padding: "10px 12px",
                    borderRadius: 10,
                    cursor: "pointer",
                    fontFamily: "inherit",
                    fontSize: 13.5,
                    fontWeight: 700,
                    color: C.text,
                    background: forStudent?.id === st.id ? C.greenBg : "#fff",
                    border: `1.5px solid ${forStudent?.id === st.id ? C.emerald : C.line}`,
                  }}
                >
                  {st.name}
                  {st.student_id && (
                    <span style={{ color: C.muted, fontWeight: 600, fontSize: 12, marginLeft: 6 }}>
                      {st.student_id}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </BlockingPopup>
      )}

      {loading && <Loader text={T("লোড হচ্ছে", "Loading")} />}
      {!loading && sections.length === 0 && (
        <div style={{ ...S.card, textAlign: "center", color: C.muted, padding: 28 }}>
          {T(
            "📋 এই কোর্সের দারস পরিকল্পনা এখনো তৈরি হয়নি।",
            "📋 The lesson plan for this course hasn't been created yet.",
          )}
        </div>
      )}

      {/* ── হেডিং ধরে টপিক ── */}
      <div style={{ display: "grid", gap: 14 }}>
        {sections.map((sec, si) => (
          <div key={sec.id} style={{ ...S.card, padding: 0, overflow: "hidden" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                flexWrap: "wrap",
                padding: "10px 14px",
                background: `linear-gradient(135deg, ${C.emeraldD}, ${C.emerald})`,
                color: "#fff",
              }}
            >
              <span style={{ fontWeight: 800, fontSize: 15, flex: 1, minWidth: 140 }}>
                {sec.name}
              </span>
              <span
                style={{
                  background: "rgba(255,255,255,.18)",
                  borderRadius: 99,
                  fontSize: 11.5,
                  fontWeight: 800,
                  padding: "2px 9px",
                }}
              >
                {T(bn((sec.topics || []).length), (sec.topics || []).length)}
              </span>
              {isDir(user) && (
                <>
                  <Btn sm kind="soft" onClick={() => openTopicEditor(sec)}>
                    ✏️ টপিক
                  </Btn>
                  <Btn sm kind="soft" onClick={() => renameSection(sec)}>
                    নাম
                  </Btn>
                  <Btn sm kind="soft" onClick={() => moveSection(si, -1)}>
                    ▲
                  </Btn>
                  <Btn sm kind="soft" onClick={() => moveSection(si, 1)}>
                    ▼
                  </Btn>
                  <Btn sm kind="danger" onClick={() => delSection(sec)}>
                    🗑
                  </Btn>
                </>
              )}
            </div>

            <div style={{ padding: 12, display: "grid", gap: 6 }}>
              {(sec.topics || []).length === 0 ? (
                <div style={{ color: C.muted, fontSize: 12.5, textAlign: "center", padding: 8 }}>
                  {isDir(user)
                    ? '"✏️ টপিক" চেপে এই হেডিংয়ের নিচে টপিক যোগ করুন'
                    : "—"}
                </div>
              ) : (
                (sec.topics || []).map((tp) => {
                  const isDone = tp.covered === "covered";
                  const isMissed = tp.covered === "missed";
                  return (
                    <div key={tp.id}>
                      <div
                        onClick={() => toggleOpen(tp.id)}
                        title={openTopics[tp.id] ? "বন্ধ করুন" : "খুলে পড়ুন"}
                        style={{
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          padding: "9px 12px",
                          borderRadius: openTopics[tp.id] ? "10px 10px 0 0" : 10,
                          flexWrap: "wrap",
                          // কভার হলে সবুজ, বাদ পড়লে লাল, বাকি থাকলে সাদা
                          background: isDone ? C.greenBg : isMissed ? C.redBg : "#fff",
                          border: `1.5px solid ${
                            isDone ? C.green : isMissed ? C.red : C.line
                          }`,
                        }}
                      >
                        <span style={{ color: C.emerald, fontWeight: 800, fontSize: 12, width: 12 }}>
                          {openTopics[tp.id] ? "▾" : "▸"}
                        </span>
                        <span
                          style={{
                            width: 22,
                            height: 22,
                            borderRadius: 6,
                            display: "grid",
                            placeItems: "center",
                            fontWeight: 900,
                            fontSize: 13,
                            background: "#fff",
                            color: isDone ? C.green : isMissed ? C.red : C.muted,
                            border: `1.5px solid ${isDone ? C.green : isMissed ? C.red : C.line}`,
                          }}
                        >
                          {isDone ? "✔" : isMissed ? "✘" : "–"}
                        </span>
                        <span
                          style={{
                            flex: 1,
                            minWidth: 140,
                            fontSize: 13.5,
                            fontWeight: 700,
                            color: isMissed ? C.red : C.text,
                          }}
                        >
                          {tp.text}
                        </span>
                        {(canMark || isAdmin) && (
                          <span
                            onClick={(e) => e.stopPropagation()}
                            style={{ display: "flex", gap: 5, flexWrap: "wrap", justifyContent: "flex-end" }}
                          >
                            <Btn
                              sm
                              style={{
                                background: isDone ? C.green : "#fff",
                                color: isDone ? "#fff" : C.green,
                                border: `1.5px solid ${C.green}`,
                              }}
                              onClick={() => mark(tp, true)}
                            >
                              ✔ কভার
                            </Btn>
                            <Btn
                              sm
                              style={{
                                background: isMissed ? C.red : "#fff",
                                color: isMissed ? "#fff" : C.red,
                                border: `1.5px solid ${C.red}`,
                              }}
                              onClick={() => mark(tp, false)}
                            >
                              ✘ বাদ
                            </Btn>
                            {isAdmin && (
                              <Btn sm kind="soft" onClick={() => mark(tp, null)}>
                                রিসেট
                              </Btn>
                            )}
                          </span>
                        )}
                      </div>
                      {openTopics[tp.id] && (
                        <div
                          style={{
                            border: `1px solid ${C.line}`,
                            borderTop: "none",
                            borderRadius: "0 0 10px 10px",
                            padding: "10px 12px",
                            fontSize: 13.5,
                            lineHeight: 1.9,
                            wordWrap: "break-word",
                            background: "#fff",
                          }}
                        >
                          {tp.content ? (
                            /* সার্ভারে ঢোকার মুখেই ছেঁকে নেওয়া (safe_html) */
                            <div
                              className="tqaLessonBody"
                              style={{ whiteSpace: /<[a-z]/i.test(tp.content) ? "normal" : "pre-wrap" }}
                              dangerouslySetInnerHTML={{ __html: tp.content }}
                            />
                          ) : (
                            <span style={{ color: C.muted, fontSize: 12.5 }}>
                              {T(
                                "— এই টপিকের ভেতরে এখনো কিছু লেখা হয়নি —",
                                "— nothing has been written inside this topic yet —",
                              )}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        ))}
      </div>

      {/* ── টপিক সম্পাদনার মডাল ── */}
      {edit && (
        <Modal title={`✏️ ${edit.name} — টপিক`} onClose={() => setEdit(null)} wide>
          <div style={{ display: "grid", gap: 10 }}>
            {(edit.blocks || []).map((b, i) => (
              <div
                key={b._uid || i}
                style={{
                  border: `1.5px solid ${C.line}`,
                  borderRadius: 12,
                  overflow: "hidden",
                  background: "#fff",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "8px 10px",
                    background: C.greenBg,
                    borderBottom: b.open ? `1px solid ${C.line}` : "none",
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setBlock(i, { open: !b.open })}
                    style={{
                      border: "none",
                      background: "none",
                      cursor: "pointer",
                      fontSize: 13,
                      color: C.emerald,
                      fontWeight: 800,
                      width: 20,
                    }}
                  >
                    {b.open ? "▾" : "▸"}
                  </button>
                  <input
                    value={b.text}
                    onChange={(e) => setBlock(i, { text: e.target.value })}
                    placeholder={`টপিক ${bn(i + 1)} — যেমন: সূরা ইখলাস`}
                    style={{
                      ...S.input,
                      flex: 1,
                      fontWeight: 700,
                      border: "none",
                      background: "transparent",
                      padding: "4px 2px",
                    }}
                  />
                  <button type="button" onClick={() => moveBlock(i, -1)} title="উপরে"
                    style={{ border: "none", background: "none", cursor: "pointer", color: C.muted, fontSize: 13 }}>
                    ▲
                  </button>
                  <button type="button" onClick={() => moveBlock(i, 1)} title="নিচে"
                    style={{ border: "none", background: "none", cursor: "pointer", color: C.muted, fontSize: 13 }}>
                    ▼
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      askConfirm(`"${b.text || "নামহীন"}" টপিকটি সরাবেন?`, () => delBlock(i))
                    }
                    title="সরান"
                    style={{ border: "none", background: "none", cursor: "pointer", color: C.red, fontSize: 14 }}
                  >
                    🗑
                  </button>
                </div>
                {b.open && (
                  <div style={{ padding: 10 }}>
                    <RichText
                      key={b._uid}
                      value={b.content}
                      onChange={(html) => setBlock(i, { content: html })}
                      placeholder="এখানে লিখুন কী পড়াবেন — আরবি, বাংলা বা ইংরেজি।"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
          <Btn sm kind="soft" onClick={addBlock} style={{ marginTop: 10 }}>
            ➕ টপিক যোগ করুন
          </Btn>
          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center", opacity: saving ? 0.7 : 1 }}
            onClick={saving ? undefined : saveTopics}
          >
            {saving ? "সংরক্ষণ হচ্ছে…" : "✔ সংরক্ষণ করুন"}
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

function AttendanceView({ user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const isDirector = user.role === "director" || user.role === "admin";
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; // লোকাল তারিখ — UTC toISOString() নয়
  });
  const [rows, setRows] = useState(null); // null = লোড হচ্ছে

  const load = async () => {
    setRows(null);
    try {
      setRows(await api.attendanceReport(month));
    } catch {
      setRows([]);
    }
  };
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month]);

  const toggle = async (a) => {
    try {
      await api.updateAttendance(a.id, { marked_present: !a.present });
      await load();
    } catch (e) {
      notice("আপডেট ব্যর্থ — " + (e?.message || "যাচাই করুন"));
    }
  };
  const remove = (a) => {
    askConfirm(`${a.user_name || "এই শিক্ষার্থীর"}-এর এই হাজিরা রেকর্ডটি মুছে ফেলবেন?`, async () => {
      try {
        await api.deleteAttendance(a.id);
        await load();
      } catch (e) {
        notice("মুছতে ব্যর্থ — " + (e?.message || "যাচাই করুন"));
      }
    });
  };

  const monthLabel = T(
    monthLabelBn(month),
    new Date(month + "-01").toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    }),
  );

  // ঠিক কত মিনিট ক্লাস করেছে তা কেবল পরিচালকই দেখবেন — স্টুডেন্ট, উস্তাদ ও
  // এডমিন শুধু উপস্থিত/অনুপস্থিত দেখবেন (পোর্টালে "৪৫+ মিনিট" সতর্কবার্তা
  // অক্ষতই থাকছে, যাতে কেউ কম সময় থেকে বেরিয়ে যাওয়াকে স্বাভাবিক না ভাবেন)
  const showMinutes = isDir(user);
  const exportExcel = () => {
    if (!rows || !rows.length) return notice("এই মাসে কোনো হাজিরা রেকর্ড নেই।");
    const head = ["নাম", "কোর্স", "উস্তাদ", "তারিখ", ...(showMinutes ? ["মিনিট"] : []), "অবস্থা"];
    const body = rows.map((r) => [
      r.user_name || "—",
      r.course_name || "—",
      r.teacher_name || "—",
      r.class_date ? fmtDate(r.class_date) : "—",
      ...(showMinutes ? [r.minutes ?? 0] : []),
      r.present ? "উপস্থিত" : "অনুপস্থিত",
    ]);
    const csv = [head, ...body]
      .map((row) => row.map(csvCell).join(","))
      .join("\r\n");
    // ﻿ (BOM) না দিলে Excel-এ বাংলা লেখা ভাঙা দেখায়
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `হাজিরা-রিপোর্ট-${month}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  };

  const printReport = () => {
    if (!rows || !rows.length) return notice("এই মাসে কোনো হাজিরা রেকর্ড নেই।");
    const esc = (s) =>
      String(s ?? "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
    const body = rows
      .map(
        (r) =>
          `<tr><td>${esc(r.user_name)}</td><td>${esc(r.course_name)}</td><td>${esc(r.teacher_name)}</td><td>${r.class_date ? fmtDate(r.class_date) : "—"}</td>${showMinutes ? `<td>${bn(r.minutes ?? 0)}</td>` : ""}<td>${r.present ? "উপস্থিত ✔" : "অনুপস্থিত ✘"}</td></tr>`,
      )
      .join("");
    const html = `<!doctype html><html lang="bn"><head><meta charset="utf-8"><title>হাজিরা রিপোর্ট — ${monthLabel}</title>
<style>
body{font-family:'Noto Sans Bengali',Arial,sans-serif;padding:24px;color:#1f2a24}
h1{font-size:18px;text-align:center;margin:0 0 4px}
.s{text-align:center;font-size:12px;color:#6b7280;margin-bottom:18px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border:1px solid #d8ded9;padding:7px 10px;text-align:right}
th{background:#eef5f0}
.pr{display:block;margin:18px auto 0;background:#1a5c3a;color:#fff;border:none;padding:11px 26px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer}
@media print{.pr{display:none}body{padding:0}}
</style></head><body>
<h1>তারবিয়াতুল কুরআন একাডেমী — হাজিরা রিপোর্ট</h1>
<div class="s">${monthLabel}</div>
<table><tr><th>নাম</th><th>কোর্স</th><th>উস্তাদ</th><th>তারিখ</th>${showMinutes ? "<th>মিনিট</th>" : ""}<th>অবস্থা</th></tr>${body}</table>
<button class="pr" onclick="window.print()">🖨️ প্রিন্ট / PDF সেভ করুন</button>
</body></html>`;
    openPrintDoc(html, `হাজিরা-রিপোর্ট-${month}.html`);
  };

  const sendWhatsApp = () => {
    if (!rows || !rows.length) return notice("এই মাসে কোনো হাজিরা রেকর্ড নেই।");
    const present = rows.filter((r) => r.present).length;
    const text =
      `📊 হাজিরা রিপোর্ট — ${monthLabel}\n` +
      `মোট রেকর্ড: ${bn(rows.length)}\n` +
      `উপস্থিত: ${bn(present)}\n` +
      `অনুপস্থিত: ${bn(rows.length - present)}\n\n` +
      `— তারবিয়াতুল কুরআন একাডেমী`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
  };

  const head = [
    T("নাম", "Name"),
    T("কোর্স", "Course"),
    T("উস্তাদ", "Teacher"),
    T("তারিখ", "Date"),
    ...(showMinutes ? [T("মিনিট", "Minutes")] : []),
    T("অবস্থা", "Status"),
    ...(isDirector ? ["অ্যাকশন"] : []),
  ];
  const tableRows = (rows || []).map((r) => [
    r.user_name || "—",
    r.course_name || "—",
    r.teacher_name || "—",
    r.class_date ? fmtDate(r.class_date) : "—",
    ...(showMinutes ? [T(`${bn(r.minutes ?? 0)} মিনিট`, `${r.minutes ?? 0} min`)] : []),
    r.present ? (
      <Tag key="t">{T("উপস্থিত ✔", "Present ✔")}</Tag>
    ) : (
      <Tag key="t" color={C.red} bg={C.redBg}>
        {T("অনুপস্থিত", "Absent")}
      </Tag>
    ),
    ...(isDirector
      ? [
          <div key="act" style={{ display: "flex", gap: 4 }}>
            <Btn sm kind="soft" onClick={() => toggle(r)}>
              {r.present ? "❌ অনুপস্থিত করুন" : "✔️ উপস্থিত করুন"}
            </Btn>
            <Btn sm kind="danger" onClick={() => remove(r)}>
              🗑️
            </Btn>
          </div>,
        ]
      : []),
  ]);

  return (
    <Section
      title={T("হাজিরা রিপোর্ট", "Attendance Report")}
      sub={T(
        "ন্যূনতম ৪৫ মিনিট ক্লাসে থাকলে তবেই হাজিরা গণ্য হয় — এই তালিকা কখনো মোছা হয় না (পুরনো ক্লাস-শিডিউল ৬০ দিন পর মুছলেও হাজিরা টিকে থাকে)",
        "Attendance only counts if you stayed 45+ minutes — this record is never deleted (it stays even after the old class schedule is removed after 60 days)",
      )}
      action={
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            style={{ ...S.input, padding: "8px 10px", width: 160 }}
          />
          <Btn sm kind="soft" onClick={exportExcel}>
            📊 Excel
          </Btn>
          <Btn sm kind="soft" onClick={printReport}>
            {T("🖨️ প্রিন্ট", "🖨️ Print")}
          </Btn>
          {isAdm(user) && (
            <Btn sm kind="soft" onClick={sendWhatsApp}>
              📱 WhatsApp
            </Btn>
          )}
        </div>
      }
    >
      {rows === null ? (
        <Loader text={T("হাজিরা লোড হচ্ছে", "Loading attendance")} />
      ) : (
        <Table
          head={head}
          rows={tableRows}
          empty={T(
            `${monthLabel}-এ কোনো হাজিরা রেকর্ড নেই`,
            `No attendance records for ${monthLabel}`,
          )}
        />
      )}
    </Section>
  );
}

/* ═══════════════ ভাগ করা টুল: প্রশ্ন বিল্ডার, জমা দেওয়া, মূল্যায়ন ═══════════════ */

/* প্রশ্ন বানানোর বিল্ডার — লিখিত প্রশ্ন বা MCQ */
function QBuilder({ qs, setQs, allowMcq }) {
  const upd = (id, patch) =>
    setQs(qs.map((q) => (q.id === id ? { ...q, ...patch } : q)));
  return (
    <div style={{ marginTop: 10 }}>
      <label style={S.label}>প্রশ্নসমূহ</label>
      {qs.map((q, i) => (
        <div
          key={q.id}
          style={{
            border: `1px solid ${C.line}`,
            borderRadius: 12,
            padding: 10,
            marginBottom: 8,
            background: C.cream,
          }}
        >
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <b style={{ fontSize: 13 }}>{bn(i + 1)}.</b>
            <input
              style={{ ...S.input, flex: 1 }}
              value={q.q}
              onChange={(e) => upd(q.id, { q: e.target.value })}
              placeholder="প্রশ্ন লিখুন..."
            />
            <Btn
              sm
              kind="danger"
              onClick={() => setQs(qs.filter((x) => x.id !== q.id))}
            >
              ✕
            </Btn>
          </div>
          {q.type === "mcq" && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 6,
                marginTop: 8,
              }}
            >
              {q.options.map((op, oi) => (
                <div
                  key={oi}
                  style={{ display: "flex", gap: 6, alignItems: "center" }}
                >
                  <input
                    type="radio"
                    checked={q.correct === oi}
                    onChange={() => upd(q.id, { correct: oi })}
                    title="সঠিক উত্তর"
                  />
                  <input
                    style={{ ...S.input, padding: "7px 10px", fontSize: 13 }}
                    value={op}
                    placeholder={`অপশন ${bn(oi + 1)}`}
                    onChange={(e) =>
                      upd(q.id, {
                        options: q.options.map((o, j) =>
                          j === oi ? e.target.value : o,
                        ),
                      })
                    }
                  />
                </div>
              ))}
              <div style={{ gridColumn: "1/-1", fontSize: 11, color: C.muted }}>
                ⭕ রেডিও বাটনে সঠিক উত্তর নির্বাচন করুন — মূল্যায়নের সময়
                অটো-হিসাব দেখাবে
              </div>
            </div>
          )}
        </div>
      ))}
      <div style={{ display: "flex", gap: 8 }}>
        <Btn
          sm
          kind="ghost"
          onClick={() => setQs([...qs, { id: uid(), q: "", type: "text" }])}
        >
          + লিখিত প্রশ্ন
        </Btn>
        {allowMcq && (
          <Btn
            sm
            kind="ghost"
            onClick={() =>
              setQs([
                ...qs,
                {
                  id: uid(),
                  q: "",
                  type: "mcq",
                  options: ["", "", "", ""],
                  correct: 0,
                },
              ])
            }
          >
            + MCQ প্রশ্ন
          </Btn>
        )}
      </div>
    </div>
  );
}

/* স্টুডেন্টের জমা — ফরম পূরণ বা ছবি/PDF আপলোড */
function SubmitWork({ item, kind, onClose, onDone }) {
  const [ans, setAns] = useState({});
  const [img, setImg] = useState(null);
  const [note, setNote] = useState("");
  const [tab, setTab] = useState(
    item.mode === "form" && item.questions?.length ? "form" : "photo",
  );
  const pickFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () =>
      setImg({
        data: r.result,
        name: f.name,
        isPdf: f.type === "application/pdf",
      });
    r.readAsDataURL(f);
  };
  const submit = () => {
    if (
      tab === "form" &&
      item.questions.some((q) => !ans[q.id] && ans[q.id] !== 0)
    )
      return notice("Please answer all questions.");
    if (tab === "photo" && !img) return notice("Please select a photo or PDF.");
    onDone({
      answers: tab === "form" ? ans : null,
      image: tab === "photo" ? img : null,
      note: note.trim(),
    });
  };
  return (
    <Modal title={`Submit ${kind} — ${item.title}`} onClose={onClose} wide>
      {item.mode === "form" && item.questions?.length > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <Btn
            sm
            kind={tab === "form" ? "primary" : "soft"}
            onClick={() => setTab("form")}
          >
            📋 Fill Form
          </Btn>
          <Btn
            sm
            kind={tab === "photo" ? "primary" : "soft"}
            onClick={() => setTab("photo")}
          >
            📷 Take Photo
          </Btn>
        </div>
      )}
      {tab === "form" ? (
        <div>
          {item.questions.map((q, i) => (
            <div key={q.id} style={{ marginBottom: 14 }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 6 }}>
                {i + 1}. {q.q}
              </div>
              {q.type === "mcq" ? (
                <div style={{ display: "grid", gap: 6 }}>
                  {q.options.map((op, oi) => (
                    <label
                      key={oi}
                      style={{
                        display: "flex",
                        gap: 8,
                        alignItems: "center",
                        padding: "8px 12px",
                        borderRadius: 10,
                        cursor: "pointer",
                        border: `1.5px solid ${ans[q.id] === oi ? C.emerald : C.line}`,
                        background: ans[q.id] === oi ? C.greenBg : "#fff",
                        fontSize: 13.5,
                      }}
                    >
                      <input
                        type="radio"
                        name={q.id}
                        checked={ans[q.id] === oi}
                        onChange={() => setAns({ ...ans, [q.id]: oi })}
                      />{" "}
                      {op}
                    </label>
                  ))}
                </div>
              ) : (
                <textarea
                  rows={2}
                  style={{ ...S.input, resize: "vertical" }}
                  value={ans[q.id] || ""}
                  onChange={(e) => setAns({ ...ans, [q.id]: e.target.value })}
                  placeholder="Write your answer..."
                />
              )}
            </div>
          ))}
        </div>
      ) : (
        <div>
          <div style={{ fontSize: 13, color: C.muted, marginBottom: 8 }}>
            {item.desc}
          </div>
          <label
            style={{
              display: "grid",
              placeItems: "center",
              gap: 6,
              padding: "26px 14px",
              border: `2px dashed ${img ? C.emerald : C.line}`,
              borderRadius: 14,
              cursor: "pointer",
              background: img ? C.greenBg : C.cream,
              textAlign: "center",
            }}
          >
            <span style={{ fontSize: 30 }}>{img ? "✅" : "📷"}</span>
            <span style={{ fontSize: 13.5, fontWeight: 700 }}>
              {img ? img.name : "Take a photo or choose a file (image / PDF)"}
            </span>
            <input
              type="file"
              accept="image/*,application/pdf"
              capture="environment"
              style={{ display: "none" }}
              onChange={pickFile}
            />
          </label>
          {img && !img.isPdf && (
            <img
              src={img.data}
              alt="Submission"
              style={{
                width: "100%",
                borderRadius: 12,
                marginTop: 10,
                border: `1px solid ${C.line}`,
              }}
            />
          )}
        </div>
      )}
      <div style={{ marginTop: 8 }}>
        <label style={S.label}>Comment (optional)</label>
        <input
          style={S.input}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Any note for the teacher..."
        />
      </div>
      <Btn
        style={{ marginTop: 14, width: "100%", justifyContent: "center" }}
        onClick={submit}
      >
        Submit
      </Btn>
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
    return {
      ok: mcqs.filter((q) => sub.answers[q.id] === q.correct).length,
      total: mcqs.length,
    };
  };
  return (
    <Modal
      title={`মূল্যায়ন — ${item.title} (পূর্ণমান ${bn(item.total)})`}
      onClose={onClose}
      wide
    >
      {item.subs.length === 0 && (
        <div style={{ textAlign: "center", color: C.muted, padding: 16 }}>
          এখনো কেউ জমা দেয়নি।
        </div>
      )}
      {item.subs.map((sub) => {
        const auto = mcqScore(sub);
        const isOpen = open === sub.id;
        return (
          <div
            key={sub.id}
            style={{
              border: `1.5px solid ${sub.mark != null ? C.green : C.line}`,
              borderRadius: 14,
              marginBottom: 10,
              overflow: "hidden",
            }}
          >
            <div
              onClick={() => setOpen(isOpen ? null : sub.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "11px 14px",
                cursor: "pointer",
                background: sub.mark != null ? C.greenBg : C.cream,
                flexWrap: "wrap",
              }}
            >
              <b style={{ flex: 1, fontSize: 14, minWidth: 140 }}>
                {userById(sub.studentId).name}
              </b>
              <span style={{ fontSize: 12, color: C.muted }}>
                {fmtDate(sub.date)}
              </span>
              {sub.mark != null ? (
                <Tag>
                  মার্ক: {bn(sub.mark)}/{bn(item.total)} ✔
                </Tag>
              ) : (
                <Tag color={C.gold} bg={C.amberBg}>
                  মূল্যায়ন বাকি
                </Tag>
              )}
              <span style={{ fontSize: 13 }}>
                {isOpen ? "▲" : "▼ মূল্যায়ন করুন"}
              </span>
            </div>
            {isOpen && (
              <div style={{ padding: 14 }}>
                {sub.answers ? (
                  <div style={{ marginBottom: 10 }}>
                    {(item.questions || []).map((q, i) => (
                      <div
                        key={q.id}
                        style={{
                          marginBottom: 10,
                          padding: "9px 12px",
                          borderRadius: 10,
                          background: C.cream,
                        }}
                      >
                        <div style={{ fontWeight: 700, fontSize: 13 }}>
                          {bn(i + 1)}. {q.q}
                        </div>
                        {q.type === "mcq" ? (
                          <div style={{ fontSize: 13, marginTop: 3 }}>
                            উত্তর:{" "}
                            <b
                              style={{
                                color:
                                  sub.answers[q.id] === q.correct
                                    ? C.green
                                    : C.red,
                              }}
                            >
                              {q.options[sub.answers[q.id]] ?? "—"}{" "}
                              {sub.answers[q.id] === q.correct ? "✔" : "✘"}
                            </b>
                            {sub.answers[q.id] !== q.correct && (
                              <span style={{ color: C.muted }}>
                                {" "}
                                · সঠিক: {q.options[q.correct]}
                              </span>
                            )}
                          </div>
                        ) : (
                          <div
                            style={{
                              fontSize: 13.5,
                              marginTop: 3,
                              whiteSpace: "pre-wrap",
                            }}
                          >
                            {sub.answers[q.id] || "—"}
                          </div>
                        )}
                      </div>
                    ))}
                    {auto && (
                      <div
                        style={{
                          fontSize: 12.5,
                          fontWeight: 700,
                          color: C.blue,
                        }}
                      >
                        🤖 MCQ অটো-হিসাব: {bn(auto.ok)}/{bn(auto.total)} সঠিক
                      </div>
                    )}
                  </div>
                ) : sub.image ? (
                  <div style={{ marginBottom: 10 }}>
                    {sub.image.isPdf ? (
                      <a
                        href={sub.image.data}
                        download={sub.image.name}
                        style={{
                          display: "inline-flex",
                          gap: 8,
                          alignItems: "center",
                          padding: "12px 16px",
                          borderRadius: 12,
                          background: C.redBg,
                          color: C.red,
                          fontWeight: 700,
                          textDecoration: "none",
                          fontSize: 13.5,
                        }}
                      >
                        📄 {sub.image.name} — খুলুন/ডাউনলোড
                      </a>
                    ) : (
                      <a href={sub.image.data} target="_blank" rel="noreferrer">
                        <img
                          src={sub.image.data}
                          alt="জমা"
                          style={{
                            width: "100%",
                            borderRadius: 12,
                            border: `1px solid ${C.line}`,
                            cursor: "zoom-in",
                          }}
                        />
                      </a>
                    )}
                  </div>
                ) : (
                  <div
                    style={{ fontSize: 13, color: C.muted, marginBottom: 10 }}
                  >
                    📎 ফাইল সংযুক্ত নেই (পুরোনো/ডেমো জমা)
                  </div>
                )}
                {sub.note && (
                  <div
                    style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}
                  >
                    💬 স্টুডেন্টের মন্তব্য: “{sub.note}”
                  </div>
                )}
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    flexWrap: "wrap",
                    borderTop: `1px dashed ${C.line}`,
                    paddingTop: 10,
                  }}
                >
                  <label style={{ fontSize: 13, fontWeight: 700 }}>
                    মার্ক দিন:
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={item.total}
                    defaultValue={sub.mark ?? ""}
                    style={{ ...S.input, width: 90 }}
                    id={"mk-" + sub.id}
                    placeholder={`/${item.total}`}
                  />
                  <Btn
                    sm
                    onClick={() => {
                      const v = document.getElementById("mk-" + sub.id).value;
                      if (v === "") return;
                      onMark(sub, Math.min(+v, item.total));
                    }}
                  >
                    ✔ মার্ক জমা দিন
                  </Btn>
                  <span style={{ fontSize: 11.5, color: C.muted }}>
                    মার্ক দিলেই সাথে সাথে স্টুডেন্ট পোর্টালে চলে যাবে
                  </span>
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
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [show, setShow] = usePersistedState("asg_show", false);
  const [doSub, setDoSub] = useState(null);
  const [evalFor, setEvalFor] = useState(null);
  const [f, setF] = usePersistedState("asg_f", {
    courseId: courses[0]?.id,
    title: "",
    desc: "",
    due: addDays(3),
    mode: "form",
    total: 10,
  });
  const [qs, setQs] = usePersistedState("asg_qs", []);
  const [assignments, setAssignments] = useState(db.assignments);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে

  const adaptAssignment = (a) => ({
    id: a.id,
    courseId: a.course || a.courseId,
    teacherId: a.teacher || a.teacherId,
    title: a.title,
    desc: a.description || a.desc || "",
    due: a.due_date || a.due,
    mode: a.mode,
    total: a.total_marks || a.total,
    questions: (a.questions || []).map((q) => ({
      id: q.id,
      q: q.text || q.q,
      type: q.qtype || q.type,
      options: q.options || [],
      correct: q.correct_index ?? q.correct,
    })),
    subs: (a.submissions || a.subs || []).map((s) => ({
      id: s.id,
      studentId: s.student || s.studentId,
      student_name: s.student_name,
      date: s.submitted_at || s.date,
      mark: s.mark,
      answers: s.answers,
      note: s.note,
    })),
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api.assignments();
      setAssignments(data.map(adaptAssignment));
    } catch {
      setAssignments(db.assignments);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const list = assignments.filter((a) => courseById(courses, a.courseId).id);
  const canCreate = user.role === "teacher" || isAdm(user);
  const add = async () => {
    if (!f.title) return notice("শিরোনাম দিন।");
    if (f.mode === "form" && qs.length === 0)
      return notice("ফরম মোডে অন্তত একটি প্রশ্ন যোগ করুন।");
    try {
      await api.createAssignment({
        course: f.courseId,
        title: f.title,
        description: f.desc,
        due_date: f.due,
        mode: f.mode,
        total_marks: +f.total,
        questions:
          f.mode === "form"
            ? qs.map((q) => ({
                text: q.q,
                qtype: q.type,
                options: q.options || [],
                correct_index: q.correct,
              }))
            : [],
      });
      await loadData();
      notice("✔ অ্যাসাইনমেন্ট তৈরি হয়েছে।");
    } catch (e) {
      notice(
        "অ্যাসাইনমেন্ট তৈরি করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
      return;
    }
    setShow(false);
    setQs([]);
  };
  const del = async (id) => {
    try {
      await api.deleteAssignment(id);
      await loadData();
      notice("✔ অ্যাসাইনমেন্ট মুছে ফেলা হয়েছে।");
    } catch (e) {
      notice(
        "অ্যাসাইনমেন্ট মুছতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const submitWork = async (a, payload) => {
    try {
      await api.submitAssignment(a.id, payload);
      await loadData();
      notice(T("✔ জমা হয়েছে।", "✔ Submitted."));
    } catch (e) {
      notice(
        T("জমা দিতে ব্যর্থ — ", "Failed to submit — ") +
          (e?.data?.error ||
            e?.message ||
            T(
              "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন",
              "check your connection and try again",
            )),
      );
      return;
    }
    setDoSub(null);
  };
  const giveMark = async (a, sub, mark) => {
    try {
      await api.gradeAssignment(a.id, sub.id, mark);
      await loadData();
      notice("✔ মার্ক সেভ হয়েছে।");
    } catch (e) {
      notice(
        "মার্ক সেভ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  return (
    <Section
      title={T("অ্যাসাইনমেন্ট", "Assignments")}
      sub="ফরম বানিয়ে বা ছবি জমার নির্দেশনা দিয়ে — মূল্যায়ন করলেই মার্ক স্টুডেন্ট পোর্টালে"
      action={
        canCreate && (
          <Btn onClick={() => setShow(true)}>+ নতুন অ্যাসাইনমেন্ট</Btn>
        )
      }
    >
      <div style={{ display: "grid", gap: 10 }}>
        {loading && <Loader text={T("লোড হচ্ছে", "Loading")} />}
        {!loading && list.length === 0 && (
          <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>
            {T("এখনো কোনো অ্যাসাইনমেন্ট নেই।", "No assignments yet.")}
          </div>
        )}
        {list.map((a) => {
          const c = courseById(courses, a.courseId);
          const mySub = a.subs.find((s) => s.studentId === user.id);
          const pendingEval = a.subs.filter((s) => s.mark == null).length;
          return (
            <div key={a.id} style={{ ...S.card, padding: 16 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 10,
                  flexWrap: "wrap",
                }}
              >
                <div style={{ flex: 1, minWidth: 220 }}>
                  <div style={{ fontWeight: 800 }}>
                    {a.title}{" "}
                    <Tag color={C.blue} bg={C.blueBg}>
                      {c.name}
                    </Tag>{" "}
                    <Tag
                      color={a.mode === "form" ? C.emerald : C.gold}
                      bg={a.mode === "form" ? C.greenBg : C.amberBg}
                    >
                      {T(
                      a.mode === "form" ? "📋 ফরম" : "📷 ছবি জমা",
                      a.mode === "form" ? "📋 Form" : "📷 Photo Submission",
                    )}
                    </Tag>
                  </div>
                  <div
                    style={{ fontSize: 13, color: C.muted, margin: "5px 0" }}
                  >
                    {a.desc}
                  </div>
                  <div style={{ fontSize: 12 }}>
                    {T("📅 শেষ তারিখ", "📅 Due date")}:{" "}
                    <b>{fmtDate(a.due)}</b> ·{" "}
                    {T("পূর্ণমান", "Total marks")}: <b>{T(bn(a.total), a.total)}</b> ·{" "}
                    {T("জমা", "Submitted")}:{" "}
                    <b>{T(bn(a.subs.length), a.subs.length)}</b>{" "}
                    {T("জন", "")}
                    {canCreate && pendingEval > 0 && (
                      <span style={{ color: C.red }}>
                        {" "}
                        · মূল্যায়ন বাকি: {bn(pendingEval)}
                      </span>
                    )}
                  </div>
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 6,
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                  }}
                >
                  {user.role === "student" &&
                    (mySub ? (
                      mySub.mark != null ? (
                        <Tag>
                          Marks obtained: {mySub.mark}/{a.total} ✔
                        </Tag>
                      ) : (
                        <Tag color={C.gold} bg={C.amberBg}>
                          Submitted — awaiting evaluation
                        </Tag>
                      )
                    ) : (
                      <Btn sm kind="gold" onClick={() => setDoSub(a)}>
                        {a.mode === "form"
                          ? "📋 Fill & Submit Form"
                          : "📷 Take Photo & Submit"}
                      </Btn>
                    ))}
                  {canCreate && (
                    <Btn sm kind="ghost" onClick={() => setEvalFor(a)}>
                      🔍 মূল্যায়ন করুন ({bn(a.subs.length)})
                    </Btn>
                  )}
                  {isAdm(user) && (
                    <Btn sm kind="danger" onClick={() => del(a.id)}>
                      মুছুন
                    </Btn>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {doSub && (
        <SubmitWork
          item={doSub}
          kind="Assignment"
          onClose={() => setDoSub(null)}
          onDone={(p) => submitWork(doSub, p)}
        />
      )}
      {evalFor && (
        <EvalWork
          item={assignments.find((x) => x.id === evalFor.id)}
          onClose={() => setEvalFor(null)}
          onMark={(sub, m) => giveMark(evalFor, sub, m)}
        />
      )}
      {show && (
        <Modal
          title="নতুন অ্যাসাইনমেন্ট বানান"
          onClose={() => setShow(false)}
          wide
        >
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}
          >
            <div>
              <label style={S.label}>কোর্স</label>
              <select
                style={S.input}
                value={f.courseId}
                onChange={(e) => setF({ ...f, courseId: e.target.value })}
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={S.label}>পূর্ণমান</label>
              <input
                type="number"
                style={S.input}
                value={f.total}
                onChange={(e) => setF({ ...f, total: e.target.value })}
              />
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>শিরোনাম</label>
            <input
              style={S.input}
              value={f.title}
              onChange={(e) => setF({ ...f, title: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>নির্দেশনা / বিবরণ</label>
            <textarea
              rows={2}
              style={{ ...S.input, resize: "vertical" }}
              value={f.desc}
              onChange={(e) => setF({ ...f, desc: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>জমা দেওয়ার ধরন — যেটা ইচ্ছা বানান</label>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}
            >
              <button
                onClick={() => setF({ ...f, mode: "form" })}
                style={{
                  padding: "12px",
                  borderRadius: 12,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: 700,
                  fontSize: 13,
                  border: `2px solid ${f.mode === "form" ? C.emerald : C.line}`,
                  background: f.mode === "form" ? C.greenBg : "#fff",
                }}
              >
                📋 ফরম — প্রশ্ন বানিয়ে দিন
              </button>
              <button
                onClick={() => setF({ ...f, mode: "photo" })}
                style={{
                  padding: "12px",
                  borderRadius: 12,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: 700,
                  fontSize: 13,
                  border: `2px solid ${f.mode === "photo" ? C.emerald : C.line}`,
                  background: f.mode === "photo" ? C.greenBg : "#fff",
                }}
              >
                📷 ছবি/PDF জমা
              </button>
            </div>
          </div>
          {f.mode === "form" && (
            <QBuilder qs={qs} setQs={setQs} allowMcq={false} />
          )}
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>শেষ তারিখ</label>
            <input
              type="date"
              style={S.input}
              value={f.due}
              onChange={(e) => setF({ ...f, due: e.target.value })}
            />
          </div>
          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
            onClick={add}
          >
            প্রকাশ করুন
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ পরীক্ষা (ফিচার ৬) — ফরম (MCQ/লিখিত) বা ছবি, মূল্যায়নসহ ═══════════════ */
function ExamsView({ db, setDb, courses, user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [show, setShow] = usePersistedState("exam_show", false);
  const [marksFor, setMarksFor] = useState(null);
  const [doSub, setDoSub] = useState(null);
  const [evalFor, setEvalFor] = useState(null);
  const [f, setF] = usePersistedState("exam_f", {
    type: "mcq",
    title: "",
    courseId: courses[0]?.id,
    total: 30,
    date: addDays(7),
    mode: "form",
  });
  const [qs, setQs] = usePersistedState("exam_qs", []);
  const [exams, setExams] = useState(db.exams);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে

  const adaptExam = (e) => ({
    id: e.id,
    courseId: e.course || e.courseId,
    type: e.exam_type || e.type,
    title: e.title,
    total: e.total_marks || e.total,
    date: e.date,
    mode: e.mode,
    questions: (e.questions || []).map((q) => ({
      id: q.id,
      q: q.text || q.q,
      type: q.qtype || q.type,
      options: q.options || [],
      correct: q.correct_index ?? q.correct,
    })),
    subs: (e.submissions || e.subs || []).map((s) => ({
      id: s.id,
      studentId: s.student || s.studentId,
      student_name: s.student_name,
      date: s.submitted_at || s.date,
      mark: s.mark,
      answers: s.answers,
      note: s.note,
    })),
    marks: e.results || e.marks || {},
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api.exams();
      setExams(data.map(adaptExam));
    } catch {
      setExams(db.exams);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const list = exams.filter((e) => courseById(courses, e.courseId).id);
  const canCreate = isAdm(user) || user.role === "teacher";
  const add = async () => {
    if (!f.title) return notice("শিরোনাম দিন।");
    if (f.mode === "form" && qs.length === 0)
      return notice("ফরম মোডে অন্তত একটি প্রশ্ন যোগ করুন।");
    try {
      await api.createExam({
        course: f.courseId,
        exam_type: f.type,
        title: f.title,
        date: f.date,
        mode: f.mode,
        total_marks: +f.total,
        questions:
          f.mode === "form"
            ? qs.map((q) => ({
                text: q.q,
                qtype: q.type,
                options: q.options || [],
                correct_index: q.correct,
              }))
            : [],
      });
      await loadData();
      notice("✔ পরীক্ষা তৈরি হয়েছে।");
    } catch (e) {
      notice(
        "পরীক্ষা তৈরি করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
      return;
    }
    setShow(false);
    setQs([]);
  };
  const saveMark = async (ex, sid, val) => {
    try {
      await api.examDirectMark(ex.id, sid, +val);
      await loadData();
      notice("✔ মার্ক সেভ হয়েছে।");
    } catch (e) {
      notice(
        "মার্ক সেভ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const submitWork = async (ex, payload) => {
    try {
      await api.submitExam(ex.id, payload);
      await loadData();
      notice(T("✔ জমা হয়েছে।", "✔ Submitted."));
    } catch (e) {
      notice(
        T("জমা দিতে ব্যর্থ — ", "Failed to submit — ") +
          (e?.data?.error ||
            e?.message ||
            T(
              "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন",
              "check your connection and try again",
            )),
      );
      return;
    }
    setDoSub(null);
  };
  const giveMark = async (ex, sub, mark) => {
    try {
      await api.gradeExam(ex.id, sub.id, mark);
      await loadData();
      notice("✔ মার্ক সেভ হয়েছে।");
    } catch (e) {
      notice(
        "মার্ক সেভ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  return (
    <Section
      title={T("পরীক্ষা — মাসিক MCQ ও লাইভ টেস্ট", "Exams — Monthly MCQ & Live Tests")}
      sub="ফরমে (MCQ/লিখিত) বা ছবিতে — মূল্যায়ন করলেই ফলাফল অটো স্টুডেন্ট পোর্টালে"
      action={
        canCreate && (
          <Btn onClick={() => setShow(true)}>+ নতুন পরীক্ষা বানান</Btn>
        )
      }
    >
      <div style={{ display: "grid", gap: 10 }}>
        {loading && <Loader text={T("লোড হচ্ছে", "Loading")} />}
        {list.map((ex) => {
          const c = courseById(courses, ex.courseId);
          const myMark = ex.marks[user.id];
          const mySub = ex.subs?.find((s) => s.studentId === user.id);
          const pendingEval = (ex.subs || []).filter(
            (s) => s.mark == null,
          ).length;
          return (
            <div key={ex.id} style={{ ...S.card, padding: 16 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 10,
                  flexWrap: "wrap",
                  alignItems: "center",
                }}
              >
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontWeight: 800 }}>
                    {ex.title}{" "}
                    {ex.type === "mcq" ? (
                      <Tag color={C.blue} bg={C.blueBg}>
                        MCQ
                      </Tag>
                    ) : (
                      <Tag color={C.gold} bg={C.amberBg}>
                        {T("লাইভ টেস্ট", "Live Test")}
                      </Tag>
                    )}{" "}
                    <Tag
                      color={ex.mode === "form" ? C.emerald : C.gold}
                      bg={ex.mode === "form" ? C.greenBg : C.amberBg}
                    >
                      {T(
                        ex.mode === "form" ? "📋 ফরম" : "📷 ছবি/খাতা",
                        ex.mode === "form" ? "📋 Form" : "📷 Photo/Answer sheet",
                      )}
                    </Tag>
                  </div>
                  <div style={{ fontSize: 12.5, color: C.muted }}>
                    {c.name} · {fmtDate(ex.date)} ·{" "}
                    {T(`পূর্ণমান ${bn(ex.total)}`, `Total marks ${ex.total}`)}
                    {canCreate && pendingEval > 0 && (
                      <span style={{ color: C.red }}>
                        {" "}
                        · মূল্যায়ন বাকি: {bn(pendingEval)}
                      </span>
                    )}
                  </div>
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 6,
                    alignItems: "center",
                    flexWrap: "wrap",
                  }}
                >
                  {user.role === "student" &&
                    (myMark != null ? (
                      <div style={{ textAlign: "right" }}>
                        <div
                          style={{
                            fontSize: 22,
                            fontWeight: 900,
                            color: C.emerald,
                          }}
                        >
                          {myMark}
                          <span style={{ fontSize: 13, color: C.muted }}>
                            /{ex.total}
                          </span>
                        </div>
                        <Tag
                          color={myMark / ex.total >= 0.8 ? C.green : C.gold}
                          bg={myMark / ex.total >= 0.8 ? C.greenBg : C.amberBg}
                        >
                          {myMark / ex.total >= 0.8
                            ? "Mumtaz (Excellent)"
                            : "Jayyid (Good)"}
                        </Tag>
                      </div>
                    ) : mySub ? (
                      <Tag color={C.gold} bg={C.amberBg}>
                        Submitted — awaiting result
                      </Tag>
                    ) : (
                      <Btn sm kind="gold" onClick={() => setDoSub(ex)}>
                        {ex.mode === "form"
                          ? "📋 Take Exam"
                          : "📷 Submit Answer Sheet Photo"}
                      </Btn>
                    ))}
                  {canCreate && (
                    <Btn sm kind="ghost" onClick={() => setEvalFor(ex)}>
                      🔍 মূল্যায়ন ({bn((ex.subs || []).length)})
                    </Btn>
                  )}
                  {canCreate && (
                    <Btn sm kind="soft" onClick={() => setMarksFor(ex)}>
                      সরাসরি মার্ক এন্ট্রি
                    </Btn>
                  )}
                  {isDir(user) && (
                    <Btn
                      sm
                      kind="danger"
                      onClick={async () => {
                        try {
                          await api.deleteExam(ex.id);
                          await loadData();
                        } catch {
                          setExams((p) => p.filter((x) => x.id !== ex.id));
                        }
                      }}
                    >
                      মুছুন
                    </Btn>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {doSub && (
        <SubmitWork
          item={doSub}
          kind="Exam"
          onClose={() => setDoSub(null)}
          onDone={(p) => submitWork(doSub, p)}
        />
      )}
      {evalFor && (
        <EvalWork
          item={exams.find((x) => x.id === evalFor.id)}
          onClose={() => setEvalFor(null)}
          onMark={(sub, m) => giveMark(evalFor, sub, m)}
        />
      )}
      {show && (
        <Modal title="নতুন পরীক্ষা বানান" onClose={() => setShow(false)} wide>
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}
          >
            <div>
              <label style={S.label}>ধরন</label>
              <select
                style={S.input}
                value={f.type}
                onChange={(e) => setF({ ...f, type: e.target.value })}
              >
                <option value="mcq">মাসিক MCQ</option>
                <option value="live">লাইভ টেস্ট</option>
              </select>
            </div>
            <div>
              <label style={S.label}>কোর্স</label>
              <select
                style={S.input}
                value={f.courseId}
                onChange={(e) => setF({ ...f, courseId: e.target.value })}
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={S.label}>পূর্ণমান</label>
              <input
                type="number"
                style={S.input}
                value={f.total}
                onChange={(e) => setF({ ...f, total: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>তারিখ</label>
              <input
                type="date"
                style={S.input}
                value={f.date}
                onChange={(e) => setF({ ...f, date: e.target.value })}
              />
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>শিরোনাম</label>
            <input
              style={S.input}
              value={f.title}
              onChange={(e) => setF({ ...f, title: e.target.value })}
              placeholder="যেমন: মাসিক MCQ — জুলাই ২০২৬"
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>পরীক্ষার ধরন — যেটা ইচ্ছা বানান</label>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}
            >
              <button
                onClick={() => setF({ ...f, mode: "form" })}
                style={{
                  padding: "12px",
                  borderRadius: 12,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: 700,
                  fontSize: 13,
                  border: `2px solid ${f.mode === "form" ? C.emerald : C.line}`,
                  background: f.mode === "form" ? C.greenBg : "#fff",
                }}
              >
                📋 ফরম — MCQ/লিখিত প্রশ্ন বানান
              </button>
              <button
                onClick={() => setF({ ...f, mode: "photo" })}
                style={{
                  padding: "12px",
                  borderRadius: 12,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: 700,
                  fontSize: 13,
                  border: `2px solid ${f.mode === "photo" ? C.emerald : C.line}`,
                  background: f.mode === "photo" ? C.greenBg : "#fff",
                }}
              >
                📷 খাতার ছবি/PDF জমা
              </button>
            </div>
          </div>
          {f.mode === "form" && (
            <QBuilder qs={qs} setQs={setQs} allowMcq={true} />
          )}
          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
            onClick={add}
          >
            তৈরি করুন
          </Btn>
        </Modal>
      )}
      {marksFor && (
        <Modal
          title={`সরাসরি মার্ক এন্ট্রি — ${marksFor.title}`}
          onClose={() => setMarksFor(null)}
        >
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>
            লাইভ টেস্টের মতো জমা ছাড়া পরীক্ষার জন্য — মার্ক দিলেই স্টুডেন্ট
            পোর্টালে দেখাবে।
          </div>
          {courseById(courses, marksFor.courseId).studentIds.map((sid) => (
            <div
              key={sid}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 8,
              }}
            >
              <span style={{ flex: 1, fontSize: 14 }}>
                {userById(sid).name}
              </span>
              <input
                type="number"
                min="0"
                max={marksFor.total}
                style={{ ...S.input, width: 90 }}
                defaultValue={
                  exams.find((x) => x.id === marksFor.id)?.marks[sid] ?? ""
                }
                onBlur={(e) =>
                  e.target.value !== "" &&
                  saveMark(marksFor, sid, e.target.value)
                }
                placeholder={`/${marksFor.total}`}
              />
            </div>
          ))}
          <div style={{ fontSize: 12, color: C.muted }}>
            ঘর থেকে বের হলেই মার্ক সংরক্ষিত হবে।
          </div>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ স্টুডেন্ট প্রোফাইল ও অগ্রগতি রিপোর্ট (ফিচার ৭) ═══════════════ */
function ProgressView({ db, setDb, courses, user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [allStudents, setAllStudents] = useState(
    user.role === "student"
      ? [user]
      : [],
  );
  /* সিলেবাস অগ্রগতি — আগে হিসাব হতো coverageOf(course) দিয়ে, যা
     api.lectures()-এর পুরনো "সবার-জন্য-একটাই" covered মান পড়ত। কভার এখন
     প্রতি শিক্ষার্থীর আলাদা, তাই ওই মান আর বসে না — বারটা সবার জন্য ০%
     দেখাত। এখন দারস পরিকল্পনার হেডিং থেকেই আনা হয়, শিক্ষার্থীর নিজের
     টিক ধরে। { [courseId]: {done,total,pct} } */
  const [progress, setProgress] = useState({});
  useEffect(() => {
    let alive = true;
    const who = user.role === "student" ? null : undefined; // শিক্ষার্থী হলে সার্ভার নিজেই তারটা দেয়
    Promise.all(
      (courses || []).map((c) =>
        api
          .lessonSections(c.id, who)
          .then((rows) => {
            const all = (rows || []).flatMap((x) => x.topics || []);
            const done = all.filter((t) => t.covered === "covered").length;
            return [
              c.id,
              {
                done,
                total: all.length,
                pct: all.length ? Math.round((done / all.length) * 100) : 0,
              },
            ];
          })
          .catch(() => [c.id, { done: 0, total: 0, pct: 0 }]),
      ),
    ).then((pairs) => alive && setProgress(Object.fromEntries(pairs)));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courses.map((c) => c.id).join(",")]);

  const [pay, setPay] = useState(false);
  const [maker, setMaker] = useState(false);
  const [pf, setPf] = useState({ method: "বিকাশ", trx: "" });
  const [sel, setSel] = useState(allStudents[0]?.id || user.id);
  // তালিকা লোড হলে সিলেকশন প্রথম স্টুডেন্টে বসাই (আগে খালি থাকলে)
  useEffect(() => {
    if (
      user.role !== "student" &&
      allStudents.length &&
      !allStudents.some((s) => String(s.id) === String(sel))
    )
      setSel(allStudents[0].id);
  }, [allStudents]);
  const [fees, setFees] = useState(db.feePayments || []);
  const [duesMap, setDuesMap] = useState(db.dueMonths || {});
  const [sessions, setSessions] = useState(null);
  const [examList, setExamList] = useState(db.exams || []);
  const [remarks, setRemarks] = useState([]);
  useEffect(() => {
    if (!sel) return;
    api.studentRemarks(sel).then(setRemarks).catch(() => setRemarks([]));
  }, [sel]);

  const loadData = async () => {
    try {
      const tasks = [api.myFees(), api.myDues(), api.classes(), api.exams()];
      if (user.role !== "student") tasks.push(api.allStudents());
      const [feesData, duesData, sessData, examsData, studsData] =
        await Promise.all(tasks);
      setFees(
        feesData.map((p) => ({
          id: p.id,
          studentId: p.student || p.studentId,
          amount: +p.amount,
          month: p.month_label || p.month,
          date: p.paid_at || p.date,
          method: p.method + (p.trx_id ? ` (Trx: ${p.trx_id})` : ""),
          status: p.status,
        })),
      );
      const dm = {};
      duesData.forEach((d) => {
        const uid2 = String(d.user || d.userId);
        if (!dm[uid2]) dm[uid2] = [];
        dm[uid2].push(d.month_label || d.month);
      });
      setDuesMap(dm);
      setSessions(sessData);
      setExamList(
        examsData.map((e) => ({
          ...e,
          courseId: e.course || e.courseId,
          total: e.total_marks || e.total,
          marks: e.results || e.marks || {},
        })),
      );
      if (studsData)
        setAllStudents(
          studsData.map((s) => ({
            id: s.id,
            name: s.name || s.name_bn,
            sub: s.sub || s.sub_title,
            fee: s.monthly_fee || s.fee,
            phone: s.phone,
            email: s.email,
            role: "student",
          })),
        );
    } catch {
      /* keep mock */
    }
  };
  useEffect(() => {
    loadData();
  }, [user.id]);

  const st =
    allStudents.find((s) => String(s.id) === String(sel)) || userById(sel);
  const selId = String(sel);
  const stCourses = courses.filter((c) =>
    (c.studentIds || c.students || []).some((x) => String(x) === selId),
  );
  const att = sessions
    ? sessions.flatMap((k) =>
        (k.attendance || [])
          .filter((a) => String(a.user) === selId)
          .map((a) => ({ minutes: a.minutes || 0 })),
      )
    : db.attendance.filter((a) => String(a.userId) === selId);
  const present = att.filter((a) => (a.present ?? a.minutes >= 45)).length;
  const missed = att.filter((a) => !(a.present ?? a.minutes >= 45)).length;
  const myFees = fees.filter((p) => String(p.studentId) === selId);
  const paid = myFees.reduce((s, p) => s + (+p.amount || 0), 0);
  const dueMonths = duesMap[selId] || db.dueMonths?.[sel] || [];
  const due = dueMonths.length * (st?.monthly_fee || st?.fee || 0);
  // "মেকআপ ক্লাস" আলাদা কোনো ফিচার/এন্ডপয়েন্ট নয় — kind="makeup" দিয়ে সিডিউল
  // করা একটা সাধারণ ক্লাস; আগে stale mock db.makeups (সবসময় খালি) থেকে আসত,
  // এখন ইতিমধ্যে লোড করা sessions থেকেই বের করা হচ্ছে
  const makeups = (sessions || []).filter(
    (k) => k.kind === "makeup" && (k.students || []).some((x) => String(x) === selId),
  );
  const exams = examList.filter((e) => e.marks && e.marks[sel] != null);
  const recordPay = async () => {
    const month = dueMonths[0];
    if (!month) return;
    try {
      await api.payFee({
        amount: st.fee,
        month_label: month,
        method: "নগদ গ্রহণ (অফিস)",
      });
      await loadData();
      notice(`✔ ${month} মাসের ফি পরিশোধ রেকর্ড করা হয়েছে।`);
    } catch (e) {
      notice(
        "পেমেন্ট রেকর্ড করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const studentPay = async () => {
    const month = dueMonths[0];
    if (!month) return;
    try {
      await api.payFee({
        amount: st.fee,
        month_label: month,
        method: pf.method,
        trx_id: pf.trx,
      });
      await loadData();
      notice(`✔ ${month} মাসের ফি জমা হয়েছে — ভেরিফাই বাকি।`);
    } catch (e) {
      notice(
        "ফি জমা দিতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
      return;
    }
    setPay(false);
    setPf({ method: "বিকাশ", trx: "" });
  };
  const verifyPay = async (pid) => {
    try {
      await api.verifyFee(pid);
      await loadData();
      notice("✔ পেমেন্ট ভেরিফাই হয়েছে।");
    } catch (e) {
      notice(
        "ভেরিফাই করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  return (
    <Section
      title={T("শিক্ষার্থীর অগ্রগতি ও রিপোর্ট", "Student Progress & Report")}
      sub={T(
        "অগ্রগতি · ফি · মিসিং ক্লাস · মেকআপ ক্লাস — সব এক জায়গায়",
        "Progress · Fees · Missed classes · Makeup classes — all in one place",
      )}
      action={
        isAdm(user) && (
          <Btn kind="gold" sm onClick={() => setMaker(true)}>
            🧾 রিসিট বানান
          </Btn>
        )
      }
    >
      {maker && <ReceiptMaker user={user} onClose={() => setMaker(false)} />}
      {user.role !== "student" && (
        <div
          style={{
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
            marginBottom: 14,
          }}
        >
          {allStudents.map((s) => (
            <Btn
              key={s.id}
              sm
              kind={String(sel) === String(s.id) ? "primary" : "soft"}
              onClick={() => setSel(s.id)}
            >
              {s.name}
            </Btn>
          ))}
        </div>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: 10,
          marginBottom: 14,
        }}
      >
        <Stat
          icon="✅"
          label={T("উপস্থিত ক্লাস", "Classes Attended")}
          value={T(bn(present), present)}
        />
        <Stat
          icon="❌"
          label={T("মিসিং ক্লাস", "Classes Missed")}
          value={T(bn(missed), missed)}
          accent={C.red}
          note={T(
            "৪৫ মিনিটের কম উপস্থিতিসহ",
            "Includes attendance under 45 minutes",
          )}
        />
        <Stat
          icon="💰"
          label={T("পরিশোধিত ফি", "Fees Paid")}
          value={`৳${bn(paid.toLocaleString("en"))}`}
          accent={C.gold}
        />
        <Stat
          icon="⏳"
          label={T("বকেয়া", "Due")}
          value={`৳${bn(due.toLocaleString("en"))}`}
          accent={C.red}
          note={dueMonths.join(", ") || T("নেই", "None")}
        />
      </div>
      <div style={{ display: "grid", gap: 14 }}>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>
            {T("📈 কোর্সভিত্তিক সিলেবাস অগ্রগতি", "📈 Syllabus Progress by Course")}
          </div>
          {stCourses.map((c) => {
            const cv = progress[c.id] || { done: 0, total: 0, pct: 0 };
            return (
              <div key={c.id} style={{ marginBottom: 10 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 13,
                    marginBottom: 4,
                  }}
                >
                  <span>{c.name}</span>
                  <b>{bn(cv.pct)}%</b>
                </div>
                <div
                  style={{ height: 9, background: C.cream, borderRadius: 99 }}
                >
                  <div
                    style={{
                      width: cv.pct + "%",
                      height: "100%",
                      background: c.color,
                      borderRadius: 99,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
        <div style={{ ...S.card }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: 8,
              marginBottom: 10,
            }}
          >
            <div style={{ fontWeight: 800 }}>
              {T("💳 ফি পরিশোধের ইতিহাস", "💳 Fee Payment History")}
            </div>
            <span style={{ display: "flex", gap: 8 }}>
              {user.role === "student" && due > 0 && (
                <Btn sm kind="gold" onClick={() => setPay(true)}>
                  💳 Pay Fee
                </Btn>
              )}
              {isAdm(user) && due > 0 && (
                <Btn sm kind="gold" onClick={recordPay}>
                  + এক মাসের পেমেন্ট রেকর্ড করুন
                </Btn>
              )}
            </span>
          </div>
          <Table
            head={T(
              ["মাস", "পরিমাণ", "তারিখ", "মাধ্যম", "অবস্থা"],
              ["Month", "Amount", "Date", "Method", "Status"],
            )}
            rows={myFees.map((p) => [
              p.month,
              `৳${bn((+p.amount).toLocaleString("en"))}`,
              fmtDate(p.date),
              p.method,
              p.status === "pending" ? (
                isDir(user) ? (
                  <Btn key="v" sm kind="gold" onClick={() => verifyPay(p.id)}>
                    ✔ ভেরিফাই করুন
                  </Btn>
                ) : (
                  <Tag key="t" color={C.gold} bg={C.amberBg}>
                    {T("⏳ পেন্ডিং", "⏳ Pending")}
                  </Tag>
                )
              ) : (
                <Tag key="t">{T("যাচাইকৃত ✔", "Verified ✔")}</Tag>
              ),
            ])}
            empty={T("কোনো পেমেন্ট নেই", "No payments yet")}
          />
          {pay && (
            <Modal
              title={T(
                `ফি পরিশোধ — ${dueMonths[0] || ""}`,
                `Pay Fee — ${dueMonths[0] || ""}`,
              )}
              onClose={() => setPay(false)}
            >
              <div
                style={{
                  ...S.card,
                  padding: 12,
                  background: C.amberBg,
                  border: "none",
                  marginBottom: 12,
                  fontSize: 13,
                }}
              >
                {T(
                  <>
                    পরিমাণ: <b>৳{bn((st.fee || 0).toLocaleString("en"))}</b> ·
                    পরিশোধের পর এডমিন যাচাই করলে নিশ্চিত হবে।
                  </>,
                  <>
                    Amount: <b>৳{(st.fee || 0).toLocaleString("en")}</b> · Once
                    paid, it will be confirmed after admin verification.
                  </>,
                )}
              </div>
              <label style={S.label}>{T("পেমেন্ট মাধ্যম", "Payment Method")}</label>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 8,
                  marginBottom: 12,
                }}
              >
                {["বিকাশ", "নগদ", "ব্যাংক ট্রান্সফার"].map((m) => (
                  <button
                    key={m}
                    onClick={() => setPf({ ...pf, method: m })}
                    style={{
                      padding: "12px 6px",
                      borderRadius: 10,
                      cursor: "pointer",
                      fontFamily: "inherit",
                      fontWeight: 700,
                      fontSize: 13,
                      border: `2px solid ${pf.method === m ? C.emerald : C.line}`,
                      background: pf.method === m ? C.greenBg : "#fff",
                      color: pf.method === m ? C.emerald : C.text,
                    }}
                  >
                    {m === "বিকাশ" ? "📱" : m === "নগদ" ? "🟠" : "🏦"}
                    <br />
                    {T(
                      m,
                      m === "বিকাশ"
                        ? "bKash"
                        : m === "নগদ"
                          ? "Nagad"
                          : "Bank Transfer",
                    )}
                  </button>
                ))}
              </div>
              <label style={S.label}>
                {T(
                  "ট্রানজেকশন আইডি / রেফারেন্স (ঐচ্ছিক)",
                  "Transaction ID / Reference (optional)",
                )}
              </label>
              <input
                style={S.input}
                value={pf.trx}
                onChange={(e) => setPf({ ...pf, trx: e.target.value })}
                placeholder="e.g. 9HX2K7..."
              />
              <Btn
                style={{
                  marginTop: 14,
                  width: "100%",
                  justifyContent: "center",
                }}
                onClick={studentPay}
              >
                {T("পরিশোধ সম্পন্ন করুন", "Complete Payment")}
              </Btn>
            </Modal>
          )}
        </div>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>
            {T("📝 পরীক্ষার ফলাফল", "📝 Exam Results")}
          </div>
          <Table
            head={T(["পরীক্ষা", "তারিখ", "প্রাপ্ত মার্ক"], ["Exam", "Date", "Marks Obtained"])}
            rows={exams.map((e) => [
              e.title,
              fmtDate(e.date),
              T(`${bn(e.marks[sel])}/${bn(e.total)}`, `${e.marks[sel]}/${e.total}`),
            ])}
            empty={T("এখনো কোনো ফল নেই", "No results yet")}
          />
        </div>
        {user.role === "student" && (
          <div style={{ ...S.card }}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>
              {T("💬 টিচারের মন্তব্য", "💬 Teacher's Comment")}
            </div>
            {remarks.length > 0 ? (
              <div
                style={{
                  padding: "12px 14px",
                  borderRadius: 10,
                  background: C.cream,
                  fontSize: 13.5,
                  lineHeight: 1.6,
                }}
              >
                {remarks[0].text}
                <div style={{ fontSize: 11.5, color: C.muted, marginTop: 8 }}>
                  — {remarks[0].teacher_name} · {fmtDate(remarks[0].created_at)}
                </div>
              </div>
            ) : (
              <div style={{ color: C.muted, fontSize: 13, textAlign: "center", padding: 8 }}>
                {T("এখনো কোনো মন্তব্য নেই", "No comments yet")}
              </div>
            )}
          </div>
        )}
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>
            {T("🔁 মেকআপ ক্লাস", "🔁 Makeup Classes")}
          </div>
          <Table
            head={T(
              ["কোর্স", "তারিখ ও সময়", "অবস্থা"],
              ["Course", "Date & Time", "Status"],
            )}
            rows={makeups.map((m) => [
              courseById(courses, m.course || m.courseId).name,
              `${fmtDate(m.date)} · ${m.time}`,
              <Tag key="t" color={C.blue} bg={C.blueBg}>
                {T(
                  m.status === "done" ? "সম্পন্ন" : m.status === "postponed" ? "স্থগিত" : "নির্ধারিত",
                  m.status === "done" ? "Completed" : m.status === "postponed" ? "Postponed" : "Scheduled",
                )}
              </Tag>,
            ])}
            empty={T("কোনো মেকআপ ক্লাস নেই", "No makeup classes")}
          />
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════ হিসাব-নিকাশ (ফিচার ৯) ═══════════════ */
function AccountsView({ db }) {
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে
  const [genDuesBusy, setGenDuesBusy] = useState(false);
  const [fees, setFees] = useState(db.feePayments || []);
  const [salaries, setSalaries] = useState(db.teacherPayments || []);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [duesMap, setDuesMap] = useState(db.dueMonths || {});

  const loadData = async () => {
    try {
      const [feesData, salData, usersData, duesData] = await Promise.all([
        api.myFees(),
        api.salaries(),
        api.allUsers(),
        api.myDues(),
      ]);
      setFees(feesData.map((p) => ({ ...p, amount: +p.amount })));
      setSalaries(
        salData.map((p) => ({
          ...p,
          teacherId: p.teacher || p.teacherId,
          amount: +p.amount,
          month: p.month_label || p.month,
          teacher_name: p.teacher_name,
        })),
      );
      setTeachers(
        usersData
          .filter((u) => u.role === "teacher")
          .map((u) => ({
            id: u.id,
            name: u.name || u.name_bn,
            salary: u.monthly_salary || u.salary || 0,
            phone: u.phone,
            email: u.email,
            role: "teacher",
          })),
      );
      setStudents(
        usersData
          .filter((u) => u.role === "student")
          .map((u) => ({
            id: u.id,
            name: u.name || u.name_bn,
            fee: u.monthly_fee || 0,
          })),
      );
      const dm = {};
      duesData.forEach((d) => {
        const k = String(d.user || d.userId);
        if (!dm[k]) dm[k] = [];
        dm[k].push(d.month_label || d.month);
      });
      setDuesMap(dm);
    } catch {
      /* keep mock */
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const genDuesNow = async () => {
    setGenDuesBusy(true);
    try {
      const r = await api.generateMonthlyDues();
      notice(`✔ চলতি মাসের বকেয়া তৈরি হয়েছে — ${bn(r.created)}টি নতুন যোগ হলো`);
      await loadData();
    } catch (e) {
      notice("বকেয়া তৈরি ব্যর্থ — " + (e?.message || "যাচাই করুন"));
    }
    setGenDuesBusy(false);
  };
  const income = fees.reduce((s, p) => s + (+p.amount || 0), 0);
  const expense = salaries.reduce((s, p) => s + (+p.amount || 0), 0);
  // কোনো মাসে ইতিমধ্যে আংশিক পেমেন্ট হয়ে থাকলে কত জমা পড়েছে তা হিসাব — যতক্ষণ
  // না সব মিলিয়ে পূর্ণ বেতনের সমান হয়, ততক্ষণ ব্যাকএন্ডে বকেয়া থেকেই যায়
  // কোনো মাসে ইতিমধ্যে আংশিক পেমেন্ট হয়ে থাকলে কত জমা পড়েছে তা হিসাব — শুধু
  // ভিউয়ের জন্য (স্ট্যাটাস দেখানো); এখান থেকে আর পেমেন্ট এডিট/তৈরি করা যায় না —
  // পেমেন্ট দেওয়া ও রিসিট বানানো এখন "টিচার রিপোর্ট ও পেমেন্ট" পেজে
  const paidSoFar = (teacherId, month) =>
    salaries
      .filter(
        (p) =>
          String(p.teacherId) === String(teacherId) && (p.month || p.month_label) === month,
      )
      .reduce((s, p) => s + (+p.amount || 0), 0);
  // এই উস্তাদকে কখনো কোনো বেতন দেওয়া হয়েছে কিনা (যেকোনো মাসে)
  const everPaid = (teacherId) =>
    salaries.some(
      (p) => String(p.teacherId) === String(teacherId) && (+p.amount || 0) > 0,
    );

  return (
    <Section
      title="হিসাব-নিকাশ"
      sub="আয় (স্টুডেন্ট ফি) · ব্যয় (উস্তাদদের বেতন) · বকেয়া — শুধু তথ্য দেখার জন্য"
      action={
        <Btn
          kind="soft"
          onClick={genDuesNow}
          style={{ opacity: genDuesBusy ? 0.6 : 1 }}
        >
          {genDuesBusy ? "⏳ তৈরি হচ্ছে…" : "🔄 এই মাসের বকেয়া তৈরি করুন"}
        </Btn>
      }
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 10,
          marginBottom: 16,
        }}
      >
        <Stat
          icon="📥"
          label="মোট আয় (ফি)"
          value={`৳${bn(income.toLocaleString("en"))}`}
        />
        <Stat
          icon="📤"
          label="মোট ব্যয় (বেতন)"
          value={`৳${bn(expense.toLocaleString("en"))}`}
          accent={C.red}
        />
        <Stat
          icon="🏦"
          label="ব্যালেন্স"
          value={`৳${bn((income - expense).toLocaleString("en"))}`}
          accent={C.gold}
        />
      </div>
      {loading && <Loader text="হিসাব লোড হচ্ছে" />}
      <div style={{ ...S.card, marginBottom: 14, display: loading ? "none" : undefined }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          👳 উস্তাদদের বেতন
        </div>
        <Table
          head={["নাম", "মাসিক বেতন", "বকেয়া মাস"]}
          rows={teachers.map((t) => {
            const dues = duesMap[String(t.id)] || db.dueMonths?.[t.id] || [];
            const month = dues[0];
            const salary = t.salary || t.monthly_salary || 0;
            const paid = month ? paidSoFar(t.id, month) : 0;
            const remaining = Math.max(0, salary - paid);
            return [
              t.name,
              `৳${bn(salary.toLocaleString("en"))}`,
              /* ⚠️ আগে বকেয়ার রেকর্ড না থাকলেই "পরিশোধিত ✔" দেখাত। কিন্তু
                 বকেয়া তৈরি হয় মাসিক cron চললে — নতুন উস্তাদের ক্ষেত্রে বা
                 cron না চললে কোনো বকেয়াই থাকে না, ফলে এক টাকা বেতন না
                 দিয়েও "পরিশোধিত" দেখাত। এখন আসল বেতনের রেকর্ড দেখে বলা হয়। */
              dues.length ? (
                <Tag key="d" color={C.red} bg={C.redBg}>
                  {month}
                  {paid > 0
                    ? ` — ৳${bn(paid.toLocaleString("en"))} পেয়েছেন, ৳${bn(remaining.toLocaleString("en"))} বাকি`
                    : ""}
                </Tag>
              ) : everPaid(t.id) ? (
                <Tag key="d">পরিশোধিত ✔</Tag>
              ) : (
                <Tag key="d" color={C.red} bg={C.redBg}>
                  এখনো কোনো বেতন দেওয়া হয়নি
                </Tag>
              ),
            ];
          })}
        />
      </div>
      <div style={{ ...S.card, marginBottom: 14 }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          📤 বেতন পরিশোধের ইতিহাস
        </div>
        <Table
          head={["উস্তাদ", "মাস", "পরিমাণ", "তারিখ", "মাধ্যম", "স্ট্যাটাস"]}
          rows={salaries.map((p) => {
            const tId = p.teacherId || p.teacher;
            const tRec = teachers.find((t) => String(t.id) === String(tId));
            const tName = p.teacher_name || tRec?.name || userById(tId)?.name || "—";
            const monthLbl = p.month || p.month_label;
            const salary = tRec?.salary || 0;
            const totalPaid = paidSoFar(tId, monthLbl);
            const remaining = Math.max(0, salary - totalPaid);
            return [
              tName,
              monthLbl,
              `৳${bn((+p.amount || 0).toLocaleString("en"))}`,
              fmtDate(p.paid_at || p.date),
              p.method,
              remaining > 0 ? (
                <Tag key="s" color={C.gold} bg={C.amberBg}>
                  ⚠️ আংশিক — ৳{bn(remaining.toLocaleString("en"))} বাকি
                </Tag>
              ) : (
                <Tag key="s">✅ ভেরিফাইড</Tag>
              ),
            ];
          })}
          empty="কোনো পেমেন্ট ইতিহাস নেই"
          loading={loading}
        />
      </div>
      <div style={{ ...S.card, display: loading ? "none" : undefined }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          📥 স্টুডেন্ট ফি বকেয়া
        </div>
        <Table
          head={["স্টুডেন্ট", "মাসিক ফি", "বকেয়া মাস", "বকেয়া টাকা"]}
          rows={students
            .filter((s) => (duesMap[String(s.id)] || []).length > 0)
            .map((s) => {
              const months = duesMap[String(s.id)] || [];
              return [
                s.name,
                `৳${bn((s.fee || 0).toLocaleString("en"))}`,
                months.join(", "),
                <Tag key="t" color={C.red} bg={C.redBg}>
                  ৳{bn((months.length * (s.fee || 0)).toLocaleString("en"))}
                </Tag>,
              ];
            })}
          empty="কোনো বকেয়া নেই ✔"
          loading={loading}
        />
      </div>
    </Section>
  );
}

/* ═══════════════ ওয়েবসাইট ফর্ম সাবমিশন (ফিচার ৮) ═══════════════ */
function FormsView({ db, setDb }) {
  const [forms, setForms] = useState(db.forms || []);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    api
      .admissions()
      .then((data) => {
        const contactForms = data.filter(
          (a) => a.kind === "trial" || a.kind === "contact",
        );
        if (contactForms.length > 0)
          setForms(
            contactForms.map((a) => ({
              id: a.id,
              type: a.kind === "trial" ? "ফ্রি ট্রায়াল" : "যোগাযোগ",
              name: a.name,
              contact: a.contact || a.email,
              msg: a.message || a.msg,
              date: a.applied_at || a.date,
              status: a.replied ? "replied" : "new",
            })),
          );
      })
      .catch(() => {
        /* keep mock */
      });
  }, []);

  // "নতুন" থেকে "রিপ্লাই হয়েছে"-তে আনলে backend-এ প্রস্তুত WhatsApp বার্তা আসলেই
  // পাঠানো হয় (আগে শুধু চিহ্নিত হতো, কোনো মেসেজ পাঠানো হতো না) — উল্টো দিকে
  // (ভুলে চিহ্নিত হলে ফেরত) কোনো মেসেজ পাঠানোর দরকার নেই, শুধু ফ্ল্যাগ বদলায়
  const toggle = async (id) => {
    const f = forms.find((x) => x.id === id);
    if (f?.status === "new") {
      setBusyId(id);
      try {
        await api.sendAdmissionReply(id);
        notice("✔ WhatsApp রিপ্লাই পাঠানো হয়েছে।");
        setForms((prev) =>
          prev.map((x) => (x.id === id ? { ...x, status: "replied" } : x)),
        );
      } catch (e) {
        notice(
          "রিপ্লাই পাঠাতে ব্যর্থ — " +
            (e?.data?.error || e?.message || "যাচাই করুন"),
        );
      }
      setBusyId(null);
    } else {
      try {
        await api.replyAdmission(id, false);
      } catch {
        /* ignore */
      }
      setForms((prev) =>
        prev.map((x) => (x.id === id ? { ...x, status: "new" } : x)),
      );
    }
  };
  return (
    <Section
      title="ওয়েবসাইট ফর্ম সাবমিশন"
      sub="tarbiyatulquran.org-এর যোগাযোগ ও ফ্রি ট্রায়াল ফর্ম থেকে আসা তথ্য"
    >
      <div style={{ display: "grid", gap: 10 }}>
        {forms.map((f) => (
          <div
            key={f.id}
            style={{
              ...S.card,
              padding: 16,
              display: "flex",
              gap: 12,
              flexWrap: "wrap",
              alignItems: "flex-start",
              borderLeft: `4px solid ${f.status === "new" ? C.gold : C.line}`,
            }}
          >
            <div style={{ flex: 1, minWidth: 220 }}>
              <div style={{ fontWeight: 800 }}>
                {f.name}{" "}
                <Tag color={C.blue} bg={C.blueBg}>
                  {f.type}
                </Tag>{" "}
                {f.status === "new" && (
                  <Tag color={C.gold} bg={C.amberBg}>
                    নতুন
                  </Tag>
                )}
              </div>
              <div style={{ fontSize: 12.5, color: C.muted, margin: "3px 0" }}>
                📞 {f.contact} · {fmtDate(f.date)}
              </div>
              <div style={{ fontSize: 13.5 }}>{f.msg}</div>
            </div>
            <Btn
              sm
              kind={f.status === "new" ? "primary" : "soft"}
              onClick={() => toggle(f.id)}
              style={{ opacity: busyId === f.id ? 0.6 : 1 }}
            >
              {busyId === f.id
                ? "⏳ পাঠানো হচ্ছে…"
                : f.status === "new"
                  ? "📲 WhatsApp রিপ্লাই পাঠান"
                  : "✔ রিপ্লাই হয়েছে"}
            </Btn>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ═══════════════ বই লাইব্রেরি (ফিচার ১০) ═══════════════ */
function BooksView({ db, user }) {
  const [show, setShow] = useState(false);
  const [f, setF] = useState({
    cls: "",
    title: "",
    author: "",
    link: "",
    file_type: "PDF",
  });
  const [books, setBooks] = useState(db.books || []);
  useEffect(() => {
    api
      .libraryBooks()
      .then((data) =>
        setBooks(
          data.map((b) => ({
            id: b.id,
            cls: b.cls,
            title: b.title,
            author: b.author,
            link: b.link || "#",
            type: b.file_type || "PDF",
          })),
        ),
      )
      .catch(() => {});
  }, []);
  const groups = [...new Set(books.map((b) => b.cls))];
  const add = async () => {
    try {
      const res = await api.addLibraryBook({
        cls: f.cls,
        title: f.title,
        author: f.author,
        link: f.link || "#",
        file_type: f.file_type,
      });
      setBooks((prev) => [
        ...prev,
        {
          id: res.id,
          cls: res.cls,
          title: res.title,
          author: res.author,
          link: res.link || "#",
          type: res.file_type || "PDF",
        },
      ]);
      notice("✔ বই যোগ করা হয়েছে।");
    } catch (e) {
      notice(
        "বই যোগ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
      return;
    }
    setShow(false);
    setF({ cls: "", title: "", author: "", link: "", file_type: "PDF" });
  };
  const del = async (b) => {
    try {
      await api.deleteLibraryBook(b.id);
      setBooks((prev) => prev.filter((x) => x.id !== b.id));
      notice("✔ বই মুছে ফেলা হয়েছে।");
    } catch (e) {
      notice(
        "বই মুছতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  return (
    <Section
      title="বই লাইব্রেরি"
      sub="সকল শ্রেণির পাঠ্যবই ও সহায়ক বই — ডাউনলোডযোগ্য"
      action={
        isAdm(user) && <Btn onClick={() => setShow(true)}>+ বই যোগ করুন</Btn>
      }
    >
      {groups.map((g) => (
        <div key={g} style={{ marginBottom: 16 }}>
          <div
            style={{
              fontWeight: 800,
              fontSize: 14.5,
              marginBottom: 8,
              color: C.emerald,
            }}
          >
            📗 {g}
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
              gap: 10,
            }}
          >
            {books
              .filter((b) => b.cls === g)
              .map((b) => (
                <div key={b.id} style={{ ...S.card, padding: 14 }}>
                  <div style={{ fontWeight: 700, fontSize: 13.5 }}>
                    {b.title}
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: C.muted,
                      margin: "3px 0 8px",
                    }}
                  >
                    {b.author}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <Tag color={C.blue} bg={C.blueBg}>
                      {b.type}
                    </Tag>
                    <span
                      style={{ display: "flex", gap: 8, alignItems: "center" }}
                    >
                      <a
                        href={b.link}
                        style={{
                          fontSize: 12.5,
                          fontWeight: 700,
                          color: C.emerald,
                          textDecoration: "none",
                        }}
                      >
                        ⬇ ডাউনলোড
                      </a>
                      {isDir(user) && (
                        <Btn sm kind="danger" onClick={() => del(b)}>
                          ✕
                        </Btn>
                      )}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}
      {show && (
        <Modal title="নতুন বই যোগ করুন" onClose={() => setShow(false)}>
          <label style={S.label}>শ্রেণি / কোর্স</label>
          <input
            style={S.input}
            value={f.cls}
            onChange={(e) => setF({ ...f, cls: e.target.value })}
            placeholder="যেমন: তাজবীদ"
          />
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>বইয়ের নাম</label>
            <input
              style={S.input}
              value={f.title}
              onChange={(e) => setF({ ...f, title: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>লেখক</label>
            <input
              style={S.input}
              value={f.author}
              onChange={(e) => setF({ ...f, author: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>ডাউনলোড লিংক</label>
            <input
              style={S.input}
              value={f.link}
              onChange={(e) => setF({ ...f, link: e.target.value })}
              placeholder="https://..."
            />
          </div>
          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
            onClick={add}
          >
            যোগ করুন
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ নোটিশ বোর্ড (অতিরিক্ত প্রফেশনাল ফিচার) ═══════════════ */
function NoticesView({ db, setDb, user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [show, setShow] = usePersistedState("notice_show", false);
  const [f, setF] = usePersistedState("notice_f", { title: "", body: "" });
  const [notices, setNotices] = useState(db.notices || []);
  const [busy, setBusy] = useState(false);

  // আগে এখানে শুধু stale mock db.notices দেখানো হতো আর প্রকাশ/মুছার বাটন
  // শুধু লোকাল স্টেটে বদলাত (সার্ভারে কিছুই সেভ হতো না, রিফ্রেশে হারিয়ে যেত,
  // অন্য কেউ কখনো দেখতে পেত না) — এখন সরাসরি /notices/ থেকে লোড হয়
  const loadNotices = async () => {
    try {
      const data = await api.notices();
      setNotices(data.map((n) => ({ id: n.id, title: n.title, body: n.body, date: n.created_at })));
    } catch {
      /* keep mock */
    }
  };
  useEffect(() => {
    loadNotices();
  }, []);

  const publish = async () => {
    if (!f.title.trim() || !f.body.trim()) return notice("শিরোনাম ও বিস্তারিত দিন।");
    setBusy(true);
    try {
      await api.createNotice({ title: f.title.trim(), body: f.body.trim() });
      await loadNotices();
      setShow(false);
      setF({ title: "", body: "" });
      notice("✔ নোটিশ প্রকাশ হয়েছে।");
    } catch (e) {
      notice(
        "নোটিশ প্রকাশ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
    setBusy(false);
  };
  const remove = async (id) => {
    try {
      await api.deleteNotice(id);
      await loadNotices();
      notice("✔ নোটিশ মুছে ফেলা হয়েছে।");
    } catch (e) {
      notice(
        "নোটিশ মুছতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };

  return (
    <Section
      title={T("নোটিশ বোর্ড", "Notice Board")}
      action={
        isAdm(user) && <Btn onClick={() => setShow(true)}>+ নোটিশ দিন</Btn>
      }
    >
      <div style={{ display: "grid", gap: 10 }}>
        {notices.map((n) => (
          <div
            key={n.id}
            style={{
              ...S.card,
              padding: 16,
              borderLeft: `4px solid ${C.gold}`,
            }}
          >
            <div
              style={{
                fontWeight: 800,
                display: "flex",
                justifyContent: "space-between",
                gap: 8,
              }}
            >
              <span>📌 {n.title}</span>
              {isDir(user) && (
                <Btn sm kind="danger" onClick={() => remove(n.id)}>
                  মুছুন
                </Btn>
              )}
            </div>
            <div style={{ fontSize: 12, color: C.muted, margin: "2px 0 6px" }}>
              {fmtDate(n.date)}
            </div>
            <div style={{ fontSize: 13.5 }}>{n.body}</div>
          </div>
        ))}
      </div>
      {show && (
        <Modal title="নতুন নোটিশ" onClose={() => setShow(false)}>
          <label style={S.label}>শিরোনাম</label>
          <input
            style={S.input}
            value={f.title}
            onChange={(e) => setF({ ...f, title: e.target.value })}
          />
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>বিস্তারিত</label>
            <textarea
              rows={4}
              style={{ ...S.input, resize: "vertical" }}
              value={f.body}
              onChange={(e) => setF({ ...f, body: e.target.value })}
            />
          </div>
          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center", opacity: busy ? 0.6 : 1 }}
            onClick={publish}
          >
            {busy ? "⏳ প্রকাশ হচ্ছে…" : "প্রকাশ করুন"}
          </Btn>
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
  const labels = [
    "",
    "Needs improvement",
    "Okay",
    "Good",
    "Very good",
    "Excellent",
  ];
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(18,63,40,.5)",
        zIndex: 95,
        display: "grid",
        placeItems: "center",
        padding: 16,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 20,
          width: "100%",
          maxWidth: 400,
          padding: 26,
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 38 }}>🌟</div>
        <h3
          style={{
            margin: "6px 0 2px",
            fontSize: 17,
            fontWeight: 800,
            color: C.text,
          }}
        >
          How was today's class?
        </h3>
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 14 }}>
          {courseName} — your feedback helps improve the academy's quality
          (optional)
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 6,
            marginBottom: 4,
          }}
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onClick={() => setStars(n)}
              onMouseEnter={() => setHover(n)}
              onMouseLeave={() => setHover(0)}
              style={{
                border: "none",
                background: "transparent",
                cursor: "pointer",
                fontSize: 32,
                lineHeight: 1,
                filter:
                  (hover || stars) >= n ? "none" : "grayscale(1) opacity(.35)",
                transform: (hover || stars) >= n ? "scale(1.08)" : "none",
                transition: "all .12s",
              }}
            >
              ⭐
            </button>
          ))}
        </div>
        <div
          style={{ height: 18, fontSize: 12.5, fontWeight: 700, color: C.gold }}
        >
          {labels[hover || stars]}
        </div>
        <textarea
          rows={2}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Write a comment if you'd like (optional)..."
          style={{ ...S.input, resize: "vertical", marginTop: 8, fontSize: 13 }}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
          <Btn
            kind="soft"
            style={{ flex: 1, justifyContent: "center" }}
            onClick={onSkip}
          >
            Skip
          </Btn>
          <Btn
            kind="gold"
            style={{
              flex: 1.4,
              justifyContent: "center",
              opacity: stars ? 1 : 0.5,
            }}
            onClick={() => stars && onSubmit(stars, comment.trim())}
          >
            Submit Rating
          </Btn>
        </div>
        <div style={{ fontSize: 11, color: C.muted, marginTop: 10 }}>
          Only the admin can see your name and comment — teachers only see the
          average rating.
        </div>
      </div>
    </div>
  );
}

/* ═══════════════ টিচার রিপোর্ট — উপস্থিতি · ক্লাসের মান · পেমেন্ট ═══════════════ */
function TeacherReportView({ db, setDb, courses, user }) {
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে
  const [allTeachers, setAllTeachers] = useState([]);
  const [sel, setSel] = useState(
    user.role === "teacher" ? user.id : allTeachers[0]?.id,
  );
  const [ratingSummary, setRatingSummary] = useState(null);
  const [allRatings, setAllRatings] = useState(db.ratings || []);
  const [salaries, setSalaries] = useState(db.teacherPayments || []);
  // আগে এখানে stale mock db.attendance/db.classes/db.dueMonths ব্যবহার হতো —
  // তাই হাজিরা, ক্লাস নেওয়ার সংখ্যা ও বকেয়া কখনো আসল ডাটা দেখাত না
  const [attendance, setAttendance] = useState([]);
  const [classes, setClasses] = useState([]);

  const tid = user.role === "teacher" ? user.id : sel || allTeachers[0]?.id;
  const t =
    allTeachers.find((x) => String(x.id) === String(tid)) || userById(tid);
  const tCourses = courses.filter(
    (c) => String(c.teacherId || c.teacher) === String(tid),
  );
  const att = attendance.filter((a) => String(a.user) === String(tid));
  const present = att.filter((a) => (a.present ?? a.minutes >= 45)).length;
  const short = att.filter((a) => !(a.present ?? a.minutes >= 45)).length;
  const taken = classes.filter(
    (k) =>
      tCourses.some((c) => String(c.id) === String(k.course || k.courseId)) &&
      (k.status === "done" || k.date < todayISO()),
  ).length;

  const avg = ratingSummary ? ratingSummary.avg || 0 : 0;
  const ratingCount = ratingSummary
    ? ratingSummary.count
    : allRatings.filter((r) => String(r.teacher || r.teacherId) === String(tid))
        .length;
  const quality = !ratingCount
    ? ["—", C.muted, C.cream]
    : avg >= 4.5
      ? ["অসাধারণ", C.green, C.greenBg]
      : avg >= 4
        ? ["খুব ভালো", C.emerald, C.greenBg]
        : avg >= 3
          ? ["ভালো", C.gold, C.amberBg]
          : ["উন্নতি প্রয়োজন", C.red, C.redBg];
  const dist = ratingSummary
    ? [5, 4, 3, 2, 1].map((n) => ({
        n,
        c: ratingSummary.distribution?.[n] || 0,
      }))
    : [5, 4, 3, 2, 1].map((n) => ({
        n,
        c: allRatings.filter(
          (r) =>
            String(r.teacher || r.teacherId) === String(tid) && r.stars === n,
        ).length,
      }));
  const pays = salaries.filter(
    (p) => String(p.teacher || p.teacherId) === String(tid),
  );
  const dues = t?.due_months || [];

  // কোনো মাসে ইতিমধ্যে আংশিক পেমেন্ট হয়ে থাকলে কত জমা পড়েছে তা হিসাব — যতক্ষণ
  // না সব মিলিয়ে পূর্ণ বেতনের সমান হয়, ততক্ষণ ব্যাকএন্ডে বকেয়া থেকেই যায়
  const paidSoFar = (teacherId, month) =>
    salaries
      .filter(
        (p) =>
          String(p.teacher || p.teacherId) === String(teacherId) &&
          (p.month_label || p.month) === month,
      )
      .reduce((s, p) => s + (+p.amount || 0), 0);
  const [maker, setMaker] = useState(false);
  const [payModal, setPayModal] = useState(false);
  const [pm, setPm] = useState({ teacherId: "", month: "", amount: "" });
  const [pmBusy, setPmBusy] = useState(false);
  const payTeacher = async (teacher, month, amount) => {
    if (!month) return;
    if (!amount || amount <= 0) return notice("সঠিক পরিমাণ দিন।");
    // পেমেন্ট সেভ ও রিসিট পাঠানো — আলাদা try/catch, নইলে পেমেন্ট আসলে সফল
    // হয়ে গেলেও শুধু রিসিট পাঠাতে ব্যর্থ হলে সেটাকে "পেমেন্ট ব্যর্থ" দেখানো
    // হতো, ফলে পরিচালক আবার পেমেন্ট দিলে ডুপ্লিকেট বেতন সেভ হয়ে যেতে পারত
    try {
      await api.payTeacherSalary({
        teacher: teacher.id,
        amount,
        month_label: month,
        method: "ব্যাংক",
      });
    } catch (e) {
      notice("পেমেন্ট সেভ করতে ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
      return;
    }
    await loadSalaries();
    try {
      await api.sendReceipt({
        to_user: teacher.id,
        kind: "বেতন পরিশোধ ভাউচার",
        month_label: month,
        amount,
        method: "ব্যাংক",
      });
      notice("✔ বেতন পেমেন্ট সেভ হয়েছে ও ভাউচার পাঠানো হয়েছে।");
    } catch (e) {
      notice(
        "✔ বেতন পেমেন্ট সেভ হয়েছে — কিন্তু ভাউচার পাঠাতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "যাচাই করুন") +
          " (আবার পেমেন্ট দেবেন না, শুধু ভাউচারটা পরে আবার পাঠান)",
      );
    }
  };
  const pmTeacher = allTeachers.find((x) => String(x.id) === String(pm.teacherId));
  const pmSalary = pmTeacher?.monthly_salary || pmTeacher?.salary || 0;
  const pmMonthLabel = pm.month ? monthLabelBn(pm.month) : "";
  const pmRemaining = pmTeacher
    ? Math.max(0, pmSalary - (pmMonthLabel ? paidSoFar(pmTeacher.id, pmMonthLabel) : 0))
    : 0;
  const submitPayModal = async () => {
    if (!pmTeacher) return notice("উস্তাদ বেছে নিন।");
    if (!pm.month) return notice("মাস ও সাল বেছে নিন।");
    const amount = pm.amount ? +pm.amount : pmRemaining;
    if (!amount || amount <= 0) return notice("সঠিক পরিমাণ দিন।");
    setPmBusy(true);
    await payTeacher(pmTeacher, pmMonthLabel, amount);
    setPmBusy(false);
    setPayModal(false);
    setPm({ teacherId: "", month: "", amount: "" });
  };

  const loadTeachers = async () => {
    try {
      const data = await api.allUsers();
      const ts = data.filter((u) => u.role === "teacher");
      setAllTeachers(
        ts.length ? ts : USERS.filter((u) => u.role === "teacher"),
      );
    } catch {
      /* keep mock */
    }
  };
  const loadRatings = async () => {
    try {
      const [summary, rData] = await Promise.all([
        api.teacherRatingSummary(tid),
        api.ratings(),
      ]);
      setRatingSummary(summary);
      setAllRatings(rData);
    } catch {
      setRatingSummary(null);
    }
  };
  const loadSalaries = async () => {
    try {
      setSalaries(await api.salaries());
    } catch {
      setSalaries(db.teacherPayments || []);
    }
  };
  const loadAttendance = async () => {
    try {
      setAttendance(await api.attendanceReport());
    } catch {
      /* keep empty */
    }
  };
  const loadClasses = async () => {
    try {
      setClasses(await api.classes());
    } catch {
      /* keep empty */
    }
  };
  useEffect(() => {
    // সব লোড শেষ হওয়ার আগে "কোনো রেকর্ড নেই" না দেখাতে
    Promise.all([
      loadTeachers(),
      loadSalaries(),
      loadAttendance(),
      loadClasses(),
    ]).finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    loadRatings();
  }, [tid]);
  return (
    <Section
      title="টিচার রিপোর্ট ও পেমেন্ট"
      sub="উপস্থিতি · ক্লাসের মান (স্টুডেন্ট মূল্যায়ন) · বেতন — চিহ্নিত করে দেখানো হয়েছে"
      action={
        isAdm(user) && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Btn kind="soft" onClick={() => setMaker(true)}>
              🧾 রিসিট বানান
            </Btn>
            <Btn
              kind="gold"
              onClick={() => {
                setPm((prev) => ({ ...prev, teacherId: String(tid) }));
                setPayModal(true);
              }}
            >
              💵 পেমেন্ট সম্পন্ন করুন
            </Btn>
          </div>
        )
      }
    >
      {loading && <Loader text="রিপোর্ট লোড হচ্ছে" />}
      {maker && <ReceiptMaker user={user} onClose={() => setMaker(false)} />}
      {payModal && (
        <Modal
          title="উস্তাদের পেমেন্ট সম্পন্ন করুন"
          onClose={() => setPayModal(false)}
        >
          <div>
            <label style={S.label}>উস্তাদ</label>
            <select
              style={S.input}
              value={pm.teacherId}
              onChange={(e) => setPm({ ...pm, teacherId: e.target.value })}
            >
              <option value="">বেছে নিন</option>
              {allTeachers.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.name}
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>মাসিক বেতন</label>
            <div
              style={{
                ...S.input,
                background: C.cream,
                fontWeight: 800,
                display: "flex",
                alignItems: "center",
              }}
            >
              ৳{bn(pmSalary.toLocaleString("en"))}
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>কোন মাসের পেমেন্ট</label>
            <input
              type="month"
              style={S.input}
              value={pm.month}
              onChange={(e) => setPm({ ...pm, month: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>কত পরিশোধ করছেন (ফাঁকা রাখলে ফুল পেমেন্ট ধরা হবে)</label>
            <input
              type="number"
              style={S.input}
              value={pm.amount}
              onChange={(e) => setPm({ ...pm, amount: e.target.value })}
              placeholder={pmTeacher && pm.month ? `${pmRemaining}` : ""}
            />
          </div>
          <Btn
            style={{ marginTop: 14, width: "100%", justifyContent: "center" }}
            kind="gold"
            onClick={submitPayModal}
          >
            {pmBusy ? "⏳ সেভ হচ্ছে…" : "✔ পেমেন্ট দিন"}
          </Btn>
        </Modal>
      )}
      {isAdm(user) && (
        <div
          style={{
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
            marginBottom: 14,
          }}
        >
          {allTeachers.map((x) => (
            <Btn
              key={x.id}
              sm
              kind={tid === x.id ? "primary" : "soft"}
              onClick={() => setSel(x.id)}
            >
              {x.name}
            </Btn>
          ))}
        </div>
      )}
      <div
        style={{
          ...S.card,
          display: "flex",
          gap: 14,
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: 14,
          borderLeft: `4px solid ${quality[1]}`,
        }}
      >
        <div
          style={{
            width: 52,
            height: 52,
            borderRadius: 14,
            background: C.greenBg,
            display: "grid",
            placeItems: "center",
            fontSize: 26,
          }}
        >
          👳
        </div>
        <div style={{ flex: 1, minWidth: 180 }}>
          <div style={{ fontWeight: 800, fontSize: 16 }}>{t.name}</div>
          <div style={S.sub}>
            {t.sub} · কোর্স: {tCourses.map((c) => c.name).join(", ") || "—"}
          </div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 24, fontWeight: 900, color: quality[1] }}>
            {ratingCount ? "★ " + bn(avg.toFixed(1)) : "★ —"}
          </div>
          <Tag color={quality[1]} bg={quality[2]}>
            ক্লাসের মান: {quality[0]}
          </Tag>
        </div>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: 10,
          marginBottom: 14,
        }}
      >
        <Stat icon="🎥" label="ক্লাস নিয়েছেন" value={bn(taken)} />
        <Stat
          icon="✅"
          label="পূর্ণ উপস্থিতি"
          value={bn(present)}
          note="৪০+ মিনিট"
        />
        <Stat
          icon="⚠️"
          label="অসম্পূর্ণ উপস্থিতি"
          value={bn(short)}
          accent={C.red}
          note="৪৫ মিনিটের কম"
        />
        <Stat
          icon="🌟"
          label="মোট মূল্যায়ন"
          value={bn(ratingCount)}
          accent={C.gold}
        />
      </div>
      <div style={{ display: "grid", gap: 14 }}>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>
            🌟 ক্লাসের মান — স্টুডেন্ট মূল্যায়ন
          </div>
          {dist.map(({ n, c }) => (
            <div
              key={n}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 6,
                fontSize: 12.5,
              }}
            >
              <span style={{ width: 34, fontWeight: 700 }}>{bn(n)} ★</span>
              <div
                style={{
                  flex: 1,
                  height: 9,
                  background: C.cream,
                  borderRadius: 99,
                }}
              >
                <div
                  style={{
                    width: ratingCount ? (c / ratingCount) * 100 + "%" : 0,
                    height: "100%",
                    background: C.gold,
                    borderRadius: 99,
                  }}
                />
              </div>
              <span style={{ width: 26, textAlign: "right", color: C.muted }}>
                {bn(c)}
              </span>
            </div>
          ))}
          {isAdm(user) ? (
            <div style={{ marginTop: 12 }}>
              <div
                style={{
                  fontSize: 12.5,
                  fontWeight: 700,
                  color: C.muted,
                  marginBottom: 6,
                }}
              >
                কে কী মূল্যায়ন করেছে (কেবল এডমিন/পরিচালক দেখছেন):
              </div>
              <Table
                head={["স্টুডেন্ট", "কোর্স", "রেটিং", "মন্তব্য", "তারিখ"]}
                rows={allRatings
                  .filter(
                    (r) => String(r.teacher || r.teacherId) === String(tid),
                  )
                  .map((r) => [
                    r.student_name || userById(r.student || r.studentId).name,
                    courseById(courses, r.course || r.courseId).name,
                    "★".repeat(r.stars),
                    r.comment || "—",
                    fmtDate(r.rated_at || r.date),
                  ])}
                empty="এখনো কোনো মূল্যায়ন নেই"
                loading={loading}
              />
            </div>
          ) : (
            <div
              style={{
                marginTop: 10,
                padding: "10px 12px",
                borderRadius: 10,
                background: C.cream,
                fontSize: 12,
                color: C.muted,
              }}
            >
              🔒 কোন স্টুডেন্ট কী মূল্যায়ন বা মন্তব্য করেছে তা গোপন — কেবল
              এডমিন দেখতে পারেন। আপনি শুধু সামগ্রিক রিপোর্ট দেখছেন।
            </div>
          )}
        </div>
        <div style={{ ...S.card }}>
          <div style={{ fontWeight: 800, marginBottom: 10 }}>
            🗓️ আমার উপস্থিতি রেকর্ড
          </div>
          <Table
            head={[
              "কোর্স",
              "তারিখ",
              // কত মিনিট ক্লাস হয়েছে তা কেবল পরিচালকই দেখবেন
              ...(isDir(user) ? ["উপস্থিতি"] : []),
              "অবস্থা",
            ]}
            rows={att.map((a) => {
              return [
                a.course_name || "—",
                a.class_date ? fmtDate(a.class_date) : "—",
                ...(isDir(user) ? [`${bn(a.minutes)} মিনিট`] : []),
                (a.present ?? a.minutes >= 45) ? (
                  <Tag key="t">উপস্থিত ✔</Tag>
                ) : (
                  <Tag key="t" color={C.red} bg={C.redBg}>
                    অসম্পূর্ণ ✘
                  </Tag>
                ),
              ];
            })}
            empty="কোনো রেকর্ড নেই"
            loading={loading}
          />
        </div>
        <div style={{ ...S.card }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: 8,
              marginBottom: 10,
            }}
          >
            <div style={{ fontWeight: 800 }}>💰 আমার বেতন ও পেমেন্ট</div>
            <div style={{ fontSize: 13 }}>
              মাসিক বেতন:{" "}
              <b>
                ৳{bn((t.monthly_salary || t.salary || 0).toLocaleString("en"))}
              </b>{" "}
              · বকেয়া:{" "}
              {dues.length ? (
                <Tag color={C.red} bg={C.redBg}>
                  {dues.join(", ")}
                </Tag>
              ) : (
                <Tag>নেই ✔</Tag>
              )}
            </div>
          </div>
          <Table
            head={["মাস", "পরিমাণ", "তারিখ", "মাধ্যম", "স্ট্যাটাস"]}
            rows={pays.map((p) => {
              const monthLbl = p.month_label || p.month;
              const salary = t.monthly_salary || t.salary || 0;
              const totalPaid = pays
                .filter((x) => (x.month_label || x.month) === monthLbl)
                .reduce((s, x) => s + (+x.amount || 0), 0);
              const remaining = Math.max(0, salary - totalPaid);
              return [
                monthLbl,
                `৳${bn((p.amount || 0).toLocaleString("en"))}`,
                fmtDate(p.paid_at || p.date),
                p.method,
                remaining > 0 ? (
                  <Tag key="s" color={C.gold} bg={C.amberBg}>
                    ⚠️ আংশিক — ৳{bn(remaining.toLocaleString("en"))} বাকি
                  </Tag>
                ) : (
                  <Tag key="s">✅ ভেরিফাইড</Tag>
                ),
              ];
            })}
            empty="এখনো কোনো পেমেন্ট হয়নি"
            loading={loading}
          />
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════ ভর্তি আবেদন — এপ্রুভ করলে তবেই স্টুডেন্ট তালিকায় ═══════════════ */
function AdmissionsView({ db, setDb, user, refresh }) {
  const adaptAdmission = (a) => ({
    id: a.id,
    name: a.name,
    age: a.age,
    course: a.course_name || a.course,
    guardian: a.guardian,
    contact: a.contact,
    country: a.country,
    msg: a.message || a.msg,
    date: a.applied_at || a.date,
    status: a.status,
    forwarded: a.forwarded_to_director ?? a.forwarded,
    newLogin: a.created_student_username || a.newLogin,
    newPass: a.created_student_password || a.newPass,
  });
  const [admissions, setAdmissions] = useState(db.admissions || []);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে
  const [acceptingId, setAcceptingId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      setAdmissions((await api.admissions()).map(adaptAdmission));
    } catch {
      setAdmissions(db.admissions || []);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const accept = async (a) => {
    if (acceptingId) return; // ডাবল-ক্লিকে দুইবার রিকোয়েস্ট গিয়ে ডুপ্লিকেট স্টুডেন্ট তৈরি ঠেকাতে
    setAcceptingId(a.id);
    try {
      const res = await api.acceptAdmission(a.id, { fee: DEFAULT_FEE });
      await loadData();
      if (res.username)
        notice(
          `✔ ভর্তি সম্পন্ন — লগইন: ${res.username} · পাস: ${res.password}`,
        );
      if (refresh) refresh();
    } catch (e) {
      // আগে এখানে ব্যর্থ হলেও ভুয়া লগইন-পাসওয়ার্ড বানিয়ে "✔ সম্পন্ন" দেখানো হতো —
      // সার্ভারে আসলে কিছুই সেভ হতো না (আবেদন এখনো "পেন্ডিং"), তাই দেওয়া
      // আইডি-পাসওয়ার্ড দিয়ে কখনোই লগইন করা যেত না। এখন স্পষ্ট এরর দেখাচ্ছে,
      // কোনো ভুয়া অ্যাকাউন্ট তৈরি করছে না।
      notice(
        "ভর্তি গ্রহণ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন") +
          " (আবেদনটা এখনো 'পেন্ডিং'-ই আছে)",
      );
    } finally {
      setAcceptingId(null);
    }
  };
  const reject = async (a) => {
    try {
      await api.rejectAdmission(a.id);
      await loadData();
      notice("✔ আবেদনটি বাতিল করা হয়েছে।");
    } catch (e) {
      notice(
        "আবেদন বাতিল করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const forward = async (a) => {
    try {
      await api.forwardAdmission(a.id);
      await loadData();
      notice("✔ আবেদনটি পরিচালকের কাছে পাঠানো হয়েছে।");
    } catch (e) {
      notice(
        "আবেদন পাঠাতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const pending = admissions.filter((a) => a.status === "pending");
  const decided = admissions.filter((a) => a.status !== "pending");
  const Card = (a) => (
    <div
      key={a.id}
      style={{
        ...S.card,
        padding: 16,
        borderLeft: `4px solid ${a.status === "pending" ? C.gold : a.status === "accepted" ? C.green : C.red}`,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: 10,
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ fontWeight: 800 }}>
            {a.name}, {bn(a.age)} বছর{" "}
            <Tag color={C.blue} bg={C.blueBg}>
              {a.course}
            </Tag>
          </div>
          <div style={{ fontSize: 12.5, color: C.muted, margin: "3px 0" }}>
            অভিভাবক: {a.guardian} · {a.country} · 📞 {a.contact} ·{" "}
            {fmtDate(a.date)}
          </div>
          <div style={{ fontSize: 13 }}>{a.msg}</div>
          {a.status === "accepted" && (
            <div style={{ fontSize: 12, color: C.green, marginTop: 4 }}>
              ✔ গৃহীত — লগইন আইডি: <b>{a.newLogin}</b> · পাসওয়ার্ড:{" "}
              <b>{a.newPass}</b> (পরিচালক/এডমিন অভিভাবককে জানিয়ে দেবেন)
            </div>
          )}
        </div>
        {a.status === "pending" ? (
          isDir(user) ? (
            <div
              style={{
                display: "flex",
                gap: 6,
                alignItems: "flex-end",
                flexDirection: "column",
              }}
            >
              {a.forwarded && (
                <Tag color={C.blue} bg={C.blueBg}>
                  📤 এডমিন পাঠিয়েছেন
                </Tag>
              )}
              <div style={{ display: "flex", gap: 6 }}>
                <Btn
                  sm
                  disabled={acceptingId === a.id}
                  onClick={() => accept(a)}
                >
                  {acceptingId === a.id ? "..." : "✔ গ্রহণ করুন"}
                </Btn>
                <Btn sm kind="danger" onClick={() => reject(a)}>
                  ✘ বাতিল
                </Btn>
              </div>
            </div>
          ) : a.forwarded ? (
            <Tag color={C.blue} bg={C.blueBg}>
              পরিচালকের কাছে পাঠানো হয়েছে ✔
            </Tag>
          ) : (
            <Btn sm kind="gold" onClick={() => forward(a)}>
              📤 পরিচালক বরাবর পাঠান
            </Btn>
          )
        ) : a.status === "accepted" ? (
          <Tag>গৃহীত ✔</Tag>
        ) : (
          <Tag color={C.red} bg={C.redBg}>
            বাতিল ✘
          </Tag>
        )}
      </div>
    </div>
  );
  return (
    <Section
      title="ভর্তি আবেদন"
      sub="গ্রহণ/বাতিলের ক্ষমতা কেবল পরিচালকের — এডমিন বিস্তারিত দেখে পরিচালক বরাবর পাঠাবেন"
    >
      <div
        style={{
          fontWeight: 800,
          fontSize: 14,
          marginBottom: 8,
          color: C.gold,
        }}
      >
        ⏳ অপেক্ষমাণ ({bn(pending.length)})
      </div>
      <div style={{ display: "grid", gap: 10, marginBottom: 18 }}>
        {loading ? (
          <Loader text="আবেদন লোড হচ্ছে" />
        ) : pending.length === 0 ? (
          <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>
            নতুন আবেদন নেই
          </div>
        ) : (
          pending.map(Card)
        )}
      </div>
      <div
        style={{
          fontWeight: 800,
          fontSize: 14,
          marginBottom: 8,
          color: C.muted,
        }}
      >
        সিদ্ধান্ত হয়েছে
      </div>
      <div style={{ display: "grid", gap: 10 }}>{decided.map(Card)}</div>
    </Section>
  );
}

/* ═══════════════ ডেটা ব্যাকআপ কার্ড ═══════════════ */
/* পরিচালক সবাইকে একসাথে একটা বার্তা পাঠান — সবার পোর্টালের নোটিফিকেশন
   ঘণ্টায় যায় (এটা সবসময় পৌঁছায়), আর যাঁরা পুশ চালু করেছেন তাঁদের ফোনে/
   ডেস্কটপেও, অ্যাপ বন্ধ থাকলেও। শুধু পাঠায় — কোনো ডাটা বদলায় না। */
function BroadcastCard({ user }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  if (!isDir(user)) return null;
  const READY_MADE =
    "📲 অ্যাপের লোগো ও নাম নতুন করা হয়েছে। যাঁরা ফোনে/পিসিতে অ্যাপটি ইনস্টল " +
    "করে রেখেছেন, একবার আনইনস্টল করে আবার ইনস্টল করে নিন — তাহলেই নতুন " +
    "লোগো ও নাম বসে যাবে। আপনার কোনো তথ্য হারাবে না।";
  const send = () => {
    const msg = text.trim();
    if (!msg) return notice("বার্তা লিখুন।");
    askConfirm(
      `এই বার্তাটি একাডেমির সবাইকে পাঠানো হবে — পরিচালক, এডমিন, উস্তাদ ও সব শিক্ষার্থীকে।

"${msg}"`,
      async () => {
        setBusy(true);
        try {
          const r = await api.broadcastNotification(msg);
          notice(`পাঠানো হয়েছে — ${bn(r?.sent ?? 0)} জনের কাছে।`);
          setText("");
        } catch (e) {
          notice("পাঠানো যায়নি — " + (e?.data?.error || e?.message || "আবার চেষ্টা করুন"));
        } finally {
          setBusy(false);
        }
      },
    );
  };
  return (
    <div style={{ ...S.card, border: `1.5px solid ${C.emerald}`, marginBottom: 14 }}>
      <div style={{ fontWeight: 800, marginBottom: 4 }}>📢 সবাইকে নোটিফিকেশন</div>
      <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>
        একাডেমির সবার পোর্টালের নোটিফিকেশন ঘণ্টায় বার্তাটি চলে যাবে। যাঁরা
        ফোনে নোটিফিকেশন চালু করেছেন, তাঁদের কাছে অ্যাপ বন্ধ থাকলেও পৌঁছাবে।
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        maxLength={500}
        placeholder="যে বার্তাটি সবাইকে জানাতে চান…"
        style={{ ...S.input, width: "100%", resize: "vertical", marginBottom: 8 }}
      />
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Btn sm kind="soft" onClick={() => setText(READY_MADE)}>
          📲 অ্যাপ নতুন করে ইনস্টলের বার্তা বসান
        </Btn>
        <Btn kind="gold" onClick={send} style={{ opacity: busy ? 0.7 : 1 }}>
          {busy ? "পাঠানো হচ্ছে…" : "📢 সবাইকে পাঠান"}
        </Btn>
      </div>
    </div>
  );
}

function BackupCard() {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState(null);

  const handleDownload = async () => {
    setBusy(true);
    setErr(null);
    setDone(false);
    try {
      await downloadBackup();
      setDone(true);
      setTimeout(() => setDone(false), 4000);
    } catch (e) {
      setErr(e.message || "ব্যর্থ হয়েছে");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      style={{
        ...S.card,
        border: `1.5px solid ${C.emerald}`,
        marginBottom: 14,
      }}
    >
      <div style={{ fontWeight: 800, marginBottom: 4 }}>💾 ডেটা ব্যাকআপ</div>
      <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 12 }}>
        সকল ডেটা (ব্যবহারকারী, কোর্স, ফি, ভর্তি, বই, উপস্থিতি ইত্যাদি) JSON
        ফাইলে ডাউনলোড করুন। যেকোনো সময় সার্ভার পরিবর্তন করলেও ডেটা কাছে থাকবে।
      </div>
      <Btn
        kind="soft"
        onClick={handleDownload}
        style={{ opacity: busy ? 0.7 : 1 }}
      >
        {busy
          ? "⏳ ডাউনলোড হচ্ছে…"
          : "⬇️ সম্পূর্ণ ব্যাকআপ ডাউনলোড করুন (.json)"}
      </Btn>
      {done && (
        <div
          style={{
            marginTop: 8,
            fontSize: 12.5,
            color: C.emerald,
            fontWeight: 600,
          }}
        >
          ✔ ডাউনলোড সম্পন্ন হয়েছে — ফাইলটি নিরাপদ জায়গায় রাখুন।
        </div>
      )}
      {err && (
        <div style={{ marginTop: 8, fontSize: 12.5, color: C.red }}>{err}</div>
      )}
    </div>
  );
}

/* ═══════════════ ম্যানেজ সেটিংস — কেবল পরিচালক (পূর্ণ নিয়ন্ত্রণ, কিছুই আড়াল নয়) ═══════════════ */
function ManageView({ db, setDb, user, refresh }) {
  const [show, setShow] = useState(false);
  const [editId, setEditId] = useState(null); // এডিট মোড — কোন ইউজার (null = নতুন)
  const [report, setReport] = useState(null); // কার বিস্তারিত রিপোর্ট দেখা হচ্ছে
  const [f, setF] = useState({
    role: "student",
    name: "",
    user: "",
    pass: genPass(),
    fee: DEFAULT_FEE,
    salary: 10000,
    sub: "",
    courseId: COURSES[0]?.id || "",
  });
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // ব্যাকএন্ড থেকে সব ব্যবহারকারী লোড — ব্যর্থ হলে mock USERS
  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await api.allUsers();
      setAllUsers(
        data.map((u) => ({
          id: u.id,
          role: u.role,
          name: u.name || u.name_bn,
          sub: u.sub || u.sub_title || "",
          user: u.username,
          pass: u.plain_password || u.password || "••••",
          fee: u.monthly_fee,
          salary: u.monthly_salary,
          guardian: u.guardian,
          country: u.country,
          phone: u.phone,
          email: u.email,
          can_fix_cross: u.can_fix_cross,
        })),
      );
    } catch {
      setAllUsers(USERS);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadUsers();
  }, []);

  // বিস্তারিত রিপোর্ট মডালের জন্য আসল ডেটা — আগে এখানে stale mock db/COURSES
  // ব্যবহার হতো (কোর্স/পেমেন্ট/হাজিরা কখনো দেখাত না বা আপডেট হতো না), তাই
  // AccountsView/ProgressView-এর মতোই সরাসরি API থেকে লোড করা হচ্ছে
  const [rCourses, setRCourses] = useState([]);
  const [rFees, setRFees] = useState([]);
  const [rSalaries, setRSalaries] = useState([]);
  const [rDuesMap, setRDuesMap] = useState({});
  const [rAttendance, setRAttendance] = useState([]);
  const [rRatings, setRRatings] = useState([]);
  const [rExams, setRExams] = useState([]);
  const loadReportData = async () => {
    try {
      const [coursesData, feesData, salData, duesData, attData, ratingsData, examsData] =
        await Promise.all([
          api.courses(),
          api.myFees(),
          api.salaries(),
          api.myDues(),
          api.attendanceReport(),
          api.ratings(),
          api.exams(),
        ]);
      setRCourses(coursesData);
      setRFees(feesData);
      setRSalaries(salData);
      const dm = {};
      duesData.forEach((d) => {
        const k = String(d.user || d.userId);
        if (!dm[k]) dm[k] = [];
        dm[k].push(d.month_label || d.month);
      });
      setRDuesMap(dm);
      setRAttendance(attData);
      setRRatings(ratingsData);
      setRExams(
        examsData.map((e) => ({
          ...e,
          total: e.total_marks || e.total,
          marks: e.results || e.marks || {},
        })),
      );
    } catch {
      /* keep mock */
    }
  };
  useEffect(() => {
    loadReportData();
  }, []);

  const openEdit = (u) => {
    // পরিচালক যেকোনো ইউজারের আইডি/পাসওয়ার্ড/নাম/ফি এডিট করতে পারবেন
    setEditId(u.id);
    setF({
      role: u.role,
      name: u.name || "",
      user: u.user || "",
      pass: u.pass && u.pass !== "••••" ? u.pass : "", // খালি = অপরিবর্তিত
      fee: u.fee || DEFAULT_FEE,
      salary: u.salary || 10000,
      sub: u.sub || "",
      courseId: COURSES[0]?.id || "",
    });
    setShow(true);
  };
  const closeForm = () => {
    setShow(false);
    setEditId(null);
    setF({
      role: "student",
      name: "",
      user: "",
      pass: genPass(),
      fee: DEFAULT_FEE,
      salary: 10000,
      sub: "",
      courseId: COURSES[0]?.id || "",
    });
  };
  const saveUser = async () => {
    if (!f.name || !f.user) return notice("নাম ও লগইন আইডি দিন।");
    if (!editId && !f.pass) return notice("পাসওয়ার্ড দিন।");
    setSaving(true);
    try {
      const payload = {
        username: f.user,
        name_bn: f.name,
        role: f.role,
        sub_title:
          f.sub ||
          (f.role === "student"
            ? "নতুন স্টুডেন্ট"
            : f.role === "teacher"
              ? "উস্তাদ/উস্তাদা"
              : "একাডেমিক এডমিন"),
        ...(f.role === "student" ? { monthly_fee: +f.fee } : {}),
        ...(f.role === "teacher" ? { monthly_salary: +f.salary } : {}),
        // পাসওয়ার্ড খালি রাখলে অপরিবর্তিত; নতুন দিলে বদলে যায়
        ...(f.pass && f.pass !== "••••" ? { password: f.pass } : {}),
      };
      await api.saveUser(payload, editId || undefined);
      await loadUsers();
      const wasEdit = !!editId;
      closeForm();
      notice(wasEdit ? "✔ আপডেট হয়েছে" : "✔ নতুন ব্যবহারকারী যোগ হয়েছে");
    } catch (err) {
      if (editId) {
        setSaving(false);
        return notice("আপডেট ব্যর্থ — সার্ভার সংযোগ যাচাই করুন।");
      }
      // ব্যাকএন্ড না থাকলে / আইডি ডুপ্লিকেট — mock এ যোগ
      if (USERS.some((x) => x.user === f.user)) {
        setSaving(false);
        return notice("এই লগইন আইডি আগে থেকেই আছে — অন্যটি দিন।");
      }
      const id = f.role[0] + uid();
      USERS.push({
        id,
        role: f.role,
        name: f.name,
        sub:
          f.sub ||
          (f.role === "student"
            ? "নতুন স্টুডেন্ট"
            : f.role === "teacher"
              ? "উস্তাদ/উস্তাদা"
              : "একাডেমিক এডমিন"),
        user: f.user,
        pass: f.pass,
        ...(f.role === "student" ? { fee: +f.fee } : {}),
        ...(f.role === "teacher" ? { salary: +f.salary } : {}),
      });
      if (f.role === "student")
        COURSES.find((c) => c.id === f.courseId)?.studentIds.push(id);
      if (f.role === "teacher")
        setDb((d) => ({
          ...d,
          permissions: {
            ...d.permissions,
            fixCross: { ...d.permissions.fixCross, [id]: false },
          },
        }));
      setAllUsers([...USERS]);
      setShow(false);
      setF({ ...f, name: "", user: "", pass: genPass() });
      refresh();
    } finally {
      setSaving(false);
    }
  };

  const delUser = (u) =>
    askConfirm(
      `${u.name}-কে মুছে ফেলবেন? এটি ফিরিয়ে আনা যাবে না।`,
      async () => {
        try {
          await api.deleteUser(u.id);
          await loadUsers();
          notice(`✔ ${u.name}-কে মুছে ফেলা হয়েছে।`);
        } catch (e) {
          // আগে ব্যর্থ হলেও তালিকা থেকে সরিয়ে "মুছে গেছে" দেখানো হতো — আসল
          // অ্যাকাউন্টটা সার্ভারে ঠিকই লগইন-সক্ষম থেকে যেত, শুধু স্ক্রিনে ভুল
          // ধারণা হতো যে অ্যাক্সেস বাতিল হয়ে গেছে। এখন স্পষ্ট এরর দেখাচ্ছে।
          notice(
            `${u.name}-কে মুছতে ব্যর্থ — ` +
              (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
          );
        }
      },
    );
  const togglePerm = async (tid) => {
    try {
      await api.toggleFixCross(tid);
      await loadUsers();
    } catch {
      setDb((d) => ({
        ...d,
        permissions: {
          ...d.permissions,
          fixCross: {
            ...d.permissions.fixCross,
            [tid]: !d.permissions.fixCross[tid],
          },
        },
      }));
    }
  };
  const permOn = (t) => t.can_fix_cross ?? db.permissions.fixCross[t.id];
  const roleBn = {
    director: "পরিচালক",
    admin: "এডমিন",
    teacher: "উস্তাদ/উস্তাদা",
    student: "স্টুডেন্ট",
  };

  /* এক ব্যবহারকারীর বিস্তারিত রিপোর্ট — পরিচালক সব দেখেন */
  const UserReport = ({ u }) => {
    const uid2 = String(u.id);
    const att = rAttendance.filter((a) => String(a.user) === uid2);
    const present = att.filter((a) => (a.present ?? a.minutes >= 45)).length,
      missed = att.length - present;
    const ratingsGiven = rRatings.filter((r) => String(r.student) === uid2);
    const ratingsGot = rRatings.filter((r) => String(r.teacher) === uid2);
    const avg = ratingsGot.length
      ? (
          ratingsGot.reduce((s, r) => s + r.stars, 0) / ratingsGot.length
        ).toFixed(1)
      : null;
    const paid = rFees.filter((p) => String(p.student) === uid2);
    const tPaid = rSalaries.filter((p) => String(p.teacher) === uid2);
    const dues = rDuesMap[uid2] || [];
    const exams = rExams.filter((e) => e.marks && e.marks[uid2] != null);
    const cs =
      u.role === "teacher"
        ? rCourses.filter((c) => String(c.teacher) === uid2)
        : rCourses.filter((c) => (c.students || []).some((x) => String(x) === uid2));
    return (
      <Modal
        title={`বিস্তারিত রিপোর্ট — ${u.name}`}
        onClose={() => setReport(null)}
        wide
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 8,
            marginBottom: 12,
            fontSize: 13,
          }}
        >
          <div
            style={{
              padding: "8px 10px",
              background: C.cream,
              borderRadius: 10,
            }}
          >
            ভূমিকা: <b>{roleBn[u.role]}</b>
          </div>
          <div
            style={{
              padding: "8px 10px",
              background: C.cream,
              borderRadius: 10,
            }}
          >
            লগইন: <b>{u.user}</b> · পাস: <b>{u.pass}</b>
          </div>
          {u.role !== "admin" && u.role !== "director" && (
            <div
              style={{
                padding: "8px 10px",
                background: C.cream,
                borderRadius: 10,
              }}
            >
              কোর্স: <b>{cs.map((c) => c.name).join(", ") || "—"}</b>
            </div>
          )}
          {u.role === "student" && (
            <div
              style={{
                padding: "8px 10px",
                background: C.cream,
                borderRadius: 10,
              }}
            >
              অভিভাবক: <b>{u.guardian || "—"}</b> · {u.country || ""}
            </div>
          )}
        </div>
        {(u.role === "student" || u.role === "teacher") && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
              gap: 8,
              marginBottom: 12,
            }}
          >
            <Stat icon="✅" label="উপস্থিত" value={bn(present)} />
            <Stat
              icon="❌"
              label="অনুপস্থিত/অসম্পূর্ণ"
              value={bn(missed)}
              accent={C.red}
            />
            {u.role === "teacher" && (
              <Stat
                icon="🌟"
                label="ক্লাসের মান"
                value={avg ? `★ ${bn(avg)}` : "—"}
                accent={C.gold}
                note={`${bn(ratingsGot.length)}টি মূল্যায়ন`}
              />
            )}
            {u.role === "student" && (
              <Stat
                icon="💰"
                label="ফি দিয়েছে"
                value={`৳${bn(paid.reduce((s, p) => s + (+p.amount || 0), 0).toLocaleString("en"))}`}
                accent={C.gold}
              />
            )}
            <Stat
              icon="⏳"
              label="বকেয়া মাস"
              value={bn(dues.length)}
              accent={dues.length ? C.red : C.emerald}
              note={dues.join(", ") || "নেই"}
            />
          </div>
        )}
        {u.role === "student" && exams.length > 0 && (
          <>
            <div style={{ fontWeight: 800, fontSize: 13.5, margin: "6px 0" }}>
              📝 পরীক্ষার ফল
            </div>
            <Table
              head={["পরীক্ষা", "মার্ক"]}
              rows={exams.map((e) => [
                e.title,
                `${bn(e.marks[uid2])}/${bn(e.total)}`,
              ])}
            />
          </>
        )}
        {u.role === "student" && ratingsGiven.length > 0 && (
          <>
            <div
              style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}
            >
              🌟 সে যেসব মূল্যায়ন করেছে (কেবল পরিচালক/এডমিন দেখেন)
            </div>
            <Table
              head={["উস্তাদ", "রেটিং", "মন্তব্য", "তারিখ"]}
              rows={ratingsGiven.map((r) => [
                allUsers.find((x) => String(x.id) === String(r.teacher))?.name || "—",
                "★".repeat(r.stars),
                r.comment || "—",
                fmtDate(r.rated_at),
              ])}
            />
          </>
        )}
        {u.role === "teacher" && ratingsGot.length > 0 && (
          <>
            <div
              style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}
            >
              🌟 তার সম্পর্কে স্টুডেন্টদের মূল্যায়ন (নাম-মন্তব্যসহ)
            </div>
            <Table
              head={["স্টুডেন্ট", "রেটিং", "মন্তব্য", "তারিখ"]}
              rows={ratingsGot.map((r) => [
                allUsers.find((x) => String(x.id) === String(r.student))?.name || "—",
                "★".repeat(r.stars),
                r.comment || "—",
                fmtDate(r.rated_at),
              ])}
            />
          </>
        )}
        {u.role === "teacher" && (
          <>
            <div
              style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}
            >
              💰 বেতন পরিশোধ
            </div>
            <Table
              head={["মাস", "পরিমাণ", "তারিখ"]}
              rows={tPaid.map((p) => [
                p.month_label,
                `৳${bn((+p.amount || 0).toLocaleString("en"))}`,
                fmtDate(p.paid_at),
              ])}
              empty="এখনো পেমেন্ট হয়নি"
              loading={loading}
            />
          </>
        )}
        {u.role === "student" && (
          <>
            <div
              style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}
            >
              💳 ফি পরিশোধ
            </div>
            <Table
              head={["মাস", "পরিমাণ", "মাধ্যম", "অবস্থা"]}
              rows={paid.map((p) => [
                p.month_label,
                `৳${bn((+p.amount || 0).toLocaleString("en"))}`,
                p.method,
                p.status === "pending" ? "যাচাই বাকি" : "যাচাইকৃত ✔",
              ])}
              empty="এখনো পেমেন্ট নেই"
              loading={loading}
            />
          </>
        )}
        {(u.role === "admin" || u.role === "director") && (
          <div
            style={{
              padding: "10px 12px",
              background: C.cream,
              borderRadius: 10,
              fontSize: 12.5,
              color: C.muted,
            }}
          >
            {u.role === "admin"
              ? "একাডেমিক এডমিন — ক্লাস, লেকচার, ভর্তি, পরীক্ষা, ফি যাচাই ও ফর্ম নিয়ন্ত্রণ করেন। হিসাব-নিকাশ ও ম্যানেজ সেটিংসে প্রবেশাধিকার নেই।"
              : "পরিচালক — সফটওয়্যারের পূর্ণ নিয়ন্ত্রণ।"}
          </div>
        )}
      </Modal>
    );
  };

  return (
    <Section
      title="ম্যানেজ সেটিংস"
      sub="পরিচালকের পূর্ণ নিয়ন্ত্রণ — সবার আইডি-পাসওয়ার্ড, বিস্তারিত রিপোর্ট; কোনো কিছুই আড়াল নয়"
      action={
        <Btn
          onClick={() => {
            setEditId(null);
            setF({
              role: "student",
              name: "",
              user: "",
              pass: genPass(),
              fee: DEFAULT_FEE,
              salary: 10000,
              sub: "",
              courseId: COURSES[0]?.id || "",
            });
            setShow(true);
          }}
        >
          + নতুন ব্যবহারকারী
        </Btn>
      }
    >
      {loading && <Loader text="ব্যবহারকারী তালিকা আসছে" />}
      <div style={{ ...S.card, marginBottom: 14 }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          👥 সকল ব্যবহারকারী — আইডি, পাসওয়ার্ড ও রিপোর্টসহ
        </div>
        <Table
          head={[
            "নাম",
            "ভূমিকা",
            "লগইন আইডি",
            "পাসওয়ার্ড",
            "রিপোর্ট",
            "অ্যাকশন",
          ]}
          rows={allUsers.map((u) => [
            u.name,
            <Tag
              key="r"
              color={
                u.role === "director"
                  ? C.red
                  : u.role === "admin"
                    ? C.emerald
                    : u.role === "teacher"
                      ? C.gold
                      : C.blue
              }
              bg={C.cream}
            >
              {roleBn[u.role]}
            </Tag>,
            u.user,
            <code
              key="p"
              style={{
                background: C.cream,
                padding: "2px 8px",
                borderRadius: 6,
                fontSize: 12,
              }}
            >
              {u.pass}
            </code>,
            <Btn key="rep" sm kind="ghost" onClick={() => setReport(u)}>
              📊 বিস্তারিত
            </Btn>,
            <span key="a" style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
              <Btn sm kind="soft" onClick={() => openEdit(u)}>
                ✏️ এডিট
              </Btn>
              {u.role !== "director" && (
                <Btn sm kind="danger" onClick={() => delUser(u)}>
                  মুছুন
                </Btn>
              )}
            </span>,
          ])}
        />
      </div>
      <div style={{ ...S.card, marginBottom: 14 }}>
        <div style={{ fontWeight: 800, marginBottom: 4 }}>
          🔑 বিশেষ অনুমতি — ভুল সংশোধন
        </div>
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>
          সাধারণত লাল ক্রস (✘) কেবল এডমিন/পরিচালক ঠিক করতে পারেন। কোনো উস্তাদের
          ভুল হলে তাকে সাময়িক এডিটের সুযোগ দিন:
        </div>
        {allUsers
          .filter((u) => u.role === "teacher")
          .map((t) => (
            <div
              key={t.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 10px",
                borderRadius: 10,
                background: C.cream,
                marginBottom: 6,
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  flex: 1,
                  fontSize: 13.5,
                  fontWeight: 600,
                  minWidth: 140,
                }}
              >
                {t.name}
              </span>
              {permOn(t) ? (
                <Tag>অনুমতি চালু ✔</Tag>
              ) : (
                <Tag color={C.muted} bg={"#fff"}>
                  বন্ধ
                </Tag>
              )}
              <Btn
                sm
                kind={permOn(t) ? "danger" : "ghost"}
                onClick={() => togglePerm(t.id)}
              >
                {permOn(t) ? "বন্ধ করুন" : "অনুমতি দিন"}
              </Btn>
            </div>
          ))}
      </div>
      <BroadcastCard user={user} />
      <BackupCard />
      <div style={{ ...S.card, border: `1.5px solid #f3c9b8` }}>
        <div style={{ fontWeight: 800, marginBottom: 4, color: C.red }}>
          ⚠️ ডেঞ্জার জোন
        </div>
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>
          ক্লাস, পরীক্ষা, নোটিশ, বই — প্রতিটি পেজে পরিচালকের জন্য আলাদা "মুছুন"
          বাটন চালু আছে। এছাড়া:
        </div>
        <Btn
          kind="danger"
          sm
          onClick={() =>
            askConfirm("সব নোটিফিকেশন মুছে ফেলবেন?", () =>
              setDb((d) => ({ ...d, notifications: [] })),
            )
          }
        >
          সব নোটিফিকেশন মুছুন
        </Btn>
      </div>
      {report && <UserReport u={report} />}
      {show && (
        <Modal
          title={
            editId ? "✏️ ব্যবহারকারী এডিট করুন" : "নতুন ব্যবহারকারী যোগ করুন"
          }
          onClose={closeForm}
        >
          <label style={S.label}>ভূমিকা</label>
          <select
            style={S.input}
            value={f.role}
            onChange={(e) => setF({ ...f, role: e.target.value })}
          >
            <option value="student">স্টুডেন্ট</option>
            <option value="teacher">উস্তাদ/উস্তাদা</option>
            <option value="admin">এডমিন</option>
          </select>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>নাম</label>
            <input
              style={S.input}
              value={f.name}
              onChange={(e) => setF({ ...f, name: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>লগইন আইডি — জিমেইল বা মোবাইল নম্বর</label>
            <input
              style={S.input}
              value={f.user}
              onChange={(e) => setF({ ...f, user: e.target.value })}
              placeholder="যেমন: name@gmail.com বা 01712345678"
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>
              পাসওয়ার্ড — অক্ষর ও সংখ্যা মিশ্রিত
              {editId ? " (খালি রাখলে অপরিবর্তিত থাকবে)" : ""}
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                style={{ ...S.input, flex: 1 }}
                value={f.pass}
                onChange={(e) => setF({ ...f, pass: e.target.value })}
                placeholder={editId ? "নতুন পাসওয়ার্ড দিলে বদলে যাবে" : ""}
              />
              <Btn kind="soft" onClick={() => setF({ ...f, pass: genPass() })}>
                🎲 বানিয়ে দিন
              </Btn>
            </div>
          </div>
          {f.role === "student" && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 10,
                marginTop: 10,
              }}
            >
              <div>
                <label style={S.label}>মাসিক ফি (৳)</label>
                <input
                  type="number"
                  style={S.input}
                  value={f.fee}
                  onChange={(e) => setF({ ...f, fee: e.target.value })}
                />
              </div>
              <div>
                <label style={S.label}>কোর্স</label>
                <select
                  style={S.input}
                  value={f.courseId}
                  onChange={(e) => setF({ ...f, courseId: e.target.value })}
                >
                  {COURSES.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
          {f.role === "teacher" && (
            <div style={{ marginTop: 10 }}>
              <label style={S.label}>মাসিক বেতন (৳)</label>
              <input
                type="number"
                style={S.input}
                value={f.salary}
                onChange={(e) => setF({ ...f, salary: e.target.value })}
              />
            </div>
          )}
          <Btn
            style={{
              marginTop: 16,
              width: "100%",
              justifyContent: "center",
              opacity: saving ? 0.7 : 1,
            }}
            onClick={saveUser}
          >
            {saving
              ? "সংরক্ষণ হচ্ছে…"
              : editId
                ? "✏️ সংরক্ষণ করুন"
                : "যোগ করুন — আইডি ও পাসওয়ার্ড তৈরি হবে"}
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ লাইভ ক্লাস ফুল-পেজ পপআপ (স্টুডেন্ট) — আয়াতসহ ═══════════════ */
function LiveClassPopup({ k, course, user, onJoin, onLater }) {
  const T = (bnText, enText) => (user?.role === "student" ? enText : bnText);
  const lec = course.lectures?.[k.lectureNo - 1];
  // শিক্ষার্থীর পপআপে জয়েন বাটন সবসময় থাকে (১ম লিংক)। রিজয়েন বাটন আসে কেবল
  // উস্তাদ নিজের রিজয়েন বাটনে ক্লিক করার পর — তার আগে অপেক্ষার বার্তা দেখায়,
  // যাতে শিক্ষার্থী ভুল করে অন্য মিটিংয়ে ঢুকে না পড়েন
  const rejoinOpen = bothJoinedToday(k);
  // অপেক্ষার বার্তা শুরুতেই নয় — শিক্ষার্থী একবার জয়েন করার পর থেকে (নইলে
  // "wait" পড়ে জয়েনই না করে বসে থাকতে পারে)
  const hasJoinedOnce = (k.attendance || []).some(
    (a) => String(a.user) === String(user?.id),
  );
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        background: `linear-gradient(160deg, ${C.emeraldD} 0%, ${C.emerald} 55%, ${C.emeraldL} 100%)`,
        display: "grid",
        placeItems: "center",
        padding: 18,
        overflowY: "auto",
      }}
    >
      <div
        style={{
          maxWidth: 520,
          width: "100%",
          textAlign: "center",
          color: "#fff",
        }}
      >
        <div style={{ animation: "tqaPulse 1.6s infinite" }}>
          <img
            src="/brand/logo-green.png"
            alt="তারবিয়াতুল কুরআন একাডেমি"
            style={{ width: 60, height: 60, borderRadius: 14 }}
          />
        </div>
        <div
          style={{
            fontFamily: "'Amiri', 'Hind Siliguri', serif",
            fontSize: 30,
            color: C.goldL,
            margin: "10px 0 4px",
            lineHeight: 1.7,
          }}
        >
          ﴿وَقُلْ رَبِّ زِدْنِي عِلْمًا﴾
        </div>
        <div style={{ fontSize: 14, color: "#d7e9de", marginBottom: 4 }}>
          {T(
            '"এবং বলো: হে আমার রব! আমার জ্ঞান বৃদ্ধি করে দিন।"',
            '"And say: My Lord, increase me in knowledge."',
          )}
        </div>
        <div style={{ fontSize: 11.5, color: "#9fc4ae", marginBottom: 18 }}>
          {T("— সূরা ত্বহা, আয়াত ১১৪", "— Surah Taha, Ayah 114")}
        </div>
        <div
          style={{
            background: "rgba(255,255,255,.10)",
            border: `1px solid rgba(240,195,85,.4)`,
            borderRadius: 20,
            padding: "22px 20px",
            backdropFilter: "blur(4px)",
          }}
        >
          <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 6 }}>
            {T("✨ এখনই দারস শুরু হবে — জয়েন করো!", "✨ Class is starting now — join in!")}
          </div>
          <div style={{ fontSize: 14.5, fontWeight: 700, color: C.goldL }}>
            {course.name} · {T(`লেকচার ${bn(k.lectureNo)}`, `Lecture ${k.lectureNo}`)}
          </div>
          {lec && (
            <div style={{ fontSize: 13, color: "#d7e9de", margin: "4px 0" }}>
              {lec.title}
            </div>
          )}
          <div style={{ fontSize: 12.5, color: "#cfe6d8", marginBottom: 16 }}>
            🕐 {k.time} · {T("উস্তাদ", "Teacher")}: {course.teacher_name || userById(course.teacherId || course.teacher).name}
          </div>
          {/* উস্তাদ রিজয়েন চালু করার পর ১ম লিংক আর দেখানো হয় না — নইলে
              শিক্ষার্থী ভুল করে পুরনো মিটিংয়ে ঢুকে পড়ত */}
          {!rejoinOpen && (
          <a
            href={k.zoom}
            target="_blank"
            rel="noreferrer"
            onClick={() => onJoin(k)}
            style={{
              display: "block",
              textDecoration: "none",
              width: "100%",
              background: "linear-gradient(135deg, #d92626, #b91c1c)",
              color: "#fff",
              fontSize: 17,
              fontWeight: 800,
              padding: "16px 20px",
              borderRadius: 14,
              boxShadow: "0 8px 24px rgba(217,38,38,.45)",
              animation: "tqaPulse 1.6s infinite",
              textAlign: "center",
              boxSizing: "border-box",
            }}
          >
            {T("🎥 এখনই জয়েন করুন — জুম খুলে যাবে", "🎥 Join Now — Zoom will open")}
          </a>
          )}
          {rejoinOpen ? (
            <a
              href={k.zoom2 || k.zoom}
              target="_blank"
              rel="noreferrer"
              onClick={() => onJoin(k)}
              style={{
                display: "block",
                textDecoration: "none",
                width: "100%",
                background: `linear-gradient(135deg, ${C.goldL}, ${C.gold})`,
                color: "#4a3200",
                fontSize: 16,
                fontWeight: 800,
                padding: "14px 20px",
                borderRadius: 14,
                boxShadow: "0 8px 24px rgba(240,195,85,.45)",
                textAlign: "center",
                boxSizing: "border-box",
              }}
            >
              🔁 Rejoin — Zoom will open
            </a>
          ) : hasJoinedOnce ? (
            <div
              style={{
                marginTop: 10,
                padding: "12px 16px",
                borderRadius: 12,
                background: "rgba(255,255,255,.12)",
                border: `1px solid rgba(240,195,85,.45)`,
                color: C.goldL,
                fontSize: 14,
                fontWeight: 700,
                textAlign: "center",
              }}
            >
              ⏳ Teacher is joining, please wait
            </div>
          ) : null}
          <div
            style={{
              fontSize: 13,
              color: "#d7e9de",
              marginTop: 14,
              fontStyle: "italic",
            }}
          >
            {T("জাযাকাল্লাহু খাইরান ফীদ-দ্বারাইন 🤲", "Jazakallahu Khairan Fid-darayn 🤲")}
          </div>
        </div>
        <button
          onClick={onLater}
          style={{
            marginTop: 16,
            border: "1px solid rgba(255,255,255,.35)",
            background: "transparent",
            color: "#cfe6d8",
            fontFamily: "inherit",
            fontSize: 12.5,
            padding: "8px 18px",
            borderRadius: 99,
            cursor: "pointer",
          }}
        >
          {T("পরে জয়েন করব", "I'll join later")}
        </button>
      </div>
      <style>{`@keyframes tqaPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.035)}}`}</style>
    </div>
  );
}

/* ═══════════════ স্টুডেন্ট পেমেন্ট পেজ — হিস্টরি, রিসিট (চোখ), এখনই পেমেন্ট ═══════════════ */
function StudentPaymentsView({ db, setDb, user }) {
  const [payMonth, setPayMonth] = useState(null);
  const [pf, setPf] = useState({
    method: "বিকাশ",
    trx: "",
    shot: null,
    shotFile: null,
  });
  const [duaMsg, setDuaMsg] = useState(false);
  const [fees, setFees] = useState(
    db.feePayments.filter((p) => p.studentId === user.id),
  );
  const [dues, setDues] = useState(db.dueMonths[user.id] || []);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে

  const loadData = async () => {
    setLoading(true);
    try {
      const [fData, dData] = await Promise.all([api.myFees(), api.myDues()]);
      setFees(
        fData.map((p) => ({
          id: p.id,
          studentId: p.student,
          amount: p.amount,
          month: p.month_label,
          date: p.paid_at,
          method: p.method + (p.trx_id ? ` (Trx: ${p.trx_id})` : ""),
          shot: p.screenshot
            ? { data: p.screenshot, name: "screenshot" }
            : null,
          status: p.status,
        })),
      );
      setDues(dData.map((d) => d.month_label));
    } catch {
      /* mock ডেটা থাকবে */
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const paid = fees;
  const totalPaid = paid
    .filter((p) => p.status !== "pending")
    .reduce((s, p) => s + p.amount, 0);
  const userFee = user.monthly_fee || user.fee || 0;
  const pickShot = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () =>
      setPf((x) => ({
        ...x,
        shot: { data: r.result, name: f.name },
        shotFile: f,
      }));
    r.readAsDataURL(f);
  };
  const submitPay = async () => {
    if (!pf.trx.trim() && !pf.shot)
      return notice("Please add a screenshot or transaction ID.");
    try {
      await api.payFee({
        amount: userFee,
        month_label: payMonth,
        method: pf.method
          .toLowerCase()
          .replace("বিকাশ", "bkash")
          .replace("নগদ", "nagad")
          .replace("ব্যাংক ট্রান্সফার", "bank"),
        trx_id: pf.trx,
        screenshot: pf.shotFile || undefined,
      });
      await loadData();
      notice(`✔ Payment for ${payMonth} submitted — pending verification.`);
    } catch (e) {
      notice(
        "Failed to submit payment — " +
          (e?.data?.error || e?.message || "check your connection and try again"),
      );
      return;
    }
    setPayMonth(null);
    setPf({ method: "বিকাশ", trx: "", shot: null, shotFile: null });
    setDuaMsg(true);
  };
  const acct = {
    বিকাশ: {
      icon: "📱",
      name: "bKash",
      line1: "bKash Personal (Send Money)",
      line2: "Number: 01402-499027",
    },
    নগদ: {
      icon: "🟠",
      name: "Nagad",
      line1: "Nagad Personal (Send Money)",
      line2: "Number: 01402-499027",
    },
    "ব্যাংক ট্রান্সফার": {
      icon: "🏦",
      name: "Bank Transfer",
      line1: "Islami Bank Bangladesh — Tarbiyatul Quran Academy",
      line2: "Account No: 2050-1234-5678-901 (Dhaka Branch)",
    },
  };
  return (
    <Section
      title="Payments"
      sub="All payment history, dues, and receipts from the start"
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: 10,
          marginBottom: 16,
        }}
      >
        <Stat
          icon="✅"
          label="Total Paid (Verified)"
          value={`৳${totalPaid.toLocaleString("en")}`}
        />
        <Stat
          icon="⏳"
          label="Due"
          value={`৳${(dues.length * userFee).toLocaleString("en")}`}
          /* ⚠️ বকেয়ার রেকর্ড না থাকলেই "no dues" বলা যায় না — বকেয়া তৈরি
             হয় মাসিক cron চললে। কেউ কখনো কিছু না দিয়ে থাকলে সেটাই বলি,
             নইলে "Alhamdulillah, no dues" দেখে ভুল বোঝার সুযোগ থাকত। */
          accent={dues.length || totalPaid === 0 ? C.red : C.emerald}
          note={
            dues.join(", ") ||
            (totalPaid === 0
              ? "No payment recorded yet"
              : "Alhamdulillah, no dues")
          }
        />
      </div>
      {dues.length > 0 && (
        <div
          style={{
            ...S.card,
            marginBottom: 14,
            borderLeft: `4px solid ${C.red}`,
          }}
        >
          <div style={{ fontWeight: 800, marginBottom: 10 }}>⏳ Due Fees</div>
          {dues.map((m) => (
            <div
              key={m}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 12px",
                borderRadius: 10,
                background: C.redBg,
                marginBottom: 8,
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  flex: 1,
                  fontWeight: 700,
                  fontSize: 14,
                  minWidth: 140,
                }}
              >
                {m} — ৳{userFee.toLocaleString("en")}
              </span>
              <Btn sm kind="gold" onClick={() => setPayMonth(m)}>
                ⚡ Pay Now
              </Btn>
            </div>
          ))}
        </div>
      )}
      <div style={{ ...S.card }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          📜 Payment History
        </div>
        <Table
          loading={loading}
          head={["Month", "Amount", "Date", "Method", "Status"]}
          rows={paid.map((p) => [
            p.month,
            `৳${p.amount.toLocaleString("en")}`,
            fmtDate(p.date),
            p.method,
            p.status === "pending" ? (
              <span
                key="s"
                style={{
                  background: C.amberBg,
                  color: "#a16207",
                  border: "1.5px solid #f0c355",
                  fontSize: 11.5,
                  fontWeight: 800,
                  padding: "4px 12px",
                  borderRadius: 99,
                  whiteSpace: "nowrap",
                }}
              >
                ⏳ Pending
              </span>
            ) : (
              <span
                key="s"
                style={{
                  background: C.greenBg,
                  color: C.green,
                  border: `1.5px solid ${C.green}`,
                  fontSize: 11.5,
                  fontWeight: 800,
                  padding: "4px 12px",
                  borderRadius: 99,
                  whiteSpace: "nowrap",
                }}
              >
                ✔ Verified
              </span>
            ),
          ])}
          empty="No payments yet"
        />
      </div>
      {payMonth && (
        <Modal
          title={`Pay Now — ${payMonth}`}
          onClose={() => setPayMonth(null)}
        >
          <div
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              background: C.greenBg,
              fontSize: 13.5,
              fontWeight: 700,
              marginBottom: 12,
            }}
          >
            Amount: ৳{userFee.toLocaleString("en")}
          </div>
          <label style={S.label}>Payment Method</label>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 8,
              marginBottom: 10,
            }}
          >
            {Object.keys(acct).map((m) => (
              <button
                key={m}
                onClick={() => setPf({ ...pf, method: m })}
                style={{
                  padding: "11px 6px",
                  borderRadius: 10,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: 700,
                  fontSize: 12.5,
                  border: `2px solid ${pf.method === m ? C.emerald : C.line}`,
                  background: pf.method === m ? C.greenBg : "#fff",
                  color: pf.method === m ? C.emerald : C.text,
                }}
              >
                {acct[m].icon}
                <br />
                {acct[m].name}
              </button>
            ))}
          </div>
          <div
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              background: C.cream,
              fontSize: 13,
              marginBottom: 12,
            }}
          >
            <b>{acct[pf.method].line1}</b>
            <br />
            {acct[pf.method].line2}
          </div>
          <label style={S.label}>Transaction ID</label>
          <input
            style={S.input}
            value={pf.trx}
            onChange={(e) => setPf({ ...pf, trx: e.target.value })}
            placeholder="e.g. 9HX2K7QM"
          />
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>Payment Screenshot</label>
            <label
              style={{
                display: "grid",
                placeItems: "center",
                gap: 4,
                padding: "18px 12px",
                border: `2px dashed ${pf.shot ? C.emerald : C.line}`,
                borderRadius: 12,
                cursor: "pointer",
                background: pf.shot ? C.greenBg : C.cream,
                textAlign: "center",
              }}
            >
              <span style={{ fontSize: 24 }}>{pf.shot ? "✅" : "🖼️"}</span>
              <span style={{ fontSize: 12.5, fontWeight: 700 }}>
                {pf.shot ? pf.shot.name : "Add a screenshot / photo"}
              </span>
              <input
                type="file"
                accept="image/*"
                style={{ display: "none" }}
                onChange={pickShot}
              />
            </label>
            {pf.shot && (
              <img
                src={pf.shot.data}
                alt="Screenshot"
                style={{
                  width: "100%",
                  borderRadius: 10,
                  marginTop: 8,
                  border: `1px solid ${C.line}`,
                }}
              />
            )}
          </div>
          <div
            style={{
              fontSize: 12.5,
              color: C.muted,
              marginTop: 10,
              textAlign: "center",
            }}
          >
            Please complete the payment, then add a screenshot or transaction
            ID and verify.
          </div>
          <Btn
            style={{ marginTop: 12, width: "100%", justifyContent: "center" }}
            onClick={submitPay}
          >
            ✔ Verify
          </Btn>
        </Modal>
      )}
      {duaMsg && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 120,
            background: "rgba(18,63,40,.55)",
            display: "grid",
            placeItems: "center",
            padding: 16,
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 20,
              maxWidth: 430,
              width: "100%",
              padding: 28,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 40 }}>🤲</div>
            <div
              style={{
                fontFamily: "'Amiri', serif",
                fontSize: 21,
                color: C.emerald,
                lineHeight: 2,
                margin: "10px 0 6px",
              }}
            >
              باركَ الله لك في أهلِكَ ومالِكَ، إنَّما جزاءُ السَّلفِ الوفاءُ
              والحمدُ
            </div>
            <div style={{ fontSize: 13.5, color: C.text, marginBottom: 6 }}>
              "May Allah bless you in your family and wealth. The reward for a
              debt repaid is nothing but full payment and gratitude."
            </div>
            <div style={{ fontSize: 11.5, color: C.muted, marginBottom: 14 }}>
              — Sunan al-Nasa'i and Ibn Majah
            </div>
            <div
              style={{
                padding: "10px 12px",
                borderRadius: 10,
                background: C.greenBg,
                color: C.green,
                fontWeight: 700,
                fontSize: 13.5,
              }}
            >
              ✔ Your payment has been submitted! It will show "Verified" once
              the director confirms it, InshaAllah.
            </div>
            <Btn
              style={{ marginTop: 14, width: "100%", justifyContent: "center" }}
              onClick={() => setDuaMsg(false)}
            >
              Alhamdulillah
            </Btn>
          </div>
        </div>
      )}
    </Section>
  );
}

/* ═══════════════ রিসিট বানানোর টুল — যে কারো জন্য PDF রিসিট/ভাউচার ═══════════════ */
function ReceiptMaker({ onClose, user }) {
  // আগে mock USERS থেকে তালিকা আসত (আসল ছাত্র/উস্তাদ দেখাতো না) — এখন সরাসরি API থেকে
  const [students, setStudents] = useState([]);
  const [teachers, setTeachers] = useState([]);
  useEffect(() => {
    api
      .allStudents()
      .then((d) => setStudents(d.map(adaptPerson)))
      .catch(() => {});
    if (isDir(user))
      api
        .allTeachers()
        .then((d) => setTeachers(d.map(adaptPerson)))
        .catch(() => {});
  }, []);
  const [f, setF] = useState({
    who: "custom",
    custom: "",
    kind: "ফি পরিশোধ রিসিট",
    month: "",
    amount: "",
    currency: "৳",
    method: "বিকাশ",
    date: todayISO(),
  });
  // মাসিক ফি/বেতন রিসিটে মাস ক্যালেন্ডার থেকে বাছাই হয় (backend-এর DueMonth
  // লেবেলের সাথে ফরম্যাট মেলাতে) — ভর্তি/অনুদান/অন্যান্যতে যেকোনো বিবরণ লেখা যায়
  const isMonthKind = f.kind === "ফি পরিশোধ রিসিট" || f.kind === "বেতন পরিশোধ ভাউচার";
  const monthDisplay = isMonthKind ? (f.month ? monthLabelBn(f.month) : "") : f.month;
  // মাসিক ফি/ভর্তি/অনুদান হলে স্টুডেন্ট তালিকা, বেতন হলে উস্তাদ তালিকা
  const people = f.kind === "বেতন পরিশোধ ভাউচার" ? teachers : students;
  // কাইন্ড বদলালে বা তালিকা লোড হলে আগের বাছাই অবৈধ হয়ে গেলে প্রথম জনকে বেছে দিই
  useEffect(() => {
    if (!people.some((p) => String(p.id) === String(f.who))) {
      setF((prev) => ({ ...prev, who: people[0]?.id ?? "custom" }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [people]);
  const make = () => {
    const person =
      f.who === "custom"
        ? { name: f.custom.trim() }
        : people.find((p) => String(p.id) === String(f.who)) || {};
    if (!person.name) return notice("নাম দিন।");
    if (!f.amount || +f.amount <= 0) return notice("সঠিক পরিমাণ দিন।");
    printReceipt(
      {
        id: uid(),
        month: monthDisplay || "—",
        amount: +f.amount,
        currency: f.currency,
        method: methodEn(f.method),
        date: fmtDateEn(f.date),
        status: "verified",
      },
      person,
      f.kind,
    );
  };
  return (
    <Modal title="🧾 রিসিট বানান" onClose={onClose}>
      <label style={S.label}>রিসিটের ধরন</label>
      <select
        style={S.input}
        value={f.kind}
        onChange={(e) => setF({ ...f, kind: e.target.value, month: "" })}
      >
        <option>ফি পরিশোধ রিসিট</option>
        {isDir(user) && <option>বেতন পরিশোধ ভাউচার</option>}
        <option>ভর্তি ফি রিসিট</option>
        <option>অনুদান রিসিট</option>
        <option>অন্যান্য পরিশোধ রিসিট</option>
      </select>
      <div style={{ marginTop: 10 }}>
        <label style={S.label}>কার জন্য</label>
        <select
          style={S.input}
          value={f.who}
          onChange={(e) => setF({ ...f, who: e.target.value })}
        >
          {people.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name} ({f.kind === "বেতন পরিশোধ ভাউচার" ? "উস্তাদ" : "স্টুডেন্ট"})
            </option>
          ))}
          <option value="custom">✏️ অন্য কেউ — নিজে লিখুন</option>
        </select>
      </div>
      {f.who === "custom" && (
        <div style={{ marginTop: 10 }}>
          <label style={S.label}>নাম</label>
          <input
            style={S.input}
            value={f.custom}
            onChange={(e) => setF({ ...f, custom: e.target.value })}
          />
        </div>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 10,
          marginTop: 10,
        }}
      >
        <div>
          <label style={S.label}>{isMonthKind ? "মাস ও সাল" : "মাস / বিবরণ"}</label>
          {isMonthKind ? (
            <input
              type="month"
              style={S.input}
              value={f.month}
              onChange={(e) => setF({ ...f, month: e.target.value })}
            />
          ) : (
            <input
              style={S.input}
              value={f.month}
              onChange={(e) => setF({ ...f, month: e.target.value })}
              placeholder="যেমন: ভর্তি ফি"
            />
          )}
        </div>
        <div>
          <label style={S.label}>পরিমাণ</label>
          <div style={{ display: "flex", gap: 6 }}>
            <select
              style={{ ...S.input, width: 78, flexShrink: 0 }}
              value={f.currency}
              onChange={(e) => setF({ ...f, currency: e.target.value })}
              title="মুদ্রা"
            >
              <option value="৳">৳ টাকা</option>
              <option value="$">$ ডলার</option>
            </select>
            <input
              type="number"
              style={S.input}
              value={f.amount}
              onChange={(e) => setF({ ...f, amount: e.target.value })}
            />
          </div>
        </div>
        <div>
          <label style={S.label}>মাধ্যম</label>
          <select
            style={S.input}
            value={f.method}
            onChange={(e) => setF({ ...f, method: e.target.value })}
          >
            <option>বিকাশ</option>
            <option>নগদ</option>
            <option>ব্যাংক ট্রান্সফার</option>
            <option>নগদ গ্রহণ (অফিস)</option>
          </select>
        </div>
        <div>
          <label style={S.label}>তারিখ</label>
          <input
            type="date"
            style={S.input}
            value={f.date}
            onChange={(e) => setF({ ...f, date: e.target.value })}
          />
        </div>
      </div>
      <Btn
        style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
        onClick={make}
      >
        🧾 PDF রিসিট তৈরি করুন
      </Btn>
      <div
        style={{
          fontSize: 11.5,
          color: C.muted,
          textAlign: "center",
          marginTop: 8,
        }}
      >
        রিসিট প্রিভিউ খুলবে — সেখান থেকে ⬇️ ডাউনলোড বা 📨 সেন্ড করা যাবে
      </div>
    </Modal>
  );
}

/* ═══════════════ পরিচালকের স্টুডেন্ট পেমেন্ট — ভেরিফাই (কেবল পরিচালক) + WhatsApp রিমাইন্ডার ═══════════════ */
function DirectorPaymentsView({ db, setDb, user }) {
  const [viewShot, setViewShot] = useState(null);
  const [maker, setMaker] = useState(false);
  const [fees, setFees] = useState(db.feePayments);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে
  const [mp, setMp] = useState({
    studentId: "",
    month: "",
    method: "নগদ",
  });
  const [mpBusy, setMpBusy] = useState(false);
  const [genDuesBusy, setGenDuesBusy] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [fData, sData] = await Promise.all([
        api.myFees(),
        api.allStudents(),
      ]);
      setFees(
        fData.map((p) => ({
          id: p.id,
          studentId: p.student,
          studentName: p.student_name,
          amount: p.amount,
          month: p.month_label,
          date: p.paid_at,
          method: p.method + (p.trx_id ? ` (Trx: ${p.trx_id})` : ""),
          shot: p.screenshot
            ? { data: p.screenshot, name: "screenshot" }
            : null,
          status: p.status,
        })),
      );
      setStudents(
        sData.map((s) => ({
          id: s.id,
          role: "student",
          name: s.name || s.name_bn,
          fee: s.monthly_fee,
          guardian: s.guardian,
          phone: s.phone,
          email: s.email,
          dueMonths: s.due_months || [],
        })),
      );
    } catch {
      /* mock থাকবে */
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const pending = fees.filter((p) => p.status === "pending");
  const verified = fees.filter((p) => p.status !== "pending");
  const verify = async (pid) => {
    try {
      await api.verifyFee(pid);
      await loadData();
      notice("✔ পেমেন্ট ভেরিফাই হয়েছে।");
    } catch (e) {
      // আগে ব্যর্থ হলেও স্ক্রিনে "ভেরিফাইড" দেখানো হতো, সার্ভারে আসলে হতো না —
      // এখন স্পষ্ট এরর দেখাচ্ছে, স্ক্রিনে ভুয়া স্ট্যাটাস বসাচ্ছে না
      notice(
        "ভেরিফাই করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const studentById = (id) => students.find((s) => s.id === id) || userById(id);

  // পরিচালক/এডমিন সরাসরি যেকোনো স্টুডেন্টের যেকোনো মাসের (সামনে বা পিছনের) পেমেন্ট
  // "পরিশোধিত" হিসেবে সরাসরি সেভ করতে পারেন — স্টুডেন্টের নিজে জমা দেওয়ার অপেক্ষা ছাড়াই
  const markPaid = async () => {
    const st = students.find((s) => String(s.id) === String(mp.studentId));
    if (!st) return notice("স্টুডেন্ট বেছে নিন।");
    if (!mp.month) return notice("মাস ও সাল বেছে নিন।");
    const label = monthLabelBn(mp.month); // "2026-07" → "জুলাই ২০২৬" — backend-এর DueMonth লেবেলের সাথে হুবহু মিলতে হবে, নইলে বকেয়া মুছবে না
    setMpBusy(true);
    try {
      await api.recordPayment({
        student_id: st.id,
        month_label: label,
        amount: st.fee || 0,
        method: mp.method
          .toLowerCase()
          .replace("বিকাশ", "bkash")
          .replace("নগদ গ্রহণ (অফিস)", "cash")
          .replace("নগদ", "nagad")
          .replace("ব্যাংক ট্রান্সফার", "bank"),
      });
      notice(`✔ ${st.name}-এর "${label}" মাসের পেমেন্ট পরিশোধিত হিসেবে সেভ হয়েছে।`);
      setMp((prev) => ({ ...prev, month: "" }));
      await loadData();
    } catch (e) {
      notice("সেভ করতে ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
    }
    setMpBusy(false);
  };
  const dueStudents = students.filter((s) => (s.dueMonths || []).length > 0);
  // ছুটির মাসের বকেয়া মওকুফ — সরিয়ে দিয়ে তালিকা নতুন করে আনি
  const waiveDueHere = async (studentId, monthLabel, reason) => {
    try {
      await api.waiveDue(studentId, monthLabel, reason);
      await loadData();
      notice(`✔ "${monthLabel}" মাসের বকেয়া মওকুফ করা হয়েছে।`);
    } catch (e) {
      notice(
        "মওকুফ করা যায়নি — " +
          (e?.data?.error || e?.message || "আবার চেষ্টা করুন"),
      );
    }
  };

  const waMsg = (s) => {
    const dues = s.dueMonths || db.dueMonths[s.id] || [];
    return `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহি ওয়া বারাকাতুহ।\n\nমুহতারাম ${s.guardian || "অভিভাবক"},\nতারবিয়াতুল কুরআন একাডেমির পক্ষ থেকে আন্তরিক দুআ ও সালাম। আল্লাহ তাআলা আপনার সন্তানের ইলম ও আমলে বরকত দান করুন।\n\nবিনয়ের সাথে স্মরণ করিয়ে দিচ্ছি — ${s.name}-এর ${dues.join(", ")} মাসের ফি (মোট ৳${(dues.length * (s.fee || 0)).toLocaleString("en")}) এখনো অপরিশোধিত রয়েছে। আপনার সুবিধাজনক সময়ে পরিশোধ করে দিলে কৃতজ্ঞ থাকব ইনশাআল্লাহ।\n\nজাযাকুমুল্লাহু খাইরান।\n— তারবিয়াতুল কুরআন একাডেমি`;
  };
  const sendAll = () => {
    const full = dueStudents
      .map((s) => {
        const dm = s.dueMonths || [];
        return `• ${s.name} (${s.guardian || ""}): ${dm.join(", ")} — ৳${(dm.length * (s.fee || 0)).toLocaleString("en")}`;
      })
      .join("\n");
    const msg = `আসসালামু আলাইকুম ওয়া রাহমাতুল্লাহ।\nমুহতারাম অভিভাবকবৃন্দ, বিনয়ের সাথে ফি পরিশোধের কথা স্মরণ করিয়ে দিচ্ছি ইনশাআল্লাহ:\n${full}\nজাযাকুমুল্লাহু খাইরান। — তারবিয়াতুল কুরআন একাডেমি`;
    navigator.clipboard?.writeText(msg.replace(/\\n/g, "\n"));
    notice(
      "সবার রিমাইন্ডার মেসেজ কপি হয়েছে ✔ — WhatsApp গ্রুপ বা ব্রডকাস্ট লিস্টে পেস্ট করে পাঠিয়ে দিন।",
    );
  };
  // এখানকার বাটন শুধু স্টুডেন্টদের বকেয়া তৈরি করে (roles=["student"]) — উস্তাদদের
  // বকেয়া তৈরি হয় "হিসাব-নিকাশ" পেজের বাটন থেকে, দুটো আলাদা রাখা হয়েছে
  const genDuesNow = async () => {
    setGenDuesBusy(true);
    try {
      const r = await api.generateMonthlyDues("student");
      notice(`✔ চলতি মাসের স্টুডেন্ট বকেয়া তৈরি হয়েছে — ${bn(r.created)}টি নতুন যোগ হলো`);
      await loadData();
    } catch (e) {
      notice("বকেয়া তৈরি ব্যর্থ — " + (e?.message || "যাচাই করুন"));
    }
    setGenDuesBusy(false);
  };
  return (
    <Section
      title="স্টুডেন্ট পেমেন্ট"
      sub="কে পেমেন্ট করেছে, কার বাকি — মিলিয়ে ভেরিফাই করুন (ভেরিফাই কেবল পরিচালকই করতে পারেন)"
      action={
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Btn
            kind="soft"
            onClick={genDuesNow}
            style={{ opacity: genDuesBusy ? 0.6 : 1 }}
          >
            {genDuesBusy ? "⏳ তৈরি হচ্ছে…" : "🔄 এই মাসের বকেয়া তৈরি করুন"}
          </Btn>
          <Btn kind="gold" onClick={() => setMaker(true)}>
            🧾 রিসিট বানান
          </Btn>
        </div>
      }
    >
      {maker && <ReceiptMaker user={user} onClose={() => setMaker(false)} />}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: 10,
          marginBottom: 16,
        }}
      >
        <Stat
          icon="⏳"
          label="ভেরিফাই বাকি"
          value={bn(pending.length)}
          accent={C.gold}
        />
        <Stat icon="✅" label="ভেরিফাইড পেমেন্ট" value={bn(verified.length)} />
        <Stat
          icon="📵"
          label="বকেয়া আছে"
          value={`${bn(dueStudents.length)} জন`}
          accent={C.red}
        />
      </div>
      <div
        style={{
          ...S.card,
          marginBottom: 14,
          borderLeft: `4px solid ${C.green}`,
        }}
      >
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          ✅ যেকোনো মাসের পেমেন্ট সরাসরি সম্পন্ন করুন
        </div>
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 10 }}>
          স্টুডেন্ট নিজে জমা না দিলেও, যেকোনো (সামনের বা পিছনের) মাসের পেমেন্ট
          এখান থেকে সরাসরি "পরিশোধিত" হিসেবে সেভ করতে পারবেন — সেই মাসের বকেয়া
          থাকলে তা অটো সরে যাবে।
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.4fr 1fr 1fr auto",
            gap: 8,
            alignItems: "end",
          }}
        >
          <div>
            <label style={S.label}>স্টুডেন্ট</label>
            <select
              style={S.input}
              value={mp.studentId}
              onChange={(e) => setMp({ ...mp, studentId: e.target.value })}
            >
              <option value="">বেছে নিন</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={S.label}>মাস ও সাল</label>
            <input
              type="month"
              style={S.input}
              value={mp.month}
              onChange={(e) => setMp({ ...mp, month: e.target.value })}
            />
          </div>
          <div>
            <label style={S.label}>মাধ্যম</label>
            <select
              style={S.input}
              value={mp.method}
              onChange={(e) => setMp({ ...mp, method: e.target.value })}
            >
              <option>নগদ</option>
              <option>বিকাশ</option>
              <option>ব্যাংক ট্রান্সফার</option>
              <option>নগদ গ্রহণ (অফিস)</option>
            </select>
          </div>
          <Btn
            kind="gold"
            onClick={markPaid}
            style={{ opacity: mpBusy ? 0.6 : 1 }}
          >
            {mpBusy ? "⏳ সেভ হচ্ছে…" : "✔ সম্পন্ন করুন"}
          </Btn>
        </div>
      </div>
      <div
        style={{
          ...S.card,
          marginBottom: 14,
          borderLeft: `4px solid ${C.gold}`,
        }}
      >
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          ⏳ ভেরিফাইয়ের অপেক্ষায় — মিলিয়ে দেখে ক্লিক করুন
        </div>
        {loading && <Loader text="পেমেন্ট লোড হচ্ছে" />}
        {!loading && pending.length === 0 && (
          <div
            style={{
              color: C.muted,
              fontSize: 13,
              textAlign: "center",
              padding: 8,
            }}
          >
            কোনো পেন্ডিং পেমেন্ট নেই, আলহামদুলিল্লাহ।
          </div>
        )}
        {pending.map((p) => {
          const s = studentById(p.studentId);
          return (
            <div
              key={p.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 12px",
                borderRadius: 12,
                background: C.amberBg,
                marginBottom: 8,
                flexWrap: "wrap",
              }}
            >
              <div style={{ flex: 1, minWidth: 200 }}>
                <b style={{ fontSize: 14 }}>{p.studentName || s.name}</b> —{" "}
                {p.month} · ৳{bn(p.amount.toLocaleString("en"))}
                <div style={{ fontSize: 12, color: C.muted }}>
                  {p.method} · {fmtDate(p.date)}
                </div>
              </div>
              {p.shot && (
                <Btn sm kind="soft" onClick={() => setViewShot(p.shot)}>
                  🖼️ স্ক্রিনশট
                </Btn>
              )}
              <span
                style={{
                  background: "#fff",
                  color: "#a16207",
                  border: "1.5px solid #f0c355",
                  fontSize: 11.5,
                  fontWeight: 800,
                  padding: "4px 12px",
                  borderRadius: 99,
                }}
              >
                ⏳ পেন্ডিং
              </span>
              <Btn sm onClick={() => verify(p.id)}>
                ✔ ভেরিফাই করুন
              </Btn>
            </div>
          );
        })}
      </div>
      <div
        style={{
          ...S.card,
          marginBottom: 14,
          borderLeft: `4px solid ${C.red}`,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 8,
            marginBottom: 10,
          }}
        >
          <div style={{ fontWeight: 800 }}>
            📵 যাদের ফি বাকি — WhatsApp রিমাইন্ডার
          </div>
          {dueStudents.length > 0 && (
            <Btn sm kind="gold" onClick={sendAll}>
              📋 সবাইকে একসাথে (মেসেজ কপি)
            </Btn>
          )}
        </div>
        {!loading && dueStudents.length === 0 && (
          <div
            style={{
              color: C.muted,
              fontSize: 13,
              textAlign: "center",
              padding: 8,
            }}
          >
            কারো বকেয়া নেই, আলহামদুলিল্লাহ।
          </div>
        )}
        {dueStudents.map((s) => (
          <div
            key={s.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "10px 12px",
              borderRadius: 12,
              background: C.redBg,
              marginBottom: 8,
              flexWrap: "wrap",
            }}
          >
            <div style={{ flex: 1, minWidth: 200 }}>
              <b style={{ fontSize: 14 }}>{s.name}</b>
              <div style={{ fontSize: 12, color: C.muted }}>
                বকেয়া: {(s.dueMonths || []).join(", ")} — ৳
                {bn(
                  ((s.dueMonths || []).length * (s.fee || 0)).toLocaleString(
                    "en",
                  ),
                )}{" "}
                · অভিভাবক: {s.guardian || "—"}
              </div>
            </div>
            {s.phone ? (
              <a
                href={`https://wa.me/${s.phone}?text=${encodeURIComponent(waMsg(s).replace(/\\n/g, "\n"))}`}
                target="_blank"
                rel="noreferrer"
                style={{ textDecoration: "none" }}
              >
                <Btn sm style={{ background: "#25D366", color: "#fff" }}>
                  📱 WhatsApp রিমাইন্ডার
                </Btn>
              </a>
            ) : (
              <Tag color={C.muted} bg={C.cream}>
                নম্বর নেই
              </Tag>
            )}
            {/* ছুটি বা অন্য কারণে যাঁর কাছ থেকে ফি নেওয়া হবে না — এখান
                থেকেই মাস ধরে মওকুফ করা যায়। আগে এটা কেবল বিস্তারিত পাতায়
                ছিল, তাই এই তালিকা দেখতে দেখতে সরানো যেত না। */}
            {isDir(user) &&
              (s.dueMonths || []).map((m) => (
                <Btn
                  key={m}
                  sm
                  kind="soft"
                  title={`${m} মাসের বকেয়া মওকুফ করুন`}
                  onClick={() =>
                    askConfirm(
                      `${s.name}-এর "${m}" মাসের বকেয়া মওকুফ করবেন?\n\n` +
                        `ছুটিতে থাকলে বা অন্য কারণে ফি না নিলে এটা করুন। ` +
                        `বকেয়াটি তালিকা থেকে সরে যাবে।`,
                      () => waiveDueHere(s.id, m, "ছুটি/মওকুফ"),
                    )
                  }
                >
                  🏝️ {m} মওকুফ
                </Btn>
              ))}
          </div>
        ))}
      </div>
      <div style={{ ...S.card }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>
          ✅ ভেরিফাইড পেমেন্টসমূহ
        </div>
        <Table
          head={["স্টুডেন্ট", "মাস", "পরিমাণ", "মাধ্যম", "তারিখ", "স্ট্যাটাস", ""]}
          rows={verified.map((p) => {
            const s = studentById(p.studentId);
            return [
              p.studentName || s.name,
              p.month,
              `৳${bn(p.amount.toLocaleString("en"))}`,
              p.method,
              fmtDate(p.date),
              <Tag key="s">✅ ভেরিফাইড</Tag>,
              <Btn
                key="d"
                sm
                kind="danger"
                onClick={() =>
                  askConfirm(
                    `${p.studentName || s.name}-এর "${p.month}" মাসের এই পেমেন্ট রেকর্ডটা মুছে ফেলবেন? ভুল/ডুপ্লিকেট এন্ট্রি হলেই শুধু মুছুন — অন্য কোনো ভেরিফাইড পেমেন্ট না থাকলে ওই মাসের বকেয়া আবার ফিরে আসবে।`,
                    async () => {
                      try {
                        await api.deleteFee(p.id);
                        await loadData();
                        notice("✔ পেমেন্ট রেকর্ড মুছে ফেলা হয়েছে।");
                      } catch (e) {
                        notice(
                          "মুছতে ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"),
                        );
                      }
                    },
                  )
                }
              >
                🗑️ মুছুন
              </Btn>,
            ];
          })}
        />
      </div>
      {viewShot && (
        <Modal title="পেমেন্টের স্ক্রিনশট" onClose={() => setViewShot(null)}>
          <img
            src={viewShot.data}
            alt="স্ক্রিনশট"
            style={{
              width: "100%",
              borderRadius: 12,
              border: `1px solid #e5e9e5`,
            }}
          />
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ক্লাস রুটিন (সাপ্তাহিক) — পরিচালক/এডমিন বানাবেন, অটো সবার পোর্টালে ═══════════════ */
const DAY_BN = [
  "রবিবার",
  "সোমবার",
  "মঙ্গলবার",
  "বুধবার",
  "বৃহস্পতিবার",
  "শুক্রবার",
  "শনিবার",
]; // JS getDay() ক্রম
const DAY_EN = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
]; // শিক্ষার্থীর ইংরেজি ভিউয়ের জন্য — একই getDay() ক্রম
const WEEK_ORDER = [6, 0, 1, 2, 3, 4, 5]; // শনি → শুক্র

// বাংলাদেশ সময় (Asia/Dhaka, UTC+6, DST নেই — তাই হিসাব সরল)
const DHAKA_OFFSET_HOURS = 6;

// নির্দিষ্ট তারিখের (routine না, বাস্তব ক্লাস instance) দিন-সময় — বাংলাদেশ সময় ধরে
// সংরক্ষিত — কোনো টাইমজোনে কী তারিখ-সময় দাঁড়ায় তা বের করতে (তারিখও বদলাতে পারে)
const toZoneFullDateTime = (dateISO, timeStr, ianaZone) => {
  const [y, mo, da] = String(dateISO || "").split("-").map(Number);
  const [hh, mm] = String(timeStr || "00:00").split(":").map(Number);
  const utcMillis = Date.UTC(y, (mo || 1) - 1, da || 1, (hh || 0) - DHAKA_OFFSET_HOURS, mm || 0);
  const d = new Date(utcMillis);
  if (!ianaZone) {
    return {
      date: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`,
      time: `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`,
    };
  }
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: ianaZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(d);
  const get = (t) => parts.find((p) => p.type === t)?.value;
  let hour = get("hour");
  if (hour === "24") hour = "00";
  return {
    date: `${get("year")}-${get("month")}-${get("day")}`,
    time: `${hour}:${get("minute")}`,
  };
};
// পরিচালক/এডমিনের জন্য প্রায়ই-দরকারি দেশ/শহরের তালিকা (এই একাডেমির বেশিরভাগ
// প্রবাসী পরিবার যেসব দেশে থাকেন) — প্রয়োজনে সহজেই আরও যোগ করা যাবে
const COMMON_ZONES = [
  { label: "🇧🇩 বাংলাদেশ (Dhaka)", zone: "Asia/Dhaka" },
  { label: "🇬🇧 যুক্তরাজ্য (London)", zone: "Europe/London" },
  { label: "🇺🇸 আমেরিকা · পূর্ব (New York)", zone: "America/New_York" },
  { label: "🇺🇸 আমেরিকা · কেন্দ্রীয় (Chicago)", zone: "America/Chicago" },
  { label: "🇺🇸 আমেরিকা · পার্বত্য (Denver)", zone: "America/Denver" },
  { label: "🇺🇸 আমেরিকা · পশ্চিম (Los Angeles)", zone: "America/Los_Angeles" },
  { label: "🇨🇦 কানাডা · পূর্ব (Toronto)", zone: "America/Toronto" },
  { label: "🇦🇺 অস্ট্রেলিয়া (Sydney)", zone: "Australia/Sydney" },
  { label: "🇦🇪 সংযুক্ত আরব আমিরাত (Dubai)", zone: "Asia/Dubai" },
  { label: "🇸🇦 সৌদি আরব (Riyadh)", zone: "Asia/Riyadh" },
  { label: "🇶🇦 কাতার (Doha)", zone: "Asia/Qatar" },
  { label: "🇰🇼 কুয়েত", zone: "Asia/Kuwait" },
  { label: "🇲🇾 মালয়েশিয়া (Kuala Lumpur)", zone: "Asia/Kuala_Lumpur" },
  { label: "🇸🇬 সিঙ্গাপুর", zone: "Asia/Singapore" },
  { label: "🇩🇪 জার্মানি (Berlin)", zone: "Europe/Berlin" },
  { label: "🇫🇷 ফ্রান্স (Paris)", zone: "Europe/Paris" },
  { label: "🇮🇳 ভারত (Kolkata)", zone: "Asia/Kolkata" },
  { label: "🇵🇰 পাকিস্তান (Karachi)", zone: "Asia/Karachi" },
];

/* ছোট বাটন — স্টুডেন্টের নামের পাশে বসে, ক্লিক করলে মন্তব্য লেখার পপআপ (Modal)
   খোলে (ইংরেজিতে লিখলে স্টুডেন্ট পোর্টালে সরাসরি সেভাবেই দেখাবে — আলাদা কোনো
   অনুবাদ হয় না) */
function RemarkBox({ studentId, studentName }) {
  const [open, setOpen] = useState(false);
  const [list, setList] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => {
    api.studentRemarks(studentId).then(setList).catch(() => {});
  };
  useEffect(() => {
    if (open) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);
  const submit = async () => {
    if (!text.trim()) return;
    setBusy(true);
    try {
      await api.addStudentRemark(studentId, text.trim());
      setText("");
      load();
    } catch (e) {
      notice("মন্তব্য যোগ করতে ব্যর্থ — " + (e?.data?.error || e?.message || "যাচাই করুন"));
    }
    setBusy(false);
  };
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        title="মন্তব্য"
        style={{
          border: "none",
          background: "none",
          cursor: "pointer",
          fontSize: 13,
          padding: 0,
          lineHeight: 1,
        }}
      >
        💬
      </button>
      {open && (
        <Modal title={`💬 মন্তব্য — ${studentName}`} onClose={() => setOpen(false)}>
          {list.length > 0 && (
            <div style={{ marginBottom: 10, display: "grid", gap: 6 }}>
              {list.map((r) => (
                <div
                  key={r.id}
                  style={{
                    fontSize: 12.5,
                    padding: "8px 10px",
                    background: C.cream,
                    borderRadius: 8,
                  }}
                >
                  <div style={{ color: C.muted, marginBottom: 3, fontSize: 11.5 }}>
                    {r.teacher_name} · {fmtDate(r.created_at)}
                  </div>
                  {r.text}
                </div>
              ))}
            </div>
          )}
          <label style={S.label}>নতুন মন্তব্য</label>
          <textarea
            rows={3}
            style={{ ...S.input, resize: "vertical" }}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="স্টুডেন্টের ব্যাপারে মন্তব্য লিখুন (ইংরেজিতে লিখুন — স্টুডেন্ট পোর্টালে সরাসরি এভাবেই দেখাবে)"
          />
          <Btn
            kind="gold"
            style={{ marginTop: 10, width: "100%", justifyContent: "center", opacity: busy ? 0.6 : 1 }}
            onClick={submit}
          >
            {busy ? "⏳ সেভ হচ্ছে…" : "+ মন্তব্য যোগ করুন"}
          </Btn>
        </Modal>
      )}
    </>
  );
}

function RoutineView({ db, setDb, courses, user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const canEdit = isAdm(user);
  const [show, setShow] = usePersistedState("rt_show", false);
  const blankR = () => ({
    courseId: courses[0]?.id,
    days: [],
    time: "17:00",
    dur: 60,
    zoom: "https://zoom.us/j/8801402499027",
    zoom2: "", // রিজয়েন লিংক (ঐচ্ছিক) — উস্তাদ+স্টুডেন্ট প্রথম লিংকে একবার জয়েন করার পর এই লিংকেই আবার জয়েন হবে
    kind: "নিয়মিত ক্লাস",
    teacherId: courses[0]?.teacherId,
    studentIds: [],
    studentSchedule: {}, // { [studentId]: { days: [0..6], time: "HH:MM" } } — শিক্ষার্থীর নিজের সময়ে ম্যানুয়াল ওভাররাইড (ঐচ্ছিক)
  });
  const [f, setF] = usePersistedState("rt_f", blankR);
  const [editId, setEditId] = usePersistedState("rt_editId", null);
  const [apiRoutines, setApiRoutines] = useState(null); // null হলে mock db.routine
  const [routinesLoading, setRoutinesLoading] = useState(true);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [genBusy, setGenBusy] = useState(false);
  // এক ক্লিকে সব রুটিনের আগামী ৭ দিনের ক্লাস তৈরি → উস্তাদ/শিক্ষার্থীর পোর্টালে
  const genClassesNow = async () => {
    setGenBusy(true);
    try {
      const r = await api.generateRoutineClasses();
      notice(
        `✔ ${bn(r?.created || 0)}টি নতুন ক্লাস তৈরি হয়েছে — উস্তাদ ও শিক্ষার্থীর পোর্টালে (রিফ্রেশ করলে) দেখা যাবে।`,
      );
    } catch {
      notice("ক্লাস তৈরি ব্যর্থ — সার্ভার সংযোগ যাচাই করুন।");
    } finally {
      setGenBusy(false);
    }
  };
  const loadRoutines = async () => {
    try {
      setApiRoutines((await api.routines()).map(adaptRoutine));
    } catch {
      setApiRoutines(null);
    } finally {
      // ব্যর্থ হলেও লোডিং শেষ — নইলে "রুটিন লোড হচ্ছে" চিরকাল আটকে থাকত
      setRoutinesLoading(false);
    }
  };
  useEffect(() => {
    loadRoutines();
  }, [user?.id]);
  useEffect(() => {
    if (!canEdit) return;
    api
      .allTeachers()
      .then((d) => setTeachers(d.map(adaptPerson)))
      .catch(() => setTeachers([]));
    api
      .allStudents()
      .then((d) => setStudents(d.map(adaptPerson)))
      .catch(() => setStudents([]));
  }, [user?.id]);
  const usingApi = apiRoutines !== null;
  // উস্তাদ তালিকা: api.allTeachers + কোর্সের উস্তাদ (dedupe) — কোনোটা ব্যর্থ হলেও ড্রপডাউন খালি হয় না
  const teacherList = (() => {
    const m = new Map();
    teachers.forEach((t) => t.id != null && m.set(String(t.id), t));
    (courses || []).forEach((c) => {
      if (c.teacherId != null && !m.has(String(c.teacherId)))
        m.set(String(c.teacherId), {
          id: c.teacherId,
          name: c.teacherName || "উস্তাদ",
          sub: "",
        });
    });
    return [...m.values()];
  })();
  // মডাল খুললে/উস্তাদ তালিকা এলে teacherId খালি থাকলে আসল উস্তাদ বসিয়ে দিই
  // (নইলে ড্রপডাউনে দেখা গেলেও state খালি থেকে "teacher আবশ্যক" error হতো)
  useEffect(() => {
    if (!show || !teacherList.length) return;
    const valid = teacherList.some((t) => String(t.id) === String(f.teacherId));
    if (!valid) {
      const courseTeacher = courseById(courses, f.courseId)?.teacherId;
      const pick = teacherList.some((t) => String(t.id) === String(courseTeacher))
        ? courseTeacher
        : teacherList[0]?.id;
      if (pick) setF((prev) => ({ ...prev, teacherId: pick }));
    }
  }, [show, teachers]);
  const nameOf = (id) =>
    (
      teachers.find((t) => t.id === id) ||
      students.find((s) => s.id === id) ||
      userById(id)
    ).name || "—";
  const plusDays = (iso, n) => {
    const d = new Date(iso + "T00:00:00");
    d.setDate(d.getDate() + n);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };
  const toggleDay = (i) =>
    setF({
      ...f,
      days: f.days.includes(i) ? f.days.filter((d) => d !== i) : [...f.days, i],
    });
  const nextDate = (wd) => {
    const d = new Date();
    const diff = (wd - d.getDay() + 7) % 7;
    d.setDate(d.getDate() + diff);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };
  const genClasses = (rid, ff, students) =>
    ff.days.flatMap((wd) =>
      [0, 7].map((off) => ({
        // এ সপ্তাহ + পরের সপ্তাহ — স্থায়ী রুটিনের ক্লাস
        id: uid(),
        routineId: rid,
        courseId: ff.courseId,
        date: plusDays(nextDate(wd), off),
        time: ff.time,
        dur: +ff.dur,
        zoom: ff.zoom,
        status: "upcoming",
        lectureNo: 1,
        fromRoutine: true,
        kind: "নিয়মিত ক্লাস",
        teacherId: ff.teacherId,
        studentIds: students,
      })),
    );
  const saveRoutine = async (students) => {
    // সবসময় সরাসরি API-তে সেভ (backend ধীরে লোড হলেও) — লোকালে রাখলে "আসে-যায়" হতো ও পোর্টালে যেত না
    try {
      if (editId) await api.updateRoutine(editId, routinePayload(f, students, f.studentSchedule));
      else await api.createRoutine(routinePayload(f, students, f.studentSchedule));
      await loadRoutines();
      setShow(false);
      setEditId(null);
      setF(blankR());
      notice(
        editId
          ? "✔ রুটিন আপডেট হয়েছে"
          : "✔ স্থায়ী রুটিন তৈরি হয়েছে — ক্লাস পোর্টালে যোগ হয়েছে",
      );
    } catch (e) {
      const detail = e?.data
        ? Object.entries(e.data)
            .map(([k, v]) => `${k}: ${v}`)
            .join(" · ")
        : e?.message || "যাচাই করুন";
      notice("রুটিন সংরক্ষণ ব্যর্থ — " + detail);
    }
  };
  // একই উস্তাদের জন্য একই বারে সময়-ওভারল্যাপ করে এমন অন্য কোনো (সক্রিয়) রুটিন
  // আছে কিনা — থাকলে ডাবল-বুকিং হয়ে যাচ্ছে, নিঃশব্দে হতে দেওয়া ঠিক না
  const timeToMin = (t) => {
    const [h, m] = String(t || "0:0").split(":").map(Number);
    return h * 60 + (m || 0);
  };
  const findTeacherConflicts = () => {
    const newStart = timeToMin(f.time);
    const newEnd = newStart + (+f.dur || 0);
    return (apiRoutines || []).filter((r) => {
      if (editId && r.id === editId) return false; // নিজেকে বাদ
      if (String(r.teacherId) !== String(f.teacherId)) return false;
      if (!(r.days || []).some((d) => f.days.includes(d))) return false;
      const exStart = timeToMin(r.time);
      const exEnd = exStart + (+r.dur || 0);
      return newStart < exEnd && exStart < newEnd; // সময়সীমা ওভারল্যাপ
    });
  };
  const add = () => {
    if (!f.days.length) return notice("সপ্তাহের অন্তত একটি দিন বাছাই করুন।");
    if (!f.teacherId)
      return notice("উস্তাদ/উস্তাদা বাছাই করুন — ড্রপডাউন থেকে একজন নির্বাচন করুন।");
    const c = courseById(courses, f.courseId);
    const afterConflictCheck = () => {
      if (!f.studentIds.length) {
        // কাউকে না বাছলে আগে চুপচাপ পুরো কোর্সের সবাইকে যুক্ত করে দিত — ভুলবশত
        // অপ্রাসঙ্গিক স্টুডেন্ট রুটিনে ঢুকে যাওয়ার কারণ ছিল এটাই; এখন স্পষ্ট
        // নিশ্চিতকরণ ছাড়া এগোবে না
        const whole = c.studentIds || [];
        const names = whole.map((sid) => nameOf(sid)).join(", ") || "কেউ নেই";
        askConfirm(
          `আপনি কোনো নির্দিষ্ট স্টুডেন্ট বাছাই করেননি — তাই "${c.name || "এই কোর্সের"}" কোর্সে ভর্তি সবাই (${names}) এই রুটিনে যুক্ত হয়ে যাবে। এগিয়ে যাবেন?`,
          () => saveRoutine(whole),
        );
        return;
      }
      saveRoutine(f.studentIds);
    };
    const conflicts = findTeacherConflicts();
    if (conflicts.length) {
      const details = conflicts
        .map(
          (r) =>
            `"${courseById(courses, r.courseId)?.name || r.courseName || "?"}" (${(r.days || [])
              .map((d) => DAY_BN[d])
              .join(", ")} ${r.time})`,
        )
        .join(" · ");
      askConfirm(
        `⚠️ ${nameOf(f.teacherId)} এই বারে-সময়ে ইতিমধ্যে অন্য রুটিনে ব্যস্ত: ${details} — একই সময়ে দুইটা ক্লাসে "বুক" হয়ে যাবেন। তবুও এগিয়ে যাবেন?`,
        afterConflictCheck,
      );
      return;
    }
    afterConflictCheck();
  };
  const del = async (id) => {
    try {
      await api.deleteRoutine(id);
      await loadRoutines();
    } catch (e) {
      notice("রুটিন মুছতে ব্যর্থ — " + (e?.message || "সার্ভার যাচাই করুন"));
    }
  };
  const visible = apiRoutines || [];
  // প্রতিটা রুটিন বাংলাদেশ-সময়ে সংরক্ষিত বার-সময় অনুযায়ীই দিন ধরে গ্রুপ করা হয় —
  // ডিভাইসের টাইমজোন থেকে অটো-হিসাব আর করা হয় না (নির্ভরযোগ্য ছিল না)। স্টুডেন্ট
  // বিদেশে থাকলে, রুটিন তৈরি/এডিটের সময় পরিচালক তার জন্য আলাদাভাবে ম্যানুয়ালি
  // বার-সময় বসিয়ে দিলে (studentSchedule) সেই স্টুডেন্ট এখানে সেটাই দেখবে।
  // রুটিন সবসময় তার আসল বাংলাদেশ-সময়ের বারেই (r.days) দেখানো হয় — আসল ক্লাস
  // (ClassSession) ঠিক ওই বারেই তৈরি হয়, তাই ভিন্ন বারে সরিয়ে দেখালে স্টুডেন্ট
  // আসল ক্লাসের দিনে "রুটিনে ক্লাস নেই" দেখে বিভ্রান্ত হতেন (আগে এমনটাই হচ্ছিল)।
  // স্টুডেন্টের নিজের সময়ে বসানো ওভাররাইড থাকলে সেটা একই এন্ট্রির পাশে শুধু
  // তথ্য হিসেবে দেখানো হয় — কোনো এন্ট্রি সরে যায় না
  const localSchedule = {};
  visible.forEach((r) => {
    const override =
      user.role === "student" ? r.studentSchedule?.[String(user.id)] : null;
    (r.days || []).forEach((d) => {
      if (!localSchedule[d]) localSchedule[d] = [];
      localSchedule[d].push({ ...r, localTime: r.time, myOverride: override });
    });
  });
  return (
    <Section
      title={T("ক্লাস রুটিন (স্থায়ী সাপ্তাহিক)", "Class Routine (Fixed Weekly)")}
      sub={
        canEdit
          ? "কোন স্টুডেন্ট কোন উস্তাদের কাছে কোন বারে কোন সময়ে কোন কোর্সে পড়বে — সব সময়ের জন্য; এডিট কেবল এডমিনের হাতে · সময়/দিন বাংলাদেশ সময় অনুযায়ী দেখানো হচ্ছে"
          : T(
              "আপনার স্থায়ী সাপ্তাহিক ক্লাসের সময়সূচি — জয়েন অপশন অটো আসবে",
              "Your fixed weekly class schedule — the join option will appear automatically at the right time",
            )
      }
      action={
        canEdit && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <Btn
              kind="soft"
              onClick={genClassesNow}
              style={{ opacity: genBusy ? 0.6 : 1 }}
            >
              {genBusy ? "⏳ তৈরি হচ্ছে…" : "🔄 সব রুটিনের ক্লাস তৈরি করুন"}
            </Btn>
            <Btn onClick={() => setShow(true)}>+ রুটিন তৈরি করুন</Btn>
          </div>
        )
      }
    >
      <TeacherWiseBoard db={db} setDb={setDb} user={user} />
      {routinesLoading && (
        <Loader text={T("রুটিন লোড হচ্ছে", "Loading routine")} />
      )}
      {/* রুটিন লোড হওয়ার আগে সাত বারের ঘরে "— ক্লাস নেই —" দেখাত, যা ভুল ধারণা
          দিত — এখন লোড শেষ হলেই সপ্তাহের ছকটা দেখানো হয় */}
      <div style={{ display: routinesLoading ? "none" : "grid", gap: 10 }}>
        {WEEK_ORDER.map((wd) => {
          const items = localSchedule[wd] || [];
          return (
            <div
              key={wd}
              style={{
                ...S.card,
                padding: 14,
                borderLeft: `4px solid ${items.length ? C.emerald : C.line}`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  flexWrap: "wrap",
                }}
              >
                <b
                  style={{
                    width: 110,
                    fontSize: 14,
                    color: items.length ? C.emerald : C.muted,
                  }}
                >
                  {T(DAY_BN[wd], DAY_EN[wd])}
                </b>
                <div
                  style={{ flex: 1, display: "flex", gap: 8, flexWrap: "wrap" }}
                >
                  {items.length === 0 && (
                    <span style={{ fontSize: 12.5, color: C.muted }}>
                      {T("— ক্লাস নেই —", "— No class —")}
                    </span>
                  )}
                  {items.map((r) => {
                    const c = courseById(courses, r.courseId);
                    const studNames =
                      r.studentNames && r.studentNames.length
                        ? r.studentNames
                        : (r.studentIds || []).map((s) => nameOf(s));
                    return (
                      <span
                        key={r.id}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: 8,
                          background: C.greenBg,
                          border: `1px solid ${C.line}`,
                          borderRadius: 10,
                          padding: "7px 12px",
                          fontSize: 12.5,
                        }}
                      >
                        <b style={{ color: c.color || C.emerald }}>
                          {c.name || r.courseName}
                        </b>{" "}
                        {r.kind && r.kind !== "নিয়মিত ক্লাস" && (
                          <Tag color={C.red} bg={C.redBg}>
                            {r.kind}
                          </Tag>
                        )}{" "}
                        🕐 {r.localTime} · {T(`${bn(r.dur)} মি`, `${r.dur} min`)} ·{" "}
                        {r.teacherName || nameOf(r.teacherId || c.teacherId)}
                        {r.myOverride &&
                          (r.myOverride.time || r.myOverride.days?.length > 0) && (
                            <span style={{ color: C.gold }}>
                              {" "}
                              · 🌍{" "}
                              {T("আপনার সময়ে", "your time")}:{" "}
                              {(r.myOverride.days || [])
                                .map((d) => T(DAY_BN[d], DAY_EN[d]))
                                .join("/")}{" "}
                              {r.myOverride.time}
                            </span>
                          )}
                        {canEdit && studNames.length > 0 && (
                          <span style={{ color: C.muted }}>
                            {" "}
                            · 👥{" "}
                            {studNames.map((n) => n.split(" ")[0]).join(", ")}
                          </span>
                        )}
                        {canEdit && (
                          <button
                            title="এডিট — কেবল এডমিন"
                            onClick={() => {
                              setF({
                                courseId: r.courseId,
                                days: [...r.days],
                                time: r.time,
                                dur: r.dur,
                                zoom: r.zoom,
                                zoom2: r.zoom2 || "",
                                kind: "নিয়মিত ক্লাস",
                                teacherId: r.teacherId,
                                studentIds: r.studentIds || [],
                                studentSchedule: r.studentSchedule || {},
                              });
                              setEditId(r.id);
                              setShow(true);
                            }}
                            style={{
                              border: "none",
                              background: "transparent",
                              cursor: "pointer",
                            }}
                          >
                            ✏️
                          </button>
                        )}
                        {canEdit && (
                          <button
                            onClick={() => del(r.id)}
                            style={{
                              border: "none",
                              background: "transparent",
                              color: C.red,
                              cursor: "pointer",
                              fontWeight: 800,
                            }}
                          >
                            ✕
                          </button>
                        )}
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
        <Modal
          title={
            editId
              ? "✏️ রুটিন এডিট করুন (কেবল এডমিন)"
              : "স্থায়ী সাপ্তাহিক রুটিন তৈরি করুন"
          }
          onClose={() => {
            setShow(false);
            setEditId(null);
            setF(blankR());
          }}
          wide
        >
          <div
            style={{
              padding: "9px 12px",
              borderRadius: 10,
              background: C.greenBg,
              fontSize: 12,
              color: C.emerald,
              marginBottom: 12,
            }}
          >
            💡 কোন স্টুডেন্ট কোন উস্তাদের কাছে সপ্তাহের কোন বারে, কোন সময়ে, কোন
            কোর্সে পড়বে — সব সময়ের জন্য রুটিন। ছুটে যাওয়া ক্লাসের
            মেকআপ/সাপোর্টের জন্য "ক্লাস ও জুম জয়েন" পেজের শিডিউল ব্যবহার করুন।
          </div>
          <div>
            <label style={S.label}>কোর্স</label>
            <select
              style={S.input}
              value={f.courseId}
              onChange={(e) => {
                const c = courseById(courses, e.target.value);
                setF({
                  ...f,
                  courseId: e.target.value,
                  teacherId: c.teacherId || f.teacherId,
                });
              }}
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {c.studentIds.length}জন শিক্ষার্থী
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>উস্তাদ/উস্তাদা — কার কাছে পড়বে</label>
            <select
              style={S.input}
              value={f.teacherId || ""}
              onChange={(e) => setF({ ...f, teacherId: e.target.value })}
            >
              {teacherList.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} {t.sub ? `(${t.sub})` : ""}
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>
              শিক্ষার্থী বাছাই করুন — এক এক করে ({bn(f.studentIds.length)} জন
              নির্বাচিত; কাউকে না বাছলে কোর্সের সবাই)
            </label>
            <StudentPicker
              selected={f.studentIds}
              people={students}
              onToggle={(id) =>
                setF({
                  ...f,
                  studentIds: f.studentIds.includes(id)
                    ? f.studentIds.filter((x) => x !== id)
                    : [...f.studentIds, id],
                })
              }
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>সপ্তাহের কোন কোন দিন</label>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {WEEK_ORDER.map((wd) => (
                <button
                  key={wd}
                  onClick={() => toggleDay(wd)}
                  style={{
                    padding: "8px 12px",
                    borderRadius: 99,
                    cursor: "pointer",
                    fontFamily: "inherit",
                    fontWeight: 700,
                    fontSize: 12.5,
                    border: `2px solid ${f.days.includes(wd) ? C.emerald : C.line}`,
                    background: f.days.includes(wd) ? C.greenBg : "#fff",
                    color: f.days.includes(wd) ? C.emerald : C.text,
                  }}
                >
                  {DAY_BN[wd]}
                </button>
              ))}
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
              marginTop: 10,
            }}
          >
            <div>
              <label style={S.label}>সময় (বাংলাদেশ সময় 🇧🇩)</label>
              <input
                type="time"
                style={S.input}
                value={f.time}
                onChange={(e) => setF({ ...f, time: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>সময়কাল (মিনিট)</label>
              <input
                type="number"
                style={S.input}
                value={f.dur}
                onChange={(e) => setF({ ...f, dur: e.target.value })}
              />
            </div>
          </div>
          {/* ছাত্র বিদেশে থাকলে তার কাছে এই ক্লাসটা অন্য বার/সময়ে পড়তে পারে —
              টাইমজোন হিসাব-নিকাশ অটোমেটিক না করে, প্রতিটি শিক্ষার্থীর জন্য
              আলাদাভাবে ম্যানুয়ালি বার+সময় বসিয়ে দেওয়া যায় (না দিলে উপরের
              বাংলাদেশ-সময়ের বার-সময়ই তার পোর্টালেও দেখাবে) */}
          {f.studentIds.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <label style={S.label}>
                🎓 শিক্ষার্থীদের নিজস্ব সময় (ঐচ্ছিক — বিদেশে থাকা কারো জন্য আলাদা বার/সময়)
              </label>
              <div style={{ display: "grid", gap: 8 }}>
                {f.studentIds.map((sid) => {
                  const sch = f.studentSchedule[sid] || { days: [], time: "" };
                  const custom = sch.days.length > 0 || !!sch.time;
                  const setSch = (patch) =>
                    setF({
                      ...f,
                      studentSchedule: {
                        ...f.studentSchedule,
                        [sid]: { ...sch, ...patch },
                      },
                    });
                  return (
                    <div
                      key={sid}
                      style={{
                        padding: "8px 10px",
                        borderRadius: 10,
                        border: `1px solid ${C.line}`,
                      }}
                    >
                      <label
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                          fontSize: 13,
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={custom}
                          onChange={(e) =>
                            setSch(
                              e.target.checked
                                ? { days: [...f.days], time: f.time }
                                : { days: [], time: "" },
                            )
                          }
                        />
                        {nameOf(sid)}{" "}
                        <span style={{ fontWeight: 400, color: C.muted }}>
                          {custom
                            ? "— আলাদা সময় সেট করা"
                            : "— বাংলাদেশ সময়ের বারেই দেখবে"}
                        </span>
                      </label>
                      {custom && (
                        <div style={{ marginTop: 8 }}>
                          <div
                            style={{ display: "flex", gap: 6, flexWrap: "wrap" }}
                          >
                            {WEEK_ORDER.map((wd) => (
                              <button
                                key={wd}
                                type="button"
                                onClick={() =>
                                  setSch({
                                    days: sch.days.includes(wd)
                                      ? sch.days.filter((x) => x !== wd)
                                      : [...sch.days, wd],
                                  })
                                }
                                style={{
                                  padding: "5px 10px",
                                  borderRadius: 99,
                                  cursor: "pointer",
                                  fontFamily: "inherit",
                                  fontWeight: 700,
                                  fontSize: 11.5,
                                  border: `2px solid ${sch.days.includes(wd) ? C.emerald : C.line}`,
                                  background: sch.days.includes(wd) ? C.greenBg : "#fff",
                                  color: sch.days.includes(wd) ? C.emerald : C.text,
                                }}
                              >
                                {DAY_BN[wd]}
                              </button>
                            ))}
                            <input
                              type="time"
                              style={{ ...S.input, width: 130 }}
                              value={sch.time}
                              onChange={(e) => setSch({ time: e.target.value })}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>১ম জুম লিংক</label>
            <input
              style={S.input}
              value={f.zoom}
              onChange={(e) => setF({ ...f, zoom: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>
              ২য় জুম লিংক (রিজয়েন — ঐচ্ছিক)
            </label>
            <input
              style={S.input}
              value={f.zoom2}
              onChange={(e) => setF({ ...f, zoom2: e.target.value })}
              placeholder="উস্তাদ+স্টুডেন্ট ১ম লিংকে একবার জয়েন করার পর, আবার জয়েন করতে চাইলে এই লিংক ব্যবহার হবে"
            />
          </div>
          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
            onClick={add}
          >
            {editId
              ? "✏️ রুটিন আপডেট করুন"
              : "রুটিন তৈরি করুন — স্টুডেন্ট ও উস্তাদের পোর্টালে অটো যোগ হবে"}
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ছুটির আবেদন — দরখাস্ত ফরমেট; এডমিন ফরওয়ার্ড, মঞ্জুর কেবল পরিচালক ═══════════════ */
const LEAVE_TYPE_EN = {
  অসুস্থতা: "Sickness",
  সফর: "Travel",
  "পারিবারিক প্রয়োজন": "Family Reasons",
  পরীক্ষা: "Exam",
  অন্যান্য: "Other",
};
function LeaveView({ db, setDb, user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [show, setShow] = usePersistedState("leave_show", false);
  const [f, setF] = usePersistedState("leave_f", {
    type: "অসুস্থতা",
    from: todayISO(),
    to: todayISO(),
    reason: "",
  });
  const [leaves, setLeaves] = useState(db.leaves || []);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে
  const canApply = user.role !== "director";

  const adaptLeave = (l) => ({
    id: l.id,
    userId: l.applicant || l.userId,
    applicant_name: l.applicant_name || userById(l.userId)?.name,
    applicant_role: l.applicant_role || userById(l.userId)?.role,
    type: l.leave_type || l.type,
    from: l.from_date || l.from,
    to: l.to_date || l.to,
    reason: l.reason,
    date: l.applied_at || l.date,
    status: l.status,
  });
  const loadData = async () => {
    try {
      setLeaves((await api.leaves()).map(adaptLeave));
    } catch {
      setLeaves(db.leaves || []);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const list =
    user.role === "student" || user.role === "teacher"
      ? leaves.filter((l) => String(l.userId) === String(user.id))
      : leaves;
  const submit = async () => {
    if (!f.reason.trim())
      return notice(T("ছুটির কারণ লিখুন।", "Please write the reason for leave."));
    try {
      await api.applyLeave({
        leave_type: f.type,
        from_date: f.from,
        to_date: f.to,
        reason: f.reason,
      });
      await loadData();
      notice(T("✔ ছুটির আবেদন জমা হয়েছে।", "✔ Leave application submitted."));
    } catch (e) {
      notice(
        T(
          "আবেদন জমা দিতে ব্যর্থ — ",
          "Failed to submit application — ",
        ) + (e?.data?.error || e?.message || T("সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন", "Check your connection and try again")),
      );
      return;
    }
    setShow(false);
    setF({ type: "অসুস্থতা", from: todayISO(), to: todayISO(), reason: "" });
  };
  const forward = async (l) => {
    try {
      await api.forwardLeave(l.id);
      await loadData();
      notice("✔ ছুটির আবেদনটি পরিচালকের কাছে পাঠানো হয়েছে।");
    } catch (e) {
      notice(
        "আবেদন পাঠাতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const decide = async (l, ok) => {
    try {
      await api.decideLeave(l.id, ok);
      await loadData();
      notice(ok ? "✔ ছুটি মঞ্জুর করা হয়েছে।" : "✔ ছুটি নামঞ্জুর করা হয়েছে।");
    } catch (e) {
      notice(
        "সিদ্ধান্ত সেভ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
  };
  const stTag = (s) =>
    s === "pending_admin" ? (
      <Tag color={"#a16207"} bg={C.amberBg}>
        {T("⏳ এডমিনের কাছে", "⏳ With Admin")}
      </Tag>
    ) : s === "forwarded" ? (
      <Tag color={C.blue} bg={C.blueBg}>
        {T("📤 পরিচালকের কাছে", "📤 With Director")}
      </Tag>
    ) : s === "approved" ? (
      <Tag>{T("মঞ্জুর ✔", "Approved ✔")}</Tag>
    ) : (
      <Tag color={C.red} bg={C.redBg}>
        {T("নামঞ্জুর ✘", "Rejected ✘")}
      </Tag>
    );
  return (
    <Section
      title={T("ছুটির আবেদন", "Leave Application")}
      sub={T(
        "দরখাস্ত ফরম পূরণ করে জমা দিন — এডমিন দেখে পরিচালক বরাবর পাঠাবেন, মঞ্জুরের ক্ষমতা কেবল পরিচালকের",
        "Fill out and submit the application form — the admin will forward it to the director, who alone can approve it",
      )}
      action={
        canApply && (
          <Btn onClick={() => setShow(true)}>
            {T("✍️ ছুটির দরখাস্ত লিখুন", "✍️ Write Leave Application")}
          </Btn>
        )
      }
    >
      <div style={{ display: "grid", gap: 10 }}>
        {loading && <Loader text={T("লোড হচ্ছে", "Loading")} />}
        {!loading && list.length === 0 && (
          <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>
            {T("কোনো ছুটির আবেদন নেই।", "No leave applications.")}
          </div>
        )}
        {list.map((l) => {
          const apName = l.applicant_name || userById(l.userId)?.name || "—";
          const apRole =
            l.applicant_role || userById(l.userId)?.role || "student";
          return (
            <div
              key={l.id}
              style={{
                ...S.card,
                padding: 0,
                overflow: "hidden",
                borderLeft: `4px solid ${l.status === "approved" ? C.green : l.status === "rejected" ? C.red : C.gold}`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "12px 16px",
                  flexWrap: "wrap",
                }}
              >
                <div style={{ flex: 1, minWidth: 200 }}>
                  <b style={{ fontSize: 14 }}>{apName}</b>{" "}
                  <Tag color={C.blue} bg={C.blueBg}>
                    {T(
                      apRole === "student"
                        ? "স্টুডেন্ট"
                        : apRole === "teacher"
                          ? "উস্তাদ/উস্তাদা"
                          : "এডমিন",
                      apRole === "student"
                        ? "Student"
                        : apRole === "teacher"
                          ? "Teacher"
                          : "Admin",
                    )}
                  </Tag>
                  <div style={{ fontSize: 12.5, color: C.muted }}>
                    {T(l.type, LEAVE_TYPE_EN[l.type] || l.type)} ·{" "}
                    {fmtDate(l.from)} — {fmtDate(l.to)} ·{" "}
                    {T("আবেদন", "Applied")}: {fmtDate(l.date)}
                  </div>
                </div>
                {stTag(l.status)}
                {user.role === "admin" && l.status === "pending_admin" && (
                  <Btn sm kind="gold" onClick={() => forward(l)}>
                    📤 পরিচালক বরাবর পাঠান
                  </Btn>
                )}
                {isDir(user) &&
                  (l.status === "pending_admin" ||
                    l.status === "forwarded") && (
                    <span style={{ display: "flex", gap: 6 }}>
                      <Btn sm onClick={() => decide(l, true)}>
                        ✔ মঞ্জুর
                      </Btn>
                      <Btn sm kind="danger" onClick={() => decide(l, false)}>
                        ✘ নামঞ্জুর
                      </Btn>
                    </span>
                  )}
              </div>
              {/* দরখাস্ত ফরমেট */}
              <div
                style={{
                  borderTop: `1px dashed ${C.line}`,
                  background: "#fffdf8",
                  padding: "14px 18px",
                  fontSize: 13,
                  lineHeight: 1.8,
                }}
              >
                {user.role === "student" ? (
                  <>
                    <div>Date: {fmtDate(l.date)}</div>
                    <div>
                      To,
                      <br />
                      The Director,
                      <br />
                      Tarbiyatul Quran Academy
                    </div>
                    <div style={{ margin: "6px 0" }}>
                      <b>Subject: Application for Leave ({LEAVE_TYPE_EN[l.type] || l.type}).</b>
                    </div>
                    <div>
                      Dear Sir,
                      <br />
                      I am {apName}, a {apRole === "student" ? "student" : apRole === "teacher" ? "teacher" : "admin"}{" "}
                      of your institution. {l.reason} In light of this, I
                      kindly request you to grant me leave from{" "}
                      {fmtDate(l.from)} to {fmtDate(l.to)}.
                    </div>
                    <div style={{ marginTop: 6 }}>
                      Sincerely,
                      <br />
                      <b>{apName}</b>
                    </div>
                  </>
                ) : (
                  <>
                    <div>তারিখ: {fmtDate(l.date)}</div>
                    <div>
                      বরাবর,
                      <br />
                      পরিচালক মহোদয়,
                      <br />
                      তারবিয়াতুল কুরআন একাডেমি
                    </div>
                    <div style={{ margin: "6px 0" }}>
                      <b>বিষয়: ছুটির আবেদন ({l.type})।</b>
                    </div>
                    <div>
                      জনাব,
                      <br />
                      সবিনয় নিবেদন এই যে, আমি {apName}, আপনার প্রতিষ্ঠানের একজন{" "}
                      {apRole === "student"
                        ? "শিক্ষার্থী"
                        : apRole === "teacher"
                          ? "শিক্ষক"
                          : "এডমিন"}
                      । {l.reason} এমতাবস্থায়, {fmtDate(l.from)} থেকে{" "}
                      {fmtDate(l.to)} পর্যন্ত ছুটি মঞ্জুর করতে আপনার সদয় মর্জি হয়।
                    </div>
                    <div style={{ marginTop: 6 }}>
                      নিবেদক,
                      <br />
                      <b>{apName}</b>
                    </div>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {show && (
        <Modal
          title={T("✍️ ছুটির দরখাস্ত", "✍️ Leave Application")}
          onClose={() => setShow(false)}
        >
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}
          >
            <div>
              <label style={S.label}>{T("ছুটির ধরন", "Leave Type")}</label>
              <select
                style={S.input}
                value={f.type}
                onChange={(e) => setF({ ...f, type: e.target.value })}
              >
                {Object.keys(LEAVE_TYPE_EN).map((k) => (
                  <option key={k} value={k}>
                    {T(k, LEAVE_TYPE_EN[k])}
                  </option>
                ))}
              </select>
            </div>
            <div></div>
            <div>
              <label style={S.label}>{T("কবে থেকে", "From")}</label>
              <input
                type="date"
                style={S.input}
                value={f.from}
                onChange={(e) => setF({ ...f, from: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>{T("কবে পর্যন্ত", "To")}</label>
              <input
                type="date"
                style={S.input}
                value={f.to}
                onChange={(e) => setF({ ...f, to: e.target.value })}
              />
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>{T("কারণ / বিবরণ", "Reason / Details")}</label>
            <textarea
              rows={3}
              style={{ ...S.input, resize: "vertical" }}
              value={f.reason}
              onChange={(e) => setF({ ...f, reason: e.target.value })}
              placeholder={T(
                "যেমন: পারিবারিক প্রয়োজনে গ্রামের বাড়ি যেতে হবে...",
                "e.g. I need to visit my hometown for a family matter...",
              )}
            />
          </div>
          <div
            style={{
              marginTop: 12,
              borderRadius: 12,
              background: "#fffdf8",
              border: `1px dashed ${C.goldL}`,
              padding: "12px 14px",
              fontSize: 12.5,
              lineHeight: 1.8,
            }}
          >
            <div style={{ fontWeight: 800, marginBottom: 4, color: C.gold }}>
              {T("দরখাস্তের প্রিভিউ:", "Application Preview:")}
            </div>
            {user.role === "student" ? (
              <>
                To, The Director, Tarbiyatul Quran Academy
                <br />
                <b>Subject: Application for Leave ({LEAVE_TYPE_EN[f.type] || f.type}).</b>
                <br />
                Dear Sir, I am {user.name}. {f.reason || "..."} In light of
                this, I kindly request you to grant me leave from{" "}
                {fmtDate(f.from)} to {fmtDate(f.to)}.
                <br />
                Sincerely, <b>{user.name}</b>
              </>
            ) : (
              <>
                বরাবর, পরিচালক মহোদয়, তারবিয়াতুল কুরআন একাডেমি
                <br />
                <b>বিষয়: ছুটির আবেদন ({f.type})।</b>
                <br />
                জনাব, সবিনয় নিবেদন এই যে, আমি {user.name}। {f.reason || "..."}{" "}
                এমতাবস্থায়, {fmtDate(f.from)} থেকে {fmtDate(f.to)} পর্যন্ত ছুটি
                মঞ্জুর করতে আপনার সদয় মর্জি হয়।
                <br />
                নিবেদক, <b>{user.name}</b>
              </>
            )}
          </div>
          <Btn
            style={{ marginTop: 14, width: "100%", justifyContent: "center" }}
            onClick={submit}
          >
            {T("দরখাস্ত জমা দিন", "Submit Application")}
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ভাউচার/রিসিট — পাঠানো রিসিট প্রাপকের পোর্টালে ═══════════════ */
function MyReceiptsView({ db, user }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const [receipts, setReceipts] = useState(
    (db.sentReceipts || []).filter(
      (x) => String(x.toUserId) === String(user.id),
    ),
  );

  useEffect(() => {
    api
      .myReceipts()
      .then((data) => {
        setReceipts(
          data.map((r) => ({
            id: r.id,
            toUserId: r.to_user || r.toUserId,
            kind: r.kind,
            month: r.month_label || r.month,
            amount: r.amount,
            method: r.method,
            date: r.sent_at ? fmtDate(r.sent_at) : r.date || todayISO(),
            rawDate: r.sent_at || r.date || todayISO(), // রিসিট ডকুমেন্টে সবসময় ইংরেজি তারিখ দেখাতে (তালিকার ভাষা-নির্ভর তারিখের বাইরে)
            sentBy: r.sent_by_name || r.sentBy || "—",
          })),
        );
      })
      .catch(() => {
        /* keep mock */
      });
  }, [user.id]);

  return (
    <Section
      title={T("ভাউচার / রিসিট", "Vouchers / Receipts")}
      sub={T(
        "একাডেমি থেকে আপনার জন্য পাঠানো রিসিট ও ভাউচার — দেখুন, প্রিন্ট বা PDF সেভ করুন",
        "Receipts and vouchers sent to you by the academy — view, print, or save as PDF",
      )}
    >
      <Table
        head={T(
          ["ধরন", "মাস/বিবরণ", "পরিমাণ", "তারিখ", "পাঠিয়েছেন", "দেখুন"],
          ["Type", "Month/Detail", "Amount", "Date", "Sent By", "View"],
        )}
        rows={receipts.map((x) => [
          x.kind,
          x.month,
          `৳${bn(Number(x.amount).toLocaleString("en"))}`,
          x.date,
          x.sentBy || "—",
          <Btn
            key="v"
            sm
            kind="soft"
            onClick={() =>
              printReceipt(
                {
                  ...x,
                  date: fmtDateEn(x.rawDate),
                  method: methodEn(x.method),
                  noSend: true,
                },
                user,
                x.kind,
              )
            }
          >
            {T("👁 দেখুন / ডাউনলোড", "👁 View / Download")}
          </Btn>,
        ])}
        empty={T("এখনো কোনো রিসিট পাঠানো হয়নি", "No receipts sent yet")}
      />
    </Section>
  );
}

/* ═══════════════ সকল স্টুডেন্ট — তালিকা, WhatsApp, বিস্তারিত; এডিট কেবল পরিচালক ═══════════════ */
/* দেশ ও কান্ট্রি কোড — ISO2 কোড থেকে পতাকা অটো-তৈরি; বিশ্বের সব দেশের তালিকা */
const flagOf = (iso) =>
  iso.toUpperCase().replace(/./g, (c) => String.fromCodePoint(127397 + c.charCodeAt(0)));
const COUNTRIES = [
  ["Afghanistan", "AF", "93"], ["Albania", "AL", "355"], ["Algeria", "DZ", "213"],
  ["Andorra", "AD", "376"], ["Angola", "AO", "244"], ["Antigua and Barbuda", "AG", "1268"],
  ["Argentina", "AR", "54"], ["Armenia", "AM", "374"], ["Australia", "AU", "61"],
  ["Austria", "AT", "43"], ["Azerbaijan", "AZ", "994"], ["Bahamas", "BS", "1242"],
  ["Bahrain", "BH", "973"], ["Bangladesh", "BD", "880"], ["Barbados", "BB", "1246"],
  ["Belarus", "BY", "375"], ["Belgium", "BE", "32"], ["Belize", "BZ", "501"],
  ["Benin", "BJ", "229"], ["Bhutan", "BT", "975"], ["Bolivia", "BO", "591"],
  ["Bosnia and Herzegovina", "BA", "387"], ["Botswana", "BW", "267"], ["Brazil", "BR", "55"],
  ["Brunei", "BN", "673"], ["Bulgaria", "BG", "359"], ["Burkina Faso", "BF", "226"],
  ["Burundi", "BI", "257"], ["Cambodia", "KH", "855"], ["Cameroon", "CM", "237"],
  ["Canada", "CA", "1"], ["Cape Verde", "CV", "238"], ["Central African Republic", "CF", "236"],
  ["Chad", "TD", "235"], ["Chile", "CL", "56"], ["China", "CN", "86"],
  ["Colombia", "CO", "57"], ["Comoros", "KM", "269"], ["Congo (DRC)", "CD", "243"],
  ["Congo (Republic)", "CG", "242"], ["Costa Rica", "CR", "506"], ["Croatia", "HR", "385"],
  ["Cuba", "CU", "53"], ["Cyprus", "CY", "357"], ["Czechia", "CZ", "420"],
  ["Denmark", "DK", "45"], ["Djibouti", "DJ", "253"], ["Dominica", "DM", "1767"],
  ["Dominican Republic", "DO", "1809"], ["Ecuador", "EC", "593"], ["Egypt", "EG", "20"],
  ["El Salvador", "SV", "503"], ["Equatorial Guinea", "GQ", "240"], ["Eritrea", "ER", "291"],
  ["Estonia", "EE", "372"], ["Eswatini", "SZ", "268"], ["Ethiopia", "ET", "251"],
  ["Fiji", "FJ", "679"], ["Finland", "FI", "358"], ["France", "FR", "33"],
  ["Gabon", "GA", "241"], ["Gambia", "GM", "220"], ["Georgia", "GE", "995"],
  ["Germany", "DE", "49"], ["Ghana", "GH", "233"], ["Greece", "GR", "30"],
  ["Grenada", "GD", "1473"], ["Guatemala", "GT", "502"], ["Guinea", "GN", "224"],
  ["Guinea-Bissau", "GW", "245"], ["Guyana", "GY", "592"], ["Haiti", "HT", "509"],
  ["Honduras", "HN", "504"], ["Hong Kong", "HK", "852"], ["Hungary", "HU", "36"],
  ["Iceland", "IS", "354"], ["India", "IN", "91"], ["Indonesia", "ID", "62"],
  ["Iran", "IR", "98"], ["Iraq", "IQ", "964"], ["Ireland", "IE", "353"],
  ["Israel", "IL", "972"], ["Italy", "IT", "39"], ["Ivory Coast", "CI", "225"],
  ["Jamaica", "JM", "1876"], ["Japan", "JP", "81"], ["Jordan", "JO", "962"],
  ["Kazakhstan", "KZ", "7"], ["Kenya", "KE", "254"], ["Kiribati", "KI", "686"],
  ["Kosovo", "XK", "383"], ["Kuwait", "KW", "965"], ["Kyrgyzstan", "KG", "996"],
  ["Laos", "LA", "856"], ["Latvia", "LV", "371"], ["Lebanon", "LB", "961"],
  ["Lesotho", "LS", "266"], ["Liberia", "LR", "231"], ["Libya", "LY", "218"],
  ["Liechtenstein", "LI", "423"], ["Lithuania", "LT", "370"], ["Luxembourg", "LU", "352"],
  ["Macau", "MO", "853"], ["Madagascar", "MG", "261"], ["Malawi", "MW", "265"],
  ["Malaysia", "MY", "60"], ["Maldives", "MV", "960"], ["Mali", "ML", "223"],
  ["Malta", "MT", "356"], ["Marshall Islands", "MH", "692"], ["Mauritania", "MR", "222"],
  ["Mauritius", "MU", "230"], ["Mexico", "MX", "52"], ["Micronesia", "FM", "691"],
  ["Moldova", "MD", "373"], ["Monaco", "MC", "377"], ["Mongolia", "MN", "976"],
  ["Montenegro", "ME", "382"], ["Morocco", "MA", "212"], ["Mozambique", "MZ", "258"],
  ["Myanmar", "MM", "95"], ["Namibia", "NA", "264"], ["Nauru", "NR", "674"],
  ["Nepal", "NP", "977"], ["Netherlands", "NL", "31"], ["New Zealand", "NZ", "64"],
  ["Nicaragua", "NI", "505"], ["Niger", "NE", "227"], ["Nigeria", "NG", "234"],
  ["North Korea", "KP", "850"], ["North Macedonia", "MK", "389"], ["Norway", "NO", "47"],
  ["Oman", "OM", "968"], ["Pakistan", "PK", "92"], ["Palau", "PW", "680"],
  ["Palestine", "PS", "970"], ["Panama", "PA", "507"], ["Papua New Guinea", "PG", "675"],
  ["Paraguay", "PY", "595"], ["Peru", "PE", "51"], ["Philippines", "PH", "63"],
  ["Poland", "PL", "48"], ["Portugal", "PT", "351"], ["Qatar", "QA", "974"],
  ["Romania", "RO", "40"], ["Russia", "RU", "7"], ["Rwanda", "RW", "250"],
  ["Saint Kitts and Nevis", "KN", "1869"], ["Saint Lucia", "LC", "1758"],
  ["Saint Vincent and the Grenadines", "VC", "1784"], ["Samoa", "WS", "685"],
  ["San Marino", "SM", "378"], ["Sao Tome and Principe", "ST", "239"],
  ["Saudi Arabia", "SA", "966"], ["Senegal", "SN", "221"], ["Serbia", "RS", "381"],
  ["Seychelles", "SC", "248"], ["Sierra Leone", "SL", "232"], ["Singapore", "SG", "65"],
  ["Slovakia", "SK", "421"], ["Slovenia", "SI", "386"], ["Solomon Islands", "SB", "677"],
  ["Somalia", "SO", "252"], ["South Africa", "ZA", "27"], ["South Korea", "KR", "82"],
  ["South Sudan", "SS", "211"], ["Spain", "ES", "34"], ["Sri Lanka", "LK", "94"],
  ["Sudan", "SD", "249"], ["Suriname", "SR", "597"], ["Sweden", "SE", "46"],
  ["Switzerland", "CH", "41"], ["Syria", "SY", "963"], ["Taiwan", "TW", "886"],
  ["Tajikistan", "TJ", "992"], ["Tanzania", "TZ", "255"], ["Thailand", "TH", "66"],
  ["Timor-Leste", "TL", "670"], ["Togo", "TG", "228"], ["Tonga", "TO", "676"],
  ["Trinidad and Tobago", "TT", "1868"], ["Tunisia", "TN", "216"], ["Turkey", "TR", "90"],
  ["Turkmenistan", "TM", "993"], ["Tuvalu", "TV", "688"], ["Uganda", "UG", "256"],
  ["Ukraine", "UA", "380"], ["United Arab Emirates", "AE", "971"], ["United Kingdom", "GB", "44"],
  ["United States", "US", "1"], ["Uruguay", "UY", "598"], ["Uzbekistan", "UZ", "998"],
  ["Vanuatu", "VU", "678"], ["Vatican City", "VA", "379"], ["Venezuela", "VE", "58"],
  ["Vietnam", "VN", "84"], ["Yemen", "YE", "967"], ["Zambia", "ZM", "260"],
  ["Zimbabwe", "ZW", "263"],
].map(([name, iso, dial]) => ({ name, iso, dial: "+" + dial, flag: flagOf(iso) }));
// কোড ও নম্বর আলাদা রাখা হয় দেশ (unique ISO) দিয়ে — তাই একই ডায়াল কোডের (যেমন +1)
// একাধিক দেশ থাকলেও একটার সাথে আরেকটা মিশে যায় না। lossless।
const DIAL_CODES = [...new Set(COUNTRIES.map((c) => c.dial.replace(/\D/g, "")))].sort(
  (a, b) => b.length - a.length,
);
const dialDigits = (iso) => {
  const c = COUNTRIES.find((x) => x.iso === iso);
  return c ? c.dial.replace(/\D/g, "") : "";
};
const splitPhone = (full) => {
  const d = String(full || "").replace(/\D/g, "");
  if (!d) return { iso: "BD", local: "" };
  for (const code of DIAL_CODES)
    if (d.startsWith(code)) {
      const c = COUNTRIES.find((x) => x.dial.replace(/\D/g, "") === code);
      return { iso: c ? c.iso : "", local: d.slice(code.length) };
    }
  return { iso: "", local: d };
};
const joinPhone = (iso, local) =>
  dialDigits(iso) + String(local || "").replace(/\D/g, "");

function AllStudentsView({ db, setDb, user, courses = [], refresh }) {
  const [detail, setDetail] = useState(null);
  const [edit, setEdit] = usePersistedState("stu_edit", null); // {id?} — null=বন্ধ, {}=নতুন
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [idBusy, setIdBusy] = useState(false); // "স্টুডেন্ট আইডি তৈরি করুন" চলছে কিনা
  const [courseList, setCourseList] = useState(courses || []); // আসল কোর্স তালিকা (ড্রপডাউনে)
  const [teachers, setTeachers] = useState([]); // উস্তাদ তালিকা (কার কাছে পড়ে)

  // ব্যাকএন্ড থেকে স্টুডেন্ট তালিকা লোড — ব্যর্থ হলে mock USERS
  // ফি স্টেটাস আসল পেমেন্ট দেখে বলার জন্য (null = এখনো আসেনি)
  const [payments, setPayments] = useState(null);
  // কোন কোন মাস মওকুফ করা হয়েছে — "মওকুফ" ও "পরিশোধিত" আলাদা দেখাতে
  const [waived, setWaived] = useState([]);
  useEffect(() => {
    let alive = true;
    api
      .myFees()
      .then((rows) => alive && setPayments(rows || []))
      .catch(() => alive && setPayments([]));
    api
      .duesWithWaived()
      .then((rows) => alive && setWaived((rows || []).filter((x) => x.waived)))
      .catch(() => alive && setWaived([]));
    return () => {
      alive = false;
    };
  }, []);

  const loadStudents = async () => {
    setLoading(true);
    try {
      const data = await api.allStudents();
      // backend format → frontend format
      setStudents(
        data.map((s) => ({
          id: s.id,
          role: "student",
          name: s.name || s.name_bn,
          sub: s.sub || s.sub_title || "",
          user: s.username,
          pass: s.plain_password || s.password || "••••",
          fee: s.monthly_fee,
          guardian: s.guardian,
          country: s.country,
          phone: s.phone,
          email: s.email,
          days: s.class_days || [],
          studentId: s.student_id || "", // অটো/ম্যানুয়াল স্টুডেন্ট আইডি (SH-LC-US-007)
          dues: s.due_months || [], // বকেয়া মাসের তালিকা — "বিস্তারিত"-এ ফি স্টেটাস দেখাতে
        })),
      );
    } catch {
      setStudents(USERS.filter((u) => u.role === "student"));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadStudents();
    api
      .courses()
      .then((cs) =>
        setCourseList(
          cs.map((c) => ({
            id: c.id,
            name: c.name,
            color: c.color,
            teacherId: c.teacher,
            teacherName: c.teacher_name,
            studentIds: c.students || [],
          })),
        ),
      )
      .catch(() => {});
    api
      .allTeachers()
      .then((d) => setTeachers(d.map(adaptPerson)))
      .catch(() => {});
  }, []);
  const teacherNameOf = (id) =>
    teachers.find((t) => String(t.id) === String(id))?.name || "";

  const waHi = (s) =>
    `Assalamu Alaikum wa Rahmatullah. Respected ${s.guardian || "Guardian"}, we are reaching out to you from Tarbiyatul Quran Academy regarding ${s.name}. JazakAllahu Khairan fid-Darayn.`;

  // পরিচালক কোনো নির্দিষ্ট মাসের বকেয়া মওকুফ করে বকেয়া তালিকা থেকে সরিয়ে দিতে পারেন
  const waiveDue = (studentId, monthLabel) =>
    askConfirm(
      `"${monthLabel}" মাসের বকেয়া মওকুফ করবেন? এটা বকেয়ার তালিকা থেকে সরে যাবে।`,
      async () => {
        try {
          await api.waiveDue(studentId, monthLabel);
        } catch {
          return notice("মওকুফ করতে ব্যর্থ — সার্ভার সংযোগ যাচাই করুন।");
        }
        const strip = (arr) => (arr || []).filter((m) => m !== monthLabel);
        setStudents((prev) =>
          prev.map((x) =>
            x.id === studentId ? { ...x, dues: strip(x.dues) } : x,
          ),
        );
        setDetail((prev) =>
          prev && prev.id === studentId
            ? { ...prev, dues: strip(prev.dues) }
            : prev,
        );
        notice(`✔ "${monthLabel}" মাসের বকেয়া মওকুফ করা হয়েছে।`);
      },
    );

  // পুরনো (আইডি ছাড়া) স্টুডেন্টদের জন্য এক ক্লিকে স্টুডেন্ট আইডি তৈরি —
  // ভর্তির ক্রম অনুযায়ী সিরিয়াল বসে; যাদের আইডি আছে তাদের কিছুই বদলায় না
  const genStudentIds = async () => {
    setIdBusy(true);
    try {
      const r = await api.backfillStudentIds();
      await loadStudents();
      notice(
        r?.created
          ? `✔ ${bn(r.created)} জন স্টুডেন্টের আইডি তৈরি হয়েছে।`
          : "সব স্টুডেন্টেরই আইডি আগে থেকেই আছে।",
      );
    } catch (e) {
      notice(
        "স্টুডেন্ট আইডি তৈরি করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
    setIdBusy(false);
  };

  /* বাছাই করা উস্তাদ কি এই কোর্সের সাথে যুক্ত?
     যুক্ত ধরা হয় দুই সূত্রে — তিনি কোর্সের নির্ধারিত উস্তাদ, অথবা এই
     কোর্সের অন্য কোনো শিক্ষার্থী ইতিমধ্যে তাঁর কাছে পড়ে। */
  const teacherLinkedToCourse = (cid, tid) => {
    const c = courseList.find((x) => String(x.id) === String(cid));
    if (!c) return true; // কোর্স জানা নেই — অকারণে সতর্ক করি না
    if (String(c.teacherId || "") === String(tid)) return true;
    return (c.studentIds || []).some((sid) =>
      students.some(
        (st) =>
          String(st.id) === String(sid) &&
          String(st.id) !== String(edit?.id || "") &&
          String(st.teacherId || "") === String(tid),
      ),
    );
  };

  const saveEdit = async () => {
    if (!edit.name || !edit.user) return notice("নাম ও আইডি দিন।");
    setSaving(true);
    try {
      const payload = {
        username: edit.user,
        name_bn: edit.name,
        role: "student",
        country: edit.country,
        phone: joinPhone(edit.phoneIso, edit.phone),
        email: edit.email,
        guardian: edit.guardian,
        monthly_fee: +edit.fee || DEFAULT_FEE,
        class_days: edit.days || [],
        // খালি পাঠালে সার্ভার নিজেই অটো আইডি তৈরি করে দেয় (নতুন স্টুডেন্টে);
        // পরিচালক নিজে কিছু লিখলে সেটাই বসে
        student_id: (edit.studentId || "").trim(),
        // "••••" placeholder পাঠাব না (নইলে পাসওয়ার্ড নষ্ট হতো); আসল/নতুন হলে পাঠাই
        ...(edit.pass && edit.pass !== "••••" ? { password: edit.pass } : {}),
        // "কার কাছে পড়ে" — এখন শিক্ষার্থীর নিজের ঘরে বসে, কোর্সে নয়। তাই
        // একজনের উস্তাদ বদলালে ওই কোর্সের বাকিদের কিছুই বদলায় না।
        teacher: edit.teacherId ? +edit.teacherId : null,
      };
      const saved = await api.saveUser(payload, edit.id || undefined);
      const sid = saved?.id || edit.id;

      /* ── কোর্স বসানো/বদলানো ──
         ⚠️ আগে এটা কেবল নতুন স্টুডেন্টেই হতো (!edit.id)। ফলে পুরনো কারও
         কোর্স বদলাতে গেলে ড্রপডাউন বদলাত ঠিকই, কিন্তু সংরক্ষণ হতো না —
         আর অন্য পাতায় কোর্স অনুযায়ী তালিকা ভুল থেকে যেত।
         এখন এডিটেও কাজ করে: আগের কোর্স থেকে সরিয়ে নতুনটিতে বসানো হয়। */
      let courseMoved = false;
      if (sid) {
        const wantId = String(edit.courseId || "");
        const inCourse = (c) =>
          ((c && c.studentIds) || []).some((x) => String(x) === String(sid));
        // এখন যে যে কোর্সে আছে
        const current = courseList.filter(inCourse);
        for (const c of current) {
          if (String(c.id) === wantId) continue; // এটাই তো চাই
          try {
            await api.saveCourse(
              {
                students: (c.studentIds || []).filter(
                  (x) => String(x) !== String(sid),
                ),
              },
              c.id,
            );
            courseMoved = true;
          } catch (e) {
            notice(
              `"${c.name}" কোর্স থেকে সরানো যায়নি — ` +
                (e?.data?.error || e?.message || "আবার চেষ্টা করুন"),
            );
          }
        }
        const target = courseList.find((x) => String(x.id) === wantId);
        if (target && !inCourse(target)) {
          try {
            await api.saveCourse(
              { students: [...(target.studentIds || []), sid] },
              target.id,
            );
            courseMoved = true;
          } catch (e) {
            notice(
              `"${target.name}" কোর্সে যুক্ত করা যায়নি — ` +
                (e?.data?.error || e?.message || "আবার চেষ্টা করুন"),
            );
          }
        }
      }
      await loadStudents(); // ব্যাকএন্ড থেকে নতুন তালিকা
      setEdit(null);
      if (courseMoved && edit.id)
        notice(
          "✔ কোর্স বদলানো হয়েছে। মনে রাখবেন — ক্লাস রুটিনে শিক্ষার্থীর " +
            "তালিকা আলাদা, দরকার হলে সেটাও মিলিয়ে নিন।",
        );
    } catch {
      // ব্যাকএন্ড না থাকলে — mock এ সংরক্ষণ
      if (edit.id) {
        const u = USERS.find((x) => x.id === edit.id);
        if (u)
          Object.assign(u, {
            name: edit.name,
            country: edit.country,
            phone: joinPhone(edit.phoneIso, edit.phone),
            email: edit.email,
            guardian: edit.guardian,
            fee: +edit.fee,
            days: edit.days || [],
            user: edit.user,
            pass: edit.pass,
          });
      } else {
        const id = "s" + uid();
        USERS.push({
          id,
          role: "student",
          name: edit.name,
          sub: courseById(COURSES, edit.courseId)?.name || "নতুন স্টুডেন্ট",
          user: edit.user,
          pass: edit.pass || genPass(),
          fee: +edit.fee || DEFAULT_FEE,
          guardian: edit.guardian,
          country: edit.country,
          phone: joinPhone(edit.phoneIso, edit.phone),
          email: edit.email,
          days: edit.days || [],
        });
        COURSES.find((c) => c.id === edit.courseId)?.studentIds.push(id);
      }
      setStudents(USERS.filter((u) => u.role === "student"));
      setEdit(null);
      refresh();
    } finally {
      setSaving(false);
    }
  };

  const delStudent = (s) =>
    askConfirm(`${s.name}-কে মুছে ফেলবেন?`, async () => {
      try {
        await api.deleteUser(s.id);
        await loadStudents();
        notice(`✔ ${s.name}-কে মুছে ফেলা হয়েছে।`);
      } catch (e) {
        notice(
          `${s.name}-কে মুছতে ব্যর্থ — ` +
            (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
        );
      }
    });
  /* এক স্টুডেন্টের পূর্ণ চিত্র */
  const Detail = ({ s }) => {
    const cs = courseList.filter((c) => (c.studentIds || []).includes(s.id));
    const routines = (db.routine || []).filter((r) =>
      r.studentIds && r.studentIds.length
        ? r.studentIds.includes(s.id)
        : (courseById(COURSES, r.courseId).studentIds || []).includes(s.id),
    );
    const dues = s.dues || [];
    /* ⚠️ আগে কেবল "বকেয়া আছে কিনা" দেখে বলা হতো — বকেয়া না থাকলেই
       "পরিশোধিত ✔"। কিন্তু বকেয়ার রেকর্ড তৈরি হয় মাসিক cron চললে
       (cron/monthly/)। নতুন ভর্তি হওয়া শিক্ষার্থীর জন্য সেটা চলার আগে
       কোনো বকেয়াই থাকে না — ফলে এক টাকাও না দিয়েই "পরিশোধিত" দেখাত।
       এখন আসল পেমেন্টের রেকর্ড দেখে বলা হয়।
       ⚠️ তালিকাটা প্যারেন্টে আনা হয় — Detail প্রতিবার নতুন করে তৈরি হয়
       বলে এখানে useEffect রাখলে বারবার রিমাউন্ট হয়ে অকারণে কল হতো। */
    const myPays =
      payments === null
        ? null
        : payments.filter(
            (x) => String(x.student) === String(s.id) && x.status === "verified",
          );
    const myWaived = (waived || []).filter(
      (x) => String(x.user) === String(s.id),
    );
    const inf = (k, v) => (
      <div
        style={{
          padding: "8px 10px",
          background: C.cream,
          borderRadius: 10,
          fontSize: 13,
        }}
      >
        {k}: <b>{v || "—"}</b>
      </div>
    );
    return (
      <Modal
        title={`বিস্তারিত — ${s.name}`}
        onClose={() => setDetail(null)}
        wide
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 8,
            marginBottom: 12,
          }}
        >
          {inf("স্টুডেন্ট আইডি", s.studentId)}
          {inf("বাবা/অভিভাবকের নাম", s.guardian)}
          {s.email ? (
            <div
              style={{
                padding: "8px 10px",
                background: C.cream,
                borderRadius: 10,
                fontSize: 13,
              }}
            >
              ইমেইল:{" "}
              <a
                href={`https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(s.email)}`}
                target="_blank"
                rel="noreferrer"
                style={{ color: C.emerald, fontWeight: 700 }}
                title="জিমেইলে নতুন মেইল লিখুন"
              >
                {s.email}
              </a>
            </div>
          ) : (
            inf("ইমেইল", s.email)
          )}
          {inf("দেশ", s.country)}
          {inf("WhatsApp", s.phone ? "+" + s.phone : "—")}
          {inf("আইডি", s.user)}
          {inf("পাসওয়ার্ড", s.pass)}
          {inf("মাসিক ফি", `৳${bn((s.fee || 0).toLocaleString("en"))}`)}
          <div
            style={{
              padding: "8px 10px",
              background: C.cream,
              borderRadius: 10,
              fontSize: 13,
            }}
          >
            ফি স্টেটাস:{" "}
            {dues.length ? (
              <span
                style={{
                  display: "inline-flex",
                  gap: 6,
                  flexWrap: "wrap",
                  verticalAlign: "middle",
                }}
              >
                {dues.map((m) => (
                  <Tag key={m} color={C.red} bg={C.redBg}>
                    বকেয়া: {m}
                    {isDir(user) && (
                      <button
                        onClick={() => waiveDue(s.id, m)}
                        title="এই মাসের বকেয়া মওকুফ করুন"
                        style={{
                          marginLeft: 6,
                          border: "none",
                          background: "none",
                          cursor: "pointer",
                          color: "inherit",
                          fontWeight: 800,
                          padding: 0,
                        }}
                      >
                        ✕
                      </button>
                    )}
                  </Tag>
                ))}
              </span>
            ) : myPays === null ? (
              <Tag color={C.muted} bg={C.cream}>
                দেখা হচ্ছে…
              </Tag>
            ) : myPays.length > 0 ? (
              <Tag>পরিশোধিত ✔ — সর্বশেষ {myPays[0].month_label}</Tag>
            ) : myWaived.length > 0 ? (
              /* মওকুফ ≠ পরিশোধিত — টাকা আসেনি, নেওয়া হবেও না।
                 তাই আলাদা রঙে, আলাদা কথায়। */
              <Tag color={C.gold} bg={C.amberBg}>
                বকেয়া নেই — মওকুফ করা হয়েছে
              </Tag>
            ) : (
              /* কোনো পেমেন্টও নেই, মওকুফও নেই */
              <Tag color={C.red} bg={C.redBg}>
                এখনো কোনো পেমেন্ট নেই
              </Tag>
            )}
            {myPays && myPays.length > 0 && (
              <div style={{ fontSize: 11.5, color: C.muted, marginTop: 4 }}>
                মোট {bn(myPays.length)}টি পেমেন্ট যাচাই করা হয়েছে
              </div>
            )}
            {myWaived.length > 0 && (
              <div style={{ fontSize: 11.5, color: "#8a5a00", marginTop: 4 }}>
                🏝️ মওকুফ:{" "}
                {myWaived
                  .map(
                    (w) =>
                      w.month_label +
                      (w.waived_reason ? ` (${w.waived_reason})` : ""),
                  )
                  .join(", ")}
              </div>
            )}
          </div>
        </div>
        <div style={{ fontWeight: 800, fontSize: 13.5, margin: "8px 0 6px" }}>
          📚 কী পড়ে, কার কাছে পড়ে
        </div>
        {cs.length === 0 && (
          <div style={{ fontSize: 13, color: C.muted }}>
            কোনো কোর্সে যুক্ত নেই
          </div>
        )}
        {cs.map((c) => (
          <div
            key={c.id}
            style={{
              padding: "9px 12px",
              borderRadius: 10,
              background: C.greenBg,
              marginBottom: 6,
              fontSize: 13,
            }}
          >
            <b style={{ color: c.color || C.emerald }}>{c.name}</b> · উস্তাদ:{" "}
            <b>{c.teacherName || teacherNameOf(c.teacherId) || "—"}</b>
          </div>
        ))}
        <div style={{ fontWeight: 800, fontSize: 13.5, margin: "10px 0 6px" }}>
          📅 সপ্তাহে কয়দিন, কী কী বারে, কোন সময়ে
        </div>
        {routines.length === 0 && (
          <div style={{ fontSize: 13, color: C.muted }}>
            এখনো রুটিন তৈরি হয়নি
          </div>
        )}
        {routines.map((r) => {
          const c = courseById(COURSES, r.courseId);
          return (
            <div
              key={r.id}
              style={{
                padding: "9px 12px",
                borderRadius: 10,
                background: C.cream,
                marginBottom: 6,
                fontSize: 13,
              }}
            >
              <b>{c.name}</b> — সপ্তাহে {bn(r.days.length)} দিন:{" "}
              <b>{r.days.map((i) => DAY_BN[i]).join(", ")}</b> · 🕐 {r.time} (
              {bn(r.dur)} মি) · উস্তাদ:{" "}
              {userById(r.teacherId || c.teacherId).name}
            </div>
          );
        })}
      </Modal>
    );
  };
  return (
    <Section
      title="সকল স্টুডেন্ট"
      sub={
        isDir(user)
          ? "সম্পূর্ণ তালিকা — এডিট, যোগ ও মুছে ফেলার নিয়ন্ত্রণ কেবল পরিচালকের"
          : "সম্পূর্ণ তালিকা — আপনি (এডমিন) কেবল দেখতে পারবেন"
      }
      action={
        isDir(user) && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {students.some((s) => !s.studentId) && (
              <Btn
                kind="soft"
                onClick={genStudentIds}
                style={{ opacity: idBusy ? 0.6 : 1 }}
              >
                {idBusy ? "⏳ তৈরি হচ্ছে…" : "🆔 বাকিদের স্টুডেন্ট আইডি তৈরি করুন"}
              </Btn>
            )}
            <Btn
              onClick={() =>
                setEdit({
                  name: "",
                  country: "",
                  phoneIso: "BD",
                  phone: "",
                  email: "",
                  guardian: "",
                  fee: DEFAULT_FEE,
                  days: [],
                  user: "",
                  pass: genPass(),
                  studentId: "", // খালি রাখলে সার্ভার নিজেই তৈরি করে দেবে
                  courseId: courseList[0]?.id || "",
                  teacherId: courseList[0]?.teacherId || "",
                })
              }
            >
              + নতুন স্টুডেন্ট
            </Btn>
          </div>
        )
      }
    >
      {loading && <Loader text="স্টুডেন্ট তালিকা আসছে" />}
      <Table
        head={[
          "স্টুডেন্ট নাম",
          "দেশ",
          "লগইন আইডি",
          "পাসওয়ার্ড",
          "WhatsApp নম্বর",
          "বিস্তারিত",
          ...(isDir(user) ? ["অ্যাকশন"] : []),
        ]}
        rows={students.map((s) => [
          <span key="n">
            <b>{s.name}</b>
            {s.studentId && (
              <span
                style={{
                  marginLeft: 8,
                  background: C.cream,
                  border: `1px solid ${C.line}`,
                  color: C.emerald,
                  padding: "2px 8px",
                  borderRadius: 99,
                  fontSize: 11.5,
                  fontWeight: 800,
                  whiteSpace: "nowrap",
                }}
                title="স্টুডেন্ট আইডি"
              >
                {s.studentId}
              </span>
            )}
          </span>,
          s.country || "—",
          s.user,
          <code
            key="p"
            style={{
              background: C.cream,
              padding: "2px 8px",
              borderRadius: 6,
              fontSize: 12,
            }}
          >
            {s.pass}
          </code>,
          <span
            key="w"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              whiteSpace: "nowrap",
            }}
          >
            {s.phone ? "+" + s.phone : "—"}
            {s.phone && (
              <a
                href={`https://wa.me/${s.phone}?text=${encodeURIComponent(waHi(s))}`}
                target="_blank"
                rel="noreferrer"
                style={{ textDecoration: "none" }}
              >
                <span
                  style={{
                    background: "#25D366",
                    color: "#fff",
                    borderRadius: 8,
                    padding: "3px 9px",
                    fontSize: 11.5,
                    fontWeight: 800,
                  }}
                >
                  💬 মেসেজ
                </span>
              </a>
            )}
          </span>,
          <Btn key="d" sm kind="ghost" onClick={() => setDetail(s)}>
            📋 বিস্তারিত
          </Btn>,
          ...(isDir(user)
            ? [
                <span key="a" style={{ display: "flex", gap: 5 }}>
                  <Btn
                    sm
                    kind="soft"
                    onClick={() => {
                      const p = splitPhone(s.phone);
                      setEdit({
                        id: s.id,
                        name: s.name,
                        country: s.country || "",
                        phoneIso: p.iso,
                        phone: p.local,
                        email: s.email || "",
                        guardian: s.guardian || "",
                        fee: s.fee,
                        days: s.days || [],
                        user: s.user,
                        pass: s.pass,
                        studentId: s.studentId || "",
                        // ⚠️ আগে এ দুটো ভরাই হতো না, তাই এডিট খুললে ঘর
                        // দুটো খালি দেখাত — মনে হতো কোর্স/উস্তাদ বসানোই নেই
                        courseId:
                          (courseList.find((c) =>
                            (c.studentIds || []).some(
                              (x) => String(x) === String(s.id),
                            ),
                          ) || {}).id || "",
                        teacherId: s.teacherId || "",
                      });
                    }}
                  >
                    ✏️
                  </Btn>
                  <Btn sm kind="danger" onClick={() => delStudent(s)}>
                    🗑
                  </Btn>
                </span>,
              ]
            : []),
        ])}
      />
      {detail && <Detail s={detail} />}
      {edit && (
        <Modal
          title={
            edit.id
              ? `✏️ এডিট — ${edit.name}`
              : "+ নতুন স্টুডেন্ট যোগ করুন (কেবল পরিচালক)"
          }
          onClose={() => setEdit(null)}
          wide
        >
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}
          >
            <div>
              <label style={S.label}>নাম</label>
              <input
                style={S.input}
                value={edit.name}
                onChange={(e) => setEdit({ ...edit, name: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>বাবা/অভিভাবকের নাম</label>
              <input
                style={S.input}
                value={edit.guardian}
                onChange={(e) => setEdit({ ...edit, guardian: e.target.value })}
              />
            </div>
            <div style={{ gridColumn: "1 / -1" }}>
              <label style={S.label}>
                স্টুডেন্ট আইডি{" "}
                <span style={{ fontWeight: 400, color: C.muted }}>
                  — খালি রাখলে নাম·বাবার নাম·দেশ·সিরিয়াল মিলিয়ে নিজে থেকেই তৈরি হবে
                </span>
              </label>
              <input
                style={S.input}
                value={edit.studentId || ""}
                onChange={(e) => setEdit({ ...edit, studentId: e.target.value })}
                placeholder={edit.id ? "" : "যেমন: SH-LC-US-007 (অটো তৈরি হবে)"}
              />
            </div>
            <div>
              <label style={S.label}>দেশ</label>
              <select
                style={S.input}
                value={edit.country || ""}
                onChange={(e) => setEdit({ ...edit, country: e.target.value })}
              >
                <option value="">— দেশ নির্বাচন করুন —</option>
                {edit.country &&
                  !COUNTRIES.some((c) => c.name === edit.country) && (
                    <option value={edit.country}>{edit.country}</option>
                  )}
                {COUNTRIES.map((c) => (
                  <option key={c.iso} value={c.name}>
                    {c.flag} {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={S.label}>WhatsApp নম্বর</label>
              {/* দেশ বেছে নিলে কোড বসে; পাশে শুধু নম্বর — দুটো আলাদা, মিশে যায় না */}
              <select
                style={S.input}
                value={edit.phoneIso || ""}
                onChange={(e) => setEdit({ ...edit, phoneIso: e.target.value })}
              >
                <option value="">— কোড / দেশ বাছুন —</option>
                {COUNTRIES.map((c) => (
                  <option key={c.iso} value={c.iso}>
                    {c.flag} {c.name} ({c.dial})
                  </option>
                ))}
              </select>
              <input
                style={{ ...S.input, marginTop: 6 }}
                type="tel"
                value={edit.phone}
                onChange={(e) => setEdit({ ...edit, phone: e.target.value })}
                placeholder="নম্বর (কোড ছাড়া, যেমন 1712345678)"
              />
              <div style={{ fontSize: 11.5, color: C.muted, marginTop: 4 }}>
                পূর্ণ নম্বর:{" "}
                <b style={{ color: C.emerald }}>
                  +{joinPhone(edit.phoneIso, edit.phone) || "—"}
                </b>
              </div>
            </div>
            <div>
              <label style={S.label}>ইমেইল</label>
              <input
                style={S.input}
                value={edit.email}
                onChange={(e) => setEdit({ ...edit, email: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>মাসিক ফি (৳)</label>
              <input
                type="number"
                style={S.input}
                value={edit.fee}
                onChange={(e) => setEdit({ ...edit, fee: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>লগইন আইডি</label>
              <input
                style={S.input}
                value={edit.user}
                onChange={(e) => setEdit({ ...edit, user: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>পাসওয়ার্ড</label>
              <div style={{ display: "flex", gap: 6 }}>
                <input
                  style={{ ...S.input, flex: 1 }}
                  value={edit.pass}
                  onChange={(e) => setEdit({ ...edit, pass: e.target.value })}
                />
                <Btn
                  kind="soft"
                  sm
                  onClick={() => setEdit({ ...edit, pass: genPass() })}
                >
                  🎲
                </Btn>
              </div>
            </div>
          </div>
          {/* সপ্তাহে কোন কোন বার পড়বে — দিন-সংখ্যা ফি ও রুটিনে ব্যবহৃত */}
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>
              সপ্তাহে কোন কোন বার পড়বে ({bn((edit.days || []).length)} দিন)
            </label>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {WEEK_ORDER.map((wd) => {
                const on = (edit.days || []).includes(wd);
                return (
                  <button
                    key={wd}
                    type="button"
                    onClick={() =>
                      setEdit({
                        ...edit,
                        days: on
                          ? (edit.days || []).filter((d) => d !== wd)
                          : [...(edit.days || []), wd],
                      })
                    }
                    style={{
                      padding: "8px 12px",
                      borderRadius: 99,
                      cursor: "pointer",
                      fontFamily: "inherit",
                      fontWeight: 700,
                      fontSize: 12.5,
                      border: `2px solid ${on ? C.emerald : C.line}`,
                      background: on ? C.greenBg : "#fff",
                      color: on ? C.emerald : C.text,
                    }}
                  >
                    {DAY_BN[wd]}
                  </button>
                );
              })}
            </div>
            <div style={{ fontSize: 11.5, color: C.muted, marginTop: 5 }}>
              💡 দিনের সংখ্যা অনুযায়ী ফি নির্ধারণ ও রুটিন তৈরিতে কাজে লাগবে।
            </div>
          </div>
          {/* ⚠️ আগে এখানে শর্ত ছিল {!edit.id && …} — অর্থাৎ কোর্স ও উস্তাদের
              ঘর দুটো কেবল নতুন স্টুডেন্ট তৈরির সময় দেখাত। পুরনো কারও
              এডিটে ঘর দুটো একেবারে লুকানো থাকত, তাই একবার বসিয়ে দিলে আর
              দেখাও যেত না, বদলানোও যেত না। এখন সবসময় দেখায়। */}
          <div
            style={{
              marginTop: 10,
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
            }}
          >
              <div>
                <label style={S.label}>📚 কী পড়ে (কোর্স)</label>
                <select
                  style={S.input}
                  value={edit.courseId || ""}
                  onChange={(e) => {
                    const cid = e.target.value;
                    const c = courseList.find(
                      (x) => String(x.id) === String(cid),
                    );
                    // কোর্স বাছলে উস্তাদ অটো বসে — কিন্তু কেবল তখনই, যখন
                    // শিক্ষার্থীর নিজের কোনো উস্তাদ এখনো বসানো হয়নি।
                    // আগে শর্তহীনভাবে বসত, ফলে কোর্স বদলাতে গেলেই
                    // পরিচালকের বসানো উস্তাদ চাপা পড়ে যেত।
                    setEdit({
                      ...edit,
                      courseId: cid,
                      teacherId: edit.teacherId || c?.teacherId || "",
                    });
                  }}
                >
                  <option value="">— কোর্স নির্বাচন করুন —</option>
                  {courseList.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label style={S.label}>
                  👳 কার কাছে পড়ে (উস্তাদ/উস্তাদা)
                  <span
                    style={{ color: C.muted, fontWeight: 600, fontSize: 11.5 }}
                  >
                    {" "}
                    — কেবল এই শিক্ষার্থীর
                  </span>
                </label>
                <select
                  style={S.input}
                  value={edit.teacherId || ""}
                  onChange={(e) =>
                    setEdit({ ...edit, teacherId: e.target.value })
                  }
                >
                  <option value="">— উস্তাদ/উস্তাদা নির্বাচন করুন —</option>
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                      {t.sub ? ` (${t.sub})` : ""}
                    </option>
                  ))}
                </select>
                {/* ⚠️ কোর্স বদলালেও শিক্ষার্থীর নিজস্ব উস্তাদ নিজে থেকে বদলায়
                    না (ইচ্ছাকৃত — এক কোর্সে একাধিক উস্তাদ থাকতে পারেন)। কিন্তু
                    নতুন কোর্সের সাথে এই উস্তাদের কোনো সম্পর্ক না থাকলে তিনি
                    শিক্ষার্থীকে নিজের তালিকায় দেখতেই পাবেন না — সেটাই এখানে
                    আগেভাগে জানিয়ে দেওয়া হয়। */}
                {edit.courseId &&
                  edit.teacherId &&
                  !teacherLinkedToCourse(edit.courseId, edit.teacherId) && (
                    <div
                      style={{
                        marginTop: 6,
                        padding: "7px 9px",
                        borderRadius: 8,
                        background: C.amberBg,
                        border: `1px solid ${C.goldL}`,
                        fontSize: 11.5,
                        lineHeight: 1.6,
                        color: "#8a5a00",
                      }}
                    >
                      ⚠️ এই উস্তাদ বাছাই করা কোর্সটির সাথে যুক্ত নন। এভাবে
                      সংরক্ষণ করলে <b>তিনি এই শিক্ষার্থীকে নিজের তালিকায়
                      দেখতে পাবেন</b> (কারণ শিক্ষার্থী তাঁর কাছেই পড়ে), তবে{" "}
                      <b>কোর্সের অন্য উস্তাদ দেখবেন না</b>। ইচ্ছা করে এমন
                      চাইলে ঠিক আছে।
                    </div>
                  )}
              </div>
          </div>
          <Btn
            style={{
              marginTop: 16,
              width: "100%",
              justifyContent: "center",
              opacity: saving ? 0.7 : 1,
            }}
            onClick={saveEdit}
          >
            {saving
              ? "সংরক্ষণ হচ্ছে…"
              : edit.id
                ? "✏️ সংরক্ষণ করুন"
                : "+ যোগ করুন"}
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ উস্তাদ-ভিত্তিক বোর্ড — কার কাছে কে পড়ে, সামনের ক্লাস, স্থগিত করার ক্ষমতা ═══════════════ */
function TeacherWiseBoard({ db, setDb, user }) {
  const [allTeachers, setAllTeachers] = useState([]);
  const [sel, setSel] = useState(
    user.role === "teacher" ? user.id : allTeachers[0]?.id,
  );
  const [routines, setRoutines] = useState(db.routine || []);
  const [upcomingAll, setUpcomingAll] = useState([]);
  // একটি নির্দিষ্ট আসন্ন ক্লাস ম্যানুয়ালি এডিট (তারিখ/সময়/সময়কাল/জুম লিংক) —
  // পুরো রুটিন না বদলে শুধু ওই একটা দিনের ক্লাস সরানো/বদলানোর জন্য
  const [editK, setEditK] = useState(null); // {id, date, time, dur, zoom}
  const [savingK, setSavingK] = useState(false);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে

  useEffect(() => {
    // উস্তাদ-তালিকা (এডমিন/পরিচালক) — ব্যর্থ হলেও routines/classes লোড থামবে না
    if (user.role !== "teacher")
      api
        .allTeachers()
        .then((d) => {
          if (d.length)
            setAllTeachers(
              d.map((u) => ({
                id: u.id,
                name: u.name || u.name_bn,
                role: "teacher",
              })),
            );
        })
        .catch(() => {});
    Promise.all([api.routines(), api.classes()])
      .then(([routData, classData]) => {
        setRoutines(
          routData.map((r) => ({
            ...r,
            courseId: r.course ?? r.courseId,
            // শিক্ষার্থীর নিজের উস্তাদ আগে; না থাকলে কোর্সের উস্তাদ
            teacherId: r.teacher ?? r.teacherId,
            teacherName: r.teacher_name || "",
            studentIds: r.students || r.studentIds || [],
            studentNames: r.student_names || [],
            days: r.days || [],
          })),
        );
        setUpcomingAll(
          classData.filter(
            (k) => (k.date || "") >= todayISO() && k.status === "upcoming",
          ),
        );
      })
      .catch(() => {
        setRoutines(db.routine || []);
        setUpcomingAll(
          db.classes.filter(
            (k) => k.date >= todayISO() && k.status === "upcoming",
          ),
        );
      })
      .finally(() => setLoading(false));
  }, []);

  const tid = user.role === "teacher" ? user.id : sel || allTeachers[0]?.id;
  const t =
    allTeachers.find((x) => String(x.id) === String(tid)) || userById(tid);
  const myRoutines = routines.filter(
    (r) =>
      String(r.teacherId || courseById(COURSES, r.courseId)?.teacherId) ===
      String(tid),
  );
  const upcoming = upcomingAll
    .filter(
      (k) =>
        String(
          k.teacher ||
            k.teacherId ||
            courseById(COURSES, k.course || k.courseId)?.teacherId,
        ) === String(tid),
    )
    .sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
    .slice(0, 6);

  const startEditClass = (k) =>
    setEditK({
      id: k.id,
      date: k.date,
      time: (k.time || "").slice(0, 5), // "17:00:00" → "17:00"
      dur: k.duration_min || k.dur || 60,
      zoom: k.zoom_link || k.zoom || "",
    });
  const saveEditClass = async () => {
    if (!editK.date || !editK.time) return notice("তারিখ ও সময় দিন।");
    setSavingK(true);
    try {
      await api.editClass(editK.id, {
        date: editK.date,
        time: editK.time,
        duration_min: +editK.dur || 60,
        zoom_link: editK.zoom,
      });
      // সার্ভারে সেভ হওয়ার পর তালিকাটাও হালনাগাদ করি, যাতে সাথে সাথেই নতুন
      // তারিখ-সময় দেখা যায় (রিফ্রেশের অপেক্ষা না করে)
      setUpcomingAll((prev) =>
        prev.map((x) =>
          x.id === editK.id
            ? {
                ...x,
                date: editK.date,
                time: editK.time,
                duration_min: +editK.dur || 60,
                zoom_link: editK.zoom,
              }
            : x,
        ),
      );
      setEditK(null);
      notice("✔ ক্লাসটি আপডেট হয়েছে — উস্তাদ ও স্টুডেন্টের পোর্টালেও বদলে গেছে।");
    } catch (e) {
      notice(
        "ক্লাস আপডেট করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    }
    setSavingK(false);
  };
  const postpone = (k) =>
    askConfirm(
      "ক্লাসটি স্থগিত করবেন? উস্তাদ, স্টুডেন্ট সবার পোর্টালে সাথে সাথে আপডেট হবে এবং অভিভাবকের WhatsApp মেসেজ তৈরি হবে।",
      async () => {
        try {
          await api.postponeClass(k.id);
          setUpcomingAll((prev) => prev.filter((x) => x.id !== k.id));
        } catch {
          const c = courseById(COURSES, k.courseId);
          const studs =
            (k.studentIds && k.studentIds.length
              ? k.studentIds
              : c.studentIds) || [];
          setDb((d) => ({
            ...d,
            classes: d.classes.map((x) =>
              x.id === k.id ? { ...x, status: "postponed" } : x,
            ),
            waOutbox: [
              ...waGuardianMsgs(k, c, "postpone"),
              ...(d.waOutbox || []),
            ],
            notifications: [
              {
                id: uid(),
                for: [tid, ...studs, "admin1", "dir1"],
                text: `⛔ ${c.name} ক্লাসটি (${fmtDate(k.date)}, ${k.time}) স্থগিত করা হয়েছে।`,
                date: todayISO(),
                read: false,
              },
              ...d.notifications,
            ],
          }));
          setUpcomingAll((prev) => prev.filter((x) => x.id !== k.id));
        }
      },
    );
  if (user.role === "student") return null;
  return (
    <div style={{ ...S.card, marginBottom: 16 }}>
      <div style={{ fontWeight: 800, marginBottom: 10 }}>
        👳 উস্তাদ-ভিত্তিক রুটিন ও ক্লাস
      </div>
      {user.role !== "teacher" && (
        <div
          style={{
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
            marginBottom: 12,
          }}
        >
          {allTeachers.map((x) => (
            <Btn
              key={x.id}
              sm
              kind={String(tid) === String(x.id) ? "primary" : "soft"}
              onClick={() => setSel(x.id)}
            >
              {x.name}
            </Btn>
          ))}
        </div>
      )}
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          marginBottom: 6,
          color: C.emerald,
        }}
      >
        📚 {t.name}-এর কাছে যারা পড়ে:
      </div>
      {loading && <Loader text="লোড হচ্ছে" />}
      {!loading && myRoutines.length === 0 && (
        <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 8 }}>
          এখনো রুটিন নেই
        </div>
      )}
      {myRoutines.map((r) => {
        const c = courseById(COURSES, r.courseId || r.course);
        const studs = r.studentIds || r.students || c.studentIds || [];
        const names =
          r.studentNames && r.studentNames.length
            ? r.studentNames
            : studs.map((s) => userById(s)?.name || "স্টুডেন্ট " + s);
        return (
          <div
            key={r.id}
            style={{
              padding: "8px 12px",
              borderRadius: 10,
              background: C.cream,
              marginBottom: 6,
              fontSize: 12.5,
            }}
          >
            👥{" "}
            {studs.length ? (
              studs.map((sid, i) => (
                <span key={sid} style={{ display: "inline-flex", alignItems: "center", gap: 3 }}>
                  <b>{names[i] || "স্টুডেন্ট " + sid}</b>
                  <RemarkBox studentId={sid} studentName={names[i] || "স্টুডেন্ট " + sid} />
                  {i < studs.length - 1 ? <span>,&nbsp;</span> : null}
                </span>
              ))
            ) : (
              <b>—</b>
            )}{" "}
            — {c.name || r.course_name || "—"} ·{" "}
            {(r.days || [])
              .map((i) => `${DAY_BN[i]} ${r.time}`)
              .join(", ")}
          </div>
        );
      })}
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          margin: "10px 0 6px",
          color: C.emerald,
        }}
      >
        📅 সামনের ক্লাস:
      </div>
      {!loading && upcoming.length === 0 && (
        <div style={{ fontSize: 12.5, color: C.muted }}>
          আসন্ন কোনো ক্লাস নেই
        </div>
      )}
      {upcoming.map((k) => {
        const c = courseById(COURSES, k.courseId || k.course);
        const studs = k.studentIds || k.students || c.studentIds || [];
        const studentNames =
          k.student_names && k.student_names.length
            ? k.student_names.map((n) => n.split(" ")[0]).join(", ")
            : studs
                .map((s) => (userById(s)?.name || "ছাত্র " + s).split(" ")[0])
                .join(", ");
        return (
          <div
            key={k.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 12px",
              borderRadius: 10,
              background: C.greenBg,
              marginBottom: 6,
              fontSize: 12.5,
              flexWrap: "wrap",
            }}
          >
            <span style={{ flex: 1, minWidth: 200 }}>
              <b>{k.course_name || c.name || "—"}</b> ·{" "}
              {fmtDate(k.date)} · 🕐 {(k.time || "").slice(0, 5)} · 👥{" "}
              {studentNames}
            </span>
            {isAdm(user) && (
              <Btn sm kind="soft" onClick={() => startEditClass(k)}>
                ✏️ এডিট
              </Btn>
            )}
            {isAdm(user) && (
              <Btn sm kind="danger" onClick={() => postpone(k)}>
                ⛔ স্থগিত করুন
              </Btn>
            )}
          </div>
        );
      })}
      {editK && (
        <Modal
          title="✏️ এই ক্লাসটি এডিট করুন"
          onClose={() => setEditK(null)}
        >
          <div
            style={{
              padding: "9px 12px",
              borderRadius: 10,
              background: C.amberBg,
              fontSize: 12,
              color: "#a16207",
              marginBottom: 12,
            }}
          >
            💡 এটা শুধু এই একটা দিনের ক্লাস বদলাবে — পুরো রুটিন অপরিবর্তিত
            থাকবে। তবে পরে রুটিনের সময়/বার এডিট করলে এই পরিবর্তন রুটিনের
            মান দিয়ে আবার বদলে যাবে।
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div>
              <label style={S.label}>তারিখ</label>
              <input
                type="date"
                style={S.input}
                value={editK.date}
                onChange={(e) => setEditK({ ...editK, date: e.target.value })}
              />
            </div>
            <div>
              <label style={S.label}>সময় (বাংলাদেশ সময় 🇧🇩)</label>
              <input
                type="time"
                style={S.input}
                value={editK.time}
                onChange={(e) => setEditK({ ...editK, time: e.target.value })}
              />
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>সময়কাল (মিনিট)</label>
            <input
              type="number"
              style={S.input}
              value={editK.dur}
              onChange={(e) => setEditK({ ...editK, dur: e.target.value })}
            />
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>জুম লিংক</label>
            <input
              style={S.input}
              value={editK.zoom}
              onChange={(e) => setEditK({ ...editK, zoom: e.target.value })}
            />
          </div>
          <Btn
            style={{
              marginTop: 16,
              width: "100%",
              justifyContent: "center",
              opacity: savingK ? 0.6 : 1,
            }}
            onClick={saveEditClass}
          >
            {savingK ? "⏳ সেভ হচ্ছে…" : "✔ আপডেট করুন"}
          </Btn>
        </Modal>
      )}
    </div>
  );
}

/* ═══════════════ WhatsApp মেসেজ আউটবক্স — অভিভাবকের কাছে অটো-প্রস্তুত মেসেজ ═══════════════ */
function WaOutboxView({ db, setDb, user }) {
  const [waList, setWaList] = useState(db.waOutbox || []);
  const [loading, setLoading] = useState(true); // প্রথম লোড শেষ হওয়ার আগে "কিছু নেই" না দেখাতে
  const cfg = db.waConfig || { backendUrl: "", autoSend: false };
  const setCfg = (patch) =>
    setDb((d) => ({ ...d, waConfig: { ...(d.waConfig || {}), ...patch } }));

  const adaptMsg = (m) => ({
    id: m.id,
    toName: m.to_name || m.toName,
    phone: m.phone,
    student: m.to_name || m.student,
    reason: m.reason,
    text: m.text,
    date: m.created_at || m.date,
    sent: m.sent || m.status === "sent",
    apiStatus: m.status || (m.sent ? "sent" : "pending"),
  });
  const loadData = async () => {
    try {
      setWaList((await api.waOutbox()).map(adaptMsg));
    } catch {
      setWaList(db.waOutbox || []);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const list = waList;
  const sendViaApi = async (m) => {
    try {
      setWaList((prev) =>
        prev.map((x) => (x.id === m.id ? { ...x, apiStatus: "sending" } : x)),
      );
      await api.waSendNow(m.id);
      await loadData();
    } catch {
      setWaList((prev) =>
        prev.map((x) => (x.id === m.id ? { ...x, apiStatus: "failed" } : x)),
      );
    }
  };
  const markSent = (id) =>
    setWaList((prev) =>
      prev.map((m) => (m.id === id ? { ...m, sent: true } : m)),
    );
  return (
    <Section
      title="WhatsApp মেসেজ"
      sub="ক্লাস শুরুর ৫ মিনিট আগের রিমাইন্ডার ও স্থগিতের মেসেজ অভিভাবকের জন্য স্বয়ংক্রিয়ভাবে তৈরি হয় — API চালু থাকলে নিজে নিজেই চলে যায়"
    >
      {isDir(user) && (
        <div
          style={{
            ...S.card,
            marginBottom: 14,
            borderLeft: `4px solid #25D366`,
          }}
        >
          <div style={{ fontWeight: 800, marginBottom: 4 }}>
            ⚙️ WhatsApp Business API সংযোগ (Twilio / Meta)
          </div>
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>
            সাথে দেওয়া ব্যাকএন্ড সার্ভারটি (whatsapp-server.js) ডেপ্লয় করে তার
            URL এখানে দিন — তারপর অটো-সেন্ড চালু করলেই মেসেজ সরাসরি অভিভাবকের
            WhatsApp-এ চলে যাবে। API কী/টোকেন ব্যাকএন্ডের .env ফাইলে থাকবে,
            এখানে নয় (নিরাপত্তার জন্য)।
          </div>
          <div
            style={{
              display: "flex",
              gap: 10,
              flexWrap: "wrap",
              alignItems: "center",
            }}
          >
            <input
              style={{ ...S.input, flex: 1, minWidth: 220 }}
              value={cfg.backendUrl}
              onChange={(e) => setCfg({ backendUrl: e.target.value })}
              placeholder="ব্যাকএন্ড URL — যেমন: https://tqa-whatsapp.onrender.com"
            />
            <label
              style={{
                display: "flex",
                gap: 8,
                alignItems: "center",
                fontSize: 13,
                fontWeight: 700,
                cursor: "pointer",
                padding: "9px 14px",
                borderRadius: 10,
                background: cfg.autoSend ? C.greenBg : C.cream,
                border: `1.5px solid ${cfg.autoSend ? C.green : C.line}`,
              }}
            >
              <input
                type="checkbox"
                checked={cfg.autoSend}
                onChange={(e) => setCfg({ autoSend: e.target.checked })}
              />
              ⚡ অটো-সেন্ড {cfg.autoSend ? "চালু" : "বন্ধ"}
            </label>
          </div>
          {cfg.autoSend && !cfg.backendUrl && (
            <div style={{ fontSize: 12, color: C.red, marginTop: 6 }}>
              ⚠️ অটো-সেন্ড চালু কিন্তু ব্যাকএন্ড URL দেওয়া হয়নি।
            </div>
          )}
        </div>
      )}
      <div style={{ display: "grid", gap: 10 }}>
        {loading && <Loader text="মেসেজ লোড হচ্ছে" />}
        {!loading && list.length === 0 && (
          <div style={{ ...S.card, color: C.muted, textAlign: "center" }}>
            এখনো কোনো মেসেজ তৈরি হয়নি — ক্লাস শুরুর ৫ মিনিট আগে বা ক্লাস স্থগিত
            করলে এখানে অটো চলে আসবে।
          </div>
        )}
        {list.map((m) => (
          <div
            key={m.id}
            style={{
              ...S.card,
              padding: 14,
              borderLeft: `4px solid ${m.sent ? C.green : m.reason === "ক্লাস স্থগিত" ? C.red : C.gold}`,
            }}
          >
            <div
              style={{
                display: "flex",
                gap: 10,
                alignItems: "flex-start",
                flexWrap: "wrap",
              }}
            >
              <div style={{ flex: 1, minWidth: 220 }}>
                <b style={{ fontSize: 13.5 }}>{m.toName}</b>{" "}
                <Tag
                  color={m.reason === "ক্লাস স্থগিত" ? C.red : C.gold}
                  bg={m.reason === "ক্লাস স্থগিত" ? C.redBg : C.amberBg}
                >
                  {m.reason}
                </Tag>{" "}
                {m.sent && (
                  <Tag>
                    পাঠানো হয়েছে ✔{m.apiStatus === "sent" ? " (API)" : ""}
                  </Tag>
                )}
                {m.apiStatus === "sending" && (
                  <Tag color={C.blue} bg={C.blueBg}>
                    ⏳ API দিয়ে যাচ্ছে...
                  </Tag>
                )}
                {m.apiStatus === "failed" && (
                  <Tag color={C.red} bg={C.redBg}>
                    API ব্যর্থ — সার্ভার/নম্বর যাচাই করুন
                  </Tag>
                )}
                <div style={{ fontSize: 11.5, color: C.muted }}>
                  শিক্ষার্থী: {m.student} · +{m.phone} · {fmtDate(m.date)}
                </div>
                <div
                  style={{
                    fontSize: 12.5,
                    marginTop: 6,
                    background: C.cream,
                    padding: "8px 10px",
                    borderRadius: 8,
                  }}
                >
                  {m.text}
                </div>
              </div>
              <span
                style={{ display: "flex", flexDirection: "column", gap: 6 }}
              >
                {!m.sent && cfg.backendUrl && (
                  <Btn sm onClick={() => sendViaApi(m)}>
                    🚀 API দিয়ে পাঠান
                  </Btn>
                )}
                <a
                  href={`https://wa.me/${m.phone}?text=${encodeURIComponent(m.text)}`}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => markSent(m.id)}
                  style={{ textDecoration: "none" }}
                >
                  <Btn sm style={{ background: "#25D366", color: "#fff" }}>
                    📱 ম্যানুয়াল (wa.me)
                  </Btn>
                </a>
              </span>
            </div>
          </div>
        ))}
      </div>
      <div
        style={{
          marginTop: 12,
          padding: "10px 12px",
          borderRadius: 10,
          background: C.blueBg,
          fontSize: 12,
          color: C.blue,
        }}
      >
        ℹ️ API সংযুক্ত থাকলে (উপরের সেটিংস) মেসেজ তৈরি হওয়ামাত্র সার্ভার
        Twilio/Meta-র মাধ্যমে সরাসরি অভিভাবকের WhatsApp-এ পাঠিয়ে দেয়। সেটআপ
        গাইড: whatsapp-setup.md ফাইলটি দেখুন। API ছাড়া ম্যানুয়াল (wa.me) বাটন
        তো আছেই।
      </div>
    </Section>
  );
}

/* ═══════════════ কোর্স ব্যবস্থাপনা — কেবল পরিচালক; যোগ/এডিট/বাদ এখান থেকেই সর্বত্র কার্যকর ═══════════════ */
function CourseManagerView({ db, setDb, refresh }) {
  const [edit, setEdit] = usePersistedState("crs_edit", null); // null=বন্ধ, {}=নতুন, {id}=এডিট
  const PALETTE = [C.emerald, C.gold, C.blue, C.red, "#7c3aed", "#0f766e"];
  const [courses, setCourses] = useState(COURSES);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [academicBooks, setAcademicBooks] = useState([]); // API থেকে লোড
  const [bookForm, setBookForm] = useState(null); // {name, fileObj, file} — ইনলাইন বই যোগ

  const BASE_MEDIA = (
    import.meta.env?.VITE_API_URL || "http://localhost:8000/api"
  ).replace(/\/api$/, "");
  const adaptBook = (b) => {
    const fileUrl = b.file
      ? b.file.startsWith("http")
        ? b.file
        : BASE_MEDIA + b.file
      : null;
    const fname = fileUrl ? fileUrl.split("/").pop() : b.name + ".pdf";
    return { id: b.id, name: b.name, file: { name: fname } };
  };

  // ব্যাকএন্ড থেকে কোর্স + উস্তাদ + বই তালিকা লোড
  const loadCourses = async () => {
    setLoading(true);
    try {
      const [cs, us, bks] = await Promise.all([
        api.courses(),
        api.allUsers(),
        api.books(),
      ]);
      const lecLists = await Promise.all(
        cs.map((c) =>
          api
            .lectures(c.id)
            .then((d) => (d || []).map(adaptLecture))
            .catch(() => []),
        ),
      );
      setCourses(
        cs.map((c, i) => ({
          id: c.id,
          name: c.name,
          teacherId: c.teacher,
          teacherName: c.teacher_name,
          color: c.color,
          books: c.books || [],
          studentIds: c.students || [],
          studentCount: c.student_count,
          lectures: lecLists[i],
        })),
      );
      setTeachers(
        us
          .filter((u) => u.role === "teacher")
          .map((t) => ({
            id: t.id,
            name: t.name || t.name_bn,
            sub: t.sub || t.sub_title || "",
          })),
      );
      setAcademicBooks(bks.map(adaptBook));
    } catch {
      setCourses(COURSES);
      setTeachers(USERS.filter((u) => u.role === "teacher"));
      setAcademicBooks([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadCourses();
  }, []);

  const save = async () => {
    if (!edit.name?.trim()) return notice("কোর্সের নাম দিন।");
    // সার্ভার teacher হিসেবে কেবল role="teacher" ব্যবহারকারীকেই গ্রহণ করে, আর
    // books হিসেবে কেবল বিদ্যমান একাডেমিক বই। কোনো উস্তাদের রোল বদলে গেলে বা
    // কোনো বই মুছে গেলে কোর্সে তার পুরনো আইডি রয়ে যেত, আর সেভ করতে গেলে
    // দুর্বোধ্য 'Invalid pk "3" - object does not exist' আসত। এখন পাঠানোর
    // আগেই যাচাই করে স্পষ্ট বাংলা বার্তা দেখানো হয়।
    if (!teachers.some((t) => String(t.id) === String(edit.teacherId))) {
      return notice(
        "দায়িত্বপ্রাপ্ত উস্তাদ/উস্তাদা বেছে নিন — আগে যিনি ছিলেন তিনি এখন আর উস্তাদ তালিকায় নেই (তাঁর রোল বদলে থাকতে পারে)।",
      );
    }
    const validBookIds = new Set(academicBooks.map((b) => String(b.id)));
    const books = (edit.books || []).filter((id) => validBookIds.has(String(id)));
    setSaving(true);
    try {
      const payload = {
        name: edit.name,
        teacher: edit.teacherId,
        color: edit.color,
        books,
      };
      await api.saveCourse(payload, edit.id || undefined);
      await loadCourses();
      setEdit(null);
      notice(edit.id ? "✔ কোর্স আপডেট হয়েছে।" : "✔ কোর্স তৈরি হয়েছে।");
      refresh();
    } catch (e) {
      notice(
        "কোর্স সেভ করতে ব্যর্থ — " +
          (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
      );
    } finally {
      setSaving(false);
    }
  };

  // ইনলাইন বই আপলোড → তালিকা রিলোড → নতুন বই অটো-নির্বাচন
  const saveNewBook = async () => {
    if (!bookForm.name.trim()) return notice("বইয়ের নাম লিখুন।");
    if (!(bookForm.fileObj instanceof File))
      return notice("ডিভাইস থেকে বইয়ের ফাইল যুক্ত করুন।");
    try {
      await api.uploadBook(bookForm.name.trim(), bookForm.fileObj);
      const bks = (await api.books()).map(adaptBook);
      setAcademicBooks(bks);
      const found = bks.find((b) => b.name === bookForm.name.trim());
      if (found && edit) {
        setEdit((prev) => {
          const cur = prev.books || [];
          if (cur.includes(found.id)) return prev;
          return { ...prev, books: [...cur, found.id] };
        });
      }
      setBookForm(null);
      notice("বই যোগ হয়েছে এবং স্বয়ংক্রিয়ভাবে নির্বাচিত হয়েছে।");
    } catch (e) {
      notice(
        "বই যোগ ব্যর্থ: " + (e?.data?.error || e?.message || "অজানা সমস্যা"),
      );
    }
  };

  const del = (c) =>
    askConfirm(
      `"${c.name}" কোর্সটি মুছে ফেলবেন? এর ক্লাস ও রুটিনও সরে যাবে এবং কোথাও আর দেখা যাবে না।`,
      async () => {
        try {
          await api.deleteCourse(c.id);
          await loadCourses();
          notice(`✔ "${c.name}" কোর্স মুছে ফেলা হয়েছে।`);
          refresh();
        } catch (e) {
          notice(
            "কোর্স মুছতে ব্যর্থ — " +
              (e?.data?.error || e?.message || "সার্ভার সংযোগ যাচাই করে আবার চেষ্টা করুন"),
          );
        }
      },
    );
  return (
    <Section
      title="কোর্স ব্যবস্থাপনা"
      sub="নতুন কোর্স যোগ, এডিট ও বাদ — কেবল পরিচালকের নিয়ন্ত্রণে; এখানকার তালিকাই সর্বত্র (রুটিন, শিডিউল, লেকচার প্ল্যান, ভর্তি ফরম) দেখা যায়"
      action={
        <Btn
          onClick={() =>
            setEdit({
              name: "",
              teacherId: teachers[0]?.id,
              color: PALETTE[0],
              books: [],
            })
          }
        >
          + নতুন কোর্স
        </Btn>
      }
    >
      {loading && <Loader text="কোর্স তালিকা আসছে" />}
      <div style={{ display: "grid", gap: 10 }}>
        {courses.map((c) => (
          <div
            key={c.id}
            style={{
              ...S.card,
              padding: 16,
              borderLeft: `4px solid ${c.color || C.emerald}`,
              display: "flex",
              gap: 12,
              alignItems: "center",
              flexWrap: "wrap",
            }}
          >
            <div style={{ flex: 1, minWidth: 220 }}>
              <div style={{ fontWeight: 800, fontSize: 15 }}>{c.name}</div>
              <div style={{ fontSize: 12.5, color: C.muted }}>
                উস্তাদ: {c.teacherName || userById(c.teacherId).name || "—"} ·
                শিক্ষার্থী:{" "}
                {bn(
                  c.studentCount != null
                    ? c.studentCount
                    : c.studentIds?.length || 0,
                )}{" "}
                জন · বই: {bn((c.books || []).length)}টি
                {/* "লেকচার: Nটি" সরানো হলো — দারস এখন কেবল লুকানো ধারক
                    (কোর্স-প্রতি একটিই), তাই সংখ্যাটা সবসময় ১ দেখাত এবং
                    কিছুই বোঝাত না। টপিকের হিসাব দারস পরিকল্পনা পাতাতেই আছে। */}
              </div>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <Btn
                sm
                kind="soft"
                onClick={() =>
                  setEdit({
                    id: c.id,
                    name: c.name,
                    teacherId: c.teacherId,
                    color: c.color || C.emerald,
                    books: [...(c.books || [])],
                  })
                }
              >
                ✏️ এডিট
              </Btn>
              <Btn sm kind="danger" onClick={() => del(c)}>
                🗑 বাদ দিন
              </Btn>
            </div>
          </div>
        ))}
      </div>
      {edit && (
        <Modal
          title={
            edit.id ? `✏️ কোর্স এডিট — ${edit.name}` : "+ নতুন কোর্স যোগ করুন"
          }
          onClose={() => {
            setEdit(null);
            setBookForm(null);
          }}
          wide
        >
          <label style={S.label}>কোর্সের নাম</label>
          <input
            style={S.input}
            value={edit.name}
            onChange={(e) => setEdit({ ...edit, name: e.target.value })}
            placeholder="যেমন: সহীহ মাসনুন দুআ কোর্স"
          />
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>দায়িত্বপ্রাপ্ত উস্তাদ/উস্তাদা</label>
            <select
              style={S.input}
              value={
                // পুরনো উস্তাদ তালিকায় না থাকলে (রোল বদলে গেলে) ফাঁকা দেখাবে —
                // নইলে ব্রাউজার প্রথম নামটা দেখাত অথচ ভেতরে পুরনো অবৈধ আইডিই
                // থেকে যেত, আর সেভ করতে গিয়ে দুর্বোধ্য এরর আসত
                teachers.some((t) => String(t.id) === String(edit.teacherId))
                  ? edit.teacherId
                  : ""
              }
              onChange={(e) => setEdit({ ...edit, teacherId: e.target.value })}
            >
              <option value="">— বেছে নিন —</option>
              {teachers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.sub})
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 10 }}>
            <label style={S.label}>রং</label>
            <div style={{ display: "flex", gap: 8 }}>
              {PALETTE.map((p) => (
                <button
                  key={p}
                  onClick={() => setEdit({ ...edit, color: p })}
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: 10,
                    cursor: "pointer",
                    background: p,
                    border:
                      edit.color === p ? "3px solid #1a1f2e" : "2px solid #fff",
                    boxShadow: "0 1px 4px rgba(0,0,0,.2)",
                  }}
                />
              ))}
            </div>
          </div>

          {/* ── একাডেমিক বই সিলেকশন + ইনলাইন আপলোড ── */}
          <div style={{ marginTop: 12 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 6,
              }}
            >
              <label style={{ ...S.label, marginBottom: 0 }}>
                📚 কোর্সের বই ({bn((edit.books || []).length)}টি নির্বাচিত)
              </label>
              {!bookForm && (
                <Btn
                  sm
                  kind="ghost"
                  onClick={() =>
                    setBookForm({ name: "", fileObj: null, file: null })
                  }
                >
                  + নতুন বই যোগ
                </Btn>
              )}
            </div>

            {/* ইনলাইন বই আপলোড ফর্ম */}
            {bookForm && (
              <div
                style={{
                  background: C.amberBg,
                  border: `1.5px solid ${C.goldL}`,
                  borderRadius: 12,
                  padding: 14,
                  marginBottom: 10,
                }}
              >
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: 13,
                    marginBottom: 8,
                    color: "#92400e",
                  }}
                >
                  📤 নতুন বই আপলোড করুন
                </div>
                <input
                  style={S.input}
                  value={bookForm.name}
                  onChange={(e) =>
                    setBookForm({ ...bookForm, name: e.target.value })
                  }
                  placeholder="বইয়ের নাম (যেমন: নুরানী কায়দা সংশোধিত)"
                />
                <label
                  style={{
                    display: "flex",
                    gap: 10,
                    alignItems: "center",
                    marginTop: 8,
                    padding: "9px 12px",
                    border: `1.5px dashed ${bookForm.file ? C.emerald : C.line}`,
                    borderRadius: 10,
                    cursor: "pointer",
                    background: "#fff",
                    fontSize: 13,
                  }}
                >
                  <span style={{ fontSize: 20 }}>
                    {bookForm.file ? "✅" : "📁"}
                  </span>
                  <span>
                    {bookForm.file
                      ? bookForm.file.name
                      : "ডিভাইস থেকে ফাইল বেছে নিন (PDF, DOC, JPG…)"}
                  </span>
                  <input
                    type="file"
                    style={{ display: "none" }}
                    onChange={(e) => {
                      const f = e.target.files[0];
                      if (f)
                        setBookForm({
                          ...bookForm,
                          fileObj: f,
                          file: { name: f.name },
                        });
                    }}
                  />
                </label>
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <Btn
                    sm
                    style={{ flex: 1, justifyContent: "center" }}
                    onClick={saveNewBook}
                  >
                    আপলোড ও নির্বাচন করুন
                  </Btn>
                  <Btn sm kind="soft" onClick={() => setBookForm(null)}>
                    বাতিল
                  </Btn>
                </div>
              </div>
            )}

            {/* বই তালিকা চেকবক্স */}
            {academicBooks.length === 0 ? (
              <div
                style={{
                  padding: "12px 14px",
                  borderRadius: 10,
                  background: C.cream,
                  fontSize: 12.5,
                  color: C.muted,
                  border: `1px dashed ${C.line}`,
                }}
              >
                📭 কোনো একাডেমিক বই নেই — উপরের "+ নতুন বই যোগ" বাটনে ক্লিক করে
                সরাসরি এখানেই বই আপলোড ও নির্বাচন করুন।
              </div>
            ) : (
              <div
                style={{
                  maxHeight: 190,
                  overflowY: "auto",
                  border: `1.5px solid ${C.line}`,
                  borderRadius: 10,
                  padding: 6,
                  background: "#fff",
                }}
              >
                {academicBooks.map((b) => {
                  const on = (edit.books || []).includes(b.id);
                  const full = false; // কোনো সীমা নেই — যত খুশি বই যোগ করা যাবে
                  return (
                    <label
                      key={b.id}
                      style={{
                        display: "flex",
                        gap: 8,
                        alignItems: "center",
                        padding: "7px 8px",
                        fontSize: 13,
                        cursor: full ? "not-allowed" : "pointer",
                        borderRadius: 8,
                        background: on ? C.greenBg : "transparent",
                        opacity: full ? 0.45 : 1,
                        transition: "background .12s",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={on}
                        disabled={full}
                        onChange={() =>
                          setEdit({
                            ...edit,
                            books: on
                              ? edit.books.filter((x) => x !== b.id)
                              : [...edit.books, b.id],
                          })
                        }
                      />
                      📖 <b>{b.name}</b>&nbsp;
                      <Tag color={C.blue} bg={C.blueBg}>
                        {bookExt(b.file?.name)}
                      </Tag>
                    </label>
                  );
                })}
              </div>
            )}
          </div>

          <Btn
            style={{
              marginTop: 16,
              width: "100%",
              justifyContent: "center",
              opacity: saving ? 0.7 : 1,
            }}
            onClick={save}
          >
            {saving
              ? "সংরক্ষণ হচ্ছে…"
              : edit.id
                ? "✏️ সংরক্ষণ করুন"
                : "+ কোর্স যোগ করুন — সর্বত্র দেখা যাবে"}
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ কোর্স সিলেবাস — ফরম-সারি কাঠামো · "+ সিলেবাস যোগ করুন" পুরো ফরমকে এক সারি হিসেবে নিচে জমা করে ═══════════════
   পরিচালক: সব কোর্স + যোগ/এডিট · এডমিন: সব কোর্স (শুধু দেখা) · উস্তাদ/স্টুডেন্ট: যুক্ত কোর্স (শুধু দেখা)
   সারি গ্রুপিং: একসাথে যোগ হওয়া আইটেমগুলো একই `order` মান পায় → নিচে এক সারিতে দেখায় (নতুন migration লাগে না) */
function SyllabusView({ db, setDb, courses, user }) {
  /* পরিচালক নিজের হাতে টেবিলের শিরোনাম ও ঘরগুলো লেখেন; উস্তাদ ও শিক্ষার্থীরা
     সেটাই ওয়েব পেজ/PDF-এর মতো দেখেন ও প্রিন্ট করতে পারেন।
     পুরনো "সিলেবাস যোগ করুন" ইনপুট সারিগুলো তুলে দেওয়া হয়েছে — তবে পুরনো
     তথ্য মোছা হয়নি: কোনো কোর্সের টেবিল প্রথমবার খুললে ব্যাকএন্ড সেই কোর্সের
     আগের সিলেবাস থেকেই টেবিলটা সাজিয়ে দেয় (views.py → _sheet_from_syllabus),
     তাই সব লেখা যেমন ছিল তেমনই থাকে, শুধু এখন এডিট করা যায়। */
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  const canEdit = isDir(user);
  const [courseList, setCourseList] = useState(courses);
  const [allBooks, setAllBooks] = useState(db.academicBooks || []);
  const [selCourse, setSelCourse] = useState(null);
  const [headers, setHeaders] = useState([]);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sheetLoading, setSheetLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  // ⚠️ শেয়ার করা courseById() হুবহু মিল (===) খোঁজে, কিন্তু <select> সবসময়
  // লেখা (string) দেয় আর API দেয় সংখ্যা — ফলে কোর্স বদলানো মাত্রই কোনো কোর্সই
  // "পাওয়া যেত না" এবং পুরো পাতাটা ফাঁকা হয়ে যেত। এখানে দুপাশকে লেখা বানিয়ে
  // মেলানো হয়। (courseById-এ হাত দিইনি — সেটা অন্য অনেক জায়গায় ব্যবহৃত।)
  const findCourse = (cid) =>
    courseList.find((c) => String(c.id) === String(cid)) || {};
  const bookNameOf = (id) => (allBooks.find((b) => b.id === id) || {}).name;
  const courseBooksOf = (cid) =>
    (findCourse(cid).books || []).map(bookNameOf).filter(Boolean);

  useEffect(() => {
    (async () => {
      try {
        const [cs, bks] = await Promise.all([api.courses(), api.books()]);
        const adapted = cs.map((c) => ({
          id: c.id,
          name: c.name,
          books: c.books || [],
          color: c.color,
        }));
        setCourseList(adapted);
        setSelCourse((prev) => prev || adapted[0]?.id || null);
        setAllBooks(bks);
      } catch (e) {
        setCourseList(courses);
        setAllBooks(db.academicBooks || []);
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line

  // কোর্স বদলালে সেই কোর্সের টেবিল আনি
  useEffect(() => {
    if (!selCourse) return;
    let alive = true;
    setSheetLoading(true);
    api
      .syllabusSheet(selCourse)
      .then((d) => {
        if (!alive) return;
        setHeaders(d.headers || []);
        setRows(d.rows || []);
        setDirty(false);
      })
      .catch((e) => {
        if (!alive) return;
        setHeaders([]);
        setRows([]);
        // কোড নম্বরটা সাথে দিই — নইলে সার্ভার HTML পাতা ফেরত দিলে (যেমন
        // ডিপ্লয় চলাকালীন ৪০৪) শুধু জেনেরিক "API error" দেখাত, আর কী ঘটেছে
        // তা বোঝার কোনো উপায় থাকত না
        const why =
          e?.data?.error ||
          e?.data?.detail ||
          (e?.status ? `সার্ভার সাড়া দিয়েছে কোড ${e.status}` : null) ||
          e?.message ||
          "আবার চেষ্টা করুন";
        notice(
          T(
            "সিলেবাস আনা যায়নি — " + why,
            "Couldn't load the syllabus — " + why,
          ),
        );
      })
      .finally(() => alive && setSheetLoading(false));
    return () => {
      alive = false;
    };
  }, [selCourse]); // eslint-disable-line

  const activeCourse = findCourse(selCourse);
  // একাধিক কোর্স থাকলে তবেই বাছাইয়ের মেনু দরকার
  const showPicker = courseList.length > 1;
  const cols = headers.length;

  // ── টেবিল বদলানো (কেবল পরিচালক) ──
  const touch = () => setDirty(true);
  const setHeader = (i, v) => {
    setHeaders((h) => h.map((x, j) => (j === i ? v : x)));
    touch();
  };
  const setCell = (r, c, v) => {
    setRows((rs) =>
      rs.map((row, i) => (i === r ? row.map((x, j) => (j === c ? v : x)) : row)),
    );
    touch();
  };
  const addRow = () => {
    setRows((rs) => [...rs, Array(Math.max(cols, 1)).fill("")]);
    touch();
  };
  const addCol = () => {
    if (cols >= 12) return notice("সর্বোচ্চ ১২টি কলাম রাখা যাবে।");
    setHeaders((h) => [...h, ""]);
    setRows((rs) => rs.map((r) => [...r, ""]));
    touch();
  };
  const delRow = (i) =>
    askConfirm("এই সারিটি মুছে ফেলবেন?", () => {
      setRows((rs) => rs.filter((_, j) => j !== i));
      touch();
    });
  const delCol = (i) =>
    askConfirm(
      `"${headers[i] || "নামহীন"}" কলামটি মুছে ফেলবেন? এই কলামের সব ঘরের লেখা চলে যাবে।`,
      () => {
        setHeaders((h) => h.filter((_, j) => j !== i));
        setRows((rs) => rs.map((r) => r.filter((_, j) => j !== i)));
        touch();
      },
    );

  const save = async () => {
    if (!selCourse) return;
    setSaving(true);
    try {
      await api.saveSyllabusSheet(selCourse, headers, rows);
      setDirty(false);
      notice("সিলেবাস সংরক্ষিত হয়েছে।");
    } catch (e) {
      notice(
        "সংরক্ষণ ব্যর্থ — " + (e?.data?.error || e?.message || "আবার চেষ্টা করুন"),
      );
    } finally {
      setSaving(false);
    }
  };

  const doPrint = () => {
    if (!activeCourse.id) return;
    openPrintDoc(
      sheetHTML(
        activeCourse.name,
        courseBooksOf(activeCourse.id),
        headers,
        rows,
        user.role === "student",
      ),
      `TQA-syllabus-${activeCourse.name || "course"}.html`,
    );
  };

  const roleNote = canEdit
    ? "শিরোনাম ও ঘরগুলো সরাসরি লিখুন — সংরক্ষণ করলে উস্তাদ ও শিক্ষার্থীদের পোর্টালেও একই টেবিল দেখাবে · যে কেউ প্রিন্ট/PDF করতে পারবে"
    : user.role === "teacher"
      ? "আপনি যে কোর্সগুলোতে পড়ান তার সিলেবাস (দেখা ও প্রিন্ট)"
      : "Your course syllabus (view & print)";

  // ঘরের রেখা গাঢ় সবুজ — আগে খুব হালকা ধূসর (#e5e9e5) ছিল বলে কোন লেখা
  // কোন ঘরের তা আলাদা করে বোঝা যেত না, বিশেষ করে ঘরে একাধিক লাইন থাকলে
  const gridLine = `1px solid ${C.emerald}`;
  const cellStyle = {
    border: gridLine,
    verticalAlign: "top",
    padding: canEdit ? 0 : "9px 10px",
    fontSize: 12.5,
    lineHeight: 1.6,
    wordWrap: "break-word",
  };

  return (
    <Section title={T("কোর্স সিলেবাস", "Course Syllabus")} sub={roleNote}>
      {loading && <Loader text={T("লোড হচ্ছে", "Loading")} />}
      {!loading && courseList.length === 0 && (
        <div
          style={{ ...S.card, textAlign: "center", color: C.muted, padding: 28 }}
        >
          📜{" "}
          {user.role === "teacher"
            ? "আপনি এখনো কোনো কোর্সে যুক্ত নন।"
            : user.role === "student"
              ? "You are not enrolled in any course yet."
              : "এখনো কোনো কোর্স তৈরি হয়নি।"}
        </div>
      )}

      {!loading && activeCourse.id && (
        <div style={{ ...S.card, padding: 0, overflow: "hidden" }}>
          {/* উপরের সবুজ বার — কোর্স বাছাই ও সংরক্ষণ।
              কোর্স একটাই হলে বাছাইয়ের মেনুর কোনো কাজ নেই, তাই দেখাই না
              (শিক্ষার্থীর পোর্টালে সাধারণত একটাই কোর্স থাকে)। তবে একাধিক
              কোর্স থাকলে মেনুটা থাকে — নইলে তিনি বাকিগুলো দেখতেই পেতেন না।
              পুরো বারটাই খালি হয়ে গেলে (এক কোর্সের শিক্ষার্থী) বারটাও দেখাই না। */}
          {(showPicker || canEdit) && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                flexWrap: "wrap",
                padding: "12px 16px",
                background: `linear-gradient(135deg, ${C.emeraldD}, ${C.emerald})`,
                color: "#fff",
              }}
            >
              {showPicker && (
                <>
                  <span style={{ fontWeight: 800, fontSize: 14 }}>
                    {T("কোর্স:", "Course:")}
                  </span>
                  <select
                    value={selCourse || ""}
                    onChange={(e) => setSelCourse(e.target.value)}
                    style={{
                      ...S.input,
                      background: "#123f28",
                      color: "#fff",
                      border: "1px solid rgba(255,255,255,.35)",
                      minWidth: 200,
                      flex: "0 1 auto",
                    }}
                  >
                    {courseList.map((c) => (
                      <option
                        key={c.id}
                        value={c.id}
                        style={{ background: "#123f28" }}
                      >
                        {c.name}
                      </option>
                    ))}
                  </select>
                </>
              )}
              <div style={{ flex: 1 }} />
              {canEdit && dirty && (
                <span style={{ fontSize: 12, fontWeight: 700, color: C.goldL }}>
                  ● অসংরক্ষিত পরিবর্তন
                </span>
              )}
              {canEdit && (
                <Btn
                  sm
                  kind="gold"
                  onClick={saving ? undefined : save}
                  style={{ opacity: saving ? 0.7 : 1 }}
                >
                  {saving ? "সংরক্ষণ হচ্ছে…" : "💾 সংরক্ষণ করুন"}
                </Btn>
              )}
            </div>
          )}

          {/* ছাপা কাগজের হুবহু লেআউট — হেডার + ব্যানার + মেটা + টেবিল */}
          <div
            style={{
              margin: 14,
              border: `2px solid ${C.emerald}`,
              borderRadius: 12,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                background: `linear-gradient(135deg, ${C.emeraldD}, ${C.emerald})`,
                color: "#fff",
                padding: "16px 22px",
                textAlign: "center",
                position: "relative",
              }}
            >
              {/* প্রিন্ট বাটন — এই ডিভের ডান-উপরের কোণে। ছাপার সময় এটা
                  কাগজে যায় না, কারণ ছাপা হয় আলাদা করে তৈরি করা পরিচ্ছন্ন
                  পাতা (sheetHTML), এই পর্দার অংশটা নয়। */}
              <div style={{ position: "absolute", top: 10, right: 12 }}>
                <Btn sm kind="soft" onClick={doPrint}>
                  {T("🖨️ প্রিন্ট / PDF", "🖨️ Print / PDF")}
                </Btn>
              </div>
              <div
                style={{
                  color: C.goldL,
                  fontSize: 13,
                  letterSpacing: 3,
                  fontFamily: "serif",
                  fontWeight: 700,
                }}
              >
                تربية القرآن
              </div>
              <div
                style={{ fontWeight: 800, fontSize: 21, margin: "4px 0 2px" }}
              >
                তারবিয়াতুল কুরআন একাডেমী
              </div>
              <div style={{ fontSize: 11.5, color: "#cfe6d8" }}>
                tarbiyatulquran.org · WhatsApp: +880 140 249 9027
              </div>
            </div>
            <div
              style={{
                background: C.gold,
                color: "#fff",
                textAlign: "center",
                fontWeight: 800,
                padding: "12px 8px",
                fontSize: 26,
                lineHeight: 1.25,
                letterSpacing: 1,
              }}
            >
              কোর্স সিলেবাস
            </div>
            {/* কোর্সের নাম — বড়, মোটা, মাঝবরাবর */}
            <div
              style={{
                textAlign: "center",
                fontSize: 20,
                fontWeight: 800,
                color: C.emerald,
                padding: "14px 22px 4px",
                lineHeight: 1.35,
              }}
            >
              {T("কোর্স:", "Course:")} {activeCourse.name}
            </div>
            {/* নির্বাচিত বইয়ের তালিকা — একাধিক কলামে, তাই অনেক বই থাকলেও
                জায়গা কম নেয়। সরু পর্দায় নিজে থেকেই এক কলামে নেমে আসে। */}
            {courseBooksOf(activeCourse.id).length > 0 && (
              <div
                style={{
                  padding: "6px 22px 12px",
                  borderBottom: `1.5px solid ${C.line}`,
                }}
              >
                <div
                  style={{
                    textAlign: "center",
                    fontWeight: 800,
                    fontSize: 13,
                    color: C.emerald,
                    marginBottom: 6,
                  }}
                >
                  {T(
                    "কোর্সের জন্য নির্বাচিত বইসমূহ",
                    "Books selected for this course",
                  )}
                </div>
                <ol
                  style={{
                    margin: 0,
                    padding: 0,
                    listStyle: "none",
                    columnWidth: 240,
                    columnGap: 20,
                    fontSize: 12.5,
                    lineHeight: 1.5,
                  }}
                >
                  {courseBooksOf(activeCourse.id).map((b, i) => (
                    <li
                      key={i}
                      style={{
                        breakInside: "avoid",
                        display: "flex",
                        gap: 6,
                        marginBottom: 2,
                      }}
                    >
                      <span style={{ color: C.gold, fontWeight: 800 }}>
                        {i + 1}.
                      </span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {sheetLoading ? (
              <Loader text={T("লোড হচ্ছে", "Loading")} />
            ) : (
              <div
                style={{
                  overflowX: "auto",
                  overflowY: "auto",
                  maxHeight: "60vh",
                }}
              >
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    tableLayout: "fixed",
                    minWidth: Math.max(cols * 180, 320),
                  }}
                >
                  <thead>
                    <tr>
                      {headers.map((h, i) => (
                        <th
                          key={i}
                          style={{
                            /* গাঢ় ও সম্পূর্ণ নিরেট রঙ — আগে হালকা সবুজ (#eafaf1)
                               ছিল বলে স্ক্রল করার সময় নিচ দিয়ে যাওয়া লেখা
                               হেডারের ভেতর দিয়ে ভেসে উঠত। boxShadow-টা ঘরের
                               পুরো জায়গা একই রঙে ভরে দেয়, তাই কোনো ফাঁক দিয়েই
                               পেছনের কিছু দেখা যায় না */
                            background: C.emeraldD,
                            boxShadow: `inset 0 0 0 9999px ${C.emeraldD}`,
                            color: "#fff",
                            fontWeight: 800,
                            fontSize: 12.5,
                            textAlign: "center",
                            padding: canEdit ? "5px 5px 7px" : "9px 6px",
                            border: `1px solid ${C.emeraldD}`,
                            borderBottom: `2px solid ${C.gold}`,
                            position: "sticky",
                            top: 0,
                            zIndex: 3,
                          }}
                        >
                          {canEdit ? (
                            <>
                              <input
                                value={h}
                                onChange={(e) => setHeader(i, e.target.value)}
                                placeholder="কলামের শিরোনাম"
                                style={{
                                  ...S.input,
                                  width: "100%",
                                  textAlign: "center",
                                  fontWeight: 800,
                                  fontSize: 12.5,
                                  color: "#fff",
                                  background: "rgba(255,255,255,.14)",
                                  border: "1px solid rgba(255,255,255,.35)",
                                  padding: "5px 6px",
                                }}
                              />
                              <button
                                onClick={() => delCol(i)}
                                title="এই কলামটি মুছুন"
                                style={{
                                  border: "none",
                                  background: "none",
                                  cursor: "pointer",
                                  color: C.goldL,
                                  fontSize: 11,
                                  fontWeight: 700,
                                  marginTop: 2,
                                }}
                              >
                                ✕ কলাম
                              </button>
                            </>
                          ) : (
                            h || "—"
                          )}
                        </th>
                      ))}
                      {canEdit && (
                        <th
                          style={{
                            background: C.emeraldD,
                            boxShadow: `inset 0 0 0 9999px ${C.emeraldD}`,
                            border: `1px solid ${C.emeraldD}`,
                            borderBottom: `2px solid ${C.gold}`,
                            width: 46,
                            position: "sticky",
                            top: 0,
                            zIndex: 3,
                          }}
                        />
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.length === 0 ? (
                      <tr>
                        <td
                          colSpan={Math.max(cols, 1) + (canEdit ? 1 : 0)}
                          style={{
                            ...cellStyle,
                            padding: "18px 10px",
                            textAlign: "center",
                            color: C.muted,
                          }}
                        >
                          {canEdit
                            ? "এখনো কিছু লেখা হয়নি — নিচের “➕ সারি যোগ করুন” চেপে শুরু করুন"
                            : "—"}
                        </td>
                      </tr>
                    ) : (
                      rows.map((row, ri) => (
                        <tr key={ri}>
                          {headers.map((_, ci) => (
                            <td key={ci} style={cellStyle}>
                              {canEdit ? (
                                <textarea
                                  value={row[ci] || ""}
                                  onChange={(e) =>
                                    setCell(ri, ci, e.target.value)
                                  }
                                  rows={2}
                                  style={{
                                    ...S.input,
                                    width: "100%",
                                    border: "none",
                                    borderRadius: 0,
                                    resize: "vertical",
                                    fontSize: 12.5,
                                    lineHeight: 1.6,
                                    padding: "8px 9px",
                                    background: "transparent",
                                  }}
                                />
                              ) : (
                                <span style={{ whiteSpace: "pre-line" }}>
                                  {row[ci] || ""}
                                </span>
                              )}
                            </td>
                          ))}
                          {canEdit && (
                            <td
                              style={{
                                ...cellStyle,
                                padding: 4,
                                textAlign: "center",
                              }}
                            >
                              <button
                                onClick={() => delRow(ri)}
                                title="এই সারিটি মুছুন"
                                style={{
                                  border: "none",
                                  background: "none",
                                  cursor: "pointer",
                                  color: C.red,
                                  fontSize: 15,
                                }}
                              >
                                ✕
                              </button>
                            </td>
                          )}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {canEdit && !sheetLoading && (
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                  padding: "10px 14px",
                  borderTop: `1.5px solid ${C.line}`,
                }}
              >
                <Btn sm kind="soft" onClick={addRow}>
                  ➕ সারি যোগ করুন
                </Btn>
                <Btn sm kind="soft" onClick={addCol}>
                  ➕ কলাম যোগ করুন
                </Btn>
                <div style={{ flex: 1 }} />
                <Btn
                  sm
                  kind="gold"
                  onClick={saving ? undefined : save}
                  style={{ opacity: saving ? 0.7 : 1 }}
                >
                  {saving ? "সংরক্ষণ হচ্ছে…" : "💾 সংরক্ষণ করুন"}
                </Btn>
              </div>
            )}
          </div>
        </div>
      )}
    </Section>
  );
}

function AcademicBooksView({ db, setDb, user, courses }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  // ডাটাবেজে বইয়ের আসল নাম (বাংলা) অপরিবর্তিত থাকে — পরিচালক/এডমিন/উস্তাদ সবসময়
  // আসল নামই দেখেন; শুধু স্টুডেন্টের পোর্টালে দেখানোর জন্য এই ম্যাপিং দিয়ে ইংরেজি
  // নাম দেখানো হয় (তালিকায় না থাকা নতুন বই হলে আসল নামই দেখাবে, কিছু বাদ পড়বে না)
  const BOOK_NAME_EN = {
    "নুজহাতুল ক্বারী": "Nuzhatul Qari",
    "কায়দা ফর বিগেনার": "Qaida for Beginner",
    "আকাঈদ ও ফিকহ ফর বিগেনার": "Aqaid and Fiqh for Beginner",
    "আখলাক ফর বিগেনার এনড কায়দা": "Akhlaq for Beginner and Qaida",
    "দুআ-মেনার্স ফর বিগেনার এনড কায়েদা কোর্স":
      "Dua & Manners for Beginner and Qaida Course",
    "প্রফেট স্টোরি ফর বিগেনার এন্ড কায়েদা কোর্স":
      "Prophet Stories for Beginner and Qaida Course",
    "নূরানী কায়েদা ফর কায়েদা কোর্স": "Noorani Qaida for Qaida Course",
    "আকাঈদ ও ফিকহ ফর কায়েদা কোর্স": "Aqaid and Fiqh for Qaida Course",
    "দুআ-মেনার্স ফর কায়দা কোর্স": "Dua & Manners for Qaida Course",
    "সূরা মুখস্থ (বিগেনার)": "Surah Memorisation (Beginner)",
    "হাদিস মুখস্থ (বিগেনার)": "Hadith Memorisation (Beginner)",
    "সূরা মুখস্থ (কায়দা কোর্স)": "Surah Memorisation (Qaida Course)",
    "হাদিস মূখস্থ (কায়দা কোর্স)": "Hadith Memorisation (Qaida Course)",
    "তাজভীদ ফর কায়দা কোর্স": "Tajweed for Qaida Course",
    "গল্পসহ হাদিস": "Hadith with Stories",
    "তাজভীদ ও মাখরাজ": "Tajweed and Makhraj",
    "আকাঈদ ও ফিকহ (৯-১২ বছর)": "Aqaid and Fiqh (Ages 9-12)",
    "আকাঈদ ও ফিকহ (১২-১৭ বছর)": "Aqaid and Fiqh (Ages 12-17)",
  };
  // ডাটাবেজ থেকে আসা নামে বাড়তি স্পেস/Unicode ভিন্নতা থাকলেও যেন মিলে যায় —
  // trim + একাধিক স্পেস এক করা + Unicode NFC নরমালাইজেশন দিয়ে তুলনা করা হচ্ছে
  const normBookName = (s) =>
    String(s || "").normalize("NFC").trim().replace(/\s+/g, " ");
  const BOOK_NAME_EN_NORM = Object.fromEntries(
    Object.entries(BOOK_NAME_EN).map(([k, v]) => [normBookName(k), v]),
  );
  const bookNameFor = (name) =>
    user.role === "student"
      ? BOOK_NAME_EN_NORM[normBookName(name)] || name
      : name;
  const [form, setForm] = useState(null); // {name, file, fileObj, courseIds:[]}
  const [books, setBooks] = useState(db.academicBooks || []);
  const [allCourses, setAllCourses] = useState(courses || []);
  const [booksLoading, setBooksLoading] = useState(true);

  const BASE_MEDIA = (
    import.meta.env?.VITE_API_URL || "http://localhost:8000/api"
  ).replace(/\/api$/, "");
  const adaptBook = (b) => {
    const fileUrl = b.file
      ? b.file.startsWith("http")
        ? b.file
        : BASE_MEDIA + b.file
      : null;
    const fname = fileUrl ? fileUrl.split("/").pop() : b.name + ".pdf";
    const isLink = fileUrl
      ? !/cloudinary\.com/.test(fileUrl) && !fileUrl.includes("/media/")
      : false;
    return {
      id: b.id,
      name: b.name,
      isLink,
      file: fileUrl
        ? {
            data: fileUrl,
            name: fname,
            type: fname.endsWith(".pdf")
              ? "application/pdf"
              : "application/octet-stream",
          }
        : b.file || null,
      date: b.uploaded_at || b.date || todayISO(),
    };
  };
  const loadData = async () => {
    try {
      const [bks, cs] = await Promise.all([api.books(), api.courses()]);
      setBooks(bks.map(adaptBook));
      setAllCourses(
        cs.map((c) => ({
          id: c.id,
          name: c.name,
          color: c.color,
          books: c.books || [],
        })),
      );
    } catch {
      setBooks(db.academicBooks || []);
      setAllCourses(courses || []);
    } finally {
      setBooksLoading(false);
    }
  };
  useEffect(() => {
    loadData();
  }, []);

  const all = books;
  const bookCourses = (bid) =>
    allCourses.filter((c) => (c.books || []).includes(bid));
  const myIds = new Set(allCourses.flatMap((c) => c.books || []));
  const visible = isAdm(user) ? all : all.filter((b) => myIds.has(b.id));
  const MAX_UPLOAD = 10 * 1024 * 1024; // Cloudinary ফ্রি সীমা: ১০ MB
  const pickFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    if (f.size > MAX_UPLOAD)
      notice(
        `⚠️ ফাইলটি ${(f.size / 1048576).toFixed(1)} MB — ফ্রি সীমা ১০ MB। PDF ছোট করুন অথবা উপরের "🔗 লিংক দিয়ে যোগ" ব্যবহার করুন।`,
      );
    setForm((x) => ({
      ...x,
      fileObj: f,
      file: { name: f.name, type: f.type },
    }));
  };
  const toggleCourse = (cid) => {
    setForm((x) => {
      const ids = x.courseIds || [];
      return {
        ...x,
        courseIds: ids.includes(cid)
          ? ids.filter((i) => i !== cid)
          : [...ids, cid],
      };
    });
  };
  const save = async () => {
    if (!form.name.trim()) return notice("বইয়ের নাম লিখুন।");
    const isLink = form.mode === "link";
    if (isLink) {
      if (!(form.link || "").trim())
        return notice("বইয়ের ডাউনলোড/দেখার লিংকটি বসান।");
    } else {
      if (!(form.fileObj instanceof File))
        return notice("ডিভাইস থেকে বইয়ের ফাইল যুক্ত করুন।");
      if (form.fileObj.size > MAX_UPLOAD)
        return notice(
          'ফাইলটি ১০ MB-র বেশি — "🔗 লিংক দিয়ে যোগ" ব্যবহার করুন অথবা PDF ছোট করুন।',
        );
    }
    try {
      if (isLink) await api.addBookLink(form.name.trim(), form.link.trim());
      else await api.uploadBook(form.name.trim(), form.fileObj);
      // নির্বাচিত কোর্সগুলোতে নতুন বই যুক্ত করো
      if ((form.courseIds || []).length > 0) {
        const freshBooks = await api.books();
        const newBook = freshBooks.find((b) => b.name === form.name.trim());
        if (newBook) {
          await Promise.all(
            (form.courseIds || []).map((cid) => {
              const c = allCourses.find((x) => String(x.id) === String(cid));
              const existing = c?.books || [];
              if (existing.includes(newBook.id)) return Promise.resolve();
              return api.saveCourse({ books: [...existing, newBook.id] }, cid);
            }),
          );
        }
      }
      await loadData();
      setForm(null);
    } catch (e) {
      const msg = e?.data?.error || e?.message || "অজানা সমস্যা";
      notice(`বই যোগ ব্যর্থ: ${msg}`);
    }
  };
  const del = (b) =>
    askConfirm(
      `"${b.name}" বইটি মুছে ফেলবেন? কোর্সগুলো থেকেও সরে যাবে।`,
      async () => {
        try {
          await api.deleteBook(b.id);
          await loadData();
        } catch {
          COURSES.forEach((c) => {
            c.books = (c.books || []).filter((x) => x !== b.id);
          });
          setBooks((prev) => prev.filter((x) => x.id !== b.id));
        }
      },
    );
  // পরিচালক সরাসরি বইয়ের নাম বদলাতে পারেন (যেমন ইংরেজি নাম দিতে চাইলে) —
  // ম্যানুয়াল ইংরেজি-অনুবাদ ম্যাপিং না রেখে সরাসরি ডাটা এডিটের অপশন
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");
  const startRename = (b) => {
    setEditingId(b.id);
    setEditName(b.name);
  };
  const saveRename = async (b) => {
    const newName = editName.trim();
    if (!newName) return notice("বইয়ের নাম খালি রাখা যাবে না।");
    if (newName === b.name) return setEditingId(null);
    try {
      await api.updateBookName(b.id, newName);
      await loadData();
    } catch (e) {
      notice(`নাম বদলাতে ব্যর্থ: ${e?.data?.error || e?.message || "অজানা সমস্যা"}`);
    }
    setEditingId(null);
  };
  /* Cache API: প্রথমবার backend থেকে ডাউনলোড করে cache এ রাখে,
     পরেরবার সরাসরি cache থেকে ডিভাইসের default reader এ খোলে */
  const openBook = async (b, setStatus) => {
    const url = b.file?.data;
    if (!url)
      return notice(
        T("এই বইয়ের কোনো ফাইল সংযুক্ত নেই।", "No file is attached to this book."),
      );
    // বাহ্যিক লিংক (Google Drive/Dropbox/অন্য সাইট) → ক্লিকের সাথে সাথেই সরাসরি খুলুন।
    // (ডাউনলোড/cache করলে CORS-এ আটকায়, আর await-এর পর window.open ব্রাউজার popup ব্লক করে দেয়)
    const isExternal = !/cloudinary\.com/.test(url) && !url.includes("/media/");
    if (isExternal) {
      window.open(url, "_blank", "noopener");
      return;
    }
    try {
      const cache = await caches.open("tqa-books-v1");
      let resp = await cache.match(url);
      if (resp) {
        // ইতিমধ্যে ডিভাইসে সংরক্ষিত আছে → আর নামাবে না, সরাসরি খোলো
        setStatus("opening");
      } else {
        // প্রথমবার → backend থেকে একবারই নামিয়ে সংরক্ষণ করো
        setStatus("downloading");
        const fresh = await fetch(url, { credentials: "omit" });
        if (!fresh.ok)
          throw Object.assign(new Error("not found"), { status: fresh.status });
        await cache.put(url, fresh.clone());
        resp = await cache.match(url);
      }
      const blob = await resp.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.target = "_blank";
      a.rel = "noopener";
      a.click();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
      setStatus("done");
      setTimeout(() => setStatus(null), 1800);
    } catch (e) {
      if (e?.status === 404) {
        notice(
          T(
            "ফাইলটি সার্ভারে পাওয়া যাচ্ছে না। পরিচালক বইটি আবার আপলোড করুন।",
            "This file could not be found on the server. Please ask the director to re-upload it.",
          ),
        );
      } else {
        // CORS বা অন্য সমস্যা → সরাসরি নতুন ট্যাবে খোলো (ব্রাউজার নিজে cache করবে)
        window.open(url, "_blank");
      }
      setStatus(null);
    }
  };
  /* বইয়ের নামে ক্লিক → প্রথমবার ডাউনলোড + cache, পরেরবার cache থেকে সরাসরি */
  const BookLink = ({ b }) => {
    const [status, setStatus] = useState(null);
    const busy = status === "downloading" || status === "opening";
    const msg =
      status === "downloading"
        ? T("প্রথমবার নামছে…", "Downloading for the first time…")
        : status === "opening"
          ? T("ডিভাইস থেকে খুলছে…", "Opening from device…")
          : status === "done"
            ? T("খুলছে…", "Opening…")
            : null;
    const icon =
      status === "downloading"
        ? "⏳"
        : status === "opening"
          ? "⚡"
          : status === "done"
            ? "✅"
            : "📖";
    return (
      <span
        onClick={() => !busy && openBook(b, setStatus)}
        style={{
          fontWeight: 800,
          fontSize: 14,
          color: busy ? C.muted : C.emerald,
          cursor: busy ? "wait" : "pointer",
          borderBottom: `1.5px dashed ${busy ? C.muted : C.emerald}`,
        }}
        title={T(
          busy
            ? "একটু অপেক্ষা করুন…"
            : "ক্লিক করলেই খুলবে — প্রথমবার একবার নামবে, পরেরবার সরাসরি ডিভাইস থেকে",
          busy
            ? "Please wait…"
            : "Click to open — downloads once the first time, then opens directly from your device",
        )}
      >
        {icon} {bookNameFor(b.name)}
        {msg && (
          <span
            style={{
              fontSize: 11,
              fontWeight: 400,
              marginLeft: 6,
              color: C.muted,
            }}
          >
            {msg}
          </span>
        )}
      </span>
    );
  };
  const Card = (b) => (
    <div
      key={b.id}
      style={{
        ...S.card,
        padding: 14,
        display: "flex",
        gap: 12,
        alignItems: "center",
        flexWrap: "wrap",
      }}
    >
      <div style={{ flex: 1, minWidth: 200 }}>
        {editingId === b.id ? (
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <input
              autoFocus
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") saveRename(b);
                if (e.key === "Escape") setEditingId(null);
              }}
              style={{ ...S.input, padding: "6px 8px", fontSize: 13.5 }}
            />
            <Btn sm onClick={() => saveRename(b)}>
              ✔
            </Btn>
            <Btn sm kind="soft" onClick={() => setEditingId(null)}>
              ✕
            </Btn>
          </div>
        ) : (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <BookLink b={b} />
            {isDir(user) && (
              <button
                onClick={() => startRename(b)}
                title="বইয়ের নাম বদলান"
                style={{
                  border: "none",
                  background: "none",
                  cursor: "pointer",
                  fontSize: 13,
                  color: C.muted,
                  padding: 0,
                }}
              >
                ✏️
              </button>
            )}
          </span>
        )}
        <div style={{ fontSize: 11.5, color: C.muted, marginTop: 3 }}>
          {b.isLink ? (
            <Tag color={C.blue} bg={C.blueBg}>
              🔗 {T("লিংক", "Link")}
            </Tag>
          ) : (
            <>
              <Tag color={C.blue} bg={C.blueBg}>
                {bookExt(b.file?.name)}
              </Tag>{" "}
              {b.file?.name || T("ফাইল সংযুক্ত নেই", "No file attached")}
            </>
          )}
          {user.role !== "student" && (
            <> · যোগ: {fmtDate(b.date)}</>
          )}
          {isAdm(user) && (
            <span>
              {" "}
              · কোর্স:{" "}
              {bookCourses(b.id)
                .map((c) => c.name)
                .join(", ") || "কোনো কোর্সে যুক্ত নয়"}
            </span>
          )}
        </div>
      </div>
      {isDir(user) && (
        <Btn sm kind="danger" onClick={() => del(b)}>
          🗑
        </Btn>
      )}
    </div>
  );
  return (
    <Section
      title={T("একাডেমিক বইসমূহ", "Academic Books")}
      sub={
        isAdm(user)
          ? "একাডেমির সকল বইয়ের কেন্দ্রীয় তালিকা — কোর্স তৈরির সময় এখান থেকেই বই সিলেক্ট হয়"
          : T(
              "আপনার কোর্সের নির্ধারিত বইসমূহ — নামে ক্লিক করলেই খুলবে",
              "Books assigned to your course — click a name to open it",
            )
      }
      action={
        isDir(user) && (
          <Btn
            onClick={() =>
              setForm({ name: "", file: null, fileObj: null, courseIds: [], mode: "file", link: "" })
            }
          >
            + বই যোগ করুন
          </Btn>
        )
      }
    >
      {/* viewer state সরানো হয়েছে — BookLink সরাসরি ডিভাইসে খোলে */}
      {booksLoading && <Loader text={T("বই লোড হচ্ছে", "Loading books")} />}
      {!booksLoading && visible.length === 0 && (
        <div
          style={{
            ...S.card,
            textAlign: "center",
            color: C.muted,
            padding: 28,
          }}
        >
          📚{" "}
          {isAdm(user)
            ? 'এখনো কোনো বই যোগ হয়নি — "+ বই যোগ করুন" দিয়ে শুরু করুন।'
            : T(
                "আপনার কোর্সে এখনো কোনো বই নির্ধারিত হয়নি।",
                "No books have been assigned to your course yet.",
              )}
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
              <div
                style={{
                  fontWeight: 800,
                  fontSize: 14.5,
                  marginBottom: 8,
                  color: c.color || C.emerald,
                }}
              >
                📗 {c.name}
              </div>
              <div style={{ display: "grid", gap: 10 }}>{items.map(Card)}</div>
            </div>
          );
        })
      )}
      {form && (
        <Modal title="+ বই যোগ করুন" onClose={() => setForm(null)}>
          <label style={S.label}>বইয়ের নাম লিখুন</label>
          <input
            style={S.input}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="যেমন: নুরানী কায়দা (সংশোধিত)"
          />
          {/* ফাইল আপলোড / লিংক — টগল */}
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <Btn
              sm
              kind={form.mode !== "link" ? "primary" : "soft"}
              style={{ flex: 1, justifyContent: "center" }}
              onClick={() => setForm((x) => ({ ...x, mode: "file" }))}
            >
              📁 ফাইল আপলোড
            </Btn>
            <Btn
              sm
              kind={form.mode === "link" ? "primary" : "soft"}
              style={{ flex: 1, justifyContent: "center" }}
              onClick={() => setForm((x) => ({ ...x, mode: "link" }))}
            >
              🔗 লিংক দিয়ে যোগ
            </Btn>
          </div>
          {form.mode === "link" ? (
            <div style={{ marginTop: 12 }}>
              <label style={S.label}>
                বইয়ের লিংক (Google Drive / Dropbox / যেকোনো URL) — সাইজ সীমা নেই
              </label>
              <input
                style={S.input}
                value={form.link || ""}
                onChange={(e) =>
                  setForm((x) => ({ ...x, link: e.target.value }))
                }
                placeholder="https://drive.google.com/..."
              />
              <div style={{ fontSize: 11.5, color: C.muted, marginTop: 5 }}>
                💡 Google Drive-এ বইটি রেখে "Anyone with the link" শেয়ার করে
                লিংকটি এখানে বসান — বড় বইও কোনো সীমা ছাড়া যোগ হবে।
              </div>
            </div>
          ) : (
            <div style={{ marginTop: 12 }}>
              <label style={S.label}>
                ফাইল যুক্ত করুন — যেকোনো ফরমেট (PDF, DOC, PNG, JPG...) · সর্বোচ্চ ১০ MB
              </label>
              <label
                style={{
                  display: "grid",
                  placeItems: "center",
                  gap: 6,
                  padding: "24px 14px",
                  border: `2px dashed ${form.file ? C.emerald : C.line}`,
                  borderRadius: 14,
                  cursor: "pointer",
                  background: form.file ? C.greenBg : C.cream,
                  textAlign: "center",
                }}
              >
                <span style={{ fontSize: 30 }}>{form.file ? "✅" : "📁"}</span>
                <span style={{ fontSize: 13, fontWeight: 700 }}>
                  {form.file
                    ? form.file.name
                    : "ডিভাইস থেকে ফাইল বেছে নিন (≤ ১০ MB)"}
                </span>
                <input
                  type="file"
                  style={{ display: "none" }}
                  onChange={pickFile}
                />
              </label>
            </div>
          )}

          {/* কোর্স অ্যাসাইনমেন্ট — ঐচ্ছিক */}
          {allCourses.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <label style={S.label}>
                📖 কোন কোর্সে যোগ করবেন? (ঐচ্ছিক — পরেও কোর্স এডিট থেকে যোগ করা
                যাবে)
              </label>
              <div
                style={{
                  border: `1.5px solid ${C.line}`,
                  borderRadius: 10,
                  padding: 6,
                  background: "#fff",
                  maxHeight: 160,
                  overflowY: "auto",
                }}
              >
                {allCourses.map((c) => {
                  const sel = (form.courseIds || []).includes(c.id);
                  const full = false; // কোনো সীমা নেই — যত খুশি বই যোগ করা যাবে
                  return (
                    <label
                      key={c.id}
                      style={{
                        display: "flex",
                        gap: 8,
                        alignItems: "center",
                        padding: "6px 8px",
                        fontSize: 13,
                        cursor: full ? "not-allowed" : "pointer",
                        borderRadius: 8,
                        background: sel ? C.greenBg : "transparent",
                        opacity: full ? 0.45 : 1,
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={sel}
                        disabled={full}
                        onChange={() => toggleCourse(c.id)}
                      />
                      <span
                        style={{
                          width: 10,
                          height: 10,
                          borderRadius: 3,
                          background: c.color || C.emerald,
                          flexShrink: 0,
                          display: "inline-block",
                        }}
                      />
                      <b>{c.name}</b>
                      {full && (
                        <span style={{ fontSize: 11, color: C.red }}>
                          (৬টি পূর্ণ)
                        </span>
                      )}
                    </label>
                  );
                })}
              </div>
              {(form.courseIds || []).length > 0 && (
                <div style={{ fontSize: 11.5, color: C.emerald, marginTop: 4 }}>
                  ✔ {bn((form.courseIds || []).length)}টি কোর্সে যোগ হবে
                </div>
              )}
            </div>
          )}

          <Btn
            style={{ marginTop: 16, width: "100%", justifyContent: "center" }}
            onClick={save}
          >
            + তালিকায় যোগ করুন
          </Btn>
        </Modal>
      )}
    </Section>
  );
}

/* ═══════════════ ওভারভিউ ড্যাশবোর্ড ═══════════════ */
function Overview({ db, courses, user, goTo }) {
  const T = (bnText, enText) => (user.role === "student" ? enText : bnText);
  // আগে এখানে stale mock db.classes/db.feePayments/db.forms/db.admissions/
  // db.ratings/db.assignments/db.notices ব্যবহার হতো — লগইনের পরের প্রথম
  // পেজ (ড্যাশবোর্ড) হওয়ায় প্রভাব সবচেয়ে বেশি ছিল; এখন সরাসরি API থেকে লোড হয়
  const [todayClasses, setTodayClasses] = useState([]);
  const [todayLoading, setTodayLoading] = useState(true); // লোড শেষ হওয়ার আগে "আজ ক্লাস নেই" না দেখাতে
  const [income, setIncome] = useState(0);
  const [admissionsPending, setAdmissionsPending] = useState(0);
  const [newForms, setNewForms] = useState(0);
  const [assignmentsCount, setAssignmentsCount] = useState(0);
  const [teacherRating, setTeacherRating] = useState({ avg: 0, count: 0 });
  const [recentNotices, setRecentNotices] = useState(db.notices || []);
  const [completedThisMonth, setCompletedThisMonth] = useState(0);
  const [hasDue, setHasDue] = useState(false);
  // নোটিফিকেশন এখনো চালু করা হয়নি এমন ডিভাইসেই একবার ব্যানারটা দেখাবে
  const [showPushBanner, setShowPushBanner] = useState(
    () =>
      typeof Notification !== "undefined" &&
      Notification.permission === "default" &&
      "serviceWorker" in navigator &&
      !sessionStorage.getItem("tqa_push_dismissed"),
  );
  // পারমিশন আগে থেকেই "granted" থাকলে (যেমন অনেক আগে "জুমে জয়েন করুন" ক্লিকের
  // সময় দেওয়া হয়ে গিয়েছিল) — তখন ব্যানার আর দেখায় না, কিন্তু পুশ-সাবস্ক্রিপশনটাও
  // কখনো ব্যাকএন্ডে সেভ হয়নি (সেটা শুধু ব্যানারের বাটনে ক্লিকেই হতো) — তাই এই
  // ডিভাইসগুলোতে নিঃশব্দে (কোনো পপআপ/নোটিস ছাড়াই) একবার সাবস্ক্রাইব করে নেওয়া হচ্ছে
  useEffect(() => {
    if (typeof Notification !== "undefined" && Notification.permission === "granted") {
      enablePushNotifications(true);
    }
  }, []);
  useEffect(() => {
    let cancelled = false;
    api
      .todayClasses()
      .then((d) => !cancelled && setTodayClasses(d))
      .catch(() => {})
      .finally(() => !cancelled && setTodayLoading(false));
    api.notices().then((d) => !cancelled && setRecentNotices(d)).catch(() => {});
    if (isAdm(user)) {
      Promise.all([api.myFees(), api.admissions()])
        .then(([fees, admissions]) => {
          if (cancelled) return;
          setIncome(fees.reduce((s, p) => s + (+p.amount || 0), 0));
          setAdmissionsPending(admissions.filter((a) => a.status === "pending").length);
          setNewForms(
            admissions.filter(
              (a) => (a.kind === "trial" || a.kind === "contact") && !a.replied,
            ).length,
          );
        })
        .catch(() => {});
    }
    if (user.role === "teacher") {
      api
        .teacherRatingSummary(user.id)
        .then((s) => !cancelled && setTeacherRating({ avg: s.avg || 0, count: s.count || 0 }))
        .catch(() => {});
    }
    if (user.role !== "admin") {
      api
        .assignments()
        .then(
          (d) =>
            !cancelled &&
            setAssignmentsCount(
              d.filter((a) => courseById(courses, a.course || a.courseId).id).length,
            ),
        )
        .catch(() => {});
    }
    if (user.role === "student") {
      const ym = todayISO().slice(0, 7); // "YYYY-MM" — চলতি মাস
      api
        .attendanceReport()
        .then(
          (d) =>
            !cancelled &&
            setCompletedThisMonth(
              d.filter((a) => a.present && (a.class_date || "").startsWith(ym)).length,
            ),
        )
        .catch(() => {});
      api
        .myDues()
        .then((d) => !cancelled && setHasDue(d.length > 0))
        .catch(() => {});
    }
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);
  const missedTopics = courses
    .flatMap((c) => (c.lectures || []).flatMap((l) => l.topics || []))
    .filter((t) => t.covered === false).length;
  const greet =
    user.role === "director"
      ? "আসসালামু আলাইকুম, পরিচালক সাহেব"
      : user.role === "admin"
        ? `আসসালামু আলাইকুম, ${user.name} (এডমিন)`
        : user.role === "teacher"
          ? `আসসালামু আলাইকুম, ${user.name}`
          : `Assalamu Alaikum, ${user.name.split(" ")[0]}`;
  return (
    <>
      {showPushBanner && (
        <div
          style={{
            ...S.card,
            display: "flex",
            alignItems: "center",
            gap: 12,
            flexWrap: "wrap",
            marginBottom: 14,
            border: `1.5px solid ${C.gold}`,
            background: C.amberBg,
          }}
        >
          <div style={{ fontSize: 24 }}>🔔</div>
          <div style={{ flex: 1, minWidth: 200, fontSize: 13 }}>
            {T(
              "এই ডিভাইসে নোটিফিকেশন চালু করুন — অ্যাপ বন্ধ থাকলেও ক্লাস/পেমেন্ট/জরুরি খবর সাথে সাথে জানতে পারবেন।",
              "Enable notifications on this device — get instant alerts for classes, payments, and important updates even when the app is closed.",
            )}
          </div>
          <Btn
            sm
            kind="gold"
            onClick={async () => {
              const ok = await enablePushNotifications();
              if (ok) setShowPushBanner(false);
            }}
          >
            {T("🔔 চালু করুন", "🔔 Enable")}
          </Btn>
          <Btn
            sm
            kind="ghost"
            onClick={() => {
              sessionStorage.setItem("tqa_push_dismissed", "1");
              setShowPushBanner(false);
            }}
          >
            {T("বাদ দিন", "Dismiss")}
          </Btn>
        </div>
      )}
      <div
        style={{
          background: `linear-gradient(135deg, ${C.emeraldD}, ${C.emerald})`,
          borderRadius: 18,
          padding: "22px 24px",
          color: "#fff",
          marginBottom: 18,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            right: 18,
            top: 8,
            opacity: 0.28,
          }}
        >
          {/* সবুজ ব্যানারে সবুজ-ব্যাকগ্রাউন্ডের লোগো মিশে যেত বলে এখানে
              transparent-background ভার্সন সাদা করে (CSS filter) বসানো হলো */}
          <img
            src="/brand/logo-mark.png"
            alt=""
            style={{
              width: 72,
              height: 72,
              filter: "brightness(0) invert(1)",
            }}
          />
        </div>
        <div
          style={{
            fontSize: 12.5,
            color: C.goldL,
            fontWeight: 700,
            letterSpacing: 1,
          }}
        >
          {T("তারবিয়াতুল কুরআন একাডেমি", "Tarbiyatul Quran Academy")}
        </div>
        <div style={{ fontSize: 21, fontWeight: 800, margin: "4px 0" }}>
          {greet} 🌙
        </div>
        <div style={{ fontSize: 13, color: "#d7e9de" }}>
          {fmtDate(todayISO())} ·{" "}
          {T(
            `আজ ${bn(todayClasses.length)}টি ক্লাস নির্ধারিত আছে`,
            `${todayClasses.length} class(es) scheduled today`,
          )}
        </div>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 10,
          marginBottom: 18,
        }}
      >
        <Stat
          icon="🎥"
          label={T("আজকের ক্লাস", "Today's Classes")}
          value={T(bn(todayClasses.length), todayClasses.length)}
        />
        <Stat
          icon="📚"
          label={T("চলমান কোর্স", "Active Courses")}
          value={T(bn(courses.length), courses.length)}
          accent={C.blue}
        />
        {user.role === "student" && (
          <Stat
            icon="✅"
            label={T(
              `${MONTHS_BN_FULL[new Date().getMonth()]}-এ সম্পন্ন ক্লাস`,
              `Classes Completed in ${MONTHS_EN_FULL[new Date().getMonth()]}`,
            )}
            value={T(bn(completedThisMonth), completedThisMonth)}
            accent={C.emerald}
          />
        )}
        {user.role === "student" && (
          <Stat
            icon={hasDue ? "⚠️" : "💳"}
            label={T("পেমেন্ট", "Payment")}
            value={
              hasDue ? T("বাকি", "Due") : T("সম্পন্ন ✔", "Paid ✔")
            }
            accent={hasDue ? C.red : C.emerald}
          />
        )}
        {isAdm(user) && (
          <Stat
            icon="💰"
            label="মোট ফি আদায়"
            value={`৳${bn(income.toLocaleString("en"))}`}
            accent={C.gold}
          />
        )}
        {isAdm(user) && (
          <Stat
            icon="🎓"
            label="ভর্তি আবেদন"
            value={bn(admissionsPending)}
            accent={C.gold}
            note="অপেক্ষমাণ"
          />
        )}
        {user.role === "teacher" && (
          <Stat
            icon="🌟"
            label="ক্লাসের মান"
            value={`★ ${bn(teacherRating.count ? teacherRating.avg.toFixed(1) : "—")}`}
            accent={C.gold}
            note={`${bn(teacherRating.count)}টি মূল্যায়ন`}
          />
        )}
        {isAdm(user) && (
          <Stat
            icon="📨"
            label="নতুন ফর্ম"
            value={bn(newForms)}
            accent={C.red}
            note="উত্তর বাকি"
          />
        )}
        {user.role !== "admin" && (
          <Stat
            icon="📝"
            label={T("অ্যাসাইনমেন্ট", "Assignments")}
            value={T(bn(assignmentsCount), assignmentsCount)}
            accent={C.gold}
          />
        )}
        {missedTopics > 0 && (
          <Stat
            icon="✘"
            label={T("বাদ পড়া টপিক", "Missed Topics")}
            value={T(bn(missedTopics), missedTopics)}
            accent={C.red}
            note={T("এডমিন সংশোধনযোগ্য", "Fixable by admin")}
          />
        )}
      </div>
      <Section
        title={T("আজকের ক্লাসে ফোকাস করুন", "Focus on Today's Classes")}
        action={
          <Btn sm kind="ghost" onClick={() => goTo("classes")}>
            {T("সব ক্লাস দেখুন →", "View all classes →")}
          </Btn>
        }
      >
        <div style={{ display: "grid", gap: 10 }}>
          {todayLoading && <Loader text={T("লোড হচ্ছে", "Loading")} />}
          {!todayLoading && todayClasses.length === 0 && (
            <div style={{ ...S.card, textAlign: "center", color: C.muted }}>
              {T(
                "আজ আর কোনো ক্লাস বাকি নেই। আলহামদুলিল্লাহ।",
                "No more classes today. Alhamdulillah.",
              )}
            </div>
          )}
          {todayClasses.map((k) => {
            const c = courseById(courses, k.course || k.courseId);
            const lec = c.lectures?.[(k.lecture_no || k.lectureNo) - 1];
            return (
              <div
                key={k.id}
                style={{
                  ...S.card,
                  padding: 16,
                  display: "flex",
                  gap: 12,
                  alignItems: "center",
                  flexWrap: "wrap",
                  border: `1.5px solid ${C.goldL}`,
                  background: "#fffdf6",
                }}
              >
                <div style={{ fontSize: 26 }}>🕐</div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontWeight: 800 }}>
                    {c.name} — {k.time}
                  </div>
                  {lec && (
                    <div style={{ fontSize: 12.5, color: C.muted }}>
                      {T(
                        `লেকচার ${bn(k.lecture_no || k.lectureNo)}: ${lec.title}`,
                        `Lecture ${k.lecture_no || k.lectureNo}: ${lec.title}`,
                      )}
                    </div>
                  )}
                  {lec?.topics?.length > 0 && (
                    <div style={{ fontSize: 12, color: C.muted }}>
                      {T("আজকের টপিক", "Today's topics")}:{" "}
                      {lec.topics.map((t) => t.text).join(" · ")}
                    </div>
                  )}
                </div>
                <Btn kind="gold" onClick={() => goTo("classes")}>
                  {T("ক্লাসে যান →", "Go to class →")}
                </Btn>
              </div>
            );
          })}
        </div>
      </Section>
      <Section
        title={T("সাম্প্রতিক নোটিশ", "Recent Notices")}
        action={
          <Btn sm kind="ghost" onClick={() => goTo("notices")}>
            {T("সব দেখুন →", "View all →")}
          </Btn>
        }
      >
        <div style={{ display: "grid", gap: 8 }}>
          {recentNotices.slice(0, 2).map((n) => (
            <div key={n.id} style={{ ...S.card, padding: 14 }}>
              <b style={{ fontSize: 13.5 }}>📌 {n.title}</b>
              <div style={{ fontSize: 12.5, color: C.muted }}>{n.body}</div>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}

/* ═══════════════ অ্যাপ শেল ═══════════════ */
const NAV = [
  {
    id: "overview",
    icon: "🏠",
    label: "ড্যাশবোর্ড",
    labelEn: "Dashboard",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "classes",
    icon: "🎥",
    label: "ক্লাস ও জুম জয়েন",
    labelEn: "Classes & Zoom Join",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "instantclass",
    icon: "⚡",
    label: "ইনস্ট্যান্ট ক্লাস",
    labelEn: "Instant Class",
    roles: ["director", "admin"],
  },
  {
    id: "postponed",
    icon: "⛔",
    label: "স্থগিত ক্লাস",
    labelEn: "Postponed Classes",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "routine",
    icon: "📅",
    label: "ক্লাস রুটিন",
    labelEn: "Class Routine",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "lectures",
    icon: "📋",
    label: "লেকচার প্ল্যান",
    labelEn: "Lecture Plan",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "syllabus",
    icon: "📜",
    label: "সিলেবাস",
    labelEn: "Syllabus",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "attendance",
    icon: "🗓️",
    label: "হাজিরা",
    labelEn: "Attendance",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "assignments",
    icon: "📝",
    label: "অ্যাসাইনমেন্ট",
    labelEn: "Assignments",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "exams",
    icon: "🏅",
    label: "পরীক্ষা ও ফলাফল",
    labelEn: "Exams & Results",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "progress",
    icon: "📈",
    label: "অগ্রগতি ও ফি রিপোর্ট",
    labelEn: "Progress & Fee Report",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "payments",
    icon: "💳",
    label: "পেমেন্ট",
    labelEn: "Payments",
    roles: ["student"],
  },
  {
    id: "studentpayments",
    icon: "💵",
    label: "স্টুডেন্ট পেমেন্ট",
    roles: ["director"],
  },
  {
    id: "waoutbox",
    icon: "📤",
    label: "WhatsApp মেসেজ",
    roles: ["director", "admin"],
  },
  {
    id: "teacherreport",
    icon: "🌟",
    label: "টিচার রিপোর্ট ও পেমেন্ট",
    roles: ["director", "admin", "teacher"],
  },
  { id: "coursemgr", icon: "📖", label: "কোর্স", roles: ["director"] },
  {
    id: "allstudents",
    icon: "👥",
    label: "সকল স্টুডেন্ট",
    roles: ["director", "admin"],
  },
  {
    id: "admissions",
    icon: "🎓",
    label: "ভর্তি আবেদন",
    roles: ["director", "admin"],
  },
  { id: "accounts", icon: "🏦", label: "হিসাব-নিকাশ", roles: ["director"] },
  {
    id: "forms",
    icon: "📨",
    label: "ফর্ম সাবমিশন",
    roles: ["director", "admin"],
  },
  {
    id: "books",
    icon: "📚",
    label: "একাডেমিক বইসমূহ",
    labelEn: "Academic Books",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "myreceipts",
    icon: "🧾",
    label: "ভাউচার/রিসিট",
    labelEn: "Vouchers/Receipts",
    // স্টুডেন্টের পোর্টালে আলাদা রিসিট ফাইল দেখানো হয় না — শুধু পেমেন্ট হিস্টরি
    // ("পেমেন্ট" মেনু); admin/teacher (নিজের বেতন-ভাউচার) এর জন্য এটা থেকে যায়
    roles: ["admin", "teacher"],
  },
  {
    id: "leaves",
    icon: "✉️",
    label: "ছুটির আবেদন",
    labelEn: "Leave Application",
    roles: ["director", "admin", "teacher", "student"],
  },
  {
    id: "notices",
    icon: "📌",
    label: "নোটিশ বোর্ড",
    labelEn: "Notice Board",
    roles: ["director", "admin", "teacher", "student"],
  },
  { id: "manage", icon: "⚙️", label: "ম্যানেজ সেটিংস", roles: ["director"] },
];

/* ═══════════════ নতুন সংস্করণ এসেছে কিনা জানানো ═══════════════
   লগইন থাকা অবস্থায় ট্যাবটা আর কখনো নিজে থেকে রিলোড হয় না (কাজ যেন না হারায়,
   সেটা ইচ্ছাকৃত) — কিন্তু এর ফলে নতুন সংস্করণও আপনাআপনি নামে না, পুরনো কোডই
   চলতে থাকে। তাই ১০ মিনিট পরপর index.html দেখে নিই: বিল্ডের হ্যাশসহ যে
   স্ক্রিপ্টের নাম ওখানে আছে সেটা এখন চালু নামটার সাথে না মিললে বুঝি নতুন
   সংস্করণ উঠেছে।
   নিজে থেকে কিছুই রিফ্রেশ করে না — শুধু জানায়, চাপবেন কিনা ব্যবহারকারীর ইচ্ছা। */
const RELOAD_GUARD_KEY = "tqa_update_reloaded_at";
let selfReloading = false;
/* সব ব্লকিং পপআপের অভিন্ন খোলস — পুরো পর্দা ঢেকে দেয়, বাইরে চাপলে বা
   ব্যাক চাপলে বন্ধ হয় না; কেবল ভেতরের বাটনেই বন্ধ হয়। উদ্দেশ্য: জরুরি
   বার্তা যেন কেউ না দেখেই পাশ কাটিয়ে যেতে না পারেন। */
function BlockingPopup({ icon, title, children, footer, zIndex = 305 }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex,
        background: "rgba(18,63,40,.72)",
        display: "grid",
        placeItems: "center",
        padding: 16,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 18,
          maxWidth: 400,
          width: "100%",
          maxHeight: "86vh",
          overflowY: "auto",
          padding: 26,
          textAlign: "center",
          fontFamily: "'Hind Siliguri', sans-serif",
        }}
      >
        <div style={{ fontSize: 40 }}>{icon}</div>
        <div
          style={{ fontWeight: 800, fontSize: 17, color: C.emerald, marginTop: 6 }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: 13.5,
            color: C.text,
            margin: "12px 0 18px",
            lineHeight: 1.7,
            textAlign: "left",
          }}
        >
          {children}
        </div>
        {footer}
      </div>
    </div>
  );
}

/* ═══════════ নতুন নোটিফিকেশন এলে ভাসমান কার্ড ═══════════
   পর্দা আটকায় না — উপরে একটা কার্ড ভেসে ওঠে, নিজেই কয়েক সেকেন্ড পর সরে
   যায়। মাউস রাখলে বা ছুঁয়ে থাকলে সরে না, যাতে পুরোটা পড়ে নেওয়া যায়।
   পরে ইচ্ছা করলে নোটিফিকেশন ঘণ্টা থেকে আবার পড়া যাবে — তাই "পড়া হয়েছে"
   চিহ্নিত করা হয় না, ঘণ্টার লাল সংখ্যাটা আগের মতোই থাকে।

   ⚠️ কেবল *নতুন* গুলোই দেখায়। কোন নম্বর পর্যন্ত দেখানো হয়ে গেছে তা
   ডিভাইসেই মনে রাখা হয়। প্রথমবার কিছুই দেখায় না — নইলে আগে জমে থাকা
   সব পুরনো নোটিফিকেশন একসাথে ঝাঁপিয়ে পড়ত। */
const SEEN_NOTIF_KEY = "tqa_seen_notif_id";
const NOTIF_TOAST_MS = 10000; // কত সময় পর নিজে থেকে সরে যাবে

function NewNotifToast({ user, notifs }) {
  const en = user?.role === "student";
  const [items, setItems] = useState([]);
  // একবার ছুঁয়ে/মাউস রাখলে (অর্থাৎ পড়তে শুরু করলে) সময় গোনা একেবারেই
  // থেমে যায় — তারপর কেবল ✕ চাপলেই সরে। পড়ার মাঝপথে সরে যাওয়ার ভয় নেই।
  const [reading, setReading] = useState(false);
  useEffect(() => {
    if (!user || !notifs || !notifs.length) return;
    const ids = notifs.map((n) => Number(n.id)).filter((x) => !Number.isNaN(x));
    if (!ids.length) return;
    const maxId = Math.max(...ids);
    let seen = null;
    try {
      const raw = window.localStorage.getItem(SEEN_NOTIF_KEY);
      seen = raw == null ? null : Number(raw);
    } catch (e) {
      /* উপেক্ষা */
    }
    const remember = () => {
      try {
        window.localStorage.setItem(SEEN_NOTIF_KEY, String(maxId));
      } catch (e) {
        /* উপেক্ষা */
      }
    };
    if (seen == null || Number.isNaN(seen)) {
      remember(); // প্রথমবার — পুরনোগুলো দেখাই না, শুধু জায়গাটা চিহ্নিত করে রাখি
      return;
    }
    const fresh = notifs.filter((n) => Number(n.id) > seen);
    if (!fresh.length) return;
    setItems(fresh);
    setReading(false); // নতুন বার্তা — আবার নিজে থেকে সরার সুযোগ পাক
    remember();
  }, [notifs, user]);
  // নিজে থেকে সরে যাওয়া — কেউ পড়তে শুরু করলে আর সরে না
  useEffect(() => {
    if (!items.length || reading) return;
    const t = setTimeout(() => setItems([]), NOTIF_TOAST_MS);
    return () => clearTimeout(t);
  }, [items, reading]);
  if (!user || !items.length) return null;
  return (
    <div
      onMouseEnter={() => setReading(true)}
      onTouchStart={() => setReading(true)}
      onClick={() => setReading(true)}
      style={{
        position: "fixed",
        top: 12,
        left: 12,
        right: 12,
        margin: "0 auto",
        maxWidth: 400,
        zIndex: 290,
        background: "#fff",
        border: `1.5px solid ${C.emerald}`,
        borderRadius: 16,
        boxShadow: "0 12px 32px rgba(0,0,0,.22)",
        padding: "14px 16px",
        fontFamily: "'Hind Siliguri', sans-serif",
        maxHeight: "60vh",
        overflowY: "auto",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 8,
        }}
      >
        <span style={{ fontSize: 18 }}>🔔</span>
        <span style={{ fontWeight: 800, fontSize: 14, color: C.emerald, flex: 1 }}>
          {en
            ? items.length > 1
              ? `${items.length} new messages`
              : "New message from the Academy"
            : items.length > 1
              ? `${bn(items.length)}টি নতুন বার্তা`
              : "একাডেমি থেকে নতুন বার্তা"}
        </span>
        <button
          onClick={() => setItems([])}
          title={en ? "Close" : "বন্ধ করুন"}
          aria-label={en ? "Close" : "বন্ধ করুন"}
          style={{
            border: "none",
            background: "none",
            cursor: "pointer",
            fontSize: 16,
            color: C.muted,
            lineHeight: 1,
          }}
        >
          ✕
        </button>
      </div>
      {items.map((n) => (
        <div
          key={n.id}
          style={{
            background: C.greenBg,
            borderRadius: 10,
            padding: "9px 11px",
            marginTop: 6,
            fontSize: 13.5,
            lineHeight: 1.65,
            color: C.text,
          }}
        >
          {n.text}
        </div>
      ))}
    </div>
  );
}

/* ═══════════ উস্তাদ রিজয়েন চালু করলে শিক্ষার্থীর পর্দা ঢেকে রিজয়েন বাটন ═══════════
   উস্তাদ "রিজয়েন" চেপে ২য় জুম লিংকে সরে গেলে শিক্ষার্থী ১ম মিটিংয়ে একা বসে
   থাকেন — তিনি বুঝতেই পারেন না উস্তাদ অন্য লিংকে চলে গেছেন। তাই পোর্টালে
   ফেরামাত্র পুরো পর্দা ঢেকে এই পপআপ, সাথে সরাসরি রিজয়েনের বাটন।
   ফাঁদে পড়ার ভয় নেই — বাটনটা নিছক একটা লিংক, সবসময় কাজ করে, আর চাপলেই
   পপআপ সরে যায়। ক্লাসের সময় পেরিয়ে গেলে এমনিতেও আর আসে না। */
function RejoinBlockPopup({ k, user, onRejoin, onLater }) {
  const en = user?.role === "student";
  return (
    <BlockingPopup
      icon="🔁"
      zIndex={302}
      title={
        en
          ? "Your teacher has opened a new meeting"
          : "উস্তাদ নতুন মিটিং খুলেছেন"
      }
      footer={
        <div style={{ display: "grid", gap: 8 }}>
          <a
            href={k.zoom2 || k.zoom}
            target="_blank"
            rel="noreferrer"
            onClick={onRejoin}
            style={{
              display: "block",
              textDecoration: "none",
              width: "100%",
              background: `linear-gradient(135deg, ${C.goldL}, ${C.gold})`,
              color: "#4a3200",
              fontSize: 16,
              fontWeight: 800,
              padding: "14px 20px",
              borderRadius: 14,
              boxShadow: "0 8px 24px rgba(240,195,85,.45)",
              textAlign: "center",
              boxSizing: "border-box",
            }}
          >
            {en ? "🔁 Rejoin now — Zoom will open" : "🔁 এখনই রিজয়েন করুন"}
          </a>
          {/* দ্বিতীয় পথ — এটা ছাড়া কেউ রিজয়েন করতে না চাইলে (যেমন ক্লাস
              শেষ হয়ে গেছে) পোর্টালে আটকে থাকতেন */}
          <Btn
            kind="soft"
            style={{ width: "100%", justifyContent: "center" }}
            onClick={onLater}
          >
            {en ? "I'll join later" : "পরে জয়েন করছি"}
          </Btn>
        </div>
      }
    >
      {en ? (
        <>
          Your teacher has moved to a <b>new Zoom meeting</b>. The old meeting
          is no longer in use — please tap the button below to join them.
          <br />
          <br />
          Your attendance is already recorded and will not be affected.
        </>
      ) : (
        <>
          আপনার উস্তাদ <b>নতুন একটি জুম মিটিংয়ে</b> সরে গেছেন। আগের মিটিংটি আর
          ব্যবহার হচ্ছে না — নিচের বাটনে চেপে তাঁর সাথে যোগ দিন।
          <br />
          <br />
          আপনার হাজিরা ইতিমধ্যেই লেখা হয়ে গেছে, এতে কিছু হবে না।
        </>
      )}
    </BlockingPopup>
  );
}

/* ═══════════ অ্যাপ ইনস্টল করার পপআপ (যাঁদের ইনস্টল করা নেই) ═══════════
   পুরো পর্দা ঢেকে দেখায়, "📲 ইনস্টল করুন" চাপলে ব্রাউজারের আসল ইনস্টল
   পপআপ খোলে।
   ⚠️ "পরে" বাটনটা কেন রাখতেই হলো: আইফোন/আইপ্যাডের সাফারিতে ওয়েবসাইট থেকে
   ইনস্টল করানোর কোনো উপায়ই নেই (অ্যাপলের সীমাবদ্ধতা) — সেখানে বাটন দিয়ে
   ইনস্টল হয় না, নিজে হাতে "Add to Home Screen" করতে হয়। ফায়ারফক্স ও কিছু
   ব্রাউজারেও একই। তাই বের হওয়ার পথ না রাখলে ওই ব্যবহারকারীরা অ্যাপে চিরকাল
   আটকে যেতেন, কিছুই করতে পারতেন না।
   তবে উপেক্ষা করা যায় না — "পরে" শুধু এইবারের জন্য, অ্যাপ আবার খুললেই
   পপআপটা আবার আসবে, যতক্ষণ না সত্যিই ইনস্টল করা হয়। */
function InstallPopup({ user }) {
  const en = user?.role === "student";
  const [ready, setReady] = useState(!!window.__tqaInstallEvent);
  const [hidden, setHidden] = useState(
    () => {
      try {
        return sessionStorage.getItem("tqa_install_dismissed") === "1";
      } catch (e) {
        return false;
      }
    },
  );
  useEffect(() => {
    const h = () => setReady(true);
    window.addEventListener("tqa-install-ready", h);
    return () => window.removeEventListener("tqa-install-ready", h);
  }, []);
  if (isInstalledApp() || hidden) return null;
  const ua = navigator.userAgent || "";
  const isIOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (ua.includes("Macintosh") && navigator.maxTouchPoints > 1);
  if (!ready && !isIOS) return null; // ইনস্টলের কোনো উপায়ই নেই — বৃথা আটকাই না
  const later = () => {
    try {
      sessionStorage.setItem("tqa_install_dismissed", "1");
    } catch (e) {
      /* উপেক্ষা */
    }
    setHidden(true);
  };
  const install = async () => {
    const evt = window.__tqaInstallEvent;
    if (!evt) return later();
    evt.prompt();
    try {
      await evt.userChoice;
    } catch (e) {
      /* উপেক্ষা */
    }
    window.__tqaInstallEvent = null;
    later();
  };
  return (
    <BlockingPopup
      icon="📲"
      zIndex={295}
      title={en ? "Install the app" : "অ্যাপটি ইনস্টল করে নিন"}
      footer={
        <div style={{ display: "grid", gap: 8 }}>
          {!isIOS && (
            <Btn
              kind="gold"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={install}
            >
              {en ? "📲 Install now" : "📲 এখনই ইনস্টল করুন"}
            </Btn>
          )}
          <Btn
            kind="soft"
            style={{ width: "100%", justifyContent: "center" }}
            onClick={later}
          >
            {en ? "Later" : "পরে"}
          </Btn>
        </div>
      }
    >
      {isIOS ? (
        en ? (
          <>
            Open the <b>Share</b> menu below and choose{" "}
            <b>“Add to Home Screen”</b>. The app will then open straight from
            your home screen — faster, and notifications will work.
          </>
        ) : (
          <>
            নিচের <b>Share</b> মেনু খুলে <b>“Add to Home Screen”</b> বেছে নিন।
            তাহলে হোম স্ক্রিন থেকেই অ্যাপটি খুলবে — দ্রুত চলবে, আর
            নোটিফিকেশনও পাবেন।
          </>
        )
      ) : en ? (
        <>
          Install the Academy app on this device. It opens faster, works like a
          real app, and you will receive class and notice alerts even when it is
          closed.
        </>
      ) : (
        <>
          এই ডিভাইসে একাডেমির অ্যাপটি ইনস্টল করে নিন। দ্রুত খুলবে, আসল অ্যাপের
          মতো চলবে, আর অ্যাপ বন্ধ থাকলেও ক্লাস ও নোটিশের খবর পেয়ে যাবেন।
        </>
      )}
    </BlockingPopup>
  );
}

/* ═══════════════ "অ্যাপটি নতুন করে ইনস্টল করুন" পপআপ ═══════════════
   অ্যাপের আইকন বা নাম বদলালে ইনস্টল করা অ্যাপে সেটা আপনাআপনি বসে না —
   উইন্ডোজ, আইপ্যাড ও অ্যান্ড্রয়েড ইনস্টলের সময়ের আইকন-নামই ধরে রাখে। তাই
   যাঁরা অ্যাপটি ইনস্টল করে ব্যবহার করছেন তাঁদের একবার নতুন করে ইনস্টল
   করতে বলতে হয়।
   • দেখায় কেবল ইনস্টল করা অ্যাপে (ব্রাউজারে খুললে নয়) — যাঁর ইনস্টলই নেই
     তাঁকে "আবার ইনস্টল করুন" বলার মানে হয় না।
   • লগইনের আগে ও পরে — দুই অবস্থাতেই আসে, কারণ overlays দুই জায়গাতেই থাকে।
     (প্রায় সবাই লগইন করাই থাকেন, তাই কেবল লগইন-পর্দায় দেখালে বেশিরভাগের
     কাছে কখনো পৌঁছাত না।)
   • একবার "বুঝেছি" চাপলে আর আসে না।
   🔧 ভবিষ্যতে আবার এমন বদল করলে নিচের NOTICE_ID-টা বদলে দিলেই যথেষ্ট —
      তখন সবার কাছে (আগে যাঁরা দেখেছেন তাঁদের কাছেও) আবার একবার করে যাবে। */
const REINSTALL_NOTICE_ID = "2026-08-icon-and-name";
const REINSTALL_SEEN_KEY = "tqa_reinstall_seen";
const isInstalledApp = () => {
  try {
    return (
      !!window.matchMedia?.("(display-mode: standalone)")?.matches ||
      window.navigator.standalone === true // আইফোন/আইপ্যাডের নিজস্ব উপায়
    );
  } catch (e) {
    return false;
  }
};
function ReinstallNotice({ lang }) {
  const en = lang === "en";
  const [show, setShow] = useState(false);
  useEffect(() => {
    if (!isInstalledApp()) return;
    try {
      if (window.localStorage.getItem(REINSTALL_SEEN_KEY) === REINSTALL_NOTICE_ID)
        return;
    } catch (e) {
      /* উপেক্ষা — দেখিয়ে দেওয়াই নিরাপদ */
    }
    setShow(true);
  }, []);
  if (!show) return null;
  const done = () => {
    try {
      window.localStorage.setItem(REINSTALL_SEEN_KEY, REINSTALL_NOTICE_ID);
    } catch (e) {
      /* উপেক্ষা */
    }
    setShow(false);
  };
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 300,
        background: "rgba(18,63,40,.72)",
        display: "grid",
        placeItems: "center",
        padding: 16,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 18,
          maxWidth: 380,
          width: "100%",
          padding: 26,
          textAlign: "center",
          fontFamily: "'Hind Siliguri', sans-serif",
        }}
      >
        <div style={{ fontSize: 40 }}>📲</div>
        <div
          style={{ fontWeight: 800, fontSize: 17, color: C.emerald, marginTop: 6 }}
        >
          {en
            ? "Please reinstall the app once"
            : "অ্যাপটি একবার নতুন করে ইনস্টল করুন"}
        </div>
        <div
          style={{
            fontSize: 13.5,
            color: C.text,
            margin: "10px 0 18px",
            lineHeight: 1.7,
            textAlign: "left",
          }}
        >
          {en ? (
            <>
              The app's logo and name have been updated. An installed app keeps
              the old logo and name, so please <b>uninstall it and install it
              again</b> — just this once.
              <br />
              <br />
              Nothing of yours will be lost. Your account and all your records
              stay exactly as they are.
            </>
          ) : (
            <>
              অ্যাপের লোগো ও নাম নতুন করা হয়েছে। ইনস্টল করা অ্যাপ পুরনো
              লোগো-নামই ধরে রাখে, তাই একবার <b>আনইনস্টল করে আবার ইনস্টল</b>{" "}
              করে নিন — শুধু এইবারের জন্য।
              <br />
              <br />
              আপনার কিছুই হারাবে না। অ্যাকাউন্ট ও সব তথ্য যেমন আছে তেমনই থাকবে।
            </>
          )}
        </div>
        <Btn
          kind="gold"
          style={{ width: "100%", justifyContent: "center" }}
          onClick={done}
        >
          {en ? "Got it" : "বুঝেছি"}
        </Btn>
      </div>
    </div>
  );
}

function UpdateBanner({ lang }) {
  const en = lang === "en";
  const [ready, setReady] = useState(false);
  const [left, setLeft] = useState(6);
  useEffect(() => {
    const cur = document
      .querySelector('script[src*="/assets/index-"]')
      ?.getAttribute("src");
    if (!cur) return; // ডেভ সার্ভার/অচেনা বিল্ড — কিছু করি না
    // ⚠️ লুপ-প্রতিরোধ: আপডেটের জন্য একবার রিফ্রেশ করার পর ১০ মিনিট আর
    // রিফ্রেশ করি না। CDN কখনো এক রিকোয়েস্টে পুরনো index.html ফেরত দিলে
    // এই প্রহরী না থাকলে পাতাটা অনন্তকাল রিলোড হতে থাকত।
    let lastReload = 0;
    try {
      lastReload = Number(window.localStorage.getItem(RELOAD_GUARD_KEY)) || 0;
    } catch (e) {
      /* উপেক্ষা */
    }
    if (Date.now() - lastReload < 10 * 60 * 1000) return;
    let stopped = false;
    const check = async () => {
      try {
        const res = await fetch("/index.html", { cache: "no-store" });
        if (!res.ok) return;
        const m = (await res.text()).match(/\/assets\/index-[A-Za-z0-9_-]+\.js/);
        if (!stopped && m && m[0] !== cur) setReady(true);
      } catch (e) {
        /* নেট সমস্যা — চুপচাপ, পরেরবার আবার দেখা হবে */
      }
    };
    check();
    const iv = setInterval(check, 10 * 60 * 1000);
    return () => {
      stopped = true;
      clearInterval(iv);
    };
  }, []);
  // নতুন সংস্করণ পাওয়া গেলে কয়েক সেকেন্ড জানিয়ে নিয়ে নিজে থেকেই রিফ্রেশ —
  // কোনো বাটন চাপতে হয় না। এই কয়েক সেকেন্ড রাখা হয়েছে যাতে পর্দা হঠাৎ
  // বদলে গেলে কেউ ঘাবড়ে না যান, কারণটা চোখে পড়ে।
  // কাজ হারানোর ভয় নেই — লগইন, খোলা পেইজ ও খোলা ফর্মের লেখা সবই আগে থেকেই
  // সংরক্ষিত থাকে, রিফ্রেশের পর যেখানে ছিলেন সেখানেই ফিরে আসবেন।
  const [waited, setWaited] = useState(0);
  useEffect(() => {
    if (!ready) return;
    if (left > 0) {
      const t = setTimeout(() => setLeft((n) => n - 1), 1000);
      return () => clearTimeout(t);
    }
    // গণনা শেষ — কিন্তু ঠিক এই মুহূর্তে কোনো সেভ সার্ভারে পাঠানো অবস্থায়
    // থাকলে রিফ্রেশ করা যাবে না। রিলোড করলে অনুরোধটা মাঝপথে কেটে যেত;
    // সার্ভার হয়তো সেটা প্রসেস করেই ফেলত, কিন্তু উত্তরটা আর ফিরত না — ফিরে
    // এসে আবার সেভ চাপলে একই রুটিন/ক্লাস দুবার তৈরি হয়ে যেতে পারত।
    // ৩০ সেকেন্ডের সীমা রাখা হয়েছে যাতে কোনো অনুরোধ আটকে গেলেও রিফ্রেশ
    // চিরকাল ঝুলে না থাকে (ওদিকে ৩০s-এ রিকোয়েস্ট নিজেই টাইমআউট করে)।
    if (hasPendingWrites() && waited < 30) {
      const t = setTimeout(() => setWaited((n) => n + 1), 1000);
      return () => clearTimeout(t);
    }
    try {
      window.localStorage.setItem(RELOAD_GUARD_KEY, String(Date.now()));
    } catch (e) {
      /* উপেক্ষা */
    }
    selfReloading = true; // "সাইট ছেড়ে যাবেন?" বাক্সটা যেন না আসে
    window.location.reload();
  }, [ready, left, waited]);
  if (!ready) return null;
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 320,
        background: "rgba(18,63,40,.6)",
        display: "grid",
        placeItems: "center",
        padding: 16,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 18,
          maxWidth: 360,
          width: "100%",
          padding: 26,
          textAlign: "center",
          fontFamily: "'Hind Siliguri', sans-serif",
        }}
      >
        <div style={{ fontSize: 40 }}>✨</div>
        <div
          style={{
            fontWeight: 800,
            fontSize: 17,
            color: C.emerald,
            marginTop: 6,
          }}
        >
          {en ? "A new update has arrived" : "নতুন আপডেট এসেছে"}
        </div>
        <div
          style={{
            fontSize: 13.5,
            color: C.text,
            margin: "8px 0 4px",
            lineHeight: 1.6,
          }}
        >
          {en
            ? "The page will refresh on its own — nothing for you to press. Your work is saved."
            : "পাতাটি নিজে থেকেই রিফ্রেশ হবে — আপনাকে কিছু চাপতে হবে না। আপনার কাজ সংরক্ষিত আছে।"}
        </div>
        <div style={{ fontSize: 13, fontWeight: 800, color: C.gold }}>
          {left > 0
            ? en
              ? `Refreshing in ${left}…`
              : `${bn(left)} সেকেন্ড পর রিফ্রেশ হচ্ছে…`
            : en
              ? "Finishing your save first…"
              : "আপনার সেভ শেষ হওয়ার অপেক্ষায়…"}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const T = (bnText, enText) => (user?.role === "student" ? enText : bnText);
  CURRENT_LANG = user?.role === "student" ? "en" : "bn"; // fmtDate সব জায়গায় এই ভাষা মেনে চলে
  const [restoring, setRestoring] = useState(hasToken());
  const [db, setDb] = useState(seedDB);
  // কোন পেজে ছিলেন তা মনে রাখি — মোবাইলে ব্যাকগ্রাউন্ডে গেলে ব্রাউজার পেজটা
  // মেমরি থেকে সরিয়ে দেয় ও ফিরে এলে নতুন করে লোড করে; আগে তখন সবসময়
  // "ওভারভিউ"-তে ফিরে যেত, চলমান কাজ হারিয়ে যেত
  const [view, setView] = useState(() => {
    try {
      return window.localStorage.getItem("tqa_view") || "overview";
    } catch {
      return "overview";
    }
  });
  const [menu, setMenu] = useState(false);
  const [bell, setBell] = useState(false);
  const [, force] = useState(0);
  const refresh = () => force((x) => x + 1);
  const [apiCourses, setApiCourses] = useState([]);
  // কোন পেজে আছেন তা মনে রাখি (ফিরে এলে সেখানেই ফিরবেন)
  useEffect(() => {
    try {
      window.localStorage.setItem("tqa_view", view);
    } catch {
      /* উপেক্ষা */
    }
  }, [view]);
  // মনে রাখা পেজটা এই রোলের জন্য বৈধ কিনা — নইলে ফাঁকা পাতা দেখাত (যেমন
  // পরিচালকের পেজ মনে রেখে পরে শিক্ষার্থী লগইন করলে)
  useEffect(() => {
    if (!user) return;
    const ok = NAV.some((n) => n.id === view && n.roles.includes(user.role));
    if (!ok) setView("overview");
  }, [user, view]);
  // ট্যাব/অ্যাপ বন্ধ করার আগে নিশ্চিতকরণ — ভুলে বন্ধ করে কাজ হারানো ঠেকাতে।
  // ব্রাউজার নিরাপত্তার কারণে এখানে নিজস্ব ডিজাইনের পপআপ দেখানো যায় না, তাই
  // ব্রাউজারের নিজের "সাইট ছেড়ে যাবেন?" বাক্সটিই আসে (হ্যাঁ/না দুটোই থাকে)
  useEffect(() => {
    if (!user) return;
    const warn = (e) => {
      // আপডেটের জন্য আমরা নিজেরাই রিফ্রেশ করছি — তখন এই সতর্কবাক্সটা এলে
      // ব্যবহারকারীকে অকারণে দুবার নিশ্চিত করতে হতো
      if (selfReloading) return;
      e.preventDefault();
      e.returnValue = "";
      return "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [user]);
  // ফোনে ইনস্টল করা অ্যাপে (ও ব্রাউজারেও) "ব্যাক" চাপলে সরাসরি বের না হয়ে
  // নিজেদের ডিজাইনের নিশ্চিতকরণ দেখাই — শিক্ষার্থীর জন্য ইংরেজিতে।
  // কীভাবে কাজ করে: লগইন থাকা অবস্থায় একটা "গার্ড" এন্ট্রি বসিয়ে রাখি; ব্যাক
  // চাপলে সেটাই সরে গিয়ে popstate আসে, তখনই আবার গার্ড বসিয়ে দিই যাতে এখনই
  // বের না হয়ে যায় (askConfirm-এ "না"-এর আলাদা কলব্যাক নেই, তাই আগেভাগে
  // বসানোই একমাত্র নিরাপদ উপায়)। "হ্যাঁ" চাপলে গার্ড খুলে সত্যিই পেছনে যাই।
  useEffect(() => {
    if (!user) return;
    let active = true;
    const pushGuard = () => {
      try {
        window.history.pushState({ tqaExitGuard: true }, "");
      } catch {
        /* উপেক্ষা */
      }
    };
    const onPop = () => {
      if (!active) return;
      pushGuard(); // এখনই বেরিয়ে যাওয়া ঠেকাই; "না" হলে এটাই বহাল থাকবে
      askConfirm(
        T("আপনি কি বের হয়ে যেতে চান?", "Do you want to exit?"),
        () => {
          active = false;
          window.removeEventListener("popstate", onPop);
          try {
            window.history.go(-2); // দুটো গার্ড এন্ট্রি পেরিয়ে সত্যিই পেছনে
          } catch {
            /* উপেক্ষা */
          }
        },
      );
    };
    pushGuard();
    window.addEventListener("popstate", onPop);
    return () => {
      active = false;
      window.removeEventListener("popstate", onPop);
    };
  }, [user]);
  // পেজ রিফ্রেশের পর সংরক্ষিত টোকেন থাকলে সেশন ফিরিয়ে আনি — শুধু রিফ্রেশ দিলে আর লগআউট হবে না
  useEffect(() => {
    // ওয়েবসাইটের "Login" (?role=...) থেকে এলে সবসময় পাসওয়ার্ড ফর্ম দেখাই —
    // আগের সেশন থাকলেও মুছে দিই, যাতে পাসওয়ার্ড ছাড়া কেউ কোনোভাবেই না ঢোকে।
    let cameFromLogin = false;
    try {
      cameFromLogin = new URLSearchParams(window.location.search).has("role");
    } catch {
      cameFromLogin = false;
    }
    if (cameFromLogin) {
      logout();
      setRestoring(false);
      return;
    }
    if (!hasToken()) {
      setRestoring(false);
      return;
    }
    let alive = true;
    getMe()
      .then((me) => {
        if (!alive) return;
        setUser({
          ...me,
          id: me.id,
          name: me.name || me.name_bn,
          sub: me.sub || me.sub_title || "",
          user: me.username,
          pass: "",
          fee: me.monthly_fee,
          salary: me.monthly_salary,
        });
      })
      .catch((e) => {
        // টোকেন সত্যিই অবৈধ (401) হলেই লগআউট; সাময়িক সার্ভার-সমস্যায় টোকেন রেখে দিই
        if (e?.status === 401) logout();
      })
      .finally(() => {
        if (alive) setRestoring(false);
      });
    return () => {
      alive = false;
    };
  }, []);
  // নিষ্ক্রিয়তায় অটো-লগআউট — ৩০ মিনিট কোনো কার্যকলাপ না থাকলে নিরাপত্তার জন্য
  // নিজে থেকেই লগআউট হয়ে যায় (শেয়ার্ড/খোলা রেখে যাওয়া কম্পিউটারের জন্য)।
  useEffect(() => {
    if (!user) return;
    const IDLE_MS = 60 * 60 * 1000; // ৬০ মিনিট (পরিচালকের নির্দেশ)
    let timer;
    const doLogout = () => {
      logout();
      setUser(null);
      setView("overview");
    };
    const reset = () => {
      clearTimeout(timer);
      timer = setTimeout(doLogout, IDLE_MS);
    };
    const events = ["mousemove", "mousedown", "keydown", "touchstart", "scroll"];
    events.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    reset();
    return () => {
      clearTimeout(timer);
      events.forEach((e) => window.removeEventListener(e, reset));
    };
  }, [user]);
  // কোর্স তালিকা API থেকে লোড — সব ভিউতে পাস করা হয়
  useEffect(() => {
    if (!user) {
      setApiCourses([]);
      return;
    }
    let alive = true;
    api
      .courses()
      .then(async (cs) => {
        const base = cs.map((c) => ({
          id: c.id,
          name: c.name,
          teacherId: c.teacher,
          teacherName: c.teacher_name,
          color: c.color,
          books: c.books || [],
          studentIds: c.students || [],
          lectures: [],
        }));
        if (alive) {
          setApiCourses(base);
        } // আগে কোর্স দেখাই, তারপর লেকচার যুক্ত হয়
        // প্রতি কোর্সের লেকচার+টপিক এনে যুক্ত করি — অগ্রগতি বার, "বাদ পড়া টপিক" ও "আজকের দারস" সঠিক দেখাতে
        const lecLists = await Promise.all(
          base.map((c) =>
            api
              .lectures(c.id)
              .then((d) => (d || []).map(adaptLecture))
              .catch(() => []),
          ),
        );
        const adapted = base.map((c, i) => ({ ...c, lectures: lecLists[i] }));
        if (alive) {
          setApiCourses(adapted);
        }
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [user?.id]);

  const [livePopup, setLivePopup] = useState(null);
  // কোন ক্লাসের রিজয়েন শিক্ষার্থী ইতিমধ্যে সেরে ফেলেছেন (আবার যেন না দেখায়)
  const [rejoinDone, setRejoinDone] = useState(null);
  // যে ক্লাসগুলোর লাইভ-পপআপে ইতিমধ্যে সাড়া দেওয়া হয়েছে (জয়েন বা "পরে")।
  // ⚠️ ছাড়া এটা: checkLive প্রতি ৬০ সেকেন্ডে livePopup আবার বসিয়ে দিত, ফলে
  // জয়েন করার পরও ক্লাসের পুরো সময় জুড়ে প্রতি মিনিটে ফুল-পেজ পপআপ ফিরে
  // আসত। রিজয়েনের পপআপ এই তালিকা মানে না — উস্তাদ নতুন লিংকে গেলে সেটা
  // আলাদাভাবেই দেখাতে হবে।
  const [livePopupDone, setLivePopupDone] = useState([]);
  const [autoJoinId, setAutoJoinId] = useState(null);
  const [receipt, setReceipt] = useState(null);
  // WhatsApp Business API অটো-সেন্ড: আউটবক্সে নতুন মেসেজ এলে ব্যাকএন্ডে পাঠায়
  useEffect(() => {
    const cfg = db.waConfig || {};
    if (!cfg.autoSend || !cfg.backendUrl) return;
    const pending = (db.waOutbox || []).filter((m) => !m.sent && !m.apiTried);
    if (!pending.length) return;
    setDb((d) => ({
      ...d,
      waOutbox: d.waOutbox.map((m) =>
        pending.some((p) => p.id === m.id)
          ? { ...m, apiTried: true, apiStatus: "sending" }
          : m,
      ),
    }));
    pending.forEach(async (m) => {
      try {
        const res = await fetch(
          cfg.backendUrl.replace(/\/+$/, "") + "/api/send-whatsapp",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ to: m.phone, text: m.text }),
          },
        );
        setDb((d) => ({
          ...d,
          waOutbox: d.waOutbox.map((x) =>
            x.id === m.id
              ? { ...x, sent: res.ok, apiStatus: res.ok ? "sent" : "failed" }
              : x,
          ),
        }));
      } catch (err) {
        setDb((d) => ({
          ...d,
          waOutbox: d.waOutbox.map((x) =>
            x.id === m.id ? { ...x, apiStatus: "failed" } : x,
          ),
        }));
      }
    });
  }, [db.waOutbox, db.waConfig]);
  const [confirmReq, setConfirmReq] = useState(null);
  const [toast, setToast] = useState(null);
  useEffect(() => {
    receiptHandler = (r) => setReceipt(r);
    confirmHandler = (c) => setConfirmReq(c);
    toastHandler = (msg) => {
      setToast(msg);
      setTimeout(() => setToast(null), 3200);
    };
    return () => {
      receiptHandler = null;
      confirmHandler = null;
      toastHandler = null;
    };
  }, []);
  const overlays = (
    <>
      <UpdateBanner lang={user?.role === "student" ? "en" : "bn"} />
      {/* জরুরি পপআপগুলো — পুরো পর্দা ঢেকে দেয়, বাটন না চাপলে সরে না।
          একসাথে একাধিক এলে zIndex অনুযায়ী উপরেরটাই আগে দেখায়:
          নোটিফিকেশন (৩০৫) → নতুন করে ইনস্টল (৩০০) → ইনস্টল (২৯৫)।
          ⚠️ নোটিফিকেশনের পপআপটা এখানে বসানো যায় না — overlays তৈরি হয়
          apiNotifs ঘোষণার আগে, তাই এখানে বসালে অ্যাপ চালু হওয়ার সাথে সাথেই
          ক্র্যাশ করত। সেটা নিচে, লগইন করা অবস্থার অংশে বসানো আছে (আর
          লগইন ছাড়া নোটিফিকেশনের প্রশ্নই আসে না)। */}
      <ReinstallNotice lang={user?.role === "student" ? "en" : "bn"} />
      <InstallPopup user={user} />
      {confirmReq && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 300,
            background: "rgba(18,63,40,.55)",
            display: "grid",
            placeItems: "center",
            padding: 16,
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 18,
              maxWidth: 380,
              width: "100%",
              padding: 24,
              textAlign: "center",
              fontFamily: "'Hind Siliguri', sans-serif",
            }}
          >
            <div style={{ fontSize: 34 }}>⚠️</div>
            <div
              style={{
                fontSize: 14.5,
                fontWeight: 700,
                color: C.text,
                margin: "10px 0 18px",
                lineHeight: 1.6,
                // বার্তায় ফাঁকা লাইন থাকলে সেটা যেন দেখা যায় (বাকি বার্তাগুলো
                // এক লাইনের, তাই তাদের চেহারা বদলায় না)
                whiteSpace: "pre-line",
              }}
            >
              {confirmReq.message}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <Btn
                kind="soft"
                style={{ flex: 1, justifyContent: "center" }}
                onClick={() => setConfirmReq(null)}
              >
                {confirmReq.no || "না, থাক"}
              </Btn>
              <Btn
                kind="danger"
                style={{ flex: 1, justifyContent: "center" }}
                onClick={() => {
                  const fn = confirmReq.onYes;
                  setConfirmReq(null);
                  fn();
                }}
              >
                {confirmReq.yes || "হ্যাঁ, নিশ্চিত"}
              </Btn>
            </div>
          </div>
        </div>
      )}
      {toast && (
        <div
          style={{
            position: "fixed",
            bottom: 22,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 310,
            background: C.emeraldD,
            color: "#fff",
            padding: "11px 20px",
            borderRadius: 99,
            fontSize: 13.5,
            fontWeight: 700,
            boxShadow: "0 8px 24px rgba(0,0,0,.3)",
            maxWidth: "90vw",
            fontFamily: "'Hind Siliguri', sans-serif",
          }}
        >
          {toast}
        </div>
      )}
    </>
  );

  // স্টুডেন্ট পোর্টাল খুললেই শিডিউল অনুযায়ী চলমান ক্লাসের ফুল-পেজ পপআপ — আগে এখানে
  // stale mock db.classes ব্যবহার হতো (একবারই, লগইনের সময়) বলে সরাসরি অ্যাডমিন
  // UI থেকে তৈরি করা কোনো ক্লাসের জন্যই এই পপআপ কখনো আসত না; এখন সরাসরি
  // /classes/today/ (backend-এই ছাত্রের নিজের ক্লাসে ফিল্টার করা) থেকে লোড হয়,
  // প্রতি ৬০ সেকেন্ডে আবার চেক হয় যাতে পোর্টাল খোলা রাখলেও ক্লাস শুরু হলে পপআপ আসে
  useEffect(() => {
    if (!user || user.role !== "student") {
      setLivePopup(null);
      return;
    }
    const checkLive = async () => {
      try {
        const classes = await api.todayClasses();
        const now = new Date();
        // ক্লাসের সময় (c.time) সবসময় বাংলাদেশ সময়ে সংরক্ষিত — তাই "এখন কয়টা
        // বাজে" এর হিসাবও বাংলাদেশ সময়েই করতে হবে, ডিভাইসের নিজস্ব টাইমজোন
        // দিয়ে নয় (নইলে বিদেশে থাকা স্টুডেন্টের জন্য এই পপআপ ভুল সময়ে আসত)
        const cur =
          ((now.getUTCHours() + DHAKA_OFFSET_HOURS) % 24) * 60 +
          now.getUTCMinutes();
        const inWindow = (c) => {
          const [h, m] = c.time.split(":").map(Number);
          const st = h * 60 + m;
          return cur >= st - 15 && cur <= st + (c.duration_min || 60); // শুরুর ১৫ মিনিট আগে থেকে শেষ পর্যন্ত "চলমান"
        };
        // ক্লাস নির্ধারিত সময়ের চেয়ে বেশি চললে (যা প্রায়ই হয়) সেটা সময়সীমার
        // বাইরে চলে যেত, আর তখন রিজয়েনের পপআপ আসত না — উস্তাদ ২য় লিংকে চলে
        // গেছেন অথচ শিক্ষার্থী ১ম মিটিংয়ে একা বসে থাকতেন। তাই রিজয়েন চালু
        // থাকা ক্লাসকে বাড়তি ৩ ঘণ্টা সময় দেওয়া হয়।
        // ⚠️ কিন্তু "সারাদিনের জন্য" নয়: rejoin_active একবার চালু হলে দিনের
        // শেষ পর্যন্ত চালুই থাকে, তাই সীমা না দিলে সকালের ক্লাসটা সারাদিন
        // অগ্রাধিকার পেত আর বিকেলের ক্লাসের পপআপ কখনো আসতই না।
        const nearby = (c) => {
          const [h, m] = c.time.split(":").map(Number);
          const st = h * 60 + m;
          return cur >= st - 15 && cur <= st + (c.duration_min || 60) + 180;
        };
        const kk =
          classes.find((c) => c.rejoin_active && nearby(c)) ||
          classes.find(inWindow);
        setLivePopup(
          kk
            ? {
                ...kk,
                courseId: kk.course,
                teacherId: kk.teacher,
                zoom: kk.zoom_link,
                zoom2: kk.zoom_link_2 || "",
                rejoinActive: !!kk.rejoin_active,
                attendance: kk.attendance || [],
                joinModeOverride: kk.join_mode_override || "auto",
                lectureNo: kk.lecture_no,
                dur: kk.duration_min,
              }
            : null,
        );
      } catch {
        /* নেটওয়ার্ক ব্যর্থ হলে চুপচাপ — পরের ৬০s-এ আবার চেষ্টা হবে */
      }
    };
    return visiblePoll(checkLive, 60000);
  }, [user]);

  const [apiNotifs, setApiNotifs] = useState(null);
  const loadNotifs = async () => {
    try {
      setApiNotifs(await api.notifications());
    } catch {
      setApiNotifs(null);
    }
  };
  useEffect(() => {
    if (user) return visiblePoll(loadNotifs, 60000);
  }, [user?.id]);

  if (restoring)
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          fontFamily: "'Hind Siliguri', sans-serif",
          background: "#f6faf7",
          color: "#1a5c3a",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <img
            src="/brand/logo-green.png"
            alt="তারবিয়াতুল কুরআন একাডেমি"
            style={{ width: 56, height: 56, borderRadius: 14 }}
          />
          <div style={{ marginTop: 10, fontWeight: 700 }}>লোড হচ্ছে…</div>
        </div>
      </div>
    );

  if (!user)
    return (
      <div
        style={{
          fontFamily: "'Hind Siliguri', 'Noto Sans Bengali', sans-serif",
        }}
      >
        {/* ফন্ট এখন index.html head-এ লোড হয় */}
        {overlays}
        <Login
          onLogin={(u) => {
            setUser(u);
            setView("overview");
          }}
        />
      </div>
    );

  const courses = myCourses(apiCourses, user);
  const myNotifs = apiNotifs
    ? apiNotifs.map((n) => ({
        id: n.id,
        text: n.text,
        date: n.created_at,
        read: n.is_read,
      }))
    : db.notifications.filter((n) => n.for.includes(user.id));
  const unread = myNotifs.filter((n) => !n.read).length;
  const markRead = async () => {
    try {
      await api.markAllRead();
      setApiNotifs(
        (prev) => prev?.map((n) => ({ ...n, is_read: true })) || null,
      );
    } catch {
      setDb((d) => ({
        ...d,
        notifications: d.notifications.map((n) =>
          n.for.includes(user.id) ? { ...n, read: true } : n,
        ),
      }));
    }
  };
  const roleLabel =
    user.role === "director"
      ? "পরিচালক"
      : user.role === "admin"
        ? "এডমিন"
        : user.role === "teacher"
          ? "উস্তাদ/উস্তাদা"
          : "Student";
  const roleColor =
    user.role === "director"
      ? C.red
      : user.role === "admin"
        ? C.emerald
        : user.role === "teacher"
          ? C.gold
          : C.blue;
  const nav = NAV.filter((n) => n.roles.includes(user.role));
  const props = { db, setDb, user, courses, refresh };
  const joinFromPopup = (k) => {
    // জুম খোলে পপআপের অ্যাংকর লিংকে; এখানে টাইমার+ভিউ
    setAutoJoinId(k.id); // হাজিরা টাইমার অটো চালু হবে
    setView("classes");
    setLivePopup(null);
    setLivePopupDone((a) => (a.includes(k.id) ? a : [...a, k.id]));
  };

  return (
    <div
      style={{
        fontFamily: "'Hind Siliguri', 'Noto Sans Bengali', sans-serif",
        background: C.cream,
        minHeight: "100vh",
        color: C.text,
      }}
    >
      <style>{`
        *{box-sizing:border-box} button:hover{filter:brightness(1.06)} ::selection{background:rgba(201,150,42,.22)}
        @media(max-width:900px){.tqa-side{position:fixed;left:0;top:0;bottom:0;z-index:80;transform:translateX(${menu ? "0" : "-105%"});transition:transform .25s;overflow-y:auto}}
        @media(min-width:901px){.tqa-side{position:sticky;top:57px;height:calc(100vh - 57px)}}`}</style>

      {/* টপবার */}
      <div
        style={{
          position: "sticky",
          top: 0,
          zIndex: 70,
          background: "#fff",
          borderBottom: `1px solid ${C.line}`,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "10px 16px",
        }}
      >
        <button
          onClick={() => setMenu(!menu)}
          style={{
            border: "none",
            background: C.cream,
            borderRadius: 8,
            width: 36,
            height: 36,
            cursor: "pointer",
            fontSize: 16,
          }}
        >
          ☰
        </button>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            flex: 1,
            minWidth: 0,
          }}
        >
          <img
            src="/brand/logo-green.png"
            alt=""
            style={{
              width: 26,
              height: 26,
              borderRadius: 7,
              flexShrink: 0,
            }}
          />
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                fontWeight: 800,
                fontSize: 14.5,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              তারবিয়াতুল কুরআন একাডেমি
            </div>
            <div style={{ fontSize: 11, color: C.muted }}>
              ম্যানেজমেন্ট সিস্টেম
            </div>
          </div>
        </div>
        <div style={{ position: "relative" }}>
          <button
            onClick={() => {
              setBell(!bell);
              if (!bell) markRead();
            }}
            style={{
              border: "none",
              background: C.cream,
              borderRadius: 8,
              width: 36,
              height: 36,
              cursor: "pointer",
              fontSize: 16,
              position: "relative",
            }}
          >
            🔔
            {unread > 0 && (
              <span
                style={{
                  position: "absolute",
                  top: -4,
                  right: -4,
                  background: C.red,
                  color: "#fff",
                  fontSize: 10,
                  fontWeight: 800,
                  borderRadius: 99,
                  padding: "1px 6px",
                }}
              >
                {bn(unread)}
              </span>
            )}
          </button>
          {bell && (
            <div
              style={{
                position: "absolute",
                right: 0,
                top: 44,
                width: 300,
                background: "#fff",
                border: `1px solid ${C.line}`,
                borderRadius: 14,
                boxShadow: "0 12px 32px rgba(26,92,58,.15)",
                padding: 10,
                zIndex: 99,
              }}
            >
              <div
                style={{ fontWeight: 800, fontSize: 13, padding: "4px 6px" }}
              >
                {T("🔔 নোটিফিকেশন", "🔔 Notifications")}
              </div>
              {myNotifs.length === 0 && (
                <div style={{ padding: 10, fontSize: 12.5, color: C.muted }}>
                  {T("কোনো নোটিফিকেশন নেই", "No notifications")}
                </div>
              )}
              {myNotifs.slice(0, 6).map((n) => (
                <div
                  key={n.id}
                  style={{
                    padding: "8px 6px",
                    borderTop: `1px solid ${C.line}`,
                    fontSize: 12.5,
                  }}
                >
                  {n.text}
                  <div style={{ fontSize: 10.5, color: C.muted }}>
                    {fmtDate(n.date)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              textAlign: "right",
              display: window.innerWidth < 480 ? "none" : "block",
            }}
          >
            <div
              style={{
                fontSize: 12.5,
                fontWeight: 700,
                maxWidth: 140,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {user.name}
            </div>
            <span style={{ fontSize: 10.5, fontWeight: 800, color: roleColor }}>
              {roleLabel}
            </span>
          </div>
          <Btn
            sm
            kind="soft"
            onClick={() => {
              // একমাত্র এখানেই keepDrafts:false — ব্যবহারকারী নিজে লগআউট
              // চাপলে তবেই খোলা ফর্মের লেখা মোছা হয়। স্বয়ংক্রিয় লগআউটে
              // (নিষ্ক্রিয়তা/টোকেন মেয়াদ/নেট গোলমাল) কিছুই মোছে না।
              logout({ keepDrafts: false });
              try {
                window.localStorage.removeItem("tqa_view");
              } catch {
                /* উপেক্ষা */
              }
              setView("overview");
              setUser(null);
            }}
          >
            {T("লগ আউট", "Log Out")}
          </Btn>
        </div>
      </div>

      {overlays}
      <NewNotifToast user={user} notifs={apiNotifs} />
      {receipt && (
        <ReceiptModal
          r={receipt}
          onClose={() => setReceipt(null)}
          db={db}
          setDb={setDb}
          sender={user}
        />
      )}
      {/* উস্তাদ রিজয়েন চালু করলে শিক্ষার্থীর পর্দা ঢেকে রিজয়েন বাটন —
          সাধারণ লাইভ-ক্লাস পপআপের বদলে এটাই দেখানো হয়, দুটো একসাথে নয় */}
      {user?.role === "student" &&
        livePopup &&
        livePopup.rejoinActive &&
        rejoinDone !== livePopup.id && (
          <RejoinBlockPopup
            k={livePopup}
            user={user}
            onRejoin={() => {
              setRejoinDone(livePopup.id);
              joinFromPopup(livePopup);
            }}
            onLater={() => {
              setRejoinDone(livePopup.id);
              setLivePopup(null);
            }}
          />
        )}
      {!(
        user?.role === "student" &&
        livePopup &&
        livePopup.rejoinActive &&
        rejoinDone !== livePopup.id
      ) &&
        livePopup &&
        !livePopupDone.includes(livePopup.id) &&
        (() => {
          // ⚠️ আগে কোর্স তালিকায় কোর্সটা না পাওয়া গেলে চুপচাপ null ফেরত যেত —
          // অর্থাৎ ক্লাসের সময় হয়ে গেলেও শিক্ষার্থী কোনো পপআপই পেতেন না, আর
          // কেন পেলেন না তা বোঝারও উপায় ছিল না। কিন্তু শিক্ষার্থী কোর্স তালিকা
          // পান কেবল তিনি Course.students-এ থাকলে (views.py → CourseViewSet),
          // আর কোর্সটি is_active থাকলে — ক্লাসে যুক্ত থাকাই যথেষ্ট নয়। ফলে
          // কোর্স নিষ্ক্রিয় হলে বা কোর্সের ছাত্র-তালিকা থেকে নাম বাদ পড়লে
          // (ক্লাসে ঠিকই থাকা সত্ত্বেও) পপআপটা হারিয়ে যেত।
          // এখন না পেলে ক্লাসের নিজের তথ্য দিয়েই পপআপ দেখাই — নাম, উস্তাদ সবই
          // ক্লাসের পেলোডেই আছে (course_name / teacher_name)।
          const found = courseById(apiCourses, livePopup.courseId);
          const c = found.id
            ? found
            : {
                id: livePopup.courseId,
                name: livePopup.course_name || "",
                teacher_name: livePopup.teacher_name || "",
                teacherId: livePopup.teacherId,
                lectures: [],
              };
          return (
            <LiveClassPopup
              k={livePopup}
              course={c}
              user={user}
              onJoin={joinFromPopup}
              onLater={() => {
                setLivePopup(null);
                setLivePopupDone((a) =>
                  a.includes(livePopup.id) ? a : [...a, livePopup.id],
                );
              }}
            />
          );
        })()}

      <div style={{ display: "flex", maxWidth: 1280, margin: "0 auto" }}>
        {/* সাইডবার */}
        <aside
          className="tqa-side"
          style={{
            width: 232,
            flexShrink: 0,
            background: `linear-gradient(180deg, ${C.emeraldD}, ${C.emerald})`,
            minHeight: "calc(100vh - 57px)",
            padding: "16px 10px",
            overflowY: "auto",
          }}
        >
          {nav.map((n) => (
            <button
              key={n.id}
              onClick={() => {
                setView(n.id);
                setMenu(false);
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                width: "100%",
                border: "none",
                cursor: "pointer",
                textAlign: "left",
                fontFamily: "inherit",
                fontSize: 13.5,
                fontWeight: 600,
                padding: "10px 14px",
                borderRadius: 12,
                marginBottom: 4,
                background:
                  view === n.id ? "rgba(255,255,255,.14)" : "transparent",
                color: view === n.id ? C.goldL : "#d7e9de",
                borderLeft:
                  view === n.id
                    ? `3px solid ${C.gold}`
                    : "3px solid transparent",
              }}
            >
              <span>{n.icon}</span>{" "}
              {user.role === "student" && n.labelEn ? n.labelEn : n.label}
            </button>
          ))}
          <div
            style={{
              marginTop: 18,
              padding: "12px 14px",
              borderRadius: 12,
              background: "rgba(255,255,255,.07)",
              color: "#cfe6d8",
              fontSize: 11.5,
              lineHeight: 1.6,
            }}
          >
            ﴾وَرَتِّلِ الْقُرْآنَ تَرْتِيلًا﴿
            <br />
            “আর কুরআন তিলাওয়াত করো ধীরে, সুস্পষ্টভাবে।” — মুযযাম্মিল ৪
          </div>
        </aside>
        {menu && (
          <div
            onClick={() => setMenu(false)}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,.3)",
              zIndex: 75,
              display: window.innerWidth > 900 ? "none" : "block",
            }}
          />
        )}

        {/* কনটেন্ট */}
        <main style={{ flex: 1, padding: "20px 18px", minWidth: 0 }}>
          {view === "overview" && <Overview {...props} goTo={setView} />}
          {view === "classes" && (
            <ClassesView
              {...props}
              autoJoinId={autoJoinId}
              onAutoJoinConsumed={() => setAutoJoinId(null)}
            />
          )}
          {view === "instantclass" && isAdm(user) && (
            <InstantClassView courses={courses} user={user} />
          )}
          {view === "postponed" && <PostponedClassesView user={user} />}
          {view === "routine" && <RoutineView {...props} />}
          {view === "lectures" && <LecturePlan {...props} />}
          {view === "syllabus" && <SyllabusView {...props} />}
          {view === "attendance" && <AttendanceView {...props} />}
          {view === "assignments" && <AssignmentsView {...props} />}
          {view === "exams" && <ExamsView {...props} />}
          {view === "progress" && <ProgressView {...props} />}
          {view === "payments" && user.role === "student" && (
            <StudentPaymentsView {...props} />
          )}
          {view === "studentpayments" && isDir(user) && (
            <DirectorPaymentsView {...props} />
          )}
          {view === "waoutbox" && isAdm(user) && <WaOutboxView {...props} />}
          {view === "teacherreport" && user.role !== "student" && (
            <TeacherReportView {...props} />
          )}
          {view === "coursemgr" && isDir(user) && (
            <CourseManagerView {...props} />
          )}
          {view === "allstudents" && isAdm(user) && (
            <AllStudentsView {...props} />
          )}
          {view === "admissions" && isAdm(user) && (
            <AdmissionsView {...props} />
          )}
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
