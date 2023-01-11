#Add Phidgets Library
from Phidget22.Phidget import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.VoltageRatioInput import *
from Phidget22.Devices.TemperatureSensor import *
from Phidget22.Devices.HumiditySensor import *
from Phidget22.Devices.Log import *
from Phidget22.Net import *
import requests
#Required for sleep statement
import time
import math
# Check file status
import os
from datetime import datetime



directionTable =[
[ 0.155, 0.104 ],
[ 0.244, 0.206 ],
[ 0.562, 0.532 ],
[ 0.881, 0.758 ],
[ 0.82, 0.632 ],
[ 0.716, 0.35 ],
[ 0.401, 0.067 ],
[ 0.076, 0.052 ],
]

def getDirection(windDirection):
    if(windDirection == 0):
        return "N"
    elif(windDirection == 1):
        return "NE"
    elif(windDirection == 2):
        return "E"
    elif(windDirection == 3):
        return "SE"
    elif(windDirection == 4):
        return "S"
    elif(windDirection == 5):
        return "SW"
    elif(windDirection == 6):
        return "W"
    elif(windDirection == 7):
        return "NW"
    
def getTimeMillis():
    return time.time() * 1000

def checkRatio(ratio, comparison):
    if(abs(ratio - comparison) < 0.01):
        return True
    else:
        return False
    
rainEvents = 0
def rain_StateChange(self, state):
    global rainEvents
    if(state):
        rainEvents = 1
        #print("Bucket tipped, add 0.2794mm of rain")
    
windTime = math.nan
windSpeed = 0
lastWindSpeed = 0
def speed_StateChange(self, state):
    global windTime
    global windSpeed
    global lastWindSpeed
    windFreq = 0    
    
    if(state):
        millis = getTimeMillis() - windTime
        windTime = getTimeMillis()
        if(millis > 0):
            windFreq = 1000.0/millis
            windSpeed = 1.492 * windFreq
            if abs(windSpeed - lastWindSpeed) < 20: #sometimes, we get huge wind speeds, meaning contact bounce? try to eliminate these 
                lastWindSpeed = windSpeed
            else:
                windSpeed = lastWindSpeed
                Log.log(LogLevel.PHIDGET_LOG_INFO, "WIND SPEED ERROR")            

prevRatio = math.nan
windDirection = 0
def direction_Change(self, voltageRatio):
    global prevRatio
    global windDirection
    badReading = False    
    if(not checkRatio(voltageRatio, prevRatio)):
        badReading = True        
    prevRatio = voltageRatio    
    if(badReading):
        return    
    for i in range(8):
        if(checkRatio(voltageRatio, directionTable[i][0]) or checkRatio(voltageRatio, directionTable[i][1])):
           windDirection = i
           return

def onAttach(self):
    if(self.getHubPort() == 0):
        try:
            #Set the wine vane to a reasonable data interval
            self.setDataInterval(10)        
        except PhidgetException as ex:            
            Log.log(LogLevel.PHIDGET_LOG_INFO, "PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)
    Log.log(LogLevel.PHIDGET_LOG_INFO, "ATTACHED: " + str(self))

def onDetach(self):
    Log.log(LogLevel.PHIDGET_LOG_INFO, "DETACHED: " + str(self))

def onError(self, code, description):
    Log.log(LogLevel.PHIDGET_LOG_INFO, "ERROR EVENT: " + str(code) + " "  + str(description))

#Initial connections
Log.enable(LogLevel.PHIDGET_LOG_INFO, "/home/pi/Desktop/weather_log.log")

#Lucas is using a WiFi VINT Hub, so this line is here. Not required if your VINT Hub is connected directly to your raspberry pi.
Net.enableServerDiscovery(PhidgetServerType.PHIDGETSERVER_DEVICEREMOTE)

#Create
anemometer = DigitalInput()
windVane = VoltageRatioInput()
rainGauge = DigitalInput()
temperature = TemperatureSensor()
humidity = HumiditySensor()

#Address
windVane.setHubPort(0)
windVane.setIsHubPortDevice(True)
windVane.setDeviceSerialNumber(597793)
windVane.setOnVoltageRatioChangeHandler(direction_Change)
windVane.setOnAttachHandler(onAttach)
windVane.setOnDetachHandler(onDetach)
windVane.setOnErrorHandler(onError)

anemometer.setHubPort(1)
anemometer.setIsHubPortDevice(True)
anemometer.setDeviceSerialNumber(597793)
anemometer.setOnStateChangeHandler(speed_StateChange)
anemometer.setOnAttachHandler(onAttach)
anemometer.setOnDetachHandler(onDetach)
anemometer.setOnErrorHandler(onError)

rainGauge.setHubPort(2)
rainGauge.setIsHubPortDevice(True)
rainGauge.setDeviceSerialNumber(597793)
rainGauge.setOnStateChangeHandler(rain_StateChange)
rainGauge.setOnAttachHandler(onAttach)
rainGauge.setOnDetachHandler(onDetach)
rainGauge.setOnErrorHandler(onError)

temperature.setHubPort(3)
temperature.setDeviceSerialNumber(597793)
temperature.setOnAttachHandler(onAttach)
temperature.setOnDetachHandler(onDetach)
temperature.setOnErrorHandler(onError)

humidity.setHubPort(3)
humidity.setDeviceSerialNumber(597793)
humidity.setOnAttachHandler(onAttach)
humidity.setOnDetachHandler(onDetach)
humidity.setOnErrorHandler(onError)


#Open
#Using open without a timeout. This allows devices to attach/detach and the program won't crash.
windVane.open()
anemometer.open()
rainGauge.open()
temperature.open()
humidity.open()


# Write Headers if file doesn't exist
if (not os.path.isfile('/var/www/html/weather/weather_data.csv')):
    with open('/var/www/html/weather/weather_data.csv', 'a') as datafile:
        datafile.write("Date,Wind Speed,Wind Direction,Rain(mm),Temperature,Humidity\n")

count = 0 #keep track of time
while(True):
    try:
        base_temperature = temperature.getTemperature() 
        temperature_f = str((base_temperature*1.8)+32) 
        temperature_c = str(base_temperature)   
    except PhidgetException as ex:
        temperature_f = ""
        temperature_c = ""
        Log.log(LogLevel.PHIDGET_LOG_INFO, "TEMP: PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)

    try:
        base_humidity = humidity.getHumidity()
        humidity_str = str(base_humidity)
    except PhidgetException as ex:
        humidity_str = ""
        Log.log(LogLevel.PHIDGET_LOG_INFO, "HUM: PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)


    windvane_str = str(round(windSpeed,2))
    anemometer_str = getDirection(windDirection)
    rain_str = str(rainEvents)
    rainEvents = 0 #reset, summing can be done on website    
        
    try:
        now = datetime.now()
        timeStr = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        fileStr = timeStr + "," + windvane_str + "," + anemometer_str + "," + rain_str + "," + temperature_c + "," + humidity_str + "\n"
        # Update for live stream on webpage
        with open('/var/www/html/weather/weather_latest.csv', 'w') as datafile:
            datafile.write(fileStr)
        
        #Only update main file every minute, should probably cut back even more
        if(count == 60):
            count = 0
            # Write data to file in CSV format                    
            with open('/var/www/html/weather/weather_data.csv', 'a') as datafile:
                datafile.write(fileStr)                        
        time.sleep(1.0)        
        count += 1
    except Exception as e:
        Log.log(LogLevel.PHIDGET_LOG_INFO, str(e))  
  