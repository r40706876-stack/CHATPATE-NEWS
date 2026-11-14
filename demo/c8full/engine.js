/* POSTAL WALA DEEP CLASS - chhota animation engine (deterministic: seek(t) -> har cheez us pal ki jagah).
   Renderer har frame par window.seek(t) bulata hai, phir screenshot. Koi CSS animation / timer nahi. */
(function () {
  const E = {};
  E.clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  E.lerp = (a, b, k) => a + (b - a) * k;
  E.ease = {
    lin: k => k,
    out: k => 1 - Math.pow(1 - k, 3),
    inout: k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    back: k => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
    elastic: k => (k === 0 || k === 1) ? k : Math.pow(2, -10 * k) * Math.sin((k * 10 - 0.75) * (2 * Math.PI) / 3) + 1,
    bounce: k => { const n = 7.5625, d = 2.75;
      if (k < 1 / d) return n * k * k; if (k < 2 / d) return n * (k -= 1.5 / d) * k + 0.75;
      if (k < 2.5 / d) return n * (k -= 2.25 / d) * k + 0.9375; return n * (k -= 2.625 / d) * k + 0.984375; },
  };
  /* p(t, t0, d, easeName) -> 0..1 */
  E.p = (t, t0, d, e = 'out') => E.ease[e](E.clamp((t - t0) / Math.max(1e-6, d)));
  /* keyframes: [[t, value], ...] (value number ya array) -> t par value (beech me ease) */
  E.kf = (t, keys, e = 'inout') => {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      if (t <= keys[i][0]) {
        const [t0, a] = keys[i - 1], [t1, b] = keys[i];
        const k = E.ease[keys[i][2] || e]((t - t0) / Math.max(1e-6, t1 - t0));
        return Array.isArray(a) ? a.map((v, j) => E.lerp(v, b[j], k)) : E.lerp(a, b, k);
      }
    }
    return keys[keys.length - 1][1];
  };
  E.$ = s => document.querySelector(s);
  E.set = (el, o) => { if (typeof el === 'string') el = E.$(el); if (!el) return; for (const k in o) el.style[k] = o[k]; };
  /* pop-in: scale 0 -> 1 (back ease) + opacity, optional chhota jhoola */
  E.pop = (el, t, t0, d = 0.45, extra = '') => {
    const k = E.p(t, t0, d, 'back');
    E.set(el, { opacity: E.clamp((t - t0) / 0.12), transform: `scale(${Math.max(0, k)}) ${extra}` });
  };
  /* kinetic caption: shabd ek-ek karke uchhalte hain, khaas shabd rangeen */
  E.caption = (el, words, t, t0, rate) => {
    if (typeof el === 'string') el = E.$(el);
    if (!el.dataset.built) {
      el.innerHTML = words.map(w => `<span class="w${w.hl ? ' hl ' + w.hl : ''}">${w.t}</span>`).join(' ');
      el.dataset.built = 1;
    }
    [...el.children].forEach((s, i) => {
      const ti = t0 + i * rate, k = E.p(t, ti, 0.32, 'back');
      s.style.opacity = E.clamp((t - ti) / 0.08);
      s.style.transform = `translateY(${(1 - k) * 26}px) scale(${0.6 + 0.4 * Math.max(0, k)})`;
    });
  };
  E.shake = (t, t0, d = 0.35, amp = 7) => {
    const k = (t - t0) / d;
    if (k < 0 || k > 1) return [0, 0];
    const a = amp * (1 - k);
    return [Math.sin(t * 90) * a, Math.cos(t * 77) * a * 0.7];
  };
  window.E = E;
})();
