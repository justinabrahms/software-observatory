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
});
