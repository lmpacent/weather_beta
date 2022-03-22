
#Add Phidgets Library
from Phidget22.Phidget import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.VoltageRatioInput import *
#Required for sleep statement
import time
import math

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
        rainEvents += 1
        print("Bucket tipped, add 0.2794mm of rain")
    
windTime = math.nan
windSpeed = 0
def speed_StateChange(self, state):
    global windTime
    global windSpeed
    windFreq = 0    
    
    if(state):
        millis = getTimeMillis() - windTime
        windTime = getTimeMillis()
        if(millis > 0):
            windFreq = 1000.0/millis
            windSpeed = 1.492 * windFreq            

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
    
#Create
anemometer = DigitalInput()
windVane = VoltageRatioInput()
rainGauge = DigitalInput()

#Address
windVane.setHubPort(0);
windVane.setIsHubPortDevice(True);
windVane.setOnVoltageRatioChangeHandler(direction_Change)


anemometer.setHubPort(1);
anemometer.setIsHubPortDevice(True);
anemometer.setOnStateChangeHandler(speed_StateChange)

rainGauge.setHubPort(2);
rainGauge.setIsHubPortDevice(True);
rainGauge.setOnStateChangeHandler(rain_StateChange)

#Open
windVane.openWaitForAttachment(1000)
anemometer.openWaitForAttachment(1000)
rainGauge.openWaitForAttachment(1000)

#Set Data Interval
windVane.setDataInterval(windVane.getMinDataInterval())

while(True):
    time.sleep(1.0)
    print("Update: Wind Speed: " + str(round(windSpeed,2)) + " mph | Wind Direction: " + getDirection(windDirection) + " Rain Fall (mm): " + str(rainEvents * 0.2794) + "\n")
  