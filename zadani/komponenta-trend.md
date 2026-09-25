# Zadání: Komponenta detekce trendu a pullbacku (pro obchodní systém P.A.T.)

Verze: revize kolo 1 (TASK-0002, 2026-09-25) · dokument je psaný pro AI implementátora a AI testera, ne pro čtení člověkem · rozhodnutí jsou závazná (16), historie změn v 17.

## 0. Kontext: obchodní systém P.A.T.

Vše v tomto zadání se dělá v kontextu obchodního systému P.A.T. a pro něj. Výsledek (komponenta detekce trendu a pullbacku) bude použit výhradně v systému P.A.T., který se ve finále implementuje; jiné použití není a nenavrhuje se pro něj. Každé rozhodnutí se posuzuje podle toho, co potřebuje P.A.T.; rozpor se systémem P.A.T. je chyba zadání.

Podklady systému ve složce `PAT/` (závazné):

- `PAT/Popis OS P.A.T.pdf` — popis obchodního systému P.A.T. (kapitoly I–IX; odkazy v tomto dokumentu jsou na čísla kapitol a pravidel, text popisu se nikam nekopíruje),
- `PAT/Obchodní deník.xls` — reálný obchodní deník s reálnými obchody,
- `PAT/obrazky-obchodu/` — obrázky jednotlivých obchodů.

Doplňkové podklady (odvozené z obrázků, přesnost ±1 tick a ±1 min, viz jejich popis):

- `PAT/PAT_obchody_z_obrazku.csv` — obchody z obrázků ve struktuře deníku, včetně změřených TL (sklon v bodech/min, kotvy), úrovní OHLC a S/R a typu vstupní zóny,
- `PAT/PAT_obchody_z_obrazku_POPIS.md` — popis sloupců a metod měření,
- `PAT/PAT_obrazky_progress.csv` — stav zpracování obrázků.

Deník a obrázky jsou pouze podklad; způsob jejich použití je omezen v 3.6 (nesmí kontaminovat algoritmus).

## 1. Účel a rozsah

### 1.1 Otázka Ø1 (primární výstup)

Komponenta musí v každém uzavřeném baru, bez pohledu do budoucnosti, odpovědět na otázku Ø1 zadavatele. Odpověď je strukturované pole `answer` ve stavu (10.3); každá část otázky má konkrétní pole a definici:

| Část Ø1 | Pole `answer` | Definice | Sekce |
|---|---|---|---|
| Jsem v trendu? Kterým směrem? | `in_trend` (bool), `direction` (UP / DOWN / NONE) | `in_trend` = `direction ≠ NONE`; `direction` podle 7.3 | 6, 7 |
| Jak silný je trend? | `strength` (float 0–1 nebo null), `strength_class` (WEAK / MEDIUM / STRONG / null) | 8.3 | 8 |
| Začíná pullback? | `pullback_starting` (bool), `pullback_active` (bool), `pullback_age_bars` (int nebo null) | 7.4 | 7 |
| Bude trend pokračovat? | `continuation_score` (float 0–1 nebo null), `continuation_n` (int nebo null), `continuation_source` (TABLE / ML / null) | odhad pravděpodobnosti, že cena dosáhne dřív +k·atr než −k·atr ve směru trendu (15.4, 15.5); null, když tabulka pokračování není načtena nebo bin nemá dost vzorků | 15.3–15.5 |
| Detaily pro P.A.T. | zbytek stavu (10.3) | TL s kotvami a projekcí, swingy, fáze, PW-SW, vzdálenosti k TL a k úrovním, kvalita | 6–9 |

Odpověď na Ø1 je hlavní kritérium hodnocení komponenty (13.6, 13.7); metody, kterými se odpovědi dosahuje, nejsou omezeny na metody P.A.T. (15).

### 1.2 Co komponenta dělá

Komponenta (knihovna) zpracovává proud barů (primárně 1min, 3.7) a v každém uzavřeném baru určuje:

1. zda je trh v trendu (nahoru / dolů / žádný), podle swingů a trendline (TL),
2. hlavní a aktuální TL jako čáru s kotvami a projekcí do budoucna,
3. zda je trh v pullbacku v rámci trendu, nebo zda byl trend prolomen,
4. metriky kvality trendu včetně filtrů PW-SW a odhad pokračování trendu.

Komponenta **přijímá cenové úrovně jako vstup** (3.5): S/R, OHLC minulého dne, premarket. Úrovně mění klasifikaci pullbacku, kotvení TL, stáří trendu i váhu prolomení a bez nich nelze rozlišit chop od zdržení na úrovni, jak vyžaduje PW-SW 3 (kapitola VIII). Komponenta ale **musí fungovat i s prázdným seznamem úrovní**, jen s horší kvalitou; rozdíl mezi během s úrovněmi a bez nich se měří (13.9). Druhým volitelným vnějším vstupem je ekonomický kalendář zpráv (3.9); ten detektor A nečte, slouží jen jako rys pro report, detektor D a spotřebitele.

Komponenta **neřeší**: výpočet S/R úrovní (jen je přijímá), vstupní zóny, profit target, stop-loss, vstup, výstup, velikost pozice, vzdálenosti ceny ke swingům ani obchodní výsledek systému. Tyto části systému P.A.T. komponentu používají jako vstup (viz 2). Součástí zadání jsou akceptační kritéria a požadavky na testovatelnost (13); postup testů je samostatné zadání (1.4).

### 1.3 Detektory

Komponenta obsahuje více druhů detekce (dodatek zadavatele; katalog metod a důvody výběru v 15). Každý detektor je samostatný modul se společným rozhraním (15.6); výstupy všech jsou ve stavu vedle sebe, nikdy se tiše neslučují.

| Detektor | Obsah | Stav v v1 | Sekce |
|---|---|---|---|
| A — strukturální | zigzag swingy, struktura HH/HL, hlavní a aktuální TL, fáze, PW-SW; metoda P.A.T., závazná, protože spotřebitelé potřebují TL a swingy | povinný, vždy zapnutý | 5–8 |
| B — statistický | síla trendu z regrese, efficiency ratio a variance ratio v klouzavém okně | zapnutý ve výchozím nastavení, vypnutelný | 15.2 |
| C — tabulka pokračování | empirická pravděpodobnost pokračování podle binů (fáze, síla, `reversal_hint`), zmrazená z vývojového období | zapnutý, je-li tabulka dodána; jinak `continuation_score = null` | 15.4 |
| D — strojové učení | gradient boosting nad rysy A + B + úrovně, cíl = pokračování; walk-forward | specifikován, vypnutý; zapne se jen po splnění brány 15.5 | 15.5 |
| delta | zigzag a TL nad kumulativní deltou (kapitola IX) | volitelný, vyžaduje bid/ask objem | 9 |

### 1.4 Vztah k ostatním zadáním

- `zadani/komponenta-sr.md` — komponenta SR; její výstup je vstupem této komponenty přes rozhraní poskytovatele úrovní (3.5). Rozhraní 3.5 je pro komponentu SR závazná smlouva (pole, sémantika platnosti, acyklicita). Rozpor obou zadání se řeší úpravou zadání SR, protože spotřebitelem je tato komponenta.
- `zadani/testy.md` — testy komponent; předmětem testů je tato komponenta. Tento dokument definuje **co** se testuje (brány, metriky, referenční hodnoty, akceptační kritéria, sekce 13) a **co komponenta musí poskytnout, aby byla testovatelná** (10.5); `zadani/testy.md` definuje **jak** se testy provádějí (data, harness, formát reportu). Při rozporu platí pro obsah bran a metrik tento dokument.

### 1.5 Další vstupy

Pokud implementátor nebo tester zjistí, že je třeba vstup, který sekce 3 neuvádí, nesmí ho odvozovat uvnitř komponenty ani tiše předpokládat. Zapíše požadavek do `requests` výsledku kola (identifikace vstupu, k čemu je nutný, náhradní chování do jeho dodání) a do té doby použije náhradní chování uvedené u příslušného vstupu v sekci 3. Aktuálně otevřené požadavky jsou v 3.8.

## 2. Požadavky systému P.A.T. na komponentu

Průchod popisem P.A.T. kapitolu po kapitole; každé pravidlo, které se týká trendu, TL nebo pullbacku, má výstup nebo chování, které ho pokrývá. Kapitoly III–VI (PT, SL, vstup, výstup) se komponenty týkají jen tím, co od ní spotřebitel potřebuje.

| Část P.A.T. | Požadavek systému (parafráze) | Výstup komponenty | Poznámka |
|---|---|---|---|
| I.1, I.2 OHLC minulého dne, S/R premarketu a minulého dne; podstatné S/R vzniklé během seance | úrovně jsou zakresleny před seancí, další přibývají během ní | vstup 3.5 (`valid_from` může být uvnitř seance) | komponenta úrovně nepočítá; SR komponenta (1.4) |
| I.3 Hlavní trend | uptrend určuje TL přes swing low, downtrend TL přes swing high; TL se kreslí tam, kde se cena pohybovala nejvíce, dlouhé knoty nemají význam | `main_tl`, `anchor_mode = body` | 6.2, 4.4 |
| Pravidlo 1 | long jen v jasném uptrendu, short jen v jasném downtrendu (určeném TL) | `trend_valid`, `direction` | jasný = TL existuje (≥ 2 kotvy) a není prolomená, 7.2 |
| I.4 Aktuální trend | nová TL při strmějším nebo pozvolnějším pokračování; strmější není podmínka; TL se během seance průběžně dokreslují | `curr_tl`, události `CURR_TL_NEW`, `CURR_TL_DROP`, `TL_UPDATE` | 6.3 |
| Pravidlo 2 | vynechat obchody v trendu se sklonem pod 45° (obrázek uvádí rozsah 45°–90°) | `slope_norm_main`, `slope_norm_curr`, `slope_ok_*`, volitelný filtr `min_slope` | úhel bez měřítka grafu není definován; kalibrace 12.3, 6.6 |
| I.5, I.6 Vstupní zóny A/B/C | křížení hlavní TL s OHLC (A), hlavní TL s S/R nebo aktuální TL s OHLC (B), aktuální TL s S/R (C) | `value_at(x)` hlavní i aktuální TL, `bar_index` | křížení počítá spotřebitel z projekce a seznamu úrovní |
| Pravidlo 3 | vstup jen ve vstupní zóně | (spotřebitel) | komponenta dodá projekci TL |
| II Zóna pozornosti | korekce, která se pomalu vrací k S/R a k TL nejaktuálnějšího trendu | `phase = PULLBACK`, `answer.pullback_starting`, `dist_to_tl_atr`, `dist_to_level_atr`, `stopped_at_level` | 7.4 |
| III PT:A, IV SL:A | high / low minulého swingu | seznam potvrzených swingů (`swings`, `pullback.pb_low`) | vzdálenosti počítá spotřebitel |
| IV SL:B | úroveň TL nejaktuálnějšího trendu v čase svíčky | `curr_tl.value_at(x)` | |
| V Pravidlo 4 | vstup nejdál 10 svíček od křížení linek | `bar_index`, projekce TL | počítá spotřebitel |
| VI OUT:B | výstup při překročení TL určující trend (v ukázce aktuální, zelená) | událost `TL_BREAK` s `which ∈ {MAIN, CURR}` | 6.5 |
| VII Závěr | systém je použitelný na NQ, ES, YM; 1min TF není podmínka, vyšší TF dává méně příležitostí | žádná konstanta trhu v kódu, prahy v ATR, `tf_minutes` parametr | 3.7, 11.3 |
| VIII PW-SW 1 | H/L swingů v souladu s trendem: před vstupní zónou stále vyšší low (uptrend) / nižší high (downtrend); rostoucí low v downtrendu je varování | `pw1_trend_side`, `pw1_counter_side` | část je interpretace ilustrace, 8.2 |
| VIII PW-SW 2 | trh stále poblíž aktuální TL; mírné odchylky se tolerují, velký odklon ne | `tl_max_dev_atr_curr`, `tl_max_dev_atr_main`, `pw2` | obrázek v kapitole VIII mluví o aktuální TL, 8.2 |
| VIII PW-SW 3 | žádný chop před vstupní zónou; chvilkové zdržení na S/R chop není | `chop_bars`, `pw3`; vyloučení barů u úrovně | 8.2, vyžaduje vstup úrovní 3.5 |
| VIII souhrn | „náznak otočení trendu“ | `reversal_hint` | 8.2 |
| IX Cumulative delta | TL na deltě v souladu s TL ceny; H/L swingů na deltě v souladu s cenou | `delta_tl_agrees`, `delta_divergence` | modul 9, volitelný, vyžaduje bid/ask data |
| Obecně | TL se kreslí průběžně během seance; rozhodnutí na 1min grafu trvá 3–5 min (III.1) | streaming API po uzavření baru, stav platný od uzavření baru | 3.1, 10, 11 |

## 3. Vstupy

### 3.1 Bary

Primárně 1min NQ, ETH, spojitá řada (export NinjaTrader, Merge back adjusted). Jiné TF a trhy musí fungovat bez změny kódu (parametry `tf_minutes`, `tick_size`, 12).

| Pole | Typ | Jednotka | Pravidlo |
|---|---|---|---|
| `ts` | tz-aware timestamp | — | libovolné pásmo na vstupu, interně převod do `America/New_York`; konvence viz níže |
| `open`, `high`, `low`, `close` | float64 | body ceny | násobky `tick_size` (kontrola níže) |
| `volume` | int64 ≥ 0 | kontrakty | 0 je platná hodnota |
| `delta` | float64, volitelné | kontrakty | kumulativní delta na konci baru (modul 9); chybí-li sloupec, modul je neaktivní |

**Konvence timestampu.** Parametr `bar_timestamp ∈ {close, open}`, výchozí `close` (NinjaTrader exportuje čas uzavření baru; **neověřeno**). Interně se pracuje s `ts_open(t)` a `ts_close(t) = ts_open(t) + tf_minutes`; `bar_timestamp = close` znamená `ts_open = ts − tf_minutes`. Kontrola při implementaci: na vývojových datech se spočítá průměrný objem 1min barů podle minuty dne (ET) v okně 09:00–10:00 ET; maximum musí padnout do baru s `ts_open = 09:30 ET` (skok objemu při otevření RTH); pokud padne do 09:29 nebo 09:31, konvence je nastavena špatně a běh se zastaví chybou `TimestampConventionError`. Kontrola se provádí jednou při startu dávkového běhu nad prvními 30 obchodními dny dat a je součástí brány 13.2.6.

**Kdy je stav platný.** `update(bar)` se volá až po uzavření baru; všechny hodnoty stavu v baru t jsou vypočtené z plných OHLC baru t a barů před ním a jsou platné od `ts_close(t)`. Spotřebitel, který jedná uvnitř otevřeného baru t+1, používá stav baru t. Uvnitř komponenty se žádný indikátor z otevřeného baru nepočítá. Prahy, které se v baru t aplikují, používají `atr_ref(t) = atr1(t−1)` (4.1), takže bar sám nemění práh, kterým je posuzován (dodatek zadavatele o indikátorech z aktuální svíčky).

**Validace baru** (v pořadí; první chyba rozhoduje):

1. `ts` chybí nebo není tz-aware → neplatný.
2. `ts_open(t) ≤ ts_open(t−1)` (nemonotónní nebo duplicitní čas) → neplatný.
3. některé z OHLC je NaN nebo `high < low` nebo `open`/`close` mimo `[low, high]` → neplatný.
4. `volume < 0` nebo NaN → neplatný.
5. cena není násobek `tick_size` (|price/tick − round(price/tick)| > 1e-6) → **varování** `NON_TICK_PRICE` (jednou za běh), bar zůstává platný; porovnávání cen (4.5) s tolerancí 0,5 ticku funguje i pro takové ceny.

Chování při neplatném baru řídí parametr `on_invalid_bar ∈ {raise, skip}`, výchozí `raise` (výjimka `InvalidBarError` s indexem a důvodem; u dávkového běhu se zastaví celý běh). Při `skip` se bar vynechá, vznikne varovná událost `BAR_SKIPPED` (10.4) a osa x se neposune (přeskočený bar nemá index). Bar s `high == low` (plochý) je platný, TR = 0.

**Kontrola časového pásma** je odpovědnost datové vrstvy; komponenta provádí jen kontrolu konvence timestampu výše.

### 3.2 Kalendář session

Vstup, komponenta rozvrh CME nezná ani neodvozuje (rozvrh se v historii měnil; správnost je odpovědnost datové vrstvy).

| Pole | Typ | Pravidlo |
|---|---|---|
| `session_id` | int, rostoucí | identifikace session (obchodní den ETH) |
| `session_open`, `session_close` | tz-aware | ETH začátek a konec, `[open, close)` |
| `rth_open`, `rth_close` | tz-aware | RTH uvnitř session; `rth_open ≥ session_open`, `rth_close ≤ session_close` |
| `trading_date` | date | obchodní datum session (datum RTH) |

Přiřazení: bar patří do session, jejíž `[session_open, session_close)` obsahuje `ts_open(t)`. Bar mimo všechny session (chyba kalendáře, halt přes konec session) dostane `session_id` poslední předchozí session a příznak `outside_session = true`; počet takových barů se hlásí varováním `BARS_OUTSIDE_SESSION` jednou za běh. Parametr `session_scope ∈ {ETH, RTH}` (výchozí ETH): při `RTH` se bary mimo RTH vynechávají před vstupem do komponenty (osa x je pak jen z RTH barů; mezera přes noc je hranice session).

Hranice session pro účely 4.1 a 8.1: bar t je první bar session, pokud `session_id(t) ≠ session_id(t−1)`.

### 3.3 Data rollu

Seznam `roll_dates` (obchodní data, `trading_date`) z nastavení rolloveru exportu (NinjaTrader), ne z kalendáře expirací; spojitá řada mění kontrakt jindy než v týdnu expirace. Bar rollu = první bar session, jejíž `trading_date ≥ roll_date` (první taková session pro každé datum). Řada je back-adjusted, takže se ceny nepřepočítávají; komponenta jen značí `roll_in_structure` (8.1) a modul delta se přes den rollu vypíná (9). Kontrola: pokud v baru rollu `|open(t) − close(t−1)| > 5 × atr_ref(t)`, vznikne varovná událost `ROLL_GAP` (řada zřejmě není back-adjusted); běh pokračuje.

