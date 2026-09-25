# TASK-0002 — kolo 1 — poznámky recenzenta

## Nálezy před zapracováním (výchozí zadání + dodatky)

### Blokující (6)

1. 6.1 „nepřerušená sekvence HH + HL“ vs. vnitřní swingy pullbacku (zigzag jednoho stupně) — rozpor v definici struktury; řešeno stupni přes korekce a přijatá low (D-8, D-46).
2. Chybí `tick_size` a pravidlo porovnávání cen (nutné pro kód) — 4.5 (D-10).
3. Nedefinovaná konvence timestampu baru (open/close) — přiřazení session, riziko pohledu do budoucnosti — 3.1 (D-28).
4. Tolerance ε bez definovaného chování při porušení — nelze implementovat; pseudokotvy 6.2 (D-12).
5. Zigzag bez pořadí vyhodnocení high/low v baru — nedeterministické; 5.3 (D-11).
6. Chybí definice primárního výstupu Ø1 (dodatek 5) — 1.1 (D-1).

### Střední (58)

Vstupy: schéma barů a typy; validace neplatných barů; nemonotónní čas; kalendář session (schéma, přiřazení, mimo session); bar rollu; back-adjusted kontrola; delta formát; 1s data (dodatek 2); aktivita úrovní (`valid_from` sémantika); `level_id` a duplicity; rozhraní poskytovatele; acyklicita vs. S/R během seance (kap. I.2); `levels_missing` sémantika; deník nerozhodnut (3.6, 12, 13.9; dodatek 9); TF nerozhodnut (dodatek 3); další vstupy (dodatek 1); SR odkaz (dodatek 12).
Normalizace: ATR studený start; ATR přes mezeru session; podlaha ATR; `atr` v čase t vs t−1 (dodatek 11); znaménkové metriky výčet.
Swingy/TL: remíza ceny kandidáta; nový kandidát po potvrzení; `L₀` po ENDED; reset kandidáta; sklon TL ≤ 0; remíza sklonů; neplatný kandidát aktuální TL; hystereze aktuální TL; `TL_BREAK` opakování; re-validace bez události; `H` při θ_pb < θ; hloubka pullbacku (close vs tělo); restart pullbacku po re-validaci (dvojí počítání v testu); remíza `direction`; pullback v baru `TREND_START`; interval korekce; `prev_major_low` u nového kandidáta; `H_final` bez potvrzeného swingu.
Metriky/PW: `dist_to_level` strana; `stopped_at_level`; `er` jmenovatel 0; `r2` kotvy; `n_swings`; `duration_min`; `tl_max_dev` okno a TL (P.A.T. VIII: aktuální TL); `levels_crossed`; `anchors_on_level`; `session_cross`/`gap`; PW1 okno a málo swingů; PW1 protistrana definice; PW3 studený start; `reversal_hint` s null; síla trendu (Ø1) chybí; `continuation_source` chybí.
Delta: vstupní formát, reset, divergence měření.
Rozhraní/chování: typy stavu; payloady událostí; serializace/snapshot; chyby a logování; složitost obálky; `min_slope` vliv na `trend_valid`; robustnost (dodatek 6); obecnost trhu (dodatek 10); metody detekce (dodatky 7, 8, 13); testy samostatné (dodatek 4); kalendář zpráv (dodatek 14, doplněn během kola).
Testy: syntetické scénáře bez kritérií; remíza cílů v jednom baru (13.4); PW3 index; 13.13 mapování časů.

### Drobné (11)

Odkaz 13.10 → 13.9 v sekci 1; chybějící log a historie; chybí `KONEC DOKUMENTU`; verze dokumentu; jednotné názvy parametrů (θ/`theta`, ε/`eps`, δ/`delta_dev`); okno kontroly timestampu (09:00–10:00 ET); formulace warmupu; kolize číslování 13.2.1 (brána vs. podsekce); duplicitní `warmup` v `Quality`; `price_conf` nedefinováno; `PULLBACK_END_DOWN` chyběl v seznamu událostí.

## Dodatek 14 (přibyl na konec souboru během kola)

Zapracován jako 3.9 (kalendář Forex Factory): rys pro D a členění reportu, detektor A nečte; Actual jen s `DateTime ≤ ts_open(t)`; překvapení z ≥ 12 minulých vydání; kontrola pásma Tehran → ET přes NFP / Unemployment Claims / FOMC. Původní text dodatku odstraněn z konce dokumentu (D-41, D-45).

## Co zkontrolovat v kole 2 (třetí průchod)

- 3.9: typy `ScheduledEvent` / `Release` (pole), chování `state.news` ve warmupu, snapshot poskytovatele, nesoulad názvů zpráv v čase (přejmenování událostí ve Forex Factory) → mapa aliasů nebo přijetí ztráty historie.
- 15.2: zarovnání B při `direction = NONE`; `se(reg_slope)` při n < 3.
- 13.13: převod časů CSV (SEČ/SELČ) na ET — definovat přes IANA `Europe/Prague`.
- 6.2 pseudokotvy: ověřit, že pseudokotva před `L₀`… nemůže vzniknout (scan jen `(t_L₀, t]`) — OK; ověřit interakci s `curr_tl` tolerancí.
- 7.4: `pb_low` u restartovaného pullbacku (počítá se od `t_H`, tj. zahrnuje původní) — potvrdit záměr.
- 10.3: `TrendLine.anchor1` u aktuální TL = starší z dvojice; `value_at` používá `anchor1.t` — sjednotit s 6.4 (`L₀.t` jen u hlavní).
- 12.2: formát anotačního CSV (sloupce) a kdo anotuje (uživatel) — dost konkrétní?
- 13.2 gate 6: očekávané chování u každého okrajového případu vypsat jako tabulku pass/fail.
- 8.3 `strength` při `curr_is_main` — složky použijí hlavní TL; OK.
- Kontrola, zda zadání SR (`komponenta-sr.md`) po své recenzi respektuje 3.5 (`level_id`, `valid_from` sémantika, `kind` výčet).
