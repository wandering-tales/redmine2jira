# -*- coding: utf-8 -*-

"""Redmine to Jira exporter classes definitions."""

from __future__ import absolute_import
from __future__ import unicode_literals

from builtins import str

try:
    from contextlib import suppress
except ImportError:
    from contextlib2 import suppress

from datetime import timedelta
from itertools import chain

import click

from inflection import humanize, underscore
from isodate import duration_isoformat
from redminelib import Redmine
from redminelib.exceptions import ForbiddenError

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


class IssuesExporter(object):
    """
    Export a Redmine issues ResourceSet to a JSON file
    compatible with the Jira Importer Plugin (JIM).
    """

    def __init__(self):
        redmine = Redmine(config.REDMINE_URL, key=config.REDMINE_API_KEY)

        # Get all Redmine users, groups, projects, trackers, issue statuses,
        # issue priorities, issue custom fields and store them by ID

        self._users = {user.id: user
                       for user in chain(redmine.user.all(),
                                         redmine.user.filter(status=3))}

        self._groups = None

        if config.ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS:
            self._groups = {group.id: group for group in redmine.group.all()}

        self._projects = \
            {project.id: project
             for project in redmine.project.all(include='issue_categories')}

        self._trackers = {tracker.id: tracker
                          for tracker in redmine.tracker.all()}

        self._issue_statuses = {issue_status.id: issue_status
                                for issue_status in redmine.issue_status.all()}

        self._issue_priorities = {
            issue_priority.id: issue_priority
            for issue_priority in
            redmine.enumeration.filter(resource='issue_priorities')}

        self._issue_custom_fields = \
            {cf.id: cf for cf in redmine.custom_field.all()
             if cf.customized_type == 'issue'}

        # Get all Redmine issue categories and versions
        # and store them by project ID and, respectively,
        # by issue category ID and version ID

        self._issue_categories = {
            project.id: {
                issue_category.id: issue_category
                for issue_category in project.issue_categories
            }
            for project in self._projects.values()
        }

        # To build versions dictionary on a per project basis
        # we need to ignore 403 errors for projects where
        # no versions have been defined yet.
        self._versions = dict()

        for project in self._projects.values():
            self._versions[project.id] = dict()

            with suppress(ForbiddenError):
                for version in project.versions:
                    self._versions[project.id][version.id] = version

        self._resource_value_mappings = None

    def export(self, issues):
        """
        Export issues and their relations to a JSON file which structure is
        compatible with the JIRA Importers plugin (JIM).

        All the issue relations which targets are not self-contained in the
        result set are exported in a separate CSV file. Such file should be
        imported whenever all the referenced issues (the endpoints of the
        relations) are already present in the target Jira instance.

        During the export loop all the occurrences of several resource types
        are mapped to Jira resource type instances. The mapping is primarily
        achieved statically, via dictionaries defined in the local
        configuration file by the final user for each resource type; the first
        time a resource misses a static mapping, as a fallback, the final user
        is prompted to interactively specify one, dynamically extending the
        initial static dictionary.

        The resource types that support custom mappings are the following:

        - Users
        - Groups
        - Projects
        - Trackers
        - Issue statuses
        - Issue priorities
        - Issue custom fields
        - Issue categories (on a per-project basis)

        Though users references can be found both in the issues properties
        (author, assignee, users related custom fields) and related child
        resources (watchers, attachments, journal entries, time entries),
        groups references can only be found in the "assignee" field.

        :param issues: Issues to export
        """
        issues_export = dict()
        self._resource_value_mappings = dict()

        for issue in issues:
            # The issue project must be saved before everything else.
            # That's because all the issues entities must be children of a
            # project entity in the export dictionary.
            project_export = self._save_project(issue.project, issues_export)

            # Create and append new empty issue dictionary
            # to project issues list
            issue_export = dict()
            project_export['issues'].append(issue_export)

            # Save required standard fields
            self._save_id(issue.id, issue_export)
            self._save_subject(issue.subject, issue_export)
            self._save_author(issue.author, issue_export)
            self._save_tracker(issue.tracker, issue_export)
            self._save_status(issue.status, issue_export)
            self._save_priority(issue.priority, issue_export)
            self._save_created_on(issue.created_on, issue_export)
            self._save_updated_on(issue.updated_on, issue_export)

            # Save optional standard fields
            if hasattr(issue, 'description'):
                self._save_description(issue.description, issue_export)

            if hasattr(issue, 'assigned_to'):
                self._save_assigned_to(issue.assigned_to, issue_export)

            if hasattr(issue, 'category'):
                self._save_category(issue.category, issue.project.id,
                                    project_export, issue_export)

            if hasattr(issue, 'estimated_hours'):
                self._save_estimated_hours(issue.estimated_hours, issue_export)

            # Save custom fields
            if hasattr(issue, 'custom_fields'):
                self._save_custom_fields(issue.custom_fields, issue.project.id,
                                         issue_export)

            # Save related resources
            self._save_watchers(issue.watchers, issue_export)
            self._save_attachments(issue.attachments, issue_export)
            self._save_journals(issue.journals, issue_export)
            self._save_time_entries(issue.time_entries)

            # TODO Save sub-tasks

            # TODO Save relations

    def _save_project(self, project, issues_export):
        """
        Save issue project in the export dictionary.

        :param project: Issue project
        :param issues_export: Issues export dictionary
        """
        project_value_mapping = \
            self._get_project_mapping(self._projects[project.id])

        projects = issues_export.setdefault('projects', [])

        try:
            project = next((project for project in projects
                            if project['key'] == project_value_mapping))
        except StopIteration:
            project = {'key': project_value_mapping, 'issues': []}
            projects.append(project)

        return project

    def _get_project_mapping(self, project):
        """
        Get the Jira value mapping for the project field.

        :param project: Issue project
        :return: Jira value mapping for the project
        """
        return self._get_resource_mapping(project)

    def _save_id(self, issue_id, issue_export):
        """
        Save issue ID in the export dictionary as "external ID".

        :param issue_id: Issue ID
        :param issue_export: Single issue export dictionary
        """
        issue_export['externalId'] = self._get_id_mapping(issue_id)

    @staticmethod
    def _get_id_mapping(issue_id):
        """
        Get the Jira value mapping for the ID field.

        :param issue_id: Issue ID
        :return: Jira value mapping for the ID
        """
        return str(issue_id)

    def _save_subject(self, subject, issue_export):
        """
        Save issue subject in the export dictionary.

        :param subject: Issue subject
        :param issue_export: Single issue export dictionary
        """
        issue_export['summary'] = self._get_subject_mapping(subject)

    @staticmethod
    def _get_subject_mapping(subject):
        """
        Get the Jira value mapping for the subject field.

        :param subject: Issue subject
        :return: Jira value mapping for the subject
        """
        return subject

    def _save_author(self, author, issue_export):
        """
        Save issue author in the export dictionary.

        :param author: Issue author
        :param issue_export: Single issue export dictionary
        """
        issue_export['reporter'] = \
            self._get_author_mapping(self._users[author.id])

    def _get_author_mapping(self, author):
        """
        Get the Jira value mapping for the author field.

        :param author: Issue author
        :return: Jira value mapping for the author
        """
        return self._get_resource_mapping(author)

    def _save_tracker(self, tracker, issue_export):
        """
        Save issue tracker in the export dictionary.

        :param tracker: Issue tracker
        :param issue_export: Single issue export dictionary
        """
        issue_export['issueType'] = \
            self._get_tracker_mapping(self._trackers[tracker.id])

    def _get_tracker_mapping(self, tracker):
        """
        Get the Jira value mapping for the tracker field.

        :param tracker: Issue tracker
        :return: Jira value mapping for the tracker
        """
        return self._get_resource_mapping(tracker)

    def _save_status(self, status, issue_export):
        """
        Save issue status in the export dictionary.

        :param status: Issue status
        :param issue_export: Single issue export dictionary
        """
        issue_export['status'] = \
            self._get_status_mapping(self._issue_statuses[status.id])

    def _get_status_mapping(self, status):
        """
        Get the Jira value mapping for the status field.

        :param status: Issue status
        :return: Jira value mapping for the issue status
        """
        return self._get_resource_mapping(status)

    def _save_priority(self, priority, issue_export):
        """
        Save issue priority in the export dictionary.

        :param priority: Issue priority
        :param issue_export: Single issue export dictionary
        """
        issue_export['priority'] = \
            self._get_priority_mapping(self._issue_priorities[priority.id])

    def _get_priority_mapping(self, priority):
        """
        Get the Jira value mapping for the priority field.

        :param priority: Issue priority
        :return: Jira value mapping for the issue priority
        """
        return self._get_resource_mapping(
            priority,
            resource_type=models.RedmineIssuePriority)

    def _save_created_on(self, created_on, issue_export):
        """
        Save issue creation date in the export dictionary.

        :param created_on: Issue creation date
        :param issue_export: Single issue export dictionary
        """
        issue_export['created'] = self._get_created_on_mapping(created_on)

    @staticmethod
    def _get_created_on_mapping(created_on):
        """
        Get the Jira value mapping for the creation date field.

        :param created_on: Issue creation date
        :return: Jira value mapping for the creation date
        """
        return created_on.isoformat()

    def _save_updated_on(self, updated_on, issue_export):
        """
        Save issue modification date in the export dictionary.

        :param updated_on: Issue modification date
        :param issue_export: Single issue export dictionary
        """
        issue_export['updated'] = self._get_updated_on_mapping(updated_on)

    @staticmethod
    def _get_updated_on_mapping(updated_on):
        """
        Get the Jira value mapping for the modification date field.

        :param updated_on: Issue modification date
        :return: Jira value mapping for the modification date
        """
        return updated_on.isoformat()

    def _save_description(self, description, issue_export):
        """
        Save issue description in the export dictionary.

        :param description: Issue description
        :param issue_export: Single issue export dictionary
        """
        issue_export['description'] = \
            self._get_description_mapping(description)

    @staticmethod
    def _get_description_mapping(description):
        """
        Get the Jira value mapping for the description field.

        :param description: Issue description
        :return: Jira value mapping for the description
        """
        if config.REDMINE_TEXT_FORMATTING != 'none':
            description = text2confluence_wiki(description)

        return description

    def _save_assigned_to(self, assigned_to, issue_export):
        """
        Save issue assignee in the export dictionary.
        By default the assignee is a user, but if the
        "Allow issue assignment to groups" setting is
        enabled in Redmine the assignee may also be a
        group.

        :param assigned_to: Issue assignee, which may refer
                            either to a user or a group
        :param issue_export: Single issue export dictionary
        """
        # If the assignee is a group...
        if config.ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS and \
           assigned_to.id in self._groups:
            assigned_to = \
                self._get_assigned_to_mapping(self._groups[assigned_to.id])
        # ...else if the assignee is a user...
        else:
            assigned_to = \
                self._get_assigned_to_mapping(self._users[assigned_to.id])

        issue_export['assignee'] = assigned_to

    def _get_assigned_to_mapping(self, assigned_to):
        """
        Get the Jira value mapping for the assignee field.

        :param assigned_to: Issue assignee
        :return: Jira value mapping for the assignee
        """
        return self._get_resource_mapping(assigned_to)

    def _save_category(self, category, project_id, project_export,
                       issue_export):
        """
        Save issue category in the export dictionary.

        :param category: Issue category
        :param project_id: ID of the project the issue belongs to
        :param project_export: Parent project export dictionary
        :param issue_export: Single issue export dictionary
        """
        category_value_mapping, category_resource_type_mapping = \
            self._get_category_mapping(
                self._issue_categories[project_id][category.id], project_id)

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

    def _get_category_mapping(self, category, project_id):
        """
        Get both the Jira value mapping for the category field,
        and the related ``ResourceTypeMapping`` object describing
        the Redmine and Jira resource types respectively involved
        in the mapping.

        :param category: Issue category
        :param project_id: ID of the project the issue belongs to
        :return: A tuple containing both the jira value mapping for the
                 category and the related ``ResourceTypeMapping`` object
        """
        return self._get_resource_mapping(category, project_id=project_id,
                                          include_type_mapping=True)

    def _save_estimated_hours(self, estimated_hours, issue_export):
        """
        Save issue estimated hours in the export dictionary.

        :param estimated_hours: Issue estimated hours
        :param issue_export: Single issue export dictionary
        """
        issue_export['originalEstimate'] = \
            self._get_estimated_hours_mapping(estimated_hours)

    @staticmethod
    def _get_estimated_hours_mapping(estimated_hours):
        """
        Get the Jira value mapping for the estimated hours field.

        :param estimated_hours: Issue estimated hours
        :return: Jira value mapping for the estimated hours
        """
        return duration_isoformat(timedelta(hours=estimated_hours))

    def _save_custom_fields(self, custom_fields, project_id, issue_export):
        """
        Save issue custom fields to export dictionary.

        :param custom_fields: Issue custom fields
        :param project_id: ID of the project the issue belongs to
        :param issue_export: Single issue export dictionary
        """
        for custom_field in custom_fields:
            custom_field_def = self._issue_custom_fields[custom_field.id]

            field_name = self._get_custom_field_mapping(custom_field)

            format_mapping = ISSUE_CUSTOM_FIELD_TYPE_MAPPINGS[
                custom_field_def.field_format]

            field_type = \
                format_mapping['multiple'] \
                if getattr(custom_field_def, 'multiple', False) \
                else format_mapping['single']

            value = self._get_custom_field_value_mapping(custom_field,
                                                         project_id)

            custom_field_dict = {
                'fieldName': field_name,
                'fieldType': field_type,
                'value': value
            }

            issue_export.setdefault('customFieldValues', []) \
                        .append(custom_field_dict)

    def _get_custom_field_mapping(self, custom_field):
        """
        Get the Jira value mapping for the issue custom field.

        :param custom_field: Issue custom field
        :return: Jira value mapping for the custom field
        """
        return self._get_resource_mapping(custom_field)

    def _get_custom_field_value_mapping(self, custom_field, project_id):
        """
        Get the Jira value mapping for the custom field value.

        :param custom_field: Issue custom field
        :param project_id: ID of the project the issue belongs to
        :return: Jira value mapping for the custom field value
        """
        custom_field_def = self._issue_custom_fields[custom_field.id]
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
                        self._get_resource_mapping(user)
                        for user_id, user in self._users.items()
                        if user_id in user_ids
                    ]
                else:
                    user_id = int(redmine_value)
                    jira_value = self._get_resource_mapping(
                        self._users[user_id])
            elif custom_field_def.field_format == 'version':
                if getattr(custom_field_def, 'multiple', False):
                    version_ids = set(map(int, redmine_value))
                    jira_value = [
                        self._get_resource_mapping(version)
                        for version_id, version in
                        self._versions[project_id].items()
                        if version_id in version_ids
                    ]
                else:
                    version_id = int(redmine_value)
                    jira_value = self._get_resource_mapping(
                        self._versions[project_id][version_id])
            elif custom_field_def.field_format in ['link', 'list']:
                pass
            else:
                raise NotImplementedError(
                    "'{}' field format not supported!"
                    .format(custom_field_def.field_format))

        return jira_value

    def _save_watchers(self, watchers, issue_export):
        """
        Save issue watchers to export dictionary.

        :param watchers: Issue watchers
        :param issue_export: Single issue export dictionary
        """
        for watcher in watchers:
            user = self._get_resource_mapping(self._users[watcher.id])

            issue_export.setdefault('watchers', []) \
                        .append(user)

    def _save_attachments(self, attachments, issue_export):
        """
        Save issue attachments to export dictionary.

        :param attachments: Issue attachments
        :param issue_export: Single issue export dictionary
        """
        for attachment in attachments:
            attacher = self._get_resource_mapping(
                self._users[attachment.author.id])

            attachment_dict = {
                "name": attachment.filename,
                "attacher": attacher,
                "created": attachment.created_on.isoformat(),
                "uri": attachment.content_url,
                "description": attachment.description
            }

            issue_export.setdefault('attachments', []) \
                        .append(attachment_dict)

    def _save_journals(self, journals, issue_export):
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
        :param issue_export: Single issue export dictionary
        """
        for journal in journals:
            # If there's a user note in the journal item...
            if getattr(journal, 'notes', None):
                self._save_journal_notes(journal, issue_export)

    def _save_journal_notes(self, journal, issue_export):
        """
        Save issue journal notes to export dictionary.

        :param journal: Issue journal item
        :param issue_export: Single issue export dictionary
        """
        author = self._get_resource_mapping(self._users[journal.user.id])

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

    @staticmethod
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

    def _get_resource_mapping(self, resource, resource_type=None,
                              project_id=None, include_type_mapping=False):
        """
        For each jira resource type mapped by the type of the given Redmine
        resource instance, this method finds a jira resource value.

        By default the type of the Redmine resource instance is guessed from
        its class, but can be explicitly defined via the ``resource_type``
        parameter.

        For each resource type mapping the method attempts to find a
        user-defined value mapping in the configuration settings first,
        falling back to value mappings dynamically defined by the final
        user at runtime.

        New dynamic value mappings are defined when no value mapping is found
        among both static and dynamic value mappings. In that case the final
        user is prompted to define one at runtime; furthermore, he may also be
        prompted to choose a jira resource type mapping, if the current Redmine
        resource type is mapped to more than one jira resource type.

        :param resource: Resource instance
        :param resource_type: Internal Redmine resource type class.
                              If not provided the Redmine resource type class
                              is dynamically derived from the RedmineLib
                              resource instance class name.
        :param project_id: ID of the project the resource value is bound to,
                           if any.
        :param include_type_mapping: If ``True`` the method return also the
                                     ``ResourceTypeMapping`` tuple-like object,
                                     which store references to the Redmine and
                                     Jira resource types respectively involved
                                     in the mapping. Default is ``False``.
        :return: The mapped jira resource value or, if ``include_type_mapping``
                 is set to ``True``, a  tuple containing both the related
                 ``ResourceTypeMapping`` object and the mapped jira resource
                 value
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
            {k.jira: v
             for k, v in RESOURCE_TYPE_IDENTIFYING_FIELD_MAPPINGS.items()
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
            redmine_resource_value = \
                getattr(resource, field_mapping.redmine.key)

            # Try to get the Jira resource value from mappings
            # statically defined in configuration settings
            static_resource_value_mappings = \
                getattr(config, resource_type_mapping_setting_name, {})

            if project_id is not None:
                # Use project identifier instead of its internal ID
                # to fetch per-project resource value mappings inside
                # user-defined configuration files.
                project_identifier = self._projects[project_id].identifier
                static_resource_value_mappings = \
                    static_resource_value_mappings.get(project_identifier, {})

            jira_resource_value = \
                static_resource_value_mappings.get(
                    redmine_resource_value, None)

            if jira_resource_value is not None:
                # A Jira resource value mapping has been found. Exit!
                break

        if jira_resource_value is None:
            # Search for a dynamically user-defined value mapping
            for jira_resource_type, field_mapping in \
                    jira_resource_type_field_mappings.items():
                # Build ResourceTypeMapping object
                resource_type_mapping = \
                    ResourceTypeMapping(redmine_resource_type,
                                        jira_resource_type)

                # Get the Redmine resource value
                redmine_resource_value = getattr(resource,
                                                 field_mapping.redmine.key)

                # Try to get the Jira resource value from mappings
                # dynamically defined at runtime
                if project_id is None:
                    jira_resource_value = \
                        self._resource_value_mappings.get(
                            (redmine_resource_value, resource_type_mapping),
                            None)
                else:
                    jira_resource_value = \
                        self._resource_value_mappings.get(
                            (project_id,
                             redmine_resource_value, resource_type_mapping),
                            None)

                if jira_resource_value is not None:
                    # A Jira resource value mapping has been found. Exit!
                    break

        if jira_resource_value is None:
            # No value mapping found!

            # If there not exist dynamically user-defined value mappings...
            if not self._resource_value_mappings:
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
                    {i + 1: jrt for i, jrt in
                     enumerate(jira_resource_type_field_mappings)}

                for k, v in static_jira_resource_type_choices.items():
                    # Strip 'Jira' prefix from class name
                    humanized_jira_resource_type = \
                        humanize(underscore(v.__name__[len('Jira'):]))

                    click.echo("{:d}) {}"
                               .format(k, humanized_jira_resource_type))

                click.echo()

                choice = click.prompt(
                    "Choose a target Jira resource type",
                    prompt_suffix=": ",
                    type=click.IntRange(
                        1, len(static_jira_resource_type_choices)))

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
                self._resource_value_mappings[
                    (redmine_resource_value,
                     resource_type_mapping)] = jira_resource_value
            else:
                self._resource_value_mappings[
                    (project_id,
                     redmine_resource_value,
                     resource_type_mapping)] = jira_resource_value

        if include_type_mapping:
            return jira_resource_value, resource_type_mapping
        else:
            return jira_resource_value
