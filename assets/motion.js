/* JII motion - Phase 5b (2026-07-12). Scroll-reveal via IntersectionObserver.
   Opacity/transform only (no layout shift); above-the-fold elements are never hidden;
   respects prefers-reduced-motion; no dependencies. */
(function () {
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var SEL = '.scope-card,.fam-card,.related-card,.plan-card,.voice-card2,.step,.deliv,' +
            '.cta-band,.faq-item,details.acc,.contact-band,.inq-form,.id-card,' +
            '.scenario-card,.card--reel,.section-head';
  var els = document.querySelectorAll(SEL);
  if (!els.length) return;
  var st = document.createElement('style');
  st.textContent = '.jr{opacity:0;transform:translateY(12px);transition:opacity .55s cubic-bezier(.22,.61,.36,1),transform .55s cubic-bezier(.22,.61,.36,1)}.jr.jr-in{opacity:1;transform:none}';
  document.head.appendChild(st);
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('jr-in'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
  var i = 0;
  els.forEach(function (el) {
    var r = el.getBoundingClientRect();
    if (r.top < window.innerHeight && r.bottom > 0) return; /* already on screen: leave alone */
    el.classList.add('jr');
    el.style.transitionDelay = ((i % 5) * 60) + 'ms';
    i++;
    io.observe(el);
  });
})();
