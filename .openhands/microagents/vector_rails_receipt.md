---
name: vector rails receipt
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - "vector rails receipt"
summary: "Assist with generating a "receipt" summary for vectors produced by the Rails component and integrate with repository PR flows."
---

# Vector Rails Receipt Microagent

When triggered with `vector rails receipt`, this microagent should:

- Summarize recent vectorization operations performed by the Rails subsystem (e.g., number of items processed, index sizes, timestamped receipts).
- Provide a short machine-readable receipt that includes: operation_id, processed_count, index_name, head_sha, timestamp, and any warnings or errors.
- Offer commands or code snippets for retrieving more detailed logs using existing repo helpers (e.g., python scripts/oh_gh.py runs.list_by_head_sha <sha>). 

Limitations:
- This microagent is ephemeral and MUST NOT persist secrets or write config files under .openhands/.
- It should operate within the assistant runtime and use provided repository helpers where possible.
