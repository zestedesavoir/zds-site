from django.db import models

from zds.tutorialv2.models.database import PublishableContent


class QuizzQuestion(models.Model):
    url = models.TextField(name="url", verbose_name="url", null=False, blank=False)
    question = models.TextField(name="question", verbose_name="question", null=False, blank=False)
    # use max_length 15 to help with indexation, question type must not be too verbose. You may want to implement
    # choices later
    question_type = models.TextField(
        name="question_type",
        verbose_name="Type de question",
        null=False,
        blank=False,
        default="qcm",
        db_index=True,
        editable=False,
        max_length=15,
    )


class QuizzAvailableAnswer(models.Model):
    label = models.TextField(name="label", verbose_name="Intitulé de la réponse")
    good_answer = models.BooleanField(name="is_good", verbose_name="Est une réponse attendue", default=False)
    related_question = models.ForeignKey(
        QuizzQuestion, name="related_question", verbose_name="Question liée", on_delete=models.CASCADE
    )


class QuizzUserAnswer(models.Model):
    related_content = models.ForeignKey(
        PublishableContent, verbose_name="Tutoriel lié", blank=True, null=True, on_delete=models.CASCADE
    )
    answer = models.TextField(name="answer", verbose_name="answer", null=False, blank=False)
    date_answer = models.DateField(name="date_answer", verbose_name="Date of answer", null=False, auto_now=True)
    related_question = models.ForeignKey(
        QuizzQuestion, name="related_question", verbose_name="Question liée", on_delete=models.CASCADE
    )
    full_answer_id = models.CharField(
        name="full_answer_id",
        verbose_name="Indentifiant de la réponse utilisateur",
        blank=False,
        max_length=64,
        default="id",
    )
