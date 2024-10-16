# Anzeige der VIFCON Messdaten

Das Programm gibt die Messdaten (CSV) von VIFCON wieder aus! Dabei werden bestimmte Teile des VIFCON-Codes wieder verwendet. 

## Requirements/Bibliotheken

- os
- sys
- argparse
- math
- pyqtgraph
- matplotlib
- randomcolor 
- PyQt5

## GUI

<img src="../Bilder/GUI_Extra_1_De.png" alt="Programm zum Anzeigen der Messdaten 1" title='Einzel-Modus' width=700/>

<img src="../Bilder/GUI_Extra_2_De.png" alt="Programm zum Anzeigen der Messdaten 2" title='Vergleich-Modus' width=700/>

## Nutzung

Die GUI besitzt zwei Modis. Einen Darstellungsmodus von einer Messdatein und einen Darstellungsmodus von mehrern Messdatein. 

Um den Vergleichsmodus zu starten muss die Checkbox betätigt werden. Geschieht dies, wird der Plot geleert. Um den Vergleichsmodus neuzustarten oder zu beenden muss die Checkbox neugesetzt werden. Alle genutzten Datein werden gelb angezeigt.

Im Einzelmodus, wird immer nur eine Datei angezeigt. Beim Wechsel zu einer anderen, wird der Plot und die Legende geleert und das neue eingesetzt!

Ein kleines Video zeigt die Nutzung - [Nutzung.mp4](./Video/Nutzung.mp4)

### Knöpfe und Bereiche

**Bereich 1 - Skallierung:**   
Mit dem Knopf `Skalierung anpassen` werden die y-Achsen angepasst von allen Größen. Dabei werden die Inhalte der freigegebenen Eingabefelder ausgelesen und die Kurven werden angepasst. 

**Bereich 2 - Save und Auto Scale:**
Mit `Save Plot` wird der aktuelle Plot gespeichert. Dabei wird ein Ordner mit dem Namen `Bilder` erstellt. Sobald der Vergleichsmodus aktiv ist, werden alle Bilder in einem Ordner `Vergleichsmodus` gespeichert, sonst in einem zur Datei passenden Ordner z.B. `PI-Achse_x_2024-07-01`.

Beim `Auto Scale` wird der Plot angepasst. 

**Bereich 3 - Plot Anpassen:**   
In dem Bereich kann man die drei Achsen beleibt Skalieren. Durch die Checkbox kann die Skalierung ein- und ausgeschaltet werden. Mit `Plot Anpassen` werden die Achsen angepasst. Bei Werte Fehlern, wird eine Fehlernachricht unter den Eingabefeldern ausgegeben. 

**Bereich 4 - Vergleichsmodus:**   
Hier ist die Checkbox mit einer kleinen Nachricht zu finden. 

**Bereich 5 - Messdaten:**
Die Knöpfe im oberen linken Bereich werden automatisch erstellt. Hierfür muss es einen Ordner `Messdaten` geben. Alle CSV Datein werden geprüft und als Knopf erstellt. Mit der Betätigung wird der Plot erstellt und die Datei ausgelesen.

**Bereich 6 - Plot:**   
Neben Bereich 5 ist der Plot mit Legende und Cursor zu finden.

Bei der Legende muss gewusst werden, dass die immer links ist. Über den Tooltip kann dann die dazugehörige Datei gesehen werden. 

### Argparser

Mit der Eingabe `python .\messdata_Read.py -f Messordner_1` kann der Datei-Ordner gewechselt werden!

```
Evaluation or Sorting from the Logging-VIFCON-File.
options:
  -h, --help            show this help message and exit
  -l LANGUAGE, --language LANGUAGE
                        Language DE (German) or EN (English) - Usage from upper() [optional, default='EN']
  -f FOLDER, --folder FOLDER
                        Name of the folder in which the measurement data is located [optional, default='Messordner]
```

## Fehlende Punkte

- Programm mit Englicher Sprache 
- Optimierungen:
    - Vergleichsmodus - Datei erneut drücken, entferne aus Plot
    - Änderung des Plot-Titels, wenn gewollt
    - Fehlermeldungen