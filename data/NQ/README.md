# NQ – futures E-mini Nasdaq-100 (CME)

Obecná pravidla, formát a postup exportu: [`data/README.md`](../README.md). Tady jsou jen fakta o NQ. Stav k 2026-09-28.

## Soubory

| Soubor | Obsah |
|---|---|
| `NQ-1-sec.csv` | 143 089 810 řádků, 9,15 GB |
| `NQ-1-min.csv` | 5 357 648 řádků, 362 MB |
| `NQ-rolls.csv` | 63 rollů |
| `NQ-export-report.json` | report exportu, `verification`, `gaps`, `missing_weekdays` |

- Zdroj: `E:\SierraChart\Data\NQ<H|M|U|Z><RR>-CME.scid`; 64 souborů s daty (NQH11 až NQZ26, žádný kontrakt nechybí) a 18 prázdných (NQU06 až NQZ10). `NQZ26.scid` a `NQZ26-CBOT.scid` jsou prázdné a k řadě nepatří. Soubory NQ byly 2026-09-28 staženy znovu; dřív končil NQM25 2025-05-15 a NQU25 až NQU26 byly prázdné.
- Export 2026-09-28 nástrojem verze 1.3, `verify` prošel.
- Příkaz: `python tools\scid_export.py all --data E:\SierraChart\Data --symbol NQ --exchange CME --out data\NQ`
- Nahrazuje dřívější CSV exporty NQ z grafu Sierra (UTC, continuous rollover, díra 2025-05-15 až 2026-09-14).

## Trh a čas

- Kontrakty březen, červen, září, prosinec; expirace 3. pátek v měsíci (NQM26 má poslední obchodní den v datech 2026-06-18). Tick 0,25; všechny ceny ve zdroji jsou přesně na mřížce.
- Obchodní den CME D: 17:00 CT dne D−1 až 16:00 CT dne D (18:00–17:00 ET), denní přestávka 16:00–17:00 CT. V Praze obvykle 00:00–23:00 dne D; v týdnech, kdy USA a Evropa mají jiný čas, 23:00 D−1 až 22:00 D.
- Konec seance v datech (CT): út–čt 16:30 (2011–2012), 16:15 (2013–2015), 16:00 (od 2016); v pátek 15:15 (2011–2012), 16:15 (2013–2015), 16:00 (od 2016).
- Hlavní seance (RTH) 08:30–15:00 CT = 09:30–16:00 ET, v Praze obvykle 15:30–22:00 (v týdnech s rozdílným letním časem 14:30–21:00); podle ní se hlásí díry.
- Svátky USA se zkrácenou seancí: konec 10:30 CT (2011–2013) nebo 12:00 CT (od 2014); den po Díkůvzdání, Štědrý den a 3. 7. konec 12:15 CT. V reportu 131 dnů `main session ends early`.

## Rollover

- 63 rollů od 2011-03-11 (NQH11 → NQM11) do 2026-09-14 (NQU26 → NQZ26), všechny podle objemu (`volume`).
- 2011–2019 v pátek týden před expirací; od 2020 v pondělí týdne expirace (2024–2025 třikrát v úterý, 2021 jednou v pátek týden před).
- Spready −14,25 až +296,25 bodu, součet +3 738,75 (o tolik se ve spojité řadě posunou ceny z počátku roku 2011).

## Zařazení dnů

- Obchodní dny 2010-12-31 až 2026-09-25, 4 060 dnů. Před tím vynecháno 18 dnů (2010-12-06 až 2010-12-30: záznamy bez klasifikace bid/ask nebo minutové bary; NQZ10 je prázdný, tyto dny jsou z NQH11).
- Vyřazeno 68 dnů:
  - 59 víkendových obchodních dnů s artefakty. Největší: sobota 2014-08-30 19:22–20:43 CT, 18 573 záznamů, 28 363 kontraktů, ceny 4042,5–4094,25, přitom pátek skončil a neděle začala na 4078,75 (zřejmě testovací seance CME). Ostatní mají 1–5 minut.
  - 7 dnů roku 2011 s bid/ask pod 99,9 %: 01-04, 02-01, 04-22, 06-29, 08-05, 08-10, 08-11.
  - 2 svátky s méně než 100 záznamy: 2011-12-26, 2012-01-02.
