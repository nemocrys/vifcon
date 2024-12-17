# Modbus und VIFCON

In VIFCON wird neben der RS232 Schnittstelle auch das Modbus-Kommunikationsprotokoll genutzt. Für die Umsetzung von Modbus wird als Schnittstelle Ethernet benötigt, sowie ein Master (PC) und ein Slave. Der Slave sind die Anlagen des IKZ. 

Zu Modbus-Theorie kann mehr in der Master-Arbeit, siehe [Readme](../Readme.md) nachgelesen werden. IN VIFCON wird für die Umsetzung in Python die *pyModbusTCP*-Bibliothek genutzt. Die Dokumentation für diese Bibliothek kann im [Python_RPi_DE.md](Python_RPi_DE.md) gefunden werden.

In VIFCON gibt es drei Geräte die Modbus nutzen. Diese sind:

- [**nemoAchseLin.py**](../vifcon/devices/nemoAchseLin.py),
- [**nemoAchseRot.py**](../vifcon/devices/nemoAchseRot.py) und,
- [**nemoGase.py**](../vifcon/devices/nemoGase.py).

Alle drei Objekte sprechen dabei mit den Anlagen Nemo-1 und Nemo-2 der Modellexperimente Gruppe des IKZ. 

## Kommunikationsdaten

Neben der IP-Adresse und dem Port, benötigt die Kommunikation Register-Nummern. Modbus arbeitet mit Registern, die ein Word beinhalten. Jedes Word besteht dabei aus 16 Bit (2 Byte). In VIFCON werden zur Umsetzung:

- **Coils**,
- **Holding-Register** und,
- **Input-Register** verwendet.

Die *pyModbusTCP*-Bibliothek übernimmt den Großteil der Kommunikation, sodass der Nutzer nur noch die Startadresse und die Anzahl von zulesenden Registern angeben muss.

### Coils

Coils beinhalten nur Boolche Werte. In VIFCON werden diese als Knöpfe verwendet. So kann z.B. die Antriebsbewegung gestartet werden. 

### Holding-Register

Bei den Holding-Registern handelt es sich um Register, die Werte vom Master erhalten und umsetzen. So sendet VIFCON z.B. die Sollgeschwindigkeit für die Antriebe an Modbus, sodass die SPS diese dann umsetzen kann.

### Input-Register 

Die Input-Register sind nun das Gegenteil zu den Holding-Registern. Der Master sendet eine Abfrage an den Slave und erhält Messdaten von der SPS. So können z.B. die Istwerte der Geschwindigkeit ausgelesen werden. 

## Spezifiche Register

Die Anlagen unterscheiden sich bei ihren Registern. Dadurch das das Antriebs-Statusword der Antriebe nicht mehr nur ein Word ist, verschieben sich einige Register. Die folgende Tabellen zeigen diese Werte:

### Hub-Antrieb - Spindel (oben)

Config-Bezeichnung |  Art | Nemo-1 Start-Register | Nemo-2 Start-Register
--- | --- | --- | --- 
hoch        | Coil    | 17 | 17
runter      | Coil    | 18 | 18
stopp       | Coil    | 16 | 16
lese_st_Reg | Input   | 38 | 39
write_v_Reg | Holding |  4 |  4
posAktuel   | Input   | 42 | 43
posLimReg   | Input   | 46 | 47
InfoReg     | Input   |  / | 143
statusReg   | Input   | 50 | 51
statusRegEil| Input   |  / | 155

### Rotations-Antrieb - Spindel (oben)

Config-Bezeichnung |  Art | Nemo-1 Start-Register | Nemo-2 Start-Register
--- | --- | --- | --- 
cw          | Coil    | 21 | 21
ccw         | Coil    | 20 | 20
stopp       | Coil    | 19 | 19
lese_st_Reg | Input   | 51 | 53
write_v_Reg | Holding |  6 |  6
statusReg   | Input   | 55 | 57

### Hub-Antrieb - Tiegel (unten)

Config-Bezeichnung |  Art | Nemo-1 Start-Register | Nemo-2 Start-Register
--- | --- | --- | --- 
hoch        | Coil    |  1 |  1
runter      | Coil    |  2 |  2
stopp       | Coil    |  0 |  0
lese_st_Reg | Input   | 20 | 20
write_v_Reg | Holding |  0 |  0
posAktuel   | Input   | 24 | 24
posLimReg   | Input   | 28 | 28
InfoReg     | Input   |  / | 121
statusReg   | Input   | 32 | 32
statusRegEil| Input   |  / | 133

### Rotations-Antrieb - Tiegel (unten)

Config-Bezeichnung |  Art | Nemo-1 Start-Register | Nemo-2 Start-Register
--- | --- | --- | --- 
cw          | Coil    |  4 |  4
ccw         | Coil    |  5 |  5
stopp       | Coil    |  3 |  3
lese_st_Reg | Input   | 33 | 34 
write_v_Reg | Holding |  2 |  2
statusReg   | Input   | 37 | 38

### Monitoring

Config-Bezeichnung |  Art | Nemo-1 Start-Register | Nemo-2 Start-Register
--- | --- | --- | --- 
lese_st_Reg_VGP_1   | Input | 2 |   2
lese_st_Reg_VGP_2   | Input | / |  58
lese_st_Reg_K       | Input | / | 161
lese_st_Reg_AS      | Input | / | 209

### Generatoren

Die Generatoren exestieren nur bei der Nemo-2-Anlage!

Config-Bezeichnung |  Art | Generator-Schnitstelle 1 Start-Register | Generator-Schnitstelle 2 Start-Register | Generator-Schnitstelle 3 Start-Register
--- | --- | --- | --- | ---
lese_st_Reg         | Input   | 217 | 257 | 297
lese_st_Reg_Info    | Input   | 229 | 269 | 309
lese_st_Reg_Status  | Input   | 248 | 288 | 328
lese_st_Reg_Gkombi  | Input   | 337 | 337 | 337
write_Soll_Reg      | Holding |  72 |  78 |  84
gen_Ein             | Coil    | 129 | 136 | 143
gen_Aus             | Coil    | 130 | 137 | 144
gen_P_Ein           | Coil    | 132 | 139 | 146
gen_I_Ein           | Coil    | 133 | 140 | 147
gen_U_Ein           | Coil    | 134 | 141 | 148


## Letzte Änderung

Die Letzte Änderung dieser Beschreibung war: 17.12.2024