# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo-Achse Rotations Bewegungs Gerät:
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


class NemoAchseRot(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, config_dat, com_dict, test, neustart, multilog_aktiv, add_Ablauf_function, name="Nemo-Achse-Rotation", typ = 'Antrieb'):
        """ Erstelle Nemo-Achse Rot Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      device configuration (as defined in config.yml in the devices-section).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            config_dat (string):                Datei-Name der Config-Datei
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
        self.config_dat                 = config_dat
        self.neustart                   = neustart
        self.multilog_OnOff             = multilog_aktiv
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
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
        self.reg_cw                 = self.config['register']['cw']               # Fahre hoch Coil Rergister
        self.reg_ccw                = self.config['register']['ccw']              # Fahre runter Coil Register
        self.reg_s                  = self.config['register']['stopp']            # Stoppe Coil Register
        self.start_Lese_Register    = self.config['register']['lese_st_Reg']      # Input Register Start-Register
        self.start_write_v          = self.config['register']['write_v_Reg']      # Holding Register Start-Register
        self.Status_Reg             = self.config['register']['statusReg']        # Startregister für Status
        ### Limits:
        self.oGw = self.config["limits"]['maxWinkel']
        self.uGw = self.config["limits"]['minWinkel']
        self.oGv = self.config["limits"]['maxSpeed']
        self.uGv = self.config["limits"]['minSpeed']

        ## Andere:
        self.value_name = {'IWv': 0, 'IWw':0, 'SWv': 0, 'SWxPID': self.Soll, 'IWxPID': self.Ist, 'Status': 0}

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
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
        self.Log_Text_169_str   = ['Kein True als Rückmeldung!',                                                                                                                                                            'No true feedback!']
        self.Log_Text_170_str   = ['Das Senden an das Gerät ist fehlgeschlagen. Stopp gescheitert!',                                                                                                                        'Sending to the device failed. Stop failed!']
        self.Log_Text_171_str   = ['Fehler Grund (Stopp Senden):',                                                                                                                                                          'Error reason (stop sending):']
        self.Log_Text_172_str   = ['Befehl wurde nicht akzeptiert (Geschwindigkeit)!',                                                                                                                                      'Command was not accepted (speed)!']
        self.Log_Text_173_str   = ['Das Senden der Geschwindigkeit an das Gerät ist fehlgeschlagen!',                                                                                                                       'Sending speed to device failed!']
        self.Log_Text_174_str   = ['Fehler Grund (Sende Geschwindigkeit):',                                                                                                                                                 'Error reason (send speed):']
        self.Log_Text_178_str   = ['Befehl wurde nicht akzeptiert (CW)!',                                                                                                                                                   'Command was not accepted (CW)!']
        self.Log_Text_179_str   = ['Befehl wurde nicht akzeptiert (CCW)!',                                                                                                                                                  'Command was not accepted (CCW)!']
        self.Log_Text_180_str   = ['Das Gerät hat keine Startwerte zum Auslesen!',                                                                                                                                          'The device has no start values to read out!']
        self.Log_Text_207_str   = ['Konfiguration aktualisieren (Nullpunkt setzen NemoRot):',                                                                                                                               'Update configuration (Define-Home NemoRot):']
        self.Log_Text_212_str   = ['Startwert überschreitet Maximum Limit! Setze Startwert auf Maximum Limit!',                                                                                                             'Starting value exceeds maximum limit! Set starting value to Maximum Limit!']
        self.Log_Text_213_str   = ['Startwert überschreitet Minimum Limit! Setze Startwert auf Minimum Limit!',                                                                                                             'Starting value exceeds minimum limit! Set starting value to minimum limit!']
        self.Log_Text_214_str   = ['Antriebs Startwert:',                                                                                                                                                                   'Drive start value:']
        self.Log_Text_215_str   = ['°',                                                                                                                                                                                      '°']
        self.Log_Text_219_str   = ['Knopf kann nicht ausgeführt werden da Limit erreicht!',                                                                                                                                 'Button cannot be executed because limit has been reached!']         
        self.Log_Text_220_str   = ['Maximum Limit erreicht! (CW)!',                                                                                                                                                         'Maximum limit reached! (CW)!']
        self.Log_Text_221_str   = ['Minimum Limit erreicht! (CCW)!',                                                                                                                                                        'Minimum limit reached! (CCW)!']
        self.Log_Text_249_str   = ['CW',                                                                                                                                                                                    'CW']
        self.Log_Text_250_str   = ['CCW',                                                                                                                                                                                   'CCW']
        self.Log_Text_Info_1    = ['Der Vorfaktor für die Istgeschwindigkeit beträgt:',                                                                                                                                     'The prefactor for the actual speed is:']
        self.Log_Text_Info_2    = ['Der Vorfaktor für die Sollgeschwindigkeit beträgt:',                                                                                                                                    'The prefactor for the target speed is:']
        self.Log_Text_Port_1    = ['Verbindungsfehler:',                                                                                                                                                                    'Connection error:']
        self.Log_Text_Port_2    = ['Der Test für den Verbindungsaufbau ist fehlgeschlagen!',                                                                                                                                'The connection establishment test failed!']
        self.Log_Text_Port_3    = ['Antwort der Test-Abfrage war None. Bearbeitung nicht möglich!',                                                                                                                         'The answer to the test query was None. Processing not possible!']
        self.Log_Text_Port_4    = ['Bei der Werte-Umwandlung ist ein Fehler aufgetreten!',                                                                                                                                  'An error occurred during value conversion!']
        self.Log_Text_Port_5    = ['Fehlerbeschreibung:',                                                                                                                                                                   'Error description:']
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
        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                                                                                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                                                                       'Initialization Failed!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                                                                                                                        'Sending failed!']
        self.Text_62_str        = ['Achse wurde erfolgreich angehalten!',                                                                                                                                                   'Axis was stopped successfully!']
        self.Text_67_str        = ['Nach',                                                                                                                                                                                  'After']
        self.Text_68_str        = ['Versuchen!',                                                                                                                                                                            'Attempts!']
        self.Text_69_str        = ['Geschwindigkeit erfolgreich gesendet!',                                                                                                                                                 'Speed sent successfully!']
        self.Text_70_str        = ['Befehl sende Geschwindigkeit fehlgeschlagen!',                                                                                                                                          'Command send speed failed!']
        self.Text_71_str        = ['Befehl Clock Wise fehlgeschlagen!',                                                                                                                                                     'Clock Wise command failed!']
        self.Text_72_str        = ['Befehl Clock Wise erfolgreich gesendet!',                                                                                                                                               'Clock Wise command sent successfully!']
        self.Text_73_str        = ['Befehl Counter Clock Wise fehlgeschlagen!',                                                                                                                                             'Counter Clock Wise command failed!']
        self.Text_74_str        = ['Befehl Counter Clock Wise erfolgreich gesendet!',                                                                                                                                       'Counter Clock Wise command sent successfully!']

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
        self.lese_anz_Register = 4

        #---------------------------------------
        # Variablen Positions-Controlle:
        #---------------------------------------
        self.start_Time = 0                                             # Startzeitpunkt
        self.ak_Time = 0                                                # Endzeitpunkt/aktuelle Zeit
        if self.config['start']['start_winkel'] > self.oGw:
            value = self.oGw
            self.CW_End = True                                          # Limit CW erreicht     (Maximum)
            self.CCW_End = False
            logger.warning(f"{self.device_name} - {self.Log_Text_212_str[self.sprache]} - {self.config['start']['start_winkel']}{self.Log_Text_215_str[self.sprache]} --> {value}{self.Log_Text_215_str[self.sprache]}")
        elif self.config['start']['start_winkel'] < self.uGw:
            value = self.uGw
            self.CW_End = False                     
            self.CCW_End = True                                         # Limit CCW erreicht    (Minimum)
            logger.warning(f"{self.device_name} - {self.Log_Text_213_str[self.sprache]} - {self.config['start']['start_winkel']}{self.Log_Text_215_str[self.sprache]} --> {value}{self.Log_Text_215_str[self.sprache]}")
        else:
            value = self.config['start']['start_winkel']
            self.CW_End = False
            self.CCW_End = False
            logger.info(f"{self.device_name} - {self.Log_Text_214_str[self.sprache]} {self.config['start']['start_winkel']}{self.Log_Text_215_str[self.sprache]}")
        
        self.akIWw      = value                                         # Aktueller berechneter Winkel
        self.ak_speed   = 0                                             # Aktuelle Geschwindigkeit                                           
        self.fahre      = False                                         # True: bewegung wird vollzogen
        self.rechne     = ''                                            # Add - Addiere Winkel, Sub - Subtrahiere Winkel     
        self.umFak      = 360/60                                        # Umrechnungsfaktor: Umdrehung zu Grad + min zu s  (1 Umdrehung = 360 °, 1 min = 60 s)

        #---------------------------------------
        # Informationen:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_Info_1[self.sprache]} {self.vF_ist}")
        logger.info(f"{self.device_name} - {self.Log_Text_Info_2[self.sprache]} {self.vF_soll}")

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        self.PID = PID(self.sprache, self.device_name, self.config['PID'], self.oGv, self.uGv)
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
        # Kontinuierlische Rotation:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_value['EndRot']:
            self.CW_End = False
            self.CCW_End = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Update Limit:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Update Limit']:
            self.oGw = write_value['Limits'][0]
            self.uGw = write_value['Limits'][1]
            write_Okay['Limit'] = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Define Home:
        #++++++++++++++++++++++++++++++++++++++++++
        if write_Okay['Define Home']:
            # Setze Position auf Null:
            self.akIWw = 0

            # Grenzen Updaten:
            with open(self.config_dat, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"{self.device_name} - {self.Log_Text_207_str[self.sprache]} {config}")
            
            self.oGw = config['devices'][self.device_name]["limits"]['maxWinkel']
            self.uGw = config['devices'][self.device_name]["limits"]['minWinkel']
            if self.uGw == 0:
                self.CCW_End = True
            else:
                self.CCW_End = False
            self.CW_End = False
            write_Okay['Define Home'] = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Position berechnen und Limits beachten:
        #++++++++++++++++++++++++++++++++++++++++++
        if self.fahre:
            # Bestimmung der Zeit zum Start:
            self.ak_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()        # Zyklus Ende
            timediff = (
                self.ak_Time - self.start_Time
            ).total_seconds()  
            #print(f'Zeit: {timediff}')
            self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()     # Neuer zyklus
            # Berechne Winkel:
            ans = self.serial.read_input_registers(self.start_Lese_Register, 2)             # vIst ist das erste Register!
            logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')
            self.ak_speed = self.umwandeln_Float(ans)[0] * self.vF_ist                      # Beachtung eines Vorfaktors!
            pos = self.umFak * abs(self.ak_speed) * timediff 
            if self.rechne == 'Add':
                self.akIWw = self.akIWw + pos
            elif self.rechne == 'Sub':
                self.akIWw = self.akIWw - pos
            # Endlose Rotation Ein/Aus:
            if not write_value['EndRot']:
                # Kontrolliere die Grenzen:
                if self.akIWw >= self.oGw and not self.CW_End:
                    self.CW_End = True
                    logger.warning(f'{self.device_name} - {self.Log_Text_220_str[self.sprache]}')
                    write_Okay['Stopp'] = True
                if self.akIWw <= self.uGw and not self.CCW_End:
                    self.CCW_End = True
                    logger.warning(f'{self.device_name} - {self.Log_Text_221_str[self.sprache]}')
                    write_Okay['Stopp'] = True
                if self.akIWw > self.uGw and self.akIWw < self.oGw:
                    self.CW_End = False
                    self.CCW_End = False

        #++++++++++++++++++++++++++++++++++++++++++
        # Normaler Betrieb:
        #++++++++++++++++++++++++++++++++++++++++++
        if not write_value ['PID']:  
            # Sollwert Lesen (v):
            speed_vorgabe = write_value['Speed']
            PID_write_V = False
        #++++++++++++++++++++++++++++++++++++++++++    
        # PID-Regler:
        #++++++++++++++++++++++++++++++++++++++++++
        elif write_value['PID']:
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
                print('Noch nicht Vorhanden!')
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
            write_Okay['CW'] = False
            write_Okay['CCW'] = False 
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
                    ans_v = self.write_v(speed_vorgabe)      
                    write_Okay['Send'] = False
                    ## Bewegung nur wenn Senden der Geschwindigkeit erfolgreich:
                    if ans_v:  
                        if write_Okay['CW'] and not self.CW_End:
                            ans = self.serial.write_single_coil(self.reg_cw, True)
                            if not ans:
                                logger.warning(f'{self.device_name} - {self.Log_Text_178_str[self.sprache]}')
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_71_str[self.sprache]}') 
                            else:
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_72_str[self.sprache]}')  
                                ## Positionsbestimmung:
                                self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                self.rechne = 'Add'
                                self.fahre = True
                            write_Okay['CW'] = False 
                        elif self.CW_End and write_Okay['CW']:
                            logger.warning(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_249_str[self.sprache]})')
                            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_249_str[self.sprache]})') 
                            write_Okay['CW'] = False     
                        if write_Okay['CCW'] and not self.CCW_End:
                            ans = self.serial.write_single_coil(self.reg_ccw, True)
                            if not ans:
                                logger.warning(f'{self.device_name} - {self.Log_Text_179_str[self.sprache]}')
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_73_str[self.sprache]}') 
                            else:
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_74_str[self.sprache]}') 
                                ## Positionsbestimmung:
                                self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                self.rechne = 'Sub'
                                self.fahre = True 
                            write_Okay['CCW'] = False  
                        elif self.CCW_End and write_Okay['CCW']:
                            logger.warning(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_250_str[self.sprache]})')
                            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Log_Text_219_str[self.sprache]} ({self.Log_Text_250_str[self.sprache]})') 
                            write_Okay['CCW'] = False  
                    else:
                        write_Okay['CCW'] = False 
                        write_Okay['CW'] = False      
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]}')          
                write_Okay['CCW'] = False 
                write_Okay['CW'] = False
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
            sollwert = round(sollwert/self.vF_soll, 2)          # Vorfaktor beachten
            sollwert_hex = utils.encode_ieee(sollwert)
            if sollwert_hex == 0:
                sollwert_hex = '0x00000000'
            else:
                sollwert_hex = hex(sollwert_hex)[2:]            # Wegschneiden von 0x
            sollwert_hex_HB = sollwert_hex[0:4]                 # ersten 4 Bit
            sollwert_hex_LB = sollwert_hex[4:]                  # letzten 4 Bit

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
        
        # Lese: vIst, vsoll
        ans = self.serial.read_input_registers(self.start_Lese_Register, self.lese_anz_Register)
        logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')

        value = self.umwandeln_Float(ans)
        multi = -1 if self.v_invert else 1                                       # Spindel ist invertiert

        # Reiehnfolge: vIst, vSoll
        self.value_name['IWv'] = round(value[0]*self.vF_ist, self.nKS) * multi   # Vorfaktor beachten        # Einheit: 1/min
        self.value_name['SWv'] = round(value[1]*self.vF_soll, self.nKS)          # Vorfaktor beachten        # Einheit: 1/min

        # Lese: Status
        ans = self.serial.read_input_registers(self.Status_Reg, 1)
        self.value_name['Status'] = ans[0]

        # Istwinkel:
        self.value_name['IWw'] = round(self.akIWw, self.nKS)                                                 # Einheit: °

        # PID-Modus:
        self.value_name['SWxPID'] = self.Soll
        self.value_name['IWxPID'] = self.Ist
        
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
        logger.info(f"{self.device_name} - {self.Log_Text_180_str[self.sprache]}")


###################################################
# Messdatendatei erstellen und beschrieben:
###################################################
    def messdaten_output(self, pfad="./"):
        """Erstelle für das Gerät eine csv-Datei mit den Daten.

        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = "# datetime,s,1/min,°,1/min,None,None,\n"
        header = "time_abs,time_rel,Ist-Winkelgeschwindigkeit,Ist-Winkel,Soll-Winkelgeschwindigkeit,Soll-x_PID-Modus,Ist-x_PID-Modus,\n"
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