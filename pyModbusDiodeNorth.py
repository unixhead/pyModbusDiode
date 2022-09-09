#
# THIS IS A POC ONLY AND SHOULD NOT BE USED IN PRODUCTION
#

# pyModbusDiodeNorth
# Reads Modbus/TCP and transmits via UDP for sending over uni-directional links
#
# Original source: https://github.com/unixhead/pyModbusDiode

# Beerware license

# Uses PyModbusTCP for all the hard work
# https://github.com/sourceperl/pyModbusTCP


from pyModbusTCP.client import ModbusClient
from socket import *
import time

def_loopTime = 20 #how long the main loop should be in milliseconds, max recommended polling frequency is 40hz = every 25ms, therefore loop every 20ms

class ModbusDiodeNorthConfig:
    
    path = "./config"
    modbusServer = "127.0.0.1"
    modbusPort = 502
    southServer = "127.0.0.1"
    southPort = 10502
    debug = False

    def __init__(self, debug = False):
        self.debug=debug
        self.points = list()
        self.loadConfig()
        
        


    def loadConfig(self):
        try:
            fHandle = open(self.path,'r')
        except (OSError, IOError) as e:
            print("Failed to open configuration file")
            return False

        for line in fHandle:
            #Config line ModbusServer=<IP>
            if line[0:12] == "ModbusServer":
                srvPos = str(line).find("=")
                self.modbusServer = line[srvPos+1:].strip()
                self.debugLog("Modbus Server: " + self.modbusServer)
                continue

            #Config line ModbusPort=<portnum>
            if line[0:10] == "ModbusPort":
                srvPos = str(line).find("=")
                self.modbusPort = line[srvPos+1:].strip()
                self.debugLog("Modbus port: " + str(self.modbusPort))
                continue
            
            #Config line SouthServer=<ip>
            if line[0:11] == "SouthServer":
                srvPos = str(line).find("=")
                self.southServer = line[srvPos+1:].strip()
                self.debugLog("South Server: " + self.southServer)
                continue

            #Config line SouthPort=<portno>
            if line[0:9] == "SouthPort":
                srvPos = str(line).find("=")
                self.southPort = line[srvPos+1:].strip()
                self.debugLog("South Port: " + self.southPort)
                continue

            if line[0:23] == "TransmitUnchangedValues":
                srvPos = str(line).find("=")
                self.unchangedValues = line[srvPos+1:].strip()
                self.debugLog("Transmit Unchanged: " + str(self.unchangedValues))
                continue




            #All other config lines
            if line[0] != "#" and line.strip() != "": #ignore lines starting with #
                #Format is: address, <frequency (ms)>, <type>
                self.debugLog("READLINE: " + line.strip())
                seperator = ","
                intervalMS = 1000
                type = "default"
                # get address, first field
                pos = str(line).find(seperator)
                if pos == -1:
                    #line just contains an address                    
                    address = line.strip()                    
                else:
                    #address = leftmost pos characters                   
                    address = line[:pos]
                    tmpInterval = line[pos+1:].strip()
                    if tmpInterval != "": # frequency value can be empty if left at default 
                        intervalMS = line[pos+1:].strip()
                    
                    nextpos = str(line).find(seperator, pos+1) # see if there's a comma in the rest of the string, if so then this line defines the type of address
                    if nextpos != -1:                        
                        type = line[nextpos+1:].strip()
                        intervalMS = line[pos+1:nextpos]

                if type == "default":
                    if int(address) < 20000:
                        type = "c"
                    else:
                        type = "r"
                    #1-9999 - discrete output coils R/W - binary
                    #10001 - 19999 - discrete input contacts R/O - binary
                    #30001 - 39999 - analog input registers - R/O - 16 bit int
                    #40001 - 49999 - analog output holding registers - R/W - 16 bit int

                self.createPoint(address,intervalMS,type)

        fHandle.close()


    def createPoint(self, address, frequency, type):
        self.points.append((address, frequency, type ))



    def debugPoints(self):
        if len(self.points) == 0:
            self.debugLog("No Points Found")
            return False

        for point in self.points:
            self.debugLog("address: " + str(point[0]))
            self.debugLog("freq: " + str(point[1]))
            self.debugLog("type: " + str(point[2]))


    def getValue(self,value):
        if value == "serverAddress":
            return self.modbusServer
        elif value == "serverPort":
            return self.modbusPort
        elif value == "southServer":
            return self.southServer
        elif value == "southPort":
            return self.southPort
        elif value == "unchangedValues":
            return self.unchangedValues
        else:
            #will be an address of a point
            for point in self.points:
                if str(point[0]) == value:
                    return point


    def getPoints(self):
        #self.debugLog("returning point array of size:" + str(len(self.points)))
        return self.points




    def debugLog(self,data = None):
        if self.debug:
            print(data)




# TODO LIST
# if there's a failure or fault, send it via UDP so the downstream side is made aware
# periodic status reports
# sort out error handling  if modbus server fails/quits
# use same UDP connection to avoid multiple source ports, make life easier for firewalls
# support non standard addresses for coils/registers/etc


