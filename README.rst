==================================================
Redmine to JIRA Importers plugin
==================================================


.. image:: https://img.shields.io/pypi/v/redmine2jira.svg
        :target: https://pypi.python.org/pypi/redmine2jira

.. image:: https://travis-ci.org/wandering-tales/redmine2jira.svg?branch=master
        :target: https://travis-ci.org/wandering-tales/redmine2jira

.. image:: https://readthedocs.org/projects/redmine2jira/badge/?version=latest
        :target: https://redmine2jira.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/wandering-tales/redmine2jira/shield.svg
     :target: https://pyup.io/repos/github/wandering-tales/redmine2jira/
     :alt: Updates

.. image:: https://pyup.io/repos/github/wandering-tales/redmine2jira/python-3-shield.svg
     :target: https://pyup.io/repos/github/wandering-tales/redmine2jira/
     :alt: Python 3

Export Redmine issues to file formats compatible with the JIRA Importers plugin (JIM).

* Free software: MIT license
* Documentation: https://redmine2jira.readthedocs.io.


Features
--------

The aim of the tool is to export Redmine issues, fetched using Redmine REST API,
to a set of files which format is compatible with the JIRA Importers Plugin.

The output of the tool, in most of the scenarios, is a single JSON file
combining all the following information for each exported issue:

- Standard/custom fields
- Journal entries (Notes)
- Status history
- Attachments URLs
- Hierarchy relationships
- Relations
- Watchers
- Time logs

Cross-project issue relations
*****************************

If the Redmine instance has configured cross-project issue relations,
and the exported issues do not correspond to the full set of issues of the
Redmine instance (the tool will properly detect the scenario and prompt a
question if needed), the issue relations will be exported in a separate
CSV file. Subsequently, when all the Redmine issues have been imported
in the target Jira instance that CSV file can be finally imported
in order to update relations on all the existing issues.

JIM file format specifications
******************************

Both the JSON and CSV files produced respectively meet their format specifications
for the JIRA Importers plugin (JIM). Those specifications can be respectively found
in the following KB articles:

- `Cloud / Importing data from JSON <https://confluence.atlassian.com/display/AdminJIRACloud/Importing+data+from+JSON>`_
- `Cloud / Importing data from CSV <https://confluence.atlassian.com/display/AdminJIRACloud/Importing+data+from+CSV>`_
- `Server (latest) / Importing data from JSON <https://confluence.atlassian.com/display/ADMINJIRASERVER/Importing+data+from+JSON>`_
- `Server (latest) / Importing data from CSV <https://confluence.atlassian.com/display/ADMINJIRASERVER/Importing+data+from+CSV>`_

However, it's worth to mention that all the articles, especially the one Related
to JSON format, are more driven by examples rather than being comprehensive
specification documents: several details related both to the structure
and the fields values format are omitted. Sometimes we had the need to rely
on other sources on the Internet to cope some strange scenarios.
Besides, the import from JSON feature is not completely stable.


Prerequisites
-------------

* TODO Users already present in Jira
* TODO Redmine REST API Enabled


Usage
-----

The '--filter' option accept a HTTP GET parameter string.
Here follows the list of the supported filter parameters:

  - issue_id (int or string): Single issue ID or comma-separated issue ID's
  - project_id (int or string): Project ID/identifier
  - subproject_id (int or string): Subproject ID/identifier
    (To be used in conjunction with 'project_id';
     you can use `project_id=X` and `subproject_id=!*`
     to get only the issues of a given project
     and none of its subprojects)
  - tracker_id (int): Tracker ID
  - query_id (int): Query ID
  - status_id (int): ['open', 'closed', '*', id]
    If the filter is not specified the default value will be 'open'.
  - assigned_to_id (int):_Assignee user ID
    (or 'me' to get issues which are assigned to the user
     whose credentials were used to access the Redmine REST API)
  - cf_x: Custom field having ID 'x'.
    The '~' sign can be used before the value to find issues
    containing a string in a custom field.

NB: operators containing ">", "<" or "=" should be hex-encoded so they're parsed correctly. Most evolved API clients will do that for you by default, but for the sake of clarity the following examples have been written with no such magic feature in mind.

To fetch issues for a date range (uncrypted filter is "><2012-03-01|2012-03-07") :
GET /issues.xml?created_on=%3E%3C2012-03-01|2012-03-07

To fetch issues created after a certain date (uncrypted filter is ">=2012-03-01") :
GET /issues.xml?created_on=%3E%3D2012-03-01

Or before a certain date (uncrypted filter is "<= 2012-03-07") :
GET /issues.xml?created_on=%3C%3D2012-03-07

To fetch issues created after a certain timestamp (uncrypted filter is ">=2014-01-02T08:12:32Z") :
GET /issues.xml?created_on=%3E%3D2014-01-02T08:12:32Z

To fetch issues updated after a certain timestamp (uncrypted filter is ">=2014-01-02T08:12:32Z") :
GET /issues.xml?updated_on=%3E%3D2014-01-02T08:12:32Z


Configuration
-------------

* TODO


Versioning
----------

We use `SemVer <http://semver.org/>`_ for versioning.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

[ ~ Dependencies scanned by PyUp.io ~ ]

