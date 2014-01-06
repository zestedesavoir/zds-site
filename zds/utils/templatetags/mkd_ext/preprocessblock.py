#! /usr/bin/env python

import markdown

class PreprocessBlockExtension(markdown.extensions.Extension):
    """This extension will change the default behaviour of python-markdown and allow to use 
    pre-processing extensions inside block"""
    def __init__(self, configs={}):
        markdown.extensions.Extension.__init__(self)
        
        if "preprocess" in configs:
            self.preprocessNames = configs["preprocess"]
        else:
            self.preprocessNames = []

    def extendMarkdown(self, md, md_globals):
        oldParseChunk = md.parser.parseChunk
        
        self.addPreprocessor(md)

        def newParseChunk( parent, text):
            lines = text.split("\n")
            for pre in self.preprocess:
                lines = pre.run(lines)
            text = "\n".join(lines)
            return oldParseChunk( parent, text)
        
        md.parser.parseChunk = newParseChunk
    
    def addPreprocessor(self, md):
        self.preprocess = []
        for name in self.preprocessNames:
            if name in md.preprocessors:
                self.preprocess.append(md.preprocessors[name])

def makeExtension(configs={}):
    return PreprocessExtension(configs=dict(configs))

