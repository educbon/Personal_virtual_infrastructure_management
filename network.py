import sys
import libvirt
import os
import xml.dom.minidom as minidom
from utils import run_command, input_default


def list_network():
    run_command(['sudo', 'virsh', 'net-list', '--all'])

def list_bridge():
    run_command(['sudo', 'ovs-vsctl', 'show'])

def create_network_xml(network_name, bridge_name, vlan_config, default_portgroup=None):
    dom = minidom.getDOMImplementation().createDocument(None, 'network', None)
    network = dom.documentElement

    name = dom.createElement('name')
    name.appendChild(dom.createTextNode(network_name))
    network.appendChild(name)

    forward = dom.createElement('forward')
    forward.setAttribute('mode', 'bridge')
    network.appendChild(forward)

    bridge = dom.createElement('bridge')
    bridge.setAttribute('name', bridge_name)
    network.appendChild(bridge)

    virtualport = dom.createElement('virtualport')
    virtualport.setAttribute('type', 'openvswitch')
    network.appendChild(virtualport)

    portgroup_names = set()

    for vlan_id in vlan_config:
        portgroup_name = f'vlan-{vlan_id}'

        if portgroup_name in portgroup_names:
            print(f"Warning: Duplicate portgroup name '{portgroup_name}' detected, skipping.")
            continue

        portgroup_names.add(portgroup_name)

        portgroup = dom.createElement('portgroup')
        portgroup.setAttribute('name', portgroup_name)

        # Kiểm tra và thiết lập portgroup mặc định
        if vlan_id == default_portgroup:
            portgroup.setAttribute('default', 'yes')

        vlan = dom.createElement('vlan')
        if vlan_id != 'all':
            tag = dom.createElement('tag')
            tag.setAttribute('id', vlan_id)
            vlan.appendChild(tag)
        else:
            vlan.setAttribute('trunk', 'yes')
            for trunk_id in vlan_config[:-1]:
                tag = dom.createElement('tag')
                tag.setAttribute('id', trunk_id)
                vlan.appendChild(tag)

        portgroup.appendChild(vlan)
        network.appendChild(portgroup)

    return dom.toxml()


def define_network(conn, network_name, bridge_name, vlan_config, save_dir, default_portgroup=None):
    xml_desc = create_network_xml(network_name, bridge_name, vlan_config, default_portgroup)

    file_path = os.path.join(save_dir, f"{network_name}.xml")
    with open(file_path, 'w') as xml_file:
        xml_file.write(xml_desc)
    print(f"Network XML saved to {file_path}")

    try:
        network = conn.networkDefineXML(xml_desc)
        if network is None:
            print(f"Failed to define the network {network_name}.")
            return
        network.create()
        print(f"Network {network_name} created and started successfully.")
    except libvirt.libvirtError as e:
        print(f"Failed to define or start the network: {e}")
        return

def delete_network(network_name):
    run_command(['sudo', 'virsh', 'net-list', '--all'])
    if network_name == '¿':
        network_name = input('Enter the network name: ')
    run_command(['sudo', 'virsh', 'net-destroy', network_name])
    run_command(['sudo', 'virsh', 'net-undefine', network_name])


def create_network(network_name):
    if network_name == '¿':
        network_name = input('Enter the network name: ')
    conn = libvirt.open('qemu:///system')
    if conn is None:
        print('Failed to connect to qemu:///system', file=sys.stderr)
        sys.exit(1)

    bridge_name = input('Enter the bridge name: ')

    vlan_input = input('Enter VLAN IDs separated by commas (e.g., 100,200): ')
    vlan_config = vlan_input.split(',')

    default_portgroup = input('Enter default VLAN ID (or leave blank for no default): ').strip()
    if default_portgroup == '':
        default_portgroup = None

    # default dir
    save_dir = '/home/bon/kvm_network'

    define_network(conn, network_name, bridge_name, vlan_config, save_dir, default_portgroup)
    # run_command(['sudo', 'virsh', 'net-start', network_name])
    run_command(['sudo', 'virsh', 'net-autostart', network_name])

    conn.close()


def create_br(br_name):
    if br_name == '¿':
        br_name = input('Enter the bridge name to be created: ')
    run_command(['sudo', 'ovs-vsctl', 'add-br', br_name])
    run_command(['sudo', 'ovs-vsctl', 'set', 'bridge', br_name, 'other-config:secure-mode=fail'])
    br_ip = input_default("Enter the bridge IP (default: None): ", default_value="None")
    if br_ip != "None":
        run_command(['sudo', 'ip', 'addr', 'add', br_ip, 'dev', br_name])
    run_command(['sudo', 'ip', 'link', 'set', 'dev', br_name, 'up'])


def delete_br(br_name):
    if br_name == '¿':
        br_name = input('Enter the bridge name to be deleted: ')
    run_command(['sudo', 'ovs-vsctl', 'del-br', br_name])

def trunk(br1, br2):
    run_command('sudo', 'ovs-vstl ', 'show')
    if br1 == '¿':
        br1 = input('Enter the bridge1: ')
    if br2 == '¿':
        br2 = input('Enter the bridge2: ')

    br1_br2 = br1 + br2
    br2_br1 = br2 + br1

    run_command(['sudo', 'ovs-vsctl', 'add-port', br1, br1_br2])
    run_command(['sudo', 'ovs-vsctl', 'set', 'Interface', br1_br2, 'type=internal'])
    run_command(['sudo', 'ovs-vsctl', 'add-port', br2, br2_br1])
    run_command(['sudo', 'ovs-vsctl', 'set', 'Interface', br2_br1, 'type=internal'])
    run_command(['sudo', 'ovs-vsctl', 'set', 'interface', br1_br2, 'type=patch', f'options:peer={br2_br1}'])
    run_command(['sudo', 'ovs-vsctl', 'set', 'interface', br2_br1, 'type=patch', f'options:peer={br1_br2}'])

