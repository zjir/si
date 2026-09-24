#!/usr/bin/env python3
"""Creates or restarts agent-loop tasks from GitHub Actions (workflow_dispatch forms).

Inputs come from environment variables (never interpolated into the shell):
  new:      IN_TITLE, IN_MODE, IN_GOAL, IN_DONE_WHEN, IN_SCOPE_ALLOW, IN_INPUTS,
            IN_MAX_ROUNDS, IN_MAX_MINUTES, IN_ADVANCED
  restart:  IN_TASK_ID, IN_FROM_SCRATCH
Writes the path of the changed task file and a commit message to $GITHUB_OUTPUT.
"""
import datetime
import json
import os
import re
import subprocess
import sys

FOLDERS = ("inbox", "active", "done")
ID_RE = re.compile(r"^TASK-(\d{4,6})$")
ADVANCED_KEYS = {"scope_deny", "priority", "notes", "inputs"}


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def split_list(v):
    return [x.strip() for x in re.split(r"[,;\n]", v or "") if x.strip()]


def to_int(name, v, lo=1):
    try:
        n = int(str(v).strip())
    except ValueError:
        fail(f"{name} must be a number, got {v!r}")
    if n < lo:
        fail(f"{name} must be >= {lo}")
    return n


def all_task_files():
    for f in FOLDERS:
        d = os.path.join("tasks", f)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.endswith(".json"):
                yield f, name


def next_id():
    mx = 0
    for _, name in all_task_files():
        m = ID_RE.match(name[:-5])
        if m:
            mx = max(mx, int(m.group(1)))
    return f"TASK-{mx + 1:04d}"


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def output(**kw):
    out = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in kw.items())
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(lines)
    print(lines, end="")


def cmd_new():
    e = os.environ
    title = e.get("IN_TITLE", "").strip()
    mode = e.get("IN_MODE", "spec").strip()
    goal = e.get("IN_GOAL", "").strip()
    done_when = e.get("IN_DONE_WHEN", "").strip()
    scope_allow = split_list(e.get("IN_SCOPE_ALLOW"))
    inputs = split_list(e.get("IN_INPUTS"))
    if not title:
        fail("title is empty")
    if mode not in ("spec", "code"):
        fail("mode must be spec or code")
    if not goal:
        fail("goal is empty")
    if not done_when:
        fail("done_when is empty")
    if not scope_allow:
        fail("scope_allow is empty")
    max_rounds = to_int("max_rounds", e.get("IN_MAX_ROUNDS", "5"))
    max_minutes = to_int("max_minutes", e.get("IN_MAX_MINUTES", "60"))
    try:
        adv = json.loads(e.get("IN_ADVANCED") or "{}")
    except json.JSONDecodeError as ex:
        fail(f"advanced is not valid JSON: {ex}")
    if not isinstance(adv, dict):
        fail("advanced must be a JSON object")
    unknown = set(adv) - ADVANCED_KEYS
    if unknown:
        fail(f"advanced: unknown keys {sorted(unknown)}; allowed {sorted(ADVANCED_KEYS)}")
    task_id = next_id()
    task = {
        "id": task_id,
        "title": title,
        "mode": mode,
        "goal": goal,
        "done_when": done_when,
        "inputs": inputs + [x for x in adv.get("inputs", []) if x not in inputs],
        "scope_allow": scope_allow,
        "scope_deny": list(adv.get("scope_deny", [])),
        "max_rounds": max_rounds,
        "max_minutes": max_minutes,
        "priority": to_int("priority", adv.get("priority", 100), lo=-10**9),
        "notes": str(adv.get("notes", "")),
        "created_at": now_iso(),
    }
    path = f"tasks/inbox/{task_id}.json"
    write_json(path, task)
    output(task_id=task_id, path=path, message=f"task: {task_id} {title}")


def cmd_restart():
    e = os.environ
    task_id = e.get("IN_TASK_ID", "").strip().upper()
    if not ID_RE.match(task_id):
        fail(f"invalid task_id {task_id!r}")
    from_scratch = e.get("IN_FROM_SCRATCH", "false").strip().lower() == "true"
    src = None
    for f in ("active", "done"):
        p = f"tasks/{f}/{task_id}.json"
        if os.path.exists(p):
            src = p
            break
    if src is None:
        if os.path.exists(f"tasks/inbox/{task_id}.json"):
            fail(f"{task_id} is already queued in tasks/inbox")
        fail(f"{task_id} not found in tasks/active or tasks/done")
    with open(src, encoding="utf-8") as fh:
        task = json.load(fh)
    task["restart"] = from_scratch
    write_json(src, task)
    dst = f"tasks/inbox/{task_id}.json"
    subprocess.run(["git", "mv", "-f", src, dst], check=True)
    state_path = f"runs/{task_id}/state.json"
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as fh:
            st = json.load(fh)
        st["status"] = "queued"
        st["phase"] = "queued"
        write_json(state_path, st)
    suffix = " from scratch" if from_scratch else ""
    output(task_id=task_id, path=dst, message=f"task: restart {task_id}{suffix}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("new", "restart"):
        fail("usage: task_tool.py new|restart")
    cmd_new() if sys.argv[1] == "new" else cmd_restart()
