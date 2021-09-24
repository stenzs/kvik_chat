from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from datetime import datetime
from database import Messages

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/', methods=['GET'])
def hello():
    if request.method == 'GET':
        return jsonify({'message': 'chat_server16'}), 200


@socketio.on('join')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id'])
    join_room(room)
    print("JOIN  " + room)
    send({'msg': 'user: ' + str((message['sender'])['id']) + ' has entered the room ' + str(room)}, to=room)

@socketio.on('text')
def text(message):
    print(message)
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id'])
    Messages.create(room=room, sender_id=(message['sender'])['id'], message=message['message'], time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    send(message, to=room)
    print(request.sid)
    print('ok')

# @socketio.on('join', namespace='/chat')
# def join(message):
#     print(message)
#     room = '123'
#     join_room(room)
#     emit('status', {'msg': 'stepan' + ' has entered the room.'}, room=room)

# @socketio.on('message')
# def handleMessage(msg):
#     print(request.sid)
#     print('Message: ' + str(msg))
#     send(msg, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
