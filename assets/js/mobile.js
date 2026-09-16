/* Mobile renderer: list screen + detail screen, treatment rows as cards,
   charts fetched only when their section is opened. */
(function () {
  'use strict';

  var esc = FG.esc;
  var state = {
    meta: null, index: [], group: 'all', evidence: 'all', query: '',
    org: null, charts: null, chartCount: 0, chartsLoading: false, directOnly: false
  };

  var el = {
    list: document.getElementById('list'),
    empty: document.getElementById('empty'),
    groupChips: document.getElementById('groupChips'),
    evidenceChips: document.getElementById('evidenceChips'),
    metrics: document.getElementById('metrics'),
    kicker: document.getElementById('kicker'),
    search: document.getElementById('search'),
    bibSect: document.getElementById('bibSect'),
    buildinfo: document.getElementById('buildinfo'),
    listScreen: document.getElementById('listScreen'),
    detailScreen: document.getElementById('detailScreen'),
    detailBar: document.getElementById('detailbar'),
    detailBody: document.getElementById('detailBody'),
    dName: document.getElementById('dName'),
    dAlias: document.getElementById('dAlias'),
    dGroup: document.getElementById('dGroup'),
    viewer: document.getElementById('viewer'),
    vstage: document.getElementById('vstage'),
    vinner: document.getElementById('vinner'),
    viewerTitle: document.getElementById('viewerTitle')
  };

  /* ---- list screen ------------------------------------------------------- */
  function renderChrome() {
    var s = state.meta.stats;
    el.kicker.textContent = state.meta.version + ' · 手機版';
    el.metrics.innerHTML =
      '<span>' + s.organisms + ' 菌種</span><span>' + s.groups + ' 分類</span>' +
      '<span>' + s.rows + ' 治療建議</span><span>' + s.charts + ' 流程圖</span>';
    el.buildinfo.textContent = state.meta.title + ' ' + state.meta.version;

    el.groupChips.innerHTML = '<button class="chip active" data-group="all">全部</button>' +
      state.meta.groups.map(function (g) {
        return '<button class="chip" data-group="' + esc(g.name) + '">' + esc(g.name) + '</button>';
      }).join('');

    el.bibSect.innerHTML = '<summary>Reference database<span class="n">' + state.meta.bibliography.length + '</span></summary>' +
      '<div class="sect-body">' + state.meta.bibliography.map(function (b) {
        return '<div class="bib-item"><b>' + esc(b.short) + '</b><br>' + esc(b.title) +
          '<div class="ref-db-buttons">' + b.links.map(function (l) {
            return '<a class="ref-db-btn ' + esc(l.kind) + '" href="' + esc(l.href) + '" target="_blank" rel="noopener noreferrer">' +
              esc(l.label) + ' \u2197</a>';
          }).join('') +
          (b.citation ? '<button class="ref-db-btn copy-cite" type="button" data-citation="' + esc(b.citation) + '">\u8907\u88fd\u5f15\u7528\u683c\u5f0f</button>' : '') +
          '</div></div>';
      }).join('') + '</div>';
  }

  /* Guidelines are written per syndrome; give that route equal standing with
     the species list instead of making the reader guess a species first. */
  function syndromeEntryHtml(group) {
    if (state.query.trim() || state.evidence !== 'all') return '';
    var hubId = (state.meta.hubs || {})[group.name];
    if (!hubId) return '';
    var hub = state.index.filter(function (o) { return o.id === hubId; })[0];
    if (!hub || !hub.families || hub.families.length < 2) return '';
    var many = hub.families.length > 6;
    return '<div class="syndrome-entry">' +
      '<div class="se-head">依感染情境查詢（syndrome）' +
      '<span>治療路徑以感染部位／情境分層；菌種主要影響感受性判讀</span></div>' +
      '<div class="se-chips' + (many ? ' collapsed' : '') + '">' + hub.families.map(function (f) {
        return '<button class="se-chip" data-syn="' + esc(hub.id) + ':' + f.index + '">' +
          esc(f.label) + (f.variants > 1 ? '<i>' + f.variants + '</i>' : '') + '</button>';
      }).join('') + '</div>' +
      (many ? '<button class="se-more" data-se-more>顯示全部 ' + hub.families.length + ' 項 ▾</button>' : '') +
      '</div>';
  }

  function renderList() {
    var q = state.query.trim().toLowerCase();
    var html = '', visible = 0;

    state.meta.groups.forEach(function (g) {
      if (state.group !== 'all' && state.group !== g.name) return;
      var orgs = state.index.filter(function (o) {
        return o.group === g.name &&
          (state.evidence === 'all' || o.evidence === state.evidence) &&
          (!q || o.q.indexOf(q) >= 0 || o.name.toLowerCase().indexOf(q) >= 0);
      });
      if (!orgs.length) return;
      visible += orgs.length;

      html += '<div class="grouphead"><span class="bar" style="background:' + esc(g.color) + '"></span>' +
        '<h2>' + esc(g.name) + '</h2><span class="count">' + orgs.length + '</span></div>' +
        syndromeEntryHtml(g) +
        '<div class="orglist">' + orgs.map(function (o) {
          return '<button class="orgrow" data-open="' + esc(o.id) + '">' +
            '<span class="dot" style="background:' + esc(g.color) + '"></span>' +
            '<span><b>' + esc(o.name) + '</b>' +
            (o.aliases ? '<small>' + esc(o.aliases) + '</small>' : '') +
            '<span class="meta"><i>' + o.rows + ' 治療建議</i>' +
            (o.charts ? '<i>' + o.charts + ' 流程圖</i>' : '') +
            '<i>' + (o.evidence === 'direct' ? 'Direct evidence' : 'Extrapolation') + '</i></span></span>' +
            '<span class="arrow">›</span></button>';
        }).join('') + '</div>';
    });

    el.list.innerHTML = html;
    el.empty.style.display = visible ? 'none' : 'block';
  }

  /* ---- detail screen ----------------------------------------------------- */
  function rowVisible(r) {
    return !state.directOnly || String(r[10] || '').toUpperCase().indexOf('DIRECT') === 0;
  }

  function kv(label, value, cls) {
    if (!value) return '';
    return '<dt>' + esc(label) + '</dt><dd' + (cls ? ' class="' + cls + '"' : '') + '>' + esc(value) + '</dd>';
  }

  function treatmentCard(r) {
    var cls = FG.priorityClass(r[0]);
    return '<div class="tcard ' + cls + '">' +
      '<div class="top"><span class="priority-pill ' + cls + '">' + FG.priorityLabel(r[0]) + '</span>' +
        '<span class="phasechip ' + FG.phaseClass(r[1]) + '">' + esc(r[1]) + '</span></div>' +
      '<div class="drug">' + esc(r[2]) + '</div>' +
      '<dl class="kv">' +
        kv('劑量', r[3], 'dose') +
        kv('療程', r[4]) +
        kv('臨床情境', r[5]) +
        kv('推薦 / QoE', r[6]) +
        kv('後續治療', r[8]) +
      '</dl>' +
      '<div class="raw">來源分級用語：' + esc(r[0]) + '</div>' +
      '<details><summary>Provenance / 來源</summary><div class="body">' +
        '<div class="row"><b>Evidence origin</b><span class="origin-badge">' + esc(r[10] || '') + '</span></div>' +
        (r[11] ? '<div class="row"><b>Recommendation origin</b>' + esc(r[11]) + '</div>' : '') +
        (r[12] ? '<div class="row"><b>Dose origin</b>' + esc(r[12]) + '</div>' : '') +
        (r[13] ? '<div class="row"><b>Duration origin</b>' + esc(r[13]) + '</div>' : '') +
        '<div class="row"><b>Source / exact locator</b>' + FG.sourceHtml(r[7]) + FG.referenceLinksHtml(r[7]) + '</div>' +
        (r[9] ? '<div class="row"><b>Evidence / note</b>' + esc(r[9]) + '</div>' : '') +
      '</div></details></div>';
  }

  function syndromeSection(s, openFirst, idx) {
    var rows = s.rows.filter(rowVisible);
    var phases = [];
    s.rows.forEach(function (r) { if (phases.indexOf(r[1]) < 0) phases.push(r[1]); });
    return '<details class="sect" id="syn-' + idx + '"' + (openFirst ? ' open' : '') + '>' +
      '<summary>' + esc(s.title) + '<span class="n">' + rows.length + '</span></summary>' +
      '<div class="sect-body">' +
        '<div class="phasebar">' + phases.map(function (p) {
          return '<span class="phasechip ' + FG.phaseClass(p) + '">' + esc(p) + '</span>';
        }).join('') + '</div>' +
        (rows.length ? rows.map(treatmentCard).join('')
          : '<p style="color:#66716b;font-size:13px">此情境沒有 DIRECT 層級的建議；關閉「僅 Direct evidence」即可看到 extrapolated 建議。</p>') +
      '</div></details>';
  }

  function infoSection(o) {
    var rows = [['Evidence scope', o.evidence_scope]];
    if (o.overview) rows.push(['Overview', o.overview]);
    if (o.taxonomy_source) rows.push(['Taxonomy source', o.taxonomy_source]);
    if (o.source_note) rows.push(['Source note', o.source_note]);
    if (o.normalization_note) rows.push(['Dose notation', o.normalization_note]);
    if (o.notes) rows.push(['Notes', o.notes]);
    if (o.audit_summary) {
      rows.push(['Audit scope', o.audit_summary.scope]);
      rows.push(['Population scope', o.audit_summary.population_scope]);
    }
    return '<details class="sect"><summary>Provenance / evidence scope</summary><div class="sect-body">' +
      '<div class="infogrid">' + rows.map(function (r) {
        return '<div><div class="k">' + esc(r[0]) + '</div>' + esc(r[1] || '') + '</div>';
      }).join('') + '</div></div></details>';
  }

  function comparisonSection(o) {
    var g = o.guideline_comparison;
    if (!g) return '';
    return '<details class="sect"><summary>' + esc(g.title) + '<span class="n">' + g.rows.length + '</span></summary>' +
      '<div class="sect-body"><div class="infogrid">' + g.rows.map(function (r) {
        return '<div><div class="k">' + esc(r[0]) + '</div>' + esc(r[1]) +
          '<div style="margin-top:5px;font-size:11.5px">' + FG.sourceHtml(r[2]) + '</div></div>';
      }).join('') + '</div></div></details>';
  }

  function chartsSection(count) {
    if (!count) return '';
    return '<details class="sect" id="chartSect"><summary>Treatment flowcharts<span class="n">' + count + '</span></summary>' +
      '<div class="sect-body" id="chartBody"><div class="loading">點開以載入流程圖…</div></div></details>';
  }

  function renderCharts(charts) {
    var body = document.getElementById('chartBody');
    if (!body) return;
    body.innerHTML =
      '<div class="flow-priority-legend" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">' +
        '<span class="priority-pill preferred">PREFERRED</span><span class="priority-pill alternative">ALTERNATIVE</span>' +
        '<span class="priority-pill salvage">SALVAGE</span><span class="priority-pill avoid">AVOID</span></div>' +
      charts.map(function (fc, i) {
        return '<div class="chartitem">' +
          '<button class="chartthumb" data-chart="' + i + '" aria-label="放大：' + esc(fc.title) + '">' + fc.svg + '</button>' +
          '<div class="chartmeta"><span class="kind">' + esc(fc.title) + '</span>' +
            '<div class="chart-source"><b>Source:</b> ' + FG.sourceHtml(fc.source) + FG.referenceLinksHtml(fc.source) + '</div>' +
            '<div class="chart-disclaimer">' + esc(fc.disclaimer) + '</div></div></div>';
      }).join('');
  }

  function pageReferenceSection(o) {
    var refs = FG.pageReferences(o);
    if (!refs.length) return '';
    return '<details class="sect"><summary>References used on this page<span class="n">' + refs.length + '</span></summary>' +
      '<div class="sect-body"><div class="page-ref-sub">以下僅列出本頁 treatment recommendations 實際使用的核心 guideline；逐列 exact locator 請在 Audit view 展開每張卡片的 Provenance。</div>' +
      '<ol class="page-ref-list">' + refs.map(function (ref) {
        return '<li><b>' + esc(ref.short) + '</b><br>' + esc(ref.title) + '<br>' +
          '<span class="page-ref-doi">doi: ' + esc(ref.doi) + '</span>' +
          '<a class="page-ref-link" href="' + esc(ref.url) + '" target="_blank" rel="noopener noreferrer">開啟 ↗</a></li>';
      }).join('') + '</ol></div></details>';
  }

  function renderOrg(o) {
    state.org = o;
    el.dName.textContent = o.name;
    el.dAlias.textContent = o.aliases || '';
    el.dGroup.textContent = o.group;
    el.detailBar.style.background = 'linear-gradient(150deg,' + o.groupColor + ',#1d2923)';

    el.detailBody.innerHTML =
      '<div style="margin:12px 0 0">' + (o.tags || []).map(function (t) {
        return '<span class="badge">' + esc(t) + '</span>';
      }).join('') + '</div>' +
      '<div class="segmented">' +
        '<button data-view="clinical"' + (document.body.classList.contains('clinical-view') ? ' class="active"' : '') + '>Clinical view</button>' +
        '<button data-view="audit"' + (document.body.classList.contains('clinical-view') ? '' : ' class="active"') + '>Audit view</button>' +
      '</div>' +
      '<div class="segmented"><button data-direct="1"' + (state.directOnly ? ' class="active"' : '') + '>僅 Direct guideline evidence</button></div>' +
      FG.hubBannerHtml(o, state.index) +
      infoSection(o) + comparisonSection(o) + chartsSection(state.chartCount) +
      o.syndromes.map(function (s, i) {
        return syndromeSection(s, i === 0 && o.syndromes.length <= 6, i);
      }).join('') +
      pageReferenceSection(o) +
      '<p class="footer" style="padding-left:0;padding-right:0">資料僅供醫療專業人員參考，不能取代臨床判斷與原始 guideline。</p>';

    // Re-attach the charts once their section is expanded.
    var sect = document.getElementById('chartSect');
    if (sect) {
      sect.addEventListener('toggle', function () {
        if (!sect.open || state.charts || state.chartsLoading) {
          if (sect.open && state.charts) renderCharts(state.charts);
          return;
        }
        state.chartsLoading = true;
        FG.loadCharts(o.id).then(function (charts) {
          state.charts = charts;
          state.chartsLoading = false;
          if (state.org && state.org.id === o.id) renderCharts(charts);
        });
      });
    }
  }

  function revealSyndrome(n) {
    if (n == null) return;
    var el = document.getElementById('syn-' + n);
    if (!el) return;
    el.open = true;
    el.scrollIntoView({ block: 'start' });
  }

  function showDetail(id, syn) {
    el.listScreen.hidden = true;
    el.detailScreen.hidden = false;
    el.detailBody.innerHTML = '<div class="loading">載入中…</div>';
    el.dName.textContent = '';
    el.dAlias.textContent = '';
    el.dGroup.textContent = '';
    window.scrollTo(0, 0);

    var summary = state.index.filter(function (o) { return o.id === id; })[0];
    if (summary) {
      el.dName.textContent = summary.name;
      el.dAlias.textContent = summary.aliases || '';
      el.dGroup.textContent = summary.group;
      el.detailBar.style.background = 'linear-gradient(150deg,' + summary.groupColor + ',#1d2923)';
    }

    FG.loadOrg(id).then(function (o) {
      if (FG.parseHash().id !== id) return;
      state.charts = null;
      state.chartCount = summary ? summary.charts : 0;
      renderOrg(o);
      window.scrollTo(0, 0);
      revealSyndrome(syn);
    }).catch(function (err) {
      el.detailBody.innerHTML = '<div class="loading">載入失敗：' + esc(err.message) + '</div>';
    });
  }

  function showList() {
    el.detailScreen.hidden = true;
    el.listScreen.hidden = false;
    state.org = null;
    state.charts = null;
  }

  /* ---- hash router (keeps the Android back button working) ---------------- */
  function route() {
    var h = FG.parseHash();
    if (h.id && state.index.some(function (o) { return o.id === h.id; })) showDetail(h.id, h.syn);
    else showList();
  }
  window.addEventListener('hashchange', route);

  /* ---- chart viewer ------------------------------------------------------ */
  var zoom = 1;

  function applyZoom() {
    el.vinner.style.width = Math.round(el.vstage.clientWidth * zoom - 20) + 'px';
  }

  function openViewer(index) {
    var fc = (state.charts || [])[index];
    if (!fc) return;
    el.viewerTitle.textContent = fc.title;
    el.vinner.innerHTML = fc.svg;
    el.viewer.classList.add('open');
    document.body.style.overflow = 'hidden';
    zoom = 1;
    applyZoom();
  }

  function closeViewer() {
    el.viewer.classList.remove('open');
    el.vinner.innerHTML = '';
    document.body.style.overflow = '';
  }

  document.getElementById('viewerClose').addEventListener('click', closeViewer);
  document.getElementById('zoomIn').addEventListener('click', function () { zoom = Math.min(zoom * 1.5, 12); applyZoom(); });
  document.getElementById('zoomOut').addEventListener('click', function () { zoom = Math.max(zoom / 1.5, 1); applyZoom(); });
  document.getElementById('zoomFit').addEventListener('click', function () { zoom = 1; applyZoom(); });

  /* ---- events ------------------------------------------------------------ */
  var searchTimer;
  el.search.addEventListener('input', function () {
    var v = this.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () { state.query = v; renderList(); }, 120);
  });

  el.groupChips.addEventListener('click', function (e) {
    var chip = e.target.closest('[data-group]');
    if (!chip) return;
    Array.prototype.forEach.call(this.querySelectorAll('.chip'), function (c) { c.classList.toggle('active', c === chip); });
    state.group = chip.dataset.group;
    renderList();
  });

  el.evidenceChips.addEventListener('click', function (e) {
    var chip = e.target.closest('[data-evidence]');
    if (!chip) return;
    Array.prototype.forEach.call(this.querySelectorAll('.chip'), function (c) { c.classList.toggle('active', c === chip); });
    state.evidence = chip.dataset.evidence;
    renderList();
  });

  el.list.addEventListener('click', function (e) {
    var more = e.target.closest('[data-se-more]');
    if (more) {
      more.previousElementSibling.classList.remove('collapsed');
      more.remove();
      return;
    }
    var chip = e.target.closest('[data-syn]');
    if (chip) { location.hash = '#' + chip.dataset.syn; return; }
    var row = e.target.closest('[data-open]');
    if (row) location.hash = row.dataset.open;
  });

  document.getElementById('back').addEventListener('click', function () {
    if (history.length > 1) history.back(); else location.hash = '';
  });

  el.detailBody.addEventListener('click', function (e) {
    var view = e.target.closest('[data-view]');
    if (view) {
      document.body.classList.toggle('clinical-view', view.dataset.view === 'clinical');
      Array.prototype.forEach.call(el.detailBody.querySelectorAll('[data-view]'), function (b) {
        b.classList.toggle('active', b === view);
      });
      return;
    }
    if (e.target.closest('[data-direct]')) {
      state.directOnly = !state.directOnly;
      var hadCharts = state.charts;
      renderOrg(state.org);
      if (hadCharts) {
        var sect = document.getElementById('chartSect');
        if (sect) { sect.open = true; renderCharts(hadCharts); }
      }
      return;
    }
    var thumb = e.target.closest('[data-chart]');
    if (thumb) openViewer(Number(thumb.dataset.chart));
  });

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.copy-cite');
    if (!btn) return;
    FG.copyText(btn.dataset.citation || '', function (ok) {
      var old = btn.textContent;
      btn.textContent = ok ? '已複製' : '複製失敗';
      setTimeout(function () { btn.textContent = old; }, 1200);
    });
  });

  FG.installViewSwitch();

  /* ---- boot -------------------------------------------------------------- */
  Promise.all([FG.loadMeta(), FG.loadIndex()]).then(function (res) {
    state.meta = res[0];
    state.index = res[1];
    FG.setMeta(state.meta);
    renderChrome();
    renderList();
    route();
  }).catch(function (err) {
    el.list.innerHTML = '<div class="loading">資料載入失敗：' + esc(err.message) + '</div>';
  });
})();
