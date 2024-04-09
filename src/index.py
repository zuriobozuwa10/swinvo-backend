from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/create-workflow", methods = ['POST'])
def create_workflow():
    input_text = request.json('text')
    print(input_text)
    apple = {"message": input_text + "Ayooo 6666"}
    return jsonify(apple)
