#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import sys
import json
import datetime

conf_file = 'bl.conf'
try:
    with open(conf_file, 'r') as conf:
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
        except KeyError:
            pass
        return version_id
    else:
        print 'Unprocessable Entity: Error %s \n' % str(request.status_code)\
            + 'version was not created due to validation failures' \
            + '\n' + request.text
        return


def create_version(project_id, project_name, version, customer_version):
    if not customer_version:
        sharing = 'tree'
    else:
        sharing = 'descendants'
    version = {
        'version': {
            'project': {
                'id': project_id,
            },
            'name': project_name + '-' + version,
            'status': 'open',
            'sharing': sharing,
            'due_date': datetime.date.today().isoformat(),
        }
    }
    return version


def post_version(version, project_id, project_name, customer_version):
    post_url = REDMINE_URL + '/projects/%s/versions.json' % str(project_id)
    parameters_json = json.dumps(
        create_version(project_id, project_name, version, customer_version))

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
    get_request = requests.get(put_url, auth=(API_KEY, ''), headers=HEADERS)
    if(get_request.status_code not in [200, 201]):
        return
    field = [VERSION_CREATED_ID[project_name]]
    for fields in (get_request.json())['issue']['custom_fields']:
        if fields['id'] == 37:
            field.extend(fields['value'])
    linked_version = {
        'issue': {
            'custom_fields': [
                {
                    'value': field,
                    'id': 37
                }
            ]
        }
    }
    parameters_json = json.dumps(linked_version)
    request = requests.put(put_url, auth=(API_KEY, ''), data=parameters_json,
        headers=HEADERS)
    print 'linking issue %s to project %s' % (issue_id, project_name)
    test_request(request)


def close_versions():
    close_data = {'version': {'status': 'closed'}}
    close_data = json.dumps(close_data)
    for project_name, version_id in VERSION_CREATED_ID.iteritems():
        requests.put(REDMINE_URL + '/versions/%s.json' % version_id,
            auth=(API_KEY, ''), data=close_data, headers=HEADERS)


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

    post_version(version, 91, 'coog', False)
    for c_name, c_id in CUSTOMERS_PROJECT_ID.iteritems():
        post_version(version, c_id, c_name, True)

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

    close_versions()

if __name__ == '__main__':
    main()
