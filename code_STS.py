SOFTWARE_VERSION_NUMBER = "2.4.0"
DEVICE_TYPE = "STELLA-Q2"
# STELLA-Q2 spectrometer instrument
# NASA open source software license
# Paul Mirel 2023
import time
start_time = time.monotonic()

# startup in continuous recording. 
# click the button to pause recording (response is a bit slow ~1s)
# click again to take a data point, as many as you want, 
# press-and-hold (2sec) to turn on the lamps, 
# press-and-hold again to turn off the lamps. 

import gc
gc.collect()
start_mem_free_kB = gc.mem_free()/1000
print("start memory free {0:.2f} kB".format( start_mem_free_kB ))

import os
import microcontroller
import board
import digitalio
import rtc
import neopixel
import storage
import busio
import adafruit_max1704x
import adafruit_pcf8523
import AS7265X_sparkfun
from AS7265X_sparkfun import AS7265X
import displayio
import terminalio
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import vectorio # for shapes
from i2c_button import I2C_Button

def main():
    DAYS = { 0:"Sunday", 1:"Monday", 2:"Tuesday", 3:"Wednesday", 4:"Thursday", 5:"Friday", 6:"Saturday" }
    DATA_FILE = "/sd/data.csv"
    LOW_BATTERY_VOLTAGE = 3.4
    RED =   ( 0, 255, 0 )
    ORANGE =( 28, 64, 0 )
    YELLOW =( 64, 64, 0 )
    GREEN = ( 255, 0, 0 )
    BLUE =  ( 0, 0, 255 )
    OFF =   ( 0, 0, 0 )
    band_center_error_plus_minus = 10
    bandwidth_FWHM_nm = 20
    FOV_FWHM_DEG = 20
    spectral_units = "uW/cm^2"
    spectral_error_plus_minus_percent = 12

    memory_check( "begin main()", start_mem_free_kB )
    displayio.release_displays()
    UID = int.from_bytes(microcontroller.cpu.uid, "big") % 10000
    print("unique identifier (UID) : {0}".format( UID ))
    number_of_onboard_neopixels = 1
    onboard_neopixel = initialize_neopixel( board.NEOPIXEL, number_of_onboard_neopixels )
    vfs, sdcard = initialize_sd_card_storage( onboard_neopixel, RED )
    band_designations = 610, 680, 730, 760, 810, 860, 560, 585, 645, 705, 900, 940, 410, 435, 460, 485, 510, 535
    bands_sorted = sorted( band_designations )
    gc.collect()
    header = ( "device_type, software_version, UID, batch, weekday, "
        "timestamp_iso8601, decimal_hour, "
        "bandwidth_FWHM_nm, field_of_view_FWHM_DEG, "
        "irradiance_410nm_purple_wavelength_nm, irradiance_410nm_purple_wavelength_uncertainty_nm, "
        "irradiance_410nm_purple_irradiance_uW_per_cm_squared, irradiance_410nm_purple_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_435nm_blue_wavelength_nm, irradiance_435nm_blue_wavelength_uncertainty_nm, "
        "irradiance_435nm_blue_irradiance_uW_per_cm_squared, irradiance_435nm_blue_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_460nm_dodgerblue_wavelength_nm, irradiance_460nm_dodgerblue_wavelength_uncertainty_nm, "
        "irradiance_460nm_dodgerblue_irradiance_uW_per_cm_squared, irradiance_460nm_dodgerblue_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_485nm_cyan_wavelength_nm, irradiance_485nm_cyan_wavelength_uncertainty_nm, "
        "irradiance_485nm_cyan_irradiance_uW_per_cm_squared, irradiance_485nm_cyan_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_510nm_green_wavelength_nm, irradiance_510nm_green_wavelength_uncertainty_nm, "
        "irradiance_510nm_green_irradiance_uW_per_cm_squared, irradiance_510nm_green_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_535nm_aquamarine_wavelength_nm, irradiance_535nm_aquamarine_wavelength_uncertainty_nm, "
        "irradiance_535nm_aquamarine_irradiance_uW_per_cm_squared, irradiance_535nm_aquamarine_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_560nm_limegreen_wavelength_nm, irradiance_560nm_limegreen_wavelength_uncertainty_nm, "
        "irradiance_560nm_limegreen_irradiance_uW_per_cm_squared, irradiance_560nm_limegreen_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_585nm_yellow_wavelength_nm, irradiance_585nm_yellow_wavelength_uncertainty_nm, "
        "irradiance_585nm_yellow_irradiance_uW_per_cm_squared, irradiance_585nm_yellow_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_610nm_orange_wavelength_nm, irradiance_610nm_orange_wavelength_uncertainty_nm, "
        "irradiance_610nm_orange_irradiance_uW_per_cm_squared, irradiance_610nm_orange_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_645nm_red_wavelength_nm, irradiance_645nm_red_wavelength_uncertainty_nm, "
        "irradiance_645nm_red_irradiance_uW_per_cm_squared, irradiance_645nm_red_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_680nm_black_wavelength_nm, irradiance_680nm_black_wavelength_uncertainty_nm, "
        "irradiance_680nm_black_irradiance_uW_per_cm_squared, irradiance_680nm_black_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_705nm_brown_wavelength_nm, irradiance_705nm_brown_wavelength_uncertainty_nm, "
        "irradiance_705nm_brown_irradiance_uW_per_cm_squared, irradiance_705nm_brown_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_730nm_gray_wavelength_nm, irradiance_730nm_gray_wavelength_uncertainty_nm, "
        "irradiance_730nm_gray_irradiance_uW_per_cm_squared, irradiance_730nm_gray_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_760nm_silver_wavelength_nm, irradiance_760nm_silver_wavelength_uncertainty_nm, "
        "irradiance_760nm_silver_irradiance_uW_per_cm_squared, irradiance_760nm_silver_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_810nm_lightgray_wavelength_nm, irradiance_810nm_lightgray_wavelength_uncertainty_nm, "
        "irradiance_810nm_lightgray_irradiance_uW_per_cm_squared, irradiance_810nm_lightgray_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_860nm_linen_wavelength_nm, irradiance_860nm_linen_wavelength_uncertainty_nm, "
        "irradiance_860nm_linen_irradiance_uW_per_cm_squared, irradiance_860nm_linen_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_900nm_wheat_wavelength_nm, irradiance_900nm_wheat_wavelength_uncertainty_nm, "
        "irradiance_900nm_wheat_irradiance_uW_per_cm_squared, irradiance_900nm_wheat_irradiance_uncertainty_uW_per_cm_squared, "
        "irradiance_940nm_gold_wavelength_nm, irradiance_940nm_gold_wavelength_uncertainty_nm, "
        "irradiance_940nm_gold_irradiance_uW_per_cm_squared, irradiance_940nm_gold_irradiance_uncertainty_uW_per_cm_squared, "
        "battery_voltage, battery_percent\n" )
    print( header )
    gc.collect()
    data_file_exists = False
    if vfs:
        storage.mount(vfs, "/sd")
        data_file_exists = initialize_data_file( header, DATA_FILE )
    del header
    gc.collect()
    i2c_bus = initialize_i2c_bus( board.SCL, board.SDA, onboard_neopixel, GREEN, YELLOW, OFF )
    hardware_clock, hardware_clock_battery_OK = initialize_real_time_clock( i2c_bus )
    batch_number = 0
    if hardware_clock:
        system_clock = rtc.RTC()
        system_clock.datetime = hardware_clock.datetime
        batch_number = update_batch( hardware_clock.datetime )
    print( "batch number == {}".format( batch_number ))
    spectral_sensor = initialize_spectral_sensor( i2c_bus )
    spectral_sensor.disable_indicator()
    spectral_sensor.disable_bulb(0)   # white
    spectral_sensor.disable_bulb(1)   # NIR
    spectral_sensor.disable_bulb(2)   # UV
    button = initialize_i2c_button( i2c_bus ) 
    blink( button, 4, 0.1, 1, 64 ) #object, count, interval, low_level, high_level
    battery_monitor = initialize_battery_monitor( i2c_bus )
    battery_voltage, battery_percent = check_battery( battery_monitor )
    button = initialize_button( i2c_bus )
    display, display_group = initialize_display( i2c_bus )

    if display: 
        display.show( display_group )
    

        text_group = displayio.Group(scale=2, x=0, y=20)
        text = "U:" + str(UID)
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
        text_group.append(text_area) # Subgroup for text scaling

        display_group.append(text_group)

        batch_number_group = displayio.Group(scale=2, x=80, y=20)
        if vfs:
            text = "B:"+str( batch_number )
        else:
            text = "NoSD"
        batch_number_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
        batch_number_group.append(batch_number_area) # Subgroup for text scaling
        display_group.append(batch_number_group)

        time.sleep(3)
        display_group.pop()
        display_group.pop()

        text_group = displayio.Group(scale=2, x=0, y=20)
        text = " {:.1f}V".format(battery_voltage)
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
        text_group.append(text_area) # Subgroup for text scaling
        display_group.append(text_group)

        battery_percent_group = displayio.Group(scale=2, x=80, y=20)
        text = "{}%".format( int( battery_percent ))
        battery_percent_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
        battery_percent_group.append(battery_percent_area) # Subgroup for text scaling
        display_group.append(battery_percent_group)

        time.sleep(2)
        display_group.pop()
        display_group.pop()

        graph_bar, graph_bar_x, batch_number_label_text_area, polygon = create_graph_screen( display_group, bands_sorted )

    end_time = time.monotonic()
    print("instrument startup time == {} s".format(int(end_time - start_time)))
    gc.collect()
    # possible excursion here to show welcome screens
    stale_data = [0]
    gc.collect()
    interval_start_time_s = time.monotonic()
    loop_count = 0
    operational = True
    recording = True
    one_shot = False
    lamps_on = False

    sample_interval_s = 1.5 # intervals shorter than 1.5 seconds lead to frequent write errors on the SD card.
    try:
        while operational:
            loop_begin_time_s = time.monotonic()
            loop_count += 1
            if loop_count > 1023:
                loop_count = 0
            gc.collect()
            if button: 
                button_values = button.status
                if button_values[ 1 ] or button_values[2]:
                    print( "button clicked" )
                    recording = False
                    one_shot = True
                    batch_number = update_batch( hardware_clock.datetime )
                    button.led_bright = 16 
                if button_values[ 2 ] and not button_values[1]: 
                    time.sleep(0.1)
                    hold_time = 0 
                    press_hold = True
                    start_hold_time = time.monotonic()
                    while button_values[ 2 ] and hold_time <= 2.2:
                        button_values = button.status
                        hold_time = time.monotonic() - start_hold_time
                        time.sleep(0.1)
                    if hold_time > 2: 
                        lamps_on = not lamps_on
                        if lamps_on: 
                            print( "turn on the lamps")
                            spectral_sensor.enable_bulb(0)   # white
                            spectral_sensor.enable_bulb(1)   # NIR
                            spectral_sensor.enable_bulb(2)   # UV
                        else:
                            print( "turn off the lamps")
                            spectral_sensor.disable_bulb(0)   # white
                            spectral_sensor.disable_bulb(1)   # NIR
                            spectral_sensor.disable_bulb(2)   # UV
                button.clear()
                

            # check if it is time to read a new datapoint. If not yet, then skip this section
            if time.monotonic() > interval_start_time_s + sample_interval_s:
                gc.collect()
                if display: 
                    if recording:
                        if vfs:
                            batch_number_label_text_area.text = "batch:" + str( batch_number )
                        else:
                            batch_number_label_text_area.text = "NoSDcard"
                    else:
                        if vfs:
                            batch_number_label_text_area.text = "lastB:" + str( batch_number )
                        else:
                            batch_number_label_text_area.text = "NoSDcard"

                if hardware_clock:
                    timenow = hardware_clock.datetime
                else:
                    timenow = time.struct_time(( 2020,  01,   01,   00,  00,  00,   0,   -1,    -1 ))
                interval_start_time_s = time.monotonic()
                mem_free_kB = gc.mem_free()/1000
                print( "\nmemory free == {} kB, {:.1f} %".format( mem_free_kB, 100 * mem_free_kB/start_mem_free_kB ))
                check_loop_count = loop_count
                spectral_data_sorted, spectral_data_dictionary = read_spectral_sensor( spectral_sensor, band_designations ) # 0.5 seconds
                if spectral_data_sorted:
                    stale_data = spectral_data_dictionary
                battery_voltage, battery_percent = check_battery( battery_monitor )
                gc.collect()
                #graph_data( spectral_data_sorted, graph_bar, graph_bar_x, polygon ) # 8 ms
                iso8601_utc = "{:04}{:02}{:02}T{:02}{:02}{:02}Z".format(
                    timenow.tm_year, timenow.tm_mon, timenow.tm_mday,
                    timenow.tm_hour, timenow.tm_min, timenow.tm_sec )
                decimal_hour = timestamp_to_decimal_hour( timenow )
                weekday = DAYS[ timenow.tm_wday ]
                datapoint_string = ""
                datapoint_string += "{}, {}, ".format( DEVICE_TYPE, SOFTWARE_VERSION_NUMBER)
                datapoint_string += ( "{}, {}, {}, {}, {}, ".format( UID, batch_number, weekday, iso8601_utc, decimal_hour ))
                datapoint_string += ( "{}, {}, ".format( bandwidth_FWHM_nm, FOV_FWHM_DEG))
                if spectral_data_dictionary:
                    for item in bands_sorted:
                        datapoint_string += str(item)
                        datapoint_string += ", "
                        datapoint_string += "{}, ".format(band_center_error_plus_minus)
                        datapoint_string += str( round( spectral_data_dictionary[item], 3))
                        datapoint_string += ", "
                        datapoint_string += str( round( spectral_error_plus_minus_percent * spectral_data_dictionary[item]/ 100, 3 ))
                        datapoint_string += ", "
                datapoint_string += ( "{:.2f}, {}".format( battery_voltage, int(battery_percent )))
                #mirror data to usb
                print ( datapoint_string )
                if display: 
                    graph_data( spectral_data_sorted, graph_bar, graph_bar_x, polygon )
                if recording or one_shot:
                    write_data_to_file( DATA_FILE, datapoint_string, button, onboard_neopixel, OFF, GREEN, ORANGE )
                    if one_shot == True:
                        button.led_bright = 0 
                    one_shot = False
            time.sleep(0.1)
            loop_time = (time.monotonic() - loop_begin_time_s)

    finally:  # clean up the busses when ctrl-c'ing out of the loop
        if sdcard:
            sdcard.deinit()
            print( "sd card deinitialized" )
        displayio.release_displays()
        print( "displayio displays released" )
        i2c_bus.deinit()
        print( "i2c_bus deinitialized" )

