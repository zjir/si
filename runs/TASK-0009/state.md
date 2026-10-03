# TASK-0009 — stav po kole 1 (2026-10-03)

## Hotovo (kolo 1)
- Celý dokument přečten (0–15, 16 D-89–D-98, 17); priorita 13.2.7 × 10.5 × 13.16.4 a 13.17.3 ověřena první.
- Střední (2, D-99): 5.3 `intrabar_ambiguous` doplněno o podmínku (b) (začátek pullbacku v baru `t_H = t` závisí na pořadí zpráv; při `θ_pb < θ` se běhy 13.2.7 lišily mimo okno); 13.2.7 otevřené okno (bez `t_e`) = do konce období, `open = true`, `WARN`.
- Drobné (3, D-100): 12.2 výčet parametrů bez anotace (`theta_pb`, `level_tol`); 5.4 `ts_ext_fine` jen při `intrabar_used = true` v baru `t_ext`; 13.16.3 `WARN` uvádí okna 13.2.7.
- Hlavička kolo 11; log D-99, D-100; historie řádek 11; poslední řádek KONEC DOKUMENTU.

## Ověřeno bez nálezu
- Maskování snapshotu 13.2.7 × 10.5 (`t_keep`, `params_hash` bez `intrabar_mode` 10.1) × 13.16.4 bod 6; 13.17.3 × 10.4 × 11.4 (`BAR_SKIPPED`, varování); sekce 2 × 7.4 × 8.2 (`swings_new`, swingy od `t_keep`); 13.4 × 13.5 × 15.4; 13.15.6 bod 1 indexy; 13.2.10 referenční minuty; modul SR bez 1s dat (3.10.3).

## Zbývá
- Nic v tomto úkolu (max_rounds 1). Doporučení pro další kontrolní kolo: druhý průchod nad novým textem 5.3 (b) × 7.4 × 13.2.7 (D-99) a nad 13.17.1 bod 4 (referenční výpočet musí počítat `intrabar_ambiguous` včetně (b)); D-81–D-100 neotvírat bez nového argumentu.
