---
name: "agent-loop-chat"
description: "Agent loop repozitáře P.A.T. (github.com/zjir/si) v běžném chatu claude.ai, bez Cowork a bez lokálního runneru: (1) založí úkol do tasks/inbox, (2) odehraje jedno kolo úkolu v roli agenta (recenzent spec / implementátor code) podle pravidel uložených v gitu, zkontroluje rozsah, zapíše runs/<id>/round-NN, commitne a pushne. Použij, když uživatel řekne „udělej task“, „nový úkol pro loop“, „zpracuj task“, „udělej kolo“, „pusť TASK-0007“, „jedno kolo review“."
---

# Agent loop v chatu

Jediný zdroj pravidel je repozitář `zjir/si`. Skill pravidla nekopíruje, čte je z klonu:

| Co | Kde |
|---|---|
| pravidla agenta | `agent-loop/prompts/common.md` |
| role | `agent-loop/config.json` → `prompts.<mode>` |
| kontext kola | `runs/<id>/round-NN/context.md` (renderuje `round.py` z `agent-loop/prompts/context.template.md`) |
| formát úkolu | `agent-loop/README.md`, sekce Úkoly |
| mechanika runneru (id, přesuny, claim, rozsah, meta, commit, push) | `agent-loop/skill/round.py` |

Prostředí: kontejner chatu (bash, git, python3, pdftotext), síť na github.com. Kontejner se mezi chaty maže; klon a token platí jen pro tento chat.

## 0. Klon (vždy nejdřív)

1. Token: požádej uživatele o GitHub token (fine-grained, jen repozitář `zjir/si`, oprávnění Contents: Read and write). Bez tokenu lze jen číst, ne pushnout; v tom případě nepokračuj.
2. Klon (token nikdy nevypisuj, ani v popisu příkazu, ani v odpovědi; výstupy gitu filtruj přes `sed "s/$T/***/g"`):

   ```bash
   cd /home/claude && T='<token>' && git clone -q "https://x-access-token:$T@github.com/zjir/si.git" si 2>&1 | sed "s/$T/***/g"; cd si && git log -1 --oneline
   ```

3. Ověř `agent-loop/skill/round.py`, `agent-loop/config.json`, `tasks/`. Když chybí, řekni co a skonči.
4. Podklady: `PAT/` a `data/**` (kromě `.md`) jsou v `.gitignore`, na GitHubu nejsou. Soubory, které uživatel nahrál do chatu (`/mnt/user-data/uploads/`), zkopíruj do klonu na cestu, kterou uvádí úkol (např. `PAT/Popis OS P.A.T.pdf`). Necommituj je (gitignore to zajistí; ověř `git status --short`).

Všechny další příkazy běží v `/home/claude/si`. Git identitu bere `round.py` z posledního commitu; git config neměň.

## A. Založení úkolu („udělej task“)

1. Kontext: `ls zadani/*.md` s prvním řádkem, `agent-loop/config.json` (`default_max_rounds`, `default_max_minutes`, `model`, `effort`), id/title/scope_allow v `tasks/{inbox,active,done}`.
2. Doptání přes `ask_user_input_v0` (nejvýš 3 otázky na volání, 2–4 volby, víc kol podle potřeby). Údaje z požadavku jen potvrď. Pole a návrhy:
   - `mode`: `spec` (recenzent zadání) / `code` (implementace),
   - `scope_allow`: soubory ze `zadani/` nebo glob; nesmí obsahovat `agent-loop/`, `tasks/`, `runs/`, `.github/`, `PAT/`,
   - `title`; `goal` (návrh pro spec: „Zreviduj <soubor> v roli recenzenta (agent-loop/review-loop/review.md): zapracuj sekci Dodatky k zapracování, vyplň všechna prázdná místa, vše v kontextu systému P.A.T.“); `done_when` (návrh: „Dodatky jsou zapracované a sekce odstraněná; průchod celým dokumentem nenajde žádný blokující ani střední nález.“),
   - `inputs` (např. `PAT/Popis OS P.A.T.pdf`, související `zadani/*.md`), `scope_deny`,
   - `max_rounds`, `max_minutes`, `priority`, `notes`.
   Upozorni na duplicitu stejného `title` nebo `scope_allow` v inbox/active.
