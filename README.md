## **Network Health Check API Script Documentation** 

This script performs various health checks on network devices using the Netmiko library and Flask.
It connects to the devices, retrieves relevant information, and performs checks related to
interface status, ping connectivity, BGP routing, and more.

The JSON POST requests can be made by using Postman or Power Automate to the URL: http://localhost:5000/wanchecks/
The code always checks the 'Authorization' header upon a POST API call and validates the provided token.

This script is divided into several functions for different aspects of health checks, including
interface status, ping tests, and BGP checks. Each function is documented to describe its purpose
and usage.

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
`https://github.com/panosnaz/SIZ_wan_healthchecks.git`

2. Install the required dependencies:

`pip install -r requirements.txt`

3. Configure the devices and health check parameters in the WAN_checks_API.py file:

- Create a config.py file with the following configurations:
	- username: Your device username.
	- password: Your device password.
	- AUTH_TOKEN: Authorization token for API access.
	- Other necessary configurations for your network.
	
- Update the device_login() function with the appropriate login credentials for your devices or create a config.py file and define there the username and password variables.

4. Start the Flask application by running the following command:

`python WAN_checks_API.py`

5. Send a POST request with JSON data using tools like Postman or Power Automate:

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



### **Authors** 

Author: Panagiotis Naziroglou

### **Acknowledgments** 

- The script is built using the Netmiko library for SSH connections to network devices.
- The Flask framework (https://flask.palletsprojects.com/) is used for handling HTTP requests and responses.
- The script uses the termcolor library for colorizing console output.