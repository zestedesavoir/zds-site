# -*- coding: utf-8 -*-
from  zds import settings
import os

smileys_baseURL =os.path.join(settings.STATIC_URL, "smileys/")
smileys_ext = ""
smileys = {
    ":)"        : "smile.png",
    ":D"        : "heureux.png",
    ";)"        : "clin.png",
    ":p"        : "langue.png",
    ":lol:"     : "rire.gif",
    ":euh:"     : "unsure.gif",
    ":("        : "triste.png",
    ":o"        : "huh.png",
    ":colere2:" : "mechant.png",
    "o_O"       : "blink.gif",
    "^^"        : "hihi.png",
   u":-°"       : "siffle.png",
    ":ange:"    : "ange.png",
    ":colere:"  : "angry.gif",
    ":diable:"  : "diable.png",
    ":magicien:": "magicien.png",
    ":ninja:"   : "ninja.png",
    ">_<"       : "pinch.png",
    ":pirate:"  : "pirage.png",
    ":'("       : "pleure.png",
    ":honte:"   : "rouge.png",
    ":soleil:"  : "soleil.png",
    ":waw:"     : "waw.png",
    ":zorro:"   : "zorro.png",
    }

