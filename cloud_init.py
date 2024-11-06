import os
from utils import run_command
import random

def create_vm_with_cloud_init(conn, vm_name,network_name, ip_address, netmask, gateway, base_image_path, ram, vcpus, portgroup):
    cloud_init_dir = f'/home/bon/cloud-init/{vm_name}'
    os.makedirs(cloud_init_dir, exist_ok=True)

    user_data = f"""#cloud-config
hostname: {vm_name} 
users:
  - name: {vm_name}
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    groups: sudo
    shell: /bin/bash
    lock_passwd: false
    passwd: $6$.DUs3h3IuM4A3ey2$/UxWZlzDVB88KIqXDcLyd/5PQ1h6C3XWgXeLaF4EnT3lg/GQlIMt8QjsPIt9tY.AteE62a8HMlpC3YZ3IpzkM0
    chpasswd: {{ expire: False }}

package_update: true
package_upgrade: true
"""

    meta_data = f"""instance-id: {vm_name}
local-hostname: {vm_name}
network-interfaces: |
  auto enp1s0
  iface enp1s0 inet static
    address {ip_address}
    netmask {netmask}
    gateway {gateway}
    dns-nameservers 8.8.8.8 1.1.1.1
"""

    with open(f'{cloud_init_dir}/user-data', 'w') as f:
        f.write(user_data)

    with open(f'{cloud_init_dir}/meta-data', 'w') as f:
        f.write(meta_data)

    iso_path = f'/var/lib/libvirt/images/seed_{vm_name}.iso'
    run_command(['genisoimage', '-output', iso_path, '-volid', 'cidata', '-joliet', '-rock',
                             f'{cloud_init_dir}/user-data', f'{cloud_init_dir}/meta-data'])

    qcow2_path = f'/var/lib/libvirt/images/{vm_name}.qcow2'
    run_command(['sudo','qemu-img', 'create', '-f', 'qcow2', '-b', base_image_path, qcow2_path, '10G'])

    if portgroup == "none":
        network_config = f'network={network_name},model=virtio'
    else:
        network_config = f'network={network_name},portgroup={portgroup},model=virtio'

    run_command([
        'sudo','virt-install', '--name', vm_name, '--ram', "1024", '--vcpus', "1",
        '--disk', f'path={qcow2_path},format=qcow2',
        '--disk', f'path={iso_path},device=cdrom', '--import', '--os-type', 'linux',
        '--os-variant', 'ubuntu20.04', '--network',network_config,
        '--graphics', 'vnc', '--noautoconsole'
    ])

    print(f"Running virt-install with network config: {network_config}")
    print(f"Running virt-install with ram: {ram}")
    print(f"Running virt-install with vcpus: {vcpus}")
    print(f"-----------------VM {vm_name} have been created successfully!-----------------\n")


def create_multiple_vms_with_cloud_init(conn, vm_name,network_name, number_of_vms, ip_range_start, ip_range_end, netmask, gateway, base_image_path, ram, vcpus, portgroup):
    # IP range calculation
    start_ip = ip_to_int(ip_range_start)
    end_ip = ip_to_int(ip_range_end)

    # Check if the number of virtual machines and IP range is sufficient
    if number_of_vms > (end_ip - start_ip + 1):
        raise ValueError("The IP range is insufficient for the requested number of VMs.")

    # Generate random IP list from given range
    allocated_ips = random.sample(range(start_ip, end_ip + 1), number_of_vms)

    # Create virtual machine with each assigned IP
    for i, ip in enumerate(allocated_ips):
        name = f"{vm_name}{i + 1}"
        ip_address = int_to_ip(ip)  # convert IP integer to string
        create_vm_with_cloud_init(conn, name,network_name, ip_address, netmask, gateway, base_image_path, ram, vcpus, portgroup)

    print(f"-----------------VMs {vm_name} have been created successfully!-----------------\n")

def ip_to_int(ip):
    return int(''.join([f'{int(x):02x}' for x in ip.split('.')]), 16)

def int_to_ip(ip_int):
    return '.'.join([str((ip_int >> (i * 8)) & 0xFF) for i in range(3, -1, -1)])