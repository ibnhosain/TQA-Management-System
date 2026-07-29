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

/* নিরাপত্তা: টোকেন sessionStorage-এ রাখি (localStorage নয়)।
   ফলে ব্রাউজার/ট্যাব বন্ধ করলেই সেশন মুছে যায় — পরেরবার পোর্টাল খুললে
   আবার পাসওয়ার্ড দিতে হবে। (localStorage হলে টোকেন স্থায়ী থেকে যেত ও
   পাসওয়ার্ড ছাড়াই auto-login হতো।) পেজ রিফ্রেশে সেশন টেকে, তাই বিরক্তিকর নয়। */
const store = window.sessionStorage;

let access = store.getItem("tqa_access") || null;
let refresh = store.getItem("tqa_refresh") || null;

const saveTokens = (a, r) => {
  access = a; refresh = r;
  store.setItem("tqa_access", a);
  if (r) store.setItem("tqa_refresh", r);
};

export const logout = () => {
  access = refresh = null;
  store.removeItem("tqa_access");
  store.removeItem("tqa_refresh");
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

/* মূল রিকোয়েস্ট র‍্যাপার — JWT সংযুক্তি + মেয়াদ শেষে অটো-রিফ্রেশ */
async function request(path, { method = "GET", body, isForm, timeoutMs } = {}) {
  const doFetch = () =>
    fetchWithTimeout(
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
    );

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
  for (let attempt = 0; ; attempt++) {
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
  if (!res.ok) throw Object.assign(new Error("API error"), { status: res.status, data: await res.json().catch(() => ({})) });
  return res.status === 204 ? null : res.json();
}

/* ── লগইন: ফ্রন্টএন্ডের Login কম্পোনেন্টের go() এর বদলে ── */
export async function login(username, password) {
  // পুরোনো সেশন/টোকেন আগে মুছে ফেলি — নতুন লগইন সবসময় পরিষ্কার থেকে শুরু হয়;
  // ফলে ভুল পাসওয়ার্ডে আগের refresh-টোকেন দিয়ে অনিচ্ছাকৃতভাবে লগইন হয়ে যাওয়া অসম্ভব।
  logout();
  const t = await request("/auth/login", { method: "POST", body: { username, password } });
  saveTokens(t.access, t.refresh);
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
  lectures: (courseId) => request(`/lectures/?course=${courseId}`),
  createLecture: (course, title, syllabus_item_ids, extra = {}) =>            // সিলেবাস থেকে টপিক সিলেকশন (+ ঐচ্ছিক দারস-নং/তারিখ)
    request("/lectures/", { method: "POST", body: { course, title, syllabus_item_ids, ...extra } }),
  editLecture: (id, d) => request(`/lectures/${id}/`, { method: "PATCH", body: d }),
  deleteLecture: (id) => request(`/lectures/${id}/`, { method: "DELETE" }),
  markTopic: (topic_id, covered) => {                             // ✔/✘ — সবুজ/লাল
    // ফ্রন্টএন্ড boolean (true/false/null) → ব্যাকএন্ড LectureTopic.Covered স্ট্রিং enum
    const v = covered === true ? "covered" : covered === false ? "missed" : "pending";
    return request("/lectures/mark_topic/", { method: "POST", body: { topic_id, covered: v } });
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
  waiveDue: (user_id, month_label) => request("/fees/waive_due/", { method: "POST", body: { user_id, month_label } }), // পরিচালক নির্দিষ্ট মাসের বকেয়া মওকুফ করে সরিয়ে দিতে পারেন
  payFee: ({ amount, month_label, method, trx_id, screenshot }) => {  // বিকাশ/নগদ/ব্যাংক + স্ক্রিনশট
    const f = new FormData();
    f.append("amount", amount); f.append("month_label", month_label);
    f.append("method", method); if (trx_id) f.append("trx_id", trx_id);
    if (screenshot) f.append("screenshot", screenshot);
    return request("/fees/", { method: "POST", body: f, isForm: true });
  },
  verifyFee: (id) => request(`/fees/${id}/verify/`, { method: "POST" }),  // কেবল পরিচালক
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
  leaves: () => request("/leaves/"),
  applyLeave: (d) => request("/leaves/", { method: "POST", body: d }),
  forwardLeave: (id) => request(`/leaves/${id}/forward/`, { method: "POST" }),
  decideLeave: (id, approve) => request(`/leaves/${id}/decide/`, { method: "POST", body: { approve } }),

  // মূল্যায়ন · নোটিশ · নোটিফিকেশন · WhatsApp
  ratings: () => request("/ratings/"),
  rateClass: (d) => request("/ratings/", { method: "POST", body: d }),
  teacherRatingSummary: (teacherId) => request(`/ratings/teacher_summary/?teacher=${teacherId}`),
  notices: () => request("/notices/"),
  notifications: () => request("/notifications/"),
  markAllRead: () => request("/notifications/mark_all_read/", { method: "POST" }),
  waOutbox: () => request("/wa-messages/"),
  waSendNow: (id) => request(`/wa-messages/${id}/send_now/`, { method: "POST" }),

  // লাইব্রেরি বই (বাহ্যিক লিংক)
  libraryBooks: () => request("/library-books/"),
  addLibraryBook: (d) => request("/library-books/", { method: "POST", body: d }),
  deleteLibraryBook: (id) => request(`/library-books/${id}/`, { method: "DELETE" }),

  // ব্যবহারকারী (পরিচালক)
  allUsers: () => request("/users/"),
  allStudents: () => request("/users/students/"),
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
