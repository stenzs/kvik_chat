from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, join_room
from datetime import datetime
from peewee import fn

import config
from database import Messages

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/', methods=['GET'])
def hello():
    if request.method == 'GET':
        return jsonify({'message': 'chat_server16'}), 200


@app.route('/chat_history', methods=['POST'])
def chat_history():
    if request.method == 'POST':
        data = request.get_json()
        try:
            page_limit = data['page_limit']
            sender_id = data['sender_id']
            recipient_id = data['recipient_id']
            last_message_id = data['last_message_id']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        if recipient_id < sender_id:
            room = str(recipient_id) + '&' + str(sender_id)
        else:
            room = str(sender_id) + '&' + str(recipient_id)
        if last_message_id == 0:
            query = list(Messages.select().where(Messages.sender_id == sender_id, Messages.recipient_id == recipient_id,
                                                 Messages.room == room).dicts().limit(page_limit).order_by(Messages.id.desc()))
        else:
            query = list(Messages.select().where(Messages.sender_id == sender_id,
                                                 Messages.recipient_id == recipient_id, Messages.room == room,
                                                 Messages.id < last_message_id).dicts().limit(page_limit).order_by(Messages.id.desc()))
        return jsonify({'message': 'success', 'data': query}), 200


@app.route('/chat_last_messages', methods=['POST'])
def chat_last_messages():
    if request.method == 'POST':
        data = request.get_json()
        try:
            user_id = data['user_id']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        subq = Messages.select(fn.MAX(Messages.id).alias('room')).group_by(Messages.room).dicts().where((Messages.sender_id == user_id) | (Messages.recipient_id == user_id))
        query = list(Messages.select().where(Messages.id.in_(subq)).dicts())
        return jsonify({'message': 'success', 'data': query}), 200


@socketio.on('join')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id'])
    join_room(room)
    query = Messages.update(messages_is_read=True).where(Messages.sender_id == (message['recipient'])['id'],
                                                         Messages.messages_is_read == False, Messages.room == room)
    query.execute()
    send({'msg': 'user: ' + str((message['sender'])['id']) + ' has entered the room ' + str(room)}, to=room)


@socketio.on('online')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id'])
    query = Messages.update(messages_is_read=True).where(Messages.sender_id == (message['recipient'])['id'],
                                                         Messages.messages_is_read == False, Messages.room == room)
    query.execute()
    send({'msg': 'user: ' + str((message['sender'])['id']) + ' online ' + str(room)}, to=room)


@socketio.on('typing')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id'])
    join_room(room)
    send({'msg': 'user_typing', 'user_t': (message['sender'])['id']}, to=room)


@socketio.on('text')
def text(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id'])
    Messages.create(room=room, sender_id=(message['sender'])['id'], recipient_id=(message['recipient'])['id'],
                    message=message['message'], time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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
