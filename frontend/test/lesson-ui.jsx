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

/* উপস্থাপনা উইন্ডো থেকে আসা বার্তার নকল — দুই উইন্ডোর সেতুটি
   localStorage-ও ব্যবহার করে, তাই এখানেই সেটাকে ধরা যায় */
const stageFire = (msg) => {
  const v = JSON.stringify({ ...msg, at: Date.now() });
  try {
    window.localStorage.setItem("tqa_stage_msg", v);
  } catch (e) {
    /* jsdom-এ না থাকলেও ইভেন্টটাই আসল */
  }
  window.dispatchEvent(
    new window.StorageEvent("storage", {
      key: "tqa_stage_msg",
      newValue: v,
    }),
  );
};
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
  { expect = [], notExpect = [], click = [], steps = [], mode, after } = {},
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
    // বাইরের কোনো ঘটনা (যেমন অন্য উইন্ডো থেকে আসা বার্তা)
    if (after) {
      await act(async () => {
        await after(host);
      });
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

  /* ───── ⚠️ পর্দা ঢাকা পড়েছে — উস্তাদকে জানানো ─────
     জুমে শিক্ষার্থী তখন পুরনো স্লাইডেই আটকে থাকেন, অথচ উস্তাদ পড়িয়েই
     যান। এই সতর্কবার্তাটাই একমাত্র উপায় যাতে তিনি টের পান। */
  /* ───── ↤ লেখার দিক বদলানোর টুল ─────
     ⚠️ আরবি বাঁ-থেকে-ডান অনুচ্ছেদে বসলে শব্দগুলো উল্টো ক্রমে সাজে —
     শেষ শব্দটাই আগে পড়া হয়। পরিচালক যেন নিজেই ঠিক করতে পারেন। */
  await scene(
    "সম্পাদকে দিক বদলানোর বোতাম আছে",
    <M.RichText value="<p>قُلْ هُوَ ٱللَّهُ</p>" onChange={nop} />,
    { expect: ["↤ ডান→বাঁ", "বাঁ→ডান ↦"] },
  );
  {
    ran++;
    const host = document.createElement("div");
    document.body.appendChild(host);
    const root = createRoot(host);
    let html = "<p>قُلْ هُوَ ٱللَّهُ</p>";
    await act(async () => {
      root.render(<M.RichText value={html} onChange={(v) => (html = v)} />);
    });
    for (let k = 0; k < 4; k++) await act(async () => { await sleep(0); });
    const btn = [...host.querySelectorAll("button")].find(
      (b) => (b.textContent || "").includes("ডান→বাঁ"));
    if (!btn) failures.push("দিক বদলানোর বোতামটি পাওয়া গেল না");
    else {
      await act(async () => { btn.click(); });
      const why = [];
      if (!/dir="rtl"/.test(html)) why.push("dir বসেনি");
      if (!/direction:\s*rtl/.test(html)) why.push("direction বসেনি");
      if (!/قُلْ/.test(html)) why.push("লেখাটাই হারিয়েছে");
      if (why.length)
        failures.push("দিক বদলালে লেখায় বসে → " + why.join(" · ") +
                      " · পেলাম: " + html.slice(0, 90));
      // এবার উল্টোটা
      const back = [...host.querySelectorAll("button")].find(
        (b) => (b.textContent || "").includes("বাঁ→ডান"));
      await act(async () => { back.click(); });
      if (!/dir="ltr"/.test(html))
        failures.push("বাঁ→ডান চাপলে ফিরে আসে না · পেলাম: " +
                      html.slice(0, 90));
    }
    await act(async () => root.unmount());
    host.remove();
  }

  const WARN = "জুমে স্ক্রিন ঢাকা পড়েছে";
  await scene(
    "স্বাভাবিক অবস্থায় সতর্কবার্তা নেই",
    <M.TeacherMode id={1} onClose={nop} />,
    { notExpect: [WARN] },
  );
  await scene(
    "পর্দা ঢাকা পড়লে উস্তাদ সতর্কবার্তা দেখেন",
    <M.TeacherMode id={1} onClose={nop} />,
    {
      after: () => stageFire({ t: "vis", hidden: true }),
      expect: [WARN, "স্টুডেন্ট দেখতে পাচ্ছে না", "🔝 ভাসমান পর্দা খুলুন"],
    },
  );
  await scene(
    "আবার দেখা গেলে সতর্কবার্তা চলে যায়",
    <M.TeacherMode id={1} onClose={nop} />,
    {
      after: async () => {
        stageFire({ t: "vis", hidden: true });
        await sleep(2);
        stageFire({ t: "vis", hidden: false });
      },
      notExpect: [WARN],
    },
  );
  /* ⚠️ বন্ধ করা আর ঢাকা পড়া এক নয় — বন্ধ উইন্ডো নিয়ে
     "স্টুডেন্ট দেখতে পাচ্ছে না" বলা ভুল হতো */
  await scene(
    "উইন্ডো বন্ধ হলে সতর্কবার্তা নয়",
    <M.TeacherMode id={1} onClose={nop} />,
    {
      after: async () => {
        stageFire({ t: "vis", hidden: true });
        await sleep(2);
        stageFire({ t: "gone" });
      },
      notExpect: [WARN],
    },
  );
  /* হৃৎস্পন্দনেও খবরটা থাকে — ইভেন্ট কোনো কারণে হারালেও ধরা পড়ে */
  await scene(
    "হৃৎস্পন্দনেও ঢাকা পড়ার খবর আসে",
    <M.TeacherMode id={1} onClose={nop} />,
    {
      after: () => stageFire({ t: "here", hidden: true }),
      expect: [WARN],
    },
  );

  /* ───── লগইন আটকালে আসল কারণটা বলা ─────
     ⚠️ আগে সব সমস্যাতেই এক কথা দেখাত, তাই পরিচালক কখনো বুঝতেন না
     দোষটা ইন্টারনেটের, নাকি সার্ভারের। প্রতিটি অবস্থার আলাদা বার্তা
     আছে কিনা — আর দুটো অবস্থা যেন এক বার্তা না দেয় — তা এখানে দেখা হয়। */
  const bnOnly = (b) => b; // পরিচালক/উস্তাদ বাংলাই দেখেন
  const say = (e) => M.loginErrorText(e, bnOnly);
  const CASES = [
    [{ status: 401 }, "ভুল আইডি বা পাসওয়ার্ড", "ভুল পাসওয়ার্ড"],
    [{ status: 429 }, "১ মিনিট অপেক্ষা", "বারবার চেষ্টা"],
    [{ status: 503 }, "সার্ভার এখন চালু হচ্ছে", "সার্ভার রিস্টার্ট"],
    [{ status: 502 }, "সার্ভার এখন চালু হচ্ছে", "গেটওয়ে"],
    [{ status: 500 }, "সার্ভারে সমস্যা", "সার্ভারের ভেতরের ত্রুটি"],
    [{ status: 403 }, "অনুমতি নেই", "নিষিদ্ধ অ্যাকাউন্ট"],
    [{ name: "AbortError", message: "aborted" }, "সময়মতো সাড়া", "টাইমআউট"],
    [{ message: "Failed to fetch" }, "পৌঁছানো যাচ্ছে না", "নেটওয়ার্ক"],
  ];
  for (const [err, want, why] of CASES) {
    check(`লগইন ত্রুটি — ${why}`, () => {
      const got = say(err);
      if (!got.includes(want))
        throw new Error(`“${want}” নেই · পেলাম “${got}”`);
    });
  }
  check("প্রতিটি অবস্থার বার্তা আলাদা", () => {
    const seen = new Map();
    for (const [err, , why] of CASES) {
      const got = say(err);
      // ৫০২ ও ৫০৩ ইচ্ছা করেই একই — দুটোই "সার্ভার চালু হচ্ছে"
      if (why === "গেটওয়ে") continue;
      if (seen.has(got))
        throw new Error(`“${why}” আর “${seen.get(got)}” একই কথা বলে`);
      seen.set(got, why);
    }
  });
  check("অচেনা কোড হলে নম্বরটা দেখায়", () => {
    const got = say({ status: 418, message: "I am a teapot" });
    if (!got.includes("418"))
      throw new Error(`নম্বর ছাড়া খোঁজার সূত্র থাকে না · পেলাম “${got}”`);
  });
  check("পুরনো ধাঁচের 401 বার্তাও ধরা পড়ে", () => {
    // status না থাকলেও বার্তায় 401 থাকলে সেটা ভুল পাসওয়ার্ডই
    const got = say({ message: "Request failed with 401" });
    if (!got.includes("ভুল আইডি"))
      throw new Error(`পেলাম “${got}”`);
  });
  check("ত্রুটি না থাকলেও ভাঙে না", () => {
    for (const e of [null, undefined, {}]) {
      const got = say(e);
      if (!got || typeof got !== "string" || !got.length)
        throw new Error("খালি বার্তা");
    }
  });

  /* ───── 📐 যেকোনো মাপে স্লাইড পুরোটা বসা ─────
     ভাসমান পর্দা ছোট-বড় করলেও আয়াত যেন কাটা না পড়ে। ⚠️ সবচেয়ে জরুরি:
     এতে যেন উপস্থাপনা পপআপ বা শিক্ষার্থীর পোর্টালের চেহারা না বদলায় —
     সেখানে পুরনো পর্দা-নির্ভর মাপই (clamp) থাকা চাই। */
  const SL = { kind: "verse", heading: "Say it with me", arabic: "قُلْ",
               text: "🎤" };
  await scene(
    "ভাসমান পর্দায় স্লাইড পুরোটা থাকে",
    <M.FloatBody slide={SL} />,
    { expect: ["Say it with me", "قُلْ", "🎤"] },
  );
  await scene(
    "লেখা অনেক বেশি হলেও ভাঙে না",
    <M.FloatBody slide={{ kind: "verse", heading: "ক".repeat(200),
                          arabic: "قُلْ ".repeat(60),
                          text: "খ".repeat(400) }} />,
    { expect: ["قُلْ"] },
  );
  await scene(
    "স্লাইড ছাড়াও ভাসমান পর্দা দাঁড়িয়ে থাকে",
    <M.FloatBody slide={null} />,
    { expect: [] },
  );
  await scene(
    "খালি বাক্সেও FitBox ভাঙে না",
    <M.FitBox>{null}</M.FitBox>,
    { expect: [] },
  );
  /* ⚠️ এটাই আসল পরীক্ষা — সত্যিকারের পর্দার মাপ ধরে হিসাব মেলানো।
     স্লাইড ১২৮০×৭২০; "ফিট" মানে ছোট করার পর দুই দিকেই ভেতরে থাকা। */
  const W = 1280, H = 720;
  const fits = (ow, oh, iw = W, ih = H) => {
    const s = M.fitScale(ow, oh, iw, ih);
    return s > 0 && iw * s <= ow + 0.5 && ih * s <= oh + 0.5;
  };
  const SCREENS = [
    ["ছোট ভাসমান পর্দা", 380, 220],
    ["মাঝারি ভাসমান পর্দা", 960, 540],
    ["ল্যাপটপ পুরো পর্দা", 1366, 768],
    ["বড় মনিটর", 1920, 1080],
    ["ফোন খাড়া", 390, 844],
    ["ফোন শোয়ানো", 844, 390],
    ["ট্যাব", 1024, 768],
    ["খুবই সরু", 240, 700],
    ["খুবই চ্যাপ্টা", 1600, 180],
  ];
  for (const [name, w, h] of SCREENS) {
    check(`স্লাইড পুরোটা বসে — ${name} (${w}×${h})`, () => {
      if (!fits(w, h))
        throw new Error(`কাটা পড়ছে · scale=${M.fitScale(w, h, W, H)}`);
    });
  }
  check("লেখা অনেক বেশি হলে আরও ছোট হয়", () => {
    const normal = M.fitScale(960, 540, W, H);
    const tall = M.fitScale(960, 540, W, H * 3); // তিনগুণ লম্বা স্লাইড
    if (!(tall < normal))
      throw new Error("লম্বা স্লাইডেও একই মাপ — নিচের অংশ কাটা পড়বে");
    if (!fits(960, 540, W, H * 3))
      throw new Error("লম্বা স্লাইড বসছে না");
  });
  check("পর্দা বড় হলে স্লাইডও বড় হয়", () => {
    const small = M.fitScale(640, 360, W, H);
    const big = M.fitScale(1920, 1080, W, H);
    if (!(big > small)) throw new Error("বড় পর্দাতেও ছোটই রয়ে গেল");
  });
  check("অনুপাত কখনো বদলায় না", () => {
    // এক সংখ্যা দিয়ে দুই দিকই ছোট-বড় হয়, তাই আকৃতি অটুট
    for (const [, w, h] of SCREENS) {
      const s = M.fitScale(w, h, W, H);
      if (!(s > 0) || !isFinite(s)) throw new Error(`অদ্ভুত মান ${s}`);
    }
  });
  check("মাপ জানা না থাকলে ০ — স্লাইড মিলিয়ে যাবে না", () => {
    for (const a of [[0, 500, W, H], [500, 0, W, H], [500, 500, 0, H],
                     [500, 500, W, 0], [NaN, 500, W, H]]) {
      if (M.fitScale(...a) !== 0)
        throw new Error(`${JSON.stringify(a)} → ০ নয়`);
    }
  });
  check("সীমার বাইরে যায় না", () => {
    const huge = M.fitScale(99999, 99999, W, H);
    const tiny = M.fitScale(1, 1, W, H);
    if (huge > 4) throw new Error("অতিরিক্ত বড় — ঝাপসা হবে");
    if (tiny < 0.05) throw new Error("অতিরিক্ত ছোট — কিছুই দেখা যাবে না");
  });
  /* ⚠️ সবচেয়ে জরুরি পরীক্ষা — অঙ্ক ঠিক থাকলেই হয় না, পর্দায় সত্যিই
     বসছে কিনা দেখতে হয়। run.mjs-এ মাপের নকল বসানো আছে বলে এটা এখন
     করা যায়। ভাসমান পর্দা "রেসপনসিভ হয়নি" — সেই অভিযোগটাই এখানে ধরা। */
  const scaleIn = async (w, h) => {
    const host = document.createElement("div");
    host.style.setProperty("--w", `${w}px`);
    host.style.setProperty("--h", `${h}px`);
    document.body.appendChild(host);
    const root = createRoot(host);
    await act(async () => {
      root.render(<M.FloatBody slide={SL} />);
    });
    for (let k = 0; k < 6; k++) await act(async () => { await sleep(0); });
    // ভেতরের যে বাক্সটি ছোট-বড় হয়
    const box = [...host.querySelectorAll("div")].find((d) =>
      (d.style.transform || "").includes("scale("));
    const got = box ? parseFloat(box.style.transform.match(/scale\(([^)]+)\)/)[1]) : null;
    await act(async () => root.unmount());
    host.remove();
    return got;
  };

  /* ⚠️ আসল বাগটা এখানে — ভাসমান উইন্ডো খোলার মুহূর্তে তার মাপ জানা
     যায় না (০ আসে)। মাপটা আসে একটু পরে। উস্তাদ যদি উইন্ডোটা হাতে না
     নাড়ান, ResizeObserver-ও আর ডাকে না — ফলে স্লাইড বড়ই থেকে যেত,
     কাটা পড়ত। "রেসপনসিভ হয়নি" বলতে ঠিক এটাই।

     এখানে সেই অবস্থাই বানানো: প্রথমে মাপ ০, বসার পরে আসল মাপ, আর
     ResizeObserver পুরো সময় নীরব। */
  const scaleAfterLateSize = async (w, h) => {
    const host = document.createElement("div");
    document.body.appendChild(host);
    const root = createRoot(host);
    await act(async () => {
      root.render(<M.FloatBody slide={SL} />);
    });
    // এখন মাপটা এলো — উইন্ডো নিজের আকার পেয়েছে
    host.style.setProperty("--w", `${w}px`);
    host.style.setProperty("--h", `${h}px`);
    // কিন্তু কেউ উইন্ডো নাড়াচ্ছে না — observer নীরব
    for (let k = 0; k < 12; k++) await act(async () => { await sleep(60); });
    const box = [...host.querySelectorAll("div")].find((d) =>
      (d.style.transform || "").includes("scale("));
    const got = box
      ? parseFloat(box.style.transform.match(/scale\(([^)]+)\)/)[1])
      : null;
    await act(async () => root.unmount());
    host.remove();
    return got;
  };

  {
    ran++;
    const s3 = await scaleAfterLateSize(380, 220);
    const want = M.fitScale(380, 220, M.FIT_W, M.FIT_H);
    if (s3 === null || Math.abs(s3 - want) > 0.001)
      failures.push(
        `মাপ দেরিতে এলেও স্লাইড বসে → scale=${s3}, হওয়ার কথা ` +
          `${want.toFixed(3)} · উইন্ডো না নাড়ালে স্লাইড কাটা পড়বে`,
      );
  }

  /* ⚠️ শুধু "কতটা ছোট হলো" জানলেই হয় না — "কোথায় বসল" সেটাও দেখতে হয়।
     আগের বাগটা ঠিক এখানেই ছিল: স্লাইড ছোট হচ্ছিল, কিন্তু গ্রিডের ঘর
     ১২৮০px হয়ে যাওয়ায় কেন্দ্র সরে গিয়ে স্লাইডটা পর্দার বাইরে চলে যেত
     আর কাটা পড়ত। তাই এখানে জ্যামিতিটাই মেলানো হয়। */
  const boxOf = async (w, h) => {
    const host = document.createElement("div");
    host.style.setProperty("--w", `${w}px`);
    host.style.setProperty("--h", `${h}px`);
    document.body.appendChild(host);
    const root = createRoot(host);
    await act(async () => {
      root.render(<M.FloatBody slide={SL} />);
    });
    for (let k = 0; k < 8; k++) await act(async () => { await sleep(10); });
    const el = [...host.querySelectorAll("div")].find((d) =>
      (d.style.transform || "").includes("scale("));
    const out = el
      ? { style: el.style, tf: el.style.transform,
          pos: el.style.position, top: el.style.top, left: el.style.left,
          s: parseFloat(el.style.transform.match(/scale\(([^)]+)\)/)[1]) }
      : null;
    await act(async () => root.unmount());
    host.remove();
    return out;
  };

  {
    ran++;
    const b = await boxOf(380, 220);
    const why = [];
    if (!b) why.push("ছোট-বড় হওয়ার বাক্সটাই নেই");
    else {
      if (b.pos !== "absolute")
        why.push(`গ্রিডের ঘরে বসে আছে (position=${b.pos}) — কেন্দ্র সরে যাবে`);
      if (b.top !== "50%" || b.left !== "50%")
        why.push(`কেন্দ্রে পিন করা নেই (top=${b.top} left=${b.left})`);
      if (!b.tf.includes("translate(-50%, -50%)"))
        why.push(`নিজের অর্ধেক পিছিয়ে আনা হয়নি: ${b.tf}`);
      // জ্যামিতি: কেন্দ্র পর্দার কেন্দ্রে, আর ছোট করার পর দুই দিকেই ভেতরে
      const halfW = (M.FIT_W * b.s) / 2;
      const halfH = (M.FIT_H * b.s) / 2;
      if (halfW > 380 / 2 + 0.5) why.push(`চওড়ায় বাইরে চলে যাচ্ছে`);
      if (halfH > 220 / 2 + 0.5) why.push(`উচ্চতায় বাইরে চলে যাচ্ছে`);
    }
    if (why.length)
      failures.push("ছোট পর্দায় স্লাইড ভেতরে বসে → " + why.join(" · "));
  }

  for (const [name, w, h] of [["মাঝারি", 960, 540], ["বড়", 1920, 1080],
                              ["ফোন শোয়ানো", 844, 390]]) {
    ran++;
    const b = await boxOf(w, h);
    const ok = b && b.pos === "absolute" &&
      (M.FIT_W * b.s) / 2 <= w / 2 + 0.5 && (M.FIT_H * b.s) / 2 <= h / 2 + 0.5;
    if (!ok)
      failures.push(`স্লাইড ভেতরে বসে — ${name} (${w}×${h}) → ` +
        (b ? `scale=${b.s} pos=${b.pos}` : "বাক্সই নেই"));
  }

  check("(প্রস্তুতি) মাপের নকল কাজ করছে", () => {
    const d = document.createElement("div");
    d.style.setProperty("--w", "800px");
    document.body.appendChild(d);
    const kid = document.createElement("div");
    d.appendChild(kid);
    if (kid.clientWidth !== 800) throw new Error("নকল মাপ কাজ করছে না");
    d.remove();
  });

  for (const [name, w, h, want] of [
    ["ছোট ভাসমান পর্দা", 380, 220, "ছোট"],
    ["মাঝারি", 960, 540, "ছোট"],
    ["বড় মনিটর", 1920, 1080, "বড়"],
  ]) {
    ran++;
    const s2 = await scaleIn(w, h);
    const ok =
      s2 !== null &&
      (want === "ছোট" ? s2 < 0.99 : s2 > 1.01) &&
      Math.abs(s2 - M.fitScale(w, h, M.FIT_W, M.FIT_H)) < 0.001;
    if (!ok)
      failures.push(
        `ভাসমান পর্দা সত্যিই বসে — ${name} (${w}×${h}) → scale=${s2}, ` +
          `হওয়ার কথা ${M.fitScale(w, h, M.FIT_W, M.FIT_H).toFixed(3)}`,
      );
  }

  check("নকশার মাপ ১৬:৯ — টিভি/প্রজেক্টরের অনুপাত", () => {
    const r = M.FIT_W / M.FIT_H;
    if (Math.abs(r - 16 / 9) > 0.01)
      throw new Error(`অনুপাত ${r.toFixed(3)}, ১৬:৯ নয়`);
  });
  /* ⚠️ পাহারা — fixed ছাড়া StageSlide-এর মাপ আগের মতোই পর্দা-নির্ভর
     থাকা চাই, নইলে উপস্থাপনা পপআপের চেহারা বদলে যেত */
  await scene(
    "উপস্থাপনার পর্দায় আগের মাপই (clamp)",
    <M.StageSlide slide={SL} />,
    { expect: ["Say it with me"] },
  );
  check("fixed ছাড়া পুরনো clamp, fixed দিলে স্থির পিক্সেল", () => {
    const el = (fixed) =>
      JSON.stringify(M.StageSlide({ slide: SL, fixed }), (k, v) =>
        typeof v === "function" ? "fn" : v);
    const loose = el(false);
    const tight = el(true);
    if (!loose.includes("clamp("))
      throw new Error("fixed ছাড়াও clamp হারিয়েছে — পুরনো পর্দা বদলে যাবে");
    if (tight.includes("clamp("))
      throw new Error("fixed দিলেও clamp রয়ে গেছে — বাক্সে ফিট হবে না");
  });

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
  /* ───── স্ক্রিপ্ট তৈরি ─────
     ⚠️ "নমুনা" ব্যবস্থাটি তুলে দেওয়া হয়েছে — দারসগুলো এখন সরাসরি আসল
     দারস। টপিকে চাপলে বিকল্প বাছার মডাল আর আসে না, খালি স্ক্রিপ্ট
     তৈরি হয়ে সরাসরি খুলে যায়। */
  await scene(
    "নমুনার বিকল্প আর দেখায় না",
    <M.LessonsView user={director} courses={courses} />,
    { notExpect: ["নমুনা", "খালি থেকে শুরু", "কীভাবে শুরু করবেন"] },
  );
  await scene(
    "স্ক্রিপ্ট লেখার বোতামটি আছে",
    <M.LessonsView user={director} courses={courses} />,
    { expect: ["✍️ স্ক্রিপ্ট লিখুন"] },
  );
  await scene(
    "চাপলে খালি স্ক্রিপ্ট তৈরি হয়ে খোলে",
    <M.LessonsView user={director} courses={courses} />,
    { click: ["✍️ স্ক্রিপ্ট লিখুন"],
      expect: ["← দারসের তালিকা", "+ নতুন ধাপ"] },
  );
  await scene(
    "তালিকায় নতুন নমুনার বোতাম নেই",
    <M.LessonsView user={director} courses={courses} />,
    { notExpect: ["♻️ নতুন নমুনা"] },
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
