#!/usr/bin/env python3.5.2

#############################################
#               REFERENCES                  #
#############################################

# http://pubs.vmware.com/vsphere-60/topic/com.vmware.wssdk.apiref.doc/right-pane.html
# https://pubs.vmware.com/vsphere-50/index.jsp#com.vmware.wssdk.pg.doc_50/PG_ChB_Using_MOB.20.2.html?path=5_0_1_17_0_0#994707
# http://velemental.com/2012/03/09/a-deep-dive-doing-it-the-manual-way-with-vmware-vim-and-powershell/
# https://github.com/vmware/pyvmomi/blob/master/tests/fixtures/basic_connection.yaml
# https://pubs.vmware.com/vsphere-50/index.jsp#com.vmware.wssdk.pg.doc_50/PG_Ch4_Introduction_Inventory.6.3.html


#############################################
#                 SSLCERT                   #
#############################################

# mkdir keys
# cd keys
# openssl genrsa -des3 -out server.key 1024
# openssl req -new -key server.key -out server.csr
# openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
# openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mycert.pem -out mycert.pem

import argparse
import datetime
import json
import logging
import lxml
import ssl
import subprocess
import uuid
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element as E
from xml.etree.ElementTree import SubElement as SE
from xml.etree.ElementTree import tostring as TS
import xml.dom.minidom
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pprint import pprint

from lib.utils import *
from lib.datasets.vm import *

USERNAME = 'administrator@vsphere.local'
PASSWORD = 'vmware1234'
#PORT = 443

# https://192.168.121.129/mob/?moid=domain-s44
INVENTORY = {
         'datacenters': {
              'datacenter-2': {
                'name': "datacenter1",
                'hosts': ['host-9', 
                          'host-16'],
                'vmFolder': 'group-v3',
                'folders': {
                    'group-d1': ['datacenter-2'],
                    'group-h4': ['domain-s42', 
                                 'domain-s44'],
                    'group-n6': ['network-11'],
                    'group-s5': ['datastore-10', 
                                 'datastore-17'],
                    'group-v3': ['group-v15', 
                                 'group-v12', 
                                 'group-v49', 
                                 'vm-20'] 
                }
             }
         },
         'clusters': {}, 
         'clustercomputeresources': {},
         'computeresources': {
            'domain-s42': {
                'name': '192.168.121.130',
                'host': 'host-16',
            },
            'domain-s44': {
                'name': '192.168.121.128',
                'host': 'host-9',
                'resourcePool': 'resgroup-45'
            }
         },
         'folders': {
            'group-v3': {
                'name': 'vm',
                'children': [
                    'vm-20',
                    'group-v12',
                    'group-v49'
                ]    
            },
            'group-v12': {
                'name': 'testvms',
                'children': [
                ]
            },
            'group-v49': {
                'name': 'testvms2'
            },
            'group-v50': {
                'name': 'testvms1'
            },
            'group-v154': {
                'name': 'testvms2_1'
            }
         },
         'hosts':{
                    'host-9': {
                               'name': '192.168.121.128',
                               'vms': [],
                               'datastores': ['datastore-10']
                              },
                    'host-16': {
                               'name': '192.168.121.130',
                               'vms': [],
                               'datastores': ['datastore-17']
                              },

         }, 
         'resourcepool': {
                'resgroup-43': {
                    'name': 'Resources',
                    'owner': 'domain-s42',
                    'vm': []
                 },
                'resgroup-45': {
                    'name': 'Resources',
                    'owner': 'domain-s44',
                    'vm': []
                 },
         },
         'datastores': {
                'datastore-10': {'name': 'datastore1'},
                'datastore-17': {'name': 'datastore2'},
         },
         'networks': {
                'network-11': {
                    'name': 'VM Network'
                }
         },
         'vm': {
            'vm-20': {
                '_meta': {
                    'guestState': 'notrunning', 
                    'powerState': 'poweredOff', 
                    'ipAddress': '', 
                    'uuid': '4211dc52-25bf-981a-7ba8-729436f9b699', 
                    'template': True
                },
                'parent': 'group-v3',
                'name': "template_el7",
                'guest': {},
                'network': ['network-11'],
                'resourcePool': None,
                'datastore': ["datastore-10"]
            }
         }
}

'''
INVENTORY = {
             'datacenters': {
                              'datacenter-2': {
                                'name': "DC2",
                                'hosts': ['host-2', 'host-3'],
                                'folders': {
                                    'group-v0': {}
                                }
                              },
                              'datacenter-1': {
                                'name': "DC1",
                                'hosts': ['host-0', 'host-1'],
                                'folders': {
                                    'group-v0': {
                                        'name': 'vm',
                                        'id': 'group-v0',
                                        'group-v1': {
                                            'name': 'folder1',
                                            'id': 'group-v1',
                                            'vms': ['vm-0', 'vm-1'],
                                        },
                                        'group-v2': {
                                            'name': 'folder2',
                                            'id': 'group-v2',
                                            'vms': ['vm-2'],
                                        },
                                        'group-v3': {
                                            'name': 'testvms',
                                            'id': 'group-v3',
                                            'vms': ['vm-3']
                                        }
                                    }
                                }
                              }
             },
             'clusters': {}, 
             'computeresources': {
                'domain-s0': {
                    'hosts': ['host-0', 'host-1', 'host-2']
                }
             },
             'hosts':{
                        'host-0': {
                                   'name': '10.10.10.1',
                                   'vms': ['vm-0', 'vm-2', 'vm-5'],
                                   'datastores': ['datastore-0']
                                  },
                        'host-1': {
                                   'name': '10.10.10.2',
                                   'vms': ['vm-1', 'vm-3'],
                                   'datastores': ['datastore-1']
                                  },
                        'host-2': {
                                   'name': '10.10.10.3',
                                   'vms': [],
                                   'datastores': ['datastore-2']
                                  },
                        'host-3': {
                                   'name': '10.10.10.4',
                                   'vms': [],
                                   'datastores': ['datastore-3']
                                  }
                     }, 
             'resourcepool': {
                    'resgroup-0': {
                        'name': 'Resources'
                     }
             },
             'datastores': {
                    'datastore-0': {'name': "data_store_0"},
                    'datastore-1': {'name': "data_store_1"},
             },
             'networks': {
                    'network-0': {
                        'name': 'VM Network'
                    }
             },
             'vm': {
                     'vm-0': {
                        '_meta': {
                            'guestState': 'running', 
                            'ipAddress': '', 
                            'uuid': '421061cd-ae1b-a90a-9c2b-05a2df878849', 
                            'template': True
                        },
                        'name': "template_el7",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-0"]
                     },
                     'vm-1': {

                        '_meta': {'guestState': 'running', 'ipAddress': '10.0.0.101', 'uuid': '421061cd-ae1b-a90a-9c2b-05a2df878851'},
                        'name': "testvm1",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-0"]
                     },
                     'vm-2': {
                        '_meta': {'guestState': 'running', 'ipAddress': '10.0.0.102', 'uuid': '421061cd-ae1b-a90a-9c2b-05a2df878852'},
                        'name': "testvm2",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-0"]
                     },
                     'vm-3': {
                        '_meta': {'guestState': 'running', 'ipAddress': '10.0.0.103', 'uuid': '421061cd-ae1b-a90a-9c2b-05a2df878853'},
                        'name': "testvm3",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-1"]
                     },
                     'vm-4': {
                        '_meta': {'guestState': 'running', 'ipAddress': '10.0.0.104', 'uuid': '421061cd-ae1b-a90a-9c2b-05a2df878854'},
                        'name': "testvm4",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-1"]
                     }
                 }
        }
'''

#############################################
#            CLIENT SESSIONS                #
#############################################

EVENTCHAINS = {}
TASKS = {}
VIEWMANAGERS = {}
CONTAINERVIEWS = {}


