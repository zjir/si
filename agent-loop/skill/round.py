#!/usr/bin/env python3
"""Jedno kolo agent loopu bez runneru (pro skill agent-loop-run-task).

Dělá to, co loop.ps1 dělá kolem jednoho kola; samotnou práci agenta dělá volající (Claude ve skillu)
podle agent-loop/prompts/common.md + role z config.json + runs/<id>/round-NN/context.md.

  python3 agent-loop/skill/round.py new      --json <soubor s úkolem> [--push]
  python3 agent-loop/skill/round.py status   [--id TASK-0007 | --latest]
  python3 agent-loop/skill/round.py prepare  [--id TASK-0007 | --latest] --model <id modelu chatu> [--push] [--takeover] [--force]
  python3 agent-loop/skill/round.py checkpoint --id TASK-0007 [--push]
  python3 agent-loop/skill/round.py finalize --id TASK-0007 --model <id modelu chatu> [--push]
  python3 agent-loop/skill/round.py abort    --id TASK-0007 [--push]

Spouští se z kořene repozitáře (lokálně nebo v klonu z GitHubu). --push = po commitu
fetch + rebase na origin/<větev> + push. prepare zapíše do state.json claim (runner: skill,
claim_until); runner takový úkol přeskakuje (Test-SkillClaim v AgentLoop.ps1), po vypršení
claimu kolo obnoví jako přerušené. Výstup: JSON na stdout.
"""
import argparse, datetime, fnmatch, json, os, re, shutil, subprocess, sys, time

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Prague")
except Exception:  # pragma: no cover
    TZ = None

ROOT = os.getcwd()
FOLDERS = ["inbox", "active", "done"]
MARK = "SKILL "  # obsah STOP, který vytvořil tento skript


def now():
    d = datetime.datetime.now(TZ) if TZ else datetime.datetime.now().astimezone()
    return d.replace(microsecond=0).isoformat()


def p(rel):
    return os.path.join(ROOT, rel.replace("/", os.sep))


def rj(rel):
    try:
        with open(p(rel), encoding="utf-8-sig") as f:
            t = f.read()
        return json.loads(t) if t.strip() else None
    except (OSError, ValueError):
        return None


def wj(rel, obj):
    os.makedirs(os.path.dirname(p(rel)), exist_ok=True)
    with open(p(rel), "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def wt(rel, text):
    os.makedirs(os.path.dirname(p(rel)), exist_ok=True)
    with open(p(rel), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def rt(rel):
    with open(p(rel), encoding="utf-8-sig") as f:
        return f.read()


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code)


def fail(msg, **kw):
    out(dict(ok=False, error=msg, **kw), 1)


# ------------------------------------------------------------------ git

_ident = None


def git(*args, allow_fail=False):
    global _ident
    env = os.environ.copy()
    if _ident is None:
        r = subprocess.run(["git", "log", "-1", "--format=%an%n%ae"], cwd=ROOT, capture_output=True, text=True)
        lines = r.stdout.splitlines()
        _ident = lines if len(lines) == 2 else []
    if _ident:
        env.update(GIT_AUTHOR_NAME=_ident[0], GIT_COMMITTER_NAME=_ident[0],
                   GIT_AUTHOR_EMAIL=_ident[1], GIT_COMMITTER_EMAIL=_ident[1])
    for attempt in range(4):
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env)
        if r.returncode == 0 or "index.lock" not in r.stderr or attempt == 3:
            break
        time.sleep(5)
    if r.returncode != 0 and not allow_fail:
        fail("git " + " ".join(args) + " selhal: " + r.stderr.strip())
    return r


def changes():
    r = git("status", "--porcelain=v1", "-z", "-uall")
    parts, items, i = r.stdout.split("\0"), [], 0
    while i < len(parts):
        e = parts[i]
        if len(e) >= 4:
            items.append((e[:2], e[3:]))
            if e[0] in "RC":
                i += 1
                if i < len(parts) and parts[i]:
                    items.append((e[:2], parts[i]))
        i += 1
    return items


def foreign_changes():
    # stejně jako runner: nové soubory v tasks/inbox nevadí
    return [c for c in changes() if not (c[0] == "??" and re.match(r"^tasks/inbox/[^/]+\.json$", c[1]))]


