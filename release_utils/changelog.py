import argparse
import os
import json
import requests
from subprocess import check_output
from collections import OrderedDict


class ChangeLogIndex(object):
    """
    Extracts a list of changelog entries to a text file
    """

    def cmd(self, c):
        return check_output(c.split())

    def __init__(self, path):
        self.path = os.path.abspath(path)
        conf_file = os.path.join(os.path.dirname(__file__), '../bl.conf')
        with open(conf_file, 'r') as conf:
            self.conf = json.load(conf)
        self.changelogs = OrderedDict()
        for fname in sorted(
                self.cmd("find %s -name CHANGELOG" % self.path).split()):
            with open(fname, 'r') as f:
                self.changelogs[fname] = f.read().split('\n')

    def match(self, line, tracker):
        return {"feature": "FEA#", "bug": "BUG#"}.get(tracker) in line

    def get_changelog_entries(self, tracker, version='next'):
        res = OrderedDict()

        for fname, text in self.changelogs.iteritems():
            section = None
            for l in text:
                if l.strip().startswith("Version "):
                    section = l.split()[1]
                    continue
                if ((version == 'next' and section is None)
                        or (version == section)) and self.match(l, tracker):
                    if fname not in res:
                        res[fname] = []
                    res[fname].append(l)
        if not res:
            print("No entries found for tracker '%s' and version '%s'"
                % (tracker, version))
        return res

    def get_redmine_items(self, search_url, item_name):
        all_items = []
        resp = requests.get(search_url, auth=(self.conf["api_key"], '')).json()
        total = resp['total_count']
        all_items.extend(resp[item_name])
        offset = 100
        while len(all_items) < total:
            resp = requests.get(search_url + '&offset=%s' % offset,
                    auth=(self.conf["api_key"], '')).json()
            all_items.extend(resp[item_name])
            offset += 100
        return all_items

    def get_features_not_in_changelogs(self):
        project_id = 1  # Coog
        status_ids = "3|5"  # resolved, closed
        tracker_id = 2  # feature

        version_url = self.conf["redmine_url"] + "/projects/coog/versions.json"
        versions = self.get_redmine_items(version_url, "versions")

        majors = [x for x in versions if x["name"].startswith("Coog-")
                or x["name"].startswith("Coog ")]
        major = sorted(majors, key=lambda x: x["id"])[-1]
        major_number = major["name"].replace(" ", "-").split("-")[1]
        X, Y = major_number.split(".")
        sprints_number = int(Y) - 1
        sprint_descriptor = "Sprint " + X + '.' + str(sprints_number)

        fixed_version_id = str(major["id"])
        fixed_version_ids = "|".join([str(x["id"]) for x in versions
            if sprint_descriptor in x["name"]] + [fixed_version_id])

        search_url = self.conf["redmine_url"] + '/issues.json'\
            + '?project_id=%s&fixed_version_id=%s&tracker_id=%s'\
            '&status_id=%s&limit=100' % (
                    project_id, fixed_version_ids, tracker_id, status_ids)
        issues = self.get_redmine_items(search_url, "issues")
        entries = sum(self.get_changelog_entries('feature').values(), [])
        return [x for x in issues if "FEA#" + str(x['id'])
                not in ''.join(entries)]

    def dump(self, tracker, language, version, output_path):
        for p, entries in self.get_changelog_entries(tracker,
                version).iteritems():
            if "/%s/" % language in p:
                pl = p.split("/")
                module_name = pl[pl.index("modules") + 1]
                with open(output_path, 'a') as f:
                    f.write("MODULE : " + module_name + "\n")
                    f.write("\n".join(entries))
                    f.write("\n\n")
        if tracker == 'feature' and version == "next":
            missings = self.get_features_not_in_changelogs()
            if missings:
                with open(output_path, 'a') as f:
                    f.write("FEATURES OF NEXT VERSION WITHOUT CHANGELOGS:\n")
            for missing in missings:
                with open(output_path, 'a') as f:
                    to_write = "feature %s : %s" % (missing["id"],
                            missing["subject"])
                    f.write(to_write.encode("utf8") + "\n")


def main():
    parser = argparse.ArgumentParser(
            description="Extracts a list of changelog entries")
    parser.add_argument('repository',
            help="Path to the repository")
    parser.add_argument('tracker', choices=["feature", "bug"],
            help="The tracker of the entries we want to extract")
    parser.add_argument('language',
            help="The target language")
    parser.add_argument('version', default="next",
            help="The version we target for extraction. "
            "For next release, use 'next'")
    parser.add_argument('output',
            help="The output file name")
    args = parser.parse_args()

    index = ChangeLogIndex(args.repository)
    index.dump(args.tracker, args.language, args.version,
            args.output)

if __name__ == '__main__':
    main()
