# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Eurotherm Geräte Widget:
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
    QLineEdit,
    QRadioButton,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,

)
from PyQt5.QtGui import (
    QIcon, 

)
from PyQt5.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,

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


class EurothermWidget(QWidget):
    signal_Pop_up       = pyqtSignal()

    def __init__(self, sprache, Frame_Anzeige, widget, line_color, config, config_dat, neustart, multilog_aktiv, add_Ablauf_function, eurotherm = 'Eurotherm', typ = 'Generator', parent=None):
        """GUI widget of Eurotherm controller.

        Args:
            sprache (int):                      Sprache der GUI (Listenplatz)
            Frame_Anzeige (bool):               Macht den Rahmen der Widgets in dem Gerät sichtbar
            widget (Objekt):                    Element in das, das Widget eingefügt wird
            line_color (list):                  Liste mit Farben
            config (dict):                      Konfigurationsdaten aus der YAML-Datei
            config_dat (string):                Datei-Name der Config-Datei
            multilog_aktiv (bool):              Multilog-Read/Send Aktiviert
            neustart (bool):                    Neustart Modus, Startkonfigurationen werden übersprungen
            add_Ablauf_function (Funktion):     Funktion zum updaten der Ablauf-Datei.
            eurotherm (str):                    Name des Gerätes
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
        self.multilog_OnOff             = multilog_aktiv
        self.add_Text_To_Ablauf_Datei   = add_Ablauf_function
        self.device_name                = eurotherm
        self.typ                        = typ

        ## Faktoren Skalierung:
        self.skalFak = self.typ_widget.Faktor

        ## Aktuelle Messwerte:
        self.ak_value = {}

        ## Signal:
        self.signal_Pop_up.connect(self.Pop_Up_Start_Later)

        ## GUI:
        self.color_Aktiv = self.typ_widget.color_On

        ## Weitere:
        self.Rezept_Aktiv   = False
        self.op_Mod         = False
        self.data           = {}
        self.start_later    = False

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
        self.Log_Pfad_conf_9    = ['Die Obergrenze ist kleiner als die Untergrenze! Setze die Limits auf Default:',                                 'The upper limit is smaller than the lower limit! Set the limits to default:']
        self.Log_Pfad_conf_10   = ['zu',                                                                                                            'to']
        self.Log_Pfad_conf_11   = ['Temperatur',                                                                                                    'Temperatur']
        self.Log_Pfad_conf_12   = ['PID-Eingang Istwert',                                                                                           'PID input actual value']
        self.Log_Pfad_conf_13   = ['Leistung',                                                                                                      'Power']
        self.Log_Pfad_conf_14   = ['Konfiguration mit VM, MV oder MM ist so nicht möglich, da der Multilink abgeschaltet ist! Setze Default VV!',   'Configuration with VM, MV or MM is not possible because the multilink is disabled! Set default VV!']
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Zum Start:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.init = self.config['start']['init']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.init = False
        #//////////////////////////////////////////////////////////////////////
        try: self.Safety = self.config['start']['sicherheit']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|sicherheit {self.Log_Pfad_conf_5[self.sprache]} True')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.Safety = True
        #//////////////////////////////////////////////////////////////////////
        try: self.startMode = self.config['start']["start_modus"]
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|start_modus {self.Log_Pfad_conf_5[self.sprache]} Manuel')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startMode = 'Manuel'
        #//////////////////////////////////////////////////////////////////////
        try: self.StartRampe = self.config['start']["ramp_start_value"].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|ramp_start_value {self.Log_Pfad_conf_5[self.sprache]} IST')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.StartRampe = 'IST'
        # Wert Kontrolle: unter `Nachrichten im Log-File:` zu finden!
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.startTemp = float(str(self.config["defaults"]['startTemp']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|startTemp {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startTemp = 0
        #//////////////////////////////////////////////////////////////////////
        try: self.startPow = float(str(self.config["defaults"]['startPow']).replace(',','.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|startPow {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.startPow = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Limits:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Solltemperatur:
        try: self.oGST = self.config["limits"]['maxTemp'] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxTemp {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGST = 1
        #//////////////////////////////////////////////////////////////////////       
        try: self.uGST = self.config["limits"]['minTemp']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minTemp {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGST = 0
        ### Ausgangsleistung (Operating Point)
        try: self.oGOp = self.config["limits"]['opMax']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|opMax {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGOp = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGOp = self.config["limits"]['opMin']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|opMin {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGOp = 0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### GUI:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: 
            self.legenden_inhalt = self.config['GUI']['legend'].split(';')
            self.legenden_inhalt = [a.strip() for a in self.legenden_inhalt]    # sollten Unnötige Leerzeichen vorhanden sein, so werden diese entfernt!
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} GUI|legend {self.Log_Pfad_conf_5[self.sprache]} [IWv, IWw]')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.legenden_inhalt = ['IWT', 'IWOp']
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Rezepte:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.rezept_config = self.config["rezepte"]
        except Exception as e: 
            self.rezept_config = {'rezept_Default':  {'n1': '10 ; 0 ; s'}}
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} rezepte {self.Log_Pfad_conf_5[self.sprache]} {self.rezept_config}')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try: self.PID_Aktiv = self.config['PID']['PID_Aktiv']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|PID_Aktiv {self.Log_Pfad_conf_5[self.sprache]} False')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Aktiv = 0 
        #//////////////////////////////////////////////////////////////////////
        try: self.origin    = self.config['PID']['Value_Origin'].upper()
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Value_Origin {self.Log_Pfad_conf_5[self.sprache]} VV')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.origin = 'VV'
        #//////////////////////////////////////////////////////////////////////
        try: self.PID_Mode_Switch_Value = float(str(self.config['PID']['umstell_wert']).replace(',', '.'))
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|umstell_wert {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.PID_Mode_Switch_Value = 0  
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ## Config-Fehler und Defaults:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### PID-Aktiv:
        if not type(self.PID_Aktiv) == bool and not self.PID_Aktiv in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} PID_Aktiv - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.PID_Aktiv}')
            self.PID_Aktiv = 0
        ### Init:
        if not type(self.init) == bool and not self.init in [0,1]: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
            self.init = 0
        ### Temperatur-Limit:
        if not type(self.oGST) in [float, int] or not self.oGST >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxTemp - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGST)}')
            self.oGST = 1
        if not type(self.uGST) in [float, int] or not self.uGST >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minTemp - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGST)}')
            self.uGST = 0
        if self.oGST <= self.uGST:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_11[self.sprache]})')
            self.uGST = 0
            self.oGST = 1
        ### Ausgangsleistungs-Limit:
        if not type(self.oGOp) in [float, int] or not self.oGOp >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} opMax - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGOp)}')
            self.oGOp = 1
        if not type(self.uGOp) in [float, int] or not self.uGOp >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} opMin - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGOp)}')
            self.uGOp = 0
        if self.oGOp <= self.uGOp:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
            self.uGOp = 0
            self.oGOp = 1
        ### HO-Start-Sicherheit:
        if not type(self.Safety) == bool and not self.Safety in [0, 1]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} sicherheit - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} True - {self.Log_Pfad_conf_8[self.sprache]} {self.Safety}')
            self.Safety = 1
        ### Start-Modus:
        if not self.startMode in ['Auto', 'Manuel']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_modus - {self.Log_Pfad_conf_2[self.sprache]} [Auto, Manuel] - {self.Log_Pfad_conf_3[self.sprache]} Manuel - {self.Log_Pfad_conf_8[self.sprache]} {self.startMode}')
            self.startMode = 'Manuel'
        ### Start-Temperatur:
        if not type(self.startTemp) in [float, int] or not self.startTemp >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startTemp - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.startTemp}')
            self.startTemp = 0
        ### Start-Leistung (OP):
        if not type(self.startPow) in [float, int] or not self.startPow >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} startPow - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8[self.sprache]} {self.startPow}')
            self.startPow = 0
        ### PID-Herkunft:
        if not type(self.origin) == str or not self.origin in ['MM', 'MV', 'VV', 'VM']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Value_Origin - {self.Log_Pfad_conf_2[self.sprache]} [VV, MM, VM, MV] - {self.Log_Pfad_conf_3[self.sprache]} VV - {self.Log_Pfad_conf_8[self.sprache]} {self.origin}')
            self.origin = 'VV'
        if not self.multilog_OnOff and self.origin in ['MM', 'MV', 'VM']:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_14[self.sprache]}')
            self.origin = 'VV'
        ### PID-Umschaltwert:
        if not type(self.PID_Mode_Switch_Value) in [float, int] or not self.PID_Mode_Switch_Value >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} umstell_wert - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.PID_Mode_Switch_Value)}')
            self.PID_Mode_Switch_Value = 0
        
        #--------------------------------------- 
        # Sprach-Einstellung:
        #--------------------------------------- 
        ## Werte: ##################################################################################################################################################################################################################################################################################
        sollwert_str            = ['Soll',                                                                                                                                                                                                  'Set']
        istwert_str             = ['Ist',                                                                                                                                                                                                   'Is']
        ## Knöpfe: #################################################################################################################################################################################################################################################################################                                                                                          
        send_str                = ['Sende',                                                                                                                                                                                                 'Send']
        rez_start_str           = ['Rezept Start',                                                                                                                                                                                          'Start recipe']
        rez_ende_str            = ['Rezept Beenden',                                                                                                                                                                                        'Finish recipe']
        ## Checkbox: ###############################################################################################################################################################################################################################################################################                                                                                                   
        cb_sync_str             = ['Sync',                                                                                                                                                                                                  'Sync']
        cb_PID                  = ['PID',                                                                                                                                                                                                   'PID']
        ## Einheiten mit Größe: ####################################################################################################################################################################################################################################################################                                                                                            
        P_str                   = ['Out-Op in %:',                                                                                                                                                                                          'Out-Op in %:']
        T_str                   = ['T in °C:',                                                                                                                                                                                              'T in °C:']
        sP_str                  = ['Op:',                                                                                                                                                                                                   'Op:']
        sT_str                  = ['T:',                                                                                                                                                                                                    'T:']
        st_P_str                = ['XXX.XX %',                                                                                                                                                                                              'XXX.XX %']
        st_T_str                = ['XXX.XX°C',                                                                                                                                                                                              'XXX.XX°C']
        st_Tsoll_str            = ['(XXX.XX)',                                                                                                                                                                                              '(XXX.XX)']
        T_einzel_str            = ['T',                                                                                                                                                                                                     'T']
        P_einzel_str            = ['P',                                                                                                                                                                                                     'P']
        PID_Von_1               = ['Wert von Multilog',                                                                                                                                                                                     'Value of Multilog']
        PID_Von_2               = ['Wert von VIFCON',                                                                                                                                                                                       'Value ofVIFCON']
        PID_Zusatz              = ['ex,',                                                                                                                                                                                                   'ex,']
        self.T_unit_einzel      = ['°C',                                                                                                                                                                                                    '°C']
        self.P_unit_einzel      = ['%',                                                                                                                                                                                                     '%']
        ## Fehlermeldungen: ########################################################################################################################################################################################################################################################################                                                                                                                                                                                    
        self.err_0_str          = ['Fehler!',                                                                                                                                                                                               'Error!']                   
        self.err_1_str          = ['Keine Eingabe!',                                                                                                                                                                                        'No input!']
        self.err_2_str          = ['Grenzen überschritten!\nGrenzen von',                                                                                                                                                                   'Limits exceeded!\nLimits from']
        self.err_3_str          = ['bis',                                                                                                                                                                                                   'to']
        self.err_4_str          = ['Gerät anschließen und\nInitialisieren!',                                                                                                                                                                'Connect the device\nand initialize!']
        self.err_5_str          = ['Fehlerhafte Eingabe!',                                                                                                                                                                                  'Incorrect input!']
        self.err_6_str          = ['Der Wert',                                                                                                                                                                                              'The value']
        self.err_7_str          = ['überschreitet\ndie Grenzen von',                                                                                                                                                                        'exceeds\nthe limits of']
        self.err_10_str         = ['Rezept Einlesefehler!',                                                                                                                                                                                 'Recipe import error!']
        self.err_11_str         = ['Keine Anzeige!',                                                                                                                                                                                        'No display!']
        self.err_12_str         = ['Erster Schritt = Sprung!\nDa keine Messwerte!',                                                                                                                                                         'First step = jump! There\nare no measurements!']
        self.err_13_str         = ['o.K.',                                                                                                                                                                                                  'o.K.']   
        self.err_14_str         = ['Rezept läuft!\nRezept Einlesen gesperrt!',                                                                                                                                                              'Recipe is running!\nReading recipes blocked!']
        self.err_15_str         = ['Wähle ein Rezept!',                                                                                                                                                                                     'Choose a recipe!']
        self.err_16_str         = ['Die Rampen Art er ist\nnur bei T-Rampen möglich!',                                                                                                                                                      'The ramp type er is only\npossible with T-ramps!']
        self.err_17_str         = ['Die Rampen Art op ist\nnur bei T-Rampen möglich!',                                                                                                                                                      'The ramp type op is only\npossible with T-ramps!']
        self.err_18_str         = ['Rezept Fehler:\nFehler im op-Schritt!',                                                                                                                                                                 'Recipe error:\nError in the op step!']
        self.err_19_str         = ['Rezept läuft!\nRezept Start gesperrt!',                                                                                                                                                                 'Recipe running!\nRecipe start blocked!']
        self.err_20_str         = ['Die Rampen Segmente er, op und opr sind\nin dem PID-Modus nicht erlaubt!',                                                                                                                              'The ramp segments er, op and opr are\nnot allowed in PID mode!']
        self.err_21_str         = ['Fehler in der Rezept konfiguration\nder Config-Datei! Bitte beheben und Neueinlesen!',                                                                                                                  'Error in the recipe configuration of\nthe config file! Please fix and re-read!']
        self.err_Rezept         = ['Rezept Einlesefehler!\nUnbekanntes Segment:',                                                                                                                                                           'Recipe reading error!\nUnknown segment:']
        ## Plot-Legende: ##########################################################################################################################################################################################################################################################################                                                                                                                                                        
        rezept_Label_str        = ['Rezept',                                                                                                                                                                                                'Recipe']
        ober_Grenze_str         = ['oG',                                                                                                                                                                                                    'uL']                                   # uL - upper Limit
        unter_Grenze_str        = ['uG',                                                                                                                                                                                                    'lL']                                   # lL - lower Limit
        ## Messgrößen: ############################################################################################################################################################################################################################################################################                                                                              
        self.temp_str           = ['Temperatur',                                                                                                                                                                                            'Temperature']
        self.op_str             = ['Leistung',                                                                                                                                                                                              'Power']
        ## Logging: ###############################################################################################################################################################################################################################################################################                                                                            
        self.Log_Text_1_str 	= ['Erstelle Widget.',                                                                                                                                                                                      'Create widget.']
        self.Log_Text_28_str    = ['Gerät wurde Gestartet/Initialisiert!',                                                                                                                                                                  'Device has been started/initialized!']
        self.Log_Text_29_str    = ['Gerät wurde nicht Initialisiert! Initialisierung durch Menü im späteren!',                                                                                                                              'Device was not initialized! Initialization through menu later!']
        self.Log_Text_30_str    = ['Neustart Modus.',                                                                                                                                                                                       'Restart mode.']
        self.Log_Text_38_str    = ['Fehlerhafte Eingabe - Grund:',                                                                                                                                                                          'Incorrect input - Reason:']
        self.Log_Text_39_str    = ['Rezept:',                                                                                                                                                                                               'Recipe:']
        self.Log_Text_40_str    = ['Rezept Inhalt:',                                                                                                                                                                                        'Recipe content:']
        self.Log_Text_41_str    = ['Prüfung der Maximalen Ausgangsleistung (HO). Auslesen aus dem Gerät. Überschreibung des Limits.',                                                                                                       'Testing the maximum output power (HO). Reading from the device. Limit override.']
        self.Log_Text_42_str    = ['Setzen des Maximalen Ausgangsleistung (HO) mit dem Maximalen Config-Limit für den Leistungsausgang.',                                                                                                   'Setting the maximum output power (HO) with the maximum config limit for the power output.']
        self.Log_Text_43_str    = ['Startmodus Leistungseingabe (Manueller Modus)!',                                                                                                                                                        'Start mode power input (manual mode)!']
        self.Log_Text_44_str    = ['Startmodus Temperatureingabe (Automatischer Modus)!',                                                                                                                                                   'Start mode temperature input (automatic mode)!']
        self.Log_Text_181_str   = ['Eurotherm Rampe geht vom Istwert aus. Eurotherm Rampe zu Beginn benötigt für den Plot den Istwert! Annahme auf 20°C!',                                                                                  'Eurotherm ramp is based on the actual value. Eurotherm ramp at the beginning requires the actual value for the plot! Assumption at 20°C!']
        self.Log_Text_182_str   = ['Eine Eurotherm-Rampe wird nur bei Temperatur durchführbar sein!',                                                                                                                                       'A Eurotherm ramp will only be possible at temperature!']
        self.Log_Text_184_str   = ['Die Rampen Art op kann nur bei einem Temperatur-Rezept angewendet werden!',                                                                                                                             'The ramp type op can only be used with a temperature recipe!']
        self.Log_Text_185_str   = ['Rezept Fehler: ',                                                                                                                                                                                       'Recipe error: ']
        self.Log_Text_205_str   = ['Update Konfiguration (Update Limits):',                                                                                                                                                                 'Update configuration (update limits):']
        self.Log_Text_242_str   = ['Die maximale Ausgangsleistung (HO) wird nicht an das Limit angepasst!',                                                                                                                                 'The maximum output power (HO) is not adjusted to the limit!']
        self.Log_Text_245_str   = ['Die Erste Rampe Startet beim Istwert!',                                                                                                                                                                 'The first ramp starts at the actual value!']
        self.Log_Text_246_str   = ['Die Erste Rampe Startet beim Sollwert!',                                                                                                                                                                'The first ramp starts at the setpoint!']
        self.Log_Text_247_str   = ['Die Einstellung für die Erste Rampe ist fehlerhaft! Möglich sind nur SOLL und IST!! Default IST.',                                                                                                      'The setting for the first ramp is incorrect! Only SOLL and IST are possible!! Default IST.']
        self.Log_Text_248_str   = ['Das Rampen Segment er kann nicht im PID-Modus angewendet werden!',                                                                                                                                      'The ramp segment er cannot be used in PID mode!']
        self.Log_Text_PID_Ex    = ['Der Wert in der Konfig liegt außerhalb des Limit-Bereiches! Umschaltwert wird auf Minimum-Limit gesetzt!',                                                                                              'The value in the config is outside the limit range! Switching value is set to minimum limit!']
        self.Log_Text_Ex1_str   = ['Fehler Grund (Rezept einlesen):',                                                                                                                                                                       'Error reason (reading recipe):']
        self.Log_Text_Ex2_str   = ['Fehler Grund (Problem mit Rezept-Konfiguration):',                                                                                                                                                      'Error reason (Problem with recipe configuration)']
        self.Log_Text_EPID_1    = ['Update Konfiguration (Update PID-Parameter Eurotherm):',                                                                                                                                                'Update configuration (update PID parameters Eurotherm):']
        self.Log_Text_EPID_2    = ['Der Wert',                                                                                                                                                                                              'The value']
        self.Log_Text_EPID_3    = ['liegt außerhalb des Bereiches 0 bis 99999! Senden verhindert!',                                                                                                                                         'is outside the range 0 to 99999! Sending prevented!']
        self.Log_Text_EPID_4    = ['Beim Vorbereiten des Sendens der neuen PID-Parameter gab es einen Fehler!',                                                                                                                             'There was an error while preparing to send the new PID parameters!']
        self.Log_Text_EPID_5    = ['Einlese-Fehler der\nneuen Eurotherm PID-Parameter!',                                                                                                                                                    'Error reading the\nnew Eurotherm PID parameters!']
        self.Log_Text_EPID_6    = ['Fehlergrund (PID-Parameter):',                                                                                                                                                                          'Reason for error (PID parameter):']
        self.Log_Text_LB_1      = ['Limitbereich',                                                                                                                                                                                          'Limit range']
        self.Log_Text_LB_2      = ['Temperatur',                                                                                                                                                                                            'Temperatur']
        self.Log_Text_LB_3      = ['Operating Point (Leistung)',                                                                                                                                                                            'Operating Point (Power)']
        self.Log_Text_LB_4      = ['bis',                                                                                                                                                                                                   'to']
        self.Log_Text_LB_5      = ['nach Update',                                                                                                                                                                                           'after update']
        self.Log_Text_Kurve     = ['Kurvenbezeichnung existiert nicht:',                                                                                                                                                                    'Curve name does not exist:']
        ## Ablaufdatei: ###########################################################################################################################################################################################################################################################################                                                                             
        self.Text_19_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da keine Eingabe.',                                                                                                                                   'Input field error message: Sending failed because there was no input.']
        self.Text_20_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da Eingabe die Grenzen überschreitet.',                                                                                                               'Input field error message: Send failed because input exceeds limits.']
        self.Text_21_str        = ['Sende den Wert',                                                                                                                                                                                        'Send the value']
        self.Text_22_str        = ['Eingabefeld Fehlermeldung: Senden Fehlgeschlagen, da fehlerhafte Eingabe.',                                                                                                                             'Input field error message: Sending failed due to incorrect input.']
        self.Text_23_str        = ['Knopf betätigt - Initialisierung!',                                                                                                                                                                     'Button pressed - initialization!']
        self.Text_24_str        = ['Ausführung des Rezeptes:',                                                                                                                                                                              'Execution of the recipe:']
        self.Text_25_str        = ['Auswahl Ausgangsleistung senden.',                                                                                                                                                                      'Send output power selection.']
        self.Text_26_str        = ['Schalte auf Manuellen Modus (SW).',                                                                                                                                                                     'Switch to manual mode (SW).']
        self.Text_27_str        = ['Auswahl Solltemperatur senden.',                                                                                                                                                                        'Send selection of target temperature.']
        self.Text_28_str        = ['Schalte auf Automatischen Modus (SW).',                                                                                                                                                                 'Switch to Automatic Mode (SW).']
        self.Text_29_str        = ['Knopf betätigt - Sende Solltemperatur (SL).',                                                                                                                                                           'Button pressed - send target temperature (SL).']
        self.Text_29_2_str      = ['Knopf betätigt - Sende Solltemperatur (PID).',                                                                                                                                                          'Button pressed - send target temperature (PID).']
        self.Text_30_str        = ['Knopf betätigt - Sende Ausgangsleistung (OP).',                                                                                                                                                         'Button pressed - send output power (OP).']
        self.Text_80_str        = ['Menü-Knopf betätigt - Lese OP maximum (HO) aus.',                                                                                                                                                       'Menu button pressed - read OP maximum (HO).']
        self.Text_80_2_str      = ['Menü-Knopf betätigt - Schreibe PID-Parameter (XP, TI, TD).',                                                                                                                                            'Menu button pressed - Write PID parameters (XP, TI, TD).']
        self.Text_80_3_str      = ['Menü-Knopf betätigt - Lese PID-Parameter (XP, TI, TD).',                                                                                                                                                'Menu button pressed - Read PID parameters (XP, TI, TD).']
        self.Text_81_str        = ['Knopf betätigt - Beende Rezept',                                                                                                                                                                        'Button pressed - End recipe']
        self.Text_82_str        = ['Rezept ist zu Ende!',                                                                                                                                                                                   'Recipe is finished!']
        self.Text_83_str        = ['Stopp betätigt - Beende Rezept',                                                                                                                                                                        'Stop pressed - End recipe']
        self.Text_84_str        = ['Rezept läuft! Erneuter Start verhindert!',                                                                                                                                                              'Recipe is running! Restart prevented!']
        self.Text_85_str        = ['Rezept Startet',                                                                                                                                                                                        'Recipe Starts']
        self.Text_86_str        = ['Rezept Beenden',                                                                                                                                                                                        'Recipe Ends']
        self.Text_87_str        = ['Knopf betätigt - Start Rezept',                                                                                                                                                                         'Button pressed - Start recipe']
        self.Text_88_str        = ['Rezept konnte aufgrund von Fehler nicht gestartet werden!',                                                                                                                                             'Recipe could not be started due to an error!']
        self.Text_89_str        = ['Knopf betätigt - Beende Rezept - Keine Wirkung, da kein aktives Rezept!',                                                                                                                               'Button pressed - End recipe - No effect because there is no active recipe!']
        self.Text_90_str        = ['Sicherer Endzustand wird hergestellt! Auslösung des Stopp-Knopfes!',                                                                                                                                    'Safe final state is established! Stop button is activated!']
        self.Text_91_str        = ['Rezept Beenden - Sicherer Endzustand',                                                                                                                                                                  'Recipe Ends - Safe End State']
        self.Text_PID_1         = ['Wechsel in PID-Modus.',                                                                                                                                                                                 'Switch to PID mode.']
        self.Text_PID_2         = ['Wechsel in Eurotherm-Regel-Modus.',                                                                                                                                                                     'Switch to Eurotherm control mode.']
        ## Pop-Up-Fenster: #########################################################################################################################################################################################################################################################################
        self.puF_HO_str         = ['Die maximale Ausgangsleistung (HO) wird nicht an das Limit angepasst! Die Einstellung Sicherheit wurde auf True gesetzt. Das bedeutet das der Wert nur direkt am Eurotherm geändert werden kann!',      'The maximum output power (HO) is not adjusted to the limit! The Security setting has been set to True. This means that the value can only be changed directly on the Eurotherm!']
        self.puF_HO_str_2       = ['Bitte beachten Sie, dass bei der Config-Einstellung "sicherheit" True der OPmax Wert nicht mit dem in dem Gerät übereinstimmen muss. Bitte Betätigen Sie zur Anpassung im Menü "Eurotherm HO lesen" oder Wechseln Sie in den Manuellen Modus, damit der OPmax-Wert in VIFCON aktualisiert wird!',
                                   'Please note that with the config setting "security" True, the OPmax valuedoes not have to match that in the device. To adjust, please press "Read Eurotherm HO" in the menu or switch to manual mode so that the OPmax value is updated in VIFCON!']
        self.puF_RezeptAnz_str = ['Beachte Konfikuration am Gerät:\n1. Sehe nach ob die richtige Einstellung für die Rampensteigung eingegeben ist (Am Eurotherm: Drücke 2xBlatt, 3xPfeil CCW -> Ramp Units -> Pfeiltasten zur Auswahl)(Achtung: Wähle das richtige Programm nach einmal Blatt)!\n2. Beachte Konfigurationseinstellung (Eurotherm) "Servo" (Eurotherm-Rampe: Start Soll- oder Istwert)!!',
                                  'Note the configuration on the device:\n1. Check whether the correct setting for the ramp gradient has been entered (On Eurotherm: Press 2xSheet, 3xArrow CCW -> Ramp Units -> arrow keys to select)(Attention: Select the correct program after one sheet)!\n2. Note configuration setting (Eurotherm) "Servo" (Eurotherm ramp: start setpoint or actual value)!!']

        #---------------------------------------
        # Konfigurationen für das Senden:
        #---------------------------------------
        #self.send_betätigt = True
        self.write_task  = {'Soll-Temperatur': False, 'Operating point':False, 'Auto_Mod': False, 'Manuel_Mod': False, 'Init':False, 'Start': False, 'EuRa': False, 'EuRa_Reset': False, 'Read_HO': False, 'Write_HO': False, 'PID': False, 'PID_Rezept_Mode_OP': False, 'PID-Update': False, 'Read_PID': False, 'Update Limit': False}
        self.write_value = {'Sollwert': 0 , 'EuRa_Soll': 0, 'EuRa_m': 0, 'Rez_OPTemp': -1, 'HO': 0, 'PID-Sollwert': 0, 'PID_Rez': -1, 'PID-Update': [0, 0, 0], 'Limits': [0, 0, 0, 0]} # Limits: oGOp, uGOp, oGx, uGx

        # Wenn Init = False, dann werden die Start-Auslesungen nicht ausgeführt:
        if self.init and not self.neustart:
            self.write_task['Start'] = True

        #---------------------------------------
        # Konfigurationen Check:
        #---------------------------------------
        try: self.write_value['PID-Sollwert'] = self.config['PID']['start_soll'] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|start_soll {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.write_value['PID-Sollwert'] = 0
        #//////////////////////////////////////////////////////////////////////
        if not type(self.write_value['PID-Sollwert']) in [int, float]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} start_soll - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.write_value["PID-Sollwert"])}')
            self.write_value['PID-Sollwert'] = 0

        #---------------------------------------
        # Nachrichten im Log-File:
        #---------------------------------------
        logger.info(f"{self.device_name} - {self.Log_Text_28_str[self.sprache]}") if self.init else logger.warning(f"{self.device_name} - {self.Log_Text_29_str[self.sprache]}")
        if self.neustart: logger.info(f"{self.device_name} - {self.Log_Text_30_str[self.sprache]}") 
        logger.info(f"{self.device_name} - {self.Log_Text_41_str[self.sprache]}") if self.Safety else logger.info(f"{self.device_name} - {self.Log_Text_42_str[self.sprache]}")
        logger.info(f"{self.device_name} - {self.Log_Text_43_str[self.sprache]}") if self.startMode == 'Manuel' else logger.info(f"{self.device_name} - {self.Log_Text_44_str[self.sprache]}")
        if self.Safety and self.init: 
            self.start_later = True 
        logger.info(f'{self.device_name} - {self.Log_Text_245_str[self.sprache]}') if self.StartRampe == 'IST' else (logger.info(f'{self.device_name} - {self.Log_Text_246_str[self.sprache]}') if self.StartRampe == 'SOLL' else logger.warning(f'{self.device_name} - {self.Log_Text_247_str[self.sprache]}'))
        ## Limit-Bereiche:
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]}: {self.uGST} {self.Log_Text_LB_4[self.sprache]} {self.oGST}{self.T_unit_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]}: {self.uGOp} {self.Log_Text_LB_4[self.sprache]} {self.oGOp} {self.P_unit_einzel[self.sprache]}')

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
        ### Grid Size - bei Verschieben der Splitter zusammenhängend darstellen: (Notiz: Das bei GUI in Arbeit erläutern!)
        self.layer_layout.setRowStretch(5, 1) 
        self.layer_layout.setColumnStretch(5, 1)

        ### Spacing:
        self.layer_layout.setHorizontalSpacing(3)       
        self.layer_layout.setVerticalSpacing(5)

        ### Zeilenhöhen:
        self.layer_layout.setRowMinimumHeight(3, 40)    # Error-Nachricht

        ### Spaltenbreiten:
        self.layer_layout.setColumnMinimumWidth(0, 100)
        self.layer_layout.setColumnMinimumWidth(1, 180)
        self.layer_layout.setColumnMinimumWidth(3, 100)
        #________________________________________
        ## Widgets:
        ### Eingabefelder:
        self.LE_Temp = QLineEdit()
        self.LE_Temp.setText(str(self.startTemp))

        self.LE_Pow = QLineEdit()
        self.LE_Pow.setText(str(self.startPow))

        ### Checkbox:
        self.Auswahl = QCheckBox(cb_sync_str[self.sprache])
        self.PID_cb  = QCheckBox(cb_PID[self.sprache])
        self.PID_cb.clicked.connect(self.PID_ON_OFF)
        if not self.PID_Aktiv:
            self.PID_cb.setEnabled(False)

        ### Radiobutton:
        self.RB_choise_Temp = QRadioButton(f'{sollwert_str[self.sprache]}-{T_str[self.sprache]} ')
        if self.color_Aktiv: self.RB_choise_Temp.setStyleSheet(f"color: {self.color[1]}")
        self.RB_choise_Temp.clicked.connect(self.BlassOutPow)

        self.RB_choise_Pow = QRadioButton(f'{P_str[self.sprache]} ')
        if self.color_Aktiv: self.RB_choise_Pow.setStyleSheet(f"color: {self.color[2]}")
        self.RB_choise_Pow.clicked.connect(self.BlassOutTemp)

        if self.init:       # and not self.neustart
            self.Start()

        ### Label:
        #### Geräte-Titel:
        self.La_name = QLabel(f'<b>{eurotherm}</b>')
        #### Isttemperatur:
        self.La_IstTemp_text = QLabel(f'{istwert_str[self.sprache]}-{sT_str[self.sprache]} ')
        self.La_IstTemp_wert = QLabel(st_T_str[self.sprache])
        if self.color_Aktiv: self.La_IstTemp_text.setStyleSheet(f"color: {self.color[0]}")
        if self.color_Aktiv: self.La_IstTemp_wert.setStyleSheet(f"color: {self.color[0]}")
        #### Istleistung:
        self.La_IstPow_text = QLabel(f'{istwert_str[self.sprache]}-{sP_str[self.sprache]} ')
        self.La_IstPow_wert = QLabel(st_P_str[self.sprache])
        if self.color_Aktiv: self.La_IstPow_text.setStyleSheet(f"color: {self.color[2]}")
        if self.color_Aktiv: self.La_IstPow_wert.setStyleSheet(f"color: {self.color[2]}")
        #### Solltemperatur:
        self.La_SollTemp_wert = QLabel(st_Tsoll_str[self.sprache])
        if self.color_Aktiv: self.La_SollTemp_wert.setStyleSheet(f"color: {self.color[1]}")
        #### Fehlernachrichten:
        self.La_error = QLabel(self.err_13_str[self.sprache])

        ### Knöpfe:
        #### Senden:
        self.btn_send_value = QPushButton(send_str[self.sprache])
        self.btn_send_value.clicked.connect(self.send) 
        #### Rezepte:
        self.btn_rezept_start =  QPushButton(rez_start_str[self.sprache])
        self.btn_rezept_start.clicked.connect(lambda: self.RezStart(1))

        self.btn_rezept_ende =  QPushButton(rez_ende_str[self.sprache])
        self.btn_rezept_ende.clicked.connect(self.RezEnde)   

        ### Combobox:
        self.cb_Rezept = QComboBox()
        self.cb_Rezept.addItem('------------')                                              # Rezept Eintrag ohne Ausführung, Für die Rezept-Anzeige relevant!
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
        #### Rezept:
        self.btn_group_Rezept = QWidget()
        self.btn_Rezept_layout = QVBoxLayout()
        self.btn_group_Rezept.setLayout(self.btn_Rezept_layout)
        self.btn_Rezept_layout.setSpacing(5)

        self.btn_Rezept_layout.addWidget(self.btn_rezept_start)
        self.btn_Rezept_layout.addWidget(self.btn_rezept_ende)
        self.btn_Rezept_layout.addWidget(self.cb_Rezept) 

        self.btn_Rezept_layout.setContentsMargins(0,0,0,0)  # left, top, right, bottom

        #### Soll-Temp:
        self.wid_group_SollT = QWidget()
        self.wid_SollT_layout = QHBoxLayout()
        self.wid_group_SollT.setLayout(self.wid_SollT_layout)
        self.wid_SollT_layout.setSpacing(5)

        self.wid_SollT_layout.addWidget(self.LE_Temp)
        self.wid_SollT_layout.addWidget(self.La_SollTemp_wert)

        self.wid_SollT_layout.setContentsMargins(0,0,0,0)

        #### First-Row:
        self.first_row_group  = QWidget()
        self.first_row_layout = QHBoxLayout()
        self.first_row_group.setLayout(self.first_row_layout)
        self.first_row_layout.setSpacing(20)

        self.first_row_layout.addWidget(self.La_name)
        self.first_row_layout.addWidget(self.Auswahl)
        self.first_row_layout.addWidget(self.PID_cb)

        self.first_row_layout.setContentsMargins(0,0,0,0)      # left, top, right, bottom
        #________________________________________
        ## Platzierung der einzelnen Widgets im Layout:
        self.layer_layout.addWidget(self.first_row_group,   0, 0, 1, 5, alignment=Qt.AlignLeft)     # Reihe, Spalte, RowSpan, ColumSpan, Ausrichtung
        self.layer_layout.addWidget(self.RB_choise_Temp,    1, 0)                          
        self.layer_layout.addWidget(self.RB_choise_Pow,     2, 0)
        self.layer_layout.addWidget(self.btn_send_value,    3, 0)
        self.layer_layout.addWidget(self.wid_group_SollT,   1, 1, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.LE_Pow,            2, 1)
        self.layer_layout.addWidget(self.La_error,          3, 1)
        self.layer_layout.addWidget(self.La_IstTemp_text,   1, 2)
        self.layer_layout.addWidget(self.La_IstPow_text,    2, 2)
        self.layer_layout.addWidget(self.La_IstTemp_wert,   1, 3, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.La_IstPow_wert,    2, 3, alignment=Qt.AlignLeft)
        self.layer_layout.addWidget(self.btn_group_Rezept,  1, 4, 3, 1, alignment=Qt.AlignTop)
        #________________________________________
        ## Größen (Size) - Widgets:
        ### Eingabefelder (Line Edit):
        self.LE_Temp.setFixedWidth(100)
        self.LE_Temp.setFixedHeight(25)

        self.LE_Pow.setFixedWidth(100)
        self.LE_Pow.setFixedHeight(25)

        ### Rezpt-Funktionen:
        self.btn_rezept_start.setFixedWidth(100)
        self.btn_rezept_ende.setFixedWidth(100)
        self.cb_Rezept.setFixedWidth(100)
        #________________________________________
        ## Border Sichtbar:
        if Frame_Anzeige:    
            self.layer_widget.setStyleSheet("border: 1px solid black;")

        #---------------------------------------
        # Kurven:
        #---------------------------------------
        ## PID-Modus:
        ### Istwert:
        PID_Export_Ist = ''
        if self.origin[0] == 'V':        PID_Label_Ist = PID_Von_2[sprache]
        elif self.origin[0] == 'M':     
            PID_Label_Ist = PID_Von_1[sprache]
            PID_Export_Ist = PID_Zusatz[sprache]
        else:                       PID_Label_Ist = PID_Von_2[sprache]
        ### Sollwert
        PID_Export_Soll = ''
        if self.origin[1] == 'V':        PID_Label_Soll = PID_Von_2[sprache]
        elif self.origin[1] == 'M':     
            PID_Label_Soll = PID_Von_1[sprache]
            PID_Export_Soll = PID_Zusatz[sprache]
        else:                       PID_Label_Soll = PID_Von_2[sprache]

        ## Kurven-Namen:
        kurv_dict = {                                                                   # Wert: [Achse, Farbe/Stift, Name]
            'IWT':    ['a1', pg.mkPen(self.color[0], width=2),                           f'{eurotherm} - {T_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'SWT':    ['a1', pg.mkPen(self.color[1]),                                    f'{eurotherm} - {T_einzel_str[self.sprache]}<sub>{sollwert_str[self.sprache]}</sub>'],
            'IWOp':   ['a2', pg.mkPen(self.color[2], width=2),                           f'{eurotherm} - {P_einzel_str[self.sprache]}<sub>{istwert_str[self.sprache]}</sub>'],
            'oGT':    ['a1', pg.mkPen(color=self.color[0], style=Qt.DashLine),           f'{eurotherm} - {T_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGT':    ['a1', pg.mkPen(color=self.color[0], style=Qt.DashDotDotLine),     f'{eurotherm} - {T_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'oGOp':   ['a2', pg.mkPen(color=self.color[2], style=Qt.DashLine),           f'{eurotherm} - {P_einzel_str[self.sprache]}<sub>{ober_Grenze_str[self.sprache]}</sub>'],
            'uGOp':   ['a2', pg.mkPen(color=self.color[2], style=Qt.DashDotDotLine),     f'{eurotherm} - {P_einzel_str[self.sprache]}<sub>{unter_Grenze_str[self.sprache]}</sub>'],
            'RezT':   ['a1', pg.mkPen(color=self.color[3], width=3, style=Qt.DotLine),   f'{eurotherm} - {rezept_Label_str[self.sprache]}<sub>{T_einzel_str[self.sprache]}</sub>'],
            'RezOp':  ['a2', pg.mkPen(color=self.color[4], width=3, style=Qt.DotLine),   f'{eurotherm} - {rezept_Label_str[self.sprache]}<sub>{P_einzel_str[self.sprache]}</sub>'],
            'SWTPID': ['a1', pg.mkPen(self.color[5], width=2, style=Qt.DashDotLine),     f'{PID_Label_Soll} - {T_einzel_str[self.sprache]}<sub>{PID_Export_Soll}{sollwert_str[self.sprache]}</sub>'], 
            'IWTPID': ['a1', pg.mkPen(self.color[6], width=2, style=Qt.DashDotLine),     f'{PID_Label_Ist} - {T_einzel_str[self.sprache]}<sub>{PID_Export_Ist}{istwert_str[self.sprache]}</sub>'],
        }

        ## Kurven erstellen:
        ist_drin_list = []                                                              # Jede Kurve kann nur einmal gesetzt werden!
        self.kurven_dict = {}
        for legend_kurve in self.legenden_inhalt:
            if legend_kurve in kurv_dict and not legend_kurve in ist_drin_list:
                if kurv_dict[legend_kurve][0] == 'a1':
                    curve = self.typ_widget.plot.achse_1.plot([], pen=kurv_dict[legend_kurve][1], name=kurv_dict[legend_kurve][2])
                    if self.typ_widget.legend_pos.upper() == 'OUT':
                        self.typ_widget.plot.legend.addItem(curve, curve.name())
                elif kurv_dict[legend_kurve][0] == 'a2':
                    curve = pg.PlotCurveItem([], pen=kurv_dict[legend_kurve][1], name=kurv_dict[legend_kurve][2])
                    self.typ_widget.plot.achse_2.addItem(curve)
                    if self.typ_widget.legend_pos.upper() == 'OUT' or self.typ_widget.legend_pos.upper() == 'IN':
                        self.typ_widget.plot.legend.addItem(curve, curve.name())
                self.kurven_dict.update({legend_kurve: curve})
                ist_drin_list.append(legend_kurve)
            elif not legend_kurve in kurv_dict:
                logger.warning(f'{self.device_name} - {self.Log_Text_Kurve[self.sprache]} {legend_kurve}')

        ## Checkboxen erstellen:
        self.kurven_side_legend         = {}

        if self.typ_widget.legend_pos.upper() == 'SIDE':
            for kurve in self.kurven_dict:
                widget, side_checkbox = self.GUI_Legend_Side(kurv_dict[kurve][2].split(' - '), kurv_dict[kurve][1], kurv_dict[kurve][0])
                if self.typ_widget.Side_Legend_position.upper() == 'RL':
                    if kurv_dict[kurve][0] == 'a1': self.typ_widget.legend_achsen_Links_widget.layout.addWidget(widget)
                    elif kurv_dict[kurve][0] == 'a2': self.typ_widget.legend_achsen_Rechts_widget.layout.addWidget(widget)
                elif self.typ_widget.Side_Legend_position.upper() == 'R':
                    self.typ_widget.legend_achsen_Rechts_widget.layout.addWidget(widget)
                elif self.typ_widget.Side_Legend_position.upper() == 'L':
                    self.typ_widget.legend_achsen_Links_widget.layout.addWidget(widget)
                self.kurven_side_legend.update({side_checkbox: kurve})

        ## Kurven-Daten-Listen:
        ### Messgrößen:
        self.opList         = []
        self.istTpList      = []
        self.sollTpList     = []
        self.sollTPID       = []
        self.istTPID        = []
        ### Grenzen
        self.ToGList        = []
        self.TuGList        = []
        self.OpoGList       = []
        self.OpuGList       = []

        #---------------------------------------
        # Dictionarys:
        #---------------------------------------
        self.curveDict      = {'IWT': '', 'SWT': '', 'IWOp': '', 'oGT':'', 'uGT':'', 'oGOp':'', 'uGOp':'', 'RezT':'', 'RezOp':'', 'SWTPID':'', 'IWTPID':''}
        for kurve in self.kurven_dict:
                self.curveDict[kurve] = self.kurven_dict[kurve] 
        self.labelDict      = {'IWT': self.La_IstTemp_wert,                                                'IWOp': self.La_IstPow_wert,      'SWT': self.La_SollTemp_wert}                              # Label
        self.labelUnitDict  = {'IWT': self.T_unit_einzel[self.sprache],                                    'IWOp': self.P_unit_einzel[self.sprache]}                                                    # Einheit
        self.listDict       = {'IWT': self.istTpList,       'SWT': self.sollTpList,                        'IWOp': self.opList,              'SWTPID':self.sollTPID,        'IWTPID':self.istTPID}      # Werte-Listen
        self.grenzListDict  = {'oGT': self.ToGList,         'uGT': self.TuGList,    'oGOp': self.OpoGList, 'uGOp': self.OpuGList}
        self.grenzValueDict = {'oGT': self.oGST,            'uGT': self.uGST,       'oGOp': self.oGOp,     'uGOp': self.uGOp}

        ## Plot-Skalierungsfaktoren:
        self.skalFak_dict = {}
        for size in self.curveDict:
            if 'WT' in size:
                self.skalFak_dict.update({size: self.skalFak['Temp']})
            if 'WOp' in size:
                self.skalFak_dict.update({size: self.skalFak['Op']})

        #---------------------------------------
        # Timer:
        #---------------------------------------
        ## Rezept-Timer
        self.RezTimer = QTimer()
        self.RezTimer.timeout.connect(self.Rezept)

        #---------------------------------------
        # Bei Init False sperren:
        #---------------------------------------
        if not self.init:
            self.RB_choise_Temp.setEnabled(False)
            self.RB_choise_Pow.setEnabled(False)

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
                                       "QCheckBox::indicator{ border : 1px solid black;}\n")
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
        checkbox = self.sender()                        # Klasse muss von QWidget erben, damit sender() Funktioniert - Durch die Methode kann geschaut werden welche Checkbox betätigt wurde!
        kurve = self.kurven_side_legend[checkbox]
        if checkbox.isChecked():
            self.curveDict[kurve].setVisible(True)
        else:
            self.curveDict[kurve].setVisible(False)

    ##########################################
    # Fehlermedlung:
    ##########################################
    def Fehler_Output(self, Fehler, error_Message_Log_GUI = '', error_Message_Ablauf = '', device = ''):
        ''' Erstelle Fehler-Nachricht für GUI, Ablaufdatei und Logging
        Args:
            Fehler (bool):                  False -> o.k. (schwarz), True -> Fehler (rot, bold)
            error_Message_Log_GUI (str):    Nachricht die im Log und der GUI angezeigt wird
            error_Message_Ablauf (str):     Nachricht für die Ablaufdatei
            device (str):                   Wenn ein anderes Gerät genutzt wird (z.B. PID)
        ''' 
        if device == '':
            device_name = self.device_name
        else:
            device_name = device
        if Fehler:
            self.La_error.setText(self.err_0_str[self.sprache])
            self.La_error.setToolTip(error_Message_Log_GUI)  
            self.La_error.setStyleSheet(f"color: red; font-weight: bold")
            log_vorberietung = error_Message_Log_GUI.replace("\n"," ")
            logger.error(f'{device_name} - {log_vorberietung}')
        else:
            self.La_error.setText(self.err_13_str[self.sprache])
            self.La_error.setToolTip('')
            self.La_error.setStyleSheet(f"color: black; font-weight: normal")
        if not error_Message_Ablauf == '':
                self.add_Text_To_Ablauf_Datei(f'{device_name} - {error_Message_Ablauf}') 

    ##########################################
    # Reaktion auf Radio-Butttons:
    ##########################################
    def BlassOutTemp(self, selected):
        ''' Leistungs Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_25_str[self.sprache]}')
            self.LE_Pow.setEnabled(True)
            self.LE_Temp.setEnabled(False)

            # Modus wechseln (Automatischer Modus):
            self.write_task['Auto_Mod'] = False      
            self.write_task['Manuel_Mod'] = True
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_26_str[self.sprache]}')           

    def BlassOutPow(self, selected):  
        ''' Temperatur Eingabefeld ist Verfügbar '''
        if selected:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_27_str[self.sprache]}')
            self.LE_Temp.setEnabled(True)
            self.LE_Pow.setEnabled(False)

            # Modus wechseln (Manueller Modus):
            self.write_task['Manuel_Mod'] = False 
            self.write_task['Auto_Mod'] = True 
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_28_str[self.sprache]}')     
    
    ##########################################
    # Reaktion auf Checkbox:
    ##########################################
    def PID_ON_OFF(self):  
        '''PID-Modus toggeln'''                     
        if self.PID_cb.isChecked():
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_1[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID'] = True
            self.write_task['Manuel_Mod'] = True
            self.write_task['Operating point'] = False  # Beim Umschalten keine Sollwerte anpassen!
            self.write_task['Soll-Temperatur'] = False

            # GUI ändern:
            self.RB_choise_Temp.setChecked(True) 
            if self.color_Aktiv:
                self.labelDict['IWT'].setStyleSheet(f"color: {self.color[6]}")  # Istwert PID
                self.La_IstTemp_text.setStyleSheet(f"color: {self.color[6]}")
                self.labelDict['SWT'].setStyleSheet(f"color: {self.color[5]}")  # Sollwert PID
                self.RB_choise_Temp.setStyleSheet(f"color: {self.color[5]}")

            # Zugriff freigeben:
            self.LE_Temp.setEnabled(True)

            # Zugriff sperren:
            self.LE_Pow.setEnabled(False)
            self.RB_choise_Pow.setEnabled(False)
            self.RB_choise_Temp.setEnabled(False)
            # Bei Multilog-Sollwert:
            if self.origin[1] == 'M':
                self.btn_rezept_start.setEnabled(False)
                self.btn_rezept_ende.setEnabled(False)
                self.cb_Rezept.setEnabled(False)
                self.LE_Temp.setEnabled(False)
                self.btn_send_value.setEnabled(False)
        else:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_PID_2[self.sprache]}')
            # Aufgaben setzen:
            self.write_task['PID'] = False
            self.write_task['Operating point'] = True  # Beim Umschalten keine Sollwerte anpassen bzw. OP auf einen Wert setzen!
            value = self.PID_Mode_Switch_Value
            if value > self.oGOp or value < self.uGOp:
                logger.warning(f"{self.device_name} - {self.Log_Text_PID_Ex[self.sprache]}") 
                self.write_value['Rez_OPTemp'] = self.uGOp
            else:
                self.write_value['Rez_OPTemp'] = value
            self.write_task['Soll-Temperatur'] = False

            # Zugriff freigeben:
            self.LE_Pow.setEnabled(True)
            self.LE_Temp.setEnabled(False)
            self.RB_choise_Pow.setEnabled(True)
            self.RB_choise_Temp.setEnabled(True)
            self.RB_choise_Pow.setChecked(True) 
            # Bei Multilog-Sollwert:
            if self.origin[1] == 'M':
                self.btn_rezept_start.setEnabled(True)
                self.btn_rezept_ende.setEnabled(True)
                self.cb_Rezept.setEnabled(True)
                self.btn_send_value.setEnabled(True)

            # GUI ändern:
            if self.color_Aktiv:
                self.labelDict['IWT'].setStyleSheet(f"color: {self.color[0]}")  # Istwert PID
                self.La_IstTemp_text.setStyleSheet(f"color: {self.color[0]}")  
                self.labelDict['SWT'].setStyleSheet(f"color: {self.color[1]}")  # Sollwert PID
                self.RB_choise_Temp.setStyleSheet(f"color: {self.color[1]}")            

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
            if self.RB_choise_Temp.isChecked():
                sollwert = self.LE_Temp.text().replace(",", ".")
                if not self.PID_cb.isChecked():
                    self.write_task['Soll-Temperatur'] = True
                self.write_task['Operating point'] = False
                oG, uG = self.oGST, self.uGST
                if not self.PID_cb.isChecked():
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_29_str[self.sprache]}')
                else:
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_29_2_str[self.sprache]}')
            # Wenn der Radio-Button der Ausgangsleistung gewählt ist:
            else:
                sollwert = self.LE_Pow.text().replace(",", ".")
                self.write_task['Operating point'] = True
                self.write_task['Soll-Temperatur'] = False
                oG, uG = self.oGOp, self.uGOp
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_30_str[self.sprache]}')
            # Kontrolliere die Eingabe im Eingabefeld:
            sollwert = self.controll_value(sollwert, oG, uG)
            # Ist alles in Ordnung, dann Gebe dem Programm Bescheid, das es den Wert schreiben kann:
            if sollwert != -1:
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = sollwert
                else:
                    self.write_value['Sollwert'] = sollwert
            else:
                self.write_task['Operating point'] = False
                self.write_task['Soll-Temperatur'] = False
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
        if self.init:
            if n == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_90_str[self.sprache]}')
            self.PID_cb.setChecked(False)
            self.PID_ON_OFF()
            self.RezEnde(excecute=n)
            self.BlassOutTemp(True)
            self.RB_choise_Pow.setChecked(True)
            self.LE_Pow.setText(str(0))
            self.write_task['Operating point'] = True
            self.write_value['Sollwert'] = 0
            #self.write_value['PID-Sollwert'] = 0
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def update_Limit(self):
        '''Lese die Config und Update die Limits'''

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Yaml erneut laden:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        with open(self.config_dat, encoding="utf-8") as f:  
            config = yaml.safe_load(f)
            logger.info(f"{self.device_name} - {self.Log_Text_205_str[self.sprache]} {config}")
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Konfiguration prüfen:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ### Solltemperatur:
        try: self.oGST = config['devices'][self.device_name]["limits"]['maxTemp'] 
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|maxTemp {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGST = 1       
        #//////////////////////////////////////////////////////////////////////
        try: self.uGST = config['devices'][self.device_name]["limits"]['minTemp']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|minTemp {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGST = 0
        #//////////////////////////////////////////////////////////////////////
        if not type(self.oGST) in [float, int] or not self.oGST >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} maxTemp - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGST)}')
            self.oGST = 1
        if not type(self.uGST) in [float, int] or not self.uGST >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} minTemp - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGST)}')
            self.uGST = 0
        if self.oGST <= self.uGST:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_11[self.sprache]})')
            self.uGST = 0
            self.oGST = 1
        #//////////////////////////////////////////////////////////////////////
        ### Ausgangsleistung (Operating Point)
        try: self.oGOp = config['devices'][self.device_name]["limits"]['opMax']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|opMax {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGOp = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGOp = config['devices'][self.device_name]["limits"]['opMin']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} limits|opMin {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGOp = 0
        #//////////////////////////////////////////////////////////////////////
        if not type(self.oGOp) in [float, int] or not self.oGOp >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} opMax - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGOp)}')
            self.oGOp = 1
        if not type(self.uGOp) in [float, int] or not self.uGOp >= 0:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} opMin - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] (Positiv) - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGOp)}')
            self.uGOp = 0
        if self.oGOp <= self.uGOp:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_13[self.sprache]})')
            self.uGOp = 0
            self.oGOp = 1
        #//////////////////////////////////////////////////////////////////////
        ### PID-Input-Output:
        try: self.oGx = config['devices'][self.device_name]['PID']['Input_Limit_max']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_max {self.Log_Pfad_conf_5[self.sprache]} 1')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.oGx = 1
        #//////////////////////////////////////////////////////////////////////
        try: self.uGx = self.uGx = config['devices'][self.device_name]['PID']['Input_Limit_min']
        except Exception as e: 
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} PID|Input_Limit_min {self.Log_Pfad_conf_5[self.sprache]} 0')
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
            logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            self.uGx = 0
        #//////////////////////////////////////////////////////////////////////
        if not type(self.oGx) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_max - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 1 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.oGx)}')
            self.oGx = 1
        if not type(self.uGx) in [float, int]:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} Input_limit_min - {self.Log_Pfad_conf_2_1[self.sprache]} [float, int] - {self.Log_Pfad_conf_3[self.sprache]} 0 - {self.Log_Pfad_conf_8_1[self.sprache]} {type(self.uGx)}')
            self.uGx = 0
        if self.oGx <= self.uGx:
            logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_9[self.sprache]} 0 {self.Log_Pfad_conf_10[self.sprache]} 1 ({self.Log_Pfad_conf_12[self.sprache]})')
            self.uGx = 0
            self.oGx = 1

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Weiterleiten:
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.write_task['Update Limit']     = True
        self.write_value['Limits']          = [self.oGOp, self.uGOp, self.oGx, self.uGx]

        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_2[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGST} {self.Log_Text_LB_4[self.sprache]} {self.oGST}{self.T_unit_einzel[self.sprache]}')
        logger.info(f'{self.device_name} - {self.Log_Text_LB_1[self.sprache]} {self.Log_Text_LB_3[self.sprache]} ({self.Log_Text_LB_5[self.sprache]}): {self.uGOp} {self.Log_Text_LB_4[self.sprache]} {self.oGOp} {self.P_unit_einzel[self.sprache]}')

        if not self.Safety and self.init:
            self.write_task['Write_HO'] = True
            self.write_value['HO'] = self.oGOp
        elif self.Safety:
            logger.warning(f"{self.device_name} - {self.Log_Text_242_str[self.sprache]}")
            self.typ_widget.Message(self.puF_HO_str[self.sprache], 3, 600)
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def Lese_HO(self):
        '''Lese HO neu aus!'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_80_str[self.sprache]}')
            self.write_task['Read_HO'] = True
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def Read_PID(self):
        '''Lese HO neu aus!'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_80_3_str[self.sprache]}')
            self.write_task['Read_PID'] = True
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])
    
    def Write_PID(self):
        '''Entnehme der Config die PID-Werte für Eurotherm und ändere diese!'''
        if self.init:
            self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_80_2_str[self.sprache]}')
            # Config auslesen:
            with open(self.config_dat, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f'{self.device_name} - {self.Log_Text_EPID_1[self.sprache]} {config}')
            # PID-Werte lesen:
            try:
                P = round(float(str(config['devices'][self.device_name]['PID-Device']['PB']).replace(',','.')),1)
                I = round(float(str(config['devices'][self.device_name]['PID-Device']['TI']).replace(',','.')),0)
                D = round(float(str(config['devices'][self.device_name]['PID-Device']['TD']).replace(',','.')),0)
                error = False
                for n in [P, I, D]:
                    if n > 99999 or n < 0:
                        self.Fehler_Output(1, f'{self.Log_Text_EPID_2[self.sprache]} {n} {self.Log_Text_EPID_3[self.sprache]}')
                        logger.warning(f'{self.Log_Text_EPID_2[self.sprache]} {n} {self.Log_Text_EPID_3[self.sprache]}')
                        error = True
                if not error:
                    self.write_task['PID-Update']  = True
                    self.write_value['PID-Update'] = [P, I, D]
                    self.Fehler_Output(0)
            except Exception as e:
                self.write_task['PID-Update']  = False
                logger.warning(f'{self.device_name} - {self.Log_Text_EPID_4[self.sprache]}')
                self.Fehler_Output(1, self.Log_Text_EPID_5[self.sprache])
                logger.exception(f'{self.device_name} - {self.Log_Text_EPID_6[self.sprache]}')     
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    ##########################################
    # Betrachtung der Labels und Plots:
    ##########################################
    def update_GUI(self, value_dict, x_value):
        ''' Update der GUI, Plot und Label!

        Args:
            value_dict (dict):  Dictionary mit den aktuellen Werten!
            x_value (list):     Werte für die x-Achse
        '''

        ## Kurven Update:
        self.data.update({'Time' : x_value[-1]})                    
        self.data.update(value_dict)   
        
        for messung in value_dict:
            if not 'SWT' in messung:
                if 'IWT' in messung:
                    if messung == 'IWT' and not self.PID_cb.isChecked():   self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}') 
                    elif messung == 'IWTPID' and  self.PID_cb.isChecked(): self.labelDict['IWT'].setText(f'{value_dict[messung]} {self.labelUnitDict["IWT"]}')
                else:
                    self.labelDict[messung].setText(f'{value_dict[messung]} {self.labelUnitDict[messung]}')
            else:
                if messung == 'SWT' and not self.PID_cb.isChecked():   self.labelDict[messung].setText(f'({value_dict[messung]})') 
                elif messung == 'SWTPID' and  self.PID_cb.isChecked(): self.labelDict['SWT'].setText(f'({value_dict[messung]})') 
            self.listDict[messung].append(value_dict[messung])
            if not self.curveDict[messung] == '':
                faktor = self.skalFak_dict[messung]
                y = [a * faktor for a in self.listDict[messung]]
                self.curveDict[messung].setData(x_value, y)

        ## Grenz-Kurven:
        ### Update Grenzwert-Dictionary:
        self.grenzValueDict['oGT']  = self.oGST * self.skalFak['Temp']
        self.grenzValueDict['uGT']  = self.uGST * self.skalFak['Temp']
        self.grenzValueDict['oGOp'] = self.oGOp * self.skalFak['Op']
        self.grenzValueDict['uGOp'] = self.uGOp * self.skalFak['Op']
        ### Update-Kurven:
        for kurve in self.kurven_dict:
            if kurve in self.grenzListDict:
                self.grenzListDict[kurve].append(float(self.grenzValueDict[kurve]))
                self.kurven_dict[kurve].setData(x_value, self.grenzListDict[kurve])
        
    def Pop_Up_Start_Later(self):
        ## Pop-Up-Fenster verzögert zum Start starten:
        if self.start_later:
            self.start_later = False
            self.typ_widget.Message(self.puF_HO_str_2[self.sprache], 3, 450) 
    
    ########################################## 
    # Reaktion auf Initialisierung:
    ##########################################
    def init_device(self):
        ''' Initialisierung soll durch geführt werden '''
        self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_23_str[self.sprache]}')
        self.write_task['Init'] = True
        if self.Safety: 
            self.typ_widget.Message(self.puF_HO_str_2[self.sprache], 3, 450)
            
    def init_controll(self, init_okay, menu):
        ''' Anzeige auf GUI ändern 
        
        Args:
            init_okay (bool):   Ändert die Init-Variable und das Icon in der GUI, je nach dem wie das Gerät entschieden hat!
            menu (QAction):     Menü Zeile in der das Icon geändert werden soll!               
        '''
        if init_okay:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_Okay.png"))
            self.RB_choise_Temp.setEnabled(True)
            self.RB_choise_Pow.setEnabled(True)
            self.Start() 
            self.Fehler_Output(0)
            self.init = True
        else:
            menu.setIcon(QIcon("./vifcon/icons/p_Init_nicht_Okay.png"))
            self.init = False

    def Start(self):
        '''Funktion die nur beim Start beachtet werden muss (Init oder Start)'''
        if self.startMode == 'Manuel':
            self.RB_choise_Pow.setChecked(True)
            self.LE_Temp.setEnabled(False)
            self.LE_Pow.setEnabled(True)
        elif self.startMode == 'Auto': 
            self.RB_choise_Temp.setChecked(True)
            self.LE_Temp.setEnabled(True)
            self.LE_Pow.setEnabled(False)

    ##########################################
    # Reaktion auf Rezepte:
    ##########################################
    def RezStart(self, execute = 1):
        ''' Rezept wurde gestartet '''
        if self.init:
            if not self.Rezept_Aktiv:
                if execute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_87_str[self.sprache]}')
                elif execute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_85_str[self.sprache]}')
            
                # Variablen:
                self.step = 0                           # Rezeptschritte
                self.Rezept_Aktiv = True                # Rezept ist Aktiv

                # Kurve erstellen:
                error = self.RezKurveAnzeige()          # Überprüfe Rezept und Erstelle Plot
                if self.cb_Rezept.currentText() == '------------':
                    self.Fehler_Output(1, self.err_15_str[self.sprache])
                    error = True
                
                if not error:
                    # Rezept Log-Notiz:
                    logger.info(f'{self.device_name} - {self.Log_Text_39_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}')
                    logger.info(f'{self.device_name} - {self.Log_Text_40_str[self.sprache]} {self.rezept_daten}')
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_24_str[self.sprache]} {self.cb_Rezept.currentText()} {self.rezept_datei}') 

                    # Erstes Element senden:
                    if self.PID_cb.isChecked():
                        self.write_value['PID-Sollwert'] = self.value_list[self.step]
                    else:
                        self.write_value['Sollwert'] = self.value_list[self.step]

                    if self.RB_choise_Temp.isChecked():
                        self.write_task['Soll-Temperatur'] = True
                    else:
                        self.write_task['Operating point'] = True

                    if self.PID_cb.isChecked():
                        self.write_task['Soll-Temperatur'] = False

                    # OP Als Erster Schritt:
                    if self.Art_list[self.step] == 'op':
                        if self.PID_cb.isChecked():
                            self.write_task['PID_Rezept_Mode_OP'] = True
                            self.write_value['PID_Rez'] = self.value_list_op[self.step]
                        else:
                            self.write_task['Auto_Mod'] = False
                            self.write_task['Manuel_Mod'] = True
                            if not self.value_list_op[self.step] == 'IST':
                                self.write_task['Operating point'] = True
                                self.write_value['Rez_OPTemp'] = self.value_list_op[self.step]
                            self.op_Mod = True

                    # Elemente GUI sperren:
                    self.cb_Rezept.setEnabled(False)
                    self.btn_rezept_start.setEnabled(False)
                    self.RB_choise_Temp.setEnabled(False)
                    self.RB_choise_Pow.setEnabled(False)
                    self.btn_send_value.setEnabled(False)
                    self.Auswahl.setEnabled(False)
                    self.PID_cb.setEnabled(False)

                    # Timer Starten:
                    self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))
                    self.RezTimer.start()
                    self.Fehler_Output(0)
                else:
                    self.Rezept_Aktiv = False
                    self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_88_str[self.sprache]}')
            else:
                self.Fehler_Output(1, self.err_19_str[self.sprache], self.Text_84_str[self.sprache])
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def RezEnde(self, rez_End=False, excecute = 1):
        ''' Rezept wurde/wird beendet 
        Args:
            rez_End (Bool):   Wenn der Knopf betätigt wird, dann muss Eurotherm Rampe ausgeschaltet werden!
        '''
        if self.init:
            if self.Rezept_Aktiv:
                if excecute == 1: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_81_str[self.sprache]}')
                elif excecute == 2: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_82_str[self.sprache]}')
                elif excecute == 3: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_83_str[self.sprache]}')
                elif excecute == 4: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_86_str[self.sprache]}')
                elif excecute == 5: self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_91_str[self.sprache]}')

                # Elemente GUI entsperren:
                self.cb_Rezept.setEnabled(True)
                self.PID_cb.setEnabled(True)
                self.btn_rezept_start.setEnabled(True)
                self.btn_send_value.setEnabled(True)
                self.Auswahl.setEnabled(True)
                
                if not self.PID_cb.isChecked():
                    self.RB_choise_Temp.setEnabled(True)
                    self.RB_choise_Pow.setEnabled(True)

                # Variablen:
                self.Rezept_Aktiv = False
                self.write_task['PID_Rezept_Mode_OP'] = False
                self.write_value['PID_Rez'] = -1

                ## Am Ende oder bei Abbruch:
                ## Eurotherm Rampe :
                if self.Art_list[self.step] == 'er' and not rez_End:
                    self.write_task['EuRa_Reset'] = True
                elif self.Art_list[self.step] == 'er' and rez_End:
                    self.write_task['Soll-Temperatur'] = True
                    self.write_value['Sollwert'] = self.value_list[-1]
                ## Leistungssprung in Temperatur-Rezept:
                elif self.Art_list[self.step] == 'op':
                    self.write_task['Auto_Mod'] = True
                    self.write_task['Manuel_Mod'] = False

                # Auto Range
                self.typ_widget.plot.AutoRange()

                # Nachricht:
                self.Fehler_Output(0)

                # Timer stoppen:
                self.RezTimer.stop()
            else:
                self.add_Text_To_Ablauf_Datei(f'{self.device_name} - {self.Text_89_str[self.sprache]}')
        else:
            self.Fehler_Output(1, self.err_4_str[self.sprache])

    def Rezept(self):
        ''' Rezept Schritt wurde beendet, Vorbereitung und Start des neuen '''
        self.step += 1
        # Ende Rezept:
        if self.step > len(self.time_list) - 1: 
            self.step = self.step - 1
            self.RezEnde(True, 2)
        # Nächster Schritt:
        else:
            self.RezTimer.setInterval(int(abs(self.time_list[self.step]*1000)))

            # Nächstes Element senden:
            if self.Art_list[self.step] == 'r' or self.Art_list[self.step] == 's' or 'op' in self.Art_list[self.step]:
                ## Kontrolliere ob der vorherige Schritt ein op-Schritt war:
                if self.op_Mod:
                    self.write_task['Manuel_Mod'] = False
                    self.write_task['Auto_Mod'] = True
                    self.op_Mod = False

                ## Senden den aktuellen Sollwert:
                if self.PID_cb.isChecked():
                    self.write_value['PID-Sollwert'] = self.value_list[self.step]
                else:
                    self.write_value['Sollwert'] = self.value_list[self.step]
                if self.RB_choise_Temp.isChecked():
                    self.write_task['Soll-Temperatur'] = True
                else:
                    self.write_task['Operating point'] = True
                
                if self.PID_cb.isChecked():
                        self.write_task['Soll-Temperatur'] = False
                
                ## Wenn op-Schritt, dann stelle Manuellen Modus ein und sende den OP-Wert:
                if 'op' in self.Art_list[self.step]:
                    if self.PID_cb.isChecked():
                        self.write_task['PID_Rezept_Mode_OP'] = True
                        self.write_value['PID_Rez'] = self.value_list_op[self.step]
                    else:
                        self.write_task['Auto_Mod'] = False
                        self.write_task['Manuel_Mod'] = True
                        if not self.value_list_op[self.step] == 'IST':
                            self.write_task['Operating point'] = True
                            self.write_value['Rez_OPTemp'] = self.value_list_op[self.step]
                        self.op_Mod = True
                else:
                    self.write_task['PID_Rezept_Mode_OP'] = False
                    self.write_value['PID_Rez'] = -1
            elif self.Art_list[self.step] == 'er':
                ## Kontrolliere ob der vorherige Schritt ein op-Schritt war:
                if self.op_Mod:
                    self.write_task['Manuel_Mod'] = False
                    self.write_task['Auto_Mod'] = True
                    self.op_Mod = False
                ## Löse die Eurotherm-Rampe aus
                self.write_value['EuRa_Soll'] = self.value_list[self.step]
                self.write_value['EuRa_m'] = self.Steigung[self.step]   
                self.write_task['EuRa'] = True
    
    def Rezept_lesen_controll(self):
        ''' Rezept wird ausgelesen und kontrolliert. Bei Fehler werden die Fehlermeldungen beschrieben auf der GUI. 
        
        Return:
            error (Bool):   Fehler vorhanden oder nicht
        '''
        #////////////////////////////////////////////////////////////
        # Variablen:
        #////////////////////////////////////////////////////////////
        error = False                   # Fehler-Variable - False = Kein Fehler, Rezept ist ausführbar!
        self.time_list      = []        # Timer-Zeiten
        self.value_list     = []        # Sollwerte
        self.value_list_op  = []        # Sollwerte für OP, im Fall eines Leistungssprungs im Temperaturrezept
        self.Art_list       = []        # Speichert ob Eurotherm-Rampe, Rampe oder Sprung
        self.Steigung       = []        # Rampensteigungen (für er benötigt)

        ## Grenzwerte:
        if self.RB_choise_Temp.isChecked():
            uG = self.uGST  
            oG = self.oGST
            ak_value = self.ak_value['IWT'] if not self.ak_value == {} and self.StartRampe == 'IST' else (self.ak_value['SWT'] if not self.ak_value == {} and self.StartRampe == 'SOLL' else (self.ak_value['IWT'] if not self.StartRampe == 'IST' or self.StartRampe == 'SOLL' and not self.ak_value == {} else 0))
        else:
            uG = self.uGOp
            oG = self.oGOp
            ak_value = self.ak_value['IWOp'] if not self.ak_value == {} else 0
        
        #////////////////////////////////////////////////////////////
        # Rezept lesen:
        #////////////////////////////////////////////////////////////
        ## Combobox auslesen:
        rezept = self.cb_Rezept.currentText()  
        ## Bearbeitung des Rezepts:
        if not rezept == '------------':
            ## Rezept aus Datei oder in Config:
            ak_rezept = self.rezept_config[rezept]
            if 'dat' in ak_rezept:
                try:
                    with open(f'vifcon/rezepte/{ak_rezept["dat"]}', encoding="utf-8") as f:
                        rez_dat = yaml.safe_load(f)
                    self.rezept_datei = f'({ak_rezept["dat"]})'
                except Exception as e:
                    self.Fehler_Output(1, self.err_10_str[self.sprache])
                    logger.exception(self.Log_Text_Ex1_str[self.sprache])
                    return False
            else:
                rez_dat = ak_rezept
                self.rezept_datei = '(Config-Datei)'
            ## Speichere aktuelle Daten des Rezepts für Logging:
            self.rezept_daten = rez_dat
            #///////////////////////////////////////////////////////////////////////////////
            ## Fehlermeldung: 
            ### Kontrolle des Leistungsrezeptes -> op und er nicht möglich
            ### PID-Modus -> op, opr und er nicht möglich
            #//////////////////////////////////////////////////////////////////////////////
            if not self.RB_choise_Temp.isChecked():
                for n in rez_dat:
                    if 'er' in rez_dat[n]:  
                        logger.warning(f'{self.device_name} - {self.Log_Text_182_str[self.sprache]}')
                        self.Fehler_Output(1, self.err_16_str[self.sprache])
                        return False
                    if 'op' in rez_dat[n]:
                        logger.warning(f'{self.device_name} - {self.Log_Text_184_str[self.sprache]}')
                        self.Fehler_Output(1, self.err_17_str[self.sprache])
                        return False
            if self.PID_cb.isChecked():
                for segment in ['er']:
                    for n in rez_dat:
                        if segment in rez_dat[n]: 
                            logger.warning(f'{self.device_name} - {self.Log_Text_248_str[self.sprache]}')
                            self.Fehler_Output(1, self.err_20_str[self.sprache])
                            return False
            #////////////////////////////////////////////////////////////
            ## Ersten Eintrag prüfen (besondere Startrampe):
            #////////////////////////////////////////////////////////////
            first_line = rez_dat[list(rez_dat.keys())[0]].split(';')[2]
            ### der aktuelle Istwert wird als Sprung eingetragen in die Werte-Listen, wenn Messdaten vorliegen:
            if (first_line.strip() == 'r' or first_line.strip() == 'er') and not self.ak_value == {}:
                self.value_list.append(ak_value)    # Aktueller Istwert
                self.time_list.append(0)            # Rezept-Zeit Null Sekunden
                self.value_list_op.append(0)        # Rezept-Zeit für OP auch 0 s
                self.Art_list.append('s')           # Art des Rezepts: Sprung
                self.Steigung.append(0)             # keine Steigung
            ### Fehlermeldung, wenn keine Messdaten-vorliegen:
            elif first_line.strip() == 'r' and self.ak_value == {}:
                self.Fehler_Output(1, self.err_12_str[self.sprache])
                return False
            ### Bei der Eurotherm-Rampe wird bei keinen Messdaten von 20°C ausgegangen:
            elif first_line.strip() == 'er' and self.ak_value == {}:
                logger.warning(f'{self.device_name} - {self.Log_Text_181_str[self.sprache]}')
                self.value_list.append(20)      # Aktueller Istwert
                self.value_list_op.append(0)    # Rezept-Zeit Null Sekunden
                self.time_list.append(0)        # Rezept-Zeit für OP auch 0 s
                self.Art_list.append('s')       # Art des Rezepts: Sprung
                self.Steigung.append(0)         # keine Steigung
            #////////////////////////////////////////////////////////////
            ## Rezept Kurven-Listen erstellen:
            #////////////////////////////////////////////////////////////
            for n in rez_dat:
                ## Rezept-Schritt aufteilen:
                werte = rez_dat[n].split(';')
                ## Beachtung von Kommas (Komma zu Punkt):
                time = float(werte[0].replace(',', '.'))
                value = float(werte[1].replace(',', '.'))
                ## Grenzwert-Kontrolle (Aktuell-ausgewählte Größe):
                if value < uG or value > oG:
                    error = True
                    self.Fehler_Output(1, f'{self.err_6_str[self.sprache]} {value} {self.err_7_str[self.sprache]} {uG} {self.err_3_str[self.sprache]} {oG}!')
                    break
                else:
                    self.Fehler_Output(0)
                #////////////////////////////////////////////////////////////
                ## Beachtung der Rampen-Art:
                #////////////////////////////////////////////////////////////
                ### Rampe:
                if werte[2].strip() == 'r':                        
                    rampen_config_step = float(werte[3].replace(',','.'))       # Zeitabstand für den Rampensprung (x-Achse)
                    rampen_bereich = value - self.value_list[-1]                # Bereich in dem die Rampe wirkt: Aktueller Wert - Letzten Eintrag (Rezept Stufe)
                    rampen_value = int(time/rampen_config_step)                 # Anzahl der Rampensprünge
                    rampen_step = rampen_bereich/rampen_value                   # Höhe des Sprungs je Rampensprung (y-Achse)
                    #### Berechnung der Listen Elemente:        
                    for rampen_n in range(1,rampen_value+1):        
                        if not rampen_n == rampen_value:        
                            ak_ramp = self.value_list[-1] + rampen_step         # Sollwert berechnen für eigene Rampe
                            self.value_list.append(round(ak_ramp,3))            # Runden: Eurotherm könnte bis 6 Nachkommerstellen, Display nur 2
                            self.time_list.append(rampen_config_step)           # Zeitwert eintragen
                        else: # Letzter Wert!
                            self.value_list.append(value)
                            self.time_list.append(rampen_config_step)    
                        self.Art_list.append('r')                               # Rampen-Art: r
                        self.value_list_op.append(0)                            # OP-Wert auf Null
                        self.Steigung.append(rampen_config_step)                # Steigungswert eintragen
                ### Eurotherm Rampe:
                elif werte[2].strip() == 'er': 
                    #### Berechnung der Steigung:
                    m = abs(round((self.value_list[-1] - value)/time, 3))       # Steigung: m = Delta(y)/Delta(x) -> m = (aktueller_Wert - Zielwert)/Segmentzeit   
                    #### Listen-füllen:
                    self.value_list.append(value)                               # Sollwert speichern
                    self.value_list_op.append(0)                                # OP-Wert auf Null
                    self.time_list.append(time)                                 # Zeit-Wert speichern
                    self.Art_list.append('er')                                  # Rampen-Art: er
                    self.Steigung.append(m)                                     # Steigungswert eintragen
                ### Leistungssprung in Temperatur-Rezept:
                elif werte[2].strip() == 'op':
                    self.value_list.append(value)                               # Sollwert (Temp) speichern
                    wert = werte[3]                                             # OP-Sollwert auslesen/Istwert halten
                    if wert.upper().strip() == 'IST':                           # Wenn IST an der Stelle steht, so soll nur der Modus gewechselt werden, sodas der Istwert gehalten wird!
                        OPvalue = wert.upper().strip()
                    else:                                                       # Bei einer Zahl wird dann auf diese gesprungen!
                        try:
                            OPvalue = float(wert.replace(',','.'))              
                            # Grenzwerrt-Kontrolle:
                            if OPvalue < self.uGOp or OPvalue > self.oGOp:              
                                error = True
                                self.Fehler_Output(1, f'{self.err_6_str[self.sprache]} {OPvalue} {self.err_7_str[self.sprache]} {self.uGOp} {self.err_3_str[self.sprache]} {self.oGOp}!')
                                break
                        except Exception as e:
                            self.Fehler_Output(1, self.err_18_str[self.sprache])
                            logger.exception(f"{self.device_name} - {self.Log_Text_185_str[self.sprache]}")
                    self.value_list_op.append(OPvalue)                          # OP-Wert anfügen
                    self.time_list.append(time)                                 # Zeit-Wert speichern
                    self.Art_list.append('op')                                  # Rampen-Art: op
                    self.Steigung.append(0)                                     # Steigung auf Null
                ### Leistungsrampe in Temperatur-Rezept:
                elif werte[2].strip() == 'opr':
                    rampen_config_step = float(werte[4].replace(',','.'))                                   # Zeitabstand für den Rampensprung (x-Achse)
                    try:
                        valueOP = werte[5].replace(',','.').strip()
                        if not valueOP == 'IST':
                            opRampStart = float(valueOP)
                    except:
                        opRampStart = 0
                    rampen_bereich = float(werte[3].replace(',','.')) - opRampStart                         # Bereich in dem die Rampe wirkt: Aktueller Wert - Letzten Eintrag (Rezept Stufe)
                    rampen_value = int(time/rampen_config_step)                                             # Anzahl der Rampensprünge
                    rampen_step = rampen_bereich/rampen_value                                               # Höhe des Sprungs je Rampensprung (y-Achse)
                    self.value_list_op.append(opRampStart)
                    self.time_list.append(rampen_config_step)                                               # Zeitwert eintragen
                    self.Art_list.append('opr')                                                             # Rampen-Art: opr
                    self.Steigung.append(rampen_config_step)                                                # Steigungswert eintragen
                    self.value_list.append(value)                                                           # Sollwert (Temp) speichern
                    #### Berechnung der Listen Elemente:        
                    for rampen_n in range(1,rampen_value+1):        
                        if not rampen_n == rampen_value:        
                            ak_ramp = self.value_list_op[-1] + rampen_step      # Sollwert berechnen für eigene Rampe
                            self.value_list_op.append(round(ak_ramp,3))         # Runden: Eurotherm könnte bis 6 Nachkommerstellen, Display nur 2
                            self.time_list.append(rampen_config_step)           # Zeitwert eintragen
                        else: # Letzter Wert!
                            self.value_list_op.append(float(werte[3].replace(',','.')))
                            self.time_list.append(rampen_config_step)    
                        self.Art_list.append('opr')                             # Rampen-Art: opr
                        self.Steigung.append(rampen_config_step)                # Steigungswert eintragen
                        self.value_list.append(value)                           # Sollwert (Temp) speichern
                ### Sprung:
                elif werte[2].strip() == 's':                                               
                    self.value_list.append(value)                               # Sollwert speichern                       
                    self.time_list.append(time)                                 # Zeit-Wert speichern
                    self.Art_list.append('s')                                   # Rampen-Art: s
                    self.Steigung.append(0)                                     # Steigung auf Null
                    self.value_list_op.append(0)                                # OP-Wert auf Null
                ### Falsches Segment:
                else:
                    self.Fehler_Output(1, f'{self.err_Rezept[self.sprache]} {werte[2].strip()} ({n})')
                    return False
        else:
            self.Fehler_Output(0)
        return error
    
    def RezKurveAnzeige(self):
        '''Soll die Rezept-Kurve anzeigen und erstellen!
        
        Return:
            error (bool):   Rezeptfehler
        '''
        #////////////////////////////////////////////////////////////
        # Pop-Up-Fenster:
        #////////////////////////////////////////////////////////////
        if not self.Rezept_Aktiv and not self.cb_Rezept.currentText() == '------------':
            self.typ_widget.Message(self.puF_RezeptAnz_str[self.sprache], 3, 450)

        #////////////////////////////////////////////////////////////
        # Variablen:
        #////////////////////////////////////////////////////////////
        error = False                                                                        # Kontrolle ob alles mit Rezept stimmt  

        ## Kurven zurücksetzen:
        self.RezTimeList = []
        self.RezValueList = [] 
        RezOPTimeList = []
        RezOPValueList = []

        ## Kurven Anzeige:
        anzeigeT  = True
        anzeigeOp = True                             
        try: self.curveDict['RezT'].setData(self.RezTimeList, self.RezValueList) 
        except: anzeigeT  = False
        try: self.curveDict['RezOp'].setData(self.RezTimeList, self.RezValueList)
        except: anzeigeOp = False

        ## Startzeit bestimmen:
        ak_time_1 = datetime.datetime.now(datetime.timezone.utc).astimezone()                # Aktuelle Zeit Absolut
        ak_time = round((ak_time_1 - self.typ_widget.start_zeit).total_seconds(), 3)         # Aktuelle Zeit Relativ

        ## Fehler-Kontrolle:
        try: error = self.Rezept_lesen_controll()
        except Exception as e:
            error = True
            logger.exception(f'{self.device_name} - {self.Log_Text_Ex1_str[self.sprache]}')
            self.Fehler_Output(1, self.err_10_str[self.sprache])

        if not error:
            #////////////////////////////////////////////////////////////
            # Kurve erstellen (Anzeige):
            #////////////////////////////////////////////////////////////
            i = 0
            for n in self.time_list:
                ## Steps/Sprünge:
                if self.Art_list[i] == 's' or self.Art_list[i] == 'r' or 'op' in self.Art_list[i]:  
                    # Punkt 1:
                    self.RezTimeList.append(ak_time)
                    self.RezValueList.append(self.value_list[i])
                    # Punkt 2:
                    self.RezTimeList.append(ak_time + n)
                    self.RezValueList.append(self.value_list[i])
                    if 'op' in self.Art_list[i] and not self.value_list_op[i] == 'IST':
                        if self.Art_list[i-1] == 's' or self.Art_list[i-1] == 'r' or self.Art_list[i-1] == 'er':
                            # Extra Punkt 1:
                            RezOPTimeList.append(ak_time)
                            RezOPValueList.append(0)
                        # Punkt 1:
                        RezOPTimeList.append(ak_time)
                        RezOPValueList.append(self.value_list_op[i])
                        # Punkt 2:
                        RezOPTimeList.append(ak_time+n)
                        RezOPValueList.append(self.value_list_op[i])
                        try: 
                            if self.Art_list[i+1] == 's' or self.Art_list[i+1] == 'r' or self.Art_list[i+1] == 'er':
                                # Extra Punkt 2:
                                RezOPTimeList.append(ak_time+n)
                                RezOPValueList.append(0)
                        except:
                            nix = 0
                ## Lineare Kurve:
                elif self.Art_list[i] == 'er':                          
                    # Punkt 1: 
                    self.RezTimeList.append(ak_time)
                    self.RezValueList.append(self.value_list[i-1])
                    # Punkt 2:
                    self.RezTimeList.append(ak_time + n)
                    self.RezValueList.append(self.value_list[i])
                ## nächsten Punkt vorbereiten:
                ak_time = ak_time + n
                i += 1

            #////////////////////////////////////////////////////////////
            # Kurve erstellen mit Skalierungsfaktor und Kurve Anzeigen:
            #////////////////////////////////////////////////////////////
            ## Temperatur oder Leistung:
            if self.RB_choise_Temp.isChecked():
                faktor = self.skalFak['Temp']
                y = [a * faktor for a in self.RezValueList]
                if anzeigeT:
                    self.curveDict['RezT'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_1.autoRange()
            else:
                faktor = self.skalFak['Op']
                y = [a * faktor for a in self.RezValueList]
                if anzeigeOp:
                    self.curveDict['RezOp'].setData(self.RezTimeList, y)
                    self.typ_widget.plot.achse_2.autoRange()                        # Rezept Achse 2 wird nicht fertig angezeigt, aus dem Grund wird dies durchgeführt! Beim Enden wird die AutoRange Funktion von base_classes.py durchgeführt. Bewegung des Plots sind mit der Lösung nicht machbar!!
                                                                                    # Plot wird nur an Achse 1 (links) angepasst!
            #//////////////////////////////////////////////////////////////
            # Erstelle fals gegeben, die Leistungs-Rezept-Kurve (Art: op)
            #//////////////////////////////////////////////////////////////
            if 'op' in self.Art_list or 'opr' in self.Art_list:
                faktor = self.skalFak['Op']
                y = [a * faktor for a in RezOPValueList]
                if anzeigeOp:
                    self.curveDict['RezOp'].setData(RezOPTimeList, y)
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
            try: self.rezept_config = config['devices'][self.device_name]['rezepte']
            except Exception as e: 
                self.rezept_config = {'rezept_Default':  {'n1': '10 ; 0 ; s'}}
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} rezepte {self.Log_Pfad_conf_5[self.sprache]} {self.rezept_config}')
                logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_7[self.sprache]}')
                logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
            
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