def commit(subject, body, paths):
    paths = sorted(set(x for x in paths if x))
    # git add selže na cestě, která neexistuje ani není v indexu (např. netrackovaný soubor po přesunu)
    paths = [x for x in paths if os.path.exists(p(x))
             or git("ls-files", "--error-unmatch", "--", x, allow_fail=True).returncode == 0]
    if paths:
        git("add", "-A", "--", *paths)
    if git("diff", "--cached", "--quiet", allow_fail=True).returncode == 0:
        return None
    msg = subject + ("\n\n" + body if body else "") + "\n"
    git("commit", "-q", "-m", msg)
    return git("rev-parse", "--short", "HEAD").stdout.strip()


def push():
    """fetch + rebase + push. Vrací dict(ok, error?, patch_dir?)."""
    br = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for attempt in range(2):
        f = git("fetch", "-q", "origin", allow_fail=True)
        if f.returncode != 0:
            return dict(ok=False, error="fetch: " + f.stderr.strip())
        if git("rev-parse", "--verify", "-q", "origin/" + br, allow_fail=True).returncode == 0:
            rb = git("rebase", "-q", "origin/" + br, allow_fail=True)
            if rb.returncode != 0:
                git("rebase", "--abort", allow_fail=True)
                pd = os.path.join(ROOT, ".git", "skill-patches")
                shutil.rmtree(pd, ignore_errors=True)
                git("format-patch", "-q", "origin/%s..HEAD" % br, "-o", pd, allow_fail=True)
                return dict(ok=False, error="konflikt s origin/%s (pravděpodobně runner pracoval na stejných souborech): %s"
                            % (br, rb.stderr.strip()), patch_dir=pd)
        ps = git("push", "-q", "origin", "HEAD:refs/heads/" + br, allow_fail=True)
        if ps.returncode == 0:
            return dict(ok=True, branch=br, head=git("rev-parse", "--short", "HEAD").stdout.strip())
    return dict(ok=False, error="push: " + ps.stderr.strip())


# ------------------------------------------------------------------ scope (port ConvertTo-GlobRegex / Test-PathMatch)

def glob_re(g):
    g = g.replace("\\", "/").strip()
    if g.endswith("/"):
        g += "**"
    s, i = "^", 0
    while i < len(g):
        c = g[i]
        if c == "*":
            if g[i + 1:i + 2] == "*":
                if g[i + 2:i + 3] == "/":
                    s += "(?:.*/)?"; i += 3; continue
                s += ".*"; i += 2; continue
            s += "[^/]*"; i += 1; continue
        if c == "?":
            s += "[^/]"; i += 1; continue
        s += re.escape(c); i += 1
    return s + "$"


def path_match(path, globs):
    path = path.replace("\\", "/")
    for g in globs:
        if not g:
            continue
        if re.match(glob_re(g), path, re.IGNORECASE):
            return True
        if not re.search(r"[*?]", g) and path.lower().startswith(g.rstrip("/").lower() + "/"):
            return True
    return False


def in_scope(path, F, task_dir):
    path = path.replace("\\", "/")
    if path.startswith(task_dir + "/") or path == "agent-loop/a1/data.js":
        return True
    if re.match(r"^tasks/inbox/[^/]+\.json$", path):
        return True
    if path_match(path, F["scope_deny"]):
        return False
    return path_match(path, F["scope_allow"])


# ------------------------------------------------------------------ tasks

def cfg():
    c = rj("agent-loop/config.json")
    if c is None:
        fail("chybí agent-loop/config.json (spouštěj z kořene repozitáře)")
    return c


def all_tasks():
    res = []
    for f in FOLDERS:
        d = p("tasks/" + f)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if n.endswith(".json"):
                res.append(dict(folder=f, name=n, rel="tasks/%s/%s" % (f, n), task=rj("tasks/%s/%s" % (f, n)) or {}))
    return res


def task_num(i):
    m = re.match(r"^TASK-(\d{4,6})$", i or "")
    return int(m.group(1)) if m else -1


def str_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in re.split(r"[,;\n]", v) if x.strip()]
    return [str(x) for x in v if str(x)]


