import xml.dom.minidom as minidom
from uuid import uuid4
import os as system_os
import random
import libvirt

def input_default(prompt, default_value):
    result = input(prompt)
    return result if result.strip() else default_value

def randomMAC():
    mac = [0x52, 0x54, 0x00] + [random.randint(0x00, 0xff) for _ in range(3)]
    return ':'.join(f"{x:02x}" for x in mac)

def create_xml(xml_path, img: bool, name_of_target):
    dom = minidom.getDOMImplementation().createDocument(None, 'domain', None)
    domain = dom.documentElement  # Virtual machine
    domain.setAttribute('type', 'kvm')

    # VM's name and UUID
    name = dom.createElement('name')
    name.appendChild(dom.createTextNode(name_of_target))
    domain.appendChild(name)

    uuid = dom.createElement('uuid')
    uuid.appendChild(dom.createTextNode(str(uuid4())))
    domain.appendChild(uuid)

    # add metadata for os
    metadata = dom.createElement('metadata')
    libosinfo = dom.createElement('libosinfo:libosinfo')
    libosinfo.setAttribute('xmlns:libosinfo', 'http://libosinfo.org/xmlns/libvirt/domain/1.0')
    osinfo = dom.createElement('libosinfo:os')
    osinfo.setAttribute('id', 'http://ubuntu.com/ubuntu/20.04')
    libosinfo.appendChild(osinfo)
    metadata.appendChild(libosinfo)
    domain.appendChild(metadata)

    # memory and CPU
    memory = dom.createElement('memory')
    memory.setAttribute('unit', 'MiB')
    memory.appendChild(dom.createTextNode('1024'))
    domain.appendChild(memory)

    currentMemory = dom.createElement('currentMemory')
    currentMemory.setAttribute('unit', 'MiB')
    currentMemory.appendChild(dom.createTextNode(input_default(
        'Please enter the virtual machine memory [unit: MB, default value 1024]:', '1024')))
    domain.appendChild(currentMemory)

    vcpu = dom.createElement('vcpu')
    vcpu.setAttribute('placement', 'static')
    vcpu.appendChild(dom.createTextNode(input_default(
        'Please enter the number of virtual machine vCPUs [default value 1]:', '1')))
    domain.appendChild(vcpu)

    # os configuration
    os = dom.createElement('os')
    type = dom.createElement('type')
    type.setAttribute('arch', 'x86_64')
    type.setAttribute('machine', 'pc-q35-4.2')
    type.appendChild(dom.createTextNode('hvm'))
    os.appendChild(type)
    domain.appendChild(os) #####

    boot_hd = dom.createElement('boot')
    boot_hd.setAttribute('dev', 'hd')
    os.appendChild(boot_hd)
    domain.appendChild(os)

    boot_cdrom = dom.createElement('boot')
    boot_cdrom.setAttribute('dev', 'cdrom')
    os.appendChild(boot_cdrom)
    domain.appendChild(os)

    # features
    features = dom.createElement('features')
    acpi = dom.createElement('acpi')
    apic = dom.createElement('apic')
    vmport = dom.createElement('vmport')
    vmport.setAttribute('state', 'off')
    features.appendChild(acpi)
    features.appendChild(apic)
    features.appendChild(vmport)
    domain.appendChild(features)

    # CPU and Timer
    cpu = dom.createElement('cpu')
    cpu.setAttribute('mode', 'host-model')
    cpu.setAttribute('check', 'partial')
    domain.appendChild(cpu)

    clock = dom.createElement('clock')
    clock.setAttribute('offset', 'utc')
    timer_rtc = dom.createElement('timer')
    timer_rtc.setAttribute('name', 'rtc')
    timer_rtc.setAttribute('tickpolicy', 'catchup')
    clock.appendChild(timer_rtc)

    timer_pit = dom.createElement('timer')
    timer_pit.setAttribute('name', 'pit')
    timer_pit.setAttribute('tickpolicy', 'delay')
    clock.appendChild(timer_pit)

    timer_hpet = dom.createElement('timer')
    timer_hpet.setAttribute('name', 'hpet')
    timer_hpet.setAttribute('present', 'no')
    clock.appendChild(timer_hpet)
    domain.appendChild(clock)

    # actions when power off, reboot and crash
    on_poweroff = dom.createElement('on_poweroff')
    on_poweroff.appendChild(dom.createTextNode('destroy'))
    domain.appendChild(on_poweroff)

    on_reboot = dom.createElement('on_reboot')
    on_reboot.appendChild(dom.createTextNode('restart'))
    domain.appendChild(on_reboot)

    on_crash = dom.createElement('on_crash')
    on_crash.appendChild(dom.createTextNode('destroy'))
    domain.appendChild(on_crash)

    # source management
    pm = dom.createElement('pm')
    suspend_to_mem = dom.createElement('suspend-to-mem')
    suspend_to_mem.setAttribute('enabled', 'no')
    pm.appendChild(suspend_to_mem)

    suspend_to_disk = dom.createElement('suspend-to-disk')
    suspend_to_disk.setAttribute('enabled', 'no')
    pm.appendChild(suspend_to_disk)
    domain.appendChild(pm)

    devices = dom.createElement('devices')

    # simulation
    emulator = dom.createElement('emulator')
    emulator.appendChild(dom.createTextNode('/usr/bin/qemu-system-x86_64'))
    devices.appendChild(emulator)

    #disk size
    disk_size = input_default('Please enter the disk size [e.g., 10G]:', '10G')
    img_path = f'/var/lib/libvirt/images/{name_of_target}.qcow2'
    system_os.system(f'qemu-img create -f qcow2 {img_path} {disk_size}')

    # hard disk
    disk = dom.createElement('disk')
    disk.setAttribute('type', 'file')
    disk.setAttribute('device', 'disk')
    driver = dom.createElement('driver')
    driver.setAttribute('name', 'qemu')
    driver.setAttribute('type', 'qcow2')
    disk.appendChild(driver)
    source = dom.createElement('source')
    source.setAttribute('file', f'/var/lib/libvirt/images/{name_of_target}.qcow2')
    disk.appendChild(source)
    target = dom.createElement('target')
    target.setAttribute('dev', 'vda')
    target.setAttribute('bus', 'virtio')
    disk.appendChild(target)
    address = dom.createElement('address')
    address.setAttribute('type', 'pci')
    address.setAttribute('domain', '0x0000')
    address.setAttribute('bus', '0x03')
    address.setAttribute('slot', '0x00')
    address.setAttribute('function', '0x0')
    disk.appendChild(address)
    devices.appendChild(disk)

    # CD-ROM
    disk_cdrom = dom.createElement('disk')
    disk_cdrom.setAttribute('type', 'file')
    disk_cdrom.setAttribute('device', 'cdrom')
    driver_cdrom = dom.createElement('driver')
    driver_cdrom.setAttribute('name', 'qemu')
    driver_cdrom.setAttribute('type', 'raw')
    disk_cdrom.appendChild(driver_cdrom)
    source_cdrom = dom.createElement('source')
    iso_path = input_default(
        'Please enter the iso file location\n[default value /home/bon/Downloads/ubuntu-20.04.6-live-server-amd64.iso]',
        '/home/bon/Downloads/ubuntu-20.04.6-live-server-amd64.iso')
    source_cdrom.setAttribute('file', iso_path)
    disk_cdrom.appendChild(source_cdrom)
    target_cdrom = dom.createElement('target')
    target_cdrom.setAttribute('dev', 'sda')
    target_cdrom.setAttribute('bus', 'sata')
    disk_cdrom.appendChild(target_cdrom)
    readonly = dom.createElement('readonly')
    disk_cdrom.appendChild(readonly)
    address_cdrom = dom.createElement('address')
    address_cdrom.setAttribute('type', 'drive')
    address_cdrom.setAttribute('controller', '0')
    address_cdrom.setAttribute('bus', '0')
    address_cdrom.setAttribute('target', '0')
    address_cdrom.setAttribute('unit', '0')
    disk_cdrom.appendChild(address_cdrom)
    devices.appendChild(disk_cdrom)

    # Controllers
    controller_usb = dom.createElement('controller')
    controller_usb.setAttribute('type', 'usb')
    controller_usb.setAttribute('index', '0')
    controller_usb.setAttribute('model', 'ich9-ehci1')
    address_usb = dom.createElement('address')
    address_usb.setAttribute('type', 'pci')
    address_usb.setAttribute('domain', '0x0000')
    address_usb.setAttribute('bus', '0x00')
    address_usb.setAttribute('slot', '0x1d')
    address_usb.setAttribute('function', '0x7')
    controller_usb.appendChild(address_usb)
    devices.appendChild(controller_usb)

    controller_usb_uhci1 = dom.createElement('controller')
    controller_usb_uhci1.setAttribute('type', 'usb')
    controller_usb_uhci1.setAttribute('index', '0')
    controller_usb_uhci1.setAttribute('model', 'ich9-uhci1')
    master_uhci1 = dom.createElement('master')
    master_uhci1.setAttribute('startport', '0')
    controller_usb_uhci1.appendChild(master_uhci1)
    address_uhci1 = dom.createElement('address')
    address_uhci1.setAttribute('type', 'pci')
    address_uhci1.setAttribute('domain', '0x0000')
    address_uhci1.setAttribute('bus', '0x00')
    address_uhci1.setAttribute('slot', '0x1d')
    address_uhci1.setAttribute('function', '0x0')
    address_uhci1.setAttribute('multifunction', 'on')
    controller_usb_uhci1.appendChild(address_uhci1)
    devices.appendChild(controller_usb_uhci1)

    controller_sata = dom.createElement('controller')
    controller_sata.setAttribute('type', 'sata')
    controller_sata.setAttribute('index', '0')
    address_sata = dom.createElement('address')
    address_sata.setAttribute('type', 'pci')
    address_sata.setAttribute('domain', '0x0000')
    address_sata.setAttribute('bus', '0x00')
    address_sata.setAttribute('slot', '0x1f')
    address_sata.setAttribute('function', '0x2')
    controller_sata.appendChild(address_sata)
    devices.appendChild(controller_sata)

    controller_pci = dom.createElement('controller')
    controller_pci.setAttribute('type', 'pci')
    controller_pci.setAttribute('index', '0')
    controller_pci.setAttribute('model', 'pcie-root')
    devices.appendChild(controller_pci)

    controller_virtio_serial = dom.createElement('controller')
    controller_virtio_serial.setAttribute('type', 'virtio-serial')
    controller_virtio_serial.setAttribute('index', '0')
    address_virtio_serial = dom.createElement('address')
    address_virtio_serial.setAttribute('type', 'pci')
    address_virtio_serial.setAttribute('domain', '0x0000')
    address_virtio_serial.setAttribute('bus', '0x02')
    address_virtio_serial.setAttribute('slot', '0x00')
    address_virtio_serial.setAttribute('function', '0x0')
    controller_virtio_serial.appendChild(address_virtio_serial)
    devices.appendChild(controller_virtio_serial)

    interface = dom.createElement('interface')
    interface.setAttribute('type', 'network')
    mac = dom.createElement('mac')
    mac.setAttribute('address', randomMAC())
    interface.appendChild(mac)

    network_name = input_default('Please enter the network name to connect this VM to '
                                 '[leave blank if default]: ', 'default')
    if network_name == 'default':
        source_i = dom.createElement('source')
        source_i.setAttribute('network', 'default')
        interface.appendChild(source_i)
    else:
        portgroup_name = input_default('Please enter the portgroup (leave blank if not applicable) '
                                       '[e.g., vlan-100, vlan-00, all: ', '').strip()
        source_i = dom.createElement('source')
        source_i.setAttribute('network', network_name)
        if portgroup_name:
            source_i.setAttribute('portgroup', portgroup_name)
        interface.appendChild(source_i)
    model_i = dom.createElement('model')
    model_i.setAttribute('type', 'virtio')
    interface.appendChild(model_i)
    address_i = dom.createElement('address')
    address_i.setAttribute('type', 'pci')
    address_i.setAttribute('domain', '0x0000')
    address_i.setAttribute('bus', '0x00')
    address_i.setAttribute('slot', '0x03')
    address_i.setAttribute('function', '0x0')
    interface.appendChild(address_i)
    devices.appendChild(interface)

    # other devices
    serial = dom.createElement('serial')
    serial.setAttribute('type', 'pty')
    target_serial = dom.createElement('target')
    target_serial.setAttribute('type', 'isa-serial')
    target_serial.setAttribute('port', '0')
    model_serial = dom.createElement('model')
    model_serial.setAttribute('name', 'isa-serial')
    target_serial.appendChild(model_serial)
    serial.appendChild(target_serial)
    devices.appendChild(serial)

    console = dom.createElement('console')
    console.setAttribute('type', 'pty')
    target_console = dom.createElement('target')
    target_console.setAttribute('type', 'serial')
    target_console.setAttribute('port', '0')
    console.appendChild(target_console)
    devices.appendChild(console)

    channel_virtio = dom.createElement('channel')
    channel_virtio.setAttribute('type', 'unix')
    target_channel_virtio = dom.createElement('target')
    target_channel_virtio.setAttribute('type', 'virtio')
    target_channel_virtio.setAttribute('name', 'org.qemu.guest_agent.0')
    channel_virtio.appendChild(target_channel_virtio)
    address_channel_virtio = dom.createElement('address')
    address_channel_virtio.setAttribute('type', 'virtio-serial')
    address_channel_virtio.setAttribute('controller', '0')
    address_channel_virtio.setAttribute('bus', '0')
    address_channel_virtio.setAttribute('port', '1')
    channel_virtio.appendChild(address_channel_virtio)
    devices.appendChild(channel_virtio)

    channel_spicevmc = dom.createElement('channel')
    channel_spicevmc.setAttribute('type', 'spicevmc')
    target_channel_spicevmc = dom.createElement('target')
    target_channel_spicevmc.setAttribute('type', 'virtio')
    target_channel_spicevmc.setAttribute('name', 'com.redhat.spice.0')
    channel_spicevmc.appendChild(target_channel_spicevmc)
    address_channel_spicevmc = dom.createElement('address')
    address_channel_spicevmc.setAttribute('type', 'virtio-serial')
    address_channel_spicevmc.setAttribute('controller', '0')
    address_channel_spicevmc.setAttribute('bus', '0')
    address_channel_spicevmc.setAttribute('port', '2')
    channel_spicevmc.appendChild(address_channel_spicevmc)
    devices.appendChild(channel_spicevmc)

    input_tablet = dom.createElement('input')
    input_tablet.setAttribute('type', 'tablet')
    input_tablet.setAttribute('bus', 'usb')
    address_input_tablet = dom.createElement('address')
    address_input_tablet.setAttribute('type', 'usb')
    address_input_tablet.setAttribute('bus', '0')
    address_input_tablet.setAttribute('port', '1')
    input_tablet.appendChild(address_input_tablet)
    devices.appendChild(input_tablet)

    input_mouse = dom.createElement('input')
    input_mouse.setAttribute('type', 'mouse')
    input_mouse.setAttribute('bus', 'ps2')
    devices.appendChild(input_mouse)

    input_keyboard = dom.createElement('input')
    input_keyboard.setAttribute('type', 'keyboard')
    input_keyboard.setAttribute('bus', 'ps2')
    devices.appendChild(input_keyboard)

    graphics = dom.createElement('graphics')
    graphics.setAttribute('type', 'spice')
    graphics.setAttribute('autoport', 'yes')
    listen = dom.createElement('listen')
    listen.setAttribute('type', 'address')
    graphics.appendChild(listen)
    image = dom.createElement('image')
    image.setAttribute('compression', 'off')
    graphics.appendChild(image)
    devices.appendChild(graphics)

    sound = dom.createElement('sound')
    sound.setAttribute('model', 'ich9')
    address_sound = dom.createElement('address')
    address_sound.setAttribute('type', 'pci')
    address_sound.setAttribute('domain', '0x0000')
    address_sound.setAttribute('bus', '0x00')
    address_sound.setAttribute('slot', '0x1b')
    address_sound.setAttribute('function', '0x0')
    sound.appendChild(address_sound)
    devices.appendChild(sound)

    video = dom.createElement('video')
    model_video = dom.createElement('model')
    model_video.setAttribute('type', 'qxl')
    model_video.setAttribute('ram', '65536')
    model_video.setAttribute('vram', '65536')
    model_video.setAttribute('vgamem', '16384')
    model_video.setAttribute('heads', '1')
    model_video.setAttribute('primary', 'yes')
    video.appendChild(model_video)
    address_video = dom.createElement('address')
    address_video.setAttribute('type', 'pci')
    address_video.setAttribute('domain', '0x0000')
    address_video.setAttribute('bus', '0x00')
    address_video.setAttribute('slot', '0x01')
    address_video.setAttribute('function', '0x0')
    video.appendChild(address_video)
    devices.appendChild(video)

    redirdev_spicevmc1 = dom.createElement('redirdev')
    redirdev_spicevmc1.setAttribute('bus', 'usb')
    redirdev_spicevmc1.setAttribute('type', 'spicevmc')
    address_redirdev1 = dom.createElement('address')
    address_redirdev1.setAttribute('type', 'usb')
    address_redirdev1.setAttribute('bus', '0')
    address_redirdev1.setAttribute('port', '2')
    redirdev_spicevmc1.appendChild(address_redirdev1)
    devices.appendChild(redirdev_spicevmc1)

    redirdev_spicevmc2 = dom.createElement('redirdev')
    redirdev_spicevmc2.setAttribute('bus', 'usb')
    redirdev_spicevmc2.setAttribute('type', 'spicevmc')
    address_redirdev2 = dom.createElement('address')
    address_redirdev2.setAttribute('type', 'usb')
    address_redirdev2.setAttribute('bus', '0')
    address_redirdev2.setAttribute('port', '3')
    redirdev_spicevmc2.appendChild(address_redirdev2)
    devices.appendChild(redirdev_spicevmc2)

    memballoon = dom.createElement('memballoon')
    memballoon.setAttribute('model', 'virtio')
    address_memballoon = dom.createElement('address')
    address_memballoon.setAttribute('type', 'pci')
    address_memballoon.setAttribute('domain', '0x0000')
    address_memballoon.setAttribute('bus', '0x04')
    address_memballoon.setAttribute('slot', '0x00')
    address_memballoon.setAttribute('function', '0x0')
    memballoon.appendChild(address_memballoon)
    devices.appendChild(memballoon)

    rng = dom.createElement('rng')
    rng.setAttribute('model', 'virtio')
    backend_rng = dom.createElement('backend')
    backend_rng.setAttribute('model', 'random')
    backend_rng.appendChild(dom.createTextNode('/dev/urandom'))
    rng.appendChild(backend_rng)
    address_rng = dom.createElement('address')
    address_rng.setAttribute('type', 'pci')
    address_rng.setAttribute('domain', '0x0000')
    address_rng.setAttribute('bus', '0x05')
    address_rng.setAttribute('slot', '0x00')
    address_rng.setAttribute('function', '0x0')
    rng.appendChild(address_rng)
    devices.appendChild(rng)

    domain.appendChild(devices)

    try:
        with open(xml_path, 'w', encoding='UTF-8') as fh:
            dom.writexml(fh, indent='', addindent='', newl='', encoding='UTF-8')
            print('Write xml OK!')
    except Exception as err:
        print(f'Error message: {err}')

    conn = libvirt.open('qemu:///system')
    with open(xml_path, 'r') as xmlfile:
        xmlconfig = xmlfile.read()
    conn.defineXML(xmlconfig)