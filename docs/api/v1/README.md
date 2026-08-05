# Infraxis Atlas — Nigeria static API v1

Base URL:

`https://diamonds10.github.io/infraxis-atlas-nigeria/api/v1/`

This is the versioned, read-only **open atlas** API: public datasource
endpoints for the Nigeria country edition. It needs no API key and supports
normal HTTP caching. Start with `manifest.json`.

It does **not** expose premium Infraxis models or client products. The
manifest `product` object states that explicitly:

- `role`: `open_datasource`
- `premium_brand`: `Infraxis`
- `relationship`: open atlas is the public datasource; Infraxis is the
  separate premium layer built on top

The base URL path may retain former Nigeria Infrastructure Atlas naming for
compatibility; product identity is authoritative in the `product` object.

## Endpoints

- `manifest.json` — API contract, release information, filter fields, and layer endpoints
- `catalogue.json` — provenance, quality, licensing, and download metadata
- `freshness.json` — machine-readable source-review cadence and due dates
- `schema.json` — JSON Schema for normalized public feature fields
- `state-profiles.json` — Nigeria and ADM1 screening summaries
- `states.geojson` — simplified Nigeria ADM1 boundaries
- `layers/{layer-key}.geojson` — one GeoJSON FeatureCollection per public map layer

The Distributed Energy section exposes:

- `layers/community_minigrids.geojson`
- `layers/captive_offgrid_systems.geojson`
- `layers/standalone_systems.geojson`
- `layers/interconnected_minigrids.geojson`

`layers/minigrids.geojson` remains a backward-compatible 93-record aggregate.
New integrations should use the four structured endpoints. The manifest lists
this under `compatibility_endpoints`.

## Filter fields

Layer features include:

- `_states`: state boundaries intersected by the public display geometry
- `_status_group`: `operating`, `development`, `proposed`, `inactive`, `other`, or `unknown`
- `_year`: relevant discovery, start, commissioning, incident, designation, or source
  release year when supported
- `_year_label`: the meaning of `_year` for that record

When applying a year cutoff, exclude records without `_year`. Do not assume an
undated record existed before the selected year.

The `oil_spills` endpoint additionally exposes NOSDRA report status, reported
cause, company, incident year, and incident-date quality. These are reported
incidents rather than independently verified spill findings.

## Stability

The `/api/v1/` contract will remain backward compatible within API version 1.
Dataset contents can change with atlas releases; inspect `atlas_release` and
source dates when reproducibility matters.

The `population_access` and `settlements` endpoints contain modelled screening
context. Their night-light fields are not measured household
electricity-access rates.

Distributed-energy endpoints contain catalogued public records from multiple
sources. State counts are not exhaustive, and a zero count does not establish
that no asset of that class exists in a state.
