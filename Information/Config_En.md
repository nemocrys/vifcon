# Config file

The config file is one of the most important features of the VIFCON control system. This file is used to configure everything in the control system. This is how:

- the GUI,
- the recipes,
- the multilog link,
- the gamepad,

and much more are provided. The config file is a Yaml file and is integrated into VIFCON using the Python library pyYAML. 

## Last change

The last change to the [template](#explanation-of-the-individual-points) and this description was: June 25, 2024

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
1. [Reaction timer](#reaction-timer)
2. [Feature-Skip](#feature-skip)
3. [Save Files and Images](#save-files-and-images)
4. [Language](#language)
5. [GUI Widget Frame](#gui-widget-frame)
6. [Logging File](#logging-file)
7. [Console Logging](#console-logging)
8. [GUI Legend](#legend)
9. ​​[Scaling Factors](#scaling-factors)
10. [Devices](#devices)


### Reaction timer:

```
time:
  dt-main: 150
```
After this time (in ms), the threads of the devices are called or the sample function of the sampler object in the thread.

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
```

At the end of the application, the config file and the log file are copied from the main folder to the measurement folder. The legend and the plots are also saved. This happens when True.

It is important to note that the plots and the legend are saved as they appear in the GUI.

### Language

```
language: de
```

The language is specified in the value here. Only German (DE) and English (EN) can be selected. The GUI changes accordingly.

### GUI widget frame

```
GUI_Frame: 0
```

If the value is set to True (1), the widget borders are turned on. This allows you to view the placement of individual widgets.

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
```

The GUI plot can be changed using the scaling factors. The different sizes are not always in the same value range. As soon as the value is not equal to one, the curve is scaled by this value. This scaling is shown in the y-axis label. Furthermore, certain numbers also cause a change in this sense. The number 1 as a scaling factor is not shown in the y-axis label. If it is zero, the size is removed from the y-axis label. If the label no longer contains any size, *No entries!* is displayed.

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
        trigger: pi1                                 
        port: 54629
    ```
    - Trigger word depends on Multilog configuration
    - Port depends on Multilog configuration
    - Using this key, VIFCON sends its data to Multilog.
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

#### Differences

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
  - Determines how the maximum power output (HO) is set.
    - True: HO can only be changed on the device
    - False: HO can only be read by VIFCON, which adjusts OPmax (1. Menu button, 2. Switch to manual mode)

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
      - These have *nKS_Aus* and *Vorfaktor*.
      - The former are the decimal places that are displayed.
      - The prefactor was used to correct the incorrect driving. The set speed was not the correct one that was received by the drives.

**Nemo-Gase:**

- Has fewer parts because only reading is done.
- Values ​​are only displayed in GUI and can be passed to Multilog.
- Similar to the rest of Nemo-1.