from django.shortcuts import render
from django.http import HttpResponse
from django.core.management import call_command




def games(request):
    response = HttpResponse(open('static/Games.csv'), content_type="application / json ")
    response['Content-Disposition'] = 'attachment; filename="Games.csv"'
    return response

def games_dlc(request):
    response = HttpResponse(open('static/Dlc_games.csv'), content_type="application / json ")
    response['Content-Disposition'] = 'attachment; filename="Dlc_games.csv"'
    return response

def start(request):
    call_command('parser')
    return HttpResponse('Start')

def games_dis(request):
    response = HttpResponse(open('static/Discount_games.csv'), content_type="application / json ")
    response['Content-Disposition'] = 'attachment; filename="Discount_games.csv"'
    return response


