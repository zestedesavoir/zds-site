import os
import sys


def patch_create_suffix(original):
    """
    Patch mysql creation policy to handle the "utf8mb4" facility. This appears tricky but it's necessary
    due to the conception of "extended utf-8" in mysql. If we do not patch, the mysql backend is not even run !
    see <http://bd808.com/blog/2017/04/17/making-django-migrations-that-work-with-mysql-55-and-utf8mb4/>
    for explanations

    :param original: the original function we are patching
    :return: the patched function
    """
    def patch(self):
        return original(self) + 'ROW_FORMAT=DYNAMIC'
    return patch


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zds.settings')

    if len(sys.argv) > 1 and sys.argv[1] in ['migrate', 'test']:

        from django.db.backends.mysql.creation import BaseDatabaseCreation

        BaseDatabaseCreation.sql_table_creation_suffix = \
            patch_create_suffix(BaseDatabaseCreation.sql_table_creation_suffix)
        from django.db.backends.mysql.schema import DatabaseSchemaEditor

        DatabaseSchemaEditor.sql_create_table += ' ROW_FORMAT=DYNAMIC'
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
