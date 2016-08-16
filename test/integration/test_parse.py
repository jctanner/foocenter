#!/usr/bin/env python

import re
from xml.parsers.expat import ParserCreate
from pyVmomi.SoapAdapter import ParseData


XML_ILLEGALS = u'|'.join(u'[%s-%s]' % (s, e) for s, e in [
    (u'\u0000', u'\u0008'),             # null and C0 controls
    (u'\u000B', u'\u000C'),             # vertical tab and form feed
    (u'\u000E', u'\u001F'),             # shift out / shift in
    (u'\u007F', u'\u009F'),             # C1 controls
    (u'\uD800', u'\uDFFF'),             # High and Low surrogate areas
    (u'\uFDD0', u'\uFDDF'),             # not permitted for interchange
    (u'\uFFFE', u'\uFFFF'),             # byte order marks
    ])

RE_SANITIZE_XML = re.compile(XML_ILLEGALS, re.M | re.U)


NS_SEP = " "
parser = ParserCreate(namespace_separator=NS_SEP)

f = open('resp.xml', 'r')
data = f.read()
f.close()
data = data.strip()

data2 = RE_SANITIZE_XML.sub('', data).encode('utf-8')
data2 += '\n'
data2 += 'HTTP/1.0 200 OK\n'

#print("# PARSE STANDALONE ...")
#parser.Parse(data)
#print("# PARSE W/ WRAPPER ...")
#ParseData(parser, data)

data2 = RE_SANITIZE_XML.sub('', data).encode('utf-8')
print("# PARSE STANDALONE ...")
parser.Parse(data2)
print("# PARSE W/ WRAPPER ...")
ParseData(parser, data2)
