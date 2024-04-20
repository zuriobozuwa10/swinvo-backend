from workflow import Workflow
import time
import pickle

flow = Workflow() # TODO: We construct workflow here but we're gonna get passed it from pickle instead

while True:
    flow.RunOnce()
    time.sleep(10)

