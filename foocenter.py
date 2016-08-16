#!/usr/bin/env python3.5

# mkdir keys
# cd keys
# openssl genrsa -des3 -out server.key 1024
# openssl req -new -key server.key -out server.csr
# openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

# openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mycert.pem -out mycert.pem

import ssl
import subprocess
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element  as E
from xml.etree.ElementTree import tostring as TS
import xml.dom.minidom
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, HTTPServer

USERNAME = 'test'
PASSWORD = 'test'
PORT = 443

## Method calls from smartconnect ...
# <soapenv:Body><Login
# <soapenv:Body><RetrieveServiceContent
# <soapenv:Body><RetrievePropertiesEx


# 1. GET /sdk/vimServiceVersions.xml HTTP/1.1

schemaurl = "http://schemas.xmlsoap.org"
xmlschema = "http://www.w3.org/2001/XMLSchema"
envelopeattr = "xmlns:soapenc=\"%s/soap/encoding/\"" % schemaurl
envelopeattr += " xmlns:soapenv=\"%s/soap/envelope/\"" % xmlschema
envelopeattr += " xmlns:xsd=\"%s\"" % xmlschema
envelopeattr += " xmlns:xsi=\"%s-instance\"" % xmlschema
envelope_header = "<soapenv:Envelope %s>" % envelopeattr
envelope_footer = "</soapenv:Envelope>"
#import pdb; pdb.set_trace()


vimServiceVersions = '''<?xml version="1.0" encoding="UTF-8" ?><namespaces
version="1.0"><namespace><name>urn:vim25</name><version>6.0</version><priorVersions><version>5.5</version><version>5.1</version><version>5.0</version><version>4.1</version><version>4.0</version><version>2.5u2server</version><version>2.5u2</version><version>2.5</version></priorVersions></namespace><namespace><name>urn:vim2</name><version>2.0</version></namespace></namespaces>'''

post1 = '''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchea" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<soapenv:Body><RetrieveServiceContent xmlns="urn:vim25"><_this type="ServiceInstance">ServiceInstance</_this></RetrieveServiceContent></soapenv:Body>
</soapenv:Envelope>'''

resp2 = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<soapenv:Envelope xmlns:soapenc=\"$schemaurl/soap/encoding/\"xmlns:soapenv=\"$schemaurl/soap/envelope/xmlns:xsd=\"\$xmlschema"\n xmlns:xsi=\"$xmlschema-instance\"\>\n
    <soapenv:Body>\n
        <LoginResponse xmlns=\"urn:vim25\">
            <returnval>
                <key>52ad453a-13a7-e8af-9186-a1b5c5ab85b7</key>
                <userName>test</userName>
                <fullName>test</fullName>
                <loginTime>2015-10-12T16:18:07.543834Z</loginTime>
                <lastActiveTime>2015-10-12T16:18:07.543834Z</lastActiveTime>
                <locale>en</locale>
                <messageLocale>en</messageLocale>
                <extensionSession>false</extensionSession>
                <ipAddress>10.20.125.215</ipAddress>
                <userAgent></userAgent>
                <callCount>0</callCount>
            </returnval>
        </LoginResponse>
    </soapenv:Body>
