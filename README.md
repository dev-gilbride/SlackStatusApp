# SlackStatusApp

Lambda function that allows for setting the status and presence across multiple Slack accounts.

## NOTE: 

'Color' is synonymous with Slack account name. The alias was chosen for the project the function was originally intended for.

Commands should not include the '+' or '=' characters, '+' is filtered out and '=' is used as a default.
 
Copying text from Slack messages can sometimes lead to the ' ' character being replaced by '%C2%A0', the current function does not handle these as a ' ' character. 


## How to use the Slack Status Function:

### Command Options:

  The options must be used in the order in which they appear below. The 'color:' option is the only required option, but can not be used alone. The 'action:' option can only be used exclusively with the 'color:' option because it acts as a replacement for the other options. The 'away:' option can be used exclusively with "color:" to change presence, or in conjunction with the other options as part of setting the status. If setting the status without using 'action:', the 'status:' option must be filled. "emoji:" and "duration:" have a default value that is set if the options are not specified otherwise, but to set "duration:" the "emoji:" option must be present.

Option | Description
------------ | -------------
  'away:' | Optional, allows you to set presence to away or auto. Slack does not allow the forcing of an active presence, auto will set the presence to the automatic presence detection. For more information: https://api.slack.com/docs/presence-and-status#manual_away. Set 'y' for away or 'n' for auto.
  'color:' | Required, name of the slack account the command will target. Takes a string.
  'action:' | Optional, sets a preset status for the given color. Takes a string.
  'status:' | Optional, sets the status message. Takes a string.
  'emoji:' | Optional, sets the emoji for the status. To set an emoji, the "status:" option must be used. Takes a string surrounded by colons (as per typical emoji formatting).
  'duration:' | Optional, length of time in seconds for the status to remain. A duration of 0 will leave the status indefinitely. When the duration expires the status will end, however the presence will remain. To set a duration, the "status:" and "emoji:" options must be used. Takes an integer. 


### Usage for AWS CLI: 

Set Status (default presence: auto):   
- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "color: ... status: ... emoji: ... duration: ... " }' response.json  

Set Presence:   
- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "away: ... color: ... " }' response.json  
  
Set Status and Presence:   
- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "away: ... color: ... status: ... emoji: ... duration: ... " }' response.json  

Set Status and Presence to predefined Values:  
- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "color: ... action: ..." }' response.json  

Set predefined Status and Presence on multiple predetermined accounts:   
- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "color: group action: ..." }' response.json  

Run a status indefinitely:   
- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "color: ... status: ... emoji: ... duration: 0 " }' response.json  

Clear Status:   
- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "color: ... action: clear " }' response.json  


#### Example:  

This command will not change your presence, and will set your status to "On my 15min break" with a sleeping emoji, for a duration of 15 minutes: 

- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "away: n color: blue status: On my 15min break emoji: :sleeping: duration: 900 " }' response.json

The same can be accomplished with the function call:  

- aws lambda invoke --function-name slackProfileSet --payload '{ "body": "color: blue action: 15" }' response.json  

Only if the function code has the following action set under the chosen color in the ACTION_DICT:  

```javascript
ACTION_DICT = {  
    'blue' : {  
        '15' : {  
            "emoji": ":sleeping:",  
            "status": "On my 15min break",  
            "duration": 900,  
            'away': 'n'  
        }  
    }  
}  
```

### Usage for Slack App Slash Command:  

The function can handle a call from a Slash Command configured in a Slack App. The format is different, but the placement of options and uses is the same as AWS CLI.  

Set Status (default presence: auto):   
- /<SLACK_APP_NAME> color: ... status: ... emoji: ... duration: ...  

Set Presence:   
- /<SLACK_APP_NAME> away: ... color: ...   

Set Status and Presence:   
- /<SLACK_APP_NAME> away: ... color: ... status: ... emoji: ... duration: ...  

Set Status and Presence to predefined Values:  
- /<SLACK_APP_NAME> color: ... action: ...  

Set predefined Status and Presence on multiple predetermined accounts:   
- /<SLACK_APP_NAME> color: group action: ...  

Run a status indefinitely:   
- /<SLACK_APP_NAME> color: ... status: ... emoji: ... duration: 0  

Clear Status:   
- /<SLACK_APP_NAME> color: ... action: clear  


#### Example:  

This command will not change your presence, and will set your status to "On my 15min break" with a sleeping emoji, for a duration of 15 minutes: 

- /<SLACK_APP_NAME> away: n color: blue status: On my 15min break emoji: :sleeping: duration: 900  

The same can be accomplished with the function call:  

- /<SLACK_APP_NAME> color: blue action: 15  

Only if the function code has the following action set under the chosen color in the ACTION_DICT:  

```javascript
ACTION_DICT = {  
    'blue' : {  
        '15' : {  
            "emoji": ":sleeping:",  
            "status": "On my 15min break",  
            "duration": 900,  
            'away': 'n'  
        }  
    }  
}  
```
