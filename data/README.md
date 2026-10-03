# Tržní data (zdroj pravdy)

Tento adresář je jediný zdroj tržních dat pro vývoj a testy komponent systému P.A.T. (zadání v `zadani/`). Dokument je samostatný návod: agent bez znalosti historie projektu podle něj data vyrobí ze souborů Sierra Chart, ověří je a použije. Platí pro všechny symboly. Fakta o jednotlivých symbolech jsou v `data/<SYMBOL>/README.md`.

Stav: 2026-09-28.

## 1. Obsah adresáře

```
data/
  README.md                        tento popis (v gitu)
  <SYMBOL>/
    README.md                      fakta o symbolu: rozsah, rolly, vyřazené dny, díry, zvláštnosti (v gitu)
    <SYMBOL>-1-sec.csv             1s bary (mimo git)
    <SYMBOL>-1-min.csv             1min bary (mimo git)
    <SYMBOL>-rolls.csv             tabulka rollů (mimo git)
    <SYMBOL>-export-report.json    report exportu a ověření (mimo git)
    .scid_export_cache/            cache denních statistik exportu (mimo git, lze smazat)
```

Do gitu patří jen soubory `.md`. CSV a JSON se necommitují: jsou velké a jde o licencovaná data burz, repozitář je veřejný. Pravidla jsou v `.gitignore`.

## 2. Přehled symbolů

| Symbol | Burza | Tick | Obchodní dny | Dnů | 1s řádků | 1min řádků | Rollů | Export | Popis |
|---|---|---|---|---|---|---|---|---|---|
| FDAX | EUREX | 0,5 | 2013-01-07 až 2026-09-25 | 3 483 | 60 600 779 | 3 403 495 | 55 | 2026-09-28, nástroj 1.2, ověřeno 1.3 | [FDAX/README.md](FDAX/README.md) |
| NQ | CME | 0,25 | 2010-12-31 až 2026-09-25 | 4 060 | 143 089 810 | 5 357 648 | 63 | 2026-09-28, nástroj 1.3 | [NQ/README.md](NQ/README.md) |
| ES, YM | CME, CBOT | 0,25 / 1 | — | — | — | — | — | historie v Sierra chybí (soubory prázdné) | — |

Po každém novém exportu se řádek tabulky aktualizuje z reportu (`first_day`, `last_day`, `days_included`, `rows_1sec`, `rows_1min`, počet `rolls`).

## 3. Zdroj: soubory Sierra Chart `.scid`

- **Umístění:** `E:\SierraChart\Data` na počítači zadavatele (v Cowork je složka připojená jako `~/mnt/Data`). Soubory se jen čtou, nikdy se nemění ani nemažou.
- **Jméno:** `<SYMBOL><měsíc><RR>-<BURZA>.scid`, měsíc je kód F G H J K M N Q U V X Z (indexové futures: H = březen, M = červen, U = září, Z = prosinec). Příklady `NQZ26-CME.scid`, `FDAXZ26-EUREX.scid`. Jeden soubor = jeden kontrakt. Jiná jména (`NQZ26.scid`, `NQZ26-CBOT.scid`) nástroj ignoruje.
- **Formát:** hlavička 56 B (`SCID`, na offsetu 4 velikost hlavičky `uint32`, na offsetu 8 velikost záznamu `uint32` = 40). Záznam 40 B, little-endian: `t` int64 = mikrosekundy od 1899-12-30 00:00 **UTC**; `o`, `h`, `l`, `c` float32; `n` (počet obchodů), `v` (objem), `bv` (objem na bid), `av` (objem na ask) uint32. Jeden záznam = jeden obchod (tick). Nástroj používá jen `t`, `c` (cena obchodu), `n`, `v`, `bv`, `av`; `o`, `h`, `l` mají u tickových záznamů jiný význam a nepoužívají se.
- **Co v souborech je:** Sierra ukládá u každého kontraktu data jen za období, které stáhla. U NQ a FDAX to je zhruba od dvou týdnů před expirací předchozího kontraktu do vlastní expirace, takže se sousední kontrakty v době rollu překrývají. Starší roky mohou obsahovat minutové bary nebo obchody bez bid/ask; takové dny export vynechá (8).
- **Stažení dat** dělá zadavatel v Sierra Chart; agent ho udělat nemůže. Agent zkontroluje úplnost (8.3) a chybějící nebo zkrácené kontrakty vypíše zadavateli jménem souboru k novému stažení.

