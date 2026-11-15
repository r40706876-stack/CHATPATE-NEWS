/* POSTAL WALA - Clause 9 (पूर्व भुगतान) poora video. Samay asli awaaz (window.CUES) se. */
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
const SID = {sc_open: "s_open", sc_word: "s_word", sc_types: "s_types", sc_lane: "s_lane", sc_q1: "s_q1", sc_myth: "f_myth", sc_hold: "s_hold", sc_q2: "s_q2", sc_round: "s_round", sc_q3: "s_q3", sc_cmp: "s_cmp", sc_end: "f_end"};
const SC = SCENES.map(([n, f], k) => ({n, el: $("#" + SID[n]), a: k ? T(f) - .3 : 0, tr: ["slide", "zoom", "flash"][k % 3]}));

/* pencil ke kaam */
const OPS = {}; function op(n, t0, d) { OPS[n] = [t0, d]; return t0 + d; }
let e;
e = op("env0", T("o1") + .05, .8); e = op("nost", e + .02, .45);
e = op("bub", Math.max(e + .05, W("o1", "बिना") - .3), .6); e = op("bubT", e + .02, .45); e = op("bubT2", Math.max(e + .02, W("o1", "पक्की") - .2), .45);
op("envL", Math.max(e + .05, W("o1", "क्योंकि")), .5);
e = op("bag", T("m2") + .9, .8); op("bagT", e + .02, .4);
e = op("desk", T("m3") + .05, .5); op("deskT", e + .02, .35);
op("ringq1", W("q1b", "जवाब") + .05, .45); op("strq1", W("q1b", "दोनों") + .05, .3);
op("strq2", W("q2b", "गलत") - .2, .3); op("ringq2", W("q2b", "सही") + .05, .45);
op("ringq3", W("q3", "जवाब") + .05, .45);
const CAP_HL = ["बैरंग", "टिकट", "पूरा", "पूरे", "सबसे", "पहली", "सुरक्षा", "नहीं", "रोका", "बाकी", "विशेष", "सामान्य", "मध्य", "प्रदेश", "गुजरात", "झारखंड", "Fully", "prepaid", "किराया", "पूर्व", "भुगतान", "मिथक", "उल्टी", "रफ़्तार", "दोनों", "गलत"];
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
  ring("ringq1", "q1a"); ring("ringq2", "q2b"); ring("ringq3", "q3a"); strike("strq1", "q1c"); strike("strq2", "q2a");
  const tk = $("#tk9"); for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; mk("line", {x1: Math.sin(a) * 44, y1: -Math.cos(a) * 44, x2: Math.sin(a) * (i % 3 ? 39 : 34), y2: -Math.cos(a) * (i % 3 ? 39 : 34), stroke: "#1e3a8a", "stroke-width": i % 3 ? 2 : 4}, tk); }
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

  /* open */
  const smA = T("o2") + .1; set("#stMyth", {opacity: clamp((t - smA) / .06), transform: `rotate(-8deg) scale(${lerp(2.6, 1, p(t, smA, .2, "out"))})`});
  if (t > smA + .15) add(shake(t, smA + .2, .3, 6));
  const c9 = W("o2", "Clause") - .1; set("#cl9", {opacity: clamp((t - c9) / .12), transform: `scale(${Math.max(0, p(t, c9, .5, "back"))})`});
  set("#s_open .bsvg", {opacity: 1 - .75 * p(t, c9 - .1, .4)}); set("#stMyth", {filter: t > c9 ? "opacity(.35)" : "none"});
  /* word */
  pop("#wT", T("a1") + .05);
  [["#wc1", W("a1", "बस") - .1], ["#wc2", W("a1", "वैसे")]].forEach(([s, a], i) => { const k = p(t, a, .5, "back"); set(s, {opacity: clamp((t - a) / .1), transform: `translateY(${(1 - k) * 50}px) rotate(${(i ? 1 : -1) * lerp(10, 3, k)}deg)`}); });
  pop("#wEq", W("a1", "वैसे") + .3);
  const pre = T("a2") + .05; set("#wPre", {opacity: clamp((t - pre) / .1), transform: `translateY(${(1 - p(t, pre, .45, "back")) * 40}px)`});
  set("#wc1,#wc2", {}); set("#wc2", {boxShadow: t > W("a2", "पूरा") ? "0 0 0 6px #4ade80,0 16px 34px rgba(0,0,0,.4)" : "0 16px 34px rgba(0,0,0,.4)"});
  term("#tm_word", W("a2", "पूर्व"));
  /* types */
  pop("#tyT", T("a3") + .05);
  [["#e1", "#l1", W("a3", "पूरा")], ["#e2", "#l2", W("a4", "लगा")], ["#e3", "#l3", W("a4", "कम")]].forEach(([en, ln, a]) => {
    const k = p(t, a - .15, .45, "back"); set(en, {opacity: clamp((t - a + .15) / .1), transform: `translateY(${(1 - k) * -60}px) rotate(${(1 - k) * -12}deg)`});
    set(ln, {opacity: p(t, a + .2, .3), transform: `translateY(${(1 - p(t, a + .2, .4, "out")) * 12}px)`}); });
  const bar = W("a4", "बैरंग"); set("#l2", {transform: t > bar ? `scale(${1 + .15 * Math.max(0, Math.sin(clamp((t - bar) / .5) * Math.PI))})` : $("#l2").style.transform});
  /* lane */
  const la = T("r1"), lb = W("r2", "बाँट");
  const vx = lerp(-180, 300, p(t, W("r1", "सबसे") - .2, 1.6, "inout")), vx2 = lerp(vx, 330, p(t, T("r2"), .6, "inout"));
  $("#van9").setAttribute("transform", `translate(${t < T("r2") ? vx : vx2},250)`);
  $("#vEnv").setAttribute("transform", `translate(${46 + p(t, lb - .3, .5, "inout") * 90},${-62 + p(t, lb - .3, .5, "inout") * 150})`);
  $("#speedL").setAttribute("opacity", (t > W("r1", "सबसे") && t < W("r1", "सबसे") + 1.5) ? 1 : 0); $("#speedL").setAttribute("transform", `translate(${vx - 4},250)`);
  pop("#done9", lb + .3); term("#tm_lane", W("r1", "पहली"));
  /* q1 */
  pop("#bn1", T("q1") - .1, T("q1b"));
  card("cq1", T("q1") + .05, opts4("q1", "q1", "किन"), "stq1", W("q1", "मध्य") + .5);
  if (t > W("q1", "मध्य") + .65) add(shake(t, W("q1", "मध्य") + .7, .3, 6));
  set("#q1a", {background: `rgba(22,163,74,${.16 * p(t, OPS.ringq1[0] + .4, .3)})`});
  set("#q1c", {color: t > OPS.strq1[0] + .3 ? "#991b1b" : ""});
  /* myth (bada sawal) */
  const mq = T("m1") + .05;
  set("#mq1", {opacity: clamp((t - mq) / .1), transform: `scale(${lerp(2, 1, p(t, mq, .35, "back"))})`});
  const mq2 = W("m1", "ज़्यादा") - .05; set("#mq2", {opacity: clamp((t - mq2) / .06), transform: `scale(${lerp(3, 1, p(t, mq2, .25, "out"))})`});
  if (t > mq2 + .2 && t < mq2 + .7) { const q = shake(t, mq2 + .22, .35, 10); set("#f_myth .k2", {translate: `${q[0]}px ${q[1]}px`}); }
  const bg = W("m1", "बैरंग"); set("#mEnv", {opacity: p(t, bg - .1, .3), transform: `translateY(${(1 - p(t, bg - .1, .5, "back")) * 60}px) rotate(${Math.sin(t * 3) * 4}deg)`});
  /* hold */
  const nA = T("m2") - .05; set("#nahi", {opacity: clamp((t - nA) / .05) * (1 - p(t, nA + .9, .3)), transform: `scale(${lerp(3, 1, p(t, nA, .22, "out"))})`});
  if (t > nA + .2 && t < nA + .6) add(shake(t, nA + .22, .35, 10));
  pop("#ch_hold", nA + 1.0); set("#ch_hold", {transform: `translateX(${(1 - p(t, nA + 1, .4, "back")) * -40}px)`});
  const into = W("m2", "थैले") - .3;
  [["#h3", 0], ["#h1", .15], ["#h2", .3]].forEach(([s, dl]) => { const k = p(t, into + dl, .55, "inout"); const kk = p(t, W("m3", "रोका") - .2, .7, "inout");
    if (s === "#h2") set(s, {opacity: p(t, T("m2") + .6, .3), transform: `translate(${lerp(0, -30, k) + kk * 190}px,${lerp(0, 230, k) - Math.sin(kk * Math.PI) * 80 + kk * 40}px) scale(.6)`});
    else set(s, {opacity: p(t, T("m2") + .6, .3) * (1 - .6 * k), transform: `translate(${lerp(0, 40, k)}px,${lerp(0, 240, k)}px) scale(${.6 - .25 * k})`}); });
  const du = W("m3", "हिसाब"); pop("#due", du); $("#dueN").textContent = t > du + .3 && t < du + 1.3 ? ["₹ ?", "₹ ..", "₹ ?"][Math.floor((t - du) * 6) % 3] : "₹ ?";
  term("#tm_hold", W("m3", "शुल्क"));
  /* q2 */
  card("cq2", T("q2") - .05, opts4("q2", "q2", "कैसी"), "stq2", W("q2", "गुजरात") + .5);
  if (t > W("q2", "गुजरात") + .65) add(shake(t, W("q2", "गुजरात") + .7, .3, 6));
  const tpA = OPS.strq2[0] + .3, tp = p(t, tpA, .35, "out");
  set("#tp2", {opacity: clamp((t - tpA) / .08) * (1 - p(t, OPS.ringq2[0] - .1, .3)), transform: `rotate(-7deg) translateX(${(1 - tp) * -560}px)`});
  set("#q2a", {color: t > tpA ? "#991b1b" : "", background: `rgba(220,38,38,${.12 * p(t, tpA, .3)})`});
  set("#q2b", {background: `rgba(22,163,74,${.16 * p(t, OPS.ringq2[0] + .4, .3)})`});
  /* round */
  const r0 = T("d1"); const hrs = 8 + 9 * p(t, r0, END("d4") - r0, "inout");
  $("#hh9").setAttribute("transform", `rotate(${hrs * 30})`); $("#mh9").setAttribute("transform", `rotate(${hrs * 360})`);
  $("#clk9").setAttribute("transform", `translate(254,78) scale(${Math.max(.01, p(t, r0, .5, "back"))})`);
  pop("#fere", W("d1", "बार") - .2);
  [["#rS", W("d2", "कुछ") - .1, -1], ["#rG", W("d3", "एक") - .1, 1]].forEach(([s, a, dir]) => { const k = p(t, a, .5, "back");
    set(s, {opacity: clamp((t - a) / .1), transform: `translateX(${(1 - k) * dir * 200}px)`}); });
  const b0 = T("d4"), toS = p(t, b0 + .1, .6, "inout"), bounce = p(t, W("d4", "नहीं") - .05, .5, "out"), toG = p(t, W("d4", "सामान्य") - .3, .8, "inout");
  let bx = lerp(0, -110, toS) + bounce * 110, by = lerp(0, -170, toS) * (1 - bounce) + bounce * -10;
  if (toG > 0) { bx = lerp(bx, 150, toG); by = lerp(by, -170, toG); }
  set("#bEnv", {opacity: p(t, b0 - .2, .3), transform: `translate(${bx}px,${by}px) scale(.62) rotate(${-bounce * (1 - toG) * 10}deg)`});
  pop("#bX", W("d4", "नहीं"), W("d4", "सामान्य")); pop("#bWait", W("d4", "रुकती") - .1, W("d4", "सामान्य")); pop("#bOk", W("d4", "बँटती"));
  if (t > W("d4", "नहीं") + .05) add(shake(t, W("d4", "नहीं") + .1, .3, 5));
  set("#rS", {filter: t > W("d4", "नहीं") && t < W("d4", "सामान्य") ? "brightness(.8)" : "none"});
  set("#rG", {boxShadow: t > W("d4", "बँटती") ? "0 0 0 6px #4ade80,0 14px 30px rgba(0,0,0,.35)" : "0 14px 30px rgba(0,0,0,.35)"});
  /* q3 */
  pop("#bn3", T("q3") - .1, W("q3", "जवाब"));
  card("cq3", T("q3") + .05, opts4("q3", "q3", "कब"), "stq3", W("q3", "झारखंड") + .5);
  if (t > W("q3", "झारखंड") + .65) add(shake(t, W("q3", "झारखंड") + .7, .3, 6));
  set("#q3a", {background: `rgba(22,163,74,${.16 * p(t, OPS.ringq3[0] + .4, .3)})`});
  /* cmp */
  const ca = T("s1");
  set("#hL", {transform: `translateX(${(1 - p(t, ca, .5, "out")) * -260}px)`}); set("#hR", {transform: `translateX(${(1 - p(t, ca + .15, .5, "out")) * 260}px)`});
  set("#vs", {transform: `scale(${Math.max(0, p(t, ca + .5, .45, "back"))}) rotate(${(1 - p(t, ca + .5, .5)) * 180}deg)`});
  [["#cA1", W("s1", "सबसे")], ["#cA2", W("s1", "जल्दी")], ["#cB1", W("s2", "सुरक्षा")], ["#cB2", W("s2", "रुक")], ["#cB3", W("s2", "इंतज़ार") - .2]].forEach(([s, a]) => {
    const k = p(t, a - .1, .4, "back"); set(s, {opacity: clamp((t - a + .1) / .08), transform: `scale(${Math.max(0, k)})`}); });
  /* end */
  const ea = T("e1") + .05; set("#myB", {opacity: clamp((t - ea) / .1) * (1 - p(t, T("k1") - .2, .3)), transform: `translateY(${(1 - p(t, ea, .5, "back")) * 50}px)`});
  const ms = W("e1", "उल्टी"); set("#stMy2", {opacity: clamp((t - ms) / .06), transform: `translateX(-50%) rotate(-10deg) scale(${lerp(2.8, 1, p(t, ms, .2, "out"))})`});
  if (t > ms + .15 && t < ms + .6) { const q = shake(t, ms + .2, .35, 9); set("#myB", {translate: `${q[0]}px ${q[1]}px`}); }
  const tzA = T("e2") + .05; set("#tz", {opacity: clamp((t - tzA) / .1) * (1 - p(t, T("k1") - .2, .3)), transform: `translateY(${(1 - p(t, tzA, .5, "back")) * 80}px)`});
  pop("#tk1", T("k1")); const t2 = W("k1", "पूरा"); set("#tk2", {opacity: clamp((t - t2) / .06), transform: `scale(${lerp(2.6, 1, p(t, t2, .25, "out"))})`});
  pop("#trN", T("k2") + .05);
  document.querySelectorAll("#trP .pill").forEach((s, i) => pop(s, T("k2") + .3 + i * .15));
  const fo = W("k2", "अगला"); set("#fol", {opacity: clamp((t - fo) / .1), transform: `scale(${Math.max(0, p(t, fo, .4, "back")) * (1 + .04 * Math.sin(t * 8))})`});

  set("#stage", {transform: `translate(${sk[0]}px,${sk[1]}px)`});
  capChunks.forEach(c => { const a = wt(c.id, c.k0) - .08, nx = c.k0 + c.n < TX[c.id].split(/\s+/).length ? wt(c.id, c.k0 + c.n) - .08 : END(c.id) + .1;
    const vis = t >= a && t < nx; c.el.style.opacity = vis ? 1 : 0; if (!vis) return;
    [...c.el.children].forEach((w, j) => { const ti = wt(c.id, c.k0 + j) - .06, k = p(t, ti, .28, "back");
      w.style.opacity = clamp((t - ti) / .07); w.style.transform = `translateY(${(1 - k) * 20}px) scale(${.75 + .25 * Math.max(0, k)})`; }); });
}
window.seek = seek;
window.SFX = function () {
  const L = []; SC.forEach((s, k) => { if (k) L.push(["whoosh", s.a]); });
  L.push(["thud", T("o2") + .3], ["pop", W("o2", "Clause")], ["pop", W("a1", "बस")], ["pop", W("a1", "वैसे")], ["ding", W("a2", "पूरा")]);
  L.push(["pop", W("a3", "पूरा")], ["pop", W("a4", "लगा")], ["pop", W("a4", "कम")]);
  L.push(["whoosh", W("r1", "सबसे")], ["ding", W("r2", "बाँट") + .3]);
  L.push(["thud", W("q1", "मध्य") + .7], ["tick", OPS.strq1[0]], ["ding", OPS.ringq1[0] + .4]);
  L.push(["pop", T("m1") + .05], ["riser", W("m1", "ज़्यादा") - .8], ["thud", W("m1", "ज़्यादा")]);
  L.push(["thud", T("m2")], ["whoosh", W("m2", "थैले") - .3], ["whoosh", W("m3", "रोका") - .2], ["tick", W("m3", "हिसाब") + .3], ["tick", W("m3", "हिसाब") + .5]);
  L.push(["thud", W("q2", "गुजरात") + .7], ["thud", OPS.strq2[0] + .35], ["ding", OPS.ringq2[0] + .4]);
  for (let x = T("d1") + .4; x < END("d1"); x += .5) L.push(["tick", x]);
  L.push(["whoosh", W("d2", "कुछ")], ["whoosh", W("d3", "एक")], ["thud", W("d4", "नहीं") + .05], ["ding", W("d4", "बँटती")]);
  L.push(["thud", W("q3", "झारखंड") + .7], ["ding", OPS.ringq3[0] + .4]);
  L.push(["whoosh", T("s1")], ["pop", W("s1", "सबसे")], ["pop", W("s1", "जल्दी")], ["pop", W("s2", "सुरक्षा")], ["pop", W("s2", "रुक")], ["pop", W("s2", "इंतज़ार")]);
  L.push(["thud", W("e1", "उल्टी") + .18], ["shutter", T("e2") + .05], ["riser", W("k1", "पूरा") - .8], ["thud", W("k1", "पूरा")], ["pop", W("k2", "अगला")]);
  return L.filter(x => x[1] > 0).map(x => [x[0], Math.round(x[1] * 1000) / 1000]);
};
})();
