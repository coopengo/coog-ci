## coog-ci

This repo contains a set of scripts used for coog continuous integration.

### How to use it

- connect to the integration server (ci.coopengo.com)
- go to coog-ci
- run
```
./version -t <tag> -p /home/coog/workspace -d <last_success_test_passing_date>
./report -v <version> -o <version_you_want_to_diff_with> -p /home/coog/workspace
```
**Warning** : The version will include all commits **strictly <** to the given date, so if you want to include today's commits, you should give the day after (tomorrow)

These commands should :
- update in-app version
- create tags in all coog repositories
- create a version for each customer in Redmine
- link issues to the matching created version
- create delivery notes for customers and convert to pdf
- create Docker image for each customer
- push Docker image on CI registry

### What to do manually

- update customers dev environnement
- create new announcement
- email customers to warn them about the release (with the pdf report)
- update customers file with version number and release date
- update customers issues to "resolved"
