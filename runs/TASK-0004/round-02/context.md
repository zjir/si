# Kontext úkolu

- Úkol: TASK-0004 — review 2 trend komponenta
- Režim: spec
- Kolo: 2 (strop tohoto běhu: kolo 2)
- Datum: 2026-10-01T08:59:53+02:00
- Pracovní složka: kořen repozitáře; všechny cesty jsou relativní k ní.

## Cíl

Zreviduj zadani/komponenta-trend.md v roli recenzenta (agent-loop/review-loop/review.md): zapracuj sekci Dodatky k zapracování, vyplň všechna prázdná místa, vše v kontextu systému P.A.T.

## Hotovo, když

Dodatky jsou zapracované a sekce odstraněná; průchod celým dokumentem nenajde žádný blokující ani střední nález.

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

Vždy smíš zapisovat do `runs/TASK-0004/` (stav úkolu a soubory tohoto kola).

## Stav a minulé kolo

- Stav úkolu: `runs/TASK-0004/state.md` 
- Výsledek minulého kola: `runs/TASK-0004/round-01/result.json`
- Diff minulého kola: `runs/TASK-0004/round-01/diff.patch`

## Poznámky zadavatele

odpovedi:

nove - vsechna data nejsou z ninjatraderu, ale ze sierra chart, jsou ve slozce /data a tam si precti .md soubor, ktery popisuje, co tam je. 

  domnivam se, ze 1 sec data se mohou hodit k potvrzovani intra svicek, napr. k lepsimu zjisteni pullbacku a tak.. ale nechavam na tobe... 
 
 - momentalne jsou data za FDAX a NQ a budou i data za ES a YM, ale ale ty az pro finalni test robustnosti... momentalne res jen NQ a muzes zkusit i na tom DAXu
 
 - timezone je praha 
 

  - na FDAX je treba trendy hledat hlavne takve v hlavni seanci, takze od 9:00 ? 

 ve slozce zadadni je zadarni pro SR komponentu, nedelejme ji jako oddelene zadani, ale zadani vprav do zadani teto komponenty, hledani trendu bude probiha jiz s aktualizovanymi SR jako pomocnym zdrojem. Prijde mi, ze nejjednodusi metoda je merit odrazy a podle toho stanovovat SR? nejde o to, abych jich bylo za den 15, ale abychom mely ty nejsilnejsi... par dnu zpet? zadani na sr komponentu smaz.  

 pokud zjistis, ze data maji sirsi rozsah nez dataset ze zpravami, vyhledej dalsi zdroj zprav at pokrejes cele obdobi pro ktere mame data. Jsou v zadani zminena vsechna mozna reseni, jak uspet? 

## Výstupy tohoto kola

- `runs/TASK-0004/state.md` — přepiš aktuálním stavem.
- `runs/TASK-0004/round-02/result.json` — povinné; `"task": "TASK-0004"`, `"round": 2`.
- `runs/TASK-0004/round-02/notes.md` — volitelné.
