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
        ### Schnittstelle:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Loop = self.config['serial-loop-read']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} serial-loop-read {self.Log_Pfad_conf_5[self.sprache]} 10')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Loop = 10

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
        ### While-Loop:
        if not type(self.Loop) == int or not self.Loop >= 1:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} serial-loop-read - {self.Log_Pfad_conf_2[self.sprache]} Integer (>=1) - {self.Log_Pfad_conf_3[self.sprache]} 10 - {self.Log_Pfad_conf_8[self.sprache]} {self.Loop}')
            self.Loop = 10

        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging: ##################################################################################################################################################################################################################################################################################
        self.Log_Text_60_str    = ['Erstelle das Schnittstellen Objekt!',                                                                                                           'Create the interface object!']
        self.Log_Text_61_str    = ['Aufbau Schnittstelle des Geräts fehlgeschlagen! Programm wird beendet!',                                                                        'Setup of the device interface failed! Program will end!']
        self.Log_Text_62_str    = ['Fehler Grund (Schnittstellen Aufbau):',                                                                                                         'Error reason (interface structure):']
        self.Log_Text_63_str    = ['Antwort Messwerte:',                                                                                                                            'Answer measurements:']
        self.Log_Text_64_str    = ['Das Gerät konnte nicht ausgelesen werden.',                                                                                                     'The device could not be read.']
        self.Log_Text_65_str    = ['Fehler Grund (Gerät Auslesen):',                                                                                                                'Error reason (reading device):']
        self.Log_Text_67_str    = ['Messwerte Umgewandelt - Messwert',                                                                                                              'Measured Values Converted - Measured Value']
        self.Log_Text_68_str    = ['Das Gerät konnte nicht initialisiert werden!',                                                                                                  'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                                                                               'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                                                                                    'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                                                                          'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                                                                               'No measurement data recording active!']
        self.Log_Text_136_str   = ['Fehler Grund (Auslesen):',                                                                                                                      'Error reason (reading):']
        self.Log_Text_Port_1    = ['Verbindungsfehler:',                                                                                                                            'Connection error:']
        self.Log_Text_Port_2    = ['Der Test für den Verbindungsaufbau ist fehlgeschlagen!',                                                                                        'The connection establishment test failed!']
        self.Log_Text_Port_3    = ['Antwort der Test-Abfrage war None. Bearbeitung nicht möglich!',                                                                                 'The answer to the test query was None. Processing not possible!']
        self.Log_Text_Port_4    = ['Bei der Werte-Umwandlung ist ein Fehler aufgetreten!',                                                                                          'An error occurred during value conversion!']
        self.Log_Text_Port_5    = ['Fehlerbeschreibung:',                                                                                                                           'Error description:']
        self.Log_Test_Ex_1      = ['Der Variablen-Typ der Größe',                                                                                                                   'The variable type of size']
        self.Log_Test_Ex_2      = ['ist nicht Float! Setze Nan ein! Fehlerhafter Wert:',                                                                                            'is not Float! Insert Nan! Incorrect value:']
        self.Log_Time_wr        = ['s gedauert!',                                                                                                                                   's lasted!']   
        self.Log_Time_r         = ['Die read-Funktion hat',                                                                                                                         'The read function has']  
        self.Log_Text_EM001_str = ['bereinigt',                                                                                                                                     'adjusted']
        self.Log_Edu_3_str      = ['Antwort Falsch!',                                                                                                                               'Answer False!']
        self.Log_Edu_4_str      = ['Wiederhole Antwort lesen, bevor neu Senden!',                                                                                                   'Please read the answer again before sending again!']
        self.Log_Edu_5_str      = ['Sende Befehl erneut!',                                                                                                                          'Resend command!']
        self.Log_Edu_6_str      = ['Das Senden an Educrys hat keine richtige Antwort erbracht!',                                                                                    'Sending to Educrys did not produce a correct response!']
        self.Log_Edu_7_str      = ['Antwort des Geräts auf !:',                                                                                                                     'Device response to !:']
        self.Log_Edu_18_str     = ['Die Antwort des Lese-Befehls beinhaltet weniger als 29 Werte. Dies wird als Fehler gewertet!! Nan-Werte werden eingetragen. Länge Liste:',      'The response of the read command contains less than 29 values. This is considered an error!! Nan values ​​are entered. List length:']
        self.Log_Edu_19_str     = ['Start- und Endzeichen stimmen nicht!',                                                                                                          'Start and end characters are wrong!']
        self.Log_Edu_20_str     = ['Leerer String!',                                                                                                                                'Empty string!']
        ## Ablaufdatei: ##############################################################################################################################################################################################################################################################################
        self.Text_51_str        = ['Initialisierung!',                                                                                                                              'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                                                                               'Initialization Failed!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                                                                                'Sending failed!']
        self.Text_Edu_1_str     = ['Befehl',                                                                                                                                        'Command']
        self.Text_Edu_2_str     = ['erfolgreich gesendet!',                                                                                                                         'sent successfully!']

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
        # Time Check 1:
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

        # Variablen:
        n               = 0
        listen_Error    = False
        error           = False 
        
        try:
            # Lese alle Monitoringswerte aus (Mehr als gebraucht!) - 29 Werte
            ## Besteht aus vielen Werten im Format *Wert_1 Wert_2#
            self.serial.write(('!\r').encode())
            ## Etwas Zeit lassen:
            time.sleep(0.1)
            
            # Lese Antwort:
            ''' 
            1. read_out_AZ()    - liest bis # -> Eigene Funktion! Liest Zeichen für Zeichen!
            2. decode()         - Bytearray umwandeln
            3. strip()          - Leerzeichen am Anfang und Ende entfernen
            4. replace()        - *, # und Abschlusszeichen entfernen

            Antwort-Beispiel: 5212.780 794.726 24.58 -99.00 22.87 -242.02 -99.00 0.00 0 0 0 0.00 0.000000 0 0 1000.00 0.00 22.87 22.85 20.00 -569.24 1000.00 -0.00 200.00 0.00 0.00 0.00 -0.00 0.00
            '''
            ans = self.read_out_AZ()
            ans = ans.replace('\r','').replace('\n','').strip()
            logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')

            ## Antwort prüfen:
            ### Fehlerfall 1 - End- und Startzeichen richtig:
            start_end = True
            if ans != '':
                if ans[0] == '*' and ans[-1] == '#':    
                    ans = ans.replace('*', '').replace('#','').replace('#','').replace('\r','').strip()   
                    logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans} ({self.Log_Text_EM001_str[self.sprache]})')
                else:                                   
                    ans         = ''
                    start_end   = False  

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
            else:
                liste = []
                for i in range(0,29,1):
                    liste.append(m.nan)
 
            ## Werte zuweisen:
            self.value_name['TC1_T']        = round(float(liste[2] ), self.nKS)   
            self.value_name['TC2_T']        = round(float(liste[3] ), self.nKS)      
            self.value_name['PT1_T']        = round(float(liste[4] ), self.nKS)  
            self.value_name['PT2_T']        = round(float(liste[5] ), self.nKS)  
            self.value_name['Pyro_T']       = round(float(liste[6] ), self.nKS)                
            self.value_name['PID_Out']      = round(float(liste[7] ), self.nKS) 
            self.value_name['PID_P']        = round(float(liste[28]), self.nKS)       
            self.value_name['PID_I']        = round(float(liste[27]), self.nKS)   
            self.value_name['PID_D']        = round(float(liste[15]), self.nKS)   
            self.value_name['PID_In']       = round(float(liste[20]), self.nKS)  
            self.value_name['PID_In_M']     = round(float(liste[21]), self.nKS)
            self.value_name['K_weight']     = round(float(liste[22]), self.nKS) 
            self.value_name['K_weight_M']   = round(float(liste[17]), self.nKS)  
            self.value_name['K_d']          = round(float(liste[18]), self.nKS)
 
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
            #ans = self.serial.read_until()
            #logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')
            #ans = ans.decode().strip().replace('*', '').replace('#','').replace('\r\n','')
