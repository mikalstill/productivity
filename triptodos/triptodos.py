#!/usr/bin/python3

import copy
import datetime
import dateutil.parser
import json
import os
import sys

import etcd
import todoist


tripit_path = '/tripit/%s' % sys.argv[1]
todoist_path = '/todoist/%s' % sys.argv[1]
etcd_server = sys.argv[2].split(':')
etcd_client = etcd.Client(host=etcd_server[0], port=int(etcd_server[1]))
todoist_conf = json.loads(etcd_client.read('%s/auth' % todoist_path).value)

# Log into todoist and find the "Travel" project
todoist_api = todoist.TodoistAPI()
user = todoist_api.user.login(todoist_conf['username'],
                              todoist_conf['password'])
todoist_api.sync()
projects = todoist_api.state['projects']

project = None
for p in projects:
    if p['name'] == 'Travel':
        project = p['id']

print('Target project is %s' % project)

for trip_path in etcd_client.get('%s/trip' % tripit_path).children:
    trip_id = trip_path.key.split('/')[-1]
    try:
        print(trip_id)
        etcd_client.read('%s/trip/%s/handled' %(tripit_path, trip_id))
        continue
    except etcd.EtcdKeyNotFound:
        pass

    d = json.loads(etcd_client.get('%s/trip/%s/data'
                                   %(tripit_path, trip_id)).value)
    d['start_date'] = dateutil.parser.parse(d['start_date'])
    d['end_date'] = dateutil.parser.parse(d['end_date'])

    print('Considering %s' % d['display_name'])
    now = datetime.datetime.now()
    distance = d['start_date'] - now
    if distance.days > 31:
        print('... Trip too far away')
        continue

    def process_todos(tripname, long_before_trip_date, before_trip_date, after_trip_date,
                      section):
        for todo in todoist_conf[section]:
            if todo.startswith('#include:'):
                process_todos(tripname, long_before_trip_date, before_trip_date, after_trip_date,
                              todo.split(':')[1])
                continue

            elif todo.startswith('#longbefore:'):
                todo_due = '%02d/%02d/%04d' %(long_before_trip_date.month,
                                              long_before_trip_date.day,
                                              long_before_trip_date.year)

            elif todo.startswith('#before:'):
                todo_due = '%02d/%02d/%04d' %(before_trip_date.month,
                                              before_trip_date.day,
                                              before_trip_date.year)

            elif todo.startswith('#after:'):
                todo_due = '%02d/%02d/%04d' %(after_trip_date.month,
                                              after_trip_date.day,
                                              after_trip_date.year)

            else:
                todo_due = '%02d/%02d/%04d' %(before_trip_date.month,
                                              before_trip_date.day,
                                              before_trip_date.year)

            todo_item = '%s: %s' %(tripname, todo)
            print('Creating %s @ %s' %(todo_item, todo_due))
            todoist_api.items.add(todo_item, project,
                                  date_string=todo_due)
            todoist_api.commit()

    long_before_trip_date = d['start_date']
    long_before_trip_date -= datetime.timedelta(days=30)
    before_trip_date = d['start_date']
    before_trip_date -= datetime.timedelta(days=2)
    after_trip_date = d['end_date']
    after_trip_date += datetime.timedelta(days=1)
    duration = d['end_date'] - d['start_date']

    if not d['primary_location'].lower().endswith(', australia'):
        # International trip
        process_todos(d['display_name'],
                      long_before_trip_date,
                      before_trip_date,
                      after_trip_date,
                      'internationaltrip')
        etcd_client.write('%s/trip/%s/handled' %(tripit_path, trip_id), 1)
        continue

    if d['display_name'].lower().endswith(' camp'):
        # Camps
        if duration.days > 4:
            typestring = 'verylongcamp'
        else:
            typestring = 'camp'

        process_todos(d['display_name'],
                      long_before_trip_date,
                      before_trip_date,
                      after_trip_date,
                      typestring)
        etcd_client.write('%s/trip/%s/handled' %(tripit_path, trip_id), 1)
        continue

    if d['display_name'].lower().endswith(' hike'):
        # Hiking
        process_todos(d['display_name'],
                      long_before_trip_date,
                      before_trip_date,
                      after_trip_date,
                      'hike')
        etcd_client.write('%s/trip/%s/handled' %(tripit_path, trip_id), 1)
        continue

    if d['display_name'].lower().endswith(' hike course'):
        # Hiking
        process_todos(d['display_name'],
                      long_before_trip_date,
                      before_trip_date,
                      after_trip_date,
                      'hike course')
        etcd_client.write('%s/trip/%s/handled' %(tripit_path, trip_id), 1)
        continue

    if duration.days < 1:
        # Day trip
        process_todos(d['display_name'],
                      long_before_trip_date,
                      before_trip_date,
                      after_trip_date,
                      'daytrip')
        etcd_client.write('%s/trip/%s/handled' %(tripit_path, trip_id), 1)
        continue

    elif duration.days < 3:
        # Short domestic trip
        process_todos(d['display_name'],
                      long_before_trip_date,
                      before_trip_date,
                      after_trip_date,
                      'shorttrip')
        etcd_client.write('%s/trip/%s/handled' %(tripit_path, trip_id), 1)
        continue

    # Long domestic trip
    process_todos(d['display_name'],
                  long_before_trip_date,
                  before_trip_date,
                  after_trip_date,
                  'longtrip')
    etcd_client.write('%s/trip/%s/handled' %(tripit_path, trip_id), 1)
