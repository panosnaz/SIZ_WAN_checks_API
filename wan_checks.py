# ---------------------------------------------------------------------------------------------------
#
#            Network Health Check Script using Python3
#
# This script is designed to perform various health checks on network devices using Netmiko library. 
# It connects to the devices, retrieves relevant information, and performs checks related to interface status, ping connectivity, BGP routing, and more. 
# The script also includes functionality to upload the generated output to a SharePoint document library.
#
# ---------------------------------------------------------------------------------------------------


from datetime import date, datetime
from netmiko import ConnectHandler, NetmikoTimeoutException
import os
import re
from termcolor import cprint
os.system('cls') 
from config import username, password
#import logging
#logging.basicConfig(filename='debug.log', level=logging.DEBUG)
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file_creation_information import FileCreationInformation

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


def validate_ip_address(ip_address):
    """Validate whether a given string is a valid IP address."""
    pattern = re.compile(r"^(([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.){3}([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])$")
    return bool(pattern.match(ip_address))

    # inteface tests 
def def_int_checks(Healthchecks_file):
    with ConnectHandler(**device) as net_connect:
        with open(Healthchecks_file, 'a') as f:
            # check interface data vlan 3000 status, for all tenants except for ΠΣΔ Ασυμμετρος 
            interface_list = []
            if tenant_type == "1":
                interface_list = ['vlan3000', 'vlan3100']  
            elif tenant_type == "2":
                interface_list = ['vlan3000']
            elif tenant_type == "3":
                interface_list = ['vlan3000']
                # check whether tenant belongs to EFKA 
                output = net_connect.send_command('show interface vlan200')
                if 'Invalid input detected' not in output:
                    interface_list.append('vlan200')
            valid_interfaces = []
            f.write(f"\nINTERFACE CHECKS\n################\n\n")

            # Check if interfaces exist before checking their status
            for interface in interface_list:
                output = net_connect.send_command(f'show ipv6 interface {interface}')
                if 'Invalid input detected' not in output:
                    valid_interfaces.append(interface)
            f.write(f"\nINTERFACE CHECKS\n################\n\n")

            # Check the status of valid interfaces
            for interface in valid_interfaces:
                output = net_connect.send_command(f'show ipv6 interface {interface}')
                if 'line protocol is up' in output:
                    cprint(f'{interface} is UP', "green")
                else:
                    cprint(f'{interface} is down', "red")
                f.write(output + '\n\n')

        return interface_list
    
    # PING tests
