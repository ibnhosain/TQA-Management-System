/* লেকচারের স্লাইড — পরিচালক .pptx আপলোড করেন; পরিচালক, এডমিন ও উস্তাদ অ্যাপের ভেতরেই চালান। আর কিছু নয়। */
import { useEffect, useRef, useState } from "react";
import { api, fetchBinary } from "../api";
import DeckPlayer from "./DeckPlayer.jsx";

export default function DecksView({ user, courses }) {
  const isDir = user?.role === "director";
  const mine = courses || [];
  const [course, setCourse] = useState("");
  const [decks, setDecks] = useState([]);
  const [busy, setBusy] = useState("");
  const [play, setPlay] = useState(null);           // { buffer, title }
  const [no, setNo] = useState(1);
  const [title, setTitle] = useState("");
  const fileRef = useRef(null);

  useEffect(() => { if (!course && mine.length) setCourse(String(mine[0].id)); }, [courses]); // eslint-disable-line
  const load = async () => {
    if (!course) return;
    try {
      const d = await api.decks(course);
      setDecks(d || []);
      const next = (d || []).reduce((m, x) => Math.max(m, x.no), 0) + 1;
      setNo(next);
    } catch (e) { setBusy("Could not load — " + (e?.data?.error || e?.message || "")); }
  };
  useEffect(() => { load(); }, [course]); // eslint-disable-line

  const upload = async (f) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pptx")) { setBusy("Please choose a .pptx file."); return; }
    setBusy("Uploading…");
    try {
      await api.uploadDeck(Number(course), Number(no) || 1, title, f);
      setTitle(""); setBusy("✅ Uploaded");
      await load();
    } catch (e) { setBusy("Could not upload — " + (e?.data?.error || e?.message || "")); }
    if (fileRef.current) fileRef.current.value = "";
  };
  const open = async (d) => {
    setBusy("Opening…");
    try { const b = await fetchBinary(`/decks/${d.id}/`); setPlay({ buffer: b, title: `Lecture ${d.no}${d.title ? " · " + d.title : ""}` }); setBusy(""); }
    catch (e) { setBusy("Could not open — " + (e?.message || "")); }
  };
  const remove = async (d) => {
    if (!window.confirm(`Delete Lecture ${d.no} slides?`)) return;
    try { await api.deleteDeck(d.id); await load(); } catch (e) { setBusy("Could not delete — " + (e?.message || "")); }
  };

  const btn = { border: "1px solid #CFE0D5", background: "#fff", color: "#123F28", borderRadius: 10, padding: "8px 14px", cursor: "pointer", font: "inherit" };
  const go = { ...btn, background: "#1A5C3A", color: "#fff", borderColor: "#1A5C3A", fontWeight: 700 };
  return (
    <div>
      <h2 style={{ margin: "0 0 12px" }}>🎞️ Lecture Slides</h2>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 14 }}>
        <select value={course} onChange={(e) => setCourse(e.target.value)} style={{ ...btn, padding: "8px 10px" }}>
          {mine.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>
      {isDir && (
        <div style={{ background: "#fff", border: "1px solid #DCE9E0", borderRadius: 14, padding: 14, marginBottom: 16, display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <b>Upload a PowerPoint (.pptx)</b>
          <label>Lecture <input type="number" min="1" value={no} onChange={(e) => setNo(e.target.value)} style={{ ...btn, width: 80, padding: "6px 8px" }} /></label>
          <input placeholder="Title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} style={{ ...btn, flex: 1, minWidth: 180, cursor: "text" }} />
          <input ref={fileRef} type="file" accept=".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation" style={{ display: "none" }} onChange={(e) => upload(e.target.files?.[0])} />
          <button style={go} onClick={() => fileRef.current?.click()}>⬆ Choose .pptx</button>
          <span style={{ fontSize: 12, color: "#5B6B62", width: "100%" }}>Same lecture number again = the old slides are replaced.</span>
        </div>
      )}
      {busy && <div style={{ marginBottom: 10, color: "#123F28" }}>{busy}</div>}
      <div style={{ display: "grid", gap: 10 }}>
        {decks.length === 0 && <div style={{ color: "#5B6B62" }}>No slides yet.</div>}
        {decks.map((d) => (
          <div key={d.id} style={{ display: "flex", alignItems: "center", gap: 12, background: "#fff", border: "1px solid #DCE9E0", borderRadius: 14, padding: "12px 14px" }}>
            <div style={{ width: 54, height: 54, borderRadius: 12, background: "#EEF6F0", display: "grid", placeItems: "center", fontWeight: 800, color: "#1A5C3A", fontSize: 20 }}>{d.no}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700 }}>Lecture {d.no}{d.title ? ` · ${d.title}` : ""}</div>
              <div style={{ fontSize: 12, color: "#5B6B62" }}>{d.filename} · {(d.size / 1048576).toFixed(1)} MB</div>
            </div>
            <button style={go} onClick={() => open(d)}>▶ Play</button>
            {isDir && <button style={btn} onClick={() => remove(d)}>🗑</button>}
          </div>
        ))}
      </div>
      {play && <DeckPlayer buffer={play.buffer} title={play.title} onClose={() => { setPlay(null); if (document.fullscreenElement) document.exitFullscreen(); }} />}
    </div>
  );
}
