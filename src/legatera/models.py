from datetime import datetime
import uuid
import json
import os
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager

class StorageModel:
    """Base class for storage operations (DynamoDB or local file system)"""
    
    @classmethod
    def _get_storage_dir(cls):
        """Get the storage directory for local files"""
        storage_dir = os.path.join(current_app.root_path, 'storage')
        os.makedirs(storage_dir, exist_ok=True)
        return storage_dir

    @classmethod
    def _get_storage_file(cls, type_name):
        """Get the storage file path for a specific type"""
        return os.path.join(cls._get_storage_dir(), f"{type_name}.json")

    @classmethod
    def _load_data(cls, type_name):
        """Load data from local storage"""
        file_path = cls._get_storage_file(type_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return []

    @classmethod
    def _save_data(cls, type_name, data):
        """Save data to local storage"""
        file_path = cls._get_storage_file(type_name)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def create_id():
        """Create a unique ID"""
        return str(uuid.uuid4())

class User(UserMixin, StorageModel):
    def __init__(self, email, password=None, first_name=None, last_name=None, is_trustee=False):
        self.id = self.create_id()
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
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
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
            table.put_item(Item=item)
        else:
            users = self._load_data('users')
            user_data = {
                'id': self.id,
                'email': self.email,
                'password_hash': self.password_hash,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'is_trustee': self.is_trustee,
                'created_at': self.created_at
            }
            users.append(user_data)
            self._save_data('users', users)

    @classmethod
    def get_by_id(cls, user_id):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
            response = table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'PROFILE#{user_id}'
                }
            )
            if 'Item' not in response:
                return None
            return cls.from_dynamo_item(response['Item'])
        else:
            users = cls._load_data('users')
            user_data = next((u for u in users if u['id'] == user_id), None)
            return cls.from_dict(user_data) if user_data else None

    @classmethod
    def get_by_email(cls, email):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
            response = table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            if not response['Items']:
                return None
            return cls.from_dynamo_item(response['Items'][0])
        else:
            users = cls._load_data('users')
            user_data = next((u for u in users if u['email'] == email), None)
            return cls.from_dict(user_data) if user_data else None

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        user = User(
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            is_trustee=data.get('is_trustee', False)
        )
        user.id = data['id']
        user.password_hash = data['password_hash']
        user.created_at = data['created_at']
        return user

    @staticmethod
    def from_dynamo_item(item):
        return User.from_dict(item)

class Trustee(StorageModel):
    def __init__(self, user_id, trustee_user_id):
        self.id = self.create_id()
        self.user_id = user_id
        self.trustee_user_id = trustee_user_id
        self.notification_triggered = False
        self.triggered_at = None

    def save(self):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
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
            table.put_item(Item=item)
        else:
            trustees = self._load_data('trustees')
            trustee_data = {
                'id': self.id,
                'user_id': self.user_id,
                'trustee_user_id': self.trustee_user_id,
                'notification_triggered': self.notification_triggered,
                'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None
            }
            trustees.append(trustee_data)
            self._save_data('trustees', trustees)

    @classmethod
    def get_by_user_id(cls, user_id):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk': 'TRUSTEE#'
                }
            )
            return [cls.from_dynamo_item(item) for item in response['Items']]
        else:
            trustees = cls._load_data('trustees')
            return [cls.from_dict(t) for t in trustees if t['user_id'] == user_id]

    @classmethod
    def get_by_trustee_id(cls, trustee_id):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
            response = table.scan(
                FilterExpression='trustee_user_id = :trustee_id',
                ExpressionAttributeValues={':trustee_id': trustee_id}
            )
            return [cls.from_dynamo_item(item) for item in response['Items']]
        else:
            trustees = cls._load_data('trustees')
            return [cls.from_dict(t) for t in trustees if t['trustee_user_id'] == trustee_id]

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        trustee = Trustee(
            user_id=data['user_id'],
            trustee_user_id=data['trustee_user_id']
        )
        trustee.id = data['id']
        trustee.notification_triggered = data['notification_triggered']
        trustee.triggered_at = datetime.fromisoformat(data['triggered_at']) if data['triggered_at'] else None
        return trustee

    @staticmethod
    def from_dynamo_item(item):
        return Trustee.from_dict(item)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

