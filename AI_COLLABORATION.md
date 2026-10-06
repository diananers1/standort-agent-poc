## Codex-assisted testing

Codex was used to generate the initial pytest suite for:
- data loading
- profile interpretation
- normalization
- specialist agents
- ranking/aggregation

I reviewed the generated tests, kept the behavior-focused cases, and ran the full suite locally with `pytest -q`.