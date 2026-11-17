/* .pptx → slides the browser can draw, with click animations and transitions (no software on the teacher's device).
   Supports what PowerPoint/pptxgenjs decks use for teaching: text boxes, shapes (rect, rounded rect, ellipse, star …),
   pictures, tables, backgrounds, layouts/masters, theme colours, slide numbers, entrance animations, transitions, notes. */
import JSZip from "jszip";

const EMU_PER_PT = 12700;
const kids = (el, name) => (el ? [...el.children].filter((c) => c.localName === name) : []);
const kid = (el, name) => kids(el, name)[0] || null;
const deep = (el, name) => (el ? el.getElementsByTagNameNS("*", name)[0] || null : null);
const deepAll = (el, name) => (el ? [...el.getElementsByTagNameNS("*", name)] : []);
const attr = (el, a, d = null) => (el && el.hasAttribute(a) ? el.getAttribute(a) : d);
const parse = (s) => new DOMParser().parseFromString(s, "application/xml");
const dirOf = (p) => p.slice(0, p.lastIndexOf("/") + 1);
function resolve(base, target) {
  if (target.startsWith("/")) return target.slice(1);
  const parts = (dirOf(base) + target).split("/");
  const out = [];
  for (const p of parts) { if (p === "..") out.pop(); else if (p !== ".") out.push(p); }
  return out.join("/");
}
const relsPath = (p) => dirOf(p) + "_rels/" + p.slice(p.lastIndexOf("/") + 1) + ".rels";

