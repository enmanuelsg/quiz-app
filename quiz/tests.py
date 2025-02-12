from django.test import TestCase
from django.contrib.auth.models import User
from .models import Question

class QuizTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        Question.objects.create(
            text="What is the capital of France?",
            option1="Berlin",
            option2="Madrid",
            option3="Paris",
            option4="Rome",
            correct_option="option3",
            explanation="Paris is the capital of France."
        )

    def test_question_str(self):
        question = Question.objects.first()
        self.assertEqual(str(question), question.text)

    def test_login_flow(self):
        login = self.client.login(username='testuser', password='password')
        self.assertTrue(login)
