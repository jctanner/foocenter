#!/usr/bin/env python

import lxml
import unittest
from lib.utils import die
from lib.datasets.vm  import VirtualMachineConfigInfo


class TestVMConfigInfo(unittest.TestCase):
    def test_constructor(self):
        vmc = VirtualMachineConfigInfo()

        # should have raw_xml
        assert hasattr(vmc, 'raw_xml')

        # should have a meta property and it should be a dict
        assert hasattr(vmc, 'meta')
        assert type(vmc.meta) == dict, '%s' % type(vmc.meta)
        assert type(vmc.data) == lxml.objectify.ObjectifiedElement, '%s' % type(vmc.data)
        assert hasattr(vmc, 'generate_xml')

    def test_constructor_set_meta(self):
        meta = {
            'name': 'foobar',
            'uuid': '42110d45-320d-c2e7-d7d9-f6c9da6735f3',
            'hardware.memoryMB': 1000
        }
        vmc = VirtualMachineConfigInfo(meta=meta, vid='vm-666')

        vid = vmc.data.Body["{urn:vim25}RetrievePropertiesExResponse"]["returnval"]["objects"]["obj"]
        assert vid == 'vm-666', '%s' % vid

        val = vmc.data.Body["{urn:vim25}RetrievePropertiesExResponse"]["returnval"]["objects"]["propSet"]["val"]
        assert val.name == 'foobar'
        assert val.uuid == '42110d45-320d-c2e7-d7d9-f6c9da6735f3'
        assert val.hardware.memoryMB == 1000
        #import ipdb; ipdb.set_trace()


    def test_set_disk_meta(self):
        meta = {
            'name': 'foobar',
            'uuid': '42110d45-320d-c2e7-d7d9-f6c9da6735f3',
            'hardware.memoryMB': 1000,
            "devices": {
              "105-2000": {
                "capacityInBytes": "26843545600",
                "capacityInKB": "26214400"
              } 
            }
        }
        vmc = VirtualMachineConfigInfo(meta=meta, vid='vm-666')
        val = vmc.data.Body["{urn:vim25}RetrievePropertiesExResponse"]["returnval"]["objects"]["propSet"]["val"]

        device = None
        for dev in val.hardware.device:
            if hasattr(dev, 'diskObjectId'):
                if dev.diskObjectId == '105-2000':
                    device = dev
        assert device != None
        assert int(device.capacityInBytes) == 26843545600, '%s' % type(device.capacityInBytes)
        assert int(device.capacityInKB) == 26214400, '%s' % type(device.capacityInKB)


