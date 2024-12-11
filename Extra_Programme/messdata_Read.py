# ++++++++++++++++++++++++++++
# Noch zu machen:
# ++++++++++++++++++++++++++++
'''
- Sprachen (bei beiden Versionen)
- Vergleichsmodus: Erneutes betätigen Löschen der Legenden-Widgets und der Kurven!

'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++

import os
import sys
from argparse import ArgumentParser
import math as m

import pyqtgraph as pg
import pyqtgraph.exporters
import matplotlib
import randomcolor 

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QLabel,
    QCheckBox,
    QLineEdit,
    
)
from PyQt5.QtCore import (
    QObject,
    Qt,

)
from PyQt5.QtGui import (
    QIcon, 

)

# ++++++++++++++++++++++++++++
# Klassen:
# ++++++++++++++++++++++++++++
class Splitter(QWidget):
    def __init__(self, orientation = 'V', collaps = True, parent=None):
        '''Erstellung eines Widgets mit einem  Splitter! (Aus VIFCON)

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
    def __init__(self, legend_ops, sprache, label_x, label_y1, label_y2 = '', parent=None):
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
        self.legend_pos         = legend_ops.upper()
        self.sprache            = sprache

        self.toggle_Grid        = True
        fontsize                = 12                                   # Integer, Schriftgröße Achsen
        self.widget_list        = []
        self.curve_dict         = {}
        self.kurven_side_legend = {}
        self.used_Color_list    = []
        self.widget_dict        = {}

        self.Vergleichsmodus    = False    
        self.label_left         = ''
        self.label_right        = '' 
        self.anzK               = 0       

        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 

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
            self.legend.setColumnCount(legend_ops['legend_anz'])                                # Anzahl der Legendenlabels in einer Reihe

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

    def update(self, label_titel, data, plot, legende, file):
        # Leere Plot:
        if not self.Vergleichsmodus:
            plot.achse_1.clear()                # https://stackoverflow.com/questions/71186683/pyqtgraph-completely-clear-plotwidget
            plot.achse_2.clear()
            self.kurven_side_legend = {}
            for widget in self.widget_list:
                widget.setParent(None)          # https://stackoverflow.com/questions/5899826/pyqt-how-to-remove-a-widget
            self.widget_list = []
            self.curve_dict = {}
            self.widget_dict = {}
            self.used_Color_list = []
        # Auto-Scale:
        plot.achse_1.autoRange()
        plot.achse_2.autoRange()
        plot.achse_1.enableAutoRange(axis="x")
        plot.achse_2.enableAutoRange(axis="x")
        plot.achse_1.enableAutoRange(axis="y")
        plot.achse_2.enableAutoRange(axis="y")
        # Einstellungen:
        fontsize            = 12
        right_color         = 'red'
        if not self.Vergleichsmodus:
            self.graph.setTitle(label_titel, color="black", size=f"{fontsize}pt")
            self.anzK = 0

        # Fraben:
        COLORS = [
            "green",
            "cyan",
            "magenta",
            "blue",
            "orange",
            "darkmagenta",
            "brown",
            "tomato",
            "lime",
            "olive",
            "navy",
            "peru",
            "grey",
            "black",
            "darkorange",
            "sienna",
            "gold",
            "yellowgreen",
            "skyblue",
            "mediumorchid",
            "deeppink",
            "purple",
            "darkred"
        ] # 23 Farben - https://matplotlib.org/stable/gallery/color/named_colors.html

        # Farben-Liste:
        if not matplotlib.colors.cnames['red'] in self.used_Color_list:   self.used_Color_list.append(matplotlib.colors.cnames['red'])
        if not matplotlib.colors.cnames['black'] in self.used_Color_list: self.used_Color_list.append(matplotlib.colors.cnames['black'])

        # Achsen-Beschriftung 1 und Mögliche anzeigbare Messgrößen:
        ## Leeren:
        if not self.Vergleichsmodus:
            self.label_left  = ''
            self.label_right = ''
        ## Definieren:
        #            Größe:                     [Möglichkeiten (list), Achsenlabel (string or list), Achse (string)]
        Achsen =    {'Temperatur':              [['Soll-Temperatur', 'Ist-Temperatur', 'Soll-Temperatur_PID-Modus', 'Ist-Temperatur_PID-Modus'],                                                'T',            'links'],
                     'Position':                [['Position', 'Position-sim', 'Position-real', 'Soll-Position','max.Pos.','min.Pos.', 'Ist-Position-sim', 'Ist-Position-real', 'Ist-Position'], 's',            'links'],
                     'Winkel':                  [['Ist-Winkel', 'Winkel'],                                                                                                                      '\u03B1',       'links'],
                     'Strom':                   [['Ist-Strom','Soll-Strom', 'Ist_Strom'],                                                                                                       'I',            'links'],
                     'Spannung':                [['Ist-Spannung', 'Soll-Spannung'],                                                                                                             'U',            'links'],
                     'Leistung':                [['Ist-Leistung','Soll-Leistung', 'Operating-point'],                                                                                           'P',            'rechts'],
                     'Geschwindigkeit':         [['Ist-Geschwindigkeit', 'Geschwindigkeit', 'Soll-Geschwindigkeit'],                                                                            ['v','\u03C9'], 'rechts'],
                     'Winkelgeschwindigkeit':   [['Ist-Winkelgeschwindigkeit', 'Soll-Winkelgeschwindigkeit'],                                                                                   '\u03C9',       'rechts'],
                     'Frequenz':                [['Ist-Frequenz'],                                                                                                                              'f',            'rechts'],
                     'PIDA':                    [['Soll-x_PID-Modus', 'Ist-x_PID-Modus', 'Soll-x_PID-Modus_A', 'Ist-x_PID-Modus_A'],                                                            'x',            'links'], 
                     'PIDG':                    [['Soll-x_PID-Modus_G', 'Ist-x_PID-Modus_G'],                                                                                                   'x',            'links'],
        } 
        Zusatz = {  'Soll':         'Soll',
                    'Ist':          'Ist',
                    'Ist-Sim':      'sim',
                    'Ist-Gerät':    'real',
                    'oG':           'max.',
                    'uG':           'min.',
        }  
        
        # Erstellung der Kurven und Achsen-Beschriftung 2:
        for n in data:
            ## x-Achsen-Werte:
            if n == 'time_rel':
                x_str = data[n][0]
                x = []
                for wert in x_str:
                    x.append(float(wert))
            ## y-Achsen: Label, Legende und Kurve:
            elif 'time' not in n:
                for size in Achsen:
                    ak_list = Achsen[size][0]
                    for element in ak_list:
                        if n == element:
                            ### Beschriftung finden:
                            ak_size     = size
                            size_Fo     = Achsen[size][1]
                            achse_pos   = Achsen[size][2] 
                            found = True
                            break
                        else:
                            found = False
                    if found: 
                        break
                    else:   
                        ak_size     = 'Unbekannt'
                        size_Fo     = '?'
                        achse_pos   = 'links'
                ### Zusatz-Beschriftung finden:
                for extra in Zusatz:
                    if Zusatz[extra] in n:
                        extra_label = extra
                        break
                    else:
                        extra_label = ''
                if extra_label == '': extra_label = 'Ist'
                ### Einheit bestimmen:
                unit = data[n][1]
                if size == 'Geschwindigkeit':
                    if unit == 'mm/min' or unit == 'mm/s':
                        size_Fo = size_Fo[0]
                    else:
                        size_Fo = size_Fo[1]
                elif size == 'PIDA':
                    unit    = 's.G.'
                    size_Fo = 'xA'
                elif size == 'PIDG':
                    unit    = 's.G.'
                    size_Fo = 'xG'
                if unit == 'DEG C':
                    unit = '°C'
                ### Zusammensetzen:
                label = f'{size_Fo} [{unit}] | '
                if achse_pos == 'links' and not label in self.label_left:        self.label_left += label
                elif achse_pos == 'rechts'and not label in self.label_right:     self.label_right += label
                ### Werte auslesen:
                y_str = data[n][0]
                y = []
                for wert in y_str:
                    try:    y.append(float(wert))
                    except: y.append(m.nan)
                ### Kurve erstellen:
                try: 
                    color = matplotlib.colors.cnames[COLORS[self.anzK]]
                    while 1: 
                        self.anzK += 1
                        if not color in self.used_Color_list:
                            self.used_Color_list.append(color)
                            break
                        color = matplotlib.colors.cnames[COLORS[self.anzK]]
                except:
                    while 1:
                        # Zufällige Farbe erzeugen, generieren und doppelte vermeiden:
                        farbe = randomcolor.RandomColor().generate()[0]
                        if not farbe in self.used_Color_list:
                            self.used_Color_list.append(farbe)
                            color = farbe
                            break
                pen_kurve = pg.mkPen(color, width=2)
                if achse_pos == 'links':
                    curve = plot.achse_1.plot(x, y, pen=pen_kurve, name='Test')
                    achse = 'a1'
                elif achse_pos == 'rechts':
                    curve = pg.PlotCurveItem(x, y, pen=pen_kurve, name='Test')
                    plot.achse_2.addItem(curve)
                    achse = 'a2'
                ### Dictionary für Kurven:
                self.curve_dict.update({curve: [label.replace(' | ', ''), x, y, achse]})
                ### Legende:
                if self.Vergleichsmodus:    extra = f'({label_titel})'
                else:                       extra = ''
                widget, side_checkbox = self.GUI_Legend_Side([f'{n} {extra}', f'{size_Fo}<sub>{extra_label}</sub>'], pen_kurve, achse)
                legende.layout.addWidget(widget)
                self.widget_list.append(widget)
                self.widget_dict.update({widget: [file, color, curve]})
                self.kurven_side_legend.update({side_checkbox: curve})
                self.anzK += 1
                
        # Achsen-Beschriftung 3
        self.y_Label_Left  = self.label_left[0:-2]
        self.y_Label_Right = self.label_right[0:-2]
        self.achse_1.setLabel(axis = 'left', text= self.y_Label_Left, **{'font-size': f'{fontsize}pt'}) 
        self.achse_1.getAxis('right').setLabel(self.y_Label_Right, **{'color': right_color, 'font-size': f'{fontsize}pt'})

        # Fehlende Punkte:
        # Legende Icons
        # verschiedene Linien-Typen
    
    def GUI_Legend_Side(self, text, check_pen, achse):
        style = {1: '\u2501', 2: '\u2501 \u2501', 3: '\u00B7 \u00B7 ' * 2, 4: '\u2501\u00B7' * 3, 5: '\u2501\u00B7\u00B7' * 2} # 1: Solid, 2: Dashed, 3: Dot, 4: Dash Dot, 5: Dash Dot Dot

        check_Widget = QWidget()
        check_Layout = QHBoxLayout()
        check_Widget.setLayout(check_Layout)
        # Checkbox:
        check_legend = QCheckBox()
        check_legend.clicked.connect(self.Side_Legend)
        check_legend.setChecked(True)
        check_legend.setToolTip(text[0])
        if achse == 'a2':
            check_legend.setStyleSheet("QCheckBox::indicator::unchecked { background-color : darkgray; image : url('./Messdaten_VIFCON/Icon/unchecked.png'); }\n"
                                       "QCheckBox::indicator::checked { background-color : red; image : url('./Messdaten_VIFCON/Icon/checked.png'); }\n"
                                       "QCheckBox::indicator{ border : 1px solid black;}\n")
        else:
            check_legend.setStyleSheet("QCheckBox::indicator::unchecked { background-color : lightgray; image : url('./Messdaten_VIFCON/Icon/unchecked.png'); }\n"
                                       "QCheckBox::indicator::checked { background-color : black; image : url('./Messdaten_VIFCON/Icon/checked2.png'); }\n"
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
        checkbox = self.sender()                        # Klasse muss von QWidget erben, damit sender() Funktioniert - Durch die Methode kann geschaut werden welche Checkbox betätigt wurde!
        kurve = self.kurven_side_legend[checkbox]
        if checkbox.isChecked():
            kurve.setVisible(True)
        else:
            kurve.setVisible(False)


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


class GUI(QMainWindow, Cursor):
    def __init__(self, sprache, messdata_files, ordner):
        super().__init__()

        # Variablen:
        self.sprache            = sprache
        self.messdata_files     = messdata_files
        self.bereits_geklicket  = []
        self.ordner             = ordner

        # Sprache Listen:
        GUI_Titel               = ['VIFCON-Messdaten Anzeige',                                              'VIFCON measurement data display']
        self.Language_VM_1      = ['Bitte nun Kurven bzw. Dateien wählen!',                                 'Please select curves or files now!']
        self.Language_VM_2      = ['Vergleichsmodus',                                                       'Comparison Mode']
        self.Language_VM_3      = ['Vergleichsmodus inaktiv!',                                              'Compare mode inactive!']
        self.Language_Knopf_1   = ['Plot Anpassen',                                                         'Adjust Plot']
        self.Language_Knopf_2   = ['Speicher Plot',                                                         'Save Plot']
        self.Language_Knopf_3   = ['Auto Scale',                                                            'Auto Scale']
        self.Language_Knopf_4   = ['Skalierung anpassen',                                                   'Adjust scaling']
        self.Language_AP_Lx     = ['x-Achse',                                                               'x-axis']
        self.Language_AP_Ly1    = ['y-Achse links',                                                         'y-axis left']
        self.Language_AP_Ly2    = ['y-Achse rechts',                                                        'y-axis right']
        self.Language_AP_LMin   = ['Minimum',                                                               'Minimum']
        self.Language_AP_LMax   = ['Maximum',                                                               'Maximum']
        self.Language_AP_LCB    = ['Aktiv',                                                                 'Active']
        self.Language_Label_1   = ['Inhalt Datei:',                                                         'File content:']
        self.Language_Label_2   = ['Skal. Faktoren:',                                                       'Scaling Factors:']
        self.Label_error_1      = ['Schon betätigt!',                                                       'Already activated!']
        self.Label_error_2      = ['Fehler: Leeres Feld!',                                                  'Error: Empty field!']
        self.Label_error_3      = ['Fehler: Kein Float!',                                                   'Error: No float!']
        self.Label_error_4      = ['x: Limit Fehler (min größer max)!',                                     'x: Limit error (min greater than max)!']
        self.Label_error_5      = ['y-Links: Limit Fehler (min größer max)!',                               'y-Links: Limit error (min greater than max)!']
        self.Label_error_6      = ['y-Rechts: Limit Fehler (min größer max)!',                              'y-Right: Limit error (min greater than max)!']
        self.Label_error_7      = ['Faktor konnte nicht in Float umgewandelt werden! Setze Faktor auf 1!',  'Factor could not be converted to float! Set factor to 1!']

        # Main Window:
        self.resize(1240, 900)                                                              # Breite und Höhe
        self.move(100, 10)                                                                  # Koordinaten der oberen linken Ecke des Fensters (x, y)                                                              # Fenster Maße
        self.setWindowTitle(GUI_Titel[self.sprache])                                        # Fenster Titel
        self.setWindowIcon(QIcon("./Icon/nemocrys.png"))                                    # Fenster Icon

        # Bereiche:
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        ## Bereich 1 - Knöpfe und Plot:
        self.Splitter_Main = Splitter('V', False)
        self.main_layout.addWidget(self.Splitter_Main.splitter)

        self.Bereich_Oben = QWidget()
        self.Bereich_Oben_Layout = QGridLayout()
        self.Bereich_Oben.setLayout(self.Bereich_Oben_Layout)
        self.Splitter_Main.splitter.addWidget(self.Bereich_Oben)

        self.Splitter_Oben = Splitter('H')
        self.Bereich_Oben_Layout.addWidget(self.Splitter_Oben.splitter)

        ### Knöpfe:
        self.Bereich_Links = QWidget()
        self.Bereich_Links_Layout = QGridLayout()
        self.Bereich_Links.setLayout(self.Bereich_Links_Layout)
        self.Splitter_Oben.splitter.addWidget(self.Bereich_Links)

        ### Plot-Bereich:
        self.Bereich_Rechts = QWidget()
        self.Bereich_Rechts_Layout = QVBoxLayout()
        self.Bereich_Rechts.setLayout(self.Bereich_Rechts_Layout)
        self.Splitter_Oben.splitter.addWidget(self.Bereich_Rechts)

        self.splitter_row_one = Splitter('H', True)
        self.Bereich_Rechts_Layout.addWidget(self.splitter_row_one.splitter)

        #### Legende:
        self.legend_achsen_Rechts_widget = Widget_VBox()
        self.splitter_row_one.splitter.addWidget(self.legend_achsen_Rechts_widget.widget)

        #### Plot:
        self.legend_ops = 'SIDE'
        self.plot = PlotWidget(self.legend_ops, self.sprache,'t [s]', ' ', ' ')            
        self.splitter_row_one.splitter.addWidget(self.plot.plot_widget)

        #### Cursor:
        self.controll_widget = QWidget()
        self.controll_layout = QGridLayout()
        self.controll_widget.setLayout(self.controll_layout)
        self.splitter_row_one.splitter.addWidget(self.controll_widget)

        self.Add_Widget(2)

        ## Bereich 2 - Plot und Kurven Anpassungen:
        self.Bereich_Unten = QWidget()
        self.Bereich_Unten_Layout = QGridLayout()
        self.Bereich_Unten.setLayout(self.Bereich_Unten_Layout)
        self.Splitter_Main.splitter.addWidget(self.Bereich_Unten)

        # Widgets:
        ## Knöpfe-Datein:
        ### Knopf Aussehen:
        self.default = 'QPushButton {background-color: #FDFDFD;}'   # Nicht betätigt
        self.aktiv   = 'QPushButton {background-color: yellow;}'    # Betätigt
        ### Anordnung und Erstellung:
        reihe  = 0
        spalte = 0
        self.knopf_Pfad = {}
        for file in self.messdata_files:
            knopf = QPushButton(file.replace('.csv', ''))
            knopf.setStyleSheet(self.default) 
            knopf.setFixedWidth(200)
            knopf.clicked.connect(self.Kurven_Anzeige)
            self.knopf_Pfad.update({knopf:f'{self.ordner}/{file}'})
            self.Bereich_Links_Layout.addWidget(knopf, reihe, spalte)
            reihe += 1
            if reihe == 10:
                spalte += 1
                reihe = 0

        ## Knöpfe-Bereichs-Auswahl im Plot:
        update = QPushButton(self.Language_Knopf_1[self.sprache])
        update.setFixedWidth(100)
        update.clicked.connect(self.Update_Kurven_Bereich)

        self.LE_minX = QLineEdit()
        self.LE_minX.setText('0')
        self.LE_maxX = QLineEdit()
        self.LE_maxX.setText('100')
        self.LE_minY1 = QLineEdit()
        self.LE_minY1.setText('0')
        self.LE_maxY1 = QLineEdit()
        self.LE_maxY1.setText('100')
        self.LE_minY2 = QLineEdit()
        self.LE_minY2.setText('0')
        self.LE_maxY2 = QLineEdit()
        self.LE_maxY2.setText('100')

        labelX            = QLabel(self.Language_AP_Lx[self.sprache])
        labelY1           = QLabel(self.Language_AP_Ly1[self.sprache])
        labelY2           = QLabel(self.Language_AP_Ly2[self.sprache])
        labelMin          = QLabel(self.Language_AP_LMin[self.sprache])
        labelMax          = QLabel(self.Language_AP_LMax[self.sprache])
        labelCB           = QLabel(self.Language_AP_LCB[self.sprache])
        self.labelError_1 = QLabel('')

        self.CBX = QCheckBox()
        self.CBX.setChecked(True)
        self.CBY1 = QCheckBox()
        self.CBY1.setChecked(True)
        self.CBY2 = QCheckBox()
        self.CBY2.setChecked(True)

        ### Befestigen:
        spalte = 27
        reihe  = 0
        self.Leerspalte(26, self.Bereich_Unten_Layout)
        self.Bereich_Unten_Layout.addWidget(update,                 reihe,      spalte) 
        self.Bereich_Unten_Layout.addWidget(labelMin,               reihe,      spalte+1)     # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung  (alignment=Qt.AlignLeft)
        self.Bereich_Unten_Layout.addWidget(labelMax,               reihe,      spalte+2) 
        self.Bereich_Unten_Layout.addWidget(labelCB,                reihe,      spalte+3) 
        self.Bereich_Unten_Layout.addWidget(labelX,                 reihe+1,    spalte) 
        self.Bereich_Unten_Layout.addWidget(self.LE_minX,           reihe+1,    spalte+1) 
        self.Bereich_Unten_Layout.addWidget(self.LE_maxX,           reihe+1,    spalte+2)
        self.Bereich_Unten_Layout.addWidget(self.CBX,               reihe+1,    spalte+3) 
        self.Bereich_Unten_Layout.addWidget(labelY1,                reihe+2,    spalte) 
        self.Bereich_Unten_Layout.addWidget(self.LE_minY1,          reihe+2,    spalte+1) 
        self.Bereich_Unten_Layout.addWidget(self.LE_maxY1,          reihe+2,    spalte+2) 
        self.Bereich_Unten_Layout.addWidget(self.CBY1,              reihe+2,    spalte+3) 
        self.Bereich_Unten_Layout.addWidget(labelY2,                reihe+3,    spalte) 
        self.Bereich_Unten_Layout.addWidget(self.LE_minY2,          reihe+3,    spalte+1) 
        self.Bereich_Unten_Layout.addWidget(self.LE_maxY2,          reihe+3,    spalte+2) 
        self.Bereich_Unten_Layout.addWidget(self.CBY2,              reihe+3,    spalte+3) 
        self.Bereich_Unten_Layout.addWidget(self.labelError_1,      reihe+4,    spalte,     1, 3)

        ## Save-Knopf:
        save = QPushButton(self.Language_Knopf_2[self.sprache])
        save.setFixedWidth(150)
        save.clicked.connect(self.Save_Kurven_Bereich)

        ## Auto Scale:
        AS = QPushButton(self.Language_Knopf_3[self.sprache])
        AS.setFixedWidth(150)
        AS.clicked.connect(self.Auto_Scale)

        ### Befestigen:
        row = 3
        self.Bereich_Unten_Layout.addWidget(save,           row,          0)
        self.Bereich_Unten_Layout.addWidget(AS,             row+1,        0)

        ## Check-Box:
        self.cb_Vergleich = QCheckBox(self.Language_VM_2[self.sprache])
        self.cb_Vergleich.clicked.connect(self.Vergleich_Modus)
        self.label_cb  = QLabel(self.Language_VM_3[self.sprache])

        ### Befestigen:
        colom = 3
        self.Bereich_Unten_Layout.addWidget(self.cb_Vergleich,           row,          colom, 1, 3)
        self.Bereich_Unten_Layout.addWidget(self.label_cb,               row+1,        colom, 1, 3)

        ## Skallierungsfaktoren:
        skal_Fak = QPushButton(self.Language_Knopf_4[self.sprache])
        skal_Fak.setFixedWidth(150)
        skal_Fak.clicked.connect(self.Pass_Kurven_An)

        self.Bereich_Unten_2 = QWidget()
        self.Bereich_Unten_Layout_2 = QGridLayout()
        self.Bereich_Unten_2.setLayout(self.Bereich_Unten_Layout_2)

        row = 0
        self.Bereich_Unten_Layout_2.addWidget(skal_Fak,                                            row,          0)
        self.Bereich_Unten_Layout_2.addWidget(QLabel(self.Language_Label_1[self.sprache]),         row+1,        0)
        self.Bereich_Unten_Layout_2.addWidget(QLabel(self.Language_Label_2[self.sprache]),         row+2,        0)

        size_list = ['T [°C]', 'P [%]', 'P [kW]', 'I [A]', 'U [V]', 'f [kHz]', 'f [Hz]', 'v [mm/s]', 'v [mm/min]', '\u03C9 [1/min]', 's [mm]', '\u03B1 [°]', 'xA [s.G.]', 'xG [s.G.]']
        self.size_dict = {}
        colom = 1
        for n in size_list:
            size = QLabel(n)
            LE   = QLineEdit()
            LE.setText('1')
            LE.setFixedWidth(80)
            LE.setEnabled(False)
            self.size_dict.update({n: [size, LE]})
            ### Befestigen:
            self.Bereich_Unten_Layout_2.addWidget(size,           row+1,          colom)
            self.Bereich_Unten_Layout_2.addWidget(LE,             row+2,          colom)
            if not n == size_list[-1]:
                self.Leerspalte(colom+1, self.Bereich_Unten_Layout_2, row+1, endRow=2)
                colom += 2
        
        self.Bereich_Unten_Layout.addWidget(self.Bereich_Unten_2, 0, 0, 3, len(size_list))

        self.show()

    def Leerzeile(self, Row, layout):
        '''
        Erstellt eine Leerzeile, eine Art Strich!

        Args:
            Row:    Zeilennummer
        '''
        # Leerzeile ChatBot:
        empty_widget = QWidget()
        empty_widget.setFixedHeight(1)                              # Festlegen der Höhe
        empty_widget.setStyleSheet("background-color: black")       # Festlegen der Hintergrundfarbe
        layout.addWidget(empty_widget, Row,0,1,-1) 

    def Leerspalte(self, Colom, layout, startRow = 0, endRow = -1):
        '''
        Erstellt eine LeerSpalte, eine Art Strich!

        Args:
            Colom:    Spaltennummer
        '''
        # Leerzeile ChatBot:
        empty_widget = QWidget()
        empty_widget.setFixedWidth(1)                              # Festlegen der Höhe
        empty_widget.setStyleSheet("background-color: black")       # Festlegen der Hintergrundfarbe
        layout.addWidget(empty_widget, startRow, Colom, endRow, 1) 

    def Kurven_Anzeige(self, state):
        for n in self.size_dict:
            self.size_dict[n][1].setText('1')
            self.size_dict[n][1].setEnabled(False)      

        button = self.sender()
        #print(button.palette().window().color().name())
        #print(button.styleSheet())
        if not self.plot.Vergleichsmodus:
            self.bereits_geklicket = []
            for n in self.knopf_Pfad:
                n.setStyleSheet(self.default)   
        button.setStyleSheet(self.aktiv)
        file = self.knopf_Pfad[button]
        if not file in self.bereits_geklicket:
            self.bereits_geklicket.append(file)
            with open(file,'r',encoding='utf8') as fo:
                lines = fo.readlines()  
            
            date = lines[2].split(' ')[0]
            self.saveName = f'{file.replace(".csv", "").replace(" ", "_").replace(f"{self.ordner}/","")}_{date}'

            werte_dict = {}
            for line in lines:
                line = line.strip()
                lzZ = line[-1]
                if not lzZ == ',':  
                    line += ',' 
                line = line[0:-1]
                if 'datetime,s,' in line:
                    units = line
                    units_list = units.split(',')
                elif 'time_abs,time_rel,' in line:
                    variables = line
                    variables_list = variables.split(',')
                    z = 0
                    for n in variables_list:
                        werte_dict.update({n:[[], units_list[z]]})
                        z += 1
                else:
                    teil_zeile = line.split(',')
                    z = 0
                    for teil in teil_zeile:
                        variable = variables_list[z]
                        werte_dict[variable][0].append(teil)
                        z += 1

            self.plot.update(f"{file.replace('.csv', '').replace(f'{self.ordner}/','')} - {date}", werte_dict, self.plot, self.legend_achsen_Rechts_widget, file)

            ## Skalierungsbereiche freischalten:
            for n in self.size_dict:
                for i in self.plot.curve_dict:
                    if self.plot.curve_dict[i][0] == n:
                        self.size_dict[n][1].setEnabled(True)     
                        break  
        else:
            #print(self.plot.used_Color_list)
            del_widget = []
            for widget in self.plot.widget_dict:
                if self.plot.widget_dict[widget][0] == file:
                    widget.setParent(None) 
                    self.plot.used_Color_list.remove(self.plot.widget_dict[widget][1])
                    #print( self.plot.used_Color_list)
                    self.plot.widget_dict[widget][2].clear()
                    self.plot.anzK = 0
                    del_widget.append(widget)
            for n in del_widget:    
                self.plot.widget_dict.pop(n)
            button.setStyleSheet(self.default)
            self.bereits_geklicket.remove(file)

    def Update_Kurven_Bereich(self):
        self.labelError_1.setText('')

        # Auslesen:
        minX  = self.LE_minX.text().replace(",", ".")
        minY1 = self.LE_minY1.text().replace(",", ".")
        minY2 = self.LE_minY2.text().replace(",", ".")

        maxX  = self.LE_maxX.text().replace(",", ".")
        maxY1 = self.LE_maxY1.text().replace(",", ".")
        maxY2 = self.LE_maxY2.text().replace(",", ".")

        # Listen:
        var_List = [minX, minY1, minY2, maxX, maxY1, maxY2]
        Default  = [0, 0, 0, 100, 100, 100]

        # Prüfung:
        i = 0
        for n in var_List:
            if n == '':
                var_List[i] = Default[i]
                self.labelError_1.setText(self.Label_error_2[self.sprache])
            try:
                var_List[i] = float(n)
            except:
                var_List[i] = Default[i]
                self.labelError_1.setText(self.Label_error_3[self.sprache])
            i += 1

        # Min-Max-Vergleich:
        if var_List[0] >= var_List[3]:
            var_List[0] = Default[0]
            var_List[3] = Default[3]
            self.labelError_1.setText(self.Label_error_4[self.sprache])
        if var_List[1] >= var_List[4]:
            var_List[1] = Default[1]
            var_List[4] = Default[4]
            self.labelError_1.setText(self.Label_error_5[self.sprache])
        if var_List[2] >= var_List[5]:
            var_List[2] = Default[2]
            var_List[5] = Default[5]
            self.labelError_1.setText(self.Label_error_6[self.sprache])
        
        # Setze Range:
        if self.CBX.isChecked():
            self.plot.achse_1.setXRange(var_List[0], var_List[3])
        if self.CBY1.isChecked():
            self.plot.achse_1.setYRange(var_List[1], var_List[4])
        if self.CBY2.isChecked():
            self.plot.achse_2.setYRange(var_List[2], var_List[5])
    
    def Save_Kurven_Bereich(self):
        # Haupt-Speicherort:
        ordner_save = 'Bilder'
        if not os.path.exists(ordner_save):            # schaue ob es den Ordner schon gibt
            os.makedirs(ordner_save)                   # wenn nicht erstelle Ordner

        # Nach CSV-Datei mit Datum:
        ordner_Plots = self.saveName
        if self.cb_Vergleich.isChecked():
            ordner_Plots = 'Vergleichsmodus'
        if not os.path.exists(f'{ordner_save}/{ordner_Plots}'):            # schaue ob es den Ordner schon gibt
            os.makedirs(f'{ordner_save}/{ordner_Plots}')                   # wenn nicht erstelle Ordner
        Pfad = f'{ordner_save}/{ordner_Plots}'
        
        # Bild-Name:
        FileOutIndex = str(1).zfill(4)
        BildOutName = 'Plot_#' + FileOutIndex + '.png'
        j = 1
        while os.path.exists(Pfad + '/' + BildOutName) :                    # Schaut ob es den Namen schon in dem Verzeichnis gibt ...
            j = j + 1                                                       # ... wenn ja wird der FileOutIndex (j) solange erhöht bis es eine neue Datei erstellen kann
            FileOutIndex = str(j).zfill(4)
            BildOutName = 'Plot_#' + FileOutIndex + '.png'

        # Save-Widget:
        pixmap = self.Bereich_Rechts.grab()     
        pixmap.save(f'./{Pfad}/{BildOutName}')       
        
    
    def Pass_Kurven_An(self):
        y_label_L = self.plot.y_Label_Left
        y_label_R = self.plot.y_Label_Right
        for i in self.plot.curve_dict:
            #print(self.plot.curve_dict[i][0])
            for n in self.size_dict:
                if self.plot.curve_dict[i][0] == n:
                    read_LE = self.size_dict[n][1].text().replace(",", ".")
                    try:
                        faktor = float(read_LE)
                    except:
                        faktor = 1
                        self.size_dict[n][1].setText('1')
                        print(self.Label_error_7[self.sprache])
                    y_new = [a * faktor for a in self.plot.curve_dict[i][2]]
                    i.setData(self.plot.curve_dict[i][1], y_new)
                    faktor_label = f'{n}x{faktor}'
                    if self.plot.curve_dict[i][3] == 'a1' and not faktor_label in y_label_L:
                        if not faktor == 1:     y_label_L = y_label_L.replace(n, faktor_label)
                        else:                   y_label_L = y_label_L.replace(n, f'{n}')
                    if self.plot.curve_dict[i][3] == 'a2' and not faktor_label in y_label_R:
                        if not faktor == 1:     y_label_R = y_label_R.replace(n, faktor_label)
                        else:                   y_label_R = y_label_R.replace(n, f'{n}')

        fontsize            = 12
        right_color         = 'red'
        self.plot.achse_1.setLabel(axis = 'left', text= y_label_L, **{'font-size': f'{fontsize}pt'}) 
        self.plot.achse_1.getAxis('right').setLabel(y_label_R, **{'color': right_color, 'font-size': f'{fontsize}pt'})

        # Fehlen tut:
        # Bei keinem Plot -> alle verriegelt und Fehlermeldung!!
        # das selbe gilt für save

    def Auto_Scale(self):
        self.plot.achse_1.autoRange()
        self.plot.achse_2.autoRange()
        self.plot.achse_1.enableAutoRange(axis="x")
        self.plot.achse_2.enableAutoRange(axis="x")
        self.plot.achse_1.enableAutoRange(axis="y")
        self.plot.achse_2.enableAutoRange(axis="y")

    def Vergleich_Modus(self):
        right_color = 'red'
        fontsize    = 12
        ## Leere Plot:
        for n in self.knopf_Pfad:
            n.setStyleSheet(self.default)  
        for widget in self.plot.widget_list:
            widget.setParent(None) 
        self.plot.achse_1.clear()               
        self.plot.achse_2.clear()
        self.plot.achse_1.setLabel(axis = 'left', text= '', **{'font-size': f'{fontsize}pt'}) 
        self.plot.achse_1.getAxis('right').setLabel('', **{'color': right_color, 'font-size': f'{fontsize}pt'})
        self.plot.used_Color_list = []
        self.bereits_geklicket = []
        self.plot.widget_dict = {}
        for n in self.size_dict:
            self.size_dict[n][1].setEnabled(False)
        ## Checkbox:
        if self.cb_Vergleich.isChecked():
            self.label_cb.setText(self.Language_VM_1[self.sprache])
            self.plot.Vergleichsmodus = True
            ## Leere Plot:
            self.plot.graph.setTitle(self.Language_VM_2[self.sprache])
            self.plot.anzK = 0
        else:
            self.label_cb.setText(self.Language_VM_3[self.sprache])
            self.plot.Vergleichsmodus = False
            ## Leere Plot:
            self.plot.graph.setTitle('')
                    
# ++++++++++++++++++++++++++++
# Hauptprogramm:
# ++++++++++++++++++++++++++++

# Sprache Festlegen:
parser = ArgumentParser(
        prog="Logging_File_Evaluation",
        description="Evaluation or Sorting from the Logging-VIFCON-File.",
    )
parser.add_argument(
        "-l",
        "--language",
        help="Language DE (German) or EN (English) - Usage from upper() [optional, default='EN']",
        default="EN",
    )
parser.add_argument(
        "-f",
        "--folder",
        help="Name of the folder in which the measurement data is located [optional, default='Messordner]",
        default="Messdaten",
    )
args = parser.parse_args()
language = args.language.upper()

if language == 'DE':    sprache = 0
elif language == 'EN':  sprache = 1
else:                   sprache = 1

# Sprache Listen:
Language_file_error =   ['Kein Messordner vorhanden!',  'No measurement folder available!']

# Ordner Auslesen und Messdaten-csv speichern:
error = False
path_O = f'./{args.folder}'
if not os.path.exists(path_O):
    path_O = './Messdaten'
    if not os.path.exists(path_O):
        print(Language_file_error[sprache])
        error = True

if not error:
    files = os.listdir(path_O) 
    messdata = []
    for file in files:
        if '.csv' in file:
            messdata.append(file)

    if __name__ == "__main__":
        app = QApplication(sys.argv)
        mainWindow = GUI(sprache, messdata, path_O)
        app.quit
        sys.exit(app.exec_())

######################
# Alt:
#####################
'''
    def update(self, label_titel, data, plot, legende):
        # Leere Plot:
        plot.achse_1.clear()                # https://stackoverflow.com/questions/71186683/pyqtgraph-completely-clear-plotwidget
        plot.achse_2.clear()
        self.kurven_side_legend = {}
        for widget in self.widget_list:
            widget.setParent(None)          # https://stackoverflow.com/questions/5899826/pyqt-how-to-remove-a-widget
        self.widget_list = []
        # Einstellungen:
        fontsize            = 12
        right_color         = 'red'
        self.graph.setTitle(label_titel, color="black", size=f"{fontsize}pt")
        anzK = 0

        # Fraben:
        COLORS = [
            "green",
            "cyan",
            "magenta",
            "blue",
            "orange",
            "darkmagenta",
            "brown",
            "tomato",
            "lime",
            "olive",
            "navy",
            "peru",
            "grey",
            "black",
            "darkorange",
            "sienna",
            "gold",
            "yellowgreen",
            "skyblue",
            "mediumorchid",
            "deeppink",
            "purple",
            "darkred"
        ] # 23 Farben - https://matplotlib.org/stable/gallery/color/named_colors.html

        # Achsen-Beschriftung 1 und Mögliche anzeigbare Messgrößen:
        ## Leeren:
        label_left  = ''
        label_right = ''
        ## Definieren:
        left_axis   = ['Temperatur', 'Position', 'Winkel', 'Strom', 'Spannung']
        right_axis  = ['Operating', 'Geschwindigkeit', 'Leistung', 'Frequenz']
        size_Label  = {'Temperatur':        'T',
                       'Position':          's',
                       'Winkel':            '\u03B1',
                       'Strom':             'I',
                       'Spannung':          'U',
                       'Leistung':          'P',
                       'Operating':         'P',
                       'Geschwindigkeit':   ['v','\u03C9'],
                       'Frequenz':          'f'}
        
        # Erstellung der Kurven und # Achsen-Beschriftung 2
        for n in data:
            position = 'left'
            ## x-Achsen-Werte:
            if n == 'time_rel':
                x_str = data[n][0]
                x = []
                for wert in x_str:
                    x.append(float(wert))
            ## y-Achsen_Werte:
            elif 'time' not in n:
                if 'max.' in n or 'min.' in n:  size_pos = True  
                else:                           size_pos = False
                ### Linke Plot-Achse:
                for i in left_axis:
                    if i in n or size_pos:
                        position = 'left'
                        #### Achsen-Beschriftung:
                        unit = data[n][1]
                        if unit == 'DEG C':
                            unit = '°C'
                        if size_pos: y_label = size_Label['Position']
                        else:        y_label = size_Label[i]
                        if not y_label in label_left:
                            label_left += f'{y_label} [{unit}] | '
                        if 'Soll' in n:                                         extra = 'Soll'
                        elif 'Ist' in n:                                        extra = 'Ist'
                        elif 'sim' in n:                                        extra = 'Ist-Sim'
                        elif 'real' in n:                                       extra = 'Ist-Gerät'
                        elif 'Winkel' in n and not 'Soll' in n:                 extra = 'Ist'
                        elif 'Position' in n and 'PI-Achse' in label_titel:     extra = 'Ist'
                        elif 'max' in n:                                        extra = 'oG'
                        elif 'min' in n:                                        extra = 'uG'
                        else:                                                   extra = ''
                        #### Beende For-Schleife, da Größe gefunden:
                        break
                ### Rechte Plot-Achse:
                for i in right_axis:
                    if i in n:
                        position = 'right'
                        #### Achsen-Beschriftung:
                        unit = data[n][1]
                        if i == 'Geschwindigkeit':
                            if unit == 'mm/min' or unit == 'mm/s':
                                y_label = size_Label[i][0]
                            else:
                                y_label = size_Label[i][1]
                        else:        
                            y_label = size_Label[i]
                        if not y_label in label_right:
                            label_right += f'{y_label} [{unit}] | '
                        if 'Soll' in n:                                     extra = 'Soll'
                        elif 'Ist' in n:                                    extra = 'Ist'
                        elif 'Geschwindigkeit' in n and not 'Soll' in n:    extra = 'Ist'
                        else:                                               extra = ''
                        ### Beende For-Schleife, da Größe gefunden:
                        break
                ## Werte auslesen:
                y_str = data[n][0]
                y = []
                for wert in y_str:
                    y.append(float(wert))
                ## Kurve erstellen:
                color = COLORS[anzK]
                pen_kurve = pg.mkPen(color, width=2)
                if position == 'left':
                    curve = plot.achse_1.plot(x, y, pen=pen_kurve, name='Test')
                    achse = 'a1'
                elif position == 'right':
                    curve = pg.PlotCurveItem(x, y, pen=pen_kurve, name='Test')
                    plot.achse_2.addItem(curve)
                    achse = 'a2'
                ## Legende:
                widget, side_checkbox = self.GUI_Legend_Side([n, f'{y_label}<sub>{extra}</sub>'], pen_kurve, achse)
                legende.layout.addWidget(widget)
                self.widget_list.append(widget)
                self.kurven_side_legend.update({side_checkbox: curve})
                anzK += 1

        # Achsen-Beschriftung 3
        self.achse_1.setLabel(axis = 'left', text= label_left[0:-2], **{'font-size': f'{fontsize}pt'}) 
        self.achse_1.getAxis('right').setLabel(label_right[0:-2], **{'color': right_color, 'font-size': f'{fontsize}pt'})


'''