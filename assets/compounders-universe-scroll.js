(() => {
  const scroller = document.querySelector('.table-scroll');
  const controls = document.querySelector('[data-table-scroll-controls]');
  if (!scroller || !controls) return;

  const previous = controls.querySelector('[data-scroll-prev]');
  const next = controls.querySelector('[data-scroll-next]');

  function update() {
    const remaining = scroller.scrollWidth - scroller.clientWidth;
    controls.hidden = remaining <= 1;
    previous.disabled = scroller.scrollLeft <= 1;
    next.disabled = scroller.scrollLeft >= remaining - 1;
  }

  function move(direction) {
    scroller.scrollBy({
      left: direction * Math.max(280, scroller.clientWidth * 0.8),
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
    });
  }

  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  scroller.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
})();
