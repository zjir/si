# TASK-0011 — stav po kole 1 (2026-10-03)

## Hotovo (kolo 1)
- Priorita D-101/D-102 ověřena první: 5.2 cand_*_fine (včetně inicializace t0) × 5.4 × 10.5 snapshot × 13.2.7 maskování × 13.2.8; 5.3 poznámka, 13.17.1 bod 4, 9, 3.10.3; `params_hash` bez `intrabar_mode` (10.1). Bez nálezu.
- Střední (1, D-103): `intrabar_order` v režimu `close` při `intrabar_mode = heuristic` — 5.3 bod 1 věta „jinak … UNKNOWN“ × 13.17.1 bod 4 `SINGLE`; 13.17.3 pole porovnává → rozhodnuto `SINGLE` vždy po warmupu v `close` (nezávisle na `intrabar_mode`), `UNKNOWN` jen warmup a heuristika `body`/`wick`. Zapsáno do 5.3, 3.4, 13.17.1; nový invariant I-17 (13.17.4): warmup × close × body/wick × `intrabar_used` ⇔ `intrabar_order` × `ts_ext_fine`.
- Drobné (2, D-104): 5.4 komentář v pseudokódu (každé nastavení/posun kandidáta ukládá i `cand_*_lvl`, `cand_*_fine`); I-17.
- 13.18–13.20 a 15 přečteny celé: bez nálezu (13.20.1 čte bar sloupce z logu 13.3; seedy S1 = 1 … S11b = 12, SR1 = 13 … SR5 = 17; 15.2 `n < 30` jen při `atr_n < 30`; 15.4 biny = `trend_valid` 7.2).
- Dále čteno celé: 3.1–3.4, 5, 6.1–6.7, 7.1–7.4, 8, 9, 10.3–10.5, 13.2, 13.16.3, 13.17.1–13.17.4; bez nálezu.
- Hlavička kolo 13; log D-103, D-104; historie řádek 13; poslední řádek KONEC DOKUMENTU; kontrola odkazů D/I skriptem bez nálezu. `result.json` DONE.

## Ověřeno jen cíleně (grep, ne celé čtení)
- 10.1–10.2, 11, 12, 13.1, 13.4–13.15, 13.16.1–13.16.2, 13.16.4–13.16.6, 14, log D-1–D-100 (hledání intrabar_*, cand_*_fine, ts_ext_fine, θ_pb, trading_date, SINGLE, I-16).

## Zbývá
- Nic v tomto úkolu (max_rounds 1, DONE). Doporučení pro další kontrolní kolo: průchod nad novým textem D-103/I-17 a sekcemi uvedenými výše jako jen cíleně prohledané; D-81–D-104 neotvírat bez nového argumentu.
