# TASK-0002 — stav po kole 1

## Hotovo (kolo 1)

- Přečteno: celé zadání, celý popis P.A.T. (42 stran; Read bez `pages` funguje, s `pages` selhává — chybí pdftoppm), POPIS CSV z obrázků, hlavička CSV, zadání SR a testy (obě jen ve stavu dodatků).
- `zadani/komponenta-trend.md` přepsáno celé (1154 řádků, sekce 0–17), sekce „Dodatky k zapracování“ odstraněna, všech 14 dodatků zapracováno (mapa v logu D-41). Dodatek 14 (kalendář zpráv Forex Factory) byl zadavatelem doplněn na konec souboru během kola → zapracován jako 3.9 (D-45).
- Struktura dokumentu: 0 kontext · 1 účel (1.1 Ø1 `answer`, 1.3 detektory A/B/C/D, 1.4 vztah k SR a testům, 1.5 další vstupy) · 2 požadavky P.A.T. · 3 vstupy (3.1 bary + konvence timestampu + validace, 3.2 session, 3.3 roll, 3.4 delta/1s/tabulka, 3.5 úrovně, 3.6 deník, 3.7 TF, 3.8 požadavky R1–R4, 3.9 kalendář zpráv) · 4 normalizace (ATR, `atr_ref = atr1(t−1)`, osa, zarovnání, `anchor_mode`, porovnání v ticích) · 5 zigzag (pseudokód, pořadí v baru) · 6 struktura (korekce `[t_H, t_H')`, přijatá low, `prev_major_low`), hlavní TL s pseudokotvami, aktuální TL, projekce, prolomení, sklon, pořadí v baru · 7 fáze/`direction`/pullback · 8 metriky, PW-SW, `strength` · 9 delta · 10 rozhraní (typy, stav, události, testovatelnost) · 11 požadavky · 12 parametry + kalibrace · 13 testy (brány 1–9, S1–S10, 13.11 robustnost, 13.12 TF, 13.13 deník) · 14 mimo rozsah · 15 metody (M1–M17, detektor B, C tabulka, D ML, plug-in) · 16 log D-1…D-46 · 17 historie · KONEC DOKUMENTU.
- Druhý průchod (kolo 1) opravil: okno kontroly timestampu, warmup, `prev_major_low` u nového kandidáta, interval korekce, `H_final` = běžící maximum, start pullbacku v baru `TREND_START`, kolizi 13.2.1, `continuation_source`, `price_conf`, PW3 index, vzorec `value_at` u aktuální TL, převod časů CSV.

## Zbývá (kolo 2)

Třetí průchod v rolích implementátor/tester; konkrétní body v `runs/TASK-0002/round-01/notes.md` (sekce „Co zkontrolovat v kole 2“): 3.9 typy `ScheduledEvent`/`Release` + aliasy názvů zpráv + warmup; 15.2 zarovnání při `direction = NONE`; 13.2 brána 6 jako tabulka; 12.2 formát anotace; 7.4 `pb_low` u restartu; 10.3 vs 6.4 sjednoceno; soulad `komponenta-sr.md` s 3.5 (`level_id`, `valid_from`, `kind`).

## Klíčová rozhodnutí (log D-1…D-46 v dokumentu)

Ø1 primární výstup; detektory A+B+C, D vypnutý; `atr_ref(t) = atr1(t−1)`; stupně swingů přes korekce; pseudokotvy; PW2 vůči aktuální TL; deník jen 13.13 + `min_slope`; TF 1min; robustnostní brána 13.11; tabulka pokračování ≤ 24 binů; kalendář zpráv jen jako rys (A nečte).

## Zkoušeno / nefunguje

- Read PDF s `pages` → chyba pdftoppm; Read bez `pages` vrátí celý dokument.
- Soubor zadání se během kola změnil mimo kontext (doplněn dodatek 14 za `KONEC DOKUMENTU`); před každým kolem číst konec souboru, zda nepřibyly další dodatky.

## Nálezy kola 1 (před zapracováním)

Blokující 6 / střední 58 / drobné 11 — rozpis v `round-01/notes.md`.

## Požadavky (requests)

R1 bid/ask objem; R2 data ES/YM; R3 rozsah 1s dat; R4 konvence timestampu exportu.
