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


class NemoGase:
    def __init__(self, sprache, config, com_dict, test, Log_WriteReadTime, add_Ablauf_function, name="nemoGase", typ = 'Monitoring'):
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
        self.value_name = {'MFC24': 0, 'MFC25': 0, 'MFC26': 0, 'MFC27': 0, 'DM21': 0, 'PP21': 0, 'PP22': 0, 'PP21Status': 0, 'PP22Status': 0, 'PP22I': 0, 
                           'PP22mPtS': 0, 'MV1_I': 0, 'MV1_S': 0, 'MV1_VS': 0, 'MV1_SG': 0, 'MV1Status': 0,
                           'MFC24_S': 0, 'MFC24_FM': 0, 'MFC24Status': 0, 
                           'MFC25_S': 0, 'MFC25_FM': 0, 'MFC25Status': 0,
                           'MFC26_S': 0, 'MFC26_FM': 0, 'MFC26Status': 0,
                           'MFC27_S': 0, 'MFC27_FM': 0, 'MFC27Status': 0,
                           'V1Status': 0, 'V2Status': 0, 'V3Status': 0, 'V4Status': 0, 
                           'V5Status': 0, 'V6Status': 0, 'V7Status': 0, 'V17Status': 0, 
                           'KWKDF_1': 0, 'KWKDF_2': 0, 'KWKDF_3': 0, 'KWKDF_4': 0, 'KWKDF_5': 0, 'KWKDF_6': 0, 'KWKDF_7': 0, 'KWKDF_8': 0, 'KWKDF_9': 0,
                           'KWKT_1': 0, 'KWKT_2': 0, 'KWKT_3': 0, 'KWKT_4': 0, 'KWKT_5': 0, 'KWKT_6': 0, 'KWKT_7': 0, 'KWKT_8': 0, 'KWKT_9': 0,
                           'KWK5_In': 0, 'KWK5_Out': 0, 'KWK5_diff': 0,
                           'KWK46_In': 0, 'KWK46_Out': 0, 'KWK46_diff': 0,
                           'ASTO': 0, 'ASTM': 0, 'ASTU': 0, 'ASBMStatus': 0, 'ASStatus':0,
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
        ### Übergeordnet:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.Anlage = self.config['nemo-Version']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} nemo-Version {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Anlage = 1
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
        ### Register:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.start_Lese_Register_VGP_1 = self.config['register']['lese_st_Reg_VGP_1']       # Input Register Start-Register für Vakkum, Gas und Pumpen Teil 1        
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg_VGP_1 {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.start_Lese_Register_VGP_2 = self.config['register']['lese_st_Reg_VGP_2']       # Input Register Start-Register für Vakkum, Gas und Pumpen Teil 2
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg_VGP_2 {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.start_Lese_Register_K = self.config['register']['lese_st_Reg_K']       # Input Register Start-Register für Kühlung
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg_K {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        #//////////////////////////////////////////////////////////////////////
        try: self.start_Lese_Register_AS = self.config['register']['lese_st_Reg_AS']       # Input Register Start-Register für Anlagensicherheit
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} register|lese_st_Reg_AS {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            exit()

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
        ### Register Lese VGP 1:
        if not type(self.start_Lese_Register_VGP_1) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg_VGP_1 - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.start_Lese_Register_VGP_1)}')
            exit()
        ### Register Lese VGP 2:
        if not type(self.start_Lese_Register_VGP_2) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg_VGP_2 - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.start_Lese_Register_VGP_2)}')
            exit()
        ### Register Lese Kühlung:
        if not type(self.start_Lese_Register_K) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg_K - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.start_Lese_Register_K)}')
            exit()
        ### Register Lese Anlagensicherheit:
        if not type(self.start_Lese_Register_AS) == int:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} lese_st_Reg_AS - {self.Log_Pfad_conf_2_1[self.sprache]} [int] - {self.Log_Pfad_conf_5_1[self.sprache].replace("; ", "")} - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.start_Lese_Register_AS)}')
            exit()
        ### Anlagen-Version:
        if not self.Anlage in [1, 2]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nemo-Version - {self.Log_Pfad_conf_2[self.sprache]} [1, 2] - {self.Log_Pfad_conf_3[self.sprache]} 1')
            self.Anlage = 1

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
        self.Log_Text_66_str    = ['Antwort Register Integer:',                                                 'Response Register Integer:']
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
        self.Bezeichnung_1      = ['Vakuum/Gas und Pumpen',                                                     'Vacuum/Gas and Pumps']
        self.Bezeichnung_2      = ['Kühlung',                                                                   'Cooling']
        self.Bezeichnung_3      = ['Anlagensicherheit',                                                         'System safety']
        self.Log_Time_wr        = ['s gedauert!',                                                               's lasted!']   
        self.Log_Time_r         = ['Die read-Funktion hat',                                                     'The read function has']  
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
                    self.serial = ModbusClient(**config["serial-interface"])
                else:
                    self.serial = com_dict[com_ak]
        except Exception as e:
            self.serial = SerialMock()
            logger.warning(f"{self.device_name} - {self.Log_Text_61_str[self.sprache]}")
            logger.exception(f"{self.device_name} - {self.Log_Text_62_str[self.sprache]}")
            exit()
        
        if self.init and not test:
            Meldungen = False
            for n in range(0,5,1):
                if not self.serial.is_open:
                    self.Test_Connection(Meldungen)
                if n == 4:
                    Meldungen = True
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
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

        try:
            # Auslese-Teil 1 - Vakuum, Gase und Pumpen:
            # Lese: MFC24, MFC25, MFC26,  MFC27, DM21, PP21, PP22, PP21 Status, PP22 Status, PP22 Drehzahl: 
            # Notiz:    8 Gleitkommazahlen
            #           2 Statuswörter          --> (8 * 2) + 2 = 18 Regsiter
            ans = self.serial.read_input_registers(self.start_Lese_Register_VGP_1, 18)
            logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans} ({self.Bezeichnung_1[self.sprache]} 1)')

            if not ans == None:
                value_1 = self.umwandeln_Float(ans[0:14])   # MFC24, MFC25, MFC26, MFC27, DM21, PP21, PP22,
                value_2 = self.umwandeln_Float(ans[-2:])    # PP22 Drehzahl
            else:
                value_1 = [m.nan, m.nan, m.nan, m.nan, m.nan, m.nan, m.nan] 
                value_2 = [m.nan]
            if not ans == None and type(ans[14]) == int: self.value_name['PP21Status'] = ans[14] 
            else:                                        self.value_name['PP21Status'] = 64
            if not ans == None and type(ans[15]) == int: self.value_name['PP22Status'] = ans[15] 
            else:                                        self.value_name['PP22Status'] = 64

            i = 0
            value_Def = ['MFC24', 'MFC25', 'MFC26', 'MFC27', 'DM21', 'PP21', 'PP22']
            for n in value_1:
                if not type(n) == float:    
                    value_1[i] = m.nan
                    logger.warning(f'{self.Log_Test_Ex_1[self.sprache]} {value_Def[i]} {self.Log_Test_Ex_2[self.sprache]} {n}')
                i += 1 
            
            i = 0
            value_Def = ['PP22I']
            for n in value_2:
                if not type(n) == float:    
                    value_2[i] = m.nan
                    logger.warning(f'{self.Log_Test_Ex_1[self.sprache]} {value_Def[i]} {self.Log_Test_Ex_2[self.sprache]} {n}')
                i += 1

            # Auslese-Teil 2 - Vakuum, Gase und Pumpen:
            if self.Anlage == 2:
                # Lese: MFC24_S, MFC24_FM, MFC25_S, MFC25_FM, MFC26_S, MFC26_FM, MFC27_S, MFC27_FM,
                #       MV1_I, MV1_S, MV1_VS, PP22mPtS, MFC24_RE, MFC24_m, MFC25_RE, MFC25_m,
                #       MFC26_RE, MFC26_m, MFC27_RE, MFC27_m, MV1_RE, MV1_m, MV1_SG, MFC24Status,
                #       MFC25Status, MFC26Status, MFC27Status, MV1Status, V1Status, V2Status,
                #       V3Status, V4Status, V5Status, V6Status, V7Status, V17Status
                # Notiz:    Alle _m und _RE werden noch nicht in die GUI integriert -> Rampen-Werte!
                #           23 Gleitkommazahlen
                #           13 Statuswörter         --> (23 * 2) + 13 = 59 Register
                ans = self.serial.read_input_registers(self.start_Lese_Register_VGP_2, 59)
                logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans} ({self.Bezeichnung_1[self.sprache]} 2)')
                if not ans == None:     value_3 = self.umwandeln_Float(ans[0:46])   
                else:
                    value_3 = []
                    for n in range(0,23,1):
                        value_3.append(m.nan)
                stat_list = ['MFC24Status', 'MFC25Status', 'MFC26Status', 'MFC27Status', 'MV1Status', 'V1Status', 'V2Status', 'V3Status', 'V4Status', 'V5Status', 'V6Status', 'V7Status', 'V17Status']
                for n in range(46, 59, 1):
                    if not ans == None and type(ans[n]) == int: self.value_name[stat_list[n-46]] = ans[n] 
                    else:                                       
                        if not stat_list[n-46][0] == 'V':   self.value_name[stat_list[n-46]] = 64   # Bit 14 wird angespochen
                        else:                               self.value_name[stat_list[n-46]] = 1024 # bei Ventilen wird der Bit 14 genutzt, weshalb der Schnittstellen-Fehler auf dem Bit 3 liegt! 

                # Auslese-Teil 3 - Kühlung:
                # Lese:     KWKDF_1, KWKDF_2, KWKDF_3, KWKDF_4, KWKDF_5, KWKDF_6, KWKDF_7, KWKDF_8, KWKDF_9,
                #           KWKT_1, KWKT_2, KWKT_3, KWKT_4, KWKT_5, KWKT_6, KWKT_7, KWKT_8, KWKT_9,
                #           KWK5_In, KWK5_Out, KWK5_diff, KWK46_In, KWK46_Out, KWK46_diff
                # Notiz:    24 Gleitkommazahlen           --> (24 * 2) = 48 Register     
                ans = self.serial.read_input_registers(self.start_Lese_Register_K, 48)
                logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans} ({self.Bezeichnung_2[self.sprache]})')
                if not ans == None:     value_4 = self.umwandeln_Float(ans)   
                else:
                    value_4 = []
                    for n in range(0,24,1):
                        value_4.append(m.nan)   

                # Auslese-Teil 4 - Anlagensicherheit: 
                # Lese:     ASTO, ASTM, ASTU, ASBMStatus, ASStatus
                # Notiz:    3 Gleitkommazahlen           
                #           2 Statuswörter          --> (3 * 2) + 2 = 8 Register
                ans = self.serial.read_input_registers(self.start_Lese_Register_AS, 8)
                logger.debug(f'{self.device_name} - {self.Log_Text_63_str[self.sprache]} {ans} ({self.Bezeichnung_3[self.sprache]})')
                if not ans == None:     value_5 = self.umwandeln_Float(ans[0:6])   
                else:
                    for n in range(0,3,1):
                        value_5.append(m.nan)
                stat_list = ['ASBMStatus', 'ASStatus']
                if not ans == None and type(ans[6]) == int: self.value_name['ASBMStatus'] = ans[6] 
                else:                                       self.value_name['ASBMStatus'] = 64
                if not ans == None and type(ans[7]) == int: self.value_name['ASStatus'] = ans[7] 
                else:                                       self.value_name['ASStatus'] = 64

            # Gas 1:
            # Reiehnfolge: MFC24, MFC25, MFC26, MFC27, DM21, PP21, PP22, PP22I
            self.value_name['MFC24'] = value_1[0]   # Einheit: ml/min
            self.value_name['MFC25'] = value_1[1]   # Einheit: ml/min
            self.value_name['MFC26'] = value_1[2]   # Einheit: ml/min
            self.value_name['MFC27'] = value_1[3]   # Einheit: ml/min
            self.value_name['DM21']  = value_1[4]   # Einheit: mbar
            self.value_name['PP21']  = value_1[5]   # Einheit: mbar
            self.value_name['PP22']  = value_1[6]   # Einheit: mbar
            self.value_name['PP22I'] = value_2[0]   # Einheit: %
            if self.Anlage == 2:
                # Gas 2:
                # Reiehnfolge:  MFC24_S, MFC24_FM, MFC25_S, MFC25_FM, MFC26_S, MFC26_FM, MFC27_S, MFC27_FM,
                #               MV1_I, MV1_S, MV1_VS, PP22mPtS, (Rampen-Werte: 12 -21), MV1_SG
                self.value_name['MFC24_S']  = value_3[0]    # Einheit: ml/min
                self.value_name['MFC24_FM'] = value_3[1]    # Einheit: ml/min
                self.value_name['MFC25_S']  = value_3[2]    # Einheit: ml/min
                self.value_name['MFC25_FM'] = value_3[3]    # Einheit: ml/min
                self.value_name['MFC26_S']  = value_3[4]    # Einheit: ml/min
                self.value_name['MFC26_FM'] = value_3[5]    # Einheit: ml/min
                self.value_name['MFC27_S']  = value_3[6]    # Einheit: ml/min
                self.value_name['MFC27_FM'] = value_3[7]    # Einheit: ml/min
                self.value_name['MV1_I']    = value_3[8]    # Einheit: mbar
                self.value_name['MV1_S']    = value_3[9]    # Einheit: mbar
                self.value_name['MV1_VS']   = value_3[10]   # Einheit: % (Annahme)
                self.value_name['PP22mPtS'] = value_3[11]   # Einheit: mbar
                self.value_name['MV1_SG']   = value_3[22]   # Einheit: % (Annahme)

                # Kühlung:
                # Reihenfolge:  KWKDF_1, KWKT_1, KWKDF_2, KWKT_2, KWKDF_3, KWKT_3, KWKDF_4, KWKT_4, KWKDF_5, KWKT_5,
                #               KWKDF_6, KWKT_6, KWKDF_7, KWKT_7, KWKDF_8, KWKT_8, KWKDF_9, KWKT_9,                   
                #               KWK5_In, KWK5_Out, KWK5_diff, KWK46_In, KWK46_Out, KWK46_diff 
                self.value_name['KWKDF_1']      = value_4[0]    # Einheit: l/min
                self.value_name['KWKT_1']       = value_4[1]    # Einheit: °C
                self.value_name['KWKDF_2']      = value_4[2]    # Einheit: l/min
                self.value_name['KWKT_2']       = value_4[3]    # Einheit: °C
                self.value_name['KWKDF_3']      = value_4[4]    # Einheit: l/min
                self.value_name['KWKT_3']       = value_4[5]    # Einheit: °C
                self.value_name['KWKDF_4']      = value_4[6]    # Einheit: l/min
                self.value_name['KWKT_4']       = value_4[7]    # Einheit: °C
                self.value_name['KWKDF_5']      = value_4[8]    # Einheit: l/min
                self.value_name['KWKT_5']       = value_4[9]    # Einheit: °C
                self.value_name['KWKDF_6']      = value_4[10]   # Einheit: l/min
                self.value_name['KWKT_6']       = value_4[11]   # Einheit: °C
                self.value_name['KWKDF_7']      = value_4[12]   # Einheit: l/min
                self.value_name['KWKT_7']       = value_4[13]   # Einheit: °C
                self.value_name['KWKDF_8']      = value_4[14]   # Einheit: l/min
                self.value_name['KWKT_8']       = value_4[15]   # Einheit: °C
                self.value_name['KWKDF_9']      = value_4[16]   # Einheit: l/min            
                self.value_name['KWKT_9']       = value_4[17]   # Einheit: °C
                self.value_name['KWK5_In']      = value_4[18]   # Einheit: l/min (Annahme)
                self.value_name['KWK5_Out']     = value_4[19]   # Einheit: l/min (Annahme)
                self.value_name['KWK5_diff']    = value_4[20]   # Einheit: l/min (Annahme)
                self.value_name['KWK46_In']     = value_4[21]   # Einheit: l/min (Annahme)
                self.value_name['KWK46_Out']    = value_4[22]   # Einheit: l/min (Annahme)
                self.value_name['KWK46_diff']   = value_4[23]   # Einheit: l/min (Annahme)

                # Anlagensicherheit:
                # Reihenfolge:  ASTO, ASTM, ASTU
                self.value_name['ASTO']         = value_5[0]    # Einheit: °C
                self.value_name['ASTM']         = value_5[1]    # Einheit: °C
                self.value_name['ASTU']         = value_5[2]    # Einheit: °C

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
    
    def umwandeln_Float(self, int_Byte_liste):
        ''' Sendet den Lese-Befehl an die Achse.

        Args:
            int_Byte_liste (list):            Liste der ausgelesenen Bytes mit Integern
        Return:
            value_list (list):                Umgewandelte Zahlen
        '''
        try:
            Bits_List_32 = utils.word_list_to_long(int_Byte_liste, big_endian=True, long_long=False)
            logger.debug(f'{self.device_name} - {self.Log_Text_66_str[self.sprache]} {Bits_List_32}')

            value_list = []
            i = 1
            for word in Bits_List_32:
                value = utils.decode_ieee(word)
                value_list.append(round(value, self.nKS))
                logger.debug(f'{self.device_name} - {self.Log_Text_67_str[self.sprache]} {i}: {value}')
                i += 1
        except Exception as e:
            logger.warning(self.Log_Text_Port_4[self.sprache])
            logger.exception(self.Log_Text_Port_5[self.sprache])
            value_list = []

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
                Meldungen = False
                for n in range(0,5,1):
                    if not self.serial.is_open:
                        self.Test_Connection(Meldungen)
                    if n == 4:
                        Meldungen = True
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
            Nemo-1:
            MFC24, MFC25, MFC26, MFC27, DM21, PP21, PP22, PP21Status, PP22Status, PP22I

            Nemo-2:
            MFC24, MFC25, MFC26, MFC27, DM21, PP21, PP22, PP21Status, PP22Status, PP22I, 
            PP22mPtS, MV1_I, MV1_S, MV1_VS, MV1_SG, MV1Status, MFC24_S, MFC24_FM, MFC24Status,
            MFC25_S, MFC25_FM, MFC25Status, MFC26_S, MFC26_FM, MFC26Status, MFC27_S, MFC27_FM, 
            MFC27Status, V1Status, V2Status, V3Status, V4Status, V5Status, V6Status, V7Status, V17Status 
        
        Args:
            pfad (str, optional): Speicherort. Default ist "./".
        """
        self.filename = f"{pfad}/{self.device_name}.csv"
        if self.Anlage == 1:    
            units  = "# datetime,s,ml/min,ml/min,ml/min,ml/min,mbar,mbar,mbar,%,\n"
            header = "time_abs,time_rel,MFC24,MFC25,MFC26,MFC27,DM21,PP21,PP22,PP22I,\n"
        elif self.Anlage == 2:  
            units = "# datetime,s,ml/min,ml/min,ml/min,ml/min,mbar,mbar,%,mbar,mbar,mbar,%,%,ml/min,ml/min,ml/min,ml/min,ml/min,ml/min,ml/min,ml/min,l/min,l/min,l/min,l/min,l/min,l/min,l/min,l/min,l/min,DEG C,DEG C,DEG C,DEG C,DEG C,DEG C,DEG C,DEG C,DEG C,l/min,l/min,l/min,l/min,l/min,l/min,DEG C,DEG C,DEG C,\n"
            header = "time_abs,time_rel,MFC1_Ist,MFC2_Ist,MFC3_Ist,MFC4_Ist,PP1,PP2,P2I,PP2mPtS,MV1_Ist,MV1_Soll,MV1_VS,MV1_SG,MFC1_Soll,MFC1_FlowMax,MFC2_Soll,MFC2_FlowMax,MFC3_Soll,MFC3_FlowMax,MFC4_Soll,MFC4_FlowMax,WK1Flow,WK2Flow,WK3Flow,WK4Flow,WK5Flow,WK6Flow,WK7Flow,WK8Flow,WK9Flow,WK1T,WK2T,WK3T,WK4T,WK5T,WK6T,WK7T,WK8T,WK9T,WK5In,WK5Out,WK5diff,WK46In,WK46Out,WK46diff,SaveThermoOben,SaveThermoMitte,SaveThermoUnten,\n"
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
            skip = 0
            if not 'Status' in size:
                if 'DM21' in size and self.Anlage == 2:
                    skip = 1
                if not skip:
                    line = line + f'{daten[size]},'
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f'{line}\n')
    
    ###################################################
    # Prüfe die Verbindung:
    ###################################################
    def Test_Connection(self, test):
        '''Aufbau Versuch der TCP/IP-Verbindung zur Nemo-Anlage
        Args:
            test (bool)     - Wenn False werden die Fehlermeldungen nicht mehr in die Log-Datei geschrieben
        Return: 
            True or False   - Eingeschaltet/Ausgeschaltet
        '''
        try:
            self.serial.open()
            time.sleep(0.1)         # Dadurch kann es in Ruhe öffnen
            ans = self.serial.read_input_registers(self.start_Lese_Register_VGP_1, 1)  # MFC24
            if ans == None:
                raise ValueError(self.Log_Text_Port_3[self.sprache])
            else:
                antwort = self.umwandeln_Float(ans)
        except Exception as e:
            if test: logger.exception(self.Log_Text_Port_1[self.sprache])
            self.serial.close()
            return False
        return True
            
##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''
            a = round(random.uniform(0,50))
            if a in [10, 20, 30, 40, 50]:  
                exst = ['0.fffßfvvk', 50.1, 90.1] 
                value_1 = []
                for re in range(0,7,1):
                    value_1.append(random.choice(exst))
                print(value_1)
                print('Fehler')

'''