#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess
import time
from datetime import datetime
import tempfile
import zipfile

import requests

TIMEOUT = 15


def fatal(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def repo_from_git():
    try:
        url = subprocess.check_output(["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        fatal("unable to determine git remote origin url")
    # handle formats like git@github.com:owner/repo.git or https://github.com/owner/repo.git
    if url.startswith("git@"):
        # git@github.com:owner/repo.git
        try:
            _, path = url.split(":", 1)
            owner_repo = path.rstrip(".git")
        except Exception:
            fatal("unable to parse git url")
    else:
        # https://.../owner/repo.git
        parts = url.rstrip(".git").split("/")
        if len(parts) < 2:
            fatal("unable to parse git url")
        owner_repo = "/".join(parts[-2:])
    return owner_repo


def gh_headers():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        fatal("GITHUB_TOKEN not set in environment")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def write_run(name, data):
    os.makedirs("runs", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_name = name.replace("/", "_")
    fname = f"runs/{ts}_{safe_name}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return fname


def pr_get(owner_repo, value):
    owner, repo = owner_repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=100"
    r = requests.get(url, headers=gh_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    prs = r.json()
    for pr in prs:
        head = pr.get("head", {})
        if head.get("ref") == value or head.get("sha") == value:
            # fetch detailed PR
            detail = requests.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr['number']}", headers=gh_headers(), timeout=TIMEOUT)
            detail.raise_for_status()
            d = detail.json()
            out = {"pr_url": d.get("html_url"), "number": d.get("number"), "head_sha": d.get("head", {}).get("sha"), "mergeable_state": d.get("mergeable_state")}
            write_run(f"pr_get_{value}", out)
            print(json.dumps(out))
            return
    out = {"pr_url": None, "number": None, "head_sha": None, "mergeable_state": None}
    write_run(f"pr_get_{value}", out)
    print(json.dumps(out))


def pr_create(owner_repo, base, head, title, body):
    owner, repo = owner_repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {"base": base, "head": head, "title": title, "body": body}
    r = requests.post(url, headers=gh_headers(), json=payload, timeout=TIMEOUT)
    if r.status_code >= 400:
        fatal(f"pr.create failed: {r.status_code} {r.text}")
    data = r.json()
    out = {"pr_url": data.get("html_url"), "number": data.get("number"), "head_sha": data.get("head", {}).get("sha")}
    write_run(f"pr_create_{head}", out)
    print(json.dumps(out))


def pr_squash_merge(owner_repo, number):
    owner, repo = owner_repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/merge"
    payload = {"merge_method": "squash"}
    r = requests.put(url, headers=gh_headers(), json=payload, timeout=TIMEOUT)
    if r.status_code == 405:
        fatal("merge not allowed")
    r.raise_for_status()
    data = r.json()
    out = {"merged": data.get("merged"), "message": data.get("message")}
    write_run(f"pr_merge_{number}", out)
    print(json.dumps(out))


def runs_list_by_head_sha(owner_repo, head_sha):
    owner, repo = owner_repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?head_sha={head_sha}&per_page=100"
    r = requests.get(url, headers=gh_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    runs = data.get("workflow_runs", [])
    summary = {"runs": []}
    for run in runs:
        summary[run.get("name") or str(run.get("id"))] = {"id": run.get("id"), "conclusion": run.get("conclusion"), "status": run.get("status")}
        summary["runs"].append({"id": run.get("id"), "name": run.get("name"), "conclusion": run.get("conclusion")})
    # smoke/e2e quick keys
    smoke = "unknown"
    e2e = "unknown"
    for run in runs:
        n = (run.get("name") or "").lower()
        if smoke == "unknown" and "smoke" in n:
            smoke = run.get("conclusion")
        if e2e == "unknown" and ("e2e" in n or "end-to-end" in n):
            e2e = run.get("conclusion")
    out = {"head_sha": head_sha, "smoke": smoke, "e2e": e2e, "runs": summary.get("runs")}
    write_run(f"runs_by_head_{head_sha}", out)
    print(json.dumps(out))


def runs_list_jobs(owner_repo, run_id):
    owner, repo = owner_repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    r = requests.get(url, headers=gh_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobs", [])
    failing = None
    for job in jobs:
        if job.get("conclusion") and job.get("conclusion") != "success":
            failing = job
            break
    if not failing:
        out = {"run_id": run_id, "failing_job": None, "excerpt": None}
        write_run(f"jobs_{run_id}", out)
        print(json.dumps(out))
        return
    job_id = failing.get("id")
    job_name = failing.get("name")
    # download logs zip
    logs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
    r2 = requests.get(logs_url, headers=gh_headers(), timeout=TIMEOUT, stream=True)
    if r2.status_code >= 400:
        # still return failing job name
        out = {"run_id": run_id, "failing_job": job_name, "excerpt": "unable to fetch logs"}
        write_run(f"jobs_{run_id}", out)
        print(json.dumps(out))
        return
    # save to temp file
    tmpf = tempfile.NamedTemporaryFile(delete=False)
    for chunk in r2.iter_content(1024*16):
        tmpf.write(chunk)
    tmpf.close()
    excerpt_lines = []
    try:
        with zipfile.ZipFile(tmpf.name) as z:
            # iterate files and read text files
            for fname in z.namelist():
                try:
                    with z.open(fname) as fh:
                        for raw in fh:
                            try:
                                line = raw.decode("utf-8", errors="replace")
                            except Exception:
                                line = str(raw)
                            excerpt_lines.append(line.rstrip("\n"))
                            if len(excerpt_lines) >= 100:
                                break
                except Exception:
                    continue
                if len(excerpt_lines) >= 100:
                    break
    except Exception:
        excerpt_lines = ["<unable to extract logs>"]
    finally:
        try:
            os.unlink(tmpf.name)
        except Exception:
            pass
    out = {"run_id": run_id, "failing_job": job_name, "excerpt_lines": excerpt_lines}
    write_run(f"jobs_{run_id}", out)
    print(json.dumps(out))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("pr.get_by_branch")
    sub.add_parser("pr.get_by_head")

    p_create = sub.add_parser("pr.create")
    p_create.add_argument("--base", required=True)
    p_create.add_argument("--head", required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--body", required=True)

    p_merge = sub.add_parser("pr.squash_merge")
    p_merge.add_argument("number")

    p_runs = sub.add_parser("runs.list_by_head_sha")
    p_runs.add_argument("head_sha")

    p_jobs = sub.add_parser("runs.list_jobs")
    p_jobs.add_argument("run_id")

    parser.add_argument("value", nargs="?")
    args = parser.parse_args()

    owner_repo = repo_from_git()

    if args.cmd == "pr.get_by_branch":
        if not args.value:
            fatal("missing branch value")
        pr_get(owner_repo, args.value)
    elif args.cmd == "pr.get_by_head":
        if not args.value:
            fatal("missing head SHA value")
        pr_get(owner_repo, args.value)
    elif args.cmd == "pr.create":
        pr_create(owner_repo, args.base, args.head, args.title, args.body)
    elif args.cmd == "pr.squash_merge":
        pr_squash_merge(owner_repo, args.number)
    elif args.cmd == "runs.list_by_head_sha":
        runs_list_by_head_sha(owner_repo, args.head_sha)
    elif args.cmd == "runs.list_jobs":
        runs_list_jobs(owner_repo, args.run_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
