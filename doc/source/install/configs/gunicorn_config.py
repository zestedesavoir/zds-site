command = '/opt/zds/zdsenv/bin/gunicorn'
pythonpath = '/opt/zds/zds-site'
bind = 'unix:/opt/zds/zdsenv/bin/gunicorn.sock'
workers = 7
user = 'zds'
group = 'zds'
errorlog = '/var/log/zds/gunicorn_error.log'
loglevel = 'info'
pid = '/opt/zds/gunicorn.pid'

