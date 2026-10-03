# TASK-0006 — stav v kole 1 (2026-10-03), rozpracováno (kolo převzato po přerušení chatu)

## Zjištění (kolo 1)

- `zadani/testy.md` (v0.2) má jen sekce 0–5 a dodatky; sekce 6–21 (brány G1–G11, report, audit, stabilita, log) nikdy nevznikly. Obsah je zastaralý proti kolům 2–6 komponenty (názvy událostí, parametry `theta`/`eps`/`curr_ratio_*`, čas ET, kalendář CME napevno, NinjaTrader parquet, období 2007/2018, generátor v jednotkách R). Tabulka výkladů P-01–P-42 je v komponenta-trend.md už rozhodnuta → orákulum se nepřenáší; referenční výpočet = nezávislá implementace 5–8, 3.10, 9 (D-40).
- Z testy.md se přenáší a rozvádí: vrstvy testů a mapování Ø1, struktura balíku a nezávislost modulů, běh harnessu a stavy, porovnání záznamů, co komponenta nesmí, serializace a hash, reálná data (zdroje přes datovou vrstvu, validace, `data_report.json`, `sample_20d`, zmrazení parametrů), syntetika (formát scénáře, návrhová pravda s okny, podmínky odstupu, škály), fixture `MechanicalLevels` (odkazují 3.10.2 bod 8–9 a 13.14.1 bod 4), report a baseline, provedení 13.15 (R8), provedení testů SR, zlatý vzorek auditu.

## Plán zápisu (pořadí)

1. Nové podsekce 13.16 harness, 13.17 referenční výpočet a brány shody/invariantů, 13.18 testovací data, 13.19 report a baseline, 13.20 provedení 13.15; 13.14.4 provedení SR; odstavec zlatý vzorek v 13.8.
2. Opravy odkazů: hlavička (řádek 3), 1.2, 1.4, 3.8 R5/R8, 3.10.2 bod 8–9, 10.1 (jméno balíku), 13 úvod, 13.10, 13.14.1 bod 4, 13.15.1, 14, 15.4, D-3; log D-81+; historie kolo 7; `data/README.md` 10.
3. Smazat `zadani/komponenta-sr.md` a `zadani/testy.md`; grep na zbytkové odkazy.
4. Recenzní průchod nového textu (implementátor / tester), nálezy zapracovat, result.json DONE/CONTINUE.

## Hotovo

- Přečteno (v tomto chatu cíleně): testy.md 1–4, 5.1 (jen předměty řádků), 5.9–6; komponenta-trend.md 1–3.5, 3.8, 3.10, 7.1–7.4, 10, 12.1/12.4 (jména), 13 celá, 14, 15.4, 16 (D-3, D-66–D-80), 17; data/README.md 10.
- Zapsáno: zatím nic (další krok = 1).
