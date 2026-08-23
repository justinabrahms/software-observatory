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
