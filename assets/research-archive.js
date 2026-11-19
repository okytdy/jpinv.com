(() => {
  const grid = document.querySelector('#archive-grid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll('.ra-card')];
  const search = document.querySelector('#archive-search');
  const sort = document.querySelector('#archive-sort');
  const count = document.querySelector('#archive-count');
  const empty = document.querySelector('#archive-empty');
  const update = () => {
    const query = search.value.trim().toLowerCase();
    cards.sort((a, b) => sort.value === 'ticker' ? Number(a.dataset.ticker) - Number(b.dataset.ticker) : b.dataset.date.localeCompare(a.dataset.date) || Number(a.dataset.ticker) - Number(b.dataset.ticker));
    let visible = 0;
    for (const card of cards) { card.hidden = !card.dataset.search.includes(query); if (!card.hidden) visible++; grid.append(card); }
    count.textContent = `${visible} ${document.documentElement.lang === 'ja' ? '件' : visible === 1 ? 'report' : 'reports'}`;
    empty.hidden = visible !== 0;
  };
  search.addEventListener('input', update);
  sort.addEventListener('change', update);
})();
