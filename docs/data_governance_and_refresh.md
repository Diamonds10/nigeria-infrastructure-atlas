# Data governance and refresh policy

## Purpose

The atlas is maintained as a versioned public evidence platform, not a live
regulatory or operating registry. Every published layer must remain traceable
to a source, an access date, a processing path, a quality statement, and
source-specific reuse conditions.

## Refresh classes

- **Monthly:** actively changing incident feeds, currently NOSDRA oil-spill
  reports.
- **Quarterly:** OpenStreetMap-derived connectivity and the distributed-energy
  public-source registry.
- **Annual or source release:** UCDP historical security context, trackers,
  protected areas, population/access products, and slower-changing reference
  layers.

The machine-readable schedule is published at
`/api/v1/freshness.json`. A due date is a maintainer review target, not a claim
that the upstream publisher has released an update.

## Promotion gate

A new or corrected record is promoted only after review of:

1. source identity and public accessibility;
2. what the evidence actually verifies;
3. coordinates, geometry, and stated precision;
4. duplicate or superseded-record risk;
5. classification and status semantics;
6. source licence, terms, attribution, and redistribution limits;
7. schema, build, API, and regression-test results.

Uncertainty is retained as metadata or a caveat. It is not silently resolved by
guessing.

## Incident-data rules

NOSDRA records are described as reported incidents. Report status is preserved,
including invalid and inconclusive records. Implausible dates remain visible in
the processed source table for auditability but are excluded from analytical
timelines. State analytics use only records with valid publishable coordinates.

UCDP records are historical organized-violence observations under UCDP's
definitions, not a general crime or live threat feed. The public map aggregates
the latest annual release to half-degree cells and excludes exact event
coordinates, actor names, narratives, headlines, and source articles. State
analytics retain UCDP's low, best, and high fatality estimates.

## Contributions

The dedicated distributed-energy workflow remains the structured route for
mini-grid and off-grid data. The repository-wide **Atlas data submission or
correction** issue form accepts evidence for every other public section.
Maintainers may request a CSV or GeoJSON contribution when a proposal contains
multiple records.

## Releases and citation

Public-contract changes require a release-note entry, regenerated API outputs,
updated tests, and a matching version in `CITATION.cff`. Archived DOI releases
should be created only after the maintainer connects the repository to an
appropriate preservation service and verifies third-party redistribution
conditions; the atlas must never invent or pre-announce a DOI.
