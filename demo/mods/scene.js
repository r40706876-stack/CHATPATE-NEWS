(function () {
const {p, clamp, lerp, $, set, shake} = E;
const B = [0, 2.4, 8.4, 16.4, 19.6, 26.0, 31.6, 36.2, 42.0, 45.2];   /* module seemaayein */
window.TOTAL = 45.2;
const MODS = ["m0", "m1", "m2", null, "m4", "m5", "m6", "m7", "m8"];
const CAPS = [
  [2.6, 5.4, "रविवार — सुबह से रात तक *आम डाकघर बंद*।"],
  [5.5, 8.2, "पर रात में भी — *नाइट PO* खुला।"],
  [8.6, 12.2, "ज़रूरी चिट्ठी? डाकघर पर *ताला*…"],
  [12.3, 16.2, "तो रास्ता — स्टेशन वाला *RMS*!"],
  [19.8, 22.8, "टिकट की जगह *मशीन की छाप*…"],
  [22.9, 25.8, "ऐसे लेख *बॉक्स में नहीं* जाते।"],
  [26.2, 31.4, "आम चिट्ठी पर लेट फीस, *अखबार* पर नहीं।"],
  [31.8, 36.0, "Clause 7 से *7 राज्यों* के पेपर में सवाल।"],
  [36.4, 39.0, "*3 सेकंड* — जवाब सोचो!"],
  [39.1, 41.9, "नहीं! *फ्रैंक लेख* बॉक्स में नहीं।"],
  [42.3, 45.2, "रोज़ एक clause — *फ़ॉलो* करो।"],
];
const STATES = ["पंजाब 2024", "गुजरात 2024", "मध्य प्रदेश 2024", "राजस्थान 2024", "दिल्ली 2023", "झारखंड 2022", "पंजाब 2021", "आंध्र 2020"];
const NS = "http://www.w3.org/2000/svg";
let built = false, capEls = [], r1L, r2L;
function mk(tag, a, par) { const e = document.createElementNS(NS, tag); for (const k in a) e.setAttribute(k, a[k]); par.appendChild(e); return e; }

function build() {
  built = true;
  const tk = $("#ticks");
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; mk("line", {x1: Math.sin(a) * 88, y1: -Math.cos(a) * 88, x2: Math.sin(a) * (i % 3 ? 80 : 72), y2: -Math.cos(a) * (i % 3 ? 80 : 72), stroke: "#1e3a8a", "stroke-width": i % 3 ? 3 : 6, "stroke-linecap": "round"}, tk); }
  const st = $("#stars1"); for (let i = 0; i < 24; i++) mk("circle", {cx: (i * 97.3) % 490 + 8, cy: (i * 41.7) % 170 + 8, r: .8 + (i % 3) * .6, fill: "#fff", "data-k": i}, st);
  const city = $("#city");
  [[0, 330, 60], [52, 300, 50], [96, 350, 44], [190, 320, 56], [240, 290, 46], [280, 340, 40], [420, 310, 50], [460, 340, 48]].forEach(([x, y, w], i) => {
    mk("rect", {x, y, width: w, height: 540 - y, fill: "#0f172a", opacity: .55}, city);
    for (let r = y + 14; r < 400; r += 22) for (let c = x + 8; c < x + w - 10; c += 16) mk("rect", {x: c, y: r, width: 8, height: 10, fill: "#fbbf24", class: "cw", "data-k": (c * 7 + r * 3) % 17, opacity: 0}, city);
  });
  let sl = ""; for (let x = -40; x < 560; x += 18) sl += `M${x},104 v22 `; $("#sleepers").setAttribute("d", sl);
  r1L = $("#r1").getTotalLength(); r2L = $("#r2").getTotalLength();
  const ch = $("#chips7"); STATES.forEach(s => { const d = document.createElement("span"); d.className = "chip7"; d.textContent = s; ch.appendChild(d); });
  const cap = $("#cap");
  CAPS.forEach(c => { const d = document.createElement("div"); d.style.cssText = "position:absolute;left:0;right:0;top:0;opacity:0";
    const ws = []; c[2].split("*").forEach((pt, i) => pt.trim().split(/\s+/).filter(Boolean).forEach(w => ws.push(`<span class="w${i % 2 ? " hl" : ""}">${w}</span>`)));
    d.innerHTML = ws.join(" "); cap.appendChild(d); capEls.push(d); });
}

function seek(t) {
  if (!built) build();
  set("#o1", {transform: `translate(${Math.sin(t * .35) * 40}px,${Math.cos(t * .27) * 50}px)`});
  set("#o2", {transform: `translate(${Math.cos(t * .3) * 40}px,${Math.sin(t * .22) * 40}px)`});
  set("#top", {opacity: p(t, .1, .5)});
  E.pop($("#logo"), t, .25, .5);
  document.querySelectorAll("#rail b").forEach((b, i) => b.style.width = (i < 2 ? 100 : i === 2 ? 100 * p(t, 2.4, 42, "lin") : 0) + "%");
  /* kaunsa module dikhe */
  let cur = 0; for (let i = 0; i < B.length - 1; i++) if (t >= B[i]) cur = i;
  MODS.forEach((m, i) => { if (m) $("#" + m).style.opacity = i === cur ? 1 : 0; });
  /* wipe (pehchaan wala laal patta) */
  let wx = -900;
  for (let i = 1; i < B.length - 1; i++) { const a = B[i] - .25; if (t >= a && t <= a + .5) wx = lerp(-700, 820, E.ease.inout((t - a) / .5)); }
  set("#wipe", {left: wx + "px"});
  /* stage halka jhatka */
  let sk = [0, 0];
  const add = s => { sk = [sk[0] + s[0], sk[1] + s[1]]; };

  /* M0 sting */
  const fl0 = p(t, .35, .5, "inout");
  $("#flap0").style.transform = `scaleY(${1 - 2 * fl0})`;
  $("#letter0").setAttribute("transform", `translate(0,${lerp(140, -40, p(t, .7, .7, "back"))})`);
  set("#m0", {transform: `scale(${1 + p(t, 1.8, .6, "inout") * .15})`});

  /* M1 ghadi */
  const dk = p(t, 2.6, 5.0, "inout");                          /* 9 baje -> 11 baje raat */
  const hrs = 9 + 14 * dk;
  $("#hh").setAttribute("transform", `rotate(${hrs * 30})`); $("#mh").setAttribute("transform", `rotate(${hrs * 360})`);
  const hh = Math.floor(hrs) % 24, label = hh < 12 ? "सुबह" : hh < 17 ? "दोपहर" : hh < 20 ? "शाम" : "रात";
  $("#clkT").textContent = `${label} ${((hh + 11) % 12) + 1}:00`;
  const night = p(t, 4.6, 2.2, "inout");
  const sky = (a, b) => `rgb(${lerp(a[0], b[0], night) | 0},${lerp(a[1], b[1], night) | 0},${lerp(a[2], b[2], night) | 0})`;
  $("#sky").style.background = `linear-gradient(180deg,${sky([125, 190, 255], [11, 16, 41])},${sky([254, 230, 160], [36, 42, 92])})`;
  $("#sun").setAttribute("transform", `translate(${dk * 340},${Math.sin(dk * Math.PI) * -60 + dk * 260})`);
  $("#sun").setAttribute("opacity", 1 - night);
  $("#moon1").setAttribute("opacity", night);
  document.querySelectorAll("#stars1 circle").forEach(c => c.setAttribute("opacity", night * (.4 + .6 * Math.abs(Math.sin(t * 1.7 + +c.dataset.k)))));
  document.querySelectorAll(".cw").forEach(c => c.setAttribute("opacity", night > (+c.dataset.k) / 20 ? .9 : 0));
  set("#clk", {}); $("#clk").setAttribute("transform", `translate(254,${lerp(250, 200, p(t, 2.4, .6))}) scale(${lerp(.6, 1, p(t, 2.45, .55, "back")) * (1 - .12 * night)})`);
  $("#band1").setAttribute("opacity", p(t, 3.4, .3)); $("#band1").setAttribute("transform", `scale(${Math.max(.01, p(t, 3.4, .4, "back"))})`);
  const lit = p(t, 6.0, .4);
  ["#npoW1", "#npoW2", "#npoD"].forEach(s => $(s).setAttribute("fill", lit > .5 ? "#ffcf4a" : "#374151"));
  $("#npoSign").setAttribute("fill", lit > .5 ? "#c81e1e" : "#374151"); $("#npoTxt").setAttribute("fill", lit > .5 ? "#fff" : "#9ca3af");
  $("#khula1").setAttribute("opacity", p(t, 6.3, .3));

  /* M2 naksha */
  const cam = p(t, 8.4, 7.8, "inout");
  $("#mapG").setAttribute("transform", `translate(254,270) scale(${lerp(1.25, 1.0, p(t, 8.4, 1.2, "out")) + .05 * Math.sin(cam * Math.PI)}) translate(${-254 + lerp(-30, 20, cam)},${-270 + lerp(20, -10, cam)})`);
  const pm = E.ease.bounce(clamp((t - 8.7) / .6));
  $("#pinMe").setAttribute("transform", `translate(365,${430 - (1 - pm) * 200})`);
  const r1 = p(t, 9.4, 1.6, "inout"); $("#r1").style.strokeDasharray = `14 10`; $("#r1").setAttribute("stroke-dashoffset", 0);
  $("#r1").style.clipPath = ""; $("#r1").setAttribute("opacity", t < 9.4 ? 0 : 1 - p(t, 12.2, .4));
  $("#r1").style.strokeDasharray = `${r1 * r1L} ${r1L}`;
  const xm = p(t, 11.1, .4, "back"); $("#xMark").setAttribute("opacity", clamp((t - 11.1) / .1));
  $("#xMark").setAttribute("transform", `translate(205,292) scale(${Math.max(.01, xm)})`);
  if (t > 11.2 && t < 11.7) add(shake(t, 11.2, .4, 5));
  const r2 = p(t, 12.4, 1.8, "inout"); $("#r2").style.strokeDasharray = `${r2 * r2L} ${r2L}`; $("#r2").setAttribute("opacity", t < 12.4 ? 0 : 1);
  $("#train").setAttribute("transform", `translate(${lerp(-200, 620, p(t, 12.6, 3.4, "inout"))},0)`);
  const ok = p(t, 14.3, .4, "back"); $("#pinOk").setAttribute("opacity", clamp((t - 14.3) / .1)); $("#pinOk").setAttribute("transform", `translate(405,190) scale(${Math.max(.01, ok)})`);
  set("#feeTag", {opacity: clamp((t - 14.7) / .1), transform: `translate(${150}px,${-150}px) scale(${Math.max(0, p(t, 14.7, .4, "back"))})`});
  set("#t2", {opacity: p(t, 13.0, .3), transform: `translateX(-50%) translateY(${(1 - p(t, 13.0, .4, "back")) * -12}px)`});

  /* M3 bada shabd (poori screen) */
  const kOn = t >= 16.4 && t < 19.6;
  set("#kin", {opacity: kOn ? 1 : 0});
  if (kOn) {
    const k1 = p(t, 16.5, .35, "back"); set("#kin .k1", {opacity: clamp((t - 16.5) / .1), transform: `scale(${lerp(2, 1, k1)})`});
    const k2 = p(t, 17.3, .22, "out"); set("#kin .k2", {opacity: clamp((t - 17.3) / .05), transform: `scale(${lerp(3, 1, k2)})`});
    set("#kin .k3", {opacity: p(t, 17.9, .4), transform: `translateY(${(1 - p(t, 17.9, .5)) * 20}px)`});
    document.querySelectorAll("#kin .coin").forEach((c, i) => { const a = i / 6 * Math.PI * 2 + .4, k = p(t, 17.45, .9, "out");
      set(c, {opacity: k > 0 ? 1 - p(t, 18.9, .5) : 0, transform: `translate(${Math.cos(a) * 190 * k}px,${Math.sin(a) * 150 * k + 60 * k * k}px) rotate(${k * 360}deg)`}); });
    const s = shake(t, 17.5, .35, 12); set("#kin", {transform: `translate(${s[0]}px,${s[1]}px)`});
  }

  /* M4 lens */
  const lin = p(t, 20.0, 1.0, "inout");
  const lx = lerp(560, 321, lin) + Math.sin(t * 1.8) * 6 * lin, ly = lerp(420, 201, lin) + Math.cos(t * 1.4) * 5 * lin;
  const lout = p(t, 22.7, .5, "inout");
  $("#lensG").setAttribute("transform", `translate(${lerp(lx, 620, lout)},${lerp(ly, 120, lout)})`);
  const Z = 2.1; $("#zoomArt").setAttribute("transform", `scale(${Z}) translate(${-lx},${-ly})`);
  set("#lensLbl", {opacity: p(t, 21.2, .3) * (1 - p(t, 22.7, .3)), transform: `translateY(${(1 - p(t, 21.2, .4, "back")) * 20}px)`});
  set("#t4", {opacity: p(t, 20.4, .3), transform: `translateX(-50%) translateY(${(1 - p(t, 20.4, .4, "back")) * -12}px)`});
  const mv = p(t, 23.0, .8, "inout"), bk = p(t, 23.9, .5, "out") * (1 - p(t, 24.6, .6, "inout"));
  $("#envG").setAttribute("transform", `translate(${lerp(0, 230, mv) - bk * 120},${lerp(0, 150, mv)}) scale(${lerp(1, .42, mv)}) rotate(${-bk * 12})`);
  $("#boxG").setAttribute("opacity", p(t, 22.8, .3));
  const no = p(t, 24.0, .35, "back"); $("#noG").setAttribute("opacity", clamp((t - 24.0) / .08)); $("#noG").setAttribute("transform", `translate(300,330) scale(${Math.max(.01, no)})`);
  if (t > 23.8 && t < 24.4) add(shake(t, 23.85, .4, 6));

  /* M5 tulna */
  set("#hL", {transform: `translateX(${(1 - p(t, 26.0, .5, "out")) * -260}px)`});
  set("#hR", {transform: `translateX(${(1 - p(t, 26.2, .5, "out")) * 260}px)`});
  set("#vs", {transform: `scale(${Math.max(0, p(t, 26.7, .45, "back"))}) rotate(${(1 - p(t, 26.7, .5)) * 180}deg)`});
  set("#cL", {transform: `translateY(${(1 - E.ease.bounce(clamp((t - 27.3) / .6))) * -120}px)`});
  set("#vL", {opacity: p(t, 28.0, .3), transform: `scale(${Math.max(0, p(t, 28.0, .4, "back"))})`});
  set("#cR", {transform: `translateY(${(1 - E.ease.bounce(clamp((t - 28.8) / .6))) * -120}px)`});
  const xr = p(t, 29.5, .3); $("#cRxp").setAttribute("stroke-dasharray", "71"); $("#cRxp").setAttribute("stroke-dashoffset", 71 * (1 - xr));
  set("#vR", {opacity: p(t, 29.9, .3), transform: `scale(${Math.max(0, p(t, 29.9, .4, "back"))})`});

  /* M6 ginti */
  $("#n1").textContent = Math.round(7 * p(t, 32.0, 1.4, "out"));
  $("#n2").textContent = Math.round(8 * p(t, 32.3, 1.4, "out"));
  set("#n1", {transform: `scale(${1 + .15 * (1 - p(t, 33.4, .3))})`}); set("#n2", {transform: `scale(${1 + .15 * (1 - p(t, 33.7, .3))})`});
  document.querySelectorAll(".chip7").forEach((c, i) => { const a = 33.9 + i * .18, k = p(t, a, .35, "back"); set(c, {opacity: clamp((t - a) / .08), transform: `scale(${Math.max(0, k)})`}); });

  /* M7 flashcard */
  set("#fc", {transform: `translateY(${(1 - p(t, 36.2, .5, "back")) * 60}px)`, opacity: p(t, 36.2, .25)});
  const left = clamp(3 - (t - 36.4) * (3 / 2.5), 0, 3);
  $("#cnt7").textContent = Math.ceil(left) || 0; $("#ring7").setAttribute("stroke-dashoffset", 201 * (1 - left / 3));
  const fl = p(t, 39.0, .6, "inout"); set("#fcIn", {transform: `rotateY(${fl * 180}deg) scale(${1 + .06 * Math.sin(fl * Math.PI)})`});

  /* M8 outro */
  $("#letter8").setAttribute("transform", `translate(0,${lerp(-10, 150, p(t, 42.3, .6, "inout"))})`);
  const f8 = p(t, 42.9, .4, "inout"); $("#flap8").style.transform = `scaleY(${-1 + 2 * f8})`;
  const s8 = p(t, 43.35, .22, "out"); $("#seal8").setAttribute("transform", `translate(254,352) scale(${lerp(2.4, 1, s8)})`); $("#seal8").setAttribute("opacity", clamp((t - 43.35) / .05));
  if (t > 43.55) add(shake(t, 43.57, .35, 7));
  set("#fol", {opacity: p(t, 43.9, .3), transform: `scale(${(Math.max(0, p(t, 43.9, .4, "back"))) * (1 + .04 * Math.sin(t * 8))})`});

  set("#stage", {transform: `translate(${sk[0]}px,${sk[1]}px)`});
  /* captions */
  CAPS.forEach((c, i) => { const el = capEls[i], vis = t >= c[0] - .05 && t <= c[1];
    el.style.opacity = vis ? 1 - p(t, c[1] - .2, .2) : 0; if (!vis) return;
    [...el.children].forEach((w, j) => { const ti = c[0] + j * .07, k = p(t, ti, .3, "back");
      w.style.opacity = clamp((t - ti) / .08); w.style.transform = `translateY(${(1 - k) * 22}px) scale(${.7 + .3 * Math.max(0, k)})`; }); });
}
window.seek = seek;
window.SFX = function () {
  const L = [{k: "power", t: .1}, {k: "whoosh", t: .4}, {k: "pop", t: .9}];
  for (let i = 1; i < B.length - 1; i++) L.push({k: "whoosh", t: B[i] - .25});
  for (let x = 2.7; x < 7.5; x += .5) L.push({k: "tick", t: x});
  L.push({k: "thud", t: 3.45}, {k: "chime", t: 6.0}, {k: "pop", t: 9.2}, {k: "pencil", t: 9.4, d: 1.6}, {k: "stamp", t: 11.15},
    {k: "pencil", t: 12.4, d: 1.8}, {k: "whoosh", t: 12.8}, {k: "ding", t: 14.35}, {k: "pop", t: 14.75}, {k: "pop", t: 13.0},
    {k: "pop", t: 16.5}, {k: "stamp", t: 17.32}, {k: "ding", t: 17.5}, {k: "swish", t: 20.0}, {k: "pop", t: 20.4}, {k: "pop", t: 21.2},
    {k: "swish", t: 23.0}, {k: "thud", t: 23.85}, {k: "stamp", t: 24.0}, {k: "swish", t: 26.0}, {k: "swish", t: 26.2}, {k: "pop", t: 26.7},
    {k: "thud", t: 27.5}, {k: "ding", t: 28.0}, {k: "thud", t: 29.0}, {k: "swish", t: 29.5}, {k: "pop", t: 29.9});
  for (let x = 32.0; x < 33.7; x += .12) L.push({k: "tick", t: x});
  for (let i = 0; i < 8; i++) L.push({k: "pop", t: 33.9 + i * .18});
  [36.4, 37.23, 38.07].forEach(x => L.push({k: "tick", t: x}));
  L.push({k: "whoosh", t: 39.0}, {k: "ding", t: 39.4}, {k: "swish", t: 42.3}, {k: "whoosh", t: 42.9}, {k: "stamp", t: 43.5}, {k: "chime", t: 43.9});
  return L;
};
})();
