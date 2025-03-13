# Modbus and VIFCON

In addition to the RS232 interface, VIFCON also uses the Modbus communication protocol. To implement Modbus, Ethernet is required as an interface, as well as a master (PC) and a slave. The slave is the IKZ system.

You can read more about Modbus theory in the master's thesis, see [Readme](../README.md). IN VIFCON, the *pyModbusTCP* library is used for implementation in Python. The documentation for this library can be found in [Python_RPI_En.md](Python_RPI_En.md).

In VIFCON there are three devices that use Modbus. These are:

- [**nemoAchseLin.py**](../vifcon/devices/nemoAchseLin.py),
- [**nemoAchseRot.py**](../vifcon/devices/nemoAchseRot.py) and,
- [**nemoGase.py**](../vifcon/devices/nemoGase.py).

All three objects communicate with the Nemo-1 and Nemo-2 systems of the IKZ model experiments group.

## Communication data

In addition to the IP address and the port, communication requires register numbers. Modbus works with registers that contain a word. Each word consists of 16 bits (2 bytes). In VIFCON, the following are used for implementation:

- **Coils**,
- **Holding registers** and,
- **Input registers** are used.

The *pyModbusTCP* library handles most of the communication, so the user only has to specify the start address and the number of registers to be read.

### Coils

Coils only contain Boolean values. In VIFCON, these are used as buttons. This is how the drive movement can be started, for example.

### Holding registers

The holding registers are registers that receive and implement values ​​from the master. For example, VIFCON sends the target speed for the drives to Modbus so that the PLC can then implement it.

### Input registers

The input registers are the opposite of the holding registers. The master sends a query to the slave and receives measurement data from the PLC. This is how the actual speed values ​​can be read out, for example.

## Specific registers

The systems differ in their registers. Because the drive status word of the drives is no longer just one word, some registers are shifted. The following tables show these values:

### Lift drive - spindle (top)

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

### Rotation drive - spindle (top)

Config name | Type | Nemo-1 start register | Nemo-2 start register
--- | --- | --- | ---
cw          | Coil    | 21 | 21
ccw         | Coil    | 20 | 20
stopp       | Coil    | 19 | 19
lese_st_Reg | Input   | 51 | 53
write_v_Reg | Holding |  6 |  6
statusReg   | Input   | 55 | 57

### Lift drive - crucible (bottom)

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

### Rotation drive - crucible (bottom)

Config name | Type | Nemo-1 start register | Nemo-2 start register
--- | --- | --- | ---
cw          | Coil    |  4 |  4
ccw         | Coil    |  5 |  5
stopp       | Coil    |  3 |  3
lese_st_Reg | Input   | 33 | 34 
write_v_Reg | Holding |  2 |  2
statusReg   | Input   | 37 | 38

### Monitoring

Config name | Type | Nemo-1 start register | Nemo-2 start register
--- | --- | --- | ---
lese_st_Reg_VGP_1   | Input | 2 |   2
lese_st_Reg_VGP_2   | Input | / |  58
lese_st_Reg_K       | Input | / | 161
lese_st_Reg_AS      | Input | / | 209

### Generators

The generators only exist in the Nemo-2 system!

Config name | Type | Generator interface 1 start register | Generator interface 2 start register | Generator interface 3 start register
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

## Last change

The last change to this description was: December 17, 2024