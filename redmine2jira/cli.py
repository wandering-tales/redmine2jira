# -*- coding: utf-8 -*-

"""Console script for redmine2jira."""

from __future__ import absolute_import

import click

from functools import reduce
from itertools import chain
from operator import and_, or_, itemgetter

from click_default_group import DefaultGroup
from redminelib import Redmine
from six import text_type
from six.moves.urllib.parse import unquote
from tabulate import tabulate

from redmine2jira import config


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

    click.echo("{:d} issues found!".format(len(issues)))

    issues_users = set()

    # Get users in users related issue custom fields
    users_related_issue_custom_fields_ids = \
        [cf.id for cf in redmine.custom_field.all()
         if cf['customized_type'] == 'issue' and
            cf['field_format'] == 'user']

    issues_users |= \
        reduce(or_,
               (set(cf['value']) if 'multiple' in dir(cf) else {cf['value']}
                for issue in issues
                for cf in getattr(issue, 'custom_fields', [])
                if cf['id'] in users_related_issue_custom_fields_ids))

    click.echo(issues_users)


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
                        click.echo("You may disable the "
                                   "ISSUE_ID_FILTER_AVAILABLE flag in the "
                                   "configuration and, eventually, "
                                   "disable the previous check via the "
                                   "CHECK_ISSUE_ID_FILTER_AVAILABILITY flag.")

                # Filter the resource set with the issue ID's in the filter
                issues = [issue for issue in issues
                          if issue.id in issues_ids_filter]

    # FIXME: Debug
    if len(issues) == 1:
        for issue in issues:
            for a, v in list(issue):
                click.echo("{}: {}".format(a, v))

    return issues


def _get_all_issues():
    """
    Fetch all issues from Redmine.

    :return: All issues
    """
    return redmine.issue.all()


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
        :return: Project full name
        """
        if full_name:
            full_name = "{} / {}".format(project['name'], full_name)
        else:
            full_name = project['name']

        if hasattr(project, 'parent'):
            parent = redmine.project.get(project['parent']['id'])
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
                    exclude_attrs={'default_status': lambda r, v: v['name']})


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
    scalar_attributes = [set((a for a, v in list(resource) if v is not None))
                         for resource in resource_set]

    # Compute a common subset of all the scalar attributes
    common_scalar_attributes = reduce(and_, scalar_attributes)

    # Exclude specific attributes
    if exclude_attrs:
        common_scalar_attributes -= set(exclude_attrs)

    # Declare base attributes for all resource types
    base_attributes = ['id']

    if sort_key in common_scalar_attributes:
        base_attributes.append(sort_key)

    # Sort the attributes by name,
    # excluding 'id' and 'name' attributes:
    # those will be inserted, respectively,
    # at the beginning of the attribute list.
    attributes = \
        base_attributes + \
        sorted(common_scalar_attributes - frozenset(base_attributes))

    def _format(key, resource):
        value = getattr(resource, key)

        if format_dict and key in format_dict:
            return format_dict[key](resource, value)

        return text_type(value)

    # Build a "table" (list of dictionaries)
    # from all the resource instances,
    # using only the calculated attributes
    resource_table = sorted(({a: _format(a, resource) for a in attributes}
                             for resource in resource_set),
                            key=itemgetter(sort_key))

    # Pretty print the resource table
    # using the dictionary keys as headers
    click.echo(tabulate(resource_table, headers="keys"))
