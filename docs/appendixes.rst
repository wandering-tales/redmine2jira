==========
Appendixes
==========

**********************
Jira REST API Handbook
**********************

Here follows a list of Jira REST API's that you might find useful
while working with the ``redmine2jira`` tool. For instance you
may want to retrieve those nasty Jira internal resource ID's used
in the dictionary mappings in the configuration files.

This handbook is organized in sections, each corresponding to a
Jira resource type.

.. note::

   Unless noted otherwise the internal ID field is always ``id``.
   Should ``id`` not be included in the JSON response, the ``key``
   field can be used in its place.

.. note::

   Some API's return paginated list of resources, each specifying a
   maximum number of fetched resources per single call. In such cases
   you may want to call them multiple times properly tweaking the
   ``startAt`` and ``maxResults`` parameters.

   In the URL examples below the ``maxResults`` parameter is set by
   default to the maximum number of results each API is able to return
   per single call.


Users
-----

- Get a user, either active or inactive, by his username::

      /rest/api/2/user?username={username}&includeInactive=True

- Get all users, both active and inactive::

      /rest/api/2/user/search?startAt=0&maxResults=1000&username=_&includeInactive=True'

  This API returns a paginated list of users. The maximum number of returned
  users is limited to 1000 (already set in the URL above).

- Get all users from group, both active and inactive::

      /rest/api/2/group/member?groupname={group_name}&startAt={index}&maxResults=50&includeInactiveUsers=True

  This API returns a paginated list of users. The maximum number of returned
  users is limited to 50 (already set in the URL above).
  This API is useful if you configured a special group containing all of
  your users.

  .. note::

     The value of ``key`` field, for the current version of the Jira REST API
     (v2), is equal to the value of the ``username`` field, hence you may simply
     avoid calling the API's above if you need to retrieve user ID's.


Projects
--------

- Get all projects::

      /rest/api/2/project

- Get project::

      /rest/api/2/project/{projectIdOrKey}


Issue Types
-----------

- Get all issue types::

      /rest/api/2/issuetype


Issue Statuses
--------------

- Get all issue statuses::

      /rest/api/2/status

- Get an issue status::

      /rest/api/2/status/{idOrName}


Issue Priorities
----------------

- Get all issue priorities::

      /rest/api/2/priority


Custom Fields
-------------

- Get all issue fields, both System and Custom::

      /rest/api/2/field


Components
----------

- Get project components::

      /rest/api/2/project/{projectIdOrKey}/components


Labels
------

Unfortunately currently there are no endpoints in Jira REST API v2
to work with labels, and there is no way to workaround.

See https://jira.atlassian.com/browse/JRASERVER-29409
