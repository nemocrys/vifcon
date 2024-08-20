# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Hauptfenster der GUI:
- Erstellung des Central-Widgets
- Erstellung des Menüs
- Erstellung der Tabs
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtGui import (
    QIcon, 

)
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QScrollArea,
    QMessageBox,
    QAction,

)

## Algemein:
import logging

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    '''Hauptfenster von Vifcon '''

    def __init__(self, exit_function, sync_function, sync_end_function, RE_function, sprache, gamepad, parent=None):
        """Initialize main window.

        Args:
            exit_function (Funktion): Weitere Auswirkungen bei Beenden der Anwendung.
            sync_funktion (Funktion): Rezepte laufen Synchron
            RE_function (Funktion):   Funktion für das Einlesen aller Rezepte  
            sprache (int):            Sprache der GUI (Listenplatz)
            gamepad (bool):           Gamepad wird genutzt
        """
        super().__init__(parent)

        #--------------------------------------- 
        # Variablen:
        #--------------------------------------- 
        self.exit_function = exit_function
        self.device_action = {}
        self.sprache       = sprache

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Menü-Leiste:
        PGR_str             = ["&Menü",                                  "&Menu"] 
        P_str               = ["&Plot",                                  "&Plot"] 
        G_str               = ["&Geräte",                                "&Devices"] 
        R_str               = ["&Rezepte",                               "&Recipes"] 
        gitter_str          = ["&Gitter",                                "&Grid"]                               # & - Ermöglicht eine Tastenkombination Alt + Buchstabe (nach &)
        init_str            = ["&Initialisiere",                         "&Initialize"]
        limits_str          = ["&Lese Limits erneut",                    "Read &Limits again"]
        PID_Para_str        = ['Lese &VIFCON-PID-Parameter erneut',      'Reread &VIFCON-PID parameters']
        syn_rez_sta_str     = ["&Starte Synchron Modus",                 "&Start synchronously mode"]
        syn_rez_end_str     = ["&Beende Synchron Modus",                 "&Finish synchronous mode"]
        new_rez_aus_str     = ["&Alle Geräte neu Einlesen",              "Re-read &all devices"]
        ## Exit:
        self.exit_1_str     = ["Anwendung beenden",                      "Close application"]
        if gamepad:
            self.exit_2_str     = ["Soll die Anwendung geschlossen werden?\n\nDas Schließen der Anwendung kann durch die Nutzung von einer Schnittstelle für mehrere Geräte etwas Zeit in Anspruch nehmen, da die Threads abgeschlossen werden müssen!", 
                               "Should the application be closed?\n\nWhen using a multi-device interface, closing the application may take some time as the threads need to be completed!"] 
        else:
            self.exit_2_str     = ["Soll die Anwendung geschlossen werden?", "Should the application be closed?"] 
        ## Init:
        self.init_str       = ["initialisieren",                         "initialize"]  
        ## Limit:
        self.limit_str      = ["für",                                    "for"]  
        
        #--------------------------------------- 
        # Hauptfenster - GUI:
        #--------------------------------------- 
        self.setWindowTitle("VIFCON")                               # Name
        self.setWindowIcon(QIcon("./vifcon/icons/nemocrys.png"))    # Icon
        self.resize(1240, 900)                                      # Breite und Höhe
        self.move(300, 10)                                          # Koordinaten der oberen linken Ecke des Fensters (x, y)
        #self.setMinimumSize(200, 500)

        self.central_widget = QWidget()                             # Haupt-Widget
        self.setCentralWidget(self.central_widget)                  # Zentrales Widget festlegen
        self.main_layout = QVBoxLayout()                            # Layout des Haupt-Widgets
        self.central_widget.setLayout(self.main_layout)

        ## Tab-Bar:
        self.tab_widget = QTabWidget()                                              # Tab-Widget
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")    # Schriftfarbe und Schriftgröße der Tabs
        scroll_area = QScrollArea()                                                     
        scroll_area.setWidget(self.tab_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(1000)
        self.main_layout.addWidget(self.tab_widget)

        ## Menü-Leiste:
        menu                    = self.menuBar()
        ### Menü-Ebene 1:
        self.PGR_menu           = menu.addMenu(PGR_str[self.sprache])
        ### Menü-Ebene 2:
        self.P_menu             = self.PGR_menu.addMenu(P_str[self.sprache])
        self.G_menu             = self.PGR_menu.addMenu(G_str[self.sprache])
        self.R_menu             = self.PGR_menu.addMenu(R_str[self.sprache])
        ### Menü-Ebene 3:
        #### Plot:
        self.grid_menu          = self.P_menu.addMenu(gitter_str[self.sprache])                      
        #### Geräte:
        self.init_menu          = self.G_menu.addMenu(init_str[self.sprache])             
        self.limits_menu        = self.G_menu.addMenu(limits_str[self.sprache]) 
        self.PID_Para_menu      = self.G_menu.addMenu(PID_Para_str[self.sprache])
        #### Rezepte:
        ##### Action Synchro Rezept Start:
        button_action = QAction(syn_rez_sta_str[self.sprache], self)
        button_action.triggered.connect(sync_function)
        self.R_menu.addAction(button_action)
        ##### Action Synchro Rezept Ende:
        button_action_RF = QAction(syn_rez_end_str[self.sprache], self)
        button_action_RF.triggered.connect(sync_end_function)
        self.R_menu.addAction(button_action_RF)
        ##### Action Rezepte Neu Einlesen:
        button_action_RE = QAction(new_rez_aus_str[self.sprache], self)
        button_action_RE.triggered.connect(RE_function)
        self.R_menu.addAction(button_action_RE)

        self.menu_dict = {'Grid': self.grid_menu, 'Init': self.init_menu, 'Limit': self.limits_menu, 'VIFCON-PID': self.PID_Para_menu}      

    ##########################################
    # Funktionen:
    ##########################################
    def add_tab(self, tab_widget, tab_name):
        """ Fügt ein Tab an das main layout.

        Args:
            tab_widget (QWidget):   widget to-be added
            tab_name (str):         name of the tab
        """
        self.tab_widget.addTab(tab_widget, tab_name)

    def closeEvent(self, event):                                                                
        ''' Event bei Betätigung von Close (Bib.-Internes benehmen) '''
        reply = QMessageBox.question(self, self.exit_1_str[self.sprache], self.exit_2_str[self.sprache],
                                     QMessageBox.Yes | QMessageBox.No , QMessageBox.No)        
                        
        # Reaktion auf Antwort der Box:
        if reply == QMessageBox.Yes:
            event.accept()
            self.exit_function()
        else:
            event.ignore()

    #####################################
    # Menü:
    #####################################
    def add_menu(self, menu_str, name, function, config_init):
        '''
        Fügt ein Element an das Initialisierungsmenü. 

        Args:
            menu_str (str):        String zur Wahl des Menüs
            name (str):            Bezeichnung des Gerätes
            function (function):   Geräte-Initialisierungs-Funktion
            config_init (bool):    True - Initialisierung ist schon erfolgt, False - Initialisierung kann noch kommen
        '''
        if menu_str == 'Init':
            if config_init:
                icon = QIcon("./vifcon/icons/p_Init_Okay.png")
            else:
                icon = QIcon("./vifcon/icons/p_Init_nicht_Okay.png")
            
            button_action = QAction(icon, f"{name} {self.init_str[self.sprache]}", self)
        elif menu_str == 'Limit' or menu_str == 'VIFCON-PID':
            button_action = QAction(f"{self.limit_str[self.sprache]} {name}", self)
        button_action.triggered.connect(function)
        self.menu_dict[menu_str].addAction(button_action)
        if menu_str == 'Init':
            self.device_action.update({name:button_action})

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''