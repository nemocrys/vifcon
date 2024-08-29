# VIFCON
**Vi**sual **F**urnace **Con**trol

Im Rahmen der Master-Arbeit "Automatisierung einer Modellanlage für Kristallzüchtung mit Induktionsheizung basierend auf Python und Raspberry Pi" von Vincent Funke (HTW) wurde die Steuerung VIFCON am Leibniz Institut für Kristallzüchtung (IKZ) für die [Gruppe Modellexperimente](https://www.ikz-berlin.de/en/research/materials-science/section-fundamental-description#c486) entworfen. 

Mit der Steuerung können verschiedene Anlagen und Geräte gesteuert werden um z.B. einfache Heiztest oder auch Kristallzüchtungen durchzuführen.

## Unterstützte Geräte

Derzeit werden folgende Geräte unterstützt:

- Eurotherm-Regler (RS232)
- PI-Achse (RS232)
    - Mercury-DC-Controller C-862
    - Mercury-DC-Controller C-863
- TruHeat-Generator (RS232)

Speziell kann VIFCON auf die SPS der Nemo-1- und Nemo-2-Anlage der Modellexperimente-Gruppe über Modbus zugreifen. Dabei werden:

- Antriebe für die Rotation,
- Antriebe für den Hub und,
- Messgeräte für Druck und Durchfluss

angesprochen.

Für die Steuerung der Antriebe kann auch ein Gamepad/Controller genutzt werden. Das genutzte Gamepad ist ein alter von Nintendo bzw. nun von GeekPi. Das Gamepad wird im Bild [Gamepad.jpg](../Bilder/Gamepad.jpg) gezeigt. 

Weiterhin kann eine Verbindung zu der Logging-Software Multilog aufgebaut werden. Auch dieses wurde von der Modellexperimente-Gruppe am IKZ entworfen. Siehe: https://github.com/nemocrys/multilog

## Benutzung
### Start von VIFCON

Um VIFCON zu starten kann folgendes getan werden:

1. Schnittstelle vorhanden und Init auf False in Config (Geräte müssen nicht angeschlossen sein)
2. Gerät vorhanden, richtig konfiguriert und Init auf True in Config
3. Test-Modus (argparser)

Startmöglichkeiten durch argparser:
```
usage: vifcon [-h] [-c CONFIG] [-n] [-o OUT_DIR] [-t] [-v]

Use of the VIFCON control. Control and reading of various devices on one system.

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        vifcon configuration file [optional, default='./config.yml']
  -n, --neustart        vifcon restart [optional, default=False]
  -o OUT_DIR, --out_dir OUT_DIR
                        directory where to put the output [optional, default='.']
  -t, --test            test-mode [optional, default=False]
  -v, --version         show program's version number and exit
```

VIFCON wird durch den Aufruf von [vifcon_main.py](..\vifcon_main.py) gestartet.
```
python .\vifcon_main.py
```

Um sich  VIFCON ohne Geräte anzuschauen bzw. einen ersten Eindruck der Steuerung zu bekommen, kann das Template genutz werden. So wird Vi#IFCON wie folgt gestartet:
```
python .\vifcon_main.py -t -c ./Template/config_temp.yml
```

### Konfiguration

Die Konfiguration von VIFCON wird durch die Datei config.yml erreicht. Anhand der Datei wird VIFCON erstellt. Das Template [config_temp.yml](../Template/config_temp.yml) zeigt dabei diese Config-Datei. Um VIFCON nutzen zu können, muss dieses kopiert und für den jeweiligen Versuch abgeändert werden. 

Neben dieser Datei sind auch ein Template für die Ablauf-Datei und die Log-Datei zu finden.

### Rezepte

Um die Auslagerung der Rezepte zu nutzen, muss im Ordner **vifcon**, ein Ordner **rezepte** existieren. 

### Datein

Wenn VIFCON gestartet wird, wird ein Messdatenordner mit dem Namen "measdata_date_#XX" erstellt. Je nach Konfiguration werden in diesem Ordner die Messdaten (csv), die Log-Datei (log), eine Ablauf-Datei (txt), die config-Datei (yml), die Plots (png) und die Legenden (png) gespeichert. Letztere wird nur gespeichert, wenn diese außerhalb des Plots ist. Im Test-Modus wird dieser Ordner nicht erstellt.

### GUI

Wenn alles richtig konfiguriert wurde startet VIFCON und die GUI wird angezeigt. Die GUI bassiert auf der Programmierung mit PyQt5.

<img src="../Bilder/GUI_S_De.png" alt="GUI" title='Grafische Oberfläche - Tab Steuerung' width=700/>
<img src="../Bilder/GUI_M_De.png" alt="GUI" title='Grafische Oberfläche - Tab Monitoring' width=700/>

Stand der GUI: 12.8.24

## Abhängigkeiten

VIFCON arbeitet mit Python >= 3.8 auf Windows, Linux und Raspberry Pi (RPi OS 64-bit Version 12 (bookworm)). Folgende Bibliotheken werden von Python gebraucht:

1. GUI:
    - PyQt5
    - pyqtgraph
    - sys

2.  Dateien:
    - logging
    - PyYaml
    - os
    - shutil

3. Schnittstellen/Kommunikationsprotokolle: 
    - pyserial (RS232)
    - pyModbusTCP (Modbus)
    - json (Multilog-Link)
    - socket (Multilog-Link)
    - pygame (Gamepad)

4. Weitere:
    - random
    - time
    - datetime
    - argparse
    - math

### Bildschirmgröße:
Die GUI benötigt eine Mindestauflösung des Bildschirms von 1240x900 Pixel.

## Dokumente

## Informationen

Im Ordner **[Information](../Information)** befinden sich weitere Dokumente, die VIFCON näher beschreiben. Folgende Themen sind dort in Deutsch und Englisch zu finden:

1. Python und Raspberry Pi - Installation und Bibliotheken 
    - [Zeige En](Python_RPI_En.md)
    - [Zeige De](Python_RPI_DE.md)
2. Rezepte 
    - [Zeige En](Rezepte_En.md) 
    - [Zeige De](Rezepte_DE.md)
3. Konfiguration
    - [Zeige En](Config_En.md) 
    - [Zeige De](Config_DE.md)

## Letzte Änderung

Die Letzte Änderung dieser Beschreibung war: 12.8.2024
