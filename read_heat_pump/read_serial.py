import csv
import time
import math
import datetime
import requests
from requests.auth import HTTPBasicAuth

import serial

from CoolProp.CoolProp import PropsSI
#=====================================================================
#Parameters
#=====================================================================
#FROST-Server parameters
frost_url = 'https://andlchaos300l.princeton.edu:8080/FROST-Server/v1.0/'
auth_user = 'chaos'
auth_pass = 'Zer0exergy'

#port
port = '/dev/ttyACM0' #or '/dev/ttyS5'
valve_pos = 0

#path variable
csv_path = '/home/chaos/Desktop/heat_pump_controls/read_heat_pump/heat_pump_data.csv'
 
#thermistor variables
SERIESRESISTOR = 10000
TEMPERATURENOMINAL = 25
BETA_COEFF = 3977
#=====================================================================
#Functions
#=====================================================================
def volt2resist(volt, series_resistor):
    resistance = 1023 / volt  - 1
    resistance = series_resistor / resistance
    return resistance
    
def steinhart_hart_eqn(resist, T_Beta, t_nominal):
    steinhart = resist / SERIESRESISTOR
    steinhart = math.log(steinhart)
    steinhart /= T_Beta
    steinhart += 1.0 / (t_nominal + 273.15)
    steinhart = 1.0 / steinhart
    steinhart -= 273.15
    return steinhart

def volt2pressure(analog_read, P_SensorMax):
    #A0 = 1mpa
    #A1 = 3mpa
    #convert the digital value to a voltage reading. "P_Voltage" is a float variable
    P_Voltage = float(analog_read) * 0.004
    #Scale the voltage reading to a pressure value. "P_SensorMax" is a constant
    pressure = P_SensorMax * ((P_Voltage - 0.5)/4);
    return pressure

def psi2pascal(psi):
    pascal = psi*6894.7572931783
    return pascal

def psi2degc(psi):
    pascal = psi2pascal(psi)
    degc = PropsSI('T','P',pascal,'Q',0,'R134A') - 273.15
    return degc

def get_id_from_header(location_str):
    split = location_str.split('/')
    thing = split[-1]
    idx1 = thing.index('(')
    idx2 = thing.index(')')
    thing_id = int(thing[idx1+1:idx2])
    return thing_id

def create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url):
    is_prop_reg = False
    observed_prop = {'name': obs_prop_name,
                      'description': prop_desc,
                      'definition': prop_def
                      }
    #check if the obs properties exist in the db
    if not prop_def: 
        filter_prop = "ObservedProperties?$filter=name eq '" + obs_prop_name + "' and description eq '" + prop_desc +\
                    "'&$select=id"
    else:
        filter_prop = "ObservedProperties?$filter=name eq '" + obs_prop_name + "' and description eq '" + prop_desc + "' and definition eq '" + prop_def +\
                    "'&$select=id"
                    
    find_prop = requests.get(frost_url + filter_prop)
    prop_content = find_prop.json()
    prop_ls = prop_content['value']
    nprops = len(prop_ls)
    if nprops> 0:
        is_prop_reg = True
    
    if is_prop_reg  == False:    
        r = requests.post(frost_url+"ObservedProperties", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=observed_prop)
        prop_id = get_id_from_header(r.headers['location'])
    
    else:
        prop_id = prop_ls[0]['@iot.id']

    return prop_id 

def create_sensor(sensor_name, sensor_desc, sensor_entype, 
                  sensor_metadata, frost_url):
    is_sensor_reg = False
    sensor_data = {"name": sensor_name,
                    "description": sensor_desc,
                    "encodingType": sensor_entype,
                    "metadata": sensor_metadata
                    }   

    #check if the sensor exist in the db
    filter_sensor = "Sensors?$filter=name eq '" + sensor_name + "' and description eq '" + sensor_desc + "' and encodingType eq '" + sensor_entype +\
                    "' and metadata eq '" +  sensor_metadata + "'&$select=id"
    find_sensor = requests.get(frost_url + filter_sensor)
    sensor_content = find_sensor.json()
    sensor_ls = sensor_content['value']
    nsensors = len(sensor_ls)
    if nsensors> 0:
        is_sensor_reg = True

    if is_sensor_reg  == False:    
        r = requests.post(frost_url+"Sensors", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=sensor_data)
        
        sensor_id = get_id_from_header(r.headers['location'])
    else:
        sensor_id = sensor_ls[0]['@iot.id']
    
    return sensor_id 

