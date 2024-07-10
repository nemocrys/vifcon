# Informationen zu den Rezepten

Im folgenden werden die einzelnen Rezept-Segmente, der Aufbau und die Auslagerung dieser Rezepte gezeigt.

## Vorhandene Rezept-Segmente

Die Rezepte hängen von den Geräten ab. Bis auf das Eurotherm Gerät sind alle Rezepte gleich aufgebaut. Somit gibt es folgende Arten von Rampen:

s	-	Sprung  
r	-	Rampe

Eurotherm Temperatur spezifisch:  
er	-	Eurotherm eigene Rampe  
op	-	Leistungssprung in einem Temperaturrezept   
opr	-	Leostungsrampe in einem Temperaturrezept  

Für Eurotherm Leistung, TruHeat, Nemo-Antriebe (Hub, Rotation) und PI-Achse sind nur s und r verfügbar!

## Aufbau Allgemein:

```
Sprung:			    SN: t ; So  ; s
Rampe:			    SN: t ; ZS  ; r   ; RZ
Eurotherm Rampe:	SN: t ; ZS  ; er  ; m
Leistungs Sprung:	SN: t ; SoT ; op  ; SoL
Leistungs Rampe:	SN: t ; ZST ; opr ; ZSL ; RZ ; SR
```
Legend:  
- SN - Schritt Nummer
- t - Zeit
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
    - Solange dauert der Rezept Schritt, Einheit Sekunden
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
- Wenn bei "Leistungs Rampe" bei "Startwert Rampe" kann auch nichts angegeben werden, dann Startet die Leistungsrampe bei Null. 
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

- Beispiel:            
	- Config.yml:
        ```   
            rezept_Ram_3:    
                dat: rezept.yml
        ```
        - rezept.yml:
        ```
            n0: 3600 ; 500 ; er  ; 0.133
            n1: 600  ; 500 ; s 
            n2: 600  ; 500 ; op  ; 20
            n3: 1200 ; 200 ; r   ; 3
            n4: 600  ; 200 ; opr ; 5 ; 1 ; 20 
            n5: 600  ; 20  ; er  ; 0.3
        ```

Das Beispiel zeigt auch mit n0 bis n5 wie es in der Config-Datei direkt aussehen müsste. Der Nutzer kann festlegen wo das Rezept stehen soll! Das gezeigte Beispiel kann in Abbildung [Beispiel_Rezepte.png](../Bilder/Beispiel_Rezepte.png) gefunden werden. 
