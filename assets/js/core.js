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

  /* ---- hash routing --------------------------------------------------------
     "#g7o0" opens an organism; "#g7o0:6" also jumps to its 7th syndrome, which
     is how the landing page's syndrome chips link straight to a condition. */
  function parseHash() {
    var raw = location.hash.slice(1);
    if (!raw) return { id: '', syn: null };
    var bits = raw.split(':');
    var syn = bits.length > 1 ? parseInt(bits[1], 10) : NaN;
    return { id: bits[0], syn: isNaN(syn) ? null : syn };
  }

  function hashFor(id, syn) {
    return '#' + id + (syn == null ? '' : ':' + syn);
  }

  /* ---- genus hubs ----------------------------------------------------------
     Guideline figures are written per syndrome, so a species page that only
     inherits genus-level recommendations should point at the hub that carries
     them. */
  function hubBannerHtml(org, index) {
    if (!org.hub) return '';
    var hub = index.filter(function (o) { return o.id === org.hub; })[0];
    if (!hub) return '';
    var extrapolated = (org.evidence_availability || '') === 'extrapolation';
    return '<div class="hub-banner">' +
      '<div class="hb-title">' + (extrapolated
        ? '此頁沿用 genus-level 建議（extrapolation）'
        : '治療依感染情境（syndrome）分層') + '</div>' +
      '<p>' + (extrapolated
        ? '本頁的治療列是從屬層級建議延伸而來，不代表存在獨立的 species-level 證據。實際治療決策請先選感染情境，species 主要影響感受性判讀與降階選擇。'
        : '完整的感染情境清單與各情境的治療路徑集中在下列頁面。') + '</p>' +
      '<a class="hb-link" href="' + hashFor(hub.id, null) + '">' + esc(hub.name) + ' — 依 syndrome 查詢 →</a>' +
      '</div>';
  }

  /* ---- desktop / mobile switching ------------------------------------------ */
  var VIEW_KEY = 'fg-view';

  function storedView() {
    try { return localStorage.getItem(VIEW_KEY); } catch (e) { return null; }
  }

  function setView(view) {
    try { localStorage.setItem(VIEW_KEY, view); } catch (e) { /* private mode */ }
  }

  /* URL of the same organism in the other build — the hash carries the reader
     across, so switching never dumps them back on the landing page. */
  function switchUrl(target) {
    var base = target === 'mobile' ? 'm/index.html' : '../index.html';
    return base + '?view=' + target + location.hash;
  }

  /* Wires every [data-switch-view] control on the page and keeps their hrefs in
     step with the current organism. They stay real links, so long-press and
     open-in-new-tab still behave. */
  function installViewSwitch() {
    var nodes = [].slice.call(document.querySelectorAll('[data-switch-view]'));
    if (!nodes.length) return;

    function refresh() {
      nodes.forEach(function (a) { a.href = switchUrl(a.getAttribute('data-switch-view')); });
    }
    nodes.forEach(function (a) {
      a.addEventListener('click', function () { setView(a.getAttribute('data-switch-view')); });
    });
    window.addEventListener('hashchange', refresh);
    refresh();
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
    parseHash: parseHash,
    hashFor: hashFor,
    hubBannerHtml: hubBannerHtml,
    priorityClass: priorityClass,
    priorityLabel: priorityLabel,
    phaseClass: phaseClass,
    sourceHtml: sourceHtml,
    referenceLinksHtml: referenceLinksHtml,
    pageReferences: pageReferences,
    storedView: storedView,
    setView: setView,
    switchUrl: switchUrl,
    installViewSwitch: installViewSwitch,
    copyText: copyText
  };
})(window);
