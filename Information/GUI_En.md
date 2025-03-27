# GUI of VIFCON

The individual widgets of the VIFCON GUI are shown below. Special features are shown or mentioned. The complete GUI can be seen in the [Readme](../README.md). The GUI contains a menu and a plot.

## Plot

<img src="../Bilder/GUI_Plot_En.png" alt="Drive plot widget" title='Plot widget of the drive side' width=700/>

The plot widget of the drive side can be seen in the picture. The generator side is identical, except for the one button for the **synchronous movement** of the drives/axes. Both sides have a button for **stopping all devices**, for **auto scaling**, for **setting all curves** and for **removing all curves**. The buttons in the lower area contain the coordinates of the mouse cursor when it is in the plot. All other points are changed by the configuration. These points are:

- the position of the legend,
- the curves to be seen (legend and plot) and,
- the scaling of the two y-axes.

The two buttons for setting and removing all legends can only be used with the **Side** variant of the legend configuration and are therefore only displayed then! This variant is shown in the example. If, for example, the Remove all curves button is pressed, all checkboxes in the legend are set to False (Unchecked). Furthermore, no curves are then displayed in the plot. The other button does the opposite.

## Menu

<img src="../Bilder/GUI_Menu_En.png" alt="Menu widget" title='Menu example for VIFCON' width=700/>

The image shows an example of the menu. The menu consists of **Plot**, **Devices** and **Recipes** settings. Some settings only appear for certain devices. In the example, three Eurotherm-specific points can be seen. Plot and recipes are always the same.

## Device widget

The individual device widgets are shown below. Parts of the GUI can be activated through configuration. On the other hand, certain parts can also be deactivated during certain processes. For example, the PID mode cannot be switched off while a recipe is running. This can be seen by a grayed out PID checkbox. Not all possible GUI versions are shown here. The PID mode, for example, changes the labels on the input fields and the actual values ​​so that the user can see the PID input and output values. The colors change to match the curves.

### Eurotherm

<img src="../Bilder/WidgetEn_Eurotherm.png" alt="Eurotherm-Widget" title='Example of Eurotherm widget' width=700/>

Image status: December 3, 2024

The image shows the widget for the Eurotherm controller. With this widget you can switch between temperature (automatic) and power (manual). The widget contains the following points:

1. Recipe functions (start, stop, selection)
2. Activate syncro recipe function (checkbox)
3. Activate PID mode (checkbox)
4. Send value from input field (send)
5. The *o.K.* shows the error messages -> If there is a red and bold *Error!* there, you can see what the problem is via the tooltip.

In PID mode, the names and colors of the target and actual values ​​then change.

### TruHeat

<img src="../Bilder/WidgetEn_TruHeat.png" alt="TruHeat-Widget" title='Example for TruHeat-Widget' width=700/>

Image status: December 3, 2024

The image shows the widget of the TruHeat generator. With this widget you can choose between power, voltage and current. The widget contains the following points:

1. Recipe functions (start, stop, selection)
2. Activate syncro recipe function (checkbox)
3. Activate PID mode (checkbox)
4. Send value from input field (send)
5. Switch generator on and off
6. The *o.K.* shows the error messages -> If there is a red and bold *Error!* there, you can see what the problem is via the tooltip.

In PID mode, the selected size is swapped with the PID values. If, for example, *Target-I* is selected, this is exchanged with *Target-PID*. The values ​​will then be displayed as *PID-Out. (I)*.

### PI axis

<img src="../Bilder/WidgetEn_PIAchse_R.png" alt="PI-Achse-Widget-Relativ" title='Example 1 for Pi axis widget' width=700/>
<img src="../Bilder/WidgetEn_PIAchse_A.png" alt="PI-Achse-Widget-Absolut" title='Example 2 for Pi axis widget' width=700/>

Images as of: December 3, 2024

The two widgets belong to the PI axis. The axis can travel relative distances or move to absolute positions using VIFCON. Speed ​​and distance or position are therefore sent. The widget contains the following points:

