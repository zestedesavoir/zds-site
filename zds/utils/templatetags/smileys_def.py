import os

from django.conf import settings

SMILEYS_BASE_PATH = settings.BASE_DIR / "dist" / "smileys"
LICENSES_BASE_PATH = settings.BASE_DIR / "dist" / "licenses"
SMILEYS_BASE_URL = os.path.join(settings.STATIC_URL, "smileys")

SMILEYS_BASE = {
    "smile.png": (
        ":)",
        ":-)",
    ),
    "heureux.png": (
        ":D",
        ":-D",
    ),
    "clin.png": (
        ";)",
        ";-)",
    ),
    "b.png": (":B",),
    "langue.png": (
        ":p",
        ":P",
        ":-p",
        ":-P",
    ),
    "rire.gif": (":lol:",),
    "unsure.gif": (":euh:",),
    "triste.png": (
        ":(",
        ":-(",
    ),
    "huh.png": (
        ":o",
        ":-o",
        ":O",
        ":-O",
    ),
    "mechant.png": (":colere2:",),
    "blink.gif": (
        "o_O",
        "O_o",
    ),
    "hihi.png": ("^^",),
    "siffle.png": (
        ":-°",
        ":°",
    ),
    "ange.png": (":ange:",),
    "angry.gif": (":colere:",),
    "diable.png": (":diable:",),
    "magicien.png": (":magicien:",),
    "ninja.gif": (":ninja:",),
    "pinch.png": (">_<", "X/"),
    "pirate.png": (":pirate:",),
    "pleure.png": (":'(",),
    "rouge.png": (":honte:",),
    "soleil.png": (":soleil:",),
    "waw.png": (":waw:",),
    "zorro.png": (":zorro:",),
    "cthulhu.png": ("^(;,;)^",),
    "popcorn.png": (":popcorn:",),
}

smileys = {}
for image_file, symbols in SMILEYS_BASE.items():
    for symbol in symbols:
        smileys[symbol] = os.path.join(SMILEYS_BASE_URL, image_file)
