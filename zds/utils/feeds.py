import re

from django.utils.feedgenerator import Atom1Feed, Rss201rev2Feed
from django.utils.xmlutils import SimplerXMLGenerator


class DropControlCharsXMLGenerator(SimplerXMLGenerator):
    def characters(self, content):
        # From django.utils.xmlutils.SimplerXMLGenerator.characters()
        super().characters(re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", content))


class DropControlCharsRss201rev2Feed(Rss201rev2Feed):
    def write(self, outfile, encoding):
        # From django.utils.feedgenerator.RssFeed.write()
        handler = DropControlCharsXMLGenerator(outfile, encoding)
        handler.startDocument()
        handler.startElement("rss", self.rss_attributes())
        handler.startElement("channel", self.root_attributes())
        self.add_root_elements(handler)
        self.write_items(handler)
        self.endChannelElement(handler)
        handler.endElement("rss")


class DropControlCharsAtom1Feed(Atom1Feed):
    def write(self, outfile, encoding):
        # From django.utils.feedgenerator.Atom1Feed.write()
        handler = DropControlCharsXMLGenerator(outfile, encoding)
        handler.startDocument()
        handler.startElement("feed", self.root_attributes())
        self.add_root_elements(handler)
        self.write_items(handler)
        handler.endElement("feed")
