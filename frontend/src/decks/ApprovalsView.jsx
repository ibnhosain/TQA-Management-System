/* এডমিন/পরিচালকের "Lecture Approvals" — উস্তাদ যে শিক্ষার্থীর একটা লেকচারের সব টপিক টিক দিয়েছেন, সেগুলো এখানে আসে।
   দেখা যায়: কোন দিন টিক, সেই দিনগুলোর ক্লাসে শিক্ষার্থী ও উস্তাদ কত মিনিট ছিলেন, কোন অংশের স্লাইড কত মিনিট চলেছে।
   Approve দিলে তবেই ওই শিক্ষার্থীর পরের লেকচার খোলে।

   ২০২৬-১১-২২: মূল অ্যাপের প্রিমিয়াম চেহারায় সাজানো (রং মূল অ্যাপের C-এর সাথে মেলানো)।
   ব্রাউজারের window.confirm-এর বদলে কার্ডের ভেতরেই "নিশ্চিত করুন / বাতিল"।
   ⚠️ মূল ফাইল (tqa-management-system.jsx) থেকে কিছু import করা হয়নি — এই পাতা সেখান
   থেকেই lazy-load হয়, উল্টো import করলে বৃত্তাকার নির্ভরতা হতো। */
import { useEffect, useState } from "react";
import { api, approvalsApi } from "../api";
import { Ico, withIcons } from "../icons";

const G = "#1a5c3a", GD = "#123f28", GL = "#2a7a50", GOLD = "#c9962a", MUTED = "#64748b", TEXT = "#14221b";
const RED = "#c0392b", LINE = "#e3e9e5";
const fmt = (d) => (d ? new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "");
const card = {
  background: "#fff",
  border: `1px solid ${LINE}`,
  borderRadius: 16,
  boxShadow: "0 1px 2px rgba(16,34,24,.04), 0 6px 18px rgba(16,34,24,.05)",
};
const btn = (kind = "primary") => ({
  border: kind === "ghost" ? "1.5px solid #c9d8cf" : "none",
  background:
    kind === "primary" ? `linear-gradient(180deg, #22714a, ${G})` : kind === "danger" ? "#fdeceb" : kind === "ghost" ? "#fff" : "#eef3f0",
  color: kind === "primary" ? "#fff" : kind === "danger" ? RED : GD,
  borderRadius: 10,
  padding: "10px 16px",
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  font: "inherit",
  display: "inline-flex",
  alignItems: "center",
  gap: 7,
  boxShadow: kind === "primary" ? "0 1px 2px rgba(18,63,40,.3), inset 0 1px 0 rgba(255,255,255,.14)" : "none",
});
const initials = (n) =>
  String(n || "?").trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";
const CSS = `
.apv details > summary{list-style:none;cursor:pointer}
.apv details > summary::-webkit-details-marker{display:none}
.apv details[open] .apv-chev{transform:rotate(90deg)}
.apv-chev{display:inline-block;transition:transform .15s}
.apv table{border-collapse:collapse;width:100%;font-size:13.5px}
.apv th{text-align:left;font-size:11.5px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#475569;
  background:#f6f9f7;padding:9px 12px;border-bottom:1px solid ${LINE}}
.apv td{padding:9px 12px;border-bottom:1px solid ${LINE};color:${TEXT}}
.apv tr:last-child td{border-bottom:none}
.apv select,.apv input{border:1px solid #d5dfd9;border-radius:10px;padding:10px 12px;font:inherit;font-size:14px;background:#fff;color:${TEXT}}
.apv select:focus,.apv input:focus{outline:none;border-color:${GL};box-shadow:0 0 0 3px rgba(26,92,58,.14)}
.apv-seg{display:inline-flex;gap:2px;padding:3px;border-radius:12px;background:#eef3f0;border:1px solid ${LINE}}
.apv-seg button{border:none;background:transparent;padding:7px 14px;border-radius:9px;font:inherit;font-size:13.5px;font-weight:600;color:#475569;cursor:pointer}
.apv-seg button.on{background:#fff;color:${G};box-shadow:0 1px 2px rgba(16,34,24,.12)}
.apv-chip{border:1px solid #d5dfd9;background:#fff;border-radius:999px;padding:7px 13px;font:inherit;font-size:13px;font-weight:600;color:#475569;cursor:pointer}
.apv-chip.on{background:#e9f3ed;border-color:${GL};color:${G}}
.apv-unlock label{display:block}
@media(max-width:560px){.apv-unlock label{flex:1 1 100%}.apv-unlock select{width:100%}}
`;

