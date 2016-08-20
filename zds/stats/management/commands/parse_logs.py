# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
import os
import re
from datetime import datetime
from user_agents import parse
from django.db import transaction
import pygeoip
from django.conf import settings
from urlparse import urlparse
from hashlib import md5
from zds.tutorialv2.models.models_database import PublishedContent
from zds.stats.models import Log, Source, Device, Browser, Country, City, OS

class ContentParsing(object):
    recognize_patterns = []
    type_content = ""

    def __init__(self, regxps):
        self.recognize_patterns = []
        for rg in regxps:
            self.recognize_patterns.append({
                "pattern": re.compile(rg["regxp"]),
                "regxp": rg["regxp"],
                "unique_group": rg["unique_group"],
                "mapped_app": "tutorialv2",
                "mapped_model": "models.models_database",
                "mapped_class": "PublishedContent",
                "mapped_column": "pk",
                })
            self.type_content = rg["type_content"].lower()

    def match_content(self, url_path):
        for rg in self.recognize_patterns:
            match_content = rg["pattern"].match(url_path)
            if match_content is not None:
                return (rg, match_content)
        return (None, None)

    def get_real_id_of_content(self, url_path):
        (reco, result) = self.match_content(url_path)
        if reco is not None:
            module = "zds.{}.{}".format(reco["mapped_app"], reco["mapped_model"])
            obj = __import__(module, globals(), locals(), [reco["mapped_class"]])
            cls = getattr(obj, reco["mapped_class"])
            args = {reco["mapped_column"]: result.group(reco["unique_group"])}
            ident = cls.objects.filter(**args).first()
            if ident is not None:
                return ident.pk
            else:
                return result.group(reco["unique_group"])

        return None

    def __unicode__(self):
        return unicode(self.recognize_patterns)


