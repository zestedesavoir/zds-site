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
from zds.stats.models import Log, Source, Device, OS, Country, City, Browser

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
    datas = []
    verbs = ['GET']
    content_paths = ['/articles', '/tutoriels']

    def get_geo_details(self, ip_adress):
        if len(ip_adress) <= 16:
            gic = pygeoip.GeoIP(os.path.join(settings.GEOIP_PATH, 'GeoLiteCity.dat'))
        else:
            gic = pygeoip.GeoIP(os.path.join(settings.GEOIP_PATH, 'GeoLiteCityv6.dat'))
        geo = gic.record_by_addr(ip_adress)
        if geo is not None:
            return (geo['city'], geo['country_name'])

        return None, None

    def is_treatable(self, dict_result):
        if dict_result['verb'] not in self.verbs or dict_result['status'] != 200:
            return False

        if dict_result['is_bot']:
            return False

        for content_path in self.content_paths:
            if dict_result['path'].startswith(content_path):
                return True

        return False

    @transaction.atomic
    def flush_data_in_database(self):
        new_logs = []
        keys = ['id_zds', 'content_type', 'remote_addr', 'hash_code', 'body_bytes_sent', 'timestamp',
                'os_version', 'browser_version', 'request_time']
        for data in self.datas:
            source, created_source = Source.objects.get_or_create(code=data['dns_referal'])
            os, created_os = OS.objects.get_or_create(code=data['os_family'])
            device, created_device = Device.objects.get_or_create(code=data['device_family'])
            country, created_country = Country.objects.get_or_create(code=data['country'])
            city, created_city = City.objects.get_or_create(code=data['city'])
            browser, created_browser = Browser.objects.get_or_create(code=data['browser_family'])

            existant = Log.objects.filter(hash_code=data['hash_code'],
                                          timestamp=data['timestamp'],
                                          content_type=data['content_type']).first()
            log_data = {key: data[key] for key in keys}

            if existant is None:
                log_instance = Log(**log_data)
            else:
                log_instance = Log(pk=existant.pk, **log_data)

            log_instance.dns_referal = source
            log_instance.os_family = os
            log_instance.device_family = device
            log_instance.country = country
            log_instance.city = city
            log_instance.browser_family = browser

            if existant is None:
                logger.debug(u'Ajout de la log du {} de type {}.'
                             .format(str(data['timestamp']), str(data['content_type'])))
                new_logs.append(log_instance)
            else:
                logger.debug(u'Mise à jour de la log du {} de type {}.'
                             .format(str(data['timestamp']), str(data['content_type'])))
                existant = Log(pk=existant.pk, **log_data)
                log_instance.save()

        if len(new_logs) > 0:
            logger.debug(u'Enregistrement de {} logs'.format(len(new_logs)))
            Log.objects.bulk_create(new_logs)
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
            content_parsing = []

            reg_tuto = [
                {
                    'regxp': '^\/tutoriels\/(?P<id_tuto>\d+)\/(?P<label_tuto>[\S][^\/]+)\/',
                    'unique_group': 'id_tuto',
                    'type_content': 'tutorial'
                }
            ]
            reg_article = [
                {
                    'regxp': '^\/articles\/(?P<id_article>\d+)\/(?P<label_article>[\S][^\/]+)\/',
                    'unique_group': 'id_article',
                    'type_content': 'article'
                }
            ]

            content_parsing.append(ContentParsing(reg_tuto))
            content_parsing.append(ContentParsing(reg_article))
            for line in source:
                match = pattern_log.match(line)
                if match is not None:
                    user_agent = parse(match.group('http_user_agent'))
                    res = {}
                    res['hash_code'] = md5(line.encode('utf-8')).hexdigest()
                    res['remote_addr'] = match.group('remote_addr')
                    (res['city'], res['country']) = self.get_geo_details(res['remote_addr'])
                    res['remote_user'] = match.group('remote_user')
                    res['timestamp'] = datetime.strptime(match.group('timestamp'), '%d/%b/%Y:%H:%M:%S')
                    res['verb'] = match.group('verb')
                    res['path'] = match.group('path')
                    res['status'] = int(match.group('status'))
                    res['body_bytes_sent'] = int(match.group('body_bytes_sent'))
                    res['dns_referal'] = urlparse(match.group('http_referer')).netloc
                    res['os_family'] = user_agent.os.family
                    res['os_version'] = user_agent.os.version_string
                    res['browser_family'] = user_agent.browser.family
                    res['browser_version'] = user_agent.browser.version_string
                    res['device_family'] = user_agent.device.family
                    res['is_bot'] = user_agent.is_bot
                    request_time_result = match.group('request_time')
                    if(request_time_result is not None):
                        res['request_time'] = float(request_time_result)
                    if self.is_treatable(res):
                        for p_content in content_parsing:
                            id_zds = p_content.get_real_id_of_content(res['path'])
                            if id_zds is not None:
                                res_content = res.copy()
                                res_content['content_type'] = p_content.type_content
                                res_content['id_zds'] = id_zds
                                self.datas.append(res_content)
            logger.info(u'Nombre de logs traitées : {}'.format(len(self.datas)))
            source.close()
            self.flush_data_in_database()
