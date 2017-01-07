import os


# create a database table only in unit test mode
if 'testsettings' in os.environ['DJANGO_SETTINGS_MODULE']:
    from django.db import models
    from uuslug import uuslug

    class CoolSlug(models.Model):
        name = models.CharField(max_length=100)
        slug = models.CharField(max_length=200)

        def __unicode__(self):
            return self.name

        def save(self, *args, **kwargs):
            self.slug = uuslug(self.name, instance=self)
            super(CoolSlug, self).save(*args, **kwargs)

    class AnotherSlug(models.Model):
        name = models.CharField(max_length=100)
        slug = models.CharField(max_length=200)

        def __unicode__(self):
            return self.name

        def save(self, *args, **kwargs):
            self.slug = uuslug(self.name, instance=self, start_no=2)
            super(AnotherSlug, self).save(*args, **kwargs)

    class TruncatedSlug(models.Model):
        name = models.CharField(max_length=15)
        slug = models.CharField(max_length=17)

        def __unicode__(self):
            return self.name

        def save(self, *args, **kwargs):
            self.slug = uuslug(self.name, instance=self, start_no=2, max_length=17, word_boundary=False)
            super(TruncatedSlug, self).save(*args, **kwargs)

    class SmartTruncatedSlug(models.Model):
        name = models.CharField(max_length=17)
        slug = models.CharField(max_length=17)

        def __unicode__(self):
            return self.name

        def save(self, *args, **kwargs):
            self.slug = uuslug(self.name, instance=self, start_no=2, max_length=17, word_boundary=True)
            super(SmartTruncatedSlug, self).save(*args, **kwargs)

    class SmartTruncatedExactWordBoundrySlug(models.Model):
        name = models.CharField(max_length=19)
        slug = models.CharField(max_length=19)

        def __unicode__(self):
            return self.name

        def save(self, *args, **kwargs):
            self.slug = uuslug(self.name, instance=self, start_no=9, max_length=19, word_boundary=True)
            super(SmartTruncatedExactWordBoundrySlug, self).save(*args, **kwargs)

    class CoolSlugDifferentSeparator(models.Model):
        name = models.CharField(max_length=100)
        slug = models.CharField(max_length=200)

        def __unicode__(self):
            return self.name

        def save(self, *args, **kwargs):
            self.slug = uuslug(self.name, instance=self, separator='_')
            super(CoolSlugDifferentSeparator, self).save(*args, **kwargs)

    class TruncatedSlugDifferentSeparator(models.Model):
        name = models.CharField(max_length=15)
        slug = models.CharField(max_length=17)

        def __unicode__(self):
            return self.name

        def save(self, *args, **kwargs):
            self.slug = uuslug(self.name, instance=self, start_no=2, max_length=17, word_boundary=False, separator='_')
            super(TruncatedSlugDifferentSeparator, self).save(*args, **kwargs)
