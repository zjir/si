# Zadání: Testy komponenty detekce trendu a pullbacku

Verze 0.2 · po 1. kole recenze (TASK-0001) · dokument je psaný pro AI implementátora testů a AI testera, ne pro čtení člověkem

## 0. Kontext: obchodní systém P.A.T.

Vše v tomto zadání se dělá v kontextu obchodního systému P.A.T. a pro něj. Výsledek (testy komponent) bude použit výhradně v systému P.A.T., který se ve finále implementuje; jiné použití není a nenavrhuje se pro něj. Každé rozhodnutí se posuzuje podle toho, co potřebuje P.A.T.; rozpor se systémem P.A.T. je chyba zadání.

Podklady systému ve složce `PAT/` (závazné):

- `PAT/Popis OS P.A.T.pdf` — popis obchodního systému P.A.T.,
- `PAT/Obchodní deník.xls` — reálný obchodní deník s reálnými obchody,
- `PAT/obrazky-obchodu/` — obrázky jednotlivých obchodů.

## 1. Účel a rozsah

### 1.1 Předmět testu

- Předmětem testu je **výhradně komponenta detekce trendu a pullbacku** podle `zadani/komponenta-trend.md` (dále „komponenta“ a „zadání komponenty“; odkaz „K 6.2“ znamená sekci 6.2 zadání komponenty).
- Komponenta SR (`zadani/komponenta-sr.md`) předmětem testu **není**. Její testy budou samostatné zadání. Zde vystupuje jen jako jeden z možných poskytovatelů cenových úrovní (K 3.5); dokud neexistuje, nahrazuje ji testovací fixture mechanických úrovní (3.5) a varianta s SR úrovněmi se přeskakuje (14).
- Testují se všechna rozhraní, stavy, události a metriky komponenty podle K 10, chování podle K 11 a vlastnosti detekce podle K 13.

### 1.2 Co testy dokazují

Tři vrstvy, každá odpovídá na jinou otázku:

| Vrstva | Otázka | Zdroj pravdy | Sekce |
|---|---|---|---|
| A. Shoda s definicí | Dělá komponenta přesně to, co zadání komponenty (K 4–8, 10) říká? | orákulum (5) + syntetická data se známou konstrukcí (4.1) | 5, 6 (G7, G8), 7 |
| B. Vlastnosti | Nevidí do budoucnosti, replay, determinismus, invarianty, výkon (K 11) | matematické vlastnosti výstupů, bez referenčních dat | 6 (G1–G6, G9–G11), 8 |
| C. Užitečnost pro P.A.T. | Jsou stavy komponenty na reálných datech pravdivé, lepší než náhoda a přijatelné pro oko tradera? | pohled do budoucnosti (9), referenční hodnoty (10), vizuální audit (13) | 9–13, 15, 16 |

Otázka Ø1 ze zadání komponenty (K 15.5) se mapuje na výstupy a kontroly takto:

| Otázka Ø1 | Výstup komponenty | Kontroly |
|---|---|---|
| Jsem v trendu, jak silném? | `direction`, `trend_valid`, `quality.*`, `slope_norm_*` | S01, S02, S09, R-2, R-6, I-01 až I-12 |
| Začíná pullback? | `PULLBACK_START`, `phase = PULLBACK`, `pullback.*` | S03, S04, S14, R-3, R-4 |
| Bude trend pokračovat? | `trend_valid` + PW-SW (`pw1_*`, `pw2`, `pw3`, `reversal_hint`) | R-4, R-6, R-7, 12 |
| Detaily pro P.A.T. | `swings`, `main_tl`, `curr_tl`, `value_at`, `dist_to_*`, `stopped_at_level` | S01, S10, S11, 19 |

### 1.3 Vztah k zadání komponenty

- K 13 je souhrn testování; tento dokument je jeho závazná podrobná specifikace (K 15.4). Při rozporu platí pro testy tento dokument; rozpor se zapíše do rozhodovacího logu (21) a do poznámek kola jako podnět pro revizi zadání komponenty.
- Kde zadání komponenty mlčí nebo připouští dvě čtení, tento dokument volí jedno čtení (tabulka výkladů 5.1). Výklad je závazný pro orákulum i pro komponentu, dokud zadání komponenty neurčí jinak. Změna v zadání komponenty vyžaduje stejnou změnu orákula a zápis do logu.
- Data a syntetické scénáře se nesmí přizpůsobovat obchodnímu deníku ani obrázkům obchodů (K 15.9); deník vstupuje jen do informativní kontroly (16), která je ve výchozím stavu vypnutá.

### 1.4 Hotovo, když

1. Brány G1–G11 (6) mají výsledek PASS ve všech variantách úrovní (14), které jsou dostupné.
2. Report (11) je vygenerován ve formátu podle 11.5 a uložen jako referenční (`baseline`), pokud referenční ještě neexistuje.
3. Vizuální audit (13) proběhl aspoň jednou a zlatý vzorek (13.5) je uložen.
4. Kontroly stability (15) jsou v reportu, včetně variant, které se přeskočily pro chybějící data (s důvodem).

## 2. Pojmy, jednotky a konvence

