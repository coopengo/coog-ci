#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

projects = {}


def read_file():
    with open('issues') as file:
        project = ''
        for line in file:
            try:
                line = int(line)
            except ValueError:
                project = line[:-1]
                projects[project] = []
                continue
            projects[project].append(line)


read_file()
if projects:
    with open('issues.json', 'w') as f:
        f.write(json.dumps(projects))
        with open('issues', 'w') as i:
            i.write('')
else:
    print 'No issue to convert'
