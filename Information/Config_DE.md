# Config-Datei

Die Config-Datei ist eins der wesentlichsten Feature der VIFCON-Steuerung. Mit dieser Datei wird alles in der Steuerung configuriert. So werden:

- die GUI,
- die Rezepte,
- der Multilog-Link,
- das Gamepad,

und vieles mehr bereitgestellt. Die Config-Datei ist eine Yaml-Datei und wird durch die Python-Bibliothek pyYAML in VIFCON eingebunden. 

## Funktion

Die Yaml-Datei wird von Python als Dictionary bzw. als Verschachtelung mehrerer Dictionaries angesehen. Ein Dictionary ist wie folgt aufgebaut:

```
    Schlüssel: Wert
```

Der Wert kann dabei eigentlich alles mögliche sein. Es kann z.B. ein Objekt, ein Dictonary, eine Liste oder auch ein Integer sein. 

Die Config-Datei wird wie folgt ausgelesen:
```
with open(config, encoding="utf-8") as f:
    self.config = yaml.safe_load(f)
```

Aufgerufen wird ein Wert wie folgt:
```
self.config['language']
```

In dem Beispiel würde so der Wert des Schlüssels "language" gewertet werden. 

## Konfigurations Templates

VIFCON wurde an 4 Anlagen erstelle. Für jede Anlage gibt es ein Template im Ordner [Template](..\Template). Das Template [config_temp.yml](..\Template\config_temp.yml) kann als Beispiel angesehen werden. Die folgenden [Erklärungen](#erklärung-der-einzelnen-punkte) zeigt die einzelnen Konfigurationen.

Anlage | Template
-------|---------------
DemoFZ | [config_temp_DemoFZ.yml](..\Template\config_temp_DemoFZ.yml)
Nemo-1 | [config_temp_Nemo-1.yml](..\Template\config_temp_Nemo-1.yml)
Nemo-2 | [config_temp_Nemo-2.yml](..\Template\config_temp_Nemo-2.yml)
DemoCZ | [config_temp_Educrys.yml](..\Template\config_temp_Educrys.yml)

## Erklärung der einzelnen Punkte

In dem [Templates](#Konfigurations-Templates) können auch Beschreibungen gefunden werden. 

Im folgenden sind die Punkte:
1. [Zeiten](#zeiten)
2. [Feature-Überspringen](#feature-überspringen)
3. [Speicher Dateien und Bilder](#speicher-dateien-und-bilder)
4. [GUI](#GUI)
5. [Logging-Datei](#logging-datei)
6. [Konsolen-Logging](#konsolen-logging)
7. [Legende der GUI](#legende)
8. [Skalierungsfaktoren](#skalierungsfaktoren)
9. [Geräte](#geräte)

### Zeiten:

```
time:
  dt-main: 150
  timeout_exit: 10
```
Nach dieser Zeit (`dt-main`) werden die Threads der Geräte aufgerufen bzw. die sample-Funktion des Sampler-Objektes in dem Thread. Die Zeit wird in ms angegeben und wird für den Reaktionstimer benötigt. 

Bei der Zeit `timeout_exit` handelt es sich um eine Zeit die in Sekunden angegeben wird. In der Exit-Funktion des Programms, gibt es eine While-Schleife, die auslösen soll, wenn die Threads fertig sind. Kommt es dort zu Problemen, so wird nach der angegebenen Zeit ein break ausgeführt und die Schleife verlassen. Bei Auslösung wird auch eine Warnung in der Konsole und der Log-Datei ausgegeben. 

### Feature-Überspringen 

```
Function_Skip:                                                
  Multilog_Link: 0        
  Generell_GamePad: 0
  writereadTime: 0
```
Wenn der Wert auf True (1) steht, so werden die Funktionen für den Multilog-Link und dem Gamepad freigeschaltet. Bei False wird dies im Code übersprungen und wirkt sich nicht auf VIFCON aus. 

Bei `writereadTime` wird eine Zeitspanne als Debug gelogged. Damit diese Funktion funktioniert, muss beim `logging` das `level` auf 10 gesetzt werden! Die Zeitspanne die hier gemessen wird ist für die Funktionen `write` und `read` der einzelnen Geräte. Somit wird ermittelt, wie lange diese Funktionen dauern. Beide Funktionen sind für die Geräte-Kommunikation wichtig!

### Speicher Dateien und Bilder

```
save:
  config_save: True                                
  log_save: True   
  plot_save: True
  GUI_save: True
```

Am Ende der Anwendung wird die Config-Datei und die Log-Datei aus dem Hauptordner in den Messordner kopiert. Auch die Legende und die Plots werden gespeichert. Dies passiert bei True. 

Beachtet werden muss hierbei, dass die Plots und die Legende so gespeichert werden, wie sie in der GUI zu sehen sind. 

Um ein gesamt Bild der GUI zu haben, kann auch die aktuelle sichtbare GUi gespeichert werden. 

### GUI

```
GUI:
  language: de
  GUI_Frame: 0
  GUI_color_Widget: 1
```

Die Einstellungen verändern die GUI in Sprache und Aussehen. 

Bei `language` wird die Sprache angegeben. Dabei können nur Deutsch (DE) und Englisch (EN) ausgewählt werden. Die GUI ändert sich dementsprechend.

Wenn der Wert bei `GUI_Frame` auf True (1) steht, dann werden die Rahmen der Widgets eingeschaltet. Mit diesem Mittel kann die Platzierung der einzelnen Widgets angesehen werden. 

<img src="../Bilder/Rahmen_DE.png" alt="GUI-Rahmen Anzeige" title='Anzeige der Widget-Rahmen' width=500/>

Mit `GUI_color_Widget` können die Farben auf dem Widget abgeschaltet werden. Anstelle der Bunten GUI wird dann alles schwarz angezeigt. In dem Bild sind die gemeinten Farben zu sehen. 

### Logging-Datei

```
logging:
  level: 20
  filename: vifcon.log
  format: '%(asctime)s %(levelname)s %(name)s - %(message)s'
  filemode: w         
  encoding: 'utf-8' 
```
Über diesen Config-Teil, wird die Logging-Datei erstellt und das Logging-Level bestimmt. Es gibt:

- 10 - Debug
- 20 - Info
- 30 - Warning
- 40 - Error

Bei einigen Systemen muss das `encoding` auskommentiert werden, da z.B. Linux dadurch einen Fehler ausgibt. 

### Konsolen-Logging
```
consol_Logging:
  level: 30
  print: 1 
  format: '%(asctime)s %(levelname)s %(name)s - %(message)s'
```
Wenn beim [Logging](#logging-datei) der Schlüssel *filename* leergelassen wird, dann werden alle Log-Nachrichten in die Konsole geschrieben. 

Das Konsolen-Logging filtert bestimmte Nachrichten herraus. Beim Schlüssel *print* können somit:

- 1 - Nur das angegebene Level,
- 2 - Auch alle kleineren Level und,
- 3 - Auch alle größeren Level

angegeben werden. Beachtet werden muss hierbei, dass das Haupt-Logging Level eine höhere Priorität hat als das neue Konsolen-Logging. Zum Beispiel:

- logging-Level = 40
- Consol-logging-Level = 30 und print = 1
- In der Konsole wird nicht ausgegeben, da die Nachrichten für Level 30 nicht vom Haupt-Logger aufgerufen werden!

### Legende

```
legend:
  generator:
    legend_pos: Side
    legend_anz: 2
    side: rl 
  antrieb:
    legend_pos: Side  
    legend_anz: 2   
    side: rl
```

Hiermit wird die Legende für die beiden Geräte-Typen der Steuerung (Antriebe, Generator) erstellt. Möglich sind beim Schlüssel *legend_pos*:

- SIDE
- IN
- OUT

Bei IN wird die Legende im Plot sein. Bei OUT wird sie unter dem Plot sein und bei SIDE wird die Legende neben dem Plot in einem seperaten Widget sein. Dabei kann bei SIDE die Position:

- rl
- l
- r

Bei rl werden zwei Widgets rechts und links vom Plot erstellt. In diesen Widgets stehen dann die Kurven die für die Achse vorgesehen sind. Bei l und r wird ein Widget nur Rechts oder nur Links erstellt.

Bei OUT und IN kann auch die Anzahl der in einer Reihe stehenden Label geändert werden. Dies geschieht durch *legend_anz*.

### Skalierungsfaktoren

```
skalFak:                                                      
  Pos:      1 
  Win:      1 
  Speed_1:  0 
  Speed_2:  1    
  WinSpeed: 1 
  Temp:     0 
  Op:       0 
  Current:  0
  Voltage:  0
  Pow:      0  
  Freq:     0
  Freq_2:   0
  PIDA:     0
  PIDG:     0
```

Durch die Skalierungsfaktoren kann der Plot der GUI geändert werden. Nicht immer sind die verschiedenen Größen im selben Wertebereich. Sobald der Wert ungleich eins ist, wird die Kurve um diesen Wert skalliert. Diese Skalierung wird in dem Label der y-Achse angezeigt. Weiterhin bewirken bestimmte Zahlen in dem Sinne auch eine Änderung. Die Zahl 1 als Skalierungsfaktor wird nicht im y-Achsen-Label angezeigt. Bei einer Null wird die Große aus dem y-Achsen-Label entfernt. Wenn keine Größe im Label mehr enthalten ist, so wird *Keine Einträge!* angezeigt.

Mit PIDA und PIDG sind spezielle Größen gemeint. PIDA findet bei der PI-Achse und den beiden Nemo-Antrieben Anwendung, während PIDG nur beim TruHeat genutzt wird. Hiermit kann die PID-Regler Input Größe skalliert werden. Bei Eurotherm ist diese Größe die Temperatur, weshalb sie nicht mit PIDG skaliert wird.  

### Geräte

```
devices:
  Eurotherm 3504:
    skip: 1                         # Ebene 1
    typ: Generator                  # Ebene 1
    ende: 1                         # Ebene 1
    start:                          # Ebene 1
      sicherheit: 1  PI-Achse_h:    # Ebene 2
    ...
  PI-Achse_h:
    ...

```

Unter dem Schlüssel ***devices*** finden sich nun alle vorhandenen Geräte wieder. Jedes Gerät muss dabei einen bestimmten Namens-Teil haben:

Gerät                                                       | String-Teil
------------------------------------------------------------|----------------------
[Eurotherm](#Eurotherm)                                     | Eurotherm
[TruHeat](#TruHeat)                                         | TruHeat
[PI-Achse](#PI-Achse)                                       | PI-Achse
[Nemo-Anlage 1 & 2 Hub-Antrieb](#nemo-achse-linear)         | Nemo-Achse-Linear
[Nemo-Anlage 1 & 2 Rotation Antrieb](#nemo-achse-rotation)  | Nemo-Achse-Rotation
[Nemo-Anlage 1 & 2 Sensoren](#nemo-gase)                    | Nemo-Gase
[Nemo-2-Anlage Generator](#nemo-generator)                  | Nemo-Generator
[Educrys-Anlage Sensoren](#educrys-monitoring)              | Educrys-Monitoring
[Educrys-Anlage Antriebe](#educrys-antrieb)                 | Educrys-Antrieb
[Educrys-Anlage Heizer](#educrys-heizer)                    | Educrys-Heizer

Bei der PI-Achse und dem Eurotherm-Regler ist ein Beispiel am Anfang zu finden. Die einzelnenen Geräte haben nun teilweise Unterschiede und teilweise Gemeinsamkeiten. Die  verschiedenen Konfigurationen werden folgend in Tabellen gezeigt. In dem Beispiel kann man die Ebenen sehen, die in den Tabellen gezeigt werden. Mit Ebene ist die Einrückung in der Yaml-Datei gemeint. Die Übergeordneten Einrückungen von `devices` und dem Geräte-Namen werden dabei nicht beachtet.

#### Gemeinsamkeiten

In der ersten Tabelle sind die Grundlegenden Gemeinsamkeiten wie PID-Regler und Multilog zu finden. 

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
skip || Um ein Gerät nicht in die GUI zu übertragen, muss bei diesem Schlüssel der Wert **True (1)** ausgewählt werden. In dem Fall wird die Definition des Gerätes im Programm übersprungen.
typ || *Auswahlmöglichkeiten*: **Generator**, **Antrieb**, **Monitoring**<br><br>Generator: Eurotherm, TruHeat, Nemo-Generator, Educrys-Heizer<br>Antrieb: PI-Achse, Nemo-Achse-Linear, Nemo-Achse-Rotation, Educrys-Antrieb<br>Monitoring: Nemo-Gase, Educrys-Monitoring<br><br>Durch diesen Schlüssel wird die Seite und der Tab (Steuerung, Monitoring) des Widgets bestimmt.
ende || Bei **True** wird bei Beendigung des Programmes ein Sicherer-Endzustand eingestellt!
multilog |write_trigger| Kommunikationsstring für Multilog
multilog |write_port| Kommunikationsport für das Senden an Multilog
multilog |read_trigger_ist| Kommunikationsstring für VIFCON – Empfang von Istwerten durch Multilog
multilog |read_port_ist| Kommunikationsport zum Empfang der Multilog Istwerte
multilog |read_trigger_soll| Kommunikationsstring für VIFCON – Empfang von Sollwerten durch Multilog
multilog |read_port_soll| multilog	read_port_soll	Kommunikationsport zum Empfang der Multilog Sollwerte
PID	|PID_Aktiv	| Bei **True** wird der PID-Modus freigeschaltet und verwendbar.
PID	|Value_Origin| Herkunft der Soll- und Istwerte: **VV**, **VM**, **MM**, **MV**<br>Erster Buchstabe = Istwert<br>Zweiter Buchstabe = Sollwert<br>V – VIFCON, M – Multilog 
PID	|kp	|VIFCON-PID P-Glied-Parameter
PID	|ki	|VIFCON-PID I-Glied-Parameter
PID	|kd	|VIFCON-PID D-Glied-Parameter
PID	|sample	|Zeit in Sekunde mit der der PID-Regler aufgerufen wird (Sample-Rate)
PID	|sample_tolleranz	|Zeit in Sekunde (Abweichung von Sample-Rate ohne Fehlermeldung)
PID	|start_ist	|Start Istwert (für Initialisierung gebraucht) (PID-Input)
PID	|start_soll	|Start Sollwert (PID-Input)
PID	|umstell_wert|Wert der in das Eingabefeld geschrieben wird, wenn der PID-Modus beendet wird und der bei Wechsel im write_value Dictionary für die Output-Größe im Normalen Modus gespeichert wird!
PID	|Multilog_Sensor_Ist	|Sensor Bezeichnung für die Multilogkommunikation (Istwert)|
PID	|Multilog_Sensor_Soll	|Sensor Bezeichnung für die Multilogkommunikation (Sollwert)
PID	|Input_Limit_max	|Limit für PID-Input
PID	|Input_Limit_min	|Limit für PID-Input
PID	|Input_Error_option	|Bei Fehlerhaftem Wert wird je nach Konfiguration etwas gemacht:<br>**error** – Letzter Wert wird beibehalten<br>**max** – maximaler Wert wird verwendet (Limit)<br>**min** – minimaler Wert wird verwendet (Limit)
PID	|debug_log_time|	Logging im Debug<br>Zeit in Sekunden die eine Log-Nachricht schreibt, die die Inputs und Outputs des PID-Reglers zeigt
rezepte	||	Siehe Erläuterungen in [Rezepte_DE.md](Rezepte_DE.md)

**Beispiele:**

Hier die Konfigurationen für Multilog und PID. Wenn die `read`-Konfigurationen genutzt werden, müssen auch bestimmte `PID`-Konfigurationen gesetzt werden. Zum Beispiel `Value_Origin` muss ein `M` enthalten und bei `Multilog_Sensor_Ist` muss je nach Sensor bei `read_trigger_ist` etwas bestimmtes stehen!

```
  multilog:
    write_trigger: Eurotherm1
    write_port: 50000
    read_trigger_ist: IGA-6-23-adv
    read_port_ist: 0              
    read_trigger_soll: DAQ-6510   
    read_port_soll: 0 
```

```
  PID:  
    PID_Aktiv: 1 
    Value_Origin: VV  
    kp: 200 
    ki: 0.3 
    kd: 0  
    sample: 500 
    sample_tolleranz: 100
    start_ist: 25
    start_soll: 25
    umstell_wert: 0
    Multilog_Sensor_Ist: TE_1_K air 155 mm over crucible
    Multilog_Sensor_Soll: TE_2_K air 155 mm over crucible
    Input_Limit_max: 1000
    Input_Limit_min: 0
    Input_Error_option: error
    debug_log_time: 5
```

Die einzelnen GUI-Legenden-Kurven werden bei den Tabellen unter [Unterschiede](#Unterschiede) gezeigt. Im folgenden ein Beispiel für die Definition besagter Konfiguration. Die Konfiguration besteht aus einem String. Bei auslesen wird dieser anhand des Zeichens `;` getrennt. 
```
 GUI:
    legend: RezOp ; RezT ; IWT ; IWOp ; SWT ; uGT ; oGT ; oGOp ; uGOp
```

---

Die zweite Tabelle zeigt die Gemeinsamkeiten bei der **RS232-Schnittstelle**:

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
serial-interface	|port	|RS232-Schnittstelle
serial-interface	|baudrate|	Übertragungsrate
serial-interface	|bytesize|	Größe des Bytes
serial-interface	|stopbits|	Anzahl der Stoppbits
serial-interface	|parity	|Überprüfungsbit
serial-interface	|timeout	|Abbruch der Schnittstellen Lese- und Schreib-Befehle

**Geräte:** Eurotherm, TruHeat, PI-Achse, Educrys-Anlage

---

Die zweite Tabelle zeigt die Gemeinsamkeiten bei der **Modbus-Kommunikation**:

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
serial-interface	|host	|IP-Adresse Server
serial-interface	|port	|Port für die Kommunikation
serial-interface	|default|Ausgabe der Kommunikation in der Konsole<br>**ACHTUNG**: Funktioniert nur bei pyModbusTCP < 0.3.0, funktioniert bei 0.2.1<br>Auskommentieren im Fehlerfall!! (siehe [Python_RPi_DE.py](Python_RPi_DE.md))
serial-interface|	timeout|	Abbruch der Schnittstellen Lese- und Schreib-Befehle

**Geräte:** Nemo-Anlage

---

#### Unterschiede

Im folgenden werden die Konfigurationen der einzelnen Geräte gezeigt. Punkte wie Multilog, PID und Schnittstelle sind oben bei den [Gemeinsamkeiten](#Gemeinsamkeiten) zu finden.

##### **Eurotherm:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
start	    | sicherheit        | Legt fest wie der Maximale Leistungsausgang (HO) gesetzt wird.<br>**True** – maximale Leistung (HO) kann nur am Gerät geändert werden <br>**False** – VIFCON sendet die max. Leistung (HO) an Eurotherm (Übergebener Wert OP max)
start	    | PID_Write         |Bei **True** werden werden die PID-Parameter aus `PID-Device` an das Eurotherm-Gerät gesendet! 
start	    | start_modus       |**Manuel** für den Manuellen Modus (Benutzer bestimmt Leistungsausgang)<br>**Auto** für den Automatischen Modus (Regelung der Temperatur aktiv, PID-Regler sorgt für Leistungsausgang)
start	    | readTime          |Zeit in Sekunde mit der das Gerät ausgelesen wird
start	    | init              |Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. **ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!
start	    | ramp_start_value  |Startwert einer Rampe, wenn diese als Segment 1 im Rezept gewählt wird!!<br>**IST** – Istwert<br>**SOLL** – Sollwert
start	    | ramp_m_unit       |Einheit des er-Rezept-Segmentes (Eurotherm-Rampe)<br>*Möglich*: **K/s**, **K/h**, **K/min**<br>**ACHTUNG**: Muss am Gerät auch eingestellt werden!!
PID-Device	| PB                |Eurotherm-Größe: Proportionalband
PID-Device	| TI                |Eurotherm-Größe: Integralzeit
PID-Device	| TD                |Eurotherm-Größe: Differenzialzeit
limits      | maxTemp           |Limit Temperatur Maximum
limits      | minTemp           |Limit Temperatur Minimum
limits      | oPMax             |Limit Operating Point (Leistung am Ausgang) Maximum
limits      | oPMin             |Limit Operating Point (Leistung am Ausgang) Minimum
GUI	        | legend            |String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: RezOP = Rezept (Rez) für die Ausgangsleistung (OP)<br><br>*Eingebaut*:<br> RezT, RezOp, IWT, IWOp, IWTPID, SWT, SWTPID, uGT, oGT, uGOp, oGOp, oGPID, uGPID
defaults	| startTemp         |Wert der in das Temperatur-Eingabefeld zur Initialisierung geschrieben wird
defaults	| startPow          |Wert der in das Leistungs-Eingabefeld zur Initialisierung geschrieben wird

---

##### **TruHeat:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
start	            |start_modus   | Start-Modus für den Generator (Radio-Button GUI)<br>Der Generator kann mit Leistung (**P**), Strom (**I**) oder Spannung (**U**) starten. 
start	            |readTime      | Zeit in Sekunde mit der das Gerät ausgelesen wird    
start	            |init          | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!    
start	            |ad            | Adresse des Generators
start	            |watchdog_Time | Der TruHeat besitzt einen Watchdog Timer als Sicherheitsfunktion. Der Zeitwert in Millisekunden wird zu Beginn des Programms gesetzt.      
start	            |send_Delay    | Hier kann eine Zeit in Millisekunden festgelegt werden, die eine Verzögerung zwischen dem Senden von Befehlen verursacht.<br>Sollte nicht Größer als die Watchdog Zeit sein!
serial-loop-read	|              | Anzahl der Wiederholungen bei Fehlerhafter Antwort des Gerätes (while-Schleife)
limits	            |maxI          | Limit Strom Maximum
limits	            |minI          | Limit Strom Minimum
limits	            |maxP          | Limit Leistung Maximum
limits	            |minP          | Limit Leistung Minimum
limits	            |maxU          | Limit Spannung Maximum
limits	            |minU          | Limit Spannung Minimum
GUI	                |legend        | String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: RezP = Rezept (Rez) für die Leistung (P)<br><br>*Eingebaut*:<br> RezI, RezU, RezP, Rezx, IWI, IWU, IWP, IWf, SWI, SWU, SWP, uGI, oGI, uGU, oGU, uGP, oGP, IWxPID, SWxPID, oGPID, uGPID
defaults	        |startCurrent  | Wert der in das Strom-Eingabefeld zur Initialisierung geschrieben wird
defaults	        |startPow      | Wert der in das Leistungs-Eingabefeld zur Initialisierung geschrieben wird
defaults	        |startVoltage  | Wert der in das Spannungs-Eingabefeld zur Initialisierung geschrieben wird

---

##### **PI-Achse:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
mercury_model	   |              | Ausgewählter Controller<br>**C862** oder **C863**
read_TT_log	     |              | Anzeige des Zielwertes (TT) als Info in der Log-Datei         
gamepad_Button	 |              | String für die Knopf-Zuweisung:<br>**PIh** - ← & → (Axis)<br>**PIz** - ↑ & ↓ (Axis)<br>**PIx** - X & B (Button)<br>**PIy** - Y & A (Button)<br><br>*Knöpfe:*<br>X - Raus <br>B - Rein<br>Y - Links<br>A - Rechts<br>← & ↑ - Hoch<br>→ & ↓ - Runter<br>Select - Stopp Antriebe
start	         |readTime      | Zeit in Sekunde mit der das Gerät ausgelesen wird 
start	         |init          | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!! 
start	         |mode          | Modus für Entriegelung der Bewegungsknöpfe:<br>**0** - Keine Verrrigelung<br>**1** - Entriegelung durch Timer<br>**2** - Entriegelung bei erreichen von 0 mm/s
serial-loop-read |              | Anzahl der Wiederholungen bei Fehlerhafter Antwort des Gerätes (while-Schleife)                      	
parameter	     |adv           | Adressauswahlcode
parameter	     |cpm           | Counts per mm (Umrechnungsfaktor)
parameter	     |mvtime        | Auslese-Delay für die Achsengeschwindigkeits Bestimmung [ms]<br>Wird für den Befehl MV bei C862 benötigt!
parameter	     |nKS_Aus       | Auslese Nachkommerstellen
limits	         |maxPos        | Limit Position Maximum        
limits	         |minPos        | Limit Position Minimum        
limits	         |maxSpeed      | Limit Geschwindigkeit Maximum           
limits	         |minSpeed      | Limit Geschwindigkeit Minimum            
GUI	             |bewegung      | Bewegungsrichtung (Darstellung der Pfeile in GUI)<br>**y** – Rechts und Links<br>**x** – Rein und Raus<br>**z** – Hoch und Runter
GUI	             |piSymbol      | Ausrichtung der Achse (Auf dem Gerät gibt es das Symbol PI)<br>y (**Li** - Links, **Re** - Rechts)<br>x (**Vo** - Vorn, **Hi** - Hinten)<br>z (**Ob** - Oben, **Un** - Unten)<br>Minus Werte zum PI-Symbol, andere Richtung plus          
GUI	             |knopf_anzeige | Knöpfe werden farbliche verändert, wenn die Bewegung ausgewählt wird. Wird nach oben gefahren, so wird der Hochzeigende Pfeil farblich dargestellt (grün oder grau).                
GUI	             |legend        | String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: Rezv = Rezept (Rez) für die Geschwindigkeit (v)<br><br>*Eingebaut*:<br> Rezv, IWs, IWv, SWv, uGv, oGv, uGs, oGs, IWxPID , SWxPID, oGPID, uGPID, Rezx         
defaults	     |startSpeed    | Wert der in das Geschwindigkeits-Eingabefeld zur Initialisierung geschrieben wird         
defaults	     |startPos      | Wert der in das Positions-Eingabefeld zur Initialisierung geschrieben wird         

---

##### **Nemo-Achse-Linear:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
nemo-version	|              | Version der genutzten Anlage: **1** oder **2** 
gamepad_Button  |              | String für die Knopf-Zuweisung:<br>*Möglich*: HubS, HubT<br>**HubS** - X & B (Spindel) (Button)<br>**HubT** - ↑ & ↓ (Tiegel)  (Axes)<br><br>*Knöpfe:* <br>X & ↑ - Hoch<br>B & ↓ - Runter<br>Select - Stopp Antriebe
start	        |readTime      | Zeit in Sekunde mit der das Gerät ausgelesen wird  
start	        |init          | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!                   
start	        |invert        | Wenn **True** gewählt wurde, so wird die Geschwindigkeit invertiert. <br>*Gebraucht*: Nemo-1-Anlage Spindel                 
start	        |invert_Pos    | Wenn **True** gewählt wurde, so wird der Positionswert invertiert. <br>*Gebraucht*: Nemo-2-Anlage Spindel (Realer Weg)
start	        |start_weg     | Startweg für den Simulierten Weg                    
start	        |pos_control   | **REAL** – Nutzung der vom Gerät ausgelesen Weges<br>**SIM** – Nutzung des simulierten Weges <br> Weg für Limitkontrolle!         
start	        |sicherheit    | Sicherheits Modus bei Nutzung des Realen Positions-Wertes:<br>**0** - Error und Fehler ignorieren<br>**1** - Error und Stopp
register	    |              | Siehe [Modbus_Nemo_DE.md](Modbus_Nemo_DE.md)	<br>Coils, Input- und Holding-Register für die Kommunikation mit der SPS
parameter	    |nKS_Aus       | Auslese Nachkommerstellen
parameter	    |Vorfaktor_Ist | Vorfaktor für die Ist-Geschwindigkeit       
parameter	    |Vorfaktor_Soll| Vorfaktor für die Soll-Geschwindigkeit      
limits	        |maxPos        | Limit Position Maximum
limits	        |minPos        | Limit Position Minimum
limits	        |maxSpeed      | Limit Geschwindigkeit Maximum   
limits	        |minSpeed      | Limit Geschwindigkeit Minimum  
GUI	            |knopf_anzeige | Knöpfe werden farbliche verändert, wenn die Bewegung ausgewählt wird. Knopf Betätigung wird sichtbar!       
GUI	            |legend        | String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: RezOP = Rezept (Rez) für die Ausgangsleistung (OP)<br><br>*Eingebaut*:<br> Rezv, Rezx, IWs, IWsd, IWv, SWv, SWs, uGv, oGv, uGs, oGs, IWxPID, SWxPID, oGPID, uGPID                   
defaults	    |startSpeed    | Wert der in das Geschwindigkeits-Eingabefeld zur Initialisierung geschrieben wird                       

---

##### **Nemo-Achse-Rotation:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
nemo-version	|               | Version der genutzten Anlage: **1** oder **2**
gamepad_Button	|               | String für die Knopf-Zuweisung:<br>*Möglich*: RotS, RotT<br>**RotS** - Y & A (Spindel) (Button)<br>**RotT** - ← & → (Tiegel)  (Axes)<br><br>*Knöpfe:*<br>Y & ← - ↻ (CW)<br>A & → - ↺ (CCW)<br>Select - Stopp Antriebe
start	        |readTime       | Zeit in Sekunde mit der das Gerät ausgelesen wird
start	        |init           | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!               
start	        |invert         | Wenn **True** gewählt wurde, so wird die Geschwindigkeit invertiert. <br>Gebraucht: Nemo-1-Anlage Spindel
start	        |start_winkel   | Startwinkel für den Simulierten Winkel            
start	        |kont_rot       | Bei **True** wird die Checkbox für das kontinuierliche Rotieren direkt gesetzt!                   
register	    |               | Siehe [Modbus_Nemo_DE.md](Modbus_Nemo_DE.md)	<br>Coils, Input- und Holding-Register für die Kommunikation mit der SPS       
parameter	    |nKS_Aus        | Auslese Nachkommerstellen               
parameter	    |Vorfaktor_Ist  | Vorfaktor für die Ist-Geschwindigkeit              
parameter	    |Vorfaktor_Soll | Vorfaktor für die Soll-Geschwindigkeit             
limits	        |maxWInkel      | Limit Winkel Maximum                   
limits	        |minWinkel      | Limit Winkel Minimum 
limits	        |maxSpeed       | Limit Geschwindigkeit Maximum                   
limits	        |minSpeed       | Limit Geschwindigkeit Minimum                   
GUI	            |knopf_anzeige  | Knöpfe werden farbliche verändert, wenn die Bewegung ausgewählt wird. Knopf Betätigung wird sichtbar!                       
GUI	            |legend         | String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: RezOP = Rezept (Rez) für die Ausgangsleistung (OP)<br><br>*Eingebaut*:<br> Rezv, Rezx, IWs, IWsd, IWv, SWv, SWs, uGv, oGv, uGs, oGs, IWxPID, SWxPID, oGPID, uGPID               
defaults	    |startSpeed     | Wert der in das Geschwindigkeits-Eingabefeld zur Initialisierung geschrieben wird                   
rezept_Loop	    |               |  Anzahl der Rezept-Wiederholungen      

---

##### **Nemo-Gase:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
nemo-version|	        | Version der genutzten Anlage: **1** oder **2**
start	    |readTime   | Zeit in Sekunde mit der das Gerät ausgelesen wird
start	    |init       | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!
register    |	        | Siehe [Modbus_Nemo_DE.md](Modbus_Nemo_DE.md)<br>Coils, Input- und Holding-Register für die Kommunikation mit der SPS
parameter	|nKS_Aus    | Auslese Nachkommerstellen

Da es sich bei *Nemo-Gase* um ein **Monitorings Modul** handelt, fallen alle Write-Funktionen weg, da nur gelesen wird! Daher treffen nicht alle Gemeinsamkeiten auf Nemo-Gase zu wie z.B. `read_trigger`.

---

##### **Nemo-Generator:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
nemo-version	|             | Version der genutzten Anlage: **2**            
start	        |start_modus  | Start-Modus für den Generator (Radio-Button GUI und Nemo-Anlagen-GUI - Coil)<br>Der Generator kann mit Leistung (**P**), Strom (**I**) oder Spannung (**U**) starten.
start	        |Auswahl      | **I** – Nur Strom steht zur Auswahl<br>**PUI** – Umschalten zwischen Strom, Spannung und Leistung möglich          
start	        |readTime     | Zeit in Sekunde mit der das Gerät ausgelesen wird
start	        |init         | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!                               
register	    |             | Siehe [Modbus_Nemo_DE.md](Modbus_Nemo_DE.md)	<br>Coils, Input- und Holding-Register für die Kommunikation mit der SPS        
limits	        |maxI         | Limit Strom Maximum
limits	        |minI         | Limit Strom Minimum
limits	        |maxP         | Limit Leistung Maximum
limits	        |minP         | Limit Leistung Minimum
limits	        |maxU         | Limit Spannung Maximum
limits	        |minU         | Limit Spannung Minimum                 
GUI	            |legend       | String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: RezOP = Rezept (Rez) für die Ausgangsleistung (OP)<br><br>*Eingebaut*:<br> RezI, RezU, RezP, Rezx, IWI, IWU, IWP, IWf, SWI, SWU, SWP, uGI, oGI, uGU, oGU, uGP, oGP, IWxPID, SWxPID, oGPID, uGPID               
parameter	    |nKS_Aus      | Auslese Nachkommerstellen                
defaults	    |startCurrent | Wert der in das Strom-Eingabefeld zur Initialisierung geschrieben wird
defaults	    |startPow     | Wert der in das Leistungs-Eingabefeld zur Initialisierung geschrieben wird
defaults	    |startVoltage | Wert der in das Spannungs-Eingabefeld zur Initialisierung geschrieben wird                        

---

##### **Educrys-Monitoring:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
start	    |readTime   | Zeit in Sekunde mit der das Gerät ausgelesen wird
start	    |init       | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. **ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!
serial-loop-read |		| Anzahl der Wiederholungen bei Fehlerhafter Antwort des Gerätes
parameter	|nKS_Aus    | Auslese Nachkommerstellen

---

##### **Educrys-Antrieb:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
Antriebs_Art	|                 | Educrys verfügt über drei Antriebe<br>**L** – Hub<br>**R** – Rotation<br>**F** – Lüfter 
gamepad_Button	|                 | String für die Knopf-Zuweisung:<br>*Möglich*: EduL, EduR, EduF<br>**EduL** - X, B, ↑ & ↓<br>**EduR** - A, Y, ← & →<br>**EduF** - Start<br><br>*Knöpfe:*<br>X & ↑ - Hoch<br>B & ↓ - Runter<br>A & → - CCW<br>Y & ← - CW<br>Start - Lüfter An<br>Select - Stopp Antriebe
start	        |readTime         | Zeit in Sekunde mit der das Gerät ausgelesen wird
start	        |init             | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!          
start	        |start_weg        | Startposition (*relevant für* Linear-Motor)  
start	        |write_SW         | Bei **True** wird der Start Weg an die Anlage gesendet und die Position gesetzt (*Define Position*). (*relevant für* Linear-Motor)              
start	        |write_SLP        | Bei **True** werden die Positions-Limits an die Anlage gesendet. (*relevant für* Linear-Motor)               
start	        |sicherheit       | Sicherheits Modus bei Nutzung des Realen Positions-Wertes:<br>**0** - Error und Fehler ignorieren<br>**1** - Error und Stopp              
serial-extra	|serial-loop-read | Anzahl der Wiederholungen bei Fehlerhafter Antwort des Gerätes                      
serial-extra	|rel_tol_write_ans| Die Relative Toleranz zum Vergleich der Antwort des Gerätes mit dem gesendeten Befehl!                      
parameter	    |nKS_Aus          | Auslese Nachkommerstellen          
limits	        |maxPos           | Limit Position Maximum          
limits	        |minPos           | Limit Position Minimum 
limits	        |maxSpeed         | Limit Geschwindigkeit Maximum              
limits	        |minSpeed         | Limit Geschwindigkeit Minimum 
GUI	            |knopf_anzeige    | Knöpfe werden farbliche verändert, wenn die Bewegung ausgewählt wird. Knopf Betätigung wird sichtbar!                  
GUI	            |legend           | String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: RezOP = Rezept (Rez) für die Ausgangsleistung (OP)<br><br>*Eingebaut*:<br> Rezv, Rezx, IWs, IWsd, IWv, uGv, oGv, uGs, oGs, IWxPID, SWxPID, oGPID, uGPID          
defaults	    |startSpeed       | Wert der in das Geschwindigkeits-Eingabefeld zur Initialisierung geschrieben wird             
defaults	    |startPos         | Wert der in das Positions-Eingabefeld zur Initialisierung geschrieben wird              
rezept_Loop	    |                 | Anzahl der Rezept-Wiederholungen  

---

##### **Educrys-Heizer:**

**Ebene 1** | **Ebene 2** | **Erläuterung**
--- | --- | ---
start	        |PID_Write        | Bei **True** werden die Eurotherm PID-Parameter zur Initialisierung beschrieben.               
start	        |start_modus      | **Manuel** für den Manuellen Modus<br>**Auto** für den Automatischen Modus
start	        |readTime         | Zeit in Sekunde mit der das Gerät ausgelesen wird
start	        |init             | Bei **True** wird das Gerät initialisiert!<br>Bei **False** wird das Senden von Befehlen geblockt, sodas VIFCON startet und die Initialisierung später erfolgen kann. <br>**ACHTUNG**: Die Schnittstelle die konfiguriert wurde muss exestieren!!          
start	        |ramp_start_value | Startwert einer Rampe, wenn diese als Segment 1 im Rezept gewählt wird!!<br>**IST** – Istwert<br>**SOLL** – Sollwert               
serial-extra	|serial-loop-read | Anzahl der Wiederholungen bei Fehlerhafter Antwort des Gerätes                       
serial-extra	|rel_tol_write_ans| Die Relative Toleranz zum Vergleich der Antwort des Gerätes mit dem gesendeten Befehl!                      
PID-Device	    |PB               | Educrys-PID-Größe - P-Anteil      
PID-Device	    |TI               | Educrys-PID-Größe - I-Anteil        
PID-Device	    |TD               | Educrys-PID-Größe - D-Anteil       
parameter	    |nKS_Aus          | Auslese Nachkommerstellen        
limits	        |maxTemp          | Limit Temperatur Maximum        
limits	        |minTemp          | Limit Temperatur Minimum 
limits	        |oPMax            | Limit Leistung am Ausgang Maximum          
limits	        |oPMin            | Limit Leistung am Ausgang Minimum          
GUI	            |legend           | String mit Kurven-Namen für die Legende<br>*Aufbau*: Wert-Art + Größe<br>*Beispiel*: RezOP = Rezept (Rez) für die Ausgangsleistung (OP)<br><br>*Eingebaut*:<br> RezT, RezOp, IWT, IWOp, IWTPID, SWT, SWTPID, uGT, oGT, uGOp, oGOp, oGPID, uGPID          
defaults	    |startTemp        | Wert der in das Temperatur-Eingabefeld zur Initialisierung geschrieben wird               
defaults	    |startPow         | Wert der in das Leistungs-Eingabefeld zur Initialisierung geschrieben wird               

## Auslese sicher:

In den Modulen (Widget, Device) wurden alle Konfigurationen überprüft. Auch im Controller (Haupt-Init) wurde dies eingebaut. Hierbei gibt es immer eine Prüfung des Schlüssels und des dazugehörigen Wertes. Beim Wert wird geschaut ob dieser vom richtigen Typ ist oder ob der Wert überhaupt genutzt werden darf. 

**Beispiel:**

Schlüssel-Test:
```
try: self.init = self.config['start']['init']
except Exception as e: 
  logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
  logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
  self.init = False
```

*Meldungen:*   
```
2024-09-26 16:36:39,210 WARNING vifcon.view.truHeat - TruHeat - Fehler beim Auslesen der Config bei Konfiguration: start|init ; Setze auf Default: False
2024-09-26 16:36:39,217 ERROR vifcon.view.truHeat - TruHeat - Fehlergrund:
Traceback (most recent call last):
  File "z:\Gruppen\modexp-all\Private\work\Vincent\vifcon\vifcon\view\truHeat.py", line 130, in __init__
    try: self.init = self.config['start']['init']
                     ~~~~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 'init'
```

---

Wert-Test:    
```
if not type(self.init) == bool and not self.init in [0,1]: 
  logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
  self.init = 0
```

*Meldungen:*  
```
2024-09-26 16:38:00,026 WARNING vifcon.view.truHeat - TruHeat - Konfigurationsfehler im Element: init - Möglich sind: [True, False] - Default wird eingesetzt: False - Fehlerhafte Eingabe: Truea
```

## Letzte Änderung

Die Letzte Änderung des [Templates](#Konfigurations-Templates) und dieser Beschreibung war: 17.02.2025