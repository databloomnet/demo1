"""

great expectations
the illiad
beowoulf


Candida albicans can facilitate the invasion of Staphylococcus aureus into host tissue by providing a surface for the bacteria to adhere to and be transported into the body


"""

import platform
import getpass

from flask import Flask
import config
from blueprints.main import main_bp
import os
from datetime import datetime

import random
import string

def get_random_alphanumeric(length=16):
    chars = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(random.choices(chars, k=length))

default_port_C = 5000
default_port_local_C = 5001

app = Flask(__name__)
app.config[config.GLOBAL_OPENAI_API_KEY] = ""
app.config[config.WARNING_BULLETS] = [
    "While I don't record any api keys, this app is just a prototype and may be vulnerable to hijacking.",
    "Do not use any high valuation keys.  I am not responsible for stolen keys.",
    "Sessions may be intercepted, so don't share private info.  You can close session manually as needed.",
    "If we're acquainted, I/Jeremy would be happy to share one of my keys.",
    ]




app.secret_key = get_random_alphanumeric()
app.register_blueprint(main_bp)



# Log startup time
with open("logs/sys_log.txt", "a") as f:
    f.write(f"{datetime.now()} App started\n")


if 0:
    print(f"OS: {platform.system()}")           # macOS, Linux, Windows
    print(f"OS Release: {platform.release()}")  # version number
    print(f"OS Version: {platform.version()}")  # detailed version
    print(f"Architecture: {platform.machine()}") # x86_64, arm64, etc.
    print(f"Username: {getpass.getuser()}")     # current user


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    port = default_port_C
    if getpass.getuser() == 'jeremybloom':
        port = default_port_local_C
        
        # ONLY SOMETIMES USE THE BELOW
        app.config[config.GLOBAL_OPENAI_API_KEY] = os.environ.get("OPENAI_API_KEY")
        app.config[config.GLOBAL_CLAUDE_API_KEY] = os.environ.get("ANTHROPIC_API_KEY")
        
        #print("openai key:", app.config[config.GLOBAL_OPENAI_API_KEY])
        #print("claude key:", app.config[config.GLOBAL_CLAUDE_API_KEY])

    app.run(host="0.0.0.0", port=port, debug=True) # debug=True will have app restart if any code changes




# i do not save or record your api key.  But I don't want to be blamed, so use this one...



# talk to clauded (uses your api key)
# talk to chatgpt (uses your api key)
# talk to SOMEONE via aws
