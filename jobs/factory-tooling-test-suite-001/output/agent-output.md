Job done. Summary:

- Built a 12-test pytest suite in `tests/` under `cic-mcp-factory` that calls the real `validate-spec.sh`, `update-index.sh`, and `run-job.sh` (no mocks): 7 tests for `validate-spec.sh` (K1/K3/K4/K8 violations + GO case + edge cases), 2 for `update-index.sh` (normal + empty `jobs/`), 3 for `run-job.sh` (usage error, validate-spec NO-GO short-circuit, `--resume` flag routing).
- No script refactoring was needed — the `--resume` flag-parsing logic was testable as-is via an observable code-path difference, so the "Nem cél" constraint was respected without any exception.
- All 12 tests pass (`pytest tests/ -v` → `12 passed in 0.33s`); full output quoted in the report.
- Wrote `jobs/factory-tooling-test-suite-001/output/factory-tooling-test-suite-report.md` following the Universal Output Contract, with a filled claim-evidence matrix and an explicit Risks section listing what's *not* covered (git/agent integration in `run-job.sh`, interactive prompts, an implicit cwd assumption in `run-job.sh`'s `validate-spec.sh` call).
- Committed and pushed to `feature/factory-tooling-test-suite-001` (commit `3465a79`, Vault-signed). Since this job's target repo is `cic-mcp-factory` itself, output and tooling went in a single commit rather than two redundant pushes to the same repo.

Next: orchestrator review via `/job-close`, then a PR for this branch.
