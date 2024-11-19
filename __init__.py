from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from .config import Config

# Initialize AWS clients
cognito_client = Config.get_cognito_client()
dynamodb = Config.get_dynamodb_resource()
s3_client = Config.get_s3_client()

login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Flask extensions
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Create DynamoDB table if it doesn't exist
    table = dynamodb.Table(Config.DYNAMODB_TABLE)
    
    # Create S3 bucket if it doesn't exist
    try:
        s3_client.head_bucket(Bucket=Config.S3_BUCKET)
    except:
        s3_client.create_bucket(Bucket=Config.S3_BUCKET)

    # Register blueprints
    from .routes import main, auth, dashboard
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)

    return app
