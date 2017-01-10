from __future__ import absolute_import
from __future__ import unicode_literals
import re
import unicodedata
from . import Extension
from ..treeprocessors import Treeprocessor
from collections import namedtuple
from ..util import etree

TitleElement = namedtuple("TitleElement", "title anchor level")


def slugify(value, separator):
    """ Slugify a string, to make it URL friendly. """
    # function coming from Table of Contents Extension for Python-Markdown
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub('[^\w\s-]', '', value.decode('ascii')).strip().lower()
    return re.sub('[%s\s]+' % separator, separator, value)


class TitleAnchorTreeprocessor(Treeprocessor):
    def __init__(self, config, md):
        self.config = config

        self.anchors = set()

        self.marker_key = self.config.get("marker_key", "")

        starting_title = self.config.get("starting_title", 1)
        ending_title = self.config.get("ending_title", 6)
        self.allowed_tags = tuple("h{}".format(i) for i in range(starting_title, ending_title + 1))

        self.root_only = bool(self.config.get('root_only', True))

        self.link_position = self.config.get('link_position', None)

        Treeprocessor.__init__(self, markdown_instance=md)

        self.reset()

    def reset(self):
        self.anchors = set()
        self.markdown.metadata["toc"] = []

    def get_anchor_key(self, title):
        slug = slugify(title, "-")
        if self.marker_key:
            slug = "{}-{}".format(self.marker_key, slug)
        if slug in self.anchors:
            i = 1
            while "{}-{}".format(slug, i) in self.anchors:
                i += 1
            slug = "{}-{}".format(slug, i)
        self.anchors.add(slug)
        return slug

    def add_anchor(self, element, title_element):
        element.set("id", title_element.anchor)

    def add_link(self, element, title_element):
        if self.link_position not in ("before", "after"):
            return
        link = etree.Element("a")
        link.set("href", u"#{}".format(title_element.anchor))
        sp = etree.Element("span")
        sp.set("class", "anchor-link")
        link.append(sp)
        if self.link_position == "before":
            link.tail = element.text
            element.text = ""
            element.insert(0, link)
        else:
            element.append(link)

    def run(self, root):
        if self.root_only:
            iterator = root.findall("*")
        else:
            iterator = root.iter()

        toc = []

        for element in iterator:
            tag = element.tag
            if tag.startswith("h") and tag in self.allowed_tags:
                level = int(tag[1:])
                title = element.text
                if title is None:
                    continue
                anchor = self.get_anchor_key(title)
                title_element = TitleElement(title, anchor, level)
                toc.append((element, title_element))

        for element, title_element in toc:
            self.add_anchor(element, title_element)
            self.add_link(element, title_element)
        self.markdown.metadata["toc"] = [e for _, e in toc]


class TitleAnchorExtension(Extension):
    def __init__(self, **kwargs):
        """ Setup configs. """
        self.ext = None
        self.config = {'root_only': [True,
                                     "Search on the root only of the html tree or in the full html tree."
                                     'Set to False to catch title into quote for example.'],
                       "starting_title": [1,
                                          "Starting level to catch. Should be set according to own header extension"],
                       "ending_title": [6,
                                        "Ending level to catch. Should be set according to own header extension"],
                       "marker_key": ["",
                                      "Text added to all anchor. Should be unique for all extract."],
                       "link_position": ["",
                                         "Set link position. With 'before' or 'after' span are inserted with link "
                                         "before/after title element. With other values, no link are inserted."]}
        Extension.__init__(self, **kwargs)

    def reset(self):
        if self.ext is not None:
            self.ext.reset()

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.ext = TitleAnchorTreeprocessor(self.getConfigs(), md)
        md.treeprocessors.add("title_anchor", self.ext, "_end")
