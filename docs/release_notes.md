# Release notes

## v0.11.0 — Hydroelectric Coverage and State-scoped Filtering

Released: 28 July 2026

- added seven Nigerian hydroelectric plants as a dedicated infrastructure
  sublayer, including operating, pre-construction, and shelved projects
- corrected the Hudson power-station coordinate to an explicitly documented
  LGA-level Lagos location after identifying a source-coordinate mismatch
- increased the public contract to 29,098 mapped records, 26 content-bearing
  catalogue entries, and 27 stable layer endpoints
- made state selection scope visible map records and all active status, time,
  and NOSDRA filter results to the selected state
- aligned release metadata, citation guidance, documentation, tests, catalogue,
  public bundle, and static API with the expanded infrastructure contract

## v0.10.0 — Licensed Historical Security Context

Released: 25 July 2026

- added Security Context as the atlas's eighth analytical section
- used UCDP GED 26.1, whose publisher explicitly licenses reuse and
  redistribution under CC BY 4.0
- published 227 half-degree exposure cells summarizing 5,565 Nigeria
  organized-violence events during 2016–2025
- added state/year analytical summaries and low/best/high UCDP fatality
  estimates to profiles, charts, reports, catalogue, and API
- excluded exact event coordinates, actor names, narratives, headlines, and
  source articles from processed public outputs
- selected the annual 1989–2025 release and excluded UCDP's near-real-time
  Candidate Events feed so the layer cannot be mistaken for live intelligence

## v0.9.0 — Distributed Energy Coverage Expansion

Released: 25 July 2026

- expanded the canonical distributed-energy registry from 80 to 93 records
- added 13 non-duplicate mini-grid communities from the official Nigeria
  SE4ALL community survey, with community-level precision clearly disclosed
- increased mapped community mini-grids from 68 to 81 and geographic coverage
  from 30 states plus the FCT to 31 states plus the FCT
- added privacy-preserving standalone-solar programme evidence to all state
  profiles and downloadable reports
- recorded the official April 2026 DARES aggregate of 830,000 systems and
  nearly 3.9 million people reached without publishing household locations
- distinguished six named strong-coverage states from states supported only by
  national programme evidence; no unsupported state unit totals were inferred

## v0.8.0 — State Analytics and Downloadable Reports

Released: 25 July 2026

- added compact state-profile charts for distributed-energy composition,
  reported oil-spill causes, NOSDRA report status, and recent incident years
- added self-contained HTML state reports for offline review and printing
- included state-level NOSDRA cause, report-status, and yearly distributions in
  the versioned public bundle and static API
- retained the existing state GeoJSON download as a separate,
  filter-responsive data export
- preserved screening caveats in both the interactive profiles and reports

## v0.7.0 — Oil Spill Intelligence and Open Atlas Contributions

Released: 25 July 2026

- integrated 21,124 NOSDRA reported incidents, including 16,326 records with
  publishable coordinates, as a documented processed dataset and API layer
- added clustered spill rendering plus filters for report status, reported
  cause, company, and incident year
- defaulted spill analysis to confirmed reports while retaining reviewed,
  invalid, and inconclusive source records for transparent inspection
- excluded one implausible 1902 source date from timelines without deleting it
  from the processed audit trail
- added national and state mapped, confirmed, invalid, and
  sabotage-attributed report summaries
- added machine-readable dataset refresh schedules at
  `/api/v1/freshness.json`
- opened a repository-wide evidence submission route covering every atlas
  section, alongside the structured distributed-energy workflow
- restored the full release gate at 28,851 mapped records across 25 public
  datasets

## v0.6.0 — Structured Distributed Energy and Open Contributions

Released: 24 July 2026

- classified all 80 public records into community mini-grids (68),
  captive/institutional off-grid systems (10), standalone systems (0), and
  interconnected mini-grids (2)
- split the website, state profiles, catalogue, and API into four
  non-overlapping distributed-energy layers
- preserved `/api/v1/layers/minigrids.geojson` as a backward-compatible
  aggregate endpoint
- added a contribution CSV template, JSON Schema, command-line validator,
  verification guide, issue form, pull-request checklist, and CI checks
- established manual evidence, geospatial, duplicate, classification, and
  licensing review before community records are promoted to the live atlas

## v0.5.0 — Gas Field Taxonomy and Map Symbology Audit

Released: 24 July 2026

- replaced the misleading two-record gas-only point layer with 147
  source-classified gas-producing fields (`gas` plus `oil and gas`)
- retained 33 source-classified oil-only fields as a separate, non-overlapping
  layer, preserving the 180-point GOGET total without double counting
- retained independent SE4ALL gas-only and mixed field-boundary layers
- documented that GOGET's fuel label still misclassifies some known
  gas-producing sites as oil
