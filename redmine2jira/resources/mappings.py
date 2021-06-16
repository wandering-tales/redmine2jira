# -*- coding: utf-8 -*-

"""
Definitions of several types of static mappings related to domain entities.
"""

from __future__ import absolute_import

from collections import namedtuple

from redmine2jira.resources import models


ResourceTypeMapping = namedtuple('ResourceTypeMapping', ['redmine', 'jira'])
FieldMapping = namedtuple('FieldMapping', ['redmine', 'jira'])


##########################
# Resource Type Mappings #
##########################

_user_rtp = \
    ResourceTypeMapping(models.RedmineUser,
                        models.JiraUser)
_group_user_rtp = \
    ResourceTypeMapping(models.RedmineGroup,
                        models.JiraUser)
_project_rtp = \
    ResourceTypeMapping(models.RedmineProject,
                        models.JiraProject)
_tracker_issue_type_rtp = \
    ResourceTypeMapping(models.RedmineTracker,
                        models.JiraIssueType)
_issue_status_rtp = \
    ResourceTypeMapping(models.RedmineIssueStatus,
                        models.JiraIssueStatus)
_issue_priority_rtp = \
    ResourceTypeMapping(models.RedmineIssuePriority,
                        models.JiraIssuePriority)
_issue_category_component_rtp = \
    ResourceTypeMapping(models.RedmineIssueCategory,
                        models.JiraProjectComponent)
_issue_category_label_rtp = \
    ResourceTypeMapping(models.RedmineIssueCategory,
                        models.JiraLabel)
_version_rtp = \
    ResourceTypeMapping(models.RedmineVersion,
                        models.JiraVersion)
_custom_field_rtp = \
    ResourceTypeMapping(models.RedmineCustomField,
                        models.JiraCustomField)

_relationship_field_rtp = \
    ResourceTypeMapping(models.RedmineRelationshipField,
                        models.JiraLinkField)


ALL_RESOURCE_TYPE_MAPPINGS = (
    _user_rtp, _group_user_rtp, _project_rtp, _tracker_issue_type_rtp,
    _issue_status_rtp, _issue_priority_rtp, _issue_category_component_rtp,
    _issue_category_label_rtp, _version_rtp, _custom_field_rtp, _relationship_field_rtp
)

RESOURCE_TYPE_MAPPINGS_BY_PROJECT = (
    _issue_category_component_rtp, _issue_category_label_rtp
)


##################
# Field Mappings #
##################

# Redmine and Jira resource type identifying field mappings
#
# NOTE: A Redmine resource type may corresponds
#       to one or more Jira resource types.
#
RESOURCE_TYPE_IDENTIFYING_FIELD_MAPPINGS = {
    _user_rtp:
        FieldMapping(models.RedmineUser.login,
                     models.JiraUser.username),
    _group_user_rtp:
        FieldMapping(models.RedmineGroup.name,
                     models.JiraUser.username),
    _project_rtp:
        FieldMapping(models.RedmineProject.identifier,
                     models.JiraProject.key),
    _tracker_issue_type_rtp:
        FieldMapping(models.RedmineTracker.name,
                     models.JiraIssueType.name),
    _issue_status_rtp:
        FieldMapping(models.RedmineIssueStatus.name,
                     models.JiraIssueStatus.name),
    _issue_priority_rtp:
        FieldMapping(models.RedmineIssuePriority.name,
                     models.JiraIssuePriority.name),
    _issue_category_component_rtp:
        FieldMapping(models.RedmineIssueCategory.name,
                     models.JiraProjectComponent.name),
    _issue_category_label_rtp:
        FieldMapping(models.RedmineIssueCategory.name,
                     models.JiraLabel.name),
    _version_rtp:
        FieldMapping(models.RedmineVersion.name,
                     models.JiraVersion.name),
    _custom_field_rtp:
        FieldMapping(models.RedmineCustomField.name,
                     models.JiraCustomField.name),
    _relationship_field_rtp:
        FieldMapping(models.RedmineRelationshipField.name,
                     models.JiraLinkField.name)
}

