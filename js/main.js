// Software Observatory — minimal interactivity

document.addEventListener('DOMContentLoaded', () => {
  // Filter list active toggle
  document.querySelectorAll('.filter-list li').forEach(li => {
    li.addEventListener('click', () => {
      const siblings = li.closest('.filter-list').querySelectorAll('li');
      siblings.forEach(s => s.classList.remove('active'));
      li.classList.add('active');
    });
  });

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

  // Atlas dot hover tooltip
  document.querySelectorAll('.atlas-svg .zone-group').forEach(g => {
    const dot = g.querySelector('.zone-dot');
    const label = g.querySelector('text');
    if (dot && label) {
      label.style.opacity = '0.7';
      dot.addEventListener('mouseenter', () => {
        label.style.opacity = '1';
        label.style.fill = 'var(--accent)';
        dot.setAttribute('r', '10');
      });
      dot.addEventListener('mouseleave', () => {
        label.style.opacity = '0.7';
        label.style.fill = '';
        dot.setAttribute('r', '7');
      });
    }
  });
});
