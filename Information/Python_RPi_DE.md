# Python Bibliotheken und Raspberry Pi

In der Information werden Punkte zu Python und Raspberry Pi erläutert.

## Python Bibliotheken

Abfrage in CMD mit: `python --version`    
**Version:** Python 3.8.5

Versions Nummer nach `pip list` im Visual Studio Code -Terminal! In dem Dokument [requirements.txt](../requirements.txt) befindet sich eine kurz Fassung der folgenden Aufzählung.

1. **argparse**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/argparse.html
2. **PyQt5**
    - *install:* pip install PyQt5
    - *Version:* 5.15.11   
    (PyQt5-Qt5 5.15.2, PyQt5_sip 12.15.0)
    - *Doku:* https://doc.qt.io/qtforpython-6/
3. **pyqtgraph**
    - *install:* pip install pyqtgraph
    - *Version:* 0.13.3
    - *Doku:* https://pyqtgraph.readthedocs.io/en/latest/
4. **logging**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/logging.html
5. **yaml**
    - *install:* pip install PyYAML
    - *Version:* 6.0.2
    - *Doku:* https://pyyaml.org/wiki/PyYAMLDocumentation
6. **sys**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/sys.html
7. **os**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/os.html
8. **datetime**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/datetime.html
9. **time**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/time.html
10. **serial**
    - *install:* pip install pyserial
    - *Version:* 3.5
    - *Doku:* https://pyserial.readthedocs.io/en/latest/pyserial.html
11. **shutil**
    - *install:* Kommt mit Python, kein install 
    - *Version:* Python standard library (nicht in Liste gefunden) 
    - *Doku:* https://docs.python.org/3/library/shutil.html
12. **random**
    - *install:* Kommt mit Python, kein install 
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/random.html
13. **json**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/random.html
14. **socket**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/socket.html
15. **pygame**
    - *install:* pip install pygame
    - *Version:* 2.6.1
    - *Doku:* 
        - https://www.pygame.org/docs/
        - https://www.pygame.org/news
        - https://pypi.org/project/pygame/  