</soapenv:Envelope>'''

servicecontent = OrderedDict()
servicecontent['rootFolder'] = {'type': 'Folder', 'value': 'group-d1'}
servicecontent['propertyCollector'] = {'value': 'propertyCollector'}
servicecontent['viewManager'] = {}
servicecontent['about'] = \
    {'type': 'UNSET',
     'value': {
        'name': 'VMware vCenter Server',
        'fullName': 'VMware vCenter Server 6.0.0 build-3018523',
        'vendor': 'VMware, Inc',
        'version': '6.0.0',
        'build': '3018523',
        'localeVersion': 'INTL',
        'localeBuild': '000',
        'osType': 'linux-x64',
        'productLineId': 'vpx',
        'apiType': 'VirtualCenter',
        'apiVersion': '6.0',
        'instanceUuid': '6cbd40cc-1416-4b2d-ba7c-ae53a166d00a',
        'licenseProductName': 'VMware VirtualCenter Server',
        'licenseProductVersion': '6.0',
        }
    }
servicecontent['setting'] = {'type': 'OptionManager', 'value': 'VpxSettings'}
servicecontent['userDirectory'] = {}
servicecontent['sessionManager'] = {}
servicecontent['authorizationManager'] = {}
servicecontent['serviceManager'] = {'value': 'ServiceMgr'}
servicecontent['perfManager'] = {'value': 'PerfMgr'}
servicecontent['scheduledTaskManager'] = {}
servicecontent['alarmManager'] = {}
servicecontent['eventManager'] = {}
servicecontent['taskManager'] = {}
servicecontent['extensionManager'] = {}
servicecontent['customizationSpecManager'] = {}
servicecontent['customFieldsManager'] = {}
servicecontent['diagnosticManager'] = {'value': 'DiagMgr'}
servicecontent['licenseManager'] = {}
servicecontent['searchIndex'] = {}
servicecontent['fileManager'] = {}
servicecontent['datastoreNamespaceManager'] = {}
servicecontent['virtualDiskManager'] = {}
servicecontent['snmpSystem'] = {}
servicecontent['vmProvisioningChecker'] = \
    {'type': 'VirtualMachineProvisioningChecker', 'value': 'ProvChecker'}
servicecontent['vmCompatibilityChecker'] = \
    {'type': 'VirtualMachineCompatibilityChecker', 'value': 'CompatChecker'}
servicecontent['ovfManager'] = {}
servicecontent['ipPoolManager'] = {}
servicecontent['dvSwitchManager'] = \
    {'type': 'DistributedVirtualSwitchManager', 'value': 'DVSManager'}
servicecontent['hostProfileManager'] = {}
servicecontent['clusterProfileManager'] = {}
servicecontent['complianceManager'] = \
    {'type': 'ProfileComplianceManager', 'value': 'MoComplianceManager'}
servicecontent['localizationManager'] = {}
servicecontent['storageResourceManager'] = {}
servicecontent['guestOperationsManager'] = {}
servicecontent['overheadMemoryManager'] = {}
servicecontent['certificateManager'] = {}
servicecontent['ioFilterManager'] = {}


sc = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
        <soapenv:Envelope xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\"\
        \n xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"\n xmlns:xsd=\"\
        http://www.w3.org/2001/XMLSchema\"\n xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\
        >\n<soapenv:Body>\n<RetrieveServiceContentResponse xmlns=\"urn:vim25\"><returnval><rootFolder\
        \ type=\"Folder\">group-d1</rootFolder><propertyCollector type=\"PropertyCollector\"\
        >propertyCollector</propertyCollector><viewManager type=\"ViewManager\">ViewManager</viewManager><about><name>VMware\
        \ vCenter Server</name><fullName>VMware vCenter Server 6.0.0 build-3018523</fullName><vendor>VMware,\
        \ Inc.</vendor><version>6.0.0</version><build>3018523</build><localeVersion>INTL</localeVersion><localeBuild>000</localeBuild><osType>linux-x64</osType><productLineId>vpx</productLineId><apiType>VirtualCenter</apiType><apiVersion>6.0</apiVersion><instanceUuid>6cbd40cc-1416-4b2d-ba7c-ae53a166d00a</instanceUuid><licenseProductName>VMware\
        \ VirtualCenter Server</licenseProductName><licenseProductVersion>6.0</licenseProductVersion></about><setting\
        \ type=\"OptionManager\">VpxSettings</setting><userDirectory type=\"UserDirectory\"\
        >UserDirectory</userDirectory><sessionManager type=\"SessionManager\">SessionManager</sessionManager><authorizationManager\
        \ type=\"AuthorizationManager\">AuthorizationManager</authorizationManager><serviceManager\
        \ type=\"ServiceManager\">ServiceMgr</serviceManager><perfManager type=\"\
        PerformanceManager\">PerfMgr</perfManager><scheduledTaskManager type=\"ScheduledTaskManager\"\
        >ScheduledTaskManager</scheduledTaskManager><alarmManager type=\"AlarmManager\"\
        >AlarmManager</alarmManager><eventManager type=\"EventManager\">EventManager</eventManager><taskManager\
        \ type=\"TaskManager\">TaskManager</taskManager><extensionManager type=\"\
        ExtensionManager\">ExtensionManager</extensionManager><customizationSpecManager\
        \ type=\"CustomizationSpecManager\">CustomizationSpecManager</customizationSpecManager><customFieldsManager\
        \ type=\"CustomFieldsManager\">CustomFieldsManager</customFieldsManager><diagnosticManager\
        \ type=\"DiagnosticManager\">DiagMgr</diagnosticManager><licenseManager type=\"\
        LicenseManager\">LicenseManager</licenseManager><searchIndex type=\"SearchIndex\"\
        >SearchIndex</searchIndex><fileManager type=\"FileManager\">FileManager</fileManager><datastoreNamespaceManager\
        \ type=\"DatastoreNamespaceManager\">DatastoreNamespaceManager</datastoreNamespaceManager><virtualDiskManager\
        \ type=\"VirtualDiskManager\">virtualDiskManager</virtualDiskManager><snmpSystem\
        \ type=\"HostSnmpSystem\">SnmpSystem</snmpSystem><vmProvisioningChecker type=\"\
        VirtualMachineProvisioningChecker\">ProvChecker</vmProvisioningChecker><vmCompatibilityChecker\
        \ type=\"VirtualMachineCompatibilityChecker\">CompatChecker</vmCompatibilityChecker><ovfManager\
        \ type=\"OvfManager\">OvfManager</ovfManager><ipPoolManager type=\"IpPoolManager\"\
        >IpPoolManager</ipPoolManager><dvSwitchManager type=\"DistributedVirtualSwitchManager\"\
        >DVSManager</dvSwitchManager><hostProfileManager type=\"HostProfileManager\"\
        >HostProfileManager</hostProfileManager><clusterProfileManager type=\"ClusterProfileManager\"\
        >ClusterProfileManager</clusterProfileManager><complianceManager type=\"ProfileComplianceManager\"\
        >MoComplianceManager</complianceManager><localizationManager type=\"LocalizationManager\"\
        >LocalizationManager</localizationManager><storageResourceManager type=\"\
        StorageResourceManager\">StorageResourceManager</storageResourceManager><guestOperationsManager\
        \ type=\"GuestOperationsManager\">guestOperationsManager</guestOperationsManager><overheadMemoryManager\
        \ type=\"OverheadMemoryManager\">OverheadMemoryManger</overheadMemoryManager><certificateManager\
        \ type=\"CertificateManager\">certificateManager</certificateManager><ioFilterManager\
        \ type=\"IoFilterManager\">IoFilterManager</ioFilterManager></returnval></RetrieveServiceContentResponse>\n\
        </soapenv:Body>\n</soapenv:Envelope>'''


