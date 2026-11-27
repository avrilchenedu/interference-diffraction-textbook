/* 干涉與繞射 教科書網站 — renders content.json (all teaching text is verbatim from the source documents) */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const txt = (s) => esc(s).replace(/\n/g, '<br>');
  const MODES = { book: '教科書模式', teach: '教師授課模式' };
  let DATA = null;
  let mounted = [];

  const store = {
    get: (k) => { try { return localStorage.getItem('idtb:' + k) || ''; } catch { return ''; } },
    set: (k, v) => { try { localStorage.setItem('idtb:' + k, v); } catch { /* ignore */ } },
  };

  function pageHref(id) {
    const p = DATA.pages.find((x) => x.id === id);
    return p ? `#/${p.mode}/${p.id}` : '#';
  }

  function figImg(im, alt) {
    const credit = im.attrib
      ? `<small class="cred web">網路替代圖｜${esc(im.attrib)}　<a href="${esc(im.link)}" target="_blank" rel="noopener">來源頁 ↗</a></small>`
      : im.link ? `<small class="cred">${im.credit ? txt(im.credit) + '　' : ''}<a href="${esc(im.link)}" target="_blank" rel="noopener">Wikimedia來源頁 ↗</a></small>` : '';
    return `<div class="fig-img"><img src="${esc(im.src)}" alt="${esc(alt)}" loading="lazy" data-zoom>${im.cap ? `<span class="cap">${esc(im.cap)}</span>` : ''}${credit}</div>`;
  }

  const R = {
    h: (b) => `<h2>${esc(b.title)}</h2>`,
    paras: (b) => `<div class="paras">${b.paras.map((p) => `<p>${txt(p)}</p>`).join('')}</div>`,
    note: (b) => `<div class="note">⚠ ${esc(b.note)}</div>`,
    box: (b) => `<section class="box box-${b.style}"><h3>${esc(b.title)}</h3><p>${txt(b.text)}</p></section>`,
    kv: (b) => `<dl class="kv">${b.rows.map((r) => `<dt>${txt(r.label)}</dt><dd>${txt(r.text)}</dd>`).join('')}</dl>`,
    table: (b) => `<div class="tbl"><table><thead><tr>${b.head.map((h) => `<th>${txt(h)}</th>`).join('')}</tr></thead><tbody>${
      b.rows.map((r) => `<tr>${r.map((c) => `<td>${txt(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`,
    linktable: (b) => `<div class="tbl"><table><thead><tr>${b.head.map((h) => `<th>${txt(h)}</th>`).join('')}</tr></thead><tbody>${
      b.rows.map((r) => `<tr>${r.cells.map((c, i) => `<td>${i === 3 && r.link ? `<a href="${esc(r.link)}" target="_blank" rel="noopener">${txt(c)} ↗</a>` : txt(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`,
    media: (b) => {
      const kind = b.kind && !/^0[78]/.test(b.kind) ? `<b>${txt(b.kind)}</b>　` : '';
      if (b.missing) {
        return `<figure class="media missing"><div class="ph"><span>圖檔待補</span><code>${esc(b.file)}</code></div>
          <figcaption>${kind}${txt(b.text)}${b.credit ? `<small>${txt(b.credit)}</small>` : ''}</figcaption></figure>`;
      }
      const imgs = b.imgs || [{ src: b.src, link: b.link }];
      const alt = (b.text || b.file || '').split('\n')[0];
      return `<figure class="media${imgs.length > 1 ? ' multi n' + Math.min(imgs.length, 3) : ''}">
        <div class="imgs">${imgs.map((im) => figImg(im, alt)).join('')}</div>
        <figcaption>${kind}${txt(b.text)}${b.web ? `<small class="orig">原規劃圖檔：${esc(b.file)}</small>` : ''}
        ${!b.web && b.credit && imgs.length === 1 && !imgs[0].credit ? `<small>${txt(b.credit)}</small>` : ''}</figcaption></figure>`;
    },
    sim: (b) => `<figure class="media simfig"><div class="sim-host" data-sim="${esc(b.sim)}"></div>${b.text ? `<figcaption>${b.kind ? `<b>${txt(b.kind)}</b>　` : ''}${txt(b.text)}</figcaption>` : ''}</figure>`,
    link: (b) => `<a class="jump" href="${pageHref(b.target)}">${esc(b.title)} →</a>`,
    exam: (b) => `<div class="exam"><b>${esc(b.title)}</b><span>建置中，將另行提供。</span></div>`,
    ref: (b) => `<div class="ref">${b.paras.map((p) => `<p>${txt(p)}</p>`).join('')}<a href="${esc(b.link)}" target="_blank" rel="noopener">開啟 OpenStax ↗</a></div>`,
    quote: (b) => `<blockquote class="quote"><p>${txt(b.text)}</p><cite>${esc(b.source)}</cite></blockquote>`,
    activity: (b, page) => {
      const key = `${page.id}:${b.title}`;
      return `<section class="activity"><h3>${esc(b.title)}</h3>
        ${b.situation ? `<p class="situ">${txt(b.situation)}</p>` : ''}
        <div class="mat"><b>使用材料與操作</b><p>${txt(b.material)}</p></div>
        <div class="qs">${b.questions.map((q) => `<p>${txt(q)}</p>`).join('')}</div>
        <label class="ans"><span>我的作答（自動儲存在本機瀏覽器）</span><textarea data-key="${esc(key)}" rows="6">${esc(store.get(key))}</textarea></label>
      </section>`;
    },
    tans: (b) => `<section class="tans"><h3>${esc(b.title)}</h3>
      <dl class="kv"><dt>使用材料<br>與操作</dt><dd>${txt(b.material)}</dd><dt>參考答案<br>與判讀</dt><dd>${txt(b.answer)}</dd><dt>常見錯誤<br>與引導</dt><dd>${txt(b.guide)}</dd></dl></section>`,
    card: (b) => `<section class="card"><h3>${esc(b.title)}</h3>
      <div class="meta">${b.meta.map((m) => `<span>${txt(m)}</span>`).join('')}</div>
      <dl class="kv">${b.rows.map((r) => `<dt>${esc(r.label)}</dt><dd>${txt(r.text)}</dd>`).join('')}</dl>
      ${b.foot ? `<p class="foot">${txt(b.foot)}</p>` : ''}</section>`,
    guide: (b) => `<section class="card"><h3>${esc(b.title)}</h3>
      <dl class="kv">${b.kv.map(([l, t]) => `<dt>${txt(l)}</dt><dd>${txt(t)}</dd>`).join('')}</dl>
      ${R.table({ head: b.head, rows: b.rows })}</section>`,
    shot: (b) => `<section class="shot"><img src="${esc(b.src)}" alt="分鏡草圖" loading="lazy" data-zoom>
      <dl class="kv">${b.head.map((h, i) => `<dt>${esc(h)}</dt><dd>${txt(b.cells[i])}</dd>`).join('')}</dl></section>`,
    chapters: (b) => `<div class="chapters">${b.items.map((c) => `<a class="chap" href="${pageHref(c.target)}">
      <span class="chap-n">${esc(c.label)}</span><b>${esc(c.name)}</b><p>${txt(c.text)}</p><span class="chap-go">開始閱讀 →</span></a>`).join('')}</div>
      <div class="quick"><a href="${pageHref('ws2')}">📝 學習單</a><a href="${pageHref('ai')}">🤖 AI 提問守則</a><a href="${pageHref('ext')}">📚 延伸閱讀</a><a href="${pageHref('d1')}">🧑‍🏫 教師上課簡報</a></div>`,
    doclist: (b) => `<div class="doclist">${b.items.map((d) => `<a href="${pageHref(d.target)}"><span class="code">${esc(d.code)}</span><b>${esc(d.name)}</b><small>${esc(d.file)}</small></a>`).join('')}</div>`,
    reflist: (b) => `<dl class="kv reflist">${b.rows.map((r) => `<dt>${esc(r.label)}</dt><dd>${txt(r.text)}${
      (r.links || []).map((u) => `<br><a href="${esc(u)}" target="_blank" rel="noopener">${esc(u.replace(/^https?:\/\//, '').slice(0, 70))} ↗</a>`).join('')}</dd>`).join('')}</dl>`,
    docraw: (b) => `<div class="docraw">${b.items.map(rawItem).join('')}</div>`,
    credits: (b) => `<div class="tbl"><table><thead><tr><th>圖片</th><th>用途（依 07A）</th><th>作者／授權與來源</th></tr></thead><tbody>${
      b.items.map((m) => `<tr><td><img class="thumb" src="${esc(m.src)}" alt="" loading="lazy" data-zoom><br><small>${esc(m.file.split('/').pop())}</small></td><td>${txt(m.text)}</td><td>${
        m.attrib ? `<span class="tag">網路替代圖</span><br>${esc(m.attrib)}` : txt(m.credit)}<br><a href="${esc(m.link)}" target="_blank" rel="noopener">來源頁 ↗</a></td></tr>`).join('')}</tbody></table></div>`,
  };

  /* 原始文件全文：段落、表格、附圖、超連結 */
  function rawPara(it) {
    if (it.table) return rawTable(it.table);
    const hint = /^提示：/.test(it.text);
    return `${it.text ? `<p class="${hint ? 'hint' : ''}">${txt(it.text)}</p>` : ''}${
      (it.imgs || []).map((s) => `<img class="raw-img" src="${esc(s)}" alt="原文件附圖" loading="lazy" data-zoom>`).join('')}${
      (it.links || []).length ? `<p class="raw-links">${it.links.map((u) => `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(u.replace(/^https?:\/\//, '').slice(0, 60))} ↗</a>`).join('<br>')}</p>` : ''}`;
  }
  function rawTable(rows) {
    const max = Math.max(...rows.map((r) => r.length));
    return `<div class="tbl"><table class="raw">${rows.map((r) => `<tr>${r.map((c, i) => {
      const span = i === r.length - 1 && r.length < max ? ` colspan="${max - r.length + 1}"` : '';
      return `<td${span}>${c.map(rawPara).join('')}</td>`;
    }).join('')}</tr>`).join('')}</table></div>`;
  }
  function rawItem(it) { return it.table ? rawTable(it.table) : rawPara(it); }

  /* ---------------------------------------------------------------- slide deck (教師授課模式) */
  const SRCNAME = (c) => (DATA.sources[c] ? `${c} ${DATA.sources[c]}` : c);
  const deckState = { notes: false };

  function slideHTML(s, page, i, n) {
    if (s.kind === 'title') {
      return `<div class="slide slide-title">
        <div class="s-kicker">第 ${page.id.slice(1)} 節上課簡報　·　${esc(s.time)}</div>
        <h2 class="s-big">${esc(s.title)}</h2>
        <div class="s-kv">${s.kv.map((c) => `<div><b>${esc(c.label)}</b><p>${txt(c.text)}</p></div>`).join('')}</div>
        <p class="s-hint">按 → 或點「下一張」開始上課；按 N 開啟教師備註。</p></div>`;
    }
    const tabs = [];
    if (s.sim) tabs.push(['sim', '🔬 互動模擬']);
    if (s.reveal) tabs.push(['reveal', '📷 揭曉實拍']);
    if (s.images?.length) tabs.push(['img', '🖼 圖片']);
    if (s.worksheet) tabs.push(['ws', '📝 學習單題目']);
    const panes = {
      sim: () => `<div class="sim-host" data-sim="${esc(s.sim)}"></div>`,
      reveal: () => `<div class="reveal"><div class="reveal-cover"><p>學生完成預測後再揭曉</p><button type="button" class="s-btn primary" data-reveal>揭曉實拍</button></div>${figImg(s.reveal, s.reveal.cap)}</div>`,
      img: () => `<div class="s-imgs n${Math.min(s.images.length, 3)}">${s.images.map((im) => figImg(im, im.cap)).join('')}</div>`,
      ws: () => `<div class="s-ws">${s.worksheet.map((q) => `<p>${txt(q)}</p>`).join('')}</div>`,
    };
    return `<div class="slide">
      <div class="s-head"><span class="s-time">⏱ ${esc(s.time)}</span><h2>${esc(s.heading)}</h2><span class="s-count">${i + 1} / ${n}</span></div>
      <div class="s-grid">
        <div class="s-main">
          ${s.ask ? `<div class="s-ask"><span>教師提問</span><p>${txt(s.ask.replace(/^問：/, ''))}</p></div>` : ''}
          ${s.do ? `<div class="s-do"><b>教師活動</b>　${txt(s.do)}</div>` : ''}
          ${tabs.length ? `<div class="s-tabs">${tabs.map(([k, l], j) => `<button type="button" class="${j ? '' : 'on'}" data-tab="${k}">${l}</button>`).join('')}</div>
            <div class="s-pane">${tabs.map(([k], j) => `<div class="pane" data-pane="${k}" ${j ? 'hidden' : ''}>${panes[k]()}</div>`).join('')}</div>` : ''}
        </div>
        <aside class="s-side">
          ${s.text ? `<section class="s-text"><div class="s-label">📖 ${esc(s.text.ref)} <a href="${pageHref(s.text.target)}" target="_blank">開啟課本 ↗</a></div>
            ${s.text.paras.map((p) => `<p>${txt(p)}</p>`).join('')}</section>` : ''}
          ${s.concept?.length ? `<section class="s-concept"><div class="s-label">💡 用什麼概念解釋
            <button type="button" class="s-btn" data-showall>全部顯示</button></div>
            ${s.concept.map((c) => `<details><summary>${esc(c.label)}<small>${esc(SRCNAME(c.source))}</small></summary><p>${txt(c.text)}</p></details>`).join('')}</section>` : ''}
        </aside>
      </div></div>`;
  }

  function notesHTML(s) {
    if (s.kind === 'title') return '<p class="muted">本張為節次說明。</p>';
    const base = [['學生活動與預期表現', s.student], ['評量／證據', s.evidence], ['教材／備註', s.material]].filter(([, v]) => v);
    return `<dl class="kv">${base.map(([l, v]) => `<dt>${l}</dt><dd>${txt(v)}</dd>`).join('')}</dl>
      ${(s.notes || []).map((g) => `<section class="n-grp"><h4>${esc(g.label)}<small>${esc(SRCNAME(g.source))}</small></h4>
        <dl class="kv">${g.rows.map(([l, v]) => `${l ? `<dt>${esc(l)}</dt><dd>` : '<dd class="full">'}${txt(v)}</dd>`).join('')}</dl></section>`).join('')}`;
  }

  function renderDeck(page, idx) {
    const deck = page.deck;
    const i = Math.max(0, Math.min(deck.length - 1, idx || 0));
    const s = deck[i];
    $('#main').innerHTML = `<div class="deck ${deckState.notes ? 'with-notes' : ''}" id="deck">
      <div class="d-bar">
        <a class="d-back" href="#/teach/t_unit">☰ 教案與資料</a>
        <b>${esc(page.title)}</b>
        <span class="d-sp"></span>
        <a class="d-btn" href="${pageHref(page.lesson)}">教案全文</a>
        <button type="button" class="d-btn" data-notes>${deckState.notes ? '隱藏' : '顯示'}教師備註 (N)</button>
        <button type="button" class="d-btn" data-fs>全螢幕 (F)</button>
      </div>
      <div class="d-body">
        <div class="d-stage">${slideHTML(s, page, i, deck.length)}</div>
        <aside class="d-notes"><h3>🗒 教師備註</h3>${notesHTML(s)}</aside>
      </div>
      <div class="d-nav">
        <button type="button" class="s-btn" data-go="${i - 1}" ${i === 0 ? 'disabled' : ''}>← 上一張</button>
        <div class="d-thumbs">${deck.map((d, j) => `<button type="button" class="${j === i ? 'on' : ''}" data-go="${j}" title="${esc(d.heading || d.title)}"><span>${j + 1}</span>${esc(d.kind === 'title' ? '節次說明' : d.heading)}<small>${esc(d.time || '')}</small></button>`).join('')}</div>
        <button type="button" class="s-btn primary" data-go="${i + 1}" ${i === deck.length - 1 ? 'disabled' : ''}>下一張 →</button>
      </div></div>`;
    mountSims($('#deck'));
  }

  function mountSims(root) {
    root.querySelectorAll('.sim-host:not([data-on])').forEach((el) => {
      if (el.closest('[hidden]')) return;
      el.dataset.on = '1';
      mounted.push(window.SIMS.mount(el, el.dataset.sim));
    });
  }
  function unmountSims() { mounted.forEach((m) => m.destroy()); mounted = []; }

  /* ---------------------------------------------------------------- pages */
  function renderSidebar(mode, current) {
    const items = DATA.pages.filter((p) => p.mode === mode);
    const groups = mode === 'book'
      ? [['單元', ['intro']], ['課文', ['sec1', 'sec2', 'sec3', 'sec4']], ['學習單', ['ws1', 'ws2', 'ws3']], ['AI 指引', ['ai']], ['資源', ['ext', 'credits']]]
      : [['上課簡報', ['d1', 'd2', 'd3']], ['教案', ['t_unit', 't1', 't2', 't3']], ['評量', ['t_assess', 't_exam']], ['教師資源', ['t_diff', 't_media', 't_07b', 't_08']],
        ['原始文件全文', ['doc_01', 'doc_02', 'doc_03', 'doc_04', 'doc_05', 'doc_06', 'doc_07A', 'doc_07B', 'doc_08', 'doc_10']]];
    $('#sidebar').innerHTML = `<div class="side-mode">${MODES[mode]}</div>` + groups.map(([g, ids]) =>
      `<div class="grp"><div class="grp-t">${g}</div>${ids.map((id) => {
        const p = items.find((x) => x.id === id);
        return p ? `<a href="#/${mode}/${id}" class="${id === current ? 'on' : ''}">${esc(p.nav)}</a>` : '';
      }).join('')}</div>`).join('');
  }

  function render() {
    const [, mode = 'book', id, sub] = (location.hash || '#/book/intro').split('/');
    const page = DATA.pages.find((p) => p.id === id && p.mode === mode) || DATA.pages.find((p) => p.mode === mode);
    unmountSims();
    document.body.dataset.mode = page.mode;
    document.body.classList.toggle('deck-mode', !!page.deck);
    document.querySelectorAll('.mode-switch a').forEach((a) => a.classList.toggle('on', a.dataset.mode === page.mode));
    renderSidebar(page.mode, page.id);
    document.body.classList.remove('side-open');
    document.title = `${page.title}｜干涉與繞射`;
    if (page.deck) { renderDeck(page, +sub || 0); return; }
    const srcs = [...new Set(page.blocks.map((b) => b.source).filter(Boolean).map((s) => s.split('　')[0]))];
    const list = DATA.pages.filter((p) => p.mode === page.mode && !p.deck);
    const i = list.indexOf(page);
    $('#main').innerHTML = `<article class="page">
      <div class="crumb">${MODES[page.mode]}</div>
      <h1>${esc(page.title)}</h1>
      ${page.worksheet ? '<button class="print" onclick="window.print()">列印學習單</button>' : ''}
      ${page.blocks.map((b) => (R[b.t] ? R[b.t](b, page) : '')).join('\n')}
      <footer class="sources">${srcs.length ? `本頁內容出處：${srcs.filter((s) => DATA.sources[s]).map((s) => `<a href="${pageHref('doc_' + s)}">${esc(s)} ${esc(DATA.sources[s])}</a>`).join('、')}　·　` : ''}<a href="${pageHref('credits')}">資料來源與授權</a></footer>
      <nav class="pager">${i > 0 ? `<a href="#/${page.mode}/${list[i - 1].id}">← ${esc(list[i - 1].nav)}</a>` : '<span></span>'}${
        i >= 0 && i < list.length - 1 ? `<a href="#/${page.mode}/${list[i + 1].id}">${esc(list[i + 1].nav)} →</a>` : '<span></span>'}</nav>
    </article>`;
    mountSims($('#main'));
    window.scrollTo(0, 0);
  }

  function deckGo(j) {
    const [, mode, id] = location.hash.split('/');
    location.hash = `#/${mode}/${id}/${j}`;
  }

  document.addEventListener('input', (e) => {
    if (e.target.matches('textarea[data-key]')) store.set(e.target.dataset.key, e.target.value);
  });
  document.addEventListener('click', (e) => {
    const t = e.target;
    const img = t.closest('img[data-zoom]');
    const lb = $('#lightbox');
    if (t.closest('[data-go]') && !t.closest('[data-go]').disabled) { deckGo(+t.closest('[data-go]').dataset.go); return; }
    if (t.closest('[data-tab]')) {
      const btn = t.closest('[data-tab]'); const slide = btn.closest('.slide');
      slide.querySelectorAll('[data-tab]').forEach((b) => b.classList.toggle('on', b === btn));
      slide.querySelectorAll('[data-pane]').forEach((p) => { p.hidden = p.dataset.pane !== btn.dataset.tab; });
      mountSims(slide); return;
    }
    if (t.closest('[data-reveal]')) { t.closest('.reveal').classList.add('shown'); return; }
    if (t.closest('[data-showall]')) { t.closest('.s-concept').querySelectorAll('details').forEach((d) => { d.open = true; }); return; }
    if (t.closest('[data-notes]')) { deckState.notes = !deckState.notes; render(); return; }
    if (t.closest('[data-fs]')) { toggleFs(); return; }
    if (img) {
      lb.querySelector('img').src = img.src;
      lb.querySelector('p').textContent = img.alt;
      lb.hidden = false;
    } else if (t.closest('#lightbox')) {
      lb.hidden = true;
    }
  });
  function toggleFs() {
    const el = document.documentElement;
    if (document.fullscreenElement) document.exitFullscreen(); else el.requestFullscreen?.();
  }
  document.addEventListener('keydown', (e) => {
    if (!document.body.classList.contains('deck-mode') || e.target.matches('input, textarea')) return;
    const cur = +(location.hash.split('/')[3] || 0);
    const page = DATA.pages.find((p) => p.id === location.hash.split('/')[2]);
    if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); if (cur < page.deck.length - 1) deckGo(cur + 1); }
    else if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); if (cur > 0) deckGo(cur - 1); }
    else if (e.key === 'n' || e.key === 'N') { deckState.notes = !deckState.notes; render(); }
    else if (e.key === 'f' || e.key === 'F') toggleFs();
  });
  $('#menuBtn').addEventListener('click', () => document.body.classList.toggle('side-open'));
  window.addEventListener('hashchange', render);

  fetch('content.json?v=3').then((r) => r.json()).then((d) => {
    DATA = d;
    $('#subtitle').textContent = d.subtitle;
    render();
  }).catch(() => {
    $('#main').innerHTML = '<p class="note">無法載入教材內容，請以網頁伺服器開啟本網站。</p>';
  });
})();