def def_ping_checks(interface_list, tenant_type, Healthchecks_file):
    with ConnectHandler(**device) as net_connect:

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
        # NTPv4 ping test from Lo0
        with open(Healthchecks_file, 'a') as f:
            f.write(f"\nPING CHECKS\n############\n\n")
            # each key in the hosts dictionary is assigned to the variable host_name and each value in the dictionary is assigned to the variable host_ip
            for host_name, host_ip in data_vlan_hosts.items():
                Lo0_ping = f"ping {host_ip} source Lo0"
                Lo0_ping_output = net_connect.send_command(Lo0_ping)
                f.write(f"\nPing from Lo0 to {host_name} ({host_ip}):\n")    
                f.write('------------------------------------------------------\n')
                f.write(Lo0_ping + '\n' + Lo0_ping_output + "\n\n")  
                # Check if the ping was successful
                if "Success rate is 100 percent" in Lo0_ping_output or "Success rate is 80 percent" in Lo0_ping_output:
                    cprint(f"Ping from Lo0 to {host_name} ({host_ip}): successful","green")
                else:
                    cprint(f"Ping from Lo0 to {host_name} ({host_ip}): failed","red")
                    
            if 'vlan200' in interface_list:
                # NTPv4 ping test from vlan200 - voice vlan
                for host_name, host_ip in voice_vlan_hosts.items():

                    vlan200_ping = f"ping {host_ip} source vlan200"
                    vlan200_ping_output = net_connect.send_command(vlan200_ping)
                    f.write(f"\nPing from vlan200 to {host_name} ({host_ip}):\n")
                    f.write('------------------------------------------------------\n')
                    f.write(vlan200_ping + '\n' + vlan200_ping_output + "\n\n\n")
                    # Check if the ping was successful
                    if "Success rate is 100 percent" in vlan200_ping_output or "Success rate is 80 percent" in vlan200_ping_output:
                        cprint(f"Ping from vlan200 to {host_name} ({host_ip}): successful","green")
                    else:
                        cprint(f"Ping from vlan200 to {host_name} ({host_ip}): failed","red")
                        
                
            elif 'vlan3100' in interface_list:
                # NTPv4 ping test from vlan3100 - voice vlan
                for host_name, host_ip in voice_vlan_hosts.items():

                    vlan3100_ping = f"ping {host_ip} source vlan3100"
                    vlan3100_ping_output = net_connect.send_command(vlan3100_ping)
                    f.write(f"\nPing from vlan3100 to {host_name} ({host_ip}):\n")
                    f.write('------------------------------------------------------\n')
                    f.write(vlan3100_ping + '\n' + vlan3100_ping_output + "\n\n\n")
                    # Check if the ping was successful
                    if "Success rate is 100 percent" in vlan3100_ping_output or "Success rate is 80 percent" in vlan3100_ping_output:
                        cprint(f"Ping from vlan3100 to {host_name} ({host_ip}): successful","green")
                    else:
                        cprint(f"Ping from vlan3100 to {host_name} ({host_ip}): failed","red")

                    
                # Απλος Ασυμμετρος
                if tenant_type == "1":
                    # NTPv4 ping test from vlan3000 - data vlan
                    for host_name, host_ip in data_vlan_hosts.items():
                
                        vlan3000_ping = f"ping {host_ip} source vlan3000"
                        vlan3000_ping_output = net_connect.send_command(vlan3000_ping)
                        f.write(f"\nPing from vlan3000 to {host_name} ({host_ip}):\n")
                        f.write('------------------------------------------------------\n')
                        f.write(vlan3000_ping + '\n' + vlan3000_ping_output + "\n\n") 
                        # Check if the ping was successful
                        if "Success rate is 100 percent" in vlan3000_ping_output or "Success rate is 80 percent" in vlan3000_ping_output:
                            cprint(f"Ping from vlan3000 to {host_name} ({host_ip}): successful","green")
                        else:
                            cprint(f"Ping from vlan3000 to {host_name} ({host_ip}): failed","red")

    # BGP checks
def asym_bgp_checks(hostname, tenant_type, provider, Healthchecks_file):
        
    if provider == "1":
        ipv4_neighbor = ote_bgp_neighbor
        ipv6_neighbor = ote_bgp_neighbor
    elif provider == "2":
        ipv4_neighbor = wind_bgp_neighbor
        ipv6_neighbor = wind_bgp_v6_neighbor
    elif provider == "3":
        ipv4_neighbor = nova_bgp_neighbor
        ipv6_neighbor = nova_bgp_v6_neighbor
    elif provider == "4":
        ipv4_neighbor = vodafone_bgp_neighbor
        ipv6_neighbor = vodafone_bgp_v6_neighbor
        

    with ConnectHandler(**device) as net_connect:
        command1 = f'\n\nshow ip bgp neighbors {ipv4_neighbor} received-routes\n'
        out1 = net_connect.send_command(command1, expect_string=r'\*>')
        if ipv4_neighbor not in out1:
            cprint(f"Error: ipv4 BGP neighbor {ipv4_neighbor} not found","red")
        output1_list = out1.split('\n')
        with open(Healthchecks_file, 'a') as f:
            f.write(f"\n\nBGP CHECKS\n############\n")
            f.write(f'\n{command1}\n')
            for line in output1_list:
                f.write(line + '\n')
                if line.startswith('*>') and output1_list.index(line) >= 50:
                    break
    with ConnectHandler(**device) as net_connect:
        command2 = f'\n\nshow ip bgp neighbors {ipv4_neighbor} advertised-routes\n'
        out2 = net_connect.send_command(command2, expect_string=r'\*>')
        output2_list = out2.split('\n')
        with open(Healthchecks_file, 'a') as f:
            f.write(f'\n{command2}\n')
            for line in output2_list:
                f.write(line + '\n')
                if line.startswith('*>') and output2_list.index(line) >= 50:
                    break
    with ConnectHandler(**device) as net_connect:
        command3 = f'\n\nshow bgp ipv6 unicast neighbors {ipv6_neighbor} received-routes\n'             
        out3 = net_connect.send_command(command3, expect_string=r'\*>')
        output3_list = out3.split('\n')
        with open(Healthchecks_file, 'a') as f:
            f.write(f'\n{command3}\n')
            for line in output3_list:
                f.write(line + '\n')
                if line.startswith('*>') and output3_list.index(line) >= 50:
                    break
    with ConnectHandler(**device) as net_connect:
        command4 = f'\n\nshow bgp ipv6 unicast neighbors {ipv6_neighbor} advertised-routes\n'
        out4 = net_connect.send_command(command4, expect_string=r'\*>')
        output4_list = out4.split('\n')
        with open(Healthchecks_file, 'a') as f:
            f.write(f'\n{command4}\n')
            for line in output4_list:
                f.write(line + '\n')
                if line.startswith('*>') and output4_list.index(line) >= 50:
                    break

    # Disconnect from device
    net_connect.disconnect()
        