def graph_data( spectral_data_sorted, graph_bar, graph_bar_x, polygon ):
    if spectral_data_sorted:
        y_zero_pixels = 31
        y_upper_pixels = 17
        graph_points = [(2, 112), (2, 104)]
        y_span_pixels = y_zero_pixels - y_upper_pixels
        irradiances = spectral_data_sorted
        irrad_min = min( irradiances )
        irrad_max = max( irradiances )
        irrad_span = irrad_max - irrad_min
        if irrad_span < 1:
            irrad_span = 1
        for count in range (len( irradiances )):
            irrad_value = irradiances[ count ]
            irrad_height = irrad_value - irrad_min
            irrad_normalized_height = irrad_height/ irrad_span
            irrad_bar_height_pixels = int(y_span_pixels * irrad_normalized_height)
            irrad_drop_height_pixels = int(y_span_pixels - irrad_bar_height_pixels)
            irrad_y_top_pixel = int(y_upper_pixels + irrad_drop_height_pixels)
            graph_bar[count].y = irrad_y_top_pixel
            graph_bar[count].height = 1
            point = (graph_bar_x[count]+1, irrad_y_top_pixel)
            graph_points.append(point)
        graph_points.append((126, 104))
        graph_points.append((126, 112))
        polygon.points = graph_points
        #del y_zero_pixels, y_upper_pixels, graph_points, y_span_pixels, irradiances, spectral_data_sorted
        #del irrad_min, irrad_max, irrad_span, count, irrad_value, irrad_height
        #del irrad_normalized_height, irrad_bar_height_pixels, irrad_drop_height_pixels
        #del irrad_y_top_pixel, point

