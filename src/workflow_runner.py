import subprocess
import sys
import time


def run(workflow_file_path):
  subprocess.run(["nohup", "python3", workflow_file_path, "&"])


while True:
  run(sys.argv[1])
  time.sleep(15)


  