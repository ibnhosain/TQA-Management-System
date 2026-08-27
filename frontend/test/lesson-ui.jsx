/* ═══════════ দারস-ব্যবস্থার ব্রাউজার পরীক্ষা ═══════════

   কেন এটা দরকার — বিল্ড পাস করা বা ব্যাকএন্ডের টেস্ট যথেষ্ট নয়। দুটো বাগ
   পরিচালকের সামনেই পাতা ভেঙে দিয়েছিল, দুটোই "তথ্য আসার পরের" অবস্থায়:
     • statusTag is not defined        — দারসের তালিকা খুললেই
     • Cannot read properties of null  — দারস "খুলুন" চাপলেই
   সার্ভার-সাইড রেন্ডারে useEffect চলে না বলে ওই অবস্থাটা কখনো পরীক্ষাই
   হতো না। এখানে সত্যিকারের DOM-এ, এফেক্টসহ, বোতামে চাপ দিয়ে চালানো হয় —
   দুটো বাগই এখানে ধরা পড়ে (বাগসহ সংস্করণে চালিয়ে যাচাই করা হয়েছে)।

   চালাতে:  npm run test:ui                                             */
import React, { act } from "react";
import { createRoot } from "react-dom/client";
import * as M from "../src/tqa-management-system.jsx";
import { setMode, LESSON } from "./api-stub.js";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const nop = () => {};
let ran = 0;
const failures = [];

/* একটি দৃশ্য — আঁকা, এফেক্ট চলা, তথ্য আসা, তারপর (চাইলে) বোতামে চাপ */
async function scene(
  name,
  node,
  { expect = [], notExpect = [], click = [] } = {},
) {
  ran++;
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  const errs = [];
  const onErr = (e) =>
    errs.push(e?.error?.message || e?.reason?.message || String(e));
  window.addEventListener("error", onErr);
  window.addEventListener("unhandledrejection", onErr);
  const settle = async () => {
    for (let i = 0; i < 6; i++) {
      await act(async () => {
        await sleep(0);
      });
    }
  };
  try {
    await act(async () => {
      root.render(node);
    });
    await settle();
    for (const label of click) {
      const btn = [...host.querySelectorAll("button")].find((b) =>
        (b.textContent || "").includes(label),
      );
      if (!btn) throw new Error(`“${label}” বোতামটি পাওয়া গেল না`);
      await act(async () => {
        btn.click();
      });
      await settle();
    }
    for (const want of expect) {
      if (!(host.textContent || "").includes(want))
        throw new Error(`পর্দায় “${want}” নেই`);
    }
    // যা পর্দায় থাকার কথা *নয়* — যেমন উস্তাদের কাছে সম্পাদনার বোতাম
    for (const no of notExpect) {
      if ((host.textContent || "").includes(no))
        throw new Error(`পর্দায় “${no}” থাকার কথা নয়`);
    }
    if (errs.length) throw new Error(errs[0]);
  } catch (e) {
    failures.push(`${name} → ${e?.message || e}`);
  } finally {
    window.removeEventListener("error", onErr);
    window.removeEventListener("unhandledrejection", onErr);
    try {
      await act(async () => {
        root.unmount();
      });
    } catch (e) {
      /* উপেক্ষা */
    }
    host.remove();
  }
}

const teacher = { id: 7, role: "teacher", name_bn: "U" };
const director = { id: 1, role: "director", name_bn: "D" };
const courses = [{ id: 1, name: "Easy Noorani Qaida", teacherId: 7 }];

