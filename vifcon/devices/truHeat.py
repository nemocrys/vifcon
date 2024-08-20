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
## Allgemein:
import logging
from serial import Serial, SerialException
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


class TruHeat:
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

        ## Aus Config:
        ### Zum Start:
        self.init       = self.config['start']['init']           # Initialisierung
        self.messZeit   = self.config['start']["readTime"]       # Auslesezeit
        self.adress     = self.config['start']['ad']             # Generatoradresse
        self.wdT        = self.config['start']['watchdog_Time']  # Watchdog-Zeit in ms
        self.Delay_sT   = self.config['start']['send_Delay']     # Sende Delay in ms

        ## Werte Dictionary:
        self.value_name = {'IWP': 0, 'IWU': 0, 'IWI': 0, 'IWf': 0, 'SWP': 0, 'SWU': 0, 'SWI': 0}

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

        ## Ablaufdatei:
        self.Text_51_str        = ['Initialisierung!',                                                                      'Initialization!']
        self.Text_52_str        = ['Initialisierung Fehlgeschlagen!',                                                       'Initialization Failed!']
        self.Text_53_str        = ['Wert wurde angenommen (ACK)!',                                                          'Value was accepted (ACK)!']
        self.Text_54_str        = ['Wert wurde nicht angenommen (NAK)!',                                                    'Value was not accepted (NAK)!']
        self.Text_55_str        = ['Senden fehlgeschlagen (Keine Antwort)!',                                                'Sending failed (no response)!']

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

    ##########################################
    # Schnittstelle (Schreiben):
    ##########################################
    def write(self, write_Okay, write_value):
        ''' Schreiben der übergebenden Werte, wenn der richtige Knopf betätigt wurde!

        Args:
            write_Okay (dict):  beinhaltet Boolsche Werte für das was beschrieben werden soll!
            write_value (dict): beinhaltet die Werte die geschrieben werden sollen
        '''

        # Sollwert:
        sollwert = write_value['Sollwert']      # in eine Zahl umgewandelter Wert (Float)

        # Schreiben:
        for auswahl in write_Okay:
            if write_Okay[auswahl] and auswahl == 'Soll-Leistung':
                self.write_read_answer(self.wbefSP, sollwert, self.resP, self.umP,  '010')
                write_Okay[auswahl] = False
            elif write_Okay[auswahl] and auswahl == 'Soll-Spannung':
                self.write_read_answer(self.wbefSU, sollwert, self.resU, self.umU, '010')
                write_Okay[auswahl] = False
            elif write_Okay[auswahl] and auswahl == 'Soll-Strom':
                self.write_read_answer(self.wbefSI, sollwert, self.resI, self.umI, '010')
                write_Okay[auswahl] = False
            elif write_Okay[auswahl] and auswahl == 'Ein':
                self.write_read_answer(self.wEin, 0, 0, 0, '000')
                write_Okay[auswahl] = False
            elif write_Okay[auswahl] and auswahl == 'Aus':
                self.write_read_answer(self.wAus, 0, 0, 0, '000')
                write_Okay[auswahl] = False
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
        while while_n != 10:
            ans_list = []
            ## Senden
            try:
                for n in write_list:
                    self.serial.write(bytearray.fromhex(n))
                    #logging.debug(f"{self.device_name} - Sende das Hexadezimal Zeichen: {n}")
            except Exception as e:
                logger.warning(f"{self.device_name} - {self.Log_Text_76_str[self.sprache]}")
                logger.exception(f"{self.device_name} - {self.Log_Text_77_str[self.sprache]}")

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

        if while_n == 10:
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
        while n != 10:
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
        if not n == 10:
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
            value = -1                                          
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
            self.value_name['IWP'] = self.read_send(self.rbefIP, 2, self.resP, self.umP)    # Einheit: kW
            # Lese Ist-Spannung:
            logger.debug(f"{self.device_name} - {self.Log_Text_106_str[self.sprache]}")
            self.value_name['IWU'] = self.read_send(self.rbefIU, 2, self.resU, self.umU)    # Einheit: V 
            # Lese Ist-Strom:
            logger.debug(f"{self.device_name} - {self.Log_Text_107_str[self.sprache]}")
            self.value_name['IWI'] = self.read_send(self.rbefII, 2, self.resI, self.umI)    # Einheit: A
            # Lese Ist-Frequenz:
            logger.debug(f"{self.device_name} - {self.Log_Text_108_str[self.sprache]}")
            self.value_name['IWf'] = self.read_send(self.rbefIf, 2, self.resf, self.umf)    # Einheit: kHz
            # Lese Soll-Leistung:
            logger.debug(f"{self.device_name} - {self.Log_Text_109_str[self.sprache]}")
            self.value_name['SWP'] = self.read_send(self.rbefSP, 2, self.resP, self.umP)    # Einheit: kW
            # Lese Soll-Spannung:
            logger.debug(f"{self.device_name} - {self.Log_Text_110_str[self.sprache]}")
            self.value_name['SWU'] = self.read_send(self.rbefSU, 2, self.resU, self.umU)    # Einheit: V
            # Lese Soll-Leistung:
            logger.debug(f"{self.device_name} - {self.Log_Text_111_str[self.sprache]}")
            self.value_name['SWI'] = self.read_send(self.rbefSI, 2, self.resI, self.umI)    # Einheit: A
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
        watchdog = self.read_send('91', 2, 1, 1, True)
        logger.info(f"{self.device_name} - {self.Log_Text_115_str[self.sprache]} {watchdog} {self.Log_Text_114_str[self.sprache]}")
        if self.wdT != watchdog:
            logger.warning(f"{self.device_name} - {self.Log_Text_116_str[self.sprache]}")
        ## Software Version:
        soft_version = self.read_send('C6', 11, 1, 1, False)
        logger.info(f"{self.device_name} - {self.Log_Text_117_str[self.sprache]} {soft_version}")
        ## Seriennummer Modul:
        snr = self.read_send('C7', 4, 1, 1)
        logger.info(f"{self.device_name} - {self.Log_Text_118_str[self.sprache]} {int(snr)}")
        ## Netzteil-Typ:
        netzTyp = self.read_send('80', 21, 1, 1, False)
        logger.info(f"{self.device_name} - {self.Log_Text_119_str[self.sprache]} {netzTyp}")
        ## SIMIN und SUMIN:
        simin = self.read_send('D0',2, self.resI, self.umI)
        logger.info(f"{self.device_name} - {self.Log_Text_120_str[self.sprache]} {simin}")
        sumin = self.read_send('D2',2, self.resU, self.umU)
        logger.info(f"{self.device_name} - {self.Log_Text_121_str[self.sprache]} {sumin}")
        ## Maximale Leistung (und Strom):
        max_P = self.read_send('82',4, 100, self.umP)
        logger.info(f"{self.device_name} - {self.Log_Text_122_str[self.sprache]} {max_P} {self.Log_Text_123_str[self.sprache]}")
        ## Maximale Spannung:
        max_U = self.read_send('CA',2, self.resU, self.umU)
        logger.info(f"{self.device_name} - {self.Log_Text_124_str[self.sprache]} {max_U} {self.Log_Text_125_str[self.sprache]}")
        ## Maximaler Strom (Teil vom Kombi-Befehl):
        max_I = self.read_send('CB',2, self.resI, self.umI)
        logger.info(f"{self.device_name} - {self.Log_Text_126_str[self.sprache]} {max_I} {self.Log_Text_127_str[self.sprache]}")
        ## Aktives Interface:
        interface = {0:'Bedienpanel', 1:'RS-232' , 2:'PROFIBUS' , 3:'CANopen' , 4:'Terminal' , 5:'AD-Schnittstelle' , 6:'Regulus (Temp)', 7:'User 1' , 8:'User 2' , 9:'User 3' , 10:'User 4'}
        ak_intF = self.read_send('9B',1, 1, 1)
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
        self.filename = f"{pfad}/{self.device_name}.csv"
        units = "# datetime,s,kW,V,A,kHz,kW,V,A,\n"
        #scaling = f"# -,-,{self.}"
        header = "time_abs,time_rel,Ist-Leistung,Ist-Spannung,Ist-Strom,Ist-Frequenz,Soll-Leistung,Soll-Spannung,Soll-Strom,\n"
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
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''