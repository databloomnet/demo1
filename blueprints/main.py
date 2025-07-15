import os
from flask import Blueprint, request, render_template, redirect, url_for, current_app
from datetime import datetime, timedelta
import openai
from flask import session, flash # for session mgmt
import time
import config

main_bp = Blueprint('main', __name__)


syslog_c = "logs/sys_log.txt"
applog_c = "logs/app_log.txt"

def write_syslog(s):
    with open(syslog_c, "a") as f:
        f.write(f"{datetime.now()} {request.remote_addr}: {s}\n")




@main_bp.route("/")
def index():
    write_syslog("/ accessed")
    #with open("logs/sys_log.txt", "a") as f:
    #    f.write(f"Accessed at {datetime.now()} from {request.remote_addr}\n")
    return render_template("index.html")

@main_bp.route("/submit_note", methods=["POST"])
def submit_note():
    write_syslog(" note submitted")
    note = request.form.get("note")
    with open(applog_c, "a") as f:
        f.write(f"{datetime.now()} - {note}\n")
    return redirect(url_for("main.index"))

@main_bp.route("/sys_log")
def show_sys_log():
    write_syslog("/sys_log accessed")
    #with open("logs/sys_log.txt", "a") as f:
    #    f.write(f"/sys_log accessed at {datetime.now()} from {request.remote_addr}\n")
    with open(syslog_c) as f:
        #  lines = f.readlines()
        lines = [line.strip() for line in f.readlines()]  # <--- strip newlines
    return render_template("sys_log.html", log=lines)

@main_bp.route("/app_log")
def show_app_log():
    write_syslog("app_log accessed")
    #with open("logs/sys_log.txt", "a") as f:
    #    f.write(f"/app_log accessed at {datetime.now()} from {request.remote_addr}\n")
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



@main_bp.route("/talk_to_claude")
def talk_to_claude():
    return render_template("coming_soon.html", label="Claude")



@main_bp.route("/query_chatgpt", methods=["GET", "POST"])
def query_chatgpt():
    openai_api_key = ""
    openai_api_key_saved = False
    
    if config.GLOBAL_OPENAI_API_KEY in current_app.config:
        tmp_key = current_app.config[config.GLOBAL_OPENAI_API_KEY]
        if tmp_key != "":
            #if config.GLOBAL_OPENAI_API_KEY != "":            
            print("using global_openai_api_key")
            openai_api_key_saved = True
            openai_api_key = tmp_key

    if config.SESSION_OPENAI_API_KEY in session:
        tmp_key = session[config.SESSION_OPENAI_API_KEY]
        if tmp_key != "":            
            print("using session_openai_api_key")
            openai_api_key_saved = True
            openai_api_key = tmp_key


    # print("openai_api_key>", openai_api_key, "<")
    response = None
    error = None
    intro_title = "This page allows you to ask ChatGPT a single question using your own OpenAI api key.  Please note:"
    intro_bullets = current_app.config[config.WARNING_BULLETS]
    default_prompt = "In 25 words or less, how can we improve our world?"
    user_prompt = default_prompt

    message_footer = ""
    if request.method == "POST":
        if not openai_api_key_saved:
            user_key = request.form.get("api_key", "").strip()
            print("user provided key:", user_key)
            if user_key != "":
                print("saving user provided key as session key")
                session[config.SESSION_OPENAI_API_KEY] = user_key
                openai_api_key = session[config.SESSION_OPENAI_API_KEY]
                openai_api_key_saved = True
 

        user_prompt = request.form.get("user_prompt", "").strip()
        completion_full = False

        t0 = time.time()
        # print(len(user_prompt))

        if not openai_api_key_saved and not openai_api_key:
            error = "oops - I need a key"
        elif not user_prompt:
            error = "prompt can't be empty"
        elif len(user_prompt) > 300:
            error = "prompt too long - I'm cheap"
        else:
            try:
                client = openai.OpenAI(api_key=openai_api_key)
                messages = [
                    {"role": "system", "content": "You are a helpful assistant.  If anyone uses any very inappropriate langauge you will respond with this exact phrase: \'I decline to engage in such rude discussion\'"},
                    #{"role": "system", "content": "You are a helpful assistant.\'"},
                    {"role": "user", "content": user_prompt}
                ]

                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # You can choose other models like "gpt-4"
                    messages=messages
                )

                completion_full = completion
                response = completion.choices[0].message.content

            except Exception as e:
                try:
                    # Try to parse the error and look for OpenAI-style structured error
                    error_json = e.response.json()
                    if error_json.get("error", {}).get("code") == "invalid_api_key":
                        error = "Invalid API key. Please double-check and try again."
                    else:
                        error = f"OpenAI Error: {error_json.get('error', {}).get('message', str(e))}"
                except:
                    # Fallback if it's not a typical OpenAI response
                    error = f"Unexpected error: {str(e)}"

        message_footer = ""
        if completion_full:
            message_footer = "\n\tAnalysis:"
            message_footer += "\n\tResponded with {:d} words in in {:.1f}s".format( len(response.split()), time.time() - t0 )

            message_footer += "\n\tUsed {:d} prompt tokens and {:d} completion tokens for {:d} total tokens".format(completion_full.usage.prompt_tokens,
                completion_full.usage.completion_tokens, completion_full.usage.prompt_tokens + completion_full.usage.completion_tokens)

    return render_template("query_chatgpt.html", 
                intro_title=intro_title,
                intro_bullets=intro_bullets,
                response=response,
                error=error,
                openai_api_key=openai_api_key,
                user_prompt=user_prompt,
                message_footer = message_footer,
                api_key_saved=openai_api_key_saved)





