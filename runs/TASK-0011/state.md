# TASK-0011 — stav (kolo 1, 2026-10-03)

## Hotovo
- D-101 ověřeno: 5.2 cand_*_fine (včetně init t0) × 5.4 × 10.5 snapshot × 13.2.7 maskování × 13.2.8 — konzistentní; params_hash bez intrabar_mode (10.1).
- D-102 ověřeno: 5.3 poznámka, 13.17.1 bod 4, 9, 3.10.3 — konzistentní.
- Střední (D-103, zapsáno v 5.3, 3.4, 13.17.1): v režimu `close` při `intrabar_mode = heuristic` 5.3 dávalo `intrabar_order = UNKNOWN` („jinak“), 13.17.1 bod 4 `SINGLE`; 13.17.3 pole porovnává → rozhodnuto SINGLE vždy po warmupu v `close`, UNKNOWN jen warmup a heuristika body/wick.
- Drobný (D-104): 5.4 pseudokód komentář k cand_*_lvl / cand_*_fine.

## Rozpracováno
- Log D-103/D-104, hlavička (kolo 13), historie řádek 13: ještě nezapsáno.

## Zbývá
- 13.18–13.20 a 15 celé; pak sekce 0–4, 6–8, 10–12, 13.1–13.17, 14, 16; kontrola odkazů skriptem.
