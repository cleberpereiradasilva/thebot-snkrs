from flask import Flask
import subprocess
app = Flask(__name__)

subprocess.Popen(['python','server_runner.py'])

@app.route("/")
def hello_world():
    return {'status' : 'ok'}