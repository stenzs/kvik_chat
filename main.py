from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/', methods=['GET'])
def hello():
    if request.method == 'GET':
        return jsonify({'message': 'chat_server16'}), 200

@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + str(msg))
    send(msg, broadcast=True)

@socketio.on('username', namespace='/private')
def receive_username(username):
    print(request.sid)
    print(username)
    send(str(username) + ' ' + str(request.sid))


if __name__ == '__main__':
    socketio.run(app)