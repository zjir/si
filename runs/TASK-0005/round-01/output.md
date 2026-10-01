Kolo 1 úkolu TASK-0005 je uzavřeno, všechny výstupy jsou v souborech.

**Co kolo udělalo**

- Dodatek zadavatele (vložená věta „ZMENA“ v 3.9 o složce `data/NEWS/`) je zapracován a odstraněn. Sekce 3.9 je přepsaná podle skutečného obsahu obou souborů kalendáře: čas v UTC (ověřeno na NFP a FOMC), dva dialekty impactu a jednotek, pravidlo spojení souborů, půlnoční řádky s neznámým časem, díra v hodnotách `actual` od 2024-08-22 do 2024-12-27, konec kalendáře 2026-09-30. Vrstvené náhradní zdroje z kola 2 jsou zrušeny, požadavek R6 je splněn a přibyla brána 13.2.10 s konkrétními referenčními hodnotami.
- Průchod dokumentem našel 1 blokující nález (kvintil `atr1` v rámci roku jako rys detektoru D byl pohled do budoucnosti), 16 středních a 19 drobných. Vše je zapsáno do textu a do logu jako D-67 až D-73. Hlavní změny: rozsah barů mimo session, kandidát aktuální TL jen s kladným sklonem, nekladný sklon hlavní TL jako prolomení s vlastním důvodem, reset modulu delta po session, přednost `levels_df` v dávkovém běhu, konkrétní postup simulace reference, kalibrace detektoru D bez přeučení.

**Stav a další kolo**

- `result.json` má stav CONTINUE, protože kolo s nálezy nemůže končit jako DONE. Příští kolo má udělat čistý průchod se zaměřením na nový text a při nulovém nálezu nastavit DONE.
- Otevřené požadavky mimo rozsah recenzenta: obnovit `data/NEWS/info.md`, který runner v minulém úkolu přesunul do složky discarded (R7), a dál trvá R5 (smazání zrušeného zadání SR a oprava odkazů).