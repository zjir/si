# TASK-0010 — stav po kole 1 (2026-10-03)

## Hotovo (kolo 1)
- Priorita D-99/D-100 ověřena první: 5.3 (a)/(b) × 6.1.1 krok 5 × 6.7 × 7.4 × 13.2.7 × 13.17.1 bod 4; 12.2; 13.16.3.
- Blokující (1, D-101): 5.4 (D-100) ukládalo jemný čas u kandidáta, ale stav 5.2 pole neměl a maskování snapshotu 13.2.7 je nezahrnovalo → snapshoty `auto`/`heuristic` by se lišily od prvního baru po warmupu, kritérium (a) selhávalo. Doplněno `cand_hi_fine`/`cand_lo_fine` (5.2 + inicializace t0), odkaz v 5.4, maskování v 13.2.7.
- Drobné (3, D-102): 5.3 poznámka „při θ_pb = θ vždy obsaženo v (a)“ opravena (neplatí při dir = DOWN, nepotvrzené low, cand_lo_atr > atr_ref(t)); 13.17.1 bod 4 referenční výpočet počítá `intrabar_ambiguous` včetně (b); 9 a 3.10 `cand_*_fine`/`ts_ext_fine` null, `intrabar_ambiguous` nevyhodnocují.
- Hlavička kolo 12; log D-101, D-102; historie řádek 12; poslední řádek KONEC DOKUMENTU; kontrola odkazů D/R/I/S skriptem bez nálezu.

## Ověřeno bez nálezu
- Sekce 0–4, 6.1–6.7, 7, 8, 9, 10, 11, 13.2–13.17 (čteno zkráceně po řádcích); 13.18–13.20 a 15 jen prohledány na 1s data / snapshot.

## Zbývá
- Nic v tomto úkolu (max_rounds 1). Doporučení pro další kontrolní kolo: průchod nad novým textem D-101 (5.2 × 5.4 × 10.5 × 13.2.7 × 13.2.8) a D-102; úplné čtení 13.18–13.20 a 15; D-81–D-102 neotvírat bez nového argumentu.
