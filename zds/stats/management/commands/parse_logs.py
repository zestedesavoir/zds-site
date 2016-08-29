# coding: utf-8
import os
import re
import codecs
from datetime import datetime
from user_agents import parse
import pygeoip
from urlparse import urlparse
from hashlib import md5
import logging
from django.db import transaction
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from zds.stats.models import Log

logger = logging.getLogger('zds')


class ContentParsing(object):
    recognize_patterns = []
    type_content = ''

    def __init__(self, regxps):
        self.recognize_patterns = []
        for rg in regxps:
            self.recognize_patterns.append(
                {
                    'pattern': re.compile(rg['regxp']),
                    'regxp': rg['regxp'],
                    'unique_group': rg['unique_group'],
                    'mapped_app': 'tutorialv2',
                    'mapped_model': 'models.models_database',
                    'mapped_class': 'PublishedContent',
                    'mapped_column': 'pk',
                }
            )
            self.type_content = rg['type_content'].lower()

    def match_content(self, url_path):
        for rg in self.recognize_patterns:
            match_content = rg['pattern'].match(url_path)
            if match_content is not None:
                return (rg, match_content)
        return (None, None)

    def get_real_id_of_content(self, url_path):
        (reco, result) = self.match_content(url_path)
        if reco is not None:
            module = 'zds.{}.{}'.format(reco['mapped_app'], reco['mapped_model'])
            obj = __import__(module, globals(), locals(), [reco['mapped_class']])
            cls = getattr(obj, reco['mapped_class'])
            args = {reco['mapped_column']: result.group(reco['unique_group'])}
            ident = cls.objects.filter(**args).first()
            if ident is not None:
                return ident.pk
            else:
                return result.group(reco['unique_group'])

        return None

    def __unicode__(self):
        return unicode(self.recognize_patterns)


