import datetime
import json
import requests
from prettytable import PrettyTable
from tqdm import tqdm

def readServiceKey(serviceKeyFileName):
    with open(serviceKeyFileName) as serviceKeyFile:
        serviceKey = json.load(serviceKeyFile)
        deviceConnectivityUrl = serviceKey['endpoints']['iot-device-connectivity']
        modelMappingUrl = serviceKey['endpoints']['i4c-model-mapping-sap']
        authenticationUrl = serviceKey['uaa']['url']
        clientId = serviceKey['uaa']['clientid']
        clientSecret = serviceKey['uaa']['clientsecret']
        scopeDcRead = serviceKey['uaa']['clientid'].split('|')[1]+'.dc.r'
        scopeDcAmRead = serviceKey['uaa']['clientid'].split('|')[1]+'.dc.r'+' '+'iotas!t'+serviceKey['uaa']['clientid'].split('|')[1].split('!')[1][1:]+'.am.map.r'
        scopeDcCrud = serviceKey['uaa']['clientid'].split('|')[1]+'.dc.cud'+' '+serviceKey['uaa']['clientid'].split('|')[1]+'.dc.r'
        return deviceConnectivityUrl, modelMappingUrl, authenticationUrl, clientId, clientSecret, scopeDcRead, scopeDcAmRead, scopeDcCrud

def getAccessToken(scope):
    url = authenticationUrl+'/oauth/token'
    response = requests.post(url=url, data={'grant_type': 'client_credentials', 'response_type': 'token', 'client_id': clientId, 'client_secret': clientSecret, 'scope': scope})
    return json.loads(response.text)['access_token']

def sendGetRequest(url):
    #TODO: Implement standard handling for OAuth2.0 credential flow
    response = requests.get(url=url, headers={'Authorization': 'Bearer '+accessToken})
    return json.loads(response.text)

def getDevices():
    devices = sendGetRequest(deviceConnectivityUrl+'/api/v1/devices?top=100000') #?top=100000 to overcome the default number of 100 devices that would be returned by the API in case there are more than 100 devices. The number 100000 has been chosen randomly without a particular reason in mind.
    return devices

def getDevice(deviceId):
    device = sendGetRequest(deviceConnectivityUrl+'/api/v1/devices/'+deviceId)
    return device

def getSensor(sensorId):
    sensor = sendGetRequest(deviceConnectivityUrl+'/api/v1/sensors/'+sensorId)
    return sensor

def getSensorType(sensorTypeId):
    sensorType = sendGetRequest(deviceConnectivityUrl+'/api/v1/sensorTypes/'+sensorTypeId)
    return sensorType

def getCapability(capabilityId):
    capability = sendGetRequest(deviceConnectivityUrl+'/api/v1/capabilities/'+capabilityId)
    return capability

def getAssignments():
    #TODO: Expanding Sensors is only a workaround to get all results and not only the top 100. Add selector for Object ID and stop expanding Sensors once possible.
    assignments = sendGetRequest(modelMappingUrl+'/Model/v1/Assignments?$expand=Sensors&$format=json')['d']['results']
    for assignment in assignments:
        del assignment['__metadata']
        del assignment['AssignmentId']
        del assignment['MappingId']
        del assignment['Sensors']
    return assignments

def getAssignment(ObjectId):
    assignment = sendGetRequest(modelMappingUrl+"/Model/v1/Assignments?$filter=ObjectId eq '"+ObjectId+"'&$expand=Sensors&$format=json")['d']['results'][0]
    del assignment['__metadata']
    return assignment

def getMappedMeasures(mappingId):
    mappedMeasures = sendGetRequest(modelMappingUrl+"/Model/v1/Mappings('"+mappingId+"')?$expand=Measures,Measures/PropertyMeasures&$format=json")['d']['Measures']['results']
    return mappedMeasures

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

def getIotSamplePayload(selectedDeviceId):
    payload = []
    currentIsoTimestamp = datetime.datetime.utcnow().isoformat()

    device = getDevice(selectedDeviceId)
    # continue with list of sensors assigned to selected device
    if 'sensors' in device: # there are sensors assigned to the device
        sensors = device['sensors']

        print('\nIterating over all sensors of selected device ...')
        for sensor in tqdm(sensors, desc='Sensors'):
            sensorType = getSensorType(sensor['sensorTypeId'])

            # continue with list of capabilities assigned to sensorType of current sensor
            capabilities = sensorType['capabilities']
            for capability in capabilities:
                if capability['type'] == 'measure':  # only consider 'measure' capabilities as we don't need 'commands' as part of the measure payload
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

def getApmSamplePayload(objectId):
    payload = []
    currentIsoTimestamp = datetime.datetime.utcnow().isoformat()

    assignment = getAssignment(objectId)
    assignedSensors = assignment['Sensors']['results']
    sensors = []

    for assignedSensor in assignedSensors:
        sensor = getSensor(assignedSensor['SensorId'])
        sensors.append(sensor)

    mappingId = assignment['MappingId']
    mappedMeasures = getMappedMeasures(mappingId)
    apmRelevantCapabilities = []

    for mappedMeasure in mappedMeasures:
        apmRelevantCapabilities.append(mappedMeasure['CapabilityId'])

    print('\nIterating over all sensors of selected technical object ...')
    for sensor in tqdm(sensors, desc='Sensors'):
        sensorType = getSensorType(sensor['sensorTypeId'])

        # continue with list of capabilities assigned to sensorType of current sensor
        capabilities = sensorType['capabilities']
        for capability in capabilities:
            if capability['id'] in apmRelevantCapabilities: # only consider APM relevant capabilities
                if capability['type'] == 'measure':  # only consider 'measure' capabilities as we don't need 'commands' as part of the measure payload
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

