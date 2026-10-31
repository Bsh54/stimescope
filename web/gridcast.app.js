// gridcast results app: binds the engine + sites to a real dashboard (demand range, growth,
// 24h profile, PV/battery sizing, bankability, confidence, and metered validation).
(function () {
  "use strict";
  var G = window.Gridcast, SITES = window.GridcastSites || [];
  if (!G) return;

  var fmt = function (n) { return Math.round(n).toLocaleString("en-US"); };
  var connected = function (c, a) { return (c.anchor || 0) + a * ((c.household || 0) + (c.commercial || 0)); };

  function el(id) { return document.getElementById(id); }

  // ---- inline SVG charts (dependency-free) -------------------------------------------------
  function areaChart(points, opts) {
    // points: [{x, lo, mid, hi}]; x already normalized 0..1
    var w = 560, h = 180, pad = 28, W = w - pad * 2, H = h - pad * 2;
    var maxY = 0; points.forEach(function (p) { if (p.hi > maxY) maxY = p.hi; });
    maxY = maxY * 1.1 || 1;
    var X = function (x) { return pad + x * W; }, Y = function (y) { return pad + H - (y / maxY) * H; };
    var top = points.map(function (p) { return X(p.x) + "," + Y(p.hi); }).join(" ");
    var bot = points.slice().reverse().map(function (p) { return X(p.x) + "," + Y(p.lo); }).join(" ");
    var mid = points.map(function (p, i) { return (i ? "L" : "M") + X(p.x) + " " + Y(p.mid); }).join(" ");
    var grid = "";
    for (var g = 0; g <= 2; g++) { var yy = pad + (H * g / 2); grid += '<line x1="' + pad + '" y1="' + yy + '" x2="' + (w - pad) + '" y2="' + yy + '" stroke="#bcc9c6" stroke-width="0.5" stroke-dasharray="3 5"/>'; }
    var labels = (opts && opts.xlabels) ? opts.xlabels.map(function (l) { return '<text x="' + X(l.x) + '" y="' + (h - 6) + '" fill="#3d4947" font-size="9" text-anchor="middle">' + l.t + '</text>'; }).join("") : "";
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" class="w-full h-auto">' + grid +
      '<polygon points="' + top + " " + bot + '" fill="#008378" opacity="0.14"/>' +
      '<path d="' + mid + '" fill="none" stroke="#00685f" stroke-width="2.5"/>' +
      '<text x="' + pad + '" y="14" fill="#3d4947" font-size="9">' + fmt(maxY) + ' kWh/mo</text>' + labels + '</svg>';
  }

  function lineChart(values, opts) {
    var w = 560, h = 150, pad = 26, W = w - pad * 2, H = h - pad * 2;
    var maxY = Math.max.apply(null, values) * 1.1 || 1;
    var X = function (i) { return pad + (i / (values.length - 1)) * W; }, Y = function (v) { return pad + H - (v / maxY) * H; };
    var path = values.map(function (v, i) { return (i ? "L" : "M") + X(i) + " " + Y(v); }).join(" ");
    var area = "M" + X(0) + " " + Y(0) + path.slice(1) + " L" + X(values.length - 1) + " " + Y(0) + " Z";
    var peakI = values.indexOf(Math.max.apply(null, values));
    var hours = [0, 6, 12, 18, 23].map(function (hh) { return '<text x="' + X(hh) + '" y="' + (h - 5) + '" fill="#3d4947" font-size="9" text-anchor="middle">' + hh + 'h</text>'; }).join("");
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" class="w-full h-auto">' +
      '<path d="' + area + '" fill="#4b41e1" opacity="0.10"/>' +
      '<path d="' + path + '" fill="none" stroke="#4b41e1" stroke-width="2.5"/>' +
      '<circle cx="' + X(peakI) + '" cy="' + Y(values[peakI]) + '" r="3.5" fill="#4b41e1"/>' +
      '<text x="' + X(peakI) + '" y="' + (Y(values[peakI]) - 6) + '" fill="#4b41e1" font-size="9" text-anchor="middle" font-weight="600">peak ' + peakI + 'h</text>' + hours + '</svg>';
  }

  // ---- results view ------------------------------------------------------------------------
  var STATE = null;

  function controlsHtml(s) {
    var seg = s.counts, isCustom = s.custom;
    var row = function (label, html) { return '<label class="flex items-center justify-between gap-3 py-1"><span class="font-body-sm text-body-sm text-on-surface-variant">' + label + '</span>' + html + '</label>'; };
    var num = function (id, val) { return '<input id="' + id + '" type="number" min="0" value="' + val + '" class="w-24 bg-surface-container-low rounded-lg px-2 py-1 font-metric-data text-metric-data text-right text-on-surface ring-1 ring-outline-variant/40 focus:ring-primary focus:outline-none"/>'; };
    var tierSel = '<select id="gc-tier" class="bg-surface-container-low rounded-lg px-2 py-1 font-label-md text-label-md text-on-surface">' +
      ["low", "typical", "high"].map(function (t) { return '<option value="' + t + '"' + (s.tier === t ? " selected" : "") + '>' + t + '</option>'; }).join("") + '</select>';
    var adopt = '<input id="gc-adopt" type="range" min="0.1" max="1" step="0.05" value="' + s.adoption + '" class="w-32 accent-primary"/><span id="gc-adopt-v" class="font-metric-data-sm text-metric-data-sm w-8 text-right">' + Math.round(s.adoption * 100) + '%</span>';
    return '<div class="bg-surface-container-lowest rounded-2xl ring-1 ring-outline-variant/30 p-space-lg shadow-sm flex flex-col gap-1">' +
      '<p class="font-body-sm text-body-sm text-on-surface-variant mb-1">' + (isCustom
        ? 'Planned connections (you set these).'
        : 'Satellite gives the building count, not what each building is. These counts are an estimate, edit any of them to match what you know on the ground.') + '</p>' +
      row("Households", num("gc-hh", seg.household || 0)) +
      row("Commercial / SME", num("gc-com", seg.commercial || 0)) +
      row("Anchor / productive", num("gc-anc", seg.anchor || 0)) +
      '<div class="h-px bg-outline-variant/40 my-1"></div>' +
      row("Wealth tier", tierSel) +
      row("Connection rate" + help("Share of the detected buildings that become active connections. Satellite counts every structure (compounds, stores, outbuildings), so this is well below 100%. Default 40% is the median across our 3 metered sites; drop it for spread-out settlements, raise it if you know most buildings connect."), '<span class="flex items-center gap-2">' + adopt + '</span>') +
      '</div>';
  }

  function help(text) {
    return '<span class="gc-help" tabindex="0" role="button" aria-label="Explanation"><span class="material-symbols-outlined" style="font-size:15px;vertical-align:-2px">info</span><span class="gc-tip">' + text + '</span></span>';
  }
  var HELP_CSS = '<style>' +
    '.gc-help{position:relative;display:inline-block;margin-left:4px;color:#6d7a77;cursor:help;font-family:Inter,sans-serif}' +
    '.gc-tip{position:absolute;bottom:135%;left:50%;transform:translateX(-50%);width:220px;max-width:62vw;background:#131b2e;color:#fff;padding:9px 11px;border-radius:8px;font-size:12px;font-weight:400;line-height:1.45;opacity:0;visibility:hidden;transition:opacity .15s;z-index:60;box-shadow:0 6px 20px rgba(0,0,0,.28);text-transform:none;letter-spacing:normal;pointer-events:none}' +
    '.gc-help:hover>.gc-tip,.gc-help:focus>.gc-tip,.gc-help.on>.gc-tip{opacity:1;visibility:visible}' +
    '</style>';

  function statTile(label, value, unit, sub, accent, tip) {
    return '<div class="bg-surface-container-lowest rounded-xl p-space-md shadow-sm ring-1 ring-outline-variant/30 flex flex-col gap-0.5">' +
      '<span class="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">' + label + (tip ? help(tip) : '') + '</span>' +
      '<span class="font-metric-display text-metric-display ' + (accent || "text-on-surface") + '">' + value + ' <span class="font-body-sm text-body-sm text-on-surface-variant">' + (unit || "") + '</span></span>' +
      (sub ? '<span class="font-body-sm text-body-sm text-on-surface-variant">' + sub + '</span>' : '') + '</div>';
  }

  function sectionTitle(icon, title, sub, tip) {
    return '<div class="flex items-center gap-2 mb-space-sm"><span class="material-symbols-outlined text-[20px] text-primary">' + icon + '</span>' +
      '<span class="font-headline-sm text-headline-sm font-semibold text-on-surface">' + title + '</span>' +
      (sub ? '<span class="font-body-sm text-body-sm text-on-surface-variant">· ' + sub + '</span>' : '') +
      (tip ? help(tip) : '') + '</div>';
  }

  function rangeBar(p10, p50, p90) {
    var max = p90 * 1.08 || 1, pc = function (v) { return 100 * v / max; };
    return '<div class="mt-space-md">' +
      '<div class="relative h-3.5 rounded-full bg-surface-container-high overflow-hidden">' +
      '<div class="absolute top-0 bottom-0 bg-primary/25" style="left:' + pc(p10) + '%;width:' + (pc(p90) - pc(p10)) + '%"></div>' +
      '<div class="absolute top-0 bottom-0 w-[3px] bg-primary rounded" style="left:calc(' + pc(p50) + '% - 1.5px)"></div></div>' +
      '<div class="flex justify-between mt-1.5 font-metric-data-sm text-metric-data-sm"><span class="text-on-surface-variant">P10 ' + fmt(p10) + '</span>' +
      '<span class="text-primary font-semibold">P50 ' + fmt(p50) + '</span><span class="text-on-surface-variant">P90 ' + fmt(p90) + '</span></div>' +
      '<p class="font-body-sm text-body-sm text-on-surface-variant mt-1">80% confidence the true demand sits inside this band.</p></div>';
  }

  var SEG_COLOR = { household: "#00685f", commercial: "#4b41e1", anchor: "#855300" };

  function stackBar(parts) {
    var total = parts.reduce(function (a, p) { return a + p.value; }, 0) || 1;
    return '<div class="flex h-3 rounded-full overflow-hidden bg-surface-container-high">' +
      parts.map(function (p) { return '<div style="width:' + (100 * p.value / total) + '%;background:' + p.color + '"></div>'; }).join("") + '</div>';
  }

  function render() {
    var s = STATE;
    var d = G.estimateSiteDemand(s.counts, { adoption: s.adoption, tier: s.tier });
    var conn = connected(s.counts, s.adoption);
    var perCust = d[0.5] / Math.max(conn, 1);
    var medians = G.segmentMedians(s.counts, s.adoption, s.tier);
    var daily = {}; Object.keys(medians).forEach(function (k) { daily[k] = medians[k] / 30.4; });
    var sys = G.sizeSystem(daily);
    var prof = G.profileMetrics(daily);
    var bank = G.bankability(d);
    var effSource = s.refined ? "user" : (s.source || "custom");
    var conf = G.confidence(s.buildings || Math.round(conn / s.adoption), effSource, s.counts.anchor || 0, perCust, s.large || 0, s.osm_buildings);
    var ramp = G.projectDemand(d);

    // hero result
    el("gc-hero-val").textContent = fmt(d[0.5]);
    el("gc-hero-range").innerHTML = rangeBar(d[0.1], d[0.5], d[0.9]);
    el("gc-hero-perc").innerHTML = statTile("Per customer", perCust.toFixed(0), "kWh/mo", fmt(conn) + " connected · metered 1.5-50", (perCust >= 1.5 && perCust <= 50) ? "text-on-surface" : "text-secondary");
    el("gc-hero-annual").innerHTML = statTile("Annual energy", fmt(d[0.5] * 12), "kWh/yr", "at mature P50");

    // drivers (plain-language breakdown)
    var mh = medians.household || 0, mc = medians.commercial || 0, ma = medians.anchor || 0;
    var totM = mh + mc + ma || 1;
    var pctOf = function (v) { return Math.round(100 * v / totM); };
    var driverRow = function (color, label, n, kwh) {
      return '<div class="flex items-center gap-2 py-1"><span class="w-2.5 h-2.5 rounded-sm shrink-0" style="background:' + color + '"></span>' +
        '<span class="font-body-md text-body-md text-on-surface flex-1">' + fmt(n) + ' ' + label + '</span>' +
        '<span class="font-metric-data-sm text-metric-data-sm text-on-surface-variant">' + fmt(kwh) + ' kWh/mo</span>' +
        '<span class="font-label-sm text-label-sm text-on-surface-variant w-10 text-right">' + pctOf(kwh) + '%</span></div>';
    };
    el("gc-drivers").innerHTML =
      sectionTitle("insights", "What drives this estimate", null, "Where the demand comes from. Each customer type uses a different amount: a shop or an anchor (mill, clinic, pump) uses far more than a home, so a few of them can drive most of the load. The bar and percentages show each type's share.") +
      stackBar([{ value: mh, color: SEG_COLOR.household }, { value: mc, color: SEG_COLOR.commercial }, { value: ma, color: SEG_COLOR.anchor }]) +
      '<div class="mt-space-md flex flex-col divide-y divide-outline-variant/30">' +
      driverRow(SEG_COLOR.household, "households", s.counts.household || 0, mh) +
      driverRow(SEG_COLOR.commercial, "commercial / SME", s.counts.commercial || 0, mc) +
      driverRow(SEG_COLOR.anchor, "anchor / productive", s.counts.anchor || 0, ma) + '</div>' +
      '<p class="font-body-md text-body-md text-on-surface-variant mt-space-md">' +
      'At a <span class="text-on-surface font-semibold">' + s.tier + '</span> wealth tier and a ' + Math.round(s.adoption * 100) + '% connection rate, ' +
      (ma + mc > mh ? 'commercial and anchor customers drive most of the load despite being the minority of connections.' : 'households make up the bulk of demand, typical of a residential village.') +
      ' Change the tier, connection rate or counts below to see the effect.</p>';

    // growth chart (map month value to x in 0..1 over 0..24)
    var gp = ramp.map(function (r) { return { x: r.month / 24, lo: r.p10, mid: r.p50, hi: r.p90 }; });
    el("gc-growth").innerHTML = areaChart(gp, { xlabels: [{ x: 0, t: "month 0" }, { x: 7 / 24, t: "m7" }, { x: 12 / 24, t: "year 1" }, { x: 1, t: "year 2" }] });

    // 24h profile
    el("gc-profile").innerHTML = lineChart(prof.hourly);

    // system sizing tiles
    el("gc-sizing").innerHTML =
      statTile("Peak load", sys.peakKw, "kW", "highest instant power", "text-on-surface", "The maximum power the plant must supply at once (usually the evening peak). It sizes the inverter and generation, not the energy total.") +
      statTile("Load factor", (+prof.loadFactor).toFixed(2), "", "flat vs peaky, peak " + prof.peakHour + "h", "text-on-surface", "Average load divided by peak load. Low (~0.2-0.3) means peaky, evening-heavy demand that costs more per kWh; adding daytime business use raises it and cuts cost.") +
      statTile("PV array", sys.pvKwp, "kWp", "solar panels needed", "text-primary", "Solar capacity to cover the daily energy, assuming 5.3 peak-sun-hours and a 0.75 performance ratio.") +
      statTile("Battery", sys.batteryKwh, "kWh", "evening/night storage", "text-primary", "Storage to carry evening and night demand when the sun is down, at 80% depth of discharge.");

    // bankability
    var floorPct = Math.round(bank.floorPct);
    el("gc-bank").innerHTML =
      '<div class="flex flex-wrap gap-4 items-end">' +
      ["0.1", "0.5", "0.9"].map(function (q) { return '<div class="flex flex-col"><span class="font-label-sm text-label-sm text-on-surface-variant">IRR if actual = P' + (q === "0.1" ? "10" : q === "0.5" ? "50" : "90") + '</span><span class="font-metric-data text-metric-data ' + (bank.irr[q] >= 6 ? "text-primary" : "text-error") + '">' + bank.irr[q].toFixed(1) + '%</span></div>'; }).join("") +
      '</div>' +
      '<div class="mt-3"><div class="flex justify-between font-body-sm text-body-sm text-on-surface-variant mb-1"><span>Viability floor (IRR ≥ 6%)</span><span class="font-metric-data-sm">' + fmt(bank.floor) + ' kWh/mo = ' + floorPct + '% of P50</span></div>' +
      '<div class="w-full h-3 bg-surface-container-high rounded-full overflow-hidden"><div class="h-full bg-primary" style="width:' + floorPct + '%"></div></div>' +
      '<p class="font-body-sm text-body-sm text-on-surface-variant mt-1">Demand can fall ~' + (100 - floorPct) + '% below forecast before the project stops clearing a 6% IRR.</p></div>';

    // confidence
    var badge = { high: ["check_circle", "text-primary", "bg-primary/10"], medium: ["info", "text-secondary", "bg-secondary/10"], low: ["warning", "text-error", "bg-error/10"] }[conf.level];
    el("gc-conf").innerHTML =
      '<div class="flex items-center gap-2"><span class="inline-flex items-center gap-1 ' + badge[2] + ' ' + badge[1] + ' px-2.5 py-1 rounded-lg font-label-md text-label-md font-semibold"><span class="material-symbols-outlined text-[16px]">' + badge[0] + '</span>' + conf.level.toUpperCase() + ' · ' + conf.score + '</span></div>' +
      '<ul class="mt-2 flex flex-col gap-1">' + conf.reasons.map(function (r) { return '<li class="font-body-sm text-body-sm text-on-surface-variant flex gap-1.5"><span class="material-symbols-outlined text-[14px] mt-0.5">chevron_right</span><span>' + r + '</span></li>'; }).join("") + '</ul>';

    // validation overlay (metered sites only)
    var vo = el("gc-valid");
    if (s.metered_kwh_month) {
      var err = 100 * (d[0.5] - s.metered_kwh_month) / s.metered_kwh_month;
      var inband = d[0.1] <= s.metered_kwh_month && s.metered_kwh_month <= d[0.9];
      vo.classList.remove("hidden");
      vo.innerHTML =
        '<div class="flex items-center gap-2 mb-2"><span class="material-symbols-outlined text-[18px] text-primary">verified</span><span class="font-label-md text-label-md font-semibold">Held-out validation: metered truth</span></div>' +
        '<div class="flex flex-wrap gap-6">' +
        '<div><span class="font-label-sm text-label-sm text-on-surface-variant block">Predicted P50</span><span class="font-metric-data text-metric-data">' + fmt(d[0.5]) + ' kWh/mo</span></div>' +
        '<div><span class="font-label-sm text-label-sm text-on-surface-variant block">Metered actual</span><span class="font-metric-data text-metric-data text-primary">' + fmt(s.metered_kwh_month) + ' kWh/mo</span></div>' +
        '<div><span class="font-label-sm text-label-sm text-on-surface-variant block">P50 error</span><span class="font-metric-data text-metric-data ' + (Math.abs(err) <= 25 ? "text-primary" : "text-secondary") + '">' + (err >= 0 ? "+" : "") + err.toFixed(0) + '%</span></div>' +
        '<div><span class="font-label-sm text-label-sm text-on-surface-variant block">Metered in P10-P90</span><span class="font-metric-data text-metric-data ' + (inband ? "text-primary" : "text-error") + '">' + (inband ? "YES" : "NO") + '</span></div>' +
        '</div>' +
        '<p class="font-body-sm text-body-sm text-on-surface-variant mt-2">' + (s.note || "") + (s.rwi != null ? ' RWI ' + s.rwi + ', VIIRS ' + s.viirs + ' (neither predicts the tier).' : '') + '</p>';
    } else { vo.classList.add("hidden"); }
  }

  function bindControls() {
    ["gc-hh", "gc-com", "gc-anc"].forEach(function (id) {
      var node = el(id); if (!node) return;
      node.addEventListener("input", function () {
        STATE.counts = { household: +el("gc-hh").value || 0, commercial: +el("gc-com").value || 0, anchor: +el("gc-anc").value || 0 };
        STATE.refined = true;
        render();
      });
    });
    var tier = el("gc-tier"); if (tier) tier.addEventListener("change", function () { STATE.tier = tier.value; render(); });
    var adopt = el("gc-adopt"); if (adopt) adopt.addEventListener("input", function () { STATE.adopt; STATE.adoption = +adopt.value; el("gc-adopt-v").textContent = Math.round(STATE.adoption * 100) + "%"; render(); });
  }

  function showResults(site) {
    STATE = JSON.parse(JSON.stringify(site));
    STATE.counts = Object.assign({ household: 0, commercial: 0, anchor: 0 }, STATE.counts);
    if (STATE.adoption == null) STATE.adoption = 0.7;
    if (!STATE.tier) STATE.tier = "typical";
    var view = el("view-results");
    var globe = el("view-globe"), map = el("view-map");
    if (globe) globe.classList.add("hidden");
    if (map) { map.style.display = "none"; }
    view.style.display = "flex";
    document.body.classList.add("overflow-hidden");
    view.innerHTML = HELP_CSS +
      '<header class="shrink-0 h-14 px-space-md flex items-center justify-between bg-surface-container-lowest/95 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.06)] sticky top-0 z-10">' +
      '<div class="flex items-center gap-2 min-w-0"><button id="gc-back" class="w-9 h-9 rounded-lg hover:bg-surface-container flex items-center justify-center text-on-surface-variant"><span class="material-symbols-outlined text-[20px]">arrow_back</span></button>' +
      '<span class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-on-primary"><span class="material-symbols-outlined text-[18px]">insights</span></span>' +
      '<div class="flex flex-col leading-tight min-w-0"><span class="font-label-md text-label-md font-semibold truncate">' + site.name + '</span>' +
      '<span class="font-metric-data-sm text-metric-data-sm text-on-surface-variant truncate">' + (site.lat != null ? site.lat.toFixed(4) + '°, ' + site.lon.toFixed(4) + '° · ' : '') + (site.custom ? 'custom input' : (site.source || '')) + '</span></div></div>' +
      '<span class="hidden sm:flex items-center gap-1 font-metric-data-sm text-metric-data-sm text-primary bg-primary/10 px-2.5 py-1.5 rounded-lg"><span class="material-symbols-outlined text-[14px]">bolt</span>pre-build demand forecast</span></header>' +
      '<div class="flex-1 overflow-y-auto bg-background"><div class="max-w-5xl mx-auto w-full px-space-lg py-space-lg flex flex-col gap-space-xl">' +

      '<section class="bg-surface-container-lowest rounded-2xl shadow-md ring-1 ring-outline-variant/30 p-space-xl">' +
      '<div class="grid grid-cols-1 md:grid-cols-[1.4fr_1fr] gap-space-lg md:items-center">' +
      '<div><span class="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant">Predicted demand · mature median' + help("The most likely monthly electricity use once the village is fully connected and settled (after the first ~2 years of growth). We give a middle estimate (P50) plus a range, because demand before building is genuinely uncertain.") + '</span>' +
      '<div class="flex items-baseline gap-2 mt-1"><span id="gc-hero-val" class="text-primary" style="font-family:\'JetBrains Mono\',monospace;font-size:3.4rem;line-height:1;font-weight:700">—</span><span class="font-headline-sm text-headline-sm text-on-surface-variant">kWh/month</span></div>' +
      '<div id="gc-hero-range"></div></div>' +
      '<div class="flex flex-col gap-space-sm"><div id="gc-conf"></div>' +
      '<div class="grid grid-cols-2 gap-space-sm"><div id="gc-hero-perc"></div><div id="gc-hero-annual"></div></div></div>' +
      '</div></section>' +

      '<section id="gc-valid" class="hidden bg-primary-container/10 ring-1 ring-primary/30 rounded-2xl p-space-lg"></section>' +
      (site.source === "open_buildings" ? '<section class="bg-secondary/10 ring-1 ring-secondary/30 rounded-2xl p-space-lg flex gap-3"><span class="material-symbols-outlined text-secondary">satellite_alt</span><div><div class="font-label-md text-label-md font-semibold text-on-surface">Satellite planning estimate</div><p class="font-body-sm text-body-sm text-on-surface-variant mt-1">' + fmt(site.buildings || 0) + ' buildings detected is the ceiling, if every structure connected. The forecast below assumes a ' + Math.round((site.adoption || 0.4) * 100) + '% connection rate, because satellite counts every structure and not all are connected dwellings (our 3 metered sites ran 1.6x to 14x more buildings than connections). For a validated result, set your actual planned connections in Tune the inputs.</p></div></section>' : '') +

      '<section><div id="gc-drivers" class="bg-surface-container-lowest rounded-2xl shadow-sm ring-1 ring-outline-variant/30 p-space-lg"></div></section>' +

      '<section>' + sectionTitle("solar_power", "System sizing", "right-sized to the P50 forecast", "The solar + battery plant sized to meet the forecast. Oversizing wastes money; undersizing causes blackouts. These are first-order estimates, not a final engineering design.") +
      '<div id="gc-sizing" class="grid grid-cols-2 md:grid-cols-4 gap-space-md"></div></section>' +

      '<section class="grid grid-cols-1 lg:grid-cols-2 gap-space-lg">' +
      '<div class="bg-surface-container-lowest rounded-2xl shadow-sm ring-1 ring-outline-variant/30 p-space-lg">' + sectionTitle("trending_up", "Demand growth", "first 2 years", "Demand is low on day one and grows as people buy appliances and businesses expand. This curve is anchored on real metered trajectories from comparable mini-grids, not a guess.") + '<div id="gc-growth"></div></div>' +
      '<div class="bg-surface-container-lowest rounded-2xl shadow-sm ring-1 ring-outline-variant/30 p-space-lg">' + sectionTitle("schedule", "24-hour load profile", null, "How consumption varies across the day. The evening peak (around 20h) is what the battery must cover; daytime business use would flatten this curve.") + '<div id="gc-profile"></div></div>' +
      '</section>' +

      '<section>' + sectionTitle("request_quote", "Bankability", "IRR exposure to demand risk", "How the project's return (IRR) changes if real demand lands at P10, P50 or P90. The viability floor is how far demand can fall before the IRR drops below a bankable 6%. It shows a lender how much demand risk the project can absorb.") +
      '<div id="gc-bank" class="bg-surface-container-lowest rounded-2xl shadow-sm ring-1 ring-outline-variant/30 p-space-lg"></div></section>' +

      '<section>' + sectionTitle("tune", "Tune the inputs", "adjust and everything recomputes live") +
      controlsHtml(STATE) + '</section>' +

      '</div></div>';
    el("gc-back").addEventListener("click", hideResults);
    bindControls();
    render();
  }

  function hideResults() {
    var view = el("view-results"); view.style.display = "none";
    document.body.classList.remove("overflow-hidden");
    var globe = el("view-globe"); if (globe) globe.classList.remove("hidden");
  }

  // ---- validation site cards on the landing -----------------------------------------------
  var COUNTRY = { MW: "Malawi", ET: "Ethiopia", BJ: "Benin", KE: "Kenya" };

  function validationCard(s) {
    var d = G.estimateSiteDemand(s.counts, { adoption: s.adoption, tier: s.tier });
    var p10 = d[0.1], p50 = d[0.5], p90 = d[0.9], metered = s.metered_kwh_month;
    var within = metered >= p10 && metered <= p90;
    var err = Math.round((p50 - metered) / metered * 100);
    var badge = within
      ? '<span class="inline-flex items-center gap-1 text-[11px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full"><span class="material-symbols-outlined text-[13px]">task_alt</span>inside P10 to P90</span>'
      : '<span class="inline-flex items-center gap-1 text-[11px] font-semibold text-error bg-error/10 px-2 py-0.5 rounded-full">outside band</span>';
    return '<button data-site="' + s.id + '" class="group text-left bg-surface-container-lowest hover:bg-surface-container ring-1 ring-outline-variant/40 hover:ring-primary/40 rounded-3xl p-5 shadow-md hover:shadow-xl transition-all flex flex-col gap-3">' +
      '<div class="flex items-start justify-between gap-2">' +
        '<div class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-[22px]">verified</span>' +
        '<div><div class="font-title-md text-title-md text-on-surface leading-tight">' + s.name + '</div>' +
        '<div class="font-body-sm text-body-sm text-on-surface-variant">' + (COUNTRY[s.country] || s.country) + '</div></div></div>' +
        badge + '</div>' +
      '<div class="grid grid-cols-2 gap-3 pt-1">' +
        '<div><div class="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Metered truth</div>' +
        '<div class="font-headline-sm text-headline-sm text-on-surface font-semibold">' + fmt(metered) + '<span class="font-body-sm text-body-sm text-on-surface-variant"> kWh/mo</span></div></div>' +
        '<div><div class="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Model P50</div>' +
        '<div class="font-headline-sm text-headline-sm text-primary font-semibold">' + fmt(p50) + '<span class="font-body-sm text-body-sm text-on-surface-variant"> (' + (err >= 0 ? "+" : "") + err + '%)</span></div></div>' +
      '</div>' +
      '<div class="font-body-sm text-body-sm text-on-surface-variant">Range P10 to P90: ' + fmt(p10) + ' to ' + fmt(p90) + ' kWh/mo</div>' +
      '<div class="flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-on-surface-variant border-t border-outline-variant/30 pt-2">' +
        '<span>' + fmt(s.counts.household) + ' households</span><span>' + fmt(s.counts.commercial) + ' commercial</span><span>' + fmt(s.counts.anchor) + ' anchor</span></div>' +
      '<div class="flex items-center gap-1 text-primary font-label-md text-label-md opacity-0 group-hover:opacity-100 transition-opacity">See full analysis<span class="material-symbols-outlined text-[16px]">arrow_forward</span></div>' +
      '</button>';
  }

  function mountChips() {
    var host = document.getElementById("gc-demo-chips"); if (!host) return;
    var sites = SITES.filter(function (s) { return s.kind === "validation"; });
    host.innerHTML = '<div class="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider text-center mb-3">Validated on real metered mini-grids</div>' +
      '<div class="grid grid-cols-1 md:grid-cols-3 gap-4">' + sites.map(validationCard).join("") + '</div>';
    host.querySelectorAll("[data-site]").forEach(function (b) {
      b.addEventListener("click", function () {
        var s = SITES.filter(function (x) { return x.id === b.dataset.site; })[0];
        if (s) showResults(s);
      });
    });
  }

  function nearestSite(lat, lon) {
    var best = null, bd = 8;
    SITES.forEach(function (s) {
      if (s.lat == null) return;
      var dx = (s.lon - lon) * 111.32 * Math.cos(lat * Math.PI / 180), dy = (s.lat - lat) * 110.54;
      var d = Math.hypot(dx, dy); if (d < bd) { bd = d; best = s; }
    });
    return best;
  }

  function showSteps(steps) {
    hideLoading();
    var o = document.createElement("div"); o.id = "gc-loading";
    o.style.cssText = "position:fixed;inset:0;z-index:300;background:rgba(250,248,255,0.95);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px";
    var rows = steps.map(function (s, i) {
      return '<div class="gc-step flex items-center gap-3" data-i="' + i + '" style="opacity:.4">' +
        '<span class="gc-ic material-symbols-outlined text-on-surface-variant" style="font-size:22px">radio_button_unchecked</span>' +
        '<span class="font-body-md text-body-md text-on-surface">' + s + '</span></div>';
    }).join("");
    o.innerHTML = '<span class="material-symbols-outlined text-primary" style="font-size:44px;animation:gcspin 1s linear infinite">progress_activity</span>' +
      '<div class="flex flex-col gap-2 items-start">' + rows + '</div>' +
      '<style>@keyframes gcspin{to{transform:rotate(360deg)}}</style>';
    document.body.appendChild(o);
  }
  function stepTo(i) {
    var o = document.getElementById("gc-loading"); if (!o) return;
    o.querySelectorAll(".gc-step").forEach(function (el) {
      var k = +el.getAttribute("data-i"), ic = el.querySelector(".gc-ic");
      if (k < i) { el.style.opacity = "1"; ic.textContent = "check_circle"; ic.className = "gc-ic material-symbols-outlined text-primary"; ic.style.animation = ""; }
      else if (k === i) { el.style.opacity = "1"; ic.textContent = "progress_activity"; ic.className = "gc-ic material-symbols-outlined text-primary"; ic.style.animation = "gcspin 1s linear infinite"; }
      else { el.style.opacity = ".4"; ic.textContent = "radio_button_unchecked"; ic.className = "gc-ic material-symbols-outlined text-on-surface-variant"; ic.style.animation = ""; }
    });
  }
  function showLoading(msg) { showSteps([msg || "Working"]); stepTo(0); }
  function hideLoading() { var o = document.getElementById("gc-loading"); if (o) o.remove(); }

  function anchorChip(text, pending) {
    var c = document.getElementById("gc-anchor-chip");
    if (!c) {
      c = document.createElement("div"); c.id = "gc-anchor-chip";
      c.style.cssText = "position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:260;display:flex;align-items:center;gap:8px;padding:8px 14px;border-radius:999px;box-shadow:0 4px 16px rgba(0,0,0,.18)";
      document.body.appendChild(c);
    }
    c.className = pending ? "bg-surface-container-lowest ring-1 ring-outline-variant/40" : "bg-surface-container-lowest ring-1 ring-primary/40";
    c.innerHTML = '<span class="material-symbols-outlined text-primary" style="font-size:16px' + (pending ? ';animation:gcspin 1s linear infinite' : '') + '">' + (pending ? 'progress_activity' : 'check_circle') + '</span><span class="font-label-md text-label-md text-on-surface">' + text + '</span>';
    if (!pending) setTimeout(function () { var x = document.getElementById("gc-anchor-chip"); if (x) x.remove(); }, 4000);
  }

  function applyAnchors(osmAnchor, osm) {
    if (!STATE || STATE.source !== "open_buildings" || STATE.buildings == null) { var x = document.getElementById("gc-anchor-chip"); if (x) x.remove(); return; }
    var anchor = Math.max(osmAnchor || 0, STATE.large || 0);
    var ordinary = Math.max((STATE.buildings || 0) - anchor, 0);
    STATE.counts = { household: Math.round(ordinary * 0.9), commercial: Math.round(ordinary * 0.1), anchor: anchor };
    STATE.osm_buildings = osm; STATE.anchorsPending = false;
    render();
    anchorChip(anchor + " likely anchor" + (anchor === 1 ? "" : "s") + " (large footprints + OSM)", false);
  }
  function fallbackCustom(lat, lon, name, msg) {
    showResults({ name: name || "Custom site", lat: lat, lon: lon, custom: true, source: "custom",
      counts: { household: 300, commercial: 30, anchor: 2 }, adoption: 1.0, tier: "typical",
      note: (msg ? msg + ". " : "") + "No live satellite count here. Set the planned connections your project will serve." });
  }

  window.GridcastApp = {
    showResults: showResults,
    showSite: function (id) { var s = SITES.filter(function (x) { return x.id === id; })[0]; if (s) showResults(s); },
    analyzePoint: function (lat, lon, name) {
      var near = nearestSite(lat, lon);
      if (near) { showResults(near); return; }
      var API = window.GRIDCAST_API || "/api";
      showLoading("Counting buildings from satellite…");
      fetch(API + "/count?lat=" + lat + "&lon=" + lon + "&radius=2000")
        .then(function (r) { return r.json(); })
        .then(function (d) {
          hideLoading();
          if (d && d.counts && !d.error) {
            showResults({ name: name || "Selected area", lat: lat, lon: lon, source: "open_buildings",
              counts: d.counts, buildings: d.buildings, large: d.large, osm_buildings: d.osm_buildings,
              adoption: 0.4, tier: "typical",
              note: d.buildings + " buildings detected (Open Buildings), " + (d.large || 0) + " large structures, " + (d.osm_buildings || 0) + " mapped by OSM." });
          } else { fallbackCustom(lat, lon, name, d && d.error); }
        })
        .catch(function () { hideLoading(); fallbackCustom(lat, lon, name); });
    },
    analyzeBounds: function (s, w, n, e, name) {
      var lat = (s + n) / 2, lon = (w + e) / 2;
      var API = window.GRIDCAST_API || "/api";
      showLoading("Counting buildings in the selected box…");
      fetch(API + "/count?minlat=" + s + "&minlon=" + w + "&maxlat=" + n + "&maxlon=" + e)
        .then(function (r) { return r.json(); })
        .then(function (d) {
          hideLoading();
          if (d && d.counts && !d.error) {
            showResults({ name: name || "Selected area", lat: lat, lon: lon, source: "open_buildings",
              counts: d.counts, buildings: d.buildings, large: d.large, osm_buildings: d.osm_buildings,
              adoption: 0.4, tier: "typical",
              note: d.buildings + " buildings in the selected box (Open Buildings), " + (d.large || 0) + " large structures, " + (d.osm_buildings || 0) + " mapped by OSM." });
          } else { fallbackCustom(lat, lon, name, d && d.error); }
        })
        .catch(function () { hideLoading(); fallbackCustom(lat, lon, name); });
    },
    analyzePolygon: function (poly, name) {
      var lat = 0, lon = 0;
      poly.forEach(function (p) { lat += p[0]; lon += p[1]; });
      lat /= poly.length; lon /= poly.length;
      var API = window.GRIDCAST_API || "/api";
      var opts = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ polygon: poly }) };
      showSteps(["Reading building footprints from satellite", "Estimating demand range"]);
      stepTo(0);
      fetch(API + "/count_polygon?anchors=0", opts)
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d || !d.counts || d.error) { hideLoading(); fallbackCustom(lat, lon, name, d && d.error); return; }
          stepTo(1);
          setTimeout(function () {
            hideLoading();
            showResults({ name: name || "Selected area", lat: lat, lon: lon, source: "open_buildings",
              counts: d.counts, buildings: d.buildings, large: d.large, osm_buildings: 0,
              adoption: 0.4, tier: "typical", anchorsPending: true,
              note: d.buildings + " buildings inside the outlined area (Open Buildings), " + (d.large || 0) + " large structures." });
            anchorChip("Looking for anchor businesses (OSM)…", true);
            fetch(API + "/anchors_polygon", opts)
              .then(function (r) { return r.json(); })
              .then(function (a) { applyAnchors((a && typeof a.anchor === "number") ? a.anchor : 0, (a && a.osm_buildings) || 0); })
              .catch(function () { applyAnchors(0, 0); });
          }, 300);
        })
        .catch(function () { hideLoading(); fallbackCustom(lat, lon, name); });
    }
  };

  document.addEventListener("click", function (e) {
    var h = e.target.closest ? e.target.closest(".gc-help") : null;
    document.querySelectorAll(".gc-help.on").forEach(function (x) { if (x !== h) x.classList.remove("on"); });
    if (h) { e.preventDefault(); h.classList.toggle("on"); }
  });

  if (document.readyState !== "loading") mountChips();
  else document.addEventListener("DOMContentLoaded", mountChips);
})();
