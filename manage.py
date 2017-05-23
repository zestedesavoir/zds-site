import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zds.settings')

    from zds.settings import DATABASES

    if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
        from django.db.backends.mysql.schema import DatabaseSchemaEditor
        DatabaseSchemaEditor.sql_create_table += ' ROW_FORMAT=DYNAMIC'

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
