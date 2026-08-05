# Third-party data rights and attribution

The repository's CC0 dedication applies only to original repository code,
documentation, and other material for which the contributors hold the necessary
rights. It does **not** replace or override the licenses, attribution
requirements, access terms, or other rights attached to third-party source data.
It also does not publish or license proprietary Infraxis financial-loss models,
parameters, software, client data, or premium services. This repository is the
open atlas / public datasource only; Infraxis premium products are a separate
layer outside it.

Processed datasets and map bundles may contain or derive from third-party data.
Anyone redistributing or commercially using those materials must review
`docs/data_sources.md` and comply with each applicable source's terms.
The machine-readable preservation gate is
`docs/redistribution_rights_register.csv`; see
`docs/zenodo_release_readiness.md` before creating an archival release.

Important examples include:

- Uppsala Conflict Data Program Georeferenced Event Dataset (UCDP GED) 26.1:
  Creative Commons Attribution 4.0 (CC BY 4.0). The public atlas republishes
  only derived half-degree exposure cells and state/year summaries, with UCDP
  attribution and the release's required dataset and codebook citations. It
  omits exact event coordinates, actor names, narratives, and source text.
- OpenStreetMap-derived connectivity data: Open Database License (ODbL).
- WDPA / Protected Planet data: source-specific terms, including restrictions
  described by UNEP-WCMC; do not assume CC0 or unrestricted commercial reuse.
- Global Energy Monitor material: attribution is expected; several mirror-based
  downloads have license uncertainty documented in the source register.
- Nigeria SE4ALL mini-grid data: publicly accessible, but the dataset page did
  not state explicit redistribution terms at the recorded access date.
- NOSDRA Oil Spill Monitor records: the publisher provides complete CSV/JSON
  downloads and encourages public use, but no formal open-data licence was
  stated at the recorded access date. Preserve attribution, the source
  disclaimer, report-status fields, and the distinction between reported and
  independently verified incidents.
- Refinery and demand-centre compilations (`refineries_nigeria.csv`,
  `demand_centers_nigeria.csv`): original atlas research synthesized from
  multiple independent public sources (NNPC/BPE disclosures, company sites,
  Global Energy Observatory, news coverage, and OSM Nominatim used to verify
  or correct individual coordinates), not copied wholesale from any single
  third-party database. Facts such as a plant's location, capacity, or
  commissioning year are not themselves copyrightable; only a database's
  particular selection or arrangement can be, and no single such database was
  reproduced here. This compilation is therefore treated as an original work
  under the repository's CC0-1.0 dedication (`redistribution_rights_register.csv`,
  `atlas_compilations` row) rather than as third-party material requiring
  external clearance. Where `docs/data_sources.md`'s `coordinate_source` column
  cites OpenStreetMap directly for a given row, that specific coordinate
  remains subject to OSM's ODbL attribution and share-alike terms regardless
  of this compilation's own status.

The public atlas is a derived screening product. Source attribution remains
required even when a derived file is stored in this repository.

The security layer is historical analytical context, not a live incident,
threat, travel-safety, or operational-security feed. Users should consult
current authoritative advice for time-sensitive decisions.
