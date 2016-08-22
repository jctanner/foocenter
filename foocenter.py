#!/usr/bin/env python3.5

#############################################
#               REFERENCES                  #
#############################################

# http://velemental.com/2012/03/09/a-deep-dive-doing-it-the-manual-way-with-vmware-vim-and-powershell/
# https://github.com/vmware/pyvmomi/blob/master/tests/fixtures/basic_connection.yaml


#############################################
#                 SSLCERT                   #
#############################################

# mkdir keys
# cd keys
# openssl genrsa -des3 -out server.key 1024
# openssl req -new -key server.key -out server.csr
# openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
# openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mycert.pem -out mycert.pem

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

USERNAME = 'root'
PASSWORD = 'vmware'
PORT = 443

INVENTORY = {
             'datacenters': {
                              'datacenter-1': {
                                'name': "DC1",
                                'hosts': ['host-28']
                              },
                              'datacenter-2': {
                                'name': "DC2",
                                'hosts': ['host-29']
                              }
                            }, 
             'clusters': {}, 
             'hosts':{
                        'host-0': {
                                   'name': '10.10.10.1',
                                   'vms': [],
                                   'datastores': ['datastore-0']
                                  },
                        'host-1': {
                                   'name': '10.10.10.2',
                                   'vms': [],
                                   'datastores': ['datastore-1']
                                  }

                     }, 
             'resourcepool': {
                    'resgroup-0': {
                        'name': 'Resources'
                     }
             },
             'datastores': {
                    'datastore-0': {'name': "data store 0"},
                    'datastore-1': {'name': "data store 1"},
             },
             'networks': {
                    'network-0': {
                        'name': 'VM Network'
                    }
             },
             'vm': {
                     'vm-1': {
                        'name': "testvm1",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-0"]
                     },
                     'vm-2': {
                        'name': "testvm2",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-0"]
                     },
                     'vm-3': {
                        'name': "testvm3",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-1"]
                     },
                     'vm-4': {
                        'name': "testvm4",
                        'guest': {},
                        'network': ['network-0'],
                        'resourcePool': 'resgroup-0',
                        'datastore': ["datastore-1"]
                     }
                 }
        }

##########################
# Build up the inventory
##########################
TOTAL_HOSTS = 2
for x in range(0, TOTAL_HOSTS + 1):
    hkey = 'host-%s' % x
    INVENTORY['hosts'][hkey] = {}
    INVENTORY['hosts'][hkey]['name'] = '10.0.0.%s' % x
    INVENTORY['hosts'][hkey]['vms'] = []
    INVENTORY['hosts'][hkey]['datastores'] = ['datastore-1']

TOTAL_VMS = 10
xhost = 0
for x in range(0, TOTAL_VMS + 1):
    vkey = 'vm-%s' % x
    INVENTORY['vm'][vkey] = {}
    INVENTORY['vm'][vkey]['name'] = 'testvm%s' % x
    INVENTORY['vm'][vkey]['guest'] = {}
    INVENTORY['vm'][vkey]['network'] = ['network-0']
    INVENTORY['vm'][vkey]['resourcePool'] = 'resgroup-0'
    INVENTORY['vm'][vkey]['datastore'] = ['datastore-1']

    # spread evenly across the hosts ...
    INVENTORY['hosts']['host-%s' % xhost]['vms'].append(vkey)
    xhost += 1
    if xhost > TOTAL_HOSTS:
        xhost = 0


# Properties for a VirtualMachine Object ...
VM_EX_PROPS = ['alarmActionsEnabled', 'availableField', 'capability', 'config', 'configIssue', 'configStatus',
               'customValue', 'datastore', 'effectiveRole', 'environmentBrowser', 'guest', 'guestHeartbeatStatus', 
               'layout', 'layoutEx', 'name', 'network', 'overallStatus', 'parent', 'parentVApp', 'permission',
               'recentTask', 'resourceConfig', 'resourcePool', 'rootSnapshot', 'runtime', 'snapshot',
               'storage', 'summary', 'tag', 'triggeredAlarmState', 'value']

