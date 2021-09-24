from peewee import *
import config

db = PostgresqlDatabase(database=config.database, user=config.user, password=config.password, host=config.host, port=config.port, autocommit=True, autorollback=True)


class BaseModel(Model):
    class Meta:
        database = db


class Messages(BaseModel):
    id = PrimaryKeyField(column_name='id', primary_key=True, unique=True)
    room = TextField(column_name='room')
    sender_id = IntegerField(column_name='sender_id')
    message = TextField(column_name='message', null=True)
    messages_isRead = BooleanField(column_name='messages_isRead', default=False)
    time = TextField(column_name='time')
    delete = BooleanField(column_name='delete', default=False)

    class Meta:
        table_name = 'messages'


# db.create_tables([Messages])
