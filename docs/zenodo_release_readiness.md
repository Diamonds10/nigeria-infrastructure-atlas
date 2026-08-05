# Zenodo release readiness

## Current decision

**Do not publish a permanent whole-repository Zenodo record yet.**

The atlas is technically ready for preservation, but several tracked processed
and curated datasets do not yet have explicit redistribution authority recorded.
A public GitHub repository and an upstream download endpoint are not, by
themselves, proof that a third-party dataset may be copied into a permanent
archive.

The authoritative gate is
[`redistribution_rights_register.csv`](redistribution_rights_register.csv).
Run:

```bash
python scripts/check_zenodo_readiness.py
```

The command exits successfully only when every source family is marked
`cleared`. It reports the unresolved source families otherwise. Do not weaken
the gate by treating “publicly accessible”, “open portal”, or an inferred
licence as clearance.

## Blocking source families

At the 25 July 2026 review, the whole-repository deposit is blocked by:

- Global Energy Monitor files served through GreenInfo Network mirrors;
- Nigeria SE4ALL WFS datasets;
- extracted OPEC statistical tables;
- the World Bank gas-flaring release until its exact licence is recorded;
- WDPA / Protected Planet redistribution conditions;
- NOSDRA bulk-derived records;
- mixed-source distributed-energy supplements; and
- atlas/user-supplied compilations whose underlying reuse basis needs a
  record-level confirmation.

UCDP GED 26.1, OpenStreetMap, WorldPop/GRID3, the World Bank DRE Atlas, and U.S.
government sources have clear reuse frameworks, subject to their stated
attribution and share-alike conditions.

## Clearance evidence

For each unresolved row, retain one of:

1. a stable publisher licence page that covers the exact dataset and release;
2. terms bundled with the downloaded archive;
3. written permission from the rights holder; or
4. a documented decision to exclude the affected files from the archival
   package.

Save the evidence URL or correspondence reference in the register, change the
status only after review, and record the required attribution or restriction in
`THIRD_PARTY_DATA.md`.

## Publication procedure after the gate passes

1. Run the atlas build, unit tests, compilation check, and
   `scripts/check_zenodo_readiness.py`.
2. Decide whether the record archives the whole repository or a rights-cleared
   subset. List excluded paths explicitly if a subset is used.
3. Add final creator identities and ORCIDs to `CITATION.cff`.
4. Add Zenodo metadata describing the mixed licences; do not apply the
   repository's CC0 dedication to third-party files.
5. Connect `Diamonds10/infraxis-atlas-nigeria` in Zenodo's GitHub
   integration.
6. Create a signed semantic-version GitHub release only after the integration
   is enabled. Zenodo will archive the release.
7. Verify the archived file manifest, attribution, licence fields, version DOI,
   and concept DOI before adding the DOI to the README and citation metadata.

Publishing is intentionally a maintainer-controlled action: a Zenodo DOI becomes
a permanent scholarly identifier, and the archived files must match the rights
review exactly.
