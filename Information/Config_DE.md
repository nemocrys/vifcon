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

## Erklärung der einzelnen Punkte

In dem Template der Datei ([config_temp.yml](../Template/config_temp.yml)) können auch Beschreibungen gefunden werden. 

Im folgenden sind die Punkte:
1. [Reaktionstimer](#reaktionstimer)
2. [Feature-Überspringen](#feature-überspringen)
3. [Speicher Dateien und Bilder](#speicher-dateien-und-bilder)
4. [Sprache](#sprache)
5. [GUI-Widget-Rahmen](#gui-widget-rahmen)
6. [Logging-Datei](#logging-datei)
7. [Konsolen-Logging](#konsolen-logging)
8. [Legende der GUI](#legende)
9. [Skalierungsfaktoren](#skalierungsfaktoren)
10. [Geräte](#geräte)

### Reaktionstimer:

```
time:
  dt-main: 150
```
Nach dieser Zeit (in ms) werden die Threads der Geräte aufgerufen bzw. die sample-Funktion des Sampler-Objektes in dem Thread. 

### Feature-Überspringen 

```
Function_Skip:                                                
  Multilog_Link: 0        
  Generell_GamePad: 0
```
Wenn der Wert auf True (1) steht, so werden die Funktionen für den Multilog-Link und dem Gamepad freigeschaltet. Bei False wird dies im Code übersprungen und wirkt sich nicht auf VIFCON aus. 

### Speicher Dateien und Bilder

```
save:
  config_save: True                                
  log_save: True   
  plot_save: True
```

Am Ende der Anwendung wird die Config-Datei und die Log-Datei aus dem Hauptordner in den Messordner kopiert. Auch die Legende und die Plots werden gespeichert. Dies passiert bei True. 

Beachtet werden muss hierbei, dass die Plots und die Legende so gespeichert werden, wie sie in der GUI zu sehen sind. 

### Sprache

```
language: de
```

Hier wird in dem Wert die Sprache angegeben. Dabei können nur Deutsch (DE) und Englisch (EN) ausgewählt werden. Die GUI ändert sich dementsprechend.

### GUI-Widget-Rahmen

```
GUI_Frame: 0
```

Wenn der Wert auf True (1) steht, dann werden die Rahmen der Widgets eingeschaltet. Mit diesem Mittel kann die Platzierung der einzelnen Widgets angesehen werden. 

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

Bei einigen Systemen muss das encoding auskommentiert werden, da z.B. Linux dadurch einen Fehler ausgibt. 

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
```

Durch die Skalierungsfaktoren kann der Plot der GUI geändert werden. Nicht immer sind die verschiedenen Größen im selben Wertebereich. Sobald der Wert ungleich eins ist, wird die Kurve um diesen Wert skalliert. Diese Skalierung wird in dem Label der y-Achse angezeigt. Weiterhin bewirken bestimmte Zahlen in dem Sinne auch eine Änderung. Die Zahl 1 als Skalierungsfaktor wird nicht im y-Achsen-Label angezeigt. Bei einer Null wird die Große aus dem y-Achsen-Label entfernt. Wenn keine Größe im Label mehr enthalten ist, so wird *Keine Einträge!* angezeigt.

### Geräte

```
devices:
  Eurotherm 3504:
    ...
  PI-Achse_h:
    ...
```

Unter dem Schlüssel ***devices*** finden sich nun alle vorhandenen Geräte wieder. Jedes Gerät muss dabei einen bestimmten Namens-Teil haben:

Gerät                          | String-Teil
-------------------------------|----------------------
Eurotherm                      | Eurotherm
TruHeat                        | TruHeat
PI-Achse                       | PI-Achse
Nemo-1-Anlage Hub-Antrieb      | Nemo-Achse-Linear
Nemo-1-Anlage Rotation Antrieb | Nemo-Achse-Rotation
Nemo-1-Anlage Sensoren         | Nemo-Gase

Bei der PI-Achse und dem Eurotherm-Regler ist ein Beispiel am Anfang zu finden. Die einzelnenen Geräte haben nun teilweise Unterschiede und teilweise Gemeinsamkeiten.

#### Gemeinsamkeiten

1. ```skip: 1```
    - Um ein Gerät nicht in die GUI zu übertragen, muss bei diesem Schlüssel der Wert True (1) ausgewählt werden. In dem Fall wird die Definition des Gerätes im Programm übersprungen.
2. ```typ:  Generator```
    - Auswahlmöglichkeiten: Generator, Antrieb, Monitoring
    - Generator: Eurotherm, TruHeat
    - Antrieb: PI-Achse, Nemo-Achse-Linear, Nemo-Achse-Rotation
    - Monitoring: Nemo-Gase
    - Durch diesen Schlüssel wird die Seite und Tab des Widgets bestimmt. 
3. ```ende: 0```
    - Mit diesem Schlüssel wird der Sichere Endzustand aktiviert. Wenn der Wert auf True (1) steht, dann wird bei Ausführung des Exits (Ende der Anwendung) die Stop-Funktion des jeweiligen Gerätes aktiviert und ausgeführt. 
4.  ```serial-interface```
    - Schnittstellen-Eigenschaften für die Kommunikation
    - RS233
      - port, baudrate, bytesize, stopbits, parity, timeout
      - Eurotherm, TruHeat, PI-Achse
    - Modbus
      - host (Server-IP-Adresse), port, debug
      - Nemo-1-Anlage
5. Multilog-Link 
    ```
      multilog:
        trigger: pi1                                 
        port: 54629
    ```
    - Trigger-Wort hängt von Multilog Konfiguration ab
    - Port hängt von Multilog Konfiguration ab
    - Durch diesen Schlüssel, sendet VIFCON seine Daten an Multilog.
6. Limits
    - Jedes Gerät hat bestimmte Limits.
    - Diese Limits sind Software-Limits, wodurch das Senden von Werten nur bis zu diesen Werten funktioniert.
    - Beispiel Eurotherm:
      ```
        limits:
        maxTemp: 1000
        minTemp: 0
        opMax: 35 
        opMin: 0
      ```
7. GUI-Kurven
    ```
      GUI:
        legend: RezOp ; RezT ; IWT ; IWOp ; SWT ; uGT ; oGT ; oGOp ; uGOp
    ```
    - Mit dieser Konfiguration wird dem Programm gesagt, welche Kurven im Plot angezeigt werden sollen. 
    - Je nach Gerät gibt es andere Bezeichnungen.
    - Grundlegend: Rezepte, Istwerte, Sollwerte, Obere Grenze, Untere Grenze + Größenbezeichnung
    - z.B. RezOP bedeutet Rezeptkurve für Operating Point (Leistung)
8. Eingabefeldanzeige
    ```
      defaults:
        startTemp: 20  
        startPow: 25 
    ```
    - Diese Werte werden zu Beginn des Programms in der GUI angezeigt. 
9. Rezepte:
    - Für diesen Punkt sehe bitte [Rezepte_DE.md](Rezepte_DE.md).

#### Unterschiede

**Eurotherm:**

```
    start:
      sicherheit: 0
      start_modus: Auto
      readTime: 2 
      init: 1
      ramp_start_value: ist 
```

*sicherheit*:
  - Legt fest wie der Maximale Leistungsausgang (HO) gesetzt wird. 
  - True: HO kann nur am Gerät geändert werden
  - False: HO kann von VIFCON nur gelesen werden, wodurch OPmax angepasst wird (1. Menü-Knopf, 2. Umschalten auf Manuel-Mode)

*start_modus*:
  - Möglichkeiten: Auto, Manuel
  - Eurotherm besitzt zwei Modies
    - Automatischer Modus: 
      - Regelung der Temperatur aktiv
      - PID-Regler sorgt für Leistungsausgang
    - Manueller Modus:
      - Benutzer legt Leistungsausgang fest

*readtime*:
  - Zeitintervall, wann das Gerät ausgelesen werden soll
  - eine Null schaltet das Lesen von Werten ab

*init*:
  - Initalisierung des Gerätes erfolgen oder nicht erfolgen
  - True: 
    - Gerät hängt an der Schnittstelle und wird direkt vom Programm angesprochen
  - False:
    - Schnittstelle existiert, das Gerät hängt aber noch nicht umbedingt daran
    - Programm sorgt dafür, dass keine Befehle gesendet werden

*ramp_start_value*:
  - Möglich: IST, SOLL
  - Jenach Auswahl fängt die erste Rampe beim Sollwert oder dem Istwert an

**TruHeat:**

```
tart:
      start_modus: P
      readTime: 0
      init: True 
      ad: '00001'
      watchdog_Time: 5000
      send_Delay: 20 
```

*init* und *readTime* sind bei allen Geräten identisch, siehe Eurotherm für Erklärung!

*start_modus*:
  - Möglich: P, I, U
  - Durch das setzen wird der Radio-Button in der GUI auf die Größe gesetzt.

*ad*:
  - TruHeat-Generator Adresse

*watchdog_Time*:
  - Der TruHeat besitzt einen Watchdog Timer als Sicherheitsfunktion. Der Zeitwert in Millisekunden wird zu Beginn des Programms gesetzt. 

*send_Delay*:
  - Hier kann eine Zeit in Millisekunden festgelegt werden, die eine Verzögerung zwischen dem Senden von Befehlen verursacht.
  - Sollte nicht Größer als die Watchdog Zeit sein!

**PI-Achse:**

1. ```mercury_model: C862```
    - Bei der PI-Achse wurden zwei verschiedene Modelle des Mercury-Models genutzt. Diese waren C862 und C863.
    - Beide Modelle haben kleine Unterschiede. Speziell bei der Messung bzw. dem Auslesen der Geschwindigkeit.

2. ```gamepad_Button: PIh```
    - Möglich bei PI-Achse: PIh, PIz, PIx, PIy
    - Durch diesen Schlüssel, werden bestimmte Knöpfe für bestimmte Achsen-Bewegungs-Richtungen freigeschaltet.

3. Start:
    - Bei der PI-Achse gibt es nur *init*, *readTime* und *mode*.
    - Die ersten beiden sind wie bei den anderen (siehe Eurotherm).
    - *mode*
      - Verriegelungsmodus der Bewegungsknöpfe
      - 0 - Keine Verriegelung
      - 1 - Entriegelung durch Timer
      - 2 - Entriegelung durch erreichen von 0 mm/s

4. Parameter:
    ```
      parameter:
        adv: '0133' 
        cpm: 29752 
        mvtime: 25  
        nKS_Aus: 3  
    ```
    - *adv* = Adressauswahlcode
    - *cpm* = Counts per mm
      - Umrechnungsfaktor
    - *mvtime*
      - Auslese-Delay für die Achsengeschwindigkeit (ms)
      - Wird für den Befehl MV bei C862 benötigt
    - *nKS_Aus*
      - angezeigte Nachkommastellen

**Nemo-Achse-Linear und Nemo-Achse-Rotation:**

1. ```gamepad_Button: HubS```
    - Möglich bei Linear: HubS, HubT
    - Möglich bei Rotation: RotS, RotT
    - Durch diesen Schlüssel, werden bestimmte Knöpfe für bestimmte Achsen-Bewegungs-Richtungen freigeschaltet.

2. Start:
    - Bei der PI-Achse gibt es nur *init*, *readTime*, *invert* und *start_weg* oder *start_winkel*.
    - Die ersten beiden sind wie bei den anderen (siehe Eurotherm).
    - *invert*
      - True: Invertierung des Geschwindigkeitswertes
        - Bei der Spindel würden Rezept und Reale Geschwindigkeit sich unterscheiden!
    - *start_weg* oder *start_winkel*
      - Bei der Nemo-1-Anlage wird der Weg und die Geschwindigkeit selbst berechnet. 
      - Aus dem Grund kann man hier einen Start Wert angeben.
  
  3. Modbus-Register
      ```
        register:
          hoch: 17 
          runter: 18  
          stopp: 16   
          lese_st_Reg: 38  
          write_v_Reg: 4  
          posLimReg: 46
          statusReg: 50
      ```
      - Bei der Nemo-Anlage werden bestimmte Register gesetzt.
      - Hierbei werden Coils, Input-Register und Holding-Register angesprochen.
  
  4. Parameter:
      - Diese haben *nKS_Aus* und *Vorfaktor*.
      - Ersteres sind wieder die Nachkommerstellen die Angezeigt werden.
      - Der Vorfaktor diente der Korrektur des Fehlerhaften fahrens. Die eingestellte Geschwindigkeit war nicht die richtig, die auch bei den Antrieben ankam.  

**Nemo-Gase:**

- Besitzt weniger Teile, da nur ausgelesen wird.
- Werte werden nur in GUI angezeigt und können an Multilog übergeben werden.
- Ähnlich wie der Rest von Nemo-1.