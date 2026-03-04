/**
 * 💎 BRASILEIRINHO ENGINE — AXIS-NIDDHI v3.0
 * main.js — Progressive Enhancement
 *
 * Axiomas:
 *   - Site 100% funcional sem este arquivo (CSS-only fallback para lang switch)
 *   - Zero dependências externas
 *   - Compatível com file://, localhost, IPFS
 *   - Sem localStorage (compatibilidade IPFS e distribuição offline)
 */

(function () {
  'use strict';

  /* ── 1. THEME SWITCHER ──────────────────────────────────────────────── */

  const THEMES = [
    { id: 'sunrise', label: '☀️', title: 'Sunrise (light)' },
    { id: 'dark',    label: '🌙', title: 'Dark'            },
    { id: 'colirio', label: '🌿', title: 'Colírio (green)' },
    { id: 'sunset',  label: '🌆', title: 'Sunset (warm)'   },
  ];

  function initThemeSwitcher() {
    const container = document.getElementById('theme-controls');
    if (!container) return;

    THEMES.forEach(function (theme) {
      const btn = document.createElement('button');
      btn.className = 'theme-btn';
      btn.textContent = theme.label;
      btn.title = theme.title;
      btn.setAttribute('aria-label', 'Theme: ' + theme.title);
      btn.addEventListener('click', function () {
        document.body.setAttribute('data-theme', theme.id);
      });
      container.appendChild(btn);
    });
  }

  /* ── 2. ACCORDION (LIBRARY INDEX) ──────────────────────────────────── */

  function initAccordion() {
    const sections = document.querySelectorAll('.library-section h2');
    if (!sections.length) return;

    // Abrir seção se URL tem âncora (#section-TL)
    const hash = window.location.hash;
    let targetCode = null;
    if (hash && hash.startsWith('#section-')) {
      targetCode = hash.replace('#section-', '');
    }

    sections.forEach(function (h2) {
      const code = h2.getAttribute('data-code');
      const list = h2.nextElementSibling;
      if (!list) return;

      if (code === targetCode) {
        h2.classList.add('active');
        list.style.display = 'block';
        // Scroll suave
        setTimeout(function () {
          h2.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }

      h2.addEventListener('click', function () {
        const isOpen = h2.classList.contains('active');
        // Fechar todos
        sections.forEach(function (s) {
          s.classList.remove('active');
          if (s.nextElementSibling) s.nextElementSibling.style.display = 'none';
        });
        // Abrir clicado (toggle)
        if (!isOpen) {
          h2.classList.add('active');
          list.style.display = 'block';
          // Atualizar hash sem scroll
          if (code) {
            history.replaceState(null, '', '#section-' + code);
          }
        } else {
          history.replaceState(null, '', window.location.pathname);
        }
      });
    });
  }

  /* ── 3. MINI-TOC DINÂMICO ───────────────────────────────────────────── */

  function buildToc(articleId, tocListId) {
    const article = document.getElementById(articleId);
    const tocList = document.getElementById(tocListId);
    if (!article || !tocList) return;

    const headings = article.querySelectorAll('h3, h4, h5');
    if (!headings.length) return;

    headings.forEach(function (h, i) {
      if (!h.id) h.id = articleId + '-h-' + i;
      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.textContent;
      a.style.paddingLeft = h.tagName === 'H5' ? '1.5rem' :
                            h.tagName === 'H4' ? '0.75rem' : '0';
      li.appendChild(a);
      tocList.appendChild(li);
    });
  }

  function initToc() {
    buildToc('content-en', 'toc-list-en');
    buildToc('content-pt', 'toc-list-pt');
  }

  /* ── 4. BUSCA OFFLINE ───────────────────────────────────────────────── */

  let _searchIndex = null;
  let _searchLoaded = false;

  function loadSearchIndex(baseUrl) {
    if (_searchLoaded) return Promise.resolve(_searchIndex);
    _searchLoaded = true;

    return fetch(baseUrl + 'search_index.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        _searchIndex = data;
        return data;
      })
      .catch(function () {
        _searchIndex = [];
        return [];
      });
  }

  function scorePost(post, query) {
    const q = query.toLowerCase();
    let score = 0;
    if (post.title_en && post.title_en.toLowerCase().includes(q)) score += 3;
    if (post.title_pt && post.title_pt.toLowerCase().includes(q)) score += 2;
    if (post.section  && post.section.toLowerCase().includes(q))  score += 1;
    if (post.slug     && post.slug.toLowerCase().includes(q))     score += 1;
    if (post.pdpn     && post.pdpn.toLowerCase().includes(q))     score += 1;
    return score;
  }

  function renderSearchResults(results, container, baseUrl) {
    container.innerHTML = '';
    if (!results.length) {
      container.innerHTML = '<p style="padding:1rem;color:var(--meta-color)">No results found.</p>';
      container.hidden = false;
      return;
    }
    const ul = document.createElement('ul');
    ul.style.cssText = 'list-style:none;margin:0;padding:0.5rem 0';
    results.slice(0, 12).forEach(function (post) {
      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href = baseUrl + post.url;
      a.style.cssText = 'display:block;padding:0.6rem 1rem;color:var(--fg);text-decoration:none;font-size:0.9rem;border-bottom:1px solid var(--border-color)';
      a.innerHTML =
        '<strong style="color:var(--green-axiom)">' + (post.title_en || post.slug) + '</strong>' +
        '<br><small style="color:var(--meta-color)">' + post.section + ' · ' + post.pdpn + (post.has_pt ? ' 🇧🇷' : '') + '</small>';
      a.addEventListener('mouseover', function () { a.style.background = 'rgba(0,204,0,0.06)'; });
      a.addEventListener('mouseout',  function () { a.style.background = ''; });
      li.appendChild(a);
      ul.appendChild(li);
    });
    container.appendChild(ul);
    container.hidden = false;
  }

  function initSearch() {
    const input     = document.getElementById('search-input');
    const resultsEl = document.getElementById('search-results');
    if (!input || !resultsEl) return;

    // Calcular base URL relativa (funciona em file:// e IPFS)
    const pathParts = window.location.pathname.split('/');
    // index.html está na raiz → baseUrl = './'
    // post.html está em pages/PDPN/ → baseUrl = '../../'
    const depth = (window.location.pathname.match(/pages\/[^/]+\//) ? 2 : 0);
    const baseUrl = depth === 0 ? './' : '../../';

    let debounceTimer = null;
    input.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      const query = input.value.trim();
      if (query.length < 2) {
        resultsEl.hidden = true;
        resultsEl.innerHTML = '';
        return;
      }
      debounceTimer = setTimeout(function () {
        loadSearchIndex(baseUrl).then(function (index) {
          if (!index || !index.length) return;
          const scored = index
            .map(function (p) { return { post: p, score: scorePost(p, query) }; })
            .filter(function (x) { return x.score > 0; })
            .sort(function (a, b) { return b.score - a.score; });
          renderSearchResults(scored.map(function (x) { return x.post; }), resultsEl, baseUrl);
        });
      }, 220);
    });

    // Fechar ao clicar fora
    document.addEventListener('click', function (e) {
      if (!input.contains(e.target) && !resultsEl.contains(e.target)) {
        resultsEl.hidden = true;
      }
    });
  }

  /* ── 5. READING PROGRESS BAR ────────────────────────────────────────── */

  function initReadingProgress() {
    const hook = document.getElementById('reading-progress-hook');
    if (!hook) return;

    const bar = document.createElement('div');
    bar.style.cssText =
      'position:fixed;top:0;left:0;height:3px;width:0%;' +
      'background:var(--green-axiom);z-index:99999;' +
      'transition:width 0.1s linear;pointer-events:none';
    document.body.appendChild(bar);

    window.addEventListener('scroll', function () {
      const scrollTop  = window.scrollY;
      const docHeight  = document.documentElement.scrollHeight - window.innerHeight;
      const progress   = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      bar.style.width  = Math.min(100, progress) + '%';
    }, { passive: true });
  }

  /* ── 6. INIT ────────────────────────────────────────────────────────── */

  function init() {
    initThemeSwitcher();
    initAccordion();
    initToc();
    initSearch();
    initReadingProgress();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

}());
