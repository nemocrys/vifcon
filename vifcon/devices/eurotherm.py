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
    signal_PID  = pyqtSignal(float, float)

    def __init__(self, sprache, config, com_dict, test, neustart, add_Ablauf_function, name="Eurotherm", typ = 'Generator'):
        """ Erstelle Eurotherm Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      Geräte Konfigurationen (definiert in config.yml in der devices-Sektion).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            name (str, optional):               Geräte Namen.
            typ (str, optional):                Geräte Typ.
        """
        super().__init__()
        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Funktionsübergabe einlesen:
        self.sprache = sprache
        self.config = config
        self.neustart = neustart
        self.add_Text_To_Ablauf_Datei = add_Ablauf_function
        self.device_name = name
        self.typ = typ

        ## Aus Config:
        ### Zum Start:
        self.init = self.config['start']['init']                # Initialisierung
        self.messZeit = self.config['start']["readTime"]        # Auslesezeit
        self.Ist = self.config['PID']["start_ist"] 
        self.Soll = self.config['PID']["start_soll"] 
        self.op = 0
        ### Limits:
        self.oGOp = self.config["limits"]['opMax']

        ## Werte Dictionary:
        self.value_name = {'SWT': 0, 'IWT': 0, 'IWOp': 0, 'SWTPID': self.Soll, 'IWTPID': self.Ist}

        ## Weitere:
        self.EuRa_Aktiv     = False
        self.Save_End_State = False
        self.done_ones      = False

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
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
        self.Log_Text_155_str   = ['Ändere Maximale Ausgangsleistungslimit auf',                                                                                                                                            'Change Maximum Output Power Limit to']
        self.Log_Text_156_str   = ['%',                                                                                                                                                                                     '%']
        self.Log_Text_157_str   = ['Maximale Ausgangsleistung wird durch die Eingabe am Gerät bestimmt!',                                                                                                                   'Maximum output power is determined by the input on the device!']
        self.Log_Text_183_str   = ['Das Senden der Werte ist fehlgeschlagen! (Rampe)',                                                                                                                                      'Sending the values failed! (Ramp)']
        self.Log_Text_243_str   = ['Beim Startwert senden an Eurotherm gab es einen Fehler! Programm wird beendet! Wurde das Gerät eingeschaltet bzw. wurde die Init-Einstellung richtig gesetzt?',                         'There was an error when sending the start value to Eurotherm! Program will end! Was the device switched on or was the init setting set correctly?']
        self.Log_Text_244_str   = ['Fehler Grund: ',                                                                                                                                                                        'Error reason:']
        self.Log_Text_PID_str   = ['Start des PID-Threads!',                                                                                                                                                                'Start of the PID thread!']
        Log_Text_PID_N1         = ['Die Konfiguration',                                                                                                                                                                     'The configuration']
        Log_Text_PID_N2         = ['existiert nicht! Möglich sind nur VV, VM, MM oder MV. Nutzung von Default VV!',                                                                                                         'does not exist! Only VV, VM, MM or MV are possible. Use default VV!']
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
        self.Log_Text_PID_N20   = ['°C - tatsächlicher Wert war',                                                                                                                                                           '°C - tatsächlicher Wert war']
        ## Ablaufdatei:
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

        #---------------------------------------
        # PID-Regler:
        #---------------------------------------
        ## PID-Regler:
        self.PID = PID(self.sprache, self.device_name, self.config['PID'], self.oGOp, self.config["limits"]['opMin'])
        self.PID_Option = self.config['PID']['Value_Origin'].upper()
        ## Info und Warnungen:
        if self.PID_Option not in ['VV', 'VM', 'MM', 'MV']:
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
        # Erwinge das Setzen der Variablen um den Endzustand sicher herzustellen:
        if self.Save_End_State and not self.done_ones:
            write_Okay['EuRa_Reset']        = True
            write_Okay['Manuel_Mod']        = True   
            write_Okay['Auto_Mod']          = False
            write_Okay['Operating point']   = True 
            write_value['Rez_OPTemp']       = 0 
            self.done_ones                  = True

        # Normaler Betrieb:
        if not write_value ['PID']:  
            # Sollwertn Lesen (OP oder Temp):
            sollwert = write_value['Sollwert']
            PID_write_OP = False
        # PID-Regler:
        elif write_value['PID']:
            # Sollwertn Lesen (OP oder Temp):
            sollwert = write_value['PID-Sollwert']
            ## Auswahl Istwert:
            ### VIFCON:
            if self.PID_Option[0] == 'V':
                self.Ist = self.read_einzeln(self.read_temperature)
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
                    logger.debug(f"{self.device_name} - {self.Log_Text_PID_N15[self.sprache]} {self.PID_Input_Limit_Max}{self.Log_Text_PID_N20[self.sprache]} {self.Ist}{self.Log_Text_145_str[self.sprache]}")
                    self.Ist = self.PID_Input_Limit_Max
                #### Input-Wert unterschreitet Minimum:
                elif self.Ist < self.PID_Input_Limit_Min:
                    logger.debug(f"{self.device_name} - {self.Log_Text_PID_N16[self.sprache]} {self.PID_Input_Limit_Min}{self.Log_Text_PID_N20[self.sprache]} {self.Ist}{self.Log_Text_145_str[self.sprache]}")
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
            ## Auswahl Sollwert:
            ### VIFCON:
            if self.PID_Option[1] == 'V':
                self.Soll = sollwert
            ### MUltilog:
            elif self.PID_Option[1] == 'M':
                print('Noch nicht Vorhanden!')
            ## Schreibe Werte:
            PID_write_OP = True
            PowOutPID = self.op

        # Schreiben:
        ## Ändere Modus:
        if write_Okay['Auto_Mod'] and not write_value['PID']:
            self.write_read_answer('SW>', '0000', self.write_Modus)                
            write_Okay['Auto_Mod'] = False
        elif write_Okay['Manuel_Mod'] or write_value['PID']:
            ## Immer beim Umsachalten, wenn die Sicherheit auf True steht wird der HO ausgelesen:
            value_HO = self.check_HO()
            if value_HO != '':
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
                self.serial.write(self.read_soll_temperatur.encode())
                soll_temperatur = float(self.serial.readline().decode()[3:-2])
                ### Übergebe diesem Eurotherm:
                self.write_read_answer('SL', str(soll_temperatur), self.write_temperatur)
                ### Reset des Programms:
                self.write_read_answer('OS>', '0100', self.EuRa_Modus)
                write_Okay[auswahl] = False
            ## Lese Maximum OP:
            elif write_Okay[auswahl] and auswahl == 'Read_HO':
                value_HO = self.check_HO()
                if value_HO != '':
                    self.oGOp = value_HO
                write_Okay[auswahl] = False
            ## Schreibe Maximum OP.
            elif write_Okay[auswahl] and auswahl == 'Write_HO':
                self.write_read_answer('HO', str(write_value['HO']), self.write_max_leistung)
                write_Okay[auswahl] = False

    def write_read_answer(self, write_mn, value, befehl_start):
        ''' Lese die Antowrt des Schreibbefehls aus!
        
        Args:
            write_mn (str):     Mnemonik Befehl des Eurotherms
            value (str):        übergebender Wert
            befehl_start (str): Start des Befehls
        '''
        # Schreibe:
        bcc_Wert = self.bcc(write_mn + value)
        try: 
            self.serial.write(f'{befehl_start}{value}\x03{bcc_Wert}'.encode())
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")

        # Lese Antwort (Kontrolle des Eingangs des Befehls):
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {write_mn}{value} {self.Text_56_str[self.sprache]}')
        try:
            answer = self.serial.readline().decode()                                            
            if answer == '\x06':
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
        i = 0
        for s in segment_v:
            stop = 0
            while 1:
                write_rampe = f"\x040000\x02{Segement[i]}"
                Sollwert = s
                bcc_Wert = self.bcc(f'{Segement[i]}' + str(Sollwert))
                self.serial.write(f'{write_rampe}{Sollwert}\x03{bcc_Wert}'.encode())
                try:
                    answer = self.serial.readline().decode()
                    if answer == '\x06':
                        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_53_str[self.sprache]}')          
                        logger.debug(f'{self.device_name} {self.Text_53_str[self.sprache]}')
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

        return self.value_name
    
    def read_einzeln(self, befehl):
        ''' Zusammenfassung der einzelnen Sende-Befehle
        
        Args: 
            befehl (str):   Befehlsstring (Steuerzeichen und Mnemonics)

        Return:
            ans (float):    Antwort des Gerätes in Float umgefandelt
        '''
        self.serial.write(befehl.encode())
        ans = float(self.serial.readline().decode()[3:-2])
        return ans

    def check_HO(self):
        ''' lese die maximale Ausgangsleistungs Grenze aus., wenn im Sicherheitsmodus.

        Return:
            '' (str):           Fehlerfall
            max_pow (float):    Aktuelle maximale Ausgangsleistung 
        '''
        if self.config['start']['sicherheit'] == True:
            max_pow = self.read_einzeln(self.read_max_leistung)
            return max_pow
        return ''

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
            ### XP - proportional band
            self.serial.write("\x040000XP\x05".encode())
            P = str(self.serial.readline().decode()[4:-2])
            ### TI - Integral time
            self.serial.write("\x040000TI\x05".encode())
            I = str(self.serial.readline().decode()[4:-2])
            ### TD - Derivative time
            self.serial.write("\x040000TD\x05".encode())
            D = str(self.serial.readline().decode()[4:-2])
            logger.info(f"{self.device_name} - {self.Log_Text_147_str[self.sprache]} {self.Log_Text_148_str[self.sprache]} {P.strip()}, {self.Log_Text_149_str[self.sprache]} {I.strip()}, {self.Log_Text_150_str[self.sprache]} {D.strip()}")
            ## Statuswort:
            self.serial.write("\x040000SW\x05".encode())
            stWort = str(self.serial.readline().decode()[3:-2])
            logger.info(f"{self.device_name} - {self.Log_Text_151_str[self.sprache]} {stWort}")
            if stWort == '>0000' or stWort == '>8000':
                ## Start-Modus setzen:
                if self.config['start']["start_modus"] == 'Auto':
                    self.write_read_answer('SW>', '0000', self.write_Modus) 
                    logger.info(f"{self.device_name} - {self.Log_Text_152_str[self.sprache]}")
                elif self.config['start']["start_modus"] == 'Manuel':
                    self.write_read_answer('SW>', '8000', self.write_Modus)
                    logger.info(f"{self.device_name} - {self.Log_Text_153_str[self.sprache]}")
            else:
                logger.warning(f"{self.device_name} - {self.Log_Text_154_str[self.sprache]}")
            ## Änderung von HO:
            if self.config['start']['sicherheit'] == False:
                self.write_read_answer('HO', str(self.oGOp), self.write_max_leistung)
                logger.info(f"{self.device_name} - {self.Log_Text_155_str[self.sprache]} {self.oGOp} {self.Log_Text_156_str[self.sprache]}")
            else:
                logger.info(f"{self.device_name} - {self.Log_Text_157_str[self.sprache]}")
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
        self.signal_PID.emit(self.Ist, self.Soll)
        self.op = self.PID.Output

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''