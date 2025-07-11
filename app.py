from flask import Flask
from blueprints.main import main_bp
import os
from datetime import datetime

app = Flask(__name__)
app.register_blueprint(main_bp)

# Log startup time
with open("logs/sys_log.txt", "a") as f:
    f.write(f"App started at {datetime.now()}\n")

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
