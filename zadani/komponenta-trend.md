# Zadání: Komponenta detekce trendu a pullbacku (pro obchodní systém P.A.T.)

## 0. Kontext: obchodní systém P.A.T.

Vše v tomto zadání se dělá v kontextu obchodního systému P.A.T. a pro něj. Výsledek (komponenta detekce trendu a pullbacku) bude použit výhradně v systému P.A.T., který se ve finále implementuje; jiné použití není a nenavrhuje se pro něj. Každé rozhodnutí se posuzuje podle toho, co potřebuje P.A.T.; rozpor se systémem P.A.T. je chyba zadání.

Podklady systému ve složce `PAT/` (závazné):

- `PAT/Popis OS P.A.T.pdf` — popis obchodního systému P.A.T.,
- `PAT/Obchodní deník.xls` — reálný obchodní deník s reálnými obchody,
- `PAT/obrazky-obchodu/` — obrázky jednotlivých obchodů.

## 1. Účel a rozsah

Komponenta (knihovna) zpracovává proud minutových barů a v každém okamžiku, bez pohledu do budoucnosti, určuje:

1. zda je trh v trendu (nahoru / dolů / žádný), podle swingů a trendline (TL),
2. hlavní a aktuální TL jako čáru s kotvami a projekcí do budoucna,
3. zda je trh v pullbacku v rámci trendu, nebo zda byl trend prolomen,
4. metriky kvality trendu včetně filtrů PW-SW.

Komponenta **přijímá cenové úrovně jako vstup** (3.5): S/R, OHLC minulého dne, premarket. Úrovně mění klasifikaci pullbacku, kotvení TL, stáří trendu i váhu prolomení a bez nich nelze rozlišit chop od zdržení na úrovni, jak vyžaduje PW-SW 3. Komponenta ale **musí fungovat i s prázdným seznamem úrovní**, jen s horší kvalitou; rozdíl mezi během s úrovněmi a bez nich se měří (13.10).

Komponenta **neřeší**: výpočet S/R úrovní (jen je přijímá), vstupní zóny, profit target, stop-loss, vstup, výstup, velikost pozice, vzdálenosti ceny ke swingům ani obchodní výsledek systému. Tyto části systému P.A.T. komponentu používají jako vstup (viz 2). Součástí zadání je test správnosti detekce na historických datech (13).

## 2. Požadavky systému P.A.T. na komponentu

| Část P.A.T. | Požadavek systému | Výstup komponenty | Poznámka |
|---|---|---|---|
| I.3 Hlavní trend | uptrend určuje TL přes swing low, downtrend TL přes swing high; dlouhé knoty se ignorují | `main_tl`, `anchor_mode = body` | 6.2, 4 |
| Pravidlo 1 | long jen v jasném uptrendu, short jen v jasném downtrendu (určeném TL) | `trend_valid`, `direction` | jasný = TL existuje (≥ 2 swing low) a není prolomená |
| I.4 Aktuální trend | nová TL při strmějším nebo pozvolnějším pokračování; průběžné překreslování během seance | `curr_tl`, události `CURR_TL_NEW`, `TL_UPDATE` | 6.3 |
| Pravidlo 2 | vynechat trendy se sklonem pod 45° | `slope_norm` + volitelný filtr `min_slope` | úhel bez měřítka grafu není definován, 6.6 |
| I.5, I.6 Vstupní zóny A/B/C | křížení hlavní / aktuální TL s OHLC minulého dne a S/R | `value_at(x)` hlavní i aktuální TL | křížení počítá spotřebitel |
| II Zóna pozornosti | korekce, která se blíží ke vstupní zóně | `phase = PULLBACK`, `dist_to_tl_atr`, `dist_to_level_atr` | 7 |
| III PT:A, IV SL:A | high / low minulého swingu | seznam potvrzených swingů | vzdálenosti počítá spotřebitel |
| IV SL:B | úroveň TL aktuálního trendu | `curr_tl.value_at(x)` | |
| VI OUT:B | výstup při překročení TL | událost `TL_BREAK` | 6.5 |
| VIII PW-SW 1 | swingy v souladu s trendem, bez protitrendové struktury | `pw1_trend_side`, `pw1_counter_side` | část je interpretace, 8.2 |
| VIII PW-SW 2 | trh stále poblíž TL | `tl_max_dev_atr`, `pw2` | 8.2 |
| VIII PW-SW 3 | žádný chop před vstupní zónou; krátké zdržení na S/R chop není | `chop_bars`, `pw3`; vyloučení barů u úrovně | 8.2, vyžaduje vstup úrovní 3.5 |
| VIII souhrn | náznak otočení trendu | `reversal_hint` | 8.2 |
| IX Cumulative delta | TL a swingy na deltě v souladu s cenou | modul 9 | volitelný, vyžaduje bid/ask data |
| Obecně | TF 1 min (i vyšší), NQ (i ES, YM); TL se kreslí průběžně | streaming API, prahy v ATR | 10, 11 |

