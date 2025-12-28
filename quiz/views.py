import logging
from django.db import transaction
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


logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def quiz_question(request):
    # Validate session data first
    quiz_questions = request.session.get('quiz_questions')
    quiz_attempt_id = request.session.get('quiz_attempt_id')
    current_index = request.session.get('current_question', 0)

    logger.info(f"Quiz Session Data - Questions: {quiz_questions}, Attempt ID: {quiz_attempt_id}, Current Index: {current_index}")

    # Redirect to start if session is invalid
    if not quiz_questions or not quiz_attempt_id:
        logger.warning("Invalid quiz session data. Redirecting to start.")
        messages.error(request, "Quiz session expired. Please start again.")
        return redirect('start_quiz')

    # Handle completed quiz
    if current_index >= len(quiz_questions):
        try:
            with transaction.atomic():
                attempt = QuizAttempt.objects.select_for_update().get(id=quiz_attempt_id)
                # Calculate score based on stored answers
                attempt.score = attempt.answers.filter(is_correct=True).count()
                attempt.save()

                # Clean up session data
                for key in ['quiz_questions', 'current_question', 'quiz_attempt_id', 'score']:
                    if key in request.session:
                        del request.session[key]

                logger.info(f"Quiz completed. User {request.user.username}, Score: {attempt.score}")
                return render(request, 'quiz/result.html', {'score': attempt.score})
        except QuizAttempt.DoesNotExist:
            logger.error(f"Quiz attempt not found. Attempt ID: {quiz_attempt_id}")
            messages.error(request, "Quiz attempt not found. Please start again.")
            return redirect('start_quiz')
        except Exception as e:
            logger.critical(f"Unexpected error in quiz completion: {e}")
            messages.error(request, "An unexpected error occurred. Please try again.")
            return redirect('start_quiz')

    # Get current question
    try:
        question_id = quiz_questions[current_index]
        question = get_object_or_404(Question, id=question_id)
    except IndexError:
        logger.error(f"Invalid question index. Current index: {current_index}")
        messages.error(request, "Invalid quiz progression. Please start again.")
        return redirect('start_quiz')

    # Process answer submission
    if request.method == 'POST':
        selected_option = request.POST.get('option')
        
        if not selected_option:
            logger.warning("No option selected")
            messages.warning(request, "Please select an answer.")
            return render(request, 'quiz/question.html', {'question': question})

        is_correct = (selected_option == question.correct_option)

        try:
            with transaction.atomic():
                attempt = QuizAttempt.objects.select_for_update().get(id=quiz_attempt_id)
                
                # Save the answer, using get_or_create to avoid duplicate entries
                answer, created = Answer.objects.get_or_create(
                    quiz_attempt=attempt,
                    question=question,
                    defaults={
                        'selected_option': selected_option,
                        'is_correct': is_correct
                    }
                )
                logger.info(f"Answer created: {answer} (created: {created})")
                print(f"--> Answer created: {answer} (created: {created})")
                if not created:
                    logger.warning(f"Duplicate answer detected for question {question.id}")

                # Update session for the next question
                request.session['current_question'] = current_index + 1
        except QuizAttempt.DoesNotExist:
            logger.error(f"Quiz attempt not found during answer submission. Attempt ID: {quiz_attempt_id}")
            messages.error(request, "Quiz session expired. Please start again.")
            return redirect('start_quiz')
        except Exception as e:
            logger.critical(f"Unexpected error in answer submission: {e}")
            messages.error(request, "An unexpected error occurred while processing your answer.")
            return redirect('start_quiz')
        
        # Set feedback message using Django's messages framework
        feedback = "Correct!" if is_correct else f"Incorrect. The right answer was {question.correct_option}."
        messages.info(request, feedback)
        return redirect('quiz_question')
    
    # Display unanswered question on GET
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
                correct_option=q.get("answer"),
                explanation=q.get("explanation", "")  # Add this line
            )

        messages.success(request, "Quiz generado correctamente. Presiona 'Start Quiz' para comenzar.")
        # Redirige a la vista que inicia el quiz; se asume que usa el parámetro quiz_name para buscar las preguntas
        return redirect("start_quiz", quiz_name=quiz_name)
    else:
        return render(request, "quiz/quiz_selection.html")



def quiz_question_view(request, quiz_name):
    quiz = get_object_or_404(GeneratedQuiz, generated_quiz=quiz_name)
    return render(request, "quiz/quiz_question.html", {"quiz": quiz.quiz_data})



