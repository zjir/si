# Zadání: Agent Loop (lokální smyčka agentů řízená přes git)

Verze 0.1 · návrh před implementací · dokument je psaný pro AI implementátora, ne pro čtení člověkem

## 1. Účel

Lokální smyčka, která bez dohledu zpracovává úkoly zadané zvenčí přes git. Jeden úkol = jedna větev = série kol jednoho agenta. Výstupy jdou do souborů a do gitu; člověk je čte přes statickou HTML stránku, která shrnuje stav úkolu, použitý model, spotřebu a výstupy jednotlivých kol.

Dva režimy agenta nad stejnou smyčkou:

- **spec** — píše a recenzuje zadání pro AI implementátora,
- **code** — implementuje a opravuje kód proti testům.

Smyčka, git, dashboard a formulář jsou pro oba režimy shodné. Liší se jen prompt, povolené cesty a podmínka ukončení.

## 2. Principy

1. **Bez serveru.** Vše je statické: soubory v repozitáři, HTML stránka otevřená z disku nebo z GitHub Pages. Žádný běžící backend, žádná databáze.
2. **Git je sběrnice.** Zadání úkolu, postup i výsledky jsou commity. Zadávat i číst jde z mobilu přes webové rozhraní gitu.
3. **Výstupy agentů jsou pro agenty.** Agent nezestručňuje pro člověka, nepíše souvislé odstavce a nevysvětluje. Píše strukturovaný stav, který příští kolo přečte a použije. Pro člověka existuje jen jeden řádek verdiktu a dashboard.
4. **Úspora tokenů je součást návrhu.** Agent dostává ukazatele na soubory, ne jejich obsah. Historii kol nečte celou, čte `state.md` a diff posledního kola.
5. **Každý běh je auditovatelný.** Model, effort, doba, spotřeba, exit kód a odkaz na commit se ukládají strojově.
6. **Restart je normální stav.** Zaseknutý úkol lze spustit znovu bez ručního úklidu.

## 3. Struktura repozitáře

```
tasks/
  inbox/            TASK-0007.json        zadané, ještě nezpracované
  active/           TASK-0007.json        právě zpracovávané (přesune runner)
  done/             TASK-0007.json        ukončené (hotovo i zablokované)
runs/
  TASK-0007/
    state.md                              aktuální stav úkolu pro příští kolo (přepisuje se)
    state.json                            strojový stav (kolo, fáze, heartbeat)
    round-01/
      meta.json                           model, effort, časy, spotřeba, exit kód
      result.json                         verdikt kola (schéma 6.3)
      stdout.log                          surový výstup běhu
      notes.md                            volitelné poznámky agenta pro příští kolo
    round-02/…
prompts/
  common.md                               pravidla společná oběma režimům
  spec_agent.md                           režim spec
  code_agent.md                           režim code
loop/
  runner.sh                               smyčka: vezmi úkol, běž kola, commituj
  task.py                                 práce s task soubory a stavem
  report.py                               generuje dashboard/data.js
dashboard/
  index.html                              dashboard (statický)
  new-task.html                           formulář pro zadání úkolu
  data.js                                 window.LOOP_DATA = {...}, generuje report.py
workspace/                                obsah, na kterém agent pracuje (spec/, src/, tests/…)
STOP                                      existuje-li, runner nezačne nové kolo
.loop.lock                                zámek běhu
```

## 4. Úkol

### 4.1 Formát `tasks/inbox/TASK-NNNN.json`

