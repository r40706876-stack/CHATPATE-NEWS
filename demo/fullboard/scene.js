/* POSTAL WALA - FULL SMART BOARD demo (Clause 7, hissa 1-2). seek(t) deterministic. */
(function () {
const {p, clamp, lerp, $, set, shake} = E;
const TOTAL = 38.2;
window.TOTAL = TOTAL;

/* pencil ke kaam: naam -> [shuru, samay] */
const OPS = {
  cal: [1.8, .85], calT: [2.72, .5], env: [3.28, .75], envT: [4.06, .5], po: [4.6, 1.1], poT: [5.74, .32],
  ctr: [8.6, .8], ctrT: [9.42, .36], bike: [9.86, .95], bikeT: [10.83, .4], box: [11.28, .6], boxT: [11.9, .45],
  x1: [12.35, .28], x2: [12.85, .28], x3: [13.35, .28],
  van: [14.5, 1.0], vanT: [15.52, .45], x4: [16.02, .3], vanL: [16.38, .62],
  moon: [22.55, .5], npo: [23.1, 1.2], npoS: [24.36, .4], npoT: [25.2, .9], npoY: [26.32, .7],
  ring8: [19.0, .5], ring4: [32.1, .5], strike4: [33.0, .35],
};
const CAPS = [
  [1.8, 4.3, "रविवार है… और चिट्ठी *आज ही* भेजनी है।"],
  [4.5, 7.6, "डाकघर पहुँचे — तो *ताला* लगा है!"],
  [8.3, 11.7, "रविवार और *डाक छुट्टी* पर — डाकघर बंद।"],
  [11.9, 14.4, "न काउंटर, न *डिलीवरी*, न बॉक्स से चिट्ठी।"],
  [14.5, 17.0, "गाँव घूमने वाला *मोबाइल डाकघर* भी बंद।"],
  [17.2, 21.5, "जो अभी समझा — वही *पंजाब 2024* के पेपर में आया।"],
  [21.8, 25.0, "पर एक डाकघर *कभी नहीं सोता*…"],
  [25.2, 28.3, "*नाइट पोस्ट ऑफिस* — छुट्टी में भी खुला!"],
  [28.5, 32.8, "यही नियम — *4 राज्यों* के पेपर में आ चुका है।"],
  [32.9, 36.3, "ऐसे भी फँसाते हैं — option A *मोबाइल डाकघर*!"],
  [36.4, 38.2, "आगे — *RMS* का रास्ता…"],
];
const STAMPS = {st8: 19.8, st4: 31.5};
const PILLS = [30.1, 30.4, 30.7, 31.0];

const svg = $("#svg"), ink2 = $("#ink2"), NS = "http://www.w3.org/2000/svg";
let built = false, ops = {}, capEls = [];

function mk(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent.appendChild(e); return e; }

function build() {
  built = true;
  for (const n in OPS) ops[n] = {paths: [], texts: [], len: 0};
  document.querySelectorAll(".dr").forEach(el => {
    const o = ops[el.dataset.op]; const L = el.getTotalLength();
    el.setAttribute("fill", "none");
    el.setAttribute("stroke", el.classList.contains("red") ? "#dc2626" : el.classList.contains("wh") ? "#f8fafc" : "#1f2937");
    el.setAttribute("stroke-width", el.classList.contains("red") ? 6 : 3.4);
    el.setAttribute("stroke-linecap", "round"); el.setAttribute("stroke-linejoin", "round");
    el.style.strokeDasharray = L; el.style.strokeDashoffset = L;
    o.paths.push({el, L, at: o.len}); o.len += L;
  });
  let ci = 0;
  document.querySelectorAll(".tx").forEach(el => {
    el.style.fontFamily = "Kalam"; el.setAttribute("font-weight", "700");
    const bb = el.getBBox(), id = "cpt" + (ci++);
    const cp = mk("clipPath", {id}, svg.querySelector("defs"));
    const r = mk("rect", {x: bb.x - 6, y: bb.y - 8, width: 0, height: bb.height + 16}, cp);
    el.setAttribute("clip-path", `url(#${id})`);
    ops[el.dataset.op].texts.push({el, bb, r});
  });
  /* taare */
  const st = $("#stars");
  for (let i = 0; i < 26; i++) {
    const x = (i * 97.3) % 470 + 10, y = (i * 53.7) % 200 + 12;
    mk("circle", {cx: x, cy: y, r: 0.8 + (i % 3) * 0.6, fill: "#fff", "data-k": i}, st);
  }
  /* card par pen: gola / kaat (card ke andar jagah se) */
  const scr = $("#screen").getBoundingClientRect(), sx = 492 / scr.width;
  function rel(id) {
    const card = $("#" + id).closest(".card"), old = card.style.transform; card.style.transform = "none";
    const r = $("#" + id).getBoundingClientRect(); card.style.transform = old;
    return {x: (r.left - scr.left) * sx, y: (r.top - scr.top) * sx, w: r.width * sx, h: r.height * sx};
  }
  function ring(name, id, col) {
    const b = rel(id), cx = b.x + 70, cy = b.y + b.h / 2, rx = 92, ry = b.h / 2 + 7;
    const d = `M${cx - rx + 6},${cy - ry + 4} A${rx},${ry} 0 1,0 ${cx + rx},${cy + 2} A${rx},${ry} 0 0,0 ${cx - rx + 18},${cy - ry - 2}`;
    const el = mk("path", {d, fill: "none", stroke: col, "stroke-width": 4.2, "stroke-linecap": "round", "data-card": $("#" + id).closest(".card").id}, ink2);
    const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L;
    ops[name].paths.push({el, L, at: 0}); ops[name].len = L;
  }
  ring("ring8", "c8c", "#16a34a"); ring("ring4", "c4d", "#16a34a");
  const a = rel("c4a");
  const el = mk("path", {d: `M${a.x + 4},${a.y + a.h / 2 + 3} L${a.x + 190},${a.y + a.h / 2 - 3}`, fill: "none", stroke: "#dc2626", "stroke-width": 5, "stroke-linecap": "round", "data-card": "c4"}, ink2);
  const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L;
  ops.strike4.paths.push({el, L, at: 0}); ops.strike4.len = L;
  /* caption lines */
  const cap = $("#cap");
  CAPS.forEach(c => {
    const d = document.createElement("div"); d.style.cssText = "position:absolute;left:0;right:0;top:0;opacity:0";
    const parts = c[2].split("*"); const ws = [];
    parts.forEach((pt, i) => pt.trim().split(/\s+/).filter(Boolean).forEach(w => ws.push(`<span class="w${i % 2 ? " hl" : ""}">${w}</span>`)));
    d.innerHTML = ws.join(" "); cap.appendChild(d); capEls.push(d);
  });
}

/* pencil ki nok kahan (svg coords) aur kitna dikhe */
function drawOps(t) {
  let tip = null, vis = 0, red = false;
  for (const n in OPS) {
    const [t0, d] = OPS[n], o = ops[n], k = clamp((t - t0) / d);
    const kk = E.ease.inout(k);
    if (o.len) {
      const at = kk * o.len;
      o.paths.forEach(pp => {
        const lk = clamp((at - pp.at) / pp.L);
        pp.el.style.strokeDashoffset = pp.L * (1 - lk);
        if (t >= t0 - .15 && t <= t0 + d + .15 && at >= pp.at && at <= pp.at + pp.L + 0.01) {
          const pt = pp.el.getPointAtLength(clamp(at - pp.at, 0, pp.L)); tip = [pt.x, pt.y];
        }
      });
    }
    o.texts.forEach(tx => {
      tx.r.setAttribute("width", (tx.bb.width + 12) * kk);
      if (t >= t0 - .15 && t <= t0 + d + .15) tip = [tx.bb.x + tx.bb.width * kk, tx.bb.y + tx.bb.height * .72 + Math.sin(t * 38) * 4];
    });
    if (t >= t0 - .15 && t <= t0 + d + .15) {
      vis = Math.max(vis, Math.min(clamp((t - t0 + .15) / .15), clamp((t0 + d + .15 - t) / .15)));
      if (n.startsWith("ring") || n.startsWith("strike")) red = true;
    }
  }
  return {tip, vis};
}

function seek(t) {
  if (!built) build();
  /* pichhe ki halchal */
  set("#o1", {transform: `translate(${Math.sin(t * .35) * 40}px,${Math.cos(t * .27) * 50}px)`});
  set("#o2", {transform: `translate(${Math.cos(t * .3) * 40}px,${Math.sin(t * .22) * 40}px)`});
  const gs = Math.floor(t * 12); set("#grain", {transform: `translate(${(gs * 37) % 60 - 30}px,${(gs * 23) % 60 - 30}px)`});
  /* upar */
  set("#top", {opacity: p(t, .15, .5), transform: `translateY(${(1 - p(t, .15, .6)) * -24}px)`});
  E.pop($("#logo"), t, .3, .5);
  const rails = document.querySelectorAll("#rail b");
  rails[0].style.width = 100 * p(t, 8.3, 13.2, "lin") + "%";
  rails[1].style.width = 100 * p(t, 22.0, 14.2, "lin") + "%";
  /* board chalu */
  const on = p(t, .2, .55, "inout");
  set("#screen", {clipPath: `inset(${50 * (1 - on)}% 0 ${50 * (1 - on)}% 0 round 11px)`});
  set("#power", {opacity: t < .9 ? Math.sin(clamp((t - .1) / .8) * Math.PI) : 0, transform: `scaleX(${p(t, .05, .3)})`});
  set("#boardWrap", {opacity: p(t, 0, .2)});
  /* sheen */
  let sh = -260;
  [[.9, .9], [8.0, .8], [22.0, .9], [28.5, .8], [36.4, .8]].forEach(([a, d]) => { if (t >= a && t <= a + d) sh = lerp(-260, 640, E.ease.inout((t - a) / d)); });
  set("#sheen", {left: sh + "px"});
  set("#live i", {opacity: .45 + .55 * Math.abs(Math.sin(t * 2.6))});
  /* night board */
  const nt = p(t, 21.7, .8, "inout") * (1 - p(t, 36.2, .5));
  set("#night", {opacity: nt}); set("#grid", {opacity: .55 * (1 - nt)});
  /* scenes */
  const s1o = 1 - p(t, 7.75, .4), s2o = p(t, 8.0, .3) * (1 - p(t, 21.6, .4));
  $("#s1").setAttribute("opacity", s1o);
  $("#s1").setAttribute("transform", `translate(${-p(t, 7.75, .45, "inout") * 60},0)`);
  $("#s2").setAttribute("opacity", s2o * (t > 17.1 && t < 21.6 ? lerp(1, .18, p(t, 17.1, .4)) : 1));
  $("#s2").setAttribute("transform", `translate(${(1 - p(t, 8.0, .45)) * 60},0)`);
  const s4o = p(t, 22.0, .3) * (1 - p(t, 36.2, .4));
  $("#s4").setAttribute("opacity", s4o * (t > 28.4 ? lerp(1, .08, p(t, 28.4, .4)) : 1));
  /* fills (rang bharna) after their op */
  document.querySelectorAll(".fl").forEach(f => { const [a, d] = OPS[f.dataset.after]; f.setAttribute("opacity", p(t, a + d + .02, .35) * .92); });
  /* taala girna */
  const lk = t < 6.15 ? 0 : E.ease.bounce(clamp((t - 6.15) / .55));
  $("#lock").setAttribute("transform", `translate(0,${(1 - lk) * -260})`);
  $("#lock").setAttribute("opacity", t < 6.12 ? 0 : 1);
  const bnd = p(t, 6.6, .4, "back"); const B = $("#band");
  B.setAttribute("opacity", clamp((t - 6.6) / .1)); B.setAttribute("transform", `translate(395,410) scale(${Math.max(0, bnd)}) rotate(-8) translate(-395,-410)`);
  /* raat: taare + khidki roshni */
  document.querySelectorAll("#stars circle").forEach(c => { const k = +c.dataset.k; c.setAttribute("opacity", p(t, 22.3 + k * .03, .3) * (.45 + .55 * Math.abs(Math.sin(t * (1.3 + k % 5 * .4) + k)))); });
  const wl = p(t, 24.4, .45, "out"), fl = .85 + .15 * Math.sin(t * 9);
  ["#win1g", "#win2g", "#doorg"].forEach(s => $(s).setAttribute("opacity", wl * fl));
  ["#win1", "#win2", "#door"].forEach(s => $(s).setAttribute("fill", wl > .02 ? `rgb(${lerp(43, 255, wl)|0},${lerp(54, 214, wl)|0},${lerp(114, 102, wl)|0})` : "#2b3672"));
  /* pencil kaam */
  const {tip, vis} = drawOps(t);
  const pen = $("#pencil");
  if (tip && vis > 0) {
    const r = svg.getBoundingClientRect(), s = r.width / 492;
    set(pen, {opacity: vis, left: (r.left + tip[0] * s) + "px", top: (r.top + tip[1] * s - 15) + "px",
      transform: `rotate(${-38 + Math.sin(t * 17) * 3}deg) translateX(${-2 + Math.sin(t * 30) * 1.5}px)`});
  } else set(pen, {opacity: 0});
  /* chip + term */
  const chipTxt = t < 21.7 ? ["1", "छुट्टी के दिन क्या बंद?", 8.3] : ["2", "फिर भी एक डाकघर खुला", 22.2];
  const chip = $("#chip"); chip.querySelector("span").textContent = chipTxt[0]; chip.querySelector("em").textContent = chipTxt[1];
  const chipOn = (t > 8.3 && t < 17.15) || (t > 22.2 && t < 36.3);
  const ck = p(t, chipTxt[2], .45, "back");
  set(chip, {opacity: chipOn ? clamp((t - chipTxt[2]) / .12) * (t > 16.95 && t < 17.2 ? 1 - p(t, 16.95, .2) : 1) * (1 - p(t, 36.1, .2)) : 0,
    transform: `translateX(${(1 - ck) * -40}px)`});
  const termSpan = t < 21.7 ? ["Postal holiday", 8.6, 17.0] : ["Night Post Office", 25.1, 28.3];
  $("#term b").textContent = termSpan[0];
  const tk = p(t, termSpan[1], .45, "back");
  set("#term", {opacity: clamp((t - termSpan[1]) / .12) * (1 - p(t, termSpan[2], .25)), transform: `translateX(-50%) translateY(${(1 - tk) * -14}px) scale(${.85 + .15 * tk})`});
  /* banner */
  const bk = p(t, 17.2, .45, "back");
  set("#banner", {opacity: clamp((t - 17.2) / .1) * (1 - p(t, 21.4, .25)), transform: `scale(${Math.max(0, bk)})`});
  /* cards */
  function card(id, tin, tout, optsT, good, bad) {
    const ki = p(t, tin, .55, "back"), ko = p(t, tout, .4, "inout");
    set("#" + id, {opacity: clamp((t - tin) / .15) * (1 - ko), transform: `translateY(${(1 - ki) * 80 - ko * 60}px) rotate(${lerp(-5, -1, ki)}deg)`});
    optsT.forEach(([oid, ta]) => { const k = p(t, ta, .3); set("#" + oid, {opacity: k, transform: `translateX(${(1 - k) * -16}px)`}); });
    if (good) set("#" + good[0], {background: `rgba(22,163,74,${.16 * p(t, good[1], .3)})`});
    if (bad) set("#" + bad[0], {background: `rgba(220,38,38,${.12 * p(t, bad[1], .3)})`, color: t > bad[1] ? "#991b1b" : ""});
  }
  card("c8", 17.4, 21.5, [["c8a", 17.95], ["c8b", 18.15], ["c8c", 18.35]], ["c8c", 19.45]);
  card("c4", 28.6, 36.2, [["c4a", 29.15], ["c4b", 29.3], ["c4c", 29.45], ["c4d", 29.6]], ["c4d", 32.55], ["c4a", 33.3]);
  ink2.querySelectorAll("path").forEach(pth => { const c = $("#" + pth.dataset.card); pth.style.opacity = c.style.opacity || 0; });
  /* thappa */
  let shk = [0, 0];
  for (const id in STAMPS) {
    const a = STAMPS[id], k = p(t, a, .2, "out");
    set("#" + id, {opacity: clamp((t - a) / .06), transform: `rotate(-9deg) scale(${lerp(2.6, 1, k)})`});
    const s = shake(t, a + .2, .3, 6); shk = [shk[0] + s[0], shk[1] + s[1]];
  }
  const s2 = shake(t, 6.7, .3, 5); shk = [shk[0] + s2[0], shk[1] + s2[1]];
  set("#boardWrap", {transform: `translate(${shk[0]}px,${shk[1]}px)`});
  /* pills */
  set("#pillsT", {opacity: p(t, 29.9, .3) * (1 - p(t, 36.1, .2))});
  document.querySelectorAll(".pill").forEach((pl, i) => { const k = p(t, PILLS[i], .4, "back");
    set(pl, {opacity: clamp((t - PILLS[i]) / .1) * (1 - p(t, 36.1, .2)), transform: `scale(${Math.max(0, k)})`});
    pl.querySelector("i").style.boxShadow = t > PILLS[i] ? `0 0 0 ${(((t - PILLS[i]) * 10) % 8)}px rgba(255,216,74,${.5 - ((t - PILLS[i]) * 10 % 8) / 16})` : "none"; });
  /* trap */
  const tp = p(t, 33.4, .35, "out");
  set("#tape", {opacity: clamp((t - 33.4) / .08) * (1 - p(t, 36.0, .25)), transform: `rotate(-7deg) translateX(${(1 - tp) * -560}px)`});
  const tn = p(t, 33.8, .4, "back");
  set("#trapNote", {opacity: clamp((t - 33.8) / .1) * (1 - p(t, 36.0, .25)), transform: `scale(${Math.max(0, tn)})`});
  /* teaser */
  const tz = p(t, 36.5, .5, "back");
  set("#teaser", {opacity: clamp((t - 36.5) / .15), transform: `translateY(${(1 - tz) * 40}px) scale(${.8 + .2 * tz})`});
  /* captions */
  CAPS.forEach((c, i) => {
    const el = capEls[i]; const vis = t >= c[0] - .05 && t <= c[1];
    el.style.opacity = vis ? 1 - p(t, c[1] - .2, .2) : 0;
    if (!vis) return;
    [...el.children].forEach((w, j) => { const ti = c[0] + j * .07, k = p(t, ti, .3, "back");
      w.style.opacity = clamp((t - ti) / .08); w.style.transform = `translateY(${(1 - k) * 22}px) scale(${.7 + .3 * Math.max(0, k)})`; });
  });
}
window.seek = seek;

/* awaaz ke pal (audio mix ke liye) */
window.SFX = function () {
  const L = [{k: "power", t: .1}];
  for (const n in OPS) { const [a, d] = OPS[n]; L.push({k: n.startsWith("x") || n.startsWith("strike") ? "swish" : "pencil", t: a, d}); }
  [6.62].forEach(t => L.push({k: "thud", t}));
  for (const id in STAMPS) L.push({k: "stamp", t: STAMPS[id] + .18});
  [7.75, 17.4, 21.6, 28.6, 36.45].forEach(t => L.push({k: "whoosh", t}));
  [19.5, 32.6].forEach(t => L.push({k: "ding", t}));
  L.push({k: "chime", t: 24.4});
  PILLS.forEach(t => L.push({k: "pop", t}));
  [8.3, 22.2].forEach(t => L.push({k: "pop", t}));
  L.push({k: "tape", t: 33.45});
  return L;
};
})();