1. Recipe functions (start, end, selection)
2. Activate synchro recipe and synchro drive function (checkbox)
3. Activate PID mode (checkbox)
4. Send value from input field (start, arrows)
5. Stop drive
6. Set position to zero
7. Activate gamepad use (checkbox)
8. The *o.K.* shows the error messages -> If there is a red and bold *Error!* there, you can see what the problem is via the tooltip. There are two of these here, for both sizes.

Here, too, the PID mode changes the setpoints. Depending on the direction of movement (z, y, x), the arrows change during relative movement.

### Nemo system: Drive stroke

<img src="../Bilder/WidgetEn_NemoLin.png" alt="NemoHub-Widget" title='Example of Nemo system hub widget' width=700/>

Image status: December 3, 2024

The widget belongs to the stroke movement of the Nemo system drives. The example shows the widget of Nemo system 2. The rapid traverse status does not exist for Nemo system 1. The speed is sent here. The widget contains the following points:

1. Recipe functions (start, stop, selection)
2. Activate synchro recipe and synchro drive function (checkbox)
3. Activate PID mode (checkbox)
4. Send value from input field (arrows)
5. Stop drive
6. Set position to zero
7. Activate gamepad use (checkbox)
8. The *o.K.* shows the error messages -> If there is a red and bold *Error!* there, you can see what the problem is via the tooltip.
9. Status messages

As with the PI axis and TruHeat, the PID mode changes the setpoint to be entered and replaces it.

### Nemo system: Drive rotation

<img src="../Bilder/WidgetEn_NemoRot.png" alt="NemoRot-Widget-Nemo-1" title='Example of Nemo 1 system rotation widget' width=700/>
<img src="../Bilder/WidgetEn_NemoRot_N2.png" alt="NemoRot-Widget-Nemo-2" title='Example of Nemo 2 system rotation widget' width=700/>

Image status: March 27, 2025

The widget belongs to the rotational movement of the Nemo system drives. Both widgets are shown in the example. The two GUIs differ only minimally from each other. The Nemo 2 system has additional values. The angular velocity is sent here. The widget contains the following items:

1. Recipe functions (start, stop, selection)
2. Activate syncro recipe function (checkbox)
3. Activate PID mode (checkbox)
4. Send value from input field (arrows)
5. Stop drive
6. Set angle to zero
7. Activate gamepad use (checkbox)
8. Activate continuous rotation (checkbox)
9. The *o.K.* shows the error messages -> If there is a red and bold *Error!* there, you can see what the problem is via the tooltip.
10. Status messages
11. Recipe Repetition (checkbox)

As with the PI axis and TruHeat, the PID mode changes the setpoint to be entered and replaces it.

### Nemo system: Monitoring

<img src="../Bilder/WidgetEn_NemoGas.png" alt="Nemo1-Monitoring-Widget" title='Example of Nemo system 1 monitoring widget' width=700/>
<img src="../Bilder/WidgetEn_NemoGas2.png" alt="Nemo2-Monitoring-Widget" title='Example of Nemo system 2 monitoring widget' width=700/>

Status of images: March 19, 2025

Monitoring varies depending on the system. The images show the monitoring values ​​of the Nemo-1 and Nemo-2 systems of the IKZ.

### Nemo system: generator
<img src="../Bilder/WidgetDe_NemoGen.png" alt="Nemo2-Generator-Widget" title='Example of Nemo-Anlage-2-Generator-Widget' width=700/>

Status of images: February 11, 2025

