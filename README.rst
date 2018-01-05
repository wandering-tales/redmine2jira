==================================================
Redmine XLS Export plugin to JIRA Importers plugin
==================================================


.. image:: https://img.shields.io/pypi/v/redmine_xls_export2jira.svg
        :target: https://pypi.python.org/pypi/redmine_xls_export2jira

.. image:: https://img.shields.io/travis/wandering-tales/redmine-xls-export2jira.svg
        :target: https://travis-ci.org/wandering-tales/redmine-xls-export2jira

.. image:: https://readthedocs.org/projects/redmine-xls-export2jira/badge/?version=latest
        :target: https://redmine-xls-export2jira.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/wandering-tales/redmine-xls-export2jira/shield.svg
     :target: https://pyup.io/repos/github/wandering-tales/redmine-xls-export2jira/
     :alt: Updates


Convert and merge XLS exports of the "Redmine XLS Export" plugin to files compatible with the JIRA Importers plugin (JIM).


* Free software: MIT license
* Documentation: https://redmine-xls-export2jira.readthedocs.io.


Features
--------

The aim of the tool is to convert and merge all the Redmine exports
obtained using the `Redmine XLS Export plugin`_
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

Time logs
*********

The only information `Redmine XLS Export plugin`_ is not able to include
in its exports are the issues time logs, which need to be exported separately,
for the same issue subset, using the related export feature already included
in Redmine. The tool may be then instructed to integrate such time logs
in the final JSON file.

JIM file format specifications
******************************

Both the JSON and CSV files produced respectively meet their format specifications
for the JIRA Importers plugin (JIM). Those specifications can be respectively found
in the following KB articles.

* Jira Cloud
  - `JSON <https://confluence.atlassian.com/display/AdminJIRACloud/Importing+data+from+JSON>`_
  - `CSV <https://confluence.atlassian.com/display/AdminJIRACloud/Importing+data+from+CSV>`_

* Jira Server (latest release)
  - `JSON <https://confluence.atlassian.com/display/ADMINJIRASERVER/Importing+data+from+JSON>`_
  - `CSV <https://confluence.atlassian.com/display/ADMINJIRASERVER/Importing+data+from+CSV>`_

However, it's worth to mention that all the articles, especially the one Related
to JSON format, are more driven by examples rather than being comprehensive
specification documents: several details related both to the structure
and the fields values format are omitted. Sometimes we had the need to rely
on other sources on the Internet to cope some strange scenarios.
Besides, the import from JSON feature is not completely stable.


Prerequisites
-------------

The tool is compatible with the version `0.2.1.t10` of the `Redmine XLS Export plugin`_,
which version, at the time of writing, is the latest one.


Usage
-----

* TODO



Configuration
-------------

* TODO


.. _Redmine XLS Export plugin: https://github.com/two-pack/redmine_xls_export


Versioning
----------

We use `SemVer <http://semver.org/>`_ for versioning.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
