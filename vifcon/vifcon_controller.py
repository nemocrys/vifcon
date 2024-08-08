# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
VIFCON-Controller:
- Erstellung der Threads und Signale
- Erstellung der GUI
- Erstellung des Sampling-Objekts
- Erstellung der Schnittstellen-Objekte für die Geräte
- Erstellung der Geräte-Widget-Objekte
- Gegebenfalls Erstellung von Gamepad und Multilog-Link

Der Controller macht die Kommunikation zwischen der GUI und den Geräten möglich.
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtWidgets import (
    QApplication,
    QAction,
    
)
from PyQt5.QtCore import (
    QObject,
    QTimer,
    QThread,
    pyqtSignal,
    QMutex, 
    QMutexLocker,

)

## Algemein:
import logging
import yaml
import sys
import os
import datetime
import time
import random
import shutil

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger()
# Quelle: https://stackoverflow.com/questions/50714316/how-to-use-logging-getlogger-name-in-multiple-modules
#   - Somit übernimmt er die Filter in die anderen unter Programme!
#   - Mainlogger


# This metaclass is required because the pyqtSignal 'signal' must be a class varaible
# see https://stackoverflow.com/questions/50294652/is-it-possible-to-create-pyqtsignals-on-instances-at-runtime-without-using-class
class SignalMetaclass(type(QObject)):
    """ Metaclass used to create new signals on the fly, required to
    setup Sampler class, see
    https://stackoverflow.com/questions/50294652/is-it-possible-to-create-pyqtsignals-on-instances-at-runtime-without-using-class"""

    def __new__(cls, name, bases, dct):
        """ Create new class including a pyqtSignal."""
        dct["signal"] = pyqtSignal(dict, list, str)
        return super().__new__(cls, name, bases, dct)


class Sampler(QObject, metaclass=SignalMetaclass):
    """ Diese Klasse wird dazu genutzt um die Geräte von seperaten Threads zu beschreiben und aus zulesen."""

    def __init__(self, device, device_name, device_widget, menu_btn, start_time, test, mutex):
        """ Create sampler object

        Args:
            device (obj):           Geräte Objekt
            device_name (str):      Geräte Name
            device_widget (obj):    Geräte GUI Objekt
            menu_btn (QAtion):      Initialisierungs Menü-Knopf
            start_time (time):      Startzeit
            test (bool):            Test Modus
            mutex (QMutex):         Mutex - gegenseitiger Ausschluss (Blockade)
        """
        super().__init__()

        #---------------------------------------
        # Geräte und GUI - Elemente:
        #---------------------------------------
        ## Objekte:
        self.device = device
        self.device_name = device_name
        self.device_widget = device_widget
        self.typ_widget = self.device_widget.typ_widget
        self.btn_Init = menu_btn

        ## Zeiten:
        self.messTime = self.device.messZeit

        self.startTime = start_time
        self.time = start_time

        ## Test-Modus:
        self.test = test

        ## Verriegelung:
        self.mutex = mutex

        ## Werte Listen:
        self.xList = []

        ## Andere Variablen:
        self.port_error_anz = 5
        self.count_error = 0
        self.exit = False

        #---------------------------------------
        # Sprache:
        #---------------------------------------
        self.sprache = self.device_widget.sprache
        ## Logging:
        self.Log_Text_2_str = ['Sampler-Funktion vor Locker!',                                      'Sampler function before Locker!']
        self.Log_Text_3_str = ['Sampler-Funktion nach Locker! Locker',                              'Sampler function according to Locker!']
        self.Log_Text_4_str = ['aktiv!',                                                            'active!']
        self.Log_Text_5_str = ['Sampler-Funktion fertig! Locker wieder freigegeben!',               'Sampler function ready! Locker released again!']
        self.Log_Text_6_str = ['Der Port ist geschlossen! Code-Ausführung gesperrt!',               'The port is closed! Code execution blocked!']
        self.Log_Text_7_str = ['Anzeige der Port-Fehler-Warnung nur',                               'Port error warning only displayed']
        self.Log_Text_8_str = ['mal! Anzeige erst nach Fehlerfreien Port-Zugang!',                  'times! Display only after error-free port access!']

    def sample(self):
        ''' Löse Lese und Schreib Funktionen am Gerät aus.
        1. Sende Werte an die Geräte (write).
        2. Lese Werte von den Geräten (read) zu bestimmten Zeitabständen. 
        '''
        self.end_done = False
        logging.debug(f"{self.device_name} - {self.Log_Text_2_str[self.sprache]}")
        with QMutexLocker(self.mutex):
            logging.debug(f"{self.device_name} - {self.Log_Text_3_str[self.sprache]} {self.mutex} {self.Log_Text_4_str[self.sprache]}")
            #---------------------------------------
            # aktuelle Zeit zum Startzeitpunkt:
            #---------------------------------------
            ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()     # Aktuelle Zeit Absolut
            time_rel = round((ak_time - self.startTime).total_seconds(), 3)         # Aktuelle Zeit Relativ

            #---------------------------------------
            # Port Kontrolle:
            #---------------------------------------
            if not self.test and self.device.init:  port = self.device.serial.is_open
            else:                                   port = True

            if 'Nemo' in self.device_name and not port and self.exit and self.device.init:  # Bei ERfolgreichen Test, Port als offen ansehen!!
                 self.device.Test_Connection()

            # Ist der Port des Gerätes erreichbar bzw. Offen so kann die Kommunikation stattfinden!
            if port:
                self.count_error = 0
                #---------------------------------------
                # Initialisierung übergeben:
                #---------------------------------------
                if self.device_widget.write_task['Init'] and not self.test:
                    self.device.init_device()
                    self.device_widget.init_controll(self.device.init, self.btn_Init)
                    self.device_widget.write_task['Init'] = False

                #---------------------------------------
                # Schreibe Werte:
                #---------------------------------------
                #if self.device_widget.send_betätigt:                                               # Ruft nun immer die write Funktion auf!
                if not self.test and not 'Nemo-Gase' in self.device_name:
                    self.device.write(self.device_widget.write_task, self.device_widget.write_value)    
                #    self.device_widget.send_betätigt = False
                
                #---------------------------------------
                # Kontrolle/ Geräte spezielle Aufagben:
                #---------------------------------------
                if 'PI-Achse' in self.device_name and self.device.init:
                    # Wenn das Gerät initialisiert wurde, soll die aktuelle Position immer an die GUI gesendet werden:
                    self.device_widget.akPos = self.device.akPos
                    # Wenn Modus 2 ausgewählt, werden die Knöpfe der GUI bei der Achse bei 0 mm/s entriegelt!
                    if self.device_widget.mode == 2 and self.device_widget.losgefahren:
                        self.device_widget.check_verriegelung(self.device.read_TV())
                if 'Eurotherm' in self.device_name and self.device.config['start']['sicherheit'] == True:
                    # So bald sich im Gerät der HO ändert und die Leistung ausgewählt wurde oder der Menü-Knopf gedrückt wird, wird auch im Widget die Leistung geändert!
                    self.device_widget.oGOp = self.device.oGOp

                #---------------------------------------
                # Lese Werte:
                #---------------------------------------
                ## Bestimme Zeitdifferenz für das Auslesen:
                timediff = (
                    datetime.datetime.now(datetime.timezone.utc).astimezone() - self.time
                ).total_seconds()                                                       

                ## Lese, wenn die Messzeit überschritten wurde oder identisch ist:
                if timediff >= self.messTime and self.messTime != 0 and self.device_widget.init:
                    self.time = datetime.datetime.now(datetime.timezone.utc).astimezone()
                    self.xList.append(time_rel)
                    if not self.test:
                        sample_values = self.device.read()
                        self.device.update_output(sample_values, ak_time, time_rel)
                    else:
                        sample_values = self.device.value_name
                        for key in sample_values:
                            sample_values[key] = round(random.uniform(0, 10), 3)
                            if 'Status' in key:
                                sample_values[key] =  128          # Bit 15 gesetzt - 0 bis 15 - Test-Modus

                    self.device_widget.ak_value = sample_values
                    self.signal.emit(sample_values, self.xList, self.device_name)
            else:
                if self.count_error < self.port_error_anz:
                    logging.warning(f"{self.device_name} - {self.Log_Text_6_str[self.sprache]} ")
                    self.count_error += 1
                    if self.count_error == self.port_error_anz:
                        logging.warning(f"{self.Log_Text_7_str[self.sprache]} {self.port_error_anz} {self.Log_Text_8_str[self.sprache]}")
        logging.debug(f"{self.device_name} - {self.Log_Text_5_str[self.sprache]}")
        self.end_done = True


