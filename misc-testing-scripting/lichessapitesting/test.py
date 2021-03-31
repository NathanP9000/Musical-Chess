import io
import chess.pgn
import lichess.api
import lichess.pgn
import re
import requests
import chess.svg
import chess.engine
from lichess.format import SINGLE_PGN
from datetime import datetime


engine = chess.engine.SimpleEngine.popen_uci('stockfish_13_win_x64/stockfish_13_win_x64.exe')

# Basic Info
user = input("Enter ur username: ")
year = input("enter the year: ")
month = input("enter the month: ")

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

print(f'{first_stamp} {last_stamp}')

url = f"https://www.lichess.org/api/games/user/{user}"
print(f'{first_stamp} {last_stamp}')


request = requests.get(
    url,
     params={"since":first_stamp , "until":last_stamp,  "opening":"true"},
     headers={"Accept": "application/x-chess-pgn"}
)

games_raw = request.content.decode("utf-8")


# # #   with -> Will make sure the file closes
with open(f'{user}.pgn', 'w') as f:  # creates a file with filename last20{user}.pgn, containing all of the pgn's for the max= games
    f.write(games_raw)



# #takes in username and last 20 games
# user = input('Enter your lichess username: ')
# info = lichess.api.user(user)
# pgn = lichess.api.user_games(user, max=20, format=SINGLE_PGN, opening = 'true')  # max param is for number of games, don't touch anything else on this line
# print()

#make sure user only enters a number between 1 and 20
game_Num = input('Enter which game would you like: ')

#pgn_store is an array that holds all the games.   r'(1-0|0-1)$' splits everything with 1-0/0-1, but only checks at the end of each line.  
pgn_store = re.split(r'(1-0|0-1)$',games_raw, flags=re.MULTILINE)

# prints out each game in the pgn_store array(debug)
# for game in pgn_store:
#    print(game)
#    print('-------------------------------------------------')

# #   with -> Will make sure the file closes
# with open(f'{user}.pgn', 'w') as f:  # creates a file with filename last20{user}.pgn, containing all of the pgn's for the max= games
#     f.write(pgn)

pgn_ = io.StringIO(pgn_store[(int(game_Num) - 1) * 2]) 

#reads in a game
game = chess.pgn.read_game(pgn_)

board = game.board()
#prints board and the moves in the game
print(f'{board}\n')
print(game.mainline_moves())
print()

#keeps track of checks. Should do pins and etc next
check = 0

# this prints a board for every position in the game.
for move in game.mainline_moves():  
    board.push(move)
    info = engine.analyse(board, chess.engine.Limit(depth=10))
    
    #prints score and board
    print(info['score'])
    score_string =  str(info['score'])[12: (str(info['score']).find(',') - 1)]
    clean_score = int(   score_string.replace(')', '').replace(',', '').replace('(', '').replace('e', ''))
    print(clean_score)
    print(f"{board}", end='\n\n\n')
    if board.is_check():
        check += 1

print(f"{check} checks")
# prints final position, and the score at the end
print(board)
print(pgn_store[(int(game_Num) - 1) * 2 + 1])
# username: khreate

# find username of player and then find opponent -> Parameters include opponent

