/* POSTAL WALA - Clause 8 (डाकघर की छुट्टियाँ) poora video. Samay asli awaaz (window.CUES) se. */
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
const SID = {sc_open: "s_open", sc_q1: "s_q1", sc_num: "s_num", sc_nat: "s_nat", sc_fest: "s_fest", sc_q2: "s_q2", sc_cmp: "s_cmp",
  sc_circ: "s_circ", sc_q3: "s_q3", sc_book: "s_book", sc_rec: "s_rec", sc_trick: "f_trick"};
const SC = SCENES.map(([n, f], k) => ({n, el: $("#" + SID[n]), a: k ? T(f) - .3 : 0, tr: ["slide", "zoom", "flash"][k % 3]}));

/* pencil ke kaam */
const OPS = {}; function op(n, t0, d) { OPS[n] = [t0, d]; return t0 + d; }
let e;
e = op("cal", T("o1") + .05, .8); e = op("calT", Math.max(e + .02, W("o1", "पैंसठ") - .3), .5); op("calT2", e + .02, .25);
e = op("po", Math.max(e + .3, W("o1", "डाकघर") - .4), .7); op("poT", e + .02, .25);
op("qT", Math.max(e + .3, W("o1", "बंद") - .2), .6);
op("ringq1", W("q1", "जवाब") + .05, .45); op("ringq2", W("q2", "जवाब") + .05, .45); op("ringq3", W("q3", "जवाब") + .05, .45);

