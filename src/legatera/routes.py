from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from .models import User, Trustee, Message, Asset, LastWishes
from .forms import (RegistrationForm, LoginForm, TrusteeForm, RecipientForm, 
                   MessageForm, LastWishesForm, AssetForm, DocumentForm)
import os

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
dashboard = Blueprint('dashboard', __name__)

def handle_file_upload(file, folder='general'):
    """Handle file upload for both S3 and local storage"""
    if not file:
        return None
        
    filename = secure_filename(file.filename)
    
    if current_app.s3_client:
        try:
            unique_filename = f"{folder}/{current_user.id}/{filename}"
            current_app.s3_client.upload_fileobj(
                file,
                current_app.config['S3_BUCKET'],
                unique_filename,
                ExtraArgs={'ACL': 'private'}
            )
            return unique_filename
        except Exception as e:
            current_app.logger.error(f"Error uploading to S3: {str(e)}")
            return None
    else:
        # Local file storage fallback
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', folder)
        os.makedirs(upload_folder, exist_ok=True)
        unique_filename = f"{current_user.id}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return f"uploads/{folder}/{unique_filename}"

@main.route('/')
def home():
    return render_template('home.html', now=datetime.utcnow())

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.user_dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            user.set_password(form.password.data)
            
            # Try Cognito registration if available
            if current_app.cognito_client:
                try:
                    current_app.cognito_client.sign_up(
                        ClientId=current_app.config['COGNITO_APP_CLIENT_ID'],
                        Username=form.email.data,
                        Password=form.password.data,
                        UserAttributes=[
                            {'Name': 'email', 'Value': form.email.data},
                            {'Name': 'given_name', 'Value': form.first_name.data},
                            {'Name': 'family_name', 'Value': form.last_name.data},
                        ]
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] == 'UsernameExistsException':
                        flash('Email already registered.', 'danger')
                        return render_template('auth/register.html', form=form, now=datetime.utcnow())
            
            # Save user locally or in DynamoDB
            user.save()
            
            flash('Registration successful! Please check your email for verification.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash('An error occurred during registration. Please try again.', 'danger')
            current_app.logger.error(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html', form=form, now=datetime.utcnow())

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.user_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Try Cognito authentication if available
            if current_app.cognito_client:
                try:
                    auth_response = current_app.cognito_client.initiate_auth(
                        ClientId=current_app.config['COGNITO_APP_CLIENT_ID'],
                        AuthFlow='USER_PASSWORD_AUTH',
                        AuthParameters={
                            'USERNAME': form.email.data,
                            'PASSWORD': form.password.data
                        }
                    )
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'NotAuthorizedException':
                        flash('Invalid email or password.', 'danger')
                        return render_template('auth/login.html', form=form, now=datetime.utcnow())
                    elif error_code == 'UserNotConfirmedException':
                        flash('Please verify your email address.', 'warning')
                        return render_template('auth/login.html', form=form, now=datetime.utcnow())
            
            # Get user from storage
            user = User.get_by_email(form.email.data)
            if user and (not current_app.cognito_client or user.check_password(form.password.data)):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.user_dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
            
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'danger')
            current_app.logger.error(f"Login error: {str(e)}")
    
    return render_template('auth/login.html', form=form, now=datetime.utcnow())

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@dashboard.route('/user-dashboard')
@login_required
def user_dashboard():
    try:
        # Get user data from storage
        trustees = Trustee.get_by_user_id(current_user.id)
        messages = Message.get_by_user_id(current_user.id)
        assets = Asset.get_by_user_id(current_user.id)
        last_wishes = LastWishes.get_by_user_id(current_user.id)
        
        return render_template('dashboard/user.html',
                             trustees=trustees,
                             messages=messages,
                             assets=assets,
                             last_wishes=last_wishes,
                             now=datetime.utcnow())
    except Exception as e:
        flash('Error loading dashboard data.', 'danger')
        current_app.logger.error(f"Dashboard error: {str(e)}")
        return redirect(url_for('main.home'))

@dashboard.route('/add-message', methods=['GET', 'POST'])
@login_required
def add_message():
    form = MessageForm()
    if form.validate_on_submit():
        media_url = handle_file_upload(form.media.data, 'messages')
        
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
    
    return render_template('dashboard/add_message.html', form=form, now=datetime.utcnow())

@dashboard.route('/add-asset', methods=['GET', 'POST'])
@login_required
def add_asset():
    form = AssetForm()
    if form.validate_on_submit():
        document_url = handle_file_upload(form.documents.data, 'assets')
        
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
    
    return render_template('dashboard/add_asset.html', form=form, now=datetime.utcnow())

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
    
    return render_template('dashboard/last_wishes.html', form=form, now=datetime.utcnow())

@auth.route('/trustee-login', methods=['GET', 'POST'])
def trustee_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.trustee_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user and user.is_trustee and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard.trustee_dashboard'))
        flash('Invalid trustee credentials.', 'danger')
    
    return render_template('auth/trustee_login.html', form=form, now=datetime.utcnow())

@dashboard.route('/trustee-dashboard')
@login_required
def trustee_dashboard():
    if not current_user.is_trustee:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    
    trusted_users = Trustee.get_by_trustee_id(current_user.id)
    return render_template('dashboard/trustee.html', trusted_users=trusted_users, now=datetime.utcnow())
