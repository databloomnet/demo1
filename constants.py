# constants.py
# for values that do not change during runtime



DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
DEFAULT_CLAUDE_MODEL = "claude-opus-4-20250514"
DEFAULT_AWS_TITAN_MODEL = "amazon.titan-text-express-v1"


# no longer used...
ABOUT_BULLETS = [
                    "I wrote this app to 1) demonstrate how to use LLM services in their python prototypes and 2) convince potential clients that I'm not just a powerpoint jockey.",
                    "Warning: This app is not hardened, is (probably) running on a dev server, and may be vulnerable.",
                    "Two user modes: 1) user_keys - you enter your own keys and 2) server_keys - I provide keys",
                    "App will start in server_keys mode if it is available.  Rate limiting is enabled in server_keys mode.",
                    "While I don't save keys, prompts, or responses, these may be visible in debug sessions.",
                    "code: https://github.com/databloomnet/demo1"
                ]

WARNING_BULLETS = [
                    "Warning: This app is not hardened, is (probably) running on a dev server, and may be vulnerable.",
                    "While I don't save keys, prompts, or responses, these may be visible in debug sessions.",
                    "Do not share private data or high value keys.",
                    # "This app is running on a dev server, is not hardened, and may be vulnerable.  Do not share private data.",
                    # "Some functions allow you to add your own keys.  Rate limiting is disabled when using your own keys.",
                    # "I sometimes provide my own keys for use.  When I do this rate limiting is on.  If you replace with your own keys rate limiting is disabled.",
                    # "Any keys you enter are saved in your session only.  I do not record them nor will I use them, but they may be visible in debug sessions",
                    # "Prompts and responses are saved in your session only, but may be visible in debug sessions.",
                    # "You may wish to click \"Clear and Restart Conversation\" to delete the conversation history from your session",
                    # "Note \"query\" options do not save any history.",
                    # "This is a experimental learning prototype, and is unsutiable for production use",
                    #"code: https://github.com/databloomnet/demo1"
                ]




DEBUG = 1

APP_MODE_SETTING =           "app_mode" # this is the name of the setting
APP_MODE_VALUE_LOCAL_KEYS =  "local_keys"
APP_MODE_VALUE_USER_KEYS =   "user_keys"
APP_MODE_VALUE_SERVER_KEYS = "server_keys"
APP_MODE_VALUE_INVALID =      "error"


SESSION_ID_SETTING = "session_id"

ERROR_NO_KEY = "please enter a key"
ERROR_EMPTY_PROMPT = "please enter a message"
MAX_PROMPT_LENGTH = 400
ERROR_MAX_PROMPT_LENGTH_EXCEEDED = "please shorten your prompt"

#RATE_LIMITER_SHORT_EXCEEDED = "throttling (short) - exceeded allowed requests in the short window"
#RATE_LIMITER_LONG_EXCEEDED = "throttling (long) - exceeded allowed requests in the long window"

RATE_LIMITERS = [   {"max": 10, "times": 60,        "name": "r1 - single minute limiter"},
                    {"max": 20, "times": 60*5,      "name": "r2 - five minute limiter"},
                    {"max": 100, "times": 60*60,    "name": "r3 - one hour limiter"},
                    {"max": 200, "times": 60*60*8,  "name": "r4 - eight hour limiter"},
                    {"max": 500, "times": 60*60*24, "name": "r5 - one day limiter"} ]


ERROR_RATE_LIMITER_PAUSE = "rate limiting active"


system_content_filter =  "You are a helpful assistant.  If anyone uses especially inappropriate language "
system_content_filter += "you will respond with this exact phrase: \'I decline to engage rude discussions\'"
SYSTEM_CONTENT_FILTER = system_content_filter


LOCAL_OPENAI_API_KEY_SETTING =  "local_openai_api_key"
LOCAL_CLAUDE_API_KEY_SETTING =  "local_claude_api_key"
USER_OPENAI_API_KEY_SETTING =   "user_openai_api_key"
USER_CLAUDE_API_KEY_SETTING =   "user_claude_api_key"
SERVER_OPENAI_API_KEY_SETTING = "server_openai_api_key"
SERVER_CLAUDE_API_KEY_SETTING = "server_claude_api_key"
CURRENT_OPENAI_API_KEY_SETTING =  "current_openai_api_key"
CURRENT_CLAUDE_API_KEY_SETTING =  "current_claude_api_key"

