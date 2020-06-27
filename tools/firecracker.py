#!/usr/bin/env python3
#
# pip install requests-unixsocket
import sys
import os
import json
import subprocess
import signal
import time
import argparse
import json
import tempfile
import uuid
from datetime import datetime


verbose = False

devnull = open('/dev/null', 'w')

firecracker_path = "firecracker"


class Tap:
    """Functionality for creating a tap and cleaning up after it."""

    def __init__(self, tap_name, bridge_name):
        """Set up tap interface."""

        bridges = subprocess.check_output(['brctl', 'show']).decode('utf-8')
        if bridges.find(bridge_name) < 0:
            print("The bridge %s does not exist per brctl -> need to create one!" % bridge_name)
            setup_bridge(bridge_name, '172.16.0.1/24')

        subprocess.run(['sudo', 'ip', 'tuntap', 'add', 'dev', tap_name, 'mode', 'tap'])
        subprocess.run(['sudo', 'ip', 'link', 'set', 'dev', tap_name, 'up'])
        subprocess.run(['sudo', 'brctl', 'addif', bridge_name, tap_name])

        self.name = tap_name

    def __del__(self):
        """Destructor doing tap interface clean up."""
        subprocess.run(['sudo', 'ip', 'tuntap', 'del', 'dev', self.name, 'mode', 'tap'])


class FCInstance(object):
    def __init__(self, id, name=None):
        if name:
            self.name = name
        else:
            self.name = uuid.uuid4().hex[:8]

        self.ip = "172.16.0." + str(id)
        self.mac = mac_from_ip(self.ip)

        self.firecracker_config = {}     

    def __del__(self):
        os.remove(self.conf_file.name)

    # def configure(self, vcpu_count, mem_size_in_mb, kernel_path, cmdline, image_path, interface_name, bridge_name):
    #     self.add_machine_config(vcpu_count, mem_size_in_mb)
    #     self.add_boot_source(kernel_path, cmdline)
    #     self.add_disk(image_path)
    #     self.add_network_interface(interface_name, bridge_name)

    def add_machine_config(self, vcpu_count, mem_size_in_mb):
        machine_config = {
            'vcpu_count': vcpu_count,
            'mem_size_mib': mem_size_in_mb,
            'ht_enabled' : False
        }
        self.firecracker_config['machine-config'] = machine_config

    def add_boot_source(self, kernel_path, cmdline):
        cmdline = "--nopci %s" % cmdline
        cmdline = '--ip=eth0,%s,255.255.255.0 --defaultgw=172.16.0.1 --nameserver=172.16.0.1 %s' % (self.ip, cmdline)
        boot_source = {
            'kernel_image_path': kernel_path,
            'boot_args': cmdline
        }
        self.firecracker_config['boot-source'] = boot_source

    def add_disk(self, image_path):
        drive = {
            'drive_id': 'rootfs',
            'path_on_host': image_path,
            'is_root_device': False,
            'is_read_only': False
        }
        self.firecracker_config['drives'] = [drive]

    def add_network_interface(self, interface_name, bridge_name):
        self.tap = Tap('fc_tap' + self.name, bridge_name)
        interface = {
            'iface_id': interface_name,
            'host_dev_name': self.tap.name,
            'guest_mac': self.mac,
            'rx_rate_limiter': {
               'bandwidth': {
                  'size': 0,
                  'refill_time': 0
               },
               'ops': {
                  'size': 0,
                  'refill_time': 0
               }
            },
            'tx_rate_limiter': {
               'bandwidth': {
                  'size': 0,
                  'refill_time': 0
               },
               'ops': {
                  'size': 0,
                  'refill_time': 0
               }
            }
        }
        self.firecracker_config['network-interfaces'] = [interface]

    def add_logger(self):
        log_config = {
            "log_fifo": "log.fifo",
            "metrics_fifo": "metrics.fifo",
            "level": "Info",
            "show_level": True,
            "show_log_origin": True
        }
        self.firecracker_config['logger'] = log_config

    def firecracker_config_json(self):
        return json.dumps(self.firecracker_config, indent=3)

    def start(self):
        #  Start firecracker process and pass configuration JSON as a file
        self.conf_file = tempfile.NamedTemporaryFile(delete=False, prefix='fc', suffix='.conf')
        self.conf_file.write(bytes(self.firecracker_config_json(), 'utf-8'))
        self.conf_file.flush()
        self.firecracker = subprocess.Popen([firecracker_path, "--no-api", "--config-file", self.conf_file.name],
                            stdout=sys.stdout, stderr=subprocess.STDOUT)

    def wait(self):
        try:
            self.firecracker.wait()
        except KeyboardInterrupt:
            os.kill(self.firecracker.pid, signal.SIGINT)

    def stop(self):
        self.firecracker.kill()


