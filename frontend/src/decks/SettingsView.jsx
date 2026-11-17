/* পরিচালকের Settings পাতা — চালু/বন্ধ বোতাম (শুধু পরিচালক বদলান) আর কোর্সপ্রতি লেকচার অনুমোদন (পরিচালক ও এডমিন)।
   লেকচার ক্রমে পড়ানো হয়, তাই "Lecture 1 থেকে কোন পর্যন্ত খোলা" — এক ক্লিকে "31 থেকে 40 খোলো" বা "+5 / +10"। */
import { useEffect, useState } from "react";
import { settingsApi } from "../api";

const G = "#1A5C3A", GOLD = "#C9962A", MUTED = "#5B6B62";

function Toggle({ on, disabled, onChange }) {
  return (
    <button onClick={() => !disabled && onChange(!on)} disabled={disabled} aria-pressed={on}
      style={{ width: 58, height: 32, borderRadius: 99, border: "none", cursor: disabled ? "not-allowed" : "pointer", position: "relative",
        background: on ? G : "#C9D4CD", opacity: disabled ? 0.6 : 1, flex: "0 0 auto" }}>
      <span style={{ position: "absolute", top: 4, left: on ? 30 : 4, width: 24, height: 24, borderRadius: "50%", background: "#fff", transition: "left .15s" }} />
    </button>
  );
}

function CourseRow({ c, onSave }) {
  const [from, setFrom] = useState(c.released + 1);
  const [to, setTo] = useState(Math.max(c.released + 10, c.released + 1));
  const [upto, setUpto] = useState(c.released);
  useEffect(() => { setFrom(c.released + 1); setTo(c.released + 10); setUpto(c.released); }, [c.released]);
  const total = Math.max(c.plan_lectures, c.slides_up_to);
  const box = { border: "1px solid #CFE0D5", borderRadius: 10, padding: "7px 8px", width: 70, font: "inherit" };
  const b = { border: "1px solid #CFE0D5", background: "#fff", color: "#123F28", borderRadius: 10, padding: "8px 12px", cursor: "pointer", font: "inherit" };
  const go = { ...b, background: G, color: "#fff", borderColor: G, fontWeight: 700 };
  const openRange = () => {
    const a = Number(from), z = Number(to);
    if (!(z >= a && a >= 1)) return alert("Please give a correct range.");
    if (a > c.released + 1 && !window.confirm(`Lectures are opened in order. Lectures ${c.released + 1}–${a - 1} will open too. Continue?`)) return;
    onSave(c.id, Math.max(c.released, z));
  };
  return (
    <div style={{ background: "#fff", border: "1px solid #DCE9E0", borderRadius: 14, padding: 14, display: "grid", gap: 10 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
        <b style={{ fontSize: 17 }}>{c.name}</b>
        <span style={{ color: G, fontWeight: 700 }}>{c.released ? `Open: Lecture 1 – ${c.released}` : "No lectures open"}</span>
        {total > 0 && <span style={{ color: MUTED, fontSize: 13 }}>(plan: {c.plan_lectures} lectures · slides ready up to {c.slides_up_to})</span>}
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <span>Open from</span><input type="number" min="1" value={from} onChange={(e) => setFrom(e.target.value)} style={box} />
        <span>to</span><input type="number" min="1" value={to} onChange={(e) => setTo(e.target.value)} style={box} />
        <button style={go} onClick={openRange}>Open</button>
        <button style={b} onClick={() => onSave(c.id, c.released + 5)}>+5</button>
        <button style={b} onClick={() => onSave(c.id, c.released + 10)}>+10</button>
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", fontSize: 14, color: MUTED }}>
        <span>Or set open up to</span><input type="number" min="0" value={upto} onChange={(e) => setUpto(e.target.value)} style={box} />
        <button style={b} onClick={() => onSave(c.id, Math.max(0, Number(upto) || 0))}>Save</button>
        <span>(a smaller number closes the later lectures again)</span>
      </div>
    </div>
  );
}

export default function SettingsView({ user }) {
  const isDir = user?.role === "director";
  const [items, setItems] = useState(null);
  const [courses, setCourses] = useState([]);
  const [msg, setMsg] = useState("");
  const load = async () => {
    try { setItems((await settingsApi.get()).items); setCourses(await settingsApi.lectures()); }
    catch (e) { setMsg("Could not load — " + (e?.data?.error || e?.message || "")); }
  };
  useEffect(() => { load(); }, []);
  const toggle = async (key, on) => {
    try { setItems((await settingsApi.set(key, on)).items); setMsg("✅ Saved"); } catch (e) { setMsg("Could not save — " + (e?.data?.error || e?.message || "")); }
  };
  const release = async (course, n) => {
    try { setCourses(await settingsApi.release(course, n)); setMsg("✅ Saved"); } catch (e) { setMsg("Could not save — " + (e?.data?.error || e?.message || "")); }
  };
  const approvalOn = items?.find((x) => x.key === "lecture_approval")?.enabled;

  return (
    <div style={{ display: "grid", gap: 18, maxWidth: 900 }}>
      <h2 style={{ margin: 0 }}>⚙️ Settings</h2>
      {msg && <div style={{ color: msg.startsWith("✅") ? G : "#b00020" }}>{msg}</div>}

      <section style={{ display: "grid", gap: 10 }}>
        <h3 style={{ margin: 0, color: G }}>On / Off</h3>
        {!isDir && <div style={{ color: MUTED, fontSize: 13 }}>Only the director can change these.</div>}
        {!items && <div>Loading…</div>}
        {(items || []).map((it) => (
          <div key={it.key} style={{ display: "flex", gap: 14, alignItems: "center", background: "#fff", border: "1px solid #DCE9E0", borderRadius: 14, padding: "12px 14px" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700 }}>{it.label}</div>
              <div style={{ fontSize: 13, color: MUTED }}>{it.help}</div>
            </div>
            <span style={{ fontWeight: 700, color: it.enabled ? G : MUTED, width: 34 }}>{it.enabled ? "On" : "Off"}</span>
            <Toggle on={it.enabled} disabled={!isDir} onChange={(v) => toggle(it.key, v)} />
          </div>
        ))}
      </section>

      <section style={{ display: "grid", gap: 10 }}>
        <h3 style={{ margin: 0, color: G }}>Lecture approval</h3>
        <div style={{ fontSize: 13, color: approvalOn === false ? GOLD : MUTED }}>
          {approvalOn === false ? "Lecture approval is Off — teachers and students can see every lecture now. The numbers below are kept for when you turn it on."
            : "Teachers and students see only the open lectures. Directors and admins always see all."}
        </div>
        {courses.map((c) => <CourseRow key={c.id} c={c} onSave={release} />)}
      </section>
    </div>
  );
}
