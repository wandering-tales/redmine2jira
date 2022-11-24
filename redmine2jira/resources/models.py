# -*- coding: utf-8 -*-

"""Definitions of internal domain entities models."""

from abc import ABCMeta
from collections import namedtuple


ResourceKey = namedtuple('ResourceKey', ['id', 'key'])
FakeResourceInstance = namedtuple('FakeResourceInstance',
                                  ['id', 'name', 'value'])


class Field(object):
    def __init__(self, key, name, identifying=False, related_resource=None):
        self.key = key
        self.name = name
        self.identifying = identifying
        self.related_resource = related_resource
        self.is_relation = False if related_resource is None else True


class ResourceType(object):
    __metaclass__ = ABCMeta

    @classmethod
    def get_related_fields(cls):
        return (field for field in cls.__dict__
                if isinstance(getattr(cls, field), Field) and
                getattr(cls, field).is_relation)

    @classmethod
    def get_identifying_field(cls):
        return next((field for field in cls.__dict__
                     if isinstance(getattr(cls, field), Field) and
                     getattr(cls, field).identifying), None)


# Redmine resource types

class RedmineUser(ResourceType):
    login = Field('login', 'Login', identifying=True)


class RedmineGroup(ResourceType):
    name = Field('name', 'Name', identifying=True)


class RedmineProject(ResourceType):
    identifier = Field('identifier', 'Identifier', identifying=True)


class RedmineTracker(ResourceType):
    name = Field('name', 'Name', identifying=True)


class RedmineIssueStatus(ResourceType):
    name = Field('name', 'Name', identifying=True)


class RedmineIssuePriority(ResourceType):
    name = Field('name', 'Name', identifying=True)


class RedmineIssueCategory(ResourceType):
    name = Field('name', 'Name', identifying=True)


class RedmineCustomField(ResourceType):
    name = Field('name', 'Name', identifying=True)


class RedmineVersion(ResourceType):
    name = Field('name', 'Name', identifying=True)


class RedmineIssue(ResourceType):
    project = Field('project', 'Project',
                    related_resource=RedmineProject)
    tracker = Field('tracker', 'Tracker',
                    related_resource=RedmineTracker)
    status = Field('status', 'Status',
                   related_resource=RedmineIssueStatus)
    priority = Field('priority', 'Priority',
                     related_resource=RedmineIssuePriority)
    author = Field('author', 'Author',
                   related_resource=RedmineUser)
    assigned_to = Field('assigned_to', 'Assignee',
                        related_resource=RedmineUser)
    category = Field('category', 'Category',
                     related_resource=RedmineIssueCategory)
    fixed_version = Field('fixed_version', 'Target version',
                          related_resource=RedmineVersion)
    subject = Field('subject', 'Subject')
    description = Field('description', 'Description')
    created_on = Field('created_on', 'Created on')
    updated_on = Field('updated_on', 'Updated on')
    start_date = Field('start_date', 'Start date')
    due_date = Field('due_date', 'Due date')
    done_ratio = Field('done_ratio', 'Done %')
    estimated_hours = Field('estimated_hours', 'Estimated time')
    is_private = Field('is_private', 'Private')


# Jira resource types

class JiraUser(ResourceType):
    username = Field('username', 'Username', identifying=True)


class JiraProject(ResourceType):
    key = Field('key', 'Key', identifying=True)


class JiraProjectComponent(ResourceType):
    name = Field('name', 'Name', identifying=True)


class JiraIssueType(ResourceType):
    name = Field('name', 'Name', identifying=True)


class JiraIssueStatus(ResourceType):
    name = Field('name', 'Name', identifying=True)


class JiraIssuePriority(ResourceType):
    name = Field('name', 'Name', identifying=True)


class JiraLabel(ResourceType):
    name = Field('name', 'Name', identifying=True)


class JiraCustomField(ResourceType):
    name = Field('name', 'Name', identifying=True)


class JiraVersion(ResourceType):
    name = Field('name', 'Name', identifying=True)


class JiraIssue(ResourceType):
    project = Field('project', 'Project',
                    related_resource=JiraProject)
    issuetype = Field('issuetype', 'Issue Type',
                      related_resource=JiraIssueType)
    status = Field('status', 'Status',
                   related_resource=JiraIssueStatus)
    priority = Field('priority', 'Priority',
                     related_resource=JiraIssuePriority)
    creator = Field('creator', 'Creator',
                    related_resource=JiraUser)
    assignee = Field('assignee', 'Assignee',
                     related_resource=JiraUser)
    components = Field('components', 'Component/s"',
                       related_resource=JiraProjectComponent)
    labels = Field('labels', 'Labels',
                   related_resource=JiraLabel)
    summary = Field('summary', 'Summary')
    description = Field('description', 'Description')
    created = Field('created', 'Created')
    updated = Field('updated', 'Updated')
    timeoriginalestimate = Field('timeoriginalestimate', 'Original Estimate')
