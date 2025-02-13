from logging import StrFormatStyle
import requests
import chess.engine
import io
import chess.pgn
from flask import Flask, jsonify, after_this_request, request
from flask import render_template
from flask_cors import CORS

import lichess.api
import lichess.pgn
import re
import requests
from lichess.format import SINGLE_PGN
from datetime import datetime


app = Flask(__name__)
CORS(app)

engine = chess.engine.SimpleEngine.popen_uci("stockfish_13_win_x64.exe")


@app.route('/')
def render_index():
    return render_template('index.html')


@app.route('/homepage')
def render_homepage():
    return render_template('homepage.html')


# chess.com implementation
@app.route('/api/chess/<name>/<year>/<month>/', methods=['GET'])
def get_games_no_opponent(name, year, month):
    # @after_this_request
    # def add_header(response):
    # response.headers['Access-Control-Allow-Origin'] = '*'
    # return response

    api_result = {}

    games_raw = requests.get(f"https://api.chess.com/pub/player/{name}/games/{year}/{month}")
    count =0
    
    wCastle = True
    bCastle = True
    for i in range(0, len(games_raw.json()['games'])):
        if count >= 10:
            break
        if 'pgn' in games_raw.json()['games'][i] :
            
            game = chess.pgn.read_game(io.StringIO(games_raw.json()['games'][i]['pgn']))
            if "Event" not in game.headers:
                continue
           
            count+=1
            board = chess.Board()
            moves_list = []
            scores = []
            colors = {}
            for move in game.mainline_moves():
                #board.push(move)
                print(str(move))
                if  str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e1-g1':
                    
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    
                    if wCastle:
                        print("1a")
                        moves_list.append('h1-f1')

                    wCastle = False
                elif wCastle and str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e1-c1':
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    
                    if wCastle:
                        print("2a")
                        moves_list.append('a1-d1')
                    wCastle = False
                elif bCastle and str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e8-g8':
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    
                    if bCastle:
                        print("3a")
                        moves_list.append('h8-f8')
                    bCastle = False
                elif bCastle and str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e8-c8':
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    if bCastle:
                        print("4a")
                        moves_list.append('a8-d8')
                    bCastle = False
                else:
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                info = engine.analyse(board, chess.engine.Limit(time=0.005))
                scores.append(info['score'].white().score())
            date = (str(game.headers["Date"])).split('.')  # year, month, day
            yearx = date[0]
            monthx = date[1]
            day = date[2]
            end_position = game.headers['CurrentPosition']
            result = game.headers['Termination'].split(' ')[3]

            if result == 'game':
                result = 'abandoned'
            if game.headers["White"].lower() == name.lower():
                enemy_username = game.headers["Black"]
                colors['name'] = 'White'
                elo = game.headers["WhiteElo"]
                colors['opponent'] = 'Black'
            else:
                enemy_username = game.headers["White"]
                colors['name'] = 'Black'
                elo = game.headers["BlackElo"]
                colors['opponent'] = 'White'
            winner = game.headers["Termination"].split(' ')[0]
            api_result[i] = {'name': name, 'year': yearx, 'month': monthx, 'day': day, 'opponent': enemy_username,
                             'result': result, 'winner': winner, 'end': end_position, 'moves': moves_list,
                             'scores': scores,
                             'colors': colors, 'elo': elo}
        else:
            pass
    return jsonify(api_result)


@app.route('/api/chess/<name>/<year>/<month>/<opponent>', methods=['GET'])
def get_games(name, year, month, opponent):
    games_raw = requests.get(f"https://api.chess.com/pub/player/{name}/games/{year}/{month}")
    api_result = {}
    colors = {}
    for i in range(0, len(games_raw.json()['games'])):
        game = chess.pgn.read_game(io.StringIO(games_raw.json()['games'][i]['pgn']))
        board = chess.Board()
        moves_list = []
        scores = []
        for move in game.mainline_moves():
            board.push(move)
            moves_list.append(str(move))
            info = engine.analyse(board, chess.engine.Limit(time=0.01))
            scores.append(info['score'].white().score())
        end_position = game.headers['CurrentPosition']
        result = game.headers['Termination'].split(' ')[3]
        if result == 'game':
            result = 'abandoned'
        if opponent in game.headers['Black'] or opponent in game.headers['White']:
            date = (str(game.headers["Date"])).split('.')  # year, month, day
            yearx = date[0]
            monthx = date[1]
            day = date[2]
            if game.headers["White"].lower() == name.lower():
                enemy_username = game.headers["Black"]
                colors['name'] = 'White'
                elo = game.headers["WhiteElo"]
                colors['opponent'] = 'Black'
            else:
                enemy_username = game.headers["White"]
                colors['name'] = 'Black'
                elo = game.headers["BlackElo"]
                colors['opponent'] = 'White'
            winner = game.headers["Termination"].split(' ')[0]
            api_result[i] = {'name': name, 'year': yearx, 'month': monthx, 'day': day, 'opponent': enemy_username,
                             'result': result,
                             'winner': winner, 'end': end_position, 'scores': scores, 'elo': elo}
            return jsonify(api_result)


