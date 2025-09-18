---
name: github_gitlab
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - github
  - git
---

# GitHub & GitLab microagent

This microagent documents how the assistant should interact with GitHub and GitLab when asked to perform repository and pull/merge request operations.

Capabilities
- Use the GITHUB_TOKEN environment variable to call the GitHub REST API (via curl) when needed.
- Use the GITLAB_TOKEN environment variable to call the GitLab REST API (via curl) when needed.
- Create branches, push commits, and open pull requests (GitHub) or merge requests (GitLab).
- Always use the repository API for operations where applicable and the provided create_pr / create_mr tools to open PRs/MRs.

Environment variables / credentials
- GITHUB_TOKEN: token with repo access for GitHub operations. Use curl with an Authorization: Bearer $GITHUB_TOKEN header.
- GITLAB_TOKEN: token with api scope for GitLab operations. Use curl with "PRIVATE-TOKEN: $GITLAB_TOKEN" or "Authorization: Bearer $GITLAB_TOKEN".

Guidelines
- Prefer using the API endpoints over web scraping or browser automation.
- For GitHub PRs, ALWAYS use the create_pr tool to open pull requests.
- For GitLab MRs, ALWAYS use the create_mr tool to open merge requests.
- Never push directly to the `main` or `master` branches.
- Create a concise, descriptive branch name. Avoid duplicates by checking for existing branches and appending a timestamp/suffix when needed.
- If `git push` fails due to authentication, update the remote URL to include the token only if necessary and with explicit user approval. Example (GitHub):
  git remote set-url origin https://${GITHUB_TOKEN}@github.com/owner/repo.git

Error handling
- If API calls return 401/403: verify token and scopes. Provide a helpful error message mentioning which token and requested scopes are required.
- If push fails due to permission: suggest using the token-updated remote URL or ask the user to provide appropriate credentials.
- If create_pr/create_mr fails: include the API response body in the error (without leaking tokens) and suggest next steps.

Examples
- Open a GitHub PR after pushing a branch:
  1. Push branch: git push -u origin feature/add-thing
  2. Use create_pr with repo_name "owner/repo", source_branch "feature/add-thing", target_branch "main" and a short title + description.

- Open a GitLab MR after pushing a branch:
  1. Push branch: git push -u origin feature/add-thing
  2. Use create_mr with id or project path, source_branch and target_branch.

Notes
- Keep this microagent concise and focused on safe, consistent usage patterns.
- Avoid embedding tokens directly in commit messages or logs.
