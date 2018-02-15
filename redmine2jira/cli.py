# -*- coding: utf-8 -*-

"""Console script for redmine2jira."""

from __future__ import absolute_import
from __future__ import unicode_literals

from builtins import str

try:
    from contextlib import suppress
except ImportError:
    from contextlib2 import suppress

from datetime import timedelta
from functools import reduce
from itertools import chain
from operator import and_, itemgetter

import click

from click_default_group import DefaultGroup
from inflection import humanize, underscore
from isodate import duration_isoformat
from redminelib import Redmine
from redminelib.exceptions import ForbiddenError
from redminelib.resultsets import ResourceSet
from six import text_type
from six.moves.urllib.parse import unquote
from tabulate import tabulate

from redmine2jira import config
from redmine2jira.resources import models
from redmine2jira.resources.mappings import (
    RESOURCE_TYPE_IDENTIFYING_FIELD_MAPPINGS,
    ISSUE_CUSTOM_FIELD_TYPE_MAPPINGS,
    ResourceTypeMapping
)
from redmine2jira.utils.text import text2confluence_wiki


##################
# Static strings #
##################

MISSING_RESOURCE_MAPPINGS_MESSAGE = "Resource value mappings definition"
MISSING_RESOURCE_MAPPING_PROMPT_SUFFIX = " -> "


redmine = Redmine(config.REDMINE_URL, key=config.REDMINE_API_KEY)


@click.group(cls=DefaultGroup, default='export', default_if_no_args=True)
def main():
    """
    Export Redmine issues to a set of files which format
    is compatible with the JIRA Importers plugin (JIM).
    """


@main.command('export')
@click.argument('output', type=click.File('w'))
@click.option('--filter', 'query_string',
              help="Filter issues using URL query string syntax. "
                   "Please check documentation for additional details.")
# TODO Add option to append an additional label to all exported issues
# in order to easily recognize all the issues in the same import batch
def export_issues(output, query_string):
    """Export Redmine issues."""

    if query_string:
        issues = _get_issues_by_filter(query_string)
    else:
        issues = _get_all_issues()

    click.echo("{:d} issue{} found!"
               .format(len(issues), "s" if len(issues) > 1 else ""))

    _export_issues(issues)

    click.echo("Issues exported in '{}'!".format(output.name))
    click.echo()
    click.echo()
    click.echo("Good Bye!")


def _get_issues_by_filter(query_string):
    """
    Fetch issues from Redmine filtering by the parameters
    in a URL query string.

    :param query_string: An URL query string
    :return: Filtered issues
    """
    # Split filters written in URL query string syntax,
    # URL decoding parameters values
    filters = {k: unquote(v)
               for k, v in zip(*[iter([kv for p in query_string.split('&')
                                       for kv in p.split('=')])] * 2)}

    issues = redmine.issue.filter(**filters)

    # The 'issue_id' filter is honored starting from
    # a certain version of Redmine, but it's not known which.
    # If the 'issue_id' filter was in the initial query string,
    # we may need to guess whether it has been ignored or not.
    if 'issue_id' in filters.keys():
        if config.CHECK_ISSUE_ID_FILTER_AVAILABILITY or \
           not config.ISSUE_ID_FILTER_AVAILABLE:
            issues_ids_filter = \
                frozenset(map(int, filters['issue_id'].split(',')))

            # If the total count of the resource set
            # is greater than the number of issue ID's
            # included in the 'issue_id' filter,
            # it means the latter is being ignored...
            if config.CHECK_ISSUE_ID_FILTER_AVAILABILITY:
                click.echo("Checking 'Issue ID' filter availability "
                           "in current Redmine instance...")

            if (config.CHECK_ISSUE_ID_FILTER_AVAILABILITY and
                len(issues) > len(issues_ids_filter)) or \
               not config.ISSUE_ID_FILTER_AVAILABLE:
                if config.CHECK_ISSUE_ID_FILTER_AVAILABILITY:
                    click.echo("The 'Issue ID' filter is not available!")

                    if config.ISSUE_ID_FILTER_AVAILABLE:
                        click.echo("You may disable both the "
                                   "ISSUE_ID_FILTER_AVAILABLE and "
                                   "CHECK_ISSUE_ID_FILTER_AVAILABILITY flags "
                                   "in your settings.")

                # Filter the resource set with the issue ID's in the filter
                issues = [issue for issue in issues
                          if issue.id in issues_ids_filter]

    return issues


def _get_all_issues():
    """
    Fetch all issues from Redmine.

    :return: All issues
    """
    return redmine.issue.all()


