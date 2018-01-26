=======
History
=======

0.4.0 (2018-01-26)
------------------

New features
************

* Added dynamic project mappings management

Improvements
************

* Refactored specific methods to save issue resources
* Minor optimizations


0.3.1 (2018-01-26)
------------------

Improvements
************

* Referenced users and groups are collected on-the-fly while exporting issues. This increases performance.
* Minor enhancements in the console output for the completion of the export

Fixes
*****

* Fix recursive function used in ``list projects`` command to build the full project hierarchical name
* Fixed a bug affecting all the ``list`` commands that caused some resource relations being included in the tables
* Fixed another minor bug affecting all the ``list`` commands


0.3.0 (2018-01-22)
------------------

Improvements
************

* Added early lookup of users and groups references within the issues being exported
* Added command to list Redmine groups
* Added option to list all Redmine users at once, including locked ones
* Enhanced notes in configuration file

Changes
*******

* Added requirements.txt for installation package requirements (useful for pyup.io)


0.2.0 (2018-01-19)
------------------

Improvements
************

* Added PyCharm IDE configuration and Python Virtual Environments to .gitignore
* Added configuration file with defaults and support for local configuration file
* Minor documentation fixes

Changes
*******

* Dropped out "Redmine XLS Plugin" in favor of Redmine REST API.

  Since the files exported by the plugin lack some information needed to produce files compatible with the Jira Importer Plugin (JIM),
  several calls to the Redmine REST API were needed to compensate the data. Hence to avoid the effort to merge the data coming from
  two difference sources I decided to rely solely on Redmine REST API to fetch all the needed data.

  This is a major project scope change that implied, in turn, the following modifications:

  - Renamed GitHub repository from "redmine-xls-export2jira" to "redmine2jira"
  - Renamed Python package from "redmine_xls_export2jira" to "redmine2jira"
  - Rename project description to "Redmine to JIRA Importers plugin"

  Any other reference to the "Redmine XLS Export" plugin has also been removed from the documentation.

* Removed Python 2.7 compatibility. Added Python 3.6 compatibility.
* Temporarily disable CLI tests


0.1.1 (2018-01-05)
------------------

Fixes
*****

* Minor fixes in docs

Improvements
************

* Initial pyup.io update
* Added pyup.io Python 3 badge

Changes
*******

* Linked pyup.io
* Removed CHANGELOG.rst


0.1.0 (2018-01-05)
------------------

* First release on PyPI.