export async function loadPptx(buffer) {
  const zip = await JSZip.loadAsync(buffer);
  const read = async (p) => { const f = zip.file(p); return f ? f.async("string") : null; };
  const rels = async (p) => {
    const x = await read(relsPath(p));
    const m = {};
    if (x) for (const r of deepAll(parse(x), "Relationship")) m[attr(r, "Id")] = { target: resolve(p, attr(r, "Target")), type: attr(r, "Type") || "" };
    return m;
  };
  const media = {};
  const blobUrl = async (p) => {
    if (!media[p]) {
      const f = zip.file(p);
      if (!f) return null;
      const ext = p.split(".").pop().toLowerCase();
      const mime = { png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", gif: "image/gif", svg: "image/svg+xml", webp: "image/webp", emf: "image/emf", wmf: "image/wmf" }[ext] || "application/octet-stream";
      media[p] = URL.createObjectURL(new Blob([await f.async("uint8array")], { type: mime }));
    }
    return media[p];
  };

  const presP = "ppt/presentation.xml";
  const pres = parse(await read(presP));
  const sz = deep(pres, "sldSz");
  const W = +attr(sz, "cx", 12192000), H = +attr(sz, "cy", 6858000);
  const presRels = await rels(presP);

  // theme colours (first theme found from the first master)
  const theme = {};
  const firstMaster = Object.values(presRels).find((r) => r.type.endsWith("/slideMaster"));
  if (firstMaster) {
    const mr = await rels(firstMaster.target);
    const th = Object.values(mr).find((r) => r.type.endsWith("/theme"));
    const tx = th && (await read(th.target));
    if (tx) {
      const cs = deep(parse(tx), "clrScheme");
      for (const c of cs ? [...cs.children] : []) {
        const v = deep(c, "srgbClr") ? attr(deep(c, "srgbClr"), "val") : attr(deep(c, "sysClr"), "lastClr", "000000");
        theme[c.localName] = v;
      }
    }
  }
  const SCHEME = { tx1: "dk1", tx2: "dk2", bg1: "lt1", bg2: "lt2" };
  function color(el) {
    if (!el) return null;
    const s = kid(el, "srgbClr") || kid(el, "schemeClr") || kid(el, "sysClr") || kid(el, "prstClr");
    if (!s) return null;
    let hex = s.localName === "srgbClr" ? attr(s, "val") : s.localName === "schemeClr" ? theme[SCHEME[attr(s, "val")] || attr(s, "val")]
      : s.localName === "sysClr" ? attr(s, "lastClr") : ({ black: "000000", white: "FFFFFF", red: "FF0000" }[attr(s, "val")] || "000000");
    if (!hex) return null;
    let a = 1;
    const al = kid(s, "alpha");
    if (al) a = +attr(al, "val") / 100000;
    const lm = kid(s, "lumMod"), lo = kid(s, "lumOff");
    let [r, g, b] = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
    if (lm || lo) {
      const m = lm ? +attr(lm, "val") / 100000 : 1, o = lo ? +attr(lo, "val") / 100000 : 0;
      [r, g, b] = [r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v * m + 255 * o))));
    }
    return a < 1 ? `rgba(${r},${g},${b},${a})` : `rgb(${r},${g},${b})`;
  }

  // slide order
  const order = deepAll(pres, "sldId").map((s) => presRels[attr(s, "r:id") || s.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "id")]?.target).filter(Boolean);

  // PowerPoint sections (p14:section) → [{ name, start }] — Lesson Plan-এর প্রতিটি টপিক তার বইয়ের অংশটুকুই চালায়
  const R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
  const mainIds = deepAll(pres, "sldId").filter((s) => attr(s, "r:id") || s.getAttributeNS(R_NS, "id")).map((s) => attr(s, "id"));
  const sections = deepAll(pres, "section").map((sec) => {
    const first = deepAll(sec, "sldId")[0];
    return { name: attr(sec, "name", ""), start: first ? mainIds.indexOf(attr(first, "id")) : -1 };
  }).filter((x) => x.start >= 0);

  const parts = {};
  async function part(p) {
    if (!parts[p]) parts[p] = { doc: parse(await read(p)), rels: await rels(p), path: p };
    return parts[p];
  }

  const slides = [];
  for (let n = 0; n < order.length; n++) {
    const sp = await part(order[n]);
    const layoutRel = Object.values(sp.rels).find((r) => r.type.endsWith("/slideLayout"));
    const layout = layoutRel ? await part(layoutRel.target) : null;
    const masterRel = layout && Object.values(layout.rels).find((r) => r.type.endsWith("/slideMaster"));
    const master = masterRel ? await part(masterRel.target) : null;
    const notesRel = Object.values(sp.rels).find((r) => r.type.endsWith("/notesSlide"));
    let notes = "";
    if (notesRel) {
      const nd = (await part(notesRel.target)).doc;
      for (const s of deepAll(nd, "sp")) {
        const ph = deep(s, "ph");
        if (ph && attr(ph, "type") === "body") notes = deepAll(s, "p").map((p) => deepAll(p, "t").map((t) => t.textContent).join("")).join("\n");
      }
    }
    const bgOf = (d) => { const bg = deep(d?.doc, "bg"); if (!bg) return null; const f = deep(bg, "solidFill"); return f ? color(f) : null; };
    const bg = bgOf(sp) || bgOf(layout) || bgOf(master) || "#fff";

    const findPh = (doc, ph) => {
      if (!doc) return null;
      const type = attr(ph, "type", "body"), idx = attr(ph, "idx");
      for (const s of deepAll(deep(doc.doc, "spTree"), "sp")) {
        const p = deep(s, "ph");
        if (!p) continue;
        if ((idx && attr(p, "idx") === idx) || attr(p, "type", "body") === type) return s;
      }
      return null;
    };

    const ctx = { W, H, color, n, total: order.length };
    const items = [];
    const addTree = async (doc, owner, fromLayout) => {
      const tree = deep(doc.doc, "spTree");
      for (const el of tree ? [...tree.children] : []) await addEl(el, owner, fromLayout, null);
    };
    async function addEl(el, owner, fromLayout, grp) {
      const ln = el.localName;
      if (ln === "sp") {
        const ph = deep(deep(el, "nvSpPr"), "ph");
        if (fromLayout && ph) return;                         // layout placeholders are only templates
        const inh = ph ? [findPh(layout, ph), findPh(master, ph)].filter(Boolean) : [];
        items.push(shape(el, inh, ctx, grp));
      } else if (ln === "pic") {
        const emb = attr(deep(el, "blip"), "r:embed") || deep(el, "blip")?.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "embed");
        const target = owner.rels[emb]?.target;
        const it = base(el, ctx, grp);
        it.kind = "pic"; it.src = target ? await blobUrl(target) : null;
        const sr = deep(el, "srcRect");
        if (sr) it.crop = ["l", "t", "r", "b"].map((k) => +attr(sr, k, 0) / 100000);
        items.push(it);
      } else if (ln === "graphicFrame") {
        const tbl = deep(el, "tbl");
        if (tbl) items.push(table(el, tbl, ctx, grp));
      } else if (ln === "grpSp") {
        const x = deep(kid(el, "grpSpPr"), "xfrm");
        const g = x ? { off: [+attr(kid(x, "off"), "x"), +attr(kid(x, "off"), "y")], ext: [+attr(kid(x, "ext"), "cx"), +attr(kid(x, "ext"), "cy")],
          choff: [+attr(kid(x, "chOff"), "x"), +attr(kid(x, "chOff"), "y")], chext: [+attr(kid(x, "chExt"), "cx"), +attr(kid(x, "chExt"), "cy")] } : null;
        for (const c of [...el.children]) await addEl(c, owner, fromLayout, g || grp);
      }
    }
    if (master) await addTree(master, master, true);
    if (layout) await addTree(layout, layout, true);
    const before = items.length;
    await addTree(sp, sp, false);
    for (let i = 0; i < before; i++) items[i].under = true;

    slides.push({ bg, items, notes, steps: timing(sp.doc), transition: transitionOf(sp.doc) });
  }
  return { W, H, slides, sections, dispose: () => Object.values(media).forEach((u) => URL.revokeObjectURL(u)) };
}

