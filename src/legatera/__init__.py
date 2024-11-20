from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from .config import Config
import boto3
from botocore.exceptions import ClientError
import os

def init_aws_clients():
    """Initialize AWS clients with error handling"""
    try:
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            cognito_client = boto3.client('cognito-idp', region_name=Config.AWS_REGION)
            dynamodb = boto3.resource('dynamodb', region_name=Config.AWS_REGION)
            s3_client = boto3.client('s3', region_name=Config.AWS_REGION)
            
            # Try to create S3 bucket if it doesn't exist
            try:
                s3_client.head_bucket(Bucket=Config.S3_BUCKET)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    s3_client.create_bucket(Bucket=Config.S3_BUCKET)
            
            return cognito_client, dynamodb, s3_client
        else:
            print("AWS credentials not found. Running in development mode without AWS services.")
            return None, None, None
    except Exception as e:
        print(f"Error initializing AWS services: {str(e)}")
        print("Running in development mode without AWS services.")
        return None, None, None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Flask extensions within app context
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    mail = Mail()
    mail.init_app(app)

    # Store extensions on app for access in views
    app.login_manager = login_manager
    app.mail = mail

    # Initialize AWS services
    app.cognito_client, app.dynamodb, app.s3_client = init_aws_clients()

    # Register blueprints
    from .routes import main, auth, dashboard
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)

    return app
