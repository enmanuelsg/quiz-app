from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    text = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=10)  # e.g., "option3"
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.text

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_taken = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField()

    def __str__(self):
        return f'{self.user.username} - {self.date_taken}'

class Answer(models.Model):
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=10)
    is_correct = models.BooleanField()
