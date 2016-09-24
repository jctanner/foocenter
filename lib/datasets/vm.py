#!usr/bin/env python

import uuid
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element as E
from xml.etree.ElementTree import SubElement as SE
from xml.etree.ElementTree import tostring as TS
import xml.dom.minidom

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

# a hardware set for a virtualmachine
VM_HARDWARE_DEFAULT = {
    'numCPU': '',
    'numCoresPerSocket': '',
    'memoryMB': '',
    'virtualICH7MPresent': '',
    'virtualSMCPresent': '',
    'devices': [
        DISK_DEFAULT.copy()
    ]
}

class VMHardware(object):
    def __init__(self):
        self._hardware = VM_HARDWARE_DEFAULT.copy()    
    