## 3. Vstupy

- **Bary:** timestamp (tz-aware, převod do America/New_York), OHLC, objem. Primárně 1min NQ, ETH, spojitá řada (export NinjaTrader, Merge back adjusted). Jiné TF a trhy musí fungovat bez změny kódu.
- **Kalendář session** (začátek a konec session, RTH) jako vstup. Komponenta rozvrh CME nezná ani neodvozuje; rozvrh se v historii několikrát měnil a jeho správnost je odpovědnost datové vrstvy.
- **Data rollu** z exportu (nastavení rolloveru v NinjaTraderu), ne z kalendáře expirací; spojitá řada mění kontrakt jindy než v týdnu expirace.
- **Volitelně:** kumulativní delta na bar (modul 9).
- **Předpoklad z datové vrstvy:** ověřené časové pásmo timestampů (např. skok objemu při otevření RTH v 9:30 ET padá do očekávané minuty).

### 3.5 Cenové úrovně (vstup, volitelný)

Úrovně dodává poskytovatel za rozhraním; komponenta je nepočítá.

| Pole | Popis |
|---|---|
| `price` | cena úrovně |
| `kind` | `PDH`, `PDL`, `PDO`, `PDC`, `PREMARKET_H`, `PREMARKET_L`, `SESSION_OPEN`, `SR` |
| `valid_from` | bar, od kterého je úroveň známa (nikdy dřív, než vznikla) |
| `valid_to` | konec platnosti, nebo prázdné |
| `strength` | volitelná síla 0–1; prázdné = neznámá |
| `source` | identifikace poskytovatele |

- **Dvě třídy úrovní za týmž rozhraním.** Mechanické (OHLC předchozího dne, premarket high a low, open seance) jsou bez diskrece a dostupné hned. Skutečné S/R (shluky swingů, opakovaně testované hladiny) jsou samostatná úloha a doplní se později jako druhá implementace.
- **Acyklicita:** poskytovatel nesmí číst výstupy této komponenty. Odvozené úrovně smí vycházet jen z uzavřených předchozích seancí, jinak vzniká smyčka a pohled do budoucnosti.
- **Bez úrovní:** prázdný seznam je platný vstup. Metriky závislé na úrovních jsou pak nedefinované (indikátor `levels_missing`) a `pw3` se počítá bez vyloučení barů u úrovně.
- **Tolerance „na úrovni“:** cena je u úrovně, pokud je vzdálenost ≤ `level_tol` × `atr1` (12).

### 3.6 Obchodní deník autora (podklad, mimo běh komponenty)

K dispozici je obchodní deník autora systému: 597 obchodů z let 2010 až 2014, trh NQ, sloupce datum, čas, kontrakt, směr, vstup, SL, SL v ticích, PT, PT v ticích, RRR, MAE, MFE a P/L. Ověřeno proti záznamu z chartbooku ze 7. 3. 2014, hodnoty sedí.

Co je to za data: **reálná rozhodnutí člověka**, tedy okamžiky, ve kterých autor viděl platný trend daného směru a pullback ve vstupní zóně. Z hodnot lze zpětně odvodit i polohu struktury, kterou viděl: u SL typu A leží stop tick pod posledním swing low, u PT typu A tick pod předchozím swing high, u PT typu B a C a SL typu B leží cíl nebo stop na úrovni, kterou autor považoval za S/R.

Omezení: deník neříká, kudy vedla trendline, a obsahuje jen kladné příklady; kde autor neobchodoval, nevíme, zda trend nebyl, nebo jen nevstoupil. Typ vstupní zóny, PT a SL je jen v chartboocích, ne v deníku.

**Způsob využití zatím není rozhodnut** (kalibrace parametrů, kontrola v testech, nebo jen orientační podklad). Dokud rozhodnutí nepadne, deník do běhu komponenty ani do jejích testů nevstupuje.

