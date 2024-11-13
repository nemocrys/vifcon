# Python libraries and Raspberry Pi

The information explains points about Python and Raspberry Pi.

## Python libraries

Query in CMD with: `python --version`   
**Version:** Python 3.8.5

Version number according to `pip list` in the Visual Studio Code terminal!

1. **argparse**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/argparse.html
2. **PyQt5**
    - *install:* pip install PyQt5
    - *version:* 5.15.11   
    (PyQt5-Qt5 5.15.2, PyQt5_sip 12.15.0)
    - *Doc:* https://doc.qt.io/qtforpython-6/
3. **pyqtgraph**
    - *install:* pip install pyqtgraph
    - *version:* 0.13.3
    - *Doc:* https://pyqtgraph.readthedocs.io/en/latest/
4. **logging**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/logging.html
5. **yaml**
    - *install:* pip install PyYAML
    - *version:* 6.0.2
    - *Doc:* https://pyyaml.org/wiki/PyYAMLDocumentation
6. **sys**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/sys.html
7. **os**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/os.html
8. **datetime**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/datetime.html
9. **time**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/time.html
10. **serial**
    - *install:* pip install pyserial
    - *version:* 3.5
    - *Doc:* https://pyserial.readthedocs.io/en/latest/pyserial.html
11. **shutil**
    - *install:* Comes with Python, no install 
    - *version:* Python standard library (not found in list) 
    - *Doc:* https://docs.python.org/3/library/shutil.html
12. **random**
    - *install:* Comes with Python, no install 
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/random.html
13. **json**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/random.html
14. **socket**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/socket.html
15. **pygame**
    - *install:* pip install pygame
    - *version:* 2.6.1
    - *Doc:* 
        - https://www.pygame.org/docs/
        - https://www.pygame.org/news
        - https://pypi.org/project/pygame/  
16. **pyModbusTCP**    
    - *install:* pip install pyModbusTCP
    - *version:* 0.3.0
    - *Doc:* 
        - https://pymodbustcp.readthedocs.io/en/latest/
        - https://pypi.org/project/pyModbusTCP/ 
17. **randomcolor**
    - *install:* pip install randomcolor
    - *version:* 0.4.4.6
    - *Doc:* https://pypi.org/project/randomcolor/ 
18. **matplotlib**
    - *install:* pip install matplotlib
    - *version:* 3.7.5
    - *Doc:* https://matplotlib.org/
19. **math**
    - *install:* Comes with Python, no install
    - *version:* Python standard library (not found in list)
    - *Doc:* https://docs.python.org/3/library/math.html

### Python standard libraries
Link: https://docs.python.org/3/library/index.html

### Special features

With the serial libraries **serial** and **pyModbusTCP** you have to pay attention to the Python version used. With *serial* it is the *encoding* (python >= 3.9) and with *pyModbusTCP* it is the *debug* variable. If the Python version does not work with the two variables, they simply have to be commented out in the config file. With pyModbusTCP the debug function is activated if Debug (Level 10) is selected for Logging. In this case, this is written to the log file:

```
2024-11-06 16:27:30,840 DEBUG pyModbusTCP.client - (192.168.117.199:502:1) Tx [DE 95 00 00 00 06 01] 04 00 02 00 12
2024-11-06 16:27:30,858 DEBUG pyModbusTCP.client - (192.168.117.199:502:1) Rx [DE 95 00 00 00 27 01] 04 24 00 00 00 00 48 EF 5C 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Actually, the debug variable should set a boolean value that outputs these values ​​to the console and not Logged. The use of debug can be shown, for example, using examples in Vincent Funke's master's thesis in Appendix I (pages 235 to 238).

### Usage in Python Code

Import example of the libraries:
```
# Generally:
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

# Interface:
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

# Own programs and classes:
-------------------------------------------------------
from .base_classes import Splitter, PlotWidget, Widget_VBox
```

## Raspberry Pi

1. Operating system: RPi OS 64-bit version 12
2. Model/version: Raspberry Pi 400 (Model No: RPI-400)
3. Debian version: 12 (bookworm)
4. Python version: 3.11.2

After installing Raspberry Pi on the micro SD card using the Raspberry Pi Imager, the libraries had to be added. Here, too, some libraries were already installed:

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

After installation had to be done:

1. pyModbusTCP (Version 0.2.1)
2. pyqtgraph (Version 0.13.1) 
3. PyYaml (Version 6.0)

Since the bookworm version, pip install can no longer be used. See: https://www.raspberrypi.com/documentation/computers/os.html#python-on-raspberry-pi

Either virtual environments (venv) or apt install can be used for installation!

```
sudo apt install python3-pyqtgraph
sudo apt install python3-yaml
```

For pyModbusTCP, this had to be installed directly from GitHub: https://github.com/sourceperl/pyModbusTCP

```
pi@raspberrypi:~ $ git clone https://github.com/sourceperl/pyModbusTCP
pi@raspberrypi:~ $ cd pyModbusTCP
pi@raspberrypi:~/pyModbusTCP $ sudo python3 setup.py install
```

After all libraries have been installed, VIFCON works on the Raspberry Pi mentioned.

## Last change

The last change of this description was: October 15, 2024