# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Educrys Gerät:
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
    

class EducrysHeizer(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, com_dict, test, neustart, multilog_aktiv, Log_WriteReadTime, add_Ablauf_function, name="Educrys-Heizer", typ = 'Generator'):
        """ Erstelle Educrys Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

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
        self.op             = 0
        self.Save_End_State = False
        self.done_ones      = False
        self.mode_aktiv     = False 
        self.Rez_OP         = -1

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
        ### Schnittstelle:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Loop = self.config['serial-extra']['serial-loop-read']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} serial-extra|serial-loop-read {self.Log_Pfad_conf_5[self.sprache]} 10')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Loop = 10
        #//////////////////////////////////////////////////////////////////////
        try: self.rel_Tolleranz = float(self.config['serial-extra']['rel_tol_write_ans'])
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} serial-extra|rel_tol_write_ans {self.Log_Pfad_conf_5[self.sprache]} 1e-02')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.rel_Tolleranz = 1e-02
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Parameter:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.nKS        = self.config['parameter']['nKS_Aus']                     # Nachkommerstellen
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} parameter|nKS_Aus {self.Log_Pfad_conf_5[self.sprache]} 3')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.nKS = 3

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
        ### Sende Educrys PID-Parameter zum Start:
        if not type(self.PID_Write) == bool and not self.PID_Write in [0, 1]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Write - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Write}')
            self.PID_Write = 0 
        ### While-Loop:
        if not type(self.Loop) == int or not self.Loop >= 1:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} serial-loop-read - {self.Log_Pfad_conf_2[self.sprache]} Integer (>=1) - {self.Log_Pfad_conf_3[self.sprache]} 10 - {self.Log_Pfad_conf_8[self.sprache]} {self.Loop}')
            self.Loop = 10
        ### Relative Toleranz:
        if not type(self.rel_Tolleranz) == float or not self.rel_Tolleranz >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} rel_tol_write_ans - {self.Log_Pfad_conf_2[self.sprache]} Float (>=0) - {self.Log_Pfad_conf_3[self.sprache]} 1e-02 - {self.Log_Pfad_conf_8[self.sprache]} {self.rel_Tolleranz}')
            self.rel_Tolleranz = 1e-02
        ### Nachkommerstellen:
        if not type(self.nKS) in [int] or not self.nKS >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nKS_Aus - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 3 - {self.Log_Pfad_conf_8[self.sprache]} {self.nKS}')
            self.nKS = 3

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
        self.Log_Text_64_1_str  = ['Das Gerät konnte nicht angesprochen werden.',                                                                                                                                           'The device could not be addressed.']
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
        self.Log_Text_159_str   = ['Wiederholungs-Versuch',                                                                                                                                                                 'Repeat attempt']
        self.Log_Text_160_str   = ['funktionierte nicht!',                                                                                                                                                                  "did not work!"]
        self.Log_Text_183_str   = ['Das Senden der Werte ist fehlgeschlagen! (Rampe)',                                                                                                                                      'Sending the values failed! (Ramp)']
        self.Log_Text_243_str   = ['Beim Startwert senden an Educrys gab es einen Fehler! Programm wird beendet! Wurde das Gerät eingeschaltet bzw. wurde die Init-Einstellung richtig gesetzt?',                           'There was an error when sending the start value to Educrys! Program will end! Was the device switched on or was the init setting set correctly?']
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
        self.Log_Time_w         = ['Die write-Funktion hat',                                                                                                                                                                'The write function has']     
        self.Log_Time_wr        = ['s gedauert!',                                                                                                                                                                           's lasted!']   
        self.Log_Time_r         = ['Die read-Funktion hat',                                                                                                                                                                 'The read function has']        
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
        self.Log_Edu_11_str     = ['Umwandlung Float fehlgeschlagen! Antwort-Wert:',                                                                                                                                        'Conversion float failed! Response value:']
        self.Log_Edu_12_str     = ['Der erhaltene Wert',                                                                                                                                                                    'The received value']
        self.Log_Edu_13_str     = ['und der gesendete Wert',                                                                                                                                                                'and the sent value']
        self.Log_Edu_14_str     = ['sind sich nicht ähnlich! Relative-Toleranz bei',                                                                                                                                        'are not similar! Relative tolerance at']
        self.Log_Edu_15_str     = ['Der Antwort-String',                                                                                                                                                                    'The response string']
        self.Log_Edu_16_str     = ['ist nicht in der Antwort',                                                                                                                                                              'is not contained in the response']
        self.Log_Edu_17_str     = [' enthalten!',                                                                                                                                                                           '!']
        self.Log_Edu_18_str     = ['Die Antwort des Lese-Befehls beinhaltet weniger als 29 Werte. Dies wird als Fehler gewertet!! Nan-Werte werden eingetragen. Länge Liste:',                                              'The response of the read command contains less than 29 values. This is considered an error!! Nan values ​​are entered. List length:']
        self.Log_Edu_19_str     = ['Start- und Endzeichen stimmen nicht!',                                                                                                                                                  'Start and end characters are wrong!']
        self.Log_Edu_20_str     = ['Leerer String!',                                                                                                                                                                        'Empty string!']
        ## Ablaufdatei: ###############################################################################################################################################################################################################################################################################
        self.Text_51_str        = ['Initialisierung!',                                                                                                                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                                                                       'Initialization Failed!']
        self.Text_53_str        = ['Wert wurde angenommen (ACK)!',                                                                                                                                                          'Value was accepted (ACK)!']
        self.Text_54_str        = ['Wert wurde nicht angenommen (NAK)!',                                                                                                                                                    'Value was not accepted (NAK)!']
        self.Text_55_str        = ['Senden fehlgeschlagen (Keine Antwort)!',                                                                                                                                                'Sending failed (no response)!']
        self.Text_56_str        = ['Befehl gesendet!',                                                                                                                                                                      'command sent!']
        self.Text_57_str        = ['Antwort nicht auslesbar!',                                                                                                                                                              'Answer cannot be read!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                                                                                                                        'Sending failed!']
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
        ## Senden:
        self.Befehl_M = '1M'
        self.Befehl_S = '1S'
        self.Befehl_O = '1O'
        self.Befehl_P = '1P'
        self.Befehl_I = '1I'
        self.Befehl_D = '1D'
        self.abschluss = '\r'

        ## Antwort:
        self.Antworts_String_M = 'm:='
        self.Antworts_String_S = 's:='
        self.Antworts_String_O = 'o:='
        self.Antworts_String_P = 'p:='
        self.Antworts_String_I = 'i:='
        self.Antworts_String_D = 'd:='

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
            # Sollwertn Lesen (OP oder Temp):
            sollwert = write_value['Sollwert']
            PID_write_OP = False
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
                ans = self.read()
                self.Ist = ans['IWT']
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
            self.send_write(self.Befehl_M, 1, self.Antworts_String_M)            
            write_Okay['Auto_Mod'] = False
        elif write_Okay['Manuel_Mod'] or write_Okay['PID']:
            self.send_write(self.Befehl_M, 2, self.Antworts_String_M)    
            write_Okay['Manuel_Mod'] = False

        for auswahl in write_Okay:
            ## Temperatur-Sollwert:
            if write_Okay[auswahl] and auswahl == 'Soll-Temperatur':
                self.send_write(self.Befehl_S, sollwert, self.Antworts_String_S)
                write_Okay[auswahl] = False
            ## Ausgangsleistung OP:
            elif write_Okay[auswahl] and auswahl == 'Operating point':
                if write_value['Rez_OPTemp'] > -1:
                    sollwert = write_value['Rez_OPTemp']
                    write_value['Rez_OPTemp'] = -1
                self.send_write(self.Befehl_O, sollwert, self.Antworts_String_O)
                write_Okay[auswahl] = False
            ## Ausgangsleistung während des PID-Modus:
            elif PID_write_OP:
                self.send_write(self.Befehl_O, PowOutPID, self.Antworts_String_O)
                PID_write_OP = False
            ## Startwerte:
            elif write_Okay[auswahl] and auswahl == 'Start' and not self.neustart:
                self.Start_Werte()
                write_Okay[auswahl] = False
            ## Schreibe die PID-Parameter:
            elif write_Okay[auswahl] and auswahl == 'PID-Update':
                self.send_write(self.Befehl_P, write_value['PID-Update'][0], self.Antworts_String_P)
                self.send_write(self.Befehl_I, write_value['PID-Update'][1], self.Antworts_String_I)
                self.send_write(self.Befehl_D, write_value['PID-Update'][2], self.Antworts_String_D)
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

    def send_write(self, Befehl, Wert, Antworts_String):
        ''' Schreibe Befehle an die Educrys Anlage!

        Args:
            Befehl (str):           Befehls-Teil - Zeichen z.B. 2L 
            Wert (float):           Zweiter Befehls-teil
            Antworts_String (str):  Aussehen des Antwortsstring - z.B. l:=
        ''' 
        n = 0
        try:
            # Reset Buffer:
            self.serial.reset_input_buffer()
            
            # Sende den Befehl:
            self.serial.write((Befehl+str(Wert)+self.abschluss).encode())
            logger.debug(f'{self.device_name} - {self.Log_Edu_1_str[self.sprache]} {(Befehl+str(Wert)+self.abschluss).encode()}')
            # Warte kurz:
            time.sleep(0.1)
            # Lese die Antwort und Vergleiche sie:
            ans = self.read_out(10)
            ans = ans.strip().replace('\r\n','')
            check = self.answer_check_write(Wert, ans, Antworts_String, Befehl+str(Wert))

            if not check:  logger.debug(f'{self.device_name} - {self.Log_Edu_2_str[self.sprache]} {ans}')
            else:                    
                logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Edu_4_str[self.sprache]} - {self.Log_Edu_2_str[self.sprache]} {ans} ({Befehl+str(Wert)})')       

                ans = self.read_out(10)
                ans = ans.strip().replace('\r\n','')
                check = self.answer_check_write(Wert, ans, Antworts_String, Befehl+str(Wert))

                if not check:  logger.debug(f'{self.device_name} - {self.Log_Edu_2_str[self.sprache]} {ans}')
                else:                    
                    logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Edu_5_str[self.sprache]} - {self.Log_Edu_2_str[self.sprache]} {ans} ({Befehl+str(Wert)})') 

                    # Antwort stimmt nicht:
                    while n != self.Loop:
                        self.serial.write((Befehl+str(Wert)+self.abschluss).encode())
                        logger.debug(f'{self.device_name} - {self.Log_Edu_1_str[self.sprache]} {(Befehl+str(Wert)+self.abschluss).encode()}')
                        time.sleep(0.1)
                        ans = self.read_out(10)
                        ans = ans.strip().replace('\r\n','')
                        check = self.answer_check_write(Wert, ans, Antworts_String, Befehl+str(Wert))
                        if not check:  
                            logger.debug(f'{self.device_name} - {self.Log_Edu_2_str[self.sprache]} {ans}') 
                            break
                        else:                       
                            logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Text_159_str[self.sprache]} {n} {self.Log_Text_160_str[self.sprache]} - {self.Log_Edu_2_str[self.sprache]} {ans} ({Befehl+str(Wert)})') 
                            n += 1 

            if n == self.Loop:
                logger.warning(f"{self.device_name} - {self.Log_Edu_6_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]} ({Befehl+str(Wert)})')
            else:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_Edu_1_str[self.sprache]} {Befehl+str(Wert)} {self.Text_Edu_2_str[self.sprache]}') 
        except:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_1_str[self.sprache]} ({Befehl+str(Wert)})")
            logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")  

    def answer_check_write(self, value_send, answer_read, res, befehl):
        ''' Überprüfe die Antwort eines Schreibbefehls! (Aussnahme ist !-Befehl)

        Args:
            value_send (float):     Wert der gesendet wurde
            answer_read (str):      Antwort des Gerätes auf einen Schreib-Befehl - Aufbau z.B. l:=10.00
            res (str):              gewollter Teil der Antwort
            befehl (str):           um Log-Nachrichten zuordnen zu können
        return:
            error (bool):           True  - Es gab einen Fehler in der Toleranz oder der Antwort!
                                    False - Antwort ist richtig
        '''
        error = False
        if res in answer_read:                      # Ist der Antwort-String in der Antwort?
            ans_value = answer_read[3:]             # Wert vom String entfernen

            ## Wandel String zu Float:
            try:    ans_value = float(ans_value)
            except:
                    logger.warning(f'{self.Log_Edu_11_str[self.sprache]} {ans_value} ({befehl})')
                    return False

            ## Überprüfe die Toleranz:
            ans_bool = m.isclose(value_send, ans_value, rel_tol=self.rel_Tolleranz)
            
            if not ans_bool:    
                logger.warning(f'{self.Log_Edu_12_str[self.sprache]} ({ans_value}) {self.Log_Edu_13_str[self.sprache]} ({value_send}) {self.Log_Edu_14_str[self.sprache]} {self.rel_Tolleranz}! ({befehl})')        
        else:
            logger.warning(f'{self.Log_Edu_15_str[self.sprache]} ({res}) {self.Log_Edu_16_str[self.sprache]} ({answer_read}){self.Log_Edu_17_str[self.sprache]}  ({befehl})')
            error = True

        return error

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def read(self):
        ''' Sende Befehle an die Achse um Werte auszulesen.

        Return: 
            Aktuelle Werte (dict)   - self.value_name
        '''
        # Time Check 1:
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

        # Variablen:
        error           = False   
        listen_Error    = False
        n               = 0

        try:
            # Sende Auslese-Befehl:
            ## Besteht aus vielen Werten im Format *Wert_1 Wert_2#
            self.serial.write(('!'+ self.abschluss).encode())
            ## Etwas Zeit lassen:
            time.sleep(0.1)

            # Antwort lesen:
            ans = self.read_out_AZ()
            ans = ans.replace('\r','').replace('\n','').strip()
            logger.debug(f'{self.device_name} - {self.Log_Edu_7_str[self.sprache]} {ans}') 
            ''' Relevante Werte:
                                                    Liste (0 - Ende)            Stelle (1 - Ende)
                         Heizer:    T-Ist           17                          18
                                    T-Soll          19                          20
                                    OP-Ist          15                          16
            ''' 
            ## Antwort prüfen:
            ### Fehlerfall 1 - End- und Startzeichen richtig:
            start_end = True
            if ans != '':
                if ans[0] == '*' and ans[-1] == '#':    ans = ans.replace('*', '').replace('#','').strip()    
                else:                                   ans, start_end = '', False

            ### Fehlerfall 2 - String ist Leer - Erneut Senden:    
            if ans == '':  
                logger.warning(f'{self.device_name} - {self.Log_Edu_3_str[self.sprache]} {self.Log_Edu_5_str[self.sprache]} {self.Log_Edu_19_str[self.sprache] if not start_end else self.Log_Edu_20_str[self.sprache]} (!)')
                while n != self.Loop: 
                    #### Erneut Senden:
                    self.serial.write(('!'+self.abschluss).encode())
                    time.sleep(0.1)
                    #### Antwort Lesen:
                    ans = self.read_out_AZ()
                    ans = ans.replace('\r','').replace('\n','').strip()
                    #### Kontrolle:
                    start_end = True
                    if ans != '':
                        if ans[0] == '*' and ans[-1] == '#':    ans = ans.replace('*', '').replace('#','').strip()     
                        else:                                   ans, start_end = '', False
                    #### Auswerten:
                    if ans == '':   n += 1
                    else:
                        logger.debug(f'{self.device_name} - {self.Log_Edu_7_str[self.sprache]} {ans}')
                        break

            ### While-Schleife hat Anschlag erreicht und wurde beendet:           
            if n == self.Loop:
                logger.warning(f"{self.device_name} - {self.Log_Edu_6_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]} (!)')
                error = True
            else:
                logging.debug(f'{self.device_name} - {self.Text_Edu_1_str[self.sprache]} ! {self.Text_Edu_2_str[self.sprache]}')
            
            ### Kein Fehler:
            if not error:
                #### Liste erstellen - Fehlerfall 3 - Liste nicht erstellebar:
                try:
                    liste = ans.split(' ')
                except:
                    listen_Error = True
                
                #### Fehlerfall 4 - Liste hat nicht die richtige Länge:
                if len(liste) != 29 or listen_Error:
                    logger.warning(f"{self.device_name} - {self.Log_Edu_18_str[self.sprache]} {len(liste)}")
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]} (!)')
                    liste = []
                    for i in range(0,29,1):
                        liste.append(m.nan)

                ## Werte eintragen:
                self.value_name['IWT']  = round(float(liste[17]), self.nKS)
                self.value_name['SWT']  = round(float(liste[19]), self.nKS)
                self.value_name['IWOp'] = round(float(liste[15]), self.nKS)
            else:
                ## Bei Fehler Nan einfügen:
                self.value_name['IWT']  = m.nan
                self.value_name['SWT']  = m.nan
                self.value_name['IWOp'] = m.nan

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

    def read_out(self, Anz):
        '''Liest eine bestimmte Anzahl von Zeichen aus, verbindet diese und gibt einen String zurück!
        
        Args:
            Anz (int):      Anzahl der maximal zu lesenden Zeichen
        
        Return:
            ans_join (Str): Zurückgegebener String (Bei Fehler Leerer String)
        '''
        try:
            ans_list = []                                   # Leere Liste
            i = 0                                           # Kontroll Variable (Zeichen)
            while 1:                                        # Endlosschleife
                z = self.serial.read()                      # Lese Zeichen
                if z != '': ans_list.append(z.decode())     # Wenn nicht Leer, dann füge an Liste
                if z == b'\n':  break                       # Wenn \n (Newline) beende Endlosschleife
                if i >= Anz:    break                       # Wenn Anzahl Zeichen überschritten oder gleich, dann Beende Endlosschleife
                i += 1                                      # Erhöhe Zählvariable
            ans_join = ''.join(ans_list)                    # Verbinde die Liste zu einem String
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")
            ans_join = ''

        return ans_join
    
    def read_out_AZ(self):
        '''Liest eine bestimmte Anzahl von Zeichen aus, verbindet diese und gibt einen String zurück!
        Seperate Funktion für !-Befehl!

        Return:
            ans_join (Str): Zurückgegebener String (Bei Fehler Leerer String)
        '''
        try:
            ans_list    = []                                # Leere Liste
            i           = 0                                 # Kontroll Variable (Zeichen)
            max_anz     = 200   
            try_read = 0                            
            while 1:                                        # Endlosschleife
                z = self.serial.read()                      # Lese Zeichen
                if z != '': ans_list.append(z.decode())     # Wenn nicht Leer, dann füge an Liste
                if z == b'#':  break                        # Wenn \n (Newline) beende Endlosschleife
                if z == b'*':                               # Start-Zeichen gefunden - Beginne!
                    i = 0
                    ans_list = []
                    ans_list.append(z.decode())             # Füge das Start-Zeichen an
                if i >= max_anz:                            # Wenn Anzahl Zeichen überschritten oder gleich, dann Beende Endlosschleife
                    if z != '#':        
                        try_read += 1
                        max_anz += 50
                    if try_read > 3:    break                       
                i += 1                                      # Erhöhe Zählvariable
            ans_join = ''.join(ans_list)                    # Verbinde die Liste zu einem String
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")
            ans_join = ''

        return ans_join

    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung des Gerätes Educrys. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
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
            ## PID-Regler Parameter:
            ### Schreiben der PID-Parameter wenn gewollt:
            if self.PID_Write:
                try:
                    P = round(float(str(self.config['PID-Device']['PB']).replace(',','.')),1)
                    I = round(float(str(self.config['PID-Device']['TI']).replace(',','.')),0)
                    D = round(float(str(self.config['PID-Device']['TD']).replace(',','.')),0)
                    self.send_write(self.Befehl_P, P, self.Antworts_String_P)
                    self.send_write(self.Befehl_I, I, self.Antworts_String_I)
                    self.send_write(self.Befehl_D, D, self.Antworts_String_D)
                except Exception as e:
                    logger.warning(f'{self.device_name} - {self.Log_Text_PID_N25[self.sprache]}')
                    logger.exception(f'{self.device_name} - {self.Log_Text_PID_N24[self.sprache]}')
            ## Start-Modus setzen:
            if self.startMode == 'Auto':
                self.send_write(self.Befehl_M, 1, self.Antworts_String_M)   
                logger.info(f"{self.device_name} - {self.Log_Text_152_str[self.sprache]}")
            elif self.startMode == 'Manuel':
                self.send_write(self.Befehl_M, 2, self.Antworts_String_M) 
                logger.info(f"{self.device_name} - {self.Log_Text_153_str[self.sprache]}")
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