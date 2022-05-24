# SIoT Device Payload Generator
__SIoT Device Payload Generator__ is a simple helper tool to generate sample payloads for the Device Connectivity component of SAP® Internet of Things. By looping through existing Device Model artifacts, this payload generator constructs a fully populated payload string for a given Device which can be used for e.g. test and development purposes.

**Important note**: This tool is a private hobby project and therefore not provided or supported by SAP® by any means. SAP® Internet of Things and all other SAP® products mentioned here are commercial products of SAP SE and not part of this project.

## Project status
This hobby project currently (May 2022) is in a very early stage. Many aspects are not finished nor extensively tested yet. As I believe this tool can still provide benefit in its current stage, I decided to already share the preliminary state of development even if there is still quite some room for improvement (see section [Known issues and to dos](#known-issues-and-to-dos)).

## Prerequisites

### SAP® Internet of Things setup
* An SAP® Internet of Things tenant with integrated Device Connectivity feature (= application plan `oneproduct`) has been set up according to [the product documentation](https://help.sap.com/docs/SAP_IoT/195126f4601945cba0886cbbcbf3d364/bfe6a46a13d14222949072bf330ff2f4.html)
* You downloaded a service key for your SAP® Internet of Things tenant in JSON format (see instructions [here](https://help.sap.com/docs/SAP_IoT/195126f4601945cba0886cbbcbf3d364/a41c28db0cf449059d48c23fa5f7b24b.html))
* At least one Device has been created in the Device Connectivity component of your SAP® Internet of Things tenant (either manually or by an SAP® Internet of Things enabled application such as PAI, APM or EPD)

### Installation of dependencies

Please make sure you have an up-to-date version of Python and all required libraries installed.

In particular:
* Install [latest Python version](https://www.python.org/downloads/), but at least a Python version **>=3.10**
* Install dependent Python libraries:
```
~$ py -m pip install requests, prettytable, tqdm
```

## Usage

1. Store the file `payload_generator.py` of this repository on your machine or simply check out the entire repository.
2. Store your SAP® Internet of Things service key in JSON format (see section [Prerequisites](#prerequisites)) in the same folder than `payload_generator.py`. In below example the file name of this service key is `SAP IOT Service Key.txt`.Alternatively lookup the full path to you service key file.
3. Run the Python program `payload_generator.py` on your command line and follow the instructions displayed (see examples below).
4. Use the generated sample payload (either from the command line output or from the newly created file `payload.json`) as a basis for sending messages to SAP® Internet of Things Device Connectivity using your favourite MQTT or HTTP client (see [official product documentation](https://help.sap.com/docs/SAP_IoT/226d46a15bb245b7bf8126604bd6f0fb/97854de9e5dd41c191db6aa65394e461.html) for more details).

 ### Example 1 - APM usage
```
 ~$ py payload_generator.py

Please enter the full path incl. file name of your service key file (e.g. "SAP IOT Service Key.txt" in case the service key file is stored in the current directory).
==>  SAP IOT Service Key.txt

Do you want to generate a sample payload for Asset Performance Management (APM) or for pure SAP IoT Device Model/standalone usage?
Enter "apm" for APM mode or "iot" for SAP IoT Device Model/standalone mode. In case you are not sure, enter "iot".
==> apm

APM mode selected

+----------+------------------------+
| Line No. |  Technical Object ID   |
+----------+------------------------+
|     1    |       E_10000024       |
|     2    |       E_10000000       |
|     3    |       E_20000502       |
|     4    |       E_10000004       |
+----------+------------------------+

Please enter the Line No. of the Technical Object for which you would like to generate a sample payload.
==>  1

Selected Technical Object:
+----------+---------------------+
| Line No. | Technical Object ID |
+----------+---------------------+
|    1     |      E_10000024     |
+----------+---------------------+

Iterating over all sensors of selected technical object ...
Sensors: 100%|█████████████████████████████████████████████████| 2/2 [00:02<00:00,  1.21s/it]

 [
    {
        "sensorAlternateId": "C",
        "capabilityAlternateId": "P_ML2",
        "timestamp": "2022-05-23T07:01:19.492312",
        "measures": [
            {
                "MP_FLOWRATE": 123456789012.75233
            }
        ]
    },
    {
        "sensorAlternateId": "M",
        "capabilityAlternateId": "P_CML",
        "timestamp": "2022-05-23T07:01:19.492312",
        "measures": [
            {
                "MP_THICKNESS": 123456789012.75233,
                "MP_SH_THICKNESS": 123456789012.75233
            }
        ]
    }
]

Sample payload has been written to file "payload.json".

```

### Example 2 - SAP IoT standalone usage
```
 ~$ py payload_generator.py

Please enter the full path incl. file name of your service key file (e.g. "SAP IOT Service Key.txt" in case the service key file is stored in the current directory).
==>  SAP IOT Service Key.txt

Do you want to generate a sample payload for Asset Performance Management (APM) or for pure SAP IoT Device Model/standalone usage?
Enter "apm" for APM mode or "iot" for SAP IoT Device Model/standalone mode. In case you are not sure, enter "iot".
==> iot

IoT standalone mode selected

Following Devices have been found:
+----------+-----------------------+----------------------+--------------------------------------+
| Line No. |      Device Name      |  Device Alternate ID |              Device ID               |
+----------+-----------------------+----------------------+--------------------------------------+
|    1     |  Temperate Device 1   | temperature_device_1 | bac6e52e-ce06-9459-8534-57f94c47aadb |
|    2     |  My Test Router MQTT  |   test_router_mqtt   | a354a583-d2ab-3467-a24c-42ca47f9c044 |
|    3     | Location Tracker 4711 |   loc_tracker_4711   | 4669baae-d3ba-4635-a7f4-c256151b21ce |
+----------+-----------------------+----------------------+--------------------------------------+

Please enter the Line No. of the device for which you would like to generate a sample payload. ==>  1

Selected device:
+----------+--------------------+----------------------+--------------------------------------+
| Line No. |     Device Name    | Device Alternate ID  |              Device ID               |
+----------+--------------------+----------------------+--------------------------------------+
|     1    | Temperate Device 1 | temperature_device_1 | bac6e52e-ce06-9459-8534-57f94c47aadb |
+----------+--------------------+----------------------+--------------------------------------+

Iterating over all sensors of selected device ...
Sensors: 100%|███████████████████████████████████████████████████████| 3/3 [00:10<00:00,  1.77s/it]

 [
    {
        "sensorAlternateId": "62c645ea-ed77-42ba-b675-5fd5b6a5d1ae",
        "capabilityAlternateId": "5265a838-f288-446d-a5a5-d83a7430312a",
        "timestamp": "2022-04-07T19:49:06.737183",
        "measures": [
            {
                "temperature": 1234567.75,
                "humidity": 1234567.75
            }
        ]
    },
    {
        "sensorAlternateId": "f447d145-6626-4113-b7f9-2098ba53fb72",
        "capabilityAlternateId": "5265a838-f288-446d-a5a5-d83a7430312a",
        "timestamp": "2022-04-07T19:49:06.737183",
        "measures": [
            {
                "temperature": 1234567.75,
                "humidity": 1234567.75
            }
        ]
    },
    {
        "sensorAlternateId": "1d3a9e49-80ae-4e72-9cb3-0ffa0756a9a5",
        "capabilityAlternateId": "5265a838-f288-446d-a5a5-d83a7430312a",
        "timestamp": "2022-04-07T19:49:06.737183",
        "measures": [
            {
                "temperature": 1234567.75,
                "humidity": 1234567.75
            }
        ]
    }
]

Sample payload has been written to file "payload.json".

```

## Known issues and to dos
- [X] Automatically extract all relevant connection details from service key file
- [ ] Perform proper development testing incl. all possible Device Model state edge cases and all possible data types
- [ ] Review and improve payload generation logic of APM mode / consolidate into common flow to reduce code
- [ ] Rework OAuth2.0 credential flow
- [ ] Add proper user input validation
- [ ] Add proper exception handling
- [ ] Optimize performance by reducing number of API calls
- [ ] Allow passing service key file as command line input parameter
- [ ] Adjust overall logic to specifically handle model abstraction mappings to better support usage along with e.g. SAP® Asset Performance Management (APM)
- [ ] Show progress bar per capability instead of per sensor
- [ ] Add a built-in MQTT and/or HTTP client to not only generate sample payloads but also offer the option to send the payload right away (using a Router Device)
- [ ] Add a GUI
- [ ] Add option to enter target deviceId or alternateId directly in addition to selecting from a list of available devices
- [ ] Generate randomized sample values
- [ ] Make resulting payload structure configurable
- [ ] Add unit tests

## Built with
* [Requests](https://docs.python-requests.org)
* [PrettyTable](https://pypi.org/project/prettytable)
* [tqdm](https://github.com/tqdm/tqdm)

## Contributions
Any contributions are highly appreciated. You can create an issue for any bugs, questions and improvement requests or simply submit your own improvements via pull request.

Please don't forget to give a ⭐️ if you like this hobby project.

## License
This tool is distributed under the GNU GPL v3 license. See LICENSE for more information.