def print_time(msg):
    if verbose:
        now = datetime.now()
        print("%s: %s" % (now.isoformat(), msg))

def setup_bridge(bridge_name, ip_and_mask):
    subprocess.run(['sudo', 'brctl', 'addbr', bridge_name])
    subprocess.run(['sudo', 'ip', 'link', 'set', 'dev', bridge_name, 'up'])
    subprocess.run(['sudo', 'ip', 'addr', 'add', ip_and_mask, 'dev', bridge_name])

def disk_path(qcow_disk_path):
    dot_pos = qcow_disk_path.rfind('.')
    raw_disk_path = qcow_disk_path[0:dot_pos] + '.raw'

    # Firecracker is not able to use disk image files in QCOW format
    # so we have to convert usr.img to raw format if the raw disk is missing
    # or source qcow file is newer
    if not os.path.exists(raw_disk_path) or os.path.getctime(qcow_disk_path) > os.path.getctime(raw_disk_path):
        ret = subprocess.call(['qemu-img', 'convert', '-O', 'raw', qcow_disk_path, raw_disk_path])
        if ret != 0:
            print('Failed to convert %s to a raw format %s!' % (qcow_disk_path, raw_disk_path))
            exit(-1)
    return raw_disk_path

def mac_from_ip(ip_address):
    """Create a MAC address based on the provided IP.
    Algorithm:
    - the first 2 bytes are fixed to 06:00
    - the next 4 bytes are the IP address
    Example of function call:
    mac_from_ip("192.168.241.2") -> 06:00:C0:A8:F1:02
    C0 = 192, A8 = 168, F1 = 241 and  02 = 2
    :param ip_address: IP address as string
    :return: MAC address from IP
    """
    mac_as_list = ['06', '00']
    mac_as_list.extend(
        list(
            map(
                lambda val: '{0:02x}'.format(int(val)),
                ip_address.split('.')
            )
        )
    )
    return "{}:{}:{}:{}:{}:{}".format(*mac_as_list)


def main(options):
    # Check if firecracker is installed
    cwd = os.getcwd()

    # Firecracker is installed so lets start
    print_time("Start")

    # Create API client and make API calls
    instance = FCInstance(options.id)

    # Prepare arguments we are going to pass when creating VM instance
    kernel_path = os.path.join(cwd, options.kernel)

    qemu_disk_path = os.path.join(cwd, options.image)
    raw_disk_path = disk_path(qemu_disk_path)

    cmdline = options.execute

    if options.verbose:
        cmdline = '--verbose ' + cmdline

    try:
        print_time("Firecracker ready")

        instance.add_machine_config(options.vcpus, options.memsize)
        print_time("Configured VM")

        instance.add_disk(raw_disk_path)
        print_time("Added disk")

        instance.add_network_interface('eth0', 'fc_br0')
        print_time("Added network interface")

        instance.add_boot_source(kernel_path, cmdline)
        print_time("Created OSv VM with cmdline: %s" % cmdline)

        instance.start()

    except Exception as e:
        print("Failed to run OSv on firecracker due to: %s" % e)
        instance.stop()
        exit(-1)

    print_time("Waiting for firecracker process to terminate")

    instance.wait()

    print_time("End")


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(prog='firecracker')
    parser.add_argument("-c", "--vcpus", action="store", type=int, default=1,
                        help="specify number of vcpus")
    parser.add_argument("-m", "--memsize", action="store", type=int, default=128,
                        help="specify memory size in MB")
    parser.add_argument("-e", "--execute", action="store", default=None, metavar="CMD",
                        help="overwrite command line")
    parser.add_argument("image", action="store",
                        help="path to disk image file.")
    parser.add_argument("-k", "--kernel", action="store", default="kernel.elf",
                        help="path to kernel loader file. defaults to kernel.elf")
    parser.add_argument("id", action="store", type=int,
                        help="unique id to set the vm's ip statically. range: [2:254]")
    parser.add_argument("-b", "--bridge", action="store", default="fc_br0",
                        help="bridge name for tap networking. defaults to fc_br0")
    parser.add_argument("-V", "--verbose", action="store_true",
                        help="pass --verbose to OSv, to display more debugging information on the console")

    cmd_args = parser.parse_args()
    if cmd_args.verbose:
        verbose = True
    main(cmd_args)
