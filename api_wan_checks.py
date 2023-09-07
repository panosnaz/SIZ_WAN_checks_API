# ---------------------------------------------------------------------------------------------------
#
#            Network Health Check API Script using Python3, JSON and Power Automate
#
# This script performs various health checks on network devices using Netmiko library and Flask. 
# It connects to the devices, retrieves relevant information, and performs checks related to 
# interface status, ping connectivity, BGP routing, and more.
# 
# The JSON POST request to the API endpoint can be made by using Postman or Power Automate, 
# to the request URL: http://localhost:5000/wanchecks/.
# ---------------------------------------------------------------------------------------------------

from datetime import datetime
from netmiko import ConnectHandler
import re
from termcolor import cprint
from flask import Flask, request, jsonify
import json
from config import username, password

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# bgp neighbors for Aplos & PSD asymmetros based on provider
ote_bgp_neighbor = '83.235.1.100'
wind_bgp_neighbor = "172.24.63.225"
wind_bgp_v6_neighbor = "2A10:D000:60:10::225"
nova_bgp_neighbor = "172.26.255.211"
nova_bgp_v6_neighbor = "2A10:D000:40:0:172:26:255:211"
vodafone_bgp_neighbor = "172.28.255.255"
vodafone_bgp_v6_neighbor = "2A10:D000:FF:FFFF::1"

# Current time and formats it to "Year/Month/Day__Time".
timestamp_format = "%Y-%m-%d %H_%M"
timestamp = datetime.now().strftime(timestamp_format)

app = Flask(__name__)

# Create a list to hold the threads
threads = []

# inteface tests 
def def_int_checks(tenant_type, device, net_connect):
    #with ConnectHandler(**device) as net_connect:  
    interface_results = []
    interface_list = []
    interface_outputs = []
    valid_interfaces = []
    INTERFACE_REPORT = "OK"  # Assume all interfaces are UP

    # check interface data vlan 3000 status, for all tenants except for ΠΣΔ Ασυμμετρος 
    if tenant_type == "APLOS":
        interface_list = ['vlan3000', 'vlan3100']
    elif tenant_type == "PSD":
        interface_list = ['vlan3000']
    elif tenant_type == "MMM":
        interface_list = ['vlan3000']
        # check whether tenant belongs to EFKA 
        output = net_connect.send_command('show interface vlan200')
        if 'Invalid input detected' not in output:
            interface_list.append('vlan200')
    
    # Check if interfaces exist before checking their status
    for interface in interface_list:
        output = net_connect.send_command(f'show ipv6 interface {interface}')
        if 'Invalid input detected' not in output:
            valid_interfaces.append(interface)
    
    # Check the status of valid interfaces
    for interface in valid_interfaces:
        interface_output = net_connect.send_command(f'show ipv6 interface {interface}')
        interface_outputs.append(interface_output + "\n")
        
        if 'line protocol is up' in interface_output:
            cprint(f'{interface} is UP', "green")
            interface_results.append(f"interface {interface} is UP")
        else:
            cprint(f'{interface} is down', "red")
            interface_results.append(f"interface {interface} is down")
            INTERFACE_REPORT = "FAIL"
        
    return interface_list, interface_results, interface_outputs, INTERFACE_REPORT

