#!/usr/bin/python2.7

import datetime
import json
import os
import sys

from tripit import tripit


with open(os.path.expanduser('~/.tripit')) as f:
    tripit_conf = json.loads(f.read())

# Log into tripit and create a key
if not 'oauth_token' in tripit_conf:
    tripit_creds = tripit.OAuthConsumerCredential(
        str(tripit_conf['apikey']),
        str(tripit_conf['apisecret']))
    tripit_api = tripit.TripIt(tripit_creds,
                               api_url='https://api.tripit.com')
    tripit_oauth = tripit_api.get_request_token()
    tripit_conf.update(tripit_oauth)

    with open(os.path.expanduser('~/.tripit'), 'w') as f:
        f.write(json.dumps(tripit_conf, indent=4, sort_keys=True))
    
    print(('Please go to https://www.tripit.com/oauth/authorize?oauth_token=%s'
           '&oauth_callback=http://www.stillhq.com/ and authorize your key.'
           % tripit_oauth['oauth_token']))
    sys.exit(1)

elif not 'authorized' in tripit_conf:
    tripit_creds = tripit.OAuthConsumerCredential(
        str(tripit_conf['apikey']),
        str(tripit_conf['apisecret']),
        str(tripit_conf['oauth_token']),
        str(tripit_conf['oauth_token_secret']))
    tripit_api = tripit.TripIt(tripit_creds,
                               api_url='https://api.tripit.com')
    tripit_oauth = tripit_api.get_access_token()
    tripit_conf.update(tripit_oauth)
    tripit_conf['authorized'] = True

    with open(os.path.expanduser('~/.tripit'), 'w') as f:
        f.write(json.dumps(tripit_conf, indent=4, sort_keys=True))

# Now get a list of trips
tripit_creds = tripit.OAuthConsumerCredential(
    str(tripit_conf['apikey']),
    str(tripit_conf['apisecret']),
    str(tripit_conf['oauth_token']),
    str(tripit_conf['oauth_token_secret']))
tripit_api = tripit.TripIt(tripit_creds,
                           api_url='https://api.tripit.com')

trip_ids = []
for child in tripit_api.list_trip(
        filter=[('traveler', 'true'),
                ('include_objects', 'false')]).get_children():
    # For now, only trips have ids, so let's find those
    try:
        trip_ids.append(child.__getattr__('id'))
    except:
        pass

# Stash details for all those trips
if os.path.exists('.state'):
    with open('.state') as f:
        state = json.loads(f.read())
else:
    state = {}

state.setdefault('handled', [])
state.setdefault('cached', {})

try:
    for trip_id in trip_ids:
        if trip_id in state['cached']:
            continue

        t = tripit_api.get_trip(trip_id).get_children()[0]
        d = {}
        for attr in t.get_attribute_names():
            d[attr] = t.__getattr__(attr)

        # 'display_name': 'Denver PTG',
        # 'relative_url': '/trip/show/id/197348092',
        # 'end_date': datetime.date(2017, 9, 23),
        # 'id': '197348092',
        # 'last_modified': '1502918680',
        # 'image_url': 'https://www.tripit.com/images/places/losangeles.jpg'
        # 'primary_location': 'Los Angeles, CA'
        # 'start_date': datetime.date(2017, 9, 4)
        # 'is_private': 'false'

        d['start_date'] = d['start_date'].isoformat()
        d['end_date'] = d['end_date'].isoformat()
        
        state['cached'][trip_id] = d
        print 'Caching %s' % trip_id

finally:
    with open('.state', 'w') as f:
        f.write(json.dumps(state, indent=4, sort_keys=True))
