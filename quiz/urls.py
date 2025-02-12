from django.urls import path
from . import views
from .views import user_rankings
from .views import rankings_page
from .views import home

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('rankings/', views.rankings_page, name='rankings_page'),    
    path('', home, name='home'),
    path('rankings/', rankings_page, name='rankings_page'),
    path('api/rankings/', user_rankings, name='user_rankings'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('quiz_selection/', views.quiz_selection, name='quiz_selection'),
    path('start_quiz/', views.start_quiz, name='start_quiz'),
    path('quiz_question/', views.quiz_question, name='quiz_question'),
]