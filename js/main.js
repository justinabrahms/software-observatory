// Software Observatory — minimal interactivity

document.addEventListener('DOMContentLoaded', () => {
  // Filter list active toggle (general)
  document.querySelectorAll('.filter-list li').forEach(li => {
    li.addEventListener('click', () => {
      const siblings = li.closest('.filter-list').querySelectorAll('li');
      siblings.forEach(s => s.classList.remove('active'));
      li.classList.add('active');
    });
  });

  // Catalog family filter
  const familyFilter = document.getElementById('family-filter');
  if (familyFilter) {
    familyFilter.querySelectorAll('li').forEach(li => {
      li.addEventListener('click', () => {
        const family = li.dataset.family;
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

  // Search: fetch the build-time index, filter on input, render a dropdown
  const searchBox = document.querySelector('.search-box');
  if (searchBox) {
    const input = searchBox.querySelector('.search-input');
    const results = searchBox.querySelector('.search-results');
    const rootDepth = searchBox.dataset.rootDepth || '';
    let index = null;
    let activeIdx = -1;

    fetch(rootDepth + 'search-index.json')
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
        <a class="search-result${i === activeIdx ? ' active' : ''}" href="${rootDepth}${item.url}">
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
      node.addEventListener('mouseenter', () => {
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
      });
      node.addEventListener('mouseleave', () => {
        nodes.forEach(n => n.classList.remove('dim'));
        edges.forEach(e => e.classList.remove('dim'));
        depGraph.classList.remove('focus-active');
      });
    });
  }
});
