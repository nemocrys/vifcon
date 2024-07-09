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
## Allgemein:
import logging
import datetime

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
logger = logging.getLogger(__name__)


class PID:
    def __init__(self, sprache, device_name, PID_config, Max, Min):
        ''' Erzeuge einen PID-Regler.
        
        Args:
            sprache (int):              Sprache des Programms (GUI, Files)
            device_name (str):          Name des Gerätes, zu dem der PID-Regler gehört
            PID_config (dict):          Config-Datei-Teil für den PID 
        '''
        #--------------------------------------- 
        # Sprach-Einstellung:
        #---------------------------------------
        ## Logging:
        self.Log_PID_0      = ['PID-Regler',            'PID controller']
        Log_PID_1           = ['P-Anteil (kp) = ',      'P-share (kp) =']
        Log_PID_2           = ['I-Anteil (ki) = ',      'I-share (ki) =']
        Log_PID_3           = ['D-Anteil (kd) = ',      'D-share (kd) =']
        self.Log_value_1    = ['Eingang - Sollwert: ',  'Input - Set-Point']
        self.Log_value_2    = ['und Istwert: ',         'and Actual Value']
        self.Log_value_3    = ['/ Ausgang: ',           '/ Output:']


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
        self.kp             = self.config['kp']
        self.ki             = self.config['ki']
        self.kd             = self.config['kd']
        self.sample_time    = self.config['sample']
        ## Startzeit:
        self.last_time      = datetime.datetime.now(datetime.timezone.utc).astimezone()
        ## Start-Werte:
        self.ITerm = 0
        self.last_Input = 0

        #---------------------------------------
        # Informationen:
        #---------------------------------------
        logging.info(f'{self.Log_PID_0[sprache]} ({self.device}) - {Log_PID_1[sprache]}{self.kp}')
        logging.info(f'{self.Log_PID_0[sprache]} ({self.device}) - {Log_PID_2[sprache]}{self.ki}')
        logging.info(f'{self.Log_PID_0[sprache]} ({self.device}) - {Log_PID_3[sprache]}{self.kd}')

        #---------------------------------------
        # PID-Werte:
        #---------------------------------------
        self.ki = self.ki *  self.sample_time
        self.kd = self.kd/self.sample_time

    ##########################################
    # Input-Output:
    ##########################################
    def InOutPID(self, Input_Ist, Input_Soll):
        ''' Regelung

        Args: 
            Input_Ist (float):  Istwert der Regelung
            Input_Soll (float): Sollwert der Regelung
        
        Return:
            Output (float):     Regelgröße die gesendet werden soll        
        '''
        # Zeit:
        ak_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        timediff = (ak_time - self.last_time).total_seconds()
        if timediff >= self.sample_time:
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

            logging.debug(f'{self.Log_value_1[self.sprache]} {Input_Soll} {self.Log_value_2[self.sprache]} {Input_Ist} {self.Log_value_3[self.sprache]} {Output}')

            return round(Output, 3)
        else:
            return -1



        