| Pojem | Definice |
|---|---|
| bar | uzavřený 1min bar (nebo bar jiného TF) s poli `ts`, `open`, `high`, `low`, `close`, `volume`, volitelně `delta` |
| `t`, index baru | pořadové číslo baru v načtené řadě od 0, bez doplňování chybějících minut (K 4) |
| `ts` | čas **začátku** baru, tz-aware, America/New_York (ET). Loader (4.2.1) převádí z konvence zdroje; kontrola konvence 4.2.2 |
| tick | minimální krok ceny; NQ 0,25 bodu; parametr datové sady `tick` |
| bod | jednotka ceny trhu |
| `ticks(p)` | `round(p / tick)` jako celé číslo; všechna porovnání cen se dělají na `ticks(·)` |
| `atr1` | K 4: průměr true range posledních `atr_n` uzavřených barů včetně aktuálního; TR prvního baru = high − low; pro `t < atr_n − 1` je `atr1` null a komponenta je v zahřívání (3.1) |
| `hi_t`, `lo_t` | kotevní ceny baru podle `anchor_mode` (K 4): `body` → `max(open, close)`, `min(open, close)`; `wick` → `high`, `low`; `close` → `close`, `close` |
| θ, θ_pb, ε, δ | parametry K 12 v násobcích `atr1`; kanonická jména 3.1 |
| práh v bodech | `k × atr1` je reálné číslo; podmínka „rozdíl cen ≥ k × atr1“ se vyhodnocuje jako `(ticks(a) − ticks(b)) × tick ≥ k × atr1 − 1e-9` |
| session, obchodní den | podle kalendáře session (3.6): ETH začíná 18:00 ET předchozího kalendářního dne a končí 17:00 ET; RTH 09:30–16:00 ET (zkrácené dny 09:30–13:00 ET); obchodní den = datum konce RTH |
| směrové zarovnání | pravidla se píší pro uptrend; downtrend vzniká zrcadlením cen `p → −p` a záměnou `hi ↔ lo` (K 4). Orákulum takto zrcadlí vstup a spouští tentýž kód |
| pořadí uvnitř baru | předpoklad pro remízy bez 1s dat: bar s `close ≥ open` má pořadí O → L → H → C, bar s `close < open` pořadí O → H → L → C. S 1s daty se pořadí čte z 1s barů (uvnitř 1s baru platí týž předpoklad) |
| nedefinovaná hodnota | `null` (NaN u float, None u objektů). Nikdy 0, −1 ani prázdný řetězec |
| horizont „5 session“ | 5 následujících obchodních dnů podle kalendáře, tj. do konce ETH pátého obchodního dne po dni události |
| „konec téže session“ | 16:00 ET obchodního dne, do kterého bar události patří; pro bary po 16:00 ET (17:00 ET konec ETH i večerní bary od 18:00 ET) je to 16:00 ET **následujícího** obchodního dne |
| p.b. | procentní bod |
| PASS / FAIL / SKIP | výsledek brány; SKIP jen z důvodu uvedeného v 6 (chybějící volitelný vstup), nikdy pro chybu |

Konvence porovnání záznamů (používá G3–G6, G7):

```
equal_records(a, b):
  1. pole typu int, bool, string, enum, seznam int: shoda přesná
  2. pole typu float: |a − b| ≤ 1e-9 × max(1, |a|, |b|); null == null; null != číslo
  3. seznamy událostí: stejná délka a po dvojicích shoda podle 1 a 2
```

Důvod tolerance u float: dávkový a streamingový běh smí sčítat v jiném pořadí; rozdíl na úrovni 1e-9 není pohled do budoucnosti. Determinismus (G6) se měří hashem, tedy bitově.

## 3. Testované rozhraní (kontrakt komponenty pro testy)

Zadání komponenty (K 10, K 15.4) požaduje testovatelné rozhraní, ale nedefinuje jeho detail. Detail určuje tato sekce a je pro komponentu závazný.

### 3.1 Konstrukce, parametry, volání

```python
engine = TrendEngine(params, session_calendar, roll_dates, levels=None)
rec = engine.update(bar)              # streaming; vrací StateRecord pro uzavřený bar
evs = engine.pop_events()             # události vzniklé od minulého volání, v pořadí 5.4
records, events = engine.run(df)      # dávkově; DataFrame podle 3.2 a 3.3
engine.version                        # str: semver + krátký git hash, např. "0.3.0+a1b2c3d"
engine.params                         # dict: efektivní parametry včetně doplněných výchozích
engine.warmup_bars                    # int: počet úvodních barů bez výstupu, výchozí = atr_n
```

Kanonická jména parametrů (`params`); hodnoty a rozsahy podle K 12:

| Klíč | Význam | Výchozí |
|---|---|---|
| `anchor_mode` | body / wick / close | `body` |
| `atr_n` | okno ATR v barech | 30 |
| `theta` | θ zigzagu, násobek `atr1` | 3.0 |
| `theta_pb` | θ_pb pullbacku; `null` = rovno `theta` | `null` |
| `eps` | ε tolerance TL, násobek `atr1` | 0.5 |
| `curr_ratio_hi`, `curr_ratio_lo` | poměr sklonu pro novou aktuální TL | 1.5, 0.67 |
| `min_slope` | filtr sklonu, `null` = vypnuto | `null` |
| `pw1_n`, `pw1_counter` | PW1: počet swingů, počet protitrendových | 3, 2 |
| `pw2_delta` | δ | 3.0 |
| `pw3_w`, `pw3_er_n`, `pw3_er_thr`, `pw3_max_chop` | PW3 | 60, 20, 0.25, 30 |
| `level_tol` | tolerance „u úrovně“, násobek `atr1` | 0.5 |
| `levels_enabled` | použít vstup úrovní | `true` |
| `session_scope` | ETH / RTH | `ETH` |
| `delta_enabled` | modul 9 | `false` |
| `tick` | velikost ticku trhu | 0.25 |

Pravidla:

1. Neznámý klíč v `params` → výjimka `ValueError` při konstrukci (chrání před překlepem v kalibraci).
2. Hodnota mimo rozsah K 12 → výjimka `ValueError`; hranice rozsahu jsou povolené.
3. `bar` pro `update` je dict nebo objekt s atributy `ts, open, high, low, close, volume`, volitelně `delta`. `df` pro `run` má tytéž sloupce; index se ignoruje, pořadí řádků je pořadí barů.
4. Bar s `ts` ≤ `ts` předchozího baru → výjimka `ValueError` (nemonotónní vstup se nikdy tiše nepřeskakuje).
5. Bar s `high < max(open, close)`, `low > min(open, close)`, nebo cenou, která není násobkem `tick` (tolerance 1e-6 ticku) → výjimka `ValueError`.
6. Chybějící pole `volume` → hodnota 0 a varování v logu komponenty; chybějící `delta` při `delta_enabled = true` → výjimka.
7. Během zahřívání (`t < warmup_bars`) vrací `update` záznam s `atr1 = null`, `phase = NONE` na obou stranách, `direction = NONE`, bez událostí. Toto je požadavek testu na komponentu (K 13.2.6 zahřívání nedefinuje; předpoklad P-01 v 5.1).
8. `run(df)` musí vracet přesně to, co by vrátila posloupnost `update` (G5).

### 3.2 Záznam odhadu (StateRecord)

Jeden řádek na bar. Společná pole a pole pro každou stranu s prefixem `up_` a `down_`. Typy parquet: `int64`, `float64`, `bool`, `string`; seznamy indexů jako JSON řetězec (`"[12, 40, 71]"`). Nedefinovaná hodnota = null.

Společná pole:

| Pole | Typ | Obsah | Null, když |
|---|---|---|---|
| `bar_idx` | int64 | index baru `t` | nikdy |
| `ts` | timestamp[ns, tz=America/New_York] | začátek baru | nikdy |
| `atr1` | float64 | K 4 | zahřívání |
| `direction` | string | UP / DOWN / NONE (K 7) | nikdy |
| `levels_missing` | bool | K 3.5 | nikdy |
| `n_levels_active` | int64 | počet úrovní platných v `t` | nikdy (0 bez úrovní) |
| `gap_before_bars` | float64 | minuty mezi `ts` předchozího a tohoto baru minus délka baru; 0 = souvislé | první bar |
| `session_id` | string | obchodní den `YYYY-MM-DD` | nikdy |
| `is_rth` | bool | bar leží v RTH | nikdy |
| `is_roll_day` | bool | obchodní den je dnem rollu | nikdy (false bez dat rollu, viz 3.7) |

Pole strany (`up_` / `down_`), vždy ve směrově zarovnaných souřadnicích (K 4):

