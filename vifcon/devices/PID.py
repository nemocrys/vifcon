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
        '''
        super().__init__()
        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
        self.Log_PID_0      = ['PID-Regler',                                'PID controller']
        Log_PID_1           = ['P-Anteil (kp) = ',                          'P-share (kp) =']
        Log_PID_2           = ['I-Anteil (ki) = ',                          'I-share (ki) =']
        Log_PID_3           = ['D-Anteil (kd) = ',                          'D-share (kd) =']
        Log_PID_4           = ['Erstelle PID-Regler für das Gerät: ',       'Create PID controller for the device: ']
        self.Log_PID_5      = ['Zeitdifferenz zwischen den Messungen: ',    'Time difference between measurements: ']
        self.Log_PID_6      = ['s',                                         's']
        self.Log_PID_7      = ['Der Sample-Zeit-Toleranzbereich',           'The sample time tolerance range']
        self.Log_PID_8      = ['des PID-Reglers wurde überschritten mit',   'of the PID controller was exceeded with']
        self.Log_PID_9      = ['des PID-Reglers wurde unterschritten mit',  'of the PID controller was undershot with ']
        self.Log_PID_10     = ['um',                                        'by']
        self.Log_PID_11     = ['ms',                                        'ms']
        self.Log_PID_12     = ['bis',                                       'to']
        self.Log_value_1    = ['Eingang - Sollwert: ',                      'Input - Set-Point']
        self.Log_value_2    = ['und Istwert: ',                             'and Actual Value']
        self.Log_value_3    = ['/ Ausgang: ',                               '/ Output:']

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
        self.sample_time        = self.config['sample']
        self.sample_toleranz    = self.config['sample_tolleranz']
        ## Startzeit:
        self.last_time      = datetime.datetime.now(datetime.timezone.utc).astimezone()
        ## Start-Werte:
        self.ITerm      = 0
        self.last_Input = 0
        self.Output     = 0

        #---------------------------------------
        # Informationen:
        #---------------------------------------
        logger.info(f'{self.Log_PID_0[self.sprache]} - {Log_PID_4[sprache]}{self.device}')
        logger.info(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {Log_PID_1[sprache]}{self.kp}')
        logger.info(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {Log_PID_2[sprache]}{self.ki}')
        logger.info(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {Log_PID_3[sprache]}{self.kd}')

        #---------------------------------------
        # PID-Werte:
        #---------------------------------------
        self.ki = self.ki *  self.sample_time
        self.kd = self.kd/self.sample_time

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
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        timediff = (ak_time - self.last_time).total_seconds()
        logger.debug(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_5[self.sprache]}{timediff} {self.Log_PID_6[self.sprache]}')
        if timediff*1000 > self.sample_time + self.sample_toleranz: 
            logger.warning(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_7[self.sprache]} ({self.sample_time - self.sample_toleranz} {self.Log_PID_12[self.sprache]} {self.sample_time + self.sample_toleranz}) {self.Log_PID_11[self.sprache]} {self.Log_PID_8[self.sprache]} {timediff*1000} {self.Log_PID_11[self.sprache]} {self.Log_PID_10[self.sprache]} {abs(self.sample_time - timediff*1000)} {self.Log_PID_11[self.sprache]}.')    
        elif timediff*1000 < self.sample_time - self.sample_toleranz:
            logger.warning(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_PID_7[self.sprache]} ({self.sample_time - self.sample_toleranz} {self.Log_PID_12[self.sprache]} {self.sample_time + self.sample_toleranz}) {self.Log_PID_11[self.sprache]} {self.Log_PID_9[self.sprache]} {timediff*1000} {self.Log_PID_11[self.sprache]} {self.Log_PID_10[self.sprache]} {abs(self.sample_time - timediff*1000)} {self.Log_PID_11[self.sprache]}.')    
        # Fehler Variablen:
        ## Fehler:
        error = Input_Soll - Input_Ist
        ## I-Anteil:
        self.ITerm += self.ki * error
        if self.ITerm > self.OutMax:
            self.ITerm = self.OutMax
        elif self.ITerm < self.OutMin:
            self.ITerm = self.OutMin
        ## D-Anteil:
        dInput = (Input_Ist - self.last_Input)
        # PID-Ausgang:
        Output = self.kp * error + self.ITerm - self.kd * dInput
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
        logger.debug(f'{self.Log_PID_0[self.sprache]} ({self.device}) - {self.Log_value_1[self.sprache]} {Input_Soll} {self.Log_value_2[self.sprache]} {Input_Ist} {self.Log_value_3[self.sprache]} {Output}')
        
        # Rückgabewert beschreiben:
        self.Output = round(Output,3)

        