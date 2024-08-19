# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Eigener PID-Regler:
- Aufruf in den Geräte-Objekten
- Regelung verschiedener Größen

bassierend auf: http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-direction/
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## GUI:
from PyQt5.QtCore import (
    QObject,
)

## Allgemein:
import logging
import datetime
import yaml

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class PID(QObject):
    def __init__(self, sprache, device_name, PID_config, Max, Min):
        ''' Erzeuge einen PID-Regler.
        
        Args:
            sprache (int):              Sprache des Programms (GUI, Files)
            device_name (str):          Name des Gerätes, zu dem der PID-Regler gehört
            PID_config (dict):          Config-Datei-Teil für den PID 
            Max (float):                Maximaler Output
            Min (float):                Minimaler Output
        '''
        super().__init__()
        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
        self.Log_PID_0      = ['PID-Regler',                                                                                                            'PID controller']
        self.Log_PID_1      = ['P-Anteil (kp) = ',                                                                                                      'P-share (kp) =']
        self.Log_PID_2      = ['I-Anteil (ki) = ',                                                                                                      'I-share (ki) =']
        self.Log_PID_3      = ['D-Anteil (kd) = ',                                                                                                      'D-share (kd) =']
        Log_PID_4           = ['Erstelle PID-Regler für das Gerät: ',                                                                                   'Create PID controller for the device: ']
        self.Log_PID_5      = ['Zeitdifferenz zwischen den Messungen: ',                                                                                'Time difference between measurements: ']
        self.Log_PID_6      = ['s',                                                                                                                     's']
        self.Log_PID_7      = ['Der Sample-Zeit-Toleranzbereich',                                                                                       'The sample time tolerance range']
        self.Log_PID_8      = ['des PID-Reglers wurde überschritten mit',                                                                               'of the PID controller was exceeded with']
        self.Log_PID_9      = ['des PID-Reglers wurde unterschritten mit',                                                                              'of the PID controller was undershot with ']
        self.Log_PID_10     = ['um',                                                                                                                    'by']
        self.Log_PID_11     = ['ms',                                                                                                                    'ms']
        self.Log_PID_12     = ['bis',                                                                                                                   'to']
        self.Log_PID_13     = ['Fehler Grund (Parameter einlesen):',                                                                                    'Error reason (read parameters):']
        self.Log_PID_14     = ['PID-Parameter falsch!',                                                                                                 'PID parameters wrong!']
        self.Log_PID_14_1   = ['PID-Modus gesperrt bis PID-Werte berichtigt!',                                                                          'PID mode locked until PID values ​​corrected!']
        self.Log_PID_15     = ['Update Konfiguration (Update VIFCON-PID-Parameter):',                                                                   'Update configuration (update VIFCON PID parameters):']
        self.Log_PID_16     = ['Fehlerhafte Konfiguration der VIFCON-PID-Parameter!\nKeine gültigen Parameter vorhanden! Speere bleibt bestehen!',      'Incorrect configuration of the VIFCON PID parameters!\nNo valid parameters available! Spears remain!']
        self.Log_PID_17     = ['Fehlerhafte Konfiguration der VIFCON-PID-Parameter!\nNutzung der alten gültigen Parameter!',                            'Incorrect configuration of the VIFCON PID parameters!\nUse of the old valid parameters!']
        self.Log_PID_18     = ['Aktuelle Parameter: ',                                                                                                  'Current parameters:']
        self.Log_value_1    = ['Eingang - Sollwert: ',                                                                                                  'Input - Set-Point']
        self.Log_value_2    = ['und Istwert: ',                                                                                                         'and Actual Value']
        self.Log_value_3    = ['/ Ausgang: ',                                                                                                           '/ Output:']

        #---------------------------------------
        # Variablen:
        #---------------------------------------
        ## Init:
        self.sprache = sprache
        self.device = device_name
        self.config = PID_config
        self.OutMax = Max
        self.OutMin = Min
        ## Config:
        self.kp                 = self.config['kp']
        self.ki                 = self.config['ki']
        self.kd                 = self.config['kd']
        self.sample_time        = self.config['sample']                 # Sample-Zeit [ms]
        self.sample_toleranz    = self.config['sample_tolleranz']       # erlaubte Tolleranz zur Sample-Zeit [ms]
        self.debug_time         = self.config['debug_log_time']         # Abstand der Aufnahme der Debug-Log-Nachrichten [s]
        ## Startzeit:
        self.last_time          = datetime.datetime.now(datetime.timezone.utc).astimezone()
        self.log_time           = datetime.datetime.now(datetime.timezone.utc).astimezone()
        ## Start-Werte:
        self.ITerm      = 0
        self.last_Input = 0
        self.Output     = 0
        self.PID_speere = False
        ## Yaml-Datei:
        self.config_dat = None
        self.widget = None

        #---------------------------------------
        # Informationen:
        #---------------------------------------
        logger.info(f'{self.Log_PID_0[self.sprache]} - {Log_PID_4[sprache]}{self.device}')
        logger.info(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_1[sprache]}{self.kp}')
        logger.info(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_2[sprache]}{self.ki}')
        logger.info(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_3[sprache]}{self.kd}')

        #---------------------------------------
        # PID-Werte-Kontrolle:
        #---------------------------------------
        error, self.kp, self.ki, self.kd = self.check_PID_Parameter(self.kp, self.ki, self.kd)
        
        #---------------------------------------
        # PID-Werte:
        #---------------------------------------
        if not error:
            self.ki_st = self.ki * self.sample_time
            self.kd_st = self.kd/self.sample_time
        else:
            # Speere setzen:
            logger.warning(self.Log_PID_14_1[self.sprache])
            self.PID_speere = True

    ##########################################
    # Input-Output:
    ##########################################
    def InOutPID(self, Input_Ist, Input_Soll, Modus, Rezept_OP):
        ''' Regelung

        Args: 
            Input_Ist (float):  Istwert der Regelung
            Input_Soll (float): Sollwert der Regelung
            Modus (bool):       Wenn True, so ist der Rezept-Modus aktiv!
            Rezept_OP (float):  Wert wird an Output gegeben - bei -1 wird der alte noch genommen!
        
        Return:
            Output (float):     Regelgröße die gesendet werden soll        
        '''
        # Zeit:
        ak_time         = datetime.datetime.now(datetime.timezone.utc).astimezone()
        timediff        = (ak_time - self.last_time).total_seconds()
        timediff_log    = (ak_time - self.log_time).total_seconds()
        # Fehler Variablen:
        ## Fehler:
        error = Input_Soll - Input_Ist
        ## I-Anteil:
        self.ITerm += self.ki_st * error
        if self.ITerm > self.OutMax:
            self.ITerm = self.OutMax
        elif self.ITerm < self.OutMin:
            self.ITerm = self.OutMin
        ## D-Anteil:
        dInput = (Input_Ist - self.last_Input)
        # PID-Ausgang:
        Output = self.kp * error + self.ITerm - self.kd_st * dInput
        if Output > self.OutMax:
            Output = self.OutMax
        elif Output < self.OutMin:
            Output = self.OutMin
        # Nächster Durchgang:
        self.last_time = ak_time
        self.last_Input = Input_Ist

        # Rezept-Modus:
        if Modus and not Rezept_OP == -1:
            Output = Rezept_OP 

        # Werte Loggen:
        if timediff*1000 > self.sample_time + self.sample_toleranz: 
            logger.warning(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_7[self.sprache]} ({self.sample_time - self.sample_toleranz} {self.Log_PID_12[self.sprache]} {self.sample_time + self.sample_toleranz}) {self.Log_PID_11[self.sprache]} {self.Log_PID_8[self.sprache]} {timediff*1000} {self.Log_PID_11[self.sprache]} {self.Log_PID_10[self.sprache]} {abs(self.sample_time - timediff*1000)} {self.Log_PID_11[self.sprache]}.')    
        elif timediff*1000 < self.sample_time - self.sample_toleranz:
            logger.warning(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_7[self.sprache]} ({self.sample_time - self.sample_toleranz} {self.Log_PID_12[self.sprache]} {self.sample_time + self.sample_toleranz}) {self.Log_PID_11[self.sprache]} {self.Log_PID_9[self.sprache]} {timediff*1000} {self.Log_PID_11[self.sprache]} {self.Log_PID_10[self.sprache]} {abs(self.sample_time - timediff*1000)} {self.Log_PID_11[self.sprache]}.')    
        
        if timediff_log >= self.debug_time:
            logger.debug(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_5[self.sprache]}{timediff} {self.Log_PID_6[self.sprache]}')    
            logger.debug(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_value_1[self.sprache]} {Input_Soll} {self.Log_value_2[self.sprache]} {Input_Ist} {self.Log_value_3[self.sprache]} {Output}')
            self.log_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

        # Rückgabewert beschreiben:
        self.Output = round(Output,3)

    ##########################################
    # Update-Parameter:
    ##########################################
    def update_VPID_Para(self):
        '''Config neu einlesen und Parameter des PID-Neusetzen'''
        # Yaml erneut laden:
        with open(self.config_dat, encoding="utf-8") as f:  
            config = yaml.safe_load(f)
            logger.info(f"{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_15[self.sprache]} {config}")
        # Prüfe PID-Parameter:
        error, kp, ki, kd = self.check_PID_Parameter(config['devices'][self.device]['PID']['kp'], config['devices'][self.device]['PID']['ki'], config['devices'][self.device]['PID']['kd'])

        if self.PID_speere and error:
            self.widget.Fehler_Output(1, self.Log_PID_16[self.sprache], device = f'{self.Log_PID_0[self.sprache]} ({self.device})')
        elif kp == self.kp and ki == self.ki and kd == self.kd and not self.PID_speere:
            self.widget.Fehler_Output(1, self.Log_PID_17[self.sprache], device = f'{self.Log_PID_0[self.sprache]} ({self.device})')
            logger.info(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_18[self.sprache]}{self.Log_PID_1[self.sprache]} {self.kp}; {self.Log_PID_2[self.sprache]}{self.ki}; {self.Log_PID_3[self.sprache]}{self.kd}')
        elif not error:
            self.kp = kp
            self.ki = ki
            self.kd = kd
            self.PID_speere = False

            self.ki_st = self.ki * self.sample_time
            self.kd_st = self.kd/self.sample_time
            self.widget.Fehler_Output(0)
                        
    def check_PID_Parameter(self, kp, ki, kd):
        ''' Prüfe die PID-Parameter aus der Config!

        Args:
            kp (float):             kp-Wert
            ki (float):             ki-Wert
            kd (float):             kd-Wert
        Return:
            Fehler (bool):          True - Fehler
            kp (float):             kontrollierter kp-Wert
            ki (float):             kontrollierter ki-Wert
            kd (float):             kontrollierter kd-Wert
        '''
        try:
            ki = float(str(ki).replace(',', '.'))
            kd = float(str(kd).replace(',', '.'))
            kp = float(str(kp).replace(',', '.'))
        except Exception as e:
            logger.warning(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_14[self.sprache]}')
            logger.exception(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_13[self.sprache]}')
            # Alte-PID-Parameter übergeben und Fehler durchgeben:
            return True, self.kp, self.ki, self.kd
        # Neue PID-Parameter übergeben:
        return False, kp, ki, kd