| Pole | Typ | Obsah | Null, když |
|---|---|---|---|
| `phase` | string | NONE / CANDIDATE / IMPULSE / PULLBACK / TL_BROKEN / ENDED | nikdy |
| `trend_valid` | bool | K 6.1, K 6.5 | nikdy |
| `L0_idx`, `L0_price` | int64, float64 | začátek trendu | phase ∈ {NONE} |
| `struct_low_idxs` | string (JSON seznam int64) | indexy strukturních swing low od `L0` včetně (5.3), poslední smí být provizorní | phase ∈ {NONE} |
| `struct_high_idxs` | string (JSON seznam int64) | indexy strukturních swing high `H_k` | phase ∈ {NONE, CANDIDATE bez H} |
| `last_swing_low_idx`, `last_swing_low_price` | int64, float64 | poslední potvrzený zigzag swing low (jakýkoli, i vnitřní) | žádný |
| `last_swing_high_idx`, `last_swing_high_price` | int64, float64 | totéž pro swing high | žádný |
| `n_swings_confirmed` | int64 | počet potvrzených zigzag swingů (obě strany sdílí zigzag; uvádí se pro kontrolu) | nikdy |
| `main_tl_x0`, `main_tl_y0`, `main_tl_slope` | int64, float64, float64 | hlavní TL: `y = y0 + slope × (x − x0)`, `x` = index baru, slope v bodech/bar | `trend_valid = false` a phase ∉ {TL_BROKEN} |
| `main_tl_anchor_idxs` | string (JSON) | kotvy hlavní TL: `L0` a koncová kotva obálky (5.3 krok 6) | jako výše |
| `main_tl_broken` | bool | K 6.5 | nikdy |
| `curr_tl_x0`, `curr_tl_y0`, `curr_tl_slope`, `curr_tl_anchor_idxs`, `curr_tl_broken` | jako hlavní TL | aktuální TL (K 6.3); pokud aktuální = hlavní, hodnoty shodné s hlavní a `curr_is_main = true` | jako hlavní |
| `curr_is_main` | bool | aktuální TL je totožná s hlavní | nikdy |
| `slope_norm_main`, `slope_norm_curr` | float64 | K 6.6, `atr1`/bar | TL chybí |
| `slope_ratio` | float64 | K 8.1 | TL chybí |
| `H_idx`, `H_price` | int64, float64 | běžící maximum `H` (5.3) | phase ∈ {NONE} |
| `pb_start_idx` | int64 | bar `PULLBACK_START` aktuálního pullbacku | phase ≠ PULLBACK |
| `pb_len` | int64 | `t − H_idx` | phase ≠ PULLBACK |
| `pb_inner_swings` | int64 | počet zigzag swingů s extrémem po `H_idx` potvrzených do `t` | phase ≠ PULLBACK |
| `pb_low_idx`, `pb_low_price` | int64, float64 | provizorní low pullbacku (5.3) | phase ≠ PULLBACK nebo dosud nepotvrzené |
| `dist_to_tl_main_atr`, `dist_to_tl_curr_atr` | float64 | `(close − TL(t)) / atr1` | TL chybí |
| `dist_to_level_atr` | float64 | K 7: vzdálenost close k nejbližší úrovni **pod** close (uptrend), v `atr1` | žádná úroveň pod close nebo `levels_missing` |
| `stopped_at_level` | bool | K 7: `pb_low` je v toleranci `level_tol` od některé úrovně | `levels_missing` nebo `pb_low` null |
| `er`, `r2`, `n_swings`, `duration_bars`, `duration_min`, `tl_max_dev_atr`, `levels_crossed`, `dist_to_next_level_atr`, `anchors_on_level`, `L0_on_level`, `session_cross`, `roll_in_structure`, `gap_in_structure` | podle K 8.1 | metriky kvality, definice 5.6 | `trend_valid = false`; úrovňové navíc při `levels_missing`; `r2` při < 3 kotvách; `roll_in_structure` bez dat rollu |
| `pw1_trend_side`, `pw1_counter_side`, `pw2`, `pw3`, `reversal_hint` | bool | K 8.2, definice 5.7 | `trend_valid = false`; `pw1_trend_side` při < `pw1_n` swing low; `pw1_counter_side` mimo PULLBACK; `reversal_hint` pokud kterýkoli vstup null |
| `chop_bars` | int64 | K 8.2 | `t < pw3_w − 1 + pw3_er_n` |
| `tl_tolerance_violations` | int64 | počet barů mezi kotvami hlavní TL, jejichž tělo podkročilo TL o více než ε (diagnostika, 5.1 P-05) | TL chybí |
| `delta_tl_agrees`, `delta_divergence` | bool | K 9 | `delta_enabled = false` nebo den rollu |

### 3.3 Záznam události (EventRecord)

| Pole | Typ | Obsah |
|---|---|---|
| `event_type` | string | SWING_CONFIRMED, TREND_START, TL_UPDATE, CURR_TL_NEW, PULLBACK_START, PULLBACK_END_UP, TL_BREAK, TREND_END |
| `side` | string | UP / DOWN pro události trendu; `NONE` u SWING_CONFIRMED (zigzag je jeden pro obě strany, typ swingu je v `detail.kind ∈ {HIGH, LOW}`) |
| `known_idx`, `known_ts` | int64, timestamp | bar, ve kterém byla událost známa (K 10) |
| `ref_idx`, `ref_ts` | int64, timestamp | bar, ke kterému se vztahuje (extrém swingu, `H` u pullbacku, `L0` u TREND_START, bar prolomení u TL_BREAK a TREND_END) |
| `price` | float64 | cena extrému / úroveň TL v baru prolomení / close u TREND_END |
| `tl_kind` | string | MAIN / CURR u TL_UPDATE, CURR_TL_NEW, TL_BREAK; jinak null |
| `seq` | int64 | pořadí uvnitř baru od 0 podle 5.4 |
| `detail` | string (JSON) | doplňky: `kind` swingu, `reason` u TREND_END (`STRUCTURE_BREAK` / `SEQUENCE_VIOLATION`), `anchors` u TL_UPDATE, `slope` |

`PULLBACK_END_UP` je název události pro obě strany (K 7); u downtrendu znamená nové minimum pod `H` v zrcadlených souřadnicích.

### 3.4 Serializace a hash

- `records` a `events` se ukládají do parquet se schématem `schemas/state_v1.json` a `schemas/events_v1.json` (součást testovacího balíku; G1 ověřuje shodu sloupců a typů).
- Hash běhu = SHA-256 nad kanonickým CSV: sloupce v pořadí schématu, float jako nejkratší round-trip `repr`, null jako `null`, řádky v pořadí `bar_idx` (u událostí `known_idx`, `seq`). Hash se zapisuje do reportu.

### 3.5 Poskytovatel úrovní pro testy (fixture mechanických úrovní)

