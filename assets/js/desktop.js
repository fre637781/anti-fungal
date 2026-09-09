/* Desktop renderer: organism grid + full-width treatment tables. */
(function () {
  'use strict';

  var esc = FG.esc;
  var state = { meta: null, index: [], group: 'all', evidence: 'all', query: '', directOnly: false, org: null };

  var el = {
    groups: document.getElementById('groups'),
    empty: document.getElementById('empty'),
    filters: document.getElementById('filters'),
    stats: document.getElementById('stats'),
    kicker: document.getElementById('kicker'),
    search: document.getElementById('search'),
    bibliography: document.getElementById('bibliography'),
    modal: document.getElementById('modal'),
    head: document.getElementById('sheetHead'),
    body: document.getElementById('mBody'),
    name: document.getElementById('mName'),
    alias: document.getElementById('mAlias'),
    groupLabel: document.getElementById('mGroup'),
    viewer: document.getElementById('svgviewer'),
    viewerInner: document.getElementById('svgviewerinner')
  };

  /* ---- landing ---------------------------------------------------------- */
  function renderChrome() {
    var s = state.meta.stats;
    el.kicker.textContent = state.meta.subtitle;
    el.stats.innerHTML =
      '<div class="stat"><b>' + s.organisms + '</b> organism pages</div>' +
      '<div class="stat"><b>' + s.groups + '</b> categories</div>' +
      '<div class="stat"><b>' + s.rows + '</b> treatment rows</div>' +
      '<div class="stat"><b>' + s.charts + '</b> flowcharts</div>';

    el.filters.innerHTML = '<button class="filter active" data-filter="all">全部</button>' +
      state.meta.groups.map(function (g) {
        return '<button class="filter" data-filter="' + esc(g.name) + '">' + esc(g.name) + '</button>';
      }).join('');

    el.bibliography.innerHTML = '<h2>Reference database</h2>' +
      '<p>按鈕依實際資源性質標示；不把 PubMed 誤標為 full text。若 supplement 沒有穩定獨立網址，會顯示 <b>Supplement via article page</b>。</p>' +
      state.meta.bibliography.map(function (b) {
        return '<div class="bib-item" id="ref-' + esc(b.key) + '"><b>' + esc(b.short) + '</b><br>' + esc(b.title) +
          '<div class="ref-db-buttons">' +
          b.links.map(function (l) {
            return '<a class="ref-db-btn ' + esc(l.kind) + '" href="' + esc(l.href) + '" target="_blank" rel="noopener noreferrer">' +
              esc(l.label) + ' ↗</a>';
          }).join('') +
          (b.citation ? '<button class="ref-db-btn copy-cite" type="button" data-citation="' + esc(b.citation) + '">Copy Vancouver citation</button>' : '') +
          '</div></div>';
      }).join('');
  }

  function renderLanding() {
    el.groups.innerHTML = state.meta.groups.map(function (g) {
      var orgs = state.index.filter(function (o) { return o.group === g.name; });
      if (!orgs.length) return '';
      return '<section class="group-block" data-group="' + esc(g.name) + '">' +
        '<div class="group-title"><span class="bar" style="background:' + esc(g.color) + '"></span>' +
        '<div><h2>' + esc(g.name) + '</h2><p>' + esc(g.desc) + '</p></div></div>' +
        '<div class="card-grid">' + orgs.map(function (o) {
          return '<button class="organism-card" data-open="' + esc(o.id) + '" data-evidence="' + esc(o.evidence) + '">' +
            '<span class="dot" style="background:' + esc(g.color) + '"></span>' +
            '<span><b>' + esc(o.name) + '</b><small>' + esc(o.aliases || o.evidence_scope || '') + '</small></span>' +
            '<span class="arrow">›</span></button>';
        }).join('') + '</div></section>';
    }).join('');
    applyFilters();
  }

  function applyFilters() {
    var q = state.query.trim().toLowerCase();
    var byId = {};
    state.index.forEach(function (o) { byId[o.id] = o; });
    var visible = 0;

    Array.prototype.forEach.call(el.groups.querySelectorAll('.group-block'), function (block) {
      var shown = 0;
      Array.prototype.forEach.call(block.querySelectorAll('.organism-card'), function (card) {
        var o = byId[card.dataset.open];
        var ok = (state.group === 'all' || o.group === state.group) &&
          (state.evidence === 'all' || o.evidence === state.evidence) &&
          (!q || o.q.indexOf(q) >= 0 || o.name.toLowerCase().indexOf(q) >= 0);
        card.style.display = ok ? 'grid' : 'none';
        if (ok) { shown++; visible++; }
      });
      block.style.display = shown ? 'block' : 'none';
    });
    el.empty.style.display = visible ? 'none' : 'block';
  }

  /* ---- detail sheet ------------------------------------------------------ */
  function rowVisible(r) {
    return !state.directOnly || String(r[10] || '').toUpperCase().indexOf('DIRECT') === 0;
  }

  function sourcePanel(o) {
    var rows = [['Evidence scope', o.evidence_scope]];
    if (o.taxonomy_source) rows.push(['Taxonomy source', o.taxonomy_source]);
    if (o.source_note) rows.push(['Source note', o.source_note]);
    if (o.normalization_note) rows.push(['Dose notation', o.normalization_note]);
    if (o.overview) rows.push(['Overview', o.overview]);
    if (o.notes) rows.push(['Notes', o.notes]);
    if (o.audit_summary) {
      rows.push(['Audit scope', o.audit_summary.scope + ' · rounds ' + o.audit_summary.rounds]);
      rows.push(['Population scope', o.audit_summary.population_scope]);
    }
    return '<div class="source-panel"><b>Provenance / evidence scope</b><div class="source-meta">' +
      rows.map(function (r) { return '<div>' + esc(r[0]) + '</div><div>' + esc(r[1] || '') + '</div>'; }).join('') +
      '</div></div>';
  }

  function legendHtml() {
    return '<div class="priority-legend">' +
      '<span class="priority-pill preferred">PREFERRED</span>' +
      '<span class="priority-pill alternative">ALTERNATIVE</span>' +
      '<span class="priority-pill salvage">SALVAGE</span>' +
      '<span class="priority-pill avoid">AVOID</span>' +
      '<span class="legend-note">整列網底直接代表建議層級：綠=Preferred、黃=Alternative、藍=Salvage、紅=Avoid。QoE / evidence grade 不用第二套網底，以免和 treatment priority 混淆；仍以 Recommendation / QoE 欄文字為準。</span></div>';
  }

  function comparisonHtml(o) {
    var g = o.guideline_comparison;
    if (!g) return '';
    return '<div class="comparison-box"><h3>' + esc(g.title) + '</h3>' + legendHtml() +
      '<div class="table-wrap"><table><thead><tr><th>Guideline</th><th>Recommendation</th><th>Locator</th></tr></thead><tbody>' +
      g.rows.map(function (r) {
        return '<tr><td><b>' + esc(r[0]) + '</b></td><td>' + esc(r[1]) + '</td><td>' + FG.sourceHtml(r[2]) + '</td></tr>';
      }).join('') + '</tbody></table></div></div>';
  }

  function syndromeHtml(s) {
    var phases = [];
    s.rows.forEach(function (r) { if (phases.indexOf(r[1]) < 0) phases.push(r[1]); });
    var rows = s.rows.filter(rowVisible);

    var head = ['Priority', 'Phase', 'Drug / regimen', 'Dose', 'Duration', 'Clinical setting', 'Recommendation / QoE'];
    var auditHead = ['Evidence origin', 'Recommendation origin', 'Dose origin', 'Duration origin', 'Source / exact locator'];

    return '<section class="syndrome"><h3>' + esc(s.title) + '</h3>' +
      '<div class="phasebar">' + phases.map(function (p) {
        return '<span class="phasechip ' + FG.phaseClass(p) + '">' + esc(p) + '</span>';
      }).join('') + '</div>' + legendHtml() +
      '<div class="table-wrap"><table><thead><tr>' +
        head.map(function (h) { return '<th>' + h + '</th>'; }).join('') +
        auditHead.map(function (h) { return '<th class="audit-col">' + h + '</th>'; }).join('') +
        '<th>Step-down / maintenance / salvage</th><th class="audit-col">Evidence / note</th>' +
      '</tr></thead><tbody>' +
      (rows.length ? rows.map(function (r) {
        return '<tr class="row-' + FG.priorityClass(r[0]) + '">' +
          '<td class="priority"><span class="priority-pill ' + FG.priorityClass(r[0]) + '">' + FG.priorityLabel(r[0]) + '</span>' +
            '<div style="margin-top:4px;font-size:10px;opacity:.75">' + esc(r[0]) + '</div></td>' +
          '<td><b>' + esc(r[1]) + '</b></td><td><b>' + esc(r[2]) + '</b></td>' +
          '<td class="dosecell">' + esc(r[3]) + '</td><td class="durationcell">' + esc(r[4]) + '</td>' +
          '<td>' + esc(r[5]) + '</td><td>' + esc(r[6]) + '</td>' +
          '<td class="audit-col"><span class="origin-badge">' + esc(r[10] || '') + '</span></td>' +
          '<td class="audit-col">' + esc(r[11] || '') + '</td>' +
          '<td class="audit-col">' + esc(r[12] || '') + '</td>' +
          '<td class="audit-col">' + esc(r[13] || '') + '</td>' +
          '<td class="audit-col">' + FG.sourceHtml(r[7]) + FG.referenceLinksHtml(r[7]) + '</td>' +
          '<td class="seqcell">' + esc(r[8]) + '</td>' +
          '<td class="audit-col">' + esc(r[9]) + '</td></tr>';
      }).join('') : '<tr><td colspan="14" style="color:#66716b">此情境沒有 DIRECT 層級的 row；關閉「Direct guideline evidence only」即可看到 extrapolated 建議。</td></tr>') +
      '</tbody></table></div></section>';
  }

  function pageReferenceHtml(o) {
    var refs = FG.pageReferences(o);
    if (!refs.length) return '';
    return '<section class="page-references"><div class="page-ref-title">References used on this page</div>' +
      '<div class="page-ref-sub">以下僅列出本頁 treatment recommendations 實際使用的核心 guideline。逐一 treatment row 的 Figure / Table / § exact locator 可在 Audit view 的 Source 欄查看。</div>' +
      '<ol class="page-ref-list">' + refs.map(function (ref) {
        return '<li><b>' + esc(ref.short) + '</b><br><span>' + esc(ref.title) + '</span><br>' +
          '<span class="page-ref-doi">doi: ' + esc(ref.doi) + '</span>' +
          '<a class="page-ref-link" href="' + esc(ref.url) + '" target="_blank" rel="noopener noreferrer">開啟文獻 ↗</a></li>';
      }).join('') + '</ol></section>';
  }

  function chartsHtml(charts) {
    if (!charts.length) return '';
    return '<section class="flowchart-section"><h3>Treatment flowcharts / algorithms</h3>' +
      '<p class="fc-note">每張圖均標示其 provenance。若原 guideline 有正式 treatment figure，標示為 original-source reconstruction；否則明確標示為 guideline-derived summary。</p>' +
      '<div class="flow-priority-legend"><span class="flow-key preferred">Preferred</span>' +
      '<span class="flow-key alternative">Alternative</span><span class="flow-key salvage">Salvage</span>' +
      '<span class="flow-key avoid">Avoid</span>' +
      '<span class="flow-key-note">流程圖節點底色與治療表格的 row 網底使用同一組顏色。</span></div>' +
      charts.map(function (fc, i) {
        return '<div class="flowchart-card">' +
          '<div class="flowchart-svg-wrap"><div class="flowchart-svg">' + fc.svg + '</div></div>' +
          '<div class="flowchart-caption"><span><b>' + esc(fc.kind) + '</b><br>' + esc(fc.title) +
            '<div class="chart-source"><b>Source:</b> ' + FG.sourceHtml(fc.source) + FG.referenceLinksHtml(fc.source) + '</div>' +
            '<div class="chart-disclaimer">' + esc(fc.disclaimer) + '</div></span>' +
          '<button class="fc-open" data-chart="' + i + '">全螢幕放大</button></div></div>';
      }).join('') + '</section>';
  }

  var currentCharts = [];

  function renderOrg(o, charts) {
    state.org = o;
    currentCharts = charts;
    el.name.textContent = o.name;
    el.alias.textContent = o.aliases || '';
    el.groupLabel.textContent = o.group;
    el.head.style.background = 'linear-gradient(145deg,' + o.groupColor + ',#1d2923)';

    el.body.innerHTML =
      '<div>' + (o.tags || []).map(function (t) { return '<span class="badge">' + esc(t) + '</span>'; }).join('') + '</div>' +
      sourcePanel(o) +
      '<div class="view-controls no-print">' +
        '<button class="view-btn' + (document.body.classList.contains('clinical-view') ? ' active' : '') + '" data-view="clinical">Clinical view</button>' +
        '<button class="view-btn' + (document.body.classList.contains('clinical-view') ? '' : ' active') + '" data-view="audit">Audit view</button>' +
      '</div>' +
      '<div class="audit-status"><b>Audit status:</b> evidence-origin classified. DIRECT-only mode hides extrapolated and label-derived rows.</div>' +
      '<div class="audit-controls no-print"><button class="audit-toggle' + (state.directOnly ? ' active' : '') + '" id="directOnlyBtn">Direct guideline evidence only</button></div>' +
      comparisonHtml(o) + chartsHtml(charts) +
      o.syndromes.map(syndromeHtml).join('') +
      pageReferenceHtml(o);
  }

  function openOrg(id) {
    if (state.org && state.org.id === id) return;
    el.body.innerHTML = '<div class="loading">載入中…</div>';
    el.modal.classList.add('open');
    el.modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    Promise.all([FG.loadOrg(id), FG.loadCharts(id)]).then(function (res) {
      if (location.hash.slice(1) !== id) return;
      renderOrg(res[0], res[1]);
      el.modal.scrollTop = 0;
    }).catch(function (err) {
      el.body.innerHTML = '<div class="loading">載入失敗：' + esc(err.message) + '</div>';
    });
  }

  function closeOrg() {
    el.modal.classList.remove('open');
    el.modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    state.org = null;
    currentCharts = [];
  }

  /* The hash is the single source of truth, so the browser back button closes
     the sheet instead of leaving the site. */
  function route() {
    var id = location.hash.slice(1);
    if (id && state.index.some(function (o) { return o.id === id; })) openOrg(id);
    else closeOrg();
  }

  /* ---- events ----------------------------------------------------------- */
  el.search.addEventListener('input', function () { state.query = this.value; applyFilters(); });

  el.filters.addEventListener('click', function (e) {
    var btn = e.target.closest('.filter');
    if (!btn) return;
    Array.prototype.forEach.call(el.filters.querySelectorAll('.filter'), function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    state.group = btn.dataset.filter;
    applyFilters();
  });

  document.getElementById('evidenceFilter').addEventListener('click', function (e) {
    var btn = e.target.closest('[data-evidence-filter]');
    if (!btn) return;
    Array.prototype.forEach.call(this.querySelectorAll('button'), function (b) { b.classList.toggle('active', b === btn); });
    state.evidence = btn.dataset.evidenceFilter;
    applyFilters();
  });

  el.groups.addEventListener('click', function (e) {
    var card = e.target.closest('[data-open]');
    if (card) location.hash = card.dataset.open;
  });

  document.getElementById('close').addEventListener('click', function () {
    if (history.length > 1) history.back(); else location.hash = '';
  });

  el.body.addEventListener('click', function (e) {
    var view = e.target.closest('[data-view]');
    if (view) {
      document.body.classList.toggle('clinical-view', view.dataset.view === 'clinical');
      Array.prototype.forEach.call(el.body.querySelectorAll('[data-view]'), function (b) {
        b.classList.toggle('active', b === view);
      });
      return;
    }
    if (e.target.closest('#directOnlyBtn')) {
      state.directOnly = !state.directOnly;
      renderOrg(state.org, currentCharts);
      return;
    }
    var chart = e.target.closest('[data-chart]');
    if (chart) {
      var fc = currentCharts[Number(chart.dataset.chart)];
      el.viewerInner.innerHTML = fc ? fc.svg : '';
      el.viewer.classList.add('open');
    }
  });

  document.getElementById('viewerClose').addEventListener('click', closeViewer);
  el.viewer.addEventListener('click', function (e) { if (e.target === el.viewer) closeViewer(); });

  function closeViewer() {
    el.viewer.classList.remove('open');
    el.viewerInner.innerHTML = '';
  }

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (el.viewer.classList.contains('open')) closeViewer();
    else if (el.modal.classList.contains('open')) { if (history.length > 1) history.back(); else location.hash = ''; }
  });

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.copy-cite');
    if (!btn) return;
    FG.copyText(btn.dataset.citation || '', function (ok) {
      var old = btn.textContent;
      btn.textContent = ok ? 'Copied' : 'Copy failed';
      setTimeout(function () { btn.textContent = old; }, 1200);
    });
  });

  document.getElementById('toMobile').addEventListener('click', function () { FG.setView('mobile'); });

  window.addEventListener('hashchange', route);

  /* ---- boot ------------------------------------------------------------- */
  Promise.all([FG.loadMeta(), FG.loadIndex()]).then(function (res) {
    state.meta = res[0];
    state.index = res[1];
    FG.setMeta(state.meta);
    renderChrome();
    renderLanding();
    route();
  }).catch(function (err) {
    el.groups.innerHTML = '<div class="loading">資料載入失敗：' + esc(err.message) +
      '<br><small>若是在本機開啟檔案，請改用 <code>python3 -m http.server</code> 之類的本機伺服器。</small></div>';
  });
})();
