# TASK-0006 — stav po kole 1 (2026-10-03)

## Hotovo (kolo 1)

- Smazány `zadani/komponenta-sr.md` a `zadani/testy.md`; odkaz v `data/README.md` 10 nahrazen; v komponenta-trend.md na ně nevede žádný živý odkaz (zbývají jen zmínky „zrušen / smazán“ v 1.4, 3.8, 13 úvod, 13.14.4, 13.16, logu a historii).
- Nové podsekce: 13.14.4 provedení testů SR; 13.16 balík a harness (vrstvy, mapování Ø1, struktura `tests/`, nezávislost importů, sady quick/full, pořadí, stavy PASS/FAIL/WARN/SKIP/ERROR/DATA_ERROR, přijetí verze, `records_equal`, kontrakt pro testy, schémata a hash); 13.17 referenční výpočet (bez výkladů; tabulka P-01–P-42 z testy.md se nepřenáší, D-82), brána shody na reálných datech 13.17.3, brána invariantů I-1–I-16 (13.17.4); 13.18 data (CSV přes datovou vrstvu, validace 9 bodů, `data_report.json`, období D-53, `params_frozen.json`, `sample_20d`, formát scénáře, návrhová pravda s okny, podmínky odstupu, škály A ∈ {2, 10}, fixture `MechanicalLevels`, statický `LevelProvider`); 13.19 report, metriky, baseline a regrese; 13.20 provedení 13.15 (R8).
- 13.8 zlatý vzorek (měkká brána od 150 označení); 10.1 jméno balíku `pat_trend`; 12.1 a 12.4 povolený rozsah parametrů (D-91, nález kola); 13.9, 13.10 doplněny; 3.8 R5 a R8 splněny; 3.10.2 body 8–9 a 13.14.1 bod 4 odkazují na 13.18.4; 13.15.1, 14, 15.4 opraveny; D-3 Zrušeno (kolo 7); D-81–D-91; historie kolo 7 (0 / 11 / 11); hlavička.
- Formát: escapovány `|` v kódových úsecích tabulek (7 míst), tabulky v celém dokumentu mají konzistentní počet sloupců.

## Rozhodnutí kola (viz log)

- D-81 sloučení; D-82 orákulum se nepřenáší; D-83 bitově vs. tolerance 1e-9; D-84 data; D-85 syntetika a škály; D-86 harness; D-87 nové brány; D-88 provedení 13.15; D-89 provedení SR a zlatý vzorek; D-90 fixture; D-91 povolený rozsah.

## Co zbývá (kolo 2 = poslední kolo tohoto běhu)

1. **Úplný recenzní průchod celým dokumentem** (dodatek 3): v kole 1 byly čteny 1–3.5, 3.8, 3.10, 7, 8, 10, 12 (jména), 13 celá, 14, 15.4, 16 (D-3, D-66–D-91), 17; **nečteny** 4–6, 9, 11, 12.2–12.3, 15.1–15.3, 15.5–15.6 a log D-4–D-65. Projít je v roli implementátora a testera a zejména ověřit, že nové sekce 13.16–13.20 s nimi souhlasí: invarianty I-9, I-10, I-13, I-14 proti 5.4–5.6, 6.1.1, 6.7 (pořadí v baru, remízy, `t_ext` vs. `t_conf`, `TL_BREAK` + `TL_REVALIDATED` v jednom baru); kontrakt 13.16.5 proti 11; `records_equal` proti 11.1; okna návrhové pravdy 13.18.3 proti 5.4 (definice potvrzení swingu) a 6.5.
2. Zkontrolovat, že 13.2.5 tabulka scénářů a 13.18.3 formát scénáře si odpovídají (segmenty S5 `SINE`, S6 „cesta“, S7, S11 `TRI`), a doplnit do 13.18.3 chybějící druh segmentu, bude-li potřeba.
3. Zvážit, zda 13.3 „Log odhadů“ má odkázat na schémata 13.16.6 (drobné).
4. Po průchodu: historie kolo 8, `result.json` DONE, pokud průchod nenajde nic nového.

## Co nedělat

- Neotvírat znovu rozhodnutí D-81–D-91 bez nového argumentu; nepřidávat zpět orákulum ani číslování G1–G11 / S01–S21.
- Nečíst PAT/ podklady (nejsou k dispozici; poznámka zadavatele).
