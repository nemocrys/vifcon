# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Educrys-Antriebs Widget:
- Anheften von weiteren Widgets (Knöpfe, Eingabefelder, Label, etc.)
- Messwert Angabe und Eingabe
- Kurven und Legende
- Update des Plots
- Rezept-Funktionen
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QRadioButton,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,

)
from PyQt5.QtGui import (
    QIcon, 

)
from PyQt5.QtCore import (
    QSize,
    Qt,
    QTimer,
)

import pyqtgraph as pg

## Allgemein:
import logging
import datetime
import yaml

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class EducrysAntriebWidget(QWidget):
    def __init__(self, sprache, Frame_Anzeige, widget, line_color, config, config_dat, neustart, multilog_aktiv, add_Ablauf_function, eduAchse, gamepad_aktiv, typ = 'Antrieb', parent=None):
        """ GUI widget of Educrys Achse.

        Args:
            sprache (int):                  Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):           Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (obj):                   Element in das, das Widget eingefügt wird
            line_color (list):              Liste mit drei Farben
            config (dict):                  Konfigurationsdaten aus der YAML-Datei
            config_dat (string):            Datei-Name der Config-Datei
            neustart (bool):                Neustart Modus, Startkonfigurationen werden übersprungen
            multilog_aktiv (bool):          Multilog-Read/Send Aktiviert
            add_Ablauf_function (Funktion): Funktion zum updaten der Ablauf-Datei.
            eduAchse (str):                 Name des Gerätes
            gamepad_aktiv (bool):           Soll das GamePad aktiviert werden bzw. wurde dies getan
            typ (str):                      Typ des Gerätes
        """
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Funktionsübergabe einlesen:
        self.sprache                    = sprache
        self.typ_widget                 = widget
        self.color                      = line_color
        self.config                     = config
        self.config_dat                 = config_dat
        self.neustart                   = neustart
        self.multilog_OnOff             = multilog_aktiv
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = eduAchse
        self.gamepad_aktiv              = gamepad_aktiv
        self.typ                        = typ

        ## GUI:
        self.color_Aktiv     = self.typ_widget.color_On

        ## Faktoren Skalierung:
        self.skalFak = self.typ_widget.Faktor

        ## Aktuelle Messwerte:
        self.ak_value = {}

        ## Weitere:
        self.Rezept_Aktiv = False
        self.data = {}

        #---------------------------------------------------------
        # Konfigurationskontrolle und Konfigurationsvariablen:
        #---------------------------------------------------------
        ''' Die Kontrolle beinhaltet folgendes:
        1. Kontrolle des Schlüssels mit Default-Vergabe!
        2. Kontrolle der Variable wegen dem Inhalt mit Default-Vergabe!
        '''
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Einstellung für Log:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                                  'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                     'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                                                                                           'The following types are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                          'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',                                                                'Error reading config during configuration:']
        self.Log_Pfad_conf_4_1  = ['Fehler beim Auslesen der Config!',                                                                                  'Error reading config!']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                                                                              '; Set to default:']
        self.Log_Pfad_conf_5_4  = ['; Gamepad Aktivierung blockiert!',                                                                                  '; Gamepad activation blocked!']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                      'Reason for error:']
        self.Log_Pfad_conf_7    = ['Bitte vor Nutzung Korrigieren und Config Neu Einlesen!',                                                            'Please correct and re-read config before use!']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                              'Incorrect input:']
        self.Log_Pfad_conf_8_1  = ['Fehlerhafte Typ:',                                                                                                  'Incorrect type:']
        self.Log_Pfad_conf_9    = ['Die Obergrenze ist kleiner als die Untergrenze! Setze die Limits auf Default:',                                     'The upper limit is smaller than the lower limit! Set the limits to default:']
        self.Log_Pfad_conf_10   = ['zu',                                                                                                                'to']
        self.Log_Pfad_conf_11   = ['Geschwindhigkeit',                                                                                                  'Velocity']
        self.Log_Pfad_conf_12   = ['PID-Eingang Istwert',                                                                                               'PID input actual value']
        self.Log_Pfad_conf_13   = ['Position',                                                                                                          'Position']
        self.Log_Pfad_conf_14   = ['Konfiguration mit VM, MV oder MM ist so nicht möglich, da der Multilog-Link abgeschaltet ist! Setze Default VV!',   'Configuration with VM, MV or MM is not possible because the Multilog-Link is disabled! Set default VV!']
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Übergeordnet:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Antriebs_wahl = self.config['Antriebs_Art']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} Antriebs_Art {self.Log_Pfad_conf_5[self.sprache]} F')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Antriebs_wahl = 'F'
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Zum Start:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.init = self.config['start']['init']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.init = False
        #//////////////////////////////////////////////////////////////////////
        try: self.startSpeed = float(str(self.config["defaults"]['startSpeed']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} defaults|startSpeed {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startSpeed = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.startPos = float(str(self.config["defaults"]['startPos']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} defaults|startPos {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startPos = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Limits:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.oGs  = self.config["limits"]['maxPos']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxPos {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGs = 1
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.uGs  = self.config["limits"]['minPos']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minPos {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGs = 0
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.oGv    = self.config["limits"]['maxSpeed']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxSpeed {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGv = 1
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.uGv    = self.config["limits"]['minSpeed']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minSpeed {self.Log_Pfad_conf_5[self.sprache]} -1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGv = -1
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.oGx    = self.config['PID']['Input_Limit_max']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_max {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGx = 1
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.uGx    = self.config['PID']['Input_Limit_min']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_min {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGx = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### GUI:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            self.legenden_inhalt = self.config['GUI']['legend'].split(';')
            self.legenden_inhalt = [a.strip() for a in self.legenden_inhalt]    # sollten Unnötige Leerzeichen vorhanden sein, so werden diese entfernt!
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} GUI|legend {self.Log_Pfad_conf_5[self.sprache]} [IWv, IWs]')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.legenden_inhalt = ['IWv']
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.BTN_BW_grün     = self.config['GUI']['knopf_anzeige']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} GUI|knopf_anzeige {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.BTN_BW_grün = False
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Rezepte:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.rezept_config = self.config["rezepte"]
        except Exception as e: 
            self.rezept_config = {'rezept_Default':  {'n1': '10 ; 0 ; s'}}
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} rezepte {self.Log_Pfad_conf_5[self.sprache]} {self.rezept_config}')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.rezept_Loop = self.config['rezept_Loop']
        except Exception as e:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} rezept_Loop {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.rezept_Loop = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Gamepad:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Button_Link = self.config['gamepad_Button']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} gamepad_Button {self.Log_Pfad_conf_5_4[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Button_Link   = 'PIz'
            self.gamepad_aktiv = False
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID-Modus:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.unit_PIDIn = self.config['PID']['Input_Size_unit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Size_unit {self.Log_Pfad_conf_5[self.sprache]} mm')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.unit_PIDIn = 'mm'
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.PID_Aktiv = self.config['PID']['PID_Aktiv']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|PID_Aktiv {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Aktiv = 0 
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: self.origin    = self.config['PID']['Value_Origin'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Value_Origin {self.Log_Pfad_conf_5[self.sprache]} VV')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.origin = 'VV'  
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Mode_Switch_Value = float(str(self.config['PID']['umstell_wert']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|umstell_wert {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Mode_Switch_Value = 0  
        #//////////////////////////////////////////////////////////////////////
        try: kp_conf                 = float(str(self.config['PID']['kp']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|kp {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            kp_conf = 0
        #//////////////////////////////////////////////////////////////////////
        try: ki_conf                 = float(str(self.config['PID']['ki']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|ki {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            ki_conf = 0
        #//////////////////////////////////////////////////////////////////////
        try: kd_conf                 = float(str(self.config['PID']['kd']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|kd {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            kd_conf = 0

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Config-Fehler und Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID-Aktiv:
        if not type(self.PID_Aktiv) == bool and not self.PID_Aktiv in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Aktiv - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Aktiv}')
            self.PID_Aktiv = 0
        ### Knopf-Anzeige:
        if not type(self.BTN_BW_grün) == bool and not self.BTN_BW_grün in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} knopf_anzeige - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.BTN_BW_grün}')
            self.BTN_BW_grün = 0
        ### Gamepad-Button:
        if not self.Button_Link in ['/']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} gamepad_Button - {self.Log_Pfad_conf_2[self.sprache]} [PIz, PIy, PIx, PIh] - {self.Log_Pfad_conf_5_4[self.sprache].replace("; ","")} - {self.Log_Pfad_conf_8[self.sprache]} {self.Button_Link}')
            self.Button_Link = '/'
            self.gamepad_aktiv = False
         ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0
        ### PID-Limit:
        if not type(self.oGx) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_max - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGx)}')
            self.oGx = 1
        if not type(self.uGx) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_min - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGx)}')
            self.uGx = 0
        if self.oGx <= self.uGx:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_12[self.sprache]})')
            self.uGx = 0
            self.oGx = 1
        ### Geschwindigkeits-Limit:
        if not type(self.oGv) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGv)}')
            self.oGv = 1
        if not type(self.uGv) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} -1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGv)}')
            self.uGv = -1
        if self.oGv <= self.uGv:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} -1 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_11[self.sprache]})')
            self.uGv = -1
            self.oGv = 1
        ### Positions-Limit:
        if not type(self.oGs) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGs)}')
            self.oGs = 1
        if not type(self.uGs) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGs)}')
            self.uGs = 0
        if self.oGs <= self.uGs:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
            self.uGs = 0
            self.oGs = 1
        ### Start-Geschwindigkeit:
        if not type(self.startSpeed) in [float, int] or not self.startSpeed >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.startSpeed}')
            self.startSpeed = 0
        ### Start-Postion:
        if not type(self.startPos) in [float, int] or not self.startPos >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.startPos}')
            self.startPos = 0
         ### PID-Herkunft:
        if not type(self.origin) == str or not self.origin in ['MM', 'MV', 'VV', 'VM']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Value_Origin - {self.Log_Pfad_conf_2[self.sprache]} [VV, MM, VM, MV] - {self.Log_Pfad_conf_3[self.sprache]} VV - {self.Log_Pfad_conf_8[self.sprache]} {self.origin}')
            self.origin = 'VV'
        if not self.multilog_OnOff and self.origin in ['MM', 'MV', 'VM']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_14[self.sprache]}')
            self.origin = 'VV'
        ### PID-Umschaltwert:
        if not type(self.PID_Mode_Switch_Value) in [float, int] or not self.PID_Mode_Switch_Value >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} umstell_wert - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.PID_Mode_Switch_Value)}')
            self.PID_Mode_Switch_Value = 0
        ### Wahl der Antriebsart:
        if not self.Antriebs_wahl in ['L', 'R', 'F']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Antriebs_Art - {self.Log_Pfad_conf_2[self.sprache]} [L, R, F] - {self.Log_Pfad_conf_3[self.sprache]} F')
            self.Antriebs_wahl = 'F'
        ### Rezept Loop Anzahl:
        if not type(self.rezept_Loop) in [int] or not self.rezept_Loop >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} rezept_Loop - {self.Log_Pfad_conf_2_1[self.sprache]} [int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.rezept_Loop)}')
            self.rezept_Loop = 0
        
        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Werte: ##################################################################################################################################################################################################################################################################################
        istwert_str             = ['Ist',                                                                                                                   'Is']
        sollwert_str            = ['Soll',                                                                                                                  'Set']
        ## Label: ##################################################################################################################################################################################################################################################################################                                                   
        self.Position           = ['Sollposition',                                                                                                          'Target position']
        ## Knöpfe: #################################################################################################################################################################################################################################################################################                                              
        rez_start_str           = ['Rezept Start',                                                                                                          'Start recipe']
        rez_ende_str            = ['Rezept Beenden',                                                                                                        'Finish recipe']
        DH_str                  = ['Setze Positon',                                                                                                         'Define Postion']
        ## Zusatz: ################################################################################################################################################################################################################################################################################## 
        self.str_Size_1         = ['Geschwindigkeit',                                                                                                       'Speed']
        self.str_Size_2         = ['Position/Weg/Strecke',                                                                                                  'Position/path/distance']
        self.str_Size_3         = ['Winkelgeschwindigkeit',                                                                                                 'Angular velocity']
        ## Checkbox: ################################################################################################################################################################################################################################################################################   
        cb_sync_str             = ['Sync',                                                                                                                  'Sync']
        cb_gPad_str             = ['GPad',                                                                                                                  'GPad']
        cb_PID                  = ['PID',                                                                                                                   'PID']
        cb_RZLoop               = ['Rez.-Loop',                                                                                                             'Rec.-Loop']
        ## ToolTip: ###############################################################################################################################################################################################################################################################################                                                                                                   
        self.TTLimit            = ['Limit-',                                                                                                                'Limit-']
        self.TTSize_1           = ['Input-',                                                                                                                'Input-']
        self.TTSize_2           = ['Output-',                                                                                                               'Output-']
        self.TTSize_3           = ['Parameter:',                                                                                                            'Parameter:']
        if self.Antriebs_wahl == 'L':   self.TTSize_v           = ['v:',                                                                                    'v:']
        else:                           self.TTSize_v           = ['\u03C9:',                                                                               '\u03C9:']
        self.TTSize_x           = ['x:',                                                                                                                    'x:']
        self.TTSize_s           = ['s:',                                                                                                                    's:']
        self.TTSize_kp          = ['kp =',                                                                                                                  'kp =']
        self.TTSize_ki          = ['ki =',                                                                                                                  'ki =']
        self.TTSize_kd          = ['kd =',                                                                                                                  'kd =']
        self.TTRezeptLoop       = ['Anzahl Rezept-Wiederholungen =',                                                                                        'Number of recipe repetitions =']
        ## Einheiten mit Größe: ####################################################################################################################################################################################################################################################################
        if self.Antriebs_wahl == 'L':
            self.v_str              = ['v in mm/min:',                                                                                                      'v in mm/min:']
            sv_str                  = ['v:',                                                                                                                'v:']
            v_einzel_str            = ['v',                                                                                                                 'v']
            st_v_str                = ['XXX.XX mm/min',                                                                                                     'XXX.XX mm/min']
            self.einheit_v_einzel   = ['mm/min',                                                                                                            'mm/min']
        else: # R oder F - Beides Rotationen!
            self.v_str              = ['\u03C9 in 1/min:',                                                                                                  '\u03C9 in 1/min:'] 
            sv_str                  = ['\u03C9:',                                                                                                           '\u03C9:']              # Omega
            v_einzel_str            = ['\u03C9',                                                                                                            '\u03C9']
            st_v_str                = ['XXX.XX 1/min',                                                                                                      'XXX.XX 1/min']
            self.einheit_v_einzel   = ['1/min',                                                                                                             '1/min']
        self.s_str              = ['in mm:',                                                                                                                'in mm:']
        self.x_str              = [f'x in {self.unit_PIDIn}:',                                                                                              f'x in {self.unit_PIDIn}:']
        sx_str                  = ['PID:',                                                                                                                  'PID:']
        st_s_str                = ['XXX.XX mm',                                                                                                             'XXX.XX mm']
        st_x_str                = [f'XXX.XX {self.unit_PIDIn}',                                                                                             f'XXX.XX {self.unit_PIDIn}'] 
        s_einzel_str            = ['s',                                                                                                                     's']
        x_einzel_str            = ['x',                                                                                                                     'x']
        self.einheit_s_einzel   = ['mm',                                                                                                                    'mm']
        self.einheit_x_einzel   = [f'{self.unit_PIDIn}',                                                                                                    f'{self.unit_PIDIn}']
        PID_Von_1               = ['Wert von Multilog',                                                                                                     'Value of Multilog']
        PID_Von_2               = ['Wert von VIFCON',                                                                                                       'Value ofVIFCON']
        PID_Zusatz              = ['ex,',                                                                                                                   'ex,']
        self.PID_G_Kurve        = ['PID-x',                                                                                                                 'PID-x']
        ## Fehlermeldungen: #####################################################################################################################################################################################################################################################################
        self.err_0_str          = ['Fehler!',                                                                                                               'Error!']
        self.err_1_str          = ['Keine EINGABE!!',                                                                                                       'No INPUT!!']
        self.err_2_str          = ['Grenzen überschritten!\nGrenzen von',                                                                                   'Limits exceeded!\nLimits from']
        self.err_3_str          = ['bis',                                                                                                                   'to']
        self.err_4_str          = ['Gerät anschließen und\nInitialisieren!',                                                                                'Connect the device\nand initialize!']
        self.err_5_str          = ['Fehlerhafte Eingabe!',                                                                                                  'Incorrect input!']
        self.err_6_str          = ['Der Wert',                                                                                                              'The value']
        self.err_7_str          = ['überschreitet\ndie Grenzen von',                                                                                        'exceeds\nthe limits of']
        self.err_9_str          = ['Der Schritt',                                                                                                           'Step']
        self.err_10_str         = ['Rezept Einlesefehler!',                                                                                                 'Recipe import error!']
        self.err_12_str         = ['Erster Schritt = Sprung!\nDa keine Messwerte!',                                                                         'First step = jump! There\nare no measurements!']
        self.err_13_str         = ['o.K.',                                                                                                                  'o.K.']   
        self.err_14_str         = ['Rezept läuft!\nRezept Einlesen gesperrt!',                                                                              'Recipe is running!\nReading recipes blocked!']
        self.err_15_str         = ['Wähle ein Rezept!',                                                                                                     'Choose a recipe!']
        self.err_16_str         = ['Rezept läuft!\nRezept Start gesperrt!',                                                                                 'Recipe running!\nRecipe start blocked!']
        self.err_21_str         = ['Fehler in der Rezept konfiguration\nder Config-Datei! Bitte beheben und Neueinlesen!',                                  'Error in the recipe configuration of\nthe config file! Please fix and re-read!']
        self.err_22_str         = ['Eingabe darf nicht negativ sein!\nNegativer Limit Bereich nur bei Rezept-Modus zu nutzen!',                             'Input must not be negative!\nNegative limit range can only be used in recipe mode!']            
        self.err_PID_1_str      = ['Die Bewegungsrichtung',                                                                                                 'The direction of movement']
        # Muss geändert werden! # self.err_PID_2_str      = ['exestiert nicht!\nGenutzt werden kann nur UP und DOWN!',                                                    'does not exist!\nOnly UP and DOWN can be used!']
        self.err_PID_3_str      = ['Der PID-Modus benötigt eine\nAngabe der Bewegungsrichtung!',                                                            'The PID mode requires a specification\nof the direction of movement!']
        self.Fehler_out_1       = ['Maximum Limit erreicht!\nStopp ausgelöst!',                                                                             'Maximum limit reached!\nStop triggered!']
        self.Fehler_out_2       = ['Minimum Limit erreicht!\nStopp ausgelöst!',                                                                             'Minimum limit reached!\nStop triggered!']
        self.Fehler_out_3       = ['Limit erreicht!\nKnopf wird nicht ausgeführt!',                                                                         'Limit reached!\nButton is not executed!']
        self.Fehler_out_4       = ['Wert wurde als Nan erkannt!\nAntrieb wird aus Sicherheitsgründen gestoppt!',                                            'Value was recognized as Nan!\nDrive is stopped for safety reasons!']
        self.Fehler_out_5       = ['Wert wurde als Nan erkannt!',                                                                                           'Value was recognized as Nan!']
        self.err_Rezept         = ['Rezept Einlesefehler!\nUnbekanntes Segment:',                                                                           'Recipe reading error!\nUnknown segment:']
        self.Log_Yaml_Error     = ['Mit der Config-Datei (Yaml) gibt es ein Problem.',                                                                      'There is a problem with the config file (YAML).']
        self.err_RezDef_str     = ['Yaml-Config Fehler\nDefault-Rezept eingefügt!',                                                                         'Yaml config error\nDefault recipe inserted!']
        self.err_Rezept_2       = ['Rezept-Schritt:',                                                                                                       'Recipe step:']
        ## Plot-Legende: ########################################################################################################################################################################################################################################################################                                                    
        rezept_Label_str        = ['Rezept',                                                                                                                'Recipe']
        ober_Grenze_str         = ['oG',                                                                                                                    'uL']                                   # uL - upper Limit
        unter_Grenze_str        = ['uG',                                                                                                                    'lL']                                   # lL - lower Limit
        ## Logging: #############################################################################################################################################################################################################################################################################
        self.Log_Text_1_str 	= ['Erstelle Widget.',                                                                                                      'Create widget.']
        self.Log_Text_28_str    = ['Gerät wurde Gestartet/Initialisiert!',                                                                                  'Device has been started/initialized!']
        self.Log_Text_29_str    = ['Gerät wurde nicht Initialisiert! Initialisierung durch Menü im späteren!',                                              'Device was not initialized! Initialization through menu later!']
        self.Log_Text_30_str    = ['Neustart Modus.',                                                                                                       'Restart mode.']
        self.Log_Text_39_str    = ['Rezept:',                                                                                                               'Recipe:']
        self.Log_Text_40_str    = ['Rezept Inhalt:',                                                                                                        'Recipe content:']
        self.Log_Text_49_str    = ['Stopp!',                                                                                                                'Stop!']
        self.Log_Text_50_str    = ['Zeit des Verriegelungs Timers kann nicht bestimmt werden! Setze Zeit auf 10 ms!',                                       'Time of the locking timer cannot be determined! Set time to 10 ms!']
        self.Log_Text_51_str    = ['Zu fahrende Position:',                                                                                                 'Position to travel:']
        self.Log_Text_52_str    = ['Konfiguration aktualisieren (Nullpunkt setzen PI)',                                                                     'Update configuration (Define-Home PI)']
        self.Log_Text_53_str    = ['Fehlerhafte Eingabe bei Position - Grund:',                                                                             'Incorrect entry at position - Reason:']
        self.Log_Text_54_str    = ['Fehlerhafte Eingabe bei Geschwindigkeit - Grund:',                                                                      'Incorrect input for speed - Rreason:']
        self.Log_Text_55_str    = ['Rezept hat folgende zu fahrende Weg-Abfolge:',                                                                          'Recipe has the following route sequence to be traveled:']
        self.Log_Text_56_str    = ['Konfiguration aktualisieren (Position setzen):',                                                                        'Update configuration (Set Position):']
        self.Log_Text_57_str    = ['Rezept hat folgende zu fahrende Positions-Abfolge:',                                                                    'Recipe has the following position sequence to be driven:']
        self.Log_Text_205_str   = ['Update Konfiguration (Update Limits):',                                                                                 'Update configuration (update limits):']
        self.Log_Text_219_str   = ['Knopf kann nicht ausgeführt werden da Limit erreicht!',                                                                 'Button cannot be executed because limit has been reached!']         
        self.Log_Text_Ex1_str   = ['Fehler Grund (Rezept einlesen):',                                                                                       'Error reason (reading recipe):']
        self.Log_Text_Ex2_str   = ['Fehler Grund (Problem mit Rezept-Konfiguration):',                                                                      'Error reason (Problem with recipe configuration)']
        self.Log_Text_PID_Ex    = ['Der Wert in der Konfig liegt außerhalb des Limit-Bereiches! Umschaltwert wird auf Minimum-Limit gesetzt!',              'The value in the config is outside the limit range! Switching value is set to minimum limit!']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                                          'Limit range']
        if self.Antriebs_wahl == 'L':   
            self.Log_Text_LB_2      = ['Geschwindigkeit',                                                                                                   'Velocity']
            self.Log_Text_247_str   = ['Hoch',                                                                                                              'Up']
            self.Log_Text_248_str   = ['Runter',                                                                                                            'Down']
        else:                                       
            self.Log_Text_LB_2      = ['Winkelgeschwindigkeit',                                                                                             'Angular velocity']
            self.Log_Text_247_str   = ['CW',                                                                                                                'CW']
            self.Log_Text_248_str   = ['CCW',                                                                                                               'CCW']                         
        self.Log_Text_LB_3      = ['Position',                                                                                                              'Position']
        self.Log_Text_LB_4      = ['bis',                                                                                                                   'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                                           'after update']
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                                      'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                         'Possible values:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                              'Default is used:']
        self.Log_Text_Kurve     = ['Kurvenbezeichnung existiert nicht:',                                                                                    'Curve name does not exist:']
        self.Log_Text_Edu_1     = ['Der Antrieb, der gewählt wurde ist: ',                                                                                  'The drive that was chosen is: ']
        self.Log_Text_Edu_2     = ['Linear',                                                                                                                'Linear']
        self.Log_Text_Edu_3     = ['Rotation',                                                                                                              'Rotation']
        self.Log_Text_Edu_4     = ['Lüfter',                                                                                                                'Fan']
        self.Log_Text_Edu_5     = ['Unbekannt',                                                                                                             'Unknown']
        self.Log_Text_Edu_6     = ['Die Darstellung der Bewegung durch Farbige Knöpfe ist beim Lüfter nicht vorgesehen! Setze Konfiguration auf False!',    'The representation of movement using colored buttons is not provided for the fan! Set configuration to False!']
        self.Log_Text_Edu_7     = ['Das Rezept',                                                                                                            'The Recipe']
        self.Log_Text_Edu_8     = ['wird',                                                                                                                  'is repeated']
        self.Log_Text_Edu_9     = ['mal wiederholt. Das Rezept läuft somit',                                                                                'times. The recipe therefore runs']
        self.Log_Text_Edu_10    = ['mal!',                                                                                                                  'times!']
        ## Ablaufdatei: ########################################################################################################################################################################################################################################################################
        if self.Antriebs_wahl == 'L':
            self.Text_35_str        = ['Setze die Geschwindigkeit auf',                                                                                     'Set the speed up to']
            self.Text_36_str        = ['mm/min!',                                                                                                           'mm/min!']
            self.Text_45_str        = ['Knopf betätigt - Hoch!',                                                                                            'Button pressed - Up!']
            self.Text_46_str        = ['Knopf betätigt - Runter!',                                                                                          'Button pressed - down!']
        else:
            self.Text_35_str        = ['Setze die Winkelgeschwindigkeit auf',                                                                               'Set the Angular velocity up to']
            self.Text_36_str        = ['1/min!',                                                                                                            '1/min!']
            if self.Antriebs_wahl == 'R':
                self.Text_45_str    = ['Knopf betätigt - CW!',                                                                                              'Button pressed - CW!']
                self.Text_46_str    = ['Knopf betätigt - CCW !',                                                                                            'Button pressed - CCW!']
            else:
                self.Text_45_str    = ['Knopf betätigt - Starte Lüfter!',                                                                                   'Button pressed - start fan!']
        self.Text_23_str        = ['Knopf betätigt - Initialisierung!',                                                                                     'Button pressed - initialization!']
        self.Text_24_str        = ['Ausführung des Rezeptes:',                                                                                              'Execution of the recipe:']
        self.Text_33_str        = ['Knopf betätigt - Stopp/Alle Stopp!',                                                                                    'Button pressed - Stop/All Stop!']
        self.Text_39_str        = ['Knopf betätigt - Positon definieren!',                                                                                  'Button pressed - Define Postion!']
        self.Text_39_1_str      = ['Position definieren aufgrund der Eingabe in der GUI fehlgeschlagen!',                                                   'Define position failed due to input in the GUI!']           
        self.Text_40_str        = ['Eingabefeld Fehlermeldung: Keine oder Fehlende Eingabe!',                                                               'Input field error message: No or missing input!']
        self.Text_42_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da Grenzen überschritten werden!',                                    'Input field error message: Sending failed because limits were exceeded!']
        self.Text_43_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da fehlerhafte Eingabe!',                                             'Input field error message: Sending failed due to incorrect input!']
        self.Text_44_str        = ['Achse steht wieder!',                                                                                                   'Axis is standing again!']
        self.Text_47_str        = ['Knopf betätigt - Stopp!',                                                                                               'Button pressed - stop!']
        self.Text_81_str        = ['Knopf betätigt - Beende Rezept',                                                                                        'Button pressed - End recipe']
        self.Text_82_str        = ['Rezept ist zu Ende!',                                                                                                   'Recipe is finished!']
        self.Text_83_str        = ['Stopp betätigt - Beende Rezept',                                                                                        'Stop pressed - End recipe']
        self.Text_84_str        = ['Rezept läuft! Erneuter Start verhindert!',                                                                              'Recipe is running! Restart prevented!']
        self.Text_85_str        = ['Rezept Startet',                                                                                                        'Recipe Starts']
        self.Text_86_str        = ['Rezept Beenden',                                                                                                        'Recipe Ends']
        self.Text_87_str        = ['Knopf betätigt - Start Rezept',                                                                                         'Button pressed - Start recipe']
        self.Text_88_str        = ['Rezept konnte aufgrund von Fehler nicht gestartet werden!',                                                             'Recipe could not be started due to an error!']
        self.Text_89_str        = ['Knopf betätigt - Beende Rezept - Keine Wirkung auf Rezept-Funktion, jedoch Auslösung des Stopp-Knopfes!',               'Button pressed - End recipe - No effect on recipe function, but triggers the stop button!']
        self.Text_90_str        = ['Sicherer Endzustand wird hergestellt! Auslösung des Stopp-Knopfes!',                                                    'Safe final state is established! Stop button is activated!']
        self.Text_91_str        = ['Rezept Beenden - Sicherer Endzustand',                                                                                  'Recipe Ends - Safe End State']
        self.Text_PID_1         = ['Wechsel in PID-Modus.',                                                                                                 'Switch to PID mode.']
        self.Text_PID_2         = ['Wechsel in PI-Achsen-Regel-Modus.',                                                                                     'Switch to PI axis control mode.']
        self.Text_PID_3         = ['Moduswechsel! Auslösung des Stopp-Knopfes aus Sicherheitsgründen!',                                                     'Mode change! Stop button triggered for safety reasons!']
        self.Text_PID_4         = ['Rezept Beenden! Wechsel des Modus!',                                                                                    'End recipe! Change mode!']
        self.Text_ExLimit_str   = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da Negativer Wert!',                                                  'Input field error message: Sending failed because of negative value!']
        self.Text_Update        = ['Update Fehlgeschlagen!',                                                                                                'Update Failed!']
        self.Text_Update_2      = ['Rezept neu einlesen Fehlgeschlagen!',                                                                                   'Reload recipe failed!']
        self.Text_PIDReset_str  = ['PID Reset ausgelöst',                                                                                                   'PID reset triggered']
        self.Text_LimitUpdate   = ['Limit Update ausgelöst',                                                                                                'limit update triggered']
        self.Text_Extra_1       = ['Menü-Knopf betätigt - ',                                                                                                'Menu button pressed - ']
        self.Text_PIDResetError = ['Der PID ist aktiv in Nutzung und kann nicht resettet werden!',                                                          'The PID is actively in use and cannot be reset!']
        self.Text_Edu_1_str     = ['Rezept-Wiederholungen:',                                                                                                'Recipe repetitions:']
        
        #---------------------------------------
        # Konfigurationen für das Senden:
        #---------------------------------------
        #self.send_betätigt = False
        self.write_task  = {'Stopp': False, 'Sende Position': False, 'Sende Speed': False, 'Init':False, 'Start':False, 'Update Limit': False, 'PID': False, 'PID-Reset': False, 'Rezept Aktiv': False}
        self.write_value = {'Position': 0, 'Speed': 0, 'Limits': [0, 0, 0, 0, 0, 0], 'PID-Sollwert': 0} # Limits: oGv, uGv, oGs, uGs, oGx, uGx

        # Wenn Init = False, dann werden die Start-Auslesungen nicht ausgeführt:
        if self.init and not self.neustart:
            self.write_task['Start'] = True

        #---------------------------------------
        # Nachrichten im Log-File:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_28_str[self.sprache]}") if self.init else logger.warning(f"{self.device_name} - {self.Log_Text_29_str[self.sprache]}")
        if self.neustart: logger.info(f"{self.device_name} - {self.Log_Text_30_str[self.sprache]}") 
        logger.info(f"{self.device_name} - {self.Log_Text_Edu_1[self.sprache]}{self.Log_Text_Edu_2[self.sprache] if self.Antriebs_wahl == 'L' else (self.Log_Text_Edu_3[self.sprache] if self.Antriebs_wahl == 'R' else (self.Log_Text_Edu_4[self.sprache] if self.Antriebs_wahl == 'F' else self.Log_Text_Edu_5[self.sprache]))}")
        ## Limit-Bereiche:
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]}: {self.uGv} {self.Log_Text_LB_4[self.sprache]} {self.oGv} {self.einheit_v_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]}: {self.uGs} {self.Log_Text_LB_4[self.sprache]} {self.oGs} {self.einheit_s_einzel[self.sprache]}')

        ## Config-Fehler und Defaults:
        if self.BTN_BW_grün == 'Error': 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} knopf_anzeige - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False')
            self.BTN_BW_grün = 0

        ## Knopf-Anzeige exestiert bei Lüfter nicht:
        if self.Antriebs_wahl == 'F' and self.BTN_BW_grün:
            logger.info(f'{self.device_name} - {self.Log_Text_Edu_6[self.sprache]}')
            self.BTN_BW_grün = 0

        #---------------------------------------
        # GUI:
        #---------------------------------------
        ## Icon Bestimmung:
        if self.Antriebs_wahl == 'L':
            self.icon_1 = "./vifcon/icons/p_hoch.png"               
            self.icon_2 = "./vifcon/icons/p_runter.png"          
        elif self.Antriebs_wahl == 'R':
            self.icon_1 = "./vifcon/icons/p_cw.png"               
            self.icon_2 = "./vifcon/icons/p_ccw.png"    
        elif self.Antriebs_wahl == 'F':
            self.icon_1 = "./vifcon/icons/p_start.png"               
            self.icon_2 = "./vifcon/icons/p_nichts.png"

         #________________________________________    
        ## Grundgerüst:
        self.layer_widget = QWidget()
        self.layer_layout = QGridLayout()
        self.layer_widget.setLayout(self.layer_layout)
        self.typ_widget.splitter_main.splitter.addWidget(self.layer_widget)
        logger.info(f"{self.device_name} - {self.Log_Text_1_str[self.sprache]}")
        #________________________________________
        ## Kompakteres Darstellen:
        ### Grid Size - bei Verschieben der Splitter zusammenhängend darstellen:
        self.layer_layout.setRowStretch(6, 1) 
        self.layer_layout.setColumnStretch(6, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)       
        self.layer_layout.setVerticalSpacing(1)

        ### Zeilenhöhen:
        self.layer_layout.setRowMinimumHeight(1, 30)    # Error-Nachricht
        self.layer_layout.setRowMinimumHeight(2, 30)    # Error-Nachricht

        ### Spaltenbreiten:
        self.layer_layout.setColumnMinimumWidth(0, 120)
        self.layer_layout.setColumnMinimumWidth(2, 60)
        self.layer_layout.setColumnMinimumWidth(3, 60)
        self.layer_layout.setColumnMinimumWidth(4, 140)
        #________________________________________
        ## Widgets:
        ### Eingabefelder:
        self.LE_Pos = QLineEdit()
        self.LE_Pos.setText(str(self.startPos))
        TT_s = f'{self.TTLimit[self.sprache]}{self.TTSize_s[self.sprache]} {self.uGs} ... {self.oGs} {self.einheit_s_einzel[self.sprache]}'
        self.LE_Pos.setToolTip(TT_s)

        if not self.Antriebs_wahl == 'L':
            self.LE_Pos.setEnabled(False)

        self.LE_Speed = QLineEdit()
        self.LE_Speed.setText(str(self.startSpeed))
        TT_v = f'{self.TTLimit[self.sprache]}{self.TTSize_v[self.sprache]} {self.uGv} ... {self.oGv} {self.einheit_v_einzel[self.sprache]}'
        self.LE_Speed.setToolTip(TT_v)

        ### Checkbox:
        self.Auswahl = QCheckBox(cb_sync_str[self.sprache])
        self.gamepad = QCheckBox(cb_gPad_str[self.sprache])
        
        if not self.gamepad_aktiv:
            self.gamepad.setEnabled(False)

        self.PID_cb  = QCheckBox(cb_PID[self.sprache])
        self.PID_cb.clicked.connect(self.PID_ON_OFF)
        if not self.PID_Aktiv:
            self.PID_cb.setEnabled(False)
        
        self.TT_PID_In   = f'{self.TTSize_1[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_x[self.sprache]} {self.uGx} ... {self.oGx} {self.einheit_x_einzel[self.sprache]}'
        self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_v[self.sprache]} {self.uGv} ... {self.oGv} {self.einheit_v_einzel[self.sprache]}'
        self.TT_PID_Para = f'{self.TTSize_3[self.sprache]} {self.TTSize_kp[self.sprache]} {kp_conf}; {self.TTSize_ki[self.sprache]} {ki_conf}; {self.TTSize_kd[self.sprache]} {kd_conf}'
        self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')

        self.RZLoop_cb = QCheckBox(cb_RZLoop[self.sprache])
        self.RZLoop_cb.setToolTip(f'{self.TTRezeptLoop[self.sprache]} {self.rezept_Loop}')

        ### Label:
        #### Titel-Gerät:
        self.La_name = QLabel(f'<b>{eduAchse}</b> ({self.Antriebs_wahl})')
        #### Fehlernachrichten:
        self.La_error_1 = QLabel(self.err_13_str[self.sprache])
        self.La_error_2 = QLabel(self.err_13_str[self.sprache])
        #### Istposition:
        self.La_IstPos_text = QLabel(f"{istwert_str[self.sprache]}-{s_einzel_str[self.sprache]}: ")
        self.La_IstPos_wert = QLabel(st_s_str[self.sprache])
        if self.color_Aktiv: self.La_IstPos_text.setStyleSheet(f"color: {self.color[0]}")
        if self.color_Aktiv: self.La_IstPos_wert.setStyleSheet(f"color: {self.color[0]}")
        #### Istgeschwindigkeit:
        self.La_IstSpeed_text = QLabel(f'{istwert_str[self.sprache]}-{sv_str[self.sprache]} ')
        self.La_IstSpeed_wert = QLabel(st_v_str[self.sprache])
        if self.color_Aktiv: self.La_IstSpeed_text.setStyleSheet(f"color: {self.color[1]}")
        if self.color_Aktiv: self.La_IstSpeed_wert.setStyleSheet(f"color: {self.color[1]}")
        #### Sollposition:
        self.La_SollPos_text = QLabel(f'{self.Position[self.sprache]} {self.s_str[self.sprache]}')
        #### Soll-Geschwindigkeit:
        self.La_SollSpeed = QLabel(self.v_str[self.sprache])
        if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: black")

        self.La_SollSpeed_text = QLabel(f'{sollwert_str[self.sprache]}-{sv_str[self.sprache]} ')
        self.La_SollSpeed_wert = QLabel(st_v_str[self.sprache])
        if self.color_Aktiv: self.La_SollSpeed_text.setStyleSheet(f"color: black")
        if self.color_Aktiv: self.La_SollSpeed_wert.setStyleSheet(f"color: black")
        #### Soll-Größe PID-Modus:
        self.La_SollPID_text = QLabel(f'{sollwert_str[self.sprache]}-{sx_str[self.sprache]} ')
        self.La_SollPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_SollPID_text.setStyleSheet(f"color: {self.color[3]}")
        if self.color_Aktiv: self.La_SollPID_wert.setStyleSheet(f"color: {self.color[3]}")
        #### Ist-Größe PID-Modus:
        self.La_IstPID_text = QLabel(f'{istwert_str[self.sprache]}-{sx_str[self.sprache]} ')
        self.La_IstPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_IstPID_text.setStyleSheet(f"color: {self.color[4]}")
        if self.color_Aktiv: self.La_IstPID_wert.setStyleSheet(f"color: {self.color[4]}")

        ### Knöpfe:
        #### Bewegungen:
        self.btn_left = QPushButton(QIcon(self.icon_1), '')
        self.btn_left.setFlat(True)
        self.btn_left.clicked.connect(self.fahre_links_K)

        self.btn_right = QPushButton(QIcon(self.icon_2), '')
        self.btn_right.setFlat(True)
        self.btn_right.clicked.connect(self.fahre_rechts_K)
        #### Stopp:
        icon_pfad = "./vifcon/icons/p_stopp.png" if sprache == 0 else  "./vifcon/icons/p_stopp_En.png" 
        self.btn_mitte = QPushButton(QIcon(icon_pfad), '')
        self.btn_mitte.setFlat(True)
        self.btn_mitte.clicked.connect(self.Stopp)
        #### Define-Home:
        self.btn_DH = QPushButton(DH_str[self.sprache])
        self.btn_DH.clicked.connect(self.define_home) 
        if not self.Antriebs_wahl == 'L':   self.btn_DH.setEnabled(False)

        #### Rezepte:
        self.btn_rezept_start =  QPushButton(rez_start_str[self.sprache])
        self.btn_rezept_start.clicked.connect(lambda: self.RezStart(1))

        self.btn_rezept_ende =  QPushButton(rez_ende_str[self.sprache])
        self.btn_rezept_ende.clicked.connect(self.Stopp)  

        ### Combobox:
        self.cb_Rezept = QComboBox()
        self.cb_Rezept.addItem('------------')
        try:
            for rezept in self.rezept_config:
                self.cb_Rezept.addItem(rezept) 
        except Exception as e:
            self.Fehler_Output(1, self.err_21_str[self.sprache])
            logger.exception(self.Log_Text_Ex2_str[self.sprache])    
        self.cb_Rezept.setStyleSheet('''* 
                                    QComboBox QAbstractItemView 
                                        {
                                        min-width:200px;
                                        }
                                    ''')    # https://stackoverflow.com/questions/37632845/qcombobox-adjust-drop-down-width

        ### Gruppen Widgets:
        #### Bewegungsknöpfe:
        self.btn_group_move = QWidget()
        self.btn_move_layout = QHBoxLayout()
        self.btn_group_move.setLayout(self.btn_move_layout)
        self.btn_move_layout.setSpacing(20)

        self.btn_move_layout.addWidget(self.btn_left)
        self.btn_move_layout.addWidget(self.btn_mitte)
        self.btn_move_layout.addWidget(self.btn_right)

        self.btn_move_layout.setContentsMargins(0,10,0,0)  # left, top, right, bottom

        #### Rezept und Define-Home:
        self.btn_group_Rezept = QWidget()
        self.btn_Rezept_layout = QVBoxLayout()
        self.btn_group_Rezept.setLayout(self.btn_Rezept_layout)
        self.btn_Rezept_layout.setSpacing(5)

        self.btn_Rezept_layout.addWidget(self.btn_DH)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_start)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_ende)
        self.btn_Rezept_layout.addWidget(self.cb_Rezept)

        self.btn_Rezept_layout.setContentsMargins(0,0,0,0)  # left, top, right, bottom

        #### First-Row:
        self.first_row_group  = QWidget()
        self.first_row_layout = QHBoxLayout()
        self.first_row_group.setLayout(self.first_row_layout)
        self.first_row_layout.setSpacing(20)

        self.first_row_layout.addWidget(self.La_name)
        self.first_row_layout.addWidget(self.Auswahl)
        self.first_row_layout.addWidget(self.gamepad)
        self.first_row_layout.addWidget(self.PID_cb)
        self.first_row_layout.addWidget(self.RZLoop_cb)

        self.first_row_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom

        #### Label-Werte:
        W_spalte = 80

        if self.Antriebs_wahl == 'L':
            label_list      = [self.La_IstSpeed_text, self.La_IstPos_text, self.La_IstPID_text, self.La_SollPID_text]
            label_unit_list = [self.La_IstSpeed_wert, self.La_IstPos_wert, self.La_IstPID_wert, self.La_SollPID_wert]
        else:
            label_list      = [self.La_IstSpeed_text, self.La_IstPID_text, self.La_SollPID_text]
            label_unit_list = [self.La_IstSpeed_wert, self.La_IstPID_wert, self.La_SollPID_wert]

        widget_list     = []
        count = 0
        
        for n in label_list:
            W = QWidget()
            W_layout = QGridLayout()
            W.setLayout(W_layout)
            W_layout.addWidget(n, 0 , 0)
            W_layout.addWidget(label_unit_list[count], 0 , 1 , alignment=Qt.AlignLeft)
            W_layout.setContentsMargins(0,0,0,0)
            W_layout.setColumnMinimumWidth(0, W_spalte)
            widget_list.append(W)
            count += 1
        
        self.V = QWidget()
        self.V_layout = QVBoxLayout()
        self.V.setLayout(self.V_layout)
        self.V_layout.setSpacing(0)
        for n in widget_list:
            self.V_layout.addWidget(n)
        self.V_layout.setContentsMargins(0,0,0,0)

        #________________________________________
        ## Platzierung der einzelnen Widgets im Layout:
        self.layer_layout.addWidget(self.first_row_group,                   0, 0, 1, 6, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_SollSpeed,                      1, 0)
        self.layer_layout.addWidget(self.La_SollPos_text,                   2, 0)      
        self.layer_layout.addWidget(self.btn_group_move,                    3, 0, 1, 4, alignment=Qt.AlignLeft)                     # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung                     
        self.layer_layout.addWidget(self.LE_Speed,                          1, 1)
        self.layer_layout.addWidget(self.LE_Pos,                            2, 1)      
        self.layer_layout.addWidget(self.La_error_1,                        1, 2,       alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_error_2,                        2, 2,       alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.V,                                 1, 3, 2, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.btn_group_Rezept,                  1, 5, 4, 1, alignment=Qt.AlignTop)
        #________________________________________
        ## Größen (Size) - Widgets:
        ### Button-Icon:
        self.btn_left.setIconSize(QSize(50, 50))
        self.btn_right.setIconSize(QSize(50, 50))
        self.btn_mitte.setIconSize(QSize(50, 50))

        ### Eingabefelder (Line Edit):
        self.LE_Speed.setFixedWidth(100)
        self.LE_Speed.setFixedHeight(25)

        self.LE_Pos.setFixedWidth(100)
        self.LE_Pos.setFixedHeight(25)

        ### Rezpt-Funktionen:
        self.btn_rezept_start.setFixedWidth(100)
        self.btn_rezept_ende.setFixedWidth(100)
        self.cb_Rezept.setFixedWidth(100)
        self.btn_DH.setFixedWidth(100)
        #________________________________________
        ## Border Sichtbar:
        if Frame_Anzeige:
            self.layer_widget.setStyleSheet("border: 1px solid black;")

        #---------------------------------------
        # Kurven:
        #---------------------------------------
        ## PID-Modus:
        ### Istwert:
        PID_Export_Ist = ''
        if self.origin[0] == 'V': PID_Label_Ist = PID_Von_2[sprache]
        elif self.origin[0] == 'M':     
            PID_Label_Ist  = PID_Von_1[sprache]
            PID_Export_Ist = PID_Zusatz[sprache]
        else:                PID_Label_Ist = PID_Von_2[sprache]
        ### Sollwert
        PID_Export_Soll = ''
        if self.origin[1] == 'V':  PID_Label_Soll = PID_Von_2[sprache]
        elif self.origin[1] == 'M':     
            PID_Label_Soll  = PID_Von_1[sprache]
            PID_Export_Soll = PID_Zusatz[sprache]
        else:                 PID_Label_Soll = PID_Von_2[sprache]

        kurv_dict = {                                                               # Wert: [Achse, Farbe/Stift, Name]
            'IWs':      ['a1', pg.mkPen(self.color[0], width=2),                         f'{eduAchse} - {s_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'IWv':      ['a2', pg.mkPen(self.color[1], width=2),                         f'{eduAchse} - {v_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'oGs':      ['a1', pg.mkPen(color=self.color[0], style=Qt.DashLine),         f'{eduAchse} - {s_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGs':      ['a1', pg.mkPen(color=self.color[0], style=Qt.DashDotDotLine),   f'{eduAchse} - {s_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGv':      ['a2', pg.mkPen(color=self.color[1], style=Qt.DashLine),         f'{eduAchse} - {v_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGv':      ['a2', pg.mkPen(color=self.color[1], style=Qt.DashDotDotLine),   f'{eduAchse} - {v_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'Rezv':     ['a2', pg.mkPen(color=self.color[2], width=3, style=Qt.DotLine), f'{eduAchse} - {rezept_Label_str[self.sprache]}<sub>{v_einzel_str[self.sprache]}</sub>'],
            'Rezx':     ['a1', pg.mkPen(color=self.color[5], width=3, style=Qt.DotLine), f'{eduAchse} - {rezept_Label_str[self.sprache]}<sub>{x_einzel_str[self.sprache]}</sub>'],
            'SWxPID':   ['a1', pg.mkPen(self.color[3], width=2, style=Qt.DashDotLine),   f'{PID_Label_Soll} - {x_einzel_str[self.sprache]}<sub>{PID_Export_Soll}{sollwert_str[self.sprache]}</sub>'], 
            'IWxPID':   ['a1', pg.mkPen(self.color[4], width=2, style=Qt.DashDotLine),   f'{PID_Label_Ist} - {x_einzel_str[self.sprache]}<sub>{PID_Export_Ist}{istwert_str[self.sprache]}</sub>'],
            'oGPID':    ['a1', pg.mkPen(color=self.color[4], style=Qt.DashLine),         f'{eduAchse} - {self.PID_G_Kurve[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGPID':    ['a1', pg.mkPen(color=self.color[4], style=Qt.DashDotDotLine),   f'{eduAchse} - {self.PID_G_Kurve[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
        }

        ## Kurven erstellen:
        ist_drin_list = []                                                      # Jede Kurve kann nur einmal gesetzt werden!
        self.kurven_dict = {}
        for legend_kurve in self.legenden_inhalt:
            if legend_kurve in kurv_dict and not legend_kurve in ist_drin_list:
                if kurv_dict[legend_kurve][0] == 'a1':
                    curve = self.typ_widget.plot.achse_1.plot([], pen=kurv_dict[legend_kurve][1], name=kurv_dict[legend_kurve][2])
                    if self.typ_widget.legend_pos.upper() == 'OUT':
                        self.typ_widget.plot.legend.addItem(curve, curve.name())
                elif kurv_dict[legend_kurve][0] == 'a2':
                    curve = pg.PlotCurveItem([], pen=kurv_dict[legend_kurve][1], name=kurv_dict[legend_kurve][2])
                    self.typ_widget.plot.achse_2.addItem(curve)
                    if self.typ_widget.legend_pos.upper() == 'OUT' or self.typ_widget.legend_pos.upper() == 'IN':
                        self.typ_widget.plot.legend.addItem(curve, curve.name())
                self.kurven_dict.update({legend_kurve: curve})
                ist_drin_list.append(legend_kurve)
            elif not legend_kurve in kurv_dict:
                logger.warning(f'{self.device_name} - {self.Log_Text_Kurve[self.sprache]} {legend_kurve}')

        ## Checkboxen erstellen:
        self.kurven_side_legend         = {}

        if self.typ_widget.legend_pos.upper() == 'SIDE':
            for kurve in self.kurven_dict:
                widget, side_checkbox = self.GUI_Legend_Side(kurv_dict[kurve][2].split(' - '), kurv_dict[kurve][1], kurv_dict[kurve][0])
                if self.typ_widget.Side_Legend_position.upper() == 'RL':
                    if kurv_dict[kurve][0] == 'a1': self.typ_widget.legend_achsen_Links_widget.layout.addWidget(widget)
                    elif kurv_dict[kurve][0] == 'a2': self.typ_widget.legend_achsen_Rechts_widget.layout.addWidget(widget)
                elif self.typ_widget.Side_Legend_position.upper() == 'R':
                    self.typ_widget.legend_achsen_Rechts_widget.layout.addWidget(widget)
                elif self.typ_widget.Side_Legend_position.upper() == 'L':
                    self.typ_widget.legend_achsen_Links_widget.layout.addWidget(widget)
                self.kurven_side_legend.update({side_checkbox: kurve})

        ## Kurven-Daten-Listen:
        ### Messgrößen:
        self.posList        = []
        self.speedList      = []
        self.speedSollList  = []
        self.sollxPID       = []
        self.istxPID        = []
        ### Grenzen:
        self.VoGList        = []
        self.VuGList        = []
        self.SoGList        = []
        self.SuGList        = []
        self.XoGList        = []
        self.XuGList        = []

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.curveDict      = {'IWs': '', 'IWv': '', 'oGs': '', 'uGs': '', 'oGv': '', 'uGv': '', 'Rezv': '', 'SWxPID':'', 'IWxPID':'', 'oGPID':'', 'uGPID':''}                                                                                                                              # Kurven
        for kurve in self.kurven_dict:
            self.curveDict[kurve] = self.kurven_dict[kurve]
        self.labelDict      = {'IWs': self.La_IstPos_wert,                  'IWv': self.La_IstSpeed_wert,                   'IWxPID': self.La_IstPID_wert,                 'SWxPID': self.La_SollPID_wert,}                            # Label
        self.labelUnitDict  = {'IWs': self.einheit_s_einzel[self.sprache],  'IWv': self.einheit_v_einzel[self.sprache],     'IWxPID': self.einheit_x_einzel[self.sprache], 'SWxPID': self.einheit_x_einzel[self.sprache]}              # Einheit
        self.listDict       = {'IWs': self.posList,                         'IWv': self.speedList,                          'IWxPID': self.istxPID,                        'SWxPID': self.sollxPID,}                                   # Werteliste
        self.grenzListDict  = {'oGv': self.VoGList,                         'uGv': self.VuGList,    'oGs': self.SoGList,    'uGs': self.SuGList,                    'oGPID': self.XoGList,                         'uGPID': self.XuGList}
        self.grenzValueDict = {'oGv': self.oGv,                             'uGv': self.uGv,        'oGs': self.oGs,      'uGs': self.uGs,                      'oGPID': self.oGx,                             'uGPID': self.uGx}

        ## Plot-Skalierungsfaktoren:
        self.skalFak_dict = {}
        for size in self.curveDict:
            if 'Ws' in size:
                self.skalFak_dict.update({size: self.skalFak['Pos']})
            if 'Wv' in size:
                if self.Antriebs_wahl == 'L':   self.skalFak_dict.update({size: self.skalFak['Speed_2']})
                else:                           self.skalFak_dict.update({size: self.skalFak['WinSpeed']})
            if 'Wx' in size:
                self.skalFak_dict.update({size: self.skalFak['PIDA']})

        #---------------------------------------
        # Timer:
        #---------------------------------------
        ## Rezept-Timer
        self.RezTimer = QTimer()                                                                
        self.RezTimer.timeout.connect(self.Rezept)  

        #---------------------------------------
        # Rezept-Anzeige Funktion aktivieren:
        #---------------------------------------
        self.cb_Rezept.currentTextChanged.connect(self.RezKurveAnzeige) 

    ##########################################
    # Legenden an der Seite:
    ##########################################
    def GUI_Legend_Side(self, text, check_pen, achse):
        style = {1: '\u2501' * 2, 2: '\u2501 \u2501', 3: '\u00B7 \u00B7 ' * 2, 4: '\u2501\u00B7' * 3, 5: '\u2501\u00B7\u00B7' * 2} # 1: Solid, 2: Dashed, 3: Dot, 4: Dash Dot, 5: Dash Dot Dot

        check_Widget = QWidget()
        check_Layout = QHBoxLayout()
        check_Widget.setLayout(check_Layout)
        # Checkbox:
        check_legend = QCheckBox()
        check_legend.clicked.connect(self.Side_Legend)
        check_legend.setChecked(True)
        check_legend.setToolTip(text[0])
        if achse == 'a2':
            check_legend.setStyleSheet("QCheckBox::indicator::unchecked { background-color : darkgray; image : url('./vifcon/icons/unchecked.png'); }\n"
                                       "QCheckBox::indicator::checked { background-color : red; image : url('./vifcon/icons/checked.png'); }\n"
                                       "QCheckBox::indicator{ border : 1px solid black;}")
        else:
            check_legend.setStyleSheet("QCheckBox::indicator::unchecked { background-color : lightgray; image : url('./vifcon/icons/unchecked.png'); }\n"
                                       "QCheckBox::indicator::checked { background-color : black; image : url('./vifcon/icons/checked2.png'); }\n"
                                       "QCheckBox::indicator{ border : 1px solid gray;}")
        # Linie:
        check_Line = QLabel(style[check_pen.style()])
        check_Line.setStyleSheet(f"color: {check_pen.color().name()};")
        font = check_Line.font()
        if check_pen.width() > 1:
            font.setBold(True)
        check_Line.setToolTip(text[0])
        # Label:
        check_text = QLabel(text[1])
        check_text.setToolTip(text[0])
        # Anhängen:
        check_Layout.addWidget(check_legend)
        check_Layout.addWidget(check_Line)
        check_Layout.addWidget(check_text)
        # Geometry:
        check_Layout.setContentsMargins(0,0,0,0)
        
        return check_Widget, check_legend
    
    def Side_Legend(self, state):
        checkbox = self.sender()                    # Klasse muss von QWidget erben, damit sender() Funktioniert - Durch die Methode kann geschaut werden welche Checkbox betätigt wurde!
        kurve = self.kurven_side_legend[checkbox]
        if checkbox.isChecked():
            self.curveDict[kurve].setVisible(True)
        else:
            self.curveDict[kurve].setVisible(False)

    ##########################################
    # Fehlermedlung:
    ##########################################
    def Fehler_Output(self, Fehler, La_error, error_Message_Log_GUI = '', error_Message_Ablauf = '', device = ''):
        ''' Erstelle Fehler-Nachricht für GUI, Ablaufdatei und Logging
        Args:
            Fehler (bool):                  False -> o.k. (schwarz), True -> Fehler (rot, bold)
            La_error (PyQt-Label):          Label das beschrieben werden soll (Objekt)
            error_Message_Log_GUI (str):    Nachricht die im Log und der GUI angezeigt wird
            error_Message_Ablauf (str):     Nachricht für die Ablaufdatei
            device (str):                   Wenn ein anderes Gerät genutzt wird (z.B. PID)
        ''' 
        if device == '':
            device_name = self.device_name
        else:
            device_name = device 
        if Fehler:
            La_error.setText(self.err_0_str[self.sprache])
            La_error.setToolTip(error_Message_Log_GUI)  
            La_error.setStyleSheet(f"color: red; font-weight: bold")
            zusatz = f'({self.str_Size_1[self.sprache]})' if La_error == self.La_error_1 else (f'({self.str_Size_2[self.sprache]})' if La_error == self.La_error_2 else '')
            log_vorberietung = error_Message_Log_GUI.replace("\n"," ") 
            logger.error(f'{device_name} - {log_vorberietung} {zusatz}')
        else:
            La_error.setText(self.err_13_str[self.sprache])
            La_error.setToolTip('')
            La_error.setStyleSheet(f"color: black; font-weight: normal")
        if not error_Message_Ablauf == '':
                self.add_Text_To_Ablauf_Datei(f'{device_name} - {error_Message_Ablauf}') 

    ##########################################
    # Reaktion auf Buttons:
    ##########################################
    def fahre_links(self):
        '''Synchron Knopf Achse'''
        if float(self.LE_Speed.text().replace(",", ".")) < 0:
            self.fahre_rechts_K()                                             # Minus
        else:
            self.fahre_links_K()                                              # Plus

    def fahre_links_K(self):
        '''Reaktion auf den Linken Knopf'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_45_str[self.sprache]}')
            self.Fehler_Output(0, self.La_error_1) 
            ans = self.controll_value()
            if not ans == '':
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = ans
                else:
                    self.write_value['Speed'] = ans
                self.write_task['Hoch'] = True
                self.write_task['Sende Speed'] = True
                if self.BTN_BW_grün:
                    self.btn_left.setIcon(QIcon(self.icon_1.replace('.png', '_Ein.png')))
                    self.btn_right.setIcon(QIcon(self.icon_2))
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def fahre_rechts_K(self):
        '''Reaktion auf den Rechten Knopf'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_46_str[self.sprache]}')
            self.Fehler_Output(0, self.La_error_1) 
            ans = self.controll_value()
            if not ans == '':
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = ans
                else:
                    self.write_value['Speed'] = ans * -1
                self.write_task['Sende Speed'] = True
                if self.BTN_BW_grün:
                    self.btn_left.setIcon(QIcon(self.icon_1))
                    self.btn_right.setIcon(QIcon(self.icon_2.replace('.png', '_Ein.png')))
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])
    
    def Stopp(self, n = 1):
        '''Halte Achse an'''
        if self.init:
            if n == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_47_str[self.sprache]}')
            elif n == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_90_str[self.sprache]}')
            elif n == 6: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_3[self.sprache]}') # PID wird eingeschaltet!!
            # Beende PID-Modus:
            if n != 6:
                self.PID_cb.setChecked(False)
                self.PID_ON_OFF()
            # Beende Rezept:
            self.RezEnde(n)
            # Sende Befehl:
            self.write_task['Stopp'] = True
            # Ändere GUI:
            if self.BTN_BW_grün:
                self.btn_left.setIcon(QIcon(self.icon_1))
                self.btn_right.setIcon(QIcon(self.icon_2))
            self.Fehler_Output(0, self.La_error_1)
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def define_home(self):
        ''' Sorgt dafür das die aktuelle Position zur Null wird.'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_39_str[self.sprache]}')
            ans = self.controll_value(False)
            if not ans == '':
                self.write_value['Position'] = ans
                logger.info(f"{self.device_name} - {self.Log_Text_56_str[self.sprache]}")
                self.update_Limit(1)
                self.write_task['Sende Position'] = True
            else:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_39_1_str[self.sprache]}')
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    ##########################################
    # Eingabefeld Kontrolle:
    ##########################################
    def controll_value(self, speed=True):
        ''' Kontrolliere die Eingabe eines Eingabefeldes.

        Args:
            speed (Bool):           Umschaltung zwischen Geschwindigkeit und Position (default True)
        Return:
            '' (str):               Fehlerfall
            speed_value (float):    Geschwindigkeitswert
        '''
        # Eingebabefeld auslesen:
        if speed:
            Eingabe = self.LE_Speed 
            Error   = self.La_error_1
        else:
            Eingabe = self.LE_Pos
            Error   = self.La_error_2
        value = Eingabe.text().replace(",", ".")
        okay = False

        # Auswahl Limits Sollwert:
        if self.PID_cb.isChecked():
            oGv = self.oGx
            uGv = self.uGx 
            unit = self.einheit_x_einzel[self.sprache]
        else:
            oGv = self.oGv
            uGv = self.uGv
            unit = self.einheit_v_einzel[self.sprache]

        # Wenn Eingabefelde leer ist, dann sende nicht:
        if value == '':
            self.Fehler_Output(1, Error, self.err_1_str[self.sprache], self.Text_40_str[self.sprache])
        else:
            # Kontrolle Speed:
            try:
                # Umwandeln Speed:
                value = float(value)
                if speed:
                # Kontrolliere die Grenzen/Limits:
                    if value < uGv or value > oGv:
                        self.Fehler_Output(1, Error, f'{self.err_2_str[self.sprache]} {uGv} {self.err_3_str[self.sprache]} {oGv} {unit}', self.Text_42_str[self.sprache])     
                    # Alles in Ordnung mit der Eingabe:
                    else:
                        self.Fehler_Output(0, Error)
                        okay = True
                else:
                    self.Fehler_Output(0, Error)
                    okay = True
            # Eingabe ist falsch:
            except:
                self.Fehler_Output(1, Error, self.err_5_str[self.sprache], self.Text_43_str[self.sprache])

        # Alles Okay:
        if okay:
            if speed:   return abs(value)
            else:       return value        # Position kann auch Negativ sein!
        # Rückgabe bei Fehler:
        return ''

    ##########################################
    # Reaktion Checkbox:
    ##########################################    
    def PID_ON_OFF(self):        
        '''PID-Modus toggeln'''               
        if self.PID_cb.isChecked():
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_1[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID'] = True
            self.write_task['Sende Speed'] = False
            self.Stopp(6)
            # GUI ändern:
            self.La_SollSpeed.setText(self.x_str[self.sprache])
            if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: {self.color[3]}")
            self.LE_Speed.setToolTip('')
            # Bei Multilog-Sollwert:
            if self.origin[1] == 'M':
                self.btn_rezept_start.setEnabled(False)
                self.btn_rezept_ende.setEnabled(False)
                self.cb_Rezept.setEnabled(False)
                self.LE_Speed.setEnabled(False)
        else:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_2[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID'] = False
            self.write_task['Sende Speed'] = False  
            self.Stopp(6)
            value = self.PID_Mode_Switch_Value
            self.LE_Speed.setText(str(value))
            if value > self.oGv or value < self.uGv:
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_Ex[self.sprache]}") 
                self.write_value['Speed'] = self.uGv
            else:
                self.write_value['Speed'] = value
            # GUI ändern:
            self.La_SollSpeed.setText(self.v_str[self.sprache])
            if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: black")
            TT_v = f'{self.TTLimit[self.sprache]}{self.TTSize_v[self.sprache]} {self.uGv} ... {self.oGv} {self.einheit_v_einzel[self.sprache]}'
            self.LE_Speed.setToolTip(TT_v)
            # Bei Multilog-Sollwert:
            if self.origin[1] == 'M':
                self.btn_rezept_start.setEnabled(True)
                self.btn_rezept_ende.setEnabled(True)
                self.cb_Rezept.setEnabled(True)
                self.LE_Speed.setEnabled(True)

    ##########################################
    # Betrachtung der Labels und Plots:
    ##########################################
    def update_GUI(self, value_dict, x_value):
        ''' Update der GUI, Plot und Label!

        Args:
            value_dict (dict):  Dictionary mit den aktuellen Werten!
            x_value (list):     Werte für die x-Achse
        '''

        self.data.update({'Time' : x_value[-1]})   
        self.data.update(value_dict)   

        for messung in value_dict:
            self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}')
            self.listDict[messung].append(value_dict[messung])
            if not self.curveDict[messung] == '':
                faktor = self.skalFak_dict[messung]
                y = [a * faktor for a in self.listDict[messung]]
                self.curveDict[messung].setData(x_value, y)   

        # Grenz-Kurven:
        ## Update Grenzwert-Dictionary:
        self.grenzValueDict['oGv']      = self.oGv      * self.skalFak['Speed_1']
        self.grenzValueDict['uGv']      = self.oGv*(-1) * self.skalFak['Speed_1']
        self.grenzValueDict['oGs']      = self.oGs    * self.skalFak['Pos']
        self.grenzValueDict['uGs']      = self.uGs    * self.skalFak['Pos']
        self.grenzValueDict['oGPID']    = self.oGx      * self.skalFak['PIDA']
        self.grenzValueDict['uGPID']    = self.uGx      * self.skalFak['PIDA']
        ## Update-Kurven:
        for kurve in self.kurven_dict:
            if kurve in self.grenzListDict:
                self.grenzListDict[kurve].append(float(self.grenzValueDict[kurve]))
                self.kurven_dict[kurve].setData(x_value, self.grenzListDict[kurve]) 

    def BTN_Back(self, Text_Number):
        ''' Mit der Funktion wird ein Limit-Stopp bzw. das Erreichen der Limits in der GUI bemerkbar gemacht!
        Args:
            Text_Number (int):  Nummer des Fehler Textes!
        '''
        if Text_Number == 0:    self.Fehler_Output(1, self.La_error_1, self.Fehler_out_1[self.sprache])
        elif Text_Number == 1:  self.Fehler_Output(1, self.La_error_1, self.Fehler_out_2[self.sprache])
        elif Text_Number == 2:  self.Fehler_Output(1, self.La_error_1, f'{self.Fehler_out_3[self.sprache]}\n{self.Log_Text_247_str[self.sprache]}', f'{self.Log_Text_219_str[self.sprache]} ({self.Log_Text_247_str[self.sprache]})')
        elif Text_Number == 3:  self.Fehler_Output(1, self.La_error_1, f'{self.Fehler_out_3[self.sprache]}\n{self.Log_Text_248_str[self.sprache]}', f'{self.Log_Text_219_str[self.sprache]} ({self.Log_Text_248_str[self.sprache]})')
        elif Text_Number == 4:  self.Fehler_Output(1, self.La_error_1, f'{self.Fehler_out_4[self.sprache]}', f'{self.Text_extra[self.sprache]}')
        elif Text_Number == 5:  self.Fehler_Output(1, self.La_error_1, f'{self.Fehler_out_5[self.sprache]}')

        if self.BTN_BW_grün and not Text_Number == 5:
            self.btn_left.setIcon(QIcon(self.icon_1))
            self.btn_right.setIcon(QIcon(self.icon_2))

    ##########################################
    # Reaktion auf Initialsierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung soll durch geführt werden '''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_23_str[self.sprache]}')
        self.write_task['Init'] = True

    def init_controll(self, init_okay, menu):
        ''' Anzeige auf GUI ändern

        Args:
            init_okay (bool):   Ändert die Init-Variable und das Icon in der GUI, je nach dem wie das Gerät entschieden hat!
            menu (QAction):     Menü Zeile in der das Icon geändert werden soll!
        '''
        if init_okay:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_Okay.png"))
            self.Fehler_Output(0, self.La_error_1)
            self.init = True
        else:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_nicht_Okay.png"))
            self.init = False

    ##########################################
    # Reaktion auf übergeordnete Butttons:
    ##########################################
    def update_Limit(self, wahl = 0):
        '''Lese die Config und Update die Limits

        Args:
            wahl (int): Ablauf-Datei Zusatz
        '''
        if wahl == 0:   extra = self.Text_Extra_1[self.sprache]
        elif wahl == 1: extra = ''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - ' + extra + f'{self.Text_LimitUpdate[self.sprache]}')
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Yaml erneut laden:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            with open(self.config_dat, encoding="utf-8") as f: 
                config = yaml.safe_load(f)
                logger.info(f"{self.device_name} - {self.Log_Text_205_str[self.sprache]} {config}")
            skippen = 0
        except Exception as e:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4_1[self.sprache]}')         
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            skippen = 1
        
        if not skippen:
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Konfiguration prüfen:
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ### Geschwindigkeits-Limit:
            try: self.oGv = config['devices'][self.device_name]["limits"]['maxSpeed']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxSpeed {self.Log_Pfad_conf_5[self.sprache]} 1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGv = 1
            #//////////////////////////////////////////////////////////////////////
            try: self.uGv = config['devices'][self.device_name]["limits"]['minSpeed']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minSpeed {self.Log_Pfad_conf_5[self.sprache]} -1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGv = -1
            #//////////////////////////////////////////////////////////////////////
            if not type(self.oGv) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGv)}')
                self.oGv = 1
            if not type(self.uGv) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} -1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGv)}')
                self.uGv = -1
            if self.oGv <= self.uGv:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} -1 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_11[self.sprache]})')
                self.uGv = -1
                self.oGv = 1    
            #//////////////////////////////////////////////////////////////////////
            ### Positions-Limit:
            try: self.oGs = config['devices'][self.device_name]["limits"]['maxPos']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxPos {self.Log_Pfad_conf_5[self.sprache]} 1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGs = 1
            #//////////////////////////////////////////////////////////////////////
            try: self.uGs = config['devices'][self.device_name]["limits"]['minPos']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minPos {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGs = 0
            #//////////////////////////////////////////////////////////////////////
            if not type(self.oGs) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 180 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGs)}')
                self.oGs = 180
            if not type(self.uGs) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGs)}')
                self.uGs = 0
            if self.oGs <= self.uGs:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
                self.uGs = 0
                self.oGs = 1
            #//////////////////////////////////////////////////////////////////////
            ### PID-Limit:
            try: self.oGx = config['devices'][self.device_name]['PID']['Input_Limit_max']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_max {self.Log_Pfad_conf_5[self.sprache]} 1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGx = 1
            #//////////////////////////////////////////////////////////////////////
            try: self.uGx = self.uGx = config['devices'][self.device_name]['PID']['Input_Limit_min']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_min {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGx = 0
            #//////////////////////////////////////////////////////////////////////
            if not type(self.oGx) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_max - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGx)}')
                self.oGx = 1
            if not type(self.uGx) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_min - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGx)}')
                self.uGx = 0
            if self.oGx <= self.uGx:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_12[self.sprache]})')
                self.uGx = 0
                self.oGx = 1

            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # ToolTip Update:
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if not self.PID_cb.isChecked():
                TT_v = f'{self.TTLimit[self.sprache]}{self.TTSize_v[self.sprache]} {self.uGv} ... {self.oGv} {self.einheit_v_einzel[self.sprache]}'
                self.LE_Speed.setToolTip(TT_v)

            self.TT_PID_In   = f'{self.TTSize_1[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_x[self.sprache]} {self.uGx} ... {self.oGx} {self.einheit_x_einzel[self.sprache]}'
            self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_v[self.sprache]} {self.uGv} ... {self.oGv} {self.einheit_v_einzel[self.sprache]}'
            self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')

            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Weiterleiten:
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGv} {self.Log_Text_LB_4[self.sprache]} {self.oGv} {self.einheit_v_einzel[self.sprache]}')
            logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGs} {self.Log_Text_LB_4[self.sprache]} {self.oGs} {self.einheit_s_einzel[self.sprache]}')

            self.write_task['Update Limit']     = True
            self.write_value['Limits']          = [self.oGs, self.uGs, self.oGv, self.uGv, self.oGx, self.uGx]

            self.Fehler_Output(0, self.La_error_1)
        else:
            self.Fehler_Output(1, self.La_error_1, self.Log_Yaml_Error[self.sprache], self.Text_Update[self.sprache])

    def PID_Reset(self):
        ''' Löse den Reset des PID-Reglers aus!'''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Extra_1[self.sprache]}{self.Text_PIDReset_str[self.sprache]}')
        
        if not self.PID_cb.isChecked():
            ## Aufagben setzen:
            self.write_task['Update Limit']  = True
            self.write_value['Limits']       = [self.oGs, self.uGs, self.oGv, self.uGv, self.oGx, self.uGx]
            self.write_task['PID-Reset']     = True
            self.write_value['PID-Sollwert'] = 0
            
            ## Meldung:
            self.Fehler_Output(0, self.La_error_1)
        else:
            self.Fehler_Output(1, self.La_error_1, self.Text_PIDResetError[self.sprache], self.Text_PIDResetError[self.sprache])

    def PID_ToolTip_Update(self, kp, ki, kd):
        '''Update des Tooltips der PID-Checkbox um die Parameter!
        
        Args: 
            kp (float):     Parameter kp - Proportionalglied
            ki (float):     Parameter ki - Integralteil
            kd (floar):     Parameter kd - Differenzialteil
        '''
        self.TT_PID_Para = f'{self.TTSize_3[self.sprache]} {self.TTSize_kp[self.sprache]} {kp}; {self.TTSize_ki[self.sprache]} {ki}; {self.TTSize_kd[self.sprache]} {kd}'
        self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')

    ##########################################
    # Reaktion auf Rezepte:
    ##########################################
    def RezStart(self, execute = 1):
        ''' Rezept wurde gestartet '''
        if self.init:
            if not self.Rezept_Aktiv:
                if execute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_87_str[self.sprache]}')
                elif execute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_85_str[self.sprache]}')
            
                # Variablen:                                                                   # Kontrolle ob alles mit Rezept stimmt
                self.step = 0
                self.Rezept_Aktiv = True

                # Kurve erstellen:
                error = self.RezKurveAnzeige()
                if self.cb_Rezept.currentText() == '------------':
                    self.Fehler_Output(1, self.La_error_1, self.err_15_str[self.sprache])
                    error = True

                if not error:
                    # Rezept Log-Notiz:
                    logger.info(f'{self.device_name} - {self.Log_Text_39_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}')
                    logger.info(f'{self.device_name} - {self.Log_Text_40_str[self.sprache]} {self.rezept_daten}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_24_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}') 

                    if self.RZLoop_cb.isChecked():
                        logger.info(f'{self.device_name} - {self.Log_Text_Edu_7[self.sprache]} {self.cb_Rezept.currentText()} {self.Log_Text_Edu_8[self.sprache]} {self.rezept_Loop} {self.Log_Text_Edu_9[self.sprache]} {self.rezept_Loop + 1} {self.Log_Text_Edu_10[self.sprache]}')
                        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Edu_1_str[self.sprache]} {self.rezept_Loop} ({self.cb_Rezept.currentText()})')
                    
                    # Erstes Element senden:
                    ## PID-Modus oder Normaler-Modus:
                    if self.PID_cb.isChecked():
                        self.write_value['PID-Sollwert'] = self.value_list[self.step]

                        if self.move_list[self.step] == 'UP':
                            self.write_task['Hoch'] = True
                            self.write_task['Runter'] = False
                            self.richtung_Rez = 'Hoch'
                        elif self.move_list[self.step] == 'DOWN':
                            self.write_task['Runter'] = True
                            self.write_task['Hoch'] = False
                            self.richtung_Rez = 'Runter'
                    else:
                        self.write_value['Speed'] = self.value_list[self.step]
                        self.write_task['Sende Speed'] = True

                        if self.value_list[self.step] < 0:             
                            ### Runter/CCW:
                            self.richtung_Rez = 'Runter'
                        else:
                            ### Hoch/CW:
                            self.richtung_Rez = 'Hoch'
                    ## Anzeige Betätigte Richtung:
                    if self.BTN_BW_grün and self.richtung_Rez == 'Hoch':
                        self.btn_right.setIcon(QIcon(self.icon_2))
                        self.btn_left.setIcon(QIcon(self.icon_1.replace('.png', '_Ein.png')))
                    if self.BTN_BW_grün and self.richtung_Rez == 'Runter':
                        self.btn_left.setIcon(QIcon(self.icon_1))
                        self.btn_right.setIcon(QIcon(self.icon_2.replace('.png', '_Ein.png')))
                    
                    # Elemente GUI sperren:
                    self.cb_Rezept.setEnabled(False)
                    self.btn_rezept_start.setEnabled(False)
                    self.btn_left.setEnabled(False)
                    self.btn_mitte.setEnabled(False)
                    self.btn_right.setEnabled(False)
                    self.btn_DH.setEnabled(False)
                    self.Auswahl.setEnabled(False)
                    self.PID_cb.setEnabled(False)
                    self.RZLoop_cb.setEnabled(False)

                    # Timer Starten:
                    self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))
                    self.RezTimer.start()
                    self.Fehler_Output(0, self.La_error_1)
                else:
                    self.Rezept_Aktiv = False
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_88_str[self.sprache]}')
            else:
                self.Fehler_Output(1, self.La_error_1, self.err_16_str[self.sprache], self.Text_84_str[self.sprache])
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def RezEnde(self, excecute = 1):
        ''' Rezept wurde/wird beendet '''
        if self.init:
            if self.Rezept_Aktiv == True:
                if excecute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_81_str[self.sprache]}')
                elif excecute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_82_str[self.sprache]}')
                elif excecute == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_83_str[self.sprache]}')
                elif excecute == 4: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_86_str[self.sprache]}')
                elif excecute == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_91_str[self.sprache]}')
                elif excecute == 6: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_4[self.sprache]}')

                # Elemente GUI entsperren:
                self.cb_Rezept.setEnabled(True)
                self.btn_rezept_start.setEnabled(True)
                self.btn_left.setEnabled(True)
                self.btn_mitte.setEnabled(True)
                if self.Antriebs_wahl == 'L':
                    self.btn_right.setEnabled(True)
                    self.btn_DH.setEnabled(True)
                self.Auswahl.setEnabled(True)
                if self.PID_Aktiv: self.PID_cb.setEnabled(True)
                self.RZLoop_cb.setEnabled(True)

                # Variablen:
                self.Rezept_Aktiv = False

                # Auto Range
                self.typ_widget.plot.AutoRange()

                # Nachricht:
                self.Fehler_Output(0, self.La_error_1)

                # Timer stoppen:
                self.RezTimer.stop()
            else:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_89_str[self.sprache]}')
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def Rezept(self):
        ''' Rezept Schritt wurde beendet, Vorbereitung und Start des neuen '''
        self.step += 1
        if self.step > len(self.time_list) - 1:
            self.Stopp(2)
        else:
            self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))

            # Nächstes Element senden:
            ## PID-Modus oder Normaler-Modus:
            if self.PID_cb.isChecked():
                self.write_value['PID-Sollwert'] = self.value_list[self.step]
                if self.move_list[self.step] == 'UP':
                    self.write_task['Hoch'] = True
                    self.write_task['Runter'] = False
                    richtung = 'Hoch'
                elif self.move_list[self.step] == 'DOWN':
                    self.write_task['Runter'] = True
                    self.write_task['Hoch'] = False
                    richtung = 'Runter'
            else:
                self.write_value['Speed'] = self.value_list[self.step]
                self.write_task['Sende Speed'] = True
                if self.value_list[self.step] < 0:             
                    ### Runter/CCW:
                    self.richtung_Rez = 'Runter'
                else:
                    ### Hoch/CW:
                    self.richtung_Rez = 'Hoch'
            ## Anzeige Betätigte Richtung:
            if self.BTN_BW_grün and self.richtung_Rez == 'Hoch':
                self.btn_right.setIcon(QIcon(self.icon_2))
                self.btn_left.setIcon(QIcon(self.icon_1.replace('.png', '_Ein.png')))
            if self.BTN_BW_grün and self.richtung_Rez == 'Runter':
                self.btn_left.setIcon(QIcon(self.icon_1))
                self.btn_right.setIcon(QIcon(self.icon_2.replace('.png', '_Ein.png')))
            
    def Rezept_lesen_controll(self):
        ''' Rezept wird ausgelesen und kontrolliert. Bei Fehler werden die Fehlermeldungen beschrieben auf der GUI.

        Return:
            error (Bool):   Fehler vorhanden oder nicht
        '''
        # Variablen:
        error = False
        self.time_list  = []
        self.value_list = []
        self.move_list  = []

        ## Geschwindigkeitlimits:
        uG = self.uGv
        oG = self.oGv
        string_einheit = self.einheit_v_einzel[self.sprache]

        ## Positionslimits:
        if self.Antriebs_wahl == 'L':
            uGs = self.uGs
            oGs = self.oGs

        ## PID-Limits:
        if self.PID_cb.isChecked():
            oG = self.oGx
            uG = self.uGx 
            string_einheit = self.einheit_x_einzel[self.sprache]

        ## Aktueller Wert Geschwindigkeit:
        ak_value = self.ak_value['IWv'] if not self.ak_value == {} else 0
        if self.PID_cb.isChecked(): ak_value = self.ak_value['IWxPID'] if not self.ak_value == {} else 0

        # Rezept lesen:
        rezept = self.cb_Rezept.currentText()
        pos_list = [] 
        try:
            start_pos = self.posList[-1]
        except:
            error = True 

        if not rezept == '------------' and not error:
            ## Rezept aus Datei oder in Config:
            ak_rezept = self.rezept_config[rezept]
            if 'dat' in ak_rezept:
                try:
                    with open(f'vifcon/rezepte/{ak_rezept["dat"]}', encoding="utf-8") as f:
                        rez_dat = yaml.safe_load(f)
                    self.rezept_datei = f'({ak_rezept["dat"]})'
                except:
                    self.Fehler_Output(1, self.La_error_1, self.err_10_str[self.sprache])
                    logger.exception(self.Log_Text_Ex1_str[self.sprache])
                    return True
            else:
                rez_dat = ak_rezept
                self.rezept_datei = '(Config-Datei)'
            ## Speichere aktuelle Daten des Rezepts für Logging:
            self.rezept_daten = rez_dat
            ## Ersten Eintrag prüfen:
            first_line = rez_dat[list(rez_dat.keys())[0]].split(';')[2]
            if first_line.strip() == 'r' and not self.ak_value == {}:
                self.value_list.append(ak_value) 
                self.time_list.append(0) 
                self.move_list.append('Beginn')
            elif first_line.strip() == 'r' and self.ak_value == {}:
                self.Fehler_Output(1, self.La_error_1, self.err_12_str[self.sprache])
                return True
            ## Bewegungsrichtung für PID-Modus prüfen:
            if self.PID_cb.isChecked():
                for n in rez_dat:
                    try:
                        werte = rez_dat[n].split(';')
                        if werte[2].strip() == 'r': sNum = 4
                        elif werte[2].strip() == 's': sNum = 3
                        if not werte[sNum].upper().strip() in ['UP', 'DOWN']:  
                            self.Fehler_Output(1, self.La_error_1, f'{self.err_PID_1_str[self.sprache]} {werte[sNum].upper()} {self.err_PID_2_str[self.sprache]}')
                            return True
                    except:
                        self.Fehler_Output(1, self.La_error_1, self.err_PID_3_str[self.sprache])
                        return True
            ## Rezept Kurven-Listen erstellen:
            for n in rez_dat:
                werte = rez_dat[n].split(';')
                ## Beachtung von Kommas (Komma zu Punkt):
                time = float(werte[0].replace(',', '.'))
                value = float(werte[1].replace(',','.'))
                ## Kontrolle Geschwindigkeit:
                if value < uG or value > oG:
                    error = True
                    self.Fehler_Output(1, self.La_error_1, f'{self.err_6_str[self.sprache]} {value} {string_einheit} {self.err_7_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG} {string_einheit}! ({self.err_Rezept_2[self.sprache]} {n})')
                    break
                else:
                    self.Fehler_Output(0, self.La_error_1)
                ## Rampe oder Sprung:
                ### Rampe:
                if werte[2].strip() == 'r':                         
                    rampen_config_step = float(werte[3])                # Zeitabstand für den Rampensprung (x-Achse)
                    rampen_bereich = value - self.value_list[-1]        # Bereich in dem die Rampe wirkt: Aktueller Wert - Letzten Eintrag (Rezept Stufe)
                    rampen_value = int(time/rampen_config_step)         # Anzahl der Rampensprünge
                    rampen_step = rampen_bereich/rampen_value           # Höhe des Sprungs je Rampensprung (y-Achse)
                    #### Berechnung der Listen Elemente:
                    for rampen_n in range(1,rampen_value+1):
                        if not rampen_n == rampen_value:
                            ak_ramp = self.value_list[-1] + rampen_step
                            self.value_list.append(round(ak_ramp,3))    # Runden: Eurotherm könnte bis 6 Nachkommerstellen, Display nur 2
                            self.time_list.append(rampen_config_step)
                        else: # Letzter Wert!
                            self.value_list.append(value)
                            self.time_list.append(rampen_config_step)   # 0 
                        if self.PID_cb.isChecked(): self.move_list.append(werte[4].upper().strip())
                ### Sprung:
                elif werte[2].strip() == 's':                                               
                    self.value_list.append(value)
                    self.time_list.append(time)
                    if self.PID_cb.isChecked(): self.move_list.append(werte[3].upper().strip())
                ### Falsches Segment:
                else:
                    self.Fehler_Output(1, self.La_error_1, f'{self.err_Rezept[self.sprache]} {werte[2].strip()} ({n})')
                    return True
            ## Loop-Funktion nutzen:
            if self.RZLoop_cb.isChecked():
                ### Listen-Vorbereiten bzw. merken:
                value_List_Loop = [] + self.value_list
                time_List_Loop  = [] + self.time_list
                if self.PID_cb.isChecked(): move_list_Loop = [] + self.move_list
                ### Listen erweitern:
                if self.rezept_Loop > 0:
                    for Loop in range(0,self.rezept_Loop,1):
                        self.value_list += value_List_Loop
                        self.time_list  += time_List_Loop
                        if self.PID_cb.isChecked(): self.move_list += move_list_Loop
            ## Positionen bestimmen:
            if not self.PID_cb.isChecked() and self.Antriebs_wahl == 'L':
                value_step = 0
                for n_PosP in self.value_list:
                    pos_list.append(1/60 * n_PosP * self.time_list[value_step])
                    value_step += 1
                
                ## Kontrolle Position:
                logger.debug(f"{self.device_name} - {self.Log_Text_57_str[self.sprache]} {pos_list}")
                rezept_schritt = 1 
                for n in pos_list:
                    pos = start_pos + n
                    start_pos = pos
                    if pos < uGs or pos > oGs:
                        error = True
                        self.Fehler_Output(1, self.La_error_1, f'{self.err_9_str[self.sprache]} {rezept_schritt} {self.err_7_str[self.sprache]} {uGs} {self.err_3_str[self.sprache]} {oGs} {self.einheit_s_einzel[self.sprache]}!')
                        break
                    else:
                        if not error:   self.Fehler_Output(0, self.La_error_1)
                    rezept_schritt += 1          
        else:
            self.Fehler_Output(0, self.La_error_1)
        return error
    
    def RezKurveAnzeige(self):
        '''Soll die Rezept-Kurve anzeigen und erstellen!
        
        Return:
            error (bool):   Rezeptfehler
        '''
        # Variablen:
        error = False                                                                        # Kontrolle ob alles mit Rezept stimmt  

        # Kurven zurücksetzen:
        self.RezTimeList = []
        self.RezValueList = []    

        anzeigev = True 
        if not self.PID_cb.isChecked():                        
            try: self.curveDict['Rezv'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigev  = False        
        else:
            try: self.curveDict['Rezx'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigev  = False                        

        # Startzeit bestimmen:
        ak_time_1 = datetime.datetime.now(datetime.timezone.utc).astimezone()                # Aktuelle Zeit Absolut
        ak_time = round((ak_time_1 - self.typ_widget.start_zeit).total_seconds(), 3)         # Aktuelle Zeit Relativ

        # Fehler-Kontrolle:
        try: error = self.Rezept_lesen_controll()
        except Exception as e:
            error = True
            logger.exception(f'{self.device_name} - {self.Log_Text_Ex1_str[self.sprache]}')
            self.Fehler_Output(1, self.La_error_1, self.err_10_str[self.sprache])

        if not error:
            # Kurve erstellen:
            i = 0
            for n in self.time_list:
                # Punkt 1:
                self.RezTimeList.append(ak_time)
                self.RezValueList.append(self.value_list[i])
                # Punkt 2:
                self.RezTimeList.append(ak_time + n)
                self.RezValueList.append(self.value_list[i])
                # nächsten Punkt vorbereiten:
                ak_time = ak_time + n
                i += 1

            # Kurve erstellen mit Skalierungsfaktor:
            if not self.PID_cb.isChecked(): 
                if self.Antriebs_wahl == 'L':   faktor = self.skalFak['Speed_2']
                else:                           faktor = self.skalFak['WinSpeed']
            else:                               faktor = self.skalFak['PIDA']
            
            y = [a * faktor for a in self.RezValueList]
            
            # Kurve Anzeigen:
            if anzeigev:
                if not self.PID_cb.isChecked(): 
                    self.curveDict['Rezv'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_2.autoRange()                            # Rezept Achse 2 wird nicht fertig angezeigt, aus dem Grund wird dies durchgeführt! Beim Enden wird die AutoRange Funktion von base_classes.py durchgeführt. Bewegung des Plots sind mit der Lösung nicht machbar!!
                                                                                        # Plot wird nur an Achse 1 (links) angepasst!
                else:
                    self.curveDict['Rezx'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_1.autoRange()

        return error

    def update_rezept(self):
        '''Liest die Config im Sinne der Rezepte neu ein und Updatet die Combo-Box'''
        if not self.Rezept_Aktiv:
            error = False
            # Trennen von der Funktion:
            self.cb_Rezept.currentTextChanged.disconnect(self.RezKurveAnzeige)                    # Benötigt um Aufruf bei Leerer ComboBox zu vermeiden (sonst KeyError: '')

            # Combo-Box leeren:
            self.cb_Rezept.clear() 

            # Config einlesen für das Gerät:
            try:
                # Yaml erneut laden:
                yaml_error = 1
                with open(self.config_dat, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                yaml_error = 2
                self.rezept_config = config['devices'][self.device_name]['rezepte']
            except Exception as e: 
                self.rezept_config = {'rezept_Default':  {'n1': '10 ; 0 ; s'}}
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Update_2[self.sprache]}')
                self.Fehler_Output(1, self.La_error_1, self.err_RezDef_str[self.sprache])
                error = True
                if yaml_error == 1:
                    logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4_1[self.sprache]} {self.Log_Pfad_conf_5[self.sprache]} {self.rezept_config}')
                    logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                elif yaml_error == 2:
                    logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} rezepte {self.Log_Pfad_conf_5[self.sprache]} {self.rezept_config}')
                    logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                    logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            
            # Combo-Box neu beschreiben:
            self.cb_Rezept.addItem('------------')
            try:
                for rezept in self.rezept_config:
                    self.cb_Rezept.addItem(rezept) 
            except Exception as e:
                self.Fehler_Output(1, self.La_error_1, self.err_21_str[self.sprache])
                error = True
                logger.exception(self.Log_Text_Ex2_str[self.sprache]) 

            # Neu verbinden von der Funktion:
            self.cb_Rezept.currentTextChanged.connect(self.RezKurveAnzeige) 

            if not error: self.Fehler_Output(0, self.La_error_1)
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_14_str[self.sprache])

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''
#'SWv':      ['a2', pg.mkPen(self.color[3], width=2),                         f'{eduAchse} - {v_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            
'SWv': self.La_SollSpeed_wert,            
'SWv': self.einheit_v_einzel[self.sprache]
'SWv': self.speedSollList,                

'SWv': '',

'''
