/* Full-screen in-app player for a lecture's .pptx: click / tap / → to go on, ← to go back, Esc to close.
   Entrance animations and slide transitions play as in PowerPoint (fade, pop, zoom, fly, bounce, spin, wipe, wheel, float). */
import { useEffect, useMemo, useRef, useState } from "react";
import { loadPptx } from "./pptx";

const CSS = `
@keyframes dk-fade{from{opacity:0}to{opacity:1}}
@keyframes dk-pop{0%{transform:scale(0);opacity:0}70%{transform:scale(1.18);opacity:1}100%{transform:scale(1)}}
@keyframes dk-zoom{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes dk-flyB{from{transform:translateY(110vh)}to{transform:none}}
@keyframes dk-flyT{from{transform:translateY(-110vh)}to{transform:none}}
@keyframes dk-flyL{from{transform:translateX(-110vw)}to{transform:none}}
@keyframes dk-flyR{from{transform:translateX(110vw)}to{transform:none}}
@keyframes dk-bounce{0%{transform:translateY(-60%);opacity:0}45%{transform:translateY(0);opacity:1}62%{transform:translateY(-12%)}78%{transform:translateY(0)}90%{transform:translateY(-3%)}100%{transform:none}}
@keyframes dk-spin{from{transform:scale(0) rotate(-360deg);opacity:0}to{transform:scale(1) rotate(0);opacity:1}}
@keyframes dk-wipe{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes dk-wheel{from{clip-path:circle(0% at 50% 50%);transform:rotate(-90deg)}to{clip-path:circle(75% at 50% 50%);transform:none}}
@keyframes dk-float{from{transform:translateY(25%);opacity:0}to{transform:none;opacity:1}}
@keyframes dk-out{from{opacity:1}to{opacity:0}}
@keyframes dk-t-fade{from{opacity:0}to{opacity:1}}
@keyframes dk-t-push{from{transform:translateY(100%)}to{transform:none}}
@keyframes dk-t-pushl{from{transform:translateX(100%)}to{transform:none}}
@keyframes dk-t-cover{from{transform:translateX(-100%)}to{transform:none}}
@keyframes dk-t-zoom{from{transform:scale(.3);opacity:0}to{transform:none;opacity:1}}
@keyframes dk-t-circle{from{clip-path:circle(0% at 50% 50%)}to{clip-path:circle(75% at 50% 50%)}}
@keyframes dk-t-split{from{clip-path:inset(0 50% 0 50%)}to{clip-path:inset(0 0 0 0)}}
@keyframes dk-t-wipe{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
.dk-stage *{box-sizing:border-box}
`;
const DUR = { fade: 500, pop: 600, zoom: 500, fly: 650, bounce: 900, spin: 700, wipe: 600, wheel: 700, float: 800, appear: 1 };
const FONT_FALLBACK = { "Traditional Arabic": "'Traditional Arabic','Amiri','Noto Naskh Arabic',serif", Cambria: "Cambria,'Caladea',Georgia,serif",
  Calibri: "Calibri,'Carlito','Segoe UI',Arial,sans-serif", Arial: "Arial,Helvetica,sans-serif" };
const fam = (f) => (f ? FONT_FALLBACK[f] || `'${f}',Calibri,Arial,sans-serif` : "Calibri,'Carlito','Segoe UI',Arial,sans-serif");

function animFor(e) {
  if (e.cls === "exit") return `dk-out ${DUR.fade}ms ease both`;
  let k = e.effect;
  if (k === "fly") k = { 4: "flyB", 1: "flyT", 8: "flyL", 2: "flyR" }[e.dir] || "flyB";
  if (k === "appear") return "none";
  return `dk-${k} ${DUR[e.effect] || 600}ms cubic-bezier(.2,.8,.3,1) ${e.delay || 0}ms both`;
}
function transitionCss(t) {
  if (!t) return "dk-t-fade 400ms ease both";
  const k = { fade: "fade", push: t.dir === "l" ? "pushl" : "push", cover: "cover", zoom: "zoom", circle: "circle", split: "split", wipe: "wipe", randomBar: "wipe" }[t.kind] || "fade";
  return `dk-t-${k} 600ms ease both`;
}

