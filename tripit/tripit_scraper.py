#!/usr/bin/python2.7

# $1 is a job tag, which identifies the tripit user authentication details
# in etcd.
# $2 is the location of an etcd server, as a hostname / ip and port tuple

import datetime
import json
import os
import sys
import time

import etcd
import tripit


etcd_path = None
etcd_client = None
tripit_conf = None


def ensure_token(jog_tag, etcd_server):
    global etcd_path
    global etcd_client
    global tripit_conf

    etcd_path = '/tripit/%s' % job_tag
    etcd_client = etcd.Client(host=etcd_server[0], port=int(etcd_server[1]))
    tripit_conf = json.loads(etcd_client.read('%s/auth' % etcd_path).value)

    # Log into tripit and create a key
    if not 'oauth_token' in tripit_conf:
        tripit_creds = tripit.OAuthConsumerCredential(
            str(tripit_conf['apikey']),
            str(tripit_conf['apisecret']))
        tripit_api = tripit.TripIt(tripit_creds,
                                   api_url='https://api.tripit.com')
        tripit_oauth = tripit_api.get_request_token()
        tripit_conf.update(tripit_oauth)

        etcd_client.write('%s/auth' % etcd_path,
                          json.dumps(tripit_conf, indent=4, sort_keys=True))

        print(('Please go to '
               'https://www.tripit.com/oauth/authorize?oauth_token=%s'
               '&oauth_callback=http://www.stillhq.com/ and authorize your '
               'key.'
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

        etcd_client.write('%s/auth' % etcd_path,
                          json.dumps(tripit_conf, indent=4, sort_keys=True))

def fetch_trips():
    global etcd_path
    global etcd_client
    global tripit_conf

    # Now get a list of trips
    print '%s Fetching trips' % datetime.datetime.now()
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
    print '%s Found active trip ids: %s' %(datetime.datetime.now(), trip_ids)

    for trip_id in trip_ids:
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

        etcd_client.write('%s/trip/%s/data' %(etcd_path, trip_id),
                          json.dumps(d, indent=4, sort_keys=True))
        print '%s Wrote trip %s to etcd' %(datetime.datetime.now(), trip_id)



if __name__ == '__main__':
    job_tag = sys.argv[1]
    etcd_server = sys.argv[2].split(':')

    ensure_token(job_tag, etcd_server)

    while True:
        fetch_trips()
        print '%s Sleeping for 15 minutes' % datetime.datetime.now()
        time.sleep(15 * 60)