def writePayloadFile(samplePayload):
    with open("payload.json", "w") as text_file:
        print(samplePayload, file=text_file)
        print('\nSample payload has been written to file "payload.json".\n')

### Main control flow starts here ###

# Step 1: Prompt user to select location of service key file
#TODO handle possible error cases
serviceKeyFileName = input('\nPlease enter the full path incl. file name of your service key file (e.g. "SAP IOT Service Key.txt" in case the service key file is stored in the current directory).\n==>  ')
deviceConnectivityUrl, modelMappingUrl, authenticationUrl, clientId, clientSecret, scopeDcRead, scopeDcAmRead, scopeDcCrud = readServiceKey(serviceKeyFileName)

# Step 2: Ask user if the sample payload is required for APM or IoT standalone usage
#TODO handle possible error cases
apmModeInput = input('\nDo you want to generate a sample payload for Asset Performance Management (APM) or for pure SAP IoT Device Model/standalone usage? \nEnter "apm" for APM mode or "iot" for SAP IoT Device Model/standalone mode. In case you are not sure, enter "iot".\n==> ')

if apmModeInput.lower() in ['apm']:
    apmMode = True
    print('\nAPM mode selected\n')
elif apmModeInput.lower() in ['iot']:
    apmMode = False
    print('\nIoT standalone mode selected')
else:
    apmMode = False
    print('\nNo proper input detected - defaulting to IoT standalone mode')

if apmMode: # Following the APM path (path a) from here on
    # Step 3a: Let user select one technical object based on existing assignments
    accessToken = getAccessToken(scopeDcAmRead)
    assignments = getAssignments()

    if assignments: # There are assignments present in current SAP IoT tenant
        assignmentsTable = PrettyTable(['Line No.','Technical Object ID'])
        for index, assignment in enumerate(assignments):
            assignmentsTable.add_row([index+1,assignment['ObjectId']]) # index+1 such that displayed lines start with 1 instead of 0
        print(assignmentsTable)

        #TODO handle possible error cases        
        lineNo = input('\nPlease enter the Line No. of the Technical Object for which you would like to generate a sample payload.\n==>  ')

        print('\nSelected Technical Object:')
        print(assignmentsTable[int(lineNo)-1]) # line input -1 to reflext correct index because displayed lines start with 1
        selectedAssignment = assignments[int(lineNo)-1]
        
        # Step 4a: Generate and print full blown sample payload for selected technical object
        accessToken = getAccessToken(scopeDcAmRead) # update access token as a precaution since old token may have expired in case user took very long time to finish their input
        samplePayload = getApmSamplePayload(selectedAssignment['ObjectId'])
        print('\n',samplePayload)
        
        #TODO Step 5a: Allow user to modify generated sample payload

        #TODO Step 6a: Allow user to manually send edited/original sample payload to selected technical object
        ## If no credentails for router device assigend to affected Gateway are present: Offer user to automatically create a new router device for affected Gateway and store router device details incl. client certificate for later reuse
        ## Send payload for selected device via newly created/existing router device

        # Step 7a: Write sample payload to file
        writePayloadFile(samplePayload)

    else: # There are no assignments present in current SAP IoT tenant
        print('\nNo assignments have been detected in your SAP IoT tenant. Please consider using IoT standalone mode instead of APM mode.\n')

else: # Following the IoT standalone path (path b) from here on
    # Step 3b: Let user select one device out of a list of retrieved devices
    accessToken = getAccessToken(scopeDcRead)
    devices = getDevices()

    if devices: # There are devices present in current SAP IoT tenant
        print('\nFollowing Devices have been found:')
        devicesTable = PrettyTable(['Line No.','Device Name', 'Device Alternate ID', 'Device ID'])
        for index, device in enumerate(devices):
            devicesTable.add_row([index+1,device['name'],device['alternateId'],device['id']]) # index+1 such that displayed lines start with 1 instead of 0
        print(devicesTable)

        #TODO handle possible error cases
        lineNo = input('\nPlease enter the Line No. of the device for which you would like to generate a sample payload.\n ==>  ')
    
        print('\nSelected device:')
        print(devicesTable[int(lineNo)-1]) # line input -1 to reflext correct index because displayed lines start with 1
        selectedDevice = devices[int(lineNo)-1]

        # Step 4b: Generate and print full blown sample payload for selected device
        accessToken = getAccessToken(scopeDcRead) # update access token as a precaution since old token may have expired in case user took very long time to finish their input
        samplePayload = getIotSamplePayload(selectedDevice['id'])
        print('\n',samplePayload)
        
        #TODO Step 5b: Allow user to modify generated sample payload

        #TODO Step 6b: Allow user to manually send edited/original sample payload to selected device
        ## If no credentails for router device assigend to affected Gateway are present: Offer user to automatically create a new router device for affected Gateway and store router device details incl. client certificate for later reuse
        ## Send payload for selected device via newly created/existing router device

        # Step 7b: Write sample payload to file
        writePayloadFile(samplePayload)

    else: # There are no devices present in current SAP IoT tenant
        print('\nNo devices have been detected in your SAP IoT tenant. Please create your first device to get started.\n')