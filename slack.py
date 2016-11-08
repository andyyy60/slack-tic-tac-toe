"""Author: Andy Rosales Elias. University of California, Santa Barbara. andy00@umail.ucsb.edu"""
from flask import Flask, jsonify
from flask import request
from slacker import Slacker
import json, requests
import db_config as db
import game_mechanics as gm
import random
import time


app = Flask(__name__)

def get_token():
    """Precondition: A file named 'token.json' is in the local directory and contains
        the following tokens: Slash command auth token, Web API token
       Postcondition: Returns a json object that contains the slash command and web API token
        with the keys token['slashToken'], token['webToken']"""
    data = None
    try:
        data = json.loads(open('token.json').read())
    except Exception as e:
        pass
    return data

def genHexColor(): #random color generator for funzies :-)
    #Postcondition: Returns a random HEX code that represents a color
   return ''.join([random.choice('0123456789ABCDEF') for x in range(6)])

def genGoodluck(): #goodluck messages!!!
    '''Postcondition: Returns a goodluck message from the text list'''
    text = ['May the force be with you :panda_face:', 'Good luck! :thumbsup:', "Break a leg! :poultry_leg:"]
    return random.choice(text)

def authUser(username, channelID):
    """Precondition: Some username needs to be checked if it exists in channel.
        Takes in a Slack username (usually called by /ttt @username)
       Postcondition: Returns bool if the Username is in the current channel"""
    webToken = get_token()['webToken']
    auth = Slacker(webToken)
    response = auth.users.list()
    response2 = auth.channels.info(channelID)
    teamMembers = response.body['members']
    channelMembers = response2.body['channel']['members']
    for user in teamMembers:
        if user['id'] in channelMembers and not user['deleted']: #if the team member is also a channel member and is not deleted
            if user['name'] == username and str(user['name']).lower() != "slackbot": #if username exists and is not slackbot
                return True
    return False

def sendResponse(endpoint, payload, debug = False):
    """Precondition: A payload has been constructed, and endpoint exists. Takes in endpoint API url, and payload to send to the endpoint
       Postcondition: Payload has been delivered to the specified endpoint URL """
    post_req = requests.post(endpoint, json=payload)
    if debug:
        print post_req.status_code, post_req.reason



def asciiBoard(board):
    """Precondition: A board in some status exists.
       Postcondition: returns the status of the board translated to ASCII in str format"""
    displayText = {"response_type": "in_channel", "text":"```"}
    for i in range(3): #ASCII formatting jargon :hankey:
        displayText['text'] += "| "
        for j in range(3):
            if board[i * 3 + j] == 1:
                displayText['text'] += 'X'
            elif board[i * 3 + j] == 0:
                displayText['text'] += 'O'
            elif board[i * 3 + j] != -1:
                displayText['text'] += str(board[i * 3 + j] - 1)
            else:
                displayText['text'] += ' '

            if j != 2:
                displayText['text'] += " | "
        if i != 2:
            displayText['text'] += ' |\n'
        elif i == 2:
            displayText['text'] += ' |'
        if i != 2:
            displayText['text'] += "|---+---+---|\n"
        else:
            displayText['text'] += ''
    displayText['text'] += "```"
    return displayText['text']


def endGame(data):
    """Precondition: The game has been verified that it has ended (either a winning move or tie move was made)
       Postcondition: The database tables have been reset for the channel in which the game ended"""
    channelID = data['channel_id']
    db.dropTable("Moves_{}".format(channelID))
    db.dropTable("GameInfo_{}".format(channelID))

def playGame(data):
    """Postcondition: An user has triggered the "next" command
       Postcondition: The game has moved to the next stage, or displayed the respective error message"""
    channelID = data['channel_id']
    if gm.checkGame(channelID):
        user1 = gm.getUsers(data)[0] #user that triggered the command
        position = data['text'].split()[1] #whatever is after "next". eg. "/ttt next 1"
        move = gm.checkMove(position, str(user1), channelID)
        if move < 0: #some error
            if move == -5:
                displayText = {"response_type": "ephemeral",
                               "text": "Patience, young grasshopper! Wait for the other user to make a move :thought_balloon:"}
                return jsonify(displayText)
            if move == -4: #user not in-game attempted to run the command
                displayText = {"response_type":"ephemeral", "text":"What a bummer. You are not currently in a game! :-1: Use [/ttt gameinfo] to see the game stats! :thumbsup: :sunglasses:"}
                return jsonify(displayText)
            if move == -1:
                displayText = {"response_type":"ephemeral", "text":"Invalid move! :no_good: Cell already taken. Please try again."}
                return jsonify(displayText)
            if move == -2 or move == -3:
                displayText = {"response_type": "ephemeral",
                               "text":"That is not a valid move! :no_good: Pick a digit 1-9. Please try again."}
                return jsonify(displayText)
        else:
            board = gm.nextMove(int(position), channelID) #play next move and save updated board
            winnerExists = gm.checkWin(board, channelID)
            if winnerExists != -1:
                if winnerExists == 'tie':
                    return displayGameInfo(data, False, False, True)
                else:
                    return displayGameInfo(data, False, True)
            else:
                return displayGameInfo(data, True)
    else:
        return "There's no game currently in place in this channel. :cry:. But it's your time to shine :sun_with_face:! Use [/ttt @user] to create one!"

