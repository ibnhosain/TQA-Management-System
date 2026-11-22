/* পরিচালকের Settings পাতা — চালু/বন্ধ বোতাম (শুধু পরিচালক বদলান)। লেকচার খোলা হয় "Lecture Approvals" পাতা থেকে।
   ২০২৬-১১-২২: মূল অ্যাপের প্রিমিয়াম চেহারায় (রং মূল অ্যাপের C-এর সাথে মেলানো)। প্রতিটি বোতাম
   বদলানোর সময় নিজের "Saving…" অবস্থা; "Saved" বার্তা নিজে থেকে মিলিয়ে যায়।
   ⚠️ মূল ফাইল থেকে import নেই — এই পাতা সেখান থেকেই lazy-load হয় (বৃত্তাকার নির্ভরতা এড়াতে)। */
import { useEffect, useRef, useState } from "react";
import { settingsApi } from "../api";
import { Ico, withIcons } from "../icons";

const G = "#1a5c3a", GL = "#2a7a50", MUTED = "#64748b", TEXT = "#14221b", LINE = "#e3e9e5", RED = "#c0392b";
// প্রতিটি বোতামের পাশের ছবি — অচেনা নতুন কী হলে সাধারণ ⚙
const ICON = { lecture_lock: "🔒", student_slides: "🎞", homework_notes: "📝", auto_cover_panel: "✅" };

function Toggle({ on, disabled, busy, onChange, label }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={() => !disabled && !busy && onChange(!on)}
      disabled={disabled}
      style={{
        width: 52,
        height: 30,
        borderRadius: 99,
        border: "none",
        cursor: disabled ? "not-allowed" : busy ? "wait" : "pointer",
        position: "relative",
        flex: "0 0 auto",
        background: on ? `linear-gradient(180deg, ${GL}, ${G})` : "#cfd9d3",
        boxShadow: on ? "inset 0 1px 2px rgba(0,0,0,.15)" : "inset 0 1px 2px rgba(0,0,0,.1)",
        opacity: disabled ? 0.55 : busy ? 0.75 : 1,
        transition: "background .2s",
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 3,
          left: on ? 25 : 3,
          width: 24,
          height: 24,
          borderRadius: "50%",
          background: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,.25)",
          transition: "left .2s cubic-bezier(.3,1.3,.5,1)",
        }}
      />
    </button>
  );
}

export default function SettingsView({ user }) {
  const isDir = user?.role === "director";
  const [items, setItems] = useState(null);
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(null); // যে কী এখন সংরক্ষণ হচ্ছে
  const timer = useRef(null);
  const say = (m) => {
    setMsg(m);
    clearTimeout(timer.current);
    if (m.startsWith("✅")) timer.current = setTimeout(() => setMsg(""), 2500);
  };
  useEffect(() => () => clearTimeout(timer.current), []);
  const load = async () => {
    try { setItems((await settingsApi.get()).items); }
    catch (e) { say("Could not load — " + (e?.data?.error || e?.message || "")); }
  };
  useEffect(() => { load(); }, []);
  const toggle = async (key, on) => {
    setSaving(key);
    try { setItems((await settingsApi.set(key, on)).items); say("✅ Saved"); } catch (e) { say("Could not save — " + (e?.data?.error || e?.message || "")); }
    setSaving(null);
  };
  const ok = msg.startsWith("✅");

  return (
    <div style={{ display: "grid", gap: 16, maxWidth: 900 }}>
      {/* ফোনে সুইচটাই অবস্থা বোঝায় — On/Off চিপ লুকিয়ে লেখার জায়গা বাড়াই */}
      <style>{`@media(max-width:560px){.st-pill{display:none}}`}</style>
      <div>
        <h2 style={{ margin: 0, fontSize: 21, fontWeight: 700, letterSpacing: "-0.02em", color: TEXT, display: "flex", alignItems: "center", gap: 8 }}>
          <Ico e="⚙" style={{ color: GL }} /> Settings
        </h2>
        <div style={{ color: MUTED, fontSize: 13.5, marginTop: 4 }}>
          Switch features on or off for the whole academy. Lectures are opened from <b>Lecture Approvals</b>.
        </div>
      </div>

      {!isDir && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "10px 14px",
            borderRadius: 12,
            background: "#fdf6e7",
            border: "1px solid #f1dfb5",
            color: "#a16207",
            fontSize: 13.5,
            fontWeight: 500,
          }}
        >
          <Ico e="🔒" /> Only the director can change these settings.
        </div>
      )}

      {msg && (
        <div
          role="status"
          style={{
            padding: "10px 14px",
            borderRadius: 12,
            background: ok ? "#f1faf4" : "#fff6f4",
            border: `1px solid ${ok ? "#bfe1cb" : "#f3c7bd"}`,
            color: ok ? G : RED,
            fontWeight: 600,
            fontSize: 14,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Ico e={ok ? "✅" : "⚠️"} /> {msg.replace(/^✅\s*/, "")}
        </div>
      )}

      <section
        style={{
          background: "#fff",
          border: `1px solid ${LINE}`,
          borderRadius: 16,
          boxShadow: "0 1px 2px rgba(16,34,24,.04), 0 6px 18px rgba(16,34,24,.05)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "12px 18px",
            borderBottom: `1px solid ${LINE}`,
            background: "#f6f9f7",
            fontSize: 11.5,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "#475569",
          }}
        >
          Features
        </div>
        {!items && <div style={{ padding: 22, textAlign: "center", color: MUTED }}>Loading…</div>}
        {(items || []).map((it, i) => (
          <div
            key={it.key}
            style={{
              display: "flex",
              gap: 14,
              alignItems: "center",
              padding: "16px 18px",
              borderTop: i ? `1px solid ${LINE}` : "none",
            }}
          >
            <span
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                flexShrink: 0,
                display: "grid",
                placeItems: "center",
                background: it.enabled ? "#e9f3ed" : "#f1f4f2",
                color: it.enabled ? G : "#94a3b8",
              }}
            >
              <Ico e={ICON[it.key] || "⚙"} size={19} style={{ verticalAlign: 0 }} />
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: 15, color: TEXT }}>{it.label}</div>
              <div style={{ fontSize: 13, color: MUTED, marginTop: 2, lineHeight: 1.5 }}>{withIcons(it.help)}</div>
            </div>
            <span
              className="st-pill"
              style={{
                fontSize: 12,
                fontWeight: 700,
                padding: "3px 10px",
                borderRadius: 999,
                color: it.enabled ? G : MUTED,
                background: it.enabled ? "#eaf5ee" : "#f1f4f2",
                minWidth: 44,
                textAlign: "center",
              }}
            >
              {saving === it.key ? "…" : it.enabled ? "On" : "Off"}
            </span>
            <Toggle
              on={it.enabled}
              disabled={!isDir}
              busy={saving === it.key}
              label={it.label}
              onChange={(v) => toggle(it.key, v)}
            />
          </div>
        ))}
      </section>
      <div style={{ fontSize: 12.5, color: MUTED }}>
        <Ico e="💡" /> Each switch is saved as soon as you change it.
      </div>
    </div>
  );
}
