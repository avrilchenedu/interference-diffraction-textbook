/* 互動模擬元件：superposition / ripple / doubleslit / singleslit / thinfilm
   SIMS.mount(element, name) — 建立模擬；回傳 { destroy } */
window.SIMS = (() => {
  const TAU = Math.PI * 2;

  function wl2rgb(nm) { // 可見光波長 → RGB (0–1)
    let r = 0, g = 0, b = 0;
    if (nm < 440) { r = -(nm - 440) / 60; b = 1; }
    else if (nm < 490) { g = (nm - 440) / 50; b = 1; }
    else if (nm < 510) { g = 1; b = -(nm - 510) / 20; }
    else if (nm < 580) { r = (nm - 510) / 70; g = 1; }
    else if (nm < 645) { r = 1; g = -(nm - 645) / 65; }
    else { r = 1; }
    let f = 1;
    if (nm < 420) f = 0.3 + 0.7 * (nm - 380) / 40;
    else if (nm > 700) f = 0.3 + 0.7 * (780 - nm) / 80;
    return [r * f, g * f, b * f];
  }
  const css = (rgb, k = 1) => `rgb(${rgb.map((v) => Math.round(255 * Math.min(1, v * k))).join(',')})`;

  function shell(el, title, note) {
    el.classList.add('sim');
    el.innerHTML = `<div class="sim-head"><b>🔬 ${title}</b>${note ? `<span class="sim-note">${note}</span>` : ''}</div>
      <div class="sim-stage"></div><div class="sim-ctrl"></div><div class="sim-read"></div>`;
    return { stage: el.querySelector('.sim-stage'), ctrl: el.querySelector('.sim-ctrl'), read: el.querySelector('.sim-read') };
  }
  function canvas(parent, w, h) {
    const c = document.createElement('canvas');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    c.width = w * dpr; c.height = h * dpr; c.style.width = '100%'; c.style.maxWidth = w + 'px';
    c.style.aspectRatio = `${w} / ${h}`;
    const ctx = c.getContext('2d'); ctx.scale(dpr, dpr);
    parent.appendChild(c);
    return { c, ctx, w, h };
  }
  function slider(parent, label, min, max, step, val, fmt, on) {
    const wrap = document.createElement('label');
    wrap.className = 'sim-slider';
    wrap.innerHTML = `<span>${label}</span><input type="range" min="${min}" max="${max}" step="${step}" value="${val}"><output></output>`;
    const inp = wrap.querySelector('input'), out = wrap.querySelector('output');
    const upd = () => { out.textContent = fmt(+inp.value); };
    inp.addEventListener('input', () => { upd(); on(+inp.value); });
    upd(); parent.appendChild(wrap);
    return { set(v) { inp.value = v; upd(); }, get: () => +inp.value };
  }
  function button(parent, label, on, cls = '') {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'sim-btn ' + cls; b.textContent = label;
    b.addEventListener('click', on); parent.appendChild(b); return b;
  }
  function loop(el, step) { // 只在可見時執行動畫
    let raf = 0, last = 0, visible = true, alive = true;
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible && !raf) go(); });
    io.observe(el);
    function frame(t) {
      raf = 0; if (!alive) return;
      const dt = last ? Math.min(0.05, (t - last) / 1000) : 0; last = t;
      step(dt);
      if (visible) go(); else last = 0;
    }
    function go() { if (!raf) raf = requestAnimationFrame(frame); }
    go();
    return () => { alive = false; io.disconnect(); cancelAnimationFrame(raf); };
  }
  const sgn = (v) => (v > 0 ? '＋' : v < 0 ? '－' : '') + Math.abs(v).toFixed(1);

  /* ------------------------------------------------ 1. 波的疊加（依 07B 模擬需求腳本） */
  function superposition(el) {
    const ui = shell(el, '波的疊加：兩個脈衝相遇', '理想線性介質中的模型示意');
    const cv = canvas(ui.stage, 720, 360);
    const S = { hA: 1, hB: 1, t: 0, play: false };
    const W = 0.2, V = 0.05; // 全寬 20% 畫面、波速每秒 5% 畫面寬度
    const pulse = (x, c, h) => (Math.abs(x - c) < W / 2 ? h * 0.5 * (1 + Math.cos(TAU * (x - c) / W)) : 0);
    const yA = (x) => pulse(x, 0.25 + V * S.t, S.hA);
    const yB = (x) => pulse(x, 0.75 - V * S.t, S.hB);
    function panel(y0, h, label) {
      const { ctx } = cv;
      ctx.fillStyle = '#f7f9fb'; ctx.fillRect(40, y0, 660, h);
      ctx.strokeStyle = '#c9d2dc'; ctx.lineWidth = 1;
      for (let v = -3; v <= 3; v++) { const yy = y0 + h / 2 - v * h / 6.4; ctx.beginPath(); ctx.moveTo(40, yy); ctx.lineTo(700, yy); ctx.stroke(); }
      ctx.strokeStyle = '#7b8794'; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(40, y0 + h / 2); ctx.lineTo(700, y0 + h / 2); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = '#5b6776'; ctx.font = '13px sans-serif';
      ctx.fillText(label, 46, y0 + 16); ctx.fillText('平衡位置', 640, y0 + h / 2 - 4);
      ctx.save(); ctx.translate(18, y0 + h / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('位移', -12, 0); ctx.restore();
      ctx.fillText('+3', 22, y0 + h / 2 - 3 * h / 6.4 + 4); ctx.fillText('-3', 22, y0 + h / 2 + 3 * h / 6.4 + 4);
    }
    function curve(f, y0, h, style) {
      const { ctx } = cv;
      ctx.beginPath();
      for (let i = 0; i <= 660; i++) { const x = i / 660; const yy = y0 + h / 2 - f(x) * h / 6.4; i ? ctx.lineTo(40 + i, yy) : ctx.moveTo(40 + i, yy); }
      ctx.strokeStyle = style.c; ctx.lineWidth = style.w; ctx.setLineDash(style.d || []); ctx.stroke(); ctx.setLineDash([]);
    }
    function draw() {
      const { ctx } = cv; ctx.clearRect(0, 0, 720, 360);
      panel(8, 160, '分波 A（細實線）、B（虛線）'); panel(190, 160, '合成繩形（粗實線）');
      curve(yA, 8, 160, { c: '#1f6fb2', w: 2 }); curve(yB, 8, 160, { c: '#d9822b', w: 2, d: [7, 5] });
      curve((x) => yA(x) + yB(x), 190, 160, { c: '#1d2733', w: 4 });
      ctx.strokeStyle = '#c0392b'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(370, 8); ctx.lineTo(370, 350); ctx.stroke();
      ctx.fillStyle = '#c0392b'; ctx.font = 'bold 14px sans-serif'; ctx.fillText('P', 376, 184);
      const a = yA(0.5), b = yB(0.5);
      ui.read.innerHTML = `<span>P 點　A：<b>${sgn(a)}</b></span><span>B：<b>${sgn(b)}</b></span><span>合成：<b>${sgn(a + b)}</b></span><span class="muted">t = ${S.t.toFixed(1)} 秒</span>`;
    }
    const reset = () => { S.t = 0; S.play = false; playBtn.textContent = '▶ 播放'; draw(); };
    const sA = slider(ui.ctrl, '脈衝高度 A（含正負號）', -1.5, 1.5, 0.1, 1, sgn, (v) => { S.hA = v; reset(); });
    const sB = slider(ui.ctrl, '脈衝高度 B（含正負號）', -1.5, 1.5, 0.1, 1, sgn, (v) => { S.hB = v; reset(); });
    const playBtn = button(ui.ctrl, '▶ 播放', () => { if (S.t > 14) S.t = 0; S.play = !S.play; playBtn.textContent = S.play ? '⏸ 暫停' : '▶ 播放'; }, 'primary');
    button(ui.ctrl, '同向：＋1、＋1', () => { S.hA = 1; S.hB = 1; sA.set(1); sB.set(1); reset(); });
    button(ui.ctrl, '反向：＋1、－1', () => { S.hA = 1; S.hB = -1; sA.set(1); sB.set(-1); reset(); });
    button(ui.ctrl, '重設', () => { S.hA = 1; S.hB = 1; sA.set(1); sB.set(1); reset(); });
    button(ui.ctrl, '跳到完全重疊', () => { S.t = 5; S.play = false; playBtn.textContent = '▶ 播放'; draw(); });
    draw();
    return loop(el, (dt) => { if (S.play) { S.t += dt; if (S.t > 15) { S.play = false; playBtn.textContent = '▶ 播放'; } draw(); } });
  }

  /* ------------------------------------------------ 2. 水波干涉（兩個同相點波源） */
  function ripple(el) {
    const ui = shell(el, '水波干涉：兩個同相點波源', '模型畫面，非真實水槽證據');
    const row = document.createElement('div'); row.className = 'sim-row'; ui.stage.appendChild(row);
    const NX = 200, NY = 150, SC = 3;
    const cv = canvas(row, NX * SC, NY * SC);
    const gr = canvas(row, 280, NY * SC);
    const off = document.createElement('canvas'); off.width = NX; off.height = NY;
    const octx = off.getContext('2d'); const img = octx.createImageData(NX, NY);
    const S = { d: 50, lam: 22, t: 0, play: true, mode: 'wave', pt: null, hist: [] };
    const src = () => [[NX / 2 - S.d / 2, 8], [NX / 2 + S.d / 2, 8]];
    const k = () => TAU / S.lam, w = TAU / 1.2;
    function field(x, y, t) {
      let v = 0;
      for (const [sx, sy] of src()) { const r = Math.hypot(x - sx, y - sy) + 1; v += Math.cos(k() * r - w * t) / Math.sqrt(r / 30 + 1); }
      return v;
    }
    function amp(x, y) {
      let re = 0, im = 0;
      for (const [sx, sy] of src()) { const r = Math.hypot(x - sx, y - sy) + 1; const a = 1 / Math.sqrt(r / 30 + 1); re += a * Math.cos(k() * r); im += a * Math.sin(k() * r); }
      return Math.hypot(re, im);
    }
    function presets() { // A：在中央腹線上；B：在第一條節線上
      const y = 95; const [s1, s2] = src();
      let best = null;
      for (let x = NX / 2; x < NX - 2; x += 0.5) { const dd = Math.abs(Math.hypot(x - s1[0], y - s1[1]) - Math.hypot(x - s2[0], y - s2[1])); if (Math.abs(dd - S.lam / 2) < 0.6) { best = x; break; } }
      return { A: [NX / 2, y], B: [best ?? NX / 2 + 20, y] };
    }
    function draw() {
      const t = S.t;
      for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
        let r, g, b;
        if (S.mode === 'wave') { const v = field(i, j, t) / 2; r = 40 + 70 * v; g = 110 + 80 * v; b = 190 + 60 * v; }
        else { const a = amp(i, j) / 2; r = 20 + 230 * a; g = 40 + 180 * a; b = 90 + 120 * a; }
        const p = 4 * (j * NX + i); img.data[p] = r; img.data[p + 1] = g; img.data[p + 2] = b; img.data[p + 3] = 255;
      }
      octx.putImageData(img, 0, 0);
      const { ctx } = cv; ctx.imageSmoothingEnabled = true; ctx.drawImage(off, 0, 0, NX * SC, NY * SC);
      ctx.fillStyle = '#ffd54a';
      for (const [sx, sy] of src()) { ctx.beginPath(); ctx.arc(sx * SC, sy * SC, 6, 0, TAU); ctx.fill(); }
      const P = presets();
      for (const [name, [x, y]] of Object.entries(P)) {
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x * SC, y * SC, 9, 0, TAU); ctx.stroke();
        ctx.fillStyle = '#fff'; ctx.font = 'bold 15px sans-serif'; ctx.fillText(name, x * SC + 11, y * SC - 8);
      }
      if (S.pt) { ctx.strokeStyle = '#ff5252'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(S.pt[0] * SC, S.pt[1] * SC, 7, 0, TAU); ctx.stroke(); }
      // 一段時間的起伏紀錄
      const g = gr.ctx; g.clearRect(0, 0, 280, NY * SC);
      g.fillStyle = '#f7f9fb'; g.fillRect(0, 0, 280, NY * SC);
      g.fillStyle = '#1d2733'; g.font = '13px sans-serif'; g.fillText('所選位置：位移隨時間變化', 10, 20);
      const mid = NY * SC / 2;
      g.strokeStyle = '#9aa5b1'; g.beginPath(); g.moveTo(10, mid); g.lineTo(270, mid); g.stroke();
      if (S.pt) {
        const H = S.hist; const sc = 50;
        g.strokeStyle = '#c0392b'; g.lineWidth = 2; g.beginPath();
        H.forEach((v, i) => { const x = 10 + i * 260 / 150; i ? g.lineTo(x, mid - v * sc) : g.moveTo(x, mid - v * sc); }); g.stroke();
        const A = amp(...S.pt);
        g.strokeStyle = '#2e6b4f'; g.setLineDash([5, 4]); g.lineWidth = 1;
        [mid - A * sc, mid + A * sc].forEach((y) => { g.beginPath(); g.moveTo(10, y); g.lineTo(270, y); g.stroke(); }); g.setLineDash([]);
        g.fillStyle = '#2e6b4f'; g.fillText(`振幅（最大位移）≈ ${A.toFixed(2)}`, 10, NY * SC - 14);
        ui.read.innerHTML = `<span>此刻位移：<b>${field(...S.pt, S.t).toFixed(2)}</b></span><span>一段時間的最大位移（振幅）：<b>${A.toFixed(2)}</b></span>`;
      } else {
        g.fillStyle = '#5b6776'; g.fillText('點選左圖中的 A、B 或任一位置', 10, mid - 10);
        ui.read.innerHTML = '<span class="muted">判讀須看一段時間的起伏。（點選水面任一位置）</span>';
      }
    }
    function pick(x, y) { S.pt = [x, y]; S.hist = []; }
    cv.c.addEventListener('click', (e) => {
      const r = cv.c.getBoundingClientRect(); pick((e.clientX - r.left) / r.width * NX, (e.clientY - r.top) / r.height * NY); draw();
    });
    const pb = button(ui.ctrl, '⏸ 暫停', () => { S.play = !S.play; pb.textContent = S.play ? '⏸ 暫停' : '▶ 播放'; }, 'primary');
    const mb = button(ui.ctrl, '顯示：振幅分布（腹線／節線）', () => { S.mode = S.mode === 'wave' ? 'amp' : 'wave'; mb.textContent = S.mode === 'wave' ? '顯示：振幅分布（腹線／節線）' : '顯示：瞬間水面'; draw(); });
    button(ui.ctrl, '選 A 點', () => { pick(...presets().A); draw(); });
    button(ui.ctrl, '選 B 點', () => { pick(...presets().B); draw(); });
    slider(ui.ctrl, '波源距離', 20, 90, 1, S.d, (v) => v, (v) => { S.d = v; S.hist = []; draw(); });
    slider(ui.ctrl, '波長', 12, 36, 1, S.lam, (v) => v, (v) => { S.lam = v; S.hist = []; draw(); });
    draw();
    return loop(el, (dt) => {
      if (!S.play) return;
      S.t += dt;
      if (S.pt) { S.hist.push(field(...S.pt, S.t) / 2); if (S.hist.length > 150) S.hist.shift(); }
      draw();
    });
  }

  /* ------------------------------------------------ 3. 雙狹縫干涉 */
  function doubleslit(el) {
    const ui = shell(el, '雙狹縫干涉：兩個相干次波源', '模型（非實拍）');
    const NX = 220, NY = 140, SC = 3;
    const cv = canvas(ui.stage, NX * SC + 90, NY * SC);
    const off = document.createElement('canvas'); off.width = NX; off.height = NY;
    const octx = off.getContext('2d'); const img = octx.createImageData(NX, NY);
    const S = { nm: 633, d: 28, t: 0, play: true, pick: 'B' };
    const BAR = 40, SCR = NX - 4;
    const lam = () => S.nm / 633 * 12;
    const slits = () => [[BAR, NY / 2 - S.d / 2], [BAR, NY / 2 + S.d / 2]];
    const w = TAU / 1.0;
    function field(x, y, t) {
      if (x < BAR) return Math.cos(TAU / lam() * (x - BAR) - w * t);
      let v = 0; for (const [sx, sy] of slits()) { const r = Math.hypot(x - sx, y - sy); v += Math.cos(TAU / lam() * r - w * t) / Math.sqrt(r / 25 + 1); }
      return v / 1.4;
    }
    function inten(y) { const [[, y1], [, y2]] = slits(); const dr = Math.hypot(SCR - BAR, y - y1) - Math.hypot(SCR - BAR, y - y2); return Math.cos(Math.PI * dr / lam()) ** 2; }
    function pts() { // B：中央亮紋上方第一條亮紋；D：第一條暗紋
      let B = NY / 2, D = NY / 2;
      for (let y = NY / 2; y > 2; y -= 0.25) { if (inten(y) < 0.01 && D === NY / 2) D = y; if (D !== NY / 2 && inten(y) > 0.995) { B = y; break; } }
      return { B, D };
    }
    function draw() {
      const rgb = wl2rgb(S.nm);
      for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
        const p = 4 * (j * NX + i);
        if (Math.abs(i - BAR) < 1.5 && !slits().some(([, sy]) => Math.abs(j - sy) < 2)) { img.data[p] = 60; img.data[p + 1] = 60; img.data[p + 2] = 60; img.data[p + 3] = 255; continue; }
        const v = (field(i, j, S.t) + 1.2) / 2.4;
        img.data[p] = 15 + 220 * rgb[0] * v; img.data[p + 1] = 15 + 220 * rgb[1] * v; img.data[p + 2] = 25 + 220 * rgb[2] * v; img.data[p + 3] = 255;
      }
      octx.putImageData(img, 0, 0);
      const { ctx } = cv; ctx.clearRect(0, 0, NX * SC + 90, NY * SC); ctx.drawImage(off, 0, 0, NX * SC, NY * SC);
      // 屏幕（時間平均光強度）
      for (let j = 0; j < NY * SC; j++) { const I = inten(j / SC); ctx.fillStyle = css(rgb, I); ctx.fillRect(NX * SC + 10, j, 30, 1); }
      ctx.strokeStyle = '#9aa5b1'; ctx.beginPath();
      for (let j = 0; j < NY * SC; j++) { const x = NX * SC + 45 + 40 * inten(j / SC); j ? ctx.lineTo(x, j) : ctx.moveTo(x, j); } ctx.stroke();
      ctx.fillStyle = '#1d2733'; ctx.font = '12px sans-serif'; ctx.fillText('屏幕', NX * SC + 12, 12);
      const P = pts(); const y = S.pick === 'B' ? P.B : P.D;
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.setLineDash([5, 4]);
      for (const [sx, sy] of slits()) { ctx.beginPath(); ctx.moveTo(sx * SC, sy * SC); ctx.lineTo(SCR * SC, y * SC); ctx.stroke(); }
      ctx.setLineDash([]);
      for (const [nm, yy] of [['B', P.B], ['D', P.D]]) {
        ctx.fillStyle = nm === S.pick ? '#ffd54a' : '#fff'; ctx.beginPath(); ctx.arc(SCR * SC, yy * SC, 6, 0, TAU); ctx.fill();
        ctx.font = 'bold 14px sans-serif'; ctx.fillText(nm, SCR * SC - 22, yy * SC + 5);
      }
      const [[, y1], [, y2]] = slits();
      const dr = Math.hypot(SCR - BAR, y - y1) - Math.hypot(SCR - BAR, y - y2);
      const n = Math.abs(dr / lam());
      const same = Math.abs(n - Math.round(n)) < 0.25;
      ui.read.innerHTML = `<span>${S.pick} 點：兩列光波到達時 <b>${same ? '同相' : '反相'}</b></span><span>→ <b>${same ? '建設性干涉，光強較強' : '破壞性干涉，理想下光強為零'}</b></span><span class="muted">路程差 ≈ ${n.toFixed(2)} 個波長</span>`;
    }
    const pb = button(ui.ctrl, '⏸ 暫停', () => { S.play = !S.play; pb.textContent = S.play ? '⏸ 暫停' : '▶ 播放'; }, 'primary');
    button(ui.ctrl, '選 B（亮紋）', () => { S.pick = 'B'; draw(); });
    button(ui.ctrl, '選 D（暗紋）', () => { S.pick = 'D'; draw(); });
    slider(ui.ctrl, '波長', 420, 680, 10, S.nm, (v) => v + ' nm', (v) => { S.nm = v; draw(); });
    slider(ui.ctrl, '縫距', 14, 50, 1, S.d, (v) => v, (v) => { S.d = v; draw(); });
    draw();
    return loop(el, (dt) => { if (S.play) { S.t += dt; draw(); } });
  }

  /* ------------------------------------------------ 4. 單狹縫繞射（可與雙狹縫比較） */
  function singleslit(el) {
    const ui = shell(el, '單狹縫繞射：縫內許多次波源', '遠場、均勻單色照明');
    const cv = canvas(ui.stage, 720, 330);
    const S = { a: 4, nm: 532, cmp: false, n: 9 };
    const sinc2 = (x) => (Math.abs(x) < 1e-6 ? 1 : (Math.sin(x) / x) ** 2);
    const I1 = (u) => sinc2(Math.PI * S.a * u / (S.nm / 532));
    const I2 = (u) => Math.cos(Math.PI * 12 * u / (S.nm / 532)) ** 2 * sinc2(Math.PI * 1.5 * u / (S.nm / 532));
    function draw() {
      const { ctx } = cv; ctx.clearRect(0, 0, 720, 330);
      const rgb = wl2rgb(S.nm);
      // 狹縫與次波源
      ctx.fillStyle = '#3d4650'; ctx.fillRect(40, 20, 10, 250);
      const hgt = S.a * 14; ctx.clearRect(40, 145 - hgt / 2, 10, hgt);
      ctx.fillStyle = css(rgb);
      for (let i = 0; i < S.n; i++) { const y = 145 - hgt / 2 + (i + 0.5) * hgt / S.n; ctx.beginPath(); ctx.arc(45, y, 3, 0, TAU); ctx.fill(); }
      ctx.fillStyle = '#5b6776'; ctx.font = '12px sans-serif';
      ctx.fillText('縫內各點視為次波源', 8, 296); ctx.fillText(`縫寬 ${S.a.toFixed(1)}`, 8, 314);
      // 屏幕亮度與曲線
      const X0 = 140, X1 = 700;
      const draws = [[I1, 30, '單狹縫']]; if (S.cmp) draws.push([I2, 175, '雙狹縫']);
      for (const [f, y0, lab] of draws) {
        for (let i = X0; i <= X1; i++) { const u = (i - (X0 + X1) / 2) / 560; ctx.fillStyle = css(rgb, Math.min(1, f(u) * 1.15)); ctx.fillRect(i, y0, 1, 40); }
        ctx.strokeStyle = '#1d2733'; ctx.lineWidth = 2; ctx.beginPath();
        for (let i = X0; i <= X1; i++) { const u = (i - (X0 + X1) / 2) / 560; const y = y0 + 125 - 75 * f(u); i === X0 ? ctx.moveTo(i, y) : ctx.lineTo(i, y); } ctx.stroke();
        ctx.fillStyle = '#1d2733'; ctx.font = 'bold 13px sans-serif'; ctx.fillText(lab + '（屏幕亮度）', X0, y0 - 6);
      }
      ui.read.innerHTML = S.cmp
        ? '<span>雙狹縫可近似為兩個分立次波源，單狹縫為連續分布的次波源。</span><span class="muted">兩者都運用波的疊加概念。</span>'
        : `<span>屏幕中央出現較寬、較亮的中央亮紋，兩側則有較窄、逐漸變弱的旁側亮紋</span><span class="muted">縮小縫寬，會使繞射展開角度增加，中央亮紋變寬。</span>`;
    }
    slider(ui.ctrl, '縫寬', 2, 8, 0.1, S.a, (v) => v.toFixed(1), (v) => { S.a = v; draw(); });
    slider(ui.ctrl, '波長', 420, 680, 10, S.nm, (v) => v + ' nm', (v) => { S.nm = v; draw(); });
    const cb = button(ui.ctrl, '與雙狹縫比較', () => { S.cmp = !S.cmp; cb.textContent = S.cmp ? '只看單狹縫' : '與雙狹縫比較'; draw(); });
    draw();
    return () => {};
  }

  /* ------------------------------------------------ 5. 薄膜干涉 */
  function thinfilm(el) {
    const ui = shell(el, '薄膜干涉：上表面與下表面的兩路反射光', '定性示意');
    const cv = canvas(ui.stage, 720, 340);
    const S = { maxd: 900, x: 0.45, mono: 0, n: 1.33 };
    const dAt = (x) => 60 + (S.maxd - 60) * x; // 膜厚隨位置變化（nm）
    const refl = (d, nm) => 1 + Math.cos(4 * Math.PI * S.n * d / nm + Math.PI); // 上表面反射有相位改變
    function color(d) {
      if (S.mono) { const k = refl(d, S.mono) / 2; return css(wl2rgb(S.mono), k); }
      let r = 0, g = 0, b = 0, sum = 0;
      for (let nm = 400; nm <= 700; nm += 10) { const c = wl2rgb(nm), k = refl(d, nm) / 2; r += c[0] * k; g += c[1] * k; b += c[2] * k; sum += 1; }
      return css([r / sum, g / sum, b / sum], 2.4);
    }
    function draw() {
      const { ctx } = cv; ctx.clearRect(0, 0, 720, 340);
      ctx.fillStyle = '#1d2733'; ctx.font = 'bold 13px sans-serif'; ctx.fillText('從上方看到的薄膜色彩（膜厚由左向右增加）', 40, 18);
      for (let i = 40; i <= 680; i++) { ctx.fillStyle = color(dAt((i - 40) / 640)); ctx.fillRect(i, 26, 1, 46); }
      // 剖面
      const top = 210, scale = 90 / S.maxd;
      ctx.fillStyle = '#cfe5f6'; ctx.beginPath(); ctx.moveTo(40, top);
      for (let i = 40; i <= 680; i++) ctx.lineTo(i, top + dAt((i - 40) / 640) * scale);
      ctx.lineTo(680, top); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = '#5b8db8'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(40, top); ctx.lineTo(680, top); ctx.stroke();
      ctx.beginPath(); for (let i = 40; i <= 680; i++) { const y = top + dAt((i - 40) / 640) * scale; i === 40 ? ctx.moveTo(i, y) : ctx.lineTo(i, y); } ctx.stroke();
      ctx.fillStyle = '#5b6776'; ctx.font = '12px sans-serif'; ctx.fillText('薄膜剖面（示意，厚度放大）', 40, 330);
      ctx.fillText('上表面', 684, top + 4);
      // 光線
      const X = 40 + S.x * 640, d = dAt(S.x), yb = top + d * scale;
      const ray = (x1, y1, x2, y2, c, dash) => { ctx.strokeStyle = c; ctx.lineWidth = 2.5; ctx.setLineDash(dash || []); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.setLineDash([]); };
      ray(X - 90, 100, X, top, '#f2b134');
      ray(X, top, X + 90, 100, '#e67e22');
      ray(X, top, X + 25, yb, '#f2b134', [5, 4]);
      ray(X + 25, yb, X + 50, top, '#f2b134', [5, 4]);
      ray(X + 50, top, X + 140, 100, '#c0392b');
      ctx.fillStyle = '#1d2733'; ctx.font = '12px sans-serif';
      ctx.fillText('入射光', X - 110, 96); ctx.fillText('① 上表面反射', X + 40, 112); ctx.fillText('② 下表面反射', X + 120, 128);
      ctx.strokeStyle = '#1d2733'; ctx.beginPath(); ctx.moveTo(X, 72); ctx.lineTo(X, 80); ctx.stroke();
      const nm = S.mono || 550, k = refl(d, nm) / 2;
      ui.read.innerHTML = `<span>此處膜厚 ≈ <b>${Math.round(d)} nm</b></span><span>${S.mono ? S.mono + ' nm 單色光' : '以 550 nm 為例'}：兩路反射光 <b>${k > 0.7 ? '增強' : k < 0.3 ? '減弱' : '部分增強'}</b></span><span class="muted">干涉結果與膜厚、折射率、觀察角度及光的波長有關</span>`;
    }
    cv.c.addEventListener('click', (e) => { const r = cv.c.getBoundingClientRect(); const x = ((e.clientX - r.left) / r.width * 720 - 40) / 640; S.x = Math.max(0, Math.min(1, x)); px.set(S.x); draw(); });
    const px = slider(ui.ctrl, '觀察位置', 0, 1, 0.01, S.x, (v) => Math.round(dAt(v)) + ' nm', (v) => { S.x = v; draw(); });
    slider(ui.ctrl, '最大膜厚', 300, 1500, 10, S.maxd, (v) => v + ' nm', (v) => { S.maxd = v; px.set(S.x); draw(); });
    const mb = button(ui.ctrl, '改用單色光', () => { S.mono = S.mono ? 0 : 600; mb.textContent = S.mono ? '改用白光' : '改用單色光'; draw(); });
    draw();
    return () => {};
  }

  const REG = { superposition, ripple, doubleslit, singleslit, thinfilm };
  return {
    mount(el, name) { const f = REG[name]; return f ? { destroy: f(el) || (() => {}) } : { destroy() {} }; },
    names: Object.keys(REG),
  };
})();
