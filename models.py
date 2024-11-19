from datetime import datetime
import uuid
from . import dynamodb, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .config import Config

class DynamoDBModel:
    table = dynamodb.Table(Config.DYNAMODB_TABLE)

    @classmethod
    def create_partition_key(cls):
        return str(uuid.uuid4())

class User(UserMixin, DynamoDBModel):
    def __init__(self, email, password=None, first_name=None, last_name=None, is_trustee=False):
        self.id = self.create_partition_key()
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_trustee = is_trustee
        self.created_at = datetime.utcnow().isoformat()
        if password:
            self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self):
        item = {
            'PK': f'USER#{self.id}',
            'SK': f'PROFILE#{self.id}',
            'type': 'user',
            'id': self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_trustee': self.is_trustee,
            'created_at': self.created_at
        }
        self.table.put_item(Item=item)

    @classmethod
    def get_by_id(cls, user_id):
        response = cls.table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PROFILE#{user_id}'
            }
        )
        if 'Item' not in response:
            return None
        return cls.from_dynamo_item(response['Item'])

    @classmethod
    def get_by_email(cls, email):
        response = cls.table.query(
            IndexName='EmailIndex',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        if not response['Items']:
            return None
        return cls.from_dynamo_item(response['Items'][0])

    @staticmethod
    def from_dynamo_item(item):
        user = User(
            email=item['email'],
            first_name=item.get('first_name'),
            last_name=item.get('last_name'),
            is_trustee=item.get('is_trustee', False)
        )
        user.id = item['id']
        user.password_hash = item['password_hash']
        user.created_at = item['created_at']
        return user

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

class Trustee(DynamoDBModel):
    def __init__(self, user_id, trustee_user_id):
        self.id = self.create_partition_key()
        self.user_id = user_id
        self.trustee_user_id = trustee_user_id
        self.notification_triggered = False
        self.triggered_at = None

    def save(self):
        item = {
            'PK': f'USER#{self.user_id}',
            'SK': f'TRUSTEE#{self.id}',
            'type': 'trustee',
            'id': self.id,
            'user_id': self.user_id,
            'trustee_user_id': self.trustee_user_id,
            'notification_triggered': self.notification_triggered,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None
        }
        self.table.put_item(Item=item)

class Message(DynamoDBModel):
    def __init__(self, user_id, recipient_id, content, media_url=None, delay_days=0):
        self.id = self.create_partition_key()
        self.user_id = user_id
        self.recipient_id = recipient_id
        self.content = content
        self.media_url = media_url
        self.delay_days = delay_days
        self.created_at = datetime.utcnow().isoformat()
        self.sent_at = None

    def save(self):
        item = {
            'PK': f'USER#{self.user_id}',
            'SK': f'MESSAGE#{self.id}',
            'type': 'message',
            'id': self.id,
            'user_id': self.user_id,
            'recipient_id': self.recipient_id,
            'content': self.content,
            'media_url': self.media_url,
            'delay_days': self.delay_days,
            'created_at': self.created_at,
            'sent_at': self.sent_at
        }
        self.table.put_item(Item=item)

class Asset(DynamoDBModel):
    def __init__(self, user_id, name, description=None, asset_type=None, value=None, location=None):
        self.id = self.create_partition_key()
        self.user_id = user_id
        self.name = name
        self.description = description
        self.asset_type = asset_type
        self.value = value
        self.location = location

    def save(self):
        item = {
            'PK': f'USER#{self.user_id}',
            'SK': f'ASSET#{self.id}',
            'type': 'asset',
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'asset_type': self.asset_type,
            'value': self.value,
            'location': self.location
        }
        self.table.put_item(Item=item)

class LastWishes(DynamoDBModel):
    def __init__(self, user_id, funeral_preferences=None, special_requests=None, personal_message=None):
        self.id = self.create_partition_key()
        self.user_id = user_id
        self.funeral_preferences = funeral_preferences
        self.special_requests = special_requests
        self.personal_message = personal_message
        self.updated_at = datetime.utcnow().isoformat()

    def save(self):
        item = {
            'PK': f'USER#{self.user_id}',
            'SK': f'WISHES#{self.id}',
            'type': 'last_wishes',
            'id': self.id,
            'user_id': self.user_id,
            'funeral_preferences': self.funeral_preferences,
            'special_requests': self.special_requests,
            'personal_message': self.personal_message,
            'updated_at': self.updated_at
        }
        self.table.put_item(Item=item)
