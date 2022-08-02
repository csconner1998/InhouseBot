from django.shortcuts import render
from django.http import HttpResponse
import os
import psycopg2
from .models import Player
from .models import Match
from decouple import config
def index(request):
    return render(request, "index.html", {"home":'active'})

def matchhistory(request):
    host=config('DB_HOST')
    database=config('DB_NAME')
    user=config('DB_USER')
    password=config('DB_PASS')
    db_conn = psycopg2.connect(host=host, dbname=database, user=user, password=password)
    db_cursor = db_conn.cursor()
    matches = []
    cmd = "SELECT match_id, name, blue, winner, roles.role, matches.created FROM matches_players INNER JOIN players ON matches_players.player_id = players.id inner join matches on matches_players.match_id = matches.matchid inner join roles on matches_players.role = roles.roleid ORDER BY matches.matchid DESC, blue DESC;"
    db_cursor.execute(cmd)
    try:
        array_matches = db_cursor.fetchall()
    except psycopg2.Error as e:
        t_error_message = "Database error: " + e + "/n SQL: " + cmd
        return render(request, "error_report.html", {"t_error_message" : t_error_message})
    for i in range(len(array_matches)):
        if i % 10 == 0:
            match = Match(array_matches[i][0],array_matches[i][3],array_matches[i][5])
        match.addPlayer(array_matches[i][1],array_matches[i][4],array_matches[i][2])
        if i % 10 == 9:
            match.makeList()
            matches.append(match)

    db_conn.close()
    # return render(request, "leaderboard.html", {"t_title" : "Test", "array_players" : players, 'leaderboard' : "active"})
    return render(request, "matchhistory.html", {"matchhistory":'active', "matches":matches})

def leaderboard(request):
    host=config('DB_HOST')
    database=config('DB_NAME')
    user=config('DB_USER')
    password=config('DB_PASS')
    db_conn = psycopg2.connect(host=host, dbname=database, user=user, password=password)
    db_cursor = db_conn.cursor()
    players = []
    cmd = "Select * from players order by sp DESC;"
    db_cursor.execute(cmd)
    try:
        array_players = db_cursor.fetchall()
    except psycopg2.Error as e:
        t_error_message = "Database error: " + e + "/n SQL: " + cmd
        return render(request, "error_report.html", {"t_error_message" : t_error_message})
    for i in array_players:
        player = Player(i[1],i[2],i[3],i[4],i[5])
        players.append(player)
    db_conn.close()
    return render(request, "leaderboard.html", {"t_title" : "Test", "array_players" : players, 'leaderboard' : "active"})