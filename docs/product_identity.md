# Infraxis Atlas product identity

## Two layers, one stack

| Layer | What it is | Where it lives |
|---|---|---|
| **Open atlas** | Public datasource and screening map | This repository |
| **Infraxis** | Premium analytical products | Separate commercial products |

This repository is the **open atlas**: reproducible public-source evidence,
catalogue, API, and country-edition map. It is not the premium Infraxis
product suite.

**Infraxis** is the **premium layer** that may sit on top of the open atlas.
It can include proprietary disruption and loss models, private client data,
financial assumptions, portfolio analytics, enterprise workspaces, and
advisory services. Those products are not published, licensed, or implied by
this repository.

Short form:

> The atlas is the open datasource. Infraxis is the premium layer.

## Open product name

**Public open product:** Infraxis Atlas — Nigeria  
**Master open-atlas brand:** Infraxis Atlas  
**Country pattern:** `Infraxis Atlas — {Country}`  
**Open-atlas tagline:** *Mapping infrastructure. Measuring disruption.*

The name keeps the Infraxis family identity while the **role** fields and this
document make the open-versus-premium split explicit. Future open country
editions should keep the same taxonomy, provenance standards, contribution
controls, and API principles.

## Nigeria transition

Infraxis Atlas — Nigeria was published as **Nigeria Infrastructure Atlas**
through v0.11.1. The former name remains in metadata for continuity.

Legacy repository, GitHub Pages, and API URLs may remain as stable technical
identifiers during transition. They are not the product definition. Any future
URL migration must provide tested redirects before legacy URLs are retired.

## What this open repository contains

- public-source infrastructure mapping and screening layers
- state profiles and downloadable reports
- source provenance, quality notes, and reuse conditions
- processed public datasets where redistribution permits
- a versioned static API
- reproducible processing and release checks
- open contribution and correction workflows

The atlas is screening and planning evidence. It is not an official government
registry, live security feed, or substitute for field, legal, regulatory, or
commercial due diligence.

## What this repository does not contain

Proprietary Infraxis products, including but not limited to:

- *What Might We Lose?* forward-looking disruption / loss scenarios
- *What Did We Actually Lose?* retrospective assessments
- private client data and enterprise workspaces
- proprietary model parameters, methods, or software
- paid advisory deliverables

Nothing in this repository's CC0 dedication publishes, relicenses, or implies
access to those premium assets. Third-party atlas data remains governed by its
original source terms in `THIRD_PARTY_DATA.md` and `docs/data_sources.md`.

## Machine-readable contract

Public JSON resources publish a `product` object with at least:

- `name` — open country edition name
- `master_brand` — open-atlas brand family
- `premium_brand` — premium product family (`Infraxis`)
- `role` — always `open_datasource` for this repository
- `relationship` — one-sentence open→premium stack description
- `country`, `former_name`, `tagline`

Integrators should treat `role: "open_datasource"` as the authoritative signal
that an endpoint belongs to the open atlas, not to premium Infraxis.

## Public description

> Infraxis Atlas — Nigeria is the open datasource and screening layer for
> Nigeria's infrastructure system: assets, energy access, communities,
> environmental conditions, and historical security exposure. Infraxis is the
> separate premium analytical layer built on top of this open evidence base.

## Naming examples

Open atlas editions:

- Infraxis Atlas — Nigeria
- Infraxis Atlas — Ghana
- Infraxis Atlas — Kenya

Premium products (outside this repository):

- Infraxis
- Infraxis *What Might We Lose?*
- Infraxis *What Did We Actually Lose?*

Do not use `official`, `national`, or `government` in a country-edition name
without formal written adoption by the relevant authority.
