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
    QCoreApplication
)

## Allgemein:
import logging
from serial import Serial, SerialException
import time

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


class Eurotherm:
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
        ### Limits:
        self.oGOp = self.config["limits"]['opMax']

        ## Werte Dictionary:
        self.value_name = {'SWT': 0, 'IWT': 0, 'IWOp': 0}

        ## Weitere:
        self.EuRa_Aktiv = False

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
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                'Error reason (send):']
        self.Log_Text_103_str   = ['Wiederhole senden nach NAK oder keiner Antwort!',                                       'Repeat send after NAK or no response!']
        self.Log_Text_132_str   = ['BCC (DEC)',                                                                             'BCC (DEC)']
        self.Log_Text_133_str   = ['Keine Antwort oder Falsche Antwort, kein NAK oder ACK!',                                'No answer or wrong answer, no NAK or ACK!']
        self.Log_Text_134_str   = ['Antwort konnte nicht ausgelesen werden!',                                               'Answer could not be read!']
        self.Log_Text_135_str   = ['Fehler Grund (Sende Antwort):',                                                         'Error reason (send response):']
        self.Log_Text_136_str   = ['Fehler Grund (Auslesen):',                                                              'Error reason (reading):']
        self.Log_Text_137_str   = ['Instrumenten Identität:',                                                               'Instrument identity:']
        self.Log_Text_138_str   = ['Software Version:',                                                                     'Software version:']
        self.Log_Text_139_str   = ['Instrumenten Modus:',                                                                   'Instrument mode:']
        self.Log_Text_140_str   = ['Normaler Betriebsmodus',                                                                'Normal Operation Mode']
        self.Log_Text_141_str   = ['Kein Effekt',                                                                           'No effect']
        self.Log_Text_142_str   = ['Konfigurationsmodus',                                                                   'Configuration Mode']
        self.Log_Text_143_str   = ['Ausgabe auf Display:',                                                                  'Output on display:']
        self.Log_Text_144_str   = ['bis',                                                                                   'to']
        self.Log_Text_145_str   = ['°C',                                                                                    '°C']
        self.Log_Text_146_str   = ['Sollwertbereich:',                                                                      'Setpoint range:']
        self.Log_Text_147_str   = ['PID-Regler Parameter:',                                                                 'PID controller parameters:']
        self.Log_Text_148_str   = ['P:',                                                                                    'P:']
        self.Log_Text_149_str   = ['I:',                                                                                    'I:']
        self.Log_Text_150_str   = ['D:',                                                                                    'D:']
        self.Log_Text_151_str   = ['Statuswort:',                                                                           'Status word:']
        self.Log_Text_152_str   = ['Automatischer Modus wird eingeschaltet!',                                               'Automatic mode is turned on!']
        self.Log_Text_153_str   = ['Manueller Modus wird eingeschaltet!',                                                   'Manual mode is switched on!']
        self.Log_Text_154_str   = ['Statuswort ist nicht 0000 oder 8000! Startmodus wird nicht geändert!',                  'Status word is not 0000 or 8000! Start mode is not changed!']
        self.Log_Text_155_str   = ['Ändere Maximale Ausgangsleistungslimit auf',                                            'Change Maximum Output Power Limit to']
        self.Log_Text_156_str   = ['%',                                                                                     '%']
        self.Log_Text_157_str   = ['Maximale Ausgangsleistung wird durch die Eingabe am Gerät bestimmt!',                   'Maximum output power is determined by the input on the device!']
        self.Log_Text_183_str   = ['Das Senden der Werte ist fehlgeschlagen! (Rampe)',                                      'Sending the values failed! (Ramp)']
        self.Log_Text_243_str   = ['Beim Startwert senden an Eurotherm gab es einen Fehler! Programm wird beendet! Wurde das Gerät eingeschaltet bzw. wurde die Init-Einstellung richtig gesetzt?',
                                   'There was an error when sending the start value to Eurotherm! Program will end! Was the device switched on or was the init setting set correctly?']
        self.Log_Text_244_str   = ['Fehler Grund: ',                                                                        'Error reason:']
        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                       'Initialization Failed!']
        self.Text_53_str        = ['Wert wurde angenommen (ACK)!',                                                          'Value was accepted (ACK)!']
        self.Text_54_str        = ['Wert wurde nicht angenommen (NAK)!',                                                    'Value was not accepted (NAK)!']
        self.Text_55_str        = ['Senden fehlgeschlagen (Keine Antwort)!',                                                'Sending failed (no response)!']
        self.Text_56_str        = ['Befehl gesendet!',                                                                      'command sent!']
        self.Text_57_str        = ['Antwort nicht auslesbar!',                                                              'Answer cannot be read!']
        self.Text_75_str        = ['Sende Eurotherm Rampe mit dem Aufbau',                                                  'Send Eurotherm ramp with the structure']
        self.Text_76_str        = ['Eurotherm-Rampe wird gestartet',                                                        'Eurotherm ramp is started']
        self.Text_77_str        = ['Reset der Eurotherm-Rampe',                                                             'Reset the Eurotherm ramp']
        self.Text_78_str        = ['Reset der Eurotherm-Rampe wegen Abbruch! Aktuellen Sollwert speichern!',                'Reset of the Eurotherm ramp due to cancellation! Save current setpoint!']

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
        logging.debug(f'{self.device_name} - {self.Log_Text_132_str[self.sprache]} = "{bcc}"')
        return chr(bcc)                         # Dezimalzahl zu ASCII

    def write(self, write_Okay, write_value):
        ''' Schreiben der übergebenden Werte, wenn der richtige Knopf betätigt wurde!

        Args:
            write_Okay (dict):  beinhaltet Boolsche Werte für das was beschrieben werden soll!
            write_value (dict): beinhaltet die Werte die geschrieben werden sollen
        '''

        # Sollwertn Lesen (OP oder Temp):
        sollwert = write_value['Sollwert']

        # Schreiben:
        ## Ändere Modus:
        if write_Okay['Auto_Mod']:
            self.write_read_answer('SW>', '0000', self.write_Modus)                
            write_Okay['Auto_Mod'] = False
        elif write_Okay['Manuel_Mod']:
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
            self.serial.write(self.read_temperature.encode())
            temperature = float(self.serial.readline().decode()[3:-2])
            self.value_name['IWT'] = temperature                                # Einheit: °C
            # Lese Leistungswert:
            self.serial.write(self.read_op.encode())
            op = float(self.serial.readline().decode()[3:-2])
            self.value_name['IWOp'] = op                                        # Einheit: %
            # Lese Soll-Temperatur:
            self.serial.write(self.read_soll_temperatur.encode())
            soll_temperatur = float(self.serial.readline().decode()[3:-2])
            self.value_name['SWT'] = soll_temperatur                            # Einheit: °C
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")

        return self.value_name

    def check_HO(self):
        ''' lese die maximale Ausgangsleistungs Grenze aus., wenn im Sicherheitsmodus.

        Return:
            '' (str):           Fehlerfall
            max_pow (float):    Aktuelle maximale Ausgangsleistung 
        '''
        if self.config['start']['sicherheit'] == True:
            self.serial.write(self.read_max_leistung.encode())
            max_pow = float(self.serial.readline().decode()[3:-2])
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
        units = "# datetime,s,DEG C,DEG C,%,\n"
        #scaling = f"# -,-,{self.}"
        header = "time_abs,time_rel,Soll-Temperatur,Ist-Temperatur,Operating-point,\n"
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
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''