# PING tests
def def_ping_checks(device, net_connect, interface_list, tenant_type):
 # Initialize the variables with default values
    Lo0_ping_output = ""        
    vlan200_ping_output = ""
    vlan3000_ping_output = ""
    vlan3100_ping_output = ""
    
    #with ConnectHandler(**device) as net_connect:

    # Define the list of hosts to ping
    data_vlan_hosts = {
        "DC1_NTPv4": "84.205.218.190",
        "DC2_NTPv4": "84.205.219.190",
        "DC2_device_DNSv4": "84.205.219.141",
        "DC1_NTPv6": "2A10:D000:14:600::3E",
        "DC2_NTPv6": "2A10:D000:1C:600::3E"
    }
    voice_vlan_hosts = {
        "DC1_NTPv6": "2A10:D000:14:600::3E",
        "DC2_NTPv6": "2A10:D000:1C:600::3E",
        "DC2_user_DNSv4": "84.205.219.140",
        "Call_Manager_v6_1": "2A10:D000:10:B:C000:0:54CD:D6AB",
        "Call_Manager_v6_2": "2A10:D000:10:B:C000:0:54CD:D6AA"
    }

    # Initialize a list to store the ping_outputs for each host
    Lo0_ping_outputs = []
    Lo0_ping_results = []

    vlan200_ping_outputs = []
    vlan200_ping_results = []

    vlan3000_ping_outputs = []
    vlan3000_ping_results = []

    vlan3100_ping_outputs = []
    vlan3100_ping_results = []
    
    PING_REPORT = "OK"  # Assume all pings are successful initially

    # NTPv4 ping test from Lo0
    # each key in the hosts dictionary is assigned to the variable host_name and each value in the dictionary is assigned to the variable host_ip
    for host_name, host_ip in data_vlan_hosts.items():
        Lo0_ping = f"ping {host_ip} source Lo0"
        Lo0_output = net_connect.send_command(Lo0_ping)
        Lo0_ping_output = Lo0_ping + "\n" + Lo0_output + "\n"
        # Append the Lo0_ping_output to the list
        Lo0_ping_outputs.append(Lo0_ping_output)
        # Check if the ping was successful
        if "Success rate is 100 percent" in Lo0_output or "Success rate is 80 percent" in Lo0_output:
            cprint(f"Ping from Lo0 to {host_name} ({host_ip}): successful","green")
            Lo0_ping_results.append(f"Ping from Lo0 to {host_name} ({host_ip}): successful")
        else:
            cprint(f"Ping from Lo0 to {host_name} ({host_ip}): failed","red")
            Lo0_ping_results.append(f"Ping from Lo0 to {host_name} ({host_ip}): failed")
            PING_REPORT = "FAIL"

    if 'vlan200' in interface_list:
        # NTPv4 ping test from vlan200 - voice vlan
        for host_name, host_ip in voice_vlan_hosts.items():

            vlan200_ping = f"ping {host_ip} source vlan200"
            vlan200_output = net_connect.send_command(vlan200_ping)
            vlan200_ping_output = vlan200_ping + "\n" + vlan200_output + "\n"
            # Append the vlan200_ping_output to the list
            vlan200_ping_outputs.append(vlan200_ping_output)
            # Check if the ping was successful
            if "Success rate is 100 percent" in vlan200_output or "Success rate is 80 percent" in vlan200_output:
                cprint(f"Ping from vlan200 to {host_name} ({host_ip}): successful","green")
                vlan200_ping_results.append(f"Ping from vlan200 to {host_name} ({host_ip}): successful")
            else:
                cprint(f"Ping from vlan200 to {host_name} ({host_ip}): failed","red")  
                vlan200_ping_results.append(f"Ping from vlan200 to {host_name} ({host_ip}): failed")    
                PING_REPORT = "FAIL"             
        
    elif 'vlan3100' in interface_list:
        # NTPv4 ping test from vlan3100 - voice vlan
        for host_name, host_ip in voice_vlan_hosts.items():

            # the vlan3100_ping test will only be performed for IPv6 addresses when the tenant_type is "APLOS"
            if tenant_type == "APLOS":
                if "v6" in host_name:  # Checking if it's an IPv6 address
                    vlan3100_ping_v6 = f"ping {host_ip} source vlan3100"
                    vlan3100_output_v6 = net_connect.send_command(vlan3100_ping_v6)
                    vlan3100_ping_output_v6 = vlan3100_ping_v6 + "\n" + vlan3100_output_v6 + "\n"
                    # Append the vlan3100_ping_output_v6 to the list
                    vlan3100_ping_outputs.append(vlan3100_ping_output_v6)
                    # Check if the ping was successful
                    if "Success rate is 100 percent" in vlan3100_output_v6 or "Success rate is 80 percent" in vlan3100_output_v6:
                        cprint(f"Ping from vlan3100 to {host_name} ({host_ip}): successful","green")
                        vlan3100_ping_results.append(f"Ping from vlan3100 to {host_name} ({host_ip}): successful")
                    else:
                        cprint(f"Ping from vlan3100 to {host_name} ({host_ip}): failed","red")
                        vlan3100_ping_results.append(f"Ping from vlan3100 to {host_name} ({host_ip}): failed")
                        PING_REPORT = "FAIL"
                continue

            vlan3100_ping = f"ping {host_ip} source vlan3100"
            vlan3100_output = net_connect.send_command(vlan3100_ping)
            vlan3100_ping_output = vlan3100_ping + "\n" + vlan3100_output + "\n"
            # Append the vlan3000_ping_output to the list
            vlan3100_ping_outputs.append(vlan3100_ping_output)
            # Check if the ping was successful
            if "Success rate is 100 percent" in vlan3100_output or "Success rate is 80 percent" in vlan3100_output:
                cprint(f"Ping from vlan3100 to {host_name} ({host_ip}): successful","green")
                vlan3100_ping_results.append(f"Ping from vlan3100 to {host_name} ({host_ip}): successful")
            else:
                cprint(f"Ping from vlan3100 to {host_name} ({host_ip}): failed","red")
                vlan3100_ping_results.append(f"Ping from vlan3100 to {host_name} ({host_ip}): failed")
                PING_REPORT = "FAIL"

            
        # Απλος Ασυμμετρος
        if tenant_type == "APLOS":
            # NTPv4 ping test from vlan3000 - data vlan
            for host_name, host_ip in data_vlan_hosts.items():
        
                vlan3000_ping = f"ping {host_ip} source vlan3000"
                vlan3000_output = net_connect.send_command(vlan3000_ping)
                vlan3000_ping_output = vlan3000_ping + "\n" + vlan3000_output + "\n"
                # Append the vlan3000_ping_output to the list
                vlan3000_ping_outputs.append(vlan3000_ping_output)
                # Check if the ping was successful
                if "Success rate is 100 percent" in vlan3000_output or "Success rate is 80 percent" in vlan3000_output:
                    cprint(f"Ping from vlan3000 to {host_name} ({host_ip}): successful","green")
                    vlan3000_ping_results.append(f"Ping from vlan3000 to {host_name} ({host_ip}): successful")
                else:
                    cprint(f"Ping from vlan3000 to {host_name} ({host_ip}): failed","red")    
                    vlan3000_ping_results.append(f"Ping from vlan3000 to {host_name} ({host_ip}): failed")
                    PING_REPORT = "FAIL"

    # split and return the ping_outputs and ping_results
    return (
        #[output.splitlines() for output in Lo0_ping_results],
        PING_REPORT,
        Lo0_ping_results,
        Lo0_ping_outputs, 
        vlan200_ping_results, 
        vlan200_ping_outputs, 
        vlan3000_ping_results, 
        vlan3000_ping_outputs,
        vlan3100_ping_results,
        vlan3100_ping_outputs,
    )
                
