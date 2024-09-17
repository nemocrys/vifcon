# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
TruHeat Generator:
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


class SerialMock: # Notiz: Näher ansehen!
    """ This class is used to mock a serial interface for debugging purposes. """

    def write(self, _):
        pass

    def readline(self):
        return "".encode()


class TruHeat(QObject):
    signal_PID  = pyqtSignal(float, float, bool, float)

    def __init__(self, sprache, config, com_dict, test, neustart, multilog_aktiv, add_Ablauf_function, name="TruHeat", typ = 'Generator'):
        """ Erstelle TruHeat Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      Geräte Konfigurationen (definiert in config.yml in der devices-Sektion).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            multilog_aktiv (bool):              Multilog-Read/Send Aktiviert
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
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = name
        self.typ                        = typ
        
        ## Auflösung und Umrechnung:
        ### Auflösung (Resolution):
        self.resP = 10
        self.resU = 1
        self.resI = 100
        self.resf = 1

        ### Umrechnungsfaktor
        self.umP = 1000                                         # Leistung in kW
        self.umU = 1                                            # Spannung in V
        self.umI = 1000                                         # Strom in A
        self.umf = 1                                            # Frequenz in kHz

        #---------------------------------------------------------
        # Konfigurationskontrolle und Konfigurationsvariablen:
        #---------------------------------------------------------
        ## Einstellung für Log:
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                                                                                                      'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                                                                                         'Possible values:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                                                                                              'Default is used:']
        
        ## Zum Start:
        self.init       = self.config['start']['init']           # Initialisierung
        self.messZeit   = self.config['start']["readTime"]       # Auslesezeit
        self.adress     = self.config['start']['ad']             # Generatoradresse
        self.wdT        = self.config['start']['watchdog_Time']  # Watchdog-Zeit in ms
        self.Delay_sT   = self.config['start']['send_Delay']     # Sende Delay in ms
        self.startMod   = self.config['start']['start_modus'] 
        self.Ist        = self.config['PID']["start_ist"] 
        self.Soll       = self.config['PID']["start_soll"]        
        ## Limits:
        self.oGP = self.config["limits"]['maxP']
        self.uGP = self.config["limits"]['minP']
        self.oGI = self.config["limits"]['maxI']
        self.uGI = self.config["limits"]['minI']
        self.oGU = self.config["limits"]['maxU']
        self.uGU = self.config["limits"]['minU']
        ## Schnittstelle Extra:
        self.Loop = self.config['serial-loop-read']
        ## PID:
        self.unit_PIDIn = self.config['PID']['Input_Size_unit']

        ## Config-Fehler und Defaults:
        if not type(self.Loop) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} serial-loop-read - {self.Log_Pfad_conf_2[self.sprache]} Integer - {self.Log_Pfad_conf_3[self.sprache]} 10')
            self.Loop = 10

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                                   'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',                'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                                 'Error reason (interface structure):']
        self.Log_Text_64_str    = ['Das Gerät konnte nicht ausgelesen werden.',                                             'The device could not be read.']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                                          'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                       'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                  'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                       'No measurement data recording active!']
        self.Log_Text_73_str    = ['Startfehler!',                                                                          'Start error!']
        self.Log_Text_74_str    = ['Fehler Grund (Startwert Fehler):',                                                      'Error reason (start value error):']
        self.Log_Text_75_str    = ['Liste der gesendeten Befehle (Schreibe):',                                              'List of commands sent (Write):']
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                'Error reason (send):']
        self.Log_Text_78_str    = ['Ausgelesene Werte (Schreiben):',                                                        'Read values (Write):']
        self.Log_Text_79_str    = ['Schreibbefehl:',                                                                        'Write command:']
        self.Log_Text_80_str    = ['Antwort ist ein ACK!',                                                                  'Answer is an ACK!']
        self.Log_Text_81_str    = ['Checksumme stimmt. Bestätige Befehl! Sende ACK!',                                       'Checksum is correct. Confirm command! Send ACK!']
        self.Log_Text_82_str    = ['Schreibbefehl erfolgreich gesendet!',                                                   'Write command sent successfully!']
        self.Log_Text_83_str    = ['Leistung ist eingeschaltet, diese Änderung ist während dieses Zustands nicht erlaubt!', 'Power is switched on, this change is not permitted during this state!']
        self.Log_Text_84_str    = ['Wert überschreitet die erlaubten Grenzen!',                                             'Value exceeds the permitted limits!']
        self.Log_Text_85_str    = ['Nicht erlaubter Parameter!',                                                            'Not allowed parameter!']
        self.Log_Text_86_str    = ['Mindestens eine Störmeldung liegt noch an!',                                            'At least one error message is still pending!']
        self.Log_Text_87_str    = ['Anzahl der Datenbytes sind falsch!',                                                    'Number of data bytes are incorrect!']
        self.Log_Text_88_str    = ['Befehl wird nicht akzeptiert! Grund: Ungültiges Interface, etc.',                       'Command is not accepted! Reason: Invalid interface, etc.']
        self.Log_Text_89_str    = ['Unbekannter Befehl! Wird ignoriert!',                                                   'Unknown command! Will be ignored!']
        self.Log_Text_90_str    = ['Antwort ist ein NAK!',                                                                  'Answer is a NAK!']
        self.Log_Text_91_str    = ['Antwort ist kein ACK oder NAK!',                                                        'Answer is not an ACK or NAK!']
        self.Log_Text_92_str    = ['Wiederholung',                                                                          'Repetition']
        self.Log_Text_93_str    = ['Senden des Befehls zum Schreiben ist fehlgeschlagen!',                                  'Sending write command failed!']
        self.Log_Text_94_str    = ['Liste der gesendeten Befehle (Lese):',                                                  'List of commands sent (Read):']
        self.Log_Text_95_str    = ['Sende das Hexadezimal Zeichen',                                                         'Send the hexadecimal character']
        self.Log_Text_96_str    = ['Ausgelesene Werte (Lesen):',                                                            'Values read (read):']
        self.Log_Text_97_str    = ['ACK beim Lese Befehl:',                                                                 'ACK on read command:']
        self.Log_Text_98_str    = ['Checksumme stimmt!',                                                                    'Checksum is correct!']
        self.Log_Text_99_str    = ['Sende ACK an Generator!',                                                               'Send ACK to generator!']
        self.Log_Text_100_str   = ['NAK beim Lese Befehl:',                                                                 'NAK on read command:']
        self.Log_Text_101_str   = ['Kein ACK oder NAK beim Lese Befehl:',                                                   'No ACK or NAK when reading command:']
        self.Log_Text_102_str   = ['Lese Befehl:',                                                                          'Read command:']
        self.Log_Text_103_str   = ['Wiederhole senden nach NAK oder keiner Antwort!',                                       'Repeat send after NAK or no response!']
        self.Log_Text_104_str   = ['Wert:',                                                                                 'Value:']
        self.Log_Text_105_str   = ['Lese Istwert Leistung',                                                                 'Read actual value power']
        self.Log_Text_106_str   = ['Lese Istwert Spannung',                                                                 'Read actual voltage value']
        self.Log_Text_107_str   = ['Lese Istwert Strom',                                                                    'Read actual current value']
        self.Log_Text_108_str   = ['Lese Istwert Frequenz',                                                                 'Read actual frequency value']
        self.Log_Text_109_str   = ['Lese Sollwert Leistung',                                                                'Read setpoint power']
        self.Log_Text_110_str   = ['Lese Sollwert Spannung',                                                                'Read setpoint voltage']
        self.Log_Text_111_str   = ['Lese Sollwert Strom',                                                                   'Read setpoint current']
        self.Log_Text_112_str   = ['Fehler Grund (Auslesen):',                                                              'Error reason (reading):']
        self.Log_Text_113_str   = ['Watchdog wird gesetzt auf:',                                                            'Watchdog is set to:']
        self.Log_Text_114_str   = ['ms',                                                                                    'ms']
        self.Log_Text_115_str   = ['Ausgelesener Watchdog:',                                                                'Read watchdog:']
        self.Log_Text_116_str   = ['Gesendeter Watchdog stimmt nicht mit ausgelesenen überein!',                            'Sent watchdog does not match the one read out!']
        self.Log_Text_117_str   = ['Softwareversion:',                                                                      'Software version:']
        self.Log_Text_118_str   = ['Seriennummer der Stromversorgung:',                                                     'Power supply serial number:']
        self.Log_Text_119_str   = ['Netzteil-Typ:',                                                                         'Power supply type:']
        self.Log_Text_120_str   = ['minimaler Sollwert für den Ausgangsstrom:',                                             'Minimum setpoint for the output current:']
        self.Log_Text_121_str   = ['minimaler Sollwert für die Kondensatorspannung:',                                       'Minimum setpoint for the capacitor voltage:']
        self.Log_Text_122_str   = ['max. Sollleistung:',                                                                    'max. target power:']
        self.Log_Text_123_str   = ['kW',                                                                                    'kW']
        self.Log_Text_124_str   = ['max. Sollspannung (UC):',                                                               'max. target voltage (UC):']
        self.Log_Text_125_str   = ['V',                                                                                     'V']
        self.Log_Text_126_str   = ['max. Sollstrom (HF):',                                                                  'max. target current (HF):']
        self.Log_Text_127_str   = ['A',                                                                                     'A']
        self.Log_Text_128_str   = ['Aktives Interface:',                                                                    'Active interface:']
        self.Log_Text_129_str   = ['Aktives Interface: Unbekannt! Ausgelesen:',                                             'Active Interface: Unknown! Read:']
        self.Log_Text_130_str   = ['Gibt es:',                                                                              'There is:']
        self.Log_Text_131_str   = ['Das aktuelle Interface ist nicht RS-232!',                                              'The current interface is not RS-232!']
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
        self.Log_Text_PID_N20   = [f'{self.unit_PIDIn} - tatsächlicher Wert war',                                                                                                                                           f'{self.unit_PIDIn} - tatsächlicher Wert war']
        Log_Text_PID_N21        = ['Multilog Verbindung wurde in Config als Abgestellt gewählt! Eine Nutzung der Werte-Herkunft mit VM, MV oder MM ist so nicht möglich! Nutzung von Default VV!',                          'Multilog connection was selected as disabled in config! Using the value origin with VM, MV or MM is not possible! Use of default VV!']
        self.Log_Test_PID_N22   = [f'{self.unit_PIDIn}',                                                                                                                                                                    f'{self.unit_PIDIn}']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                                                                                                          'Limit range']
        self.Log_Text_LB_4      = ['bis',                                                                                                                                                                                   'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                                                                                                           'after update']
        self.Log_Text_LB_6      = ['PID',                                                                                                                                                                                   'PID']
        self.Log_Text_LB_7      = ['Output',                                                                                                                                                                                'Outout']
        self.Log_Text_LB_8      = ['Input',                                                                                                                                                                                 'Input']
        self.Log_Text_PID1_str  = ['Die PID-Start-Modus aus der Config-Datei existiert nicht! Setze auf Default P! Fehlerhafter Eintrag:',                                                                                  'The PID start mode from the config file does not exist! Set to default P! Incorrect entry:']
        self.Log_Nan_1_Float    = ['Wert ist nicht vom Type Float! Setze Wert auf Nan!',                                                                                                                                    'Value is not of type Float! Set value to Nan!']
        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                                                                                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                                                                       'Initialization Failed!']
        self.Text_53_str        = ['Wert wurde angenommen (ACK)!',                                                                                                                                                          'Value was accepted (ACK)!']
        self.Text_54_str        = ['Wert wurde nicht angenommen (NAK)!',                                                                                                                                                    'Value was not accepted (NAK)!']
        self.Text_55_str        = ['Senden fehlgeschlagen (Keine Antwort)!',                                                                                                                                                'Sending failed (no response)!']

        #---------------------------------------
        # Werte Dictionary:
        #---------------------------------------
        self.value_name = {'IWP': 0, 'IWU': 0, 'IWI': 0, 'IWf': 0, 'SWP': 0, 'SWU': 0, 'SWI': 0, 'SWxPID': self.Soll, 'IWxPID': self.Ist}

        #---------------------------------------
        # Schnittstelle:
        #---------------------------------------
        logger.info(f" {self.device_name} - {self.Log_Text_60_str[self.sprache]}")
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
        self.rbefSP = '8E'       # Sollleistung
        self.rbefIP = 'A5'       # Istleistung
        self.rbefSU = '8F'       # Sollspannung 
        self.rbefIU = 'A6'       # Istspannung
        self.rbefSI = '8D'       # Sollstrom
        self.rbefII = 'A4'       # Iststrom
        self.rbefIf = 'C4'       # Istfrequenz
        
        ## Schreiben:
        self.wbefSP = '32'       # Sollleistung
        self.wbefSU = '33'       # Sollspannung
        self.wbefSI = '31'       # Sollstrom
        self.wEin   = '02'       # Einschalten
        self.wAus   = '01'       # Ausschalten
        self.wWDT   = '2D'       # Watchdog Zeit

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        if not self.startMod in ['P', 'I', 'U']:
            logger.warning(f'{self.device_name} - {self.Log_Text_PID1_str} {self.startMod}')
            self.startMod = 'P'
        if self.startMod == 'P':      oG, uG, unit = self.oGP, self.uGP, self.Log_Text_123_str[self.sprache]
        elif self.startMod == 'I':    oG, uG, unit = self.oGI, self.uGI, self.Log_Text_127_str[self.sprache]
        elif self.startMod == 'U':    oG, uG, unit = self.oGU, self.uGU, self.Log_Text_125_str[self.sprache]

        self.PID = PID(self.sprache, self.device_name, self.config['PID'], oG, uG)
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
        logger.info(f'{self.PID.Log_PID_0[self.sprache]} ({self.PID.device}) - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_6[self.sprache]}-{self.Log_Text_LB_7[self.sprache]}: {self.PID.OutMin} {self.Log_Text_LB_4[self.sprache]} {self.PID.OutMax} {unit}')
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
        ''' Schreiben der übergebenden Werte, wenn der richtige Knopf betätigt wurde!

        Args:
            write_Okay (dict):  beinhaltet Boolsche Werte für das was beschrieben werden soll!
            write_value (dict): beinhaltet die Werte die geschrieben werden sollen
        '''

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
        # Normaler Betrieb:
        #++++++++++++++++++++++++++++++++++++++++++
        if not write_Okay['PID']:  
            ## Sollwert Lesen (v):
            sollwert = write_value['Sollwert']      # in eine Zahl umgewandelter Wert (Float)
            PID_write_wert = False
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
            wert_vorgabe    = self.PID_Out
            PID_write_wert  = True

        #++++++++++++++++++++++++++++++++++++++++++
        # Schreiben:
        #++++++++++++++++++++++++++++++++++++++++++
        for auswahl in write_Okay:
            ## Soll-Leistung:
            if write_Okay[auswahl] and auswahl == 'Soll-Leistung':
                self.write_read_answer(self.wbefSP, sollwert, self.resP, self.umP,  '010')
                write_Okay[auswahl] = False
            ## Soll-Spannung:
            elif write_Okay[auswahl] and auswahl == 'Soll-Spannung':
                self.write_read_answer(self.wbefSU, sollwert, self.resU, self.umU, '010')
                write_Okay[auswahl] = False
            ## Soll-Strom:
            elif write_Okay[auswahl] and auswahl == 'Soll-Strom':
                self.write_read_answer(self.wbefSI, sollwert, self.resI, self.umI, '010')
                write_Okay[auswahl] = False
            ## PID-Modus:
            elif PID_write_wert:
                if write_value['PID Output-Size']   == 'P': befehl, resolution, umFak = self.wbefSP, self.resP, self.umP
                elif write_value['PID Output-Size'] == 'I': befehl, resolution, umFak = self.wbefSI, self.resI, self.umI
                elif write_value['PID Output-Size'] == 'U': befehl, resolution, umFak = self.wbefSU, self.resU, self.umU 
                self.write_read_answer(befehl, wert_vorgabe, resolution, umFak,  '010')
                PID_write_wert = False
            ## Generator Ein:
            elif write_Okay[auswahl] and auswahl == 'Ein':
                self.write_read_answer(self.wEin, 0, 0, 0, '000')
                write_Okay[auswahl] = False
            ## Generator Aus:
            elif write_Okay[auswahl] and auswahl == 'Aus':
                self.write_read_answer(self.wAus, 0, 0, 0, '000')
                write_Okay[auswahl] = False
            ## Startwerte auslesen:
            elif write_Okay[auswahl] and auswahl == 'Start' and not self.neustart:
                try:
                    self.Start_Werte()
                    write_Okay[auswahl] = False
                except Exception as e:
                    logger.warning(f"{self.device_name} - {self.Log_Text_73_str[self.sprache]}")
                    logger.exception(f"{self.device_name} - {self.Log_Text_74_str[self.sprache]}")

    def hex_schnitt(self, hex_value):
        ''' Für das Senden muss der Hex-String in der Form ohne '0x' vorliegen.
            Weiterhin wird eine Null angefügt, sollte der Wert zu kurz sein!

        Args:
            hex_value (str):    Hexadezimalwert in der Form '0x'
        Return:
            value (str):        Hexadezimalwert, bestehend aus einem Byte
        '''
        value = hex_value[2:]       # Wegschneiden des 0x am Anfang
        if len(value) == 1:
            value = '0' + value     # Anfügen einer 0, wenn nur ein Halber-Byte bekannt z.B. 0x8 --> 8 --> 08
        return value
    
    def write_checksum(self, liste):
        ''' XOR-Verknüpfung von Hex-Strings ohne Prefix

        Args:
            liste (list):   Liste mit den Werten in String
        Return:
            cs (str):       Checksumme
        '''
        cs_alt = 0                      # Dezimal, Startwert
        for n in liste:
            cs = int(n,16) ^ cs_alt     # Berechnet den Dezimalwert mit XOR
            cs_alt = cs
        cs = hex(cs)                    # Umwandeln in Hex (Dezimal zu Hexadezimal)
        return cs

    def write_read_answer(self, befehl, value, res, um, Anz_DatBy, op_Anz_DatBy = '00000000'):
        ''' Lese die Antowrt des Schreibbefehls aus!
        
        Args:
            befehl (str):       String mit Hex-Zahl
            value (float):      übergebender Wert
            res (int):          Auflösung (Resolution) des Wertes
            um (int):           Umrechnungswert
            Anz_DatBy (str):    Anzahl der Datenbytes in Binär!
            op_Anz_DatBy (Str): Optionales Längenbyte
        '''
        # Kurze Verzögerung:
        time.sleep(self.Delay_sT/1000)                          # ms in s
        # Schreibe:
        ## Vorbereitung:
        write_list = []                                         # Aussehen: [Header, Befehl, (optionales Längenbyte), Datenbytes, Checksumme]
        ### Header und Anzahl Datenbytes:
        header = hex(int(self.adress + Anz_DatBy, 2))           # Header bestimmen (Binär zu Hexadezimal-String)
        header = self.hex_schnitt(header)                       # wegschneiden des Prefix
        write_list.append(header)
        ### Befehl:
        write_list.append(befehl)
        ### Optionales Länegnbyte:
        if Anz_DatBy == '111':
            op_LB = hex(int(op_Anz_DatBy, 2)) 
            op_LB = self.hex_schnitt(op_LB)
            write_list.append(op_LB)
        ### Datenbytes:
            # Eingabefeld:  kW,  A, V, kHz
            # Senden:       W,  mA, V, kHz
            # Beispiel:     149 bedeutet 14,9 A. --> erst umrechnen, dann Auflösung
        if not Anz_DatBy == '000':
            send_value_dec = value * um/res
            send_value_hex = hex(int(send_value_dec))           # hex erwartet einen Integer-Typ
            if len(send_value_hex) > 4:                         # Wenn das Auflösen und Umrechnen mehr als 1 Byte bringen, dann ist das zweite Datenbyte ungleich Null
                dat_1 = send_value_hex[-2:]
                dat_2 = self.hex_schnitt(send_value_hex[:-2])
            else:
                dat_1 = self.hex_schnitt(send_value_hex)
                dat_2 = '00'
            write_list.append(dat_1)
            write_list.append(dat_2)
        ### Checksumme:
        cs = self.hex_schnitt(self.write_checksum(write_list))
        write_list.append(cs)
        logging.debug(f"{self.device_name} - {self.Log_Text_75_str[self.sprache]} {write_list}")

        # Senden des Befehls und Auslesen der Antwort:
        while_n = 0
        while while_n != self.Loop:
            ans_list = []
            ## Senden
            error = False
            try:
                for n in write_list:
                    self.serial.write(bytearray.fromhex(n))
                    #logging.debug(f"{self.device_name} - Sende das Hexadezimal Zeichen: {n}")
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
                error = True

            if not error:
                ## Lese Antwort (Kontrolle des Eingangs des Befehls):
                for byte_bef in range(1,6):                         # ACK, Header, Befehl, Quittierungsnachricht, CS
                    ans = self.serial.read()                        # Notiz: eventuell wird noch ein Try-Except gebraucht!
                    ans_list.append(ans)
                    #time.sleep(0.1)
                logging.debug(f"{self.device_name} - {self.Log_Text_78_str[self.sprache]} {ans_list}")
                if ans_list[0] == b'\x06':
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_53_str[self.sprache]}')             
                    logging.debug(f"{self.device_name} - {self.Log_Text_79_str[self.sprache]} {befehl} - {self.Log_Text_80_str[self.sprache]}")
                    ans_list.pop(0)
                    ### Prüfe-Checksumme:
                    key_alt = b'\x00'                               # Vieleicht noch in Funktion da 2mal gebraucht
                    for n in ans_list:
                        key = self.byte_xor(key_alt, n)
                        key_alt = key
                    if key == b'\x00':
                        ans_list.pop(-1)
                        logging.debug(f"{self.device_name} - {self.Log_Text_81_str[self.sprache]}")
                        self.serial.write(bytearray.fromhex('06'))  # bestätigte das alles in Ordnung ist!
                        # Quittierungsmedlung ansehen:
                        quittierung = int(ans_list[2].hex(),16)
                        if quittierung == 0:
                            logging.debug(f"{self.device_name} - {self.Log_Text_82_str[self.sprache]}")
                        elif quittierung == 2:
                            logging.warning(f"{self.device_name} - {self.Log_Text_83_str[self.sprache]}")
                        elif quittierung == 4:
                            logging.warning(f"{self.device_name} - {self.Log_Text_84_str[self.sprache]}")
                        elif quittierung == 5:
                            logging.warning(f"{self.device_name} - {self.Log_Text_85_str[self.sprache]}")
                        elif quittierung == 7:
                            logging.warning(f"{self.device_name} - {self.Log_Text_86_str[self.sprache]}")
                        elif quittierung == 9:
                            logging.warning(f"{self.device_name} - {self.Log_Text_87_str[self.sprache]}")
                        elif quittierung == 22:
                            logging.warning(f"{self.device_name} - {self.Log_Text_88_str[self.sprache]}")
                        elif quittierung == 99:
                            logging.warning(f"{self.device_name} - {self.Log_Text_89_str[self.sprache]}")
                        break   
                elif ans_list[0] == b'\x15':
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_54_str[self.sprache]}')       
                    logging.warning(f"{self.device_name} - {self.Log_Text_79_str[self.sprache]} {befehl} - {self.Log_Text_90_str[self.sprache]}")
                else:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_55_str[self.sprache]}')  
                    logging.warning(f"{self.device_name} - {self.Log_Text_79_str[self.sprache]} {befehl} - {self.Log_Text_91_str[self.sprache]}")
                
            # Kurze Verzögerung:
            time.sleep(self.Delay_sT/1000) # ms in s
            # Wiederhole Senden!
            while_n += 1 
            logging.debug(f"{self.device_name} - {self.Log_Text_79_str[self.sprache]} {befehl} - {self.Log_Text_92_str[self.sprache]} {while_n}")

        if while_n == self.Loop:
            logging.warning(f"{self.device_name} - {self.Log_Text_93_str[self.sprache]}")

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def byte_xor(self, ba1, ba2): 
        ''' Funktion wurde der Quelle: https://nitratine.net/blog/post/xor-python-byte-strings/
        entnommen. Sie berechnet aus Byte-Arrays ein XOR.
        
        Args:
            ba1 (bytes):    Bytearray 1
            ba2 (bytes):    Bytearray 2

        Return:
            XOR von zwei Bytes, als Bytearray
        '''                                    
        
        return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])        

    def read_send(self, befehl, dat_Anz, res, um, dreh = True):
        ''' Sende Lese-Befehl und Lese die Antowrt des Lesebefehls aus!
        
        Args:
            befehl (str):       String mit Hex-Zahl
            dat_Anz (int):      Anzahl der Datenbytes der Antwort
            res (int):          Auflösung (Resolution) des Wertes
            um (int):           Umrechnungsfaktor
            dreh (bool):        True - Datenwertbytes werden von rechts nach links gelesen
        Return:
            value   (float, String):  ausgelesener Wert aus den Datenbytes
                                      Im Fall des Befehls 0x82 sind in der Antwort zwei Werte enthalten, da es den Max. Stromsollwert seperat
                                      gibt, muss hier etwas spezielles getan werden!
        '''
        # Kurze Verzögerung:
        time.sleep(self.Delay_sT/1000)              # ms in s
        # Befehl erstellen:
        ## Vorbereitung:
        write_list = []                             # Aussehen: [Header, Befehl, Checksumme]
        ## Header:
        header = hex(int(self.adress + '000', 2))   # Header bestimmen, Binär zu Hexadezimal-String
        header = self.hex_schnitt(header)
        write_list.append(header)
        ## Befehl:
        write_list.append(befehl)
        ## Checksumme:
        write_list.append(self.hex_schnitt(self.write_checksum(write_list)))
        logging.debug(f"{self.device_name} - {self.Log_Text_94_str[self.sprache]} {write_list}")

        # Senden und Auslesen:
        n = 0
        while n != self.Loop:
            ans_list = []
            ## Sende Befehl:
            for send_byte in write_list:
                self.serial.write(bytearray.fromhex(send_byte))
                logging.debug(f"{self.device_name} - {self.Log_Text_95_str[self.sprache]} {send_byte}!")

            ## Antwort auslesen:
            for ans_byte in range(1,dat_Anz + 6):   # ACK, Header, Befehl, Datenbytes, CS, Optionales Längenbyte bei Datenbytes >7 (oder 6)           
                ans = self.serial.read()
                ans_list.append(ans)
                #time.sleep(0.1)
            logging.debug(f"{self.device_name} - {self.Log_Text_96_str[self.sprache]} {ans_list}")

            ## Antwort verarbeiten:
            if b'' in ans_list:                     # Entferne Leere Byte-Arrays
                ans_list.remove(b'')   
            ### Überprüfe Sendebestätigung 
            if ans_list[0] == b'\x06':              
                logger.debug(f"{self.device_name} - {self.Log_Text_97_str[self.sprache]} {befehl}")
                ans_list.pop(0)                     # Entferne ACK
                ### Prüfe-Checksumme:
                key_alt = b'\x00'   
                for ans_byte in ans_list:
                    key = self.byte_xor(key_alt, ans_byte)
                    key_alt = key
                if key == b'\x00':
                    ans_list.pop(-1)                # Entferne Checksumme
                    logger.debug(f"{self.device_name} - {self.Log_Text_98_str[self.sprache]}")
                    ### Bestätige dem Generator das alles in Ordnung ist:
                    logger.debug(f"{self.device_name} - {self.Log_Text_99_str[self.sprache]}")
                    self.serial.write(bytearray.fromhex('06')) 
                    break
            elif ans_list[0] == b'\x15':
                logger.warning(f"{self.device_name} - {self.Log_Text_100_str[self.sprache]} {befehl}")
                # Wenn NAK erhalten wurde, dann wird dem Generator nicht NAK gesendet, sondern einfach noch einmal der Befehl!
                # Wenn der Generator NAK erhalten würde, so würde er den letzten Befehl nochmal bearbeiten.
                # Im Programm sollte das Schreiben dann vor die While-Schleife kommen! 
                # Notiz: mal ansprechen was lieber ist und was bei Fall 3 passieren soll!
            else:
                logger.warning(f"{self.device_name} - {self.Log_Text_101_str[self.sprache]} {befehl}")
                #break
            
            # Kurze Verzögerung:
            time.sleep(self.Delay_sT/1000)                      # ms in s
            # Nächste Schleife:
            n += 1
            logger.debug(f"{self.device_name} - {self.Log_Text_102_str[self.sprache]} {befehl} - {self.Log_Text_92_str[self.sprache]} {n}: {self.Log_Text_103_str[self.sprache]}")

        # Auswertung der Datenbytes:
        if not n == self.Loop:
            ## Header und Anzahl Datenbytes:
            header_ans = ans_list[0].hex()                      # Umwandeln in Hex (Quelle: https://java2blog.com/print-bytes-as-hex-python/)
            anz_ans_DatBy = bin(int(header_ans,16))[-3:]        # Umwandeln in Binär (Quelle: https://www.geeksforgeeks.org/python-ways-to-convert-hex-into-binary/) und Anzahl Datenbytes auslesen                

            ## Optionales Längenbyte, wenn vorhanden:
            if not anz_ans_DatBy == '111':
                anz_DatBy = int(anz_ans_DatBy,2) 
                for n in range(1,3):                            # Header und Befehl weg
                    ans_list.pop(0)
            else:
                op_L = ans_list[2].hex()
                anz_ans_DatBy = bin(int(op_L,16))
                anz_DatBy = int(anz_ans_DatBy,2)   
                for n in range(1,4):                            # Header, Befehl und Optionales Längenbyte weg
                    ans_list.pop(0) 

            ## Datenbytes:
            dat_list = []
            if dreh:
                for n in range(1 - anz_DatBy,1,1):
                    dat_list.append(ans_list[abs(n)].hex())
                if befehl == '82':
                    dat_list = dat_list[0:2]
                value = ''.join(dat_list)
                value = int(value, 16)
                value = value * res/um
            else:                                               # Wird bei Versionsnummer und Netzteil-Typ gebraucht:
                for n in range(0,anz_DatBy,1):
                    wert = chr(int(ans_list[abs(n)].hex(), 16))
                    dat_list.append(wert)
                value = ''.join(dat_list)
        else:
            value = m.nan                                        
        logger.debug(f"{self.device_name} - {self.Log_Text_104_str[self.sprache]} {value}")

        return value
            
    def read(self):
        ''' Lese TruHeat aus!

        Return: 
            self.value_name (dict): Aktuelle Werte 
        '''
        try:
            # Lese Ist-Leistung:
            logger.debug(f"{self.device_name} - {self.Log_Text_105_str[self.sprache]}")
            value = self.read_send(self.rbefIP, 2, self.resP, self.umP)
            value = value if type(value) == float else m.nan
            if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} ({self.rbefIP})')
            self.value_name['IWP'] = value                                                  # Einheit: kW
            # Lese Ist-Spannung:
            logger.debug(f"{self.device_name} - {self.Log_Text_106_str[self.sprache]}")
            value = self.read_send(self.rbefIU, 2, self.resU, self.umU)
            value = value if type(value) == float else m.nan
            if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} ({self.rbefIU})')
            self.value_name['IWU'] = value                                                  # Einheit: V 
            # Lese Ist-Strom:
            logger.debug(f"{self.device_name} - {self.Log_Text_107_str[self.sprache]}")
            value = self.read_send(self.rbefII, 2, self.resI, self.umI)
            if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} ({self.rbefII})')
            value = value if type(value) == float else m.nan
            self.value_name['IWI'] = value                                                  # Einheit: A
            # Lese Ist-Frequenz:
            logger.debug(f"{self.device_name} - {self.Log_Text_108_str[self.sprache]}")
            value = self.read_send(self.rbefIf, 2, self.resf, self.umf)
            value = value if type(value) == float else m.nan
            if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} ({self.rbefIf})')
            self.value_name['IWf'] = value                                                  # Einheit: kHz
            # Lese Soll-Leistung:
            logger.debug(f"{self.device_name} - {self.Log_Text_109_str[self.sprache]}")
            value = self.read_send(self.rbefSP, 2, self.resP, self.umP) 
            value = value if type(value) == float else m.nan
            if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} ({self.rbefSP})')
            self.value_name['SWP'] = value                                                 # Einheit: kW
            # Lese Soll-Spannung:
            logger.debug(f"{self.device_name} - {self.Log_Text_110_str[self.sprache]}")
            value = self.read_send(self.rbefSU, 2, self.resU, self.umU)
            value = value if type(value) == float else m.nan
            if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} ({self.rbefSU})')
            self.value_name['SWU'] = value                                                 # Einheit: V
            # Lese Soll-Leistung:
            logger.debug(f"{self.device_name} - {self.Log_Text_111_str[self.sprache]}")
            value = self.read_send(self.rbefSI, 2, self.resI, self.umI)
            value = value if type(value) == float else m.nan
            if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} ({self.rbefSI})')
            self.value_name['SWI'] = value                                                 # Einheit: A
            # PID-Modus:
            self.value_name['SWxPID'] = self.Soll
            self.value_name['IWxPID'] = self.Ist
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_112_str[self.sprache]}")

        return self.value_name

    ##########################################
    # Reaktion auf Initialisierung und Start:
    ##########################################
    def init_device(self):
        ''' Initialisierung des Gerätes TruHeat. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
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
        ## Watchdog:
        self.write_read_answer(self.wWDT, self.wdT, 1, 1, '010')
        logger.info(f"{self.device_name} - {self.Log_Text_113_str[self.sprache]} {self.wdT} {self.Log_Text_114_str[self.sprache]}")
        value = self.read_send('91', 2, 1, 1, True)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (91)')
        watchdog = value
        logger.info(f"{self.device_name} - {self.Log_Text_115_str[self.sprache]} {watchdog} {self.Log_Text_114_str[self.sprache]}")
        if self.wdT != watchdog:
            logger.warning(f"{self.device_name} - {self.Log_Text_116_str[self.sprache]}")
        ## Software Version:
        soft_version = self.read_send('C6', 11, 1, 1, False)
        logger.info(f"{self.device_name} - {self.Log_Text_117_str[self.sprache]} {soft_version}")
        ## Seriennummer Modul:
        value = self.read_send('C7', 4, 1, 1)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (C7)')
        snr = value
        logger.info(f"{self.device_name} - {self.Log_Text_118_str[self.sprache]} {int(snr) if not m.isnan(snr) else m.nan}")
        ## Netzteil-Typ:
        netzTyp = self.read_send('80', 21, 1, 1, False)
        logger.info(f"{self.device_name} - {self.Log_Text_119_str[self.sprache]} {netzTyp}")
        ## SIMIN und SUMIN:
        value = self.read_send('D0',2, self.resI, self.umI)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (D0)')
        simin = value
        logger.info(f"{self.device_name} - {self.Log_Text_120_str[self.sprache]} {simin}")
        value = self.read_send('D2',2, self.resU, self.umU)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (D2)')
        sumin = value
        logger.info(f"{self.device_name} - {self.Log_Text_121_str[self.sprache]} {sumin}")
        ## Maximale Leistung (und Strom):
        value = self.read_send('82', 4, 100, self.umP)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (82)')
        max_P = value
        logger.info(f"{self.device_name} - {self.Log_Text_122_str[self.sprache]} {max_P} {self.Log_Text_123_str[self.sprache]}")
        ## Maximale Spannung:
        value = self.read_send('CA',2, self.resU, self.umU)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (CA)')
        max_U = value
        logger.info(f"{self.device_name} - {self.Log_Text_124_str[self.sprache]} {max_U} {self.Log_Text_125_str[self.sprache]}")
        ## Maximaler Strom (Teil vom Kombi-Befehl):
        value = self.read_send('CB',2, self.resI, self.umI)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (CB)')
        max_I = value
        logger.info(f"{self.device_name} - {self.Log_Text_126_str[self.sprache]} {max_I} {self.Log_Text_127_str[self.sprache]}")
        ## Aktives Interface:
        interface = {0:'Bedienpanel', 1:'RS-232' , 2:'PROFIBUS' , 3:'CANopen' , 4:'Terminal' , 5:'AD-Schnittstelle' , 6:'Regulus (Temp)', 7:'User 1' , 8:'User 2' , 9:'User 3' , 10:'User 4'}
        value = self.read_send('9B',1, 1, 1)
        value = value if type(value) == float else m.nan
        if m.isnan(value): logger.warning(f'{self.device_name} - {self.Log_Nan_1_Float[self.sprache]} (9B)')
        else:
            ak_intF = value
            try:
                logger.info(f"{self.device_name} - {self.Log_Text_128_str[self.sprache]} {interface[ak_intF]}")
            except:
                logger.info(f"{self.device_name} - {self.Log_Text_129_str[self.sprache]} {ak_intF} | {self.Log_Text_130_str[self.sprache]} {interface}")
            if ak_intF != 1 and ak_intF != 10:
                logger.warning(f"{self.device_name} - {self.Log_Text_131_str[self.sprache]}")

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
        units = f"# datetime,s,kW,V,A,kHz,kW,V,A,{PID_x_unit},{PID_x_unit},\n"
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
            daten (Dict):               Dictionary mit den Daten in der Reihenfolge: Ist-PUIf, Soll-PUI ('IWP', 'IWU', 'IWI', 'IWf', 'SWP', 'SWU', 'SWI')
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