def create_graph_screen( display_group, bands_sorted ):
    if display_group is not False:
        palette = displayio.Palette(1)
        palette[0] = 0xFFFFFF
        points2 = [ (2, 32), (2, 30), (126, 30), (126, 32)]
        polygon = vectorio.Polygon(pixel_shader=palette, points=points2, x=0, y=0)
        display_group.append( polygon )
        bar_color = 0xFFFFFF
        bar = displayio.Palette(1)
        bar[0] = bar_color
        bar_width = 1
        bar_default_height = 1
        graph_bar_x = (0, 6, 12, 18, 24, 29, 35, 41, 47, 55, 63, 69, 75, 82, 93, 105, 114, 124)
        graph_bar=[]
        for count in range( len( bands_sorted)):
            graph_bar.append( vectorio.Rectangle(pixel_shader=bar, width=bar_width, height=bar_default_height, x=graph_bar_x[count], y=106))
            display_group.append( graph_bar[count] )

        wavelength_label_group = displayio.Group( scale=1, x=4, y=9)
        wavelength_label_text = "410nm          940nm"
        wavelength_label_text_area = label.Label( terminalio.FONT, text=wavelength_label_text, color=0xFFFFFF )
        wavelength_label_group.append( wavelength_label_text_area )
        display_group.append( wavelength_label_group )

        batch_number_label_group = displayio.Group( scale=1, x=38, y=9)
        batch_number_label_text = "batch:"
        batch_number_label_text_area = label.Label( terminalio.FONT, text=batch_number_label_text, color=0xFFFFFF )
        batch_number_label_group.append( batch_number_label_text_area )
        display_group.append( batch_number_label_group )

        print( "initialized graph screen" )
        return ( graph_bar, graph_bar_x, batch_number_label_text_area, polygon )
    else:
        print( "graph screen initialization failed" )
        return False, False, False, False, False, False, False, False, False, False, False, False



