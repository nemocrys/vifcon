# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Nemo Gase Geräte GUI:
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


class NemoGaseWidget:
    def __init__(self, sprache, Frame_Anzeige, widget, config, config_dat, add_Ablauf_function, nemoGase = 'Nemo-Gase', typ = 'Monitoring', parent=None):
        """GUI widget of Nemo Gase.

        Args:
            sprache (int):                      Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):               Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (Objekt):                    Element in das, das Widget eingefügt wird
            config (dict):                      Konfigurationsdaten aus der YAML-Datei
            config_dat (string):                Datei-Name der Config-Datei
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            nemoGase (str):                     Name des Gerätes
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
        self.device_name                = nemoGase
        self.typ                        = typ

        ## Dictionary:
        self.write_task     = {'Init':False}
        self.write_value    = {}
        self.data           = {}

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Anlage:
        self.nemo               = ['Nemo-Anlage',                       'Nemo facility']
        ## Überschriften und Größenbezeichnung:
        ü1_str                  = ['Durchfluss',                        'Flow']
        ü2_str                  = ['Druck',                             'Pressure']
        ü3_str                  = ['Status',                            'Status']
        ü4_str                  = ['Drehzahl',                          'Rotational frequency']             # Rotational speed, Rate of rotation
        ## Status:                          
        self.no_sta_str         = ['Kein Status!',                      'No Status!']
        self.Stat_1_str         = ['Hand',                              'Manual']                           # Hand
        self.Stat_2_str         = ['Auto',                              'Auto']                             # Auto
        self.Stat_3_str         = ['Läuft',                             'Run']                              # Run
        self.Stat_4_str         = ['Norm',                              'Norm']                             # Norm
        self.Stat_5_str         = ['Warm',                              'Warm']                             # Warm
        self.Stat_6_str         = ['Fehler',                            'Error']                            # Err
        self.Stat_14_str        = ['Schnittstellenfehler',              'Interface error']
        self.Stat_15_str        = ['Test-Modus Aktiv',                  'Test Mode Active']
        ## Geräte-Bezeichnung:                  
        G1_F_str                = ['MFC24',                             'MFC24']
        G2_F_str                = ['MFC25',                             'MFC25']
        G3_F_str                = ['MFC26',                             'MFC26']
        G4_F_str                = ['MFC27',                             'MFC27']
        G5_D_str                = ['DM21',                              'DM21']
        G6_D_str                = ['PP21',                              'PP21']
        G7_D_str                = ['PP22',                              'PP22']
        ## Einheit:                         
        E1_F_str                = ['ml/min',                            'ml/min']
        E2_D_str                = ['mbar',                              'mbar']
        E3_n_str                = ['%',                                 '%']
        ## Ablaufdatei:
        self.Text_1_str         = ['Initialisierungsknopf betätigt.',   'Initialization button pressed.']
        ## Logging:
        self.Log_Text_1_str     = ['Erstelle Widget.',                  'Create widget.']
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',  'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                     'Possible values:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',          'Default is used:']
        
        #---------------------------------------------------------
        # Konfigurationskontrolle und Konfigurationsvariablen:
        #---------------------------------------------------------
        ## Übergeordnet:
        self.Anlage = self.config['nemo-Version']
        ## Zum Start:
        self.init = self.config['start']['init']

        ## Config-Fehler und Defaults:
        if not self.Anlage in [1, 2]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nemo-Version - {self.Log_Pfad_conf_2[self.sprache]} [1, 2] - {self.Log_Pfad_conf_3[self.sprache]} 1')
            self.Anlage = 1

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
        self.layer_layout.setRowStretch(16, 1) 
        self.layer_layout.setColumnStretch(5, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)       
        self.layer_layout.setVerticalSpacing(1)
        #________________________________________
        ## Widgets:
        ### Label:
        #### Überschriften:
        self.La_name = QLabel(f'<b>{nemoGase}</b> ({self.nemo[self.sprache]} {self.Anlage})')
        self.labelÜ1 = QLabel(f'<b>{ü1_str[self.sprache]}:</b>')
        self.labelÜ2 = QLabel(f'<b>{ü2_str[self.sprache]}:</b>')
        self.labelÜ3 = QLabel(f'<b>{ü3_str[self.sprache]}:</b>')

        #### Flow:
        self.FlabelSize_MFC24 = QLabel(f'{G1_F_str[self.sprache]} {ü1_str[self.sprache]}: ')
        self.FlabelValu_MFC24 = QLabel()
        self.FlabelUnit_MFC24 = QLabel(E1_F_str[self.sprache])

        self.FlabelSize_MFC25 = QLabel(f'{G2_F_str[self.sprache]} {ü1_str[self.sprache]}: ')
        self.FlabelValu_MFC25 = QLabel()
        self.FlabelUnit_MFC25 = QLabel(E1_F_str[self.sprache])

        self.FlabelSize_MFC26 = QLabel(f'{G3_F_str[self.sprache]} {ü1_str[self.sprache]}: ')
        self.FlabelValu_MFC26 = QLabel()
        self.FlabelUnit_MFC26 = QLabel(E1_F_str[self.sprache])

        self.FlabelSize_MFC27 = QLabel(f'{G4_F_str[self.sprache]} {ü1_str[self.sprache]}: ')
        self.FlabelValu_MFC27 = QLabel()
        self.FlabelUnit_MFC27 = QLabel(E1_F_str[self.sprache])

        #### Drücke
        self.DlabelSize_DM21 = QLabel(f'{G5_D_str[self.sprache]} {ü2_str[self.sprache]}: ')
        self.DlabelValu_DM21 = QLabel()
        self.DlabelUnit_DM21 = QLabel(E2_D_str[self.sprache])

        self.DlabelSize_PP21 = QLabel(f'{G6_D_str[self.sprache]} {ü2_str[self.sprache]}: ')
        self.DlabelValu_PP21 = QLabel()
        self.DlabelUnit_PP21 = QLabel(E2_D_str[self.sprache])

        self.DlabelSize_PP22 = QLabel(f'{G7_D_str[self.sprache]} {ü2_str[self.sprache]}: ')
        self.DlabelValu_PP22 = QLabel()
        self.DlabelUnit_PP22 = QLabel(E2_D_str[self.sprache])

        #### Pumpen Status:
        self.DSlabelSize_PP21 = QLabel(f'{G6_D_str[self.sprache]} {ü3_str[self.sprache]}: ')
        self.DSlabelValu_PP21 = QLabel()

        self.DSlabelSize_PP22 = QLabel(f'{G7_D_str[self.sprache]} {ü3_str[self.sprache]}: ')
        self.DSlabelValu_PP22 = QLabel()

        #### Pumpen Drehzahl:
        self.DIlabelSize_PP22 = QLabel(f'{G7_D_str[self.sprache]} {ü4_str[self.sprache]}: ')
        self.DIlabelValu_PP22 = QLabel()
        self.DIlabelUnit_PP22 = QLabel(E3_n_str[self.sprache])
        #________________________________________
        ## Platzierung der einzelnen Widgets im Layout:
        self.layer_layout.addWidget(self.La_name,               0,   0,  1, 3) 
        pos = 1
        self.layer_layout.addWidget(self.labelÜ1,               pos,   0) 
        self.layer_layout.addWidget(self.FlabelSize_MFC24,      pos+1, 0)                          # Reihe, Spalte, Ausrichtung
        self.layer_layout.addWidget(self.FlabelValu_MFC24,      pos+1, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC24,      pos+1, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.FlabelSize_MFC25,      pos+2, 0)                          
        self.layer_layout.addWidget(self.FlabelValu_MFC25,      pos+2, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC25,      pos+2, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.FlabelSize_MFC26,      pos+3, 0)                          
        self.layer_layout.addWidget(self.FlabelValu_MFC26,      pos+3, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC26,      pos+3, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.FlabelSize_MFC27,      pos+4, 0)                          
        self.layer_layout.addWidget(self.FlabelValu_MFC27,      pos+4, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC27,      pos+4, 2, alignment=Qt.AlignLeft)
        self.Leerzeile(pos+5)

        pos = 7
        self.layer_layout.addWidget(self.labelÜ2,               pos,   0) 
        self.layer_layout.addWidget(self.DlabelSize_DM21,       pos+1, 0)
        self.layer_layout.addWidget(self.DlabelValu_DM21,       pos+1, 1)
        self.layer_layout.addWidget(self.DlabelUnit_DM21,       pos+1, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.DlabelSize_PP21,       pos+2, 0)
        self.layer_layout.addWidget(self.DlabelValu_PP21,       pos+2, 1)
        self.layer_layout.addWidget(self.DlabelUnit_PP21,       pos+2, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.DlabelSize_PP22,       pos+3, 0)
        self.layer_layout.addWidget(self.DlabelValu_PP22,       pos+3, 1)
        self.layer_layout.addWidget(self.DlabelUnit_PP22,       pos+3, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.DIlabelSize_PP22,      pos+4, 0)
        self.layer_layout.addWidget(self.DIlabelValu_PP22,      pos+4, 1)
        self.layer_layout.addWidget(self.DIlabelUnit_PP22,      pos+4, 2, alignment=Qt.AlignLeft)
        self.Leerzeile(pos+5)
        
        pos = 13
        spa = 0
        self.layer_layout.addWidget(self.labelÜ3,               pos,   spa)
        self.layer_layout.addWidget(self.DSlabelSize_PP21,      pos+1, spa)
        self.layer_layout.addWidget(self.DSlabelValu_PP21,      pos+1, spa+2) 
        self.layer_layout.addWidget(self.DSlabelSize_PP22,      pos+2, spa)
        self.layer_layout.addWidget(self.DSlabelValu_PP22,      pos+2, spa+2)
        #________________________________________
        ## Border Sichtbar:
        if Frame_Anzeige:
            self.layer_widget.setStyleSheet("border: 1px solid black;")

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.labelDict      = {'MFC24': self.FlabelValu_MFC24, 'MFC25': self.FlabelValu_MFC25, 'MFC26': self.FlabelValu_MFC26,  'MFC27': self.FlabelValu_MFC27, 'DM21': self.DlabelValu_DM21, 'PP21': self.DlabelValu_PP21, 'PP22': self.DlabelValu_PP22, 'PP21Status': self.DSlabelValu_PP21, 'PP22Status': self.DSlabelValu_PP22, 'PP22I': self.DIlabelValu_PP22}     # Label

    ##########################################
    # GUI-Funktion:
    ##########################################
    def Leerzeile(self, Row):
        '''
        Erstellt eine Leerzeile, eine Art Strich!

        Args:
            Row:    Zeilennummer
        '''
        # Leerzeile ChatBot:
        empty_widget = QWidget()
        empty_widget.setFixedHeight(1)                              # Festlegen der Höhe
        empty_widget.setStyleSheet("background-color: black")       # Festlegen der Hintergrundfarbe
        self.layer_layout.addWidget(empty_widget, Row,0,1,-1) 

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
            if not 'Status' in messung:
                self.labelDict[messung].setText(f'{value_dict[messung]}')

        # Status:
        ## P21:
        status_1 = value_dict['PP21Status']
        status_1 = self.status_report_umwandlung(status_1)
        label_s1 = ''
        status = [self.Stat_1_str[self.sprache], self.Stat_2_str[self.sprache], '', '', '', '', '', '', self.Stat_3_str[self.sprache], '', '', '', '', '', self.Stat_14_str[self.sprache], self.Stat_15_str[self.sprache]]
        l = len(status_1)
        for n in range(0,l):
            if status_1[n] == '1':
                if not status[n] == '':
                    label_s1 = label_s1 + f'{status[n]}, '
        if label_s1 == '':
            label_s1 = self.no_sta_str[self.sprache]
        else:
            label_s1 = label_s1[0:-2]
        self.labelDict['PP21Status'].setText(f'{label_s1}')

        ## P22:
        status_2 = value_dict['PP22Status']
        status_2 = self.status_report_umwandlung(status_2)
        label_s2 = ''
        status = [self.Stat_1_str[self.sprache], self.Stat_2_str[self.sprache], '', '', '', '', '', '', self.Stat_3_str[self.sprache], self.Stat_4_str[self.sprache], self.Stat_5_str[self.sprache], self.Stat_6_str[self.sprache], '', '', self.Stat_14_str[self.sprache], self.Stat_15_str[self.sprache]]     # Lowest Bit zu Highest Bit
        l = len(status_2)
        for n in range(0,l):
            if status_2[n] == '1':
                if not status[n] == '':
                    label_s2 = label_s2 + f'{status[n]}, '
        if label_s2 == '':
            label_s2 = self.no_sta_str[self.sprache]
        else:
            label_s2 = label_s2[0:-2]
        self.labelDict['PP22Status'].setText(f'{label_s2}')
    
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
        
        if len(byte_list) == 1:
            byte_list.append('00000000')

        # Byte zusammensetzen in der richtigen Reihenfolge:
        byte_string = ''    
        for n in byte_list:
            byte_string = byte_string + n

        return byte_string[::-1]   # [::-1] --> dreht String um! (Lowest Bit to Highest Bit)
            
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