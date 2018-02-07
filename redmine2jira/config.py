# -*- coding: utf-8 -*-

from __future__ import absolute_import


##########################################################################
#
# Redmine to JIRA Importers plugin
#
# Copyright (C) 2018, Michele Cardone
#
# config.py - Core application configuration settings
#
##########################################################################

########
# Core #
########

# The export feature of this tool offer a way to filter issues
# via a query string.Among the several filter parameters there's
# one by issue ID(s).
# However, depending on your Redmine version, it might not be
# available in your Redmine REST API,
# As it's not known which specific version introduced it,
# the tool embeds a mechanism to guess if it's available or not.
# If you don't know this detail we suggest to leave the
# CHECK_ISSUE_ID_FILTER_AVAILABILITY setting to its default value:
# every time the 'issue_id' filter is used the tool will automatically:
#
# - Verify its availability
# - Prompt the result of the verification
# - Propose to change the ISSUE_ID_FILTER_AVAILABLE setting
#   according to the result
# - Propose to disable CHECK_ISSUE_ID_FILTER_AVAILABILITY
#   to avoid performing the same check again in the future
#
# For instance it may be useful to re-enable CHECK_ISSUE_ID_FILTER_AVAILABILITY
# if the Redmine instance version changed.
#
CHECK_ISSUE_ID_FILTER_AVAILABILITY = True
ISSUE_ID_FILTER_AVAILABLE = True

# Custom Redmine to Jira user mappings used during issue export.
# The mapping is defined via usernames (login names). When no
# mapping is defined for a referenced Redmine user, by default
# the tool will map the Redmine username to the Jira one as it is.
#
# NOTE: The concept of "Jira user" is also extended to Jira Service Desk
#       "portal only customers".
#
CUSTOM_REDMINE_USER_JIRA_USER_MAPPINGS = {
    #
    # Example:
    #
    #    'alice.cooper': 'dave.grohl',
    #    ...
}

# Custom Redmine group to Jira user mappings used during issue export.
# The only relations between issues and groups is via the "Assignee"
# field, and only if issue assignment to groups is explicitly allowed
# in the Redmine instance settings.
# However, as Jira does not (and will not) support issue assignment to groups
# (https://jira.atlassian.com/browse/JRASERVER-1397) one possible mapping
# is from group names to user names. It's worth to check out the section
# "Managing Issues via a User Account" in the following KB article:
#
# https://confluence.atlassian.com/jira/how-do-i-assign-issues-to-multiple-users-207489749.html#HowdoIassignissuestomultipleusers-ManagingIssuesviaaUserAccount
#
# Therefore in such scenario the mapping is defined between Redmine
# group names and Jira usernames. When no mapping is defined for a
# referenced group the tool will prompt the user to input a Jira username.
#
# NOTE: The concept of "Jira user" is also extended to Jira Service Desk
#       "portal only customers".
#
CUSTOM_REDMINE_GROUP_JIRA_USER_MAPPINGS = {
    #
    # Example:
    #
    #    'lead-developers': 'linus.torvalds',
    #    ...
}

# Custom Redmine to Jira project mappings used during issue export.
# The mapping is defined between Redmine project identifiers and
# Jira project keys. When no mapping is defined for a referenced project
# the tool will prompt the user to input a Jira project key.
#
CUSTOM_REDMINE_PROJECT_JIRA_PROJECT_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': 'MCP',
    #    ...
}


# Custom Redmine tracker to Jira issue type mappings used during issue export.
# The mapping is defined between Redmine tracker and Jira issue type names,
# case sensitive. When no mapping is defined for a referenced tracker
# the tool will prompt the user to input a Jira issue type name.
#
CUSTOM_REDMINE_TRACKER_JIRA_ISSUE_TYPE_MAPPINGS = {
    #
    # Example:
    #
    #    'Defect': 'Bug',
    #    ...
}

# Custom Redmine to Jira issue status mappings used during issue export.
# The mapping is defined between Redmine and Jira issue status names,
# case sensitive. When no mapping is defined for a referenced issue status
# the tool will prompt the user to input a Jira issue status name.
#
CUSTOM_REDMINE_ISSUE_STATUS_JIRA_ISSUE_STATUS_MAPPINGS = {
    #
    # Example:
    #
    #    'Open': 'To Do',
    #    ...
}

# Custom Redmine to Jira issue priority mappings used during issue export.
# The mapping is defined between Redmine and Jira issue priority names,
# case sensitive. When no mapping is defined for a referenced issue priority
# the tool will prompt the user to input a Jira issue priority name.
#
CUSTOM_REDMINE_ISSUE_PRIORITY_JIRA_ISSUE_PRIORITY_MAPPINGS = {
    #
    # Example:
    #
    #    'High': 'Highest',
    #    ...
}

# Custom Redmine issue category to Jira component mappings
# used during issue export.
# The mapping is defined between Redmine issue category names
# and Jira component names, case sensitive, on a per-project basis.
# Basically this is a dictionary of projects, using project identifiers
# as keys, and the mappings are nested dictionaries with respect to the
# related project.
# When no mapping is defined for a referenced issue category
# the tool will prompt the user to input a Jira component name.
#
CUSTOM_REDMINE_ISSUE_CATEGORY_JIRA_COMPONENT_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': {
    #        'Backend': 'Backend',
    #        ...
    #    }
    #    ...
}

# Custom Redmine issue category to Jira label mappings
# used during issue export.
# The mapping is defined between Redmine issue category names
# and Jira labels, case sensitive, on a per-project basis.
# Basically this is a dictionary of projects, using project identifiers
# as keys, and the mappings are nested dictionaries with respect to the
# related project.
# When no mapping is defined for a referenced issue category
# the tool will prompt the user to input a Jira label.
#
CUSTOM_REDMINE_ISSUE_CATEGORY_JIRA_LABEL_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': {
    #        'My Functional Module': 'My Functional Module',
    #        ...
    #    }
    #    ...
}


###########
# Redmine #
###########

#
# General configuration
#

REDMINE_USE_HTTPS = True
REDMINE_HOST = 'redmine.example.com'
REDMINE_API_KEY = '<put-administrator-user-redmine-api-key>'

# Markup language used for text fields.
#
# Choose one among:
# - none     (No formatting used)
# - textile  (Textile markup language)
# - markdown (Markdown markup language)
#
REDMINE_TEXT_FORMATTING = 'none'

#
# Issue tracking configuration
#

ALLOW_CROSS_PROJECT_ISSUE_RELATIONS = False

# The value of this setting in Redmine comes from a selection list.
# Here the list values are collapsed to a boolean
# using the following criterion:
#
# - "disabled"   -> False
# - Other values -> True
#
ALLOW_CROSS_PROJECT_SUBTASKS = False

ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS = False


# Overrides default settings with user defined ones, if any...
try:
    from redmine2jira.config_local import *  # noqa
except ImportError:
    pass


# Compose Redmine URL...
REDMINE_URL = ('{protocol}://{host}'
               .format(protocol=('https' if REDMINE_USE_HTTPS else 'http'),
                       host=REDMINE_HOST))
