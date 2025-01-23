# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Educrys-Achse Gerät:
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
# import threading
import datetime

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


class EducrysAntrieb(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, config_dat, com_dict, test, neustart, multilog_aktiv, Log_WriteReadTime, add_Ablauf_function, name="Educrys-Achse", typ = 'Antrieb'):
        """ Erstelle Nemo-Achse Lin Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      device configuration (as defined in config.yml in the devices-section).
            config_dat (string):                Datei-Name der Config-Datei
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            multilog_aktiv (bool):              Multilog-Read/Send Aktiviert
            Log_WriteReadTime (bool):           Logge die Zeit wie lange die Write und Read Funktion dauern
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            name (str, optional):               device name.
            typ (str, optional):                device typ.
        """
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Funktionsübergabe einlesen:
        self.sprache                    = sprache
        self.config                     = config
        self.config_dat                 = config_dat
        self.neustart                   = neustart
        self.multilog_OnOff             = multilog_aktiv
        self.Log_WriteReadTime          = Log_WriteReadTime
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = name
        self.typ                        = typ

        ## Weitere:
        self.angezeigt = False

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
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                                                                                                      'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                                                                                         'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                                                                                                                                                               'The following types are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                                                                                              'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',                                                                                                                                    'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                                                                                                                                                  '; Set to default:']
        self.Log_Pfad_conf_5_1  = ['; Adressauswahlcode-Fehler -> Programm zu Ende!!!',                                                                                                                                     '; Address selection code error -> program ends!!!']
        self.Log_Pfad_conf_5_2  = ['; PID-Modus Aus!!',                                                                                                                                                                     '; PID mode off!!']
        self.Log_Pfad_conf_5_3  = ['; Multilog-Link Aus!!',                                                                                                                                                                 '; Multilog-Link off!!']
        self.Log_Pfad_conf_5_4  = ['; Mercury-Model Fehler -> Programm zu Ende!!!',                                                                                                                                         '; Mercury model error -> program ended!!!']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                                                                                          'Reason for error:']
        self.Log_Pfad_conf_7    = ['Bitte vor Nutzung Korrigieren und Config Neu Einlesen!',                                                                                                                                'Please correct and re-read config before use!']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                                                                                                  'Incorrect input:']
        self.Log_Pfad_conf_8_1  = ['Fehlerhafte Typ:',                                                                                                                                                                      'Incorrect type:']
        self.Log_Pfad_conf_9    = ['Die Obergrenze ist kleiner als die Untergrenze! Setze die Limits auf Default:',                                                                                                         'The upper limit is smaller than the lower limit! Set the limits to default:']
        self.Log_Pfad_conf_10   = ['zu',                                                                                                                                                                                    'to']
        self.Log_Pfad_conf_11   = ['Winkelgeschwindhigkeit',                                                                                                                                                                'Angular velocity']
        self.Log_Pfad_conf_12   = ['PID-Eingang Istwert',                                                                                                                                                                   'PID input actual value']
        self.Log_Pfad_conf_13   = ['Winkel',                                                                                                                                                                                'Angle']
        self.Log_Pfad_conf_14   = ['Konfiguration mit VM, MV oder MM ist so nicht möglich, da der Multilink abgeschaltet ist! Setze Default VV!',                                                                           'Configuration with VM, MV or MM is not possible because the multilink is disabled! Set default VV!']
        Log_Text_PID_N18        = ['Die Fehlerbehandlung ist falsch konfiguriert. Möglich sind max, min und error! Fehlerbehandlung wird auf error gesetzt, wodurch der alte Inputwert für den PID-Regler genutzt wird!',   'The error handling is incorrectly configured. Possible values ​​are max, min and error! Error handling is set to error, which means that the old input value is used for the PID controller!']    

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
        #//////////////////////////////////////////////////////////////////////
        try: self.Start_Weg_write          = self.config['start']["write_SW"]
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|write_SW {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Start_Weg_write = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.Start_WegLimit_write     = self.config['start']["write_SLP"]
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|write_SLP {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Start_WegLimit_write = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.Start_Weg   = self.config['start']['start_weg']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|start_weg {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Start_Weg = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.save_mode = self.config['start']['sicherheit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|sicherheit {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.save_mode = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Parameter:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.nKS        = self.config['parameter']['nKS_Aus']                     # Nachkommerstellen
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} parameter|nKS_Aus {self.Log_Pfad_conf_5[self.sprache]} 3')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.nKS = 3
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Limits:
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
        try: self.oGs = self.config["limits"]['maxPos']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxPos {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGs = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGs = self.config["limits"]['minPos']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minPos {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGs = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
        try: self.unit_PIDIn             = self.config['PID']['Input_Size_unit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Size_unit {self.Log_Pfad_conf_5[self.sprache]} mm')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.unit_PIDIn = 'mm'
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Option             = self.config['PID']['Value_Origin'].upper()
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
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Schnittstelle:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Loop = self.config['serial-loop-read']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} serial-loop-read {self.Log_Pfad_conf_5[self.sprache]} 10')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Loop = 10

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Config-Fehler und Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID-Aktiviert:
        if not type(self.PID_Aktiv) == bool and not self.PID_Aktiv in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Aktiv - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Aktiv}')
            self.PID_Aktiv = 0
        ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0
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
        if not type(self.oGs) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 180 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGs)}')
            self.oGs = 1
        if not type(self.uGs) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minPos - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGs)}')
            self.uGs = 0
        if self.oGs <= self.uGs:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
            self.uGs = 0
            self.oGs = 1
        ### Messzeit:
        if not type(self.messZeit) in [int, float] or not self.messZeit >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} readTime - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 2 - {self.Log_Pfad_conf_8[self.sprache]} {self.messZeit}')
            self.messZeit = 2
        ### Wahl der Antriebsart:
        if not self.Antriebs_wahl in ['L', 'R', 'F']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Antriebs_Art - {self.Log_Pfad_conf_2[self.sprache]} [L, R, F] - {self.Log_Pfad_conf_3[self.sprache]} F')
            self.Antriebs_wahl = 'F'
        ### While-Loop:
        if not type(self.Loop) == int or not self.Loop >= 1:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} serial-loop-read - {self.Log_Pfad_conf_2[self.sprache]} Integer (>=1) - {self.Log_Pfad_conf_3[self.sprache]} 10 - {self.Log_Pfad_conf_8[self.sprache]} {self.Loop}')
            self.Loop = 10
        ### Start Weg:
        if not type(self.Start_Weg) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_weg - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.Start_Weg)}')
            self.Start_Weg = 0
        ### Start-Wert schreiben:
        if not type(self.Start_WegLimit_write) == bool and not self.Start_WegLimit_write in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} write_SLP - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.Start_WegLimit_write}')
            self.Start_WegLimit_write = 0 
        ### Anlagen-Sciherheit bei Realer-Positions-Limitregelung:
        if not self.save_mode in [0, 1]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} sicherheit - {self.Log_Pfad_conf_2[self.sprache]} [0, 1] - {self.Log_Pfad_conf_3[self.sprache]} 0')
            self.save_mode = 0

        ## Andere:
        self.Limit_stop         = False
        self.Limit_Stop_Text    = -1
        self.value_name         = {'IWs': 0, 'IWv': 0, 'SWxPID': self.Soll, 'IWxPID': self.Ist}
        self.akPos              = 0
        self.akPos_StoppLimit   = 0
        self.last_Pos           = 0
        self.Min_End            = False
        self.Max_End            = False

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging: ##################################################################################################################################################################################################################################################################################
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                                                                                                                                   'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',                                                                                                                'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                                                                                                                                 'Error reason (interface structure):']
        self.Log_Text_64_str    = ['Das Gerät konnte nicht ausgelesen werden.',                                                                                                                                             'The device could not be read.']
        self.Log_Text_64_1_str  = ['Das Gerät konnte nicht angesprochen werden.',                                                                                                                                           'The device could not be addressed.']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                                                                                                                                          'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                                                                                                                       'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                                                                                                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                                                                                                                  'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                                                                                                                       'No measurement data recording active!']
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                                                                                                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                                                                                                                'Error reason (send):']
        self.Log_Text_136_str   = ['Fehler Grund (Auslesen):',                                                                                                                                                              'Error reason (reading):']
        self.Log_Text_159_str   = ['Wiederholungs-Versuch',                                                                                                                                                                 'Repeat attempt']
        self.Log_Text_160_str   = ['funktionierte nicht!',                                                                                                                                                                  "did not work!"]
        self.Log_Text_164_str   = ['Startposition:',                                                                                                                                                                        'Starting position:']
        self.Log_Text_165_str   = ['mm',                                                                                                                                                                                    'mm']
        self.Log_Text_180_str   = ['Das Gerät hat keine Startwerte zum Auslesen!',                                                                                                                                          'The device has no start values to read out!']
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
        self.Log_Text_LB_unit   = ['mm/min',                                                                                                                                                                                'mm/min']
        self.Log_Text_217_str   = ['Maximum Limit erreicht!',                                                                                                                                                               'Maximum limit reached!']
        self.Log_Text_218_str   = ['Minimum Limit erreicht!',                                                                                                                                                               'Minimum limit reached!']
        self.Log_Filter_PID_S   = ['Sollwert',                                                                                                                                                                              'Setpoint'] 
        self.Log_Filter_PID_I   = ['Istwert',                                                                                                                                                                               'Actual value'] 
        self.Log_Time_w         = ['Die write-Funktion hat',                                                                                                                                                                'The write function has']     
        self.Log_Time_wr        = ['s gedauert!',                                                                                                                                                                           's lasted!']   
        self.Log_Time_r         = ['Die read-Funktion hat',                                                                                                                                                                 'The read function has']  
        self.Log_Text_PIDVV     = ['Noch nicht vollkommen implementiert, Vifcon als PID-Input Sollwert! Hier wird Istwert auf Sollwert gesetzt!',                                                                           'Not yet fully implemented, Vifcon as PID input setpoint!! Here the actual value is set to the target value!']
        self.Log_Edu_1_str      = ['Gesendeter-Befehl:',                                                                                                                                                                    'Sent command:']
        self.Log_Edu_2_str      = ['Antwort-Gerät:',                                                                                                                                                                        'Answering device:']
        self.Log_Edu_3_str      = ['Antwort Falsch!',                                                                                                                                                                       'Answer False!']
        self.Log_Edu_4_str      = ['Wiederhole Antwort lesen, bevor neu Senden!',                                                                                                                                           'Please read the answer again before sending again!']
        self.Log_Edu_5_str      = ['Sende Befehl erneut!',                                                                                                                                                                  'Resend command!']
        self.Log_Edu_6_str      = ['Das Senden an Educrys hat keine richtige Antwort erbracht! Dies kann trotzdem bedeuten, dass der Befehl am Gerät angekommen ist!',                                                      'Sending to Educrys did not produce a correct response! This may still mean that the command was received by the device!']
        self.Log_Edu_7_str      = ['Antwort des Geräts auf !:',                                                                                                                                                             'Device response to !:']
        self.Log_Edu_8_str      = ['Vor Änderung',                                                                                                                                                                          'Before change']
        self.Log_Edu_9_str      = ['Nach Änderung',                                                                                                                                                                         'After change']
        self.Log_Edu_10_str     = ['Setze die Limits ins Gerät ein! (Init)',                                                                                                                                                'Set the limits in the device! (Init)']
        ## Ablaufdatei: ###############################################################################################################################################################################################################################################################################
        self.Text_51_str        = ['Initialisierung!',                                                                                                                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                                                                       'Initialization Failed!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                                                                                                                        'Sending failed!']
        self.Text_62_str        = ['Achse wurde erfolgreich angehalten!',                                                                                                                                                   'Axis was stopped successfully!']
        self.Text_69_str        = ['Geschwindigkeit erfolgreich gesendet!',                                                                                                                                                 'Speed sent successfully!']
        self.Text_70_str        = ['Befehl sende Geschwindigkeit fehlgeschlagen!',                                                                                                                                          'Command send speed failed!']
        self.Text_Edu_1_str     = ['Befehl',                                                                                                                                                                                'Command']
        self.Text_Edu_2_str     = ['erfolgreich gesendet!',                                                                                                                                                                 'sent successfully!']

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
        self.haupt_befehl = f'2{self.Antriebs_wahl}'
        self.abschluss = '\r'

        if self.Antriebs_wahl == 'L':   self.Antworts_String = 'l:='
        elif self.Antriebs_wahl == 'R': self.Antworts_String = 'r:='
        elif self.Antriebs_wahl == 'F': self.Antworts_String = 'f:='

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        if self.uGv < 0:     controll_under_Null = 0
        else:                controll_under_Null = self.uGv
        self.PID = PID(self.sprache, self.device_name, self.PID_Config, self.oGv, controll_under_Null, self.add_Text_To_Ablauf_Datei)
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
        self.PID_Ist_Last  = self.Ist
        self.PID_Soll_Last = self.Soll

    ##########################################
    # Schnittstelle (Schreiben):
    ##########################################
    def write(self, write_Okay, write_value):
        ''' Sende Befehle an die Achse um Werte zu verändern.

        Args:
            write_Okay (dict):  beinhaltet Boolsche Werte für das was beschrieben werden soll!
            write_value (dict): beinhaltet die Werte die geschrieben werden sollen
        '''
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        #++++++++++++++++++++++++++++++++++++++++++
        # Start:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Start'] and not self.neustart:
            self.Start_Werte()
            write_Okay['Start'] = False

        #++++++++++++++++++++++++++++++++++++++++++
        # PID-Reset:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['PID-Reset']:
            self.PID.Reset()
            write_Okay['PID-Reset'] = False
            self.Ist  = 0
            self.Soll = 0

        #++++++++++++++++++++++++++++++++++++++++++
        # Update Limit:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Update Limit']:
            ## Geschwindigkeit/PID-Output:
            self.PID.OutMax = write_value['Limits'][2]
            if write_value['Limits'][1] < 0:    self.PID.OutMin = 0
            else:                               self.PID.OutMin = write_value['Limits'][3]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {self.Log_Text_LB_unit[self.sprache]}')
            ## PID-Input:
            self.PID_Input_Limit_Max = write_value['Limits'][4]
            self.PID_Input_Limit_Min = write_value['Limits'][5]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max} {self.unit_PIDIn}')
            ## Position:
            self.oGs = write_value['Limits'][0]
            self.uGs = write_value['Limits'][1]
            ## Sende Werte an Anlage:
            self.send_write('2T'+'{:.2f}'.format(round(self.oGs,2)), 't:='+'{:.2f}'.format(round(self.oGs,2))) # Rundet perfekt auf zwei Nachkommerstellen, auch wenn eine Null ist!
            self.send_write('2B'+'{:.2f}'.format(round(self.uGs,2)), 'b:='+'{:.2f}'.format(round(self.uGs,2)))
            write_Okay['Update Limit'] = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Normaler Betrieb:
        #++++++++++++++++++++++++++++++++++++++++++
        if not write_Okay['PID']:  
            ## Sollwert Lesen (v):
            speed_vorgabe = write_value['Speed']
            PID_write_V = False
            self.angezeigt = False
        #++++++++++++++++++++++++++++++++++++++++++    
        # PID-Regler:
        #++++++++++++++++++++++++++++++++++++++++++
        elif write_Okay['PID']:
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
            ### Sollwert Filter:
            self.Soll, error_Input_S = self.Input_Filter(self.Soll, 'Soll')
            ### Fehler-Behandlung:
            if error_Input_S:
                #### Input auf letzten Sollwert-Input setzen:
                self.Soll = self.PID_Soll_Last
            else:
                self.PID_Soll_Last = self.Soll
            #---------------------------------------------
            ## Auswahl Istwert:
            #---------------------------------------------
            ### VIFCON:
            if self.PID_Option[0] == 'V':
                if not self.angezeigt:
                    logger.warning(self.Log_Text_PIDVV[self.sprache])
                self.angezeigt = True
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
            self.Ist, error_Input_I = self.Input_Filter(self.Ist)
            ### Fehler-Behandlung:
            if error_Input_I:
                #### Input auf Maximum setzen:
                if self.PID_Input_Error_Option == 'max':
                    self.Ist = self.PID_Input_Limit_Max
                #### Input auf Minimum setzen:
                elif self.PID_Input_Error_Option == 'min':
                    self.Ist = self.PID_Input_Limit_Min
                #### Input auf letzten Istwert-Input setzen:
                elif self.PID_Input_Error_Option == 'error':
                    self.Ist = self.PID_Ist_Last
            else:
                self.PID_Ist_Last = self.Ist
            #---------------------------------------------    
            ## Schreibe Werte:
            #---------------------------------------------
            speed_vorgabe = self.PID_Out * self.cpm
            PID_write_V = True
 
        if self.Antriebs_wahl == 'L':
            #+++++++++++++++++++++++++++++++++++++++++++++++++++++
            # Sende Position (Define Home - beliebiger Wert):
            #+++++++++++++++++++++++++++++++++++++++++++++++++++++
            if write_Okay['Sende Position']:
                self.send_write('2Z'+'{:.2f}'.format(round(write_value["Position"],2)), 'z:='+'{:.2f}'.format(round(write_value["Position"],2)))
                write_Okay['Sende Position'] = False 
                if self.oGs == 0:        self.Max_End = True
                else:                    self.Max_End = False                       
                if self.uGs == 0:        self.Min_End = True                    
                else:                    self.Min_End = False

            #++++++++++++++++++++++++++++++++++++++++++
            # Lese Aktuelle Position aus:
            #++++++++++++++++++++++++++++++++++++++++++
            if self.init:
                read_ans = self.read()
                self.akPos = read_ans['IWs']
                ## Abfangen von Nan-Werten:
                if m.isnan(self.akPos) and self.save_mode == 1:
                    write_Okay['Stopp']     = True
                    self.Limit_stop         = True
                    self.Limit_Stop_Text    = 4
                elif m.isnan(self.akPos) and self.save_mode == 0:
                    self.Limit_Stop_Text    = 5
                ## Bei Nan - Alten Wert nutzen:
                if m.isnan(self.akPos): self.akPos = self.last_Pos
                else:                   self.last_Pos = self.akPos

            #++++++++++++++++++++++++++++++++++++++++++
            # Limit Kontrolle:
            #++++++++++++++++++++++++++++++++++++++++++
            ## Abfangen von Nan-Werten:
            if m.isnan(self.akPos) and self.save_mode == 1:
                write_Okay['Stopp']     = True
                self.Limit_stop         = True
                self.Limit_Stop_Text    = 4
            elif m.isnan(self.akPos) and self.save_mode == 0:
                self.Limit_Stop_Text    = 5
            if self.akPos > self.oGs and not self.Max_End:
                self.Max_End = True
                logger.warning(f'{self.device_name} - {self.Log_Text_217_str[self.sprache]}')
                self.Limit_Stop_Text    = 0
                self.Limit_stop         = True
                write_Okay['Stopp']     = True
                self.akPos_StoppLimit = self.akPos
            if self.akPos < self.uGs and not self.Min_End:
                self.Min_End = True
                logger.warning(f'{self.device_name} - {self.Log_Text_218_str[self.sprache]}') 
                self.Limit_Stop_Text    = 1
                self.Limit_stop         = True
                write_Okay['Stopp']     = True
                self.akPos_StoppLimit = self.akPos
            if self.akPos > self.uGs and self.akPos < self.oGs:
                self.Max_End = False
                self.Min_End = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Sende Stopp:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Stopp']:
            try:
                self.send_write(f'2{self.Antriebs_wahl}'+'{:.2f}'.format(round(0,2)), self.Antworts_String+'{:.2f}'.format(round(0,2)))       
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_62_str[self.sprache]}') 
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_64_1_str[self.sprache]} ({f'2{self.Antriebs_wahl}'+'{:.2f}'.format(round(0,2))})")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
            # Rücksetzen aller Bewegungen:
            write_Okay['Stopp'] = False
            write_Okay['Sende Position'] = False
            write_Okay['Sende Speed'] = False  
        #++++++++++++++++++++++++++++++++++++++++++                                  
        # Schreiben, wenn nicht Stopp:
        #++++++++++++++++++++++++++++++++++++++++++
        else:
            try:     
                ## Sende Geschwindigkeit:
                if write_Okay['Sende Speed']:
                    self.send_write(f'2{self.Antriebs_wahl}'+'{:.2f}'.format(round(write_value["Speed"],2)), self.Antworts_String+'{:.2f}'.format(round(write_value["Speed"],2)))
                    write_Okay['Sende Speed'] = False     
                ## PID-Modus:
                elif PID_write_V:
                    self.send_write(f'2{self.Antriebs_wahl}'+'{:.2f}'.format(round(speed_vorgabe,2)), self.Antworts_String+'{:.2f}'.format(round(speed_vorgabe,2)))
                    PID_write_V = False                    
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]}')
        
        #++++++++++++++++++++++++++++++++++++++++++
        # Funktions-Dauer aufnehmen:
        #++++++++++++++++++++++++++++++++++++++++++
        timediff = (datetime.datetime.now(datetime.timezone.utc).astimezone() - ak_time).total_seconds()  
        if self.Log_WriteReadTime:
            logger.info(f"{self.device_name} - {self.Log_Time_w[self.sprache]} {timediff} {self.Log_Time_wr[self.sprache]}")   

    def send_write(self, Befehl, Antworts_String):
        ''' Schreibe Befehle an die Educrys Anlage!

        Args:
            Befehl (str):           Volkommender Befehl - Zeichen z.B. 2L und Wert (zwei Nachkommerstellen)
            Antworts_String (str):  Aussehen des Antwortsstring - z.B. l:=Wert
        ''' 
        n = 0
        try:
            # Reset Buffer:
            self.serial.reset_input_buffer()
            
            # Sende den Befehl:
            self.serial.write((Befehl+self.abschluss).encode())
            logger.debug(f'{self.device_name} - {self.Log_Edu_1_str[self.sprache]} {(Befehl+self.abschluss).encode()}')
            # Warte kurz:
            time.sleep(0.1)
            # Lese die Antwort und Verhleiche sie:
            ans = self.serial.read_until().decode().strip()             # excepted = \n ist default
            if ans == Antworts_String:  logger.debug(f'{self.device_name} - {self.Log_Edu_2_str[self.sprache]} {ans}')
            else:                    
                logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Edu_4_str[self.sprache]}')       

                ans = self.serial.read_until().decode().strip()
                if ans == Antworts_String:  logger.debug(f'{self.device_name} - {self.Log_Edu_2_str[self.sprache]} {ans}')
                else:                    
                    logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Edu_5_str[self.sprache]}') 

                    # Antwort stimmt nicht:
                    while n != self.Loop:
                        self.serial.write((Befehl+self.abschluss).encode())
                        logger.debug(f'{self.device_name} - {self.Log_Edu_1_str[self.sprache]} {(Befehl+self.abschluss).encode()}')
                        time.sleep(0.1)
                        ans = self.serial.read_until().decode().strip()
                        if ans == Antworts_String:  
                            logger.debug(f'{self.device_name} - {self.Log_Edu_2_str[self.sprache]} {ans}') 
                            break
                        else:                       
                            logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Text_159_str[self.sprache]} {n} {self.Log_Text_160_str[self.sprache]}') 
                            n += 1 

            if n == self.Loop:
                logger.warning(f"{self.device_name} - {self.Log_Edu_6_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]} ({Befehl})')
            else:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Edu_1_str[self.sprache]} {Befehl} {self.Text_Edu_2_str[self.sprache]}') 
        except:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_1_str[self.sprache]} ({Befehl})")
            logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")

    def Input_Filter(self, Input, Art = 'Ist'):
        ''' Input-Filter für den Multilog-VIFCON Link und die PID-Nutzung
        
        Args:
            Input (Float):      Wert der überprüft werden soll
            Art (str):          Sollwert (Soll) oder Istwert (Ist) für Logging
        Return:
            Input (Float):      Bei Limit-Überschreitung kann dies geändert werden, deswegen wird der Eingangswert auch wieder Ausgegeben.
            error_Input (bool): Fehler Ausgabe (True: NAN oder falscher Typ)         
        '''
        if Art == 'Ist':    Input_String = self.Log_Filter_PID_I
        elif Art == 'Soll': Input_String = self.Log_Filter_PID_S
        error_Input = False
        try:
            #### Nan-Werte:
            if m.isnan(Input):
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_N14[self.sprache]} ({Input_String[self.sprache]})")
                error_Input = True
            #### Kein Float oder Integer:
            elif type(Input) not in [int, float]:
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_N17[self.sprache]} {type(Input)} ({Input_String[self.sprache]})")
                error_Input = True
            #### Input-Wert überschreitet Maximum:
            elif Input > self.PID_Input_Limit_Max:
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_N15[self.sprache]} {self.PID_Input_Limit_Max} {self.Log_Text_PID_N20[self.sprache]} {self.Ist}{self.Log_Test_PID_N22[self.sprache]} ({Input_String[self.sprache]})")
                Input = self.PID_Input_Limit_Max
            #### Input-Wert unterschreitet Minimum:
            elif Input < self.PID_Input_Limit_Min:
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_N16[self.sprache]} {self.PID_Input_Limit_Min} {self.Log_Text_PID_N20[self.sprache]} {self.Ist}{self.Log_Test_PID_N22[self.sprache]} ({Input_String[self.sprache]})")
                Input = self.PID_Input_Limit_Min
        except Exception as e:
            error_Input = True
            logger.warning(f"{self.device_name} - {self.Log_Text_PID_N11[self.sprache]} ({Input_String[self.sprache]})")
            logger.exception(f"{self.device_name} - {self.Log_Text_PID_N12[self.sprache]}")

        return Input, error_Input

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def read(self):
        ''' Sende Befehle an die Achse um Werte auszulesen.

        Return: 
            Aktuelle Werte (dict)   - self.value_name
        '''
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        error = False   
        listen_Error = False
        n = 0

        try:
            # Sende Auslese-Befehl:
            ## Besteht aus vielen Werten im Format *Wert_1 Wert_2#
            self.serial.write(('!'+ self.abschluss).encode())
            # Etwas Zeit lassen:
            time.sleep(0.1)
            # Antwort lesen:
            ans = self.serial.read_until().decode().strip().replace('*', '').replace('#','').replace('\r\n','')
            ''' Relevante Werte:
                                                    Liste (0 - Ende)            Stelle (1 - Ende)
                         Linear:    Koordinate      23                          24
                                    Ist-v           24                          25
                         Rotation:  Ist-v           25                          26
                         Lüfter:    Ist-v           26                          27
            '''     
            logger.debug(f'{self.device_name} - {self.Log_Edu_7_str[self.sprache]} {ans}')   
            if ans == '':  
                logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Edu_4_str[self.sprache]}')
                ans = self.serial.read_until().decode().strip().replace('*', '').replace('#','').replace('\r\n','')
                if ans == '':   
                    logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Edu_5_str[self.sprache]}')
                    while n != self.Loop: 
                        self.serial.write(('!'+self.abschluss).encode())
                        time.sleep(0.1)
                        ans = self.serial.read_until().decode().strip().replace('*', '').replace('#','').replace('\r\n','')

                        if ans == '':   n += 1
                        else:
                            logger.debug(f'{self.device_name} - {self.Log_Edu_7_str[self.sprache]} {ans}')
                            break
            if n == self.Loop:
                logger.warning(f"{self.device_name} - {self.Log_Edu_6_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]} (!)')
                error = True
            else:
                logging.debug(f'{self.device_name} - {self.Text_Edu_1_str[self.sprache]} ! {self.Text_Edu_2_str[self.sprache]}')

            if not error:
                ## Liste erstellen:
                try:
                    liste = ans.split(' ')
                except:
                    listen_Error = True
                
                if len(liste) != 29 or listen_Error:
                    logger.warning(f"{self.device_name} - {self.Log_Edu_6_str[self.sprache]}")
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]} (!)')
                    liste = []
                    for i in range(0,29,1):
                        liste.append(m.nan)

                ## Werte eintragen:
                if self.Antriebs_wahl == 'L':
                    self.value_name['IWs'] = float(liste[23])
                    self.value_name['IWv'] = float(liste[24])
                elif self.Antriebs_wahl == 'R':
                    self.value_name['IWv'] = float(liste[25])
                elif self.Antriebs_wahl == 'F':
                    self.value_name['IWv'] = float(liste[26])
            else:
                ## Bei Fehler Nan einfügen:
                self.value_name['IWs'] = m.nan
                self.value_name['IWv'] = m.nan

            # PID-Modus:
            self.value_name['SWxPID'] = self.Soll
            self.value_name['IWxPID'] = self.Ist

        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")

        #++++++++++++++++++++++++++++++++++++++++++
        # Funktions-Dauer aufnehmen:
        #++++++++++++++++++++++++++++++++++++++++++
        timediff = (datetime.datetime.now(datetime.timezone.utc).astimezone() - ak_time).total_seconds()  
        if self.Log_WriteReadTime:
            logger.info(f"{self.device_name} - {self.Log_Time_r[self.sprache]} {timediff} {self.Log_Time_wr[self.sprache]}")
        return self.value_name

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
            if self.Antriebs_wahl == 'L':
                ## Start-Position auslesen:
                read_ans = self.read()
                self.akPos = read_ans['IWs']
                if self.akPos == m.nan:
                    self.akPos = self.last_Pos
                    zusatz = '(Error Nan)'
                else: 
                    zusatz = ''
                    self.last_Pos = self.akPos
                if self.Start_Weg_write:    zusatz_2 = f'- {self.Log_Edu_8_str[self.sprache]}'
                else:                       zusatz_2 = ''
                logger.info(f"{self.device_name} - {self.Log_Text_164_str[self.sprache]} {self.akPos} {self.Log_Text_165_str[self.sprache]} {zusatz} {zusatz_2}")
            
                ## Start-Wert Überschreiben:
                if self.Start_Weg_write:
                    self.send_write('2Z'+'{:.2f}'.format(round(self.Start_Weg,2)), 'z:='+'{:.2f}'.format(round(self.Start_Weg,2)))
                
                    ## Start-Position auslesen:
                    read_ans = self.read()
                    self.akPos = read_ans['IWs']
                    if self.akPos == m.nan:
                        self.akPos = self.last_Pos
                        zusatz = '(Error Nan)'
                    else: 
                        zusatz = ''
                        self.last_Pos = self.akPos
                    zusatz_2 = f'- {self.Log_Edu_9_str[self.sprache]}'
                    logger.info(f"{self.device_name} - {self.Log_Text_164_str[self.sprache]} {self.akPos} {self.Log_Text_165_str[self.sprache]} {zusatz} {zusatz_2}")
            
                if self.Start_WegLimit_write:
                    logger.info(f"{self.device_name} - {self.Log_Edu_10_str[self.sprache]}")
                    self.send_write('2T'+'{:.2f}'.format(round(self.oGs,2)), 't:='+'{:.2f}'.format(round(self.oGs,2))) # Rundet perfekt auf zwei Nachkommerstellen, auch wenn eine Null ist!
                    self.send_write('2B'+'{:.2f}'.format(round(self.uGs,2)), 'b:='+'{:.2f}'.format(round(self.uGs,2)))
            else:
                logger.info(f"{self.device_name} - {self.Log_Text_180_str[self.sprache]}")
        except Exception as e:
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
        if self.Antriebs_wahl == 'L':
            units = f"# datetime,s,mm,mm/min,{PID_x_unit},{PID_x_unit},\n"
            header = "time_abs,time_rel,Ist-Position,Ist-Geschwindigkeit,Soll-x_PID-Modus_A,Ist-x_PID-Modus_A,\n"
        else:
            units = f"# datetime,mm,1/min,{PID_x_unit},{PID_x_unit},\n"
            header = "time_abs,time_rel,Ist-Winkelgeschwindigkeit,Soll-x_PID-Modus_A,Ist-x_PID-Modus_A,\n"
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