def fields(t, c):
    return dict(
        id=str(t.get("id") or ""), title=str(t.get("title") or ""), mode=str(t.get("mode") or "spec"),
        goal=str(t.get("goal") or ""), done_when=str(t.get("done_when") or ""),
        inputs=str_list(t.get("inputs")), scope_allow=str_list(t.get("scope_allow")),
        scope_deny=str_list(t.get("scope_deny")),
        max_rounds=int(t.get("max_rounds") or c.get("default_max_rounds", 5)),
        max_minutes=int(t.get("max_minutes") or c.get("default_max_minutes", 60)),
        priority=int(t.get("priority") if t.get("priority") is not None else 100),
        notes=str(t.get("notes") or ""))


def validate(F):
    e = []
    if F["mode"] not in ("spec", "code"): e.append("mode must be spec or code")
    if not F["title"]: e.append("title is empty")
    if not F["goal"]: e.append("goal is empty")
    if not F["done_when"]: e.append("done_when is empty")
    if not F["scope_allow"]: e.append("scope_allow is empty")
    if F["max_rounds"] < 1: e.append("max_rounds < 1")
    if F["max_minutes"] < 1: e.append("max_minutes < 1")
    return e


def select(task_id, latest=False):
    ts = all_tasks()
    if latest and not task_id:
        c = [t for t in ts if t["folder"] == "inbox"]
        if not c:
            fail("tasks/inbox je prázdný")
        c.sort(key=lambda t: (task_num(t["name"][:-5]), str(t["task"].get("created_at") or ""), t["name"]))
        return c[-1]
    if task_id:
        hit = [t for t in ts if t["name"] == task_id + ".json" or t["task"].get("id") == task_id]
        if not hit:
            fail("úkol %s neexistuje v tasks/inbox|active|done" % task_id)
        return hit[0]
    for f in ("active", "inbox"):
        c = [t for t in ts if t["folder"] == f]
        if c:
            c.sort(key=lambda t: (int(t["task"].get("priority") or 100), str(t["task"].get("created_at") or ""), t["name"]))
            return c[0]
    fail("žádný úkol v tasks/active ani tasks/inbox")


def loop_lock(c):
    lk = rj(".loop.lock")
    if not lk or not lk.get("heartbeat"):
        return None
    try:
        hb = datetime.datetime.fromisoformat(lk["heartbeat"])
        age = (datetime.datetime.now(hb.tzinfo) - hb).total_seconds() / 60
    except ValueError:
        return None
    # smyčka obnovuje zámek každých 5 s při čekání a heartbeat_seconds při kole
    return dict(lock=lk, age_min=round(age, 1), fresh=age < 10)


def stop_text():
    try:
        return rt("STOP")
    except OSError:
        return None


def round_dir(i, n):
    return "runs/%s/round-%02d" % (i, n)


def checks(c, need_clean=True):
    lk = loop_lock(c)
    if lk and lk["fresh"]:
        fail("smyčka běží (.loop.lock heartbeat před %s min). Zastav ji: agent-loop\\start-loop.cmd stop a počkej na konec kola." % lk["age_min"])
    st = stop_text()
    if st and st.startswith(MARK):
        fail("STOP od nedokončeného kola skillu: " + st.strip() + ". Dokonči ho (finalize) nebo zruš (abort).")
    if need_clean:
        fc = foreign_changes()
        if fc:
            fail("pracovní strom není čistý; commitni nebo vrať změny", changes=[x[1] for x in fc])
    return lk, st


# ------------------------------------------------------------------ commands

def cmd_status(a):
    c = cfg()
    t = select(a.id, a.latest)
    F = fields(t["task"], c)
    s = rj("runs/%s/state.json" % (F["id"] or t["name"][:-5])) or {}
    rnd = int(s.get("round") or 0)
    last = int(s.get("run_start_round") or 0) + F["max_rounds"] if t["folder"] != "inbox" else F["max_rounds"]
    out(dict(ok=True, task=F["id"], folder=t["folder"], title=F["title"], mode=F["mode"],
             state_status=s.get("status"), phase=s.get("phase"), next_round=rnd + 1, last_round=last,
             loop_lock=loop_lock(c), stop=stop_text(), foreign_changes=[x[1] for x in foreign_changes()],
             config_model=c.get("model"), config_effort=c.get("effort")))