def _export_issues(issues):
    """
    Export issues and their relations to a JSON file which structure is
    compatible with the JIRA Importers plugin (JIM).

    All the issue relations which targets are not self-contained in the
    result set are exported in a separate CSV file. Such file should be
    imported whenever all the referenced issues (the endpoints of the
    relations) are already present in the target Jira instance.

    During the export loop all the occurrences of several resource types
    are mapped to Jira resource type instances. The mapping is primarily
    achieved statically, via dictionaries defined in the local configuration
    file by the final user for each resource type; the first time a resource
    misses a static mapping, as a fallback, the final user is prompted to
    interactively specify one, dynamically extending the initial static
    dictionary.

    The resource types that support custom mappings are the following:

    - Users
    - Groups
    - Projects
    - Trackers
    - Issue statuses
    - Issue priorities
    - Issue custom fields
    - Issue categories (on a per-project basis)

    Though users references can be found both in the issues properties (author,
    assignee, users related custom fields) and related child resources
    (watchers, attachments, journal entries, time entries), groups references
    can only be found in the "assignee" field.

    :param issues: Issues to export
    """
    # Get all Redmine users, groups, projects, trackers, issue statuses,
    # issue priorities, issue custom fields and store them by ID

    users = {user.id: user for user in chain(redmine.user.all(),
                                             redmine.user.filter(status=3))}

    groups = None

    if config.ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS:
        groups = {group.id: group for group in redmine.group.all()}

    projects = {project.id: project
                for project in redmine.project.all(include='issue_categories')}
    trackers = {tracker.id: tracker for tracker in redmine.tracker.all()}
    issue_statuses = {issue_status.id: issue_status
                      for issue_status in redmine.issue_status.all()}
    issue_priorities = {
        issue_priority.id: issue_priority
        for issue_priority in redmine.enumeration
                                     .filter(resource='issue_priorities')}

    issue_custom_fields = \
        {cf.id: cf for cf in redmine.custom_field.all()
         if cf.customized_type == 'issue'}

    # Get all Redmine issue categories and versions
    # and store them by project ID and, respectively,
    # by issue category ID and version ID

    issue_categories = {
        project.id: {
            issue_category.id: issue_category
            for issue_category in project.issue_categories
        }
        for project in projects.values()
    }

    # To build versions dictionary on a per project basis
    # we need to ignore 403 errors for projects where
    # no versions have been defined yet.
    versions = dict()

    for project in projects.values():
        versions[project.id] = dict()

        with suppress(ForbiddenError):
            for version in project.versions:
                versions[project.id][version.id] = version

    issues_export = dict()
    resource_value_mappings = dict()

    for issue in issues:
        # The issue project must be saved before everything else.
        # That's because all the issues entities must be children of a project
        # entity in the export dictionary.
        project_export = _save_project(issue.project, projects,
                                       resource_value_mappings, issues_export)

        # Create and append new empty issue dictionary
        # to project issues list
        issue_export = dict()
        project_export['issues'].append(issue_export)

        # Save required standard fields
        _save_id(issue.id, issue_export)
        _save_subject(issue.subject, issue_export)
        _save_author(issue.author, users, projects,
                     resource_value_mappings, issue_export)
        _save_tracker(issue.tracker, trackers, projects,
                      resource_value_mappings, issue_export)
        _save_status(issue.status, issue_statuses, projects,
                     resource_value_mappings, issue_export)
        _save_priority(issue.priority, issue_priorities, projects,
                       resource_value_mappings, issue_export)
        _save_created_on(issue.created_on, issue_export)
        _save_updated_on(issue.updated_on, issue_export)

        # Save optional standard fields
        if hasattr(issue, 'description'):
            _save_description(issue.description, issue_export)

        if hasattr(issue, 'assigned_to'):
            _save_assigned_to(issue.assigned_to, users, groups, projects,
                              resource_value_mappings, issue_export)

        if hasattr(issue, 'category'):
            _save_category(issue.category, issue.project.id, issue_categories,
                           projects, resource_value_mappings, project_export,
                           issue_export)

        if hasattr(issue, 'estimated_hours'):
            _save_estimated_hours(issue.estimated_hours, issue_export)

        # Save custom fields
        if hasattr(issue, 'custom_fields'):
            _save_custom_fields(issue.custom_fields, issue.project.id,
                                issue_custom_fields, users, projects, versions,
                                resource_value_mappings, issue_export)

        # Save related resources
        _save_watchers(issue.watchers, users, projects,
                       resource_value_mappings, issue_export)
        _save_attachments(issue.attachments, users, projects,
                          resource_value_mappings, issue_export)
        _save_journals(issue.journals, users, projects,
                       resource_value_mappings, issue_export)
        _save_time_entries(issue.time_entries)

        # TODO Save sub-tasks

        # TODO Save relations