## 4. Normalizace a osy

- **ATR:** `atr1` = průměrný true range posledních 30 dokončených barů včetně aktuálního uzavřeného. Všechny prahy a metriky jsou v násobcích `atr1`. Důvod: systém pracuje se swingy o velikosti jednotek bodů na 1min grafu; denní ATR je o řád hrubší.
- **Osa x** = pořadové číslo baru v řadě tak, jak ji zobrazuje graf (bez doplňování prázdných minut). Sklon = cena / bar. Odpovídá tomu, jak trader kreslí TL na grafu; u 1min barů v RTH totožné s cenou za minutu.
- **Směrové zarovnání:** všechny metriky se vrací v souřadnicích směru trendu (u downtrendu × −1). Kladná hodnota znamená „ve prospěch trendu“ u long i short, takže výstupy obou směrů jsou přímo srovnatelné.
- **Režim kotev** `anchor_mode`: `body` (výchozí; extrém baru = min / max z open a close), `wick` (high / low), `close`. Důvod: systém považuje dlouhé knoty za nevýznamné a TL kreslí tam, kde se cena pohybovala nejvíce.

## 5. Swingy

- Zigzag s prahem θ × `atr1` (výchozí θ = 3, kalibruje se, viz 12).
- Kandidát extrému se průběžně posouvá; spolu s ním se ukládá `atr1` v čase extrému. Potvrzení = návrat ceny od kandidáta o θ × `atr1(t_extrém)`. Změna ATR bez pohybu ceny tak swing nepotvrdí.
- Každý swing má: typ (high / low), čas a cenu extrému (dle `anchor_mode`), čas potvrzení, `atr1` v čase extrému.
- Potvrzený swing se zpětně nemění. Stav v čase t používá jen swingy s časem potvrzení ≤ t.

## 6. Trendline

Popis pro uptrend; downtrend zrcadlově (swing high, HH ↔ LL, HL ↔ LH).

### 6.1 Struktura trendu

- Začátek `L₀` = nejstarší swing low, od kterého tvoří následující potvrzené swingy nepřerušenou sekvenci HH + HL.
- Trend je **platný**, pokud existují ≥ 2 swing low v sekvenci (≥ 1 HL) a mezi nimi swing high. S jediným swing low TL nejde určit a trend je jen kandidát.

### 6.2 Hlavní TL

- Kotvy = swing low sekvence od `L₀`.
- TL = přímka z `L₀` s nejmenším sklonem ke kterékoli další kotvě (hrana dolní konvexní obálky kotev začínající v `L₀`). Všechny kotvy leží na TL nebo nad ní.
- Tolerance ε = 0,5 × `atr1`: těla barů mezi kotvami smí TL podkročit nejvýše o ε; knoty se nekontrolují.
- Překreslení: nový potvrzený swing low nad předchozím swing low (HL platí) se zahrne do obálky; pokud se tím TL změní, událost `TL_UPDATE`.

### 6.3 Aktuální TL

- Kandidát = přímka přes poslední dvě swing low sekvence, splňující toleranci ε.
- Kandidát se stane aktuální TL, pokud poměr jeho sklonu ke sklonu hlavní TL je ≥ 1,5 (strmější) nebo ≤ 0,67 (pozvolnější). Jinak aktuální TL = hlavní TL.
- Událost `CURR_TL_NEW`. Prolomení aktuální TL při neprolomené hlavní TL: aktuální TL = hlavní TL až do dalšího kandidáta.

### 6.4 Projekce

`value_at(x)` vrací hodnotu hlavní i aktuální TL pro libovolný bar x, i budoucí. Slouží spotřebiteli pro vstupní zóny, SL:B a výstup OUT:B.

### 6.5 Prolomení

- **Prolomení TL:** close baru pod TL − ε. Událost `TL_BREAK` s údajem, zda jde o hlavní nebo aktuální TL.
- Po prolomení hlavní TL je trend neobchodovatelný (`TL_BROKEN`): pravidlo 1 vyžaduje trend určený TL. Pokud se poté potvrdí nový swing low nad předchozím swing low, hlavní TL se překreslí (6.2) a trend je opět platný.
- **Prolomení struktury:** close pod posledním potvrzeným swing low. Trend končí (`TREND_END`) a hledá se nová struktura.

### 6.6 Sklon a pravidlo 45°

