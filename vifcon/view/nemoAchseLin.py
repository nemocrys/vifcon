# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo-Achse Lineare Bewegung Widget:
- Anheften von weiteren Widgets (Knöpfe, Eingabefelder, Label, etc.)
- Messwert Angabe und Eingabe
- Kurven und Legende
- Update des Plots
- Rezept-Funktionen
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,

)
from PyQt5.QtGui import (
    QIcon,

)
from PyQt5.QtCore import (
    QSize,
    Qt,
    QTimer,

)
import pyqtgraph as pg

## Allgemein:
import logging
import datetime
import yaml

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)

class NemoAchseLinWidget(QWidget):
    def __init__(self, sprache, Frame_Anzeige, widget, line_color, config, config_dat, neustart, add_Ablauf_function, nemoAchse, gamepad_aktiv, typ = 'Antrieb', parent=None):
        """ GUI widget of Nemo-Achse Lineare Bewegung.

        Args:
            sprache (int):                  Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):           Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (obj):                   Element in das, das Widget eingefügt wird
            line_color (list):              Liste mit drei Farben
            config (dict):                  Konfigurationsdaten aus der YAML-Datei
            config_dat (string):            Datei-Name der Config-Datei
            neustart (bool):                Neustart Modus, Startkonfigurationen werden übersprungen
            add_Ablauf_function (Funktion): Funktion zum updaten der Ablauf-Datei.
            nemoAchse (str):                Name des Gerätes
            gamepad_aktiv (bool):           Soll das GamePad aktiviert werden bzw. wurde dies getan
            typ (str):                      Typ des Gerätes
        """
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Funktionsübergabe einlesen:
        self.sprache                    = sprache
        self.typ_widget                 = widget
        self.color                      = line_color
        self.config                     = config
        self.config_dat                 = config_dat
        self.neustart                   = neustart
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = nemoAchse
        self.typ                        = typ

        ## Aus Config:
        ### Zum Start:
        self.init = self.config['start']['init']
        ### Limits:
        self.oGv = self.config["limits"]['maxSpeed']
        self.uGv = self.config["limits"]['minSpeed']
        self.oGs = self.config["limits"]['maxPos']
        self.uGs = self.config["limits"]['minPos']
        self.oGx = self.config['PID']['Input_Limit_max']
        self.uGx = self.config['PID']['Input_Limit_min']
        ### GUI:
        self.legenden_inhalt = self.config['GUI']['legend'].split(';')
        self.legenden_inhalt = [a.strip() for a in self.legenden_inhalt]    # sollten Unnötige Leerzeichen vorhanden sein, so werden diese entfernt!
        self.color_Aktiv = self.typ_widget.color_On
        ### Rezepte:
        self.rezept_config = self.config["rezepte"]
        ### Gamepad:
        self.Button_Link = self.config['gamepad_Button']
        ### PID-Modus:
        self.unit_PIDIn = self.config['PID']['Input_Size_unit']

        ## Faktoren Skalierung:
        self.skalFak = self.typ_widget.Faktor

        ## Aktuelle Messwerte:
        self.ak_value = {}

        ## Weitere:
        self.Rezept_Aktiv = False
        self.data = {}

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Werte:
        istwert_str             = ['Ist',                                                                                                       'Is']
        istwert2_str            = ['Ist-Sim',                                                                                                   'Is-Sim']
        istwert3_str            = ['Ist-Gerät',                                                                                                 'Is-Device']
        sollwert_str            = ['Soll',                                                                                                      'Set']
        ## Knöpfe:                                                                  
        rez_start_str           = ['Rezept Start',                                                                                              'Start recipe']
        rez_ende_str            = ['Rezept Beenden',                                                                                            'Finish recipe']
        DH_str                  = ['Setz Nullpunkt',                                                                                            'Define Home']
        ## Zusatz:  
        self.str_Size_1         = ['Geschwindigkeit',                                                                                           'Speed']
        self.str_Size_2         = ['Position/Weg/Strecke',                                                                                      'Position/path/distance']
        ## Checkbox:    
        cb_sync_str             = ['Sync',                                                                                                      'Sync']
        cb_gPad_str             = ['GPad',                                                                                                      'GPad']
        cb_PID                  = ['PID',                                                                                                       'PID']
        ## Einheiten mit Größe: 
        self.v_str              = ['v in mm/min:',                                                                                              'v in mm/min:']
        self.x_str              = [f'x in {self.unit_PIDIn}:',                                                                                  f'x in {self.unit_PIDIn}:']
        sv_str                  = ['v:',                                                                                                        'v:']
        ss_str                  = ['s (sim):',                                                                                                  's (sim):']
        ssd_str                 = ['s (Orig):',                                                                                                 's (orig):']
        sx_str                  = ['PID:',                                                                                                      'PID:']
        st_v_str                = ['XXX.XX mm/min',                                                                                             'XXX.XX mm/min']
        st_s_str                = ['XXX.XX mm',                                                                                                 'XXX.XX mm'] 
        st_x_str                = [f'XXX.XX {self.unit_PIDIn}',                                                                                 f'XXX.XX {self.unit_PIDIn}'] 
        s_einzel_str            = ['s',                                                                                                         's']
        v_einzel_str            = ['v',                                                                                                         'v']
        x_einzel_str            = ['x',                                                                                                         'x']
        self.einheit_s_einzel   = ['mm',                                                                                                        'mm']
        self.einheit_v_einzel   = ['mm/min',                                                                                                    'mm/min']
        self.einheit_x_einzel   = [f'{self.unit_PIDIn}',                                                                                        f'{self.unit_PIDIn}']
        PID_Von_1               = ['Wert von Multilog',                                                                                         'Value of Multilog']
        PID_Von_2               = ['Wert von VIFCON',                                                                                           'Value ofVIFCON']
        PID_Zusatz              = ['ex,',                                                                                                       'ex,']
        ## Fehlermeldungen:         
        self.err_0_str          = ['Fehler!',                                                                                                   'Error!']
        self.err_1_str          = ['Keine EINGABE!!',                                                                                           'No INPUT!!']
        self.err_2_str          = ['Grenzen überschritten!\nGrenzen von',                                                                       'Limits exceeded!\nLimits from']
        self.err_3_str          = ['bis',                                                                                                       'to']
        self.err_4_str          = ['Gerät anschließen und\nInitialisieren!',                                                                    'Connect the device\nand initialize!']
        self.err_5_str          = ['Fehlerhafte Eingabe!',                                                                                      'Incorrect input!']
        self.err_6_str          = ['Der Wert',                                                                                                  'The value']
        self.err_7_str          = ['überschreitet\ndie Grenzen von',                                                                            'exceeds\nthe limits of']
        self.err_9_str          = ['Der Schritt',                                                                                               'Step']
        self.err_10_str         = ['Rezept Einlesefehler!',                                                                                     'Recipe import error!']
        self.err_12_str         = ['Erster Schritt = Sprung!\nDa keine Messwerte!',                                                             'First step = jump! There\nare no measurements!']
        self.err_13_str         = ['o.K.',                                                                                                      'o.K.']      
        self.err_14_str         = ['Rezept läuft!\nRezept Einlesen gesperrt!',                                                                  'Recipe is running!\nReading recipes blocked!']
        self.err_15_str         = ['Wähle ein Rezept!',                                                                                         'Choose a recipe!']
        self.err_16_str         = ['Rezept läuft!\nRezept Start gesperrt!',                                                                     'Recipe running!\nRecipe start blocked!']
        self.err_21_str         = ['Fehler in der Rezept konfiguration\nder Config-Datei! Bitte beheben und Neueinlesen!',                      'Error in the recipe configuration of\nthe config file! Please fix and re-read!']
        self.err_PID_1_str      = ['Die Bewegungsrichtung',                                                                                     'The direction of movement']
        self.err_PID_2_str      = ['exestiert nicht!\nGenutzt werden kann nur UP und DOWN!',                                                    'does not exist!\nOnly UP and DOWN can be used!']
        self.err_PID_3_str      = ['Der PID-Modus benötigt eine\nAngabe der Bewegungsrichtung!',                                                'The PID mode requires a specification\nof the direction of movement!']
        ## Status:          
        status_1_str            = ['Status: Inaktiv',                                                                                           'Status: Inactive']
        self.status_2_str       = ['Kein Status',                                                                                               'No Status']
        self.status_3_str       = ['Status:',                                                                                                   'Status:']
        self.sta_Bit0_str       = ['Betriebsbereit',                                                                                            'Ready for operation']
        self.sta_Bit1_str       = ['Achse referiert',                                                                                           'Axis referenced']
        self.sta_Bit2_str       = ['Achse Fehler',                                                                                              'Axis error']
        self.sta_Bit3_str       = ['Antrieb läuft',                                                                                             'Drive is running']
        self.sta_Bit4_str       = ['Antrieb läuft aufwärts',                                                                                    'Drive runs upwards']
        self.sta_Bit5_str       = ['Antrieb läuft abwärts',                                                                                     'Drive runs downwards']
        self.sta_Bit6_str       = ['Achse Position oben (Soft.-End.)',                                                                          'Axis position up (Soft.-End.)']
        self.sta_Bit7_str       = ['Achse Position unten (Soft.-End.)',                                                                         'Axis position down (Soft.-End.)']
        self.sta_Bit8_str       = ['Achse Endlage oben (Hard.-End.)',                                                                           'Axis end position up (Hard.-End.)']
        self.sta_Bit9_str       = ['Achse Endlage unten (Hard.-End.)',                                                                          'Axis end position down (Hard.-End.)']
        self.sta_Bit10_str      = ['Software-Endlagen aus',                                                                                     'Software end positions']
        self.sta_Bit11_str      = ['Achse in Stopp',                                                                                            'Axis in stop']
        self.sta_Bit15_str      = ['Test-Modus Aktiv',                                                                                          'Test Mode Active']
        ## Plot-Legende:                                                            
        rezept_Label_str        = ['Rezept',                                                                                                    'Recipe']
        ober_Grenze_str         = ['oG',                                                                                                        'uL']                                   # uL - upper Limit
        unter_Grenze_str        = ['uG',                                                                                                        'lL']                                   # lL - lower Limit
        ## Logging:
        self.Log_Text_1_str 	= ['Erstelle Widget.',                                                                                          'Create widget.']
        self.Log_Text_28_str    = ['Gerät wurde Gestartet/Initialisiert!',                                                                      'Device has been started/initialized!']
        self.Log_Text_29_str    = ['Gerät wurde nicht Initialisiert! Initialisierung durch Menü im späteren!',                                  'Device was not initialized! Initialization through menu later!']
        self.Log_Text_30_str    = ['Neustart Modus.',                                                                                           'Restart mode.']
        self.Log_Text_39_str    = ['Rezept:',                                                                                                   'Recipe:']
        self.Log_Text_40_str    = ['Rezept Inhalt:',                                                                                            'Recipe content:']
        self.Log_Text_56_str    = ['Konfiguration aktualisieren (Nullpunkt setzen Nemo Hub):',                                                  'Update configuration (Define-Home Nemo Hub):']
        self.Log_Text_57_str    = ['Rezept hat folgende zu fahrende Positions-Abfolge:',                                                        'Recipe has the following position sequence to be driven:']
        self.Log_Text_181_str   = ['Die Geschwindigkeit wird Invertiert! Die Wahren Werte hätten ein anderes Vorzeichen!',                      'The speed is inverted! The true values would have a different sign!']
        self.Log_Text_205_str   = ['Update Konfiguration (Update Limits):',                                                                     'Update configuration (update limits):']
        self.Log_Text_Ex1_str   = ['Fehler Grund (Rezept einlesen):',                                                                           'Error reason (reading recipe):']
        self.Log_Text_Ex2_str   = ['Fehler Grund (Problem mit Rezept-Konfiguration):',                                                          'Error reason (Problem with recipe configuration)']
        self.Log_Text_PID_Ex    = ['Der Wert in der Konfig liegt außerhalb des Limit-Bereiches! Umschaltwert wird auf Minimum-Limit gesetzt!',  'The value in the config is outside the limit range! Switching value is set to minimum limit!']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                              'Limit range']
        self.Log_Text_LB_2      = ['Geschwindigkeit',                                                                                           'Velocity']
        self.Log_Text_LB_3      = ['Position',                                                                                                  'Position']
        self.Log_Text_LB_4      = ['bis',                                                                                                       'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                               'after update']
        ## Ablaufdatei: 
        self.Text_23_str        = ['Knopf betätigt - Initialisierung!',                                                                         'Button pressed - initialization!']
        self.Text_24_str        = ['Ausführung des Rezeptes:',                                                                                  'Execution of the recipe:']
        self.Text_39_str        = ['Knopf betätigt - Nullpunkt setzen!',                                                                        'Button pressed - Define Home!']
        self.Text_42_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da Grenzen überschritten werden!',                        'Input field error message: Sending failed because limits were exceeded!']
        self.Text_43_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da fehlerhafte Eingabe!',                                 'Input field error message: Sending failed due to incorrect input!']
        self.Text_45_str        = ['Knopf betätigt - Hoch!',                                                                                    'Button pressed - Up!']
        self.Text_46_str        = ['Knopf betätigt - Runter!',                                                                                  'Button pressed - down!']
        self.Text_47_str        = ['Knopf betätigt - Stopp!',                                                                                   'Button pressed - stop!']
        self.Text_48_str        = ['Eingabefeld Fehlermeldung: Keine Eingabe!',                                                                 'Input field error message: No input!']
        self.Text_81_str        = ['Knopf betätigt - Beende Rezept',                                                                            'Button pressed - End recipe']
        self.Text_82_str        = ['Rezept ist zu Ende!',                                                                                       'Recipe is finished!']
        self.Text_83_str        = ['Stopp betätigt - Beende Rezept',                                                                            'Stop pressed - End recipe']
        self.Text_84_str        = ['Rezept läuft! Erneuter Start verhindert!',                                                                  'Recipe is running! Restart prevented!']
        self.Text_85_str        = ['Rezept Startet',                                                                                            'Recipe Starts']
        self.Text_86_str        = ['Rezept Beenden',                                                                                            'Recipe Ends']
        self.Text_87_str        = ['Knopf betätigt - Start Rezept',                                                                             'Button pressed - Start recipe']
        self.Text_88_str        = ['Rezept konnte aufgrund von Fehler nicht gestartet werden!',                                                 'Recipe could not be started due to an error!']
        self.Text_89_str        = ['Knopf betätigt - Beende Rezept - Keine Wirkung auf Rezept-Funktion, jedoch Auslösung des Stopp-Knopfes!',   'Button pressed - End recipe - No effect on recipe function, but triggers the stop button!']
        self.Text_90_str        = ['Sicherer Endzustand wird hergestellt! Auslösung des Stopp-Knopfes!',                                        'Safe final state is established! Stop button is activated!']
        self.Text_91_str        = ['Rezept Beenden - Sicherer Endzustand',                                                                      'Recipe Ends - Safe End State']
        self.Text_PID_1         = ['Wechsel in PID-Modus.',                                                                                     'Switch to PID mode.']
        self.Text_PID_2         = ['Wechsel in Eurotherm-Regel-Modus.',                                                                         'Switch to Eurotherm control mode.']
        self.Text_PID_3         = ['Moduswechsel! Auslösung des Stopp-Knopfes aus Sicherheitsgründen!',                                         'Mode change! Stop button triggered for safety reasons!']
        self.Text_PID_4         = ['Rezept Beenden! Wechsel des Modus!',                                                                        'End recipe! Change mode!']
        
        #---------------------------------------
        # Konfigurationen für das Senden:
        #---------------------------------------
        #self.send_betätigt = False
        self.write_task = {'Stopp': False, 'Hoch': False, 'Runter': False, 'Init':False, 'Define Home': False, 'Send': False, 'Start':False, 'Update Limit': False, 'PID': False}
        self.write_value = {'Speed': 0, 'Limits': [0, 0, 0, 0, 0, 0], 'PID-Sollwert': 0} # Limits: oGs, uGs, oGv, uGv, oGx, uGx

        # Wenn Init = False, dann werden die Start-Auslesungen nicht ausgeführt:
        if self.init and not self.neustart:
            self.write_task['Start'] = True

        #---------------------------------------
        # Nachrichten im Log-File:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_28_str[self.sprache]}") if self.init else logger.warning(f"{self.device_name} - {self.Log_Text_29_str[self.sprache]}")
        if self.neustart: logger.info(f"{self.device_name} - {self.Log_Text_30_str[self.sprache]}") 
        if self.config['start']['invert']: logger.warning(f'{self.device_name} - {self.Log_Text_181_str[self.sprache]}')
        ## Limit-Bereiche:
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]}: {self.uGv} {self.Log_Text_LB_4[self.sprache]} {self.oGv} {self.einheit_v_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]}: {self.uGs} {self.Log_Text_LB_4[self.sprache]} {self.oGs} {self.einheit_s_einzel[self.sprache]}')

        #---------------------------------------
        # GUI:
        #---------------------------------------
        ## Grundgerüst:
        self.layer_widget = QWidget()
        self.layer_layout = QGridLayout()
        self.layer_widget.setLayout(self.layer_layout)
        self.typ_widget.splitter_main.splitter.addWidget(self.layer_widget)
        logger.info(f"{self.device_name} - {self.Log_Text_1_str[self.sprache]}")
        #________________________________________
        ## Kompakteres Darstellen:
        ### Grid Size - bei Verschieben der Splitter zusammenhängend darstellen:
        self.layer_layout.setRowStretch(6, 1)
        self.layer_layout.setColumnStretch(6, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)
        self.layer_layout.setVerticalSpacing(1)

        ### Zeilenhöhen:
        self.layer_layout.setRowMinimumHeight(1, 40)     # Error-Nachricht

        ### Spaltenbreiten:
        self.layer_layout.setColumnMinimumWidth(0, 120)
        self.layer_layout.setColumnMinimumWidth(2, 60)
        self.layer_layout.setColumnMinimumWidth(3, 90)
        self.layer_layout.setColumnMinimumWidth(4, 110)
        #________________________________________
        ## Widgets:
        ### Eingabefelder:
        self.LE_Speed = QLineEdit()
        self.LE_Speed.setText(str(self.config["defaults"]['startSpeed']))

        ### Checkbox:
        self.Auswahl = QCheckBox(cb_sync_str[self.sprache])
        
        self.gamepad = QCheckBox(cb_gPad_str[self.sprache])
        if not gamepad_aktiv:
            self.gamepad.setEnabled(False)

        self.PID_cb  = QCheckBox(cb_PID[self.sprache])
        self.PID_cb.clicked.connect(self.PID_ON_OFF)

        ### Label:
        #### Titel-Gerät:
        self.La_name = QLabel(f'<b>{nemoAchse}</b>')
        #### Fehlernachrichten:
        self.La_error_1 = QLabel(self.err_13_str[self.sprache])
        #### Istwert Weg Simuliert:
        self.La_IstPos_text = QLabel(f'{istwert_str[self.sprache]}-{ss_str[self.sprache]} ')
        self.La_IstPos_wert = QLabel(st_s_str[self.sprache])
        if self.color_Aktiv: self.La_IstPos_text.setStyleSheet(f"color: {self.color[0]}")
        if self.color_Aktiv: self.La_IstPos_wert.setStyleSheet(f"color: {self.color[0]}")
        #### Istwert Weg ausgelesen:
        self.La_IstPosOr_text = QLabel(f'{istwert_str[self.sprache]}-{ssd_str[self.sprache]} ')
        self.La_IstPosOr_wert = QLabel(st_s_str[self.sprache])
        if self.color_Aktiv: self.La_IstPosOr_text.setStyleSheet(f"color: {self.color[5]}")
        if self.color_Aktiv: self.La_IstPosOr_wert.setStyleSheet(f"color: {self.color[5]}")
        #### Istwert Geschwindigkeit ausgelesen:
        self.La_IstSpeed_text = QLabel(f'{istwert_str[self.sprache]}-{sv_str[self.sprache]} ')
        self.La_IstSpeed_wert = QLabel(st_v_str[self.sprache])
        if self.color_Aktiv: self.La_IstSpeed_text.setStyleSheet(f"color: {self.color[1]}")
        if self.color_Aktiv: self.La_IstSpeed_wert.setStyleSheet(f"color: {self.color[1]}")
        #### Status ausgelesen:
        self.La_Status = QLabel(status_1_str[self.sprache])
        #### Sollgeschwindigkeit:
        self.La_SollSpeed = QLabel(self.v_str[self.sprache])
        if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: {self.color[2]}")

        self.La_SollSpeed_text = QLabel(f'{sollwert_str[self.sprache]}-{sv_str[self.sprache]} ')
        self.La_SollSpeed_wert = QLabel(st_v_str[self.sprache])
        if self.color_Aktiv: self.La_SollSpeed_text.setStyleSheet(f"color: {self.color[2]}")
        if self.color_Aktiv: self.La_SollSpeed_wert.setStyleSheet(f"color: {self.color[2]}")
        #### Soll-Größe PID-Modus:
        self.La_SollPID_text = QLabel(f'{sollwert_str[self.sprache]}-{sx_str[self.sprache]} ')
        self.La_SollPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_SollPID_text.setStyleSheet(f"color: {self.color[6]}")
        if self.color_Aktiv: self.La_SollPID_wert.setStyleSheet(f"color: {self.color[6]}")
        #### Ist-Größe PID-Modus:
        self.La_IstPID_text = QLabel(f'{istwert_str[self.sprache]}-{sx_str[self.sprache]} ')
        self.La_IstPID_wert = QLabel(st_x_str[self.sprache])
        if self.color_Aktiv: self.La_IstPID_text.setStyleSheet(f"color: {self.color[7]}")
        if self.color_Aktiv: self.La_IstPID_wert.setStyleSheet(f"color: {self.color[7]}")

        ### Knöpfe:
        #### Bewegung:
        self.btn_hoch = QPushButton(QIcon("./vifcon/icons/p_hoch.png"), '')
        self.btn_hoch.setFlat(True)
        self.btn_hoch.clicked.connect(self.fahre_Hoch)

        self.btn_runter = QPushButton(QIcon(QIcon("./vifcon/icons/p_runter.png")), '')
        self.btn_runter.setFlat(True)
        self.btn_runter.clicked.connect(self.fahre_Runter)
        #### Stopp:
        icon_pfad = "./vifcon/icons/p_stopp.png" if sprache == 0 else  "./vifcon/icons/p_stopp_En.png" 
        self.btn_mitte = QPushButton(QIcon(icon_pfad), '')
        self.btn_mitte.setFlat(True)
        self.btn_mitte.clicked.connect(lambda: self.Stopp(3))
        #### Rezepte:
        self.btn_rezept_start =  QPushButton(rez_start_str[self.sprache])
        self.btn_rezept_start.clicked.connect(lambda: self.RezStart(1))

        self.btn_rezept_ende =  QPushButton(rez_ende_str[self.sprache])
        self.btn_rezept_ende.clicked.connect(lambda: self.Stopp(1))
        #### Define Home:
        self.btn_DH = QPushButton(DH_str[self.sprache])
        self.btn_DH.clicked.connect(self.define_home)

        ### Combobox:
        self.cb_Rezept = QComboBox()
        self.cb_Rezept.addItem('------------')
        try:
            for rezept in self.rezept_config:
                self.cb_Rezept.addItem(rezept) 
        except Exception as e:
            self.Fehler_Output(1, self.err_21_str[self.sprache])
            logger.exception(self.Log_Text_Ex2_str[self.sprache])
        self.cb_Rezept.setStyleSheet('''* 
                                    QComboBox QAbstractItemView 
                                        {
                                        min-width:200px;
                                        }
                                    ''')    # https://stackoverflow.com/questions/37632845/qcombobox-adjust-drop-down-width
        
        ### Gruppen Widgets:
        #### Bewegungsknöpfe:
        self.btn_group_move = QWidget()
        self.btn_move_layout = QHBoxLayout()
        self.btn_group_move.setLayout(self.btn_move_layout)
        self.btn_move_layout.setSpacing(20)

        self.btn_move_layout.addWidget(self.btn_hoch)
        self.btn_move_layout.addWidget(self.btn_mitte)
        self.btn_move_layout.addWidget(self.btn_runter)

        #### Rezept:
        self.btn_group_Rezept = QWidget()
        self.btn_Rezept_layout = QVBoxLayout()
        self.btn_group_Rezept.setLayout(self.btn_Rezept_layout)
        self.btn_Rezept_layout.setSpacing(5)

        self.btn_Rezept_layout.addWidget(self.btn_DH)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_start)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_ende)
        self.btn_Rezept_layout.addWidget(self.cb_Rezept)

        self.btn_Rezept_layout.setContentsMargins(2,0,2,0)      # left, top, right, bottom

        #### Label-Werte:
        W_spalte = 80
        self.W1 = QWidget()
        self.W1_layout = QGridLayout()
        self.W1.setLayout(self.W1_layout)
        self.W1_layout.addWidget(self.La_IstSpeed_text, 0 , 0)
        self.W1_layout.addWidget(self.La_IstSpeed_wert, 0 , 1 , alignment=Qt.AlignLeft)
        self.W1_layout.setContentsMargins(0,0,0,0)
        self.W1_layout.setColumnMinimumWidth(0, W_spalte)

        self.W2 = QWidget()
        self.W2_layout = QGridLayout()
        self.W2.setLayout(self.W2_layout)
        self.W2_layout.addWidget(self.La_IstPos_text, 0 , 0)
        self.W2_layout.addWidget(self.La_IstPos_wert, 0 , 1 , alignment=Qt.AlignLeft)
        self.W2_layout.setContentsMargins(0,0,0,0)
        self.W2_layout.setColumnMinimumWidth(0, W_spalte)

        self.W3 = QWidget()
        self.W3_layout = QGridLayout()
        self.W3.setLayout(self.W3_layout)
        self.W3_layout.addWidget(self.La_IstPosOr_text, 0 , 0)
        self.W3_layout.addWidget(self.La_IstPosOr_wert, 0 , 1 , alignment=Qt.AlignLeft)
        self.W3_layout.setContentsMargins(0,0,0,0)
        self.W3_layout.setColumnMinimumWidth(0, W_spalte)

        self.W4 = QWidget()
        self.W4_layout = QGridLayout()
        self.W4.setLayout(self.W4_layout)
        self.W4_layout.addWidget(self.La_SollSpeed_text, 0 , 0)
        self.W4_layout.addWidget(self.La_SollSpeed_wert, 0 , 1 , alignment=Qt.AlignLeft)
        self.W4_layout.setContentsMargins(0,0,0,0)
        self.W4_layout.setColumnMinimumWidth(0, W_spalte)

        self.W5 = QWidget()
        self.W5_layout = QGridLayout()
        self.W5.setLayout(self.W5_layout)
        self.W5_layout.addWidget(self.La_IstPID_text, 0 , 0)
        self.W5_layout.addWidget(self.La_IstPID_wert, 0 , 1 , alignment=Qt.AlignLeft)
        self.W5_layout.setContentsMargins(0,0,0,0)
        self.W5_layout.setColumnMinimumWidth(0, W_spalte)

        self.W6 = QWidget()
        self.W6_layout = QGridLayout()
        self.W6.setLayout(self.W6_layout)
        self.W6_layout.addWidget(self.La_SollPID_text, 0 , 0)
        self.W6_layout.addWidget(self.La_SollPID_wert, 0 , 1 , alignment=Qt.AlignLeft)
        self.W6_layout.setContentsMargins(0,0,0,0)
        self.W6_layout.setColumnMinimumWidth(0, W_spalte)

        self.V = QWidget()
        self.V_layout = QVBoxLayout()
        self.V.setLayout(self.V_layout)
        self.V_layout.setSpacing(0)
        self.V_layout.addWidget(self.W1)
        self.V_layout.addWidget(self.W4)
        self.V_layout.addWidget(self.W2)
        self.V_layout.addWidget(self.W3)
        self.V_layout.addWidget(self.W5)
        self.V_layout.addWidget(self.W6) 
        self.V_layout.setContentsMargins(0,0,0,0)

        #### First-Row:
        self.first_row_group  = QWidget()
        self.first_row_layout = QHBoxLayout()
        self.first_row_group.setLayout(self.first_row_layout)
        self.first_row_layout.setSpacing(20)

        self.first_row_layout.addWidget(self.La_name)
        self.first_row_layout.addWidget(self.Auswahl)
        self.first_row_layout.addWidget(self.gamepad)
        self.first_row_layout.addWidget(self.PID_cb)

        self.first_row_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom
        #________________________________________
        ## Platzierung der einzelnen Widgets im Layout:
        self.layer_layout.addWidget(self.first_row_group,                   0, 0, 1, 6, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_SollSpeed,                      1, 0)
        self.layer_layout.addWidget(self.btn_group_move,                    3, 0, 1, 3, alignment=Qt.AlignLeft)                     # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung
        self.layer_layout.addWidget(self.La_Status,                         4, 0, 1, 6, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.LE_Speed,                          1, 1)
        self.layer_layout.addWidget(self.La_error_1,                        1, 2,       alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.V,                                 1, 3, 3, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.btn_group_Rezept,                  1, 5, 3, 1, alignment=Qt.AlignTop)
        #________________________________________
        ## Größen (Size) - Widgets:
        ### Button-Icon:
        self.btn_hoch.setIconSize(QSize(50, 50))
        self.btn_runter.setIconSize(QSize(50, 50))
        self.btn_mitte.setIconSize(QSize(50, 50))

        ### Eingabefelder (Line Edit):
        self.LE_Speed.setFixedWidth(100)
        self.LE_Speed.setFixedHeight(25)

        ### Rezpt-Funktionen:
        self.btn_rezept_start.setFixedWidth(100)
        self.btn_rezept_ende.setFixedWidth(100)
        self.cb_Rezept.setFixedWidth(100)
        self.btn_DH.setFixedWidth(100)
        #________________________________________
        ## Border Sichtbar:
        if Frame_Anzeige:
            self.layer_widget.setStyleSheet("border: 1px solid black;")

        #---------------------------------------
        # Kurven:
        #---------------------------------------
        ## PID-Modus:
        origin = self.config['PID']['Value_Origin'].upper()
        ### Istwert:
        PID_Export_Ist = ''
        if origin[0] == 'V': PID_Label_Ist = PID_Von_2[sprache]
        elif origin [0] == 'M':     
            PID_Label_Ist  = PID_Von_1[sprache]
            PID_Export_Ist = PID_Zusatz[sprache]
        else:                PID_Label_Ist = PID_Von_2[sprache]
        ### Sollwert
        PID_Export_Soll = ''
        if origin[1] == 'V':  PID_Label_Soll = PID_Von_2[sprache]
        elif origin [1] == 'M':     
            PID_Label_Soll  = PID_Von_1[sprache]
            PID_Export_Soll = PID_Zusatz[sprache]
        else:                 PID_Label_Soll = PID_Von_2[sprache]
        
        ### Start Wert:
        self.write_value['PID-Sollwert'] = self.config['PID']['start_soll']

        kurv_dict = {                                                                   # Wert: [Achse, Farbe/Stift, Name]
            'IWs':      ['a1', pg.mkPen(self.color[0], width=2),                            f'{nemoAchse} - {s_einzel_str[self.sprache]}<sub>{istwert2_str[self.sprache]}</sub>'],
            'IWv':      ['a2', pg.mkPen(self.color[1], width=2),                            f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWv':      ['a2', pg.mkPen(self.color[2]),                                     f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            'SWs':      ['a1', pg.mkPen(self.color[3]),                                     f'{nemoAchse} - {s_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            'oGs':      ['a1', pg.mkPen(color=self.color[0], style=Qt.DashLine),            f'{nemoAchse} - {s_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGs':      ['a1', pg.mkPen(color=self.color[0], style=Qt.DashDotDotLine),      f'{nemoAchse} - {s_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGv':      ['a2', pg.mkPen(color=self.color[1], style=Qt.DashLine),            f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGv':      ['a2', pg.mkPen(color=self.color[1], style=Qt.DashDotDotLine),      f'{nemoAchse} - {v_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'Rezv':     ['a2', pg.mkPen(color=self.color[4], width=3, style=Qt.DotLine),    f'{nemoAchse} - {rezept_Label_str[self.sprache]}<sub>{v_einzel_str[self.sprache]}</sub>'],
            'IWsd':     ['a1', pg.mkPen(color=self.color[5], width=2),                      f'{nemoAchse} - {s_einzel_str[self.sprache]}<sub>{istwert3_str[self.sprache]}</sub>'],
            'SWxPID':   ['a1', pg.mkPen(self.color[6], width=2, style=Qt.DashDotLine),      f'{PID_Label_Soll} - {x_einzel_str[self.sprache]}<sub>{PID_Export_Soll}{sollwert_str[self.sprache]}</sub>'], 
            'IWxPID':   ['a1', pg.mkPen(self.color[7], width=2, style=Qt.DashDotLine),      f'{PID_Label_Ist} - {x_einzel_str[self.sprache]}<sub>{PID_Export_Ist}{istwert_str[self.sprache]}</sub>'],
            'Rezx':     ['a1', pg.mkPen(color=self.color[8], width=3, style=Qt.DotLine),    f'{nemoAchse} - {rezept_Label_str[self.sprache]}<sub>{x_einzel_str[self.sprache]}</sub>'],
        }

        ## Kurven erstellen:
        ist_drin_list = []                                                              # Jede Kurve kann nur einmal gesetzt werden!
        self.kurven_dict = {}
        for legend_kurve in self.legenden_inhalt:
            if legend_kurve in kurv_dict and not legend_kurve in ist_drin_list:
                if kurv_dict[legend_kurve][0] == 'a1':
                    curve = self.typ_widget.plot.achse_1.plot([], pen=kurv_dict[legend_kurve][1], name=kurv_dict[legend_kurve][2])
                    if self.typ_widget.legend_ops['legend_pos'].upper() == 'OUT':
                        self.typ_widget.plot.legend.addItem(curve, curve.name())
                elif kurv_dict[legend_kurve][0] == 'a2':
                    curve = pg.PlotCurveItem([], pen=kurv_dict[legend_kurve][1], name=kurv_dict[legend_kurve][2])
                    self.typ_widget.plot.achse_2.addItem(curve)
                    if self.typ_widget.legend_ops['legend_pos'].upper() == 'OUT' or self.typ_widget.legend_ops['legend_pos'].upper() == 'IN':
                        self.typ_widget.plot.legend.addItem(curve, curve.name())
                self.kurven_dict.update({legend_kurve: curve})
                ist_drin_list.append(legend_kurve)

        ## Checkboxen erstellen:
        self.kurven_side_legend         = {}

        if self.typ_widget.legend_ops['legend_pos'].upper() == 'SIDE':
            for kurve in self.kurven_dict:
                widget, side_checkbox = self.GUI_Legend_Side(kurv_dict[kurve][2].split(' - '), kurv_dict[kurve][1], kurv_dict[kurve][0])
                if self.typ_widget.legend_ops['side'].upper() == 'RL':
                    if kurv_dict[kurve][0] == 'a1': self.typ_widget.legend_achsen_Links_widget.layout.addWidget(widget)
                    elif kurv_dict[kurve][0] == 'a2': self.typ_widget.legend_achsen_Rechts_widget.layout.addWidget(widget)
                elif self.typ_widget.legend_ops['side'].upper() == 'R':
                    self.typ_widget.legend_achsen_Rechts_widget.layout.addWidget(widget)
                elif self.typ_widget.legend_ops['side'].upper() == 'L':
                    self.typ_widget.legend_achsen_Links_widget.layout.addWidget(widget)
                self.kurven_side_legend.update({side_checkbox: kurve})

        ## Kurven-Daten-Listen:
        ### Messgrößen:
        self.posList        = []
        self.speedList      = []
        self.sollspeedList  = []
        self.sollposList    = []
        self.posListOr      = []
        self.sollxPID       = []
        self.istxPID        = []
        ### Grenzen:
        self.VoGList = []
        self.VuGList = []
        self.SoGList = []
        self.SuGList = []

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.curveDict      = {'IWs': '', 'IWv': '', 'SWv': '', 'SWs': '', 'oGv': '', 'uGv': '', 'oGs': '', 'uGs':'', 'Rezv': '', 'IWsd': '', 'SWTPID':'', 'IWTPID':'', 'Rezx': ''}                                                                                                                                                                                 # Kurven
        for kurve in self.kurven_dict:
            self.curveDict[kurve] = self.kurven_dict[kurve]
        self.labelDict      = {'IWs': self.La_IstPos_wert,                                  'IWv': self.La_IstSpeed_wert,               'SWv':self.La_SollSpeed_wert,                                       'IWsd': self.La_IstPosOr_wert,                  'SWxPID': self.La_SollPID_wert,                     'IWxPID': self.La_IstPID_wert}                      # Label
        self.labelUnitDict  = {'IWs': self.einheit_s_einzel[self.sprache],                  'IWv': self.einheit_v_einzel[self.sprache], 'SWv':self.einheit_v_einzel[self.sprache],                          'IWsd': self.einheit_s_einzel[self.sprache],    'SWxPID': self.einheit_x_einzel[self.sprache],      'IWxPID': self.einheit_x_einzel[self.sprache]}      # Einheit
        self.listDict       = {'IWs': self.posList,                                         'IWv': self.speedList,                      'SWv':self.sollspeedList,                   'SWs':self.sollposList, 'IWsd': self.posListOr,                         'SWxPID': self.sollxPID,                            'IWxPID': self.istxPID}                             # Werteliste
        self.grenzListDict  = {'oGv': self.VoGList,        'uGv': self.VuGList,             'oGs':self.SoGList,                         'uGs':self.SuGList}
        self.grenzValueDict = {'oGv': self.oGv,            'uGv': self.uGv,                 'oGs':self.oGs,                             'uGs':self.uGs}

        ## Plot-Skalierungsfaktoren:
        self.skalFak_dict = {}
        for size in self.curveDict:
            if 'Ws' in size:
                self.skalFak_dict.update({size: self.skalFak['Pos']})
            if 'Wv' in size:
                self.skalFak_dict.update({size: self.skalFak['Speed_2']})
            if 'Wx' in size:
                self.skalFak_dict.update({size: self.skalFak['PIDA']})

        #---------------------------------------
        # Timer:
        #---------------------------------------
        ## Rezept-Timer
        self.RezTimer = QTimer()
        self.RezTimer.timeout.connect(self.Rezept)

        #---------------------------------------
        # Rezept-Anzeige Funktion aktivieren:
        #---------------------------------------
        self.cb_Rezept.currentTextChanged.connect(self.RezKurveAnzeige) 
    
    ##########################################
    # Legenden an der Seite:
    ##########################################
    def GUI_Legend_Side(self, text, check_pen, achse):
        style = {1: '\u2501' * 2, 2: '\u2501 \u2501', 3: '\u00B7 \u00B7 ' * 2, 4: '\u2501\u00B7' * 3, 5: '\u2501\u00B7\u00B7' * 2} # 1: Solid, 2: Dashed, 3: Dot, 4: Dash Dot, 5: Dash Dot Dot

        check_Widget = QWidget()
        check_Layout = QHBoxLayout()
        check_Widget.setLayout(check_Layout)
        # Checkbox:
        check_legend = QCheckBox()
        check_legend.clicked.connect(self.Side_Legend)
        check_legend.setChecked(True)
        check_legend.setToolTip(text[0])
        if achse == 'a2':
            check_legend.setStyleSheet("QCheckBox::indicator::unchecked { background-color : darkgray; image : url('./vifcon/icons/unchecked.png'); }\n"
                                       "QCheckBox::indicator::checked { background-color : red; image : url('./vifcon/icons/checked.png'); }\n"
                                       "QCheckBox::indicator{ border : 1px solid black;}")
        else:
            check_legend.setStyleSheet("QCheckBox::indicator::unchecked { background-color : lightgray; image : url('./vifcon/icons/unchecked.png'); }\n"
                                       "QCheckBox::indicator::checked { background-color : black; image : url('./vifcon/icons/checked2.png'); }\n"
                                       "QCheckBox::indicator{ border : 1px solid gray;}")
        # Linie:
        check_Line = QLabel(style[check_pen.style()])
        check_Line.setStyleSheet(f"color: {check_pen.color().name()};")
        font = check_Line.font()
        if check_pen.width() > 1:
            font.setBold(True)
        check_Line.setToolTip(text[0])
        # Label:
        check_text = QLabel(text[1])
        check_text.setToolTip(text[0])
        # Anhängen:
        check_Layout.addWidget(check_legend)
        check_Layout.addWidget(check_Line)
        check_Layout.addWidget(check_text)
        # Geometry:
        check_Layout.setContentsMargins(0,0,0,0)
        
        return check_Widget, check_legend
    
    def Side_Legend(self, state):
        checkbox = self.sender()                    # Klasse muss von QWidget erben, damit sender() Funktioniert - Durch die Methode kann geschaut werden welche Checkbox betätigt wurde!
        kurve = self.kurven_side_legend[checkbox]
        if checkbox.isChecked():
            self.curveDict[kurve].setVisible(True)
        else:
            self.curveDict[kurve].setVisible(False)

    ##########################################
    # Fehlermedlung:
    ##########################################
    def Fehler_Output(self, Fehler, La_error, error_Message_Log_GUI = '', error_Message_Ablauf = '', device = ''):
        ''' Erstelle Fehler-Nachricht für GUI, Ablaufdatei und Logging
        Args:
            Fehler (bool):                  False -> o.k. (schwarz), True -> Fehler (rot, bold)
            La_error (PyQt-Label):          Label das beschrieben werden soll (Objekt)
            error_Message_Log_GUI (str):    Nachricht die im Log und der GUI angezeigt wird
            error_Message_Ablauf (str):     Nachricht für die Ablaufdatei
            device (str):                   Wenn ein anderes Gerät genutzt wird (z.B. PID)
        ''' 
        if device == '':
            device_name = self.device_name
        else:
            device_name = device
        if Fehler:
            La_error.setText(self.err_0_str[self.sprache])
            La_error.setToolTip(error_Message_Log_GUI)  
            La_error.setStyleSheet(f"color: red; font-weight: bold")
            zusatz = f'({self.str_Size_1[self.sprache]})' if La_error == self.La_error_1 else (f'({self.str_Size_2[self.sprache]})' if La_error == self.La_error_2 else '')
            log_vorberietung = error_Message_Log_GUI.replace("\n"," ") 
            logger.error(f'{device_name} - {log_vorberietung} {zusatz}')
        else:
            La_error.setText(self.err_13_str[self.sprache])
            La_error.setToolTip('')
            La_error.setStyleSheet(f"color: black; font-weight: normal")
        if not error_Message_Ablauf == '':
                self.add_Text_To_Ablauf_Datei(f'{device_name} - {error_Message_Ablauf}') 

    ##########################################
    # Reaktion auf Buttons:
    ##########################################
    def fahre_links(self):
        '''Synchron Knopf Achse'''
        if float(self.LE_Speed.text().replace(",", ".")) < 0:
            self.fahre_Runter()                                             # Minus
        else:
            self.fahre_Hoch()                                               # Plus

    def fahre_Hoch(self):
        '''Reaktion auf den Linken Knopf'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_45_str[self.sprache]}')
            ans = self.controll_value()
            if not ans == '':
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = ans
                else:
                    self.write_value['Speed'] = ans
                self.write_task['Hoch'] = True
                self.write_task['Send'] = True
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def fahre_Runter(self):
        '''Reaktion auf den Rechten Knopf'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_46_str[self.sprache]}')
            self.write_task['Runter'] = True
            ans = self.controll_value()
            if not ans == '':
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = ans
                else:
                    self.write_value['Speed'] = ans 
                self.write_task['Runter'] = True
                self.write_task['Send'] = True
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def Stopp(self, n = 1):
        '''Halte Achse an'''
        if self.init:
            if n == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_47_str[self.sprache]}')
            elif n == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_90_str[self.sprache]}')
            elif n == 6: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_3[self.sprache]}')
            self.RezEnde(n)
            # Sende Befehl:
            self.write_task['Stopp'] = True
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])
    
    def define_home(self):
        ''' Sorgt dafür das die aktuelle Position zur Null wird.'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_39_str[self.sprache]}')
            self.write_task['Define Home'] = True

            # Grenzen Updaten:
            with open(self.config_dat, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"{self.Log_Text_56_str[self.sprache]} {config}") 
            
            self.oGs = config['devices'][self.device_name]["limits"]['maxPos']
            self.uGs = config['devices'][self.device_name]["limits"]['minPos']
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    ##########################################
    # Eingabefeld Kontrolle:
    ##########################################
    def controll_value(self):
        ''' Kontrolliere die Eingabe eines Eingabefeldes.

        Return:
            '' (str):               Fehlerfall
            speed_value (float):    Geschwindigkeitswert
        '''
        # Eingebabefeld auslesen:
        speed_value = self.LE_Speed.text().replace(",", ".")
        speed_okay = False

        # Auswahl Limits Sollwert:
        if self.PID_cb.isChecked():
            oGv = self.oGx
            uGv = self.uGx 
        else:
            oGv = self.oGv
            uGv = self.uGv

        # Wenn eins der beiden Eingabefelder leer ist, dann sende nicht:
        if speed_value == '':
            self.Fehler_Output(1, self.La_error_1, self.err_1_str[self.sprache], self.Text_48_str[self.sprache])
        else:
            # Kontrolle Position:
            try:
                # Umwandeln Position:
                speed_value = float(speed_value)
                # Kontrolliere die Grenzen/Limits:
                if speed_value < uGv or speed_value > oGv:
                    self.Fehler_Output(1, self.La_error_1, f'{self.err_2_str[self.sprache]} {uGv} {self.err_3_str[self.sprache]} {oGv}', self.Text_42_str[self.sprache])     
                # Alles in Ordnung mit der Eingabe:
                else:
                    self.Fehler_Output(0, self.La_error_1)
                    speed_okay = True
            # Eingabe ist falsch:
            except:
                self.Fehler_Output(1, self.La_error_1, self.err_5_str[self.sprache], self.Text_43_str[self.sprache])

        # Alles Okay:
        if speed_okay:
            return abs(speed_value)
        # Rückgabe bei Fehler:
        return ''

    ##########################################
    # Reaktion Checkbox:
    ##########################################    
    def PID_ON_OFF(self):                       
        if self.PID_cb.isChecked():
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_1[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID'] = True
            self.write_task['Send'] = False
            self.Stopp(6)
        else:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_2[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID'] = False
            self.write_task['Send'] = False  
            self.Stopp(6)
            try:
                value = float(str(self.config['PID']['umstell_wert'].replace(',', '.')))
            except:
                value = 0
            self.LE_Speed.setText(str(value))
            if value > self.oGv or value < self.uGv:
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_Ex[self.sprache]}") 
                self.write_value['Speed'] = self.uGv
            else:
                self.write_value['Speed'] = value

    ##########################################
    # Betrachtung der Labels und Plots:
    ##########################################
    def update_GUI(self, value_dict, x_value):
        ''' Update der GUI, Plot und Label!

        Args:
            value_dict (dict):  Dictionary mit den aktuellen Werten!
            x_value (list):     Werte für die x-Achse
        '''

        ## PID-Modus - Werte Anzeige und Farbe:
        if self.PID_cb.isChecked():
            self.La_SollSpeed.setText(self.x_str[self.sprache])
            if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: {self.color[6]}")
        else:
            self.La_SollSpeed.setText(self.v_str[self.sprache])
            if self.color_Aktiv: self.La_SollSpeed.setStyleSheet(f"color: {self.color[2]}")
               
        ## Kurven Update:
        self.data.update({'Time' : x_value[-1]})                    
        self.data.update(value_dict)   

        for messung in value_dict:
            if not 'Gs' in messung and not 'Gv'in messung and not 'Status' in messung:
                if not 'SWs' in messung:
                    self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}')
                self.listDict[messung].append(value_dict[messung])
                if not self.curveDict[messung] == '':
                    faktor = self.skalFak_dict[messung]
                    y = [a * faktor for a in self.listDict[messung]]
                    self.curveDict[messung].setData(x_value, y)

        # Grenz-Kurven:
        ## Update Grenzwert-Dictionary:
        self.grenzValueDict['oGv']  = self.oGv              * self.skalFak['Speed_2']
        self.grenzValueDict['uGv']  = self.uGv              * self.skalFak['Speed_2']
        self.grenzValueDict['oGs']  = value_dict['oGs']     * self.skalFak['Pos']
        self.grenzValueDict['uGs']  = value_dict['uGs']     * self.skalFak['Pos']
        ## Update-Kurven:
        for kurve in self.kurven_dict:
            if kurve in self.grenzListDict:
                self.grenzListDict[kurve].append(float(self.grenzValueDict[kurve]))
                self.kurven_dict[kurve].setData(x_value, self.grenzListDict[kurve])

        # Status-Meldung:
        status_1 = value_dict['Status']
        status_1 = self.status_report_umwandlung(status_1)

        label_s1 = ''
        status = [self.sta_Bit0_str[self.sprache], self.sta_Bit1_str[self.sprache] , self.sta_Bit2_str[self.sprache], self.sta_Bit3_str[self.sprache], self.sta_Bit4_str[self.sprache], self.sta_Bit5_str[self.sprache], self.sta_Bit6_str[self.sprache], self.sta_Bit7_str[self.sprache] , self.sta_Bit8_str[self.sprache] , self.sta_Bit9_str[self.sprache], self.sta_Bit10_str[self.sprache], self.sta_Bit11_str[self.sprache], '', '', '', self.sta_Bit15_str[self.sprache]]
        # status = ['Betriebsbereit', 'Achse referiert', 'Achse Fehler', 'Antrieb läuft', 'Antrieb läuft aufwärts', 'Antrieb läuft abwärts', 'Achse Position oben', 'Achse Position unten', 'Achse Endlage oben', 'Achse Endlage unten', 'Software-Endlagen aus', 'Achse in Stopp']
        l = len(status_1)
        for n in range(0,l):
            if status_1[n] == '1':
                if not status[n] == '':
                    label_s1 = label_s1 + f'{status[n]}, '
        if label_s1 == '':
            label_s1 = self.status_2_str[self.sprache]
        else:
            label_s1 = label_s1[:-2]
        self.La_Status.setText(f'{self.status_3_str[self.sprache]} {label_s1}')

    def status_report_umwandlung(self, StatusInteger):
        ''' Umwandlung des Status - Integer zu Umgedrehten Binärcode: \n
        Beispiel:   \n
                    512                 - StatusInteger (Args) \n
                    10 0000 0000        - Lower Byte, Higher Byte \n
                    0000 0000           - Higher Byte \n
                    0000 0010           - Lower Byte \n
                    0000 0000 0000 0010 - Gewollte Bit-Folge \n
                    0100 0000 0000 0000 - Umkehren um mit Liste zu Vergleichen
        '''

        status = bin(StatusInteger)[2:]            # Status Integer in Binär-Code
        l = len(status)                            # Länge bestimmen

        anz = int(l/8)                             # Anzahl von vollen Byte auslesen

        # Bytes aus den String lesen:
        byte_list = []
        for n in range(0,anz):
            byte_list.append(status[-8:])
            status = status[0:-8]

        # Unvolständige Bytes Auffüllen und auf 8 Bit kürzen:
        if len(status) < 8 and not status == '':
            status = '0000000' + status
            byte_list.append(status[-8:])
        elif status == '' and len(byte_list) == 1:
            byte_list.append('00000000')

        # Byte zusammensetzen in der richtigen Reihenfolge:
        byte_string = ''
        for n in byte_list:
            byte_string = byte_string + n
       
        return byte_string[::-1]                    # [::-1] --> dreht String um! (Lowest Bit to Highest Bit)

    ##########################################
    # Reaktion auf Initialsierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung soll durch geführt werden '''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_23_str[self.sprache]}')
        self.write_task['Init'] = True

    def init_controll(self, init_okay, menu):
        ''' Anzeige auf GUI ändern

        Args:
            init_okay (bool):   Ändert die Init-Variable und das Icon in der GUI, je nach dem wie das Gerät entschieden hat!
            menu (QAction):     Menü Zeile in der das Icon geändert werden soll!
        '''
        if init_okay:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_Okay.png"))
            self.Fehler_Output(0, self.La_error_1)
            self.init = True
        else:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_nicht_Okay.png"))
            self.init = False

    ##########################################
    # Reaktion auf übergeordnete Butttons:
    ##########################################
    def update_Limit(self):
        '''Lese die Config und Update die Limits'''

        # Yaml erneut laden:
        with open(self.config_dat, encoding="utf-8") as f: 
            config = yaml.safe_load(f)
            logger.info(f"{self.device_name} - {self.Log_Text_205_str[self.sprache]} {config}")
        
        self.oGv = config['devices'][self.device_name]["limits"]['maxSpeed']
        self.uGv = config['devices'][self.device_name]["limits"]['minSpeed']
        self.oGs = config['devices'][self.device_name]["limits"]['maxPos']
        self.uGs = config['devices'][self.device_name]["limits"]['minPos']
        self.oGx = config['devices'][self.device_name]['PID']['Input_Limit_max']
        self.uGx = config['devices'][self.device_name]['PID']['Input_Limit_min']

        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGv} {self.Log_Text_LB_4[self.sprache]} {self.oGv} {self.einheit_v_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGs} {self.Log_Text_LB_4[self.sprache]} {self.oGs} {self.einheit_s_einzel[self.sprache]}')

        self.write_task['Update Limit']     = True
        self.write_value['Limits']          = [self.oGs, self.uGs, self.oGv, self.uGv, self.oGx, self.uGx]

    ##########################################
    # Reaktion auf Rezepte:
    ##########################################
    def RezStart(self, execute = 1):
        ''' Rezept wurde gestartet '''
        if self.init:
            if not self.Rezept_Aktiv:
                if execute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_87_str[self.sprache]}')
                elif execute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_85_str[self.sprache]}')
            
                # Variablen:                                                                   # Kontrolle ob alles mit Rezept stimmt
                self.step = 0
                self.Rezept_Aktiv = True

                # Kurve erstellen:
                error = self.RezKurveAnzeige()
                if self.cb_Rezept.currentText() == '------------':
                    self.Fehler_Output(1, self.La_error_1, self.err_15_str[self.sprache])
                    error = True

                if not error:
                    # Rezept Log-Notiz:
                    logger.info(f'{self.device_name} - {self.Log_Text_39_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}')
                    logger.info(f'{self.device_name} - {self.Log_Text_40_str[self.sprache]} {self.rezept_daten}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_24_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}') 

                    # Erstes Element senden:
                    if self.PID_cb.isChecked():
                        self.write_value['PID-Sollwert'] = self.value_list[self.step]

                        if self.move_list[self.step] == 'UP':
                            self.write_task['Hoch'] = True
                            self.write_task['Runter'] = False
                        elif self.move_list[self.step] == 'DOWN':
                            self.write_task['Runter'] = True
                            self.write_task['Hoch'] = False
                    else:
                        self.write_value['Speed'] = abs(self.value_list[self.step])

                        if self.value_list[self.step] < 0:             # Nachsehen: Wie was sich bei Hoch und Runter verhält bei Geschwindigkeit!
                            self.write_task['Runter'] = True
                            self.write_task['Hoch'] = False
                        else:
                            self.write_task['Hoch'] = True
                            self.write_task['Runter'] = False
                    self.write_task['Send'] = True

                    # Elemente GUI sperren:
                    self.cb_Rezept.setEnabled(False)
                    self.btn_rezept_start.setEnabled(False)
                    self.btn_hoch.setEnabled(False)
                    self.btn_mitte.setEnabled(False)
                    self.btn_runter.setEnabled(False)
                    self.btn_DH.setEnabled(False)
                    self.Auswahl.setEnabled(False)
                    self.PID_cb.setEnabled(False)

                    # Timer Starten:
                    self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))
                    self.RezTimer.start()
                    self.Fehler_Output(0, self.La_error_1)
                else:
                    self.Rezept_Aktiv = False
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_88_str[self.sprache]}')
            else:
                self.Fehler_Output(1, self.La_error_1, self.err_16_str[self.sprache], self.Text_84_str[self.sprache])
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def RezEnde(self, excecute = 1):
        ''' Rezept wurde/wird beendet '''
        if self.init:
            if self.Rezept_Aktiv == True:
                if excecute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_81_str[self.sprache]}')
                elif excecute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_82_str[self.sprache]}')
                elif excecute == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_83_str[self.sprache]}')
                elif excecute == 4: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_86_str[self.sprache]}')
                elif excecute == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_91_str[self.sprache]}')
                elif excecute == 6: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_4[self.sprache]}')

                # Elemente GUI entsperren:
                self.cb_Rezept.setEnabled(True)
                self.btn_rezept_start.setEnabled(True)
                self.btn_hoch.setEnabled(True)
                self.btn_mitte.setEnabled(True)
                self.btn_runter.setEnabled(True)
                self.btn_DH.setEnabled(True)
                self.Auswahl.setEnabled(True)
                self.PID_cb.setEnabled(True)

                # Variablen:
                self.Rezept_Aktiv = False

                # Auto Range
                self.typ_widget.plot.AutoRange()

                # Nachricht:
                self.Fehler_Output(0, self.La_error_1)

                # Timer stoppen:
                self.RezTimer.stop()
            else:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_89_str[self.sprache]}')
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])

    def Rezept(self):
        ''' Rezept Schritt wurde beendet, Vorbereitung und Start des neuen '''
        self.step += 1
        if self.step > len(self.time_list) - 1:
            self.Stopp(2)
        else:
            self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))

            # Nächstes Element senden:
            if self.PID_cb.isChecked():
                self.write_value['PID-Sollwert'] = self.value_list[self.step]

                if self.move_list[self.step] == 'UP':
                    self.write_task['Hoch'] = True
                    self.write_task['Runter'] = False
                elif self.move_list[self.step] == 'DOWN':
                    self.write_task['Runter'] = True
                    self.write_task['Hoch'] = False
            else:
                self.write_value['Speed'] = abs(self.value_list[self.step])

                if self.value_list[self.step] < 0:
                    self.write_task['Runter'] = True
                    self.write_task['Hoch'] = False
                else:
                    self.write_task['Hoch'] = True
                    self.write_task['Runter'] = False
            self.write_task['Send'] = True

    def Rezept_lesen_controll(self):
        ''' Rezept wird ausgelesen und kontrolliert. Bei Fehler werden die Fehlermeldungen beschrieben auf der GUI.

        Return:
            error (Bool):   Fehler vorhanden oder nicht
        '''
        # Variablen:
        error = False
        self.time_list  = []
        self.value_list = []
        self.move_list  = []

        ## Geschwindigkeitlimits:
        uG = self.uGv
        oG = self.oGv

        ## Positionslimits:
        uGs = self.uGs
        oGs = self.oGs

        ## PID-Limits:
        if self.PID_cb.isChecked():
            oG = self.oGx
            uG = self.uGx 

        ## Aktueller Wert Geschwindigkeit:
        ak_value = self.ak_value['IWv'] if not self.ak_value == {} else 0

        # Rezept lesen:
        rezept = self.cb_Rezept.currentText()
        pos_list = [] 
        try:
            start_pos = self.posList[-1]
        except:
            error = True 

        if not rezept == '------------' and not error:
            ## Rezept aus Datei oder in Config:
            ak_rezept = self.rezept_config[rezept]
            if 'dat' in ak_rezept:
                try:
                    with open(f'vifcon/rezepte/{ak_rezept["dat"]}', encoding="utf-8") as f:
                        rez_dat = yaml.safe_load(f)
                    self.rezept_datei = f'({ak_rezept["dat"]})'
                except:
                    self.Fehler_Output(1, self.La_error_1, self.err_10_str[self.sprache])
                    logger.exception(self.Log_Text_Ex1_str[self.sprache])
                    return False
            else:
                rez_dat = ak_rezept
                self.rezept_datei = '(Config-Datei)'
            ## Speichere aktuelle Daten des Rezepts für Logging:
            self.rezept_daten = rez_dat
            ## Ersten Eintrag prüfen:
            first_line = rez_dat[list(rez_dat.keys())[0]].split(';')[2]
            if first_line.strip() == 'r' and not self.ak_value == {}:
                self.value_list.append(ak_value) 
                self.time_list.append(0) 
            elif first_line.strip() == 'r' and self.ak_value == {}:
                self.Fehler_Output(1, self.La_error_1, self.err_12_str[self.sprache])
                return False
            ## Bewegungsrichtung für PID-Modus prüfen:
            if self.PID_cb.isChecked():
                for n in rez_dat:
                    try:
                        werte = rez_dat[n].split(';')
                        if werte[2].strip() == 'r': sNum = 4
                        elif werte[2].strip() == 's': sNum = 3
                        if not werte[sNum].upper().strip() in ['UP', 'DOWN']:  
                            self.Fehler_Output(1, self.La_error_1, f'{self.err_PID_1_str[self.sprache]} {werte[sNum].upper()} {self.err_PID_2_str[self.sprache]}')
                            return False
                    except:
                        self.Fehler_Output(1, self.La_error_1, self.err_PID_3_str[self.sprache])
                        return False
            ## Rezept Kurven-Listen erstellen:
            for n in rez_dat:
                werte = rez_dat[n].split(';')
                ## Beachtung von Kommas (Komma zu Punkt):
                time = float(werte[0].replace(',', '.'))
                value = float(werte[1].replace(',','.'))
                ## Kontrolle Geschwindigkeit:
                if value < uG or value > oG:
                    error = True
                    self.Fehler_Output(1, self.La_error_1, f'{self.err_6_str[self.sprache]} {value} {self.err_7_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG}!')
                    break
                else:
                    self.Fehler_Output(0, self.La_error_1)
                ## Rampe oder Sprung:
                ### Rampe:
                if werte[2].strip() == 'r':                         
                    rampen_config_step = float(werte[3])                # Zeitabstand für den Rampensprung (x-Achse)
                    rampen_bereich = value - self.value_list[-1]        # Bereich in dem die Rampe wirkt: Aktueller Wert - Letzten Eintrag (Rezept Stufe)
                    rampen_value = int(time/rampen_config_step)         # Anzahl der Rampensprünge
                    rampen_step = rampen_bereich/rampen_value           # Höhe des Sprungs je Rampensprung (y-Achse)
                    #### Berechnung der Listen Elemente:
                    for rampen_n in range(1,rampen_value+1):
                        if not rampen_n == rampen_value:
                            ak_ramp = self.value_list[-1] + rampen_step
                            self.value_list.append(round(ak_ramp,3))    # Runden: Eurotherm könnte bis 6 Nachkommerstellen, Display nur 2
                            self.time_list.append(rampen_config_step)
                        else: # Letzter Wert!
                            self.value_list.append(value)
                            self.time_list.append(rampen_config_step)   # 0 
                        if self.PID_cb.isChecked(): self.move_list.append(werte[4].upper().strip())
                ### Sprung:
                else:                                               
                    self.value_list.append(value)
                    self.time_list.append(time)
                    if self.PID_cb.isChecked(): self.move_list.append(werte[3].upper().strip())
            if not self.PID_cb.isChecked():
                ## Positionen bestimmen:
                value_step = 0
                for n_PosP in self.value_list:
                    pos_list.append(1/60 * n_PosP * self.time_list[value_step])
                    value_step += 1
                
                ## Kontrolle Position:
                logger.debug(f"{self.device_name} - {self.Log_Text_57_str[self.sprache]} {pos_list}")
                rezept_schritt = 1 
                for n in pos_list:
                    pos = start_pos + n
                    start_pos = pos
                    if pos < uGs or pos > oGs:
                        error = True
                        self.Fehler_Output(1, self.La_error_1, f'{self.err_9_str[self.sprache]} {rezept_schritt} {self.err_7_str[self.sprache]} {uGs} {self.err_3_str[self.sprache]} {oGs}!')
                        break
                    else:
                        self.Fehler_Output(0, self.La_error_1)
                    rezept_schritt += 1
        else:
            self.Fehler_Output(0, self.La_error_1)
        return error
    
    def RezKurveAnzeige(self):
        '''Soll die Rezept-Kurve anzeigen und erstellen!
        
        Return:
            error (bool):   Rezeptfehler
        '''
        # Variablen:
        error = False                                                                        # Kontrolle ob alles mit Rezept stimmt  

        # Kurven zurücksetzen:
        self.RezTimeList = []
        self.RezValueList = []    

        anzeigev = True 
        if not self.PID_cb.isChecked():                        
            try: self.curveDict['Rezv'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigev  = False        
        else:
            try: self.curveDict['Rezx'].setData(self.RezTimeList, self.RezValueList)
            except: anzeigev  = False                        

        # Startzeit bestimmen:
        ak_time_1 = datetime.datetime.now(datetime.timezone.utc).astimezone()                # Aktuelle Zeit Absolut
        ak_time = round((ak_time_1 - self.typ_widget.start_zeit).total_seconds(), 3)         # Aktuelle Zeit Relativ

        # Fehler-Kontrolle:
        error = self.Rezept_lesen_controll()

        if not error:
            # Kurve erstellen:
            i = 0
            for n in self.time_list:
                # Punkt 1:
                self.RezTimeList.append(ak_time)
                self.RezValueList.append(self.value_list[i])
                # Punkt 2:
                self.RezTimeList.append(ak_time + n)
                self.RezValueList.append(self.value_list[i])
                # nächsten Punkt vorbereiten:
                ak_time = ak_time + n
                i += 1

            # Kurve erstellen mit Skalierungsfaktor:
            if not self.PID_cb.isChecked(): faktor = self.skalFak['Speed_2']
            else:                           faktor = self.skalFak['PIDA']
            
            y = [a * faktor for a in self.RezValueList]
            
            # Kurve Anzeigen:
            if anzeigev:
                if not self.PID_cb.isChecked(): 
                    self.curveDict['Rezv'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_2.autoRange()                            # Rezept Achse 2 wird nicht fertig angezeigt, aus dem Grund wird dies durchgeführt! Beim Enden wird die AutoRange Funktion von base_classes.py durchgeführt. Bewegung des Plots sind mit der Lösung nicht machbar!!
                                                                                        # Plot wird nur an Achse 1 (links) angepasst!
                else:
                    self.curveDict['Rezx'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_1.autoRange()

        return error

    def update_rezept(self):
        '''Liest die Config im Sinne der Rezepte neu ein und Updatet die Combo-Box'''
        if not self.Rezept_Aktiv:
            # Trennen von der Funktion:
            self.cb_Rezept.currentTextChanged.disconnect(self.RezKurveAnzeige)                    # Benötigt um Aufruf bei Leerer ComboBox zu vermeiden (sonst KeyError: '')

            # Combo-Box leeren:
            self.cb_Rezept.clear() 

            # Yaml erneut laden:
            with open(self.config_dat, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Config einlesen für das Gerät:
            self.rezept_config = config['devices'][self.device_name]['rezepte']
            
            # Combo-Box neu beschreiben:
            self.cb_Rezept.addItem('------------')
            try:
                for rezept in self.rezept_config:
                    self.cb_Rezept.addItem(rezept) 
            except Exception as e:
                self.Fehler_Output(1, self.err_21_str[self.sprache])
                logger.exception(self.Log_Text_Ex2_str[self.sprache]) 

            # Neu verbinden von der Funktion:
            self.cb_Rezept.currentTextChanged.connect(self.RezKurveAnzeige) 

            self.Fehler_Output(0, self.La_error_1)
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_14_str[self.sprache])

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''
