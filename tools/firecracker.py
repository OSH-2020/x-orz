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
from random import randint
from datetime import datetime


verbose = False

devnull = open('/dev/null', 'w')


class Tap:
    """Functionality for creating a tap and cleaning up after it."""

    def __init__(self, tap_name, bridge_name):
        """Set up tap interface."""

        bridges = subprocess.check_output(['brctl', 'show']).decode('utf-8')
        if bridges.find(bridge_name) < 0:
            print("The bridge %s does not exist per brctl -> need to create one!" % bridge_name)
            setup_bridge(bridge_name)

        subprocess.run(['sudo','ip', 'tuntap', 'add', 'dev', tap_name, 'mode', 'tap'])
        subprocess.run(['ip', 'link', 'set', 'dev', tap_name, 'up'])
        subprocess.run(['brctl', 'addif', bridge_name, tap_name])

        self.name = tap_name

    def __del__(self):
        """Destructor doing tap interface clean up."""
        subprocess.run(['ip', 'tuntap', 'del', 'dev', self.name, 'mode', 'tap'])


class ApiException(Exception):
    pass


class ApiClient(object):
    def __init__(self, id, name=None, socket_less=True):
        if name:
            self.name = name
        else:
            self.name = uuid.uuid4().hex[:8]

        self.mac = ":".join(["%02x" % x for x in map(lambda x: randint(0, 255), range(6))])
        self.ip = "172.16.0." + str(id)

        self.socket_less = socket_less
        if socket_less:
            self.firecracker_config = {}
        else:
           import requests_unixsocket
           self.socket_path = "/tmp/fc" + self.name + ".socket"
           self.session = requests_unixsocket.Session()
        
        print_time("API socket-less: %s" % self.socket_less)

    def api_socket_url(self, path):
        return "http+unix://%s%s" % (self.socket_path, path)

    def make_put_call(self, path, request_body):
        url = self.api_socket_url(path)
        res = self.session.put(url, data=json.dumps(request_body))
        if res.status_code != 204:
            raise ApiException(res.text)
        return res.status_code

    def create_instance(self, kernel_path, cmdline):
        cmdline = "--nopci %s" % cmdline
        cmdline = '--ip=eth0,%s,255.255.255.0 --defaultgw=172.16.0.1 --nameserver=172.16.0.1 %s' % (self.ip, cmdline)
        boot_source = {
            'kernel_image_path': kernel_path,
            'boot_args': cmdline
        }
        if self.socket_less:
            self.firecracker_config['boot-source'] = boot_source
        else:
            self.make_put_call('/boot-source', boot_source)

    def add_disk(self, image_path):
        drive = {
            'drive_id': 'rootfs',
            'path_on_host': image_path,
            'is_root_device': False,
            'is_read_only': False
        }
        if self.socket_less:
            self.firecracker_config['drives'] = [drive]
        else:
            self.make_put_call('/drives/rootfs', drive)

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
        if self.socket_less:
            self.firecracker_config['network-interfaces'] = [interface]
        else:
            self.make_put_call('/network-interfaces/%s' % interface_name, interface)

    def start_instance(self):
        if self.socket_less == False:
            self.make_put_call('/actions', {
                'action_type': 'InstanceStart'
            })

    def configure_logging(self):
        log_config = {
            "log_fifo": "log.fifo",
            "metrics_fifo": "metrics.fifo",
            "level": "Info",
            "show_level": True,
            "show_log_origin": True
        }
        if self.socket_less:
            self.firecracker_config['logger'] = log_config
        else:
            self.make_put_call('/logger', log_config)

    def configure_machine(self, vcpu_count, mem_size_in_mb):
        machine_config = {
            'vcpu_count': vcpu_count,
            'mem_size_mib': mem_size_in_mb,
            'ht_enabled' : False
        }
        if self.socket_less:
            self.firecracker_config['machine-config'] = machine_config
        else:
            self.make_put_call('/machine-config', machine_config)

    def firecracker_config_json(self):
        return json.dumps(self.firecracker_config, indent=3)