Komponenta úrovně nepočítá (K 3.5, K 14). Testy potřebují poskytovatele; do vzniku komponenty SR ho nahrazuje fixture `MechanicalLevels`, které z barů a kalendáře session (3.6) odvozuje jen mechanické úrovně bez diskrece. Rozhraní poskytovatele: `levels.active_at(t) -> list[Level]` s poli K 3.5 (`price, kind, valid_from, valid_to, strength, source`).

| `kind` | Cena | `valid_from` (index baru) | `valid_to` |
|---|---|---|---|
| `PDH`, `PDL` | high / low RTH barů obchodního dne D (high = max `high`, low = min `low`) | první bar s `ts ≥ 16:00 ET` dne D (tj. hned po konci RTH) | poslední bar před 16:00 ET obchodního dne D+1 |
| `PDO` | `open` prvního RTH baru dne D | jako PDH | jako PDH |
| `PDC` | `close` posledního RTH baru dne D (u zkráceného dne poslední bar před 13:00 ET) | jako PDH | jako PDH |
| `PREMARKET_H`, `PREMARKET_L` | max `high` / min `low` barů od začátku ETH dne D+1 (18:00 ET dne D) do posledního baru před 09:30 ET dne D+1 | bar 09:30 ET dne D+1 | poslední bar před 16:00 ET dne D+1 |
| `SESSION_OPEN` | `open` baru 09:30 ET dne D+1 | bar 09:30 ET dne D+1 | poslední bar před 16:00 ET dne D+1 |
| `SR` | fixture neposkytuje; dodá komponenta SR (14) | | |

Pravidla:

1. `strength = null`, `source = "fixture-mechanical-v1"`.
2. Chybí-li RTH bary dne D (svátek s jen ETH obchodováním), PD* se odvozují z posledního obchodního dne, který RTH bary má; report uvádí počet takových dnů.
3. Chybí-li bary premarketu (halt, mezera), PREMARKET_* se odvozují z dostupných barů; není-li žádný, úroveň se nevydá.
4. Fixture čte jen bary s indexem < `valid_from`; nikdy pozdější (acyklicita K 3.5). G4 (změna budoucnosti) to ověřuje i pro fixture.
5. Pro syntetická data se úrovně definují ve scénáři explicitně (7); fixture se na syntetická data použije jen tam, kde to scénář uvádí.
6. Poskytovatel se stejnými pravidly musí dávat stejný výstup při dávkovém i streamingovém běhu (fixture se testuje týmiž branami G3–G6 jako komponenta, přes výstup `n_levels_active`).

### 3.6 Kalendář session pro testy

- Vstup: `data/session_calendar.csv` se sloupci `trading_day` (YYYY-MM-DD), `eth_start`, `rth_start`, `rth_end`, `eth_end` (ISO 8601 s posunem, ET). Dodává datová vrstva (K 3).
- **Náhradní postup**, chybí-li soubor: kalendář se odvodí z dat a report nastaví `calendar_derived = true`:
  1. Obchodní den baru = kalendářní datum `ts + 6 h` v ET (bary od 18:00 ET spadají do následujícího dne).
  2. `eth_start` = `ts` prvního baru dne, `eth_end` = `ts` posledního baru dne + délka baru.
  3. `rth_start` = 09:30 ET; `rth_end` = 16:00 ET, pokud existuje bar s `ts` v [15:55, 16:00) ET; jinak 13:00 ET, pokud existuje bar v [12:55, 13:00) ET; jinak den nemá RTH (`rth_start = rth_end = null`).
  4. Dny bez barů se v kalendáři nevyskytují (víkendy, svátky).
- Pro syntetická data generátor kalendář vytváří spolu s bary.

### 3.7 Data rollu pro testy

- Vstup: `data/roll_dates.csv` se sloupcem `trading_day`; z nastavení rolloveru exportu (K 3). Chybí-li, `is_roll_day = false` všude, `roll_in_structure = null` všude, report `roll_dates_missing = true` a `requests` obsahuje požadavek na soubor. Kontroly, které den rollu potřebují (S21 na reálných datech, členění 11.4), se přeskočí se SKIP.

### 3.8 Co komponenta nesmí

- Číst z `df` nic za aktuálním barem při `run` (G3, G4).
- Měnit již vrácené záznamy (G5 porovnává záznam vrácený z `update` s řádkem z `run`; oba musí být hodnotově shodné, i když komponenta interně přepisuje provizorní low pullbacku, mění se jen budoucí záznamy).
- Používat systémový čas, náhodná čísla, pořadí iterace dictů bez řazení, nebo síť (G6 spouští dvakrát v různých procesech s jiným `PYTHONHASHSEED`).

## 4. Testovací data

### 4.1 Syntetická data

Důvod (dodatek 2 zadavatele): jen u syntetických dat je pravda plně pod kontrolou; každý bar vznikl z návrhu, který známe.

#### 4.1.1 Principy

