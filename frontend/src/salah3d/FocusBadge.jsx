/* ডান উপরের কোণে: এই ধাপে কোন অঙ্গে মনোযোগ — কাছের ছবি, সোনালি গোল দাগ দেওয়া। চাপলে বড় হয়ে খোলে।
   ছবি সার্ভার থেকে টোকেন দিয়ে আসে (খোলা লিংক নেই)। */
import { useEffect, useState } from "react";
import { fetchBinary } from "../api";
import { ASSET_VERSION } from "./version";

const cache = {};

export default function FocusBadge({ stepKey, label }) {
  const [url, setUrl] = useState(null);
  const [big, setBig] = useState(false);
  useEffect(() => {
    let alive = true;
    setUrl(null);
    if (!cache[stepKey]) cache[stepKey] = fetchBinary(`/salah3d/focus/${stepKey}/?v=${ASSET_VERSION}`)
      .then((b) => URL.createObjectURL(new Blob([b], { type: "image/jpeg" }))).catch(() => null);
    cache[stepKey].then((u) => { if (alive) setUrl(u); });
    return () => { alive = false; };
  }, [stepKey]);
  if (!url) return null;
  return (
    <>
      <button onClick={() => setBig(true)} title="Tap to enlarge"
        style={{ position: "absolute", top: 10, right: 10, width: "clamp(96px, 22%, 170px)", aspectRatio: "1", padding: 0, border: "3px solid #fff",
          borderRadius: "50%", overflow: "hidden", cursor: "zoom-in", boxShadow: "0 4px 16px rgba(0,0,0,.28)", background: "#fff", zIndex: 3 }}>
        <img src={url} alt={label} draggable={false} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
      </button>
      {big && (
        <div onClick={() => setBig(false)} style={{ position: "fixed", inset: 0, background: "rgba(10,20,15,.82)", zIndex: 1000,
          display: "grid", placeItems: "center", padding: 16, cursor: "zoom-out" }}>
          <div style={{ textAlign: "center" }}>
            <img src={url} alt={label} draggable={false} style={{ maxWidth: "min(92vw, 640px)", maxHeight: "80vh", borderRadius: 16, display: "block" }} />
            <div style={{ color: "#fff", marginTop: 10, fontSize: 18 }}>{label}</div>
            <div style={{ color: "#cfe6d8", fontSize: 13 }}>Tap anywhere to close · যেকোনো জায়গায় চাপলে বন্ধ হবে</div>
          </div>
        </div>
      )}
    </>
  );
}
