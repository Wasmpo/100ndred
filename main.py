import os
import subprocess

# Start both bots and let them run forever
subprocess.Popen(["python", "levelbot.py"])
subprocess.Popen(["python", "devupdates.py"])

# Keep the container alive
while True:
    pass
