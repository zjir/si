# TASK-0007 — stav po kole 1 (2026-10-03)

## Hotovo (kolo 1)
- Celý dokument přečten (0–17, log, historie); křížové kontroly identifikátorů událostí, odkazů sekcí, D-čísel, počtu sloupců tabulek.
- Blokující (1): brána 13.2.7 „rozdíl jen do nejbližšího TREND_END“ byla nesplnitelná (pořadová id `swing_id`, `event_id`, `pb_id` se liší do konce běhu) → nové kritérium: maskování id, okna rozdílu od baru `intrabar_ambiguous` do shody `snapshot()`; obsah snapshotu zpevněn ořezem seznamu swingů (10.5); 13.16.4 doplněno (D-92).
- Střední (3): odstavec „Stav ve warmupu a ve fázi NONE“ v 10.3 + odkazy z 4.1, 13.16.5 bod 3, I-1 (D-93); 12.2 dělení 40 dnů na 28/12 (`i mod 10 ∈ {3,6,9}`, D-94); 13.4 „Začátek sledování“ od baru t+1, TREND_END v baru TL_BREAK = SKUTEČNÉ (D-95).
- Drobné (12, D-96): 3.10.2 bod 2; 3.5 `meta` klíče; 6.1.1 krok 3; I-4; 15.4 odkaz; 3.1 delta; 13.2.2 náhodná procházka; 13.2.8 výběr bodů; 13.18.3 "start"/"end"; S10 doji; 11.4 + 13.17.3 `BAR_SKIPPED`; 7.4 `dist_to_tl_atr_*`.
- Hlavička kolo 9; historie řádek 9; poslední řádek KONEC DOKUMENTU; tabulky mají shodný počet sloupců.

## Zbývá (kolo 2)
- Kontrolní průchod celého dokumentu po změnách (nová rozhodnutí mohou vytvořit nové otázky): zejména 10.3 warmup × 3.5 × 15.2 × 15.6; 10.5 ořez swingů × 8.2 PW1 × 7.4 `n_inner_swings` × 13.2.8 snapshot; 13.2.7 × 13.16.4; 13.4 × 13.5 × 15.4 (k, h); 12.2 × 12.3; 11.4 × 10.4 × 13.17.3.
- Neotvírat D-81–D-96 bez nového argumentu; nic z PAT neověřovat; data/README.md nebylo třeba měnit.
- Očekávání: žádný blokující nález; pokud průchod nenajde ani střední, zapsat DONE.
