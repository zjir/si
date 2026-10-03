# TASK-0012 — stav kola 1 (2026-10-03)

## Hotovo
- D-103/I-17 text ověřen: 3.4 × 5.3 bod 1 × 5.4 Časy × 10.3 (tabulka + odstavec D-93) × 13.17.1 bod 4 × 13.17.4 I-17 × log D-103 — bez rozporu. D-104 (5.4 komentář) bez nálezu.
- Přečteno celé: 10.1–10.2, 11, 12, 13.1, 13.4–13.15, 4.
- Nálezy ZAPRACOVÁNY (4.5 konvence, 10.1, 12.2, 12.3, 13.5, 13.6, 13.8, 13.11, 13.14.2, 13.19.1, 13.20, 14, 15.4; log D-105, D-106; historie řádek 14; hlavička kolo 14; kontrola odkazů D/I/sekce bez nálezu):
  1. (střední) zaokrouhlení poloviny na celé číslo není definováno: 13.11 perturbace ±25 % (atr_n 30 → 22,5/37,5; pw3_max 30; sr_max_levels 6 → 4,5/7,5), 12.2 bod 1 `round((i+0,5)×n/8)` (n ≡ 8 mod 16 dává přesně ,5; 0/1-based pořadí), 12.3 `pw3_max` ∈ {W/4, …} (W = 45, 75 → ,5); Python `round` = půl k sudému → dva implementátoři jinak → globální konvence půl nahoru `⌊x + 0,5⌋` do 4.5.
  2. (drobný) denní doba: 13.6 a 13.14.2 „po 30 min“ vs. 15.4 „zaokrouhlené na 30 min“ → definovat bin `⌊m / 30⌋ × 30` jednou (13.6), odkázat.
  3. (drobný) 13.5 simulace: OBNOVENÍ `c_i ≥ H` vs. 13.4 `ext_high > H` (ostré); krok `i` od 1 → sjednotit (`c_i > H`, i ≥ 1).
  4. (drobný) 13.8 „náhodný vzorek … semínko v reportu“ bez pravidla → systematický výběr v časovém pořadí (jako 13.5 bod 2 / 12.2 bod 1), bez semínka.
  5. (drobný) 13.14.2 `atr_ref(valid_from)` → `atr_ref` prvního baru rozsahu s `ts_open ≥ valid_from`.

## Rozpracováno
- Přečteno celé i 13.16.1–13.16.2, 13.16.4–13.16.6, 14. Dočítá se 13.2–13.3, 1–2, 3.5–3.9.

## Zbývá
- Dočíst zbytek, nastavit DONE (max_rounds 1).
