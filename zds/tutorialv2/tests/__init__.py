from django.conf import settings
import shutil


class TutorialTestMixin:
    def clean_media_dir(self):
        shutil.rmtree(self.overridden_zds_app['content']['repo_private_path'], ignore_errors=True)
        shutil.rmtree(self.overridden_zds_app['content']['repo_public_path'], ignore_errors=True)
        shutil.rmtree(self.overridden_zds_app['content']['extra_content_watchdog_dir'], ignore_errors=True)
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def tearDown(self):
        self.clean_media_dir()
