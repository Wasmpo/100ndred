from flask import Flask
import os
import subprocess
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bots are running!"

def run_flask():
    app.run(host='0.0.0.0', port=8000)

def start_bot(bot_file, token_var):
    token = os.getenv(token_var)
    if token:
        print(f"🚀 Starting {bot_file}...")
        # Log bot output to debug crashes
        with open(f"{bot_file}.log", "w") as log_file:
            subprocess.Popen(
                ["python", bot_file],
                stdout=log_file,
                stderr=log_file
            )
    else:
        print(f"❌ Missing token for {bot_file}!")

if __name__ == "__main__":
    # Start Flask server
    threading.Thread(target=run_flask, daemon=True).start()

    # Start bots (only once)
    if not os.environ.get("BOTS_STARTED"):
        os.environ["BOTS_STARTED"] = "1"
        start_bot("levelbot.py", "DISCORD_TOKEN")
        start_bot("devupdates.py", "ANNOUNCE_TOKEN")

    # Keep alive
    while True:
        pass