- `slope_norm` = sklon TL v `atr1` / bar, pro hlavní i aktuální TL.
- Úhel na grafu závisí na měřítku osy ceny a šířce baru, takže „45°“ bez měřítka nemá číselnou hodnotu. Komponenta vrací `slope_norm`; filtr `min_slope` je parametr, výchozí vypnutý.
- Hodnotu `slope_norm` odpovídající 45° ze systému neznám; určí se kalibrací (viz 12).

## 7. Stav trendu a pullbacku

Stav se vede pro každý směr zvlášť; uptrend a downtrend mohou existovat současně (např. při přechodu trendu). `direction` = směr s platným trendem; při dvou platných ten s novějším `L₀`.

| Fáze (uptrend) | Podmínka |
|---|---|
| `NONE` | žádná struktura |
| `CANDIDATE` | jedna vlna, TL nelze určit |
| `IMPULSE` | trend platný, pokles od běžícího maxima `H` < θ_pb × `atr1(t_H)` |
| `PULLBACK` | trend platný, pokles od `H` ≥ θ_pb × `atr1(t_H)`, close nad posledním swing low, hlavní TL neprolomená |
| `TL_BROKEN` | close pod hlavní TL − ε, struktura trvá |
| `ENDED` | close pod posledním swing low |

- θ_pb = θ (výchozí), takže začátek pullbacku = potvrzení swing high `H`.
- Pullback končí novým maximem nad `H` (→ `IMPULSE`, událost `PULLBACK_END_UP`), nebo prolomením (→ `TL_BROKEN` / `ENDED`).
- Prolomení aktuální TL během pullbacku fázi nemění, jen se zaznamená `TL_BREAK` aktuální TL.
- Výstupy pullbacku: čas začátku (`H`), délka v barech, počet vnitřních swingů, `dist_to_tl_atr` = vzdálenost close od hlavní a aktuální TL v `atr1`, `dist_to_level_atr` = vzdálenost k nejbližší úrovni proti směru pullbacku (3.5), `stopped_at_level` = pullback se zastavil u úrovně v toleranci `level_tol`.

## 8. Kvalita trendu

### 8.1 Metriky (úsek `L₀` → aktuální bar, směrově zarovnané)

| Metrika | Definice |
|---|---|
| `slope_norm_main`, `slope_norm_curr` | 6.6 |
| `slope_ratio` | aktuální / hlavní; > 1 zrychlení, < 1 zpomalení |
| `er` | Kaufman efficiency ratio: \|close_t − close(`L₀`)\| / Σ\|close_i − close_{i−1}\| přes **tytéž bary** včetně skoků mezi session; vždy ≤ 1 |
| `r2` | R² regrese kotev swing low; jen při ≥ 3 kotvách, jinak chybí |
| `n_swings` | počet HH + HL od `L₀` |
| `duration_bars`, `duration_min` | délka trendu |
| `tl_max_dev_atr` | největší vzdálenost těla baru nad hlavní TL od `L₀`, v `atr1` |
| `levels_crossed` | počet úrovní proražených od `L₀` ve směru trendu |
| `dist_to_next_level_atr` | vzdálenost close k nejbližší úrovni ve směru trendu, v `atr1` |
| `anchors_on_level` | podíl kotev TL, které vznikly u úrovně (tolerance `level_tol`) |
| `L0_on_level` | začátek trendu vznikl u úrovně |
| `levels_missing` | vstup úrovní je prázdný, metriky výše nedefinované |
| `session_cross` | úsek protíná hranici session |
| `roll_in_structure` | úsek protíná den rollu |
| `gap_in_structure` | úsek obsahuje mezeru ≥ 5 min uvnitř session |

### 8.2 Filtry PW-SW

- **PW1 (swingy v souladu s trendem):**
  - `pw1_trend_side`: posledních N = 3 swing low roste (v downtrendu swing high klesá),
  - `pw1_counter_side`: uvnitř aktuálního pullbacku nevznikly ≥ 2 po sobě jdoucí nižší swing high (v downtrendu ≥ 2 vyšší swing low). Tato část je moje interpretace ilustrace v systému; ověřit kalibrací.