## 4. Export: `tools/scid_export.py`

Požadavky: Python 3.9+, `numpy`, `pandas` (`pip install numpy pandas`). Nic jiného.

Příkaz (Windows, kořen repozitáře):

```bat
python tools\scid_export.py all --data E:\SierraChart\Data --symbol NQ --exchange CME --out data\NQ
python tools\scid_export.py all --data E:\SierraChart\Data --symbol FDAX --exchange EUREX --out data\FDAX
```

V Cowork, kde jedno volání shellu smí běžet nejvýš 180 s, se fáze spouštějí zvlášť s `--budget` a opakují, dokud příkaz vrací kód 3:

```bash
python3 tools/scid_export.py plan     --data ~/mnt/Data --symbol NQ --exchange CME --out data/NQ --budget 140
python3 tools/scid_export.py build    --data ~/mnt/Data --symbol NQ --exchange CME --out data/NQ --budget 150 --stage ~/stage
python3 tools/scid_export.py finalize --data ~/mnt/Data --symbol NQ --exchange CME --out data/NQ
python3 tools/scid_export.py verify   --symbol NQ --exchange CME --out data/NQ --budget 150
```

| Fáze | Co dělá |
|---|---|
| `plan` | přečte denní statistiky všech kontraktů (cache v `<out>/.scid_export_cache`), určí rolly, zařazené a vyřazené dny, změří spready; zapíše `<out>/.<SYMBOL>-plan.json` |
| `build` | zapíše `<SYMBOL>-1-sec.csv.part` a `<SYMBOL>-1-min.csv.part` po kontraktech; přerušený běh pokračuje stejným příkazem (rozpracovaný kontrakt se zahodí a udělá znovu) |
| `finalize` | nahradí hotové CSV najednou (do té doby platí staré), zapíše `<SYMBOL>-rolls.csv` a `<SYMBOL>-export-report.json`, smaže plán a stav |
| `verify` | ověří soubory (9) a zapíše do reportu `verification`, `gaps` a `missing_weekdays` |
| `all` | vše v tomto pořadí |

| Parametr | Výchozí | Význam |
|---|---|---|
| `--data` | — | složka se `.scid` (plan, build) |
| `--symbol` | — | např. `FDAX`, `NQ`, `ES`, `YM` |
| `--exchange` | — | přípona souborů a pravidla burzy: `CME`, `CBOT`, `EUREX` (tabulka `EXCHANGES` v nástroji; nová burza se tam doplní) |
| `--out` | — | výstupní složka, konvence `data/<SYMBOL>` |
| `--tz` | `Europe/Prague` | pásmo časových značek barů |
| `--tick` | podle symbolu | mřížka cen (`TICKS` v nástroji) |
| `--min-bidask` | 0,999 | minimální podíl `(BidVolume + AskVolume) / Volume` dne |
| `--min-records` | 100 | minimální počet záznamů dne |
| `--include-today` | ne | exportovat i dnešní (neúplný) obchodní den |
| `--gap-rth`, `--gap-other` | 5, 60 | verify: hlásit mezery ≥ N minut v hlavní seanci / mimo ni |
| `--budget` | bez limitu | sekund na jeden běh plan, build a verify; pak kód 3 a opakovat |
| `--stage` | — | build: kontrakt se nejdřív zapíše do rychlé lokální složky a pak připojí do `--out` velkými bloky (pro pomalou síťovou nebo synchronizovanou složku) |

Návratové kódy: 0 hotovo, 3 spustit znovu stejný příkaz, jiný = chyba (text chyby na výstupu). Doba v Cowork se zápisem do synchronizované složky: FDAX asi 30 min, NQ asi 65 min (plan 6, build 52, verify 7).

## 5. Formát CSV

