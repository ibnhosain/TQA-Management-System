/* স্লাইড শেষ হলে নিজে থেকে আসে — কোন টপিক কভার হলো, কোন শিক্ষার্থীর জন্য টিক দিন।
   Lecture Plan-এ এই লেকচারের টপিক থাকলে সেগুলোই (সেখানে কভার বসে); না থাকলে স্লাইডের নিজের টপিক। */
import { useEffect, useState } from "react";
import { deckApi } from "../api";

export default function CoverPanel({ deck, preselect, onBack, onDone }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [studs, setStuds] = useState({});
  const [tops, setTops] = useState({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    deckApi.cover(deck.id).then((d) => {
      setData(d);
      setStuds(Object.fromEntries(d.students.map((s) => [s.id, true])));
      if (preselect && d.plan_topics.some((t) => t.id === preselect)) setTops({ ["p" + preselect]: true });   // এইমাত্র চালানো টপিক
    }).catch((e) => setErr(e?.data?.error || e?.message || "Could not load"));
  }, [deck.id]);

  const topics = data ? [...data.plan_topics.map((t) => ({ key: "p" + t.id, id: t.id, text: t.text, section: t.section })),
    ...data.deck_topics.map((t, i) => ({ key: "d" + i, text: t, section: "" }))] : [];
  const allOn = topics.length > 0 && topics.every((t) => tops[t.key]);
  const save = async () => {
    const sids = Object.keys(studs).filter((k) => studs[k]).map(Number);
    if (!sids.length) { setErr("Please choose at least one student."); return; }
    if (!topics.some((t) => tops[t.key])) { setErr("Please tick the topics you covered."); return; }
    setSaving(true); setErr("");
    try {
      await deckApi.saveCover(deck.id, {
        student_ids: sids,
        topic_ids: topics.filter((t) => t.id && tops[t.key]).map((t) => t.id),
        deck_topics: topics.filter((t) => !t.id && tops[t.key]).map((t) => t.text),
      });
      setSaved("✅ Saved — the students can now see today's notes in Homework.");
    } catch (e) { setErr(e?.data?.error || e?.message || "Could not save"); }
    setSaving(false);
  };

  const box = { width: "min(720px, 94vw)", maxHeight: "88vh", overflow: "auto", background: "#fff", color: "#1f2a24", borderRadius: 18, padding: 20, boxShadow: "0 10px 50px rgba(0,0,0,.5)" };
  const b = { border: "1px solid #CFE0D5", background: "#fff", color: "#123F28", borderRadius: 10, padding: "9px 16px", cursor: "pointer", font: "inherit" };
  const go = { ...b, background: "#1A5C3A", color: "#fff", borderColor: "#1A5C3A", fontWeight: 700 };
  const row = (on) => ({ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", borderRadius: 10, cursor: "pointer",
    background: on ? "#EEF6F0" : "#F7F9F8", border: `1px solid ${on ? "#1A5C3A" : "#E3ECE6"}` });
  let lastSec = null;
  return (
    <div onClick={(e) => e.stopPropagation()} style={{ position: "absolute", inset: 0, background: "rgba(5,20,12,.72)", display: "grid", placeItems: "center", zIndex: 5 }}>
      <div style={box}>
        <h2 style={{ margin: "0 0 4px", color: "#1A5C3A" }}>🎉 {preselect ? "This part is finished" : `Lecture ${deck.no} finished`}</h2>
        <div style={{ color: "#5B6B62", marginBottom: 14 }}>Tick the topics you covered today.</div>
        {!data && !err && <div>Loading…</div>}
        {data && (
          <>
            {topics.length === 0 && <div style={{ color: "#8a5a00", marginBottom: 12 }}>No topics yet for Lecture {deck.no} — add them in Lecture Plan (or ask the director to write the slide topics).</div>}
            {topics.length > 0 && (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <b>Topics</b>
                <button style={b} onClick={() => setTops(Object.fromEntries(topics.map((t) => [t.key, !allOn])))}>{allOn ? "Clear all" : "✓ Tick all"}</button>
              </div>
            )}
            <div style={{ display: "grid", gap: 6, marginBottom: 16 }}>
              {topics.map((t) => {
                const head = t.section && t.section !== lastSec ? (lastSec = t.section) : null;
                return (
                  <div key={t.key}>
                    {head && <div style={{ fontWeight: 700, color: "#C9962A", margin: "8px 0 4px" }}>{head}</div>}
                    <label style={row(!!tops[t.key])}>
                      <input type="checkbox" checked={!!tops[t.key]} onChange={(e) => setTops({ ...tops, [t.key]: e.target.checked })} style={{ width: 20, height: 20 }} />
                      <span>{t.text}</span>
                    </label>
                  </div>
                );
              })}
            </div>
            <b>Students</b>
            {data.students.length === 0 && <div style={{ color: "#8a5a00", margin: "6px 0 12px" }}>No students of yours in this course.</div>}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "8px 0 16px" }}>
              {data.students.map((s) => (
                <label key={s.id} style={{ ...row(!!studs[s.id]), padding: "6px 12px" }}>
                  <input type="checkbox" checked={!!studs[s.id]} onChange={(e) => setStuds({ ...studs, [s.id]: e.target.checked })} />
                  <span>{s.name}{s.done ? " ✓" : ""}</span>
                </label>
              ))}
            </div>
          </>
        )}
        {err && <div style={{ color: "#b00020", marginBottom: 10 }}>{err}</div>}
        {saved && <div style={{ color: "#1A5C3A", marginBottom: 10, fontWeight: 700 }}>{saved}</div>}
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", flexWrap: "wrap" }}>
          <button style={b} onClick={onBack}>‹ Back to slides</button>
          {!saved && <button style={go} disabled={saving || !data} onClick={save}>{saving ? "Saving…" : "Save"}</button>}
          {saved && <button style={go} onClick={onDone}>Close</button>}
        </div>
      </div>
    </div>
  );
}
