from slackclient import SlackClient
import requests
import time
import re
from collections import defaultdict

#constants
API_TOKEN=''
BOT_NAME='ticktock'
BOT_ID='U5PSZK810'
EXAMPLE_COMMAND = 'log'
AT_BOT = "<@" + BOT_ID + ">"
VALID_PROJECTS = ['acc','k8', 'classic', 'food']
VALID_COMMANDS = ['log', 'report', 'dadjoke', 'help']

slack_client = SlackClient(API_TOKEN)

REPORT = dict()

def updateTimeSpent(project, timeSpentNumber, timeSpentWord, userName):

    workLog = [timeSpentNumber, timeSpentWord, project] 
    if userName in REPORT:
        REPORT[userName].append(workLog)

    else:
        REPORT.setdefault(userName, [])
        REPORT[userName].append(workLog)

    print (REPORT)


def getDadJoke():
    
    headers = {"Accept": "text/plain"}
    joke = requests.get('https://icanhazdadjoke.com/', headers = headers)
    return joke.text

def generateHelpText(command, text, userName):
    
    if re.search('^<*.*> help$', text):
        response = "Hey " + userName + " I'm ticktock! \n" \
        "I'm a slackbot written by Michael Griffiths\n" \
        "Usage = `@ticktock COMMAND TEXT` \n" \
        "Valid Commands (case sensitive) = `log, help, report, dadjoke` \n" \
        "For more info on a command type: ```@ticktock help COMMAND```"
    elif re.search('^<*.*> help *', text):
        matches = re.match(r'(^<*.*>) (help) (\w*).*' , text)
        helpCommand = (matches.group(3))
        
        if helpCommand == "report":
            response = "*Report* \n" \
            "Report will retrieve an array of logged time and send it to you. \n" \
            "Usage = `@ticktock report \n" \
            "Example Usage = `@ticktock report`"
            
        elif helpCommand == "log":
            response = "*Log* \n" \
            "Usage = `@ticktock log PROJECT TIME` \n" \
            "Example Usage = `@ticktock log acc 2hr`"
    
        elif helpCommand == "dadjoke":
            response = "\n ***DADJOKE*** \n Gets a dadjoke from the icanhasdadjoke api and sends it to you!" \
            "\n Dadjoke Usage = ```@ticktock dadjoke```"
    else: 
        response = "Sorry none of those commands are valid \n" \
        "Please type ```@ticktock help``` for a list of valid commands" 

    return response
    
    
def logWork(text, userName):
    
    matches = re.match(r'(^<*.*>) (log) (\w*) (\w.*).*' , text)
    if matches:
        project = matches.group(3)
        time = matches.group(4)
        print(project)
    
        #need to take the users input and make sure it is correct
        matchTime = re.match(r'(\d*)(\D*)', time)
        timeSpentNumber = matchTime.group(1)
        timeSpentWord = matchTime.group(2)

        updateTimeSpent(project, timeSpentNumber, timeSpentWord, userName)

        response = "Hey " + str(userName) + " You worked on " + str(project) + " for " + str(time)

    else:
        response = "Sorry none of those commands are valid \n" \
            "Please type ```@ticktock help log``` for a list of valid commands"


    return response


def getUserName(userID):
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        #retrieve all users so we can find our bot
        users = api_call.get('members')

        for user in users:
            if 'name' in user and user.get('id') == userID:
                return user['name']
    else:
        print("Could  not find user name")

def getBotId():
    """
        This function is used during development to find the userID of the bot. 
        It is not currently in use.
    """
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        #retrieve all users so we can find our bot
        users = api_call.get('members')

        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print("Bot name for user " + user['name'] + " is " + user.get('id'))
    else:
        print("Could  not find bot name")

def handle_command(command, text, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Valid commands are log, report and help."
    userName = getUserName(user)

    if command.startswith("dadjoke"):
        response = getDadJoke()

    elif command.startswith("log"):
        response = logWork(text, userName)

    elif command.startswith("help"):
        response = generateHelpText(command, text, userName)
    
    elif command.startswith("report"):
        response = str(REPORT)

    else:
        response = "Sorry " + userName + " none of those commands are valid \n" \
        "Please type ```@ticktock help ``` for a list of valid commands"

    greetings = ['hi', 'hello', 'good morning', 'sup']
    for greeting in greetings:
        if text.find(greeting) > 0:
            response = "Well hello there!" + userName

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                ##DEBUG
                print(output)
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['text'], \
                       output['channel'], \
                       output['user'] \

    return None, None, None, None

def initiateWebsocket():
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("ticktock connected and running!")
        while True:
            command, text, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, text, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

if __name__ == "__main__":
    initiateWebsocket()

