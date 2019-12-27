import json
from botocore.vendored import requests
import time
import datetime
import boto3
import urllib

# Colors are used to differentiate between Slack accounts

# Sets defaults for emoji and/or duration in the event they are missing
# from a status call
DEFAULT_DICT = {
    'emoji': ':slightly_smiling_face:',
    'duration': 3600
}

# Sets the colors to their Slack auth tokens
# Auth tokens are stored in AWS SSM Parameter Store
# Color 'default' cannot be used
COLOR_DICT = {
    'purple': '/SlackAPIToken/Purple',
    'yellow': '/SlackAPIToken/Yellow',
    'blue': '/SlackAPIToken/Blue',
    'group': 'none',
}

# Sets preset action per color
ACTION_DICT = {
    'purple': {
        'lunch': {
            "emoji": ":bento:",
            "status": "Lunch",
            "duration": 0,
            'away': 'y'
        },
        'clear': {
            "emoji": "",
            "status": "",
            "duration": 0,
            'away': 'n'
        }
    },
    'yellow': {
        'lunch': {
            "emoji": ":hamburger:",
            "status": "Out to lunch",
            "duration": 0,
            'away': 'y'
        },
        'clear': {
            "emoji": "",
            "status": "",
            "duration": 0,
            'away': 'n'
        }
    },
    'blue': {
        '15': {
            "emoji": ":sleeping:",
            "status": "On my 15min. break",
            "duration": 900,
            'away': 'n'
        },
        'lunch30': {
            "emoji": ":hamburger:",
            "status": "On lunch break",
            "duration": 1800,
            'away': 'y'
        },
        'lunch60': {
            "emoji": ":pie:",
            "status": "Out to lunch",
            "duration": 3600,
            'away': 'y'
        },
        'pickup': {
            "emoji": ":oncoming_automobile:",
            "status": "Picking up goods",
            "duration": 0,
            'away': 'y'
        },
        'clear': {
            "emoji": "",
            "status": "",
            "duration": 0,
            'away': 'n'
        }
    },
    # group actions will run the specified color and action
    'group': {
        'lunch': {
            'yellow': 'lunch',
            'purple': 'lunch',
        }
    }
}


def presence_update(client, dictIn):

    # Collect AWS SSM Parameters
    response = client.get_parameter(
        Name=dictIn["auth_token_path"],
        WithDecryption=True
    )
    account_access_token = (response['Parameter']['Value'])

    # URL to set user presence
    url = 'https://slack.com/api/users.setPresence'

    headers = {'Content-type': 'application/json',
               'Authorization': 'Bearer %s' % account_access_token
               }
    if dictIn['away'] == 'y':
        data = {
            'presence': 'away'
        }
        resp = requests.post(url, data=json.dumps(data), headers=headers)
    elif dictIn['away'] == 'n':
        data = {
            'presence': 'auto'
        }
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        # 'auto' means automatic Slack presence detection, cannot force a 'present' presence
        # https://api.slack.com/docs/presence-and-status#manual_away


def slack_update(client, dictIn):

    # Collect AWS SSM Parameters
    response = client.get_parameter(
        Name=dictIn["auth_token_path"],
        WithDecryption=True
    )
    account_access_token = (response['Parameter']['Value'])

    # Time setup
    if dictIn['duration'] == 0:
        unix_time = '0'
    else:
        unix_time = str(time.time()).split('.')[0]
        unix_int = int(unix_time) + dictIn['duration']
        unix_time = str(unix_int)

    # defining the api-endpoint
    url = 'https://slack.com/api/users.profile.set'

    txt_in = dictIn['status']
    emoji_in = dictIn['emoji']
    # data to be sent to api
    data = {'profile': {
            'status_text': f'{txt_in}',
            'status_emoji': f'{emoji_in}',
            'status_expiration': f'{unix_time}',
            }}

    headers = {'Content-type': 'application/json',
               'Authorization': 'Bearer %s' % account_access_token
               }

    # sending post request and saving response as response object
    resp = requests.post(url, data=json.dumps(data), headers=headers)

    presence_update(client, dictIn)