def cmd_prepare(a):
    c = cfg()
    _, stop_before = checks(c)
    t = select(a.id, a.latest)
    if t["folder"] == "done":
        fail("úkol je v tasks/done; restart: agent-loop\\start-loop.cmd restart -Id %s" % t["name"][:-5])
    paths = []
    if t["folder"] == "inbox":
        raw = dict(t["task"])
        tid = str(raw.get("id") or "")
        ok = task_num(tid) > 0 and t["name"] == tid + ".json"
        if ok and any(x["rel"] != t["rel"] and x["name"] == tid + ".json" for x in all_tasks()):
            ok = False
        if not ok:
            mx = 0
            for x in all_tasks():
                mx = max(mx, task_num(x["name"][:-5]), task_num(str(x["task"].get("id") or "")))
            tid = "TASK-%04d" % (mx + 1)
            raw["id"] = tid
        raw.setdefault("created_at", now())
        raw.pop("restart", None)
        F = fields(raw, c)
        errs = validate(F)
        if errs:
            fail("neplatný úkol: " + "; ".join(errs) + " (soubor nechán v inbox)")
        tracked = git("ls-files", "--error-unmatch", "--", t["rel"], allow_fail=True).returncode == 0
        wj(t["rel"], raw)
        dest = "tasks/active/%s.json" % tid
        if tracked:
            git("mv", "-f", "--", t["rel"], dest)
        else:
            os.makedirs(os.path.dirname(p(dest)), exist_ok=True)
            shutil.move(p(t["rel"]), p(dest))
        paths += [t["rel"], dest]
        s = rj("runs/%s/state.json" % tid)
        if s is None:
            s = dict(task=tid, status="running", phase="queued", round=0, run_start_round=0, started_at=now(),
                     ended_at=None, heartbeat=now(), last_status=None, last_summary=None, push_failed=False)
        else:
            s.update(status="running", run_start_round=int(s.get("round") or 0), ended_at=None)
        # claim už ve start commitu: runner úkol po pullu nepřevezme a kontrola níže ho nepovažuje za běžící u runneru
        s.update(runner="skill", claim_until=(datetime.datetime.fromisoformat(now()) + datetime.timedelta(
            minutes=int(raw.get("max_minutes") or c.get("default_max_minutes", 60)) + 30)).isoformat(), updated_at=now())
        wj("runs/%s/state.json" % tid, s)
        paths.append("runs/%s/state.json" % tid)
        commit("%s start [%s] %s" % (tid, F["mode"], F["title"]), "", paths)
        t = dict(folder="active", name=tid + ".json", rel=dest, task=raw)
    F = fields(t["task"], c)
    tid = F["id"]
    task_dir = "runs/" + tid
    s = rj(task_dir + "/state.json") or dict(task=tid, status="running", phase="queued", round=0,
                                              run_start_round=0, started_at=now(), push_failed=False)
    if s.get("runner") == "skill" and s.get("phase") == "running" and not a.takeover:
        fail("kolo %s už běží ve skillu (jiný chat), claim do %s. Po vypršení ho obnoví runner; převzetí: --takeover"
             % (s.get("current_round"), s.get("claim_until")))
    if s.get("runner") == "skill" and s.get("phase") == "running" and a.takeover:
        s["round"] = int(s.get("current_round") or 1) - 1
        s["phase"] = "between_rounds"
    if s.get("phase") in ("running", "retry_wait"):
        fail("kolo %s je podle state.json rozběhnuté smyčkou (phase=%s); nech ho obnovit runnerem: agent-loop\\start-loop.cmd once" % (s.get("current_round"), s.get("phase")))
    if s.get("status") == "model_mismatch":
        fail("úkol je pozastavený kvůli MODEL_MISMATCH; vyřeš ho v runneru")
    hb = s.get("heartbeat")
    if (not a.force and s.get("status") == "running" and s.get("runner") != "skill" and hb
            and hb != s.get("skill_heartbeat") and t["folder"] == "active"):
        try:
            age = (datetime.datetime.now(TZ) - datetime.datetime.fromisoformat(hb)).total_seconds() / 60
        except (ValueError, TypeError):
            age = 1e9
        if age < F["max_minutes"] + 10:
            fail("úkol podle state.json zpracovává runner (heartbeat před %d min); souběh by skončil konfliktem. Zastav smyčku, nebo --force." % age)
    n = int(s.get("round") or 0) + 1
    last = int(s.get("run_start_round") or 0) + F["max_rounds"]
    if n > last:
        fail("vyčerpáno %d kol (max_rounds); restart: agent-loop\\start-loop.cmd restart -Id %s" % (F["max_rounds"], tid))
    rd = round_dir(tid, n)
    if os.path.isdir(p(rd)):
        shutil.rmtree(p(rd))
    os.makedirs(p(rd))
    # kontext kola: stejná šablona a texty jako runner
    S = rj("agent-loop/prompts/strings.json") or {}
    empty = S.get("empty_list", "- -")
    fl = lambda xs: "\n".join("- `%s`" % x for x in xs) if xs else empty
    prev = round_dir(tid, n - 1) if n > 1 and os.path.isdir(p(round_dir(tid, n - 1))) else None
    m = dict(ID=tid, TITLE=F["title"], MODE=F["mode"], ROUND=n, LAST_ROUND=last, DATE=now(), GOAL=F["goal"],
             DONE_WHEN=F["done_when"], INPUTS=fl(F["inputs"]), SCOPE_ALLOW=fl(F["scope_allow"]),
             SCOPE_DENY=fl(F["scope_deny"]), TASK_DIR=task_dir, ROUND_DIR=rd,
             STATE_NOTE="" if os.path.exists(p(task_dir + "/state.md")) else S.get("state_missing", ""),
             PREV_RESULT=("`%s/result.json`" % prev) if prev else S.get("no_prev_result", "-"),
             PREV_DIFF=("`%s/diff.patch`" % prev) if prev and os.path.exists(p(prev + "/diff.patch")) else S.get("no_prev_diff", "-"),
             NOTES=F["notes"] or S.get("no_notes", "-"))
    ctx = rt("agent-loop/prompts/context.template.md")
    for k, v in m.items():
        ctx = ctx.replace("{{%s}}" % k, str(v))
    wt(rd + "/context.md", ctx)
    until = datetime.datetime.fromisoformat(now()) + datetime.timedelta(minutes=F["max_minutes"] + 30)
    s.update(status="running", phase="running", current_round=n, heartbeat=now(), runner="skill",
             skill_model=a.model, skill_round_started_at=now(), claim_until=until.isoformat(), updated_at=now())
    s.pop("agent_pid", None)
    wj(task_dir + "/state.json", s)
    commit("%s r%02d claim [%s] runner=skill model=%s" % (tid, n, F["mode"], a.model), "", [task_dir + "/state.json"])
    pushed = push() if a.push else None
    if pushed and not pushed["ok"]:
        fail("claim se nepodařilo pushnout; kolo nezačínej: " + pushed["error"], push=pushed)
    if stop_before is None:
        wt("STOP", "%s%s r%02d: kolo běží ve skillu agent-loop-run-task (%s)\n" % (MARK, tid, n, now()))
    prompts = c.get("prompts", {})
    out(dict(ok=True, task=tid, round=n, last_round=last, mode=F["mode"],
             read_in_order=[prompts.get("common", "agent-loop/prompts/common.md"),
                            prompts.get(F["mode"], "agent-loop/review-loop/review.md"), rd + "/context.md"],
             tools_allowed=c.get("tools", {}).get(F["mode"]), max_minutes=F["max_minutes"],
             scope_allow=F["scope_allow"], scope_deny=F["scope_deny"], task_dir=task_dir, round_dir=rd,
             stop_created=stop_before is None, claim_until=until.isoformat(), push=pushed))


