# FDAX – futures na index DAX (Eurex)

Obecná pravidla, formát a postup exportu: [`data/README.md`](../README.md). Tady jsou jen fakta o FDAX. Stav k 2026-09-28.

## Soubory

| Soubor | Obsah |
|---|---|
| `FDAX-1-sec.csv` | 60 600 779 řádků, 3,70 GB |
| `FDAX-1-min.csv` | 3 403 495 řádků, 218 MB |
| `FDAX-rolls.csv` | 55 rollů |
| `FDAX-export-report.json` | report exportu, `verification`, `gaps`, `missing_weekdays` |

- Zdroj: `E:\SierraChart\Data\FDAX<H|M|U|Z><RR>-EUREX.scid`; 69 souborů s daty, 13 prázdných.
- Export 2026-09-28 nástrojem verze 1.2. Plán verze 1.3 dává stejné dny, rolly i spready, nový export by byl shodný. `verify` 1.3 prošel.
- Příkaz: `python tools\scid_export.py all --data E:\SierraChart\Data --symbol FDAX --exchange EUREX --out data\FDAX`

## Trh a čas

- Kontrakty březen, červen, září, prosinec; expirace 3. pátek v měsíci.
- Tick 0,5 bodu do 2020-12-18, 1,0 bodu od 2020-12-21 (v datech od 2020-12-21 žádná cena s .5). Export používá mřížku 0,5 v celé historii. Prahy v ticích mají po 2020-12-21 jiný význam.
- Obchodní den = kalendářní den v Praze (Eurex).
- Obchodní hodiny v datech (Praha): 2013–2018 08:00–22:00; od 2019 01:15 v zimě a 02:15 v létě až 22:00. Poslední řádný bar 21:59.
- Hlavní seance (Xetra) 09:00–17:30; podle ní se hlásí díry. Objem skáče v 09:00 (maximum průměrného objemu v okně 08:55–09:05 je v baru 09:00, tedy bar = začátek intervalu), v 15:30 (otevření USA) a 17:30–17:35 (uzavírací aukce Xetra).

## Záznamy mimo obchodní hodiny

Datová vrstva je vynechá: bar FDAX s časem ≥ 22:00 nebo před začátkem obchodování (08:00 do roku 2018, od 2019 01:15 v zimě a 02:15 v létě).

- Po 22:00 je skoro každý den jeden až dva osamocené obchody, typicky v 22:03: 3 924 barů za 2013–2026, 0,03 % objemu, cena až 84 bodů od posledního obchodu před 22:00 (medián 3,5).
- 2023-11-21 až 2024-02-29 navíc záznamy mezi 22:04 a 23:56 a v některých dnech mezi 00:00 a 01:15 (v `gaps` jako mezery mimo hlavní seanci).

## Rollover

- 55 rollů od 2013-03-15 (FDAXH13 → FDAXM13) do 2026-09-17 (FDAXU26 → FDAXZ26), všechny podle objemu (`volume`).
- Do roku 2021 roll v den expirace (pátek), od roku 2024 den před expirací (čtvrtek), v letech 2022–2023 obojí.
- Spready −27,5 až +291 bodů, součet +2 781 bodů (o tolik se ve spojité řadě posunou ceny z počátku roku 2013).

## Zařazení dnů

- Obchodní dny 2013-01-07 až 2026-09-25, 3 483 dnů. Před 2013-01-07 vynecháno 855 dnů (obchody bez klasifikace bid/ask nebo minutové bary; 2013-01-04 měl bid/ask 99,6 %).
- Vyřazeno 15 dnů: 2023-11-29 (jen minutové bary, bid/ask pod 99,9 %), 12 nedělí 2023-11-26 až 2024-02-25 (jediný artefaktní záznam), 2023-12-26 a 2024-01-01 (svátky, jediný záznam).
- Pracovní dny bez dat (97) jsou svátky Eurex: Velký pátek (14), Velikonoční pondělí (14), 1. 5. (11), 24. 12. (9), 25. 12. (10), 26. 12. (10), 31. 12. (9), 1. 1. (10), 3. 10. (2014, 2016–2018), Svatodušní pondělí (2015–2018), 31. 10. 2017; k tomu vyřazený 2023-11-29.

## Díry

Úseky bez obchodů podle `verify` (čas Praha; konec = první bar po mezeře). Příčina (výpadek burzy, nebo díra v datech Sierra) není ověřená. Datová vrstva je předá komponentě jako mezery, nedoplňují se.

| Den | Bez obchodů | Minut | Poznámka |
|---|---|---|---|
| 2013-04-22 | 09:00–13:46 | 286 | den začal až ve 13:46 |
| 2013-05-03 | 16:15–17:48 | 93 | |
| 2013-06-20 | 11:40–11:45 | 5 | |
| 2013-08-26 | 08:15–09:39 | 84 | |
| 2014-06-11 | 10:20–10:25 | 5 | |
| 2015-02-17 | 09:00–09:20 | 20 | den začal v 09:20 |
| 2015-07-20 | 09:00–10:30 | 90 | den začal v 10:30 |
| 2015-11-30 | 14:37–15:00 | 23 | |
| 2016-02-22 | 11:04–12:50 | 106 | |
| 2018-03-16 | 09:00–09:20 | 20 | den začal v 09:20 |
| 2020-04-14 | 09:26–14:06 | 280 | |
| 2020-07-01 | 08:48–11:30 | 162 | |
| 2026-03-23 | 12:06–12:11 | 5 | |
| 2026-04-27 | 02:15–10:32 | 497 | den začal až v 10:32 (v hlavní seanci 92 min); nové stažení FDAXM26 to může opravit |

Mimo hlavní seanci ≥ 60 min (kromě záznamů po 22:00): 2025-08-18 03:48–05:02, 2025-12-23 04:20–05:31, 2026-08-04 05:55–07:02, 2026-08-07 04:30–06:02, 2026-09-03 05:11–06:11 (asijské hodiny s malou likviditou, nebo díra).

## Záznamy mimo pořadí a ceny

- FDAXM16: 17 141 záznamů střídá uvnitř sekundy časy .000 a .001 ms; export drží pořadí ze souboru.
- Soubory 2013–2017: 1 114 záznamů má čas o 1–5 s starší než předchozí záznam; patří do sekundy svého času.
- Část cen 2017–2020 je ve float32 mimo mřížku o ~0,001 (např. 13422.499); export je zaokrouhluje na 0,5.

## Ověření

`verify` 1.3 (2026-09-28): `passed`. Agregace 1s po minutách = 1min soubor ve všech 3 403 495 minutách; časy, OHLC, mřížka a ceny v pořádku; `Contract` se mění jen v 55 dnech rollu; `BidVolume + AskVolume ≠ Volume` u 25 1s barů a 9 1min barů.

Srovnání se starším CSV exportem z grafu Sierra (UTC, ceny zaokrouhlené na celé body), mimo okna rollů: objem shodný v 99,999 % minut, ceny v rámci zaokrouhlení kromě 9 minut, kde obchod s opožděným časem padl do jiné minuty.

## Překryv s kalendářem zpráv

Kalendář Forex Factory (Hugging Face, 2007-01-01 až 2025-04-07) pokrývá FDAX od 2013-01-07 do 2025-04-07. Pro 2025-04-08 až 2026-09-25 zprávy chybí.
