#!/usr/bin/python3

import copy
import datetime
import dateutil.parser
import json
import os
import sys

import todoist


with open(os.path.expanduser('~/.todoist')) as f:
    todoist_conf = json.loads(f.read())

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

# We really need the state file to exist, so deliberately crash here if it
# doesn't.
with open('.state') as f:
    state = json.loads(f.read())

try:
    for trip_id in state['cached']:
        if trip_id in state['handled']:
            continue

        d = copy.deepcopy(state['cached'][trip_id])
        d['start_date'] = dateutil.parser.parse(d['start_date'])
        d['end_date'] = dateutil.parser.parse(d['end_date'])

        print('Considering %s' % d['display_name'])
        now = datetime.datetime.now()
        distance = d['start_date'] - now
        if distance.days > 14:
            print('... Trip too far away')
            continue

        def process_todos(tripname, todo_due_date, section):
            for todo in todoist_conf[section]:
                if todo.startswith('#include:'):
                    process_todos(tripname, todo_due_date, todo.split(':')[1])
                    continue

                todo_item = '%s: %s' %(tripname, todo)
                todo_due = '%02d/%02d/%04d' %(todo_due_date.month,
                                              todo_due_date.day,
                                              todo_due_date.year)
                print('Creating %s @ %s' %(todo_item, todo_due))
                todoist_api.items.add(todo_item, project,
                                      date_string=todo_due)
                todoist_api.commit()

        todo_due_date = d['start_date']
        todo_due_date -= datetime.timedelta(days=2)
        duration = d['end_date'] - d['start_date']
        
        if not d['primary_location'].lower().endswith(', australia'):
            # International trip
            process_todos(d['display_name'], todo_due_date,
                          'internationaltrip')
            state['handled'].append(trip_id)
            continue
        
        if d['display_name'].lower().endswith(' camp'):
            # Camps
            if duration.days > 4:
                typestring = 'verylongcamp'
            else:
                typestring = 'camp'

            process_todos(d['display_name'], todo_due_date, typestring)
            state['handled'].append(trip_id)
            continue
        
        if d['display_name'].lower().endswith(' hike'):
            # Hiking
            process_todos(d['display_name'], todo_due_date, 'hike')
            state['handled'].append(trip_id)
            continue

        if duration.days < 3:
            # Short domestic trip
            process_todos(d['display_name'], todo_due_date,
                          'shorttrip')
            state['handled'].append(trip_id)
            continue

        # Long domestic trip
        process_todos(d['display_name'], todo_due_date, 'longtrip')
        state['handled'].append(trip_id)

finally:
    with open('.state', 'w') as f:
        f.write(json.dumps(state, indent=4, sort_keys=True))