# BGP checks
def asym_bgp_checks(device, provider, net_connect):
    bgp_results = []
    bgp_neighbor_output_ = []
    BGP_REPORT = "OK"   # Assume all BGP neighborships are UP

    if provider == "OTE":
        ipv4_neighbor = ote_bgp_neighbor
        ipv6_neighbor = ote_bgp_neighbor # v6 over v4 neighbor
    elif provider == "WIND":
        ipv4_neighbor = wind_bgp_neighbor
        ipv6_neighbor = wind_bgp_v6_neighbor
    elif provider == "NOVA":
        ipv4_neighbor = nova_bgp_neighbor
        ipv6_neighbor = nova_bgp_v6_neighbor
    elif provider == "VODAFONE":
        ipv4_neighbor = vodafone_bgp_neighbor
        ipv6_neighbor = vodafone_bgp_v6_neighbor
    
    # check BGPv4 status
    v4_neighbor_command = f'show ip bgp neighbor {ipv4_neighbor}\n'
    bgp_output = net_connect.send_command(v4_neighbor_command)
    bgp_neighbor_output_.append(bgp_output + "\n")
    
    if "Established" in bgp_output:
        cprint(f"BGP v4 neighbor {ipv4_neighbor} Established", "green")
        bgp_results.append(f"BGP v4 neighbor {ipv4_neighbor} Established")
    else:
        cprint(f"BGP v4 neighbor {ipv4_neighbor} not found", "red")
        BGP_REPORT = "FAIL"
    
    # check BGPv6 status 
    v6_neighbor_command = ('show bgp ipv6 unicast neighbors\n')
    bgp_output = net_connect.send_command(v6_neighbor_command)
    bgp_neighbor_output_.append(bgp_output + "\n")
    
    if "Established" in bgp_output:
        cprint(f"BGP v6 neighbor {ipv6_neighbor} Established", "green")
        bgp_results.append(f"BGP v6 neighbor {ipv6_neighbor} Established")
    else:
        cprint(f"BGP v6 neighbor {ipv6_neighbor} not found", "red")
        BGP_REPORT = "FAIL"

    # check BGP routes
    with ConnectHandler(**device) as net_connect:
        command1 = f'\n\nshow ip bgp neighbors {ipv4_neighbor} received-routes\n'
        out1 = net_connect.send_command(command1, expect_string=r'\*>')
        if ipv4_neighbor not in out1:
            cprint(f"Error: ipv4 BGP neighbor {ipv4_neighbor} not found","red")
            bgp_results.append(f"BGP neighbor {ipv4_neighbor} not found")
            BGP_REPORT = "FAIL"
        output1_list = out1.split('\n')
        bgp_neighbor_output_.append(command1)
        for line in output1_list:
            bgp_neighbor_output_.append(line)
            if line.startswith('*>') and output1_list.index(line) >= 50:
                break
    with ConnectHandler(**device) as net_connect:
        command2 = f'\n\nshow ip bgp neighbors {ipv4_neighbor} advertised-routes\n'
        out2 = net_connect.send_command(command2, expect_string=r'\*>')
        output2_list = out2.split('\n')
        bgp_neighbor_output_.append(command2)
        for line in output2_list:
            bgp_neighbor_output_.append(line)
            if line.startswith('*>') and output2_list.index(line) >= 50:
                break
    with ConnectHandler(**device) as net_connect:
        command3 = f'\n\nshow bgp ipv6 unicast neighbors {ipv6_neighbor} received-routes\n'             
        out3 = net_connect.send_command(command3, expect_string=r'\*>')
        output3_list = out3.split('\n')
        bgp_neighbor_output_.append(command3)
        for line in output3_list:
            bgp_neighbor_output_.append(line)
            if line.startswith('*>') and output3_list.index(line) >= 50:
                break
    with ConnectHandler(**device) as net_connect:
        command4 = f'\n\nshow bgp ipv6 unicast neighbors {ipv6_neighbor} advertised-routes\n'
        out4 = net_connect.send_command(command4, expect_string=r'\*>')
        output4_list = out4.split('\n')
        bgp_neighbor_output_.append(command4)
        for line in output4_list:
            bgp_neighbor_output_.append(line)
            if line.startswith('*>') and output4_list.index(line) >= 50:
                break
    bgp_neighbor_output = '\n'.join(bgp_neighbor_output_)

    return bgp_results, bgp_neighbor_output, BGP_REPORT

