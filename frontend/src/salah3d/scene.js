/* নামাজ শিক্ষা — 3D দৃশ্য: আলো, মেঝে, জায়নামাজ, বেসিন, টুল … (শিশুর মডেল আসে সার্ভারের .glb থেকে)।
   শিশু +Z দিকে (কিবলা) মুখ করে, মেঝে y = 0। */
import * as THREE from "three";

const cache = {};
const mat = (c, o = {}) => {
  const k = c + JSON.stringify(o);
  if (!cache[k]) cache[k] = new THREE.MeshStandardMaterial({ color: new THREE.Color(c), roughness: 0.8, ...o });
  return cache[k];
};
const V = (x, y, z) => new THREE.Vector3(x, y, z);

function rod(g, A, B, r, m) {
  const d = B.clone().sub(A);
  const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, d.length(), 16), m);
  c.position.copy(A).add(B).multiplyScalar(0.5);
  c.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize());
  g.add(c);
}

function prayerMat(g) {
  const base = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.012, 1.18), mat(0x1a5c3a, { roughness: 0.95 }));
  base.position.set(0, 0.006, 0.28); g.add(base);
  const gold = mat(0xc9962a, { roughness: 0.55 });
  const bar = (w, d, x, z) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, 0.004, d), gold); b.position.set(x, 0.0135, z); g.add(b); };
  bar(0.6, 0.018, 0, -0.27); bar(0.6, 0.018, 0, 0.83); bar(0.018, 1.1, -0.29, 0.28); bar(0.018, 1.1, 0.29, 0.28);
  const arch = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.009, 8, 40, Math.PI), gold);
  arch.rotation.x = -Math.PI / 2; arch.position.set(0, 0.0135, 0.62); g.add(arch);
}

function basin(g, waterOn) {
  const white = mat(0xf2f2f0, { roughness: 0.3 }), steel = mat(0xb9c2c8, { roughness: 0.25, metalness: 0.7 });
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.09, 0.56, 28), white); stand.position.set(0, 0.28, 0.4); g.add(stand);
  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.21, 0.14, 0.12, 40, 1, true), mat(0xf2f2f0, { roughness: 0.3, side: THREE.DoubleSide }));
  bowl.position.set(0, 0.62, 0.4); g.add(bowl);
  const bottom = new THREE.Mesh(new THREE.CircleGeometry(0.14, 40), white); bottom.rotation.x = -Math.PI / 2; bottom.position.set(0, 0.565, 0.4); g.add(bottom);
  rod(g, V(0, 0.68, 0.6), V(0, 0.8, 0.6), 0.016, steel); rod(g, V(0, 0.8, 0.6), V(0, 0.8, 0.44), 0.013, steel);
  if (waterOn) {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(0.009, 0.012, 0.17, 12),
      new THREE.MeshStandardMaterial({ color: 0x7ec8f0, transparent: true, opacity: 0.5, roughness: 0.1 }));
    w.position.set(0, 0.69, 0.44); g.add(w);
  }
}

function stool(g) {
  const wood = mat(0x8a5a2b, { roughness: 0.7 });
  const top = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.035, 0.26), wood); top.position.set(0, 0.29, -0.15); g.add(top);
  for (const x of [-0.12, 0.12]) for (const z of [-0.25, -0.05]) {
    const l = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.28, 0.03), wood); l.position.set(x, 0.14, z); g.add(l);
  }
  const s = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.14, 0.2), mat(0x8e9a95, { roughness: 0.9 })); s.position.set(-0.09, 0.07, 0.27); g.add(s);
}

export function makeScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xfbf8f1);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xcfc4b3, 1.2));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  sun.position.set(1.4, 3.0, 2.2); sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -1.2, right: 1.2, top: 1.6, bottom: -0.6, near: 0.5, far: 8 });
  sun.shadow.bias = -0.0006; scene.add(sun);
  const fill = new THREE.DirectionalLight(0xffffff, 0.5); fill.position.set(-2, 1.5, -2.2); scene.add(fill);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), new THREE.ShadowMaterial({ opacity: 0.16 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const props = new THREE.Group(); scene.add(props);
  return { scene, props };
}

/* ধাপ অনুযায়ী আসবাব: অজু = বেসিন (পা ধোয়া = টুল), নামাজ = জায়নামাজ */
export function setProps(props, key) {
  while (props.children.length) props.remove(props.children[0]);
  if (key === "wudu-12-feet") stool(props);
  else if (key.startsWith("wudu")) basin(props, !["wudu-01-niyyah", "wudu-07-face", "wudu-09-head", "wudu-10-ears", "wudu-11-neck"].includes(key));
  else prayerMat(props);
  props.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
}
