/**
 * TQA-MS — ফ্রন্টএন্ড API ক্লায়েন্ট (mock useState → আসল ব্যাকএন্ড)
 * ব্যবহার: import { api, login } from "./api";
 * .env (Vite): VITE_API_URL=http://localhost:8000/api
 */
const BASE = import.meta.env?.VITE_API_URL || "http://localhost:8000/api";

/* Render ফ্রি ব্যাকএন্ড ~১৫ মিনিট নিষ্ক্রিয় থাকলে ঘুমায় → পরের লোড ধীর।
   অ্যাপ খোলার সাথে সাথেই জাগানো শুরু + খোলা থাকলে প্রতি ১০ মিনিটে জাগিয়ে রাখা।
   (সম্পূর্ণ সমাধানে বাইরের cron-job.org/UptimeRobot পিংও রাখুন — README দেখুন) */
const wakeBackend = () => fetch(`${BASE}/ping/`).catch(() => {});
wakeBackend();
setInterval(wakeBackend, 10 * 60 * 1000);

/* টোকেন localStorage-এ রাখা হয় — পরিচালকের নির্দেশ: "লগআউট করার আগে কিছুই
   যাবে না"। আগে sessionStorage ছিল, ফলে ট্যাব বন্ধ করলে বা অন্য ট্যাবে গেলে
   (বিশেষত মোবাইলে, যেখানে ব্রাউজার ব্যাকগ্রাউন্ডের পেজ মেমরি থেকে সরিয়ে দেয়)
   সেশন মুছে গিয়ে চলমান কাজ হারিয়ে যেত। এখন কেবল "লগআউট" চাপলেই সেশন মোছে।
   ⚠️ ফলে ডিভাইসটি অন্য কেউ ব্যবহার করলে পাসওয়ার্ড ছাড়াই পোর্টাল খুলে ফেলতে
   পারবে — শেয়ার করা ডিভাইসে কাজ শেষে লগআউট করা জরুরি। */
const store = window.localStorage;

let access = store.getItem("tqa_access") || null;
let refresh = store.getItem("tqa_refresh") || null;

const saveTokens = (a, r) => {
  access = a; refresh = r;
  store.setItem("tqa_access", a);
  if (r) store.setItem("tqa_refresh", r);
};

/* খোলা ফর্মের সংরক্ষিত অসমাপ্ত লেখা (ড্রাফট) মুছে ফেলা।
   ⚠️ এটা কেবল দুই ক্ষেত্রেই ডাকা হয় — (১) ব্যবহারকারী নিজে লগআউট বাটন
   চাপলে, (২) একই ডিভাইসে অন্য একজন লগইন করলে (তখন আগের জনের লেখা তাঁকে
   দেখানো যাবে না)। আর কোথাও নয়। */
export const clearDrafts = () => {
  try {
    Object.keys(store)
      .filter((k) => k.startsWith("tqa_draft_"))
      .forEach((k) => store.removeItem(k));
  } catch {
    /* উপেক্ষা */
  }
};

/* সেশন শেষ করা।
   ⚠️ keepDrafts ডিফল্টভাবে true — অর্থাৎ খোলা ফর্মের লেখা মোছে না।
   কারণ logout() স্বয়ংক্রিয়ভাবেও ডাকা হয় (৩০ মিনিট নিষ্ক্রিয় থাকলে, টোকেন
   রিফ্রেশ ব্যর্থ হলে, সেশন ফেরাতে গিয়ে 401 পেলে) — সেসব ক্ষেত্রে ব্যবহারকারী
   কিছু মুছতে বলেননি, তাই তাঁর আধা-লেখা ফর্ম মুছে ফেলা যাবে না। ফিরে এসে
   আবার লগইন করলেই লেখাগুলো যেখানে ছিল সেখানেই পাবেন।
   কেবল নিজে লগআউট বাটন চাপলে keepDrafts:false পাঠানো হয়। */
export const logout = ({ keepDrafts = true } = {}) => {
  access = refresh = null;
  store.removeItem("tqa_access");
  store.removeItem("tqa_refresh");
  // পুরনো সংস্করণের রেখে যাওয়া sessionStorage টোকেনও পরিষ্কার করি
  try {
    window.sessionStorage.removeItem("tqa_access");
    window.sessionStorage.removeItem("tqa_refresh");
  } catch {
    /* উপেক্ষা */
  }
  if (!keepDrafts) clearDrafts();
};

