# Kontext úkolu

- Úkol: TASK-0008 — review 6: trend — kontrolní průchod celým dokumentem po zapracování nálezů TASK-0007 (D-92–D-96)
- Režim: spec
- Kolo: 1 (strop tohoto běhu: kolo 1)
- Datum: 2026-10-03T15:42:34+02:00
- Pracovní složka: kořen repozitáře; všechny cesty jsou relativní k ní.

## Cíl

Zreviduj zadani/komponenta-trend.md v roli recenzenta (agent-loop/review-loop/review.md): projdi celý dokument (sekce 1–17 včetně podsekcí 13.x, rozhodovací log, historie revizí), vyplň všechna prázdná místa, odstraň rozpory a nekonzistence mezi sekcemi, zejména ty, které mohly vzniknout změnami kola 1 TASK-0007 (10.3 warmup × 3.5 × 15.2 × 15.6; 10.5 ořez swingů × 8.2 PW1 × 7.4 n_inner_swings × 13.2.8 snapshot; 13.2.7 × 13.16.4; 13.4 × 13.5 × 15.4; 12.2 × 12.3; 11.4 × 10.4 × 13.17.3), vše v kontextu systému P.A.T. Žádné dodatky zadavatele; jde o kontrolní kolo. Nálezy zapracuj do dokumentu, zaznamenej do rozhodovacího logu a historie revizí.

## Hotovo, když

Průchod celým dokumentem nenajde žádný blokující ani střední nález; zapracované nálezy jsou zaznamenané v rozhodovacím logu a historii revizí; všechny křížové odkazy (sekce, D-xx, R-x, I-x, brány, scénáře) vedou na existující místa; poslední řádek je KONEC DOKUMENTU.

## Vstupy (čti podle potřeby, cíleně)

- `data/README.md`
- `data/NQ/README.md`
- `data/FDAX/README.md`
- `runs/TASK-0007/state.md`
- `runs/TASK-0007/round-01/result.json`

## Rozsah

Smíš měnit:

- `zadani/komponenta-trend.md`
- `data/README.md`

Nesmíš měnit (má přednost):

- (nic)

Vždy smíš zapisovat do `runs/TASK-0008/` (stav úkolu a soubory tohoto kola).

## Stav a minulé kolo

- Stav úkolu: `runs/TASK-0008/state.md` (zatím neexistuje, jde o první kolo; vytvoř ho)
- Výsledek minulého kola: (žádný, první kolo)
- Diff minulého kola: (žádný)

## Poznámky zadavatele

Jediné kolo (max_rounds 1): výsledek kola je konečný, zapiš DONE nebo CONTINUE s přesným next. Podklady PAT/ a datové soubory data/** (kromě .md) nejsou k dispozici; nic z PAT znovu neověřuj, vycházej z textu dokumentu a data/*/README.md. Rozhodnutí vyžadující PAT podklad rozhodni jako předpoklad s kontrolou při implementaci a zapiš do requests. Rozhodovací log je závazný: D-81–D-96 neotvírej bez nového argumentu; nepřidávej zpět orákulum ani číslování G1–G11 / S01–S21; číslování sekcí 14–17 zachovej. Dokument je velký (~312 KB, ~2000 řádků): čti po částech (≤ 420 řádků), dlouhé řádky zkracuj v Pythonu, zapisuj průběžně a po každém větším kroku checkpoint. Priorita: nejdřív oblasti změněné v TASK-0007 r01, pak zbytek dokumentu.

## Výstupy tohoto kola

- `runs/TASK-0008/state.md` — přepiš aktuálním stavem.
- `runs/TASK-0008/round-01/result.json` — povinné; `"task": "TASK-0008"`, `"round": 1`.
- `runs/TASK-0008/round-01/notes.md` — volitelné.
