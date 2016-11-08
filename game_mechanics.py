"""Author: Andy Rosales Elias. University of California, Santa Barbara. andy00@umail.ucsb.edu"""
import db_config as db

def checkGame(channelID):
    """Postcondition: Returns bool whether or not a game is in place"""
    if db.retrieveMove(channelID):
        return True
    return False

def getUsers(data, in_game = False):
    """Precondition: A game is being launched (/ttt @user), or game exists and has two users in-game.
       Postcondition: If in-game = True, returns the in-game users.
       User that launched the game is "user1" and X, challenged user is "user2" and O
       if in-game = False, it returns users based on the command. The following states are possible:
       1) Some user challenged another by launching a game (User1 and User2 can be obtained from command).
        e.g (/ttt @user) can obtain user1 (triggered the command), and user2 (challenged user)
       2) Some user executed some command, only user1 (who executed the command) can be obtained
        e.g (/ttt gameinfo) or (/ttt next <1-9>)"""
    if in_game:
        user1 = db.retrieveGameInfo(data['channel_id'])[0]
        user2 = db.retrieveGameInfo(data['channel_id'])[1]
        return (user1, user2)
    else:
        text = data['text'].split()
        user1 = str(data['user_name'])  # user that started the challenge
        user2 = str(text[0])[1:] #[:1] to skip the @, beware not all /ttt calls contain a second user (e.g next and gameinfo)
        return (user1, user2)

def getMove(channelID):
    """Precondition: A game exists and is in some valid state
       Postcondition: An int value with the number of moves is returned """
    move = db.retrieveMove(channelID)[1]
    return move

def nextMove(position, channelID):
    """Precondition: A game exists and is in some valid state
       Postcondition: Makes next move, and returns updated board"""
    board = db.retrieveMove(channelID)[0]
    board[position-1] = 1 if getMove(channelID)%2 == 0 else 0 #1 if x, 0 if O
    db.saveMove(board,channelID) #save
    return board

def getBoard(channelID):
    """Precondition: A game exists and is in some valid state
       Postcondition: returns board status without making any changes to it"""
    return db.retrieveMove(channelID)[0]

def checkMove(move, user1, channelID):
    """Precondtion: A game exists and is in some valid state. A user has made a move to be checked for validity
       Postcondition: Returns different states of move validity, (-1 to -5), denoted by the comments next to each return status"""
    user1_db = str(db.retrieveGameInfo(channelID)[0])
    user2_db = str(db.retrieveGameInfo(channelID)[1])
    board = db.retrieveMove(channelID)[0]
    turn = int(getMove(channelID))
    if turn%2 == 0: #user1 turn (even)
        if user1 == user2_db:
            return -5 #If the other who just made a turn tried to make another
        elif user1 != user1_db and user1 != user2_db:
            return -4 #if anyone else not in-game tried to make a move
    elif turn%2 != 0: #user2 turn (odd)
        if user1 == user1_db:
            return -5 #If the other who just made a turn tried to make another
        elif user1 != user2_db and user1 != user1_db:
            return -4 #if anyone else not in-game tried to make a move
    try:
        move = int(move)
        if move >= 1 and move <= 9:
            if board[move-1] != -1:
                return -1 # error a move attempted on an already taken cell
            else:
                return(move - 1)
        else:
            return -2 # attempted move on a  cell > 9 or cell < 0
    except:
        return -3 #non-integer input (e.g str)

def checkWin(board, channelID):
    """Precondition: A game exists and is in some valid state. User has made a valid move
       Postcondition: Returns 3 different states: winner, no winner, tie. Description denoted in return statements"""
    move = getMove(channelID)
    if move > 4: #minimum amount of moves to win
        winCondition = ((1, 2, 3), (4, 5, 6), (7, 8, 9), (1, 4, 7), (2, 5, 8), (3, 6, 9), (1, 5, 9), (3, 5, 7))
        for each in winCondition:
            try:
                if board[each[0] - 1] == board[each[1] - 1] and board[each[1] - 1] == board[each[2] - 1]:
                    return board[each[0] - 1] #we got a winner!!!!!
            except:
                pass
    if move == 9:
        return "tie" #no winner :cry:
    return -1 # not a tie or a win
