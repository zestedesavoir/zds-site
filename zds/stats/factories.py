# coding: utf-8

from faker import Factory

from zds.tutorialv2.models.models_database import PublishedContent


class LogRandomFactory():
    remote_addr = ''
    remote_user = ''
    time_local = ''
    request = ''
    status = ''
    body_bytes_sent = ''
    http_referer = ''
    http_user_agent = ''
    http_x_forwarded_for = ''
    request_time = ''
    upstream_response_time = ''
    pipe = ''

    def __init__(self):
        fake = Factory.create(locale='fr_FR')
        self.remote_addr = fake.random_element(elements=(fake.ipv4(), fake.ipv6()))
        self.remote_user = fake.user_name()
        self.time_local = '{}:{} {}'.format(fake.date(pattern='%d/%b/%Y'),
                                            fake.time(pattern='%H:%M:%S'), fake.timezone())
        pub_content1 = PublishedContent.objects.filter(content_type='ARTICLE',
                                                       sha_public__isnull=False).order_by('?').first()
        pub_content2 = PublishedContent.objects.filter(content_type='TUTORIAL',
                                                       sha_public__isnull=False).order_by('?').first()
        pub_full = [pub_content1, pub_content2]

        fake_content = fake.random_element(elements=pub_full)
        if not fake_content:
            fake_url = '/'
        else:
            fake_url = fake_content.get_absolute_url_online()

        self.request = '{} {} {}'.format(fake.random_element(elements=('GET', 'POST')),
                                         fake_url,
                                         fake.random_element(elements=('HTTP/1.0', 'HTTP/1.1')))
        self.status = fake.random_element(elements=('404', '200', '403'))
        self.body_bytes_sent = fake.pyint()
        self.http_referer = fake.random_element(elements=('/', fake.uri()))
        self.http_user_agent = fake.user_agent()
        self.http_x_forwarded_for = '-'
        self.request_time = fake.pyint()
        self.upstream_response_time = fake.pyint()
        self.pipe = fake.random_element(elements=('.', 'P'))

    def __str__(self):
        return u'{0} - {1} [{2}] \"{3}\" {4} {5} \"{6}\" \"{7}\" \"{8}\" {9} {10} {11}'. format(
            self.remote_addr,
            self.remote_user,
            self.time_local,
            self.request,
            self.status,
            self.body_bytes_sent,
            self.http_referer,
            self.http_user_agent,
            self.http_x_forwarded_for,
            self.request_time,
            self.upstream_response_time,
            self.pipe)


class LogFactory():
    remote_addr = ''
    remote_user = ''
    time_local = ''
    request = ''
    status = ''
    body_bytes_sent = ''
    http_referer = ''
    http_user_agent = ''
    http_x_forwarded_for = ''
    request_time = ''
    upstream_response_time = ''
    pipe = ''

    def __init__(self, pk, type_content=None, source=None, uagent=None, ip=None):
        fake = Factory.create(locale='fr_FR')
        if source is None:
            source = '/'
        if uagent is None:
            uagent = fake.user_agent()
        if ip is None:
            ip = fake.random_element(elements=(fake.ipv4(), fake.ipv6()))
        self.remote_addr = ip
        self.remote_user = fake.user_name()
        self.time_local = '{}:{} {}'.format(fake.date(pattern='%d/%b/%Y'),
                                            fake.time(pattern='%H:%M:%S'),
                                            fake.timezone())

        if type_content:
            fake_content = PublishedContent.objects.filter(content_pk=pk, content_type=type_content).first()
        else:
            fake_content = None

        if fake_content is None:
            fake_url = '/'
        else:
            fake_url = fake_content.get_absolute_url_online()

        self.request = '{} {} {}'.format('GET', fake_url, 'HTTP/1.0')
        self.status = '200'
        self.body_bytes_sent = fake.pyint()
        self.http_referer = source
        self.http_user_agent = uagent
        self.http_x_forwarded_for = '-'
        self.request_time = fake.pyint()
        self.upstream_response_time = fake.pyint()
        self.pipe = 'P'

    def __str__(self):
        return u'{0} - {1} [{2}] \"{3}\" {4} {5} \"{6}\" \"{7}\" \"{8}\" {9} {10} {11}'. format(
            self.remote_addr,
            self.remote_user,
            self.time_local,
            self.request,
            self.status,
            self.body_bytes_sent,
            self.http_referer,
            self.http_user_agent,
            self.http_x_forwarded_for,
            self.request_time,
            self.upstream_response_time,
            self.pipe)
