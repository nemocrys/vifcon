# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Erstellung verschiedener Objekte:
1. Plot
2. Splitter (Vertikal, Horizontal)
3. VBox-Widget
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QSplitter,
    QFrame,
    QGridLayout,
    QAction,
    QVBoxLayout,

)
from PyQt5.QtGui import (
    QIcon, 

)
import pyqtgraph as pg
import pyqtgraph.exporters

## Algemein:
import logging

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class Splitter(QWidget):
    def __init__(self, orientation = 'V', collaps = True, parent=None):
        '''Erstellung eines Widgets mit einem  Splitter!
        
        Args:
            orientation (String):       V - vertikal, H - Horizontal
            collaps (bool):             Splitter einklappbar oder nicht
        '''
        super().__init__()

        splitter_style_sheet = (
            "QSplitter::handle{background: LightGrey; width: 5px; height: 5px;}"
        )
        if orientation == 'V':
            self.splitter = QSplitter(Qt.Vertical, frameShape=QFrame.StyledPanel)
        elif orientation == 'H':
            self.splitter = QSplitter(Qt.Horizontal, frameShape=QFrame.StyledPanel)
        self.splitter.setStyleSheet(splitter_style_sheet)
        self.splitter.setChildrenCollapsible(collaps)
    

class Widget_VBox(QWidget):
    def __init__(self, parent=None):
        '''Erstellung eine Widgets mit einem  QVBoxLayout!'''
        super().__init__()

        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.layout.setSpacing(0)


