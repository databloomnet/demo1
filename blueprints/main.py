import os
from pathlib import Path
from flask import Blueprint, request, render_template, redirect, url_for, current_app
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

import openai
import anthropic
from flask import session, flash # for session mgmt
import time
import config
import constants

import uuid


from rate_limiter import RateLimiter

main_bp = Blueprint('main', __name__)

syslog_c = "logs/sys_log.txt"
applog_c = "logs/app_log.txt"

global_rate_limiters = {}

# stored here instead of session for security
dict_of_openai_api_keys = {}
dict_of_claude_api_keys = {}

def write_syslog(s):
    with open(syslog_c, "a") as f:
        f.write(f"{datetime.now()} {request.remote_addr}: {s}\n")

def write_applog(s):
    with open(applog_c, "a") as f:
        f.write(f"{datetime.now()} - {s}\n")



def get_session_id():
    if constants.SESSION_ID_SETTING not in session:
        session[constants.SESSION_ID_SETTING] = uuid.uuid4() # 128 bit id
    return session[constants.SESSION_ID_SETTING]

def print_session_info(m = ""):
    sid = get_session_id()
    s = f"{sid} mode: {session[constants.APP_MODE_SETTING]} "
    if sid in dict_of_openai_api_keys:
        s += str(len(dict_of_openai_api_keys[sid]))
    else:
        s += "<na>"
    s+= " "
    if sid in dict_of_claude_api_keys:
        s += str(len(dict_of_claude_api_keys[sid]))
    else:
        s += "<na>"
    s+= f" {sid}"
    print(s)

    #print(f"{m} mode: {session[constants.APP_MODE_SETTING]} { len( dict_of_openai_api_keys[sid] ) } { len( dict_of_claude_api_keys[sid] ) }  Session: {sid} ")