function xfrmOf(el) {
  const x = deep(el, "xfrm");
  if (!x || !kid(x, "off")) return null;
  return { x: +attr(kid(x, "off"), "x"), y: +attr(kid(x, "off"), "y"), w: +attr(kid(x, "ext"), "cx"), h: +attr(kid(x, "ext"), "cy"),
           rot: +attr(x, "rot", 0) / 60000, flipH: attr(x, "flipH") === "1", flipV: attr(x, "flipV") === "1" };
}
function inGroup(b, g) {
  if (!g || !g.chext[0]) return b;
  const sx = g.ext[0] / g.chext[0], sy = g.ext[1] / g.chext[1];
  return { ...b, x: g.off[0] + (b.x - g.choff[0]) * sx, y: g.off[1] + (b.y - g.choff[1]) * sy, w: b.w * sx, h: b.h * sy };
}
function base(el, ctx, grp, inh = []) {
  const nv = deep(el, "cNvPr");
  let b = xfrmOf(kid(el, "spPr") || el);
  for (const s of inh) if (!b) b = xfrmOf(kid(s, "spPr"));
  b = inGroup(b || { x: 0, y: 0, w: 0, h: 0, rot: 0 }, grp);
  return { id: attr(nv, "id"), name: attr(nv, "name", ""), ...b };
}

function shape(el, inh, ctx) {
  const it = base(el, ctx, null, inh);
  it.kind = "sp";
  const spPr = kid(el, "spPr");
  const geom = deep(spPr, "prstGeom");
  it.geom = geom ? attr(geom, "prst", "rect") : "rect";
  const adj = geom && deep(geom, "gd");
  it.adj = adj ? +String(attr(adj, "fmla", "val 16667")).replace("val ", "") : 16667;
  const fill = kid(spPr, "solidFill");
  it.fill = kid(spPr, "noFill") ? null : fill ? ctx.color(fill) : null;
  const lnEl = kid(spPr, "ln");
  it.line = lnEl && !kid(lnEl, "noFill") && kid(lnEl, "solidFill") ? { c: ctx.color(kid(lnEl, "solidFill")), w: +attr(lnEl, "w", 12700) } : null;
  const tb = kid(el, "txBody") || inh.map((s) => kid(s, "txBody")).find(Boolean);
  if (kid(el, "txBody")) it.text = textBody(kid(el, "txBody"), inh.map((s) => kid(s, "txBody")).filter(Boolean), ctx);
  else it.text = null;
  void tb;
  return it;
}

function textBody(tb, inheritBodies, ctx) {
  const bp = kid(tb, "bodyPr");
  const pick = (a, d) => { if (attr(bp, a) != null) return attr(bp, a); for (const ib of inheritBodies) { const v = attr(kid(ib, "bodyPr"), a); if (v != null) return v; } return d; };
  const lvlDef = (b) => deep(deep(kid(b, "lstStyle"), "lvl1pPr"), "defRPr");
  const defs = [lvlDef(tb), ...inheritBodies.map(lvlDef)].filter(Boolean);
  const lvlP = [deep(kid(tb, "lstStyle"), "lvl1pPr"), ...inheritBodies.map((b) => deep(kid(b, "lstStyle"), "lvl1pPr"))].filter(Boolean);
  const runStyle = (rPr) => {
    const chain = [rPr, ...defs].filter(Boolean);
    const g = (a) => { for (const c of chain) if (attr(c, a) != null) return attr(c, a); return null; };
    let col = null, font = null, cs = null;
    for (const c of chain) { if (!col && kid(c, "solidFill")) col = ctx.color(kid(c, "solidFill")); if (!font && kid(c, "latin")) font = attr(kid(c, "latin"), "typeface"); if (!cs && kid(c, "cs")) cs = attr(kid(c, "cs"), "typeface"); }
    return { sz: (+g("sz") || 1800) / 100, b: g("b") === "1", i: g("i") === "1", u: g("u") && g("u") !== "none", col, font, cs };
  };
  const paras = kids(tb, "p").map((p) => {
    const pPr = kid(p, "pPr");
    let algn = attr(pPr, "algn"); if (algn == null) for (const l of lvlP) if (attr(l, "algn")) { algn = attr(l, "algn"); break; }
    const runs = [];
    for (const c of [...p.children]) {
      if (c.localName === "r") runs.push({ t: deep(c, "t")?.textContent || "", ...runStyle(kid(c, "rPr")) });
      else if (c.localName === "br") runs.push({ br: true });
      else if (c.localName === "fld") runs.push({ t: attr(c, "type") === "slidenum" ? String(ctx.n + 1) : deep(c, "t")?.textContent || "", ...runStyle(kid(c, "rPr")) });
    }
    const end = runStyle(kid(p, "endParaRPr"));
    const spcAft = deep(deep(pPr, "spcAft"), "spcPts"), spcBef = deep(deep(pPr, "spcBef"), "spcPts");
    const bullet = pPr && kid(pPr, "buChar") ? attr(kid(pPr, "buChar"), "char") : null;
    return { algn: algn || "l", rtl: attr(pPr, "rtl") === "1", runs, endSz: end.sz, bullet, marL: +attr(pPr, "marL", 0),
             aft: spcAft ? +attr(spcAft, "val") / 100 : 0, bef: spcBef ? +attr(spcBef, "val") / 100 : 0 };
  });
  const ins = (k, d) => +pick(k, d);
  return { paras, anchor: pick("anchor", "t"), wrap: pick("wrap", "square") !== "none", vert: pick("vert", "horz"),
           pad: [ins("tIns", 45720), ins("rIns", 91440), ins("bIns", 45720), ins("lIns", 91440)], rtlCol: pick("rtlCol", "0") === "1" };
}

