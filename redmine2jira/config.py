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

# Jira has a limit of 10Mb for import files, so you may need to export and
# immport in groups, especially if using a file that contains pretty printed
# JSON
# command line filtering examples
#   redmine2jira export --filter='status_id=*&sort=id'  -v /tmp/all_issues_debug.json
#   redmine2jira export --filter='status_id=*&sort=id&offset=1000&limit=5' -p -v /tmp/all_issues_debug.json
#   redmine2jira export --filter='status_id=*&sort=id&offset=1000&limit=5' -p -v /tmp/all_issues_debug.json
#

# As well as this file review the following methods in issues.py to fix issues with invalid textile
#    site_specific_journal_fixups
#    site_specific_description_fixups
#

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

# Flag to include journals in the issues export.
# As the export of the journals of an issue is a complex feature
# and comes with several requirements on configuration settings,
# it needs to be explicitly enabled by the final user.
#
EXPORT_ISSUE_JOURNALS = False


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

# These settings are declared as Python dictionaries where the keys are the
# "identifying names" of the instances of the related Redmine resource types,
# and the values may be one of:
#
# - "Identifying names" of the mapped Jira resource instances
# - Tuples composed by:
#   - Internal ID of the mapped Jira resource instance
#   - "Identifying name" of the mapped Jira resource instance
#
# The second form, more complex, that contains Jira resources internal ID's,
# is necessary only if issue journals need to be included in the export,
# as that feature needs those ID's to properly generate Jira history items.
# The most effective (and official) method to retrieve Jira resources
# internal ID's is via Jira REST API. Nonetheless, calling those API's may
# not be feasible for everyone, for several reasons. So we added a short
# handbook in the tool documentation with a list of useful API's to
# retrieve those ID's:
#
# https://redmine2jira.readthedocs.io/en/latest/appendixes.html#jira-rest-api-handbook
#
# For both forms, instead, by "identifying names" we mean strings that
# "uniquely" identify each instance of a specific resource type, in addition
# to its internal ID number.
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
#        'My Redmine instance name': (10, 'My Jira instance name'),
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
# Relationship.Name ==> Link.name
#
#
REDMINE_RELATIONSHIP_FIELD_JIRA_LINK_FIELD_MAPPINGS = {

    'blocks': 'blocks',
    'copied from': 'cloners',
    'copied to': 'cloners',
    'copied_to': 'cloners',
    'duplicates': 'duplicates',
    'duplicated by': 'duplicates',
    'precedes': 'precedes',
    'related to': 'relates',
    'relates': 'relates'
# precedes - Links issues to define an "order", where A needs to be
# completed x days before B can be started on
# If B follows A, you can't give B
# a starting date equal or less
# than the ending date of A.
# follows - Reciprocal of precedes.
# If issue B follows A (ex A ends the 21/04 and B begins the 22/04)
# and you add +2 day at the ending date of A,
# the starting and ending dates of B will be +2 too.
# copied to - Reciprocal of copied from.
}

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
    #    'ozzy.osbourne: 'ronny.james.dio',  # 1st form
    #    ...
    #    'alice.cooper': ('dave.grohl', 'dave.grohl'),  # 2nd form
    #    ...
    'admin': 'admin',
    'andrewy': 'andrewy',
    'brucef': 'brucef',
    'chrisw': 'chrisw',
    'Craig': 'craigr',
    'clintone': 'clintone',
    'davek': 'davek',
    'davidb': 'davidb',
    'dylan': 'dylan',
    'edisonh': 'edisonh',
    'graemef': 'graemef',
    'jimw': 'jimw',
    'mafdyb': 'mafdyb',
    'MafdyB': 'mafdyB',
    'markk': 'markk',
    'ravic': 'ravic',
    'redbug': 'redbug',
    'nathanm': 'nathanm',
    'Nathanm': 'nathanm',
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
    #    'qa-leads': 'johann.sebastian.bach',  # 1st form
    #    ...
    #    'lead-developers': ('linus.torvalds', 'linus.torvalds'),  # 2nd form
    #    ...
    'developers': 'markk',
    'Support Staff': 'andrewy',
    'Support-Staff': 'andrewy',
}

