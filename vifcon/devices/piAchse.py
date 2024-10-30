# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
PI-Achse Gerät:
- Schnittstelle erstellen
- Werte Lesen und schreiben
- Messdatei updaten
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtCore import (
    pyqtSignal,
    QThread,
    QTimer,
    QObject
)

## Allgemein:
import logging
from serial import Serial, SerialException
import time
import math as m
import threading

## Eigene:
from .PID import PID

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class SerialMock:
    """ This class is used to mock a serial interface for debugging purposes."""

    def write(self, _):
        pass

    def readline(self):
        return "".encode()


class PIAchse(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, com_dict, test, neustart, multilog_aktiv, add_Ablauf_function, name="PI-Achse", typ = 'Antrieb'):
        """ Erstelle PI-Achse Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      device configuration (as defined in config.yml in the devices-section).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            multilog_aktiv (bool):              Multilog-Read/Send Aktiviert
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            name (str, optional):               device name.
            typ (str, optional):                device name.
        """
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Funktionsübergabe einlesen:
        self.sprache                    = sprache
        self.config                     = config
        self.neustart                   = neustart
        self.multilog_OnOff             = multilog_aktiv
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = name
        self.typ                        = typ

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
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                              'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                 'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                                                                                       'The following types are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                      'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',                                                            'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                                                                          '; Set to default:']
        self.Log_Pfad_conf_5_1  = ['; Adressauswahlcode-Fehler -> Programm zu Ende!!!',                                                             '; Address selection code error -> program ends!!!']
        self.Log_Pfad_conf_5_2  = ['; PID-Modus Aus!!',                                                                                             '; PID mode off!!']
        self.Log_Pfad_conf_5_3  = ['; Multilog-Link Aus!!',                                                                                         '; Multilog-Link off!!']
        self.Log_Pfad_conf_5_4  = ['; Mercury-Model Fehler -> Programm zu Ende!!!',                                                                 '; Mercury model error -> program ended!!!']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                  'Reason for error:']
        self.Log_Pfad_conf_7    = ['Bitte vor Nutzung Korrigieren und Config Neu Einlesen!',                                                        'Please correct and re-read config before use!']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                          'Incorrect input:']
        self.Log_Pfad_conf_8_1  = ['Fehlerhafte Typ:',                                                                                              'Incorrect type:']
        self.Log_Pfad_conf_9    = ['Die Obergrenze ist kleiner als die Untergrenze! Setze die Limits auf Default:',                                 'The upper limit is smaller than the lower limit! Set the limits to default:']
        self.Log_Pfad_conf_10   = ['zu',                                                                                                            'to']
        self.Log_Pfad_conf_11   = ['Winkelgeschwindhigkeit',                                                                                        'Angular velocity']
        self.Log_Pfad_conf_12   = ['PID-Eingang Istwert',                                                                                           'PID input actual value']
        self.Log_Pfad_conf_13   = ['Winkel',                                                                                                        'Angle']
        self.Log_Pfad_conf_14   = ['Konfiguration mit VM, MV oder MM ist so nicht möglich, da der Multilink abgeschaltet ist! Setze Default VV!',   'Configuration with VM, MV or MM is not possible because the multilink is disabled! Set default VV!']
        Log_Text_PID_N18        = ['Die Fehlerbehandlung ist falsch konfiguriert. Möglich sind max, min und error! Fehlerbehandlung wird auf error gesetzt, wodurch der alte Inputwert für den PID-Regler genutzt wird!',   'The error handling is incorrectly configured. Possible values ​​are max, min and error! Error handling is set to error, which means that the old input value is used for the PID controller!']    

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Übergeordnet:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.mercury_model  = self.config['mercury_model']  
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} mercury_model {self.Log_Pfad_conf_5_4[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.read_TT        = self.config['read_TT_log']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} read_TT_log {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.read_TT = False
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Zum Start:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.init           = self.config['start']['init']                            # Initialisierung
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.init = False
        #//////////////////////////////////////////////////////////////////////
        try: self.messZeit       = self.config['start']["readTime"]                        # Auslesezeit
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|readTime {self.Log_Pfad_conf_5[self.sprache]} 2')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.messZeit = 2
        #//////////////////////////////////////////////////////////////////////
        try: self.Ist                    = self.config['PID']["start_ist"] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|start_ist {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Ist = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.Soll              = self.config['PID']["start_soll"]
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|start_soll {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Soll = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Parameter:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.cpm            = self.config["parameter"]['cpm']                       # Counts per mm
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} parameter|cpm {self.Log_Pfad_conf_5[self.sprache]} 29572')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.cpm = 29572
        #//////////////////////////////////////////////////////////////////////
        try: self.mvtime         = self.config["parameter"]['mvtime']                    # Delay-Zeit MV-Befehl (Auslesen der Geschwindigkeit)
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} parameter|mvtime {self.Log_Pfad_conf_5[self.sprache]} 25')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.mvtime = 25
        #//////////////////////////////////////////////////////////////////////
        try: self.nKS        = self.config['parameter']['nKS_Aus']                     # Nachkommerstellen
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} parameter|nKS_Aus {self.Log_Pfad_conf_5[self.sprache]} 3')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.nKS = 3
        #//////////////////////////////////////////////////////////////////////
        try: self.adv = self.config["parameter"]['adv']                      # Adressauswahlcode
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} parameter|adv {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Limits:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.oGPos          = self.config["limits"]['maxPos']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxPos {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGPos = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGPos          = self.config["limits"]['minPos']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minPos {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGPos = 0
        #//////////////////////////////////////////////////////////////////////
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
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Schnittstelle:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Loop = self.config['serial-loop-read']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} serial-loop-read {self.Log_Pfad_conf_5[self.sprache]} 10')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Loop = 10
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.unit_PIDIn             = self.config['PID']['Input_Size_unit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Size_unit {self.Log_Pfad_conf_5[self.sprache]} mm')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.unit_PIDIn = 'mm'
        #//////////////////////////////////////////////////////////////////////
        error_PID = False
        try: self.PID_Config             = self.config['PID']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID {self.Log_Pfad_conf_5_2[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            error_PID = True
            self.PID_Config = {}
            self.PID_Aktiv  = 0 
        #//////////////////////////////////////////////////////////////////////
        if not error_PID:
            try: self.PID_Aktiv = self.config['PID']['PID_Aktiv']
            except Exception as e: 
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|PID_Aktiv {self.Log_Pfad_conf_5[self.sprache]} False')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
                self.PID_Aktiv = 0 
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Option = self.config['PID']['Value_Origin'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Value_Origin {self.Log_Pfad_conf_5[self.sprache]} VV')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Option = 'VV' 
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Sample_Time        = self.config['PID']['sample']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|sample {self.Log_Pfad_conf_5[self.sprache]} 500')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Sample_Time = 500 
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Input_Limit_Max    = self.config['PID']['Input_Limit_max']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_max {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Input_Limit_Max  = 1 
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Input_Limit_Min    = self.config['PID']['Input_Limit_min'] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_min {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Input_Limit_Min = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Input_Error_Option = self.config['PID']['Input_Error_option']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Error_option {self.Log_Pfad_conf_5[self.sprache]} error')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Input_Error_Option = 'error' 
        #//////////////////////////////////////////////////////////////////////
        try: self.M_device_ist           = self.config['multilog']['read_trigger_ist'] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|read_trigger_ist {self.Log_Pfad_conf_5_3[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.M_device_ist = ''
            self.multilog_OnOff = False
        #//////////////////////////////////////////////////////////////////////
        try: self.M_device_soll          = self.config['multilog']['read_trigger_soll'] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|read_trigger_soll {self.Log_Pfad_conf_5_3[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.M_device_soll = ''
            self.multilog_OnOff = False
        #//////////////////////////////////////////////////////////////////////
        try: self.sensor_ist             = self.config['PID']['Multilog_Sensor_Ist']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Multilog_Sensor_Ist {self.Log_Pfad_conf_5_3[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.sensor_ist = ''
            self.multilog_OnOff = False
        #//////////////////////////////////////////////////////////////////////
        try: self.sensor_soll             = self.config['PID']['Multilog_Sensor_Soll']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Multilog_Sensor_Soll {self.Log_Pfad_conf_5_3[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.sensor_soll = ''
            self.multilog_OnOff = False

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Config-Fehler und Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID-Aktiviert:
        if not type(self.PID_Aktiv) == bool and not self.PID_Aktiv in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Aktiv - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Aktiv}')
            self.PID_Aktiv = 0
        ### Mercury-Model:
        if not self.mercury_model in ['C863', 'C862']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} mercury_model - {self.Log_Pfad_conf_2[self.sprache]} [C862, C863] - {self.Log_Pfad_conf_5_4[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8[self.sprache]} {self.mercury_model}')
            exit()
        ### Loge TT (Zielwerte):
        if not type(self.read_TT) == bool and not self.read_TT in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} read_TT_log - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.read_TT}')
            self.read_TT = 0
        ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0
        ### Messzeit:
        if not type(self.messZeit) in [int, float] or not self.messZeit >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} readTime - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 2 - {self.Log_Pfad_conf_8[self.sprache]} {self.messZeit}')
            self.messZeit = 2
        ### PID-Start-Soll:
        if not type(self.Soll) in [float, int] or not self.Soll >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_soll - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.Soll}')
            self.Soll = 0
        ### PID-Start-Ist:
        if not type(self.Ist) in [float, int] or not self.Ist >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_ist - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.Ist}')
            self.Ist = 0
        ### CPM:
        if not type(self.cpm) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} cpm - {self.Log_Pfad_conf_2_1[self.sprache]} [Int] - {self.Log_Pfad_conf_3[self.sprache]} 29752 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.cpm)}')
            self.cpm = 29752
        ### Nachkommerstellen:
        if not type(self.nKS) in [int] or not self.nKS >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nKS_Aus - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 3 - {self.Log_Pfad_conf_8[self.sprache]} {self.nKS}')
            self.nKS = 3
        ### MV-Delay-Zeit:
        if not type(self.mvtime) == int or not self.mvtime >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} mvtime - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 25 - {self.Log_Pfad_conf_8[self.sprache]} {self.mvtime}')
            self.mvtime = 25
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
        ### Position-Limit:
        if not type(self.oGPos) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGPos)}')
            self.oGPos = 1
        if not type(self.uGPos) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGPos)}')
            self.uGPos = 0
        if self.oGPos <= self.uGPos:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
            self.uGPos = 0
            self.oGPos = 1
        ### Adressauswahlcode:
        if not type(self.adv) == str:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} adv - {self.Log_Pfad_conf_2_1[self.sprache]} [str] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.adv)}')
            exit()
        ### PID Sample Zeit:
        if not type(self.PID_Sample_Time) in [int] or not self.PID_Sample_Time >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} sample - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 500 - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Sample_Time}')
            self.PID_Sample_Time = 500 
        ### Multilog_Sensor Ist:
        if not type(self.sensor_ist) == str:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Multilog_Sensor_Ist - {self.Log_Pfad_conf_2_1[self.sprache]} [str] - {self.Log_Pfad_conf_5_3[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.sensor_ist)}')
            self.multilog_OnOff = False
        ### Multilog_Sensor Soll:
        if not type(self.sensor_soll) == str:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Multilog_Sensor_Soll - {self.Log_Pfad_conf_2_1[self.sprache]} [str] - {self.Log_Pfad_conf_5_3[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.sensor_soll)}')
            self.multilog_OnOff = False
        ### read-Trigger Multilog Ist:
        if not type(self.M_device_ist) == str:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} read_trigger_ist - {self.Log_Pfad_conf_2_1[self.sprache]} [str] - {self.Log_Pfad_conf_5_3[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.M_device_ist)}')
            self.multilog_OnOff = False
        ### read-Trigger Multilog Soll:
        if not type(self.M_device_soll) == str:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} read_trigger_soll - {self.Log_Pfad_conf_2_1[self.sprache]} [str] - {self.Log_Pfad_conf_5_3[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.M_device_soll)}')
            self.multilog_OnOff = False
        ### PID-Wert-Fehler:
        if self.PID_Input_Error_Option not in ['min', 'max', 'error']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N18[sprache]}')
            self.PID_Input_Error_Option = 'error'
        ### PID-Start-Soll:
        if not type(self.Soll) in [float, int] or not self.Soll >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_soll - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.Soll}')
            self.Soll = 0
        ### PID-Start-Ist:
        if not type(self.Ist) in [float, int] or not self.Ist >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_ist - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.Ist}')
            self.Ist = 0
        ### PID-Limit:
        if not type(self.PID_Input_Limit_Max) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_max - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.PID_Input_Limit_Max)}')
            self.PID_Input_Limit_Max = 1
        if not type(self.PID_Input_Limit_Min) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_min - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.PID_Input_Limit_Min)}')
            self.PID_Input_Limit_Min = 0
        if self.PID_Input_Limit_Max <= self.PID_Input_Limit_Min:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_12[self.sprache]})')
            self.PID_Input_Limit_Min = 0
            self.PID_Input_Limit_Max = 1
        ### While-Loop:
        if not type(self.Loop) == int or not self.Loop >= 1:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} serial-loop-read - {self.Log_Pfad_conf_2[self.sprache]} Integer (>=1) - {self.Log_Pfad_conf_3[self.sprache]} 10 - {self.Log_Pfad_conf_8[self.sprache]} {self.Loop}')
            self.Loop = 10

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Andere:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.akPos              = 0
        self.last_Pos           = 0
        self.Min_End            = False
        self.Max_End            = False
        self.Limit_Stop_Text    = -1
        self.Limit_stop         = False
        self.value_name         = {'IWs': 0, 'IWv': 0, 'SWv': 0, 'SWxPID': self.Soll, 'IWxPID': self.Ist}

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                                   'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',                'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                                 'Error reason (interface structure):']
        self.Log_Text_64_str    = ['Das Gerät konnte nicht ausgelesen werden.',                                             'The device could not be read.']
        self.Log_Text_64_1_str  = ['Das Gerät konnte nicht angesprochen werden.',                                           'The device could not be addressed.']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                                          'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                       'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                  'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                       'No measurement data recording active!']
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                'Error reason (send):']
        self.Log_Text_136_str   = ['Fehler Grund (Auslesen):',                                                              'Error reason (reading):']
        self.Log_Text_158_str   = ['Zielposition:',                                                                         'Target position:']
        self.Log_Text_159_str   = ['Versuch',                                                                               'Attempt']
        self.Log_Text_160_str   = ['funktioniert nicht!',                                                                   "doesn't work!"]
        self.Log_Text_161_str   = ['Mercury Adresse (Board):',                                                              'Mercury address (board):']
        self.Log_Text_162_str   = ['Status:',                                                                               'Status:']
        self.Log_Text_163_str   = ['Version:',                                                                              'Version:']
        self.Log_Text_164_str   = ['Startposition:',                                                                        'Starting position:']
        self.Log_Text_165_str   = ['mm',                                                                                    'mm']
        self.Log_Text_PID_str   = ['Start des PID-Threads!',                                                                                                                                                                'Start of the PID thread!']
        Log_Text_PID_N1         = ['Die Konfiguration',                                                                                                                                                                     'The configuration']
        Log_Text_PID_N2         = ['existiert nicht! Möglich sind nur VV, VM, MM oder MV. Nutzung von Default VV!',                                                                                                         'does not exist! Only VV, VM, MM or MV are possible. Use default VV!']
        Log_Text_PID_N2_1       = ['ist für das Gerät noch nicht umgesetzt! Nutzung von Default VV!',                                                                                                                       'is not yet implemented for the device! Use of default VV!']
        Log_Text_PID_N3         = ['Gewählter PID-Modus ist: ',                                                                                                                                                             'Selected PID mode is: ']
        Log_Text_PID_N4         = ['Istwert von Multilog',                                                                                                                                                                  'Actual value from Multilog']
        Log_Text_PID_N5         = ['Istwert von VIFCON',                                                                                                                                                                    'Actual value of VIFCON']
        Log_Text_PID_N6         = ['Sollwert von Multilog',                                                                                                                                                                 'Setpoint from Multilog']
        Log_Text_PID_N7         = ['Sollwert von VIFCON',                                                                                                                                                                   'Setpoint from VIFCON']
        Log_Text_PID_N8         = ['Istwert wird von Multilog-Sensor',                                                                                                                                                      'Actual value is from multilog sensor']
        Log_Text_PID_N9         = ['Sollwert wird von Multilog-Sensor',                                                                                                                                                     'Setpoint is from Multilog sensor']
        Log_Text_PID_N10        = ['geliefert!',                                                                                                                                                                            'delivered!']
        self.Log_Text_PID_N11   = ['Bei der Multilog-PID-Input-Variable gab es einen Fehler!',                                                                                                                              'There was an error with the multilog PID input variable!']
        self.Log_Text_PID_N12   = ['Fehler Grund:',                                                                                                                                                                         'Error reason:']
        Log_Text_PID_N13        = ['durch das Gerät',                                                                                                                                                                       'through the device']
        self.Log_Text_PID_N14   = ['Input-Fehler: Input Werte sind NAN-Werte!',                                                                                                                                             'Input error: Input values ​​are NAN values!']
        self.Log_Text_PID_N15   = ['Input Werte überschreiten das Maximum von',                                                                                                                                             'Input values ​​exceed the maximum of']
        self.Log_Text_PID_N16   = ['Input Werte unterschreiten das Minimum von',                                                                                                                                            'Input values ​​fall below the minimum of']
        self.Log_Text_PID_N17   = ['Input Fehler: Input-Wert ist nicht von Typ Int oder Float! Variablen Typ:',                                                                                                             'Input error: Input value is not of type Int or Float! Variable type:']
        self.Log_Text_PID_N19   = ['Auslesefehler bei Multilog-Dictionary!',                                                                                                                                                'Reading error in multilog dictionary!']
        self.Log_Text_PID_N20   = [f'{self.unit_PIDIn} - tatsächlicher Wert war',                                                                                                                                           f'{self.unit_PIDIn} - tatsächlicher Wert war']
        Log_Text_PID_N21        = ['Multilog Verbindung wurde in Config als Abgestellt gewählt! Eine Nutzung der Werte-Herkunft mit VM, MV oder MM ist so nicht möglich! Nutzung von Default VV!',                          'Multilog connection was selected as disabled in config! Using the value origin with VM, MV or MM is not possible! Use of default VV!']
        self.Log_Test_PID_N22   = [f'{self.unit_PIDIn}',                                                                                                                                                                    f'{self.unit_PIDIn}']
        self.Log_Text_PID_N23   = ['PID-Modus wird nicht aktiviert!',                                                                                                                                                       'PID mode is not activated!']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                                                                                                          'Limit range']
        self.Log_Text_LB_4      = ['bis',                                                                                                                                                                                   'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                                                                                                           'after update']
        self.Log_Text_LB_6      = ['PID',                                                                                                                                                                                   'PID']
        self.Log_Text_LB_7      = ['Output',                                                                                                                                                                                'Outout']
        self.Log_Text_LB_8      = ['Input',                                                                                                                                                                                 'Input']
        self.Log_Text_LB_unit   = ['mm/s',                                                                                                                                                                                  'mm/s']
        self.Log_Text_217_str   = ['Maximum Limit erreicht!',                                                                                                                                                               'Maximum limit reached!']
        self.Log_Text_218_str   = ['Minimum Limit erreicht!',                                                                                                                                                               'Minimum limit reached!']
        ## Ablaufdatei:                                                                                             
        self.Text_51_str        = ['Initialisierung!',                                                                                                                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                                                                       'Initialization Failed!']
        self.Text_58_str        = ['Befehl MR erfolgreich gesendet!',                                                                                                                                                       'MR command sent successfully!']
        self.Text_59_str        = ['Befehl SV erfolgreich gesendet!',                                                                                                                                                       'SV command sent successfully!']
        self.Text_60_str        = ['Befehl DH erfolgreich gesendet!',                                                                                                                                                       'DH command sent successfully!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                                                                                                                        'Sending failed!']
        self.Text_62_str        = ['Achse wurde erfolgreich angehalten!',                                                                                                                                                   'Axis was stopped successfully!']
       
        #---------------------------------------
        # Schnittstelle:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_60_str[self.sprache]}")
        try:
            if not test:
                com_ak = ''
                for com in com_dict:
                    if com == self.config['serial-interface']['port']:
                        com_ak = com
                        break
                if com_ak == '':
                    self.serial = Serial(**config["serial-interface"])
                else:
                    self.serial = com_dict[com_ak]
        except SerialException as e:
            self.serial = SerialMock()
            logger.warning(f"{self.device_name} - {self.Log_Text_61_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_62_str[self.sprache]}")
            exit()

        #---------------------------------------
        # Befehle:
        #---------------------------------------
        steuer = '0D'                                                   # Befehl-Abschlusszeichen (\r)
        self.t1 = bytearray.fromhex(self.adv)                           # Adressauswahlcode vorbereiten zum senden
        self.t3 = bytearray.fromhex(steuer)                             # Befehl-Abschlusszeichen vorbereiten zum senden

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        if self.uGv < 0:     controll_under_Null = 0
        else:                controll_under_Null = self.uGv
        self.PID = PID(self.sprache, self.device_name, self.PID_Config, self.oGv, controll_under_Null)
        ## Info und Warnungen: --> Überarbeiten da VIFCON Istwert noch nicht vorhanden!
        if not self.multilog_OnOff and self.PID_Option in ['MV', 'MM', 'VM']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N21[sprache]}')
            self.PID_Option = 'VV'
        # elif self.PID_Option in ['MM', 'VM']:
        #     logger.warning(f'{self.device_name} - {Log_Text_PID_N1[sprache]} {self.PID_Option} {Log_Text_PID_N2_1[self.sprache]}')
        #     self.PID_Option = 'VV'
        elif self.PID_Option not in ['MV', 'VV', 'MM', 'VM']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N1[sprache]} {self.PID_Option} {Log_Text_PID_N2[self.sprache]}')
            self.PID_Option = 'VV'
        ### Herkunft Istwert:
        if self.PID_Option[0] == 'V':
            teil_1 = Log_Text_PID_N5
        elif self.PID_Option[0] == 'M':
            teil_1 = Log_Text_PID_N4 
        ### Herkunft Sollwert:
        if self.PID_Option[1] == 'V':
            teil_2 = Log_Text_PID_N7
        elif self.PID_Option[1] == 'M':
            teil_2 = Log_Text_PID_N6 
        logger.info(f'{self.device_name} - {Log_Text_PID_N3[self.sprache]}{self.PID_Option} ({teil_1[self.sprache]}, {teil_2[self.sprache]})')

        if self.PID_Aktiv:
            ## PID-Thread:
            self.PIDThread = QThread()
            self.PID.moveToThread(self.PIDThread)
            logger.info(f'{self.device_name} - {self.Log_Text_PID_str[self.sprache]}') 
            self.PIDThread.start()
            self.signal_PID.connect(self.PID.InOutPID)
            ## Timer:
            self.timer_PID = QTimer()                                              # Reaktionszeittimer (ruft die Geräte auf, liest aber nur unter bestimmten Bedingungen!)
            self.timer_PID.setInterval(self.PID_Sample_Time)
            self.timer_PID.timeout.connect(self.PID_Update)
            self.timer_PID.start()
            ### PID-Timer Thread:
            #self.PIDThreadTimer = threading.Thread(target=self.PID_Update)
            #self.PIDThreadTimer.start()
        else:
            logger.info(f'{self.device_name} - {self.Log_Text_PID_N23[self.sprache]}')
        ## Multilog-Lese-Variable für die Daten:
        self.mult_data              = {}
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]}: {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {self.Log_Text_LB_unit[self.sprache]}')
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]}: {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max} {self.unit_PIDIn}')   
        if self.PID_Option[0] == 'M':
            logger.info(f'{Log_Text_PID_N8[self.sprache]} {self.sensor_ist} {Log_Text_PID_N13[self.sprache]} {self.M_device_ist} {Log_Text_PID_N10[self.sprache]}')
        if self.PID_Option[1] == 'M':
            logger.info(f'{Log_Text_PID_N9[self.sprache]} {self.sensor_soll} {Log_Text_PID_N13[self.sprache]} {self.M_device_soll} {Log_Text_PID_N10[self.sprache]}')
        self.PID_Ist_Last = self.Ist

    ##########################################
    # Schnittstelle (Schreiben):
    ##########################################
    def write(self, write_Okay, write_value):
        ''' Sende Befehle an die Achse um Werte zu verändern.

        Args:
            write_Okay (dict):  beinhaltet Boolsche Werte für das was beschrieben werden soll!
            write_value (dict): beinhaltet die Werte die geschrieben werden sollen
        '''
        #++++++++++++++++++++++++++++++++++++++++++
        # Start:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Start'] and not self.neustart:
            self.Start_Werte()
            write_Okay['Start'] = False
        
        #++++++++++++++++++++++++++++++++++++++++++
        # Update Limit:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Update Limit']:
            ## Geschwindigkeit/PID-Output:
            self.PID.OutMax = write_value['Limits'][0]
            if write_value['Limits'][1] < 0:    self.PID.OutMin = 0
            else:                               self.PID.OutMin = write_value['Limits'][1]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {self.Log_Text_LB_unit[self.sprache]}')
            ## PID-Input:
            self.PID_Input_Limit_Max = write_value['Limits'][4]
            self.PID_Input_Limit_Min = write_value['Limits'][5]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max} {self.unit_PIDIn}')
            ## Position:
            self.oGPos = write_value['Limits'][2]
            self.uGPos = write_value['Limits'][3]
            write_Okay['Update Limit'] = False
        
        #++++++++++++++++++++++++++++++++++++++++++
        # Normaler Betrieb:
        #++++++++++++++++++++++++++++++++++++++++++
        if not write_Okay['PID']:  
            ## Sollwert Lesen (v):
            speed_vorgabe = write_value['Speed']
            PID_write_V = False
        #++++++++++++++++++++++++++++++++++++++++++    
        # PID-Regler:
        #++++++++++++++++++++++++++++++++++++++++++
        elif write_Okay['PID']:
            #---------------------------------------------
            ## Auswahl Istwert:
            #---------------------------------------------
            ### VIFCON:
            if self.PID_Option[0] == 'V':
                print(['Noch nicht vollkommen implementiert! Hier wird Istwert auf Sollwert gesetzt!', 'Not yet fully implemented! Here the actual value is set to the target value!'][self.sprache])
                self.Ist = self.Soll
            ### Multilog:
            elif self.PID_Option[0] == 'M':
                try:
                    if self.sensor_ist.lower() == 'no sensor':  self.Ist = self.mult_data[self.M_device_ist]
                    else:                                       self.Ist = self.mult_data[self.M_device_ist][self.sensor_ist]
                except Exception as e:
                    logger.warning(f"{self.device_name} - {self.Log_Text_PID_N19[self.sprache]} ({self.M_device_ist})")
                    logger.exception(f"{self.device_name} - {self.Log_Text_PID_N12[self.sprache]}")
            ### Istwert Filter:
            error_Input = False
            try:
                #### Nan-Werte:
                if m.isnan(self.Ist):
                    logger.warning(f"{self.device_name} - {self.Log_Text_PID_N14[self.sprache]}")
                    error_Input = True
                #### Kein Float oder Integer:
                elif type(self.Ist) not in [int, float]:
                    logger.warning(f"{self.device_name} - {self.Log_Text_PID_N17[self.sprache]} {type(self.Ist)}")
                    error_Input = True
                #### Input-Wert überschreitet Maximum:
                elif self.Ist > self.PID_Input_Limit_Max:
                    logger.debug(f"{self.device_name} - {self.Log_Text_PID_N15[self.sprache]} {self.PID_Input_Limit_Max} {self.Log_Text_PID_N20[self.sprache]} {self.Ist}{self.Log_Test_PID_N22[self.sprache]}")
                    self.Ist = self.PID_Input_Limit_Max
                #### Input-Wert unterschreitet Minimum:
                elif self.Ist < self.PID_Input_Limit_Min:
                    logger.debug(f"{self.device_name} - {self.Log_Text_PID_N16[self.sprache]} {self.PID_Input_Limit_Min} {self.Log_Text_PID_N20[self.sprache]} {self.Ist}{self.Log_Test_PID_N22[self.sprache]}")
                    self.Ist = self.PID_Input_Limit_Min
            except Exception as e:
                error_Input = True
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_N11[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_PID_N12[self.sprache]}")
            ### Fehler-Behandlung:
            if error_Input:
                #### Input auf Maximum setzen:
                if self.PID_Input_Error_Option == 'max':
                    self.Ist = self.PID_Input_Limit_Max
                #### Input auf Minimum setzen:
                elif self.PID_Input_Error_Option == 'min':
                    self.Ist = self.PID_Input_Limit_Min
                #### Input auf letzten Input setzen:
                elif self.PID_Input_Error_Option == 'error':
                    self.Ist = self.PID_Ist_Last
            else:
                self.PID_Ist_Last = self.Ist
            #---------------------------------------------
            ## Auswahl Sollwert:
            #---------------------------------------------
            ### VIFCON:
            if self.PID_Option[1] == 'V':
                self.Soll = write_value['PID-Sollwert']
            ### Multilog:
            elif self.PID_Option[1] == 'M':
                try:
                    if self.sensor_soll.lower() == 'no sensor':     self.Soll = self.mult_data[self.M_device_soll]
                    else:                                           self.Soll = self.mult_data[self.M_device_soll][self.sensor_soll] 
                except Exception as e:
                    logger.warning(f"{self.device_name} - {self.Log_Text_PID_N19[self.sprache]} ({self.M_device_soll})")  
                    logger.exception(f"{self.device_name} - {self.Log_Text_PID_N12[self.sprache]}")
            #---------------------------------------------    
            ## Schreibe Werte:
            #---------------------------------------------
            speed_vorgabe = self.PID_Out * self.cpm
            PID_write_V = True
        
        #++++++++++++++++++++++++++++++++++++++++++
        # Lese Aktuelle Position aus:
        #++++++++++++++++++++++++++++++++++++++++++
        if self.init:
            self.akPos = self.read_TX('TP', 'P:')
            if self.akPos == m.nan: self.akPos = self.last_Pos
            else:                   self.last_Pos = self.akPos

        #++++++++++++++++++++++++++++++++++++++++++
        # Limit Kontrolle:
        #++++++++++++++++++++++++++++++++++++++++++
        if self.akPos > self.oGPos and not self.Max_End:
            self.Max_End = True
            logger.warning(f'{self.device_name} - {self.Log_Text_217_str[self.sprache]}')
            self.Limit_Stop_Text    = 0
            self.Limit_stop         = True
            write_Okay['Stopp']     = True
        if self.akPos < self.uGPos and not self.Min_End:
            self.Min_End = True
            logger.warning(f'{self.device_name} - {self.Log_Text_218_str[self.sprache]}') 
            self.Limit_Stop_Text    = 1
            self.Limit_stop         = True
            write_Okay['Stopp']     = True
        if self.akPos > self.uGPos and self.akPos < self.oGPos:
            self.Max_End = False
            self.Min_End = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Sende Stopp:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Stopp']:
            self.stopp()
            # Rücksetzen aller Bewegungen:
            write_Okay['Stopp'] = False
            write_Okay['Position'] = False
            write_Okay['Speed'] = False  
        #++++++++++++++++++++++++++++++++++++++++++                                  
        # Schreiben, wenn nicht Stopp:
        #++++++++++++++++++++++++++++++++++++++++++
        else:
            try:
                ## Sende Position:
                if write_Okay['Sende Position']:
                    fahre = round(write_value["Position"] * int(self.cpm))                                      # Befehl bekommt einen Integer!
                    Befehl = f'MR{fahre}'
                    self.serial.write(self.t1+Befehl.encode()+self.t3)
                    write_Okay['Sende Position'] = False
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_58_str[self.sprache]}')       
                ## Sende Geschwindigkeit:
                if write_Okay['Sende Speed']:
                    Befehl = f'SV{round(write_value["Speed"])}'
                    self.serial.write(self.t1+Befehl.encode()+self.t3)
                    write_Okay['Sende Speed'] = False 
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_59_str[self.sprache]}')      
                ## PID-Modus:
                elif PID_write_V:
                    Befehl = f'SV{round(speed_vorgabe)}'
                    self.serial.write(self.t1+Befehl.encode()+self.t3)
                    PID_write_V = False
                ## Sende Define-Home:
                if write_Okay['Define Home']:
                    Befehl = 'DH'
                    self.serial.write(self.t1+Befehl.encode()+self.t3)
                    write_Okay['Define Home'] = False 
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_60_str[self.sprache]}')
                    if self.oGPos == 0:        self.Max_End = True
                    else:                      self.Max_End = False                       
                    if self.uGPos == 0:        self.Min_End = True                    
                    else:                      self.Min_End = False
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]}')           

    def stopp(self):
        ''' Halte Motor an und setze STA-LED auf rot ''' 
        Befehl = 'AB'                                                                                            
        try: 
            self.serial.write(self.t1+Befehl.encode()+self.t3)
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_1_str[self.sprache]} ({Befehl})")
            logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
        time.sleep(0.1)                                                 # Kurze Verzögerung, damit der Motor stehen bleiben kann und die Zielposition geupdatet werden kann
        Befehl = 'MF'
        try: 
            self.serial.write(self.t1+Befehl.encode()+self.t3)              # Status Lampe leuchtet nun Rot
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_62_str[self.sprache]}') 
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_1_str[self.sprache]} ({Befehl})")
            logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")         

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def read(self):
        ''' Sende Befehle an die Achse um Werte auszulesen.

        Return: 
            Aktuelle Werte (dict)   - self.value_name
        '''
        try:
            # Lese Ist-Position:
            position = self.read_TX('TP','P:')
            self.value_name['IWs'] = position       # Einheit: mm

            # Lese Geschwindigkeit:
            speed = self.read_TX('TV', 'V:')
            self.value_name['IWv'] = speed          # Einheit: mm/s

            # Lese Geschwindigkeit:
            speedS = self.read_TX('TY', 'Y:')
            self.value_name['SWv'] = speedS         # Einheit: mm/s

            # Lese Zielposition in Log-Datei:
            if self.read_TT:
                ziel = self.send_read_command('TT', 'T:')
                logger.debug(f"{self.device_name} - {self.Log_Text_158_str[self.sprache]} {ziel/int(self.cpm)}")

            # PID-Modus:
            self.value_name['SWxPID'] = self.Soll
            self.value_name['IWxPID'] = self.Ist

        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")

        return self.value_name
    
    def read_TX(self, komando, start_str):
        '''Lese die Anfrage an das Gerät aus
        Args:
            komando (str):      Befehl für die Anfrage (z.B. TP, TY, TV, TT)
            start_str (str):    Beginn der Antwort     (z.B. P:, Y:, V:, T:)
        Return:
            ans (float):   aktuelle Antwort des Gerätes
        '''
        # Geschwindigkeit hängt vom Modell ab:
        delay = 0.01
        if komando == 'TV' and self.mercury_model == 'C862':
            komando = f'TV{self.mvtime}'
            delay = self.mvtime/1000

        # Senden und Auslesen:                                              
        ans = self.send_read_command(komando, start_str, delay)
        if not ans == m.nan:
            if komando == 'TV' and self.mercury_model == 'C862':
                ans = ans*1000/self.mvtime
            ans = round(ans/int(self.cpm), self.nKS)

        return ans

    def send_read_command(self, Befehl, Antwortbegin, delay = 0.01):
        ''' Sendet den Lese-Befehl an die Achse.

        Args:
            Befehl (str):               String mit Befehl (zwei Buchstaben)                 (z.B. TP)
            Antwortbegin (str):         String für die ersten beiden Charakter der Antwort  (z.B. P:)
            delay (time, optional):     Verzögerungs Zeit in s
        Return:
            ant (int):                        Umgewandelte Zahl 
        '''
        n = 0
        try:
            self.serial.write(self.t1+Befehl.encode()+self.t3)
            time.sleep(delay)
            ant = self.serial.readline().decode()
            ant = self.entferneSteuerzeichen(ant)
            while n != self.Loop:
                if Antwortbegin in ant and len(ant) == 13:
                    ant = self.wertSchneiden(ant, Antwortbegin)
                    break
                else:
                    logger.warning(f'{self.Log_Text_159_str[self.sprache]} {n} {self.Log_Text_160_str[self.sprache]} ({Befehl})')
                    n += 1
                self.serial.write(self.t1+Befehl.encode()+self.t3)
                time.sleep(delay)
                ant = self.serial.readline().decode()
                ant = self.entferneSteuerzeichen(ant)
                    
                if n == self.Loop:
                    ant = m.nan
        except:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]} ({Befehl})")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")
            ant = m.nan
        return ant

    def entferneSteuerzeichen(self, String):
        ''' Entfernt bestimmte Steruzeichen aus dem String.

        Args:
            String (str): String aus dem die Steuerzeichen entfernt werden sollen.
        Return:
            String (str): beschnittender String
        '''
        weg_List = ['\r', '\n', '\x03']
        for n in weg_List:
            String = String.replace(n, '')
        return String

    def wertSchneiden(self, String, Art):
        ''' Schneidet den ausgelesenen String zurecht.

        Args:
            String (str):   String der beschnitten werden soll.
            Art (str):      Anfangsstring des ausgelesenen Strings. Zwei Zeichen - Buchstabe und Doppelpunkt!
                            Wird ausgeschnitten!
        Return:
            akvalue (int):  Ausgelesener Wert
        '''
        akvalue = String.replace(Art, '')   # Auschneiden des Befehltyps
        sign = akvalue[0]                   # Auslesen des Vorzeichens
        akvalue = int(akvalue[1:])          # Umwandeln des Wertes in einen Integer
        if sign == '-':                     # Beachtung des Vorzeichens
            akvalue = akvalue * -1
        return akvalue

    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung des Gerätes PI_Achse. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
        if not self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_51_str[self.sprache]}')
            logger.info(f"{self.device_name} - {self.Text_51_str[self.sprache]}")
            # Schnittstelle prüfen:
            try: 
                ## Start Werte abfragen:
                self.Start_Werte()
                ## Setze Init auf True:
                self.init = True
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_68_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_69_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_52_str[self.sprache]}')
                self.init = False
        else:
            logger.info(f"{self.device_name} - {self.Log_Text_70_str[self.sprache]}")
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Log_Text_70_str[self.sprache]}')
            self.init = False

    def Start_Werte(self):
        '''Lese und Schreibe bestimmte Werte bei Start des Gerätes!'''
        try:
            ## Board Adresse:
            self.serial.write(self.t1+'TB'.encode()+self.t3)
            ant_TB = self.serial.readline().decode()
            ant_TB = self.entferneSteuerzeichen(ant_TB)
            logger.info(f"{self.device_name} - {self.Log_Text_161_str[self.sprache]} {ant_TB}")
            ## Status:
            self.serial.write(self.t1+'TS'.encode()+self.t3)
            ant_ST = self.serial.readline().decode()
            ant_ST = self.entferneSteuerzeichen(ant_ST)
            logger.info(f"{self.device_name} - {self.Log_Text_162_str[self.sprache]} {ant_ST}")
            ## Version:
            self.serial.write(self.t1+'VE'.encode()+self.t3)
            ant_VE = self.serial.readline().decode()
            ant_VE = self.entferneSteuerzeichen(ant_VE)
            logger.info(f"{self.device_name} - {self.Log_Text_163_str[self.sprache]} {ant_VE}")
            ## Start-Position auslesen:
            self.serial.write(self.t1+'TP'.encode()+self.t3)
            ant = self.serial.readline().decode()
            if 'P:' in ant:
                self.akPos = self.read_TX('TP', 'P:')
                if self.akPos == m.nan:
                    self.akPos = self.last_Pos
                    zusatz = '(Error Nan)'
                else: 
                    zusatz = ''
                    self.last_Pos = self.akPos
                logger.info(f"{self.device_name} - {self.Log_Text_164_str[self.sprache]} {self.akPos} {self.Log_Text_165_str[self.sprache]} {zusatz}")
        except:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")

