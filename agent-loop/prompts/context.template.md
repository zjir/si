# Kontext úkolu

- Úkol: {{ID}} — {{TITLE}}
- Režim: {{MODE}}
- Kolo: {{ROUND}} (strop tohoto běhu: kolo {{LAST_ROUND}})
- Datum: {{DATE}}
- Pracovní složka: kořen repozitáře; všechny cesty jsou relativní k ní.

## Cíl

{{GOAL}}

## Hotovo, když

{{DONE_WHEN}}

## Vstupy (čti podle potřeby, cíleně)

{{INPUTS}}

## Rozsah

Smíš měnit:

{{SCOPE_ALLOW}}

Nesmíš měnit (má přednost):

{{SCOPE_DENY}}

Vždy smíš zapisovat do `{{TASK_DIR}}/` (stav úkolu a soubory tohoto kola).

## Stav a minulé kolo

- Stav úkolu: `{{TASK_DIR}}/state.md` {{STATE_NOTE}}
- Výsledek minulého kola: {{PREV_RESULT}}
- Diff minulého kola: {{PREV_DIFF}}

## Poznámky zadavatele

{{NOTES}}

## Výstupy tohoto kola

- `{{TASK_DIR}}/state.md` — přepiš aktuálním stavem.
- `{{ROUND_DIR}}/result.json` — povinné; `"task": "{{ID}}"`, `"round": {{ROUND}}`.
- `{{ROUND_DIR}}/notes.md` — volitelné.