def read_spectral_sensor( spectral_sensor, band_designations ):
    bands_sorted = sorted( band_designations )
    try:
        spectral_all_uW_per_cm_2 = spectral_sensor.get_value(1) # 0==raw, 1==calibrated:  data arrives in sensor order, not sorted order
    except (OSError, AttributeError) as err:
        print( "spectral sensor fail: {}".format( err ))
        return False, False
    spectral_dictionary = {band_designations:spectral_all_uW_per_cm_2 for band_designations,spectral_all_uW_per_cm_2 in zip(band_designations,spectral_all_uW_per_cm_2)}
    values_sorted =[ ]
    for i in range (len(bands_sorted)):
        #print( round( spectral_dictionary[bands_sorted[i]], 3 ) )
        values_sorted.append( round( spectral_dictionary[bands_sorted[i]], 3 ) )
    #print( values_sorted )
    return values_sorted, spectral_dictionary

def initialize_button( i2c_bus ):
    try:
        button = I2C_Button( i2c_bus )
        print( "initialized_button" )
    except ValueError:
        button = False
        print( "button device not found" )
    return button

def initialize_display( i2c_bus ):
    try:
        display_bus = displayio.I2CDisplay( i2c_bus, device_address=0x3c )
        display = adafruit_displayio_ssd1306.SSD1306( display_bus, width=128, height=32 )
        display_group = displayio.Group()
        print( "initialized display" )
    except ValueError:
        display = False
        display_group = False
    return display, display_group

