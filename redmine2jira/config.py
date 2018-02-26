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
# However, depending on the Redmine version, it might not be
# available in the Redmine REST API,
# As it's not known which specific version introduced it,
# the tool embeds a mechanism to guess if it's available or not.
# If those details are not known we suggest to leave the
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

#
# Resource mappings
#

# Here follows a bunch of settings related to mappings used during the
# issues export to statically map Redmine resource instances to Jira ones.
#
# Each settings is valid within the context of a specific mapping between
# a Redmine resource type and a Jira one. It's worth to mention that those
# resource type mappings consist in One-to-Many relationships: a Redmine
# resource type may be mapped to one or more Jira resource types.
#
# The naming convention for these settings is the following:
#
# REDMINE_{RESOURCE_TYPE}_JIRA_{RESOURCE_TYPE}_MAPPINGS
#
# where the two "RESOURCE_TYPE" placeholders respectively refers to the
# Redmine and Jira resource types where the mappings of resources apply.

# These settings are declared as Python dictionaries where the keys and the
# values are both "identifying names" of the instances of the two resource
# types involved in the mappings, respectively for Redmine and Jira.
# By "identifying names", in this context, we mean strings that "uniquely"
# identify each instance of a specific resource type, in addition to its
# internal ID number.
# As each resource type, either it belongs to Redmine or Jira, has always
# at least one field designated to contain such identifying name, for each
# one of its instances, we will specify, in a comment before each dictionary
# setting, which of them are involved in the mapping:
#
# Example:
#
#    {redmine_resource_type}.{identifying_field} ==>
#       {jira_resource_type}.{identifying_field}
#
# Furthermore, some of the mappings defined via these settings are valid
# only "on a per-project basis".
# As both Redmine and Jira are project management tools, it's natural to
# state that for both of them the "Project" is one of the main resource types
# around which they are built, likewise any other software tool belonging
# to this category. In turn, there are some resource types which instances
# are defined only within the context of a specific "Project" instance.
# In such cases our dictionary keys become the "identifying names" of
# Redmine projects ("identifier" field), and the values the final mappings
# with respect to the resource type instances:
#
# Example:
#
#    'my-cool-project': {
#        'My Redmine instance name': 'My Jira instance name',
#        ...
#    }
#    ...
#
# As we assume a Redmine project has a One-to-One mapping with a Jira project,
# it would be pointless to specify the latter.
# Therefore, for mappings defined on a per project basis we extend the above
# syntax as follows:
#
#    {redmine_project}.{redmine_resource_type}.{identifying_field} ==>
#       {jira_project}.{jira_resource_type}.{identifying_field}
#
# The configuration of all the following mappings entirely depends on the
# specific use case, hence all the dictionaries hereby defined are empty.
# That's because they are meant to be properly overridden in the
# `config_local.py` file, according to the actual configuration of both
# the Redmine and Jira instances he's dealing with.
#
# In case the tool detect some needed missing mapping at runtime, it will
# prompt to input one, which will be retained for the whole session.
#

#
# User.Login ==> User.Username
#
# NOTE: The concept of "Jira user" is also extended to Jira Service Desk
#       "portal only customers".
#
REDMINE_USER_JIRA_USER_MAPPINGS = {
    #
    # Example:
    #
    #    'alice.cooper': 'dave.grohl',
    #    ...
}

#
# Group.Name ==> User.Username
#
# The only relations between issues and groups is via the "Assignee"
# field, and only if issue assignment to groups is explicitly allowed
# in the Redmine instance settings.
# However, as Jira does not (and will not) support issue assignment to groups
# (https://jira.atlassian.com/browse/JRASERVER-1397) one possible mapping
# is from external system group names to Jira usernames.
# It's worth to check out the section "Managing Issues via a User Account"
# in the following KB article:
#
# https://confluence.atlassian.com/jira/how-do-i-assign-issues-to-multiple-users-207489749.html#HowdoIassignissuestomultipleusers-ManagingIssuesviaaUserAccount
#
# NOTE: The concept of "Jira user" is also extended to Jira Service Desk
#       "portal only customers".
#
REDMINE_GROUP_JIRA_USER_MAPPINGS = {
    #
    # Example:
    #
    #    'lead-developers': 'linus.torvalds',
    #    ...
}

#
# Project.Identifier ==> Project.Key
#
REDMINE_PROJECT_JIRA_PROJECT_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': 'MCP',
    #    ...
}

#
# Tracker.Name ==> Issue_Type.Name
#
REDMINE_TRACKER_JIRA_ISSUE_TYPE_MAPPINGS = {
    #
    # Example:
    #
    #    'Defect': 'Bug',
    #    ...
}

#
# Issue_Status.Name ==> Issue_Status.Name
#
REDMINE_ISSUE_STATUS_JIRA_ISSUE_STATUS_MAPPINGS = {
    #
    # Example:
    #
    #    'Open': 'To Do',
    #    ...
}

#
# Issue_Priority.Name ==> Issue_Priority.Name
#
REDMINE_ISSUE_PRIORITY_JIRA_ISSUE_PRIORITY_MAPPINGS = {
    #
    # Example:
    #
    #    'High': 'Highest',
    #    ...
}

#
# Custom_Field.Name ==> Custom_Field.Name
#
REDMINE_CUSTOM_FIELD_JIRA_CUSTOM_FIELD_MAPPINGS = {
    #
    # Example:
    #
    #    'Severity': 'Severity',
    #    ...
}


#
# Project.Issue_Category.Name ==> Project.Component.Name
#
REDMINE_ISSUE_CATEGORY_JIRA_COMPONENT_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': {
    #        'Backend': 'Backend',
    #        ...
    #    }
    #    ...
}

#
# Project.Issue_Category.Name ==> Project.Label.Name
#
REDMINE_ISSUE_CATEGORY_JIRA_LABEL_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': {
    #        'My Functional Module': 'My Functional Module',
    #        ...
    #    }
    #    ...
}

#
# Project.Version.Name ==> Project.Version.Name
#
REDMINE_VERSION_JIRA_VERSION_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': {
    #        '1.0.0': '1.0.0',
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
