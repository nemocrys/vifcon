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
## Allgemein:
import yaml
import logging
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import datetime

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


class NemoAchseLin:
    def __init__(self, sprache, config, config_dat, com_dict, test, neustart, add_Ablauf_function, name="Nemo-Achse-Linear", typ = 'Antrieb'):
        """ Erstelle Nemo-Achse Lin Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      device configuration (as defined in config.yml in the devices-section).
            config_dat (string):                Datei-Name der Config-Datei
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
        self.config_dat = config_dat
        self.neustart = neustart
        self.add_Text_To_Ablauf_Datei = add_Ablauf_function
        self.device_name = name
        self.typ = typ

        ## Andere:
        self.value_name = {'IWs': 0, 'IWsd':0, 'IWv': 0, 'SWv': 0, 'SWs':0, 'oGs':0, 'uGs': 0, 'Status': 0}

        ## Aus Config:
        ### Zum Start:
        self.init = self.config['start']['init']                                # Initialisierung
        self.messZeit = self.config['start']["readTime"]                        # Auslesezeit
        self.v_invert = self.config['start']['invert']                          # Invertierung bei True der Geschwindigkeit
        ### Parameter:
        self.nKS      = self.config['parameter']['nKS_Aus']                     # Nachkommerstellen
        self.vF_ist   = self.config['parameter']['Vorfaktor_Ist']               # Vorfaktor Istgeschwindigkeit
        self.vF_soll  = self.config['parameter']['Vorfaktor_Soll']              # Vorfaktor Istgeschwindigkeit
        ### Register:
        self.reg_h = self.config['register']['hoch']                            # Fahre hoch Coil Rergister
        self.reg_r = self.config['register']['runter']                          # Fahre runter Coil Register
        self.reg_s = self.config['register']['stopp']                           # Stoppe Coil Register
        self.start_Lese_Register = self.config['register']['lese_st_Reg']       # Input Register Start-Register
        self.start_write_v = self.config['register']['write_v_Reg']             # Holding Register Start-Register
        self.reg_PLim = self.config['register']['posLimReg']                    # Startregister für Limits
        self.Status_Reg = self.config['register']['statusReg']                  # Startregister für Status
        ### Limits:
        self.oGs = self.config["limits"]['maxPos']
        self.uGs = self.config["limits"]['minPos']

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

        # Update Limit:
        if write_Okay['Update Limit']:
            self.oGs = write_value['Limits'][0]
            self.uGs = write_value['Limits'][1]
            write_Okay['Limit'] = False

        # Define Home:
        if write_Okay['Define Home']:
            # Setze Position auf Null:
            self.akIWs = 0

            # Grenzen Updaten:
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

        # Position berechnen und Limits beachten:
        if self.fahre:
            # Bestimmung der Zeit zum Start:
            self.ak_Time = datetime.datetime.now(datetime.timezone.utc).astimezone()    # Zyklus Ende
            timediff = (
                self.ak_Time - self.start_Time
            ).total_seconds()  
            self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone() # Neuer zyklus
            # Berechne Weg:
            ans = self.serial.read_input_registers(self.start_Lese_Register, 2)         # vIst ist das erste Register!
            logger.debug(f'{self.device_name} - {self.Log_Text_166_str[self.sprache]} {ans}')
            self.ak_speed = self.umwandeln_Float(ans)[0] * self.vF_ist                  # Istwert kann negativ sein. Beachtung eines Vorfaktors!
            pos = self.umFak * abs(self.ak_speed) * timediff 
            if self.rechne == 'Add':
                self.akIWs = self.akIWs + pos
            elif self.rechne == 'Sub':
                self.akIWs = self.akIWs - pos
            # Kontrolliere die Grenzen:
            if self.akIWs >= self.oGs and not self.Auf_End:
                self.Auf_End = True
                logger.warning(f'{self.device_name} - {self.Log_Text_217_str[self.sprache]}')
                write_Okay['Stopp'] = True
            if self.akIWs <= self.uGs and not self.Ab_End:
                self.Ab_End = True
                logger.warning(f'{self.device_name} - {self.Log_Text_218_str[self.sprache]}')
                write_Okay['Stopp'] = True
            if self.akIWs > self.uGs and self.akIWs < self.oGs:
                self.Auf_End = False
                self.Ab_End = False

        # Sende Stopp:
        if write_Okay['Stopp']:
            self.stopp()
            # Rücksetzen aller Bewegungen:
            write_Okay['Stopp'] = False
            write_Okay['Hoch'] = False
            write_Okay['Runter'] = False
            write_Okay['Send'] = False
            self.fahre = False    
            self.start_Time = 0                                      
        # Schreiben, wenn nicht Stopp:          
        else:
            try:
                if write_Okay['Send']:
                    ans_v = self.write_v(write_value['Speed'])      
                    write_Okay['Send'] = False
                    if ans_v:                                           # Bewegung nur wenn Senden der Geschwindigkeit erfolgreich!
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
        
        return self.value_name

    def umwandeln_Float(self, int_Byte_liste):
        ''' Wandelt die Register-Werte in Zahlen um.

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
        ''' Initialisierung des Gerätes Nemo Hub. Solange die Variable init auf False steht, kann das Gerät initialisiert werden! '''
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
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = "# datetime,s,mm,mm/min,mm/min,mm,mm,mm\n"
        header = "time_abs,time_rel,Position,Geschwindigkeit,Soll-Geschwindigkeit,Soll-Position,max.Pos.,min.Pos,\n"
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
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''        