### 3.4 Volitelné vstupy

- **Kumulativní delta** (`delta` sloupec, 3.1) pro modul 9. Zda export 1min barů z NinjaTraderu obsahuje bid/ask objem, není známo (požadavek 3.8).
- **1s data (`intrabar`)**: poskytovatel `IntrabarProvider.bars_1s(t) -> list[Bar1s]` vrací sekundové bary uvnitř 1min baru t (stejná validace jako 3.1). Použití je omezeno na tři místa: (i) pořadí high a low uvnitř baru v zigzagu (5.3), (ii) jemný čas extrému swingu `ts_ext_fine` (5.4, informativní), (iii) v testu 13.4 pro rozhodnutí, který z cílů byl dosažen dřív, když oba padly do téhož 1min baru. Parametr `intrabar_mode ∈ {auto, heuristic}`, výchozí `auto` = 1s data se použijí, jsou-li pro bar k dispozici, jinak heuristika 5.3. Bez 1s dat musí komponenta dávat úplné výstupy; rozdíl mezi režimy smí být jen v barech označených `intrabar_ambiguous = true` (13.2.7). 1s data nikdy nemění osu x (bary zůstávají 1min) ani prahy.
- **Tabulka pokračování** (`continuation_table`, JSON, 15.4) pro `answer.continuation_score`; bez ní je skóre null.

### 3.5 Cenové úrovně (vstup, volitelný)

Úrovně dodává poskytovatel za rozhraním `LevelProvider` (10.2); komponenta je nepočítá. Referenční implementace poskytovatele je komponenta SR (`zadani/komponenta-sr.md`); pro ni je tato sekce závazná smlouva.

| Pole | Typ | Popis |
|---|---|---|
| `level_id` | str | jednoznačná identifikace (poskytovatel + pořadové číslo); dvě úrovně se stejnou cenou mají různá id |
| `price` | float64 | cena úrovně (body) |
| `kind` | enum | `PDH`, `PDL`, `PDO`, `PDC`, `PREMARKET_H`, `PREMARKET_L`, `SESSION_OPEN`, `SR`; neznámá hodnota → úroveň se přeskočí s varováním `UNKNOWN_LEVEL_KIND` |
| `valid_from` | tz-aware | okamžik, od kterého je úroveň známa (nikdy dřív, než vznikla) |
| `valid_to` | tz-aware nebo null | konec platnosti (exkluzivně); null = bez konce |
| `strength` | float 0–1 nebo null | volitelná síla; null = neznámá; komponenta ji jen předává (nepoužívá v rozhodování) |
| `source` | str | identifikace poskytovatele |

- **Aktivní úroveň v baru t**: `valid_from ≤ ts_open(t)` a (`valid_to` je null nebo `ts_open(t) < valid_to`). Úroveň známá při uzavření baru k (`valid_from = ts_close(k)`) je tedy aktivní od baru k+1. Komponenta volá `levels_at(ts_open(t))` jednou za bar; poskytovatel musí být deterministický a smí vracet jen úrovně s `valid_from ≤ ts_open(t)`. Porušení (úroveň s `valid_from > ts_open(t)`) → výjimka `LookaheadLevelError`.
- **Dvě třídy úrovní za týmž rozhraním.** Mechanické (OHLC předchozího dne, premarket high a low, open seance) jsou bez diskrece a dostupné hned. Skutečné S/R (shluky swingů, opakovaně testované hladiny) jsou samostatná úloha (komponenta SR) a doplní se jako druhá implementace téhož rozhraní.
- **Acyklicita:** poskytovatel nesmí číst výstupy této komponenty. Odvozené úrovně smí vycházet z libovolných barů s `ts_close ≤ valid_from` (i z aktuální seance, kapitola I.2 počítá s S/R vzniklými během seance), nikdy z pozdějších.
- **Duplicity:** úrovně se stejnou cenou (rovnost v ticích, 4.5) se pro vzdálenostní metriky (7.4, 8.1) berou jako jedna cena; pro `levels_crossed` se počítají podle `level_id`.
- **Bez úrovní:** prázdný seznam je platný vstup. `levels_missing = true` v baru t, pokud v baru t není aktivní žádná úroveň (ať proto, že `levels = None`, `levels_enabled = false`, nebo poskytovatel nic nevrátil). Metriky závislé na úrovních jsou pak null a `pw3` se počítá bez vyloučení barů u úrovně.
- **Tolerance „na úrovni“:** cena `p` je u úrovně `L` v baru t, pokud `|p − L.price| ≤ level_tol × atr_ref(t)` (12).

### 3.6 Obchodní deník autora a obchody z obrázků (podklad, mimo běh komponenty)

K dispozici je obchodní deník autora systému: 597 obchodů z let 2010 až 2014, trh NQ, sloupce datum, čas, kontrakt, směr, vstup, SL, SL v ticích, PT, PT v ticích, RRR, MAE, MFE a P/L. Ověřeno proti záznamu z chartbooku ze 7. 3. 2014, hodnoty sedí. Doplňkem je `PAT/PAT_obchody_z_obrazku.csv` (obchody z obrázků, včetně změřených TL v bodech/min a úrovní; přesnost ±1 tick, ±1 min).

Co je to za data: **reálná rozhodnutí člověka**, tedy okamžiky, ve kterých autor viděl platný trend daného směru a pullback ve vstupní zóně. Z hodnot lze zpětně odvodit i polohu struktury, kterou viděl: u SL typu A leží stop tick pod posledním swing low, u PT typu A tick pod předchozím swing high, u PT typu B a C a SL typu B leží cíl nebo stop na úrovni, kterou autor považoval za S/R.

Omezení: deník neříká, kudy vedla trendline, a obsahuje jen kladné příklady; kde autor neobchodoval, nevíme, zda trend nebyl, nebo jen nevstoupil. Typ vstupní zóny, PT a SL je jen v chartboocích a v CSV z obrázků, ne v deníku.

**Rozhodnutí o využití (D-31, D-32):** deník a CSV z obrázků nesmí kontaminovat algoritmus (dodatek zadavatele). Povolená použití jsou přesně dvě:

1. **Kontrola shody s rozhodnutími autora** (13.13): pro každý obchod se zjistí stav komponenty v baru vstupu; hlásí se podíl obchodů, u nichž `direction` odpovídá směru obchodu a `phase ∈ {PULLBACK, IMPULSE}`, a podíl s `phase = PULLBACK`. Je to report, ne brána, a parametry se podle něj neladí.
2. **Kalibrace jediného parametru `min_slope`** (12.3) ze sloupce `TL sklon (bodů/min)` CSV z obrázků, protože pravidlo 2 (45°) nelze z popisu číselně určit jinak.

Jakékoli jiné použití (ladění θ, ε, δ, W, tvaru algoritmu podle deníku) je zakázáno; do bran 13.2 ani do historických metrik 13.6 deník nevstupuje.

### 3.7 Časový rámec (rozhodnutí D-33)

K dispozici jsou 1s a 1min data. Základní časový rámec komponenty je **1min** a nemění se. Důvody: (a) P.A.T. je definován a obchodován na 1min grafu (kapitoly III.1, VII), spotřebitel rozhoduje v okně 3–5 min; (b) 1s bary mají řádově nižší poměr signálu k šumu pro swingy velikosti θ·atr a nepřinesou rozhodnutí dřív, než se uzavře 1min bar, ve kterém spotřebitel jedná; (c) vyšší TF (5min) zpožďuje potvrzení každého swingu o násobek baru a překračuje rozhodovací okno. 1s data se používají jen pro jemnou detekci v citlivých místech (3.4).

Vhodnost jiného TF se přesto měří (13.12): detektor A se spustí nad 1, 2, 3 a 5min bary vytvořenými z týchž 1min dat a porovná se úspěšnost pokračování (13.4) a zpoždění. Pokud vyšší TF dá o ≥ 5 p.b. vyšší úspěšnost pokračování při zpoždění začátku trendu ≤ 2× hodnoty 1min, report to uvede jako doporučení ke změně základního TF; do té doby zůstává 1min.

### 3.8 Otevřené požadavky na vstupy

Požadavky předané zadavateli (dodatek zadavatele: o chybějící vstupy se musí požádat). Do jejich splnění platí uvedené náhradní chování.

| # | Požadavek | Proč | Náhradní chování |
|---|---|---|---|
| R1 | potvrdit, zda export 1min barů z NinjaTraderu obsahuje bid/ask objem (sloupec pro kumulativní deltu) | modul 9 | modul 9 neaktivní, pole null |
| R2 | 1min data ES a YM (stejný formát jako NQ) | robustnostní brána 13.11 přes trhy | brána běží jen na NQ (roky) a syntetice |
| R3 | rozsah 1s dat (od kdy, formát, konvence timestampu) | 3.4, test 13.2.7 | `intrabar_mode = heuristic` |
| R4 | potvrdit konvenci timestampu 1min exportu (čas uzavření vs. otevření) | 3.1 | kontrola objemem při startu |

### 3.9 Ekonomický kalendář zpráv (vstup, volitelný)

Rozhodnutí D-45: kalendář je **doplňkový rys**, ne součást definice trendu. Detektor A (5–8) ho nečte, takže fáze, TL a swingy jsou s kalendářem i bez něj totožné. Kalendář slouží: (a) členění reportu 13.6 (bary v okně zprávy vs. mimo), (b) rysům detektoru D (15.5), (c) spotřebiteli přes `state.news`. Důvod: P.A.T. zprávy neřeší; zásah do definice trendu podle vnějších dat by porušil soulad se systémem. Hypotéza, že se pokračování trendu v okolí zpráv s vysokým dopadem liší, se ověří členěním 13.6 (předpoklad); teprve podle výsledku se rozhodne o dalším použití (např. bin tabulky pokračování), zápisem do logu.

**Zdroj:** Forex Factory Calendar, Hugging Face `Ehsanrs2/Forex_Factory_Calendar` (2007-01-01 až 2025-04-07, ~83 400 řádků; pole `DateTime`, `Currency`, `Impact` (4 třídy), `Event`, `Actual`, `Forecast`, `Previous`, `Detail`). Načítá **datová vrstva / harness**, ne komponenta: `pd.read_csv("hf://datasets/Ehsanrs2/Forex_Factory_Calendar/<soubor>.csv")` (vyžaduje `huggingface_hub`, volitelná závislost); stažený soubor se uloží lokálně a jeho SHA-256 se zapíše do reportu.

**Normalizace (datová vrstva, deterministická):**

1. **Čas:** `DateTime` se interpretuje jako `Asia/Tehran` a převede přes IANA na `America/New_York` (IANA zahrnuje zrušení letního času v Íránu v roce 2022). Řádky bez přesného času (All Day, Tentative, prázdný čas) se vyřadí. **Kontrola pásma** (předpoklad, neověřeno): po převodu musí „Non-Farm Employment Change“ (USD) a „Unemployment Claims“ padat na 08:30 ET v ≥ 95 % výskytů a „FOMC Statement“ na 14:00 ET v ≥ 90 % výskytů od roku 2013. Nesplnění → `NewsTimezoneError`, kalendář se nepoužije (`state.news = null` všude) a report to uvede.
2. **Filtr:** `Currency = USD`, `Impact ∈ {High, Medium}`.
3. **Čísla:** `Actual`, `Forecast`, `Previous` → float: odstranit mezery, `%`, znaky `<`, `>`; přípony `K`, `M`, `B`, `T` = ×10³, ×10⁶, ×10⁹, ×10¹²; záporná čísla se znaménkem; neparsovatelné → null.
4. **Překvapení:** pro vydání zprávy `E` v čase `d`: `surprise_raw = Actual − Forecast` (null, chybí-li některé). `surprise_z = surprise_raw / sd`, kde `sd` = výběrová směrodatná odchylka `surprise_raw` **minulých vydání téže zprávy** (stejný `Event`, `DateTime < d`) s definovaným `surprise_raw`; podmínka **≥ 12 minulých vydání** (`news_min_history`). Jinak (méně vydání, `sd = 0`, `surprise_raw` null) `surprise_z = 0` a `surprise_missing = true` (indikátor dodatku `prekvapeni_chybi = 1`). Vydání se zpracovávají v pořadí `DateTime`; hodnoty pozdějších vydání se nikdy nepoužijí.
5. **Konec dat:** vydání a rozvrh po 2025-04-07 se nepoužívají; pro bary s `ts_open` po 2025-04-07 23:59 ET je `state.news = null`.

**Rozhraní** (10.2): `NewsProvider.scheduled_between(ts_from, ts_to) -> list[ScheduledEvent]` (`DateTime`, `Event`, `Impact`; bez `Actual`) a `NewsProvider.released_until(ts) -> list[Release]` (vydání s `DateTime ≤ ts`, včetně `surprise_z`, `surprise_missing`). Pravidla proti pohledu do budoucnosti: v baru t se smí použít rozvrh (čas, název, dopad) libovolné budoucí události (je znám předem) a `Actual`/`surprise_z` jen u vydání s `DateTime ≤ ts_open(t)` (rezerva jednoho baru proti minutové přesnosti kalendáře; vydání uvnitř baru t se použije až v baru t+1). `Forecast` se samostatně nepoužívá (dataset neuchovává historii revizí, hodnota mohla být revidovaná po vydání), jen uvnitř `surprise_z` po vydání. Poskytovatel, který vrátí vydání s `DateTime > ts`, → `LookaheadNewsError`.

**Stav `state.news`** (null, když poskytovatel chybí, selhala kontrola pásma nebo je bar po konci dat; horizont `news_horizon_min` = 1 440 min):

| Pole | Typ | Definice |
|---|---|---|
| `next_event_min` | float nebo null | minuty od `ts_close(t)` do nejbližší naplánované události s `DateTime ≥ ts_close(t)`; null, není-li do horizontu |
| `next_event_impact`, `next_event_name` | enum / str nebo null | její dopad a název |
| `last_event_min` | float nebo null | minuty od poslední události s `DateTime < ts_close(t)` do `ts_close(t)` (může ležet uvnitř baru t); null, není-li do horizontu zpět |
| `last_event_impact`, `last_event_name` | enum / str nebo null | |
| `last_surprise_z`, `last_surprise_missing` | float nebo null, bool nebo null | z posledního **použitelného** vydání (`DateTime ≤ ts_open(t)`) do horizontu zpět |
| `in_news_window` | bool | `next_event_min ≤ news_pre_min` (výchozí 5) nebo `last_event_min ≤ news_post_min` (výchozí 15) |
| `in_high_impact_window` | bool | totéž jen pro události s `Impact = High` |

Použití: 13.6 členění, 15.5 rysy, robustnost 13.11 s kalendářem i bez něj (jen pro D). Brána 13.2.1 zahrnuje i poskytovatele zpráv.

## 4. Normalizace a osy

### 4.1 ATR

- `TR(t) = max(high_t − low_t, |high_t − close_{t−1}|, |low_t − close_{t−1}|)`; pro první bar řady a pro první bar session (3.2) `TR(t) = high_t − low_t` (mezera přes hranici session se do TR nepočítá; mezera uvnitř session, např. po haltu, se počítá, protože jde o skutečný pohyb).
- `atr1(t)` = aritmetický průměr `TR` přes bary `t − atr_n + 1 … t` (výchozí `atr_n = 30`), v bodech ceny. Přeskočené bary (3.1) se nepočítají.
- **Podlaha:** `atr1(t) = max(atr1(t), atr_floor_ticks × tick_size)`, výchozí `atr_floor_ticks = 2`. Důvod: plochý trh (30 barů `high == low`) by dal nulový práh a dělení nulou.
- **Referenční hodnota pro prahy:** `atr_ref(t) = atr1(t − 1)`. Každý práh nebo normalizace, které se aplikují na bar t (θ, θ_pb, ε, δ, `level_tol`, `dist_*_atr`, `slope_norm`), používají `atr_ref(t)`; bar t tak neovlivňuje práh, kterým je sám posuzován (dodatek zadavatele). U veličin uložených „v čase extrému“ (5.4) se ukládá `atr_ref(t_ext)`.
- **Studený start (warmup):** `atr1(t)` existuje od baru `t = atr_n − 1` (prvních `atr_n` barů), `atr_ref(t)` od baru `t = atr_n`. Bary `t ≤ atr_n − 1` jsou warmup: `warmup = true`, zigzag neběží, stav je `phase = NONE`, `direction = NONE`, všechna ostatní pole null (`atr1` se v baru `atr_n − 1` už vyplní). První bar, ve kterém zigzag běží, je bar s indexem `atr_n`. Po `reset()` začíná warmup znovu.
- Všechny prahy a metriky jsou v násobcích `atr_ref`. Důvod: systém pracuje se swingy o velikosti jednotek bodů na 1min grafu; denní ATR je o řád hrubší.

### 4.2 Osa x

Osa x = pořadové číslo platného baru v řadě (`bar_index`, 0-based, bez doplňování prázdných minut, přeskočené bary index nedostávají). Sklon = cena / bar. Odpovídá tomu, jak trader kreslí TL na grafu; u 1min barů uvnitř session totožné s cenou za minutu, přes mezery a hranice session se čas neprodlužuje. Časové údaje (`duration_min`, `ts_*`) jsou vždy z timestampů, ne z indexů.

### 4.3 Směrové zarovnání

Popis v 5–8 je pro uptrend; downtrend je zrcadlový (swing high ↔ swing low, HH ↔ LL, HL ↔ LH, „nad“ ↔ „pod“, „<“ ↔ „>“). Implementace: řada `p' = −p` (open, high, low, close, extrémy, úrovně, hodnoty TL) prochází týmž kódem jako uptrend; výstupní ceny se převedou zpět (`× −1`), znaménkové metriky zůstávají v souřadnicích směru trendu. Znaménkové metriky (kladná = ve prospěch trendu): `slope_norm_*`, `slope_ratio`, `dist_to_tl_atr_*`, `dist_to_level_atr`, `dist_to_next_level_atr`, `tl_max_dev_atr_*`, `pb_depth_atr` (kladná = pullback proti trendu), `reg_slope_t` (15.2). Bezznaménkové: `er`, `r2`, počty, délky, `strength`.

