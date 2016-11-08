"""Author: Andy Rosales Elias. University of California, Santa Barbara. andy00@umail.ucsb.edu"""
import sqlite3 as lite

####CONFIG FOR GAME MECHANICS#######

def dropTable(table):
    """Precondition: Table exists and wants to be deleted/dropped :rip:
       Postcondition: Deletes tablename_{channel} db table"""
    con = lite.connect('contents.db')
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS {}".format(table))

def createTable(user1, user2, channel_id):
    """Postcondition: Creates table for moves_{channel}, on default state [-1,-1,-1, 1,-1,-1, 1,-1,-1]
        and GameInfo_{channel} has been initialized to user1 = who launched the game and user2 = who was challenged"""
    con = lite.connect('contents.db')
    board = []
    for i in range(9): #initiate board with values of -1 (default)
        board.append(-1)
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE Moves_{}(a int, b int, c int, d int, e int, f int, g int, h int, i int)".format(channel_id))#create moves tied to specific channel
        cur.execute("CREATE TABLE GameInfo_{}(user1 text, user2 text, channel_id text)".format(channel_id))#create gameinfo tied to specific channel
        cur.execute('INSERT INTO Moves_{} VALUES(?,?,?,?,?,?,?,?,?)'.format(channel_id), (board))  # creates table with all the values on board
        cur.execute('INSERT INTO GameInfo_{} VALUES(?,?,?)'.format(channel_id), (user1,user2,channel_id))  # creates table users and channelID
    return (board)


def saveMove(current_status, channel_id):
    """Precondition: A game exists and is in some valid state. A valid move was made and needs to be saved
       Postcondition: Saves current move to the Moves_ {} table"""
    con = lite.connect('contents.db')
    with con:
        cur = con.cursor()
        cur.execute('INSERT INTO Moves_{} VALUES(?,?,?,?,?,?,?,?,?)'.format(channel_id), current_status)

def retrieveMove(channel_id):
    """Postcondition: If a game exists and is in a valid state, Returns lastest table status from Moves_{channel}, along with the number of turns.
        If no game exists for the channel, returns None"""
    con = lite.connect('contents.db')
    with con:
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM Moves_{}".format(channel_id))
            allRows = cur.fetchall()
            lastRow = allRows[-1]
            moveList = [row for row in lastRow]
            return (moveList, len(allRows)-1)
        except:
            return None

def retrieveGameInfo(channel_id):
    """Postcondition: If a game exists and is in a valid state, It will return the users that are in game.
        If a game is not taking place, returns None"""
    con = lite.connect('contents.db')
    with con:
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM GameInfo_{}".format(channel_id))
            allRows = cur.fetchall()
            lastRow = allRows[-1]
            return lastRow
        except:
            return None

