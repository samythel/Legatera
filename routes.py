import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from . import cognito_client, s3_client
from .models import User, Trustee, Message, Asset, LastWishes
from .forms import (RegistrationForm, LoginForm, TrusteeForm, RecipientForm, 
                   MessageForm, LastWishesForm, AssetForm, DocumentForm)
from .config import Config

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
dashboard = Blueprint('dashboard', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file_to_s3(file, folder='general'):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{folder}/{current_user.id}/{filename}"
        try:
            s3_client.upload_fileobj(
                file,
                Config.S3_BUCKET,
                unique_filename,
                ExtraArgs={'ACL': 'private'}
            )
            return unique_filename
        except Exception as e:
            current_app.logger.error(f"Error uploading to S3: {str(e)}")
            return None
    return None

@main.route('/')
def home():
    return render_template('home.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.user_dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user in Cognito
            cognito_client.sign_up(
                ClientId=Config.COGNITO_APP_CLIENT_ID,
                Username=form.email.data,
                Password=form.password.data,
                UserAttributes=[
                    {'Name': 'email', 'Value': form.email.data},
                    {'Name': 'given_name', 'Value': form.first_name.data},
                    {'Name': 'family_name', 'Value': form.last_name.data},
                ]
            )
            
            # Create user in DynamoDB
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            user.set_password(form.password.data)
            user.save()
            
            flash('Registration successful! Please check your email for verification.', 'success')
            return redirect(url_for('auth.login'))
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                flash('Email already registered.', 'danger')
            else:
                flash('An error occurred during registration. Please try again.', 'danger')
                current_app.logger.error(f"Cognito error: {str(e)}")
    
    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.user_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Authenticate with Cognito
            auth_response = cognito_client.initiate_auth(
                ClientId=Config.COGNITO_APP_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': form.email.data,
                    'PASSWORD': form.password.data
                }
            )
            
            # Get user from DynamoDB
            user = User.get_by_email(form.email.data)
            if user:
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.user_dashboard'))
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                flash('Invalid email or password.', 'danger')
            elif error_code == 'UserNotConfirmedException':
                flash('Please verify your email address.', 'warning')
            else:
                flash('An error occurred during login. Please try again.', 'danger')
                current_app.logger.error(f"Cognito error: {str(e)}")
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@dashboard.route('/user-dashboard')
@login_required
def user_dashboard():
    # Query DynamoDB for user's data
    trustees = Trustee.table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'USER#{current_user.id}',
            ':sk': 'TRUSTEE#'
        }
    )['Items']
    
    messages = Message.table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'USER#{current_user.id}',
            ':sk': 'MESSAGE#'
        }
    )['Items']
    
    assets = Asset.table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'USER#{current_user.id}',
            ':sk': 'ASSET#'
        }
    )['Items']
    
    last_wishes = LastWishes.table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'USER#{current_user.id}',
            ':sk': 'WISHES#'
        }
    )['Items']
    
    return render_template('dashboard/user.html',
                         trustees=trustees,
                         messages=messages,
                         assets=assets,
                         last_wishes=last_wishes[0] if last_wishes else None)

@dashboard.route('/add-message', methods=['GET', 'POST'])
@login_required
def add_message():
    form = MessageForm()
    if form.validate_on_submit():
        media_url = None
        if form.media.data:
            media_url = upload_file_to_s3(form.media.data, 'messages')
            if not media_url:
                flash('Error uploading media file.', 'danger')
                return redirect(url_for('dashboard.add_message'))
        
        message = Message(
            user_id=current_user.id,
            recipient_id=form.recipient.data,
            content=form.content.data,
            media_url=media_url,
            delay_days=form.delay_days.data
        )
        message.save()
        
        flash('Message saved successfully.', 'success')
        return redirect(url_for('dashboard.user_dashboard'))
    
    return render_template('dashboard/add_message.html', form=form)

@dashboard.route('/add-asset', methods=['GET', 'POST'])
@login_required
def add_asset():
    form = AssetForm()
    if form.validate_on_submit():
        document_url = None
        if form.documents.data:
            document_url = upload_file_to_s3(form.documents.data, 'assets')
            if not document_url:
                flash('Error uploading document.', 'danger')
                return redirect(url_for('dashboard.add_asset'))
        
        asset = Asset(
            user_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            asset_type=form.type.data,
            value=float(form.value.data) if form.value.data else None,
            location=form.location.data
        )
        asset.save()
        
        flash('Asset added successfully.', 'success')
        return redirect(url_for('dashboard.user_dashboard'))
    
    return render_template('dashboard/add_asset.html', form=form)

@dashboard.route('/last-wishes', methods=['GET', 'POST'])
@login_required
def last_wishes():
    form = LastWishesForm()
    if form.validate_on_submit():
        wishes = LastWishes(
            user_id=current_user.id,
            funeral_preferences=form.funeral_preferences.data,
            special_requests=form.special_requests.data,
            personal_message=form.personal_message.data
        )
        wishes.save()
        
        flash('Last wishes updated successfully.', 'success')
        return redirect(url_for('dashboard.user_dashboard'))
    
    return render_template('dashboard/last_wishes.html', form=form)
