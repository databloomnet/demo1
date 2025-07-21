# app.py

import platform
import getpass
from flask import Flask
import config
from blueprints.main import main_bp
import os
from datetime import datetime
import random
import string

import constants # lesser accessed
# from constants import (
#     ABOUT_BULLETS,
#     WARNING_BULLETS,
#     DEFAULT_OPENAI_MODEL,
#     APP_MODE_SETTING,
#     APP_MODE_VALUE_LOCAL_KEYS,
#     APP_MODE_VALUE_USER_KEYS,
#     APP_MODE_VALUE_SERVER_KEYS,
#     APP_MODE_VALUE_INVALID, 
#     SYSTEM_CONTENT_FILTER,
#     LOCAL_OPENAI_API_KEY_SETTING,
#     LOCAL_CLAUDE_API_KEY_SETTING,
#     USER_OPENAI_API_KEY_SETTING,
#     USER_CLAUDE_API_KEY_SETTING,
#     SERVER_OPENAI_API_KEY_SETTING,
#     SERVER_CLAUDE_API_KEY_SETTING,
#     )

app = Flask(__name__)

def get_random_alphanumeric(length=16):
    chars = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(random.choices(chars, k=length))


app.secret_key = get_random_alphanumeric()
app.register_blueprint(main_bp)


# Log startup time
with open("logs/sys_log.txt", "a") as f:
    f.write(f"{datetime.now()} App started\n")


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    port = 5000
    app.config[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_INVALID
    if getpass.getuser() == 'jeremybloom':
        # start dev mode
        port = 5001

        # set to dev mode
        app.config[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_LOCAL_KEYS
        # app.config[constants.LOCAL_OPENAI_API_KEY_SETTING] = os.environ.get("OPENAI_API_KEY")
        # app.config[constants.LOCAL_CLAUDE_API_KEY_SETTING] = os.environ.get("ANTHROPIC_API_KEY")

        # if app.config[constants.LOCAL_OPENAI_API_KEY_SETTING] in ( None, ""):
        #     print("Starting devmode but no openai key available")
        # if app.config[constants.LOCAL_CLAUDE_API_KEY_SETTING] in ( None, ""):
        #     print("Starting devmode but no claude key available")
    elif True:
        # allow server keys
        import boto3
        from botocore.exceptions import ClientError

        app.config[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_SERVER_KEYS

        # try:
        #     client = boto3.client('secretsmanager', region_name='us-east-1')
        #     response = client.get_secret_value(SecretId="llms/api_keys")
        #     secrets = json.loads(response['SecretString'])

        #     app.config[constants.SERVER_OPENAI_API_KEY] = secrets["openai_api_key"]
        #     app.config[constants.SERVER_CLAUDE_API_KEY] = secrets["anthropic_api_key"]



        # except ClientError as e:
        #     # For a list of exceptions thrown, see
        #     # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        #     raise e


    print(f"Mode: {app.config[constants.APP_MODE_SETTING]}")
    app.run(host="0.0.0.0", port=port, debug=True) # debug=True will have app restart if any code changes






# talk to clauded (uses your api key)
# talk to chatgpt (uses your api key)
# talk to SOMEONE via aws