def debugLog(data = None):
    print(data)

def getTimeMS():
    return int(time.time()*1000)


def getCoil(modbusObject, address):
    coilValue = modbusObject.read_coils(address)

    #debugLog("coil value at addr: " + str(address) + " = " + str(coilValue))
    if coilValue[0] == True:
        return 1
    else:
        return 0


def getRegister(modbusObject, address):
    if address >= 40000 and address <= 49999:
            regContent = modbusObject.read_holding_registers(address)
    elif address >= 30000 and address <= 39999:
        regContent = modbusObject.read_input_registers(address)
    else:
        # will probably error as the pyModbusTCp library checks addresses
        regContent = modbusObject.read_holding_registers(address)

    #debugLog("value at addr: " + str(address) + " = " + str(regContent))
    return regContent[0]


def transmitPoint(txData):
    debugLog("TX: " + str(txData))
    s = socket(type=SOCK_DGRAM)
    s.sendto(bytes(str(txData), 'utf-8'),(southServer,int(southPort)))
    s.close()


#read config
conf = ModbusDiodeNorthConfig(True)
conf.debugPoints()

#create client using pyModbusTCP
modbusClientObj = ModbusClient() 
modbusClientObj.host(conf.getValue("serverAddress"))
modbusClientObj.port(conf.getValue("serverPort"))

#extract other needed variables from config object
southServer = conf.getValue("southServer")
southPort = conf.getValue("southPort")
unchangedValues  = conf.getValue("unchangedValues")
debugLog("unchanged: " + str(unchangedValues))

# Try to connect to modbus server
while True:
    if (modbusClientObj.open() != True):
        debugLog("Connect failed")
        time.sleep(5)
    else:
        debugLog("connected")
        break
    

points = list()
mainPoints = list()
points = conf.getPoints()

# no longer need the conf object, destroy it
del conf

lastLoopStartTime=getTimeMS()
debugLog("STARTTIME: " + str(lastLoopStartTime))

#do an initial scan of all points
for point in points:
    #debugLog("initial scan: " + str(point))
    pointAddress = int(point[0])
    pointInterval = point[1]
    pointType = point[2]

    if pointType == "c":
        pointValue = getCoil(modbusClientObj, pointAddress)

    else:
        pointValue = getRegister(modbusClientObj,pointAddress)


    currentPoint =(pointAddress,pointInterval,pointType,getTimeMS(), pointValue)
    currentPointStr = str(pointAddress) + "," + str(pointInterval) + "," + str(pointType) + "," + str(getTimeMS()) + "," + str(pointValue)
    #create new array for main loop that includes previous value and poll time
    mainPoints.append(currentPoint)

    #send the data over the diode link
    transmitPoint(currentPointStr)


#delete original array as will only use the main one with previous value and poll time in from now on
points= False


#
# MAIN LOOP
#
# Runs through each point
# If the scanning interval has been reached then poll a value for the point and send it
# If not then loop through rest of points
# At the end see how long the main loop took, this is set to def_loopTime in milliseconds
# Aim for each loop to last exactly def_loopTime milliseconds, so pause code if it completed in less time
#

lastLoopStartTime=getTimeMS()
while True:
    loopStartTime = getTimeMS()
    #debugLog("MAIN START: " + str(loopStartTime))
    n = 0
    for point in mainPoints:
        #debugLog("MAIN: " + str(point))
        pointAddress = point[0]
        pointInterval = int(point[1])
        pointType = point[2]
        pointLastScanned = int(point[3])
        pointLastValue = point[4]
        # do we need to scan it, if lastLoopStartTime - loopStartTime is smaller than interval
        interval =  loopStartTime - pointLastScanned
        if interval > pointInterval:
            #debugLog("SCANNING as elapsed is : " + str(interval) + " and interval: " + str(pointInterval))
            if pointType == "c":
                pointValue = getCoil(modbusClientObj, pointAddress)
            else:                
                pointValue = getRegister(modbusClientObj,pointAddress)

            currentPoint = pointAddress,pointInterval,pointType,getTimeMS(), pointValue
            currentPointStr = str(pointAddress) + "," + str(pointInterval) + "," + str(pointType) + "," + str(getTimeMS()) + "," + str(pointValue)
            mainPoints[n] = currentPoint
            
            if pointValue == pointLastValue: # unchanged
                if int(unchangedValues) != 0 : # value hasn't changed but config requests to transmit them anyway                    
                    transmitPoint(currentPointStr)
            else: # value has changed = send it
                transmitPoint(currentPointStr)

        n+=1

    elapsed =  loopStartTime - lastLoopStartTime
    lastLoopStartTime = loopStartTime

    # work out how long it took to run this loop (usually <1ms, but depends how slow the modbus server is in responding)
    # max recommended frequency is 40hz, which is 40ms between runs.
    # aim at def_loopTime (20ms default) between run
    if elapsed < def_loopTime:
        sleepTime = (def_loopTime - elapsed) / 1000
        #debugLog("loop took: " + str(elapsed) + " - sleeping for :" + str(sleepTime))
        time.sleep(sleepTime)
        

