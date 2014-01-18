# From https://github.com/mayoff/python-markdown-mathjax

import markdown

class MathJaxPattern(markdown.inlinepatterns.Pattern):

    def __init__(self):
        markdown.inlinepatterns.Pattern.__init__(self, r'(?<!\\)(\$\$?)(.+?)\2')

    def handleMatch(self, m):
        if m.group(2) == "$" and "\n" in m.group(3):
            node = markdown.util.etree.Element('span')
            node.text = "\\" + m.group(2) + m.group(3) + "\\" + m.group(2)
        else:
            node = markdown.util.etree.Element('mathjax')
            node.text = markdown.util.AtomicString(m.group(2) + m.group(3) + m.group(2))
        return node

class MathJaxExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        # Needs to come before escape matching because \ is pretty important in LaTeX
        md.inlinePatterns.add('mathjax', MathJaxPattern(), '<escape')

def makeExtension(configs=None):
    return MathJaxExtension(configs)