### 4.4 Režim kotev

`anchor_mode ∈ {body, wick, close}`, výchozí `body`:

| Režim | `ext_high(t)` | `ext_low(t)` |
|---|---|---|
| `body` | `max(open_t, close_t)` | `min(open_t, close_t)` |
| `wick` | `high_t` | `low_t` |
| `close` | `close_t` | `close_t` |

Extrémy podle `anchor_mode` se používají pro zigzag (5), kotvy TL a pseudokotvy (6.2), běžící maximum `H` a hloubku pullbacku (7.4) a `tl_max_dev_atr` (8.1). **Prolomení (6.5), konec struktury (6.1) a vstupní podmínky fází (7) používají vždy `close`**, nezávisle na režimu. Důvod režimu `body`: systém považuje dlouhé knoty za dočasnou paniku bez významu a TL kreslí tam, kde se cena pohybovala nejvíce (kapitola I.3).

### 4.5 Porovnávání cen

Ceny jsou násobky ticku, hodnoty TL nikoli. Všechna porovnání cen a hodnot TL v tomto dokumentu jsou **v ticích s tolerancí půl ticku**:

- `a >ₜ b` ⇔ `a − b > 0,5 × tick_size`,
- `a <ₜ b` ⇔ `b − a > 0,5 × tick_size`,
- `a =ₜ b` ⇔ `|a − b| ≤ 0,5 × tick_size`,
- `a ≥ₜ b` ⇔ ne `a <ₜ b`; `a ≤ₜ b` ⇔ ne `a >ₜ b`.

Zápisy `<`, `>`, `≤`, `≥`, `=` u cen v sekcích 5–9 znamenají tyto operace. Porovnání v násobcích ATR (`x ≥ θ × atr_ref`) se provádí přímo v plovoucí čárce bez tolerance (obě strany jsou spojité veličiny). Rovnost sklonů TL: dvě přímky jsou shodné, pokud se jejich hodnoty v aktuálním baru liší o ≤ 0,5 ticku a jejich sklony o ≤ 0,5 ticku na 1 000 barů.

## 5. Swingy

### 5.1 Princip

- Zigzag s prahem θ × `atr_ref` (výchozí θ = 3, kalibruje se, viz 12). Jeden zigzag pro oba směry (swingy se střídají high, low, high, …).
- Kandidát extrému se průběžně posouvá; spolu s ním se ukládá `atr_ref(t_kandidát)`. Potvrzení = návrat ceny od kandidáta o `θ × atr_ref(t_kandidát)`. Změna ATR bez pohybu ceny tak swing nepotvrdí.
- Potvrzený swing se zpětně nemění. Stav v čase t používá jen swingy s `t_conf ≤ t`.

### 5.2 Stav zigzagu

| Proměnná | Význam |
|---|---|
| `dir` | `UNDEF` (před prvním swingem), `UP` (hledá se swing high, poslední potvrzený je low), `DOWN` (hledá se swing low) |
| `cand_hi`, `cand_hi_t`, `cand_hi_atr` | kandidát swing high: cena `ext_high`, index baru, `atr_ref` v jeho baru |
| `cand_lo`, `cand_lo_t`, `cand_lo_atr` | kandidát swing low |
| `swings` | seznam potvrzených swingů v pořadí potvrzení |

Inicializace v prvním baru po warmupu (`t0 = atr_n`): `dir = UNDEF`, `cand_hi = ext_high(t0)`, `cand_lo = ext_low(t0)`, oba s `t = t0` a `atr = atr_ref(t0)`.

### 5.3 Pořadí uvnitř baru

Bar t nese dvě zprávy: `ext_high(t)` a `ext_low(t)`. Pořadí, v jakém nastaly, určuje:

1. **1s data k dispozici** (`intrabar_mode = auto`, 3.4): pořadí = pořadí, v jakém sekundové bary poprvé dosáhly `ext_high(t)` a `ext_low(t)` (u režimu `body` se hledá první sekundový bar, jehož close ≥ `ext_high(t)`, resp. ≤ `ext_low(t)`; u `wick` high/low; u `close` je jen jedna zpráva). Pokud to 1s data neurčí (obě hodnoty v téže sekundě), použije se heuristika.
2. **Heuristika** (bez 1s dat): `close_t ≥ open_t` (býčí nebo doji) → nejdřív low, pak high; `close_t < open_t` (medvědí) → nejdřív high, pak low.

`intrabar_ambiguous(t) = true`, pokud v baru t mohlo pořadí změnit výsledek: tj. pokud by zpracování v opačném pořadí dalo jiný seznam potvrzených swingů nebo jiné kandidáty. Implementace to zjistí tak, že bar zpracuje v obou pořadích nad kopií stavu a porovná výsledek; příznak je součástí stavu (10.3) a testu 13.2.7.

### 5.4 Algoritmus (bar t, po warmupu)

Zprávy se zpracují v pořadí z 5.3; každá zpráva je buď `HIGH(p = ext_high(t))`, nebo `LOW(p = ext_low(t))`.

```
proces_zprávy(HIGH, p, t):
  if dir in (UNDEF, UP):
     if p > cand_hi:                         # tick-strict; rovnost nechává starší bar
        cand_hi, cand_hi_t, cand_hi_atr = p, t, atr_ref(t)
  if dir in (UNDEF, DOWN):
     if p − cand_lo ≥ θ × cand_lo_atr:      # návrat od kandidáta low o θ
        potvrď swing LOW (price=cand_lo, t_ext=cand_lo_t, t_conf=t, atr_ext=cand_lo_atr)
        dir = UP
        cand_hi, cand_hi_t, cand_hi_atr = p, t, atr_ref(t)

proces_zprávy(LOW, p, t):
  if dir in (UNDEF, DOWN):
     if p < cand_lo:
        cand_lo, cand_lo_t, cand_lo_atr = p, t, atr_ref(t)
  if dir in (UNDEF, UP):
     if cand_hi − p ≥ θ × cand_hi_atr:
        potvrď swing HIGH (price=cand_hi, t_ext=cand_hi_t, t_conf=t, atr_ext=cand_hi_atr)
        dir = DOWN
        cand_lo, cand_lo_t, cand_lo_atr = p, t, atr_ref(t)
```

Pravidla:

- Při `dir = UNDEF` se sledují oba kandidáti; první potvrzení určí `dir`. Potvrzení obou v témže baru (obrovský bar) řeší pořadí zpráv 5.3: druhá zpráva už pracuje s nastaveným `dir`.
- **Remíza ceny:** nový extrém se stejnou cenou (rovnost v ticích) kandidáta neposouvá; extrém zůstává na dřívějším baru. Důvod: determinismus a nejstarší dotyk hladiny.
- Po potvrzení swingu LOW v baru t je nový kandidát high `ext_high(t)` z téhož baru (bary mezi `cand_lo_t` a t měly nižší high, jinak by potvrdily dřív; přesněji: kandidát high v baru potvrzení je správný, protože potvrzující bar je první, který dosáhl `cand_lo + θ × atr`).
- Potvrzení a nový kandidát v témže baru jsou legitimní (bar s tělem ≥ θ × atr).
- Časy: `t_ext` i `t_conf` jsou indexy baru; `ts_ext = ts_open(t_ext)`, `ts_conf = ts_close(t_conf)`. Pokud jsou 1s data, `ts_ext_fine` = čas prvního sekundového baru, který dosáhl extrému, jinak null. `ts_ext_fine` se nikde v rozhodování nepoužívá.

### 5.5 Záznam swingu a událost

| Pole | Typ | Popis |
|---|---|---|
| `swing_id` | int | pořadové číslo od 0 v pořadí potvrzení |
| `kind` | HIGH / LOW | |
| `price` | float | `ext_*` v baru extrému podle `anchor_mode` |
| `t_ext`, `ts_ext`, `ts_ext_fine` | int, tz-aware, tz-aware nebo null | extrém |
| `t_conf`, `ts_conf` | int, tz-aware | potvrzení |
| `atr_ext` | float | `atr_ref(t_ext)` |
| `conf_delay_bars` | int | `t_conf − t_ext` |

Událost `SWING_CONFIRMED` v baru `t_conf` nese celý záznam. Swingy jsou globální (nezávislé na směru trendu); struktury 6.1 z nich vybírají.

### 5.6 Okrajové případy

- **Mezera přes session / víkend:** zigzag pokračuje bez resetu; skok ceny je běžná zpráva (extrém prvního baru po mezeře). Práh θ používá `atr_ref` uložený u kandidáta, mezera ho nemění.
- **Extrémně dlouhý knot:** v režimu `body` se knot ignoruje; v `wick` tvoří extrém. Bez zvláštního ošetření.
- **Plochý trh:** žádná zpráva nedosáhne θ × atr (atr má podlahu 4.1), swing se nepotvrdí; kandidáti se neposouvají při rovnosti.
- **Halt:** stejné jako mezera.
- **Den rollu:** back-adjusted řada, bez ošetření (3.3).

## 6. Trendline

Popis pro uptrend; downtrend zrcadlově (4.3). Struktury obou směrů se vedou nezávisle a současně nad týmiž swingy (5).

### 6.1 Struktura trendu

**Stupně swingů.** Zigzag dává swingy jednoho stupně; pullback v trendu může obsahovat vnitřní swingy téhož stupně (nižší high a nižší low uvnitř korekce). Struktura trendu proto nepracuje s posloupností „každý swing je HH nebo HL“, ale s **korekcemi** a jejich **přijatými low**:

| Pojem | Definice |
|---|---|
| `L₀` | začátek struktury: potvrzený swing low, od kterého struktura vzniká (6.1.1) |
| `H` (běžící maximum) | `max ext_high(x)` pro `x ∈ [t_L₀, t]`, s časem `t_H` prvního dosažení (rovnost v ticích nechává starší); aktualizuje se každý bar |
| korekce | úsek `[t_H, t_H')`, kde `t_H'` je první bar po `t_H`, ve kterém `ext_high(x) > H` (nové běžící maximum a začátek další korekce); korekce je **dokončená** barem `t_H'`, jinak **probíhající**. Každý bar `x ≥ t_L₀` patří právě do jedné korekce (té s největším `t_H ≤ x`); bar, který nastavil nové maximum, je prvním barem nové korekce |
| `prev_major_low` | nejnižší přijaté low poslední **dokončené** korekce, která nějaké přijaté low má; jinak `L₀` |
| přijaté low (`anchors`) | potvrzený swing low s `t_ext ≥ t_L₀`, `t_conf ≤ t`, jehož cena je `> prev_major_low` (v ticích) v okamžiku potvrzení; přijaté low se přiřadí korekci, do níž padá `t_ext` |
| hlavní high (`major_highs`) | potvrzený swing high s `t_ext ≥ t_L₀`, jehož cena `>` všechna dřívější hlavní high struktury (první hlavní high je první potvrzený swing high po `L₀`) |
| `n_anchors` | `1 + počet přijatých low` (L₀ se počítá) |

**Platnost.** Trend je **platný**, pokud `n_anchors ≥ 2` (mezi `L₀` a prvním přijatým low leží nutně swing high, protože se swingy střídají), hlavní TL má kladný sklon (6.2) a není prolomená (6.5). S jediným swing low TL nejde určit a trend je jen kandidát.

#### 6.1.1 Životní cyklus struktury (uptrend)

Vyhodnocuje se v každém baru po zigzagu (pořadí 6.7):

1. **Bez `L₀`** (stav NONE): první potvrzený swing low s `t_ext ≥ t_reset` (`t_reset` = index baru posledního `TREND_END` této strany, na začátku `t_reset = 0`) se stane `L₀`; událost `TREND_CANDIDATE`. `H` se inicializuje `ext_high(t_L₀)` a přepočítá přes bary `[t_L₀, t]`.
2. **Kandidát** (`n_anchors = 1`):
   - potvrzený swing low s cenou `≤ L₀.price` → nahradí `L₀` (nová `TREND_CANDIDATE`, `prev_major_low` = nové `L₀`, `H` přepočítat přes `[t_L₀, t]`),
   - `close_t < L₀.price` → `L₀ = None`, stav NONE (bez události; příští swing low je nový kandidát),
   - potvrzený swing low s cenou `> L₀.price` → přijaté low, `n_anchors = 2`, trend platný (pokud sklon > 0), událost `TREND_START` (nese `L₀`, první kotvu, TL).
3. **Platný nebo prolomený** (`n_anchors ≥ 2`): při každém potvrzeném swing low s `t_ext ≥ t_L₀`:
   - cena `> prev_major_low` → přijaté low; přepočet hlavní TL (6.2) a aktuální TL (6.3),
   - cena `≤ prev_major_low` → `TREND_END` s `reason = LL_SWING` (nastává jen při mezeře v otevření, jinak dřív zafunguje pravidlo close),
   - `close_t < prev_major_low` (v ticích) → `TREND_END` s `reason = STRUCTURE`.
4. **Konec** (`TREND_END`): fáze `ENDED` v tomto baru, `t_reset = t`, struktura se zahodí (`L₀ = None`, kotvy, TL, pullback), od příštího baru NONE. Přijatá low a swingy zůstávají v globálním seznamu swingů (5.5); nová struktura začíná prvním swing low s `t_ext ≥ t_reset`.
5. **Dokončení korekce** (bar, kde `ext_high(t) > H`): `prev_major_low` := nejnižší přijaté low právě dokončené korekce (té s dosavadním `t_H`; existuje-li takové low), pak `H := ext_high(t)`, `t_H := t` (začátek nové korekce). Pořadí uvnitř baru: nejdřív se posoudí konec pullbacku se starým `H` (7.4), potom se nastaví nové `H`, potom se posoudí případný nový začátek pullbacku podle pořadí zpráv 5.3 (u medvědího baru je high dřív než low, takže nový pullback může začít v témže baru).

Poznámka k pravidlu 3: vnitřní low korekce (druhé, nižší low uvnitř téže korekce) je přijaté, pokud je nad `prev_major_low`; hlavní TL se pak přepočítá s nižším sklonem (překreslení). Vnitřní low se tedy nepovažuje za LL, i když je pod předchozím přijatým low téže korekce. To je rozhodnutí D-8 (soulad s kapitolou I.3: TL se táhne od začátku trendu přes low, které cena respektuje).

### 6.2 Hlavní TL

- **Kotvy** = `L₀` a všechna přijatá low (`anchors`), plus **pseudokotvy** (níže).
- **Přímka:** z `L₀` s nejmenším sklonem ke kterékoli jiné kotvě nebo pseudokotvě (hrana dolní konvexní obálky začínající v `L₀`): `slope = min over a ∈ A \ {L₀} of (a.price − L₀.price) / (a.t − L₀.t)`; `intercept` z `L₀`. Všechny kotvy leží na TL nebo nad ní. Druhá kotva (`anchor2`) = kotva, která dává minimum; **remíza** (dvě kotvy se shodným sklonem podle 4.5) → pozdější kotva.
- **Tolerance ε** (výchozí 0,5 × `atr_ref`, 12): extrémy `ext_low(x)` barů mezi `L₀` a aktuálním barem smí TL podkročit nejvýše o `ε × atr_ref(x)`. Knoty se v režimu `body` nekontrolují.
- **Pseudokotvy:** bar, jehož `ext_low(x) < TL(x) − ε × atr_ref(x)`, se do množiny kotev přidá jako pseudokotva `(x, ext_low(x))`, protože trader by TL vedl pod ním. Algoritmus přepočtu (při každém přijetí low a při `TREND_START`):

```
přepočet_hlavní_TL(t):
  A = {L₀} ∪ anchors ∪ pseudo_anchors
  loop:
     (slope, anchor2) = min_slope(A)                # 6.2 přímka
     worst = argmax over x in (t_L₀, t] of (TL(x) − ext_low(x)) / atr_ref(x)
     if worst existuje and (TL(worst) − ext_low(worst)) > ε × atr_ref(worst):
         pseudo_anchors.add((worst, ext_low(worst)))
         A.add(...)
         continue
     break
  if slope ≤ 0: tl_valid = False (fáze TL_BROKEN, reason NONPOSITIVE_SLOPE), jinak tl_valid = True
  if přímka se změnila proti minulé (4.5): událost TL_UPDATE (stará i nová přímka, důvod: NEW_ANCHOR | PSEUDO_ANCHOR)
```

  Smyčka skončí, protože každá iterace přidá bod pod aktuální přímkou a sklon klesá; bod na obálce už podkročit nemůže. Složitost `O(délka trendu × počet iterací)` na jedno přijetí; iterací je typicky 0–2.

- Přepočet se dělá **jen** při přijetí low (a při `TREND_START`), nikdy v jiných barech; mezi přepočty se TL nemění a testuje se prolomení (6.5). Těsně po přepočtu není TL prolomená (žádný `ext_low` v `(t_L₀, t]` není pod TL − ε a `close ≥ ext_low`).
- `TL_UPDATE` vzniká jen, když se přímka změní; přijetí low nad stávající TL, které obálku nemění, událost nevyvolá (nová kotva se ale do `anchors` zapíše).

### 6.3 Aktuální TL

