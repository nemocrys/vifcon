# VIFCON
**Vi**sual **F**urnace **Con**trol

As part of Vincent Funke's (HTW) master's thesis "Automation of a model system for crystal growth with induction heating based on Python and Raspberry Pi", the VIFCON controller was designed at the Leibniz Institute for Crystal Growth (IKZ) for the [model experiments group](https://www.ikz-berlin.de/en/research/materials-science/section-fundamental-description#c486).

The controller can be used to control various systems and devices, for example to carry out simple heating tests or crystal growth.

## Supported devices

The following devices are currently supported:

- Eurotherm controller (RS232)
- PI axis (RS232)
    - Mercury-DC-controller C-862
    - Mercury-DC-controller C-863
- TruHeat generator (RS232)

In particular, VIFCON can access the PLC of the Nemo-1 and Nemo-2 system of the model experiments group via Modbus. This addresses:

- drives for rotation,
- drives for stroke and,
- measuring devices for pressure and flow.

A gamepad/controller can also be used to control the drives. The gamepad used is an old one from Nintendo or now from GeekPi. The gamepad is shown in the picture [Gamepad.jpg](Bilder/Gamepad.jpg).

A connection to the Multilog logging software can also be established. This was also designed by the model experiments group at the IKZ. See: https://github.com/nemocrys/multilog

## Usage
### Starting VIFCON

To start VIFCON, you can do the following:

1. Interface available and Init set to False in Config (devices do not have to be connected)
2. Device present, correctly configured and Init set to True in Config
3. Test mode (argparser)

Start options using argparser:
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

VIFCON is started by calling [vifcon_main.py](vifcon_main.py).
```
python .\vifcon_main.py
```

To view VIFCON without devices or to get a first impression of the control system, the template can be used. Vi#IFCON is started as follows:
```
python .\vifcon_main.py -t -c ./Template/config_temp.yml
```

### Configuration

The configuration of VIFCON is achieved through the config.yml file. VIFCON is created using this file. The template [config_temp.yml](Template/config_temp.yml) shows this config file. In order to use VIFCON, it must be copied and modified for the respective experiment.

In addition to this file, you will also find a template for the execution file and the log file.

### Recipes

To use the swapping of recipes, a folder **rezepte** must exist in the folder **vifcon**.

### Files

When VIFCON is started, a measurement data folder with the name "measdata_date_#XX" is created. Depending on the configuration, the measurement data (csv), the log file (log), a process file (txt), the config file (yml), the plots (png) and the legends (png) are saved in this folder. The latter is only saved if it is outside the plot. In test mode, this folder is not created.

### GUI

If everything has been configured correctly, VIFCON starts and the GUI is displayed. The GUI is based on programming with PyQt5.

<img src="Bilder/GUI_S_En.png" alt="GUI" title='Graphical interface - Tab Control' width=700/>
<img src="Bilder/GUI_M_En.png" alt="GUI" title='Graphical interface - Tab Monitoring' width=700/>

Status of the GUI: 12.8.24

## Dependencies

VIFCON works with Python >= 3.8 on Windows, Linux and Raspberry Pi (RPi OS 64-bit Version 12 (bookworm)). The following libraries are needed by Python:

1. GUI:
    - PyQt5
    - pyqtgraph
    - sys

2.  Files:
    - logging
    - PyYaml
    - os
    - shutil

3. Interfaces/communication protocols:
    - pyserial (RS232)
    - pyModbusTCP (Modbus)
    - json (Multilog-Link)
    - socket (Multilog-Link)
    - pygame (Gamepad)

4. More:
    - random
    - time
    - datetime
    - argparse

### Screen size:
The GUI requires a minimum screen resolution of 1240x900 pixels.

## Documents

## Information

The **[Information](Information)** folder contains further documents that describe VIFCON in more detail. The following topics can be found there in German and English:

1. The Readme file in German. [Show](Information/Readme_DE.md)
2. Python and Raspberry Pi - Installation and libraries 
    - [Show En](Information/Python_RPI_En.md)
    - [Show De](Information/Python_RPI_DE.md)
3. Recipes 
    - [Show En](Information/Rezepte_En.md) 
    - [Show De](Information/Rezepte_DE.md)
4. Config
    - [Show En](Information/Config_En.md) 
    - [Show De](Information/Config_DE.md)
5. Function descriptions
    - [Show En](Information/Funktionen_En.md) 
    - [Show De](Information/Funktionen_DE.md) 

## Last change

The last change of this description was: June 25, 2024