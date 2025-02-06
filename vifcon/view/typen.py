# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Erstellung der Geräte-Typen:
1. Generator 
2. Antrieb

und der ersten Zeile mit dem Plot und den übergeordneten Knöpfen!

Weiteres:
- Anfügen des Cursors am Plot
- Erstellung von Pop-Up-Fenstern
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QPushButton,
    QMessageBox

)
from PyQt5.QtGui import (
    QIcon, 

)
from PyQt5.QtCore import (
    QSize,
    Qt,

)

## Algemein:
import logging

## Eigene:
from .base_classes import Splitter, PlotWidget, Widget_VBox

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)

class Cursor:
    def Add_Widget(self, Zeile):
        ''' Fügt das Text-Widget, mit verbundener Funktion an!
        Args:
            Zeile (int):    Zeilennummer
        '''
        self.achs_werte = QLabel(text=" x: 0 \nyL: 0\nyR: 0")
        self.controll_layout.addWidget(self.achs_werte, Zeile, 0, Qt.AlignBottom)                        
        self.plot.graph.scene().sigMouseMoved.connect(self.onMouseMoved)

    def onMouseMoved(self, evt):
        ''' Cursor-Anzeige:
        Grundlegende Idee von: https://stackoverflow.com/questions/65323578/how-to-show-cursor-coordinate-in-pyqtgraph-embedded-in-pyqt5
        '''
        if self.plot.achse_1.vb.mapSceneToView(evt):
            point_yLx = self.plot.achse_1.vb.mapSceneToView(evt)
            point_yR = self.plot.achse_2.mapSceneToView(evt)
            self.achs_werte.setText(f' x: {round(point_yLx.x(),2)} \nyL: {round(point_yLx.y(),2)} \nyR: {round(point_yR.y(),2)}')


class PopUpWindow:
    def Message(self, Zeile, art, width = 400):
        ''' Erstellt ein Pop-Up-Fenster mit Okay zum Schließen des Fensters.
        Args:
            Zeile (str):        Zu sehende Nachricht.
            art (int):          Art der Nachricht und Icons für die Boxn - 1: "Question", 2 : "Information", 3 : "Warning", 4 : 'Critical'
            width (int):        Breite des Fensters
            
        Quellen:
            https://stackoverflow.com/questions/49266964/how-to-make-qmessagebox-non-modal          (setModal)
            https://stackoverflow.com/questions/42248147/qmessagebox-seticon-doesnt-set-the-icon    (Icon)
            https://stackoverflow.com/questions/37668820/how-can-i-resize-qmessagebox               (MessageBox Size)
        '''
        artStr_dict     = {1: self.PopUp_1[self.sprache], 2 : self.PopUp_2[self.sprache], 3 : self.PopUp_3[self.sprache], 4 : self.PopUp_4[self.sprache]}
        artIcon_dict    = {1 : QMessageBox.Question, 2 : QMessageBox.Information, 3 : QMessageBox.Warning, 4 : QMessageBox.Critical}
        
        mess = QMessageBox(self.tab)  
        mess.setIcon(artIcon_dict[art])
        mess.setWindowTitle(artStr_dict[art])
        breite = '{min-width: ' + str(width) + 'px;}'
        mess.setStyleSheet(f"QLabel{breite}")
        mess.setText(Zeile)
        mess.setStandardButtons(QMessageBox.Ok)
        mess.setModal(False)
        mess.show()