def create_thing_loc(thing_name, thing_desc, thing_props, 
                     loc_name, loc_desc, loc_coord):
    is_thingloc_reg = False
    foi = {"name": loc_name,
            "description": loc_desc,
            "encodingType": "application/vnd.geo+json",
            "location": {"type": "Point",
                        "coordinates": loc_coord
                        }
            }

    thingloc_data = {"name": thing_name,
                      "description": thing_desc,
                      "properties": thing_props,
                      "Locations": [foi]
                      }
    
    #check if the thing exist in the db
    filter_thing = "Things?$filter=name eq '" + thing_name + "' and description eq '" + thing_desc + "'&$select=id"
    find_thing = requests.get(frost_url + filter_thing)
    thing_content = find_thing.json()
    thing_ls = thing_content['value']
    nthings = len(thing_ls)
    if nthings> 0:
        is_thingloc_reg = True

    if is_thingloc_reg  == False:    
        r = requests.post(frost_url+"Things", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=thingloc_data)
        
        thing_id = get_id_from_header(r.headers['location'])
    else:
        thing_id = thing_ls[0]['@iot.id']
    
    return thing_id 
        
def create_datastream(ds_name, ds_desc, uom, thing_id, obs_prop_id,
                      sensor_id):
    is_ds_reg = False
    datastream_data = {"name": ds_name,
                       "description": ds_desc,
                       "observationType": "measurement",
                       "unitOfMeasurement": uom,
                       "Thing":{"@iot.id":thing_id},
                       "ObservedProperty":{"@iot.id":obs_prop_id},
                       "Sensor":{"@iot.id":sensor_id}
                       }
    
    #check if the ds exist in the db
    filter_ds = "Datastreams?$filter=name eq '" + ds_name + "' and Things/id eq '" + str(thing_id) + "'&$select=id"
    find_ds = requests.get(frost_url + filter_ds)
    ds_content = find_ds.json()
    ds_ls = ds_content['value']
    nds = len(ds_ls)
    if nds> 0:
        is_ds_reg = True

    if is_ds_reg == False:    
        r = requests.post(frost_url+"Datastreams", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=datastream_data)
        
        ds_id = get_id_from_header(r.headers['location'])
    else:
        ds_id = ds_ls[0]['@iot.id']
    
    return ds_id
#=====================================================================
#main script
#=====================================================================
#========================================================================
print('Creating obsProp')
#========================================================================
obs_prop_name = 'Temperature'
prop_desc = 'Temperature'
prop_def = 'https://en.wikipedia.org/wiki/Temperature'
temp_id = create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url)
print('****************************************')
print('Temp ID:', temp_id)
print('****************************************')
obs_prop_name = 'Pressure'
prop_desc = 'Pressure'
prop_def = ''
pressure_id = create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url)
print('****************************************')
print('Pressure ID:', pressure_id)
print('****************************************')
obs_prop_name = 'voltage'
prop_desc = 'voltage of the plug'
prop_def = ''
voltage_id = create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url)
print('****************************************')
print('Voltage ID:', voltage_id)
print('****************************************')
#========================================================================
print('Creating Sensor')
#========================================================================
sensor_name = 'TT0P-10KC3-T105-1500'
sensor_desc = 'THERMISTOR NTC 10KOHM 3977K CLIP'
sensor_entype = 'url'
sensor_metadata = 'https://www.digikey.com/en/products/detail/tewa-sensors-llc/TT0P-10KC3-T105-1500/8549160'
thermistor_id = create_sensor(sensor_name, sensor_desc, sensor_entype, 
                              sensor_metadata, frost_url)
