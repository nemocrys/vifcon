# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo-Achse Lineare Bewegungs Gerät:
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
import yaml
import logging
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import datetime
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


class NemoAchseLin(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, config_dat, com_dict, test, neustart, multilog_aktiv, add_Ablauf_function, typ_Widget, name="Nemo-Achse-Linear", typ = 'Antrieb'):
        """ Erstelle Nemo-Achse Lin Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      device configuration (as defined in config.yml in the devices-section).
            config_dat (string):                Datei-Name der Config-Datei
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            multilog_aktiv (bool):              Multilog-Read/Send Aktiviert
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            typ_Widget (obj):                   Typ-Widget dieses Gerätes (Nutzung für Pop-Up-Fenster)
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
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.typ_Widget                 = typ_Widget
        self.device_name                = name
        self.typ                        = typ

        ## Aus Config:
        ### Zum Start:
        self.init       = self.config['start']['init']                            # Initialisierung
        self.messZeit   = self.config['start']["readTime"]                        # Auslesezeit
        self.v_invert   = self.config['start']['invert']                          # Invertierung bei True der Geschwindigkeit
        self.Ist        = self.config['PID']["start_ist"] 
        self.Soll       = self.config['PID']["start_soll"]
        ### Parameter:
        self.nKS        = self.config['parameter']['nKS_Aus']                     # Nachkommerstellen
        self.vF_ist     = self.config['parameter']['Vorfaktor_Ist']               # Vorfaktor Istgeschwindigkeit
        self.vF_soll    = self.config['parameter']['Vorfaktor_Soll']              # Vorfaktor Istgeschwindigkeit
        ### Register:
        self.reg_h                  = self.config['register']['hoch']             # Fahre hoch Coil Rergister
        self.reg_r                  = self.config['register']['runter']           # Fahre runter Coil Register
        self.reg_s                  = self.config['register']['stopp']            # Stoppe Coil Register
        self.start_Lese_Register    = self.config['register']['lese_st_Reg']      # Input Register Start-Register
        self.start_write_v          = self.config['register']['write_v_Reg']      # Holding Register Start-Register
        self.reg_PLim               = self.config['register']['posLimReg']        # Startregister für Limits
        self.Status_Reg             = self.config['register']['statusReg']        # Startregister für Status
        ### Limits:
        self.oGs = self.config["limits"]['maxPos']
        self.uGs = self.config["limits"]['minPos']
        self.oGv = self.config["limits"]['maxSpeed']
        self.uGv = self.config["limits"]['minSpeed']
        ### PID:
        self.unit_PIDIn = self.config['PID']['Input_Size_unit']

        ## Andere:
        self.value_name = {'IWs': 0, 'IWsd':0, 'IWv': 0, 'SWv': 0, 'SWs':0, 'oGs':0, 'uGs': 0, 'SWxPID': self.Soll, 'IWxPID': self.Ist, 'Status': 0}

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                                   'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',                'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                                 'Error reason (interface structure):']
        self.Log_Text_63_str    = ['Antwort Messwerte:',                                                                    'Answer measurements:']
        self.Log_Text_66_str    = ['Antwort Register Integer:',                                                             'Response Register Integer:']
        self.Log_Text_67_str    = ['Messwerte Umgewandelt - Messwert',                                                      'Measured Values Converted - Measured Value']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                                          'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                       'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                  'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                       'No measurement data recording active!']
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                'Error reason (send):']
        self.Log_Text_166_str   = ['Antwort Messwerte (v_ist für Rechnung):',                                               'Answer measured values (v_is for calculation):']
        self.Log_Text_167_str   = ['Befehl wurde nicht akzeptiert (Hoch)!',                                                 'Command was not accepted (Up)!']
        self.Log_Text_168_str   = ['Befehl wurde nicht akzeptiert (Runter)!',                                               'Command not accepted (Down)!']
        self.Log_Text_169_str   = ['Kein True als Rückmeldung!',                                                            'No true feedback!']
        self.Log_Text_170_str   = ['Das Senden an das Gerät ist fehlgeschlagen. Stopp gescheitert!',                        'Sending to the device failed. Stop failed!']
        self.Log_Text_171_str   = ['Fehler Grund (Stopp Senden):',                                                          'Error reason (stop sending):']
        self.Log_Text_172_str   = ['Befehl wurde nicht akzeptiert (Geschwindigkeit)!',                                      'Command was not accepted (speed)!']
        self.Log_Text_173_str   = ['Das Senden der Geschwindigkeit an das Gerät ist fehlgeschlagen!',                       'Sending speed to device failed!']
        self.Log_Text_174_str   = ['Fehler Grund (Sende Geschwindigkeit):',                                                 'Error reason (send speed):']
        self.Log_Text_175_str   = ['Messwerte - Sollposition:',                                                             'Measured values - target position:']
        self.Log_Text_176_str   = ['Position Max.',                                                                         'Position Max.']
        self.Log_Text_177_str   = ['Position Min.',                                                                         'Position Min.']
        self.Log_Text_206_str   = ['Konfiguration aktualisieren (Nullpunkt setzen NemoHub):',                               'Update configuration (Define-Home NemoHub):']
        self.Log_Text_212_str   = ['Startwert überschreitet Maximum Limit! Setze Startwert auf Maximum Limit!',             'Starting value exceeds maximum limit! Set starting value to Maximum Limit!']
        self.Log_Text_213_str   = ['Startwert überschreitet Minimum Limit! Setze Startwert auf Minimum Limit!',             'Starting value exceeds minimum limit! Set starting value to minimum limit!']
        self.Log_Text_214_str   = ['Antriebs Startwert:',                                                                   'Drive start value:']
        self.Log_Text_216_str   = ['mm',                                                                                    'mm']
        self.Log_Text_217_str   = ['Maximum Limit erreicht! (Hoch)!',                                                       'Maximum limit reached! (Up)!']
        self.Log_Text_218_str   = ['Minimum Limit erreicht! (Down)!',                                                       'Minimum limit reached! (Down)!']
        self.Log_Text_219_str   = ['Knopf kann nicht ausgeführt werden da Limit erreicht!',                                 'Button cannot be executed because limit has been reached!']         
        self.Log_Text_247_str   = ['Hoch',                                                                                  'Up']
        self.Log_Text_248_str   = ['Runter',                                                                                'Down']
        self.Log_Text_Info_1    = ['Der Vorfaktor für die Istwinkelgeschwindigkeit beträgt:',                               'The prefactor for the actual angular velocity is:']
        self.Log_Text_Info_2    = ['Der Vorfaktor für die Sollwinkelgeschwindigkeit beträg:',                               'The prefactor for the target angular velocity is:']
        self.Log_Text_Port_1    = ['Verbindungsfehler:',                                                                    'Connection error:']
        self.Log_Text_Port_2    = ['Der Test für den Verbindungsaufbau ist fehlgeschlagen!',                                'The connection establishment test failed!']
        self.Log_Text_Port_3    = ['Antwort der Test-Abfrage war None. Bearbeitung nicht möglich!',                         'The answer to the test query was None. Processing not possible!']
        self.Log_Text_Port_4    = ['Bei der Werte-Umwandlung ist ein Fehler aufgetreten!',                                  'An error occurred during value conversion!']
        self.Log_Text_Port_5    = ['Fehlerbeschreibung:',                                                                   'Error description:']
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
        Log_Text_PID_N18        = ['Die Fehlerbehandlung ist falsch konfiguriert. Möglich sind max, min und error! Fehlerbehandlung wird auf error gesetzt, wodurch der alte Inputwert für den PID-Regler genutzt wird!',   'The error handling is incorrectly configured. Possible values ​​are max, min and error! Error handling is set to error, which means that the old input value is used for the PID controller!']    
        self.Log_Text_PID_N19   = ['Auslesefehler bei Multilog-Dictionary!',                                                                                                                                                'Reading error in multilog dictionary!']
        self.Log_Text_PID_N20   = ['? - tatsächlicher Wert war',                                                                                                                                                            '°C - tatsächlicher Wert war']
        Log_Text_PID_N21        = ['Multilog Verbindung wurde in Config als Abgestellt gewählt! Eine Nutzung der Werte-Herkunft mit VM, MV oder MM ist so nicht möglich! Nutzung von Default VV!',                          'Multilog connection was selected as disabled in config! Using the value origin with VM, MV or MM is not possible! Use of default VV!']
        self.Log_Test_PID_N22   = ['?',                                                                                                                                                                                     '?']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                                                                                                          'Limit range']
        self.Log_Text_LB_4      = ['bis',                                                                                                                                                                                   'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                                                                                                           'after update']
        self.Log_Text_LB_6      = ['PID',                                                                                                                                                                                   'PID']
        self.Log_Text_LB_7      = ['Output',                                                                                                                                                                                'Outout']
        self.Log_Text_LB_8      = ['Input',                                                                                                                                                                                 'Input']
        self.Log_Text_LB_unit   = ['mm/min',                                                                                                                                                                                'mm/min']
        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                       'Initialization Failed!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                        'Sending failed!']
        self.Text_62_str        = ['Achse wurde erfolgreich angehalten!',                                                   'Axis was stopped successfully!']
        self.Text_63_str        = ['Befehl Hoch fehlgeschlagen!',                                                           'Up command failed!']
        self.Text_64_str        = ['Befehl Hoch erfolgreich gesendet!',                                                     'Up command sent successfully!']
        self.Text_65_str        = ['Befehl Runter fehlgeschlagen!',                                                         'Down command failed!']
        self.Text_66_str        = ['Befehl Runter erfolgreich gesendet!',                                                   'Down command sent successfully!']
        self.Text_67_str        = ['Nach',                                                                                  'After']
        self.Text_68_str        = ['Versuchen!',                                                                            'Attempts!']
        self.Text_69_str        = ['Geschwindigkeit erfolgreich gesendet!',                                                 'Speed sent successfully!']
        self.Text_70_str        = ['Befehl sende Geschwindigkeit fehlgeschlagen!',                                          'Command send speed failed!']

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
                logger.warning(f"{self.device_name} - {self.Log_Text_61_str[self.sprache]}")
                logger.warning(f"{self.device_name} - {self.Log_Text_Port_2[self.sprache]}")
                exit()

        #---------------------------------------
        # Befehle:
        #---------------------------------------
        self.lese_anz_Register = 12

        #---------------------------------------
        # Variablen Positions-Controlle:
        #---------------------------------------
        self.start_Time = 0                                             # Startzeitpunkt
        self.ak_Time    = 0                                             # Endzeitpunkt/aktuelle Zeit
        if self.config['start']['start_weg'] > self.oGs:
            value = self.oGs
            self.Auf_End = True                                         # Limit Hoch erreicht     (Maximum)
            self.Ab_End = False 
            logger.warning(f"{self.device_name} - {self.Log_Text_212_str[self.sprache]} - {self.config['start']['start_weg']} {self.Log_Text_216_str[self.sprache]} --> {value} {self.Log_Text_216_str[self.sprache]}")
        elif self.config['start']['start_weg'] < self.uGs:
            value = self.uGs
            self.Ab_End = True                                          # Limit Runter erreicht   (Minimum)
            self.Auf_End = False   
            logger.warning(f"{self.device_name} - {self.Log_Text_213_str[self.sprache]} - {self.config['start']['start_weg']} {self.Log_Text_216_str[self.sprache]} --> {value} {self.Log_Text_216_str[self.sprache]}")
        else:
            value = self.config['start']['start_weg']
            self.Ab_End = False
            self.Auf_End = False
            logger.info(f"{self.device_name} - {self.Log_Text_214_str[self.sprache]} {self.config['start']['start_weg']} {self.Log_Text_216_str[self.sprache]}")
        
        self.akIWs      = value                                         # Aktueller berechneter Weg
        self.ak_speed   = 0                                             # Aktuelle Geschwindigkeit
        self.fahre      = False                                         # True: bewegung wird vollzogen
        self.rechne     = ''                                            # Add - Addiere Winkel, Sub - Subtrahiere Winkel     
        self.umFak      = 1/60                                          # Umrechnungsfaktor:  min zu s (1 min = 60 s)

        #---------------------------------------
        # Informationen:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_Info_1[self.sprache]} {self.vF_ist}")
        logger.info(f"{self.device_name} - {self.Log_Text_Info_2[self.sprache]} {self.vF_soll}")

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        if self.uGv < 0:     controll_under_Null = 0
        else:                controll_under_Null = self.uGv
        self.PID = PID(self.sprache, self.device_name, self.config['PID'], self.oGv, controll_under_Null)
        self.PID_Option = self.config['PID']['Value_Origin'].upper()
        ## Info und Warnungen: --> Überarbeiten da VIFCON Istwert noch nicht vorhanden!
        if not self.multilog_OnOff and self.PID_Option in ['MV', 'MM', 'VM']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N21[sprache]}')
            self.PID_Option = 'VV'
        elif self.PID_Option in ['MM', 'VM']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N1[sprache]} {self.PID_Option} {Log_Text_PID_N2_1[self.sprache]}')
            self.PID_Option = 'VV'
        elif self.PID_Option not in ['MV', 'VV']:
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

        ## PID-Thread:
        self.PIDThread = QThread()
        self.PID.moveToThread(self.PIDThread)
        logger.info(f'{self.device_name} - {self.Log_Text_PID_str[self.sprache]}') 
        self.PIDThread.start()
        self.signal_PID.connect(self.PID.InOutPID)
        ## Timer:
        self.timer_PID = QTimer()                                              # Reaktionszeittimer (ruft die Geräte auf, liest aber nur unter bestimmten Bedingungen!)
        self.timer_PID.setInterval(self.config['PID']['sample'])
        self.timer_PID.timeout.connect(self.PID_Update)
        self.timer_PID.start()
        ### PID-Timer Thread:
        #self.PIDThreadTimer = threading.Thread(target=self.PID_Update)
        #self.PIDThreadTimer.start()
        ## Multilog-Lese-Variable für die Daten:
        self.mult_data              = {}
        self.PID_Input_Limit_Max    = self.config['PID']['Input_Limit_max'] 
        self.PID_Input_Limit_Min    = self.config['PID']['Input_Limit_min'] 
        self.PID_Input_Error_Option = self.config['PID']['Input_Error_option']
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]}: {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {self.Log_Text_LB_unit[self.sprache]}')
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]}: {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max} {self.unit_PIDIn}')   
        if self.PID_Input_Error_Option not in ['min', 'max', 'error']:
            logger.warning(f'{self.device_name} - {Log_Text_PID_N18[sprache]}')
            self.PID_Input_Error_Option = 'error'
        self.M_device               = self.config['multilog']['read_trigger'] 
        self.sensor                 = self.config['PID']['Multilog_Sensor_Ist'] 
        if self.PID_Option[0] == 'M':
            logger.info(f'{Log_Text_PID_N8[self.sprache]} {self.sensor} {Log_Text_PID_N13[self.sprache]} {self.M_device} {Log_Text_PID_N10[self.sprache]}')
        if self.PID_Option[1] == 'M':
            logger.info(f'{Log_Text_PID_N9[self.sprache]} ... {Log_Text_PID_N13[self.sprache]} ... {Log_Text_PID_N10[self.sprache]}')
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
            ## Position:
            self.oGs = write_value['Limits'][0]
            self.uGs = write_value['Limits'][1]
            ## Geschwindigkeit/PID-Output:
            self.PID.OutMax = write_value['Limits'][2]
            if write_value['Limits'][3] < 0:    self.PID.OutMin = 0
            else:                               self.PID.OutMin = write_value['Limits'][3]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {self.Log_Text_LB_unit[self.sprache]}')
            ## PID-Input:
            self.PID_Input_Limit_Max = write_value['Limits'][4]
            self.PID_Input_Limit_Min = write_value['Limits'][5]
            logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_8[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.PID_Input_Limit_Min} {self.Log_Text_LB_4[self.sprache]} {self.PID_Input_Limit_Max} {self.unit_PIDIn}')
            
            write_Okay['Update Limit'] = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Define Home:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Define Home']:
            ## Setze Position auf Null:
            self.akIWs = 0

            ## Grenzen Updaten:
            with open(self.config_dat, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"{self.device_name} - {self.Log_Text_206_str[self.sprache]} {config}")
            
            self.oGs = config['devices'][self.device_name]["limits"]['maxPos']
            self.uGs = config['devices'][self.device_name]["limits"]['minPos']
            self.Auf_End = False                       
            if self.uGs == 0:                           
                self.Ab_End = True                    
            else:  
                self.Ab_End = False
            write_Okay['Define Home'] = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Position berechnen und Limits beachten:
        #++++++++++++++++++++++++++++++++++++++++++
        if self.fahre:
            ## Bestimmung der Zeit zum Start:
            self.ak_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()    # Zyklus Ende
            timediff = (
                self.ak_Time - self.start_Time
            ).total_seconds()  
            self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone() # Neuer zyklus
            ## Berechne Weg:
            ans = self.serial.read_input_registers(self.start_Lese_Register, 2)         # vIst ist das erste Register!
            logger.debug(f'{self.device_name} - {self.Log_Text_166_str[self.sprache]} {ans}')
            self.ak_speed = self.umwandeln_Float(ans)[0] * self.vF_ist                  # Istwert kann negativ sein. Beachtung eines Vorfaktors!
            pos = self.umFak * abs(self.ak_speed) * timediff 
            if self.rechne == 'Add':
                self.akIWs = self.akIWs + pos
            elif self.rechne == 'Sub':
                self.akIWs = self.akIWs - pos
            ## Kontrolliere die Grenzen:
            if self.akIWs >= self.oGs and not self.Auf_End:
                self.Auf_End = True
                logger.warning(f'{self.device_name} - {self.Log_Text_217_str[self.sprache]}')
                self.typ_Widget.Message(self.Log_Text_217_str[self.sprache], 3, 450)
                write_Okay['Stopp'] = True
            if self.akIWs <= self.uGs and not self.Ab_End:
                self.Ab_End = True
                logger.warning(f'{self.device_name} - {self.Log_Text_218_str[self.sprache]}')
                self.typ_Widget.Message(self.Log_Text_218_str[self.sprache], 3, 450)
                write_Okay['Stopp'] = True
            if self.akIWs > self.uGs and self.akIWs < self.oGs:
                self.Auf_End = False
                self.Ab_End = False
        
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
                    if self.sensor.lower() == 'no sensor':
                        self.Ist = self.mult_data[self.M_device]
                    else:
                        self.Ist = self.mult_data[self.M_device][self.sensor]
                except Exception as e:
                    logger.warning(f"{self.device_name} - {self.Log_Text_PID_N19[self.sprache]}")
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
            ### MUltilog:
            elif self.PID_Option[1] == 'M':
                print(['Noch nicht Vorhanden!', 'Not available yet!'][self.sprache])
            #---------------------------------------------    
            ## Schreibe Werte:
            #---------------------------------------------
            speed_vorgabe = self.PID_Out
            PID_write_V = True

        #++++++++++++++++++++++++++++++++++++++++++
        # Sende Stopp:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Stopp']:
            self.stopp()
            # Rücksetzen aller Bewegungen:
            write_Okay['Stopp'] = False
            write_Okay['Hoch'] = False
            write_Okay['Runter'] = False
            write_Okay['Send'] = False
            self.fahre = False    
            self.start_Time = 0                                    
        #++++++++++++++++++++++++++++++++++++++++++                                      
        # Schreiben, wenn nicht Stopp:
        #++++++++++++++++++++++++++++++++++++++++++         
        else:
            try:
                # PID-Modus:
                if not write_Okay['Send'] and PID_write_V:
                    ans_v = self.write_v(speed_vorgabe)
                    PID_write_V = False
                # Normaler Modus und PID-Modus bei Bewegungsauslösung:
                elif write_Okay['Send']:
                    ans_v = self.write_v(write_value['Speed'])      
                    write_Okay['Send'] = False
                    # Bewegung nur wenn Senden der Geschwindigkeit erfolgreich:
                    if ans_v:                              
                        if write_Okay['Hoch'] and not self.Auf_End:
                            ans = self.serial.write_single_coil(self.reg_h, True)
                            if not ans:
                                logger.warning(f'{self.device_name} - {self.Log_Text_167_str[self.sprache]}')
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_63_str[self.sprache]}') 
                            else:
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_64_str[self.sprache]}')  
                                # Positionsbestimmung:
                                self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                self.rechne = 'Add'
                                self.fahre = True
                            write_Okay['Hoch'] = False 
                        elif self.Auf_End and write_Okay['Hoch']:
                            logger.warning(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_247_str[self.sprache]})')
                            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_247_str[self.sprache]})') 
                            write_Okay['Hoch'] = False     
                        if write_Okay['Runter'] and not self.Ab_End:
                            ans = self.serial.write_single_coil(self.reg_r, True)
                            if not ans:
                                logger.warning(f'{self.device_name} - {self.Log_Text_168_str[self.sprache]}')
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_65_str[self.sprache]}') 
                            else:
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_66_str[self.sprache]}') 
                                # Positionsbestimmung:
                                self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                self.rechne = 'Sub'
                                self.fahre = True 
                            write_Okay['Runter'] = False  
                        elif self.Ab_End and write_Okay['Runter']:
                            logger.warning(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_248_str[self.sprache]})')
                            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_248_str[self.sprache]})') 
                            write_Okay['Runter'] = False  
                    else:
                        write_Okay['Runter'] = False 
                        write_Okay['Hoch'] = False      
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]}')          
                write_Okay['Runter'] = False 
                write_Okay['Hoch'] = False 
                write_value['Speed'] = False
                
    def stopp(self):
        ''' Halte Achse an!'''
        
        try:
            n = 0
            while n != 10:
                ans = self.serial.write_single_coil(self.reg_s, True)

                if ans:
                    extra = ''
                    if not n == 0:
                        extra = f'{self.Text_67_str[self.sprache]} {n}-{self.Text_68_str[self.sprache]}'
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_62_str[self.sprache]} {extra}') 
                    break
                else:
                    logger.warning(f"{self.device_name} - {self.Log_Text_169_str[self.sprache]}")
                n += 1
        except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_170_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_171_str[self.sprache]}")
    
    def write_v(self, sollwert):
        ''' Schreibe den Geschwindigkeitswert in das Register
        
        Args:
            sollwert (float):   Sollwert der Geschwindigkeit
        Return:
            ans (bool):         Senden funktioniert
            False:              Exception ausgelöst!    
        '''
        try:
            sollwert = round(sollwert/self.vF_soll, 2)      # Beachtung des Vorfaktors
            sollwert_hex = utils.encode_ieee(sollwert)
            if sollwert_hex == 0:
                sollwert_hex = '0x00000000'
            else:
                sollwert_hex = hex(sollwert_hex)[2:]        # Wegschneiden von 0x
            sollwert_hex_HB = sollwert_hex[0:4]             # ersten 4 Bit
            sollwert_hex_LB = sollwert_hex[4:]              # letzten 4 Bit

            ans = self.serial.write_multiple_registers(self.start_write_v, [int(sollwert_hex_HB,16), int(sollwert_hex_LB,16)])
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
        ''' Sende Befehle an die Achse um Werte auszulesen.

        Return: 
            Aktuelle Werte (dict)   - self.value_name
        '''
        
        # Lese: vIst, vSoll, posIst, posSoll, posMax, posMin
        ans = self.serial.read_input_registers(self.start_Lese_Register, self.lese_anz_Register)
        logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')

        value = self.umwandeln_Float(ans)
        multi = -1 if self.v_invert else 1                                       # Spindel ist invertiert

        # Reiehnfolge: vIst, vSoll, posIst, posSoll, posMax, posMin
        self.value_name['IWv']  = round(value[0] * self.vF_ist, self.nKS) * multi   # Vorfaktor     # Einheit: mm/min 
        self.value_name['SWv']  = round(value[1] * self.vF_soll , self.nKS)         # Vorfaktor     # Einheit: mm/min
        self.value_name['IWs']  = round(self.akIWs, self.nKS)                       # value[2]      # Einheit: mm
        self.value_name['IWsd'] = round(value[2], self.nKS)                                         # Einheit: mm
        self.value_name['SWs']  = round(value[3], self.nKS)                                         # Einheit: mm
        self.value_name['oGs']  = round(self.oGs, self.nKS)                         # value[4]      # Einheit: mm
        self.value_name['uGs']  = round(self.uGs, self.nKS)                         # value[5]      # Einheit: mm
        logger.debug(f'{self.device_name} - {self.Log_Text_175_str[self.sprache]} {value[3]}, {self.Log_Text_176_str[self.sprache]}: {value[4]}, {self.Log_Text_177_str[self.sprache]}: {value[5]}')

        # Lese: Status
        ans = self.serial.read_input_registers(self.Status_Reg, 1)
        self.value_name['Status'] = ans[0]

        # PID-Modus:
        self.value_name['SWxPID'] = self.Soll
        self.value_name['IWxPID'] = self.Ist
        
        return self.value_name

    def umwandeln_Float(self, int_Byte_liste):
        ''' Wandelt die Register-Werte in Zahlen um.

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
        ''' Initialisierung des Gerätes Nemo Hub. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
        if not self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_51_str[self.sprache]}')
            logger.info(f"{self.device_name} - {self.Text_51_str[self.sprache]}")
            # Schnittstelle prüfen:
            try: 
                ## Prüfe Verbindung:
                Meldungen = False
                for n in range(0,5,1):
                    if not self.serial.is_open:
                        self.Test_Connection(Meldungen)
                    if n == 4:
                        Meldungen = True
                if not self.serial.is_open:
                    raise ValueError(self.Log_Text_Port_2[self.sprache])
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
        ans = self.serial.read_input_registers(self.reg_PLim, 4)
        
        value = self.umwandeln_Float(ans)
        logger.info(f"{self.device_name} - {self.Log_Text_176_str[self.sprache]} = {value[0]}!")
        logger.info(f"{self.device_name} - {self.Log_Text_177_str[self.sprache]} = {value[1]}!")

    ###################################################
    # Messdatendatei erstellen und beschrieben:
    ###################################################
    def messdaten_output(self, pfad="./"):
        """Erstelle für das Gerät eine csv-Datei mit den Daten.

        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        PID_x_unit = self.config['PID']['Input_Size_unit']
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = f"# datetime,s,mm,mm,mm/min,mm/min,mm,mm,mm,{PID_x_unit},{PID_x_unit},\n"
        header = "time_abs,time_rel,Ist-Position-sim,Ist-Position-real,Ist-Geschwindigkeit,Soll-Geschwindigkeit,Soll-Position,max.Pos.,min.Pos.,Soll-x_PID-Modus_A,Ist-x_PID-Modus_A,\n"
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
        
        #daten = daten[0:2] # Nur Position und Geschwindigkeit!
        line = f"{absolut_Time.isoformat(timespec='milliseconds').replace('T', ' ')},{relativ_Time},"
        for size in daten:
            if not size == 'Status':
                line = line + f'{daten[size]},'
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f'{line}\n')
    
    ##########################################
    # PID-Regler:
    ##########################################
    def PID_Update(self):
        '''PID-Regler-Thread-Aufruf'''
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
            ans = self.serial.read_input_registers(self.start_Lese_Register, 2)  # vIst
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
'''


'''        