function Text({ tx, s }) {
  if (!tx) return null;
  const v = { t: "flex-start", ctr: "center", b: "flex-end" }[tx.anchor] || "flex-start";
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: v,
      padding: `${tx.pad[0] * s}px ${tx.pad[1] * s}px ${tx.pad[2] * s}px ${tx.pad[3] * s}px`, overflow: "visible" }}>
      {tx.paras.map((p, i) => {
        const rtl = p.rtl || p.runs.some((r) => /[؀-ۿ]/.test(r.t || ""));
        const align = { l: rtl ? "right" : "left", ctr: "center", r: "right", just: "justify" }[p.algn] || "left";
        const align2 = p.algn === "l" && rtl ? "left" : align;
        const empty = !p.runs.some((r) => r.t);
        return (
          <div key={i} dir={rtl ? "rtl" : "ltr"} style={{ textAlign: p.algn === "ctr" ? "center" : align2, marginTop: p.bef * s * 12700, marginBottom: p.aft * s * 12700,
            paddingLeft: p.marL * s, lineHeight: 1.15, whiteSpace: tx.wrap ? "pre-wrap" : "pre", wordBreak: "normal", minHeight: empty ? p.endSz * s * 12700 * 1.15 : undefined }}>
            {p.bullet ? <span>{p.bullet} </span> : null}
            {p.runs.map((r, k) => r.br ? <br key={k} /> : (
              <span key={k} style={{ fontSize: r.sz * s * 12700, fontWeight: r.b ? 700 : 400, fontStyle: r.i ? "italic" : "normal",
                textDecoration: r.u ? "underline" : "none", color: r.col || "#000",
                fontFamily: fam(/[؀-ۿ]/.test(r.t) ? r.cs || r.font : r.font) }}>{r.t}</span>
            ))}
          </div>
        );
      })}
    </div>
  );
}

function star(n, inner = 0.38) {
  const pts = [];
  for (let i = 0; i < n * 2; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / n, r = i % 2 ? inner * 0.5 : 0.5;
    pts.push(`${50 + r * 100 * Math.cos(a)},${50 + r * 100 * Math.sin(a)}`);
  }
  return pts.join(" ");
}

function Item({ it, s, anim, hidden }) {
  const box = { position: "absolute", left: it.x * s, top: it.y * s, width: it.w * s, height: it.h * s,
    transform: `${it.rot ? `rotate(${it.rot}deg)` : ""}${it.flipH ? " scaleX(-1)" : ""}${it.flipV ? " scaleY(-1)" : ""}` || undefined,
    visibility: hidden ? "hidden" : "visible", animation: anim || undefined };
  if (it.kind === "pic") {
    if (!it.src) return null;
    if (it.crop) {
      const [l, t, r, b] = it.crop, iw = (it.w * s) / (1 - l - r), ih = (it.h * s) / (1 - t - b);
      return <div style={{ ...box, overflow: "hidden" }}><img alt="" draggable={false} src={it.src} style={{ position: "absolute", left: -l * iw, top: -t * ih, width: iw, height: ih }} /></div>;
    }
    return <img alt="" draggable={false} src={it.src} style={{ ...box, objectFit: "fill" }} />;
  }
  if (it.kind === "tbl") {
    const tw = it.cols.reduce((a, b) => a + b, 0);
    return (
      <table style={{ ...box, height: "auto", borderCollapse: "collapse", tableLayout: "fixed" }}>
        <colgroup>{it.cols.map((c, i) => <col key={i} style={{ width: `${(c / tw) * 100}%` }} />)}</colgroup>
        <tbody>{it.rows.map((r, i) => (
          <tr key={i} style={{ height: r.h * s }}>{r.cells.filter((c) => !c.hm).map((c, k) => (
            <td key={k} colSpan={c.span} style={{ position: "relative", background: c.fill || "transparent", verticalAlign: { t: "top", ctr: "middle", b: "bottom" }[c.anchor] || "top",
              border: c.border ? `${Math.max(1, c.border.w * s)}px solid ${c.border.c}` : "1px solid #d7e7dc", padding: 0 }}>
              <div style={{ position: "relative", minHeight: r.h * s }}><Text tx={{ ...c.text, pad: c.pad, anchor: c.anchor }} s={s} /></div>
            </td>))}</tr>))}</tbody>
      </table>
    );
  }
  const g = it.geom;
  const border = it.line ? `${Math.max(1, it.line.w * s)}px solid ${it.line.c}` : "none";
  let shapeEl = null;
  if (g === "star5" || g === "star4" || g === "star6" || g === "triangle" || g === "rightArrow" || g === "leftArrow" || g === "heart") {
    const poly = { star5: star(5), star4: star(4, 0.2), star6: star(6), triangle: "50,0 100,100 0,100",
      rightArrow: "0,30 60,30 60,0 100,50 60,100 60,70 0,70", leftArrow: "100,30 40,30 40,0 0,50 40,100 40,70 100,70" }[g];
    shapeEl = g === "heart"
      ? <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}><path d="M50 90 C10 60 0 35 20 18 C35 5 50 18 50 28 C50 18 65 5 80 18 C100 35 90 60 50 90Z" fill={it.fill || "none"} /></svg>
      : <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}><polygon points={poly} fill={it.fill || "none"} stroke={it.line?.c || "none"} strokeWidth={it.line ? 1 : 0} /></svg>;
  } else if (it.fill || it.line) {
    const radius = g === "ellipse" ? "50%" : g === "roundRect" ? Math.min(it.w, it.h) * s * (it.adj / 100000) : 0;
    shapeEl = <div style={{ position: "absolute", inset: 0, background: it.fill || "transparent", border, borderRadius: radius }} />;
  }
  return <div style={box}>{shapeEl}<Text tx={it.text} s={s} /></div>;
}