# Properties for a VirtualMachine.guest Object ...
VM_EX_GUEST_PROPS = [('toolsStatus', 'toolsNotInstalled'), 
                     ('toolsVersionStatus', 'guestToolsNotInstalled'), 
                     ('toolsVersionStatus2', 'guestToolsNotInstalled'), 
                     ('toolsRunningStatus', 'guestToolsNotRunning'),
                     ('toolsVersion', '0'), 
                     ('screen', None), 
                     ('guestState', 'notRunning'),
                     ('appHeartbeatStatus', 'appStatusGray'), 
                     ('appState', 'none'),
                     ('guestOperationsReady', 'false'),
                     ('interactiveGuestOperationsReady', 'false')]


#############################################
#            CLIENT SESSIONS                #
#############################################

VIEWMANAGERS = {}
CONTAINERVIEWS = {}



class VCenter(BaseHTTPRequestHandler):

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

        #print("")
        #print("")

        requestline = self.requestline
        rparts = requestline.split()
        url = rparts[1]
        #print("URL %s" % url)

        postdata = self.rfile.read(int(self.headers['Content-Length']))
        postdata = postdata.decode("utf-8")
        #print(postdata)
        query = xml2dict(postdata)

        print("# QUERY START")
        pprint(query)
        print("# QUERY END")

        rc = 200 #http returncode

        # What is the method being called?
        methodCalled = list(query['Body'].keys())[0]

        if hasattr(self, methodCalled):
            # call the method
            #print("# CALLING %s" % methodCalled)
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


        # pretty print the response
        splitxml(resp)
        #print("# RESP TYPE: %s" % type(resp))

        self.send_response(rc)
        self.send_header("Content-type", "text/xml")
        if rc == 200:
            self.send_header("msg", "OK")
        else:
            self.send_header("msg", "Internal Server Error")
        self.end_headers()
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
        #import pdb; pdb.set_trace()

        # Build the SOAP response ...
        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        CreateContainerViewResponse = SE(Body, 'CreateContainerViewResponse')
        CreateContainerViewResponse.set('xmlns', 'urn:vim25')
        returnval = SE(CreateContainerViewResponse, 'returnval')
        returnval.set('type', 'ContainerView')
        returnval.text = sessionid

        fdata = TS(X).decode("utf-8")

        '''
        f = open('fixtures/vc550_CreateContainerViewResponse.xml', 'r')
        fdata = f.read()
        f.close()
        '''

        #splitxml(fdata)

        return fdata


    def RetrieveProperties(self, postdata, query):
        # pshphere get hosts ...

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

        '''
        print('retrieveproperties requested: %s' % requested)
        print('retrieveproperties select_path: %s' % select_path)
        print('retrieveproperties propset_path: %s' % propset_path)
        print('retrieveproperties propset_type: %s' % propset_type)
        '''


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

    def RetrievePropertiesEx(self, postdata, query):

        # sometimes the caller wants a list of hosts ...

        # sometimes the caller wants a list of vms ...
        '''
        <val xsi:type=\"ArrayOfManagedObjectReference\">
            <ManagedObjectReference type=\"VirtualMachine\" xsi:type=\"ManagedObjectReference\">
                vm-744
            </ManagedObjectReference>
            <ManagedObjectReference type=\"VirtualMachine\" xsi:type=\"ManagedObjectReference\">
                vm-730
            </ManagedObjectReference>
            <ManagedObjectReference type=\"VirtualMachine\" xsi:type=\"ManagedObjectReference\">
                vm-741
            </ManagedObjectReference>
        '''

        # sometimes the caller wants a single vm ...
        '''
        <soapenv:Body>
            <RetrievePropertiesEx xmlns="urn:vim25">
            <_this type="PropertyCollector">propertyCollector</_this>
            <specSet>
                <propSet>
                    <type>VirtualMachine</type>
                    <all>false</all>
                    <pathSet>name</pathSet>
                </propSet>
                <objectSet>
                    <objtype="VirtualMachine">vm-744</obj>
                    <skip>false</skip>
                </objectSet>
            </specSet>
            <options>
                <maxObjects>1</maxObjects>
            </options>
            </RetrievePropertiesEx>
        </soapenv:Body>
        '''

        #try:
        #    requested = query.get('Body').get('RetrievePropertiesEx').get('specSet').get('objectSet').get('obj')
        #    pathset = query.get('Body').get('RetrievePropertiesEx').get('specSet').get('propSet').get('pathSet')
        #except:
        #    pass

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

        '''
        print('retrievepropertiesex requested: %s' % requested)
        print('retrievepropertiesex select_path: %s' % select_path)
        print('retrievepropertiesex propset_path: %s' % propset_path)
        print('retrievepropertiesex propset_type: %s' % propset_type)
        '''

        # session[0bc77834-77fc-7422-e2cd-81d4e5127926]52ef3fa7-892d-d0c0-d12d-7f16d61aa6e2 --> vmlist
        # vm-1 --> a VM

        if requested.startswith('session['):

            type_map = {'HostSystem': 'hosts',
                        'VirtualMachine': 'vm'}


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



        elif not requested.startswith('vm-'):

            # FIXME ... we need to figure out what the requestor actually wants.
            '''
            print('#############################')
            print('REQUEST: %s name (ALLVMS)' % requested)
            print('#############################')
            '''

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

        #if prop.lower() == 'network' or propname.lower() == 'network':
        #    import pdb; pdb.set_trace()

        X = self._get_soap_element()
        Body = SE(X, 'soapenv:Body')
        RPResponse = SE(Body, responsetype)
        RPResponse.set('xmlns', "urn:vim25")

        # Extract the desired data
        rdata = None
        try:
            #print("INVENTORY['%s']['%s']['%s']" % (okey, oval, prop))
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
            this_obj.text = oval #need the VM id here 
            this_val.set('xsi:type', 'VirtualMachineConfigInfo')
            vm = INVENTORY['vm'][oval]
            ckeys = ['changeVersion', 'modified', 'name', 'guestFullName', 'version',
                     'uuid', 'instanceUuid', 'npivTemporaryDisabled', 'locationId', 'template',
                     'guestId', 'alternateGuestName', 'annotation', 'files', 'tools',
                     'flags', 'defaultPowerOps', 'hardware', 'cpuAllocation', 'memoryAllocation',
                     'latencySensititivy', 'memoryHotAddEnabled', 'cpuHotAddEnabled', 'extraConfig',
                     'swapPlacement', 'bootOptions', 'vAssertsEnabled', 'changeTrackingEnabled',
                     'firmware', 'maxMksConnections', 'guestAutoLockEnabled', 'memoryReservationLockedToMax',
                     'initialOverhead', 'nestedHVEnabled', 'vPMCEnabled', 'scheduledHardwareUpgradeInfo',
                     'vFlashCacheReservation']
            for ckey in ckeys:
                x = E(ckey)
                this_val.append(x)

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
            #import pdb; pdb.set_trace()

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

            #print("###########################")
            #print("#         GUEST           #")
            #print("###########################")

            X = None
            Body = None
            RPResponse = None
            this_rval = None
            this_objects = None
            this_obj = None
            this_propset = None
            this_name = None
            this_val = None

            #print("## 1")
            X = self._get_soap_element()
            #splitxml(X)
            Body = SE(X, 'soapenv:Body')
            #splitxml(X)

            #print("## 2")
            RPResponse = SE(Body, responsetype)
            RPResponse.set('xmlns', "urn:vim25")
            #splitxml(X)

            #print("## 3")
            this_rval = SE(RPResponse, 'returnval')
            #splitxml(X)

            #print("## 4")
            this_objects = SE(this_rval, 'objects')
            #splitxml(X)

            #print("## 5")
            this_obj = SE(this_objects, 'obj')
            #splitxml(X)

            #print("## 6")
            this_obj.set('type', 'VirtualMachine')
            this_obj.text = oval
            #splitxml(X)

            #print("## 7")
            this_propset = SE(this_objects, 'propSet')
            #splitxml(X)

            #print("## 8")
            this_name = SE(this_propset, 'name')
            this_name.text = 'guest'
            #splitxml(X)

            #print("## 9")
            this_val = SE(this_propset, 'val')
            this_val.set('xsi:type', 'GuestInfo')
            #splitxml(X)

            for x in VM_EX_GUEST_PROPS:
                y = E(x[0])
                if x[1] != None:
                    y.text = x[1]
                this_val.append(y)

            #print("## 10")
            #splitxml(X)
            return X

        elif responsetype == 'RetrievePropertiesExResponse':

            # This is probably asking for an attribute of a single object (such as a vm)
            if okey != 'vm':
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
                        #import pdb; pdb.set_trace()

                #import pdb; pdb.set_trace()
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


        #if propname.lower() == 'resourcepool':
        #    import pdb; pdb.set_trace()

        RPResponse.append(this_rval)
        return X

