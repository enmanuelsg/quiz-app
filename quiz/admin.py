from django.contrib import admin
from .models import Question, QuizAttempt, Answer

admin.site.register(Question)
admin.site.register(QuizAttempt)
admin.site.register(Answer)
