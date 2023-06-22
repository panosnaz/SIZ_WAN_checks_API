## **Network Health Check Script Documentation** 

This script is designed to perform various health checks on network devices using Netmiko library. 
It connects to the devices, retrieves relevant information, and performs checks related to interface status, ping connectivity, BGP routing, and more. 
The script also includes functionality to upload the generated output to a SharePoint document library.

### **Prerequisites** 

Before running the script, make sure you have the following prerequisites:

- Python 3.x installed
- Required Python packages: netmiko, termcolor, office365
- Access to the network devices you want to perform health checks on
- SharePoint account with necessary permissions to upload files

### **Usage** 

1. Clone the script repository:
`https://github.com/panosnaz/SIZ_wan_healthchecks.git`

2. Install the required Python packages:
`pip install netmiko termcolor office365`

3. Configure the script:

- Update the device dictionary with the connection details of your network devices.
- Modify the IP addresses of the BGP neighbors (ote_bgp_neighbor, wind_bgp_neighbor, etc.) based on your network configuration.
- Customize the ping targets in the hosts and vlan3100_hosts dictionaries.

4. Run the script:
`python wan_checks.py`

- You can specify the provider as "ote", "wind", "nova", or "vodafone" when running the health checks.
- You can specify the tenant_type as "aplos", "psd asymmetros" and "mmm" when running the health checks. 
- The script will generate a health checks output file and a show run file in a directory named after the device hostname.

5. (Optional) To upload the output to SharePoint, update the SharePoint configuration details (sharepoint_url, username, password, sharepoint_folder) and uncomment the def_sharepoint(hostname) function call at the end of the main() function.

### **Script Structure** 

The script is structured as follows:

- Import necessary modules and packages
- Define global variables for BGP neighbors and timestamp format
- Define a function to validate IP addresses
- Define functions for interface checks, ping checks, BGP checks, and SharePoint upload
- Define the main function that orchestrates the health checks
- Execute the main function

### **Authors** 

Author: Panagiotis Naziroglou

### **Acknowledgments** 

- The script utilizes the Netmiko library for network device connectivity and interaction.
- The script uses the termcolor library for colorizing console output.
- SharePoint functionality is enabled using the office365 library.
