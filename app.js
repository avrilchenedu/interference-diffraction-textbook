/* 干涉與繞射 教科書網站 — renders content.json (all teaching text is verbatim from the source documents) */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const txt = (s) => esc(s).replace(/\n/g, '<br>');
  const MODES = { book: '教科書模式', teach: '教師授課模式' };
  let DATA = null;

  const store = {
    get: (k) => { try { return localStorage.getItem('idtb:' + k) || ''; } catch { return ''; } },
    set: (k, v) => { try { localStorage.setItem('idtb:' + k, v); } catch { /* ignore */ } },
  };

  function srcTag(code) {
    if (!code) return '';
    const name = DATA.sources[code.split('　')[0]];
    return `<span class="src">出處：${esc(code)}${name && !code.includes('　') ? ' ' + esc(name) : ''}</span>`;
  }

  function pageHref(id) {
    const p = DATA.pages.find((x) => x.id === id);
    return p ? `#/${p.mode}/${p.id}` : '#';
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
      if (b.missing) {
        return `<figure class="media missing"><div class="ph"><span>圖檔待補</span><code>${esc(b.file)}</code></div>
          <figcaption>${b.kind ? `<b>${txt(b.kind)}</b>　` : ''}${txt(b.text)}${b.credit ? `<small>${txt(b.credit)}</small>` : ''}</figcaption></figure>`;
      }
      return `<figure class="media"><img src="${esc(b.src)}" alt="${esc((b.text || b.file || '').split('\n')[0])}" loading="lazy" data-zoom>
        <figcaption>${b.kind && !/^0[78]/.test(b.kind) ? `<b>${txt(b.kind)}</b>　` : ''}${txt(b.text)}
        ${b.credit ? `<small>${txt(b.credit)}${b.link ? `　<a href="${esc(b.link)}" target="_blank" rel="noopener">Wikimedia來源頁 ↗</a>` : ''}</small>` : ''}</figcaption></figure>`;
    },
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
    credits: (b) => `<div class="tbl"><table><thead><tr><th>照片</th><th>用途</th><th>作者／授權</th></tr></thead><tbody>${
      b.items.map((m) => `<tr><td><img class="thumb" src="${esc(m.src)}" alt="" loading="lazy"><br><small>${esc(m.file.split('/').pop())}</small></td><td>${txt(m.text)}</td><td>${txt(m.credit)}<br><a href="${esc(m.link)}" target="_blank" rel="noopener">Wikimedia來源頁 ↗</a></td></tr>`).join('')}</tbody></table></div>`,
  };

  function renderSidebar(mode, current) {
    const items = DATA.pages.filter((p) => p.mode === mode);
    const groups = mode === 'book'
      ? [['單元', ['intro']], ['課文', ['sec1', 'sec2', 'sec3', 'sec4']], ['學習單', ['ws1', 'ws2', 'ws3']], ['AI 指引', ['ai']], ['資源', ['ext', 'credits']]]
      : [['教學設計', ['t_unit']], ['分節授課', ['t1', 't2', 't3']], ['評量', ['t_assess', 't_exam']], ['教師資源', ['t_diff', 't_media', 't_07b', 't_08']]];
    $('#sidebar').innerHTML = `<div class="side-mode">${MODES[mode]}</div>` + groups.map(([g, ids]) =>
      `<div class="grp"><div class="grp-t">${g}</div>${ids.map((id) => {
        const p = items.find((x) => x.id === id);
        return p ? `<a href="#/${mode}/${id}" class="${id === current ? 'on' : ''}">${esc(p.nav)}</a>` : '';
      }).join('')}</div>`).join('');
  }

  function render() {
    const [, mode = 'book', id] = (location.hash || '#/book/intro').split('/');
    const page = DATA.pages.find((p) => p.id === id && p.mode === mode) || DATA.pages.find((p) => p.mode === mode);
    document.body.dataset.mode = page.mode;
    document.querySelectorAll('.mode-switch a').forEach((a) => a.classList.toggle('on', a.dataset.mode === page.mode));
    renderSidebar(page.mode, page.id);
    const srcs = [...new Set(page.blocks.map((b) => b.source).filter(Boolean).map((s) => s.split('　')[0]))];
    const list = DATA.pages.filter((p) => p.mode === page.mode);
    const i = list.indexOf(page);
    $('#main').innerHTML = `<article class="page">
      <div class="crumb">${MODES[page.mode]}</div>
      <h1>${esc(page.title)}</h1>
      ${page.worksheet ? '<button class="print" onclick="window.print()">列印學習單</button>' : ''}
      ${page.blocks.map((b) => (R[b.t] ? R[b.t](b, page) : '')).join('\n')}
      ${srcs.length ? `<footer class="sources">本頁內容出處：${srcs.map((s) => `${esc(s)} ${esc(DATA.sources[s] || '')}`).join('、')}</footer>` : ''}
      <nav class="pager">${i > 0 ? `<a href="#/${page.mode}/${list[i - 1].id}">← ${esc(list[i - 1].nav)}</a>` : '<span></span>'}${
        i < list.length - 1 ? `<a href="#/${page.mode}/${list[i + 1].id}">${esc(list[i + 1].nav)} →</a>` : '<span></span>'}</nav>
    </article>`;
    document.title = `${page.title}｜干涉與繞射`;
    document.body.classList.remove('side-open');
    window.scrollTo(0, 0);
  }

  document.addEventListener('input', (e) => {
    if (e.target.matches('textarea[data-key]')) store.set(e.target.dataset.key, e.target.value);
  });
  document.addEventListener('click', (e) => {
    const img = e.target.closest('img[data-zoom]');
    const lb = $('#lightbox');
    if (img) {
      lb.querySelector('img').src = img.src;
      lb.querySelector('p').textContent = img.alt;
      lb.hidden = false;
    } else if (e.target.closest('#lightbox')) {
      lb.hidden = true;
    }
  });
  $('#menuBtn').addEventListener('click', () => document.body.classList.toggle('side-open'));
  window.addEventListener('hashchange', render);

  fetch('content.json?v=1').then((r) => r.json()).then((d) => {
    DATA = d;
    $('#subtitle').textContent = d.subtitle;
    render();
  }).catch(() => {
    $('#main').innerHTML = '<p class="note">無法載入教材內容，請以網頁伺服器開啟本網站。</p>';
  });
})();
