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

  // Signal card keyboard accessibility
  document.querySelectorAll('.signal-card').forEach(card => {
    if (card.getAttribute('onclick')) {
      card.setAttribute('tabindex', '0');
      card.setAttribute('role', 'link');
      card.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          card.click();
        }
      });
    }
  });

  // Deep-linkable headings: hovering a heading with an id shows a link icon;
  // clicking it copies the jumplink (page URL + #anchor) to the clipboard.
  const HEADING_LINK_SELECTOR = [
    '.section-heading',
    '.property-detail-title',
    '.family-title',
    '.featured-title',
    '.about-content h2',
    '.signal-detail-body h2',
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

    fetch('/search-index.json')
      .then(r => r.json())
      .then(data => { index = data; })
      .catch(() => {});

    function render(items, query) {
      if (!query) { results.hidden = true; return; }
      if (!items.length) {
        results.innerHTML = '<div class="search-empty">No matches</div>';
        results.hidden = false;
        return;
      }
      results.innerHTML = items.map((item, i) => `
        <a class="search-result${i === activeIdx ? ' active' : ''}" href="${item.url}">
          <div class="search-result-title">${item.title}</div>
          <div class="search-result-meta">${item.kind === 'family' ? 'Family' : item.family}</div>
          ${item.blurb ? `<div class="search-result-blurb">${item.blurb}</div>` : ''}
        </a>`).join('');
      results.hidden = false;
    }

    function run() {
      const q = input.value.trim().toLowerCase();
      if (!q || !index) { render([], q); return; }
      const scored = [];
      for (const item of index) {
        const title = item.title.toLowerCase();
        const fam = (item.family || '').toLowerCase();
        const blurb = (item.blurb || '').toLowerCase();
        let score = -1;
        if (title.startsWith(q)) score = 3;
        else if (title.includes(q)) score = 2;
        else if (fam.includes(q)) score = 1;
        else if (blurb.includes(q)) score = 0;
        if (score >= 0) scored.push([score, item]);
      }
      scored.sort((a, b) => b[0] - a[0] || a[1].title.localeCompare(b[1].title));
      activeIdx = -1;
      render(scored.slice(0, 8).map(s => s[1]), q);
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
        links.forEach((l, i) => l.classList.toggle('active', i === activeIdx));
        links[activeIdx].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter' && activeIdx >= 0 && links[activeIdx]) {
        e.preventDefault();
        window.location.href = links[activeIdx].href;
      } else if (e.key === 'Escape') {
        results.hidden = true;
        input.blur();
      }
    });

    document.addEventListener('click', e => {
      if (!searchBox.contains(e.target)) results.hidden = true;
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