# MMM Checks
def mmm_bgp_checks(device, bgp_neighbor, net_connect):
    print(f"BGP neighbor(s): {bgp_neighbor}")  

    #with ConnectHandler(**device) as net_connect:
    bgp_results = []
    bgp_neighbor_output = []
    BGP_REPORT = "OK"   # Assume all BGP neighborships are UP

    # split into individual addresses
    bgp_neighbors = bgp_neighbor.split(',')
    cprint(f"List of BGP neighbor IP addresses: {bgp_neighbors}", "yellow")
    # remove any whitespace characters
    bgp_neighbors = [n.strip() for n in bgp_neighbors]
    #bgp_neighbors = bgp_neighbors.replace(" ", "").split(",")
    
    for neighbor in bgp_neighbors:
        command = f'show ip bgp neighbor {neighbor}\n'
        cprint(command, "green")
        bgp_output = net_connect.send_command(command)
        bgp_neighbor_output.append(bgp_output + "\n")
        
        # Check the status of the neighbors
        if "No such neighbor" in bgp_output:
            cprint(f"BGP neighbor {neighbor} not found", "red")
            bgp_results.append(f"BGP neighbor {neighbor} not found")
            BGP_REPORT = "FAIL"
        else:
            for line in bgp_output.split("\n"):
                if "BGP state" in line:
                    if "Idle" in line:
                        cprint(f"BGP neighbor {neighbor} is Idle", "red")
                        bgp_results.append(f"BGP neighbor {neighbor} is Idle")
                        BGP_REPORT = "FAIL"
                    elif "Established" in line:
                        cprint(f"BGP neighbor {neighbor} is Established", "green")
                        bgp_results.append(f"BGP neighbor {neighbor} is Established")
                    else:
                        cprint(line.strip())
                        BGP_REPORT = "FAIL"
        
        # clear the output buffer to avoid caching/buffering issues
        net_connect.clear_buffer()
    cprint("Completed BGP checks", "green")

    return bgp_results, '\n'.join(bgp_neighbor_output), BGP_REPORT