def splitxml(xmlobj):
    if type(xmlobj) in [str, bytes]:
        rxml = xml.dom.minidom.parseString(xmlobj)
    else:
        rxml = xml.dom.minidom.parseString(TS(xmlobj).decode("utf-8"))
    pxml = rxml.toprettyxml()
    lines = [x for x in pxml.split('\n') if x.strip()]
    for line in lines:
        print(line)


def oneup(text):
    '''Capitalize the first letter of a string'''
    newstr = []
    for idx,x in enumerate(text):
        if idx == 0:
            newstr.append(x.upper())
        else:    
            newstr.append(x)
    return ''.join(newstr)


def xml2dict(data):
    ddict = {}
    root = ET.fromstring(data)
    if len(root) > 0:
        ddict = children2dict(root)
    return ddict

def children2dict(root):
    ddict = {}
    for child in root:
        key = remove_urn(child.tag)

        # what is the name of this child?
        if len(child) == 0:
            if hasattr(child, 'itertext'):
                ddict[key] = ''.join([x for x in child.itertext()])
            else:
                ddict[key] = None
            #import pdb; pdb.set_trace()
        else:
            ddict[key] = children2dict(child)
    return ddict

def remove_urn(urnstring):
    #{http://schemas.xmlsoap.org/soap/envelope/}Body
    #{urn:vim25}_this
    inphase = False
    new = ""
    for x in urnstring:
        if x == '{':
            inphase = True
            continue
        if x == '}':
            inphase = False
            continue
        if not inphase:
            new += x
    return new

