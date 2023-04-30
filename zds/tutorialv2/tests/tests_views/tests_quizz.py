from django.test import TestCase
from zds.tutorialv2.models.quizz import QuizzAvailableAnswer, QuizzQuestion, QuizzUserAnswer
from zds.tutorialv2.tests.factories import QuizzQuestionFactory, QuizzAvailableAnswerFactory, QuizzUserAnswerFactory


class QuizzQuestionTestCase(TestCase):
    def setUp(self):
        self.question_1 = QuizzQuestionFactory()
        self.question_2 = QuizzQuestionFactory()

        self.answer_1 = QuizzAvailableAnswerFactory(related_question=self.question_1, is_good=True)
        self.answer_2 = QuizzAvailableAnswerFactory(related_question=self.question_1, is_good=False)
        self.answer_3 = QuizzAvailableAnswerFactory(related_question=self.question_2, is_good=True)
        self.answer_4 = QuizzAvailableAnswerFactory(related_question=self.question_2, is_good=False)

        self.user_answer_1 = QuizzUserAnswerFactory(related_question=self.question_1)
        self.user_answer_2 = QuizzUserAnswerFactory(related_question=self.question_2)

    def test_question_count(self):
        # Vérifiez qu'il y a bien deux questions créées dans la base de données
        self.assertEqual(QuizzQuestion.objects.count(), 2)

    def test_answer_count(self):
        # Vérifiez qu'il y a bien quatre réponses créées dans la base de données
        self.assertEqual(QuizzAvailableAnswer.objects.count(), 4)

    def test_user_answer_count(self):
        # Vérifiez qu'il y a bien deux réponses d'utilisateur créées dans la base de données
        self.assertEqual(QuizzUserAnswer.objects.count(), 2)

    def test_related_user_answers(self):
        # Vérifiez que les réponses d'utilisateur sont bien liées aux bonnes questions
        self.assertEqual(self.user_answer_1.related_question, self.question_1)
        self.assertEqual(self.user_answer_2.related_question, self.question_2)

    def test_related_answers(self):
        self.assertEqual(self.answer_1.related_question, self.question_1)
        self.assertEqual(self.answer_2.related_question, self.question_1)
        self.assertEqual(self.answer_3.related_question, self.question_2)
        self.assertEqual(self.answer_4.related_question, self.question_2)

    def test_answer_is_good(self):
        # Vérifiez qu'au moins une réponse disponible pour chaque question est marquée comme bonne
        self.assertTrue(self.question_1.quizzavailableanswer_set.filter(is_good=True).exists())
        self.assertTrue(self.question_2.quizzavailableanswer_set.filter(is_good=True).exists())

    def test_user_answer_unique_id(self):
        # Vérifiez que chaque réponse d'utilisateur a un ID unique
        self.assertNotEqual(self.user_answer_1.full_answer_id, self.user_answer_2.full_answer_id)
