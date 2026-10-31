// Precomputed real sites (offline). Counts from Google Open Buildings + OSM; metered totals and
// enrolled connections from Frame 2023 (Sitolo) and Wassie & Ahlgren 2024 (Omorate, Tum).
(function (root) {
  "use strict";
  var SITES = [
    {
      id: "pobe", name: "Pobè", country: "BJ", lat: 6.980, lon: 2.665, kind: "town",
      source: "open_buildings", radius_m: 2500, buildings: 13882, large: 148, osm_buildings: 1039,
      counts: { household: 12479, commercial: 1387, anchor: 16 }, adoption: 0.7, tier: "typical",
      metered_kwh_month: null, rwi: -0.25, viirs: 19.2,
      note: "West-African town; satellite footprints solid, OSM undercounts businesses."
    },
    {
      id: "rural-bj", name: "Rural Bénin (OSM = 0)", country: "BJ", lat: 7.080, lon: 2.665, kind: "rural",
      source: "open_buildings", radius_m: 2500, buildings: 726, large: 0, osm_buildings: 0,
      counts: { household: 653, commercial: 73, anchor: 0 }, adoption: 0.7, tier: "typical",
      metered_kwh_month: null, rwi: null, viirs: 0,
      note: "OSM returns zero buildings here; only satellite footprints see the village."
    },
    {
      id: "sitolo", name: "Sitolo", country: "MW", lat: -13.84, lon: 33.04, kind: "validation",
      source: "metered", counts: { household: 696, commercial: 8, anchor: 4 }, adoption: 1.0, tier: "typical",
      metered_kwh_month: 70003 / 12, rwi: -0.32, viirs: 2.4,
      note: "80 kW CEM mini-grid, metered 2022 (Frame et al.). Low-consumption rural: our sweet spot."
    },
    {
      id: "omorate", name: "Omorate", country: "ET", lat: 4.8032, lon: 36.0504, kind: "validation",
      source: "metered", counts: { household: 301, commercial: 112, anchor: 30 }, adoption: 1.0, tier: "high",
      metered_kwh_month: 1065 * 30.4, rwi: -0.40, viirs: 0,
      note: "Hot border town, 20-month EEU meter (Wassie 2024). High tier; RWI/VIIRS fail to flag it."
    },
    {
      id: "tum", name: "Tum", country: "ET", lat: 6.2602, lon: 35.5193, kind: "validation",
      source: "metered", counts: { household: 384, commercial: 40, anchor: 26 }, adoption: 1.0, tier: "high",
      metered_kwh_month: 640 * 30.4, rwi: -0.32, viirs: 0,
      note: "24h-supply highland town, 20-month EEU meter (Wassie 2024). High tier."
    }
  ];
  if (typeof module !== "undefined" && module.exports) module.exports = SITES;
  root.GridcastSites = SITES;
})(typeof window !== "undefined" ? window : globalThis);
