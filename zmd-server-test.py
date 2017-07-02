import timeit
import textwrap
from pprint import pprint
import os
from requests import post


def foo():
    md_source = textwrap.dedent("""
        !(https://www.youtube.com/watch?v=dQw4w9WgXcQ)
        # title 1

        A [link with **bold**](http://example.com)

        Some ZDS and ||key|| with a~~One~~ b~two~ c^three^

        Some typo : a'tchou "cheers"...

        A sentence ($S$) with *italic*[^italic] and inline match ($C_L$) and another[^bar] footnote.

        $$
        L = \frac{1}{2} \rho v^2 S C_L
        $$

        A quote:
        > With a custom block:
        >
        > [[attention]]
        > | A link: [example](http://example.com)
        > | > A nested quote!
        > | After the nested quote.
        > Outside the block.
        After the quote.

        *[ZDS]: Look, title!
        [^bar]: bar
        [^italic]: italic

    """)

    opts = {'foo': True, 'disable_ping': True, 'disable_jsfiddle': False}
    r = post('http://127.0.0.1:27272/html', json={
        'opts': opts,
        'md': md_source
    })
    content, metadata = r.json()
    pprint(content)
    pprint(metadata)

if __name__ == '__main__':
    foo()
# print(timeit.timeit("foo()", setup="from __main__ import foo", number=10000))
