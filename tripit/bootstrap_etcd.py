#!/usr/bin/python2.7

# This is a simple script which copies old tripit auth details into etcd.
# If you've never run the scraper, you don't need to run this script.

# $1 is a job tag, which identifies the tripit user authentication details
# in etcd.

import json
import os
import sys

import etcd


etcd_path = '/tripit/%s' % sys.argv[1]
etcd_client = etcd.Client(host='192.168.50.1', port=2379)

# Copy across our auth details
with open(os.path.expanduser('~/.tripit')) as f:
    etcd_client.write('%s/auth' % etcd_path, f.read())

# Copy across our saved trips
with open('.state') as f:
    d = json.loads(f.read())

for trip in d['cached']:
    etcd_client.write('%s/trip/%s/data' %(etcd_path, trip),
                      json.dumps(d['cached'][trip], indent=4, sort_keys=True))

for trip in d['handled']:
    etcd_client.write('%s/trip/%s/handled' %(etcd_path, trip), '1')

# Dump the finished state
def dumpdir(path):
    dir = etcd_client.get(path)
    for result in dir.children:
        if result.dir:
            dumpdir(result.key)
        else:
            print('%s: %s' %(result.key, result.value))

dumpdir(etcd_path)
