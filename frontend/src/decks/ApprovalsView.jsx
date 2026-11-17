/* এডমিন/পরিচালকের "Lecture Approvals" — উস্তাদ যে শিক্ষার্থীর একটা লেকচারের সব টপিক টিক দিয়েছেন, সেগুলো এখানে আসে।
   দেখা যায়: কোন দিন টিক, সেই দিনগুলোর ক্লাসে শিক্ষার্থী ও উস্তাদ কত মিনিট ছিলেন, কোন অংশের স্লাইড কত মিনিট চলেছে।
   Approve দিলে তবেই ওই শিক্ষার্থীর পরের লেকচার খোলে। */
import { useEffect, useState } from "react";
import { api, approvalsApi } from "../api";

const G = "#1A5C3A", GOLD = "#C9962A", MUTED = "#5B6B62", RED = "#b00020";
const fmt = (d) => (d ? new Date(d).toLocaleDateString("en-GB") : "");

function Card({ p, onApprove, busy }) {
  const marked = p.topics.filter((t) => t.covered === "covered").length;
  const missed = p.topics.length - marked;
  const classMin = p.classes.reduce((a, c) => a + (c.student_min || 0), 0);
  const cell = { padding: "4px 8px", borderBottom: "1px solid #EEF3F0", fontSize: 14 };
  return (
    <div style={{ background: "#fff", border: "1px solid #DCE9E0", borderRadius: 14, padding: 14, display: "grid", gap: 10 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
        <b style={{ fontSize: 17 }}>{p.student_name}</b>
        <span style={{ color: G, fontWeight: 700 }}>Lecture {p.no} finished</span>
        <span style={{ color: MUTED, fontSize: 13 }}>{p.course_name} · teacher: {p.teacher_name || "—"}{p.ticked_by.length ? ` · ticked by ${p.ticked_by.join(", ")}` : ""}</span>
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {[["Topics", `${marked} ✔${missed ? ` · ${missed} ✘` : ""}`, missed ? GOLD : G],
          ["Class time (student)", `${classMin} min`, classMin ? G : RED],
          ["Slides played", `${p.slides_total_min} min`, p.slides_total_min ? G : RED]].map(([k, v, c]) => (
          <div key={k} style={{ background: "#F6FAF7", borderRadius: 10, padding: "8px 12px", minWidth: 150 }}>
            <div style={{ fontSize: 12, color: MUTED }}>{k}</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: c }}>{v}</div>
          </div>
        ))}
      </div>
      <details>
        <summary style={{ cursor: "pointer", color: G, fontWeight: 600 }}>Details</summary>
        <div style={{ display: "grid", gap: 10, marginTop: 8 }}>
          <div>
            <b>Ticked on:</b> {p.days.map(fmt).join(", ") || "—"}
          </div>
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead><tr>{["Class date", "Student min", "Teacher min", "Planned min"].map((h) => <th key={h} style={{ ...cell, textAlign: "left", color: MUTED }}>{h}</th>)}</tr></thead>
            <tbody>
              {p.classes.length === 0 && <tr><td style={{ ...cell, color: RED }} colSpan={4}>No class attendance found on these days.</td></tr>}
              {p.classes.map((c, i) => <tr key={i}><td style={cell}>{fmt(c.date)}</td><td style={cell}>{c.student_min}</td><td style={cell}>{c.teacher_min ?? "—"}</td><td style={cell}>{c.planned_min ?? "—"}</td></tr>)}
            </tbody>
          </table>
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead><tr>{["Slide part", "Minutes"].map((h) => <th key={h} style={{ ...cell, textAlign: "left", color: MUTED }}>{h}</th>)}</tr></thead>
            <tbody>
              {p.slides.length === 0 && <tr><td style={{ ...cell, color: RED }} colSpan={2}>No slides were played for this student.</td></tr>}
              {p.slides.map((s, i) => <tr key={i}><td style={cell}>{s.part}</td><td style={cell}>{s.minutes}</td></tr>)}
            </tbody>
          </table>
          <div>{p.topics.map((t, i) => <div key={i} style={{ fontSize: 14 }}>{t.covered === "covered" ? "✔" : "✘"} {t.text}</div>)}</div>
        </div>
      </details>
      <div>
        <button disabled={busy} onClick={() => onApprove(p)}
          style={{ border: "none", background: G, color: "#fff", borderRadius: 10, padding: "10px 18px", fontWeight: 700, cursor: "pointer", font: "inherit" }}>
          ✅ Approve — open Lecture {p.no + 1}
        </button>
      </div>
    </div>
  );
}

