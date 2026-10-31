// gridcast demand engine -- faithful JS port of the Python package (offline, no dependencies).
(function (root) {
  "use strict";

  // Median per-customer demand (kWh/month) by segment, metered-grounded (Blodgett ~3.4,
  // MDPI 2026 existing median ~3.9; AMDA commercial ~26; productive anchors).
  var SEGMENT_MEDIAN = { household: 4.0, commercial: 22.0, anchor: 180.0 };
  var WEALTH_TIER = { low: 0.5, typical: 1.0, high: 3.0 };
  // Cross-site demand spread (lognormal sigma), calibrated on 38 metered African microgrids
  // (Ajasse 2026, Zenodo 21324726): leave-one-country-out P10-P90 coverage ~80%.
  var SITE_LOG_SIGMA = 1.4;
  var Z90 = 1.2815515655446004;

  // Growth curve: year 1 = A2EI metered ramp, year 2 = Wassie Tum metered (+~30%/yr).
  var GROWTH_CURVE = [
    [0, 0.293], [1, 0.71], [2, 0.77], [3, 0.817], [4, 0.955], [5, 0.904],
    [6, 0.963], [7, 1.0], [8, 0.987], [9, 0.828],
    [12, 1.0], [15, 1.07], [18, 1.14], [21, 1.22], [24, 1.3]
  ];

  // 24h normalized shapes: household = NREL "all households" rural SSA; commercial/anchor = A2EI metered.
  var HOUSEHOLD = [0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.070, 0.070, 0.207, 0.207, 0.207, 0.228,
                   0.126, 0.126, 0.126, 0.074, 0.074, 0.234, 0.365, 0.673, 1.000, 0.939, 0.481, 0.124];
  var A2EI_COMMERCIAL = [0.227, 0.193, 0.176, 0.165, 0.123, 0.122, 0.132, 0.227, 0.457, 0.678, 0.807, 0.934,
                         0.998, 1.000, 0.995, 0.985, 0.916, 0.864, 0.844, 0.903, 0.867, 0.709, 0.468, 0.293];
  var SEGMENT_SHAPES = { household: HOUSEHOLD, commercial: A2EI_COMMERCIAL, anchor: A2EI_COMMERCIAL };

  var IRR_AT_MATCH = 12.5, IRR_LOSS_PER_OVERSIZE = 6.4;

  function tierFactor(segment, tier) {
    return segment === "anchor" ? 1.0 : (WEALTH_TIER[tier] || 1.0);
  }

  // Central estimate is bottom-up (customers x metered median x tier); the P10-P90 band is the
  // measured cross-site spread (SITE_LOG_SIGMA), the dominant uncertainty before connection.
  function estimateSiteDemand(counts, opts) {
    opts = opts || {};
    var m = segmentMedians(counts, opts.adoption, opts.tier);
    var p50 = Object.keys(m).reduce(function (a, k) { return a + m[k]; }, 0);
    if (p50 <= 0) return { 0.1: 0, 0.5: 0, 0.9: 0 };
    return { 0.1: p50 * Math.exp(-Z90 * SITE_LOG_SIGMA), 0.5: p50, 0.9: p50 * Math.exp(Z90 * SITE_LOG_SIGMA) };
  }

  function segmentMedians(counts, adoption, tier) {
    adoption = adoption != null ? adoption : 0.7; tier = tier || "typical";
    var out = {};
    Object.keys(counts).forEach(function (segment) {
      var med = SEGMENT_MEDIAN[segment]; if (med == null) return;
      var connected = segment === "anchor" ? counts[segment] : counts[segment] * adoption;
      out[segment] = connected * med * tierFactor(segment, tier);
    });
    return out;
  }

  function projectDemand(mature, curve) {
    curve = curve || GROWTH_CURVE;
    return curve.map(function (row) {
      return { month: row[0], p10: mature[0.1] * row[1], p50: mature[0.5] * row[1], p90: mature[0.9] * row[1] };
    });
  }

  function irrForDemand(planned, actual) {
    var oversize = Math.max(planned / Math.max(actual, 1e-9), 1.0);
    return IRR_AT_MATCH - IRR_LOSS_PER_OVERSIZE * (oversize - 1.0);
  }

  function bankability(q, minIrr) {
    minIrr = minIrr != null ? minIrr : 6.0;
    var planned = q[0.5];
    var irr = { 0.1: irrForDemand(planned, q[0.1]), 0.5: irrForDemand(planned, q[0.5]), 0.9: irrForDemand(planned, q[0.9]) };
    var floor = planned / (1 + (IRR_AT_MATCH - minIrr) / IRR_LOSS_PER_OVERSIZE);
    return { irr: irr, floor: floor, floorPct: 100 * floor / planned };
  }

  function siteHourly(segmentEnergy) {
    var hourly = new Array(24).fill(0);
    Object.keys(segmentEnergy).forEach(function (segment) {
      var shape = SEGMENT_SHAPES[segment]; if (!shape) return;
      var s = shape.reduce(function (a, b) { return a + b; }, 0);
      for (var h = 0; h < 24; h++) hourly[h] += segmentEnergy[segment] * shape[h] / s;
    });
    return hourly;
  }

  function profileMetrics(segmentEnergy) {
    var hourly = siteHourly(segmentEnergy);
    var peak = Math.max.apply(null, hourly);
    var mean = hourly.reduce(function (a, b) { return a + b; }, 0) / 24;
    return { hourly: hourly, peakKw: peak, loadFactor: peak ? mean / peak : 0, peakHour: hourly.indexOf(peak) };
  }

  function sizeSystem(segmentEnergyDaily, opts) {
    opts = opts || {};
    var psh = opts.psh || 5.3, pr = opts.pr || 0.75, dod = opts.dod || 0.8;
    var hourly = siteHourly(segmentEnergyDaily);
    var daily = hourly.reduce(function (a, b) { return a + b; }, 0);
    var offSolar = 0;
    for (var h = 0; h < 24; h++) if (h < 7 || h >= 17) offSolar += hourly[h];
    var m = profileMetrics(segmentEnergyDaily);
    return {
      peakKw: Math.round(m.peakKw * 10) / 10, loadFactor: Math.round(m.loadFactor * 1000) / 1000,
      dailyEnergyKwh: Math.round(daily * 10) / 10,
      pvKwp: Math.round(daily / (psh * pr) * 10) / 10,
      batteryKwh: Math.round(offSolar / dod * 10) / 10
    };
  }

  function confidence(nBuildings, source, nAnchor, perCustomerKwh, nLarge, osmBuildings) {
    nLarge = nLarge || 0;
    var score = 1.0, reasons = [];
    if (!(perCustomerKwh >= 1.5 && perCustomerKwh <= 50)) {
      score -= 0.40; reasons.push("implied " + perCustomerKwh.toFixed(0) + " kWh/customer is outside the metered 1.5-50 range; trust the range, not the P50");
    }
    if (source === "open_buildings") { score -= 0.25; reasons.push("automatic satellite estimate: buildings are a ceiling, not connections (our 3 metered sites ran 1.6x-14x more buildings than connections). Set your planned connections and wealth tier for a validated figure"); }
    if (source === "osm") { score -= 0.20; reasons.push("count from OSM only (undercounts rural)"); }
    if (osmBuildings != null && nBuildings >= 100 && osmBuildings < 0.2 * nBuildings) {
      score -= 0.25; reasons.push("OSM maps only " + osmBuildings + " of " + nBuildings + " structures: business/anchor share is a guess");
    }
    if (nBuildings < 30) { score -= 0.30; reasons.push("very small settlement (" + nBuildings + " buildings)"); }
    else if (nBuildings < 100) { score -= 0.10; reasons.push("small settlement (" + nBuildings + " buildings)"); }
    if (nAnchor === 0 && nLarge > 0) { score -= 0.10; reasons.push(nLarge + " large structures but no mapped anchors"); }
    score = Math.max(score, 0);
    var level = score >= 0.8 ? "high" : score >= 0.5 ? "medium" : "low";
    return { level: level, score: Math.round(score * 100) / 100, reasons: reasons.length ? reasons : ["resembles the validated low-consumption rural sites"] };
  }

  var api = {
    SEGMENT_MEDIAN: SEGMENT_MEDIAN, WEALTH_TIER: WEALTH_TIER, GROWTH_CURVE: GROWTH_CURVE,
    HOUSEHOLD: HOUSEHOLD, A2EI_COMMERCIAL: A2EI_COMMERCIAL,
    estimateSiteDemand: estimateSiteDemand, segmentMedians: segmentMedians, projectDemand: projectDemand,
    bankability: bankability, profileMetrics: profileMetrics, sizeSystem: sizeSystem, confidence: confidence
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.Gridcast = api;
})(typeof window !== "undefined" ? window : globalThis);
