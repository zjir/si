# TASK-0010 — stav (kolo 1, 2026-10-03)

## Hotovo
- Priorita D-99: 5.3 (a)/(b) × 6.7 × 7.4 × 13.2.7 × 13.17.1 přečteno. Nález B1 (D-101): 5.4 ukládalo jemný čas u kandidáta, 5.2 pole nemělo, maskování snapshotu 13.2.7 ho nezahrnovalo → `cand_hi_fine`/`cand_lo_fine` v 5.2 (+ inicializace), odkaz v 5.4, maskování v 13.2.7, D-101, historie řádek 12, hlavička kolo 12.
- Rozpracováno (drobné, zatím nezapsáno): 5.3 poznámka „při θ_pb = θ vždy obsaženo v (a)“ neplatí při `dir = DOWN` a nepotvrzeném low (ATR kandidáta > atr_ref(t)); 13.17.1 bod 4 doplnit, že referenční výpočet počítá `intrabar_ambiguous` včetně (b).

## Zbývá
- D-100 místa (12.2 ověřeno; 13.16.3 WARN ověřeno), zbytek dokumentu (sekce 1–4, 6, 8–11, 13.x, 15), kontrola křížových odkazů D-xx/R-x/I-x.
