from flask import Flask, render_template
from flask_socketio import SocketIO,emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/")
def index():
    return render_template('log.html')

@app.route("/login", methods = ["POST","GET"])
def login():
    #to do:
    #login authentication here

    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, debug=True)
