/* শিক্ষার্থীর Homework — প্রতিদিনের স্লাইড থেকে নোট (যে লেকচার তাকে পড়ানো হয়েছে, নতুনটা আগে)। */
import { useEffect, useState } from "react";
import { deckApi, settingsApi } from "../api";

const AR = /[؀-ۿ]/;

export default function HomeworkNotes() {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(null);
  const [off, setOff] = useState(false);
  useEffect(() => { settingsApi.get().then((r) => setOff(r?.flags?.homework_notes === false)).catch(() => {}); }, []);
  useEffect(() => {
    deckApi.notes().then((r) => { setRows(r || []); if (r?.length) setOpen(r[0].id); })
      .catch((e) => setErr(e?.message || "Could not load"));
  }, []);

  const line = (t, i) => {
    if (!t.trim()) return <div key={i} style={{ height: 8 }} />;
    const head = /^[📖✏️🏠]/u.test(t) || /^Lecture \d+/.test(t);
    const parts = t.split(" — ");
    const ar = parts.length > 1 && AR.test(parts[0].trim()[0] || "");
    return (
      <div key={i} style={{ margin: head ? "12px 0 4px" : "3px 0", fontWeight: head ? 800 : 400, color: head ? "#1A5C3A" : "#1f2a24", fontSize: head ? 18 : 16, lineHeight: 1.6 }}>
        {ar ? <><span dir="rtl" style={{ fontFamily: "Amiri, 'Traditional Arabic', serif", fontSize: 24 }}>{parts[0].trim()}</span>{parts[1] ? <span style={{ color: "#5B6B62" }}> — {parts.slice(1).join(" — ")}</span> : null}</> : t}
      </div>
    );
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 12px" }}>📚 Homework</h2>
      <div style={{ color: "#5B6B62", marginBottom: 14 }}>Notes from your daily lecture slides.</div>
      {err && <div style={{ color: "#b00020" }}>{err}</div>}
      {!rows && !err && <div>Loading…</div>}
      {off && <div style={{ color: "#5B6B62" }}>Homework notes are turned off for now.</div>}
      {!off && rows && rows.length === 0 && <div style={{ color: "#5B6B62" }}>No notes yet. They will appear here after your class.</div>}
      <div style={{ display: "grid", gap: 10 }}>
        {(rows || []).map((r) => (
          <div key={r.id} style={{ background: "#fff", border: "1px solid #DCE9E0", borderRadius: 14, overflow: "hidden" }}>
            <button onClick={() => setOpen(open === r.id ? null : r.id)} style={{ all: "unset", cursor: "pointer", display: "flex", gap: 12, alignItems: "center", padding: "12px 14px", width: "100%", boxSizing: "border-box" }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: "#EEF6F0", display: "grid", placeItems: "center", fontWeight: 800, color: "#1A5C3A", fontSize: 18 }}>{r.no}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700 }}>Lecture {r.no}{r.title ? ` · ${r.title}` : ""}</div>
                <div style={{ fontSize: 12, color: "#5B6B62" }}>{r.course} · {new Date(r.taught_at).toLocaleDateString("en-GB")}</div>
              </div>
              <span style={{ color: "#1A5C3A" }}>{open === r.id ? "▲" : "▼"}</span>
            </button>
            {open === r.id && (
              <div style={{ padding: "0 16px 16px", borderTop: "1px solid #EEF3F0" }}>
                {r.topics?.length > 0 && (
                  <div style={{ background: "#EEF6F0", borderRadius: 10, padding: "10px 12px", margin: "12px 0" }}>
                    <b style={{ color: "#1A5C3A" }}>Covered in class</b>
                    {r.topics.map((t, i) => <div key={i}>✓ {t}</div>)}
                  </div>
                )}
                {r.note ? r.note.split("\n").map(line) : <div style={{ color: "#5B6B62", marginTop: 12 }}>No note for this lecture yet.</div>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
