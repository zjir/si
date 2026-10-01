# PAT_obchody_z_obrazku.csv – popis

**Účel.** Obchody ze screenshotů ve složce `obrazky-obchodu\` (NQ, 1min graf, Sierra Chart) převedené na řádky se strukturou podle `Obchodní deník.xls` (list *Obchody*). Deník zůstává beze změny.

**Formát.** CSV, kódování UTF-8 s BOM, oddělovač `;`, desetinná čárka, datum `RRRR-MM-DD`, čas `HH:MM`. Časy jsou podle časové osy grafu, tj. středoevropský čas (americká seance začíná v 15:30). Jeden řádek odpovídá jednomu obchodu. Obrázek se dvěma obchody (např. `3.4.png`) dává dva řádky. Když je stejný obchod (stejné datum, čas, směr a vstup) ve více obrázcích, má jen jeden řádek a sloupec *Obrázek* obsahuje všechny názvy oddělené `; `.

Čtení v Pythonu: `pd.read_csv(cesta, sep=';', decimal=',', encoding='utf-8-sig')`.

## Typ záznamu (1. sloupec)

| Hodnota | Význam |
|---|---|
| `REAL` | Obchod z obrázku byl nalezen v `Obchodní deník.xls`. Shoda = stejné datum, stejný směr, vstup ±2 ticky (±0,5 bodu) a čas vstupu ±5 min; při více kandidátech rozhoduje nejbližší čas. Obchod mimo tyto tolerance je jiný obchod a zůstává GUESSED. Sloupce *Datum* až *OUT: B výstup* jsou skutečné hodnoty převzaté z deníku a číslo obchodu je ve sloupci *Obchod (deník)*. Zbylé sloupce jsou i u REAL čtené nebo odhadnuté z obrázku: *Čas výstupu*, *Vstupní zóna*, *Typ PT*, *Typ SL*, *PW-SW*, *Trend směr*, *TL …*, *Graf …*, *OHLC …*, *S/R …* a *Úroveň vstupní zóny*. |
| `GUESSED` | Obchod v deníku není, všechny hodnoty pocházejí z obrázku. Část z nich je přesná, protože je přečtená z infoboxu obchodníka: vstup, výstup, směr, RRR, P/L, vstupní zóna, typ PT/SL a PW-SW. Část je dopočtená z těchto hodnot: SL, PT a ticky. Zbytek je odhad z pixelů grafu s přesností ±1 tick a ±1 min: čas, MAE, MFE, TL, S/R a OHLC úrovně. Zdroj každého sloupce udává tabulka *Sloupce*. |

Deník pokrývá období 15. 9. 2010 – 14. 8. 2014 (obchody 1–597). Obrázek s datem mimo toto období nemůže být REAL.

## Sloupce

Zdroj u řádků GUESSED: **I** = přečteno z infoboxu v obrázku, **V** = dopočteno z hodnot infoboxu nebo z čar PT/SL v grafu, **G** = odhad z pixelů grafu, **N** = z názvu souboru. Zdroj u řádků REAL: **D** = převzato z deníku.

| Sloupec | Význam | GUESSED | REAL |
|---|---|---|---|
| Typ záznamu | viz výše | – | – |
| Obrázek | název souboru v `obrazky-obchodu\` (zdroj řádku) | N | N |
| Obchod v obrázku | pořadí obchodu v obrázku podle času vstupu (1, 2, …) | G | G |
| Číslo dle názvu obrázku | číslo odvozené z názvu (`3.4.png` → 3 a 4); nejde o číslo z deníku | N | N |
| Obchod (deník) | číslo obchodu v deníku | prázdné | D |
| Datum | datum obchodu | hlavička grafu | D |
| Čas | čas vstupní 1min svíčky podle osy grafu; odpovídá sloupci *Čas* v deníku (ověřeno na 4 REAL obchodech) | G | D |
| Trh | kontrakt ve formátu deníku (`NQZ4` = NQ prosinec 2014); front-month podle data | G | D |
| L/S | 1 = Long, 0 = Short (kódování deníku) | I | D |
| Vstup | vstupní cena; ověřeno proti close vstupní svíčky | I | D |
| SL | stop-loss | V | D |
| SL (tick) | vzdálenost SL od vstupu v ticích (1 tick = 0,25 bodu = 5 USD) | V | D |
| PT | profit target | V | D |
| PT (tick) | vzdálenost PT od vstupu v ticích | V | D |
| RRR | PT (tick) / SL (tick) | I nebo V | D |
| MAE (hodnota) | nejhorší cena proti pozici (metoda níže) | G | D |
| MAE (tick) | vzdálenost MAE od vstupu v ticích | G | D |
| MFE (hodnota) | nejlepší cena ve směru pozice (metoda níže) | G | D |
| MFE (tick) | vzdálenost MFE od vstupu v ticích | G | D |
| Zisk | 1 = ziskový obchod | I | D |
| Ztráta | 1 = ztrátový obchod | I | D |
| P/L | USD na 1 kontrakt včetně RT komise 5 USD (výstup OUT: A) | I | D |
| Výstup | skutečná výstupní cena | I | D (PT při zisku, SL při ztrátě) |
| Čas výstupu | první svíčka po vstupu, která dosáhla výstupní ceny | G | G |
| Vstupní zóna | A / B / C podle P.A.T. | I | I |
| Typ PT | A / B / C (výjimečně `B+`, jak je v infoboxu) | I | I |
| Typ SL | A / B | I | I |
| PW-SW | Ano / Ne; ve screenshotech z února 2014 infobox PW-SW neuvádí (prázdné) | I | I |
| OUT: C výstup | výstupní cena alternativního výstupu OUT: C | prázdné | D |
| OUT: B výstup | výstupní cena alternativního výstupu OUT: B | prázdné | D |
| Trend směr | UP / DOWN, směr trendové linie (TL) | G | G |
| TL zdroj | `zakreslená žlutá/zelená/červená` = TL změřena z čáry v obrázku; `odhad (TL nezakreslena)` = TL odhadnuta | G | G |
| TL typ | `hlavní` / `aktuální` trend (metoda níže) | G | G |
| TL sklon (°) | úhel TL vůči ose X v měřítku screenshotu | G | G |
| TL sklon (bodů/min) | sklon TL nezávislý na měřítku (absolutní hodnota) | G | G |
| TL bod 1, TL bod 2 | u zakreslené TL začátek a konec čáry, u odhadu dvě kotvy; ve tvaru `HH:MM @ cena` | G | G |
| TL cena v čase vstupu | cena na TL v minutě vstupu | G | G |
| Graf px/bod | svislé měřítko screenshotu (pixelů na 1 bod) | G | G |
| Graf px/min | vodorovné měřítko screenshotu (pixelů na 1 svíčku) | G | G |
| OHLC předchozího dne | ceny fialových čar (legenda P.A.T.: OHLC minulého dne), oddělené ` \| `, od nejvyšší | G | G |
| S/R úrovně | ceny S/R čar ve tvaru `cena barva` (černá, modrá, šedá), oddělené ` \| `, od nejvyšší | G | G |
| Úroveň vstupní zóny | čára (OHLC nebo S/R), která je nejblíže ceně TL v čase vstupu (max. 3 body), ve tvaru `cena OHLC` nebo `cena S/R barva` | G | G |
| Poznámka | u REAL číslo řádku v deníku; opravy překlepů v infoboxu, rozpory, omezení měření | – | – |
| Zpracováno | datum zpracování řádku | – | – |

## Barvy čar podle `Popis OS P.A.T.pdf`

| Barva v grafu | Význam podle PDF | Použití v CSV |
|---|---|---|
| fialovo-růžová | OHLC minulého dne | sloupec *OHLC předchozího dne* |
| šedá; v grafech z roku 2014 kreslena černě | S/R premarketu a S/R minulého dne | sloupec *S/R úrovně* |
| modrá (vodorovná čára přes graf) | PDF ji nepopisuje (modře jsou v PDF jen obdélníky vstupních zón a krátké značky swingů v kapitole PW-SW). V obrázcích funguje jako S/R, např. PT: B v `3.4.png` leží na modré čáře. | sloupec *S/R úrovně* s označením `modrá` |
| žlutá | TL hlavního trendu | *TL zdroj*, *TL typ* = hlavní |
| zelená / červená (šikmá) | TL aktuálního uptrendu / downtrendu | *TL zdroj*, *TL typ* = aktuální |
| červená vodorovná | PT (u OUT: B posunutý SL) | kontrola PT, do S/R se nepočítá |
| tyrkysová | SL | kontrola SL, do S/R se nepočítá |
| bílá šipka / červená šipka | vstup / výstup | čas vstupu |

Barvy se určují z pixelů. Tenká fialová čára na zmenšeném náhledu vypadá šedě, v datech je ale fialová.

## Metody

**Kalibrace os.** Popisky cenové osy se čtou pomocí OCR a proloží se lineární závislostí pixel → cena; odlehlé hodnoty se vyřadí. Časová osa se kalibruje z popisků času, 1 svíčka = 1 minuta. OHLC každé svíčky se odečítá z pixelů (knot = střední sloupec, tělo = boční sloupce). Přesnost cen je ±1 tick, přesnost časů ±1 min. `14.png` je degradovaný (JPEG), přesnost je u něj horší.

**Vstup.** Vstupní svíčku označuje bílá šipka: pod svíčkou pro long, nad svíčkou pro short. Cena IN z infoboxu se kontroluje proti close této svíčky. Zjevný překlep, např. `3848,00` místo `3948,00`, se opraví a zapíše do Poznámky. Infobox se k šipce přiřazuje podle ceny IN.

**SL a PT.** Infobox uvádí IN, OUT, RRR a P/L. Ve starších screenshotech je RRR ve tvaru `1:2,00`, u některých obchodů chybí.
- Ziskový obchod: PT = OUT, PT (tick) = |OUT − IN| / 0,25, SL (tick) = zaokrouhlení (PT (tick) / RRR).
- Ztrátový obchod: SL = OUT, SL (tick) = |OUT − IN| / 0,25, PT (tick) = zaokrouhlení (SL (tick) × RRR).
- Když RRR chybí, bere se SL z tyrkysové čáry a PT z červené čáry u obchodu; RRR se pak dopočítá.
- Kontrola: P/L = ±ticky × 5 USD − 5 USD. Nesoulad se zapíše do Poznámky.

**MAE / MFE.** Popis P.A.T. okno měření neuvádí. Pravidlo je proto zvoleno tak, aby odpovídalo deníku. Na 4 REAL obchodech (473, 474, 475, 480) sedí MAE i MFE s deníkem přesně, u degradovaného `14.png` s odchylkou 1 tick.
1. Po dobu obchodu (od svíčky po vstupu do svíčky výstupu) se MAE i MFE aktualizují vždy.
2. Po výstupu se MAE může dál prohlubovat, dokud cena nepostoupí ve směru obchodu aspoň o velikost SL. Od té chvíle okno končí první svíčkou, která překoná dosavadní MAE.
3. Když k tomu nedojde, okno končí koncem grafu a Poznámka to uvádí.

Když cena proti pozici vůbec nešla, MAE = vstup (0 ticků).

**Trendová linie (TL).** Když je TL v obrázku zakreslena (žlutá, zelená nebo červená šikmá čára), změří se přímo. Použije se čára se sklonem ve směru obchodu, která začíná před vstupem a v minutě vstupu je nejblíže extrému pullbacku. Když TL zakreslena není, odhadne se podle pravidla P.A.T.: uptrend spojuje swingová low, downtrend swingová high.
- Kotvy jsou dva swingové extrémy (extrém v okolí ±3 svíček) po nejnižším low (long) nebo nejvyšším high (short) za posledních 150 minut před vstupem. Kotvy jsou od sebe aspoň 10 minut.
- Podmínky: sklon ve směru obchodu; mezi první kotvou a vstupem těla svíček linii neprorazí o více než 1 tick. Knoty prorazit smí, jako v P.A.T. Tolerována je nejvýše 1 výjimka.
- Vybere se linie, která v minutě vstupu leží nejblíže extrému pullbacku (low/high posledních 3 svíček do vstupu). Rozdíly do 2 ticků se berou jako shodné a pak rozhoduje větší počet dotyků a delší linie.
- Každá TL je vizuálně zkontrolována v překresleném grafu.

Úhel = arctan(sklon [bod/min] × px/bod ÷ px/min). Úhel závisí na měřítku screenshotu. Pravidlo č. 2 P.A.T. (trend se sklonem pod 45° vynechat) se vztahuje k měřítku grafu obchodníka, které se se screenshotem shodovat nemusí. Pro srovnání mezi obrázky je vhodnější *TL sklon (bodů/min)*.

**TL typ.** U zakreslené TL podle barvy: žlutá = hlavní, zelená/červená = aktuální. U odhadu podle vstupní zóny z infoboxu (definice P.A.T.):
- VZ A = hlavní TL × OHLC → hlavní.
- VZ C = aktuální TL × S/R → aktuální.
- VZ B = hlavní TL × S/R nebo aktuální TL × OHLC → podle toho, zda *Úroveň vstupní zóny* je S/R (hlavní), nebo OHLC (aktuální).

**Doplňky metody (od 28. 9. 2026)**
- *Datum a trh.* Datum grafu se čte OCR z hlavičky ve třech výškách pásu a rozhoduje většina (text bývá posunutý o 2 px, jinak se čte např. 12 místo 13). Trh = front month NQ podle data (roll 8 dní před 3. pátkem měsíce expirace). Když hlavička grafu uvádí jiný kontrakt (typicky v den rollu), platí kontrakt z hlavičky a uvede se v Poznámce.
- *Časová osa.* Popisky času se přepočtou na index svíčky. Chybně přečtené popisky se vyřadí: posun (x − index × px/min) musí s časem klesat, bere se nejdelší konzistentní posloupnost. Samostatný popisek se použije jen po obvyklé přestávce (21:30–23:00 nebo 23:59–01:00). Skutečné mezery v datech (např. zkrácený obchodní den 3. 7.) zůstávají.
- *Opravy infoboxu* (každá je uvedena v Poznámce):
  - IN nesedí s grafem, OUT a P/L jsou konzistentní → IN dopočten z OUT a P/L.
  - IN i OUT o více než 20 bodů mimo graf (překlep) → IN = close vstupní svíčky, OUT posunut o stejný rozdíl a zkontrolován přes P/L.
  - Position (Long/Short) v rozporu s IN/OUT/P/L i se šipkou → směr podle šipky a IN/OUT/P/L.
  - OUT v rozporu se směrem a P/L → OUT dopočten z P/L.
- *Duplicitní obrázky.* Stejný obchod bývá na více obrázcích (screenshot se zakreslenou TL, čistý screenshot, graf dalšího dne). Obchod má jeden řádek; sloupec Obrázek obsahuje názvy oddělené „; “, první je primární zdroj. Když duplicitní obrázek má zakreslenou TL a řádek měl jen odhad, TL se převezme ze zakreslené čáry (Poznámka „TL převzata ze zakreslené čáry v …“).
- *Graf bez infoboxu* (bílé šipky bez infoboxu, typicky graf následujícího dne): šipky se spárují s obchody jiného obrázku podle data (stejný nebo předchozí den), směru, času a ceny. Progress uvádí „bez infoboxu – stejné obchody jako X.png“.
- *Grafy bez obchodu.* Ranní grafy (0:30–13:30, bez data v hlavičce) a grafy bez bílé šipky a infoboxu se po vizuální kontrole zapíší do progress jako ZPRACOVÁNO s 0 obchody.
- *Kontrola dávky.* Po každé dávce se CSV na počítači porovná se zpracovanými daty: shoda hodnot, žádný duplicitní klíč (Datum, Čas, L/S, Vstup), P/L = ±ticky × 5 − 5.

## Nástroje (skripty)

Data vyrábějí skripty v Pythonu uložené v projektu „Super intelligence“ na claude.ai jako dokumenty `claude/…`; ve složce PAT ani v repozitáři nejsou. Postup krok za krokem (dávky, kontroly, zápis) je v dokumentu projektu `claude/PAT_postup.md`. „Kontejner“ = pracovní prostředí Claude, „počítač“ = počítač zadavatele (zápis do složky PAT).

| Skript v projektu | Kde běží | Co dělá |
|---|---|---|
| `claude/pat_extract.py` | kontejner | extrakce z jednoho screenshotu: barvy podle palety, kalibrace cenové a časové osy (OCR popisků, lineární proložení), OHLC svíček z pixelů, vodorovné a zakreslené šikmé čáry s barvou, bílé šipky (vstupy), OCR hlavičky (datum, kontrakt) a infoboxů |
| `claude/pat_pipeline.py` | kontejner | z extrakce sestaví obchody: čtení infoboxu a jeho párování se šipkou, opravy překlepů, SL/PT/RRR, čas výstupu, MAE/MFE, TL (zakreslená nebo odhad), úrovně a vstupní zóna, párování s deníkem (funkce `match_journal`: datum, směr, vstup ±0,5 bodu, čas ±5 min), řádky CSV; příkazy `analyze`, `append`, `init-progress` |
| `claude/pat_batch_run.py` | kontejner | dávka obrázků přes `pat_pipeline` (paralelně), příznaky anomálií, náhledy s překreslením, kompaktní zápisy `run/batch_<id>.jsonl` |
| `claude/pat_fix_noinfobox.py` | kontejner | obchody z grafů bez infoboxu spáruje s obchody jiného obrázku (datum, směr, čas a vstup v tolerancích) a zapíše je jako duplicitu |
| `claude/pat_mark_empty.py` | kontejner | označí obrázky bez obchodu po vizuální kontrole |
| `claude/pat_thumbs.py` | kontejner | mřížka náhledů pro vizuální kontrolu |
| `claude/pat_next_batch.py` | kontejner | vybere dalších N obrázků se stavem NEZPRACOVÁNO |
| `claude/pat_cmds.py` | kontejner | vytiskne příkazy zápisu na počítač, pro každý obrázek zvlášť; duplicity zkráceně |
| `claude/pat_append_dev.py` | počítač (`~/pat_append_dev.py`) | zapíše řádky jednoho obrázku do CSV a progress ve složce PAT, sloučí duplicity, převezme zakreslenou TL; předchozí stav zálohuje do `~/pat_backup/` |
| `claude/pat_dup.py` | počítač (`~/pat_dup.py`) | krátký zápis obrázku, jehož obchody už v CSV jsou |
| `claude/pat_verify_batch.py` | kontejner | po dávce porovná CSV a progress z počítače s očekávanými zápisy (hodnoty, počty, duplicitní klíče) |

Závislosti: Python 3, numpy, Pillow, scipy, pytesseract s programem tesseract, xlrd (čtení deníku `.xls`).

- *Český infobox (od 08/2016):* Vstup, Výstup, Vstupní zóna nebo Pozice, RRR, Typ PT, Typ SL, Profit (vč. RT). Čte se OCR z původního obrázku ve stupních šedi. Bez pole Pozice se směr určí ze šipky (šipka pod svíčkou = long, nad svíčkou = short) a z IN/OUT/P/L. Pozice v rozporu s IN/OUT/P/L (překlep obchodníka) → směr podle IN/OUT/P/L a šipky, uvedeno v Poznámce.
- *Svíčky od 08/2016:* rostoucí svíčka má obrys (0,128,0) a jasně zelenou výplň (0,255,0). Výplň se počítá do svíčky (jinak by high/low odpovídalo tělu místo knotu) a nebere se jako zelená TL. Text infoboxu (červený Profit) se nebere jako svíčka ani TL.
- *Zakreslená TL:* použije se, když v minutě vstupu leží do 4 bodů od extrému pullbacku; když je čára zakreslena přes čas vstupu, do 8 bodů.
- *Více infoboxů a šipek:* infobox se k šipce přiřazuje podle rozdílu IN – close vstupní svíčky a směru; při podobných cenách rozhoduje pořadí zleva doprava.
- *Graf přes půlnoc:* když hlavička ukazuje čas po půlnoci, obchod z večera patří k předchozímu dni (uvedeno v Poznámce).
- *Screenshot bez hlavičky* (1142, 1143): datum 2016-10-21 odvozeno z pořadí obrázků (grafy obchodních dnů čt/pá), uvedeno v Poznámce.
- Obrázky 9991–9997 jsou duplicitní s obchody z listopadu a prosince 2014, 9999 je REAL obchod z 6. 2. 2014.

## Průběh zpracování – `PAT_obrazky_progress.csv`

Soubor obsahuje všechny obrázky ze složky `obrazky-obchodu\` v pořadí zpracování, řazené číselně podle názvu (1, 2, 3.4, 5.6, 7, 7.8, 8, …, 9999). Sloupce:
- *Pořadí*, *Obrázek*
- *Stav*: `NEZPRACOVÁNO` / `ZPRACOVÁNO` / `CHYBA`
- *Počet obchodů*, *Výsledek* (REAL / GUESSED, případně duplicita), *Datum grafu*, *Zpracováno*, *Poznámka*

Pokyn „vem N obrázků“ nebo „dále“ znamená: zpracovat dalších N obrázků se stavem `NEZPRACOVÁNO` v pořadí sloupce *Pořadí*. CSV i progress se ukládají po každém zpracovaném obrázku.

Čísla v názvech obrázků neodpovídají pořadí v čase: `7.png`, `8.png` a `14.png` jsou z února 2014 (REAL), okolní obrázky z října a listopadu 2014.
