<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xhtml="http://www.w3.org/1999/xhtml"
  xmlns:lookup="http://www.fundi.com.au/">

<!--

XSLT 1.0 stylesheet.

Transforms HTML copied from the Confluence 4 rich text editor (RTE) -
that has been made well-formed by appending end tags to empty elements
(such as br, hr, and img), and wrapping in a root element - into wiki markup.

Last updated 2012-07-07.

Developed by Graham Hannington <graham_hannington@fundi.com.au>
(Confluence user; no other affiliation with Atlassian).

Distributed under the BSD 2-Clause license
(also known as the Simplified BSD license):

Copyright (c) 2012, Fundi Software.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

-  Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
-  Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 -->

  <xsl:output method="text"/>

  <xsl:strip-space elements="xhtml:body xhtml:div xhtml:table xhtml:tbody xhtml:tr xhtml:ol xhtml:ul"/>
  <xsl:preserve-space elements="xhtml:p"/>

  <xsl:variable name="spaces" select="'                                                            '"/>
  <xsl:variable name="indentStep" select="2"/>

  
  <xsl:template match="/*">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Headings -->

  <xsl:template match="xhtml:h1 | xhtml:h2 | xhtml:h3 | xhtml:h4 | xhtml:h5 | xhtml:h6">
    <xsl:choose>
      <xsl:when test="not(parent::*=/* and position() = 1)"><xsl:text>&#xa;</xsl:text></xsl:when>
    </xsl:choose>
    <xsl:value-of select="local-name(.)"/>
    <xsl:text>. </xsl:text>
    <xsl:apply-templates/>
    <xsl:text>&#xa;</xsl:text>
  </xsl:template>

  <!-- Text effects -->

  <xsl:template match="xhtml:strong | xhtml:b">
    <xsl:text>*</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>*</xsl:text>
  </xsl:template>

  <!-- Emphasis and italics -->
  <xsl:template match="xhtml:em | xhtml:i">
    <xsl:choose>
      <!-- Previous node is a text node that does not end in whitespace: we are emphasizing or italicizing part of a word -->
      <xsl:when test="preceding-sibling::text()[not(normalize-space(substring(., string-length(.))) = '')]">
        <xsl:text>{_}</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>_</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:apply-templates/>
    <xsl:text>_</xsl:text>
  </xsl:template>

  <!-- Citation -->
  <xsl:template match="xhtml:cite">
    <xsl:text>??</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>??</xsl:text>
  </xsl:template>

  <!-- Strikethrough -->
  <xsl:template match="xhtml:s | xhtml:del | xhtml:span[@style='text-decoration: line-through;']">
    <xsl:text>-</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>-</xsl:text>
  </xsl:template>

  <!-- Underlined -->
  <xsl:template match="xhtml:u">
    <xsl:text>+</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>+</xsl:text>
  </xsl:template>

  <!-- Superscript -->
  <xsl:template match="xhtml:sup">
    <xsl:text>^</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>^</xsl:text>
  </xsl:template>

  <!-- Subscript -->
  <xsl:template match="xhtml:sub">
    <xsl:text>~</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>~</xsl:text>
  </xsl:template>

  <!-- Code -->
  <xsl:template match="xhtml:code">
    <xsl:text>{{</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>}}</xsl:text>
  </xsl:template>

  <!-- Preformatted -->
  <xsl:template match="xhtml:pre">
    <xsl:if test="parent::*=/*">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
    <xsl:text>{noformat}&#xa;</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>&#xa;{noformat}&#xa;</xsl:text>
    <xsl:if test="parent::*=/*">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
  </xsl:template>

  <!-- Quote -->
  <xsl:template match="xhtml:blockquote">
    <xsl:if test="parent::*=/*">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
    <xsl:text>{quote}&#xa;</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>{quote}</xsl:text>
    <xsl:if test="parent::*=/*">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
  </xsl:template>

  <!-- Color -->
  <xsl:template match="xhtml:span[contains(@style,'color: rgb')]">
    <xsl:text>{color:#</xsl:text>
    <xsl:variable name="r" select="substring-before(substring-after(@style,'rgb('),',')"/>
    <xsl:variable name="g" select="substring-before(substring-after(substring-after(@style,'rgb('),','),',')"/>
    <xsl:variable name="b" select="substring-before(substring-after(substring-after(substring-after(@style,'rgb('),','),','),')')"/>
    <xsl:call-template name="decimal2hex2digits">
        <xsl:with-param name="decimal" select="$r"/>
      </xsl:call-template>
    <xsl:call-template name="decimal2hex2digits">
        <xsl:with-param name="decimal" select="$g"/>
    </xsl:call-template>
    <xsl:call-template name="decimal2hex2digits">
        <xsl:with-param name="decimal" select="$b"/>
      </xsl:call-template>
    <xsl:text>}</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>{color}</xsl:text>
  </xsl:template>

  <!-- Text breaks -->

  <!-- Line break nested in pre element -->
  <xsl:template match="xhtml:br[ancestor::xhtml:pre]">
    <xsl:text>&#xa;</xsl:text>
  </xsl:template>

  <!-- Line break (that is not a descendant of a pre element, or a "bogus" line break inserted by the editor, or precedes a list) -->
  <xsl:template match="xhtml:br[not(ancestor::xhtml:pre) and not(@data-mce-bogus='1') and not(following-sibling::xhtml:ul) and not(following-sibling::xhtml:ol)]">
    <xsl:text>\\&#xa;</xsl:text>
  </xsl:template>

  <!-- Paragraph -->
  <xsl:template match="xhtml:p">
  <!-- Insert newline before paragraph, unless it is the first element of the document, or the first child of a list item or table cell -->
    <xsl:if test="not(.=parent::*/*[position()=1]) and not(.=parent::xhtml:li/*[1]) and not(.=parent::xhtml:td/*[1]) and not(.=parent::xhtml:th/*[1])">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:choose>
      <xsl:when test="parent::*[local-name()='th'] and .=parent::*/*[position()=last()]"/>
      <xsl:when test="parent::*[local-name()='td'] and .=parent::*/*[position()=last()]"/>
      <xsl:when test="parent::*[local-name()='li'] and .=parent::*/*[position()=last()]"/>
      <xsl:when test="(parent::*[local-name()='td'] or parent::*[local-name()='th']) and not(.=parent::*/*[position()=last()])">
        <xsl:text>\\ \\</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>&#xa;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Paragraph nested in list: insert explicit line breaks for all but first paragraph -->
  <xsl:template match="xhtml:li/xhtml:p[position() > 1]">
    <xsl:text>\\ \\&#xa;</xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Paragraph nested in list, where paragraph contains only a line break, and the paragraph is the last child of the list item -->
  <xsl:template match="xhtml:li/xhtml:p[xhtml:br and (count(*)=1)]"><xsl:text>\\</xsl:text></xsl:template>


  <!-- Paragraph nested inside body of section macro, but outside column: non-significant, delete -->
  <xsl:template match="xhtml:table[@class='wysiwyg-macro' and @data-macro-name='section']/xhtml:tbody/xhtml:tr/xhtml:td/xhtml:p"/>

  <!-- Horizontal rules -->
  <xsl:template match="xhtml:hr">
    <xsl:text>&#xa;----&#xa;</xsl:text>
  </xsl:template>

  <!-- Lists -->

  <!-- List items -->
  <xsl:template match="xhtml:ol/xhtml:li | xhtml:ul/xhtml:li">
    <!-- Insert newline before list item, unless it is the first item of a list that is the first child of a table cell -->
    <xsl:if test="not(.=parent::*/xhtml:li[1] and parent::*=parent::*/parent::xhtml:td/*[1])">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
    <!-- Insert the appropriate list item characters, depending on the ancestor lists -->
    <xsl:for-each select="ancestor::*[local-name(.)='ol' or local-name(.)='ul']">
      <xsl:choose>
        <xsl:when test="local-name(.)='ol'">#</xsl:when>
        <xsl:when test="local-name(.)='ul'">*</xsl:when>
      </xsl:choose>
    </xsl:for-each>
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Insert newline after list (that is not nested) -->
  <xsl:template match="xhtml:ol[parent::*=/*] | xhtml:ul[parent::*=/*]">
    <xsl:apply-templates/>
    <xsl:text>&#xa;</xsl:text>
  </xsl:template>

  <!-- Links -->

  <!-- Link to Confluence page -->
  <xsl:template match="xhtml:a[contains(@class, 'confluence-link') and @data-linked-resource-type = 'page']">
    <xsl:text>[</xsl:text>
    <xsl:if test="@data-linked-resource-default-alias">
      <xsl:value-of select="."/>
      <xsl:text>|</xsl:text>
    </xsl:if>
    <!-- The RTE HTML does not contain the space key as a discrete attribute. We must extract the space key from the href attribute. -->
    <!-- The RTE HTML does not indicate whether the destination page is in the same space as this page, or in a different space. -->
    <!-- Therefore, we always qualify the link with the space key, even if it is not required. -->
    <xsl:variable name="spaceKey" select="substring-before(substring-after(@data-mce-href, '/display/'), '/')"/>
    <xsl:value-of select="$spaceKey"/>
    <xsl:text>:</xsl:text>
    <xsl:choose>
      <xsl:when test="@data-linked-resource-default-alias">
        <xsl:value-of select="@data-linked-resource-default-alias"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="."/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:if test="@title">
      <xsl:text>|</xsl:text>
      <xsl:value-of select="@title"/>
    </xsl:if>
    <xsl:text>]</xsl:text>
  </xsl:template>

  <!-- User -->
  <xsl:template match="xhtml:a[@data-linked-resource-type = 'userinfo']">
    <xsl:text>[</xsl:text>
    <!-- If default link text is different from link contents, then specify custom link text -->
    <xsl:if test="not(@data-linked-resource-default-alias = normalize-space(.))">
      <xsl:value-of select="normalize-space(.)"/>
      <xsl:text>|</xsl:text>
    </xsl:if>
    <xsl:text>~</xsl:text>
    <xsl:value-of select="@data-username"/>
    <xsl:text>]</xsl:text>
  </xsl:template>

  <!-- Attachment -->
  <xsl:template match="xhtml:a[@data-linked-resource-type = 'attachment']">
    <xsl:text>[</xsl:text>
    <!-- If default link text is different from link contents, then specify custom link text -->
    <xsl:if test="not(@data-linked-resource-default-alias = normalize-space(.))">
      <xsl:value-of select="normalize-space(.)"/>
      <xsl:text>|</xsl:text>
    </xsl:if>
    <xsl:text>^</xsl:text>
    <xsl:value-of select="@data-linked-resource-default-alias"/>
    <xsl:text>]</xsl:text>
  </xsl:template>

  <!-- Web link -->
  <xsl:template match="xhtml:a">
    <xsl:text>[</xsl:text>
    <!-- If default link text is different from link contents, then specify custom link text -->
    <xsl:if test="not(@data-mce-href = normalize-space(.))">
      <xsl:value-of select="normalize-space(.)"/>
      <xsl:text>|</xsl:text>
    </xsl:if>
    <xsl:value-of select="@href"/>
    <xsl:text>]</xsl:text>
  </xsl:template>

  <!-- Tables -->

  <!-- Table data cell -->
  <xsl:template match="xhtml:td">
    <xsl:if test="position() = 1">
      <xsl:text>&#xa;|</xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:text>|</xsl:text>
  </xsl:template>

  <!-- Table header cell -->
  <xsl:template match="xhtml:th">
    <xsl:if test="position() = 1">
      <xsl:text>&#xa;||</xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:text>||</xsl:text>
  </xsl:template>

  <!-- Insert newline after table -->
  <xsl:template match="xhtml:table">
    <xsl:apply-templates/>
    <xsl:text>&#xa;</xsl:text>
  </xsl:template>

  <!-- Images -->
  <xsl:template match="xhtml:img">
    <xsl:text>!</xsl:text>
    <xsl:choose>
      <!-- Attachment -->
      <xsl:when test="@data-linked-resource-type = 'attachment'">
        <xsl:value-of select="@data-linked-resource-default-alias"/>
      </xsl:when>
      <!-- Web -->
      <xsl:otherwise>
        <xsl:value-of select="@data-mce-src"/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:text>!</xsl:text>
  </xsl:template>

  <!-- Macros -->
  <xsl:template match="xhtml:table[@class='wysiwyg-macro']|xhtml:img[@class='editor-inline-macro']">
    <xsl:variable name="macro" select="@data-macro-name"/>
    <xsl:variable name="indent" select="substring($spaces, 1, count(ancestor::*[local-name()='macro']) * $indentStep)"/>
    <xsl:if test="parent::*=/*">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
    <xsl:if test="document('')/*/lookup:macros/lookup:macro[@name=$macro and @indent='yes']">
      <xsl:value-of select="$indent"/>
    </xsl:if>
    <xsl:text>{</xsl:text>
    <xsl:value-of select="$macro"/>
    <xsl:if test="@data-macro-parameters or @data-macro-default-parameter">
      <xsl:text>:</xsl:text>
      <xsl:if test="@data-macro-default-parameter">
        <xsl:value-of select="@data-macro-default-parameter"/>
        <xsl:if test="@data-macro-parameters">
          <xsl:text>|</xsl:text>
        </xsl:if>
      </xsl:if>
      <xsl:value-of select="@data-macro-parameters"/>
    </xsl:if>
    <xsl:text>}</xsl:text>
    <xsl:if test="parent::*=/* or document('')/*/lookup:macros/lookup:macro[@name=$macro and @type='blockwrapper']">
      <xsl:text>&#xa;</xsl:text>
    </xsl:if>
    <xsl:if test="@data-macro-body-type='RICH_TEXT' or @data-macro-body-type='PLAIN_TEXT'">
      <xsl:if test="@data-macro-body-type='RICH_TEXT'">
      <xsl:apply-templates select="xhtml:tbody/xhtml:tr/xhtml:td/node()"/>
      </xsl:if>
      <xsl:if test="@data-macro-body-type='PLAIN_TEXT'">
      <xsl:apply-templates select="xhtml:tbody/xhtml:tr/xhtml:td/xhtml:pre/node()"/>
      </xsl:if>
      <xsl:if test="$macro='code'">
        <xsl:text>&#xa;</xsl:text>
      </xsl:if>
      <xsl:if test="document('')/*/lookup:macros/lookup:macro[@name=$macro and @indent='yes' and @type='blockwrapper']">
        <xsl:value-of select="$indent"/>
      </xsl:if>
      <xsl:text>{</xsl:text>
      <xsl:value-of select="$macro"/>
      <xsl:text>}</xsl:text>
      <xsl:if test="not(document('')/*/lookup:macros/lookup:macro[@name=$macro and @type='inline'])
        and not(parent::*[local-name()='li'] and .=parent::*/*[position()=last()])">
        <xsl:text>&#xa;</xsl:text>
      </xsl:if>
    </xsl:if>
  </xsl:template>

<lookup:macros>
  <lookup:macro name="highlight" type="inline"/>
  <lookup:macro name="span" type="inline"/>
  <lookup:macro name="color" type="inline"/>
  <lookup:macro name="table" type="blockwrapper" indent="yes"/>
  <lookup:macro name="tr" type="blockwrapper" indent="yes"/>
  <lookup:macro name="td" indent="yes"/>
  <lookup:macro name="th" indent="yes"/>
  <lookup:macro name="thead" type="blockwrapper" indent="yes"/>
  <lookup:macro name="tbody" type="blockwrapper" indent="yes"/>
  <lookup:macro name="tfoot" type="blockwrapper" indent="yes"/>
</lookup:macros>

  <!-- Emoticons -->

  <xsl:template match="xhtml:img[@data-emoticon-name]">
    <xsl:choose>
      <xsl:when test="@data-emoticon-name='smile'">:)</xsl:when>
      <xsl:when test="@data-emoticon-name='sad'">:(</xsl:when>
      <xsl:when test="@data-emoticon-name='cheeky'">:P</xsl:when>
      <xsl:when test="@data-emoticon-name='laugh'">:D</xsl:when>
      <xsl:when test="@data-emoticon-name='wink'">;)</xsl:when>
      <xsl:when test="@data-emoticon-name='thumbs-up'">(y)</xsl:when>
      <xsl:when test="@data-emoticon-name='thumbs-down'">(n)</xsl:when>
      <xsl:when test="@data-emoticon-name='information'">(i)</xsl:when>
      <xsl:when test="@data-emoticon-name='tick'">(/)</xsl:when>
      <xsl:when test="@data-emoticon-name='cross'">(x)</xsl:when>
      <xsl:when test="@data-emoticon-name='warning'">(!)</xsl:when>
      <xsl:otherwise>(Emoticon: <xsl:value-of select="@data-emoticon-name"/>)</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Text -->

  <xsl:template match="text()">
    <xsl:value-of select="."/>
  </xsl:template>

  <!-- Discard unwanted leading white space inside elements -->
  <xsl:template match="node()[(parent::xhtml:p or parent::xhtml:li or parent::xhtml:td) and position() = 1 and self::text()]">
    <xsl:variable name="input" select="."/>
    <xsl:choose>
      <xsl:when test="normalize-space($input) = ' ' or normalize-space($input) = ''"/>
      <xsl:otherwise>
        <xsl:variable name="firstNonWhiteSpaceChar" select="substring(normalize-space($input), 1, 1)"/>
        <xsl:value-of select="concat($firstNonWhiteSpaceChar, substring-after($input, $firstNonWhiteSpaceChar))"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!-- Discard unwanted leading white space after block elements -->
  <xsl:template match="text()[preceding-sibling::xhtml:p and normalize-space(.) = '']"/>
  <!-- Discard trailing white space after br (line break) element -->
  <xsl:template match="text()[preceding-sibling::xhtml:br and not(ancestor::xhtml:pre) and not(normalize-space(.) = .)]">
    <xsl:variable name="input" select="."/>
    <xsl:choose>
      <xsl:when test="normalize-space($input) = ' ' or normalize-space($input) = ''"/>
      <xsl:otherwise>
        <xsl:variable name="firstNonWhiteSpaceChar" select="substring(normalize-space($input), 1, 1)"/>
        <xsl:value-of select="concat($firstNonWhiteSpaceChar, substring-after($input, $firstNonWhiteSpaceChar))"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!-- Discard unwanted trailing space inside elements -->
  <xsl:template match="text()[(parent::xhtml:p or parent::xhtml:li or parent::xhtml:td) and position() = last() and not(preceding-sibling::xhtml:br)]">
    <xsl:variable name="input" select="."/>
    <xsl:variable name="firstChar" select="substring($input, 1, 1)"/>
    <!-- If the text node begins with whitespace, then reinstate a single leading space -->
    <xsl:if test="translate($firstChar, '&#xa; ', '') = ''">
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:value-of select="normalize-space(.)"/>
  </xsl:template>
  <!-- Discard unwanted newline before list element -->
  <xsl:template match="text()[following-sibling::xhtml:ol or following-sibling::xhtml:ul]">
    <xsl:variable name="input" select="."/>
    <xsl:variable name="firstChar" select="substring($input, 1, 1)"/>
    <!-- If the text node begins with whitespace, then reinstate a single leading space -->
    <xsl:if test="translate($firstChar, '&#xa; ', '') = ''">
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:value-of select="normalize-space(.)"/>
  </xsl:template>

  <!-- Page layout -->
  <xsl:template match="xhtml:div">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="xhtml:div[@class='innerCell'][preceding::xhtml:div[@class='innerCell']]">
    <xsl:text>&#xa;----&#xa;</xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Utility templates -->
  <xsl:template name="decimal2hex2digits">
    <xsl:param name="decimal" />
    <xsl:choose>
      <xsl:when test="$decimal > 0">
        <xsl:call-template name="decimal2hex">
          <xsl:with-param name="decimal" select="$decimal"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>00</xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="decimal2hex">
    <xsl:param name="decimal" />
    <xsl:if test="$decimal > 0">
      <xsl:call-template name="decimal2hex">
        <xsl:with-param name="decimal" select="floor($decimal div 16)" />
      </xsl:call-template>
      <xsl:choose>
        <xsl:when test="$decimal mod 16 &lt; 10">
          <xsl:value-of select="$decimal mod 16" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:choose>
            <xsl:when test="$decimal mod 16 = 10">A</xsl:when>
            <xsl:when test="$decimal mod 16 = 11">B</xsl:when>
            <xsl:when test="$decimal mod 16 = 12">C</xsl:when>
            <xsl:when test="$decimal mod 16 = 13">D</xsl:when>
            <xsl:when test="$decimal mod 16 = 14">E</xsl:when>
            <xsl:when test="$decimal mod 16 = 15">F</xsl:when>
            <xsl:otherwise>A</xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>