@main_bp.route("/converse_chatgpt", methods=["GET", "POST"])
def converse_chatgpt():
    openai_api_key = ""
    openai_api_key_saved = False
    
    if config.GLOBAL_OPENAI_API_KEY in current_app.config:
        tmp_key = current_app.config[config.GLOBAL_OPENAI_API_KEY]
        if tmp_key != "":
            #if config.GLOBAL_OPENAI_API_KEY != "":            
            print("using global_openai_api_key")
            openai_api_key_saved = True
            openai_api_key = tmp_key

    if config.SESSION_OPENAI_API_KEY in session:
        tmp_key = session[config.SESSION_OPENAI_API_KEY]
        if tmp_key != "":            
            print("using session_openai_api_key")
            openai_api_key_saved = True
            openai_api_key = tmp_key


    print("openai_api_key>", openai_api_key, "<")
    response = None
    error = None
    intro_title = "This page allows you to hold a conversation with ChatGPT using your own OpenAI api key.  Please note:"
    intro_bullets = current_app.config[config.WARNING_BULLETS]



    default_prompt = "Please describe me in a haiku.  You can ask questions, but end each response with a haiku.  Try to use all the info you learn about me in the haiku."
    # user_prompt = default_prompt

    chat_history = session.get("chat_history", [])
    if len(chat_history) == 0:
        user_prompt = default_prompt
    else:
        user_prompt = "any other thoughts?"
    message_footer = ""

    print("222")
    print("user_prompt", user_prompt)
    print("chat_history", chat_history)

    if request.method == "POST":
        if not openai_api_key_saved:
            user_key = request.form.get("api_key", "").strip()
            print("user provided key:", user_key)
            if user_key != "":
                print("saving user provided key as session key")
                session[config.SESSION_OPENAI_API_KEY] = user_key
                openai_api_key = session[config.SESSION_OPENAI_API_KEY]
                openai_api_key_saved = True
 

        user_prompt = request.form.get("user_prompt", "").strip()
        #completion_full = False

        t0 = time.time()
        # print(len(user_prompt))

        if not openai_api_key_saved and not openai_api_key:
            error = "oops - I need a key"
        elif not user_prompt:
            error = "prompt can't be empty"
        elif len(user_prompt) > 300:
            error = "prompt too long - I'm cheap"
        else:
            try:
                if len(chat_history) == 0:                    
                    chat_history.append( {"role": "system",
                        "content": "You are a helpful assistant.  If anyone uses any very inappropriate langauge you will respond with this exact phrase: \'I decline to engage in such rude discussion\'"} )
                    #chat_history.append( {"role": "user",
                    #    "content": "How would you describe me in a haiku?  You can ask questions to get to know me better."} )
                    print("blank chat_history is now:", chat_history)
                chat_history.append( {"role": "user", "content": user_prompt} )


                client = openai.OpenAI(api_key=openai_api_key)
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=chat_history,
                    response_format={"type": "text"}  # works
                )

                completion_full = completion
                response = completion.choices[0].message.content
                chat_history.append({"role": "assistant", "content": response})

                session["chat_history"] = chat_history
                #session["chat_timestamp"] = now.isoformat()
                session["chat_timestamp"] = datetime.utcnow().isoformat()

                user_prompt = "any other thoughts?"

                #message_footer = f"\nResponded in {time.time() - t0:.1f} seconds using gpt-3.5-turbo"
                print("response", response)

            except Exception as e:
                try:
                    # Try to parse the error and look for OpenAI-style structured error
                    error_json = e.response.json()
                    if error_json.get("error", {}).get("code") == "invalid_api_key":
                        error = "Invalid API key. Please double-check and try again."
                    else:
                        error = f"OpenAI Error: {error_json.get('error', {}).get('message', str(e))}"
                except:
                    # Fallback if it's not a typical OpenAI response
                    error = f"Unexpected error: {str(e)}"

        message_footer = ""
        if completion_full:
            message_footer = "\n\tAnalysis:"
            message_footer += "\n\tResponded with {:d} words in in {:.1f}s".format( len(response.split()), time.time() - t0 )

            message_footer += "\n\tUsed {:d} prompt tokens and {:d} completion tokens for {:d} total tokens".format(completion_full.usage.prompt_tokens,
                completion_full.usage.completion_tokens, completion_full.usage.prompt_tokens + completion_full.usage.completion_tokens)
            print("message_footer:", message_footer)

    return render_template("converse_chatgpt.html", 
                intro_title=intro_title,
                intro_bullets=intro_bullets,
                response=response,
                error=error,
                openai_api_key=openai_api_key,
                user_prompt=user_prompt,
                message_footer = message_footer,
                api_key_saved=openai_api_key_saved,
                chat_history = chat_history[1:])  # leave out the system message in chat history