# lichess api implementation

@app.route('/api/lichess/<name>/<year>/<month>/')
def get_games_li_no_opponent(name, year, month):
        api_result = {}
        #midnight first day  ->  #midnight last day month into timestamped seconds format 
        first = datetime.strptime(f'01.{month}.{year} 01:00:00,76',
                                '%d.%m.%Y %H:%M:%S,%f')                      
        last = datetime.strptime(f'28.{month}.{year} 12:00:00,76',
                                '%d.%m.%Y %H:%M:%S,%f')
        first_stamp = first.timestamp() * 1000
        last_stamp = last.timestamp() * 1000
        #lichess api method only takes it in int format
        first_stamp = int(first_stamp)
        last_stamp = int(last_stamp)
        url = f"https://www.lichess.org/api/games/user/{name}"
        
        request = requests.get(
            url,
            params={"since":first_stamp , "until":last_stamp,  "opening":"true"},
            headers={"Accept": "application/x-chess-pgn"}
        )

        games_raw = request.content.decode("utf-8")

        #pgn_store is an array that holds all the games.   r'(1-0|0-1)$' splits everything with 1-0/0-1, but only checks at the end of each line.  
        pgn_store = re.split(r'(1-0|0-1)$',games_raw, flags=re.MULTILINE)

        #new pgn
        pgn_arr = {}
        for i in range(0, len(pgn_store)):
            if ((i+1) *2) >= len(pgn_store): 
                break
            pgn_arr[i] = pgn_store[i*2]
            

        # # prints out each game in the pgn_store array(debug)

        for i in pgn_arr:

            moves_list = []
            scores = []
            colors = {}
            winner ={}
            #reads in a game
            game = chess.pgn.read_game(io.StringIO(pgn_arr[i]))
            #game = chess.pgn.read_game(pgn_)

            board = game.board()
             # this prints a board for every position in the game.
            for move in game.mainline_moves():
                if str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e1-g1':
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    moves_list.append('h1-f1')
                elif str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e1-c1':
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    moves_list.append('a1-d1')
                elif str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e8-g8':
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    moves_list.append('h8-f8')
                elif str(move)[0] + str(move)[1] + '-' + str(move)[2:] == 'e8-c8':
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                    moves_list.append('a8-d8')
                else:
                    moves_list.append(str(move)[0] + str(move)[1] + '-' + str(move)[2:])
                      
                board.push(move)
                info = engine.analyse(board, chess.engine.Limit(time=0.01))
                scores.append(info['score'].white().score())
                date = (str(game.headers["Date"])).split('.')  # year, month, day
                yearx = date[0]
                monthx = date[1]
                day = date[2]
                #end_position = game.headers['CurrentPosition']
                result = game.headers["Result"]
                winner =""
                if result == "1-0":
                     winner = game.headers["White"]
                if result == "0-1":
                     winner = game.headers["Black"]
                      
                if game.headers["White"].lower() == name.lower():
                    enemy_username = game.headers["Black"]
                    colors['name'] = 'White'
                    elo = game.headers["WhiteElo"]
                    colors['opponent'] = 'Black'
                else:
                    enemy_username = game.headers["White"]
                    colors['name'] = 'Black'
                    elo = game.headers["BlackElo"]
                    colors['opponent'] = 'White'
                
                api_result[i] = {'name': name, 'year': yearx, 'month': monthx, 'day': day, 'opponent': enemy_username,
                                'result': result, 'winner': winner, 'moves': moves_list,
                                'scores': scores,
                                'colors': colors, 'elo': elo}
            else:
                pass
        return jsonify(api_result)


        


@app.route('/api/chess/<name>/<year>/<month>/<opponent>')
def get_games_li(name, year, month, opponent):
    return None
