Kolo 1 je uzavřené, `result.json` zapsán se stavem `CONTINUE`.

**Co se stalo**
- `zadani/komponenta-trend.md`: zapracovány dodatky 15–17 (data Sierra Chart, `bar_timestamp = open`, pásmo Praha, spojitá řada aditivním posunem, skutečný rozsah dat) a zadání SR sloučeno jako modul SR 3.10 s parametry 12.4 a branami 13.14. Sekce dodatků je odstraněna, log má D-47 až D-61, D-28/D-32/D-43 jsou zrušené s náhradou.
- Poznámky zadavatele jsou uzavřeny rozhodnutími: `MarketSpec` místo konstant ET, FDAX okno 09:00–22:00 a tick 0,5, NQ primární / FDAX druhý / ES a YM až závěrečná brána, dělicí den 2021-12-31, 1s data zůstávají omezená (přidáno `intrabar_order`), katalog metod doplněn o M18–M32.
- Nálezy před zapracováním: 2 blokující, 18 středních, 8 drobných; vše zapracováno do textu.

**Otevřené požadavky (mimo můj rozsah)**
- R5: smazat `zadani/komponenta-sr.md` a opravit odkazy v `zadani/testy.md` a `data/README.md`.
- R6: zdroj zpráv pro 2025-04-08 až 2026-09-25. WebSearch i WebFetch mi byly zamítnuty, takže zdroje jsou v 3.9 označeny jako neověřené s náhradním oficiálním zdrojem a kontrolou na překryvu.

**Další kolo**: úplný kontrolní průchod celým dokumentem po změnách; seznam míst k prověření je v `runs/TASK-0004/state.md`. Bez nových nálezů bude stav `DONE`.