def validate_session():
    # verify or establish session[constants.SESSION_ID_SETTING]
    if constants.SESSION_ID_SETTING not in session:
        session[constants.SESSION_ID_SETTING] = "" # gets set during validate_session
    if session[constants.SESSION_ID_SETTING] == "":
        session[constants.SESSION_ID_SETTING] = uuid.uuid4() # 128 bit id
        if constants.DEBUG:
            print(f"establishing session_id { session[constants.SESSION_ID_SETTING] }")

    # verify or establish session[constants.APP_MODE_SETTING]
    if constants.APP_MODE_SETTING not in session:
        # need to est session by pulling from current_app.config
        session[constants.APP_MODE_SETTING] = current_app.config[constants.APP_MODE_SETTING]
        if constants.DEBUG:
            print(f"establishing session app mode { session[constants.APP_MODE_SETTING] }")

    if constants.DEBUG:
        print(f"session mode {session[constants.APP_MODE_SETTING]} by session id {session[constants.SESSION_ID_SETTING]}")

    # handle by session app mode
    if session[constants.APP_MODE_SETTING] == constants.APP_MODE_VALUE_LOCAL_KEYS:
        # this is LOCAL or DEV mode - gets keys from the local/server running the flask app
        #session_id = session[constants.SESSION_ID_SETTING] # convienence var
        if get_session_id() not in dict_of_openai_api_keys:
            if constants.DEBUG:
                print(f"LOCAL/dev adding openai_api key for {get_session_id()}")
            dict_of_openai_api_keys[get_session_id()] = os.environ.get("OPENAI_API_KEY")

        if get_session_id() not in dict_of_claude_api_keys:
            if constants.DEBUG:
                print(f"LOCAL/dev adding claude_api key for {get_session_id()}")
            dict_of_claude_api_keys[get_session_id()] = os.environ.get("ANTHROPIC_API_KEY")
    elif session[constants.APP_MODE_SETTING] == constants.APP_MODE_VALUE_SERVER_KEYS:
        # SERVER mode - get from AWS secrets - use throttling
        # if either  is missing, just reload both...
        session_id = session[constants.SESSION_ID_SETTING] # convienence var
        if (session_id not in dict_of_openai_api_keys) or (session_id not in dict_of_claude_api_keys) or (dict_of_openai_api_keys[session_id] == "") or (dict_of_claude_api_keys[session_id] == ""):
            if constants.DEBUG:
                print(f"SERVER - adding aws secrets openai and claude keys for { session_id}")
            try:
                import boto3
                from botocore.exceptions import ClientError, NoCredentialsError

                client = boto3.client('secretsmanager', region_name='us-east-1')
                response = client.get_secret_value(SecretId="llms/api_keys")
                secrets = json.loads(response['SecretString'])

                dict_of_openai_api_keys[session_id] = secrets["openai_api_key"]
                dict_of_claude_api_keys[session_id] = secrets["anthropic_api_key"]
            except NoCredentialsError:
                m = f"This system does not have access to server_keys via aws secrets.  Reverting to {constants.APP_MODE_VALUE_LOCAL_KEYS}"
                print(m)
                write_syslog(m)
                session[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_LOCAL_KEYS
            except ClientError as e:
                m = f"ClientError: {e.response['Error']['Message']} - Reverting to {constants.APP_MODE_VALUE_LOCAL_KEYS}"
                print(m)
                write_syslog(m)
                session[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_LOCAL_KEYS
            except Exception as e:
                m = f"Unexpected error: {str(e)} - Reverting to {constants.APP_MODE_VALUE_LOCAL_KEYS}"
                print(m)
                write_syslog(m)
                session[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_LOCAL_KEYS
    elif session[constants.APP_MODE_SETTING] == constants.APP_MODE_VALUE_USER_KEYS:
        # user to enter keys...
        #session_id = session[constants.SESSION_ID_SETTING] # convienence var
        if get_session_id() not in dict_of_openai_api_keys:
            if constants.DEBUG:
                print(f"USER - adding blank openai_api key for {get_session_id()}")
            dict_of_openai_api_keys[get_session_id()] = ""

        if get_session_id() not in dict_of_claude_api_keys:
            if constants.DEBUG:
                print(f"USER - adding blank claude_api key for {get_session_id()}")
            dict_of_claude_api_keys[get_session_id()] = os.environ.get("ANTHROPIC_API_KEY")
    else:
        # error
        session_id = session[constants.SESSION_ID_SETTING] # convienence var
        print(f"error: invalid session app mode { session[constants.APP_MODE_SETTING] } { get_session_id() }")
        if session_id in dict_of_openai_api_keys:
            if dict_of_openai_api_keys[session_id] != "":
                print(f"error: openai key present even though state is invalid... deleting { get_session_id() }")
                dict_of_openai_api_keys[session_id] = ""
        if session_id in dict_of_claude_api_keys:
            if dict_of_claude_api_keys[session_id] != "":
                print(f"error: claude key present even though state is invalid... deleting { get_session_id() }")
                dict_of_clade_api_keys[session_id] = ""


    if constants.DEBUG:
        print(f"session id {get_session_id()} keys lengths { len(dict_of_openai_api_keys[get_session_id()]), len(dict_of_openai_api_keys[get_session_id()])}")
    print("-" * 70)

    return session[constants.SESSION_ID_SETTING]

def get_hms_pt():
    now_pt = datetime.now(ZoneInfo("America/Los_Angeles"))
    now_pt_s = now_pt.strftime("%H:%M:%S")
    return now_pt_s


@main_bp.route("/")
def index():
    write_syslog("/ accessed")
    #return render_template("index.html", current_app_mode = session[config.APP_MODE])
    
    validate_session()

    print_session_info("/")

    # now_pt = datetime.now(ZoneInfo("America/Los_Angeles"))
    # now_pt_s = now_pt.strftime("%Y-%m-%d %H:%M:%S")
    # print(f"{now_pt_s}:  accessed index with state {session[constants.APP_MODE_SETTING]}")

    return render_template("index.html",current_app_mode = session[constants.APP_MODE_SETTING], about_bullets = constants.ABOUT_BULLETS)


@main_bp.route("/submit_note", methods=["POST"])
def submit_note():
    write_syslog("note submitted")
    note = request.form.get("note")
    write_applog(note)
    return redirect(url_for("main.show_app_log"))


@main_bp.route("/sys_log")
def show_sys_log():
    # write_syslog("/sys_log accessed")
    with open(syslog_c) as f:
        lines = [line.strip() for line in f.readlines()]  # <--- strip newlines
    return render_template("sys_log.html", log=lines)

@main_bp.route("/rates")
def show_rates():
    # init if needed
    if len(global_rate_limiters.keys()) == 0:
        for rate_lim in constants.RATE_LIMITERS:
            next_rate_limiter = RateLimiter(max_requests= rate_lim["max"],  interval_sec = rate_lim["times"])
            global_rate_limiters[rate_lim["name"]] = next_rate_limiter

    # check on rates
    lines = []
    for name, rate_lim in global_rate_limiters.items():
        lines.append( rate_lim.status() )
    return render_template("rates.html", log=lines)


@main_bp.route("/app_log")
def show_app_log():
    # write_syslog("app_log accessed")
    with open(applog_c) as f:
        # lines = f.readlines()
        lines = [line.strip() for line in f.readlines()]  # <--- strip newlines
    return render_template("app_log.html", log=lines)


@main_bp.route("/delete_sys_log", methods=["POST"])
def delete_sys_log():
    open(syslog_c, "w").close()  # truncate file
    write_syslog("/sys_log reset")
    return redirect(url_for("main.index"))

@main_bp.route("/delete_app_log", methods=["POST"])
def delete_app_log():
    open(applog_c, "w").close()  # truncate file
    write_syslog("/app_log reset")
    return redirect(url_for("main.index"))


def rate_limiter_exceeded():
    # ideally sort by duration increasing... in future

    # init if not active
    if len(global_rate_limiters.keys()) == 0:
        for rate_lim in constants.RATE_LIMITERS:
            next_rate_limiter = RateLimiter(max_requests= rate_lim["max"],  interval_sec = rate_lim["times"])
            global_rate_limiters[rate_lim["name"]] = next_rate_limiter

    # check on rates
    for name, rate_lim in global_rate_limiters.items():
        if rate_lim.allow() == False:
            s = constants.ERROR_RATE_LIMITER_PAUSE + ": " + rate_lim.status()
            print(s)
            write_applog(s)
            return s
    
    return False



@main_bp.route("/query_chatgpt", methods=["GET", "POST"])
def query_chatgpt():
    session_id = validate_session()
    api_key = dict_of_openai_api_keys[ session_id ]
    api_key_saved = len(api_key)

    response = ""
    error = False
    intro_title = "This page allows you to ask ChatGPT a single question.  Please note:"
    intro_bullets = constants.WARNING_BULLETS
    default_prompt = "In 15 words or less, how can we improve our world?"
    user_prompt = default_prompt

    message_footer = ""
    completion = "" # empty is error

    if request.method == "POST":
        if not api_key_saved:
            print("CHECK -saving new api key")
            api_key = request.form.get("api_key", "").strip()
            api_key_saved = len(api_key)
            if api_key_saved:
                session[config.OPENAI_API_KEY] = api_key

        user_prompt = request.form.get("user_prompt", "").strip()
        t0 = time.time()

        if not user_prompt:
            error = constants.ERROR_EMPTY_PROMPT
        elif len(user_prompt) > constants.MAX_PROMPT_LENGTH:
            error = constants.ERROR_MAX_PROMPT_LENGTH_EXCEEDED
        elif is_rate_limiting_on():
            error = rate_limiter_exceeded()

        if not error:
            try:
                completion = False
                client = openai.OpenAI(api_key=api_key)
                messages = [
                    {"role": "system", "content": constants.SYSTEM_CONTENT_FILTER},
                    {"role": "user", "content": user_prompt}
                ]

                completion = client.chat.completions.create(
                    model=constants.DEFAULT_OPENAI_MODEL,  
                    messages=messages
                )

                # completion_full = completion
                response = completion.choices[0].message.content
                if constants.DEBUG > 0:
                    print("prompt:", user_prompt)
                    print("response:", response)

            except Exception as e:
                try:
                    # poor parsing, not sure if it matches
                    error_json = e.response.json()
                    if error_json.get("error", {}).get("code") == "invalid_api_key":
                        error = "Invalid API key. Please double-check and try again."
                    else:
                        error = f"OpenAI Error: {error_json.get('error', {}).get('message', str(e))}"
                except:
                    error = f"Unexpected error: {str(e)}"

        message_footer = ""
        if completion:
            message_footer = "\n\tAnalysis:"
            message_footer += "\n\tResponded with {:d} words at {:} in {:.1f}s".format( len(response.split()), get_hms_pt(), time.time() - t0 )
            message_footer += "\n\tUsed {:d} prompt tokens and {:d} completion tokens for {:d} total tokens".format(completion.usage.prompt_tokens,
                completion.usage.completion_tokens, completion.usage.prompt_tokens + completion.usage.completion_tokens)

        write_applog(f"query_chatgpt called with len(prompt) { len(user_prompt) } and len(response) { len(response) }")

    return render_template("query_chatgpt.html", 
                intro_title=intro_title,
                intro_bullets=intro_bullets,
                response=response,
                error=error,
                api_key=api_key,
                user_prompt=user_prompt,
                message_footer = message_footer,
                api_key_saved=api_key_saved)



@main_bp.route("/converse_chatgpt", methods=["GET", "POST"])
def converse_chatgpt():
    session_id = validate_session()
    api_key = dict_of_openai_api_keys[ session_id ]
    api_key_saved = len(api_key)

    response = ""
    error = False
    intro_title = "This page allows you to ask ChatGPT a single question.  Please note:"
    intro_bullets = constants.WARNING_BULLETS
    default_prompt = "Please describe me in a haiku.  You can ask questions, but end each response with a haiku.  Try to use all the info you learn about me in the haiku."

    chat_history = session.get("converse_chatgpt_chat_history", [])
    if len(chat_history) == 0:
        user_prompt = default_prompt
    else:
        user_prompt = "any other thoughts?"

    message_footer = ""
    completion = "" # empty is error

    if request.method == "POST":
        if not api_key_saved:
            user_key = request.form.get("api_key", "").strip()
            print("CHECK -saving new api key")
            print("user provided key:", user_key)
            if user_key != "":
                print("saving user provided key as session key")
                session[config.SESSION_OPENAI_API_KEY] = user_key
                openai_api_key = session[config.SESSION_OPENAI_API_KEY]
                openai_api_key_saved = True
 

        user_prompt = request.form.get("user_prompt", "").strip()
        t0 = time.time()

        if not user_prompt:
            error = constants.ERROR_EMPTY_PROMPT
        elif len(user_prompt) > constants.MAX_PROMPT_LENGTH:
            error = constants.ERROR_MAX_PROMPT_LENGTH_EXCEEDED
        elif is_rate_limiting_on():
            error = rate_limiter_exceeded()

        if not error:
            try:
                if len(chat_history) == 0:                    
                    chat_history.append({"role": "system", "content": constants.SYSTEM_CONTENT_FILTER})
                chat_history.append( {"role": "user", "content": user_prompt} )

                client = openai.OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                    model=constants.DEFAULT_OPENAI_MODEL,
                    messages=chat_history,
                    response_format={"type": "text"}  # works, check if json works...
                )

                #completion_full = completion
                response = completion.choices[0].message.content
                chat_history.append({"role": "assistant", "content": response})

                session["converse_chatgpt_chat_history"] = chat_history
                session["converse_chatgpt_chat_timestamp"] = datetime.utcnow().isoformat()

                if constants.DEBUG > 0:
                    print("prompt:", user_prompt)
                    print("response:", response)

                user_prompt = "any other thoughts?"

            except Exception as e:
                try:
                    # poor parsing, not sure if it matches
                    error_json = e.response.json()
                    if error_json.get("error", {}).get("code") == "invalid_api_key":
                        error = "Invalid API key. Please double-check and try again."
                    else:
                        error = f"OpenAI Error: {error_json.get('error', {}).get('message', str(e))}"
                except:
                    error = f"Unexpected error: {str(e)}"

        message_footer = ""
        if completion:
            message_footer = "\n\tAnalysis:"
            message_footer += "\n\tResponded with {:d} words in in {:.1f}s".format( len(response.split()), time.time() - t0 )

            message_footer += "\n\tUsed {:d} prompt tokens and {:d} completion tokens for {:d} total tokens".format(completion.usage.prompt_tokens,
                completion.usage.completion_tokens, completion.usage.prompt_tokens + completion.usage.completion_tokens)
            if constants.DEBUG > 0:
                print("message_footer:", message_footer)

        write_applog(f"converse_chatgpt called with len(prompt) { len(user_prompt) } and len(response) { len(response) }")

    return render_template("converse_chatgpt.html", 
                intro_title=intro_title,
                intro_bullets=intro_bullets,
                response=response,
                error=error,
                openai_api_key=api_key,
                user_prompt=user_prompt,
                message_footer = message_footer,
                api_key_saved=api_key_saved,
                chat_history = chat_history[1:])  # leave out the system message in chat history


@main_bp.route("/query_claude", methods=["GET", "POST"])
def query_claude():
    session_id = validate_session()
    api_key = dict_of_claude_api_keys[ session_id ]
    api_key_saved = len(api_key)
    
    response = ""
    error = False
    intro_title = "This page allows you to ask Claude a single question.  Please note:"
    intro_bullets = constants.WARNING_BULLETS
    default_prompt = "In 15 words or less, how can we improve our educational system?"
    user_prompt = default_prompt

    message_footer = ""
    if request.method == "POST":        
        if not api_key_saved:
            print("saving new api key")
            api_key = request.form.get("api_key", "").strip()
            api_key_saved = len(api_key)
            if api_key_saved:
                session[config.OPENAI_API_KEY] = api_key

        user_prompt = request.form.get("user_prompt", "").strip()

        t0 = time.time()

        if not user_prompt:
            error = constants.ERROR_EMPTY_PROMPT
        elif len(user_prompt) > constants.MAX_PROMPT_LENGTH:
            error = constants.ERROR_MAX_PROMPT_LENGTH_EXCEEDED
        elif is_rate_limiting_on():
            error = rate_limiter_exceeded()

        if not error:
            try:
                completion = False
                client = anthropic.Anthropic(api_key = api_key)
                completion = client.messages.create(
                    model=constants.DEFAULT_CLAUDE_MODEL,
                    max_tokens=200,
                    temperature=1,
                    system=constants.SYSTEM_CONTENT_FILTER,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_prompt
                                }
                            ]
                        }
                    ]
                )

                response = completion.content[0].text
                if constants.DEBUG > 0:
                    print("prompt:", user_prompt)
                    print("response:", response)                

            except Exception as e:
                try:
                    # Try to parse the error and look for OpenAI-style structured error
                    # this is chatgpt but for claude, so prolly doesn't work
                    error_json = e.response.json()
                    if error_json.get("error", {}).get("code") == "invalid_api_key":
                        error = "Invalid API key. Please double-check and try again."
                    else:
                        error = f"Claude Error: {error_json.get('error', {}).get('message', str(e))}"
                except:
                    # Fallback if it's not a typical response
                    error = f"Unexpected error: {str(e)}"

        message_footer = ""
        if completion:
            message_footer = "\n\tAnalysis:"
            message_footer += "\n\tResponded with {:d} words at {:} in {:.1f}s".format( len(response.split()), get_hms_pt(), time.time() - t0 )
            message_footer += "\n\tUsed {:d} prompt tokens and {:d} completion tokens for {:d} total tokens".format(completion.usage.input_tokens,
                completion.usage.output_tokens, completion.usage.input_tokens + completion.usage.output_tokens)
    
    write_applog(f"query_claude called with len(prompt) { len(user_prompt) } and len(response) { len(response) }")

    return render_template("query_claude.html", 
                intro_title=intro_title,
                intro_bullets=intro_bullets,
                response=response,
                error=error,
                api_key=api_key,
                user_prompt=user_prompt,
                message_footer = message_footer,
                api_key_saved=api_key_saved)



