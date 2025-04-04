# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Eurotherm Gerät:
- Schnittstelle erstellen
- Werte Lesen und schreiben
- Messdatei updaten
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtCore import (
    QCoreApplication,
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
    """ This class is used to mock a serial interface for debugging purposes. """

    def write(self, _):
        pass

    def readline(self):
        return "".encode()
    

class Eurotherm(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, com_dict, test, neustart, multilog_aktiv, Log_WriteReadTime, add_Ablauf_function, name="Eurotherm", typ = 'Generator'):
        """ Erstelle Eurotherm Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      Geräte Konfigurationen (definiert in config.yml in der devices-Sektion).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            multilog_aktiv (bool):              Multilog-Read/Send Aktiviert
            Log_WriteReadTime (bool):           Logge die Zeit wie lange die Write und Read Funktion dauern
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            name (str, optional):               Geräte Namen.
            typ (str, optional):                Geräte Typ.
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
        self.Log_WriteReadTime          = Log_WriteReadTime
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = name
        self.typ                        = typ

        ## Weitere:
        self.op                 = 0
        self.EuRa_Aktiv         = False
        self.Save_End_State     = False
        self.done_ones          = False
        self.mode_aktiv         = False 
        self.Rez_OP             = -1
        self.PID_Ein            = False
        self.Block_Ablaufdatei  = False
        self.value_old          = -1

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
        self.Log_Pfad_conf_5_1  = ['; Register-Fehler -> Programm zu Ende!!!',                                                                                                                                              '; Register error -> program ends!!!']
        self.Log_Pfad_conf_5_2  = ['; PID-Modus Aus!!',                                                                                                                                                                     '; PID mode off!!']
        self.Log_Pfad_conf_5_3  = ['; Multilog-Link Aus!!',                                                                                                                                                                 '; Multilog-Link off!!']
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
        try: self.Ist            = self.config['PID']["start_ist"] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|start_ist {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Ist = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.Soll           = self.config['PID']["start_soll"]
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|start_soll {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Soll = 0 
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Write      = self.config['start']['PID_Write']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|PID_Write {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Write = False 
        #//////////////////////////////////////////////////////////////////////
        try: self.startMode = self.config['start']["start_modus"]
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|start_modus {self.Log_Pfad_conf_5[self.sprache]} Manuel')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startMode = 'Manuel'
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Sicherheit:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Safety = self.config['start']['sicherheit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|sicherheit {self.Log_Pfad_conf_5[self.sprache]} True')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Safety = True
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Limits:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.oGOp = self.config["limits"]['opMax']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|opMax {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGOp = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGOp = self.config["limits"]['opMin']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|opMin {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGOp = 0
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
        try: self.PID_Option             = self.config['PID']['Value_Origin'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Value_Origin {self.Log_Pfad_conf_5[self.sprache]} VV')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Option = 'VV' 
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
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Sample_Time        = self.config['PID']['sample']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|sample {self.Log_Pfad_conf_5[self.sprache]} 500')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Sample_Time = 500 
        ### Start-Modus:
        if not self.startMode in ['Auto', 'Manuel']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_modus - {self.Log_Pfad_conf_2[self.sprache]} [Auto, Manuel] - {self.Log_Pfad_conf_3[self.sprache]} Manuel - {self.Log_Pfad_conf_8[self.sprache]} {self.startMode}')
            self.startMode = 'Manuel'

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
        ### HO-Start-Sicherheit:
        if not type(self.Safety) == bool and not self.Safety in [0, 1]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} sicherheit - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} True - {self.Log_Pfad_conf_8[self.sprache]} {self.Safety}')
            self.Safety = 1
        ### Ausgangsleistungs-Limit:
        if not type(self.oGOp) in [float, int] or not self.oGOp >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} opMax - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGOp)}')
            self.oGOp = 1
        if not type(self.uGOp) in [float, int] or not self.uGOp >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} opMin - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGOp)}')
            self.uGOp = 0
        if self.oGOp <= self.uGOp:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_11[self.sprache]})')
            self.uGOp = 0
            self.oGOp = 1
        ### PID-Fehlerbehandlung:
        if self.PID_Input_Error_Option not in ['min', 'max', 'error']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N18[sprache]}')
            self.PID_Input_Error_Option = 'error'
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
        ### PID Sample Zeit:
        if not type(self.PID_Sample_Time) in [int] or not self.PID_Sample_Time >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} sample - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 500 - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Sample_Time}')
            self.PID_Sample_Time = 500
        ### Sende Eurotherm PID-Parameter zum Start:
        if not type(self.PID_Write) == bool and not self.PID_Write in [0, 1]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Write - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Write}')
            self.PID_Write = 0 

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Werte Dictionary:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.value_name = {'SWT': 0, 'IWT': 0, 'IWOp': 0, 'SWTPID': self.Soll, 'IWTPID': self.Ist}

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging: ##################################################################################################################################################################################################################################################################################
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                                                                                                                                   'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',                                                                                                                'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                                                                                                                                 'Error reason (interface structure):']
        self.Log_Text_64_str    = ['Das Gerät konnte nicht ausgelesen werden.',                                                                                                                                             'The device could not be read.']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                                                                                                                                          'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                                                                                                                       'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                                                                                                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                                                                                                                  'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                                                                                                                       'No measurement data recording active!']
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                                                                                                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                                                                                                                'Error reason (send):']
        self.Log_Text_103_str   = ['Wiederhole senden nach NAK oder keiner Antwort!',                                                                                                                                       'Repeat send after NAK or no response!']
        self.Log_Text_132_str   = ['BCC (DEC)',                                                                                                                                                                             'BCC (DEC)']
        self.Log_Text_133_str   = ['Keine Antwort oder Falsche Antwort, kein NAK oder ACK!',                                                                                                                                'No answer or wrong answer, no NAK or ACK!']
        self.Log_Text_134_str   = ['Antwort konnte nicht ausgelesen werden!',                                                                                                                                               'Answer could not be read!']
        self.Log_Text_135_str   = ['Fehler Grund (Sende Antwort):',                                                                                                                                                         'Error reason (send response):']
        self.Log_Text_136_str   = ['Fehler Grund (Auslesen):',                                                                                                                                                              'Error reason (reading):']
        self.Log_Text_137_str   = ['Instrumenten Identität:',                                                                                                                                                               'Instrument identity:']
        self.Log_Text_138_str   = ['Software Version:',                                                                                                                                                                     'Software version:']
        self.Log_Text_139_str   = ['Instrumenten Modus:',                                                                                                                                                                   'Instrument mode:']
        self.Log_Text_140_str   = ['Normaler Betriebsmodus',                                                                                                                                                                'Normal Operation Mode']
        self.Log_Text_141_str   = ['Kein Effekt',                                                                                                                                                                           'No effect']
        self.Log_Text_142_str   = ['Konfigurationsmodus',                                                                                                                                                                   'Configuration Mode']
        self.Log_Text_143_str   = ['Ausgabe auf Display:',                                                                                                                                                                  'Output on display:']
        self.Log_Text_144_str   = ['bis',                                                                                                                                                                                   'to']
        self.Log_Text_145_str   = ['°C',                                                                                                                                                                                    '°C']
        self.Log_Text_146_str   = ['Sollwertbereich:',                                                                                                                                                                      'Setpoint range:']
        self.Log_Text_147_str   = ['PID-Regler Parameter:',                                                                                                                                                                 'PID controller parameters:']
        self.Log_Text_148_str   = ['P:',                                                                                                                                                                                    'P:']
        self.Log_Text_149_str   = ['I:',                                                                                                                                                                                    'I:']
        self.Log_Text_150_str   = ['D:',                                                                                                                                                                                    'D:']
        self.Log_Text_151_str   = ['Statuswort:',                                                                                                                                                                           'Status word:']
        self.Log_Text_152_str   = ['Automatischer Modus wird eingeschaltet!',                                                                                                                                               'Automatic mode is turned on!']
        self.Log_Text_153_str   = ['Manueller Modus wird eingeschaltet!',                                                                                                                                                   'Manual mode is switched on!']
        self.Log_Text_154_str   = ['Statuswort ist nicht 0000 oder 8000! Startmodus wird nicht geändert!',                                                                                                                  'Status word is not 0000 or 8000! Start mode is not changed!']
        self.Log_Text_155_str   = ['Ändere Maximale Ausgangsleistungslimit von',                                                                                                                                            'Change Maximum Output Power Limit from']
        self.Log_Text_155_str_1 = ['auf',                                                                                                                                                                                   'to']
        self.Log_Text_156_str   = ['%',                                                                                                                                                                                     '%']
        self.Log_Text_157_str   = ['Maximale Ausgangsleistung wird durch die Eingabe am Gerät bestimmt!',                                                                                                                   'Maximum output power is determined by the input on the device!']
        self.Log_Text_157_str_1 = ['Maximale Ausgangsleistung (am Gerät eingestellt):',                                                                                                                                     'Maximum output power (set on the device):']
        self.Log_Text_183_str   = ['Das Senden der Werte ist fehlgeschlagen! (Rampe)',                                                                                                                                      'Sending the values failed! (Ramp)']
        self.Log_Text_243_str   = ['Beim Startwert senden an Eurotherm gab es einen Fehler! Programm wird beendet! Wurde das Gerät eingeschaltet bzw. wurde die Init-Einstellung richtig gesetzt?',                         'There was an error when sending the start value to Eurotherm! Program will end! Was the device switched on or was the init setting set correctly?']
        self.Log_Text_244_str   = ['Fehler Grund: ',                                                                                                                                                                        'Error reason:']
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
        self.Log_Text_PID_N20   = ['°C - tatsächlicher Wert war',                                                                                                                                                           '°C - tatsächlicher Wert war']
        Log_Text_PID_N21        = ['Multilog Verbindung wurde in Config als Abgestellt gewählt! Eine Nutzung der Werte-Herkunft mit VM, MV oder MM ist so nicht möglich! Nutzung von Default VV!',                          'Multilog connection was selected as disabled in config! Using the value origin with VM, MV or MM is not possible! Use of default VV!']
        self.Log_Text_PID_N22   = ['Wert',                                                                                                                                                                                  'Value']
        self.Log_Text_PID_N23   = ['ist außerhalb gültigen Bereich von 0 bis 99999!',                                                                                                                                       'is outside the valid range from 0 to 99999!']
        self.Log_Text_PID_N24   = ['Fehlergrund (PID-Parameter senden):',                                                                                                                                                   'Reason for error (send PID parameters):']
        self.Log_Text_PID_N25   = ['Senden der PID-Parameter am Start ist Fehlgeschlagen. Um es erneut zu versuchen überprüfe die Config-Datei und nutze das Menü!',                                                        'Sending PID parameters at startup failed. To try again check the config file and use the menu!']   
        self.Log_Extra          = ['Vor Änderung',                                                                                                                                                                          'Before change']
        self.Log_Extra_2        = ['Nach Änderung',                                                                                                                                                                         'After change']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                                                                                                          'Limit range']
        self.Log_Text_LB_4      = ['bis',                                                                                                                                                                                   'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                                                                                                           'after update']
        self.Log_Text_LB_6      = ['PID',                                                                                                                                                                                   'PID']
        self.Log_Text_LB_7      = ['Output',                                                                                                                                                                                'Outout']
        self.Log_Text_LB_8      = ['Input',                                                                                                                                                                                 'Input']
        self.Log_Text_HO        = ['Die aktuelle maximale Ausgangsleistung (HO) ist folgendermaßen:',                                                                                                                       'The current maximum output power (HO) is as follows:']
        self.Log_Filter_PID_S   = ['Sollwert',                                                                                                                                                                              'Setpoint'] 
        self.Log_Filter_PID_I   = ['Istwert',                                                                                                                                                                               'Actual value'] 
        self.Log_EuRa_Befehl    = ['Zu sendener Befehl für die Eurotherm-Rampe:',                                                                                                                                           'Command to send for the Eurotherm ramp:']
        self.Log_Time_w         = ['Die write-Funktion hat',                                                                                                                                                                'The write function has']     
        self.Log_Time_wr        = ['s gedauert!',                                                                                                                                                                           's lasted!']   
        self.Log_Time_r         = ['Die read-Funktion hat',                                                                                                                                                                 'The read function has']        
        ## Ablaufdatei: ###############################################################################################################################################################################################################################################################################
        self.Text_51_str        = ['Initialisierung!',                                                                                                                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                                                                       'Initialization Failed!']
        self.Text_53_str        = ['Wert wurde angenommen (ACK)!',                                                                                                                                                          'Value was accepted (ACK)!']
        self.Text_54_str        = ['Wert wurde nicht angenommen (NAK)!',                                                                                                                                                    'Value was not accepted (NAK)!']
        self.Text_55_str        = ['Senden fehlgeschlagen (Keine Antwort)!',                                                                                                                                                'Sending failed (no response)!']
        self.Text_56_str        = ['Befehl gesendet!',                                                                                                                                                                      'command sent!']
        self.Text_57_str        = ['Antwort nicht auslesbar!',                                                                                                                                                              'Answer cannot be read!']
        self.Text_75_str        = ['Sende Eurotherm Rampe mit dem Aufbau',                                                                                                                                                  'Send Eurotherm ramp with the structure']
        self.Text_76_str        = ['Eurotherm-Rampe wird gestartet',                                                                                                                                                        'Eurotherm ramp is started']
        self.Text_77_str        = ['Reset der Eurotherm-Rampe',                                                                                                                                                             'Reset the Eurotherm ramp']
        self.Text_78_str        = ['Reset der Eurotherm-Rampe wegen Abbruch! Aktuellen Sollwert speichern!',                                                                                                                'Reset of the Eurotherm ramp due to cancellation! Save current setpoint!']

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
        ## Lesen:
        self.read_temperature =         "\x040000PV\x05"                # Isttemperatur
        self.read_op =                  "\x040000OP\x05"                # Leistung (Operating point)
        self.read_soll_temperatur =     "\x040000SL\x05"                # Solltemperatur lesen
        self.read_max_leistung =        "\x040000HO\x05"                # maximale Sollleistung lesen 
        self.read_Modus =               "\x040000SW\x05"                # Modus lesen
        
        ## Schreiben:
        self.write_temperatur =         "\x040000\x02SL"                # Solltemperatur schreiben
        self.write_leistung =           "\x040000\x02OP"                # Sollleistung schreiben       
        self.write_Modus =              "\x040000\x02SW>"               # Modus ändern schreiben 
        self.write_max_leistung =       "\x040000\x02HO"                # maximale Sollleistung schreiben 
        self.EuRa_Modus =               "\x040000\x02OS>"               # Modus Euro-Rampe
        self.write_PB   =               "\x040000\x02XP"                # PID-Regler P-Anteil
        self.write_TI   =               "\x040000\x02TI"                # PID-Regler I-Anteil
        self.write_TD   =               "\x040000\x02TD"                # PID-Regler D-Anteil

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        self.PID = PID(self.sprache, self.device_name, self.PID_Config, self.oGOp, self.uGOp, self.add_Text_To_Ablauf_Datei)
        ## Info und Warnungen:
        if not self.multilog_OnOff and self.PID_Option in ['MV', 'MM', 'VM']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N21[sprache]}')
            self.PID_Option = 'VV'
        # elif self.PID_Option in ['MM', 'VM']:
        #     logger.warning(f'{self.device_name} - {Log_Text_PID_N1[sprache]} {self.PID_Option} {Log_Text_PID_N2_1[self.sprache]}')
        #     self.PID_Option = 'VV'
        elif self.PID_Option not in ['VV', 'MV', 'MM', 'VM']:
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
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]}: {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {self.Log_Text_156_str[self.sprache]}')
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]}: {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max}{self.Log_Text_145_str[self.sprache]}')    
        if self.PID_Option[0] == 'M':
            logger.info(f'{Log_Text_PID_N8[self.sprache]} {self.sensor_ist} {Log_Text_PID_N13[self.sprache]} {self.M_device_ist} {Log_Text_PID_N10[self.sprache]}')
        if self.PID_Option[1] == 'M':
            logger.info(f'{Log_Text_PID_N9[self.sprache]} {self.sensor_soll} {Log_Text_PID_N13[self.sprache]} {self.M_device_soll} {Log_Text_PID_N10[self.sprache]}')
        self.PID_Ist_Last  = self.Ist
        self.PID_Soll_Last = self.Soll

    ##########################################
    # Schnittstelle (Schreiben):
    ##########################################
    def bcc(self, string):
        ''' Berechnet die Prüfsumme (BCC). 

        Args:
            string (str) - Befehl und Wert des Eurotherm schreib Befehles
        '''
        # Umwandlung: https://stackoverflow.com/questions/3673428/convert-int-to-ascii-and-back-in-python

        bcc_list = []
        for c in string:
            dec = ord(c)                        # ASCII zu Dezimalzahl       
            bcc_list.append(dec)                # Anhängen an Liste
        bcc_list.append(3)                      # das Steuerzeichen ETX (\x03) hat die Dezimalzahl 3
        bcc = 0
        for item in bcc_list:
            bcc = (bcc^item)                    # XOR
        logger.debug(f'{self.device_name} - {self.Log_Text_132_str[self.sprache]} = "{bcc}"')
        return chr(bcc)                         # Dezimalzahl zu ASCII

    def write(self, write_Okay, write_value):
        ''' Schreiben der übergebenden Werte, wenn der richtige Knopf betätigt wurde!

        Args:
            write_Okay (dict):  beinhaltet Boolsche Werte für das was beschrieben werden soll!
            write_value (dict): beinhaltet die Werte die geschrieben werden sollen
        '''
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Erwinge das Setzen der Variablen um den Endzustand sicher herzustellen:
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        if self.Save_End_State and not self.done_ones:
            write_Okay['EuRa_Reset']        = True
            write_Okay['Manuel_Mod']        = True   
            write_Okay['Auto_Mod']          = False
            write_Okay['Operating point']   = True 
            write_value['Rez_OPTemp']       = 0 
            self.done_ones                  = True
        
        #++++++++++++++++++++++++++++++++++++++++++
        # PID-Reset:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['PID-Reset']:
            self.PID.Reset()
            write_Okay['PID-Reset'] = False
            self.Ist  = 0
            self.Soll = 0
            self.value_old = -1

        #++++++++++++++++++++++++++++++++++++++++++
        # Update Limit:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Update Limit']:
            ## PID-Output:
            self.PID.OutMax = write_value['Limits'][0]
            self.PID.OutMin = write_value['Limits'][1]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {self.Log_Text_156_str[self.sprache]}')
            ## PID-Input:
            self.PID_Input_Limit_Max = write_value['Limits'][2]
            self.PID_Input_Limit_Min = write_value['Limits'][3]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max}{self.Log_Text_145_str[self.sprache]}')

            ## OP:
            self.oGOp = write_value['Limits'][0]
            self.uGOp = write_value['Limits'][1]

            write_Okay['Update Limit'] = False

        #++++++++++++++++++++++++++++++++++++++++++    
        # Normaler Betrieb:
        #++++++++++++++++++++++++++++++++++++++++++
        if not write_Okay['PID']:  
            self.PID_Ein = False
            # Sollwertn Lesen (OP oder Temp):
            sollwert = write_value['Sollwert']
            PID_write_OP = False
        #++++++++++++++++++++++++++++++++++++++++++
        # PID-Regler:
        #++++++++++++++++++++++++++++++++++++++++++
        elif write_Okay['PID']:
            self.PID_Ein = True
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
                self.Ist = self.read_einzeln(self.read_temperature)
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
            PID_write_OP = True
            PowOutPID = self.op
            #---------------------------------------------
            ## Rezept-Modus:
            #---------------------------------------------
            self.mode_aktiv = write_Okay['PID_Rezept_Mode_OP']
            if self.mode_aktiv:
                self.Rez_OP = write_value['PID_Rez']

        #++++++++++++++++++++++++++++++++++++++++++
        # Schreiben:
        #++++++++++++++++++++++++++++++++++++++++++
        ## Ändere Modus:
        if write_Okay['Auto_Mod'] and not write_Okay['PID']:
            self.write_read_answer('SW>', '0000', self.write_Modus)                
            write_Okay['Auto_Mod'] = False
        elif write_Okay['Manuel_Mod'] or write_Okay['PID']:
            ## Immer beim Umsachalten, wenn die Sicherheit auf True steht wird der HO ausgelesen:
            value_HO = self.check_HO()
            if value_HO != '' and value_HO != m.nan:
                self.oGOp = value_HO
            self.write_read_answer('SW>', '8000', self.write_Modus)
            write_Okay['Manuel_Mod'] = False

        for auswahl in write_Okay:
            ## Temperatur-Sollwert:
            if write_Okay[auswahl] and auswahl == 'Soll-Temperatur':
                self.write_read_answer('SL', str(sollwert), self.write_temperatur)
                if self.EuRa_Aktiv:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_77_str[self.sprache]}')
                    self.write_read_answer('OS>', '0100', self.EuRa_Modus)
                    self.EuRa_Aktiv = False
                write_Okay[auswahl] = False
            ## Ausgangsleistung OP:
            elif write_Okay[auswahl] and auswahl == 'Operating point':
                if write_value['Rez_OPTemp'] > -1:
                    sollwert = write_value['Rez_OPTemp']
                    write_value['Rez_OPTemp'] = -1
                self.write_read_answer('OP', str(sollwert), self.write_leistung)
                write_Okay[auswahl] = False
            ## Ausgangsleistung während des PID-Modus:
            elif PID_write_OP:
                self.write_read_answer('OP', str(PowOutPID), self.write_leistung)
                PID_write_OP = False
            ## Startwerte:
            elif write_Okay[auswahl] and auswahl == 'Start' and not self.neustart:
                self.Start_Werte()
                write_Okay[auswahl] = False
            ## Eurotherm-Rampe Start:
            elif write_Okay[auswahl] and auswahl == 'EuRa':
                if self.EuRa_Aktiv:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_77_str[self.sprache]}')
                    self.write_read_answer('OS>', '0100', self.write_leistung)
                    self.EuRa_Aktiv = False
                self.EuRa_Aktiv = True
                self.write_EuRa(write_value['EuRa_Soll'], write_value['EuRa_m'])
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_76_str[self.sprache]}')
                self.write_read_answer('OS>', '0102', self.EuRa_Modus)
                write_Okay[auswahl] = False
            ## Eurotherm-Rampe zurücksetzen + Sollwert senden:
            elif write_Okay[auswahl] and auswahl == 'EuRa_Reset':
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_78_str[self.sprache]}')
                ### Lese aktuellen Sollwert:
                try:    
                    self.serial.write(self.read_soll_temperatur.encode())
                    soll_temperatur = float(self.serial.readline().decode()[3:-2])
                except Exception as e: 
                    soll_temperatur = self.value_name['IWT']    # setze letzten gemessenen Istwert als Sollwert ein!!
                    logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]} ({self.read_soll_temperatur.encode()})")
                    logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")
                ### Übergebe diesem Eurotherm:
                self.write_read_answer('SL', str(soll_temperatur), self.write_temperatur)
                ### Reset des Programms:
                self.write_read_answer('OS>', '0100', self.EuRa_Modus)
                write_Okay[auswahl] = False
            ## Lese Maximum OP:
            elif write_Okay[auswahl] and auswahl == 'Read_HO':
                value_HO = self.check_HO(True)
                if value_HO != '' and value_HO != m.nan:
                    self.oGOp = value_HO
                write_Okay[auswahl] = False
            ## Schreibe Maximum OP.
            elif write_Okay[auswahl] and auswahl == 'Write_HO':
                self.write_read_answer('HO', str(write_value['HO']), self.write_max_leistung)
                write_Okay[auswahl] = False
            ## Schreibe die PID-Parameter:
            elif write_Okay[auswahl] and auswahl == 'PID-Update':
                self.write_read_answer('XP', str(write_value['PID-Update'][0]), self.write_PB)
                self.write_read_answer('TI', str(write_value['PID-Update'][1]), self.write_TI)
                self.write_read_answer('TD', str(write_value['PID-Update'][2]), self.write_TD)
                write_Okay[auswahl] = False
            ## Lese die PID-Parameter:
            elif write_Okay[auswahl] and auswahl == 'Read_PID':
                self.check_PID()
                write_Okay[auswahl] = False
        
        #++++++++++++++++++++++++++++++++++++++++++
        # Funktions-Dauer aufnehmen:
        #++++++++++++++++++++++++++++++++++++++++++
        timediff = (datetime.datetime.now(datetime.timezone.utc).astimezone() - ak_time).total_seconds()  
        if self.Log_WriteReadTime:
            logger.info(f"{self.device_name} - {self.Log_Time_w[self.sprache]} {timediff} {self.Log_Time_wr[self.sprache]}")

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

    def write_read_answer(self, write_mn, value, befehl_start):
        ''' Lese die Antowrt des Schreibbefehls aus!
        
        Args:
            write_mn (str):     Mnemonik Befehl des Eurotherms
            value (str):        übergebender Wert
            befehl_start (str): Start des Befehls
        '''
        # Ablaufdatei Zusatz:
        if self.PID_Ein and write_mn == 'OP':
            if self.value_old != self.op:
                self.value_old = self.op
                self.Block_Ablaufdatei = False
            else:
                self.Block_Ablaufdatei = True
        elif self.PID_Ein and write_mn == 'SW>':
            self.Block_Ablaufdatei = True
        else:
            self.Block_Ablaufdatei = False

        # Schreibe:
        bcc_Wert = self.bcc(write_mn + value)
        try: 
            self.serial.write(f'{befehl_start}{value}\x03{bcc_Wert}'.encode())
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")

        # Lese Antwort (Kontrolle des Eingangs des Befehls):
        if not self.Block_Ablaufdatei:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {write_mn}{value} {self.Text_56_str[self.sprache]}')
        try:
            answer = self.serial.readline().decode()                                            
            if answer == '\x06':
                if not self.Block_Ablaufdatei:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_53_str[self.sprache]}')          
                logger.debug(f'{self.device_name} {self.Text_53_str[self.sprache]}')
            elif answer == '\x15':
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_54_str[self.sprache]}')    
                logger.warning(f"{self.device_name} - {self.Text_54_str[self.sprache]}")
            else:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_55_str[self.sprache]}')      
                logger.warning(f"{self.device_name} - {self.Log_Text_133_str[self.sprache]}")
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_134_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_135_str[self.sprache]}")
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_57_str[self.sprache]}')    

    def write_EuRa(self, Sollwert, Steigung):
        ''' Übergebe und Kontrolliere die Rampeneinstellung
        
        Args:
            Sollwert (float):   Zielsollwert der Rampe         
            Steigung (float):   Steigung der Rampe
        '''
        Segement    = ['r1',  'l1', 't1']
        segment_v   = [Steigung, Sollwert, -0.01]
        self.add_Text_To_Ablauf_Datei(f"{self.device_name} - {self.Text_75_str[self.sprache]} ['r1',  'l1', 't1']: {[Steigung, Sollwert, -0.01]}")
        logger.info(f"{self.device_name} - {self.Text_75_str[self.sprache]} ['r1',  'l1', 't1']: {[Steigung, Sollwert, -0.01]}")
        i = 0
        for s in segment_v:
            stop = 0
            while 1:
                write_rampe = f"\x040000\x02{Segement[i]}"
                Sollwert = s
                bcc_Wert = self.bcc(f'{Segement[i]}' + str(Sollwert))
                self.serial.write(f'{write_rampe}{Sollwert}\x03{bcc_Wert}'.encode())
                befehl_extra = f"{write_rampe}{Sollwert}\x03{bcc_Wert}".encode()
                logger.debug(f'{self.device_name} - {self.Log_EuRa_Befehl[self.sprache]} {befehl_extra}')
                try:
                    answer = self.serial.readline().decode()
                    if answer == '\x06':
                        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_53_str[self.sprache]}')          
                        logger.debug(f'{self.device_name} - {self.device_name} {self.Text_53_str[self.sprache]}')
                        i += 1
                        break
                    elif answer == '\x15':
                        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_54_str[self.sprache]}')    
                        logger.warning(f"{self.device_name} - {self.Text_54_str[self.sprache]}")
                        logger.warning(f'{self.device_name} - {self.Log_Text_103_str[self.sprache]}')
                        stop += 1
                    else:
                        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_55_str[self.sprache]}')      
                        logger.warning(f"{self.device_name} - {self.Log_Text_133_str[self.sprache]}")    
                        logger.warning(f'{self.device_name} - {self.Log_Text_103_str[self.sprache]}')
                        stop += 1
                except:
                    logger.warning(f"{self.device_name} - {self.Log_Text_134_str[self.sprache]}")
                    logger.exception(f"{self.device_name} - {self.Log_Text_135_str[self.sprache]}")
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_57_str[self.sprache]}') 
                    logger.warning(f'{self.device_name} - {self.Log_Text_103_str[self.sprache]}')
                    stop += 1
                if stop == 10:
                    logger.warning(f'{self.device_name} - {self.Log_Text_183_str[self.sprache]}')
                    break
                time.sleep(0.2)       

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def read(self):
        ''' Lese Eurotherm aus!

        Return: 
            self.value_name (dict): Aktuelle Werte 
        '''
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

        try:
            # Lese Ist-Temperatur:
            temperature = self.read_einzeln(self.read_temperature)
            self.value_name['IWT'] = temperature                                # Einheit: °C
            # Lese Leistungswert:
            op = self.read_einzeln(self.read_op)
            self.value_name['IWOp'] = op                                        # Einheit: %
            # Lese Soll-Temperatur:
            soll_temperatur = self.read_einzeln(self.read_soll_temperatur)
            self.value_name['SWT'] = soll_temperatur                            # Einheit: °C
            # PID-Modus:
            self.value_name['SWTPID'] = self.Soll
            self.value_name['IWTPID'] = self.Ist
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
        
    def read_einzeln(self, befehl):
        ''' Zusammenfassung der einzelnen Sende-Befehle
        
        Args: 
            befehl (str):   Befehlsstring (Steuerzeichen und Mnemonics)

        Return:
            ans (float):    Antwort des Gerätes in Float umgefandelt
        '''
        try:
            self.serial.write(befehl.encode())
            ans = float(self.serial.readline().decode()[3:-2])
        except Exception as e: 
            ans = m.nan         # Input-Filter fängt das ab!
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]} ({befehl.encode()})")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")
        return ans

    def check_HO(self, Read_menu=False):
        ''' lese die maximale Ausgangsleistungs Grenze aus., wenn im Sicherheitsmodus.
        Args:
            Read_menu (bool):   Wenn True wurde der Aufruf im Menü betätigt -> logge Wert!
        Return:
            '' (str):           Fehlerfall
            max_pow (float):    Aktuelle maximale Ausgangsleistung 
        '''
        read = self.read_einzeln(self.read_max_leistung)
        if Read_menu:
            logger.info(f'{self.device_name} - {self.Log_Text_HO[self.sprache]} {read} {self.Log_Text_156_str[self.sprache]}')
        if self.Safety == True:
            max_pow = read
            return max_pow
        return ''
    
    def check_PID(self, extra_str = ''):
        '''Lese die drei Parameter aus und Logge sie!
        Args:
            extra_str (str):    Extra String für den Log!
        '''
        ### XP - proportional band
        self.serial.write("\x040000XP\x05".encode())
        P = str(self.serial.readline().decode()[3:-2])
        ### TI - Integral time
        self.serial.write("\x040000TI\x05".encode())
        I = str(self.serial.readline().decode()[3:-2])
        ### TD - Derivative time
        self.serial.write("\x040000TD\x05".encode())
        D = str(self.serial.readline().decode()[3:-2])
        logger.info(f"{self.device_name} - {self.Log_Text_147_str[self.sprache]} {self.Log_Text_148_str[self.sprache]} {P.strip()}, {self.Log_Text_149_str[self.sprache]} {I.strip()}, {self.Log_Text_150_str[self.sprache]} {D.strip()} {extra_str}")

    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung des Gerätes Eurotherm. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
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
            ## Instrument Identity:
            instrument = {'E440':'3504' , 'E480':'3508' , '9050':'900EPC'}
            self.serial.write("\x040000II\x05".encode())
            ins_ID = str(self.serial.readline().decode()[4:-2])
            try:
                logger.info(f"{self.device_name} - {self.Log_Text_137_str[self.sprache]} {ins_ID} -> {instrument[ins_ID]}")
            except:
                logger.info(f"{self.device_name} - {self.Log_Text_137_str[self.sprache]} {ins_ID}")
            ## Software Version:
            self.serial.write("\x040000V0\x05".encode())
            version = str(self.serial.readline().decode()[4:-2])
            logger.info(f"{self.device_name} - {self.Log_Text_138_str[self.sprache]} {version}")
            ## Instrumenten Modus:
            IM = {0:self.Log_Text_140_str[self.sprache] , 1:self.Log_Text_141_str[self.sprache] , 2:self.Log_Text_142_str[self.sprache]}
            self.serial.write("\x040000IM\x05".encode())
            mode = int(self.serial.readline().decode()[4:-2])
            logger.info(f"{self.device_name} - {self.Log_Text_139_str[self.sprache]} {IM[mode]}")
            ## Display:  
            ### Maximum:
            self.serial.write("\x0400001H\x05".encode())
            max_dis = str(self.serial.readline().decode()[3:-3])
            ### Minimum
            self.serial.write("\x0400001L\x05".encode())
            min_dis = str(self.serial.readline().decode()[3:-3])
            logger.info(f"{self.device_name} - {self.Log_Text_143_str[self.sprache]} {min_dis.strip()} {self.Log_Text_144_str[self.sprache]} {max_dis.strip()} {self.Log_Text_145_str[self.sprache]}")
            ## Sollwert 
            ### Maximum:
            self.serial.write("\x040000HS\x05".encode())
            max_s = str(self.serial.readline().decode()[3:-2])
            ### Minimum:
            self.serial.write("\x040000LS\x05".encode())
            min_s = str(self.serial.readline().decode()[3:-2])
            logger.info(f"{self.device_name} - {self.Log_Text_146_str[self.sprache]} {min_s} {self.Log_Text_144_str[self.sprache]} {max_s} {self.Log_Text_145_str[self.sprache]}")
            ## PID-Regler Parameter:
            ### Schreiben der PID-Parameter wenn gewollt:
            if self.PID_Write:
                self.check_PID(f'({self.Log_Extra[self.sprache]})')
                try:
                    P = round(float(str(self.config['PID-Device']['PB']).replace(',','.')),1)
                    I = round(float(str(self.config['PID-Device']['TI']).replace(',','.')),0)
                    D = round(float(str(self.config['PID-Device']['TD']).replace(',','.')),0)
                    for n in [P, I, D]:
                        if n > 99999 or n < 0:
                            raise ValueError(f'{self.device_name} - {self.Log_Text_PID_N22[self.sprache]} {n} {self.Log_Text_PID_N23[self.sprache]}')
                    self.write_read_answer('XP', str(P), self.write_PB)
                    self.write_read_answer('TI', str(I), self.write_TI)
                    self.write_read_answer('TD', str(D), self.write_TD)
                except Exception as e:
                    logger.warning(f'{self.device_name} - {self.Log_Text_PID_N25[self.sprache]}')
                    logger.exception(f'{self.device_name} - {self.Log_Text_PID_N24[self.sprache]}')
            ## Lese PID-Parameter:
            self.check_PID(f'({self.Log_Extra_2[self.sprache]})')
            ## Statuswort:
            self.serial.write("\x040000SW\x05".encode())
            stWort = str(self.serial.readline().decode()[3:-2])
            logger.info(f"{self.device_name} - {self.Log_Text_151_str[self.sprache]} {stWort}")
            if stWort == '>0000' or stWort == '>8000':
                ## Start-Modus setzen:
                if self.startMode == 'Auto':
                    self.write_read_answer('SW>', '0000', self.write_Modus) 
                    logger.info(f"{self.device_name} - {self.Log_Text_152_str[self.sprache]}")
                elif self.startMode == 'Manuel':
                    self.write_read_answer('SW>', '8000', self.write_Modus)
                    logger.info(f"{self.device_name} - {self.Log_Text_153_str[self.sprache]}")
            else:
                logger.warning(f"{self.device_name} - {self.Log_Text_154_str[self.sprache]}")
            ## Änderung von HO:
            if self.Safety == False:
                self.serial.write("\x040000HO\x05".encode())
                HO_vorher = str(self.serial.readline().decode()[4:-2])
                self.write_read_answer('HO', str(self.oGOp), self.write_max_leistung)
                logger.info(f"{self.device_name} - {self.Log_Text_155_str[self.sprache]} {HO_vorher} {self.Log_Text_156_str[self.sprache]} {self.Log_Text_155_str_1[self.sprache]} {self.oGOp} {self.Log_Text_156_str[self.sprache]}")
            else:
                logger.info(f"{self.device_name} - {self.Log_Text_157_str[self.sprache]}")
            ## Lese HO aus:
            self.serial.write("\x040000HO\x05".encode())
            HO_Aktuel= str(self.serial.readline().decode()[4:-2])
            logger.info(f"{self.device_name} - {self.Log_Text_157_str_1[self.sprache]} {HO_Aktuel} {self.Log_Text_156_str[self.sprache]}")
        except Exception as e:
            if self.init:
                logger.warning(f"{self.device_name} - {self.Log_Text_243_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_244_str[self.sprache]}")
                QCoreApplication.quit()
            else:
                raise Exception(self.Log_Text_243_str[self.sprache]) 
   
    ###################################################
    # Messdatendatei erstellen und beschrieben:
    ###################################################
    def messdaten_output(self, pfad="./"):
        """Erstelle für das Gerät eine csv-Datei mit den Daten.

        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = "# datetime,s,DEG C,DEG C,%,DEG C,DEG C,\n"
        #scaling = f"# -,-,{self.}"
        header = "time_abs,time_rel,Soll-Temperatur,Ist-Temperatur,Operating-point,Soll-Temperatur_PID-Modus,Ist-Temperatur_PID-Modus,\n"
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
            daten (Dict):               Dictionary mit den Daten in der Reihenfolge: 'SWT', 'IWT', 'IWOp'
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
                self.signal_PID.emit(self.Ist, self.Soll, self.mode_aktiv, self.Rez_OP)
                self.op = self.PID.Output

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''

    # def read_Filter(self, wert):
    #     '''Prüfe den Wert auf Richtigkeit: Abfangen von nicht Float- oder Int-Werten!
    #     Args:
    #         wert (float):               Überprüfe die Richtigkeit des Float- oder Int-Wertes
    #     Return:
    #        wert oder m.nan (Bool):      Bei Fehler wird Nan zurück gegeben! Wenn alles Okay wird der gesendete Wert zurückgegeben!
    #     '''
    #     self.Log_Text_Nan_str_1 = ['Der Wert', 'The value']
    #     self.Log_Text_Nan_str_2 = ['hat den Typ String. Wert wird auf Nan gesetzt!', 'has the type String. Value is set to Nan!']

    #     var_type = type(wert)
    #     if var_type == str:
    #         logger.warning(f"{self.device_name} - {self.Log_Text_Nan_str_1[self.sprache]} {wert} {self.Log_Text_Nan_str_2[self.sprache]}")
    #         return m.nan
    #     return wert