def _save_project(project, projects, resource_value_mappings, issues_export):
    """
    Save issue project in the export dictionary.

    :param project: Issue project
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issues_export: Issues export dictionary
    """
    project_value_mapping = \
        _get_project_mapping(projects[project.id], projects,
                             resource_value_mappings)

    projects = issues_export.setdefault('projects', [])

    try:
        project = next((project for project in projects
                        if project['key'] == project_value_mapping))
    except StopIteration:
        project = {'key': project_value_mapping, 'issues': []}
        projects.append(project)

    return project


def _get_project_mapping(project, projects, resource_value_mappings):
    """
    Get the Jira value mapping for the project field.

    :param project: Issue project
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the project
    """
    return _get_resource_mapping(project, projects, resource_value_mappings)


def _save_id(issue_id, issue_export):
    """
    Save issue ID in the export dictionary as "external ID".

    :param issue_id: Issue ID
    :param issue_export: Single issue export dictionary
    """
    issue_export['externalId'] = _get_id_mapping(issue_id)


def _get_id_mapping(issue_id):
    """
    Get the Jira value mapping for the ID field.

    :param issue_id: Issue ID
    :return: Jira value mapping for the ID
    """
    return str(issue_id)


def _save_subject(subject, issue_export):
    """
    Save issue subject in the export dictionary.

    :param subject: Issue subject
    :param issue_export: Single issue export dictionary
    """
    issue_export['summary'] = _get_subject_mapping(subject)


def _get_subject_mapping(subject):
    """
    Get the Jira value mapping for the subject field.

    :param subject: Issue subject
    :return: Jira value mapping for the subject
    """
    return subject


def _save_author(author, users, projects, resource_value_mappings,
                 issue_export):
    """
    Save issue author in the export dictionary.

    :param author: Issue author
    :param users: All Redmine users
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    issue_export['reporter'] = _get_author_mapping(users[author.id], projects,
                                                   resource_value_mappings)


def _get_author_mapping(author, projects, resource_value_mappings):
    """
    Get the Jira value mapping for the author field.

    :param author: Issue author
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the author
    """
    return _get_resource_mapping(author, projects, resource_value_mappings)


def _save_tracker(tracker, trackers, projects, resource_value_mappings,
                  issue_export):
    """
    Save issue tracker in the export dictionary.

    :param tracker: Issue tracker
    :param trackers: All Redmine trackers
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    issue_export['issueType'] = \
        _get_tracker_mapping(trackers[tracker.id], projects,
                             resource_value_mappings)


def _get_tracker_mapping(tracker, projects, resource_value_mappings):
    """
    Get the Jira value mapping for the tracker field.

    :param tracker: Issue tracker
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the tracker
    """
    return _get_resource_mapping(tracker, projects, resource_value_mappings)


def _save_status(status, issue_statuses, projects, resource_value_mappings,
                 issue_export):
    """
    Save issue status in the export dictionary.

    :param status: Issue status
    :param issue_statuses: All Redmine issue statuses
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    issue_export['status'] = \
        _get_status_mapping(issue_statuses[status.id], projects,
                            resource_value_mappings)


def _get_status_mapping(status, projects, resource_value_mappings):
    """
    Get the Jira value mapping for the status field.

    :param status: Issue status
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the issue status
    """
    return _get_resource_mapping(status, projects, resource_value_mappings)


def _save_priority(priority, issue_priorities, projects,
                   resource_value_mappings, issue_export):
    """
    Save issue priority in the export dictionary.

    :param priority: Issue priority
    :param issue_priorities: All Redmine issue priorities
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    issue_export['priority'] = \
        _get_priority_mapping(issue_priorities[priority.id], projects,
                              resource_value_mappings)


def _get_priority_mapping(priority, projects, resource_value_mappings):
    """
    Get the Jira value mapping for the priority field.

    :param priority: Issue priority
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the issue priority
    """
    return _get_resource_mapping(priority, projects,
                                 resource_value_mappings,
                                 resource_type=models.RedmineIssuePriority)


def _save_created_on(created_on, issue_export):
    """
    Save issue creation date in the export dictionary.

    :param created_on: Issue creation date
    :param issue_export: Single issue export dictionary
    """
    issue_export['created'] = _get_created_on_mapping(created_on)


def _get_created_on_mapping(created_on):
    """
    Get the Jira value mapping for the creation date field.

    :param created_on: Issue creation date
    :return: Jira value mapping for the creation date
    """
    return created_on.isoformat()


def _save_updated_on(updated_on, issue_export):
    """
    Save issue modification date in the export dictionary.

    :param updated_on: Issue modification date
    :param issue_export: Single issue export dictionary
    """
    issue_export['updated'] = _get_updated_on_mapping(updated_on)


def _get_updated_on_mapping(updated_on):
    """
    Get the Jira value mapping for the modification date field.

    :param updated_on: Issue modification date
    :return: Jira value mapping for the modification date
    """
    return updated_on.isoformat()


