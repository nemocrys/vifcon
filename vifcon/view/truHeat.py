# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
TruHeat Generator Widget:
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
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,

)
from PyQt5.QtGui import (
    QIcon, 

)
from PyQt5.QtCore import (
    Qt,
    QTimer,
    QSize,

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


class TruHeatWidget(QWidget):
    def __init__(self, sprache, Frame_Anzeige, widget, line_color, config, config_dat, neustart, add_Ablauf_function, truheat = 'TruHeat', typ = 'Generator', parent=None):
        """GUI widget of TruHeat generator.

        Args:
            sprache (int):                      Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):           Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (Objekt):                    Element in das, das Widget eingefügt wird
            line_color (list):                  Liste mit Farben
            config (dict):                      Konfigurationsdaten aus der YAML-Datei
            config_dat (string):                Datei-Name der Config-Datei
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            truheat (str):                      Name des Gerätes
            typ (str):                          Typ des Gerätes
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
        self.device_name                = truheat
        self.typ                        = typ

        ## Aus Config:
        ### Zum Start:
        self.init   = self.config['start']['init']
        self.stMode = self.config['start']['start_modus']
        ### Limits:
        ### Sollleistung:
        self.oGP = self.config["limits"]['maxP']        
        self.uGP = self.config["limits"]['minP']
        ### Sollstrom:
        self.oGI = self.config["limits"]['maxI']        
        self.uGI = self.config["limits"]['minI']
        ### Sollspannung:
        self.oGU = self.config["limits"]['maxU']        
        self.uGU = self.config["limits"]['minU']
        ### GUI:
        self.legenden_inhalt = self.config['GUI']['legend'].split(';')
        self.legenden_inhalt = [a.strip() for a in self.legenden_inhalt]    # sollten Unnötige Leerzeichen vorhanden sein, so werden diese entfernt!
        ### Rezepte:
        self.rezept_config = self.config["rezepte"]

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
        sollwert_str            = ['Soll',                                                                                                      'Set']
        istwert_str             = ['Ist',                                                                                                       'Is']
        ## Knöpfe:                                                              
        send_str                = ['Sende',                                                                                                     'Send']
        rez_start_str           = ['Rezept Start',                                                                                              'Start recipe']
        rez_ende_str            = ['Rezept Beenden',                                                                                            'Finish recipe']
        ## Checkbox:    
        cb_sync_str             = ['Sync',                                                                                                      'Sync']
        ## Einheiten mit Größe: 
        P_str                   = ['P in kW:',                                                                                                  'P in kW:']
        U_str                   = ['U in V:',                                                                                                   'U in V:']
        I_str                   = ['I in A:',                                                                                                   'I in A:']
        sP_str                  = ['P:',                                                                                                        'P:']
        sU_str                  = ['U:',                                                                                                        'U:']
        sI_str                  = ['I:',                                                                                                        'I:']
        sf_str                  = ['f:',                                                                                                        'f:']
        st_P_str                = ['XXX.XX kW',                                                                                                 'XXX.XX kW']
        st_U_str                = ['XXX.XX V',                                                                                                  'XXX.XX V']
        st_I_str                = ['XXX.XX A',                                                                                                  'XXX.XX A']
        st_f_str                = ['XXX.XX kHz',                                                                                                'XXX.XX kHz']
        I_einzel_str            = ['I',                                                                                                         'I']
        U_einzel_str            = ['U',                                                                                                         'U']
        f_einzel_str            = ['f',                                                                                                         'f']
        P_einzel_str            = ['P',                                                                                                         'P']
        ## Fehlermeldungen:   
        self.err_0_str          = ['Fehler!',                                                                                                   'Error!']                  
        self.err_1_str          = ['Keine Eingabe!',                                                                                            'No input!']
        self.err_2_str          = ['Grenzen überschritten!\nGrenzen von',                                                                       'Limits exceeded!\nLimits from']
        self.err_3_str          = ['bis',                                                                                                       'to']
        self.err_4_str          = ['Gerät anschließen und\nInitialisieren!',                                                                    'Connect the device\nand initialize!']
        self.err_5_str          = ['Fehlerhafte Eingabe!',                                                                                      'Incorrect input!']
        self.err_6_str          = ['Der Wert',                                                                                                  'The value']
        self.err_7_str          = ['überschreitet\ndie Grenzen von',                                                                            'exceeds\nthe limits of']
        self.err_10_str         = ['Rezept Einlesefehler!',                                                                                     'Recipe import error!']
        self.err_12_str         = ['Erster Schritt = Sprung!\nDa keine Messwerte!',                                                             'First step = jump! There\nare no measurements!']
        self.err_13_str         = ['o.K.',                                                                                                      'o.K.']   
        self.err_14_str         = ['Rezept läuft!\nRezept Einlesen gesperrt!',                                                                  'Recipe is running!\nReading recipes blocked!']
        self.err_15_str         = ['Wähle ein Rezept!',                                                                                         'Choose a recipe!']
        self.err_16_str         = ['Rezept läuft!\nRezept Start gesperrt!',                                                                     'Recipe running!\nRecipe start blocked!']
        ## Plot-Legende:                                                
        rezept_Label_str        = ['Rezept',                                                                                                    'Recipe']
        ober_Grenze_str         = ['oG',                                                                                                        'uL']                                   # uL - upper Limit
        unter_Grenze_str        = ['uG',                                                                                                        'lL']                                   # lL - lower Limit
        ## Logging:
        self.Log_Text_1_str 	= ['Erstelle Widget.',                                                                                          'Create widget.']
        self.Log_Text_28_str    = ['Gerät wurde Gestartet/Initialisiert!',                                                                      'Device has been started/initialized!']
        self.Log_Text_29_str    = ['Gerät wurde nicht Initialisiert! Initialisierung durch Menü im späteren!',                                  'Device was not initialized! Initialization through menu later!']
        self.Log_Text_30_str    = ['Neustart Modus.',                                                                                           'Restart mode.']
        self.Log_Text_31_str    = ['Der RS232-User Watchdog, sollte auf NULL gesetzt werden, da keine regelmäßigen Lese-Befehle kommen!',       'The RS232 user watchdog should be set to ZERO because there are no regular read commands!']
        self.Log_Text_32_str    = ['Störungen verhindern einschalten des Generators!',                                                          'Prevent interference when switching on the generator!']
        self.Log_Text_33_str    = ['Bei nicht angeschlossenen Gerät --> Fehlermeldungen da Lese-Befehle senden eingeschaltet!',                 'If the device is not connected --> error messages because sending read commands is switched on!']
        self.Log_Text_34_str    = ['Startmodus Leistung!',                                                                                      'Start mode power!']
        self.Log_Text_35_str    = ['Startmodus Spannung!',                                                                                      'Start mode voltage!']
        self.Log_Text_36_str    = ['Startmodus Strom!',                                                                                         'Start mode current!']
        self.Log_Text_37_str    = ['Startmodus Unbekannt!',                                                                                     'Start mode Unknown!']
        self.Log_Text_38_str    = ['Fehlerhafte Eingabe - Grund:',                                                                              'Incorrect input - Reason:']
        self.Log_Text_39_str    = ['Rezept:',                                                                                                   'Recipe:']
        self.Log_Text_40_str    = ['Rezept Inhalt:',                                                                                            'Recipe content:']
        self.Log_Text_205_str   = ['Update Konfiguration (Update Limits):',                                                                     'Update configuration (update limits):']
        ## Ablaufdatei:
        self.Text_13_str        = ['Auswahl Leistung senden.',                                                                                  'Send power selection.']
        self.Text_14_str        = ['Auswahl Spannung senden.',                                                                                  'Send voltage selection.']
        self.Text_15_str        = ['Auswahl Strom senden.',                                                                                     'Send current selection.']
        self.Text_16_str        = ['Knopf betätigt - Sende Sollleistung!',                                                                      'Button pressed - send target power!']
        self.Text_17_str        = ['Knopf betätigt - Sende Sollspannung!',                                                                      'Button pressed - send target voltage!']
        self.Text_18_str        = ['Knopf betätigt - Sende Sollstrom!',                                                                         'Button pressed - send target current!']
        self.Text_19_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da keine Eingabe.',                                       'Input field error message: Sending failed because there was no input.']
        self.Text_20_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da Eingabe die Grenzen überschreitet.',                   'Input field error message: Send failed because input exceeds limits.']
        self.Text_21_str        = ['Sende den Wert',                                                                                            'Send the value']
        self.Text_22_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da fehlerhafte Eingabe.',                                 'Input field error message: Sending failed due to incorrect input.']
        self.Text_23_str        = ['Knopf betätigt - Initialisierung!',                                                                         'Button pressed - initialization!']
        self.Text_24_str        = ['Ausführung des Rezeptes:',                                                                                  'Execution of the recipe:']
        self.Text_81_str        = ['Knopf betätigt - Beende Rezept',                                                                            'Button pressed - End recipe']
        self.Text_82_str        = ['Rezept ist zu Ende!',                                                                                       'Recipe is finished!']
        self.Text_83_str        = ['Stopp betätigt - Beende Rezept',                                                                            'Stop pressed - End recipe']
        self.Text_84_str        = ['Rezept läuft! Erneuter Start verhindert!',                                                                  'Recipe is running! Restart prevented!']
        self.Text_85_str        = ['Rezept Startet',                                                                                            'Recipe Starts']
        self.Text_86_str        = ['Rezept Beenden',                                                                                            'Recipe Ends']
        self.Text_87_str        = ['Knopf betätigt - Start Rezept',                                                                             'Button pressed - Start recipe']
        self.Text_88_str        = ['Rezept konnte aufgrund von Fehler nicht gestartet werden!',                                                 'Recipe could not be started due to an error!']
        self.Text_89_str        = ['Knopf betätigt - Beende Rezept - Keine Wirkung, da kein aktives Rezept!',                                   'Button pressed - End recipe - No effect because there is no active recipe!']
        self.Text_90_str        = ['Sicherer Endzustand wird hergestellt! Auslösung des Stopp-Knopfes!',                                        'Safe final state is established! Stop button is activated!']
        self.Text_91_str        = ['Rezept Beenden - Sicherer Endzustand',                                                                      'Recipe Ends - Safe End State']
        ## Print:   
        self.ExPrint_str        = ['ACHTUNG: Keine regelmäßigen Lese-Befehle - RS232-User watchdog deaktivieren (auf Null stellen)!',           'ATTENTION: No regular read commands - deactivate RS232 user watchdog (set to zero)!']
        ## Message-Box:
        self.Message_1          = ['Der Watchdog sollte auf Null gesetzt (Deaktiviert) werden, da die Lese-Befehle ausgestellt worden sind.',  
                                   'The watchdog should be set to zero (disabled) since the read commands have been issued.']

        #---------------------------------------
        # Konfigurationen für das Senden:
        #---------------------------------------
        #self.send_betätigt = True
        self.write_task = {'Soll-Leistung': False, 'Soll-Strom': False, 'Soll-Spannung': False, 'Init':False, 'Ein': False, 'Aus': False, 'Start':False}
        self.write_value = {'Sollwert': 0}

        if self.init and not self.neustart:
            self.write_task['Start'] = True

        #---------------------------------------
        # Nachrichten im Log-File:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_28_str[self.sprache]}") if self.init else logger.warning(f"{self.device_name} - {self.Log_Text_29_str[self.sprache]}")
        if self.neustart: logger.info(f"{self.device_name} - {self.Log_Text_30_str[self.sprache]}") 
        if self.config['start']["readTime"] == 0:  
            logger.warning(f"{self.device_name} - {self.Log_Text_31_str[self.sprache]}")  
            logger.warning(f"{self.device_name} - {self.Log_Text_32_str[self.sprache]}")  
            self.typ_widget.Message(self.Message_1[self.sprache], 3, 500)         # Aufruf einer Message-Box, Warnung
            print(self.ExPrint_str[self.sprache])
        if not self.init and not self.config['start']["readTime"] == 0: logger.warning(f"{self.device_name} - {self.Log_Text_33_str[self.sprache]}")
        logger.info(f"{self.device_name} - {self.Log_Text_34_str[self.sprache]}") if self.stMode == 'P' else (logger.info(f"{self.device_name} - {self.Log_Text_35_str[self.sprache]}") if self.stMode == 'U' else (logger.info(f"{self.device_name} - {self.Log_Text_36_str[self.sprache]}") if self.stMode == 'I' else logger.info(f"{self.device_name} - {self.Log_Text_37_str[self.sprache]}")))        

        #---------------------------------------    
        # GUI:
        #---------------------------------------
        ## Grundgerüst:
        self.layer_widget = QWidget()
        self.layer_layout = QGridLayout()
        self.layer_widget.setLayout(self.layer_layout)
        self.typ_widget.splitter_main.splitter.addWidget(self.layer_widget)
        logger.info(f"{self.device_name} - {self.Log_Text_1_str[self.sprache]}")
        
        ## Kompakteres Darstellen:
        ### Grid Size - bei Verschieben der Splitter zusammenhängend darstellen:
        self.layer_layout.setRowStretch(7, 1) 
        self.layer_layout.setColumnStretch(6, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)       
        self.layer_layout.setVerticalSpacing(5)

        ### Zeilenhöhen:
        self.layer_layout.setRowMinimumHeight(4, 40)    # Error-Nachricht

        ### Spaltenbreiten:
        self.layer_layout.setColumnMinimumWidth(0, 100)
        self.layer_layout.setColumnMinimumWidth(1, 105)
        self.layer_layout.setColumnMinimumWidth(3, 120)

        ## Eingabefelder:
        self.LE_Pow = QLineEdit()
        self.LE_Pow.setText(str(self.config["defaults"]['startPow']))

        self.LE_Voltage = QLineEdit()
        self.LE_Voltage.setText(str(self.config["defaults"]['startVoltage']))

        self.LE_Current = QLineEdit()
        self.LE_Current.setText(str(self.config["defaults"]['startCurrent']))

        ## Checkbox:
        self.Auswahl = QCheckBox(cb_sync_str[self.sprache])

        ## Radiobutton:
        self.RB_choise_Pow = QRadioButton(f'{sollwert_str[self.sprache]}-{P_str[self.sprache]} ')
        self.RB_choise_Pow.setStyleSheet(f"color: {self.color[0]}")
        self.RB_choise_Pow.clicked.connect(self.BlassOutUI)

        self.RB_choise_Voltage = QRadioButton(f'{sollwert_str[self.sprache]}-{U_str[self.sprache]} ')
        self.RB_choise_Voltage.setStyleSheet(f"color: {self.color[1]}")
        self.RB_choise_Voltage.clicked.connect(self.BlassOutPI)

        self.RB_choise_Current = QRadioButton(f'{sollwert_str[self.sprache]}-{I_str[self.sprache]} ')
        self.RB_choise_Current.setStyleSheet(f"color: {self.color[2]}")
        self.RB_choise_Current.clicked.connect(self.BlassOutPU)

        ## Start-Modus:
        if self.init:       # and not self.neustart
            self.Start()

        ## Label:
        self.La_name = QLabel(f'<b>{truheat}</b>')

        self.La_IstPow_text = QLabel(f'{istwert_str[self.sprache]}-{sP_str[self.sprache]} ')
        self.La_IstPow_wert = QLabel(st_P_str[self.sprache])
        self.La_IstPow_text.setStyleSheet(f"color: {self.color[3]}")
        self.La_IstPow_wert.setStyleSheet(f"color: {self.color[3]}")

        self.La_IstVoltage_text = QLabel(f'{istwert_str[self.sprache]}-{sU_str[self.sprache]} ')
        self.La_IstVoltage_wert = QLabel(st_U_str[self.sprache])
        self.La_IstVoltage_text.setStyleSheet(f"color: {self.color[4]}")
        self.La_IstVoltage_wert.setStyleSheet(f"color: {self.color[4]}")

        self.La_IstCurrent_text = QLabel(f'{istwert_str[self.sprache]}-{sI_str[self.sprache]} ')
        self.La_IstCurrent_wert = QLabel(st_I_str[self.sprache])
        self.La_IstCurrent_text.setStyleSheet(f"color: {self.color[5]}")
        self.La_IstCurrent_wert.setStyleSheet(f"color: {self.color[5]}")

        self.La_IstFre_text = QLabel(f'{istwert_str[self.sprache]}-{sf_str[self.sprache]} ')
        self.La_IstFre_wert = QLabel(st_f_str[self.sprache])
        self.La_IstFre_text.setStyleSheet(f"color: {self.color[6]}")
        self.La_IstFre_wert.setStyleSheet(f"color: {self.color[6]}")

        self.La_error = QLabel(self.err_13_str[self.sprache])

        ## Knöpfe:
        self.btn_send_value = QPushButton(send_str[self.sprache])
        self.btn_send_value.clicked.connect(self.send) 

        self.btn_rezept_start =  QPushButton(rez_start_str[self.sprache])
        self.btn_rezept_start.clicked.connect(lambda: self.RezStart(1))

        self.btn_rezept_ende =  QPushButton(rez_ende_str[self.sprache])
        self.btn_rezept_ende.clicked.connect(self.RezEnde)   

        self.btn_Ein = QPushButton(QIcon("./vifcon/icons/p_TH_Ein.png"), '')
        self.btn_Ein.setFlat(True)
        self.btn_Ein.clicked.connect(self.THEin)   

        self.btn_Aus = QPushButton(QIcon("./vifcon/icons/p_TH_Aus.png"), '')
        self.btn_Aus.setFlat(True)
        self.btn_Aus.clicked.connect(self.THAus)   

        ## Combobox:
        self.cb_Rezept = QComboBox()
        self.cb_Rezept.addItem('------------')
        for rezept in self.rezept_config:
            self.cb_Rezept.addItem(rezept)    
        self.cb_Rezept.setStyleSheet('''* 
                                    QComboBox QAbstractItemView 
                                        {
                                        min-width:200px;
                                        }
                                    ''')    # https://stackoverflow.com/questions/37632845/qcombobox-adjust-drop-down-width

        ## Gruppen Widgets:
        ### Knöpfe:
        self.btn_group = QWidget()
        self.btn_group_layout = QVBoxLayout()
        self.btn_group.setLayout(self.btn_group_layout)
        self.btn_group_layout.setSpacing(0)

        self.btn_group_layout.addWidget(self.btn_Ein)
        self.btn_group_layout.addWidget(self.btn_Aus)

        self.btn_group_layout.setContentsMargins(15,0,5,0)       # left, top, right, bottom

        ### Rezept:
        self.btn_group_Rezept = QWidget()
        self.btn_Rezept_layout = QVBoxLayout()
        self.btn_group_Rezept.setLayout(self.btn_Rezept_layout)
        self.btn_Rezept_layout.setSpacing(5)

        self.btn_Rezept_layout.addWidget(self.btn_rezept_start)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_ende)
        self.btn_Rezept_layout.addWidget(self.cb_Rezept)

        self.btn_Rezept_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom

        ### First-Row:
        self.first_row_group  = QWidget()
        self.first_row_layout = QHBoxLayout()
        self.first_row_group.setLayout(self.first_row_layout)
        self.first_row_layout.setSpacing(20)

        self.first_row_layout.addWidget(self.La_name)
        self.first_row_layout.addWidget(self.Auswahl)

        self.first_row_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom

        ## Platzierung der einzelnen Widgets im Layout:
        self.layer_layout.addWidget(self.first_row_group,       0, 0, 1, 5, alignment=Qt.AlignLeft)  # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung
        self.layer_layout.addWidget(self.RB_choise_Pow,         1, 0)                         
        self.layer_layout.addWidget(self.RB_choise_Voltage,     2, 0)
        self.layer_layout.addWidget(self.RB_choise_Current,     3, 0)
        self.layer_layout.addWidget(self.btn_send_value,        4, 0) 
        self.layer_layout.addWidget(self.LE_Pow,                1, 1)
        self.layer_layout.addWidget(self.LE_Voltage,            2, 1)
        self.layer_layout.addWidget(self.LE_Current,            3, 1)
        self.layer_layout.addWidget(self.La_error,              4, 1) 
        self.layer_layout.addWidget(self.La_IstPow_text,        1, 2)
        self.layer_layout.addWidget(self.La_IstVoltage_text,    2, 2)
        self.layer_layout.addWidget(self.La_IstCurrent_text,    3, 2)
        self.layer_layout.addWidget(self.La_IstFre_text,        4, 2)
        self.layer_layout.addWidget(self.La_IstPow_wert,        1, 3, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_IstVoltage_wert,    2, 3, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_IstCurrent_wert,    3, 3, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_IstFre_wert,        4, 3, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.btn_group_Rezept,      1, 4, 3, 1, alignment=Qt.AlignTop)
        self.layer_layout.addWidget(self.btn_group,             1, 5, 4, 1, alignment=Qt.AlignTop)

        ## Größen (Size) - Widgets:
        ### Button-Icon:
        self.btn_Aus.setIconSize(QSize(50, 50))
        self.btn_Ein.setIconSize(QSize(50, 50))

        ### Eingabefelder (Line Edit):
        self.LE_Pow.setFixedWidth(100)
        self.LE_Pow.setFixedHeight(25)

        self.LE_Voltage.setFixedWidth(100)
        self.LE_Voltage.setFixedHeight(25)

        self.LE_Current.setFixedWidth(100)
        self.LE_Current.setFixedHeight(25)

        ### Rezpt-Funktionen:
        self.btn_rezept_start.setFixedWidth(100)
        self.btn_rezept_ende.setFixedWidth(100)
        self.cb_Rezept.setFixedWidth(100)

        ## Border Sichtbar:
        if Frame_Anzeige:
            self.layer_widget.setStyleSheet("border: 1px solid black;")

        #---------------------------------------
        # Kurven:
        #---------------------------------------
        kurv_dict = {                                                                   # Wert: [Achse, Farbe/Stift, Name]
            'IWI':  ['a1', pg.mkPen(self.color[5], width=2),                            f'{truheat} - {I_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWI':  ['a1', pg.mkPen(self.color[2]),                                     f'{truheat} - {I_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            'IWU':  ['a1', pg.mkPen(self.color[4], width=2),                            f'{truheat} - {U_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWU':  ['a1', pg.mkPen(self.color[1]),                                     f'{truheat} - {U_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            'IWP':  ['a2', pg.mkPen(self.color[3], width=2),                            f'{truheat} - {P_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWP':  ['a2', pg.mkPen(self.color[0]),                                     f'{truheat} - {P_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            'IWf':  ['a2', pg.mkPen(self.color[6], width=2),                            f'{truheat} - {f_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'oGI':  ['a1', pg.mkPen(color=self.color[5], style=Qt.DashLine),            f'{truheat} - {I_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGI':  ['a1', pg.mkPen(color=self.color[5], style=Qt.DashDotDotLine),      f'{truheat} - {I_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGU':  ['a1', pg.mkPen(color=self.color[4], style=Qt.DashLine),            f'{truheat} - {U_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGU':  ['a1', pg.mkPen(color=self.color[4], style=Qt.DashDotDotLine),      f'{truheat} - {U_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGP':  ['a2', pg.mkPen(color=self.color[3], style=Qt.DashLine),            f'{truheat} - {P_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGP':  ['a2', pg.mkPen(color=self.color[3], style=Qt.DashDotDotLine),      f'{truheat} - {P_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'RezI': ['a1', pg.mkPen(color=self.color[9], width=3, style=Qt.DotLine),    f'{truheat} - {rezept_Label_str[self.sprache]}<sub>{I_einzel_str[self.sprache]}</sub>'],
            'RezU': ['a1', pg.mkPen(color=self.color[8], width=3, style=Qt.DotLine),    f'{truheat} - {rezept_Label_str[self.sprache]}<sub>{U_einzel_str[self.sprache]}</sub>'],
            'RezP': ['a2', pg.mkPen(color=self.color[7], width=3, style=Qt.DotLine),    f'{truheat} - {rezept_Label_str[self.sprache]}<sub>{P_einzel_str[self.sprache]}</sub>']
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
        # Notiz: Frequenzgrenzen auch?
                
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
        self.IWIList     = []
        self.IWUList     = []
        self.IWPList     = []
        self.IWfList     = []

        self.SWIList     = []
        self.SWUList     = []
        self.SWPList     = []
        # ### Grenzen
        self.IoGList     = []
        self.IuGList     = []
        self.PoGList     = []
        self.PuGList     = []
        self.UoGList     = []
        self.UuGList     = []
               
        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.curveDict      = {'IWP': '', 'IWU': '', 'IWI': '', 'IWf': '', 'SWP': '', 'SWU': '', 'SWI': '', 'oGI':'', 'uGI':'', 'oGU':'', 'uGU':'', 'oGP':'', 'uGP':'', 'RezI':'', 'RezU':'', 'RezP':''}                         # Kurven
        for kurve in self.kurven_dict: 
            self.curveDict[kurve] = self.kurven_dict[kurve]
        self.labelDict      = {'IWP': self.La_IstPow_wert,  'IWU': self.La_IstVoltage_wert,    'IWI': self.La_IstCurrent_wert,   'IWf': self.La_IstFre_wert}                                                                     # Label
        self.labelUnitDict  = {'IWP': 'kW',                 'IWU': 'V',                        'IWI': 'A',                       'IWf': 'kHz'}                                                                                   # Einheit
        self.listDict       = {'IWP': self.IWPList,         'IWU': self.IWUList,               'IWI': self.IWIList,              'IWf': self.IWfList,        'SWP': self.SWPList,  'SWU': self.SWUList,  'SWI': self.SWIList}    # Werte-Listen
        self.grenzListDict  = {'oGP': self.PoGList,         'uGP': self.PuGList,                'oGU': self.UoGList,             'uGU': self.UuGList,        'oGI': self.IoGList,  'uGI': self.IuGList}
        self.grenzValueDict = {'oGP': self.oGP,             'uGP': self.uGP,                    'oGU': self.oGU,                 'uGU': self.uGU,            'oGI': self.oGI,      'uGI': self.uGI}

        ## Plot-Skalierungsfaktoren:
        self.skalFak_dict = {}
        for size in self.curveDict:
            if 'WP' in size:
                self.skalFak_dict.update({size: self.skalFak['Pow']})
            if 'WI' in size:
                self.skalFak_dict.update({size: self.skalFak['Current']})
            if 'WU' in size:
                self.skalFak_dict.update({size: self.skalFak['Voltage']})
            if 'Wf' in size:
                self.skalFak_dict.update({size: self.skalFak['Freq']})

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
    def Fehler_Output(self, Fehler, error_Message_Log_GUI = '', error_Message_Ablauf = ''):
        ''' Erstelle Fehler-Nachricht für GUI, Ablaufdatei und Logging
        Args:
            Fehler (bool):                  False -> o.k. (schwarz), True -> Fehler (rot, bold)
            error_Message_Log_GUI (str):    Nachricht die im Log und der GUI angezeigt wird
            error_Message_Ablauf (str):     Nachricht für die Ablaufdatei
        ''' 
        if Fehler:
            self.La_error.setText(self.err_0_str[self.sprache])
            self.La_error.setToolTip(error_Message_Log_GUI)  
            self.La_error.setStyleSheet(f"color: red; font-weight: bold")
            log_vorberietung = error_Message_Log_GUI.replace("\n"," ")
            logger.error(f'{self.device_name} - {log_vorberietung}')
        else:
            self.La_error.setText(self.err_13_str[self.sprache])
            self.La_error.setToolTip('')
            self.La_error.setStyleSheet(f"color: black; font-weight: normal")
        if not error_Message_Ablauf == '':
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {error_Message_Ablauf}') 
        
    ##########################################
    # Reaktion auf Radio-Butttons:
    ##########################################
    def BlassOutUI(self, selected):
        ''' Leistungs Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_13_str[self.sprache]}')
            self.LE_Pow.setEnabled(True)
            self.LE_Current.setEnabled(False)
            self.LE_Voltage.setEnabled(False)

    def BlassOutPI(self, selected):
        ''' Spannungs Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_14_str[self.sprache]}')
            self.LE_Pow.setEnabled(False)
            self.LE_Current.setEnabled(False)
            self.LE_Voltage.setEnabled(True)

    def BlassOutPU(self, selected):
        ''' Strom Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_15_str[self.sprache]}')
            self.LE_Pow.setEnabled(False)
            self.LE_Current.setEnabled(True)
            self.LE_Voltage.setEnabled(False)

    ##########################################
    # Reaktion auf Butttons:
    ##########################################
    def send(self):
        ''' Sende Knopf betätigt:
        - Lese Eingabefelder aus
        - Kontrolliere Wert
        - Sage Programm Bescheid das Knopf betätigt wurde!
        '''
        if self.init:
            # Wenn der Radio-Button der Solltemperatur gewählt ist:
            if self.RB_choise_Pow.isChecked():
                sollwert = self.LE_Pow.text().replace(",", ".")
                self.write_task['Soll-Leistung'] = True
                self.write_task['Soll-Spannung'] = False
                self.write_task['Soll-Strom'] = False
                oG, uG = self.oGP, self.uGP
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_16_str[self.sprache]}')
            # Wenn der Radio-Button der Sollspannung gewählt ist:
            elif self.RB_choise_Voltage.isChecked():
                sollwert = self.LE_Voltage.text().replace(",", ".")
                self.write_task['Soll-Leistung'] = False
                self.write_task['Soll-Spannung'] = True
                self.write_task['Soll-Strom'] = False
                oG, uG = self.oGU, self.uGU
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_17_str[self.sprache]}')
            # Wenn der Radio-Button der Sollspannung gewählt ist:
            else:
                sollwert = self.LE_Current.text().replace(",", ".")
                self.write_task['Soll-Leistung'] = False
                self.write_task['Soll-Spannung'] = False
                self.write_task['Soll-Strom'] = True
                oG, uG = self.oGI, self.uGI
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_18_str[self.sprache]}')
            # Kontrolliere die Eingabe im Eingabefeld:
            sollwert = self.controll_value(sollwert, oG, uG)
            # Ist alles in Ordnung, dann Gebe dem Programm Bescheid, das es den Wert schreiben kann:
            if sollwert != -1:
                self.write_value['Sollwert'] = sollwert
            else:
                self.write_task['Soll-Leistung'] = False
                self.write_task['Soll-Spannung'] = False
                self.write_task['Soll-Strom'] = False
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def THEin(self):
        '''Schalte Generator Ein'''
        if self.init:
            self.write_task['Ein'] = True
            self.write_task['Aus'] = False
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def THAus(self):
        '''Schalte Generator Aus'''
        if self.init:
            self.write_task['Aus'] = True
            self.write_task['Ein'] = False
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    ##########################################
    # Eingabefeld Kontrolle:
    ##########################################
    def controll_value(self, value, oG, uG):
        ''' Kontrolliere die Eingabe eines Eingabefeldes.

        Args:
            value (str):    zu untersuchende Eingabe
            oG (int):       Ober Grenze
            uG (int):       Unter Grenze
        Return:
            -1 (int):       Fehlerfall
            value (float):  Ausgelesener Wert
        '''

        if value == '':
            self.Fehler_Output(1, self.err_1_str[self.sprache], self.Text_19_str[self.sprache])                             
        else:
            try:
                value = float(value)
                if value < uG or value > oG:
                    self.Fehler_Output(1, f'{self.err_2_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG}', self.Text_20_str[self.sprache])     
                else:
                    self.Fehler_Output(0, error_Message_Ablauf=f'{self.Text_21_str[self.sprache]} {value}.')                                      
                    return value
            except Exception as e:
                self.Fehler_Output(1, self.err_5_str[self.sprache], self.Text_22_str[self.sprache])   
                logger.exception(f"{self.device_name} - {self.Log_Text_38_str[self.sprache]}")
                                
        return -1

    ##########################################
    # Reaktion auf übergeordnete Butttons:
    ##########################################
    def Stopp(self, n = 3):
        ''' Setzt den Eurotherm in einen Sicheren Zustand '''
        if n == 5:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_90_str[self.sprache]}')
        self.RezEnde(n)
        self.THAus()
        self.write_value['Sollwert'] = 0
        self.write_task['Soll-Leistung'] = True
        self.write_task['Soll-Spannung'] = True
        self.write_task['Soll-Strom'] = True

    def update_Limit(self):
        '''Lese die Config und Update die Limits'''

        # Yaml erneut laden:
        with open(self.config_dat, encoding="utf-8") as f: 
            config = yaml.safe_load(f)
            logger.info(f"{self.device_name} - {self.Log_Text_205_str[self.sprache]} {config}")
        
        ### Sollleistung:
        self.oGP = config['devices'][self.device_name]["limits"]['maxP']        
        self.uGP = config['devices'][self.device_name]["limits"]['minP']
        ### Sollstrom:
        self.oGI = config['devices'][self.device_name]["limits"]['maxI']        
        self.uGI = config['devices'][self.device_name]["limits"]['minI']
        ### Sollspannung:
        self.oGU = config['devices'][self.device_name]["limits"]['maxU']        
        self.uGU = config['devices'][self.device_name]["limits"]['minU']

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
            if not 'SW' in messung:
               self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}')
            self.listDict[messung].append(value_dict[messung])
            if not self.curveDict[messung] == '':
                faktor = self.skalFak_dict[messung]
                y = [a * faktor for a in self.listDict[messung]]
                self.curveDict[messung].setData(x_value, y)

        # Grenz-Kurven:
        ## Update Grenzwert-Dictionary:
        self.grenzValueDict['oGP'] = self.oGP * self.skalFak['Pow']
        self.grenzValueDict['uGP'] = self.uGP * self.skalFak['Pow']
        self.grenzValueDict['oGU'] = self.oGU * self.skalFak['Voltage']
        self.grenzValueDict['uGU'] = self.uGU * self.skalFak['Voltage']
        self.grenzValueDict['oGI'] = self.oGI * self.skalFak['Current']
        self.grenzValueDict['uGI'] = self.uGI * self.skalFak['Current']
        ## Update-Kurven:
        for kurve in self.kurven_dict:
            if kurve in self.grenzListDict:
                self.grenzListDict[kurve].append(float(self.grenzValueDict[kurve]))
                self.kurven_dict[kurve].setData(x_value, self.grenzListDict[kurve])
        
    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung soll durch geführt werden '''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_23_str[self.sprache]}')
        self.write_task['Init'] = True
        if self.config['start']["readTime"] == 0:  
            self.typ_widget.Message(self.Message_1[self.sprache], 3)
            
    def init_controll(self, init_okay, menu):
        ''' Anzeige auf GUI ändern 
        
        Args:
            init_okay (bool):   Ändert die Init-Variable und das Icon in der GUI, je nach dem wie das Gerät entschieden hat!
            menu (QAction):     Menü Zeile in der das Icon geändert werden soll!               
        '''
        if init_okay:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_Okay.png"))
            self.init = True
        else:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_nicht_Okay.png"))
            self.init = False

    def Start(self):
        '''Funktion die nur beim Start beachtet werden muss (Init oder Start)'''
        if self.stMode == 'U':
            self.RB_choise_Voltage.setChecked(True)
            self.LE_Pow.setEnabled(False)
            self.LE_Voltage.setEnabled(True)
            self.LE_Current.setEnabled(False)
        elif self.stMode == 'I':
            self.RB_choise_Current.setChecked(True)
            self.LE_Pow.setEnabled(False)
            self.LE_Voltage.setEnabled(False)
            self.LE_Current.setEnabled(True)
        else:                                           # Leistung ist Default!
            self.RB_choise_Pow.setChecked(True)
            self.LE_Pow.setEnabled(True)
            self.LE_Voltage.setEnabled(False)
            self.LE_Current.setEnabled(False)

    ##########################################
    # Reaktion auf Rezepte:
    ##########################################
    def RezStart(self, execute = 1):
        ''' Rezept wurde gestartet '''
        if not self.Rezept_Aktiv:
            if execute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_87_str[self.sprache]}')
            elif execute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_85_str[self.sprache]}')
            # Variablen:
            self.step = 0
            self.Rezept_Aktiv = True

            # Kurve erstellen:
            error = self.RezKurveAnzeige()
            if self.cb_Rezept.currentText() == '------------':
                self.Fehler_Output(1, self.err_15_str[self.sprache])
                error = True
            
            if not error:
                # Rezept Log-Notiz:
                logger.info(f'{self.device_name} - {self.Log_Text_39_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}')
                logger.info(f'{self.device_name} - {self.Log_Text_40_str[self.sprache]} {self.rezept_daten}')
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_24_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}')                    

                # Erstes Element senden und Kurve erstellen:
                self.write_value['Sollwert'] = self.value_list[self.step]

                if self.RB_choise_Pow.isChecked():
                    self.write_task['Soll-Leistung'] = True
                elif self.RB_choise_Voltage.isChecked():
                    self.write_task['Soll-Spannung'] = True
                elif self.RB_choise_Current.isChecked():
                    self.write_task['Soll-Strom'] = True

                # Elemente GUI sperren:
                self.cb_Rezept.setEnabled(False)
                self.btn_rezept_start.setEnabled(False)
                self.RB_choise_Pow.setEnabled(False)
                self.RB_choise_Voltage.setEnabled(False)
                self.RB_choise_Current.setEnabled(False)
                self.btn_send_value.setEnabled(False)
                self.Auswahl.setEnabled(False)

                # Timer Starten:
                self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))
                self.RezTimer.start()
                self.Fehler_Output(0)
            else:
                self.Rezept_Aktiv = False
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_88_str[self.sprache]}')
        else:
            self.Fehler_Output(1, self.err_16_str[self.sprache], self.Text_84_str[self.sprache])

    def RezEnde(self, excecute = 1):
        ''' Rezept wurde/wird beendet '''
        if self.Rezept_Aktiv == True:
            if excecute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_81_str[self.sprache]}')
            elif excecute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_82_str[self.sprache]}')
            elif excecute == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_83_str[self.sprache]}')
            elif excecute == 4: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_86_str[self.sprache]}')
            elif excecute == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_91_str[self.sprache]}')

            # Elemente GUI entsperren:
            self.cb_Rezept.setEnabled(True)
            self.btn_rezept_start.setEnabled(True)
            self.RB_choise_Pow.setEnabled(True)
            self.RB_choise_Voltage.setEnabled(True)
            self.RB_choise_Current.setEnabled(True)
            self.btn_send_value.setEnabled(True)
            self.Auswahl.setEnabled(True)

            # Variablen:
            self.Rezept_Aktiv = False

            # Auto Range
            self.typ_widget.plot.AutoRange()

            # Nachricht:
            self.Fehler_Output(0)

            # Timer stoppen:
            self.RezTimer.stop()
        else:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_89_str[self.sprache]}')
        
    def Rezept(self):
        ''' Rezept Schritt wurde beendet, Vorbereitung und Start des neuen '''
        self.step += 1
        if self.step > len(self.time_list) - 1:
            self.RezEnde(2)
        else:
            self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))

            # Nächstes Element senden:
            self.write_value['Sollwert'] = self.value_list[self.step]

            if self.RB_choise_Pow.isChecked():
                self.write_task['Soll-Leistung'] = True
            elif self.RB_choise_Voltage.isChecked():
                self.write_task['Soll-Spannung'] = True
            elif self.RB_choise_Current.isChecked():
                self.write_task['Soll-Strom'] = True
    
    def Rezept_lesen_controll(self):
        ''' Rezept wird ausgelesen und kontrolliert. Bei Fehler werden die Fehlermeldungen beschrieben auf der GUI. 
    
        Return:
            error (Bool):   Fehler vorhanden oder nicht
        '''
        # Variablen:
        error = False  
        self.time_list  = []
        self.value_list = []

        ## Limits (Leistung, Strom oder Spannung):
        if self.RB_choise_Pow.isChecked():
            uG = self.uGP
            oG = self.oGP
            ak_value = self.ak_value['IWP'] if not self.ak_value == {} else 0
        elif self.RB_choise_Voltage.isChecked():
            uG = self.uGU
            oG = self.oGU
            ak_value = self.ak_value['IWU'] if not self.ak_value == {} else 0
        else:
            uG = self.uGI
            oG = self.oGI
            ak_value = self.ak_value['IWI'] if not self.ak_value == {} else 0

        # Rezept lesen:
        rezept = self.cb_Rezept.currentText()  
        if not rezept == '------------':
            ## Rezept aus Datei oder in Config:
            ak_rezept = self.rezept_config[rezept]
            if 'dat' in ak_rezept:
                try:
                    with open(f'vifcon/rezepte/{ak_rezept["dat"]}', encoding="utf-8") as f:
                        rez_dat = yaml.safe_load(f)
                    self.rezept_datei = f'({ak_rezept["dat"]})'
                except:
                    self.Fehler_Output(1, self.err_10_str[self.sprache])
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
                self.Fehler_Output(1, self.err_12_str[self.sprache])
                return False
            ## Rezept Kurven-Listen erstellen:
            for n in rez_dat:
                werte = rez_dat[n].split(';')
                ## Beachtung von Kommas (Komma zu Punkt):
                time = float(werte[0].replace(',', '.'))
                value = float(werte[1].replace(',', '.'))
                ## Grenzwert-Kontrolle:
                if value < uG or value > oG:
                    error = True
                    self.Fehler_Output(1, f'{self.err_6_str[self.sprache]} {value} {self.err_7_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG}!')
                    break
                else:
                    self.Fehler_Output(0)
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
        else:
            self.Fehler_Output(0)
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

        anzeigeI = True
        anzeigeP = True      
        anzeigeU = True                         
        try: self.curveDict['RezI'].setData(self.RezTimeList, self.RezValueList)
        except: anzeigeI  = False
        try: self.curveDict['RezU'].setData(self.RezTimeList, self.RezValueList)
        except: anzeigeU = False   
        try: self.curveDict['RezP'].setData(self.RezTimeList, self.RezValueList)
        except: anzeigeP = False                          
        
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
            
            # Kurve erstellen mit Skalierungsfaktor und Kurve Anzeigen:
            ## Leistung, Strom oder Spannung:
            if self.RB_choise_Pow.isChecked():
                faktor = self.skalFak['Pow']
                y = [a * faktor for a in self.RezValueList]
                if anzeigeP:
                    self.curveDict['RezP'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_2.autoRange()                    # Rezept Achse 2 wird nicht fertig angezeigt, aus dem Grund wird dies durchgeführt! Beim Enden wird die AutoRange Funktion von base_classes.py durchgeführt. Bewegung des Plots sind mit der Lösung nicht machbar!!
                                                                                # Plot wird nur an Achse 1 (links) angepasst!
            elif self.RB_choise_Voltage.isChecked():
                faktor = self.skalFak['Voltage']
                y = [a * faktor for a in self.RezValueList]
                if anzeigeU:
                    self.curveDict['RezU'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_1.autoRange()
            else:
                faktor = self.skalFak['Current']
                y = [a * faktor for a in self.RezValueList]
                if anzeigeI:
                    self.curveDict['RezI'].setData(self.RezTimeList, y)
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
            for rezept in self.rezept_config:
                self.cb_Rezept.addItem(rezept) 

            # Neu verbinden von der Funktion:
            self.cb_Rezept.currentTextChanged.connect(self.RezKurveAnzeige) 

            self.Fehler_Output(0)
        else:
            self.Fehler_Output(1, self.err_14_str[self.sprache])

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''
