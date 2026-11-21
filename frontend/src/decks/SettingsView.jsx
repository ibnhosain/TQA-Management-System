/* পরিচালকের Settings পাতা — চালু/বন্ধ বোতাম (শুধু পরিচালক বদলান)। লেকচার খোলা হয় "Lecture Approvals" পাতা থেকে। */
import { useEffect, useState } from "react";
import { settingsApi } from "../api";
import { Ico } from "../icons";

const G = "#1A5C3A", MUTED = "#5B6B62";

function Toggle({ on, disabled, onChange }) {
  return (
    <button onClick={() => !disabled && onChange(!on)} disabled={disabled} aria-pressed={on}
      style={{ width: 58, height: 32, borderRadius: 99, border: "none", cursor: disabled ? "not-allowed" : "pointer", position: "relative",
        background: on ? G : "#C9D4CD", opacity: disabled ? 0.6 : 1, flex: "0 0 auto" }}>
      <span style={{ position: "absolute", top: 4, left: on ? 30 : 4, width: 24, height: 24, borderRadius: "50%", background: "#fff", transition: "left .15s" }} />
    </button>
  );
}

export default function SettingsView({ user }) {
  const isDir = user?.role === "director";
  const [items, setItems] = useState(null);
  const [msg, setMsg] = useState("");
  const load = async () => {
    try { setItems((await settingsApi.get()).items); }
    catch (e) { setMsg("Could not load — " + (e?.data?.error || e?.message || "")); }
  };
  useEffect(() => { load(); }, []);
  const toggle = async (key, on) => {
    try { setItems((await settingsApi.set(key, on)).items); setMsg("✅ Saved"); } catch (e) { setMsg("Could not save — " + (e?.data?.error || e?.message || "")); }
  };

  return (
    <div style={{ display: "grid", gap: 18, maxWidth: 900 }}>
      <h2 style={{ margin: 0 }}><Ico e="⚙" /> Settings</h2>
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

    </div>
  );
}