Soubory `<SYMBOL>-1-sec.csv` a `<SYMBOL>-1-min.csv`, UTF-8 (jen ASCII), konce řádků LF, hlavička:

```
Date,Time,Open,High,Low,Last,Volume,NumberOfTrades,BidVolume,AskVolume,Contract
2013/1/7,08:00:00,7765,7769,7763,7767.5,673,121,560,113,FDAXH13
```

| Sloupec | Význam |
|---|---|
| `Date` | datum začátku baru v `Europe/Prague`, tvar `R/M/D` bez úvodních nul |
| `Time` | čas začátku baru v `Europe/Prague`, `HH:MM:SS` |
| `Open`, `High`, `Low`, `Last` | první, nejvyšší, nejnižší a poslední cena obchodu v baru, na mřížce ticku |
| `Volume` | zobchodované kontrakty |
| `NumberOfTrades` | počet obchodů |
| `BidVolume` | kontrakty zobchodované na bid (agresor prodávající) |
| `AskVolume` | kontrakty zobchodované na ask (agresor kupující) |
| `Contract` | zdrojový kontrakt, např. `NQZ26` |

- Bar je označený **začátkem** intervalu. Bar vzniká jen v sekundě nebo minutě s obchodem; prázdné bary nejsou, chybějící minuta = žádný obchod.
- Řádky jsou seřazené podle času bez duplicit. 1min bar = souhrn 1s barů téže minuty (ověřuje `verify`).
- Delta baru = `AskVolume − BidVolume`. `BidVolume + AskVolume = Volume` platí až na ojedinělé bary (počty v reportu, `bidask_ne_volume_*`).
- Ceny nejsou upravené o rollover; spojitou řadu sestaví datová vrstva (7.3).

Načtení (pandas):

```python
import pandas as pd
df = pd.read_csv('data/NQ/NQ-1-min.csv')
ts = pd.to_datetime(df.Date + ' ' + df.Time, format='%Y/%m/%d %H:%M:%S').dt.tz_localize('Europe/Prague')
```

Nejednoznačné ani neexistující časy (přechod letního času) v datech nejsou, protože burzy v té hodině neobchodují; kdyby `tz_localize` hlásil chybu, jde o chybu dat.

## 6. Čas a obchodní den

- Časové značky jsou v `Europe/Prague`, začátek baru.
- **Obchodní den** je den burzy, ne kalendářní den v Praze. Podle něj se zařazují dny, přepíná kontrakt při rollu a staví kalendář session:
  - **CME, CBOT** (NQ, ES, YM): obchodní den D trvá od 17:00 `America/Chicago` dne D−1 do 17:00 dne D (18:00–17:00 ET). V Praze je to obvykle 00:00–23:00 dne D; v týdnech, kdy USA a Evropa mají jiný čas (březen, přelom října a listopadu), 23:00 dne D−1 až 22:00 dne D.
  - **EUREX** (FDAX): kalendářní den v `Europe/Berlin` (= Praha).
- Výpočet z CSV:

```python
td = (ts.dt.tz_convert('America/Chicago') + pd.Timedelta(hours=7)).dt.tz_localize(None).dt.normalize()   # CME, CBOT
td = ts.dt.tz_localize(None).dt.normalize()                                                             # EUREX
```

- Export session nefiltruje: obsahuje celý obchodní den včetně ojedinělých záznamů mimo obchodní hodiny, které popisuje README symbolu. Kalendář session a vyřazení barů mimo obchodní hodiny dělá datová vrstva (10).

## 7. Rollover

### 7.1 Pravidlo

- Každý kontrakt je front od začátku obchodního dne rollu do začátku dalšího rollu. Všechny bary jednoho obchodního dne jsou z jednoho kontraktu.
- Den rollu = první obchodní den v okně 21 dní před expirací (3. pátek měsíce kontraktu) aktuálního kontraktu, kdy má další kontrakt vyšší denní objem. Počítají se jen pracovní dny, kdy mají oba kontrakty aspoň `--min-records` záznamů (jinak by roll spustil artefakt, např. jediný nedělní záznam). Nenastane-li to, roll je v den expirace (`expiry-fallback`); chybí-li mezi kontrakty soubor, `hole`.
- Ceny se **neupravují**; sloupec `Contract` říká, ze kterého kontraktu bar je.

