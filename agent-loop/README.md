# Agent loop (Windows)

Lokální smyčka, která bez dohledu zpracovává úkoly z `tasks/inbox/` pomocí `claude -p`. Zadání se drží v `zadani/`, role recenzenta je v `review-loop/review.md`. Výsledky každého kroku jdou do `runs/` a do gitu (jedna linie commitů, žádné větve). Historii zobrazuje aplikace **A1** (`a1/index.html`).

Specifikace: `zadani/agent_loop.md` (včetně dodatků v sekci 15, které implementace již respektuje).

## Požadavky

- Windows 10/11 s Windows PowerShell 5.1 (je součástí systému) nebo PowerShell 7.
- Git for Windows, přihlášený ke GitHubu (Git Credential Manager), aby fungoval `git push` bez dotazu.
- Claude Code CLI (`claude`) přihlášené předplatným. Každé kolo používá model **Fable 5.1** s effortem **max** (`config.json`).

## První spuštění

```bat
cd C:\...\09-2026
git push -u origin master
agent-loop\start-loop.cmd selftest
```

`selftest` vypíše cestu a verzi CLI, zda CLI zná `--effort` a `--bare`, a jedním krátkým voláním ověří, jaký model skutečně běží.

- Pokud `selftest` hlásí jiný model než Fable, uprav v `config.json` hodnotu `model` na id, které CLI přijímá (`claude --model ...`). Alias `fable` je předpoklad, neověřený.
- Pokud CLI nezná `--effort`, effort se požaduje jen proměnnou prostředí `CLAUDE_CODE_EFFORT_LEVEL` a A1 hlásí `EFFORT_UNVERIFIED`.

## Spuštění

```bat
agent-loop\start-loop.cmd            &rem smyčka: čeká na úkoly, zpracuje je, čeká dál
agent-loop\start-loop.cmd once       &rem zpracuje jeden úkol a skončí
agent-loop\start-loop.cmd stop       &rem vytvoří STOP: smyčka skončí před dalším kolem
agent-loop\start-loop.cmd resume     &rem smaže STOP
agent-loop\start-loop.cmd report     &rem přegeneruje a1\data.js
```

Běh bez dohledu: Plánovač úloh Windows, akce `agent-loop\start-loop.cmd`, spouštěč „Při přihlášení“. Zámek `.loop.lock` brání dvěma běhům současně; zámek mrtvého procesu se převezme a osiřelý proces agenta se ukončí.

## Úkoly

Zadání úkolu (hlavní cesta): GitHub → Actions → **new-task** → Run workflow. Akce ověří vstupy, přidělí id `TASK-NNNN` a commitne `tasks/inbox/TASK-NNNN.json`. Smyčka ho při dalším `git pull` najde.

Další cesty:

- lokálně: `agent-loop\start-loop.cmd new -Title "..." -Goal "..." -DoneWhen "..." -Scope zadani\komponenta-sr.md -Inputs "PAT/Popis OS P.A.T.pdf" -MaxRounds 5`,
- záložní formulář `a1/new-task.html` (sestaví JSON, nabídne stažení nebo založení souboru na GitHubu),
- ruční vložení JSON souboru do `tasks/inbox/` (runner ho sám commitne a přečísluje).

Restart: Actions → **restart-task** (`task_id`, `from_scratch`), nebo `start-loop.cmd restart -Id TASK-0003 [-FromScratch]`. Bez `from_scratch` úkol naváže dalším kolem a dostane nových N kol; s ním se staré kroky přesunou do `runs/<id>/archive-<čas>/` a začne se od kola 1.

Formát úkolu:

| Pole | Povinné | Popis |
|---|---|---|
| `id` | ano | `TASK-0007`; jiné tvary runner přečísluje |
| `title` | ano | jedna věta |
| `mode` | ano | `spec` (recenzent zadání) nebo `code` (implementace) |
| `goal`, `done_when` | ano | cíl a ověřitelná podmínka dokončení, pro agenta |
| `scope_allow` | ano | cesty/globy (`zadani/**`, `src/*.py`), které smí agent měnit |
| `scope_deny` | ne | zakázané cesty, mají přednost |
| `inputs` | ne | cesty ke čtení |
| `max_rounds` | ne | N, strop kol (výchozí 5) |
| `max_minutes` | ne | strop jednoho kola (výchozí 60) |
| `priority` | ne | nižší dřív (výchozí 100) |
| `notes` | ne | poznámky pro agenta |

