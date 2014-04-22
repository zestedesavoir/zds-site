# coding: utf-8

import os


if __name__ == "__main__":
    smileys_baseURL = os.path.join("../../../assets", "smileys")
else:
    from zds import settings
    smileys_baseURL = os.path.join(settings.STATIC_URL, "smileys")

smileys_base = {
    "smile.png": (":)", ":-)", ),
    "heureux.png": (":D", ":-D", ),
    "clin.png": (";)", ";-)", ),
    "langue.png": (":p", ":P", ":-p", ":-P", ),
    "rire.gif": (":lol:", ),
    "unsure.gif": (":euh:", ),
    "triste.png": (":(", ":-(", ),
    "huh.png": (":o", ":-o", ":O", ":-O", ),
    "mechant.png": (":colere2:", ),
    "blink.gif": ("o_O", "O_o", ),
    "hihi.png": ("^^", ),
    "siffle.png": (u":-°", u":°", ),
    "ange.png": (":ange:", ),
    "angry.gif": (":colere:", ),
    "diable.png": (":diable:", ),
    "magicien.png": (":magicien:", ),
    "ninja.png": (":ninja:", ),
    "pinch.png": (">_<", ),
    "pirate.png": (":pirate:", ),
    "pleure.png": (":'(", ),
    "rouge.png": (":honte:", ),
    "soleil.png": (":soleil:", ),
    "waw.png": (":waw:", ),
    "zorro.png": (":zorro:", ),
}

smileys = {}
for imageFile, symboles in smileys_base.iteritems():
    for symbole in symboles:
        smileys[symbole] = os.path.join(smileys_baseURL, imageFile)

if __name__ == "__main__":
    for image in smileys.values():
        if not os.path.isfile(image):
            print "[" + image + "] is not found !!!"
