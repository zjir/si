---
name: "agent-loop-create-task"
description: "Založí úkol pro agent loop repozitáře P.A.T. (github.com/zjir/si) z běžného chatu claude.ai: naklonuje repozitář s tokenem uživatele, doptá se na údaje úkolu, zapíše tasks/inbox/TASK-NNNN.json, commitne a pushne. Použij, když uživatel řekne „udělej task“, „nový task“, „založ úkol“, „nový úkol pro loop“."
---

# Založení úkolu agent loopu (chat)

Jediný zdroj pravidel je repozitář `zjir/si`; formát úkolu je v `agent-loop/README.md` (sekce Úkoly), zápis a validaci dělá `agent-loop/skill/round.py new`. Zpracování úkolu dělá skill `agent-loop-run`.

Prostředí: kontejner chatu (bash, git, python3, pdftotext), síť na github.com. Kontejner se mezi chaty maže; klon a token platí jen pro tento chat.

## 0. Klon (vždy nejdřív)

Když v tomto chatu už existuje `/home/claude/si` s remote s tokenem, jen ho aktualizuj (`git pull -q --rebase`) a přeskoč body 1–2.

1. Token: požádej uživatele o GitHub token (fine-grained, jen repozitář `zjir/si`, oprávnění Contents: Read and write). Bez tokenu lze jen číst, ne pushnout; v tom případě nepokračuj.
2. Klon (token nikdy nevypisuj, ani v popisu příkazu, ani v odpovědi; výstupy gitu filtruj přes `sed "s/$T/***/g"`):

   ```bash
   cd /home/claude && T='<token>' && git clone -q "https://x-access-token:$T@github.com/zjir/si.git" si 2>&1 | sed "s/$T/***/g"; cd si && git log -1 --oneline
   ```

3. Ověř `agent-loop/skill/round.py`, `agent-loop/config.json`, `tasks/`. Když chybí, řekni co a skonči.
4. Podklady: `PAT/` a `data/**` (kromě `.md`) jsou v `.gitignore`, na GitHubu nejsou. Pro založení úkolu nejsou potřeba. Soubory, které uživatel nahrál do chatu (`/mnt/user-data/uploads/`), zkopíruj do klonu na cestu, kterou uvádí úkol (např. `PAT/Popis OS P.A.T.pdf`). Necommituj je (gitignore to zajistí; ověř `git status --short`).

Všechny další příkazy běží v `/home/claude/si`. Git identitu bere `round.py` z posledního commitu; git config neměň.

## 1. Založení úkolu

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
5. Odpověď: id, hash, výsledek push. Úkol pak zpracuje lokální smyčka, nebo skill `agent-loop-run` (ve stejném chatu bez nového klonu).

