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
HEADERS = {'Content-Type': 'application/json'}
VERSION_CREATED_ID = {}


def test_request(request):
    if request.status_code in [200, 201]:
        print 'Request Ok'
        version_id = None
        try:
            version_id = (request.json())['version']['id']
        except ValueError:
            pass
        return version_id
    else:
        print 'Unprocessable Entity: Error %s \n' % str(request.status_code)\
            + 'version was not created due to validation failures' \
            + '\n' + request.text
        return


def create_version(project_id, project_name, version):
    version = {
        'version': {
            'project': {
                'id': project_id,
            },
            'name': project_name + '-' + version,
            'status': 'open',
            'sharing': 'tree'
        }
    }
    return version


def post_version(version, project_id, project_name):
    post_url = REDMINE_URL + '/projects/%s/versions.json' % str(project_id)
    parameters_json = json.dumps(
        create_version(project_id, project_name, version))

    request = requests.post(post_url, auth=(API_KEY, ''), data=parameters_json,
        headers=HEADERS)
    print 'version ', project_name
    VERSION_CREATED_ID[project_name] = test_request(request)


def read_issues():
    with open('issues.json') as file:
        issues = json.load(file)
    return issues


def link_issue_to_version(issue_id, project_name):
    put_url = REDMINE_URL + '/issues/%s.json' % str(issue_id)
    linked_version = {
        'issue': {
            'fixed_version_id': VERSION_CREATED_ID[project_name]
        }
    }
    parameters_json = json.dumps(linked_version)
    request = requests.put(put_url, auth=(API_KEY, ''), data=parameters_json,
        headers=HEADERS)
    test_request(request)


def main():
    try:
        _, version = sys.argv
    except ValueError:
        sys.stderr.write('''
    Usage :
        create_version.py <version>

        Will create version <version> on every project
    ''')
        return 1

    post_version(version, 91, 'coog')
    for c_name, c_id in CUSTOMERS_PROJECT_ID.iteritems():
        post_version(version, c_id, c_name)

    print VERSION_CREATED_ID

    issues = read_issues()
    for project in issues.keys():
        if project not in CUSTOMERS_PROJECT_ID.keys() and issues[project]:
            for issue in issues[project]:
                print 'issue: ', issue
                link_issue_to_version(issue, 'coog')
        else:
            for issue in issues[project]:
                print 'issue: ', issue
                link_issue_to_version(issue, project)


if __name__ == '__main__':
    main()
