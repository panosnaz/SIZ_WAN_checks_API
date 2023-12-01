## **Network Health Check API Script using Python3, JSON, and Power Automate** 

This script performs various health checks on network devices using the Netmiko library and Flask.
It is designed to run as an executable (.exe) on a server environment. 
The script connects to the devices, retrieves relevant information, and performs checks related to
interface status, ping connectivity, BGP routing, and more.

The JSON POST requests can be made by using Postman or Power Automate to the URL: http://localhost:5000/wanchecks/
The code always checks the 'Authorization' header upon a POST API call and validates the provided token.
If the header is missing or the provided token doesn't match the expected token (AUTH_TOKEN), the script returns a 401 Unauthorized response.

This script is divided into several functions for different aspects of health checks, including
interface status, ping tests, and BGP checks. Each function is documented to describe its purpose
and usage.

- When a valid POST request is received, the Flask route function `run_health_checks()` is executed.
  The function retrieves the required data from the incoming JSON payload, such as `device_ip`, `tenant_type`, `provider`, and `bgp_neighbor`.

- The `main()` function is responsible for executing various health checks on the network device. It takes parameters such as `tenant_type`, `device`, `hostname`, `net_connect`, `provider`, and `bgp_neighbor`.

- The `main()` function orchestrates the execution of health checks, including interface status checks, ping tests, BGP checks, and license status checks.

- The results of the health checks are stored in a dictionary (`json_return_output`), which includes information about the device, health check results, and other relevant details.

- The Flask response includes the JSON-serialized results, the HTTP status code (200 for successful response), and the content type header.

This architecture allows external systems or tools, such as Power Automate, to send JSON POST requests to the API endpoint. The script processes these requests, performs health checks on the specified network device, and returns the results in JSON format.
Additional steps can be configured to upload TXT health check files to SharePoint using Power Automate and send a notification in Microsoft Teams with a message to notify about the check results.

Below high-level architecture involves the execution of this Python script as an API endpoint, interactions with Power Automate for file uploads to SharePoint, and communication with Teams for notifications. 
This architecture ensures a seamless and automated flow of network health information within the specified environment.

![WAN_checks_API Diagram](https://github.com/panosnaz/SIZ_WAN_checks_API/blob/83fbef1f9af8a1eda2a810d28260e770c11e35a3/WAN%20checks%20API.png)
### **Prerequisites** 

Before running the script, make sure you have the following prerequisites:

- Python 3.x installed
- Required Python packages: netmiko, termcolor, flask
- Access to the network devices you want to perform health checks on
- Postman or Power Automate tool
- Configuration file (config.py) containing the username and password for device authentication

### **Usage** 

1. Clone the script repository:
`https://github.com/panosnaz/SIZ_WAN_checks_API.git`

2. Install the required dependencies:

`pip install -r requirements.txt`

3. Configure the devices and health check parameters in the WAN_checks_API.py file:

- Create a config.py file with the following configurations:
	- username: Your device username.
	- password: Your device password.
	- AUTH_TOKEN: Authorization token for API access.
	- Other necessary configurations for your network.
	
- Update the device_login() function with the appropriate login credentials for your devices or create a config.py file and define there the username and password variables.

4. Use an executable version (.exe) of this script for easy deployment on a server, or start the Flask application by running the following command:

`python WAN_checks_API.py`

5. Send a POST request with appropriate JSON data using tools like Postman or Power Automate:

	- URL: http://localhost:5000/wanchecks/
	- Method: POST
	- Request body: JSON payload containing the required parameters
	- In the Headers section, the Content-Type header value must be set to application/json 
	- Make sure to include the Authorization header with the correct token.

JSON data examples:

`
{
  "device_ip": "192.168.0.1",
  "tenant_type": "MMM",
  "provider": "OTE",
  "bgp_neighbor": "80.80.80.80,90.90.90.90"
}
`

`
{
"device_ip": "172.23.0.1", 
"tenant_type": "APLOS", 
"provider": "OTE",
"bgp_neighbor": ""
}
`

- You will receive a JSON response with the results of the health checks.


6. 
- The script will connect to the specified device, perform health checks, and return a health check report and a show run text files in the json response.
- If tenant is APLOS or PSD, the script runs bgp tests on a pre-defined bgp neighbor IPs. 
- In case of a MMM tenant, the POST API should include the appropriate list of BGP neighbor IPs.
- The code always checks the 'Authorization' header upon a POST API call and validates the provided token. 
- If the 'Authorization' header is present and the provided token matches `AUTH_TOKEN`, the code will proceed with processing the request. 
- Otherwise, it will return a 401 Unauthorized response with an error message.


#### **Important Note**

Security Considerations: 
This script is designed for internal usage. 
The Flask application is set to run on localhost for security reasons. 
If you intend to expose this script publicly, adjust the host and port settings accordingly and implement proper security measures.
	
### **Endpoints**

POST /wanchecks/

This endpoint performs network health checks on the specified network devices.

#### **Request Body**

The request body should be a JSON object with the following parameters:

`tenant_type` (string): The type of tenant (e.g., "APLOS", "PSD", "MMM").

`device_ip` : The login IP address of the network device.

`provider` (string): The network provider (e.g., "OTE", "WIND", "NOVA", "VODAFONE").

`bgp_neighbor` : The IP address of the BGP neighbor for the MMM tenant.


#### **Response**

The API will respond with a JSON object containing below network health check results (among others):

`system_image`: The system image name.

`serial_number` : The serial number.

`license_output` (array): The output of the license checks.

`interface_results` (array): The results of the interface checks.

`interface_outputs` (array): The outputs of the interface checks.

`ping_results` (object): The results of the ping tests for each interface.

`ping_outputs` (object): The outputs of the ping tests for each interface.

`bgp_report` (string): The overall result of the BGP checks ("OK" or "FAIL").

`bgp_results` (array): The results of the BGP checks.

`bgp_neighbor_output` (array): The outputs of the BGP neighbor checks.



### **Detailed Information**

For detailed information on each function and usage, refer to the respective docstrings within the code.

### **Authors** 

Author: Panagiotis Naziroglou

### **Acknowledgments** 

- The script is built using the Netmiko library for SSH connections to network devices.
- The Flask framework (https://flask.palletsprojects.com/) is used for handling HTTP requests and responses.
- The script uses the termcolor library for colorizing console output.