def main():
    with ConnectHandler(**device) as net_connect:

        # Get the hostname of the device
        prompt = net_connect.find_prompt()
        hostname = prompt[:-1]  # Remove the trailing '#' character
  
        # Print the hostname
        print("hostname: ", end='')
        cprint(hostname, 'yellow')

        Healthchecks_file = f'{hostname}/Healthchecks_{timestamp}.txt'
        show_run_file = f'{hostname}/show_run_{timestamp}.txt'

        # Create a directory with the hostname if it doesn't exist
        if not os.path.exists(hostname):
          os.mkdir(hostname)

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
        command5 = 'show license status'
        license_output = net_connect.send_command("show license status")
        with open(Healthchecks_file, 'a') as f:
            f.write(f"{timestamp}\n#################")
            f.write(f"\n\n\nLICENSE CHECKS\n##############\n\n")
            f.write(f'\n{command5}\n')
            f.write(f'\n' + license_output + '\n')
        if "Trust Code Installed: <none>" in license_output:
            cprint("Error: Trust Code not installed", "red")
        else:
            match = re.search(r"Trust Code Installed:\s+(\S+ \S+ \S+ \S+ \S+)", license_output)
            if match:
                trust_code = match.group(1)
                print("License: ", end='')
                cprint(f"Trust Code Installed: {trust_code}", "green")
            else:
                cprint("Error: Failed to extract Trust Code", "red")

        
        # Extract 'show run'
        with open(show_run_file, 'w') as a:
            show_run = net_connect.send_command("show run")
            a.write(f'\n{show_run}\n')
            a.write(f'\n' + show_run + '\n')

        # Call below functions
        interface_list = def_int_checks(Healthchecks_file)
        def_ping_checks(interface_list, tenant_type, Healthchecks_file)
        if tenant_type == "3":
            mmm_bgp_checks(Healthchecks_file, bgp_neighbor)
        else:
            asym_bgp_checks(hostname, tenant_type, provider, Healthchecks_file)
            
        #def_sharepoint(hostname)
 
        print("==========================================================")

        cprint(hostname, 'yellow', end=' ')
        print("checks complete.")

        print("Healthchecks file: ", end='')
        cprint(Healthchecks_file, 'yellow')
        
        print("Running config file: ", end='')
        cprint(show_run_file, 'yellow')

        print("==========================================================")


def def_sharepoint(hostname):
    # SharePoint configuration
    sharepoint_url = "xxxxxx"
    username = "xxxxxx"
    password = "xxxxxx"
    sharepoint_folder = "xxxxxx"

    # Path to the output folder
    output_folder = os.path.join(hostname, "Output")

    try:
        # Authenticate with SharePoint
        ctx_auth = AuthenticationContext(sharepoint_url)
        if ctx_auth.acquire_token_for_user(username, password):
            ctx = ClientContext(sharepoint_url, ctx_auth)
            web = ctx.web
            ctx.load(web)
            ctx.execute_query()

            # Upload the output folder
            folder_url = sharepoint_url + sharepoint_folder + os.path.basename(output_folder)
            folder = web.get_folder_by_server_relative_url(folder_url)
            folder.upload_file(os.path.join(output_folder, "output.txt"))

            # Upload individual txt files
            txt_files = [f for f in os.listdir(output_folder) if f.endswith(".txt")]
            for txt_file in txt_files:
                file_url = sharepoint_url + sharepoint_folder + os.path.basename(txt_file)
                file_info = FileCreationInformation()
                file_info.content = open(os.path.join(output_folder, txt_file), 'rb')
                file_info.url = file_url
                folder.files.add(file_info)

            ctx.execute_query()
        else:
            raise Exception("Failed to acquire SharePoint access token.")
    except Exception as e:
        raise Exception(f"Error authenticating with SharePoint: {e}")


    
