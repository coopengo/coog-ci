#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import requests
import sys
import json
from collections import defaultdict

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
COMMON_PROJECTS_ID = data['coog']
CUSTOMERS_PROJECT_ID = data['customers']
API_KEY = data['api_key']


def read_issues():
    with open('issues') as file:
        issues = [int(line) for line in file]
    return issues


def get_issues(fixed_issues, api_key):
    for sublist in fixed_issues:
        for issue in sublist:
            search_url = REDMINE_URL + '/issues/'\
                + '%s.json?include=relations' % issue
            request = requests.get(search_url, auth=(api_key, ''))
            parsed = request.json()['issue']
            if not parsed:
                sys.stderr.write('No issue found, check redmine api key !\n')
                sys.exit()
            yield parsed


def main():
    try:
        _, version_name, project_name = sys.argv
    except ValueError:
        sys.stderr.write('''
    Usage :
        bl.py <version_name> <project_name>

        Will output html with all closed issues of version <version_name>
    ''')
        return 1

    fixed_issues = read_issues()
    if not fixed_issues:
        sys.stderr.write("No issue to treat")
        return 1
    # split fixed_issues in sublists with max 100 issues
    fixed_issues = [fixed_issues[x: x + 100] for x in
        xrange(0, len(fixed_issues), 100)]

    features, bugs, params, scripts = \
        defaultdict(list), defaultdict(list), [], []
    for issue in get_issues(fixed_issues, API_KEY):
        issue['custom_fields'] = {x['id']: x.get('value', '').encode('utf-8')
            for x in issue.get('custom_fields', {}) if not x.get('multiple',
               False)}
        if issue['status']['id'] == 6:
            # Rejected => ignored
            continue
        if issue['project']['id'] not in COMMON_PROJECTS_ID and \
                project_name == 'coog':
            # client issue => ignored if printing general BL
            continue
        issue['subject'] = issue['subject'].encode('utf-8')
        issue['updated_on'] = datetime.datetime.strptime(issue['updated_on'],
            '%Y-%m-%dT%H:%M:%SZ')
        if issue['tracker']['name'] == 'Feature':
            features[issue['priority']['name']].append(issue)
        else:
            bugs[issue['priority']['name']].append(issue)
        # Custom field 7 => Param
        if issue['custom_fields'].get(7, ''):
            params.append(issue)
        # Custom field 9 => Script
        if issue['custom_fields'].get(9, ''):
            scripts.append(issue)

    report_html(version_name, features, bugs, params, scripts)


def get_issue_id(issue):
    return '<a href="https://support.coopengo.com/issues/%i' \
        % issue + '">%i</a>' % issue


def get_related_issues(issue):
    if 'relations' in issue:
        relates = []
        for relate in issue['relations']:
            issue_id = get_issue_id(relate['issue_id'])
            issue_to_id = get_issue_id(relate['issue_to_id'])
            if issue_id == issue['id']:
                relates.append(issue_to_id)
            else:
                relates.append(issue_id)
        return relates
    return []


def report_html(version_name, features, bugs, params, scripts):
    print '<html>'
    print '<head>'
    print '<meta charset="utf-8"/>'
    print '<style>'
    print '''
    h1 {
        font-size: 150%;
    }
    h2 {
        font-size: 120%;
    }
    table {
        border:#ccc 1px solid
        table-layout: fixed;
        width: 700px;
        border-width: 1px;
        border-color: #666666;
        border-collapse: collapse;
        border-spacing: 10px;
    }
    th {
        font-size: 90%;
        align: left;
        border-width: 1px;
        padding: 5px;
        border-style: solid;
        border-color: #666666;
        background-color: #dedede;
    }
    td {
        font-size: 80%;
        border-width: 1px;
        vertical-align: middle;
        padding: 2px;
        border-style: solid;
        border-color: #666666;
        background-color: #ffffff;
    }
    tr td:first-child {
        width: 70px;
    }
    tr td:last-child {
        min-width: 40px;
    }
    '''
    print '</style>'
    print '</head>'
    print '<body>'

    count = 1
    print '<h2>Version: %s</h2>' % version_name
    if features:
        print '<h2>%i. Fonctionnalités</h2>' % count
        count += 1
        print '<table>'
        print '    <tr><th>#</th><th>Priorité</th><th>Sujet</th>' + \
            '<th>Fiches liées</th></tr>'
        for priority in ('Immediate', 'High', 'Normal', 'Low'):
            issues = features[priority]
            if not issues:
                continue
            for issue in issues:
                print '    <tr><td>' + '</td><td>'.join([get_issue_id(
                            issue['id']),
                        issue['priority']['name'].encode('utf-8'),
                        issue['subject'],
                        '        <div>' + '</div>'.join(
                            get_related_issues(issue)) + '</div>',
                        ]) + '</td></tr>'
        print '</table>'

    if bugs:
        print '<h2>%i. Anomalies</h2>' % count
        count += 1
        print '<table>'
        print '    <tr><th>#</th><th>Priorité</th><th>Sujet</th>' + \
            '<th>Fiches liées</th></tr>'
        for priority in ('Immediate', 'High', 'Normal', 'Low'):
            issues = bugs[priority]
            if not issues:
                continue
            for issue in issues:
                print '    <tr><td>' + '</td><td>'.join([get_issue_id(
                            issue['id']),
                        issue['priority']['name'].encode('utf-8'),
                        issue['subject'],
                        '        <div>' + '</div>'.join(
                            get_related_issues(issue)) + '</div>',
                        ]) + '</td></tr>'
        print '</table>'

    if params:
        print '<h2>%i. Params</h2>' % count
        count += 1
        print '<table>'
        print '    <tr><th>#</th><th>Subject</th><th width="200">Param ' + \
            '</th><th>Fiches liées</th></tr>'
        for issue in params:
            print '    <tr><td>' + get_issue_id(issue['id']) + '</td><td>' + \
                issue['subject'] + '</td><td>' + \
                issue['custom_fields'][7] + '</td><td>' + \
                '        <div>' + '</div>'.join(
                    get_related_issues(issue)) + '</div>',
        print '</table>'

    if scripts:
        print '<h2>%i. Scripts</h2>' % count
        count += 1
        print '<table>'
        print '    <tr><th>#</th><th>Subject</th><th width="200">Script' + \
            '</th><th>Fiches liées</th></tr>'
        for issue in scripts:
            print '    <tr><td>' + get_issue_id(issue['id']) + '</td><td>' + \
                issue['subject'] + '</td><td>' + \
                issue['custom_fields'][9] + '</td><td>' + \
                '        <div>' + '</div>'.join(
                    get_related_issues(issue)) + '</div>',
        print '</table>'
    print '</body>'
    print '</html>'


if __name__ == '__main__':
    main()
