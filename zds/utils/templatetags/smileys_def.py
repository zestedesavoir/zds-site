# coding: utf-8

import os
from django.conf import settings

SMILEYS_BASE_URL = os.path.join(settings.STATIC_URL, 'smileys')

SMILEYS_BASE = {
    'smile.png': (':)', ':-)', ),
    'heureux.png': (':D', ':-D', ),
    'clin.png': (';)', ';-)', ),
    'langue.png': (':p', ':P', ':-p', ':-P', ),
    'rire.gif': (':lol:', ),
    'unsure.gif': (':euh:', ),
    'triste.png': (':(', ':-(', ),
    'huh.png': (':o', ':-o', ':O', ':-O', ),
    'mechant.png': (':colere2:', ),
    'blink.gif': ('o_O', 'O_o', ),
    'hihi.png': ('^^', ),
    'siffle.png': (':-°', ':°', ),
    'ange.png': (':ange:', ),
    'angry.gif': (':colere:', ),
    'diable.png': (':diable:', ),
    'magicien.png': (':magicien:', ),
    'ninja.gif': (':ninja:', ),
    'pinch.png': ('>_<', ),
    'pirate.png': (':pirate:', ),
    'pleure.png': (":'(", ),
    'rouge.png': (':honte:', ),
    'soleil.png': (':soleil:', ),
    'waw.png': (':waw:', ),
    'zorro.png': (':zorro:', ),
    'cthulhu.png': ('^(;,;)^', ),
}

smileys = {}
for image_file, symbols in SMILEYS_BASE.items():
    for symbol in symbols:
        smileys[symbol] = os.path.join(SMILEYS_BASE_URL, image_file)
