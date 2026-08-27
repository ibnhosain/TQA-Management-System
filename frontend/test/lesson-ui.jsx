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
import { setMode, reset, LESSON } from "./api-stub.js";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* পর্দা ছাড়াই যেসব নিয়ম যাচাই করা যায় — যেমন কোন ঘরগুলো পর্দায় যেতে পারে */
function check(name, fn) {
  ran++;
  try {
    fn();
  } catch (e) {
    failures.push(`${name} → ${e.message}`);
  }
}
const eq = (a, b, why) => {
  if (JSON.stringify(a) !== JSON.stringify(b))
    throw new Error(`${why} · পেলাম ${JSON.stringify(a)}`);
};
const nop = () => {};
let ran = 0;
const failures = [];

/* একটি দৃশ্য — আঁকা, এফেক্ট চলা, তথ্য আসা, তারপর (চাইলে) বোতামে চাপ */
/* React-এর নিজস্ব মান-ট্র্যাকিং পাশ কাটিয়ে সত্যিকারের টাইপিং —
   শুধু value বসালে React বদলটা টেরই পায় না */
function typeInto(el, text) {
  const proto =
    el.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
  setter.call(el, text);
  el.dispatchEvent(new window.Event("input", { bubbles: true }));
}

/* click ও type একই তালিকায় রাখা যায়, তাই ক্রম ঠিক থাকে:
     steps: [["click", "খুলুন"], ["type", "Say line 0", "নতুন"], …]        */
