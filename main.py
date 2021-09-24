from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, join_room
from datetime import datetime

import config
from database import Messages

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
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
    print('JOIN')
    print((message['sender'])['id'])
    print(room)
    query = Messages.update(messages_is_read=True).where(Messages.sender_id == (message['sender'])['id'],
                                                         Messages.messages_is_read == False, Messages.room == room)
    query.execute()
    send({'msg': 'user: ' + str((message['sender'])['id']) + ' has entered the room ' + str(room)}, to=room)


@socketio.on('text')
def text(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id'])
    Messages.create(room=room, sender_id=(message['sender'])['id'], message=message['message'],
                    time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    send(message, to=room)


# @socketio.on('join', namespace='/chat')
# def join(message):
#     room = '123'
#     join_room(room)
#     emit('status', {'msg': 'stepan' + ' has entered the room.'}, room=room)
# @socketio.on('message')
# def handleMessage(msg):
#     send(msg, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
