import os
import subprocess
import time

# Start both bots
subprocess.Popen(["python", "levelbot.py"])
subprocess.Popen(["python", "devupdates.py"])

# Keep the container alive
while True:
    time.sleep(60)