class PlotWidget(QWidget):
    def __init__(self, menu, btn_AS, legend_ops, sprache, typ, label_x, label_y1, label_y2 = '', parent=None):
        """Setup plot widget.
           siehe auch: https://stackoverflow.com/questions/71175650/pyqtgraph-add-items-from-seperate-viewbox-to-legend       

        Args:
            menu (dict):        Menü Bar Elemente im Dictionary
            legend_ops (dict):  Optionen für die Legende aus der Config-Datei
            sprache (int):      Sprache der GUI (Listenplatz)
            typ (str):          Typ der Geräte
            label_x (str):      x-Achsen Label
            label_y1 (str):     y-Label der linken y-Achse
            label_y2 (str):     y-Label der rechten y-Achse (Wenn nichts angegeben wird dies übersprungen!)
        """
        super().__init__()

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        self.sprache            = sprache
        self.button_action_2    = btn_AS

        self.toggle_Grid        = True
        fontsize                = 12                                   # Integer, Schriftgröße Achsen

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
        self.Log_Pfad_conf_1    = ['Konfigurationsfehler im Element:',                                                                              'Configuration error in element:']
        self.Log_Pfad_conf_2    = ['Möglich sind:',                                                                                                 'Possible values:']
        self.Log_Pfad_conf_2_1  = ['Möglich sind die Typen:',                                                                                       'The following types are possible:']
        self.Log_Pfad_conf_3    = ['Default wird eingesetzt:',                                                                                      'Default is used:']
        self.Log_Pfad_conf_4    = ['Fehler beim Auslesen der Config bei Konfiguration:',                                                            'Error reading config during configuration:']
        self.Log_Pfad_conf_5    = ['; Setze auf Default:',                                                                                          '; Set to default:']
        self.Log_Pfad_conf_6    = ['Fehlergrund:',                                                                                                  'Reason for error:']
        self.Log_Pfad_conf_7    = ['Bitte vor Nutzung Korrigieren und Config Neu Einlesen!',                                                        'Please correct and re-read config before use!']
        self.Log_Pfad_conf_8    = ['Fehlerhafte Eingabe:',                                                                                          'Incorrect input:']
        self.Log_Pfad_conf_8_1  = ['Fehlerhafte Typ:',                                                                                              'Incorrect type:']
        
        ### Legenden Position:
        try: self.legend_pos         = legend_ops['legend_pos'].upper()
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|{typ}|legend_pos {self.Log_Pfad_conf_5[self.sprache]} SIDE')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            self.legend_pos = 'SIDE'
        if not self.legend_pos in ['IN', 'OUT', 'SIDE']:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} legend_pos ({typ}) - {self.Log_Pfad_conf_2[self.sprache]} [IN, OUT, SIDE] - {self.Log_Pfad_conf_3[self.sprache]} SIDE - {self.Log_Pfad_conf_8[self.sprache]} {self.legend_pos}')
            self.legend_pos = 'SIDE'

        ### Legenden Spalten Anzahl:
        try: self.legend_anz = legend_ops['legend_anz']
        except Exception as e: 
            logger.warning(f'{self.Log_Pfad_conf_4[self.sprache]} legend|{typ}|legend_anz {self.Log_Pfad_conf_5[self.sprache]} 2')
            logger.exception(f'{self.Log_Pfad_conf_6[self.sprache]}')
            self.legend_anz = 2
        if not type(self.legend_anz) == int or not self.legend_anz >= 1:
            logger.warning(f'{self.Log_Pfad_conf_1[self.sprache]} legend_anz ({typ}) - {self.Log_Pfad_conf_2_1[self.sprache]} Integer (>=1) - {self.Log_Pfad_conf_3[self.sprache]} 2 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.legend_anz)}')
            self.legend_anz = 2

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Menü-Leiste:
        action_grid_str_G       = ['Generator - &Toggle Gitter An/Aus',  'Generator - &Toggle Grid On/Off']
        action_grid_str_A       = ['Antrieb - T&oggle Gitter An/Aus',    'Drive - T&oggle Grid On/Off']
        ## Save:
        self.sichere_Bild_3_str = ['legend',                'legend']

        #---------------------------------------
        # Graph - Grundgerüst:
        #---------------------------------------
        self.plot_widget = QWidget()
        self.plot_layout = QGridLayout() 
        self.plot_widget.setLayout(self.plot_layout)      

        if self.legend_pos == 'OUT':
            self.graph = pg.GraphicsLayoutWidget()          # Erstelle Layout für die Graphen
        else:
            self.graph = pg.PlotWidget()                    # Erstelle Graphen
        
        self.graph.setBackground('w')                       # Hintergrund des Plots weiß

        self.plot_layout.addWidget(self.graph)

        #---------------------------------------
        # Graph - Legende:
        #---------------------------------------
        ''' 
        Um die Legende unterhalb des Plots haben zu können, muss zunächst ein GraphicsLayoutWidget definiert werden 
        und dann ein LegendItem mit addItem in das Grid eingefügt werden! Die Legend behält die gewollten Eigenschaften!
        Je nach Config-Auswahl wird das eine oder das andere ausgeführt!
        '''
        if self.legend_pos == 'OUT':
            self.legend = pg.LegendItem(horSpacing=25, verSpacing=-5)                           # LegendItem erstellen
            self.graph.addItem(self.legend, row=1, col=0)                                       # anheften an GraphicsLayoutWidget
            self.achse_1 = self.graph.addPlot(row=0, col=0)                                     # Erstelle Graphen/Plot
        elif self.legend_pos == 'IN':
            self.legend = self.graph.addLegend()                                                # Füge Legende hinzu
            self.achse_1 = self.graph.plotItem                                                  # Erstelle Plot    
        else:
            self.achse_1 = self.graph.plotItem 

        if not self.legend_pos == 'SIDE':
            self.legend.setColumnCount(self.legend_anz)                                # Anzahl der Legendenlabels in einer Reihe

        #---------------------------------------
        # Achse 1:
        #---------------------------------------           
        self.achse_1.setLabel(axis = 'left', text= label_y1, **{'font-size': f'{fontsize}pt'})       # y-Achse Links
        self.achse_1.setLabel(axis = 'bottom', text= label_x, **{'font-size': f'{fontsize}pt'})      # x-Achse

        self.achse_1.showGrid(x=True, y=True)
        self.achse_1.enableAutoRange(axis="x")
        self.achse_1.enableAutoRange(axis="y")

        #---------------------------------------
        # Achse 2:
        #---------------------------------------
            # (Notiz: Funktionen hier näher ansehen!) 
            # Themengebiet Achse 1 und Achse 2 --> Quelle: https://stackoverflow.com/questions/71175650/pyqtgraph-add-items-from-seperate-viewbox-to-legend  
        if label_y2 != '':
            self.achse_2 = pg.ViewBox()
            self.achse_1.showAxis('right')                                                          # y-Achse Rechts
            self.achse_1.scene().addItem(self.achse_2)
            self.achse_1.getAxis('right').linkToView(self.achse_2)
            self.achse_2.setXLink(self.achse_1)
            right_color = 'red'
            self.achse_1.getAxis('right').setLabel(label_y2, **{'color': right_color, 'font-size': f'{fontsize}pt'})
            self.achse_1.getAxis('right').setPen(color=right_color, style=Qt.DashLine)

            self.achse_2.enableAutoRange(axis="x")
            self.achse_2.enableAutoRange(axis="y")

            def updateViews():
                self.achse_2.setGeometry(self.achse_1.vb.sceneBoundingRect())
                self.achse_2.linkedViewChanged(self.achse_1.vb, self.achse_2.XAxis)

            updateViews()
            self.achse_1.vb.sigResized.connect(updateViews)
    
        #---------------------------------------
        # Grid und AutoRange - Menüleiste:
        #---------------------------------------        
        ## Actions:
        action_grid_str = action_grid_str_A if typ == 'Antrieb' else action_grid_str_G
        self.button_action_1 = QAction(QIcon("./vifcon/icons/p_nichts.png"), f"{action_grid_str[self.sprache]}", self)
        self.button_action_1.triggered.connect(self.GridOnOff)
        self.button_action_1.setCheckable(True)

        self.button_action_2.clicked.connect(self.AutoRange)
        
        ## Anhaften:
        menu['Grid'].addAction(self.button_action_1)

    ##########################################
    # Reaktion auf Menüleiste:
    ##########################################
    def GridOnOff(self):
        ''' Ein- und Ausschalten des Grids'''
        if not self.toggle_Grid:
            self.toggle_Grid = True
            self.achse_1.showGrid(x=True, y=True)
            self.button_action_1.setIcon(QIcon("./vifcon/icons/p_nichts.png"))
        else:
            self.toggle_Grid = False
            self.achse_1.showGrid(x=False, y=False)
            self.button_action_1.setIcon(QIcon("./vifcon/icons/grid.png"))         
    
    def AutoRange(self):
        ''' Auslösen des Anpassen der Kurven und Aktivierung des Auto Scalings'''
        self.achse_1.autoRange()
        self.achse_2.autoRange()
        self.achse_1.enableAutoRange(axis="x")
        self.achse_2.enableAutoRange(axis="x")
        self.achse_1.enableAutoRange(axis="y")
        self.achse_2.enableAutoRange(axis="y")
        # Notiz:    Wenn in der Legende nur Kurven der Achse 2 ausgewählt sind, so wird die x-Achse nicht angepasst für die Achse 2
        #           Um die Anpassung manschmal hinzubekommen, muss Autorange betätigt werden!

    ##########################################
    # Speicher Plot:
    ##########################################
    def save_plot(self, Pfad):
        ''' Speichert den Plot (Quelle: https://pyqtgraph.readthedocs.io/en/latest/user_guide/exporting.html)

        Args:
            Pfad (str): Speicherpfad        
        '''
        exporter = pg.exporters.ImageExporter(self.achse_1)
        exporter.export(Pfad)
        if self.legend_pos == 'OUT':
            export = pg.exporters.ImageExporter(self.legend)
            export.export(f"{Pfad.replace('.png', f'_{self.sichere_Bild_3_str[self.sprache]}.png')}")

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''