@main_bp.route("/talk_to_bedrock")
def talk_to_bedrock():
    return render_template("coming_soon.html", label="AWS Bedrock")



@main_bp.route("/converse_chatgptOLD", methods=["GET", "POST"])
def converse_chatgptOLD():
    now = datetime.utcnow()

    # Reset chat if older than 5 minutes or not initialized
    if "chat_timestamp" not in session or now - datetime.fromisoformat(session["chat_timestamp"]) > timedelta(minutes=1):
        session["chat_history"] = []
        session["chat_timestamp"] = now.isoformat()

    response = None
    error = None
    intro_title = "This page allows you to converse with ChatGPT in a session using your own OpenAI api key.  Please note:"
    intro_bullets = current_app.config["warning_bullets"]
    default_prompt = "In 25 words or less, how would you describe my personality?  It's ok to ask short questions to get to know me."
    user_prompt = default_prompt

    openai_api_key = current_app.config["openai_api_key"]


    chat_history = session.get("chat_history", [])
    user_input = ""

    message_footer = ""
    if request.method == "POST":
        openai_api_key = request.form.get("api_key", "").strip()
        user_prompt = request.form.get("user_prompt", "").strip()
        completion_full = False

        if not openai_api_key:
            error = "oops - I need a key"
        elif not user_prompt:
            error = "prompt can't be empty"
        elif len(user_prompt) > 300:
            error = "prompt too long - I'm cheap"

        else:
            try:
                # Add user message to history
                chat_history.append({"role": "user", "content": user_prompt})
                # Call OpenAI
                client = openai.OpenAI(api_key=openai_api_key)
                result = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=chat_history,
                    response_format={"type": "text"}  # works
                )


                assistant_message = result.choices[0].message.content
                chat_history.append({"role": "assistant", "content": assistant_message})

                session["chat_history"] = chat_history
                session["chat_timestamp"] = now.isoformat()
                response = assistant_message

            except Exception as e:
                error = f"ChatGPT Error: {str(e)}"

        if completion_full:
            pass


    return render_template("converse_chatgpt.html",
                            intro_title=intro_title,
                            intro_bullets=intro_bullets,
                            chat_history=session.get("chat_history", []),
                            response=response,
                            error=error,
                            openai_api_key=openai_api_key,
                            user_prompt=user_prompt,
                            message_footer = message_footer
                        )

@main_bp.route("/forget_keys")
def forget_keys():
    session.pop(config.SESSION_OPENAI_API_KEY, None)
    session.pop(config.SESSION_CLAUDE_API_KEY, None)
    current_app.config[config.GLOBAL_OPENAI_API_KEY] = ""
    current_app.config[config.GLOBAL_CLAUDE_API_KEY] = ""
    write_syslog("all api keys deletes")
    #flash("All api keys removed.")
    return redirect(url_for("main.index"))  # Adjust if your route name is different
    #return redirect(url_for("query_chatgpt"))  # Adjust if your route name is different