| Pole | Typ | Povinné | Popis |
|---|---|---|---|
| `id` | string | ano | `TASK-0007`, shodné s názvem souboru |
| `title` | string | ano | jedna věta |
| `mode` | `spec` \| `code` | ano | který prompt se použije |
| `goal` | string | ano | co má být hotovo; píše se pro agenta, ne pro člověka |
| `done_when` | string | ano | ověřitelná podmínka dokončení |
| `inputs` | string[] | ne | cesty, které má agent přečíst |
| `scope_allow` | string[] | ano | cesty, které smí měnit (glob) |
| `scope_deny` | string[] | ne | cesty, které měnit nesmí (má přednost) |
| `model` | string | ano | např. `opus`, `sonnet` |
| `effort` | `low` \| `medium` \| `high` \| `xhigh` \| `max` | ano | předává se přes `--effort` |
| `max_rounds` | int | ano | strop kol (výchozí 5) |
| `max_minutes` | int | ano | strop na jedno kolo (výchozí 30) |
| `max_tokens_total` | int | ne | rozpočet spotřeby; při překročení se úkol zablokuje |
| `priority` | int | ne | nižší číslo dřív (výchozí 100) |
| `restart` | bool | ne | vynutí běh od kola 1 a smaže `state.json` |
| `created_at` | ISO8601 | ano | vyplní formulář |
| `notes` | string | ne | volný text pro agenta |

### 4.2 Životní cyklus

1. Soubor se objeví v `tasks/inbox/` (vytvoří ho GitHub Action z formuláře, viz 11).
2. Runner ho přesune do `tasks/active/`, založí větev `task/TASK-0007` z `main` a commitne přesun.
3. Běží kola, po každém commit do větve.
4. Konec: soubor do `tasks/done/`, do `state.json` se zapíše `status` (`done`, `blocked`, `budget`, `stopped`), větev se **nemerguje automaticky**; sloučení je rozhodnutí člověka.
5. Restart: člověk vrátí soubor do `inbox/` s `restart: true`, nebo jen změní `status` na `queued`; runner naváže na poslední kolo, při `restart: true` začne od začátku.

### 4.3 Stavy

`queued` → `running` → `done` | `blocked` | `budget` | `stopped` | `failed`

- `blocked`: agent potřebuje rozhodnutí, které nemá v zadání. Napíše ho do `result.json` (`needs_decision`).
- `budget`: vyčerpán `max_rounds` nebo `max_tokens_total`.
- `stopped`: existoval soubor `STOP`.
- `failed`: běh skončil nenulovým kódem po vyčerpání pokusů (typicky týdenní limit).

## 5. Smyčka (`loop/runner.sh`)

1. Zámek `.loop.lock`; existuje-li a je živý, konec.
2. `git pull --rebase`.
3. Vyber úkol: `tasks/active/` má přednost před `tasks/inbox/`; v rámci složky podle `priority`, pak podle `created_at`.
4. Není-li úkol, spi `POLL_SECONDS` (výchozí 300) a opakuj. Čekání nic nestojí, agent neběží.
5. Připrav větev `task/<id>`, existuje-li, přepni se na ni.
6. Pro každé kolo:
   a. zapiš heartbeat do `state.json`,
   b. spusť agenta (6.1) s timeoutem `max_minutes`,
   c. ulož `meta.json`, `stdout.log`, `result.json`,
   d. zkontroluj rozsah změn (6.4), při porušení kolo zahoď (`git checkout -- .`) a zapiš porušení,
   e. přegeneruj `dashboard/data.js`,
   f. commit se strukturovanou zprávou (5.1), push.
7. Ukončení kola podle režimu (7.3, 8.3), jinak další kolo.
8. Po ukončení úkolu přesuň task soubor do `done/`, commit, push, uvolni zámek.

### 5.1 Formát commit zprávy

```
TASK-0007 r03 [code] model=claude-opus-... effort=high verdict=GAPS tok=12.4k/3.1k min=7
```

Jeden řádek, strojově parsovatelný; tělo commitu obsahuje `summary` z `result.json`.

## 6. Běh agenta

### 6.1 Volání

```
claude -p "$(cat prompts/common.md prompts/<mode>_agent.md task_context.md)" \
  --bare \
  --model "<model>" \
  --effort "<effort>" \
  --allowedTools "<dle režimu>" \
  --permission-mode acceptEdits \
  --output-format json
```

`task_context.md` sestaví runner: identifikace úkolu, číslo kola, cesty `inputs`, `scope_allow`, `scope_deny`, `done_when`, a **jen odkazy na** `state.md` a na diff posledního kola, ne jejich obsah.

### 6.2 `meta.json`

