# -*- coding: utf-8 -*-

"""Utilities for manipulating Redmine resources text contents."""

from __future__ import absolute_import

from contextlib import closing
from io import StringIO

from lxml import etree as et

from redmine2jira import config

import unicodedata
import re

# In the regular expressions below the following is a white space character that isn't new line or carriage return
# [^\S\r\n]
regExEmail = re.compile("<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>", re.DOTALL)
regExCodeStart = re.compile("\n?[^\S\r\n]*<pre(\s*lang\s*=\s*(\w+)\s*)?>[\n\s]*<code>", re.DOTALL | re.IGNORECASE)
regExCodeEnd = re.compile("\n?[^\S\r\n]*</code>\s*</pre>", re.DOTALL | re.IGNORECASE)
regExPreFormattedStart = re.compile("\n?[^\S\r\n]*<pre>", re.DOTALL | re.IGNORECASE)
regExPreFormattedEnd = re.compile("</pre>\s*\n?", re.DOTALL | re.IGNORECASE)
regExPreFormattedEndAtFileEnd = re.compile("\n\np. \n", re.DOTALL | re.IGNORECASE)
regExChar01 = re.compile("\x01", re.DOTALL | re.IGNORECASE)
regLtThan = re.compile("<(?![/]?notextile)", re.DOTALL | re.IGNORECASE)  # Replace <  if it isn't followed by the word notextile or /notextile
regGtThan = re.compile("(?<!notextile)>", re.DOTALL | re.IGNORECASE)  # Replace >  if it isn't preceded by the word notextile
regAmpersand = re.compile("&", re.DOTALL | re.IGNORECASE)
regDoubleQuote = re.compile('"', re.DOTALL | re.IGNORECASE)
regSingleQuote = re.compile("'", re.DOTALL | re.IGNORECASE)


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

        # Make e-mail addresses acceptable
        replaced_text = regExEmail.sub("&lt;\1&gt;", text)

        # Turn non textile code blocks into valid textile
        replaced_text = regExCodeStart.sub("\nbc.. \n", replaced_text)
        replaced_text = regExCodeEnd.sub("\n\np. \n", replaced_text)

        # Turn non textile <pre> and </pre>into valid textile
        replaced_text = regExPreFormattedStart.sub("\n\npre.. ", replaced_text)
        replaced_text = regExPreFormattedEnd.sub("\n\np. \n", replaced_text)

        # deal with closing pre formatted block if it's at the end of the file
        replaced_text = regExPreFormattedEndAtFileEnd.sub("\n\np. .\n", replaced_text)

        # Character 1 as seen this in data and xhtml2confluence_wiki doesn't like it
        replaced_text = regExChar01.sub("", replaced_text)

        replaced_text = regLtThan.sub("&lt;", replaced_text)
        replaced_text = regGtThan.sub("&gt;", replaced_text)
        replaced_text = regAmpersand.sub("&amp;", replaced_text)
        replaced_text = regDoubleQuote.sub("&quot;", replaced_text)
        replaced_text = regSingleQuote.sub("&apos;", replaced_text)

        temp_text = textile(replaced_text);
        confluence_wiki = xhtml2confluence_wiki(temp_text)
    elif config.REDMINE_TEXT_FORMATTING == 'markdown':
        from markdown import markdown

        temp_text = markdown(text);
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

# rte-xhtml2wiki.xsl from http://www.amnet.net.au/~ghannington/confluence/wikifier/rt/rte-xhtml2wiki.xsl
    with closing(StringIO()) as xml:
        xml.write(u'<body xmlns="http://www.w3.org/1999/xhtml">\n')
        xml.write(xhtml)
        xml.write(u'\n</body>')
        xml_string = xml.getvalue()
        dom = et.fromstring(xml_string)
        xsl_stream = resource_stream(__name__, 'rte-xhtml2wiki.xsl')
        xsl = et.parse(xsl_stream)
        transform = et.XSLT(xsl)
        confluence_wiki = unicode(transform(dom))

    return confluence_wiki
