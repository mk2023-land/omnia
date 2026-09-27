# Testfoto's voor US-3

Zet hier foto's van typeplaatjes en displays (jpg/png). De foto's zelf gaan niet naar GitHub,
want er kunnen serienummers of adressen op staan.

Optioneel: `verwacht.csv` met wat er op elke foto staat, dan rekent het script de score uit:

```csv
bestand;merk;type;foutcode
remeha-1.jpg;Remeha;Calenta Ace 28C;
intergas-2.jpg;Intergas;Kombi Kompakt HRE 28/24;F4
```

Laat een veld leeg als het niet op de foto staat. Dan moet de AI het ook leeg laten.

Draaien (kost een paar cent per foto):

```powershell
.venv\Scripts\python -m scripts.test_fotos
```