- **Kandidát** vzniká při každém přijetí low, pokud existují ≥ 2 přijatá low: přímka přes **poslední dvě přijatá low** (pseudokotvy se nepoužívají), `a1` starší, `a2` novější.
- **Tolerance:** pro všechna `x ∈ (a1.t, t]` musí platit `ext_low(x) ≥ cand(x) − ε × atr_ref(x)`; jinak kandidát neplatí (žádná událost).
- **Poměr sklonů** `r = slope_cand / slope_main` (obě kladné; při `slope_main ≤ 0` se kandidát nevyhodnocuje). Kandidát se stane aktuální TL, pokud `r ≥ ratio_steep` (výchozí 1,5) nebo `r ≤ ratio_flat` (výchozí 0,67, tj. 1/1,5). Událost `CURR_TL_NEW` (nese obě kotvy, sklon, `r`).
- **Hystereze:** platná aktuální TL zůstává, dokud není prolomená (6.5) nebo nahrazená novým kandidátem, který poměr splní; kandidát, který poměr nesplní, ji neruší. Změna hlavní TL (`TL_UPDATE`) aktuální TL neruší; pokud se po změně obě přímky shodují (4.5), je `curr_is_main = true`.
- **Bez aktuální TL:** `curr_tl` = hlavní TL, `curr_is_main = true`. Po prolomení aktuální TL při neprolomené hlavní: `curr_tl = main_tl` až do dalšího kandidáta; událost `CURR_TL_DROP` s `reason = BREAK`. Při `TREND_END` zaniká bez události (stačí `TREND_END`).
- Kapitola I.4: strmější pohyb není podmínka; kandidát pozvolnějšího pokračování (`r ≤ ratio_flat`) je rovnocenný.

### 6.4 Projekce

`value_at(x)` vrací hodnotu hlavní i aktuální TL pro libovolný `bar_index` x (int; i budoucí `x > t`), `value = intercept + slope × (x − anchor1.t)` v bodech ceny (u hlavní TL `anchor1 = L₀`, u aktuální TL starší z dvojice kotev; `intercept` = cena `anchor1`; u downtrendu převedeno zpět). Slouží spotřebiteli pro vstupní zóny, SL:B a výstup OUT:B. Stav nese `bar_index` aktuálního baru, aby spotřebitel mohl adresovat budoucí bary `bar_index + n`. Pro `x < L₀.t` vrací hodnotu extrapolace (bez omezení), spotřebitel ji nemá používat.

### 6.5 Prolomení

- **Prolomení TL:** `close_t < TL(t) − ε × atr_ref(t)` (v ticích), pro hlavní i aktuální TL zvlášť, v každém baru mezi přepočty. Událost `TL_BREAK` s `which ∈ {MAIN, CURR}`, `tl_value`, `close`, `depth_atr = (TL(t) − close_t)/atr_ref(t)`. Událost vzniká jen při **přechodu** (první bar prolomení); po dobu prolomení je `main_tl.broken = true` a další bary pod TL událost neopakují.
- **Hlavní TL:** po prolomení je trend neobchodovatelný, fáze `TL_BROKEN` (pravidlo 1 vyžaduje trend určený TL). `H` se dál aktualizuje; nová maxima fázi nemění. Prolomení se ruší jen přepočtem TL při přijetí nového low (6.2): pokud po přepočtu `close_t ≥ TL(t) − ε` (po přepočtu vždy), `broken = false`, událost `TL_REVALIDATED`, fáze podle 7. Bez přijatého low se TL neobnoví, ani když cena vystoupí zpět nad ni (trader nemá novou kotvu).
- **Aktuální TL:** prolomení fázi nemění (7.4), jen `CURR_TL_DROP`.
- **Prolomení struktury:** `close_t < prev_major_low` → `TREND_END` (6.1.1). Priorita v témže baru: `TREND_END` má přednost před `TL_BREAK` (obojí se zaznamená v pořadí `TL_BREAK`, `TREND_END`, fáze je `ENDED`).

### 6.6 Sklon a pravidlo 45°

- `slope_norm_main(t) = slope_main / atr_ref(t)`, `slope_norm_curr(t)` obdobně; jednotka `atr_ref` na bar; přepočítává se každý bar (sklon přímky je konstantní, normalizace ne). `slope_ratio = slope_curr / slope_main` (1, když `curr_is_main`).
- Úhel na grafu závisí na měřítku osy ceny a šířce baru, takže „45°“ bez měřítka nemá číselnou hodnotu (obrázky z chartbooků měřené ve vlastním měřítku dávají u obchodů autora úhly 9°–56°, sklony 0,05–0,5 bodu/min; `PAT_obchody_z_obrazku.csv`). Komponenta vrací `slope_norm_*`; filtr `min_slope` je parametr, výchozí vypnutý (null).
- `slope_ok_main = (min_slope is null) or (slope_norm_main ≥ min_slope)`; `slope_ok_curr` obdobně. Je-li filtr zapnut, `trend_valid` vyžaduje `slope_ok_main` (7.2); fáze se filtrem nemění.
- Hodnota `min_slope` odpovídající 45° se určí kalibrací (12.3).

### 6.7 Pořadí vyhodnocení v baru

Pro každý platný bar t (po warmupu), v tomto pořadí; každý krok vidí výsledky předchozích:

1. validace baru (3.1), `atr1(t)`, `atr_ref(t)`, session, roll, mezera,
2. načtení aktivních úrovní `levels_at(ts_open(t))`,
3. zigzag: zprávy HIGH/LOW v pořadí 5.3 → potvrzené swingy (`SWING_CONFIRMED`),
4. pro každou stranu (UP, DOWN) v tomto pořadí UP, DOWN:
   a. struktura 6.1.1 (nový kandidát, přijetí low, `TREND_END` podle LL_SWING),
   b. konec pullbacku se starým `H`, dokončení korekce, nové `H` (6.1.1 krok 5),
   c. přepočet hlavní TL (jen při přijetí low) a kandidát aktuální TL,
   d. prolomení hlavní a aktuální TL (6.5), konec struktury podle close (`TREND_END` STRUCTURE),
   e. začátek pullbacku (7.4),
   f. fáze (7.1), `trend_valid`, pullback pole, kvalita (8.1), PW-SW (8.2), síla (8.3),
5. `direction` (7.3), detektor B (15.2), kalendář zpráv (3.9), tabulka pokračování (15.4), modul delta (9), doplňkové detektory (15.6), `answer` (1.1),
6. zápis stavu a událostí baru; události nesou `t_known = t`.

Události jednoho baru se vydávají v pořadí vzniku podle tohoto seznamu.

## 7. Stav trendu a pullbacku

Stav se vede pro každý směr zvlášť (`up`, `down`); uptrend a downtrend mohou existovat současně (např. při přechodu trendu). Popis pro uptrend.

### 7.1 Fáze

Fáze se určí po krocích 6.7 4a–4e první splněnou podmínkou v tomto pořadí:

| Pořadí | Fáze | Vstupní podmínka (uptrend) | Výstup z fáze |
|---|---|---|---|
| 1 | `ENDED` | v tomto baru nastal `TREND_END` | vždy jen jeden bar; další bar → `NONE` |
| 2 | `NONE` | `L₀` neexistuje | potvrzení swing low → `CANDIDATE` |
| 3 | `CANDIDATE` | `L₀` existuje, `n_anchors = 1` | přijaté low → platná (4–6); `close < L₀` → `NONE`; nižší swing low → `CANDIDATE` s novým `L₀` |
| 4 | `TL_BROKEN` | `n_anchors ≥ 2` a (`main_tl.broken` nebo `slope_main ≤ 0`) | přijaté low s přepočtem, po němž TL není prolomená a má kladný sklon → 5/6 (`TL_REVALIDATED`); `close < prev_major_low` → `ENDED` |
| 5 | `PULLBACK` | `n_anchors ≥ 2`, TL neprolomená, pullback aktivní (7.4) | `ext_high > H` → `IMPULSE` (`PULLBACK_END_UP`); prolomení hlavní TL → `TL_BROKEN`; konec struktury → `ENDED` (obojí `PULLBACK_END_DOWN`) |
| 6 | `IMPULSE` | `n_anchors ≥ 2`, TL neprolomená, pullback neaktivní | začátek pullbacku → `PULLBACK`; prolomení → `TL_BROKEN`; konec → `ENDED` |

Podmínky se nepřekrývají (pořadí je rozhodující) a pokrývají všechny kombinace (`L₀` ne/existuje × `n_anchors` × prolomení × pullback).

### 7.2 `trend_valid`

`trend_valid = phase ∈ {IMPULSE, PULLBACK} and slope_ok_main` (6.6). Ve fázi `TL_BROKEN` je `trend_valid = false`, i když struktura trvá (pravidlo 1).

### 7.3 `direction`

| Situace | `direction` |
|---|---|
| `up.trend_valid` a ne `down.trend_valid` | `UP` |
| `down.trend_valid` a ne `up.trend_valid` | `DOWN` |
| obě platné | strana s novějším `L₀` (`t_L₀` větší); remíza → strana s novějším posledním přijatým low; další remíza → `UP` |
| žádná platná | `NONE` |

`direction_phase` = fáze strany `direction` (null při `NONE`). Stav obou stran je vždy k dispozici celý (10.3).

### 7.4 Pullback

- **Začátek:** v baru t, kde po krocích 6.7 4a–4d platí `n_anchors ≥ 2`, hlavní TL má kladný sklon a není prolomená (tj. fáze bude `IMPULSE` nebo `PULLBACK`), pullback není aktivní a `H − ext_low(t) ≥ θ_pb × atr_ref(t_H)`. Pullback tak může začít i v baru `TREND_START` (korekce od prvního hlavního high byla hlubší než θ_pb a ještě neskončila). `θ_pb = θ` (výchozí), takže při `body`/`wick` režimu začátek pullbacku zpravidla splývá s barem potvrzení swing high v `H`; při `θ_pb < θ` může pullback začít dřív, než je `H` potvrzený swing. `H` je vždy běžící maximum (6.1), ne nutně potvrzený swing. Událost `PULLBACK_START` (`pb_id`, `H`, `t_H`, `t_start = t`, `restart`).
- **Konec nahoru:** první bar, kde `ext_high(t) > H` (posuzuje se se starým `H`, 6.1.1 krok 5) → `PULLBACK_END_UP` (`pb_id`, `bars`, `pb_low`, `outcome = RESUMED`), fáze `IMPULSE`.
- **Konec dolů:** přechod do `TL_BROKEN` nebo `ENDED` → `PULLBACK_END_DOWN` (`pb_id`, `reason ∈ {TL_BREAK, STRUCTURE}`), pullback neaktivní.
- **Restart:** po `TL_REVALIDATED`, je-li v témže baru stále `H − ext_low(t) ≥ θ_pb × atr_ref(t_H)` a `ext_high(t) ≤ H`, začne nový pullback s `restart = true` a stejným `H`; nese `pb_id` nový, `parent_pb_id` = původní. Testy 13.4 hodnotí jen pullbacky s `restart = false`.
- Prolomení aktuální TL během pullbacku fázi nemění, jen se zaznamená `TL_BREAK` aktuální TL a `CURR_TL_DROP`.
- Pullback v `CANDIDATE` fázi neexistuje (trend není platný); běžící `H` se ale vede od `t_L₀`.

**Pole `pullback`** (null, když pullback není aktivní; u `pb_low`, `pb_depth_atr`, `pb_retrace` se počítá z barů `[t_H, t]`):

| Pole | Typ | Definice |
|---|---|---|
| `pb_id`, `parent_pb_id`, `restart` | int, int nebo null, bool | identifikace |
| `H`, `t_H`, `ts_H` | float, int, tz-aware | běžící maximum, od kterého pullback jde |
| `t_start`, `bars` | int, int | bar začátku; `bars = t − t_start + 1` |
| `pb_low`, `t_pb_low` | float, int | `min ext_low(x)` pro `x ∈ [t_H, t]` (rovnost nechává starší) |
| `pb_depth_atr` | float | `(H − pb_low) / atr_ref(t_H)` |
| `pb_retrace` | float | `(H − pb_low) / (H − prev_major_low)`; jmenovatel je > 0, protože `H > prev_major_low` |
| `n_inner_swings` | int | počet potvrzených swingů (obou typů) s `t_ext > t_H` a `t_conf ≤ t` |
| `dist_to_tl_atr_main`, `dist_to_tl_atr_curr` | float | `(close_t − TL(t)) / atr_ref(t)`; kladná = nad TL (počítá se i mimo pullback jako pole TL, 10.3) |
| `dist_to_level_atr` | float nebo null | vzdálenost close k nejbližší aktivní úrovni **na straně, ke které pullback míří** (uptrend: `price ≤ close`; nejbližší = největší taková cena): `(close − price)/atr_ref(t)`; null, když taková úroveň není nebo `levels_missing` |
| `stopped_at_level` | bool nebo null | existuje aktivní úroveň `L` s `|pb_low − L.price| ≤ level_tol × atr_ref(t)`; null při `levels_missing` |

`answer.pullback_active = (phase == PULLBACK)`; `answer.pullback_starting = pullback_active and bars ≤ pb_start_window` (výchozí 3); `answer.pullback_age_bars = bars` nebo null. Pole `answer` se plní ze strany `direction`; při `direction = NONE` jsou `pullback_*` false/null.

### 7.5 Přechody a události (souhrn)

| Přechod | Událost(i) |
|---|---|
| NONE → CANDIDATE | `TREND_CANDIDATE` |
| CANDIDATE → CANDIDATE (nové `L₀`) | `TREND_CANDIDATE` |
| CANDIDATE → NONE | žádná (stav `L0 = null`) |
| CANDIDATE → IMPULSE / PULLBACK | `TREND_START`, případně `TL_UPDATE`, `PULLBACK_START` |
| IMPULSE → PULLBACK | `PULLBACK_START` |
| PULLBACK → IMPULSE | `PULLBACK_END_UP` |
| IMPULSE / PULLBACK → TL_BROKEN | `TL_BREAK(MAIN)`, u pullbacku `PULLBACK_END_DOWN(TL_BREAK)`, případně `CURR_TL_DROP` |
| TL_BROKEN → IMPULSE / PULLBACK | `TL_UPDATE`, `TL_REVALIDATED`, případně `PULLBACK_START(restart)` |
| kterákoli s `n_anchors ≥ 2` → ENDED | případně `PULLBACK_END_DOWN(STRUCTURE)`, `TREND_END(reason)` |
| ENDED → NONE | žádná |

## 8. Kvalita trendu

### 8.1 Metriky (úsek `L₀` → aktuální bar, směrově zarovnané)

Počítají se pro každou stranu s existujícím `L₀` (i ve fázi `CANDIDATE` a `TL_BROKEN`); bez `L₀` je celé pole `quality` null. Metriky závislé na TL jsou null při `n_anchors < 2`. Zkratky: `t₀ = t_L₀`, okno `W_T = [t₀, t]`.

| Metrika | Typ | Definice | Hodnota, když není definována |
|---|---|---|---|
| `slope_norm_main`, `slope_norm_curr` | float | 6.6 | null bez TL |
| `slope_ratio` | float | `slope_curr / slope_main`; > 1 zrychlení, < 1 zpomalení; 1 při `curr_is_main` | null bez TL |
| `er` | float 0–1 | Kaufman efficiency ratio přes `W_T`: `|close_t − close_{t₀}| / Σ_{i=t₀+1..t} |close_i − close_{i−1}|`, včetně skoků mezi session (tytéž bary v čitateli i jmenovateli); jmenovatel 0 → `er = 0` | 0 při `t = t₀` |
| `r2` | float 0–1 | koeficient determinace OLS regrese `price ~ t` přes `L₀` a přijatá low (bez pseudokotev) | null při `n_anchors < 3` |
| `n_hl`, `n_hh`, `n_swings` | int | počet přijatých low, počet hlavních high (6.1), `n_swings = n_hl + n_hh` | 0 |
| `duration_bars`, `duration_min` | int, float | `t − t₀`; `(ts_close(t) − ts_open(t₀))` v minutách (včetně mezer a nocí) | 0 |
| `tl_max_dev_atr_main`, `tl_max_dev_atr_curr` | float | `max_{x ∈ W_dev} (ext_high(x) − TL(x)) / atr_ref(x)` pro hlavní, resp. aktuální TL, kde `W_dev = [t_last_anchor, t]` a `t_last_anchor` = `t_ext` posledního přijatého low (nebo `t₀`, když žádné není); měří odklon poslední vlny od TL (PW2) | null bez TL |
| `tl_max_dev_atr_trend` | float | totéž přes celé `W_T` pro hlavní TL (informativní) | null bez TL |
| `tl_dev_atr_now` | float | `(ext_high(t) − TL_curr(t)) / atr_ref(t)` | null bez TL |
| `levels_crossed` | int | počet různých `level_id`, které byly od `t₀` proraženy closem ve směru trendu: úroveň `L` aktivní v baru `x ∈ (t₀, t]` je proražena v x, pokud `close_{x−1} ≤ L.price < close_x` (uptrend, v ticích); každé `level_id` nejvýš jednou | null při `levels_missing` po celý úsek; 0, když úrovně jsou, ale nic proraženo |
| `dist_to_next_level_atr` | float | nejbližší aktivní úroveň s `price > close_t`: `(price − close_t)/atr_ref(t)` | null, když taková není nebo `levels_missing` |
| `anchors_on_level` | float 0–1 | podíl kotev (`L₀` + přijatá low), jejichž cena je u úrovně aktivní v baru `t_ext` kotvy (tolerance `level_tol × atr_ref(t_ext)`) | null při `levels_missing` |
| `L0_on_level` | bool | `L₀` u úrovně aktivní v `t₀` | null při `levels_missing` |
| `levels_missing` | bool | v baru t není aktivní žádná úroveň (3.5) | — |
| `session_cross` | bool | `session_id(t) ≠ session_id(t₀)` | — |
| `roll_in_structure` | bool | v `(t₀, t]` leží bar rollu (3.3) | — |
| `gap_in_structure` | bool | existuje `x ∈ (t₀, t]` se `session_id(x) = session_id(x−1)` a `ts_open(x) − ts_close(x−1) ≥ gap_min` minut (výchozí 5) | — |

### 8.2 Filtry PW-SW (kapitola VIII)

Filtry se počítají v každém baru pro stranu s `L₀`; null znamená „nelze posoudit“. Swingy pro PW1 jsou **všechny potvrzené swingy** zigzagu (5) s `t_ext ≥ t₀` a `t_conf ≤ t` (včetně vnitřních swingů korekcí), ne jen přijatá low; důvod: P.A.T. posuzuje swingové vlny před vstupní zónou bez ohledu na stupeň.

