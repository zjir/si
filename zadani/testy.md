# Zadání: Testy komponent

Verze 0.1 · výchozí zadání před recenzí · dokument je psaný pro AI implementátora, ne pro čtení člověkem

## 0. Kontext: obchodní systém P.A.T.

Vše v tomto zadání se dělá v kontextu obchodního systému P.A.T. a pro něj. Výsledek (testy komponent) bude použit výhradně v systému P.A.T., který se ve finále implementuje; jiné použití není a nenavrhuje se pro něj. Každé rozhodnutí se posuzuje podle toho, co potřebuje P.A.T.; rozpor se systémem P.A.T. je chyba zadání.

Podklady systému ve složce `PAT/` (závazné):

- `PAT/Popis OS P.A.T.pdf` — popis obchodního systému P.A.T.,
- `PAT/Obchodní deník.xls` — reálný obchodní deník s reálnými obchody,
- `PAT/obrazky-obchodu/` — obrázky jednotlivých obchodů.

## 1. Dodatky k zapracování

> **Úkol pro recenzenta:** body níže jsou dodatky zadavatele. Zapracuj každý do příslušných sekcí dokumentu jako konkrétní řešení. Po zapracování tuto sekci odstraň; zapracování zaznamenej v rozhodovacím logu.

1. Udělat zadání, jak testovat trend a SR komponentu. Ve skutečnosti je scope testu pouze trend komponenta (`zadani/komponenta-trend.md`).
2. Test by měl proběhnout na syntetických datech, aby bylo zaručeno, že jsou data skutečně pod kontrolou.
3. Měl by proběhnout také na skutečných tržních datech, ale tam nejsou označené správné referenční situace.