- assigned every public sublayer a distinct colour and audited point icons,
  marker sizes, line weights, dash patterns, polygon fills, legends, and
  dark/light-theme refresh behavior

## v0.4.2 — Mini-grid and Off-grid Layer Clarification

Released: 24 July 2026

- renamed the public map layer and state metric to “Catalogued Mini-grid &
  Off-grid Sites”
- clarified the state coverage notice and site footer so both mini-grid and
  off-grid systems are explicitly represented
- retained “catalogued” because the public-source inventory is evidence-backed
  but not an exhaustive national asset registry

## v0.4.1 — National Mini-grid Coverage Correction

Released 2026-07-24.

### Included

- 14 named official-source off-grid additions, including two Bayero University
  Kano systems
- 80 combined records across 30 states and the FCT
- current rehabilitation status and capacity caveat for the original BUK EEP plant
- exact-site, facility, campus, and community coordinate-precision fields
- a reproducible 37-state/FCT coverage audit
- programme-only evidence for Abia, Borno, Ekiti, Enugu, Imo, and Zamfara
- interface wording changed from implied asset totals to explicitly catalogued
  public-site counts
- explicit warning that zero catalogued records does not mean zero assets

## v0.4.0 — Population, Settlements, and Electricity-access Context

Released 2026-07-24.

### Included

- WorldPop v3.0 2025 population estimates for all 36 states and the FCT
- 154,319 World Bank DRE Atlas settlement clusters in an analysis-ready table
- 1,278 quarter-degree population/access cells for responsive national mapping
- 1,480 major-settlement display records, retaining 40 per state
- state-profile settlement, population, night-light, and grid-distance indicators
- People & Access map controls, catalogue entries, filtered downloads, and API endpoints
- explicit UI and documentation warnings that night-light is not a measured
  household electricity-access rate
- 12,511 public-map features across 22 datasets

## v0.3.0 — Status, Time Filters, Downloads, and Static API

Released 2026-07-24.

### Included

- normalized operating, development, proposed, inactive, other, and unknown status groups
- opt-in evidence-year cutoff with explicit exclusion of undated records
- filter-aware map rendering, search results, layer counts, and visible-record totals
- shareable URLs preserving state, status, and year selections
- national and state GeoJSON downloads using the active filters
- download metadata recording the active selection and time semantics
- stable `/api/v1/` static API with no API key requirement
- API manifest, catalogue, state profiles, ADM1 boundaries, and 15 layer endpoints
- human-readable developer documentation and reproducibility tests

### Temporal coverage

The current release has 266 records with a defensible relevant year between
1912 and 2026. The remaining records are marked undated and are excluded when
the time cutoff is active. This avoids implying historical presence where the
source provides no usable date.

## v0.2.0 — State Intelligence and Data Catalogue

Released 2026-07-24.

### Included

- reproducible profiles for Nigeria, all 36 states, and the FCT
- per-feature ADM1 memberships derived from the committed state boundaries
- state selection by dropdown or direct map click
- shareable state URLs and state-specific GeoJSON downloads
- national and state summaries for key asset counts and reported capacities
- searchable catalogue for all 15 public map datasets
- source, access-date, reuse, quality, limitation, record-count, and CSV-download metadata
- automated profile and catalogue consistency checks

### Interpretation boundary

State figures count public-map records whose display geometry intersects a
state. Lines and polygons can appear in multiple profiles, unit-level datasets
can contain several records at one facility, and offshore features remain
national rather than being forced into coastal states.

## v0.1.0 — Public Atlas

Released 2026-07-23.

This milestone establishes a reproducible, research-grade public atlas release.

### Included

- canonical Leaflet/GitHub Pages atlas with 9,531 public-map features across 15 sublayers
- deterministic `scripts/build_public_atlas_data.py` web-bundle build
- committed simplified ADM1 boundary input under `data/final/`
- automated schema, count, coordinate, JavaScript, and reproducibility checks
- GitHub Actions validation workflow
- six implemented layers: resource, infrastructure, environmental, demand,
  connectivity, and renewables
- 66-site mini-grid inventory across 26 states and the FCT
- machine-readable citation metadata and explicit third-party data-rights guidance

### Explicitly not included

- a processed security layer; candidate sources are documented for future work
- a complete live operating registry
- standalone solar-home-system coverage
- field verification or commercial diligence

### Canonical map

The static Leaflet application under `docs/` is the canonical public map. The
PNG snapshot remains the canonical print/static summary. Experimental Folium
outputs are not versioned release artifacts.

### Known follow-up work

- verify ambiguous redistribution terms with source publishers
- add the security layer only after source licensing and processing are complete
- extend renewable coverage beyond the current mini-grid inventory
- introduce dated dataset snapshots as sources are refreshed