1. Generátor `SyntheticScenario(spec, seed)` je deterministický: stejný `spec` a `seed` dávají bitově stejné bary. PRNG = `numpy.random.default_rng(seed)`; pořadí odběrů je pevné (pro každý bar: šum close, horní knot, dolní knot).
2. Scénář = posloupnost segmentů (4.1.2). Každý segment určuje **páteř** `m_t` (cílový close bez šumu, v bodech) a případně změnu času nebo úrovní.
3. Jednotka velikostí je `R` (bodů) = základní rozpětí baru. Výchozí `R = 8.0`, `tick = 0.25`, `p0 = 15000.0`. Všechny velikosti ve scénářích jsou násobky `R`, takže scénář platí pro libovolné měřítko. Každý scénář se spouští pro `R ∈ {2, 8, 40}` (test nezávislosti na měřítku trhu, K 15.6 a K 15.10) a musí projít ve všech třech.
4. Výchozí kalendář: jen RTH dny (09:30–16:00 ET, 390 barů), po sobě jdoucí pracovní dny od pondělí 2020-01-06. Segmenty mohou pokračovat přes hranici dne; hranice dne je hranice session, ne mezera v datech. Noční a víkendové mezery, halty a den rollu vkládají jen segmenty, které to říkají.
5. Pravda má dvě vrstvy (4.1.5): návrhová (z páteře, s okny tolerance) a přesná (orákulum 5).
6. Scénář je platný, jen když splní podmínky odstupu 4.1.6; jinak jde o chybu testovací sady (ERROR), ne komponenty.

#### 4.1.2 Segmenty

| Segment | Parametry | Páteř a účinek |
|---|---|---|
| `LEG(n, s)` | `n` barů, sklon `s` v R/bar (záporný = dolů) | `m_t = m_{t−1} + s × R` |
| `FLAT(n)` | `n` barů | `m_t = m_{t−1}` |
| `CHOP(n, A=0.3, P=8)` | `n` barů, amplituda `A` v R, perioda `P` barů | pilovitá páteř: `m_t = m_base + A × R × tri(t)`, `tri` trojúhelníkový signál v rozsahu [−1, 1] s periodou `P`; `m_base` = páteř na začátku segmentu |
| `GAP(g)` | skok `g` v R | žádný bar; páteř i `open` následujícího baru se posunou o `g × R` (`open ≠ close_prev`) |
| `HALT(minutes)` | minuty | žádný bar; časový kurzor skočí o `minutes` uvnitř session (mezera v datech) |
| `NIGHT()` | — | žádný bar; kurzor skočí na 18:00 ET téhož dne a od té chvíle se generují i ETH bary až do 17:00 ET dalšího dne (kalendář se přepne na ETH pro zbytek scénáře) |
| `WEEKEND()` | — | kurzor skočí z pátku 17:00 ET na neděli 18:00 ET (vyžaduje, aby kurzor byl v pátek; generátor jinak vyhodí chybu) |
| `WICK(side, len)` | `side ∈ {HIGH, LOW}`, `len` v R | jeden bar s normálním tělem, jehož knot na straně `side` je prodloužen o `len × R` |
| `ROLL()` | — | následující obchodní den je v `roll_dates`; první bar dne má `open = close_prev + 1 × R` (zbytkový skok spojité řady) |
| `NOISE(a, w)` | amplituda šumu close `a` v R, měřítko knotů `w` v R | platí pro následující segmenty; výchozí `a = 0.15`, `w = 0.2`; `a = w = 0` = přesná geometrie |
| `LEVEL(kind, y, from, to)` | `kind` podle K 3.5, `y` v R vůči `p0`, `from`/`to` indexy barů nebo `"start"`/`"end"` | úroveň `price = p0 + y × R` platná v [from, to] |
| `MECH_LEVELS()` | — | scénář navíc použije fixture 3.5 nad vlastními bary |
| `DELTA(scale, mode)` | `scale` násobek, `mode ∈ {AGREE, DIVERGE_LOW, DIVERGE_HIGH}` | generuje kumulativní deltu: `AGREE` = páteř × scale + vlastní šum; `DIVERGE_LOW` = při posledním navrženém HL ceny delta udělá LL; `DIVERGE_HIGH` zrcadlově |

#### 4.1.3 Generování barů

```
1. t = 0; c_prev = p0; m = p0; kurzor = 2020-01-06 09:30 ET; a = 0.15; w = 0.2
2. pro každý segment a každý jeho bar:
   a. m = páteř segmentu pro tento bar (4.1.2)
   b. n_c = U(−a, a) × R;  close_raw = m + n_c
   c. open = c_prev  (po GAP(g): open = c_prev + g × R; po ROLL: open = c_prev + 1 × R)
   d. u = U(0, 1); v = U(0, 1)
      high_raw = max(open, close_raw) + u × w × R
      low_raw  = min(open, close_raw) − v × w × R
   e. WICK(side, len): high_raw += len × R (HIGH) nebo low_raw −= len × R (LOW)
   f. zaokrouhlení na tick: p = round(p / tick) × tick pro open, high, low, close
      (round je monotónní, takže high ≥ max(open, close) a low ≤ min(open, close) zůstává)
   g. volume = 100 + round(50 × |close − open| / R); bar 09:30 ET navíc × 5
      (aby kontrola časového pásma 4.2.2 platila i na syntetických datech)
   h. ts = kurzor; kurzor += 1 min; po baru 15:59 ET kurzor skočí na 09:30 ET
      dalšího pracovního dne (v režimu ETH po NIGHT(): po 16:59 ET na 18:00 ET)
   i. c_prev = close; t += 1
3. zapiš návrhovou pravdu (4.1.5), kalendář session (3.6), roll_dates (3.7), úrovně (LEVEL)
```