print('****************************************')
print('Thermistor ID:', thermistor_id )
print('****************************************')
sensor_name = 'Generic Pressure Sensor'
sensor_desc = 'A generic pressure sensor'
sensor_entype = 'string'
sensor_metadata = 'If unclear what is the specific sensor use this entry'
pressure_sensor_id = create_sensor(sensor_name, sensor_desc, sensor_entype, 
                                   sensor_metadata, frost_url)

print('****************************************')
print('Pressure Sensor ID:', pressure_sensor_id)
print('****************************************')
#======================================================================
print('Creating things and location')
#======================================================================
thing_name = 'Heat Pump Controller'
thing_desc = 'data from the heat pump controller'
thing_props = {'deployment': 'heat pump controller'}
loc_name = 'Coral Gables'
loc_desc = 'City in Miami'
loc_coord = [0,0,0]
thing_id = create_thing_loc(thing_name, thing_desc, thing_props, 
                            loc_name, loc_desc, loc_coord)
print('****************************************')    
print('Thing ID:', thing_id)
print('****************************************')
#========================================================================
#datastream
#========================================================================
ds_name = thing_name + '_pressure voltage1'
ds_desc = 'pressure voltage1'
uom = {"name": "volt",
       "symbol": "v",
       "definition": ""}
ds_id1 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           voltage_id, pressure_sensor_id)

ds_name = thing_name + '_pressure1'
ds_desc = 'pressure1'
uom = {"name": "PSI",
       "symbol": "PSI",
       "definition": ""}
ds_id2 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           pressure_id, pressure_sensor_id)

ds_name = thing_name + '_pressure voltage2'
ds_desc = 'pressure voltage2'
uom = {"name": "volt",
       "symbol": "v",
       "definition": ""}
ds_id3 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           voltage_id, pressure_sensor_id)

ds_name = thing_name + '_pressure2'
ds_desc = 'pressure2'
uom = {"name": "PSI",
       "symbol": "PSI",
       "definition": ""}
ds_id4 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           pressure_id, pressure_sensor_id)

ds_name = thing_name + '_temp voltage1'
ds_desc = 'temp voltage1'
uom = {"name": "volt",
       "symbol": "v",
       "definition": ""}
ds_id5 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           voltage_id, thermistor_id)

ds_name = thing_name + '_liquid temp1'
ds_desc = 'liquid temperature 1'
uom = {"name": "degree celsius",
       "symbol": "degC",
       "definition": ""}
ds_id6 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           temp_id, thermistor_id)

ds_name = thing_name + '_temp voltage2'
ds_desc = 'temp voltage2'
uom = {"name": "volt",
       "symbol": "v",
       "definition": ""}
ds_id7 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           voltage_id, thermistor_id)

ds_name = thing_name + '_liquid temp2'
ds_desc = 'liquid temperature 2'
uom = {"name": "degree celsius",
       "symbol": "degC",
       "definition": ""}
ds_id8 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           temp_id, thermistor_id)


ds_name = thing_name + '_superheat'
ds_desc = 'superheat'
uom = {"name": "degree celsius",
       "symbol": "degC",
       "definition": ""}
ds_id9 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           temp_id, thermistor_id)

ds_name = thing_name + '_valve_pos'
ds_desc = 'valve position'
uom = {"name": "valve position",
       "symbol": "unitless",
       "definition": ""}
ds_id10 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           temp_id, thermistor_id)
#======================================================================
print('Creating observations')
#======================================================================
obs_data = {'phenomenonTime': '',
            'resultTime': '',
            'result': '',
            'Datastream': {}}

#UNCOMMENT IF USING 1MPa SENSOR
#This is the max pressure of the test sensor IN PSI