###################################################
# Messdatendatei erstellen und beschrieben:
###################################################
    def messdaten_output(self, pfad="./"):
        """Erstelle für das Gerät eine csv-Datei mit den Daten.

        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        PID_x_unit = self.unit_PIDIn
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = f"# datetime,s,mm,mm/s,mm/s,{PID_x_unit},{PID_x_unit},\n"
        #scaling = f"# -,-,{self.}"
        header = "time_abs,time_rel,Ist-Position,Ist-Geschwindigkeit,Soll-Geschwindigkeit,Soll-x_PID-Modus_A,Ist-x_PID-Modus_A,\n"
        if self.messZeit != 0:                                          # Erstelle Datei nur wenn gemessen wird!
            logger.info(f"{self.device_name} - {self.Log_Text_71_str[self.sprache]} {self.filename}")
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(units)
                f.write(header)
        else:
            logger.info(f"{self.device_name} - {self.Log_Text_72_str[self.sprache]}")

    def update_output(self, daten, absolut_Time, relativ_Time):
        '''Schreibe die Daten in die Datei.

        Args:
            daten (Dict):               Dictionary mit den Daten in der Reihenfolge: 'IWs', 'IWv'
            absolut_Time (datetime):    Absolute Zeit der Messung (Zeitstempel)
            relativ_Time (float):       Zeitpunkt der Messung zum Startzeiptpunkt.
        '''
        line = f"{absolut_Time.isoformat(timespec='milliseconds').replace('T', ' ')},{relativ_Time},"
        for size in daten:
            line = line + f'{daten[size]},'
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f'{line}\n')
    
    ##########################################
    # PID-Regler:
    ##########################################
    def PID_Update(self):
        '''PID-Regler-Thread-Aufruf'''
        if self.PID_Aktiv:
            if not self.PID.PID_speere:
                self.signal_PID.emit(self.Ist, self.Soll, False, 0)
                self.PID_Out = self.PID.Output
    
##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''
    # def read_TP(self):
    #     '''Lese die Aktuelle Position
        
    #     Return:
    #         position (float):   aktuelle position
    #     '''
    #     position = self.send_read_command('TP', 'P:')
    #     position = round(position/int(self.cpm), self.nKS)

    #     return position
    
    # def read_TY(self):
    #     '''Lese die Aktuelle Programmierte Geschwindigkeit
        
    #     Return:
    #         position (float):   aktuelle Sollgeschwindigkeit
    #     '''
    #     position = self.send_read_command('TY', 'Y:')
    #     position = round(position/int(self.cpm), self.nKS)

    #     return position

    # def read_TV(self):
    #     '''Lese die Aktuelle Geschwindigkeit
        
    #     Return:
    #         speed (float):  aktuelle Geschwindigkeit
    #     '''
    #     if self.mercury_model == 'C862':
    #         speed = self.send_read_command(f'TV{self.mvtime}', 'V:', self.mvtime/1000) 
    #         speed = speed*1000/self.mvtime
    #     elif self.mercury_model == 'C863':
    #         speed = self.send_read_command(f'TV', 'V:')   
    #     speed = round(speed/int(self.cpm), self.nKS) 

    #     return speed