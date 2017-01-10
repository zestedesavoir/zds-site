# -*- coding: utf-8 -*-
# Gestion fine de la typographie française, du moins, ce qui peut être
# automatisé, Lointainement inspiré de l’extension SmartyPants.

from __future__ import unicode_literals
import markdown
from ..inlinepatterns import HtmlPattern


class ReplacePattern(HtmlPattern):
    def __init__(self, pattern, replacement, markdown):
        """ Replace the pattern by a simple text. """
        HtmlPattern.__init__(self, pattern)
        self.replacement = replacement
        self.markdown = markdown

    def handleMatch(self, m):
        return self.markdown.htmlStash.store(self.replacement, safe=True)


class ReplaceWithSpacePattern(HtmlPattern):
    def __init__(self, pattern, replacement, markdown):
        """ Replace the pattern by a simple text. """
        HtmlPattern.__init__(self, pattern)
        self.replacement = replacement
        self.markdown = markdown

    def handleMatch(self, m):
        space = m.group(2)
        replacement = self.replacement + space
        return self.markdown.htmlStash.store(replacement, safe=True)


class FrenchTypographyExtension(markdown.extensions.Extension):
    def __init__(self, *args, **kwargs):
        self.config = {
            'apostrophes': [True, 'Typographic apostrophes'],
            'em_dashes': [True, 'Em dashes'],
            'en_dashes': [True, 'En dashes'],
            'unbreakable_spaces': [True, 'Unbreakable spaces'],
            'angle_quotes': [True, 'Angle quotes'],
            'per_mil': [True, 'Per mil symbol'],
            'ellipses': [True, 'Ellipses'],
        }
        super(FrenchTypographyExtension, self).__init__(*args, **kwargs)

    def replaceApostrophes(self, md):
        apostrophesPattern = ReplacePattern("'", "&rsquo;", md)
        self.replacements.add('apostrophes', apostrophesPattern, '_begin')

    def replaceEmDashes(self, md):
        emDashesPattern = ReplacePattern(r'(?<!-)---(?!-)', "&mdash;", md)
        self.replacements.add('em_dashes', emDashesPattern, '_begin')

    def replaceEnDashes(self, md):
        enDashesPattern = ReplacePattern(
            r'(?<!-)--(?!-)', "&ndash;", md
        )
        self.replacements.add(
            'en_dashes', enDashesPattern, '_begin'
        )

    def replaceSpaces(self, md):
        semicolonWithSpacePattern = ReplaceWithSpacePattern(
            r' ;([\s]|$)', "&#x202F;;", md
        )
        colonWithSpacePattern = ReplaceWithSpacePattern(
            r' :([\s]|$)', "&#x202F;:", md
        )
        interrogationWithSpacePattern = ReplacePattern(" \?", "&#x202F;?", md)
        exclamationWithSpacePattern = ReplacePattern(" !", "&#x202F;!", md)
        perCentWithSpacePattern = ReplacePattern(" %", "&nbsp;%", md)
        perMilWithSpacePattern = ReplacePattern(' ‰', "&nbsp;&permil;", md)
        openingAngleQuoteWithSpacePattern = ReplacePattern('« ', "&laquo;&nbsp;", md)
        closingAngleQuoteWithSpacePattern = ReplacePattern(' »', "&nbsp;&raquo;", md)

        self.replacements.add(
            'semicolon_with_space', semicolonWithSpacePattern, '_end'
        )
        self.replacements.add(
            'colon_with_space',
            colonWithSpacePattern,
            '<semicolon_with_space'
        )
        self.replacements.add(
            'interrogation_mark_with_space',
            interrogationWithSpacePattern,
            '<colon_with_space'
        )
        self.replacements.add(
            'exclamation_mark_with_space',
            exclamationWithSpacePattern,
            '<interrogation_mark_with_space'
        )
        self.replacements.add(
            'per_cent_with_space',
            perCentWithSpacePattern,
            '<exclamation_mark_with_space'
        )
        self.replacements.add(
            'per_mil_with_space',
            perMilWithSpacePattern,
            '<per_cent_with_space'
        )
        self.replacements.add(
            'opening_angle_quote_with_space',
            openingAngleQuoteWithSpacePattern,
            '<per_mil_with_space'
        )
        self.replacements.add(
            'closing_angle_quote_with_space',
            closingAngleQuoteWithSpacePattern,
            '<opening_angle_quote_with_space'
        )

    def replaceAngleQuotes(self, md):
        openingAngleQuotesPattern = ReplacePattern(r'<<', "&laquo;", md)
        closingAngleQuotesPattern = ReplacePattern(r'>>', "&raquo;", md)
        self.replacements.add(
            'opening_angle_quotes', openingAngleQuotesPattern, '_begin'
        )
        self.replacements.add(
            'closing_angle_quotes',
            closingAngleQuotesPattern,
            '>opening_angle_quotes'
        )

    def replaceAngleQuotesWithSpaces(self, md):
        openingAngleQuotesPattern = ReplacePattern(
            r'<< ', "&laquo;&nbsp;", md
        )
        closingAngleQuotesPattern = ReplacePattern(
            r' >>', "&nbsp;&raquo;", md
        )
        self.replacements.add(
            'opening_angle_quotes_space', openingAngleQuotesPattern, '_begin'
        )
        self.replacements.add(
            'closing_angle_quotes_space',
            closingAngleQuotesPattern,
            '>opening_angle_quotes'
        )

    def replacePerMil(self, md):
        perMilPattern = ReplacePattern("%o", "&permil;", md)
        self.replacements.add('per_mil', perMilPattern, '_begin')

    def replacePerMilWithSpace(self, md):
        perMilPattern = ReplacePattern(" %o", "&nbsp;&permil;", md)
        self.replacements.add('per_mil_with_space2', perMilPattern, '_begin')

    def replaceEllipses(self, md):
        ellipsesPattern = ReplacePattern(
            r'(?<!\.)\.{3}(?!\.)', "&hellip;", md
        )
        self.replacements.add('ellipses', ellipsesPattern, '_begin')

    def extendMarkdown(self, md, md_globals):
        configs = self.getConfigs()
        self.replacements = markdown.odict.OrderedDict()
        if configs['apostrophes']:
            self.replaceApostrophes(md)
            md.ESCAPED_CHARS.append("'")
        if configs['em_dashes']:
            self.replaceEmDashes(md)
        if configs['en_dashes']:
            self.replaceEnDashes(md)
        if configs['unbreakable_spaces']:
            self.replaceSpaces(md)
            md.ESCAPED_CHARS.extend([" ", "«", "»"])
        if configs['angle_quotes']:
            self.replaceAngleQuotes(md)
            md.ESCAPED_CHARS.append("<")
        if configs['angle_quotes'] and configs['unbreakable_spaces']:
            self.replaceAngleQuotesWithSpaces(md)
        if configs['per_mil']:
            self.replacePerMil(md)
            md.ESCAPED_CHARS.append("%")
        if configs['per_mil'] and configs['unbreakable_spaces']:
            self.replacePerMilWithSpace(md)
        if configs['ellipses']:
            self.replaceEllipses(md)
            md.ESCAPED_CHARS.append("...")
        processing = markdown.treeprocessors.InlineProcessor(md)
        processing.inlinePatterns = self.replacements
        md.treeprocessors.add('french_typography', processing, '_end')