// fetch()-এর নিজের কোনো টাইমআউট নেই — নেটওয়ার্ক গণ্ডগোলে (যেমন দুর্বল/অস্থির
// সংযোগ) একটা রিকোয়েস্ট চিরকাল ঝুলে থাকতে পারত (লোডিং স্ক্রিন অনন্তকাল ঘুরতেই
// থাকত) — তাই নির্দিষ্ট সময় পর নিজে থেকে বাতিল করে দেওয়া এই হেল্পারটা সব fetch
// কলেই (মূল রিকোয়েস্ট, টোকেন-রিফ্রেশ, ব্যাকআপ ডাউনলোড) ব্যবহার হয়। ডিফল্ট ৩০s —
// Neon কোল্ড-স্টার্টই একা ১৫-২০s নিতে পারে, তাই ২০s আগে অনেক বৈধ রিকোয়েস্টও
// (যেমন "সব রুটিনের ক্লাস তৈরি করুন" — একাধিক রুটিন × ৭ দিন ধরে লুপ চালায়)
// সময়মতো শেষ না হয়েই বাতিল/ব্যর্থ দেখাচ্ছিল
const fetchWithTimeout = (url, opts = {}, ms = 30000) => {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  return fetch(url, { ...opts, signal: ctrl.signal }).finally(() => clearTimeout(timer));
};

/* এই মুহূর্তে সার্ভারে কয়টা "লেখালেখির" রিকোয়েস্ট পাঠানো অবস্থায় আছে
   (POST/PATCH/PUT/DELETE)। GET গোনা হয় না — সেটা মাঝপথে কেটে গেলে কিছুই
   হারায় না, শুধু আবার পড়তে হয়।
   কাজে লাগে অটো-আপডেটের রিফ্রেশে: সেভ পাঠানো অবস্থায় পাতা রিলোড হলে
   অনুরোধটা মাঝপথে কেটে যেত। সার্ভার হয়তো সেটা প্রসেস করেই ফেলত, কিন্তু
   উত্তরটা আর ফিরত না — ফিরে এসে আবার সেভ চাপলে একই রুটিন/ক্লাস দুবার
   তৈরি হয়ে যেতে পারত। */
let pendingWrites = 0;
export const hasPendingWrites = () => pendingWrites > 0;

