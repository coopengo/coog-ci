#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import sys
import json

conf_file = 'bl.conf'
try:
    with open(conf_file) as conf:
        data = json.load(conf)
except IOError:
    sys.stderr.write('No conf file found\n')
    sys.exit(1)

if not data:
    sys.stderr.write('No data found, check %s !\n' % conf_file)
    sys.exit(1)

REDMINE_URL = data['redmine_url']
PUBLIC_PROJECT_ID = {"public": 91}
COMMON_PROJECTS_ID = {"coog": 31}
CUSTOMERS_PROJECT_ID = data['customers']
API_KEY = data['api_key']


def create_version(version, project_id, project_name, api_key):
    post_url = REDMINE_URL + '/projects/'\
        + '%s' % str(project_id)\
        + '/versions/%s_%s' % project_name, version
    request = requests.post(post_url, auth=(api_key, ''))
    if request.status_code == 201:
        print 'Version created'
    else:
        print 'Unprocessable Entity: version was not created due to \
            validation failures'
    return


def main():
    try:
        _, version_name = sys.argv
    except ValueError:
        sys.stderr.write('''
    Usage :
        create_version.py <version>

        Will create version <version> on every project
    ''')
        return 1

    create_version(version_name, 31, 'coog', API_KEY)


if __name__ == '__main__':
    main()