- **PW2 (trh poblíž TL):** `pw2` = `tl_max_dev_atr` ≤ δ (výchozí δ = 3).
- **PW3 (bez chopu):** `chop_bars` = počet barů v posledních W = 60 barech, kde ER(20) < 0,25 **a cena zároveň není u úrovně** (vzdálenost > `level_tol` × `atr1`); `pw3` = `chop_bars` < 30. Bez vstupu úrovní se podmínka o úrovni vynechá a nastaví se `levels_missing`.
- `reversal_hint` = ne (PW1 a PW2 a PW3).

Výchozí hodnoty δ, W a prahů ER jsou odhady; kalibrují se (12).

## 9. Modul cumulative delta (volitelný)

- Tentýž zigzag, struktura a TL nad řadou kumulativní delty, s prahem v násobcích ATR delta řady.
- `delta_tl_agrees`: TL na deltě má stejný směr jako trend ceny a není prolomená.
- `delta_divergence`: cena vytvořila vyšší swing low, delta ne (nižší nebo stejné v toleranci ε); v downtrendu zrcadlově.
- Přes den rollu neplatné (objem je rozdělen mezi dva kontrakty).
- Vyžaduje bid/ask objem. Zda jej export 1min barů z NinjaTraderu obsahuje, nevím.

## 10. Rozhraní

```python
engine = TrendEngine(params, session_calendar, roll_dates, levels=None)  # levels: poskytovatel úrovní (3.5), None = bez úrovní
state = engine.update(bar)        # streaming, volá se po uzavření baru
states, events = engine.run(df)   # dávkově, výsledky identické se streamingem
```

**Stav (pro každý bar, zvlášť `up` a `down`, plus `direction`):**

| Pole | Popis |
|---|---|
| `direction` | UP / DOWN / NONE |
| `phase` | NONE / CANDIDATE / IMPULSE / PULLBACK / TL_BROKEN / ENDED |
| `trend_valid` | TL existuje a není prolomená |
| `L0` | začátek trendu (čas, cena) |
| `swings` | potvrzené swingy trendu (typ, čas extrému, cena, čas potvrzení) |
| `main_tl`, `curr_tl` | kotvy, `slope_norm`, `value_at(x)`, stav prolomení |
| `pullback` | začátek (`H`), délka v barech, vnitřní swingy, `dist_to_tl_atr`, `dist_to_level_atr`, `stopped_at_level` |
| `quality` | metriky 8.1 |
| `pw1_trend_side`, `pw1_counter_side`, `pw2`, `pw3`, `reversal_hint` | filtry 8.2 |
| `delta_tl_agrees`, `delta_divergence` | modul 9, pokud je aktivní |
| `levels_missing` | vstup úrovní je prázdný |

**Události:** `SWING_CONFIRMED`, `TREND_START`, `TL_UPDATE`, `CURR_TL_NEW`, `PULLBACK_START`, `PULLBACK_END_UP`, `TL_BREAK`, `TREND_END`. Každá nese čas baru, kdy byla známa, a čas, ke kterému se vztahuje (např. čas extrému swingu).

## 11. Požadavky na chování

- **Bez pohledu do budoucnosti:** výstup v baru t závisí jen na barech ≤ t.
- **Replay invariance:** `run(df)` dává totéž co postupné volání `update()`.
- **Determinismus:** žádná náhodnost.
- **Neměnnost historie:** potvrzené swingy a minulé stavy se zpětně nemění; změny jen jako nové události.
- **Mezery:** chybějící minuty se nedoplňují; mezera ≥ 5 min uvnitř session se označí (8.1).
- **Výkon:** lineární čas; celá historie 2007–2025 (řádově 6 mil. 1min barů ETH) do 10 min na jednom jádře.

## 12. Parametry a kalibrace

| Parametr | Výchozí | Rozsah kalibrace |
|---|---|---|
| `anchor_mode` | body | body / wick / close |
| `atr_n` | 30 barů | 20–60 |
| θ (zigzag) | 3 × `atr1` | 2–6 |
| θ_pb | = θ | 0,5θ–θ |
| ε (tolerance TL) | 0,5 × `atr1` | 0,25–1 |
| poměr sklonu aktuální TL | ≥ 1,5 / ≤ 0,67 | 1,25–2 |
| `min_slope` | vypnuto | určit kalibrací |
| PW1: N, protitrendové swingy | 3, 2 | 2–4, 2–3 |
| PW2: δ | 3 × `atr1` | 2–5 |
| PW3: W, okno ER, práh ER, počet barů | 60, 20, 0,25, 30 | dle kalibrace |
| `level_tol` | 0,5 × `atr1` | 0,25–1,5 |
| `levels_enabled` | true | true / false (běh bez úrovní, 13.10) |
| `session_scope` | ETH | ETH / RTH |

