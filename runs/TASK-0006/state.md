# TASK-0006 — stav v kole 1 (2026-10-03), rozpracováno

## Zjištění po přečtení (kolo 1)

- `zadani/testy.md` (v0.2, po TASK-0001) má jen sekce 0–5 (konvence, kontrakt rozhraní, fixture úrovní, syntetika, reálná data, orákulum s tabulkou výkladů P-01–P-42) a nezapracované dodatky (data v `data/<SYMBOL>/`, čas Praha, rolly, díry); sekce 6–21, na které odkazuje (brány G1–G11, report, audit, stabilita, log), nikdy nevznikly.
- Obsah testy.md je zastaralý proti kolům 2–6 komponenty: názvy událostí (`PULLBACK_END_UP` pro obě strany, `SEQUENCE_VIOLATION`), parametry (`theta`, `eps`, `curr_ratio_*`), čas ET, kalendář CME napevno, NinjaTrader parquet, období 2007/2018, generátor v jednotkách R. Všechna místa z tabulky výkladů P-01–P-42 jsou v komponenta-trend.md už rozhodnuta (4.1 warmup, 5.3 pořadí v baru, 6.1 korekce/`prev_major_low`, 6.1.1, 6.2, 6.5, 7.3, 7.4, 8.1, 8.2, 9). Pseudokód orákula se proto nepřenáší; referenční výpočet = nezávislá implementace 5–8, 3.10, 9 (D-40).
- Co z testy.md v dokumentu chybí a zapracovává se: vrstvy testů a mapování Ø1, struktura balíku a nezávislost modulů (import), běh harnessu a stavy PASS/FAIL/SKIP/ERROR/DATA_ERROR, `equal_records`, hotovo-když sady; brána shody s referenčním výpočtem na reálných datech (G8) a brána invariantů (8); validace reálných dat a `data_report.json`, rychlá sada `sample_20d`, zmrazení parametrů; formát scénáře a návrhové pravdy, podmínky odstupu, škály A; fixture `MechanicalLevels` (odkazují 3.10.2 bod 8–9 a 13.14.1 bod 4); report a baseline; provedení 13.15 (R8); provedení testů SR; zlatý vzorek auditu.

## Plán zápisu

1. Nové podsekce 13.16 harness, 13.17 referenční výpočet (+ brány 13.2.11, 13.2.12), 13.18 testovací data (reálná, období, syntetika, fixture, kalendář/rolly), 13.19 report a baseline, 13.20 provedení 13.15; 13.14.4 provedení SR; odstavec zlatý vzorek v 13.8.
2. Opravy odkazů: hlavička, 1.2, 1.4, 3.8 R5/R8, 3.10.2 bod 8–9, 13 úvod, 13.2 úvod, 13.14.1 bod 4, 13.15.1, 14, 15.4, D-3; log D-81+, historie kolo 7; `data/README.md` 10.
3. Smazat `zadani/komponenta-sr.md` a `zadani/testy.md`; grep na zbytkové odkazy.
4. Recenzní průchod nového textu.

## Hotovo

- přečteno: testy.md celý; komponenta-trend.md sekce 0–13, 14, 16–17 (15 jen cíleně), 3.10 celá; komponenta-sr.md; data/README.md 10.
