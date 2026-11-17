/* Lesson Plan-এ টপিকে ক্লিক → সেদিনের লেকচারের স্লাইড। উস্তাদ/এডমিন/পরিচালক পান উস্তাদের স্লাইড (শেষে টপিক-টিক),
   শিক্ষার্থী পায় তার পড়া ও প্র্যাকটিসের স্লাইড। কোনো সফটওয়্যার লাগে না — অ্যাপের ভেতরেই চলে। */
import { useEffect, useRef, useState } from "react";
import { approvalsApi, deckApi, fetchBinary, settingsApi } from "../api";
import DeckPlayer from "./DeckPlayer.jsx";
import CoverPanel from "./CoverPanel.jsx";

export default function PlanPlayer({ course, no, part, topicId, student, forStudent, onClose }) {
  const [play, setPlay] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const d = await deckApi.find(course, no, forStudent);
        const buffer = await fetchBinary(`/decks/${d.id}/`);
        let auto = true;
        try { auto = (await settingsApi.get()).flags.auto_cover_panel !== false; } catch { /* ডিফল্ট চালু */ }
        if (live) setPlay({ deck: d, buffer, auto });
      } catch (e) { if (live) setErr(e?.data?.error || e?.message || "Could not open the slides"); }
    })();
    return () => { live = false; };
  }, [course, no]);
  // উস্তাদ/এডমিন স্লাইড চালালে সময় রাখা (এডমিন অনুমোদনের আগে দেখেন) — প্রতি ৩০ সেকেন্ডে ও বন্ধ করলে
  const playRef = useRef({ id: null, t0: 0 });
  const tick = () => { const p = playRef.current; if (p.id) approvalsApi.playTick(p.id, Math.round((Date.now() - p.t0) / 1000)).catch(() => {}); };
  useEffect(() => {
    if (!play || student) return undefined;
    let live = true;
    approvalsApi.playStart(course, no, part?.key || "", forStudent).then((r) => { if (live && r?.id) playRef.current = { id: r.id, t0: Date.now() }; }).catch(() => {});
    const iv = setInterval(tick, 30000);
    return () => { live = false; clearInterval(iv); tick(); };
  }, [play]); // eslint-disable-line
  const close = () => { if (document.fullscreenElement) document.exitFullscreen(); onClose(); };

  if (!play)
    return (
      <div onClick={err ? close : undefined} style={{ position: "fixed", inset: 0, background: "rgba(5,20,12,.75)", zIndex: 2000, display: "grid", placeItems: "center" }}>
        <div style={{ background: "#fff", borderRadius: 16, padding: "18px 22px", maxWidth: 420, textAlign: "center", color: "#123F28" }}>
          {err ? <>{err}<div style={{ marginTop: 12 }}><button onClick={close} style={{ border: "1px solid #CFE0D5", background: "#fff", borderRadius: 10, padding: "8px 16px", cursor: "pointer" }}>Close</button></div></> : `Opening Lecture ${no}…`}
        </div>
      </div>
    );
  return (
    <DeckPlayer buffer={play.buffer} part={part} autoFinish={play.auto} title={`Lecture ${no}${part?.label ? " · " + part.label : ""}${student ? " · My Practice" : ""}`} onClose={close}
      finish={student ? undefined : (back) => <CoverPanel deck={play.deck} preselect={topicId} onBack={back} onDone={close} />} />
  );
}
