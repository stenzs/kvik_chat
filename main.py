import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send, join_room, leave_room
from datetime import datetime
from peewee import fn
import requests
import config
from database import Messages, Rooms, Tokens

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/', methods=['GET'])
def hello():
    if request.method == 'GET':
        return jsonify({'message': 'chat_server16'}), 200


@app.route('/push_token', methods=['POST'])
def push_token():
    if request.method == 'POST':
        data = request.get_json()
        try:
            user_id = data['user_id']
            platform = data['platform']
            token = data['token']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        check_token = Tokens.get_or_none(Tokens.token == token)
        if check_token is None:
            Tokens.create(user_id=user_id, platform=platform, token=token)
        else:
            if check_token.user_id != user_id:
                tokendel = Tokens.get(Tokens.token == token)
                tokendel.delete_istance()
                Tokens.create(user_id=user_id, platform=platform, token=token)
        return jsonify({'message': 'success'}), 200

@app.route('/send_push', methods=['POST'])
def send_push():
    if request.method == 'POST':
        data = request.get_json()
        try:
            user_id = data['user_id']
            message = data['message']
            user_name = data['user_name']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        token_list = list(Tokens.select().where(Tokens.user_id == user_id).dicts())
        web_tokens = []
        ios_tokens = []
        android_tokens = []
        for string in token_list:
            if string['platform'] == 3:
                web_tokens.append(string['token'])
            elif string['platform'] == 2:
                ios_tokens.append(string['token'])
            elif string['platform'] == 1:
                android_tokens.append(string['token'])
        answer = []
        if len(web_tokens) > 0:
            for token in web_tokens:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + config.web_token_key
                }
                body = {
                    'notification': {
                        'title': 'KVIK',
                        'body': 'У тебя новое сообщение от ' + user_name + ':\n' + message},
                    'to': token, 'priority': 'high'}
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))
                answer.append(response.json())
                print(response.json())
        return jsonify({"message": 'success', "answers": answer})


@app.route('/chat_history', methods=['POST'])
def chat_history():
    if request.method == 'POST':
        data = request.get_json()
        try:
            page_limit = data['page_limit']
            sender_id = data['user_id']
            recipient_id = data['companion_id']
            last_message_id = data['last_message_id']
            product_id = data['product_id']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        if recipient_id < sender_id:
            room = str(recipient_id) + '&' + str(sender_id) + '&' + str(product_id)
        else:
            room = str(sender_id) + '&' + str(recipient_id) + '&' + str(product_id)
        check_room = Rooms.get_or_none(Rooms.name == room)
        if check_room is None:
            return jsonify({'message': 'invalid room'}), 422
        if last_message_id == 0:
            query = list(Messages.select().where(Messages.room == room, Messages.delete != True).dicts().limit(page_limit).order_by(Messages.id.desc()))
            return jsonify({'message': 'success', 'data': query, 'room': {'seller_id': check_room.seller_id, 'customer_id': check_room.customer_id, 'product_id': check_room.product_id}}), 200
        else:
            query = list(Messages.select().where(Messages.room == room,
                                                 Messages.id < last_message_id, Messages.delete != True).dicts().limit(page_limit).order_by(Messages.id.desc()))
            return jsonify({'message': 'success', 'data': query}), 200


@app.route('/chat_last_messages', methods=['POST'])
def chat_last_messages():
    if request.method == 'POST':
        data = request.get_json()
        try:
            user_id = data['user_id']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        subq = Messages.select(fn.MAX(Messages.id).alias('room')).group_by(Messages.room).dicts().where(((Messages.sender_id == user_id) & (Messages.delete != True)) | ((Messages.recipient_id == user_id) & (Messages.delete != True)))
        query = list(Messages.select(Messages.message, Messages.messages_is_read, Messages.sender_id, Messages.time, Rooms.seller_id, Rooms.customer_id, Rooms.product_id).where(Messages.id.in_(subq)).dicts().order_by(Messages.id.desc()).join(Rooms, on=(Messages.room == Rooms.name)))
        return jsonify({'message': 'success', 'data': list(query)}), 200


@app.route('/make_room', methods=['POST'])
def make_room():
    if request.method == 'POST':
        data = request.get_json()
        try:
            seller_id = data['seller_id']
            customer_id = data['customer_id']
            product_id = data['product_id']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        if seller_id < customer_id:
            room = str(seller_id) + '&' + str(customer_id) + '&' + str(product_id)
        else:
            room = str(customer_id) + '&' + str(seller_id) + '&' + str(product_id)
        check_room = Rooms.get_or_none(Rooms.name == room)
        if check_room is None:
            Rooms.create(name=room, seller_id=seller_id, customer_id=customer_id, product_id=product_id)
            return jsonify({'message': 'room created'}), 200
        return jsonify({'message': 'room already exist'}), 403


@socketio.on('join')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id']) + '&' + str((message['product'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id']) + '&' + str((message['product'])['id'])
    join_room(room)
    query = Messages.update(messages_is_read=True).where(Messages.sender_id == (message['recipient'])['id'],
                                                         Messages.messages_is_read == False, Messages.room == room)
    query.execute()
    send({'msg': 'user_join', 'user_jo': (message['sender'])['id']}, to=room)


@socketio.on('leave')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id']) + '&' + str((message['product'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id']) + '&' + str((message['product'])['id'])
    leave_room(room)
    send({'msg': 'user_leave', 'user_le': (message['sender'])['id']}, to=room)


@socketio.on('online')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id']) + '&' + str((message['product'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id']) + '&' + str((message['product'])['id'])
    query = Messages.update(messages_is_read=True).where(Messages.sender_id == (message['recipient'])['id'],
                                                         Messages.messages_is_read == False, Messages.room == room)
    query.execute()
    send({'msg': 'user_online', 'user_on': (message['sender'])['id']}, to=room)


@socketio.on('typing')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id']) + '&' + str((message['product'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id']) + '&' + str((message['product'])['id'])
    join_room(room)
    send({'msg': 'user_typing', 'user_t': (message['sender'])['id']}, to=room)


@socketio.on('text')
def text(message):
    print(message)
    print(message['time'])
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id']) + '&' + str((message['product'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id']) + '&' + str((message['product'])['id'])
    if len(message['message']) > 1000:
        send({'msg': 'msg_to_looooong'}, to=room)
    else:
        time_dict = {"y": datetime.now().strftime("%Y"), "mo": datetime.now().strftime("%m"),
                 "d": datetime.now().strftime("%d"), "h": datetime.now().strftime("%H"),
                 "mi": datetime.now().strftime("%M")}
        time = json.dumps(time_dict)
        Messages.create(room=room, sender_id=(message['sender'])['id'], recipient_id=(message['recipient'])['id'],
                        message=message['message'], time=time)
        send(message, to=room)


if __name__ == '__main__':
    socketio.run(app, debug=True)