16. **pyModbusTCP**    
    - *install:* pip install pyModbusTCP
    - *Version (siehe [Besonderheiten](#Besonderheiten)):*    
            - 0.3.0 (Debug im Template auskommentieren!)  
            - 0.2.1 (Template)
    - *Doku:* 
        - https://pymodbustcp.readthedocs.io/en/latest/
        - https://pypi.org/project/pyModbusTCP/      
17. **randomcolor**
    - *install:* pip install randomcolor
    - *Version:* 0.4.4.6
    - *Doku:* https://pypi.org/project/randomcolor/ 
18. **matplotlib**
    - *install:* pip install matplotlib
    - *Version:* 3.7.5
    - *Doku:* https://matplotlib.org/
19. **math**
    - *install:* Kommt mit Python, kein install
    - *Version:* Python standard library (nicht in Liste gefunden)
    - *Doku:* https://docs.python.org/3/library/math.html

### Python Standard Bibliotheken
Link: https://docs.python.org/3/library/index.html

### Besonderheiten

Bei den Seriellen-Bibliotheken **serial** und **pyModbusTCP** muss auf die genutzte Python-Version geachtet werden. Bei *serial* ist es die *encoding* (python >= 3.9) und bei *pyModbusTCP* die *debug* Variable. Sollte die Python-Version nicht mit den beiden Variablen Arbeiten, müssen sie einfach in der Config-Datei auskommentiert werden. Bei pyModbusTCP wird die Debug-Funktion aktiviert, wenn bei Logging Debug (Level 10) gewählt wird. In dem Fall wird dies in die Log-Datei geschrieben:

```
2024-11-06 16:27:30,840 DEBUG pyModbusTCP.client - (192.168.117.199:502:1) Tx [DE 95 00 00 00 06 01] 04 00 02 00 12
2024-11-06 16:27:30,858 DEBUG pyModbusTCP.client - (192.168.117.199:502:1) Rx [DE 95 00 00 00 27 01] 04 24 00 00 00 00 48 EF 5C 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Eigentlich sollte durch die Debug-Variable ein Boolcherwert gesetzt werden, der diese Werte in die Konsole ausgibt und nicht Logged. Die Nutzung von Debug kann z.B. an Beispielen in der Masterarbeit von Vincent Funke im Anhang I (Seite 235 bis 238) gezeigt.

In der Version 0.3.0 von pyModbusTCP (https://pymodbustcp.readthedocs.io/en/latest/) wird die neuste Version diser Bibliothek gezeigt. Die Debug-Funktion funktioniert nun mit Logging. In der Version 0.2.0 (https://pymodbustcp.readthedocs.io/en/v0.2.0/) exestierte die Debug-Funktion noch bzw. war sie noch vorhanden. 

In dem Template wurde `debug` nicht auskommentiert! Sollte der folgende Fehler erscheinen, so muss `debug` entfernt werden!

```
Traceback (most recent call last):
  File "C:\Users\funke-lokal\AppData\Local\Programs\Python\Python38\lib\site-packages\pyModbusTCP\client.py", line 136, in __del__
    self.close()
  File "C:\Users\funke-lokal\AppData\Local\Programs\Python\Python38\lib\site-packages\pyModbusTCP\client.py", line 324, in close
    self._sock.close()
AttributeError: 'ModbusClient' object has no attribute '_sock'
```

### Nutzung in Python Code

Import-Beispiel der Bibliotheken:
```
# Allgemein:
-------------------------------------------------------
import yaml
import logging
import time
import datetime
import sys
import os
import random
import shutil
from argparse import ArgumentParser

# Schnittstelle:
-------------------------------------------------------
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
from serial import Serial, SerialException

import socket   
import json
import pygame

# GUI:
-------------------------------------------------------
from PyQt5.QtGui import (
    QIcon, 
)
from PyQt5.QtCore import (
    QSize,
    Qt,
    QTimer,
)
import pyqtgraph as pg

# Eigene Programme und Klassen:
-------------------------------------------------------
from .base_classes import Splitter, PlotWidget, Widget_VBox
```

## Raspberry Pi

1. Betriebssystem: RPi OS 64-bit Version 12
2. Modell/Version: Raspberry Pi 400 (Model No: RPI-400)
3. Debian Version: 12 (bookworm)
4. Python Version: 3.11.2

Nach der Installation von Raspberry Pi auf der Micro-SD-Karte mithilfe des Raspberry Pi Imagers, mussten nun noch die Bibliotheken hinzugefügt werden. Auch hier waren einige Bibliotheken bereits installiert:

1. argparse
2. datetime
3. json
4. logging
5. os
6. pygame (Version 2.1.2)
7. PyQt5 (Version 5.15.9)
8. pySerial (Version 3.5)
9. random
10. shutil
11. socket
12. sys
13. time 

Nach Installiert werden mussten:

1. pyModbusTCP (Version 0.2.1)
2. pyqtgraph (Version 0.13.1) 
3. PyYaml (Version 6.0)

Seit der Version bookworm, kann nicht mehr pip install genutzt werden. Siehe dafür: https://www.raspberrypi.com/documentation/computers/os.html#python-on-raspberry-pi

Zur Installation können entweder Virtuelle Umgebungen (venv) oder apt install genutzt werden!

```
sudo apt install python3-pyqtgraph
sudo apt install python3-yaml
```

Bei pyModbusTCP musste dieses direkt von GitHub installiert werden: https://github.com/sourceperl/pyModbusTCP 

```
pi@raspberrypi:~ $ git clone https://github.com/sourceperl/pyModbusTCP
pi@raspberrypi:~ $ cd pyModbusTCP
pi@raspberrypi:~/pyModbusTCP $ sudo python3 setup.py install
```

Nach dem alle Bibliotheken installiert worden sind, funktioniert VIFCON auf dem genannten Raspberry Pi. 

## Letzte Änderung

Die Letzte Änderung dieser Beschreibung war: 19.03.2025