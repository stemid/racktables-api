#!/usr/bin/python
#
#   RTAPI
#   Racktables API is simple python module providing some methods 
#   for monipulation with racktables objects.
#
#   This utility is released under GPL v2
#   
#   Server Audit utility for Racktables Datacenter management project.
#   Copyright (C) 2012  Robert Vojcik (robert@vojcik.net)
#                 2015  Stefan Midjich (swehack@gmail.com)
#   
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Forked from Robert Vojcik by Stefan Midjich <swehack@gmail.com>

'''Python racktables API. 

This started as a fork of Robert Vojcik's API but has evolved into a complete rewrite. 

For proper function, some methods need ipaddr module (https://pypi.python.org/pypi/ipaddr)
'''
__author__ = "Stefan Midjich (swehack@gmail.com)"
__version__ = "0.20.8"
__copyright__ = "OpenSource"
__license__ = "GPLv2"

__all__ = ["Racktables"]

import re
import ipaddr

class Racktables(object):
    '''Racktables object. Require database object as argument. '''

    # Init method
    def __init__(self, dbobject):
        '''Initialize Object'''
        self.db = dbobject
        self.dbcursor = self.db.cursor()

    # DATABASE methods
    def db_query_one(self, sql, values=()):
        '''SQL query function, return one row. Require sql query as parameter'''
        self.dbcursor.execute(sql, values)
        return self.dbcursor.fetchone()

    def db_query_all(self, sql, values=()):
        '''SQL query function, return all rows. Require sql query as 
        parameter'''
        self.dbcursor.execute(sql, values)
        return self.dbcursor.fetchall()
    
    def db_insert(self, sql, values=()):
        '''SQL insert/update function. Require sql query as parameter'''
        self.dbcursor.execute(sql, values)
        self.db.commit()

    def db_fetch_lastid(self):
        '''SQL function which return ID of last inserted row.'''
        return self.dbcursor.lastrowid
    
    def Objects(self):
        sql = 'select id from Object'
        self.dbcursor.execute(sql)
        for object_id in self.dbcursor:
            yield RTObject(self.db, object_id)

    def ObjectTypes(self):
        '''List all object types'''
        # First find the ObjectType chapter ID
        sql = 'select id from Chapter where name=\'ObjectType\''
        chapter_id = self.db_query_one(sql)
        if not chapter_id:
            raise ValueError('Found not ObjectType Chapter ID')

        sql = '''select dict_key, dict_value 
        from Dictionary where chapter_id=%s'''
        self.dbcursor.execute(sql, (chapter_id,))
        for (object_id, object_name) in self.dbcursor:
            yield (object_id, object_name)

    def IPv4Networks(self):
        sql = 'select id from IPv4Network'
        networks = self.dbcursor.execute(sql)
        for row in self.dbcursor:
            _ip_network = IPv4Network(self.db, row[0])
            yield _ip_network

    def ObjectExistST(self, service_tag):
        '''Check if object exist in database based on asset_no'''
        sql = 'SELECT name FROM Object WHERE asset_no = %s'
        if self.db_query_one(sql, (service_tag,)) == None:
            return False
        else:
            return True
    
    def ObjectExistName(self, name):
        '''Check if object exist in database based on name'''
        sql = 'select id from Object where name = %s'
        self.dbcursor.execute(sql, (name,))
        object_id = self.dbcursor.fetchone()
        return RTObject(self.db, object_id)

    def ObjectExistSTName(self, name, asset_no):
        '''Check if object exist in database based on name'''
        sql = "SELECT id FROM Object WHERE name = %s AND asset_no = %s"
        if self.db_query_one(sql, (name, asset_no,)) == None:
            return False
        else:
            return True

    def AddObject(self, name, server_type_id, asset_no, label):
        '''Add new object to racktables'''
        self.db_insert('''
                       insert into Object 
                       (name, objtype_id, asset_no, label) 
                       values (%s, %s, %s, %s)
                      ''',
                      (name, server_type_id, asset_no, label,)
                     )
        object_id = self.db.lastrowid
        return RTObject(self.db, object_id)

    def UpdateObjectLabel(self,object_id,label):
        '''Update label on object'''
        sql = "UPDATE Object SET label = %s where id = %s"
        self.db_insert(sql, (label, object_id,))
    
    def UpdateObjectComment(self,object_id,comment):
        '''Update comment on object'''
        sql = "UPDATE Object SET comment = %s where id = %s"
        self.db_insert(sql, (comment, object_id,))

    def UpdateObjectName(self,object_id,name):
        '''Update name on object'''
        old_name = self.GetObjectName(object_id)
        sql = "UPDATE Object SET name = '%s' where id = %s"
        self.db_insert(sql, (name, object_id,))
        self.InsertLog(object_id, 'Name changed from %s to %s' % (
            old_name, name
        ))

    def GetObjectName(self,object_id):
        '''Translate Object ID to Object Name'''
        #Get interface id
        sql = "SELECT name FROM Object WHERE id = %s"
        result = self.db_query_one(sql, (object_id, ))
        if result != None:
            object_name = result[0]
        else:
            object_name = None

        return object_name
    
    def GetObjectLabel(self,object_id):
        '''Get object label'''
        #Get interface id
        sql = "SELECT label FROM Object WHERE id = %s"
        result = self.db_query_one(sql, (object_id, ))
        if result != None:
            object_label = result[0]
        else:
            object_label = None

        return object_label

    def GetObjectComment(self,object_id):
        '''Get object comment'''
        #Get interface id
        sql = "SELECT comment FROM Object WHERE id = %s"
        result = self.db_query_one(sql, (object_id, ))
        if result != None:
            object_comment = result[0]
        else:
            object_comment = None

        return object_comment

    def GetObjectId(self,name):
        '''Translate Object name to object id'''
        #Get interface id
        sql = "SELECT id FROM Object WHERE name = %s"
        result = self.db_query_one(sql, (name, ))
        if result != None:
            object_id = result[0]
        else:
            object_id = None

        return object_id

    # Logging
    def InsertLog(self,object_id,message):
        '''Attach log message to specific object'''
        sql = "INSERT INTO ObjectLog (object_id,user,date,content) VALUES (%s,'script',now(),%s)"
        self.db_insert(sql, (object_id, message,))

    # Attrubute methods
    def InsertAttribute(self,object_id,object_tid,attr_id,string_value,uint_value,name):
        '''Add or Update object attribute. 
        Require 6 arguments: object_id, object_tid, attr_id, string_value, uint_value, name'''
    
        # Check if attribute exist
        sql = "SELECT string_value,uint_value FROM AttributeValue WHERE object_id = %s AND object_tid = %s AND attr_id = %s"
        result = self.db_query_one(sql, (object_id, object_tid, attr_id, ))

        if result != None:
            # Check if attribute value is same and determine attribute type
            old_string_value = result[0]
            old_uint_value = result[1]
            same_flag = "no"
            attribute_type = "None"

            if old_string_value != None:
                attribute_type = "string"
                old_value = old_string_value
                if old_string_value == string_value:
                    same_flag = "yes"
            elif old_uint_value != None:
                attribute_type = "uint"
                old_value = old_uint_value
                if old_uint_value == uint_value:
                    same_flag = "yes"

            # If exist, update value
            new_value = ''
            if same_flag == "no":
                if attribute_type == "string":
                    sql = "UPDATE AttributeValue SET string_value = %s WHERE object_id = %s AND attr_id = %s AND object_tid = %s"
                    new_value = string_value
                    self.db_insert(sql, (string_value, object_id, attr_id, object_tid, ))
                if attribute_type == "uint":
                    sql = "UPDATE AttributeValue SET uint_value = %s WHERE object_id = %s AND attr_id = %s AND object_tid = %s"
                    new_value = uint_value
                    self.db_insert(sql, (uint_value, object_id, attr_id, object_tid, ))

        else:
            # Attribute not exist, insert new
            if string_value == "NULL":
                sql = "INSERT INTO AttributeValue (object_id,object_tid,attr_id,uint_value) VALUES (%s,%s,%s,%s)"
                self.db_insert(sql, (object_id,object_tid,attr_id,uint_value,))
            else:
                sql = "INSERT INTO AttributeValue (object_id,object_tid,attr_id,string_value) VALUES (%s,%s,%s,%s)"
                self.db_insert(sql, (object_id, object_tid, attr_id, string_value,))

    def GetAttributeId(self,searchstring):
        '''Search racktables database and get attribud id based on search string as argument'''
        sql = "SELECT id FROM Attribute WHERE name LIKE '%%%s%%'"
  
        result = self.db_query_one(sql, (searchstring,))

        if result != None:
            getted_id = result[0]
        else:
            getted_id = None

        return getted_id

    # Interfaces methods
    def GetInterfaceName(self,object_id,interface_id):
        '''Find name of specified interface. Required object_id and interface_id argument'''
        #Get interface id
        sql = "SELECT name FROM Port WHERE object_id = %s AND name = %s"
        result = self.db_query_one(sql, (object_id, interface_id,))
        if result != None:
            port_name = result[0]
        else:
            port_name = None

        return port_name

    def GetInterfaceId(self,object_id,interface):
        '''Find id of specified interface'''
        #Get interface id
        sql = "SELECT id,name FROM Port WHERE object_id = %s AND name = %s"
        result = self.db_query_one(sql, (object_id, interface,))
        if result != None:
            port_id = result[0]
        else:
            port_id = None

        return port_id

    def UpdateNetworkInterface(self,object_id,interface):
        '''Add network interfece to object if not exist'''

        sql = "SELECT id,name FROM Port WHERE object_id = %s AND name = %s"

        result = self.db_query_one(sql, (object_id, interface,))
        if result == None:
        
            sql = "INSERT INTO Port (object_id,name,iif_id,type) VALUES (%s,%s,1,24)"
            self.db_insert(sql, (object_id, interface,))
            port_id = self.db_fetch_lastid()

        else:
            port_id = result[0]

        return port_id

    def LinkNetworkInterface(self,object_id,interface,switch_name,interface_switch):
        '''Link two devices togetger'''
        #Get interface id
        port_id = self.GetInterfaceId(object_id,interface)
        if port_id != None:
            #Get switch object ID
            switch_object_id = self.GetObjectId(switch_name)
            if switch_object_id != None:
                switch_port_id = self.GetInterfaceId(switch_object_id,interface_switch)
                if switch_port_id != None:
                    if switch_port_id > port_id:
                        select_object = 'portb'
                    else:
                        select_object = 'porta'
                    sql = "SELECT %s FROM Link WHERE porta = %s OR portb = %s"
                    result = self.db_query_one(sql, (select_object, port_id, port_id,))
                    if result == None:
                        #Insert new connection
                        sql = "INSERT INTO Link (porta,portb) VALUES (%s, %s)"
                        self.db_insert(sql, (port_id, switch_port_id,))
                        resolution = True
                    else:
                        #Update old connection
                        old_switch_port_id = result[0]
                        if old_switch_port_id != switch_port_id:
                            sql = "UPDATE Link set portb = %s, porta = %s WHERE porta = %s OR portb = %s"
                            self.db_insert(sql, (switch_port_id, port_id, port_id, port_id,))
                            sql = '''SELECT Port.name as port_name, Object.name as obj_name 
                            FROM Port INNER JOIN Object ON Port.object_id = Object.id WHERE Port.id = %s'''
                            result = self.db_query_one(sql, (old_switch_port_id, ))
                            old_switch_port, old_device_link = result

                            text = "Changed link from %s -> %s" % (old_device_link,old_switch_port)
                            self.InsertLog(object_id,text)
                            resolution = True
                        resolution = None

                else:
                    resolution = None
            else:
                resolution = None

        else:
            resolution = None

        return resolution

    def InterfaceAddIpv4IP(self,object_id,device,ip):
        '''Add/Update IPv4 IP on interface'''

        sql = "SELECT INET_NTOA(ip) from IPv4Allocation WHERE object_id = %s AND name = %s"
        result = self.db_query_all(sql, (object_id,device,))

        if result != None:
            old_ips = result
        
        is_there = "no"
            
        for old_ip in old_ips:
            if old_ip[0] == ip:
                is_there = "yes"

        if is_there == "no":
            sql = "INSERT INTO IPv4Allocation (object_id,ip,name) VALUES (%s,INET_ATON(%s),%s)"
            self.db_insert(sql, (object_id, ip, device,))
            text = "Added IP %s on %s" % (ip,device)
            self.InsertLog(object_id,text)
            return True
        return False

    def InterfaceAddIpv6IP(self,object_id,device,ip):
        '''Add/Update IPv6 IP on interface'''
        #Create address object using ipaddr 
        addr6 = ipaddr.IPAddress(ip)
        #Create IPv6 format for Mysql
        ip6 = "".join(str(x) for x in addr6.exploded.split(':'))

        sql = "SELECT HEX(ip) FROM IPv6Allocation WHERE object_id = %s AND name = %s"
        result = self.db_query_all(sql, (object_id, device,))
        
        if result != None:
            old_ips = result

        is_there = "no"

        for old_ip in old_ips:
            if old_ip[0] != ip6:
                is_there = "yes"

        if is_there == "no":
            sql = "INSERT INTO IPv6Allocation (object_id,ip,name) VALUES (%d,UNHEX(%s),%s)"
            self.db_insert(sql, (object_id, ip6, device,))
            text = "Added IPv6 IP %s on %s" % (ip,device)
            self.InsertLog(object_id,text)


    
    def GetDictionaryId(self,searchstring):
        '''Search racktables dictionary using searchstring and return id of dictionary element'''
        sql = "SELECT dict_key FROM Dictionary WHERE dict_value LIKE '%%%s%%'"

        result = self.db_query_one(sql, (searchstring,))
        if result != None:
            getted_id = result[0]
        else:
            getted_id = None

        return getted_id

    def CleanVirtuals(self,object_id,virtual_servers):
        '''Clean dead virtuals from hypervisor. virtual_servers is list of active virtual servers on hypervisor (object_id)'''

        sql = "SELECT child_entity_id FROM EntityLink WHERE parent_entity_id = %s"

        result = self.db_query_all(sql, (object_id,))

        if result != None:
            old_virtuals_ids = result
            delete_virtual_id = []
            new_virtuals_ids = []
            # Translate names into ids
            for new_virt in virtual_servers:
                new_id = self.GetObjectId(new_virt)
                if new_id != None:
                    new_virtuals_ids.append(new_id)

            for old_id in old_virtuals_ids:
                try:
                    test = new_virtuals_ids.index(old_id[0])
                except ValueError:
                    delete_virtual_id.append(old_id[0]) 
        if len(delete_virtual_id) != 0:
            for virt_id in delete_virtual_id:

                sql = "DELETE FROM EntityLink WHERE parent_entity_id = %s AND child_entity_id = %s"
                self.db_insert(sql, (object_id, virt_id,))
                virt_name = self.GetObjectName(virt_id)
                logstring = "Removed virtual %s" % virt_name
                self.InsertLog(object_id,logstring)

    def CleanIPAddresses(self,object_id,ip_addresses,device):
        '''Clean unused ip from object. ip addresses is list of IP addresses configured on device (device) on host (object_id)'''

        sql = "SELECT INET_NTOA(ip) FROM IPv4Allocation WHERE object_id = %s AND name = %s"
        
        result = self.db_query_all(sql, (object_id, device, ))

        if result != None:
            old_ips = result
            delete_ips = []

            for old_ip in old_ips:
                try:
                    test = ip_addresses.index(old_ip[0])
                except ValueError:
                    delete_ips.append(old_ip[0]) 
        if len(delete_ips) != 0:
            for ip in delete_ips:
                sql = "DELETE FROM IPv4Allocation WHERE ip = INET_ATON(%s) AND object_id = %s AND name = %s"
                self.db_insert(sql, (ip, object_id, device,))
                logstring = "Removed IP %s from %s" % (ip,device)
                self.InsertLog(object_id,logstring)

    def CleanIPv6Addresses(self,object_id,ip_addresses,device):
        '''Clean unused ipv6 from object. ip_addresses mus be list of active IP addresses on device (device) on host (object_id)'''

        sql = "SELECT HEX(ip) FROM IPv6Allocation WHERE object_id = %s AND name = %s"
        result = self.db_query_all(sql, (object_id, device, ))

        if result != None:
            old_ips = result
            delete_ips = []
            new_ip6_ips = []

            #We must prepare ipv6 addresses into same format for compare
            for new_ip in ip_addresses:
                converted = ipaddr.IPAddress(new_ip).exploded.lower()
                new_ip6_ips.append(converted)


            for old_ip_hex in old_ips:
                try:
                    #First we must construct IP from HEX
                    tmp = re.sub("(.{4})","\\1:", old_ip_hex[0], re.DOTALL)
                    #Remove last : and lower string
                    old_ip = tmp[:len(tmp)-1].lower()

                    test = new_ip6_ips.index(old_ip)

                except ValueError:
                    delete_ips.append(old_ip)

        if len(delete_ips) != 0:
            for ip in delete_ips:
                db_ip6_format = "".join(str(x) for x in ip.split(':')) 
                sql = "DELETE FROM IPv6Allocation WHERE ip = UNHEX(%s) AND object_id = %s AND name = %s"
                self.db_insert(sql, (db_ip6_format, object_id, device,))
                logstring = "Removed IP %s from %s" % (ip,device)
                self.InsertLog(object_id,logstring)

    def LinkVirtualHypervisor(self,object_id,virtual_id):
        '''Assign virtual server to correct hypervisor'''
        sql = '''
        SELECT child_entity_id FROM EntityLink 
        WHERE parent_entity_id = %s AND 
        child_entity_id = %s
        '''
        result = self.db_query_one(sql, (object_id, virtual_id,))

        if result == None:
            sql = "INSERT INTO EntityLink (parent_entity_type, parent_entity_id, child_entity_type, child_entity_id) VALUES ('object',%s,'object',%s)"
            self.db_insert(sql, (object_id, virtual_id,))
            text = "Linked virtual %s with hypervisor" % self.GetObjectName(virtual_id)
            self.InsertLog(object_id,text)

    def AssignChassisSlot(self,chassis_name,slot_number,server_name):
        '''Assign server objects to server chassis'''
        chassis_id = self.GetObjectId(chassis_name)
        server_id = self.GetObjectId(server_name)
        slot_attribute_id = self.GetAttributeId("Slot number")

        # Assign slot number to server
        sql = "INSERT INTO AttributeValue (object_id,object_tid,attr_id,string_value) VALUES ( %s, 4, %s, %s)"
        try:
            self.db_insert(sql, (server_id, slot_attribute_id, slot_number,))
        except:
            pass

        # Assign server to chassis
        # Check if it's connected
        sql = "SELECT parent_entity_id FROM EntityLink WHERE child_entity_type = 'object' AND child_entity_id = %s"
        result = self.db_query_one(sql, (server_id,))

        if result != None:
        # Object is connected to someone
            if result[0] != chassis_id:
            # Connected to differend chassis/chassis
                sql = "UPDATE EntityLink SET parent_entity_id = %s WHERE child_entity_id = %s AND child_entity_type = 'object' AND parent_entity_id = %s"
                self.db_insert(sql, (chassis_id, server_id, result[0], ))

                old_object_name = self.GetObjectName(result[0])
                self.InsertLog(old_object_name, "Unlinked server %s" % (server_name))
                self.InsertLog(server_id, "Unlinked from Blade Chassis %s" % (old_object_name))
                self.InsertLog(chassis_id, "Linked with server %s" % (server_name))
                self.InsertLog(server_id, "Linked with Blade Chassis %s" % (chassis_name))
        
        else:
        # Object is not connected
            sql = "INSERT INTO EntityLink (parent_entity_type, parent_entity_id, child_entity_type, child_entity_id) VALUES ('object', %s, 'object', %s)"
            self.db_insert(sql, (chassis_id, server_id, ))
            self.InsertLog(chassis_id, "Linked with server %s" % (server_name))
            self.InsertLog(server_id, "Linked with Blade Chassis %s" % (chassis_name))
            
    def GetAllServerChassisId(self):
        '''Get list of all server chassis IDs'''
        sql = "SELECT object_id FROM AttributeValue WHERE attr_id = 2 AND uint_value = 994"
        return self.db_query_all(sql)