const CAP_HL = ["सत्रह", "चौदह", "तीन", "ग्यारह", "सर्किल", "पक्की", "राष्ट्रीय", "धार्मिक", "रक्षाबंधन", "वैकल्पिक", "Optional", "दिल्ली", "बिहार", "हरियाणा", "राजस्थान", "जम्मू-कश्मीर", "तेलंगाना", "जाल", "Clause", "आठ", "सभी", "हिंदू", "मुस्लिम", "ईसाई", "सिख", "बौद्ध", "जैन", "पुरानी"];
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
  function ring(n, id) { const b = rel(id), ink = $("#" + id).closest(".sc").querySelector(".ink"); const cx = b.x + 104, cy = b.y + b.h / 2 + 12, rx = 112, ry = b.h / 2 + 7;
    const el = mk("path", {d: `M${cx - rx + 6},${cy - ry + 4} A${rx},${ry} 0 1,0 ${cx + rx},${cy + 2} A${rx},${ry} 0 0,0 ${cx - rx + 18},${cy - ry - 2}`, fill: "none", stroke: "#16a34a", "stroke-width": 4.2, "stroke-linecap": "round", "data-card": b.card}, ink);
    const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L; ops[n].paths.push({el, L, at: 0, svg: ink}); ops[n].len = L; }
  ring("ringq1", "q1b"); ring("ringq2", "q2d"); ring("ringq3", "q3d");
  /* trick ke ank */
  const dg = $("#digs");
  [["2", "हिंदू", "#ea580c"], ["4", "मुस्लिम", "#15803d"], ["2", "ईसाई", "#1d4ed8"], ["1", "सिख", "#7c3aed"], ["1", "बौद्ध", "#7c3aed"], ["1", "जैन", "#7c3aed"]].forEach(([n, l, c]) => {
    const d = document.createElement("div"); d.className = "dg"; d.style.cssText = `display:inline-block;width:76px;margin:0 2px;opacity:0;text-align:center`;
    d.innerHTML = `<div style="font:800 70px/1 Poppins;color:#fff;text-shadow:0 0 24px ${c}">${n}</div><div style="font:800 16px/30px 'Baloo 2';color:#fff;background:${c};border-radius:15px;margin-top:8px">${l}</div>`; dg.appendChild(d); });
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
  const qa = W("o2", "नंबर"); $("#qmark").setAttribute("opacity", clamp((t - qa) / .1)); $("#qmark").setAttribute("transform", `translate(440,160) scale(${Math.max(.01, p(t, qa, .45, "back")) * (1 + .06 * Math.sin(t * 6))}) translate(-440,-160)`);
  const c8 = p(t, W("o3", "Clause", -1) - .1, .5, "back"); set("#cl8", {opacity: clamp((t - W("o3", "Clause", -1) + .1) / .12), transform: `scale(${Math.max(0, c8)})`});
  if (t > W("o3", "Clause", -1) + .2) add(shake(t, W("o3", "Clause", -1) + .25, .3, 5));
  set("#s_open .bsvg", {opacity: 1 - .75 * p(t, W("o3", "Clause", -1) - .2, .4)});
  /* q1 */
  pop("#bn1", T("q1") - .1, W("q1", "जवाब"));
  card("cq1", T("q1") + .05, opts4("q1", "q1", "किस"), "stq1", W("q1", "दिल्ली") + .1);
  if (t > W("q1", "दिल्ली") + .25) add(shake(t, W("q1", "दिल्ली") + .3, .3, 6));
  set("#q1b", {background: `rgba(22,163,74,${.16 * p(t, OPS.ringq1[0] + .4, .3)})`});
  pop("#pl_bh", W("q1", "बिहार"));
  /* num */
  const nA = W("n1", "सत्रह") - .05, nk = p(t, nA, .25, "out");
  set("#n17", {opacity: clamp((t - nA) / .05) * (1 - p(t, W("n2", "बाँटो"), .3)), transform: `scale(${lerp(3, 1, nk)})`});
  if (t > nA + .2) add(shake(t, nA + .22, .35, 9));
  pop("#n17t", nA + .3, W("n2", "बाँटो"));
  const sp = W("n2", "बाँटो");
  set("#p14", {opacity: clamp((t - sp) / .1), transform: `translateX(${(1 - p(t, sp, .5, "back")) * 120}px)`});
  set("#p3", {opacity: clamp((t - sp) / .1), transform: `translateX(${(1 - p(t, sp, .5, "back")) * -120}px)`});
  set("#p14 .l", {opacity: p(t, W("n2", "पक्की"), .3)}); set("#p3 .l", {opacity: p(t, W("n2", "सर्किल"), .3)});
  set("#p14 .n", {transform: `scale(${1 + .15 * Math.max(0, Math.sin(clamp((t - W("n2", "चौदह")) / .5) * Math.PI))})`});
  set("#p3 .n", {transform: `scale(${1 + .2 * Math.max(0, Math.sin(clamp((t - W("n2", "तीन")) / .5) * Math.PI))})`});
  pop("#plus", sp + .4); pop("#eq", W("n3", "मतलब"));
  if (t > W("n3", "सत्रह")) $("#eq").textContent = "17 = 14 + 3"; else $("#eq").textContent = "सर्किल = डाक विभाग का बड़ा इलाका";
  term("#tm_num", nA + .6);
  /* nat */
  pop("#natT", T("r1") + .1);
  [["k1", W("r2", "छब्बीस")], ["k2", W("r2", "पंद्रह")], ["k3", W("r2", "दो")]].forEach(([id, a]) => { const k = p(t, a - .1, .45, "out");
    set("#" + id, {opacity: clamp((t - a + .1) / .1), transform: `rotateX(${(1 - k) * -90}deg) translateY(${Math.sin(clamp((t - a) / .6) * Math.PI) * -10}px)`}); });
  pop("#natB", END("r2") - .3);
  /* fest */
  pop("#festT", T("f1") + .05);
  const tiles = [["g1", 0, W("f2", "दशहरा")], ["g1", 1, W("f2", "दिवाली")], ["g2", 0, W("f2", "ईद-उल")], ["g2", 1, W("f2", "बकरीद")], ["g2", 2, W("f2", "मुहर्रम")], ["g2", 3, W("f2", "ईद-ए")],
    ["g3", 0, W("f3", "क्रिसमस")], ["g3", 1, W("f3", "फ्राइडे")], ["g4", 0, W("f3", "नानक")], ["g4", 1, W("f3", "पूर्णिमा")], ["g4", 2, W("f3", "महावीर")]];
  const grpA = {g1: W("f2", "हिंदू"), g2: W("f2", "मुस्लिम"), g3: W("f3", "ईसाई"), g4: W("f3", "तीन")};
  for (const g in grpA) set("#" + g, {opacity: p(t, grpA[g] - .1, .3), transform: `translateX(${(1 - p(t, grpA[g] - .1, .4, "out")) * -60}px)`});
  let cnt = 0;
  tiles.forEach(([g, i, a]) => { const el = $("#" + g).querySelectorAll(".tile")[i]; const k = p(t, a - .05, .35, "back"); if (t > a) cnt++;
    set(el, {opacity: clamp((t - a + .05) / .08), transform: `scale(${Math.max(0, k)})`}); });
  $("#cnt11").firstChild.nodeValue = cnt;
  set("#cnt11", {transform: `scale(${1 + .12 * Math.max(0, Math.sin(clamp((t - (tiles.find(x => x[2] > t - .3) || [0, 0, 0])[2]) / .3) * Math.PI))})`});
  const fs = T("f4") + .1; pop("#festSum", fs);
  ["g1", "g2", "g3", "g4"].forEach((g, i) => { const gl = W("f4", ["दो", "चार", "दो", "एक"][i], i === 2 ? 1 : 0);
    set("#" + g + " .g", {boxShadow: t > gl && t < gl + .6 ? "0 0 0 5px #ffd84a" : "none"}); });
  /* q2 */
  pop("#bn2", T("q2") - .1, W("q2", "तीनों"));
  card("cq2", T("q2") + .05, opts4("q2", "q2", "गणतंत्र"), "stq2", W("q2", "हरियाणा") + .4);
  if (t > W("q2", "हरियाणा") + .55) add(shake(t, W("q2", "हरियाणा") + .6, .3, 6));
  set("#q2d", {background: `rgba(22,163,74,${.16 * p(t, OPS.ringq2[0] + .4, .3)})`});
  /* cmp */
  const ca = T("t1");
  set("#hL", {transform: `translateX(${(1 - p(t, ca, .5, "out")) * -260}px)`}); set("#hR", {transform: `translateX(${(1 - p(t, ca + .15, .5, "out")) * 260}px)`});
  set("#vs", {transform: `scale(${Math.max(0, p(t, ca + .5, .45, "back"))}) rotate(${(1 - p(t, ca + .5, .5)) * 180}deg)`});
  pop("#cmpQ", W("t1", "कौन"));
  pop("#vL1", W("t2", "बुद्ध")); pop("#vL2", W("t2", "महावीर")); pop("#vL3", W("t2", "गुड"));
  const rb = W("t2", "रक्षाबंधन", -1); const rk = p(t, rb - .1, .3, "out");
  set("#vR1", {opacity: clamp((t - W("t2", "रक्षाबंधन")) / .1), transform: `scale(${Math.max(0, p(t, W("t2", "रक्षाबंधन"), .4, "back")) * (t > rb ? 1 + .06 * Math.sin((t - rb) * 10) * Math.exp(-(t - rb) * 2) : 1)})`});
  const sa = W("t2", "जवाब"); set("#stcmp", {opacity: clamp((t - sa) / .06), transform: `translateX(-50%) rotate(-9deg) scale(${lerp(2.6, 1, p(t, sa, .2, "out"))})`});
  if (t > sa + .15) add(shake(t, sa + .2, .3, 6));
  /* circ */
  const fcs = [["fc1", 30, 420], ["fc2", 189, 420], ["fc3", 348, 420], ["fc4", 110, 480], ["fc5", 268, 480]];
  const pick = [W("c2", "होली"), W("c2", "गणेश"), W("c2", "महाशिवरात्रि")]; const slots = [[44, 150], [189, 150], [334, 150]];
  fcs.forEach(([id, x, y], i) => { const show = T("c1") + .4 + i * .12; let X = x, Y = y;
    if (i < 3) { const k = p(t, pick[i] - .1, .55, "inout"); X = lerp(x, slots[i][0], k); Y = lerp(y, slots[i][1], k) - Math.sin(k * Math.PI) * 60; }
    set("#" + id, {opacity: p(t, show, .3) * (i >= 3 ? 1 - .5 * p(t, pick[2], .4) : 1), left: X + "px", top: Y + "px", transform: `scale(${Math.max(0, p(t, show, .4, "back"))})`}); });
  term("#tm_circ", W("c2", "Optional"));
  /* q3 */
  card("cq3", T("q3") - .05, opts4("q3", "q3", "होली"), "stq3", W("q3", "जम्मू") + .5);
  if (t > W("q3", "जम्मू") + .65) add(shake(t, W("q3", "जम्मू") + .7, .3, 6));
  set("#q3d", {background: `rgba(22,163,74,${.16 * p(t, OPS.ringq3[0] + .4, .3)})`});
  const mt = p(t, T("q4") + .05, .45, "back"); set("#mn_tl", {opacity: clamp((t - T("q4") - .05) / .1), transform: `translateY(${(1 - mt) * 120}px)`});
  set("#mn_tl .s", {opacity: p(t, W("q4", "सत्रह"), .2), transform: `scale(${Math.max(0, p(t, W("q4", "सत्रह"), .35, "back"))})`});
  set("#cq3", {filter: t > T("q4") ? `brightness(${1 - .3 * p(t, T("q4"), .3)})` : "none"});
  /* book */
  const ba = T("b1") + .05; set("#bk", {opacity: p(t, ba, .3), transform: `translateX(${(1 - p(t, ba, .5, "out")) * -80}px) rotate(${-3 + 2 * p(t, ba, .5)}deg)`});
  const so = W("b1", "पाँच") + .3; set("#stOld", {opacity: clamp((t - so) / .06), transform: `rotate(-12deg) scale(${lerp(2.4, 1, p(t, so, .2, "out"))})`});
  if (t > so + .15) add(shake(t, so + .2, .3, 5));
  const pa = W("b2", "सत्रह") - .1; set("#pr", {opacity: p(t, pa, .25), transform: `translateY(${(1 - p(t, pa, .5, "back")) * 60}px)`});
  [["w16", W("b2", "सोलह")], ["w5", W("b2", "पाँच")]].forEach(([id, a]) => { pop("#" + id, a - .1); set("#" + id + " i", {transform: `scaleX(${p(t, a + .3, .3)})`}); });
  pop("#noFall", W("b2", "फँसना") - .1);
  /* rec */
  [["n1", T("h1") + .1], ["n2", T("h2") + .05], ["n3", W("h2", "ग्यारह") + .1], ["n4", W("h2", "रक्षाबंधन")]].forEach(([n, a], i) => {
    const k = p(t, a, .3, "out"); set("#" + n, {opacity: clamp((t - a) / .06), transform: `scale(${lerp(1.5, 1, k)}) rotate(${(i % 2 ? 1 : -1) * lerp(6, 1.2, k)}deg)`});
    if (t > a + .25) add(shake(t, a + .28, .22, 3)); });
  /* trick */
  pop("#tk1", T("k1"));
  const dw = [W("k1", "दो"), W("k1", "चार"), W("k1", "दो", 1), W("k1", "एक"), W("k1", "एक", 1), W("k1", "एक", 2)];
  document.querySelectorAll("#digs .dg").forEach((d, i) => { const k = p(t, dw[i] - .05, .35, "back");
    set(d, {opacity: clamp((t - dw[i] + .05) / .08), transform: `translateY(${(1 - k) * 40}px) scale(${Math.max(0, k)})`}); });
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
  L.push(["pop", W("o2", "नंबर")], ["thud", W("o3", "Clause", -1)], ["thud", W("q1", "दिल्ली") + .3], ["ding", OPS.ringq1[0] + .4], ["pop", W("q1", "बिहार")]);
  L.push(["riser", W("n1", "सत्रह") - .9], ["thud", W("n1", "सत्रह")], ["whoosh", W("n2", "बाँटो")], ["pop", W("n2", "पक्की")], ["pop", W("n2", "सर्किल")], ["ding", W("n3", "सत्रह")]);
  ["छब्बीस", "पंद्रह"].forEach(w => L.push(["shutter", W("r2", w) - .1])); L.push(["shutter", W("r2", "दो") - .1]);
  L.push(["pop", W("f2", "हिंदू")]);
  ["दशहरा", "दिवाली", "ईद-उल", "बकरीद", "मुहर्रम", "ईद-ए"].forEach(w => L.push(["tick", W("f2", w)]));
  ["क्रिसमस", "फ्राइडे", "नानक", "पूर्णिमा", "महावीर"].forEach(w => L.push(["tick", W("f3", w)]));
  L.push(["ding", T("f4") + .1], ["thud", W("q2", "हरियाणा") + .6], ["ding", OPS.ringq2[0] + .4]);
  L.push(["whoosh", T("t1")], ["pop", W("t2", "बुद्ध")], ["pop", W("t2", "महावीर")], ["pop", W("t2", "गुड")], ["thud", W("t2", "जवाब") + .2]);
  pick_sfx(L);
  L.push(["thud", W("q3", "जम्मू") + .7], ["ding", OPS.ringq3[0] + .4], ["whoosh", T("q4")], ["ding", W("q4", "सत्रह")]);
  L.push(["thud", W("b1", "पाँच") + .5], ["pop", W("b2", "सत्रह")], ["tick", W("b2", "सोलह") + .3], ["tick", W("b2", "पाँच") + .3]);
  L.push(["thud", T("h1") + .3], ["thud", T("h2") + .25], ["thud", W("h2", "ग्यारह") + .3], ["thud", W("h2", "रक्षाबंधन") + .2]);
  [W("k1", "दो"), W("k1", "चार"), W("k1", "दो", 1), W("k1", "एक"), W("k1", "एक", 1), W("k1", "एक", 2)].forEach(a => L.push(["pop", a]));
  L.push(["pop", W("k2", "अगला")]);
  return L.filter(x => x[1] > 0).map(x => [x[0], Math.round(x[1] * 1000) / 1000]);
};
function pick_sfx(L) { ["होली", "गणेश", "महाशिवरात्रि"].forEach(w => L.push(["whoosh", W("c2", w)])); }
})();