# https://github.com/vmware/pyvmomi/blob/master/tests/fixtures/basic_connection.yaml
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
            #import pdb; pdb.set_trace()
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
        print("URL %s" % url)

        postdata = self.rfile.read(int(self.headers['Content-Length']))
        postdata = postdata.decode("utf-8")
        print(postdata)
        query = xml2dict(postdata)

        rc = 200 #http returncode

        # What is the method being called?
        methodCalled = list(query['Body'].keys())[0]

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

        self.send_response(rc)
        self.send_header("Content-type", "text/xml")
        if rc == 200:
            self.send_header("msg", "OK")
        else:
            self.send_header("msg", "Internal Server Error")
        self.end_headers()
        self.wfile.write(bytes(resp, 'utf-8'))

        '''
        f = open('/tmp/resp.xml', 'w')
        f.write(resp)
        f.close()
        '''


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

    def CreateContainerView(self, postdata, query):
        f = open('fixtures/vc550_CreateContainerViewResponse.xml', 'r')
        fdata = f.read()
        f.close()
        return fdata

    def RetrievePropertiesEx(self, postdata, query):

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
        try:
            requested = query.get('Body').get('RetrievePropertiesEx').get('specSet').get('objectSet').get('obj')
            pathset = query.get('Body').get('RetrievePropertiesEx').get('specSet').get('propSet').get('pathSet')
        except:
            pass

        # session[0bc77834-77fc-7422-e2cd-81d4e5127926]52ef3fa7-892d-d0c0-d12d-7f16d61aa6e2 --> vmlist
        # vm-1 --> a VM

        if not requested.startswith('vm-'):

            print('#############################')
            print('REQUEST: %s name (ALLVMS)' % requested)
            print('#############################')

            f = open('fixtures/vc550_RetrievePropertiesExResponse.xml', 'r')
            fdata = f.read()
            f.close()

            # let's try to deserialize and reserialize this resp
            root = ET.fromstring(fdata)

            for x in range(1,2):
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

        elif pathset == 'name':
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
        elif pathset == 'guest':
            print('#############################')
            print('REQUEST: %s %s' % (requested, pathset))
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
            print('REQUEST: %s %s' % (requested, pathset))
            print('#############################')

            import pdb; pdb.set_trace()
    
       


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
