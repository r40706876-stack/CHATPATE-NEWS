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
const SID = {sc_hook: "f_hook", sc_q: "s_q", sc_base: "s_base", sc_abc: "s_abc", sc_shift: "s_shift", sc_ans: "s_ans", sc_trap: "f_trap", sc_pyq: "s_pyq", sc_trick: "f_trick", sc_cta: "s_cta"};
const SC = SCENES.map(([n, f], k) => ({n, el: $("#" + SID[n]), a: k ? T(f) - .3 : 0, tr: ["slide", "zoom", "flash"][k % 3]}));

/* pencil ke kaam - is reel me board pencil nahi, sirf paper card */
const OPS = {}; function op(n, t0, d) { OPS[n] = [t0, d]; return t0 + d; }
{ const st = document.getElementById("stars1"); for (let i = 0; i < 24; i++) { const c = document.createElementNS("http://www.w3.org/2000/svg", "circle"); c.setAttribute("cx", (i * 97.3) % 490 + 8); c.setAttribute("cy", (i * 41.7) % 170 + 8); c.setAttribute("r", .8 + (i % 3) * .6); c.setAttribute("fill", "#fff"); c.dataset.k = i; st.appendChild(c); } }
const CAP_HL = ["जाल", "झारखंड", "नहीं", "नाइट", "रात्रि", "बंद", "खुला", "सच", "झूठ", "पाली", "दस", "पाँच", "सीमित", "गलत", "D।", "अधूरा", "सभी", "MOCK", "पोस्टमार्टम", "पूरे", "पूरा"];
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
  pop("#hk1", T("h1") + .02);
  const jA = W("h1", "जाल") - .2; set("#hk2", {opacity: clamp((t - jA) / .06), transform: `scale(${lerp(3, 1, p(t, jA, .25, "out"))})`});
  if (t > jA + .2 && t < jA + .6) { const q = shake(t, jA + .22, .35, 10); set("#f_hook .k2", {translate: `${q[0]}px ${q[1]}px`}); }
  document.querySelectorAll("#hkP .pill").forEach(s => pop(s, W("h1", "झारखंड")));
  pop("#hk3", W("h2", "पोस्टमार्टम") - .2);
  /* sawal */
  const qa = T("q1"); set("#mk1", {opacity: p(t, qa - .1, .3), transform: `translateY(${(1 - p(t, qa - .1, .5, "back")) * 60}px)`});
  [["a", W("q1", "रविवार")], ["b", W("q1", "राष्ट्रीय")], ["c", W("q1", "बाकी")], ["d", W("q1", "पूरे")]].forEach(([x, a]) => { const k = p(t, a - .1, .35, "back");
    set("#o1" + x, {opacity: clamp((t - a + .1) / .08), transform: `translateX(${(1 - k) * -30}px)`}); });
  const ul = W("q2", "नहीं") - .2; $("#ul path").setAttribute("stroke-dashoffset", 110 * (1 - p(t, ul, .4)));
  set("#snahi", {color: t > ul ? "#f87171" : "#fff"});
  const ta = W("q2", "तीन"), left = clamp(3 - (t - ta) * (3 / Math.max(1.4, END("q2") - ta + .2)), 0, 3);
  set("#tm3", {opacity: p(t, ta - .1, .2), transform: `scale(${Math.max(0, p(t, ta - .1, .4, "back"))})`});
  $("#tmN").textContent = Math.ceil(left) || 0; $("#tmR").setAttribute("stroke-dashoffset", 314 * (1 - left / 3));
  /* din-raat */
  const z0 = T("z1"), night = p(t, z0 + .3, 1.6, "inout");
  const sky = (a, b) => `rgb(${lerp(a[0], b[0], night) | 0},${lerp(a[1], b[1], night) | 0},${lerp(a[2], b[2], night) | 0})`;
  $("#sky").style.background = `linear-gradient(180deg,${sky([125, 190, 255], [11, 16, 41])},${sky([254, 230, 160], [36, 42, 92])})`;
  $("#moon1").setAttribute("opacity", night);
  document.querySelectorAll("#stars1 circle").forEach(c => c.setAttribute("opacity", night * (.4 + .6 * Math.abs(Math.sin(t * 1.7 + +c.dataset.k)))));
  $("#bnd").setAttribute("opacity", p(t, W("z1", "बंद"), .3));
  const lit = t > W("z2", "नाइट") ? 1 : 0;
  document.querySelectorAll(".npw").forEach(w => w.setAttribute("fill", lit ? "#ffcf4a" : "#374151"));
  $("#npS").setAttribute("fill", lit ? "#c81e1e" : "#374151"); $("#npT").setAttribute("fill", lit ? "#fff" : "#9ca3af");
  $("#khl").setAttribute("opacity", p(t, W("z2", "बंद") + .1, .3));
  document.querySelectorAll("#dP .pill").forEach((s, i) => pop(s, W("z2", ["रविवार", "राष्ट्रीय", "बाकी"][i])));
  term("#tm_base", W("z2", "नाइट"));
  /* abc */
  ["a", "b", "c"].forEach((x, i) => { const a = W("a1", ["A,", "B,", "C,"][i]); set("#o2" + x + " .tg", {opacity: clamp((t - a) / .08), transform: `scale(${Math.max(0, p(t, a, .35, "back"))})`});
    set("#o2" + x, {background: t > a ? "rgba(74,222,128,.14)" : "rgba(255,255,255,.1)"}); });
  set("#mk2", {transform: `translateY(${(1 - p(t, T("a1") - .2, .5, "back")) * 50}px)`});
  const jh = W("a1", "झूठ") - .3; set("#jhooth", {opacity: clamp((t - jh) / .08), transform: `scale(${Math.max(0, p(t, jh, .4, "back"))})`});
  /* paali */
  pop("#shS", W("z3", "पाली") - .3);
  set("#bar24", {opacity: p(t, T("z3") + .2, .3)}); document.querySelectorAll(".hr").forEach(h => h.style.opacity = p(t, T("z3") + .3, .3));
  const bw = p(t, W("z3", "दस") - .1, .9, "inout"); $("#band").style.width = 29.17 * bw + "%"; set("#bandT", {opacity: p(t, W("z3", "पाँच"), .3)});
  [["#sv1", W("z4", "बाँटना")], ["#sv2", W("z4", "मनी")], ["#sv3", W("z4", "बचत")]].forEach(([s, a]) => { const k = p(t, a - .1, .4, "back"); set(s, {opacity: clamp((t - a + .1) / .08), transform: `translateX(${(1 - k) * 80}px)`}); });
  term("#tm_shift", W("z4", "सीमित"));
  /* jawab */
  set("#mk3", {transform: `translateY(${(1 - p(t, T("d1") - .2, .5, "back")) * 50}px)`});
  const dg = W("d1", "गलत"); set("#o3d", {background: t > dg ? "rgba(220,38,38,.35)" : "rgba(255,255,255,.1)", borderColor: t > dg ? "#f87171" : "rgba(255,255,255,.18)", transform: `scale(${1 + .05 * Math.max(0, Math.sin(clamp((t - dg) / .5) * Math.PI))})`});
  set("#o3t", {opacity: clamp((t - dg) / .08), transform: `scale(${Math.max(0, p(t, dg, .35, "back"))})`});
  if (t > dg + .05 && t < dg + .5) add(shake(t, dg + .08, .3, 6));
  pop("#ansB", W("d1", "D।") - .1);
  /* jaal */
  pop("#tp1", T("t1")); const tp = W("t1", "खुला", -1) - .1; set("#tp2", {opacity: clamp((t - tp) / .06), transform: `scale(${lerp(2.6, 1, p(t, tp, .25, "out"))})`});
  if (t > tp + .2 && t < tp + .6) { const q = shake(t, tp + .22, .35, 10); set("#f_trap .k2", {translate: `${q[0]}px ${q[1]}px`}); }
  /* pyq */
  pop("#bnp", T("p1") - .1);
  card("cp", T("p1") + .05, [["pa", W("p1", "किन") - .1], ["pb", W("p1", "किन") + .05], ["pc", W("p1", "किन") + .2], ["pd", W("p1", "किन") + .35]], "stp", W("p1", "झारखंड") + .4);
  if (t > W("p1", "झारखंड") + .55) add(shake(t, W("p1", "झारखंड") + .6, .3, 6));
  set("#pd", {background: `rgba(22,163,74,${.18 * p(t, W("p1", "सभी") - .1, .3)})`});
  /* trick */
  pop("#tk1", T("k1")); const tk = W("k1", "खुला"); set("#tk2", {opacity: clamp((t - tk) / .06), transform: `scale(${lerp(2.4, 1, p(t, tk, .25, "out"))})`});
  pop("#tc1", W("k1", "दस") - .1);
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
  L.push(["pop", T("h1")], ["thud", W("h1", "जाल")], ["pop", W("h1", "झारखंड")], ["pop", W("h2", "पोस्टमार्टम")]);
  ["रविवार", "राष्ट्रीय", "बाकी", "पूरे"].forEach(w => L.push(["tick", W("q1", w)]));
  L.push(["swish", W("q2", "नहीं") - .2]); [0, 1, 2].forEach(i => L.push(["tick", W("q2", "तीन") + i * .5]));
  L.push(["thud", W("z1", "बंद")], ["ding", W("z2", "नाइट")]); ["रविवार", "राष्ट्रीय", "बाकी"].forEach(w => L.push(["pop", W("z2", w)]));
  ["A,", "B,", "C,"].forEach(w => L.push(["tick", W("a1", w)])); L.push(["pop", W("a1", "झूठ") - .3]);
  L.push(["whoosh", W("z3", "दस") - .1], ["pop", W("z3", "पाँच")]); ["बाँटना", "मनी", "बचत"].forEach(w => L.push(["thud", W("z4", w)]));
  L.push(["thud", W("d1", "गलत") + .05], ["ding", W("d1", "D।")]);
  L.push(["riser", W("t1", "खुला", -1) - .9], ["thud", W("t1", "खुला", -1)], ["thud", W("p1", "झारखंड") + .6], ["ding", W("p1", "सभी")]);
  L.push(["thud", W("k1", "खुला")], ["pop", W("k1", "दस")]);
  ["सही", "गलत", "जाल", "trick"].forEach(w => L.push(["pop", W("m1", w)])); L.push(["ding", W("m2", "MOCK")]);
  return L.filter(x => x[1] > 0).map(x => x[0] === "swish" ? ["whoosh", x[1]] : x).map(x => [x[0], Math.round(x[1] * 1000) / 1000]);
};
})();