#
# Project.Identifier ==> Project.Key
#
REDMINE_PROJECT_JIRA_PROJECT_MAPPINGS = {
    #
    # Example:
    #
    #    'my-very-cool-project': 'MVCP',  # 1st form
    #    ...
    #    'my-cool-project': (123, 'MCP'),  # 2nd form
    #    ...
    # Map redmine project to Jira project key
    'administration': 'AD',
    'autonesting-improvements': 'AUTONESTIM',
    'database-improvement': 'DB',
    'fabtech2011': 'PC',
    'kmc': 'KMC',
    'kmcapp': 'KMCAP',
    'kmcweb': 'KMCWEB',
    'machine-integration-primecutne': 'MACINTEGRA',
    'machines': 'TC',
    'oldissues': 'OI',
    'osk': 'OSK',
    'pc-plate-dragger': 'PCPLAT',
    'primecut': 'PC',
    'primecut3': 'PC3',
    'primecutne-doc': 'PC',
    'primecut-pipe-support': 'PCP',
    'primeshape': 'PS',
    'pug-part-unloader': 'PUGUNLOAD',
    'software-department': 'SW',
    'solid-import': 'IMPORTSLID',
    'support': 'SUP',
    'tc7': 'TC7',
    'tc6': 'TC6',
    'tc-plate-dragger': 'TCPLATE',
    'TouchCut <-> PrimecutNE': 'MACINTEGRA',
    'touchcut': 'TC',
    'touchmill': 'TM',
    'towerp': 'PCTOWER',
    'tubenc': 'TNC'
}

#
# Tracker.Name ==> Issue_Type.Name
#
REDMINE_TRACKER_JIRA_ISSUE_TYPE_MAPPINGS = {
    #
    # Example:
    #
    #    'Nonconformity': 'Incident',  # 1st form
    #    ...
    #    'Defect': (8, 'Bug'),  # 2nd form
    #    ...
    'Administration': 'Administration',
    'Bug': 'Bug',
    'Documentation': 'Documentation',
    'Feature': 'New Feature',
    'Idea': 'Idea',
    'Open': 'Open',
    'PostProcessor Development': 'PostProcessor Development',
    'Report Development': 'Report Development',
    'Support': 'Support',

}

#
# Issue_Status.Name ==> Issue_Status.Name
#
REDMINE_ISSUE_STATUS_JIRA_ISSUE_STATUS_MAPPINGS = {
    #
    # Example:
    #
    #    'Closed': 'Done',  # 1st form
    #    ...
    #    'Open': (19, 'To Do'),  # 2nd form
    #    ...
    'Accepted': 'Accepted',
    'Closed': 'Closed',
    'In Progress': 'In Progress',
    'New': 'Open',
    'Rejected': 'Rejected',
    'Unreproducible': 'Rejected'
}

#
# Issue_Priority.Name ==> Issue_Priority.Name
#
REDMINE_ISSUE_PRIORITY_JIRA_ISSUE_PRIORITY_MAPPINGS = {
    #
    # Example:
    #
    #    'Low': 'Lowest',  # 1st form
    #    ...
    #    'High': (9, 'Highest'),  # 2nd form
    #    ...
    'High': 'High',
    'Immediate': 'Highest',
    'Low': 'Low',
    'Normal': 'Normal',
    'Urgent': 'High'
}

#
# Custom_Field.Name ==> Custom_Field.Name
#
REDMINE_CUSTOM_FIELD_JIRA_CUSTOM_FIELD_MAPPINGS = {
    #
    # Example:
    #
    #    'Approval Team': 'Approvers',  # 1st form
    #    ...
    #    'Severity': (16, 'Severity'),  # 2nd form
    #    ...
    'Bug Reported Count': 'Bug Reported Count',
    'Bug Type / Address / Build': 'Bug Type / Address / Build',
    'Customer': 'Customer',
    'Fixed Version': 'Fixed Version',
    'Custom Fixed Version': 'Fixed Version'
}


