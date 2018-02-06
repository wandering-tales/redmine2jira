# -*- coding: utf-8 -*-

"""Console script for redmine2jira."""

from __future__ import absolute_import

from functools import reduce
from itertools import chain
from operator import and_, itemgetter

import click

from click_default_group import DefaultGroup
from inflection import humanize, underscore
from redminelib import Redmine
from redminelib.resultsets import ResourceSet
from six import text_type
from six.moves.urllib.parse import unquote
from tabulate import tabulate

from redmine2jira import config


# Redmine and Jira resource type field mappings
#
# NOTE: A Redmine resource type may corresponds
#       to one or more Jira resource types.
RESOURCE_TYPE_FIELD_MAPPINGS = {
    'user': {
        'user': ('login', 'username')
    },
    'group': {
        'user': ('name', 'username'),
        'user1': ('name', 'username'),
        'user2': ('name', 'username')
    },
    'project': {
        'project': ('identifier', 'key')
    },
    'tracker': {
        'issue_type': ('name', 'name')
    },
    'issue_status': {
        'issue_status': ('name', 'name')
    },
    'issue_priority': {
        'issue_priority': ('name', 'name')
    },
    'issue_category': {
        'component': ('name', 'name'),
        'label': ('name', 'name')
    }
}

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
def export_issues(output, query_string):
    """Export Redmine issues."""

    if query_string:
        issues = _get_issues_by_filter(query_string)
    else:
        issues = _get_all_issues()

    click.echo("{:d} issue{} found!"
               .format(len(issues), "s" if len(issues) > 1 else ""))

    # Get all Redmine users, groups, projects, trackers, issue statuses,
    # issue priorities and store them by ID

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

    # Get all Redmine issue categories and store them by project ID
    # and, for each project ID, by issue category ID
    issue_categories = {
        project.id: {
            issue_category.id: issue_category
            for issue_category in project.issue_categories
        }
        for project in projects.values()
    }

    referenced_users_ids = _export_issues(issues, users, groups,
                                          projects, trackers, issue_statuses,
                                          issue_priorities, issue_categories)

    click.echo("Issues exported in '{}'!".format(output.name))

    _list_unmapped_referenced_users(users, referenced_users_ids)

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


