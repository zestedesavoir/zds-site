import sys
import urllib.request
import os
import base64

url = os.environ["url"]
category = os.environ.get("graph_category", "")
login = os.environ.get("login", "")
password = os.environ.get("password", "")
base64string = base64.encodestring(f"{login}:{password}").replace("\n", "")

if len(sys.argv) == 2:
    url = url + "?" + sys.argv[1] + "=1"
    request = urllib.request.Request(url)
    if login != "" and password != "":
        request.add_header("Authorization", "Basic %s" % base64string)
    print(urllib.request.urlopen(request).read())
    # they can set the category in the config
    if category != "":
        print("graph_category " + category)
else:
    request = urllib.request.Request(url)
    if login != "" and password != "":
        request.add_header("Authorization", "Basic %s" % base64string)
    data = urllib.request.urlopen(request).readlines()
    for line in data:
        parts = line.split(" ")
        label = parts[0]
        value = " ".join(parts[1:])
        print(label + ".value " + value)
