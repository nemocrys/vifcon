# Config file

The config file is one of the most important features of the VIFCON control system. This file is used to configure everything in the control system. This is how:

- the GUI,
- the recipes,
- the multilog link,
- the gamepad,

and much more are provided. The config file is a Yaml file and is integrated into VIFCON using the Python library pyYAML. 

## Function

Python sees the Yaml file as a dictionary or a nesting of several dictionaries. A dictionary is structured as follows:

```
    Key: Value
```

The value can actually be anything. For example, it can be an object, a dictionary, a list or even an integer.

The config file is read as follows:
```
with open(config, encoding="utf-8") as f:
    self.config = yaml.safe_load(f)
```

A value is called as follows:
```
self.config['language']
```

In the example, the value of the key "language" would be evaluated.

## Configuration templates

VIFCON was created on 4 systems. There is a template for each system in the [Template](../Template) folder. The template [config_temp.yml](../Template/config_temp.yml) can be seen as an example. The following [explanations](#explanation-of-the-individual-points) shows the individual configurations.

System | Template
-------|---------------
DemoFZ | [config_temp_DemoFZ.yml](../Template/config_temp_DemoFZ.yml)
Nemo-1 | [config_temp_Nemo-1.yml](../Template/config_temp_Nemo-1.yml)
Nemo-2 | [config_temp_Nemo-2.yml](../Template/config_temp_Nemo-2.yml)
DemoCZ | [config_temp_Educrys.yml](../Template/config_temp_Educrys.yml)

There's also a template called [config_temp_Empty.yml](../Template/config_temp_Empty.yml) where all devices (`skip`) are set to True. Thus, when this template is launched, nothing is displayed in VIFCON except for two empty plots! With this template, the user can start the configuration from scratch.

## Starting the configuration

The image [Guide_Config_En.png](../Bilder/Guide_Config_En.png) shows a schematic process for configuring an experiment. The left side represents the setup from scratch, and the right side represents an existing system template. The following steps can be found in the flowchart:

1. Selecting the template
2. Initial changes and adding devices (GUI, legend, logging, etc.)
3. Initial settings for the individual devices (start and end)
4. Should Multilog be used?
5. Should the PID controller be used, and should Multilog provide one or both input values?
6. Should the gamepad be used?
7. Setting the parameters, limits, and recipes
8. Starting the program

Steps 4, 5, 6, and 7 are optional. Step 7 can be adjusted during operation via the GUI. To understand all the individual configurations, you should look at this readme or at least the comments in the templates for the individual configurations!

## Explanation of the individual points

Descriptions can also be found in the [templates](#Configuration-templates).  

The following are the points:
1. [Times](#times)
2. [Feature-Skip](#feature-skip)
3. [Multilog-Extra](#Multilog-extra)
4. [Save Files and Images](#save-files-and-images)
5. [GUI](#gui)
6. [Logging File](#logging-file)
7. [Console Logging](#console-logging)
8. [GUI Legend](#legend)
9. ​​[Scaling Factors](#scaling-factors)
10. [Devices](#devices)

### Times:

```
time:
  dt-main: 150
  timeout_exit: 10
```
After this time (`dt-main`), the threads of the devices or the sample function of the sampler object in the thread are called. The time is specified in ms and is required for the reaction timer.

The time `timeout_exit` is a time specified in seconds. In the exit function of the program, there is a while loop that should trigger when the threads are finished. If there are problems there, a break is executed after the specified time and the loop is exited. When triggered, a warning is also output in the console and the log file.

### Feature Skip

```
Function_Skip:                                                
  Multilog_Link: 0        
  Generell_GamePad: 0
  writereadTime: 0
```
If the value is set to True (1), the functions for the multilog link and the gamepad are enabled. If False, this is skipped in the code and has no effect on VIFCON.

With `writereadTime` a time period is logged as a debug. For this function to work, the `level` must be set to 10 for `logging`! The time period measured here is for the `write` and `read` functions of the individual devices. This determines how long these functions take. Both functions are important for device communication!

### Multilog-Extra

```
Multilog_extra:
  timeout: 10             
  connection_error_case: 1
```

The function for the Multilog link can be activated under [Feature Skip](#Feature-Skip). Using the function and the various settings under the [Devices](#Devices) ([similarities](#Similarities) - `Multilog` and `PID`), communication can be established with the Multilog program. The extra configurations are for crash handling. With the link, it is important that VIFCON is started first and then Multilog. Despite this, it can happen that the ports are not activated in the correct order (Multilog side), which causes VIFCON to hang. This is why there is the `timeout`. The timeout must be set somewhat higher because Multilog must be started. The `connection_error_case` setting regulates how the crash is handled, i.e. when the timeout is triggered. In case **1** the program is terminated and in case **2** it is started. If a read port (receiving multilog data) is not created in case 2, the PID function is blocked. With multilog, Nan values ​​would arrive in the event of a write port error.

### Save files and images

```
save:
  config_save: True                                
  log_save: True   
  plot_save: True
  GUI_save: True
```

At the end of the application, the config file and the log file are copied from the main folder to the measurement folder. The legend and the plots are also saved. This happens when True.

It is important to note that the plots and the legend are saved as they appear in the GUI.

To have a complete picture of the GUI, the currently visible GUI can also be saved.

### GUI

```
GUI:
  language: de
  GUI_Frame: 0
  GUI_color_Widget: 1
```

The settings change the GUI in terms of language and appearance.

`language` specifies the language. Only German (DE) and English (EN) can be selected. The GUI changes accordingly.

If the value for `GUI_Frame` is set to True (1), the widget frames are switched on. This means that the placement of the individual widgets can be viewed.

<img src="../Bilder/Rahmen_EN.png" alt="GUI frame display" title='Display of widget frames' width=500/>

With `GUI_color_Widget` you can turn off the colors on the widget. Instead of the colorful GUI everything will be shown in black. The colors in question can be seen in the picture.

### Logging file

```
logging:
  level: 20
  filename: vifcon.log
  format: '%(asctime)s %(levelname)s %(name)s - %(message)s'
  filemode: w         
  encoding: 'utf-8' 
```
This config part is used to create the logging file and determine the logging level. There are:

- 10 - Debug
- 20 - Info
- 30 - Warning
- 40 - Error

On some systems the `encoding` must be commented out, as this will cause Linux, for example, to issue an error.

### Console logging
```
consol_Logging:
  level: 30
  print: 1 
  format: '%(asctime)s %(levelname)s %(name)s - %(message)s'
```
If the key *filename* is left empty in [Logging](#logging-file), all log messages are written to the console.

Console logging filters out certain messages. With the key *print* you can:

- 1 - Only the specified level,
- 2 - Also all smaller levels and,
- 3 - Also all larger levels

must be specified. It must be noted that the main logging level has a higher priority than the new console logging. For example:

- logging level = 40
- Console logging level = 30 and print = 1
- Nothing is output in the console because the messages for level 30 are not called by the main logger!

### Legend

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

This creates the legend for the two device types of the control system (drives, generator). The following are possible with the key *legend_pos*:

- SIDE
- IN
- OUT

If IN the legend will be in the plot. If OUT it will be below the plot and if SIDE the legend will be next to the plot in a separate widget. If SIDE the position can be:

- rl
- l
- r

With rl, two widgets are created to the right and left of the plot. These widgets then contain the curves intended for the axis. With l and r, a widget is created only on the right or only on the left.

For OUT and IN, the number of labels in a row can also be changed. This is done using *legend_anz*.

### Scaling factors

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

The GUI plot can be changed using the scaling factors. The different sizes are not always in the same value range. As soon as the value is not equal to one, the curve is scaled by this value. This scaling is shown in the y-axis label. Furthermore, certain numbers also cause a change in this sense. The number 1 as a scaling factor is not shown in the y-axis label. If it is zero, the size is removed from the y-axis label. If the label no longer contains any size, *No entries!* is displayed.

PIDA and PIDG refer to specific values. PIDA is used for the PI axis and the two Nemo drives, while PIDG is only used for TruHeat. This can be used to scale the PID controller input value. At Eurotherm, this value is the temperature, which is why it is not scaled with PIDG.

### Devices

```
devices:
  Eurotherm 3504:
    skip: 1                         # Level 1
    typ: Generator                  # Level 1
    ende: 1                         # Level 1
    start:                          # Level 1
      sicherheit: 1  PI-Achse_h:    # Level 2
    ...
  PI-Achse_h:
    ...

```

All existing devices can now be found under the key ***devices***. Each device must have a specific part of its name:

Device                                                      | String part
------------------------------------------------------------|----------------------
[Eurotherm](#Eurotherm)                                     | Eurotherm
[TruHeat](#TruHeat)                                         | TruHeat
[PI axis](#PI-Achse)                                        | PI-Achse
[Nemo facility 1 & 2 lifting drive](#nemo-achse-linear)     | Nemo-Achse-Linear
[Nemo facility 1 & 2 rotation drive](#nemo-achse-rotation)  | Nemo-Achse-Rotation
[Nemo facility 1 & 2 sensors](#nemo-gase)                   | Nemo-Gase
[Nemo facility 2 generator](#nemo-generator)                | Nemo-Generator
[Educrys facility sensors](#educrys-monitoring)             | Educrys-Monitoring
[Educrys facility drives](#educrys-antrieb)                 | Educrys-Antrieb
[Educrys facility heater](#educrys-heizer)                  | Educrys-Heizer

An example can be found at the beginning of the PI axis and the Eurotherm controller. The individual devices have some differences and some similarities. The different configurations are shown in tables below. In the example you can see the levels that are shown in the tables. Level refers to the indentation in the Yaml file. The higher-level indentations of `devices` and the device name are not taken into account.

#### Similarities

The first table shows the basic similarities such as PID controller and Multilog.

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
skip || In order not to transfer a device to the GUI, the value **True (1)** must be selected for this key. In this case, the definition of the device in the program is skipped.
typ || *Options*: **Generator**, **Antrieb**, **Monitoring**<br><br>Generator: Eurotherm, TruHeat, Nemo generator, Educrys heater<br>Drive: PI axis, Nemo axis linear, Nemo axis rotation, Educrys drive<br>Monitoring: Nemo gases, Educrys monitoring<br><br>This key determines the page and tab (control, monitoring) of the widget.
ende || If **True** is selected, a safe end state is set when the program ends!
multilog |write_trigger| Communication string for Multilog
multilog |write_port| Communication port for sending to Multilog
multilog |read_trigger_ist| Communication string for VIFCON – reception of actual values ​​by Multilog
multilog |read_port_ist| Communication port for receiving the Multilog actual values
multilog |read_trigger_soll| Communication string for VIFCON – reception of setpoint values ​​by Multilog
multilog |read_port_soll| multilog read_port_soll Communication port for receiving the Multilog setpoint values
PID |PID_Aktiv | If **True**, the PID mode is enabled and usable.
PID |Value_Origin| Origin of the target and actual values: **VV**, **VM**, **MM**, **MV**<br>First letter = actual value<br>Second letter = target value<br>V – VIFCON, M – Multilog
PID |kp |VIFCON-PID P-element parameter
PID |ki |VIFCON-PID I-element parameter
PID |kd |VIFCON-PID D-element parameter
PID |sample |Time in seconds with which the PID controller is called (sample rate)
PID |sample_tolleranz |Time in seconds (deviation from sample rate without error message)
PID |start_ist |Start actual value (used for initialization) (PID input)
PID |start_soll |Start target value (PID input)
PID |umstell_wert|Value that is written into the input field when the PID mode is ended and which is Change in the write_value dictionary for the output size is saved in normal mode!
PID |Multilog_Sensor_Ist |Sensor name for the multilog communication (actual value)|
PID |Multilog_Sensor_Soll |Sensor name for the multilog communication (setpoint)
PID |Input_Limit_max |Limit for PID input
PID |Input_Limit_min |Limit for PID input
PID |Input_Error_option |If the value is incorrect, something is done depending on the configuration:<br>**error** – last value is retained<br>**max** – maximum value is used (limit)<br>**min** – minimum value is used (limit)
PID |debug_log_time| Logging in debug<br>Time in seconds that writes a log message that shows the inputs and outputs of the PID controller
rezepte || See explanations in [Rezepte_En.md](Rezepte_En.md)

**Examples:**

Here are the configurations for Multilog and PID. If the `read` configurations are used, certain `PID` configurations must also be set. For example, `Value_Origin` must contain an `M` and `Multilog_Sensor_Ist` must contain something specific in `read_trigger_ist` depending on the sensor!

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

The individual GUI legend curves are shown in the tables under [Differences](#Differences). Below is an example of the definition of the configuration in question. The configuration consists of a string. When read, this is separated using the character `;`.

```
 GUI:
    legend: RezOp ; RezT ; IWT ; IWOp ; SWT ; uGT ; oGT ; oGOp ; uGOp
```

---

The second table shows the similarities in the **RS232 interface**:

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
serial-interface |port |RS232 interface
serial-interface |baudrate| transfer rate
serial-interface |bytesize| size of the byte
serial-interface |stopbits| number of stop bits
serial-interface |parity |check bit
serial-interface |timeout |abort of the interface read and write commands

**Devices:** Eurotherm, TruHeat, PI axis, Educrys facility

---

The second table shows the similarities in **Modbus communication**:

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
serial-interface |host |IP address server
serial-interface |port |Port for communication
serial-interface |default|Output of communication in the console<br>**ATTENTION**: Only works with pyModbusTCP < 0.3.0, works with 0.2.1<br>Comment out in case of error!! (see [Python_RPI_En.py](Python_RPI_En.md))
serial-interface| timeout| Abort of interface read and write commands

**Devices:** Nemo facility

---

#### Differences

The configurations of the individual devices are shown below. Points such as multilog, PID and interface can be found above in the [similarities](#similarities).

##### **Eurotherm:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
start | sicherheit | Specifies how the maximum power output (HO) is set.<br>**True** – maximum power (HO) can only be changed on the device <br>**False** – VIFCON sends the max. power (HO) to Eurotherm (transmitted value OP max)
start | PID_Write |If **True**, the PID parameters from `PID-Device` are sent to the Eurotherm device!
start | start_modus |**Manuel** for manual mode (user determines power output)<br>**Auto** for automatic mode (temperature control active, PID controller ensures power output)
start | readTime |Time in seconds at which the device is read
start | init |If **True** the device is initialized!<br>If **False** the sending of commands is blocked so that VIFCON starts and the initialization can take place later. **ATTENTION**: The interface that was configured must exist!!
start | ramp_start_value |Start value of a ramp if this is selected as segment 1 in the recipe!!<br>**IST** – actual value<br>**SOLL** – setpoint
start | ramp_m_unit |Unit of the recipe segment (Eurotherm ramp)<br>*Possible*: **K/s**, **K/h**, **K/min**<br>**ATTENTION**: Must also be set on the device!!
PID device | PB |Eurotherm size: proportional band
PID device | TI |Eurotherm size: integral time
PID device | TD |Eurotherm size: differential time
limits | maxTemp |Limit temperature maximum
limits | minTemp |Limit temperature minimum
limits | oPMax |Limit operating point (output power) maximum
limits | oPMin |Limit operating point (output power) minimum
GUI | legend |String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: RezOP = recipe (Rez) for the output power (OP)<br><br>*Built-in*:<br> RezT, RezOp, IWT, IWOp, IWTPID, SWT, SWTPID, uGT, oGT, uGOp, oGOp, oGPID, uGPID
defaults | startTemp |Value that is written into the temperature input field for initialization
defaults | startPow |Value that is written into the power input field for initialization

---

##### **TruHeat:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
start |start_modus | Start mode for the generator (radio button GUI)<br>The generator can start with power (**P**), current (**I**) or voltage (**U**).
start |readTime | Time in seconds at which the device is read
start |init | If **True**, the device is initialized!<br>If **False**, the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
start |ad | Address of the generator
start |watchdog_Time | The TruHeat has a watchdog timer as a safety function. The time value in milliseconds is set at the start of the program.
start |send_Delay | Here you can specify a time in milliseconds that causes a delay between sending commands.<br>Should not be greater than the watchdog time!
serial-loop-read | | Number of repetitions if the device responds incorrectly (while loop)
limits |maxI | Limit current maximum
limits |minI | Limit current minimum
limits |maxP | Limit power maximum
limits |minP | Limit power minimum
limits |maxU | Limit voltage maximum
limits |minU | Limit voltage minimum
GUI |legend | String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: RezP = recipe (Rez) for the power (P)<br><br>*Built-in*:<br> RezI, RezU, RezP, Rezx, IWI, IWU, IWP, IWf, SWI, SWU, SWP, uGI, oGI, uGU, oGU, uGP, oGP, IWxPID, SWxPID, oGPID, uGPID
defaults |startCurrent | Value that is written into the current input field for initialization
defaults |startPow | Value that is written into the power input field for initialization
defaults |startVoltage | Value that is written into the voltage input field for initialization

---

##### **PI-Achse:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
mercury_model | | Selected controller<br>**C862** or **C863**
read_TT_log | | Display of the target value (TT) as info in the log file
gamepad_Button | | String for the button assignment:<br>**PIh** - ← & → (Axis)<br>**PIz** - ↑ & ↓ (Axis)<br>**PIx** - X & B (Button)<br>**PIy** - Y & A (Button)<br><br>*Buttons:*<br>X - Out <br>B - In<br>Y - Left<br>A - Right<br>← & ↑ - Up<br>→ & ↓ - Down<br>Select - Stop drives
start |readTime | Time in seconds for the device to be read out
start |init | If **True**, the device is initialized!<br>If **False**, the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
start |mode | Mode for unlocking the movement buttons:<br>**0** - No locking<br>**1** - Unlocking by timer<br>**2** - Unlocking when 0 mm/s is reached
serial-loop-read | | Number of repetitions if the device gives an incorrect response (while loop)
parameter |adv | Address selection code
parameter |cpm | Counts per mm (conversion factor)
parameter |mvtime | Read delay for determining the axis speed [ms]<br>Required for the MV command on C862!
parameter |nKS_Aus | Read decimal places
limits |maxPos | Limit position maximum
limits |minPos | Limit position minimum
limits |maxSpeed ​​| Limit speed maximum, minimum speed = maxSpeed ​​* -1 -> maxSpeed ​​> 0
GUI |bewegung | Direction of movement (display of arrows in GUI)<br>**y** – right and left<br>**x** – in and out<br>**z** – up and down
GUI |piSymbol | Alignment of the axis (there is a PI symbol on the device)<br>y (**Left** - left, **Right** - right)<br>x (**Front** - front, **Hi** - back)<br>z (**Up** - top, **Down** - bottom)<br>Minus values ​​to the PI symbol, other direction plus
GUI |knopf_anzeige | Buttons change color when the movement is selected. If you move upwards, the arrow pointing upwards is displayed in color (green or gray).
GUI |legend | String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: Rezv = recipe (Rez) for the speed (v)<br><br>*Built-in*:<br> Rezv, IWs, IWv, SWv, uGv, oGv, uGs, oGs, IWxPID , SWxPID, oGPID, uGPID, Rezx
defaults |startSpeed ​​| Value that is written into the speed input field for initialization
defaults |startPos | Value that is written into the position input field for initialization

---

##### **Nemo-Achse-Linear:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
nemo-version | | Version of the system used: **1** or **2**
gamepad_Button | | String for the button assignment:<br>*Possible*: HubS, HubT<br>**HubS** - X & B (spindle) (button)<br>**HubT** - ↑ & ↓ (crucible) (axes)<br><br>*Buttons:* <br>X & ↑ - Up<br>B & ↓ - Down<br>Select - Stop drives
start |readTime | Time in seconds at which the device is read
start |init | If **True** the device is initialized!<br>If **False** the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
start |invert | If **True** was selected, the speed is inverted. <br>*Used*: Nemo-1 system spindle
start |invert_Pos | If **True** was selected, the position value is inverted. <br>*Used*: Nemo-2 system spindle (real path)
start |start_weg | Start path for the simulated path
start |pos_control | **REAL** – Use of the path read from the device<br>**SIM** – Use of the simulated path <br> Path for limit control!
start |sicherheit | Safety mode when using the real position value:<br>**0** - Ignore errors and faults<br>**1** - Error and stop
register | | See [Modbus_Nemo_En.md](Modbus_Nemo_En.md) <br>Coils, input and holding registers for communication with the PLC
parameter |nKS_Aus | Read decimal places
parameter |Vorfaktor_Ist | Prefactor for the actual speed
parameter |Vorfaktor_Soll| Prefactor for the target speed
limits |maxPos | Limit position maximum
limits |minPos | Limit position minimum
limits |maxSpeed ​​| Limit speed maximum, minimum speed = maxSpeed ​​* -1 -> maxSpeed ​​> 0
GUI |knopf_anzeige | Buttons change color when the movement is selected. Button operation becomes visible!
GUI |legend | String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: RezOP = recipe (Rez) for the output power (OP)<br><br>*Built-in*:<br> Rezv, Rezx, IWs, IWsd, IWv, SWv, SWs, uGv, oGv, uGs, oGs, IWxPID, SWxPID, oGPID, uGPID
defaults |startSpeed ​​| Value that is written into the speed input field for initialization

---

##### **Nemo-Achse-Rotation:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
nemo-version | | Version of the system used: **1** or **2**
gamepad_Button | | String for the button assignment:<br>*Possible*: RotS, RotT<br>**RotS** - Y & A (spindle) (button)<br>**RotT** - ← & → (crucible) (axes)<br><br>*Buttons:*<br>Y & ← - ↻ (CW)<br>A & → - ↺ (CCW)<br>Select - Stop drives
start |readTime | Time in seconds at which the device is read
start |init | If **True** the device is initialized!<br>If **False** the sending of commands is blocked so that VIFCON starts and initialization can take place later.<br>**ATTENTION**: The interface that was configured must exist!!
start |invert | If **True** was selected, the speed is inverted. <br>Used: Nemo-1 system spindle
start |invert_winkel | If set to **True**, the read angle is inverted. This is required for limit control with read angle values ​​on the Nemo 2 spindle!
start |start_winkel | Start angle for the simulated angle
start |winkel_control | **REAL** – Use of the angle read from the device<br>**SIM** – Use of the simulated angle <br> Angle for limit control!
start |kont_rot | If **True** the checkbox for continuous rotation is set directly!
start         |sicherheit   | Safety mode when using the real angle value:<br>**0** - Ignore errors and faults<br>**1** - Error and stop
register | | See [Modbus_Nemo_En.md](Modbus_Nemo_En.md) <br>Coils, input and holding registers for communication with the PLC
parameter |nKS_Aus | Reading of decimal places
parameter |Vorfaktor_Ist | Prefactor for the actual speed
parameter |Vorfaktor_Soll | Pre-factor for the target speed
limits |maxWinkel | Limit angle maximum
limits |minWinkel | Limit angle minimum
limits |maxSpeed ​​| Limit speed maximum, minimum speed = maxSpeed ​​* -1 -> maxSpeed ​​> 0
GUI |knopf_anzeige | Buttons change color when the movement is selected. Button activation becomes visible!
GUI |legend | String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: RezOP = Recipe (Rez) for the output power (OP)<br><br>*Built-in*:<br> Rezv, Rezx , IWw, IWv, IWwd, SWv, uGv, oGv, uGw, oGw, IWxPID, SWxPID, oGPID, uGPID<br>IWwd only at Nemo-2
defaults |startSpeed ​​| Value that is written into the speed input field for initialization
rezept_Loop | | Number of recipe repetitions

---

##### **Nemo-Gase:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
nemo-version| | Version of the system used: **1** or **2**
start |readTime | Time in seconds at which the device is read
start |init | If **True**, the device is initialized!<br>If **False**, the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
register | | See [Modbus_Nemo_En.md](Modbus_Nemo_En.md)<br>Coils, input and holding registers for communication with the PLC
parameter |nKS_Aus | Reading decimal places

Since *Nemo-Gase* is a **monitoring module**, all write functions are not available, as only reading is possible! Therefore, not all similarities apply to Nemo-Gase, such as `read_trigger`.

---

##### **Nemo-Generator:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
nemo-version | | Version of the system used: **2**
start |start_modus | Start mode for the generator (radio button GUI and Nemo system GUI - Coil)<br>The generator can start with power (**P**), current (**I**) or voltage (**U**).
start |Auswahl | **I** – Only current is available for selection<br>**PUI** – Switching between current, voltage and power is possible
start |readTime | Time in seconds for which the device is read out
start |init | If **True**, the device is initialized!<br>If **False**, the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
register | | See [Modbus_Nemo_En.md](Modbus_Nemo_En.md) <br>Coils, input and holding registers for communication with the PLC
limits |maxI | Limit current maximum
limits |minI | Limit current minimum
limits |maxP | Limit power maximum
limits |minP | Limit power minimum
limits |maxU | Limit voltage maximum
limits |minU | Limit voltage minimum
GUI |legend | String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: RezOP = recipe (Rez) for the output power (OP)<br><br>*Built-in*:<br> RezI, RezU, RezP, Rezx, IWI, IWU, IWP, IWf, SWI, SWU, SWP, uGI, oGI, uGU, oGU, uGP, oGP, IWxPID, SWxPID, oGPID, uGPID
parameter |nKS_Aus | Read decimal places
defaults |startCurrent | Value that is written to the current input field for initialization
defaults |startPow | Value that is written to the power input field for initialization
defaults |startVoltage | Value that is written to the voltage input field for initialization

---

##### **Educrys-Monitoring:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
start |readTime | Time in seconds at which the device is read
start |init | If **True**, the device is initialized!<br>If **False**, the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
serial-loop-read | | Number of repetitions if the device responds incorrectly
parameter |nKS_Aus | Reading decimal places

---

##### **Educrys-Antrieb:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
Antriebs_Art | | Educrys has three drives<br>**L** – Hub<br>**R** – Rotation<br>**F** – Fan
gamepad_Button | | String for the button assignment:<br>*Possible*: EduL, EduR, EduF<br>**EduL** - X, B, ↑ & ↓<br>**EduR** - A, Y, ← & →<br>**EduF** - Start<br><br>*Buttons:*<br>X & ↑ - Up<br>B & ↓ - Down<br>A & → - CCW<br>Y & ← - CW<br>Start - Fan On<br>Select - Stop drives
start |readTime | Time in seconds for the device to be read
start |init | If **True**, the device is initialized!<br>If **False**, the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
start |start_weg | Start position (*relevant for* linear motor)
start |write_SW | If **True**, the start path is sent to the system and the position is set (*Define Position*). (*relevant for* linear motor)
start |write_SLP | If **True**, the position limits are sent to the system. (*relevant for* linear motor)
start |sicherheit | Safety mode when using the real position value:<br>**0** - Ignore errors and faults<br>**1** - Error and stop
serial-extra |serial-loop-read | Number of repetitions if the device responds incorrectly
serial-extra |rel_tol_write_ans| The relative tolerance for comparing the device's response with the command sent!
parameter |nKS_Aus | Read decimal places
limits |maxPos | Limit position maximum
limits |minPos | Limit position minimum
limits |maxSpeed ​​| Limit speed maximum, minimum speed = maxSpeed ​​* -1 -> maxSpeed ​​> 0<br>For the fan (F) the minimum is set to zero!
GUI |knopf_anzeige | Buttons change color when the movement is selected. Button operation becomes visible!
GUI |legend | String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: RezOP = Recipe (Rez) for the output power (OP)<br><br>*Built-in*:<br> Rezv, Rezx, IWs, IWsd, IWv, uGv, oGv, uGs, oGs, IWxPID, SWxPID, oGPID, uGPID
defaults |startSpeed ​​| Value that is written into the speed input field for initialization
defaults |startPos | Value that is written into the position input field for initialization
rezept_Loop | | Number of recipe repetitions

---

##### **Educrys-Heizer:**

**Level 1** | **Level 2** | **Explanation**
--- | --- | ---
start |PID_Write | If **True**, the Eurotherm PID parameters are written for initialization.
start |start_modus | **Manual** for manual mode<br>**Auto** for automatic mode
start |readTime | Time in seconds at which the device is read
start |init | If **True**, the device is initialized!<br>If **False**, the sending of commands is blocked so that VIFCON starts and initialization can take place later. <br>**ATTENTION**: The interface that was configured must exist!!
start |ramp_start_value | Start value of a ramp if this is selected as segment 1 in the recipe!!<br>**IST** – actual value<br>**SOLL** – setpoint
serial-extra |serial-loop-read | Number of repetitions if the device responds incorrectly
serial-extra |rel_tol_write_ans| The relative tolerance for comparing the device's response with the command sent!
PID-Device |PB | Educrys-PID-Size - P-component
PID-Device |TI | Educrys-PID-Size - I-component
PID-Device |TD | Educrys-PID-Size - D-component
parameter |nKS_Aus | Read decimal places
limits |maxTemp | Limit temperature maximum
limits |minTemp | Limit temperature minimum
limits |oPMax | Limit power at the output maximum
limits |oPMin | Limit power at the output minimum
GUI |legend | String with curve names for the legend<br>*Structure*: Value type + size<br>*Example*: RezOP = recipe (Rez) for the output power (OP)<br><br>*Built-in*:<br> RezT, RezOp, IWT, IWOp, IWTPID, SWT, SWTPID, uGT, oGT, uGOp, oGOp, oGPID, uGPID
defaults |startTemp | Value that is written into the temperature input field for initialization
defaults |startPow | Value that is written into the power input field for initialization

## Reading secure:

All configurations were checked in the modules (widget, device). This was also built into the controller (main init). The key and the associated value are always checked. The value is checked to see whether it is of the correct type or whether the value can be used at all.

**Example:**

Key test:
```
try: self.init = self.config['start']['init']
except Exception as e: 
  logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_4[self.sprache]} start|init {self.Log_Pfad_conf_5[self.sprache]} False')
  logger.exception(f'{self.device_name} - {self.Log_Pfad_conf_6[self.sprache]}')
  self.init = False
```

*Notifications:*
```
2024-09-26 16:49:57,877 WARNING vifcon.view.truHeat - TruHeat - Error reading config during configuration: start|init ; Set to default: False
2024-09-26 16:49:57,883 ERROR vifcon.view.truHeat - TruHeat - Reason for error:
Traceback (most recent call last):
  File "z:\Gruppen\modexp-all\Private\work\Vincent\vifcon\vifcon\view\truHeat.py", line 130, in __init__
    try: self.init = self.config['start']['init']
                     ~~~~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 'init'
```

---

Value test:
```
if not type(self.init) == bool and not self.init in [0,1]: 
  logger.warning(f'{self.device_name} - {self.Log_Pfad_conf_1[self.sprache]} init - {self.Log_Pfad_conf_2[self.sprache]} [True, False] - {self.Log_Pfad_conf_3[self.sprache]} False - {self.Log_Pfad_conf_8[self.sprache]} {self.init}')
  self.init = 0
```

*Notifications:*
```
2024-09-26 16:50:34,004 WARNING vifcon.view.truHeat - TruHeat - Configuration error in element: init - Possible values: [True, False] - Default is used: False - Incorrect input: Truea
```

## Last change

The last change to the [templates](#Configuration-templates) and this description was: March 26, 2025