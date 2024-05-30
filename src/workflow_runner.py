import subprocess
import sys
import time
import os

from database_accessor import DatabaseAccessor

database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD'))

def run(workflow_file_path, workflow_id):
  process = subprocess.Popen(["nohup", "python3", workflow_file_path, workflow_id, "&"])
  return_code = process.wait()
  if return_code == 0:
    database.SetWorkflowToGood(workflow_id)
  else:
    database.SetWorkflowToError(workflow_id)

while True:
  if database.CheckIfWorkflowIsOnById(sys.argv[2]):
    run(sys.argv[1], sys.argv[2]) # index 1 is workflow file path, index 2 is workflow id (mongo)
    time.sleep(15)


  