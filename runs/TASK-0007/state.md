# TASK-0007 — stav (kolo 1 rozpracováno)

## Hotovo
- Přečten celý dokument zadani/komponenta-trend.md (0–17 včetně logu) + křížové kontroly (identifikátory událostí, odkazy sekcí, D-čísla).

## Nálezy (před zapracováním)
- B1: 13.2.7 kritérium „výstupy se smí lišit jen od prvního baru intrabar_ambiguous po nejbližší TREND_END“ je nesplnitelné: po rozdílném počtu potvrzených swingů se trvale liší pořadová id (`swing_id`, `event_id`, `pb_id`) ve všech dalších stavech → přepsat kritérium (maskování id, okna rozdílu podle `snapshot()`).
- S1: stav ve warmupu: 4.1 „všechna ostatní pole null“ × 3.5 (`levels_missing`, `n_levels_active` se plní) × 13.16.5 bod 3 × I-1; `bar_index`, `session_id` atd. nemohou být null → přesná tabulka hodnot ve warmupu / fázi NONE.
- S2: 12.2 krok 3–4: dělení 40 dnů na 28 ladicích / 12 ověřovacích není definováno.
- S3: 13.4: od kterého baru se posuzuje horizont (bar t+1), remíza TREND_END v témže baru u TL_BREAK.
- D: 3.10.2 bod 2 formulace („odvodí“ vs. zůstává); 3.5 `meta` klíče (3.10.3, chybí `n_touches_window`); 6.1.1 krok 3 `t_ext ≥ t_L₀` vs `swing_id`; I-4 `n_anchors` při `L0 = null`; 15.4 odkaz „13.16.3 krok 6“ → 5a; 3.1 delta „od prvního baru session“ vs 9; 13.2.2 náhodná procházka nedefinována; 13.2.8 výběr 100 bodů; 13.18.3 `from = "start"`; S10 doji asymetrie heuristiky; 11.4 „jednou za běh“ vs `BAR_SKIPPED` po barech (13.17.3); 7.4 `dist_to_tl_atr_*` = `*.dist_close_atr`.

## Rozpracováno
- Zapracování nálezů do textu + log D-92… + historie kolo 9.

## Pro příští kolo
- Pokud kolo 1 skončí před finalizací: dokončit zápis podle seznamu výše, pak kontrolní průchod změněných míst.