export async function run() {
  /* ───── তথ্য আসার পরের আসল অবস্থা ───── */
  await scene(
    "সম্পাদক খোলা (পরিচালক)",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    { expect: ["Surah Al-Ikhlas", "পড়ানোর ধাপ", "কাঙ্ক্ষিত ফল"] },
  );
  await scene(
    "সম্পাদক খোলা (কেবল দেখা)",
    <M.LessonEditor id={1} canEdit={false} onClose={nop} />,
    { expect: ["Surah Al-Ikhlas"] },
  );
  await scene(
    "সম্পাদক — ধাপহীন দারস",
    <M.LessonEditor id={2} canEdit onClose={nop} />,
    { expect: ["এখনো কোনো ধাপ নেই"] },
  );
  await scene(
    "দারসের তালিকা (উস্তাদ) — হেডিং ও টপিক ধরে",
    <M.LessonsView user={teacher} courses={courses} />,
    {
      expect: [
        "Memorized Surah", "Memorized Hadith",   // হেডিং
        "Al-Ikhlas-الإخلاص",                      // যে টপিকে স্ক্রিপ্ট আছে
        "শিক্ষক মোড",
        "টপিকের বাইরে", "পুরনো স্ক্রিপ্ট",        // টপিকহীন স্ক্রিপ্ট
      ],
    },
  );
  await scene(
    "দারসের তালিকা (পরিচালক) — স্ক্রিপ্টহীন টপিকও দেখায়",
    <M.LessonsView user={director} courses={courses} />,
    {
      expect: [
        "Al-Kawthar-الكوثر", "Hadith -N-01",      // স্ক্রিপ্ট নেই এমন টপিক
        "এখনো স্ক্রিপ্ট লেখা হয়নি", "স্ক্রিপ্ট লিখুন",
        "১/২ টপিকে স্ক্রিপ্ট আছে",                 // হেডিংয়ের গণনা
      ],
    },
  );
  await scene("শিক্ষক মোড", <M.TeacherMode id={1} onClose={nop} />, {
    expect: ["Say line 0", "শিক্ষার্থী এখন যা দেখছেন"],
  });
  await scene("উপস্থাপনা উইন্ডো", <M.PresentWindow />);
  await scene(
    "অগ্রগতির পাতা",
    <M.ProgressPanel lesson={LESSON} atStep={1} onClose={nop} />,
    { expect: ["S", "ট্রায়াল অতিথি", "মুখস্থ হয়েছে"] },
  );
  await scene("শিক্ষার্থীর দারস", <M.StudentLessonsView />, {
    expect: ["My Lessons", "Revise", "Ask your teacher"],
  });
  await scene(
    "শিক্ষার্থীর পুনরাবৃত্তি পর্দা",
    <M.StudentLessonPlayer lessonId={1} title="T" onClose={nop} />,
    { expect: ["Next"] },
  );
  await scene(
    "ক্লাস থেকে শিক্ষক মোড",
    <M.TeachFromClass courseId={1} label="Q" />,
    { expect: ["শিক্ষক মোড"] },
  );

  /* ───── কিছুই না থাকার দৃশ্য ───── */
  setMode("empty");
  await scene(
    "তালিকা — কোনো হেডিং বা দারস নেই",
    <M.LessonsView user={director} courses={courses} />,
    { expect: ["এখনো দারস পরিকল্পনার কোনো হেডিং নেই"] },
  );
  await scene(
    "অগ্রগতি — কোনো শিক্ষার্থী নেই",
    <M.ProgressPanel lesson={LESSON} onClose={nop} />,
    { expect: ["কোনো শিক্ষার্থী নেই"] },
  );
  await scene("শিক্ষার্থীর দারস — কিছু নেই", <M.StudentLessonsView />, {
    expect: ["will appear here"],
  });
  setMode("full");

  /* ───── বোতামে চাপ: আসল ব্যবহারের পথ ───── */
  await scene(
    "সম্পাদকে ধাপ খোলা ও গোটানো",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    { click: ["খুলুন", "গুটিয়ে নিন"] },
  );
  await scene(
    "সম্পাদকে নতুন ধাপ",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    { click: ["+ নতুন ধাপ"] },
  );
  await scene(
    "তালিকা → দারস খোলা → ফেরা",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["✏️ খুলুন", "← দারসের তালিকা"] },
  );
  await scene(
    "টপিকের নামে চাপলেই স্ক্রিপ্ট খোলে",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["Al-Ikhlas-الإخلاص"], expect: ["পড়ানোর ধাপ"] },
  );
  await scene(
    "স্ক্রিপ্টহীন টপিক → ✍️ স্ক্রিপ্ট লিখুন → বিকল্প দেখায়",
    <M.LessonsView user={director} courses={courses} />,
    {
      click: ["✍️ স্ক্রিপ্ট লিখুন"],
      expect: ["খালি থেকে শুরু", "নমুনা — সূরা আল-ইখলাস",
               "নমুনা — Noorani Qaida"],
    },
  );
  await scene(
    "স্ক্রিপ্টহীন টপিক → নমুনা থেকে শুরু",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["✍️ স্ক্রিপ্ট লিখুন", "নমুনা — সূরা আল-ইখলাস"],
      expect: ["পড়ানোর ধাপ"] },
  );
  /* ───── ধাপ ২ — হেডিং ও টপিক এখান থেকেই ───── */
  await scene(
    "পরিচালক হেডিংয়ের বোতামগুলো দেখেন",
    <M.LessonsView user={director} courses={courses} />,
    { expect: ["✏️ টপিক", "নাম", "➕ নতুন হেডিং"] },
  );
  await scene(
    "উস্তাদ হেডিং সাজাতে পারেন না",
    <M.LessonsView user={teacher} courses={courses} />,
    { expect: ["Memorized Surah"], notExpect: ["➕ নতুন হেডিং", "✏️ টপিক"] },
  );
  await scene(
    "➕ নতুন হেডিং → নাম লেখার পাতা",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["➕ নতুন হেডিং"], expect: ["নতুন হেডিং", "হেডিংয়ের নাম"] },
  );
  await scene(
    "নাম → হেডিংয়ের নাম বদলানোর পাতা",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["নাম"], expect: ["হেডিংয়ের নাম", "Memorized Surah"] },
  );
  await scene(
    "✏️ টপিক → টপিক সাজানোর পাতা",
    <M.LessonsView user={director} courses={courses} />,
    {
      click: ["✏️ টপিক"],
      expect: ["টপিক সাজান", "Al-Ikhlas-الإخلاص", "Al-Kawthar-الكوثر",
               "স্ক্রিপ্ট আছে", "+ যোগ", "💾 সংরক্ষণ করুন"],
    },
  );
  await scene(
    "টপিক সাজানো → যোগ করে সংরক্ষণ",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["✏️ টপিক", "+ যোগ", "💾 সংরক্ষণ করুন"] },
  );

  await scene(
    "সম্পাদকে টপিক বেছে দেওয়া যায়",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    { expect: ["দারস পরিকল্পনার টপিক", "কোনো টপিকের সাথে যুক্ত নয়"] },
  );
  await scene(
    "তালিকা → শিক্ষক মোড → বন্ধ",
    <M.LessonsView user={teacher} courses={courses} />,
    { click: ["▶️ শিক্ষক মোড", "✕ বন্ধ"] },
  );
  await scene(
    "তালিকা → অগ্রগতি",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["📈 অগ্রগতি"] },
  );
  await scene(
    "তালিকা → বয়সের সংস্করণ",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["➕ বয়সের সংস্করণ"] },
  );
  await scene(
    "শিক্ষক মোড → পরের ধাপ → অগ্রগতি",
    <M.TeacherMode id={1} onClose={nop} />,
    { click: ["পরের ধাপ", "পরের ধাপ", "📈 অগ্রগতি"] },
  );
  await scene(
    "শিক্ষক মোড → ধাপের তালিকা, লক্ষ্য, অক্ষরের আকার, ঘড়ি",
    <M.TeacherMode id={1} onClose={nop} />,
    { click: ["☰ ধাপ", "🎯 লক্ষ্য", "A+", "A−", "⏸"] },
  );
  await scene(
    "ক্লাস → শিক্ষক মোড চালু",
    <M.TeachFromClass courseId={1} label="Q" />,
    { click: ["📗 শিক্ষক মোড"] },
  );
  await scene("শিক্ষার্থী → Revise → Next → Close", <M.StudentLessonsView />, {
    click: ["🔁 Revise", "Next", "Close"],
  });

  console.log(`\n  ${ran} রকম দৃশ্য চালানো হলো (এফেক্ট ও ক্লিকসহ)`);
  if (failures.length) {
    console.log(`\n❌ ব্যর্থ ${failures.length}টি:`);
    failures.forEach((f) => console.log("   • " + f));
  } else {
    console.log("  ✅ সবগুলো ঠিক আছে");
  }
  return failures.length;
}
