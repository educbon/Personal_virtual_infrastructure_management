import sys
import time
import libvirt
from utils import input_default
from network import list_network, create_network, delete_network, create_br, delete_br, trunk, list_bridge
from create_xml import create_xml
import cloud_init
import uuid
import shutil

def init():
    global conn
    conn = libvirt.open('qemu:///system')
    if conn is None:
        print('Failed to connect to qemu:///system', file=sys.stderr)
        sys.exit(1)

def getDomainStateStr(domain_state):
    state_str = ['No State', 'Running', 'Blocked', 'Paused', 'Shutting Down', 'Shut Off', 'Crashed', 'Paused by Guest Power Management', 'Last State']
    return state_str[domain_state]

def listDomains():
    domains = conn.listAllDomains()
    for domain in domains:
        state = domain.state()[0]
        state_str = getDomainStateStr(state)
        print(f"\n------{domain.name()}: {state_str}------")
        print(f"Virtual Machine ID: {domain.ID() if domain.isActive() else 'Inactive'}")
        print(f"Virtual Machine State: {state_str}")
        print(f"Virtual Machine Memory: {domain.maxMemory() // 1024}MB")
        if domain.isActive():
            print(f"Virtual Machine CPU Cores: {domain.maxVcpus()}")
        else:
            print("Virtual Machine CPU Cores: Not available (VM is not running)")
    print("\n")

def define(name):
    if name == '¿':
        name = input('Please enter the name of the virtual machine to operate：')
    xml_path = f'/etc/libvirt/qemu/{name}.xml'
    xmldesc = f'<volume type="file"><name>{name}.qcow2</name><allocation unit="M">10</allocation><capacity unit="M">1000</capacity><target><path>/var/lib/libvirt/images/{name}.qcow2</path><format type="qcow2"/></target></volume>'
    storage_pool = conn.storagePoolLookupByName('default')
    storage_vol = storage_pool.createXML(xmldesc, 0)
    create_xml(xml_path, False, name)
    with open(xml_path) as xmlfile:
        xmlconfig = xmlfile.read()
    dom = conn.defineXML(xmlconfig)
    if dom is None:
        print("Failed to define the domain from XML configuration.")
    else:
        print(f"Virtual Machine {name} Created")

def undefine(name):
    if name == '¿':
        name = input('Please enter the name of the virtual machine to operate: ')
    try:
        dom = conn.lookupByName(name)
        dom.undefine()
        print(f"Virtual Machine {name} Suspended")
    except libvirt.libvirtError as e:
        print(f"[libvirtError] Error: {e}")
        return 1

def suspend(name):
    if name == '¿':
        name = input('Please enter the name of the virtual machine to be operated:')
    try:
        dom = conn.lookupByName(name)
        dom.suspend()
        print(f"Virtual Machine {name} Paused")
    except libvirt.libvirtError as e:
        print(f"[libvirtError] Error: {e}")
        return 1

def resume(name):
    if name == '¿':
        name = input('Please enter the name of the virtual machine to be operated：')
    try:
        dom = conn.lookupByName(name)
        dom.resume()
        print(f"Virtual Machine {name} Running")
    except libvirt.libvirtError as e:
        print(f"[libvirtError] Error: {e}")
        return 1

def destroy(name):
    if name == '¿':
        name = input('Please enter the name of the virtual machine to be operated:')
    try:
        dom = conn.lookupByName(name)
        dom.destroy()
        print(f"Virtual Machine {name} Destroyed")
    except libvirt.libvirtError as e:
        print(f"[libvirtError] Error: {e}")
        return 1

def start(name):
    if name == '¿':
        name = input('Please enter the name of the virtual machine to be operated:')
    try:
        dom = conn.lookupByName(name)
        dom.create()
        print(f"Virtual Machine {name} Started")
    except libvirt.libvirtError as e:
        print(f"[libvirtError] Error: {e}")
        return 1

def shutdown(name):
    if name == '¿':
        name = input('Please enter the name of the virtual machine to be operated:')
    try:
        dom = conn.lookupByName(name)
        dom.shutdown()
        print(f"Shutting down {name}...")
        time.sleep(3)
        if dom.isActive():
            print(f"Cannot shut down {name}, try to destroy it")
        else:
            print(f"Virtual machine {name} shut down successfully")
    except libvirt.libvirtError as e:
        print(f"[libvirtError] Error: {e}")
        return 1


