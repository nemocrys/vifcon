# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo-Achse Rotation Bewegung Widget:
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

class NemoAchseRotWidget(QWidget):
    def __init__(self, sprache, Frame_Anzeige, widget, line_color, config, config_dat, neustart, multilog_aktiv, add_Ablauf_function, nemoAchse, gamepad_aktiv, typ = 'Antrieb', parent=None):
        """ GUI widget of Nemo-Achse Rotation Bewegung.

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
            nemoAchse (str):                Name des Gerätes 
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
        self.device_name                = nemoAchse
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
        self.Log_Pfad_conf_11   = ['Winkelgeschwindhigkeit',                                                                                            'Angular velocity']
        self.Log_Pfad_conf_12   = ['PID-Eingang Istwert',                                                                                               'PID input actual value']
        self.Log_Pfad_conf_13   = ['Winkel',                                                                                                            'Angle']
        self.Log_Pfad_conf_14   = ['Konfiguration mit VM, MV oder MM ist so nicht möglich, da der Multilog-Link abgeschaltet ist! Setze Default VV!',   'Configuration with VM, MV or MM is not possible because the Multilog-Link is disabled! Set default VV!']
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Übergeordnet:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Anlage = self.config['nemo-Version']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} nemo-Version {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Anlage = 1
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Zum Start:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.init = self.config['start']['init']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.init = False
        #//////////////////////////////////////////////////////////////////////
        try: self.v_invert       = self.config['start']['invert']                          # Invertierung bei True der Geschwindigkeit
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|invert {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.v_invert = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.kont_Rot = self.config['start']['kont_rot']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|kont_rot {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.kont_Rot = False
        #//////////////////////////////////////////////////////////////////////
        try: self.startSpeed = float(str(self.config["defaults"]['startSpeed']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} defaults|startSpeed {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startSpeed = 1
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Limits:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.oGv = self.config["limits"]['maxSpeed']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxSpeed {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGv = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGv = self.config["limits"]['minSpeed']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minSpeed {self.Log_Pfad_conf_5[self.sprache]} -1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGv = -1
        #//////////////////////////////////////////////////////////////////////
        try: self.oGw = self.config["limits"]['maxWinkel']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxWinkel {self.Log_Pfad_conf_5[self.sprache]} 180')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGw = 180
        #//////////////////////////////////////////////////////////////////////
        try: self.uGw = self.config["limits"]['minWinkel']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minWinkel {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGw = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.oGx = self.config['PID']['Input_Limit_max']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_max {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGx = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGx = self.config['PID']['Input_Limit_min']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_min {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGx = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## GUI:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: 
            self.legenden_inhalt = self.config['GUI']['legend'].split(';')
            self.legenden_inhalt = [a.strip() for a in self.legenden_inhalt]    # sollten Unnötige Leerzeichen vorhanden sein, so werden diese entfernt!
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} GUI|legend {self.Log_Pfad_conf_5[self.sprache]} [IWv, IWw]')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.legenden_inhalt = ['IWv', 'IWw']
        #//////////////////////////////////////////////////////////////////////
        try: self.BTN_BW_grün     = self.config['GUI']['knopf_anzeige']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} GUI|knopf_anzeige {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.BTN_BW_grün = False
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Gamepad:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Button_Link = self.config['gamepad_Button']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} gamepad_Button {self.Log_Pfad_conf_5_4[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Button_Link   = 'RotS'
            self.gamepad_aktiv = False
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Rezepte:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.rezept_config = self.config["rezepte"]
        except Exception as e: 
            self.rezept_config = {'rezept_Default':  {'n1': '10 ; 0 ; s'}}
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} rezepte {self.Log_Pfad_conf_5[self.sprache]} {self.rezept_config}')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## PID-Modus:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.unit_PIDIn    = self.config['PID']['Input_Size_unit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Size_unit {self.Log_Pfad_conf_5[self.sprache]} mm')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.unit_PIDIn = 'mm'
        #//////////////////////////////////////////////////////////////////////
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
        try: self.PID_Aktiv = self.config['PID']['PID_Aktiv']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|PID_Aktiv {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Aktiv = 0 

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Config-Fehler und Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Knopf-Anzeige:
        if not type(self.BTN_BW_grün) == bool and not self.BTN_BW_grün in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} knopf_anzeige - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.BTN_BW_grün}')
            self.BTN_BW_grün = 0
        ### Anlagen-Version:
        if not self.Anlage in [1, 2]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nemo-Version - {self.Log_Pfad_conf_2[self.sprache]} [1, 2] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8[self.sprache]} {self.Anlage}')
            self.Anlage = 1
        ### Gamepad-Button:
        if not self.Button_Link in ['RotS', 'RotT']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} gamepad_Button - {self.Log_Pfad_conf_2[self.sprache]} [RotS, RotT] - {self.Log_Pfad_conf_5_4[self.sprache].replace("; ","")} - {self.Log_Pfad_conf_8[self.sprache]} {self.Button_Link}')
            self.Button_Link = 'RotS'
            self.gamepad_aktiv = False
        ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0
        ### Kontinuierlich Rotieren:
        if not type(self.kont_Rot) == bool and not self.kont_Rot in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} kont_rot - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.kont_Rot}')
            self.kont_Rot = 0
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
        ### Winkel-Limit:
        if not type(self.oGw) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxWinkel - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 180 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGw)}')
            self.oGw = 180
        if not type(self.uGw) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minWinkel - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGw)}')
            self.uGw = 0
        if self.oGw <= self.uGw:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 180 ({self.Log_Pfad_conf_13[self.sprache]})')
            self.uGw = 0
            self.oGw = 180
        ### Start-Geschwindigkeit:
        if not type(self.startSpeed) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.startSpeed)}')
            self.startSpeed = 1
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
        ### PID-Aktiv:
        if not type(self.PID_Aktiv) == bool and not self.PID_Aktiv in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Aktiv - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Aktiv}')
            self.PID_Aktiv = 0  
        ### Achsen-Invert:
        if not type(self.v_invert) == bool and not self.v_invert in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} invert - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.v_invert}')
            self.v_invert = 0
         
        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Anlage: ##################################################################################################################################################################################################################################################################################
        self.nemo               = ['Nemo-Anlage',                                                                                               'Nemo facility']
        ## Werte: ###################################################################################################################################################################################################################################################################################
        istwert_str             = ['Ist',                                                                                                       'Is']
        sollwert_str            = ['Soll',                                                                                                      'Set']
        ## Knöpfe: ##################################################################################################################################################################################################################################################################################                                                                  
        rez_start_str           = ['Rezept Start',                                                                                              'Start recipe']
        rez_ende_str            = ['Rezept Beenden',                                                                                            'Finish recipe']
        DH_str                  = ['Setz Nullpunkt',                                                                                            'Define Home']
        ## Zusatz: ##################################################################################################################################################################################################################################################################################
        self.str_Size_1         = ['Winkelgeschwindigkeit',                                                                                     'Angular velocity']
        self.str_Size_2         = ['Winkel',                                                                                                    'Angle']
        ## Checkbox: ################################################################################################################################################################################################################################################################################        
        cb_sync_str             = ['Sync',                                                                                                      'Sync']
        cb_EndloseRot_str       = ['Kont. Rot.',                                                                                                'Cont. Rot.']           # \u221E \u03B1
        cb_gPad_str             = ['GPad',                                                                                                      'GPad']
        cb_PID                  = ['PID',                                                                                                       'PID']
        ## ToolTip: ###############################################################################################################################################################################################################################################################################                                                                                                   
        self.TTLimit            = ['Limit:',                                                                                                    'Limit:']
        ## Einheiten mit Größe: #####################################################################################################################################################################################################################################################################
        self.v_str              = ['\u03C9 in 1/min:',                                                                                          '\u03C9 in 1/min:']
        self.x_str              = [f'x in {self.unit_PIDIn}:',                                                                                  f'x in {self.unit_PIDIn}:']
        sv_str                  = ['\u03C9:',                                                                                                   '\u03C9:']              # Omega
        sw_str                  = ['\u03B1 (sim):',                                                                                             '\u03B1 (sim):']        # Alpha
        sx_str                  = ['PID:',                                                                                                      'PID:']
        st_v_str                = ['XXX.XX 1/min',                                                                                              'XXX.XX 1/min']
        st_w_str                = ['XXX.XX°',                                                                                                   'XXX.XX°'] 
        st_x_str                = [f'XXX.XX {self.unit_PIDIn}',                                                                                 f'XXX.XX {self.unit_PIDIn}'] 
        w_einzel_str            = ['\u03B1',                                                                                                    '\u03B1']
        v_einzel_str            = ['\u03C9',                                                                                                    '\u03C9']
        x_einzel_str            = ['x',                                                                                                         'x']
        self.einheit_w_einzel   = ['°',                                                                                                         '°']
        self.einheit_v_einzel   = ['1/min',                                                                                                     '1/min']
        self.einheit_x_einzel   = [f'{self.unit_PIDIn}',                                                                                        f'{self.unit_PIDIn}']
        PID_Von_1               = ['Wert von Multilog',                                                                                         'Value of Multilog']
        PID_Von_2               = ['Wert von VIFCON',                                                                                           'Value ofVIFCON']
        PID_Zusatz              = ['ex,',                                                                                                       'ex,']
        self.PID_G_Kurve        = ['PID-x',                                                                                                     'PID-x']
        ## Fehlermeldungen: ########################################################################################################################################################################################################################################################################     
        self.err_0_str          = ['Fehler!',                                                                                                   'Error!'] 
        self.err_1_str          = ['Keine EINGABE!!',                                                                                           'No INPUT!!']
        self.err_2_str          = ['Grenzen überschritten!\nGrenzen von',                                                                       'Limits exceeded!\nLimits from']
        self.err_3_str          = ['bis',                                                                                                       'to']
        self.err_4_str          = ['Gerät anschließen und\nInitialisieren!',                                                                    'Connect the device\nand initialize!']
        self.err_5_str          = ['Fehlerhafte Eingabe!',                                                                                      'Incorrect input!']
        self.err_6_str          = ['Der Wert',                                                                                                  'The value']
        self.err_7_str          = ['überschreitet\ndie Grenzen von',                                                                            'exceeds\nthe limits of']
        self.err_9_str          = ['Der Schritt',                                                                                               'Step']
        self.err_10_str         = ['Rezept Einlesefehler!',                                                                                     'Recipe import error!']
        self.err_12_str         = ['Erster Schritt = Sprung!\nDa keine Messwerte!',                                                             'First step = jump! There\nare no measurements!']
        self.err_13_str         = ['o.K.',                                                                                                      'o.K.']                                     
        self.err_14_str         = ['Rezept läuft!\nRezept Einlesen gesperrt!',                                                                  'Recipe is running!\nReading recipes blocked!']
        self.err_15_str         = ['Wähle ein Rezept!',                                                                                         'Choose a recipe!']
        self.err_16_str         = ['Rezept läuft!\nRezept Start gesperrt!',                                                                     'Recipe running!\nRecipe start blocked!']    
        self.err_21_str         = ['Fehler in der Rezept konfiguration\nder Config-Datei! Bitte beheben und Neueinlesen!',                      'Error in the recipe configuration of\nthe config file! Please fix and re-read!']
        self.err_PID_1_str      = ['Die Bewegungsrichtung',                                                                                     'The direction of movement']
        self.err_PID_2_str      = ['exestiert nicht!\nGenutzt werden kann nur CW und CCW!',                                                     'does not exist!\nOnly CW and CCW can be used!']
        self.err_PID_3_str      = ['Der PID-Modus benötigt eine\nAngabe der Bewegungsrichtung!',                                                'The PID mode requires a specification\nof the direction of movement!']
        self.Fehler_out_1       = ['Limit Clock Wise erreicht!\nStopp ausgelöst!',                                                              'Limit Clock Wise reached!\nStop triggered!']
        self.Fehler_out_2       = ['Limit Counter Clock Wise erreicht!\nStopp ausgelöst!',                                                      'Limit Counter Clock Wise reached!\nStop triggered!']
        self.Fehler_out_3       = ['Limit erreicht!\nKnopf wird nicht ausgeführt!',                                                             'Limit reached!\nButton is not executed!']
        self.err_Rezept         = ['Rezept Einlesefehler!\nUnbekanntes Segment:',                                                               'Recipe reading error!\nUnknown segment:']
        self.Log_Yaml_Error     = ['Mit der Config-Datei (Yaml) gibt es ein Problem.',                                                          'There is a problem with the config file (YAML).']
        self.err_RezDef_str     = ['Yaml-Config Fehler\nDefault-Rezept eingefügt!',                                                             'Yaml config error\nDefault recipe inserted!']
        self.err_Rezept_2       = ['Rezept-Schritt:',                                                                                                                                                                                       'Recipe step:']
        ## Status-Algemein: ########################################################################################################################################################################################################################################################################          
        status_1_str            = ['Status: Inaktiv',                                                                                           'Status: Inactive']
        ## Status-N1: ##############################################################################################################################################################################################################################################################################                                                              
        self.status_2_str       = ['Kein Status',                                                                                               'No Status']
        self.status_3_str       = ['Status:',                                                                                                   'Status:']
        self.sta_Bit0_str       = ['Betriebsbereit',                                                                                            'Ready for operation']
        self.sta_Bit1_str       = ['Achse referiert',                                                                                           'Axis referenced']
        self.sta_Bit2_str       = ['Achse Fehler',                                                                                              'Axis error']
        self.sta_Bit3_str       = ['Antrieb läuft',                                                                                             'Drive is running']
        self.sta_Bit5_str       = ['Antrieb läuft im Uhrzeigersinn (Nemo-Anlage Rechts)',                                                       'Drive runs clock Wise (Nemo facility right)']
        self.sta_Bit4_str       = ['Antrieb läuft gegen den Uhrzeigersinn (Nemo-Anlage Links)',                                                 'Drive runs counter clockwise (Nemo facility left)']
        self.sta_Bit6_str       = ['Achse Position oben (Soft.-End.)',                                                                          'Axis position up (Soft.-End.)']
        self.sta_Bit7_str       = ['Achse Position unten (Soft.-End.)',                                                                         'Axis position down (Soft.-End.)']
        self.sta_Bit8_str       = ['Achse Endlage oben (Hard.-End.)',                                                                           'Axis end position up (Hard.-End.)']
        self.sta_Bit9_str       = ['Achse Endlage unten (Hard.-End.)',                                                                          'Axis end position down (Hard.-End.)']
        self.sta_Bit10_str      = ['Software-Endlagen aus',                                                                                     'Software end positions']
        self.sta_Bit11_str      = ['Achse in Stopp',                                                                                            'Axis in stop']
        self.sta_Bit12_str      = ['', ''] # Reserve
        self.sta_Bit13_str      = ['', ''] # Reserve
        self.sta_Bit14_str      = ['Schnittstellenfehler',                                                                                      'Interface error']
        self.sta_Bit15_str      = ['Test-Modus Aktiv',                                                                                          'Test Mode Active']
        ## Status-N2: ##############################################################################################################################################################################################################################################################################                                                              
        self.Stat_N2_Bit0       = self.sta_Bit5_str
        self.Stat_N2_Bit1       = self.sta_Bit11_str
        self.Stat_N2_Bit2       = self.sta_Bit4_str
        self.Stat_N2_Bit3       = self.sta_Bit0_str
        self.Stat_N2_Bit4       = self.sta_Bit2_str 
        self.Stat_N2_Bit5       = ['', ''] # Reserve
        self.Stat_N2_Bit6       = ['', ''] # Reserve
        self.Stat_N2_Bit7       = ['', ''] # Reserve
        self.Stat_N2_Bit8       = ['Rampe eingeschaltet',                                                                                       'Ramp switched on']
        self.Stat_N2_Bit9       = ['Rampe ausgeschaltet',                                                                                       'Ramp switched off']
        self.Stat_N2_Bit10      = ['Auf Winkel fahren ein',                                                                                     'Drive to angle on']
        self.Stat_N2_Bit11      = ['Auf Winkel fahren aus',                                                                                     'Drive to angle off']
        self.Stat_N2_Bit12      = ['', ''] # Reserve
        self.Stat_N2_Bit13      = ['', ''] # Reserve
        self.Stat_N2_Bit14      = self.sta_Bit14_str # Schnittstellen Fehler
        self.Stat_N2_Bit15      = self.sta_Bit15_str # Test-Modus
        ## Plot-Legende: ############################################################################################################################################################################################################################################################################                                                           
        rezept_Label_str        = ['Rezept',                                                                                                    'Recipe']
        ober_Grenze_str         = ['oG',                                                                                                        'uL']                    # uL - upper Limit
        unter_Grenze_str        = ['uG',                                                                                                        'lL']                    # lL - lower Limit
        ## Logging: #################################################################################################################################################################################################################################################################################
        self.Log_Text_1_str 	= ['Erstelle Widget.',                                                                                          'Create widget.']
        self.Log_Text_28_str    = ['Gerät wurde Gestartet/Initialisiert!',                                                                      'Device has been started/initialized!']
        self.Log_Text_29_str    = ['Gerät wurde nicht Initialisiert! Initialisierung durch Menü im späteren!',                                  'Device was not initialized! Initialization through menu later!']
        self.Log_Text_30_str    = ['Neustart Modus.',                                                                                           'Restart mode.']
        self.Log_Text_39_str    = ['Rezept:',                                                                                                   'Recipe:']
        self.Log_Text_40_str    = ['Rezept Inhalt:',                                                                                            'Recipe content:']
        self.Log_Text_58_str    = ['Konfiguration aktualisieren (Nullpunkt setzen Nemo Rotation)!',                                             'Update configuration (Define-Home Nemo rotation)!']
        self.Log_Text_59_str    = ['Rezept hat folgende zu fahrende Winkel-Abfolge:',                                                           'Recipe has the following angle sequence to be driven:']
        self.Log_Text_181_str   = ['Die Geschwindigkeit wird Invertiert! Die Wahren Werte hätten ein anderes Vorzeichen!',                      'The speed is inverted! The true values would have a different sign!']
        self.Log_Text_205_str   = ['Update Konfiguration (Update Limits):',                                                                     'Update configuration (update limits):']
        self.Log_Text_219_str   = ['Knopf kann nicht ausgeführt werden da Limit erreicht!',                                                     'Button cannot be executed because limit has been reached!']         
        self.Log_Text_249_str   = ['CW',                                                                                                        'CW']
        self.Log_Text_250_str   = ['CCW',                                                                                                       'CCW']
        self.Log_Text_Ex1_str   = ['Fehler Grund (Rezept einlesen):',                                                                           'Error reason (reading recipe):']
        self.Log_Text_Ex2_str   = ['Fehler Grund (Problem mit Rezept-Konfiguration):',                                                          'Error reason (Problem with recipe configuration)']
        self.Log_Text_PID_Ex    = ['Der Wert in der Konfig liegt außerhalb des Limit-Bereiches! Umschaltwert wird auf Minimum-Limit gesetzt!',  'The value in the config is outside the limit range! Switching value is set to minimum limit!']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                              'Limit range']
        self.Log_Text_LB_2      = ['Winkelgeschwindigkeit',                                                                                     'Angular velocity']
        self.Log_Text_LB_3      = ['Winkel',                                                                                                    'Angle']
        self.Log_Text_LB_4      = ['bis',                                                                                                       'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                               'after update']
        self.Log_Text_PS_1      = ['Auslösung des priorisierten Stopps! Richtungswechsel: Von',                                                 'Initiation of the prioritized stop! Change of direction: From']
        self.Log_Text_PS_2      = ['zu',                                                                                                        'to']
        self.Log_Text_Kurve     = ['Kurvenbezeichnung existiert nicht:',                                                                        'Curve name does not exist:']
        self.Log_Status_Int     = ['Status-Integer',                                                                                            'Status-Integer']
        ## Ablaufdatei: #############################################################################################################################################################################################################################################################################
        self.Text_23_str        = ['Knopf betätigt - Initialisierung!',                                                                         'Button pressed - initialization!']
        self.Text_24_str        = ['Ausführung des Rezeptes:',                                                                                  'Execution of the recipe:']
        self.Text_39_str        = ['Knopf betätigt - Nullpunkt setzen!',                                                                        'Button pressed - Define Home!']
        self.Text_42_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da Grenzen überschritten werden!',                        'Input field error message: Sending failed because limits were exceeded!']
        self.Text_43_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da fehlerhafte Eingabe!',                                 'Input field error message: Sending failed due to incorrect input!']
        self.Text_47_str        = ['Knopf betätigt - Stopp!',                                                                                   'Button pressed - stop!']
        self.Text_48_str        = ['Eingabefeld Fehlermeldung: Keine Eingabe!',                                                                 'Input field error message: No input!']
        self.Text_49_str        = ['Knopf betätigt - CW!',                                                                                      'Button pressed - CW!']
        self.Text_50_str        = ['Knopf betätigt - CCW !',                                                                                    'Button pressed - CCW!']
        self.Text_81_str        = ['Knopf betätigt - Beende Rezept',                                                                            'Button pressed - End recipe']
        self.Text_82_str        = ['Rezept ist zu Ende!',                                                                                       'Recipe is finished!']
        self.Text_83_str        = ['Stopp betätigt - Beende Rezept',                                                                            'Stop pressed - End recipe']
        self.Text_84_str        = ['Rezept läuft! Erneuter Start verhindert!',                                                                  'Recipe is running! Restart prevented!']
        self.Text_85_str        = ['Rezept Startet',                                                                                            'Recipe Starts']
        self.Text_86_str        = ['Rezept Beenden',                                                                                            'Recipe Ends']
        self.Text_87_str        = ['Knopf betätigt - Start Rezept',                                                                             'Button pressed - Start recipe']
        self.Text_88_str        = ['Rezept konnte aufgrund von Fehler nicht gestartet werden!',                                                 'Recipe could not be started due to an error!']
        self.Text_89_str        = ['Knopf betätigt - Beende Rezept - Keine Wirkung auf Rezept-Funktion, jedoch Auslösung des Stopp-Knopfes!',   'Button pressed - End recipe - No effect on recipe function, but triggers the stop button!']
        self.Text_90_str        = ['Sicherer Endzustand wird hergestellt! Auslösung des Stopp-Knopfes!',                                        'Safe final state is established! Stop button is activated!']
        self.Text_91_str        = ['Rezept Beenden - Sicherer Endzustand',                                                                      'Recipe Ends - Safe End State']
        self.Text_PID_1         = ['Wechsel in PID-Modus.',                                                                                     'Switch to PID mode.']
        self.Text_PID_2         = ['Wechsel in Nemo-Anlage Rotations-Regel-Modus.',                                                             'Switch to Nemo system rotation control mode.']
        self.Text_PID_3         = ['Moduswechsel! Auslösung des Stopp-Knopfes aus Sicherheitsgründen!',                                         'Mode change! Stop button triggered for safety reasons!']
        self.Text_PID_4         = ['Rezept Beenden! Wechsel des Modus!',                                                                        'End recipe! Change mode!']
        self.Text_PS_1          = ['Priorisierter Stopp aktiviert!',                                                                            'Prioritized stop activated!']
        self.Text_Update        = ['Update Fehlgeschlagen!',                                                                                    'Update Failed!']
        self.Text_Update_2      = ['Rezept neu einlesen Fehlgeschlagen!',                                                                       'Reload recipe failed!']
        self.Text_PIDReset_str  = ['PID Reset ausgelöst',                                                                                       'PID reset triggered']
        self.Text_LimitUpdate   = ['Limit Update ausgelöst',                                                                                    'limit update triggered']
        self.Text_Extra_1       = ['Menü-Knopf betätigt - ',                                                                                    'Menu button pressed - ']
        self.Text_PIDResetError = ['Der PID ist aktiv in Nutzung und kann nicht resettet werden!',                                              'The PID is actively in use and cannot be reset!']
        # Pop-Up-Fenster: ###########################################################################################################################################################################################################################################################################
        self.Pop_up_EndRot      = ['Das kontinuierlische rotieren wurde beendet. Bitte beachte, dass zu diesem Zeitpunkt bereits ein Limit überschritten sein kann. In Fall der Überschreitung setze den Winkel auf Null, schalte die kontinuierlische Rotation wieder ein oder fahre in die andere Richtung. Wenn z.B. das CCW Limit erreicht wurde, so kann der Antrieb noch immer bis zum CW Limit fahren.',
                                   'Continuous rotation has ended. Please note that a limit may already have been exceeded at this point. If this limit is exceeded, set the angle to zero, switch continuous rotation back on or move in the other direction. If, for example, the CCW limit has been reached, the drive can still move up to the CW limit.']
        
        #---------------------------------------
        # Konfigurationen für das Senden:
        #---------------------------------------
        self.write_task  = {'Stopp': False, 'CCW': False, 'CW': False, 'Init':False, 'Define Home': False, 'Start':False, 'Send':False, 'Update Limit': False, 'PID': False, 'EndRot':False, 'Prio-Stopp': False, 'PID-Reset': False}
        self.write_value = {'Speed': 0, 'Limits': [0, 0, 0, 0, 0, 0], 'PID-Sollwert': 0} # Limits: oGw, uGw, oGv, uGv, oGx, uGx

        # Wenn Init = False, dann werden die Start-Auslesungen nicht ausgeführt:
        if self.init and not self.neustart:
            self.write_task['Start'] = True
        
        #---------------------------------------
        # Konfigurationen Check:
        #---------------------------------------
        try: self.write_value['PID-Sollwert'] = self.config['PID']['start_soll'] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|start_soll {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.write_value['PID-Sollwert'] = 0
        #//////////////////////////////////////////////////////////////////////
        if not type(self.write_value['PID-Sollwert']) in [int, float]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_soll - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.write_value["PID-Sollwert"])}')
            self.write_value['PID-Sollwert'] = 0

        #---------------------------------------
        # Nachrichten im Log-File:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_28_str[self.sprache]}") if self.init else logger.warning(f"{self.device_name} - {self.Log_Text_29_str[self.sprache]}")
        if self.neustart: logger.info(f"{self.device_name} - {self.Log_Text_30_str[self.sprache]}") 
        if self.v_invert: logger.warning(f'{self.device_name} - {self.Log_Text_181_str[self.sprache]}')
        ## Limit-Bereiche:
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]}: {self.uGv} {self.Log_Text_LB_4[self.sprache]} {self.oGv} {self.einheit_v_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]}: {self.uGw} {self.Log_Text_LB_4[self.sprache]} {self.oGw}{self.einheit_w_einzel[self.sprache]}')

        #---------------------------------------
        # GUI:
        #---------------------------------------                    
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
        self.layer_layout.setRowMinimumHeight(1, 40)    # Error-Nachricht

        ### Spaltenbreiten:
        self.layer_layout.setColumnMinimumWidth(0, 120)
        self.layer_layout.setColumnMinimumWidth(2, 60)
        self.layer_layout.setColumnMinimumWidth(3, 80)
        self.layer_layout.setColumnMinimumWidth(4, 120)
        #________________________________________
        ## Widgets:
        ### Eingabefelder:
        self.LE_Speed = QLineEdit()
        self.LE_Speed.setText(str(self.startSpeed))
        TT_v = f'{self.TTLimit[self.sprache]} {self.uGv} ... {self.oGv} {self.einheit_v_einzel[self.sprache]}'
        self.LE_Speed.setToolTip(TT_v)

        ### Checkbox:
        self.Auswahl = QCheckBox(cb_sync_str[self.sprache])
        self.EndRot  = QCheckBox(cb_EndloseRot_str[self.sprache])
        self.EndRot.clicked.connect(self.Rotation_Nonstopp)
        if self.kont_Rot:
            self.EndRot.setChecked(True)
            self.Rotation_Nonstopp()
        
        self.gamepad = QCheckBox(cb_gPad_str[self.sprache])
        if not self.gamepad_aktiv:
            self.gamepad.setEnabled(False)

        self.PID_cb  = QCheckBox(cb_PID[self.sprache])
        self.PID_cb.clicked.connect(self.PID_ON_OFF)
        if not self.PID_Aktiv:
            self.PID_cb.setEnabled(False)
        
        TT_PID = f'{self.TTLimit[self.sprache]} {self.uGx} ... {self.oGx} {self.einheit_x_einzel[self.sprache]}'
        self.PID_cb.setToolTip(TT_PID)

        ### Label:
        #### Titel-Gerät:
        self.La_name = QLabel(f'<b>{nemoAchse}</b> ({self.nemo[self.sprache]} {self.Anlage})')
        #### Fehlernachrichten:
        self.La_error_1 = QLabel(self.err_13_str[self.sprache])
        #### Istwinkelgeschwindigkeit:
        self.La_IstSpeed_text = QLabel(f'{istwert_str[self.sprache]}-{sv_str[self.sprache]} ')
        self.La_IstSpeed_wert = QLabel(st_v_str[self.sprache])
        if self.color_Aktiv: self.La_IstSpeed_text.setStyleSheet(f"color: {self.color[0]}")
        if self.color_Aktiv: self.La_IstSpeed_wert.setStyleSheet(f"color: {self.color[0]}")
        #### Istwinkel:
        self.La_IstWin_text = QLabel(f'{istwert_str[self.sprache]}-{sw_str[self.sprache]} ')
        self.La_IstWin_wert = QLabel(st_w_str[self.sprache])
        if self.color_Aktiv: self.La_IstWin_text.setStyleSheet(f"color: {self.color[1]}")
        if self.color_Aktiv: self.La_IstWin_wert.setStyleSheet(f"color: {self.color[1]}")
        #### Statuswert:
        self.La_Status = QLabel(status_1_str[self.sprache])
        #### Sollwinkelgeschwindigkeit:
        self.La_SollSpeed = QLabel(self.v_str[self.sprache])
        if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: {self.color[2]}")

        self.La_SollSpeed_text = QLabel(f'{sollwert_str[self.sprache]}-{sv_str[self.sprache]} ')
        self.La_SollSpeed_wert = QLabel(st_v_str[self.sprache])
        if self.color_Aktiv: self.La_SollSpeed_text.setStyleSheet(f"color: {self.color[2]}")
        if self.color_Aktiv: self.La_SollSpeed_wert.setStyleSheet(f"color: {self.color[2]}")
        #### Soll-Größe PID-Modus:
        self.La_SollPID_text = QLabel(f'{sollwert_str[self.sprache]}-{sx_str[self.sprache]} ')
        self.La_SollPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_SollPID_text.setStyleSheet(f"color: {self.color[4]}")
        if self.color_Aktiv: self.La_SollPID_wert.setStyleSheet(f"color: {self.color[4]}")
        #### Ist-Größe PID-Modus:
        self.La_IstPID_text = QLabel(f'{istwert_str[self.sprache]}-{sx_str[self.sprache]} ')
        self.La_IstPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_IstPID_text.setStyleSheet(f"color: {self.color[5]}")
        if self.color_Aktiv: self.La_IstPID_wert.setStyleSheet(f"color: {self.color[5]}")

        ### Knöpfe:
        #### Bewegung:
        self.icon_cw = "./vifcon/icons/p_cw.png"
        self.btn_cw  = QPushButton(QIcon(self.icon_cw), '')
        self.btn_cw.setFlat(True)
        self.btn_cw.clicked.connect(self.fahre_cw)

        self.icon_ccw = "./vifcon/icons/p_ccw.png"
        self.btn_ccw  = QPushButton(QIcon(QIcon(self.icon_ccw)), '')
        self.btn_ccw.setFlat(True)
        self.btn_ccw.clicked.connect(self.fahre_ccw)
        #### Stopp:
        icon_pfad = "./vifcon/icons/p_stopp.png" if sprache == 0 else  "./vifcon/icons/p_stopp_En.png" 
        self.btn_mitte = QPushButton(QIcon(icon_pfad), '')
        self.btn_mitte.setFlat(True)
        self.btn_mitte.clicked.connect(lambda: self.Stopp(2))
        #### Rezepte:
        self.btn_rezept_start =  QPushButton(rez_start_str[self.sprache])
        self.btn_rezept_start.clicked.connect(lambda: self.RezStart(1))

        self.btn_rezept_ende =  QPushButton(rez_ende_str[self.sprache])
        self.btn_rezept_ende.clicked.connect(lambda: self.Stopp(1))   
        #### Define Home:
        self.btn_DH = QPushButton(DH_str[self.sprache])
        self.btn_DH.clicked.connect(self.define_home)

        ### Combobox:
        self.cb_Rezept = QComboBox()
        self.cb_Rezept.addItem('------------')
        try:
            for rezept in self.rezept_config:
                self.cb_Rezept.addItem(rezept) 
        except Exception as e:
            self.Fehler_Output(1, self.La_error_1, self.err_21_str[self.sprache])
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

        self.btn_move_layout.addWidget(self.btn_cw)
        self.btn_move_layout.addWidget(self.btn_mitte)
        self.btn_move_layout.addWidget(self.btn_ccw)

        #### Rezept/Define Home:
        self.btn_group_Rezept = QWidget()
        self.btn_Rezept_layout = QVBoxLayout()
        self.btn_group_Rezept.setLayout(self.btn_Rezept_layout)
        self.btn_Rezept_layout.setSpacing(5)

        self.btn_Rezept_layout.addWidget(self.btn_DH)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_start)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_ende)
        self.btn_Rezept_layout.addWidget(self.cb_Rezept)

        self.btn_Rezept_layout.setContentsMargins(2,0,2,0)      # left, top, right, bottom

        #### First-Row:
        self.first_row_group  = QWidget()
        self.first_row_layout = QHBoxLayout()
        self.first_row_group.setLayout(self.first_row_layout)
        self.first_row_layout.setSpacing(20)

        self.first_row_layout.addWidget(self.La_name)
        self.first_row_layout.addWidget(self.Auswahl)
        self.first_row_layout.addWidget(self.gamepad)
        self.first_row_layout.addWidget(self.EndRot)
        self.first_row_layout.addWidget(self.PID_cb)

        self.first_row_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom

        #### Label-Werte:
        W_spalte = 80

        label_list      = [self.La_IstSpeed_text, self.La_SollSpeed_text, self.La_IstWin_text, self.La_IstPID_text, self.La_SollPID_text]
        label_unit_list = [self.La_IstSpeed_wert, self.La_SollSpeed_wert, self.La_IstWin_wert, self.La_IstPID_wert, self.La_SollPID_wert]
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
        self.layer_layout.addWidget(self.btn_group_move,                    3, 0, 1, 3, alignment=Qt.AlignLeft)                     # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung                     
        self.layer_layout.addWidget(self.La_Status,                         4, 0, 1, 6, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.LE_Speed,                          1, 1)   
        self.layer_layout.addWidget(self.La_error_1,                        1, 2,       alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.V,                                 1, 3, 3, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.btn_group_Rezept,                  1, 5, 3, 1, alignment=Qt.AlignTop)
        #________________________________________
        ## Größen (Size) - Widgets:
        ### Button-Icon:
        self.btn_cw.setIconSize(QSize(50, 50))
        self.btn_ccw.setIconSize(QSize(50, 50))
        self.btn_mitte.setIconSize(QSize(50, 50))

        ### Eingabefelder (Line Edit):
        self.LE_Speed.setFixedWidth(100)
        self.LE_Speed.setFixedHeight(25)

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
        if self.origin[0] == 'V':        PID_Label_Ist = PID_Von_2[sprache]
        elif self.origin[0] == 'M':     
            PID_Label_Ist = PID_Von_1[sprache]
            PID_Export_Ist = PID_Zusatz[sprache]
        else:                       PID_Label_Ist = PID_Von_2[sprache]
        ### Sollwert
        PID_Export_Soll = ''
        if self.origin[1] == 'V':        PID_Label_Soll = PID_Von_2[sprache]
        elif self.origin[1] == 'M':     
            PID_Label_Soll = PID_Von_1[sprache]
            PID_Export_Soll = PID_Zusatz[sprache]
        else:                       PID_Label_Soll = PID_Von_2[sprache]
        
        ## Kurven-Namen:
        kurv_dict = {                                                                       # Wert: [Achse, Farbe/Stift, Name]
            'IWv':      ['a2', pg.mkPen(self.color[0], width=2),                            f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'IWw':      ['a1', pg.mkPen(self.color[1], width=2),                            f'{nemoAchse} - {w_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWv':      ['a2', pg.mkPen(self.color[2]),                                     f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            'oGv':      ['a2', pg.mkPen(color=self.color[0], style=Qt.DashLine),            f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGv':      ['a2', pg.mkPen(color=self.color[0], style=Qt.DashDotDotLine),      f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGw':      ['a1', pg.mkPen(color=self.color[1], style=Qt.DashLine),            f'{nemoAchse} - {w_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGw':      ['a1', pg.mkPen(color=self.color[1], style=Qt.DashDotDotLine),      f'{nemoAchse} - {w_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'Rezv':     ['a2', pg.mkPen(color=self.color[3], width=3, style=Qt.DotLine),    f'{nemoAchse} - {rezept_Label_str[self.sprache]}<sub>{v_einzel_str[self.sprache]}</sub>'],
            'SWxPID':   ['a1', pg.mkPen(self.color[4], width=2, style=Qt.DashDotLine),      f'{PID_Label_Soll} - {x_einzel_str[self.sprache]}<sub>{PID_Export_Soll}{sollwert_str[self.sprache]}</sub>'], 
            'IWxPID':   ['a1', pg.mkPen(self.color[5], width=2, style=Qt.DashDotLine),      f'{PID_Label_Ist} - {x_einzel_str[self.sprache]}<sub>{PID_Export_Ist}{istwert_str[self.sprache]}</sub>'],
            'Rezx':     ['a1', pg.mkPen(color=self.color[6], width=3, style=Qt.DotLine),    f'{nemoAchse} - {rezept_Label_str[self.sprache]}<sub>{x_einzel_str[self.sprache]}</sub>'],
            'oGPID':    ['a1', pg.mkPen(color=self.color[5], style=Qt.DashLine),            f'{nemoAchse} - {self.PID_G_Kurve[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGPID':    ['a1', pg.mkPen(color=self.color[5], style=Qt.DashDotDotLine),      f'{nemoAchse} - {self.PID_G_Kurve[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
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
        self.winList        = []       
        self.speedList      = []   
        self.sollspeedList  = []  
        self.sollxPID       = []
        self.istxPID        = []
        ### Grenzen:
        self.VoGList        = []
        self.VuGList        = []
        self.WoGList        = []
        self.WuGList        = []
        self.XoGList        = []
        self.XuGList        = []

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.curveDict      = {'IWv': '', 'SWv': '', 'IWw':'', 'oGv': '', 'uGv': '', 'oGw': '', 'uGw': '', 'Rezv':'', 'SWxPID':'', 'IWxPID':'', 'Rezx': '', 'oGPID':'', 'uGPID':''}                                                                                             # Kurven
        for kurve in self.kurven_dict:
            self.curveDict[kurve] = self.kurven_dict[kurve]
        self.labelDict      = {'IWv': self.La_IstSpeed_wert,                'SWv': self.La_SollSpeed_wert,              'IWw':self.La_IstWin_wert,                  'SWxPID': self.La_SollPID_wert,                     'IWxPID': self.La_IstPID_wert}                          # Label
        self.labelUnitDict  = {'IWv': self.einheit_v_einzel[self.sprache],  'SWv': self.einheit_v_einzel[self.sprache], 'IWw':self.einheit_w_einzel[self.sprache],  'SWxPID': self.einheit_x_einzel[self.sprache],      'IWxPID': self.einheit_x_einzel[self.sprache]}          # Einheit
        self.listDict       = {'IWv': self.speedList,                       'SWv':self.sollspeedList,                   'IWw':self.winList,                         'SWxPID': self.sollxPID,                            'IWxPID': self.istxPID}                                 # Werteliste
        self.grenzListDict  = {'oGv': self.VoGList,                         'uGv': self.VuGList,                        'oGw': self.WoGList,                        'uGw': self.WuGList,                                'oGPID': self.XoGList, 'uGPID': self.XuGList}
        self.grenzValueDict = {'oGv': self.oGv,                             'uGv': self.uGv,                            'oGw': self.oGw,                            'uGw': self.uGw,                                    'oGPID': self.oGx,     'uGPID': self.uGx}

        ## Plot-Skalierungsfaktoren:
        self.skalFak_dict = {}
        for size in self.curveDict:
            if 'Ww' in size:
                self.skalFak_dict.update({size: self.skalFak['Win']})
            if 'Wv' in size:
                self.skalFak_dict.update({size: self.skalFak['WinSpeed']})
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
        checkbox = self.sender()                        # Klasse muss von QWidget erben, damit sender() Funktioniert - Durch die Methode kann geschaut werden welche Checkbox betätigt wurde!
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
            self.fahre_ccw()                                             # Minus
        else:
            self.fahre_cw()                                              # Plus

    def fahre_cw(self):
        '''Reaktion auf den Linken Knopf'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_49_str[self.sprache]}')
            self.Fehler_Output(0, self.La_error_1) 
            ans = self.controll_value()
            if not ans == '':
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = ans
                else:
                    self.write_value['Speed'] = ans
                self.write_task['CW'] = True
                self.write_task['Send'] = True
                if self.BTN_BW_grün:
                    self.btn_ccw.setIcon(QIcon(self.icon_ccw))
                    self.btn_cw.setIcon(QIcon(self.icon_cw.replace('.png', '_Ein.png')))
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def fahre_ccw(self):
        '''Reaktion auf den Rechten Knopf'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_50_str[self.sprache]}')
            self.Fehler_Output(0, self.La_error_1) 
            ans = self.controll_value()
            if not ans == '':
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = ans
                else:
                    self.write_value['Speed'] = ans
                self.write_task['CCW'] = True
                self.write_task['Send'] = True
                if self.BTN_BW_grün:
                    self.btn_cw.setIcon(QIcon(self.icon_cw))
                    self.btn_ccw.setIcon(QIcon(self.icon_ccw.replace('.png', '_Ein.png')))
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
                self.btn_ccw.setIcon(QIcon(self.icon_ccw))
                self.btn_cw.setIcon(QIcon(self.icon_cw))
            self.Fehler_Output(0, self.La_error_1) 
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def define_home(self):
        ''' Sorgt dafür das die aktuelle Position zur Null wird.'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_39_str[self.sprache]}')
            logger.info(f"{self.device_name} - {self.Log_Text_58_str[self.sprache]}")
            self.update_Limit(1)
            self.write_task['Define Home'] = True
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    ##########################################
    # Reaktion Checkbox:
    ##########################################    
    def Rotation_Nonstopp(self):                       
        if self.EndRot.isChecked():
            self.write_task['EndRot'] = True
        else:
            self.write_task['EndRot'] = False
            self.typ_widget.Message(f'{self.device_name} - {self.Pop_up_EndRot[self.sprache]}', 3, 500)

    def PID_ON_OFF(self):    
        '''PID-Modus toggeln'''                   
        if self.PID_cb.isChecked():
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_1[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID'] = True
            self.write_task['Send'] = False
            self.Stopp(6)
            # GUI ändern:
            self.La_SollSpeed.setText(self.x_str[self.sprache])
            if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: {self.color[4]}")
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
            self.write_task['Send'] = False  
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
            if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: {self.color[2]}")
            # Bei Multilog-Sollwert:
            if self.origin[1] == 'M':
                self.btn_rezept_start.setEnabled(True)
                self.btn_rezept_ende.setEnabled(True)
                self.cb_Rezept.setEnabled(True)
                self.LE_Speed.setEnabled(True)

    ##########################################
    # Eingabefeld Kontrolle:
    ##########################################
    def controll_value(self):
        ''' Kontrolliere die Eingabe eines Eingabefeldes.
        
        Return:
            '' (str):               Fehlerfall
            speed_value (float):    Geschwindigkeitswert
        '''

        # Eingebabefeld auslesen:
        speed_value = self.LE_Speed.text().replace(",", ".")
        speed_okay = False

        # Auswahl Limits Sollwert:
        if self.PID_cb.isChecked():
            oGv = self.oGx
            uGv = self.uGx 
            unit = self.einheit_x_einzel[self.sprache]
        else:
            oGv = self.oGv
            uGv = self.uGv
            unit = self.einheit_v_einzel[self.sprache]

        # Wenn eins der beiden Eingabefelder leer ist, dann sende nicht:
        if speed_value == '':
            self.Fehler_Output(1, self.La_error_1, self.err_1_str[self.sprache], self.Text_48_str[self.sprache])          
        else:  
            # Kontrolle Position:                                                                                                 
            try:
                # Umwandeln Position:
                speed_value = float(speed_value)
                # Kontrolliere die Grenzen/Limits:
                if speed_value < uGv or speed_value > oGv: 
                    self.Fehler_Output(1, self.La_error_1, f'{self.err_2_str[self.sprache]} {uGv} {self.err_3_str[self.sprache]} {oGv} {unit}', self.Text_42_str[self.sprache])                                                                 
                # Alles in Ordnung mit der Eingabe:
                else:                           
                    self.Fehler_Output(0, self.La_error_1)                                                               
                    speed_okay = True                                                           
            # Eingabe ist falsch:
            except:                    
                self.Fehler_Output(1, self.La_error_1, self.err_5_str[self.sprache], self.Text_43_str[self.sprache])                                                                                 

        # Alles Okay:
        if speed_okay:
            return abs(speed_value)
        # Rückgabe bei Fehler:
        return ''  
    
    ##########################################
    # Betrachtung der Labels und Plots:
    ##########################################
    def update_GUI(self, value_dict, x_value):
        ''' Update der GUI, Plot und Label!

        Args:
            value_dict (dict):  Dictionary mit den aktuellen Werten!
            x_value (list):     Werte für die x-Achse
        '''
                
        ### Kurven Update:
        self.data.update({'Time' : x_value[-1]})                  
        self.data.update(value_dict)   

        for messung in value_dict:
            if not 'Status' in messung:
                Leerzeichen = ''
                if 'SWv' in messung or 'IWv' in messung or 'SWx' in messung or 'IWx' in messung:
                    Leerzeichen = ' '
                # Label Veränderung im PID-Modus!
                self.labelDict[messung].setText(f'{value_dict[messung]}{Leerzeichen}{self.labelUnitDict[messung]}')
                self.listDict[messung].append(value_dict[messung])
                if not self.curveDict[messung] == '':
                    faktor = self.skalFak_dict[messung]
                    y = [a * faktor for a in self.listDict[messung]]
                    self.curveDict[messung].setData(x_value, y)   
            elif 'Status' in messung:
                logger.debug(f'{self.device_name} - {self.Log_Status_Int[self.sprache]} ({messung}): {value_dict[messung]}')

        # Grenz-Kurven:
        ## Update Grenzwert-Dictionary:
        self.grenzValueDict['oGv']      = self.oGv  * self.skalFak['WinSpeed']
        self.grenzValueDict['uGv']      = self.uGv  * self.skalFak['WinSpeed']
        self.grenzValueDict['oGw']      = self.oGw  * self.skalFak['Win']
        self.grenzValueDict['uGw']      = self.uGw  * self.skalFak['Win']
        self.grenzValueDict['oGPID']    = self.oGx  * self.skalFak['PIDA']
        self.grenzValueDict['uGPID']    = self.uGx  * self.skalFak['PIDA']
        ## Update-Kurven:
        for kurve in self.kurven_dict:
            if kurve in self.grenzListDict:
                self.grenzListDict[kurve].append(float(self.grenzValueDict[kurve]))
                self.kurven_dict[kurve].setData(x_value, self.grenzListDict[kurve]) 

        # Status-Meldung
        status_1 = value_dict['Status']                     
        status_1 = self.status_report_umwandlung(status_1)
        
        label_s1 = ''
        status = ['','','','','','','','','','','','','','','','']
        if self.Anlage == 1:
            status = [self.sta_Bit0_str[self.sprache], self.sta_Bit1_str[self.sprache], self.sta_Bit2_str[self.sprache], self.sta_Bit3_str[self.sprache], self.sta_Bit4_str[self.sprache], self.sta_Bit5_str[self.sprache], self.sta_Bit6_str[self.sprache], self.sta_Bit7_str[self.sprache], self.sta_Bit8_str[self.sprache], self.sta_Bit9_str[self.sprache], self.sta_Bit10_str[self.sprache], self.sta_Bit11_str[self.sprache], self.sta_Bit12_str[self.sprache], self.sta_Bit13_str[self.sprache], self.sta_Bit14_str[self.sprache], self.sta_Bit15_str[self.sprache]]
        elif self.Anlage == 2:
            status = [self.Stat_N2_Bit0[self.sprache], self.Stat_N2_Bit1[self.sprache], self.Stat_N2_Bit2[self.sprache], self.Stat_N2_Bit3[self.sprache], self.Stat_N2_Bit4[self.sprache], self.Stat_N2_Bit5[self.sprache], self.Stat_N2_Bit6[self.sprache], self.Stat_N2_Bit7[self.sprache], self.Stat_N2_Bit8[self.sprache], self.Stat_N2_Bit9[self.sprache], self.Stat_N2_Bit10[self.sprache], self.Stat_N2_Bit11[self.sprache], self.Stat_N2_Bit12[self.sprache], self.Stat_N2_Bit13[self.sprache], self.Stat_N2_Bit14[self.sprache], self.Stat_N2_Bit15[self.sprache]]

        l = len(status_1)
        for n in range(0,l):
            if status_1[n] == '1':
                if not status[n] == '':
                    label_s1 = label_s1 + f'{status[n]}, '
        if label_s1 == '':
            label_s1 = self.status_2_str[self.sprache]
        else:
            label_s1 = label_s1[:-2]
        self.La_Status.setText(f'{self.status_3_str[self.sprache]} {label_s1}')

    def status_report_umwandlung(self, StatusInteger):
        ''' Umwandlung des Status - Integer zu Umgedrehten Binärcode: \n
        Beispiel:   \n
                    512                 - StatusInteger (Args) \n
                    10 0000 0000        - Lower Byte, Higher Byte \n
                    0000 0000           - Higher Byte \n
                    0000 0010           - Lower Byte \n
                    0000 0000 0000 0010 - Gewollte Bit-Folge \n
                    0100 0000 0000 0000 - Umkehren um mit Liste zu Vergleichen 
        '''

        status = bin(StatusInteger)[2:]            # Status Integer in Binär-Code
        l = len(status)                            # Länge bestimmen

        anz = int(l/8)                             # Anzahl von vollen Byte auslesen

        # Bytes aus den String lesen:
        byte_list = []                             
        for n in range(0,anz):
            byte_list.append(status[-8:])
            status = status[0:-8]

        # Unvolständige Bytes Auffüllen und auf 8 Bit kürzen:
        if len(status) < 8 and not status == '':                             
            status = '0000000' + status
            byte_list.append(status[-8:])
        elif status == '' and len(byte_list) == 1:
            byte_list.append('00000000')

        if len(byte_list) == 1:
            byte_list.append('00000000')

        # Byte zusammensetzen in der richtigen Reihenfolge:
        byte_string = ''
        for n in byte_list:
            byte_string = byte_string + n

        return byte_string[::-1]   # [::-1] --> dreht String um! (Lowest Bit to Highest Bit)

    def BTN_Back(self, Text_Number):
        ''' Mit der Funktion wird ein Limit-Stopp bzw. das Erreichen der Limits in der GUI bemerkbar gemacht!
        Args:
            Text_Number (int):  Nummer des Fehler Textes!
        '''
        if Text_Number == 0:    self.Fehler_Output(1, self.La_error_1, self.Fehler_out_1[self.sprache])
        elif Text_Number == 1:  self.Fehler_Output(1, self.La_error_1, self.Fehler_out_2[self.sprache])
        elif Text_Number == 2:  self.Fehler_Output(1, self.La_error_1, f'{self.Fehler_out_3[self.sprache]}\n{self.Log_Text_249_str[self.sprache]}', f'{self.Log_Text_219_str[self.sprache]} ({self.Log_Text_249_str[self.sprache]})')
        elif Text_Number == 3:  self.Fehler_Output(1, self.La_error_1, f'{self.Fehler_out_3[self.sprache]}\n{self.Log_Text_250_str[self.sprache]}', f'{self.Log_Text_219_str[self.sprache]} ({self.Log_Text_250_str[self.sprache]})')                     
        if self.BTN_BW_grün:
            self.btn_cw.setIcon(QIcon(self.icon_cw))
            self.btn_ccw.setIcon(QIcon(self.icon_ccw))

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
            ### Winkel-Limit:
            try: self.oGw = config['devices'][self.device_name]["limits"]['maxWinkel']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxWinkel {self.Log_Pfad_conf_5[self.sprache]} 180')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGw = 180
            #//////////////////////////////////////////////////////////////////////
            try: self.uGw = config['devices'][self.device_name]["limits"]['minWinkel']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minWinkel {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGw = 0
            #//////////////////////////////////////////////////////////////////////
            if not type(self.oGw) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxWinkel - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 180 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGw)}')
                self.oGw = 180
            if not type(self.uGw) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minWinkel - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGw)}')
                self.uGw = 0
            if self.oGw <= self.uGw:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 180 ({self.Log_Pfad_conf_13[self.sprache]})')
                self.uGw = 0
                self.oGw = 180
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
            TT_v = f'{self.TTLimit[self.sprache]} {self.uGv} ... {self.oGv} {self.einheit_v_einzel[self.sprache]}'
            self.LE_Speed.setToolTip(TT_v)

            TT_PID = f'{self.TTLimit[self.sprache]} {self.uGx} ... {self.oGx} {self.einheit_x_einzel[self.sprache]}'
            self.PID_cb.setToolTip(TT_PID)

            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Weiterleiten:
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGv} {self.Log_Text_LB_4[self.sprache]} {self.oGv} {self.einheit_v_einzel[self.sprache]}')
            logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGw} {self.Log_Text_LB_4[self.sprache]} {self.oGw}{self.einheit_w_einzel[self.sprache]}')

            self.write_task['Update Limit']     = True
            self.write_value['Limits']          = [self.oGw, self.uGw, self.oGv, self.uGv, self.oGx, self.uGx]

            self.Fehler_Output(0, self.La_error_1)
        else:
            self.Fehler_Output(1, self.La_error_1, self.Log_Yaml_Error[self.sprache], self.Text_Update[self.sprache])

    def PID_Reset(self):
        ''' Löse den Reset des PID-Reglers aus!'''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Extra_1[self.sprache]}{self.Text_PIDReset_str[self.sprache]}')
        
        if not self.PID_cb.isChecked():
            ## Aufagben setzen:
            self.write_task['Update Limit']  = True
            self.write_value['Limits']       = [self.oGw, self.uGw, self.oGv, self.uGv, self.oGx, self.uGx]
            self.write_task['PID-Reset']     = True
            self.write_value['PID-Sollwert'] = 0

            ## Meldung:
            self.Fehler_Output(0, self.La_error_1)
        else:
            self.Fehler_Output(1, self.La_error_1, self.Text_PIDResetError[self.sprache], self.Text_PIDResetError[self.sprache])

    ##########################################
    # Reaktion auf Rezepte:
    ##########################################
    def RezStart(self, execute = 1):
        ''' Rezept wurde gestartet '''
        if self.init:
            if not self.Rezept_Aktiv:
                if execute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_87_str[self.sprache]}')
                elif execute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_85_str[self.sprache]}')
            
                # Variablen:                                   
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
                    logger.info(f'{self.device_name} - {self.Log_Text_40_str[self.sprache]} {self.rezept_daten} {self.rezept_datei}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_24_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}') 

                    # Erstes Element senden:
                    ## PID-Modus oder Normaler-Modus:
                    if self.PID_cb.isChecked():
                        self.write_value['PID-Sollwert'] = self.value_list[self.step]

                        if self.move_list[self.step] == 'CW':
                            self.write_task['CW'] = True
                            self.write_task['CCW'] = False
                            self.richtung_Rez = 'CW'
                        elif self.move_list[self.step] == 'CCW':
                            self.write_task['CCW'] = True
                            self.write_task['CW'] = False
                            self.richtung_Rez = 'CCW'
                    else:
                        self.write_value['Speed'] = abs(self.value_list[self.step]) 

                        if self.value_list[self.step] < 0:
                            self.write_task['CCW'] = True
                            self.write_task['CW'] = False
                            self.richtung_Rez = 'CCW'
                        else:
                            self.write_task['CW'] = True
                            self.write_task['CCW'] = False
                            self.richtung_Rez = 'CW'
                    ## Anzeige Betätigte Richtung:
                    if self.BTN_BW_grün and self.write_task['CW']:
                        self.btn_ccw.setIcon(QIcon(self.icon_ccw))
                        self.btn_cw.setIcon(QIcon(self.icon_cw.replace('.png', '_Ein.png')))
                    if self.BTN_BW_grün and self.write_task['CCW']:
                        self.btn_cw.setIcon(QIcon(self.icon_cw))
                        self.btn_ccw.setIcon(QIcon(self.icon_ccw.replace('.png', '_Ein.png')))
                    ## Bestätige Sende Wert:
                    self.write_task['Send'] = True

                    # Elemente GUI sperren:
                    self.cb_Rezept.setEnabled(False)
                    self.btn_rezept_start.setEnabled(False)
                    self.btn_cw.setEnabled(False)
                    self.btn_mitte.setEnabled(False)
                    self.btn_ccw.setEnabled(False)
                    self.EndRot.setEnabled(False)
                    self.btn_DH.setEnabled(False)
                    self.Auswahl.setEnabled(False)
                    self.PID_cb.setEnabled(False)

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
                self.btn_cw.setEnabled(True)
                self.btn_mitte.setEnabled(True)
                self.btn_ccw.setEnabled(True) 
                self.btn_DH.setEnabled(True)
                self.EndRot.setEnabled(True)
                self.btn_DH.setEnabled(True)
                self.Auswahl.setEnabled(True)
                if self.PID_Aktiv: self.PID_cb.setEnabled(True)

                # Variablen:
                self.Rezept_Aktiv = False

                # Nachricht:
                self.Fehler_Output(0, self.La_error_1)

                # Auto Range
                self.typ_widget.plot.AutoRange()

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

                if self.move_list[self.step] == 'CW':
                    self.write_task['CW'] = True
                    self.write_task['CCW'] = False
                    richtung = 'CW'
                elif self.move_list[self.step] == 'CCW':
                    self.write_task['CCW'] = True
                    self.write_task['CW'] = False
                    richtung = 'CCW'
            else:
                self.write_value['Speed'] = abs(self.value_list[self.step]) 

                if self.value_list[self.step] < 0:
                    self.write_task['CCW'] = True
                    self.write_task['CW'] = False
                    richtung = 'CCW'
                else:
                    self.write_task['CW'] = True
                    self.write_task['CCW'] = False
                    richtung = 'CW'
            ## Prio-Stopp bei Nemo-2-Anlage:
            if self.Anlage == 2 and not self.richtung_Rez == richtung:
                self.write_task['Prio-Stopp'] = True 
                logger.info(f'{self.device_name} - {self.Log_Text_PS_1[self.sprache]} {self.richtung_Rez} {self.Log_Text_PS_2[self.sprache]} {richtung}')
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PS_1[self.sprache]}')
                self.richtung_Rez = richtung
            ## Anzeige Betätigte Richtung:
            if self.BTN_BW_grün and self.write_task['CW']:
                self.btn_ccw.setIcon(QIcon(self.icon_ccw))
                self.btn_cw.setIcon(QIcon(self.icon_cw.replace('.png', '_Ein.png')))
            if self.BTN_BW_grün and self.write_task['CCW']:
                self.btn_cw.setIcon(QIcon(self.icon_cw))
                self.btn_ccw.setIcon(QIcon(self.icon_ccw.replace('.png', '_Ein.png')))
            ## Bestätige Sende Wert:
            self.write_task['Send'] = True
    
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

        ## Winkellimits:
        uGw = self.uGw
        oGw = self.oGw

        ## PID-Limits:
        if self.PID_cb.isChecked():
            oG = self.oGx
            uG = self.uGx 
            string_einheit = self.einheit_x_einzel[self.sprache]

        ## Aktueller Wert Geschwindigkeit:
        ak_value = self.ak_value['IWv'] if not self.ak_value == {} else 0

        # Rezept lesen:
        rezept = self.cb_Rezept.currentText() 
        pos_list = [] 
        try:
            start_pos = self.winList[-1]
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
                        if not werte[sNum].upper().strip() in ['CW', 'CCW']:  
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
                ## Kontrolle Geschwindigkeit oder PID-Input:
                if (value < uG or value > oG):
                    error = True
                    self.Fehler_Output(1, self.La_error_1, f'{self.err_6_str[self.sprache]} {value} {string_einheit} {self.err_7_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG} {string_einheit}! ({self.err_Rezept_2[self.sprache]} {n})') # Grenz-Fehler: {value}\nGrenzen: {uG} bis {oG}
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
            if not self.PID_cb.isChecked():
                ## Positionen bestimmen:
                value_step = 0
                for n_PosP in self.value_list:
                    pos_list.append(360/60 * n_PosP * self.time_list[value_step])
                    value_step += 1
                ## Kontrolle Winkel:
                logger.debug(f"{self.device_name} - {self.Log_Text_59_str[self.sprache]} {pos_list}")
                rezept_schritt = 1 
                for n in pos_list:
                    pos = start_pos + n
                    start_pos = pos
                    if (pos < uGw or pos > oGw) and not self.EndRot.isChecked():
                        error = True
                        self.Fehler_Output(1, self.La_error_1, f'{self.err_9_str[self.sprache]} {rezept_schritt} {self.err_7_str[self.sprache]} {uGw} {self.err_3_str[self.sprache]} {oGw}{self.einheit_w_einzel[self.sprache]}!')
                        break
                    else:
                        self.Fehler_Output(0, self.La_error_1)
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
            if not self.PID_cb.isChecked(): faktor = self.skalFak['WinSpeed']
            else:                           faktor = self.skalFak['PIDA']
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
            # Grenzen Updaten:
            with open(self.config_dat, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"{self.Log_Text_58_str[self.sprache]} {config}")
            
            # Konfigurations-Kontrolle und Auslesen:
            try: self.oGw = config['devices'][self.device_name]["limits"]['maxWinkel']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxWinkel {self.Log_Pfad_conf_5[self.sprache]} 180')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGw = 180
            try: self.uGw = config['devices'][self.device_name]["limits"]['minWinkel']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minWinkel {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGw = 0
            if not type(self.oGw) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGw)}')
                self.oGw = 180
            if not type(self.uGw) in [float, int]:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minSpeed - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} -1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGw)}')
                self.uGw = 0
            if self.oGw <= self.uGw:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 180 ({self.Log_Pfad_conf_13[self.sprache]})')
                self.uGw = 180
                self.oGw = 0

'''