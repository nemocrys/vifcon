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
## Allgemein:
import logging
from serial import Serial, SerialException
import time

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


class PIAchse:
    def __init__(self, sprache, config, com_dict, test, neustart, add_Ablauf_function, name="PI-Achse", typ = 'Antrieb'):
        """ Erstelle PI-Achse Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      device configuration (as defined in config.yml in the devices-section).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            name (str, optional):               device name.
            typ (str, optional):                device name.
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

        ## Andere:
        self.akPos = 0
        self.value_name = {'IWs': 0, 'IWv': 0}

        ## Aus Config:
        self.mercury_model = self.config['mercury_model']  
        self.read_TT = self.config['read_TT_log']
        ### Zum Start:
        self.init = self.config['start']['init']                        # Initialisierung
        self.messZeit = self.config['start']["readTime"]                # Auslesezeit
        ### Parameter:
        self.cpm = self.config["parameter"]['cpm']                      # Counts per mm
        self.mvtime = self.config["parameter"]['mvtime']                # Delay-Zeit MV-Befehl (Auslesen der Geschwindigkeit)
        self.nKS = self.config['parameter']['nKS_Aus']                  # Nachkommerstellen
        ### Limits:
        self.oGPos = self.config["limits"]['maxPos']
        self.uGPos = self.config["limits"]['minPos']

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
        self.Log_Text_136_str   = ['Fehler Grund (Auslesen):',                                                              'Error reason (reading):']
        self.Log_Text_158_str   = ['Zielposition:',                                                                         'Target position:']
        self.Log_Text_159_str   = ['Versuch',                                                                               'Attempt']
        self.Log_Text_160_str   = ['funktioniert nicht!',                                                                   "doesn't work!"]
        self.Log_Text_161_str   = ['Mercury Adresse (Board):',                                                              'Mercury address (board):']
        self.Log_Text_162_str   = ['Status:',                                                                               'Status:']
        self.Log_Text_163_str   = ['Version:',                                                                              'Version:']
        self.Log_Text_164_str   = ['Startposition:',                                                                        'Starting position:']
        self.Log_Text_165_str   = ['mm',                                                                                    'mm']

        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                       'Initialization Failed!']
        self.Text_58_str        = ['Befehl MR erfolgreich gesendet!',                                                       'MR command sent successfully!']
        self.Text_59_str        = ['Befehl SV erfolgreich gesendet!',                                                       'SV command sent successfully!']
        self.Text_60_str        = ['Befehl DH erfolgreich gesendet!',                                                       'DH command sent successfully!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                        'Sending failed!']
        self.Text_62_str        = ['Achse wurde erfolgreich angehalten!',                                                   'Axis was stopped successfully!']

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
        self.adv = self.config["parameter"]['adv']                      # Adressauswahlcode
        steuer = '0D'                                                   # Befehl-Abschlusszeichen (\r)
        self.t1 = bytearray.fromhex(self.adv)                           # Adressauswahlcode vorbereiten zum senden
        self.t3 = bytearray.fromhex(steuer)                             # Befehl-Abschlusszeichen vorbereiten zum senden

    ##########################################
    # Schnittstelle (Schreiben):
    ##########################################
    def write(self, write_Okay, write_value):
        ''' Sende Befehle an die Achse um Werte zu verändern.

        Args:
            write_Okay (dict):  beinhaltet Boolsche Werte für das was beschrieben werden soll!
            write_value (dict): beinhaltet die Werte die geschrieben werden sollen
        '''
        # Start:
        if write_Okay['Start'] and not self.neustart:
            self.Start_Werte()
            write_Okay['Start'] = False

        # Sende Stopp:
        if write_Okay['Stopp']:
            self.stopp()
            # Rücksetzen aller Bewegungen:
            write_Okay['Stopp'] = False
            write_Okay['Position'] = False
            write_Okay['Speed'] = False                                    
        # Schreiben, wenn nicht Stopp:
        else:
            try:
                if write_Okay['Sende Position']:
                    fahre = round(write_value["Position"] * int(self.cpm))                                      # Befehl bekommt einen Integer!
                    Befehl = f'MR{fahre}'
                    self.serial.write(self.t1+Befehl.encode()+self.t3)
                    write_Okay['Sende Position'] = False
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_58_str[self.sprache]}')       
                if write_Okay['Sende Speed']:
                    Befehl = f'SV{round(write_value["Speed"])}'
                    self.serial.write(self.t1+Befehl.encode()+self.t3)
                    write_Okay['Sende Speed'] = False 
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_59_str[self.sprache]}')      
                if write_Okay['Define Home']:
                    Befehl = 'DH'
                    self.serial.write(self.t1+Befehl.encode()+self.t3)
                    write_Okay['Define Home'] = False 
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_60_str[self.sprache]}')
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_61_str[self.sprache]}')           
        
        # Lese Aktuelle Position aus:
        if self.init:
            self.akPos = self.read_TP()

    def stopp(self):
        ''' Halte Motor an und setze STA-LED auf rot ''' 
        Befehl = 'AB'                                                                                            
        self.serial.write(self.t1+Befehl.encode()+self.t3)
        time.sleep(0.1)                                                 # Kurze Verzögerung, damit der Motor stehen bleiben kann und die Zielposition geupdatet werden kann
        Befehl = 'MF'
        self.serial.write(self.t1+Befehl.encode()+self.t3)              # Status Lampe leuchtet nun Rot
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_62_str[self.sprache]}')          

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
            position = self.read_TP()
            self.value_name['IWs'] = position       # Einheit: mm

            # Lese Geschwindigkeit:
            speed = self.read_TV()
            self.value_name['IWv'] = speed          # Einheit: mm/s

            # Lese Zielposition in Log-Datei:
            if self.read_TT:
                ziel = self.send_read_command('TT', 'T:')
                logger.debug(f"{self.device_name} - {self.Log_Text_158_str[self.sprache]} {ziel/int(self.cpm)}")

        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")

        return self.value_name

    def read_TP(self):
        '''Lese die Aktuelle Position
        
        Return:
            position (float):   aktuelle position
        '''
        position = self.send_read_command('TP', 'P:')
        position = round(position/int(self.cpm), self.nKS)

        return position

    def read_TV(self):
        '''Lese die Aktuelle Geschwindigkeit
        
        Return:
            speed (float):  aktuelle Geschwindigkeit
        '''
        if self.mercury_model == 'C862':
            speed = self.send_read_command(f'TV{self.mvtime}', 'V:', self.mvtime/1000) 
            speed = speed*1000/self.mvtime
        elif self.mercury_model == 'C863':
            speed = self.send_read_command(f'TV', 'V:')   
        speed = round(speed/int(self.cpm), self.nKS) 

        return speed

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
        self.serial.write(self.t1+Befehl.encode()+self.t3)
        time.sleep(delay)
        ant = self.serial.readline().decode()
        ant = self.entferneSteuerzeichen(ant)
        while n != 10:
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
                
            if n == 10:
                ant = ''
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
            self.akPos = self.read_TP()
            logger.info(f"{self.device_name} - {self.Log_Text_164_str[self.sprache]} {self.akPos} {self.Log_Text_165_str[self.sprache]}")

###################################################
# Messdatendatei erstellen und beschrieben:
###################################################
    def messdaten_output(self, pfad="./"):
        """Erstelle für das Gerät eine csv-Datei mit den Daten.

        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = "# datetime,s,mm,mm/s,\n"
        #scaling = f"# -,-,{self.}"
        header = "time_abs,time_rel,Position,Geschwindigkeit,\n"
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
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''