def input_handler(input):
    try:
        in_command = input.split("&text=", 1)[1]
        in_command = in_command.split("&response_url=", 1)[0]
        in_command = urllib.parse.unquote(in_command)
    except BaseException:
        in_command = urllib.parse.unquote(input)

    # No using '+' or '=' in status
    # '=' character used as placeholder if a value is not filled
    away_test = False
    color_in = action_in = status_in = emoji_in = duration_in = '='
    away_in = '='

    if in_command.startswith('away:'):
        if 'color:' in in_command:
            away_in = in_command.split('color:', 1)[0].split('away:', 1)[1]
            away_test = True

    if 'color:' in in_command:
        in_command = in_command.split('color:', 1)[1]
        if 'action:' in in_command:
            command_list = in_command.split('action:', 1)
            color_in = command_list[0]
            action_in = command_list[1]
        elif 'status:' in in_command:
            command_list = in_command.split('status:', 1)
            color_in = command_list[0]
            if 'emoji:' in command_list[1]:
                command_list_2 = command_list[1].split('emoji:', 1)
                status_in = command_list_2[0]
                if 'duration:' in command_list_2[1]:
                    command_list_3 = command_list_2[1].split('duration:', 1)
                    emoji_in = command_list_3[0]
                    duration_in = command_list_3[1]
                else:
                    emoji_in = command_list_2[1]
            else:
                status_in = command_list[1]
        else:
            if not away_test:
                color_in = 'default'
            else:
                color_in = in_command
    else:
        color_in = 'default'

    re_pkg = {
        'color': command_handler(color_in),
        'action': command_handler(action_in),
        'status': status_handler(status_in),
        'emoji': command_handler(emoji_in),
        'duration': command_handler(duration_in),
        'away': command_handler(away_in)
    }

    return re_pkg

# Caution: If slack command typed out, ' ' becomes '+' character
# If copy pasted from a slack msg command however, ' ' becomes %C2%A0
# TODO: Filter for %C2%A0


def command_handler(in_str):
    out_str = in_str.replace('+', '').replace(' ', '').casefold()
    return out_str


def status_handler(in_str):
    out_str = in_str.strip('+').replace('+', ' ')
    return out_str


def input_interpreter(dictC, client):
    error_msg = 'Status Set!'
    away_test = False

    if dictC['away'] == '=':
        dictC['away'] = 'n'
    else:
        away_test = True
        if 'y' in dictC['away']:
            dictC['away'] = 'y'
        elif 'n' in dictC['away']:
            dictC['away'] = 'n'
        else:
            # Error: incorrect presence
            error_msg = 'Incorrect Presence'
            return error_msg

    if dictC['color'] == 'default':
        # Error: incorrect format
        error_msg = 'Incorrect format.'
        return error_msg
    else:

        if dictC['color'] in COLOR_DICT:
            auth_in = COLOR_DICT[dictC['color']]
            if dictC['action'] != '=':
                if dictC['action'] in ACTION_DICT[dictC['color']]:
                    if dictC['color'] == 'group':
                        group_handler(dictC['action'], client)
                        error_msg = 'Ran Group Command!'
                        return error_msg
                    else:
                        re_pkg = ACTION_DICT[dictC['color']][dictC['action']]
                        re_pkg.update(auth_token_path=auth_in)
                else:
                    # Error: action does not exist
                    error_msg = 'Action does not exist.'
                    return error_msg

            elif dictC['status'] != '=':
                if dictC['emoji'] != '=':
                    emoji_in = dictC['emoji']
                else:
                    emoji_in = DEFAULT_DICT['emoji']
                if dictC['duration'] != '=':
                    try:
                        duration_in = int(dictC['duration'])
                    except BaseException:
                        # Error: duration should be of type int
                        error_msg = 'Duration is not integer.'
                        return error_msg
                else:
                    duration_in = DEFAULT_DICT['duration']
                re_pkg = {
                    'emoji': emoji_in,
                    'status': dictC['status'],
                    'duration': duration_in,
                    'away': dictC['away'],
                    'auth_token_path': auth_in
                }
            else:
                # If no command, but Presence is set
                if away_test:
                    error_msg = 'Presence Set!'
                    re_pkg = {
                        'emoji': dictC['emoji'],
                        'status': dictC['status'],
                        'duration': dictC['duration'],
                        'away': dictC['away'],
                        'auth_token_path': auth_in
                    }
                    presence_update(client, re_pkg)
                    return error_msg
                else:
                    # Error: missing command
                    error_msg = 'Missing Command.'
                    return error_msg

        else:
            # Error: color does not exist
            error_msg = 'Color does not exist.'
            return error_msg

    slack_update(client, re_pkg)

    return error_msg


def group_handler(action_in, client):
    for x in ACTION_DICT['group'][action_in]:
        inside = ACTION_DICT['group'][action_in][x]
        re_pkg = ACTION_DICT[x][inside]
        re_pkg.update(auth_token_path=COLOR_DICT[x])
        slack_update(client, re_pkg)


def lambda_handler(event, context):

    # TODO: Add Security Screening
    try:
        input = event["body"]
    except BaseException:
        return {
            'statusCode': 500,
            'body': "Error! Incorrect POST."
        }

    ssm = boto3.client('ssm')
    midway = input_handler(input)
    output_msg = input_interpreter(midway, ssm)

    return {
        'statusCode': 200,
        'body': output_msg
    }
