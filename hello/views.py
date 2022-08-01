from django.shortcuts import render
from django.http import HttpResponse
import os
import psycopg2
from .models import Greeting
from .models import Player

# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")

def leaderboard(request):
    host=os.environ.get('DB_HOST')
    database=os.environ.get('DB_NAME')
    user=os.environ.get('DB_USER')
    password=os.environ.get('DB_PASS')
    db_conn = psycopg2.connect(host=host, dbname=database, user=user, password=password)
    db_cursor = db_conn.cursor()
    players = []
    cmd = "Select * from players;"
    db_cursor.execute(cmd)
    try:
        array_players = db_cursor.fetchall()
    except psycopg2.Error as e:
        t_error_message = "Database error: " + e + "/n SQL: " + cmd
        return render(request, "error_report.html", {"t_error_message" : t_error_message})
    for i in array_players:
        player = Player(i[1],i[2],i[3],i[4],i[5])
        players.append(player)

    return render(request, "leaderboard.html", {"t_title" : "Test", "array_players" : players})
def db(request):
    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})
