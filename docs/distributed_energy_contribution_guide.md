# Distributed-energy contribution and verification guide

## What belongs in this registry

The atlas accepts named, geocodable Nigerian distributed-energy assets in four
classes:

| Class | Definition |
|---|---|
| `community_mini_grid` | Local generation plus a distribution network serving a community, market, or customer cluster |
| `captive_institutional_off_grid` | A system serving a defined campus, hospital, school, department, factory, or other captive facility |
| `standalone_system` | A household, shop, facility, or solar-home system without a local distribution network |
| `interconnected_mini_grid` | A mini-grid designed to operate with or connect to an existing distribution network |

Programme targets, state totals, tenders, and unnamed deployments are useful
coverage evidence but are not promoted to site records without a named
location and defensible coordinates.

## How to contribute

For one record or a correction, use the repository's **Distributed-energy
record** issue form. For multiple records:

1. Copy the CSV template under `data/contributions/07_renewables/`.
2. Use one row per physical system.
3. Keep `verification_status` as `submitted`.
4. Set `attestation` to `true`.
5. Validate the file:

```bash
python scripts/07_renewables/03_validate_distributed_energy_submission.py \
  path/to/submission.csv
```

6. Open a pull request containing the submission file. Do not edit the
   processed registry or generated API files directly.

## Evidence threshold

At least one public source must support the asset's name, location, and
delivery status. Preferred sources are regulators, REA/NEP/DARES, government
institutions, operators, universities, hospitals, development partners, and
project financiers. Credible secondary reporting may initiate a review but
normally requires corroboration before acceptance.

Coordinates must be labelled honestly:

- `exact_site`: verified plant parcel or published GPS point
- `facility`: known host facility, exact energy-system position unknown
- `campus`: campus centroid or representative campus point
- `community`: named community centroid
- `lga`, `state`, or `derived_centroid`: coarse screening location

## Verification workflow

| Stage | Meaning |
|---|---|
| Submitted | Community proposal; not published |
| Automated checks passed | Schema, enum, coordinate, date, and URL checks pass |
| Evidence review | Source supports the claimed asset and status |
| Geospatial review | Coordinates and precision label are defensible |
| Duplicate review | Name, operator, programme, and nearby records checked |
| Classification review | One of the four distributed-energy classes confirmed |
| Accepted | Maintainer assigns a stable asset ID and promotes the record |
| Rejected or needs information | Reason is recorded publicly |

Acceptance is intentionally manual. A valid CSV proves that a proposal is
well-formed; it does not prove that the asset exists.

## Promotion into the atlas

Accepted records are added to the curated supplement with:

- a stable `asset_id`
- canonical distributed-energy class
- classification basis and confidence
- evidence and coordinate provenance
- reviewer notes and source-access date

The processor then regenerates the canonical registry, state audit, website,
static API, benchmark outputs, and tests. This keeps public contributions
traceable without allowing unreviewed submissions onto the live map.

## Corrections and disputes

Open an issue identifying the existing `asset_id`, the disputed field, and a
public supporting source. Records are corrected rather than silently deleted;
material status or classification changes are noted in release documentation.