class Command(BaseCommand):
    args = 'path'
    help = 'Parse, filter and save logs into database'
    data_set = []

    def get_geo_details(self, ip_adress):
        if len(ip_adress) <= 16:
            gic = pygeoip.GeoIP(os.path.join(settings.GEOIP_PATH, 'GeoLiteCity.dat'))
        else:
            gic = pygeoip.GeoIP(os.path.join(settings.GEOIP_PATH, 'GeoLiteCityv6.dat'))
        geo = gic.record_by_addr(ip_adress)
        if geo is not None:
            return (geo['city'], geo['country_name'])

        return None, None

    def check_verb(self, verb):
        return verb == "GET"

    def check_status(self, status):
        return status == "200"

    def check_user_agent(self, user_agent):
        return not user_agent.is_bot

    def flush_denormalize(self, class_name, field_in_class, field_in_log, list_of_datas):
        module = 'zds.stats.models'
        obj = __import__(module, globals(), locals(), [class_name])
        cls = getattr(obj, class_name)
        data_existants = cls.objects.values_list(field_in_class, flat=True)
        data_for_save = set(set(list_of_datas) - set(data_existants))

        data_set_ready = []
        for my_data in data_for_save:
            ins = {field_in_class: my_data}
            data_set_ready.append(cls(**ins))

        cls.objects.bulk_create(data_set_ready)

    @transaction.atomic
    def flush_data_in_database(self):
        my_sources = []
        my_os = []
        my_browsers = []
        my_devices = []
        my_cities = []
        my_countries = []
        new_logs = []
        keys = ['id_zds', 'content_type', 'remote_addr', 'hash_code', 'body_bytes_sent', 'timestamp',
                'dns_referal', 'os_family', 'os_version', 'browser_family', 'browser_version',
                'device_family', 'request_time', 'country', 'city']

        for data in self.data_set:
            existant = Log.objects.filter(hash_code=data['hash_code'],
                                          timestamp=data['timestamp'],
                                          content_type=data['content_type']).first()
            log_data = {key: data[key] for key in keys}

            if existant is None:
                log_instance = Log(**log_data)
                logger.debug(u'Ajout de la log du {} de type {}.'
                             .format(str(data['timestamp']), str(data['content_type'])))
                new_logs.append(log_instance)
            else:
                logger.debug(u'Mise à jour de la log du {} de type {}.'
                             .format(str(data['timestamp']), str(data['content_type'])))
                existant = Log(pk=existant.pk, **log_data)
                existant.save()

            my_sources.append(data['dns_referal'])
            my_os.append(data['os_family'])
            my_cities.append(data['city'])
            my_countries.append(data['country'])
            my_devices.append(data['device_family'])
            my_browsers.append(data['browser_family'])

        if len(new_logs) > 0:
            logger.debug(u'Enregistrement de {} logs'.format(len(new_logs)))
            Log.objects.bulk_create(new_logs)
        self.flush_denormalize('Source', 'code', 'dns_referal', my_sources)
        self.flush_denormalize('OS', 'code', 'os_family', my_os)
        self.flush_denormalize('Device', 'code', 'device_family', my_devices)
        self.flush_denormalize('Country', 'code', 'country', my_countries)
        self.flush_denormalize('City', 'code', 'city', my_cities)
        self.flush_denormalize('Browser', 'code', 'browser_family', my_browsers)

        logger.debug(u'Taille de logs dans la base {} enregistrements '.format(Log.objects.all().count()))

    def handle(self, *args, **options):
        if len(args) != 1:
            logger.error(u'Chemin du fichier à parser absent')
            raise CommandError('Veuillez préciser le chemin du fichier')
        elif not os.path.isfile(args[0]):
            logger.error(u'Le paramètre passé en argument n\'est pas un fichier')
            raise CommandError('Veuillez préciser un chemin de fichier')
        else:
            logger.info(u'Début du parsing du fichier {}'.format(args[0]))

        regx = r'''
                ^(?P<remote_addr>\S+)\s-\s              # Remote address
                (?P<remote_user>\S+)\s                  # Remote user
                \[(?P<timestamp>.*?)\s(.*)\]\s          # Local time
                "                                       # Request
                (?P<verb>[A-Z]+)\s                      # HTTP verb (GET, POST, PUT, ...)
                (?P<path>[^?]+)                         # Request path
                (?:\?.+)?                               # Query string
                \sHTTP\/(?:[\d.]+)                      # HTTP/x.x protocol
                "\s                                     # /Request
                (?P<status>\d+?)\s                      # Response status code
                (?P<body_bytes_sent>\d+?)\s             # Body size in bytes
                "(?P<http_referer>[^"]+?)"\s            # Referer header
                "(?P<http_user_agent>[^"]+?)"\s?        # User-Agent header
                "?(?P<http_x_forwarded_for>[^"]+?)?"?\s?    # X-Forwarded-For header
                (?P<request_time>[\d\.]+)?\s?           # Request time
                (?P<upstream_response_time>[\d\.]+)?\s? # Upstream response time
                (?P<pipe>\S+)?$                         # Pipelined request
                '''

        with codecs.open(args[0], "r", "utf-8") as source:
            pattern_log = re.compile(regx, re.VERBOSE)

            reg_content = '^\/(articles|tutoriels)\/(?P<id>\d+)\/(?P<label>[\S][^\/]+)'
            pattern_path = re.compile(reg_content)

            for line in source:
                match = pattern_log.match(line)
                if match is not None:
                    if not self.check_verb(match.group('verb')):
                        continue

                    if not self.check_status(match.group('status')):
                        continue

                    user_agent = parse(match.group('http_user_agent'))
                    if not self.check_user_agent(user_agent):
                        continue
                    res = {}

                    path = match.group('path')
                    match_path = pattern_path.match(path)
                    if match_path is not None:
                        res['id_zds'] = match_path.group('id')
                        if(path.startswith("/articles")):
                            res['content_type'] = "article"
                        elif (path.startswith("/tutoriels")):
                            res['content_type'] = "tutorial"

                    res['hash_code'] = md5(line.encode('utf-8')).hexdigest()
                    res['remote_addr'] = match.group('remote_addr')
                    (res['city'], res['country']) = self.get_geo_details(res['remote_addr'])
                    res['remote_user'] = match.group('remote_user')
                    res['timestamp'] = datetime.strptime(match.group('timestamp'), '%d/%b/%Y:%H:%M:%S')
                    res['body_bytes_sent'] = int(match.group('body_bytes_sent'))
                    res['dns_referal'] = urlparse(match.group('http_referer')).netloc
                    res['os_family'] = user_agent.os.family
                    res['os_version'] = user_agent.os.version_string
                    res['browser_family'] = user_agent.browser.family
                    res['browser_version'] = user_agent.browser.version_string
                    res['device_family'] = user_agent.device.family
                    request_time_result = match.group('request_time')
                    if(request_time_result is not None):
                        res['request_time'] = float(request_time_result)

                    self.data_set.append(res)

            logger.info(u'Nombre de logs a traiter : {}'.format(len(self.data_set)))
            source.close()
            self.flush_data_in_database()
            logger.info(u'Fin du parsing du fichier réalisé avec succes')