- **PW1 (H/L swingů v souladu s trendem):**
  - `pw1_trend_side`: posledních `pw1_n` (výchozí 3) swing low je ostře rostoucích (v ticích) v pořadí `t_ext`; je-li k dispozici jen 2, posoudí se 2; při < 2 → null.
  - `pw1_counter_side`: `false`, pokud posledních `pw1_counter_n + 1` (výchozí 2 + 1 = 3) swing high tvoří ostře klesající posloupnost (≥ `pw1_counter_n` po sobě jdoucích nižších high, tj. protitrendová struktura); `true`, pokud ne nebo pokud je swing high méně než `pw1_counter_n + 1`. Tato část je interpretace ilustrace v kapitole VIII (v downtrendu autor varuje před rostoucími low); ověřit kalibrací (12.3).
- **PW2 (trh stále poblíž aktuální TL):** `pw2_curr = tl_max_dev_atr_curr ≤ δ`, `pw2_main = tl_max_dev_atr_main ≤ δ` (výchozí δ = 3); `pw2 = pw2_curr` (obrázek v kapitole VIII mluví o aktuální TL; při `curr_is_main` jsou shodné). null bez TL.
- **PW3 (žádný náznak chopu):** `ER20(i) = |close_i − close_{i−20}| / Σ_{j=i−19..i} |close_j − close_{j−1}|` (jmenovatel 0 → 0); bar i je **chop bar**, pokud `ER20(i) < er_chop` (výchozí 0,25) **a** close_i není u žádné úrovně aktivní v baru i (tolerance `level_tol × atr_ref(i)`; při `levels_missing` v baru i se podmínka o úrovni vynechá). `chop_bars` = počet chop barů v `[t − W + 1, t]` (výchozí W = 60); bary s indexem < max(20, `atr_n`) nemají ER20 nebo `atr_ref` a nepočítají se. `pw3 = chop_bars < pw3_max` (výchozí 30). Vyloučení barů u úrovně odpovídá „chvilkové zdržení na S/R je v pořádku“.
- `reversal_hint = not (pw1_trend_side and pw1_counter_side and pw2 and pw3)`, kde null se bere jako `true` (nelze posoudit → nepenalizuje); `reversal_hint = null`, jsou-li všechny čtyři null. Spotřebitel, který chce přísnější chování, má jednotlivá pole k dispozici.

Výchozí hodnoty δ, W a prahů ER jsou odhady; kalibrují se (12.3).

### 8.3 Síla trendu (`answer.strength`)

Předpoklad s kalibrací (D-24). Složky, každá v [0, 1], se počítají pro stranu `direction`:

- `s_er = er` (8.1),
- `s_dev = 1 − min(1, tl_max_dev_atr_curr / (2 × δ))`,
- `s_slope = min(1, slope_norm_curr / slope_ref)`, `slope_ref` výchozí 0,2 atr/bar (kalibrace: medián `slope_norm_main` platných trendů na vývojovém období, 12.3).

`strength` = aritmetický průměr definovaných složek; null, jsou-li všechny null nebo `direction = NONE`.

`strength_class`: `STRONG`, pokud `strength ≥ 0,6` a `reversal_hint` není `true`; `WEAK`, pokud `strength < 0,3` nebo `reversal_hint = true`; jinak `MEDIUM`; null při `strength = null`. Kalibrační kontrola (13.7): úspěšnost pokračování (13.4) musí být na vývojovém období monotónní `STRONG > MEDIUM > WEAK`; jinak se prahy 0,6 / 0,3 posunou (zápis do logu) tak, aby monotonie platila a žádná třída neměla < 10 % barů s platným trendem.

## 9. Modul cumulative delta (volitelný, kapitola IX)

- **Vstup:** sloupec `delta` (3.1) = kumulativní delta (Σ(ask objem − bid objem) od začátku session) na konci baru. Modul je aktivní, jen když je sloupec přítomen a `delta_enabled = true` (výchozí `true`); jinak jsou všechna pole modulu null. Delta se na začátku každé session resetuje na 0 (kumulace jen uvnitř session); pokud vstup kumuluje přes session, komponenta ho převede odečtením hodnoty na konci předchozí session (parametr `delta_cumulates_across_sessions`, výchozí `false`).
- **Řada delty jako „cena“:** `open = delta_{t−1}` (0 na začátku session), `close = delta_t`, `high = max(open, close)`, `low = min(open, close)`; `anchor_mode` pro deltu je vždy `close`. `atr_delta(t)` = průměr `|delta_t − delta_{t−1}|` přes `atr_n` barů s podlahou 1 kontrakt; `atr_delta_ref(t) = atr_delta(t−1)`.
- Nad touto řadou běží tentýž zigzag (5) s prahem `θ_delta × atr_delta_ref` (`θ_delta = θ`) a tatáž struktura a TL (6) s `ε_delta = ε`, nezávisle na cenové struktuře (druhá instance téhož kódu).
- `delta_tl_agrees` (bool): strana `direction` má na deltě strukturu s `trend_valid = true` (TL téhož směru existuje a není prolomená). null při `direction = NONE`.
- `delta_divergence` (bool): pro poslední dvě přijatá low cenové struktury `L_{k−1}`, `L_k` (uptrend): `D(L) = min delta_low(x)` pro `x ∈ [t_ext(L) − 2, t_ext(L) + 2] ∩ [t₀, t]`; divergence, pokud `D(L_k) ≤ D(L_{k−1}) + ε × atr_delta_ref(t)`. null při `n_hl < 2`. V downtrendu zrcadlově (high a max).
- **Den rollu:** v session obsahující bar rollu jsou obě pole null (objem je rozdělen mezi dva kontrakty) a delta struktura se na jejím konci resetuje.
- Vyžaduje bid/ask objem; zda jej export obsahuje, není známo (R1 v 3.8).

## 10. Rozhraní

### 10.1 Volání

Jazyk: Python ≥ 3.11; povinné závislosti jen `numpy` a `pandas` (dávkový režim); vše ostatní volitelné.

```python
engine = TrendEngine(params, session_calendar, roll_dates,
                     levels=None,            # LevelProvider (3.5) nebo None = bez úrovní
                     intrabar=None,          # IntrabarProvider (3.4) nebo None
                     news=None,              # NewsProvider (3.9) nebo None
                     continuation_table=None,# cesta k JSON (15.4) nebo None
                     detectors=("A", "B", "C"))  # aktivní detektory (1.3); "A" je vždy
state = engine.update(bar)          # streaming, volá se po uzavření baru; vrací TrendState
states, events = engine.run(df, levels_df=None)   # dávkově; výsledky identické se streamingem
engine.reset()                      # zpět do stavu po konstrukci (warmup znovu)
snap = engine.snapshot()            # serializovatelný vnitřní stav (10.5)
engine2 = TrendEngine.from_snapshot(snap, session_calendar, roll_dates, levels, intrabar, news, continuation_table)
```

- `bar` je záznam se sloupci 3.1; `df` DataFrame s týmiž sloupci seřazený podle `ts`; `levels_df` DataFrame se sloupci 3.5 (v dávkovém režimu se zabalí do deterministického `LevelProvider`).
- `run` vrací `states` (DataFrame, jeden řádek na platný bar, sloupce = zploštělá pole 10.3 s prefixy `up_`, `down_`, `answer_`) a `events` (DataFrame se sloupci 10.4). `run` musí být implementován jako smyčka nad `update` nebo dávkově s totožným výsledkem (13.2.3).
- `params` je datová třída `TrendParams` s poli z 12; neznámé pole → `ValueError` při konstrukci; hodnoty mimo povolený rozsah → `ValueError`.
- Verze: `engine.version` (semver knihovny) a `engine.params_hash` (SHA-256 kanonického JSON parametrů) jsou součástí každého stavu a logu.

### 10.2 Protokoly vstupů

```python
class LevelProvider(Protocol):
    def levels_at(self, ts_open: datetime) -> list[Level]: ...   # jen úrovně s valid_from <= ts_open (3.5)

class IntrabarProvider(Protocol):
    def bars_1s(self, t: int, ts_open: datetime) -> list[Bar1s] | None: ...  # None = pro tento bar nedostupné

class SessionCalendar(Protocol):
    def session_for(self, ts_open: datetime) -> Session | None: ...   # 3.2

class NewsProvider(Protocol):
    def scheduled_between(self, ts_from: datetime, ts_to: datetime) -> list[ScheduledEvent]: ...  # rozvrh, bez Actual (3.9)
    def released_until(self, ts: datetime) -> list[Release]: ...      # jen vydání s DateTime <= ts (3.9)
```

Poskytovatelé musí být deterministické funkce svých argumentů (stejný vstup → stejný výstup); komponenta jejich výstup nekešuje přes bary.

### 10.3 Stav (`TrendState`, jeden na bar)

Společná pole:

| Pole | Typ | Popis |
|---|---|---|
| `bar_index`, `ts_open`, `ts_close` | int, tz-aware, tz-aware | aktuální bar (4.2) |
| `session_id`, `outside_session`, `is_roll_bar`, `gap_before_min` | int, bool, bool, float | 3.2, 3.3; `gap_before_min = (ts_open(t) − ts_close(t−1))` v minutách, 0 u prvního baru |
| `warmup` | bool | 4.1 |
| `atr1`, `atr_ref` | float, float | 4.1 (null ve warmupu) |
| `intrabar_ambiguous`, `intrabar_used` | bool, bool | 5.3 |
| `levels_missing`, `n_levels_active` | bool, int | 3.5 |
| `direction`, `direction_phase` | enum, enum nebo null | 7.3 |
| `swings_new` | list[Swing] | swingy potvrzené v tomto baru (5.5) |
| `up`, `down` | `SideState` | níže |
| `answer` | `Answer` | 1.1 |
| `stat` | `StatFeatures` nebo null | detektor B (15.2) |
| `news` | `NewsState` nebo null | kalendář zpráv (3.9) |
| `delta_tl_agrees`, `delta_divergence` | bool nebo null | 9 |
| `extra` | dict[str, dict] | výstupy doplňkových detektorů (15.6) |
| `version`, `params_hash` | str, str | 10.1 |

`SideState` (pro `up` i `down`; ceny v původních souřadnicích, znaménkové metriky podle 4.3):

| Pole | Typ | Popis |
|---|---|---|
| `phase` | enum | 7.1 |
| `trend_valid` | bool | 7.2 |
| `L0` | Swing nebo null | 6.1 |
| `t_reset` | int | 6.1.1 |
| `anchors` | list[Swing] | přijatá low (bez `L₀`) v pořadí `t_ext` |
| `pseudo_anchors` | list[(int, float)] | 6.2 |
| `major_highs` | list[Swing] | 6.1 |
| `H`, `t_H` | float nebo null, int nebo null | běžící maximum |
| `prev_major_low` | float nebo null | 6.1 |
| `n_anchors` | int | 6.1 |
| `main_tl`, `curr_tl` | `TrendLine` nebo null | níže; null při `n_anchors < 2` |
| `curr_is_main` | bool | 6.3 |
| `pullback` | `Pullback` nebo null | 7.4 |
| `quality` | `Quality` nebo null | 8.1 |
| `pw1_trend_side`, `pw1_counter_side`, `pw2`, `pw2_main`, `pw2_curr`, `pw3`, `chop_bars`, `reversal_hint` | bool/int nebo null | 8.2 |
| `slope_ok_main`, `slope_ok_curr` | bool nebo null | 6.6 |

`TrendLine`:

| Pole | Typ | Popis |
|---|---|---|
| `kind` | MAIN / CURR | |
| `anchor1`, `anchor2` | (t, price), (t, price) | `L₀` a kotva s minimálním sklonem (hlavní); dvě poslední přijatá low (aktuální) |
| `slope`, `intercept` | float, float | body/bar; `value_at(x) = intercept + slope × (x − anchor1.t)` |
| `slope_norm` | float | 6.6 |
| `value_now` | float | `value_at(bar_index)` |
| `dist_close_atr` | float | `(close − value_now)/atr_ref` |
| `broken` | bool | 6.5 |
| `created_at`, `updated_at` | int, int | bar vzniku, poslední změny |
| `value_at(x)` | metoda | 6.4 |

`Answer`: pole z 1.1 (`in_trend`, `direction`, `strength`, `strength_class`, `pullback_starting`, `pullback_active`, `pullback_age_bars`, `continuation_score`, `continuation_n`, `continuation_source`) plus `reversal_hint` a `phase` strany `direction`.

### 10.4 Události

Každá událost má: `event_id` (int, pořadové), `type`, `side` (UP / DOWN / null u globálních), `t_known` (bar_index, kdy byla známa), `ts_known` (= `ts_close(t_known)`), `t_ref` (bar, ke kterému se vztahuje, např. `t_ext` swingu), `ts_ref`, `payload` (dict). Typy a povinný obsah `payload`:

| Typ | `side` | `t_ref` | Payload |
|---|---|---|---|
| `SWING_CONFIRMED` | null | `t_ext` | celý záznam swingu (5.5) |
| `TREND_CANDIDATE` | strana | `t_ext(L₀)` | `L0` |
| `TREND_START` | strana | `t_ext` první kotvy | `L0`, `anchor`, `main_tl` |
| `TL_UPDATE` | strana | `t_known` | `which = MAIN`, `old` (slope, intercept, anchor2), `new`, `reason ∈ {NEW_ANCHOR, PSEUDO_ANCHOR}` |
| `CURR_TL_NEW` | strana | `t_ext` novější kotvy | `anchor1`, `anchor2`, `slope`, `ratio` |
| `CURR_TL_DROP` | strana | `t_known` | `reason = BREAK` |
| `PULLBACK_START` | strana | `t_H` | `pb_id`, `parent_pb_id`, `restart`, `H`, `t_H`, `t_start` |
| `PULLBACK_END_UP` | strana | `t_known` | `pb_id`, `bars`, `pb_low`, `pb_depth_atr`, `outcome = RESUMED` |
| `PULLBACK_END_DOWN` | strana | `t_known` | `pb_id`, `bars`, `pb_low`, `reason ∈ {TL_BREAK, STRUCTURE}` |
| `TL_BREAK` | strana | `t_known` | `which ∈ {MAIN, CURR}`, `tl_value`, `close`, `depth_atr` |
| `TL_REVALIDATED` | strana | `t_known` | `main_tl` |
| `TREND_END` | strana | `t_known` | `reason ∈ {STRUCTURE, LL_SWING}`, `L0`, `H_final` (= běžící maximum `H` v okamžiku konce; nemusí být potvrzený swing), `t_H_final` (= `t_H`), `duration_bars`, `n_swings` |
| `BAR_SKIPPED` | null | `t_known` (index, který by bar dostal) | `ts`, `reason` |
| `ROLL_GAP`, `NON_TICK_PRICE`, `BARS_OUTSIDE_SESSION`, `UNKNOWN_LEVEL_KIND`, `CONTINUATION_TABLE_MISMATCH` | null | `t_known` | `detail` |

Varovné události (poslední řádek) se zároveň logují přes `logging` na úrovni WARNING; ostatní na úrovni DEBUG. Pořadí událostí v baru: 6.7.

### 10.5 Testovatelnost

- `snapshot()` vrací JSON-serializovatelný dict celého vnitřního stavu (zigzag, obě strany, ATR okno, čítače, poslední timestamp); `from_snapshot` obnoví engine tak, že další `update` dává totožné výsledky jako nepřerušený běh (13.2.8).
- `TrendState` je serializovatelný do dict/JSON (`state.to_dict()`); ceny jako float, časy ISO 8601 s pásmem; null jako `null`. Pořadí klíčů je pevné (pro hash v 13.2.4).
- Všechny výpočty jsou čistě funkcí vstupů a parametrů; žádný globální stav, žádné čtení hodin, žádná náhodnost.
- Konstanty popsané v 12 nejsou nikde zapsané natvrdo v kódu mimo `TrendParams`.
- Log odhadů pro testy (13.3) vzniká přímo ze `states`/`events` bez další transformace.

## 11. Požadavky na chování

### 11.1 Kauzalita a determinismus

- **Bez pohledu do budoucnosti:** výstup v baru t závisí jen na barech ≤ t, úrovních s `valid_from ≤ ts_open(t)`, 1s datech barů ≤ t, rozvrhu zpráv (znám předem) a vydáních zpráv s `DateTime ≤ ts_open(t)` (3.9).
- **Replay invariance:** `run(df)` dává totéž co postupné volání `update()` (bitově shodné hodnoty float).
- **Determinismus:** žádná náhodnost, žádná závislost na pořadí hashování nebo vláknech; jednovláknový výpočet.
- **Neměnnost historie:** potvrzené swingy, minulé stavy a vydané události se zpětně nemění; změny jen jako nové události.
- **Obnovitelnost:** `snapshot`/`from_snapshot` (10.5).

### 11.2 Data

- **Mezery:** chybějící minuty se nedoplňují; mezera ≥ `gap_min` uvnitř session se označí (8.1); hranice session mění TR (4.1).
- **Neplatné bary:** 3.1 (`raise` výchozí).
- **Studený start:** warmup 4.1; po něm první swingy vznikají přirozeně; žádné pole nesmí být NaN tam, kde dokument říká null (null se serializuje jako `null`, ne NaN).

### 11.3 Obecnost trhu a odolnost proti overfittingu

- **Žádná konstanta trhu v kódu:** velikost ticku, TF, rozvrh session, data rollu jsou vstupy nebo parametry; všechny prahy jsou v násobcích `atr_ref` nebo v barech. Primární trh je NQ; ES a YM (kapitola VII) musí běžet beze změny kódu a se stejnými výchozími parametry (doladění pro jiné trhy může přijít později, ale nesmí být nutné pro běh).
- **Stejné parametry pro syntetiku i reálná data:** brána 13.2.5 (syntetika) i historický běh (13.3) používají tytéž výchozí parametry; jakákoli sada parametrů, která projde jen na jednom z nich, je odmítnuta.
- **Robustnostní brána 13.11:** výsledky s týmiž parametry na syntetice, NQ (po letech), ES a YM se smí lišit jen v mezích 13.11; perturbace parametrů ±25 % nesmí výsledky zlomit. Nesplnění = overfitting → mění se parametry (zápis do logu), ne kritéria.
- **Počet parametrů** ladících se kalibrací je omezen tabulkou 12.1; přidání parametru vyžaduje záznam v logu s důvodem a musí projít 13.11.
- **Kalibrace jen na vývojovém období** (13.3); deník a obrázky jen podle 3.6.

