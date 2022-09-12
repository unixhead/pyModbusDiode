#
# THIS IS A POC ONLY AND SHOULD NOT BE USED IN PRODUCTION
#

#
# For paid support/development activities, please visit https://otnss.co.uk
#
# For open source support, please visit https://github.com/unixhead/pyModbusDiode
#


# pyModbusDiodeSouth
# Receives UDP transmission from pyModbusDiodeNorth and presents the data in a Modbus Server
#
# Original source: https://github.com/unixhead/pyModbusDiode

# Beerware license

# Uses PyModbusTCP for all the hard work
# https://github.com/sourceperl/pyModbusTCP



#TODO modbus server allows clients to update data, should be read-only
# support non standard addresses


from socket import *
from pyModbusTCP.server import ModbusServer, ModbusServerDataBank



def debugLog(data = None):
    print(data)

def indexExists(list,index):
    try:
        list[index]
        return True
    except IndexError:
        return False


modbusIP = "127.0.0.1"
modbusPort = 10503

# start udp server
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', 15000))

#start modbus server
dataBank = ModbusServerDataBank()
serverObj = ModbusServer(host=modbusIP, port=modbusPort, no_block=True, data_bank=dataBank)
serverObj.start()

registerList = list()
for i in range (0,20000):
    registerList.append(0)

coilList = list()
coilList = [0] * 9999

while True:
    message, address = serverSocket.recvfrom(1024)
    strMessage = message.decode('utf-8')
    strIP = str(address[0])
    srcPport=int(address[1])
    debugLog("From: " + str(strIP) + " / " + str(srcPport) + "  Message: " + str(strMessage))

    if strMessage[0:6] == "STATUS":
        #status message
        debugLog("STATUS: " + str(strMessage))
    else:
        #normal message format: (pointAddress,pointInterval,pointType,getTimeMS(), pointValue)
        mAr = strMessage.split(",")
        #print("ar: " + str(mAr))
        if len(mAr) != 5:
            debugLog("Invalid Array")

        # address must be int < 65535
        mAddress = int(mAr[0])
        if (mAddress > 65535): 
            debugLog("Invalid Address")
            continue

        # type needs to be r or c
        mType = mAr[2]
        if mType != "r" and mType != "c":
            debugLog("Invalid Type")
            continue

        # timestamp is integer of milliseconds unixhtime
        if mAr[3].isdigit():
            mTimestamp = int(mAr[3])
        else:
            debugLog("invalid timestamp: " + str(mAr[3]))
            continue
        
        if mAr[4].isdigit():
            mValue = int(mAr[4])
        else:
            debugLog("invalid value")
            continue


        # if received value was a coil
        if mType == "c":
            if indexExists(coilList, mAddress):
                if coilList[mAddress] != mValue:
                    coilList[mAddress] = mValue
                    #debugLog("writing coils: " + str(coilList))
                    serverObj.data_hdl.write_coils(0, coilList, "None")
            else:
                coilList[mAddress] = mValue
                #debugLog("writing coils: " + str(coilList))
                serverObj.data_hdl.write_coils(0, coilList, "None")
        else:
            # otherwise treat as a register
            listAddress = mAddress - 30000
            if indexExists(registerList, listAddress):
                if registerList[listAddress] != mValue:
                    registerList[listAddress] = mValue
                    debugLog("setting register: " + str(listAddress))
                    serverObj.data_hdl.data_bank.set_input_registers(30000, registerList)
            else:
                
                registerList[listAddress] = mValue
                debugLog("setting register: " + str(listAddress))
                serverObj.data_hdl.data_bank.set_input_registers(30000, registerList)



