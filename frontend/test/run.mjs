/* jsdom দিয়ে ব্রাউজারের পরিবেশ বানিয়ে দারস-ব্যবস্থার পরীক্ষাটি চালায়।

   ⚠️ jsdom কেবল devDependency — চালু সাইটের বিল্ডে এর কিছুই যায় না।
   চালাতে:  npm run test:ui                                             */
import { JSDOM } from "jsdom";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "https://app.tarbiyatulquran.org/",
  pretendToBeVisual: true,
});
const w = dom.window;

const COPY = [
  "window", "document", "navigator", "HTMLElement", "Element", "Node",
  "Event", "CustomEvent", "MouseEvent", "KeyboardEvent", "getComputedStyle",
  "requestAnimationFrame", "cancelAnimationFrame", "localStorage",
  "sessionStorage", "location", "history", "MutationObserver", "Image",
  "DOMParser", "URLSearchParams",
];
for (const k of COPY) {
  try {
    if (w[k] !== undefined) globalThis[k] = w[k];
  } catch {
    /* কিছু নাম বদলানো যায় না — উপেক্ষা */
  }
}

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => [] });

/* jsdom-এ যেগুলো নেই */
globalThis.BroadcastChannel = class {
  postMessage() {}
  addEventListener() {}
  removeEventListener() {}
  close() {}
};
w.BroadcastChannel = globalThis.BroadcastChannel;
w.open = () => ({
  closed: false,
  focus() {},
  document: { write() {}, close() {}, open() {} },
});
w.alert = () => {};
w.scrollTo = () => {};

/* ───── মাপের নকল ─────
   jsdom কিছুই আঁকে না, তাই সব উপাদানের মাপ ০ — ফলে "পর্দার মাপে স্লাইড
   বসছে কিনা" সেটাই পরীক্ষা করা যেত না, আর ভাসমান পর্দার বাগটাও ধরা
   পড়ত না। এখানে মাপগুলো নকল করে দিই:
     • style-এ px দেওয়া থাকলে সেটাই মাপ (যেমন ভেতরের ১২৮০×৭২০)
     • নইলে নিকটতম পূর্বপুরুষের --w / --h (পরীক্ষার "পর্দা")            */
const num = (v) => parseFloat(v) || 0;
const sizeOf = (el, own, fallbackVar) => {
  const mine = el.style?.getPropertyValue?.(own);
  if (mine && mine.endsWith("px")) return num(mine);
  let p = el;
  while (p) {
    const got = p.style?.getPropertyValue?.(fallbackVar);
    if (got) return num(got);
    p = p.parentElement;
  }
  return 0;
};
for (const [prop, own, cssVar] of [
  ["clientWidth", "width", "--w"],
  ["offsetWidth", "width", "--w"],
  ["clientHeight", "height", "--h"],
  ["offsetHeight", "min-height", "--h"],
]) {
  Object.defineProperty(w.HTMLElement.prototype, prop, {
    configurable: true,
    get() {
      return sizeOf(this, own, cssVar);
    },
  });
}

/* ResizeObserver — jsdom-এ নেই। observe() ডাকলেই একবার মেপে দেয়,
   ব্রাউজারও ঠিক তাই করে। */
w.ResizeObserver = class {
  constructor(cb) {
    this.cb = cb;
  }
  observe() {
    // ⚠️ TQA_NO_RO=1 দিলে observer চুপ করে থাকে — ঠিক যেমনটা আসল
    // ভাসমান উইন্ডোতে হতো: খোলার মুহূর্তে মাপ জানা যায় না, আর উস্তাদ
    // উইন্ডো না নাড়ালে observer আর কখনো ডাকে না। এই অবস্থাতেও স্লাইড
    // ঠিক মাপে বসছে কিনা — সেটাই পরীক্ষার আসল কাজ।
    if (process.env.TQA_NO_RO === "1") return;
    this.cb([], this);
  }
  unobserve() {}
  disconnect() {}
};
globalThis.ResizeObserver = w.ResizeObserver;

const mod = await import("./.out/lesson-ui.js");
process.exit((await mod.run()) ? 1 : 0);