class RTObject(Racktables):
    '''This object represents an object in racktables db.'''

    def __init__(self, dbobject, object_id):
        self.rt = Racktables(dbobject)
        self.db = dbobject
        self.dbcursor = self.db.cursor()

        sql = '''
        select id, name, label, objtype_id, asset_no, has_problems, comment
        from Object where id = %s
        '''

        (
            self._id, 
            self._name,
            self._label,
            self._objtype_id,
            self._asset_no,
            self._has_problems,
            self._comment
        ) = self.rt.db_query_one(sql, (object_id,))

    def __repr__(self):
        return self._name

    def InsertLog(self, message):
        '''Attach log message to specific object'''
        sql = '''INSERT INTO ObjectLog (object_id,user,date,content) 
        VALUES (%s,'script',now(),%s)'''
        self.rt.db_insert(sql, (self._id, message,))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        old_name = self._name
        sql = "UPDATE Object SET name = '%s' where id = %s"
        self.rt.db_insert(sql, (new_name, object_id,))
        self.InsertLog(self._id, 'Name changed from %s to %s' % (
            old_name, name
        ))
        self._name = name

    def Delete(self):
        sql = 'delete from Object where id=%s'
        self.rt.db_insert(sql, (self._id,))

    def Tags(self):
        sql = 'select tag_id from TagStorage where entity_id = %s'
        tags = self.dbcursor.execute(sql, (self._id,))
        for tag_id in self.dbcursor:
            rt_tag = RTTag(self.db, tag_id)
            yield rt_tag

    def IPv4Allocations(self):
        sql = 'select ip from IPv4Allocation where object_id = %s'
        tags = self.dbcursor.execute(sql, (self._id,))
        for ip in self.dbcursor:
            allocation = IPv4Allocation(self.db, ip)
            yield allocation

    def ObjectTypeName(self):
        types = dict(self.ObjectTypes())
        return types[self._objtype_id]

