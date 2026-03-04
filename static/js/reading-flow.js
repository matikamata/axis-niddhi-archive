/**
 * 💎 BRASILEIRINHO ENGINE — AXIS-NIDDHI v3.0
 * reading-flow.js — Scroll spy + smooth anchors
 * Progressive enhancement — nenhuma funcionalidade essencial aqui.
 */

(function () {
  'use strict';

  /* ── SCROLL SPY: destaca item ativo no mini-TOC ─────────────────────── */
  function initScrollSpy() {
    const tocLinks = document.querySelectorAll('.mini-toc a[href^="#"]');
    if (!tocLinks.length) return;

    const headings = Array.from(tocLinks).map(function (a) {
      return document.getElementById(a.getAttribute('href').slice(1));
    }).filter(Boolean);

    function onScroll() {
      let current = null;
      headings.forEach(function (h) {
        if (window.scrollY >= h.offsetTop - 120) current = h;
      });
      tocLinks.forEach(function (a) {
        const isActive = current && a.getAttribute('href') === '#' + current.id;
        a.style.color      = isActive ? 'var(--green-axiom)' : '';
        a.style.fontWeight = isActive ? 'bold' : '';
      });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // Inicializar
  }

  /* ── SMOOTH SCROLL para âncoras internas ────────────────────────────── */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        const target = document.getElementById(a.getAttribute('href').slice(1));
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  /* ── INIT ───────────────────────────────────────────────────────────── */
  function init() {
    initScrollSpy();
    initSmoothScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());
