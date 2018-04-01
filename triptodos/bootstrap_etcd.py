#!/usr/bin/python2.7

# This is a simple script which copies old tripit auth details into etcd.
# If you've never run the scraper, you don't need to run this script.

# $1 is a job tag, which identifies the tripit user authentication details
# in etcd.

import json
import os
import sys

import etcd


etcd_path = '/todoist/%s' % sys.argv[1]
etcd_client = etcd.Client(host='192.168.50.1', port=2379)

# Copy across our auth details
with open(os.path.expanduser('~/.todoist')) as f:
    etcd_client.write('%s/auth' % etcd_path, f.read())

# Dump the finished state
def dumpdir(path):
    dir = etcd_client.get(path)
    for result in dir.children:
        if result.dir:
            dumpdir(result.key)
        else:
            print('%s: %s' %(result.key, result.value))

dumpdir(etcd_path)
