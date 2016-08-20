import os
import sys


def patch_mysql_sql_create_model(original):
    """
    Inspired by github.com/miyagi389/zipcode-django-python - The MIT License - Copyright (c) 2014 miyagi389

    :param :class:`django.db.backends.creation.BaseDatabaseCreation` original: BaseDatabaseCreation
    :return: BaseDatabaseCreation
    :rtype: :class:`django.db.backends.creation.BaseDatabaseCreation`
    """

    def revised(self, model, style, known_models=set()):
        """
        :class:`django.db.backends.creation.BaseDatabaseCreation`
        """

        fullname = self.__module__ + "." + self.__class__.__name__
        if fullname == 'django.db.backends.mysql.creation.DatabaseCreation':
            # the migration will run MySQL
            sql_statements, pending_references = original(self, model, style, known_models)

            final_output = []
            for statement in sql_statements:
                if not statement.startswith('CREATE TABLE'):
                    continue

                end = ''
                if statement.endswith(';'):
                    end = ';'
                    statement = statement[:-1]

                statement += 'ROW_FORMAT=DYNAMIC{}'.format(end)

                final_output.append(statement)

            return final_output, pending_references
        else:
            return original(self, model, style, known_models)

    return revised

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zds.settings")

    if len(sys.argv) > 1 and sys.argv[1] in ['migrate', 'test']:
        from django.db.backends.base.creation import BaseDatabaseCreation
        BaseDatabaseCreation.sql_create_model = patch_mysql_sql_create_model(BaseDatabaseCreation.sql_create_model)

        from django.db.backends.mysql.schema import DatabaseSchemaEditor
        DatabaseSchemaEditor.sql_create_table += ' ROW_FORMAT=DYNAMIC'

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