#
# Project.Issue_Category.Name ==> Project.Component.Name
#
REDMINE_ISSUE_CATEGORY_JIRA_COMPONENT_MAPPINGS = {
    #
    # Example:
    #
    #    'my-cool-project': {
    #        'Frontend': 'Frontend',  # 1st form
    #        ...
    #        'Backend': (5, 'Backend'),  # 2nd form
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
    #        'A category': 'A label',  # 1st form
    #        ...
    #        'Another category': (13, 'Another label'),  # 2nd form
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
    #        '1.0.0': '1.0.0',  # 1st form
    #        ...
    #        '0.0.1': (1, '0.0.1'),  # 2nd form
    #        ...
    #    }
    #    ...
    'machine-integration-primecutne': {
        '6': '6',
        '7': '7',
        'DB28': 'DB28'},
    'tc-plate-dragger': {
        '6': '6',
        '7': '7'},
    'touchcut': {
        '6': '6',
        '7': '7'},
    'pug-part-unloader': {
        '7': '7'
    },
    'PUG Part Unloader': {
        '7': '7'
    },
    'pug part unloader': {
        '7': '7'
    },
    'tc': {
        '7': '7'
    },
    'tm': {
        '7': '7'
    },
    'tc6': {
        '6': '6'
    },
    'tc7': {
        '6': '6',
        '7': '7'
    },
    'towerp': {
        'PrimeTower3': 'PrimeTower3'
    },
    'primecut': {
        '7': 'Primecut NE Release 007',
        'DB28': 'DB28',
        'NE': 'Primecut NE Release 000',
        'NE Release 1': 'Primecut NE Release 001',
        'NE Release 2': 'Primecut NE Release 002',
        'NE Release 3': 'Primecut NE Release 003',
        'NE Release 4': 'Primecut NE Release 004',
        'NE Release 5': 'Primecut NE Release 005',
        'NE Release 6': 'Primecut NE Release 006',
        'NE Release 7': 'Primecut NE Release 007',
        'NE Release 8': 'Primecut NE Release 008',
        'NE Release 9': 'Primecut NE Release 009',
        'NE Release 10': 'Primecut NE Release 010',
        'NE Release 11': 'Primecut NE Release 011',
        'NE Release 12': 'Primecut NE Release 012',
        'NE Release 13': 'Primecut NE Release 013',
        'NE Release 14': 'Primecut NE Release 014',
        'NE Release 15': 'Primecut NE Release 015',
        'NE Release 16': 'Primecut NE Release 016',
        'NE Release 17': 'Primecut NE Release 017',
        'NE Release 18': 'Primecut NE Release 018',
        'NE Release 19': 'Primecut NE Release 019',
        'NE Release 20': 'Primecut NE Release 020',
        'NE Release 21': 'Primecut NE Release 021',
        'NE Release 22': 'Primecut NE Release 022',
        'NE Release 23': 'Primecut NE Release 023',
        'NE Release 24': 'Primecut NE Release 024',
        'NE Release 25': 'Primecut NE Release 025',
        'NE Release 26': 'Primecut NE Release 026',
        'NE Release 27': 'Primecut NE Release 027',
        'NE Release 28': 'Primecut NE Release 028',
        'NE Release 29': 'Primecut NE Release 029',
        'NE Release 30': 'Primecut NE Release 030',
        'NE Release 31': 'Primecut NE Release 031',
        'NE Release 32': 'Primecut NE Release 032',
        'NE Release 33': 'Primecut NE Release 033',
        'NE Release 34': 'Primecut NE Release 034',
        'NE Release 35': 'Primecut NE Release 035',
        'NE Release 36': 'Primecut NE Release 036',
        'NE Release 37': 'Primecut NE Release 037',
        'NE Release 38': 'Primecut NE Release 038',
        'NE Release 39': 'Primecut NE Release 039',
        'NE Release 40': 'Primecut NE Release 040',
        'NE Release 41': 'Primecut NE Release 041',
        'NE Release 42': 'Primecut NE Release 042',
        'NE Release 43': 'Primecut NE Release 043',
        'NE Release 44': 'Primecut NE Release 044',
        'NE Release 45': 'Primecut NE Release 045',
        'NE Release 46': 'Primecut NE Release 046',
        'NE Release 47': 'Primecut NE Release 047',
        'NE Release 48': 'Primecut NE Release 048',
        'NE Release 49': 'Primecut NE Release 049',
        'NE Release 50': 'Primecut NE Release 050',
        'NE Release 51': 'Primecut NE Release 051',
        'NE Release 52': 'Primecut NE Release 052',
        'NE Release 53': 'Primecut NE Release 053',
        'NE Release 54': 'Primecut NE Release 054',
        'NE Release 55': 'Primecut NE Release 055',
        'NE Release 56': 'Primecut NE Release 056',
        'NE Release 57': 'Primecut NE Release 057',
        'NE Release 58': 'Primecut NE Release 058',
        'NE Release 59': 'Primecut NE Release 059',
        'NE Release 60': 'Primecut NE Release 060',
        'NE Release 61': 'Primecut NE Release 061',
        'NE Release 62': 'Primecut NE Release 062',
        'NE Release 63': 'Primecut NE Release 063',
        'NE Release 64': 'Primecut NE Release 064',
        'NE Release 65': 'Primecut NE Release 065',
        'NE Release 66': 'Primecut NE Release 066',
        'NE Release 67': 'Primecut NE Release 067',
        'NE Release 68': 'Primecut NE Release 068',
        'NE Release 69': 'Primecut NE Release 069',
        'NE Release 70': 'Primecut NE Release 070',
        'NE Release 71': 'Primecut NE Release 071',
        'NE Release 72': 'Primecut NE Release 072',
        'NE Release 73': 'Primecut NE Release 073',
        'NE Release 74': 'Primecut NE Release 074',
        'NE Release 75': 'Primecut NE Release 075',
        'NE Release 76': 'Primecut NE Release 076',
        'NE Release 77': 'Primecut NE Release 077',
        'NE Release 78': 'Primecut NE Release 078',
        'NE Release 79': 'Primecut NE Release 079',
        'NE Release 80': 'Primecut NE Release 080',
        'Release 81':    'Primecut NE Release 081',
        'NE Release 81': 'Primecut NE Release 081',
        'NE Release 82': 'Primecut NE Release 082',
        'NE Release 83': 'Primecut NE Release 083',
        'NE Release 84': 'Primecut NE Release 084',
        'NE Release 85': 'Primecut NE Release 085',
        'NE Release 86': 'Primecut NE Release 086',
        'NE Release 87': 'Primecut NE Release 087',
        'NE Release 88': 'Primecut NE Release 088',
        'NE Release 89': 'Primecut NE Release 089',
        'NE Release 90': 'Primecut NE Release 090',
        'NE Release 91': 'Primecut NE Release 091',
        'NE Release 92': 'Primecut NE Release 092',
        'NE Release 93': 'Primecut NE Release 093',
        'NE Release 94': 'Primecut NE Release 094',
        'NE Release 95': 'Primecut NE Release 095',
        'NE Release 96': 'Primecut NE Release 096',
        'NE Release 97': 'Primecut NE Release 097',
        'NE Release 98': 'Primecut NE Release 098',
        'NE Release 99': 'Primecut NE Release 099',
        'NE Release 100': 'Primecut NE Release 100',
        'NE Release 101': 'Primecut NE Release 101',
        'NE Release 102': 'Primecut NE Release 102',
        'NE Release 103': 'Primecut NE Release 103',
        'NE Release 104': 'Primecut NE Release 104',
        'NE Release 105': 'Primecut NE Release 105',
        'NE Release 106': 'Primecut NE Release 106',
        'NE Release 107': 'Primecut NE Release 107',
        'NE Release 108': 'Primecut NE Release 108',
        'NE Release 109': 'Primecut NE Release 109',
        'NE Release 110': 'Primecut NE Release 110',
        'NE Release 111': 'Primecut NE Release 111',
        'NE Release 112': 'Primecut NE Release 112',
        'NE Release 113': 'Primecut NE Release 113',
        'NE Release 114': 'Primecut NE Release 114',
        'NE Release 115': 'Primecut NE Release 115',
        'NE Release 116': 'Primecut NE Release 116',
        'NE Release 117': 'Primecut NE Release 117',
        'NE Release 118': 'Primecut NE Release 118',
        'NE Release 119': 'Primecut NE Release 119',
        'NE Release 120': 'Primecut NE Release 120',
        'NE Release 121': 'Primecut NE Release 121',
        'NE Release 122': 'Primecut NE Release 122',
        'NE Release 123': 'Primecut NE Release 123',
        'NE Release 124': 'Primecut NE Release 124',
        'NE Release 125': 'Primecut NE Release 125',
        'NE Release 126': 'Primecut NE Release 126',
        'NE Release 127': 'Primecut NE Release 127',
        'NE Release 128': 'Primecut NE Release 128',
        'NE Release 129': 'Primecut NE Release 129',
        'NE Release 130': 'Primecut NE Release 130',
        'NE Release 131': 'Primecut NE Release 131',
        'NE Release 132': 'Primecut NE Release 132',
        'NE Release 133': 'Primecut NE Release 133',
        'NE Release 134': 'Primecut NE Release 134',
        'NE Release 135': 'Primecut NE Release 135',
        'NE Release 136': 'Primecut NE Release 136',
        'NE Release 137': 'Primecut NE Release 137',
        'NE Release 138': 'Primecut NE Release 138',
        'NE Release 139': 'Primecut NE Release 139',
        'NE Release 140': 'Primecut NE Release 140',
        'NE Release 141': 'Primecut NE Release 141',
        'NE Release 142': 'Primecut NE Release 142',
        'NE Release 143': 'Primecut NE Release 143',
        'NE Release 144': 'Primecut NE Release 144',
        'NE Release 145': 'Primecut NE Release 145',
        'NE Release 146': 'Primecut NE Release 146',
        'NE Release 147': 'Primecut NE Release 147',
        'NE Release 148': 'Primecut NE Release 148',
        'NE Release 149': 'Primecut NE Release 149',
        'NE Release 150': 'Primecut NE Release 150'
    }
}

