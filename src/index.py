from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/create-workflow", methods = ['POST'])
def create_workflow():
    return ("Ayoooo 99999")