class RTTag(RTObject):
    def __init__(self, dbobject, tag_id):
        self.rt = Racktables(dbobject)
        self.db = dbobject
        self.dbcursor = self.db.cursor()

        self._id = tag_id
        sql = 'select parent_id, tag from TagTree where id = %s'
        (
            self._parent_id,
            self._tag
        ) = self.rt.db_query_one(sql, (tag_id,))

    def __repr__(self):
        return self._tag

    def parent(self):
        return RTTag(self.db, self._parent_id)

    # Change name of tag
    @property
    def Tag(self):
        return self._tag

    @Tag.setter
    def Tag(self, new_name):
        sql = 'update TagTree set tag = %s where id = %s'
        self.dbcursor.execute(sql, (new_name, self._id,))

class IPv4Allocation(RTObject):
    def __init__(self, dbobject, ip):
        self.rt = Racktables(dbobject)
        self.db = dbobject
        self.dbcursor = self.db.cursor()

        self._id = ip
        sql = 'select object_id, INET_NTOA(ip), name, type from IPv4Allocation where ip = %s'
        (
            self._object_id,
            self._ip,
            self._name,
            self._type
        ) = self.rt.db_query_one(sql, (ip,))

    def __repr__(self):
        return self._ip

    def Object(self):
        return RTObject(self.db, self._object_id)

class IPv4Network(Racktables):
    # TODO: This should only require the ID of the network as argument.
    def __init__(self, dbobject, id):
        self.rt = Racktables(dbobject)
        self.db = dbobject
        self.dbcursor = self.db.cursor()

        self._id = id
        sql = 'select INET_NTOA(ip), mask, name from IPv4Network where id = %s'
        (
            self._ip,
            self._mask,
            self._name,
        ) = self.rt.db_query_one(sql, (id,))


    def __repr__(self):
        return '%s/%s' % (self._ip, self._mask)