def clone(source_name, target_name):
    if source_name == '¿':
        source_name = input('Please enter the name of the source virtual machine:')
    if target_name == '¿':
        target_name = input('Please enter the name of the target virtual machine:')

    try:
        # Lookup the source domain
        source_dom = conn.lookupByName(source_name)
        if source_dom is None:
            print(f"Source VM '{source_name}' not found.")
            return 1

        # Retrieve and modify the XML configuration
        source_xml = source_dom.XMLDesc()
        target_xml = source_xml.replace(source_name, target_name)
        target_xml = target_xml.replace(
            source_dom.UUIDString(), str(uuid.uuid4())
        )

        # Modify disk path in XML
        source_disk_path = f'/var/lib/libvirt/images/{source_name}.qcow2'
        target_disk_path = f'/var/lib/libvirt/images/{target_name}.qcow2'
        target_xml = target_xml.replace(source_disk_path, target_disk_path)

        # Copy the disk image
        print(f"Cloning disk from {source_disk_path} to {target_disk_path}...")
        shutil.copy(source_disk_path, target_disk_path)

        # Handle cloud-init ISO if exists

        # Define the new domain
        target_dom = conn.defineXML(target_xml)
        if target_dom is None:
            print("Failed to define the target VM.")
            return 1
        else:
            print(f"Virtual Machine '{target_name}' cloned successfully from '{source_name}'.")
            return 0

    except libvirt.libvirtError as e:
        print(f"[libvirtError] Error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"[FileNotFoundError] Error: {e}")
        return 1

def help_info():
    print("\n------ Main Menu ------")
    print("1. Manager VMs")
    print("2. Manager Networks")
    print("3. Quit Program")


def help_manager_vms():
    print("\n------ Manager VMs ------")
    print("1. List VMs and Status")
    print("2. Create VM")
    print("3. Start VM")
    print("4. Suspend VM")
    print("5. Resume VM")
    print("6. Shutdown VM")
    print("7. Destroy VM")
    print("8. clone VM")
    print("9. Delete VM")
    print("10. Back")
    print("11. Quit Program")


def help_create_vm():
    print("\n------ Create VM ------")
    print("1. Default")
    print("2. Custom (Cloud-Init)")
    print("3. Back")
    print("4. Quit Program")


def help_custom_cloud_init():
    print("\n------ Custom VM with Cloud-Init ------")
    print("1. Create VM with Cloud-Init")
    print("2. Create Multiple VMs with Cloud-Init")
    print("3. Back")
    print("4. Quit Program")


def help_manager_networks():
    print("\n------ Manager Networks ------")
    print("1. List Network")
    print("2. List Bridge")
    print("3. Create Network")
    print("4. Delete Network")
    print("5. Create Bridge")
    print("6. Delete Bridge")
    print("7. Connect Trunk Between Bridges")
    print("8. Back")
    print("9. Quit Program")


def menu():
    while True:
        help_info()
        main_choice = input("> ")

        if main_choice == "1":  # Manager VMs
            while True:
                help_manager_vms()
                vm_choice = input("> ")

                if vm_choice == "1":
                    listDomains()
                elif vm_choice == "2":  # Create VM
                    while True:
                        help_create_vm()
                        create_vm_choice = input("> ")

                        if create_vm_choice == "1":  # Default create VM
                            arg = input("Enter VM name to create: ")
                            define(arg)
                        elif create_vm_choice == "2":  # Custom VM with Cloud-Init
                            while True:
                                help_custom_cloud_init()
                                cloud_choice = input("> ")

                                if cloud_choice == "1":  # Create VM with Cloud-Init
                                    vm_name = input("Enter VM name: ")
                                    ram = input_default("Enter VM ram (default = 1024): ", 1024)
                                    vcpus = input_default("Enter VM vcpus (default = 1): ", 1)
                                    network_name = input("Enter network name: ")
                                    ip_address = input("Enter IP address: ")
                                    netmask = input_default("Enter netmask (default = 255.255.255.0): ", "255.255.255.0")
                                    gateway = input("Enter gateway: ")
                                    portgroup = input_default("Enter VLAN (default=none; e.g., vlan-100,vlan-200): ", "none")
                                    base_image_path = input_default(
                                        "Enter path to base image (default: /var/lib/libvirt/images/focal-server-cloudimg-amd64.img): ",
                                        default_value="/var/lib/libvirt/images/focal-server-cloudimg-amd64.img")
                                    cloud_init.create_vm_with_cloud_init(conn, vm_name, network_name, ip_address, netmask,
                                                                         gateway, base_image_path, ram, vcpus, portgroup)
                                elif cloud_choice == "2":  # Create Multiple VMs with Cloud-Init
                                    vm_name = input("Enter VM based name: ")
                                    number_of_vms = int(input("Number of VMs: "))
                                    ram = input_default("Enter VMs ram (default = 1024): ", 1024)
                                    vcpus = input_default("Enter VMs vcpus (default = 1): ", 1)
                                    network_name = input("Enter network name: ")
                                    ip_range_start = input("Started IP range: ")
                                    ip_range_end = input("Ended IP range: ")
                                    netmask = input_default("Enter netmask (default = 255.255.255.0): ",
                                                            "255.255.255.0")
                                    gateway = input("Enter gateway: ")
                                    portgroup = input_default("Enter VLAN (default=none; e.g., vlan-100,vlan-200): ", "none")
                                    base_image_path = input_default(
                                        "Enter path to base image (default: /var/lib/libvirt/images/focal-server-cloudimg-amd64.img): ",
                                        default_value="/var/lib/libvirt/images/focal-server-cloudimg-amd64.img")
                                    cloud_init.create_multiple_vms_with_cloud_init(None, vm_name, network_name,
                                                                                   number_of_vms, ip_range_start,
                                                                                   ip_range_end, netmask, gateway,
                                                                                   base_image_path, ram, vcpus,
                                                                                   portgroup)
                                elif cloud_choice == "3":
                                    break
                                elif cloud_choice == "4":
                                    print("Exiting Program.")
                                    return
                                else:
                                    print("Invalid command, please try again.\n")

                        elif create_vm_choice == "3":
                            break
                        elif create_vm_choice == "4":
                            print("Exiting Program.")
                            return
                        else:
                            print("Invalid command, please try again.\n")

                elif vm_choice == "3":
                    arg = input("Enter VM name to start: ")
                    start(arg)
                elif vm_choice == "4":
                    arg = input("Enter VM name to suspend: ")
                    suspend(arg)
                elif vm_choice == "5":
                    arg = input("Enter VM name to resume: ")
                    resume(arg)
                elif vm_choice == "6":
                    arg = input("Enter VM name to shutdown: ")
                    shutdown(arg)
                elif vm_choice == "7":
                    arg = input("Enter VM name to destroy: ")
                    destroy(arg)
                elif vm_choice == "8":
                    source_vm = input("Enter source VM name to clone: ")
                    target_vm = input("Enter target VM name to clone: ")
                    clone(source_vm, target_vm)
                elif vm_choice == "9":
                    arg = input("Enter VM name to delete: ")
                    undefine(arg)
                elif vm_choice == "10":
                    break
                elif vm_choice == "11":
                    print("Exiting Program.")
                    return
                else:
                    print("Invalid command, please try again.\n")

        elif main_choice == "2":  # Manager Networks
            while True:
                help_manager_networks()
                network_choice = input("> ")
                if network_choice in ["1", "list_network"]:
                    list_network()
                elif network_choice in ["2", "list_bridge"]:
                    list_bridge()
                elif network_choice in ["3", "create_network"]:
                    arg = input("Enter Network name to create: ")
                    create_network(arg)
                elif network_choice in ["4", "delete_network"]:
                    arg = input("Enter Network name to delete: ")
                    delete_network(arg)
                elif network_choice in ["5", "create_bridge"]:
                    arg = input("Enter Bridge name to create: ")
                    create_br(arg)
                elif network_choice in ["6", "delete_bridge"]:
                    arg = input("Enter Bridge name to delete: ")
                    delete_br(arg)
                elif network_choice == "7":
                    bridge1 = input("Enter first bridge name: ")
                    bridge2 = input("Enter second bridge name: ")
                    trunk(bridge1, bridge2)
                elif network_choice == "8":
                    break
                elif network_choice == "9":
                    print("Exiting Program.")
                    return
                else:
                    print("Invalid command, please try again.\n")

        elif main_choice == "3":
            print("Exiting Program.")
            break
        else:
            print("Invalid command, please try again.\n")



if __name__ == "__main__":
    init()
    menu()