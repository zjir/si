# TASK-0008 — stav po kole 1 (2026-10-03)

## Hotovo (kolo 1)
- Celý dokument přečten (1–15 úplně, 0 a 16 křížově; automatická kontrola odkazů D-xx, sekcí, I-x, R-x, bran 13.2.x bez nálezu).
- Blokující (1, D-97): brána 13.2.7 byla nesplnitelná — snapshot obsahuje záznamy swingů s `ts_ext_fine` (null jen v běhu `heuristic`), takže by se snapshoty obou běhů po prvním swingu nikdy neshodly a okna rozdílu by se nezavřela; událost `INTRABAR_MISMATCH` vzniká jen v běhu `auto`. Maskování snapshotu rozšířeno o `ts_ext_fine`, událost vyjmuta z porovnání, události porovnávány po skupinách `t_known`.
- Střední (1, D-97): okno rozdílu `[t_a, t_e]` včetně `t_e` (výstupy baru `t_e` vznikají z ještě odlišného stavu); kritérium rozděleno na (a) úseky neshody snapshotů začínají barem `intrabar_ambiguous`, (b) bary s rozdílem výstupů leží v oknech.
- Drobné (7, D-98): 3.4 rozdíl režimů jen v oknech; 8.1 ořez logu proražení = `t_keep` z 10.5; 10.4 `BAR_SKIPPED` na úrovni WARNING; 13.16.4 bod 6 výjimka pro 13.2.7; 13.17.3 `BAR_SKIPPED` mimo hlavní porovnání; sekce 2 `swings_new`/`SWING_CONFIRMED` místo `swings`; 13.4 formulace začátku sledování.
- Hlavička kolo 10; historie řádek 10; poslední řádek KONEC DOKUMENTU.

## Ověřeno bez nálezu
- 10.3 warmup × 4.1 × 3.5 × 13.16.5 bod 3 × I-1 × 15.2; 10.5 ořez × 6.1.1 × 7.4 × 8.1 × 8.2 × 9; 13.4 × 13.5 × 15.4; 12.2 dělení 28/12 (`i mod 10 ∈ {3,6,9}` = 12 dnů); 11.4 × 10.4 × 13.17.3; 13.15.6 bod 1 indexy S1 (`H₈` = bar 230).

## Zbývá
- Nic v tomto úkolu (max_rounds 1). Doporučení pro další kontrolní kolo: druhý průchod nad novým textem 13.2.7 (D-97) proti 10.5 a 13.16.4 a nad 13.17.3; D-81–D-98 neotvírat bez nového argumentu.
