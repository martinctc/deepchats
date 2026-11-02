/* --------------------------------------------------------------------------
   Deep Chats — theme toggle, live search, and "Surprise me"
   Everything degrades gracefully: without Fuse.js search falls back to
   substring matching, and without JS the search form still submits ?q= to
   the server-rendered home page (which ignores it and shows all cards).
   -------------------------------------------------------------------------- */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ theme */
  var THEME_KEY = 'theme';

  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function applyTheme(theme, persist) {
    document.documentElement.setAttribute('data-theme', theme);
    if (persist) {
      try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* private mode */ }
    }
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      var isDark = theme === 'dark';
      btn.textContent = isDark ? '☀️' : '🌙';
      btn.setAttribute('aria-pressed', String(isDark));
      btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    }
  }

  var themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    applyTheme(currentTheme(), false);
    themeToggle.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark', true);
    });
  }

  /* ----------------------------------------------------------------- search */
  var input = document.getElementById('site-search');
  var grid = document.getElementById('card-grid');
  var statusEl = document.getElementById('search-status');
  var emptyEl = document.getElementById('search-empty');
  var fuse = null;
  var cards = [];
  var items = [];

  function readIndex() {
    var raw = document.getElementById('search-index');
    if (!raw) return [];
    try { return JSON.parse(raw.textContent); } catch (e) { return []; }
  }

  function buildFuse() {
    if (typeof Fuse === 'undefined') return null; // CDN blocked — fallback below
    return new Fuse(items, {
      keys: [
        { name: 'question', weight: 0.5 },
        { name: 'tags', weight: 0.3 },
        { name: 'description', weight: 0.15 },
        { name: 'related', weight: 0.05 }
      ],
      threshold: 0.4,
      ignoreLocation: true,
      includeScore: true
    });
  }

  // Fallback matcher: every whitespace-separated term must appear somewhere
  // in the card's question/description/tags/related questions.
  function substringMatch(query) {
    var terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    return items.filter(function (item) {
      var haystack = [
        item.question || '',
        item.description || '',
        (item.tags || []).join(' '),
        (item.related || []).map(function (r) { return r.question || ''; }).join(' ')
      ].join(' ').toLowerCase();
      return terms.every(function (term) { return haystack.indexOf(term) !== -1; });
    });
  }

  function filterCards(query) {
    if (!grid) return;
    var matchedIds = null; // null = show everything
    if (query) {
      var matches = fuse ? fuse.search(query).map(function (r) { return r.item; })
                         : substringMatch(query);
      matchedIds = {};
      matches.forEach(function (item) { matchedIds[item.id] = true; });
    }

    var visible = 0;
    cards.forEach(function (card) {
      var show = !matchedIds || matchedIds[card.getAttribute('data-id')] === true;
      card.hidden = !show;
      if (show) visible++;
    });

    if (statusEl) {
      statusEl.textContent = query
        ? 'Showing ' + visible + ' of ' + cards.length + ' questions for “' + query + '”'
        : '';
    }
    if (emptyEl) emptyEl.hidden = !(query && visible === 0);
  }

  /* -------------------------------------------------------------- surprise */
  function surprise() {
    var visibleCards = cards.filter(function (c) { return !c.hidden; });
    if (visibleCards.length === 0 && cards.length > 0) visibleCards = cards;
    if (visibleCards.length === 0) {
      // No cards on this page (e.g. About): go home with ?surprise=1
      var home = document.querySelector('.site-title a');
      window.location.href = (home ? home.getAttribute('href') : './') + '?surprise=1';
      return;
    }
    var pick = visibleCards[Math.floor(Math.random() * visibleCards.length)];
    pick.scrollIntoView({ behavior: 'smooth', block: 'center' });
    var card = pick.querySelector('.card');
    if (card) {
      card.classList.remove('flash');
      void card.offsetWidth; // restart animation
      card.classList.add('flash');
      card.addEventListener('animationend', function handler() {
        card.classList.remove('flash');
        card.removeEventListener('animationend', handler);
      });
    }
  }

  var surpriseBtn = document.getElementById('surprise-btn');
  if (surpriseBtn) surpriseBtn.addEventListener('click', surprise);

  /* ------------------------------------------------------------------ wire */
  document.addEventListener('DOMContentLoaded', function () {
    items = readIndex();
    cards = grid ? Array.prototype.slice.call(grid.querySelectorAll('.search-card')) : [];
    fuse = items.length ? buildFuse() : null;

    if (input && grid) {
      // Live-filter as the user types on pages that have cards.
      input.addEventListener('input', function () { filterCards(input.value.trim()); });

      // Keep the URL shareable (?q=...) without a page reload.
      input.form && input.form.addEventListener('submit', function (e) {
        e.preventDefault();
        var q = input.value.trim();
        try {
          history.replaceState(null, '', q ? '?q=' + encodeURIComponent(q) : location.pathname);
        } catch (err) { /* file:// or old browsers */ }
        filterCards(q);
      });

      // Apply ?q= from the URL (used by related-question links and searches
      // submitted from pages that have no cards of their own).
      var params = new URLSearchParams(location.search);
      var q = params.get('q');
      if (q) {
        input.value = q;
        filterCards(q);
      }
      if (params.get('surprise')) surprise();
    } else if (input) {
      // No cards here (About/Tags): submitting the form navigates home
      // with ?q=... which the home page then applies on load.
      input.form && input.form.addEventListener('submit', function (e) {
        e.preventDefault();
        var q = input.value.trim();
        window.location.href = input.form.getAttribute('action') + (q ? '?q=' + encodeURIComponent(q) : '');
      });
    }
  });
})();
