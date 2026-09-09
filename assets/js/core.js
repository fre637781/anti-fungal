/* Shared logic for the desktop and mobile builds: data loading, priority
   classification and the provenance / reference rendering carried over from the
   original single-file guideline. */
(function (global) {
  'use strict';

  var BASE = document.documentElement.getAttribute('data-base') || './';

  var cache = { meta: null, index: null, org: {}, charts: {} };

  function getJSON(path) {
    return fetch(BASE + path, { cache: 'no-cache' }).then(function (res) {
      if (!res.ok) throw new Error(path + ' → HTTP ' + res.status);
      return res.json();
    });
  }

  function loadMeta() {
    if (!cache.meta) cache.meta = getJSON('data/meta.json');
    return cache.meta;
  }

  function loadIndex() {
    if (!cache.index) cache.index = getJSON('data/index.json').then(function (d) { return d.organisms; });
    return cache.index;
  }

  function loadOrg(id) {
    if (!cache.org[id]) cache.org[id] = getJSON('data/org/' + id + '.json');
    return cache.org[id];
  }

  /* Charts are the bulk of the payload, so they are fetched only when a view
     actually renders them. Organisms without charts resolve to an empty list. */
  function loadCharts(id) {
    if (!cache.charts[id]) {
      cache.charts[id] = getJSON('data/charts/' + id + '.json')
        .then(function (d) { return d.charts || []; })
        .catch(function () { return []; });
    }
    return cache.charts[id];
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }

  /* ---- treatment priority -------------------------------------------------
     Same classification the source file used: the row keeps the guideline's own
     wording, and only the colour band is derived from it. */
  function priorityClass(priority) {
    var p = String(priority || '').toLowerCase();
    if (p.indexOf('avoid') >= 0 || p.indexOf('against') >= 0 ||
        p.indexOf('not recommended') >= 0 || p.indexOf('discourag') >= 0) return 'avoid';
    if (p.indexOf('salvage') >= 0 || p.indexOf('rescue') >= 0) return 'salvage';
    if (p === '1' || p.indexOf('1 ') === 0 || p.indexOf('preferred') >= 0 ||
        p.indexOf('first-line') >= 0 || p.indexOf('first line') >= 0 ||
        p.indexOf('strongly supported') >= 0) return 'preferred';
    return 'alternative';
  }

  var PRIORITY_LABEL = {
    preferred: 'PREFERRED',
    alternative: 'ALTERNATIVE',
    salvage: 'SALVAGE',
    avoid: 'AVOID'
  };

  function priorityLabel(priority) { return PRIORITY_LABEL[priorityClass(priority)]; }

  function phaseClass(phase) {
    var l = String(phase || '').toLowerCase();
    if (l.indexOf('induction') >= 0) return 'induction';
    if (l.indexOf('maintenance') >= 0) return 'maintenance';
    if (l.indexOf('salvage') >= 0) return 'salvage';
    if (l.indexOf('initial') >= 0) return 'initial';
    return '';
  }

  /* ---- references ---------------------------------------------------------- */
  var meta = null;
  function setMeta(m) { meta = m; }

  function referenceForSource(src) {
    if (!meta) return null;
    var low = String(src || '').toLowerCase();
    for (var i = 0; i < meta.reference_database.length; i++) {
      var ref = meta.reference_database[i];
      for (var j = 0; j < ref.match.length; j++) {
        if (low.indexOf(String(ref.match[j]).toLowerCase()) >= 0) return ref;
      }
    }
    return null;
  }

  var LOCATOR_RE = /(sTable\s*\d+[A-Za-z]?|Table\s*[A-Za-z]?\d+[A-Za-z]?|Figures?\s*[A-Za-z]?\d+[A-Za-z]?(?:\s*[–-]\s*[A-Za-z]?\d+[A-Za-z]?)?|Figs?\s*[A-Za-z]?\d+[A-Za-z]?(?:\s*[–-]\s*[A-Za-z]?\d+[A-Za-z]?)?|§\s*[\d.]+|Section\s*[\d.]+)/g;

  /* Renders a source line with an external-link chip after every Figure / Table /
     § locator, each pointing at the article that contains it. */
  function sourceHtml(src) {
    var raw = String(src || '');
    var ref = referenceForSource(raw);
    var safe = esc(raw);
    if (!ref) return '<b>' + safe + '</b>';

    LOCATOR_RE.lastIndex = 0;
    var hasLocator = LOCATOR_RE.test(raw);
    LOCATOR_RE.lastIndex = 0;

    if (hasLocator) {
      safe = safe.replace(LOCATOR_RE, function (m) {
        return m + '<a class="locator-link" href="' + ref.main + '" target="_blank" rel="noopener noreferrer"' +
          ' title="Open the source article containing ' + m + ' (external site)">↗</a>';
      });
    } else {
      safe += '<a class="locator-link" href="' + ref.main + '" target="_blank" rel="noopener noreferrer"' +
        ' title="Open the source article">↗</a>';
    }
    return '<span class="source-locator-wrap"><b>' + safe + '</b></span>';
  }

  function referenceLinksHtml(src) {
    var ref = referenceForSource(src);
    if (!ref) return '';
    var links = [
      { href: ref.main, label: ref.main_label },
      { href: ref.supplement, label: ref.supp_label },
      { href: ref.third, label: ref.third_label }
    ];
    return '<div class="ref-links">' + links.map(function (l) {
      return '<a class="ref-link" href="' + l.href + '" target="_blank" rel="noopener noreferrer">' +
        esc(l.label) + ' ↗</a>';
    }).join('') + '</div>';
  }

  /* The guidelines a page's recommendations actually cite, matched against every
     source / origin cell on the page. */
  function pageReferences(org) {
    if (!meta) return [];
    var hay = [];
    (org.syndromes || []).forEach(function (s) {
      (s.rows || []).forEach(function (r) {
        [7, 9, 11, 12, 13].forEach(function (i) { hay.push(String(r[i] || '')); });
      });
    });
    var joined = hay.join(' || ').toLowerCase();
    return meta.page_reference_db.filter(function (ref) {
      return ref.match.some(function (m) { return joined.indexOf(String(m).toLowerCase()) >= 0; });
    });
  }

  /* ---- desktop / mobile switching ------------------------------------------ */
  var VIEW_KEY = 'fg-view';

  function storedView() {
    try { return localStorage.getItem(VIEW_KEY); } catch (e) { return null; }
  }

  function setView(view) {
    try { localStorage.setItem(VIEW_KEY, view); } catch (e) { /* private mode */ }
  }

  function copyText(text, onDone) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { onDone(true); }, function () { onDone(false); });
    } else {
      onDone(false);
    }
  }

  global.FG = {
    BASE: BASE,
    loadMeta: loadMeta,
    loadIndex: loadIndex,
    loadOrg: loadOrg,
    loadCharts: loadCharts,
    setMeta: setMeta,
    esc: esc,
    priorityClass: priorityClass,
    priorityLabel: priorityLabel,
    phaseClass: phaseClass,
    sourceHtml: sourceHtml,
    referenceLinksHtml: referenceLinksHtml,
    pageReferences: pageReferences,
    storedView: storedView,
    setView: setView,
    copyText: copyText
  };
})(window);
