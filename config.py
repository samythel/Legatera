import os
import boto3
from botocore.exceptions import ClientError

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # AWS Configuration
    AWS_REGION = 'us-east-1'
    
    # Cognito Configuration
    COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
    COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID')
    
    # DynamoDB Configuration
    DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'legatera-table')
    
    # S3 Configuration
    S3_BUCKET = os.environ.get('S3_BUCKET', 'legatera-files')
    
    # Flask Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    @staticmethod
    def get_secret(secret_name):
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=Config.AWS_REGION
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            raise e
        else:
            if 'SecretString' in get_secret_value_response:
                return get_secret_value_response['SecretString']
            else:
                return None

    @staticmethod
    def get_cognito_client():
        return boto3.client('cognito-idp', region_name=Config.AWS_REGION)
    
    @staticmethod
    def get_dynamodb_resource():
        return boto3.resource('dynamodb', region_name=Config.AWS_REGION)
    
    @staticmethod
    def get_s3_client():
        return boto3.client('s3', region_name=Config.AWS_REGION)
