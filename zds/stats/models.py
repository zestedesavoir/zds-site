# coding: utf-8

from django.db import models
from django.db.models import Avg, Min, Max, Count
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Dimension:

    def get_total_visits(self):
        args = {self.code_name: self.code_value}
        return Log.objects.filter(**args).count()

    def get_unique_visits(self):
        args = {self.code_name: self.code_value}
        return Log.objects.filter(**args).values_list('remote_addr', flat=True).distinct().count()

    def get_avg_load_speed(self):
        args = {self.code_name: self.code_value}
        req_result = Log.objects.filter(**args).aggregate(avg_load_speed=Avg('request_time'))
        return req_result['avg_load_speed']

    def get_avg_size_page(self):
        args = {self.code_name: self.code_value}
        req_result = Log.objects.filter(**args).aggregate(avg_size_page=Max('body_bytes_sent'))
        return req_result['avg_size_page']

    def __str__(self):
        return u'{}'.format(self.code)


class Loggable(Dimension):

    def __init__(self, *args, **kwargs):
        self.code_name = 'id_zds'
        super(Loggable, self).__init__()
        self.code_value = self.pk

    def get_min_load_speed(self):
        args = {self.code_name: self.code_value}
        req_result = Log.objects.filter(**args).aggregate(avg_load_speed=Min('request_time'))
        return req_result['avg_load_speed']

    def get_max_load_speed(self):
        args = {self.code_name: self.code_value}
        req_result = Log.objects.filter(**args).aggregate(avg_load_speed=Max('request_time'))
        return req_result['avg_load_speed']

    def get_min_size_page(self):
        args = {self.code_name: self.code_value}
        req_result = Log.objects.filter(**args).aggregate(min_size_page=Max('body_bytes_sent'))
        return req_result['min_size_page']

    def get_max_size_page(self):
        args = {self.code_name: self.code_value}
        req_result = Log.objects.filter(**args).aggregate(max_size_page=Max('body_bytes_sent'))
        return req_result['max_size_page']

    def get_sources(self):
        return list(Log.objects.filter(id_zds=self.pk)
                    .values('dns_referal')
                    .annotate(total_visits=Count('pk'), unique_visits=Count('remote_addr')))

    def get_countries(self):
        return list(Log.objects.filter(id_zds=self.pk)
                    .values('country')
                    .annotate(total_visits=Count('pk'), unique_visits=Count('remote_addr')))

    def get_cities(self):
        return list(Log.objects.filter(id_zds=self.pk)
                    .values('city')
                    .annotate(total_visits=Count('pk'), unique_visits=Count('remote_addr')))


class Source(models.Model, Dimension):
    """
    Source model
    """
    class Meta:
        verbose_name = 'Stats Source'
        verbose_name_plural = 'Stats Sources'

    def __init__(self, *args, **kwargs):
        self.code_name = 'dns_referal'
        super(Source, self).__init__(*args, **kwargs)
        self.code_value = self.code

    code = models.CharField(u'Source', max_length=80, null=True)


class Country(models.Model, Dimension):
    """
    Country model
    """
    class Meta:
        verbose_name = 'Stats Pays'
        verbose_name_plural = 'Stats Pays'

    def __init__(self, *args, **kwargs):
        self.code_name = 'country'
        super(Country, self).__init__(*args, **kwargs)
        self.code_value = self.code

    code = models.CharField(u'Pays', max_length=80, null=True)


class City(models.Model, Dimension):
    """
    City model
    """
    class Meta:
        verbose_name = 'Stats Ville'
        verbose_name_plural = 'Stats Villes'

    def __init__(self, *args, **kwargs):
        self.code_name = 'city'
        super(City, self).__init__(*args, **kwargs)
        self.code_value = self.code

    code = models.CharField(u'Ville', max_length=80, null=True)


class OS(models.Model, Dimension):
    """
    Operating System model
    """
    class Meta:
        verbose_name = 'Stats OS'

    def __init__(self, *args, **kwargs):
        self.code_name = 'os_family'
        super(OS, self).__init__(*args, **kwargs)
        self.code_value = self.code

    code = models.CharField(u'Système d\'exploitaiton', max_length=80, null=True)


class Browser(models.Model, Dimension):
    """
    Browser model
    """
    class Meta:
        verbose_name = 'Stats navigateur'

    def __init__(self, *args, **kwargs):
        self.code_name = 'browser_family'
        super(Browser, self).__init__(*args, **kwargs)
        self.code_value = self.code

    code = models.CharField(u'Navigateur', max_length=80, null=True)


class Device(models.Model, Dimension):
    """
    Device model
    """
    class Meta:
        verbose_name = 'Stats Device'

    def __init__(self, *args, **kwargs):
        self.code_name = 'device_family'
        super(Device, self).__init__(*args, **kwargs)
        self.code_value = self.code

    code = models.CharField(u'Device', max_length=80, null=True)


@python_2_unicode_compatible
class Log(models.Model):
    """
    Log model
    """
    class Meta:
        verbose_name = 'Log web'
        verbose_name_plural = 'Logs web'

    id_zds = models.IntegerField('Identifiant sur ZdS')
    content_type = models.CharField('Type de contenu', max_length=80)
    hash_code = models.CharField('Hash code de la ligne de log', max_length=80, null=True)
    timestamp = models.DateTimeField('Timestamp', db_index=True)
    remote_addr = models.CharField('Adresse IP', max_length=39, null=True, db_index=True)
    body_bytes_sent = models.IntegerField('Taille de la page')
    dns_referal = models.CharField('Source', max_length=80, null=True)
    os_family = models.CharField('Famille de systeme d\'exploitation', max_length=40, null=True)
    os_version = models.CharField('Version du systeme d\'exploitation', max_length=5, null=True)
    browser_family = models.CharField('Famille du navigateur', max_length=40, null=True)
    browser_version = models.CharField('Version du navigateur', max_length=5, null=True)
    device_family = models.CharField('Famille de device', max_length=20, null=True)
    request_time = models.IntegerField('Temps de chargement de la page')
    country = models.CharField('Pays', max_length=80, null=True)
    city = models.CharField('Ville', max_length=80, null=True)

    def __str__(self):
        return '{}-{}|{}'.format(self.id_zds, self.content_type, self.hash_code)
