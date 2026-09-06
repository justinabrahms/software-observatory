// Software Observatory — minimal interactivity

document.addEventListener('DOMContentLoaded', () => {
  // Filter list active toggle (general)
  document.querySelectorAll('.filter-list button').forEach(btn => {
    btn.addEventListener('click', () => {
      const siblings = btn.closest('.filter-list').querySelectorAll('button');
      siblings.forEach(s => {
        s.classList.remove('active');
        s.setAttribute('aria-pressed', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-pressed', 'true');
    });
  });

  // Catalog family filter
  const familyFilter = document.getElementById('family-filter');
  if (familyFilter) {
    familyFilter.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        const family = btn.dataset.family;
        const sections = document.querySelectorAll('.family-section');
        sections.forEach(section => {
          if (family === 'all' || section.dataset.family === family) {
            section.classList.remove('hidden');
          } else {
            section.classList.add('hidden');
          }
        });
      });
    });
  }

  // Deep-linkable headings: hovering a heading with an id shows a link icon;
  // clicking it copies the jumplink (page URL + #anchor) to the clipboard.
  const HEADING_LINK_SELECTOR = [
    '.section-heading',
    '.property-detail-title',
    '.family-title',
    '.featured-title',
    '.about-content h2',
    '.signal-detail-body h2',
    '.glossary-term',
  ].map(s => s + '[id]').join(', ');

  document.querySelectorAll(HEADING_LINK_SELECTOR).forEach(h => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'heading-anchor';
    btn.title = 'Copy link to this section';
    btn.setAttribute('aria-label', 'Copy link to this section');
    btn.innerHTML = '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
      + '<path d="M6.5 9.5a3 3 0 0 0 4.2.2l2-2a3 3 0 0 0-4.2-4.2l-1.1 1.1"/>'
      + '<path d="M9.5 6.5a3 3 0 0 0-4.2-.2l-2 2a3 3 0 0 0 4.2 4.2l1.1-1.1"/>'
      + '</svg>';
    btn.addEventListener('click', async e => {
      e.preventDefault();
      const url = location.origin === 'null' || location.protocol === 'file:'
        ? location.href.split('#')[0] + '#' + h.id
        : location.origin + location.pathname + '#' + h.id;
      try {
        await navigator.clipboard.writeText(url);
      } catch {
        // clipboard API unavailable (insecure context, denied) — fall back
        const ta = document.createElement('textarea');
        ta.value = url;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
      }
      history.replaceState(null, '', '#' + h.id);
      btn.classList.add('copied');
      btn.title = 'Copied!';
      setTimeout(() => {
        btn.classList.remove('copied');
        btn.title = 'Copy link to this section';
      }, 1200);
    });
    h.appendChild(btn);
  });

  // Confidence scatter: toggle between stack layers and individual sensors
  const scatterFrame = document.querySelector('.scatter-frame');
  if (scatterFrame) {
    document.querySelectorAll('.scatter-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.scatter-toggle-btn')
          .forEach(b => b.classList.toggle('active', b === btn));
        scatterFrame.dataset.scatterMode = btn.dataset.scatter;
      });
    });

    // Legend hover/focus isolates one family's dots
    const sensorPoints = Array.from(scatterFrame.querySelectorAll('.sensor-point'));
    document.querySelectorAll('.scatter-legend .legend-key').forEach((key, i) => {
      const slug = key.querySelector('.legend-dot').className.match(/fam-[\w-]+/)[0].slice(4);
      key.setAttribute('tabindex', '0');
      key.setAttribute('role', 'button');
      key.setAttribute('aria-label', key.textContent.trim());
      const isolate = () => {
        sensorPoints.forEach(p => {
          const match = p.classList.contains('fam-' + slug);
          p.classList.toggle('fam-dim', !match);
          p.classList.toggle('fam-spotlit', match);
        });
      };
      const reset = () => {
        sensorPoints.forEach(p => p.classList.remove('fam-dim', 'fam-spotlit'));
      };
      key.addEventListener('mouseenter', isolate);
      key.addEventListener('mouseleave', reset);
      key.addEventListener('focus', isolate);
      key.addEventListener('blur', reset);
    });
  }

  // Search: fetch the build-time index, filter on input, render a dropdown
  const searchBox = document.querySelector('.search-box');
  if (searchBox) {
    const input = searchBox.querySelector('.search-input');
    const results = searchBox.querySelector('.search-results');
    let index = null;
    let activeIdx = -1;

    if (!results.id) results.id = 'search-results';
    results.setAttribute('role', 'listbox');
    results.setAttribute('aria-label', 'Search results');
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-controls', results.id);
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');

    fetch('/search-index.json')
      .then(r => r.json())
      .then(data => { index = Array.isArray(data) ? data : []; })
      .catch(() => {});

    // search-index.json is generated from content/sensors/*.md, which the
    // README invites outside contributors to add to. Treat every field in it
    // as untrusted: text goes through textContent, and href only ever gets a
    // root-relative same-origin path (no javascript:, data:, or //host).
    const SAFE_PATH = /^\/(?!\/)[A-Za-z0-9\-._~/%#?&=+,:@!$'()*;]*$/;
    function safeHref(url) {
      return typeof url === 'string' && SAFE_PATH.test(url) ? url : null;
    }
    function str(v) { return v == null ? '' : String(v); }

    function escapeRe(t) { return t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

    // Match only at word starts. Substring matching made "AI" hit the "ai"
    // inside "Time-to-Repair"; a word-start match still lets "test" find
    // "testing" and "mutation" find "Mutation Testing".
    const reCache = new Map();
    function termRe(t) {
      let re = reCache.get(t);
      if (!re) {
        re = new RegExp('(?:^|[^a-z0-9])' + escapeRe(t), 'i');
        reCache.set(t, re);
      }
      return re;
    }

    function tokenize(q) {
      return q.toLowerCase().split(/[^a-z0-9+#]+/).filter(Boolean);
    }

    // Per-term field weights: a title hit always outranks a blurb hit.
    function scoreItem(item, terms) {
      const title = str(item.title);
      const lt = title.toLowerCase();
      const fam = str(item.family);
      const blurb = str(item.blurb);
      const keywords = str(item.keywords);
      const text = str(item.text);
      const slug = str(item.url).replace(/[^A-Za-z0-9]+/g, ' ');
      let score = 0;
      let matched = 0;
      for (const t of terms) {
        const re = termRe(t);
        let best = 0;
        if (lt === t) best = 120;
        else if (lt.startsWith(t)) best = 80;
        else if (re.test(title)) best = 60;
        else if (re.test(slug)) best = 45;
        else if (re.test(fam)) best = 25;
        else if (re.test(blurb)) best = 12;
        else if (re.test(keywords)) best = 30;
        else if (re.test(text)) best = 8;
        if (best) { matched++; score += best; }
      }
      return { score: score, matched: matched };
    }

    function search(q) {
      if (!index) return [];
      const terms = tokenize(q);
      if (!terms.length) return [];
      const all = [];
      for (const item of index) {
        if (!safeHref(item.url)) continue;
        const s = scoreItem(item, terms);
        if (!s.matched) continue;
        // whole query as a phrase in the title is the strongest signal
        if (terms.length > 1 && termRe(q.trim()).test(str(item.title))) s.score += 40;
        if (item.kind === 'family') s.score += 5;
        all.push([s.matched, s.score, item]);
      }
      // Prefer rows matching every term; fall back to partial matches so a
      // multi-word query degrades to something useful instead of nothing.
      const strict = all.filter(r => r[0] === terms.length);
      const pool = strict.length ? strict : all;
      pool.sort((a, b) => b[1] - a[1] || str(a[2].title).localeCompare(str(b[2].title)));
      return pool.slice(0, 8).map(r => r[2]);
    }

    function setExpanded(open) {
      input.setAttribute('aria-expanded', open ? 'true' : 'false');
      results.hidden = !open;
    }

    function emptyState(query) {
      const wrap = document.createElement('div');
      wrap.className = 'search-empty';
      const line = document.createElement('p');
      line.textContent = 'No sensors match “' + query + '”.';
      const actions = document.createElement('p');
      actions.className = 'search-empty-actions';
      const a1 = document.createElement('a');
      a1.href = '/catalog/';
      a1.textContent = 'Browse all sensors';
      const a2 = document.createElement('a');
      a2.href = '/categories/';
      a2.textContent = 'Browse by category';
      actions.append(a1, document.createTextNode(' · '), a2);
      wrap.append(line, actions);
      return wrap;
    }

    function render(items, query) {
      results.textContent = '';
      if (!query) { setExpanded(false); return; }
      if (!items.length) {
        results.append(emptyState(query));
        setExpanded(true);
        return;
      }
      items.forEach((item, i) => {
        const a = document.createElement('a');
        a.className = 'search-result' + (i === activeIdx ? ' active' : '');
        a.setAttribute('role', 'option');
        a.setAttribute('aria-selected', i === activeIdx ? 'true' : 'false');
        a.href = safeHref(item.url);

        const title = document.createElement('div');
        title.className = 'search-result-title';
        title.textContent = str(item.title);

        const meta = document.createElement('div');
        meta.className = 'search-result-meta';
        meta.textContent = item.kind === 'family' ? 'Family' : str(item.family);

        a.append(title, meta);

        if (item.blurb) {
          const blurb = document.createElement('div');
          blurb.className = 'search-result-blurb';
          blurb.textContent = str(item.blurb);
          a.append(blurb);
        }
        results.append(a);
      });
      setExpanded(true);
    }

    function run() {
      const q = input.value.trim();
      activeIdx = -1;
      if (!q || !index) { render([], q); return; }
      render(search(q), q);
    }

    input.addEventListener('input', run);
    input.addEventListener('focus', run);

    input.addEventListener('keydown', e => {
      const links = results.querySelectorAll('.search-result');
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!links.length) return;
        activeIdx = e.key === 'ArrowDown'
          ? (activeIdx + 1) % links.length
          : (activeIdx - 1 + links.length) % links.length;
        links.forEach((l, i) => {
          l.classList.toggle('active', i === activeIdx);
          l.setAttribute('aria-selected', i === activeIdx ? 'true' : 'false');
        });
        links[activeIdx].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter' && activeIdx >= 0 && links[activeIdx]) {
        e.preventDefault();
        window.location.href = links[activeIdx].href;
      } else if (e.key === 'Escape') {
        setExpanded(false);
        input.blur();
      }
    });

    document.addEventListener('click', e => {
      if (!searchBox.contains(e.target)) setExpanded(false);
    });
  }

  // Code blocks and ASCII diagrams scroll horizontally rather than wrapping
  // (wrapping destroys the column alignment the author drew). A scrollable
  // region has to be keyboard-reachable — WCAG 2.1.1 — and the generated
  // markup carries no tabindex, so add it here when it is actually needed.
  const scrollables = document.querySelectorAll(
    '.signal-detail-body pre, .signal-detail-body .code-block, .signal-detail-body table');
  if (scrollables.length) {
    const markScrollable = () => {
      scrollables.forEach(el => {
        if (el.scrollWidth > el.clientWidth + 1) {
          el.setAttribute('tabindex', '0');
          el.setAttribute('role', 'region');
          if (!el.hasAttribute('aria-label')) {
            el.setAttribute('aria-label', el.tagName === 'TABLE'
              ? 'Table, scroll horizontally to read'
              : 'Code block, scroll horizontally to read');
          }
        } else {
          el.removeAttribute('tabindex');
          el.removeAttribute('role');
          el.removeAttribute('aria-label');
        }
      });
    };
    markScrollable();
    let t;
    window.addEventListener('resize', () => {
      clearTimeout(t);
      t = setTimeout(markScrollable, 150);
    });
  }

  // Atlas dependency graph: hovering a node dims everything not 1 hop away
  const depGraph = document.querySelector('.dep-graph');
  if (depGraph) {
    const nodes = Array.from(depGraph.querySelectorAll('.dep-node'));
    const edges = Array.from(depGraph.querySelectorAll('[data-src]'));

    nodes.forEach(node => {
      node.setAttribute('tabindex', '0');
      const isolate = () => {
        const fam = node.dataset.family;
        const neighbors = new Set([fam]);
        edges.forEach(e => {
          if (e.dataset.src === fam) neighbors.add(e.dataset.tgt);
          if (e.dataset.tgt === fam) neighbors.add(e.dataset.src);
        });
        nodes.forEach(n => n.classList.toggle('dim', !neighbors.has(n.dataset.family)));
        edges.forEach(e => {
          const connected = e.dataset.src === fam || e.dataset.tgt === fam;
          e.classList.toggle('dim', !connected);
        });
        depGraph.classList.add('focus-active');
      };
      const reset = () => {
        nodes.forEach(n => n.classList.remove('dim'));
        edges.forEach(e => e.classList.remove('dim'));
        depGraph.classList.remove('focus-active');
      };
      node.addEventListener('mouseenter', isolate);
      node.addEventListener('mouseleave', reset);
      node.addEventListener('focus', isolate);
      node.addEventListener('blur', reset);
    });
  }

  // Playbook index: the "what do you already run?" checklist. The graph is
  // in the markup (each checkbox carries the doubts its sensor closes and
  // reveals; the hidden list carries the doubt names), so this only counts.
  // Two closers of one doubt count once, which is the composition rule.
  const stackForm = document.querySelector('.stack-form');
  if (stackForm) {
    const result = document.querySelector('.stack-result');
    const tally = stackForm.querySelector('.stack-tally');
    const doubts = Array.from(document.querySelectorAll('.stack-doubts li')).map(li => ({
      id: li.dataset.d, name: li.textContent, closable: li.dataset.closable === '1',
    }));
    const boxes = Array.from(stackForm.querySelectorAll('input[type="checkbox"]'));
    const split = v => (v || '').split(' ').filter(Boolean);
    const meta = {};
    boxes.forEach(b => {
      meta[b.value] = {
        title: b.parentNode.textContent.trim(),
        closes: split(b.dataset.closes),
        reveals: split(b.dataset.reveals),
      };
    });
    const STORE = 'so-stack';
    const load = () => { try { return JSON.parse(localStorage.getItem(STORE) || '[]'); } catch (e) { return []; } };
    const save = v => { try { localStorage.setItem(STORE, JSON.stringify(v)); } catch (e) { /* private mode */ } };
    const esc = t => t.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const doubtLink = d => `<a href="/what-each-sensor-proves/#${d.id}" class="wikilink">${esc(d.name.toLowerCase())}</a>`;
    const sensorLink = slug => `<a href="/sensors/${slug}/" class="wikilink">${esc(meta[slug].title)}</a>`;
    const list = items => items.length ? items.join(', ') : 'none';

    const render = () => {
      const ticked = boxes.filter(b => b.checked).map(b => b.value);
      save(ticked);
      if (!ticked.length) { result.hidden = true; result.innerHTML = ''; tally.textContent = ''; return; }
      const closed = new Set(), revealed = new Set();
      ticked.forEach(s => { meta[s].closes.forEach(d => closed.add(d)); meta[s].reveals.forEach(d => revealed.add(d)); });
      const closedD = doubts.filter(d => closed.has(d.id));
      const revealedD = doubts.filter(d => !closed.has(d.id) && revealed.has(d.id));
      const openD = doubts.filter(d => !closed.has(d.id) && !revealed.has(d.id));
      const open = new Set(openD.map(d => d.id));
      const silent = ticked.filter(s => !meta[s].closes.length && !meta[s].reveals.length);

      // The addition that closes the most of what is left. Ties keep page
      // order, which is family order, so nothing here ranks one closer of
      // a doubt above another on a scale the catalog does not have.
      // Sensors that would close exactly the same set share a line: the
      // catalog has no scale on which to prefer one closer to another.
      const gainBy = {};
      boxes.filter(b => !b.checked).forEach(b => {
        const newly = meta[b.value].closes.filter(d => open.has(d));
        if (!newly.length) return;
        const key = newly.join(' ');
        (gainBy[key] = gainBy[key] || { slugs: [], newly }).slugs.push(b.value);
      });
      const gains = Object.values(gainBy).sort((a, b) => b.newly.length - a.newly.length).slice(0, 3);
      const byId = {}; doubts.forEach(d => { byId[d.id] = d; });
      const unclosable = openD.filter(d => !d.closable);

      let h = `<p class="stack-count"><b>${closedD.length} of ${doubts.length}</b> doubts closed by what you run` +
        (revealedD.length ? `, <b>${revealedD.length}</b> more revealed after the fact` : '') + '.</p>';
      h += `<p><span class="k">Closed</span> ${list(closedD.map(doubtLink))}.</p>`;
      if (revealedD.length) h += `<p><span class="k">Revealed after the fact</span> ${list(revealedD.map(doubtLink))}.</p>`;
      h += `<p><span class="k">Still open</span> ${list(openD.map(d => doubtLink(d) + (d.closable ? '' : ' <small>(no closer before shipping)</small>')))}.</p>`;
      if (gains.length) {
        h += '<p class="k">Add next</p><ol class="stack-next">' + gains.map(g =>
          `<li>${g.slugs.map(sensorLink).join(' or ')} <span class="stack-gain">closes ${g.newly.map(d => doubtLink(byId[d])).join(', ')}</span></li>`).join('') + '</ol>';
      } else if (openD.length) {
        h += `<p>Nothing in the catalog closes what is left before shipping. ` +
          `${unclosable.length ? 'Only retrospective sensors touch ' + list(unclosable.map(doubtLink)) + '. ' : ''}` +
          `The plays under <a href="#where-you-are" class="wikilink">where you are</a> cover that case.</p>`;
      }
      if (silent.length) {
        h += `<p class="stack-silent"><span class="k">Counted for nothing</span> ${list(silent.map(sensorLink))}: no doubt edge in this vocabulary yet.</p>`;
      }
      result.innerHTML = h;
      result.hidden = false;
      tally.innerHTML = `<a href="#stack-result">${closedD.length} of ${doubts.length} doubts closed</a>` +
        (openD.length ? `, ${openD.length} open` : '');
    };

    const remembered = new Set(load());
    boxes.forEach(b => { if (remembered.has(b.value)) b.checked = true; });
    // Always starts folded, remembered ticks or not; only a link straight
    // into the checklist opens it.
    const details = stackForm.closest('details');
    if (details && /^#(your-stack|stack-result)$/.test(location.hash)) {
      details.open = true;
    }
    stackForm.addEventListener('change', render);
    stackForm.addEventListener('reset', () => { setTimeout(render, 0); });
    render();
  }

  // Doubts page: isolate a doubt or a sensor in the server-rendered graph.
  // Hover previews, click pins, click again (or click away) releases. The
  // detail strip is filled from the per-doubt entries further down the page,
  // so the two can never say different things.
  const doubtGraph = document.querySelector('.doubt-graph');
  if (doubtGraph) {
    const cards = document.querySelector('.doubt-cards');
    const detail = document.querySelector('.doubt-detail');
    const cardOf = {};
    document.querySelectorAll('.doubt-card').forEach(e => { cardOf[e.dataset.d] = e; });
    const doubtName = {};
    doubtGraph.querySelectorAll('.doubt').forEach(g => {
      doubtName[g.dataset.d] = g.querySelector('.d-name').textContent;
    });
    const sensorTitle = {};
    const sensorFamily = {};
    doubtGraph.querySelectorAll('.sensor[data-side="l"]').forEach(g => {
      sensorTitle[g.dataset.s] = g.querySelector('.s-label').textContent;
      const fill = g.querySelector('.s-dot').getAttribute('fill') || '';
      sensorFamily[g.dataset.s] = fill.replace(/^var\(--fam-|\)$/g, '');
    });
    let pinned = null, hover = null;
    const same = (a, b) => a && b && a.type === b.type && a.id === b.id;
    const list = (cls, label, items) =>
      `<span class="list ${cls}"><span class="k">${label}</span>${items.length ? items.join(', ') : '—'}</span>`;

    const render = () => {
      const sel = hover || pinned;
      doubtGraph.classList.toggle('has-sel', !!sel);
      doubtGraph.querySelectorAll('.hi, .sel').forEach(n => n.classList.remove('hi', 'sel'));
      cards.querySelectorAll('.doubt-card').forEach(c => {
        c.classList.toggle('on', !!sel && sel.type === 'doubt' && c.dataset.d === sel.id);
      });
      detail.hidden = false;
      if (!sel) {
        detail.innerHTML = '<span class="who">Nothing selected</span><span>Hover or click a doubt card above, a doubt in the middle of the graph, or a sensor on either side.</span>';
        return;
      }
      if (sel.type === 'doubt') {
        doubtGraph.querySelector(`.doubt[data-d="${sel.id}"]`).classList.add('hi', 'sel');
        doubtGraph.querySelectorAll(`.edge[data-d="${sel.id}"]`).forEach(e => {
          e.classList.add('hi');
          const side = e.classList.contains('misread') ? 'l' : 'r';
          doubtGraph.querySelector(`.sensor[data-s="${e.dataset.s}"][data-side="${side}"]`).classList.add('hi');
        });
        const card = cardOf[sel.id];
        const desc = card ? card.querySelector('.doubt-card-desc').textContent : '';
        const misread = [], closes = [], reveals = [];
        doubtGraph.querySelectorAll(`.edge[data-d="${sel.id}"]`).forEach(e => {
          const link = `<a href="/sensors/${e.dataset.s}/" class="wikilink">${sensorTitle[e.dataset.s]}</a>`;
          (e.classList.contains('misread') ? misread : e.classList.contains('reveals') ? reveals : closes).push(link);
        });
        detail.innerHTML =
          `<span class="who"><a href="#${sel.id}" class="wikilink">${doubtName[sel.id]}</a><small>${sel.id}</small></span><span>${desc}</span>` +
          list('misread', 'misread as closing', misread) +
          list('closes', 'closed by', closes) +
          (reveals.length ? list('reveals', 'revealed after by', reveals) : '');
        return;
      }
      doubtGraph.querySelectorAll(`.sensor[data-s="${sel.id}"]`).forEach(n => n.classList.add('hi', 'sel'));
      const misread = [], closes = [], reveals = [];
      doubtGraph.querySelectorAll(`.edge[data-s="${sel.id}"]`).forEach(e => {
        e.classList.add('hi');
        doubtGraph.querySelector(`.doubt[data-d="${e.dataset.d}"]`).classList.add('hi');
        const name = `<a href="#${e.dataset.d}" class="wikilink">${doubtName[e.dataset.d]}</a>`;
        (e.classList.contains('misread') ? misread : e.classList.contains('reveals') ? reveals : closes).push(name);
      });
      const none = !misread.length && !closes.length && !reveals.length;
      detail.innerHTML =
        `<span class="who"><a href="/sensors/${sel.id}/" class="wikilink">${sensorTitle[sel.id]}</a><small>${sensorFamily[sel.id]}</small></span>` +
        (none ? '<span>No doubt edge in this vocabulary.</span>' : '') +
        list('misread', 'misread as closing', misread) +
        list('closes', 'closes', closes) +
        (reveals.length ? list('reveals', 'reveals after', reveals) : '');
    };

    const target = ev => {
      const g = ev.target.closest('.doubt, .sensor, .doubt-card');
      if (!g) return null;
      if (g.dataset.d) return { type: 'doubt', id: g.dataset.d };
      if (g.dataset.s) return { type: 'sensor', id: g.dataset.s };
      return null;
    };
    [doubtGraph, cards].forEach(root => {
      root.addEventListener('mouseover', ev => { const t = target(ev); if (t) { hover = t; render(); } });
      root.addEventListener('mouseout', ev => { if (target(ev)) { hover = null; render(); } });
      root.addEventListener('click', ev => {
        const t = target(ev);
        if (!t) return;
        pinned = same(pinned, t) ? null : t;
        hover = null;
        render();
      });
    });
    cards.addEventListener('keydown', ev => {
      if (ev.key !== 'Enter' && ev.key !== ' ') return;
      const t = target(ev);
      if (!t) return;
      ev.preventDefault();
      pinned = same(pinned, t) ? null : t;
      hover = null;
      render();
    });
    document.addEventListener('click', ev => {
      if (!ev.target.closest('.doubt, .sensor, .doubt-card, .doubt-detail')) {
        pinned = null; hover = null; render();
      }
    });
    render();
  }
});
