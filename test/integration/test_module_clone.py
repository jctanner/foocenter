#!/usr/bin/env python

import atexit
import os
import requests
import ssl
import sys
import time

from pprint import pprint
from pyVim import connect
from pyVmomi import vim
from vmware_guest import PyVmomiHelper

def connect_to_api(module, disconnect_atexit=True):
    # FIXME ... the real code is not handling self-signed cert exceptions correctly
    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    validate_certs = module.params['validate_certs']

    if validate_certs and not hasattr(ssl, 'SSLContext'):
        module.fail_json(msg='pyVim does not support changing verification mode with python < 2.7.9. Either update python or or use validate_certs=false')

    try:
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password)
    except vim.fault.InvalidLogin, invalid_login:
        module.fail_json(msg=invalid_login.msg, apierror=str(invalid_login))
    except ssl.SSLError as e:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password, sslContext=context)

    # Disabling atexit should be used in special cases only.
    # Such as IP change of the ESXi host which removes the connection anyway.
    # Also removal significantly speeds up the return of the module
    if disconnect_atexit:
        atexit.register(connect.Disconnect, service_instance)
    #import epdb; epdb.st()
    return service_instance.RetrieveContent()

class FakeModule(object):
    def __init__(self):
        self.params = {}
        self.params['validate_certs'] = False
        self.params['hostname'] = '192.168.121.129'
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

def main():
    module = FakeModule()
    pyv = PyVmomiHelperWrapper(module)

    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'],
                   name_match=module.params['name_match'])

    result = {}
    print(vm)
    if vm:
        result = pyv.set_powerstate(vm, 'poweredoff', module.params['force'])
        result = pyv.remove_vm(vm)
    else:
        poweron = (module.params['state'] != 'poweredoff')
        result = pyv.deploy_template(
                    poweron=poweron, 
                    wait_for_ip=module.params['wait_for_ip_address']
                 )

    pprint(result)


if __name__ == "__main__":
    main()
