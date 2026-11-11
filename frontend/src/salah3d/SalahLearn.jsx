/* নামাজ শিক্ষা — বাস্তব শিশুর 3D মডেল অজু ও নামাজের প্রতিটি ধাপ করে দেখায় (চলতে থাকে, থামানো/চালানো যায়)।
   মডেল (.glb) আসে সার্ভার থেকে, কেবল লগইন করা ব্যবহারকারীর টোকেন দিয়ে — খোলা কোনো লিংক নেই।
   লেখা নির্বাচন, কপি, কাট, রাইট-ক্লিক ও টেনে নেওয়া বন্ধ। */
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { fetchBinary } from "../api";
import { STEPS } from "./steps";
import { makeScene, setProps } from "./scene";

const GROUPS = [["wudu", "Wudu", "অজু"], ["boy", "Salah — Boys", "নামাজ — ছেলে"], ["girl", "Salah — Girls", "নামাজ — মেয়ে"]];
const VIEWS = { front: [0.35, 0.25, 1], side: [-1, 0.2, 0.1], back: [-0.35, 0.3, -1] };
const block = (e) => e.preventDefault();

export default function SalahLearn() {
  const box = useRef(null);
  const eng = useRef(null);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [status, setStatus] = useState("Loading…");
  const st = STEPS[idx];

  // 3D ইঞ্জিন একবারই তৈরি
  useEffect(() => {
    const el = box.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    el.appendChild(renderer.domElement);
    const cam = new THREE.PerspectiveCamera(30, 1, 0.05, 30);
    const ctl = new OrbitControls(cam, renderer.domElement);
    Object.assign(ctl, { enableDamping: true, enablePan: false, minDistance: 0.6, maxDistance: 5, maxPolarAngle: Math.PI * 0.49 });
    const { scene, props } = makeScene();
    const clock = new THREE.Clock();
    const e = { renderer, cam, ctl, scene, props, models: {}, mixer: null, action: null, center: new THREE.Vector3(0, 0.5, 0.1), radius: 0.75 };
    eng.current = e;
    const size = () => { const w = el.clientWidth, h = el.clientHeight; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); };
    const ro = new ResizeObserver(size); ro.observe(el); size();
    let raf;
    const loop = () => { raf = requestAnimationFrame(loop); const dt = clock.getDelta(); if (e.mixer) e.mixer.update(dt); ctl.update(); renderer.render(scene, cam); };
    loop();
    return () => { cancelAnimationFrame(raf); ro.disconnect(); renderer.dispose(); el.innerHTML = ""; };
  }, []);

  function view(dir) {
    const e = eng.current; if (!e) return;
    const v = new THREE.Vector3(...VIEWS[dir]).normalize();
    e.cam.position.copy(e.center).add(v.multiplyScalar(e.radius / Math.sin(15 * Math.PI / 180) * 0.95));
    e.ctl.target.copy(e.center); e.ctl.update();
  }

  async function model(kind) {
    const e = eng.current;
    if (!e.models[kind]) {
      e.models[kind] = (async () => {
        const buf = await fetchBinary(`/salah3d/${kind}/`);
        const gltf = await new GLTFLoader().parseAsync(buf, "");
        gltf.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
        return gltf;
      })();
    }
    return e.models[kind];
  }

  // ধাপ বদলালে: ঠিক শিশু, ঠিক আসবাব, ঠিক নড়াচড়া
  useEffect(() => {
    let alive = true;
    (async () => {
      const e = eng.current;
      const kind = st.group === "girl" ? "girl" : "boy";
      try {
        setStatus("Loading…");
        const g = await model(kind);
        if (!alive) return;
        for (const k of Object.keys(e.models)) e.scene.remove((await e.models[k]).scene);
        e.scene.add(g.scene);
        setProps(e.props, st.key);
        const wuduNow = st.key.startsWith("wudu");      // অজুতে টুপি খোলা, পুরো চুল দেখা যায়
        g.scene.traverse((o) => {
          if (o.name.startsWith("kufi") || o.name.startsWith("hair_cap")) o.visible = !wuduNow;
          if (o.name.startsWith("hair_full")) o.visible = wuduNow;
        });
        if (e.mixer?.getRoot() !== g.scene) e.mixer = new THREE.AnimationMixer(g.scene);
        e.mixer.stopAllAction();
        const clip = g.animations.find((a) => a.name === st.key);
        if (clip) { e.action = e.mixer.clipAction(clip); e.action.reset().setLoop(THREE.LoopRepeat).play(); e.action.paused = !playing; }
        const wudu = st.key.startsWith("wudu");
        e.center.set(0, wudu ? 0.55 : 0.45, wudu ? 0.15 : 0.12); e.radius = wudu ? 0.72 : 0.78;
        if (!e.viewed) { view("front"); e.viewed = true; } else { e.ctl.target.copy(e.center); }
        setStatus("");
      } catch (err) {
        setStatus("Could not load the model — please check the internet and try again. (" + err.message + ")");
      }
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx]);

  useEffect(() => { const e = eng.current; if (e?.action) e.action.paused = !playing; }, [playing]);

  const groupSteps = STEPS.map((s, i) => ({ ...s, i })).filter((s) => s.group === st.group);
  const go = (i) => setIdx((i + STEPS.length) % STEPS.length);
  const btn = { border: "1px solid #CFE0D5", background: "#fff", color: "#123F28", borderRadius: 999, padding: "7px 14px", cursor: "pointer", font: "inherit" };
  const on = { ...btn, background: "#1A5C3A", color: "#fff", borderColor: "#1A5C3A" };

  return (
    <div onCopy={block} onCut={block} onContextMenu={block} onDragStart={block}
      style={{ userSelect: "none", WebkitUserSelect: "none", WebkitTouchCallout: "none" }}>
      <h2 style={{ margin: "0 0 2px" }}>🕌 Learn Salah <span style={{ fontSize: 15, color: "#5B6B62", fontWeight: 500 }}>· নামাজ শিক্ষা</span></h2>
      <p style={{ margin: "0 0 2px", color: "#1F2A24", fontSize: 16 }}>Wudu and salah the Hanafi way — the child does every step. Turn the model with your finger to see it from all sides.</p>
      <p style={{ margin: "0 0 14px", color: "#5B6B62", fontSize: 13 }}>হানাফি নিয়মে অজু ও নামাজ — প্রতিটি ধাপ শিশু নিজে করে দেখায়। আঙুল দিয়ে ঘুরিয়ে চারদিক থেকে দেখুন।</p>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
        {GROUPS.map(([g, label, bn]) => (
          <button key={g} style={st.group === g ? on : btn} onClick={() => go(STEPS.findIndex((s) => s.group === g))}>{label} <small style={{ opacity: 0.75, fontSize: 11 }}>{bn}</small></button>
        ))}
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
        {groupSteps.map((s, n) => (
          <button key={s.key} style={{ ...(s.i === idx ? on : btn), fontSize: 13, padding: "5px 11px" }} onClick={() => go(s.i)}>
            {n + 1}. {s.en.title.split(" · ").pop()}
          </button>
        ))}
      </div>
      <div style={{ position: "relative", background: "#FBF8F1", border: "1px solid #DCE9E0", borderRadius: 16, overflow: "hidden" }}>
        <div ref={box} style={{ width: "100%", height: "min(62vh, 560px)", touchAction: "none" }} />
        {status && <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", color: "#123F28", background: "rgba(251,248,241,.7)" }}>{status}</div>}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center", padding: 10, borderTop: "1px solid #E5EEE8", background: "#fff" }}>
          <button style={playing ? btn : on} onClick={() => setPlaying((p) => !p)}>{playing ? "⏸ Pause" : "▶ Play"}</button>
          <button style={btn} onClick={() => view("front")}>Front</button>
          <button style={btn} onClick={() => view("side")}>Side</button>
          <button style={btn} onClick={() => view("back")}>Back</button>
        </div>
      </div>
      <div style={{ marginTop: 12, background: "#fff", border: "1px solid #DCE9E0", borderLeft: "5px solid #C9962A", borderRadius: 14, padding: "14px 16px" }}>
        <h3 style={{ margin: "0 0 6px", color: "#123F28", fontSize: 21 }}>{st.en.title}</h3>
        <p style={{ margin: 0, lineHeight: 1.7, fontSize: 17 }} dangerouslySetInnerHTML={{ __html: st.en.text }} />
        {st.en.rule && <span style={{ display: "inline-block", marginTop: 8, fontSize: 13, background: "#FFF6E0", color: "#7A5A12", borderRadius: 8, padding: "3px 10px" }}>{st.en.rule}</span>}
        <p style={{ margin: "10px 0 0", color: "#5B6B62", fontSize: 13, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: st.bn.title + " — " + st.bn.text + (st.bn.rule ? " (" + st.bn.rule + ")" : "") }} />
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button style={{ ...btn, flex: 1 }} onClick={() => go(idx - 1)}>‹ Previous</button>
        <span style={{ alignSelf: "center", color: "#5B6B62" }}>{idx + 1} / {STEPS.length}</span>
        <button style={{ ...on, flex: 1 }} onClick={() => go(idx + 1)}>Next ›</button>
      </div>
    </div>
  );
}
