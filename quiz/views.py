from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from django.contrib import messages
from .models import GeneratedQuiz
from services.ai_integration import generate_quiz


from .forms import RegistrationForm
from .models import Question, QuizAttempt, Answer
import random


def home(request):
    return render(request, 'home.html')

def rankings_page(request):
    return render(request, 'quiz/rankings.html')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('quiz_selection')
    else:
        form = RegistrationForm()
    return render(request, 'quiz/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('quiz_selection')
        else:
            error = "Invalid username or password."
            return render(request, 'quiz/login.html', {'error': error})
    return render(request, 'quiz/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def quiz_selection(request):
    return render(request, 'quiz/quiz_selection.html')

@login_required
def start_quiz(request):
    question_ids = list(Question.objects.values_list('id', flat=True))
    if len(question_ids) < 5:
        return render(request, 'quiz/quiz_selection.html', {'error': 'Not enough questions.'})

    # Create QuizAttempt and force session save
    attempt = QuizAttempt.objects.create(user=request.user, score=0)
    request.session['quiz_attempt_id'] = attempt.id
    request.session.modified = True  # Force session to save

    selected_ids = random.sample(question_ids, 5)
    request.session['quiz_questions'] = selected_ids
    request.session['current_question'] = 0
    request.session['score'] = 0  # Optional: Can now be removed since score is calculated from DB

    return redirect('quiz_question')

@login_required
def quiz_question(request):
    # Validate session data first
    quiz_questions = request.session.get('quiz_questions')
    quiz_attempt_id = request.session.get('quiz_attempt_id')
    current_index = request.session.get('current_question', 0)

    # Redirect to start if session is invalid
    if not quiz_questions or not quiz_attempt_id:
        return redirect('start_quiz')

    # Handle completed quiz
    if current_index >= len(quiz_questions):
        try:
            attempt = QuizAttempt.objects.get(id=quiz_attempt_id)
            # Calculate score from actual answers
            attempt.score = attempt.answers.filter(is_correct=True).count()
            attempt.save()
            # Cleanup session
            for key in ['quiz_questions', 'current_question', 'quiz_attempt_id', 'score']:
                if key in request.session:
                    del request.session[key]
            return render(request, 'quiz/result.html', {'score': attempt.score})
        except QuizAttempt.DoesNotExist:
            # Handle invalid attempt ID
            return redirect('start_quiz')

    # Get current question
    question_id = quiz_questions[current_index]
    question = get_object_or_404(Question, id=question_id)

    # Process answer submission
    if request.method == 'POST':
        selected_option = request.POST.get('option')
        is_correct = (selected_option == question.correct_option)

        try:
            # Save answer to database
            attempt = QuizAttempt.objects.get(id=quiz_attempt_id)
            Answer.objects.create(
                quiz_attempt=attempt,
                question=question,
                selected_option=selected_option,
                is_correct=is_correct
            )
        except QuizAttempt.DoesNotExist:
            return redirect('start_quiz')

        # Prepare feedback and advance
        request.session['current_question'] = current_index + 1
        feedback = 'Correct!' if is_correct else f'Incorrect. The right answer was {question.correct_option}'
        return render(request, 'quiz/question.html', {
            'question': question,
            'feedback': feedback,
            'answered': True
        })

    # Display unanswered question
    return render(request, 'quiz/question.html', {'question': question})


def user_rankings(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT au.username,
                COUNT(au.username) as total_quiz,
                SUM(qa.is_correct) as correct_quiz,
                ROUND(AVG(qa.is_correct), 2) as score
            FROM quiz_answer qa
            INNER JOIN quiz_quizattempt qq ON qa.quiz_attempt_id = qq.id
            INNER JOIN auth_user au ON qq.user_id = au.id
            GROUP BY au.username
            ORDER BY score DESC;
        """)
        columns = [col[0] for col in cursor.description]
        rankings = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"rankings": rankings})





def generate_quiz_view(request):
    if request.method == "POST":
        quiz_name = request.POST.get("quiz_name")
        source_text = request.POST.get("source_text")

        if not quiz_name or not source_text:
            messages.error(request, "Debes ingresar un nombre y un texto.")
            return redirect("quiz_selection")

        # Llamada a la API de IA
        quiz_data = generate_quiz(source_text, quiz_name)
        if quiz_data is None:
            messages.error(request, "Error al generar el quiz con IA. Intenta nuevamente.")
            return redirect("quiz_selection")

        # (Opcional) Guardar el registro completo del quiz generado por IA
        GeneratedQuiz.objects.create(
            generated_quiz=quiz_name,
            user=request.user,
            source_text=source_text,
            model_name="OpenAI gpt-3.5-turbo",
            quiz_data=quiz_data
        )

        # Iterar sobre las preguntas generadas y crear objetos Question
        for q in quiz_data.get("questions", []):
            options = q.get("options", [])
            if len(options) < 4:
                continue  # O bien manejar el error de formato
            Question.objects.create(
                quiz_name=quiz_name,
                question_text=q.get("question"),
                option1=options[0],
                option2=options[1],
                option3=options[2],
                option4=options[3],
                correct_option=q.get("answer")
            )

        messages.success(request, "Quiz generado correctamente. Presiona 'Start Quiz' para comenzar.")
        # Redirige a la vista que inicia el quiz; se asume que usa el parámetro quiz_name para buscar las preguntas
        return redirect("start_quiz", quiz_name=quiz_name)
    else:
        return render(request, "quiz/quiz_selection.html")



def quiz_question_view(request, quiz_name):
    quiz = get_object_or_404(GeneratedQuiz, generated_quiz=quiz_name)
    return render(request, "quiz/quiz_question.html", {"quiz": quiz.quiz_data})



def start_quiz_view_old(request, quiz_name):
    # Obtenemos la primera pregunta (o la siguiente según tu lógica)
    question = Question.objects.filter(quiz_name=quiz_name).first()

    if not question:
        messages.error(request, "No hay preguntas para este quiz.")
        return redirect("quiz_selection")  # Ajusta a tu URL de selección

    # Opcional: Determinar si ya se respondió
    answered = False
    feedback = ""

    # Si la solicitud es POST, manejamos la respuesta
    if request.method == "POST":
        selected_option = request.POST.get("option")
        if selected_option:
            # Comparamos la opción elegida con la correcta
            if selected_option == question.correct_option:
                feedback = "Correct!"
            else:
                feedback = f"Incorrect. La respuesta correcta era {question.correct_option}."
            answered = True

    context = {
        "question": question,     # Enviamos UN solo objeto
        "answered": answered,
        "feedback": feedback
    }
    return render(request, "quiz/question.html", context)



def start_quiz_view(request, quiz_name):
    """
    Prepara el quiz, guarda en la sesión las preguntas que se deben contestar y redirige a la primera.
    """
    # Filtra las preguntas asociadas al quiz
    questions_qs = Question.objects.filter(quiz_name=quiz_name)

    if not questions_qs.exists():
        messages.error(request, f"No hay preguntas para el quiz '{quiz_name}'.")
        return redirect('quiz_selection')

    # Guarda en sesión la lista de IDs de preguntas, en orden
    request.session['question_ids'] = list(questions_qs.values_list('id', flat=True))
    request.session['current_index'] = 0  # Empezar en la primera pregunta

    # Redirige a la vista que mostrará la primera pregunta
    return redirect('question_view', quiz_name=quiz_name, index=0)


def question_view(request, quiz_name, index):
    """
    Muestra la pregunta con índice 'index' y maneja la respuesta del usuario.
    """
    question_ids = request.session.get('question_ids', [])

    # Si el índice excede el total de preguntas, podemos mostrar resultados o volver al menú
    if index >= len(question_ids):
        messages.info(request, "Has completado el quiz.")
        return redirect('quiz_selection')

    # Recuperar la pregunta correspondiente al índice
    question_id = question_ids[index]
    question = get_object_or_404(Question, id=question_id)

    # Si el usuario envía la respuesta
    if request.method == 'POST':
        selected_option = request.POST.get('option')
        if selected_option:
            # Ejemplo: comparar con question.correct_option
            if selected_option == question.correct_option:
                messages.success(request, "¡Respuesta correcta!")
            else:
                messages.error(request, "Respuesta incorrecta.")
        else:
            messages.warning(request, "Debes seleccionar una opción.")

        # Pasar a la siguiente pregunta
        next_index = index + 1
        return redirect('question_view', quiz_name=quiz_name, index=next_index)

    # Renderizar la plantilla con la pregunta actual
    context = {
        'quiz_name': quiz_name,
        'question': question,
        'index': index,
        # Puedes pasar más variables si necesitas
    }
    return render(request, 'quiz/question.html', context)
