#!/usr/bin/env python

import ssl

from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

from psphere.client import Client
from psphere.errors import ObjectNotFoundError
from psphere.managedobjects import HostSystem, VirtualMachine, ManagedObject, Network, ClusterComputeResource
from suds.sudsobject import Object as SudsObject

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def main():

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE 

    # real vcenter
    kwargs = {'host': '192.168.1.39', 'user': 'root', 'pwd': 'vmware', 'port': 443, 'sslContext': context}

    # fake vcenter
    kwargs = {'host': 'localhost', 'user': 'test', 'pwd': 'test', 'port': 443, 'sslContext': context }


    print('# PYVMOMI ...')
    try:
        si = SmartConnect(**kwargs)
        content = si.RetrieveContent()
        virtual_machines = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

        for virtual_machine in virtual_machines.view:
            name = virtual_machine.name
            print('name: %s' % name)
            if virtual_machine.guest:
                for net in virtual_machine.guest.net:
                    print('mac: %s' % net.macAddress)
    except Exception as e:
        print e

    print('# PSPHERE ...')
    client = Client(kwargs['host'], kwargs['user'], kwargs['pwd']) 
    hosts = HostSystem.all(client)
    for host in hosts:
        print 'host:',host.name
        for vm in host.vm:
            print 'name: ',vm.name

if __name__ == "__main__":
    main()