def start_quiz_view(request, quiz_name):
    """
    Prepara el quiz: guarda en sesión los IDs de las preguntas, crea un QuizAttempt persistente
    y redirige a la primera pregunta.
    """
    questions_qs = Question.objects.filter(quiz_name=quiz_name)
    if not questions_qs.exists():
        messages.error(request, f"No hay preguntas para el quiz '{quiz_name}'.")
        return redirect('quiz_selection')

    request.session['question_ids'] = list(questions_qs.values_list('id', flat=True))
    request.session['current_score'] = 0
    request.session['total_questions'] = questions_qs.count()
    request.session['quiz_name'] = quiz_name

    # Crear un QuizAttempt persistente si el usuario está autenticado
    if request.user.is_authenticated:
        attempt = QuizAttempt.objects.create(user=request.user, score=0)
        request.session['quiz_attempt_id'] = attempt.id

    return redirect('question_view', quiz_name=quiz_name, index=0)



def question_view(request, quiz_name, index):
    # Recupera la lista de IDs guardada en la sesión
    question_ids = request.session.get('question_ids', [])
    if index >= len(question_ids):
        return redirect('result', quiz_name=quiz_name)
    
    # Obtiene la pregunta actual
    question = get_object_or_404(Question, id=question_ids[index])
    
    # Si se envía una respuesta
    if request.method == 'POST':
        selected_option = request.POST.get('option')
        if not selected_option:
            messages.warning(request, "Debes seleccionar una opción.")
            context = {
                'quiz_name': quiz_name,
                'question': question,
                'index': index
            }
            return render(request, 'quiz/question.html', context)
        else:
            # Determinar si es correcta
            is_correct = (selected_option == question.correct_option)

            # Guardar/actualizar Answer si existe un QuizAttempt creado
            attempt_id = request.session.get('quiz_attempt_id')
            if attempt_id:
                try:
                    attempt = QuizAttempt.objects.get(id=attempt_id)
                    Answer.objects.update_or_create(
                        quiz_attempt=attempt,
                        question=question,
                        defaults={
                            'selected_option': selected_option,
                            'is_correct': is_correct
                        }
                    )
                except QuizAttempt.DoesNotExist:
                    # Si no existe el intento en DB, podemos ignorar o loggear
                    pass

            # Actualizar score en sesión (UX inmediata)
            if is_correct:
                request.session['current_score'] = request.session.get('current_score', 0) + 1

            # Si era la última pregunta, calcular y persistir score final en QuizAttempt
            if index + 1 >= len(question_ids):
                if attempt_id:
                    try:
                        attempt = QuizAttempt.objects.get(id=attempt_id)
                        attempt.score = attempt.answers.filter(is_correct=True).count()
                        attempt.save()
                    except QuizAttempt.DoesNotExist:
                        pass

            # Definir el feedback y renderizar la misma página con feedback
            if is_correct:
                feedback = "¡Respuesta correcta!"
            else:
                feedback = "Respuesta incorrecta."
            
            context = {
                'quiz_name': quiz_name,
                'question': question,
                'index': index,
                'feedback': feedback
            }
            return render(request, 'quiz/question.html', context)
    
    # En GET, muestra la pregunta sin feedback
    context = {
        'quiz_name': quiz_name,
        'question': question,
        'index': index
    }
    return render(request, 'quiz/question.html', context)


def result_view(request, quiz_name):
    """
    Muestra la página de resultados cuando se completa el quiz.
    Si existe un QuizAttempt en sesión, lee el resultado desde la DB (más confiable).
    """
    attempt_id = request.session.get('quiz_attempt_id')
    if attempt_id:
        try:
            attempt = QuizAttempt.objects.get(id=attempt_id)
            total = attempt.answers.count() or request.session.get('total_questions', 0)
            score = attempt.score
            context = {
                'quiz_name': quiz_name,
                'total_questions': total,
                'score': score,
            }
            # Limpiar datos de sesión del quiz
            for key in ['question_ids', 'current_score', 'total_questions', 'quiz_name', 'quiz_attempt_id']:
                if key in request.session:
                    del request.session[key]
            return render(request, 'quiz/result.html', context)
        except QuizAttempt.DoesNotExist:
            # fallback a valores en sesión si por algún motivo no encontramos el intento
            pass

    # Fallback: usar valores en sesión
    total = request.session.get('total_questions', 0)
    score = request.session.get('current_score', 0)
    context = {
        'quiz_name': quiz_name,
        'total_questions': total,
        'score': score,
    }
    # limpiar session keys usadas por este flujo
    for key in ['question_ids', 'current_score', 'total_questions', 'quiz_name', 'quiz_attempt_id']:
        if key in request.session:
            del request.session[key]
    return render(request, 'quiz/result.html', context)