async function scene(
  name,
  node,
  { expect = [], notExpect = [], click = [], steps = [], mode } = {},
) {
  ran++;
  // প্রতিটি দৃশ্য আগের অবস্থা থেকেই শুরু হোক
  reset();
  if (mode) setMode(mode);
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
    const all = [...click.map((c) => ["click", c]), ...steps];
    for (const [what, where, text] of all) {
      if (what === "click") {
        /* ⚠️ হুবহু মিল আগে, তারপর আংশিক — নইলে "খুলুন" খুঁজতে গিয়ে
           "🔓 তালা খুলুন"-এ চাপ পড়ে যেত */
        const all_btn = [...host.querySelectorAll("button")];
        const btn =
          all_btn.find((b) => (b.textContent || "").trim() === where) ||
          all_btn.find((b) => (b.textContent || "").includes(where));
        if (!btn) {
          const have = [...host.querySelectorAll("button")]
            .map((b) => JSON.stringify((b.textContent || "").slice(0, 20)))
            .join(", ");
          throw new Error(
            `“${where}” বোতামটি পাওয়া গেল না · আছে: ${have || "(কিছুই নয়)"}`,
          );
        }
        await act(async () => {
          btn.click();
        });
      } else {
        const box = [...host.querySelectorAll("textarea, input")].find(
          (b) => (b.value || "") === where,
        );
        if (!box) {
          const have = [...host.querySelectorAll("textarea, input")]
            .map((b) => JSON.stringify((b.value || "").slice(0, 24)))
            .join(", ");
          throw new Error(
            `“${where}” ঘরটি পাওয়া গেল না · আছে: ${have || "(কিছুই নয়)"}`,
          );
        }
        await act(async () => {
          typeInto(box, text);
        });
      }
      await settle();
    }
    /* ⚠️ ঘরের ভেতরের লেখা (input/textarea-এর value) textContent-এ আসে
       না — অথচ পরিচালক ওটাই দেখেন। তাই দুটোই মিলিয়ে খোঁজা হয়। */
    const seen =
      (host.textContent || "") +
      " " +
      [...host.querySelectorAll("input, textarea")]
        .map((b) => b.value || "")
        .join(" ");
    for (const want of expect) {
      if (!seen.includes(want)) throw new Error(`পর্দায় “${want}” নেই`);
    }
    // যা পর্দায় থাকার কথা *নয়* — যেমন উস্তাদের কাছে সম্পাদনার বোতাম
    for (const no of notExpect) {
      if (seen.includes(no)) throw new Error(`পর্দায় “${no}” থাকার কথা নয়`);
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
  /* ───── ধাপ ৩ — স্ক্রিপ্ট থেকে লেকচার প্ল্যানে কভার ───── */
  await scene(
    "অগ্রগতির পাতায় কভারের ব্যবস্থা",
    <M.ProgressPanel lesson={LESSON} atStep={1} onClose={nop} />,
    {
      expect: [
        "Al-Ikhlas-الإخلاص",              // কোন টপিকে বসবে তা বলে দেয়
        "প্রত্যেকের হিসাব আলাদা",
        "দারস পরিকল্পনায় কভার ✔",         // ৯ নং আগেই কভার করা
        "↩️ টিকটি ফিরিয়ে নিন",
        "ট্রায়াল অতিথির দারস পরিকল্পনা আলাদা", // অতিথির জন্য বোতাম নয়
      ],
    },
  );
  await scene(
    "কভার ফিরিয়ে নিয়ে আবার বসানো",
    <M.ProgressPanel lesson={LESSON} atStep={1} onClose={nop} />,
    {
      click: ["↩️ টিকটি ফিরিয়ে নিন", "✔ কভার হয়েছে চিহ্নিত করুন"],
      expect: ["দারস পরিকল্পনায় কভার ✔"],
    },
  );
  await scene(
    "টপিকহীন স্ক্রিপ্টে কভারের বোতাম আসে না",
    <M.ProgressPanel
      lesson={{ ...LESSON, topic: null, topic_text: null }}
      onClose={nop}
    />,
    {
      expect: ["কোনো টপিকের সাথে যুক্ত নয়"],
      notExpect: ["✔ কভার হয়েছে চিহ্নিত করুন"],
    },
  );
  await scene(
    "শিক্ষক মোডের শেষ ধাপে কভারের পাতা খোলে",
    <M.TeacherMode id={1} onClose={nop} />,
    {
      click: ["পরের ধাপ", "পরের ধাপ", "পরের ধাপ", "✓ শেষ — অগ্রগতি ও কভার"],
      expect: ["প্রত্যেকের হিসাব আলাদা"],
    },
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
  await scene(
    "তালিকা — কোনো হেডিং বা দারস নেই",
    <M.LessonsView user={director} courses={courses} />,
    { expect: ["এখনো দারস পরিকল্পনার কোনো হেডিং নেই"], mode: "empty" },
  );
  await scene(
    "অগ্রগতি — কোনো শিক্ষার্থী নেই",
    <M.ProgressPanel lesson={LESSON} onClose={nop} />,
    { expect: ["কোনো শিক্ষার্থী নেই"], mode: "empty" },
  );
  await scene("শিক্ষার্থীর দারস — কিছু নেই", <M.StudentLessonsView />, {
    expect: ["will appear here"], mode: "empty",
  });

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

  /* ───── শিশুদের পর্দার সাজ ───── */
  for (const [kind, label] of M.SLIDE_KINDS) {
    await scene(
      `স্লাইডের সাজ — ${label}`,
      <M.SlidePreview
        slide={{
          kind,
          heading: "শিরোনাম",
          arabic: "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
          translit: "Qul huwal-lahu ahad",
          text: "পর্দার লেখা",
          image: "",
        }}
      />,
      // ⚠️ নকশা যেন লেখাকে ঢেকে না দেয় — সবই পর্দায় থাকা চাই
      { expect: ["শিরোনাম", "قُلْ هُوَ ٱللَّهُ أَحَدٌ", "পর্দার লেখা"] },
    );
    const [bg, art] = M.artOf(kind);
    if (!bg) throw new Error(`${kind} — পটভূমির রং নেই`);
    if (!art) throw new Error(`${kind} — নকশার ধরন নেই`);
  }
  await scene(
    "খালি পর্দায় সাজ থাকে না",
    <M.SlidePreview slide={{ kind: "blank", heading: "", arabic: "", text: "" }} />,
    { expect: ["এখনো খালি"] },
  );
  await scene(
    "অচেনা ধরনেও ভাঙে না",
    <M.SlidePreview slide={{ kind: "zzz", heading: "ক", arabic: "", text: "" }} />,
    { expect: ["ক"] },
  );

  /* ───── সংরক্ষণ সত্যিই টেকে কিনা ───── */
  await scene(
    "ধাপে লিখে সংরক্ষণ করলে লেখা টেকে",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    {
      steps: [
        ["click", "খুলুন"],
        ["type", "Say line 0", "আমার নতুন লেখা"],
        ["click", "💾 সংরক্ষণ করুন"],
      ],
      expect: ["আমার নতুন লেখা", "✓ সংরক্ষিত"],
      notExpect: ["অসংরক্ষিত"],
    },
  );
  await scene(
    "দারসের শিরোনাম বদলে সংরক্ষণ করলে টেকে",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    {
      steps: [
        ["type", "Surah Al-Ikhlas", "নতুন শিরোনাম"],
        ["click", "💾 সংরক্ষণ করুন"],
      ],
      expect: ["নতুন শিরোনাম"],
      notExpect: ["অসংরক্ষিত"],
    },
  );

  await scene(
    "⚠️ এক ধাপ সংরক্ষণ করলে অন্য ধাপের অসংরক্ষিত লেখা মুছে যায় কিনা",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    {
      steps: [
        // দুটি ধাপ খুলে দুটোতেই লিখি
        ["click", "খুলুন"],
        ["type", "Say line 0", "প্রথম ধাপের লেখা"],
        ["click", "খুলুন"],
        ["type", "Say line 1", "দ্বিতীয় ধাপের লেখা"],
        // এখন কেবল দ্বিতীয়টি সংরক্ষণ করি
        ["click", "💾 সংরক্ষণ করুন"],
      ],
      // ⚠️ প্রথম ধাপের লেখাটি পর্দাতেই থাকা চাই
      expect: ["প্রথম ধাপের লেখা", "দ্বিতীয় ধাপের লেখা"],
    },
  );

  /* ───── ⚠️ সার্ভার যদি না রাখে — লেখা যেন না হারায় ───── */
  await scene(
    "সার্ভার না রাখলে ধাপের লেখা পর্দাতেই থাকে",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    {
      steps: [
        ["click", "খুলুন"],
        ["type", "Say line 0", "আমার নতুন লেখা"],
        ["click", "💾 সংরক্ষণ করুন"],
      ],
      // লেখাটি রয়ে গেছে, আর "সংরক্ষিত" বলে ভুল আশ্বাস দেওয়া হয়নি
      // "অসংরক্ষিত" থেকে যাওয়াই প্রমাণ — ভুল আশ্বাস দেওয়া হয়নি
      expect: ["আমার নতুন লেখা", "অসংরক্ষিত"],
      mode: "forget",
    },
  );
  await scene(
    "সার্ভার না রাখলে শিরোনামও পর্দাতেই থাকে",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    {
      steps: [
        ["type", "Surah Al-Ikhlas", "নতুন শিরোনাম"],
        ["click", "💾 সংরক্ষণ করুন"],
      ],
      expect: ["নতুন শিরোনাম"],
      mode: "forget",
    },
  );

  /* ───── ধাপ ৪ — স্ক্রিপ্ট থেকে টগলের লেখা ───── */
  await scene(
    "টপিকযুক্ত স্ক্রিপ্টে সারাংশের বোতাম আসে",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    {
      expect: ["📋 লেকচার প্ল্যানে সারাংশ বসান",
               "শিক্ষার্থী পরে দেখে রিভিশন দিতে পারবেন",
               "নিজের মতো বদলে নিতে পারবেন"],
    },
  );
  await scene(
    "সারাংশ বসানো — নিশ্চিত করে",
    <M.LessonEditor id={1} canEdit onClose={nop} onChanged={nop} />,
    { click: ["📋 লেকচার প্ল্যানে সারাংশ বসান"] },
  );
  await scene(
    "কেবল দেখা-মাত্র হলে বোতামটি নেই",
    <M.LessonEditor id={1} canEdit={false} onClose={nop} />,
    { notExpect: ["📋 লেকচার প্ল্যানে সারাংশ বসান"] },
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
  /* ───── পুরনো লেখা মুছে নতুন নমুনা বসানো ─────
     ⚠️ ধ্বংসাত্মক কাজ — তাই বোতামটি কেবল পরিচালকের কাছেই, আর চাপলেই
     সরাসরি না মুছে আগে নিশ্চিত করতে চায়। */
  await scene(
    "পরিচালক নতুন নমুনা বসানোর বোতাম পান",
    <M.LessonsView user={director} courses={courses} />,
    { expect: ["♻️ নতুন নমুনা"] },
  );
  await scene(
    "উস্তাদের কাছে নতুন নমুনার বোতাম নেই",
    <M.LessonsView user={teacher} courses={courses} />,
    { notExpect: ["♻️ নতুন নমুনা"] },
  );
  /* এখানে confirmHandler বসানো নেই, তাই askConfirm সরাসরি কাজটাই চালায়
     (অ্যাপের নিজেরই ফলব্যাক) — ফলে পুরো পথটা এক ক্লিকেই যাচাই হয়ে যায়:
     নমুনা বসে, তালিকা নতুন করে আসে, আর স্ক্রিপ্টটি খুলে যায়। */
  await scene(
    "নতুন নমুনা বসিয়ে স্ক্রিপ্টটি খোলে",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["♻️ নতুন নমুনা"], expect: ["← দারসের তালিকা", "+ নতুন ধাপ"] },
  );

  /* ───── 🔝 সবার উপরে ভাসমান পর্দা ─────
     ⚠️ এটি উস্তাদের উইন্ডোর ভেতরেই আঁকা হয়, তাই "শুধু স্লাইডের ঘর যাবে"
     দেয়ালটা এখানে কোডেই — onlySlide()। সেটি ফুটো হলে বাচ্চার পর্দায়
     উস্তাদের স্ক্রিপ্ট ভেসে উঠত, তাই সবচেয়ে কড়া পরীক্ষাটি এখানে। */
  check("ভাসমান পর্দায় উস্তাদের স্ক্রিপ্ট যেতে পারে না", () => {
    const dirty = {
      kind: "verse",
      heading: "Say it with me",
      arabic: "قُلْ",
      text: "🎤",
      // ⚠️ নিচেরগুলো কখনো যেতে পারবে না
      teacher_says: "Listen carefully",
      correction: "Almost! Try again",
      note: "মাখরাজ: গলার গভীর থেকে",
      expected: "قُلْ",
      student_does: "বলে",
    };
    const out = M.onlySlide(dirty);
    eq(Object.keys(out).sort(), ["arabic", "heading", "kind", "text"],
       "অনুমোদিত ঘরের বাইরে কিছু গেছে");
    for (const bad of ["teacher_says", "correction", "note", "expected",
                       "student_does"]) {
      if (bad in out) throw new Error(`“${bad}” ঘরটি পার হয়ে গেছে`);
    }
  });
  check("স্লাইড না থাকলে ভাসমান পর্দা খালি", () => {
    eq(M.onlySlide(null), null, "null-এর বদলে অন্য কিছু");
    eq(M.onlySlide(undefined), null, "undefined-এর বদলে অন্য কিছু");
  });
  check("খালি ঘর বাদ যায়, শূন্য নয়", () => {
    eq(M.onlySlide({ kind: "title", heading: "", arabic: null, text: "হ্যাঁ" }),
       { kind: "title", heading: "", text: "হ্যাঁ" },
       "null বাদ পড়েনি বা খালি লেখা হারিয়েছে");
  });
  check("এই ব্রাউজারে ভাসমান পর্দা নেই — তা বোঝা যায়", () => {
    if (M.pipReady() !== false)
      throw new Error("jsdom-এ তো documentPictureInPicture নেই");
  });
  await scene(
    "ভাসমান পর্দা স্লাইডটাই আঁকে",
    <M.FloatBody slide={{ kind: "verse", heading: "Say it with me",
                          arabic: "قُلْ", text: "🎤" }} />,
    { expect: ["Say it with me", "قُلْ"] },
  );
  await scene(
    "স্লাইড ছাড়াও ভাসমান পর্দা ভাঙে না",
    <M.FloatBody slide={null} />,
    { expect: [] },
  );
  await scene(
    "শিক্ষক মোডে ভাসমান পর্দার বোতাম আছে",
    <M.TeacherMode id={1} onClose={nop} />,
    { expect: ["🔝 ভাসমান পর্দা"] },
  );
  /* ⚠️ jsdom-এ ভাসমান উইন্ডো নেই — চাপলে যেন ভেঙে না পড়ে, বরং
     উস্তাদকে পরিষ্কার করে বলে দেয় */
  await scene(
    "ভাসমান পর্দা না থাকলেও চাপলে ভাঙে না",
    <M.TeacherMode id={1} onClose={nop} />,
    { click: ["🔝 ভাসমান পর্দা"], expect: ["🔝 ভাসমান পর্দা"] },
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