### 11.4 Chyby a logování

- Výjimky: `InvalidBarError`, `TimestampConventionError`, `LookaheadLevelError`, `ValueError` (parametry). Po výjimce z `update` je engine v nedefinovaném stavu a musí se resetovat nebo obnovit ze snapshotu.
- Varování vznikají jako události (10.4) i přes `logging`; každé varování nejvýš jednou za typ a běh, s počítadlem v `engine.warnings` (dict typ → počet).
- Žádný výstup na stdout.

### 11.5 Výkon

- Časová složitost: `O(N + Σ_trendy (délka × počet přepočtů TL))`; přepočty TL jen při přijetí low (6.2). Paměť: `O(atr_n + W + délka aktivních struktur)` na stranu, plus výstupy.
- Celá historie 2007–2025 (řádově 6 mil. 1min barů ETH) do 10 min na jednom jádře v dávkovém režimu, včetně zápisu `states` a `events`; měří se v 13.2.9. Volitelná akcelerace (numba) nesmí měnit výsledky (bitová shoda s čistou implementací, 13.2.4).

## 12. Parametry a kalibrace

### 12.1 Parametry (`TrendParams`)

Sloupec „Kalibrace“: **ne** = vstupní vlastnost dat nebo pevné rozhodnutí, nekalibruje se; jinak rozsah kalibrace (12.2). Všechny násobky ATR jsou násobky `atr_ref`.

| Parametr | Typ | Výchozí | Kalibrace | Sekce |
|---|---|---|---|---|
| `tick_size` | float > 0 | 0,25 (NQ) | ne (vlastnost trhu) | 4.5 |
| `tf_minutes` | int ≥ 1 | 1 | ne (3.7) | 3.1 |
| `bar_timestamp` | close / open | close | ne | 3.1 |
| `on_invalid_bar` | raise / skip | raise | ne | 3.1 |
| `session_scope` | ETH / RTH | ETH | ne | 3.2 |
| `gap_min` | float, min | 5 | ne | 8.1 |
| `atr_n` | int | 30 | 20–60 | 4.1 |
| `atr_floor_ticks` | int | 2 | ne | 4.1 |
| `anchor_mode` | body / wick / close | body | body / wick / close | 4.4 |
| `theta` (θ) | float | 3 | 2–6 | 5 |
| `theta_pb` (θ_pb) | float nebo null (= θ) | null | 0,5θ–θ | 7.4 |
| `eps` (ε) | float | 0,5 | 0,25–1 | 6.2 |
| `ratio_steep` | float | 1,5 | 1,25–2 | 6.3 |
| `ratio_flat` | float nebo null (= 1/`ratio_steep`) | null | odvozený | 6.3 |
| `min_slope` | float nebo null | null (vypnuto) | 12.3 | 6.6 |
| `pw1_n` | int | 3 | 2–4 | 8.2 |
| `pw1_counter_n` | int | 2 | 2–3 | 8.2 |
| `delta_dev` (δ) | float | 3 | 2–5 | 8.2 |
| `pw3_window` (W), `pw3_er_window`, `er_chop`, `pw3_max` | int, int, float, int | 60, 20, 0,25, 30 | 30–120, 10–30, 0,15–0,35, W/4–3W/4 | 8.2 |
| `level_tol` | float | 0,5 | 0,25–1,5 | 3.5 |
| `levels_enabled` | bool | true | ne (běh bez úrovní, 13.9) | 3.5 |
| `pb_start_window` | int | 3 | ne | 7.4 |
| `slope_ref` | float | 0,2 | 12.3 | 8.3 |
| `strength_strong`, `strength_weak` | float, float | 0,6, 0,3 | 8.3 (monotonie) | 8.3 |
| `intrabar_mode` | auto / heuristic | auto | ne | 3.4 |
| `delta_enabled`, `theta_delta`, `delta_cumulates_across_sessions` | bool, float nebo null (= θ), bool | true, null, false | ne | 9 |
| `detectors` | tuple[str] | ("A", "B", "C") | ne | 1.3 |
| `stat_window`, `vr_q` | int, int | 60, 5 | 30–120, 3–10 | 15.2 |
| `ml_enabled` | bool | false | 15.5 | 15.5 |
| `news_pre_min`, `news_post_min` | float, float | 5, 15 | ne (členění reportu; změna jen záznamem v logu) | 3.9 |
| `news_min_history` | int | 12 | ne (dodatek zadavatele) | 3.9 |
| `news_horizon_min` | float | 1 440 | ne | 3.9 |

Odvozené hodnoty (null = odvodit) se při konstrukci doplní a zapíší do `params_hash`.

### 12.2 Postup kalibrace

Podklady: chartbooky s ručně zakreslenými TL (obrázky, CSV z obrázků) a obchodní deník; jejich použití je omezeno na 3.6. Kalibrace probíhá **jen na vývojovém období** (13.3) a jen v rozsazích 12.1.

1. Vybrat vzorek 40 obchodních dnů z vývojového období (stratifikovaně: 10 na kvintil `atr1` denní, rovnoměrně přes roky; generátor výběru je deterministický se semínkem zapsaným do reportu).
2. Ručně označit (uživatel, mimo běh): trend (směr, `L₀`, konec), hlavní a aktuální TL (dvě kotvy), začátek každého pullbacku, PW-SW 1–3 v okamžiku dotyku TL. Formát anotace: CSV s jedním řádkem na objekt (den, typ, čas, cena, poznámka).
3. Nastavit parametry pro nejlepší shodu na 28 dnech (mřížkové hledání v rozsazích 12.1, krok: θ 0,5; ε 0,25; δ 0,5; W 15; ostatní podle tabulky).
4. Ověřit shodu na zbývajících 12 dnech; přijmout jen sadu, u které se shoda na ověřovacích dnech liší od ladicích o ≤ 10 p.b.
5. Spustit robustnostní bránu 13.11; při nesplnění vrátit k bodu 3 s užším rozsahem.

Metriky shody: shoda fáze po barech (podíl barů se shodným `direction`), rozdíl sklonu TL (`|slope_norm_komponenta − slope_norm_ruční|`, medián), rozdíl času začátku pullbacku (bary, medián a 90. percentil), shoda PW-SW (podíl shod po pullbacích). Cíl: shoda fáze ≥ 80 %, medián rozdílu začátku pullbacku ≤ 2 bary; nesplnění není chyba komponenty, ale musí být v reportu s rozborem příčin.

### 12.3 Kalibrace jednotlivých předpokladů

- **`min_slope` (pravidlo 2):** z `PAT/PAT_obchody_z_obrazku.csv` vzít sloupec `TL sklon (bodů/min)` pro všechny řádky, vydělit `atr_ref` v baru vstupu obchodu (z 1min dat, `tf_minutes = 1`) → rozdělení `slope_norm` u TL, které autor považoval za vyhovující. `min_slope` = 10. percentil tohoto rozdělení (90 % obchodů autora projde). Zapnout jen jako volitelný filtr; výchozí zůstává vypnuto, protože rozdělení je z jediného zdroje s přesností ±1 tick a rozsah úhlů v obrázcích (9°–56°) ukazuje, že autor 45° neuplatňoval doslova. Předpoklad (D-27).
- **`slope_ref` (8.3):** medián `slope_norm_main` přes všechny bary s `trend_valid = true` na vývojovém období.
- **Prahy `strength_*`:** podle monotonie 8.3.
- **PW1 protistrana (`pw1_counter_n`) a PW2 (δ):** volba hodnoty s největším rozdílem úspěšnosti pullbacků (13.7) mezi `reversal_hint = 0` a `1` na vývojovém období, při zachování podílu vyřazených pullbacků 40–75 % (kapitola VIII uvádí, že PW-SW vyřadí zhruba dvě třetiny obchodů).
- **PW3:** stejně jako PW2 pro W, `er_chop`, `pw3_max`.
- **θ, ε, `anchor_mode`:** podle shody s ruční anotací (12.2), ne podle úspěšnosti (aby se definice trendu nepřizpůsobila výsledku).

## 13. Testování: požadavky a akceptační kritéria

Postup provedení testů (harness, data, formát reportu) je v `zadani/testy.md` (1.4). Tato sekce definuje, co se testuje a kdy je výsledek přijat.

### 13.1 Princip

Jeden test, který:

1. spustí komponentu nad historickými daty bar po baru,
2. uloží každý její odhad tak, jak byl známý v daném baru,
3. každý odhad zkontroluje pohledem do budoucnosti: podívá se, co se po něm skutečně stalo, a určí, zda byl pravdivý,
4. spočítá metriky.

Pohled do budoucnosti má jen test v kroku 3, až po běhu komponenty. Komponenta sama budoucnost nikdy nevidí.

### 13.2 Povinné funkční testy (brány, pass / fail)

Bez splnění všech bran se historické metriky nevyhodnocují. Shoda výstupů = shoda `states.to_dict()` a `events` po barech včetně float hodnot (bitově); u bran 1–2 se porovnávají všechny bary ≤ t.

1. **Zkrácení dat:** pro 1 000 bodů t (deterministický generátor, semínko 20260925, rovnoměrně přes vývojové období) se komponenta spustí na datech do t a na celých datech. Všechny výstupy do t musí být identické. Nejsilnější test absence pohledu do budoucnosti. Totéž s poskytovatelem úrovní: úrovně s `valid_from > ts_open(t)` musí být pro běh do t nedostupné a výsledek shodný. Totéž s kalendářem zpráv: vydání s `DateTime > ts_open(t)` nedostupná, rozvrh dostupný.
2. **Změna budoucnosti:** pro tytéž body t se bary po t nahradí náhodnou procházkou (semínko t); žádný výstup do t se nezmění.
3. **Replay:** `run(df)` = postupné `update()` (11.1), bitově.
4. **Determinismus:** dva běhy dávají bitově shodné výstupy (SHA-256 kanonického JSON logu); totéž s akcelerací a bez ní (11.5).
5. **Syntetické scénáře se známou pravdou** (podsekce „Syntetické scénáře“ níže).
6. **Okrajové případy:** mezery přes noc a víkend, halt (mezera 30 min uvnitř session), den rollu (s mezerou i bez), extrémně dlouhý knot (knot 10 × atr, tělo 0,2 × atr), plochý trh (200 barů `high == low`), první bary historie (warmup), neplatný bar v obou režimech `on_invalid_bar`, chybná konvence timestampu (`TimestampConventionError`), úroveň s `valid_from` v budoucnosti (`LookaheadLevelError`). Kritérium: žádná výjimka mimo očekávané, žádný NaN, chování podle 3–5.
7. **Ekvivalence 1s dat:** běh s `intrabar_mode = auto` (1s data) a `heuristic` nad týmž obdobím (≥ 20 obchodních dnů, kde 1s data jsou): výstupy se smí lišit jen od prvního baru s `intrabar_ambiguous = true` po nejbližší `TREND_END` obou stran; podíl barů `intrabar_ambiguous` se hlásí (očekávání < 2 %; vyšší hodnota není chyba, ale musí být v reportu).
8. **Snapshot:** běh přerušený v 100 bodech a obnovený z `snapshot()` dává bitově shodné výstupy s nepřerušeným během.
9. **Výkon:** celá historie 1min NQ ETH v dávkovém režimu do 10 min na jednom jádře (11.5); paměť do 4 GB.

#### Syntetické scénáře (brána 13.2.5)

Generátor: po částech lineární „ideální“ cesta `m(t)` v jednotkách `A` (cílový ATR, např. 2 body), z níž vzniknou bary `open = m(t−1) + n₁`, `close = m(t) + n₂`, `high = max(open, close) + |n₃|`, `low = min(open, close) − |n₄|`, šum `n_i` deterministický (semínko scénáře), amplituda `≤ 0,2 A`; `tick_size` 0,25, `atr_n` 30, θ = 3, warmup 30 barů plochých s rozsahem A. Očekávání se vyhodnocuje **po** warmupu; tolerance zpoždění: událost smí nastat nejpozději v baru, kde ji definice (5–7) vyžaduje (zpoždění potvrzení je součástí pravdy, ne chybou).

| # | Scénář (cesta `m`) | Očekávané výstupy | Kritérium pass |
|---|---|---|---|
| S1 | trend s pravidelnými pullbacky: 8 opakování (impuls +6A za 20 barů, pullback −3,5A za 10 barů) | `TREND_CANDIDATE` po potvrzení 1. low, `TREND_START` po potvrzení 2. low; každý pullback: `PULLBACK_START` v baru, kde pokles od `H` dosáhne 3A, `PULLBACK_END_UP` v baru nového maxima; žádný `TREND_END`; `direction = UP` od `TREND_START` do konce | přesná shoda barů událostí s referenčním výpočtem podle 5–7 (referenční výpočet je součást testu, nezávislá implementace pravidel na ideální cestě), `down.trend_valid = false` všude |
| S2 | jako S1, po 5. pullbacku obrat: pokles −12A za 30 barů | `PULLBACK_START`, pak `TL_BREAK(MAIN)` a `PULLBACK_END_DOWN`, pak `TREND_END(STRUCTURE)` v baru prvního close pod `prev_major_low`; poté `TREND_CANDIDATE` strany DOWN | pořadí a bary událostí přesně |
| S3 | trend jako S1, po 3. pullbacku zpomalení: impulsy +2A za 20 barů, pullbacky −3,2A za 10 barů | `TL_BREAK(MAIN)` bez `TREND_END`, po dalším přijatém low `TL_UPDATE(PSEUDO_ANCHOR nebo NEW_ANCHOR)` a `TL_REVALIDATED`; `CURR_TL_NEW` s `ratio ≤ 0,67` | události nastanou; `TREND_END` nenastane |
| S4 | zrychlení: po 3. pullbacku impulsy +12A za 20 barů | `CURR_TL_NEW` s `ratio ≥ 1,5`; `curr_is_main = false` | přesně |
| S5 | chop: 300 barů sinusoida amplitudy 1,5A, perioda 40 barů | žádný `TREND_START`; `phase ∈ {NONE, CANDIDATE}` obou stran | žádná platná fáze |
| S6 | chop s velkou amplitudou: sinusoida 4A, perioda 60 | swingy se potvrzují; může vzniknout `TREND_START`, ale každý trend skončí do 2 period; `pw3 = false` po ≥ 50 % barů s `L₀` | `chop_bars ≥ pw3_max` po ≥ 50 % takových barů |
| S7 | současný uptrend a downtrend: S1 do 4. pullbacku, pak klesající sekvence (impuls −6A/20, pullback +3,5A/10) 3× bez close pod `prev_major_low` uptrendu | `down.trend_valid = true` a `up.phase ∈ {TL_BROKEN, PULLBACK}` současně aspoň 1 bar; `direction = DOWN` (novější `L₀`) | přesně |
| S8 | pullback na úroveň: S1 s úrovní `SR` na ceně pullback low 3. pullbacku | `stopped_at_level = true`, `dist_to_level_atr ≤ 0,5` v baru pullback low; s `levels_enabled = false` obě null a ostatní výstupy shodné | přesně |
| S9 | mezera: S1 s odstraněnými 60 bary uprostřed 2. impulsu a hranicí session před nimi | `gap_in_structure = false` (hranice session), `session_cross = true`, ATR bez skoku (TR prvního baru = high − low) | přesně |
| S10 | zrcadlo: S1–S4 vynásobené −1 | zrcadlové události strany DOWN, znaménkové metriky shodné s UP variantou | rovnost hodnot po zrcadlení (bitově u int, do 1e-9 u float) |

### 13.3 Historický běh

- **Data:** celá dostupná historie 1min NQ ETH (cílově ~20 let), s ověřenými časy z datové vrstvy (3); 1s data tam, kde jsou (R3).
- **Období:** chronologicky rozdělené **před prvním během**:
  - vývojové: prvních ~70 % (např. 2007-01-01 až 2018-12-31) — smí se na něm ladit parametry (12),
  - testovací: posledních ~30 % (např. 2019-01-01 až konec dat) — vyhodnotí se **jednou** se zmrazenými parametry.
- Pokud se parametry po pohledu na testovací období změní, testovací období se stává vývojovým a report to uvede.
- **Log odhadů:** `states` a `events` z `run` (10.1) uložené jako parquet; obsahuje pro každý bar `direction`, fáze, TL (kotvy, sklon, intercept), `answer`, PW-SW, kvalitu; události s `t_known`.

### 13.4 Kontrola odhadů pohledem do budoucnosti

Pro uptrend; downtrend zrcadlově. Kontrola používá stejnou definici swingů a struktury (5, 6) nad celými daty (zigzag je kauzální, takže swingy jsou stejné; pohled do budoucnosti dává jen znalost, kdy byl extrém a jak trend skončil).

