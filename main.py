import os
import subprocess
import time
import sys

def run_bot(bot_file):
    try:
        process = subprocess.Popen(["python", bot_file])
        print(f"Started {bot_file} with PID {process.pid}")
        return process
    except Exception as e:
        print(f"Failed to start {bot_file}: {e}")
        return None

# Start both bots
levelbot = run_bot("levelbot.py")
devupdates = run_bot("devupdates.py")

if not levelbot or not devupdates:
    print("Failed to start one or more bots, exiting")
    sys.exit(1)

# Keep the container alive
while True:
    time.sleep(60)