def _save_description(description, issue_export):
    """
    Save issue description in the export dictionary.

    :param description: Issue description
    :param issue_export: Single issue export dictionary
    """
    issue_export['description'] = _get_description_mapping(description)


def _get_description_mapping(description):
    """
    Get the Jira value mapping for the description field.

    :param description: Issue description
    :return: Jira value mapping for the description
    """
    if config.REDMINE_TEXT_FORMATTING != 'none':
        description = text2confluence_wiki(description)

    return description


def _save_assigned_to(assigned_to, users, groups, projects,
                      resource_value_mappings, issue_export):
    """
    Save issue assignee in the export dictionary.
    By default the assignee is a user, but if the
    "Allow issue assignment to groups" setting is
    enabled in Redmine the assignee may also be a
    group.

    :param assigned_to: Issue assignee, which may refer
                        either to a user or a group
    :param users: All Redmine users
    :param groups: All redmine groups
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    # If the assignee is a group...
    if config.ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS and assigned_to.id in groups:
        assigned_to = \
            _get_assigned_to_mapping(groups[assigned_to.id], projects,
                                     resource_value_mappings)
    # ...else if the assignee is a user...
    else:
        assigned_to = \
            _get_assigned_to_mapping(users[assigned_to.id], projects,
                                     resource_value_mappings)

    issue_export['assignee'] = assigned_to


def _get_assigned_to_mapping(assigned_to, projects, resource_value_mappings):
    """
    Get the Jira value mapping for the assignee field.

    :param assigned_to: Issue assignee
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the assignee
    """
    return _get_resource_mapping(assigned_to, projects,
                                 resource_value_mappings)


def _save_category(category, project_id, issue_categories, projects,
                   resource_value_mappings, project_export, issue_export):
    """
    Save issue category in the export dictionary.

    :param category: Issue category
    :param project_id: ID of the project the issue belongs to
    :param issue_categories: All Redmine issue categories
                             on a per-project basis
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param project_export: Parent project export dictionary
    :param issue_export: Single issue export dictionary
    """
    category_value_mapping, category_resource_type_mapping = \
        _get_category_mapping(issue_categories[project_id][category.id],
                              project_id, projects, resource_value_mappings)

    if category_resource_type_mapping.jira == models.JiraProjectComponent:
        # Add component to parent project export dictionary
        project_export.setdefault('components', []) \
                      .append(category_value_mapping)
        # Add component to issue export dictionary
        issue_export.setdefault('components', []) \
                    .append(category_value_mapping)
    elif category_resource_type_mapping.jira == models.JiraLabel:
        # Add label to issue export dictionary
        issue_export.setdefault('labels', []) \
                    .append(category_value_mapping)


def _get_category_mapping(category, project_id, projects,
                          resource_value_mappings):
    """
    Get both the Jira value mapping for the category field,
    and the related ``ResourceTypeMapping`` object describing
    the Redmine and Jira resource types respectively involved
    in the mapping.

    :param category: Issue category
    :param project_id: ID of the project the issue belongs to
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: A tuple containing both the jira value mapping for the
             category and the related ``ResourceTypeMapping`` object
    """
    return _get_resource_mapping(category, projects,
                                 resource_value_mappings,
                                 project_id=project_id,
                                 include_type_mapping=True)


def _save_estimated_hours(estimated_hours, issue_export):
    """
    Save issue estimated hours in the export dictionary.

    :param estimated_hours: Issue estimated hours
    :param issue_export: Single issue export dictionary
    """
    issue_export['originalEstimate'] = \
        _get_estimated_hours_mapping(estimated_hours)


def _get_estimated_hours_mapping(estimated_hours):
    """
    Get the Jira value mapping for the estimated hours field.

    :param estimated_hours: Issue estimated hours
    :return: Jira value mapping for the estimated hours
    """
    return duration_isoformat(timedelta(hours=estimated_hours))


def _save_custom_fields(custom_fields, project_id, issue_custom_fields, users,
                        projects, versions, resource_value_mappings,
                        issue_export):
    """
    Save issue custom fields to export dictionary.

    :param custom_fields: Issue custom fields
    :param project_id: ID of the project the issue belongs to
    :param issue_custom_fields: All Redmine issue custom fields definitions
    :param users: All Redmine users
    :param projects: All Redmine projects
    :param versions: All Redmine versions on a per-project basis
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    for custom_field in custom_fields:
        custom_field_def = issue_custom_fields[custom_field.id]

        field_name = _get_custom_field_mapping(custom_field, projects,
                                               resource_value_mappings)

        format_mapping = \
            ISSUE_CUSTOM_FIELD_TYPE_MAPPINGS[custom_field_def.field_format]

        field_type = \
            format_mapping['multiple'] \
            if getattr(custom_field_def, 'multiple', False) \
            else format_mapping['single']

        value = _get_custom_field_value_mapping(custom_field, project_id,
                                                issue_custom_fields, users,
                                                projects, versions,
                                                resource_value_mappings)

        custom_field_dict = {
            'fieldName': field_name,
            'fieldType': field_type,
            'value': value
        }

        issue_export.setdefault('customFieldValues', []) \
                    .append(custom_field_dict)


