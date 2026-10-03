# Kontext úkolu

- Úkol: TASK-0012 — review 10: trend — kontrolní průchod celým dokumentem po zapracování nálezů TASK-0011 (D-103–D-104, I-17)
- Režim: spec
- Kolo: 1 (strop tohoto běhu: kolo 1)
- Datum: 2026-10-03T16:28:50+02:00
- Pracovní složka: kořen repozitáře; všechny cesty jsou relativní k ní.

## Cíl

Zreviduj zadani/komponenta-trend.md v roli recenzenta (agent-loop/review-loop/review.md): projdi celý dokument (sekce 1–17 včetně podsekcí 13.x, rozhodovací log, historie revizí), vyplň všechna prázdná místa, odstraň rozpory a nekonzistence mezi sekcemi, zejména ty, které mohly vzniknout změnami kola 1 TASK-0011 (D-103: intrabar_order v režimu close = SINGLE vždy po warmupu nezávisle na intrabar_mode, UNKNOWN jen warmup a heuristika body/wick — 5.3 × 3.4 × 13.17.1 bod 4 × 13.17.3 × nový invariant I-17 v 13.17.4; D-104: komentáře v pseudokódu 5.4 k ukládání cand_*_lvl/cand_*_fine), vše v kontextu systému P.A.T. Sekce 10.1–10.2, 11, 12, 13.1, 13.4–13.15, 13.16.1–13.16.2, 13.16.4–13.16.6 a 14 byly v TASK-0011 jen cíleně prohledány (grep), ne čteny celé: tentokrát je přečti celé. Žádné dodatky zadavatele; jde o kontrolní kolo. Nálezy zapracuj do dokumentu, zaznamenej do rozhodovacího logu a historie revizí.

## Hotovo, když

Průchod celým dokumentem nenajde žádný blokující ani střední nález; zapracované nálezy jsou zaznamenané v rozhodovacím logu a historii revizí; všechny křížové odkazy (sekce, D-xx, R-x, I-x, brány, scénáře) vedou na existující místa; poslední řádek je KONEC DOKUMENTU.

## Vstupy (čti podle potřeby, cíleně)

- `data/README.md`
- `data/NQ/README.md`
- `data/FDAX/README.md`
- `runs/TASK-0011/state.md`
- `runs/TASK-0011/round-01/result.json`

## Rozsah

Smíš měnit:

- `zadani/komponenta-trend.md`
- `data/README.md`

Nesmíš měnit (má přednost):

- (nic)

Vždy smíš zapisovat do `runs/TASK-0012/` (stav úkolu a soubory tohoto kola).

## Stav a minulé kolo

- Stav úkolu: `runs/TASK-0012/state.md` (zatím neexistuje, jde o první kolo; vytvoř ho)
- Výsledek minulého kola: (žádný, první kolo)
- Diff minulého kola: (žádný)

## Poznámky zadavatele

Jediné kolo (max_rounds 1): výsledek kola je konečný, zapiš DONE nebo CONTINUE s přesným next. Podklady PAT/ a datové soubory data/** (kromě .md) nejsou k dispozici; nic z PAT znovu neověřuj, vycházej z textu dokumentu a data/*/README.md. Rozhodnutí vyžadující PAT podklad rozhodni jako předpoklad s kontrolou při implementaci a zapiš do requests. Rozhodovací log je závazný: D-81–D-104 neotvírej bez nového argumentu; nepřidávej zpět orákulum ani číslování G1–G11 / S01–S21; číslování sekcí 14–17 zachovej. Dokument je velký (~335 KB, ~2000 řádků): čti po částech (≤ 420 řádků), dlouhé řádky zkracuj v Pythonu, zapisuj průběžně a po každém větším kroku checkpoint. Priorita: nejdřív nový text D-103 (5.3 × 3.4 × 13.17.1 × 13.17.3 × I-17) a D-104, pak úplné čtení sekcí dosud jen prohledaných (10.1–10.2, 11, 12, 13.1, 13.4–13.15, 13.16.1–13.16.2, 13.16.4–13.16.6, 14), pak zbytek dokumentu.

## Výstupy tohoto kola

- `runs/TASK-0012/state.md` — přepiš aktuálním stavem.
- `runs/TASK-0012/round-01/result.json` — povinné; `"task": "TASK-0012"`, `"round": 1`.
- `runs/TASK-0012/round-01/notes.md` — volitelné.
