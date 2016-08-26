#!/usr/bin/env python2

import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('ggplot')


RESULTSFILE = 'results.json'

RDATA = {}
with open(RESULTSFILE, 'rb') as f:
    RDATA = f.read()
RDATA = json.loads(RDATA)
#print RDATA

records = []
for x in RDATA:
    record = []
    record.append(x['count'])

    cols = ['pysphere', 'pyvmomi']
    for col in cols:
        record.append(x[col]['duration'])        
    records.append(record)

df = pd.DataFrame.from_records(records)
df.columns = ['instancecount', 'pysphere', 'pyvmomi']
df = df.set_index(['instancecount'])


plt.figure()
plot = df.plot()
plt.title('pysphere vs. pyvmomi inventory script duration as instance count increases')
plt.ylabel('duration in seconds')
fig = plot.get_figure()
#import epdb; epdb.st()
fig.set_size_inches(16.5, 10.5)
fig.savefig('inventory_benchmark.png', bbox_inches='tight')
plt.clf()
plt.close(fig)
