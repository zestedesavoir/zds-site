from django.conf import settings
import os
import shutil


class TutorialTestMixin:
    def clean_media_dir(self):
        if os.path.isdir(self.overridden_zds_app['content']['repo_private_path']):
            shutil.rmtree(self.overridden_zds_app['content']['repo_private_path'])
        if os.path.isdir(self.overridden_zds_app['content']['repo_public_path']):
            shutil.rmtree(self.overridden_zds_app['content']['repo_public_path'])
        if os.path.isdir(self.overridden_zds_app['content']['extra_content_watchdog_dir']):
            shutil.rmtree(self.overridden_zds_app['content']['extra_content_watchdog_dir'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

    def tearDown(self):
        self.clean_media_dir()
