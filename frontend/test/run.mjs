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

const mod = await import("./.out/lesson-ui.js");
process.exit((await mod.run()) ? 1 : 0);
