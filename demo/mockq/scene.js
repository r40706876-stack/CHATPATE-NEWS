/* POSTAL WALA - Mock sawal ka poora analysis (demo). Samay asli awaaz (window.CUES) se. */
(function () {
const {p, clamp, lerp, $, set, shake} = E;
const NS = "http://www.w3.org/2000/svg";
const TX = {}; LINES.forEach(([i, t]) => TX[i] = t);
let C = window.CUES;
if (!C) { C = {}; let t = .35; const st = new Set(SCENES.map(s => s[1]));
  LINES.forEach(([i, x]) => { if (st.has(i) && t > .5) t += .3; const d = .42 * x.split(/\s+/).length + .3; C[i] = {t, d}; t += d + .12; }); }
const T = i => C[i].t, END = i => C[i].t + C[i].d;
function W(i, sub, occ = 0) {
  const ws = TX[i].split(/\s+/); const hits = []; ws.forEach((w, k) => { if (w.includes(sub)) hits.push(k); });
  const k = hits.length ? hits[occ < 0 ? hits.length + occ : Math.min(occ, hits.length - 1)] : 0;
  return C[i].w && C[i].w[k] != null ? C[i].t + C[i].w[k] : C[i].t + C[i].d * k / ws.length;
}
function wt(id, k) { const c = C[id]; return c.w && c.w[k] != null ? c.t + c.w[k] : c.t + c.d * k / TX[id].split(/\s+/).length; }
const last = LINES[LINES.length - 1][0];
const TOTAL = END(last) + 1.8; window.TOTAL = TOTAL;
const SID = {sc_hook: "f_hook", sc_q: "s_q", sc_mach: "s_mach", sc_rule: "s_rule", sc_dates: "s_dates", sc_box: "s_box", sc_ans: "s_ans", sc_trap: "f_trap", sc_trick: "f_trick", sc_cta: "s_cta"};
const SC = SCENES.map(([n, f], k) => ({n, el: $("#" + SID[n]), a: k ? T(f) - .3 : 0, tr: ["slide", "zoom", "flash"][k % 3]}));

/* pencil ke kaam */
const OPS = {}; function op(n, t0, d) { OPS[n] = [t0, d]; return t0 + d; }
let e;
e = op("stack", T("z1") + .05, .9); op("stackT", Math.max(e + .02, W("z1", "सैकड़ों") - .2), .55);
e = op("mach", Math.max(T("z2"), W("z2", "मशीन") - .5), .8); op("machT", e + .02, .35);
e = op("win", T("z4") + .05, .8); op("winT", e + .02, .4);
const CAP_HL = ["तीन", "महाराष्ट्र", "आंध्र", "अवैतनिक", "फ्रैंक", "फ्रैंकिंग", "तारीख", "खिड़की", "उसी", "पिछली", "अगली", "लेटर", "बॉक्स", "बैरंग", "सभी", "जाल", "MOCK", "चाबी", "D,", "पोस्टमार्टम", "गलत"];
let built = false, ops = {}, capChunks = [];
function mk(tag, a, par) { const x = document.createElementNS(NS, tag); for (const k in a) x.setAttribute(k, a[k]); par.appendChild(x); return x; }

function build() {
  built = true;
  for (const n in OPS) ops[n] = {paths: [], texts: [], len: 0};
  SC.forEach(s => s.el.style.opacity = 1);
  document.querySelectorAll(".dr").forEach(el => { const o = ops[el.dataset.op]; if (!o) return; const L = el.getTotalLength();
    el.setAttribute("fill", "none"); el.setAttribute("stroke", el.classList.contains("red") ? "#dc2626" : "#1f2937");
    el.setAttribute("stroke-width", el.classList.contains("red") ? 6 : 3.4); el.setAttribute("stroke-linecap", "round"); el.setAttribute("stroke-linejoin", "round");
    el.style.strokeDasharray = L; el.style.strokeDashoffset = L; o.paths.push({el, L, at: o.len, svg: el.ownerSVGElement}); o.len += L; });
  let ci = 0;
  document.querySelectorAll(".tx").forEach(el => { const o = ops[el.dataset.op]; if (!o) return; el.setAttribute("font-weight", "700");
    const bb = el.getBBox(), id = "cpt" + (ci++); const svg = el.ownerSVGElement; let defs = svg.querySelector("defs"); if (!defs) defs = mk("defs", {}, svg);
    const cp = mk("clipPath", {id}, defs); const r = mk("rect", {x: bb.x - 6, y: bb.y - 8, width: 0, height: bb.height + 16}, cp);
    el.setAttribute("clip-path", `url(#${id})`); o.texts.push({el, bb, r, svg}); });
  const stg = $("#stage").getBoundingClientRect();
  function rel(id) { const c = $("#" + id).closest(".card"), old = c.style.transform; c.style.transform = "none"; c.style.opacity = 1;
    const r = $("#" + id).getBoundingClientRect(); c.style.transform = old; return {x: r.left - stg.left, y: r.top - stg.top, w: r.width, h: r.height, card: c.id}; }
  function textW(id) { const el = $("#" + id), c = el.closest(".card"), old = c.style.transform; c.style.transform = "none"; const r = document.createRange(); r.selectNodeContents(el); const w = r.getBoundingClientRect().width; c.style.transform = old; return w + 20; }
  function strike(n, id) { const a = rel(id), ink = $("#" + id).closest(".sc").querySelector(".ink");
    const el = mk("path", {d: `M${a.x + 4},${a.y + a.h / 2 + 3 + 12} L${a.x + Math.min(textW(id), 440)},${a.y + a.h / 2 - 3 + 12}`, fill: "none", stroke: "#dc2626", "stroke-width": 5, "stroke-linecap": "round", "data-card": a.card}, ink);
    const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L; ops[n].paths.push({el, L, at: 0, svg: ink}); ops[n].len = L; }
  function ring(n, id) { const b = rel(id), ink = $("#" + id).closest(".sc").querySelector(".ink"); const tw = textW(id); const rx = Math.min(tw, 440) / 2 + 12, cx = b.x + rx, cy = b.y + b.h / 2 + 12, ry = b.h / 2 + 7;
    const el = mk("path", {d: `M${cx - rx + 6},${cy - ry + 4} A${rx},${ry} 0 1,0 ${cx + rx},${cy + 2} A${rx},${ry} 0 0,0 ${cx - rx + 18},${cy - ry - 2}`, fill: "none", stroke: "#16a34a", "stroke-width": 4.2, "stroke-linecap": "round", "data-card": b.card}, ink);
    const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L; ops[n].paths.push({el, L, at: 0, svg: ink}); ops[n].len = L; }

  /* captions */
  const cap = $("#cap");
  LINES.forEach(([id, txt]) => { const ws = txt.split(/\s+/); for (let s = 0; s < ws.length;) {
    let n = Math.min(6, ws.length - s); if (ws.length - s - n > 0 && ws.length - s - n < 3) n = Math.ceil((ws.length - s) / 2);
    const d = document.createElement("div"); d.style.cssText = "position:absolute;left:0;right:0;top:0;opacity:0";
    d.innerHTML = ws.slice(s, s + n).map(w => `<span class="w${CAP_HL.some(h => w.includes(h)) ? " hl" : ""}">${w}</span>`).join(" ");
    cap.appendChild(d); capChunks.push({el: d, id, k0: s, n}); s += n; } });
  SC.forEach(s => s.el.style.opacity = 0);
}

function drawOps(t) {
  let tip = null, vis = 0, svg = null;
  for (const n in OPS) { const [t0, d] = OPS[n], o = ops[n]; if (!o) continue; const kk = E.ease.inout(clamp((t - t0) / d)); const act = t >= t0 - .15 && t <= t0 + d + .15; const at = kk * o.len;
    o.paths.forEach(pp => { const lk = clamp((at - pp.at) / pp.L); pp.el.style.strokeDashoffset = pp.L * (1 - lk);
      if (act && at >= pp.at && at <= pp.at + pp.L + .01) { const q = pp.el.getPointAtLength(clamp(at - pp.at, 0, pp.L)); tip = [q.x, q.y]; svg = pp.svg; } });
    o.texts.forEach(tx => { tx.r.setAttribute("width", (tx.bb.width + 12) * kk); if (act) { tip = [tx.bb.x + tx.bb.width * kk, tx.bb.y + tx.bb.height * .72 + Math.sin(t * 38) * 4]; svg = tx.svg; } });
    if (act) vis = Math.max(vis, Math.min(clamp((t - t0 + .15) / .15), clamp((t0 + d + .15 - t) / .15))); }
  return {tip, vis, svg};
}
let t_ = 0;
function card(id, tin, opts, stampId, stampT) {
  const ki = p(t_, tin, .5, "back");
  set("#" + id, {opacity: clamp((t_ - tin) / .15), transform: `translateY(${(1 - ki) * 80}px) rotate(${lerp(-5, -1, ki)}deg)`});
  opts.forEach(([oid, ta]) => { const k = p(t_, ta, .3); set("#" + oid, {opacity: k, transform: `translateX(${(1 - k) * -16}px)`}); });
  if (stampId) { const k = p(t_, stampT, .2, "out"); set("#" + stampId, {opacity: clamp((t_ - stampT) / .06), transform: `rotate(-9deg) scale(${lerp(2.6, 1, k)})`}); }
}
function pop(sel, at, out = 1e9) { const k = p(t_, at, .4, "back"); set(sel, {opacity: clamp((t_ - at) / .1) * (1 - p(t_, out, .25)), transform: `scale(${Math.max(0, k)})`}); }
function term(sel, at, out = 1e9) { const k = p(t_, at, .4, "back"); set(sel, {opacity: clamp((t_ - at) / .1) * (1 - p(t_, out, .25)), transform: `translateX(-50%) scale(${Math.max(0, k)})`}); }
function opts4(pre, wordLine, word) { const a = W(wordLine, word); return ["a", "b", "c", "d"].map((x, i) => [pre + x, a - .1 + i * .15]); }

function seek(t) {
  t_ = t; if (!built) build();
  set("#o1", {transform: `translate(${Math.sin(t * .35) * 40}px,${Math.cos(t * .27) * 50}px)`});
  set("#o2", {transform: `translate(${Math.cos(t * .3) * 40}px,${Math.sin(t * .22) * 40}px)`});
  const gs = Math.floor(t * 12); set("#grain", {transform: `translate(${(gs * 37) % 60 - 30}px,${(gs * 23) % 60 - 30}px)`});
  set("#top", {opacity: p(t, .05, .4)}); E.pop($("#logo"), t, .15, .5);
  $("#rail b").style.width = 100 * clamp(t / TOTAL) + "%";
  let cur = 0; SC.forEach((s, k) => { if (t >= s.a) cur = k; });
  let fl = 0;
  SC.forEach((s, k) => { const isFull = s.el.classList.contains("full");
    if (k === cur) { const ki = p(t, s.a, .38, "out"); let tf = "none", o = 1;
      if (k > 0 && s.tr === "slide") tf = `translateX(${(1 - ki) * 105}%)`;
      if (k > 0 && s.tr === "zoom") { tf = `scale(${lerp(1.18, 1, ki)})`; o = clamp((t - s.a) / .25); }
      if (k > 0 && s.tr === "flash") fl = Math.max(fl, 1 - clamp((t - s.a) / .3));
      set(s.el, {opacity: o, transform: tf, zIndex: isFull ? 40 : 2}); }
    else if (k === cur - 1 && t - SC[cur].a < .38) { const ko = p(t, SC[cur].a, .38, "out");
      set(s.el, {opacity: 1, zIndex: isFull ? 39 : 1, transform: SC[cur].tr === "slide" ? `translateX(${-ko * 40}%)` : SC[cur].tr === "zoom" ? `scale(${1 - .06 * ko})` : "none"}); }
    else set(s.el, {opacity: 0}); });
  set("#flash", {opacity: fl * .85});
  let sk = [0, 0]; const add = q => { sk = [sk[0] + q[0], sk[1] + q[1]]; };
  document.querySelectorAll(".fl").forEach(f => { const o = OPS[f.dataset.after]; if (o) f.setAttribute("opacity", p(t, o[0] + o[1] + .02, .35) * .92); });
  const dr = drawOps(t);
  document.querySelectorAll(".ink path").forEach(pth => { const c = $("#" + pth.dataset.card); pth.style.opacity = c ? (c.style.opacity || 0) : 1; });
  const pen = $("#pencil");
  if (dr.tip && dr.vis > 0) { const r = dr.svg.getBoundingClientRect(), s = r.width / 508;
    set(pen, {opacity: dr.vis, left: (r.left + dr.tip[0] * s) + "px", top: (r.top + dr.tip[1] * s - 15) + "px", transform: `rotate(${-38 + Math.sin(t * 17) * 3}deg)`}); }
  else set(pen, {opacity: 0});

  /* hook */
  const h0 = T("h1"); pop("#hk1", h0 + .02);
  const h3b = W("h1", "तीन"); set("#hk2", {opacity: clamp((t - h3b) / .06), transform: `scale(${lerp(3, 1, p(t, h3b, .25, "out"))})`});
  if (t > h3b + .2 && t < h3b + .6) { const q = shake(t, h3b + .22, .35, 10); set("#f_hook .k2", {translate: `${q[0]}px ${q[1]}px`}); }
  pop("#hk3", h3b + .4);
  document.querySelectorAll("#hkP .pill").forEach((s, i) => pop(s, W("h1", ["महाराष्ट्र", "आंध्र", "महाराष्ट्र"][i], i === 2 ? 1 : 0)));
  const hs = W("h2", "गलत"); set("#hkS", {opacity: clamp((t - hs) / .06), transform: `translateX(-50%) rotate(-6deg) scale(${lerp(2.6, 1, p(t, hs, .2, "out"))})`});
  /* sawal */
  const qa = T("q1"); set("#mk1", {opacity: p(t, qa - .1, .3), transform: `translateY(${(1 - p(t, qa - .1, .5, "back")) * 60}px)`});
  ["a", "b", "c", "d"].forEach((x, i) => { const a = W("q1", ["पिछली", "अगली", "लेटर", "उपरोक्त"][i]) - .1, k = p(t, a, .35, "back");
    set("#o1" + x, {opacity: clamp((t - a) / .08), transform: `translateX(${(1 - k) * -30}px)`}); });
  const ta = T("q2") + .1, left = clamp(3 - (t - ta) * (3 / Math.max(1.5, END("q2") - ta + .2)), 0, 3);
  set("#tm3", {opacity: p(t, ta - .1, .2), transform: `scale(${Math.max(0, p(t, ta - .1, .4, "back"))})`});
  $("#tmN").textContent = Math.ceil(left) || 0; $("#tmR").setAttribute("stroke-dashoffset", 314 * (1 - left / 3));
  /* machine */
  const ea = W("z2", "छाप") - .4, ek = p(t, ea, .7, "inout");
  set("#fEnv", {opacity: p(t, T("z2") + .2, .3), transform: `translate(${lerp(-200, 0, ek)}px,${-Math.sin(ek * Math.PI) * 30}px)`});
  set("#fEnv .box", {opacity: p(t, ea + .65, .15)});
  if (t > ea + .65 && t < ea + 1) add(shake(t, ea + .66, .25, 4));
  const za = W("z3", "तारीख") - .2; set("#zoomImp", {opacity: clamp((t - za) / .1), transform: `scale(${lerp(.3, 1, p(t, za, .5, "back"))})`});
  set("#zD", {boxShadow: t > W("z3", "चाबी") ? `0 0 0 ${3 + 3 * Math.abs(Math.sin(t * 5))}px #f59e0b` : "none"});
  term("#tm_mach", W("z2", "फ्रैंकिंग"));
  /* niyam */
  pop("#calR", W("z4", "उसी") - .2);
  [["#ru1", W("z4", "उसी")], ["#ru2", W("z4", "खिड़की") + .1]].sort((x, y) => x[1] - y[1]).forEach(([s, a]) => { const k = p(t, a, .4, "back"); set(s, {opacity: clamp((t - a) / .08), transform: `scale(${Math.max(0, k)})`}); });
  term("#tm_rule", W("z4", "खिड़की"));
  /* taareekh */
  [["#d14", T("a1") + .05], ["#d15", T("a1") + .2], ["#d16", T("a1") + .35]].forEach(([s, a]) => { const k = p(t, a, .45, "back"); set(s, {opacity: clamp((t - a) / .1), transform: `translateY(${(1 - k) * 60}px)`}); });
  const bA = T("b1");
  $("#dEnvD").textContent = t < bA ? "14-11-2026" : "16-11-2026";
  const toA = p(t, W("a1", "कल") - .2, .6, "inout"), toB = p(t, bA + .1, .6, "inout");
  let ex = lerp(179, 17, toA), ey = lerp(40, 330, toA) * 1;
  if (t >= bA) { ex = lerp(179, 341, toB); ey = lerp(40, 330, toB); }
  set("#dEnv", {opacity: p(t, T("a1") + .3, .3), left: ex + "px", top: (t < W("a1", "कल") - .2 ? 40 : ey) + "px", transform: `scale(.9)`});
  if (t >= bA && t < bA + .1) set("#dEnv", {top: "40px", left: "179px"});
  set("#d14", {boxShadow: t > W("a1", "पीछे") && t < bA ? "0 0 0 6px #ef4444" : "0 12px 26px rgba(0,0,0,.3)"});
  set("#d16", {boxShadow: t > W("b1", "आगे") ? "0 0 0 6px #ef4444" : "0 12px 26px rgba(0,0,0,.3)"});
  set("#d15", {boxShadow: "0 0 0 5px #4ade80"});
  const sA = W("a1", "अवैतनिक"); set("#stA", {opacity: clamp((t - sA) / .06), transform: `rotate(-9deg) scale(${lerp(2.6, 1, p(t, sA, .2, "out"))})`});
  const sB = W("b1", "अवैतनिक"); set("#stB", {opacity: clamp((t - sB) / .06), transform: `rotate(8deg) scale(${lerp(2.6, 1, p(t, sB, .2, "out"))})`});
  if (t > sA + .15 && t < sA + .5) add(shake(t, sA + .18, .3, 6)); if (t > sB + .15 && t < sB + .5) add(shake(t, sB + .18, .3, 6));
  pop("#bairang", W("a2", "बैरंग") - .3, bA);
  term("#tm_dates", W("a2", "अवैतनिक"));
  /* box */
  const ca = T("c1");
  set("#hL", {transform: `translateX(${(1 - p(t, ca, .5, "out")) * -260}px)`}); set("#hR", {transform: `translateX(${(1 - p(t, ca + .15, .5, "out")) * 260}px)`});
  set("#vs", {transform: `scale(${Math.max(0, p(t, ca + .5, .45, "back"))}) rotate(${(1 - p(t, ca + .5, .5)) * 180}deg)`});
  pop("#vL", W("c1", "खिड़की"));
  const dropA = W("c1", "डाल") - .4, dk = p(t, dropA, .7, "inout");
  set("#bxEnv", {opacity: p(t, ca + .6, .3) * (1 - p(t, dropA + .7, .15)), transform: `translate(${lerp(0, 40, dk)}px,${lerp(0, 150, dk)}px) scale(${lerp(.55, .3, dk)})`});
  pop("#vR", W("c1", "अवैतनिक"));
  if (t > W("c1", "अवैतनिक") + .1) add(shake(t, W("c1", "अवैतनिक") + .15, .3, 6));
  /* jawab */
  [["#o2a", W("d1", "A")], ["#o2b", W("d1", "B")], ["#o2c", W("d1", "C")]].forEach(([s, a]) => {
    set(s + " .tk", {opacity: clamp((t - a) / .08), transform: `scale(${Math.max(0, p(t, a, .35, "back"))})`});
    set(s, {background: t > a ? "rgba(74,222,128,.14)" : "rgba(255,255,255,.1)"}); });
  const dA = W("d1", "D,"); set("#o2d .tk", {opacity: clamp((t - dA) / .08), transform: `scale(${Math.max(0, p(t, dA, .35, "back"))})`});
  set("#o2d", {background: t > dA ? "#16a34a" : "rgba(255,255,255,.1)", borderColor: t > dA ? "#4ade80" : "rgba(255,255,255,.18)", transform: `scale(${1 + .05 * Math.max(0, Math.sin(clamp((t - dA) / .5) * Math.PI))})`});
  set("#mk2", {transform: `translateY(${(1 - p(t, T("d1") - .2, .5, "back")) * 50}px)`});
  pop("#ansB", dA + .3);
  document.querySelectorAll("#ansP .pill").forEach((s, i) => pop(s, dA + .7 + i * .15));
  /* jaal */
  pop("#tp1", T("t1")); const tp = W("t1", "C"); set("#tp2", {opacity: clamp((t - tp) / .06), transform: `scale(${lerp(2.8, 1, p(t, tp, .25, "out"))})`});
  if (t > tp + .2 && t < tp + .6) { const q = shake(t, tp + .22, .35, 10); set("#f_trap .k2", {translate: `${q[0]}px ${q[1]}px`}); }
  pop("#tp3", W("t1", "पढ़ते") - .2);
  /* trick */
  pop("#tk1", T("k1"));
  [["#tc1", W("k1", "छाप")], ["#tc2", W("k1", "खिड़की")]].forEach(([s, a]) => { const k = p(t, a - .1, .4, "back"); set(s, {opacity: clamp((t - a + .1) / .08), transform: `translateX(${(1 - k) * -80}px)`}); });
  const tb = W("k1", "टूटी") - .1; set("#tk3", {opacity: clamp((t - tb) / .06), transform: `scale(${lerp(2.4, 1, p(t, tb, .25, "out"))})`});
  /* cta */
  pop("#ctaT", T("m1"));
  [["#sc1", W("m1", "सही")], ["#sc2", W("m1", "गलत")], ["#sc3", W("m1", "जाल")], ["#sc4", W("m1", "trick")]].forEach(([s, a]) => { const k = p(t, a - .15, .4, "back");
    set(s, {opacity: clamp((t - a + .15) / .08), transform: `translateX(${(1 - k) * 120}px)`}); });
  const mb = W("m2", "MOCK") - .3; set("#mockBtn", {opacity: clamp((t - mb) / .1), transform: `scale(${Math.max(0, p(t, mb, .4, "back")) * (1 + .05 * Math.sin(t * 8))})`});

  set("#stage", {transform: `translate(${sk[0]}px,${sk[1]}px)`});
  capChunks.forEach(c => { const a = wt(c.id, c.k0) - .08, nx = c.k0 + c.n < TX[c.id].split(/\s+/).length ? wt(c.id, c.k0 + c.n) - .08 : END(c.id) + .1;
    const vis = t >= a && t < nx; c.el.style.opacity = vis ? 1 : 0; if (!vis) return;
    [...c.el.children].forEach((w, j) => { const ti = wt(c.id, c.k0 + j) - .06, k = p(t, ti, .28, "back");
      w.style.opacity = clamp((t - ti) / .07); w.style.transform = `translateY(${(1 - k) * 20}px) scale(${.75 + .25 * Math.max(0, k)})`; }); });
}
window.seek = seek;
window.SFX = function () {
  const L = []; SC.forEach((s, k) => { if (k) L.push(["whoosh", s.a]); });
  L.push(["pop", T("h1")], ["thud", W("h1", "तीन")]); ["महाराष्ट्र", "आंध्र"].forEach(w => L.push(["pop", W("h1", w)])); L.push(["pop", W("h1", "महाराष्ट्र", 1)], ["thud", W("h2", "गलत") + .18]);
  ["पिछली", "अगली", "लेटर", "उपरोक्त"].forEach(w => L.push(["tick", W("q1", w)]));
  [0, 1, 2].forEach(i => L.push(["tick", T("q2") + .1 + i * .55]));
  L.push(["thud", W("z2", "छाप") + .27], ["pop", W("z3", "तारीख") - .2], ["ding", W("z3", "चाबी")]);
  L.push(["pop", W("z4", "उसी")], ["ding", W("z4", "खिड़की") + .1]);
  L.push(["shutter", T("a1") + .05], ["whoosh", W("a1", "कल") - .2], ["thud", W("a1", "अवैतनिक") + .18], ["pop", W("a2", "बैरंग") - .3], ["whoosh", T("b1") + .1], ["thud", W("b1", "अवैतनिक") + .18]);
  L.push(["ding", W("c1", "खिड़की")], ["whoosh", W("c1", "डाल") - .4], ["thud", W("c1", "अवैतनिक") + .15]);
  L.push(["tick", W("d1", "A")], ["tick", W("d1", "B")], ["tick", W("d1", "C")], ["ding", W("d1", "D,")]);
  L.push(["riser", W("t1", "C") - .8], ["thud", W("t1", "C")], ["pop", W("k1", "छाप")], ["pop", W("k1", "खिड़की")], ["thud", W("k1", "टूटी")]);
  ["सही", "गलत", "जाल", "trick"].forEach(w => L.push(["pop", W("m1", w)])); L.push(["ding", W("m2", "MOCK")]);
  return L.filter(x => x[1] > 0).map(x => [x[0], Math.round(x[1] * 1000) / 1000]);
};
})();
