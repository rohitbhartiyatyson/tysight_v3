---
name: tysight_repo_microagent
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - tysight_microagent
  - repo_layout
  - openhands_run_contract
---

# Tysight v3 — OpenHands Microagent

Purpose
- Provide authoritative repo layout and the Ultra-Minimal Run Contract for contributors and automated assistants.

Authoritative project layout (canonical)
- insight_agent/
- tools/
- handoff/
- domain/catalog/{kinds,datasets}/
- runs/
- logs/

Primary responsibilities when triggered
- Ensure the repository contains the expected layout and helper scripts.
- Enforce the Output Protocol: every response must be prefixed with the exact token "Below is the OpenHands Output:" and include the RUN RECEIPT block when finishing tasks.
- Provide and maintain handoff artifacts: handoff/capsule.md, handoff/status.json, handoff/new_chat_bundle.md.
- Create or validate scripts/oh_gh.py exists and provide the documented commands for PR and Actions interactions.

Run contract highlights (summary)
- One shell command per tool call; single-line commands only.
- All file edits must be atomic Python one-liners.
- Use scripts/oh_gh.py for all GitHub interactions (pr.get_by_branch, pr.create, runs.list_by_head_sha, runs.list_jobs, pr.squash_merge).
- Never push to main; use feature branches like feat/<desc>.

What this microagent provides to assistants
- Clear instructions about response prefixing and the exact RUN RECEIPT template.
- Where to find and how to update handoff artifacts.
- Guidance to create or validate scripts/oh_gh.py when missing.

Limitations & security
- Does not store or surface secrets. Assistants must use GITHUB_TOKEN from environment.
- Network operations to GitHub must use the helper script; direct curl calls are disallowed.

Usage examples
- Trigger phrase: "tysight_microagent"
- Assistant action: validate layout, ensure scripts/oh_gh.py present, update handoff/status.json, and produce the required end-of-task prints.
