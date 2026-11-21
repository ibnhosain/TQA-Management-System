/* লেকচারের স্লাইড — পরিচালক .pptx আপলোড করেন; পরিচালক ও এডমিন সব কোর্সে, উস্তাদ নিজের কোর্সে অ্যাপের ভেতরেই চালান।
   শিক্ষার্থী স্লাইড দেখে না। স্লাইড শেষে টপিক টিক (CoverPanel); পরিচালক শিক্ষার্থীর নোট লেখেন (✎ Note)। */
import { useEffect, useRef, useState } from "react";
import { api, deckApi, fetchBinary } from "../api";
import CoverPanel from "./CoverPanel.jsx";
import DeckPlayer from "./DeckPlayer.jsx";
import { Ico } from "../icons";

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
  const [edit, setEdit] = useState(null);           // { id, no, note, topics }

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
    try { const b = await fetchBinary(`/decks/${d.id}/`); setPlay({ deck: d, buffer: b, title: `Lecture ${d.no}${d.title ? " · " + d.title : ""}` }); setBusy(""); }
    catch (e) { setBusy("Could not open — " + (e?.message || "")); }
  };
  const saveEdit = async () => {
    try { await deckApi.edit(edit.id, { note: edit.note, topics: edit.topics }); setEdit(null); setBusy("✅ Saved"); await load(); }
    catch (e) { setBusy("Could not save — " + (e?.data?.error || e?.message || "")); }
  };
  const remove = async (d) => {
    if (!window.confirm(`Delete Lecture ${d.no} slides?`)) return;
    try { await api.deleteDeck(d.id); await load(); } catch (e) { setBusy("Could not delete — " + (e?.message || "")); }
  };

  const btn = { border: "1px solid #CFE0D5", background: "#fff", color: "#123F28", borderRadius: 10, padding: "8px 14px", cursor: "pointer", font: "inherit" };
  const go = { ...btn, background: "#1A5C3A", color: "#fff", borderColor: "#1A5C3A", fontWeight: 700 };
  return (
    <div>
      <h2 style={{ margin: "0 0 12px" }}><Ico e="🎞" /> Lecture Slides</h2>
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
          <button style={go} onClick={() => fileRef.current?.click()}><Ico e="⬆" /> Choose .pptx</button>
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
            {isDir && <button style={btn} onClick={() => setEdit({ id: d.id, no: d.no, note: d.note || "", topics: d.topics || "" })}><Ico e="✎" /> Note</button>}
            {isDir && <button style={btn} onClick={() => remove(d)}><Ico e="🗑" /></button>}
          </div>
        ))}
      </div>
      {edit && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.45)", zIndex: 1500, display: "grid", placeItems: "center" }}>
          <div style={{ background: "#fff", borderRadius: 16, padding: 18, width: "min(760px, 94vw)", maxHeight: "90vh", overflow: "auto" }}>
            <h3 style={{ margin: "0 0 6px" }}>Lecture {edit.no} · Student note</h3>
            <div style={{ fontSize: 12, color: "#5B6B62", marginBottom: 6 }}>Students see this in Homework after the teacher finishes the slides.</div>
            <textarea value={edit.note} onChange={(e) => setEdit({ ...edit, note: e.target.value })} rows={14} style={{ width: "100%", boxSizing: "border-box", font: "inherit", padding: 10, borderRadius: 10, border: "1px solid #CFE0D5" }} />
            <h3 style={{ margin: "12px 0 6px" }}>Slide topics (one per line)</h3>
            <div style={{ fontSize: 12, color: "#5B6B62", marginBottom: 6 }}>Used for ticking at the end only when Lecture Plan has no topics for this lecture.</div>
            <textarea value={edit.topics} onChange={(e) => setEdit({ ...edit, topics: e.target.value })} rows={6} style={{ width: "100%", boxSizing: "border-box", font: "inherit", padding: 10, borderRadius: 10, border: "1px solid #CFE0D5" }} />
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 12 }}>
              <button style={btn} onClick={() => setEdit(null)}>Cancel</button>
              <button style={go} onClick={saveEdit}>Save</button>
            </div>
          </div>
        </div>
      )}
      {play && <DeckPlayer buffer={play.buffer} title={play.title}
        finish={(back) => <CoverPanel deck={play.deck} onBack={back} onDone={() => { setPlay(null); if (document.fullscreenElement) document.exitFullscreen(); }} />}
        onClose={() => { setPlay(null); if (document.fullscreenElement) document.exitFullscreen(); }} />}
    </div>
  );
}
