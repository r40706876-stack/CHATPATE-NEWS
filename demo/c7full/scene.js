/* POSTAL WALA - Clause 7 poora video: board + ghadi + naksha + bada shabd + tulna + paper card + parchi + recap + trick.
   Sab samay asli awaaz (window.CUES) se; CUES na ho to andaaza (peek ke liye). */
(function () {
const {p, clamp, lerp, $, set, shake} = E;
const NS = "http://www.w3.org/2000/svg";
const TX = {}; LINES.forEach(([i, t]) => TX[i] = t);
let C = window.CUES;
if (!C) {                                          /* andaaza - deep_demo.py jaisa */
  C = {}; let t = .35; const st = new Set(SCENES.map(s => s[1]));
  LINES.forEach(([i, x]) => { if (st.has(i) && t > .5) t += .3; const d = .42 * x.split(/\s+/).length + .3; C[i] = {t, d}; t += d + .12; });
}
const T = i => C[i].t, D = i => C[i].d, END = i => C[i].t + C[i].d;
function W(i, sub, occ = 0) {
  const ws = TX[i].split(/\s+/); const hits = []; ws.forEach((w, k) => { if (w.includes(sub)) hits.push(k); });
  const k = hits.length ? hits[occ < 0 ? hits.length + occ : Math.min(occ, hits.length - 1)] : 0;
  return C[i].w && C[i].w[k] != null ? C[i].t + C[i].w[k] : C[i].t + C[i].d * k / ws.length;
}
const last = LINES[LINES.length - 1][0];
const TOTAL = END(last) + 1.8; window.TOTAL = TOTAL;
const SID = {sc_open: "s_open", sc_cal: "s_cal", sc_band: "s_band", sc_q8: "s_q8", sc_clock: "s_clock", sc_q4: "s_q4", sc_map: "s_map",
  sc_kin: "f_kin", sc_frank: "s_frank", sc_mp: "s_mp", sc_cmp: "s_cmp", sc_rc: "s_rc", sc_rec: "s_rec", sc_trick: "f_trick"};
const SC = SCENES.map(([n, f], k) => ({n, el: $("#" + SID[n]), a: k ? T(f) - .3 : 0, tr: ["slide", "zoom", "flash"][k % 3]}));
SC.forEach((s, k) => s.b = k + 1 < SC.length ? SC[k + 1].a : TOTAL + 1);

/* ---- pencil ke kaam (board) ---- */
const OPS = {};
function op(n, t0, d) { OPS[n] = [t0, d]; return t0 + d; }
let e;
e = op("cal", T("o1") + .05, .8); e = op("calT", e + .02, .45);
e = op("env", Math.max(e + .05, W("o1", "ज़रूरी") - .15), .7); op("envT", e + .02, .45);
e = op("po", T("o2") + .02, .9); op("poT", e + .02, .3);
e = op("ctr", T("a3") + .02, .65); e = op("ctrT", e + .02, .3);
const x1 = op("x1", Math.max(e + .02, W("a3", "काउंटर") + .2), .25);
e = op("bike", x1 + .05, .65); e = op("bikeT", e + .02, .3);
op("x2", Math.max(e + .02, W("a3", "डिलीवरी") + .1), .25);
e = op("box", T("a4") + .02, .55); e = op("boxT", e + .02, .4);
op("x3", Math.max(e + .02, W("a4", "निकाली")), .25);
e = op("van", T("a5") + .02, .85); e = op("vanT", e + .02, .4);
e = op("x4", Math.max(e + .02, W("a5", "बंद")), .28); op("vanL", e + .05, .55);
e = op("fenv", T("e1") + .05, .85);
op("fimp", Math.max(e + .02, W("e1", "मशीन") - .2), .6);
op("fT", T("e2") + .05, .6);
/* card par pen */
op("ring8", T("p2") + .05, .45); op("strike4", W("p4", "मोबाइल") + .05, .3); op("ring4", W("p4", "रात्रि") - .05, .45);
op("ringmp", W("e4", "मशीन") - .05, .45);

const CAP_HL = ["लेट", "फीस", "नाइट", "RMS", "फ्रैंक", "मोबाइल", "बंद", "खुला", "रजिस्टर्ड", "अखबार", "पंजाब", "दिल्ली", "झारखंड", "गुजरात", "मध्य", "प्रदेश", "ताला", "दोस्त", "शर्त", "उल्टा", "गलत", "छूट", "Railway"];
let built = false, ops = {}, capChunks = [], rcOff = [];
function mk(tag, a, par) { const x = document.createElementNS(NS, tag); for (const k in a) x.setAttribute(k, a[k]); par.appendChild(x); return x; }

function build() {
  built = true;
  for (const n in OPS) ops[n] = {paths: [], texts: [], len: 0};
  SC.forEach(s => s.el.style.opacity = 1);           /* naap-jokh ke liye sab dikhao */
  document.querySelectorAll(".dr").forEach(el => {
    const o = ops[el.dataset.op]; if (!o) return; const L = el.getTotalLength();
    el.setAttribute("fill", "none"); el.setAttribute("stroke", el.classList.contains("red") ? "#dc2626" : "#1f2937");
    el.setAttribute("stroke-width", el.classList.contains("red") ? 6 : 3.4); el.setAttribute("stroke-linecap", "round"); el.setAttribute("stroke-linejoin", "round");
    el.style.strokeDasharray = L; el.style.strokeDashoffset = L; o.paths.push({el, L, at: o.len, svg: el.ownerSVGElement}); o.len += L;
  });
  let ci = 0;
  document.querySelectorAll(".tx").forEach(el => {
    const o = ops[el.dataset.op]; if (!o) return; el.setAttribute("font-weight", "700");
    const bb = el.getBBox(), id = "cpt" + (ci++); const svg = el.ownerSVGElement;
    let defs = svg.querySelector("defs"); if (!defs) defs = mk("defs", {}, svg);
    const cp = mk("clipPath", {id}, defs); const r = mk("rect", {x: bb.x - 6, y: bb.y - 8, width: 0, height: bb.height + 16}, cp);
    el.setAttribute("clip-path", `url(#${id})`); o.texts.push({el, bb, r, svg});
  });
  /* card par gole/kaat */
  const stg = $("#stage").getBoundingClientRect();
  function rel(id) { const c = $("#" + id).closest(".card"), old = c.style.transform; c.style.transform = "none"; c.style.opacity = 1;
    const r = $("#" + id).getBoundingClientRect(); c.style.transform = old; return {x: r.left - stg.left, y: r.top - stg.top, w: r.width, h: r.height, card: c.id}; }
  function ring(n, id) { const b = rel(id), ink = $("#" + id).closest(".sc").querySelector(".ink"); const cx = b.x + 100, cy = b.y + b.h / 2, rx = 122, ry = b.h / 2 + 7;
    const el = mk("path", {d: `M${cx - rx + 6},${cy - ry + 4} A${rx},${ry} 0 1,0 ${cx + rx},${cy + 2} A${rx},${ry} 0 0,0 ${cx - rx + 18},${cy - ry - 2}`, fill: "none", stroke: "#16a34a", "stroke-width": 4.2, "stroke-linecap": "round", "data-card": b.card}, ink);
    const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L; ops[n].paths.push({el, L, at: 0, svg: ink}); ops[n].len = L; }
  ring("ring8", "c8c"); ring("ring4", "c4d"); ring("ringmp", "cmpb");
  { const a = rel("c4a"), ink = $("#s_q4 .ink"); const el = mk("path", {d: `M${a.x + 4},${a.y + a.h / 2 + 3} L${a.x + 200},${a.y + a.h / 2 - 3}`, fill: "none", stroke: "#dc2626", "stroke-width": 5, "stroke-linecap": "round", "data-card": "c4"}, ink);
    const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L; ops.strike4.paths.push({el, L, at: 0, svg: ink}); ops.strike4.len = L; }
  { const a = rel("cmpa"); const ok = $("#okA"); ok.style.left = Math.min(330, a.x + 210) + "px"; ok.style.top = (a.y + 2) + "px"; }
  /* ghadi, taare, shahar, rail */
  const tk = $("#ticks");
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; mk("line", {x1: Math.sin(a) * 84, y1: -Math.cos(a) * 84, x2: Math.sin(a) * (i % 3 ? 76 : 68), y2: -Math.cos(a) * (i % 3 ? 76 : 68), stroke: "#1e3a8a", "stroke-width": i % 3 ? 3 : 6, "stroke-linecap": "round"}, tk); }
  const st = $("#stars1"); for (let i = 0; i < 24; i++) mk("circle", {cx: (i * 97.3) % 490 + 8, cy: (i * 41.7) % 170 + 8, r: .8 + (i % 3) * .6, fill: "#fff", "data-k": i}, st);
  const city = $("#city");
  [[0, 330, 60], [52, 300, 50], [190, 320, 56], [240, 290, 46], [420, 310, 50], [460, 340, 48]].forEach(([x, y, w]) => {
    mk("rect", {x, y, width: w, height: 540 - y, fill: "#0f172a", opacity: .55}, city);
    for (let r = y + 14; r < 400; r += 22) for (let c = x + 8; c < x + w - 10; c += 16) mk("rect", {x: c, y: r, width: 8, height: 10, fill: "#fbbf24", class: "cw", "data-k": (c * 7 + r * 3) % 17, opacity: 0}, city); });
  let sl = ""; for (let x = -40; x < 560; x += 18) sl += `M${x},104 v22 `; $("#sleepers").setAttribute("d", sl);
  /* parchi ke hisse */
  const rc = $("#rc"); const H = rc.offsetHeight; rcOff = ["ri1", "ri2", "ri3"].map(i => { const el = $("#" + i); return el.offsetTop + el.offsetHeight; }); rcOff.push(H); rc.dataset.h = H;
  /* captions: har line 6-6 shabd ke tukde */
  const cap = $("#cap");
  LINES.forEach(([id, txt]) => { const ws = txt.split(/\s+/); for (let s = 0; s < ws.length;) {
    let n = Math.min(6, ws.length - s); if (ws.length - s - n > 0 && ws.length - s - n < 3) n = Math.ceil((ws.length - s) / 2);
    const d = document.createElement("div"); d.style.cssText = "position:absolute;left:0;right:0;top:0;opacity:0";
    d.innerHTML = ws.slice(s, s + n).map(w => `<span class="w${CAP_HL.some(h => w.includes(h)) ? " hl" : ""}">${w}</span>`).join(" ");
    cap.appendChild(d); capChunks.push({el: d, id, k0: s, n}); s += n; } });
  SC.forEach(s => s.el.style.opacity = 0);
}

function wt(id, k) { const c = C[id]; return c.w && c.w[k] != null ? c.t + c.w[k] : c.t + c.d * k / TX[id].split(/\s+/).length; }

function drawOps(t) {
  let tip = null, vis = 0, svg = null;
  for (const n in OPS) {
    const [t0, d] = OPS[n], o = ops[n]; if (!o) continue; const kk = E.ease.inout(clamp((t - t0) / d)); const act = t >= t0 - .15 && t <= t0 + d + .15;
    const at = kk * o.len;
    o.paths.forEach(pp => { const lk = clamp((at - pp.at) / pp.L); pp.el.style.strokeDashoffset = pp.L * (1 - lk);
      if (act && at >= pp.at && at <= pp.at + pp.L + .01) { const q = pp.el.getPointAtLength(clamp(at - pp.at, 0, pp.L)); tip = [q.x, q.y]; svg = pp.svg; } });
    o.texts.forEach(tx => { tx.r.setAttribute("width", (tx.bb.width + 12) * kk); if (act) { tip = [tx.bb.x + tx.bb.width * kk, tx.bb.y + tx.bb.height * .72 + Math.sin(t * 38) * 4]; svg = tx.svg; } });
    if (act) vis = Math.max(vis, Math.min(clamp((t - t0 + .15) / .15), clamp((t0 + d + .15 - t) / .15)));
  }
  return {tip, vis, svg};
}

function card(id, tin, tout, opts, stampId, stampT) {
  const ki = p(t_, tin, .5, "back"), ko = p(t_, tout, .35);
  set("#" + id, {opacity: clamp((t_ - tin) / .15) * (1 - ko), transform: `translateY(${(1 - ki) * 80 - ko * 40}px) rotate(${lerp(-5, -1, ki)}deg)`});
  opts.forEach(([oid, ta]) => { const k = p(t_, ta, .3); set("#" + oid, {opacity: k, transform: `translateX(${(1 - k) * -16}px)`}); });
  if (stampId) { const k = p(t_, stampT, .2, "out"); set("#" + stampId, {opacity: clamp((t_ - stampT) / .06), transform: `rotate(-9deg) scale(${lerp(2.6, 1, k)})`}); }
}
function pop(sel, at, out = 1e9) { const k = p(t_, at, .4, "back"); set(sel, {opacity: clamp((t_ - at) / .1) * (1 - p(t_, out, .25)), transform: `scale(${Math.max(0, k)})`}); }
let t_ = 0;

function seek(t) {
  t_ = t; if (!built) build();
  set("#o1", {transform: `translate(${Math.sin(t * .35) * 40}px,${Math.cos(t * .27) * 50}px)`});
  set("#o2", {transform: `translate(${Math.cos(t * .3) * 40}px,${Math.sin(t * .22) * 40}px)`});
  const gs = Math.floor(t * 12); set("#grain", {transform: `translate(${(gs * 37) % 60 - 30}px,${(gs * 23) % 60 - 30}px)`});
  set("#top", {opacity: p(t, .05, .4)}); E.pop($("#logo"), t, .15, .5);
  $("#rail b").style.width = 100 * clamp(t / TOTAL) + "%";
  /* drishya + badlaav */
  let cur = 0; SC.forEach((s, k) => { if (t >= s.a) cur = k; });
  let fl = 0;
  SC.forEach((s, k) => {
    const isFull = s.el.classList.contains("full");
    if (k === cur) {
      const ki = p(t, s.a, .38, "out");
      let tf = "none", op_ = 1;
      if (k > 0 && s.tr === "slide") tf = `translateX(${(1 - ki) * 105}%)`;
      if (k > 0 && s.tr === "zoom") { tf = `scale(${lerp(1.18, 1, ki)})`; op_ = clamp((t - s.a) / .25); }
      if (k > 0 && s.tr === "flash") fl = Math.max(fl, 1 - clamp((t - s.a) / .3));
      set(s.el, {opacity: op_, transform: tf, zIndex: isFull ? 40 : 2});
    } else if (k === cur - 1 && t - SC[cur].a < .38) {
      const ko = p(t, SC[cur].a, .38, "out");
      set(s.el, {opacity: 1, zIndex: isFull ? 39 : 1, transform: SC[cur].tr === "slide" ? `translateX(${-ko * 40}%)` : SC[cur].tr === "zoom" ? `scale(${1 - .06 * ko})` : "none"});
    } else set(s.el, {opacity: 0});
  });
  set("#flash", {opacity: fl * .85});
  let sk = [0, 0]; const add = q => { sk = [sk[0] + q[0], sk[1] + q[1]]; };

  /* fills after their op */
  document.querySelectorAll(".fl").forEach(f => { const o = OPS[f.dataset.after]; if (o) f.setAttribute("opacity", p(t, o[0] + o[1] + .02, .35) * .92); });
  const dr = drawOps(t);
  document.querySelectorAll(".ink path").forEach(pth => { const c = $("#" + pth.dataset.card); pth.style.opacity = c ? (c.style.opacity || 0) : 1; });
  const pen = $("#pencil");
  if (dr.tip && dr.vis > 0) { const r = dr.svg.getBoundingClientRect(), s = r.width / 508;
    set(pen, {opacity: dr.vis, left: (r.left + dr.tip[0] * s) + "px", top: (r.top + dr.tip[1] * s - 15) + "px", transform: `rotate(${-38 + Math.sin(t * 17) * 3}deg)`}); }
  else set(pen, {opacity: 0});

  /* --- open --- */
  const lockAt = W("o2", "ताला") - .1, lk = t < lockAt ? 0 : E.ease.bounce(clamp((t - lockAt) / .55));
  $("#lock0").setAttribute("transform", `translate(0,${(1 - lk) * -280})`); $("#lock0").setAttribute("opacity", t < lockAt ? 0 : 1);
  if (t > lockAt + .3) add(shake(t, lockAt + .35, .3, 5));
  const bA = lockAt + .45, bk = p(t, bA, .4, "back"); $("#band0").setAttribute("opacity", clamp((t - bA) / .1));
  $("#band0").setAttribute("transform", `translate(410,410) scale(${Math.max(.01, bk)}) rotate(-8) translate(-410,-410)`);
  const c7 = p(t, T("o3") + .1, .5, "back"); set("#cl7", {opacity: clamp((t - T("o3") - .1) / .12), transform: `scale(${Math.max(0, c7)})`});
  set("#s_open .bsvg", {opacity: 1 - .75 * p(t, T("o3"), .4)});

  /* --- calendar --- */
  const f1 = p(t, T("a1") + .3, .5, "inout"), f2 = p(t, T("a1") + .75, .5, "inout");
  set("#pg1", {transform: `rotateX(${f1 * -100}deg)`, opacity: f1 > .95 ? 0 : 1}); set("#pg2", {transform: `rotateX(${f2 * -100}deg)`, opacity: f2 > .95 ? 0 : 1});
  const sun = t > T("a1") + 1.1; $("#pg3").querySelector(".hd").style.background = sun ? "#dc2626" : "#1e3a8a";
  $("#pgy3").style.color = sun ? "#dc2626" : "#6b7280"; $("#pgd3").style.color = sun ? "#dc2626" : "#1f2937";
  if (t > T("a2")) { const f3 = p(t, T("a2") + .05, .5, "inout");
    if (f3 > .5) { $("#pgd3").textContent = "17"; $("#pgy3").textContent = "सोमवार"; $("#pg3").querySelector(".hd").style.background = "#1e3a8a"; $("#pgy3").style.color = "#6b7280"; $("#pgd3").style.color = "#1f2937"; }
    else { $("#pgd3").textContent = "16"; $("#pgy3").textContent = "रविवार"; }
    set("#pg3", {transform: `rotateX(${Math.sin(f3 * Math.PI) * -70}deg)`}); }
  else { $("#pgd3").textContent = "16"; $("#pgy3").textContent = "रविवार"; set("#pg3", {transform: "none"}); }
  const sk2 = W("a2", "डाक", -1); const sti = p(t, sk2 - .05, .35, "back"); set("#sticker", {opacity: clamp((t - sk2 + .05) / .08), transform: `rotate(8deg) scale(${lerp(2.2, 1, Math.min(1, sti))})`});
  if (t > sk2 + .2) add(shake(t, sk2 + .25, .3, 5));
  pop("#tm_cal", sk2 + .3);
  set("#tm_cal", {transform: `translateX(-50%) scale(${Math.max(0, p(t, sk2 + .3, .4, "back"))})`});

  /* --- band --- */
  pop("#ch_band", T("a3") - .1); set("#ch_band", {transform: `translateX(${(1 - p(t, T("a3") - .1, .4, "back")) * -40}px)`});

  /* --- q8 --- */
  pop("#bn8", T("p1") - .1, END("p2"));
  card("c8", T("p1") + .05, 1e9, [["c8a", W("p1", "किस") - .1], ["c8b", W("p1", "किस") + .05], ["c8c", W("p1", "किस") + .2]], "st8", T("p1") + .7);
  if (t > T("p1") + .85) add(shake(t, T("p1") + .9, .3, 6));
  set("#c8c", {background: `rgba(22,163,74,${.16 * p(t, OPS.ring8[0] + .4, .3)})`});
  pop("#pl_gj", W("p2", "गुजरात"));

  /* --- clock --- */
  const ca = T("b1"), cb = END("b2") - .3;
  const dk = p(t, ca + .2, Math.max(1, cb - ca - .2), "inout"), hrs = 9 + 14 * dk;
  $("#hh").setAttribute("transform", `rotate(${hrs * 30})`); $("#mh").setAttribute("transform", `rotate(${hrs * 360})`);
  const hh = Math.floor(hrs) % 24; $("#clkT").textContent = `${hh < 12 ? "सुबह" : hh < 17 ? "दोपहर" : hh < 20 ? "शाम" : "रात"} ${((hh + 11) % 12) + 1}:00`;
  const night = p(t, W("b1", "रविवार"), Math.max(.8, T("b2") - W("b1", "रविवार") + .4), "inout");
  const sky = (a, b) => `rgb(${lerp(a[0], b[0], night) | 0},${lerp(a[1], b[1], night) | 0},${lerp(a[2], b[2], night) | 0})`;
  $("#sky").style.background = `linear-gradient(180deg,${sky([125, 190, 255], [11, 16, 41])},${sky([254, 230, 160], [36, 42, 92])})`;
  $("#sun").setAttribute("transform", `translate(${dk * 340},${Math.sin(dk * Math.PI) * -60 + dk * 260})`); $("#sun").setAttribute("opacity", 1 - night);
  $("#moon1").setAttribute("opacity", night);
  document.querySelectorAll("#stars1 circle").forEach(c => c.setAttribute("opacity", night * (.4 + .6 * Math.abs(Math.sin(t * 1.7 + +c.dataset.k)))));
  document.querySelectorAll(".cw").forEach(c => c.setAttribute("opacity", night > (+c.dataset.k) / 20 ? .9 : 0));
  $("#clk").setAttribute("transform", `translate(254,${lerp(250, 205, p(t, ca, .6))}) scale(${lerp(.6, 1, p(t, ca, .55, "back")) * (1 - .12 * night)})`);
  $("#band1").setAttribute("opacity", p(t, ca + .4, .3));
  const lit = t > W("b2", "नाइट") ? 1 : 0;
  document.querySelectorAll(".npw").forEach(w => w.setAttribute("fill", lit ? "#ffcf4a" : "#374151"));
  $("#npoSign").setAttribute("fill", lit ? "#c81e1e" : "#374151"); $("#npoTxt").setAttribute("fill", lit ? "#fff" : "#9ca3af");
  $("#khula1").setAttribute("opacity", p(t, W("b2", "खुला"), .3));
  pop("#tm_clock", W("b2", "नाइट") + .1); set("#tm_clock", {transform: `translateX(-50%) scale(${Math.max(0, p(t, W("b2", "नाइट") + .1, .4, "back"))})`});

  /* --- q4 --- */
  card("c4", T("p3") - .1, 1e9, [["c4a", W("p3", "कौन") - .1], ["c4b", W("p3", "कौन") + .05], ["c4c", W("p3", "कौन") + .2], ["c4d", W("p3", "कौन") + .35]], "st4", T("p3") + .6);
  if (t > T("p3") + .75) add(shake(t, T("p3") + .8, .3, 6));
  pop("#pl_dl", W("p3", "दिल्ली"));
  const tpA = OPS.strike4[0] + .35, tp = p(t, tpA, .35, "out");
  set("#tp4", {opacity: clamp((t - tpA) / .08) * (1 - p(t, OPS.ring4[0] - .1, .3)), transform: `rotate(-7deg) translateX(${(1 - tp) * -560}px)`});
  set("#c4a", {color: t > tpA ? "#991b1b" : "", background: `rgba(220,38,38,${.12 * p(t, tpA, .3)})`});
  set("#c4d", {background: `rgba(22,163,74,${.16 * p(t, OPS.ring4[0] + .4, .3)})`});
  const mj = p(t, T("p5") + .05, .45, "back"); set("#mn_jh", {opacity: clamp((t - T("p5") - .05) / .1), transform: `translateY(${(1 - mj) * 120}px)`});
  set("#mn_jh .s", {opacity: p(t, W("p5", "नाइट"), .2), transform: `scale(${Math.max(0, p(t, W("p5", "नाइट"), .35, "back"))})`});
  set("#c4", {filter: t > T("p5") ? `brightness(${1 - .35 * p(t, T("p5"), .3)})` : "none"});

  /* --- map --- */
  const m0 = T("c1"), m1 = END("c3");
  const cam = p(t, m0, m1 - m0, "inout");
  $("#mapG").setAttribute("transform", `translate(254,270) scale(${lerp(1.25, 1.0, p(t, m0, 1.2, "out")) + .05 * Math.sin(cam * Math.PI)}) translate(${-254 + lerp(-30, 20, cam)},${-270 + lerp(20, -10, cam)})`);
  const pm = E.ease.bounce(clamp((t - m0 - .1) / .6)); $("#pinMe").setAttribute("transform", `translate(365,${430 - (1 - pm) * 220})`);
  const r1L = $("#r1").getTotalLength(), r2L = $("#r2").getTotalLength();
  const r1a = W("c1", "डाकघर") - .1; $("#r1").style.strokeDasharray = `${p(t, r1a, .8, "inout") * r1L} ${r1L}`; $("#r1").setAttribute("opacity", t < r1a ? 0 : 1 - p(t, W("c1", "RMS") + .2, .4) * .7);
  const xa = W("c1", "बंद"); $("#xMark").setAttribute("opacity", clamp((t - xa) / .1)); $("#xMark").setAttribute("transform", `translate(205,292) scale(${Math.max(.01, p(t, xa, .4, "back"))})`);
  if (t > xa + .1) add(shake(t, xa + .1, .3, 5));
  const r2a = W("c1", "RMS") - .2; $("#r2").style.strokeDasharray = `${p(t, r2a, 1.3, "inout") * r2L} ${r2L}`; $("#r2").setAttribute("opacity", t < r2a ? 0 : 1);
  const oka = r2a + 1.3; $("#pinOk").setAttribute("opacity", clamp((t - oka) / .1)); $("#pinOk").setAttribute("transform", `translate(405,190) scale(${Math.max(.01, p(t, oka, .4, "back"))})`);
  pop("#tm_map", W("c1", "Railway") - .1); set("#tm_map", {transform: `translateX(-50%) scale(${Math.max(0, p(t, W("c1", "Railway") - .1, .4, "back"))})`});
  $("#train").setAttribute("transform", `translate(${lerp(-200, 620, p(t, W("c2", "ट्रेन") - .2, 2.8, "inout"))},0)`);
  const sp = W("c3", "चुने"); $("#selPO").setAttribute("opacity", p(t, sp, .25)); $("#selPO").setAttribute("transform", `translate(16,150) scale(${Math.max(.01, p(t, sp, .4, "back"))})`);
  const va = W("c3", "वैन") - .4; $("#mvan").setAttribute("opacity", clamp((t - va) / .15)); $("#mvan").setAttribute("transform", `translate(${lerp(-90, 250, p(t, va, 1.6, "out"))},412)`);
  const rmsP = W("c3", "RMS"); $("#rmsB").setAttribute("transform", `translate(330,138) scale(${1 + .08 * Math.max(0, Math.sin(clamp((t - rmsP) / .6) * Math.PI))})`);
  pop("#feeTag", W("c3", "डाल"));

  /* --- bada shabd --- */
  const kq = p(t, T("d1") + .05, .35, "back"); set("#kq", {opacity: clamp((t - T("d1") - .05) / .1), transform: `scale(${lerp(2, 1, kq)})`});
  const kwA = W("d1", "लेट") - .05, kw = p(t, kwA, .22, "out"); set("#kw", {opacity: clamp((t - kwA) / .05), transform: `scale(${lerp(3, 1, kw)})`});
  document.querySelectorAll(".kcoin").forEach((c, i) => { const a = i / 6 * Math.PI * 2 + .4, k = p(t, kwA + .15, .9, "out");
    set(c, {opacity: k > 0 ? 1 - p(t, kwA + 1.6, .5) : 0, transform: `translate(${Math.cos(a) * 190 * k}px,${Math.sin(a) * 150 * k + 60 * k * k}px) rotate(${k * 360}deg)`}); });
  { const q = shake(t, kwA + .2, .35, 12); set("#f_kin", {transform: SC[cur].n === "sc_kin" && t - SC[cur].a > .38 ? `translate(${q[0]}px,${q[1]}px)` : $("#f_kin").style.transform}); }
  const kc = p(t, T("d2") + .05, .5, "back"); set("#kc", {opacity: clamp((t - T("d2") - .05) / .12), transform: `translateY(${(1 - kc) * 80}px)`});
  set("#kq", {top: lerp(290, 220, p(t, T("d2"), .5, "inout")) + "px"}); set("#kw", {top: lerp(390, 310, p(t, T("d2"), .5, "inout")) + "px"});
  { const k = p(t, T("d2") + .6, .2, "out"); set("#stk", {opacity: clamp((t - T("d2") - .6) / .06), transform: `rotate(-9deg) scale(${lerp(2.6, 1, k)})`}); }

  /* --- frank --- */
  pop("#ch_frank", T("e1") - .1); set("#ch_frank", {transform: `translateX(${(1 - p(t, T("e1") - .1, .4, "back")) * -40}px)`});
  const ia = OPS.fimp[0] + OPS.fimp[1]; $("#impT").setAttribute("opacity", p(t, ia, .3)); $("#impT2").setAttribute("opacity", p(t, ia, .3));
  pop("#tm_frank", W("e2", "फ्रैंक")); set("#tm_frank", {transform: `translateX(-50%) scale(${Math.max(0, p(t, W("e2", "फ्रैंक"), .4, "back"))})`});
  $("#boxF").setAttribute("opacity", p(t, W("e2", "मेल") - .2, .3));
  const mvA = W("e2", "नहीं") - .9, mv = p(t, mvA, .75, "inout"), bkA = mvA + .75, bk2 = p(t, bkA, .4, "out") * (1 - p(t, bkA + .5, .5, "inout"));
  $("#envF").setAttribute("transform", `translate(${lerp(0, 270, mv) - bk2 * 130},${lerp(0, 190, mv)}) scale(${lerp(1, .42, mv)}) rotate(${-bk2 * 12})`);
  const noA = bkA + .05; $("#noF").setAttribute("opacity", clamp((t - noA) / .08)); $("#noF").setAttribute("transform", `translate(250,300) scale(${Math.max(.01, p(t, noA, .35, "back"))})`);
  if (t > noA) add(shake(t, noA + .05, .35, 6));

  /* --- mp --- */
  pop("#bnmp", T("e3") - .1, T("e4"));
  card("cmp", T("e3") + .05, 1e9, [["cmpa", W("e3", "क्या") - .1], ["cmpb", W("e3", "क्या") + .05], ["cmpc", W("e3", "क्या") + .2], ["cmpd", W("e3", "क्या") + .35]], "stmp", T("e3") + .7);
  if (t > T("e3") + .85) add(shake(t, T("e3") + .9, .3, 6));
  pop("#okA", W("e4", "डाल"));
  set("#cmpb", {background: `rgba(22,163,74,${.16 * p(t, OPS.ringmp[0] + .4, .3)})`});
  pop("#pl_jh", W("e4", "झारखंड"));

  /* --- tulna --- */
  const f0 = T("f1");
  set("#hL", {transform: `translateX(${(1 - p(t, f0, .5, "out")) * -260}px)`}); set("#hR", {transform: `translateX(${(1 - p(t, f0 + .15, .5, "out")) * 260}px)`});
  set("#vs", {transform: `scale(${Math.max(0, p(t, f0 + .5, .45, "back"))}) rotate(${(1 - p(t, f0 + .5, .5)) * 180}deg)`});
  set("#cL", {transform: `translateY(${(1 - E.ease.bounce(clamp((t - W("f1", "लेट") + .3) / .6))) * -120}px)`});
  pop("#vL", W("f1", "लगती"));
  set("#cR", {transform: `translateY(${(1 - E.ease.bounce(clamp((t - W("f1", "अखबार") + .2) / .6))) * -120}px)`});
  $("#cRxp").setAttribute("stroke-dashoffset", 71 * (1 - p(t, W("f1", "नहीं", -1), .3)));
  pop("#vR", W("f1", "नहीं", -1) + .2);
  document.querySelectorAll("#drop3 span").forEach((s, i) => { const a = W("f2", ["प्रेस", "RMS", "नाइट"][i]); const k = p(t, a, .4, "back");
    set(s, {opacity: clamp((t - a) / .1), transform: `translateY(${(1 - k) * 30}px) scale(${Math.max(0, k)})`}); });
  pop("#tm_cmp", W("f1", "रजिस्टर्ड")); set("#tm_cmp", {transform: `translateX(-50%) scale(${Math.max(0, p(t, W("f1", "रजिस्टर्ड"), .4, "back"))})`});

  /* --- parchi --- */
  const H = +$("#rc").dataset.h; const steps = [T("g1") + .1, W("g1", "टिकट"), W("g1", "पोस्टिंग"), W("g1", "रजिस्ट्री")];
  let shown = 60; const offs = [70, rcOff[0], rcOff[1], rcOff[2]];
  steps.forEach((a, i) => { const k = p(t, a, .5, "out"); if (t >= a) shown = lerp(i ? offs[i - 1] : 0, offs[i], k); });
  if (t > W("g1", "रजिस्ट्री") + .6) shown = lerp(rcOff[2], H, p(t, W("g1", "रजिस्ट्री") + .6, .5));
  set("#rc", {transform: `translateY(${-6 + 6 * clamp(shown / H)}px)`, clipPath: `inset(0 0 ${Math.max(0, H - shown)}px 0)`});
  ["ri1", "ri2", "ri3"].forEach((r, i) => set("#" + r + " b", {transform: `scale(${Math.max(0, p(t, steps[i + 1] + .3, .3, "back"))})`, display: "inline-block"}));
  const ta = p(t, T("g2") + .1, .5, "back"); set("#tar", {opacity: clamp((t - T("g2") - .1) / .12), transform: `translateY(${(1 - ta) * 90}px)`});
  pop("#tm_rc", W("g1", "सर्टिफ़िकेट"), T("g2")); set("#tm_rc", {transform: `translateX(-50%) scale(${Math.max(0, p(t, W("g1", "सर्टिफ़िकेट"), .4, "back"))})`});

  /* --- recap --- */
  [["n1", T("h1") + .1], ["n2", W("h1", "चिट्ठी")], ["n3", T("h2") + .05], ["n4", W("h2", "अखबार")]].forEach(([n, a], i) => {
    const k = p(t, a, .3, "out"); set("#" + n, {opacity: clamp((t - a) / .06), transform: `scale(${lerp(1.5, 1, k)}) rotate(${(i % 2 ? 1 : -1) * lerp(6, 1.2, k)}deg)`});
    if (t > a + .25) add(shake(t, a + .28, .22, 3)); });

  /* --- trick --- */
  pop("#tk1", T("h3")); pop("#tk2", W("h3", "छुट्टी"));
  const fa = W("h3", "नाइट"), fb = W("h3", "RMS");
  set("#fA", {transform: `translateX(${(1 - p(t, fa, .45, "back")) * -320 + p(t, fb + .35, .3, "inout") * 20}px)`});
  set("#fB", {transform: `translateX(${(1 - p(t, fb, .45, "back")) * 320 - p(t, fb + .35, .3, "inout") * 20}px)`});
  set("#spark", {opacity: Math.sin(clamp((t - fb - .5) / .5) * Math.PI), transform: `scale(${1 + 2 * clamp((t - fb - .5) / .5)})`});
  const h4 = T("h4"); set("#tk1", {top: "200px"});
  pop("#trN", h4 + .05);
  document.querySelectorAll("#trP .pill").forEach((s, i) => pop(s, h4 + .3 + i * .15));
  const fo = W("h4", "अगला"); set("#fol", {opacity: clamp((t - fo) / .1), transform: `scale(${Math.max(0, p(t, fo, .4, "back")) * (1 + .04 * Math.sin(t * 8))})`});
  set("#fA,#fB", {});
  if (t > END(last) - .2) { const k = p(t, END(last) - .2, .5); set("#f_trick", {filter: `brightness(${1 - .2 * k})`}); }

  set("#stage", {transform: `translate(${sk[0]}px,${sk[1]}px)`});
  /* captions */
  capChunks.forEach(c => { const a = wt(c.id, c.k0) - .08, nx = c.k0 + c.n < TX[c.id].split(/\s+/).length ? wt(c.id, c.k0 + c.n) - .08 : END(c.id) + .1;
    const vis = t >= a && t < nx; c.el.style.opacity = vis ? 1 : 0; if (!vis) return;
    [...c.el.children].forEach((w, j) => { const ti = wt(c.id, c.k0 + j) - .06, k = p(t, ti, .28, "back");
      w.style.opacity = clamp((t - ti) / .07); w.style.transform = `translateY(${(1 - k) * 20}px) scale(${.75 + .25 * Math.max(0, k)})`; }); });
}
window.seek = seek;
window.SFX = function () {
  const L = [];
  SC.forEach((s, k) => { if (k) L.push(["whoosh", s.a]); });
  L.push(["thud", W("o2", "ताला") + .35], ["pop", T("o3") + .1], ["shutter", T("a1") + .3], ["shutter", T("a1") + .75], ["thud", W("a2", "डाक", -1)]);
  ["x1", "x2", "x3", "x4"].forEach(x => L.push(["tick", OPS[x][0]]));
  L.push(["thud", T("p1") + .85], ["ding", OPS.ring8[0] + .4], ["pop", W("p2", "गुजरात")]);
  for (let x = T("b1") + .3; x < END("b2") - .4; x += .45) L.push(["tick", x]);
  L.push(["ding", W("b2", "नाइट")], ["thud", T("p3") + .75], ["pop", W("p3", "दिल्ली")], ["thud", OPS.strike4[0] + .35], ["ding", OPS.ring4[0] + .4], ["whoosh", T("p5")], ["thud", W("p5", "नाइट")]);
  L.push(["pop", T("c1") + .2], ["thud", W("c1", "बंद") + .1], ["ding", W("c1", "RMS") + 1.1], ["whoosh", W("c2", "ट्रेन")], ["pop", W("c3", "चुने")], ["pop", W("c3", "डाल")]);
  L.push(["riser", T("d1") - .9], ["pop", T("d1") + .05], ["thud", W("d1", "लेट")], ["ding", W("d1", "लेट") + .2], ["thud", T("d2") + .65]);
  L.push(["pop", W("e2", "फ्रैंक")], ["whoosh", W("e2", "नहीं") - .9], ["thud", W("e2", "नहीं") - .1], ["thud", T("e3") + .85], ["ding", OPS.ringmp[0] + .4], ["pop", W("e4", "झारखंड")]);
  L.push(["whoosh", T("f1")], ["thud", W("f1", "लेट") + .2], ["ding", W("f1", "लगती")], ["thud", W("f1", "अखबार") + .35], ["pop", W("f2", "प्रेस")], ["pop", W("f2", "RMS")], ["pop", W("f2", "नाइट")]);
  L.push(["tick", W("g1", "टिकट")], ["tick", W("g1", "पोस्टिंग")], ["tick", W("g1", "रजिस्ट्री")], ["whoosh", T("g2") + .1]);
  L.push(["thud", T("h1") + .3], ["thud", W("h1", "चिट्ठी") + .2], ["thud", T("h2") + .25], ["thud", W("h2", "अखबार") + .2]);
  L.push(["whoosh", W("h3", "नाइट")], ["whoosh", W("h3", "RMS")], ["ding", W("h3", "RMS") + .5], ["pop", W("h4", "अगला")]);
  return L.filter(x => x[1] > 0).map(x => [x[0], Math.round(x[1] * 1000) / 1000]);
};
})();
