# Distributed-energy contributions

Copy `distributed_energy_submission_template.csv`, add one or more records, and
submit the completed CSV in a pull request. Do not edit the canonical processed
registry directly.

Validate a submission locally:

```bash
python scripts/07_renewables/03_validate_distributed_energy_submission.py path/to/submission.csv
```

Files in this directory are intake records, not automatically published map
assets. Acceptance requires the verification workflow documented in
`docs/distributed_energy_contribution_guide.md`.