| Pole | Zdroj |
|---|---|
| `requested_model`, `requested_effort` | task |
| `actual_model` | z JSON výstupu CLI |
| `effort_verified` | `false`, dokud CLI effort nevrací; hodnota se bere z požadavku |
| `input_tokens`, `output_tokens`, `cache_read_tokens` | z JSON výstupu, pokud jsou |
| `cost_usd` | z JSON výstupu, pokud je; jinak `null` |
| `started_at`, `ended_at`, `duration_s`, `exit_code` | runner |
| `rounds_so_far`, `restarted_from` | runner |

Přesná jména polí ve výstupu CLI se ověří jedním pokusným během a zapíší do `loop/README.md`. Dokud ověřena nejsou, `report.py` je hlásí jako neznámá, ne nulová.

### 6.3 `result.json` (zapisuje agent)

```json
{
  "task": "TASK-0007",
  "round": 3,
  "status": "CONTINUE",
  "summary": "jedna věta pro člověka",
  "findings": {"blocking": 1, "medium": 4, "minor": 2},
  "changed": ["spec/trend.md"],
  "next": "co má udělat příští kolo",
  "needs_decision": null
}
```

`status`: `DONE` (splněno `done_when`), `CONTINUE`, `BLOCKED`. Chybí-li soubor, runner to bere jako `failed` kolo.

### 6.4 Kontrola rozsahu

Po každém kole runner porovná `git status` se `scope_allow` a `scope_deny`. Změna mimo rozsah znamená zahození kola a zápis do `result.json` runnerem (`status: BLOCKED`, důvod `scope_violation`). Tím je vynucena dělba rolí: implementátor nesmí měnit testy, recenzent nesmí měnit kód.

### 6.5 Povolené nástroje

- **spec:** `Read,Edit,Write,Glob,Grep`
- **code:** `Read,Edit,Write,Glob,Grep,Bash`

Git obsluhuje runner, ne agent. Síť agent nemá.

## 7. Režim `spec`

### 7.1 Co agent dělá

Doplňuje a recenzuje zadání určené pro AI implementátora.

### 7.2 Pravidla promptu (`prompts/spec_agent.md`)

- Dokument čte a implementuje AI. **Vyplň všechna prázdná místa.** Každá věc, na kterou by se implementátor nebo tester musel zeptat, je chyba dokumentu.
- **Nezestručňuj.** Délka není omezena, obsah se nesmí ořezávat kvůli čitelnosti pro člověka.
- Otázky se nenechávají na člověku: každou uzavři konkrétním rozhodnutím a zapiš ho do rozhodovacího logu. Nejde-li rozhodnout, urči výchozí chování a označ je jako předpoklad s kontrolou při implementaci.
- Grilování ve dvou rolích (AI implementátor, AI tester) v opakovaných průchodech, dokud průchod nenajde nové prázdné místo.
- Závažnosti: blokující, střední (prázdné místo), drobný.
- Rozhodovací log je závazný, uzavřená rozhodnutí se znovu neotevírají bez nového argumentu.
- Fakta se zdrojem, jinak označit „neověřeno“ a dát náhradní postup.

### 7.3 Ukončení

`DONE`, když průchod nenajde blokující ani střední nález, nebo když je splněno `done_when` úkolu. Jinak `CONTINUE` do vyčerpání `max_rounds`.

## 8. Režim `code`

### 8.1 Co agent dělá

Implementuje proti testům, dokud nejsou zelené, nebo opravuje konkrétní chybu.

### 8.2 Pravidla promptu (`prompts/code_agent.md`)

- Nejdřív spusť testy a teprve pak měň kód. Výstup testů je jediné kritérium hotovo.
- Měň jen `scope_allow`. **Test se neopravuje, aby prošel.** Když je test podle tebe špatný, zapiš spor do `result.json` (`needs_decision`) a skonči s `BLOCKED`.
- Do `state.md` zapiš, co jsi zkusil a co nefungovalo, aby to příští kolo neopakovalo.
- Žádné TODO ani zástupné implementace; nejde-li něco dokončit, `BLOCKED` s důvodem.
- Do logu kola dávej jen jména padajících testů a krátký výpis, ne celé logy.