**Kalibrace:** podklady systému obsahují záznamy obchodů s ručně zakreslenými TL (chartbooks). Druhým dostupným podkladem je obchodní deník autora (3.6); zda a jak se použije, není rozhodnuto.

1. Vybrat vzorek dnů.
2. Ručně označit trend, hlavní a aktuální TL, začátek pullbacku a PW-SW.
3. Nastavit parametry pro nejlepší shodu na části dnů.
4. Ověřit shodu na zbývajících dnech.

Metriky shody: shoda fáze po barech, rozdíl sklonu TL, rozdíl času začátku pullbacku, shoda PW-SW. Pro `min_slope`: změřit `slope_norm` u TL, které systém označuje jako vyhovující a nevyhovující pravidlu 45°.

## 13. Testování

### 13.1 Princip

Jeden test, který:

1. spustí komponentu nad historickými daty bar po baru,
2. uloží každý její odhad tak, jak byl známý v daném baru,
3. každý odhad zkontroluje pohledem do budoucnosti: podívá se, co se po něm skutečně stalo, a určí, zda byl pravdivý,
4. spočítá metriky.

Pohled do budoucnosti má jen test v kroku 3, až po běhu komponenty. Komponenta sama budoucnost nikdy nevidí.

### 13.2 Povinné funkční testy (brány, pass / fail)

Bez splnění všech bran se historické metriky nevyhodnocují.

1. **Zkrácení dat:** pro 1 000 náhodných bodů t se komponenta spustí na datech do t a na celých datech. Všechny výstupy do t musí být identické. Nejsilnější test absence pohledu do budoucnosti.
2. **Změna budoucnosti:** náhodná změna barů po t nezmění žádný výstup do t.
3. **Replay:** `run(df)` = postupné `update()` (11).
4. **Determinismus:** dva běhy dávají bitově shodné výstupy (hash logu).
5. **Syntetické scénáře se známou pravdou:** přímkový trend se šumem, pullbacky s obnovením i s obratem, prolomení TL bez prolomení struktury, chop, současný uptrend a downtrend. Komponenta musí vrátit očekávané fáze a události ve správných barech.
6. **Okrajové případy:** mezery přes noc a víkend, halt, den rollu, extrémně dlouhý knot, plochý trh, první bary historie (málo dat pro ATR).

### 13.3 Historický běh

- **Data:** celá dostupná historie 1min NQ ETH (cílově ~20 let), s ověřenými časy z datové vrstvy (3).
- **Období:** chronologicky rozdělené **před prvním během**:
  - vývojové: prvních ~70 % (např. 2007-01-01 až 2018-12-31) — smí se na něm ladit parametry (12),
  - testovací: posledních ~30 % (např. 2019-01-01 až konec dat) — vyhodnotí se **jednou** se zmrazenými parametry.
- Pokud se parametry po pohledu na testovací období změní, testovací období se stává vývojovým a report to uvede.
- **Log odhadů:** pro každý bar `direction`, `phase`, parametry hlavní a aktuální TL; seznam událostí s časem, kdy byly známy. Formát parquet.

### 13.4 Kontrola odhadů pohledem do budoucnosti

Pro uptrend; downtrend zrcadlově. Kontrola používá stejnou definici swingů (5), ale nad celými daty.

| Odhad komponenty | Co test zkontroluje v budoucnosti | Výsledek |
|---|---|---|
| Swing potvrzen v baru t | kdy nastal extrém swingu | **zpoždění potvrzení** (bary, minuty) |
| Trend platný v baru t | zda bar leží v úseku trendu `L₀` → `H_final` (poslední swing high před prolomením struktury) | **pravda / nepravda po barech** |
| Začátek trendu | kdy byl `L₀` úseku | **zpoždění začátku** (od `L₀` do prvního `trend_valid`) |
| Konec trendu (`TREND_END`) | kdy byl `H_final` úseku | **zpoždění konce** (od `H_final` do `TREND_END`) |
| `PULLBACK_START` | co nastalo dřív: nové maximum nad `H`, nebo close pod posledním swing low | **OBNOVENÍ** (pravda) / **OBRAT** (nepravda) / **NEVYŘEŠENO** (nic z toho do 5 session nebo do konce dat) |
| `TL_BREAK` hlavní TL | co nastalo dřív: nové maximum nad `H`, nebo prolomení struktury | **FALEŠNÉ** / **SKUTEČNÉ** prolomení |
| Trend UP v baru t (nezávisle na swingech) | zda cena dosáhla dřív `close_t + k × atr1(t)`, nebo `close_t − k × atr1(t)`, v horizontu h barů | **pravda** při dosažení horní úrovně první / **nepravda** / nic v horizontu |

