# Informationen zu den Rezepten

Im folgenden werden die einzelnen Rezept-Segmente, der Aufbau und die Auslagerung dieser Rezepte gezeigt und erläutert.

## Letzte Änderung

Die Letzte Änderung dieser Beschreibung war: 12.8.2024

## Vorhandene Rezept-Segmente

Die Rezepte hängen von den Geräten ab. Bis auf das Eurotherm Gerät sind alle Rezepte gleich aufgebaut. Somit gibt es folgende Arten von Rezept-Segmenten:

s	-	Sprung  
r	-	Rampe

Eurotherm Temperatur spezifisch:  
er	-	Eurotherm eigene Rampe  
op	-	Leistungssprung in einem Temperaturrezept   
opr	-	Leostungsrampe in einem Temperaturrezept  

Für Eurotherm Leistung, PID-Modus, TruHeat, Nemo-Antriebe (Hub, Rotation) und PI-Achse sind nur s und r verfügbar!

## Aufbau Allgemein:

```
Sprung:             SN: t ; So  ; s
Rampe:              SN: t ; ZS  ; r   ; RZ
Eurotherm Rampe:    SN: t ; ZS  ; er  ; m
Leistungs Sprung:   SN: t ; SoT ; op  ; SoL
Leistungs Rampe:    SN: t ; ZST ; opr ; ZSL ; RZ ; SR
```
Legend:  
- SN - Schritt Nummer
- t - Segment-Zeit
- RZ - Rampensprung Zeitabstand
- ZS - Zielsollwert
- ZST - Zielsollwert Temperatur
- ZSL - Zielsollwert Leistung
- So - Sollwert
- SoT - Sollwert Temperatur
- SoL - Sollwert Leistung
- m - Steigung
- SR - Startwert Rampe

### Beschreibung:
1. Zeit:	
    - Solange dauert das Segment, Einheit Sekunden
2.  Sollwert: 			
    - Wert zu dem gesprungen werden soll.
3.  Zielsollwert:			
    - Ende der Rampe
4.  Steigung:			
    - Steilheit der Rampe
	    - er:  z.B. 0.01 --> Übergabe an Eurotherm, Bedeutung 0.01°C/s
        - Berechnung: m = delta y / delta x
            - z.B. Rezept: `n1: 600 ; 200 ; er ; 0,297` mit einer Starttemperatur von 25°C
            - m = (200°C - 25°C)/ 600 s = 0,297 °C/s
5.  Rampensprung Zeitabstand:	
    - Abstand der Rampensprünge
    - Beispiele:  
		- r:   
            - Angabe in Config: 1 s
            - bei Zeit = 10 s und Zielsollwert = 100°C 
            - Starttemperatur: 30°C    
            --> 10 s/1 s = 10  
            --> (100°C - 30°C)/10 s = 7 °C (Sprünge)   
            --> Jede Sekunde ein Sprung
		- opr:  
            - Angabe in Config: 2 s
            - bei Zeit = 10 s und Zielsollwert = 100 % 
            - Startleistung: 0 %   
            -> 10 s/2 s =  5   
            -> (100 % -  0 %)/5 s  = 20 % (Sprünge)   
            -> Alle 2 Sekunden ein Sprung 
6. Startwert:	
    - Beginn der Rampe

## Besonderheiten:
- Leistungsrezepte bei Eurotherm werden durch s und r erzeugt. Wenn eine Leistung in einem Temperatur-Rezept verändert werden soll, dann werden dort op und opr genutzt.
- Bei "Leistungs Sprung" kann bei "Sollwert Leistung" auch IST angegeben werden. Dadurch wechselt nur der Modus des Eurotherms auf Manuell. Der aktuelle Leistungswert wird als Istwert/Sollwert gehalten. 
- Bei "Leistungs Rampe" kann bei "Startwert Rampe" auch nichts angegeben werden, dann Startet die Leistungsrampe bei Null. 
- Bei "Leistungs Sprung" und "Leistungs Rampe" wird auch ein Temperatursprung ausgelöst. 

## Auslagern von Rezepten

Der Ordner **rezepte** ist für VIFCON-Rezepte vorgesehen. Das Format dieser Datein ist Yaml (.yml). 
Diese Rezepte werden aus der Config-Datei folgendermaßen aufgerufen:

```
dat: Dateiname
```

Das **dat** muss  enthalten sein, wenn Rezepte ausgelagert werden. Die Configuration der Rezepte kann nun auch über eine seperate Datei durchgeführt werden. Für diesen Zweck müssen drei Dinge eingehalten werden:
1. Schritt muss ***dat*** heißen!
2. Rezeptdatei muss im Ordner 'vifcon/rezepte/' liegen!
3. In der Datei dürfen nur die Schritte stehen!
4. Die normalen Config-Rezept-Schritte dürfen niemals dat heißen!

In dem Ordner *rezepte* befindet sich die Beispiel-Datei [rec_example.yml](../vifcon/rezepte/rec_example.yml), welche eine Datei mit den hier zu finden Erläuterung enthält.

