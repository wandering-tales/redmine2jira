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


# Overrides default settings with user defined ones, if any...
try:
    from redmine2jira.config_local import *  # noqa
except ImportError:
    pass


# Compose Redmine URL...
REDMINE_URL = ('{protocol}://{host}'
               .format(protocol=('https' if REDMINE_USE_HTTPS else 'http'),
                       host=REDMINE_HOST))