`model` a `effort` v úkolu se ignorují; platí `config.json`.

## Jak běží jeden úkol

1. Úkol se přesune z `inbox` do `active`, commit `TASK-0007 start`.
2. Každé kolo je nový proces `claude -p` (nezávislý agent bez paměti). Prompt = `prompts/common.md` + role (`review-loop/review.md` nebo `prompts/code.md`) + kontext kola (`runs/<id>/round-NN/context.md`, jen odkazy na soubory).
3. Agent zapíše změny v rozsahu, `runs/<id>/state.md` a `runs/<id>/round-NN/result.json`. Na nic se neptá, rozhoduje sám; chybějící prostředky zapíše do `requests`.
4. Runner zkontroluje rozsah: změna mimo rozsah = celé kolo se zahodí (kopie v `round-NN/discarded/`) a pokračuje se dalším kolem.
5. Uloží `meta.json` (model, effort, tokeny, cena, doba, exit), `diff.patch`, `output.md`, přegeneruje `a1/data.js`, commitne `TASK-0007 r03 [...]` a pushne.
6. Konec: agent vrátí `DONE` (sám rozhodl, že není co dodat), `BLOCKED`, nebo je vyčerpáno N kol (`max_rounds`). Opakované selhání CLI (např. vyčerpaný limit) po `retries` pokusech s pauzou `retry_sleep_seconds` = `failed`. Úkol se přesune do `done`.

Smyčka nezačne kolo, když má pracovní strom necommitnuté změny (kromě nových souborů v `tasks/inbox/`); počká, až je commitneš nebo vrátíš.

## A1

Otevři `agent-loop/a1/index.html` (funguje z disku i z GitHub Pages). Seznam úkolů se stavem, spotřebou a varováními; klik na úkol ukáže zadání, stav, odkazy na commity a kroky. Kroky jsou sbalené a rozbalují se po jednom (shrnutí, další krok, požadavky, změněné soubory, metadata, poznámky, výstup, diff). Data se obnovují každé 2 minuty nebo tlačítkem.

Varování: `MODEL_MISMATCH`, `EFFORT_UNVERIFIED`, `SCOPE_VIOLATION`, `NO_RESULT`, `TIMEOUT`, `STUCK`, `NO_CHANGE`, `COST_UNKNOWN`, `MAX_ROUNDS`, `FAILED`, `BLOCKED`, `INVALID`, `PUSH_FAILED`, `REQUESTS`.

## Živý průběh

CLI běží v režimu `stream-json`; runner průběžně zapisuje čitelný průběh kola do `runs/<id>/round-NN/live.log` (čtení souborů, hledání, zápisy, poznámky agenta, chyby nástrojů) a každých `heartbeat_seconds` přegeneruje A1. V A1 je běžící kolo automaticky rozbalené s oddílem „Průběh (živě)“ a stránka se při běžícím úkolu obnovuje každých 30 s.

## Konfigurace (`config.json`)

| Klíč | Výchozí | Popis |
|---|---|---|
| `model`, `model_expect` | `fable` | id modelu pro `--model`; podřetězec, který musí obsahovat skutečný model |
| `effort` | `max` | `--effort` |
| `claude_command` | `claude` | příkaz nebo plná cesta k CLI |
| `use_bare` | `false` | `--bare` (bez CLAUDE.md, skillů, MCP); vypnuto, protože není ověřeno, že v tomto režimu funguje přihlášení předplatným |
| `extra_args` | `[]` | další argumenty pro CLI |
| `poll_seconds` | 300 | čekání na nové úkoly |
| `retries`, `retry_sleep_seconds` | 3, 3600 | opakování při selhání CLI |
| `default_max_rounds`, `default_max_minutes` | 5, 60 | výchozí N a strop kola |
| `push`, `remote`, `repo_url` | `true`, `origin` | push po každém kole; odkazy v A1 |
| `prompts`, `tools` | | prompty a povolené nástroje podle režimu |

## Otevřené body

- Přesné id modelu Fable 5.1 pro CLI a podpora `--effort` / `--bare` ve verzi CLI: ověří `selftest`.
- Jména polí JSON výstupu CLI (`usage`, `total_cost_usd`, `modelUsage`) jsou předpoklad; chybějí-li, A1 hlásí `COST_UNKNOWN`, ne nulu.
- `workflow_dispatch` má 9 vstupů; limit GitHubu (10 nebo více) tím není překročen.
