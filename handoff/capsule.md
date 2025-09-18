# Tysight v3 - Handoff Capsule

Objective
- Apply Ultra-Minimal Run Contract + Run Receipt for CI/PR merging and handoff.

Canonical constraints
- Kind: minimal, reproducible verification artifacts.
- Instance: this repo clone at current branch/HEAD.
- NL→SQL rules: none applicable in this task; keep procedural steps explicit.

What’s implemented (baseline)
- Created scripts/oh_gh.py: a small wrapper for GitHub PR and Actions queries and operations (get PR by branch/head, create PR, squash merge, list runs by head SHA, list jobs and extract failing excerpts). It writes JSON artifacts into runs/.
- Created handoff/status.json with branch and HEAD info and ci keys.

Current status
- Repo present and on branch main at HEAD commit.
- GITHUB_TOKEN present in environment.
- Direct GitHub network operations will use scripts/oh_gh.py; no API calls performed yet.

How to reproduce state
- git rev-parse --abbrev-ref HEAD
- git rev-parse HEAD
- ls -la scripts/oh_gh.py handoff/status.json