def _get_custom_field_mapping(custom_field, projects, resource_value_mappings):
    """
    Get the Jira value mapping for the issue custom field.

    :param custom_field: Issue custom field
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the custom field
    """
    return _get_resource_mapping(custom_field, projects,
                                 resource_value_mappings)


def _get_custom_field_value_mapping(custom_field, project_id,
                                    issue_custom_fields, users, projects,
                                    versions, resource_value_mappings):
    """
    Get the Jira value mapping for the custom field value.

    :param custom_field: Issue custom field
    :param project_id: ID of the project the issue belongs to
    :param issue_custom_fields: All Redmine issue custom fields definitions
    :param users: All Redmine users
    :param projects: All Redmine projects
    :param versions: All Redmine versions on a per-project basis
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :return: Jira value mapping for the custom field value
    """
    custom_field_def = issue_custom_fields[custom_field.id]
    redmine_value = custom_field.value
    jira_value = redmine_value

    if redmine_value:
        if custom_field_def.field_format == 'bool':
            if redmine_value == '1':
                jira_value = 'Yes'
            elif redmine_value == '0':
                jira_value = 'No'
        elif custom_field_def.field_format == 'date':
            jira_value = redmine_value.isoformat()
        elif custom_field_def.field_format == 'float':
            jira_value = float(redmine_value)
        elif custom_field_def.field_format == 'int':
            jira_value = int(redmine_value)
        elif custom_field_def.field_format in ['text', 'string']:
            if config.REDMINE_TEXT_FORMATTING != 'none':
                # Here we should check also if text formatting is enabled
                # at custom field level via the "Text Formatting" option.
                # Unfortunately the current version of Redmine REST API
                # for custom fields does not return this property.
                # Therefore we make the assumption that if the Redmine
                # administrator enabled the text formatting at system
                # level, he did it for text custom fields as well.
                jira_value = text2confluence_wiki(redmine_value)
        elif custom_field_def.field_format == 'user':
            if getattr(custom_field_def, 'multiple', False):
                user_ids = set(map(int, redmine_value))
                jira_value = [
                    _get_resource_mapping(
                        user, projects, resource_value_mappings)
                    for user_id, user in users.items()
                    if user_id in user_ids
                ]
            else:
                user_id = int(redmine_value)
                jira_value = _get_resource_mapping(
                    users[user_id], projects, resource_value_mappings)
        elif custom_field_def.field_format == 'version':
            if getattr(custom_field_def, 'multiple', False):
                version_ids = set(map(int, redmine_value))
                jira_value = [
                    _get_resource_mapping(
                        version, projects, resource_value_mappings)
                    for version_id, version in versions[project_id].items()
                    if version_id in version_ids
                ]
            else:
                version_id = int(redmine_value)
                jira_value = \
                    _get_resource_mapping(
                        versions[project_id][version_id], projects,
                        resource_value_mappings)
        elif custom_field_def.field_format in ['link', 'list']:
            pass
        else:
            raise NotImplementedError(
                "'{}' field format not supported!"
                .format(custom_field_def.field_format))

    return jira_value


def _save_watchers(watchers, users, projects, resource_value_mappings,
                   issue_export):
    """
    Save issue watchers to export dictionary.

    :param watchers: Issue watchers
    :param users: All Redmine users
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    for watcher in watchers:
        user = _get_resource_mapping(users[watcher.id], projects,
                                     resource_value_mappings)

        issue_export.setdefault('watchers', []) \
                    .append(user)


def _save_attachments(attachments, users, projects, resource_value_mappings,
                      issue_export):
    """
    Save issue attachments to export dictionary.

    :param attachments: Issue attachments
    :param users: All Redmine users
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    for attachment in attachments:
        attacher = _get_resource_mapping(users[attachment.author.id], projects,
                                         resource_value_mappings)

        attachment_dict = {
            "name": attachment.filename,
            "attacher": attacher,
            "created": attachment.created_on.isoformat(),
            "uri": attachment.content_url,
            "description": attachment.description
        }

        issue_export.setdefault('attachments', []) \
                    .append(attachment_dict)