- Výsledek pullbacku se reportuje ve dvou variantách: do 5 session a do konce téže session (16:00 ET), protože P.A.T. je intradenní systém.
- Poslední kontrola (pokračování trendu) nepoužívá swingy, takže měří, zda trend skutečně pokračoval, ne jen zda komponenta správně aplikovala vlastní definici. Primárně k = θ, h = 240 barů; citlivost k = 2θ a h = 60.
- Zpoždění začátku trendu je zčásti nevyhnutelné: trend smí být vyhlášen až po potvrzení druhého swing low. Report uvádí i minimální možné zpoždění.

### 13.5 Referenční hodnoty (co by dala náhoda)

Bez referenční hodnoty nelze říct, zda je úspěšnost odhadu dílem komponenty, nebo jen geometrie a driftu trhu.

| Kontrola | Reference |
|---|---|
| Výsledek pullbacku | `p₀ = (c − L) / (H − L)` v baru `PULLBACK_START` (c = close, L = poslední swing low, H = swing high; náhodná procházka bez driftu a limitu); navíc simulace blokovým bootstrapem 1min výnosů (bloky 15 min, stejný den v týdnu a kvintil `atr1`, bez driftu) se stejnými úrovněmi a horizontem |
| Prolomení TL | totéž `p₀` z ceny v baru `TL_BREAK` |
| Pokračování trendu | 0,5 (bez driftu) a podíl „horní úroveň první“ mezi **všemi** bary téhož roku (zohlední drift NQ) |
| Trend po barech | podíl barů v úsecích trendu (odhad „vždy trend“) |

Referenční výpočty používají vzdálenosti ke swingům. V testu je to povoleno; do komponenty nepatří.

### 13.6 Metriky a report

- **Trend:** matice záměn UP / DOWN / NONE po barech, přesnost a úplnost pro každý směr, rozdělení zpoždění začátku a konce, podíl úseků trendu, které komponenta nezachytila vůbec.
- **Pullback:** počty OBNOVENÍ / OBRAT / NEVYŘEŠENO, úspěšnost = OBNOVENÍ / (OBNOVENÍ + OBRAT), rozdíl proti průměrnému `p₀` a proti simulaci.
- **Prolomení TL:** podíl falešných prolomení vs. reference; podíl konců trendu, kterým předcházelo prolomení hlavní TL (včasné varování).
- **Swingy:** rozdělení zpoždění potvrzení v barech a v násobcích `atr1`.
- **Pokračování trendu:** podíl pravdivých odhadů pro UP a DOWN vs. obě reference.
- **Členění:** po letech, směrech, RTH / noc, kvintilech `atr1`, vývojové / testovací období.
- **Intervaly:** 95% intervaly blokovým bootstrapem po týdnech (výsledky uvnitř týdne nejsou nezávislé).

### 13.7 Vyhodnocení filtrů PW-SW

- Úspěšnost pullbacků (13.4) zvlášť pro `reversal_hint` = 0 a 1 a pro každý filtr PW1–PW3.
- Očekávání systému: při `reversal_hint` = 1 je úspěšnost nižší. Report uvádí rozdíl s intervalem a podíl pullbacků, které filtr vyřadí.
- Totéž pro modul delta (9), pokud je aktivní.

### 13.8 Vizuální audit

P.A.T. je vizuální systém; číselná kontrola nezachytí vše.

- Náhodný vzorek 100 událostí `PULLBACK_START` a 50 `TREND_END`, rozložený přes roky.
- Graf: 300 barů před a 300 po události; TL **tak, jak byla známa v čase události** (ne pozdější překreslení), swingy komponenty a swingy určené zpětně nad celými daty.
- Uživatel u každého označí: souhlasím / nesouhlasím s tím, že šlo o trend a pullback podle P.A.T., a důvod nesouhlasu.
- Výstup: míra souhlasu a typy chyb.