def servicecontent2xml():

    # https://www.safaribooksonline.com/library/view/python-cookbook-3rd/9781449357337/ch06s05.html

    elem = E('returnval')
    #elem = E()
    for k,v in servicecontent.items():
        child = E(k)
        if type(v.get('value', None)) == dict:
            for k2,v2 in v['value'].items():
                newchild = E(k2)
                newchild.text = v2
                child.append(newchild)
        else:
            child.text = v.get('value', capfirst(k))
        if v.get('type') != 'UNSET':
            child.set('type', v.get('type', capfirst(k)))
        elem.append(child)

    '''
    #import pdb; pdb.set_trace()
    # http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    '''
    rxml = xml.dom.minidom.parseString(TS(elem))
    pxml = rxml.toprettyxml()

    # get rid of the xml header
    lines = [x for x in pxml.split('\n')]
    pxml = '\n'.join(lines[1:])
    return pxml

def capfirst(s):
    new = ''
    for idx,x in enumerate(s):
        if idx == 0:
            new += x.upper()
        else:
            new += x
    return new


def run_command(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    (so, se) = p.communicate()
    return (p.returncode, so, se)


if __name__ == "__main__":
    service = HTTPServer(('localhost', PORT), VCenter)
    service.socket = ssl.wrap_socket(service.socket,
                               server_side=True,
                               certfile='mycert.pem',
                               ssl_version=ssl.PROTOCOL_TLSv1)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass

    service.server_close()    
