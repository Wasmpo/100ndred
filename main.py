import os
import subprocess
import time

def start_bot(bot_file, token_var):
    token = os.getenv(token_var)
    if token:
        print(f"🚀 Starting {bot_file}...")
        # Start bot and redirect output to log file
        with open(f"{bot_file}.log", "w") as log_file:
            subprocess.Popen(
                ["python", bot_file],
                stdout=log_file,
                stderr=log_file
            )
    else:
        print(f"❌ Missing token for {bot_file}!")

if __name__ == "__main__":
    # Start bots
    start_bot("levelbot.py", "DISCORD_TOKEN")
    start_bot("devupdates.py", "ANNOUNCE_TOKEN")
    
    # Keep the process running
    while True:
        time.sleep(60)  # Prevent high CPU usage
