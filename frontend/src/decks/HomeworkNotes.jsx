/* শিক্ষার্থীর Homework — প্রতিদিনের স্লাইড থেকে নোট (যে লেকচার তাকে পড়ানো হয়েছে, নতুনটা আগে)।
   ২০২৬-১১-২৪: মূল অ্যাপের প্রিমিয়াম চেহারায় (রং মূল অ্যাপের C-এর সাথে মেলানো)।
   ⚠️ মূল ফাইল থেকে import নেই — এই পাতা সেখান থেকেই lazy-load হয় (বৃত্তাকার নির্ভরতা এড়াতে)। */
import { useEffect, useState } from "react";
import { deckApi, settingsApi } from "../api";
import { Ico, withIcons } from "../icons";

const AR = /[؀-ۿ]/;
const G = "#1a5c3a", GD = "#123f28", GL = "#2a7a50", MUTED = "#64748b", TEXT = "#14221b", LINE = "#e3e9e5";
const card = {
  background: "#fff",
  border: `1px solid ${LINE}`,
  borderRadius: 16,
  boxShadow: "0 1px 2px rgba(16,34,24,.04), 0 6px 18px rgba(16,34,24,.05)",
};
const fmt = (d) => (d ? new Date(d).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }) : "");

function Notice({ icon, title, text }) {
  return (
    <div style={{ ...card, padding: "28px 18px", textAlign: "center" }}>
      <div style={{ width: 52, height: 52, margin: "0 auto", borderRadius: 16, background: "#eef4f0", color: GL, display: "grid", placeItems: "center" }}>
        <Ico e={icon} size={24} style={{ verticalAlign: 0 }} />
      </div>
      <div style={{ fontWeight: 700, fontSize: 15.5, marginTop: 10, color: TEXT }}>{title}</div>
      {text && <div style={{ fontSize: 13, color: MUTED, marginTop: 2 }}>{text}</div>}
    </div>
  );
}

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

  // নোটের একেকটি লাইন — 📖/✏️/🏠 বা "Lecture N" দিয়ে শুরু হলে অংশের শিরোনাম; "আরবি — অর্থ" হলে আরবি বড় করে
  const line = (t, i) => {
    if (!t.trim()) return <div key={i} style={{ height: 8 }} />;
    const head = /^[📖✏️🏠]/u.test(t) || /^Lecture \d+/.test(t);
    const parts = t.split(" — ");
    const ar = parts.length > 1 && AR.test(parts[0].trim()[0] || "");
    if (head)
      return (
        <div
          key={i}
          style={{
            margin: "16px 0 6px",
            padding: "8px 12px",
            borderRadius: 10,
            background: "#f1f8f4",
            borderLeft: `3px solid ${G}`,
            fontWeight: 700,
            color: GD,
            fontSize: 16.5,
            lineHeight: 1.5,
          }}
        >
          {withIcons(t, { style: { verticalAlign: "-0.15em", color: GL } })}
        </div>
      );
    return (
      <div key={i} style={{ margin: "4px 0", color: TEXT, fontSize: 16, lineHeight: 1.7 }}>
        {ar ? (
          <>
            <span dir="rtl" style={{ fontFamily: "Amiri, 'Traditional Arabic', serif", fontSize: 25, color: GD }}>
              {parts[0].trim()}
            </span>
            {parts[1] ? <span style={{ color: MUTED }}> — {parts.slice(1).join(" — ")}</span> : null}
          </>
        ) : (
          withIcons(t)
        )}
      </div>
    );
  };

  return (
    <div style={{ display: "grid", gap: 16, maxWidth: 900 }}>
      <style>{`.hw-row:hover{background:#f8fbf9}`}</style>
      <div>
        <h2 style={{ margin: 0, fontSize: 21, fontWeight: 700, letterSpacing: "-0.02em", color: TEXT, display: "flex", alignItems: "center", gap: 8 }}>
          <Ico e="📚" style={{ color: GL }} /> Homework
          {rows && rows.length > 0 && (
            <span
              style={{
                minWidth: 24,
                height: 22,
                padding: "0 8px",
                borderRadius: 999,
                display: "inline-grid",
                placeItems: "center",
                fontSize: 12,
                fontWeight: 700,
                background: "#e9f3ed",
                color: G,
              }}
            >
              {rows.length}
            </span>
          )}
        </h2>
        <div style={{ color: MUTED, fontSize: 13.5, marginTop: 4 }}>
          Notes from your daily lecture slides — newest first. Tap a lecture to open its notes.
        </div>
      </div>

      {err && <Notice icon="⚠️" title="Could not load your notes" text={err} />}
      {!rows && !err && <div style={{ ...card, padding: 24, textAlign: "center", color: MUTED }}>Loading…</div>}
      {off && <Notice icon="🔒" title="Homework notes are turned off for now" text="Your academy will switch them back on soon." />}
      {!off && rows && rows.length === 0 && (
        <Notice icon="📝" title="No notes yet" text="They will appear here after your class." />
      )}

      <div style={{ display: "grid", gap: 10 }}>
        {(rows || []).map((r, idx) => {
          const isOpen = open === r.id;
          return (
            <div key={r.id} style={{ ...card, overflow: "hidden", borderLeft: `4px solid ${isOpen ? G : LINE}` }}>
              <button
                className="hw-row"
                onClick={() => setOpen(isOpen ? null : r.id)}
                aria-expanded={isOpen}
                style={{
                  all: "unset",
                  cursor: "pointer",
                  display: "flex",
                  gap: 14,
                  alignItems: "center",
                  padding: "14px 16px",
                  width: "100%",
                  boxSizing: "border-box",
                }}
              >
                <div
                  style={{
                    width: 46,
                    height: 46,
                    borderRadius: 12,
                    flexShrink: 0,
                    display: "grid",
                    placeItems: "center",
                    fontWeight: 700,
                    fontSize: 18,
                    color: "#fff",
                    background: `linear-gradient(135deg, ${GL}, ${GD})`,
                  }}
                >
                  {r.no}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <b style={{ fontSize: 15.5, color: TEXT, letterSpacing: "-0.01em" }}>
                      Lecture {r.no}
                      {r.title ? ` · ${r.title}` : ""}
                    </b>
                    {idx === 0 && (
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: 999,
                          color: "#a16207",
                          background: "#fdf6e7",
                          border: "1px solid #f1dfb5",
                        }}
                      >
                        Latest
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12.5, color: MUTED, marginTop: 2 }}>
                    {r.course} · Taught on {fmt(r.taught_at)}
                  </div>
                </div>
                <span
                  aria-hidden="true"
                  style={{
                    color: G,
                    fontSize: 18,
                    transform: isOpen ? "rotate(90deg)" : "none",
                    transition: "transform .15s",
                    lineHeight: 1,
                  }}
                >
                  ›
                </span>
              </button>
              {isOpen && (
                <div style={{ padding: "4px 18px 18px", borderTop: `1px solid ${LINE}` }}>
                  {r.topics?.length > 0 && (
                    <div style={{ background: "#f1f8f4", border: "1px solid #d6e9dd", borderRadius: 12, padding: "12px 14px", margin: "14px 0 6px" }}>
                      <div style={{ fontSize: 11.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: G, marginBottom: 6 }}>
                        Covered in class
                      </div>
                      <div style={{ display: "grid", gap: 6 }}>
                        {r.topics.map((t, i) => (
                          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14.5, color: TEXT }}>
                            <span
                              style={{
                                width: 20,
                                height: 20,
                                borderRadius: "50%",
                                flexShrink: 0,
                                display: "grid",
                                placeItems: "center",
                                background: G,
                                color: "#fff",
                              }}
                            >
                              <Ico e="✓" size={12} style={{ verticalAlign: 0 }} />
                            </span>
                            {t}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {r.note ? (
                    r.note.split("\n").map(line)
                  ) : (
                    <div style={{ color: MUTED, marginTop: 12 }}>No note for this lecture yet.</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