function table(el, tbl, ctx) {
  const it = base(el, ctx, null);
  it.kind = "tbl";
  it.cols = kids(kid(tbl, "tblGrid"), "gridCol").map((g) => +attr(g, "w"));
  it.rows = kids(tbl, "tr").map((tr) => ({ h: +attr(tr, "h"), cells: kids(tr, "tc").map((tc) => {
    const pr = kid(tc, "tcPr");
    const f = kid(pr, "solidFill");
    const bl = kid(pr, "lnB") || kid(pr, "lnL");
    return { text: textBody(kid(tc, "txBody"), [], ctx), fill: f ? ctx.color(f) : null, span: +attr(tc, "gridSpan", 1), hm: attr(tc, "hMerge") === "1",
             border: bl && kid(bl, "solidFill") ? { c: ctx.color(kid(bl, "solidFill")), w: +attr(bl, "w", 12700) } : null,
             pad: [+attr(pr, "marT", 45720), +attr(pr, "marR", 91440), +attr(pr, "marB", 45720), +attr(pr, "marL", 91440)], anchor: attr(pr, "anchor", "t") };
  }) }));
  return it;
}

/* click steps: [{ items: [{ id, effect, dir, delay, exit }] }]; steps before the first click play at once */
const PRESET_FX = { 1: "appear", 10: "fade", 53: "pop", 23: "zoom", 2: "fly", 26: "bounce", 49: "spin", 22: "wipe", 21: "wheel", 42: "float", 47: "float", 37: "float", 16: "zoom", 31: "spin", 3: "zoom", 9: "fade", 14: "fade", 18: "wipe", 12: "fly" };
function timing(doc) {
  const seq = deepAll(doc, "cTn").find((c) => attr(c, "nodeType") === "mainSeq");
  if (!seq) return { auto: [], clicks: [] };
  const groups = kids(kid(seq, "childTnLst"), "par");
  const auto = [], clicks = [];
  for (const g of groups) {
    const effects = deepAll(g, "cTn").filter((c) => attr(c, "presetClass"));
    if (!effects.length) continue;
    const list = effects.map((c) => {
      const spid = attr(deep(c, "spTgt"), "spid");
      const pid = +attr(c, "presetID", 10), sub = +attr(c, "presetSubtype", 0);
      const cls = attr(c, "presetClass");
      const cond = deep(kid(c, "stCondLst"), "cond");
      return { id: spid, cls, effect: PRESET_FX[pid] || "fade", dir: sub, node: attr(c, "nodeType"), delay: +attr(cond, "delay", 0) || 0 };
    }).filter((e) => e.id && (e.cls === "entr" || e.cls === "exit"));
    if (!list.length) continue;
    if (list[0].node === "clickEffect" || clicks.length) clicks.push(list); else auto.push(...list);
  }
  return { auto, clicks };
}
function transitionOf(doc) {
  const t = deep(doc, "transition");
  if (!t) return null;
  const c = [...t.children].find((x) => x.localName !== "extLst");
  return c ? { kind: c.localName, dir: attr(c, "dir", "") } : { kind: "fade" };
}

export const EMU = { PT: EMU_PER_PT };
