# TASK-0004 kolo 1 — poznámky recenzenta

## Nálezy před zapracováním (2 B / 18 S / 8 D)

Blokující:
1. Rozpor zdroje dat: dokument popisoval NinjaTrader, konvenci `close` a pásmo ET; skutečná data jsou Sierra Chart, bar = začátek, Praha (dodatek 15) → posun všech stavů o minutu a chybné kalendáře.
2. Chyběla definice referenčního poskytovatele úrovní (zadání SR bylo jen seznam dodatků bez algoritmu) → detektory s úrovněmi nešlo implementovat ani testovat.

Střední (výběr): `anchors_on_level`/`L0_on_level` bez určení, z kterého baru se úrovně berou (jedno volání `levels_at` za bar); vývojové období odkazovalo na rok 2007 mimo data; `params_hash` s `tick_size` odmítal tabulku na jiném trhu; mezera kalendáře zpráv 2025-04-08+; tick FDAX; rozsah barů FDAX; ET napevno na více místech; `pb_retrace` dělení nulou; 13.13 převod pásma a obchody před začátkem dat; vstup delty nedefinovaný z dat; „konec téže session“ u FDAX; `news_currencies` pro FDAX; úplnost katalogu metod; (druhý průchod) pořadí volání SR/engine, okamžik vydání PD*, medián shluku, SR parametry mimo `params_hash`.

Drobné: zastaralé požadavky 3.8, odkazy na komponenta-sr.md, 11.5 rozsah historie, rys „hodina session“, D-28/D-32/D-43 zastaralé, chybějící varovné události a výjimky v seznamech, FDAX okrajové případy v 13.2.6, řádky tabulky 2.

## Odpovědi na poznámky zadavatele (kde jsou v dokumentu)

- Data ze Sierra, `/data` README → 0, 3.1–3.4, 3.8, D-47, D-48.
- 1s data k potvrzování svíček → 3.4 (ponecháno omezené, `intrabar_order`), D-54; rozšíření až podle 13.2.7.
- Trhy: NQ teď, FDAX zkusit, ES/YM později → 0, 11.3, 13.3, 13.11, D-53.
- Pásmo Praha → 3.1, 3.2 `MarketSpec.tz`, 13.13, D-52.
- FDAX trendy od 9:00 → 3.2 `WINDOW` 09:00–22:00 s kontrolou proti `ETH`, D-51.
- SR do tohoto zadání, měřit odrazy, nejsilnější, pár dnů zpět → 3.10, 12.4, 13.14, D-55; smazání souboru = R5.
- Zprávy pro celé období dat → 3.9 vrstvené zdroje, R6, D-57 (web nebyl povolen; zdroje označeny neověřeno s kontrolou na překryvu).
- Jsou uvedena všechna řešení? → 15.1 M18–M32, D-58 (přijat jen Wilsonův interval pro C; M18 objemový profil kandidát pro SR po 13.14).

## Mimo rozsah (požadavky v result.json)

- Smazat `zadani/komponenta-sr.md`; opravit odkazy v `zadani/testy.md` (ř. 24, 3.5 fixture; `SESSION_OPEN` o bar dřív než 3.10.2) a `data/README.md` 10; testy.md převést na `MarketSpec`/Praha.
