# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo Generator Widget:
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
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,

)
from PyQt5.QtGui import (
    QIcon, 

)
from PyQt5.QtCore import (
    Qt,
    QTimer,
    QSize,
    pyqtSignal,

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

class NemoGeneratortWidget(QWidget):
    signal_Pop_up       = pyqtSignal()

    def __init__(self, sprache, Frame_Anzeige, widget, line_color, config, config_dat, neustart, multilog_aktiv, add_Ablauf_function, nemoGenerator = 'Nemo-Generator', typ = 'Generator', parent=None):
        """GUI widget of Nemo generator.

        Args:
            sprache (int):                      Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):               Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (Objekt):                    Element in das, das Widget eingefügt wird
            line_color (list):                  Liste mit Farben
            config (dict):                      Konfigurationsdaten aus der YAML-Datei
            config_dat (string):                Datei-Name der Config-Datei
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            multilog_aktiv (bool):              Multilog-Read/Send Aktiviert
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            nemoGenerator (str):                Name des Gerätes
            typ (str):                          Typ des Gerätes
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
        self.device_name                = nemoGenerator
        self.typ                        = typ

        ## Signal:
        self.signal_Pop_up.connect(self.Pop_Up_Start_Later)

        ## GUI:
        self.color_Aktiv = self.typ_widget.color_On

        ## Faktoren Skalierung:
        self.skalFak = self.typ_widget.Faktor

        ## Aktuelle Messwerte:
        self.ak_value = {}

        ## Weitere:
        self.Rezept_Aktiv   = False
        self.data           = {}
        self.start_later    = False
        self.Generator_Ein  = False

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
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                      'Reason for error:']
        self.Log_Pfad_conf_7    = ['Bitte vor Nutzung Korrigieren und Config Neu Einlesen!',                                                            'Please correct and re-read config before use!']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                              'Incorrect input:']
        self.Log_Pfad_conf_8_1  = ['Fehlerhafte Typ:',                                                                                                  'Incorrect type:']
        self.Log_Pfad_conf_9    = ['Die Obergrenze ist kleiner als die Untergrenze! Setze die Limits auf Default:',                                     'The upper limit is smaller than the lower limit! Set the limits to default:']
        self.Log_Pfad_conf_10   = ['zu',                                                                                                                'to']
        self.Log_Pfad_conf_11   = ['Strom',                                                                                                             'Current']
        self.Log_Pfad_conf_12   = ['PID-Eingang Istwert',                                                                                               'PID input actual value']
        self.Log_Pfad_conf_13   = ['Spannung',                                                                                                          'Voltage']
        self.Log_Pfad_conf_14   = ['Konfiguration mit VM, MV oder MM ist so nicht möglich, da der Multilog-Link abgeschaltet ist! Setze Default VV!',   'Configuration with VM, MV or MM is not possible because the Multilog-Link is disabled! Set default VV!']
        self.Log_Pfad_conf_15   = ['Leistung',                                                                                                          'Power']
        self.Log_Pfad_conf_NGe1 = ['Konfiguration start|start_modus wird auf Default I gesetzt!!',                                                      'Configuration start|start_modus is set to Default I!!']

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Übergeordnet:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Anlage = self.config['nemo-Version']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} nemo-Version {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Anlage = 1
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Zum Start:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.init = self.config['start']['init']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.init = False
        #//////////////////////////////////////////////////////////////////////
        try: self.stMode = self.config['start']['start_modus'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|start_modus {self.Log_Pfad_conf_5[self.sprache]} P')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.stMode = 'I'
        #//////////////////////////////////////////////////////////////////////
        try: self.Auswahl_PUI = self.config['start']['Auswahl'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|Auswahl {self.Log_Pfad_conf_5[self.sprache]} I')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_NGe1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.stMode = 'I'
            self.Auswahl_PUI = 'I'
        #//////////////////////////////////////////////////////////////////////
        try: self.messZeit = self.config['start']["readTime"]
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|readTime {self.Log_Pfad_conf_5[self.sprache]} 2')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.messZeit = 2 
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Limits:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #### Sollleistung:
        try: self.oGP = self.config["limits"]['maxP']  
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxP {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGP = 1
        #//////////////////////////////////////////////////////////////////////      
        try: self.uGP = self.config["limits"]['minP']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minP {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGP = 0
        #### Sollstrom:
        try: self.oGI = self.config["limits"]['maxI']   
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxI {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGI = 1
        #//////////////////////////////////////////////////////////////////////     
        try: self.uGI = self.config["limits"]['minI']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minI {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGI = 0
        #### Sollspannung:
        try: self.oGU = self.config["limits"]['maxU']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxU {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGU = 1        
        #//////////////////////////////////////////////////////////////////////
        try: self.uGU = self.config["limits"]['minU']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minU {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGU = 0
        #### PID:
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
        ### Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.startP = float(str(self.config["defaults"]['startPow']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} defaults|startPow {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startP = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.startI = float(str(self.config["defaults"]['startCurrent']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} defaults|startCurrent {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startI = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.startU = float(str(self.config["defaults"]['startVoltage']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} defaults|startVoltage {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startU = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### GUI:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            self.legenden_inhalt = self.config['GUI']['legend'].split(';')
            self.legenden_inhalt = [a.strip() for a in self.legenden_inhalt]    # sollten Unnötige Leerzeichen vorhanden sein, so werden diese entfernt!
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} GUI|legend {self.Log_Pfad_conf_5[self.sprache]} [IWP, IWU, IWI]')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.legenden_inhalt = ['IWP', 'IWU', 'IWI']
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Rezepte:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.rezept_config = self.config["rezepte"]
        except Exception as e: 
            self.rezept_config = {'rezept_Default':  {'n1': '10 ; 0 ; s'}}
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} rezepte {self.Log_Pfad_conf_5[self.sprache]} {self.rezept_config}')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID-Modus:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.unit_PIDIn  = self.config['PID']['Input_Size_unit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Size_unit {self.Log_Pfad_conf_5[self.sprache]} mm')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.unit_PIDIn = 'mm'
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Aktiv = self.config['PID']['PID_Aktiv']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|PID_Aktiv {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Aktiv = 0 
        #//////////////////////////////////////////////////////////////////////
        try: self.origin    = self.config['PID']['Value_Origin'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Value_Origin {self.Log_Pfad_conf_5[self.sprache]} VV')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.origin = 'VV'  
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Mode_Switch_Value_P = float(str(self.config['PID']['umstell_wert_P']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|umstell_wert_P {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Mode_Switch_Value_P = 0  
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Mode_Switch_Value_I = float(str(self.config['PID']['umstell_wert_I']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|umstell_wert_I {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Mode_Switch_Value_I = 0  
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Mode_Switch_Value_U = float(str(self.config['PID']['umstell_wert_U']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|umstell_wert_U {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Mode_Switch_Value_U = 0
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
        ### Anlagenbezeichnung:
        if not self.Anlage in [2]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nemo-Version - {self.Log_Pfad_conf_2[self.sprache]} [2] - {self.Log_Pfad_conf_3[self.sprache]} 2')
            self.Anlage = 2
        ### PID-Aktiv:
        if not type(self.PID_Aktiv) == bool and not self.PID_Aktiv in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Aktiv - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Aktiv}')
            self.PID_Aktiv = 0
        ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0
        ### Start-Modus:
        if not self.stMode in ['P', 'I', 'U']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_modus - {self.Log_Pfad_conf_2[self.sprache]} [P, I, U] - {self.Log_Pfad_conf_3[self.sprache]} I - {self.Log_Pfad_conf_8[self.sprache]} {self.stMode}')
            self.stMode = 'I'
        ### Auswahl:
        if not self.Auswahl_PUI in ['I', 'PUI']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Auswahl - {self.Log_Pfad_conf_2[self.sprache]} [PUI, I] - {self.Log_Pfad_conf_3[self.sprache]} I - {self.Log_Pfad_conf_8[self.sprache]} {self.Auswahl_PUI}')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_NGe1[self.sprache]}')
            self.stMode = 'I'
            self.Auswahl_PUI = 'I'
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
        ### Leistungs-Limit:
        if not type(self.oGP) in [float, int] or not self.oGP >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGP)}')
            self.oGP = 1
        if not type(self.uGP) in [float, int] or not self.oGP >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGP)}')
            self.uGP = 0
        if self.oGP <= self.uGP:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_15[self.sprache]})')
            self.uGP = 0
            self.oGP = 1
        ### Strom-Limit:
        if not type(self.oGI) in [float, int] or not self.oGI >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGI)}')
            self.oGI = 1
        if not type(self.uGI) in [float, int] or not self.oGI >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGI)}')
            self.uGI = 0
        if self.oGI <= self.uGI:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_11[self.sprache]})')
            self.uGI = 0
            self.oGI = 1
        ### Spannung-Limit:
        if not type(self.oGU) in [float, int] or not self.oGU >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGU)}')
            self.oGU = 1
        if not type(self.uGU) in [float, int] or not self.oGU >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGU)}')
            self.uGU = 0
        if self.oGU <= self.uGU:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
            self.uGU = 0
            self.oGU = 1
        ### Messzeit:
        if not type(self.messZeit) in [int, float] or not self.messZeit >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} readTime - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 2 - {self.Log_Pfad_conf_8[self.sprache]} {self.messZeit}')
            self.messZeit = 2
        ### Start-Leistung:
        if not type(self.startP) in [float, int] or not self.startP >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startPow - {self.Log_Pfad_conf_2[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.startP}')
            self.startP = 0
        ### Start-Strom:
        if not type(self.startI) in [float, int] or not self.startI >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startCurrent - {self.Log_Pfad_conf_2[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.startI}')
            self.startI = 0
        ### Start-Spannung:
        if not type(self.startU) in [float, int] or not self.startU >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startVoltage - {self.Log_Pfad_conf_2[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.startU}')
            self.startU = 0
        ### PID-Herkunft:
        if not type(self.origin) == str or not self.origin in ['MM', 'MV', 'VV', 'VM']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Value_Origin - {self.Log_Pfad_conf_2[self.sprache]} [VV, MM, VM, MV] - {self.Log_Pfad_conf_3[self.sprache]} VV - {self.Log_Pfad_conf_8[self.sprache]} {self.origin}')
            self.origin = 'VV'
        if not self.multilog_OnOff and self.origin in ['MM', 'MV', 'VM']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_14[self.sprache]}')
            self.origin = 'VV'
        ### PID-Umschaltwert Leistung:
        if not type(self.PID_Mode_Switch_Value_P) in [float, int] or not self.PID_Mode_Switch_Value_P >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} umstell_wert_P - {self.Log_Pfad_conf_2[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Mode_Switch_Value_P}')
            self.PID_Mode_Switch_Value_P = 0
        ### PID-Umschaltwert Strom:
        if not type(self.PID_Mode_Switch_Value_I) in [float, int] or not self.PID_Mode_Switch_Value_I >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} umstell_wert_I - {self.Log_Pfad_conf_2[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Mode_Switch_Value_I}')
            self.PID_Mode_Switch_Value_I = 0
        ### PID-Umschaltwert Spannung:
        if not type(self.PID_Mode_Switch_Value_U) in [float, int] or not self.PID_Mode_Switch_Value_U >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} umstell_wert_U - {self.Log_Pfad_conf_2[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Mode_Switch_Value_U}')
            self.PID_Mode_Switch_Value_U = 0
        
        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Werte: ##################################################################################################################################################################################################################################################################################
        self.sollwert_str       = ['Soll',                                                                                                      'Set']
        istwert_str             = ['Ist',                                                                                                       'Is']
        ## Knöpfe: #################################################################################################################################################################################################################################################################################                                                             
        send_str                = ['Sende',                                                                                                     'Send']
        rez_start_str           = ['Rezept Start',                                                                                              'Start recipe']
        rez_ende_str            = ['Rezept Beenden',                                                                                            'Finish recipe']
        ## Checkbox: ###############################################################################################################################################################################################################################################################################    
        cb_sync_str             = ['Sync',                                                                                                      'Sync']
        cb_PID                  = ['PID',                                                                                                       'PID']
        ## ToolTip: ###############################################################################################################################################################################################################################################################################                                                                                                   
        self.TTLimit            = ['Limit-',                                                                                                    'Limit-']
        self.TTSize_1           = ['Input-',                                                                                                    'Input-']
        self.TTSize_2           = ['Output-',                                                                                                   'Output-']
        self.TTSize_3           = ['Parameter:',                                                                                                'Parameter:']
        self.TTSize_x           = ['x:',                                                                                                        'x:']
        self.TTSize_I           = ['I:',                                                                                                        'I:']
        self.TTSize_U           = ['U:',                                                                                                        'U:']
        self.TTSize_P           = ['P:',                                                                                                        'P:']
        self.TTSize_kp          = ['kp =',                                                                                                      'kp =']
        self.TTSize_ki          = ['ki =',                                                                                                      'ki =']
        self.TTSize_kd          = ['kd =',                                                                                                      'kd =']
        self.TTName             = ['Typ:',                                                                                                      'Typ:']
        self.TTSKombi           = ['Schnittstellen Kombination:',                                                                               'Interface Combination:']
        self.TTTM               = ['TM',                                                                                                        'TM']
        ## Einheiten mit Größe: ####################################################################################################################################################################################################################################################################
        self.P_str              = ['P in kW:',                                                                                                  'P in kW:']
        self.U_str              = ['U in V:',                                                                                                   'U in V:']
        self.I_str              = ['I in A:',                                                                                                   'I in A:']
        self.x_str              = [f'x in {self.unit_PIDIn}:',                                                                                  f'x in {self.unit_PIDIn}:']
        sP_str                  = ['P:',                                                                                                        'P:']
        sU_str                  = ['U:',                                                                                                        'U:']
        sI_str                  = ['I:',                                                                                                        'I:']
        sf_str                  = ['f:',                                                                                                        'f:']
        self.sx_str             = ['PID:',                                                                                                      'PID:']
        st_P_str                = ['XXX.XX kW',                                                                                                 'XXX.XX kW']
        st_U_str                = ['XXX.XX V',                                                                                                  'XXX.XX V']
        st_I_str                = ['XXX.XX A',                                                                                                  'XXX.XX A']
        st_f_str                = ['XXX.XX Hz',                                                                                                 'XXX.XX Hz']
        st_x_str                = [f'XXX.XX {self.unit_PIDIn}',                                                                                 f'XXX.XX {self.unit_PIDIn}'] 
        st_Wsoll_str            = ['(XXX.XX)',                                                                                                  '(XXX.XX)']
        I_einzel_str            = ['I',                                                                                                         'I']
        U_einzel_str            = ['U',                                                                                                         'U']
        f_einzel_str            = ['f',                                                                                                         'f']
        P_einzel_str            = ['P',                                                                                                         'P']
        x_einzel_str            = ['x',                                                                                                         'x']
        self.einheit_I_einzel   = ['A',                                                                                                         'A']
        self.einheit_U_einzel   = ['V',                                                                                                         'V']
        self.einheit_P_einzel   = ['kW',                                                                                                        'kW']
        self.einheit_f_einzel   = ['Hz',                                                                                                        'Hz']
        self.einheit_x_einzel   = [f'{self.unit_PIDIn}',                                                                                        f'{self.unit_PIDIn}']
        PID_Von_1               = ['Wert von Multilog',                                                                                         'Value of Multilog']
        PID_Von_2               = ['Wert von VIFCON',                                                                                           'Value ofVIFCON']
        PID_Zusatz              = ['ex,',                                                                                                       'ex,']
        self.PID_Out            = ['PID-Out.',                                                                                                  'PID-Out.']
        self.PID_Out_P          = ['(P):',                                                                                                      '(P):']
        self.PID_Out_I          = ['(I):',                                                                                                      '(I):']
        self.PID_Out_U          = ['(U):',                                                                                                      '(U):']
        self.PID_G_Kurve        = ['PID-x',                                                                                                     'PID-x']
        ## Fehlermeldungen: #######################################################################################################################################################################################################################################################################  
        self.err_0_str          = ['Fehler!',                                                                                                   'Error!']                  
        self.err_1_str          = ['Keine Eingabe!',                                                                                            'No input!']
        self.err_2_str          = ['Grenzen überschritten!\nGrenzen von',                                                                       'Limits exceeded!\nLimits from']
        self.err_3_str          = ['bis',                                                                                                       'to']
        self.err_4_str          = ['Gerät anschließen und\nInitialisieren!',                                                                    'Connect the device\nand initialize!']
        self.err_5_str          = ['Fehlerhafte Eingabe!',                                                                                      'Incorrect input!']
        self.err_6_str          = ['Der Wert',                                                                                                  'The value']
        self.err_7_str          = ['überschreitet\ndie Grenzen von',                                                                            'exceeds\nthe limits of']
        self.err_10_str         = ['Rezept Einlesefehler!',                                                                                     'Recipe import error!']
        self.err_12_str         = ['Erster Schritt = Sprung!\nDa keine Messwerte!',                                                             'First step = jump! There\nare no measurements!']
        self.err_13_str         = ['o.K.',                                                                                                      'o.K.']   
        self.err_14_str         = ['Rezept läuft!\nRezept Einlesen gesperrt!',                                                                  'Recipe is running!\nReading recipes blocked!']
        self.err_15_str         = ['Wähle ein Rezept!',                                                                                         'Choose a recipe!']
        self.err_16_str         = ['Rezept läuft!\nRezept Start gesperrt!',                                                                     'Recipe running!\nRecipe start blocked!']
        self.err_21_str         = ['Fehler in der Rezept konfiguration\nder Config-Datei! Bitte beheben und Neueinlesen!',                      'Error in the recipe configuration of\nthe config file! Please fix and re-read!']
        self.err_Rezept         = ['Rezept Einlesefehler!\nUnbekanntes Segment:',                                                               'Recipe reading error!\nUnknown segment:']
        self.Log_Yaml_Error     = ['Mit der Config-Datei (Yaml) gibt es ein Problem.',                                                          'There is a problem with the config file (YAML).']
        self.err_RezDef_str     = ['Yaml-Config Fehler\nDefault-Rezept eingefügt!',                                                             'Yaml config error\nDefault recipe inserted!']
        self.err_Rezept_2       = ['Rezept-Schritt:',                                                                                                                                                                                       'Recipe step:']
        ## Status-N2: ##############################################################################################################################################################################################################################################################################          
        status_1_str            = ['Status: Inaktiv',                                                                                           'Status: Inactive']
        self.status_2_str       = ['Kein Status',                                                                                               'No Status']
        self.status_3_str       = ['Status:',                                                                                                   'Status:']
        self.Stat_N2_Bit0       = ['Generator Aktiv',                                                                                           'Generator Active']
        self.Stat_N2_Bit1       = ['Interlock',                                                                                                 'Interlock']   
        self.Stat_N2_Bit2       = ['externe Steuerung',                                                                                         'external control'] 
        self.Stat_N2_Bit3       = ['Fehler',                                                                                                    'Error'] 
        self.Stat_N2_Bit4       = ['Generator ist eingeschaltet',                                                                               'Generator is on'] 
        self.Stat_N2_Bit5       = ['Hochfrequenz ist eingeschaltet',                                                                            'High frequency is on'] 
        self.Stat_N2_Bit6       = ['',                                                                                                          ''] 
        self.Stat_N2_Bit7       = ['',                                                                                                          ''] 
        self.Stat_N2_Bit8       = ['P-Regelung gewählt',                                                                                        'P-control selected'] 
        self.Stat_N2_Bit9       = ['I-Regelung gewählt',                                                                                        'I-control selected'] 
        self.Stat_N2_Bit10      = ['U-Regelung gewählt',                                                                                        'U-control selected'] 
        self.Stat_N2_Bit11      = ['Anwahl Rampe',                                                                                              'ramp selection']  
        self.Stat_N2_Bit12      = ['',                                                                                                          '']  
        self.Stat_N2_Bit13      = ['',                                                                                                          '']  
        self.Stat_N2_Bit14      = ['Schnittstellenfehler',                                                                                      'Interface error']  
        self.Stat_N2_Bit15      = ['Test-Modus Aktiv',                                                                                          'Test Mode Active']
        ## Plot-Legende: ##########################################################################################################################################################################################################################################################################                                               
        rezept_Label_str        = ['Rezept',                                                                                                    'Recipe']
        ober_Grenze_str         = ['oG',                                                                                                        'uL']                                   # uL - upper Limit
        unter_Grenze_str        = ['uG',                                                                                                        'lL']                                   # lL - lower Limit
        Kurven_Device_M         = ['Gerät:',                                                                                                    'Device:']
        ## Logging: ###############################################################################################################################################################################################################################################################################
        self.Log_Text_1_str 	= ['Erstelle Widget.',                                                                                          'Create widget.']
        self.Log_Text_28_str    = ['Gerät wurde Gestartet/Initialisiert!',                                                                      'Device has been started/initialized!']
        self.Log_Text_29_str    = ['Gerät wurde nicht Initialisiert! Initialisierung durch Menü im späteren!',                                  'Device was not initialized! Initialization through menu later!']
        self.Log_Text_30_str    = ['Neustart Modus.',                                                                                           'Restart mode.']
        self.Log_Text_34_str    = ['Startmodus Leistung!',                                                                                      'Start mode power!']
        self.Log_Text_35_str    = ['Startmodus Spannung!',                                                                                      'Start mode voltage!']
        self.Log_Text_36_str    = ['Startmodus Strom!',                                                                                         'Start mode current!']
        self.Log_Text_37_str    = ['Startmodus Unbekannt!',                                                                                     'Start mode Unknown!']
        self.Log_Text_38_str    = ['Fehlerhafte Eingabe - Grund:',                                                                              'Incorrect input - Reason:']
        self.Log_Text_39_str    = ['Rezept:',                                                                                                   'Recipe:']
        self.Log_Text_40_str    = ['Rezept Inhalt:',                                                                                            'Recipe content:']
        self.Log_Text_205_str   = ['Update Konfiguration (Update Limits):',                                                                     'Update configuration (update limits):']
        self.Log_Text_PID_Ex    = ['Der Wert in der Konfig liegt außerhalb des Limit-Bereiches! Umschaltwert wird auf Minimum-Limit gesetzt!',  'The value in the config is outside the limit range! Switching value is set to minimum limit!']
        self.Log_Text_Ex1_str   = ['Fehler Grund (Rezept einlesen):',                                                                           'Error reason (reading recipe):']
        self.Log_Text_Ex2_str   = ['Fehler Grund (Problem mit Rezept-Konfiguration):',                                                          'Error reason (Problem with recipe configuration)']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                              'Limit range']
        self.Log_Text_LB_2      = ['Strom',                                                                                                     'Current']
        self.Log_Text_LB_3      = ['Spannung',                                                                                                  'Voltage']
        self.Log_Text_LB_3_1    = ['Leistung',                                                                                                  'Power']
        self.Log_Text_LB_4      = ['bis',                                                                                                       'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                               'after update']
        self.Log_Text_Kurve     = ['Kurvenbezeichnung existiert nicht:',                                                                        'Curve name does not exist:']
        self.Log_Text_NG_1_str  = ['Bei dem Generator sind alle drei Größen (PUI) auswählbar!',                                                 'All three sizes (PUI) are selectable in the generator!']
        self.Log_Text_NG_2_str  = ['Bei dem Generator ist nur der Strom nutzbar!',                                                              'With the generator only the electricity can be used!']
        self.Log_Text_NG_3_str  = ['Unbekannte Auswahl!',                                                                                       'Unknown selection!']
        self.Log_Status_Int     = ['Status-Integer',                                                                                            'Status-Integer']
        ## Ablaufdatei: ###########################################################################################################################################################################################################################################################################
        self.Text_13_str        = ['Auswahl Leistung senden.',                                                                                  'Send power selection.']
        self.Text_14_str        = ['Auswahl Spannung senden.',                                                                                  'Send voltage selection.']
        self.Text_15_str        = ['Auswahl Strom senden.',                                                                                     'Send current selection.']
        self.Text_16_str        = ['Knopf betätigt - Sende Sollleistung!',                                                                      'Button pressed - send target power!']
        self.Text_17_str        = ['Knopf betätigt - Sende Sollspannung!',                                                                      'Button pressed - send target voltage!']
        self.Text_18_str        = ['Knopf betätigt - Sende Sollstrom!',                                                                         'Button pressed - send target current!']
        self.Text_19_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da keine Eingabe.',                                       'Input field error message: Sending failed because there was no input.']
        self.Text_20_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da Eingabe die Grenzen überschreitet.',                   'Input field error message: Send failed because input exceeds limits.']
        self.Text_21_str        = ['Sende den Wert',                                                                                            'Send the value']
        self.Text_22_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da fehlerhafte Eingabe.',                                 'Input field error message: Sending failed due to incorrect input.']
        self.Text_23_str        = ['Knopf betätigt - Initialisierung!',                                                                         'Button pressed - initialization!']
        self.Text_24_str        = ['Ausführung des Rezeptes:',                                                                                  'Execution of the recipe:']
        self.Text_81_str        = ['Knopf betätigt - Beende Rezept',                                                                            'Button pressed - End recipe']
        self.Text_82_str        = ['Rezept ist zu Ende!',                                                                                       'Recipe is finished!']
        self.Text_83_str        = ['Stopp betätigt - Beende Rezept',                                                                            'Stop pressed - End recipe']
        self.Text_84_str        = ['Rezept läuft! Erneuter Start verhindert!',                                                                  'Recipe is running! Restart prevented!']
        self.Text_85_str        = ['Rezept Startet',                                                                                            'Recipe Starts']
        self.Text_86_str        = ['Rezept Beenden',                                                                                            'Recipe Ends']
        self.Text_87_str        = ['Knopf betätigt - Start Rezept',                                                                             'Button pressed - Start recipe']
        self.Text_88_str        = ['Rezept konnte aufgrund von Fehler nicht gestartet werden!',                                                 'Recipe could not be started due to an error!']
        self.Text_89_str        = ['Knopf betätigt - Beende Rezept - Keine Wirkung, da kein aktives Rezept!',                                   'Button pressed - End recipe - No effect because there is no active recipe!']
        self.Text_90_str        = ['Sicherer Endzustand wird hergestellt! Auslösung des Stopp-Knopfes!',                                        'Safe final state is established! Stop button is activated!']
        self.Text_91_str        = ['Rezept Beenden - Sicherer Endzustand',                                                                      'Recipe Ends - Safe End State']
        self.Text_PID_1         = ['Wechsel in PID-Modus.',                                                                                     'Switch to PID mode.']
        self.Text_PID_2         = ['Wechsel in Nemo-Generator-Regel-Modus.',                                                                    'Switch to Nemo-Generator control mode.']
        self.Text_PID_3         = ['Moduswechsel! Auslösung des Stopp-Knopfes aus Sicherheitsgründen!',                                         'Mode change! Stop button triggered for safety reasons!']
        self.Text_PID_4         = ['Rezept Beenden! Wechsel des Modus!',                                                                        'End recipe! Change mode!']
        self.Text_Update        = ['Update Fehlgeschlagen!',                                                                                    'Update Failed!']
        self.Text_Update_2      = ['Rezept neu einlesen Fehlgeschlagen!',                                                                       'Reload recipe failed!']
        self.Text_Neu_1         = ['Knopf betätigt - Generator Ein!',                                                                           'Button pressed - generator on!']
        self.Text_Neu_2         = ['Knopf betätigt - Generator Aus!',                                                                           'Button pressed - generator off!']
        self.Text_PIDReset_str  = ['PID Reset ausgelöst',                                                                                       'PID reset triggered']
        self.Text_LimitUpdate   = ['Limit Update ausgelöst',                                                                                    'limit update triggered']
        self.Text_Extra_1       = ['Menü-Knopf betätigt - ',                                                                                    'Menu button pressed - ']
        self.Text_PIDResetError = ['Der PID ist aktiv in Nutzung und kann nicht resettet werden!',                                              'The PID is actively in use and cannot be reset!']
        ## Message-Box: ###########################################################################################################################################################################################################################################################################
        self.Message_1          = ['Beachten Sie die Einstellungen des gewählten Generators! Diese werden als Tooltip beim Namen angezeigt und können in der Anlagen-GUI eingestellt werden!\n\nBei Änderung wird ein Neustart empfohlen!',   
                                   'Note the settings of the selected generator! These are displayed as a tooltip next to the name and can be set in the system GUI!\n\nIf changes are made, a restart is recommended!']

        #---------------------------------------
        # Konfigurationen für das Senden:
        #---------------------------------------
        self.write_task  = {'Soll-Leistung': False, 'Soll-Strom': False, 'Soll-Spannung': False, 'Init':False, 'Start': False, 'Ein': False, 'Aus': False, 'Update Limit': False, 'PID': False, 'Wahl_P': False, 'Wahl_I': False, 'Wahl_U': False, 'PID-Reset': False}
        self.write_value = {'Sollwert': 0, 'Limits': [0, 0, 0, 0, False], 'PID-Sollwert': 0, 'Limit Unit': self.einheit_I_einzel[self.sprache], 'PID Output-Size': 'I', 'Ak_Size': 'I'} # Limits: oGWahl, uGWahl, oGx, uGx, Input Update True?

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
        logger.info(f"{self.device_name} - {self.Log_Text_34_str[self.sprache]}") if self.stMode == 'P' else (logger.info(f"{self.device_name} - {self.Log_Text_35_str[self.sprache]}") if self.stMode == 'U' else (logger.info(f"{self.device_name} - {self.Log_Text_36_str[self.sprache]}") if self.stMode == 'I' else logger.info(f"{self.device_name} - {self.Log_Text_37_str[self.sprache]}"))) 
        logger.info(f"{self.device_name} - {self.Log_Text_NG_2_str[self.sprache]}") if self.Auswahl_PUI == 'I' else (logger.info(f"{self.device_name} - {self.Log_Text_NG_1_str[self.sprache]}") if self.Auswahl_PUI == 'PUI' else logger.info(f"{self.device_name} - {self.Log_Text_37_str[self.sprache]}")) 
        self.start_later = True
        ## Limit-Bereiche:
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]}: {self.uGI} {self.Log_Text_LB_4[self.sprache]} {self.oGI} {self.einheit_I_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]}: {self.uGU} {self.Log_Text_LB_4[self.sprache]} {self.oGU} {self.einheit_U_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3_1[self.sprache]}: {self.uGP} {self.Log_Text_LB_4[self.sprache]} {self.oGP} {self.einheit_P_einzel[self.sprache]}')
        
        #---------------------------------------    
        # GUI:
        #---------------------------------------
        ## Grundgerüst:
        self.layer_widget = QWidget()
        self.layer_layout = QGridLayout()
        self.layer_widget.setLayout(self.layer_layout)
        self.typ_widget.splitter_main.splitter.addWidget(self.layer_widget)
        #logger.info(f"{self.device_name} - {self.Log_Text_1_str[self.sprache]}")
        #________________________________________
        ## Kompakteres Darstellen:
        ### Grid Size - bei Verschieben der Splitter zusammenhängend darstellen:
        self.layer_layout.setRowStretch(7, 1) 
        self.layer_layout.setColumnStretch(6, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)       
        self.layer_layout.setVerticalSpacing(5)

        ### Zeilenhöhen:
        self.layer_layout.setRowMinimumHeight(4, 40)    # Error-Nachricht

        ### Spaltenbreiten:
        self.layer_layout.setColumnMinimumWidth(0, 120)
        self.layer_layout.setColumnMinimumWidth(1, 150)
        self.layer_layout.setColumnMinimumWidth(3, 160)

        #________________________________________
        ## Widgets:
        ### Eingabefelder:
        self.LE_Pow = QLineEdit()
        self.LE_Pow.setText(str(self.startP))
        TT_P = f'{self.TTLimit[self.sprache]}{self.TTSize_P[self.sprache]}  {self.uGP} ... {self.oGP} {self.einheit_P_einzel[self.sprache]}'
        self.LE_Pow.setToolTip(TT_P)

        self.LE_Voltage = QLineEdit()
        self.LE_Voltage.setText(str(self.startU))
        TT_U = f'{self.TTLimit[self.sprache]}{self.TTSize_U[self.sprache]}  {self.uGU} ... {self.oGU} {self.einheit_U_einzel[self.sprache]}'
        self.LE_Voltage.setToolTip(TT_U)

        self.LE_Current = QLineEdit()
        self.LE_Current.setText(str(self.startI))
        TT_I = f'{self.TTLimit[self.sprache]}{self.TTSize_I[self.sprache]}  {self.uGP} ... {self.oGI} {self.einheit_I_einzel[self.sprache]}'
        self.LE_Current.setToolTip(TT_I)

        ### Checkbox:
        self.Auswahl = QCheckBox(cb_sync_str[self.sprache])

        self.PID_cb  = QCheckBox(cb_PID[self.sprache])
        self.PID_cb.clicked.connect(self.PID_ON_OFF)
        if not self.PID_Aktiv:
            self.PID_cb.setEnabled(False)
        
        self.TT_PID_In   = f'{self.TTSize_1[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_x[self.sprache]} {self.uGx} ... {self.oGx} {self.einheit_x_einzel[self.sprache]}'
        if self.stMode == 'P':    self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_P[self.sprache]} {self.uGP} ... {self.oGP} {self.einheit_P_einzel[self.sprache]}'
        elif self.stMode == 'I':  self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_I[self.sprache]} {self.uGI} ... {self.oGI} {self.einheit_I_einzel[self.sprache]}'
        elif self.stMode == 'U':  self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_U[self.sprache]} {self.uGU} ... {self.oGU} {self.einheit_U_einzel[self.sprache]}'
        self.TT_PID_Para = f'{self.TTSize_3[self.sprache]} {self.TTSize_kp[self.sprache]} {kp_conf}; {self.TTSize_ki[self.sprache]} {ki_conf}; {self.TTSize_kd[self.sprache]} {kd_conf}'
        self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')
        
        ### Radiobutton:
        self.RB_choise_Pow = QRadioButton(f'{self.sollwert_str[self.sprache]}-{self.P_str[self.sprache]} ')
        if self.color_Aktiv: self.RB_choise_Pow.setStyleSheet(f"color: {self.color[0]}")
        self.RB_choise_Pow.clicked.connect(self.BlassOutUI)

        self.RB_choise_Voltage = QRadioButton(f'{self.sollwert_str[self.sprache]}-{self.U_str[self.sprache]} ')
        if self.color_Aktiv: self.RB_choise_Voltage.setStyleSheet(f"color: {self.color[1]}")
        self.RB_choise_Voltage.clicked.connect(self.BlassOutPI)

        self.RB_choise_Current = QRadioButton(f'{self.sollwert_str[self.sprache]}-{self.I_str[self.sprache]} ')
        if self.color_Aktiv: self.RB_choise_Current.setStyleSheet(f"color: {self.color[2]}")
        self.RB_choise_Current.clicked.connect(self.BlassOutPU)

        ### Start-Modus:
        if self.Auswahl_PUI == 'I':
            self.stMode = 'I'
            self.RB_choise_Voltage.setEnabled(False)
            self.RB_choise_Pow.setEnabled(False)

        if self.init: 
            self.Start()

        ### Label:
        #### Geräte-Titel:
        self.La_name = QLabel(f'<b>{nemoGenerator}</b>')
        self.La_name.setToolTip(f'{self.TTName[self.sprache]} ... (...)\n{self.TTSKombi[self.sprache]} ...')
        #### Istleistung:
        self.La_IstPow_text = QLabel(f'{istwert_str[self.sprache]}-{sP_str[self.sprache]} ')
        self.La_IstPow_wert = QLabel(st_P_str[self.sprache])
        if self.color_Aktiv: self.La_IstPow_text.setStyleSheet(f"color: {self.color[3]}")
        if self.color_Aktiv: self.La_IstPow_wert.setStyleSheet(f"color: {self.color[3]}")
        #### Istspannung:
        self.La_IstVoltage_text = QLabel(f'{istwert_str[self.sprache]}-{sU_str[self.sprache]} ')
        self.La_IstVoltage_wert = QLabel(st_U_str[self.sprache])
        if self.color_Aktiv: self.La_IstVoltage_text.setStyleSheet(f"color: {self.color[4]}")
        if self.color_Aktiv: self.La_IstVoltage_wert.setStyleSheet(f"color: {self.color[4]}")
        #### Iststrom:
        self.La_IstCurrent_text = QLabel(f'{istwert_str[self.sprache]}-{sI_str[self.sprache]} ')
        self.La_IstCurrent_wert = QLabel(st_I_str[self.sprache])
        if self.color_Aktiv: self.La_IstCurrent_text.setStyleSheet(f"color: {self.color[5]}")
        if self.color_Aktiv: self.La_IstCurrent_wert.setStyleSheet(f"color: {self.color[5]}")
        #### Istfrequenz:
        self.La_IstFre_text = QLabel(f'{istwert_str[self.sprache]}-{sf_str[self.sprache]} ')
        self.La_IstFre_wert = QLabel(st_f_str[self.sprache])
        if self.color_Aktiv: self.La_IstFre_text.setStyleSheet(f"color: {self.color[6]}")
        if self.color_Aktiv: self.La_IstFre_wert.setStyleSheet(f"color: {self.color[6]}")
        #### Fehlernachrichten:
        self.La_error = QLabel(self.err_13_str[self.sprache])
        #### Soll-Größe PID-Modus:
        self.La_SollPID_text = QLabel(f'{self.sollwert_str[self.sprache]}-{self.sx_str[self.sprache]} ')
        self.La_SollPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_SollPID_text.setStyleSheet(f"color: {self.color[10]}")
        if self.color_Aktiv: self.La_SollPID_wert.setStyleSheet(f"color: {self.color[10]}")
        #### Ist-Größe PID-Modus:
        self.La_IstPID_text = QLabel(f'{istwert_str[self.sprache]}-{self.sx_str[self.sprache]} ')
        self.La_IstPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_IstPID_text.setStyleSheet(f"color: {self.color[11]}")
        if self.color_Aktiv: self.La_IstPID_wert.setStyleSheet(f"color: {self.color[11]}")
        #### Soll-Größen:
        self.La_SollP_wert = QLabel(st_Wsoll_str[self.sprache])
        if self.color_Aktiv: self.La_SollP_wert.setStyleSheet(f"color: {self.color[0]}")
        self.La_SollU_wert = QLabel(st_Wsoll_str[self.sprache])
        if self.color_Aktiv: self.La_SollU_wert.setStyleSheet(f"color: {self.color[1]}")
        self.La_SollI_wert = QLabel(st_Wsoll_str[self.sprache])
        if self.color_Aktiv: self.La_SollI_wert.setStyleSheet(f"color: {self.color[2]}")
        #### Status ausgelesen:
        self.La_Status = QLabel(status_1_str[self.sprache])

        ### Knöpfe:
        #### Senden:
        self.btn_send_value = QPushButton(send_str[self.sprache])
        self.btn_send_value.clicked.connect(self.send) 
        #### Rezepte:
        self.btn_rezept_start =  QPushButton(rez_start_str[self.sprache])
        self.btn_rezept_start.clicked.connect(lambda: self.RezStart(1))

        self.btn_rezept_ende =  QPushButton(rez_ende_str[self.sprache])
        self.btn_rezept_ende.clicked.connect(self.RezEnde)   
        #### Generator Ein/Aus;
        self.btn_Ein = QPushButton(QIcon("./vifcon/icons/p_TH_Ein.png"), '')
        self.btn_Ein.setFlat(True)
        self.btn_Ein.clicked.connect(self.NGEin)   

        self.btn_Aus = QPushButton(QIcon("./vifcon/icons/p_TH_Aus.png"), '')
        self.btn_Aus.setFlat(True)
        self.btn_Aus.clicked.connect(self.NGAus) 

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
        #### Knöpfe:
        self.btn_group = QWidget()
        self.btn_group_layout = QVBoxLayout()
        self.btn_group.setLayout(self.btn_group_layout)
        self.btn_group_layout.setSpacing(0)

        self.btn_group_layout.addWidget(self.btn_Ein)
        self.btn_group_layout.addWidget(self.btn_Aus)

        self.btn_group_layout.setContentsMargins(15,0,5,0)       # left, top, right, bottom

        #### Rezept:
        self.btn_group_Rezept = QWidget()
        self.btn_Rezept_layout = QVBoxLayout()
        self.btn_group_Rezept.setLayout(self.btn_Rezept_layout)
        self.btn_Rezept_layout.setSpacing(5)

        self.btn_Rezept_layout.addWidget(self.btn_rezept_start)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_ende)
        self.btn_Rezept_layout.addWidget(self.cb_Rezept)

        self.btn_Rezept_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom

        #### Soll-Werte und Eingabefeld:
        wid_list       = [[self.LE_Pow, self.La_SollP_wert], [self.LE_Voltage, self.La_SollU_wert], [self.LE_Current, self.La_SollI_wert]]
        group_wid_list = []
        for n in wid_list:
            wid_group_Soll  = QWidget()
            wid_Soll_layout = QHBoxLayout()
            wid_group_Soll.setLayout(wid_Soll_layout)
            wid_Soll_layout.setSpacing(5)

            wid_Soll_layout.addWidget(n[0])
            wid_Soll_layout.addWidget(n[1])

            wid_Soll_layout.setContentsMargins(0,0,0,0)
            group_wid_list.append(wid_group_Soll) # P, U, I

        #### First-Row:
        self.first_row_group  = QWidget()
        self.first_row_layout = QHBoxLayout()
        self.first_row_group.setLayout(self.first_row_layout)
        self.first_row_layout.setSpacing(20)

        self.first_row_layout.addWidget(self.La_name)
        self.first_row_layout.addWidget(self.Auswahl)
        self.first_row_layout.addWidget(self.PID_cb)

        self.first_row_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom
        
        #### Label-Werte:
        W_spalte = 80

        label_list      = [self.La_IstPow_text, self.La_IstVoltage_text, self.La_IstCurrent_text, self.La_IstFre_text, self.La_IstPID_text, self.La_SollPID_text]
        label_unit_list = [self.La_IstPow_wert, self.La_IstVoltage_wert, self.La_IstCurrent_wert, self.La_IstFre_wert, self.La_IstPID_wert, self.La_SollPID_wert]
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
        self.layer_layout.addWidget(self.first_row_group,       0, 0, 1, 5, alignment=Qt.AlignLeft)  # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung
        self.layer_layout.addWidget(self.RB_choise_Pow,         1, 0)                         
        self.layer_layout.addWidget(self.RB_choise_Voltage,     2, 0)
        self.layer_layout.addWidget(self.RB_choise_Current,     3, 0)
        self.layer_layout.addWidget(self.btn_send_value,        4, 0) 
        self.layer_layout.addWidget(self.La_Status,             5, 0, 1, 6, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(group_wid_list[0],          1, 1, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(group_wid_list[1],          2, 1, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(group_wid_list[2],          3, 1, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_error,              4, 1) 
        self.layer_layout.addWidget(self.V,                     1, 2, 4, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.btn_group_Rezept,      1, 4, 3, 1, alignment=Qt.AlignTop)
        self.layer_layout.addWidget(self.btn_group,             1, 5, 4, 1, alignment=Qt.AlignTop)

        #________________________________________
        ## Größen (Size) - Widgets:
        ### Button-Icon:
        self.btn_Aus.setIconSize(QSize(50, 50))
        self.btn_Ein.setIconSize(QSize(50, 50))

        ### Eingabefelder (Line Edit):
        width = 70
        self.LE_Pow.setFixedWidth(width)
        self.LE_Pow.setFixedHeight(25)

        self.LE_Voltage.setFixedWidth(width)
        self.LE_Voltage.setFixedHeight(25)

        self.LE_Current.setFixedWidth(width)
        self.LE_Current.setFixedHeight(25)

        ### Rezpt-Funktionen:
        self.btn_rezept_start.setFixedWidth(100)
        self.btn_rezept_ende.setFixedWidth(100)
        self.cb_Rezept.setFixedWidth(100)

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

        kurv_dict = {                                                                   # Wert: [Achse, Farbe/Stift, Name]
            'IWI':      ['a1', pg.mkPen(self.color[5], width=2),                            f'{nemoGenerator} - {I_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWI':      ['a1', pg.mkPen(self.color[2]),                                     f'{nemoGenerator} - {I_einzel_str[self.sprache]}<sub>{self.sollwert_str[self.sprache]}</sub>'],
            'IWU':      ['a1', pg.mkPen(self.color[4], width=2),                            f'{nemoGenerator} - {U_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWU':      ['a1', pg.mkPen(self.color[1]),                                     f'{nemoGenerator} - {U_einzel_str[self.sprache]}<sub>{self.sollwert_str[self.sprache]}</sub>'],
            'IWP':      ['a2', pg.mkPen(self.color[3], width=2),                            f'{nemoGenerator} - {P_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWP':      ['a2', pg.mkPen(self.color[0]),                                     f'{nemoGenerator} - {P_einzel_str[self.sprache]}<sub>{self.sollwert_str[self.sprache]}</sub>'],
            'IWf':      ['a2', pg.mkPen(self.color[6], width=2),                            f'{nemoGenerator} - {f_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'oGI':      ['a1', pg.mkPen(color=self.color[5], style=Qt.DashLine),            f'{nemoGenerator} - {I_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGI':      ['a1', pg.mkPen(color=self.color[5], style=Qt.DashDotDotLine),      f'{nemoGenerator} - {I_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGU':      ['a1', pg.mkPen(color=self.color[4], style=Qt.DashLine),            f'{nemoGenerator} - {U_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGU':      ['a1', pg.mkPen(color=self.color[4], style=Qt.DashDotDotLine),      f'{nemoGenerator} - {U_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGP':      ['a2', pg.mkPen(color=self.color[3], style=Qt.DashLine),            f'{nemoGenerator} - {P_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGP':      ['a2', pg.mkPen(color=self.color[3], style=Qt.DashDotDotLine),      f'{nemoGenerator} - {P_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'RezI':     ['a1', pg.mkPen(color=self.color[9], width=3, style=Qt.DotLine),    f'{nemoGenerator} - {rezept_Label_str[self.sprache]}<sub>{I_einzel_str[self.sprache]}</sub>'],
            'RezU':     ['a1', pg.mkPen(color=self.color[8], width=3, style=Qt.DotLine),    f'{nemoGenerator} - {rezept_Label_str[self.sprache]}<sub>{U_einzel_str[self.sprache]}</sub>'],
            'RezP':     ['a2', pg.mkPen(color=self.color[7], width=3, style=Qt.DotLine),    f'{nemoGenerator} - {rezept_Label_str[self.sprache]}<sub>{P_einzel_str[self.sprache]}</sub>'],
            'SWxPID':   ['a1', pg.mkPen(self.color[10], width=2, style=Qt.DashDotLine),     f'{PID_Label_Soll} ({Kurven_Device_M[self.sprache]} {nemoGenerator}) - {x_einzel_str[self.sprache]}<sub>{PID_Export_Soll}{self.sollwert_str[self.sprache]}</sub>'], 
            'IWxPID':   ['a1', pg.mkPen(self.color[11], width=2, style=Qt.DashDotLine),     f'{PID_Label_Ist}({Kurven_Device_M[self.sprache]} {nemoGenerator}) - {x_einzel_str[self.sprache]}<sub>{PID_Export_Ist}{istwert_str[self.sprache]}</sub>'],
            'Rezx':     ['a1', pg.mkPen(color=self.color[12], width=3, style=Qt.DotLine),   f'{nemoGenerator} - {rezept_Label_str[self.sprache]}<sub>{x_einzel_str[self.sprache]}</sub>'],
            'oGPID':    ['a1', pg.mkPen(color=self.color[11], style=Qt.DashLine),           f'{nemoGenerator} - {self.PID_G_Kurve[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGPID':    ['a1', pg.mkPen(color=self.color[11], style=Qt.DashDotDotLine),     f'{nemoGenerator} - {self.PID_G_Kurve[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
        }

        ## Kurven erstellen:
        ist_drin_list = []                                                              # Jede Kurve kann nur einmal gesetzt werden!
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
        self.IWIList     = []
        self.IWUList     = []
        self.IWPList     = []
        self.IWfList     = []

        self.SWIList     = []
        self.SWUList     = []
        self.SWPList     = []
        
        self.sollxPID    = []
        self.istxPID     = []
        ### Grenzen
        self.IoGList     = []
        self.IuGList     = []
        self.PoGList     = []
        self.PuGList     = []
        self.UoGList     = []
        self.UuGList     = []
        self.XoGList     = []
        self.XuGList     = []

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.curveDict      = {'IWP': '', 'IWU': '', 'IWI': '', 'IWf': '', 'SWP': '', 'SWU': '', 'SWI': '', 'oGI':'', 'uGI':'', 'oGU':'', 'uGU':'', 'oGP':'', 'uGP':'', 'RezI':'', 'RezU':'', 'RezP':'', 'SWxPID':'', 'IWxPID':'', 'Rezx': '', 'oGPID':'', 'uGPID':''}                                                                                                                                                                              # Kurven
        for kurve in self.kurven_dict: 
            self.curveDict[kurve] = self.kurven_dict[kurve]
        self.labelDict      = {'IWP': self.La_IstPow_wert,                                  'IWU': self.La_IstVoltage_wert,                              'IWI': self.La_IstCurrent_wert,                'IWf': self.La_IstFre_wert,                       'IWxPID': self.La_IstPID_wert,                 'SWxPID': self.La_SollPID_wert, 'SWP': self.La_SollP_wert,  'SWU': self.La_SollU_wert,  'SWI': self.La_SollI_wert}  # Label
        self.labelUnitDict  = {'IWP': self.einheit_P_einzel[self.sprache],                  'IWU': self.einheit_U_einzel[self.sprache],                  'IWI': self.einheit_I_einzel[self.sprache],    'IWf': self.einheit_f_einzel[self.sprache],       'IWxPID': self.einheit_x_einzel[self.sprache], 'SWxPID': self.einheit_x_einzel[self.sprache]}                                                                      # Einheit
        self.listDict       = {'IWP': self.IWPList,                                         'IWU': self.IWUList,                                         'IWI': self.IWIList,                           'IWf': self.IWfList,                              'IWxPID': self.istxPID,                        'SWxPID': self.sollxPID,        'SWP': self.SWPList,        'SWU': self.SWUList,        'SWI': self.SWIList}        # Werte-Listen
        self.grenzListDict  = {'oGP': self.PoGList,     'uGP': self.PuGList,                'oGU': self.UoGList,             'uGU': self.UuGList,        'oGI': self.IoGList,  'uGI': self.IuGList,     'oGPID': self.XoGList,                            'uGPID': self.XuGList}
        self.grenzValueDict = {'oGP': self.oGP,         'uGP': self.uGP,                    'oGU': self.oGU,                 'uGU': self.uGU,            'oGI': self.oGI,      'uGI': self.uGI,         'oGPID': self.oGx,                                'uGPID': self.uGx}

        ## Plot-Skalierungsfaktoren:
        self.skalFak_dict = {}
        for size in self.curveDict:
            if 'WP' in size:
                self.skalFak_dict.update({size: self.skalFak['Pow']})
            if 'WI' in size:
                self.skalFak_dict.update({size: self.skalFak['Current']})
            if 'WU' in size:
                self.skalFak_dict.update({size: self.skalFak['Voltage']})
            if 'Wf' in size:
                self.skalFak_dict.update({size: self.skalFak['Freq_2']})
            if 'Wx' in size:
                self.skalFak_dict.update({size: self.skalFak['PIDG']})

        #---------------------------------------
        # Timer:
        #---------------------------------------
        ## Rezept-Timer
        self.RezTimer = QTimer()
        self.RezTimer.timeout.connect(self.Rezept)

        #---------------------------------------
        # Bei Init False sperren:
        #---------------------------------------
        if not self.init:
            self.RB_choise_Voltage.setEnabled(False)
            self.RB_choise_Pow.setEnabled(False)
            self.RB_choise_Current.setEnabled(False)

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
    def Fehler_Output(self, Fehler, error_Message_Log_GUI = '', error_Message_Ablauf = '', device = ''):
        ''' Erstelle Fehler-Nachricht für GUI, Ablaufdatei und Logging
        Args:
            Fehler (bool):                  False -> o.k. (schwarz), True -> Fehler (rot, bold)
            error_Message_Log_GUI (str):    Nachricht die im Log und der GUI angezeigt wird
            error_Message_Ablauf (str):     Nachricht für die Ablaufdatei
            device (str):                   Wenn ein anderes Gerät genutzt wird (z.B. PID)
        '''
        if device == '':
            device_name = self.device_name
        else:
            device_name = device 
        if Fehler:
            self.La_error.setText(self.err_0_str[self.sprache])
            self.La_error.setToolTip(error_Message_Log_GUI)  
            self.La_error.setStyleSheet(f"color: red; font-weight: bold")
            log_vorberietung = error_Message_Log_GUI.replace("\n"," ")
            logger.error(f'{device_name} - {log_vorberietung}')
        else:
            self.La_error.setText(self.err_13_str[self.sprache])
            self.La_error.setToolTip('')
            self.La_error.setStyleSheet(f"color: black; font-weight: normal")
        if not error_Message_Ablauf == '':
                self.add_Text_To_Ablauf_Datei(f'{device_name} - {error_Message_Ablauf}') 
        
    ##########################################
    # Reaktion auf Radio-Butttons:
    ##########################################
    def BlassOutUI(self, selected):
        ''' Leistungs Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_13_str[self.sprache]}')
            self.LE_Pow.setEnabled(True)
            self.LE_Current.setEnabled(False)
            self.LE_Voltage.setEnabled(False)
            self.write_value['Ak_Size'] = 'P'
            self.write_task['Wahl_P']   = True
            self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_P[self.sprache]} {self.uGP} ... {self.oGP} {self.einheit_P_einzel[self.sprache]}'
            self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')
            self.PID_Reset(1)

    def BlassOutPI(self, selected):
        ''' Spannungs Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_14_str[self.sprache]}')
            self.LE_Pow.setEnabled(False)
            self.LE_Current.setEnabled(False)
            self.LE_Voltage.setEnabled(True)
            self.write_value['Ak_Size'] = 'U'
            self.write_task['Wahl_U'] = True
            self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_U[self.sprache]} {self.uGU} ... {self.oGU} {self.einheit_U_einzel[self.sprache]}'
            self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')
            self.PID_Reset(1)

    def BlassOutPU(self, selected):
        ''' Strom Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_15_str[self.sprache]}')
            self.LE_Pow.setEnabled(False)
            self.LE_Current.setEnabled(True)
            self.LE_Voltage.setEnabled(False)
            self.write_value['Ak_Size'] = 'I'
            self.write_task['Wahl_I'] = True
            self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_I[self.sprache]} {self.uGI} ... {self.oGI} {self.einheit_I_einzel[self.sprache]}'
            self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')
            self.PID_Reset(1)
    
    ##########################################
    # Reaktion auf Butttons:
    ##########################################
    def send(self):
        ''' Sende Knopf betätigt:
        - Lese Eingabefelder aus
        - Kontrolliere Wert
        - Sage Programm Bescheid das Knopf betätigt wurde!
        '''
        if self.init:
            ## Wenn der Radio-Button der Sollleistung gewählt ist:
            if self.RB_choise_Pow.isChecked():
                sollwert = self.LE_Pow.text().replace(",", ".")
                if not self.PID_cb.isChecked():
                    self.write_task['Soll-Leistung'] = True
                self.write_task['Soll-Spannung'] = False 
                self.write_task['Soll-Strom'] = False
                oG, uG, einheit = self.oGP, self.uGP, self.einheit_P_einzel[self.sprache]
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_16_str[self.sprache]}')
            ## Wenn der Radio-Button der Sollspannung gewählt ist:
            elif self.RB_choise_Voltage.isChecked():
                sollwert = self.LE_Voltage.text().replace(",", ".")
                self.write_task['Soll-Leistung'] = False
                if not self.PID_cb.isChecked():
                    self.write_task['Soll-Spannung'] = True
                self.write_task['Soll-Strom'] = False
                oG, uG, einheit = self.oGU, self.uGU, self.einheit_U_einzel[self.sprache]
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_17_str[self.sprache]}')
            ## Wenn der Radio-Button des Sollstroms gewählt ist:
            else:
                sollwert = self.LE_Current.text().replace(",", ".")
                self.write_task['Soll-Leistung'] = False
                self.write_task['Soll-Spannung'] = False
                if not self.PID_cb.isChecked():
                    self.write_task['Soll-Strom'] = True
                oG, uG, einheit = self.oGI, self.uGI, self.einheit_I_einzel[self.sprache]
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_18_str[self.sprache]}')
            # PID-Modus:
            if self.PID_cb.isChecked():
                self.write_task['Soll-Leistung'] = False
                self.write_task['Soll-Spannung'] = False
                self.write_task['Soll-Strom'] = False
                oG, uG, einheit = self.oGx, self.uGx, self.einheit_x_einzel[self.sprache]
            # Kontrolliere die Eingabe im Eingabefeld:
            sollwert = self.controll_value(sollwert, oG, uG, einheit)
            # Ist alles in Ordnung, dann Gebe dem Programm Bescheid, das es den Wert schreiben kann:
            if sollwert != -1:
                if not self.PID_cb.isChecked(): self.write_value['Sollwert']     = sollwert
                else:                           self.write_value['PID-Sollwert'] = sollwert
            else:
                self.write_task['Soll-Leistung'] = False
                self.write_task['Soll-Spannung'] = False
                self.write_task['Soll-Strom'] = False
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def NGEin(self):
        '''Schalte Generator Ein'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Neu_1[self.sprache]}')
            self.write_task['Ein'] = True
            self.write_task['Aus'] = False
            self.Generator_Ein = True
            self.RB_choise_Pow.setEnabled(False)
            self.RB_choise_Current.setEnabled(False)
            self.RB_choise_Voltage.setEnabled(False)
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])
    
    def NGAus(self):
        '''Schalte Generator Aus'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Neu_2[self.sprache]}')
            self.write_task['Aus'] = True
            self.write_task['Ein'] = False
            self.Generator_Ein = False
            if not self.write_task['PID']:
                if self.Auswahl_PUI == 'PUI':
                    self.RB_choise_Pow.setEnabled(True)
                    self.RB_choise_Voltage.setEnabled(True) 
                self.RB_choise_Current.setEnabled(True)
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])
    
    ##########################################
    # Eingabefeld Kontrolle:
    ##########################################
    def controll_value(self, value, oG, uG, unit):
        ''' Kontrolliere die Eingabe eines Eingabefeldes.

        Args:
            value (str):    zu untersuchende Eingabe
            oG (int):       Ober Grenze
            uG (int):       Unter Grenze
            unit (str):     Einheiten String für Log/Fehlermeldung GUI
        Return:
            -1 (int):       Fehlerfall
            value (float):  Ausgelesener Wert
        '''

        if value == '':
            self.Fehler_Output(1, self.err_1_str[self.sprache], self.Text_19_str[self.sprache])                             
        else:
            try:
                value = float(value)
                if value < uG or value > oG:
                    self.Fehler_Output(1, f'{self.err_2_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG} {unit}', self.Text_20_str[self.sprache])     
                else:
                    self.Fehler_Output(0, error_Message_Ablauf=f'{self.Text_21_str[self.sprache]} {value}.')                                      
                    return value
            except Exception as e:
                self.Fehler_Output(1, self.err_5_str[self.sprache], self.Text_22_str[self.sprache])   
                logger.exception(f"{self.device_name} - {self.Log_Text_38_str[self.sprache]}")
                                
        return -1

    ##########################################
    # Reaktion Checkbox:
    ##########################################    
    def PID_ON_OFF(self):  
        '''PID-Modus toggeln'''
        if self.PID_cb.isChecked():
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_1[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID']          = True
            self.write_task['Soll-Leistung'] = False
            self.write_task['Soll-Spannung'] = False
            self.write_task['Soll-Strom']    = False

            # Zugriff freigeben, Speeren, GUI-ändern:
            ## Strom:
            if self.RB_choise_Current.isChecked(): 
                self.LE_Current.setEnabled(True)
                self.LE_Current.setToolTip('')
                self.LE_Pow.setEnabled(False)
                self.LE_Voltage.setEnabled(False)
                label = self.RB_choise_Current
                self.write_value['Limit Unit']      = self.einheit_I_einzel[self.sprache]
                self.write_value['PID Output-Size'] = 'I'
                uG, oG = self.uGI, self.oGI
                if self.color_Aktiv: self.La_SollI_wert.setStyleSheet(f"color: {self.color[10]}")
                self.La_SollPID_text.setText(f'{self.PID_Out[self.sprache]} {self.PID_Out_I[self.sprache]}')
                color_Size = 2
            ## Leistung:
            elif self.RB_choise_Pow.isChecked():  
                self.LE_Current.setEnabled(False)
                self.LE_Pow.setEnabled(True)
                self.LE_Pow.setToolTip('')
                self.LE_Voltage.setEnabled(False)
                label = self.RB_choise_Pow
                self.write_value['Limit Unit']      = self.einheit_P_einzel[self.sprache]
                self.write_value['PID Output-Size'] = 'P'
                uG, oG = self.uGP, self.oGP
                if self.color_Aktiv: self.La_SollP_wert.setStyleSheet(f"color: {self.color[10]}")
                self.La_SollPID_text.setText(f'{self.PID_Out[self.sprache]} {self.PID_Out_P[self.sprache]}')
                color_Size = 0
            ## Spannung:
            elif self.RB_choise_Voltage.isChecked():   
                self.LE_Current.setEnabled(False)
                self.LE_Pow.setEnabled(False)
                self.LE_Voltage.setEnabled(True)
                self.LE_Voltage.setToolTip('')
                label = self.RB_choise_Voltage
                self.write_value['Limit Unit']      = self.einheit_U_einzel[self.sprache]
                self.write_value['PID Output-Size'] = 'U'
                uG, oG = self.uGU, self.oGU
                if self.color_Aktiv: self.La_SollU_wert.setStyleSheet(f"color: {self.color[10]}")
                self.La_SollPID_text.setText(f'{self.PID_Out[self.sprache]} {self.PID_Out_U[self.sprache]}')
                color_Size = 1
            
            label.setText(f'{self.sollwert_str[self.sprache]}-{self.x_str[self.sprache]}')
            if self.color_Aktiv: label.setStyleSheet(f"color: {self.color[10]}")
            if self.color_Aktiv: self.La_SollPID_text.setStyleSheet(f"color: {self.color[color_Size]}")
            if self.color_Aktiv: self.La_SollPID_wert.setStyleSheet(f"color: {self.color[color_Size]}")

            self.write_task['Update Limit'] = True
            self.write_value['Limits']      = [oG, uG, self.oGx, self.uGx, False] 

            # Zugriff sperren:
            self.RB_choise_Pow.setEnabled(False)
            self.RB_choise_Current.setEnabled(False)
            self.RB_choise_Voltage.setEnabled(False)
            # Bei Multilog-Sollwert:
            if self.origin[1] == 'M':
                self.btn_rezept_start.setEnabled(False)
                self.btn_rezept_ende.setEnabled(False)
                self.cb_Rezept.setEnabled(False)
                self.btn_send_value.setEnabled(False)
        
        else:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_2[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID']           = False
            self.write_task['Soll-Leistung'] = False
            self.write_task['Soll-Spannung'] = False
            self.write_task['Soll-Strom']    = False  
            valueP = self.PID_Mode_Switch_Value_P
            valueI = self.PID_Mode_Switch_Value_I
            valueU = self.PID_Mode_Switch_Value_U
            ## Strom:
            if self.RB_choise_Current.isChecked():
                self.LE_Current.setText(str(valueI))
                TT_I = f'{self.TTLimit[self.sprache]}{self.TTSize_I[self.sprache]}  {self.uGP} ... {self.oGI} {self.einheit_I_einzel[self.sprache]}'
                self.LE_Current.setToolTip(TT_I)
                if self.color_Aktiv: self.La_SollI_wert.setStyleSheet(f"color: {self.color[2]}")
                oG    = self.oGI
                uG    = self.uGI
                Task  = 'Soll-Strom'
                label = self.RB_choise_Current
                text  = self.I_str
                cn    = 2
                value = valueI
            ## Leistung:
            elif self.RB_choise_Pow.isChecked():
                self.LE_Pow.setText(str(valueP))
                self.LE_Pow.setText(str(valueP))
                TT_P = f'{self.TTLimit[self.sprache]}{self.TTSize_P[self.sprache]}  {self.uGP} ... {self.oGP} {self.einheit_P_einzel[self.sprache]}'
                if self.color_Aktiv: self.La_SollP_wert.setStyleSheet(f"color: {self.color[0]}") 
                oG    = self.oGP
                uG    = self.uGP
                Task  = 'Soll-Leistung'
                label = self.RB_choise_Pow
                text  = self.P_str
                cn    = 0
                value = valueP
            # Spannung:
            elif self.RB_choise_Voltage.isChecked():
                self.LE_Voltage.setText(str(valueU))
                TT_U = f'{self.TTLimit[self.sprache]}{self.TTSize_U[self.sprache]}  {self.uGU} ... {self.oGU} {self.einheit_U_einzel[self.sprache]}'
                self.LE_Voltage.setToolTip(TT_U)
                if self.color_Aktiv: self.La_SollU_wert.setStyleSheet(f"color: {self.color[1]}")
                oG    = self.oGU
                uG    = self.uGU
                Task  = 'Soll-Spannung'
                label = self.RB_choise_Voltage
                text  = self.U_str
                cn    = 1
                value = valueU
            if value > oG or value < uG:
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_Ex[self.sprache]}") 
                self.write_value[Task] = uG
            else:
                self.write_value[Task] = value

            # GUI-ändern:
            label.setText(f'{self.sollwert_str[self.sprache]}-{text[self.sprache]}')
            if self.color_Aktiv: label.setStyleSheet(f"color: {self.color[cn]}")    
            self.La_SollPID_text.setText(f'{self.sollwert_str[self.sprache]}-{self.sx_str[self.sprache]}') 
            if self.color_Aktiv: self.La_SollPID_text.setStyleSheet(f"color: {self.color[10]}")
            if self.color_Aktiv: self.La_SollPID_wert.setStyleSheet(f"color: {self.color[10]}")  

            # Zugriff sperren; Zugriff freigeben:
            if not self.Generator_Ein:
                if self.Auswahl_PUI == 'PUI':
                    self.RB_choise_Pow.setEnabled(True)
                    self.RB_choise_Voltage.setEnabled(True)
                self.RB_choise_Current.setEnabled(True)
            # Bei Multilog-Sollwert:
            if self.origin[1] == 'M':
                self.btn_rezept_start.setEnabled(True)
                self.btn_rezept_ende.setEnabled(True)
                self.cb_Rezept.setEnabled(True)
                self.btn_send_value.setEnabled(True)
    
    ##########################################
    # Reaktion auf übergeordnete Butttons:
    ##########################################
    def Stopp(self, n = 3):
        ''' Setzt den Eurotherm in einen Sicheren Zustand '''
        if self.init:
            if n == 5:  self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_90_str[self.sprache]}')
            # Beende PID-Modus:
            self.PID_cb.setChecked(False)
            self.PID_ON_OFF()
            # Beende Rezept:
            self.RezEnde(n)
            # Schalte Generator aus:
            self.NGAus()
            # Sende Befehle:
            self.write_value['Sollwert'] = 0
            self.write_task['Soll-Leistung'] = True
            self.write_task['Soll-Spannung'] = True
            self.write_task['Soll-Strom'] = True
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])
    
    def update_Limit(self):
        '''Lese die Config und Update die Limits'''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Extra_1[self.sprache]}{self.Text_LimitUpdate[self.sprache]}')

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
            ### Sollleistung:
            try: self.oGP = config['devices'][self.device_name]["limits"]['maxP'] 
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxP {self.Log_Pfad_conf_5[self.sprache]} 1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGP = 1       
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            try: self.uGP = config['devices'][self.device_name]["limits"]['minP']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minP {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGP = 0
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            if not type(self.oGP) in [float, int] or not self.oGP >= 0:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGP)}')
                self.oGP = 1
            if not type(self.uGP) in [float, int] or not self.oGP >= 0:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGP)}')
                self.uGP = 0
            if self.oGP <= self.uGP:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_15[self.sprache]})')
                self.uGP = 0
                self.oGP = 1
            ### Sollstrom:
            try: self.oGI = config['devices'][self.device_name]["limits"]['maxI'] 
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxI {self.Log_Pfad_conf_5[self.sprache]} 1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGI = 1 
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\      
            try: self.uGI = config['devices'][self.device_name]["limits"]['minI']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minI {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGI = 0
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            if not type(self.oGI) in [float, int] or not self.oGI >= 0:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGI)}')
                self.oGI = 1
            if not type(self.uGI) in [float, int] or not self.oGI >= 0:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGI)}')
                self.uGI = 0
            if self.oGI <= self.uGI:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_11[self.sprache]})')
                self.uGI = 0
                self.oGI = 1
            ### Sollspannung:
            try: self.oGU = config['devices'][self.device_name]["limits"]['maxU']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxU {self.Log_Pfad_conf_5[self.sprache]} 1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGU = 1  
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\        
            try: self.uGU = config['devices'][self.device_name]["limits"]['minU']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minU {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGU = 0  
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            if not type(self.oGU) in [float, int] or not self.oGU >= 0:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGU)}')
                self.oGU = 1
            if not type(self.uGU) in [float, int] or not self.oGU >= 0:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGU)}')
                self.uGU = 0
            if self.oGU <= self.uGU:
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
                self.uGU = 0
                self.oGU = 1
            ### PID-Input-Output:
            try: self.oGx = config['devices'][self.device_name]['PID']['Input_Limit_max']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_max {self.Log_Pfad_conf_5[self.sprache]} 1')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.oGx = 1
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            try: self.uGx = config['devices'][self.device_name]['PID']['Input_Limit_min']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_min {self.Log_Pfad_conf_5[self.sprache]} 0')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.uGx = 0
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
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
            if self.PID_cb.isChecked() and self.RB_choise_Pow.isChecked():  self.LE_Pow.setToolTip('')
            else:
                TT_P = f'{self.TTLimit[self.sprache]}{self.TTSize_P[self.sprache]} {self.uGP} ... {self.oGP} {self.einheit_P_einzel[self.sprache]}'
                self.LE_Pow.setToolTip(TT_P)

            if self.PID_cb.isChecked() and self.RB_choise_Current.isChecked():  self.LE_Current.setToolTip('')
            else:
                TT_I = f'{self.TTLimit[self.sprache]}{self.TTSize_I[self.sprache]} {self.uGI} ... {self.oGI} {self.einheit_I_einzel[self.sprache]}'
                self.LE_Current.setToolTip(TT_I)

            if self.PID_cb.isChecked() and self.RB_choise_Voltage.isChecked():  self.LE_Voltage.setToolTip('')
            else:
                TT_U = f'{self.TTLimit[self.sprache]}{self.TTSize_U[self.sprache]} {self.uGU} ... {self.oGU} {self.einheit_U_einzel[self.sprache]}'
                self.LE_Voltage.setToolTip(TT_U)

            self.TT_PID_In   = f'{self.TTSize_1[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_x[self.sprache]} {self.uGx} ... {self.oGx} {self.einheit_x_einzel[self.sprache]}'
            if self.RB_choise_Pow.isChecked():          self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_P[self.sprache]} {self.uGP} ... {self.oGP} {self.einheit_P_einzel[self.sprache]}'
            elif self.RB_choise_Current.isChecked():    self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_I[self.sprache]} {self.uGI} ... {self.oGI} {self.einheit_I_einzel[self.sprache]}'
            elif self.RB_choise_Voltage.isChecked():    self.TT_PID_Out  = f'{self.TTSize_2[self.sprache]}{self.TTLimit[self.sprache]}{self.TTSize_U[self.sprache]} {self.uGU} ... {self.oGU} {self.einheit_U_einzel[self.sprache]}'
            self.PID_cb.setToolTip(f'{self.TT_PID_In}\n{self.TT_PID_Out}\n{self.TT_PID_Para}')

            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Weiterleiten:
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if self.RB_choise_Current.isChecked():
                oG    = self.oGI
                uG    = self.uGI
                self.write_value['Limit Unit']  = self.einheit_I_einzel[self.sprache]
            elif self.RB_choise_Pow.isChecked():
                oG    = self.oGP
                uG    = self.uGP
                self.write_value['Limit Unit']  = self.einheit_P_einzel[self.sprache]
            elif self.RB_choise_Voltage.isChecked():
                oG    = self.oGU
                uG    = self.uGU
                self.write_value['Limit Unit']  = self.einheit_U_einzel[self.sprache]

            self.write_task['Update Limit']     = True
            self.write_value['Limits']          = [oG, uG, self.oGx, self.uGx, True]

            logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGI} {self.Log_Text_LB_4[self.sprache]} {self.oGI} {self.einheit_I_einzel[self.sprache]}')
            logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGU} {self.Log_Text_LB_4[self.sprache]} {self.oGU} {self.einheit_U_einzel[self.sprache]}')
            logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3_1[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGP} {self.Log_Text_LB_4[self.sprache]} {self.oGP} {self.einheit_P_einzel[self.sprache]}')
        
            self.Fehler_Output(0)
        else:
            self.Fehler_Output(1, self.Log_Yaml_Error[self.sprache], self.Text_Update[self.sprache])
    
    def PID_Reset(self, wahl = 0):
        ''' Löse den Reset des PID-Reglers aus!
        
        Args:
            wahl (int): Ablauf-Datei Zusatz
        '''
        if wahl == 0:   extra = self.Text_Extra_1[self.sprache]
        elif wahl == 1: extra = ''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - ' + extra + f'{self.Text_PIDReset_str[self.sprache]}')
        
        if not self.PID_cb.isChecked():
            ## Aktuelle Limits:
            if self.RB_choise_Pow.isChecked():              oGPID, uGPID = self.oGP, self.uGP
            elif self.RB_choise_Current.isChecked():        oGPID, uGPID = self.oGI, self.uGI
            elif self.RB_choise_Voltage.isChecked():        oGPID, uGPID = self.oGU, self.uGU

            ## Aufagben setzen:
            self.write_task['Update Limit']  = True
            self.write_value['Limits']       = [oGPID, uGPID, self.oGx, self.uGx, True]
            self.write_task['PID-Reset']     = True
            self.write_value['PID-Sollwert'] = 0
            ## Meldung:
            self.Fehler_Output(0)
        else:
            self.Fehler_Output(1, self.Text_PIDResetError[self.sprache], self.Text_PIDResetError[self.sprache])
            
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
    # Betrachtung der Labels und Plots:
    ##########################################
    def update_GUI(self, value_dict, x_value):
        ''' Update der GUI, Plot und Label!

        Args:
            value_dict (dict):  Dictionary mit den aktuellen Werten!
            x_value (list):     Werte für die x-Achse
        '''

        ## Setze ToolTip Name:
        if value_dict["Status_Name"] == 128:   Name = self.Stat_N2_Bit15[self.sprache]
        else:                                  Name = value_dict["Status_Name"]
        if value_dict["Status_Typ"] == 128:    Typ = self.TTTM[self.sprache]
        else:                                  Typ = value_dict["Status_Typ"]
        if value_dict["Status_Kombi"] == 128:  Kombi = self.TTTM[self.sprache]
        else:                                  Kombi = value_dict["Status_Kombi"]
        self.La_name.setToolTip(f'{self.TTName[self.sprache]} {Name} ({Typ})\n{self.TTSKombi[self.sprache]} {Kombi}')

        ## Kurven Update:
        self.data.update({'Time' : x_value[-1]})         
        self.data.update(value_dict) 

        for messung in value_dict:
            if not 'Status' in messung:
                if 'SW' in messung:
                    if messung =='SWxPID':
                        if   self.PID_cb.isChecked() and self.RB_choise_Current.isChecked():    self.labelDict['SWI'].setText(f'({value_dict[messung]})')
                        elif self.PID_cb.isChecked() and self.RB_choise_Voltage.isChecked():    self.labelDict['SWU'].setText(f'({value_dict[messung]})')
                        elif self.PID_cb.isChecked() and self.RB_choise_Pow.isChecked():        self.labelDict['SWP'].setText(f'({value_dict[messung]})')
                        else:                                                                   self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}')
                    if messung == 'SWI':
                        if   self.PID_cb.isChecked() and self.RB_choise_Current.isChecked():    self.labelDict['SWxPID'].setText(f'{value_dict[messung]} {self.labelUnitDict["IWI"]}')
                        else:                                                                   self.labelDict[messung].setText(f'({value_dict[messung]})')
                    if messung == 'SWP':
                        if   self.PID_cb.isChecked() and self.RB_choise_Pow.isChecked():        self.labelDict['SWxPID'].setText(f'{value_dict[messung]} {self.labelUnitDict["IWP"]}')
                        else:                                                                   self.labelDict[messung].setText(f'({value_dict[messung]})')
                    if messung == 'SWU':
                        if   self.PID_cb.isChecked() and self.RB_choise_Voltage.isChecked():    self.labelDict['SWxPID'].setText(f'{value_dict[messung]} {self.labelUnitDict["IWU"]}')
                        else:                                                                   self.labelDict[messung].setText(f'({value_dict[messung]})')
                else:
                    self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}')
                self.listDict[messung].append(value_dict[messung])
                if not self.curveDict[messung] == '':
                    faktor = self.skalFak_dict[messung]
                    y = [a * faktor for a in self.listDict[messung]]
                    self.curveDict[messung].setData(x_value, y)
            #elif 'Status' in messung:
            #    logger.debug(f'{self.device_name} - {self.Log_Status_Int[self.sprache]} ({messung}): {value_dict[messung]}')

        ## Grenz-Kurven:
        ### Update Grenzwert-Dictionary:
        self.grenzValueDict['oGP']      = self.oGP * self.skalFak['Pow']
        self.grenzValueDict['uGP']      = self.uGP * self.skalFak['Pow']
        self.grenzValueDict['oGU']      = self.oGU * self.skalFak['Voltage']
        self.grenzValueDict['uGU']      = self.uGU * self.skalFak['Voltage']
        self.grenzValueDict['oGI']      = self.oGI * self.skalFak['Current']
        self.grenzValueDict['uGI']      = self.uGI * self.skalFak['Current']
        self.grenzValueDict['oGPID']    = self.oGx * self.skalFak['PIDG']
        self.grenzValueDict['uGPID']    = self.uGx * self.skalFak['PIDG']
        ### Update-Kurven:
        for kurve in self.kurven_dict:
            if kurve in self.grenzListDict:
                self.grenzListDict[kurve].append(float(self.grenzValueDict[kurve]))
                self.kurven_dict[kurve].setData(x_value, self.grenzListDict[kurve])

        ## Status:
        status_1 = value_dict['Status']
        logger.debug(f'{self.device_name} - {self.Log_Status_Int[self.sprache]} (Status): {value_dict["Status"]}')
        status_1 = self.status_report_umwandlung(status_1)
        ### Status-Liste:
        status = [self.Stat_N2_Bit0[self.sprache], self.Stat_N2_Bit1[self.sprache], self.Stat_N2_Bit2[self.sprache], self.Stat_N2_Bit3[self.sprache], self.Stat_N2_Bit4[self.sprache], self.Stat_N2_Bit5[self.sprache], self.Stat_N2_Bit6[self.sprache], self.Stat_N2_Bit7[self.sprache], self.Stat_N2_Bit8[self.sprache], self.Stat_N2_Bit9[self.sprache], self.Stat_N2_Bit10[self.sprache], self.Stat_N2_Bit11[self.sprache], self.Stat_N2_Bit12[self.sprache], self.Stat_N2_Bit13[self.sprache], self.Stat_N2_Bit14[self.sprache], self.Stat_N2_Bit15[self.sprache]]
        ### Status Zusammenfügen:
        label_s1 = ''
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

    def Pop_Up_Start_Later(self):
        ## Pop-Up-Fenster verzögert zum Start starten:
        if self.start_later:
            self.start_later = False
            self.typ_widget.Message(f'{self.device_name} - {self.Message_1[self.sprache]}', 3, 500)         # Aufruf einer Message-Box, Warnung
        
    ##########################################
    # Reaktion auf Initialisierung:
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
            self.Start()
            self.init = True
        else:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_nicht_Okay.png"))
            self.init = False

    def Start(self):
        '''Funktion die nur beim Start beachtet werden muss (Init oder Start)'''
        if self.stMode == 'U':
            self.RB_choise_Voltage.setChecked(True)
            self.LE_Pow.setEnabled(False)
            self.LE_Voltage.setEnabled(True)
            self.LE_Current.setEnabled(False)
            self.write_value['Ak_Size'] = 'U'
            self.write_task['Wahl_U'] = True
        elif self.stMode == 'I':                            # Strom ist Default
            self.RB_choise_Current.setChecked(True)
            self.LE_Pow.setEnabled(False)
            self.LE_Voltage.setEnabled(False)
            self.LE_Current.setEnabled(True)
            self.write_value['Ak_Size'] = 'I'
            self.write_task['Wahl_I'] = True
        elif self.stMode == 'P':                                           
            self.RB_choise_Pow.setChecked(True)
            self.LE_Pow.setEnabled(True)
            self.LE_Voltage.setEnabled(False)
            self.LE_Current.setEnabled(False)
            self.write_value['Ak_Size'] = 'P'
            self.write_task['Wahl_P'] = True

    ##########################################
    # Reaktion auf Rezepte:
    ##########################################
    def RezStart(self, execute = 1):
        ''' Rezept wurde gestartet '''
        if not self.Rezept_Aktiv:
            if execute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_87_str[self.sprache]}')
            elif execute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_85_str[self.sprache]}')
            
            # Variablen:
            self.step = 0
            self.Rezept_Aktiv = True

            # Kurve erstellen:
            error = self.RezKurveAnzeige()
            if self.cb_Rezept.currentText() == '------------':
                self.Fehler_Output(1, self.err_15_str[self.sprache])
                error = True
            
            if not error:
                # Rezept Log-Notiz:
                logger.info(f'{self.device_name} - {self.Log_Text_39_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}')
                logger.info(f'{self.device_name} - {self.Log_Text_40_str[self.sprache]} {self.rezept_daten}')
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_24_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}')                    

                # Erstes Element senden und Kurve erstellen:
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = self.value_list[self.step]
                    self.write_task['Soll-Leistung'] = False
                    self.write_task['Soll-Spannung'] = False
                    self.write_task['Soll-Strom']    = False
                else:   
                    self.write_value['Sollwert']     = self.value_list[self.step]
                
                    if self.RB_choise_Pow.isChecked():
                        self.write_task['Soll-Leistung'] = True
                    elif self.RB_choise_Voltage.isChecked():
                        self.write_task['Soll-Spannung'] = True
                    elif self.RB_choise_Current.isChecked():
                        self.write_task['Soll-Strom'] = True

                # Elemente GUI sperren:
                self.cb_Rezept.setEnabled(False)
                self.btn_rezept_start.setEnabled(False)
                self.RB_choise_Pow.setEnabled(False)
                self.RB_choise_Voltage.setEnabled(False)
                self.RB_choise_Current.setEnabled(False)
                self.btn_send_value.setEnabled(False)
                self.Auswahl.setEnabled(False)
                self.PID_cb.setEnabled(False)

                # Timer Starten:
                self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))
                self.RezTimer.start()
                self.Fehler_Output(0)
            else:
                self.Rezept_Aktiv = False
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_88_str[self.sprache]}')
        else:
            self.Fehler_Output(1, self.err_16_str[self.sprache], self.Text_84_str[self.sprache])

    def RezEnde(self, excecute = 1):
        ''' Rezept wurde/wird beendet '''
        if self.Rezept_Aktiv == True:
            if excecute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_81_str[self.sprache]}')
            elif excecute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_82_str[self.sprache]}')
            elif excecute == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_83_str[self.sprache]}')
            elif excecute == 4: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_86_str[self.sprache]}')
            elif excecute == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_91_str[self.sprache]}')

            # Elemente GUI entsperren:
            self.cb_Rezept.setEnabled(True)
            if self.PID_Aktiv: self.PID_cb.setEnabled(True)
            self.btn_rezept_start.setEnabled(True)
            if not self.PID_cb.isChecked() and not self.Generator_Ein:
                if self.Auswahl_PUI == 'PUI':
                    self.RB_choise_Pow.setEnabled(True)
                    self.RB_choise_Voltage.setEnabled(True)
                self.RB_choise_Current.setEnabled(True)
            self.btn_send_value.setEnabled(True)
            self.Auswahl.setEnabled(True)

            # Variablen:
            self.Rezept_Aktiv = False

            # Auto Range
            self.typ_widget.plot.AutoRange()

            # Nachricht:
            self.Fehler_Output(0)

            # Timer stoppen:
            self.RezTimer.stop()
        else:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_89_str[self.sprache]}')
        
    def Rezept(self):
        ''' Rezept Schritt wurde beendet, Vorbereitung und Start des neuen '''
        self.step += 1
        if self.step > len(self.time_list) - 1:
            self.RezEnde(2)
        else:
            self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))

            # Nächstes Element senden:
            if self.PID_cb.isChecked():
                self.write_value['PID-Sollwert'] = self.value_list[self.step]
                self.write_task['Soll-Leistung'] = False
                self.write_task['Soll-Spannung'] = False
                self.write_task['Soll-Strom']    = False
            else:
                self.write_value['Sollwert'] = self.value_list[self.step]

                if self.RB_choise_Pow.isChecked():
                    self.write_task['Soll-Leistung'] = True
                elif self.RB_choise_Voltage.isChecked():
                    self.write_task['Soll-Spannung'] = True
                elif self.RB_choise_Current.isChecked():
                    self.write_task['Soll-Strom'] = True
    
    def Rezept_lesen_controll(self):
        ''' Rezept wird ausgelesen und kontrolliert. Bei Fehler werden die Fehlermeldungen beschrieben auf der GUI. 
    
        Return:
            error (Bool):   Fehler vorhanden oder nicht
        '''

        # Variablen:
        error = False  
        self.time_list  = []
        self.value_list = []

        ## Limits (Leistung, Strom oder Spannung):
        if self.RB_choise_Pow.isChecked():
            uG = self.uGP
            oG = self.oGP
            ak_value = self.ak_value['IWP'] if not self.ak_value == {} else 0
            string_einheit = self.einheit_P_einzel[self.sprache]
        elif self.RB_choise_Voltage.isChecked():
            uG = self.uGU
            oG = self.oGU
            ak_value = self.ak_value['IWU'] if not self.ak_value == {} else 0
            string_einheit = self.einheit_U_einzel[self.sprache]
        else:
            uG = self.uGI
            oG = self.oGI
            ak_value = self.ak_value['IWI'] if not self.ak_value == {} else 0
            string_einheit = self.einheit_I_einzel[self.sprache]

        ## PID-Limits:
        if self.PID_cb.isChecked():
            oG = self.oGx
            uG = self.uGx 
            string_einheit = self.einheit_x_einzel[self.sprache]

        # Rezept lesen:
        rezept = self.cb_Rezept.currentText()  
        if not rezept == '------------':
            ## Rezept aus Datei oder in Config:
            ak_rezept = self.rezept_config[rezept]
            if 'dat' in ak_rezept:
                try:
                    with open(f'vifcon/rezepte/{ak_rezept["dat"]}', encoding="utf-8") as f:
                        rez_dat = yaml.safe_load(f)
                    self.rezept_datei = f'({ak_rezept["dat"]})'
                except:
                    self.Fehler_Output(1, self.err_10_str[self.sprache])
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
                self.Fehler_Output(1, self.err_12_str[self.sprache])
                return True
            ## Rezept Kurven-Listen erstellen:
            for n in rez_dat:
                werte = rez_dat[n].split(';')
                ## Beachtung von Kommas (Komma zu Punkt):
                time = float(werte[0].replace(',', '.'))
                value = float(werte[1].replace(',', '.'))
                ## Grenzwert-Kontrolle:
                if value < uG or value > oG:
                    error = True
                    self.Fehler_Output(1, f'{self.err_6_str[self.sprache]} {value} {string_einheit} {self.err_7_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG} {string_einheit}! ({self.err_Rezept_2[self.sprache]} {n})')
                    break
                else:
                    self.Fehler_Output(0)
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
                ### Sprung:
                elif werte[2].strip() == 's':                                               
                    self.value_list.append(value)
                    self.time_list.append(time)
                ### Falsches Segment:
                else:
                    self.Fehler_Output(1, f'{self.err_Rezept[self.sprache]} {werte[2].strip()} ({n})')
                    return True
        else:
            self.Fehler_Output(0)
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

        anzeigeI = True
        anzeigeP = True      
        anzeigeU = True
        anzeigex = True
        if self.PID_cb.isChecked():                        
            try: self.curveDict['Rezx'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigex  = False      
        else:                     
            try: self.curveDict['RezI'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigeI  = False
            try: self.curveDict['RezU'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigeU = False   
            try: self.curveDict['RezP'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigeP = False                          
        
        # Startzeit bestimmen:
        ak_time_1 = datetime.datetime.now(datetime.timezone.utc).astimezone()                # Aktuelle Zeit Absolut
        ak_time = round((ak_time_1 - self.typ_widget.start_zeit).total_seconds(), 3)         # Aktuelle Zeit Relativ

        # Fehler-Kontrolle:
        try: error = self.Rezept_lesen_controll()
        except Exception as e:
            error = True
            logger.exception(f'{self.device_name} - {self.Log_Text_Ex1_str[self.sprache]}')
            self.Fehler_Output(1, self.err_10_str[self.sprache])

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
            
            # Kurve erstellen mit Skalierungsfaktor und Kurve Anzeigen:
            # Kurve erstellen mit Skalierungsfaktor:
            
            ## Leistung, Strom oder Spannung:
            if not self.PID_cb.isChecked():
                if self.RB_choise_Pow.isChecked():
                    faktor = self.skalFak['Pow']
                    y = [a * faktor for a in self.RezValueList]
                    if anzeigeP:
                        self.curveDict['RezP'].setData(self.RezTimeList, y)
                        self.typ_widget.plot.achse_2.autoRange()                    # Rezept Achse 2 wird nicht fertig angezeigt, aus dem Grund wird dies durchgeführt! Beim Enden wird die AutoRange Funktion von base_classes.py durchgeführt. Bewegung des Plots sind mit der Lösung nicht machbar!!
                                                                                    # Plot wird nur an Achse 1 (links) angepasst!
                elif self.RB_choise_Voltage.isChecked():
                    faktor = self.skalFak['Voltage']
                    y = [a * faktor for a in self.RezValueList]
                    if anzeigeU:
                        self.curveDict['RezU'].setData(self.RezTimeList, y)
                        self.typ_widget.plot.achse_1.autoRange()
                else:
                    faktor = self.skalFak['Current']
                    y = [a * faktor for a in self.RezValueList]
                    if anzeigeI:
                        self.curveDict['RezI'].setData(self.RezTimeList, y)
                        self.typ_widget.plot.achse_1.autoRange()
            else:
                faktor = self.skalFak['PIDG']
                y = [a * faktor for a in self.RezValueList]
                if anzeigex:
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
                self.Fehler_Output(1, self.err_RezDef_str[self.sprache])
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
                self.Fehler_Output(1, self.err_21_str[self.sprache])
                logger.exception(self.Log_Text_Ex2_str[self.sprache])
                error = True

            # Neu verbinden von der Funktion:
            self.cb_Rezept.currentTextChanged.connect(self.RezKurveAnzeige) 
            
            if not error:
                self.Fehler_Output(0)
        else:
            self.Fehler_Output(1, self.err_14_str[self.sprache])
  
    ##########################################
    # Verworfen:
    ##########################################
    ## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
    ## da dieser später vieleicht wieder ergänzt wird!!