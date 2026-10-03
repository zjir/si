# Kontext úkolu

- Úkol: TASK-0013 — review 11: trend — kontrolní průchod celým dokumentem po zapracování nálezů TASK-0012 (D-105–D-106)
- Režim: spec
- Kolo: 1 (strop tohoto běhu: kolo 1)
- Datum: 2026-10-03T16:43:30+02:00
- Pracovní složka: kořen repozitáře; všechny cesty jsou relativní k ní.

## Cíl

Zreviduj zadani/komponenta-trend.md v roli recenzenta (agent-loop/review-loop/review.md): projdi celý dokument (sekce 1–17 včetně podsekcí 13.x, rozhodovací log, historie revizí), vyplň všechna prázdná místa, odstraň rozpory a nekonzistence mezi sekcemi, zejména ty, které mohly vzniknout změnami kola 1 TASK-0012 (D-105: globální konvence zaokrouhlení půl nahoru ⌊x + 0,5⌋ v 4.5 včetně pravidla ceny na tick × odkazy 12.2 bod 1, 12.3, 13.11 perturbace; D-106: bin denní doby 30 × ⌊m/30⌋ v 13.6 × 13.14.2 × 15.4, 13.5 simulace i ≥ 1 a OBNOVENÍ c_i > H ostře, 13.8 vzorek auditu v časovém pořadí bez semínka × 13.20 × audit/sample.json, 13.14.2 atr_ref(t_pub), 10.1 prefixy stat_/news_/extra_<name>_ × 13.3 × 13.16.6, 14 sloučené body o vstupních zónách), vše v kontextu systému P.A.T. Sekce 2, 3.5–3.10, 5, 6–9, 10.3–10.5, 13.2 syntetika, 13.16.3, 13.17–13.20, 15 a log D-1–D-102 nebyly v TASK-0012 čteny celé (jen grep, celé čteny naposledy v TASK-0010/0011): tentokrát je přečti celé. Žádné dodatky zadavatele; jde o kontrolní kolo. Nálezy zapracuj do dokumentu, zaznamenej do rozhodovacího logu a historie revizí.

## Hotovo, když

Průchod celým dokumentem nenajde žádný blokující ani střední nález; zapracované nálezy jsou zaznamenané v rozhodovacím logu a historii revizí; všechny křížové odkazy (sekce, D-xx, R-x, I-x, brány, scénáře) vedou na existující místa; poslední řádek je KONEC DOKUMENTU.

## Vstupy (čti podle potřeby, cíleně)

- `data/README.md`
- `data/NQ/README.md`
- `data/FDAX/README.md`
- `runs/TASK-0012/state.md`
- `runs/TASK-0012/round-01/result.json`

## Rozsah

Smíš měnit:

- `zadani/komponenta-trend.md`
- `data/README.md`

Nesmíš měnit (má přednost):

- (nic)

Vždy smíš zapisovat do `runs/TASK-0013/` (stav úkolu a soubory tohoto kola).

## Stav a minulé kolo

- Stav úkolu: `runs/TASK-0013/state.md` (zatím neexistuje, jde o první kolo; vytvoř ho)
- Výsledek minulého kola: (žádný, první kolo)
- Diff minulého kola: (žádný)

## Poznámky zadavatele

Jediné kolo (max_rounds 1): výsledek kola je konečný, zapiš DONE nebo CONTINUE s přesným next. Podklady PAT/ a datové soubory data/** (kromě .md) nejsou k dispozici; nic z PAT znovu neověřuj, vycházej z textu dokumentu a data/*/README.md. Rozhodnutí vyžadující PAT podklad rozhodni jako předpoklad s kontrolou při implementaci a zapiš do requests. Rozhodovací log je závazný: D-81–D-106 neotvírej bez nového argumentu; nepřidávej zpět orákulum ani číslování G1–G11 / S01–S21; číslování sekcí 14–17 zachovej. Dokument je velký (~342 KB, ~2000 řádků): čti po částech (≤ 420 řádků), dlouhé řádky zkracuj v Pythonu, zapisuj průběžně a po každém větším kroku checkpoint. Priorita: nejdřív nový text D-105 (4.5 × 12.2 × 12.3 × 13.11) a D-106 (13.5, 13.6, 13.8, 13.14.2, 13.20, 10.1, 13.3, 14, 15.4), pak úplné čtení sekcí dosud jen prohledaných (2, 3.5–3.10, 5, 6–9, 10.3–10.5, 13.2 syntetika, 13.16.3, 13.17–13.20, 15, log D-1–D-102), pak zbytek dokumentu.

## Výstupy tohoto kola

- `runs/TASK-0013/state.md` — přepiš aktuálním stavem.
- `runs/TASK-0013/round-01/result.json` — povinné; `"task": "TASK-0013"`, `"round": 1`.
- `runs/TASK-0013/round-01/notes.md` — volitelné.