/* মূল রিকোয়েস্ট র‍্যাপার — JWT সংযুক্তি + মেয়াদ শেষে অটো-রিফ্রেশ */
async function request(path, { method = "GET", body, isForm, timeoutMs } = {}) {
  const isWrite = method !== "GET";
  const doFetch = () => {
    if (isWrite) pendingWrites += 1;
    return fetchWithTimeout(
      `${BASE}${path}`,
      {
        method,
        headers: {
          ...(access ? { Authorization: `Bearer ${access}` } : {}),
          ...(body && !isForm ? { "Content-Type": "application/json" } : {}),
        },
        body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
      },
      timeoutMs,
    ).finally(() => {
      if (isWrite) pendingWrites -= 1;
    });
  };

  // কোল্ড-স্টার্ট/সাময়িক সার্ভার সমস্যায় কয়েকবার চেষ্টা (Render ফ্রি প্ল্যান ঘুম থেকে জাগতে সময় নেয়)
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  // ⚠️ গুরুত্বপূর্ণ: POST (create) রিট্রাই করা নিরাপদ না — যদি সার্ভার আসলে রিকোয়েস্ট
  // প্রসেস করে ফেলে (রুটিন/ক্লাস তৈরি হয়ে যায়) কিন্তু রেসপন্সটা গেটওয়ে-টাইমআউটে
  // (502/503/504) হারিয়ে যায়, তাহলে রিট্রাই একই জিনিস আবার তৈরি করে ফেলবে —
  // এটাই "রুটিন ডবল ডবল হয়ে যাচ্ছে" বাগের কারণ ছিল। GET/PATCH/PUT/DELETE
  // idempotent (দুবার চালালেও একই ফলাফল), তাই এগুলোই শুধু রিট্রাই-নিরাপদ —
  // + /auth/login (দুবার সফল হলেও ক্ষতি নেই, শুধু নতুন টোকেন)
  const isSafeRetry =
    ["GET", "PATCH", "PUT", "DELETE"].includes(method) || path === "/auth/login";
  let res;
  let attempt = 0; // লুপের বাইরে ঘোষণা — পরে "এটা কি রিট্রাই ছিল" জানতে লাগে (DELETE+404 কেস)
  for (; ; attempt++) {
    try {
      res = await doFetch();
    } catch (e) {
      // নেটওয়ার্ক এরর — শুধু নিরাপদ (idempotent) রিকোয়েস্ট আবার চেষ্টা করি
      // Neon DB কোল্ড-স্টার্টে কখনো ১৫-২০ সেকেন্ডও লাগে — তাই ৩ থেকে ৫ বার বাড়ানো হলো
      if (isSafeRetry && attempt < 5) { await sleep(1500 * (attempt + 1)); continue; }
      throw e;
    }
    // 502/503/504 = গেটওয়ে/সার্ভার সাময়িক সমস্যা — শুধু নিরাপদ (idempotent) মেথডেই রিট্রাই
    if (isSafeRetry && [502, 503, 504].includes(res.status) && attempt < 5) { await sleep(1500 * (attempt + 1)); continue; }
    break;
  }
  // DELETE রিট্রাই হওয়ার পর ৪০৪ পেলে — সম্ভবত প্রথম চেষ্টাতেই আসলে ডিলিট হয়ে
  // গিয়েছিল, শুধু উত্তরটা (নেটওয়ার্ক/গেটওয়ে সমস্যায়) হারিয়ে গিয়েছিল, তাই দ্বিতীয়
  // চেষ্টায় "খুঁজে পাওয়া যায়নি" এসেছে — এটাকে ব্যর্থতা না ধরে সফলই ধরা ঠিক
  if (method === "DELETE" && attempt > 0 && res.status === 404) {
    return null;
  }
  if (res.status === 401 && refresh) {           // টোকেন মেয়াদোত্তীর্ণ → রিফ্রেশ
    try {
      const r = await fetchWithTimeout(`${BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });
      if (r.ok) {
        saveTokens((await r.json()).access, refresh);
        res = await doFetch();
      } else logout();
    } catch {
      // নেটওয়ার্ক এরর/টাইমআউট — সেশন অক্ষত রেখেই ব্যর্থতা জানাই, লগআউট নয়
      // (নইলে সাময়িক নেটওয়ার্ক গণ্ডগোলেই ভুলবশত লগআউট হয়ে যেত)
    }
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    // DRF-এর নিজস্ব exception (PermissionDenied/ValidationError ইত্যাদি) সবসময়
    // {"detail": "..."} আকারে আসে — কিন্তু পুরো অ্যাপে সব জায়গায় e?.data?.error
    // চেক করা হয় (এই অ্যাপের কাস্টম ভিউগুলো Response({"error": ...}) ব্যবহার করে
    // বলে)। ফলে detail-নির্ভর এররের আসল বার্তা কখনো দেখানো হতো না, শুধু জেনেরিক
    // "API error"/"যাচাই করুন" দেখাত। এখানে e.message-এই আসল বার্তা বসিয়ে দিলে
    // সব জায়গার (e?.data?.error || e?.message) ফলব্যাক একবারেই ঠিক হয়ে যায়।
    // সিরিয়ালাইজারের ফিল্ড-লেভেল ValidationError (যেমন AdmissionSerializer-এর
    // email/contact ভ্যালিডেশন) আরও ভিন্ন আকারে আসে — {"email": ["..."], ...} —
    // error/detail/non_field_errors কোনোটাই না থাকলে প্রথম ফিল্ডের প্রথম বার্তাটাই
    // শেষ ভরসা হিসেবে দেখানো হয়, নইলে সেটাও জেনেরিক "API error"-এ হারিয়ে যেত
    // কোন ঘরে সমস্যা তা না বললে বার্তাটা বোঝা যায় না (যেমন "Invalid pk 3" —
    // কিসের pk?), তাই ফিল্ডের নামসহ দেখানো হয়
    const firstFieldEntry = Object.entries(data).find(
      ([, v]) => Array.isArray(v) && v.length,
    );
    const firstFieldError = firstFieldEntry
      ? `${firstFieldEntry[0]}: ${firstFieldEntry[1][0]}`
      : null;
    const msg =
      // ৪০১ = টোকেন মেয়াদোত্তীর্ণ/অবৈধ (উপরে রিফ্রেশের চেষ্টাও ব্যর্থ হয়েছে) —
      // DRF-এর ইংরেজি বার্তার বদলে স্পষ্ট বাংলা নির্দেশনা দিই
      (res.status === 401
        ? "সেশনের মেয়াদ শেষ — একবার লগআউট করে আবার লগইন করুন।"
        : null) ||
      data.error ||
      data.detail ||
      (Array.isArray(data.non_field_errors) && data.non_field_errors[0]) ||
      firstFieldError ||
      "API error";
    throw Object.assign(new Error(msg), { status: res.status, data });
  }
  return res.status === 204 ? null : res.json();
}

/* ── লগইন: ফ্রন্টএন্ডের Login কম্পোনেন্টের go() এর বদলে ── */
export async function login(username, password) {
  // পুরোনো সেশন/টোকেন আগে মুছে ফেলি — নতুন লগইন সবসময় পরিষ্কার থেকে শুরু হয়;
  // ফলে ভুল পাসওয়ার্ডে আগের refresh-টোকেন দিয়ে অনিচ্ছাকৃতভাবে লগইন হয়ে যাওয়া অসম্ভব।
  logout(); // টোকেন যায়, কিন্তু ড্রাফট থাকে — কে লগইন করছেন তা এখনো জানি না
  const t = await request("/auth/login", { method: "POST", body: { username, password } });
  saveTokens(t.access, t.refresh);
  // একই ডিভাইসে আগের জনের আধা-লেখা ফর্ম নতুন ব্যবহারকারীকে দেখানো যাবে না।
  // কিন্তু একই ব্যবহারকারী আবার লগইন করলে তাঁর নিজের লেখা মুছে ফেলাও চলবে না —
  // তাই কে সর্বশেষ লগইন করেছিলেন তা মনে রেখে কেবল ভিন্ন হলেই মুছি।
  const who = String(username || "").trim().toLowerCase();
  try {
    const prev = store.getItem("tqa_last_user");
    if (prev !== null && prev !== who) clearDrafts();
    store.setItem("tqa_last_user", who);
  } catch {
    /* উপেক্ষা */
  }
  return request("/users/me/");  // {id, role, name_bn, ...} → setUser()
}

/* পেজ রিফ্রেশের পর সংরক্ষিত টোকেন দিয়ে সেশন ফিরিয়ে আনতে */
export const hasToken = () => !!access;
export const getMe = () => request("/users/me/");

/* ── রিসোর্স অনুযায়ী ফাংশন — প্রতিটি ফিচারের mock setDb এর প্রতিস্থাপন ── */
export const api = {
  // ক্লাস ও জুম জয়েন
  todayClasses: () => request("/classes/today/"),
  classes: () => request("/classes/"),
  scheduleClass: (d) => request("/classes/", { method: "POST", body: d }),
  editClass: (id, d) => request(`/classes/${id}/`, { method: "PATCH", body: d }),
  joinClass: (id) => request(`/classes/${id}/join/`, { method: "POST" }),       // নতুন সেগমেন্ট শুরু
  leaveClass: (id, minutes) => request(`/classes/${id}/leave/`, { method: "POST", body: minutes != null ? { minutes } : {} }), // সেগমেন্টের মিনিট যোগ
  checkpointClass: (id, minutes) => request(`/classes/${id}/checkpoint/`, { method: "POST", body: { minutes } }), // ব্যাকগ্রাউন্ড অটো-সেভ — presence অক্ষুণ্ণ রেখে শুধু মিনিট যোগ
  classPresence: (id) => request(`/classes/${id}/presence/`),                   // কে এখন মিটিংয়ে (দুজন-জয়েন গেটিং)
  markAttendance: (id, student_id, present = true) => request(`/classes/${id}/mark_attendance/`, { method: "POST", body: { student_id, present } }), // পরিচালকের ম্যানুয়াল হাজিরা
  postponeClass: (id) => request(`/classes/${id}/postpone/`, { method: "POST" }), // ⛔ স্থগিত
  setClassJoinMode: (id, mode) => request(`/classes/${id}/set_join_mode/`, { method: "POST", body: { mode } }), // auto/join/rejoin — জয়েন/রিজয়েন লিংক ম্যানুয়ালি জোর করা (পরিচালক/এডমিন)
  finishClass: (id) => request(`/classes/${id}/finish/`, { method: "POST" }), // ক্লাস সত্যিই শেষ — মিনিট বসে, হাজিরা পাকা হয়, ক্লাস "সম্পন্ন" হয়
  openRejoin: (id) => request(`/classes/${id}/open_rejoin/`, { method: "POST" }), // উস্তাদ রিজয়েন চাপলে — শিক্ষার্থীর কাছেও ২য় লিংক খোলে
  deleteClass: (id) => request(`/classes/${id}/`, { method: "DELETE" }),

  // হাজিরা রিপোর্ট (মাসভিত্তিক) — উস্তাদ নিজের, শিক্ষার্থী নিজের, পরিচালক সবার + এডিট/মোছা
  attendanceReport: (month) => request(`/attendance/?month=${encodeURIComponent(month)}`),
  updateAttendance: (id, d) => request(`/attendance/${id}/`, { method: "PATCH", body: d }),
  deleteAttendance: (id) => request(`/attendance/${id}/`, { method: "DELETE" }),

  // রুটিন
  routines: () => request("/routines/"),
  createRoutine: (d) => request("/routines/", { method: "POST", body: d }),
  updateRoutine: (id, d) => request(`/routines/${id}/`, { method: "PATCH", body: d }),
  deleteRoutine: (id) => request(`/routines/${id}/`, { method: "DELETE" }),
  generateRoutineClasses: () => request("/routines/generate/", { method: "POST", timeoutMs: 60000 }), // সব রুটিনের ক্লাস তৈরি (একাধিক রুটিন × ৭ দিন লুপ — সময় বেশি লাগতে পারে)

  // কোর্স · বই · সিলেবাস · লেকচার
  courses: () => request("/courses/"),
  saveCourse: (d, id) => request(id ? `/courses/${id}/` : "/courses/", { method: id ? "PATCH" : "POST", body: d }),
  deleteCourse: (id) => request(`/courses/${id}/`, { method: "DELETE" }),
  books: () => request("/books/"),
  uploadBook: (name, file) => {  // একাডেমিক বই — ডিভাইস থেকে যেকোনো ফরমেট
    const f = new FormData(); f.append("name", name); f.append("file", file);
    return request("/books/", { method: "POST", body: f, isForm: true });
  },
  addBookLink: (name, link) => request("/books/", { method: "POST", body: { name, link } }),  // Google Drive/লিংক — সাইজ সীমা নেই
  updateBookName: (id, name) => request(`/books/${id}/`, { method: "PATCH", body: { name } }),  // পরিচালক বইয়ের নাম বদলাতে পারেন (যেমন ইংরেজি করতে)
  deleteBook: (id) => request(`/books/${id}/`, { method: "DELETE" }),
  syllabus: (courseId) => request(`/syllabus/?course=${courseId}`),
  addSyllabus: (d) => request("/syllabus/", { method: "POST", body: d }),
  editSyllabus: (id, d) => request(`/syllabus/${id}/`, { method: "PATCH", body: d }),
  deleteSyllabus: (id) => request(`/syllabus/${id}/`, { method: "DELETE" }),
  // studentId দিলে ওই শিক্ষার্থীর নিজের কভার-টিক নিয়ে আসে
  lectures: (courseId, studentId) =>
    request(
      `/lectures/?course=${courseId}` +
        (studentId ? `&student=${studentId}` : ""),
    ),
  createLecture: (course, title, syllabus_item_ids, extra = {}) =>            // সিলেবাস থেকে টপিক সিলেকশন (+ ঐচ্ছিক দারস-নং/তারিখ)
    request("/lectures/", { method: "POST", body: { course, title, syllabus_item_ids, ...extra } }),
  // নতুন পথ — পরিচালকের নিজের লেখা টগল: [{id?, text, content}, ...]
  createLectureBlocks: (course, title, topic_blocks, extra = {}) =>
    request("/lectures/", {
      method: "POST",
      body: { course, title, topic_blocks, ...extra },
    }),
  editLecture: (id, d) => request(`/lectures/${id}/`, { method: "PATCH", body: d }),
  deleteLecture: (id) => request(`/lectures/${id}/`, { method: "DELETE" }),
  markTopic: (topic_id, covered, student_id) => {                 // ✔/✘ — সবুজ/লাল
    // ফ্রন্টএন্ড boolean (true/false/null) → ব্যাকএন্ড LectureTopic.Covered স্ট্রিং enum
    const v = covered === true ? "covered" : covered === false ? "missed" : "pending";
    // student_id দিলে টিকটা কেবল সেই শিক্ষার্থীর জন্য বসে, অন্য কারও নয়
    return request("/lectures/mark_topic/", {
      method: "POST",
      body: { topic_id, covered: v, ...(student_id ? { student_id } : {}) },
    });
  },

  // অ্যাসাইনমেন্ট ও পরীক্ষা
  assignments: () => request("/assignments/"),
  createAssignment: (d) => request("/assignments/", { method: "POST", body: d }),
  deleteAssignment: (id) => request(`/assignments/${id}/`, { method: "DELETE" }),
  submitAssignment: (id, { answers, file, note }) => {
    const f = new FormData();
    if (answers) f.append("answers", JSON.stringify(answers));
    if (file) f.append("file", file);
    if (note) f.append("note", note);
    return request(`/assignments/${id}/submit/`, { method: "POST", body: f, isForm: true });
  },
  gradeAssignment: (id, submission_id, mark) =>
    request(`/assignments/${id}/grade/`, { method: "POST", body: { submission_id, mark } }),
  exams: () => request("/exams/"),
  createExam: (d) => request("/exams/", { method: "POST", body: d }),
  deleteExam: (id) => request(`/exams/${id}/`, { method: "DELETE" }),
  submitExam: (id, { answers, file, note }) => {
    const f = new FormData();
    if (answers) f.append("answers", JSON.stringify(answers));
    if (file) f.append("file", file);
    if (note) f.append("note", note);
    return request(`/exams/${id}/submit/`, { method: "POST", body: f, isForm: true });
  },
  gradeExam: (id, submission_id, mark) =>
    request(`/exams/${id}/grade/`, { method: "POST", body: { submission_id, mark } }),
  examDirectMark: (id, student_id, mark) =>
    request(`/exams/${id}/direct_mark/`, { method: "POST", body: { student_id, mark } }),

  // ফি ও বেতন ও রিসিট
  myFees: () => request("/fees/"),
  myDues: () => request("/fees/dues/"),
  generateMonthlyDues: (role) => request("/fees/generate_dues/", { method: "POST", body: role ? { role } : undefined, timeoutMs: 60000 }), // চলতি মাসের বকেয়া এখনই তৈরি — role="student" দিলে কেবল স্টুডেন্ট, না দিলে সবার জন্য
  // মওকুফ — রেকর্ড মুছে না, চিহ্নিত হয়। কারণ লিখে রাখা যায়।
  waiveDue: (user_id, month_label, reason) =>
    request("/fees/waive_due/", {
      method: "POST",
      body: { user_id, month_label, ...(reason ? { reason } : {}) },
    }),
  // মওকুফ করা মাসগুলোসহ পুরো তালিকা (কে কোন মাস মওকুফ পেয়েছেন দেখাতে)
  duesWithWaived: () => request("/fees/dues/?include_waived=1"), // পরিচালক নির্দিষ্ট মাসের বকেয়া মওকুফ করে সরিয়ে দিতে পারেন
  payFee: ({ amount, month_label, method, trx_id, screenshot }) => {  // বিকাশ/নগদ/ব্যাংক + স্ক্রিনশট
    const f = new FormData();
    f.append("amount", amount); f.append("month_label", month_label);
    f.append("method", method); if (trx_id) f.append("trx_id", trx_id);
    if (screenshot) f.append("screenshot", screenshot);
    return request("/fees/", { method: "POST", body: f, isForm: true });
  },
  verifyFee: (id) => request(`/fees/${id}/verify/`, { method: "POST" }),  // কেবল পরিচালক
  deleteFee: (id) => request(`/fees/${id}/`, { method: "DELETE" }),  // ভুল/ডুপ্লিকেট পেমেন্ট মুছা — কেবল পরিচালক
  recordPayment: (d) => request("/fees/record_payment/", { method: "POST", body: d }), // পরিচালক/এডমিন সরাসরি যেকোনো স্টুডেন্টের যেকোনো মাসের পেমেন্ট "পরিশোধিত" হিসেবে সেভ করেন
  salaries: () => request("/salaries/"),
  payTeacherSalary: (d) => request("/salaries/", { method: "POST", body: d }), // বেতন পরিশোধের আসল রেকর্ড — সেই মাসের বকেয়া অটো বাদ যায়
  myReceipts: () => request("/receipts/"),
  sendReceipt: (d) => request("/receipts/", { method: "POST", body: d }),

  // ভর্তি ও ছুটি
  applyAdmission: (d) => request("/admissions/", { method: "POST", body: d }),  // পাবলিক
  admissions: () => request("/admissions/"),
  forwardAdmission: (id) => request(`/admissions/${id}/forward/`, { method: "POST" }),
  acceptAdmission: (id, opts) => request(`/admissions/${id}/accept/`, { method: "POST", body: opts }),
  rejectAdmission: (id) => request(`/admissions/${id}/reject/`, { method: "POST" }),
  replyAdmission: (id, replied) => request(`/admissions/${id}/`, { method: "PATCH", body: { replied } }),
  sendAdmissionReply: (id) => request(`/admissions/${id}/send_reply/`, { method: "POST" }), // এক ক্লিকে প্রস্তুত WhatsApp রিপ্লাই পাঠায় ও replied=true করে
  leaves: () => request("/leaves/"),
  applyLeave: (d) => request("/leaves/", { method: "POST", body: d }),
  forwardLeave: (id) => request(`/leaves/${id}/forward/`, { method: "POST" }),
  decideLeave: (id, approve) => request(`/leaves/${id}/decide/`, { method: "POST", body: { approve } }),

  // মূল্যায়ন · নোটিশ · নোটিফিকেশন · WhatsApp
  ratings: () => request("/ratings/"),
  rateClass: (d) => request("/ratings/", { method: "POST", body: d }),
  teacherRatingSummary: (teacherId) => request(`/ratings/teacher_summary/?teacher=${teacherId}`),
  studentRemarks: (studentId) => request(`/remarks/?student=${studentId}`), // টিচারের মন্তব্য — নির্দিষ্ট স্টুডেন্টের (না দিলে নিজের, স্টুডেন্ট হলে)
  addStudentRemark: (student, text) => request("/remarks/", { method: "POST", body: { student, text } }),
  myRemarks: () => request("/remarks/"), // স্টুডেন্ট নিজের সব মন্তব্য
  notices: () => request("/notices/"),
  createNotice: (d) => request("/notices/", { method: "POST", body: d }),
  deleteNotice: (id) => request(`/notices/${id}/`, { method: "DELETE" }),
  notifications: () => request("/notifications/"),
  markAllRead: () => request("/notifications/mark_all_read/", { method: "POST" }),

  // Web Push (PWA) — ব্রাউজার/ট্যাব বন্ধ থাকলেও নোটিফিকেশন পাঠাতে
  // পরিচালক সবাইকে একসাথে একটা বার্তা পাঠান — সবার নোটিফিকেশন ঘণ্টায় যায়,
  // আর যাঁরা পুশ চালু করেছেন তাঁদের ফোনে/ডেস্কটপেও (অ্যাপ বন্ধ থাকলেও)
  broadcastNotification: (text) =>
    request("/notifications/broadcast/", { method: "POST", body: { text } }),
  // কোর্সের সিলেবাস টেবিল — পরিচালকের নিজের হাতে লেখা (পড়া: সবাই, লেখা: পরিচালক)
  // কোর্সের শিক্ষার্থী তালিকা — লেকচার প্ল্যানে "কার জন্য টিক" বাছাই করতে
  // দারসের টগলে বসানোর ছবি/PDF আপলোড — ঠিকানা ফেরত আসে (কেবল পরিচালক)
  uploadLessonMedia: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/lesson-media/", { method: "POST", body: fd, isForm: true });
  },
  // ── দারস পরিকল্পনার হেডিং ও তার নিচের টপিক ──
  // studentId দিলে ওই শিক্ষার্থীর নিজের কভার-টিক নিয়ে আসে
  // trial=true দিলে ট্রায়াল অতিথিদের জন্য পরিচালকের সাজানো আলাদা পরিকল্পনা।
  // না দিলে আগের মতোই নিয়মিত পরিকল্পনা — দুটো কখনো মেশে না।
  lessonSections: (courseId, studentId, trial) =>
    request(
      `/lesson-sections/?course=${courseId}` +
        (studentId ? `&student=${studentId}` : "") +
        (trial ? "&is_trial=1" : ""),
    ),
  ensureSections: (course, trial) =>
    request("/lesson-sections/ensure/", {
      method: "POST",
      body: { course, ...(trial ? { is_trial: true } : {}) },
    }),
  addSection: (course, name, order, trial) =>
    request("/lesson-sections/", {
      method: "POST",
      body: { course, name, order, ...(trial ? { is_trial: true } : {}) },
    }),
  renameSection: (id, name) =>
    request(`/lesson-sections/${id}/`, { method: "PATCH", body: { name } }),
  delSection: (id) => request(`/lesson-sections/${id}/`, { method: "DELETE" }),
  reorderSections: (ids) =>
    request("/lesson-sections/reorder/", { method: "POST", body: { ids } }),
  saveSectionTopics: (id, topics) =>
    request(`/lesson-sections/${id}/topics/`, { method: "PUT", body: { topics } }),
  courseStudents: (courseId) => request(`/courses/${courseId}/students/`),
  syllabusSheet: (courseId) => request(`/courses/${courseId}/syllabus_sheet/`),
  saveSyllabusSheet: (courseId, headers, rows) =>
    request(`/courses/${courseId}/syllabus_sheet/`, {
      method: "PUT",
      body: { headers, rows },
    }),
  vapidPublicKey: () => request("/push/vapid-public-key/"),
  subscribePush: (sub) =>
    request("/push-subscriptions/", {
      method: "POST",
      body: {
        endpoint: sub.endpoint,
        p256dh: sub.p256dh,
        auth: sub.auth,
      },
    }),
  unsubscribePush: (endpoint) =>
    request("/push-subscriptions/unsubscribe/", { method: "POST", body: { endpoint } }),
  waOutbox: () => request("/wa-messages/"),
  waSendNow: (id) => request(`/wa-messages/${id}/send_now/`, { method: "POST" }),

  // লাইব্রেরি বই (বাহ্যিক লিংক)
  libraryBooks: () => request("/library-books/"),
  addLibraryBook: (d) => request("/library-books/", { method: "POST", body: d }),
  deleteLibraryBook: (id) => request(`/library-books/${id}/`, { method: "DELETE" }),

  // ব্যবহারকারী (পরিচালক)
  allUsers: () => request("/users/"),
  allStudents: () => request("/users/students/"),
  // ── ট্রায়াল (সাময়িক অতিথি) — কেবল পরিচালক/এডমিন ──
  trials: () => request("/trials/"),
  createTrial: (d) => request("/trials/", { method: "POST", body: d }),
  editTrial: (id, d) => request(`/trials/${id}/`, { method: "PATCH", body: d }),
  resetTrialPassword: (id) =>
    request(`/trials/${id}/reset_password/`, { method: "POST" }),
  setTrialCredentials: (id, d) =>
    request(`/trials/${id}/credentials/`, { method: "POST", body: d }),
  deleteTrial: (id) => request(`/trials/${id}/`, { method: "DELETE" }),
  // ── ট্রায়াল মূল্যায়ন — উস্তাদ লেখেন, কর্তৃপক্ষ যাচাই করে পাঠান ──
  trialReports: () => request("/trial-reports/"),
  createTrialReport: (d) => request("/trial-reports/", { method: "POST", body: d }),
  editTrialReport: (id, d) =>
    request(`/trial-reports/${id}/`, { method: "PATCH", body: d }),
  reviewTrialReport: (id) =>
    request(`/trial-reports/${id}/review/`, { method: "POST" }),
  sendTrialReport: (id) =>
    request(`/trial-reports/${id}/send/`, { method: "POST" }),
  offerTrialReport: (id) =>
    request(`/trial-reports/${id}/offer/`, { method: "POST" }),
  acceptTrialOffer: (id) =>
    request(`/trial-reports/${id}/accept/`, { method: "POST" }),
  convertTrial: (id, d) =>
    request(`/trials/${id}/convert/`, { method: "POST", body: d }),
  // যাদের এখনো স্টুডেন্ট আইডি নেই তাদের সবার জন্য তৈরি (কেবল পরিচালক)
  backfillStudentIds: () => request("/users/backfill_student_ids/", { method: "POST" }),
  allTeachers: () => request("/users/teachers/"),
  saveUser: (d, id) => request(id ? `/users/${id}/` : "/users/", { method: id ? "PATCH" : "POST", body: d }),
  deleteUser: (id) => request(`/users/${id}/`, { method: "DELETE" }),
  toggleFixCross: (id) => request(`/users/${id}/toggle_fix_cross/`, { method: "POST" }),
};

/** পরিচালকের সম্পূর্ণ ডেটা ব্যাকআপ — JSON ডাউনলোড */
export async function downloadBackup() {
  // পূর্ণ ডাটা এক্সপোর্ট (সব ইউজার/কোর্স/ফি/উপস্থিতি ইত্যাদি) স্বাভাবিক API কলের
  // চেয়ে অনেক বেশি সময় নিতে পারে, তাই টাইমআউট আরও বাড়ানো হলো (১২০s)
  let res;
  try {
    res = await fetchWithTimeout(
      `${BASE}/export/`,
      { headers: access ? { Authorization: `Bearer ${access}` } : {} },
      120000,
    );
  } catch (e) {
    // AbortController টাইমআউটে ব্রাউজারের raw বার্তা ("signal is aborted
    // without reason") সরাসরি দেখানোর বদলে বোধগম্য বাংলা মেসেজ দেখাই
    if (e?.name === "AbortError" || /aborted/i.test(e?.message || "")) {
      throw new Error("ব্যাকআপ তৈরি করতে সময় বেশি লাগছে — একটু পরে আবার চেষ্টা করুন।");
    }
    throw new Error("ব্যাকআপ নামাতে ব্যর্থ হয়েছে — সার্ভার সংযোগ যাচাই করুন।");
  }
  if (!res.ok) throw new Error("ব্যাকআপ নামাতে ব্যর্থ হয়েছে");
  const blob = await res.blob();
  const today = new Date().toISOString().slice(0, 10);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `tqa-backup-${today}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 60000);
}