// এডমিন নিজে বাছাই করে খোলেন: কোর্স → শিক্ষার্থী → লেকচার। শুধু ওই শিক্ষার্থীর জন্য খোলে, অন্য কারও নয়।
function ManualUnlock({ courses, onDone }) {
  const [course, setCourse] = useState(courses?.[0]?.id || "");
  const [students, setStudents] = useState([]);
  const [student, setStudent] = useState("");
  const [no, setNo] = useState(2);
  useEffect(() => {
    if (!course) return;
    api.courseStudents(course).then((r) => { setStudents(r || []); setStudent(r?.[0]?.id || ""); }).catch(() => setStudents([]));
  }, [course]);
  const box = { border: "1px solid #CFE0D5", borderRadius: 10, padding: "8px 10px", font: "inherit" };
  const go = async () => {
    const st = students.find((x) => String(x.id) === String(student));
    if (!st || !(Number(no) >= 2)) return alert("Please choose a student and a lecture (2 or more).");
    if (!window.confirm(`Unlock Lecture ${no} for ${st.name} only?`)) return;
    onDone(course, st.id, Number(no) - 1, `✅ Lecture ${no} is now open for ${st.name} (only).`);
  };
  return (
    <div style={{ background: "#fff", border: "1px solid #DCE9E0", borderRadius: 14, padding: 14, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
      <b style={{ width: "100%" }}>Unlock a lecture for one student</b>
      <select value={course} onChange={(e) => setCourse(e.target.value)} style={box}>{(courses || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
      <select value={student} onChange={(e) => setStudent(e.target.value)} style={{ ...box, minWidth: 180 }}>{students.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
      <span>Lecture</span><input type="number" min="2" value={no} onChange={(e) => setNo(e.target.value)} style={{ ...box, width: 80 }} />
      <button onClick={go} style={{ border: "none", background: G, color: "#fff", borderRadius: 10, padding: "9px 16px", fontWeight: 700, cursor: "pointer", font: "inherit" }}>Unlock</button>
      <span style={{ fontSize: 12, color: MUTED, width: "100%" }}>Usually you approve from the list below after checking the times. Use this only when you need to open a lecture by hand.</span>
    </div>
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
    if (!window.confirm(`Approve Lecture ${p.no} for ${p.student_name}? Lecture ${p.no + 1} will open for this student.`)) return;
    setBusy(true);
    try { setData(await approvalsApi.approve(p.course, p.student, p.no)); setMsg(`✅ Lecture ${p.no + 1} is now open for ${p.student_name}.`); }
    catch (e) { setMsg("Could not approve — " + (e?.data?.error || e?.message || "")); }
    setBusy(false);
  };
  return (
    <div style={{ display: "grid", gap: 14, maxWidth: 980 }}>
      <h2 style={{ margin: 0 }}>✅ Lecture Approvals</h2>
      <div style={{ color: MUTED }}>Everything here is per student: approving opens the next lecture for that one student only, not for anyone else. When a teacher ticks every topic of a lecture for a student, it waits here — check the class time and slide time, then approve.</div>
      {msg && <div style={{ color: msg.startsWith("✅") ? G : RED }}>{msg}</div>}
      <ManualUnlock courses={courses} onDone={async (c, st, prev, ok) => {
        try { setData(await approvalsApi.approve(c, st, prev)); setMsg(ok); } catch (e) { setMsg("Could not unlock — " + (e?.data?.error || e?.message || "")); }
      }} />
      {!data && <div>Loading…</div>}
      {data && data.pending.length === 0 && <div style={{ color: MUTED }}>Nothing is waiting for approval.</div>}
      {(data?.pending || []).map((p) => <Card key={`${p.course}-${p.student}-${p.no}`} p={p} onApprove={approve} busy={busy} />)}
      {data?.recent?.length > 0 && (
        <details>
          <summary style={{ cursor: "pointer", color: G, fontWeight: 600 }}>Recently approved</summary>
          <div style={{ display: "grid", gap: 4, marginTop: 8 }}>
            {data.recent.map((r, i) => <div key={i} style={{ fontSize: 14 }}>{fmt(r.at)} · {r.student_name} · {r.course_name} · Lecture {r.no} · by {r.by || "—"}</div>)}
          </div>
        </details>
      )}
    </div>
  );
}
