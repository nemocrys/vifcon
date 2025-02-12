# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Gamepad Controller initialisieren:
- Ertsellt eine While-Schleife, die die Aktionen des Gamepads ausliest und dann Funktionen der Antriebe auslöst.
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
import pygame
import datetime

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)

pygame.init()

class Gamepad_1(QObject):
    '''Quelle: https://www.pygame.org/docs/ref/joystick.html'''
    def __init__(self, sprache, Achsen_list, Ablauf_Funktion):
        ''' Nutzung eines Gamepads
        
        Args:
            sprache (int):              Sprache der GUI (Listenplatz)
            Achsen_list (list):         Verbundene Achsen-Widgets
            Ablauf_Funktion (function): Funktion zur Erweiterung einer Textdatei
        '''
        super().__init__()
        
        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Init:
        self.sprache                    = sprache
        self.Achsen_list                = Achsen_list                          # Verbundene Achsen
        self.add_Text_To_Ablauf_Datei   = Ablauf_Funktion

        ## Andere:
        self.done = False

        #---------------------------------------------------------------------------
        # Sprachvariablen:
        #--------------------------------------------------------------------------
        ## Logging:                                                     
        self.Log_Text_224_str       = ["Gamepad",                                                               'Gamepad']
        self.Log_Text_225_str       = ['Anzahl:',                                                               'Amount:']
        self.Log_Text_226_str       = ['Name:',                                                                 'Name:']
        self.Log_Text_227_str       = ['GUID:',                                                                 'GUID:']
        self.Log_Text_228_str       = ['Leistungspegel:',                                                       'Power level:']
        self.Log_Text_229_str       = ['Anzahl der Achsen:',                                                    'Number of axes:']
        self.Log_Text_230_str       = ['Anzahl der Knöpfe:',                                                    'Number of buttons:']
        self.Log_Text_231_str       = ['Anzahl der Bediensticks:',                                              'Number of control sticks:']
        self.Log_Text_232_str       = ['Event:',                                                                'Event:']
        self.Log_Text_233_str       = ['verbunden',                                                             'connected']
        self.Log_Text_234_str       = ['Knopf betätigt - X!',                                                   'Button pressed - X!']
        self.Log_Text_235_str       = ['Knopf betätigt - A!',                                                   'Button pressed - A!']
        self.Log_Text_236_str       = ['Knopf betätigt - B!',                                                   'Button pressed - B!']
        self.Log_Text_237_str       = ['Knopf betätigt - Y!',                                                   'Button pressed - Y!']
        self.Log_Text_238_str       = ['Knopf betätigt - L!',                                                   'Button pressed - L!']
        self.Log_Text_239_str       = ['Knopf betätigt - R!',                                                   'Button pressed - R!']
        self.Log_Text_240_str       = ['Knopf betätigt - Select!',                                              'Button pressed - Select!']
        self.Log_Text_241_str       = ['Knopf betätigt - Start!',                                               'Button pressed - Start!']
        self.Log_Text_242_str       = ['Knopf betätigt - Achse Hoch!',                                          'Button pressed - axes up!']                                          
        self.Log_Text_243_str       = ['Knopf betätigt - Achse Runter!',                                        'Button pressed - axes down!']                                          
        self.Log_Text_244_str       = ['Knopf betätigt - Achse Rechts!',                                        'Button pressed - axes right!']                                          
        self.Log_Text_245_str       = ['Knopf betätigt - Achse Links!',                                         'Button pressed - axes left!']                                          
        #---------------------------------------
        # Informationen:
        #---------------------------------------
        joystick_count = pygame.joystick.get_count()
        logger.info(f"{self.Log_Text_224_str[self.sprache]} - {self.Log_Text_225_str[self.sprache]} {joystick_count}")

        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                self.joystick = joy
                logger.info(f"{self.Log_Text_224_str[self.sprache]} {joy.get_instance_id()} {self.Log_Text_233_str[self.sprache]}")

        ## Informationen für die Joysticks:
        self.name = self.joystick.get_name()
        logger.info(f"{self.Log_Text_224_str[self.sprache]} - {self.Log_Text_226_str[self.sprache]} {self.name}")
        guid = self.joystick.get_guid()
        logger.info(f"{self.Log_Text_224_str[self.sprache]} - {self.Log_Text_227_str[self.sprache]}: {guid}")
        power_level = self.joystick.get_power_level()
        logger.info(f"{self.Log_Text_224_str[self.sprache]} - {self.Log_Text_228_str[self.sprache]} {power_level}")

        ## Axis:
        axes = self.joystick.get_numaxes()
        logger.info(f"{self.Log_Text_224_str[self.sprache]} - {self.Log_Text_229_str[self.sprache]} {axes}")

        ## Buttons
        buttons = self.joystick.get_numbuttons()
        logger.info(f"{self.Log_Text_224_str[self.sprache]} - {self.Log_Text_230_str[self.sprache]} {buttons}")

        ## Hats:
        hats = self.joystick.get_numhats()
        logger.info(f"{self.Log_Text_224_str[self.sprache]} - {self.Log_Text_231_str[self.sprache]} {hats}")

        # PI-Achse Riegel:
        self.Riegel_dict = {}

    def event_Loop(self):
        '''While-Schleife die bis zum Programm Ende läuft - Reaktion auf Knöpfe!'''
        while not self.done:
            for achse in self.Riegel_dict:
                if achse.mode == 1 and self.Riegel_dict[achse][0] != 0:
                    timediff = (
                        datetime.datetime.now(datetime.timezone.utc).astimezone() - self.Riegel_dict[achse][1]
                    ).total_seconds() 
                    if timediff >= self.Riegel_dict[achse][0]:
                        achse.entriegel_Knopf(True)    
                        self.Riegel_dict[achse][0] = 0    

            for event in pygame.event.get():
                logger.debug(f"{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_232_str[self.sprache]} {event}")
                if event.type == pygame.QUIT:
                    pygame.quit()

                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0: # X
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_234_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_234_str[self.sprache]}')
                        for achse in self.Achsen_list:
                            if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIx':
                                if achse.Achse_steht: 
                                    achse.fahre_rechts(True)
                                    startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                    self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                            if achse.gamepad.isChecked() and 'Nemo-Achse-Linear' in achse.device_name and achse.Button_Link == 'HubS':
                                achse.fahre_Hoch()
                            if achse.gamepad.isChecked() and 'Educrys-Antrieb' in achse.device_name and achse.Button_Link == 'EduL':
                                achse.fahre_links_K()

                    if event.button == 1: # A
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_235_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_235_str[self.sprache]}')
                        for achse in self.Achsen_list:
                            if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIy':
                                if achse.Achse_steht: 
                                    achse.fahre_rechts(True)
                                    startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                    self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                            if achse.gamepad.isChecked() and 'Nemo-Achse-Rotation' in achse.device_name and achse.Button_Link == 'RotS':
                                achse.fahre_ccw()
                            if achse.gamepad.isChecked() and 'Educrys-Antrieb' in achse.device_name and achse.Button_Link == 'EduR':
                                achse.fahre_rechts_K()

                    if event.button == 2: # B
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_236_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_236_str[self.sprache]}')
                        for achse in self.Achsen_list: 
                            if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIx':
                                if achse.Achse_steht: 
                                    achse.fahre_links(True)
                                    startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                    self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                            if achse.gamepad.isChecked() and 'Nemo-Achse-Linear' in achse.device_name and achse.Button_Link == 'HubS':
                                achse.fahre_Runter()
                            if achse.gamepad.isChecked() and 'Educrys-Antrieb' in achse.device_name and achse.Button_Link == 'EduL':
                                achse.fahre_rechts_K()
                    
                    if event.button == 3: # Y
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_237_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_237_str[self.sprache]}')
                        for achse in self.Achsen_list:
                            if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIy':
                                if achse.Achse_steht: 
                                    achse.fahre_links(True)
                                    startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                    self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                            if achse.gamepad.isChecked() and 'Nemo-Achse-Rotation' in achse.device_name and achse.Button_Link == 'RotS':
                                achse.fahre_cw()
                            if achse.gamepad.isChecked() and 'Educrys-Antrieb' in achse.device_name and achse.Button_Link == 'EduR':
                                achse.fahre_links_K()
                        
                    if event.button == 4: # L
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_238_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_238_str[self.sprache]}')
                    
                    if event.button == 5: # R
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_239_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_239_str[self.sprache]}')
                    
                    if event.button == 8: # Select
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_240_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_240_str[self.sprache]}')
                        for achse in self.Achsen_list:
                            if achse.gamepad.isChecked():
                                achse.Stopp()

                    if event.button == 9: # Start
                        self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_241_str[self.sprache]}')
                        logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_241_str[self.sprache]}')
                        for achse in self.Achsen_list:
                            if achse.gamepad.isChecked() and 'Educrys-Antrieb' in achse.device_name and achse.Button_Link == 'EduF':
                                achse.fahre_links_K()
                    
                elif event.type == pygame.JOYAXISMOTION:
                    if event.axis == 0:         # Links, Rechts
                        if round(self.joystick.get_axis(0)) == 1: # Rechts
                            self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_244_str[self.sprache]}')
                            logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_244_str[self.sprache]}')
                            for achse in self.Achsen_list:
                                if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIh':
                                    if achse.Achse_steht: 
                                        achse.fahre_rechts(True)
                                        startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                        self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                                if achse.gamepad.isChecked() and 'Nemo-Achse-Rotation' in achse.device_name and achse.Button_Link == 'RotT':
                                    achse.fahre_ccw()
                        elif round(self.joystick.get_axis(0)) == -1: # Links
                            self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_245_str[self.sprache]}')
                            logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_245_str[self.sprache]}') 
                            for achse in self.Achsen_list: 
                                if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIh':
                                    if achse.Achse_steht: 
                                        achse.fahre_links(True)
                                        startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                        self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                                if achse.gamepad.isChecked() and 'Nemo-Achse-Rotation' in achse.device_name and achse.Button_Link == 'RotT':
                                    achse.fahre_cw()
                    
                    if event.axis == 1:         # Auf, Runter
                        if round(self.joystick.get_axis(1)) == 1: # Runter
                            self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_243_str[self.sprache]}')
                            logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_243_str[self.sprache]}')
                            for achse in self.Achsen_list:
                                if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIz':
                                    if achse.Achse_steht: 
                                        achse.fahre_rechts(True)
                                        startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                        self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                                if achse.gamepad.isChecked() and 'Nemo-Achse-Linear' in achse.device_name and achse.Button_Link == 'HubT':
                                    achse.fahre_Runter()
                        elif round(self.joystick.get_axis(1)) == -1: # Hoch
                            self.add_Text_To_Ablauf_Datei(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_242_str[self.sprache]}')
                            logger.debug(f'{self.Log_Text_224_str[self.sprache]} - {self.name} - {self.Log_Text_242_str[self.sprache]}')
                            for achse in self.Achsen_list:
                                if achse.gamepad.isChecked() and 'PI-Achse' in achse.device_name and achse.Button_Link == 'PIz':
                                    if achse.Achse_steht: 
                                        achse.fahre_links(True)
                                        startzeit = datetime.datetime.now(datetime.timezone.utc).astimezone()
                                        self.Riegel_dict.update({achse: [achse.time_Riegel, startzeit]})
                                if achse.gamepad.isChecked() and 'Nemo-Achse-Linear' in achse.device_name and achse.Button_Link == 'HubT':
                                    achse.fahre_Hoch()

    def ende(self):
        '''Beendet die Nutzung des Gamepads. Beendet While-Schleife!'''
        self.done = True

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''

'''