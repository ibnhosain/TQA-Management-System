/**
 * TQA-MS — ফ্রন্টএন্ড API ক্লায়েন্ট (mock useState → আসল ব্যাকএন্ড)
 * ব্যবহার: import { api, login } from "./api";
 * .env (Vite): VITE_API_URL=http://localhost:8000/api
 */
const BASE = import.meta.env?.VITE_API_URL || "http://localhost:8000/api";

let access = localStorage.getItem("tqa_access") || null;
let refresh = localStorage.getItem("tqa_refresh") || null;

const saveTokens = (a, r) => {
  access = a; refresh = r;
  localStorage.setItem("tqa_access", a);
  if (r) localStorage.setItem("tqa_refresh", r);
};

export const logout = () => {
  access = refresh = null;
  localStorage.removeItem("tqa_access");
  localStorage.removeItem("tqa_refresh");
};

/* মূল রিকোয়েস্ট র‍্যাপার — JWT সংযুক্তি + মেয়াদ শেষে অটো-রিফ্রেশ */
async function request(path, { method = "GET", body, isForm } = {}) {
  const doFetch = () =>
    fetch(`${BASE}${path}`, {
      method,
      headers: {
        ...(access ? { Authorization: `Bearer ${access}` } : {}),
        ...(body && !isForm ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });

  let res = await doFetch();
  if (res.status === 401 && refresh) {           // টোকেন মেয়াদোত্তীর্ণ → রিফ্রেশ
    const r = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (r.ok) {
      saveTokens((await r.json()).access, refresh);
      res = await doFetch();
    } else logout();
  }
  if (!res.ok) throw Object.assign(new Error("API error"), { status: res.status, data: await res.json().catch(() => ({})) });
  return res.status === 204 ? null : res.json();
}

/* ── লগইন: ফ্রন্টএন্ডের Login কম্পোনেন্টের go() এর বদলে ── */
export async function login(username, password) {
  const t = await request("/auth/login", { method: "POST", body: { username, password } });
  saveTokens(t.access, t.refresh);
  return request("/users/me/");  // {id, role, name_bn, ...} → setUser()
}

/* ── রিসোর্স অনুযায়ী ফাংশন — প্রতিটি ফিচারের mock setDb এর প্রতিস্থাপন ── */
export const api = {
  // ক্লাস ও জুম জয়েন
  todayClasses: () => request("/classes/today/"),
  classes: () => request("/classes/"),
  scheduleClass: (d) => request("/classes/", { method: "POST", body: d }),
  editClass: (id, d) => request(`/classes/${id}/`, { method: "PATCH", body: d }),
  joinClass: (id) => request(`/classes/${id}/join/`, { method: "POST" }),       // হাজিরা শুরু
  leaveClass: (id) => request(`/classes/${id}/leave/`, { method: "POST" }),     // ৪০-মিনিট হিসাব সার্ভারে
  postponeClass: (id) => request(`/classes/${id}/postpone/`, { method: "POST" }), // ⛔ স্থগিত

  // রুটিন
  routines: () => request("/routines/"),
  createRoutine: (d) => request("/routines/", { method: "POST", body: d }),

  // কোর্স · বই · সিলেবাস · লেকচার
  courses: () => request("/courses/"),
  saveCourse: (d, id) => request(id ? `/courses/${id}/` : "/courses/", { method: id ? "PATCH" : "POST", body: d }),
  deleteCourse: (id) => request(`/courses/${id}/`, { method: "DELETE" }),
  books: () => request("/books/"),
  uploadBook: (name, file) => {  // একাডেমিক বই — ডিভাইস থেকে যেকোনো ফরমেট
    const f = new FormData(); f.append("name", name); f.append("file", file);
    return request("/books/", { method: "POST", body: f, isForm: true });
  },
  deleteBook: (id) => request(`/books/${id}/`, { method: "DELETE" }),
  syllabus: (courseId) => request(`/syllabus/?course=${courseId}`),
  addSyllabus: (d) => request("/syllabus/", { method: "POST", body: d }),
  editSyllabus: (id, d) => request(`/syllabus/${id}/`, { method: "PATCH", body: d }),
  deleteSyllabus: (id) => request(`/syllabus/${id}/`, { method: "DELETE" }),
  lectures: (courseId) => request(`/lectures/?course=${courseId}`),
  createLecture: (course, title, syllabus_item_ids) =>            // সিলেবাস থেকে টপিক সিলেকশন
    request("/lectures/", { method: "POST", body: { course, title, syllabus_item_ids } }),
  editLecture: (id, d) => request(`/lectures/${id}/`, { method: "PATCH", body: d }),
  deleteLecture: (id) => request(`/lectures/${id}/`, { method: "DELETE" }),
  markTopic: (topic_id, covered) =>                               // ✔/✘ — সবুজ/লাল
    request("/lectures/mark_topic/", { method: "POST", body: { topic_id, covered } }),

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
  payFee: ({ amount, month_label, method, trx_id, screenshot }) => {  // বিকাশ/নগদ/ব্যাংক + স্ক্রিনশট
    const f = new FormData();
    f.append("amount", amount); f.append("month_label", month_label);
    f.append("method", method); if (trx_id) f.append("trx_id", trx_id);
    if (screenshot) f.append("screenshot", screenshot);
    return request("/fees/", { method: "POST", body: f, isForm: true });
  },
  verifyFee: (id) => request(`/fees/${id}/verify/`, { method: "POST" }),  // কেবল পরিচালক
  salaries: () => request("/salaries/"),
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

  // ব্যবহারকারী (পরিচালক)
  allUsers: () => request("/users/"),
  allStudents: () => request("/users/students/"),
  saveUser: (d, id) => request(id ? `/users/${id}/` : "/users/", { method: id ? "PATCH" : "POST", body: d }),
  deleteUser: (id) => request(`/users/${id}/`, { method: "DELETE" }),
  toggleFixCross: (id) => request(`/users/${id}/toggle_fix_cross/`, { method: "POST" }),
};
