#!/usr/bin/env python3.5

from pprint import pprint
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element  as E
from xml.etree.ElementTree import tostring as TS


f = open('fixtures/vc550_RetrievePropertiesExResponse.xml', 'r')
fdata = f.read()
f.close()

# let's try to deserialize and reserialize this resp
fdata = fdata.replace('\n', '')
root = ET.fromstring(fdata)

# make some fake VMs
for x in range(1,2):
    vm = E('ManagedObjectReference')
    vm.text = 'vm-%s' % x
    vm.set('type', 'VirtualMachine')
    vm.set('xsi:type', 'ManagedObjectReference')
    #root[0][0][0][0][0].append(vm)

    root[0][0][0] #returnval
    root[0][0][0][0] #objects
    root[0][0][0][0][0] #obj:containerview
    root[0][0][0][0][1] #propset
    root[0][0][0][0][1][0] #name
    root[0][0][0][0][1][1] #val

    root[0][0][0][0][1][1].append(vm)
    import pdb; pdb.set_trace()


xmlstr = ET.tostring(root, encoding='utf8', method='xml')
xmlstr = xmlstr.decode("utf-8")

#pprint(xmlstr)
print(xmlstr)
