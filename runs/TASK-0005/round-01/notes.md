# TASK-0005 kolo 1 — poznámky pro příští kolo

## Fakta o `data/NEWS/` (ověřeno Grepem, bez Bash)

| | forex-factory-1.csv | forex-factory-2.csv |
|---|---|---|
| řádků (`^\d+,`) | 81 769 | 8 899 |
| první / poslední `datetime` | 2007-01-01 00:00 / 2024-12-27 15:30 | 2024-12-30 00:30 / 2026-09-30 23:50 |
| impact | `High Impact Expected` (17 563), Medium…, Low…, `Non-Economic` | `High` (1 397), `Medium`, `Low`, `Non-Economic` |
| USD/EUR High+Medium s časem | 18 951 | 1 344 |
| jednotky | `unit_none|unit_percentage|unit_thousand|unit_million|unit_billion` (64 293 řádků s jednotkou) | `%|K|M|B|` |
| `previous_revised` | True/False | číslo nebo prázdné |
| ověření UTC | NFP 2007-01-05 13:30, 2007-04-06 12:30; FOMC 2013-03-20 18:00, 2013-12-18 19:00; Unemployment Claims 2010–2024: 514/515 řádků v 12:30/13:30 | NFP 2025-01-10 13:30, 2025-04-04 12:30; FOMC 2025-01-29 19:00, 2025-03-19 18:00 |
| USD High/Medium s časem 00:00:00 | 40 | 13 |
| díra `actual` | od 2024-08-22 (Unemployment Claims 2024-08-22 bez actual; 2024-08-29 dál i bez forecast) | — |
| `id` v obou souborech | 135050 (KOF): 2024-12-27 v s1, 2024-12-30 v s2 | |

Prázdné řádky v souboru 1 (např. řádky 682, 1383, 2091, …). CRLF konce řádků (`$` v Grepu nefunguje bez `\r?`). Adresářové hledání v `data/NEWS` nic nevrací (gitignore) — hledat po souborech.

Testovací hodnoty 13.2.10: 2025-01-10 13:30 UTC = 14:30 CET: USD NFP (id 142565, 256 vs 164 K), Unemployment Rate (142577), AHE (142589); další USD událost 15:00 UTC (UoM, Medium). 2024-10-04 12:30 UTC = 14:30 CEST: AHE (135999), Unemployment Rate (136000), NFP (136001), vše bez hodnot.

## Co jsem v tomto kole nestihl prověřit do hloubky (kandidáti pro kolo 2)

- 3.10.3 publikace krok 3 při více kandidátech v témže baru po sloučení (skóre přepočteno „ihned“ — pořadí kandidátů se po sloučení nepřeřazuje; je to záměr? rozhodnout a zapsat).
- 13.4 horizont „5 session“ u pullbacku při `WINDOW` (session = obchodní den v rozsahu) — asi OK, jen ověřit formulaci.
- 13.14.2 test úrovně: první bar po publikaci, když je cena už v toleranci (čeká se na vzdálení) — formulace OK, ověřit zrcadlo.
- 12.3 `min_slope`: `atr_ref` v baru vstupu z 1min dat — bar vstupu definován v 13.13 (stejné pravidlo) — doplnit odkaz.
- 15.4 JSON: chybí `levels_provider_hash` explicitně? (je uvnitř `params_hash`) — OK.
- Nový text: 3.9 kroky 1–10, 6.2 pseudokód (pořadí TL_UPDATE vs TL_BREAK/REVALIDATED v témže přepočtu — 6.5 říká priorita TREND_END; pořadí událostí v baru = pořadí vzniku), 9 reset, 13.5 simulace, 15.5 kalibrace.
