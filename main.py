from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send, join_room
from datetime import datetime
from peewee import fn

import config
from database import Messages, Rooms

app = Flask(__name__)
CORS(app)
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
        if last_message_id == 0:
            query = list(Messages.select().where(Messages.room == room, Messages.delete != True).dicts().limit(page_limit).order_by(Messages.id.desc()))
            check_room = Rooms.get_or_none(Rooms.name == room)
            if check_room is None:
                return jsonify({'message': 'success', 'data': query, 'room': None}), 200
            else:
                return jsonify({'message': 'success', 'data': query, 'room': {'seller_id': check_room.seller_id, 'seller_name': check_room.seller_name, 'seller_photo': check_room.seller_photo, 'customer_id': check_room.customer_id, 'customer_name': check_room.customer_name, 'customer_photo': check_room.customer_photo, 'product_id': check_room.product_id, 'product_name': check_room.product_name, 'product_photo': check_room.product_photo, 'product_price': check_room.product_price}}), 200
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

        query = list(Messages.select(Messages.message, Messages.messages_is_read, Messages.sender_id, Messages.time, Rooms.seller_id, Rooms.seller_name, Rooms.seller_photo, Rooms.customer_id, Rooms.customer_name, Rooms.customer_photo, Rooms.product_id, Rooms.product_name, Rooms.product_photo, Rooms.product_price).where(Messages.id.in_(subq)).dicts().order_by(Messages.id.desc()).join(Rooms, on=(Messages.room == Rooms.name)))
        # query = list(Messages.select(Messages.message, Messages.messages_is_read, Messages.sender_id, Messages.time, Rooms.seller_id, Rooms.seller_name, Rooms.seller_photo, Rooms.customer_id, Rooms.customer_name, Rooms.customer_photo, Rooms.product_id, Rooms.product_name, Rooms.product_photo).where(Messages.id.in_(subq)).dicts().order_by(Messages.id.desc()))

        return jsonify({'message': 'success', 'data': list(query)}), 200


@app.route('/make_room', methods=['POST'])
def make_room():
    if request.method == 'POST':
        data = request.get_json()
        try:
            seller_id = data['seller_id']
            seller_name = data['seller_name']
            seller_photo = data['seller_photo']
            customer_id = data['customer_id']
            customer_name = data['customer_name']
            customer_photo = data['customer_photo']
            product_id = data['product_id']
            product_name = data['product_name']
            product_photo = data['product_photo']
            product_price = data['product_price']
        except KeyError:
            return jsonify({'message': 'invalid data'}), 422
        if seller_id < customer_id:
            room = str(seller_id) + '&' + str(customer_id) + '&' + str(product_id)
        else:
            room = str(customer_id) + '&' + str(seller_id) + '&' + str(product_id)
        check_room = Rooms.get_or_none(Rooms.name == room)
        if check_room is None:
            Rooms.create(name=room, seller_id=seller_id, seller_name=seller_name, seller_photo=seller_photo,
                         customer_id=customer_id, customer_name=customer_name, customer_photo=customer_photo,
                         product_id=product_id, product_name=product_name, product_photo=product_photo,
                         product_price=product_price)
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
    send({'msg': 'user: ' + str((message['sender'])['id']) + ' has entered the room ' + str(room)}, to=room)


@socketio.on('online')
def join(message):
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id']) + '&' + str((message['product'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id']) + '&' + str((message['product'])['id'])
    query = Messages.update(messages_is_read=True).where(Messages.sender_id == (message['recipient'])['id'],
                                                         Messages.messages_is_read == False, Messages.room == room)
    query.execute()
    send({'msg': 'user: ' + str((message['sender'])['id']) + ' online in the room ' + str(room)}, to=room)


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
    if (message['recipient'])['id'] < (message['sender'])['id']:
        room = str((message['recipient'])['id']) + '&' + str((message['sender'])['id']) + '&' + str((message['product'])['id'])
    else:
        room = str((message['sender'])['id']) + '&' + str((message['recipient'])['id']) + '&' + str((message['product'])['id'])
    Messages.create(room=room, sender_id=(message['sender'])['id'], recipient_id=(message['recipient'])['id'],
                    message=message['message'], time=datetime.now().strftime(str({"y": "%Y", "mo": "%m", "d": "%d",
                                                                              "h": "%H", "mi": "%M"})))
    send(message, to=room)


if __name__ == '__main__':
    socketio.run(app, debug=True)