### 13.9 Běh s úrovněmi a bez nich

- Celá sada z 13.2 až 13.8 se pouští dvakrát: s poskytovatelem úrovní (3.5) a s `levels_enabled = false`.
- Report uvádí rozdíl obou běhů pro každou metriku z 13.6. Rozdíl je odpověď na otázku, kolik úrovně přidávají; kdyby byly zapečené uvnitř komponenty, nelze ji položit.
- Brány z 13.2 musí projít v obou variantách. Komponenta bez úrovní nesmí spadnout ani vracet nedefinované hodnoty; smí jen nastavit `levels_missing`.
- Využití obchodního deníku (3.6) v testech zatím není rozhodnuto; do žádné z bran ani metrik nevstupuje.

### 13.10 Interpretace

- **Brány 13.2** jsou pass / fail.
- **Historické metriky** nemají pevné cílové hodnoty; dosažitelnou úroveň neznám. První běh na vývojovém období stanoví referenci. Každá další verze komponenty nebo sada parametrů se porovná proti ní (metriky uložené jako JSON, změny se hlásí).
- Úspěšnost ≈ reference: komponenta stavy detekuje, ale bez informace nad rámec geometrie. Úspěšnost nad referencí: na daném měřítku trendy přetrvávají.
- **Podezření na únik budoucnosti:** úspěšnost kontroly pokračování trendu nad 0,7, nebo úspěšnost pullbacků o víc než 20 p.b. nad referencí → zopakovat brány 13.2.1 a 13.2.2 na dotčených obdobích, než se výsledek přijme.
- Test měří správnost detekce stavů, ne obchodní výsledek systému (vstup, cíl, stop zůstávají mimo rozsah).

## 14. Mimo rozsah

- **Výpočet** S/R, OHLC minulého dne a premarketu; komponenta je přijímá jako vstup (3.5), sama je neurčuje.
- Vstupní zóny (křížení TL s úrovněmi) počítá spotřebitel z projekce TL a ze seznamu úrovní.
- Profit target, stop-loss, vstup, výstup, position sizing.
- Vzdálenosti ceny ke swingům a geometrie obchodu.
- Hodnocení obchodního výsledku (vstup, cíl, stop), prediktivní modely, zprávy. Test správnosti detekce (13) do rozsahu patří.

## 15. Dodatky k zapracování

> **Úkol pro recenzenta:** body níže jsou dodatky zadavatele. Zapracuj každý do příslušných sekcí dokumentu jako konkrétní řešení. Po zapracování tuto sekci odstraň; zapracování zaznamenej v rozhodovacím logu.

1. Pokud se zjistí, že jsou třeba další vstupy, musí se o ně požádat.
2. K dispozici budou 1s a 1min data. 1s data je možné použít pro jemnou detekci v citlivých místech.
3. Pokud se zjistí, že by pro detekci byla vhodnější jiná než 1min data, je třeba to uvést a zdůvodnit.
4. Komponenta musí mít testovatelné rozhraní. Testy komponenty jsou samostatné zadání `zadani/testy.md`.
5. Komponenta musí především umět odpovědět na otázku Ø1:
   - Jsem v trendu (jak silném atd.)?
   - Začíná pullback?
   - Bude trend pokračovat?
   - \+ detaily pro P.A.T.
6. Nesmí overfittovat. Měla by mít podobné výsledky na syntetických datech jako na různých trzích.
7. Metoda detekce se nemusí omezovat na metody P.A.T. Recenzent může k zodpovězení Ø1 použít naprosto jakékoliv prostředky a techniky. Pokud jimi nedisponuje (např. GPU), může o ně požádat.
8. Komponenta může implementovat více druhů detekce. Každý, který bude výhodné implementovat, bude popsán.
9. Dodatečným podkladem je reálný obchodní deník s reálnými obchody. Nesmí ale kontaminovat algoritmus do té míry, že bude poplatný těmto datům.
10. Vše by mělo fungovat na obecném trhu, primární je teď trh NQ. Doladění na ostatních trzích může přijít později.
11. Jakýkoliv indikátor je na aktuální svíčce počítán z hodnot, které nejsou dopředu známé (OPEN/CLOSE/HIGH/LOW). Zvážit, zda vycházet z hodnoty předchozí svíčky.
12. Výstup SR komponenty (`zadani/komponenta-sr.md`) slouží jako vstup této komponenty.
