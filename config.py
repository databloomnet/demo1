# config.py
"""
These values may change during runtime
Assuming config.py has:
    APP_MODE = "app_mode"
Access from other with:
    from flask import Flask
    import config

    app = Flask(__name__)
    app.config.from_object(config)

    # Without config.APP_MODE
    app.config["app_mode"] = "my_mode"

    # with config.APP_MODE
    app.config[config.APP_MODE] = "my_mode" 
"""

# set this to invalid - need to see if this keeps overwriting

# app.config[constants.APP_MODE_SETTING] = "" # APP_MODE_VALUE_INVALID

# app.config[LOCAL_OPENAI_API_KEY_SETTING] = ""
# app.config[LOCAL_CLAUDE_API_KEY_SETTING] = ""
# app.config[USER_OPENAI_API_KEY_SETTING] = ""
# app.config[USER_CLAUDE_API_KEY_SETTING] = ""
# app.config[SERVER_OPENAI_API_KEY_SETTING] = ""
# app.config[SERVER_CLAUDE_API_KEY_SETTING] = ""


# LOCAL_OPENAI_API_KEY_SETTING =  "local_openai_api_key"
# LOCAL_CLAUDE_API_KEY_SETTING =  "local_claude_api_key"
# USER_OPENAI_API_KEY_SETTING =   "user_openai_api_key"
# USER_CLAUDE_API_KEY_SETTING =   "user_claude_api_key"
# SERVER_OPENAI_API_KEY_SETTING = "server_openai_api_key"
# SERVER_CLAUDE_API_KEY_SETTING = "server_claude_api_key"
