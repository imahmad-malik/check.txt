/* Progressive enhancement for the native-block editorial theme. */
(() => {
 'use strict';
 const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
 const rawSettings = window.BixieEditorialSettings || {};
 const enabled = (value) => value !== false && value !== 0 && value !== '0';
 const readLabel = (value, fallback) => typeof value === 'string' && value.trim() ? value.trim() : fallback;
 const photoControlSelector = '[data-bixie-motion-toggle], .bixie-photo-motion-toggle a';
 const videoControlSelector = '[data-bixie-video-toggle], .bixie-video-motion-toggle a';
 const settings = {
  motionEnabled: enabled(rawSettings.motionEnabled),
  motionSpeed: Number.isFinite(Number(rawSettings.motionSpeed)) ? Math.max(5, Math.min(36, Number(rawSettings.motionSpeed))) : 15,
  videoAutoplay: enabled(rawSettings.videoAutoplay),
  photoPlayLabel: readLabel(rawSettings.photoPlayLabel, 'Play photo motion'),
  photoNextLabel: readLabel(rawSettings.photoNextLabel, 'Show next photographs'),
  filmPauseLabel: readLabel(rawSettings.filmPauseLabel, 'Pause film')
 };
 const rails = [];
 const rotating = [];
 const films = [];
 let frame = 0;
 let previousTime = 0;
 const now = () => window.performance.now();

 function findTarget(button, selector) {
  const id = button.getAttribute('aria-controls') || button.getAttribute('data-bixie-target') || (button.tagName === 'A' && button.hash ? button.hash : '');
  if (id) {
   const target = document.getElementById(id.replace(/^#/, ''));
   if (target) return target.matches(selector) ? target : target.querySelector(selector);
  }
  const section = button.closest('.bixie-section, .bixie-film, section');
  if (section) return section.matches(selector) ? section : section.querySelector(selector);
  let group = button.parentElement;
  while (group) {
   const target = group.matches(selector) ? group : group.querySelector(selector);
   if (target) return target;
   group = group.parentElement;
  }
  return null;
 }

 function prepareControl(button, type) {
  button.setAttribute(type === 'photo' ? 'data-bixie-motion-toggle' : 'data-bixie-video-toggle', '');
  if (!button.hasAttribute('data-bixie-initial-label')) {
   button.setAttribute('data-bixie-initial-label', button.textContent.trim().replace(/\s+/g, ' ') || (type === 'photo' ? 'Pause photographs' : 'Play film'));
  }
  if (button.tagName === 'A') {
   button.setAttribute('role', 'button');
   button.setAttribute('tabindex', '0');
   button.addEventListener('keydown', (event) => {
    if (event.key === ' ' || event.key === 'Spacebar') {
     event.preventDefault();
     button.click();
    }
   });
  }
 }

 function updateRailButton(button, paused) {
  if (reducedMotion.matches) button.removeAttribute('aria-pressed');
  else button.setAttribute('aria-pressed', String(paused));
  button.setAttribute('data-bixie-reduced', String(reducedMotion.matches));
  const label = button.querySelector('[data-bixie-motion-label]');
  const message = reducedMotion.matches ? settings.photoNextLabel : paused ? settings.photoPlayLabel : button.getAttribute('data-bixie-initial-label');
  if (label) label.textContent = message;
  else button.textContent = message;
  button.setAttribute('aria-label', message);
 }

 function measureRail(rail) {
  rail.travel = Math.max(0, rail.element.scrollWidth - rail.element.clientWidth);
  rail.position = Math.min(rail.travel, Math.max(0, rail.element.scrollLeft));
 }

 function railActive(rail) {
  return !reducedMotion.matches && !rail.paused && rail.visible && !document.hidden && now() > rail.holdUntil && rail.travel > 1;
 }

 function tick(time) {
  frame = 0;
  const delta = previousTime ? Math.min(50, time - previousTime) / 1000 : 0;
  previousTime = time;
  let active = false;
  rails.forEach((rail) => {
   if (!railActive(rail)) return;
   active = true;
   rail.position += rail.direction * rail.speed * delta;
   if (rail.position >= rail.travel) {
    rail.position = rail.travel;
    rail.direction = -1;
   } else if (rail.position <= 0) {
    rail.position = 0;
    rail.direction = 1;
   }
   rail.writing = true;
   rail.element.scrollLeft = rail.position;
   rail.lastWrittenPosition = rail.element.scrollLeft;
   rail.writing = false;
  });
  if (active) frame = window.requestAnimationFrame(tick);
  else previousTime = 0;
 }

 function beginMotion() {
  if (!frame && rails.some(railActive)) frame = window.requestAnimationFrame(tick);
 }

 function holdRail(rail, milliseconds = 5000) {
  rail.holdUntil = now() + milliseconds;
  rail.position = rail.element.scrollLeft;
  window.clearTimeout(rail.holdTimer);
  rail.holdTimer = window.setTimeout(beginMotion, milliseconds + 30);
 }

 function prepareRails() {
  document.querySelectorAll('.bixie-photo-row, [data-bixie-motion]').forEach((element) => {
   if (rails.some((rail) => rail.element === element)) return;
   if (!element.querySelector('.bixie-photo-track, .bixie-photo-item, figure, img')) return;
   const requestedSpeed = Number(element.getAttribute('data-bixie-speed'));
   const rail = { element, travel: 0, position: 0, direction: 1, speed: Number.isFinite(requestedSpeed) && requestedSpeed > 0 ? Math.max(5, Math.min(36, requestedSpeed)) : settings.motionSpeed, paused: !settings.motionEnabled, visible: true, holdUntil: 0, holdTimer: 0, writing: false, lastWrittenPosition: null, buttons: [] };
   rails.push(rail);
   measureRail(rail);
   element.setAttribute('data-bixie-motion-ready', 'true');
   element.addEventListener('wheel', () => holdRail(rail), { passive: true });
   element.addEventListener('pointerdown', () => holdRail(rail, 8000), { passive: true });
   element.addEventListener('keydown', () => holdRail(rail, 8000));
   element.addEventListener('focusin', () => holdRail(rail, 8000));
   element.addEventListener('scroll', () => {
    if (rail.writing || (rail.lastWrittenPosition !== null && Math.abs(element.scrollLeft - rail.lastWrittenPosition) < .5)) return;
    rail.position = element.scrollLeft;
   }, { passive: true });
   element.querySelectorAll('img').forEach((img) => {
    if (!img.complete) img.addEventListener('load', () => { measureRail(rail); beginMotion(); }, { once: true });
   });
   if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(() => { measureRail(rail); beginMotion(); });
    observer.observe(element);
    const track = element.querySelector('.bixie-photo-track');
    if (track) observer.observe(track);
   }
  });
  document.querySelectorAll(photoControlSelector).forEach((button) => {
   prepareControl(button, 'photo');
   const target = findTarget(button, '.bixie-photo-row, [data-bixie-motion]');
   const controlled = target ? rails.filter((rail) => rail.element === target) : rails;
   if (!controlled.length) { button.hidden = true; return; }
   if (target) {
    if (!target.id) target.id = 'bixie-photo-flow-runtime-' + (rails.findIndex((rail) => rail.element === target) + 1);
    button.setAttribute('aria-controls', target.id);
   }
   controlled.forEach((rail) => rail.buttons.push(button));
   updateRailButton(button, reducedMotion.matches || controlled.every((rail) => rail.paused));
   button.addEventListener('click', (event) => {
    event.preventDefault();
    if (reducedMotion.matches) {
     controlled.forEach((rail) => {
      measureRail(rail);
      rail.element.scrollTo({ left: rail.position >= rail.travel - 1 ? 0 : Math.min(rail.travel, rail.position + rail.element.clientWidth * .8), behavior: 'instant' });
     });
     button.setAttribute('aria-label', settings.photoNextLabel);
     return;
    }
    const pause = !controlled.every((rail) => rail.paused);
    controlled.forEach((rail) => {
     rail.paused = pause;
     rail.holdUntil = 0;
     rail.position = rail.element.scrollLeft;
     rail.buttons.forEach((control) => updateRailButton(control, pause));
    });
    rotating.forEach((gallery) => { gallery.paused = pause; updateRotation(gallery); });
    beginMotion();
   });
  });
 }

 function prepareRotation() {
  document.querySelectorAll('[data-bixie-rotate]').forEach((element) => {
   const items = [...element.children].filter((child) => child.matches('figure, .wp-block-image, .wp-block-group, .bixie-photo-item'));
   if (items.length < 2) return;
   const gallery = { element, items, current: 0, timer: 0, visible: true, paused: !settings.motionEnabled || !document.querySelector(photoControlSelector) };
   rotating.push(gallery);
   element.classList.add('bixie-rotate-ready');
   items[0].classList.add('is-current');
   updateRotation(gallery);
  });
 }

 function updateRotation(gallery) {
  window.clearInterval(gallery.timer);
  if (reducedMotion.matches || document.hidden || !gallery.visible || gallery.paused) return;
  gallery.timer = window.setInterval(() => {
   gallery.items[gallery.current].classList.remove('is-current');
   gallery.current = (gallery.current + 1) % gallery.items.length;
   gallery.items[gallery.current].classList.add('is-current');
  }, 4800);
 }

 function updateVideo(film) {
  const playing = !film.video.paused && !film.video.ended;
  film.buttons.forEach((button) => {
   button.setAttribute('aria-pressed', String(playing));
   const label = button.querySelector('[data-bixie-video-label]');
   const message = playing ? settings.filmPauseLabel : button.getAttribute('data-bixie-initial-label');
   if (label) label.textContent = message;
   else button.textContent = message;
   button.setAttribute('aria-label', message);
  });
 }

 function playVideo(film) {
  const attempt = film.video.play();
  if (attempt && typeof attempt.catch === 'function') attempt.catch(() => updateVideo(film));
 }

 function pauseVideo(film) {
  if (film.video.paused) return;
  film.internalPause = true;
  film.video.pause();
 }

 function prepareFilms() {
  document.querySelectorAll('.bixie-film video, video[data-bixie-autoplay]').forEach((video) => {
   if (films.some((film) => film.video === video)) return;
   video.playsInline = true;
   video.setAttribute('playsinline', '');
   video.controls = true;
   const requestedAutoplay = video.hasAttribute('autoplay') || video.hasAttribute('data-bixie-autoplay');
   const film = { video, buttons: [], visible: true, userPaused: false, internalPause: false, auto: requestedAutoplay && settings.videoAutoplay && settings.motionEnabled };
   films.push(film);
   if (!film.auto) { video.autoplay = false; video.removeAttribute('autoplay'); pauseVideo(film); }
   if (film.auto) {
    video.muted = true;
    video.defaultMuted = true;
    video.setAttribute('muted', '');
    if (reducedMotion.matches) { video.autoplay = false; pauseVideo(film); }
    else playVideo(film);
   }
   ['play', 'pause', 'ended', 'error'].forEach((event) => video.addEventListener(event, () => {
    if (event === 'pause') {
     if (!film.internalPause && !video.ended) film.userPaused = true;
     film.internalPause = false;
    } else if (event === 'play') film.userPaused = false;
    updateVideo(film);
   }));
  });
  document.querySelectorAll(videoControlSelector).forEach((button) => {
   prepareControl(button, 'video');
   const video = findTarget(button, 'video');
   const film = films.find((candidate) => candidate.video === video);
   if (!film) { button.hidden = true; return; }
   if (!video.id) video.id = 'bixie-film-runtime-' + (films.indexOf(film) + 1);
   button.setAttribute('aria-controls', video.id);
   film.buttons.push(button);
   updateVideo(film);
   button.addEventListener('click', (event) => {
    event.preventDefault();
    if (video.paused || video.ended) {
     film.userPaused = false;
     playVideo(film);
    } else {
     film.userPaused = true;
     video.pause();
    }
   });
  });
 }

 function observeVisibility() {
  if (!('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver((entries) => {
   entries.forEach((entry) => {
    const rail = rails.find((candidate) => candidate.element === entry.target);
    if (rail) { rail.visible = entry.isIntersecting; beginMotion(); }
    const gallery = rotating.find((candidate) => candidate.element === entry.target);
    if (gallery) { gallery.visible = entry.isIntersecting; updateRotation(gallery); }
    const film = films.find((candidate) => candidate.video === entry.target);
    if (film) {
     film.visible = entry.isIntersecting;
     if (!entry.isIntersecting && !film.video.paused) pauseVideo(film);
     else if (entry.isIntersecting && film.auto && !film.userPaused && !reducedMotion.matches) playVideo(film);
    }
   });
  }, { rootMargin: '80px 0px', threshold: 0.01 });
  rails.forEach((rail) => observer.observe(rail.element));
  rotating.forEach((gallery) => observer.observe(gallery.element));
  films.forEach((film) => observer.observe(film.video));
 }

 function preferenceChanged() {
  rails.forEach((rail) => rail.buttons.forEach((button) => updateRailButton(button, reducedMotion.matches || rail.paused)));
  rotating.forEach(updateRotation);
  films.forEach((film) => {
   if (reducedMotion.matches && film.auto) pauseVideo(film);
   else if (film.auto && film.visible && !film.userPaused && !document.hidden) playVideo(film);
  });
  beginMotion();
 }

 function init() {
  prepareRails();
  prepareRotation();
  prepareFilms();
  observeVisibility();
  beginMotion();
  if (reducedMotion.addEventListener) reducedMotion.addEventListener('change', preferenceChanged);
  else if (reducedMotion.addListener) reducedMotion.addListener(preferenceChanged);
  document.addEventListener('visibilitychange', () => {
   previousTime = 0;
   rotating.forEach(updateRotation);
   if (document.hidden) films.forEach((film) => { if (film.auto) pauseVideo(film); });
   else films.forEach((film) => { if (film.auto && film.visible && !film.userPaused && !reducedMotion.matches) playVideo(film); });
   beginMotion();
  });
  window.addEventListener('resize', () => { rails.forEach(measureRail); beginMotion(); }, { passive: true });
 }
 if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
 else init();
})();