class MyFilter(object):
    ''' Logging Filter für Konsolen Ausgabe:
    Quelle:     https://stackoverflow.com/questions/8162419/python-logging-specific-level-only
    Erweitert:  1. Init - operator 
                2. Funktion filter um die If-Else Anweisung
                3. Kommentare
    '''
    def __init__(self, level, operator):
        ''' 
        Args:
            level (logging Objekt): definiert das Ausgangslevel der zu filternden Log-Nachrichten
            operator (int):         Was soll zu dem level noch gelogget werden in der Konsole
        '''
        self.__level = level
        self.operator = operator

    def filter(self, logRecord):
        ''' Log-Nachrichten Filtern und in Konsole zurückgeben!
        Args:
            logRecord (Logging Objekt): Log-Nachricht
        '''
        if self.operator == 1:
            return logRecord.levelno == self.__level
        elif self.operator == 2:
            return logRecord.levelno <= self.__level
        elif self.operator == 3:
            return logRecord.levelno >= self.__level


class Controller(QObject):
    # Controller der die Kommunikationn zwischen GUI und Gerät ermöglicht

    # Signale:
    signal_sample_main  = pyqtSignal()
    signal_Multilog     = pyqtSignal()
    signal_gamepad      = pyqtSignal()

    def __init__(self, config, output_dir, test_mode, neustart) -> None:
        """Initialize and run vifcon.

        Args:
            config (str):       File Pfad vom Configurations File.
            output_dir (str):   Verzeichnis, wo die Outputs hingelegt werden sollen.
            test_mode (bool):   Test Mode Aktiv.
        """
        super().__init__()

        self.test_mode = test_mode
        self.config_pfad = config
        self.neustart = neustart

        #--------------------------------------------------------------------------
        # Yaml-Datei auslesen:
        #--------------------------------------------------------------------------
        ## Yaml:
        with open(config, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        #---------------------------------------------------------------------------
        # Sprachvariablen:
        #--------------------------------------------------------------------------
        ## Konfiguriere Sprache:
        if self.config['language'].upper() == 'DE':
            logger.info('Sprache der GUI ist Deutsch!')
            self.sprache = 0
        elif self.config['language'].upper() == 'EN':
            logger.info('The language of the GUI is English!')
            self.sprache = 1
        else:
            logger.warning('The language is not defined. Only German and English are defined in this program. Set language to English!')
            print('Warning: The language is not defined. Only German and English are defined in this program. Set language to English!')
            self.sprache = 1
        
        ## Variablen:
        main_window_tab_1_str   = ['Steuerung'  ,                                                                                                       'Control']
        main_window_tab_2_str   = ['Überwachung',                                                                                                       'Monitoring']
        ## Logging:                                                     
        self.Log_Text_6_str     = ["Initialisiere VIFCON",                                                                                              'Initialize VIFCON']
        self.Log_Text_7_str     = ['Konfiguration:',                                                                                                    'Configuration:']
        self.Log_Text_8_str     = ["Test Modus aktiv.",                                                                                                 "Test mode active."]
        self.Log_Text_9_str     = ['In der Config stimmt etwas nicht! Default Ein: Nur Warning in Konsole möglich.',                                    'Something is wrong in the config! Default On: Only warning in console possible.']
        self.Log_Text_10_str    = ['in QMutex',                                                                                                         'in QMutex']
        self.Log_Text_11_str    = ['Das Gerät konnte nicht in der Menüleiste Initialisierung erstellt werden!',                                         'The device could not be created in the initialization menu bar!']
        self.Log_Text_12_str    = ["Bereite Threads vor",                                                                                               "Prepare threads"]
        self.Log_Text_13_str    = ['in Thread',                                                                                                         'in thread']
        self.Log_Text_14_str    = ['Start des Sampling-Timers',                                                                                         'Start of the sampling timer']
        self.Log_Text_15_str    = ['Update GUI von',                                                                                                    'Update GUI from']
        self.Log_Text_16_str    = ['Fehler beim Updaten der GUI im Gerät',                                                                              'Error updating the GUI in the device']
        self.Log_Text_17_str    = ["Aufruf der Threads!",                                                                                               "Calling the Threads!"]
        self.Log_Text_18_str    = ['Beende Thread',                                                                                                     'Quitting thread']
        self.Log_Text_19_str    = ['Schließe Port am Gerät',                                                                                            'Close port on device']
        self.Log_Text_20_str    = ['Kopiere Config-Datei in',                                                                                           'Copy config file to']
        self.Log_Text_21_str    = ['Kopiere Logging Datei in',                                                                                          'Copy logging file into']
        self.Log_Text_22_str    = ['Speichere Plot des',                                                                                                'Save plot of']
        self.Log_Text_23_str    = ['Typs in',                                                                                                           'type in']
        self.Log_Text_24_str    = ['Stoppe alle Achsen!',                                                                                               'Stop all axes!']
        self.Log_Text_25_str    = ['Achsen sollen synchron fahren!',                                                                                    'Axes should move synchronously!']
        self.Log_Text_26_str    = ['Synchro Rezept!',                                                                                                   'Synchro recipe!']
        self.Log_Text_27_str    = ['Update Konfiguration (Update Rezepte):',                                                                            'Update configuration (update recipes):']
        self.Log_Text_203_str   = ['Synchro Rezept Abschaltung!',                                                                                       'Synchro recipe shutdown!']
        self.Log_Text_204_str   = ['Das Gerät konnte nicht in der Menüleiste Limit erstellt werden!',                                                   'The device could not be created in the limit menu bar!']
        self.Log_Text_208_str   = ['Beende Multilog Verbindung und Beende den Thread:',                                                                 'Close Multilog connection and end the thread:']
        self.Log_Text_222_str   = ['Der Aufbau mit dem Gamepad ist fehlgeschlagen!',                                                                    'The setup with the gamepad failed!']
        self.Log_Text_223_str   = ['Start des Gamepad-Threads!',                                                                                        'Start of the gamepad thread!']
        self.Log_Text_251_str   = ['Main-Window Größe (x-Koordinate, y-Koordinate, Breite, Höhe)',                                                      'Main window size (x coordinate, y coordinate, width, height)']
        self.Log_Text_252_str   = ['Geräte-Widget Größe (x-Koordinate, y-Koordinate, Breite, Höhe)',                                                    'Device widget size (x-coordinate, y-coordinate, width, height)']
        self.Log_Text_End_str   = ['Beenden Betätigt - Sicheren Zustand herstellen, Threads beenden, Ports schließen, Dateien und Plots speichern',     'Exit Activated - Establish a safe state, terminate threads, close ports, save files and plots']
        self.Log_Text_300_str   = ['Anwendung Schließen - Aufruf Exit - Von:',                                                                          'Application Close - Call Exit - From:']  
        self.Log_Text_301_str   = ['bis',                                                                                                               'to']        
        self.Log_Text_302_str   = ['Gesamtdauer:',                                                                                                      'Total duration:']
        self.Log_Text_303_str   = ['s',                                                                                                                 's']
        self.Log_Text_304_str   = ['Aufruf der Threads bzw. der Funktion ckeck_device:',                                                                'Calling the threads or the function ckeck_device:']
        self.Log_Text_305_str   = ['Startzeit:',                                                                                                        'Start time:']
        self.Log_Text_S_GUI     = ['Speichere die aktuell sichtbare GUI in',                                                                            'Save the currently visible GUI in']
        ## Error:
        self.err_Text_1         = ['Zu hohe Verzeichnisanzahl.',                                                                                        "Too high directory count."]
        self.err_Text_2         = ['Synchron Modus benötigt\nAbsolute Positionierung (PI-Achse)!!',                                                     'Synchronous mode requires\nabsolute positioning (PI axis)!!']
        ## Ablaufdatei:
        self.Text_2_str         = ['Ablauf der Messung:',                                                                                               'Measuring process:']
        self.Text_3_str         = ['Werteingaben und Knopfberührungen',                                                                                 'Value entries and button touches']
        self.Text_4_str         = ['Exit-Knopf betätigt - Programm beendet!',                                                                           'Exit button pressed - program ended!']
        self.Text_5_str         = ['Knopf betätigt - Alle',                                                                                             'Button pressed - All']
        self.Text_6_str         = ['stoppen!',                                                                                                          'stop!']
        self.Text_7_str         = ['Knopf betätigt - Synchrones Achsen Fahren!',                                                                        'Button pressed - synchronous axis movement!']
        self.Text_8_str         = ['Menü-Knopf betätigt - Synchro Rezepte Start!',                                                                      'Menu button pressed - Synchro recipes start!']
        self.Text_9_str         = ['Menü-Knopf betätigt - Rezepte Neu einlesen!',                                                                       'Menu button pressed - re-read recipes!']
        self.Text_79_str        = ['Menü-Knopf betätigt - Synchro Rezepte Ende!',                                                                       'Menu button pressed - Synchro recipes end!']
        ## Menü:
        EuHO_Menu_str           = ['&HO lesen',                                                                                                         'Read &HO']
        
        #--------------------------------------------------------------------------
        # Logging-Datei erstellen:
        #--------------------------------------------------------------------------
        ## Logging:
        logging.basicConfig(**self.config["logging"])
        logging.info(self.Log_Text_6_str[self.sprache])
        logging.info(f"{self.Log_Text_7_str[self.sprache]} {self.config}")
        if self.test_mode:
            logging.info(self.Log_Text_8_str[self.sprache])

        ## Logging in der Konsole:
        # Quelle:   https://stackoverflow.com/questions/13733552/logger-configuration-to-log-to-file-and-print-to-stdout
        #           https://stackoverflow.com/questions/8162419/python-logging-specific-level-only
        ### Erzeugung eines weiteren Handlers für das Logging:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.DEBUG)                                   # Das Level muss hier Info sein!
        consolFormat = logging.Formatter(self.config['consol_Logging']['format'])
        consoleHandler.setFormatter(consolFormat)
        ### Füge an bestehenden Handler:
        logger.addHandler(consoleHandler)
        ### Filter für den neuen Handler:
        ak_Level_Consol_Log = self.config['consol_Logging']['level']
        level_Log = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR}
        ak_Anzeige_Level = self.config['consol_Logging']['print']
        try:
            consoleHandler.addFilter(MyFilter(level_Log[ak_Level_Consol_Log], ak_Anzeige_Level))
        except:
            consoleHandler.addFilter(MyFilter(logging.WARNING, 1))
            logger.warning(self.Log_Text_9_str[self.sprache])

        ## Ordnerpfad einlesen:
        self.output_dir = output_dir   
        
        #---------------------------------------------------------------------------
        # Bibliotheken GUI und Geräte - Eigene:
        #--------------------------------------------------------------------------
        ## Geräte:
        from .devices.eurotherm import Eurotherm
        from .devices.piAchse import PIAchse
        from .devices.truHeat import TruHeat
        from .devices.nemoAchseLin import NemoAchseLin
        from .devices.nemoAchseRot import NemoAchseRot
        from .devices.nemoGase import NemoGase
        from .devices.multilog import Multilog
        from .devices.gamepad import Gamepad_1

        ## GUI:
        ### Hauptteile:
        from .view.main_window import MainWindow
        from .view.base_classes import Splitter
        from .view.typen import Generator, Antrieb

        ### Geräte-GUI-Teile:
        from .view.eurotherm import EurothermWidget
        from .view.piAchse import PIAchseWidget
        from .view.truHeat import TruHeatWidget
        from .view.nemoAchseLin import NemoAchseLinWidget
        from .view.nemoAchseRot import NemoAchseRotWidget
        from .view.nemoGase import NemoGaseWidget

        #---------------------------------------------------------------------------
        # Vorbereitung:
        #--------------------------------------------------------------------------
        ## Reaktionstimer:
        self.timer_check_device = QTimer()                                              # Reaktionszeittimer (ruft die Geräte auf, liest aber nur unter bestimmten Bedingungen!)
        self.timer_check_device.setInterval(self.config["time"]["dt-main"])
        self.timer_check_device.timeout.connect(self.ckeck_device)

        ## Zeiten:
        self.start_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        logging.info(f'{self.Log_Text_305_str[self.sprache]} {self.start_time}')

        #---------------------------------------------------------------------------
        # Hauptteile der GUI erstellen:
        #--------------------------------------------------------------------------
        app = QApplication(sys.argv)
        ## Hauptfenster:
        self.main_window = MainWindow(self.exit, self.sync_rezept, self.sync_end_rezept, self.rezept_einlesen, self.sprache, self.config['Function_Skip']['Generell_GamePad'])  
        Frame_Anzeige = self.config['GUI_Frame']                                      

        ## Hauttabs erstellen:
        ### Haupttab Steuerung:
        self.tab_GenAnt = Splitter('H', True)
        self.main_window.add_tab(self.tab_GenAnt.splitter, main_window_tab_1_str[self.sprache])

        scale = self.config['skalFak']
        self.generator = Generator(self.start_time, self.tab_GenAnt.splitter, self.add_Ablauf, self.stopp_all, self.main_window.menu_dict, self.config["legend"]["generator"], scale, self.sprache)
        self.antrieb = Antrieb(self.start_time, self.tab_GenAnt.splitter, self.add_Ablauf, self.stopp_all, self.synchro_achse, self.main_window.menu_dict, self.config["legend"]["antrieb"], scale, self.sprache)

        ### Haupttab Monitoring:
        self.tab_Mon = Splitter('H', True)
        self.main_window.add_tab(self.tab_Mon.splitter, main_window_tab_2_str[self.sprache])

        self.tab_Teile = {'Generator':self.generator, 'Antrieb':self.antrieb, 'Monitoring': self.tab_Mon}

        #---------------------------------------------------------------------------
        # Geräte und ihre GUI-Teile erstellen:
        #--------------------------------------------------------------------------
        ## Kurven und Label Farb-Liste:
        COLORS = [
            "green",
            "cyan",
            "magenta",
            "blue",
            "orange",
            "darkmagenta",
            "brown",
            "tomato",
            "lime",
            "olive",
            "navy",
            "peru",
            "grey",
            "black",
            "darkorange",
            "sienna",
            "gold",
            "yellowgreen",
            "skyblue",
            "mediumorchid",
            "deeppink",
            "purple",
            "darkred"
        ] # 23 Farben - https://matplotlib.org/stable/gallery/color/named_colors.html 

        ## Geräte und ihre Tabs erstellen:
        color_Gen_n = 0
        color_Ant_n = 0

        ### Schnittstelle:
        self.com_sammlung           = {}                                                  # Dictionary für alle Coms (Schnittstellen)
        self.com_doppelt            = []                                                  # Alle Coms die öfters genutzt werden
        self.mutexs                 = {}                                                  # Dictionary mit QMutex
        ### Geräte:
        self.devices                = {}                                                  # Dictionary für alle Geräte
        self.widgets                = {}                                                  # Dictionary für alle Geräte GUI Teile
        ### Multilog:
        self.trigger_send           = {}                                                  # Dictionary für die Trigger-Wörter (an Multilog)
        self.trigger_read           = {}                                                  # Dictionary für die Trigger-Wörter (von Mulitlog)
        self.port_List_send         = []                                                  # Liste der Ports
        self.port_List_read         = []                                                  # Liste der Ports
        ### Gamepad:
        self.PadAchsenList          = []                                                  # Verbundene Achsen mit dem Controller
        self.hardware_controller    = False                                               # Controller soll erstellt werden

        for device_name in self.config['devices']:
            if not self.config['devices'][device_name]['skip']:                           # Wenn skip == True, dann überspringe die Erstellung
                ### Auswahl Farbe und Geräte-Typ:
                ak_color = []                                                             # zu übergebene Liste mit Farben
                color = 0                                                                 # Start-Listenwert 
                device_typ = self.config['devices'][device_name]['typ']                   # Geräte-Typ
                device_typ_widget = self.tab_Teile[device_typ]                            # Geräte-Widget, an das das Gerät geaddet werden soll

                if device_typ == 'Generator':
                    color = color_Gen_n
                elif device_typ == 'Antrieb':
                    color = color_Ant_n
                for n in range(color,color+10,1):
                    try:
                        ak_color.append(COLORS[n])
                    except:
                        # Verhindert das Überlaufen von Farben, da Liste immer mit 10 Farben gefüllt wird, da TruHeat so viele braucht!
                        nix = 'nix'
                
                ### Geräte erstellen:
                if device_typ == 'Generator':
                    if 'Eurotherm' in device_name:
                        device = Eurotherm(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, self.add_Ablauf, device_name)
                        widget = EurothermWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, self.add_Ablauf, device_name)
                        menu_HO_Button = QAction(f'{device_name} - {EuHO_Menu_str[self.sprache]}', self)
                        menu_HO_Button.triggered.connect(widget.Lese_HO)
                        self.main_window.G_menu.addAction(menu_HO_Button)
                        color_Gen_n = color_Gen_n + 5
                    elif 'TruHeat' in device_name:
                        device = TruHeat(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, self.add_Ablauf, device_name) 
                        widget = TruHeatWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, self.add_Ablauf, device_name)
                        color_Gen_n = color_Gen_n + 10
                elif device_typ == 'Antrieb':
                    if 'PI-Achse' in device_name:
                        device = PIAchse(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, self.add_Ablauf, device_name)
                        if device.config['start']['init'] and not self.test_mode:
                            start_werte = device.read() 
                        else:
                            start_werte = {'IWv': '?', 'IWs': '?'}
                        widget = PIAchseWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, start_werte, self.neustart, self.add_Ablauf, device_name, self.config['Function_Skip']['Generell_GamePad'])
                        color_Ant_n = color_Ant_n + 3
                    elif 'Nemo-Achse-Linear' in device_name:
                        device = NemoAchseLin(self.sprache, self.config['devices'][device_name], config, self.com_sammlung, self.test_mode, self.neustart, self.add_Ablauf, device_name) 
                        widget = NemoAchseLinWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, self.add_Ablauf, device_name, self.config['Function_Skip']['Generell_GamePad'])
                        color_Ant_n = color_Ant_n + 6
                    elif 'Nemo-Achse-Rotation' in device_name:
                        device = NemoAchseRot(self.sprache, self.config['devices'][device_name], config, self.com_sammlung, self.test_mode, self.neustart, self.add_Ablauf, device_name) 
                        widget = NemoAchseRotWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, self.add_Ablauf, device_name, self.config['Function_Skip']['Generell_GamePad'])
                        color_Ant_n = color_Ant_n + 4
                    self.PadAchsenList.append(widget)
                elif device_typ == 'Monitoring':
                    if 'Nemo-Gase' in device_name:
                        device = NemoGase(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.add_Ablauf, device_name)
                        widget = NemoGaseWidget(self.sprache, Frame_Anzeige, device_typ_widget, self.config['devices'][device_name], config, self.add_Ablauf, device_name)
                
                ### Alle Coms merken:
                ak_com = self.config['devices'][device_name]['serial-interface']['port']
                if not ak_com in self.com_sammlung:
                    if not self.test_mode:
                        self.com_sammlung.update({ak_com: device.serial})
                    mutex = QMutex()
                    logger.debug(f"{ak_com} {self.Log_Text_10_str[self.sprache]} {mutex}")   
                    self.mutexs.update({ak_com: mutex})

                ### Menüleisten-Tab Init und Limit:
                try:
                    self.main_window.add_menu('Init', device_name, widget.init_device, widget.init)
                except Exception as e:
                    logger.exception(f'{device_name} - {self.Log_Text_11_str[self.sprache]}')
                if not 'Nemo-Gase' in device_name:
                    try:
                        self.main_window.add_menu('Limit', device_name, widget.update_Limit, widget.init)
                    except Exception as e:
                        logger.exception(f'{device_name} - {self.Log_Text_204_str[self.sprache]}')
                
                ### Speichern der Informationen/Zuweisungen:
                self.devices.update({device_name: device})
                self.widgets.update({device_name: widget})
                #### Ist der Port Null, wird keine Verbindung hergestellt:
                if not self.config["devices"][device_name]['multilog']['write_port'] == 0:
                    self.port_List_send.append(self.config["devices"][device_name]['multilog']['write_port'])
                    self.trigger_send.update({device_name: self.config['devices'][device_name]['multilog']['write_trigger']})
                if not 'Nemo-Gase' in device_name:    
                    if not self.config["devices"][device_name]['multilog']['read_port'] == 0:
                        self.port_List_read.append(self.config["devices"][device_name]['multilog']['read_port'])
                        self.trigger_read.update({self.config["devices"][device_name]['multilog']['read_port']: [self.config['devices'][device_name]['multilog']['read_trigger'], device_name]})
    
        logger.debug(f"{self.mutexs}")

        #---------------------------------------------------------------------------
        # Multilog Trigger Thread erstellen:
        #--------------------------------------------------------------------------
        self.Multilog_Nutzung = self.config['Function_Skip']['Multilog_Link']
        if self.Multilog_Nutzung:
            self.LinkMultilogThread = QThread()
            self.MultiLink = Multilog(self.sprache, self.port_List_send, self.port_List_read, self.add_Ablauf, self.widgets, self.devices, self.trigger_send, self.trigger_read)
            self.MultiLink.moveToThread(self.LinkMultilogThread)
            self.LinkMultilogThread.start()
            self.signal_Multilog.connect(self.MultiLink.event_Loop)
            self.signal_Multilog.emit()

        #---------------------------------------------------------------------------
        # Hardware Controller erstellen:
        #--------------------------------------------------------------------------
        self.Gamepad_Nutzung = self.config['Function_Skip']['Generell_GamePad']
        if self.Gamepad_Nutzung:
            self.PadThread = QThread()
            try:
                self.gamepad = Gamepad_1(self.sprache, self.PadAchsenList, self.add_Ablauf)
                logger.debug(f"{self.gamepad.name} {self.Log_Text_13_str[self.sprache]} {self.PadThread}") 
                self.gamepad.moveToThread(self.PadThread)
                logger.info(self.Log_Text_223_str[self.sprache]) 
                self.PadThread.start()
                self.signal_gamepad.connect(self.gamepad.event_Loop)
                self.signal_gamepad.emit()
            except:
                logger.warning(f'{self.Log_Text_222_str[self.sprache]}')
                self.Gamepad_Nutzung = False

        #---------------------------------------------------------------------------
        # Threads erstellen:
        #--------------------------------------------------------------------------
        logger.debug(self.Log_Text_12_str[self.sprache])
        self.samplers = []  
        self.threads = []
        for device in self.devices:
            thread = QThread()   
            logger.debug(f"{device} {self.Log_Text_13_str[self.sprache]} {thread}")                                                                                                            # Erstelle Thread
            dev_mutex = self.mutexs[self.config['devices'][device]['serial-interface']['port']]
            sampler = Sampler(self.devices[device], device, self.widgets[device], self.main_window.device_action[device], self.start_time, test_mode, dev_mutex)    # Erstelle Sampler-Objekt
            sampler.moveToThread(thread)                                                                                                                            # Verknüpfe Sampler-Objekt mit dem Thread
            sampler.signal.connect(self.update_view)                                                                                                                # Verknüpfe Sampler_Signal mit update_view Funtkion
            self.signal_sample_main.connect(sampler.sample)                                                                                                         # Verknüpfe Signal mit sampler-Funktion des Sampler-Objektes    
            self.samplers.append(sampler)
            self.threads.append(thread) 

        #---------------------------------------------------------------------------
        # Datein erstellen:
        #--------------------------------------------------------------------------
        ## Messdaten-Ordner erstellen:
        if not self.test_mode:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            for i in range(100):
                if i == 99:
                    raise ValueError(self.err_Text_1[self.sprache])
                self.directory = f"{self.output_dir}/measdata_{date}_#{i+1:02}"
                if not os.path.exists(self.directory):
                    os.makedirs(self.directory)
                    break

            ## Datei für Wert-Änderungen und Knopf-Betätigungen:
            self.txtDat_btn = f'{self.directory}/Ablauf.txt'
            with open(self.txtDat_btn,'w', encoding="utf-8") as f:
                f.write(f'{self.Text_2_str[self.sprache]}\n')
                f.write(f'{self.Text_3_str[self.sprache]}\n\n')

            ## Messdaten-Datein:
            for device in self.devices:
                self.devices[device].messdaten_output(self.directory)

            ## Config und Log speichern:
            self.save_config    = self.config['save']['config_save']
            self.save_log       = self.config['save']['log_save']
            self.save_plot      = self.config['save']['plot_save']
            self.save_GUI       = self.config['save']['GUI_save']
        else:
            self.save_config    = False
            self.save_log       = False
            self.save_plot      = False
            self.save_GUI       = False

        #---------------------------------------------------------------------------
        # Extra Variablen:
        #---------------------------------------------------------------------------
        self.anzExcecute = 0    # Zähle wie oft die Thread-Signale aufgerufen werden

        #---------------------------------------------------------------------------
        # Starte Timer und Thread:
        #--------------------------------------------------------------------------
        for thread in self.threads:
            thread.start()    
        logger.info(f"{self.Log_Text_14_str[self.sprache]} - {self.timer_check_device}")  
        self.timer_check_device.start()

        #---------------------------------------------------------------------------
        # Starte die Anwendung und zeige die GUI:
        #---------------------------------------------------------------------------
        self.main_window.show()
        logger.info(f'{self.Log_Text_251_str[self.sprache]} - {self.main_window.geometry()}')
        for widget in self.widgets:
            if not 'Nemo-Gase' in widget:
                logger.info(f'{self.Log_Text_252_str[self.sprache]}: {widget} - {self.widgets[widget].geometry()}')
        sys.exit(app.exec())

    ##########################################
    # Betrachtung der Labels und Plots:
    ##########################################
    def update_view(self, y_values, x_value, name):
        ''' Verbundene Funktion mit dem Sampler-Signal! Update der Graphen.
        Erklärung für die Umsetzung so (Vorher Aufruf der Funktion update_GUI in der sample-Funktion der Sampler-Klasse):
        - https://github.com/pyqtgraph/pyqtgraph/issues/1398
        - https://stackoverflow.com/questions/64307813/pyqtgraph-stops-updating-and-freezes-when-grapahing-live-sensor-data/64520032#64520032

        Args:
            y_values (dict):    Alle Messgrößen
            x_value (list):     Alle Zeiten zun den Messgrößen
            name (str):         Geräte-Name
        '''
        try:
            logger.debug(f"{self.Log_Text_15_str[self.sprache]} {name}")
            self.widgets[name].update_GUI(y_values, x_value) 
        except Exception as e:
            logger.exception(f"{self.Log_Text_16_str[self.sprache]} {name}.")

    ##########################################
    # Aufruf der Threads:
    ##########################################
    def ckeck_device(self):
        ''' Ruft die Geräte auf über einen Timer auf. Durch die Verbindung des Signals mit allen sample-Funktionen der Sampler-Objekte, werden
        all diese aufgerufen. Durch die Verbindung des Objektes mit dem Thread, wird diese Funktion im Thread aufgerufen. '''
        logging.debug(self.Log_Text_17_str[self.sprache])
        self.anzExcecute += 1
        self.signal_sample_main.emit()

    ############################################################################
    # Reaktion auf Buttons aus typen.py oder main_window.py:
    ############################################################################
    def exit(self):
        ''' Wird beim schließen der Anwendung aufgerufen und beendet die Threads. '''
        #////////////////////////////////////////////////////////////
        # Informationen zum Exit - Teil 1:
        #////////////////////////////////////////////////////////////
        time1 = datetime.datetime.now(datetime.timezone.utc).astimezone()   # Messung der Zeit für das Beenden der Anwednung
        ## Notizen in Datein:
        self.add_Ablauf(self.Text_4_str[self.sprache])
        logging.debug(self.Log_Text_End_str[self.sprache])
        #////////////////////////////////////////////////////////////
        # Beende Sample-Timer für Geräte-Threads:
        #////////////////////////////////////////////////////////////
        self.timer_check_device.stop()
        time.sleep(1)                                                       # Verzögerung um die sampling Aufträge zu beenden (in Threads)
        #////////////////////////////////////////////////////////////
        # Beennde PID:
        #////////////////////////////////////////////////////////////
        for device in self.widgets:
            if 'Eurotherm' in device:
                self.widgets[device].write_value['PID'] = False 
                self.devices[device].PIDThread.quit()
                self.devices[device].timer_PID.stop()
        #////////////////////////////////////////////////////////////
        # Sicheren Endzustand herstellen:
        #////////////////////////////////////////////////////////////
        ## Rufe Stopp-Befehle und setze End-Variable auf und sende Threads ein letztes Mal:
        ### Stopp - Beendigung von Teilen im Programm
        ### End-Variable - Sicheres Auslösen bzw. Setzen der nötigen Aufgaben
        for device in self.widgets:
            if not 'Nemo-Gase' in device:
                if self.config['devices'][device]['ende']:
                    self.devices[device].Save_End_State = True
                    self.widgets[device].Stopp(n=5)
        self.ckeck_device()
        time.sleep(1)                                                   # Verzögerung um die sampling Aufträge zu beenden bzw. überhaupt zu starten (in Threads)              
        #////////////////////////////////////////////////////////////
        # Beende die Threads - Teil 1:
        #////////////////////////////////////////////////////////////
        if self.Multilog_Nutzung:
            logger.debug(f"{self.Log_Text_208_str[self.sprache]} {self.LinkMultilogThread}")
            self.LinkMultilogThread.quit()
            if not self.MultiLink.done:
                self.MultiLink.ende()
        if self.Gamepad_Nutzung:
            self.PadThread.quit()
            self.gamepad.ende()
        #////////////////////////////////////////////////////////////
        # Schaue ob alle Sample-Aufträge tatsächlich zu Ende sind:
        #////////////////////////////////////////////////////////////
        ## Lesen von Werten abschalten:
        for sampler in self.samplers:
            sampler.messTime = 0
            sampler.exit = True
        ## Thread abschließen:
        ''' Info: Durch das Gamepad (pygame) kann es zu Verzögerungen kommen! Noch überarbeiten!'''
        while 1: 
            not_done = False
            for sampler in self.samplers:
                if not sampler.end_done:
                    not_done = True
            if not not_done:
                break
        #////////////////////////////////////////////////////////////
        # Beende die Threads - Teil 2:
        #////////////////////////////////////////////////////////////
        for thread in self.threads:
            logger.debug(f"{self.Log_Text_18_str[self.sprache]} {thread}")
            thread.quit()
        #////////////////////////////////////////////////////////////
        # Schließe Ports, wenn offen:
        #////////////////////////////////////////////////////////////
        if not self.test_mode:
            for device in self.devices:
                if self.devices[device].serial.is_open:
                    logger.debug(f"{self.Log_Text_19_str[self.sprache]} {device}")
                    self.devices[device].serial.close()
        #////////////////////////////////////////////////////////////
        # Speichere Datein:
        #////////////////////////////////////////////////////////////
        ## Speicher Config-Datei:
        if not self.test_mode:
            VerschiebePfad = self.directory
        if self.save_config:
            logger.debug(f"{self.Log_Text_20_str[self.sprache]} {VerschiebePfad}")
            Bild_Pfad = self.config_pfad
            Erg_Bild_Name = '/config.yml'
            shutil.copyfile(Bild_Pfad, VerschiebePfad + Erg_Bild_Name)
        ## Speicher Log-Datei:
        if self.save_log:
            logger.debug(f"{self.Log_Text_21_str[self.sprache]} {VerschiebePfad}")
            Bild_Pfad = self.config["logging"]['filename']
            Erg_Bild_Name = f'/{self.config["logging"]["filename"]}'
            shutil.copyfile(Bild_Pfad, VerschiebePfad + Erg_Bild_Name)
        ## Speichere Plot:
        if self.save_plot:
            for typ in self.tab_Teile:
                if not typ == 'Monitoring':
                    logger.debug(f"{self.Log_Text_22_str[self.sprache]} {typ}-{self.Log_Text_23_str[self.sprache]} {VerschiebePfad}")
                    self.tab_Teile[typ].plot.save_plot(f'{VerschiebePfad}/{typ}_Plot.png')
                    if self.tab_Teile[typ].legend_ops['legend_pos'].upper() == 'SIDE':
                        self.tab_Teile[typ].save_legend(f'{VerschiebePfad}/{typ}_Plot.png')
        ## Speichere GUI:
        if self.save_GUI:
            logger.debug(f"{self.Log_Text_S_GUI[self.sprache]} {VerschiebePfad}")
            saveGUI = self.main_window.grab()
            saveGUI.save(f'{VerschiebePfad}/GUI.png')
        #////////////////////////////////////////////////////////////
        # Informationen zum Exit - Teil 2:
        #////////////////////////////////////////////////////////////
        time2 = datetime.datetime.now(datetime.timezone.utc).astimezone()           # Messung der Zeit für das Beenden der Anwednung
        timediff = (
                time2 - time1
            ).total_seconds()
        logging.info(f'{self.Log_Text_300_str[self.sprache]} {time1} {self.Log_Text_301_str[self.sprache]} {time2} - {self.Log_Text_302_str[self.sprache]} {timediff} {self.Log_Text_303_str[self.sprache]}')
        logging.info(f'{self.Log_Text_304_str[self.sprache]} {self.anzExcecute}')

    def stopp_all(self, typ):
        ''' Funktion um ein Signal zu schreiben, das dann alle Achsen stopped!

        Args:
            typ (str):  Typ des Gerätes. 
        '''
        logger.debug(self.Log_Text_24_str[self.sprache])
        self.add_Ablauf(f'{self.Text_5_str[self.sprache]} {typ} {self.Text_6_str[self.sprache]}')
        for worker in self.samplers:
            if worker.device.typ == typ:
                worker.device_widget.Stopp(3)

    def synchro_achse(self): 
        ''' Lässt bestimmte Achsen synchron (gleichzeitig) sich bewegen. '''
        achse = []
        error = False
        eingabe_error = False
        logger.debug(self.Log_Text_25_str[self.sprache])
        self.add_Ablauf(self.Text_7_str[self.sprache])
        for worker in self.samplers:
            if worker.device.typ == 'Antrieb':
                if worker.device_widget.Auswahl.isChecked():
                    if 'PI-Achse' in worker.device_name:
                        if not worker.device_widget.RB_choise_absPos.isChecked():
                            error = True
                        controlle_1, controlle_2 = worker.device_widget.controll_value()
                        if controlle_1 == '' or controlle_2 == '':
                            eingabe_error = True
                            break
                    else:
                        if worker.device_widget.controll_value() == '':
                            eingabe_error = True
                            break
                    achse.append(worker)
        if error:
            for worker in achse:
                    worker.device_widget.Fehler_Output(1, worker.device_widget.La_error_1, self.err_Text_2[self.sprache])
        else:
            if not eingabe_error:
                for worker in achse:
                        worker.device_widget.fahre_links()

    def sync_rezept(self):
        '''Startet ausgewählte Rezepte synchron'''
        error = []
        devices = []
        logger.debug(self.Log_Text_26_str[self.sprache])
        self.add_Ablauf(self.Text_8_str[self.sprache])
        for worker in self.samplers:
            if not 'Nemo-Gase' in worker.device_widget.device_name:
                if worker.device_widget.Auswahl.isChecked() and worker.device_widget.init:
                    error.append(worker.device_widget.Rezept_lesen_controll())
                    devices.append(worker)
                    if worker.device_widget.cb_Rezept.currentText() == '------------':
                        error.append(True)
                        if 'Achse' in worker.device_widget.device_name: # PI-Achse, Nemo-Achse-Rotation, Nemo-Achse-Linear
                            worker.device_widget.Fehler_Output(1, worker.device_widget.La_error_1, worker.device_widget.err_15_str[worker.device_widget.sprache])
                        else: # TruHeat, Eurotherm
                            worker.device_widget.Fehler_Output(1, worker.device_widget.err_15_str[worker.device_widget.sprache])
        if not True in error:
            for worker in devices:
                worker.device_widget.RezStart(execute=2)  
    
    def sync_end_rezept(self):
        '''Beendet die ausgewählten Rezepte synchron'''
        devices = []
        logger.debug(self.Log_Text_203_str[self.sprache])
        self.add_Ablauf(self.Text_79_str[self.sprache])
        for worker in self.samplers:
            if not 'Nemo-Gase' in worker.device_widget.device_name:
                if worker.device_widget.Auswahl.isChecked():
                    devices.append(worker)
        for worker in devices:
            if'Nemo-Achse' in worker.device_widget.device_name or 'PI-Achse' in worker.device_widget.device_name:
                worker.device_widget.Stopp(4)
            else:
                worker.device_widget.RezEnde(excecute=4) 

    def rezept_einlesen(self):
        '''Liest die Config-datei wegen der Rezepte neu aus'''
        self.add_Ablauf(self.Text_9_str[self.sprache])
        for worker in self.samplers:
            if not 'Nemo-Gase' in worker.device_widget.device_name:
                worker.device_widget.update_rezept()        

        # Aktuelle Config-Datei notieren:
        with open(self.config_pfad, encoding="utf-8") as f:
            logger.info(f"{self.Log_Text_27_str[self.sprache]} {yaml.safe_load(f)}")  

    ##########################################
    # Erweiterung von Text-Datein:
    ##########################################
    def add_Ablauf(self, text):
        ''' Hinzufügen einer Zeile in die Ablauf-Datei. 

        Args:
            text (str):     Was zum Zeitpunkt passiert bzw. betätigt wurde. 
        '''
        if not self.test_mode:
            timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec='milliseconds').replace('T', ' ')
            with open(self.txtDat_btn,'a', encoding="utf-8") as f:
                f.write(f'{timestamp} - {text}\n')
        
def main(config, output_dir, test_mode, neustart):
    """ Um Vifcon zu starten, diese Funktion ausführen.

    Args:
        config (str):       File Pfad vom Configurations File.
        output_dir (str):   Verzeichnis, wo die Outputs hingelegt werden sollen.
        test_mode (bool):   Test Mode Aktiv.
    """
    ctrl = Controller(config, output_dir, test_mode, neustart)

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''