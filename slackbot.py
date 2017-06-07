from slackclient import SlackClient
import requests
import time
import re

#constants
API_TOKEN='xoxb-193917654034-i0qThchzFt7a7g4BhpDwSJO2'
BOT_NAME='ticktock'
BOT_ID='U5PSZK810'
EXAMPLE_COMMAND = 'log'
AT_BOT = "<@" + BOT_ID + ">"
VALID_PROJECTS = ['acc','k8', 'classic', 'food']
VALID_COMMANDS = ['log', 'report', 'dadjoke', 'help']

slack_client = SlackClient(API_TOKEN)

def getDadJoke():
    
    headers = {"Accept": "text/plain"}
    joke = requests.get('https://icanhazdadjoke.com/', headers = headers)
    return joke.text

def generateHelpText(command, text):
    
    if re.search('^<*.*> help$', text):
        response = "I'm ticktock! I'm a slackbot written by Michael Griffiths\n" \
        "Usage = `@ticktock COMMAND TEXT` \n" \
        "Valid Commands (case sensitive) = `log, help, report, dadjoke` \n" \
        "For more info on a command type: ```@ticktock help COMMAND```"
    elif re.search('^<*.*> help *', text):
        matches = re.match(r'(^<*.*>) (help) (\w*).*' , text)
        helpCommand = (matches.group(3))
        
        if helpCommand == "report":
            response = "command report not implemented"
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
        
    
def logWork(text):
    
    matches = re.match(r'(^<*.*>) (log) (\w*) (\w.*).*' , text)
    if matches:
        project = matches.group(3)
        time = matches.group(4)
    
        print(project)
        print(time)

        response = "You worked on " + project + " for " + time

    else:
        response = "Sorry none of those commands are valid \n" \
            "Please type ```@ticktock help log``` for a list of valid commands"


    return response


def getBotId():
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        #retrieve all users so we can find our bot
        users = api_call.get('members')

        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print("Bot name for user " + user['name'] + " is " + user.get('id'))
    else:
        print("Could  not find bot name")

def handle_command(command, text, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    
    response = "Not sure what you mean. Valid commands are log, report and help."

    if command.startswith("dadjoke"):
        response = getDadJoke()

    elif command.startswith("log"):
        response = logWork(text)

    elif command.startswith("help"):
        response = generateHelpText(command, text)
    
    elif command.startswith("report"):
        print("report")
    else:
        response = "Sorry none of those commands are valid \n" \
        "Please type ```@ticktock help ``` for a list of valid commands"

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
                       output['channel']

    return None, None, None

def initiateWebsocket():
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("ticktock connected and running!")
        while True:
            command, text, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, text, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

if __name__ == "__main__":
    initiateWebsocket()