def _export_issues(issues, users, groups, projects, trackers,
                   issue_statuses, issue_priorities, issue_categories):
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
    - Issue categories (on a per-project basis)

    Though users references can be found both in the issues properties (author,
    assignee, users related custom fields) and related child resources
    (watchers, attachments, journal entries, time entries), groups references
    can only be found in the "assignee" field.

    :param issues: Issues to export
    :param users: All Redmine users
    :param groups: All Redmine groups
    :param projects: All Redmine projects
    :param trackers: All Redmine trackers
    :param issue_statuses: All Redmine issue statuses
    :param issue_priorities: All Redmine issue priorities
    :param issue_categories: All Redmine issue categories
                             on a per-project basis
    :return: ID's of users referenced in the issues being exported
    """
    # Get users related issue custom field ID's
    users_related_issue_custom_field_ids = \
        {cf.id for cf in redmine.custom_field.all()
         if cf.customized_type == 'issue' and cf.field_format == 'user'}

    referenced_users_ids = set()
    resource_value_mappings = dict()

    for issue in issues:
        # The issue project must be saved before everything else.
        # That's because all the issues entities must be children of a project
        # entity in the export dictionary.
        _save_project(projects[issue.project.id], resource_value_mappings)

        # Save required standard fields
        _save_id(issue.id)
        _save_subject(issue.subject)
        _save_author(issue.author, referenced_users_ids)
        _save_tracker(trackers[issue.tracker.id],
                      resource_value_mappings)
        _save_issue_status(issue_statuses[issue.status.id],
                           resource_value_mappings)
        _save_issue_priority(issue_priorities[issue.priority.id],
                             resource_value_mappings)
        _save_creation_date(issue.created_on)
        _save_modification_date(issue.updated_on)

        # Save optional standard fields
        if hasattr(issue, 'description'):
            _save_description(issue.description)

        if hasattr(issue, 'assigned_to'):
            # If the issue assignee is a Redmine group...
            if config.ALLOW_ISSUE_ASSIGNMENT_TO_GROUPS and \
               issue.assigned_to.id in groups:
                assignee = groups[issue.assigned_to.id]
            else:
                assignee = users[issue.assigned_to.id]

                referenced_users_ids.add(issue.assigned_to.id)

            _save_assignee(assignee, resource_value_mappings)

        if hasattr(issue, 'category'):
            category = issue_categories[issue.project.id][issue.category.id]

            _save_issue_category(category, issue.project.id,
                                 resource_value_mappings)

        if hasattr(issue, 'estimated_hours'):
            _save_estimated_hours(issue.estimated_hours)

        # Save custom fields
        if hasattr(issue, 'custom_fields'):
            _save_custom_fields(issue.custom_fields,
                                users_related_issue_custom_field_ids,
                                referenced_users_ids)

        # Save related resources
        _save_watchers(issue.watchers, referenced_users_ids)
        _save_attachments(issue.attachments, referenced_users_ids)
        _save_journals(issue.journals, referenced_users_ids)
        _save_time_entries(issue.time_entries, referenced_users_ids)

    return referenced_users_ids


def _save_project(project, resource_value_mappings):
    """
    Save issue project in the export dictionary.

    :param project: Issue project
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    """
    project_value_mapping = \
        _get_resource_value_mapping(project, resource_value_mappings)

    # TODO Set value in the export dictionary
    click.echo("Project: {}".format(project_value_mapping))


def _save_id(issue_id):
    """
    Save issue ID in the export dictionary as "external ID".

    :param issue_id: Issue ID
    """
    # TODO Set value in the export dictionary
    click.echo("ID: {}".format(issue_id))


def _save_subject(subject):
    """
    Save issue subject in the export dictionary.

    :param subject: Issue subject
    """
    # TODO Set value in the export dictionary
    click.echo("Subject: {}".format(subject))


def _save_author(author, referenced_users_ids):
    """
    Save issue author in the export dictionary.

    :param author: Issue author
    :param referenced_users_ids: Set of ID's of referenced users
                                 found so far in the issue resource set
    """
    referenced_users_ids.add(author.id)

    # TODO Set value in the export dictionary
    click.echo("Author: {}".format(author))


def _save_tracker(tracker, resource_value_mappings):
    """
    Save issue tracker in the export dictionary.

    :param tracker: Issue tracker
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    """
    tracker_value_mapping = \
        _get_resource_value_mapping(tracker, resource_value_mappings)

    # TODO Set value in the export dictionary
    click.echo("Tracker: {}".format(tracker_value_mapping))


def _save_issue_status(issue_status, resource_value_mappings):
    """
    Save issue status in the export dictionary.

    :param issue_status: Issue status
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    """
    issue_status_value_mapping = \
        _get_resource_value_mapping(issue_status, resource_value_mappings)

    # TODO Set value in the export dictionary
    click.echo("Issue status: {}".format(issue_status_value_mapping))


def _save_issue_priority(issue_priority, resource_value_mappings):
    """
    Save issue priority in the export dictionary.

    :param issue_priority: Issue priority
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    """
    issue_priority_value_mapping = \
        _get_resource_value_mapping(issue_priority, resource_value_mappings,
                                    resource_type="issue_priority")

    # TODO Set value in the export dictionary
    click.echo("Issue priority: {}".format(issue_priority_value_mapping))


def _save_creation_date(creation_date):
    """
    Save issue creation date in the export dictionary.

    :param creation_date: Issue creation date
    """
    # TODO Set value in the export dictionary
    click.echo("Created on: {:%Y-%m-%d}".format(creation_date))


def _save_modification_date(modification_date):
    """
    Save issue modification date in the export dictionary.

    :param modification_date: Issue modification date
    """
    # TODO Set value in the export dictionary
    click.echo("Updated on: {:%Y-%m-%d}".format(modification_date))


def _save_description(description):
    """
    Save issue description in the export dictionary.

    :param description: Issue description
    """
    # TODO Set value in the export dictionary
    click.echo("Description: {}".format(description))


def _save_assignee(assignee, resource_value_mappings):
    """
    Save issue assignee in the export dictionary.
    By default the assignee is a user, but if the
    "Allow issue assignment to groups" setting is
    enabled in Redmine the assignee may also be a
    group.

    :param assignee: Issue assignee, which may refer
                     either to a user or a group
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    """
    assignee_value_mapping = \
        _get_resource_value_mapping(assignee, resource_value_mappings)

    # TODO Set value in the export dictionary
    click.echo("Assignee: {}".format(assignee_value_mapping))


def _save_issue_category(issue_category, project_id, resource_value_mappings):
    """
    Save issue category in the export dictionary.

    :param issue_category: Issue category
    :param project_id: ID of the project the issue belongs to
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    """
    issue_category_value_mapping = \
        _get_resource_value_mapping(issue_category, resource_value_mappings,
                                    project_id=project_id)

    # TODO Set value in the export dictionary
    click.echo("Issue category: {}".format(issue_category_value_mapping))

    # TODO Save additional label to recognize the specific import


def _save_estimated_hours(estimated_hours):
    """
    Save issue estimated hours in the export dictionary.

    :param estimated_hours: Issue estimated hours
    """
    # TODO Set value in the export dictionary
    click.echo("Estimated hours: {}".format(estimated_hours))

    # TODO Calculate and save total time spent


def _save_custom_fields(custom_fields, users_related_issue_custom_field_ids,
                        referenced_users_ids):
    """
    Save issue custom fields to export dictionary.

    :param custom_fields: Issue custom fields
    :param users_related_issue_custom_field_ids: Set of ID's of all the users
                                                 related issue custom fields
    :param referenced_users_ids: Set of ID's of referenced users
                                 found so far in the issue resource set
    """
    for custom_field in (cf for cf in custom_fields
                         if cf.id in users_related_issue_custom_field_ids):
        referenced_users_ids |= \
            set(custom_field.value) \
            if getattr(custom_field, 'multiple', False) \
            else {custom_field.value}

        # TODO Set value in the export dictionary
        click.echo("Custom field: {}".format(custom_field))


def _save_watchers(watchers, referenced_users_ids):
    """
    Save issue watchers to export dictionary.

    :param watchers: Issue watchers
    :param referenced_users_ids: Set of ID's of referenced users
                                 found so far in the issue resource set
    """
    for watcher in watchers:
        referenced_users_ids.add(watcher.id)

        # TODO Set value in the export dictionary
        click.echo("Watcher: {}".format(watcher))


def _save_attachments(attachments, referenced_users_ids):
    """
    Save issue attachments to export dictionary.

    :param attachments: Issue attachments
    :param referenced_users_ids: Set of ID's of referenced users
                                 found so far in the issue resource set
    """
    for attachment in attachments:
        referenced_users_ids.add(attachment.author.id)

        # TODO Set value in the export dictionary
        click.echo("Attachment: {}".format(attachment))


def _save_journals(journals, referenced_users_ids):
    """
    Save issue journals to export dictionary.

    :param journals: Issue journals
    :param referenced_users_ids: Set of ID's of referenced users
                                 found so far in the issue resource set
    """
    for journal in journals:
        referenced_users_ids.add(journal.user.id)

        # TODO Set value in the export dictionary
        click.echo("Journal: {}".format(journal))


def _save_time_entries(time_entries, referenced_users_ids):
    """
    Save issue time entries to export dictionary.

    :param time_entries: Issue time entries
    :param referenced_users_ids: Set of ID's of referenced users
                                 found so far in the issue resource set
    """
    for time_entry in time_entries:
        referenced_users_ids.add(time_entry.user.id)

        # TODO Set value in the export dictionary
        click.echo("Time entry: {}".format(time_entry))


def _get_resource_value_mapping(resource, resource_value_mappings,
                                resource_type=None, project_id=None):
    """
    :param resource: Resource instance
    :param resource_value_mappings: Dictionary of the resource mappings
                                    dynamically defined at runtime
                                    by the final user
    :param project_id: ID of the project the resource value is bound to,
                       if any.
    :return: The Jira value for the resource
    """
    # Guess Redmine resource type by class name
    # unless explicitly specified
    redmine_resource_type = resource_type

    if not redmine_resource_type:
        redmine_resource_type = underscore(resource.__class__.__name__)

    redmine_resource_value = None
    jira_resource_type = None
    jira_resource_value = None
    field_mapping = None

    # Get all Jira resource types mapped by the the Redmine one.
    # Even though a Redmine resource type can be mapped
    # to more than one Jira resource type, user-defined
    # Redmine values have one-to-one mappings with Jira
    # ones: if a mapping exists the Jira resource type
    # is automatically guessed.
    current_resource_type_field_mappings = \
        RESOURCE_TYPE_FIELD_MAPPINGS[redmine_resource_type]

    # Search for a statically user-defined value mapping
    for jira_resource_type, field_mapping in \
            current_resource_type_field_mappings.items():
        # Dynamically compose resource type mapping setting name
        custom_mapping_setting_name = \
            'CUSTOM_REDMINE_{}_JIRA_{}_MAPPINGS'.format(
                redmine_resource_type.upper(),
                jira_resource_type.upper())

        # Get the Redmine resource value
        redmine_resource_value = getattr(resource, field_mapping[0])

        # Try to get the Jira resource value from mappings
        # statically defined in configuration settings
        static_resource_value_mappings = \
            getattr(config, custom_mapping_setting_name)

        if project_id is not None:
            static_resource_value_mappings = \
                static_resource_value_mappings.get(project_id, {})

        jira_resource_value = \
            static_resource_value_mappings.get(redmine_resource_value, None)

        if jira_resource_value is not None:
            # A Jira resource value mapping has been found. Exit!
            break

    if jira_resource_value is None:
        # Search for a dynamically user-defined value mapping
        for jira_resource_type, field_mapping \
                in current_resource_type_field_mappings.items():
            # Get the Redmine resource value
            redmine_resource_value = getattr(resource, field_mapping[0])

            # Try to get the Jira resource value from mappings
            # dynamically defined at runtime
            dynamic_resource_value_mapping = resource_value_mappings \
                .get(redmine_resource_type, {})\
                .get(jira_resource_type, {})

            if project_id is not None:
                dynamic_resource_value_mapping = \
                    dynamic_resource_value_mapping.get(project_id, {})

            jira_resource_value = dynamic_resource_value_mapping \
                .get(redmine_resource_value, None)

            if jira_resource_value is not None:
                # A Jira resource value mapping has been found. Exit!
                break

    if jira_resource_value is None:
        # No value mapping found!

        # If there not exist dynamically user-defined value mappings...
        if not any(True for jrt in resource_value_mappings.values()
                   for _ in jrt):
            click.echo()
            click.echo("-" * len(MISSING_RESOURCE_MAPPINGS_MESSAGE))
            click.echo(MISSING_RESOURCE_MAPPINGS_MESSAGE)
            click.echo("-" * len(MISSING_RESOURCE_MAPPINGS_MESSAGE))

        # If the Redmine resource type can be mapped
        # to more than one Jira resource types...
        if len(current_resource_type_field_mappings.keys()) > 1:
            # ...prompt user to choose one
            click.echo(
                "Missing value mapping for Redmine {} '{}'."
                .format(humanize(redmine_resource_type).lower(),
                        redmine_resource_value))
            click.echo("A Redmine '{}' can be mapped with one of the "
                       "following Jira resource types:"
                       .format(humanize(redmine_resource_type)))
            click.echo()

            static_jira_resource_type_choices = \
                {i + 1: jrt
                 for i, jrt in enumerate(current_resource_type_field_mappings)}

            for k, v in static_jira_resource_type_choices.items():
                click.echo("{:d}) {}".format(k, humanize(v)))

            click.echo()

            choice = click.prompt(
                "Choose a target Jira resource type",
                prompt_suffix=": ",
                type=click.IntRange(1, len(static_jira_resource_type_choices)))

            jira_resource_type = static_jira_resource_type_choices[choice]

        click.echo()

        jira_resource_value = click.prompt(
            "[Redmine {} {}{}Jira {} {}] {}"
            .format(humanize(redmine_resource_type),
                    field_mapping[0],
                    MISSING_RESOURCE_MAPPING_PROMPT_SUFFIX,
                    humanize(jira_resource_type),
                    field_mapping[1],
                    redmine_resource_value),
            prompt_suffix=MISSING_RESOURCE_MAPPING_PROMPT_SUFFIX)

        # Setting dictionary key aliases
        rrt = redmine_resource_type
        jrt = jira_resource_type
        rrv = redmine_resource_value

        resource_value_mappings.setdefault(rrt, {}) \
                               .setdefault(jrt, {})[rrv] = jira_resource_value

    return jira_resource_value


def _list_unmapped_referenced_users(users, referenced_users_ids):
    """
    Print in a table fashion all the users not explicitly mapped to specific
    Jira users, via the CUSTOM_USERS_MAPPINGS setting. The purpose is to warn
    the final user to create them in the target Jira instance before importing
    the issues.

    :param users: All Redmine users
    :param referenced_users_ids: ID's of Redmine users referenced
                                 in issues being exported
    """
    # Retrieve all the Redmine users referenced in the issues being
    # exported, excluding the ones that have been explicitly mapped
    # to Jira users.
    # The purpose of this list is to warn the final user to check their
    # existence in the target Jira instance: if the final user willingly
    # mapped a Redmine user to a Jira one obviously we need to exclude
    # it from the list.
    unmapped_referenced_users = \
        [v for k, v in users.items()
         if k in referenced_users_ids and
            v.login not in config.CUSTOM_REDMINE_USER_JIRA_USER_MAPPINGS]

    if unmapped_referenced_users:
        click.echo("Loading users referenced in the exported issues...")
        click.echo()

        _list_resources(unmapped_referenced_users,
                        sort_key='login',
                        exclude_attrs=('id', 'created_on', 'last_login_on'))

        click.echo()
        click.echo("No static mappings have been defined for them via the "
                   "CUSTOM_USERS_MAPPINGS setting.")
        click.echo("Ensure the above users already exist in your "
                   "Jira instance before starting the import.")


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


@list_resources.command('custom_fields')
def list_custom_fields():
    """List Redmine custom fields."""

    custom_fields = redmine.custom_field.all()

    _list_resources(custom_fields, sort_key='name')


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
