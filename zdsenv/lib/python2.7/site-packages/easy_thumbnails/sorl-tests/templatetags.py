import os
from django.conf import settings
from django.template import Template, Context, TemplateSyntaxError
from easy_thumbnails.tests.classes import BaseTest, RELATIVE_PIC_NAME


class ThumbnailTagTest(BaseTest):
    def render_template(self, source):
        context = Context({
            'source': RELATIVE_PIC_NAME,
            'invalid_source': 'not%s' % RELATIVE_PIC_NAME,
            'size': (90, 100),
            'invalid_size': (90, 'fish'),
            'strsize': '80x90',
            'invalid_strsize': ('1notasize2'),
            'invalid_q': 'notanumber'})
        source = '{% load thumbnail %}' + source
        return Template(source).render(context)

    def testTagInvalid(self):
        # No args, or wrong number of args
        src = '{% thumbnail %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)
        src = '{% thumbnail source %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)
        src = '{% thumbnail source 80x80 as variable crop %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Invalid option
        src = '{% thumbnail source 240x200 invalid %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Old comma separated options format can only have an = for quality
        src = '{% thumbnail source 80x80 crop=1,quality=1 %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Invalid quality
        src_invalid = '{% thumbnail source 240x200 quality=invalid_q %}'
        src_missing = '{% thumbnail source 240x200 quality=missing_q %}'
        # ...with THUMBNAIL_DEBUG = False
        self.assertEqual(self.render_template(src_invalid), '')
        self.assertEqual(self.render_template(src_missing), '')
        # ...and with THUMBNAIL_DEBUG = True
        self.change_settings.change({'DEBUG': True})
        self.assertRaises(TemplateSyntaxError, self.render_template,
                          src_invalid)
        self.assertRaises(TemplateSyntaxError, self.render_template,
                          src_missing)

        # Invalid source
        src = '{% thumbnail invalid_source 80x80 %}'
        src_on_context = '{% thumbnail invalid_source 80x80 as thumb %}'
        # ...with THUMBNAIL_DEBUG = False
        self.change_settings.change({'DEBUG': False})
        self.assertEqual(self.render_template(src), '')
        # ...and with THUMBNAIL_DEBUG = True
        self.change_settings.change({'DEBUG': True})
        self.assertRaises(TemplateSyntaxError, self.render_template, src)
        self.assertRaises(TemplateSyntaxError, self.render_template,
                          src_on_context)

        # Non-existant source
        src = '{% thumbnail non_existant_source 80x80 %}'
        src_on_context = '{% thumbnail non_existant_source 80x80 as thumb %}'
        # ...with THUMBNAIL_DEBUG = False
        self.change_settings.change({'DEBUG': False})
        self.assertEqual(self.render_template(src), '')
        # ...and with THUMBNAIL_DEBUG = True
        self.change_settings.change({'DEBUG': True})
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Invalid size as a tuple:
        src = '{% thumbnail source invalid_size %}'
        # ...with THUMBNAIL_DEBUG = False
        self.change_settings.change({'DEBUG': False})
        self.assertEqual(self.render_template(src), '')
        # ...and THUMBNAIL_DEBUG = True
        self.change_settings.change({'DEBUG': True})
        self.assertRaises(TemplateSyntaxError, self.render_template, src)
        # Invalid size as a string:
        src = '{% thumbnail source invalid_strsize %}'
        # ...with THUMBNAIL_DEBUG = False
        self.change_settings.change({'DEBUG': False})
        self.assertEqual(self.render_template(src), '')
        # ...and THUMBNAIL_DEBUG = True
        self.change_settings.change({'DEBUG': True})
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Non-existant size
        src = '{% thumbnail source non_existant_size %}'
        # ...with THUMBNAIL_DEBUG = False
        self.change_settings.change({'DEBUG': False})
        self.assertEqual(self.render_template(src), '')
        # ...and THUMBNAIL_DEBUG = True
        self.change_settings.change({'DEBUG': True})
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

    def testTag(self):
        expected_base = RELATIVE_PIC_NAME.replace('.', '_')
        # Set DEBUG = True to make it easier to trace any failures
        self.change_settings.change({'DEBUG': True})

        # Basic
        output = self.render_template('src="'
            '{% thumbnail source 240x240 %}"')
        expected = '%s_240x240_q85.jpg' % expected_base
        expected_fn = os.path.join(settings.MEDIA_ROOT, expected)
        self.verify_thumbnail((240, 180), expected_filename=expected_fn)
        expected_url = ''.join((settings.MEDIA_URL, expected))
        self.assertEqual(output, 'src="%s"' % expected_url)

        # Size from context variable
        # as a tuple:
        output = self.render_template('src="'
            '{% thumbnail source size %}"')
        expected = '%s_90x100_q85.jpg' % expected_base
        expected_fn = os.path.join(settings.MEDIA_ROOT, expected)
        self.verify_thumbnail((90, 67), expected_filename=expected_fn)
        expected_url = ''.join((settings.MEDIA_URL, expected))
        self.assertEqual(output, 'src="%s"' % expected_url)
        # as a string:
        output = self.render_template('src="'
            '{% thumbnail source strsize %}"')
        expected = '%s_80x90_q85.jpg' % expected_base
        expected_fn = os.path.join(settings.MEDIA_ROOT, expected)
        self.verify_thumbnail((80, 60), expected_filename=expected_fn)
        expected_url = ''.join((settings.MEDIA_URL, expected))
        self.assertEqual(output, 'src="%s"' % expected_url)

        # On context
        output = self.render_template('height:'
            '{% thumbnail source 240x240 as thumb %}{{ thumb.height }}')
        self.assertEqual(output, 'height:180')

        # With options and quality
        output = self.render_template('src="'
            '{% thumbnail source 240x240 sharpen crop quality=95 %}"')
        # Note that the opts are sorted to ensure a consistent filename.
        expected = '%s_240x240_crop_sharpen_q95.jpg' % expected_base
        expected_fn = os.path.join(settings.MEDIA_ROOT, expected)
        self.verify_thumbnail((240, 240), expected_filename=expected_fn)
        expected_url = ''.join((settings.MEDIA_URL, expected))
        self.assertEqual(output, 'src="%s"' % expected_url)

        # With option and quality on context (also using its unicode method to
        # display the url)
        output = self.render_template(
            '{% thumbnail source 240x240 sharpen crop quality=95 as thumb %}'
            'width:{{ thumb.width }}, url:{{ thumb }}')
        self.assertEqual(output, 'width:240, url:%s' % expected_url)

        # Old comma separated format for options is still supported.
        output = self.render_template(
            '{% thumbnail source 240x240 sharpen,crop,quality=95 as thumb %}'
            'width:{{ thumb.width }}, url:{{ thumb }}')
        self.assertEqual(output, 'width:240, url:%s' % expected_url)
