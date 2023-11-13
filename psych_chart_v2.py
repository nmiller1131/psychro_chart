# plot a simple psychrometric chart
import psychrolib as psy
import numpy as np
import PySimpleGUI as sg
from matplotlib import pyplot as plt
from IPython.display import clear_output

plotted_points = []
x_coord = []
y_coord = []
input_array = []
chart = False

def psych_calcs(array):
    while True:
        psy.SetUnitSystem(psy.IP)

        variables = {'tdb': False, 'twb': False, 'rh': False, 'tdp': False}

        # declarations
        userInp = {}
        pressure = psy.GetStandardAtmPressure(0)
        Cp_ip = 0.2402  # Specific heat of dry air in Btu/lb·°F
        L_ip = 970.3   # Latent heat of vaporization in Btu/lb
        air_enthalpy_ratio = 0.62198 # from ideal gas law
        process_description = 'This will be changed once a second point is plotted'

        # intakes user inputs and changes flags
        if array.get('input_Dry Bulb Temp (°F)'):
            userInp['tdb'] = float(array['input_Dry Bulb Temp (°F)'])
            variables['tdb'] = True
        if array.get('input_Wet Bulb Temp (°F)'):
            userInp['twb'] = float(array['input_Wet Bulb Temp (°F)'])
            variables['twb'] = True
        if array.get('input_Relative Humidity (%)'):
            userInp['rh'] = float(array['input_Relative Humidity (%)'])
            variables['rh'] = True
        if array.get('input_Dew Point (°F)'):
            userInp['tdp'] = float(array['input_Dew Point (°F)'])
            variables['tdp'] = True

        #Handle user inputs and calculate psychrometrics accordingly
        try:
            if (variables['tdb'] and variables['twb']):
                t = int(userInp['tdb'])
                wb = int(userInp['twb'])
                psych = psy.CalcPsychrometricsFromTWetBulb(t, wb, pressure)
                hri = psych[0]
                plotted_points.append((t, hri))
                x_coord.append(t)
                y_coord.append(hri)
            elif(variables['tdb'] and variables['rh']):
                t = int(userInp['tdb'])
                rh = int(userInp['rh'])
                if (rh > 1):
                    rh = rh / 100
                psych = psy.CalcPsychrometricsFromRelHum(t, rh, pressure)
                hri = psych[0]
                plotted_points.append((t, hri))
                x_coord.append(t)
                y_coord.append(hri)
            elif(variables['tdb'] and variables['tdp']):
                t = int(userInp['tdb'])
                dp = int(userInp['tdp'])
                psych = psy.CalcPsychrometricsFromTDewPoint(t, dp, pressure)
                hri = psych[0]
                plotted_points.append((t, hri))
                x_coord.append(t)
                y_coord.append(hri)
        except ValueError as ve:
            print(f'ValueError: {ve}')
            raise ve
        except Exception as e:
            print(e)
            raise e
        if (len(x_coord) >= 2) and (len(y_coord) >= 2):
            delta_x = x_coord[-1] - x_coord[-2]
            delta_y = y_coord[-1] - y_coord[-2]
            try:
                slope = (delta_y / delta_x)
                if (slope == 0):
                    if (delta_x > 0):
                        process_description = 'Sensible Cooling'
                    else:
                        process_description = 'Sensible Heating'
                elif (slope > 0):
                    if (delta_x > 0):
                        process_description = 'Heating and Humidification'
                    else:
                        process_description = 'Evaporative Cooling'
                elif (slope < 0):
                    if (delta_x > 0):
                        process_description = 'Chemical Dehumidifying'
                    else:
                        process_description = 'Cooling and Dehumidification'
                print(f'This is {process_description}')
            except ZeroDivisionError as e:
                if (delta_y > 0) and (delta_y != 0):
                    process_description = 'Dehumidification'
                    slope = 0
                else:
                    process_description = 'Humidification'
                    slope = 0
        return (psych, process_description, x_coord, y_coord)


def show_chart(x_coord, y_coord):
    global plotted_points, chart

    psy.SetUnitSystem(psy.IP)
    plt.ion()
    if chart == False:
        chart = True
    else:
        plt.close(chart)

    # declarations
    pressure = psy.GetStandardAtmPressure(0)

    # define subplots
    f, ax = plt.subplots()

    # set up graph ranges
    t_array = np.arange(0, 140, 1)
    rh_array = np.arange(0, 1, 0.1)
    enthalpy_array = np.arange(10, 65, 1)
    hr_hor_lines = np.arange(0, 0.035, 0.01)
    twb_array = np.arange(0, 100, 5)
    v_array = np.arange(11, 16, 0.5)

    # plot constant relative humidity lines
    for rh in rh_array:
        hr_array = []
        for t in t_array:
            hr = psy.GetHumRatioFromRelHum(t, rh, pressure)
            hr_array.append(hr)
        ax.plot(t_array, hr_array, color = 'black')

    # plot constant wet bulb lines
    for twb in twb_array:
        hr_array = []
        t_plot_array = []
        for t in t_array:
            if twb <= t:
                hr = psy.GetHumRatioFromTWetBulb(t, twb, pressure)
                hr_array.append(hr)
                t_plot_array.append(t)
        ax.plot(t_plot_array, hr_array, ':', color = 'black')

    enthalpy_plot_array = []

    # plot constant specific volume
    for enthalpy in enthalpy_array:
        hr_array = []
        enthalpy_plot_array = []
        for t in t_array:
            hr = psy.GetHumRatioFromEnthalpyAndTDryBulb(enthalpy, t)    
            if psy.GetRelHumFromHumRatio(t, hr, pressure) <= 1.0:
                hr_array.append(hr)
                enthalpy_plot_array.append(t)
        ax.plot(enthalpy_plot_array, hr_array, '-', color = 'black')

    # formatting right axis
    ax.set(ylim=(0, 0.03), xlim=(20, 120), ylabel=r"Humidity Ratio [$lb_{water}/lb_{dry air}$]", xlabel="Dry-bulb Temperature [°F]")
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    plt.tight_layout()

    for point in plotted_points:
        ax.plot(point[0], point[1], 'o')
    ax.plot(x_coord, y_coord, 'bo', linestyle="solid")
    ax.plot(x_coord[-1], y_coord[-1], 'ro')

    plt.subplots_adjust(top=0.95)
    plt.title('Psychrometric Chart')

    plt.draw()
    plt.pause(0.1)
    plt.show(block=True)

