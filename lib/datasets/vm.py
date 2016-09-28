#!usr/bin/env python

import lxml
import uuid

from pprint import pprint
from lxml import etree as ET
from lxml.etree import tostring as LTS
from lxml import objectify

from lib.utils import *

# Properties for a VirtualMachine Object ...
VM_EX_PROPS = ['alarmActionsEnabled', 'availableField', 
               'capability', 'config', 'configIssue', 'configStatus',
               'customValue', 'datastore', 'effectiveRole', 
               'environmentBrowser', 'guest', 'guestHeartbeatStatus', 
               'layout', 'layoutEx', 'name', 'network', 'overallStatus', 
               'parent', 'parentVApp', 'permission', 'recentTask', 
               'resourceConfig', 'resourcePool', 'rootSnapshot', 'runtime', 
               'snapshot', 'storage', 'summary', 'tag', 'triggeredAlarmState', 
               'value']

# Properties for a VirtualMachine.guest Object ...
VM_EX_GUEST_PROPS = [('toolsStatus', 'toolsNotInstalled'), 
                     ('toolsVersionStatus', 'guestToolsNotInstalled'), 
                     ('toolsVersionStatus2', 'guestToolsNotInstalled'), 
                     ('toolsRunningStatus', 'guestToolsNotRunning'),
                     ('toolsVersion', '0'), 
                     ('screen', None), 
                     ('guestId', 'centos64Guest'),
                     ('guestFamily', 'linuxGuest'),
                     ('guestFullName', 'CentOS 4/5/6/7 (64-bit)'),
                     ('guestState', 'notRunning'),
                     ('ipAddress', None),
                     ('hostName', 'localhost.localdomain'),
                     ('appHeartbeatStatus', 'appStatusGray'), 
                     ('appState', 'none'),
                     ('disk', []),
                     ('guestOperationsReady', 'false'),
                     ('interactiveGuestOperationsReady', 'false')]

# properties for a disk device
DISK_DEFAULT = {
    'key': 2000,
    'deviceInfo': {
        'label': 'Hard disk 1',
        'summary': '10,485,760 KB'
    },
    'backing': {
        'filename': '',
        'datastore': '',
        'diskMode': '',
        'split': '',
        'writeThrough': '',
        'thinProvisioned': '',
        'uuid': '',
        'contentId': '',
        'digestEnabled': ''
    },
    'controllerKey': 100,
    'unitNumber': 0,
    'capacityInKB': '',
    'capacityInBytes': '',
    'shares': {
        'shares': '',
        'level': '',
    },
    'storageIOAllocation': {
        'limit': -1,
        'shares': {
            'shares': '',
            'level': ''
        },
        'reservation': 0,
    },
    'diskObjectId': '3-2000'
}


def die():
    import os; os.system('kill -9 %d' % os.getpid())

class VirtualMachineConfigInfo(object):
    def __init__(self, vid='vm-1', meta={}):
        self.vid = vid
        self.meta = meta
        self.datafile = 'fixtures/vc600_vm.config.xml'
        #self.datafile = 'fixtures/unknown_method.xml'

        with open(self.datafile, 'rb') as f:
            self.raw_xml = f.read().decode("utf-8") 

        # read in the default data
        self.data = self.load_xml(self.raw_xml)

        # change the xml data based on input meta
        self.set_meta()

        # recreate stringy xml
        self.xml = self.generate_xml()


    def set_meta(self):

        ''' Set custom values in the xml object '''

        #ipdb> self.data.Body.getchildren()
        #[<Element {urn:vim25}RetrievePropertiesExResponse at 0x7f1c93f41208>]
        #ipdb> self.data.Body
        #<Element {http://schemas.xmlsoap.org/soap/envelope/}Body at 0x7f1c93ecdc88>
        #ipdb> self.data.Body["{urn:vim25}RetrievePropertiesExResponse"]
        #<Element {urn:vim25}RetrievePropertiesExResponse at 0x7f1c93f443c8>

        # <uuid py:pytype="str" xmlns:py="http://codespeak.net/lxml/objectify/pytype">42110d45-320d-c2e7-d7d9-f6c9da6735f3</uuid>
        # <name py:pytype="str" xmlns:py="http://codespeak.net/lxml/objectify/pytype">foobar</name>

        val = self.data.Body["{urn:vim25}RetrievePropertiesExResponse"]["returnval"]["objects"]["propSet"]["val"]
        for k,v in self.meta.items():

            if not '.' in k:
                if hasattr(val, k):
                    val[k]._setText(str(v))
                elif k == 'devices':
                    for dev in val.hardware.device:
                        if hasattr(dev, 'diskObjectId'):
                            if dev.diskObjectId == k:
                                for k2,v2 in v.iteritems():
                                    setattr(dev, k2, v2)
                                break
                else:
                    print('%s not in val' % k)
                    import ipdb; ipdb.set_trace()
            else:
                # keys with periods are namespaced subvalues (hardware.memoryMB)
                parts = k.split('.')
                prop = val
                for idx,x in enumerate(parts):
                    prop = getattr(prop, x)
                prop._setText(str(v))

        # set the vim id
        self.data.Body["{urn:vim25}RetrievePropertiesExResponse"]["returnval"]["objects"]["obj"]._setText(str(self.vid))

        #pprint(splitxml(LTS(self.data), stdout=True))
        #pprint(splitxml(LTS(val), stdout=True))
        #import ipdb; ipdb.set_trace()

    def generate_xml(self):
        xml = LTS(self.data)
        #import ipdb; ipdb.set_trace()
        return xml

    def clean_xml(self, xml):
        lines = xml.split('\n')
        lines = [x.strip() for x in lines]
        return ''.join(lines)

    def load_xml(self, xml):
        data = objectify.fromstring(xml)
        #import ipdb; ipdb.set_trace()
        return data