| Odhad komponenty | Co test zkontroluje v budoucnosti | Výsledek |
|---|---|---|
| Swing potvrzen v baru t | kdy nastal extrém swingu | **zpoždění potvrzení** (`conf_delay_bars`, minuty, `|close_{t_conf} − price| / atr_ext`, tj. kolik ATR cena ušla od extrému do potvrzení) |
| Trend platný v baru t | zda bar leží v úseku trendu `[t_ext(L₀), t_H_final]` (`H_final`, `t_H_final` z payloadu `TREND_END`, tj. běžící maximum struktury v okamžiku konce; u struktur bez `TREND_END` do konce dat = `H`, `t_H` v posledním baru) | **pravda / nepravda po barech** |
| Začátek trendu | kdy byl `L₀` úseku | **zpoždění začátku** (od `t_ext(L₀)` do prvního `trend_valid`), a minimální možné zpoždění (od `t_ext(L₀)` do `t_conf` prvního přijatého low) |
| Konec trendu (`TREND_END`) | kdy byl `H_final` úseku | **zpoždění konce** (od `t_H_final` do `TREND_END`) |
| `PULLBACK_START` (`restart = false`) | co nastalo dřív: nové maximum nad `H` (`ext_high > H`), nebo close pod `prev_major_low` | **OBNOVENÍ** (pravda) / **OBRAT** (nepravda) / **NEVYŘEŠENO** (nic z toho do 5 session nebo do konce dat) |
| `TL_BREAK` hlavní TL | co nastalo dřív: nové maximum nad `H`, nebo `TREND_END` | **FALEŠNÉ** / **SKUTEČNÉ** prolomení |
| Trend UP v baru t (nezávisle na swingech) | zda cena (`high`/`low` baru) dosáhla dřív `close_t + k × atr_ref(t)`, nebo `close_t − k × atr_ref(t)`, v horizontu h barů | **pravda** při dosažení horní úrovně první / **nepravda** / **NEVYŘEŠENO** |

- **Remíza v témže baru** (oba cíle v jednom baru): 1s data, jsou-li; jinak heuristika 5.3 (býčí bar: dolní cíl dřív; medvědí: horní dřív). Podíl remíz se hlásí.
- Výsledek pullbacku se reportuje ve dvou variantách: do 5 session a do konce téže session (`rth_close`), protože P.A.T. je intradenní systém.
- Poslední kontrola (pokračování trendu) nepoužívá swingy, takže měří, zda trend skutečně pokračoval, ne jen zda komponenta správně aplikovala vlastní definici. Primárně k = θ, h = 240 barů; citlivost k = 2θ a h = 60.
- Zpoždění začátku trendu je zčásti nevyhnutelné: trend smí být vyhlášen až po potvrzení druhého swing low. Report uvádí i minimální možné zpoždění.

### 13.5 Referenční hodnoty (co by dala náhoda)

Bez referenční hodnoty nelze říct, zda je úspěšnost odhadu dílem komponenty, nebo jen geometrie a driftu trhu.

| Kontrola | Reference |
|---|---|
| Výsledek pullbacku | `p₀ = (c − L) / (H − L)` v baru `PULLBACK_START` (c = close, L = `prev_major_low`, H = běžící maximum; náhodná procházka bez driftu a limitu); navíc simulace blokovým bootstrapem 1min výnosů (bloky 15 min, stejný den v týdnu a kvintil `atr1`, bez driftu) se stejnými úrovněmi a horizontem |
| Prolomení TL | totéž `p₀` z ceny v baru `TL_BREAK` |
| Pokračování trendu | 0,5 (bez driftu) a podíl „horní úroveň první“ mezi **všemi** bary téhož roku (zohlední drift NQ) |
| Trend po barech | podíl barů v úsecích trendu (odhad „vždy trend“) |

Referenční výpočty používají vzdálenosti ke swingům. V testu je to povoleno; do komponenty nepatří.

### 13.6 Metriky a report

- **Trend:** matice záměn UP / DOWN / NONE po barech, přesnost a úplnost pro každý směr, rozdělení zpoždění začátku a konce, podíl úseků trendu, které komponenta nezachytila vůbec.
- **Pullback:** počty OBNOVENÍ / OBRAT / NEVYŘEŠENO, úspěšnost = OBNOVENÍ / (OBNOVENÍ + OBRAT), rozdíl proti průměrnému `p₀` a proti simulaci.
- **Prolomení TL:** podíl falešných prolomení vs. reference; podíl konců trendu, kterým předcházelo prolomení hlavní TL (včasné varování).
- **Swingy:** rozdělení zpoždění potvrzení v barech a v násobcích `atr_ext`.
- **Pokračování trendu:** podíl pravdivých odhadů pro UP a DOWN vs. obě reference; zvlášť podle `strength_class` a `phase` (Ø1).
- **Skóre pokračování:** Brier skóre a kalibrační křivka `continuation_score` proti výsledku kontroly pokračování (jen bary se skóre ≠ null), na testovacím období; srovnání s konstantou (roční základní podíl).
- **Členění:** po letech, směrech, RTH / noc, kvintilech `atr1`, vývojové / testovací období, v okně zprávy / mimo (`in_news_window` a `in_high_impact_window`, 3.9; jen je-li kalendář k dispozici).
- **Intervaly:** 95% intervaly blokovým bootstrapem po týdnech (výsledky uvnitř týdne nejsou nezávislé).

### 13.7 Vyhodnocení filtrů PW-SW a síly

- Úspěšnost pullbacků (13.4) zvlášť pro `reversal_hint` = 0 a 1 a pro každý filtr PW1–PW3.
- Očekávání systému: při `reversal_hint` = 1 je úspěšnost nižší. Report uvádí rozdíl s intervalem a podíl pullbacků, které filtr vyřadí.
- Úspěšnost pokračování podle `strength_class` (monotonie 8.3) a korelace `strength` s výsledkem.
- Totéž pro modul delta (9), pokud je aktivní.

### 13.8 Vizuální audit

P.A.T. je vizuální systém; číselná kontrola nezachytí vše.

- Náhodný vzorek 100 událostí `PULLBACK_START` a 50 `TREND_END`, rozložený přes roky (deterministický výběr, semínko v reportu).
- Graf: 300 barů před a 300 po události; TL **tak, jak byla známa v čase události** (ne pozdější překreslení), swingy komponenty a swingy určené zpětně nad celými daty, aktivní úrovně.
- Uživatel u každého označí: souhlasím / nesouhlasím s tím, že šlo o trend a pullback podle P.A.T., a důvod nesouhlasu.
- Výstup: míra souhlasu a typy chyb.

### 13.9 Běh s úrovněmi a bez nich

- Celá sada z 13.2 až 13.8 se pouští dvakrát: s poskytovatelem úrovní (3.5) a s `levels_enabled = false`.
- Report uvádí rozdíl obou běhů pro každou metriku z 13.6. Rozdíl je odpověď na otázku, kolik úrovně přidávají; kdyby byly zapečené uvnitř komponenty, nelze ji položit.
- Brány z 13.2 musí projít v obou variantách. Komponenta bez úrovní nesmí spadnout ani vracet nedefinované hodnoty; smí jen nastavit `levels_missing` a null v polích závislých na úrovních.
- Obchodní deník do bran ani metrik nevstupuje (3.6); jeho jediné testové použití je 13.13.

### 13.10 Interpretace

- **Brány 13.2 a 13.11** jsou pass / fail.
- **Historické metriky** nemají pevné cílové hodnoty; dosažitelná úroveň není známa. První běh na vývojovém období stanoví referenci. Každá další verze komponenty nebo sada parametrů se porovná proti ní (metriky uložené jako JSON, změny se hlásí).
- Úspěšnost ≈ reference: komponenta stavy detekuje, ale bez informace nad rámec geometrie. Úspěšnost nad referencí: na daném měřítku trendy přetrvávají.
- **Podezření na únik budoucnosti:** úspěšnost kontroly pokračování trendu nad 0,7, nebo úspěšnost pullbacků o víc než 20 p.b. nad referencí → zopakovat brány 13.2.1 a 13.2.2 na dotčených obdobích, než se výsledek přijme.
- Test měří správnost detekce stavů, ne obchodní výsledek systému (vstup, cíl, stop zůstávají mimo rozsah).

### 13.11 Robustnostní brána (overfitting, obecnost trhu)

Jádrové metriky: (a) přesnost `direction` po barech proti „vždy trend“ (rozdíl v p.b.), (b) úspěšnost pullbacků minus průměrné `p₀`, (c) úspěšnost pokračování minus roční základní podíl. Se **stejnými** parametry se spočítají na: syntetice S1–S10 (jen a), NQ po letech vývojového období, NQ testovací období, ES a YM (jsou-li data, R2).

| Kritérium | Pass |
|---|---|
| znaménko zisku (b) a (c) | shodné na všech trzích a ve ≥ 80 % let NQ |
| rozdíl (a), (b), (c) mezi trhy | ≤ 10 p.b. |
| perturbace každého kalibrovaného parametru (12.1) o ±25 % (po jednom) | změna (a), (b), (c) ≤ 10 p.b.; změna počtu trendů ≤ 30 % |
| syntetika S1–S4 se šumem 0,2 A → 0,4 A | brána 13.2.5 dál prochází s tolerancí ±2 bary u událostí |

Je-li zapnut detektor D, brána běží s kalendářem zpráv i bez něj (3.9); detektor A kalendář nečte, takže (a) a (b) se tím nemění. Nesplnění = overfitting nebo křehkost; řeší se změnou parametrů nebo definic (zápis do logu), nikdy uvolněním kritéria.

### 13.12 Porovnání časových rámců

Detektor A se spustí nad 1, 2, 3 a 5min bary (agregace z 1min: open prvního, close posledního, max/min), `atr_n` v barech beze změny. Pro každý TF: úspěšnost pokračování (k = θ, h = 240 min přepočtený na bary), zpoždění začátku trendu v minutách, počet trendů za rok. Pravidlo doporučení v 3.7.

### 13.13 Shoda s rozhodnutími autora (report, ne brána)

Pro každý obchod z `PAT/Obchodní deník.xls` a `PAT/PAT_obchody_z_obrazku.csv` (čas vstupu převedený na `ts_open` 1min baru v ET; časy v deníku i v CSV jsou středoevropské podle osy grafu, převod přes IANA `Europe/Prague` → `America/New_York`; dny, kdy se liší přechod na letní čas v EU a USA, se převádějí stejně, protože IANA pásma tyto rozdíly obsahují) se z logu 13.3 vezme stav baru **před** barem vstupu (spotřebitel jedná na uzavřeném baru) a hlásí se:

- podíl obchodů s `direction` = směr obchodu,
- podíl s `direction` = směr obchodu a `phase = PULLBACK`,
- podíl s `reversal_hint = false` mezi obchody s PW-SW = Ano v CSV, a s `reversal_hint = true` mezi PW-SW = Ne,
- rozdělení `dist_to_tl_atr_curr` a `dist_to_tl_atr_main` v baru vstupu (očekávání: blízko 0, protože vstupy jsou na křížení TL).

Bez cílové hodnoty; slouží k rozboru odchylek ve vizuálním auditu. Parametry se podle něj nemění (3.6).

## 14. Mimo rozsah

- **Výpočet** S/R, OHLC minulého dne a premarketu; komponenta je přijímá jako vstup (3.5), sama je neurčuje.
- Vstupní zóny (křížení TL s úrovněmi) počítá spotřebitel z projekce TL a ze seznamu úrovní.
- Profit target, stop-loss, vstup, výstup, position sizing.
- Vzdálenosti ceny ke swingům a geometrie obchodu.
- Hodnocení obchodního výsledku (vstup, cíl, stop), prediktivní modely obchodního výsledku, zprávy pro člověka. Odhad pokračování trendu (Ø1, 15.4–15.5) a akceptační kritéria detekce (13) do rozsahu patří.
- Implementace testovacího harnessu (`zadani/testy.md`).

## 15. Metody detekce a odpověď na Ø1

Zadavatel požaduje vyčerpat použitelné metody (klasické, statistické, strojové učení, jiné) a implementovat každou, kterou je výhodné implementovat; prioritou je spolehlivost odpovědi na Ø1, ne úplnost výčtu. Tato sekce je katalog s rozhodnutím pro každou metodu.

### 15.1 Katalog metod

| # | Metoda | Princip | Část Ø1 | Pro | Proti / riziko | Rozhodnutí |
|---|---|---|---|---|---|---|
| M1 | zigzag + TL + struktura HH/HL (P.A.T., kapitoly I.3–I.4, VIII) | swingy s prahem v ATR, TL přes low, fáze, PW-SW | 1, 2, 4 | přesně to, co spotřebitelé P.A.T. potřebují (TL, swingy, zóny); interpretovatelné; 6 kalibrovaných parametrů | zpoždění potvrzení swingu (nutné); definice stupňů (řešeno 6.1) | **detektor A, povinný** (5–8) |
| M2 | OLS sklon a jeho t-statistika v klouzavém okně | `close ~ t` přes `w` barů; t = sklon / se | 1 (síla), 3 (rys) | levné, bez parametrů kromě okna, škálově nezávislé po dělení ATR | autokorelace zvyšuje t (jen pořadí, ne test); okno pevné | **detektor B** (15.2) |
| M3 | Kaufman efficiency ratio | čistý pohyb / součet pohybů | 1 (síla), 4 (PW3) | robustní, bez ladění | necitlivé na směr (bezznaménkové) | v A (8.1, 8.2) a v B (okno) |
| M4 | variance ratio (Lo–MacKinlay) | rozptyl q-barových výnosů / (q × rozptyl 1-barových) | 3 | přímo měří perzistenci (trendování vs. návrat) | šum v krátkém okně; potřebuje ≥ 30 barů | **detektor B** (`vr`, q = 5) |
| M5 | Hurstův exponent, DFA | škálování rozptylu přes měřítka | 3 | teoreticky perzistence | nestabilní v oknech < 200 barů; pomalé | později; ne v v1 |
| M6 | Kalmanův filtr (lokální lineární trend) | stav = úroveň + sklon, rozptyl sklonu | 1, 3 | hladký odhad sklonu a jeho jistoty | 2 šumové parametry k ladění; informace srovnatelná s M2 | později; M2 postačuje v v1 |
| M7 | ADX/DMI, klouzavé průměry, SuperTrend, ATR kanály | klasické indikátory | 1 | rozšířené, jednoduché | zpoždění, redundantní s M1/M2, bez vztahu k TL P.A.T. | zamítnuto jako detektor; povoleny jako rysy D |
| M8 | HMM / Markov-switching (2–3 režimy) | pravděpodobnost režimu z výnosů | 1, 3 | modeluje režim přímo | nestabilní odhad, přeučení, nepřehledné chování při refitu; nedeterministické bez pevného semínka | později; přezkoumat, až D ukáže, zda „režim“ přidává informaci |
| M9 | detekce bodů změny (CUSUM, bayesovská online detekce) | změna střední hodnoty výnosů | 2 (začátek pullbacku), konec trendu | rychlá reakce | ladění prahů, falešné poplachy v chopu | později; kandidát na rys D |
| M10 | segmentace PIP / Ramer–Douglas–Peucker jako alternativní swingy | aproximace cesty úsečkami | 1, 2 | méně parametrů než zigzag | bez okna má pohled do budoucnosti; s oknem ≈ zigzag | zamítnuto pro běh; povoleno v testech jako alternativní „pravda“ swingů (13.4, informativně) |
| M11 | gradient boosting nad rysy A + B + úrovně, cíl = pokračování | GBDT, walk-forward | 3 | využije interakce rysů; kalibrovaná pravděpodobnost | přeučení na jednom trhu; nutná přísná brána | **detektor D** (15.5), vypnutý do splnění brány |
| M12 | sekvenční neuronové sítě (LSTM, TCN, transformer) nad bary | učení z posloupností | 1, 3 | bez ručních rysů | malý počet nezávislých trendů (řádově 10⁴), vysoké riziko přeučení, potřeba GPU, nedeterminismus | mimo v1; žádost o GPU se podá jen, pokud D prokáže zisk nad C (15.5) |
| M13 | kumulativní delta (kapitola IX) | tentýž zigzag nad deltou | 4 (potvrzení) | součást P.A.T. | vyžaduje bid/ask data (R1) | modul 9, volitelný |
| M14 | shoda více časových rámců | A nad 5min bary jako potvrzení 1min trendu | 1, 3 | levné, deterministické | zpoždění vyššího TF | později; rozhodne 13.12 |
| M15 | tabulka pokračování (empirické základní podíly) | P(pokračování \| bin) z vývojového období | 3 | nejjednodušší kalibrovaný odhad; ≤ 24 binů, nelze přeučit | hrubé | **detektor C** (15.4) |
| M16 | fraktální dimenze, entropie výnosů | složitost cesty | 1 | — | redundantní s M3/M4, bez jasné výhody | zamítnuto |
| M17 | ekonomický kalendář zpráv (dodatek zadavatele) | okno kolem zpráv s vysokým dopadem, standardizované překvapení | 3 (rys), členění reportu | vnější informace, kterou cena nenese; známý rozvrh | mimo definici P.A.T.; riziko pohledu do budoucnosti přes časové pásmo a revize | **vstup 3.9**: rys pro D a členění 13.6; detektor A nečte |

Rozhodnutí (D-2): v1 = A + B + C; D specifikován a vypnutý; ostatní později nebo zamítnuto s důvodem výše.

### 15.2 Detektor B (statistický)

Vstup: closes posledních `w = stat_window` (výchozí 60) platných barů (po warmupu); s méně než 30 bary jsou výstupy null; s 30 ≤ n < w se použije n barů. Výstupy v `state.stat`, zarovnané do směru `direction` (při `direction = NONE` do směru UP, tj. bez zarovnání):

| Pole | Definice |
|---|---|
| `reg_slope` | OLS sklon `close ~ index` (body/bar) |
| `reg_slope_norm` | `reg_slope / atr_ref(t)` |
| `reg_slope_t` | `reg_slope / se(reg_slope)` (klasická OLS směrodatná chyba; autokorelace se neopravuje, hodnota slouží k pořadí, ne k testu) |
| `er_w` | Kaufman ER přes okno (jmenovatel 0 → 0) |
| `vr` | variance ratio s `q = vr_q` (5): `Var(r_q) / (q × Var(r_1))`, výnosy `r = Δclose`, rozptyly výběrové přes okno; null při `Var(r_1) = 0` |
| `n_window` | použitý počet barů |

Detektor B nemění fáze ani `trend_valid`; slouží pro report (13.6), jako rysy D a pro spotřebitele.

### 15.3 Jak se odpovídá na Ø1

