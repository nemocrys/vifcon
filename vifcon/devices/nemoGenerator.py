# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo Generator:
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
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import time
import math as m
import datetime

## Eigene:
from .PID import PID

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class SerialMock: # Notiz: Näher ansehen!
    """ This class is used to mock a serial interface for debugging purposes. """

    def write(self, _):
        pass

    def readline(self):
        return "".encode()

class NemoGenerator(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, com_dict, test, neustart, multilog_aktiv, Log_WriteReadTime, add_Ablauf_function, name="Nemo-Generator", typ = 'Generator'):
        """ Erstelle Nemo-Generator Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

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
        self.Log_Pfad_conf_5_1  = ['; Adressen-Fehler -> Programm zu Ende!!!',                                                                                                                                              '; Address error -> program ends!!!']
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
        ## Übergeordnet:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Anlage = self.config['nemo-Version']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} nemo-Version {self.Log_Pfad_conf_5[self.sprache]} 2')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Anlage = 2
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Zum Start:
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
        try: self.startMod   = self.config['start']['start_modus'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|start_modus {self.Log_Pfad_conf_5[self.sprache]} I')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startMod = 'I'
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Parameter:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.nKS        = self.config['parameter']['nKS_Aus']                     # Nachkommerstellen
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} parameter|nKS_Aus {self.Log_Pfad_conf_5[self.sprache]} 3')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.nKS = 3
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      
        ## Limits:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
        #//////////////////////////////////////////////////////////////////////
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
        #//////////////////////////////////////////////////////////////////////
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
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## PID:
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
        ## Register:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.reg_GEin                  = self.config['register']['gen_Ein']             # Generator Ein Coil Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|gen_Ein {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_GAus                  = self.config['register']['gen_Aus']             # Generator Aus Coil Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|gen_Aus {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_PEin                  = self.config['register']['gen_P_Ein']             # Generator Leistungswahl Coil Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|gen_P_Ein {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_IEin                  = self.config['register']['gen_I_Ein']             # Generator Stromwahl Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|gen_I_Ein {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_UEin                  = self.config['register']['gen_U_Ein']             # Generator Spannungswahl Coil Rergister
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|gen_U_Ein {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_lese_SollIst         = self.config['register']['lese_st_Reg']             # Soll- und Istwert Input Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_lese_Info            = self.config['register']['lese_st_Reg_Info']             # Info Input Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg_Info {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_Status               = self.config['register']['lese_st_Reg_Status']             # Status Input Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg_Status {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_lese_Kombi           = self.config['register']['lese_st_Reg_Gkombi']             # Generator Schnittstelle/Kombi Input Register
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg_Gkombi {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.reg_write_Soll           = self.config['register']['write_Soll_Reg']             # Schreibe Sollwert Holding Rergister
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|write_Soll_Reg {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        
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
        ### Register Generator Ein:
        if not type(self.reg_GEin) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} gen_Ein - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator Aus:
        if not type(self.reg_GAus) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} gen_Aus - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator P-Wahl:
        if not type(self.reg_PEin) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} gen_P_Ein - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator I-Wahl:
        if not type(self.reg_IEin) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} gen_I_Ein - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator U-Wahl:
        if not type(self.reg_UEin) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} gen_U_Ein - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator Soll- und Istwerte lesen:
        if not type(self.reg_lese_SollIst) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator Informationen lesen:
        if not type(self.reg_lese_Info) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg_Info - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator Status lesen:
        if not type(self.reg_Status) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg_Status - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator Schnittstelle lesen:
        if not type(self.reg_lese_Kombi) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg_Gkombi - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Register Generator Sollwert schreiben:
        if not type(self.reg_write_Soll) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} write_Soll_Reg - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.reg_r)}')
            exit()
        ### Messzeit:
        if not type(self.messZeit) in [int, float] or not self.messZeit >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} readTime - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 2 - {self.Log_Pfad_conf_8[self.sprache]} {self.messZeit}')
            self.messZeit = 2
        ### PID Sample Zeit:
        if not type(self.PID_Sample_Time) in [int] or not self.PID_Sample_Time >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} sample - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 500 - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Sample_Time}')
            self.PID_Sample_Time = 500
        ### PID-Wert-Fehler:
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
        ### PID-Start-Soll:
        if not type(self.Soll) in [float, int] or not self.Soll >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_soll - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.Soll}')
            self.Soll = 0
        ### PID-Start-Ist:
        if not type(self.Ist) in [float, int] or not self.Ist >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_ist - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.Ist}')
            self.Ist = 0
        ### Anlagen-Version:
        if not self.Anlage in [2]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nemo-Version - {self.Log_Pfad_conf_2[self.sprache]} [2] - {self.Log_Pfad_conf_3[self.sprache]} 2')
            self.Anlage = 2
        ### Start-Modus:
        if not self.startMod in ['P', 'I', 'U']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_modus - {self.Log_Pfad_conf_2[self.sprache]} [P, I, U] - {self.Log_Pfad_conf_3[self.sprache]} I - {self.Log_Pfad_conf_8[self.sprache]} {self.startMod}')
            self.startMod = 'I'
        ### Leistungs-Limit:
        if not type(self.oGP) in [float, int] or not self.oGP >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGP)}')
            self.oGP = 1
        if not type(self.uGP) in [float, int] or not self.oGP >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minP - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGP)}')
            self.uGP = 0
        if self.oGP <= self.uGP:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_12[self.sprache]})')
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
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_12[self.sprache]})')
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
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_12[self.sprache]})')
            self.uGU = 0
            self.oGU = 1
        
        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging: ##################################################################################################################################################################################################################################################################################
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                                                                                                                                   'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',                                                                                                                'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                                                                                                                                 'Error reason (interface structure):']
        self.Log_Text_63_str    = ['Antwort Messwerte:',                                                                                                                                                                    'Answer measurements:']
        self.Log_Text_66_str    = ['Antwort Register Integer:',                                                                                                                                                             'Response Register Integer:']
        self.Log_Text_67_str    = ['Messwerte Umgewandelt - Messwert',                                                                                                                                                      'Measured Values Converted - Measured Value']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                                                                                                                                          'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                                                                                                                       'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                                                                                                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                                                                                                                  'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                                                                                                                       'No measurement data recording active!']
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                                                                                                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                                                                                                                'Error reason (send):']
        self.Log_Text_105_str   = ['Lese Istwert Leistung',                                                                                                                                                                 'Read actual value power']
        self.Log_Text_106_str   = ['Lese Istwert Spannung',                                                                                                                                                                 'Read actual voltage value']
        self.Log_Text_107_str   = ['Lese Istwert Strom',                                                                                                                                                                    'Read actual current value']
        self.Log_Text_108_str   = ['Lese Istwert Frequenz',                                                                                                                                                                 'Read actual frequency value']
        self.Log_Text_109_str   = ['Lese Sollwert Leistung',                                                                                                                                                                'Read setpoint power']
        self.Log_Text_110_str   = ['Lese Sollwert Spannung',                                                                                                                                                                'Read setpoint voltage']
        self.Log_Text_111_str   = ['Lese Sollwert Strom',                                                                                                                                                                   'Read setpoint current']
        self.Log_Text_112_str   = ['Fehler Grund (Auslesen):',                                                                                                                                                              'Error reason (reading):']
        self.Log_Text_123_str   = ['kW',                                                                                                                                                                                    'kW']
        self.Log_Text_125_str   = ['V',                                                                                                                                                                                     'V']
        self.Log_Text_127_str   = ['A',                                                                                                                                                                                     'A']
        self.Log_Text_172_str   = ['Befehl wurde nicht akzeptiert (Sollwert)!',                                                                                                                                             'Command was not accepted (setpoint)!']
        self.Log_Text_173_str   = ['Das Senden des Sollwertes an das Gerät ist fehlgeschlagen!',                                                                                                                            'Sending setpoint to device failed!']
        self.Log_Text_174_str   = ['Fehler Grund (Sende Sollwert):',                                                                                                                                                        'Error reason (send setpoint):']
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
        self.Log_Text_PID1_str  = ['Die PID-Start-Modus aus der Config-Datei existiert nicht! Setze auf Default P! Fehlerhafter Eintrag:',                                                                                  'The PID start mode from the config file does not exist! Set to default P! Incorrect entry:']
        self.Log_Test_Ex_1      = ['Der Variablen-Typ der Größe',                                                                                                                                                           'The variable type of size']
        self.Log_Test_Ex_2      = ['ist nicht Float! Setze Nan ein! Fehlerhafter Wert:',                                                                                                                                    'is not Float! Insert Nan! Incorrect value:']
        self.Log_Filter_PID_S   = ['Sollwert',                                                                                                                                                                              'Setpoint'] 
        self.Log_Filter_PID_I   = ['Istwert',                                                                                                                                                                               'Actual value'] 
        self.Log_Time_w         = ['Die write-Funktion hat',                                                                                                                                                                'The write function has']     
        self.Log_Time_wr        = ['s gedauert!',                                                                                                                                                                           's lasted!']   
        self.Log_Time_r         = ['Die read-Funktion hat',                                                                                                                                                                 'The read function has']  
        self.Log_Text_NG_1      = ['Auswahl P-Modus wurde nicht akzeptiert!',                                                                                                                                               'P-mode selection was not accepted!']
        self.Log_Text_NG_2      = ['Auswahl I-Modus wurde nicht akzeptiert!',                                                                                                                                               'I-mode selection was not accepted!']
        self.Log_Text_NG_3      = ['Auswahl U-Modus wurde nicht akzeptiert!',                                                                                                                                               'U-mode selection was not accepted!']
        self.Log_Text_NG_4      = ['Befehl Generator Ein wurde nicht akzeptiert!',                                                                                                                                          'Command Generator On was not accepted!']
        self.Log_Text_NG_5      = ['Befehl Generator Aus wurde nicht akzeptiert!',                                                                                                                                          'Command Generator Off was not accepted!']
        self.Log_Text_Port_1    = ['Verbindungsfehler:',                                                                                                                                                                    'Connection error:']
        self.Log_Text_Port_2    = ['Der Test für den Verbindungsaufbau ist fehlgeschlagen!',                                                                                                                                'The connection establishment test failed!']
        self.Log_Text_Port_3    = ['Antwort der Test-Abfrage war None. Bearbeitung nicht möglich!',                                                                                                                         'The answer to the test query was None. Processing not possible!']
        self.Log_Text_Port_4    = ['Bei der Werte-Umwandlung ist ein Fehler aufgetreten!',                                                                                                                                  'An error occurred during value conversion!']
        self.Log_Text_Port_5    = ['Fehlerbeschreibung:',                                                                                                                                                                   'Error description:']
        self.Log_ST_NG_1        = ['Fehler bei den Start-Werten!',                                                                                                                                                          'Error in the initial values!']
        self.Log_ST_NG_2        = ['Fehler',                                                                                                                                                                                'Error']
        self.Log_ST_NG_3        = ['Schnittstelle 1',                                                                                                                                                                       'Interface 1']
        self.Log_ST_NG_4        = ['Schnittstelle 2',                                                                                                                                                                       'Interface 2']
        self.Log_ST_NG_5        = ['Schnittstelle 3',                                                                                                                                                                       'Interface 3']
        self.Log_ST_NG_6        = ['Schnittstelle 1 und 2',                                                                                                                                                                 'Interface 1 and 2']
        self.Log_ST_NG_7        = ['Schnittstelle 1 und 3',                                                                                                                                                                 'Interface 1 and 3']
        self.Log_ST_NG_8        = ['Schnittstelle 2 und 3',                                                                                                                                                                 'Interface 2 and 3']
        self.Log_ST_NG_9        = ['Der Generator',                                                                                                                                                                         'The Generator']
        self.Log_ST_NG_10       = ['wurde an der Anlage ausgewählt - siehe Service bzw. Typ und Limit-Werte!',                                                                                                              'was selected on the system - see service or typ and limit values!']
        self.Log_ST_NG_11       = ['Leistungsmaximum = ',                                                                                                                                                                   'Power Maximum     = ']
        self.Log_ST_NG_12       = ['Strommaximum     = ',                                                                                                                                                                   'Current maximum   = ']
        self.Log_ST_NG_13       = ['Spannungsmaximum = ',                                                                                                                                                                   'Voltage maximum   = ']
        self.Log_ST_NG_14       = ['Frequenzmaximum  = ',                                                                                                                                                                   'Frequency maximum = ']
        self.Log_ST_NG_15       = ['Hz',                                                                                                                                                                                    'Hz']
        self.Log_ST_NG_16       = ['Der gewählte Generator hat den Typ:',                                                                                                                                                   'The selected generator has the typ:']
        self.Log_ST_NG_17       = ['Generator-Anlagen-GUI Kombination',                                                                                                                                                     'Generator-Plant-GUI Combination']
        self.Log_ST_NG_18       = ['Bei der Umwandlung des Typs gab es einen Fehler!',                                                                                                                                      'There was an error while converting the typ!']
        self.Log_Text_PIDVV     = ['Noch nicht vollkommen implementiert, Vifcon als PID-Input Sollwert! Hier wird Istwert auf Sollwert gesetzt!',                                                                           'Not yet fully implemented, Vifcon as PID input setpoint!! Here the actual value is set to the target value!']
        ## Ablaufdatei: ###############################################################################################################################################################################################################################################################################
        self.Text_51_str        = ['Initialisierung!',                                                                                                                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                                                                       'Initialization Failed!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                                                                                                                        'Sending failed!']
        self.Text_69_str        = ['Sollwert erfolgreich gesendet!',                                                                                                                                                        'Setpoint sent successfully!']
        self.Text_70_str        = ['Befehl sende Sollwert fehlgeschlagen!',                                                                                                                                                 'Command send setpoint failed!']
        self.Text_NG_1          = ['Auswahl P-Modus fehlgeschlagen!',                                                                                                                                                       'Selection P-mode failed!']
        self.Text_NG_2          = ['Auswahl P-Modus erfolgreich gesendet!',                                                                                                                                                 'Selection P-mode sent successfully!']
        self.Text_NG_3          = ['Auswahl I-Modus fehlgeschlagen!',                                                                                                                                                       'Selection I-mode failed!']
        self.Text_NG_4          = ['Auswahl I-Modus erfolgreich gesendet!',                                                                                                                                                 'Selection I-mode sent successfully!']
        self.Text_NG_5          = ['Auswahl U-Modus fehlgeschlagen!',                                                                                                                                                       'Selection U-mode failed!']
        self.Text_NG_6          = ['Auswahl U-Modus erfolgreich gesendet!',                                                                                                                                                 'Selection U-mode sent successfully!']
        self.Text_NG_7          = ['Befehl Generator Ein fehlgeschlagen!',                                                                                                                                                  'Command Generator On failed!']
        self.Text_NG_8          = ['Befehl Generator Ein erfolgreich gesendet!',                                                                                                                                            'Command Generator On sent successfully!']
        self.Text_NG_9          = ['Befehl Generator Aus fehlgeschlagen!',                                                                                                                                                  'Command Generator Off failed!']
        self.Text_NG_10         = ['Befehl Generator Aus erfolgreich gesendet!',                                                                                                                                            'Command Generator Off sent successfully!']

        #---------------------------------------
        # Werte Dictionary:
        #---------------------------------------
        self.value_name = {'IWP': 0, 'IWU': 0, 'IWI': 0, 'IWf': 0, 'SWP': 0, 'SWU': 0, 'SWI': 0, 'SWxPID': self.Soll, 'IWxPID': self.Ist, 'Status': 0, 'Status_Name': '', 'Status_Typ': 0, 'Status_Kombi': 0}

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
                    self.serial = ModbusClient(**config["serial-interface"])
                else:
                    self.serial = com_dict[com_ak]
        except Exception as e:
            self.serial = SerialMock()
            logger.warning(f"{self.device_name} - {self.Log_Text_61_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_62_str[self.sprache]}")
            exit()
        
        if self.init and not test:
            Meldungen = False
            for n in range(0,5,1):
                if not self.serial.is_open:
                    self.Test_Connection(Meldungen)
                if n == 4:
                    Meldungen = True
            if not self.serial.is_open:
                logger.warning(f"{self.device_name} - {self.Log_Text_Port_2[self.sprache]}")
                logger.warning(f"{self.device_name} - {self.Log_Text_61_str[self.sprache]}")
                exit()
        
        #---------------------------------------
        # Befehle:
        #---------------------------------------
        self.lese_anz_Register_SI   = 12
        self.lese_anz_Register_Info = 19
        self.lese_anz_Register_GK   = 1
        self.lese_anz_Register_Stat = 1

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        if not self.startMod in ['P', 'I', 'U']:
            logger.warning(f'{self.device_name} - {self.Log_Text_PID1_str} {self.startMod}')
            self.startMod = 'I'
        if self.startMod == 'P':      oG, uG, unit, self.ak_Size = self.oGP, self.uGP, self.Log_Text_123_str[self.sprache], 'P'
        elif self.startMod == 'I':    oG, uG, unit, self.ak_Size = self.oGI, self.uGI, self.Log_Text_127_str[self.sprache], 'I'
        elif self.startMod == 'U':    oG, uG, unit, self.ak_Size = self.oGU, self.uGU, self.Log_Text_125_str[self.sprache], 'U'

        self.PID = PID(self.sprache, self.device_name, self.PID_Config, oG, uG, self.add_Text_To_Ablauf_Datei)
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
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]}: {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {unit}')
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
        ''' Schreiben der übergebenden Werte, wenn der richtige Knopf betätigt wurde!

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
            self.PID.OutMax = write_value['Limits'][0]
            self.PID.OutMin = write_value['Limits'][1]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {write_value["Limit Unit"]}')
            ## PID-Input:
            if write_value['Limits'][4]:
                self.PID_Input_Limit_Max = write_value['Limits'][2]
                self.PID_Input_Limit_Min = write_value['Limits'][3]
                logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max} {self.unit_PIDIn}')
                
            write_Okay['Update Limit'] = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Aktuelle Größe:
        #++++++++++++++++++++++++++++++++++++++++++
        self.ak_Size = write_value['Ak_Size']

        #++++++++++++++++++++++++++++++++++++++++++
        # Normaler Betrieb:
        #++++++++++++++++++++++++++++++++++++++++++
        if not write_Okay['PID']:  
            ## Sollwert Lesen:
            sollwert = write_value['Sollwert']      # in eine Zahl umgewandelter Wert (Float)
            PID_write_wert = False
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
            wert_vorgabe    = self.PID_Out
            PID_write_wert  = True

        #++++++++++++++++++++++++++++++++++++++++++
        # Schreiben:
        #++++++++++++++++++++++++++++++++++++++++++
        for auswahl in write_Okay:
            ## P-Auswahl:
            if write_Okay[auswahl] and auswahl == 'Wahl_P':
                ans = self.serial.write_single_coil(self.reg_PEin, True)
                if not ans:
                    logger.warning(f'{self.device_name} - {self.Log_Text_NG_1[self.sprache]}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_1[self.sprache]}') 
                else:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_2[self.sprache]}')  
                write_Okay[auswahl] = False
            ## I-Auswahl:
            elif write_Okay[auswahl] and auswahl == 'Wahl_I':
                ans = self.serial.write_single_coil(self.reg_IEin, True)
                if not ans:
                    logger.warning(f'{self.device_name} - {self.Log_Text_NG_2[self.sprache]}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_3[self.sprache]}') 
                else:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_4[self.sprache]}') 
                write_Okay[auswahl] = False
            ## U-Auswahl:
            elif write_Okay[auswahl] and auswahl == 'Wahl_U':
                ans = self.serial.write_single_coil(self.reg_UEin, True)
                if not ans:
                    logger.warning(f'{self.device_name} - {self.Log_Text_NG_3[self.sprache]}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_5[self.sprache]}') 
                else:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_6[self.sprache]}') 
                write_Okay[auswahl] = False
            ## Sende Soll-Leistung:
            elif write_Okay[auswahl] and auswahl == 'Soll-Leistung':
                self.write_PUI(sollwert)
                write_Okay[auswahl] = False
            ## Sende Soll-Strom:
            elif write_Okay[auswahl] and auswahl == 'Soll-Strom':
                self.write_PUI(sollwert)
                write_Okay[auswahl] = False
            ## Sende Soll-Spannung:
            elif write_Okay[auswahl] and auswahl == 'Soll-Spannung':
                self.write_PUI(sollwert)
                write_Okay[auswahl] = False
            ## PID-Modus:
            elif PID_write_wert:
                self.write_PUI(wert_vorgabe)
                PID_write_wert = False
            ## Schalte Generator Ein:
            elif write_Okay[auswahl] and auswahl == 'Ein':
                ans = self.serial.write_single_coil(self.reg_GEin, True)
                if not ans:
                    logger.warning(f'{self.device_name} - {self.Log_Text_NG_4[self.sprache]}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_7[self.sprache]}') 
                else:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_8[self.sprache]}') 
                write_Okay[auswahl] = False
            ## Schalte Generator Aus:
            elif write_Okay[auswahl] and auswahl == 'Aus':
                ans = self.serial.write_single_coil(self.reg_GAus, True)
                if not ans:
                    logger.warning(f'{self.device_name} - {self.Log_Text_NG_5[self.sprache]}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_9[self.sprache]}') 
                else:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_NG_10[self.sprache]}') 
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

    def write_PUI(self, sollwert):
        ''' Schreibe den gewollten Sollwert in das Register
        
        Args:
            sollwert (float):   Sollwert 
        Return:
            ans (bool):         Senden funktioniert
            False:              Exception ausgelöst!         
        '''
        try:
            sollwert = round(sollwert, 2)                       
            sollwert_hex = utils.encode_ieee(sollwert)
            if sollwert_hex == 0:
                sollwert_hex = '0x00000000'
            else:
                sollwert_hex = hex(sollwert_hex)[2:]            # Wegschneiden von 0x
            sollwert_hex_HB = sollwert_hex[0:4]                 # ersten 4 Bit
            sollwert_hex_LB = sollwert_hex[4:]                  # letzten 4 Bit

            ans = self.serial.write_multiple_registers(self.reg_write_Soll, [int(sollwert_hex_HB,16), int(sollwert_hex_LB,16)])
            if ans:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_69_str[self.sprache]}') 
            else:
                logger.warning(f'{self.device_name} - {self.Log_Text_172_str[self.sprache]}')
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_70_str[self.sprache]}') 
                ans = False
            return ans 
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_173_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_174_str[self.sprache]}")
            return False

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def read(self):
        ''' Sende Befehle an die Anlage um Werte auszulesen.

        Return: 
            Aktuelle Werte (dict)   - self.value_name
        '''
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

        # Lese: Soll, PIst, IIst, UIst, AHFSoll, fIst -> AHFSoll exestiert nicht mehr
        ans = self.serial.read_input_registers(self.reg_lese_SollIst, self.lese_anz_Register_SI)
        logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')
        value = self.umwandeln_Float(ans)

        # Fehlerfall:
        if value == []: value = [m.nan, m.nan, m.nan, m.nan, m.nan, m.nan]

        # Kontrolle der ausgelesenen Werte:
        i = 0
        value_Def = ['SW', 'IWP', 'IWI', 'IWU', 'SWAHf', 'IWf']
        for n in value:
            if not type(n) == float:    
                value[i] = m.nan
                logger.warning(f'{self.Log_Test_Ex_1[self.sprache]} {value_Def[i]} {self.Log_Test_Ex_2[self.sprache]} {n}')
            i += 1
        
        # Reiehnfolge: vIst, vSoll, posIst, posSoll, posMax, posMin
        self.value_name['SWP']  = round(value[0], self.nKS) if self.ak_Size == 'P' else 0                    # Einheit: kW 
        self.value_name['SWI']  = round(value[0], self.nKS) if self.ak_Size == 'I' else 0                    # Einheit: A
        self.value_name['SWU']  = round(value[0], self.nKS) if self.ak_Size == 'U' else 0                    # Einheit: V
        self.value_name['IWP']  = round(value[1], self.nKS)                                                  # Einheit: kW
        self.value_name['IWI']  = round(value[2], self.nKS)                                                  # Einheit: A
        self.value_name['IWU']  = round(value[3], self.nKS)                                                  # Einheit: V
        self.value_name['IWf']  = round(value[5], self.nKS)                                                  # Einheit: Hz

        # Lese: Status
        ans = self.serial.read_input_registers(self.reg_Status, self.lese_anz_Register_Stat)
        if not ans == None and type(ans[0]) == int: self.value_name['Status'] = ans[0]
        else:                                       self.value_name['Status'] = 64

        # PID-Modus:
        self.value_name['SWxPID'] = self.Soll
        self.value_name['IWxPID'] = self.Ist

        #++++++++++++++++++++++++++++++++++++++++++
        # Funktions-Dauer aufnehmen:
        #++++++++++++++++++++++++++++++++++++++++++
        timediff = (datetime.datetime.now(datetime.timezone.utc).astimezone() - ak_time).total_seconds()  
        if self.Log_WriteReadTime:
            logger.info(f"{self.device_name} - {self.Log_Time_r[self.sprache]} {timediff} {self.Log_Time_wr[self.sprache]}")
        
        return self.value_name
    
    def umwandeln_Float(self, int_Byte_liste):
        ''' Sendet den Lese-Befehl an die Achse.

        Args:
            int_Byte_liste (list):            Liste der ausgelesenen Bytes mit Integern
        Return:
            value_list (list):                Umgewandelte Zahlen
        '''
        try:
            Bits_List_32 = utils.word_list_to_long(int_Byte_liste, big_endian=True, long_long=False)
            logger.debug(f'{self.device_name} - {self.Log_Text_66_str[self.sprache]} {Bits_List_32}')

            value_list = []
            i = 1
            for word in Bits_List_32:
                value = utils.decode_ieee(word)
                value_list.append(round(value, self.nKS))
                logger.debug(f'{self.device_name} - {self.Log_Text_67_str[self.sprache]} {i}: {value}')
                i += 1
        except Exception as e:
            logger.warning(self.Log_Text_Port_4[self.sprache])
            logger.exception(self.Log_Text_Port_5[self.sprache])
            value_list = []

        return value_list

    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung des Gerätes Nemo Rotation. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
        if not self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_51_str[self.sprache]}')
            logger.info(f"{self.device_name} - {self.Text_51_str[self.sprache]}")
            # Schnittstelle prüfen:
            try: 
                ## Start Werte abfragen:
                self.Start_Werte()
                ## Setze Init auf True:
                self.init = True
                ## Prüfe Verbindung:
                Meldungen = False
                for n in range(0,5,1):
                    if not self.serial.is_open:
                        self.Test_Connection(Meldungen)
                    if n == 4:
                        Meldungen = True
                if not self.serial.is_open:
                    raise ValueError(self.Log_Text_Port_2[self.sprache])
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_68_str[self.sprache]}.")
                logger.exception(f"{self.device_name} - {self.Log_Text_69_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_52_str[self.sprache]}')
                self.init = False
        else:
            logger.info(f"{self.device_name} - {self.Log_Text_70_str[self.sprache]}")
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Log_Text_70_str[self.sprache]}')
            self.init = False

    def Start_Werte(self):
        '''Lese und Schreibe bestimmte Werte bei Start des Gerätes!'''
        
        # Reihenfolge: Pmax, Imax, Umax, fmax, Name, Typ, Mode
        # Max-Werte: Register mit Größe 2
        # Name: 9 Register
        # Typ, Mode: Dezimalzahlen jeweils 1 Register
        value_error = [m.nan, m.nan, m.nan, m.nan]
        try:
            ans_1 = self.serial.read_input_registers(self.reg_lese_Info, self.lese_anz_Register_Info)
            value = self.umwandeln_Float(ans_1[0:8])
            liste = [ans_1[8], ans_1[9], ans_1[10], ans_1[11], ans_1[12], ans_1[13], ans_1[14], ans_1[15], ans_1[16]]

            ans_2 = self.serial.read_input_registers(self.reg_lese_Kombi, self.lese_anz_Register_GK)
            kombi = {0: self.Log_ST_NG_2[self.sprache], 1: self.Log_ST_NG_3[self.sprache], 2: self.Log_ST_NG_4[self.sprache], 3: self.Log_ST_NG_5[self.sprache], 4: self.Log_ST_NG_6[self.sprache], 5: self.Log_ST_NG_7[self.sprache], 6: self.Log_ST_NG_8[self.sprache]}
        except Exception as e:
            value = []
            ans_1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, self.Log_ST_NG_2[self.sprache], self.Log_ST_NG_2[self.sprache]]
            ans_2 = 0
            liste = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            logger.warning(f'{self.device_name} - {self.Log_ST_NG_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Text_112_str[self.sprache]}')

        if value == []:     value = value_error

        # Umwanldung Name:
        try:
            new_list = liste[1:]                        # Register 1 - Nicht Teil des Namens, sondern Extra Vorwahl
            ## Alles in Hex umwandeln:
            liste_letter_hex = []                   
            for n in new_list:                          
                a = hex(n)[2:]
                if not n == 0: 
                    liste_letter_hex.append(a[0:2])
                    liste_letter_hex.append(a[2:])
            ## Alles in Dez umwandeln:
            liste_letter_dez = []
            for n in liste_letter_hex:
                liste_letter_dez.append(int(n, 16))
            ## Alles in ASCII Zeichen umwandeln:
            liste_letter_ASCII = []
            for n in liste_letter_dez:
                liste_letter_ASCII.append(chr(n))
            Name = ''.join(liste_letter_ASCII)
            if Name == '': Name = self.Log_ST_NG_2[self.sprache]
        except Exception as e:
            Name = self.Log_ST_NG_2[self.sprache]
            logger.warning(f'{self.device_name} - {self.Log_ST_NG_18[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Text_112_str[self.sprache]}')

        logger.info(f'{self.device_name} - {self.Log_ST_NG_9[self.sprache]} {ans_1[17]} {self.Log_ST_NG_10[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_ST_NG_16[self.sprache]} {Name}')
        logger.info(f'{self.device_name} - {self.Log_ST_NG_11[self.sprache]} {value[0]} {self.Log_Text_123_str[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_ST_NG_12[self.sprache]} {value[1]} {self.Log_Text_127_str[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_ST_NG_13[self.sprache]} {value[2]} {self.Log_Text_125_str[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_ST_NG_14[self.sprache]} {value[3]} {self.Log_ST_NG_15[self.sprache]}')

        try:
            kombination_Generator = kombi[ans_2[0]]
        except:
            kombination_Generator = '/'

        logger.info(f'{self.device_name} - {self.Log_ST_NG_17[self.sprache]} {ans_2[0]}: {kombination_Generator}')

        self.value_name['Status_Name']  = Name
        self.value_name['Status_Typ']   = ans_1[17]
        self.value_name['Status_Kombi'] = kombination_Generator + f' ({ans_2[0]})'

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
        units = f"# datetime,s,kW,V,A,Hz,kW,V,A,{PID_x_unit},{PID_x_unit},\n"
        #scaling = f"# -,-,{self.}"
        header = "time_abs,time_rel,Ist-Leistung,Ist-Spannung,Ist-Strom,Ist-Frequenz,Soll-Leistung,Soll-Spannung,Soll-Strom,Soll-x_PID-Modus_G,Ist-x_PID-Modus_G,\n"
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
            if not 'Status' in size:
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
    
    ###################################################
    # Prüfe die Verbindung:
    ###################################################
    def Test_Connection(self, test=True):
        '''Aufbau Versuch der TCP/IP-Verbindung zur Nemo-Anlage
        Args:
            test (bool)     - Wenn False werden die Fehlermeldungen nicht mehr in die Log-Datei geschrieben
        Return: 
            True or False   - Eingeschaltet/Ausgeschaltet
        '''
        try:
            self.serial.open()
            time.sleep(0.1)         # Dadurch kann es in Ruhe öffnen
            ans = self.serial.read_input_registers(self.reg_lese_SollIst, 2)  # Sollwert 
            if ans == None:
                raise ValueError(self.Log_Text_Port_3[self.sprache])
            else:
                antwort = self.umwandeln_Float(ans)
        except Exception as e:
            if test: logger.exception(self.Log_Text_Port_1[self.sprache])
            self.serial.close()
            return False
        return True
    
    ##########################################
    # Verworfen:
    ##########################################
    ## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
    ## da dieser später vieleicht wieder ergänzt wird!!