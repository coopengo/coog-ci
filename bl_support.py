#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import requests
import sys
import json
from collections import defaultdict

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
COMMON_PROJECTS_ID = data['coog']
CUSTOMERS_PROJECT_ID = data['customers']
API_KEY = data['api_key']


def read_issues():
    with open('issues.json') as file:
        issues = json.load(file)
    return issues


def get_issue(issue):
    search_url = REDMINE_URL + '/issues/'\
        + '%s.json?include=relations' % issue
    request = requests.get(search_url, auth=(API_KEY, ''))
    parsed = request.json()['issue']
    if not parsed:
        sys.stderr.write('No issue found, check redmine api key !\n')
        sys.exit()
    return parsed


def sort_before_report(project, issues):
    features, bugs, params, scripts = \
        defaultdict(list), defaultdict(list), [], []

    for issue in issues:
        issue = get_issue(issue)
        issue['custom_fields'] = {x['id']:
                x.get('value', '').encode('utf-8')
                for x in issue.get('custom_fields', {})
                if not x.get('multiple', False)}
        if issue['project']['id'] not in COMMON_PROJECTS_ID and \
                project == 'coog':
            sys.stderr.write('issue %s not in the right project' % issue)
            # client issue => need to manual link it to client project
            continue
        issue['subject'] = issue['subject'].encode('utf-8')
        issue['updated_on'] = datetime.datetime.strptime(
            issue['updated_on'], '%Y-%m-%dT%H:%M:%SZ')
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
    sorted_project = {}
    sorted_project['features'] = features
    sorted_project['bugs'] = bugs
    sorted_project['params'] = params
    sorted_project['scripts'] = scripts
    return sorted_project


def main():
    try:
        _, version_name = sys.argv
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

    # move all non customers issues in coog project
    linked_issues = read_issues()
    for project, issues in fixed_issues.iteritems():
        if project not in CUSTOMERS_PROJECT_ID.keys() and project != 'coog':
            linked_issues['coog'] += fixed_issues[project]
            del linked_issues[project]

    delivery_notes = {}
    for project, issues in linked_issues.iteritems():
        if project in CUSTOMERS_PROJECT_ID.keys():
            delivery_notes[project] = sort_before_report(project, issues)
        else:
            delivery_notes['coog'] = sort_before_report('coog', issues)

    for project in delivery_notes.keys():
        filename = project + '-' + version_name + '.html'
        if project != 'coog':
            delivery_notes[project]['features'].update(
                delivery_notes['coog']['features'])
            delivery_notes[project]['bugs'].update(
                delivery_notes['coog']['bugs'])
            delivery_notes[project]['params'] += \
                delivery_notes['coog']['params']
            delivery_notes[project]['scripts'] += \
                delivery_notes['coog']['scripts']
        report_html(filename, version_name,
                delivery_notes[project]['features'],
                delivery_notes[project]['bugs'],
                delivery_notes[project]['params'],
                delivery_notes[project]['scripts'])


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


def report_html(filename, version_name, features, bugs, params, scripts):
    with open('reports/' + filename, 'w') as file:
        sys.stdout = file
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
            print '<h2>%i. Fiches avec paramétrage</h2>' % count
            count += 1
            print '<table>'
            print '    <tr><th>#</th><th>Subject</th><th width="200">Param ' +\
                '</th><th>Fiches liées</th></tr>'
            for issue in params:
                print '    <tr><td>' + get_issue_id(issue['id']) + \
                    '</td><td>' + \
                    issue['subject'] + '</td><td>' + \
                    issue['custom_fields'][7] + '</td><td>' + \
                    '        <div>' + '</div>'.join(
                        get_related_issues(issue)) + '</div>',
            print '</table>'

        if scripts:
            print '<h2>%i. Fiche avec scripts</h2>' % count
            count += 1
            print '<table>'
            print '    <tr><th>#</th><th>Subject</th><th width="200">Script' +\
                '</th><th>Fiches liées</th></tr>'
            for issue in scripts:
                print '    <tr><td>' + get_issue_id(issue['id']) + \
                    '</td><td>' + \
                    issue['subject'] + '</td><td>' + \
                    issue['custom_fields'][9] + '</td><td>' + \
                    '        <div>' + '</div>'.join(
                        get_related_issues(issue)) + '</div>',
            print '</table>'
        print '</body>'
        print '</html>'


if __name__ == '__main__':
    main()