class Command(BaseCommand):
    args = 'path'
    help = 'Parse, filter and save logs into database'
    datas = []
    verbs = ["GET"]
    content_paths = ["/articles", "/tutoriels"]

    def get_geo_details(self, ip_adress):
        if len(ip_adress) <= 16:
            gic = pygeoip.GeoIP(os.path.join(settings.GEOIP_PATH, 'GeoLiteCity.dat'))
        else:
            gic = pygeoip.GeoIP(os.path.join(settings.GEOIP_PATH, 'GeoLiteCityv6.dat'))
        geo = gic.record_by_addr(ip_adress)
        if geo is not None:
            return (geo['city'], geo['country_name'])

        return (None, None)

    def is_treatable(self, dict_result):
        if dict_result["verb"] not in self.verbs or dict_result["status"] != 200:
            return False

        if dict_result["is_bot"]:
            return False

        for content_path in self.content_paths:
            if dict_result["path"].startswith(content_path):
                return True

        return False

    def flush_denormalize(self, class_name, field_in_class, field_in_log, list_of_datas):
        module = "zds.stats.models"
        obj = __import__(module, globals(), locals(), [class_name])
        cls = getattr(obj, class_name)
        data_existants = cls.objects.values_list(field_in_class, flat=True)
        data_for_save = list(set(list_of_datas)-set(data_existants))

        for my_data in data_for_save:
            create_arg = {field_in_class: my_data}
            cls.objects.create(**create_arg)


    @transaction.atomic
    def flush_data_in_database(self):
        my_sources = []
        my_os = []
        my_browsers = []
        my_devices = []
        my_cities = []
        my_countries = []
        for data in self.datas:
            existant = Log.objects.filter(hash_code=data["hash"], timestamp=data["timestamp"], content_type=data["type"]).first()
            if existant is None:
                existant = Log(id_zds=data["id_zds"],
                    content_type=data["type"],
                    remote_addr=data["remote_addr"],
                    hash_code=data["hash"],
                    body_bytes_sent=data["body_bytes_sent"],
                    timestamp=data["timestamp"],
                    dns_referal=data["dns_referal"],
                    os_family=data["os_family"],
                    os_version=data["os_version"],
                    browser_family=data["browser_family"],
                    browser_version=data["browser_version"],
                    device_family=data["device_family"],
                    request_time=data["request_time"],
                    country=data["country"],
                    city=data["city"])
            else:
                existant.id_zds = data["id_zds"]
                existant.remote_addr = data["remote_addr"]
                existant.body_bytes_sent=data["body_bytes_sent"]
                existant.dns_referal=data["dns_referal"]
                existant.os_family=data["os_family"]
                existant.os_version=data["os_version"]
                existant.browser_family=data["browser_family"]
                existant.browser_version=data["browser_version"]
                existant.device_family=data["device_family"]
                existant.request_time=data["request_time"]
                existant.country=data["country"]
                existant.city=data["city"]

            existant.save()
            my_sources.append(data["dns_referal"])
            my_os.append(data["os_family"])
            my_cities.append(data["city"])
            my_countries.append(data["country"])
            my_devices.append(data["device_family"])
            my_browsers.append(data["browser_family"])

        self.flush_denormalize("Source", "code", "dns_referal", my_sources)
        self.flush_denormalize("OS", "code", "os_family", my_os)
        self.flush_denormalize("Device", "code", "device_family", my_devices)
        self.flush_denormalize("Country", "code", "country", my_countries)
        self.flush_denormalize("City", "code", "city", my_cities)
        self.flush_denormalize("Browser", "code", "browser_family", my_browsers)



    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Veuillez préciser le chemin du fichier")
        elif not os.path.isfile(args[0]):
            raise CommandError("Veuillez préciser un chemin de fichier")


        regx = r'''
                ^(?P<remote_addr>\S+)\s-\s              # Remote address
                (?P<remote_user>\S+)\s                  # Remote user
                \[(?P<timestamp>.*?)\s(.*)\]\s                # Local time
                "                                       # Request
                (?P<verb>[A-Z]+)\s                      # HTTP verb (GET, POST, PUT, ...)
                (?P<path>[^?]+)                         # Request path
                (?:\?.+)?                               # Query string
                \sHTTP\/(?:[\d.]+)                       # HTTP/x.x protocol
                "\s                                     # /Request
                (?P<status>\d+?)\s                      # Response status code
                (?P<body_bytes_sent>\d+?)\s             # Body size in bytes
                "(?P<http_referer>[^"]+?)"\s            # Referer header
                "(?P<http_user_agent>[^"]+?)"\s         # User-Agent header
                "(?P<http_x_forwarded_for>[^"]+?)"\s    # X-Forwarded-For header
                (?P<request_time>[\d\.]+)\s             # Request time
                (?P<upstream_response_time>[\d\.]+)\s?  # Upstream response time
                (?P<pipe>\S+)?$                         # Pipelined request
                '''
        source = open(args[0], "r")
        pattern_log = re.compile(regx, re.VERBOSE)
        content_parsing = []
        
        reg_tuto= [{
            "regxp": "^\/tutoriels\/(?P<id_tuto>\d+)\/(?P<label_tuto>[\S][^\/]+)\/",
            "unique_group": "id_tuto",
            "type_content": "tutorial"
            }]
        reg_article= [{
            "regxp": "^\/articles\/(?P<id_article>\d+)\/(?P<label_article>[\S][^\/]+)\/",
            "unique_group": "id_article",
            "type_content": "article"
            }]
        
        content_parsing.append(ContentParsing(reg_tuto))
        content_parsing.append(ContentParsing(reg_article))

        for line in source:
            match = pattern_log.match(line)
            if match is not None:
                user_agent = parse(match.group("http_user_agent"))
                res = {}
                res["hash"] = md5(line.encode("utf-8")).hexdigest()
                res["remote_addr"] = match.group("remote_addr")
                (res["city"], res["country"]) = self.get_geo_details(res["remote_addr"])
                res["remote_user"] = match.group("remote_user")
                res["timestamp"] = datetime.strptime(match.group("timestamp"), "%d/%b/%Y:%H:%M:%S")
                res["verb"] = match.group("verb")
                res["path"] = match.group("path")
                res["status"] = int(match.group("status"))
                res["body_bytes_sent"] = int(match.group("body_bytes_sent"))
                res["dns_referal"] = urlparse(match.group("http_referer")).netloc
                res["os_family"] = user_agent.os.family
                res["os_version"] = user_agent.os.version_string
                res["browser_family"] = user_agent.browser.family
                res["browser_version"] = user_agent.browser.version_string
                res["device_family"] = user_agent.device.family
                res["request_time"] = float(match.group("request_time"))
                res["is_bot"] = user_agent.is_bot

                if self.is_treatable(res):
                    # treat
                    for p_content in content_parsing:
                        id_zds = p_content.get_real_id_of_content(res["path"])
                        if id_zds is not None:
                            res_content = res.copy()
                            res_content["type"] = p_content.type_content
                            res_content["id_zds"] = id_zds
                            self.datas.append(res_content)

        print("---> total : {}".format(len(self.datas)))
        source.close()
        self.flush_data_in_database()
        