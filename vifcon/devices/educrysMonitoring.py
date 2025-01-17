# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Educrys Monitoring (Temperaturen, PID-Werte und Kristallwerte):
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
import math as m
import datetime

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


class EducrysMon:
    def __init__(self, sprache, config, com_dict, test, Log_WriteReadTime, add_Ablauf_function, name="Educrys-Monitoring", typ = 'Monitoring'):
        """ Erstelle Nemo Gase Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      Geräte Konfigurationen (definiert in config.yml in der devices-Sektion).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            test (bool):                        Test Modus
            Log_WriteReadTime (bool):           Logge die Zeit wie lange die Write und Read Funktion dauern
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
        self.Log_WriteReadTime          = Log_WriteReadTime
        self.add_Text_To_Ablauf_Datei = add_Ablauf_function
        self.device_name = name
        self.typ = typ

        ## Werte Dictionary:
        self.value_name     = {'TC1_T': 0,    'TC2_T': 0,       'PT1_T': 0,   'PT2_T': 0,   'Pyro_T': 0,
                               'PID_Out': 0,  'PID_P': 0,       'PID_I': 0,   'PID_D': 0,   'PID_In': 0,  'PID_In_M': 0,
                               'K_weight': 0, 'K_weight_M': 0,  'K_d': 0
                              }  

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
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                      'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                         'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                               'The following types are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                              'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',    'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                  '; Set to default:']
        self.Log_Pfad_conf_5_1  = ['; Register-Fehler -> Programm zu Ende!!!',              '; Register error -> program ends!!!']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                          'Reason for error:']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                  'Incorrect input:']
        self.Log_Pfad_conf_8_1  = ['Fehlerhafte Typ:',                                      'Incorrect type:']

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
        ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0
        ### Messzeit:
        if not type(self.messZeit) in [int, float] or not self.messZeit >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} readTime - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer, Float] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 2 - {self.Log_Pfad_conf_8[self.sprache]} {self.messZeit}')
            self.messZeit = 2
        ### Nachkommerstellen:
        if not type(self.nKS) in [int] or not self.nKS >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nKS_Aus - {self.Log_Pfad_conf_2_1[self.sprache]} [Integer] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 3 - {self.Log_Pfad_conf_8[self.sprache]} {self.nKS}')
            self.nKS = 3

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging: ##################################################################################################################################################################################################################################################################################
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                       'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',    'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                     'Error reason (interface structure):']
        self.Log_Text_63_str    = ['Antwort Messwerte:',                                                        'Answer measurements:']
        self.Log_Text_64_str    = ['Das Gerät konnte nicht ausgelesen werden.',                                 'The device could not be read.']
        self.Log_Text_65_str    = ['Fehler Grund (Gerät Auslesen):',                                            'Error reason (reading device):']
        self.Log_Text_67_str    = ['Messwerte Umgewandelt - Messwert',                                          'Measured Values Converted - Measured Value']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                              'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                           'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                      'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                           'No measurement data recording active!']
        self.Log_Text_Port_1    = ['Verbindungsfehler:',                                                        'Connection error:']
        self.Log_Text_Port_2    = ['Der Test für den Verbindungsaufbau ist fehlgeschlagen!',                    'The connection establishment test failed!']
        self.Log_Text_Port_3    = ['Antwort der Test-Abfrage war None. Bearbeitung nicht möglich!',             'The answer to the test query was None. Processing not possible!']
        self.Log_Text_Port_4    = ['Bei der Werte-Umwandlung ist ein Fehler aufgetreten!',                      'An error occurred during value conversion!']
        self.Log_Text_Port_5    = ['Fehlerbeschreibung:',                                                       'Error description:']
        self.Log_Test_Ex_1      = ['Der Variablen-Typ der Größe',                                               'The variable type of size']
        self.Log_Test_Ex_2      = ['ist nicht Float! Setze Nan ein! Fehlerhafter Wert:',                        'is not Float! Insert Nan! Incorrect value:']
        self.Log_Time_wr        = ['s gedauert!',                                                               's lasted!']   
        self.Log_Time_r         = ['Die read-Funktion hat',                                                     'The read function has']  
        self.Log_Text_EM001_str = ['bereinigt',                                                                 'adjusted']
        ## Ablaufdatei: ##############################################################################################################################################################################################################################################################################
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
                    self.serial = Serial(**config["serial-interface"])
                else:
                    self.serial = com_dict[com_ak]
        except SerialException as e:
            self.serial = SerialMock()
            logger.warning(f"{self.device_name} - {self.Log_Text_61_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_62_str[self.sprache]}")
            exit()

    ##########################################
    # Schnittstelle (lesen):
    ##########################################
    def read(self):
        ''' Lese Educrys Monitoring aus!

        Return: 
            self.value_name (dict): Aktuelle Werte 
        '''
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

        try:
            # Lese alle Monitoringswerte aus (Mehr als gebraucht!) - 29 Werte
            self.serial.write(('!\r').encode())
            time.sleep(0.1)
            # Lese Antwort:
            ''' 
            1. read_until() - liest bin \n -> Timeout auf None, da scheinbar ein Bug in serial!
            2. decode()     - Bytearray umwandeln
            3. strip()      - Leerzeichen am Anfang und Ende entfernen
            4. replace()    - *, # und Abschlusszeichen entfernen

            Antwort-Beispiel: 5212.780 794.726 24.58 -99.00 22.87 -242.02 -99.00 0.00 0 0 0 0.00 0.000000 0 0 1000.00 0.00 22.87 22.85 20.00 -569.24 1000.00 -0.00 200.00 0.00 0.00 0.00 -0.00 0.00
            '''
            ans = self.serial.read_until()
            logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')
            ans = ans.decode().strip().replace('*', '').replace('#','').replace('\r\n','')
            logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans} ({self.Log_Text_EM001_str[self.sprache]})')
            ## Antwort an den Leerzeichen trennen:
            liste = ans.split(' ')

            # Zuweisung:
            ## Wenn nur b'' ankommt:
            if liste == [''] or len(liste) != 29:
                liste = []
                for n in range(0,29,1):
                    liste.append(m.nan)

            ## Werte zuweisen:
            self.value_name['TC1_T']        = liste[2]    
            self.value_name['TC2_T']        = liste[3]       
            self.value_name['PT1_T']        = liste[4]   
            self.value_name['PT2_T']        = liste[5]   
            self.value_name['Pyro_T']       = liste[6]                 
            self.value_name['PID_Out']      = liste[7]  
            self.value_name['PID_P']        = liste[28]       
            self.value_name['PID_I']        = liste[27]   
            self.value_name['PID_D']        = liste[15]   
            self.value_name['PID_In']       = liste[20]  
            self.value_name['PID_In_M']     = liste[21]
            self.value_name['K_weight']     = liste[22] 
            self.value_name['K_weight_M']   = liste[17]  
            self.value_name['K_d']          = liste[18]
 
        except Exception as e:
            logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_65_str[self.sprache]}")

        #++++++++++++++++++++++++++++++++++++++++++
        # Funktions-Dauer aufnehmen:
        #++++++++++++++++++++++++++++++++++++++++++
        timediff = (datetime.datetime.now(datetime.timezone.utc).astimezone() - ak_time).total_seconds()  
        if self.Log_WriteReadTime:
            logger.info(f"{self.device_name} - {self.Log_Time_r[self.sprache]} {timediff} {self.Log_Time_wr[self.sprache]}")

        return self.value_name

    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung des Gerätes Educrys Monitoring. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
        if not self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_51_str[self.sprache]}')
            logger.info(f"{self.device_name} - {self.Text_51_str[self.sprache]}")
            # Schnittstelle prüfen:
            try: 
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
    
    ###################################################
    # Messdatendatei erstellen und beschrieben:
    ###################################################
    def messdaten_output(self, pfad="./"):
        """Erstelle für das Gerät eine csv-Datei mit den Daten.
            TC1_T, TC2_T, PT1_T, PT2_T, Pyro_T,
            PID_Out, PID_P, PID_I, PID_D, PID_In, PID_In_M,
            K_weight, K_weight_M, K_d      
            
        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        self.filename = f"{pfad}/{self.device_name}.csv"
        units  = "# datetime,s,DEG C,DEG C,DEG C,DEG C,DEG C,ms,ms,ms,ms,DEG C,DEG C,g,g,mm,\n"
        header = "time_abs,time_rel,TC1_Temp,TC2_Temp,PT1_Temp,PT2_Temp,Pyrometer_Temp,PID_Output,PID_P_Anteil,PID_I_Anteil,PID_D_Anteil,PID_Input,PID_Input_gemittelt,Gewischt,Gewischt_gemittelt,Durchmesser,\n"
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