###########
# Redmine #
###########

#
# General configuration
#

REDMINE_USE_HTTPS = False
# REDMINE_HOST = 'goofy:3001'
# next line is mark's test vm
REDMINE_HOST = '172.25.0.98/redmine'
# REDMINE_API_KEY = '<put-administrator-user-redmine-api-key>'
REDMINE_API_KEY = '276e78f06bc8297708f3d12c64d9d5c2bbc75c56'

# Markup language used for text fields.
#
# Choose one among:
# - none     (No formatting used)
# - textile  (Textile markup language)
# - markdown (Markdown markup language)
#
# REDMINE_TEXT_FORMATTING = 'none'
REDMINE_TEXT_FORMATTING = 'textile'

#
# Issue tracking configuration
#

ALLOW_CROSS_PROJECT_ISSUE_RELATIONS = True

# The value of this setting in Redmine comes from a selection list.
# Here the list values are collapsed to a boolean
# using the following criterion:
#
# - "disabled"   -> False
# - Other values -> True
#
ALLOW_CROSS_PROJECT_SUBTASKS = False

# ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS = False
ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS = True


# Overrides default settings with user defined ones, if any...
try:
    from redmine2jira.config_local import *  # noqa
except ImportError:
    pass


# Compose Redmine URL...
REDMINE_URL = ('{protocol}://{host}'
               .format(protocol=('https' if REDMINE_USE_HTTPS else 'http'),
                       host=REDMINE_HOST))