function rangeOf(deck, part) {
  const all = [0, deck.slides.length];
  const secs = deck.sections || [];
  if (!part?.key) return all;
  const me = secs.find((s) => s.name === part.key);
  if (!me) return all;
  const mine = secs.filter((s) => (part.keys || []).includes(s.name)).sort((a, b) => a.start - b.start);
  const from = mine[0] === me ? 0 : me.start;
  const nxt = mine.find((s) => s.start > me.start);
  return [from, nxt ? nxt.start : deck.slides.length];
}

export default function DeckPlayer({ buffer, title, onClose, finish, part }) {
  const [done, setDone] = useState(false);   // শেষ স্লাইডের পর — কভার-টিকের প্যানেল নিজে থেকে আসে
  const [deck, setDeck] = useState(null);
  const [err, setErr] = useState("");
  const [n, setN] = useState(0);
  const [step, setStep] = useState(0);
  const [notes, setNotes] = useState(false);
  const [size, setSize] = useState({ w: window.innerWidth, h: window.innerHeight });
  const wrap = useRef(null);

  useEffect(() => {
    let d;
    loadPptx(buffer).then((x) => { d = x; setDeck(x); setN(rangeOf(x, part)[0]); setStep(0); }).catch((e) => setErr(String(e?.message || e)));
    if (!document.getElementById("dk-css")) { const st = document.createElement("style"); st.id = "dk-css"; st.textContent = CSS; document.head.appendChild(st); }
    if (!document.getElementById("dk-amiri")) { const l = document.createElement("link"); l.id = "dk-amiri"; l.rel = "stylesheet";
      l.href = "https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap"; document.head.appendChild(l); }
    const r = () => setSize({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener("resize", r);
    return () => { window.removeEventListener("resize", r); d && d.dispose(); };
  }, [buffer]);

  // part = { key, keys }: শুধু এই টপিকের বইয়ের অংশ (PowerPoint section) চলে, পরের টপিকের অংশ এলে থামে
  const [from, to] = deck ? rangeOf(deck, part) : [0, 0];
  const slide = deck?.slides[n];
  const clicks = slide?.steps.clicks.length || 0;
  const next = () => { if (!deck) return; if (step < clicks) setStep(step + 1); else if (n < to - 1) { setN(n + 1); setStep(0); } else if (finish) setDone(true); };
  const prev = () => { if (!deck) return; if (step > 0) setStep(step - 1); else if (n > from) { const p = deck.slides[n - 1]; setN(n - 1); setStep(p.steps.clicks.length); } };

  useEffect(() => {
    const k = (e) => {
      if (done) return;
      if (["ArrowRight", "ArrowDown", "PageDown", " ", "Enter"].includes(e.key)) { e.preventDefault(); next(); }
      else if (["ArrowLeft", "ArrowUp", "PageUp", "Backspace"].includes(e.key)) { e.preventDefault(); prev(); }
      else if (e.key === "Escape") onClose && onClose();
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  });

  const notesH = notes ? Math.min(220, size.h * 0.28) : 0;
  const barH = 52;
  const scale = deck ? Math.min(size.w / deck.W, (size.h - barH - notesH) / deck.H) : 1;

  // which items are hidden/animating at this step
  const state = useMemo(() => {
    if (!slide) return {};
    const st = {};
    const entr = new Set();
    for (const g of slide.steps.clicks) for (const e of g) if (e.cls === "entr") entr.add(e.id);
    for (const e of slide.steps.auto) if (e.cls === "entr") st[e.id] = { anim: animFor(e) };
    for (const id of entr) if (!st[id]) st[id] = { hidden: true };
    for (let k = 0; k < step; k++) for (const e of slide.steps.clicks[k]) {
      st[e.id] = e.cls === "exit" ? { hidden: k < step - 1, anim: k === step - 1 ? animFor(e) : undefined } : { anim: k === step - 1 ? animFor(e) : undefined };
    }
    return st;
  }, [slide, step]);

  const btn = { background: "rgba(255,255,255,.12)", color: "#fff", border: "1px solid rgba(255,255,255,.25)", borderRadius: 999, padding: "6px 14px", cursor: "pointer", font: "inherit", fontSize: 14 };
  return (
    <div ref={wrap} onContextMenu={(e) => e.preventDefault()} style={{ position: "fixed", inset: 0, background: "#0d1f16", zIndex: 2000, display: "flex", flexDirection: "column", userSelect: "none" }}>
      <div style={{ height: barH, display: "flex", alignItems: "center", gap: 8, padding: "0 12px", color: "#fff" }}>
        <b style={{ flex: 1, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}>{title}</b>
        {deck && <span style={{ opacity: 0.8, fontSize: 14 }}>{n - from + 1} / {to - from}</span>}
        <button style={btn} onClick={prev}>‹</button>
        <button style={btn} onClick={next}>›</button>
        <button style={btn} onClick={() => setNotes((v) => !v)}>{notes ? "Hide notes" : "Notes"}</button>
        <button style={btn} onClick={() => (document.fullscreenElement ? document.exitFullscreen() : wrap.current.requestFullscreen?.())}>⛶</button>
        {finish && <button style={btn} onClick={() => setDone(true)}>✓ Topics</button>}
        <button style={btn} onClick={onClose}>✕</button>
      </div>
      <div onClick={next} style={{ flex: 1, display: "grid", placeItems: "center", overflow: "hidden", cursor: "pointer" }}>
        {err && <div style={{ color: "#fff", padding: 20 }}>Could not open this file: {err}</div>}
        {!deck && !err && <div style={{ color: "#fff" }}>Opening…</div>}
        {slide && (
          <div key={n} className="dk-stage" style={{ position: "relative", width: deck.W * scale, height: deck.H * scale, background: slide.bg, overflow: "hidden",
            boxShadow: "0 8px 40px rgba(0,0,0,.5)", animation: transitionCss(slide.transition) }}>
            {slide.items.map((it, i) => {
              const sst = !it.under ? state[it.id] : null;
              return <Item key={i} it={it} s={scale} anim={sst?.anim} hidden={sst?.hidden} />;
            })}
          </div>
        )}
      </div>
      {done && finish && finish(() => setDone(false))}
      {notes && slide && (
        <div style={{ height: notesH, overflow: "auto", background: "#fff8e6", color: "#1f2a24", padding: "10px 16px", whiteSpace: "pre-wrap", fontSize: 15, borderTop: "3px solid #c9962a" }}>
          {slide.notes || "—"}
        </div>
      )}
    </div>
  );
}