# MMM Checks
def mmm_bgp_checks(Healthchecks_file, bgp_neighbor):
    print(f"BGP neighbor(s): {bgp_neighbor}")

    with ConnectHandler(**device) as net_connect:

        # split into individual addresses
        bgp_neighbors = bgp_neighbor.split(',')
        cprint(f"List of BGP neighbor IP addresses: {bgp_neighbors}", "yellow")
        # remove any whitespace characters
        bgp_neighbors = [n.strip() for n in bgp_neighbors]
        #bgp_neighbors = bgp_neighbors.replace(" ", "").split(",")
        
        for neighbor in bgp_neighbors:
            command = f'show ip bgp neighbor {neighbor}\n'
            cprint(command, "green")
            bgp_neighbor_output = net_connect.send_command(command)
  
            with open(Healthchecks_file, 'a') as f:
                f.write(f'{command}\n{"-"*30}\n{bgp_neighbor_output}\n\n')

            # Check the status of the neighbors
            if "No such neighbor" in bgp_neighbor_output:
                cprint(f"BGP neighbor {neighbor} not found", "red")
            else:
                for line in bgp_neighbor_output.split("\n"):
                    if "BGP state" in line:
                        if "Idle" in line:
                            cprint(f"BGP neighbor {neighbor} is Idle", "red")
                        elif "Established" in line:
                            cprint(f"BGP neighbor {neighbor} is Established", "green")
                        else:
                            cprint(line.strip())

            # clear the output buffer to avoid caching/buffering issues
            net_connect.clear_buffer()
    cprint("Completed BGP checks", "green")
            

def validate_device_connection(device):
    try:
        net_connect = ConnectHandler(**device)
        print(f"Successfully connected to {device['host']}")
        return net_connect
    except NetmikoTimeoutException as e:
        print(f"Error: Timeout occurred while connecting to {device['ip']}. Error message: {str(e)}")
        raise  
    except Exception as e:
        print(f"Error: Failed to connect to {device['ip']}. Error message: {str(e)}")
    return None
    
# Asks the user what options they are going to use.
while True:

    # Asks the user for the IP address.
    cprint("Enter tenant IP address: ", "cyan", end="")
    ip_address = input()
    print("You entered:", ip_address)

    if validate_ip_address(ip_address):
        print("Valid IP address")
        print()  # print a blank line

            # Define the device details
        device = {
            "device_type": "cisco_ios",
            "ip": ip_address,
            "username": username,
            "password": password
        }

        # if exception, print error message and do not continue with the script execution:
        #validate_device_connection(device)
  

    else:
        cprint("Invalid IP address","red")
        break

    # Asks the user for the tenant type
    cprint("Now please select the tenant type:","cyan")
    cprint("1. Απλος Ασυμμετρος","cyan")
    cprint("2. ΠΣΔ Ασυμμετρος","cyan")
    cprint("3. MMM","cyan")
    tenant_type = input("Enter your choice (1-3): ")

    # Απλος Ασυμμετρος
    if tenant_type == "1": 
        cprint("\nΑπλος Ασυμμετρος","cyan")
        cprint("\nNow please select the provider","yellow")
        cprint("\n1. OTE","yellow")
        cprint("2. WIND","yellow")
        cprint("3. NOVA","yellow")
        cprint("4. VODAFONE\n","yellow")
        provider = input("Please pick an option: ")

        if provider in ("1", "2", "3", "4"):
            main()

    # ΠΣΔ Ασυμμετρος
    elif tenant_type == "2":
        cprint("\nΠΣΔ Ασυμμετρος","cyan")
        cprint("\nNow please select the provider","yellow")
        cprint("\n1. OTE","yellow")
        cprint("2. WIND","yellow")
        cprint("3. NOVA","yellow")
        cprint("4. VODAFONE\n","yellow")
        provider = input("Please pick an option: ")

        if provider in ("1", "2", "3", "4"):
            main()

    # MMM
    elif tenant_type == "3":
        cprint("\nΜΜΜ","cyan")
        cprint("\nPlease enter a comma-separated list of BGP neighbor IPs:", "cyan")
        bgp_neighbor = input()
        
        main()

    else: 
        cprint("Invalid option","red")

    print()  # print a blank line
        
    ask_again = input("Would you like to run checks again for another tenant IP ? (y/n): ")
    if ask_again.lower() != "y":
            print("Goodbye!")
            print()  # print a blank line
            break