# Zadání: Komponenta SR (supporty a rezistence)

Verze 0.1 · výchozí zadání před recenzí · dokument je psaný pro AI implementátora, ne pro čtení člověkem

## 1. Dodatky k zapracování

> **Úkol pro recenzenta:** body níže jsou dodatky zadavatele. Zapracuj každý do příslušných sekcí dokumentu jako konkrétní řešení. Po zapracování tuto sekci odstraň; zapracování zaznamenej v rozhodovacím logu.

1. Výstup komponenty slouží jako vstup do trend komponenty (`zadani/komponenta-trend.md`).
2. Slouží pro účely P.A.T.
3. Umí vrátit SR úrovně na základě vstupních dat.
4. Vrací úrovně podle P.A.T., ale premarket nepoužívá vždy, protože to záleží na trhu. Je to parametr runtime.
5. Cílem není vracet co nejvíce úrovní, ale ty nejspolehlivější.
6. Metoda zjišťování a délka okna nejsou dány; k jejich stanovení lze využít jakýchkoliv prostředků a technických metod.
7. Každá SR ve výstupu ponese svůj typ, aby šlo později vyhodnocovat, které SR byly úspěšné.
