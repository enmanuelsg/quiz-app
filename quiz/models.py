from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    quiz_name = models.CharField(max_length=255)
    question_text = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=255)  # Keep existing answer field
    explanation = models.TextField(blank=True)  # Add this new field

    def __str__(self):
        return self.question_text

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


class GeneratedQuiz(models.Model):
    generated_quiz = models.CharField(max_length=255)          # Nombre del quiz
    user = models.ForeignKey(User, on_delete=models.CASCADE)    # Usuario que generó el quiz
    source_text = models.TextField()                             # Texto ingresado por el usuario
    generation_date = models.DateTimeField(auto_now_add=True)    # Fecha de generación
    model_name = models.CharField(max_length=100)                # Modelo/proveedor de IA utilizado
    quiz_data = models.JSONField(null=True, blank=True)          # Preguntas y respuestas en formato JSON

    def __str__(self):
        return self.generated_quiz


