#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `redmine_xls_export2jira` package."""


import unittest
from click.testing import CliRunner

from redmine_xls_export2jira import cli


class TestRedmineXlsExport2Jira(unittest.TestCase):
    """Tests for `redmine_xls_export2jira` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        # TODO: Temporarily disable CLI tests
        # result = runner.invoke(cli.main)
        # assert result.exit_code == 0
        # assert 'redmine_xls_export2jira.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
