import boto3
import botocore
from flask import current_app
import os
from functools import wraps
from flask import session, redirect, url_for, jsonify

class CognitoClient:
    def __init__(self):
        self.client = boto3.client('cognito-idp',
            region_name=os.getenv('AWS_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_APP_CLIENT_ID')

    def sign_up(self, email, password, name):
        try:
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'name', 'Value': name}
                ]
            )
            return True, response
        except botocore.exceptions.ClientError as e:
            return False, str(e)

    def initiate_auth(self, email, password):
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            return True, response
        except botocore.exceptions.ClientError as e:
            return False, str(e)

    def verify_token(self, token):
        try:
            response = self.client.get_user(
                AccessToken=token
            )
            return True, response
        except botocore.exceptions.ClientError as e:
            return False, str(e)

    def forgot_password(self, email):
        try:
            response = self.client.forgot_password(
                ClientId=self.client_id,
                Username=email
            )
            return True, response
        except botocore.exceptions.ClientError as e:
            return False, str(e)

    def confirm_forgot_password(self, email, confirmation_code, new_password):
        try:
            response = self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            return True, response
        except botocore.exceptions.ClientError as e:
            return False, str(e)

    def sign_out(self, access_token):
        try:
            response = self.client.global_sign_out(
                AccessToken=access_token
            )
            return True, response
        except botocore.exceptions.ClientError as e:
            return False, str(e)

def cognito_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('access_token')
        if not token:
            return redirect(url_for('auth.login'))
        
        cognito = CognitoClient()
        success, user = cognito.verify_token(token)
        if not success:
            session.pop('access_token', None)
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function
