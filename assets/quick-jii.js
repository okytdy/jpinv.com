/* Show the delivery sequence once, when it enters the viewport. */
(function () {
  var flow = document.querySelector('.qj-process-line');
  if (!flow || !('IntersectionObserver' in window)) return;
  var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (motion.matches) return;

  var observer = new IntersectionObserver(function (entries) {
    if (!entries.some(function (entry) { return entry.isIntersecting; })) return;
    if (!motion.matches) flow.classList.add('is-in-view');
    observer.disconnect();
  }, { threshold: 0.2 });
  observer.observe(flow);
})();
