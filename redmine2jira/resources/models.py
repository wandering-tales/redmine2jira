# -*- coding: utf-8 -*-

"""Definitions of internal domain entities models."""

from collections import namedtuple


FieldDefinition = namedtuple('FieldDefinition', ['key', 'name'])


class ResourceType(object):
    pass


# Redmine resource types

class RedmineUser(ResourceType):
    login = FieldDefinition('login', 'Login')


class RedmineGroup(ResourceType):
    name = FieldDefinition('name', 'Name')


class RedmineProject(ResourceType):
    identifier = FieldDefinition('identifier', 'Identifier')


class RedmineTracker(ResourceType):
    name = FieldDefinition('name', 'Name')


class RedmineIssue(ResourceType):
    project = FieldDefinition('project', 'Project')
    tracker = FieldDefinition('tracker', 'Tracker')
    status = FieldDefinition('status', 'Status')
    priority = FieldDefinition('priority', 'Priority')
    author = FieldDefinition('author', 'Author')
    assigned_to = FieldDefinition('assigned_to', 'Assignee')
    category = FieldDefinition('category', 'Category')
    subject = FieldDefinition('subject', 'Subject')
    description = FieldDefinition('description', 'Description')
    created = FieldDefinition('created_on', 'Created on')
    updated = FieldDefinition('updated_on', 'Updated on')
    start_date = FieldDefinition('start_date', 'Start date')
    due_date = FieldDefinition('due_date', 'Due date')
    done_ratio = FieldDefinition('done_ratio', 'Done %')
    estimated_hours = FieldDefinition('estimated_hours', 'Estimated time')


class RedmineIssueStatus(ResourceType):
    name = FieldDefinition('name', 'Name')


class RedmineIssuePriority(ResourceType):
    name = FieldDefinition('name', 'Name')


class RedmineIssueCategory(ResourceType):
    name = FieldDefinition('name', 'Name')


class RedmineCustomField(ResourceType):
    name = FieldDefinition('name', 'Name')


# Jira resource types

class JiraUser(ResourceType):
    username = FieldDefinition('username', 'Username')


class JiraProject(ResourceType):
    key = FieldDefinition('key', 'Key')


class JiraProjectComponent(ResourceType):
    name = FieldDefinition('name', 'Name')


class JiraIssue(ResourceType):
    project = FieldDefinition('project', 'Project')
    issuetype = FieldDefinition('issuetype', 'Issue Type')
    status = FieldDefinition('status', 'Status')
    priority = FieldDefinition('priority', 'Priority')
    creator = FieldDefinition('creator', 'Creator')
    assignee = FieldDefinition('assignee', 'Assignee')
    components = FieldDefinition('components', 'Component/s"')
    labels = FieldDefinition('labels', 'Labels')
    summary = FieldDefinition('summary', 'Summary')
    description = FieldDefinition('description', 'Description')
    created = FieldDefinition('created', 'Created')
    updated = FieldDefinition('updated', 'Updated')
    timeoriginalestimate = FieldDefinition('timeoriginalestimate',
                                           'Original Estimate')


class JiraIssueType(ResourceType):
    name = FieldDefinition('name', 'Name')


class JiraIssueStatus(ResourceType):
    name = FieldDefinition('name', 'Name')


class JiraIssuePriority(ResourceType):
    name = FieldDefinition('name', 'Name')


class JiraLabel(ResourceType):
    name = FieldDefinition('name', 'Name')


class JiraCustomField(ResourceType):
    name = FieldDefinition('name', 'Name')
