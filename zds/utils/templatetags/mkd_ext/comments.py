"""
A Python-Markdown preprocessor extension to ignore html comments opened by
three dashes (<!---comment-->) and any whitespace prior to them. I believe
pandoc has similar functionality.

Note: This extension does not work with the markdownfromFile function or
the convertFile method. They raise a UnicodeDecodeError.

Note: If using multiple extensions, mkdcomments probably should be last in
the list. Markdown extensions are loaded into the OrderedDict from which they
are executed in the order of the extension list. If a different extension is
loaded after mkdcomments, it may insert itself before mkdcomments in the
OrderedDict. Undesirable results may ensue. If, for instance, the 'meta'
extension is executed before mkdcomments, any comments in the meta-data will be
included in meta's dictionary.
"""

import re
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension


class CommentsExtension(Extension):
    def __init__(self,config={}):
        self.config={"START_TAG" : "<--COMMENTS", 
                     "END_TAG"   : "COMMENTS-->"}
        for key, value in config.iteritems():
            self.config[key] = value
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.preprocessors.add("comments", CommentsProcessor(md,self.config), "_begin")


class CommentsProcessor(Preprocessor):
    def __init__(self, md, config={}):
        Preprocessor.__init__(self, md)
        
        StaEsc = re.escape(config["START_TAG"])
        EndEsc = re.escape(config["END_TAG"])

        self.reMatchStart1 = r'.*'  + StaEsc
        self.reMatchEnd1   = r'.*'  + EndEsc
        self.reMatchComp1  = self.reMatchStart1 + self.reMatchEnd1
        self.reMatchStart2 = r'\s*' + StaEsc + r'.*'
        self.reMatchComp2  = self.reMatchStart2 + r'?' + EndEsc
        self.reMatchEnd2   = r'.*?' + EndEsc
        

    def run(self, lines):
        new_lines = []
        multi = False
        for line in lines:
            if not multi:
                resParse = self._uncommenter(line)
                multi = resParse[1]
                new_lines.append(resParse[0])
            else:
                resParse = self._unmultiliner(line)
                multi = resParse[1]
                nextLine = resParse[0]
                if not multi:
                    if len(nextLine.strip()) and len(new_lines) > 0:
                        new_lines[-1] += nextLine
                    else:
                        new_lines.append(nextLine)
        return new_lines

    def _uncommenter(self, line):
        if re.match(self.reMatchComp1, line):     # inline(could start multiline)
            return self._uncommenter(re.sub(self.reMatchComp2, '', line))
        elif re.match(self.reMatchStart1, line):        # start multiline
            return [re.sub(self.reMatchStart2, '', line), True]
        else:                                   # no comment
            return [line, False]

    def _unmultiliner(self, line):
        if re.match(self.reMatchEnd1, line):    # end multiline (could start comment)
            return self._uncommenter(re.sub(self.reMatchEnd2, '', line, count=1))
        else:
            return ['', True]                   # continue multiline