def _save_journals(journals, users, projects, resource_value_mappings,
                   issue_export):
    """
    Save issue journals to export dictionary.

    A Redmine issue journal is conceived as a list of changes
    applied to the issue. Those changes includes both additions
    of user notes and modifications of issue properties.
    Following such criteria an user, in a single action, can
    either add a note, or change several issue properties, or both.
    Redmine saves all this data atomically in a new "journal" item,
    which is shown in the issue "History" section under the same
    sequential number.

    Jira, on the other hand, treats addition of comments and issue
    property changes as different events, achievable with distinct
    user actions. Coherently, all issue comments are visible in the
    "Comments" section, whereas all issue property changes in the
    "History" section: both lists are chronologically sorted and
    both are activated clicking the tab having the same name.

    Therefore this method "splits" a single journal item into
    a comment and a list of changes to issue properties, only
    if they respectively exist, since a single journal item
    **may** contain either only a comment, or only a list of
    changes to issue properties, or both.

    :param journals: Issue journals
    :param users: All Redmine users
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    for journal in journals:
        # If there's a user note in the journal item...
        if getattr(journal, 'notes', None):
            _save_journal_notes(journal, users, projects,
                                resource_value_mappings, issue_export)


def _save_journal_notes(journal, users, projects, resource_value_mappings,
                        issue_export):
    """
    Save issue journal notes to export dictionary.

    :param journal: Issue journal item
    :param users: All Redmine users
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param issue_export: Single issue export dictionary
    """
    author = _get_resource_mapping(users[journal.user.id], projects,
                                   resource_value_mappings)

    comment_body = journal.notes

    if config.REDMINE_TEXT_FORMATTING != 'none':
        comment_body = text2confluence_wiki(comment_body)

    comment_dict = {
        "author": author,
        "body": comment_body,
        "created": journal.created_on.isoformat()
    }

    issue_export.setdefault('comments', []) \
                .append(comment_dict)


def _save_time_entries(time_entries):
    """
    Save issue time entries to export dictionary.

    :param time_entries: Issue time entries
    """
    for time_entry in time_entries:
        # TODO Set value in the export dictionary
        click.echo("Time entry: {}".format(time_entry))

        # TODO Add time spent to issue total time spent

    # TODO Save issue total time spent


def _get_resource_mapping(resource, projects, resource_value_mappings,
                          resource_type=None, project_id=None,
                          include_type_mapping=False):
    """
    For each jira resource type mapped by the type of the given Redmine
    resource instance, this method finds a jira resource value.

    By default the type of the Redmine resource instance is guessed from
    its class, but can be explicitly defined via the ``resource_type``
    parameter.

    For each resource type mapping the method attempts to find a user-defined
    value mapping in the configuration settings first, falling back to value
    mappings dynamically defined by the final user at runtime.

    New dynamic value mappings are defined when no value mapping is found
    among both static and dynamic value mappings. In that case the final user
    is prompted to define one at runtime; furthermore, he may also be
    prompted to choose a jira resource type mapping, if the current Redmine
    resource type is mapped to more than one jira resource type.

    :param resource: Resource instance
    :param projects: All Redmine projects
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param resource_type: Internal Redmine resource type class.
                          If not provided the Redmine resource type class is
                          dynamically derived from the RedmineLib resource
                          instance class name.
    :param project_id: ID of the project the resource value is bound to,
                       if any.
    :param include_type_mapping: If ``True`` the method return also the
                                 ``ResourceTypeMapping`` tuple-like object,
                                 which store references to the Redmine and Jira
                                 resource types respectively involved in the
                                 mapping. Default is ``False``.
    :return: The mapped jira resource value or, if ``include_type_mapping``
             is set to ``True``, a  tuple containing both the related
             ``ResourceTypeMapping`` object and the mapped jira resource value
    """
    # Guess Redmine resource type class
    # by RedmineLib resource instance class name
    # unless explicitly specified
    redmine_resource_type = resource_type

    if not redmine_resource_type:
        redmine_resource_type = \
            eval('models.Redmine' + resource.__class__.__name__)

    humanized_redmine_resource_type = \
        humanize(underscore(redmine_resource_type.__name__))

    jira_resource_type = None
    resource_type_mapping = None
    redmine_resource_value = None
    jira_resource_value = None
    field_mapping = None

    jira_resource_type_field_mappings = \
        {k.jira: v for k, v in RESOURCE_TYPE_IDENTIFYING_FIELD_MAPPINGS.items()
         if k.redmine == redmine_resource_type}

    # Search for a statically user-defined value mapping
    for jira_resource_type, field_mapping in \
            jira_resource_type_field_mappings.items():
        # Build ResourceTypeMapping object
        resource_type_mapping = ResourceTypeMapping(redmine_resource_type,
                                                    jira_resource_type)

        # Dynamically compose resource type mapping setting name
        resource_type_mapping_setting_name = \
            '{}_{}_MAPPINGS'.format(
                underscore(redmine_resource_type.__name__).upper(),
                underscore(jira_resource_type.__name__).upper())

        # Get the Redmine resource value
        redmine_resource_value = getattr(resource, field_mapping.redmine.key)

        # Try to get the Jira resource value from mappings
        # statically defined in configuration settings
        static_resource_value_mappings = \
            getattr(config, resource_type_mapping_setting_name, {})

        if project_id is not None:
            # Use project identifier instead of its internal ID
            # to fetch per-project resource value mappings inside
            # user-defined configuration files.
            project_identifier = projects[project_id].identifier
            static_resource_value_mappings = \
                static_resource_value_mappings.get(project_identifier, {})

        jira_resource_value = \
            static_resource_value_mappings.get(redmine_resource_value, None)

        if jira_resource_value is not None:
            # A Jira resource value mapping has been found. Exit!
            break

    if jira_resource_value is None:
        # Search for a dynamically user-defined value mapping
        for jira_resource_type, field_mapping \
                in jira_resource_type_field_mappings.items():
            # Build ResourceTypeMapping object
            resource_type_mapping = ResourceTypeMapping(redmine_resource_type,
                                                        jira_resource_type)

            # Get the Redmine resource value
            redmine_resource_value = getattr(resource,
                                             field_mapping.redmine.key)

            # Try to get the Jira resource value from mappings
            # dynamically defined at runtime
            if project_id is None:
                jira_resource_value = \
                    resource_value_mappings.get((redmine_resource_value,
                                                 resource_type_mapping), None)
            else:
                jira_resource_value = \
                    resource_value_mappings.get((project_id,
                                                 redmine_resource_value,
                                                 resource_type_mapping), None)

            if jira_resource_value is not None:
                # A Jira resource value mapping has been found. Exit!
                break

    if jira_resource_value is None:
        # No value mapping found!

        # If there not exist dynamically user-defined value mappings...
        if not resource_value_mappings:
            click.echo()
            click.echo("-" * len(MISSING_RESOURCE_MAPPINGS_MESSAGE))
            click.echo(MISSING_RESOURCE_MAPPINGS_MESSAGE)
            click.echo("-" * len(MISSING_RESOURCE_MAPPINGS_MESSAGE))

        # If the Redmine resource type can be mapped
        # to more than one Jira resource types...
        if len(jira_resource_type_field_mappings.keys()) > 1:
            # ...prompt user to choose one
            click.echo(
                "Missing value mapping for {} '{}'."
                .format(humanized_redmine_resource_type,
                        redmine_resource_value))
            click.echo("A {} can be mapped with one of the "
                       "following Jira resource types:"
                       .format(humanized_redmine_resource_type))
            click.echo()

            static_jira_resource_type_choices = \
                {i + 1: jrt
                 for i, jrt in enumerate(jira_resource_type_field_mappings)}

            for k, v in static_jira_resource_type_choices.items():
                # Strip 'Jira' prefix from class name
                humanized_jira_resource_type = \
                    humanize(underscore(v.__name__[len('Jira'):]))

                click.echo("{:d}) {}".format(k, humanized_jira_resource_type))

            click.echo()

            choice = click.prompt(
                "Choose a target Jira resource type",
                prompt_suffix=": ",
                type=click.IntRange(1, len(static_jira_resource_type_choices)))

            jira_resource_type = static_jira_resource_type_choices[choice]

        click.echo()

        humanized_jira_resource_type = \
            humanize(underscore(jira_resource_type.__name__))

        jira_resource_value = click.prompt(
            "[{} {}{}{} {}] {}"
            .format(humanized_redmine_resource_type,
                    field_mapping.redmine.name.upper(),
                    MISSING_RESOURCE_MAPPING_PROMPT_SUFFIX,
                    humanized_jira_resource_type,
                    field_mapping.jira.name.upper(),
                    redmine_resource_value),
            prompt_suffix=MISSING_RESOURCE_MAPPING_PROMPT_SUFFIX)

        resource_type_mapping = ResourceTypeMapping(redmine_resource_type,
                                                    jira_resource_type)

        if project_id is None:
            resource_value_mappings[
                (redmine_resource_value,
                 resource_type_mapping)] = jira_resource_value
        else:
            resource_value_mappings[
                (project_id,
                 redmine_resource_value,
                 resource_type_mapping)] = jira_resource_value

    if include_type_mapping:
        return jira_resource_value, resource_type_mapping
    else:
        return jira_resource_value


@main.group('list')
def list_resources():
    """List Redmine resources."""


@list_resources.command('users')
@click.option('--all', 'user_status', flag_value=0,
              help="Get all users")
@click.option('--active', 'user_status', flag_value=1, default=True,
              help="Filter active users")
@click.option('--locked', 'user_status', flag_value=3,
              help="Filter locked users")
def list_users(user_status):
    """List Redmine users."""

    users = None

    if user_status == 0:
        # Get Redmine all users
        users = chain(redmine.user.all(), redmine.user.filter(status=3))
    elif user_status == 1:
        # Get Redmine active users
        users = redmine.user.all()
    elif user_status == 3:
        # Get Redmine locked users
        users = redmine.user.filter(status=3)

    _list_resources(users, sort_key='login', exclude_attrs=('created_on',))


@list_resources.command('groups')
def list_groups():
    """List Redmine groups."""

    groups = redmine.group.all()

    _list_resources(groups, sort_key='name')


@list_resources.command('projects')
def list_projects():
    """List Redmine projects."""

    projects = redmine.project.all()

    def get_project_full_name(project, full_name):
        """
        Build the full name of the project including hierarchy information.

        :param project: Project Resource
        :param full_name: Full name of the project used in the recursion
        :return: Project full name (at the end of recursion)
        """
        # If it's not the first level of recursion...
        if full_name != project.name:
            full_name = "{} / {}".format(project.name, full_name)
        else:
            full_name = project.name

        if hasattr(project, 'parent'):
            parent = redmine.project.get(project.parent.id)
            full_name = get_project_full_name(parent, full_name)

        return full_name

    _list_resources(projects,
                    sort_key='name',
                    format_dict={'name': get_project_full_name},
                    exclude_attrs=('description', 'enabled_modules',
                                   'created_on', 'updated_on'))


@list_resources.command('trackers')
def list_trackers():
    """List Redmine trackers."""

    trackers = redmine.tracker.all()

    _list_resources(trackers,
                    sort_key='name',
                    exclude_attrs={'default_status': lambda r, v: v.name})


@list_resources.command('queries')
def list_queries():
    """List Redmine queries."""

    queries = redmine.query.all()

    _list_resources(queries, sort_key='name')


@list_resources.command('issue_statuses')
def list_issues_statuses():
    """List Redmine issue statuses."""

    issue_statuses = redmine.issue_status.all()

    _list_resources(issue_statuses, sort_key='name')


@list_resources.command('issue_priorities')
def list_issues_priorities():
    """List Redmine issue priorities."""

    issue_priorities = redmine.enumeration.filter(resource='issue_priorities')

    _list_resources(issue_priorities, sort_key='name')


@list_resources.command('custom_fields')
def list_custom_fields():
    """List Redmine custom fields."""

    custom_fields = redmine.custom_field.all()

    _list_resources(custom_fields, sort_key='name')


@list_resources.command('issue_categories')
@click.argument('project', 'Project ID/identifier')
def list_issue_categories(project):
    """List Redmine issue categories for a project."""

    categories = redmine.version.filter(project_id=project)

    _list_resources(categories, sort_key='name', exclude_attrs=['project'])


@list_resources.command('versions')
@click.argument('project', 'Project ID/identifier')
def list_versions(project):
    """List Redmine versions for a project."""

    versions = redmine.version.filter(project_id=project)

    _list_resources(versions, sort_key='name', exclude_attrs=['project'])


def _list_resources(resource_set, sort_key,
                    format_dict=None, exclude_attrs=None):
    # Find resource attributes excluding relations with other resource types
    scalar_attributes = \
        (set((a for a in dir(resource)
              if not isinstance(getattr(resource, a), ResourceSet)))
         for resource in resource_set)

    # Compute a common subset among all the scalar attributes
    common_scalar_attributes = reduce(and_, scalar_attributes)
    # Declare base headers for all resource types
    base_headers = ['id']

    # Exclude specific attributes
    if exclude_attrs:
        base_headers[:] = [h for h in base_headers if h not in exclude_attrs]
        common_scalar_attributes -= set(exclude_attrs)

    # Appending sorting key to base headers
    if sort_key not in base_headers:
        base_headers.append(sort_key)

    # Create table headers appending lexicographically sorted
    # common attribute names to base headers list, which has
    # already been statically ordered.
    headers = \
        base_headers + sorted(common_scalar_attributes - set(base_headers))

    def _format(key, resource):
        value = getattr(resource, key)

        if format_dict and key in format_dict:
            return format_dict[key](resource, value)

        return text_type(value)

    # Build a "table" (list of dictionaries)
    # from all the resource instances,
    # using only the calculated attributes
    resource_table = sorted(({h: _format(h, resource) for h in headers}
                             for resource in resource_set),
                            key=itemgetter(sort_key))

    # Pretty print the resource table
    # using the dictionary keys as headers
    click.echo(tabulate(resource_table, headers="keys"))