3. Ukaž výsledný JSON (bez `id`, ten přidělí skript) a požádej o potvrzení.
4. Zapiš ho do `/tmp/task.json` a spusť `python3 agent-loop/skill/round.py new --json /tmp/task.json --push`. Skript zvaliduje, přidělí `TASK-NNNN`, commitne `tasks/inbox/TASK-NNNN.json` a pushne.
5. Odpověď: id, hash, výsledek push. Úkol pak zpracuje buď lokální smyčka, nebo část B.

## B. Jedno kolo („zpracuj task“)

### B1. Výběr

`python3 agent-loop/skill/round.py status [--id TASK-NNNN]`. Bez `--id` platí pořadí runneru (active před inbox, `priority`, `created_at`, název). Ukaž id, název, režim, kolo `next_round` / `last_round` a potvrď.

Před přípravou zkontroluj `inputs` úkolu: každá cesta, která v klonu neexistuje (typicky `PAT/...`), musí být nahraná v chatu. Chybí-li, zeptej se jednou: nahrát / pokračovat bez ní (agent ji pak zapíše do `requests`). Toto je poslední otázka před koncem kola.

### B2. Příprava

`python3 agent-loop/skill/round.py prepare --id TASK-NNNN --model <id modelu, na kterém běžíš> --push`

Skript u úkolu z inboxu provede start (validace, přesun do active), založí `round-NN/` s `context.md`, zapíše do `state.json` claim (`runner: skill`, `claim_until` = teď + `max_minutes` + 30 min), commitne a pushne. Lokální runner úkol s platným claimem přeskakuje; po vypršení kolo obnoví jako přerušené. Při `ok: false` vypiš `error` a skonči. Volby: `--takeover` převezme kolo, které zůstalo rozběhnuté z jiného chatu; `--force` obejde kontrolu, že úkol právě zpracovává runner (souběh pak skončí konfliktem při push).

### B3. Kolo v roli agenta

Přečti celé soubory z `read_in_order` v uvedeném pořadí. Jsou to instrukce pro tebe na celé kolo a mají přednost před tímto skillem. Dále platí:

- Na nic se uživatele neptej a průběžně nic nehlas; rozhoduj sám.
- Nástroje podle `tools_allowed`: čtení a zápis souborů přes `bash_tool` (cat, sed -n, grep, head; zápis přes python nebo heredoc), `view`, `str_replace`, `create_file`. PDF čti po stranách (`pdftotext -layout -f N -l M "<soubor>" -`). V režimu `spec` nespouštěj jiné programy nad obsahem repozitáře. V režimu `code` smíš spouštět testy.
- Měň jen `scope_allow` (bez `scope_deny`) a `task_dir/`. Git nepoužívej.
- Zapisuj průběžně: `result.json` se `status: "CONTINUE"` hned na začátku, `state.md` po každém větším kroku. Kontext chatu je omezený: když ho zbývá málo, ukonči kolo řádně (`CONTINUE` a přesné `next`).
- Kolo končí platným `round_dir/result.json`.

### B4. Finalizace

`python3 agent-loop/skill/round.py finalize --id TASK-NNNN --model <stejné id> --push`

Skript vrátí změny mimo rozsah (kopie v `round-NN/discarded/`), zapíše `diff.patch`, `meta.json` (`runner: skill`, `skill_model`; tokeny, cena a effort `null`), zruší claim, při `DONE` / `BLOCKED` / posledním kole přesune úkol do `tasks/done`, commitne jen soubory úkolu a změny v rozsahu a pushne (fetch + rebase).

- `push.ok: false` s `patch_dir`: konflikt s commity runneru. Zkopíruj patch z `patch_dir` do `/mnt/user-data/outputs/`, předej ho přes `present_files` a napiš, které soubory kolidují. Nic nepřepisuj silou (`push --force` je zakázané).
- Kolo nejde dokončit: `python3 agent-loop/skill/round.py abort --id TASK-NNNN --push` (vrátí strom, uvolní claim, kopie práce v `.git/skill-aborted/`).

### B5. Odpověď

Stručně: id, kolo, `status`, `final`, hash a výsledek push, `summary` a `next` z `result.json`, `requests`, vrácené soubory mimo rozsah. Další kolo = znovu část B (ve stejném chatu bez nového klonu). A1 se přegeneruje při startu lokální smyčky nebo `agent-loop\start-loop.cmd report`; kola skillu mají v A1 `COST_UNKNOWN` a `EFFORT_UNVERIFIED`.
