# -*- coding: utf-8 -*-

"""Utilities for manipulating Redmine resources text contents."""

from __future__ import absolute_import

from contextlib import closing
from io import StringIO

from lxml import etree as et

from redmine2jira import config


def text2confluence_wiki(text):
    """
    Convert a Redmine resource text content to Confluence Wiki notation.

    :param text: Plain text or formatted text using Textile or Markdown
                 markup languages
    :return: Text in Confluence Wiki notation
    """
    confluence_wiki = None

    if config.REDMINE_TEXT_FORMATTING == 'textile':
        from textile import textile

        confluence_wiki = xhtml2confluence_wiki(textile(text))
    elif config.REDMINE_TEXT_FORMATTING == 'markdown':
        from markdown import markdown

        confluence_wiki = xhtml2confluence_wiki(markdown(text))
    elif config.REDMINE_TEXT_FORMATTING != 'none':
        raise NotImplementedError(
            "The '{}' text formatting is not supported by Redmine!"
            .format(config.REDMINE_TEXT_FORMATTING))

    return confluence_wiki


def xhtml2confluence_wiki(xhtml):
    """
    Convert an XHTML fragment to Confluence Wiki notation.

    :param xhtml: UTF-8 encoded XHTML 1.x fragment
    :return: Confluence Wiki fragment
    """
    from pkg_resources import resource_stream
    from xml.sax.saxutils import escape

    with closing(StringIO()) as xml:
        xml.write('<body xmlns="http://www.w3.org/1999/xhtml">\n')
        xml.write(escape(xhtml))
        xml.write('\n</body>')
        xml_string = xml.getvalue()
        dom = et.fromstring(xml_string)
        xsl_stream = resource_stream(__name__, 'rte-xhtml2wiki.xsl')
        xsl = et.parse(xsl_stream)
        transform = et.XSLT(xsl)
        confluence_wiki = str(transform(dom), encoding='utf-8')

    return confluence_wiki
