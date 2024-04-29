import subprocess
import sys
import time
import os

from database_accessor import DatabaseAccessor

database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD'))

def run(workflow_file_path):
  subprocess.run(["nohup", "python3", workflow_file_path, "&"])


while True:
  if database.CheckIfWorkflowIsOnById(sys.argv[2]):
    run(sys.argv[1])
    time.sleep(15)


  