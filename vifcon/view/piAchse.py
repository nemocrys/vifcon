# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
PI-Achse mit Mercury-DC-Motor Controller Widget:
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
    QRadioButton,
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


class PIAchseWidget(QWidget):
    def __init__(self, sprache, Frame_Anzeige, widget, line_color, config, config_dat, start_werte, neustart, add_Ablauf_function, piAchse, gamepad_aktiv, typ = 'Antrieb', parent=None):
        """ GUI widget of PI-Achse.

        Args:
            sprache (int):                  Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):           Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (obj):                   Element in das, das Widget eingefügt wird
            line_color (list):              Liste mit drei Farben
            config (dict):                  Konfigurationsdaten aus der YAML-Datei
            config_dat (string):            Datei-Name der Config-Datei
            start_werte (dict):             Start-Werte nach Initialisierung der Achse
            neustart (bool):                Neustart Modus, Startkonfigurationen werden übersprungen
            add_Ablauf_function (Funktion): Funktion zum updaten der Ablauf-Datei.
            piAchse (str):                  Name des Gerätes (wird für DH dringend gebraucht!)
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
        self.akPos                      = start_werte['IWs']
        self.neustart                   = neustart
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = piAchse
        self.typ                        = typ

        ## Status der Achse (Notiz: beide kombinieren!):
        self.losgefahren = False
        self.Achse_steht = True
    
        ## Aus Config:
        ### Zum Start:
        self.init = self.config['start']['init']
        self.mode = self.config['start']['mode']
        ### Parameter:        
        self.cpm  = self.config["parameter"]['cpm']
        ### Limits:
        self.oGPos  = self.config["limits"]['maxPos']
        self.uGPos  = self.config["limits"]['minPos']
        self.oGv    = self.config["limits"]['maxSpeed']
        self.uGv    = self.config["limits"]['minSpeed']
        ### GUI:
        self.legenden_inhalt = self.config['GUI']['legend'].split(';')
        self.legenden_inhalt = [a.strip() for a in self.legenden_inhalt]    # sollten Unnötige Leerzeichen vorhanden sein, so werden diese entfernt!
        ### Rezepte:
        self.rezept_config = self.config["rezepte"]
        ### Gamepad:
        self.Button_Link = self.config['gamepad_Button']

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
        ## Label:                                                   
        self.pos_1_str          = ['Fahrweg',                                                                                                   'Route']
        self.pos_2_str          = ['Sollposition',                                                                                              'Target position']
        pos_rel_str             = ['relativ',                                                                                                   'relative']
        pos_abs_str             = ['absolut',                                                                                                   'absolute']
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
        ## Einheiten mit Größe:
        self.s_str              = ['in mm:',                                                                                                    'in mm:']
        v_str                   = ['v in mm/s:',                                                                                                'v in mm/s:']
        sv_str                  = ['v:',                                                                                                        'v:']
        st_v_str                = ['XXX.XX mm/s',                                                                                               'XXX.XX mm/s']
        st_s_str                = ['XXX.XX mm',                                                                                                 'XXX.XX mm']
        s_einzel_str            = ['s',                                                                                                         's']
        v_einzel_str            = ['v',                                                                                                         'v']
        ## Fehlermeldungen: 
        self.err_0_str          = ['Fehler!',                                                                                                   'Error!']
        self.err_1_str          = ['Beide Felder benötigen\neine EINGABE!!',                                                                    'Both fields require\nan INPUT!!']
        self.err_2_str          = ['Grenzen überschritten!\nGrenzen von',                                                                       'Limits exceeded!\nLimits from']
        self.err_3_str          = ['bis',                                                                                                       'to']
        self.err_4_str          = ['Gerät anschließen und\nInitialisieren!',                                                                    'Connect the device\nand initialize!']
        self.err_5_str          = ['Fehlerhafte Eingabe!',                                                                                      'Incorrect input!']
        self.err_6_str          = ['Der Wert',                                                                                                  'The value']
        self.err_7_str          = ['überschreitet\ndie Grenzen von',                                                                            'exceeds\nthe limits of']
        self.err_8_str          = ['Eingabe muss Positiv sein,\nbei Auswahl rel. Position!',                                                    'Input must be positive, if\nrelative position is selected!']
        self.err_9_str          = ['Der Schritt',                                                                                               'Step']
        self.err_10_str         = ['Rezept Einlesefehler!',                                                                                     'Recipe import error!']
        self.err_12_str         = ['Erster Schritt = Sprung!\nDa keine Messwerte!',                                                             'First step = jump! There\nare no measurements!']
        self.err_13_str         = ['o.K.',                                                                                                      'o.K.']   
        self.err_14_str         = ['Rezept läuft!\nRezept Einlesen gesperrt!',                                                                  'Recipe is running!\nReading recipes blocked!']
        self.err_15_str         = ['Wähle ein Rezept!',                                                                                         'Choose a recipe!']
        self.err_16_str         = ['Rezept läuft!\nRezept Start gesperrt!',                                                                     'Recipe running!\nRecipe start blocked!']
        self.err_21_str         = ['Fehler in der Rezept konfiguration\nder Config-Datei! Bitte beheben und Neueinlesen!',                      'Error in the recipe configuration of\nthe config file! Please fix and re-read!']
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
        self.Log_Text_45_str    = ['Verriegelungsmodus 1 aktiv - Knöpfe werden bei Bewegung nicht verriegelt!',                                 'Locking mode 1 active - buttons are not locked when moved!']
        self.Log_Text_46_str    = ['Verriegelungsmodus 2 aktiv - Knöpfe werden durch einen Timer entriegelt!',                                  'Locking mode 2 active - buttons are unlocked by a timer!']
        self.Log_Text_47_str    = ['Verriegelungsmodus 3 aktiv - Knöpfe werden bei erreichen von 0 mm/s entriegelt!',                           'Locking mode 3 active - buttons are unlocked when 0 mm/s is reached!']
        self.Log_Text_48_str    = ['Verriegelungsmodus unbekannt!',                                                                             'Locking mode unknown!']
        self.Log_Text_49_str    = ['Stopp!',                                                                                                    'Stop!']
        self.Log_Text_50_str    = ['Zeit des Verriegelungs Timers kann nicht bestimmt werden! Setze Zeit auf 10 ms!',                           'Time of the locking timer cannot be determined! Set time to 10 ms!']
        self.Log_Text_51_str    = ['Zu fahrende Position:',                                                                                     'Position to travel:']
        self.Log_Text_52_str    = ['Konfiguration aktualisieren (Nullpunkt setzen PI):',                                                        'Update configuration (Define-Home PI):']
        self.Log_Text_53_str    = ['Fehlerhafte Eingabe bei Position - Grund:',                                                                 'Incorrect entry at position - Reason:']
        self.Log_Text_54_str    = ['Fehlerhafte Eingabe bei Geschwindigkeit - Grund:',                                                          'Incorrect input for speed - Rreason:']
        self.Log_Text_55_str    = ['Rezept hat folgende zu fahrende Weg-Abfolge:',                                                              'Recipe has the following route sequence to be traveled:']
        self.Log_Text_205_str   = ['Update Konfiguration (Update Limits):',                                                                     'Update configuration (update limits):']
        self.Log_Text_Ex1_str   = ['Fehler Grund (Rezept einlesen):',                                                                           'Error reason (reading recipe):']
        self.Log_Text_Ex2_str   = ['Fehler Grund (Problem mit Rezept-Konfiguration):',                                                          'Error reason (Problem with recipe configuration)']
        ## Ablaufdatei: 
        self.Text_23_str        = ['Knopf betätigt - Initialisierung!',                                                                         'Button pressed - initialization!']
        self.Text_24_str        = ['Ausführung des Rezeptes:',                                                                                  'Execution of the recipe:']
        self.Text_31_str        = ['Auswahl relative Position (Fahrweg Angabe)!',                                                               'Select relative position (travel path information)!']
        self.Text_32_str        = ['Auswahl absolute Position (Konkrette Position)!',                                                           'Select absolute position (concrete position)!']
        self.Text_33_str        = ['Knopf betätigt - Stopp/Alle Stopp!',                                                                        'Button pressed - Stop/All Stop!']
        self.Text_34_str        = ['betätigt - Sende Geschwindigkeit und Position/Fahrweg!',                                                    'pressed - send speed and position/travel!']
        self.Text_35_str        = ['Setze die Geschwindigkeit auf',                                                                             'Set the speed up to']
        self.Text_36_str        = ['mm/s!',                                                                                                     'mm/s!']
        self.Text_37_str        = ['Setze den Fahrweg auf',                                                                                     'Set up the driveway to']
        self.Text_38_str        = ['mm!',                                                                                                       'mm!']
        self.Text_39_str        = ['Knopf betätigt - Nullpunkt setzen!',                                                                        'Button pressed - Define Home!']
        self.Text_40_str        = ['Eingabefeld Fehlermeldung: Keine oder Fehlende Eingabe!',                                                   'Input field error message: No or missing input!']
        self.Text_41_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen bei, da relative Positionen positiv sein müssen!',         'Input field error message: Sending failed because relative positions must be positive!']
        self.Text_42_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da Grenzen überschritten werden!',                        'Input field error message: Sending failed because limits were exceeded!']
        self.Text_43_str        = ['Eingabefeld Fehlermeldung: Senden fehlgeschlagen, da fehlerhafte Eingabe!',                                 'Input field error message: Sending failed due to incorrect input!']
        self.Text_44_str        = ['Achse steht wieder!',                                                                                       'Axis is standing again!']
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
        ## Extra:
        self.abLauf_Button_r    = ['rechter Knopf',                                                                                             'right button']
        self.abLauf_Button_l    = ['linker Knopf',                                                                                              'left button']    

        #---------------------------------------
        # Konfigurationen für das Senden:
        #---------------------------------------
        #self.send_betätigt = False
        self.write_task = {'Stopp': False, 'Sende Position': False, 'Sende Speed': False, 'Init':False, 'Define Home': False, 'Start':False}
        self.write_value = {'Position': 0, 'Speed': 0}

        # Wenn Init = False, dann werden die Start-Auslesungen nicht ausgeführt:
        if self.init and not self.neustart:
            self.write_task['Start'] = True
        
        #---------------------------------------
        # Nachrichten im Log-File:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_28_str[self.sprache]}") if self.init else logger.warning(f"{self.device_name} - {self.Log_Text_29_str[self.sprache]}")
        if self.neustart: logger.info(f"{self.device_name} - {self.Log_Text_30_str[self.sprache]}") 
        logger.info(f"{self.device_name} - {self.Log_Text_45_str[self.sprache]}") if self.mode == 0 else (logger.info(f"{self.device_name} - {self.Log_Text_46_str[self.sprache]}") if self.mode == 1 else (logger.info(f"{self.device_name} - {self.Log_Text_47_str[self.sprache]}") if self.mode == 2 else logger.warning(f"{self.device_name} - {self.Log_Text_48_str[self.sprache]}"))) 

        #---------------------------------------
        # GUI:
        #---------------------------------------
        ## Icon Bestimmung:
        if self.config["GUI"]['bewegung'] == 'y':
            self.icon_1 = "./vifcon/icons/p_links.png"               
            self.icon_2 = "./vifcon/icons/p_rechts.png"          
        elif self.config["GUI"]['bewegung'] == 'x':
            self.icon_1 = "./vifcon/icons/p_raus.png"               
            self.icon_2 = "./vifcon/icons/p_rein.png"    
        elif self.config["GUI"]['bewegung'] == 'z':
            self.icon_1 = "./vifcon/icons/p_hoch.png"               
            self.icon_2 = "./vifcon/icons/p_runter.png"  
        
        #________________________________________
        ## Richtungszuordnung:
        ausrichtung = self.config["GUI"]['piSymbol'].upper()
        if ausrichtung == 'RE' or ausrichtung == 'HI' or ausrichtung == 'UN':
            self.links = 'Plus'
            self.rechts = 'Minus' 
        else: 
            self.links = 'Minus'
            self.rechts = 'Plus'  
        #________________________________________    
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
        self.layer_layout.setRowMinimumHeight(1, 30)    # Error-Nachricht
        self.layer_layout.setRowMinimumHeight(2, 30)    # Error-Nachricht

        ### Spaltenbreiten:
        self.layer_layout.setColumnMinimumWidth(0, 120)
        self.layer_layout.setColumnMinimumWidth(2, 60)
        self.layer_layout.setColumnMinimumWidth(4, 100)
        #________________________________________
        ## Widgets:
        ### Eingabefelder:
        self.LE_Pos = QLineEdit()
        self.LE_Pos.setText(str(self.config["defaults"]['startPos']))

        self.LE_Speed = QLineEdit()
        self.LE_Speed.setText(str(self.config["defaults"]['startSpeed']))

        ### Checkbox:
        self.Auswahl = QCheckBox(cb_sync_str[self.sprache])
        self.gamepad = QCheckBox(cb_gPad_str[self.sprache])
        
        if not gamepad_aktiv:
            self.gamepad.setEnabled(False)

        ### Label:
        #### Titel-Gerät:
        self.La_name = QLabel(f'<b>{piAchse}</b>')
        #### Fehlernachrichten:
        self.La_error_1 = QLabel(self.err_13_str[self.sprache])
        self.La_error_2 = QLabel(self.err_13_str[self.sprache])
        #### Istposition:
        self.La_IstPos_text = QLabel(f"{istwert_str[self.sprache]}-{self.config['GUI']['bewegung']}: ")
        self.La_IstPos_wert = QLabel(st_s_str[self.sprache])
        self.La_IstPos_text.setStyleSheet(f"color: {self.color[0]}")
        self.La_IstPos_wert.setStyleSheet(f"color: {self.color[0]}")
        #### Istgeschwindigkeit:
        self.La_IstSpeed_text = QLabel(f'{istwert_str[self.sprache]}-{sv_str[self.sprache]} ')
        self.La_IstSpeed_wert = QLabel(st_v_str[self.sprache])
        self.La_IstSpeed_text.setStyleSheet(f"color: {self.color[1]}")
        self.La_IstSpeed_wert.setStyleSheet(f"color: {self.color[1]}")
        #### Sollposition:
        self.La_SollPos_text = QLabel(f'{self.pos_1_str[self.sprache]} {self.s_str[self.sprache]}')

        ### Knöpfe:
        #### Bewegungen:
        self.btn_left = QPushButton(QIcon(self.icon_1), '')
        self.btn_left.setFlat(True)
        self.btn_left.clicked.connect(self.fahre_links)

        self.btn_right = QPushButton(QIcon(self.icon_2), '')
        self.btn_right.setFlat(True)
        self.btn_right.clicked.connect(self.fahre_rechts)
        #### Stopp:
        icon_pfad = "./vifcon/icons/p_stopp.png" if sprache == 0 else  "./vifcon/icons/p_stopp_En.png" 
        self.btn_mitte = QPushButton(QIcon(icon_pfad), '')
        self.btn_mitte.setFlat(True)
        self.btn_mitte.clicked.connect(self.Stopp)
        #### Define-Home:
        self.btn_DH = QPushButton(DH_str[self.sprache])
        self.btn_DH.clicked.connect(self.define_home) 
        #### Rezepte:
        self.btn_rezept_start =  QPushButton(rez_start_str[self.sprache])
        self.btn_rezept_start.clicked.connect(lambda: self.RezStart(1))

        self.btn_rezept_ende =  QPushButton(rez_ende_str[self.sprache])
        self.btn_rezept_ende.clicked.connect(self.Stopp)   

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
        
        ### Radiobutton:
        self.RB_choise_relPos= QRadioButton(pos_rel_str[self.sprache])
        self.RB_choise_relPos.clicked.connect(self.relPos)
        self.RB_choise_relPos.setChecked(True)

        self.RB_choise_absPos = QRadioButton(pos_abs_str[self.sprache])
        self.RB_choise_absPos.clicked.connect(self.absPos)

        ### Gruppen Widgets:
        #### Radiobutton:
        self.btn_group_RB = QWidget()
        self.btn_RB_layout = QVBoxLayout()
        self.btn_group_RB.setLayout(self.btn_RB_layout)
        #self.btn_RB_layout.setSpacing(30)

        self.btn_RB_layout.addWidget(self.RB_choise_relPos)
        self.btn_RB_layout.addWidget(self.RB_choise_absPos)

        #### Bewegungsknöpfe:
        self.btn_group_move = QWidget()
        self.btn_move_layout = QHBoxLayout()
        self.btn_group_move.setLayout(self.btn_move_layout)
        self.btn_move_layout.setSpacing(20)

        self.btn_move_layout.addWidget(self.btn_left)
        self.btn_move_layout.addWidget(self.btn_mitte)
        self.btn_move_layout.addWidget(self.btn_right)
        self.btn_move_layout.addWidget(self.btn_group_RB)

        self.btn_move_layout.setContentsMargins(0,10,0,0)  # left, top, right, bottom

        #### Rezept und Define-Home:
        self.btn_group_Rezept = QWidget()
        self.btn_Rezept_layout = QVBoxLayout()
        self.btn_group_Rezept.setLayout(self.btn_Rezept_layout)
        self.btn_Rezept_layout.setSpacing(5)

        self.btn_Rezept_layout.addWidget(self.btn_DH)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_start)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_ende)
        self.btn_Rezept_layout.addWidget(self.cb_Rezept)

        self.btn_Rezept_layout.setContentsMargins(0,0,0,0)  # left, top, right, bottom

        #### First-Row:
        self.first_row_group  = QWidget()
        self.first_row_layout = QHBoxLayout()
        self.first_row_group.setLayout(self.first_row_layout)
        self.first_row_layout.setSpacing(20)

        self.first_row_layout.addWidget(self.La_name)
        self.first_row_layout.addWidget(self.Auswahl)
        self.first_row_layout.addWidget(self.gamepad)

        self.first_row_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom
        #________________________________________
        ## Platzierung der einzelnen Widgets im Layout:
        self.layer_layout.addWidget(self.first_row_group,                   0, 0, 1, 6, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(QLabel(v_str[self.sprache]),            1, 0)
        self.layer_layout.addWidget(self.La_SollPos_text,                   2, 0)      
        self.layer_layout.addWidget(self.btn_group_move,                    3, 0, 1, 4, alignment=Qt.AlignLeft)                     # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung                     
        self.layer_layout.addWidget(self.LE_Speed,                          1, 1)
        self.layer_layout.addWidget(self.LE_Pos,                            2, 1)      
        self.layer_layout.addWidget(self.La_error_1,                        1, 2,       alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_error_2,                        2, 2,       alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_IstSpeed_text,                  1, 3)
        self.layer_layout.addWidget(self.La_IstPos_text,                    2, 3)
        self.layer_layout.addWidget(self.La_IstSpeed_wert,                  1, 4,       alignment=Qt.AlignLeft)     
        self.layer_layout.addWidget(self.La_IstPos_wert,                    2, 4,       alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.btn_group_Rezept,                  1, 5, 4, 1, alignment=Qt.AlignTop)
        #________________________________________
        ## Größen (Size) - Widgets:
        ### Button-Icon:
        self.btn_left.setIconSize(QSize(50, 50))
        self.btn_right.setIconSize(QSize(50, 50))
        self.btn_mitte.setIconSize(QSize(50, 50))

        ### Eingabefelder (Line Edit):
        self.LE_Speed.setFixedWidth(100)
        self.LE_Speed.setFixedHeight(25)

        self.LE_Pos.setFixedWidth(100)
        self.LE_Pos.setFixedHeight(25)

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
        kurv_dict = {                                                               # Wert: [Achse, Farbe/Stift, Name]
            'IWs':  ['a1', pg.mkPen(self.color[0], width=2),                         f'{piAchse} - {s_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'IWv':  ['a2', pg.mkPen(self.color[1], width=2),                         f'{piAchse} - {v_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'oGs':  ['a1', pg.mkPen(color=self.color[0], style=Qt.DashLine),         f'{piAchse} - {s_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGs':  ['a1', pg.mkPen(color=self.color[0], style=Qt.DashDotDotLine),   f'{piAchse} - {s_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGv':  ['a2', pg.mkPen(color=self.color[1], style=Qt.DashLine),         f'{piAchse} - {v_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGv':  ['a2', pg.mkPen(color=self.color[1], style=Qt.DashDotDotLine),   f'{piAchse} - {v_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'Rezv': ['a2', pg.mkPen(color=self.color[2], width=3, style=Qt.DotLine), f'{piAchse} - {rezept_Label_str[self.sprache]}<sub>{v_einzel_str[self.sprache]}</sub>'],
        }

        ## Kurven erstellen:
        ist_drin_list = []                                                      # Jede Kurve kann nur einmal gesetzt werden!
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
        self.posList    = []       
        self.speedList  = []     
        ### Grenzen:
        self.VoGList    = []
        self.VuGList    = []
        self.SoGList    = []
        self.SuGList    = []

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.curveDict      = {'IWs': '', 'IWv': '', 'oGs': '', 'uGs': '', 'oGv': '', 'uGv': '', 'Rezv': ''}        # Kurven
        for kurve in self.kurven_dict:
            self.curveDict[kurve] = self.kurven_dict[kurve]
        self.labelDict      = {'IWs': self.La_IstPos_wert,  'IWv': self.La_IstSpeed_wert}                            # Label
        self.labelUnitDict  = {'IWs': 'mm',                 'IWv': 'mm/s'}                                           # Einheit
        self.listDict       = {'IWs': self.posList,         'IWv': self.speedList}                                   # Werteliste
        self.grenzListDict  = {'oGv': self.VoGList,         'uGv': self.VuGList,    'oGs': self.SoGList,    'uGs': self.SuGList}
        self.grenzValueDict = {'oGv': self.oGv,             'uGv': self.uGv,        'oGs': self.oGPos,      'uGs': self.uGPos}

        ## Plot-Skalierungsfaktoren:
        self.skalFak_dict = {}
        for size in self.curveDict:
            if 'Ws' in size:
                self.skalFak_dict.update({size: self.skalFak['Pos']})
            if 'Wv' in size:
                self.skalFak_dict.update({size: self.skalFak['Speed_1']})

        #---------------------------------------
        # Timer:
        #---------------------------------------
        ## Entrigelungstimer:
        self.timer_rigel = QTimer()                                                             
        self.timer_rigel.timeout.connect(self.entriegel_Knopf)

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
    def Fehler_Output(self, Fehler, La_error, error_Message_Log_GUI = '', error_Message_Ablauf = ''):
        ''' Erstelle Fehler-Nachricht für GUI, Ablaufdatei und Logging
        Args:
            Fehler (bool):                  False -> o.k. (schwarz), True -> Fehler (rot, bold)
            La_error (PyQt-Label):          Label das beschrieben werden soll (Objekt)
            error_Message_Log_GUI (str):    Nachricht die im Log und der GUI angezeigt wird
            error_Message_Ablauf (str):     Nachricht für die Ablaufdatei
        ''' 
        if Fehler:
            La_error.setText(self.err_0_str[self.sprache])
            La_error.setToolTip(error_Message_Log_GUI)  
            La_error.setStyleSheet(f"color: red; font-weight: bold")
            zusatz = f'({self.str_Size_1[self.sprache]})' if La_error == self.La_error_1 else (f'({self.str_Size_2[self.sprache]})' if La_error == self.La_error_2 else '')
            log_vorberietung = error_Message_Log_GUI.replace("\n"," ") 
            logger.error(f'{self.device_name} - {log_vorberietung} {zusatz}')
        else:
            La_error.setText(self.err_13_str[self.sprache])
            La_error.setToolTip('')
            La_error.setStyleSheet(f"color: black; font-weight: normal")
        if not error_Message_Ablauf == '':
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {error_Message_Ablauf}') 

    ##########################################
    # Reaktion auf Radio-Buttons:
    ##########################################
    def relPos(self):
        ''' Auswahl relative Position! '''
        # Passe an:
        self.btn_left.setIcon(QIcon(self.icon_1)) 
        self.btn_right.setIcon(QIcon(self.icon_2))                                             # Setze Icon, linker Knopf
        self.La_SollPos_text.setText(f'{self.pos_1_str[self.sprache]} {self.s_str[self.sprache]}')
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_31_str[self.sprache]}')
        
        if self.Achse_steht and self.mode != 0:
            self.btn_left.setEnabled(True)
            self.btn_right.setEnabled(True)

    def absPos(self):
        ''' Auswahl absolute Position! '''
        # Passe an:
        self.btn_left.setIcon(QIcon("./vifcon/icons/p_start.png"))
        self.btn_right.setIcon(QIcon("./vifcon/icons/p_nichts.png"))
        self.La_SollPos_text.setText(f'{self.pos_2_str[self.sprache]} {self.s_str[self.sprache]}')
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_32_str[self.sprache]}')

        if self.Achse_steht and self.mode != 0:
            self.btn_left.setEnabled(True)
            self.btn_right.setEnabled(False)

    ##########################################
    # Reaktion auf Buttons:
    ##########################################
    def fahre_links(self, gamepad = False):
        '''Reaktion auf den Linken Knopf
        Args:
            gamepad (bool):     Auslösung von Gamepad
        '''
        self.links_rechts(self.abLauf_Button_l[self.sprache], self.links, gamepad)

    def fahre_rechts(self, gamepad = False):
        '''Reaktion auf den Rechten Knopf
        Args:
            gamepad (bool):     Auslösung von Gamepad
        '''
        self.links_rechts(self.abLauf_Button_r[self.sprache], self.rechts, gamepad)
             
    def Stopp(self, n = 3):
        '''Halte Achse an'''
        if n == 5:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_90_str[self.sprache]}')
        self.RezEnde(n)

        if self.init:
            # Sende Befehl:
            self.write_task['Stopp'] = True
            #self.send_betätigt = True
            if n == 3:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_33_str[self.sprache]}')
            logger.debug(f"{self.device_name} - {self.Log_Text_49_str[self.sprache]}")

            # Entriegelung der Bewegungsknöpfe:
            self.Achse_steht = True
                
            # Timer start:
            if self.mode == 1:
                self.timer_rigel.stop()
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])
            self.Fehler_Output(1, self.La_error_2, self.err_4_str[self.sprache])

    def links_rechts(self, Knopf, Ausrichtung, gamepad):
        ''' Ausführung der beiden Bewegungsknöpfe!

        Args:
            Knopf (str):        Welcher Knopf wird verwendet (Ablaufdatei)
            Ausrichtung (str):  Vorzeichen
            gamepad (bool):     Auslösung von Gamepad
        ''' 

        if self.init:
            # Lese Einagbefelder aus und lasse den Wert kontrollieren:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {Knopf} {self.Text_34_str[self.sprache]}')
            pos, speed = self.controll_value(Ausrichtung)
            #self.send_betätigt = True
            
            # Alles in Ordnung mit Eingabe, dann setze Wert:
            if speed != '' and pos != '':
                # Achse darf sich bewegen:
                self.Achse_steht = False

                # Berechnung der Zeit:
                try:
                    time = pos/speed                                        # mm/(mm/s)
                except Exception as e:
                    logger.exception(f"{self.device_name} - {self.Log_Text_50_str[self.sprache]}")
                    time = 0.01 

                self.time_Riegel = abs(time)                                # Für Gamepad   
                self.timer_rigel.setInterval(abs(round(time*1000)))         # Timer in Millisekunden

                # Geschwindigkeit:
                self.write_task['Sende Speed'] = True
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_35_str[self.sprache]} {round(speed)} {self.Text_36_str[self.sprache]}')           
                speed = speed * self.cpm                                    # Umrechnung in counts/s
                self.write_value['Speed'] = speed
            
                # Position:
                self.write_task['Sende Position'] = True
                self.write_value['Position'] = pos
                logger.debug(f"{self.device_name} - {self.Log_Text_51_str[self.sprache]} {pos}!")
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_37_str[self.sprache]} {round(pos)} {self.Text_38_str[self.sprache]}')                        
                # Verriegeln der Bewegungsknöpfe:
                if self.mode != 0:
                    self.btn_left.setEnabled(False)
                    self.btn_right.setEnabled(False) 

                # Timer start:
                if self.mode == 1 and not gamepad:
                    self.timer_rigel.start()
                elif self.mode == 2:
                    self.losgefahren = True
            else:
                self.write_task['Sende Speed'] = False
                self.write_task['Sende Position'] = False
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])
            self.Fehler_Output(1, self.La_error_2, self.err_4_str[self.sprache])

    def define_home(self):
        ''' Sorgt dafür das die aktuelle Position zur Null wird.'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_39_str[self.sprache]}')
            self.write_task['Define Home'] = True

            with open(self.config_dat, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"{self.Log_Text_52_str[self.sprache]} {config}") 
            
            self.oGPos = config['devices'][self.device_name]["limits"]['maxPos']
            self.uGPos = config['devices'][self.device_name]["limits"]['minPos']
            self.oGv = config['devices'][self.device_name]["limits"]['maxSpeed']
            self.uGv = config['devices'][self.device_name]["limits"]['minSpeed']
        else:
            self.Fehler_Output(1, self.La_error_1, self.err_4_str[self.sprache])
            self.Fehler_Output(1, self.La_error_2, self.err_4_str[self.sprache])

    ##########################################
    # Eingabefeld Kontrolle:
    ##########################################
    def controll_value(self,  sign = 'Plus'):
        ''' Kontrolliere die Eingabe eines Eingabefeldes.

        Args:
            sign (str):     Vorzeichen der Bewegung
        
        Return:
            '' (str):               Fehlerfall
            pos_value (float):      Positionswert
            speed_value (float):    Geschwindigkeitswert
        '''
        pos_value = self.LE_Pos.text().replace(",", ".")
        speed_value = self.LE_Speed.text().replace(",", ".")

        pos_okay = False
        speed_okay = False

        # Wenn eins der beiden Eingabefelder leer ist, dann sende nicht:
        if pos_value == '' or speed_value == '':
            self.Fehler_Output(1, self.La_error_1, self.err_1_str[self.sprache])
            self.Fehler_Output(1, self.La_error_2, self.err_1_str[self.sprache], self.Text_40_str[self.sprache])      
        else:  
            # Kontrolle Position:                                                                                                 
            try:
                # Umwandeln Position:
                pos_value = float(pos_value)
                # Bei Relativer Bewegung muss der Wert Positiv sein:
                if self.RB_choise_relPos.isChecked():                                           
                    if pos_value < 0:      
                        self.Fehler_Output(1, self.La_error_2, self.err_8_str[self.sprache], self.Text_41_str[self.sprache])                                                                                 
                        return '', ''
                    else:
                        if sign == 'Minus':                                                                     # Kontrolliere Bewegungsrichtung
                            pos_value = pos_value * -1
                        newPos = pos_value + self.akPos                                                         # Berechnung der neuen Position zur aktuellen Position
                # Bei Absoluter Bewegung:
                elif self.RB_choise_absPos.isChecked():                      
                    newPos = pos_value
                # Kontrolliere die Grenzen/Limits:
                if newPos < self.uGPos or newPos > self.oGPos:   
                    self.Fehler_Output(1, self.La_error_2, f'{self.err_2_str[self.sprache]} {self.uGPos} {self.err_3_str[self.sprache]} {self.oGPos}', self.Text_42_str[self.sprache])                                                               
                # Alles in Ordnung mit der Eingabe:
                else:       
                    self.Fehler_Output(0, self.La_error_2)                                                                                   
                    # Berechne Fahrweg für die Absolute Bewegung:
                    if self.RB_choise_absPos.isChecked():                                        
                        pos_value = pos_value - self.akPos   
                    pos_okay = True                                                           
                    #return pos_value
            # Eingabe ist falsch:
            except Exception as e:
                self.Fehler_Output(1, self.La_error_2, self.err_5_str[self.sprache], self.Text_43_str[self.sprache])    
                logger.exception(f"{self.device_name} - {self.Log_Text_53_str[self.sprache]}")                                                                                                       
            # Kontrolle Geschwindigkeit:
            try:
                # Umwandeln Geschwindigkeit:
                speed_value = float(speed_value)
                if speed_value < self.uGv or speed_value > self.oGv:  
                    self.Fehler_Output(1, self.La_error_1, f'{self.err_2_str[self.sprache]} {self.uGv} {self.err_3_str[self.sprache]} {self.oGv}', self.Text_42_str[self.sprache])                                                                  
                else:
                    self.Fehler_Output(0, self.La_error_1)
                    speed_okay = True
            # Eingabe ist falsch:
            except Exception as e:
                self.Fehler_Output(1, self.La_error_1, self.err_5_str[self.sprache], self.Text_43_str[self.sprache])
                logger.exception(f"{self.device_name} - {self.Log_Text_54_str[self.sprache]}")                                                                                                            
        # Alles Okay:
        if speed_okay and pos_okay:
            return pos_value, speed_value
        # Rückgabe bei Fehler:
        return '', ''      

    ##########################################
    # Betrachtung der Labels und Plots:
    ##########################################
    def update_GUI(self, value_dict, x_value):
        ''' Update der GUI, Plot und Label!

        Args:
            value_dict (dict):  Dictionary mit den aktuellen Werten!
            x_value (list):     Werte für die x-Achse
        '''

        self.data.update({'Time' : x_value[-1]})   
        self.data.update(value_dict)   

        for messung in value_dict:
            self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}')
            self.listDict[messung].append(value_dict[messung])
            if not self.curveDict[messung] == '':
                faktor = self.skalFak_dict[messung]
                y = [a * faktor for a in self.listDict[messung]]
                self.curveDict[messung].setData(x_value, y)   

        # Grenz-Kurven:
        ## Update Grenzwert-Dictionary:
        self.grenzValueDict['oGv']  = self.oGv      * self.skalFak['Speed_1']
        self.grenzValueDict['uGv']  = self.oGv*(-1) * self.skalFak['Speed_1']
        self.grenzValueDict['oGs']  = self.oGPos    * self.skalFak['Pos']
        self.grenzValueDict['uGs']  = self.uGPos    * self.skalFak['Pos']
        ## Update-Kurven:
        for kurve in self.kurven_dict:
            if kurve in self.grenzListDict:
                self.grenzListDict[kurve].append(float(self.grenzValueDict[kurve]))
                self.kurven_dict[kurve].setData(x_value, self.grenzListDict[kurve]) 

    ##########################################
    # Reaktion auf Verriegelungsmodus:
    ##########################################
    def entriegel_Knopf(self, gamepad = False):
        ''' An Timer geknüpfte Funktion. Gibt die Knöpfe wieder frei nach Ablauf der Bewegung! 
        Args:
            gamepad (bool):     Auslösung von Gamepad
        '''
        self.btn_left.setEnabled(True)
        if not self.RB_choise_absPos.isChecked():
            self.btn_right.setEnabled(True) 
        if not gamepad:
            self.timer_rigel.stop()
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_44_str[self.sprache]}')         
        self.Achse_steht = True

    def check_verriegelung(self, speed):
        ''' An Modus 2 verknüpfte Funktion, Entriegelung bei Stillstand '''
        if speed == 0:
            self.Achse_steht = True
            self.losgefahren = False
            self.btn_left.setEnabled(True)
            if not self.RB_choise_absPos.isChecked():
                self.btn_right.setEnabled(True) 

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
            self.Fehler_Output(0, self.La_error_2)
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
        
        self.oGPos  = config['devices'][self.device_name]["limits"]['maxPos']
        self.uGPos  = config['devices'][self.device_name]["limits"]['minPos']
        self.oGv    = config['devices'][self.device_name]["limits"]['maxSpeed']
        self.uGv    = config['devices'][self.device_name]["limits"]['minSpeed']

    ##########################################
    # Reaktion auf Rezepte:
    ##########################################
    def RezStart(self, execute = 1):
        ''' Rezept wurde gestartet '''
        if self.init:
            if not self.Rezept_Aktiv:
                if execute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_87_str[self.sprache]}')
                elif execute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_85_str[self.sprache]}')
            
                # Variablen:                                                                     # Kontrolle ob alles mit Rezept stimmt
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

                    # Erste Elemente senden :
                    self.write_value['Speed'] = abs(self.value_list[self.step]) * self.cpm
                    self.write_value['Position'] = self.value_list[self.step] * self.time_list[self.step]

                    self.write_task['Sende Position'] = True
                    self.write_task['Sende Speed'] = True

                    # Elemente GUI sperren:
                    self.cb_Rezept.setEnabled(False)
                    self.btn_rezept_start.setEnabled(False)
                    self.btn_left.setEnabled(False)
                    self.btn_mitte.setEnabled(False)
                    self.btn_right.setEnabled(False)
                    self.btn_DH.setEnabled(False)
                    self.RB_choise_relPos.setEnabled(False)
                    self.RB_choise_absPos.setEnabled(False)
                    self.Auswahl.setEnabled(False)

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
            self.Fehler_Output(1, self.La_error_2, self.err_4_str[self.sprache])

    def RezEnde(self, excecute):
        ''' Rezept wurde/wird beendet '''
        if self.init:
            if self.Rezept_Aktiv == True:
                if excecute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_81_str[self.sprache]}')
                elif excecute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_82_str[self.sprache]}')
                elif excecute == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_83_str[self.sprache]}')
                elif excecute == 4: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_86_str[self.sprache]}')
                elif excecute == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_90_str[self.sprache]}')

                # Elemente GUI entsperren:
                self.cb_Rezept.setEnabled(True)
                self.btn_rezept_start.setEnabled(True)
                self.btn_left.setEnabled(True)
                self.btn_mitte.setEnabled(True)
                if not self.RB_choise_absPos.isChecked():
                    self.btn_right.setEnabled(True) 
                self.btn_DH.setEnabled(True)
                self.RB_choise_relPos.setEnabled(True)
                self.RB_choise_absPos.setEnabled(True)
                self.Auswahl.setEnabled(True)

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
            self.Fehler_Output(1, self.La_error_2, self.err_4_str[self.sprache])
        
    def Rezept(self):
        ''' Rezept Schritt wurde beendet, Vorbereitung und Start des neuen '''
        self.step += 1
        if self.step > len(self.time_list) - 1:
            self.Stopp(2)
        else:
            self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))

            # Nächstes Element senden:
            self.write_value['Speed']       = abs(self.value_list[self.step]) * self.cpm
            self.write_value['Position']    = self.value_list[self.step] * self.time_list[self.step]

            self.write_task['Sende Position'] = True
            self.write_task['Sende Speed'] = True
    
    def Rezept_lesen_controll(self):
        ''' Rezept wird ausgelesen und kontrolliert. Bei Fehler werden die Fehlermeldungen beschrieben auf der GUI. 
        
        Return:
            error (Bool):   Fehler vorhanden oder nicht
        '''
        # Variablen:
        error = False 
        self.time_list  = []
        self.value_list = []
        
        ## Geschwindigkeitlimits:
        uG = self.oGv * (-1)
        oG = self.oGv

        ## Positionlimits:
        uGPos = self.uGPos
        oGPos = self.oGPos

        ## Aktuelle Wert Geschwindigkeit:
        ak_value = self.ak_value['IWv'] if not self.ak_value == {} else 0

        # Rezept lesen:
        rezept = self.cb_Rezept.currentText() 
        pos_list = [] 
        start_pos = self.akPos

        if not rezept == '------------':
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
                ### Sprung:
                else:                                               
                    self.value_list.append(value)
                    self.time_list.append(time)
            
            ## Positionen bestimmen:
            value_step = 0
            for n_PosP in self.value_list:
                pos_list.append(n_PosP * self.time_list[value_step])
                value_step += 1
            
            ## Kontrolle Position/Weg:
            logger.debug(f"{self.device_name} - {self.Log_Text_55_str[self.sprache]} {pos_list}")
            rezept_schritt = 1 
            for n in pos_list:
                pos = start_pos + n
                start_pos = pos
                if pos < uGPos or pos > oGPos:
                    error = True
                    self.Fehler_Output(1, self.La_error_2, f'{self.err_9_str[self.sprache]} {rezept_schritt} {self.err_7_str[self.sprache]} {uGPos} {self.err_3_str[self.sprache]} {oGPos}!')    
                    break
                else:
                    self.Fehler_Output(0, self.La_error_2)  
                rezept_schritt += 1 
        else:
            self.Fehler_Output(0, self.La_error_1)
            self.Fehler_Output(0, self.La_error_2)
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
        try: self.curveDict['Rezv'].setData(self.RezTimeList, self.RezValueList)
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
            faktor = self.skalFak['Speed_1']
            y = [a * faktor for a in self.RezValueList]
            
            # Kurve Anzeigen:
            if anzeigev:
                self.curveDict['Rezv'].setData(self.RezTimeList, y)
                self.typ_widget.plot.achse_2.autoRange()                            # Rezept Achse 2 wird nicht fertig angezeigt, aus dem Grund wird dies durchgeführt! Beim Enden wird die AutoRange Funktion von base_classes.py durchgeführt. Bewegung des Plots sind mit der Lösung nicht machbar!!
                                                                                    # Plot wird nur an Achse 1 (links) angepasst!

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