'''

    # def read_out(self, Anz):
    #     '''Liest eine bestimmte Anzahl von Zeichen aus, verbindet diese und gibt einen String zurück!
        
    #     Args:
    #         Anz (int):      Anzahl der maximal zu lesenden Zeichen
        
    #     Return:
    #         ans_join (Str): Zurückgegebener String (Bei Fehler Leerer String)
    #     '''
    #     try:
    #         ans_list = []                                   # Leere Liste
    #         i = 0                                           # Kontroll Variable (Zeichen)
    #         while 1:                                        # Endlosschleife
    #             z = self.serial.read()                      # Lese Zeichen
    #             if z != '': ans_list.append(z.decode())     # Wenn nicht Leer, dann füge an Liste
    #             if z == b'\n':  break                       # Wenn \n (Newline) beende Endlosschleife
    #             if i >= Anz:    break                       # Wenn Anzahl Zeichen überschritten oder gleich, dann Beende Endlosschleife
    #             i += 1                                      # Erhöhe Zählvariable
    #         ans_join = ''.join(ans_list)                    # Verbinde die Liste zu einem String
    #     except Exception as e:
    #         logger.warning(f"{self.device_name} - {self.Log_Text_64_str[self.sprache]}")
    #         logger.exception(f"{self.device_name} - {self.Log_Text_136_str[self.sprache]}")
    #         ans_join = ''

    #     return ans_join