### 7.2 `<SYMBOL>-rolls.csv`

| Sloupec | Význam |
|---|---|
| `roll_day` | obchodní den, od jehož začátku platí nový kontrakt |
| `from_contract`, `to_contract` | starý a nový kontrakt |
| `rule` | `volume`, `expiry-fallback` nebo `hole` |
| `first_day_of_new_contract` | první zařazený den nového kontraktu (obvykle = `roll_day`) |
| `spread_to_minus_from` | medián rozdílu `Last` (nový − starý) přes posledních 60 minut obchodovaných v obou kontraktech posledního obchodního dne před rollem, zaokrouhlený na tick |
| `spread_minutes` | počet minut, ze kterých je spread spočítaný |
| `spread_measured_on` | obchodní den měření |

### 7.3 Spojitá řada (dělá datová vrstva)

Komponenty dostávají spojitou řadu **zpětně aditivně posunutou**: bar s obchodním dnem `d` dostane `adj(d) = Σ spread_to_minus_from` přes všechny rolly s `roll_day > d`. Poslední kontrakt má skutečné ceny. Posun je násobek ticku, takže ceny zůstanou na mřížce a vzdálenosti v bodech uvnitř kontraktu se nezmění; poměrový posun by mřížku porušil a nepoužívá se.

```python
import numpy as np
r = pd.read_csv('data/NQ/NQ-rolls.csv', parse_dates=['roll_day']).sort_values('roll_day')
roll = r.roll_day.to_numpy().astype('datetime64[D]')
cum = np.r_[np.cumsum(r.spread_to_minus_from.to_numpy()[::-1])[::-1], 0.0]   # součet spreadů rollu i a pozdějších
i = np.searchsorted(roll, td.to_numpy().astype('datetime64[D]'), side='right')  # počet rollů s roll_day <= d
adj = cum[i]
for c in ('Open', 'High', 'Low', 'Last'):
    df[c] = df[c] + adj
```

Úrovně nebo obchody se skutečnými cenami (např. z deníku) se před porovnáním s řadou posunou o stejné `adj(d)`. Kontrola: sloupec `Contract` se mění právě na prvních barech dnů `roll_day`.

## 8. Zařazení dnů a úplnost

### 8.1 Pravidla

Obchodní den je v exportu, jen když:

1. není sobota ani neděle (obchodní den burzy; víkendové záznamy jsou artefakty, např. testovací seance),
2. front kontrakt má skutečné ticky s klasifikací bid/ask: `(BidVolume + AskVolume) / Volume ≥ 0,999`,
3. má aspoň 100 záznamů,
4. není dnešní ani pozdější (neúplný den).

Vše před prvním dnem, který pravidla splní, se vynechá (`days_skipped_before_start`). Pozdější dny, které je nesplní, jsou v reportu v `excluded_days` s důvodem.

### 8.2 Report `<SYMBOL>-export-report.json`

| Klíč | Obsah |
|---|---|
| `version`, `created`, `rules`, `exchange_rules`, `tick`, `tz` | verze nástroje, čas a pravidla exportu |
| `sources` | zdrojové soubory: velikost, čas změny, první a poslední obchodní den |
| `empty_files`, `holes` | prázdné soubory; chybějící kontrakty mezi soubory s daty |
| `first_day`, `last_day`, `days_included`, `days_skipped_before_start`, `excluded_days`, `skipped_incomplete_days` | rozsah a zařazení dnů |
| `rolls` | totéž co `<SYMBOL>-rolls.csv` |
| `rows_1sec`, `rows_1min`, `total_volume`, `total_records` | velikost výstupu |
| `out_of_order`, `off_grid_records` | záznamy mimo časové pořadí a ceny mimo mřížku ticku (zaokrouhlené), po kontraktech |
| `verification` | výsledky kontrol (9), `passed` |
| `gaps` | úseky bez obchodů: v hlavní seanci ≥ 5 min, mimo ni ≥ 60 min, pozdní začátek, předčasný konec a den bez hlavní seance |
| `missing_weekdays` | pracovní dny bez dat v rozsahu (svátky burzy, vyřazené dny, díry) |