#### 4.1.4 Šum

- Šum close je `U(−a, a) × R`, knoty `U(0, 1) × w × R`. S výchozími `a = 0.15`, `w = 0.2` je největší zvrat tělem uvnitř šumu ≤ `2a × R = 0.3 R`, v režimu `wick` ≤ `0.3 R + 2 × 0.2 R = 0.7 R`.
- Realizované `atr1` (z orákula) leží u plochých úseků kolem `0.3 R`, u ramen se sklonem `0.5 R/bar` kolem `0.7 R`. Práh zigzagu θ × `atr1` je tedy 0,9 R až 2,1 R; návrhové zvraty ve scénářích mají hloubku ≥ 5 R, šumové ≤ 0,7 R.

#### 4.1.5 Pravda

**Vrstva 1, návrhová pravda** (z páteře; generátor ji ukládá do `truth.json` scénáře):

- `designed_swings`: lokální extrémy páteře (index, cena páteře, typ HIGH/LOW). Extrém = bar, kde se znaménko sklonu páteře mění; u plochého úseku (`FLAT`, `CHOP`) se za extrém bere první bar úseku pro vstupní směr a poslední bar pro výstupní směr, jen pokud se směr před a po úseku liší.
- `designed_pullbacks`: dvojice (swing high `H_i`, následující swing low `L_i`) uvnitř navrženého uptrendu, tj. tam, kde po `L_i` páteř překoná `H_i`; zrcadlově pro downtrend.
- `designed_phases`: pro každý bar fáze podle návrhu (NONE / CANDIDATE / IMPULSE / PULLBACK / TL_BROKEN / ENDED / ANY) a směr; `ANY` = bar leží v přechodovém okně (4.1.5 okna), kde se fáze nekontroluje.
- `designed_events`: očekávané události s referenčním barem `t_ref` a oknem pro `known_idx` (níže).
- `designed_absent`: co se nesmí stát (např. „žádný `TL_BREAK` hlavní TL“, „žádný `TREND_END`“).

**Okna pro `known_idx`** (počítá harness z realizovaného `atr_min`, `atr_max` scénáře po zahřívání, sklon `s` v R/bar z páteře segmentu, který následuje po extrému):

| Událost | Dolní mez | Horní mez |
|---|---|---|
| SWING_CONFIRMED pro navržený extrém v `t_ref` | `t_ref + floor(θ × atr_min / (|s| × R)) − 1` | `t_ref + ceil(θ × atr_max / (|s| × R)) + 2` |
| PULLBACK_START (θ_pb = θ) | jako SWING_CONFIRMED pro `H_i` | totéž |
| TREND_START | okno SWING_CONFIRMED pro první navržený HL | totéž |
| PULLBACK_END_UP | první bar, kde `páteř > H_i + 0.3 R` − 1 | tentýž bar + 1 |
| TL_BREAK / TREND_END | první bar, kde `páteř < práh − 0.3 R` − 1 | první bar, kde `páteř < práh − 0.3 R` + 1; práh = navržená TL − ε × atr_max, resp. navržené poslední low |

Přechodové okno fáze = sjednocení oken událostí, které fázi mění; uvnitř okna je `designed_phase = ANY`.

**Vrstva 2, přesná pravda** = výstup orákula (5) nad vygenerovanými bary; G7 porovnává komponentu s orákulem funkcí `equal_records`.

**Vzájemná kontrola:** orákulum musí samo splnit vrstvu 1 na každém scénáři. Nesplní-li, jde o chybu orákula nebo scénáře (ERROR), nikdy o PASS komponenty.

#### 4.1.6 Podmínky odstupu (platnost scénáře)

Harness spočítá `atr_min`, `atr_max` = minimum a maximum `atr1` orákula po zahřívání a ověří:

1. Každý navržený zvrat (rozdíl páteře mezi sousedními navrženými extrémy) je ≥ `1.5 × θ × atr_max`.
2. V každém úseku bez navrženého extrému (šum, `FLAT`, `CHOP`) je největší zvrat řady `hi_t`/`lo_t` ≤ `0.75 × θ × atr_min`.
3. Navržená TL (přímka navrženými low) není podkročena těly barů mezi kotvami o více než `0.5 × ε × atr_min` mimo scénáře, které to záměrně dělají (S12, S13).

Nesplnění = `scenario_valid = false`, výsledek ERROR, scénář se musí přepracovat (většinou zvětšit hloubku zvratu nebo zmenšit šum).

### 4.2 Reálná data

Důvod (dodatek 3 zadavatele): komponenta musí obstát na skutečném trhu, kde ale nejsou označené správné situace. Jak se s tím test vyrovnává, říká 4.2.4.

#### 4.2.1 Zdroje a formát

