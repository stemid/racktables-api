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
config.readfp(open('import_vms.cfg'))
config.read(['import_vms.cfg.local'])

with open(vm_file, 'rb') as csvfile:
    conn = MySQLdb.connect(
        host=config.get('DEFAULT', 'db_host'), 
        user=config.get('DEFAULT', 'db_user'), 
        passwd=config.get('DEFAULT', 'db_pass'), 
        db=config.get('DEFAULT', 'db_name')
    )
    rt = rtapi.Racktables(conn)

    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    lines = csv.DictReader(csvfile, dialect=dialect)

    for line in lines:
        object_added = False
        vm_name = line['Name']
        vm_label = line['Name']
        vm_interfaces = line['NIC'].split(',')
        vm_ipaddresses = line['IP'].split(',')
        vm_vlans = line['VLAN'].split(',')

        # Get the VM type ID
        for (obj_id, obj_type) in rt.ObjectTypes():
            if obj_type == 'VM':
                vm_objtype = obj_id
                break
        else:
            print('Could not get VM object type ID', file=stderr)
            exit(1)

        rtobject = None
        # Check if object already exists
        rtobject = rt.ObjectExistName(vm_name)
        if rtobject:
            print('Object already exists, not adding: %s' % vm_name, file=stderr)
            # This is temporary code to replace all names with new naming 
            # standard.
            new_name = '%s-%s' % (line['Folder'], line['Name'])
            rtobject.UpdateName(new_name)
        else:
            try:
                rtobject = rt.AddObject(vm_name, vm_objtype, None, vm_label)
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
        for ifname in vm_interfaces:
            port_id = None

            # Add network interface name
            if ifname:
                port_id = rt.UpdateNetworkInterface(object_id, ifname)
            if port_id:
                print('Updated object %s with interface %s' % (vm_name, ifname))

        for ipaddrs in vm_ipaddresses:
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
