# -*- coding: utf-8 -*-

"""Console script for redmine_xls_export2jira."""

from __future__ import absolute_import

import mmap
import os.path
import tempfile
import shutil

import click
import magic
import xlrd

from datetime import datetime
from functools import reduce
from glob import glob
from operator import and_, or_, itemgetter
from zipfile import ZipFile, ZIP_DEFLATED

from click_default_group import DefaultGroup
from redminelib import Redmine
from six import text_type
from six.moves.urllib.parse import unquote
from tabulate import tabulate

from redmine_xls_export2jira import config


redmine = Redmine(config.REDMINE_URL, key=config.REDMINE_API_KEY)


def scan_export_file_system(file_obj):
    """
    Scan the full export file system which is relative
    to the export main MS Excel file, provided as the only input parameter.
    The file system may be set up manually by the users or, more commonly,
    be automatically extracted from the Zip archive provided alternatively
    as input file.
    In both scenarios the scan of the export file system is always driven by
    the specific content of the export main MS Excel file.

    TODO Move in some more specific place
    The format of the that file is BIFF
    (Binary Interchange File Format),
    used by MS Excel versions from 97 to 2007.

    The main file contains all the exported issues main data,
    including at least standard fields and custom fields values;
    it may also contain, depending on the export options,
    the following information:

    - Issue relations
    - Watchers list
    - Journal entries
    - Attachments filename list

    :param file_obj: Export main MS Excel file object
    :return:
    """

    # Open a memory-mapped file object from the OS file descriptor
    # of the input file object

    with mmap.mmap(file_obj.fileno(), 0, access=mmap.ACCESS_READ) as mm_file:
        # Open workbook
        book = xlrd.open_workbook(file_contents=mm_file)
        # Get first (and only) sheet
        sheet = book.sheet_by_index(0)
        # Get column headers
        column_headers = [col.value for col in sheet.row(0)]

        file_basedir = os.path.dirname(file_obj.name)

        if config.EXPORT_MAIN_XLS_RELATIONS_COLUMN_NAME in column_headers:
            # TODO: Save issues relations
            click.echo("Relations found!")

        if config.EXPORT_MAIN_XLS_WATCHERS_COLUMN_NAME in column_headers:
            # TODO: Save issues watchers
            click.echo("Watchers found!")

        if config.EXPORT_MAIN_XLS_JOURNALS_COLUMN_NAME in column_headers:
            # TODO: Save issues journal
            if os.path.exists(
                os.path.join(file_basedir,
                             config.EXPORT_JOURNALS_ROOT_DIR)):
                click.echo("Journals as separated files found!")
            else:
                click.echo("Journals found!")

        if config.EXPORT_MAIN_XLS_ATTACHMENTS_COLUMN_NAME in column_headers:
            # TODO: Save issues attachments
            #       only if the directory dedicated to issue attachments exists
            #       in the same directory of the main MS Excel export file
            if os.path.exists(
                os.path.join(file_basedir,
                             config.EXPORT_ATTACHMENTS_ROOT_DIR)):
                click.echo("Attachments found!")
            else:
                click.echo("WARNING: The main export file contains issues "
                           "attachments information, but no attachment files "
                           "have been found.\n"
                           "WARNING. The issues attachment lists "
                           "will be ignored!")

        if os.path.exists(
            os.path.join(file_basedir,
                         config.EXPORT_STATUS_HISTORIES_FILENAME)):
            # TODO: Save issues status history
            click.echo("Status histories found!")

        # Get Redmine issue fields
        issue = redmine.issue.get(4870, include='children,attachments,'
                                                'relations,journals,watchers')

        for attr in [a for a in dir(issue)
                     if a not in ['attachments,children,custom_fields,'
                                  'journals,relations,time_entries,watchers']]:
            click.echo("{}: {}".format(attr, getattr(issue, attr, '')))

        if hasattr(issue, 'attachments'):
            click.echo("-----------")
            click.echo("Attachments")
            click.echo("-----------")

            for attachment in issue.attachments:
                for attr in dir(attachment):
                    click.echo("{}: {}"
                               .format(attr, getattr(attachment, attr, None)))


def extract_zip_archive(file_obj):
    """
    Extract the Zip archive export of the `Redmine XLS Export` plugin
    in a temporary directory.
    The Zip archive format is used by the plugin whenever multiple files
    need to be exported. That happens when in the export options
    the user decided to export the following issues related resources:

    - Journals (explicitly asked as separated files)
    - Attachments files
    - Status histories

    :param file_obj: Open file object
    :return:
    """

    with ZipFile(file_obj, mode='r', compression=ZIP_DEFLATED) as zip_file_obj:
        # Extract the Zip archive contents to a temporary directory
        timestamp_suffix = '_{:%Y%m%d_%H%M%S}'.format(datetime.now())
        temp_extract_dir = tempfile.mkdtemp(suffix=timestamp_suffix)

        try:
            zip_file_obj.extractall(path=temp_extract_dir)

            # Find the export main MS Excel file
            for path in glob(os.path.join(temp_extract_dir, '*.xls')):
                filename = os.path.basename(path)

                # In the archive root directory we may find up to
                # two MS Excel files: the export main MS Excel file,
                # which name is dynamically generated according to the
                # "Redmine XLS Export" plugin export options,
                # and the issues status histories optional file,
                # which name, instead, is well-known.
                if filename != config.EXPORT_STATUS_HISTORIES_FILENAME:
                    with open(path, mode='r') as export_main_file:
                        scan_export_file_system(export_main_file)
        finally:
            shutil.rmtree(temp_extract_dir)


def old_main(input, output):
    scan_export_file_system(input)
    mimetype = magic.from_buffer(input.read(), mime=True)

    if mimetype == 'application/vnd.ms-excel':
        scan_export_file_system(input)
    elif mimetype == 'application/zip':
        extract_zip_archive(input)
    else:
        raise click.BadArgumentUsage(
            "The input filename must be a "
            "BIFF MS Excel file (Excel 2007) or a Zip archive!")


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
@click.option('--active', 'user_status', flag_value=1, default=True,
              help="Filter active users")
@click.option('--locked', 'user_status', flag_value=3,
              help="Filter locked users")
def list_users(user_status):
    """List Redmine users."""

    users = None

    if user_status == 1:
        # Get Redmine active users
        users = redmine.user.all()
    elif user_status == 3:
        # Get Redmine locked users
        users = redmine.user.filter(status=3)

    _list_resources(users, sort_key='login', exclude_attrs=('created_on',))


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
