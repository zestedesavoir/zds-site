from django.db import models

from zds.tutorialv2.models.database import PublishableContent


class QuizzStat(models.Model):
    related_content = models.ForeignKey(PublishableContent,
                              verbose_name='Tutoriel lié',
                              blank=True, null=True,
                              on_delete=models.CASCADE)
    url = models.TextField(name='url', verbose_name='url', null=False, blank=False)
    question = models.TextField(name="question", verbose_name="question", null=False, blank=False)
    answer = models.TextField(name="answer", verbose_name="anwser", null=False, blank=False)
