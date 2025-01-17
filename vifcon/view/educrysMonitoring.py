# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Educrys Monitoring Geräte GUI:
- Label
- Werte Angabe und Eingabe
- wird an Tab Monitoring angefügt
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,

)
from PyQt5.QtGui import (
    QIcon, 

)
from PyQt5.QtCore import (
    Qt,

)

## Allgemein:
import logging

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class EducrysMonWidget:
    def __init__(self, sprache, Frame_Anzeige, widget, config, config_dat, add_Ablauf_function, educrysMon = 'Educrys-Monitoring', typ = 'Monitoring', parent=None):
        """GUI widget of Educrys Monitoring.

        Args:
            sprache (int):                      Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):               Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (Objekt):                    Element in das, das Widget eingefügt wird
            config (dict):                      Konfigurationsdaten aus der YAML-Datei
            config_dat (string):                Datei-Name der Config-Datei
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            educrysMon (str):                   Name des Gerätes
            typ (str):                          Typ des Gerätes
        """

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Funktionsübergabe einlesen:
        self.sprache                    = sprache
        self.typ_widget                 = widget
        self.config                     = config
        self.config_dat                 = config_dat
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = educrysMon
        self.typ                        = typ

        ## Dictionary:
        self.write_task     = {'Init':False}
        self.write_value    = {}
        self.data           = {}
        
        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Überschriften und Größenbezeichnung: #####################################################################################################################################################################################################################################################                    
        ü1_str                  = ['M1. Temperatur',                                            'M1. Temperature']
        ü2_str                  = ['M2. PID',                                                   'M2. PID']
        ü3_str                  = ['M3. Kristall',                                              'M3. Crystal']
        ## Bezeichnung: #############################################################################################################################################################################################################################################################################
        B1_str                  = ['TC1',                                                       'TC1']
        B2_str                  = ['TC2',                                                       'TC2'] 
        B3_str                  = ['PT1',                                                       'PT1'] 
        B4_str                  = ['PT2',                                                       'PT2'] 
        B5_str                  = ['Pyrometer',                                                 'Pyrometer']
        B6_str                  = ['Output',                                                    'Output']
        B7_str                  = ['P-Anteil',                                                  'P-Share'] 
        B8_str                  = ['I-Anteil',                                                  'I-Share'] 
        B9_str                  = ['D-Anteil',                                                  'D-Share'] 
        B10_str                 = ['Input',                                                     'Input']
        B11_str                 = ['Input gemittelt',                                           'Input average']
        B12_str                 = ['Gewicht',                                                   'Weight']
        B13_str                 = ['Gewicht gemittelt',                                         'Weight averaged']
        B14_str                 = ['Durchmesser',                                               'Diameter']
        ## Einheit: ################################################################################################################################################################################################################################################################################                                                 
        E1_G_str                = ['g',                                                         'g']
        E2_PIDO_str             = ['ms',                                                        'ms']
        E3_D_str                = ['mm',                                                        'mm']
        E4_T_str                = ['°C',                                                        '°C']
        E5_PIDP_str             = ['ms',                                                        'ms']
        ## Ablaufdatei: ############################################################################################################################################################################################################################################################################
        self.Text_1_str         = ['Initialisierungsknopf betätigt.',                           'Initialization button pressed.']
        ## Logging: ################################################################################################################################################################################################################################################################################                     
        self.Log_Text_1_str     = ['Erstelle Widget.',                                          'Create widget.']
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                          'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                             'Possible values:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                  'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',        'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                      '; Set to default:']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                              'Reason for error:']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                      'Incorrect input:']

        #---------------------------------------------------------
        # Konfigurationskontrolle und Konfigurationsvariablen:
        #---------------------------------------------------------
        ## Zum Start:
        try: self.init = self.config['start']['init']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.init = False

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Config-Fehler und Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0

        #---------------------------------------    
        # GUI:
        #---------------------------------------
        ## Grundgerüst:
        self.layer_widget = QWidget()
        self.layer_layout = QGridLayout()
        self.layer_widget.setLayout(self.layer_layout)
        self.typ_widget.splitter.addWidget(self.layer_widget)
        logger.info(f"{self.device_name} - {self.Log_Text_1_str[self.sprache]}")
        #________________________________________
        ## Kompakteres Darstellen:
        ### Grid Size - bei Verschieben der Splitter zusammenhängend darstellen: (Notiz: Das bei GUI in Arbeit erläutern!)
        self.layer_layout.setRowStretch(21, 1) 
        self.layer_layout.setColumnStretch(4, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)       
        self.layer_layout.setVerticalSpacing(1)

        #________________________________________
        ## Spalten Breite:
        self.layer_layout.setColumnMinimumWidth(0, 100)

        #________________________________________
        ## Widgets:
        ### Label:
        #### Überschriften:
        self.La_name = QLabel(f'<b>{educrysMon}</b>')
        self.labelÜ1 = QLabel(f'<b>{ü1_str[self.sprache]}:</b>')        # Temperatur
        self.labelÜ2 = QLabel(f'<b>{ü2_str[self.sprache]}:</b>')        # PID
        self.labelÜ3 = QLabel(f'<b>{ü3_str[self.sprache]}:</b>')        # Kristall

        #### Temperatur:
        self.TlabelSize_TC1 = QLabel(f'{B1_str[self.sprache]}')
        self.TlabelValu_TC1 = QLabel()
        self.TlabelUnit_TC1 = QLabel(E4_T_str[self.sprache])

        self.TlabelSize_TC2 = QLabel(f'{B2_str[self.sprache]}')
        self.TlabelValu_TC2 = QLabel()
        self.TlabelUnit_TC2 = QLabel(E4_T_str[self.sprache])

        self.TlabelSize_PT1 = QLabel(f'{B3_str[self.sprache]}')
        self.TlabelValu_PT1 = QLabel()
        self.TlabelUnit_PT1 = QLabel(E4_T_str[self.sprache])

        self.TlabelSize_PT2 = QLabel(f'{B4_str[self.sprache]}')
        self.TlabelValu_PT2 = QLabel()
        self.TlabelUnit_PT2 = QLabel(E4_T_str[self.sprache])

        self.TlabelSize_Pyr = QLabel(f'{B5_str[self.sprache]}')
        self.TlabelValu_Pyr = QLabel()
        self.TlabelUnit_Pyr = QLabel(E4_T_str[self.sprache])

        #### PID:
        self.PlabelSize_Out = QLabel(f'{B6_str[self.sprache]}')
        self.PlabelValu_Out = QLabel()
        self.PlabelUnit_Out = QLabel(E2_PIDO_str[self.sprache])

        self.PlabelSize_PGl = QLabel(f'{B7_str[self.sprache]}')
        self.PlabelValu_PGl = QLabel()
        self.PlabelUnit_PGl = QLabel(E5_PIDP_str[self.sprache])

        self.PlabelSize_IGl = QLabel(f'{B8_str[self.sprache]}')
        self.PlabelValu_IGl = QLabel()
        self.PlabelUnit_IGl = QLabel(E5_PIDP_str[self.sprache])

        self.PlabelSize_DGl = QLabel(f'{B9_str[self.sprache]}')
        self.PlabelValu_DGl = QLabel()
        self.PlabelUnit_DGl = QLabel(E5_PIDP_str[self.sprache])

        self.PlabelSize_Inp = QLabel(f'{B10_str[self.sprache]}')
        self.PlabelValu_Inp = QLabel()
        self.PlabelUnit_Inp = QLabel(E4_T_str[self.sprache])

        self.PlabelSize_Ing = QLabel(f'{B11_str[self.sprache]}')
        self.PlabelValu_Ing = QLabel()
        self.PlabelUnit_Ing = QLabel(E4_T_str[self.sprache])

        #### Kristall:
        self.KlabelSize_Gew = QLabel(f'{B12_str[self.sprache]}')
        self.KlabelValu_Gew = QLabel()
        self.KlabelUnit_Gew = QLabel(E1_G_str[self.sprache])

        self.KlabelSize_Geg = QLabel(f'{B13_str[self.sprache]}')
        self.KlabelValu_Geg = QLabel()
        self.KlabelUnit_Geg = QLabel(E1_G_str[self.sprache])

        self.KlabelSize_Dum = QLabel(f'{B14_str[self.sprache]}')
        self.KlabelValu_Dum = QLabel()
        self.KlabelUnit_Dum = QLabel(E3_D_str[self.sprache])

        #________________________________________
        ## Platzierung der einzelnen Widgets im Layout:
        CS = 3
        self.layer_layout.addWidget(self.La_name,           0,  0,  1,  CS                          )     # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung
        ### Temperatur:
        self.layer_layout.addWidget(self.labelÜ1,           1,  0                                   )
        self.layer_layout.addWidget(self.TlabelSize_TC1,    2,  0                                   )                          
        self.layer_layout.addWidget(self.TlabelValu_TC1,    2,  1                                   )
        self.layer_layout.addWidget(self.TlabelUnit_TC1,    2,  2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.TlabelSize_TC2,    3,  0                                   )                          
        self.layer_layout.addWidget(self.TlabelValu_TC2,    3,  1                                   )
        self.layer_layout.addWidget(self.TlabelUnit_TC2,    3,  2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.TlabelSize_PT1,    4,  0                                   )                          
        self.layer_layout.addWidget(self.TlabelValu_PT1,    4,  1                                   )
        self.layer_layout.addWidget(self.TlabelUnit_PT1,    4,  2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.TlabelSize_PT2,    5,  0                                   )                          
        self.layer_layout.addWidget(self.TlabelValu_PT2,    5,  1                                   )
        self.layer_layout.addWidget(self.TlabelUnit_PT2,    5,  2,            alignment=Qt.AlignLeft)
        self.Leerzeile(6, 0, 3) 
        ### PID:
        self.layer_layout.addWidget(self.labelÜ2,           7,  0                                   )
        self.layer_layout.addWidget(self.PlabelSize_Out,    8,  0                                   )                          
        self.layer_layout.addWidget(self.PlabelValu_Out,    8,  1                                   )
        self.layer_layout.addWidget(self.PlabelUnit_Out,    8,  2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.PlabelSize_PGl,    9,  0                                   )                          
        self.layer_layout.addWidget(self.PlabelValu_PGl,    9,  1                                   )
        self.layer_layout.addWidget(self.PlabelUnit_PGl,    9,  2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.PlabelSize_IGl,    10, 0                                   )                          
        self.layer_layout.addWidget(self.PlabelValu_IGl,    10, 1                                   )
        self.layer_layout.addWidget(self.PlabelUnit_IGl,    10, 2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.PlabelSize_DGl,    11, 0                                   )                          
        self.layer_layout.addWidget(self.PlabelValu_DGl,    11, 1                                   )
        self.layer_layout.addWidget(self.PlabelUnit_DGl,    11, 2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.PlabelSize_Inp,    12, 0                                   )                          
        self.layer_layout.addWidget(self.PlabelValu_Inp,    12, 1                                   )
        self.layer_layout.addWidget(self.PlabelUnit_Inp,    12, 2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.PlabelSize_Ing,    13, 0                                   )                          
        self.layer_layout.addWidget(self.PlabelValu_Ing,    13, 1                                   )
        self.layer_layout.addWidget(self.PlabelUnit_Ing,    13, 2,            alignment=Qt.AlignLeft)
        self.Leerzeile(14, 0, 3)
        ### Kristall:
        self.layer_layout.addWidget(self.labelÜ3,           15, 0                                   )
        self.layer_layout.addWidget(self.KlabelSize_Gew,    16, 0                                   )                          
        self.layer_layout.addWidget(self.KlabelValu_Gew,    16, 1                                   )
        self.layer_layout.addWidget(self.KlabelUnit_Gew,    16, 2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.KlabelSize_Geg,    17, 0                                   )                          
        self.layer_layout.addWidget(self.KlabelValu_Geg,    17, 1                                   )
        self.layer_layout.addWidget(self.KlabelUnit_Geg,    17, 2,            alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.KlabelSize_Dum,    18, 0                                   )                          
        self.layer_layout.addWidget(self.KlabelValu_Dum,    18, 1                                   )
        self.layer_layout.addWidget(self.KlabelUnit_Dum,    18, 2,            alignment=Qt.AlignLeft)
        self.Leerzeile(19, 0, 3)

        #________________________________________
        ## Border Sichtbar:
        if Frame_Anzeige:
            self.layer_widget.setStyleSheet("border: 1px solid black;")

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.labelDict      = {'TC1_T': self.TlabelValu_TC1,    'TC2_T': self.TlabelValu_TC2,       'PT1_T': self.TlabelValu_PT1,   'PT2_T': self.TlabelValu_PT2,   'Pyro_T': self.TlabelValu_Pyr,
                               'PID_Out': self.PlabelValu_Out,  'PID_P': self.PlabelValu_PGl,       'PID_I': self.PlabelValu_IGl,   'PID_D': self.PlabelValu_DGl,   'PID_In': self.PlabelValu_Inp,  'PID_In_M': self.PlabelValu_Ing,
                               'K_weight': self.KlabelValu_Gew, 'K_weight_M': self.KlabelValu_Geg,  'K_d': self.KlabelValu_Dum
                              }   

    ##########################################
    # GUI-Funktion:
    ##########################################
    def Leerzeile(self, Row, startColum = 0, AnzColum = -1):
        '''
        Erstellt eine Leerzeile, eine Art Strich!

        Args:
            Row (int):          Zeilennummer
            startColum (int):   Start_Spalte
            AnzColum (int):     Colum-Span -> Anzahl Spalten (-1 bis Ende)    
        '''
        # Leerzeile ChatBot:
        empty_widget = QWidget()
        empty_widget.setFixedHeight(1)                              # Festlegen der Höhe
        empty_widget.setStyleSheet("background-color: black")       # Festlegen der Hintergrundfarbe
        self.layer_layout.addWidget(empty_widget, Row, startColum , 1 , AnzColum) 

    def Leerspalte(self, Colom, startRow = 0, AnzRow = -1):
        '''
        Erstellt eine LeerSpalte, eine Art Strich!

        Args:
            Colom (int):        Spaltennummer
            startRow (int):     Start-Reihe
            AnzRow (int):       Row-Span -> Anzahl Reihen (-1 bis Ende) 
        '''
        # Leerzeile ChatBot:
        empty_widget = QWidget()
        empty_widget.setFixedWidth(1)                              # Festlegen der Höhe
        empty_widget.setStyleSheet("background-color: black")       # Festlegen der Hintergrundfarbe
        self.layer_layout.addWidget(empty_widget, startRow, Colom, AnzRow, 1) 

    ##########################################
    # Betrachtung der Labels:
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
            self.labelDict[messung].setText(f'{value_dict[messung]}')

    ##########################################
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung soll durch geführt werden '''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_1_str[self.sprache]}')
        self.write_task['Init'] = True
            
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

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''