class Message(StorageModel):
    def __init__(self, user_id, recipient_id, content, media_url=None, delay_days=0):
        self.id = self.create_id()
        self.user_id = user_id
        self.recipient_id = recipient_id
        self.content = content
        self.media_url = media_url
        self.delay_days = delay_days
        self.created_at = datetime.utcnow().isoformat()
        self.sent_at = None

    def save(self):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
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
            table.put_item(Item=item)
        else:
            messages = self._load_data('messages')
            message_data = {
                'id': self.id,
                'user_id': self.user_id,
                'recipient_id': self.recipient_id,
                'content': self.content,
                'media_url': self.media_url,
                'delay_days': self.delay_days,
                'created_at': self.created_at,
                'sent_at': self.sent_at
            }
            messages.append(message_data)
            self._save_data('messages', messages)

    @classmethod
    def get_by_user_id(cls, user_id):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk': 'MESSAGE#'
                }
            )
            return [cls.from_dynamo_item(item) for item in response['Items']]
        else:
            messages = cls._load_data('messages')
            return [cls.from_dict(m) for m in messages if m['user_id'] == user_id]

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        message = Message(
            user_id=data['user_id'],
            recipient_id=data['recipient_id'],
            content=data['content'],
            media_url=data.get('media_url'),
            delay_days=data['delay_days']
        )
        message.id = data['id']
        message.created_at = data['created_at']
        message.sent_at = data.get('sent_at')
        return message

    @staticmethod
    def from_dynamo_item(item):
        return Message.from_dict(item)

class Asset(StorageModel):
    def __init__(self, user_id, name, description=None, asset_type=None, value=None, location=None):
        self.id = self.create_id()
        self.user_id = user_id
        self.name = name
        self.description = description
        self.asset_type = asset_type
        self.value = value
        self.location = location

    def save(self):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
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
            table.put_item(Item=item)
        else:
            assets = self._load_data('assets')
            asset_data = {
                'id': self.id,
                'user_id': self.user_id,
                'name': self.name,
                'description': self.description,
                'asset_type': self.asset_type,
                'value': self.value,
                'location': self.location
            }
            assets.append(asset_data)
            self._save_data('assets', assets)

    @classmethod
    def get_by_user_id(cls, user_id):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk': 'ASSET#'
                }
            )
            return [cls.from_dynamo_item(item) for item in response['Items']]
        else:
            assets = cls._load_data('assets')
            return [cls.from_dict(a) for a in assets if a['user_id'] == user_id]

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        asset = Asset(
            user_id=data['user_id'],
            name=data['name'],
            description=data.get('description'),
            asset_type=data.get('asset_type'),
            value=data.get('value'),
            location=data.get('location')
        )
        asset.id = data['id']
        return asset

    @staticmethod
    def from_dynamo_item(item):
        return Asset.from_dict(item)

class LastWishes(StorageModel):
    def __init__(self, user_id, funeral_preferences=None, special_requests=None, personal_message=None):
        self.id = self.create_id()
        self.user_id = user_id
        self.funeral_preferences = funeral_preferences
        self.special_requests = special_requests
        self.personal_message = personal_message
        self.updated_at = datetime.utcnow().isoformat()

    def save(self):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
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
            table.put_item(Item=item)
        else:
            wishes = self._load_data('last_wishes')
            wish_data = {
                'id': self.id,
                'user_id': self.user_id,
                'funeral_preferences': self.funeral_preferences,
                'special_requests': self.special_requests,
                'personal_message': self.personal_message,
                'updated_at': self.updated_at
            }
            # Remove any existing wishes for this user
            wishes = [w for w in wishes if w['user_id'] != self.user_id]
            wishes.append(wish_data)
            self._save_data('last_wishes', wishes)

    @classmethod
    def get_by_user_id(cls, user_id):
        if current_app.dynamodb:
            table = current_app.dynamodb.Table(current_app.config['DYNAMODB_TABLE'])
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk': 'WISHES#'
                }
            )
            items = response['Items']
            return cls.from_dynamo_item(items[0]) if items else None
        else:
            wishes = cls._load_data('last_wishes')
            wish_data = next((w for w in wishes if w['user_id'] == user_id), None)
            return cls.from_dict(wish_data) if wish_data else None

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        wishes = LastWishes(
            user_id=data['user_id'],
            funeral_preferences=data.get('funeral_preferences'),
            special_requests=data.get('special_requests'),
            personal_message=data.get('personal_message')
        )
        wishes.id = data['id']
        wishes.updated_at = data['updated_at']
        return wishes

    @staticmethod
    def from_dynamo_item(item):
        return LastWishes.from_dict(item)
