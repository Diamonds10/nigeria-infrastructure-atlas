(function () {
  "use strict";

  var loadingEl = document.getElementById("loading");

  fetch("./assets/atlas_data.json?v=0.12.1")
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(runApp)
    .catch(function (err) {
      if (loadingEl) {
        loadingEl.querySelector(".loading-text").textContent = "Couldn't load atlas data — " + err.message;
      }
    });

  function runApp(ATLAS) {
  if (loadingEl) loadingEl.remove();

  function featureCount(sub) {
    if (sub && sub.deferred && typeof sub.deferred.feature_count === "number") {
      return sub.deferred.feature_count;
    }
    return (sub && sub.data && sub.data.features) ? sub.data.features.length : 0;
  }

  function deferredCacheUrl(sub) {
    if (!sub || !sub.deferred || !sub.deferred.url) return "";
    var version = (ATLAS.release && ATLAS.release.version) || "0";
    return sub.deferred.url + (sub.deferred.url.indexOf("?") === -1 ? "?v=" : "&v=") + encodeURIComponent(version);
  }

  var root = document.documentElement;
  function cssVar(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  // ---------------- Theme ----------------
  var themeBtn = document.getElementById("theme-toggle");
  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  themeBtn.addEventListener("click", function () {
    var next = currentTheme() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    themeBtn.textContent = next === "dark" ? "◑" : "◐";
    refreshAllLayerColors();
  });
  themeBtn.textContent = currentTheme() === "dark" ? "◑" : "◐";

  // ---------------- Category / sublayer meta ----------------
  var CAT_META = {
    resource: { colorVar: "--cat-resource" },
    infrastructure: { colorVar: "--cat-infrastructure" },
    environmental: { colorVar: "--cat-environmental" },
    security: { colorVar: "--cat-security" },
    demand: { colorVar: "--cat-demand" },
    connectivity: { colorVar: "--cat-connectivity" },
    renewables: { colorVar: "--cat-renewables" },
    context: { colorVar: "--cat-context" }
  };
  var CAT_ORDER = ["resource", "infrastructure", "environmental", "security", "demand", "connectivity", "renewables", "context"];

  // Every public sublayer has an explicit visual identity. Colour identifies
  // the asset class, shape identifies point types, and size/weight establishes
  // a usable hierarchy at national zoom.
  var SUB_STYLE = {
    fields_oil:          { colorVar: "--layer-fields-oil", shape: "droplet", size: 15 },
    fields_gas:          { colorVar: "--layer-fields-gas", shape: "flame", size: 16 },
    field_polygons_gas:  { colorVar: "--layer-field-polygons-gas", shape: "flame", size: 12, weight: 1.6, fillOpacity: 0.16 },
    field_polygons_mixed:{ colorVar: "--layer-field-polygons-mixed", shape: "hex", size: 12, weight: 1.3, fillOpacity: 0.12, dash: "5,3" },
    gas_pipelines:       { colorVar: "--layer-gas-pipelines", shape: "circle", size: 10, weight: 3.2 },
    oil_pipelines:       { colorVar: "--layer-oil-pipelines", shape: "circle", size: 10, weight: 2.8, dash: "8,5" },
    lng_terminals:       { colorVar: "--layer-lng-terminals", shape: "hex", size: 17 },
    power_plants:        { colorVar: "--layer-power-plants", shape: "bolt", size: 17 },
    hydro_plants:        { colorVar: "--layer-hydro-plants", shape: "droplet", size: 17 },
    refineries:          { colorVar: "--layer-refineries", shape: "factory", size: 18 },
    gas_infrastructure:  { colorVar: "--layer-gas-infrastructure", shape: "diamond", size: 14 },
    oil_spills:          { colorVar: "--layer-oil-spills", shape: "droplet", size: 12 },
    protected_areas:     { colorVar: "--layer-protected-areas", shape: "square", size: 10, weight: 1.1, fillOpacity: 0.15 },
    conflict_exposure:   { colorVar: "--layer-conflict-exposure", shape: "circle", size: 14 },
    demand_centers:      { colorVar: "--layer-demand-centers", shape: "target", size: 16 },
    roads:               { colorVar: "--layer-roads", shape: "circle", size: 9, weight: 2.4 },
    railways:            { colorVar: "--layer-railways", shape: "circle", size: 9, weight: 2.2, dash: "2,6" },
    rail_stations:       { colorVar: "--layer-rail-stations", shape: "train", size: 15 },
    power_grid:          { colorVar: "--layer-power-grid", shape: "circle", size: 9, weight: 1.7, dash: "3,4" },
    substations:         { colorVar: "--layer-substations", shape: "triangle", size: 14 },
    ports:               { colorVar: "--layer-ports", shape: "anchor", size: 17 },
    community_minigrids: { colorVar: "--layer-community-minigrids", shape: "sun", size: 18 },
    captive_offgrid_systems: { colorVar: "--layer-captive-offgrid", shape: "building", size: 17 },
    standalone_systems:  { colorVar: "--layer-standalone-systems", shape: "panel", size: 16 },
    interconnected_minigrids: { colorVar: "--layer-interconnected-minigrids", shape: "network", size: 18 },
    population_access:   { colorVar: "--layer-population-access", shape: "circle", size: 10 },
    settlements:         { colorVar: "--layer-settlements", shape: "circle", size: 11 }
  };
  function visualStyle(catKey, subKey) {
    return SUB_STYLE[subKey] || {
      colorVar: CAT_META[catKey].colorVar,
      shape: "circle",
      size: 13
    };
  }
  var DEFAULT_ON = {
    fields_oil: true,
    fields_gas: true,
    field_polygons_gas: false,
    field_polygons_mixed: false,
    gas_pipelines: true,
    oil_pipelines: true,
    lng_terminals: true,
    power_plants: true,
    hydro_plants: true,
    refineries: true,
    gas_infrastructure: true,
    oil_spills: false,
    protected_areas: false,
    conflict_exposure: false,
    demand_centers: true,
    roads: false,
    railways: false,
    rail_stations: true,
    power_grid: false,
    substations: true,
    ports: true,
    community_minigrids: true,
    captive_offgrid_systems: true,
    // Empty by design (programme aggregates live in state profiles only).
    standalone_systems: false,
    interconnected_minigrids: true,
    population_access: false,
    settlements: false
  };

  var STATUS_MAP = {
    operating: "good", active: "good", "in use": "good",
    construction: "warning", "in development": "warning", "pre-construction": "warning", rehabilitation: "warning",
    proposed: "serious", planned: "serious", announced: "serious", discovered: "serious",
    mothballed: "critical", cancelled: "critical", shelved: "critical", "shut in": "critical", retired: "critical"
  };

  // ---------------- SVG glyph builder ----------------
  // filled=true (operating/unknown status): solid category-color fill.
  // filled=false (non-operating: construction/proposed/mothballed/etc.):
  // hollow outline only, same hue, so category identity is never lost --
  // status reads as "weight" (solid vs open) rather than a second color.
  function shapeSvg(shape, color, size, filled) {
    size = size || 13;
    var s = size, h = size / 2;
    var inner = "";
    var fillValue = filled === false ? "none" : color;
    var strokeValue = filled === false ? color : "rgba(0,0,0,0.35)";
    var strokeWidth = filled === false ? "1.6" : "1";
    switch (shape) {
      case "square":
        inner = '<rect x="2" y="2" width="' + (s-4) + '" height="' + (s-4) + '" rx="1.5" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/>';
        break;
      case "triangle":
        inner = '<polygon points="' + h + ',2 ' + (s-2) + ',' + (s-2) + ' 2,' + (s-2) + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "diamond":
        inner = '<polygon points="' + h + ',1 ' + (s-1) + ',' + h + ' ' + h + ',' + (s-1) + ' 1,' + h + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "hex":
        var pts = [];
        for (var i = 0; i < 6; i++) {
          var ang = Math.PI / 180 * (60 * i - 30);
          pts.push((h + (h - 1.5) * Math.cos(ang)).toFixed(1) + "," + (h + (h - 1.5) * Math.sin(ang)).toFixed(1));
        }
        inner = '<polygon points="' + pts.join(" ") + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "star":
        var spts = [];
        for (var k = 0; k < 10; k++) {
          var r = k % 2 === 0 ? h - 1 : (h - 1) * 0.45;
          var a = Math.PI / 180 * (36 * k - 90);
          spts.push((h + r * Math.cos(a)).toFixed(1) + "," + (h + r * Math.sin(a)).toFixed(1));
        }
        inner = '<polygon points="' + spts.join(" ") + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "plus":
        var arm = s * 0.2;
        inner = '<path d="M ' + (h-arm) + ' 2 L ' + (h+arm) + ' 2 L ' + (h+arm) + ' ' + (h-arm) + ' L ' + (s-2) + ' ' + (h-arm) + ' L ' + (s-2) + ' ' + (h+arm) + ' L ' + (h+arm) + ' ' + (h+arm) + ' L ' + (h+arm) + ' ' + (s-2) + ' L ' + (h-arm) + ' ' + (s-2) + ' L ' + (h-arm) + ' ' + (h+arm) + ' L 2 ' + (h+arm) + ' L 2 ' + (h-arm) + ' L ' + (h-arm) + ' ' + (h-arm) + ' Z" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "droplet":
        inner = '<path d="M ' + h + ' 1 C ' + (h-1) + ' 3 3 ' + (h+2) + ' 3 ' + (s-5) + ' C 3 ' + (s-3) + ' ' + (h-1) + ' ' + (s-1) + ' ' + h + ' ' + (s-1) + ' C ' + (s-h+1) + ' ' + (s-1) + ' ' + (s-3) + ' ' + (s-3) + ' ' + (s-3) + ' ' + (s-5) + ' C ' + (s-3) + ' ' + (h+2) + ' ' + (h+1) + ' 3 ' + h + ' 1 Z" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/>';
        break;
      case "flame":
        inner = '<path d="M ' + h + ' 1 C ' + (h+2) + ' 4 ' + (s-3) + ' 6 ' + (s-3) + ' ' + (h+2) + ' C ' + (s-3) + ' ' + (s-2) + ' ' + (h+2) + ' ' + (s-1) + ' ' + h + ' ' + (s-1) + ' C 4 ' + (s-1) + ' 2 ' + (s-4) + ' 3 ' + (h+1) + ' C 4 ' + (h-1) + ' ' + (h-1) + ' ' + (h-2) + ' ' + h + ' 1 Z" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/>';
        break;
      case "bolt":
        inner = '<polygon points="' + (h+1) + ',1 3,' + (h+1) + ' ' + (h-1) + ',' + (h+1) + ' ' + (h-2) + ',' + (s-1) + ' ' + (s-3) + ',' + (h-2) + ' ' + (h+1) + ',' + (h-2) + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "factory":
        inner = '<path d="M2 ' + (s-2) + ' V' + h + ' L' + (h-1) + ' ' + (h-2) + ' V' + h + ' L' + (s-4) + ' ' + (h-2) + ' V3 H' + (s-2) + ' V' + (s-2) + ' Z" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "target":
        inner = '<circle cx="' + h + '" cy="' + h + '" r="' + (h-2) + '" fill="' + fillValue + '" stroke="' + color + '" stroke-width="1.4"/><circle cx="' + h + '" cy="' + h + '" r="' + (h*0.34) + '" fill="' + (filled === false ? "none" : "#fff") + '" stroke="' + color + '" stroke-width="1.2"/>';
        break;
      case "train":
        inner = '<rect x="2" y="1.5" width="' + (s-4) + '" height="' + (s-5) + '" rx="2.5" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/><path d="M4 ' + (h-1) + ' H' + (s-4) + ' M5 ' + (s-3) + ' L3 ' + (s-1) + ' M' + (s-5) + ' ' + (s-3) + ' L' + (s-3) + ' ' + (s-1) + '" fill="none" stroke="' + color + '" stroke-width="1.2"/>';
        break;
      case "anchor":
        inner = '<path d="M' + h + ' 2 V' + (s-4) + ' M' + (h-3) + ' 5 A3 3 0 1 0 ' + (h+3) + ' 5 A3 3 0 1 0 ' + (h-3) + ' 5 M2 ' + (h+2) + ' C3 ' + (s-2) + ' ' + (h-2) + ' ' + (s-1) + ' ' + h + ' ' + (s-3) + ' C' + (h+2) + ' ' + (s-1) + ' ' + (s-3) + ' ' + (s-2) + ' ' + (s-2) + ' ' + (h+2) + '" fill="none" stroke="' + color + '" stroke-width="1.8" stroke-linecap="round"/>';
        break;
      case "sun":
        inner = '<circle cx="' + h + '" cy="' + h + '" r="' + (h*0.34) + '" fill="' + fillValue + '" stroke="' + color + '" stroke-width="1.2"/><path d="M' + h + ' 1 V3 M' + h + ' ' + (s-3) + ' V' + (s-1) + ' M1 ' + h + ' H3 M' + (s-3) + ' ' + h + ' H' + (s-1) + ' M3 3 L4.5 4.5 M' + (s-3) + ' 3 L' + (s-4.5) + ' 4.5 M3 ' + (s-3) + ' L4.5 ' + (s-4.5) + ' M' + (s-3) + ' ' + (s-3) + ' L' + (s-4.5) + ' ' + (s-4.5) + '" fill="none" stroke="' + color + '" stroke-width="1.4" stroke-linecap="round"/>';
        break;
      case "building":
        inner = '<path d="M3 ' + (s-2) + ' V4 L' + h + ' 1 L' + (s-3) + ' 4 V' + (s-2) + ' Z" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/><path d="M' + (h-2) + ' ' + (s-2) + ' V' + (h+2) + ' H' + (h+2) + ' V' + (s-2) + '" fill="none" stroke="' + color + '" stroke-width="1.1"/>';
        break;
      case "panel":
        inner = '<polygon points="2,4 ' + (s-3) + ',2 ' + (s-2) + ',' + (s-5) + ' 3,' + (s-3) + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/><path d="M' + h + ' 3 L' + h + ' ' + (s-4) + ' M2.5 ' + h + ' L' + (s-2.5) + ' ' + (h-1) + ' M' + h + ' ' + (s-4) + ' V' + (s-2) + ' M' + (h-3) + ' ' + (s-2) + ' H' + (h+3) + '" fill="none" stroke="' + color + '" stroke-width="1"/>';
        break;
      case "network":
        inner = '<path d="M4 4 L' + (s-4) + ' 4 L' + h + ' ' + (s-4) + ' Z" fill="none" stroke="' + color + '" stroke-width="1.4"/><circle cx="4" cy="4" r="2.2" fill="' + fillValue + '" stroke="' + color + '" stroke-width="1"/><circle cx="' + (s-4) + '" cy="4" r="2.2" fill="' + fillValue + '" stroke="' + color + '" stroke-width="1"/><circle cx="' + h + '" cy="' + (s-4) + '" r="2.2" fill="' + fillValue + '" stroke="' + color + '" stroke-width="1"/>';
        break;
      default:
        inner = '<circle cx="' + h + '" cy="' + h + '" r="' + (h - 2) + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/>';
    }
    return '<svg width="' + s + '" height="' + s + '" viewBox="0 0 ' + s + ' ' + s + '" xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>';
  }

  function divIcon(shape, color, filled, size) {
    size = size || 14;
    return L.divIcon({
      html: shapeSvg(shape, color, size, filled),
      className: "atlas-marker",
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -(size / 2)]
    });
  }

  // Resolves a feature's status field to whether it should render as
  // "operating" (solid marker) or not (hollow marker). Layers with no status
  // field at all default to solid, since there's nothing to distinguish.
  function isOperating(props) {
    var raw = (props.status || props.STATUS || "").toString().toLowerCase();
    if (!raw) return true;
    if (raw.indexOf("operat") !== -1 || raw.indexOf("active") !== -1 || raw.indexOf("in use") !== -1) return true;
    return false;
  }

  // ---------------- Popup builder ----------------
  var FIELD_LABELS = {
    project: "Project", status: "Status", operator: "Operator", owner: "Owner",
    fuel_type: "Fuel type", discovery_year: "Discovered", start_year: "Start year",
    parent: "Operator/Owner", capacity: "Capacity", capacity_units: "Units", units: "Units",
    unit: "Unit", province: "State", technology: "Technology",
    capacity_bpd: "Capacity (bpd)", commissioned_year: "Commissioned", state: "State",
    NAME: "Name", DESIG_ENG: "Designation", IUCN_CAT: "IUCN category",
    GIS_AREA: "Area (km²)", STATUS: "Status", STATUS_YR: "Since", GOV_TYPE: "Governance",
    demand_center: "Site", category: "Category", state_or_region: "State/Region", notes: "Notes",
    highway: "Road class", name: "Name", ref: "Ref", surface: "Surface", lanes: "Lanes",
    railway: "Type", gauge: "Gauge", power: "Type", voltage: "Voltage",
    PORT_NAME: "Port", HARBORSIZE: "Harbor size", HARBORTYPE: "Harbor type",
    CARGOWHARF: "Cargo wharf", CRANEFIXED: "Fixed crane", RAILWAY: "Rail service", MAX_VESSEL: "Max vessel size",
    asset_id: "Asset ID", asset_name: "Site", lga: "LGA", capacity_kw: "Capacity (kW)", customers_served: "Customers served",
    financing_source: "Financing", source_url: "Source",
    field_type: "Field type", in_goget_fields: "Also in GOGET inventory",
    type: "Asset type", company: "Operator", location: "Location",
    design_cap: "Design capacity", date_of_co: "Commissioned",
    asset_type: "Asset type", program_name: "Programme",
    distributed_energy_class: "Distributed-energy class",
    classification_basis: "Classification basis",
    classification_confidence: "Classification confidence",
    community: "Community / site", owner_operator: "Owner / operator",
    geocode_precision: "Coordinate precision",
    coordinate_source: "Coordinate source", source_name: "Evidence source",
    source_date_accessed: "Source checked", evidence_level: "Evidence level",
    record_origin: "Registry origin",
    cell_id: "Aggregate cell", period: "Period", event_count: "Organized-violence events",
    fatalities_best: "Fatalities (best estimate)", fatalities_low: "Fatalities (low estimate)",
    fatalities_high: "Fatalities (high estimate)", first_year: "First year",
    latest_year: "Latest year", state_based_events: "State-based events",
    non_state_events: "Non-state events", one_sided_events: "One-sided events",
    source_states: "Source-assigned states",
    population_estimate: "Modelled population", settlement_count: "Settlement clusters",
    population_with_nightlight_signal: "Population with night-light signal",
    population_without_nightlight_signal: "Population without night-light signal",
    nightlight_population_share_pct: "Night-light population share (%)",
    total_buildings: "Mapped buildings", modeled_demand: "Modelled demand",
    population_weighted_distance_transmission_km: "Population-weighted transmission distance (km)",
    population_weighted_distance_gridlight_km: "Population-weighted grid-light distance (km)",
    settlement_name: "Settlement", population: "Modelled population",
    state_population_rank: "Population rank in state", num_buildings: "Mapped buildings",
    nightlight_signal: "Night-light signal",
    distance_to_existing_transmission_lines: "Distance to transmission (km)",
    distance_to_existing_hv_transmission_lines: "Distance to HV transmission (km)",
    distance_to_gridlight_targets: "Distance to grid-light target (km)",
    main_road_access: "Main-road access", dist_main_road_km: "Distance to main road (km)",
    has_education_facility: "Education facility signal", has_health_facility: "Health facility signal",
    incidentnumber: "Incident number", incidentdate: "Incident date",
    incident_year: "Incident year", incident_date_quality: "Date quality",
    status_label: "Report status", cause_label: "Reported cause",
    is_sabotage_attributed: "Sabotage-attributed", contaminant_label: "Contaminant",
    facility_label: "Facility type", habitat_label: "Habitat", estimatedquantity: "Est. quantity (bbl)",
    state_label: "State", sitelocationname: "Location"
  };
  var SKIP_IN_ROWS = { project: 1, url: 1, NAME: 1, demand_center: 1, name: 1, PORT_NAME: 1, status: 1, STATUS: 1, asset_name: 1, source_url: 1, sitelocationname: 1 };

  function titleOf(props) {
    return props._label || props.project || props.NAME || props.demand_center || props.name || props.PORT_NAME || props.asset_name || "Untitled asset";
  }
  function statusOf(props) {
    var raw = (props.status || props.STATUS || "").toString().toLowerCase();
    for (var key in STATUS_MAP) { if (raw.indexOf(key) !== -1) return { raw: props.status || props.STATUS, level: STATUS_MAP[key] }; }
    return raw ? { raw: props.status || props.STATUS, level: null } : null;
  }

  function popupHtml(sublayerLabel, catColorVar, props) {
    var title = titleOf(props);
    var st = statusOf(props);
    var html = '<div class="popup-card">';
    html += '<div class="p-eyebrow" style="color:var(' + catColorVar + ')">' + sublayerLabel + '</div>';
    html += '<div class="p-title">' + escapeHtml(title) + '</div>';
    if (st) {
      var lvl = st.level;
      var color = lvl ? "var(--status-" + lvl + ")" : "var(--text-muted)";
      html += '<div class="p-status" style="background:color-mix(in srgb, ' + color + ' 16%, transparent); color:' + color + '"><span class="dot" style="background:' + color + '"></span>' + escapeHtml(st.raw) + '</div>';
    }
    html += '<div class="p-rows">';
    var keys = Object.keys(props).filter(function (k) { return !SKIP_IN_ROWS[k] && k.charAt(0) !== "_" && props[k] !== null && props[k] !== undefined && props[k] !== ""; });
    keys.forEach(function (k) {
      var label = FIELD_LABELS[k] || k;
      var val = props[k];
      html += '<div class="p-row"><span class="p-k">' + escapeHtml(label) + '</span><span class="p-v">' + escapeHtml(String(val)) + '</span></div>';
    });
    html += '</div>';
    var link = props.url || props.source_url;
    if (link) {
      html += '<a class="p-link" href="' + escapeAttr(link) + '" target="_blank" rel="noopener">View source ↗</a>';
    }
    html += '</div>';
    return html;
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]; }); }
  function escapeAttr(s) { return escapeHtml(s); }
  function filenameFromUrl(url) {
    var clean = String(url).split(/[?#]/)[0];
    var parts = clean.split("/");
    return parts[parts.length - 1] || "download.csv";
  }

  // ---------------- Map init ----------------
  var map = L.map("map", { zoomControl: false, minZoom: 5, maxZoom: 16, attributionControl: false });
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.control.attribution({ position: "bottomleft", prefix: false }).addTo(map)
    .addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions" target="_blank" rel="noopener">CARTO</a>');
  var NIGERIA_BOUNDS = [[3.9, 2.5], [14.0, 14.8]];
  map.fitBounds(NIGERIA_BOUNDS);

  // "_nolabels" variants -- the app draws its own permanent state-name
  // tooltips below, so the basemap's own place-name labels would otherwise
  // double up with ours (e.g. "Kaduna" rendered twice, at slightly different
  // positions/styles).
  var TILE_URLS = {
    light: "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
    dark: "https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
  };
  var tileLayer = L.tileLayer(TILE_URLS[currentTheme() === "dark" ? "dark" : "light"], {
    maxZoom: 20,
    subdomains: "abcd"
  }).addTo(map);

  var selectedState = "";
  var stateLayersByName = {};
  function stateStyle(feature) {
    var name = feature.properties && feature.properties.name;
    var selected = selectedState && name === selectedState;
    return {
      color: selected ? cssVar("--accent") : cssVar("--line"),
      weight: selected ? 2.8 : 1.4,
      fillColor: selected ? cssVar("--accent") : cssVar("--paper-100"),
      // A heavy fill on every unselected state (i.e. the whole country, by
      // default) read as a grey "shadow" cast over the whole map -- this is
      // now just enough to give the boundary a filled look, with the
      // selected state's highlight staying prominent for contrast.
      fillOpacity: selected ? 0.22 : 0.06
    };
  }

  var statesLayer = L.geoJSON(ATLAS.states, {
    style: stateStyle,
    onEachFeature: function (feature, lyr) {
      var name = feature.properties && feature.properties.name;
      if (!name) return;
      stateLayersByName[name] = lyr;
      lyr.bindTooltip(name, { permanent: true, direction: "center", className: "state-label", interactive: false });
      lyr.on("click", function () { selectState(name, true); });
    }
  }).addTo(map);
  statesLayer.bringToBack();
  tileLayer.bringToBack();

  // ---------------- Click highlight (pin drop) ----------------
  function pinIconHtml() {
    var accent = cssVar("--accent");
    return (
      '<div class="highlight-pin">' +
        '<div class="pulse-ring"></div>' +
        '<div class="pin-body">' +
          '<svg width="34" height="46" viewBox="0 0 34 46" xmlns="http://www.w3.org/2000/svg">' +
            '<path d="M17 1 C9.8 1 4 6.8 4 14 C4 24 17 45 17 45 C17 45 30 24 30 14 C30 6.8 24.2 1 17 1 Z" fill="' + accent + '" stroke="rgba(0,0,0,0.3)" stroke-width="1"/>' +
            '<circle cx="17" cy="14" r="5.5" fill="#fff"/>' +
          '</svg>' +
        '</div>' +
      '</div>'
    );
  }
  var highlightMarker = L.marker([0, 0], {
    icon: L.divIcon({ html: pinIconHtml(), className: "highlight-pin-wrap", iconSize: [34, 46], iconAnchor: [17, 45] }),
    interactive: false,
    keyboard: false,
    zIndexOffset: 1000
  });
  map.on("popupopen", function (e) {
    var latlng = e.popup.getLatLng();
    if (!latlng) return;
    highlightMarker.setIcon(L.divIcon({ html: pinIconHtml(), className: "highlight-pin-wrap", iconSize: [34, 46], iconAnchor: [17, 45] }));
    highlightMarker.setLatLng(latlng);
    if (!map.hasLayer(highlightMarker)) highlightMarker.addTo(map);
  });
  map.on("popupclose", function () {
    if (map.hasLayer(highlightMarker)) map.removeLayer(highlightMarker);
  });

  // ---------------- Build layers ----------------
  var registry = {}; // subKey -> { leafletLayer, catKey, meta, count }
  var allFeaturesIndex = []; // for search: {label, subKey, catKey, feature, latlng}

  function lineStyle(style) {
    return {
      color: cssVar(style.colorVar),
      weight: style.weight || 2.2,
      opacity: 0.88,
      dashArray: style.dash || null,
      lineCap: "round"
    };
  }

  function polygonStyle(style) {
    var color = cssVar(style.colorVar);
    return {
      color: color,
      weight: style.weight || 1.2,
      opacity: 0.85,
      dashArray: style.dash || null,
      fillColor: color,
      fillOpacity: style.fillOpacity === undefined ? 0.18 : style.fillOpacity
    };
  }

  function buildSublayer(catKey, subKey, sub) {
    var style = visualStyle(catKey, subKey);
    var color = cssVar(style.colorVar);
    var geomType = sub.geomType;
    var layer;

    if (geomType === "point") {
      layer = L.geoJSON(sub.data, {
        pointToLayer: function (feature, latlng) {
          if (subKey === "population_access" || subKey === "conflict_exposure") {
            var magnitude = subKey === "population_access"
              ? Number(feature.properties.population_estimate || 0)
              : Number(feature.properties.event_count || 0);
            var radius = subKey === "population_access"
              ? Math.max(3, Math.min(12, 2 + Math.log10(Math.max(magnitude, 1))))
              : Math.max(4, Math.min(14, 3 + 2.4 * Math.log10(Math.max(magnitude, 1))));
            var contextMarker = L.circleMarker(latlng, {
              radius: radius,
              color: color,
              weight: subKey === "conflict_exposure" ? 1.2 : 0.8,
              fillColor: color,
              fillOpacity: subKey === "conflict_exposure" ? 0.62 : 0.48
            });
            contextMarker._infraxisContextGrid = true;
            return contextMarker;
          }
          var filled = isOperating(feature.properties);
          var marker = L.marker(latlng, {
            icon: divIcon(style.shape, color, filled, style.size)
          });
          marker._infraxisFilled = filled;
          return marker;
        },
        onEachFeature: function (feature, lyr) {
          lyr.bindPopup(popupHtml(sub.label, style.colorVar, feature.properties), { maxWidth: 300 });
          var lbl = titleOf(feature.properties);
          if (lbl && subKey !== "population_access" && subKey !== "conflict_exposure") {
            allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr, feature: feature });
          }
        }
      });
    } else if (geomType === "line") {
      layer = L.geoJSON(sub.data, {
        style: function () { return lineStyle(style); },
        // Guards against any stray Point feature inside a line-typed sublayer --
        // without this, Leaflet silently falls back to its (unstyled, broken-
        // image) default marker icon instead of using our design system.
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, {
            icon: divIcon(style.shape, color, true, style.size)
          });
        },
        onEachFeature: function (feature, lyr) {
          lyr.bindPopup(popupHtml(sub.label, style.colorVar, feature.properties), { maxWidth: 300 });
          var lbl = titleOf(feature.properties);
          if (lbl && lbl !== "Untitled asset") allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr, feature: feature });
        }
      });
    } else {
      layer = L.geoJSON(sub.data, {
        style: function () { return polygonStyle(style); },
        // Same guard as above -- WDPA in particular mixes polygon boundaries
        // with point-only records (protected areas with no mapped footprint).
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, {
            icon: divIcon(style.shape, color, true, style.size)
          });
        },
        onEachFeature: function (feature, lyr) {
          lyr.bindPopup(popupHtml(sub.label, style.colorVar, feature.properties), { maxWidth: 300 });
          var lbl = titleOf(feature.properties);
          if (lbl) allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr, feature: feature });
        }
      });
    }
    if (subKey === "oil_spills" && typeof L.markerClusterGroup === "function") {
      var spillMarkers = [];
      layer.eachLayer(function (marker) { spillMarkers.push(marker); });
      var clustered = L.markerClusterGroup({
        chunkedLoading: true,
        chunkInterval: 100,
        chunkDelay: 30,
        removeOutsideVisibleBounds: true,
        showCoverageOnHover: false,
        maxClusterRadius: 54,
        iconCreateFunction: function (cluster) {
          var count = cluster.getChildCount();
          var size = count < 100 ? 34 : count < 1000 ? 40 : 46;
          var scaleClass = count < 100 ? "" : count < 1000 ? " spill-cluster-medium" : " spill-cluster-large";
          return L.divIcon({
            html: '<div class="spill-cluster' + scaleClass + '" style="width:' + size + 'px;height:' + size + 'px">' +
              count.toLocaleString() + '</div>',
            className: "",
            iconSize: [size, size]
          });
        }
      });
      clustered.addLayers(spillMarkers);
      layer = clustered;
    }
    var children = [];
    layer.eachLayer(function (child) { children.push(child); });
    return { layer: layer, children: children };
  }

  function ensureSublayerLoaded(subKey) {
    var entry = registry[subKey];
    if (!entry) return Promise.resolve(null);
    var sub = ATLAS.layers[entry.catKey].sublayers[subKey];
    if (!sub.deferred || sub.deferred.loaded) return Promise.resolve(entry);
    if (sub.deferred.loading) return sub.deferred.loading;
    var countEl = document.querySelector('[data-sub-count="' + subKey + '"]');
    if (countEl) countEl.textContent = "loading…";
    sub.deferred.loading = fetch(deferredCacheUrl(sub))
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (collection) {
        var wasOnMap = map.hasLayer(entry.leafletLayer);
        if (wasOnMap) map.removeLayer(entry.leafletLayer);
        allFeaturesIndex = allFeaturesIndex.filter(function (item) {
          return item.subKey !== subKey;
        });
        sub.data = {
          type: "FeatureCollection",
          features: (collection && collection.features) || []
        };
        var built = buildSublayer(entry.catKey, subKey, sub);
        registry[subKey] = {
          leafletLayer: built.layer,
          children: built.children,
          catKey: entry.catKey,
          geomType: sub.geomType,
          label: sub.label,
          count: featureCount(sub)
        };
        sub.deferred.loaded = true;
        sub.deferred.loading = null;
        if (typeof applyFilters === "function") applyFilters(false);
        else updateVisibleStat();
        if (wasOnMap) registry[subKey].leafletLayer.addTo(map);
        updateVisibleStat();
        return registry[subKey];
      })
      .catch(function (err) {
        sub.deferred.loading = null;
        if (countEl) countEl.textContent = featureCount(sub).toLocaleString();
        throw err;
      });
    return sub.deferred.loading;
  }

  var totalFeatures = 0;
  CAT_ORDER.forEach(function (catKey) {
    var cat = ATLAS.layers[catKey];
    if (!cat) return;
    Object.keys(cat.sublayers).forEach(function (subKey) {
      var sub = cat.sublayers[subKey];
      var count = featureCount(sub);
      totalFeatures += count;
      var built = buildSublayer(catKey, subKey, sub);
      registry[subKey] = {
        leafletLayer: built.layer, children: built.children,
        catKey: catKey, geomType: sub.geomType, label: sub.label, count: count
      };
      if (DEFAULT_ON[subKey]) {
        if (sub.deferred) {
          ensureSublayerLoaded(subKey).then(function (loaded) {
            if (loaded) loaded.leafletLayer.addTo(map);
            updateVisibleStat();
          });
        } else {
          built.layer.addTo(map);
        }
      }
    });
  });
  document.getElementById("stat-total").textContent = totalFeatures.toLocaleString();

  function refreshAllLayerColors() {
    tileLayer.setUrl(TILE_URLS[currentTheme() === "dark" ? "dark" : "light"]);
    // rebuild point icons & line styles to match new theme's CSS vars
    CAT_ORDER.forEach(function (catKey) {
      var cat = ATLAS.layers[catKey];
      if (!cat) return;
      Object.keys(cat.sublayers).forEach(function (subKey) {
        var entry = registry[subKey];
        if (!entry) return;
        var style = visualStyle(catKey, subKey);
        var color = cssVar(style.colorVar);
        if (entry.geomType === "point") {
          entry.leafletLayer.eachLayer(function (lyr) {
            if (lyr._infraxisContextGrid && lyr.setStyle) {
              lyr.setStyle({ color: color, fillColor: color });
            } else if (lyr.setIcon) {
              lyr.setIcon(divIcon(style.shape, color, lyr._infraxisFilled, style.size));
            }
          });
        } else if (entry.geomType === "line") {
          entry.leafletLayer.setStyle(lineStyle(style));
          entry.leafletLayer.eachLayer(function (lyr) {
            if (lyr.setIcon) {
              lyr.setIcon(divIcon(style.shape, color, true, style.size));
            }
          });
        } else {
          entry.leafletLayer.setStyle(polygonStyle(style));
          entry.leafletLayer.eachLayer(function (lyr) {
            if (lyr.setIcon) {
              lyr.setIcon(divIcon(style.shape, color, true, style.size));
            }
          });
        }
      });
    });
    statesLayer.setStyle(stateStyle);
  }

  // ---------------- Panel UI ----------------
  var CAVEAT_BY_SUB = {
    fields_oil: "33 points that GOGET classifies oil-only. The source fuel label is not an authoritative reservoir classification; known gas-producing sites such as Soku, Bonny, and Gbaran are labelled oil.",
    fields_gas: "147 non-overlapping points that GOGET classifies gas-only or oil-and-gas. This is a much better gas-producing footprint than the former two-record gas-only display, but the source still mislabels some known gas sites as oil.",
    conflict_exposure: "Historical UCDP organized-violence events aggregated to half-degree cells for 2016–2025. This is not a live threat feed. Exact event points, actor names, narratives, and source text are not republished."
  };
  var listEl = document.getElementById("category-list");
  var CAT_LABELS = { resource: "Resource", infrastructure: "Infrastructure", environmental: "Environmental", security: "Security Context", demand: "Demand", connectivity: "Connectivity", renewables: "Distributed Energy", context: "People & Access" };

  CAT_ORDER.forEach(function (catKey) {
    var cat = ATLAS.layers[catKey];
    if (!cat) return;
    var group = document.createElement("div");
    group.className = "category-group";
    var subKeys = Object.keys(cat.sublayers);
    var catCount = subKeys.reduce(function (s, k) { return s + featureCount(cat.sublayers[k]); }, 0);

    var head = document.createElement("div");
    head.className = "category-head";
    head.innerHTML =
      '<span class="swatch" style="background:var(' + CAT_META[catKey].colorVar + ')"></span>' +
      '<span class="cname">' + CAT_LABELS[catKey] + '</span>' +
      '<span class="ccount">' + catCount.toLocaleString() + '</span>' +
      '<svg class="chev" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>';
    head.addEventListener("click", function () { group.classList.toggle("collapsed"); });
    group.appendChild(head);

    var subWrap = document.createElement("div");
    subWrap.className = "sublayers";
    subKeys.forEach(function (subKey) {
      var sub = cat.sublayers[subKey];
      var row = document.createElement("label");
      row.className = "sub-row";
      var style = visualStyle(catKey, subKey);
      var color = cssVar(style.colorVar);
      var glyphHtml = sub.geomType === "point"
        ? shapeSvg(style.shape, color, Math.min(style.size || 12, 16))
        : sub.geomType === "line"
          ? '<svg width="18" height="12" viewBox="0 0 18 12"><line x1="1" y1="6" x2="17" y2="6" stroke="' + color + '" stroke-width="' + (style.weight || 2.2) + '" stroke-dasharray="' + (style.dash || "") + '" stroke-linecap="round"/></svg>'
          : '<svg width="16" height="12" viewBox="0 0 16 12"><rect x="1" y="1" width="14" height="10" rx="2" fill="' + color + '" opacity="' + (style.fillOpacity || 0.18) + '" stroke="' + color + '" stroke-width="' + (style.weight || 1.2) + '" stroke-dasharray="' + (style.dash || "") + '"/></svg>';
      var caveat = CAVEAT_BY_SUB[subKey];
      var caveatHtml = caveat ? ' <span class="caveat-flag" title="' + escapeAttr(caveat) + '">⚠</span>' : '';
      row.innerHTML =
        '<input type="checkbox" ' + (DEFAULT_ON[subKey] ? "checked" : "") + ' data-sub="' + subKey + '"/>' +
        '<span class="glyph">' + glyphHtml + '</span>' +
        '<span class="sname">' + sub.label + caveatHtml + '</span>' +
        '<span class="scount" data-sub-count="' + subKey + '">' + featureCount(sub).toLocaleString() + '</span>';
      subWrap.appendChild(row);
      row.querySelector("input").addEventListener("change", function (e) {
        var entry = registry[subKey];
        if (e.target.checked) {
          ensureSublayerLoaded(subKey).then(function (loaded) {
            if (!loaded) return;
            if (!e.target.checked) return;
            loaded.leafletLayer.addTo(map);
            if (typeof applyFilters === "function") applyFilters(false);
            updateVisibleStat();
          }).catch(function (err) {
            e.target.checked = false;
            window.alert("Could not load layer: " + err.message);
          });
        } else {
          map.removeLayer(entry.leafletLayer);
          updateVisibleStat();
        }
      });
    });
    group.appendChild(subWrap);
    listEl.appendChild(group);
  });

  function updateVisibleStat() {
    var n = 0;
    Object.keys(registry).forEach(function (k) {
      var entry = registry[k];
      var filteredCount = entry.children.reduce(function (sum, child) {
        return sum + (entry.leafletLayer.hasLayer(child) ? 1 : 0);
      }, 0);
      var countEl = document.querySelector('[data-sub-count="' + k + '"]');
      if (countEl) countEl.textContent = filteredCount === entry.count
        ? entry.count.toLocaleString()
        : filteredCount.toLocaleString() + "/" + entry.count.toLocaleString();
      if (map.hasLayer(entry.leafletLayer)) n += filteredCount;
    });
    document.getElementById("stat-visible").textContent = n.toLocaleString();
  }
  updateVisibleStat();

  // ---------------- State intelligence ----------------
  var stateSelect = document.getElementById("state-select");
  var stateProfileEl = document.getElementById("state-profile");
  var downloadStateButton = document.getElementById("download-state");
  var downloadReportButton = document.getElementById("download-report");
  var copyStateLinkButton = document.getElementById("copy-state-link");
  var stateNames = Object.keys(ATLAS.state_profiles || {}).filter(function (name) { return name !== "Nigeria"; }).sort();

  stateNames.forEach(function (name) {
    var option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    stateSelect.appendChild(option);
  });

  function formatNumber(value, maximumFractionDigits) {
    return Number(value || 0).toLocaleString(undefined, {
      maximumFractionDigits: maximumFractionDigits === undefined ? 0 : maximumFractionDigits
    });
  }

  function profileMetric(value, label) {
    return '<div class="profile-metric"><strong>' + formatNumber(value) + '</strong><span>' + escapeHtml(label) + '</span></div>';
  }

  function profileChart(title, values, limit) {
    var rows = Object.keys(values || {}).map(function (label) {
      return { label: label, value: Number(values[label] || 0) };
    }).filter(function (item) { return item.value > 0; })
      .sort(function (a, b) { return b.value - a.value || a.label.localeCompare(b.label); })
      .slice(0, limit || 6);
    if (!rows.length) return "";
    var maximum = rows[0].value;
    return '<div class="profile-chart"><h4>' + escapeHtml(title) + '</h4>' +
      rows.map(function (item) {
        return '<div class="chart-row"><span class="chart-label" title="' + escapeAttr(item.label) + '">' +
          escapeHtml(item.label) + '</span><span class="chart-track"><span class="chart-fill" style="width:' +
          Math.max(2, 100 * item.value / maximum).toFixed(1) + '%"></span></span><span class="chart-value">' +
          formatNumber(item.value) + '</span></div>';
      }).join("") + '</div>';
  }

  function profileTimelineChart(title, values, limit) {
    var rows = Object.keys(values || {}).map(function (label) {
      return { label: label, value: Number(values[label] || 0) };
    }).filter(function (item) { return item.value > 0; })
      .sort(function (a, b) { return Number(a.label) - Number(b.label); });
    rows = rows.slice(-1 * (limit || 10));
    if (!rows.length) return "";
    var maximum = Math.max.apply(null, rows.map(function (item) { return item.value; }));
    return '<div class="profile-chart"><h4>' + escapeHtml(title) + '</h4>' +
      rows.map(function (item) {
        return '<div class="chart-row"><span class="chart-label">' +
          escapeHtml(item.label) + '</span><span class="chart-track"><span class="chart-fill" style="width:' +
          Math.max(2, 100 * item.value / maximum).toFixed(1) + '%"></span></span><span class="chart-value">' +
          formatNumber(item.value) + '</span></div>';
      }).join("") + '</div>';
  }

  function renderStateProfile() {
    var profileName = selectedState || "Nigeria";
    var profile = ATLAS.state_profiles[profileName];
    if (!profile) return;
    var counts = profile.counts;
    var capacity = profile.capacity;
    var peopleAccess = profile.people_access || {};
    var minigridCoverage = profile.minigrid_coverage || {};
    var standaloneProgramme = profile.standalone_solar_programme || {};
    var securityIntelligence = profile.security_intelligence || {};
    var spillIntelligence = profile.oil_spill_intelligence || {};
    var distributedMix = {
      "Community mini-grid": counts.community_minigrids,
      "Captive / institutional": counts.captive_offgrid_systems,
      "Standalone": counts.standalone_systems,
      "Interconnected": counts.interconnected_minigrids
    };
    var scopeLabel = selectedState ? "records intersecting state" : "national public-map records";
    var capacityBits = [];
    if (capacity.power_mw) capacityBits.push("<strong>" + formatNumber(capacity.power_mw, 1) + " MW</strong> reported power");
    if (capacity.minigrid_kw) capacityBits.push("<strong>" + formatNumber(capacity.minigrid_kw, 1) + " kW</strong> distributed energy");
    if (capacity.refinery_bpd) capacityBits.push("<strong>" + formatNumber(capacity.refinery_bpd) + " bpd</strong> refinery");

    stateProfileEl.innerHTML =
      '<div class="profile-title-row"><h3>' + escapeHtml(profileName) + '</h3><span>' + formatNumber(profile.mapped_records) + " " + escapeHtml(scopeLabel) + '</span></div>' +
      '<div class="profile-metrics">' +
        profileMetric(peopleAccess.worldpop_population_2025, "Population (WorldPop 2025)") +
        profileMetric(peopleAccess.settlement_count, "Settlement clusters") +
        profileMetric(peopleAccess.nightlight_population_share_pct, "Population with night-light signal (%)") +
        profileMetric(counts.power_plants, "Power-plant units") +
        profileMetric(counts.substations, "Substations") +
        profileMetric(counts.demand_centers, "Demand centres") +
        profileMetric(counts.community_minigrids, "Community mini-grids") +
        profileMetric(counts.captive_offgrid_systems, "Captive/institutional off-grid") +
        profileMetric(counts.standalone_systems, "Mapped standalone sites") +
        profileMetric(counts.interconnected_minigrids, "Interconnected mini-grids") +
        profileMetric(counts.fields_oil + counts.fields_gas, "Source-classified field points") +
        profileMetric(counts.ports, "Ports & terminals") +
        profileMetric(spillIntelligence.mapped_reports, "Mapped NOSDRA reports") +
        profileMetric(spillIntelligence.confirmed_reports, "Confirmed NOSDRA reports") +
        profileMetric(spillIntelligence.sabotage_attributed_reports, "Sabotage-attributed reports") +
        profileMetric(securityIntelligence.event_count, "UCDP events (2016–2025)") +
        profileMetric(securityIntelligence.fatalities_best, "UCDP fatalities, best estimate") +
      '</div>' +
      '<div class="profile-charts">' +
        profileChart("Distributed-energy mix", distributedMix, 4) +
        profileChart("Reported oil-spill causes", spillIntelligence.cause_counts, 6) +
        profileChart("Oil-spill report status", spillIntelligence.report_status_counts, 4) +
        profileTimelineChart("Mapped oil-spill reports by recent incident year", spillIntelligence.yearly_counts, 10) +
        profileTimelineChart("UCDP organized-violence events by year", securityIntelligence.yearly_counts, 10) +
      '</div>' +
      (capacityBits.length ? '<div class="capacity-strip">' + capacityBits.join(" · ") + '</div>' : "") +
      (standaloneProgramme.coverage_note
        ? '<div class="coverage-strip"><strong>Standalone solar programme evidence:</strong> ' +
          (standaloneProgramme.systems_reported
            ? '<strong>' + formatNumber(standaloneProgramme.systems_reported) +
              ' systems</strong> and <strong>' +
              formatNumber(standaloneProgramme.people_reached) +
              ' people reached</strong> reported nationally as of ' +
              escapeHtml(standaloneProgramme.as_of_date) + '. '
            : '') +
          escapeHtml(standaloneProgramme.coverage_note) +
          ' <a href="' + escapeAttr(standaloneProgramme.source_url) +
          '" target="_blank" rel="noopener">Official source</a>.</div>'
        : '') +
      (minigridCoverage.coverage_interpretation
        ? '<div class="coverage-strip"><strong>Distributed-energy coverage note:</strong> ' +
          escapeHtml(minigridCoverage.coverage_interpretation) +
          (minigridCoverage.programme_evidence
            ? ' ' + escapeHtml(minigridCoverage.programme_evidence)
            : '') +
          '</div>'
        : '') +
      '<p class="profile-note">UCDP figures describe historical organized violence and use uncertain low/best/high fatality estimates; the map shows 2016–2025 half-degree aggregates, not live or village-level events. NOSDRA figures count mapped reported incidents, not independently verified spill events. Population totals are WorldPop 2025 estimates. Night-light is a screening signal, not a measured household electricity-access rate.</p>';
    updateDownloadLabel();
  }

  function updateDownloadLabel() {
    var spillFiltersActive = spillStatusFilter && (
      spillStatusFilter.value !== spillFilters.default_report_status ||
      spillCauseFilter.value !== "all" ||
      spillCompanyFilter.value !== "all"
    );
    var filtersActive = statusFilter && (
      statusFilter.value !== "all" || timeFilterEnabled.checked || spillFiltersActive
    );
    var scope = selectedState ? "state" : "national";
    downloadStateButton.textContent = "Download " + (filtersActive ? "filtered " : "") + scope + " GeoJSON";
  }

  function selectState(name, fitBounds) {
    if (name && !ATLAS.state_profiles[name]) return;
    selectedState = name || "";
    stateSelect.value = selectedState;
    statesLayer.setStyle(stateStyle);
    if (selectedState && stateLayersByName[selectedState]) {
      if (fitBounds) map.fitBounds(stateLayersByName[selectedState].getBounds(), { padding: [24, 24] });
    } else if (fitBounds) {
      map.fitBounds(NIGERIA_BOUNDS);
    }
    renderStateProfile();

    var url = new URL(window.location.href);
    if (selectedState) url.searchParams.set("state", selectedState);
    else url.searchParams.delete("state");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);

    // Filter markers to the selected state once status/time controls exist.
    // The initial URL restore runs before those controls are wired; the later
    // applyFilters(false) call picks up selectedState then.
    if (statusFilter) applyFilters(false);
  }

  stateSelect.addEventListener("change", function () {
    selectState(stateSelect.value, true);
  });

  function selectedGeoJSON() {
    var output = {
      type: "FeatureCollection",
      name: selectedState || "Nigeria",
      product: ATLAS.product,
      atlas_release: ATLAS.release,
      atlas_selection: {
        state: selectedState || null,
        status_group: statusFilter && statusFilter.value !== "all" ? statusFilter.value : null,
        year_cutoff: timeFilterEnabled && timeFilterEnabled.checked ? Number(yearCutoff.value) : null,
        oil_spill_report_status: spillStatusFilter.value === "all" ? null : spillStatusFilter.value,
        oil_spill_cause: spillCauseFilter.value === "all" ? null : spillCauseFilter.value,
        oil_spill_company: spillCompanyFilter.value === "all" ? null : spillCompanyFilter.value,
        time_semantics: ATLAS.filters.temporal.semantics
      },
      features: []
    };
    CAT_ORDER.forEach(function (catKey) {
      var category = ATLAS.layers[catKey];
      Object.keys(category.sublayers).forEach(function (subKey) {
        category.sublayers[subKey].data.features.forEach(function (sourceFeature) {
          var memberships = sourceFeature.properties._states || [];
          if (selectedState && memberships.indexOf(selectedState) === -1) return;
          if (!featureMatches(sourceFeature, subKey)) return;
          var item = JSON.parse(JSON.stringify(sourceFeature));
          item.properties.atlas_category = category.label;
          item.properties.atlas_layer = category.sublayers[subKey].label;
          item.properties.atlas_states = item.properties._states;
          delete item.properties._states;
          output.features.push(item);
        });
      });
    });
    return output;
  }

  downloadStateButton.addEventListener("click", function () {
    var previousLabel = downloadStateButton.textContent;
    downloadStateButton.disabled = true;
    downloadStateButton.textContent = "Preparing…";
    Promise.all(Object.keys(registry).map(ensureSublayerLoaded)).then(function () {
      var data = JSON.stringify(selectedGeoJSON());
      var blob = new Blob([data], { type: "application/geo+json" });
      var href = URL.createObjectURL(blob);
      var anchor = document.createElement("a");
      var slug = (selectedState || "nigeria").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      anchor.href = href;
      anchor.download = "infraxis-atlas-nigeria-" + slug + "-v" + ATLAS.release.version + ".geojson";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(href);
    }).catch(function (err) {
      window.alert("Could not prepare GeoJSON: " + err.message);
    }).then(function () {
      downloadStateButton.disabled = false;
      updateDownloadLabel();
      if (downloadStateButton.textContent === "Preparing…") {
        downloadStateButton.textContent = previousLabel;
      }
    });
  });

  function reportRows(values) {
    return Object.keys(values || {}).map(function (key) {
      var value = values[key];
      var display = value === null || value === undefined || value === ""
        ? "Not disclosed"
        : typeof value === "number"
          ? formatNumber(value, 2)
          : escapeHtml(value);
      return '<tr><th>' + escapeHtml(key) + '</th><td>' + display + '</td></tr>';
    }).join("");
  }

  downloadReportButton.addEventListener("click", function () {
    var profileName = selectedState || "Nigeria";
    var profile = ATLAS.state_profiles[profileName];
    var spill = profile.oil_spill_intelligence || {};
    var standalone = profile.standalone_solar_programme || {};
    var security = profile.security_intelligence || {};
    var report = '<!doctype html><html lang="en"><meta charset="utf-8"><title>' +
      escapeHtml(profileName) + ' — Infraxis Atlas report</title><style>' +
      'body{font:14px/1.5 system-ui;margin:40px auto;max-width:900px;color:#17231f}h1,h2{font-family:Georgia,serif}' +
      'table{border-collapse:collapse;width:100%;margin:12px 0 28px}th,td{border-bottom:1px solid #ccd2cc;padding:7px;text-align:left}' +
      'th{width:65%}.note{background:#f2f4ef;padding:12px;border-left:4px solid #a86612}small{color:#59645d}' +
      '@media print{body{margin:18mm}.no-print{display:none}}</style><body>' +
      '<h1>' + escapeHtml(profileName) + '</h1><p>Infraxis Atlas — Nigeria state report · v' +
      escapeHtml(ATLAS.release.version) + ' · ' + escapeHtml(ATLAS.release.date) + '</p>' +
      '<p class="note">Public screening evidence, not an official operating registry or substitute for field verification.</p>' +
      '<h2>State overview</h2><table>' +
      reportRows({
        "Mapped public records": profile.mapped_records,
        "WorldPop population estimate (2025)": (profile.people_access || {}).worldpop_population_2025,
        "Settlement clusters": (profile.people_access || {}).settlement_count,
        "Power-plant units": profile.counts.power_plants,
        "Substations": profile.counts.substations,
        "Community mini-grids": profile.counts.community_minigrids,
        "Captive / institutional off-grid": profile.counts.captive_offgrid_systems,
        "Standalone systems": profile.counts.standalone_systems,
        "Interconnected mini-grids": profile.counts.interconnected_minigrids
      }) + '</table><h2>Standalone solar programme evidence</h2><table>' +
      reportRows({
        "Systems reported (national aggregate only)": standalone.systems_reported,
        "People reached (national aggregate only)": standalone.people_reached,
        "Evidence date": standalone.as_of_date
      }) + '</table><p>' + escapeHtml(standalone.coverage_note || "") +
      '</p><h2>Historical organized-violence context (UCDP, 2016–2025)</h2><table>' +
      reportRows({
        "Events": security.event_count,
        "Fatalities (best estimate)": security.fatalities_best,
        "Fatalities (low estimate)": security.fatalities_low,
        "Fatalities (high estimate)": security.fatalities_high,
        "State-based events": security.state_based_events,
        "Non-state events": security.non_state_events,
        "One-sided events": security.one_sided_events
      }) + '</table><p>Annual, historical UCDP GED 26.1 data licensed CC BY 4.0. The atlas map aggregates source events into half-degree cells and does not republish exact event locations, actor names, narratives, or source text. This is not a live threat feed.</p>' +
      '<h2>NOSDRA reported incidents</h2><table>' +
      reportRows({
        "Mapped reports": spill.mapped_reports,
        "Confirmed reports": spill.confirmed_reports,
        "Invalid reports": spill.invalid_reports,
        "Sabotage-attributed reports": spill.sabotage_attributed_reports
      }) + '</table><h2>Reported causes</h2><table>' + reportRows(spill.cause_counts) +
      '</table><h2>Reports by incident year</h2><table>' + reportRows(spill.yearly_counts) +
      '</table><h2>Reported capacities</h2><table>' + reportRows({
        "Power (MW)": profile.capacity.power_mw,
        "Distributed energy (kW)": profile.capacity.minigrid_kw,
        "Refinery (bpd)": profile.capacity.refinery_bpd
      }) + '</table><small>Generated from the versioned public state profile. Review source-specific limitations and reuse terms in the atlas data catalogue.</small></body></html>';
    var blob = new Blob([report], { type: "text/html;charset=utf-8" });
    var href = URL.createObjectURL(blob);
    var anchor = document.createElement("a");
    var slug = profileName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    anchor.href = href;
    anchor.download = "infraxis-atlas-nigeria-" + slug + "-state-report-v" + ATLAS.release.version + ".html";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
  });

  copyStateLinkButton.addEventListener("click", function () {
    var original = copyStateLinkButton.textContent;
    function showResult(label) {
      copyStateLinkButton.textContent = label;
      window.setTimeout(function () { copyStateLinkButton.textContent = original; }, 1400);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(window.location.href).then(function () { showResult("Copied"); });
    } else {
      var temporary = document.createElement("textarea");
      temporary.value = window.location.href;
      document.body.appendChild(temporary);
      temporary.select();
      document.execCommand("copy");
      temporary.remove();
      showResult("Copied");
    }
  });

  var initialState = new URLSearchParams(window.location.search).get("state") || "";
  selectState(initialState, Boolean(initialState));

  // ---------------- Status and time filters ----------------
  var statusFilter = document.getElementById("status-filter");
  var timeFilterEnabled = document.getElementById("time-filter-enabled");
  var timeFilterControls = document.getElementById("time-filter-controls");
  var yearCutoff = document.getElementById("year-cutoff");
  var yearCutoffOutput = document.getElementById("year-cutoff-output");
  var filterSummary = document.getElementById("filter-summary");
  var spillFilterSummary = document.getElementById("spill-filter-summary");
  var resetFiltersButton = document.getElementById("reset-filters");
  var temporal = ATLAS.filters.temporal;
  var statusCounts = ATLAS.filters.status_groups;
  var spillFilters = ATLAS.filters.oil_spills;
  var spillStatusFilter = document.getElementById("spill-status-filter");
  var spillCauseFilter = document.getElementById("spill-cause-filter");
  var spillCompanyFilter = document.getElementById("spill-company-filter");

  function populateSpillFilter(select, entries, allLabel) {
    select.innerHTML = "";
    var allOption = document.createElement("option");
    allOption.value = "all";
    allOption.textContent = allLabel;
    select.appendChild(allOption);
    entries.forEach(function (entry) {
      var option = document.createElement("option");
      option.value = entry.value;
      option.textContent = entry.value + " (" + formatNumber(entry.count) + ")";
      select.appendChild(option);
    });
  }
  populateSpillFilter(
    spillStatusFilter,
    spillFilters.fields.report_statuses,
    "All report statuses"
  );
  populateSpillFilter(spillCauseFilter, spillFilters.fields.causes, "All reported causes");
  populateSpillFilter(spillCompanyFilter, spillFilters.fields.companies, "All companies");
  spillStatusFilter.value = spillFilters.default_report_status;

  Array.prototype.forEach.call(statusFilter.options, function (option) {
    if (option.value !== "all") {
      option.textContent += " (" + formatNumber(statusCounts[option.value]) + ")";
    }
  });
  yearCutoff.min = temporal.minimum_year;
  yearCutoff.max = temporal.maximum_year;
  yearCutoff.value = temporal.maximum_year;
  yearCutoffOutput.textContent = yearCutoff.value;

  function featureMatches(feature, subKey) {
    feature = feature || {};
    var props = feature.properties || {};
    if (selectedState) {
      var memberships = props._states || [];
      if (memberships.indexOf(selectedState) === -1) return false;
    }
    if (statusFilter.value !== "all" && props._status_group !== statusFilter.value) return false;
    if (timeFilterEnabled.checked) {
      if (!props._year || Number(props._year) > Number(yearCutoff.value)) return false;
    }
    if (subKey === "oil_spills") {
      if (spillStatusFilter.value !== "all" && props.status_label !== spillStatusFilter.value) return false;
      if (spillCauseFilter.value !== "all" && props.cause_label !== spillCauseFilter.value) return false;
      if (spillCompanyFilter.value !== "all" && props.company !== spillCompanyFilter.value) return false;
    }
    return true;
  }

  function syncFilterUrl() {
    var url = new URL(window.location.href);
    if (statusFilter.value !== "all") url.searchParams.set("status", statusFilter.value);
    else url.searchParams.delete("status");
    if (timeFilterEnabled.checked) url.searchParams.set("year", yearCutoff.value);
    else url.searchParams.delete("year");
    if (spillStatusFilter.value !== spillFilters.default_report_status) {
      url.searchParams.set("spill_status", spillStatusFilter.value);
    } else {
      url.searchParams.delete("spill_status");
    }
    if (spillCauseFilter.value !== "all") url.searchParams.set("spill_cause", spillCauseFilter.value);
    else url.searchParams.delete("spill_cause");
    if (spillCompanyFilter.value !== "all") url.searchParams.set("spill_company", spillCompanyFilter.value);
    else url.searchParams.delete("spill_company");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  }

  function applyFilters(updateUrl) {
    var matchedRecords = 0;
    var matchedSpillRecords = 0;
    Object.keys(registry).forEach(function (subKey) {
      var entry = registry[subKey];
      entry.children.forEach(function (child) {
        var matches = featureMatches(child.feature, subKey);
        var included = entry.leafletLayer.hasLayer(child);
        if (matches && !included) entry.leafletLayer.addLayer(child);
        else if (!matches && included) entry.leafletLayer.removeLayer(child);
        if (matches) matchedRecords += 1;
        if (matches && subKey === "oil_spills") matchedSpillRecords += 1;
      });
    });
    timeFilterControls.setAttribute("aria-disabled", timeFilterEnabled.checked ? "false" : "true");
    yearCutoff.disabled = !timeFilterEnabled.checked;
    yearCutoffOutput.textContent = yearCutoff.value;
    var summary = formatNumber(matchedRecords) + " records match";
    if (selectedState) summary += " · " + selectedState;
    if (timeFilterEnabled.checked) summary += " · dated through " + yearCutoff.value;
    filterSummary.textContent = summary;
    spillFilterSummary.textContent =
      formatNumber(matchedSpillRecords) + " of " +
      formatNumber(spillFilters.mapped_record_count) + " mapped reports match. " +
      formatNumber(spillFilters.source_record_count - spillFilters.mapped_record_count) +
      " source reports have no publishable map coordinate.";
    updateDownloadLabel();
    updateVisibleStat();
    if (updateUrl) syncFilterUrl();
  }

  statusFilter.addEventListener("change", function () { applyFilters(true); });
  spillStatusFilter.addEventListener("change", function () { applyFilters(true); });
  spillCauseFilter.addEventListener("change", function () { applyFilters(true); });
  spillCompanyFilter.addEventListener("change", function () { applyFilters(true); });
  timeFilterEnabled.addEventListener("change", function () { applyFilters(true); });
  yearCutoff.addEventListener("input", function () {
    yearCutoffOutput.textContent = yearCutoff.value;
    applyFilters(true);
  });
  resetFiltersButton.addEventListener("click", function () {
    statusFilter.value = "all";
    timeFilterEnabled.checked = false;
    yearCutoff.value = temporal.maximum_year;
    spillStatusFilter.value = spillFilters.default_report_status;
    spillCauseFilter.value = "all";
    spillCompanyFilter.value = "all";
    applyFilters(true);
  });

  var initialParams = new URLSearchParams(window.location.search);
  var initialStatus = initialParams.get("status");
  if (initialStatus && statusCounts[initialStatus] !== undefined) statusFilter.value = initialStatus;
  var initialYear = Number(initialParams.get("year"));
  if (initialYear >= temporal.minimum_year && initialYear <= temporal.maximum_year) {
    timeFilterEnabled.checked = true;
    yearCutoff.value = initialYear;
  }
  var initialSpillStatus = initialParams.get("spill_status");
  if (initialSpillStatus && Array.prototype.some.call(
    spillStatusFilter.options, function (option) { return option.value === initialSpillStatus; }
  )) spillStatusFilter.value = initialSpillStatus;
  var initialSpillCause = initialParams.get("spill_cause");
  if (initialSpillCause && Array.prototype.some.call(
    spillCauseFilter.options, function (option) { return option.value === initialSpillCause; }
  )) spillCauseFilter.value = initialSpillCause;
  var initialSpillCompany = initialParams.get("spill_company");
  if (initialSpillCompany && Array.prototype.some.call(
    spillCompanyFilter.options, function (option) { return option.value === initialSpillCompany; }
  )) spillCompanyFilter.value = initialSpillCompany;
  applyFilters(false);

  // ---------------- Data catalogue ----------------
  var catalogueDialog = document.getElementById("data-catalogue");
  var catalogueButton = document.getElementById("catalogue-button");
  var catalogueClose = document.getElementById("catalogue-close");
  var catalogueSearch = document.getElementById("catalogue-search");
  var catalogueGrid = document.getElementById("catalogue-grid");
  var catalogueSummary = document.getElementById("catalogue-summary");

  function catalogueCard(item) {
    return (
      '<article class="catalogue-card">' +
        '<div class="catalogue-card-head"><h3>' + escapeHtml(item.label) + '</h3><span class="quality-badge quality-' + escapeAttr(item.quality.toLowerCase()) + '" title="' + escapeAttr(item.quality_note) + '">' + escapeHtml(item.quality) + '</span></div>' +
        '<div class="catalogue-category">' + escapeHtml(item.category_label) + ' · ' + formatNumber(item.record_count) + ' records</div>' +
        '<p class="catalogue-description">' + escapeHtml(item.description) + '</p>' +
        '<dl class="catalogue-facts">' +
          '<div><dt>Source</dt><dd>' + escapeHtml(item.source) + '</dd></div>' +
          '<div><dt>Source date</dt><dd>' + escapeHtml(item.source_date) + '</dd></div>' +
          '<div><dt>Last checked</dt><dd>' + escapeHtml(item.refresh.last_checked) + '</dd></div>' +
          '<div><dt>Refresh</dt><dd>' + escapeHtml(item.refresh.cadence) + ' · next review ' + escapeHtml(item.refresh.next_review_due) + '</dd></div>' +
          '<div><dt>Reuse</dt><dd>' + escapeHtml(item.license) + '</dd></div>' +
        '</dl>' +
        '<p class="quality-note"><strong>Quality ' + escapeHtml(item.quality) + ':</strong> ' + escapeHtml(item.quality_note) + '</p>' +
        '<a class="download-link" href="' + escapeAttr(item.download_url) + '" data-remote-download="' + escapeAttr(filenameFromUrl(item.download_url)) + '">Download processed CSV ↓</a>' +
        (item.coverage_audit_url ? '<a class="download-link" href="' + escapeAttr(item.coverage_audit_url) + '" data-remote-download="' + escapeAttr(filenameFromUrl(item.coverage_audit_url)) + '">Download state coverage audit ↓</a>' : '') +
        (item.supplement_url ? '<a class="download-link" href="' + escapeAttr(item.supplement_url) + '" data-remote-download="' + escapeAttr(filenameFromUrl(item.supplement_url)) + '">Download verified supplement ↓</a>' : '') +
      '</article>'
    );
  }

  function renderCatalogue(query) {
    var normalized = (query || "").trim().toLowerCase();
    var items = (ATLAS.catalogue || []).filter(function (item) {
      if (!normalized) return true;
      return [item.label, item.category_label, item.source, item.description, item.license]
        .join(" ").toLowerCase().indexOf(normalized) !== -1;
    });
    catalogueGrid.innerHTML = items.map(catalogueCard).join("");
    var records = items.reduce(function (sum, item) { return sum + item.record_count; }, 0);
    catalogueSummary.textContent = items.length + " datasets · " + formatNumber(records) + " map records";
  }

  // Cross-origin links (these point at raw.githubusercontent.com) silently
  // ignore the `download` attribute in Chrome/Firefox and just navigate the
  // tab to the raw file instead of saving it -- fetch the bytes ourselves
  // and trigger the save from a same-origin blob: URL, matching how the
  // state/national GeoJSON export buttons already work below.
  catalogueGrid.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("[data-remote-download]");
    if (!link) return;
    event.preventDefault();
    var filename = link.getAttribute("data-remote-download");
    var originalText = link.textContent;
    link.textContent = "Downloading…";
    fetch(link.href)
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.blob();
      })
      .then(function (blob) {
        var href = URL.createObjectURL(blob);
        var anchor = document.createElement("a");
        anchor.href = href;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(href);
        link.textContent = originalText;
      })
      .catch(function () {
        link.textContent = originalText;
        window.open(link.href, "_blank", "noopener");
      });
  });

  catalogueButton.addEventListener("click", function () {
    renderCatalogue(catalogueSearch.value);
    if (catalogueDialog.showModal) catalogueDialog.showModal();
    else catalogueDialog.setAttribute("open", "");
    catalogueSearch.focus();
  });
  catalogueClose.addEventListener("click", function () { catalogueDialog.close(); });
  catalogueDialog.addEventListener("click", function (event) {
    if (event.target === catalogueDialog) catalogueDialog.close();
  });
  catalogueSearch.addEventListener("input", function () { renderCatalogue(catalogueSearch.value); });
  renderCatalogue("");

  // ---------------- Search ----------------
  var searchInput = document.getElementById("search-input");
  var searchResults = document.getElementById("search-results");
  searchInput.addEventListener("input", function () {
    var q = searchInput.value.trim().toLowerCase();
    if (q.length < 2) { searchResults.classList.remove("open"); searchResults.innerHTML = ""; return; }
    var matches = allFeaturesIndex.filter(function (item) {
      return item.label.toLowerCase().indexOf(q) !== -1 && featureMatches(item.feature, item.subKey);
    }).slice(0, 8);
    if (!matches.length) {
      searchResults.innerHTML = '<div class="result">No matches</div>';
    } else {
      searchResults.innerHTML = matches.map(function (m, i) {
        return '<div class="result" data-idx="' + i + '"><span>' + escapeHtml(m.label) + '</span><span class="r-cat">' + m.subLabel + '</span></div>';
      }).join("");
      Array.prototype.forEach.call(searchResults.querySelectorAll(".result"), function (el, i) {
        el.addEventListener("click", function () {
          var m = matches[i];
          var entry = registry[m.subKey];
          if (!map.hasLayer(entry.leafletLayer)) {
            entry.leafletLayer.addTo(map);
            var cb = document.querySelector('input[data-sub="' + m.subKey + '"]');
            if (cb) cb.checked = true;
            updateVisibleStat();
          }
          if (m.subKey === "oil_spills" && entry.leafletLayer.zoomToShowLayer) {
            entry.leafletLayer.zoomToShowLayer(m.layer, function () {
              m.layer.openPopup();
            });
            searchResults.classList.remove("open");
            searchInput.value = m.label;
            return;
          }
          var target = m.layer.getBounds ? m.layer.getBounds() : m.layer.getLatLng();
          if (target && target.isValid && target.isValid()) map.fitBounds(target.pad ? target.pad(2) : target, { maxZoom: 11 });
          else if (m.layer.getLatLng) map.setView(m.layer.getLatLng(), 11);
          m.layer.openPopup();
          searchResults.classList.remove("open");
          searchInput.value = m.label;
        });
      });
    }
    searchResults.classList.add("open");
  });
  document.addEventListener("click", function (e) {
    if (!searchResults.contains(e.target) && e.target !== searchInput) searchResults.classList.remove("open");
  });
  } // end runApp
})();