def print_time(msg):
    if verbose:
        now = datetime.now()
        print("%s: %s" % (now.isoformat(), msg))

def setup_bridge(bridge_name):
    subprocess.run(['brctl', 'addbr', bridge_name])
    subprocess.run(['ip', 'link', 'set', 'dev', bridge_name, 'up'])
    subprocess.run(['ip', 'addr', 'add', '172.16.0.1/24', 'dev', bridge_name])

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


def start_firecracker(firecracker_path, socket_path):
    # Start firecracker process to communicate over specified UNIX socket file
    return subprocess.Popen([firecracker_path, '--api-sock', socket_path],
                           stdout=sys.stdout, stderr=subprocess.STDOUT)

def start_firecracker_with_no_api(firecracker_path, firecracker_config_json):
    #  Start firecracker process and pass configuration JSON as a file
    api_file = tempfile.NamedTemporaryFile(delete=False)
    api_file.write(bytes(firecracker_config_json, 'utf-8'))
    api_file.flush()
    return subprocess.Popen([firecracker_path, "--no-api", "--config-file", api_file.name],
                           stdout=sys.stdout, stderr=subprocess.STDOUT), api_file.name


def main(options):
    # Check if firecracker is installed
    cwd = os.getcwd()

    # Firecracker is installed so lets start
    print_time("Start")

    # Create API client and make API calls
    client = ApiClient(options.id, socket_less = not options.api)

    if options.api:
        firecracker = start_firecracker('firecracker', client.socket_path)

    # Prepare arguments we are going to pass when creating VM instance
    kernel_path = os.path.join(cwd, options.kernel)

    qemu_disk_path = os.path.join(cwd, options.image)
    raw_disk_path = disk_path(qemu_disk_path)

    cmdline = options.execute

    if options.verbose:
        cmdline = '--verbose ' + cmdline

    try:
        # Very often on the very first run firecracker process
        # is not ready yet to accept calls over socket file
        # so we poll existence of this file as a good
        # enough indicator if firecracker is ready
        if options.api:
            while not os.path.exists(client.socket_path):
                time.sleep(0.01)
        print_time("Firecracker ready")

        client.configure_machine(options.vcpus, options.memsize)
        print_time("Configured VM")

        client.add_disk(raw_disk_path)
        print_time("Added disk")

        client.add_network_interface('eth0', 'fc_br0')

        client.create_instance(kernel_path, cmdline)
        print_time("Created OSv VM with cmdline: %s" % cmdline)

        if not options.api:
            firecracker, config_file_path = start_firecracker_with_no_api("firecracker", client.firecracker_config_json())
        else:
            client.start_instance()
            print_time("Booted OSv VM")

    except Exception as e:
        print("Failed to run OSv on firecracker due to: %s" % e)
        firecracker.kill()
        exit(-1)

    print_time("Waiting for firecracker process to terminate")
    try:
        firecracker.wait()
    except KeyboardInterrupt:
        os.kill(firecracker.pid, signal.SIGINT)

    if options.api:
        os.remove(client.socket_path)
    else:
        os.remove(config_file_path)
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
    # parser.add_argument("-n", "--networking", action="store_true",
    #                     help="needs root to setup tap networking first time")
    parser.add_argument("id", action="store", type=int,
                        help="unique id to set the vm's ip statically. range: [2:254]")
    parser.add_argument("-b", "--bridge", action="store", default="fc_br0",
                        help="bridge name for tap networking. defaults to fc_br0")
    parser.add_argument("-V", "--verbose", action="store_true",
                        help="pass --verbose to OSv, to display more debugging information on the console")
    parser.add_argument("-a", "--api", action="store_true",
                        help="use socket-based API to configure and start OSv on firecracker")
    parser.add_argument("-p", "--physical_nic", action="store", default=None,
                        help="name of the physical NIC (wired or wireless) to forward to if in natted mode")

    cmd_args = parser.parse_args()
    if cmd_args.verbose:
        verbose = True
    main(cmd_args)
