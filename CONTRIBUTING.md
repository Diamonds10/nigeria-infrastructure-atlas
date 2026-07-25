# Contributing to the Nigeria Infrastructure Atlas

Thank you for helping improve Nigeria's open infrastructure evidence.

## Distributed-energy records

Use one of these routes:

1. For a single site or a correction, open the **Distributed-energy record**
   GitHub issue form.
2. For multiple sites, copy
   `data/contributions/07_renewables/distributed_energy_submission_template.csv`,
   validate it, and open a pull request.

```bash
python scripts/07_renewables/03_validate_distributed_energy_submission.py \
  path/to/submission.csv
```

Every proposed record needs a public evidence URL, a defensible location,
coordinate precision, and one of the four canonical classes:

- `community_mini_grid`
- `captive_institutional_off_grid`
- `standalone_system`
- `interconnected_mini_grid`

A passing automated check does not publish a record. Maintainers also review
the evidence, coordinates, duplication risk, classification, status, and reuse
conditions. See `docs/distributed_energy_contribution_guide.md`.

## General pull requests

For a single record, correction, source/licensing update, or data-quality
concern in any atlas section, use the **Atlas data submission or correction**
GitHub issue form. It captures evidence scope, location, geometry precision,
and source reuse terms before maintainer review.

- Keep raw, processed, and generated data responsibilities separate.
- Preserve source URLs, access dates, and source-specific caveats.
- Do not overwrite unrelated work.
- Run `make validate PYTHON=.venv/bin/python` before requesting review.
- Update documentation and release tests when a public contract changes.

By contributing, you confirm that you have the right to submit your own work
and that any referenced third-party data remains subject to its original terms.

See `docs/data_governance_and_refresh.md` for the repository-wide promotion
gate and maintenance cadence.
