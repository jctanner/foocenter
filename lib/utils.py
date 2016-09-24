#!/usr/bin/env python

import logging
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

def splitxml(xmlobj, stdout=None):
    if type(xmlobj) in [str, bytes]:
        rxml = xml.dom.minidom.parseString(xmlobj)
    else:
        rxml = xml.dom.minidom.parseString(TS(xmlobj).decode("utf-8"))
    pxml = rxml.toprettyxml()
    lines = [x for x in pxml.split('\n') if x.strip()]
    for line in lines:
        if stdout:
            print(line)
        else:
            logging.debug(line)


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

    # http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    rxml = xml.dom.minidom.parseString(TS(elem))
    pxml = rxml.toprettyxml()

    # get rid of the xml header
    lines = [x for x in pxml.split('\n')]
    pxml = '\n'.join(lines[1:])
    return pxml


