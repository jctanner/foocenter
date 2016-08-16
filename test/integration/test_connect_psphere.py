#!/usr/bin/env python
import ssl
from pysphere import VIServer, VIProperty, MORTypes
#>>> client = Client("server.esx.com", "Administrator", "strongpass")

def main():
    default_context = ssl._create_default_https_context
    ssl._create_default_https_context = ssl._create_unverified_context
    viserver = VIServer()
    viserver.connect('localhost', 'test', 'test')

if __name__ == "__main__":
    main()
