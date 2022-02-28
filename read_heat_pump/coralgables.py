import time
import datetime
import requests
from requests.auth import HTTPBasicAuth
#========================================================================
#Parameters
#========================================================================
#FROST SERVER
frost_url = 'https://andlchaos300l.princeton.edu:8080/FROST-Server/v1.0/'
auth_user = 'chaos'
auth_pass = 'Zer0exergy'

#OPEN WEATHER API
lat = '25.71694688819991'
lon = '-80.27940134068889'
api_key = '5f587efcc6bbf890d3b689a82f77d589'
base_url = 'http://api.openweathermap.org/data/2.5/'
get_req = base_url+'weather?lat=' + lat + '&lon=' + lon + '&units=metric' + '&appid=' + api_key
interval = 600 #seconds
#========================================================================
#Functions
#=============================================================================
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
        print(observed_prop)
        print(r)
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
#========================================================================
print('Creating obsProp')
#========================================================================
obs_prop_name = 'Air Temperature'
prop_desc = 'air temperature'
prop_def = 'air temperature'
air_temp_id = create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url)
print('****************************************')
print('Air Temp ID:', air_temp_id)
print('****************************************')
obs_prop_name = 'Relative Humidity'
prop_desc = 'Relative Humidity'
prop_def = 'https://en.wikipedia.org/wiki/Humidity'
rel_humid_id = create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url)
print('****************************************')
print('Rel Humid ID:', rel_humid_id)
print('****************************************')
obs_prop_name = 'wind speed'
prop_desc = 'speed of air movement'
prop_def = ''
wind_speed_id = create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url)
print('****************************************')
print('Wind Speed ID:', wind_speed_id)
print('****************************************')
obs_prop_name = 'wind deg'
prop_desc = 'wind direction'
prop_def = ''
wind_deg_id = create_obs_prop(obs_prop_name, prop_desc, prop_def, frost_url)
print('****************************************')
print('Wind deg ID:', wind_deg_id)
print('****************************************')
#========================================================================
print('Creating Sensor')
#========================================================================
sensor_name = 'open weathermap'
sensor_desc = 'data from open weathermap'
sensor_entype = 'url'
sensor_metadata = 'https://openweathermap.org/api'
sensor_id = create_sensor(sensor_name, sensor_desc, sensor_entype, 
                  sensor_metadata, frost_url)
print('****************************************')
print('Sensor ID:', sensor_id )
print('****************************************')
#======================================================================
print('Creating things and location')
#======================================================================
thing_name = 'open weather map'
thing_desc = 'data from open weathermap api'
thing_props = {'deployment': 'pulling data from open weather api'}
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
ds_name = thing_name + '_air temp'
ds_desc = 'air temperature'
uom = {"name": "degree celsius",
       "symbol": "degC",
       "definition": ""}
ds_id1 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           air_temp_id, sensor_id)
ds_name = thing_name + '_rel humidity'
ds_desc = 'relative humidity'
uom = {"name": "relative humidity",
       "symbol": "%",
       "definition": ""}
ds_id2 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           rel_humid_id, sensor_id)
ds_name = thing_name + '_wind speed'
ds_desc = 'wind speed'
uom = {"name": "meter per second",
       "symbol": "m/s",
       "definition": ""}
ds_id3 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           wind_speed_id, sensor_id)

ds_name = thing_name + '_wind deg'
ds_desc = 'wind degree'
uom = {"name": "degree",
       "symbol": "o",
       "definition": ""}
ds_id4 = create_datastream(ds_name, ds_desc, uom, thing_id, 
                           wind_deg_id, sensor_id)

#======================================================================
print('Creating observations')
#======================================================================
obs_data = {'phenomenonTime': '',
            'resultTime': '',
            'result': '',
            'Datastream': {}}

prev_dt = None
loop = True
while loop:    
    #request for data from the open weather map 
    r = requests.get(get_req)
    json_data = r.json()
    epoch_time = json_data['dt']
    dt = datetime.datetime.fromtimestamp(epoch_time)
    dt = dt.astimezone() # local time
    print(dt)
    if dt != prev_dt:
        dtstr = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
        obs_data['phenomenonTime'] = dtstr
        obs_data['resultTime'] = dtstr
        
        #air temp
        air_temp = json_data['main']['temp']
        obs_data['result'] = air_temp
        obs_data['Datastream'] = {'@iot.id':ds_id1}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print(r1)
        #rel humidity
        rel_humid = json_data['main']['humidity']
        obs_data['result'] = rel_humid
        obs_data['Datastream'] = {'@iot.id':ds_id2}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print(r1)
        #wind speed
        wind_speed = json_data['wind']['speed']
        obs_data['result'] = wind_speed
        obs_data['Datastream'] = {'@iot.id':ds_id3}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print(r1)   
        #wind deg
        wind_deg = json_data['wind']['deg']
        obs_data['result'] = wind_deg
        obs_data['Datastream'] = {'@iot.id':ds_id4}
        r1 = requests.post(frost_url+"Observations", 
                          auth=HTTPBasicAuth(auth_user, auth_pass), 
                          json=obs_data)
        print(r1)
        prev_dt = dt
        time.sleep(interval)
    else:
        time.sleep(interval)