def initialize_battery_monitor( i2c_bus ):
    try:
        monitor = adafruit_max1704x.MAX17048(i2c_bus)
    except:
        print( "battery monitor failed to initialize" )
        monitor = False
    return monitor

def check_battery( monitor ):
    if monitor:
        battery_voltage = monitor.cell_voltage
        battery_percent = monitor.cell_percent
        time.sleep(0.2)
        battery_voltage = monitor.cell_voltage
        battery_percent = monitor.cell_percent
    else:
        battery_voltage = 0
        battery_percent = 0
    return battery_voltage, battery_percent

def initialize_spectral_sensor( i2c_bus ):
    try:
        spectral_sensor = AS7265X( i2c_bus )
        spectral_sensor.disable_indicator()
        spectral_sensor.set_measurement_mode(AS7265X_sparkfun.MEASUREMENT_MODE_6CHAN_CONTINUOUS)
        #print( f"Spectral sensor device type: {spectral_sensor.get_devicetype()}")
        #print( f"Spectral sensor firmware-version {spectral_sensor.get_major_firmware_version()}.{spectral_sensor.get_patch_firmware_version()}.{spectral_sensor.get_build_firmware_version()}")
        #print( f"Spectral sensor hardware-version {spectral_sensor.get_hardware_version()}")
        #print( f"Spectral sensor temperature {spectral_sensor.get_temperature_average()}C")
        #print( f"Spectral sensor temperature instantaneous {spectral_sensor.get_temperature()}C")
        gain_settings = ( "1X", "3.7X", "16X", "64X" )
        spectral_sensor.set_gain(AS7265X_sparkfun.GAIN_16X)
        gain = (spectral_sensor.virtual_read_register(AS7265X_sparkfun.CONFIG) & 0b110000) >> 4
        print("spectral sensor: successfully set gain to {}. 16X is the value at calibration".format(gain_settings[ gain ]))
        # *sic* INTERGRATION with the extra R is needed to interact with firmware
        # sensor will not saturate below 64*2.78ms
        integration_cycle_length_ms = 2.78
        desired_integration_time_ms = 167 # closest value to 166 as calibrated
        integration_setting_in_cycles = int( desired_integration_time_ms / integration_cycle_length_ms )
        spectral_sensor.set_integration_cycles(integration_setting_in_cycles)
        readout_of_integration_cycles = spectral_sensor.virtual_read_register(AS7265X_sparkfun.INTERGRATION_TIME)
        print( "spectral sensor: successfully set to integration cycles {} = {} ms".format(readout_of_integration_cycles, readout_of_integration_cycles*integration_cycle_length_ms))
        del gain_settings, gain, integration_cycle_length_ms, desired_integration_time_ms
        del integration_setting_in_cycles, readout_of_integration_cycles
        gc.collect()
    except ValueError as err:
        print( "spectral sensor initialization failed: {}".format(err))
        spectral_sensor = False
    return spectral_sensor