### 8.3 Ukončení

`DONE`, když jsou testy zelené a `done_when` splněno. `BLOCKED` při sporu o test nebo chybějící definici v zadání.

## 9. Úspora tokenů

1. `--bare`: žádné CLAUDE.md, skilly, MCP ani paměti.
2. Kontext kola: `task_context.md` (krátký) + `state.md` (strop 150 řádků, přepisuje se) + diff posledního kola. Starší kola se nečtou.
3. Agent čte soubory cíleně (Grep, rozsah řádků), ne celé, pokud to úkol nevyžaduje.
4. Výstup agenta do chatu je jen `result.json`; vše ostatní jde do souborů.
5. Zákaz opakování: agent nepřepisuje do odpovědi to, co už je v souboru.
6. Runner nikdy nevkládá obsah souborů do promptu, jen cesty.
7. `state.md` je append-only jen logicky: agent ho **přepisuje** do aktuálního stavu, neroste donekonečna.

## 10. Dashboard (`dashboard/index.html`)

Statická stránka bez serveru. Data čte z `dashboard/data.js` (`window.LOOP_DATA`), který generuje `report.py` po každém kole. Funguje z `file://` i z GitHub Pages, responzivní pro mobil.

### 10.1 Přehled úkolů

Tabulka: id, title, mode, status, větev, počet kol, poslední model, souhrn spotřeby, doba, poslední verdikt, varování.

### 10.2 Detail úkolu

- Zadání (pole z task souboru).
- Časová osa kol: kolo, model, effort, doba, tokeny, cena, verdikt, počty nálezů, odkaz na commit a na diff.
- `summary` a `next` z každého kola.
- Odkaz na `stdout.log` a na `state.md`.
- Tlačítko „znovu spustit“ = vygeneruje patch pro `restart: true` a nabídne ho ke zkopírování nebo jako odkaz do gitu (viz 11.2).

### 10.3 Varování (červeně, s důvodem)

| Kód | Podmínka |
|---|---|
| `MODEL_MISMATCH` | `actual_model` neodpovídá `requested_model` |
| `EFFORT_UNVERIFIED` | `effort_verified = false` |
| `SCOPE_VIOLATION` | kolo zahozeno kvůli změně mimo rozsah |
| `NO_RESULT` | kolo neodevzdalo `result.json` |
| `STUCK` | heartbeat starší než `max_minutes` |
| `BUDGET` | překročen `max_rounds` nebo `max_tokens_total` |
| `NO_CHANGE` | dvě kola po sobě bez změny v repozitáři |
| `COST_UNKNOWN` | chybí údaje o spotřebě |

Varování se počítají v `report.py`, ne v prohlížeči, aby šla použít i ve skriptech.

## 11. Zadávání úkolů

Hlavní cesta je **GitHub Action s formulářem** (`workflow_dispatch`). Formulář vykreslí GitHub, akce z něj vytvoří soubor úkolu a commitne ho do `main`. Smyčka jen sleduje, zda v `tasks/inbox/` přibyl soubor. Statický `dashboard/new-task.html` zůstává jako záloha, když akce selže nebo je repozitář offline.

### 11.1 Workflow `.github/workflows/new-task.yml`

- Spouštění: `workflow_dispatch` s poli formuláře. Práva: `permissions: contents: write`, autentizace vestavěným `GITHUB_TOKEN`, žádný osobní token.
- Kroky: checkout → validace vstupů → přidělení id → zápis `tasks/inbox/TASK-NNNN.json` → commit a push na `main` (s `pull --rebase` a opakováním při souběhu).
- **Přidělení id dělá akce**, ne formulář: má repozitář k dispozici, takže vezme nejvyšší existující číslo napříč `inbox`, `active` i `done` a přidá jedna. Runnerovo přečíslování (4.2) zůstává jen jako pojistka.
- **Validace v akci:** `mode` ∈ {spec, code}, `effort` ∈ {low, medium, high, xhigh, max}, čísla jsou čísla, `scope_allow` není prázdné, `done_when` není prázdné. Neplatný vstup = akce selže a soubor nevznikne, takže se vadné zadání k agentovi nedostane.
- Commit zpráva: `task: TASK-0007 <title>`.

