# TASK-0005 — stav po kole 1 (2026-10-01)

## Hotovo v kole 1 (dokumentové kolo 4)

- **Dodatek zadavatele** (byl inline v 3.9 jako řádek „ZMENA: data\NEWS\ obsahuje všechny zprávy…“) zapracován a řádek odstraněn: 3.9 přepsána podle skutečného formátu `data/NEWS/forex-factory-1.csv` (2007-01-01 až 2024-12-27) a `forex-factory-2.csv` (2024-12-30 až 2026-09-30): UTC ověřeno z dat, dva dialekty (impact, jednotky, `previous_revised`), spojení podle `split_ts`, duplicitní `id` → pozdější `datetime`, půlnoční řádky se nepoužívají, díra `actual` 2024-08-22 až 2024-12-27 → `surprise_missing`, `news_end` 2026-09-30, kontrola pásma jako brána 13.2.10 (konkrétní hodnoty kolem NFP 2025-01-10 a 2024-10-04), remízy událostí se stejným `DateTime` (vyšší `Impact`, pak menší `id`), rozhraní `ScheduledEvent`/`Release` s poli. Sekce 0 odstavec o kalendáři, 3.8 R6 splněn + R7 (obnovit `data/NEWS/info.md`), 13.6 kategorie „bez actual“, D-57 → Zrušeno (kolo 4), D-67, D-45 stav upraven, hlavička verze, historie řádek 4.
- **Průchod dokumentem** (nálezy před zapracováním 1 B / 16 S / 19 D, vše zapsáno do textu):
  - B: 15.5 kvintil `atr1` „v rámci roku“ jako rys D = pohled do budoucnosti → hranice z předchozího roku (D-72).
  - S: 3.2 bar `outside_session` vs rozsah; 6.3 kandidát aktuální TL musí mít `a2 > a1`; 6.2/6.5/7.1/7.5/10.4 nekladný sklon hlavní TL = `TL_BREAK(MAIN, NONPOSITIVE_SLOPE)`, `broken = true`, `reason ∈ {CLOSE, NONPOSITIVE_SLOPE}` (D-69); 9 reset zigzagu a struktur delty v prvním baru session, `delta_divergence` null přes session (D-68); 10.1 `run(df, levels_df, levels_provider_hash)` s předností `levels_df`, `detectors=None`; 13.5 postup simulace bootstrapem, cesta v `close` (D-71); 13.6 bootstrap 1 000 × `default_rng(20260925)`; 13.11 perturbace celočíselných/výčtových parametrů; 15.5 isotonic kalibrace na vyňatém roce, finální model do 2020 + kalibrace 2021; 6.1.1 `prev_major_low` znovu podle definice po pozdním potvrzení low (D-73); 13.9 tabulka pokračování pro každou variantu zvlášť.
  - D (D-70): 3.1 validace času proti poslednímu přijatému baru; 5.2 zprávy baru `t0`; 6.1 `swing_id > L₀.swing_id`; 6.1.1 bod 1 poznámka; 8.3 ořez `s_dev`; 10.5 obsah snapshotu (efektivní params, verze, kontrola při obnově); 12.2 výběr dnů bez semínka; 12.3 odkaz na bar vstupu 13.13; S8 testovací `LevelProvider`; 15.2 `reg_slope_t` null při `se = 0`; 3.10.3 krok 3 pořadí kandidátů se nepřeřazuje; 7.5 řádek `TL_BREAK` s důvody.
- Druhý průchod nad novým textem (6.2, 6.5, 9, 10.1, 13.5, 15.5) našel jen 2 drobnosti (snapshot, cesta simulace v `close`), zapracovány.

## Zbývá (kolo 2)

1. Čistý průchod celým dokumentem; zvlášť nový text kola 4: 3.9 kroky 1–10 + remízy + 13.2.10, 6.2 pseudokód (pořadí `TL_UPDATE` → `TL_BREAK`/`TL_REVALIDATED`), 6.5 nekladný sklon, 9 reset delty, 10.1 `run`, 10.5 snapshot, 13.5 simulace, 15.5 kalibrace.
2. Položky z `runs/TASK-0005/round-01/notes.md` (13.4 horizont při `WINDOW`, 13.14.2 zrcadlo, 15.4 hash) — při druhém pohledu bez nálezu, jen potvrdit.
3. Nenajde-li průchod nic blokujícího ani středního → `DONE`.

## Otevřené požadavky (mimo dokument, nebrání DONE)

- R5: smazat `zadani/komponenta-sr.md`, opravit odkazy v `zadani/testy.md` a `data/README.md` 10.
- R7: obnovit `data/NEWS/info.md` z `runs/TASK-0004/round-02/discarded/data/NEWS/info.md`.

## Rozhodnutí přijatá v kole 1

- Kalendář: půlnoční řádky (čas neznámý) se nepoužívají vůbec; `Low` a `Non-Economic` mimo; hodnoty zůstávají v jednotce sloupce; překvapení jen při shodné jednotce; synonyma názvů zpráv se nevedou; remíza stejného `DateTime` → vyšší `Impact`, pak menší `id`.
- Delta: reset zigzagu a struktur po session (hladiny delty mezi session nejsou srovnatelné), `atr_delta` bez resetu.
- Aktuální TL jen s kladným sklonem; nekladný sklon hlavní TL je prolomení s vlastním `reason`.

## Co bylo zkoušeno a nefungovalo

- Grep s cestou na adresář `data/NEWS` nic nenajde (CSV jsou v `.gitignore`) — hledat s cestou na soubor. `$` v Grepu nematchuje kvůli CRLF (`\r?$`). Lookahead `(?!…)` ripgrep nepodporuje.
- `data/NEWS/info.md` není v pracovním stromu (přesunut runnerem); jeho obsah: data přímo z Forex Factory, vyčištěna (odstraněny neplatné datum/hodnoty), `datetime` UTC, „All Day/Tentative/Day n“ = 00:00, hodnoty `<0.25` = 0.25.