| Sada | Soubor | Povinná | Použití |
|---|---|---|---|
| NQ 1min ETH, spojitá řada (NinjaTrader, Merge back adjusted) | `data/nq_1min_eth.parquet` | ano | všechny brány a kontroly |
| NQ 1s ETH | `data/nq_1s_eth.parquet` | ne | pořadí uvnitř baru (9.4), audit (13), G11 varianta TF |
| ES, YM 1min ETH | `data/es_1min_eth.parquet`, `data/ym_1min_eth.parquet` | ne | stabilita napříč trhy (15) |
| kalendář session | `data/session_calendar.csv` | ne (náhradní postup 3.6) | |
| data rollu | `data/roll_dates.csv` | ne (3.7) | |

- Loader `load_bars(path, ts_convention)` přijme parquet nebo textový export NinjaTraderu (`yyyyMMdd HHmmss;open;high;low;close;volume`, čas v časovém pásmu exportu, parametr `source_tz`). Převádí na `ts` = začátek baru v ET; `ts_convention ∈ {start, end}` říká, co zdroj ukládá (u konce baru se odečte délka baru). Konvence zdroje je **neověřená**; rozhoduje kontrola 4.2.2 bod 6 a loader při neshodě skončí chybou s doporučením druhé konvence.
- Hash souboru (SHA-256) se zapisuje do reportu; metriky jsou vázané na hash dat.
- 1s data komponenta v 1min testech nikdy nedostane; slouží jen testu (K 15.2 připouští 1s pro jemnou detekci uvnitř komponenty; to je věc komponenty, ne tohoto zadání, a testuje se jen jako varianta vstupu v G11).

#### 4.2.2 Validace dat (před každým během; nesplnění = DATA_ERROR, testy se nespustí)

1. `ts` ostře rostoucí; duplicita = chyba.
2. `low ≤ min(open, close) ≤ max(open, close) ≤ high`; všechny ceny násobky `tick` (tolerance 1e-6 ticku); `volume ≥ 0` celé číslo.
3. Bary mimo ETH podle kalendáře (3.6): zahodí se, počet do reportu; nad 0,1 % barů = chyba.
4. Skok `|close_t − close_{t−1}| > 5 % × close_{t−1}`: chyba (i den rollu má u back-adjusted řady skok malý).
5. Mezery uvnitř session: seznam a počet mezer ≥ 5 min (informace pro `gap_in_structure`); mezera > 120 min uvnitř RTH = halt, do reportu.
6. Kontrola časového pásma a konvence `ts`: pro každý obchodní den s RTH bar s největším objemem v [09:25, 09:35) ET musí být bar 09:30 ET v ≥ 95 % dnů. Jinak chyba „posun času nebo špatná konvence `ts`“.
7. Pokrytí: počet obchodních dnů na rok do reportu; rok s < 200 dny = varování.
8. Výstup: `data_report.json` (počty, mezery, halty, hash, konvence, `calendar_derived`, `roll_dates_missing`).

#### 4.2.3 Období

- Rozdělení chronologicky **před prvním během**: vývojové = 2007-01-01 až 2018-12-31, testovací = 2019-01-01 až konec dat (K 13.3). Je-li historie kratší, dělicí datum = první obchodní den roku, ve kterém kumulativní podíl obchodních dnů poprvé překročí 70 %; report uvádí skutečné datum.
- Zmrazení parametrů: první vyhodnocení testovacího období zapíše `params_frozen.json` (efektivní parametry + hash). Každé další vyhodnocení testovacího období s jiným hashem nastaví `test_period_contaminated = true` s datem a od té chvíle se testovací období v reportu označuje jako vývojové (K 13.3).
- Rychlá sada používá `sample_20d`: 20 obchodních dnů z vývojového období, 4 z každého roku {2008, 2010, 2012, 2014, 2016}, vybrané jednou generátorem `default_rng(20260925)` rovnoměrně z obchodních dnů roku a uložené v `tests/config/sample_days.json` (soubor je součást repozitáře, nemění se).

#### 4.2.4 Absence označených referenčních situací

Na reálných datech nikdo neoznačil „správný“ trend ani pullback. Test to nahrazuje šesti zdroji pravdy, každý s jinou silou:

| Zdroj | Co dokazuje | Sekce | Charakter |
|---|---|---|---|
| 1. Vlastnosti výstupu (zkrácení, změna budoucnosti, replay, determinismus, invarianty) | komponenta nepodvádí a je vnitřně konzistentní | 6 (G3–G6), 8 | brána |
| 2. Shoda s orákulem na reálných datech | komponenta implementuje definici zadání komponenty i na datech, která návrhář scénářů nevymyslel | 6 (G8) | brána |
| 3. Pohled do budoucnosti | stavy komponenty se v budoucnu potvrdily (pullback obnovil, trend pokračoval) | 9 | metrika |
| 4. Referenční hodnoty náhody | úspěšnost není jen geometrie a drift | 10 | metrika |
| 5. Lidské označení vzorku (vizuální audit) a zlatý vzorek | shoda s okem tradera P.A.T.; vzorek roste s každým auditem a slouží jako regresní sada | 13 | metrika, po nasbírání ≥ 150 označení soft brána (13.5) |
| 6. Obchodní deník a obrázky obchodů | kladné příklady situací, které autor systému obchodoval | 16 | informativní, vypnuto (K 3.6, K 13.9) |

Zdroje 3–5 nemají pevné cílové hodnoty (K 13.10); první běh stanoví referenci, další verze se porovnávají s ní (11.6).

KONEC DOKUMENTU
