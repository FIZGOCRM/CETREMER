/* Only enrolled, accessible courses are rendered by the server. */
(() => {
  'use strict';
  const root = document.querySelector('[data-course-carousel]');
  if (!root) return;
  // Increase the natural block height without scaling its text or controls.
  function resizeHero() {
    const styles = getComputedStyle(root);
    const contentHeight = Math.max(...[...root.querySelectorAll('.hero__content')].map(content => content.scrollHeight));
    const naturalHeight = Math.max(parseFloat(styles.minHeight), contentHeight + parseFloat(styles.paddingTop) + parseFloat(styles.paddingBottom));
    root.style.height = `${naturalHeight * 1.2}px`;
  }
  resizeHero();
  document.fonts.ready.then(resizeHero);
  addEventListener('resize', () => requestAnimationFrame(resizeHero));
  const contentObserver = new ResizeObserver(resizeHero);
  root.querySelectorAll('.hero__content').forEach(content => contentObserver.observe(content));
  const slides = [...root.querySelectorAll('[data-hero-slide]')];
  if (slides.length < 2) return;
  const dots = [...root.querySelectorAll('[data-hero-index]')];
  const pause = root.querySelector('[data-hero-pause]');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let current = 0;
  let paused = motion.matches;

  function show(index) {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, position) => {
      const inactive = position !== current;
      slide.hidden = inactive;
      slide.inert = inactive;
      slide.setAttribute('aria-hidden', String(inactive));
    });
    dots.forEach((dot, position) => {
      if (position === current) dot.setAttribute('aria-current', 'true');
      else dot.removeAttribute('aria-current');
    });
  }
  function renderPause() {
    pause.setAttribute('aria-pressed', String(paused));
    pause.setAttribute('aria-label', paused ? 'Iniciar rotação automática' : 'Pausar rotação automática');
    pause.querySelector('[data-pause-icon]').hidden = paused;
    pause.querySelector('[data-play-icon]').hidden = !paused;
  }
  root.querySelector('[data-hero-prev]').addEventListener('click', () => show(current - 1));
  root.querySelector('[data-hero-next]').addEventListener('click', () => show(current + 1));
  dots.forEach((dot, index) => dot.addEventListener('click', () => show(index)));
  pause.addEventListener('click', () => { paused = !paused; renderPause(); });
  motion.addEventListener('change', () => { paused = motion.matches; renderPause(); });
  renderPause();
  // No automatic changes while reading, using the keyboard or viewing a dialog.
  setInterval(() => {
    if (paused || document.hidden || root.matches(':hover') || root.contains(document.activeElement) || document.querySelector('dialog[open]')) return;
    show(current + 1);
  }, 8000);
})();
