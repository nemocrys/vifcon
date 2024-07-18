# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Verbindung mit Multilog
- In Zusammenarbeit mit Felix Osterle, Studentische Hilfskraft im IKZ - Gruppe: Modellexperimente (Student an der TU Berlin)
- Vorlage für die Verknüpfung stammt von Felix Osterle
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtCore import (
    QObject,
)

## Algemein:
import logging
import socket                       # TCP-Verbindungen
import json                         # Dicts zu String

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)

class Multilog(QObject):
    def __init__(self, sprache, ports_send, ports_read, Ablauf_Funktion, widget_dict, device_dict, trigger_dict_sM, trigger_dict_rM):
        ''' Erstellung einer Verbindung zum IKZ
        
        Args:
            sprache (int):              Sprache der GUI (Listenplatz)
            ports_send (list):          Liste der genutzten Ports (Sende an Multilog)  
            ports_read (list):          Liste der genutzten Ports (Lese von Multilog)               
            Ablauf_Funktion (function): Funktion zur Erweiterung einer Textdatei
            widget_dict (dict):         Dictionary mit allen Geräte-Widgets
            device_dict (dict):         Dictionary mit allen Geräte-Schnittstellen
            trigger_dict_sM (dict):     Dictionary mit allen Triggern für das senden an Multilog
            trigger_dict_rM (dict):     Dictionary mit allen Triggern für das Empfangen von Werten von Multilog
        '''
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Init:
        self.sprache                    = sprache
        portList_send                   = ports_send
        portList_read                   = ports_read
        self.add_Text_To_Ablauf_Datei   = Ablauf_Funktion
        self.device_widget              = widget_dict
        self.device_schnitt             = device_dict
        self.trigger_send               = trigger_dict_sM   
        self.trigger_read               = trigger_dict_rM       

        ## Weitere:
        self.done                       = False                 # Ende der Endlosschleife, wenn True      
        self.trigger_send_List          = []                    # Leere Trigger-Liste
        self.trigger_read_List          = []                    # Leere Trigger-Liste
        error                           = False                 # Fehler beim Aufbau!

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Logging:                             
        self.Log_Text_186_str   =   ['Multilog-Verbindungs Objekt',                                                         'Multilog connection object']
        self.Log_Text_187_str   =   ['Erstellung!',                                                                         'Creation!']
        self.Log_Text_188_str   =   ['Port-Liste (Sende an Multilog) (genutzte Ports):',                                    'Port list (Send to Multilog) (ports used):']
        self.Log_Text_189_str   =   ['Trigger-Liste (Sende an Multilog) (genutzte Trigger aus der Konfigurationsdatei):',   'Trigger list (Send to Multilog) (used triggers from the configuration file):']
        self.Log_Text_190_str   =   ['Der folgende Trigger existiert mehr als einmal:',                                     'The following trigger exists more than once:']
        self.Log_Text_191_str   =   ['Der folgende Port existiert mehr als einmal:',                                        'The following port exists more than once:']
        self.Log_Text_192_str   =   ['-Port hat folgende Objekt-Parameter:',                                                '-Port has the following object parameters:']
        self.Log_Text_193_str   =   ['und folgende Endverbindung:',                                                         'and the following end connection:']
        self.Log_Text_194_str   =   ['Bearbeitung von Trigger:',                                                            'Editing triggers:']
        self.Log_Text_195_str   =   ['an Verbindung',                                                                       'to connection']
        self.Log_Text_196_str   =   ['Sende Daten:',                                                                        'Send data:']
        self.Log_Text_197_str   =   ['Trigger-Fehler: Unbekannter Trigger von Multilog ->',                                 'Trigger error: Unknown trigger from Multilog ->']
        self.Log_Text_198_str   =   ['Existieren tun folgende Trigger in VIFCON:',                                          'The following triggers do exist in VIFCON:']
        self.Log_Text_199_str   =   ['Verbindung beendet mit Multilog!',                                                    'Connection terminated with Multilog!']
        self.Log_Text_200_str   =   ['Multilog sendet Leere String als Trigger -> Beende Kommunikation!',                   'Multilog sends empty string as trigger -> end communication!']
        self.Log_Text_201_str   =   ['Sende Fehler:',                                                                       'Send error:']
        self.Log_Text_202_str   =   ['Aufgrund eines falschen Triggers, wird die Verbindung gelöscht:',                     'Due to an incorrect trigger, the connection is deleted:']
        self.Log_Text_209_str   =   ['ACHTUNG: Multilog starten, wenn noch nicht erfolgt!! Aufbau Verbindung zu Port',      "ATTENTION: Start multilog if it hasn't already happened!! Establishing a connection to port"]
        self.Log_Text_210_str   =   ['Multilog-Link wird nicht erstellt, da Fehler!',                                       "Multilog link is not created because error!"]
        self.Log_Text_211_str   =   ['Anzahl:',                                                                             "Amount:"]
        self.Log_Text_189r_str  =   ['Trigger-Liste (Lese von Multilog) (genutzte Trigger aus der Konfigurationsdatei):',   'Trigger list (Read from Multilog) (used triggers from the configuration file):']
        self.Log_Text_188r_str  =   ['Port-Liste (Lese von Multilog) (genutzte Ports):',                                    'Port list (Read from Multilog) (ports used):']
        self.Log_Text_rM        =   ['Wert konnte nicht von Multilog geholt werden. Connection: ',                          'Value could not be retrieved from Multilog. Connection: ']
        self.Log_Text_MD_1      =   ['Multilog Daten:',                                                                     'Multilog data:']
        self.Log_Text_MD_2      =   ['für',                                                                                 'for']
        
        #--------------------------------------- 
        # Informationen 1:
        #---------------------------------------
        ## Trigger-Liste:
        for n in self.trigger_send:
            self.trigger_send_List.append(self.trigger_send[n])
        for n in self.trigger_read:
            self.trigger_read_List.append(self.trigger_read[n])

        ## Logging-Infos:
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_187_str[self.sprache]}")
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_188_str[self.sprache]} {portList_send}")
        find_List = []
        for n in portList_send:
            z = portList_send.count(n)
            if z > 1:
                if not n in find_List:
                    find_List.append(n)
                    logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_191_str[self.sprache]} {n} - {self.Log_Text_211_str[self.sprache]} {z}")
                    error = True
        
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_188r_str[self.sprache]} {portList_read}")
        find_List = []
        for n in portList_read:
            z = portList_read.count(n)
            if z > 1:
                if not n in find_List:
                    find_List.append(n)
                    logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_191_str[self.sprache]} {n} - {self.Log_Text_211_str[self.sprache]} {z}")
                    error = True

        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_189_str[self.sprache]} {self.trigger_send_List}")
        find_List = []
        for n in self.trigger_send_List:
            z = self.trigger_send_List.count(n)
            if z > 1:
                if not n in find_List:
                    find_List.append(n)
                    logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_190_str[self.sprache]} {n} - {self.Log_Text_211_str[self.sprache]} {z}")
                    error = True
        
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_189r_str[self.sprache]} {self.trigger_read_List}")
        find_List = []
        for n in self.trigger_read_List:
            z = self.trigger_read_List.count(n)
            if z > 1:
                if not n in find_List:
                    find_List.append(n)
                    logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_190_str[self.sprache]} {n} - {self.Log_Text_211_str[self.sprache]} {z}")
                    error = True

        #--------------------------------------------------
        # Multilog Verbindungsaufbau 1 & Informationen 2:
        #--------------------------------------------------
        self.connectList            = []
        ReadSend                    = {}
        self.ReadSend_Connection    = {}
        self.Trigger_Connection     = {}
        portList                    = []
        for n in portList_send:
            ReadSend.update({n:'Send'})
            portList.append(n)
        for n in portList_read:
            ReadSend.update({n:'Read'})
            portList.append(n)

        portList.sort()                                             # Liste der Ports muss sortiert sein!
        if not error:
            for port in portList:
                c, a = self.create_socket(port)                     # Erstellen einer neuen Verbindung
                logger.info(f"{self.Log_Text_186_str[self.sprache]} - {port}{self.Log_Text_192_str[self.sprache]} {c} {self.Log_Text_193_str[self.sprache]} {a}")
                self.connectList.append(c)                          # Verbindung zu einer Liste hinzufügen
                self.ReadSend_Connection.update({c:ReadSend[port]})
                if self.ReadSend_Connection[c] == 'Read':
                    self.Trigger_Connection.update({c:trigger_dict_rM[port]})
        else:
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_210_str[self.sprache]}")
            self.done = True

    ##########################################
    # Multilog Verbindungsaufbau 2:
    ##########################################
    def create_socket(self, TCP_PORT):
        '''Erstellt die Verbindung zum TCP Port
        
        Args:
            TCP_PORT (int):         Port aus der Config
        Return:
            connection (objekt):    Verbindung (<class 'socket.socket'>)            - neues Objekt zum Senden und Empfangen von Daten über die Verbindung
            address (tuple):        Adresse (raddr z.B. ('172.18.52.219', 62576))   - Adresse die an den Socket am anderen Ende der Verbindung gebunden ist
                                                                                    -> Quelle: https://docs.python.org/3/library/socket.html#socket.socket.accept
        '''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:    # durch with, kann auf das close verzichtet werden
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('', TCP_PORT))                                      # Eine bestimmte IP muss nur in Mutilog angegeben werden
            server_socket.listen(1)
            logging.warning(f'{self.Log_Text_209_str[self.sprache]} {TCP_PORT}')
            connection, address = server_socket.accept() 
        return connection, address 

    ##########################################
    # Daten besorgen und weitersenden:
    ##########################################
    def sendData(self, c, trigger):
        '''Hole und Sende Daten
        
        Args:
            c (<class 'socket.socket'>):        Verbindung
            trigger (str):                      Trigger Wort
        '''
        logger.debug(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_194_str[self.sprache]} {trigger} {self.Log_Text_195_str[self.sprache]} {c}")

        # Trigger ist in Liste:
        if trigger in self.trigger_send_List :
            deviceJSON = ""
            for device in self.trigger_send:
                if trigger == self.trigger_send[device]:
                    data_ak = self.device_widget[device].data
                    logger.debug(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_196_str[self.sprache]} ({trigger}) {data_ak}")
                    deviceJSON += json.dumps(data_ak) 

            data = bytes(deviceJSON,encoding="utf-8")       # Dict zu String zu Bianry
            c.sendall(data)                                 # Dict senden
        # Client (Multilog) wurde beendet bzw. die Verbindung wurde getrennt --> Leerer Stirng:
        elif trigger == '' and not self.done:
            logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_200_str[self.sprache]}")
            self.ende()
        # Trigger ist nicht in Liste:
        elif not trigger in self.trigger_send_List  and not self.done:
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_197_str[self.sprache]} {trigger}")
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_198_str[self.sprache]} {self.trigger_send_List }")
            logger.warning(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_202_str[self.sprache]} {c}")
            self.connectList.remove(c)                      # Entfernt Verbindung des falschen Triggers!
            
    def HoleData(self, c, trigger_Device):
        '''Hole Daten von Multilog und gebe sie ans richtige Gerät!
        
        Args:
            c (<class 'socket.socket'>):        Verbindung
            trigger_Device (list):              Trigger Wort, Geräte-Name
        '''
        try:
            c.send(bytes(trigger_Device[0], 'UTF-8'))
            received = c.recv(1024)
            received = received.decode("utf-8")
            data = json.loads(received)
            logger.debug(f'{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_MD_1[self.sprache]} {data} {self.Log_Text_MD_2[self.sprache]} {trigger_Device[1]}')
            self.device_schnitt[trigger_Device[1]].mult_data = data
        except Exception as e:
            logger.exception(f'{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_201_str[self.sprache]} - {self.Log_Text_rM[self.sprache]}{c}, {trigger_Device}')
            
    ##########################################
    # Endlosschleife und Endfunktion:
    ##########################################
    def event_Loop(self):
        '''Endlosschleife: Empfang der Trigger und Senden der Daten'''
        while not self.done:
            try:
                for c in self.connectList:                  # gehe jede Verbindung die besteht durch
                    if self.ReadSend_Connection[c] == 'Send':
                        trigger = c.recv(1024).decode('utf-8')  # warte auf Triggerwort und lese dieses
                        self.sendData(c, trigger)               # erstelle und sende die Daten
                    elif self.ReadSend_Connection[c] == 'Read':
                        self.HoleData(c, self.Trigger_Connection[c])
            except Exception as e:
                logger.exception(f'{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_201_str[self.sprache]}')
    
    def ende(self):
        '''Setzt While-Schleifen Bedingung auf True und beendet so Endlosschleife!'''
        self.done = True
        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_199_str[self.sprache]}')
        logger.info(f"{self.Log_Text_186_str[self.sprache]} - {self.Log_Text_199_str[self.sprache]}")

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''