def launchGame(data):
    """Precondition: An user has attempted to launch a game (triggered the /ttt @user command)
       Postcondition: A game has  been launched or it has been determined that there is already a game taking place"""
    channelID = data['channel_id']
    endpoint = str(data['response_url'])
    if gm.checkGame(channelID): #If a game is already taking place
        return "A game is currently taking place. Use [/ttt next] to see the game info!"

    else:
        user1 = gm.getUsers(data)[0] #user that started the challenge
        user2 = gm.getUsers(data)[1] #challenged user
        if not authUser(user2, channelID): #Checks if challenged user is NOT in the channel
            return "Oops! The user that you challenged is not part of this channel or does not exist! :ghost:"
        db.createTable(user1, user2, channelID) #creates game table, and user/channel table
        displayUser1 = {
            "response_type": "ephemeral",
            "attachments": [
                {
                    "fallback": "instructions",
                    "color": "#{}".format(genHexColor()),
                    "pretext": "You have challenged @{}! {}".format(user2, genGoodluck()),
                    "author_name": "@{}: X  |  @{}: O". format(user1, user2),
                    "title": "Select choice 1-9! The table looks like this:",
                    "text": "```| 1 | 2 | 3 |\n|---+---+---|\n| 4 | 5 | 6 |\n|---+---+---|\n| 7 | 8 | 9 |```",
                    "fields": [
                        {
                            "value": "Type [/ttt next <1-9>]",

                        }
                    ],
                    "footer": "Tic-Tac-Toe, made with :heart: by Andy",
                    "footer_icon": "https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2016-10-27/97399130870_958916a8a18844b0009e_48.png",
                    "ts": time.time(),
                    "mrkdwn_in": ["text", "pretext", "footer"]
                }
            ]
        }
        displayText = {
            "response_type": "in_channel",
            "text": "@{} has started a Tic-Tac-Toe battle with @{}! :muscle:. Tune in at [/ttt gameinfo] for details!".format(user1, user2)
        }
        sendResponse(endpoint, displayText)
        sendResponse(endpoint,displayUser1)
        return ('', 204) #empty response

def displayGameInfo(data, displayTurn = False, displayWin = False, displayTie = False):
    """Precondition: A user has triggered the 'gameinfo' command, or a turn has been made.
       Postcondition: returns information about the game, if a game exists the following info will be returned:
        board in ASCII format, in-game users (and their respective symbols), next turn user, and current move
        else, a message displaying that there is no game taking place will be returned
        If the turn leads to a tie or a win, the proper message will be displayed"""
    channelID = data['channel_id']
    if not gm.checkGame(channelID): #not a game in place
        return "There's no game currently in place in this channel. :cry:. But it's your time to shine :sun_with_face:! Use [/ttt @user] to create one!"
    else: # purpose of displaying game info
        board = gm.getBoard(channelID)  # play next move and save updated board
        currentUser = gm.getUsers(data)[0]
        user1 = gm.getUsers(data, True)[0] # In-game players
        user2 = gm.getUsers(data, True)[1] # In-game players
        text = asciiBoard(board) #get the board in string form
        turn = gm.getMove(channelID)
        move = 1 if turn %2 == 0 else 0
        displayText = {
            "response_type": "in_channel",
            "attachments": [
                {

                    "fallback": "",
                    "color": "#{}".format(genHexColor()),
                    "pretext": "The current board of the Tic-Tac-Toe game is:",
                    "author_name": "@{}: X  |  @{}: O". format(user1, user2),
                    "text": "{}".format(text),
                    "fields": [
                        {
                            "title": "Next turn: @{}!".format(user1 if move ==1 else user2),
                            "value": "Current move: {}".format(turn)
                        }
                    ],
                    "footer": "Tic-Tac-Toe, made with :heart: by Andy",
                    "footer_icon": "https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2016-10-27/97399130870_958916a8a18844b0009e_48.png",
                    "ts": time.time(),
                    "mrkdwn_in": ["text", "pretext", "footer"]
                }
            ]
        }
        if displayTurn: #display turn instead
            displayText['attachments'][0]['pretext'] = "@{} has made a move! The current board is: :mag:".format(currentUser)
        elif displayWin:
            displayText['attachments'][0]['pretext'] = "@{} won the Tic-Tac-Toe game against @{}! :trophy: :trophy: :trophy:, Congratulations! :confetti_ball: :tada:".format(user1, user2)
            displayText['attachments'][0]['color'] = "#ffff00" # yellow for champion!!!
            displayText['attachments'][0]['fields'][0]['title'] = ""
            displayText['attachments'][0]['fields'][0]['value'] = "Challenge the champion by starting a new game! :eyes: [/ttt @user]"
            endGame(data)
        elif displayTie:
            displayText['attachments'][0]['pretext'] = " The game between @{} and @{}! has ended with a tie! :scream: The final board is:".format(user1, user2)
            displayText['attachments'][0]['fields'][0]['title'] = ""
            displayText['attachments'][0]['fields'][0]['value'] = "Try again by starting a new game! :grimacing: [/ttt @user]"
        return jsonify(displayText)


@app.route('/', methods= ['POST'])
def index():
    """Precondition: An user has called the /ttt command
       Postcondition: One of 6 messages may be displayed"""
    data = request.form
    slashToken = get_token()['slashToken'] #load token from disk
    if slashToken != data['token']: #slash auth token does not match
        return "Token for /ttt does not match."
    try:
        text = data['text'].split() #split text by space
        if '@' in str(text[0]).lower(): #username
            return launchGame(data)
        elif str(text[0]).lower() == 'next': #next move
            return playGame(data)
        elif str(text[0]).lower() == 'gameinfo': #display current game info
            return displayGameInfo(data)
        elif str(text[0]).lower() == 'help':
            return "Valid commands: [/ttt @user] to challenge an user, [/ttt next <1-9>] to make a move, and [/ttt gameinfo] to display the current board"
        else: #any other command
            return "That is not a valid command! :no_good: Type [/ttt help] to see the commands!"
    except:
        return "That is not a valid command! :no_good: Type [/ttt help] to see the commands!"


if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0', port='5000')
