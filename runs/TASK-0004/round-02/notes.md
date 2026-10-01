# TASK-0004 kolo 2 — poznámky

## Nálezy kola (před zapracováním)

Blokující (1):
- 13.14.1 SR1: s odrazem 4A (`w_bounce` 0,67) a dotyky v nesousedních dnech mohlo být skóre při potvrzení 2. dotyku < 1 (např. 0,67 × 0,5 + 0,5 = 0,83) → test nesplnitelný. Opraveno: odraz 6A, po sobě jdoucí dny, bar z referenčního výpočtu.

Střední (17): 3.1 krok (3) vs. 3.10.4 (které bary dostává engine a modul SR); 3.4 `Bar1s` a výběr sekund baru t, chování při nesouladu agregace; 5.3 pravidlo „close sekundy ≥ ext_high“ v režimu `body` (hladina `open_t`) a nedefinované `intrabar_used`; 3.5 `n_levels_active` bez definice; 3.10.2 podmínka vydání PD* (poslední bar `pd_scope` znám až zpětně); `level_id` PD* u dnů bez barů v `pd_scope`; 3.10.3 kandidát v toleranci publikované úrovně (dvě úrovně v jednom baru); `LEVEL_UPDATED` nestačilo k rekonstrukci `strength` v čase testu; remíza nejslabšího publikovaného; `theta_sr = null (= θ)` nerozhodnutelné bez `TrendParams`; zigzag modulu SR a 1s data; `on_invalid_bar` modulu; 8.1 `levels_crossed` nad úrovněmi minulých barů (mechanismus); 8.2 chop bar nad úrovněmi minulých barů; 12.2 bez anotace a 10 × 5 ≠ 40; 13.14.2 HOLD bez pole baru; `t_known` událostí modulu vs. `bar_index`.

Drobné (14 + 1 z druhého průchodu): hlavička verze; odkazy v sekci 2 (3×); `ROLL_GAP` ve warmupu; signatura `bars_1s`; 3.5 popis `level_id` a zastaralá věta o „samostatné úloze“; 3.9 měny v oknech; 3.10.3 „vždy dva swingy od sebe“, význam `n_touches`, přepočet po sloučení; 3.10.4 krok 2 a `atr_n` vs. `atr_n_sr`; 9 R1 a `tick_size` delty; 10.1 `scope_from/to`; 10.4 `INTRABAR_MISMATCH`; 12.4 hash bez `sr_break_atr`; 13.2.1 trhy, 13.5 drift, 13.11 perturbace 12.4; 1.3 `levels=None`; 13.14.1 bod 4 inkluzivní vs. exkluzivní `valid_to` fixture.

## Zvážené a ponechané (bez změny)

- `sr_min_score = 1,0`: dva odrazy přesně θ (w_bounce 0,5) kvalifikují jen v týž den; záměr „jen nejsilnější“, kalibrační rozsah 0,5–2 pokrývá alternativu.
- 13.4 u FDAX obě varianty horizontu (`rth_close` 17:30 a `scope_close` 22:00) — report, ne brána.
- `bounce_atr` přes mezeru dne: konečná hodnota může být velká, `w_bounce` je omezeno na 1.

## Pro příští kolo

- Čistý průchod celým dokumentem (tento průchod našel 18 B+S, takže DONE ještě nelze). Zaměřit se na nový text D-62–D-66 (viz state.md).
- R5 a R6 zůstávají otevřené mimo rozsah.
