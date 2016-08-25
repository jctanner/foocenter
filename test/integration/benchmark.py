#!/usr/bin/env python2

import datetime
import json
import os
import requests
import sys
import subprocess


def run_command(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (so, se) = p.communicate()
    return (p.returncode, so, se)

def main():

    results = []

    for i in xrange(20, 1000, 5):

        res = {'count': i}

        r = requests.post('https://localhost:443/xapi/inventory', verify=False, json={'vms': str(i)})

        commands = [
            ('pysphere', "./vmware.py | jq '.all.hosts' | wc -l"),
            ('pyvmomi', "./vmware_inventory.py --refresh-cache | jq '.all.hosts' | wc -l")
        ]

        for command in commands:
            print command

            start = datetime.datetime.now()
            (rc, so, se) = run_command(command[1])
            stop = datetime.datetime.now()
            duration = (stop - start)

            print "rc: %s" % rc
            print "so: %s" % so.strip()
            print "se: %s" % se.strip()
            print "start: %s" % start
            print "stop: %s" % stop
            print "duration: %s" % duration

            res[command[0]] = duration.seconds
        
        
        # save it
        results.append(res)
        with open('results.json', 'wb') as f:
            f.write(json.dumps(results, indent=2))            






if __name__ == '__main__':
    main()
