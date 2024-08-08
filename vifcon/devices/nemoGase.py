# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo Gase (Drücke, Durchfluss und Drehzahl):
- Schnittstelle erstellen
- Werte Lesen und schreiben
- Messdatei updaten
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## Allgemein:
import logging
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import time

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


class NemoGase:
    def __init__(self, sprache, config, com_dict, test, add_Ablauf_function, name="nemoGase", typ = 'Monitoring'):
        """ Erstelle Nemo Gase Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      Geräte Konfigurationen (definiert in config.yml in der devices-Sektion).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
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
        self.add_Text_To_Ablauf_Datei = add_Ablauf_function
        self.device_name = name
        self.typ = typ

        ## Aus Config:
        ### Zum Start:
        self.init = self.config['start']['init']                # Initialisierung
        self.messZeit = self.config['start']["readTime"]        # Auslesezeit
        ### Parameter:
        self.nKS = self.config['parameter']['nKS_Aus']          # Nachkommerstellen
        ### Register:
        self.start_Lese_Register = self.config['register']['lese_st_Reg']       # Input Register Start-Register
    
        ## Werte Dictionary:
        self.value_name = {'MFC24': 0, 'MFC25': 0, 'MFC26': 0,  'MFC27': 0, 'DM21': 0, 'PP21': 0, 'PP22': 0, 'PP21Status': 0, 'PP22Status': 0, 'PP22I': 0}

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                       'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',    'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                     'Error reason (interface structure):']
        self.Log_Text_63_str    = ['Antwort Messwerte:',                                                        'Answer measurements:']
        self.Log_Text_64_str    = ['Das Gerät konnte nicht ausgelesen werden.',                                 'The device could not be read.']
        self.Log_Text_65_str    = ['Fehler Grund (Gerät Auslesen):',                                            'Error reason (reading device):']
        self.Log_Text_66_str    = ['Antwort Register Integer:',                                                 'Response Register Integer:']
        self.Log_Text_67_str    = ['Messwerte Umgewandelt - Messwert',                                          'Measured Values Converted - Measured Value']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                              'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                           'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                      'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                           'No measurement data recording active!']
        self.Log_Text_Port_1    = ['Verbindungsfehler:',                                                                    'Connection error:']
        self.Log_Text_Port_2    = ['Der Test für den Verbindungsaufbau ist fehlgeschlagen!',                                'The connection establishment test failed!']
        self.Log_Text_Port_3    = ['Antwort der Test-Abfrage war None. Bearbeitung nicht möglich!',                         'The answer to the test query was None. Processing not possible!']
        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                          'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                           'Initialization Failed!']
        
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
        
        if self.init:
            for n in range(0,5,1):
                if not self.serial.is_open:
                    self.Test_Connection()
            if not self.serial.is_open:
                logger.warning(f"{self.device_name} - {self.Log_Text_61_str[self.sprache]}")
                logger.warning(f"{self.device_name} - {self.Log_Text_Port_2[self.sprache]}")
                exit()

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def read(self):
        ''' Lese Nemo Gase aus!

        Return: 
            self.value_name (dict): Aktuelle Werte 
        '''

        try:
            # Lese: MFC24, MFC25, MFC26,  MFC27, DM21, PP21, PP22, PP21 Status, PP22 Status, PP22 Drehzahl: 
            ans = self.serial.read_input_registers(self.start_Lese_Register, 18)
            logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')

            value_1 = self.umwandeln_Float(ans[0:14])   # MFC24, MFC25, MFC26, MFC27, DM21, PP21, PP22,
            value_2 = self.umwandeln_Float(ans[-2:])    # PP22 Drehzahl
            self.value_name['PP21Status'] = ans[14]   
            self.value_name['PP22Status'] = ans[15]  

            # Reiehnfolge: MFC24, MFC25, MFC26, MFC27, DM21, PP21, PP22, PP22I
            self.value_name['MFC24'] = value_1[0]   # Einheit: ml/min
            self.value_name['MFC25'] = value_1[1]   # Einheit: ml/min
            self.value_name['MFC26'] = value_1[2]   # Einheit: ml/min
            self.value_name['MFC27'] = value_1[3]   # Einheit: ml/min
            self.value_name['DM21']  = value_1[4]   # Einheit: mbar
            self.value_name['PP21']  = value_1[5]   # Einheit: mbar
            self.value_name['PP22']  = value_1[6]   # Einheit: mbar
            self.value_name['PP22I'] = value_2[0]   # Einheit: %
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_65_str[self.sprache]}")

        return self.value_name
    
    def umwandeln_Float(self, int_Byte_liste):
        ''' Sendet den Lese-Befehl an die Achse.

        Args:
            int_Byte_liste (list):            Liste der ausgelesenen Bytes mit Integern
        Return:
            value_list (list):                Umgewandelte Zahlen
        '''

        Bits_List_32 = utils.word_list_to_long(int_Byte_liste, big_endian=True, long_long=False)
        logger.debug(f'{self.device_name} - {self.Log_Text_66_str[self.sprache]} {Bits_List_32}')

        value_list = []
        i = 1
        for word in Bits_List_32:
            value = utils.decode_ieee(word)
            value_list.append(round(value, self.nKS))
            logger.debug(f'{self.device_name} - {self.Log_Text_67_str[self.sprache]} {i}: {value}')
            i += 1

        return value_list

    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung des Geräte Nemo Gase. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
        if not self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_51_str[self.sprache]}')
            logger.info(f"{self.device_name} - {self.Text_51_str[self.sprache]}")
            # Schnittstelle prüfen:
            try:
                ## Prüfe Verbindung:
                for n in range(0,5,1):
                    self.Test_Connection()
                if not self.serial.is_open:
                    raise ValueError(self.Log_Text_Port_2[self.sprache])
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

    ###################################################
    # Messdatendatei erstellen und beschrieben:
    ###################################################
    def messdaten_output(self, pfad="./"):
        """Erstelle für das Gerät eine csv-Datei mit den Daten.
           MFC24, MFC25, MFC26, MFC27, DM21, PP21, PP22, PP21Status, PP22Status, PP22I
        
        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = "# datetime,s,ml/min,ml/min,ml/min,ml/min,mbar,mbar,mbar,%,\n"
        #scaling = f"# -,-,{self.}"
        header = "time_abs,time_rel,MFC24,MFC25,MFC26,MFC27,DM21,PP21,PP22,PP22I,\n"
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
            if not 'Status' in size:
                line = line + f'{daten[size]},'
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f'{line}\n')
    
    ###################################################
    # Prüfe die Verbindung:
    ###################################################
    def Test_Connection(self):
        '''Aufbau Versuch der TCP/IP-Verbindung zur Nemo-Anlage'''
        try:
            self.serial.open()
            time.sleep(0.1)         # Dadurch kann es in Ruhe öffnen
            ans = self.serial.read_input_registers(self.start_Lese_Register, 1)  # MFC24
            if ans == None:
                raise ValueError(self.Log_Text_Port_3[self.sprache])
            else:
                self.umwandeln_Float(ans)
        except Exception as e:
            logger.exception(self.Log_Text_Port_1[self.sprache])
            self.serial.close()
            
##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''