### 8.3 Kontrola úplnosti zdroje (před exportem i po něm)

1. `plan`: v logu a v `.<SYMBOL>-plan.json` zkontroluj `holes` (musí být prázdné), `empty_files` (jen kontrakty před začátkem dat) a v `sources` první a poslední den každého kontraktu (každý musí sahat aspoň do svého dne rollu).
2. Po `verify`: `missing_weekdays` porovnej se svátky burzy; zbytek jsou díry. `gaps` porovnej se známými událostmi trhu (zkrácené seance, přerušení obchodování, výpadky burzy); zbytek jsou díry v datech.
3. Díry se zapíšou do README symbolu. Chybí-li celý kontrakt nebo jeho část, požádej zadavatele o nové stažení konkrétních souborů v Sierra Chart a export zopakuj.

## 9. Ověření (`verify`)

Kontroly (výsledek v `verification`, `passed = true` jen když projdou všechny povinné):

- počty řádků souhlasí s reportem (povinné),
- agregace 1s barů po minutách dává přesně 1min soubor ve všech sloupcích včetně `Contract` (povinné),
- časy rostou bez duplicit, OHLC jsou konzistentní, ceny jsou kladné a na mřížce ticku, objem > 0 (povinné),
- `Contract` se mění jen na prvním baru dne rollu (povinné),
- počty barů s `BidVolume + AskVolume ≠ Volume` (informativní),
- `gaps` a `missing_weekdays` (informativní, posuzuje se podle 8.3).

## 10. Použití v komponentách

Komponenta a její testy (`zadani/komponenta-trend.md`: detektory, modul SR 3.10, testovací harness 13.16–13.20) čtou data jen přes datovou vrstvu, která:

1. načte CSV a lokalizuje čas (`Europe/Prague`, 5),
2. přiřadí obchodní den a session podle burzy (6) a vynechá bary mimo obchodní hodiny burzy (README symbolu),
3. sestaví spojitou řadu zpětným aditivním posunem (7.3) a předá `roll_day` jako data rollu,
4. předá díry z `gaps` a `missing_weekdays` (komponenta mezery nedoplňuje),
5. dodá 1s bary pro rozhodnutí uvnitř 1min baru (stejné dny a konvence jako 1min).

## 11. Postup pro nový symbol nebo nový export (pro agenta)

1. Ověř, že v `E:\SierraChart\Data` jsou soubory `<SYMBOL><měsíc><RR>-<BURZA>.scid` pro všechny kontrakty období a nejsou prázdné (56 B = prázdný).
2. Je-li burza nová, doplň ji do `EXCHANGES` v nástroji (pásmo, začátek obchodního dne, hlavní seance); je-li symbol nový, doplň tick do `TICKS` nebo použij `--tick`.
3. Spusť `plan` a zkontroluj úplnost (8.3, bod 1). Chybí-li kontrakty, požádej o stažení a skonči.
4. Spusť `build` (opakuj při kódu 3), `finalize` a `verify`. `verification.passed` musí být `true`.
5. Napiš nebo aktualizuj `data/<SYMBOL>/README.md` podle vzoru existujících (rozsah, rolly, vyřazené dny, díry s posouzením, zvláštnosti trhu, ověření) a řádek tabulky v 2.
6. Commitni jen soubory `.md` (a změny nástroje). Data se necommitují.

## 12. Omezení

- ES a YM: soubory v Sierra jsou prázdné, data chybí.
- Hlavní seance pro report děr (`EXCHANGES.rth`) platí pro indexové futures; jiné produkty potřebují vlastní hodnoty.
- Sierra ukládá ceny jako float32; export je zaokrouhluje na tick (počty v `off_grid_records`).
- Pořadí záznamů: čas oříznutý na sekundu, stabilní řazení (uvnitř sekundy pořadí ze souboru); počty záznamů mimo pořadí v `out_of_order`.
- FDAX byl exportován nástrojem 1.2; pravidla verze 1.3 pro něj dávají stejný výsledek (`data/FDAX/README.md`).
