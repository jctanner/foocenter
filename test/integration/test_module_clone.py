#!/usr/bin/env python

import atexit
import os
import shutil
import ssl
import sys
import time
import yaml
import vcr

#import xml.etree.ElementTree as ET
import xml.etree.cElementTree as ET
from lxml import etree as LET
from string import rjust

from pprint import pprint
from pyVim import connect
from pyVmomi import vim
from vmware_guest import PyVmomiHelper

# Always clean out the fixture before re-executing 
#   to avoid [SSL: CERTIFICATE_VERIFY_FAILED]
if os.path.isdir('/tmp/fixtures'):
    shutil.rmtree('/tmp/fixtures')
os.makedirs('/tmp/fixtures')

REQUESTS = []
REQUESTID = 0
def record_requests(request):
    # vcr interceptor

    global REQUESTS
    global REQUESTID

    thistype = None
    method = None
    uri = None
    body = None

    if type(request) == dict:
        thistype = 'response'
    else:
        REQUESTID += 1
        thistype = 'request'

    if thistype == 'request':
        ydata = {}
        ydata['request'] = {}
        ydata['request']['method'] = request.method
        ydata['request']['uri'] = request.uri
        if request.headers:
            ydata['request']['headers'] = {}
            for x in request.headers.items():
                ydata['request']['headers'][x[0]] = x[1]
        else:
            ydata['request']['headers'] = request.headers
        ydata['request']['body'] = request.body
        REQUESTS.append(ydata)
    else:
        ydata = REQUESTS[-1]
        ydata['response'] = request.copy()
        REQUESTS[-1]['response'] = request.copy()
        REQUESTS[-1]['response']['body'] = request['body']['string']
        fid = str(REQUESTID).rjust(4, '0')
        fname = os.path.join('/tmp', 'fixtures', '%s.yml' % (fid))
        with open(fname, 'wb') as f:
            yaml.dump(REQUESTS[-1], f, width=1000, indent=2)

    return request

# Make a custom VCR instance so we can inject our spyware into it
vcrshim = vcr.VCR(
    cassette_library_dir='/tmp/fixtures',
    before_record=record_requests,
    before_record_response=record_requests
)

def connect_to_api(module, disconnect_atexit=True):
    # FIXME ... the real code is not handling self-signed cert exceptions correctly
    hostname = module.params['hostname']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    validate_certs = module.params['validate_certs']

    if validate_certs and not hasattr(ssl, 'SSLContext'):
        module.fail_json(msg='pyVim does not support changing verification mode with python < 2.7.9. Either update python or or use validate_certs=false')

    try:
        service_instance = connect.SmartConnect(host=hostname, port=port, user=username, pwd=password)
    except vim.fault.InvalidLogin, invalid_login:
        module.fail_json(msg=invalid_login.msg, apierror=str(invalid_login))
    except ssl.SSLError as e:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        service_instance = connect.SmartConnect(host=hostname, port=port, user=username, pwd=password, sslContext=context)

    # Disabling atexit should be used in special cases only.
    # Such as IP change of the ESXi host which removes the connection anyway.
    # Also removal significantly speeds up the return of the module
    if disconnect_atexit:
        atexit.register(connect.Disconnect, service_instance)
    #import epdb; epdb.st()
    return service_instance.RetrieveContent()

def pretty_xml(rawxml):
    parser = LET.XMLParser(remove_blank_text=True)
    root = LET.fromstring(rawxml, parser)
    pxml = LET.tostring(root, pretty_print=True)
    return pxml

class FakeModule(object):
    def __init__(self):
        self.params = {}
        self.params['validate_certs'] = False
        self.params['hostname'] = '192.168.121.129'
        self.params['port'] = '443'
        self.params['username'] = 'administrator@vsphere.local'
        self.params['password'] = 'vmware1234'

        self.params['name'] = 'testvm1'
        self.params['name_match'] = 'first'
        self.params['uuid'] = None
        self.params['state'] = 'absent'
        self.params['folder'] = '/vm/testvms'
        self.params['template'] = 'template_el7'
        self.params['wait_for_ip_address'] = False
        self.params['force'] = True
        self.params['datacenter'] = 'datacenter1'
        self.params['esxi_hostname'] = '192.168.121.128'
        self.params['disk'] = [
            { 'size_gb': 25,
              'type': 'thin',
              'datastore': 'datastore1'}
        ]
        self.params['nic'] = [
            { 'type': 'vmxnet3',
              'network': 'VMNetwork',
              'network_type': 'standard'}
        ]
        self.params['hardware'] = {
            'memory_mb': 512,
            'num_cpus': 2,
            'scsi': 'paravirtual'
        }

    def fail_json(self, msg=None):
        print(msg)
        sys.exit(1)

class PyVmomiHelperWrapper(PyVmomiHelper):
    def smartconnect(self):
        self.content = connect_to_api(self.module)

@vcrshim.use_cassette('wrapper.yaml', 
                  cassette_library_dir='/tmp/fixtures',
                  record_mode='always')
def main():
    module = FakeModule()
    pyv = PyVmomiHelperWrapper(module)

    print('# Looking for existing VM')
    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'],
                   name_match=module.params['name_match'])

    result = {}
    if vm:
        print('# Removing existing vm: %s' % vm)
        result = pyv.set_powerstate(vm, 'poweredoff', module.params['force'])
        result = pyv.remove_vm(vm)
        pprint(result)

    print('# Cloning template')
    poweron = (module.params['state'] != 'poweredoff')
    result = pyv.deploy_template(
                poweron=poweron, 
                wait_for_ip=module.params['wait_for_ip_address']
             )

    pprint(result)


if __name__ == "__main__":
    main()