@main_bp.route("/converse_claude", methods=["GET", "POST"])
def converse_claude():
    session_id = validate_session()
    api_key = dict_of_claude_api_keys[ session_id ]
    api_key_saved = len(api_key)

    response = ""
    error = False
    intro_title = "This page allows you to hold a conversation with Claude using your own Anthropic api key.  Please note:"
    intro_bullets = constants.WARNING_BULLETS

    default_prompt = "Please describe me in a haiku.  You can ask questions, but end each response with a haiku.  Try to use all the info you learn about me in the haiku."

    chat_history = session.get("converse_claude_chat_history", [])
    if len(chat_history) == 0:
        user_prompt = default_prompt
    else:
        user_prompt = "any other thoughts?"
    message_footer = ""
    completion = "" # empty is error

    if request.method == "POST":
        if not api_key_saved:
            user_key = request.form.get("api_key", "").strip()
            print("FIX user provided key:", user_key)
            if user_key != "":
                print("saving user provided key as session key")
                session[config.SESSION_CLAUDE_API_KEY] = user_key
                api_key = session[config.SESSION_CLAUDE_API_KEY]
                api_key_saved = True
 
        user_prompt = request.form.get("user_prompt", "").strip()
        t0 = time.time()

        if not user_prompt:
            error = constants.ERROR_EMPTY_PROMPT
        elif len(user_prompt) > constants.MAX_PROMPT_LENGTH:
            error = constants.ERROR_MAX_PROMPT_LENGTH_EXCEEDED
        elif is_rate_limiting_on():
            error = rate_limiter_exceeded()

        if not error:
            try:
                """
                Note that if you want to include a system prompt, 
                you can use the top-level system parameter — 
                there is no "system" role for input messages in the Messages API.
                """

                # if len(chat_history) == 0:                    
                #     chat_history.append({"role": "system", "content": system_content_filter})
                #     print("blank chat_history is now:", chat_history)
                chat_history.append( {"role": "user", "content": user_prompt} )

                client = anthropic.Anthropic(api_key = api_key)

                message = client.messages.create(
                    model=constants.DEFAULT_CLAUDE_MODEL,
                    max_tokens=200,
                    temperature=1,
                    system=constants.SYSTEM_CONTENT_FILTER,
                    messages= chat_history
                )

                completion = message
                response = message.content[0].text


                chat_history.append({"role": "assistant", "content": response})

                session["converse_claude_chat_history"] = chat_history
                session["converse_claude_chat_timestamp"] = datetime.utcnow().isoformat()

                if constants.DEBUG > 0:
                    print("prompt:", user_prompt)
                    print("response:", response)

                user_prompt = "any other thoughts?"

            except Exception as e:
                try:
                    # broken...
                    error_json = e.response.json()
                    if error_json.get("error", {}).get("code") == "invalid_api_key":
                        error = "Invalid API key. Please double-check and try again."
                    else:
                        error = f"Error: {error_json.get('error', {}).get('message', str(e))}"
                except:
                    error = f"Unexpected error: {str(e)}"

        message_footer = ""
        if completion:
            message_footer = "\n\tAnalysis:"
            message_footer += "\n\tResponded with {:d} words in in {:.1f}s".format( len(response.split()), time.time() - t0 )
            message_footer += f"\n\tUsed {completion.usage.input_tokens} prompt tokens and {completion.usage.input_tokens} completion tokens for {completion.usage.input_tokens + completion.usage.output_tokens} total tokens"
            if constants.DEBUG > 0:
                print("message_footer:", message_footer)

        write_applog(f"converse_claude called with len(prompt) { len(user_prompt) } and len(response) { len(response) }")

    return render_template("converse_claude.html", 
                intro_title=intro_title,
                intro_bullets=intro_bullets,
                response=response,
                error=error,
                api_key=api_key,
                user_prompt=user_prompt,
                message_footer = message_footer,
                api_key_saved=api_key_saved,
                chat_history = chat_history)  # for claude, there is no system message to leave out the system message in chat history