| Část Ø1 | Zdroj v v1 | Poznámka |
|---|---|---|
| v trendu, směr | A (`direction`, 7.3) | definice P.A.T. |
| síla | A (`strength`, 8.3) + B (`stat`) | `strength` je jediné skalární shrnutí; B dává rysy |
| začíná pullback | A (7.4) | `pullback_starting` |
| bude pokračovat | C (15.4); D, je-li zapnut a prošel bránou | `answer.continuation_source ∈ {TABLE, ML, null}` |
| detaily P.A.T. | A, modul 9 | TL, swingy, PW-SW, úrovně |

### 15.4 Detektor C: tabulka pokračování

- **Vznik:** testovací harness (`zadani/testy.md`) spočítá na **vývojovém období** pro každý bar s `trend_valid = true` výsledek kontroly pokračování (13.4, k = θ, h = 240; NEVYŘEŠENO se vynechá) a agreguje podle binu `(direction, phase ∈ {IMPULSE, PULLBACK}, strength_class ∈ {WEAK, MEDIUM, STRONG}, reversal_hint ∈ {false, true})` → nejvýš 24 binů. Pro každý bin: `p` = podíl pravda, `n` = počet.
- **Formát:** JSON `{ "params_hash": …, "k": 3, "h": 240, "period": ["2007-01-01", "2018-12-31"], "bins": [ {"direction": "UP", "phase": "PULLBACK", "strength_class": "STRONG", "reversal_hint": false, "p": 0.57, "n": 12345}, … ] }`.
- **Použití v komponentě:** při konstrukci se tabulka načte; pokud `params_hash` neodpovídá `engine.params_hash`, tabulka se odmítne s varováním `CONTINUATION_TABLE_MISMATCH` a skóre je null. V baru se vyhledá bin; `continuation_score = p`, `continuation_n = n`, jen pokud `n ≥ 500`; jinak null. Bez `direction` null.
- **Anti-overfitting:** biny jsou pevné (žádné učení hranic), tabulka jen z vývojového období, ověření kalibrace na testovacím období (13.6 Brier). Tabulka je součást parametrizace (verze v reportu).
- Bin s `reversal_hint = null` nebo `strength_class = null` → null.

### 15.5 Detektor D (strojové učení)

- **Cíl:** totéž jako C (pokračování v horizontu h), jako pravděpodobnost.
- **Rysy (jen kauzální, z baru t):** `slope_norm_main`, `slope_norm_curr`, `slope_ratio`, `er`, `r2`, `n_swings`, `duration_bars`, `tl_max_dev_atr_curr`, `tl_dev_atr_now`, `dist_to_tl_atr_main/curr`, `pb_depth_atr`, `pb_retrace`, `bars` pullbacku, `n_inner_swings`, `pw1_*`, `pw2`, `chop_bars`, `dist_to_level_atr`, `dist_to_next_level_atr`, `stopped_at_level`, `levels_crossed`, `stat.*`, hodina session (kategorie), kvintil `atr1` v rámci roku, a je-li kalendář (3.9): `news.next_event_min`, `news.last_event_min`, `news.last_surprise_z`, `news.last_surprise_missing`, dopad nejbližší a poslední události (kategorie), `in_news_window`. Null → chybějící hodnota (GBDT ji umí).
- **Model:** histogramový gradient boosting (např. `sklearn.ensemble.HistGradientBoostingClassifier`), hloubka ≤ 4, ≤ 200 stromů, learning rate 0,05, jednovláknový, pevné semínko; kalibrace isotonic na validační části.
- **Walk-forward:** pro každý rok y vývojového období: trénink na letech < y (min. 3 roky), validace y; finální model pro testovací období: trénink na celém vývojovém období.
- **Brána zapnutí:** Brier skóre lepší než C o ≥ 0,01 v **každém** walk-forward roce a na testovacím období, a robustnostní brána 13.11 projde s D zapnutým. Jinak `ml_enabled = false` zůstává a D je jen v reportu.
- **Výstup:** `extra["ml"] = {"continuation_score": p, "model_hash": …}`; je-li zapnut a prošel, `answer.continuation_score` bere D a `continuation_source = ML`, jinak C.
- **Reprodukovatelnost:** model serializovaný s hashem; trénink deterministický; komponenta model jen načítá (nikdy netrénuje za běhu).

### 15.6 Rozhraní doplňkového detektoru

```python
class Detector(Protocol):
    name: str
    def reset(self) -> None: ...
    def update(self, ctx: BarContext, state: TrendState) -> dict[str, float | int | bool | str | None]: ...
    def snapshot(self) -> dict: ...
    def restore(self, snap: dict) -> None: ...
```

- `BarContext` nese bar t, `atr_ref`, session, aktivní úrovně, posledních `stat_window` barů (jen minulost).
- `update` je čistá funkce svého stavu a argumentů; nesmí měnit `state`; smí číst jen bary ≤ t. Výstup se ukládá pod `state.extra[name]` a podléhá branám 13.2.1–13.2.4 stejně jako jádro.
- Detektory se registrují v `params.detectors`; pořadí volání = pořadí v seznamu; A je vždy první.

## 16. Rozhodovací log

Stav: Platí / Předpoklad (s kontrolou při implementaci) / Zrušeno (kolo NN). Kolo 0 = původní zadání před recenzí.

| # | Rozhodnutí | Důvod | Kolo | Stav |
|---|---|---|---|---|
| D-1 | Ø1 je primární výstup; pole `answer` s definicí každé části (1.1) | dodatek 5; bez definice hlavního výstupu nelze komponentu hodnotit | 1 | Platí |
| D-2 | Detektory A (povinný), B (statistický, zapnutý), C (tabulka pokračování), D (ML, vypnutý do splnění brány); ostatní metody z katalogu 15.1 později nebo zamítnuty s důvodem | dodatky 7, 8, 13; priorita spolehlivosti nad úplností | 1 | Platí |
| D-3 | Rozhraní úrovní 3.5 je závazná smlouva pro komponentu SR; sekce 13 zůstává jako akceptační kritéria, postup testů je v `zadani/testy.md`; při rozporu platí tento dokument pro obsah bran | dodatky 4, 12; jeden zdroj pravdy pro rozhraní a kritéria | 1 | Platí |
| D-4 | Chybějící vstup se nikdy neodvozuje uvnitř; zapíše se do `requests` s náhradním chováním (1.5, 3.8) | dodatek 1 | 1 | Platí |
| D-5 | ATR: 30 barů; TR na prvním baru session bez mezery; podlaha 2 ticky | mezera přes hranici session by na 30 barů zdvojnásobila prahy; plochý trh by dal nulový práh | 0/1 | Platí |
| D-6 | Prahy v baru t používají `atr_ref(t) = atr1(t−1)` | dodatek 11: bar nemá ovlivňovat práh, kterým je posuzován | 1 | Platí |
| D-7 | Osa x = index platného baru; sklon v ceně na bar; časy z timestampů | shoda s kreslením TL na grafu | 0 | Platí |
| D-8 | Struktura přes korekce a přijatá low (`prev_major_low`); vnitřní low korekce je přijaté, pokud je nad `prev_major_low`; konec = close pod `prev_major_low` nebo LL swing | původní „nepřerušená sekvence HH + HL“ byla v rozporu s vnitřními swingy pullbacku (jeden stupeň zigzagu); kapitola I.3 vede TL od začátku trendu | 1 | Platí |
| D-9 | `anchor_mode = body` výchozí; prolomení, konec struktury a fáze vždy podle close | kapitola I.3: knoty bez významu; close je jednoznačný | 0/1 | Platí |
| D-10 | Porovnávání cen a hodnot TL v ticích s tolerancí 0,5 ticku; hodnoty v ATR bez tolerance | ceny jsou násobky ticku, rovnost plovoucích čísel je nespolehlivá | 1 | Platí |
| D-11 | Zigzag θ = 3 s prahem z `atr_ref` kandidáta; rovnost ceny nechává starší extrém; pořadí high/low v baru z 1s dat, jinak podle barvy baru; `intrabar_ambiguous` | determinismus; dodatek 2 (1s jen v citlivých místech) | 0/1 | Platí |
| D-12 | Hlavní TL = přímka z `L₀` s minimálním sklonem ke kotvě; ε = 0,5; porušení ε mezi kotvami řeší pseudokotvy; přepočet jen při přijetí low; remíza sklonů → pozdější kotva | původní text neříkal, co se stane při porušení ε; trader vede TL pod porušujícím tělem | 1 | Platí |
| D-13 | Aktuální TL z posledních dvou přijatých low; poměr ≥ 1,5 / ≤ 0,67; hystereze (zůstává do prolomení nebo náhrady); `CURR_TL_DROP` | kapitola I.4; trader zakreslenou čáru neruší při každém přepočtu hlavní TL | 0/1 | Platí |
| D-14 | Prolomení TL = close < TL − ε; událost jen při přechodu; obnovení hlavní TL jen přepočtem s novou kotvou (`TL_REVALIDATED`) | kapitola VI OUT:B; bez nové kotvy trader novou čáru nemá | 0/1 | Platí |
| D-15 | `ENDED` trvá jeden bar; nová struktura z prvního swing low s `t_ext ≥ t_reset`; v `CANDIDATE` close pod `L₀` → NONE, nižší swing low → nový kandidát | úplnost stavového automatu | 1 | Platí |
| D-16 | Fáze podle pořadí 7.1; pořadí vyhodnocení v baru 6.7; `direction` při dvou platných = novější `L₀`, remíza novější kotva, pak UP | determinismus | 1 | Platí |
| D-17 | θ_pb = θ; `H` = běžící maximum extrémů; pullback se po `TL_REVALIDATED` restartuje s `restart = true`; testy hodnotí jen `restart = false` | jinak by se táž korekce počítala dvakrát | 1 | Platí |
| D-18 | `dist_to_level_atr` k nejbližší úrovni na straně, kam pullback míří; `stopped_at_level` z `pb_low`; `levels_missing` = žádná aktivní úroveň v baru | kapitola II (korekce k S/R) | 1 | Platí |
| D-19 | Definice metrik 8.1 včetně hodnot, když nejsou definované (null, 0) | testovatelnost | 1 | Platí |
| D-20 | PW1 nad všemi potvrzenými swingy zigzagu od `L₀` (ne jen kotvami); N = 3, protistrana = 2 po sobě nižší high ze 3 | kapitola VIII posuzuje vlny před vstupní zónou bez ohledu na stupeň | 1 | Předpoklad (kalibrace 12.3) |
| D-21 | PW2 vůči aktuální TL (`pw2 = pw2_curr`), okno od posledního přijatého low; hlavní TL zvlášť (`pw2_main`); δ = 3 | obrázek v kapitole VIII uvádí aktuální TL; maximum od `L₀` by trvale penalizovalo starou odchylku | 1 | Předpoklad (kalibrace 12.3) |
| D-22 | PW3: chop bar = ER20 < 0,25 mimo úroveň; W = 60; `pw3` při < 30 | kapitola VIII: zdržení na S/R není chop | 0 | Předpoklad (kalibrace 12.3) |
| D-23 | `reversal_hint`: null filtr = pass; vše null → null | nelze posoudit ≠ varování | 1 | Platí |
| D-24 | `strength` = průměr (er, 1 − odklon/2δ, sklon/`slope_ref`); třídy 0,6 / 0,3 s monotonní kalibrací | Ø1 vyžaduje skalární sílu; složky jsou dostupné bez učení | 1 | Předpoklad (kalibrace 8.3, 12.3) |
| D-25 | Modul delta: vstup kumulativní delta na bar, režim `close`, reset na začátku session, null v session rollu | kapitola IX; objem rozdělený mezi kontrakty | 1 | Platí |
| D-26 | Rozhraní: Python ≥ 3.11, numpy + pandas; `snapshot`/`from_snapshot`; události s pevnými payloady; `params_hash` | testovatelnost (dodatek 4) | 1 | Platí |
| D-27 | `min_slope` výchozí vypnuto; kalibrace = 10. percentil `slope_norm` TL z obrázků obchodů autora | pravidlo 2 nelze převést na číslo bez měřítka; obrázky ukazují úhly 9°–56° | 1 | Předpoklad (kalibrace 12.3) |
| D-28 | `bar_timestamp = close` výchozí s kontrolou objemem v 09:30 ET; chyba zastaví běh | konvence exportu neověřena (R4) | 1 | Předpoklad (kontrola při implementaci) |
| D-29 | Neplatný bar: `raise` výchozí, `skip` s událostí `BAR_SKIPPED`; ceny mimo tick jen varování | správnost dat je věc datové vrstvy; tichý průchod by skryl chybu | 1 | Platí |
| D-30 | Úroveň aktivní od `valid_from ≤ ts_open(t)`; acyklicita = poskytovatel nečte výstupy komponenty a používá jen bary s `ts_close ≤ valid_from` (i z aktuální seance); duplicity podle `level_id` | kapitola I.2 počítá s S/R vzniklými během seance; původní omezení na uzavřené seance bylo zbytečně přísné | 1 | Platí |
| D-31 | Obchodní deník se používá jen pro kontrolu shody 13.13 (report, ne brána, ne kalibrace) | dodatek 9: nesmí kontaminovat algoritmus; obsahuje jen kladné příklady | 1 | Platí |
| D-32 | CSV z obrázků se používá jen pro kalibraci `min_slope` (D-27) a pro 13.13 | jediný zdroj číselné informace k pravidlu 2 | 1 | Platí |
| D-33 | Základní TF 1min; 1s data jen pro pořadí v baru, jemný čas extrému a remízy v testu; jiné TF se měří v 13.12 s pravidlem doporučení | dodatky 2, 3; P.A.T. je 1min systém s rozhodovacím oknem 3–5 min | 1 | Platí |
| D-34 | Robustnostní brána 13.11: shodné znaménko zisku, rozdíl mezi trhy ≤ 10 p.b., perturbace ±25 % ≤ 10 p.b. | dodatky 6, 10; konkrétní měřitelná definice „podobných výsledků“ | 1 | Předpoklad (prahy se mohou po prvním běhu zpřísnit, ne uvolnit) |
| D-35 | Tabulka pokračování: ≤ 24 pevných binů, `n ≥ 500`, jen vývojové období, kontrola `params_hash` | odpověď na „bude trend pokračovat“ bez učení hranic | 1 | Platí |
| D-36 | Detektor B: okno 60, OLS t-statistika, ER, VR(5); nemění fáze | levné rysy síly bez ladění | 1 | Platí |
| D-37 | Detektor D: GBDT, walk-forward po letech, brána Brier ≥ 0,01 v každém roce + 13.11; vypnutý | dodatek 13 s ochranou proti přeučení | 1 | Platí |
| D-38 | Sekvenční sítě a GPU mimo v1; žádost jen po prokázaném zisku D | řádově 10⁴ nezávislých trendů nestačí; nedeterminismus | 1 | Platí |
| D-39 | Vývojové / testovací období 70/30 chronologicky, testovací jednou se zmrazenými parametry | ochrana proti přeučení | 0 | Platí |
| D-40 | Syntetické scénáře S1–S10 s nezávislým referenčním výpočtem událostí na ideální cestě | brána 13.2.5 musí mít pass/fail | 1 | Platí |
| D-41 | Zapracování dodatků: 1 → 1.5, 3.8; 2 → 3.4, 5.3; 3 → 3.7, 13.12; 4 → 1.4, 10.5, 13; 5 → 1.1, 7.4, 8.3, 15.4; 6 → 11.3, 13.11; 7, 8, 13 → 1.3, 15; 9 → 3.6, 13.13; 10 → 11.3, 13.11; 11 → 3.1, 4.1; 12 → 1.4, 3.5; 14 (kalendář zpráv, doplněný zadavatelem během kola 1) → 3.9, 10.2, 13.6, 15.5, D-45; sekce Dodatky odstraněna | úkol kola 1 | 1 | Platí |
| D-42 | `session_scope = ETH` výchozí; RTH filtrováním barů před vstupem | kapitola I.2 pracuje s premarketem, autor obchoduje od 17:30 SEČ | 0/1 | Platí |
| D-43 | Roll: řada back-adjusted, jen příznak `roll_in_structure`; podezřelá mezera → `ROLL_GAP` | spojitá řada z exportu | 1 | Platí |
| D-44 | Konstanty jen v `TrendParams`; přidání parametru vyžaduje záznam v logu a bránu 13.11 | omezení počtu laděných parametrů | 1 | Platí |
| D-45 | Kalendář zpráv (Forex Factory) jako doplňkový rys (3.9): detektor A ho nečte; `Actual`/překvapení jen u vydání s `DateTime ≤ ts_open(t)`; překvapení z ≥ 12 minulých vydání téže zprávy, jinak 0 + `surprise_missing`; pásmo `Asia/Tehran` → ET s kontrolou na NFP / Unemployment Claims / FOMC; použití = členění 13.6 a rysy D | dodatek 14; P.A.T. zprávy neřeší, zásah do definice trendu podle vnějších dat by porušil soulad; vliv zpráv na pokračování se nejdřív změří | 1 | Předpoklad (kontrola pásma při načtení; přínos ověří 13.6) |
| D-46 | Korekce = `[t_H, t_H')`; bar nového maxima začíná novou korekci; `H_final` v `TREND_END` = běžící maximum při konci (nemusí být potvrzený swing) | jednoznačné přiřazení přijatých low ke korekcím; konec trendu může nastat dřív, než je `H` potvrzený swing | 1 | Platí |

## 17. Historie revizí

| Kolo | Datum | Nálezy B / S / D | Hlavní změny |
|---|---|---|---|
| 0 | — | — | výchozí zadání se sekcí dodatků |
| 1 | 2026-09-25 | 6 / 58 / 11 | zapracováno 14 dodatků (Ø1, detektory, 1s data, TF, testovatelnost, robustnost, deník, SR, indikátory z předchozí svíčky, katalog metod, kalendář zpráv); definice stupňů swingů, pseudokotvy, porovnávání v ticích, konvence timestampu, pořadí v baru, úplný stavový automat, události s payloady, rozhraní, parametry, syntetické scénáře, robustnostní brána; založen rozhodovací log; druhý průchod opravil interval korekce, `prev_major_low` u nového kandidáta, `H_final`, start pullbacku v baru `TREND_START` |

KONEC DOKUMENTU
