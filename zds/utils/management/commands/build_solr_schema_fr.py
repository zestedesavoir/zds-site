from io import StringIO
import xml.etree.ElementTree as libxml
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import BaseCommand
from haystack import constants

import sys


class Command(BaseCommand):
    help = 'Generates a Solr schema with french filter that reflects the indexes.'
    base_options = (
        make_option("-f", "--filename", action="store", type="string", dest="filename",
                    help='If provided, directs output to a file instead of stdout.'),
        make_option("-u", "--using", action="store", type="string", dest="using", default=constants.DEFAULT_ALIAS,
                    help='If provided, chooses a connection to work with.'),
    )
    option_list = BaseCommand.option_list + base_options

    def handle(self, *args, **options):
        using = options.get('using')
        filename = options.get('filename')

        command = 'build_solr_schema'

        if using and using != 'default':
            command + ' --using ' + using

        # We need to save the build_solr_schema
        orig_stdout = sys.stdout
        sys.stdout = contentio = StringIO()

        # Call the command
        call_command(command, stdout=contentio)

        # Save the result
        sys.stdout = orig_stdout
        contentio.seek(0)
        content = contentio.getvalue()
        contentio.close()

        # Load the XML
        root = libxml.fromstring(content)

        field_type_french = '    <fieldType name="text_french" class="solr.TextField" positionIncrementGap="100">\n' \
                            '      <analyzer>\n' \
                            '        <tokenizer class="solr.StandardTokenizerFactory" />\n' \
                            '        <filter class="solr.ElisionFilterFactory" ignoreCase="true" ' \
                            '        articles="lang/contractions_fr.txt"/>\n' \
                            '        <filter class="solr.LowerCaseFilterFactory"/>\n' \
                            '        <filter class="solr.StopFilterFactory" ignoreCase="true" ' \
                            '        words="lang/stopwords_fr.txt" format="snowball" />\n' \
                            '        <filter class="solr.FrenchLightStemFilterFactory"/>\n' \
                            '      </analyzer>\n' \
                            '    </fieldType>\n' \

        xml_field_type_french = libxml.fromstring(field_type_french)

        root.find('types').append(xml_field_type_french)

        # Replace all text_en to text_french
        for field in root.find('fields').findall('field'):
            if field.get('type') == 'text_en':
                field.set('type', 'text_french')

        licence = '<?xml version="1.0" ?>\n' \
                  '<!--\n' \
                  '  Licensed to the Apache Software Foundation (ASF) under one or more\n' \
                  '  contributor license agreements.  See the NOTICE file distributed with\n' \
                  '  this work for additional information regarding copyright ownership.\n' \
                  '  The ASF licenses this file to You under the Apache License, Version 2.0\n' \
                  '  (the "License"); you may not use this file except in compliance with\n' \
                  '  the License. You may obtain a copy of the License at\n' \
                  '\n' \
                  '      http://www.apache.org/licenses/LICENSE-2.0\n' \
                  '\n' \
                  '  Unless required by applicable law or agreed to in writing, software\n' \
                  '  distributed under the License is distributed on an "AS IS" BASIS,\n' \
                  '  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n' \
                  '  See the License for the specific language governing permissions and\n' \
                  '  limitations under the License.\n' \
                  '-->\n'

        xml = licence + libxml.tostring(root)

        if filename:
            self.write_file(options.get('filename'), xml)
        else:
            self.stdout.write(xml)

    def write_file(self, filename, schema_xml):
        schema_file = open(filename, 'w')
        schema_file.write(schema_xml)
        schema_file.close()