## Beispiele
           
1. Rezept in Config-Datei konfigurieren:
    ``` 
    device:
        Eurotherm:
            # Sonstige Einstellungen
            rezepte:
                Test_Rezept_1:  
                    n1: 600 ; 100 ; r ; 100
                Test_Rezept_2:
                    n1: 600 ; 100 ; r ; 10
                Test_Rezept_3:    
                    dat: rec_example.yml
    ```

Beachtet müssen hier nur die Einrückungen, damit alles richtig ausgelesen werden kann. 

2. Ausgelagerte Datei konfigurieren:
    - rec_example.yml:
        ```
        n0: 3600 ; 500 ; er  ; 0.133
        n1: 600  ; 500 ; s 
        n2: 600  ; 500 ; op  ; 20
        n3: 1200 ; 200 ; r   ; 3
        n4: 600  ; 200 ; opr ; 5 ; 1 ; 20 
        n5: 600  ; 20  ; er  ; 0.3
        ```

Diese Datei benötigt keine Einrückungen. Kommentare können in diesen Dateien erstellt werden, beachte hierbei aber das bestimmte Zeichen wie z.B. "\t" nicht außerhalb der Kommentare auftauchen!

---

**Test_Rezept_1:**

<img src="../Bilder/Beispiel_Rezept_1.png" alt="Rezept Beispiel 1" title='Rezept Beispiel 1 - r-Segment' width=700/>

In dem Beispiel wird nur ein r-Segment erzeugt.Mit dem *Test_Rezept_2* soll hier die Nutzung von dem r-Segment Teil *Rampensprung Zeitabstand* gezeigt werden. Die letzte Zahl gibt somit die Genauigkeit bzw. die Häufigkeit der Sollwertsprünge in diesem Segment an. Je kleiner die Zahl, desto eher ähnelt das Segment einer linearen Funktion.

**ACHTUNG**: Sprünge sind die größte Belastung für ein System. Für die Nutzung dieser Art Rampe, sollten genügend Test durchgeführt werden, somit diese sicher mit dem System funktioniert. Beim Eurotherm-Regler könnten durch eine schlechte oder nicht konfigurierte Regelung Spitzen in der Ausgangsleistung bei jedem Sprung entstehen!!

---

**Test_Rezept_2:**

<img src="../Bilder/Beispiel_Rezept_2.png" alt="Rezept Beispiel 2" title='Rezept Beispiel 2 - r-Segment' width=700/>

--- 

**Test_Rezept_3:**

Das Beispiel zeigt auch mit n0 bis n5 wie es in der Config-Datei direkt aussehen müsste. Der Nutzer kann festlegen wo das Rezept stehen soll! Das gezeigte Beispiel kann in Abbildung [Beispiel_Rezept_3.png](../Bilder/Beispiel_Rezept_3.png) gefunden werden und ist folgend zu sehen. 

In dem Beispiel werden alle 5 Segmentarten genutzt. Somit handelt es sich um einen Eurotherm-Regler. Das gezeigte Rezept hier ist auch Teil des [Config-Templates](../Template/config_temp.yml). 

<img src="../Bilder/Beispiel_Rezept_3.png" alt="Rezept Beispiel 3" title='Rezept Beispiel Eurotherm 1' width=700/>

---

**Weitere Beispiele:**

Rezept:
```
n1: 10 ; 100 ; er ; 8
n2: 10 ; 100 ; s
n3: 10 ; 200 ; r ; 0,667
n4: 10 ; 200 ; op ; 20
n5: 10 ; 200 ; opr ; 0 ; 0,667 ; 20
```
Plot:    
<img src="../Bilder/Beispiel_Rezept_4.png" alt="Rezept Beispiel 4" title='Rezept Beispiel Eurotherm 2' width=700/>

Dieses Rezept ist ähnlich zu *Test_Rezept_3*. Hierbei gibt es nun eine manuelle Beschriftung der einzelnen Segmente.  

---

Rezept:
```
n1: 600 ; 100 ; s
n2: 600 ; 50 ; op ; 10
n3: 600 ; 20 ; s
```
Plot:    
<img src="../Bilder/Beispiel_Rezept_5.png" alt="Rezept Beispiel 5" title='Rezept Beispiel Eurotherm 3' width=700/>

Mit dem Beispiel soll gezeigt werden, dass es möglich ist bei op und opr auch einen Temperatur-Sprung durchzuführen. 

---

Rezept:
```
n1: 1 ; -2 ; s
n2: 4 ; -1 ; s
n3: 1 ; -0.5 ; s
n4: 1 ; 1 ; s
n5: 5 ; 2 ; s
```
Plot:    
<img src="../Bilder/Beispiel_Rezept_6.png" alt="Rezept Beispiel 6" title='Rezept Beispiel PI-Achse' width=700/>

Auch dieses Rezept ist im [Template der Configdatei](../Template/config_temp.yml) zu finden. Dieses Rezept ist z.B. für die PI-Achse. 

