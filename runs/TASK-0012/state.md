# TASK-0012 — stav po kole 1 (2026-10-03)

## Hotovo (kolo 1)
- D-103/I-17 ověřeno první: 3.4 × 5.3 bod 1 × 5.4 Časy × 10.3 (tabulka + odstavec D-93) × 13.17.1 bod 4 × 13.17.3 × I-17 × log D-103 — bez rozporu. D-104 (5.4 komentář) bez nálezu.
- Přečteno celé: 1, 4, 10.1–10.2, 11, 12, 13.1, 13.2 brány 1–10, 13.3, 13.4–13.15, 13.16.1–13.16.2, 13.16.4–13.16.6, 14.
- Střední (1, D-105): zaokrouhlení hodnoty přesně ,5 na celé číslo nebylo určeno (13.11 perturbace ±25 %: `atr_n` 30 → 22,5/37,5, `pw3_max` 30, `sr_max_levels` 6 → 4,5/7,5; 12.2 bod 1 `round((i+0,5)×n/8)` při `n ≡ 8 (mod 16)` a 0/1-based pořadí; 12.3 mřížka `pw3_max` při W = 45, 75). Zapsána globální konvence půl nahoru `⌊x + 0,5⌋` do 4.5 (včetně pravidla ceny na tick: přesně uprostřed → nižší tick) a odkazy v 12.2, 12.3, 13.11.
- Drobné (6, D-106): bin denní doby `30 × ⌊m/30⌋` definován v 13.6, odkazy 13.14.2 a 15.4; 13.5 simulace kroky `i ≥ 1`, OBNOVENÍ `c_i > H` ostře (jako 13.4); 13.8 vzorek auditu systematicky v časovém pořadí bez semínka (13.20 sladěno, `audit/sample.json` nese pravidlo a N); 13.14.2 `atr_ref(t_pub)` (první bar s `ts_open ≥ valid_from`); 10.1 prefixy `stat_`, `news_`, `extra_<name>_` a 13.3 sloupce baru podle 13.16.6; 14 sloučeny duplicitní body o vstupních zónách.
- Hlavička kolo 14; log D-105, D-106; historie řádek 14; poslední řádek KONEC DOKUMENTU; kontrola odkazů D-1–D-106, I-1–I-17 a číslovaných sekcí skriptem bez nálezu. `result.json` DONE.

## Nečteno v tomto kole (celé čteno v TASK-0010/0011 bez nálezu)
- 2, 3.5–3.10, 5, 6–9, 10.3–10.5, 13.2 syntetika, 13.16.3, 13.17–13.20, 15, log D-1–D-102 (jen grep).

## Zbývá
- Nic v tomto úkolu (max_rounds 1, DONE). Doporučení pro další kontrolní kolo: průchod nad novým textem D-105/D-106 a sekcemi výše; D-81–D-106 neotvírat bez nového argumentu.
