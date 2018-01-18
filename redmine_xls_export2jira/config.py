# -*- coding: utf-8 -*-

from __future__ import absolute_import


##########################################################################
#
# Redmine XLS Export plugin to JIRA Importers plugin
#
# Copyright (C) 2018, Michele Cardone
#
# config.py - Core application configuration settings
#
##########################################################################

########
# Core #
########

CHECK_ISSUE_ID_FILTER_AVAILABILITY = True
ISSUE_ID_FILTER_AVAILABLE = True


###########
# Redmine #
###########

REDMINE_USE_HTTPS = True
REDMINE_HOST = 'redmine.example.com'
REDMINE_API_KEY = '<put-administrator-user-redmine-api-key>'

#
# Issue tracking configuration
#

ALLOW_CROSS_PROJECT_ISSUE_RELATIONS = False

# The value of this setting in Redmine comes from a selection list.
# Here the list values are collapsed to a boolean
# using the following criterion:
# - "disabled"   -> False
# - Other values -> True
ALLOW_CROSS_PROJECT_SUBTASKS = False

ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS = False


#############################
# Redmine XLS Export plugin #
#############################

#
# Export settings
#

# Date format options
#
# WARNING: The format of the following masks is specific of the plugin,
#          but is not documented anywhere.
#          Further, it's kind of ambiguous as "months" and "minutes"
#          use the same "mm" (lowercase) placeholder.
#          We warmly suggest to keep their defaults untouched
#          in the plugin settings and, in turn,
#          avoid overriding the following settings.
#
REDMINE_XLS_PLUGIN_ISSUE_CREATED_DATE_FORMAT = 'dd.mm.yyyy hh:mm:ss'
REDMINE_XLS_PLUGIN_ISSUE_UPDATED_DATE_FORMAT = 'dd.mm.yyyy hh:mm:ss'
REDMINE_XLS_PLUGIN_ISSUE_START_DATE_FORMAT = 'dd.mm.yyyy'
REDMINE_XLS_PLUGIN_ISSUE_DUE_DATE_FORMAT = 'dd.mm.yyyy'

#
# Export file system context
#

EXPORT_JOURNALS_ROOT_DIR = 'journals'
EXPORT_JOURNALS_FILENAME_MASK = '{:05d}_journal_details.xls'
EXPORT_ATTACHMENTS_ROOT_DIR = 'attachments'
EXPORT_ATTACHMENTS_ISSUE_DIRNAME_MASK = '{:05d}'
EXPORT_STATUS_HISTORIES_FILENAME = 'status_histories.xls'


#
# Export main MS Excel file settings
#

# Column names corresponding to Redmine standard fields.
# The column names for the custom fields, instead,
# inherit the same internal name of the respective custom field.
# In turn, the custom fields will be dynamically retrieved
# via the Redmine REST API.
EXPORT_MAIN_XLS_STANDARD_FIELDS_COLUMN_NAMES = (
    '#',
    'Project',
    'Tracker',
    'Parent task',
    'Status',
    'Priority',
    'Subject',
    'Author',
    'Assignee',
    'Updated',
    'Category',
    'Target version',
    'Start date',
    'Due date',
    'Estimated time',
    'Spent time',
    '% Done',
    'Created',
    'Closed',
    'Description',
)

EXPORT_MAIN_XLS_RELATIONS_COLUMN_NAME = 'Related issues'
EXPORT_MAIN_XLS_WATCHERS_COLUMN_NAME = 'Watcher'
EXPORT_MAIN_XLS_JOURNALS_COLUMN_NAME = 'Journal'
EXPORT_MAIN_XLS_ATTACHMENTS_COLUMN_NAME = 'Attachments'


# Overrides default settings with user defined ones, if any...
try:
    from redmine_xls_export2jira.config_local import *  # noqa
except ImportError:
    pass


# Compose Redmine URL...
REDMINE_URL = ('{protocol}://{host}'
               .format(protocol=('https' if REDMINE_USE_HTTPS else 'http'),
                       host=REDMINE_HOST))
