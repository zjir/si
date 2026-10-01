# TASK-0004 — stav po kole 1 (2026-10-01)

## Hotovo v kole 1

- Sekce 18 (dodatky 15–17) zapracována a odstraněna; zadání SR (`zadani/komponenta-sr.md`, dodatky SR-1…SR-8) sloučeno jako modul SR 3.10 + parametry 12.4 + brány a vyhodnocení 13.14.
- Poznámky zadavatele uzavřeny rozhodnutími D-47…D-61 (log 16), historie 17 má řádek kola 2 (dokumentové číslování: kolo 2 = TASK-0004 kolo 1).
- Hlavní rozhodnutí: data Sierra (`bar_timestamp = open`, pásmo Praha, D-47, D-52); spojitá řada posunem, `roll_day`, `adj(d)` (D-48); `MarketSpec` 3.2 a `params_hash` bez trhu, s `levels_provider_hash` (D-49, D-60); FDAX tick 0,5 (D-50); FDAX `WINDOW` 09:00–22:00, NQ `ETH` (D-51); dělicí den 2021-12-31, NQ primární, FDAX druhý, ES/YM až závěrečná brána (D-53); 1s data omezené použití + `intrabar_order` (D-54); modul SR: odrazy = swingy vlastního zigzagu, shluky 0,5 atr, okno 5 dnů, poločas 2 dny, min 2 dotyky, skóre ≥ 1, top 6 s hysterezí, cena zmrazená (D-55); CSV třetí použití = report 13.14.3 (D-56, ruší D-32); zprávy po 2025-04-07 vrstvené zdroje + oficiální náhrada bez Forecast (D-57); katalog M18–M32, Wilsonův interval C (D-58); `on_level` u kandidáta, `pb_retrace` null (D-59).
- Požadavky 3.8: R1, R3, R4 splněny; R2 trvá; R5 (smazat komponenta-sr.md, opravit odkazy v testy.md a data/README.md 10) a R6 (zdroj zpráv 2025-04-08+; WebSearch/WebFetch recenzentovi nepovoleny) otevřeny.

## Co bylo zkoušeno a nefungovalo

- WebSearch i WebFetch zamítnuty (bez oprávnění) → zdroje zpráv po 2025-04-07 jsou „neověřeno“ s kontrolou při implementaci.
- Smazání `zadani/komponenta-sr.md` je mimo rozsah (runner by kolo zahodil) → jen požadavek R5.

## Druhý průchod novým obsahem (opraveno v kole 1)

- Pořadí `sr.update` → `engine.update` je závazné (mechanické úrovně mají `valid_from ≤ ts_open` baru vydání); PD* se vydávají hned po konci `pd_scope`; medián shluku při sudém počtu = průměr; `sr_params_hash` vstupuje do `params_hash`.

## Na co se zaměřit v kole 2 (úplný průchod celým dokumentem)

1. Konzistence nového 3.10/12.4/13.14 se sekcemi 5–8 a 10 (např. `n_levels_active`, `levels_crossed` s `level_id` mechanických úrovní po dnech, `LEVEL_UPDATED` vs. `levels_df`).
2. Zbylé zmínky ET/RTH v 13.5, 13.12, 12.2 (vzorek dnů jen NQ?) a v 2 (řádek „Obecně“), zda vše odkazuje na `MarketSpec`.
3. Grilování 3.10.3: `bounce_atr` konečná hodnota při mezeře přes den, chování shluků při rollu (ceny posunuté — OK), `sr_min_score = 1` vs. dva odrazy přesně θ v různých dnech (nekvalifikují; záměr? zvážit 0,75), `LEVEL_UPDATED` při změně skóre po dni.
4. 3.9: `news_currencies` EUR — kontrola pásma jen přes USD události; `in_news_window` pro FDAX zahrnuje EUR i USD události (dořešit, zda `in_high_impact_window` má filtr měny).
5. 13.4 horizont „konec téže session“ u FDAX (`rth_close` 17:30 vs. `scope_close` 22:00) — ověřit, že report obě varianty opravdu potřebuje.
6. Ověřit, že `zadani/testy.md` po úpravě (mimo rozsah) nebude v rozporu: fixture `SESSION_OPEN` o bar dřív (3.10.2 bod 9), kalendář ET.
7. Pokud průchod nic nového nenajde → `DONE` (R5, R6 nejsou blokující pro dokument).
