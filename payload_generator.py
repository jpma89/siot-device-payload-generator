import datetime
import json
import requests
from prettytable import PrettyTable
from tqdm import tqdm

def readServiceKey(serviceKeyFileName):
    with open(serviceKeyFileName) as serviceKeyFile:
        serviceKey = json.load(serviceKeyFile)
        deviceConnectivityUrl = serviceKey['endpoints']['iot-device-connectivity']
        authenticationUrl = serviceKey['uaa']['url']
        clientId = serviceKey['uaa']['clientid']
        clientSecret = serviceKey['uaa']['clientsecret']
        scopeRead = serviceKey['uaa']['clientid'].split('|')[1]+'.dc.r'
        scopeCrud = serviceKey['uaa']['clientid'].split('|')[1]+'.dc.cud'+' '+serviceKey['uaa']['clientid'].split('|')[1]+'.dc.r'
        return deviceConnectivityUrl, authenticationUrl, clientId, clientSecret, scopeRead, scopeCrud

def getAccessToken(scope):
    url = authenticationUrl+'/oauth/token'
    response = requests.post(url=url, data={'grant_type': 'client_credentials', 'response_type': 'token', 'client_id': clientId, 'client_secret': clientSecret, 'scope': scope})
    return json.loads(response.text)['access_token']

def sendGetRequest(urlEndpoint):
    #TODO: Implement standard handling for OAuth2.0 credential flow
    url = deviceConnectivityUrl+urlEndpoint
    response = requests.get(url=url, headers={'Authorization': 'Bearer '+accessToken})
    return json.loads(response.text)

def getDevices():
    devices = sendGetRequest('/api/v1/devices?top=100000') #?top=100000 to overcome the default number of 100 devices that would be returned by the API in case there are more than 100 devices. The number 100000 has been chosen randomly without a particular reason in mind.
    return devices

def getDevice(deviceId):
    device = sendGetRequest('/api/v1/devices/'+deviceId)
    return device

def getSensorType(sensorTypeId):
    sensorType = sendGetRequest('/api/v1/sensorTypes/'+sensorTypeId)
    return sensorType

def getCapability(capabilityId):
    capability = sendGetRequest('/api/v1/capabilities/'+capabilityId)
    return capability

def getSampleValue(dataType, currentIsoTimestamp):
    # matching a sample measurement value to each data type
    # official documentation of supported data types: https://help.sap.com/docs/SAP_IoT/226d46a15bb245b7bf8126604bd6f0fb/9c7273450a874772ad2db007ce212a79.html?locale=en-US#loio2b5ac1ae2bf843d691ed763a96b10712
    match dataType:
        case 'integer':
            return 42
        case 'long':
            return 314159265359
        case 'float':
            return 1234567.75
        case 'double':
            return 123456789012.75234
        case 'boolean':
            return True
        case 'string':
            return 'Sample String'
        case 'binary':
            return 'Binary content as Base64-encoded string'
        case 'date': 
            return currentIsoTimestamp
        case _:        
            return 'Error - Unknown Data Type'

def getFullSamplePayload(selectedDeviceId):

    device = getDevice(selectedDeviceId)
    payload = []
    currentIsoTimestamp = datetime.datetime.utcnow().isoformat()

    # continue with list of sensors assigned to selected device
    if 'sensors' in device: # there are sensors assigned to the device
        sensors = device['sensors']

        print('\nIterating over all sensors of selected device ...')
        for sensor in tqdm(sensors, desc='Sensors'):
            sensorType = getSensorType(sensor['sensorTypeId'])

            # continue with list of capabilities assigned to sensorType of current sensor
            capabilities = sensorType['capabilities']
            for capability in capabilities:
                if capability['type'] == 'measure':  # skip 'command' capabilities as we don't need them as part of the measure payload
                    capabilityDetails = getCapability(capability['id'])
                    capabilityPayloadObject = {}
                    capabilityPayloadObject['sensorAlternateId'] = sensor['alternateId']
                    capabilityPayloadObject['capabilityAlternateId'] = capabilityDetails['alternateId']
                    capabilityPayloadObject['timestamp'] = currentIsoTimestamp
                    capabilityPayloadObject['measures'] = []

                    # continue with list of properties assigned to current capability
                    properties = capabilityDetails['properties']
                    measuresPayloadObject = {}
                    for property in properties:
                        # remove timestamp from outer structure in case there is a property of type 'date' in the inner structure which will act as the timestamp (see https://help.sap.com/docs/SAP_IoT/226d46a15bb245b7bf8126604bd6f0fb/755de2516dde4fafb446efaaafb2c81a.html)
                        if property['dataType'] == 'date':
                            del capabilityPayloadObject['timestamp']

                        # get generated sample measurement value for current property
                        measurement = getSampleValue(property['dataType'], currentIsoTimestamp)
                        measuresPayloadObject[property['name']] = measurement
                    capabilityPayloadObject['measures'].append(measuresPayloadObject)
                    payload.append(capabilityPayloadObject)

        return json.dumps(payload, indent=4) # JSON pretty-printing
    else: # there are no sensors assigned to the device
        return 'Stopping - No sensors have been assigned to selected device\n'

def writePayloadFile(samplePayload):
    with open("payload.json", "w") as text_file:
        print(samplePayload, file=text_file)
        print('\nSample payload has been written to file "payload.json".\n')


## Main program starts here

# Step 1: Prompt user to select location of service key file
serviceKeyFileName = input('\nPlease enter the full file name of your service key file, stored in the current directory (e.g. "SAP IOT Service Key.txt") ==>  ')
#TODO handle possible error cases

deviceConnectivityUrl, authenticationUrl, clientId, clientSecret, scopeRead, scopeCrud = readServiceKey(serviceKeyFileName)

# Step 2: Let user select one device out of a list of retrieved devices

accessToken = getAccessToken(scopeRead)
devices = getDevices()
print('\nFollowing Devices have been found:')

devicesTable = PrettyTable(['Line No.','Device Name', 'Device Alternate ID', 'Device ID'])
for index, device in enumerate(devices):
    devicesTable.add_row([index+1,device['name'],device['alternateId'],device['id']]) # index+1 such that displayed lines start with 1 instead of 0
print(devicesTable)

lineNo = input('\nPlease enter the Line No. of the device for which you would like to generate a sample payload ==>  ')
#TODO handle possible error cases

print('\nSelected device:')
print(devicesTable[int(lineNo)-1]) # line input -1 to reflext correct index because displayed lines start with 1
selectedDevice = devices[int(lineNo)-1]

# Step 4: Generate and print full blown sample payload for selected device
accessToken = getAccessToken(scopeRead) # update access token as a precaution since old token may have expiered in case user took very long time to finish their input
samplePayload = getFullSamplePayload(selectedDevice['id'])
print('\n',samplePayload)

#TODO Step 5: Allow user to modify generated sample payload

#TODO Step 6a: Allow user to manually send edited/original sample payload to selected device
## If no credentails for router device assigend to affected Gateway are present: Offer user to automatically create a new router device for affected Gateway and store router device details incl. client certificate for later reuse
## Send payload for selected device via newly created/existing router device

# Step 6b: Write sample payload to file
writePayloadFile(samplePayload)