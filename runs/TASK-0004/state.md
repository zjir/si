# TASK-0004 — stav po kole 2 (2026-10-01)

## Hotovo v kole 2

- Úplný kontrolní průchod celým dokumentem po sloučení modulu SR (kolo 1). Nálezy 1 B / 17 S / 15 D (14 v hlavním průchodu, 1 drobný v druhém průchodu nad novým textem: inkluzivní `valid_to` fixture v 13.14.1 bod 4), všechny zapracovány do textu, log D-62–D-66, historie řádek „3 (TASK-0004 kolo 2)“ (dokumentové číslování kol: kolo 3 = TASK-0004 kolo 2).
- Blokující: test SR1 (13.14.1) byl s odrazem 4A a nesousedními dny nesplnitelný (skóre < 1) → odraz 6A, tři po sobě jdoucí dny, bar publikace z referenčního výpočtu.
- Hlavní změny: modul SR nezávislý na `TrendParams` (`theta_sr` 3,0, `atr_n_sr` 30 explicitně; vlastní `on_invalid_bar`; zigzag bez 1s dat; `t_known` v indexu proudu modulu) — D-62; vydání sady PD* (podmínka `ts_open ≥ pd_scope_close(D)` nebo pozdější session), `level_id` PD* podle zdrojového dne, expirace `PREMARKET_*`/`SESSION_OPEN` v prvním baru další session, kandidát v toleranci publikované úrovně se slučuje, remíza nejslabšího, `LEVEL_UPDATED` při změně `strength` (3 des.) — D-63; 1s data: `Bar1s`, výběr barů `[ts_open, ts_close)`, pořadí extrémů přes `high ≥ ext_high` / `low ≤ ext_low`, kontrola shody `INTRABAR_MISMATCH`, `intrabar_used` — D-64; hodnoty závislé na úrovních minulých barů se ukládají (chop okno W, log proražení ořezávaný pod kandidáty zigzagu, `last_bar_with_levels`) — D-65; kalibrace 12.2 na NQ, 8 dnů na kvintil, náhradní postup bez anotace, 13.2.1 1 000 bodů NQ + 200 FDAX, HOLD/BREAK přes high/low/close — D-66.
- Drobné: odkazy v sekci 2 (3.10.1→3.10.2/3.10.3), 3.1 krok (3) (bary mimo rozsah jen modulu SR), `ROLL_GAP` jen po warmupu, signatura `bars_1s(t, ts_open)`, 3.5 text o „samostatné úloze“ nahrazen, `n_levels_active` definováno, 3.9 věta o měnách v oknech, 9 R1 splněn a `tick_size` delty, 10.1 `scope_from/to` mimo hash, 10.4 `INTRABAR_MISMATCH`, 12.4 hash bez `sr_break_atr`, 13.5 drift trhu, 13.11 perturbace i 12.4.
- Položky ze stavu kola 1 vyřešeny: 1 (konzistence 3.10/10: `n_levels_active`, `levels_crossed`, `LEVEL_UPDATED`), 2 (žádné ET v 13.5/13.12/12.2; 12.2 výslovně NQ), 3 (`bounce_atr` přes den OK — cap min(1,·); `sr_min_score` 1,0 ponecháno, kalibrační rozsah 0,5–2 to pokrývá; `LEVEL_UPDATED` řešeno D-63), 4 (okna zpráv nad událostmi po filtru měn, bez dalšího rozlišení), 5 (13.4 obě varianty horizontu u FDAX ponechány, je to report), 6 (fixture testy.md — jen R5, mimo rozsah).

## Otevřené požadavky (mimo dokument, nebrání DONE)

- R5: smazat `zadani/komponenta-sr.md`, opravit odkazy v `zadani/testy.md` (řádek 24, fixture 3.5, ET → MarketSpec) a `data/README.md` 10 — mimo rozsah recenzenta.
- R6: zdroj kalendáře zpráv 2025-04-08 až 2026-09-25 (WebSearch/WebFetch recenzentovi nepovoleny) — platí vrstvené zdroje 3.9.

## Co bylo zkoušeno a nefungovalo

- Kolo 1: WebSearch i WebFetch zamítnuty; smazání souboru mimo rozsah.

## Na co se zaměřit v dalším kole (pokud bude)

1. Druhý průchod nad novým textem kola 2: 3.10.2 bod 10–11 (vydání PD* při session bez barů v `pd_scope` a při `ETH`), 3.10.3 krok 3 (sloučení kandidáta s publikovanou: přepočet skóre před dalším kandidátem v témže baru), 5.3 bod 1 (remíza v téže sekundě), 8.1 ořez logu proražení (správnost při `TREND_END` a `t_reset`).
2. Pokud průchod nic nového nenajde → `DONE`.