function Metric({ label, value, ok, icon }) {
  const col = ok === "warn" ? "#a16207" : ok ? G : RED;
  const bg = ok === "warn" ? "#fdf6e7" : ok ? "#f1faf4" : "#fff6f4";
  return (
    <div style={{ background: bg, border: `1px solid ${col}22`, borderRadius: 12, padding: "10px 14px", minWidth: 150, flex: "1 1 150px" }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", display: "flex", alignItems: "center", gap: 6 }}>
        <Ico e={icon} style={{ color: col }} /> {label}
      </div>
      <div style={{ fontSize: 21, fontWeight: 700, color: col, letterSpacing: "-0.02em", marginTop: 2 }}>{value}</div>
    </div>
  );
}

function Card({ p, onApprove, busy }) {
  const [confirm, setConfirm] = useState(false);
  const marked = p.topics.filter((t) => t.covered === "covered").length;
  const missed = p.topics.length - marked;
  const classMin = p.classes.reduce((a, c) => a + (c.student_min || 0), 0);
  const warnings = [
    !classMin && "No class attendance was found on the days the topics were ticked.",
    !p.slides_total_min && "No slides were played for this student.",
  ].filter(Boolean);
  return (
    <div style={{ ...card, overflow: "hidden" }}>
      <div style={{ padding: "16px 18px", display: "grid", gap: 14 }}>
        {/* কে, কোন লেকচার */}
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <span
            aria-hidden="true"
            style={{
              width: 42,
              height: 42,
              borderRadius: "50%",
              flexShrink: 0,
              display: "grid",
              placeItems: "center",
              fontWeight: 700,
              fontSize: 14,
              color: "#fff",
              background: `linear-gradient(135deg, ${GL}, ${GD})`,
            }}
          >
            {initials(p.student_name)}
          </span>
          <div style={{ flex: 1, minWidth: 180 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <b style={{ fontSize: 17, letterSpacing: "-0.01em" }}>{p.student_name}</b>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  padding: "3px 10px",
                  borderRadius: 999,
                  color: G,
                  background: "#eaf5ee",
                  border: `1px solid ${G}26`,
                }}
              >
                Lecture {p.no} finished
              </span>
            </div>
            <div style={{ color: MUTED, fontSize: 13, marginTop: 2 }}>
              {p.course_name} · Teacher: {p.teacher_name || "—"}
              {p.ticked_by.length ? ` · Ticked by ${p.ticked_by.join(", ")}` : ""}
            </div>
          </div>
        </div>

        {/* মাপ */}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Metric
            icon="📋"
            label="Topics"
            value={withIcons(`${marked} ✔${missed ? ` · ${missed} ✘` : ""}`, { size: 16, style: { verticalAlign: "-0.15em" } })}
            ok={missed ? "warn" : true}
          />
          <Metric icon="🕐" label="Class time (student)" value={`${classMin} min`} ok={!!classMin} />
          <Metric icon="🎞" label="Slides played" value={`${p.slides_total_min} min`} ok={!!p.slides_total_min} />
        </div>

        {warnings.length > 0 && (
          <div
            style={{
              display: "grid",
              gap: 4,
              padding: "10px 12px",
              borderRadius: 10,
              background: "#fff6f4",
              border: "1px solid #f3c7bd",
              color: RED,
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            {warnings.map((w) => (
              <div key={w}>
                <Ico e="⚠️" /> {w}
              </div>
            ))}
          </div>
        )}

        {/* বিস্তারিত */}
        <details>
          <summary style={{ color: G, fontWeight: 600, fontSize: 14, display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span className="apv-chev">›</span> Details
          </summary>
          <div style={{ display: "grid", gap: 12, marginTop: 10 }}>
            <div style={{ fontSize: 13.5 }}>
              <b>Ticked on:</b>{" "}
              {p.days.length
                ? p.days.map((d) => (
                    <span
                      key={d}
                      style={{
                        display: "inline-block",
                        margin: "2px 4px 2px 0",
                        padding: "2px 9px",
                        borderRadius: 999,
                        background: "#eef3f0",
                        fontSize: 12.5,
                        fontWeight: 600,
                      }}
                    >
                      {fmt(d)}
                    </span>
                  ))
                : "—"}
            </div>
            <div style={{ border: `1px solid ${LINE}`, borderRadius: 12, overflow: "hidden", overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    {["Class date", "Student min", "Teacher min", "Planned min"].map((h) => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {p.classes.length === 0 && (
                    <tr>
                      <td style={{ color: RED }} colSpan={4}>
                        No class attendance found on these days.
                      </td>
                    </tr>
                  )}
                  {p.classes.map((c, i) => (
                    <tr key={i}>
                      <td>{fmt(c.date)}</td>
                      <td>{c.student_min}</td>
                      <td>{c.teacher_min ?? "—"}</td>
                      <td>{c.planned_min ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ border: `1px solid ${LINE}`, borderRadius: 12, overflow: "hidden" }}>
              <table>
                <thead>
                  <tr>
                    {["Slide part", "Minutes"].map((h) => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {p.slides.length === 0 && (
                    <tr>
                      <td style={{ color: RED }} colSpan={2}>
                        No slides were played for this student.
                      </td>
                    </tr>
                  )}
                  {p.slides.map((s, i) => (
                    <tr key={i}>
                      <td>{s.part}</td>
                      <td>{s.minutes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display: "grid", gap: 6 }}>
              {p.topics.map((t, i) => {
                const ok = t.covered === "covered";
                return (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
                    <span
                      style={{
                        width: 20,
                        height: 20,
                        borderRadius: "50%",
                        flexShrink: 0,
                        display: "grid",
                        placeItems: "center",
                        background: ok ? G : RED,
                        color: "#fff",
                      }}
                    >
                      <Ico e={ok ? "✔" : "✘"} size={12} style={{ verticalAlign: 0 }} />
                    </span>
                    {t.text}
                  </div>
                );
              })}
            </div>
          </div>
        </details>
      </div>

      {/* অনুমোদন — কার্ডের ভেতরেই নিশ্চিতকরণ */}
      <div
        style={{
          padding: "12px 18px",
          borderTop: `1px solid ${LINE}`,
          background: confirm ? "#f1faf4" : "#fafcfb",
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {!confirm ? (
          <button disabled={busy} onClick={() => setConfirm(true)} style={btn("primary")}>
            <Ico e="✅" /> Approve — open Lecture {p.no + 1}
          </button>
        ) : (
          <>
            <span style={{ fontSize: 13.5, fontWeight: 600, color: GD, flex: "1 1 240px" }}>
              Open Lecture {p.no + 1} for {p.student_name} only?
            </span>
            <button
              disabled={busy}
              onClick={async () => {
                await onApprove(p);
                setConfirm(false);
              }}
              style={{ ...btn("primary"), opacity: busy ? 0.6 : 1 }}
            >
              {busy ? "Approving…" : "Yes, approve"}
            </button>
            <button onClick={() => setConfirm(false)} style={btn("ghost")}>
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// এডমিন নিজে বাছাই করে খোলেন — দুই রকম (পরিচালকের নির্দেশ, ২০২৬-১১-২৫):
//  • একসাথে অনেক: কোর্স → শিক্ষার্থী বা কোর্সের সবাই → কয়টি (যে সংখ্যা ইচ্ছা)। যে যেখানে আছে সেখান থেকে পরের অতগুলো খোলে।
//  • একটি লেকচার: কোর্স → শিক্ষার্থী → লেকচার নম্বর।
const ALL_LEFT = 500; // "All" — কোর্সের বাকি সব লেকচার (সার্ভার শেষ লেকচারে থামে)
function ManualUnlock({ courses, onOne, onMany }) {
  const [mode, setMode] = useState("many");
  const [course, setCourse] = useState(courses?.[0]?.id || "");
  const [students, setStudents] = useState([]);
  const [student, setStudent] = useState("all");
  const [no, setNo] = useState(2);
  const [count, setCount] = useState(10);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  // কোর্সের তালিকা পরে এলে প্রথমটি বাছাই
  useEffect(() => {
    if (!course && courses?.length) setCourse(courses[0].id);
  }, [courses]);
  useEffect(() => {
    if (!course) return;
    api
      .courseStudents(course)
      .then((r) => {
        const rows = r || [];
        setStudents(rows);
        setStudent((cur) =>
          cur === "all" || !rows.some((x) => String(x.id) === String(cur)) ? (mode === "many" ? "all" : rows[0]?.id || "") : cur,
        );
      })
      .catch(() => setStudents([]));
  }, [course]);
  const st = students.find((x) => String(x.id) === String(student));
  const all = student === "all";
  const n = Number(count);
  const howMany = n >= ALL_LEFT ? "every remaining lecture" : `the next ${n} ${n === 1 ? "lecture" : "lectures"}`;
  const who = all ? `all ${students.length} ${students.length === 1 ? "student" : "students"} of this course` : st?.name;
  const change = (f) => (e) => {
    f(e.target.value);
    setConfirm(false);
    setErr("");
  };
  const pickMode = (m) => {
    setMode(m);
    setConfirm(false);
    setErr("");
    if (m === "one" && all) setStudent(students[0]?.id || "");
  };
  const ask = () => {
    if (mode === "many") {
      if (!all && !st) return setErr("Please choose a student.");
      if (all && !students.length) return setErr("This course has no students.");
      if (!(Number.isInteger(n) && n >= 1)) return setErr("How many lectures? Write a number — 1 or more.");
    } else if (!st || !(Number(no) >= 2)) return setErr("Please choose a student and a lecture (2 or more).");
    setErr("");
    setConfirm(true);
  };
  const go = async () => {
    setBusy(true);
    if (mode === "many") await onMany(course, all ? "all" : st.id, Math.min(n, ALL_LEFT), all ? null : st.name);
    else await onOne(course, st.id, Number(no) - 1, `✅ Lecture ${no} is now open for ${st.name} (only).`);
    setBusy(false);
    setConfirm(false);
  };
  const lbl = { fontSize: 12, fontWeight: 600, color: "#475569", display: "block", marginBottom: 5 };
  return (
    <details style={{ ...card, padding: "14px 18px" }}>
      <summary style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span
          style={{ width: 34, height: 34, borderRadius: 10, background: "#e9f3ed", color: G, display: "grid", placeItems: "center" }}
        >
          <Ico e="🔑" size={17} style={{ verticalAlign: 0 }} />
        </span>
        <span style={{ flex: 1 }}>
          <b style={{ fontSize: 15 }}>Unlock lectures by hand</b>
          <span style={{ display: "block", fontSize: 12.5, color: MUTED }}>
            Open many lectures at once — for one student or a whole course — or a single lecture.
          </span>
        </span>
        <span className="apv-chev" style={{ color: MUTED, fontSize: 20 }}>›</span>
      </summary>

      <div className="apv-seg" role="tablist" aria-label="Unlock mode" style={{ marginTop: 14 }}>
        {[
          ["many", "Many at once"],
          ["one", "One lecture"],
        ].map(([k, l]) => (
          <button key={k} role="tab" aria-selected={mode === k} className={mode === k ? "on" : ""} onClick={() => pickMode(k)}>
            {l}
          </button>
        ))}
      </div>

      <div className="apv-unlock" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end", marginTop: 12 }}>
        <label>
          <span style={lbl}>Course</span>
          <select value={course} onChange={change(setCourse)}>
            {(courses || []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span style={lbl}>Student</span>
          <select value={student} onChange={change(setStudent)} style={{ minWidth: 200 }}>
            {mode === "many" && <option value="all">All students ({students.length})</option>}
            {students.map((x) => (
              <option key={x.id} value={x.id}>
                {x.name}
              </option>
            ))}
          </select>
        </label>
        {mode === "many" ? (
          <label>
            <span style={lbl}>How many lectures</span>
            <input
              type="number"
              min="1"
              inputMode="numeric"
              value={n >= ALL_LEFT ? "" : count}
              placeholder={n >= ALL_LEFT ? "All" : ""}
              onChange={change(setCount)}
              style={{ width: 96 }}
            />
          </label>
        ) : (
          <label>
            <span style={lbl}>Lecture</span>
            <input type="number" min="2" inputMode="numeric" value={no} onChange={change(setNo)} style={{ width: 96 }} />
          </label>
        )}
        {mode === "many" && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingBottom: 4 }}>
            {[5, 10, 20, ALL_LEFT].map((k) => (
              <button
                key={k}
                className={"apv-chip" + (n === k ? " on" : "")}
                onClick={() => {
                  setCount(k);
                  setConfirm(false);
                  setErr("");
                }}
              >
                {k === ALL_LEFT ? "All" : k}
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ fontSize: 12.5, color: MUTED, marginTop: 10, lineHeight: 1.5 }}>
        {mode === "many"
          ? "Each student starts from where they are now — already open lectures are skipped, and nothing opens past the course's last lecture."
          : "Opens only this lecture, for this one student."}{" "}
        This matters only while “Lectures unlock only after approval” is on in Settings — when it is off, every lecture is open anyway.
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginTop: 12 }}>
        {!confirm ? (
          <button onClick={ask} style={btn("primary")}>
            <Ico e="🔓" /> Unlock
          </button>
        ) : (
          <>
            <button onClick={go} disabled={busy} style={{ ...btn("primary"), opacity: busy ? 0.6 : 1 }}>
              {busy ? "Unlocking…" : mode === "many" ? `Yes, unlock ${howMany} for ${who}` : `Yes, unlock Lecture ${no} for ${st?.name}`}
            </button>
            <button onClick={() => setConfirm(false)} disabled={busy} style={btn("ghost")}>
              Cancel
            </button>
          </>
        )}
      </div>
      {err && <div style={{ color: RED, fontSize: 13, marginTop: 8 }}>{err}</div>}
    </details>
  );
}

export default function ApprovalsView({ courses }) {
  const [data, setData] = useState(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const load = async () => {
    try { setData(await approvalsApi.list()); } catch (e) { setMsg("Could not load — " + (e?.data?.error || e?.message || "")); }
  };
  useEffect(() => { load(); }, []);
  const approve = async (p) => {
    setBusy(true);
    try { setData(await approvalsApi.approve(p.course, p.student, p.no)); setMsg(`✅ Lecture ${p.no + 1} is now open for ${p.student_name}.`); }
    catch (e) { setMsg("Could not approve — " + (e?.data?.error || e?.message || "")); }
    setBusy(false);
  };
  const ok = msg.startsWith("✅");
  const pending = data?.pending || [];
  return (
    <div className="apv" style={{ display: "grid", gap: 16, maxWidth: 980 }}>
      <style>{CSS}</style>
      <div>
        <h2 style={{ margin: 0, fontSize: 21, fontWeight: 700, letterSpacing: "-0.02em", color: TEXT, display: "flex", alignItems: "center", gap: 8 }}>
          <Ico e="✅" style={{ color: GL }} /> Lecture Approvals
          {data && (
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
                background: pending.length ? "#fdf6e7" : "#e9f3ed",
                color: pending.length ? "#a16207" : G,
              }}
            >
              {pending.length}
            </span>
          )}
        </h2>
        <div style={{ color: MUTED, fontSize: 13.5, marginTop: 4, lineHeight: 1.5 }}>
          Everything here is per student: approving opens the next lecture for that one student only. When a teacher ticks every
          topic of a lecture for a student, it waits here — check the class time and slide time, then approve.
        </div>
      </div>

      {msg && (
        <div
          role="status"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "11px 14px",
            borderRadius: 12,
            background: ok ? "#f1faf4" : "#fff6f4",
            border: `1px solid ${ok ? "#bfe1cb" : "#f3c7bd"}`,
            color: ok ? G : RED,
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          <span style={{ flex: 1 }}>{withIcons(msg)}</span>
          <button onClick={() => setMsg("")} aria-label="Dismiss" style={{ border: "none", background: "transparent", cursor: "pointer", color: "inherit" }}>
            <Ico e="✕" />
          </button>
        </div>
      )}

      <ManualUnlock
        courses={courses}
        onOne={async (c, st, prev, okMsg) => {
          try { setData(await approvalsApi.approve(c, st, prev)); setMsg(okMsg); } catch (e) { setMsg("Could not unlock — " + (e?.data?.error || e?.message || "")); }
        }}
        onMany={async (c, st, n, name) => {
          try {
            const r = await approvalsApi.unlockMany(c, st, n);
            setData(r);
            const rows = r?.unlocked || [];
            const got = rows.filter((x) => x.opened > 0);
            const range = (x) => (x.from === x.to ? `Lecture ${x.from}` : `Lectures ${x.from}–${x.to}`);
            if (name)
              setMsg(
                got.length
                  ? `✅ ${range(got[0])} ${got[0].from === got[0].to ? "is" : "are"} now open for ${name}.`
                  : `✅ Nothing to unlock — ${name} already has every lecture open (up to Lecture ${r.last_lecture}).`,
              );
            else
              setMsg(
                `✅ Unlocked for ${got.length} of ${rows.length} ${rows.length === 1 ? "student" : "students"}, each from where they were` +
                  (got.length ? ` (${got.slice(0, 4).map((x) => `${x.student_name}: ${range(x)}`).join(" · ")}${got.length > 4 ? " · …" : ""})` : "") +
                  "." +
                  (rows.length - got.length ? ` ${rows.length - got.length} already had every lecture open.` : ""),
              );
          } catch (e) {
            setMsg("Could not unlock — " + (e?.data?.error || e?.message || ""));
          }
        }}
      />

      {!data && <div style={{ ...card, padding: 24, textAlign: "center", color: MUTED }}>Loading…</div>}
      {data && pending.length === 0 && (
        <div style={{ ...card, padding: "28px 18px", textAlign: "center" }}>
          <div
            style={{ width: 52, height: 52, margin: "0 auto", borderRadius: 16, background: "#eaf5ee", color: G, display: "grid", placeItems: "center" }}
          >
            <Ico e="✅" size={24} style={{ verticalAlign: 0 }} />
          </div>
          <div style={{ fontWeight: 700, fontSize: 15.5, marginTop: 10 }}>Nothing is waiting for approval</div>
          <div style={{ fontSize: 13, color: MUTED, marginTop: 2 }}>Finished lectures appear here once a teacher ticks every topic.</div>
        </div>
      )}
      {pending.map((p) => (
        <Card key={`${p.course}-${p.student}-${p.no}`} p={p} onApprove={approve} busy={busy} />
      ))}

      {data?.recent?.length > 0 && (
        <details style={{ ...card, padding: "14px 18px" }}>
          <summary style={{ color: G, fontWeight: 600, fontSize: 14.5, display: "flex", alignItems: "center", gap: 8 }}>
            <span className="apv-chev">›</span> Recently approved
            <span style={{ fontSize: 12, color: MUTED, fontWeight: 600 }}>({data.recent.length})</span>
          </summary>
          <div style={{ border: `1px solid ${LINE}`, borderRadius: 12, overflow: "hidden", overflowX: "auto", marginTop: 12 }}>
            <table>
              <thead>
                <tr>
                  {["Date", "Student", "Course", "Lecture", "By"].map((h) => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.recent.map((r, i) => (
                  <tr key={i}>
                    <td style={{ whiteSpace: "nowrap" }}>{fmt(r.at)}</td>
                    <td>{r.student_name}</td>
                    <td>{r.course_name}</td>
                    <td>Lecture {r.no}</td>
                    <td>{r.by || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}