def device_login(device_ip):   
    device = {
        "device_type": "cisco_ios",
        "ip": device_ip,
        "username": username,
        "password": password
    }
    # Connect to the device using Netmiko
    try:
        net_connect = ConnectHandler(**device)
        hostname = net_connect.find_prompt()[:-1] 
        cprint(f"Successfully connected to {device_ip}", 'green')
        return net_connect, hostname, device      
    
    except Exception as e:
        cprint(f"Failed to connect to {device_ip}", 'red')
        cprint(str(e), 'red')
        return

def main(tenant_type, device, hostname, net_connect, provider, bgp_neighbor):
    LICENSE_REPORT = "OK" 

    # Extract S/N & image
    output = net_connect.send_command("show version")
    serial_number_match = re.search(r"Processor board ID\s+(\S+)", output)
    system_image_match = re.search(r"System image file is \"bootflash:(\S+)\"", output)
    if serial_number_match and system_image_match:
        serial_number = serial_number_match.group(1)
        system_image = system_image_match.group(1)
        print("Serial number: ", end='')
        cprint(serial_number, 'yellow')
        print("System image: ", end='')
        cprint(system_image, 'yellow')
    else:
        cprint("Unable to find serial number and/or system image","red")

    # Extract license status
    license_command = 'show license status'
    license_output = net_connect.send_command("show license status")

    if "Trust Code Installed: <none>" in license_output:
        cprint("Error: Trust Code not installed", "red")
        LICENSE_REPORT = "FAIL"
    else:
        match = re.search(r"Trust Code Installed:\s+(\S+ \S+ \S+ \S+ \S+)", license_output)
        if match:
            trust_code = match.group(1)
            print("License: ", end='')
            cprint(f"Trust Code Installed: {trust_code}", "green") 
            license_status = (f"Trust Code Installed: {trust_code}")   
        else:
            cprint("Error: Failed to extract Trust Code", "red")
            license_status = "Failed to extract Trust Code"

    # Call below functions
    # capture the interface_list return value of def_int_checks and pass it as an argument to def_ping_checks.
    interface_list, interface_results, interface_outputs, INTERFACE_REPORT = def_int_checks(tenant_type, device, net_connect)
    PING_REPORT, Lo0_ping_results, Lo0_ping_outputs, vlan200_ping_results, vlan200_ping_outputs, vlan3000_ping_results, vlan3000_ping_outputs, vlan3100_ping_results, vlan3100_ping_outputs  = def_ping_checks(device, net_connect, interface_list, tenant_type)
    if tenant_type == "MMM":
        bgp_results, bgp_neighbor_output, BGP_REPORT = mmm_bgp_checks(device, bgp_neighbor, net_connect)
    else:
        bgp_results, bgp_neighbor_output, BGP_REPORT = asym_bgp_checks(device, provider, net_connect)

    json_return_output = {
        "tenant_type": tenant_type,
        "provider": provider,        
        "serial_number": serial_number,
        "system_image": system_image,
        "bgp_neighbor": bgp_neighbor,
        "PING_REPORT": PING_REPORT,
        "INTERFACE_REPORT": INTERFACE_REPORT,
        "LICENSE_REPORT": LICENSE_REPORT,
        "BGP_REPORT": BGP_REPORT,

        "interface_results": "\n".join(interface_results),
        "interface_outputs": "\n".join(interface_outputs),

        "license_results": license_status,
        "license_output": license_command + "\n" + license_output,

        # Convert array to separate lines
        "Lo0_ping_results": "\n".join(Lo0_ping_results),  
        "vlan200_ping_results": "\n".join(vlan200_ping_results),
        "vlan3000_ping_results": "\n".join(vlan3000_ping_results),
        "vlan3100_ping_results":"\n".join(vlan3100_ping_results),

        "Lo0_ping_outputs": "\n".join(Lo0_ping_outputs),
        "vlan200_ping_outputs":"\n".join(vlan200_ping_outputs),
        "vlan3000_ping_outputs": "\n".join(vlan3000_ping_outputs),
        "vlan3100_ping_outputs":"\n".join(vlan3100_ping_outputs),

        "bgp_results": "\n".join(bgp_results),
        "bgp_neighbor_output": bgp_neighbor_output
    }
    return json_return_output



