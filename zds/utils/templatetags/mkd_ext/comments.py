# Comment extension by cgabard
# inspired by  https://github.com/ryneeverett/python-markdown-comments

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
        md.preprocessors.add("comments", CommentsProcessor(md, self.config), "_begin")

class CommentsProcessor(Preprocessor):
    
    def __init__(self, md, config={}):
        Preprocessor.__init__(self, md)
        
        StaEsc = re.escape(config["START_TAG"])
        EndEsc = re.escape(config["END_TAG"])
        
        self.RE = re.compile(StaEsc + r'.*?' + EndEsc, re.MULTILINE | re.DOTALL)

    def run(self, lines):
        text = "\n".join(lines)
        while True:
            m = self.RE.search(text)
            if m:
                text = "%s%s" % (text[:m.start()], text[m.end():])
            else:
                break
        return text.split("\n")