class Generator(QWidget, Cursor, PopUpWindow):
    ''' Splitter-GUI für Generator mit Knöpfen und Plot in der ersten Zeile. '''
    def __init__(self, start_zeit, tab_splitter_widget, add_Ablauf_function, stopp_all_function, menu_dict, legend_ops, Faktoren, sprache, color_On, parent=None):
        """Generator Widget für Generator und Controller Geräte.

        Args:
            start_zeit (time):                  Zeitpunkt an dem die Messung gestartet hat
            tab_splitter_widget (QSplitter):    Tab an den dieser Splitter angehangen werden soll!  
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei. 
            stopp_all_function (Funktion):      Funktion um alle Achsen zu stoppen.
            menu_dict (dict):                   Menü Bar Elemente im Dictionary
            legend_ops (dict):                  Optionen für die Legende aus der Config-Datei
            Faktoren (dict):                    Skalierungsfaktoren für den Plot
            sprache (int):                      Sprache der GUI (Listenplatz)
            color_On (bool):                    Einstellung ob die Widget-Werte in Farbe oder Schwarz sind
        """
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        self.start_zeit                 = start_zeit
        self.tab                        = tab_splitter_widget
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.stopp_all_function         = stopp_all_function
        self.legend_ops                 = legend_ops
        self.Faktor                     = Faktoren
        self.sprache                    = sprache
        self.color_On                   = color_On

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Ablauf: ##################################################################################################################################################################################################################################################################################
        self.Text_10_str        = ['Knopf zum ausschalten aller Generatoren und Regler betätigt!',                                                          'Button pressed to switch off all generators and controllers!']
        ## Speichere Bilder: ########################################################################################################################################################################################################################################################################
        self.sichere_Bild_1_str = ['legende_Achse_Links',                                                                                                   'legend_axis_left']
        self.sichere_Bild_2_str = ['legende_Achse_Rechts',                                                                                                  'legend_axis_right']
        ## GUI: #####################################################################################################################################################################################################################################################################################
        self.Eintrag_Achse      = ['Keine Einträge!',                                                                                                       'No entries!']
        autoR_str               = ["Auto Achse",                                                                                                            "Auto Range"]
        action_ar_str           = ['Passe Achsen an',                                                                                                       'Adjust axes']
        Typ                     = ['Generatoren und Regler',                                                                                                'Generators and Controllers']
        sehe_device             = ['s.G.',                                                                                                                  's.d.']
        ## Pop-Up: ##################################################################################################################################################################################################################################################################################
        self.PopUp_1            = ['Frage',                                                                                                                 'Question']
        self.PopUp_2            = ['Information',                                                                                                           'Information']
        self.PopUp_3            = ['Warnung',                                                                                                               'Warning']
        self.PopUp_4            = ['Kritisch',                                                                                                              'Critical']           
        ## Logging: #################################################################################################################################################################################################################################################################################
        self.Log_Text_185_str_1 = ['Skalierungsfaktor für Größe',                                                                                           'Scaling factor for size']
        self.Log_Text_185_str_2 = ['auf Null gesetzt, keine Anzeige im Plot.',                                                                              'set to zero, not displayed in plot.']

        #---------------------------------------------------------
        # Konfigurationskontrolle und Konfigurationsvariablen:
        #---------------------------------------------------------
        ''' Die Kontrolle beinhaltet folgendes:
        1. Kontrolle des Schlüssels mit Default-Vergabe!
        2. Kontrolle der Variable wegen dem Inhalt mit Default-Vergabe!
        '''
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Einstellung für Log:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                                      'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                         'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                                                                                               'The following types are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                              'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',                                                                    'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                                                                                  '; Set to default:']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                          'Reason for error:']
        self.Log_Pfad_conf_7    = ['Bitte vor Nutzung Korrigieren und Config Neu Einlesen!',                                                                'Please correct and re-read config before use!']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                                  'Incorrect input:']
        
        ### Legenden Position:
        try: self.legend_pos         = self.legend_ops['legend_pos'].upper()
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|generator|legend_pos ({Typ[self.sprache]}) {self.Log_Pfad_conf_5[self.sprache]} SIDE')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            self.legend_pos = 'SIDE'
        if not self.legend_pos in ['IN', 'OUT', 'SIDE']:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} legend_pos ({Typ[self.sprache]}) - {self.Log_Pfad_conf_2[self.sprache]} [IN, OUT, SIDE] - {self.Log_Pfad_conf_3[self.sprache]} SIDE - {self.Log_Pfad_conf_8[self.sprache]} {self.legend_pos}')
            self.legend_pos = 'SIDE'
        ### Legenden Seite:
        try: self.Side_Legend_position = self.legend_ops['side'].upper()
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|generator|side ({Typ[self.sprache]}) {self.Log_Pfad_conf_5[self.sprache]} RL')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            self.Side_Legend_position = 'RL'
        if not self.Side_Legend_position in ['L', 'R', 'RL']:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} side ({Typ[self.sprache]}) - {self.Log_Pfad_conf_2[self.sprache]} [L, R, RL] - {self.Log_Pfad_conf_3[self.sprache]} RL - {self.Log_Pfad_conf_8[self.sprache]} {self.Side_Legend_position}')
            self.Side_Legend_position = 'RL'

        #---------------------------------------
        # Horizontaller Splitter:
        #---------------------------------------
        self.splitter_main = Splitter('V', True)
        self.tab.addWidget(self.splitter_main.splitter)

        #---------------------------------------
        # Übergeordnete Zeile erstellen:
        #---------------------------------------
        self.splitter_row_one = Splitter('H', True)
        self.splitter_main.splitter.addWidget(self.splitter_row_one.splitter)

        # Faktoren bestimmen für Label:
        label_dict = {'Temp': 'T [°C]', 'Current': 'I [A]', 'Voltage': 'U [V]', 'Op': 'P [%]', 'Pow': 'P [kW]', 'Freq': 'f [kHz]', 'Freq_2': 'f [Hz]', 'PIDG': f'x [{sehe_device[self.sprache]}]'}
        label_list = []
        for size in label_dict:
            if not self.Faktor[size] == 1:
                if not self.Faktor[size] == 0:
                    label_list.append(f'{label_dict[size]}x{self.Faktor[size]}')
                else:
                    label_list.append('0')
                    logging.warning(f'{self.Log_Text_185_str_1[self.sprache]} {size} {self.Log_Text_185_str_2[self.sprache]}')
            else:
                label_list.append(f'{label_dict[size]}')
        
        ## AutoScale Knopf definieren:
        self.btn_AS = QPushButton(QIcon("./vifcon/icons/AutoScale.png"), '')     # Icon

        ## All Check and All Uncheck definieren:
        if self.legend_pos == 'SIDE':
            if sprache == 0:    image_CL  = "./vifcon/icons/p_LCA.png"
            else:               image_CL  = "./vifcon/icons/p_LCA_En.png"
            if sprache == 0:    image_UCL = "./vifcon/icons/p_LUCA.png"
            else:               image_UCL = "./vifcon/icons/p_LUCA_En.png"

            self.btn_LCA  = QPushButton(QIcon(image_CL), '') 
            self.btn_LUCA = QPushButton(QIcon(image_UCL), '') 
        
        ## Graphen/Plot erstellen:
        if self.legend_pos == 'SIDE' and (self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'L'):
            self.legend_achsen_Links_widget = Widget_VBox()
            self.splitter_row_one.splitter.addWidget(self.legend_achsen_Links_widget.widget)

        Achse_y1_str = f'{label_list[0]} | {label_list[1]} | {label_list[2]} | {label_list[7]}'.replace(' | 0', '').replace('0 |','')
        if Achse_y1_str == '0':
            Achse_y1_str = self.Eintrag_Achse[self.sprache]
        Achse_y2_str = f'{label_list[3]} | {label_list[4]} | {label_list[5]} | {label_list[6]}'.replace(' | 0', '').replace('0 |','')
        if Achse_y2_str == '0':
            Achse_y2_str = self.Eintrag_Achse[self.sprache]
        self.plot = PlotWidget(menu_dict, self.btn_AS, self.legend_ops, self.sprache, 'Generator', 't [s]', Achse_y1_str, Achse_y2_str)            
        self.splitter_row_one.splitter.addWidget(self.plot.plot_widget)

        if self.legend_pos == 'SIDE' and (self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'R'):
            self.legend_achsen_Rechts_widget = Widget_VBox()
            self.splitter_row_one.splitter.addWidget(self.legend_achsen_Rechts_widget.widget)

        ## Knöpfe und anderes:
        self.controll_widget = QWidget()
        self.controll_layout = QGridLayout()
        self.controll_widget.setLayout(self.controll_layout)
        self.splitter_row_one.splitter.addWidget(self.controll_widget)

        ### Alle Generatoren und Controller Stoppen Knopf:
        icon_pfad = "./vifcon/icons/p_stopp_all.png" if sprache == 0 else  "./vifcon/icons/p_stopp_all_en.png" 
        self.btn_stopp_all = QPushButton(QIcon(icon_pfad), '')                          # Icon
        self.btn_stopp_all.setFlat(True)                                                # Rahmen weg
        self.btn_stopp_all.clicked.connect(self.stopp_all)                              # Verbindung zur Funktion
        self.btn_stopp_all.setIconSize(QSize(60, 60))                                   # Icon Size
        self.controll_layout.addWidget(self.btn_stopp_all, 0, 0)                        # Platzierung

        ### Auto-Scale:                 
        self.btn_AS.setFlat(True)                                                                                   # Rahmen weg
        self.btn_AS.setIconSize(QSize(60, 60))                                                                      # Icon Size
        self.btn_AS.setToolTip(f'{autoR_str[self.sprache]} {Typ[self.sprache]} - {action_ar_str[self.sprache]}')    # ToolTip
        self.controll_layout.addWidget(self.btn_AS, 1, 0)                                                           # Platzierung

        ### Legenden Setzen/nicht setzen:
        if self.legend_pos == 'SIDE':
            self.btn_LCA.setFlat(True) 
            self.btn_LCA.setIconSize(QSize(60, 60)) 
            self.controll_layout.addWidget(self.btn_LCA, 2, 0) 

            self.btn_LUCA.setFlat(True) 
            self.btn_LUCA.setIconSize(QSize(60, 60)) 
            self.controll_layout.addWidget(self.btn_LUCA, 3, 0) 

        ### Achsen Werte:
        self.Add_Widget(4)

        ## Anordnung-rechts-Grid Size:
        self.controll_layout.setRowStretch(1, 1) 
        self.controll_layout.setColumnStretch(4, 1)

        ## Spacing:
        self.controll_layout.setHorizontalSpacing(3)       
        self.controll_layout.setVerticalSpacing(1)

    ##########################################
    # Reaktion auf Buttons:
    ##########################################
    def stopp_all(self):
        ''' Funktion des Alle Generatoren Stoppen Knopf. '''
        self.add_Text_To_Ablauf_Datei(self.Text_10_str[self.sprache]) 
        self.stopp_all_function('Generator')
    
    ##########################################
    # Andere Funktionen:
    ##########################################
    def save_legend(self, Pfad):
        '''Speichere die Legende bei Side-Legend!'''
        if self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'L':
            pixmap_L = self.legend_achsen_Links_widget.widget.grab()
            pixmap_L.save(f"{Pfad.replace('.png', f'_{self.sichere_Bild_1_str[self.sprache]}.png')}")
        if self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'R':
            pixmap_R = self.legend_achsen_Rechts_widget.widget.grab()
            pixmap_R.save(f"{Pfad.replace('.png', f'_{self.sichere_Bild_2_str[self.sprache]}.png')}")

    