def timestamp_to_decimal_hour( timestamp ):
    try:
        decimal_hour = timestamp.tm_hour + timestamp.tm_min/60.0 + timestamp.tm_sec/3600.0
        return decimal_hour
    except ValueError as err:
        print( "Error: invalid timestamp: {:}".format(err) )
        return False

def update_batch( timestamp ):
    gc.collect()
    datestamp = "{:04}{:02}{:02}".format( timestamp.tm_year, timestamp.tm_mon, timestamp.tm_mday)
    try:
        with open( "/sd/batch.txt", "r" ) as b:
            try:
                previous_batchfile_string = b.readline()
                previous_datestamp = previous_batchfile_string[ 0:8 ]
                previous_batch_number = int( previous_batchfile_string[ 8: ])
            except ValueError:
                previous_batch_number = 0
            if datestamp == previous_datestamp:
                # this is the same day, so increment the batch number
                batch_number = previous_batch_number + 1
            else:
                # this is a different day, so start the batch number at 0
                batch_number = 0
    except OSError:
            print( "batch.txt file not found" )
            batch_number = 0

    batch_string = ( "{:03}".format( batch_number ))
    batch_file_string = datestamp + batch_string
    try:
        with open( "/sd/batch.txt", "w" ) as b:
            b.write( batch_file_string )
    except OSError as err:
        print("Error: writing batch.txt {:}".format(err) )
        pass
    batch_string = ( "{:}".format( batch_number ))
    return batch_string

def initialize_real_time_clock( i2c_bus ):
    null_time = time.struct_time(( 2020,  01,   01,   00,  00,  00,   0,   -1,    -1 ))
    try:
        real_time_clock = adafruit_pcf8523.PCF8523( i2c_bus )
        clock_battery_low = real_time_clock.battery_low
        if clock_battery_low:
            print( "clock battery is low. replace clock battery" )
        else:
            print( "clock battery is OK" )
        timenow = real_time_clock.datetime
        if timenow.tm_wday not in range ( 0, 7 ):
            real_time_clock.datetime = null_time
        timenow = real_time_clock.datetime
    except (ValueError, NameError) as err:
        print( "hardware clock fail: {}".format(err))
        real_time_clock = False
        clock_battery_low = True
        timenow = null_time
    if real_time_clock:
        # set the microcontroller system clock to real time
        system_clock = rtc.RTC()
        system_clock.datetime = real_time_clock.datetime
    return real_time_clock, clock_battery_low

