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


class NemoAchseRot:
    def __init__(self, sprache, config, config_dat, com_dict, test, neustart, add_Ablauf_function, name="Nemo-Achse-Rotation", typ = 'Antrieb'):
        """ Erstelle Nemo-Achse Rot Schnittstelle. Bereite Messwertaufnahme und Daten senden vor.

        Args:
            sprache (int):                      Sprache des Programms (GUI, Files)
            config (dict):                      device configuration (as defined in config.yml in the devices-section).
            com_dict (dict):                    Dictionary mit den anderen Ports der PI-Achsen
            config_dat (string):                Datei-Name der Config-Datei
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
        self.value_name = {'IWv': 0, 'IWw':0, 'SWv': 0, 'Status': 0}

        ## Aus Config:
        ### Zum Start:
        self.init = self.config['start']['init']                                # Initialisierung
        self.messZeit = self.config['start']["readTime"]                        # Auslesezeit
        self.v_invert = self.config['start']['invert']                          # Invertierung bei True der Geschwindigkeit
        ### Parameter:
        self.nKS = self.config['parameter']['nKS_Aus']                          # Nachkommerstellen
        self.vF_ist   = self.config['parameter']['Vorfaktor_Ist']               # Vorfaktor Istgeschwindigkeit
        self.vF_soll  = self.config['parameter']['Vorfaktor_Soll']              # Vorfaktor Istgeschwindigkeit
        ### Register:
        self.reg_cw = self.config['register']['cw']                             # Fahre hoch Coil Rergister
        self.reg_ccw = self.config['register']['ccw']                           # Fahre runter Coil Register
        self.reg_s = self.config['register']['stopp']                           # Stoppe Coil Register
        self.start_Lese_Register = self.config['register']['lese_st_Reg']       # Input Register Start-Register
        self.start_write_v = self.config['register']['write_v_Reg']             # Holding Register Start-Register
        self.Status_Reg = self.config['register']['statusReg']                  # Startregister für Status
        ### Limits:
        self.oGw = self.config["limits"]['maxWinkel']
        self.uGw = self.config["limits"]['minWinkel']

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
        self.Log_Text_67_str    = ['Das Gerät konnte nicht initialisiert werden!',                                          'The device could not be initialized!']
        self.Log_Text_69_str    = ['Fehler Grund (Initialisierung):',                                                       'Error reason (initialization):']
        self.Log_Text_70_str    = ['Initialisierung aufheben! Gerät abtrennen!',                                            'Cancel initialization! Disconnect device!']
        self.Log_Text_71_str    = ['Erstelle die Messdatei mit dem Pfad:',                                                  'Create the measurement file with the path:']
        self.Log_Text_72_str    = ['Keine Messdatenerfassung aktiv!',                                                       'No measurement data recording active!']
        self.Log_Text_76_str    = ['Das Senden an das Gerät ist fehlgeschlagen.',                                           'Sending to the device failed.']
        self.Log_Text_77_str    = ['Fehler Grund (Senden):',                                                                'Error reason (send):']
        self.Log_Text_169_str   = ['Kein True als Rückmeldung!',                                                            'No true feedback!']
        self.Log_Text_170_str   = ['Das Senden an das Gerät ist fehlgeschlagen. Stopp gescheitert!',                        'Sending to the device failed. Stop failed!']
        self.Log_Text_171_str   = ['Fehler Grund (Stopp Senden):',                                                          'Error reason (stop sending):']
        self.Log_Text_172_str   = ['Befehl wurde nicht akzeptiert (Geschwindigkeit)!',                                      'Command was not accepted (speed)!']
        self.Log_Text_173_str   = ['Das Senden der Geschwindigkeit an das Gerät ist fehlgeschlagen!',                       'Sending speed to device failed!']
        self.Log_Text_174_str   = ['Fehler Grund (Sende Geschwindigkeit):',                                                 'Error reason (send speed):']
        self.Log_Text_178_str   = ['Befehl wurde nicht akzeptiert (CW)!',                                                   'Command was not accepted (CW)!']
        self.Log_Text_179_str   = ['Befehl wurde nicht akzeptiert (CCW)!',                                                  'Command was not accepted (CCW)!']
        self.Log_Text_180_str   = ['Das Gerät hat keine Startwerte zum Auslesen!',                                          'The device has no start values to read out!']
        self.Log_Text_207_str   = ['Konfiguration aktualisieren (Nullpunkt setzen NemoRot):',                               'Update configuration (Define-Home NemoRot):']
        self.Log_Text_212_str   = ['Startwert überschreitet Maximum Limit! Setze Startwert auf Maximum Limit!',             'Starting value exceeds maximum limit! Set starting value to Maximum Limit!']
        self.Log_Text_213_str   = ['Startwert überschreitet Minimum Limit! Setze Startwert auf Minimum Limit!',             'Starting value exceeds minimum limit! Set starting value to minimum limit!']
        self.Log_Text_214_str   = ['Antriebs Startwert:',                                                                   'Drive start value:']
        self.Log_Text_215_str   = ['°',                                                                                      '°']
        self.Log_Text_219_str   = ['Knopf kann nicht ausgeführt werden da Limit erreicht!',                                 'Button cannot be executed because limit has been reached!']         
        self.Log_Text_220_str   = ['Maximum Limit erreicht! (CW)!',                                                         'Maximum limit reached! (CW)!']
        self.Log_Text_221_str   = ['Minimum Limit erreicht! (CCW)!',                                                        'Minimum limit reached! (CCW)!']
        self.Log_Text_249_str   = ['CW',                                                                                    'CW']
        self.Log_Text_250_str   = ['CCW',                                                                                   'CCW']
        self.Log_Text_Info_1    = ['Der Vorfaktor für die Istgeschwindigkeit beträgt:',                                     'The prefactor for the actual speed is:']
        self.Log_Text_Info_2    = ['Der Vorfaktor für die Sollgeschwindigkeit beträgt:',                                    'The prefactor for the target speed is:']
        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                       'Initialization Failed!']
        self.Text_61_str        = ['Das Senden ist fehlgeschlagen!',                                                        'Sending failed!']
        self.Text_62_str        = ['Achse wurde erfolgreich angehalten!',                                                   'Axis was stopped successfully!']
        self.Text_67_str        = ['Nach',                                                                                  'After']
        self.Text_68_str        = ['Versuchen!',                                                                            'Attempts!']
        self.Text_69_str        = ['Geschwindigkeit erfolgreich gesendet!',                                                 'Speed sent successfully!']
        self.Text_70_str        = ['Befehl sende Geschwindigkeit fehlgeschlagen!',                                          'Command send speed failed!']
        self.Text_71_str        = ['Befehl Clock Wise fehlgeschlagen!',                                                     'Clock Wise command failed!']
        self.Text_72_str        = ['Befehl Clock Wise erfolgreich gesendet!',                                               'Clock Wise command sent successfully!']
        self.Text_73_str        = ['Befehl Counter Clock Wise fehlgeschlagen!',                                             'Counter Clock Wise command failed!']
        self.Text_74_str        = ['Befehl Counter Clock Wise erfolgreich gesendet!',                                       'Counter Clock Wise command sent successfully!']

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

        # Kontinuierlische Rotation:
        if write_value['EndRot']:
            self.CW_End = False
            self.CCW_End = False

        # Update Limit:
        if write_Okay['Update Limit']:
            self.oGw = write_value['Limits'][0]
            self.uGw = write_value['Limits'][1]
            write_Okay['Limit'] = False

        # Define Home:
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

        # Position berechnen und Limits beachten:
        if self.fahre:
            # Bestimmung der Zeit zum Start:
            self.ak_Time = datetime.datetime.now(datetime.timezone.utc).astimezone() # Zyklus Ende
            timediff = (
                self.ak_Time - self.start_Time
            ).total_seconds()  
            #print(f'Zeit: {timediff}')
            self.start_Time = datetime.datetime.now(datetime.timezone.utc).astimezone() # Neuer zyklus
            # Berechne Winkel:
            ans = self.serial.read_input_registers(self.start_Lese_Register, 2)         # vIst ist das erste Register!
            logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans}')
            self.ak_speed = self.umwandeln_Float(ans)[0] * self.vF_ist                  # Beachtung eines Vorfaktors!
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

        # Sende Stopp:
        if write_Okay['Stopp']:
            self.stopp()
            # Rücksetzen aller Bewegungen:
            write_Okay['Stopp'] = False
            write_Okay['CW'] = False
            write_Okay['CCW'] = False 
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
                        if write_Okay['CW'] and not self.CW_End:
                            ans = self.serial.write_single_coil(self.reg_cw, True)
                            if not ans:
                                logger.warning(f'{self.device_name} - {self.Log_Text_178_str[self.sprache]}')
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_71_str[self.sprache]}') 
                            else:
                                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_72_str[self.sprache]}')  
                                # Positionsbestimmung:
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
                                # Positionsbestimmung:
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
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_67_str[self.sprache]}.")
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
        units = "# datetime,s,1/min,°,1/min,\n"
        header = "time_abs,time_rel,Geschwindigkeit,Winkel,Soll-Geschwindigkeit,\n"
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
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''       