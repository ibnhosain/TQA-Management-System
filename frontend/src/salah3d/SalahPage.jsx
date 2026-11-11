/* /salah-learn — নামাজ শিক্ষার আলাদা পেজ। অ্যাপের মেনু থেকে আসে; ওয়েবসাইট বা অন্য কোথাও এর লিংক নেই।
   লগইন না থাকলে বা ট্রায়াল হলে কিছুই লোড হয় না (মডেল ফাইলও সার্ভার টোকেন ছাড়া দেয় না)। */
import { useEffect, useState } from "react";
import { getMe, hasToken } from "../api";
import SalahLearn from "./SalahLearn.jsx";

const ALLOWED = ["director", "admin", "teacher", "student"];

export default function SalahPage() {
  const [state, setState] = useState(hasToken() ? "checking" : "out");
  useEffect(() => {
    document.title = "Learn Salah — Tarbiyatul Quran Academy";
    const m = document.createElement("meta"); m.name = "robots"; m.content = "noindex, nofollow"; document.head.appendChild(m);
    if (!hasToken()) return;
    getMe().then((u) => setState(ALLOWED.includes(u?.role) ? "ok" : "denied")).catch(() => setState("out"));
  }, []);
  const shell = { minHeight: "100vh", background: "#F4F8F5", fontFamily: "inherit" };
  const bar = { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, padding: "12px 16px", background: "#123F28", color: "#fff" };
  const back = <a href="/" style={{ color: "#F3D58A", textDecoration: "none", fontWeight: 600 }}>← Back to the app</a>;
  if (state !== "ok") {
    const msg = state === "checking" ? ["Checking your login…", "লগইন যাচাই হচ্ছে…"]
      : state === "denied" ? ["This page is for our teachers and admitted students.", "এই পেজ আমাদের শিক্ষক ও ভর্তি হওয়া শিক্ষার্থীদের জন্য।"]
      : ["Please log in to the academy app first.", "আগে একাডেমির অ্যাপে লগইন করুন।"];
    return (
      <div style={shell}>
        <div style={bar}><b>Tarbiyatul Quran Academy</b>{back}</div>
        <div style={{ maxWidth: 520, margin: "80px auto", textAlign: "center", padding: 20 }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#123F28" }}>{msg[0]}</div>
          <div style={{ fontSize: 14, color: "#5B6B62", marginTop: 6 }}>{msg[1]}</div>
        </div>
      </div>
    );
  }
  return (
    <div style={shell}>
      <div style={bar}><b>Tarbiyatul Quran Academy</b>{back}</div>
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "18px 14px 40px" }}><SalahLearn /></div>
    </div>
  );
}