def initialize_i2c_bus( SCL_pin, SDA_pin, pixel, success_color, fault_color, OFF ):
    try:
        i2c_bus = busio.I2C( SCL_pin, SDA_pin )
        print( "initialized i2c_bus" )
        for n in range (0, 4):
            pixel.fill( success_color )
            time.sleep( 0.1 )
            pixel.fill( OFF )
            time.sleep( 0.1 )
    except ValueError as err:
        i2c_bus = False
        print( "i2c bus fail: {} -- press reset button, or power off to restart".format( err ))
        while True:
            pixel.fill( fault_color )
            time.sleep( 0.1 )
            pixel.fill( OFF )
            time.sleep( 0.1 )
    return i2c_bus

def initialize_i2c_button( i2c_bus ):
    try:
        button = I2C_Button( i2c_bus )
        print( "initialized button" )
        print("    firmware version", button.version)
        print("    debounce ms", button.debounce_ms)
        button.clear()
        return button
    except:
        print( "button failed to initialize" )
        return False
        
def initialize_data_file( header, DATA_FILE ):
    try:
        os.stat( DATA_FILE )
        print( "data file already exists, does not need header" )
        return True
    except OSError:
        gc.collect()
        try:
            # create a new data file, and write the header in it
            with open( DATA_FILE, "w" ) as f:
                f.write( header )
            print( "header written" )
            return True
        except OSError as err:
            print( "error opening datafile, {}".format( err ))
            return False

def write_data_to_file( DATA_FILE, datapoint, button, pixel, OFF, success_color, fault_color ):
    try:
        with open( DATA_FILE, "a" ) as f:
            if pixel:
                pixel.fill ( success_color )
            if button: 
                button.led_bright = 64 
            f.write( datapoint )
            f.write("\n")
            time.sleep( 0.05 )
            f.close()
        if pixel:
            pixel.fill( OFF )
        if button: 
            button.led_bright = 1
        return True
    except OSError as err:
        print( "\nError: sd card fail: {:}\n".format(err) )
        if pixel:
            pixel.fill( fault_color ) #  ORANGE to show error: likely no SD card present, or SD card full.
            time.sleep( 0.25 )
            pixel.fill( OFF )

        return False

def initialize_sd_card_storage( onboard_neopixel, RED ):
    try:
        import sdioio
        sdcard = sdioio.SDCard( clock=board.SDIO_CLOCK,command=board.SDIO_COMMAND,data=board.SDIO_DATA,frequency=25000000)
        vfs = storage.VfsFat(sdcard)
        print( "sdioio success" )
    except:
        try:
            import sdcardio
            cs = board.SD_CS
            sd_card_spi = busio.SPI(board.SD_SCK, MOSI=board.SD_MOSI, MISO=board.SD_MISO)
            sdcard = sdcardio.SDCard(sd_card_spi, cs)
            vfs = storage.VfsFat(sdcard)
            print( "sdcardio success" )
        except( OSError, ValueError ) as err:
            print( "No SD card found, or card is full: {}".format(err) )
            vfs = False
            sdcard = False
            onboard_neopixel.fill( RED )
    return vfs, sdcard

def initialize_neopixel( pin, count ):
    num_pixels = count
    ORDER = neopixel.RGB
    neopixel_instance = neopixel.NeoPixel( pin, num_pixels, brightness=0.2, auto_write=True, pixel_order=ORDER )
    return neopixel_instance

def memory_check( message, start_mem_free_kB ):
    gc.collect()
    mem_free_kB = gc.mem_free()/1000
    print( "memory check: {}: free memory remaining = {:.2f} kB, {:.2f} %".format( message, mem_free_kB, (100* (mem_free_kB)/start_mem_free_kB )))

def blink(object, count, interval, low_level, high_level):
    try: 
        for n in range( 0, count ):
            object.led_bright = high_level
            time.sleep(interval)
            object.led_bright = low_level
            time.sleep(interval)
    except: 
        pass


def stall():
    print("intentionally stalled, press return to continue")
    input_string = False
    while input_string == False:
        input_string = input().strip()
mem_free_kB = gc.mem_free()/1000
print("after define functions memory free................. {:.2f} kB, {:.2f} %".format( mem_free_kB, 100 * mem_free_kB/start_mem_free_kB))

main()
