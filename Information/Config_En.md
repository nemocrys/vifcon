# Config file

The config file is one of the most important features of the VIFCON control system. This file is used to configure everything in the control system. This is how:

- the GUI,
- the recipes,
- the multilog link,
- the gamepad,

and much more are provided. The config file is a Yaml file and is integrated into VIFCON using the Python library pyYAML. 

## Last change

The last change to the [template](#explanation-of-the-individual-points) and this description was: September 26, 2024

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

## Explanation of the individual points

Descriptions can also be found in the template of the file ([config_temp.yml](../Template/config_temp.yml)). 

The following are the points:
1. [Times](#times)
2. [Feature-Skip](#feature-skip)
3. [Save Files and Images](#save-files-and-images)
4. [GUI](#gui)
5. [Logging File](#logging-file)
6. [Console Logging](#console-logging)
7. [GUI Legend](#legend)
8. ​​[Scaling Factors](#scaling-factors)
9. [Devices](#devices)

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
```
If the value is set to True (1), the functions for the multilog link and the gamepad are enabled. If False, this is skipped in the code and has no effect on VIFCON.

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

On some systems the encoding must be commented out, as this will cause Linux, for example, to issue an error.

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
  PIDA:     0
  PIDG:     0
```

The GUI plot can be changed using the scaling factors. The different sizes are not always in the same value range. As soon as the value is not equal to one, the curve is scaled by this value. This scaling is shown in the y-axis label. Furthermore, certain numbers also cause a change in this sense. The number 1 as a scaling factor is not shown in the y-axis label. If it is zero, the size is removed from the y-axis label. If the label no longer contains any size, *No entries!* is displayed.

PIDA and PIDG refer to specific values. PIDA is used for the PI axis and the two Nemo drives, while PIDG is only used for TruHeat. This can be used to scale the PID controller input value. At Eurotherm, this value is the temperature, which is why it is not scaled with PIDG.

### Devices

```
devices:
  Eurotherm 3504:
    ...
  PI-Achse_h:
    ...
```

All existing devices can now be found under the key ***devices***. Each device must have a specific part of its name:

Device                         | String part
-------------------------------|----------------------
Eurotherm                      | Eurotherm
TruHeat                        | TruHeat
PI axis                        | PI-Achse
Nemo-1 facility lifting drive  | Nemo-Achse-Linear
Nemo-1 facility rotation drive | Nemo-Achse-Rotation
Nemo-1 facility sensors        | Nemo-Gase

An example of the PI axis and the Eurotherm controller can be found at the beginning. The individual devices have some differences and some similarities.

#### Similarities

1. ```skip: 1```
    - In order not to transfer a device to the GUI, the value True (1) must be selected for this key. In this case, the definition of the device in the program is skipped.
2. ```typ:  Generator```
    - Options: Generator, Antrieb, Monitoring
    - Generator: Eurotherm, TruHeat
    - Drive: PI-Achse, Nemo-Achse-Linear, Nemo-Achse-Rotation
    - Monitoring: Nemo-Gase
    - This key determines the page and tab of the widget. 
3. ```ende: 0```
    - This key is used to activate the safe end state. If the value is set to True (1), the stop function of the respective device is activated and executed when the exit (end of the application) is executed. 
4.  ```serial-interface```
    - Interface properties for communication
    - RS233
      - port, baudrate, bytesize, stopbits, parity, timeout
      - Eurotherm, TruHeat, PI-Achse
    - Modbus
      - host (Server IP address), port, debug
      - Nemo-1 facility
5. Multilog-Link 
    ```
      multilog:
        write_trigger: Eurotherm1
        write_port: 50000
        read_trigger: DAQ-6510
        read_port: 56000
    ```
    - Trigger word depends on Multilog configuration
    - Port depends on Multilog configuration
    - Using this key, VIFCON sends its data to Multilog.
    - Write: VIFCON sends values ​​to Multilog
    - Read: VIFCON gets values ​​from Multilog for the PID mode
      - read_trigger and read_Port are not available in Nemo-Gase!
6. Limits
    - Every device has certain limits.
    - These limits are software limits, which means that sending values ​​only works up to these values.
    - Example Eurotherm:
      ```
        limits:
        maxTemp: 1000
        minTemp: 0
        opMax: 35 
        opMin: 0
      ```
7. GUI curves
    ```
      GUI:
        legend: RezOp ; RezT ; IWT ; IWOp ; SWT ; uGT ; oGT ; oGOp ; uGOp
    ```
    - This configuration tells the program which curves should be displayed in the plot.
    - Depending on the device, there are different names.
    - Basic: recipes, actual values, target values, upper limit, lower limit + size name
    - e.g. RezOP means recipe curve for operating point (power)
8. Input field display
    ```
      defaults:
        startTemp: 20  
        startPow: 25 
    ```
    - These values ​​are displayed in the GUI at the beginning of the program. 
9. Recipes:
    - For this item please see [Rezepte_En.md](Rezepte_En.md).
10. PID-Mode:
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
        Input_Limit_max: 1000
        Input_Limit_min: 0
        Input_Error_option: error
        debug_log_time: 5
    ```
    - There are only minimal differences between the devices!
    - `PID_Active` - If True, the PID mode can be activated!
    - `Value_Origin` - Shows the origin of the input values
      - First position: actual value
      - Second position: setpoint
      - V - VIFCON, M - Multilog
    - PID parameters: kp, ki, kd
    - `sample` - PID timer time, sample rate
      - `sample_tolleranz` - Deviation from sample rate without error message
    - `start_ist` and `start_soll` show the first value for the input
    - `umstell_wert` - Value that is saved in the write_value dictionary for the output size in normal mode when changing!
      - TruHeat has three of these variables
    - `Multilog_Sensor_Ist` - Multilog sensor from which the actual value input comes
    - Limits input: `Input_Limit_max` and `Input_Limit_min`
    - `Input_Error_option` - If a reading error occurs, one of three options is set
      - max - Upper limit is set as input
      - min - Lower limit is set as input
      - error - Use error message and last input
    - `debug_log_time` - Debug log time in s

#### Differences

**Eurotherm:**

```
    start:
      sicherheit: 0
      PID_Write: 0
      start_modus: Auto
      readTime: 2 
      init: 1
      ramp_start_value: ist 
```

*sicherheit*:
  - Determines how the maximum power output (HO) is set.
    - True: HO can only be changed on the device
    - False: HO can only be read by VIFCON, which adjusts OPmax (1. Menu button, 2. Switch to manual mode)

*PID_Write:*
  - If True, the PID parameters from `PID-Device` are sent to the Eurotherm device!

*start_modus*:
  - Options: Auto, Manual
    - Eurotherm has two modes
        - Automatic mode:
            - Temperature control active
            - PID controller provides power output
        - Manual mode:
            - User sets power output

*readtime*:
    - Time interval when the device should be read
    - a zero switches off the reading of values

*init*:
    - Initialization of the device should or should not occur
    - True:
        - Device is connected to the interface and is addressed directly by the program
    - False:
        - Interface exists, but the device is not necessarily connected to it yet
        - Program ensures that no commands are sent

*ramp_start_value*:
  - Possible: IST, SOLL
  - Depending on the selection, the first ramp starts at the target value or the actual value

```
  PID-Device:
    PB: 11.8
    TI: 114
    TD: 0 
```

The three Eurotherm PID parameters are defined here. These can be written at start-up or via a menu function.

**TruHeat:**

```
    start:
      start_modus: P
      readTime: 0
      init: True 
      ad: '00001'
      watchdog_Time: 5000
      send_Delay: 20 
```

*init* and *readTime* are identical on all devices, see Eurotherm for explanation!

*start_modus*:
  - Possible: P, I, U
  - This will set the radio button in the GUI to the size.

*ad*:
  - TruHeat Generator Address

*watchdog_Time*:
  - The TruHeat has a watchdog timer as a safety function. The time value in milliseconds is set at the beginning of the program.

*send_Delay*:
  - Here you can specify a time in milliseconds that causes a delay between sending commands.
  - Should not be greater than the watchdog time!

```
    serial-loop-read: 3
```

The configuration controls a while loop. With TruHeat and the PI axis there is a while loop that repeats a reading attempt. The value indicates the frequency of these repetitions.

**PI-Achse:**

1. ```mercury_model: C862```
    - Two different models of the Mercury model were used for the PI axis. These were C862 and C863.
    - Both models have small differences. Especially when measuring or reading the speed.

2. ```gamepad_Button: PIh```
    - Possible for PI axis: PIh, PIz, PIx, PIy
    - This key unlocks certain buttons for certain axis movement directions.

3. Start:
    - For the PI axis there are only *init*, *readTime* and *mode*.
    - The first two are the same as for the others (see Eurotherm).
    - *mode*
        - Locking mode of the movement buttons
        - 0 - No locking
        - 1 - Unlocking by timer
        - 2 - Unlocking by reaching 0 mm/s

4. Parameter:
    ```
      parameter:
        adv: '0133' 
        cpm: 29752 
        mvtime: 25  
        nKS_Aus: 3  
    ```
    - *adv* = Address selection code
    - *cpm* = Counts per mm
      - Conversion factor
    - *mvtime*
      - Read delay for the axis speed (ms)
      - Required for the MV command at C862
    - *nKS_Aus*
      - displayed decimal places

5. Logging target values:
      ```
          read_TT_log: True
      ```
    - If True, the TT command is executed, which logs the position target values.

6. While loop:
      ```
        serial-loop-read: 3
      ```

    - The configuration controls a while loop. For TruHeat and the PI axis, there is a while loop that repeats a read attempt. The value indicates the frequency of these repetitions.

7. Display of the button status:
    - Under GUI: `button_display: 1`
    - If True, the direction is displayed by a green button!
      - Movement button e.g. ↑ then turns green (background)
      - When stopped, the color returns to normal!

**Nemo-Achse-Linear and Nemo-Achse-Rotation:**

1. ```gamepad_Button: HubS```
    - Possible for Linear: HubS, HubT
    - Possible for Rotation: RotS, RotT
    - This key unlocks certain buttons for certain axis movement directions.

2. Start:
    - For the PI axis there are only *init*, *readTime*, *invert* and *start_weg* or *start_winkel*.
    - The first two are the same as for the others (see Eurotherm).
    - *invert*
        - True: Inversion of the speed value
        - For the spindle, the recipe and the real speed would be different!
    - *start_weg* or *start_winkel*
        - For the Nemo-1 system, the path and the speed are calculated automatically.
        - For this reason, you can specify a start value here.
  
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
      - Certain registers are set in the Nemo system.
      - This addresses coils, input registers and holding registers.
  
  4. Parameter:
      - These have *nKS_Aus*, *Vorfaktor_Ist* and *Vorfaktor_Soll*.
      - The former are the decimal places that are displayed.
      - The prefactor was used to correct the incorrect driving. The set speed was not the correct one that was received by the drives.

  5. System version:
    - `nemo version: 2`
    - The configuration can be used to switch between Nemo-1 and Nemo-2!

  6. Display of the button status:
    - Under GUI: `button_display: 1`
    - If True, the direction is displayed by a green button!
      - Movement button e.g. ↑ then turns green (background)
      - When stopped, the color returns to normal!

**Nemo-Gase:**

- Has fewer parts because only reading is done.
- Values ​​are only displayed in GUI and can be passed to Multilog.
- Similar to the rest of Nemo-1.

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