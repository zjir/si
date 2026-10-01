---
name: "agent-loop-run"
description: "Odehraje jedno kolo úkolu agent loopu repozitáře P.A.T. (github.com/zjir/si) v běžném chatu claude.ai místo lokálního runneru: vezme nejnovější úkol z tasks/inbox (nebo zadané id), odehraje kolo v roli agenta (recenzent spec / implementátor code) podle pravidel uložených v gitu, zkontroluje rozsah, zapíše runs/<id>/round-NN, commitne a pushne. Použij, když uživatel řekne „zpracuj task“, „pusť poslední task“, „udělej kolo“, „pusť TASK-0007“, „další kolo“."
---

# Jedno kolo agent loopu (chat)

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

Když v tomto chatu už existuje `/home/claude/si` s remote s tokenem, jen ho aktualizuj (`git pull -q --rebase`) a přeskoč body 1–2.

1. Token: nainstalovaná kopie skillu obsahuje vedle SKILL.md soubor `github_token` (fine-grained token jen pro `zjir/si`, Contents: Read and write). Načti ho:

   ```bash
   TF=$(find /mnt/skills -name github_token -path '*agent-loop*' 2>/dev/null | head -1); T=$(tr -d ' \r\n' < "$TF")
   ```

   Když soubor chybí (kopie v repozitáři ho nemá a mít nesmí, repozitář je veřejný) nebo push vrátí 401/403 (token vypršel), požádej uživatele o nový token a řekni mu, ať ho zapíše do `github_token` v nainstalovaném skillu.
2. Klon (token nikdy nevypisuj, ani v popisu příkazu, ani v odpovědi; výstupy gitu filtruj přes `sed "s/$T/***/g"`):

   ```bash
   cd /home/claude && git clone -q "https://x-access-token:$T@github.com/zjir/si.git" si 2>&1 | sed "s/$T/***/g"; cd si && git log -1 --oneline
   ```

3. Ověř `agent-loop/skill/round.py`, `agent-loop/config.json`, `tasks/`. Když chybí, řekni co a skonči.
4. Podklady: `PAT/` a `data/**` (kromě `.md`) jsou v `.gitignore`, na GitHubu nejsou. Soubory, které uživatel nahrál do chatu (`/mnt/user-data/uploads/`), zkopíruj do klonu na cestu, kterou uvádí úkol (např. `PAT/Popis OS P.A.T.pdf`). Necommituj je (gitignore to zajistí; ověř `git status --short`).

Všechny další příkazy běží v `/home/claude/si`. Git identitu bere `round.py` z posledního commitu; git config neměň.

## 1. Výběr

Výchozí je nejnovější úkol v inboxu: `python3 agent-loop/skill/round.py status --latest` (nejvyšší číslo `TASK-NNNN` v `tasks/inbox`). Když uživatel uvede id, nebo chce další kolo úkolu v `tasks/active`: `status --id TASK-NNNN`. Inbox prázdný a id nezadané = vypiš úkoly v `tasks/active` a zeptej se, který. Ukaž id, název, režim, kolo `next_round` / `last_round` a potvrď.

Před přípravou zkontroluj `inputs` úkolu: každá cesta, která v klonu neexistuje (typicky `PAT/...`), musí být nahraná v chatu. Chybí-li, zeptej se jednou: nahrát / pokračovat bez ní (agent ji pak zapíše do `requests`). Toto je poslední otázka před koncem kola.

## 2. Příprava

`python3 agent-loop/skill/round.py prepare --id <id z kroku 1> --model <id modelu, na kterém běžíš> --push`

Skript u úkolu z inboxu provede start (validace, přesun do active), založí `round-NN/` s `context.md`, zapíše do `state.json` claim (`runner: skill`, `claim_until` = teď + `max_minutes` + 30 min), commitne a pushne. Lokální runner úkol s platným claimem přeskakuje; po vypršení kolo obnoví jako přerušené. Při `ok: false` vypiš `error` a skonči. Volby: `--takeover` převezme kolo, které zůstalo rozběhnuté z jiného chatu; `--force` obejde kontrolu, že úkol právě zpracovává runner (souběh pak skončí konfliktem při push).

## 3. Kolo v roli agenta

Přečti celé soubory z `read_in_order` v uvedeném pořadí. Jsou to instrukce pro tebe na celé kolo a mají přednost před tímto skillem. Dále platí:

- Na nic se uživatele neptej a průběžně nic nehlas; rozhoduj sám.
- Nástroje podle `tools_allowed`: čtení a zápis souborů přes `bash_tool` (cat, sed -n, grep, head; zápis přes python nebo heredoc), `view`, `str_replace`, `create_file`. PDF čti po stranách (`pdftotext -layout -f N -l M "<soubor>" -`). V režimu `spec` nespouštěj jiné programy nad obsahem repozitáře. V režimu `code` smíš spouštět testy.
- Měň jen `scope_allow` (bez `scope_deny`) a `task_dir/`. Git nepoužívej.
- Zapisuj průběžně: `result.json` se `status: "CONTINUE"` hned na začátku, `state.md` po každém větším kroku. Kontext chatu je omezený: když ho zbývá málo, ukonči kolo řádně (`CONTINUE` a přesné `next`).
- Kolo končí platným `round_dir/result.json`.

## 4. Finalizace

`python3 agent-loop/skill/round.py finalize --id TASK-NNNN --model <stejné id> --push`

Skript vrátí změny mimo rozsah (kopie v `round-NN/discarded/`), zapíše `diff.patch`, `meta.json` (`runner: skill`, `skill_model`; tokeny, cena a effort `null`), zruší claim, při `DONE` / `BLOCKED` / posledním kole přesune úkol do `tasks/done`, commitne jen soubory úkolu a změny v rozsahu a pushne (fetch + rebase).

- `push.ok: false` s `patch_dir`: konflikt s commity runneru. Zkopíruj patch z `patch_dir` do `/mnt/user-data/outputs/`, předej ho přes `present_files` a napiš, které soubory kolidují. Nic nepřepisuj silou (`push --force` je zakázané).
- Kolo nejde dokončit: `python3 agent-loop/skill/round.py abort --id TASK-NNNN --push` (vrátí strom, uvolní claim, kopie práce v `.git/skill-aborted/`).

## 5. Odpověď

Stručně: id, kolo, `status`, `final`, hash a výsledek push, `summary` a `next` z `result.json`, `requests`, vrácené soubory mimo rozsah. Další kolo = znovu tento skill s `--id` (ve stejném chatu bez nového klonu). A1 se přegeneruje při startu lokální smyčky nebo `agent-loop\start-loop.cmd report`; kola skillu mají v A1 `COST_UNKNOWN` a `EFFORT_UNVERIFIED`.
