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
        ## Anlage: ##################################################################################################################################################################################################################################################################################
        self.nemo               = ['Nemo-Anlage',                                               'Nemo facility']
        ## Überschriften und Größenbezeichnung: #####################################################################################################################################################################################################################################################                    
        ü1_str                  = ['1. Durchfluss',                                             '1. Flow']
        ü2_str                  = ['2. Pumpen-Werte',                                           '2. Pump values']
        ü3_str                  = ['3. Status',                                                 '3. Status']
        ü4_str                  = ['Vakuum/Gas und Pumpen',                                     'Vacuum/Gas and Pumps']
        ## Bezeichnung: #############################################################################################################################################################################################################################################################################
        B1_str                  = ['Durchfluss',                                                'Flow']
        B2_str                  = ['Druck',                                                     'Pressure']
        B3_str                  = ['Status',                                                    'Status']
        B4_str                  = ['Drehzahl',                                                  'Rotational frequency']             # Rotational speed, Rate of rotation
        B5_str                  = ['max P zum Start',                                           'max P to start']
        B6_str                  = ['Ventilstellung',                                            'valve position']
        B7_str                  = ['Servicegrad',                                               'service level']
        B8_str                  = ['Sollwert',                                                  'Setpoint']
        B9_str                  = ['Istwert',                                                   'Actual value']
        B10_str                 = ['MaxFlow',                                                   'MaxFlow']
        ## Status: ##################################################################################################################################################################################################################################################################################                                                 
        self.no_sta_str         = ['Kein Status!',                                              'No Status!']
        ### Pumpe Nemo-1: ###########################################################################################################################################################################################################################################################################
        self.Stat_1_str         = ['Hand',                                                      'Manual']                           # Hand
        self.Stat_2_str         = ['Auto',                                                      'Auto']                             # Auto
        self.Stat_3_str         = ['Läuft',                                                     'Run']                              # Run
        self.Stat_4_str         = ['Norm',                                                      'Norm']                             # Norm
        self.Stat_5_str         = ['Warm',                                                      'Warm']                             # Warm
        self.Stat_6_str         = ['Fehler',                                                    'Error']                            # Err
        self.Stat_14_str        = ['Schnittstellenfehler',                                      'Interface error']
        self.Stat_15_str        = ['Test-Modus Aktiv',                                          'Test Mode Active']
        ### MFC/MV: ################################################################################################################################################################################################################################################################################
        self.Stat_MFC_1_str     = ['Auto',                                                      'Auto']
        self.Stat_MFC_2_str     = ['Rampe',                                                     'Ramp']
        ### Pumpe Nemo-2: ##########################################################################################################################################################################################################################################################################
        self.Stat_P1_1_str      = self.Stat_1_str 
        self.Stat_P1_2_str      = self.Stat_2_str
        self.Stat_P1_9_str      = self.Stat_3_str
        self.Stat_P2_1_str      = ['Sperre Ein',                                                'Lock On']
        self.Stat_P2_2_str      = ['Bereit',                                                    'Ready']
        self.Stat_P2_3_str      = self.Stat_3_str
        self.Stat_P2_10_str     = ['Warnung',                                                   'Warning']
        self.Stat_P2_11_str     = self.Stat_6_str
        ### Ventil: ##########################################################################################################################################################################################################################################################################
        self.Stat_V_1_str       = self.Stat_1_str
        self.Stat_V_2_str       = self.Stat_2_str
        self.Stat_V_9_str       = ['Ventil öffnet',                                             'Valve opens']
        self.Stat_V_10_str      = ['Ventil schließt',                                           'Valve closes']
        self.Stat_V_11_str      = ['Ventil Offen',                                              'Valve open']
        self.Stat_V_12_str      = ['Ventil Geschlossen',                                        'Valve closed']
        self.Stat_V_13_str      = self.Stat_6_str
        self.Stat_V_14_str      = ['Fehler Endlage Offen',                                      'Error End Position Open']
        self.Stat_V_15_str      = ['Fehler Endlage Zu',                                         'Error end position closed']
        ## Geräte-Bezeichnung: #####################################################################################################################################################################################################################################################################                                         
        ### Nemo-1 -> _1 | Nemo-2 -> _2
        G1_F_str_1              = ['MFC24',                                                     'MFC24']
        G1_F_str_2              = ['MFC1 (N2)',                                                 'MFC1 (N2)']
        G2_F_str_1              = ['MFC25',                                                     'MFC25']
        G2_F_str_2              = ['MFC2 (Ar)',                                                 'MFC2 (Ar)']
        G3_F_str_1              = ['MFC26',                                                     'MFC26']
        G3_F_str_2              = ['MFC3 (Luft)',                                               'MFC3 (Air)']
        G4_F_str_1              = ['MFC27',                                                     'MFC27']
        G4_F_str_2              = ['MFC4 (X)',                                                  'MFC4 (X)']
        G5_D_str_1              = ['DM21',                                                      'DM21']
        G6_D_str_1              = ['PP21',                                                      'PP21']
        G6_D_str_2              = ['PP1',                                                       'PP1']
        G7_D_str_1              = ['PP22',                                                      'PP22']
        G7_D_str_2              = ['PP2',                                                       'PP2']
        G8_D_str_2              = ['P2',                                                        'P2']
        G9_D_str_2              = ['MV1',                                                       'MV1']
        G10_V_str_2             = ['Ventil 1 (V1)',                                             'Valve 1 (V1)']
        G11_V_str_2             = ['Ventil 2 (V2)',                                             'Valve 2 (V2)']
        G12_V_str_2             = ['Ventil 3 (V3)',                                             'Valve 3 (V3)']
        G13_V_str_2             = ['Ventil 4 (V4)',                                             'Valve 4 (V4)']
        G14_V_str_2             = ['Ventil 5 (V5)',                                             'Valve 5 (V5)']
        G15_V_str_2             = ['Ventil 6 (V6)',                                             'Valve 6 (V6)']
        G16_V_str_2             = ['Ventil 7 (V7)',                                             'Valve 7 (V7)']
        G17_V_str_2             = ['Ventil 17 (V17)',                                           'Valve 17 (V17)']
        ## Einheit: ################################################################################################################################################################################################################################################################################                                                 
        E1_F_str                = ['ml/min',                                                    'ml/min']
        E2_D_str                = ['mbar',                                                      'mbar']
        E3_n_str                = ['%',                                                         '%']
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
        ## Übergeordnet:
        try: self.Anlage = self.config['nemo-Version']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} nemo-Version {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Anlage = 1
        ## Zum Start:
        try: self.init = self.config['start']['init']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.init = False

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Config-Fehler und Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Anlagen-Version:
        if not self.Anlage in [1, 2]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} nemo-Version - {self.Log_Pfad_conf_2[self.sprache]} [1, 2] - {self.Log_Pfad_conf_3[self.sprache]} 1')
            self.Anlage = 1
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
        self.layer_layout.setRowStretch(36, 1) 
        self.layer_layout.setColumnStretch(9, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)       
        self.layer_layout.setVerticalSpacing(1)
        #________________________________________
        ## Spalten Breite:
        if self.Anlage == 1:
            self.layer_layout.setColumnMinimumWidth(2, 100)
            self.layer_layout.setColumnMinimumWidth(3, 100)
            self.layer_layout.setColumnMinimumWidth(4, 100)
        elif self.Anlage == 2:
            self.layer_layout.setColumnMinimumWidth(1, 40)
            self.layer_layout.setColumnMinimumWidth(2, 40)
            self.layer_layout.setColumnMinimumWidth(4, 40)
            self.layer_layout.setColumnMinimumWidth(5, 40)
            self.layer_layout.setColumnMinimumWidth(7, 40)
            self.layer_layout.setColumnMinimumWidth(8, 40)
        #________________________________________
        ## Widgets:
        ### Anlagen-Differenz:
        if self.Anlage == 1:
            G1_F_str = G1_F_str_1
            G2_F_str = G2_F_str_1
            G3_F_str = G3_F_str_1
            G4_F_str = G4_F_str_1
            G6_D_str = G6_D_str_1
            G7_D_str = G7_D_str_1
            G7       = G7_D_str_1
        elif self.Anlage == 2:
            G1_F_str = G1_F_str_2
            G2_F_str = G2_F_str_2
            G3_F_str = G3_F_str_2
            G4_F_str = G4_F_str_2
            G6_D_str = G6_D_str_2
            G7_D_str = G7_D_str_2
            G7       = G8_D_str_2

        ### Label:
        #### Überschriften:
        self.La_name = QLabel(f'<b>{nemoGase}</b> ({self.nemo[self.sprache]} {self.Anlage})')
        self.labelÜ1 = QLabel(f'<b>{ü1_str[self.sprache]}:</b>')
        self.labelÜ2 = QLabel(f'<b>{ü2_str[self.sprache]}:</b>')
        self.labelÜ3 = QLabel(f'<b>{ü3_str[self.sprache]}:</b>')
        self.labelMon1 = QLabel(f'<i><b>{ü4_str[self.sprache]}:</b></i>')

        #### Flow:
        ##### Nemo-1 -> MFC24 | Nemo-2 -> MFC1
        self.FlabelSize_MFC24 = QLabel(f'{G1_F_str[self.sprache]} {B1_str[self.sprache] if self.Anlage == 1 else ""}: '.replace(' : ', ': '))
        self.FlabelValu_MFC24 = QLabel()
        self.FlabelUnit_MFC24 = QLabel(E1_F_str[self.sprache])

        self.FlabelValu_MFC24_S   = QLabel()
        self.FlabelUnit_MFC24_S   = QLabel(E1_F_str[self.sprache])
        self.FlabelValu_MFC24_FM  = QLabel()
        self.FlabelUnit_MFC24_FM  = QLabel(E1_F_str[self.sprache])

        ##### Nemo-1 -> MFC25 | Nemo-2 -> MFC2
        self.FlabelSize_MFC25 = QLabel(f'{G2_F_str[self.sprache]} {B1_str[self.sprache] if self.Anlage == 1 else ""}: '.replace(' : ', ': '))
        self.FlabelValu_MFC25 = QLabel()
        self.FlabelUnit_MFC25 = QLabel(E1_F_str[self.sprache])

        self.FlabelValu_MFC25_S   = QLabel()
        self.FlabelUnit_MFC25_S   = QLabel(E1_F_str[self.sprache])
        self.FlabelValu_MFC25_FM  = QLabel()
        self.FlabelUnit_MFC25_FM  = QLabel(E1_F_str[self.sprache])

        ##### Nemo-1 -> MFC26 | Nemo-2 -> MFC3
        self.FlabelSize_MFC26 = QLabel(f'{G3_F_str[self.sprache]} {B1_str[self.sprache] if self.Anlage == 1 else ""}: '.replace(' : ', ': '))
        self.FlabelValu_MFC26 = QLabel()
        self.FlabelUnit_MFC26 = QLabel(E1_F_str[self.sprache])

        self.FlabelValu_MFC26_S   = QLabel()
        self.FlabelUnit_MFC26_S   = QLabel(E1_F_str[self.sprache])
        self.FlabelValu_MFC26_FM  = QLabel()
        self.FlabelUnit_MFC26_FM  = QLabel(E1_F_str[self.sprache])

        ##### Nemo-1 -> MFC27 | Nemo-2 -> MFC4
        self.FlabelSize_MFC27 = QLabel(f'{G4_F_str[self.sprache]} {B1_str[self.sprache] if self.Anlage == 1 else ""}: '.replace(' : ', ': '))
        self.FlabelValu_MFC27 = QLabel()
        self.FlabelUnit_MFC27 = QLabel(E1_F_str[self.sprache])

        self.FlabelValu_MFC27_S   = QLabel()
        self.FlabelUnit_MFC27_S   = QLabel(E1_F_str[self.sprache])
        self.FlabelValu_MFC27_FM  = QLabel()
        self.FlabelUnit_MFC27_FM  = QLabel(E1_F_str[self.sprache])

        ##### Tabelle:
        self.TabÜ1 = QLabel(f'<i>{B9_str[self.sprache]}</i>')
        self.TabÜ2 = QLabel(f'<i>{B8_str[self.sprache]}</i>')
        self.TabÜ3 = QLabel(f'<i>{B10_str[self.sprache]}</i>')

        #### Drücke
        self.DlabelSize_DM21 = QLabel(f'{G5_D_str_1[self.sprache]} {B2_str[self.sprache]}: ')
        self.DlabelValu_DM21 = QLabel()
        self.DlabelUnit_DM21 = QLabel(E2_D_str[self.sprache])

        self.DlabelSize_PP21 = QLabel(f'{G6_D_str[self.sprache]} {B2_str[self.sprache]}: ')
        self.DlabelValu_PP21 = QLabel()
        self.DlabelUnit_PP21 = QLabel(E2_D_str[self.sprache])

        self.DlabelSize_PP22 = QLabel(f'{G7_D_str[self.sprache]} {B2_str[self.sprache]}: ')
        self.DlabelValu_PP22 = QLabel()
        self.DlabelUnit_PP22 = QLabel(E2_D_str[self.sprache])

        self.DlabelSize_P2   = QLabel(f'{G7[self.sprache]} {B5_str[self.sprache]}: ')
        self.DlabelValu_P2   = QLabel()
        self.DlabelUnit_P2   = QLabel(E2_D_str[self.sprache])

        self.DlabelSize_MV1_I = QLabel(f'{G9_D_str_2[self.sprache]} {B2_str[self.sprache]} {B9_str[self.sprache]}: ')
        self.DlabelValu_MV1_I = QLabel()
        self.DlabelUnit_MV1_I = QLabel(E2_D_str[self.sprache])

        self.DlabelSize_MV1_S = QLabel(f'{G9_D_str_2[self.sprache]} {B2_str[self.sprache]} {B8_str[self.sprache]}: ')
        self.DlabelValu_MV1_S = QLabel()
        self.DlabelUnit_MV1_S = QLabel(E2_D_str[self.sprache])

        #### Pumpen Status:
        self.DSlabelSize_PP21 = QLabel(f'{G6_D_str[self.sprache]} {B3_str[self.sprache]}: ')
        self.DSlabelValu_PP21 = QLabel()

        self.DSlabelSize_PP22 = QLabel(f'{G7_D_str[self.sprache]} {B3_str[self.sprache]}: ')
        self.DSlabelValu_PP22 = QLabel()

        #### Pumpen Drehzahl:
        self.DIlabelSize_PP22 = QLabel(f'{G7[self.sprache]} {B4_str[self.sprache]}: ')
        self.DIlabelValu_PP22 = QLabel()
        self.DIlabelUnit_PP22 = QLabel(E3_n_str[self.sprache])

        #### Ventil-Einstellung:
        self.DVlabelSize_MV1_VS = QLabel(f'{G9_D_str_2[self.sprache]} {B6_str[self.sprache]}: ')
        self.DVlabelValu_MV1_VS = QLabel()
        self.DVlabelUnit_MV1_VS = QLabel('')

        self.DVlabelSize_MV1_SG = QLabel(f'{G9_D_str_2[self.sprache]} {B7_str[self.sprache]}: ')
        self.DVlabelValu_MV1_SG = QLabel()
        self.DVlabelUnit_MV1_SG = QLabel('')

        #### Andere Status-Werte:
        self.FSlabelSize_MFC24 = QLabel(f'{G1_F_str[self.sprache]} {B3_str[self.sprache]}: ')
        self.FSlabelValu_MFC24 = QLabel()

        self.FSlabelSize_MFC25 = QLabel(f'{G2_F_str[self.sprache]} {B3_str[self.sprache]}: ')
        self.FSlabelValu_MFC25 = QLabel()

        self.FSlabelSize_MFC26 = QLabel(f'{G3_F_str[self.sprache]} {B3_str[self.sprache]}: ')
        self.FSlabelValu_MFC26 = QLabel()

        self.FSlabelSize_MFC27 = QLabel(f'{G4_F_str[self.sprache]} {B3_str[self.sprache]}: ')
        self.FSlabelValu_MFC27 = QLabel()

        self.DSlabelSize_MV1 = QLabel(f'{G9_D_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.DSlabelValu_MV1 = QLabel()

        self.VSlabelSize_V1 = QLabel(f'{G10_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V1 = QLabel()

        self.VSlabelSize_V2 = QLabel(f'{G11_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V2 = QLabel()

        self.VSlabelSize_V3 = QLabel(f'{G12_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V3 = QLabel()

        self.VSlabelSize_V4 = QLabel(f'{G13_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V4 = QLabel()

        self.VSlabelSize_V5 = QLabel(f'{G14_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V5 = QLabel()

        self.VSlabelSize_V6 = QLabel(f'{G15_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V6 = QLabel()

        self.VSlabelSize_V7 = QLabel(f'{G16_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V7 = QLabel()

        self.VSlabelSize_V17 = QLabel(f'{G17_V_str_2[self.sprache]} {B3_str[self.sprache]}: ')
        self.VSlabelValu_V17 = QLabel()

        #________________________________________
        ## Platzierung der einzelnen Widgets im Layout:
        if self.Anlage == 1:    
            pos = 1
            CS  = 5
        elif self.Anlage == 2:  
            pos = 3 
            CS = 9
        self.layer_layout.addWidget(self.La_name,                   0,     0, 1, CS)  
        self.layer_layout.addWidget(self.FlabelSize_MFC24,          pos+1, 0)                          # Reihe, Spalte, Ausrichtung
        self.layer_layout.addWidget(self.FlabelValu_MFC24,          pos+1, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC24,          pos+1, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.FlabelSize_MFC25,          pos+2, 0)                          
        self.layer_layout.addWidget(self.FlabelValu_MFC25,          pos+2, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC25,          pos+2, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.FlabelSize_MFC26,          pos+3, 0)                          
        self.layer_layout.addWidget(self.FlabelValu_MFC26,          pos+3, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC26,          pos+3, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.FlabelSize_MFC27,          pos+4, 0)                          
        self.layer_layout.addWidget(self.FlabelValu_MFC27,          pos+4, 1)
        self.layer_layout.addWidget(self.FlabelUnit_MFC27,          pos+4, 2, alignment=Qt.AlignLeft) 
        if self.Anlage == 1:
            self.layer_layout.addWidget(self.labelÜ1,               pos,   0, 1, CS)
        elif self.Anlage == 2: 
            self.layer_layout.addWidget(self.labelMon1,             1,     0, 1, CS)
            self.layer_layout.addWidget(self.labelÜ1,               pos-1, 0, 1, CS)
            self.layer_layout.addWidget(self.TabÜ1,                 pos,   1, 1, 2)
            self.layer_layout.addWidget(self.TabÜ2,                 pos,   4, 1, 2)
            self.layer_layout.addWidget(self.TabÜ3,                 pos,   7, 1, 2)
            self.Leerspalte(3, 4, 4)
            self.layer_layout.addWidget(self.FlabelValu_MFC24_S,    pos+1, 4)
            self.layer_layout.addWidget(self.FlabelUnit_MFC24_S,    pos+1, 5, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.FlabelValu_MFC25_S,    pos+2, 4)
            self.layer_layout.addWidget(self.FlabelUnit_MFC25_S,    pos+2, 5, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.FlabelValu_MFC26_S,    pos+3, 4)
            self.layer_layout.addWidget(self.FlabelUnit_MFC26_S,    pos+3, 5, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.FlabelValu_MFC27_S,    pos+4, 4)
            self.layer_layout.addWidget(self.FlabelUnit_MFC27_S,    pos+4, 5, alignment=Qt.AlignLeft)
            self.Leerspalte(6, 4, 4)
            self.layer_layout.addWidget(self.FlabelValu_MFC24_FM,   pos+1, 7)
            self.layer_layout.addWidget(self.FlabelUnit_MFC24_FM,   pos+1, 8, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.FlabelValu_MFC25_FM,   pos+2, 7)
            self.layer_layout.addWidget(self.FlabelUnit_MFC25_FM,   pos+2, 8, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.FlabelValu_MFC26_FM,   pos+3, 7)
            self.layer_layout.addWidget(self.FlabelUnit_MFC26_FM,   pos+3, 8, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.FlabelValu_MFC27_FM,   pos+4, 7)
            self.layer_layout.addWidget(self.FlabelUnit_MFC27_FM,   pos+4, 8, alignment=Qt.AlignLeft)
        self.Leerzeile(pos+5, AnzColum = 5 if self.Anlage == 1 else (9 if self.Anlage == 2 else -1)) 

        if   self.Anlage == 1: pos = 7
        elif self.Anlage == 2: pos = 9
        self.layer_layout.addWidget(self.labelÜ2,               pos,   0, 1, CS) 
        if self.Anlage == 1:
            self.layer_layout.addWidget(self.DlabelSize_DM21,   pos+1, 0)
            self.layer_layout.addWidget(self.DlabelValu_DM21,   pos+1, 1)
            self.layer_layout.addWidget(self.DlabelUnit_DM21,   pos+1, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.DlabelSize_PP21,       pos+2, 0)
        self.layer_layout.addWidget(self.DlabelValu_PP21,       pos+2, 1)
        self.layer_layout.addWidget(self.DlabelUnit_PP21,       pos+2, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.DlabelSize_PP22,       pos+3, 0)
        self.layer_layout.addWidget(self.DlabelValu_PP22,       pos+3, 1)
        self.layer_layout.addWidget(self.DlabelUnit_PP22,       pos+3, 2, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.DIlabelSize_PP22,      pos+4, 0)
        self.layer_layout.addWidget(self.DIlabelValu_PP22,      pos+4, 1)
        self.layer_layout.addWidget(self.DIlabelUnit_PP22,      pos+4, 2, alignment=Qt.AlignLeft)
        if self.Anlage == 2: 
            self.layer_layout.addWidget(self.DlabelSize_P2,     pos+5, 0)
            self.layer_layout.addWidget(self.DlabelValu_P2,     pos+5, 1)
            self.layer_layout.addWidget(self.DlabelUnit_P2,     pos+5, 2, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.DlabelSize_MV1_I,  pos+6, 0)
            self.layer_layout.addWidget(self.DlabelValu_MV1_I,  pos+6, 1)
            self.layer_layout.addWidget(self.DlabelUnit_MV1_I,  pos+6, 2, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.DlabelSize_MV1_S,  pos+7, 0)
            self.layer_layout.addWidget(self.DlabelValu_MV1_S,  pos+7, 1)
            self.layer_layout.addWidget(self.DlabelUnit_MV1_S,  pos+7, 2, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.DVlabelSize_MV1_VS,pos+8, 0)
            self.layer_layout.addWidget(self.DVlabelValu_MV1_VS,pos+8, 1)
            self.layer_layout.addWidget(self.DVlabelUnit_MV1_VS,pos+8, 2, alignment=Qt.AlignLeft)
            self.layer_layout.addWidget(self.DVlabelSize_MV1_SG,pos+9, 0)
            self.layer_layout.addWidget(self.DVlabelValu_MV1_SG,pos+9, 1)
            self.layer_layout.addWidget(self.DVlabelUnit_MV1_SG,pos+9, 2, alignment=Qt.AlignLeft)
        if   self.Anlage == 1: posLZ = pos+5
        elif self.Anlage == 2: posLZ = pos+10
        self.Leerzeile(posLZ, AnzColum = 5 if self.Anlage == 1 else (9 if self.Anlage == 2 else -1))
        
        if   self.Anlage == 1: pos = 13
        elif self.Anlage == 2: 
            pos = 20
            CS  = 8
        spa = 0
        self.layer_layout.addWidget(self.labelÜ3,                   pos,   spa   , 1 , CS)
        self.layer_layout.addWidget(self.DSlabelSize_PP21,          pos+1, spa)
        self.layer_layout.addWidget(self.DSlabelValu_PP21,          pos+1, spa+1 , 1 , CS) 
        self.layer_layout.addWidget(self.DSlabelSize_PP22,          pos+2, spa)
        self.layer_layout.addWidget(self.DSlabelValu_PP22,          pos+2, spa+1 , 1 , CS)
        if self.Anlage == 2:
            self.layer_layout.addWidget(self.FSlabelSize_MFC24,     pos+3, spa)
            self.layer_layout.addWidget(self.FSlabelValu_MFC24,     pos+3, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.FSlabelSize_MFC25,     pos+4, spa)
            self.layer_layout.addWidget(self.FSlabelValu_MFC25,     pos+4, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.FSlabelSize_MFC26,     pos+5, spa)
            self.layer_layout.addWidget(self.FSlabelValu_MFC26,     pos+5, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.FSlabelSize_MFC27,     pos+6, spa)
            self.layer_layout.addWidget(self.FSlabelValu_MFC27,     pos+6, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.DSlabelSize_MV1,       pos+7, spa)
            self.layer_layout.addWidget(self.DSlabelValu_MV1,       pos+7, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V1,        pos+8, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V1,        pos+8, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V2,        pos+9, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V2,        pos+9, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V3,        pos+10, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V3,        pos+10, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V4,        pos+11, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V4,        pos+11, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V5,        pos+12, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V5,        pos+12, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V6,        pos+13, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V6,        pos+13, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V7,        pos+14, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V7,        pos+14, spa+1 , 1 , CS)
            self.layer_layout.addWidget(self.VSlabelSize_V17,       pos+15, spa)
            self.layer_layout.addWidget(self.VSlabelValu_V17,       pos+15, spa+1 , 1 , CS)
        #________________________________________
        ## Border Sichtbar:
        if Frame_Anzeige:
            self.layer_widget.setStyleSheet("border: 1px solid black;")

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.labelDict      = {'MFC24': self.FlabelValu_MFC24,  'MFC24_S': self.FlabelValu_MFC24_S,  'MFC24_FM': self.FlabelValu_MFC24_FM, 'MFC24Status': self.FSlabelValu_MFC24,
                               'MFC25': self.FlabelValu_MFC25,  'MFC25_S': self.FlabelValu_MFC25_S,  'MFC25_FM': self.FlabelValu_MFC25_FM, 'MFC25Status': self.FSlabelValu_MFC25,
                               'MFC26': self.FlabelValu_MFC26,  'MFC26_S': self.FlabelValu_MFC26_S,  'MFC26_FM': self.FlabelValu_MFC26_FM, 'MFC26Status': self.FSlabelValu_MFC26,
                               'MFC27': self.FlabelValu_MFC27,  'MFC27_S': self.FlabelValu_MFC27_S,  'MFC27_FM': self.FlabelValu_MFC27_FM, 'MFC27Status': self.FSlabelValu_MFC27,
                               'MV1_I': self.DlabelValu_MV1_I,  'MV1_S': self.DlabelValu_MV1_S,      'MV1_VS': self.DVlabelValu_MV1_VS,    'MV1_SG': self.DVlabelValu_MV1_SG,      'MV1Status': self.DSlabelValu_MV1,
                               'DM21': self.DlabelValu_DM21, 
                               'PP21': self.DlabelValu_PP21,    'PP21Status': self.DSlabelValu_PP21,
                               'PP22': self.DlabelValu_PP22,    'PP22Status': self.DSlabelValu_PP22, 'PP22I': self.DIlabelValu_PP22,       'PP22mPtS': self.DlabelValu_P2,
                               'V1Status': self.VSlabelValu_V1, 'V2Status': self.VSlabelValu_V2,     'V3Status': self.VSlabelValu_V3,      'V4Status': self.VSlabelValu_V4,
                               'V5Status': self.VSlabelValu_V5, 'V6Status': self.VSlabelValu_V6,     'V7Status': self.VSlabelValu_V7,      'V17Status': self.VSlabelValu_V17,
                               }     # Label

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
            if not 'Status' in messung:
                self.labelDict[messung].setText(f'{value_dict[messung]}')

        # Status:
        ## Listen:
        status_P21_N1 = [self.Stat_1_str[self.sprache],     self.Stat_2_str[self.sprache],     '',                               '', '', '', '', '', self.Stat_3_str[self.sprache],     '',                                 '',                                 '',                             '',                                 '',                                 self.Stat_14_str[self.sprache],     self.Stat_15_str[self.sprache]]
        status_P21_N2 = [self.Stat_P1_1_str[self.sprache],  self.Stat_P1_2_str[self.sprache],  '',                               '', '', '', '', '', self.Stat_P1_9_str[self.sprache],  '',                                 '',                                 '',                             '',                                 '',                                 self.Stat_14_str[self.sprache],     self.Stat_15_str[self.sprache]]
        status_P22_N1 = [self.Stat_1_str[self.sprache],     self.Stat_2_str[self.sprache],     '',                               '', '', '', '', '', self.Stat_3_str[self.sprache],     self.Stat_4_str[self.sprache],      self.Stat_5_str[self.sprache],      self.Stat_6_str[self.sprache],  '',                                 '',                                 self.Stat_14_str[self.sprache],     self.Stat_15_str[self.sprache]]     # Lowest Bit zu Highest Bit
        status_P22_N2 = [self.Stat_P2_1_str[self.sprache],  self.Stat_P2_2_str[self.sprache],  self.Stat_P2_3_str[self.sprache], '', '', '', '', '', '',                                self.Stat_P2_10_str[self.sprache],  self.Stat_P2_11_str[self.sprache],  '',                             '',                                 '',                                 self.Stat_14_str[self.sprache],     self.Stat_15_str[self.sprache]]
        status_MFC    = [self.Stat_MFC_1_str[self.sprache], self.Stat_MFC_2_str[self.sprache], '',                               '', '', '', '', '', '',                                '',                                 '',                                 '',                             '',                                 '',                                 self.Stat_14_str[self.sprache],     self.Stat_15_str[self.sprache]]
        status_Ventil = [self.Stat_V_1_str[self.sprache],   self.Stat_V_2_str[self.sprache],   self.Stat_14_str[self.sprache],   '', '', '', '', '', self.Stat_V_9_str[self.sprache],   self.Stat_V_10_str[self.sprache],   self.Stat_V_11_str[self.sprache],   self.Stat_V_12_str[self.sprache], self.Stat_V_13_str[self.sprache], self.Stat_V_14_str[self.sprache],   self.Stat_V_15_str[self.sprache],   self.Stat_15_str[self.sprache]]

        # self.Stat_14_str[self.sprache] -> Schnittstellen-Problem
        # self.Stat_15_str[self.sprache] -> Test-Modus

        if self.Anlage == 1: 
            status_P21 = status_P21_N1
            status_P22 = status_P22_N1
        elif self.Anlage == 2: 
            status_P21 = status_P21_N2
            status_P22 = status_P22_N2

        ## P21:
        status_wert_P21 = value_dict['PP21Status']
        self.Status_Bund('PP21Status', status_P21, status_wert_P21)

        ## P22:
        status_wert_P22 = value_dict['PP22Status']
        self.Status_Bund('PP22Status', status_P22, status_wert_P22)
        
        if self.Anlage == 2:
            ## MFC/MV1: 
            status_wert_MFC24 = value_dict['MFC24Status']
            self.Status_Bund('MFC24Status', status_MFC, status_wert_MFC24)
            status_wert_MFC25 = value_dict['MFC25Status']
            self.Status_Bund('MFC25Status', status_MFC, status_wert_MFC25)
            status_wert_MFC26 = value_dict['MFC26Status']
            self.Status_Bund('MFC26Status', status_MFC, status_wert_MFC26)
            status_wert_MFC27 = value_dict['MFC27Status']
            self.Status_Bund('MFC27Status', status_MFC, status_wert_MFC27)
            status_wert_MV1 = value_dict['MV1Status']
            self.Status_Bund('MV1Status', status_MFC, status_wert_MV1)
            ## Ventile:
            status_wert_V1 = value_dict['V1Status']
            self.Status_Bund('V1Status', status_Ventil, status_wert_V1)
            status_wert_V2 = value_dict['V2Status']
            self.Status_Bund('V2Status', status_Ventil, status_wert_V2)
            status_wert_V3 = value_dict['V3Status']
            self.Status_Bund('V3Status', status_Ventil, status_wert_V3)
            status_wert_V4 = value_dict['V4Status']
            self.Status_Bund('V4Status', status_Ventil, status_wert_V4)
            status_wert_V5 = value_dict['V5Status']
            self.Status_Bund('V5Status', status_Ventil, status_wert_V5)
            status_wert_V6 = value_dict['V6Status']
            self.Status_Bund('V6Status', status_Ventil, status_wert_V6)
            status_wert_V7 = value_dict['V7Status']
            self.Status_Bund('V7Status', status_Ventil, status_wert_V7)
            status_wert_V17 = value_dict['V17Status']
            self.Status_Bund('V17Status', status_Ventil, status_wert_V17)
    
    def Status_Bund(self, status_Key, status_Liste, wert):
        ''' String für den Status des Gerätes zusammensetzen und in die GUI einsetzen.
        
        Args:
            status_Key (str):       Bezeichnung des Schlüssels für den Statuswert
            status_Liste (list):    Status-Bit-Liste mit den Strings für die Bits
            wert (int):             Status-Integer
        '''
        status_Bin = self.status_report_umwandlung(wert)
        label = ''
        l = len(status_Bin)
        for n in range(0, l):
            if status_Bin[n] == '1':
                if not status_Liste[n] == '':
                    label = label + f'{status_Liste[n]}, '
        if label == '': label = self.no_sta_str[self.sprache]
        else:           label = label[0:-2]
        self.labelDict[status_Key].setText(f'{label}')

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