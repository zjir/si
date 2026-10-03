# Kontext úkolu

- Úkol: TASK-0010 — review 8: trend — kontrolní průchod celým dokumentem po zapracování nálezů TASK-0009 (D-99–D-100)
- Režim: spec
- Kolo: 1 (strop tohoto běhu: kolo 1)
- Datum: 2026-10-03T16:07:47+02:00
- Pracovní složka: kořen repozitáře; všechny cesty jsou relativní k ní.

## Cíl

Zreviduj zadani/komponenta-trend.md v roli recenzenta (agent-loop/review-loop/review.md): projdi celý dokument (sekce 1–17 včetně podsekcí 13.x, rozhodovací log, historie revizí), vyplň všechna prázdná místa, odstraň rozpory a nekonzistence mezi sekcemi, zejména ty, které mohly vzniknout změnami kola 1 TASK-0009 (5.3 intrabar_ambiguous podmínka (b) × 7.4 × 13.2.7; 13.2.7 otevřené okno bez t_e = do konce období, open = true, WARN; 13.17.1 bod 4 referenční výpočet intrabar_ambiguous včetně (b); 12.2 anotace parametrů; 5.4 ts_ext_fine jen při intrabar_used = true; 13.16.3 WARN × okna 13.2.7), vše v kontextu systému P.A.T. Žádné dodatky zadavatele; jde o kontrolní kolo. Nálezy zapracuj do dokumentu, zaznamenej do rozhodovacího logu a historie revizí.

## Hotovo, když

Průchod celým dokumentem nenajde žádný blokující ani střední nález; zapracované nálezy jsou zaznamenané v rozhodovacím logu a historii revizí; všechny křížové odkazy (sekce, D-xx, R-x, I-x, brány, scénáře) vedou na existující místa; poslední řádek je KONEC DOKUMENTU.

## Vstupy (čti podle potřeby, cíleně)

- `data/README.md`
- `data/NQ/README.md`
- `data/FDAX/README.md`
- `runs/TASK-0009/state.md`
- `runs/TASK-0009/round-01/result.json`

## Rozsah

Smíš měnit:

- `zadani/komponenta-trend.md`
- `data/README.md`

Nesmíš měnit (má přednost):

- (nic)

Vždy smíš zapisovat do `runs/TASK-0010/` (stav úkolu a soubory tohoto kola).

## Stav a minulé kolo

- Stav úkolu: `runs/TASK-0010/state.md` (zatím neexistuje, jde o první kolo; vytvoř ho)
- Výsledek minulého kola: (žádný, první kolo)
- Diff minulého kola: (žádný)

## Poznámky zadavatele

Jediné kolo (max_rounds 1): výsledek kola je konečný, zapiš DONE nebo CONTINUE s přesným next. Podklady PAT/ a datové soubory data/** (kromě .md) nejsou k dispozici; nic z PAT znovu neověřuj, vycházej z textu dokumentu a data/*/README.md. Rozhodnutí vyžadující PAT podklad rozhodni jako předpoklad s kontrolou při implementaci a zapiš do requests. Rozhodovací log je závazný: D-81–D-100 neotvírej bez nového argumentu; nepřidávej zpět orákulum ani číslování G1–G11 / S01–S21; číslování sekcí 14–17 zachovej. Dokument je velký (~315 KB, ~2000 řádků): čti po částech (≤ 420 řádků), dlouhé řádky zkracuj v Pythonu, zapisuj průběžně a po každém větším kroku checkpoint. Priorita: nejdřív nový text D-99 (5.3 (b) × 7.4 × 13.2.7, otevřené okno) a 13.17.1 bod 4, pak D-100 a zbytek dokumentu.

## Výstupy tohoto kola

- `runs/TASK-0010/state.md` — přepiš aktuálním stavem.
- `runs/TASK-0010/round-01/result.json` — povinné; `"task": "TASK-0010"`, `"round": 1`.
- `runs/TASK-0010/round-01/notes.md` — volitelné.