def cmd_finalize(a):
    c = cfg()
    lk = loop_lock(c)
    if lk and lk["fresh"]:
        fail("smyčka mezitím naběhla (.loop.lock); nefinalizuji, vyřeš ručně")
    t = select(a.id)
    F = fields(t["task"], c)
    tid, task_dir = F["id"], "runs/" + F["id"]
    s = rj(task_dir + "/state.json") or {}
    if s.get("runner") != "skill" or s.get("phase") != "running":
        fail("úkol nemá rozběhnuté kolo skillu (state.json runner/phase)")
    n = int(s.get("current_round"))
    last = int(s.get("run_start_round") or 0) + F["max_rounds"]
    rd = round_dir(tid, n)
    res = rj(rd + "/result.json")
    status = str((res or {}).get("status") or "")
    no_result = status not in ("DONE", "CONTINUE", "BLOCKED")
    ch = changes()
    viol = [x[1] for x in ch if not in_scope(x[1], F, task_dir)]
    for code, path in ch:
        if path in viol and not (code == "??" and re.match(r"^tasks/inbox/[^/]+\.json$", path)):
            if os.path.isfile(p(path)):
                dst = rd + "/discarded/" + path
                os.makedirs(os.path.dirname(p(dst)), exist_ok=True)
                shutil.copy2(p(path), p(dst))
            if code == "??":
                os.remove(p(path))
            else:
                git("checkout", "-q", "HEAD", "--", path, allow_fail=True)
    work = in_scope_work(F, task_dir)
    git("add", "-A", "--", *[x for x in [task_dir, *work] if os.path.exists(p(x)) or
                              git("ls-files", "--", x, allow_fail=True).stdout.strip()])
    # celé kolo včetně checkpointů: diff proti commitu claim
    base = round_base(tid, n)
    rng = [base] if base else []
    work = sorted(set(work) | set(x for x in git("diff", "--cached", "--name-only", *rng, "--", ".",
                                                   ":(exclude)%s/**" % task_dir, ":(exclude)agent-loop/a1/data.js",
                                                   ":(exclude)tasks/**", allow_fail=True).stdout.split("\n") if x.strip()))
    d = git("diff", "--cached", *rng, "--stat", "-p", "--", ".", ":(exclude)%s/**" % rd,
            ":(exclude)%s/state.json" % task_dir, ":(exclude)agent-loop/a1/data.js", allow_fail=True).stdout
    if d:
        mx = int(c.get("diff_max_kb", 200)) * 1024
        b = d.encode("utf-8")
        wt(rd + "/diff.patch", d if len(b) <= mx else b[:mx].decode("utf-8", "ignore") + "\n... (zkráceno)\n")
    started = s.get("skill_round_started_at") or now()
    ended = now()
    try:
        dur = int((datetime.datetime.fromisoformat(ended) - datetime.datetime.fromisoformat(started)).total_seconds())
    except ValueError:
        dur = None
    meta = dict(task=tid, round=n, mode=F["mode"], runner="skill", skill_model=a.model,
                requested_model=c.get("model"), requested_effort=c.get("effort"), actual_models=[],
                effort_verified=False, claude_version=None, bare=False, input_tokens=None, output_tokens=None,
                cache_read_tokens=None, cache_creation_tokens=None, cost_usd=None, num_turns=None, is_error=False,
                session_id=None, started_at=started, ended_at=ended, duration_s=dur, exit_code=0, attempts=1,
                timed_out=False, fatal_error=None, no_result=no_result, scope_violation=bool(viol),
                scope_violations=viol, model_mismatch=False, model_mismatch_detail="", changed_files=sorted(work))
    wj(rd + "/meta.json", meta)
    final = None
    if no_result: final = None
    elif status == "DONE": final = "done"
    elif status == "BLOCKED": final = "blocked"
    if final is None and n >= last: final = "max_rounds"
    # skill_heartbeat == heartbeat znamená, že state.json naposledy zapsal skill, ne runner
    s.update(round=n, phase="between_rounds", heartbeat=ended, skill_heartbeat=ended, last_status=status or "NO_RESULT",
             last_summary=str((res or {}).get("summary") or ""), updated_at=ended)
    for k in ("current_round", "runner", "skill_model", "skill_round_started_at", "claim_until", "skill_checkpoints"):
        s.pop(k, None)
    paths = [task_dir, *work, *viol]
    if final:
        s.update(status=final, phase="ended", ended_at=ended)
        if t["folder"] == "active":
            git("mv", "-f", "--", t["rel"], "tasks/done/" + t["name"])
            paths += [t["rel"], "tasks/done/" + t["name"]]
    wj(task_dir + "/state.json", s)
    fnd = (res or {}).get("findings") or {}
    st = (status or "NO_RESULT") + ("+SCOPE(reverted %d)" % len(viol) if viol else "")
    subj = "%s r%02d [%s] model=%s effort=- runner=skill status=%s B/S/D=%s/%s/%s tok=?/? min=%s" % (
        tid, n, F["mode"], a.model, st, fnd.get("blocking", "-"), fnd.get("medium", "-"), fnd.get("minor", "-"),
        (dur or 0) // 60)
    h = commit(subj, str((res or {}).get("summary") or ""), paths)
    stp = stop_text()
    if stp and stp.startswith(MARK + tid):
        os.remove(p("STOP"))
    left = [x[1] for x in foreign_changes()]
    pushed = push() if a.push else None
    out(dict(ok=pushed is None or pushed["ok"], task=tid, round=n, status=st, final=final, commit=h, push=pushed, changed=sorted(work),
             scope_reverted=viol, no_result=no_result, requests=(res or {}).get("requests", []),
             next=(res or {}).get("next"), uncommitted_left=left))


def in_scope_work(F, task_dir):
    return [x[1] for x in changes() if in_scope(x[1], F, task_dir)
            and not x[1].startswith(task_dir + "/") and x[1] != "agent-loop/a1/data.js"
            and not re.match(r"^tasks/inbox/", x[1])]


def round_base(tid, n):
    r = git("log", "-1", "--format=%H", "--fixed-strings", "--grep", "%s r%02d claim " % (tid, n), allow_fail=True)
    return r.stdout.strip() or None


def cmd_checkpoint(a):
    """Průběžné uložení rozpracovaného kola: commit změn v rozsahu + task_dir, prodloužení claimu, push.
    Změny mimo rozsah necommituje (zůstanou pro finalize, který je vrátí)."""
    c = cfg()
    t = select(a.id)
    F = fields(t["task"], c)
    tid, task_dir = F["id"], "runs/" + F["id"]
    s = rj(task_dir + "/state.json") or {}
    if s.get("runner") != "skill" or s.get("phase") != "running":
        fail("úkol nemá rozběhnuté kolo skillu (state.json runner/phase)")
    n = int(s.get("current_round"))
    until = datetime.datetime.fromisoformat(now()) + datetime.timedelta(minutes=F["max_minutes"] + 30)
    s.update(heartbeat=now(), claim_until=until.isoformat(), updated_at=now())
    s["skill_checkpoints"] = int(s.get("skill_checkpoints") or 0) + 1
    wj(task_dir + "/state.json", s)
    work = in_scope_work(F, task_dir)
    outside = [x[1] for x in changes() if not in_scope(x[1], F, task_dir)]
    res = rj(round_dir(tid, n) + "/result.json") or {}
    h = commit("%s r%02d checkpoint %d [%s] runner=skill" % (tid, n, s["skill_checkpoints"], F["mode"]),
               str(res.get("summary") or ""), [task_dir, *work])
    pushed = push() if a.push else None
    out(dict(ok=pushed is None or pushed["ok"], task=tid, round=n, checkpoint=s["skill_checkpoints"], commit=h,
             push=pushed, committed=sorted(work), outside_scope_not_committed=outside, claim_until=until.isoformat()))


def cmd_abort(a):
    c = cfg()
    t = select(a.id)
    F = fields(t["task"], c)
    tid, task_dir = F["id"], "runs/" + F["id"]
    s = rj(task_dir + "/state.json") or {}
    if s.get("runner") != "skill":
        fail("úkol nemá rozběhnuté kolo skillu")
    n = int(s.get("current_round"))
    rd = round_dir(tid, n)
    ch = changes()
    for code, path in ch:
        if path.startswith(task_dir + "/") or re.match(r"^tasks/inbox/[^/]+\.json$", path):
            continue
        dst = rd + "/aborted/" + path
        if os.path.isfile(p(path)):
            os.makedirs(os.path.dirname(p(dst)), exist_ok=True)
            shutil.copy2(p(path), p(dst))
        if code == "??":
            os.remove(p(path))
        else:
            git("checkout", "-q", "HEAD", "--", path, allow_fail=True)
    git("checkout", "-q", "HEAD", "--", task_dir, allow_fail=True)
    s = rj(task_dir + "/state.json") or {}
    pushed = None
    if s.get("runner") == "skill":
        s["phase"] = "between_rounds"
        for k in ("current_round", "runner", "skill_model", "skill_round_started_at", "claim_until", "skill_checkpoints"):
            s.pop(k, None)
        s["updated_at"] = now()
        s["skill_heartbeat"] = s.get("heartbeat")
        wj(task_dir + "/state.json", s)
        commit("%s r%02d abort [skill]" % (tid, n), "", [task_dir + "/state.json"])
    keep = os.path.join(ROOT, ".git", "skill-aborted", tid + "-r%02d" % n)
    if os.path.isdir(p(rd)):
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        shutil.rmtree(keep, ignore_errors=True)
        shutil.move(p(rd), keep)
    for code, path in changes():
        if code == "??" and path.startswith(task_dir + "/"):
            os.remove(p(path))
    stp = stop_text()
    if stp and stp.startswith(MARK + tid):
        os.remove(p("STOP"))
    if a.push:
        pushed = push()
    out(dict(ok=True, task=tid, round=n, aborted=True, copies=keep, push=pushed, uncommitted_left=[x[1] for x in foreign_changes()]))


def cmd_new(a):
    c = cfg()
    raw = json.load(open(a.json, encoding="utf-8-sig"))
    F = fields(raw, c)
    errs = validate(F)
    for x in F["scope_allow"]:
        if re.match(r"^(agent-loop|tasks|runs|\.github|PAT)(/|$)", x.replace("\\", "/")):
            errs.append("scope_allow nesmí obsahovat %s" % x)
    if errs:
        fail("neplatný úkol: " + "; ".join(errs))
    if a.push:
        git("pull", "-q", "--rebase", "origin", git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip(), allow_fail=True)
    mx = 0
    for x in all_tasks():
        mx = max(mx, task_num(x["name"][:-5]), task_num(str(x["task"].get("id") or "")))
    tid = "TASK-%04d" % (mx + 1)
    order = ["id", "title", "mode", "goal", "done_when", "inputs", "scope_allow", "scope_deny", "max_rounds",
             "max_minutes", "priority", "notes", "created_at"]
    raw.update(id=tid, inputs=F["inputs"], scope_allow=F["scope_allow"], scope_deny=F["scope_deny"],
               max_rounds=F["max_rounds"], max_minutes=F["max_minutes"], priority=F["priority"], notes=F["notes"])
    raw.setdefault("created_at", now())
    obj = {k: raw[k] for k in order if k in raw}
    obj.update({k: v for k, v in raw.items() if k not in obj})
    rel = "tasks/inbox/%s.json" % tid
    wj(rel, obj)
    h = commit("task: %s %s" % (tid, F["title"]), "", [rel])
    pushed = push() if a.push else None
    out(dict(ok=True, task=tid, file=rel, commit=h, push=pushed, task_json=obj))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["new", "status", "prepare", "checkpoint", "finalize", "abort"])
    ap.add_argument("--json")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--latest", action="store_true", help="nejnovější úkol v tasks/inbox (nejvyšší číslo)")
    ap.add_argument("--takeover", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--id")
    ap.add_argument("--model", default="unknown")
    a = ap.parse_args()
    if not os.path.isdir(p(".git")):
        fail("spouštěj z kořene repozitáře (chybí .git)")
    if a.cmd in ("checkpoint", "finalize", "abort") and not a.id:
        fail("--id je povinné")
    if a.cmd == "new" and not a.json:
        fail("--json je povinné")
    dict(new=cmd_new, checkpoint=cmd_checkpoint, status=cmd_status, prepare=cmd_prepare, finalize=cmd_finalize, abort=cmd_abort)[a.cmd](a)


if __name__ == "__main__":
    main()