- Pracovní dny bez dat (46): 37 svátků CME (Vánoce, Nový rok, Velký pátek a jejich náhradní dny) a 9 vyřazených dnů 2011–2012 výše. Na Velký pátek 2012, 2015, 2021, 2023 a 2026 se obchodovalo do 08:15 CT.

## Díry a události

Úseky bez obchodů podle `verify`, čas CT (Praha = CT + 7 h, v týdnech s rozdílným letním časem + 6 h); konec = první bar po mezeře.

Díry bez známé příčiny (obchody nejsou v žádném kontraktu):

| Obchodní den | Bez obchodů (CT) | Minut |
|---|---|---|
| 2011-04-21 | 00:10–08:33 | 503 |
| 2012-02-20 | 02-19 17:05–23:02 (neděle večer) | 357 |
| 2012-06-07 | 10:11–10:19 | 8 |
| 2012-09-11 | 07:18–08:59 a 09:02–11:25 | 101 + 143 |
| 2019-02-27 | 02-26 18:41–21:45 | 184 |

Události trhu (nejde o chybu dat):

- 2025-11-28: výpadek CME (chlazení datacentra), 11-27 20:45 – 11-28 07:30 CT (645 min); pak zkrácená seance do 12:15 CT.
- Přerušení obchodování 2020: 03-09 08:36–08:49, 03-12 08:37–08:50, 03-16 08:31–08:45 a v noci 04:12–05:57 (limit down), 03-18 11:58–12:11 CT.
- Dny bez hlavní seance (`no main session`, 9): Velký pátek 2012-04-06, 2015-04-03, 2021-04-02, 2023-04-07, 2026-04-03 (obchod do 08:15 CT); hurikán Sandy 2012-10-29 a 2012-10-30 (do 08:15 CT); dny státního smutku 2018-12-05 a 2025-01-09 (do 08:30 CT).
- Zkrácené seance svátků USA (131 dnů, viz Trh a čas).
- Osamocené obchody po konci seance: 2012-04-06 15:40 a 15:45, 2012-07-03 15:29, 2012-07-04 16:59, 2012-10-29 16:59 CT; v pátek 2011-03-25, 04-01 a 04-29 po 15:15 CT (16:19–16:39). Datová vrstva je vynechá spolu s ostatními bary mimo obchodní hodiny.
- Mimo hlavní seanci s malou likviditou: 2012-12-30 23:25 – 12-31 00:30 CT (Silvestr), 2013-02-18 09:21–09:26 CT (Presidents Day).

## Záznamy mimo pořadí

Soubory 2011–2012 mají záznamy s časem o víc než sekundu starším než předchozí záznam: NQM11 99, NQU11 297, NQZ11 552, NQH12 595, NQM12 216; v ostatních souborech nejvýš 3. Export je zařadí do sekundy jejich času.

## Ověření

`verify` 1.3 (2026-09-28): `passed`. Agregace 1s po minutách = 1min soubor ve všech 5 357 648 minutách; časy, OHLC, mřížka a ceny v pořádku; `Contract` se mění jen v 63 dnech rollu. `BidVolume + AskVolume ≠ Volume` u 10 742 1s barů a 9 008 1min barů, všechny v letech 2010–2012 (bez klasifikace 0,0009 % objemu).

## Překryv s kalendářem zpráv

Kalendář Forex Factory (Hugging Face, 2007-01-01 až 2025-04-07) pokrývá NQ od 2010-12-31 do 2025-04-07. Pro 2025-04-08 až 2026-09-25 zprávy chybí.
