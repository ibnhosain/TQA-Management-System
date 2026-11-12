/* নামাজ শিক্ষা — ৩৬০° ছবি: একটি ধাপের ২৪টি দিক (একটি ছবিতে ৬ × ৪)। টেনে বা আঙুলে ঘোরানো যায়, নিজে ঘোরে, থামানো যায়।
   ছবি আসে সার্ভার থেকে টোকেন দিয়ে (খোলা লিংক নেই)। দিক: ফ্রেম ৩ = সামনে, ৯ = বাম পাশ, ১৫ = পেছন, ২১ = ডান পাশ। */
import { useEffect, useRef, useState } from "react";
import { fetchBinary } from "../api";

const N = 24, COLS = 6, FW = 400, FH = 467;
export const FRAME_OF = { front: 3, side: 21, back: 15 };
const cache = {};

export default function Turn360({ stepKey, playing, view, onStatus }) {
  const cv = useRef(null);
  const img = useRef(null);
  const frame = useRef(FRAME_OF.front);
  const drag = useRef(null);
  const [ready, setReady] = useState(false);

  const draw = () => {
    const c = cv.current, im = img.current;
    if (!c || !im) return;
    const f = ((Math.round(frame.current) % N) + N) % N;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#FBF8F1"; ctx.fillRect(0, 0, c.width, c.height);
    const s = Math.min(c.width / FW, c.height / FH), w = FW * s, h = FH * s;
    ctx.drawImage(im, (f % COLS) * FW, Math.floor(f / COLS) * FH, FW, FH, (c.width - w) / 2, (c.height - h) / 2, w, h);
  };

  useEffect(() => {
    let alive = true;
    setReady(false); onStatus?.("Loading…");
    (async () => {
      try {
        if (!cache[stepKey]) cache[stepKey] = fetchBinary(`/salah3d/turn/${stepKey}/`).then((b) => URL.createObjectURL(new Blob([b], { type: "image/jpeg" })));
        const url = await cache[stepKey];
        const im = new Image();
        im.onload = () => { if (!alive) return; img.current = im; setReady(true); onStatus?.(""); draw(); };
        im.src = url;
      } catch (e) {
        if (alive) onStatus?.("Could not load the pictures — please check the internet. (" + e.message + ")");
      }
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepKey]);

  useEffect(() => { if (view) { frame.current = FRAME_OF[view.dir]; draw(); } }, [view]);

  useEffect(() => {
    if (!playing || !ready) return;
    const t = setInterval(() => { if (!drag.current) { frame.current += 1; draw(); } }, 140);
    return () => clearInterval(t);
  }, [playing, ready]);

  useEffect(() => {
    const c = cv.current;
    const fit = () => { const r = c.getBoundingClientRect(); c.width = r.width * (window.devicePixelRatio || 1); c.height = r.height * (window.devicePixelRatio || 1); draw(); };
    const ro = new ResizeObserver(fit); ro.observe(c); fit();
    return () => ro.disconnect();
  }, []);

  const down = (e) => { drag.current = { x: e.clientX, f: frame.current }; e.currentTarget.setPointerCapture?.(e.pointerId); };
  const move = (e) => { if (!drag.current) return; frame.current = drag.current.f - (e.clientX - drag.current.x) / 14; draw(); };
  const up = () => { drag.current = null; };

  return (
    <canvas ref={cv} onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}
      style={{ width: "100%", height: "100%", display: "block", cursor: "grab", touchAction: "none" }} />
  );
}