class Antrieb(QWidget, Cursor, PopUpWindow):
    ''' Splitter-GUI für Antriebe mit Knöpfen und Plot in der ersten Zeile. '''
    def __init__(self, start_zeit, tab_splitter_widget, add_Ablauf_function, stopp_all_function, synchro_function, menu_dict, legend_ops, Faktoren, sprache, color_On, parent=None):
        """ Generator Widget für Generator und Controller Geräte.

        Args:
            start_zeit (time):                  Zeitpunkt an dem die Messung gestartet hat
            tab_splitter_widget (QSplitter):    Tab an den dieser Splitter angehangen werden soll!  
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei. 
            stopp_all_function (Funktion):      Funktion um alle Achsen zu stoppen.
            synchro_function (Funktion):        Funktion um Achsen in absoluter Bewegung synchron laufen zu lassen.
            menu_dict (dict):                   Menü Bar Elemente im Dictionary
            legend_ops (dict):                  Optionen für die Legende aus der Config-Datei
            Faktoren (dict):                    Skalierungsfaktoren für den Plot
            sprache (int):                      Sprache der GUI (Listenplatz)
            color_On (bool):                    Einstellung ob die Widget-Werte in Farbe oder Schwarz sind
        """
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        self.start_zeit                 = start_zeit
        self.tab                        = tab_splitter_widget
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.stopp_all_function         = stopp_all_function
        self.synchro_function           = synchro_function
        self.legend_ops                 = legend_ops
        self.Faktor                     = Faktoren
        self.sprache                    = sprache
        self.color_On                   = color_On

        #--------------------------------------- 
        # Sprach-Einstellung:                                                               
        #---------------------------------------                                                                
        ## Ablaufdatei: ##################################################################################################################################################################################################################################################################################                                                             
        self.Text_11_str        = ['Knopf zum ausschalten aller Achsen/Antribe betätigt!',                                                                  'Button pressed to switch off all axes/drives!']
        self.Text_12_str        = ['Knopf zum synchronen Achsen/Antribe bewegen betätigt!',                                                                 'Button for synchronous axes/drives movement pressed!']
        ## Speichere Bilder: #############################################################################################################################################################################################################################################################################                                                                        
        self.sichere_Bild_1_str = ['legende_Achse_Links',                                                                                                   'legend_axis_left']
        self.sichere_Bild_2_str = ['legende_Achse_Rechts',                                                                                                  'legend_axis_right']
        ## GUI: ##########################################################################################################################################################################################################################################################################################                                                                     
        self.Eintrag_Achse      = ['Keine Einträge!',                                                                                                       'No entries!']
        autoR_str               = ["Auto Achse",                                                                                                            "Auto Range"]
        action_ar_str           = ['Passe Achsen an',                                                                                                       'Adjust axes']
        Typ                     = ['Antriebe',                                                                                                              'Drives']
        sehe_device             = ['s.G.',                                                                                                                  's.d.']
        ## Pop-Up: #######################################################################################################################################################################################################################################################################################
        self.PopUp_1            = ['Frage',                                                                                                                 'Question']
        self.PopUp_2            = ['Information',                                                                                                           'Information']
        self.PopUp_3            = ['Warnung',                                                                                                               'Warning']
        self.PopUp_4            = ['Kritisch',                                                                                                              'Critical']           
        ## Logging: ######################################################################################################################################################################################################################################################################################
        self.Log_Text_185_str_1 = ['Skalierungsfaktor für Größe',                                                                                           'Scaling factor for size']
        self.Log_Text_185_str_2 = ['auf Null gesetzt, keine Anzeige im Plot.',                                                                              'set to zero, not displayed in plot.']

        #---------------------------------------------------------
        # Konfigurationskontrolle und Konfigurationsvariablen:
        #---------------------------------------------------------
        ''' Die Kontrolle beinhaltet folgendes:
        1. Kontrolle des Schlüssels mit Default-Vergabe!
        2. Kontrolle der Variable wegen dem Inhalt mit Default-Vergabe!
        '''
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Einstellung für Log:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                                      'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                         'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                                                                                               'The following types are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                              'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',                                                                    'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                                                                                  '; Set to default:']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                          'Reason for error:']
        self.Log_Pfad_conf_7    = ['Bitte vor Nutzung Korrigieren und Config Neu Einlesen!',                                                                'Please correct and re-read config before use!']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                                  'Incorrect input:']
        
        ### Legenden Position:
        try: self.legend_pos         = self.legend_ops['legend_pos'].upper()
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|antrieb|legend_pos ({Typ[self.sprache]}) {self.Log_Pfad_conf_5[self.sprache]} SIDE')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            self.legend_pos = 'SIDE'
        if not self.legend_pos in ['IN', 'OUT', 'SIDE']:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} legend_pos ({Typ[self.sprache]}) - {self.Log_Pfad_conf_2[self.sprache]} [IN, OUT, SIDE] - {self.Log_Pfad_conf_3[self.sprache]} SIDE - {self.Log_Pfad_conf_8[self.sprache]} {self.legend_pos}')
            self.legend_pos = 'SIDE'
        ### Legenden Seite:
        try: self.Side_Legend_position = self.legend_ops['side'].upper()
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|antrieb|side ({Typ[self.sprache]}) {self.Log_Pfad_conf_5[self.sprache]} RL')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            self.Side_Legend_position = 'RL'
        if not self.Side_Legend_position in ['L', 'R', 'RL']:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} side ({Typ[self.sprache]}) - {self.Log_Pfad_conf_2[self.sprache]} [L, R, RL] - {self.Log_Pfad_conf_3[self.sprache]} RL - {self.Log_Pfad_conf_8[self.sprache]} {self.Side_Legend_position}')
            self.Side_Legend_position = 'RL'

        #---------------------------------------
        # Horizontaller Splitter:
        #---------------------------------------
        self.splitter_main = Splitter('V', True)
        self.tab.addWidget(self.splitter_main.splitter)

        #---------------------------------------
        # Übergeordnete Zeile erstellen:
        #---------------------------------------
        self.splitter_row_one = Splitter('H', True)
        self.splitter_main.splitter.addWidget(self.splitter_row_one.splitter)

        # Faktoren bestimmen für Label:
        label_dict = {'Pos': 's [mm]', 'Win': '\u03B1 [°]', 'Speed_1': 'v [mm/s]', 'Speed_2': 'v [mm/min]',  'WinSpeed': '\u03C9 [1/min]', 'PIDA': f'x [{sehe_device[self.sprache]}]'}         # https://pythonforundergradengineers.com/unicode-characters-in-python.html
        label_list = []
        for size in label_dict:
            if not self.Faktor[size] == 1:
                if not self.Faktor[size] == 0:
                    label_list.append(f'{label_dict[size]}x{self.Faktor[size]}')
                else:
                    label_list.append('0')
                    logging.warning(f'{self.Log_Text_185_str_1[self.sprache]} {size} {self.Log_Text_185_str_2[self.sprache]}')
            else:
                label_list.append(f'{label_dict[size]}')

        ## AutoScale Knopf definieren:
        self.btn_AS = QPushButton(QIcon("./vifcon/icons/AutoScale.png"), '')     # Icon

        ## All Check and All Uncheck definieren:
        if self.legend_pos == 'SIDE':
            if sprache == 0:    image_CL  = "./vifcon/icons/p_LCA.png"
            else:               image_CL  = "./vifcon/icons/p_LCA_En.png"
            if sprache == 0:    image_UCL = "./vifcon/icons/p_LUCA.png"
            else:               image_UCL = "./vifcon/icons/p_LUCA_En.png"

            self.btn_LCA  = QPushButton(QIcon(image_CL), '') 
            self.btn_LUCA = QPushButton(QIcon(image_UCL), '') 

        ## Graphen erstellen:
        if self.legend_pos == 'SIDE' and (self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'L'):
            self.legend_achsen_Links_widget = Widget_VBox()
            self.splitter_row_one.splitter.addWidget(self.legend_achsen_Links_widget.widget)

        Achse_y1_str = f'{label_list[0]} | {label_list[1]} | {label_list[5]}'.replace(' | 0', '').replace('0 |','')
        if Achse_y1_str == '0':
            Achse_y1_str = self.Eintrag_Achse[self.sprache]
        Achse_y2_str = f'{label_list[2]} | {label_list[3]} | {label_list[4]}'.replace(' | 0', '').replace('0 |','')
        if Achse_y2_str == '0':
            Achse_y2_str = self.Eintrag_Achse[self.sprache]
        self.plot = PlotWidget(menu_dict, self.btn_AS, self.legend_ops, self.sprache, 'Antrieb', 't [s]', Achse_y1_str, Achse_y2_str)          
        self.splitter_row_one.splitter.addWidget(self.plot.plot_widget)

        if self.legend_pos == 'SIDE' and (self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'R'):
            self.legend_achsen_Rechts_widget = Widget_VBox()
            self.splitter_row_one.splitter.addWidget(self.legend_achsen_Rechts_widget.widget)

        ## Knöpfe und anderes:
        self.controll_widget = QWidget()
        self.controll_layout = QGridLayout()
        self.controll_widget.setLayout(self.controll_layout)
        self.splitter_row_one.splitter.addWidget(self.controll_widget)

        ### Alle Achsen Stoppen Knopf:
        icon_pfad = "./vifcon/icons/p_stopp_all.png" if sprache == 0 else  "./vifcon/icons/p_stopp_all_en.png" 
        self.btn_stopp_all = QPushButton(QIcon(icon_pfad), '')                    # Icon
        self.btn_stopp_all.setFlat(True)                                          # Rahmen weg
        self.btn_stopp_all.clicked.connect(self.stopp_all)                        # Verbindung zur Funktion
        self.btn_stopp_all.setIconSize(QSize(60, 60))                             # Icon Size
        self.controll_layout.addWidget(self.btn_stopp_all, 0, 0)                  # Platzierung

        ### Achsen synchron fahren lassen:
        self.btn_syn = QPushButton(QIcon("./vifcon/icons/p_synchro.png"), '')     # Icon
        self.btn_syn.setFlat(True)                                                # Rahmen weg
        self.btn_syn.clicked.connect(self.synchro)                                # Verbindung zur Funktion
        self.btn_syn.setIconSize(QSize(60, 60))                                   # Icon Size
        self.controll_layout.addWidget(self.btn_syn, 1, 0)                        # Platzierung

        ### Auto-Scale:
        self.btn_AS.setFlat(True)                                                                                   # Rahmen weg
        self.btn_AS.setIconSize(QSize(60, 60))                                                                      # Icon Size
        self.btn_AS.setToolTip(f'{autoR_str[self.sprache]} {Typ[self.sprache]} - {action_ar_str[self.sprache]}')    # ToolTip
        self.controll_layout.addWidget(self.btn_AS, 2, 0)                                                           # Platzierung

        ### Legenden Setzen/nicht setzen:
        if self.legend_pos == 'SIDE':
            self.btn_LCA.setFlat(True) 
            self.btn_LCA.setIconSize(QSize(60, 60)) 
            self.controll_layout.addWidget(self.btn_LCA, 3, 0) 

            self.btn_LUCA.setFlat(True) 
            self.btn_LUCA.setIconSize(QSize(60, 60)) 
            self.controll_layout.addWidget(self.btn_LUCA, 4, 0) 

        ### Achsen Werte:
        self.Add_Widget(5)

        ## Grid Size:
        self.controll_layout.setRowStretch(3, 1) 
        self.controll_layout.setColumnStretch(5, 1)

        ## Spacing:
        self.controll_layout.setHorizontalSpacing(3)       
        self.controll_layout.setVerticalSpacing(1)
    
    ##########################################
    # Reaktion auf Buttons:
    ##########################################
    def stopp_all(self):
        ''' Funktion des Alle Achsen Stoppen Knopf. '''
        self.add_Text_To_Ablauf_Datei(self.Text_11_str[self.sprache]) 
        self.stopp_all_function('Antrieb')

    def synchro(self):
        ''' Funktion zum Starten der Synchron Bewegung '''
        self.add_Text_To_Ablauf_Datei(self.Text_12_str[self.sprache]) 
        self.synchro_function()
    
    ##########################################
    # Andere Funktionen:
    ##########################################
    def save_legend(self, Pfad):
        '''Speichere die Legende bei Side-Legend!
        
        Args:
            Pfad (str): Speicherpfad        
        '''
        if self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'L':
            pixmap_L = self.legend_achsen_Links_widget.widget.grab()
            pixmap_L.save(f"{Pfad.replace('.png', f'_{self.sichere_Bild_1_str[self.sprache]}.png')}")
        if self.Side_Legend_position == 'RL' or self.Side_Legend_position == 'R':
            pixmap_R = self.legend_achsen_Rechts_widget.widget.grab()
            pixmap_R.save(f"{Pfad.replace('.png', f'_{self.sichere_Bild_2_str[self.sprache]}.png')}") 

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''