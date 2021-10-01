from peewee import *
import config

db = PostgresqlDatabase(database=config.database, user=config.user, password=config.password, host=config.host,
                        port=config.port, autocommit=True, autorollback=True)


class BaseModel(Model):
    class Meta:
        database = db


class Messages(BaseModel):
    id = PrimaryKeyField(column_name='id', primary_key=True, unique=True)
    room = TextField(column_name='room')
    sender_id = IntegerField(column_name='sender_id')
    recipient_id = IntegerField(column_name='recipient_id')
    message = TextField(column_name='message', null=True)
    messages_is_read = BooleanField(column_name='messages_is_read', default=False)
    time = TextField(column_name='time')
    delete = BooleanField(column_name='delete', default=False)

    class Meta:
        table_name = 'messages'


class Rooms(BaseModel):
    id = PrimaryKeyField(column_name='id', primary_key=True, unique=True)
    name = TextField(column_name='name')
    seller_id = IntegerField(column_name='seller_id')
    seller_name = TextField(column_name='seller_name')
    seller_photo = TextField(column_name='seller_photo')
    customer_id = IntegerField(column_name='customer_id')
    customer_name = TextField(column_name='customer_name')
    customer_photo = TextField(column_name='customer_photo')
    product_id = IntegerField(column_name='product_id')
    product_name = TextField(column_name='product_name')
    product_photo = TextField(column_name='product_photo')
    product_price = IntegerField(column_name='product_price')

    class Meta:
        table_name = 'rooms'


db.create_tables([Rooms])
