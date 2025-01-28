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
import matplotlib
import randomcolor            

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
        self.Log_Text_1_PID = ['PID-Modus gilt als gesperrt! PID-Parameter nicht richtig!',         'PID mode is locked! PID parameters not correct!']

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

            if 'Nemo' in self.device_name and not port and self.exit and self.device.init:  # Bei Erfolgreichen Test, Port als offen ansehen!!
                check1 = self.device.Test_Connection()
                check2 = self.device.serial.is_open
                if check1 and check2:   port = True
                else:                   port = False

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
                if not 'Nemo-Gase' in self.device_name and not 'Educrys-Monitoring' in self.device_name:
                    if self.device.PID.PID_speere and self.device_widget.write_task['PID']:
                        self.device_widget.PID_cb.setChecked(False)
                        self.device_widget.PID_ON_OFF()
                        if 'Achse' in self.device_name:  self.device_widget.Fehler_Output(1, self.device_widget.La_error_1, self.Log_Text_1_PID[self.sprache])
                        else:                            self.device_widget.Fehler_Output(1, self.Log_Text_1_PID[self.sprache])
                #if self.device_widget.send_betätigt:                                               # Ruft nun immer die write Funktion auf!
                if not self.test and not 'Nemo-Gase' in self.device_name and not 'Educrys-Monitoring' in self.device_name:
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
                        self.device_widget.check_verriegelung(self.device.read_TX('TV', 'V:'))
                if 'Eurotherm' in self.device_name and self.device.Safety == True:
                    # So bald sich im Gerät der HO ändert und die Leistung ausgewählt wurde oder der Menü-Knopf gedrückt wird, wird auch im Widget die Leistung geändert!
                    self.device_widget.oGOp = self.device.oGOp
                    TT_Pow = f'{self.device_widget.TTLimit[self.device_widget.sprache]} {self.device_widget.uGOp} ... {self.device_widget.oGOp} {self.device_widget.P_unit_einzel[self.device_widget.sprache]}'
                    self.device_widget.LE_Pow.setToolTip(TT_Pow)
                if ('Nemo-Achse' in self.device_name or 'PI-Achse' in self.device_name or 'Educrys-Achse' in self.device_name) and self.device.Limit_stop:
                    self.device_widget.BTN_Back(self.device.Limit_Stop_Text)
                    self.device.Limit_stop      = False
                    self.device.Limit_Stop_Text = -1
                elif ('Nemo-Achse' in self.device_name or 'Educrys-Achse' in self.device_name) and self.device.Limit_Stop_Text == 5:
                    self.device_widget.BTN_Back(self.device.Limit_Stop_Text)
                    self.device.Limit_Stop_Text = -1
                if ('TruHeat' in self.device_name or 'Eurotherm' in self.device_name or 'Nemo-Generator' in self.device_name) and self.device_widget.start_later:
                    self.device_widget.signal_Pop_up.emit()

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
                                if not 'Nemo-Achse-Linear' in self.device_name:  
                                    sample_values[key] =  128           # Bit 15 gesetzt - 0 bis 15 - Test-Modus
                                else:
                                    if self.device.Anlage == 2:         # Nemo-2 hat zwei Status-Listen (Bit 15 ist bei Liste 1 besetzt!!)
                                        if key == 'Status_2':     sample_values[key] = 128
                                        elif key == 'Status':     sample_values[key] = 0
                                        if key == 'StatusEil_2':  sample_values[key] = 128
                                        elif key == 'StatusEil':  sample_values[key] = 0
                                    else:                               # Nemo-1 hat nur eine Liste und brauch Status_2 nicht!
                                        if key == 'Status':       sample_values[key] = 128
                                        elif key == 'Status_2':   sample_values[key] = 0

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
        try:
            with open(config, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.warning('There is a problem with the config file (YAML). The program will be closed!\n')
            logger.warning('Error:')
            print(e)
            exit()
        
        #---------------------------------------------------------------------------
        # Sprachvariablen:
        #--------------------------------------------------------------------------
        ## Konfiguriere Sprache:
        try:
            if self.config['GUI']['language'].upper() == 'DE':
                logger.info('Sprache der GUI ist Deutsch!')
                self.sprache = 0
            elif self.config['GUI']['language'].upper() == 'EN':
                logger.info('The language of the GUI is English!')
                self.sprache = 1
            else:
                logger.warning('The language is not defined. Only German and English are defined in this program. Set language to English!')
                #print('Warning: The language is not defined. Only German and English are defined in this program. Set language to English!')
                self.sprache = 1
        except Exception as e:
            logger.warning('The language is not defined. Only German and English are defined in this program. Set language to English!')
            #print('Warning: The language is not defined. Only German and English are defined in this program. Set language to English!')
            logger.exception('Error reason:')
            self.sprache = 1
        
        ## Variablen: ##################################################################################################################################################################################################################################################################################
        main_window_tab_1_str   = ['Steuerung'  ,                                                                                                                                           'Control']
        main_window_tab_2_str   = ['Überwachung',                                                                                                                                           'Monitoring']
        TypA                    = ['Antriebe',                                                                                                                                              'Drives']
        TypG                    = ['Generatoren und Regler',                                                                                                                                'Generators and Controllers']
        ## Logging: ####################################################################################################################################################################################################################################################################################                                                    
        self.Log_Text_6_str     = ["Initialisiere VIFCON",                                                                                                                                  'Initialize VIFCON']
        self.Log_Text_7_str     = ['Konfiguration:',                                                                                                                                        'Configuration:']
        self.Log_Text_8_str     = ["Test Modus aktiv.",                                                                                                                                     "Test mode active."]
        self.Log_Text_9_str     = ['In der Config stimmt etwas nicht! Default Ein: Nur Warning in Konsole möglich.',                                                                        'Something is wrong in the config! Default On: Only warning in console possible.']
        self.Log_Text_10_str    = ['in QMutex',                                                                                                                                             'in QMutex']
        self.Log_Text_11_str    = ['Das Gerät konnte nicht in der Menüleiste Initialisierung erstellt werden!',                                                                             'The device could not be created in the initialization menu bar!']
        self.Log_Text_12_str    = ["Bereite Threads vor",                                                                                                                                   "Prepare threads"]
        self.Log_Text_13_str    = ['in Thread',                                                                                                                                             'in thread']
        self.Log_Text_14_str    = ['Start des Sampling-Timers',                                                                                                                             'Start of the sampling timer']
        self.Log_Text_15_str    = ['Update GUI von',                                                                                                                                        'Update GUI from']
        self.Log_Text_16_str    = ['Fehler beim Updaten der GUI im Gerät',                                                                                                                  'Error updating the GUI in the device']
        self.Log_Text_17_str    = ["Aufruf der Threads!",                                                                                                                                   "Calling the Threads!"]
        self.Log_Text_18_str    = ['Beende Thread',                                                                                                                                         'Quitting thread']
        self.Log_Text_19_str    = ['Schließe Port am Gerät',                                                                                                                                'Close port on device']
        self.Log_Text_20_str    = ['Kopiere Config-Datei in',                                                                                                                               'Copy config file to']
        self.Log_Text_21_str    = ['Kopiere Logging Datei in',                                                                                                                              'Copy logging file into']
        self.Log_Text_22_str    = ['Speichere Plot des',                                                                                                                                    'Save plot of']
        self.Log_Text_23_str    = ['Typs in',                                                                                                                                               'type in']
        self.Log_Text_24_str    = ['Stoppe alle Achsen!',                                                                                                                                   'Stop all axes!']
        self.Log_Text_25_str    = ['Achsen sollen synchron fahren!',                                                                                                                        'Axes should move synchronously!']
        self.Log_Text_26_str    = ['Synchro Rezept!',                                                                                                                                       'Synchro recipe!']
        self.Log_Text_27_str    = ['Update Konfiguration (Update Rezepte):',                                                                                                                'Update configuration (update recipes):']
        self.Log_Text_203_str   = ['Synchro Rezept Abschaltung!',                                                                                                                           'Synchro recipe shutdown!']
        self.Log_Text_204_str   = ['Das Gerät konnte nicht in der Menüleiste Limit oder Update VIFCON-PID-Parameter erstellt werden!',                                                      'The device could not be created in the menu bar Limit or Update VIFCON PID parameters!']
        self.Log_Text_208_str   = ['Beende Multilog Verbindung und Beende den Thread:',                                                                                                     'Close Multilog connection and end the thread:']
        self.Log_Text_222_str   = ['Der Aufbau mit dem Gamepad ist fehlgeschlagen!',                                                                                                        'The setup with the gamepad failed!']
        self.Log_Text_223_str   = ['Start des Gamepad-Threads!',                                                                                                                            'Start of the gamepad thread!']
        self.Log_Text_251_str   = ['Main-Window Größe (x-Koordinate, y-Koordinate, Breite, Höhe)',                                                                                          'Main window size (x coordinate, y coordinate, width, height)']
        self.Log_Text_252_str   = ['Geräte-Widget Größe (x-Koordinate, y-Koordinate, Breite, Höhe)',                                                                                        'Device widget size (x-coordinate, y-coordinate, width, height)']
        self.Log_Text_End_str   = ['Beenden Betätigt - Sicheren Zustand herstellen, Threads beenden, Ports schließen, Dateien und Plots speichern',                                         'Exit Activated - Establish a safe state, terminate threads, close ports, save files and plots']
        self.Log_Text_300_str   = ['Anwendung Schließen - Aufruf Exit - Von:',                                                                                                              'Application Close - Call Exit - From:']  
        self.Log_Text_301_str   = ['bis',                                                                                                                                                   'to']        
        self.Log_Text_302_str   = ['Gesamtdauer:',                                                                                                                                          'Total duration:']
        self.Log_Text_303_str   = ['s',                                                                                                                                                     's']
        self.Log_Text_304_str   = ['Aufruf der Threads bzw. der Funktion ckeck_device:',                                                                                                    'Calling the threads or the function ckeck_device:']
        self.Log_Text_305_str   = ['Startzeit:',                                                                                                                                            'Start time:']
        self.Log_Text_S_GUI     = ['Speichere die aktuell sichtbare GUI in',                                                                                                                'Save the currently visible GUI in']
        self.Log_Text_Color     = ['Definierte Farben aufgebraucht! Folgend werden nun neue zufällige Farben für die Kurven verwendet!',                                                    'Defined colors used up! New random colors will now be used for the curves!']
        self.Log_Text_Exit_str  = ['Die Timeout-Zeit wurde erreicht! Bearbeitung der Threads wird auf False gesetzt! Beachte das der Sichere Endzustand eventuell nicht erreicht wurde!!',  'The timeout has been reached! Thread processing is set to false! Note that the safe end state may not have been reached!!']
        self.Log_Device_1       = ['Das Gerät',                                                                                                                                             'The device']
        self.Log_Device_2       = ['gehört nicht zum Geräte-Typ Generator!',                                                                                                                'does not belong to the device type generator!']
        self.Log_Device_3       = ['gehört nicht zum Geräte-Typ Antrieb!',                                                                                                                  'does not belong to the device type drive!']
        self.Log_Device_4       = ['gehört nicht zum Geräte-Typ Monitoring!',                                                                                                               'does not belong to the monitoring device type!']
        self.Log_Yaml_Error     = ['Mit der Config-Datei (Yaml) gibt es ein Problem.',                                                                                                      'There is a problem with the config file (YAML).']
        self.Log_Yaml_Reason    = ['Fehlergrund:',                                                                                                                                          'Reason for the error']
        ## Error: ######################################################################################################################################################################################################################################################################################
        self.err_Text_1         = ['Zu hohe Verzeichnisanzahl.',                                                                                                                            "Too high directory count."]
        self.err_Text_2         = ['Synchron Modus benötigt\nAbsolute Positionierung (PI-Achse)!!',                                                                                         'Synchronous mode requires\nabsolute positioning (PI axis)!!']
        ## Ablaufdatei:                                  
        self.Text_2_str         = ['Ablauf der Messung:',                                                                                                                                   'Measuring process:']
        self.Text_3_str         = ['Werteingaben und Knopfberührungen',                                                                                                                     'Value entries and button touches']
        self.Text_4_str         = ['Exit-Knopf betätigt - Programm beendet!',                                                                                                               'Exit button pressed - program ended!']
        self.Text_5_str         = ['Knopf betätigt - Alle',                                                                                                                                 'Button pressed - All']
        self.Text_6_str         = ['stoppen!',                                                                                                                                              'stop!']
        self.Text_7_str         = ['Knopf betätigt - Synchrones Achsen Fahren!',                                                                                                            'Button pressed - synchronous axis movement!']
        self.Text_8_str         = ['Menü-Knopf betätigt - Synchro Rezepte Start!',                                                                                                          'Menu button pressed - Synchro recipes start!']
        self.Text_9_str         = ['Menü-Knopf betätigt - Rezepte Neu einlesen!',                                                                                                           'Menu button pressed - re-read recipes!']
        self.Text_79_str        = ['Menü-Knopf betätigt - Synchro Rezepte Ende!',                                                                                                           'Menu button pressed - Synchro recipes end!']
        ## Menü: #######################################################################################################################################################################################################################################################################################
        EuHO_Menu_str           = ['&HO lesen',                                                                                                                                             'Read &HO']
        EuPIDS_Menu_str         = ['PID-Parameter &schreiben',                                                                                                                              '&Write PID parameters']
        EuPIDR_Menu_str         = ['PID-Paramete&r lesen',                                                                                                                                  '&Read PID parameters']
        ## Config-Kontrolle: ###########################################################################################################################################################################################################################################################################
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                                                                      'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                                                         'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                                                                                                                               'The following types are possible:']
        self.Log_Pfad_conf_2_2  = ['Möglich sind die Schlüssel:',                                                                                                                           'The following keys are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                                                              'Default is used:']
        self.Log_Pfad_conf_3_1  = ['Default wird eingesetzt: Alle auf 1!',                                                                                                                  'Default is used: All on 1!']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',                                                                                                    'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                                                                                                                  '; Set to default:']
        self.Log_Pfad_conf_5_1  = ['; Keine Geräte konfigurieren!! Exit!',                                                                                                                  '; Do not configure any devices!! Exit!']
        self.Log_Pfad_conf_5_2  = ['; Keine Geräte konfigurieren!! Multilog-Link wird nicht erstellt!',                                                                                     '; Do not configure any devices!! Multilog link is not created!']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                                                          'Reason for error:']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                                                                  'Incorrect input:']
        self.Log_Pfad_conf_8_1  = ['Fehlerhafte Typ:',                                                                                                                                      'Incorrect type:']
        self.Log_Pfad_conf_8_2  = ['Fehlerhafte Schlüssel:',                                                                                                                                'Incorrect Key:']
        self.Log_Pfad_conf_9    = ['Folgende Größe wurde nicht in Konfiguration definiert, setze Skalierung auf Null:',                                                                     'The following size was not defined in configuration, set scaling to zero:']

        #--------------------------------------------------------------------------
        # Logging-Datei erstellen:
        #--------------------------------------------------------------------------
        ## Logging:
        ### Konfigurationscheck Logging:
        try: 
            logging.basicConfig(**self.config["logging"])
            self.log_Pfad = self.config["logging"]['filename']
        except Exception as e: 
            default_log_dict = {'level': 20, 'filename': 'vifcon.log', 'format': '%(asctime)s %(levelname)s %(name)s - %(message)s', 'filemode': 'w'} 
            self.log_Pfad = 'vifcon.log'
            logging.basicConfig(**default_log_dict)
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} logging {self.Log_Pfad_conf_5[self.sprache]} {default_log_dict}')
            print(f'{self.Log_Pfad_conf_4[self.sprache]} logging {self.Log_Pfad_conf_5[self.sprache]} {default_log_dict}')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
        ### Logging-Informationen:
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
        try: consolFormat = logging.Formatter(self.config['consol_Logging']['format'])
        except Exception as e: 
            consolFormat = logging.Formatter('%(asctime)s %(levelname)s %(name)s - %(message)s')
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} consol_Logging|format {self.Log_Pfad_conf_5[self.sprache]} %(asctime)s %(levelname)s %(name)s - %(message)s')
            print(f'{self.Log_Pfad_conf_4[self.sprache]} consol_Logging|format {self.Log_Pfad_conf_5[self.sprache]} %(asctime)s %(levelname)s %(name)s - %(message)s')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
        consoleHandler.setFormatter(consolFormat)
        ### Füge an bestehenden Handler:
        logger.addHandler(consoleHandler)
        ### Filter für den neuen Handler:
        try: ak_Level_Consol_Log = self.config['consol_Logging']['level']
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} consol_Logging|level {self.Log_Pfad_conf_5[self.sprache]} 30')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            ak_Level_Consol_Log = 30
        if not ak_Level_Consol_Log in [10, 20, 30, 40]:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} level - {self.Log_Pfad_conf_2[self.sprache]} [10, 20, 30, 40] - {self.Log_Pfad_conf_3[self.sprache]} 30 - {self.Log_Pfad_conf_8[self.sprache]} {ak_Level_Consol_Log}')
            ak_Level_Consol_Log = 30
        level_Log = {10: logging.DEBUG, 20: logging.INFO, 30: logging.WARNING, 40: logging.ERROR}
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        try: ak_Anzeige_Level = self.config['consol_Logging']['print']
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} consol_Logging|print {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            ak_Anzeige_Level = 1
        if not ak_Anzeige_Level in [1, 2, 3]:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} print - {self.Log_Pfad_conf_2[self.sprache]} [1, 2, 3] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8[self.sprache]} {ak_Anzeige_Level}')
            ak_Anzeige_Level = 1
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
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
        from .devices.nemoGenerator import NemoGenerator
        from .devices.educrysMonitoring import EducrysMon
        from .devices.educrysAntriebe import EducrysAntrieb
        from .devices.educrysHeizer import EducrysHeizer
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
        from .view.nemoGenerator import NemoGeneratortWidget
        from .view.educrysMonitoring import EducrysMonWidget
        from .view.educrysAntriebe import EducrysAntriebWidget
        from .view.educrysHeizer import EducrysHeizerWidget

        #---------------------------------------------------------------------------
        # Vorbereitung:
        #--------------------------------------------------------------------------
        ## Reaktionstimer:
        self.timer_check_device = QTimer()                                              # Reaktionszeittimer (ruft die Geräte auf, liest aber nur unter bestimmten Bedingungen!)
        ### Konfigurationscheck Reaktionszeit:
        try: reaktion_time = self.config["time"]["dt-main"]
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} time|dt-main {self.Log_Pfad_conf_5[self.sprache]} 150')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            reaktion_time = 150
        if not type(reaktion_time) in [int] or not reaktion_time >= 0:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} dt-main - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 150 - {self.Log_Pfad_conf_8[self.sprache]} {reaktion_time}')
            reaktion_time = 150 
        ### Timer setzen:
        self.timer_check_device.setInterval(reaktion_time)
        self.timer_check_device.timeout.connect(self.ckeck_device)

        ## Zeiten:
        self.start_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        logging.info(f'{self.Log_Text_305_str[self.sprache]} {self.start_time}')

        #---------------------------------------------------------------------------
        # Hauptteile der GUI erstellen:
        #--------------------------------------------------------------------------
        app = QApplication(sys.argv)
        
        ## Konfigurationen prüfen:
        ### Gamapad Aktiviuerung:
        try: gamepad_Link = self.config['Function_Skip']['Generell_GamePad']
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} Function_Skip|Generell_GamePad {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            gamepad_Link = False
        if not type(gamepad_Link) == bool and not gamepad_Link in [0,1]: 
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} Generell_GamePad - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {gamepad_Link}')
            gamepad_Link = 0
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        ### Read und Write Funktion Dauer Loggen:
        try: WriteReadTime = self.config['Function_Skip']['writereadTime']
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} Function_Skip|writereadTime {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            WriteReadTime = False
        if not type(WriteReadTime) == bool and not WriteReadTime in [0,1]: 
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} writereadTime - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {WriteReadTime}')
            WriteReadTime = 0
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        ### GUI Rahmen:
        try: Frame_Anzeige = self.config['GUI']['GUI_Frame'] 
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} GUI|GUI_Frame {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            Frame_Anzeige = False
        if not type(Frame_Anzeige) == bool and not Frame_Anzeige in [0,1]: 
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} GUI_Frame - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {Frame_Anzeige}')
            Frame_Anzeige = 0
        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        ### GUI Farben:
        try: Color_Anzeige = self.config['GUI']['GUI_color_Widget'] 
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} GUI|GUI_color_Widget {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            Color_Anzeige = False 
        if not type(Color_Anzeige) == bool and not Color_Anzeige in [0,1]: 
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} GUI_color_Widget - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {Color_Anzeige}')
            Color_Anzeige = 0 
        
        ## Hauptfenster:
        self.main_window = MainWindow(self.exit, self.sync_rezept, self.sync_end_rezept, self.rezept_einlesen, self.sprache, gamepad_Link)                                    

        ## Hauttabs erstellen:
        ### Haupttab Steuerung:
        self.tab_GenAnt = Splitter('H', True)
        self.main_window.add_tab(self.tab_GenAnt.splitter, main_window_tab_1_str[self.sprache])

        #### Konfigurationscheck Skalierungsfaktoren:
        default_scale = {'Pos': 1, 'Win': 1, 'Speed_1': 1, 'Speed_2': 1, 'WinSpeed': 1, 'Temp': 1, 'Op': 1, 
                         'Current': 1, 'Voltage': 1, 'Pow': 1, 'Freq': 1, 'Freq_2': 1, 'PIDA': 1, 'PIDG': 1} 
        try: scale = self.config['skalFak']
        except Exception as e:
            scale = default_scale
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} skalFak {self.Log_Pfad_conf_5[self.sprache]} {scale}')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
        size_List = ['Pos', 'Win', 'Speed_1', 'Speed_2', 'WinSpeed', 'Temp', 'Op', 'Current', 'Voltage', 'Pow', 'Freq', 'Freq_2', 'PIDA', 'PIDG']
        list_drin = []
        for size in scale:
            if not size in size_List:
                logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} skalFak - {self.Log_Pfad_conf_2_2[self.sprache]} {size_List} - {self.Log_Pfad_conf_3_1[self.sprache]} - {self.Log_Pfad_conf_8_2[self.sprache]} {size}')
                scale = default_scale
                break
            else:
                list_drin.append(size)
            if not type(scale[size]) in [float, int] or not scale[size] >= 0:
                logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} skalFak|{size} - {self.Log_Pfad_conf_2_1[self.sprache]} [Float, Integer] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8[self.sprache]} {scale[size]}')
                scale[size] = 1
        if not scale == default_scale:
            for size in size_List:
                if not size in list_drin:
                    logger.warning(f'{self.Log_Pfad_conf_9[self.sprache]} {size}')
                    scale.update({size: 0})

        #### Konfigurationscheck Legendentyp:
        try: legend_generator = self.config["legend"]["generator"]
        except Exception as e:
            legend_generator = {'legend_pos': 'Side', 'legend_anz': 2, 'side': 'rl'} 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|generator {self.Log_Pfad_conf_5[self.sprache]} {legend_generator}')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
        try: legend_antriebe = self.config["legend"]["antrieb"]
        except Exception as e:
            legend_antriebe = {'legend_pos': 'Side', 'legend_anz': 2, 'side': 'rl'} 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|generator {self.Log_Pfad_conf_5[self.sprache]} {legend_generator}')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')

        self.generator = Generator(self.start_time, self.tab_GenAnt.splitter, self.add_Ablauf, self.stopp_all, self.main_window.menu_dict, legend_generator, scale, self.sprache, Color_Anzeige)
        self.antrieb = Antrieb(self.start_time, self.tab_GenAnt.splitter, self.add_Ablauf, self.stopp_all, self.synchro_achse, self.main_window.menu_dict, legend_antriebe, scale, self.sprache, Color_Anzeige)

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

        ## Farb-Liste:
        used_Color_list = []
        for n in COLORS:
            used_Color_list.append(matplotlib.colors.cnames[n])
        used_Color_list.append(matplotlib.colors.cnames['red'])
        used_Color_list.append(matplotlib.colors.cnames['black'])

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

        überlaufA = False
        überlaufG = False

        ## Konfigurationscheck - Geräte:
        try: devices_dict_conf = self.config['devices']
        except Exception as e:
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} devices {self.Log_Pfad_conf_5_1[self.sprache]}')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            exit()
        
        ## Konfigurationscheck - Multilog-Link:
        try: multilog_Link = self.config['Function_Skip']['Multilog_Link']
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} Function_Skip|Multilog_Link {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            multilog_Link = False
        if not type(multilog_Link) == bool and not multilog_Link in [0,1]: 
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} Multilog_Link - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {gamepad_Link}')
            multilog_Link = 0

        ## Geräte Erstellung:
        for device_name in devices_dict_conf:
            jump = False
            try: skip = self.config['devices'][device_name]['skip']
            except Exception as e: 
                logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} {device_name}|skip {self.Log_Pfad_conf_5[self.sprache]} True')
                logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                skip = 1
            if not type(skip) == bool and not skip in [0,1]: 
                logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} skip ({device_name}) - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} True - {self.Log_Pfad_conf_8[self.sprache]} {skip}')
                skip = 1 

            if not skip:                                                                  # Wenn skip == True, dann überspringe die Erstellung
                ### Auswahl Farbe und Geräte-Typ:
                ak_color = []                                                             # zu übergebene Liste mit Farben
                color = 0                                                                 # Start-Listenwert 
                try: device_typ = self.config['devices'][device_name]['typ']              # Geräte-Typ
                except Exception as e: 
                    logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} {device_name}|typ {self.Log_Pfad_conf_5[self.sprache]} Generator')
                    logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                    device_typ = 'Generator'
                if not device_typ in ['Generator', 'Antrieb', 'Monitoring']:
                    logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} typ ({device_name}) - {self.Log_Pfad_conf_2[self.sprache]} [Generator, Antrieb, Monitoring] - {self.Log_Pfad_conf_3[self.sprache]} Generator - {self.Log_Pfad_conf_8[self.sprache]} {device_typ}')
                    device_typ = 'Generator' 
                device_typ_widget = self.tab_Teile[device_typ]                            # Geräte-Widget, an das das Gerät geaddet werden soll

                if device_typ == 'Generator':
                    color = color_Gen_n
                elif device_typ == 'Antrieb':
                    color = color_Ant_n
                for n in range(color,color+13,1):
                    try:
                        ak_color.append(COLORS[n])
                    except Exception as e:
                        # Wenn ein Überlauf der 23 Farben geschieht, werden zufällige Farben ausgewählt!
                        if not überlaufG and device_typ == 'Generator':
                            logger.warning(f'{self.Log_Text_Color[self.sprache]} ({TypG[self.sprache]})')
                            überlaufG = True
                        elif not überlaufA and device_typ == 'Antrieb':
                            logger.warning(f'{self.Log_Text_Color[self.sprache]} ({TypA[self.sprache]})')
                            überlaufA = True
                        while 1:
                            # Zufällige Farbe erzeugen, generieren und doppelte vermeiden:
                            farbe = randomcolor.RandomColor().generate()[0]
                            if not farbe in used_Color_list:
                                used_Color_list.append(farbe)
                                ak_color.append(farbe)
                                break   
                        
                ### Geräte erstellen:
                if device_typ == 'Generator':
                    if 'Eurotherm' in device_name:
                        #### Objekte erstellen:
                        device = Eurotherm(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf, device_name)
                        widget = EurothermWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, multilog_Link, self.add_Ablauf, device_name)
                        #### Menü-Sonder-Knöpfe:
                        ##### Lese HO:
                        menu_HO_Button = QAction(f'{device_name} - {EuHO_Menu_str[self.sprache]}', self)
                        menu_HO_Button.triggered.connect(widget.Lese_HO)
                        self.main_window.G_menu.addAction(menu_HO_Button)
                        ##### Lese PID:
                        menu_PIDR_Button = QAction(f'{device_name} - {EuPIDR_Menu_str[self.sprache]}', self)
                        menu_PIDR_Button.triggered.connect(widget.Read_PID)
                        self.main_window.G_menu.addAction(menu_PIDR_Button)
                        ##### Schreibe PID:
                        menu_PIDS_Button = QAction(f'{device_name} - {EuPIDS_Menu_str[self.sprache]}', self)
                        menu_PIDS_Button.triggered.connect(widget.Write_PID)
                        self.main_window.G_menu.addAction(menu_PIDS_Button)
                        #### Farben-Option:
                        color_Gen_n = color_Gen_n + 7
                    elif 'TruHeat' in device_name:
                        #### Objekte erstellen:
                        device = TruHeat(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf, device_name) 
                        widget = TruHeatWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, multilog_Link, self.add_Ablauf, device_name)
                        #### Farben-Option:
                        color_Gen_n = color_Gen_n + 13
                    elif 'Nemo-Generator' in device_name:
                        #### Objekte erstellen:
                        device = NemoGenerator(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf, device_name) 
                        widget = NemoGeneratortWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, multilog_Link, self.add_Ablauf, device_name)
                        #### Farben-Option:
                        color_Gen_n = color_Gen_n + 13
                    elif 'Educrys-Heizer' in device_name:
                        #### Objekte erstellen:
                        device = EducrysHeizer(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf, device_name) 
                        widget = EducrysHeizerWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, multilog_Link, self.add_Ablauf, device_name)
                        ##### Schreibe PID:
                        menu_PIDS_Button = QAction(f'{device_name} - {EuPIDS_Menu_str[self.sprache]}', self)
                        menu_PIDS_Button.triggered.connect(widget.Write_PID)
                        self.main_window.G_menu.addAction(menu_PIDS_Button)
                        #### Farben-Option:
                        color_Gen_n = color_Gen_n + 7
                    else:
                        logger.warning(f'{self.Log_Device_1[self.sprache]} {device_name} {self.Log_Device_2[self.sprache]}')
                        jump = True
                elif device_typ == 'Antrieb':
                    if 'PI-Achse' in device_name:
                        #### Objekte erstellen:
                        device = PIAchse(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf, device_name)
                        if device.init and not self.test_mode:
                            start_werte = device.read() 
                        else:
                            start_werte = {'IWv': '?', 'IWs': '?'}
                        widget = PIAchseWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, start_werte, self.neustart, multilog_Link, self.add_Ablauf, device_name, gamepad_Link)
                        #### Farben-Option:
                        color_Ant_n = color_Ant_n + 7
                    elif 'Nemo-Achse-Linear' in device_name:
                        #### Objekte erstellen:
                        device = NemoAchseLin(self.sprache, self.config['devices'][device_name], config, self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf,  device_name) 
                        widget = NemoAchseLinWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, multilog_Link, self.add_Ablauf, device_name, gamepad_Link)
                        #### Farben-Option:
                        color_Ant_n = color_Ant_n + 9
                    elif 'Nemo-Achse-Rotation' in device_name:
                        #### Objekte erstellen:
                        device = NemoAchseRot(self.sprache, self.config['devices'][device_name], config, self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf, device_name) 
                        widget = NemoAchseRotWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, multilog_Link, self.add_Ablauf, device_name, gamepad_Link)
                        #### Farben-Option:
                        color_Ant_n = color_Ant_n + 7
                    elif 'Educrys-Antrieb' in device_name:
                        #### Objekte erstellen:
                        device = EducrysAntrieb(self.sprache, self.config['devices'][device_name], config, self.com_sammlung, self.test_mode, self.neustart, multilog_Link, WriteReadTime, self.add_Ablauf,  device_name) 
                        widget = EducrysAntriebWidget(self.sprache, Frame_Anzeige, device_typ_widget, ak_color, self.config["devices"][device_name], config, self.neustart, multilog_Link, self.add_Ablauf, device_name, gamepad_Link)
                        #### Farben-Option:
                        color_Ant_n = color_Ant_n + 6
                    else:
                        logger.warning(f'{self.Log_Device_1[self.sprache]} {device_name} {self.Log_Device_3[self.sprache]}')
                        jump = True
                    if not jump: self.PadAchsenList.append(widget)
                elif device_typ == 'Monitoring':
                    if 'Nemo-Gase' in device_name:
                        #### Objekte erstellen:
                        device = NemoGase(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, WriteReadTime, self.add_Ablauf, device_name)
                        widget = NemoGaseWidget(self.sprache, Frame_Anzeige, device_typ_widget, self.config['devices'][device_name], config, self.add_Ablauf, device_name)
                    elif 'Educrys-Monitoring' in device_name:
                        #### Objekte erstellen:
                        device = EducrysMon(self.sprache, self.config['devices'][device_name], self.com_sammlung, self.test_mode, WriteReadTime, self.add_Ablauf, device_name)
                        widget = EducrysMonWidget(self.sprache, Frame_Anzeige, device_typ_widget, self.config['devices'][device_name], config, self.add_Ablauf, device_name)
                    else:
                        logger.warning(f'{self.Log_Device_1[self.sprache]} {device_name} {self.Log_Device_4[self.sprache]}')
                        jump = True

                if not jump:
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
                    if not 'Nemo-Gase' in device_name and not 'Educrys-Monitoring' in device_name:
                        try:
                            self.main_window.add_menu('Limit', device_name, widget.update_Limit, widget.init)
                            self.main_window.add_menu('VIFCON-PID', device_name, device.PID.update_VPID_Para, widget.init)
                            device.PID.config_dat = config
                            device.PID.widget = widget
                            self.main_window.add_menu('Reset-PID', device_name, widget.PID_Reset, widget.init)
                        except Exception as e:
                            logger.exception(f'{device_name} - {self.Log_Text_204_str[self.sprache]}')
                    
                    ### Speichern der Informationen/Zuweisungen:
                    self.devices.update({device_name: device})
                    self.widgets.update({device_name: widget})
                    #### Ist der Port Null, wird keine Verbindung hergestellt:
                    ##### Konfigurations Check:
                    try: write_port = self.config["devices"][device_name]['multilog']['write_port']
                    except Exception as e:
                        logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} multilog|write_port ({device_name}) {self.Log_Pfad_conf_5_2[self.sprache]}')
                        logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                        write_port = 0
                    if not type(write_port) == int or not write_port >= 0:
                        logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} write_port ({device_name}) - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {write_port}')
                        write_port = 0 
                    #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
                    try: write_trigger = self.config['devices'][device_name]['multilog']['write_trigger']
                    except Exception as e:
                        logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} multilog|write_trigger ({device_name}) {self.Log_Pfad_conf_5_2[self.sprache]}')
                        logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                        write_port = 0
                    if not 'Nemo-Gase' in device_name and not 'Educrys-Monitoring' in device_name:
                        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
                        try: read_port_ist = self.config["devices"][device_name]['multilog']['read_port_ist']
                        except Exception as e:
                            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} multilog|read_port_ist ({device_name}) {self.Log_Pfad_conf_5_2[self.sprache]}')
                            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                            read_port_ist = 0
                        if not type(read_port_ist) == int or not read_port_ist >= 0:
                            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} read_port_ist ({device_name}) - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {read_port_ist}')
                            read_port_ist = 0 
                        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
                        try: read_trigger_ist = self.config['devices'][device_name]['multilog']['read_trigger_ist']
                        except Exception as e:
                            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} multilog|read_trigger_ist ({device_name}) {self.Log_Pfad_conf_5_2[self.sprache]}')
                            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                            read_port_ist = 0
                        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
                        try: read_port_soll = self.config["devices"][device_name]['multilog']['read_port_soll']
                        except Exception as e:
                            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} multilog|read_port_soll ({device_name}) {self.Log_Pfad_conf_5_2[self.sprache]}')
                            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                            read_port_soll = 0
                        if not type(read_port_soll) == int or not read_port_soll >= 0:
                            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} read_port_soll ({device_name}) - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {read_port_soll}')
                            read_port_soll = 0 
                        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
                        try: read_trigger_soll = self.config['devices'][device_name]['multilog']['read_trigger_soll']
                        except Exception as e:
                            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} multilog|read_trigger_soll ({device_name}) {self.Log_Pfad_conf_5_2[self.sprache]}')
                            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                            read_port_soll = 0
                    
                    ##### Ports setzen:
                    if not write_port == 0:
                        self.port_List_send.append(write_port)
                        self.trigger_send.update({device_name: write_trigger})
                    if not 'Nemo-Gase' in device_name and not 'Educrys-Monitoring' in device_name:    
                        if not read_port_ist == 0:
                            self.port_List_read.append(read_port_ist)
                            self.trigger_read.update({read_port_ist: [read_trigger_ist, device_name]})
                        if not read_port_soll == 0:
                            self.port_List_read.append(read_port_soll)
                            self.trigger_read.update({read_port_soll: [read_trigger_soll, device_name]})
        
        logger.debug(f"{self.mutexs}")

        #---------------------------------------------------------------------------
        # Multilog Trigger Thread erstellen:
        #--------------------------------------------------------------------------
        self.Multilog_Nutzung = multilog_Link
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
        self.Gamepad_Nutzung = gamepad_Link
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
            try: self.save_config    = self.config['save']['config_save']
            except Exception as e: 
                logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} save|config_save {self.Log_Pfad_conf_5[self.sprache]} True')
                logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                self.save_config = True 
            if not type(self.save_config) == bool and not self.save_config in [0,1]: 
                logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} config_save - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} True - {self.Log_Pfad_conf_8[self.sprache]} {self.save_config}')
                self.save_config = 1
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            try: self.save_log       = self.config['save']['log_save']
            except Exception as e: 
                logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} save|log_save {self.Log_Pfad_conf_5[self.sprache]} True')
                logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                self.save_log = True 
            if not type(self.save_log) == bool and not self.save_log in [0,1]: 
                logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} log_save - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} True - {self.Log_Pfad_conf_8[self.sprache]} {self.save_log}')
                self.save_log = 1
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            try: self.save_plot      = self.config['save']['plot_save']
            except Exception as e: 
                logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} save|plot_save {self.Log_Pfad_conf_5[self.sprache]} True')
                logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                self.save_plot = True 
            if not type(self.save_plot) == bool and not self.save_plot in [0,1]: 
                logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} plot_save - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} True - {self.Log_Pfad_conf_8[self.sprache]} {self.save_plot}')
                self.save_plot = 1
            #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            try: self.save_GUI       = self.config['save']['GUI_save']
            except Exception as e: 
                logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} save|GUI_save {self.Log_Pfad_conf_5[self.sprache]} False')
                logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                self.save_GUI = False 
            if not type(self.save_GUI) == bool and not self.save_GUI in [0,1]: 
                logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} GUI_save - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.save_GUI}')
                self.save_GUI = 0
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
            if not 'Nemo-Gase' in widget and not 'Educrys-Monitoring' in widget:
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
            if not 'Nemo-Gase' in device and not 'Educrys-Monitoring' in device:
                self.widgets[device].write_task['PID'] = False 
                if self.devices[device].PID_Aktiv:
                    self.devices[device].PIDThread.quit()
                    self.devices[device].timer_PID.stop()
        #////////////////////////////////////////////////////////////
        # Sicheren Endzustand herstellen:
        #////////////////////////////////////////////////////////////
        ## Rufe Stopp-Befehle und setze End-Variable auf und sende Threads ein letztes Mal:
        ### Stopp - Beendigung von Teilen im Programm
        ### End-Variable - Sicheres Auslösen bzw. Setzen der nötigen Aufgaben
        for device in self.widgets:
            if not 'Nemo-Gase' in device and not 'Educrys-Monitoring' in device:
                #### Konfigurationscheck:
                try: save_ende = self.config['devices'][device]['ende']
                except Exception as e:
                    logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} {device}|ende {self.Log_Pfad_conf_5[self.sprache]} True')
                    logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
                    save_ende = True 
                if not type(save_ende) == bool and not save_ende in [0,1]: 
                    logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} ende ({device}) - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} True - {self.Log_Pfad_conf_8[self.sprache]} {save_ende}')
                    save_ende = 1
                #### Ausführung:
                if save_ende:
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
        ### Timeout setzen:
        try:    timeout = float(str(self.config["time"]["timeout_exit"]).replace(',','.')) 
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} time|timeout_exit {self.Log_Pfad_conf_5[self.sprache]} 10')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            timeout = 10    # Sekunden  
        if not type(timeout) in [float,int] or not timeout >= 0:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} timeout_exit - {self.Log_Pfad_conf_2_1[self.sprache]} [Float, Integer] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 10 - {self.Log_Pfad_conf_8[self.sprache]} {timeout}')
            timeout = 10
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        ### While-Schleife um die Threads sicher abzuarbeiten:
        while 1: 
            not_done = False
            for sampler in self.samplers:
                if not sampler.end_done:
                    not_done = True
            if not not_done:
                break
            #### Timeout:
            self.time = datetime.datetime.now(datetime.timezone.utc).astimezone()
            timediff = (self.time - ak_time).total_seconds()                                                       
            if timediff >= timeout:
                logger.warning(self.Log_Text_Exit_str[self.sprache])
                for sampler in self.samplers:
                    sampler.port = False
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
            Bild_Pfad = self.log_Pfad
            Erg_Bild_Name = f'/{self.log_Pfad}'
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
            if not 'Nemo-Gase' in worker.device_widget.device_name and not 'Educrys-Monitoring' in worker.device_widget.device_name:
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
            if not 'Nemo-Gase' in worker.device_widget.device_name and not 'Educrys-Monitoring' in worker.device_widget.device_name:
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
            if not 'Nemo-Gase' in worker.device_widget.device_name and not 'Educrys-Monitoring' in worker.device_widget.device_name:
                worker.device_widget.update_rezept()        

        # Aktuelle Config-Datei notieren:
        try:
            with open(self.config_pfad, encoding="utf-8") as f:
                logger.info(f"{self.Log_Text_27_str[self.sprache]} {yaml.safe_load(f)}")  
        except Exception as e: 
            logger.warning(f'{self.Log_Yaml_Error[self.sprache]}')
            logger.exception(f'{self.Log_Yaml_Reason[self.sprache]}')

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