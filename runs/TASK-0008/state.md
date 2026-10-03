# TASK-0008 — stav (kolo 1, 2026-10-03)

## Hotovo
- Přečteno: 3.5, 4, 5, 6, 7, 8, 9, 10.3–10.5, 11, 12, 13.1–13.13, 13.16–13.20, log D-92–D-96, historie.
- Blokující B1 (13.2.7): snapshoty bez maskování `ts_ext_fine` se nikdy neshodnou → maskování rozšířeno (D-97).
- Střední M1 (13.2.7): okno rozdílu `[t_a, t_e]` včetně `t_e`; kritérium rozděleno na (a) úseky neshody snapshotů, (b) bary s rozdílem výstupů (D-97).

## Rozpracováno / drobné k zapracování
- 8.1 ořez logu proražení: `t₀ obou stran` nedefinováno u strany bez `L₀` → sjednotit s 10.5 (`t_reset`).
- 10.4: úroveň logování `BAR_SKIPPED` (WARNING jako varování, 11.4).
- 13.16.4 bod 6: u 13.2.7 porovnání událostí po skupinách `t_known` (id maskována).
- 13.17.3: `BAR_SKIPPED` vyjmout z hlavního porovnání událostí (porovnává se zvlášť).

## Zbývá
- Číst: 0–3 (3.1–3.4, 3.6–3.10), 10.1–10.2, 13.14, 13.15, 14–15, log D-1–D-91 (jen křížové odkazy).
- Pak hlavička (kolo 10), historie řádek 10, KONEC DOKUMENTU.
