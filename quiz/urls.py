from django.urls import path
from . import views
from .views import user_rankings
from .views import rankings_page
from .views import home
from .views import generate_quiz_view
from .views import quiz_question_view
from .views import generate_quiz_view, start_quiz_view 
from .views import question_view
from .views import result_view


urlpatterns = [
    path('start-quiz/<str:quiz_name>/', start_quiz_view, name='start_quiz'),
    path('result/<str:quiz_name>/', result_view, name='result'),
    path('take-quiz/<str:quiz_name>/question/<int:index>/', question_view, name='question_view'),
    path('generate-quiz/', generate_quiz_view, name='generate_quiz'),
    path('quiz/<str:quiz_name>/', quiz_question_view, name='quiz_question'),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('rankings/', views.rankings_page, name='rankings_page'),    
    path('logout/', views.logout_view, name='logout'),
    path('quiz_selection/', views.quiz_selection, name='quiz_selection'),

]