# Redmine and Jira issue field definitions mappings
#
# NOTE: A Redmine field may be mapped to one or more Jira fields
#       with respect to several issue related resource type mappings.
#
ISSUE_FIELD_MAPPINGS = {
    (models.RedmineIssue.project, _project_rtp):
        models.JiraIssue.project,
    (models.RedmineIssue.tracker, _tracker_issue_type_rtp):
        models.JiraIssue.issuetype,
    (models.RedmineIssue.status, _issue_status_rtp):
        models.JiraIssue.status,
    (models.RedmineIssue.priority, _issue_priority_rtp):
        models.JiraIssue.priority,
    (models.RedmineIssue.author, _user_rtp):
        models.JiraIssue.creator,
    (models.RedmineIssue.assigned_to, _user_rtp):
        models.JiraIssue.assignee,
    (models.RedmineIssue.assigned_to, _group_user_rtp):
        models.JiraIssue.assignee,
    (models.RedmineIssue.category, _issue_category_component_rtp):
        models.JiraIssue.components,
    (models.RedmineIssue.category, _issue_category_label_rtp):
        models.JiraIssue.labels,
    (models.RedmineIssue.fixed_version, _version_rtp):
        models.JiraIssue.fixedversion,
    models.RedmineIssue.subject: models.JiraIssue.summary,
    models.RedmineIssue.description: models.JiraIssue.description,
    models.RedmineIssue.created_on: models.JiraIssue.created,
    models.RedmineIssue.updated_on: models.JiraIssue.updated,
    models.RedmineIssue.start_date: None,
    models.RedmineIssue.due_date: None,
    models.RedmineIssue.done_ratio: None,
    models.RedmineIssue.estimated_hours: models.JiraIssue.timeoriginalestimate,
    models.RedmineIssue.parent_id: None,
    models.RedmineIssue.is_private: None
}

# Redmine and Jira issue custom field type mappings.
# A single Redmine issue custom field type may correspond
# up to two Jira issue custom field types, respectively
# if they accept single and multiple values.
#
ISSUE_CUSTOM_FIELD_TYPE_MAPPINGS = {
    # Currently Jira does not support boolean custom fields.
    # Here's an open suggestion:
    #
    # https://jira.atlassian.com/browse/JRACLOUD-4689
    #
    # A workaround is to map a Redmine boolean custom fields
    # with a Jira select custom field having Yes/No as options.
    'bool': {'single': 'com.atlassian.jira.plugin.system.'
                       'customfieldtypes:select'},

    'date': {'single': 'com.atlassian.jira.plugin.system.'
                       'customfieldtypes:datepicker'},
    'float': {'single': 'com.atlassian.jira.plugin.system.'
                        'customfieldtypes:float'},
    'int': {'single': 'com.atlassian.jira.plugin.system.'
                      'customfieldtypes:float'},
    'link': {'single': 'com.atlassian.jira.plugin.system.'
                       'customfieldtypes:url'},
    'list': {'single': 'com.atlassian.jira.plugin.system.'
                       'customfieldtypes:select',
             'multiple': 'com.atlassian.jira.plugin.system.'
                         'customfieldtypes:multiselect'},
    'text': {'single': 'com.atlassian.jira.plugin.system.'
                       'customfieldtypes:textarea'},
    'string': {'single': 'com.atlassian.jira.plugin.system.'
                         'customfieldtypes:textfield'},
    'user': {'single': 'com.atlassian.jira.plugin.system.'
                       'customfieldtypes:userpicker',
             'multiple': 'com.atlassian.jira.plugin.system.'
                         'customfieldtypes:multiuserpicker'},
    'version': {'single': 'com.atlassian.jira.plugin.system.'
                          'customfieldtypes:version',
                'multiple': 'com.atlassian.jira.plugin.system.'
                            'customfieldtypes:multiversion'}
}