### 11.2 Pole formuláře

`workflow_dispatch` má strop na počet vstupů (u GitHubu 10; ověřit), proto jsou pole složená:

| Vstup | Typ | Výchozí |
|---|---|---|
| `title` | string | — |
| `mode` | choice: spec, code | spec |
| `goal` | string (víceřádkový) | — |
| `done_when` | string | — |
| `scope_allow` | string, cesty oddělené čárkou | — |
| `model` | choice | opus |
| `effort` | choice | high |
| `max_rounds` | string (číslo) | 5 |
| `budget` | string, `minuty/tokeny`, např. `30/400000` | 30/ |
| `advanced` | string, JSON s dalšími poli (`inputs`, `scope_deny`, `priority`, `notes`, `restart`) | `{}` |

Akce rozloží `scope_allow`, `budget` a `advanced` do plného formátu úkolu ze 4.1.

### 11.3 Workflow `.github/workflows/restart-task.yml`

Druhý formulář pro restart bez psaní souboru: vstupy `task_id` a `from_scratch` (bool). Akce najde task soubor v `active` nebo `done`, nastaví `status: queued`, případně `restart: true`, přesune ho zpět do `tasks/inbox/` a commitne. Tím je restart dostupný i z mobilu.

### 11.4 Jak to smyčka vidí

- Runner v každém cyklu udělá `git pull --rebase` a hledá soubory v `tasks/inbox/`. Nový soubor = nový úkol, žádná jiná signalizace není potřeba.
- Soubor, který přibude během běhu jiného úkolu, se prostě zpracuje v dalším cyklu; fronta je pořadí podle `priority` a `created_at`.
- Runner pracuje ve větvích `task/*`, akce commituje jen do `main`, takže si nelezou do cesty. Při konfliktu na `main` runner netlačí silou a úkol označí jako `blocked`.
- Po převzetí úkolu runner přesune soubor do `tasks/active/`; opakované spuštění akce se stejným `task_id` ho vrátí do `inbox` jen přes restart workflow, ne omylem.

### 11.5 Záložní statický formulář

`dashboard/new-task.html` sestaví tentýž JSON a nabídne zkopírování do schránky, stažení souboru nebo odkaz na založení souboru ve webovém rozhraní. Id navrhne jako `TASK-<timestamp>`, runner ho přečísluje.

## 12. Ochrany

- `STOP` soubor zastaví smyčku před dalším kolem.
- Zámek `.loop.lock` s PID a časem; mrtvý zámek starší než `max_minutes × 2` se uvolní.
- Timeout kola, po něm `STUCK` a `status: blocked`.
- Při nenulovém exit kódu běhu: čekání `RETRY_SLEEP` (výchozí 3600 s) a opakování, nejvýše `RETRIES` (výchozí 3). Pak `failed`.
- Konflikty gitu: runner nikdy netlačí silou; při konfliktu zastaví úkol a nastaví `blocked`.
- Žádné automatické slučování do `main`.

## 13. Otevřené body

1. Přesná jména polí ve výstupu `claude -p --output-format json` (model, spotřeba, cena) — ověřit prvním během.
2. Zda CLI vrací effort; dokud ne, `effort_verified = false`.
3. Strop počtu vstupů u `workflow_dispatch` (předpoklad 10) a zda předvyplnění souboru odkazem funguje jako záloha.
4. Spouštění bez dohledu: cron nebo démon s `POLL_SECONDS`, podle toho, zda má stroj běžet trvale.
5. Zda dashboard poběží z `file://`, nebo z GitHub Pages (u Pages je potřeba veřejný nebo privátní repozitář s Pages).
6. Jak se bude počítat cena na předplatném, kde se neplatí za tokeny; zřejmě jen spotřeba, cena `null`.

## 14. Mimo rozsah

- Vlastní obsah úkolů (zadání komponenty, kód, testy); loop je jen nosič.
- Server, fronta, uživatelské účty, notifikace.
- Automatické slučování větví a nasazení.
