# TASK-0005 — stav v kole 3 (2026-10-02), dokumentové kolo 6

## Hotovo v kole 3

- Dodatek zadavatele zapracován: nová podsekce **13.15 Nezávislý zpětný test polohy trendů** (D-80): pravda = optimální segmentace cesty close dynamickým programováním (stavy UP/DOWN/NONE, cena `c` za vstup, normalizace denním průměrem TR, remízy pevně), bez zigzagu/swingů/TL/`TrendParams`; primární `c = 6` ATR, citlivost {3, 4,5, 6, 9, 12}, `c*` = argmax κ; shoda po barech (κ, matice záměn, opačný směr, členění `strength_class`/`phase`), po úsecích (`first_hit`, `delay_start`, `move_left`, `captured ≥ 1/3`, `cover`, `delay_end_bars`, `overrun_atr`, `size_bin`; falešné běhy `overlap < 0,5`, `net_move`); reference: `p_e` kappy, posun o 1–20 obchodních dnů, B0 momentum; brány 13.15.6: 1 kontrola pravdy na syntetice (S1/S3/S4/S8 UP 0→230, S9 0→170, S2 UP 0→140 + DOWN 140→180, S5 nic, S6 střídavě po 30, S7 UP 0→110, S10 zrcadlo, S11a/b UP 0→50), 2 κ > 0 a > posuny, 3 `captured` (gain ≥ 2c) a falešné běhy lepší než posuny, 4 podezření na únik.
- Křížové odkazy: 13.1 (dvě pravdy), 13.3 (log nese bary), 13.4 (vlastní struktura = jen zpoždění), 13.5, 13.6, 13.9 (sada včetně 13.15), 13.10 (brány, únik), 13.11 (a) = κ proti 13.15 (střední nález: dřívější metrika byla shoda s vlastní strukturou); R8 (testy.md), hlavička verze, historie řádek 6.
- Nálezy kola před zapracováním: 0 B / 1 S (13.11 a) / 4 D (13.1, 13.3, 13.5, 13.9 odkazy).

## Rozpracováno

- Kontrolní průchod nad novým textem 13.15 (nové rozhodnutí vytváří nové otázky: remízy DP, warmup, hranice období, S9 indexy) a zbytek druhého průchodu textu kola 5 (13.2.5, 7.4, 6.1.1 krok 2, 12.2 krok 3, 15.5, D-78 — přečteno, bez nálezu).

## Zbývá

1. Dočíst 13.15 v dokumentu po vložení a opravit nesrovnalosti.
2. Bez blokujícího ani středního nálezu → `DONE`.

## Otevřené požadavky (mimo dokument, nebrání DONE)

- R5: smazat `zadani/komponenta-sr.md`, opravit odkazy v `zadani/testy.md` a `data/README.md` 10.
- R7: obnovit `data/NEWS/info.md`.
- R8 (nový): `zadani/testy.md` doplnit provedení testu 13.15.

## Rozhodnutí přijatá v kole 3

- Pravda testu nesmí být odvozena z výstupů ani definic komponenty: zvolena globální optimální segmentace s pevnou cenou (jiná rodina než kauzální zigzag s potvrzením); měřítko `c` pevné, mimo kalibraci.
- Historické metriky 13.15 bez pevných cílů (13.10); pass/fail jen „lepší než náhoda“ (κ, posuny) a kontrola pravdy na syntetice.

## Co bylo zkoušeno a nefungovalo

- Soubor má v klonu LF; číst po ≤ 420 řádcích; dlouhé řádky zkracovat v Pythonu (cut -c láme UTF-8).
- `round.py prepare --takeover` nad kolem s dřívějším checkpointem selže na push (rmtree round-NN nechá unstaged změny); řešení: hned zapsat result.json a `checkpoint --push`, který claim pushne.