class VCenter(BaseHTTPRequestHandler):

    def do_REST(self, method, path, data=None):
        # ['POST', '/xapi/inventory', 'HTTP/1.1']

        # default empty response
        resp = json.dumps({})

        # what is the resource being called?
        xparts = path.split('/')
        xparts = [x for x in xparts if x]

        if xparts[1] == 'inventory':

            if method == 'POST':
                # assume the caller wants to increase the inventory size
                pdict = json.loads(data)
                extend_inventory(**pdict)

            elif method == 'GET':
                if len(xparts) == 2:
                    resp = json.dumps(INVENTORY)
                else:
                    import pdb; pdb.set_trace()
            else:
                pass

        else:
            print('%s not yet handled in REST api' % xparts)
            import pdb; pdb.set_trace()

        rc = 200
        self.send_response(rc)
        self.send_header("Content-type", "text/json")
        self.send_header("msg", "OK")
        self.end_headers()
        self.wfile.write(bytes(resp, 'utf-8'))


    def do_GET(self):


        # 'GET /sdk/vimServiceVersions.xml HTTP/1.1'
        requestline = self.requestline
        rparts = requestline.split()
        url = rparts[1]

        if url == '/sdk/vimServiceVersions.xml':
            self.send_response(200)
            self.send_header("Content-type", "text/xml")

            f = open('fixtures/vc550_vimServiceVersions.xml', 'r')
            fdata = f.read()
            f.close()
            self.wfile.write(bytes(fdata, 'utf-8'))

            #self.wfile.write(bytes(vimServiceVersions, 'utf-8'))
        else:
            print("#######################################")
            print(" UNKNOWN PATH: %s" % url)
            print("#######################################")
            import pdb; pdb.set_trace()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Title goes here.</title></head>", "utf-8"))
            self.wfile.write(bytes("<body><p>This is a test.</p>", "utf-8"))
            self.wfile.write(bytes("<p>You accessed path: %s</p>" % self.path, "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))

    def do_POST(self):


        requestline = self.requestline
        rparts = requestline.split()
        url = rparts[1]

        postdata = self.rfile.read(int(self.headers['Content-Length']))
        postdata = postdata.decode("utf-8")

        # REST SHIM ...
        if url.startswith('/xapi'):
            logging.debug('REST POST %s' % url)
            self.do_REST('POST', url, data=postdata)
            return None

        # Convert POST XML to dict
        query = xml2dict(postdata)

        logging.debug("# QUERY START")
        logging.debug(json.dumps(query, indent=2))
        logging.debug("# QUERY END")

        rc = 200 #http returncode

        # What is the method being called?
        methodCalled = list(query['Body'].keys())[0]
        logging.debug('methodCalled: %s' % methodCalled)

        if hasattr(self, methodCalled):
            # call the method
            caller = getattr(self, methodCalled)
            resp = caller(postdata, query)
            if type(resp) == tuple:
                rc = resp[1]
                resp = resp[0]

        else:
            print('##################################################')
            print('UNKNOWN METHOD: %s' % methodCalled)
            print('##################################################')
            import pdb; pdb.set_trace()


        logging.debug("# RESPONSE START")
        splitxml(resp)
        logging.debug("# RESPONSE END")

        self.send_response(rc)
        self.send_header("Content-type", "text/xml")
        if rc == 200:
            self.send_header("msg", "OK")
        else:
            self.send_header("msg", "Internal Server Error")
        self.end_headers()

        #try:
        #    bytes(resp, 'utf-8')
        #except TypeError:
        #    import pdb; pdb.set_trace()

        if type(resp) == bytes:
            self.wfile.write(resp)
        else:
            self.wfile.write(bytes(resp, 'utf-8'))


    def __combine_soap_resp(self, rtype, urn, rval):
        # <LoginResponse xmlns=\"urn:vim25\">
        resp = ''
        resp += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        resp += envelope_header + '\n'
        resp += "<soapenv:Body>" + '\n'
        resp += "<%s xmlns=\"urn:%s\">" % (rtype, urn)+ '\n' 
        resp += rval
        resp += "</%s>" % rtype + '\n'
        resp += "</soapenv:Body>" + '\n'
        resp += envelope_footer + '\n'
        return resp

    def RetrieveServiceContent(self, postdata, query):
        f = open('fixtures/vc550_RetrieveServiceContentResponse.xml', 'r')
        fdata = f.read()
        f.close()
        return fdata

    def Login(self, postdata, query):
        inusername = query.get('Body').get('Login').get('userName')
        inpassword = query.get('Body').get('Login').get('password')

        rc = 200
        if inusername == USERNAME and inpassword == PASSWORD:
            f = open('fixtures/vc550_LoginResponse.xml', 'r')
            xml = f.read()
            f.close()
        else:
            rc = 500
            xml = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<soapenv:Envelope 
    xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\"
    xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"
    xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
    xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
<soapenv:Body>
<soapenv:Fault>
    <faultcode>ServerFaultCode</faultcode>
    <faultstring>Cannot complete login due to an incorrect user name or password.</faultstring>
    <detail>
        <InvalidLoginFault xmlns=\"urn:vim25\" xsi:type=\"InvalidLogin\">
        </InvalidLoginFault>
    </detail>
</soapenv:Fault>
</soapenv:Body>
</soapenv:Envelope>'''
        return (xml, rc)

    def Logout(self, postdata, query):
        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        LResponse = SE(Body, 'LogoutResponse')
        LResponse.set('xmlns', "urn:vim25")
        fdata = TS(X).decode("utf-8")
        return (fdata, 200)

    def DestroyView(self, postdata, query):
        global CONTAINERVIEWS
        print("DESTROYVIEW")
        print(postdata)
        print(query)
        key = query.get('Body', {}).get('DestroyView', {}).get('_this', None)
        if key:
            CONTAINERVIEWS.pop(key, None)    

        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        destroyResponse = SE(Body, 'DestroyViewResponse')
        destroyResponse.set('xmlns', 'urn:vim25')
        fdata = TS(X).decode("utf-8")
        return fdata


    def CreateContainerView(self, postdata, query):

        # A container view is a request for some type of object
        # The response should be a session number which the
        # client will later request the results for.

        global CONTAINERVIEWS

        # What is the sessionid going to be?
        #   session[0bc77834-77fc-7422-e2cd-81d4e5127926]52ef3fa7-892d-d0c0-d12d-7f16d61aa6e2
        sessionid = uuid.uuid4()
        sessionid2 = uuid.uuid4()
        sessionid = 'session[' + str(sessionid) + ']' + str(sessionid2)

        # What does the requester want?
        qobject = query.get('Body').get('CreateContainerView').get('container')
        qtype = query.get('Body').get('CreateContainerView').get('type')

        # Store this for future reference ...
        CONTAINERVIEWS[sessionid] = {'container': qobject, 'type': qtype}

        # Build the SOAP response ...
        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        CreateContainerViewResponse = SE(Body, 'CreateContainerViewResponse')
        CreateContainerViewResponse.set('xmlns', 'urn:vim25')
        returnval = SE(CreateContainerViewResponse, 'returnval')
        returnval.set('type', 'ContainerView')
        returnval.text = sessionid

        fdata = TS(X).decode("utf-8")
        return fdata


    def RetrieveProperties(self, postdata, query):

        ## SOMETIMES A SELECTSET IS GIVEN
        # 'specSet': {'objectSet': {'obj': 'group-d1',
        # 'selectSet': {'name': 'resource_pool_vm_traversal_spec',
        # 'path': 'vm',
        # 'type': 'ResourcePool'}},
        # 'propSet': {'type': 'HostSystem'}

        ## SOMETIMES JUST A PROPSET
        # specSet': {'objectSet': {'obj': 'host-28'}
        # 'propSet': {'type': 'HostSystem'}

        requested = None
        select_path = None
        propset_path = None
        propset_type = None
        try:
            requested = query.get('Body').get('RetrieveProperties').get('specSet').get('objectSet').get('obj')
        except:
            pass
        try:
            select_path = query.get('Body').get('RetrieveProperties').get('specSet')\
                               .get('objectSet').get('selectSet').get('path')
        except:
            pass
        try:
            propset_path = query.get('Body').get('RetrieveProperties').get('specSet').get('propSet').get('pathSet')
        except:
            pass
        try:
            propset_type = query.get('Body').get('RetrieveProperties').get('specSet').get('propSet').get('type')
        except:
            pass


        if 'TraversalSpec' in postdata:
            #print("# TRAVERSALSPEC ...")
            # https://www.vmware.com/support/developer/vc-sdk/visdk2xpubs/ReferenceGuide/vmodl.query.PropertyCollector.TraversalSpec.html
            #root = ET.fromstring(postdata)
            #body = root[1]
            #rprops = body.getchildren()
            #import pdb; pdb.set_trace()

            # Just return a list of HostSystems with VM properties?
            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, 'RetrievePropertiesResponse')
            RPResponse.set('xmlns', "urn:vim25")

            for k,v in INVENTORY['hosts'].items():

                this_rval = E("returnval")
                this_obj = SE(this_rval, 'obj')
                this_obj.set('type', 'HostSystem')
                this_obj.text = k
                this_propset = SE(this_rval, 'propSet')
                this_name = SE(this_propset, 'name')
                this_name.text = 'name'
                this_val = SE(this_propset, 'val')
                this_val.set('xsi:type', 'ArrayOfManagedObjectReference')

                for vm in v['vms']:
                    MO = E('ManagedObjectReference')
                    MO.set('type', 'VirtualMachine')
                    MO.set('xsi:type', 'ManagedObjectReference')
                    MO.text = vm
                    this_val.append(MO)

                RPResponse.append(this_rval)

            fdata = TS(X).decode("utf-8")
                   

        elif requested == 'group-d1':
            # This is a request for the known datacenters
            print("# DATACENTERS ...")
            if propset_type == 'HostSystem' and propset_path == 'name':

                # FIXME - is this asking for a list of VMs or hostsystems?
                # What host's VMs does it want?

                print("# DATACENTERS :: HOSTSYSTEM :: NAME ...")

                X = self._get_soap_element()
                Body = SE(X, 'soapenv:Body')
                RPResponse = SE(Body, 'RetrievePropertiesResponse')
                RPResponse.set('xmlns', "urn:vim25")
                ReturnVal = SE(RPResponse, "returnval")


                if select_path == 'vm':
                    # This req wants a list of VMs for a the given host (whch host?)
                    import pdb; pdb.set_trace()

                else:

                    OType = SE(ReturnVal, 'obj')
                    OType.set('type', "HostSystem")
                    OType.text = 'group-d1'
                    PropSet = SE(ReturnVal, 'propSet')
                    PName = SE(PropSet, 'name')
                    PName.text = 'name'
                    PVal = SE(PropSet, 'val')
                    PVal.set('xsi:type', "xsd:ArrayOfManagedObjectReference")

                    for k,v in INVENTORY['datacenters'].items():
                        MO = E('ManagedObjectReference')
                        MO.set('type', 'Datacenter')
                        MO.set('xsi:type', 'ManagedObjectReference')
                        MO.text = k
                        PVal.append(MO)

                # Make into string 
                fdata = TS(X).decode("utf-8")


            elif propset_type == 'HostSystem' and propset_path == 'vm':

                print("# DATACENTERS :: HOSTSYSTEM :: VM ...")

                X = self._get_soap_element()
                Body = SE(X, 'soapenv:Body')
                RPResponse = SE(Body, 'RetrievePropertiesResponse')
                RPResponse.set('xmlns', "urn:vim25")

                for k,v in INVENTORY['hosts'].items():

                    ReturnVal = E("returnval")
                    OType = SE(ReturnVal, 'obj')
                    OType.set('type', "HostSystem")
                    OType.text = k
                    PropSet = SE(ReturnVal, 'propSet')
                    PName = SE(PropSet, 'name')
                    PName.text = 'name'
                    PVal = SE(PropSet, 'val')
                    PVal.set('xsi:type', "xsd:string")
                    PVal.text = v['name']
                    RPResponse.append(ReturnVal)

                # Make into string 
                fdata = TS(X).decode("utf-8")


            elif propset_type == 'Folder' and propset_path == 'name':

                print("# DATACENTERS :: FOLDER :: NAME ...")

                print("# ROOT Folder ...")
                X = self._get_soap_element()
                Body = SE(X, 'soapenv:Body')
                RPResponse = SE(Body, 'RetrievePropertiesResponse')
                RPResponse.set('xmlns', "urn:vim25")
                ReturnVal = SE(RPResponse, "returnval")
                OType = SE(ReturnVal, 'obj')
                OType.set('type', "Folder")
                OType.text = 'group-d1'
                PropSet = SE(ReturnVal, 'propSet')
                PName = SE(PropSet, 'name')
                PName.text = 'name'
                PVal = SE(PropSet, 'val')
                PVal.set('xsi:type', "xsd:string")
                PVal.text = 'Datacenters'

                # Make into string 
                fdata = TS(X).decode("utf-8")

            elif propset_type == 'Datacenter' and propset_path == 'name':

                print("# ROOT Folder ...")
                X = self._get_soap_element()
                Body = SE(X, 'soapenv:Body')
                RPResponse = SE(Body, 'RetrievePropertiesResponse')
                RPResponse.set('xmlns', "urn:vim25")

                for k,v in INVENTORY['datacenters'].items():

                    ReturnVal = E("returnval")
                    OType = SE(ReturnVal, 'obj')
                    OType.set('type', "Datacenter")
                    OType.text = k
                    PropSet = SE(ReturnVal, 'propSet')
                    PName = SE(PropSet, 'name')
                    PName.text = 'name'
                    PVal = SE(PropSet, 'val')
                    PVal.set('xsi:type', "xsd:string")
                    PVal.text = v['name']

                    RPResponse.append(ReturnVal)

                # Make into string 
                fdata = TS(X).decode("utf-8")


            else:
                import pdb; pdb.set_trace()


        elif propset_type == 'ServiceInstance' and propset_path == 'content':

            #print("# (1) USING DEFAULT PROPERTIES RESP")
            #f = open('fixtures/vc550_RetrievePropertiesResponse.xml', 'r')
            #f = open('fixtures/vc550_RetrieveServiceContentResponse.xml.bak', 'r')
            f = open('fixtures/vc550_RetrievePropertiesResponse_ServiceInstance_ServiceContent.xml', 'r')
            fdata = f.read()
            f.close()

        elif propset_type == 'HostSystem' and propset_path == 'vm':

            # make list of VMs for the host
            host = requested
            #print("# MAKING HOST W/ VMLIST")

            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, 'RetrievePropertiesResponse')
            RPResponse.set('xmlns', "urn:vim25")
            ReturnVal = SE(RPResponse, "returnval")

            OType = SE(ReturnVal, 'obj')
            OType.set('type', "HostSystem")
            OType.text = "host-28"

            PropSet = SE(ReturnVal, 'propSet')

            PName = SE(PropSet, 'name')
            PName.text = 'vm'

            PVal = SE(PropSet, 'val')
            PVal.set('xsi:type', "ArrayOfManagedObjectReference")

            # Iterate through the VMs and add them as children to the Val
            for vm in INVENTORY['hosts'][host]['vms']:
                MO = E('ManagedObjectReference')
                MO.set('type', 'VirtualMachine')
                MO.set('xsi:type', 'ManagedObjectReference')
                MO.text = vm
                PVal.append(MO)

            # Make into string
            fdata = TS(X).decode("utf-8")

        elif propset_type == 'HostSystem' and propset_path == 'name':
            #print("# MAKING NAME PROP FOR HOST:%s" % requested)
            host = requested
            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, 'RetrievePropertiesResponse')
            RPResponse.set('xmlns', "urn:vim25")

            ReturnVal = SE(RPResponse, "returnval")

            OType = SE(ReturnVal, 'obj')
            OType.set('type', "HostSystem")
            OType.text = host

            PropSet = SE(ReturnVal, 'propSet')

            PName = SE(PropSet, 'name')
            PName.text = 'name'
            PVal = SE(PropSet, 'val')
            PVal.set('xsi:type', "xsd:string")
            PVal.text = INVENTORY['hosts'][host]['name']

            # Make into string 
            fdata = TS(X).decode("utf-8")


        elif propset_type == 'VirtualMachine' and propset_path == 'name':

            # need to return the name of the object        
            #print("# MAKING NAME PROP FOR VM:%s" % requested)
            vm = requested
            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, 'RetrievePropertiesResponse')
            RPResponse.set('xmlns', "urn:vim25")

            ReturnVal = SE(RPResponse, "returnval")

            OType = SE(ReturnVal, 'obj')
            OType.set('type', "VirtualMachine")
            OType.text = vm

            PropSet = SE(ReturnVal, 'propSet')

            PName = SE(PropSet, 'name')
            PName.text = 'name'
            PVal = SE(PropSet, 'val')
            PVal.set('xsi:type', "xsd:string")
            PVal.text = INVENTORY['vm'][vm]['name']

            # Make into string 
            fdata = TS(X).decode("utf-8")

        elif propset_type == 'ResourcePool' and propset_path == 'name':

            X = self.get_soap_properties_response('resourcepool', propset_type, requested, 'name', 'Resources') 
            fdata = TS(X).decode("utf-8")

        elif propset_type == 'VirtualMachine' and propset_path == 'summary':

            X = self.get_soap_properties_response('vm', propset_type, requested, 'summary', 'VirtualMachineSummary') 
            fdata = TS(X).decode("utf-8")

        elif propset_type == 'VirtualMachine' and propset_path == 'guest':

            X = self.get_soap_properties_response('vm', propset_type, requested, 'guest', 'GuestInfo') 
            fdata = TS(X).decode("utf-8")

        elif propset_type == 'VirtualMachine' and propset_path == 'datastore':

            X = self.get_soap_properties_response('vm', propset_type, requested, 'datastore', 'Datastore') 
            fdata = TS(X).decode("utf-8")

        elif propset_type == 'VirtualMachine' and propset_path == 'network':

            X = self.get_soap_properties_response('vm', propset_type, requested, 'network', 'Network') 
            fdata = TS(X).decode("utf-8")

        elif propset_type == 'VirtualMachine' and propset_path == 'resourcePool':

            X = self.get_soap_properties_response('vm', propset_type, requested, 
                                                  'resourcePool', 'ResourcePool', xsitype='Resources') 
            fdata = TS(X).decode("utf-8")
            #import pdb; pdb.set_trace()

        elif propset_type == 'VirtualMachine' and propset_path == 'alarmActionsEnabled':

            import pdb; pdb.set_trace()
            X = self.get_soap_properties_response('vm', propset_type, requested, 'alarmActionsEnabled', 'alarmActionsEnabled') 
            fdata = TS(X).decode("utf-8")



        elif requested.startswith('host-'):
            # return the list of VMs for the host
            print("# HOST: %s" % requested)
            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, 'RetrievePropertiesResponse')
            RPResponse.set('xmlns', "urn:vim25")

            for vm in INVENTORY['hosts'][requested]['vms']:

                this_rval = E("returnval")
                this_obj = SE(this_rval, 'obj')
                this_obj.set('type', 'VirtualMachine')
                this_obj.text = vm
                this_propset = SE(this_rval, 'propSet')
                this_name = SE(this_propset, 'name')
                this_name.text = 'name'
                this_val = SE(this_propset, 'val')
                this_val.set('xsi:type', 'xsd:string')
                this_val.text = INVENTORY['vms'][vm]['name']

                RPResponse.append(this_rval)

            fdata = TS(X).decode("utf-8")

        else:
            #print("# USING DEFAULT PROPERTIES RESP")
            f = open('fixtures/vc550_RetrievePropertiesResponse.xml', 'r')
            fdata = f.read()
            f.close()

        return fdata

    def FindByInventoryPath(self, postdata, query):

        # inventoryPath': 'DC1/vm/testvms'}

        '''
        <?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope ...">
          <soapenv:Body>
            <FindByInventoryPathResponse xmlns="urn:vim25">
              <returnval type="Folder">group-v61</returnval>
            </FindByInventoryPathResponse>
          </soapenv:Body>
        </soapenv:Envelope>
        '''

        splitxml(postdata)

        searchpath = query.get('Body', {}).\
                        get('FindByInventoryPath', {}).\
                        get('inventoryPath', None)

        parts = searchpath.split('/')
        dcname = parts[0]
        dcid = None
        folder = None

        # find the datacenter id based on name
        for k,v in INVENTORY['datacenters'].items():
            if v['name'] == dcname:
                dcid = k
                break
        # find the folder id based on dc and path
        if dcid:
            folders = INVENTORY['datacenters'][dcid]['folders']
            lastfolder = None
            for idx,x in enumerate(parts):            
                if not lastfolder:
                    lastfolder = folders
                    continue
                found = False
                for k,v in lastfolder.items():
                    if k == 'name' or k == 'id':
                        continue
                    if type(v) != dict:
                        continue
                    if not 'name' in x:
                        continue
                    if v['name'] == x:
                        found = True
                        lastfolder = v
                        continue

        #if not found:
        #    raise "ERROR: folder path not found"

        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        FIPR = SE(Body, 'FindByInventoryPathResponse')
        FIPR.set('xmlns', 'urn:vim25')
        if found:
            RVAL = SE(FIPR, 'returnval')
            RVAL.set('type', 'Folder')
            RVAL.text = lastfolder['id']
        fdata = TS(X).decode("utf-8")
        return fdata


    def RetrievePropertiesEx(self, postdata, query):

        requested = None
        select_path = None
        propset_path = None
        propset_type = None
        try:
            requested = query.get('Body').get('RetrievePropertiesEx').get('specSet').get('objectSet').get('obj')
        except:
            pass
        try:
            select_path = query.get('Body').get('RetrievePropertiesEx').get('specSet')\
                               .get('objectSet').get('selectSet').get('path')
        except:
            pass
        try:
            propset_path = query.get('Body').get('RetrievePropertiesEx').get('specSet').get('propSet').get('pathSet')
        except:
            pass
        try:
            propset_type = query.get('Body').get('RetrievePropertiesEx').get('specSet').get('propSet').get('type')
        except:
            pass

        #if propset_type == 'HostSystem':
        #    import pdb; pdb.set_trace()

        #if '-' in requested and propset_type == 'VirtualMachine':
        #    import pdb; pdb.set_trace()

        #if propset_path == 'vmFolder':
        #    import pdb; pdb.set_trace()

        # VM Config responses have a -lot- of data, so we edit a captured response
        if propset_type == 'VirtualMachine' and propset_path == 'config':
            vmc = VirtualMachineConfigInfo(vid=requested, meta=INVENTORY['vm'].get(requested, {}).get('meta', {}))
            return vmc.generate_xml()

        ''' PARENT
        # Parents are the owner for the object based on the tree hierarchy
        if propset_path == 'parent':
            parent = None
            if propset_type == 'ResourcePool':
                parent = INVENTORY[propset_type.lower()][requested]['owner'] 
            else:
                print('WHAT IS PARENT FOR %s !?' % requested)
                import pdb; pdb.set_trace()

            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, 'RetrievePropertiesExResponse')
            RPResponse.set('xmlns', "urn:vim25")
            returnval = SE(RPResponse, 'returnval')
            objects = SE(returnval, 'objects')
            obj = SE(objects, 'obj')
            obj.set('type', propset_type)
            obj.text = requested
            propSet = SE(objects, 'propSet')
            propSet_name = SE(propSet, 'name')
            propSet_name.text = propset_path
            propSet_val = SE(propSet, 'val')
            if propset_type == 'ResourcePool':
                propSet_val.set('type', 'ComputeResource')
            else:
                #FIXME ... this is different for every object
                print('WHAT IS THE VAL TYPE FOR %s' % requested)
                import pdb; pdb.set_trace()
            propSet_val.set('xsi:type', 'ManagedObjectReference')
            propSet_val.text = parent
            fdata = TS(X).decode("utf-8")
            return fdata
        '''

        #if propset_path == 'name' and propset_type == 'ResourcePool':
        #    import pdb; pdb.set_trace()

        if requested.startswith('session['):

            type_map = {'Datacenter': 'datacenters',
                        'Datastore': 'datastores',
                        'ResourcePool': 'resourcepool',
                        'HostSystem': 'hosts',
                        'VirtualMachine': 'vm',
                        'Folder': 'folders'}

            # Get the container's properties ...
            cview = CONTAINERVIEWS[requested]

            # What level of the inventory should this start at?
            root = None
            if cview['container'] == 'group-d1':
                root = INVENTORY
            else:
                print("# What is %s ?" % cview['container'])                
                import pdb; pdb.set_trace()

            # What element of the root does the request want?
            key = None
            if cview['type'] in type_map:
                key = type_map[cview['type']]
            else:
                print("# What is %s ?" % cview['type'])                
                import pdb; pdb.set_trace()

            # Build the SOAP
            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, 'RetrievePropertiesExResponse')
            RPResponse.set('xmlns', "urn:vim25")
            returnval = SE(RPResponse, 'returnval')
            objects = SE(returnval, 'objects')
            obj = SE(objects, 'obj')
            obj.set('type', 'ContainerView')
            obj.text = requested
            propSet = SE(objects, 'propSet')
            propSet_name = SE(propSet, 'name')
            propSet_name.text = 'view'
            propSet_val = SE(propSet, 'val')
            propSet_val.set('xsi:type', 'ArrayOfManagedObjectReference')

            if key not in root and cview['type'] == 'Folder':
                # if group-d1 and Folder ... return list of datacenters?
                root = INVENTORY
                #foldermap = self._get_folder_map()
                foldermap = INVENTORY['folders'].copy()
                for k,v in foldermap.items():
                    MO = E('ManagedObjectReference')
                    MO.set('type', 'Folder')
                    MO.set('xsi:type', 'ManagedObjectReference')
                    MO.text = k
                    propSet_val.append(MO)

            else:
                # Add all the results ...
                for k,v in root[key].items():
                    MO = E('ManagedObjectReference')
                    MO.set('type', cview['type'])
                    MO.set('xsi:type', 'ManagedObjectReference')
                    MO.text = k
                    propSet_val.append(MO)

            fdata = TS(X).decode("utf-8")
            #splitxml(fdata)
            return fdata

        elif propset_type == 'Task':
            splitxml(postdata)
            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')

            if propset_path == 'info':

                task = TASKS[requested]

                RPResponse = SE(Body, 'RetrievePropertiesExResponse')
                RPResponse.set('xmlns', 'urn:vim25')
                this_rval = SE(RPResponse, 'returnval')
                this_objects = SE(this_rval, 'objects')
                this_obj = SE(this_objects, 'obj')
                this_obj.set('type', 'Task')
                this_obj.text = requested
                this_propset = SE(this_objects, 'propSet')
                this_name = SE(this_propset, 'name')
                this_name.text = propset_path
                this_val = SE(this_propset, 'val')
                this_val.set('xsi:type', "TaskInfo") 
                vkey = SE(this_val, 'key')
                vkey.text = requested
                vtask = SE(this_val, 'task')
                vtask.set('type', 'Task')
                vtask.text = requested
                vname = SE(this_val, 'name')
                vname.text = task['type']
                vdesc = SE(this_val, 'descriptionId')
                vdesc.text = 'VirtualMachine.clone'
                vent = SE(this_val, 'entity')
                vent.set('type', 'VirtualMachine')
                vent.text = task['dest']
                ventname = SE(this_val, 'entityName')
                ventname.text = INVENTORY['vm'][task['src']]['name']
                vstate = SE(this_val, 'state')
                if task['spec']['powerOn']:
                    vstate.text = 'running'
                else:
                    vstate.text = 'notrunning'
                vcancel = SE(this_val, 'cancelled')
                vcancel.text = 'false'
                vcancelable = SE(this_val, 'cancelable')
                vcancelable.text = 'true'
                vreason = SE(this_val, 'reason')
                vreason.set('xsi:type', 'TaskReasonUser')
                vusername = SE(vreason, 'userName')
                vusername.text = 'root'
                vquetime = SE(this_val, 'queueTime')
                vquetime.text = '{:%Y-%m-%dT%H:%M:%S.%f}'.format(task['queueTime'])
                vstarttime = SE(this_val, 'startTime')
                vstarttime.text = '{:%Y-%m-%dT%H:%M:%S.%f}'.format(task['startTime'])
                vevent = SE(this_val, 'eventChainId')
                vevent.text = str(task['eventid'])

                # "FINISH" the task when the time limit has been exceeeded ...
                if datetime.datetime.now() >= task['completeTime']:
                    vcancel.text = 'false'
                    vcancelable.text = 'false'    
                    vcomplete = SE(this_val, 'completeTime')
                    vcomplete.text = '{:%Y-%m-%dT%H:%M:%S.%f}'.\
                        format(task['completeTime'])
                    vstate = SE(this_val, 'state')
                    vstate.text = 'success'
                    vres = SE(this_val, 'result')
                    vres.set('type', 'VirtualMachine')
                    vres.set('xsi:type', "ManagedObjectReference")
                    vres.text = task['dest']

            else:
                print('UNHANDLED PROPERTY FOR TASK: %s' % propset_path)
                import pdb; pdb.set_trace()

            fdata = TS(X).decode("utf-8")
            return fdata

        elif requested == 'ServiceInstance':
            f = open('fixtures/vc550_RetrievePropertiesExResponse_ServiceInstance.xml', 'r')
            fdata = f.read()
            f.close()
            return fdata

        elif not requested.startswith('vm-'):
            # FIXME ... we need to figure out what the requestor actually wants.

            if propset_type == 'Datacenter':
                X = self.get_soap_properties_response('datacenter', 
                                                      propset_type, 
                                                      requested, 
                                                      propset_path, 
                                                      propset_path, 
                                                      responsetype='RetrievePropertiesExResponse')
                try:
                    fdata = TS(X).decode("utf-8")
                except Exception as e:
                    print(e)
                    import pdb; pdb.set_trace()

                return fdata

            elif propset_type == 'HostSystem':
                X = self.get_soap_properties_response('hostsystem', 
                                                      propset_type, 
                                                      requested, 
                                                      propset_path, 
                                                      propset_path, 
                                                      responsetype='RetrievePropertiesExResponse')
                try:
                    fdata = TS(X).decode("utf-8")
                except Exception as e:
                    print(e)
                    import pdb; pdb.set_trace()

                return fdata

            elif propset_type == 'ResourcePool':
                X = self.get_soap_properties_response('resourcepool', 
                                                      propset_type, 
                                                      requested, 
                                                      propset_path, 
                                                      propset_path, 
                                                      responsetype='RetrievePropertiesExResponse')
                try:
                    fdata = TS(X).decode("utf-8")
                except Exception as e:
                    print(e)
                    import pdb; pdb.set_trace()

                return fdata



            elif propset_type == 'Folder':

                # Get the requested folder meta ...
                #folder_map = self._get_folder_map()
                folder_map = INVENTORY['folders'].copy()

                X = self._get_soap_element()
                Body = SE(X, 'soapenv:Body')
                RPResponse = SE(Body, 'RetrievePropertiesExResponse')
                RPResponse.set('xmlns', 'urn:vim25')
                this_rval = SE(RPResponse, 'returnval')
                this_objects = SE(this_rval, 'objects')
                this_obj = SE(this_objects, 'obj')
                this_obj.set('type', propset_type)
                this_obj.text = requested
                this_propset = SE(this_objects, 'propSet')
                this_name = SE(this_propset, 'name')
                this_name.text = propset_path
                this_val = SE(this_propset, 'val')

                if propset_path == 'childEntity' and requested == 'group-d1':
                    this_val.set('xsi:type', 'ArrayOfManagedObjectReference')

                    for dcid,dc in INVENTORY['datacenters'].items():
                        if not 'folders' in dc:
                            continue
                        for fid,folder in dc['folders'].items():
                            MO = E('ManagedObjectReference')
                            MO.set('type', 'Folder')
                            MO.set('xsi:type', 'ManagedObjectReference')
                            MO.text = fid
                            this_val.append(MO)

                    #import pdb; pdb.set_trace()


                elif propset_path == 'childEntity' and requested != 'group-d1':
                    # return a list of items ... vms/folders/etc
                    this_val.set('xsi:type', 'ArrayOfManagedObjectReference')
                    folder_children = self._get_folder_children(requested)
                    for child in folder_children:
                        MO = E('ManagedObjectReference')
                        MO.set('xsi:type', 'ManagedObjectReference')
                        MO.text = child
                        if child.startswith('vm-'):
                            MO.set('type', 'VirtualMachine')
                        elif child.startswith('group-'):
                            MO.set('type', 'Folder')
                        else:
                            print("UNMAPPED TYPE FOR: %s" % child)
                            import pdb; pdb.set_trace()
                        this_val.append(MO)
                else:
                    print('%s for folder %s requested' % (propset_path, requested))
                    this_val.set('xsi:type', 'xsd:string')
                    this_val.text = folder_map[requested]['name']

                fdata = TS(X).decode("utf-8")
                return fdata

            else:
                f = open('fixtures/vc550_RetrievePropertiesExResponse.xml', 'r')
                fdata = f.read()
                f.close()

                # let's try to deserialize and reserialize this resp
                root = ET.fromstring(fdata)

                for x in range(1,10):
                    vm = E('ManagedObjectReference')
                    vm.text = 'vm-%s' % x
                    vm.set('type', 'VirtualMachine')
                    vm.set('xsi:type', 'ManagedObjectReference')

                    root[0][0][0] #returnval
                    root[0][0][0][0] #objects
                    root[0][0][0][0][0] #obj:containerview
                    root[0][0][0][0][1] #propset
                    root[0][0][0][0][1][0] #name
                    root[0][0][0][0][1][1] #val

                    root[0][0][0][0][1][1].append(vm)

                xmlstr = ET.tostring(root, encoding='utf8', method='xml')
                xmlstr = xmlstr.decode("utf-8")
                return xmlstr

        elif requested.startswith('vm-') and propset_path in VM_EX_PROPS:
            X = self.get_soap_properties_response('vm', 
                                                  propset_type, 
                                                  requested, 
                                                  propset_path, 
                                                  propset_path, 
                                                  responsetype='RetrievePropertiesExResponse')
            try:
                fdata = TS(X).decode("utf-8")
            except Exception as e:
                print(e)
                import pdb; pdb.set_trace()
            return fdata


        elif propset_path == 'name':
            print('#############################')
            print('REQUEST: %s name' % requested)
            print('#############################')

            xml = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<soapenv:Envelope 
    xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\"
    xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"
    xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
    xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
<soapenv:Body>
<RetrievePropertiesExResponse xmlns=\"urn:vim25\">
    <returnval>
        <objects>
            <obj type=\"VirtualMachine\">%s</obj>
            <propSet>
                <name>name</name>
                <val xsi:type=\"xsd:string\">%s</val>
            </propSet>
        </objects>
    </returnval>
</RetrievePropertiesExResponse>
</soapenv:Body>
</soapenv:Envelope>''' % (requested, 'FOO_' + requested.upper())
            return xml
        elif propset_path == 'guest':
            print('#############################')
            print('REQUEST: %s %s' % (requested, propset_path))
            print('#############################')

            xml = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<soapenv:Envelope
        xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\"
        xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"
        xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
        xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
<soapenv:Body>
<RetrievePropertiesExResponse xmlns=\"urn:vim25\">
    <returnval>
        <objects>
            <obj type=\"VirtualMachine\">%s</obj>
            <propSet>
                <name>guest</name>
                <val xsi:type=\"GuestInfo\">
                    <toolsStatus>toolsNotInstalled</toolsStatus>
                    <toolsVersionStatus>guestToolsNotInstalled</toolsVersionStatus>
                    <toolsVersionStatus2>guestToolsNotInstalled</toolsVersionStatus2>
                    <toolsRunningStatus>guestToolsNotRunning</toolsRunningStatus>
                    <toolsVersion>0</toolsVersion>
                    <guestId>ubuntu64Guest</guestId>
                    <guestFullName>Ubuntu Linux (64-bit)</guestFullName>
                    <net>
                        <network>VM Network</network>
                        <macAddress>00:50:56:82:34:02</macAddress>
                        <connected>false</connected>
                        <deviceConfigId>4000</deviceConfigId>
                    </net>
                    <screen>
                        <width>-1</width>
                        <height>-1</height>
                    </screen>
                    <guestState>notRunning</guestState>
                    <guestOperationsReady>false</guestOperationsReady>
                    <interactiveGuestOperationsReady>false</interactiveGuestOperationsReady>
                </val>
            </propSet>
        </objects>
    </returnval>
</RetrievePropertiesExResponse>
</soapenv:Body>
</soapenv:Envelope>''' % requested
            return xml

        else:

            print('#############################')
            print('REQUEST: %s %s' % (requested, propset_path))
            print('#############################')
            import pdb; pdb.set_trace()


    def CloneVM_Task(self, postdata, query):

        # The postdata should send:
        #   * template guestid
        #   * new guest name
        #   * Folder
        #   * Spec
        #       * location
        #           * Datastore
        #           * ResourcePool
        #           * HostSystem
        #       * template true/false
        #       * poweron true/false
        # For any missing spec item, use the templates existing spec

        global EVENTCHAINS
        global INVENTORY
        global TASKS

        templateid = query.get('Body', {}).get('CloneVM_Task', {}).get('_this', None)
        folderid = query.get('Body', {}).get('CloneVM_Task', {}).get('folder', None)
        vmname = query.get('Body', {}).get('CloneVM_Task', {}).get('name', None)
        spec = query.get('Body', {}).get('CloneVM_Task', {}).get('spec', {})
        powerstate = spec.get('powerOn', False)
        if not powerstate:
            powerstate = 'poweredOff'
        else:
            powerstate = 'poweredOn'
        template = INVENTORY['vm'][templateid]
        folder = self._get_folder_by_id(folderid)
        

        events = EVENTCHAINS.keys()
        events = list(events)
        events = [int(x) for x in events]
        events = sorted(set(events))
        if len(events) > 0:
            eventid = events[-1]
            eventid += 1
        else:
            eventid = 0

        tasks = TASKS.keys()
        tasks = list(tasks)
        tasks = [x.replace('task-', '') for x in tasks]
        tasks = [int(x) for x in tasks]
        tasks = sorted(set(tasks))
        if len(tasks) > 0:
            this_taskid = tasks[-1]
            this_taskid += 1
        else:
            this_taskid = 0
        taskkey = 'task-%s' % this_taskid

        vms = INVENTORY['vm'].keys()
        vms = list(vms)
        vms = [x.replace('vm-', '') for x in vms] 
        vms = [int(x) for x in vms]
        vms = sorted(set(vms))
        if len(vms) > 0:
            this_vmid = vms[-1]
            this_vmid += 1
        else:
            this_vmid = 0

        # Create the VM
        key = 'vm-%s' % this_vmid
        vdict = {}
        vdict['_meta'] = {}
        vdict['_meta']['guestState'] = powerstate
        vdict['_meta']['ipAddress'] = ''
        vdict['_meta']['uuid'] = str(uuid.uuid4())
        vdict['_meta']['ipAddress'] = False
        vdict['_meta']['from_template'] = (templateid, template['name'])
        vdict['name'] = vmname
        for i in [('network', 'network'), ('resourcePool', 'pool'), ('datastore', 'datastore')]:
            vdict[i[0]] = spec['location'].get(i[1], template.get(i[0], None))
        INVENTORY['vm'][key] = vdict
        vmid = key
        
        # Add to a datacenter + folder
        dcid = spec['location'].get('datcenter', None)
        if not dcid:
            dcid = self._get_datacenterid_for_vmid(templateid)
        #self._add_vmid_to_folder(dcid, folderid, key)
        if folderid != 'group-v0':
            INVENTORY['datacenters'][dcid]['folders']['group-v0'][folderid]['vms'].append(key)
        else:
            INVENTORY['datacenters'][dcid]['folders'][folderid]['vms'].append(key)

        # Create the taskid response
        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        cvt = SE(Body, 'CloneVM_TaskResponse')
        cvt.set('xmlns', "urn:vim25")
        rval = SE(cvt, 'returnval')
        rval.set('type', 'Task')
        rval.text = taskkey

        TASKS[taskkey] =  {}
        TASKS[taskkey]['type'] = 'CloneVM_Task'
        TASKS[taskkey]['eventid'] = eventid
        TASKS[taskkey]['dest'] = vmid
        TASKS[taskkey]['src'] = templateid
        TASKS[taskkey]['folder'] = folderid
        TASKS[taskkey]['spec'] = spec
        TASKS[taskkey]['queueTime'] = datetime.datetime.now()
        TASKS[taskkey]['startTime'] = datetime.datetime.now()
        TASKS[taskkey]['completeTime'] = datetime.datetime.now() + datetime.timedelta(seconds=1)

        fdata = TS(X).decode("utf-8")
        return fdata


    def FindByUuid(self, postdata, query):
        ''' 
        # REQUEST ...
        <FindByUuid xmlns="urn:vim25">
          <_this type="SearchIndex">SearchIndex</_this>
          <uuid>4210694e-0ab4-8765-2aea-873c507b746d</uuid>
          <vmSearch>true</vmSearch>
        </FindByUuid>

        # RESPONSE ...
        <FindByUuidResponse xmlns="urn:vim25">
          <returnval type="VirtualMachine">vm-68</returnval>
        </FindByUuidResponse>
        '''
        vmuid = query.get('Body', {}).get('FindByUuid', {}).get('uuid', None)
        vmid = self._find_vm_by_uuid(vmuid)

        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        FBUR = SE(Body, 'FindByUuidResponse')
        FBUR.set('xmlns', "urn:vim25")
        rval = SE(FBUR, 'returnval')
        rval.set('type', 'VirtualMachine')
        rval.text = vmid
        fdata = TS(X).decode("utf-8")
        return fdata

    def _find_vm_by_uuid(self, vmuid):
        vmid = None
        for k,v in INVENTORY['vm'].items():
            if v['_meta']['uuid'] == vmuid:
                vmid = k
                break
        return vmid

    def _add_vmid_to_folder(self, dcid, folderid, vmid):
        global INVENTORY
        if folderid not in INVENTORY['datacenters'][dcid]['folders']:
            print('NESTED FOLDERS NOT HANDLED YET!')
            import pdb; pdb.set_trace()
        else:
            INVENTORY['datacenters'][dcid]['folders'][folderid]['vms'].append(vmid)

    def _get_datacenterid_for_vmid(self, vmid):
        foldermap = self._get_folder_map()
        thisfolder = None
        for k,v in foldermap.items():
            if not 'vms' in v:
                continue
            if vmid in v['vms']:
                thisfolder = v
                break
        return thisfolder['datacenter']
        
    def _get_folder_map(self):
        ''' Make a hashmap of folders and their names '''

        # fid: datacenter=datacenter1        
        # fid: datacenter=datacenter2

        folders = INVENTORY['folders'].copy()
        import pdb; pdb.set_trace()

        #for dcname,datacenter in INVENTORY['datacenters'].items():
        return folders


    def _get_folder_by_id(self, folderid):
        foldermap = self._get_folder_map()
        return foldermap[folderid]

    def _get_folder_children(self, folderid):
        '''Get children of a folder'''

        '''
        foldermap = self._get_folder_map()
        children = []

        # group-d1 is the "root folder"
        if folderid not in foldermap:
            print('%s not in foldermap!' % folderid)
            import pdb; pdb.set_trace()

        if 'vms' in foldermap[folderid]:
            for vm in foldermap[folderid]['vms']:
                children.append((vm, 'VirtualMachine'))

        for k,v in foldermap[folderid].items():
            if k.startswith('group-'):
                children.append((k, 'Folder'))
        '''
        if not folderid in INVENTORY['folders']:
            import pdb; pdb.set_trace()
        children = INVENTORY['folders'][folderid].get('children', [])
        #import pdb; pdb.set_trace()
        return children


    def _get_soap_element(self):    
        X = E('soapenv:Envelope')
        X.set('xmlns:soapenc', "http://schemas.xmlsoap.org/soap/encoding/")
        X.set('xmlns:soapenv', "http://schemas.xmlsoap.org/soap/envelope/")
        X.set('xmlns:xsd', "http://www.w3.org/2001/XMLSchema")
        X.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        #Body = SE(X, 'soapenv:Body')
        return X

          
    def get_soap_properties_response(self, okey, otype, oval, prop, propname, 
                                     responsetype='RetrievePropertiesResponse', rawpost=None, xsitype=None):
        # okey = datacenter/host/vm/network/etc
        # otype = HostSystem/VirtualMachine/Datastore/Network
        # oval = vm-x, datstore-x, network-x, etc-x
        # prop = name/datastore/network/vms/etc
        # propname = HostSystem/VirtualMachine/Datastore/Network

        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        RPResponse = SE(Body, responsetype)
        RPResponse.set('xmlns', "urn:vim25")

        # Extract the desired data
        rdata = None
        try:
            rdata = INVENTORY['%s' % okey][oval]['%s' % prop]
        except Exception as e:
            pass

        this_rval = E("returnval")

        # For EX returns the "obj" node is a child of an "objects" node
        if responsetype == 'RetrievePropertiesExResponse':
            this_objects = SE(this_rval, 'objects')
            this_obj = SE(this_objects, 'obj')
        else:
            this_obj = SE(this_rval, 'obj')

        this_obj.set('type', otype)
        this_obj.text = okey
        this_propset = SE(this_rval, 'propSet')
        this_name = SE(this_propset, 'name')
        this_name.text = prop

        this_val = SE(this_propset, 'val')

        if propname == 'VirtualMachineSummary':
            this_val.set('xsi:type', 'VirtualMachineSummary')
            this_vm = SE(this_val, 'vm')
            this_vm.set('type', 'VirtualMachine')
            this_vm.text = oval
            this_runtime = SE(this_val, 'runtime')
            this_guest = SE(this_val, 'guest')
            tools_status = SE(this_guest, 'toolsStatus')
            tools_status.text = 'toolsNotInstalled'
            tools_version_status = SE(this_guest, 'toolsVersionStatus')
            tools_version_status.text = 'guestToolsNotInstalled'
            tools_running_status = SE(this_guest, 'toolsRunningStatus')
            tools_running_status.text = 'guestToolsNotRunning'

            this_config = SE(this_val, 'config')
            this_storage = SE(this_val, 'storage')
            this_stats = SE(this_val, 'quickStats')
            this_status = SE(this_val, 'overallStatus')
            this_status.text = 'green'

        elif propname == 'GuestInfo':
            this_val.set('xsi:type', 'GuestInfo')
            tools_status = SE(this_val, 'toolsStatus')
            tools_status.text = 'toolsNotInstalled'
            tools_version_status = SE(this_val, 'toolsVersionStatus')
            tools_version_status.text = 'guestToolsNotInstalled'
            tools_running_status = SE(this_val, 'toolsRunningStatus')
            tools_running_status.text = 'guestToolsNotRunning'
            tools_version = SE(this_val, 'toolsVersion')
            tools_version.text = '0'
            guest_state = SE(this_val, 'guestState')
            guest_state.text = 'notRunning'

        elif propname == 'summary':

            rdata = INVENTORY['vm'][oval]

            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, responsetype)
            RPResponse.set('xmlns', "urn:vim25")
            this_rval = E("returnval")
            this_objects = SE(this_rval, 'objects')
            this_obj = SE(this_objects, 'obj')
            this_obj.set('type', otype)
            this_obj.text = okey
            this_propset = SE(this_objects, 'propSet')
            this_name = SE(this_propset, 'name')
            this_name.text = prop
            this_val = SE(this_propset, 'val')

            this_val.set('xsi:type', 'VirtualMachineSummary')
            this_vm = SE(this_val, 'vm')
            this_vm.set('type', 'VirtualMachine')
            this_vm.text = oval
            this_runtime = SE(this_val, 'runtime')
            this_device = SE(this_runtime, 'device')
            this_host = SE(this_runtime, 'host')
            this_host.set('type', 'HostSystem')

            this_powerstate = SE(this_runtime, 'powerState')
            state = rdata['_meta'].get('guestState', 'poweredOff')
            if state != 'poweredOff':
                state = 'poweredOn'
            this_powerstate.text = state
            this_guest = SE(this_val, 'guest')

        elif propname == 'capability':
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'VirtualMachineCapability')
            cdata = {}
            ckeys= ['snapshotOperationsSupported', 'multipleSnapshotsSupported', 'poweredOffSnapshotsSupported',
                    'memorySnapshotsSupported', 'revertToSnapshotSupported', 'quiescedSnapshotsSupported',
                    'disableSnapshotsSupported', 'lockSnapshotsSupported', 'consolePreferencesSupported',
                    'cpuFeatureMaskSupported', 's1AcpiManagementSupported', 'settingScreenResolutionSupported',
                    'toolsAutoUpdateSupported', 'vmNpivWwnSupported', 'npivWwnOnNonRdmVmSupported',
                    'vmNpivWwnDisableSupported', 'vmNpivWwnUpdateSupported', 'swapPlacementSupported',
                    'toolsSyncTimeSupported', 'virtualMmuUsageSupported', 'diskSharesSupported',
                    'bootOptionsSupported', 'bootRetryOptionsSupported', 'settingVideoRamSizeSupported',
                    'settingDisplayTopologySupported', 'recordReplaySupported', 'changeTrackingSupported',
                    'multipleCoresPerSocketSupported', 'hostBasedReplicationSupported', 'guestAutoLockSupported',
                    'memoryReservationLockSupported', 'featureRequirementSupported', 'poweredOnMonitorTypeChangeSupported',
                    'seSparseDiskSupported', 'nestedHVSupported', 'vPMCSupported']
            for x in ckeys:
                cdata[x] = 'true'
            cdata['consolePreferencesSupported'] = 'false'
            cdata['settingScreenResolutionSupported'] = 'false'
            cdata['toolsAutoUpdateSupported'] = 'false'
            cdata['settingDisplayTopologySupported'] = 'false'
            for k,v in cdata.items():
                x = E(k)
                x.text = v
                this_val.append(x)

        elif propname == 'config':
            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, responsetype)
            RPResponse.set('xmlns', "urn:vim25")
            this_rval = SE(RPResponse, 'returnval')
            this_objects = SE(this_rval, 'objects')
            this_obj = SE(this_objects, 'obj')
            this_obj.set('type', 'VirtualMachine')
            this_obj.text = oval
            this_propset = SE(this_objects, 'propSet')
            this_name = SE(this_propset, 'name')
            this_name.text = 'config'

            this_val = SE(this_propset, 'val')
            this_val.set('xsi:type', 'VirtualMachineConfigInfo')

            vm = INVENTORY['vm'][oval]
            ckeys = ['changeVersion', 'modified', 'name', 'guestFullName', 'version',
                     'uuid', 'instanceUuid', 'npivTemporaryDisabled', 'locationId', 'template',
                     'guestId', 'alternateGuestName', 'annotation', 'files', 'tools',
                     'flags', 'defaultPowerOps', 'hardware', 'cpuAllocation', 'memoryAllocation',
                     'latencySensitivity', 'memoryHotAddEnabled', 'cpuHotAddEnabled', 'extraConfig',
                     'swapPlacement', 'bootOptions', 'vAssertsEnabled', 'changeTrackingEnabled',
                     'firmware', 'maxMksConnections', 'guestAutoLockEnabled', 'memoryReservationLockedToMax',
                     'initialOverhead', 'nestedHVEnabled', 'vPMCEnabled', 'scheduledHardwareUpgradeInfo',
                     'vFlashCacheReservation']
            for ckey in ckeys:
                if ckey == 'hardware':
                    # need to add a hardware managed object w/ disks
                    print("Creating HARDWARE...")
                    hw = VMHardware()
                    hwe = hw.to_element()
                    import pdb; pdb.set_trace()

                else:
                    x = E(ckey)
                    if ckey in vm:
                        x.text = str(vm[ckey])
                    elif ckey in vm['_meta']:
                        x.text = str(vm['_meta'][ckey])
                    elif ckey == 'modified':
                        x.text = '1970-01-01T00:00:00Z'
                    elif ckey == 'version':
                        x.text = 'vmx-10'
                    elif ckey == 'npivTemporaryDisabled':
                        x.text = 'true'
                    elif ckey == 'template':
                        x.text = 'false'
                    elif ckey == 'latencySensitivity':
                        latency = SE(x, 'level')
                        latency.text = 'normal'
                    elif ckey == 'cpuHotAddEnabled' or ckey == 'cpuHotRemoveEnabled':
                        x.text = 'false'
                    elif ckey == 'memoryHotAddEnabled':
                        x.text = 'false'
                    elif ckey == 'memoryAllocation':
                        reservation = SE(x, 'reservation')
                        reservation.text = '0'
                        expandableres = SE(x, 'expandableReservation')
                        expandableres.text = 'false'
                        limit = SE(x, 'limit')
                        limit.text = '-1'
                        shares = SE(x, 'shares')
                        shares2 = SE(shares, 'shares')
                        shares2.text = '2560'
                        level2 = SE(shares, 'level')
                        level2.text = 'normal'
                    elif ckey == 'bootOptions':
                        bootdelay = SE(x, 'bootDelay')
                        bootdelay.text = '0'
                        entersetup = SE(x, 'enterBIOSSetup')
                        entersetup.text = 'false'
                        retryenabled = SE(x, 'bootRetryEnabled')
                        retryenabled.text = 'false'
                        retrydelay = SE(x, 'bootRetryDelay')
                        retrydelay.text = '10000'
                    elif ckey == 'firmware':
                        x.text = 'bios'
                    elif ckey == 'maxMksConnections':
                        x.text = '40'
                    elif ckey == 'memoryReservationLockedToMax':
                        x.text = 'false'
                    elif ckey == 'vFlashCacheReservation':
                        x.text = '0'
                    elif ckey == 'files':
                        pathname = SE(x, 'vmPathName')
                        pathname.text = '[datastore1] testvm1/testvm1.vmx'
                        snapshotdir = SE(x, 'snapshotDirectory')
                        snapshotdir.text = '[datastore1] testvm1/'
                        suspenddir = SE(x, 'suspendDirectory')
                        suspenddir.text = '[datastore1] testvm1/'
                        logdir = SE(x, 'logDirectory')
                        logdir.text = '[datastore1] testvm1/'
                    elif 'enabled' in ckey.lower():
                        x.text = 'false'
                    else:
                        x.text = 'null'
                    this_val.append(x)

            return X

        elif propname == 'configIssue':
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'ArrayOfEvent')

        elif propname == 'configStatus':
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'ManagedEntityStatus')
            this_val.text = 'green'

        elif propname == 'customValue':
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'ArrayOfCustomFieldValue')

        elif propname == 'datastore':
            vm = INVENTORY['vm'][oval]
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'ArrayOfManagedObjectReference')
            for x in vm['datastore']:
                d = E('ManagedObjectReference')
                d.set('type', 'Datastore')
                d.set('xsi:type', 'ManagedObjectReference')
                d.text = x
                this_val.append(d)

        elif propname == 'effectiveRole':
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'ArrayOfInt')
            x = E('int')
            x.set('xsi:type', 'xsd:int')
            x.text = '-1'
            this_val.append(x)

        elif propname == 'alarmActionsEnabled':
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'xsd:boolean')
            this_val.text = 'true'

        elif propname == 'availableField':
            this_obj.text = oval
            this_val.set('xsi:type', 'ArrayOfCustomFieldDef')

        elif propname == 'guest':

            vm = INVENTORY['vm'][oval]
            meta = vm.get('_meta', {})

            X = None
            Body = None
            RPResponse = None
            this_rval = None
            this_objects = None
            this_obj = None
            this_propset = None
            this_name = None
            this_val = None

            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, responsetype)
            RPResponse.set('xmlns', "urn:vim25")
            this_rval = SE(RPResponse, 'returnval')
            this_objects = SE(this_rval, 'objects')
            this_obj = SE(this_objects, 'obj')
            this_obj.set('type', 'VirtualMachine')
            this_obj.text = oval
            this_propset = SE(this_objects, 'propSet')

            this_name = SE(this_propset, 'name')
            this_name.text = 'guest'
            this_val = SE(this_propset, 'val')
            this_val.set('xsi:type', 'GuestInfo')

            for x in VM_EX_GUEST_PROPS:
                y = E(x[0])
                if x[0] in meta:
                    y.text = meta[x[0]]
                elif x[1] != None:
                    y.text = x[1]
                this_val.append(y)

            netdict = {
                       'network': 'VM Network',
                       'ipAddress': ['192.168.1.42', 'fe80::250:56ff:fe90:97b'],
                       'macAddress': '00:50:56:90:09:7b',
                       'connected': 'true',
                       'deviceConfigId': '4000',
                       'ipConfig': [{'ipAddress': '192.168.1.42', 'prefixLength': '24', 'state': 'preferred'},
                                    {'ipAddress': 'fe80::250:56ff:fe90:97b', 'prefixLength': '64', 'state': 'unknown'}]
                      }

            this_net = SE(this_val, 'net')
            for k,v in netdict.items():

                if k == 'ipAddress':
                    for ip in v:
                        ni = SE(this_net, k)
                        ni.text = ip
                elif k == 'ipConfig':
                    ipconfig = SE(this_net, 'ipConfig')
                    for v2 in v:
                        ip = SE(ipconfig, 'ipAddress')
                        for k2,v2 in v2.items():
                            ip_se = SE(ip, k2)
                            ip_se.text = v2
                        
                else:
                    ni = SE(this_net, k)
                    ni.text = str(v)

            return X

        elif propname == 'vmFolder':
            #print('VMFOLDER!!!!')
            folder = INVENTORY['datacenters'][oval]['vmFolder']

            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, responsetype)
            RPResponse.set('xmlns', "urn:vim25")
            this_rval = SE(RPResponse, 'returnval')
            this_objects = SE(this_rval, 'objects')
            this_obj = SE(this_objects, 'obj')
            this_obj.set('type', oneup(okey))
            this_obj.text = oval
            this_propset = SE(this_objects, 'propSet')
            this_name = SE(this_propset, 'name')
            this_name.text = propname
            this_val = SE(this_propset, 'val')
            this_val.set('xsi:type', 'ManagedObjectReference')
            this_val.set('type', 'Folder')
            this_val.text = folder
            #import pdb; pdb.set_trace()
            return X

        elif responsetype == 'RetrievePropertiesExResponse':

            X = self._get_soap_element()
            Body = SE(X, 'soapenv:Body')
            RPResponse = SE(Body, responsetype)
            RPResponse.set('xmlns', "urn:vim25")
            this_rval = SE(RPResponse, 'returnval')
            this_objects = SE(this_rval, 'objects')
            this_obj = SE(this_objects, 'obj')
            this_obj.set('type', oneup(okey))
            this_obj.text = oval
            this_propset = SE(this_objects, 'propSet')
            this_name = SE(this_propset, 'name')
            this_name.text = propname
            this_val = SE(this_propset, 'val')

            # This is probably asking for an attribute of a single object (such as a datacenter name)
            if okey == 'datacenter':

                this_val.set('xsi:type', 'xsd:string')
                if propname in INVENTORY['datacenters'][oval]:
                    this_val.text = INVENTORY['datacenters'][oval][propname]
                else:
                    import pdb; pdb.set_trace()
                return X

            elif okey == 'resourcepool':

                this_obj.set('type', 'ResourcePool')
                this_val.set('xsi:type', 'xsd:string')
                if propname in INVENTORY['resourcepool'][oval]:
                    this_val.text = INVENTORY['resourcepool'][oval][propname]
                elif propname == 'parent':
                    this_val.text = INVENTORY['resourcepool'][oval]['owner']
                else:
                    import pdb; pdb.set_trace()
                return X

            elif okey == 'hostsystem':

                this_obj.set('type', 'HostSystem')
                this_val.set('xsi:type', 'xsd:string')
                if propname in INVENTORY['hosts'][oval]:
                    this_val.text = INVENTORY['hosts'][oval][propname]
                elif propname == 'parent':
                    this_val.set('type', 'ComputeResource')
                    this_val.set('xsi:type', 'ManagedObjectReference')
                    # what is the parent for this host?
                    parent = None
                    for dcitem in INVENTORY['datacenters'].items():
                        k = dcitem[0]
                        v = dcitem[1]
                        if oval in v['hosts']:
                            parent = k
                            break
                    this_val.text = parent    
                else:
                    import pdb; pdb.set_trace()
                return X

            elif okey != 'vm':
                print("# EXRESPONSE FOR %s,%s,%s NOT YET IMPLEMENTED !!!" % (okey,oval,propname))
                import pdb; pdb.set_trace()
            else:
                # name, type, etc ...
                data = INVENTORY[okey][oval].get(propname, None)

                X = self._get_soap_element()
                Body = SE(X, 'soapenv:Body')
                RPResponse = SE(Body, responsetype)
                RPResponse.set('xmlns', "urn:vim25")
                this_rval = SE(RPResponse, 'returnval')
                this_objects = SE(this_rval, 'objects')
                this_obj = SE(this_objects, 'obj')
                this_obj.set('type', 'VirtualMachine')
                this_obj.text = oval
                this_propset = SE(this_objects, 'propSet')
                this_name = SE(this_propset, 'name')
                this_name.text = propname
                this_val = SE(this_propset, 'val')

                if type(rdata) != list:
                    # make the string based result ...
                    this_val.set('xsi:type', 'xsd:string')
                    this_val.text = data
                else:
                    # make the list result type
                    this_val.set('xsi:type', 'ArrayOfManagedObjectReference')
                    for rd in rdata:
                        MO = E('ManagedObjectReference')
                        MO.set('type', oneup(propname))
                        MO.set('xsi:type', 'ManagedObjectReference')
                        MO.text = rd
                        this_val.append(MO)

                return X                

        elif type(rdata) in [str,bytes]:

            #print('# PROCESSING STRING OR MO ...')

            # How do we know to return a MO or a string?
            if prop.lower() in INVENTORY:
                # this is a managed object reference
                this_val.set('type', oneup(prop))
                this_val.set('xsi:type', 'ManagedObjectReference')
                this_val.text = rdata
            else:
                # this is a string ???
                this_val.set('xsi:type', 'xsd:string')
                this_val.text = rdata
                this_obj.text = oval

        elif type(rdata) == list:
            this_val.set('xsi:type', 'ArrayOfManagedObjectReference')
            for x in rdata:
                MO = E('ManagedObjectReference')
                MO.set('type', propname)
                MO.set('xsi:type', 'ManagedObjectReference')
                MO.text = x
                this_val.append(MO)


        RPResponse.append(this_rval)
        return X


########################################
#         INVENTORY EXPANDER           #
########################################

def _extend_inventory(hosts=2, vms=10):
    ''' Create more fake inventory '''

    global INVENTORY

    if type(hosts) != int:
        hosts = int(hosts)
    if type(vms) != int:
        vms = int(vms)

    for x in range(0, hosts + 1):
        hkey = 'host-%s' % x
        if hkey in INVENTORY['hosts']:
            continue
        INVENTORY['hosts'][hkey] = {}
        INVENTORY['hosts'][hkey]['name'] = '10.0.0.%s' % x
        INVENTORY['hosts'][hkey]['vms'] = []
        INVENTORY['hosts'][hkey]['datastores'] = ['datastore-1']

    xhost = 0
    _ip = 104
    for x in range(0, vms + 1):
        vkey = 'vm-%s' % x
        if vkey in INVENTORY['vm']:
            continue
        _ip += 1
        thisip = '10.0.0.%s' % _ip
        INVENTORY['vm'][vkey] = {}
        INVENTORY['vm'][vkey]['_meta'] = {'guestState': 'running', 'ipAddress': thisip}
        INVENTORY['vm'][vkey]['_meta']['uuid'] = str(uuid.uuid4())
        INVENTORY['vm'][vkey]['_meta']['template'] = False
        INVENTORY['vm'][vkey]['name'] = 'testvm%s' % x
        INVENTORY['vm'][vkey]['guest'] = {}
        INVENTORY['vm'][vkey]['network'] = ['network-0']
        INVENTORY['vm'][vkey]['resourcePool'] = 'resgroup-0'
        INVENTORY['vm'][vkey]['datastore'] = ['datastore-1']

        # spread evenly across the hosts ...
        if vkey not in INVENTORY['hosts']['host-%s' % xhost]['vms']:
            INVENTORY['hosts']['host-%s' % xhost]['vms'].append(vkey)
        xhost += 1
        if xhost > hosts:
            xhost = 0

    logging.info('%s total DCs' % len(list(INVENTORY['datacenters'].keys())))
    logging.info('%s total HOSTs' % len(list(INVENTORY['hosts'].keys())))
    logging.info('%s total VMs' % len(list(INVENTORY['vm'].keys())))
    #import pdb; pdb.set_trace()


########################################
#                MAIN                  #
########################################

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=443, help='enable debug logging')
    parser.add_argument("--debug", action='store_true', help='enable debug logging')
    parser.add_argument("--vms", type=int, help="total VMs to create")
    parser.add_argument("--extend", action='store_true', help="total VMs to create")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.extend or args.vms:
        if args.vms:
            extend_inventory(vms=args.vms)
        else:
            extend_inventory()

    logging.debug('creating server')
    service = HTTPServer(('localhost', args.port), VCenter)
    logging.debug('adding ssl wrapper')
    service.socket = ssl.wrap_socket(service.socket,
                               server_side=True,
                               certfile='mycert.pem',
                               ssl_version=ssl.PROTOCOL_TLSv1)

    logging.debug('serving forever')
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass

    logging.debug('closing server')
    service.server_close()    