The widget shows the Nemo generator module. The structure is the same as [TruHeat](#TruHeat).

### Educrys system: drives
<img src="../Bilder/WidgetEn_EducrysAntrieb.png" alt="Educrys system drive widget" title='Example of Educrys system drive widget' width=700/>

Status of the images: February 11, 2025

The widget shows the Educrys drive module. Educrys has three addressable drive types: **R**otation, **L**inear and **F**an. The last two can be seen in the image. Depending on which of the three drives is selected, only small details change. With Linear, everything is available and with Rotation and Fan, the position is set and the target position is locked, as well as the buttons changed. With the Fan (ventilator), only a start button is needed. With Rotation, the arrows from the [Nemo rotation widget](#Nemo-system:-Drive-rotation) would be visible.

The widget contains the following points:
1. Start movement (arrow or start)
2. End movement (stop)
3. Synchro mode (checkbox)
4. GamePad mode (checkbox)
5. PID mode (checkbox)
6. Recipe repeat mode (checkbox)
7. Recipe functions (start, end, selection)
8. Set a position (linear only)
9. Enter speed and target position

### Educrys system: heater
<img src="../Bilder/WidgetEn_EducrysHeizer.png" alt="Educrys system heater widget" title='Example of Educrys system heater widget' width=700/>

Status of the images: February 11, 2025

The widget shows the Educrys heater module. The structure is the same as [Eurotherm](#Eurotherm).

### Educrys system: monitoring
<img src="../Bilder/WidgetEn_EducrysMon.png" alt="Educrys system monitoring widget" title='Example of Educrys system monitoring widget' width=200/>

Status of the images: February 11, 2025

The widget shows the monitoring data of the Educrys system.

## More

<img src="../Bilder/Rahmen_EN.png" alt="Widget frame" title='Widget frame visible' width=700/>

The configurations can be used to make the widget frames visible so that placement can be improved. The colors of the labels can also be turned off. The colors of the labels reflect the corresponding curves in the plot.

<img src="../Bilder/Widget_ToolTip_En.png" alt="Limit-Tool-Tip" title='Widget Limit-Tool-Tip' width=700/>

All input fields and the PID checkbox show the corresponding limits as a tool tip. The Nemo generator provides another tool tip, which contains the interface combination and the read name of the generator. This data can then be found in the displayed config name (in the example this would be TruHeat or PI-Achse_h).

## Pop-up window

In VIFCON there are various pop-up windows. These windows can be called up under various circumstances. At the end of the application, when it is to be closed using Windows-X, the following window is displayed. *Yes* confirms the closing and triggers the VIFCON exit function.

<img src="../Bilder/PU_Ende_En.png" alt="Application_End" title='Pop-up window, end application' width=300/>

In addition to this pop-up window, there are six more:

Device | Trigger | Text
--- | --- | ---
Eurotherm           | security = 1 & update limit triggered | The maximum output power (HO) is not adjusted to the limit! The Security setting has been set to True. This means that the value can only be changed directly on the Eurotherm!kann!      
Eurotherm           | security = 1 & program start or init to True | Please note that with the config setting "security" True, the OPmax valuedoes not have to match that in the device. To adjust, please press "Read Eurotherm HO" in the menu or switch to manual mode so that the OPmax value is updated in VIFCON!
Eurotherm           | selecting a recipe | Note the configuration on the device:<br>1. Check whether the correct setting for the ramp gradient has been entered (On Eurotherm: Press 2xSheet, 3xArrow CCW -> Ramp Units -> arrow keys to select)(Attention: Select the correct program after one sheet)!<br>2. Note configuration setting (Eurotherm) "Servo" (Eurotherm ramp: start setpoint or actual value)!!
Nemo-Achse-Rotation | Uncheck continuous rotation | Continuous rotation has ended. Please note that a limit may already have been exceeded at this point. If this limit is exceeded, set the angle to zero, switch continuous rotation back on or move in the other direction. If, for example, the CCW limit has been reached, the drive can still move up to the CW limit.
Nemo-Generator      | launch of VIFCON | Note the settings of the selected generator! These are displayed as a tooltip next to the name and can be set in the system GUI!<br><br>If changes are made, a restart is recommended!
TruHeat             | Set measurement time to zero seconds! Also at Init! | The watchdog should be set to zero (disabled) since the read commands have been issued.

## Last change

The last change to this description was: March 26, 2025