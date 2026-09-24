# Lokální smyčka review: zadání komponenty trend-pullback

Každé kolo je nový proces `claude -p`, tedy nezávislý recenzent bez historie. Recenzent přečte `spec.md` a systém P.A.T., najde prázdná místa, uzavře je zápisem do `spec.md`, zapíše `verdict.json`. Skript commitne změny a podle verdiktu pokračuje dalším kolem, nebo skončí.

## Instalace

1. Nainstalujte Claude Code a přihlaste se předplatným (bez API klíče).
2. Vložte PDF systému P.A.T. jako `input/Popis_OS_P_A_T.pdf` (zůstává jen lokálně, git ho ignoruje).
3. `./setup.sh` — převede PDF na text, založí git repozitář.
4. `./run_review_loop.sh` — spustí smyčku.

## Konec smyčky

| Situace | Návratový kód |
|---|---|
| Verdikt APPROVED (0 blokujících, 0 středních) | 0 |
| Opakované selhání běhu (například vyčerpaný týdenní limit) | rc claude |
| Agent nezapsal verdict.json | 2 |
| Dvě kola bez jediné změny | 3 |
| Vyčerpán strop kol | 4 |

## Nastavení

Proměnné prostředí: `MAX_ROUNDS` (8), `MODELS` ("opus sonnet opus sonnet"), `RETRIES` (3), `RETRY_SLEEP` (3600 s), `TOOLS` ("Read,Edit,Write,Glob,Grep").

```bash
MAX_ROUNDS=5 MODELS="opus sonnet" ./run_review_loop.sh
```

Střídání modelů je záměr: stejný model má stejná slepá místa. Názvy modelů musí odpovídat tomu, co přijímá `--model` ve vaší verzi CLI.

## Běh bez dohledu

cron, jedno kolo denně ve 3:00:

```
0 3 * * * cd /cesta/review-loop && MAX_ROUNDS=1 ./run_review_loop.sh >> logs/cron.log 2>&1
```

Celá smyčka najednou: spusťte `./run_review_loop.sh` v `tmux` nebo `screen` a odpojte se.

## Kontrola po běhu

```bash
git log --oneline            # kola a počty nálezů
git diff HEAD~1 -- spec.md   # co poslední kolo změnilo
cat verdict.json             # poslední verdikt
less logs/round_03_opus.log  # průběh kola
```

## Omezení

- `--bare` vypíná načítání CLAUDE.md, skillů, MCP a pamětí, aby byla kola srovnatelná.
- Agent má povolené jen čtení a zápis souborů, žádný Bash ani síť. Git obsluhuje skript.
- Běh čerpá týdenní limit předplatného. Při vyčerpání skript čeká a zkouší znovu.
- Z PDF se extrahuje pouze text; pravidla, která stojí jen na obrázku, recenzent označí jako předpoklad.
