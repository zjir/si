# TASK-0005 — stav po kole 2 (2026-10-01), dokumentové kolo 5

## Hotovo v kole 2

- Čistý průchod celým dokumentem (žádné dodatky zadavatele k zapracování). Nálezy před zapracováním 3 B / 13 S / 12 D, vše zapsáno do textu, log D-74 až D-79, historie řádek 5, hlavička „revize kolo 5“.
- **Blokující (D-74):** syntetické scénáře 13.2.5 byly nesplnitelné: generátor bez knotů dával `atr1 ≈ 0,5A` (prahy „3A“ neodpovídaly `θ × atr_ref`); S3 (+2A/−3,2A) tvořil nižší low → `TREND_END` a žádný kandidát aktuální TL; S5 (1,5A) potvrzoval swingy; S6 požadoval `pw3 = false`, ale ER20 sinusoidy s periodou 60 je < 0,25 jen ≈ 6 barů z 60; S7 (−6A) protínal `prev_major_low`; SR1 `|price − P| ≤ 1 tick` s náhodnými knoty. Nový generátor: knoty `n₃, n₄ ∈ [0,2A, 0,4A]`, těla `≤ 0,2A`, ceny na ticku, `volume = 100`, časová osa NQ/CME od 2020-01-06, cesta navazuje přes session, warmup s knoty 0,5A. S1 pullback −4A (`L_k = L₀ + 2kA`, `H_k = L_{k−1} + 6A`); S2 (DOWN `TREND_CANDIDATE` před koncem uptrendu); S3 = +5A/−4A; S4 = +9A/−4A; S5 = 0,6A; S6 = cesta `0 → 9A → 1A → 10A → −1A → …`; S7 = od `H₄` −5A/+4A/−3,5A + 20 plochých (souběh platných stran aspoň 1 bar, `direction = DOWN`); S9 s hranicí session; S10 i S6; S11a/b (PW3 trojúhelník ±0,7A perioda 8 kolem `L₀ + 5A`, bez úrovně `pw3 = false`, s úrovní `pw3 = true`); SR1 tři session s dotyky `P − 0,4A`.
- **Střední:** D-75 (TREND_START se `slope ≤ 0` → `TL_BREAK(NONPOSITIVE_SLOPE)` + řádek 7.5 CANDIDATE → TL_BROKEN; bez `TL_UPDATE` při `TREND_START`; `TL_UPDATE.reason` podle `anchor2`; náhrada curr TL jen `CURR_TL_NEW`; pořadí MAIN/CURR break; restart ⇔ stejné `t_H`; začátek pullbacku v baru nového maxima jen HIGH_FIRST; režim `close`); D-76 (D: roky, trénink `< y − 1`, první `y` 2015/2017, vzorek, purge, srovnávací C, soubor modelu, `ML_MODEL_MISMATCH`, `ml_enabled` mimo hash); D-77 (mřížky a hledání po souřadnicích 12.2, PW mřížky 12.3, posun prahů 8.3); D-78 (brány 13.2.1/2 a 13.14.1 ze snapshotu ≥ 10 session, každý 50. bod od začátku); 3.5 expirované úrovně; 3.1 `delta` NaN, `OUT_OF_SCOPE`, `BEFORE_FIRST_SESSION`; 3.2 `WINDOW` uvnitř session; 15.2 VR překrývající se výnosy.
- **Drobné (D-79):** 3.4 reasons `INTRABAR_MISMATCH`; 3.9 volání poskytovatele; 6.1.1 LL_SWING poznámka; 6.7 4d kandidát; 9 bez událostí a bez `min_slope`; 10.3 `updated_at`; 10.4 `event_id`, `t_known = 0` u varování z konstrukce; 11.4 `reset()`; 13.4 horizont „n session“, `H`/`prev_major_low` ze stavu v baru události; 13.11 šum těl; 13.12 agregace; 13.14.2 horizont; 15.2 `n_window`, okno do warmupu.

## Zbývá (kolo 3, pokud bude)

1. Druhý průchod nad novým textem kola 5: 13.2.5 generátor a tabulka S1–S11 (čísla ověřena ručně v kole 2: viz notes.md), SR1, 7.4 restart, 6.1.1 krok 2, 12.2 krok 3, 15.5, D-78.
2. Nenajde-li průchod nic blokujícího ani středního → `DONE`.

## Otevřené požadavky (mimo dokument, nebrání DONE)

- R5: smazat `zadani/komponenta-sr.md` (stále existuje), opravit odkazy v `zadani/testy.md` a `data/README.md` 10.
- R7: obnovit `data/NEWS/info.md` (v `data/NEWS/` jsou jen oba CSV).

## Rozhodnutí přijatá v kole 2 (shrnutí)

- Syntetika: ATR se řídí knoty, geometrie těly; čísla scénářů jsou v `A` při `atr_ref ≈ A`, závazný je referenční výpočet.
- Restart pullbacku je vlastnost `t_H`, ne okamžiku `TL_REVALIDATED`.
- `ml_enabled` nesmí měnit `params_hash` (tabulka C je náhrada D).
- Brány kauzality se smí provádět ze snapshotu (D-78, předpoklad).

## Co bylo zkoušeno a nefungovalo

- Read celého souboru najednou překračuje limit tokenů; číst po ≤ 420 řádcích (soubor má ≈ 1 480 řádků).
- Grep s cestou na adresář `data/NEWS` nic nenajde (CSV v `.gitignore`); `$` v Grepu nematchuje kvůli CRLF.
