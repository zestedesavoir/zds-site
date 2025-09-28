#!/usr/bin/env python3
import base64
import os
import sys
import urllib.request

plugin_name = os.path.basename(__file__)
route = plugin_name[plugin_name.find("_") + 1 :]

url_base = os.environ.get("url_base", "http://127.0.0.1")
category = os.environ.get("graph_category", plugin_name[: plugin_name.find("_")])
login = os.environ.get("login", "")
password = os.environ.get("password", "")
base64string = base64.b64encode(f"{login}:{password}".encode())

url = url_base + "/munin/" + route + "/"

if len(sys.argv) == 2:
    url = url + "?" + sys.argv[1] + "=1"
    request = urllib.request.Request(url)
    if login != "" and password != "":
        request.add_header("Authorization", "Basic %s" % base64string)
    print(urllib.request.urlopen(request).read().decode())
    # they can set the category in the config
    if category != "":
        print("graph_category " + category)
else:
    request = urllib.request.Request(url)
    if login != "" and password != "":
        request.add_header("Authorization", "Basic %s" % base64string)
    data = urllib.request.urlopen(request).readlines()
    for line in data:
        parts = line.decode().split(" ")
        label = parts[0]
        value = " ".join(parts[1:])
        print(label + ".value " + value)
