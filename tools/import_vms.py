#!/usr/bin/env python
# Import VMs from vSphere into Racktables
# by Stefan Midjich <swehack@gmail.com>
#
# See README.md for details.
# TODO: See if dialect='excel' can make use of the header in csv.reader() 
# See: (Sniffer.has_header())

from __future__ import print_function
from sys import stderr, exit
from ConfigParser import ConfigParser
import csv
import datetime
import ipaddr
import MySQLdb
import rtapi

config = ConfigParser()
config.read('import_vms.cfg')

# Helper method to return empty strings instead of None
def xstr(s):
    if s is None:
        return('')
    return str(s)

def grouper(iterable, n, fillvalue=None):
    from itertools import izip_longest
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

with open(vm_file, 'rb') as csvfile:
    conn = MySQLdb.connect(user=db_user, passwd=db_pass, db=db_name)
    rt = rtapi.RTObject(conn)

    lines = csv.reader(csvfile, delimiter=',', quotechar='"')

    for line in lines:
        object_added = False
        vm_name = line[0]
        vm_label = line[0]
        vm_interfaces = line[3:]

        # Get the VM type ID
        for (obj_id, obj_type) in rt.ObjectTypes:
            if obj_type == 'VM':
                vm_objtype = obj_id
                break
        else:
            print('Could not get VM object type ID', file=stderr)
            exit(1)

        # Check if object already exists
        if rt.ObjectExistName(vm_name):
            print('Object already exists, not adding: %s' % vm_name, file=stderr)
            object_id = rt.GetObjectId(vm_name)
        else:
            try:
                rt.AddObject(vm_name, vm_objtype, None, vm_label)
            except Exception as e:
                print('Failed adding object %s: %s' % (
                    vm_name, 
                    str(e),
                ), file=stderr)
                exit(1)

            print('Added object: %s' % vm_name)
            object_id = rt.GetObjectId(vm_name)
            rt.InsertLog(
                object_id, 
                'Object imported by script at %s' % datetime.datetime.now()
            )

        # Now proceed to update the object with network interfaces
        for if_data in grouper(vm_interfaces, 4, None):
            port_id = None
            (vlan, hwaddr, ipaddrs, ifname) = if_data

            # Add network interface name
            if ifname:
                port_id = rt.UpdateNetworkInterface(object_id, ifname)
            if port_id:
                print('Updated object %s with interface %s' % (vm_name, ifname))
            if not ipaddrs:
                continue

            # See if ipaddrs is valid
            try:
                _ip = ipaddr.IPv4Network('%s/24' % ipaddrs)
            except Exception as e:
                print('Could not add IPv4 address %s to object %s: %s' % (
                    ipaddrs, 
                    vm_name, 
                    str(e),
                ), file=stderr)
                continue

            # Add IP-address
            if rt.InterfaceAddIpv4IP(object_id, ifname, ipaddrs):
                print('Updated device %s on object %s with IP %s' % (
                    ifname, 
                    vm_name, 
                    ipaddrs,
                ))
