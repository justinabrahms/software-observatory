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
});