AUTH_TOKEN = "d94cb90ee88b7631001f06d3658132d3"

@app.route('/wanchecks/', methods=['POST'])
def run_health_checks():
    # Check if the 'Authorization' header is present in the request
    if 'Authorization' not in request.headers:
        return jsonify({"error": "Authorization header missing"}), 401

    # Get the token from the 'Authorization' header
    provided_token = request.headers.get('Authorization')

    # Check if the provided token matches the expected token
    if provided_token != AUTH_TOKEN:
        return jsonify({"error": "Invalid authorization token"}), 401

    # The token is valid, proceed with processing the request
    post_data = request.json
    device_ip = post_data['device_ip']
    tenant_type = post_data['tenant_type']
    provider = post_data['provider']
    bgp_neighbor = post_data['bgp_neighbor']
    device_ip = request.json.get('device_ip')
    #tenant_type = request.json.get('tenant_type')

    # Connect to the device
    net_connect, hostname, device = device_login(device_ip)
    if hostname is None:
        return jsonify({"response": f"Failed to connect to {device_ip}"}), 400

   # Execute show run command
    show_run_output = net_connect.send_command("show run")

    json_return_output = main(tenant_type, device, hostname, net_connect, provider, bgp_neighbor)
    # Close the SSH connection after all checks are performed
    net_connect.disconnect()

    response_data = {
        "hostname": hostname,
        "device_ip": device_ip,
        'json_return_output': json_return_output,
        'show_run_output': show_run_output
    }

    # Manually construct the JSON response
    response_json = json.dumps(response_data, indent=4)
    # send the JSON response data, the status code, and the headers to the client making the HTTP request.
    return response_json, 200, {'Content-Type': 'application/json'}
        

if __name__  == '__main__':
    print("Starting Flask application...")
    app.debug = True
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=80)
