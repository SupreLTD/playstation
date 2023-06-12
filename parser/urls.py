from django.urls import path

from . import views

app_name = 'parser'

urlpatterns = [
    path('get_games/', views.games),
    path('get_dlc/', views.games_dlc),
    path('get_dis/', views.games_dis),
    path('go/', views.start),
]