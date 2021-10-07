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
    customer_id = IntegerField(column_name='customer_id')
    product_id = IntegerField(column_name='product_id')

    class Meta:
        table_name = 'rooms'


class Tokens(BaseModel):
    id = PrimaryKeyField(column_name='id', primary_key=True, unique=True)
    user_id = IntegerField(column_name='user_id')
    platform = IntegerField(column_name='platform')
    token = TextField(column_name='token', unique=True)

    class Meta:
        table_name = 'tokens'


db.create_tables([Tokens])
