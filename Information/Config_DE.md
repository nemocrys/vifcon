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
3. [Speicher Datein und Bilder](#speicher-datein-und-bilder)
4. [Sprache](#sprache)
5. [GUI-Widget-Rahmen](#gui-widget-rahmen)
6. [Logging-Datei](#logging-datei)
7. [Konsolen-Logging](#konsolen-logging)
8. [Legende der GUI](#legende)

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

### Speicher Datein und Bilder

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

Hier wird in dem Wert die Sprache angegeben. Dabei können nur Deutsch (DE) und Englisch (EN) ausgewählt werden. 

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



Schlüssel | Wert          | Erklärung
----------|---------------|------------
time      | dt-main       | Reaktionszeit in ms, Aufruf der Threads
Function_Skip | Multilog_Link | Bei True wird die Verbindung zu Multilog eingerichtet!
Function_Skip | Generell_Gamepad | Bei True wird die Verbindung zu einem Gamepad eingerichtet!