@main_bp.route("/test", methods=["GET", "POST"])
def test():
    #main_bp = Blueprint("main", __name__)

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=200,
        temperature=1,
        system="You are a world-class poet. Respond only with short poems.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Why is the ocean salty?"
                    }
                ]
            }
        ]
    )
    print(message.content)
    return render_template("coming_soon.html", label="test")


@main_bp.route("/talk_to_bedrock")
def talk_to_bedrock():
    return render_template("coming_soon.html", label="AWS Bedrock")


@main_bp.route("/clear_chat_chatgpt")
def clear_chat_chatgpt():
    session.pop("converse_chatgpt_chat_history", None)
    session.pop("converse_chatgpt_chat_timestamp", None)
    return redirect(url_for("main.converse_chatgpt"))


@main_bp.route("/clear_chat_claude")
def clear_chat_claude():
    session.pop("converse_claude_chat_history", None)
    session.pop("converse_claude_chat_timestamp", None)
    return redirect(url_for("main.converse_claude"))




@main_bp.route("/forget_keys")
def forget_keys():
    session[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_USER_KEYS

    session_id = get_session_id()
    dict_of_openai_api_keys[ get_session_id() ] = ""
    dict_of_claude_api_keys[ get_session_id() ] = ""


    # session[config.APP_MODE] = config.APP_MODE_USER

    # session[config.OPENAI_API_KEY] = ""
    # session[config.ANTHROPIC_API_KEY] = ""
    print_session_info("forget_keys")
    write_syslog("erasing keys and reset to user mode")
    #return redirect(url_for("main.index"))  # Adjust if your route name is different
    return redirect(request.referrer or "/")


@main_bp.route("/mode_to_server_keys", methods=["GET", "POST"])
def set_mode_to_server_keys():
    validate_session()
    print_session_info("===\nset_mode_to_user_keys...")


    if session[constants.APP_MODE_SETTING] == constants.APP_MODE_VALUE_SERVER_KEYS:
        m = f"ignoring request: { session[constants.APP_MODE_SETTING] } --> {constants.APP_MODE_VALUE_SERVER_KEYS}"
        if constants.DEBUG:        
            print(m)
        write_syslog(m)
    else:
        session[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_SERVER_KEYS
        # reset these keys so validate_session() will reload them
        dict_of_openai_api_keys[get_session_id()] = ""
        dict_of_claude_api_keys[get_session_id()] = ""
        
        validate_session()
        m = f"processed request: { session[constants.APP_MODE_SETTING] } --> {constants.APP_MODE_VALUE_SERVER_KEYS}"
        if constants.DEBUG:        
            print(m)
        write_syslog(m)
    print_session_info("...set_mode_to_server_keys===\n")
    return redirect(url_for("main.index"))


@main_bp.route("/mode_to_user_keys", methods=["GET", "POST"])
def set_mode_to_user_keys():
    print_session_info("set_mode_to_user_keys...")

    session[constants.APP_MODE_SETTING] = constants.APP_MODE_VALUE_USER_KEYS
    dict_of_openai_api_keys[ get_session_id() ] = ""
    dict_of_claude_api_keys[ get_session_id() ] = ""
    validate_session()
    
    print_session_info("...set_mode_to_user_keys")
    return redirect(url_for("main.index"))


def is_rate_limiting_on():
    # for testing, always on
    return True

    if session[constants.APP_MODE_SETTING] in [constants.APP_MODE_VALUE_USER_KEYS, constants.APP_MODE_VALUE_LOCAL_KEYS]:
        return False
    return True