#A0 = 1mpa
#A1 = 3mpa
TestSensorMax_1mpa = 145.04 
TestSensorMax_3mpa = 435.113

loop = True
#read the serial that is connected to the usb port of laptop
ser = serial.Serial()
ser.baudrate = 115200
ser.port = port
ser.open()

#the first few lines are initialisation lines
for _ in range(4):
    init_str = ser.readline()
    print(init_str)
    
ser.write(str.encode('v'+str(valve_pos)))
#read the lines from changing the valve
for _ in range(4):
    init_str = ser.readline()
    print(init_str)

while loop:
    dt = datetime.datetime.now()
    dt = dt.astimezone()
    dtstr = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    try:
        obs_data['phenomenonTime'] = dtstr
        obs_data['resultTime'] = dtstr
        #get the data streaming through the usb
        data_str = str(ser.readline())
        data_ls = data_str.split(',')
        with open(csv_path, 'a') as f:
            writer = csv.writer(f)
            data_ls.insert(0, dtstr)
            writer.writerow(data_ls)
            
        print(data_ls)
        print(data_str)
        #the pressure volt data1
        pressure_volt1 = int(data_ls[2])
        pressure1 = volt2pressure(pressure_volt1, TestSensorMax_1mpa)
        obs_data['result'] = pressure_volt1
        obs_data['Datastream'] = {'@iot.id':ds_id1}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Pressure Raw1:', pressure_volt1)
        print(r1)
        
        #the pressure data1
        obs_data['result'] = pressure1
        obs_data['Datastream'] = {'@iot.id':ds_id2}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        
        print('Pressure1 (PSI):', pressure_volt1)
        print(r1)
        
        #the pressure volt data2
        pressure_volt2 = int(data_ls[3])
        pressure2 = volt2pressure(pressure_volt2, TestSensorMax_3mpa)
        obs_data['result'] = pressure_volt2
        obs_data['Datastream'] = {'@iot.id':ds_id3}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Pressure Raw2:', pressure_volt2)
        print(r1)
        #the pressure data2
        obs_data['result'] = pressure2
        obs_data['Datastream'] = {'@iot.id':ds_id4}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Pressure2:', pressure2)
        print(r1)
        #the thermistor data1
        thermistor1 = int(data_ls[4])
        resist1 = volt2resist(thermistor1, SERIESRESISTOR)
        temp1 = steinhart_hart_eqn(resist1, BETA_COEFF, TEMPERATURENOMINAL)
        obs_data['result'] = thermistor1
        obs_data['Datastream'] = {'@iot.id':ds_id5}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Thermistor Raw1:', thermistor1)
        print(r1)
        obs_data['result'] = temp1
        obs_data['Datastream'] = {'@iot.id':ds_id6}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Thermistor temp1:', temp1)
        print(r1)
        #the thermistor data2
        thermistor2 = int(data_ls[5])
        resist2 = volt2resist(thermistor2, SERIESRESISTOR)
        temp2 = steinhart_hart_eqn(resist2, BETA_COEFF, TEMPERATURENOMINAL)
        obs_data['result'] = thermistor2
        obs_data['Datastream'] = {'@iot.id':ds_id7}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Thermistor Raw2:', thermistor2)
        print(r1)
        obs_data['result'] = temp2
        obs_data['Datastream'] = {'@iot.id':ds_id8}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Thermistor temp2:', temp2)
        print(r1)
        
        #calculate the superheat
        pressure_degc = psi2degc(pressure1)
        superheat = temp2-pressure_degc
        obs_data['result'] = superheat
        obs_data['Datastream'] = {'@iot.id':ds_id9}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Superheat:', superheat)
        print(r1)
        
        #valve position
        valve_pos1 = int(data_ls[10])
        obs_data['result'] = valve_pos1
        obs_data['Datastream'] = {'@iot.id':ds_id10}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print('Valve position:', valve_pos1)
        print(r1)
        
    except:
        ser.close()