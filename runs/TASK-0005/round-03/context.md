# Kontext úkolu

- Úkol: TASK-0005 — review 3
- Režim: spec
- Kolo: 3 (strop tohoto běhu: kolo 4)
- Datum: 2026-10-02T11:52:06+02:00
- Pracovní složka: kořen repozitáře; všechny cesty jsou relativní k ní.

## Cíl

Zreviduj zadani/komponenta-trend.md v roli recenzenta (agent-loop/review-loop/review.md): zapracuj sekci Dodatky k zapracování, vyplň všechna prázdná místa, vše v kontextu systému P.A.T. Dodatek zadavatele (kolo 3): navrhni do sekce 13 nezávislý test detekce trendu: test zná polohu trendů ze zpětného pohledu (pravda určená nad celými daty s look-ahead, nezávisle na definicích a kódu komponenty, tj. ne přes zigzag a strukturu z 5–6) a vyhodnotí, zda komponenta trend odhadla správně: shoda po barech i po úsecích trendu (zachycení úseku, zpoždění začátku a konce, falešné trendy), s referencí náhody a kritériem pass / fail nebo reportu.

## Hotovo, když

Dodatky jsou zapracované a sekce odstraněná; průchod celým dokumentem nenajde žádný blokující ani střední nález. Sekce 13 obsahuje nezávislý zpětný test polohy trendů (definice pravdy bez použití výstupů komponenty, metriky, kritérium) se záznamem v rozhodovacím logu.

## Vstupy (čti podle potřeby, cíleně)

- `PAT/Popis OS P.A.T.pdf`
- `PAT/Obchodní deník.xls`
- `PAT/PAT_obchody_z_obrazku.csv`
- `PAT/PAT_obchody_z_obrazku_POPIS.md`
- `/data slozka pro data`

## Rozsah

Smíš měnit:

- `zadani/komponenta-trend.md`

Nesmíš měnit (má přednost):

- (nic)

Vždy smíš zapisovat do `runs/TASK-0005/` (stav úkolu a soubory tohoto kola).

## Stav a minulé kolo

- Stav úkolu: `runs/TASK-0005/state.md` 
- Výsledek minulého kola: `runs/TASK-0005/round-02/result.json`
- Diff minulého kola: `runs/TASK-0005/round-02/diff.patch`

## Poznámky zadavatele

Prochazej dal zadani... Kolo 3+: nejdřív dokončit zapracování nálezů kola 2 (runs/TASK-0005/state.md), potom dodatek testů. Pravda zpětného testu nesmí být odvozena z výstupů komponenty ani z jejích definic swingů a struktury.

## Výstupy tohoto kola

- `runs/TASK-0005/state.md` — přepiš aktuálním stavem.
- `runs/TASK-0005/round-03/result.json` — povinné; `"task": "TASK-0005"`, `"round": 3`.
- `runs/TASK-0005/round-03/notes.md` — volitelné.