def gui():
    sg.theme('LightGreen1')

    # dictionary of decimal places
    decimal_places = {
        'output_Humidity ratio (lb_H₂O/lb_Air)': 3,
        'output_Dew-Point (°F)': 1, 
        'output_Relative Humidity (%)': 2,
        'output_Partial pressure of water vapor in moist air (Psi)': 3,
        'output_Moist air enthalpy in Btu/lb': 1, 
        'output_Specific volume of moist air (ft³/lb)': 1, 
        'output_Degree of saturation (unitless)': 2
    }

    # captures user inputs
    layout = [
        [sg.Frame('Instructions', description_cells(), expand_x=True)],
        [sg.Frame('Input', input_cells(), expand_x=True)],
        [sg.Frame('Output', output_cells(), expand_y=True, expand_x=True)],
        [sg.Frame('Process', process_cells('This will be changed once a second point is plotted'), expand_x=True)],
        [sg.Button('Calculate'), sg.Button('Close')],
    ]

    # creates window
    window = sg.Window('Psychrometric Data Compiler', layout, size=(450, 550))

    # Event Loop to process events and get the "value of the inputs
    while True:
        event, values = window.read()
        if (len(x_coord) >= 2):
            window['Process'].Update(f'{description}')
        # stops code if window is closed
        if event == sg.WIN_CLOSED or event == 'Close':
            window.close()
            break
        elif event == 'Calculate':
            try:
                dry = int(values.get('input_Dry Bulb Temp (°F)'))
                # handles if dry bulb temp is negative
                if dry <= 0:
                    sg.popup_error('Dry Bulb Temperature must be a positive number')
                    continue
            # handles if dry bulb temp was not entered
            except ValueError as ve:
                    sg.popup_error('Dry Bulb Temperature is a required input')
                    continue
            # creates object to pass to psych calc function
            input_values = {key: values[key] for key in values if key.startswith("input_")}
            used_inputs = {key: value for key, value in input_values.items() if value != '0.0'}
            # handles if not enough inputs were used
            if len(used_inputs) < 2:
                sg.popup_error('Please submit at least two varibales')
                continue
            psychr = psych_calcs(used_inputs)
            psychro = psychr[0]
            process = psychr[1]
            x = psychr[2]
            y = psychr[3]
            # shows output of psych calc function in the window
            for i, output_key in enumerate(output_items):
                decimal_place = decimal_places.get(f'output_{output_key}', 2)
                window[f'output_{output_key}'].update(f'{psychro[i]:.{decimal_place}f}')
            # resets input values to default
            for key in input_values:
                window[key].update(default)
            window['Process'].update(process)
            show_chart(x, y)
            continue

# gui variables
size1, size2 = 40, 10
default  = '0.0'
input_items  = ('Dry Bulb Temp (°F)', 'Wet Bulb Temp (°F)', 'Relative Humidity (%)', 'Dew Point (°F)')
output_items = ('Humidity ratio (lb_H₂O/lb_Air)', 'Dew-Point (°F)', 'Relative Humidity (%)', 'Partial pressure of water vapor in moist air (Psi)', 'Moist air enthalpy (Btu/lb)', 'Specific volume of moist air (ft³/lb)', 'Degree of saturation (unitless)')
instructions = 'Input values for dry bulb temp and at least one other variable below'
labels = ('Dry Bulb Temp (°F)', 'Wet Bulb Temp (°F)', 'Relative Humidity (%)', 'Dew Point (°F)')
description = ''

def input_cells():
    return [
        [sg.Text(item, size=size1, pad=(5, 5)),
         sg.Input(default, size=size2, enable_events=True, key=f'input_{item}', expand_x=True)]
            for item in input_items]

def output_cells():
    return [
        [sg.Text(item, size=size1, pad=(5, 5)),
         sg.Input(default, size=size2, disabled=True, background_color='CadetBlue1', key=f'output_{item}', expand_x=True)]
            for item in output_items]

def description_cells():
        return [
            [sg.Text(instructions, size=size1, pad=(5, 5), expand_x=True)]
        ]

def process_cells(string):
        return [
            [sg.Text(string, size=size1, pad=(5, 5), expand_x=True, key='Process')]
        ]

if __name__ == "__main__":
    gui()