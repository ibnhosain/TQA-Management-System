/* ═══════════ পরীক্ষার জন্য api.js-এর নকল ═══════════
   আসল সার্ভারে না গিয়ে সাথে সাথেই তথ্য ফেরত দেয়, তাই কম্পোনেন্টগুলো
   "লোড হচ্ছে" পেরিয়ে আসল অবস্থায় পৌঁছায় — আর সেখানেই বাগ লুকিয়ে থাকে।

   ⚠️ এই ফাইলটি কেবল test/vite.config.js-এর alias দিয়ে বসে। চালু
   সাইটের বিল্ডে এর কিছুই যায় না। */
const VERSE = "قُلْ هُوَ ٱللَّهُ أَحَدٌ";
const slide = (heading) => ({
  kind: "verse", heading, arabic: VERSE, arabic_locked: true,
  translit: "Qul huwal-lahu ahad", text: "👂", image: "", audio: "",
});
const mkStep = (i) => ({
  id: 100 + i, lesson: 1, order: i, section: "Step " + i,
  teacher_says: "Say line " + i, teacher_does: "Recite.",
  student_does: "Listens.", expected: "CHECK", correction: "", note: "",
  seconds: 40, topic: null, is_active: true,
  // ⚠️ একটি ধাপ ইচ্ছা করেই স্লাইডহীন — সেটাও যেন ভাঙে না
  slide: i === 2 ? null : slide("Line " + i),
});

export const LESSON = {
  id: 1, course: 1, course_name: "Easy Noorani Qaida",
  title: "Surah Al-Ikhlas", title_ar: "الإخلاص", kind: "memorization",
  age_from: 5, age_to: 7, duration_min: 25,
  objectives: "<p><b>Goal</b></p><ul><li>x</li></ul>",
  status: "published", order: 0, step_count: 4,
  // দারস পরিকল্পনার টপিকের সাথে যুক্ত
  topic: 11, topic_text: "Al-Ikhlas-الإخلاص", section: 1,
  steps: [0, 1, 2, 3].map(mkStep),
};
export const EMPTY_LESSON = {
  ...LESSON, id: 2, title: "খালি দারস", step_count: 0, steps: [],
};
// ⚠️ টপিকহীন স্ক্রিপ্ট — পুরনো লেখা, "টপিকের বাইরে" দলে দেখানো হয়
export const LOOSE_LESSON = {
  ...LESSON, id: 5, title: "পুরনো স্ক্রিপ্ট",
  topic: null, topic_text: null, section: null,
};

/* দারস পরিকল্পনার হেডিং ও টপিক — পাতাটি এগুলো ধরেই সাজে।
   টপিক ১১-এ স্ক্রিপ্ট আছে, ১২ ও ২১-এ নেই — দুই অবস্থাই পরীক্ষা হয়। */
const SECTIONS = [
  { id: 1, course: 1, name: "Memorized Surah", order: 0, is_trial: false,
    topics: [
      { id: 11, text: "Al-Ikhlas-الإخلاص", section: 1, order: 0,
        content: "", covered: "pending" },
      { id: 12, text: "Al-Kawthar-الكوثر", section: 1, order: 1,
        content: "", covered: "pending" },
    ] },
  { id: 2, course: 1, name: "Memorized Hadith", order: 1, is_trial: false,
    topics: [
      { id: 21, text: "Hadith -N-01", section: 2, order: 0,
        content: "", covered: "pending" },
    ] },
];
const PROGRESS = [
  { id: 1, student: 9, student_name: "S", lesson: 1,
    lesson_title: "Surah Al-Ikhlas", course: 1, lesson_status: "published",
    status: "learning", times_taught: 2, last_taught: "2026-08-26",
    last_step: 1, note: "৪ নং আয়াতে থামে", updated_at: "2026-08-26T00:00:00Z" },
  // ⚠️ খসড়া দারস — শিক্ষার্থীর "Revise" বোতামটি এখানে আসা উচিত নয়
  { id: 2, student: 9, student_name: "S", lesson: 2, lesson_title: "খালি দারস",
    course: 1, lesson_status: "draft", status: "mastered", times_taught: 1,
    last_taught: null, last_step: 0, note: "", updated_at: "2026-08-26T00:00:00Z" },
];

/* "empty" মোডে সব তালিকা খালি — কিছু না থাকার দৃশ্যগুলো পরীক্ষা করতে */
let MODE = "full";
export const setMode = (m) => { MODE = m; };

export const api = {
  lessons: async () => (MODE === "empty" ? [] : [
    LESSON,
    // একই টপিকের আরেক বয়সের সংস্করণ
    { ...LESSON, id: 3, age_from: 9, age_to: 12, status: "draft" },
    LOOSE_LESSON,
  ]),
  lessonSections: async () => (MODE === "empty" ? [] : SECTIONS),
  lesson: async (id) => (Number(id) === 2 ? EMPTY_LESSON : LESSON),
  lessonStage: async () => ({
    id: 1, title: LESSON.title, title_ar: LESSON.title_ar,
    steps: LESSON.steps.map((s) => ({ id: s.id, order: s.order, slide: s.slide })),
  }),
  addLesson: async () => LESSON,
  editLesson: async () => LESSON,
  delLesson: async () => ({}),
  duplicateLesson: async () => ({ ...LESSON, id: 4 }),
  seedSampleLesson: async () => LESSON,
  addLessonStep: async () => mkStep(9),
  editLessonStep: async () => mkStep(0),
  delLessonStep: async () => ({}),
  reorderLessonSteps: async () => ({ ok: true }),
  lessonProgress: async () => (MODE === "empty" ? [] : PROGRESS),
  markLessonProgress: async () => PROGRESS[0],
  editLessonProgress: async () => PROGRESS[0],
  courseLearners: async () => (MODE === "empty" ? [] : [
    { id: 9, name: "S", student_id: "SH-1", is_trial: false },
    { id: 10, name: "G", student_id: "", is_trial: true },
  ]),
  courseStudents: async () => [{ id: 9, name: "S", student_id: "SH-1" }],
  uploadLessonMedia: async () => ({ url: "x" }),
};

export const login = async () => ({});
export const logout = () => {};
export const getMe = async () => ({});
export const hasToken = () => true;
export const downloadBackup = async () => {};
export const hasPendingWrites = () => false;
export const clearDrafts = () => {};
