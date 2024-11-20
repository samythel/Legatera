from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from .models import User
from .forms import RegistrationForm, LoginForm
from ..auth.cognito import CognitoClient, cognito_auth_required

auth = Blueprint('auth', __name__)
cognito = CognitoClient()

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.user_dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Register with Cognito
            success, response = cognito.sign_up(
                email=form.email.data,
                password=form.password.data,
                name=f"{form.first_name.data} {form.last_name.data}"
            )
            
            if success:
                # Create local user
                user = User(
                    email=form.email.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data
                )
                user.set_password(form.password.data)
                user.save()
                
                flash('Registration successful! Please check your email for verification.', 'success')
                return redirect(url_for('auth.login'))
            else:
                if "UsernameExistsException" in str(response):
                    flash('Email already registered.', 'danger')
                else:
                    flash(f'Registration error: {str(response)}', 'danger')
                    current_app.logger.error(f"Cognito registration error: {str(response)}")
            
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
            # Authenticate with Cognito
            success, response = cognito.initiate_auth(
                email=form.email.data,
                password=form.password.data
            )
            
            if success:
                # Get access token from response
                access_token = response['AuthenticationResult']['AccessToken']
                
                # Store token in session
                session['access_token'] = access_token
                
                # Get user from local storage
                user = User.get_by_email(form.email.data)
                if user:
                    login_user(user)
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('dashboard.user_dashboard'))
                else:
                    flash('User not found in local database.', 'danger')
            else:
                if "NotAuthorizedException" in str(response):
                    flash('Invalid email or password.', 'danger')
                elif "UserNotConfirmedException" in str(response):
                    flash('Please verify your email address.', 'warning')
                else:
                    flash(f'Login error: {str(response)}', 'danger')
                    current_app.logger.error(f"Cognito login error: {str(response)}")
            
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'danger')
            current_app.logger.error(f"Login error: {str(e)}")
    
    return render_template('auth/login.html', form=form, now=datetime.utcnow())

@auth.route('/logout')
@login_required
def logout():
    try:
        # Sign out from Cognito
        access_token = session.get('access_token')
        if access_token:
            success, response = cognito.sign_out(access_token)
            if not success:
                current_app.logger.error(f"Cognito sign out error: {str(response)}")
        
        # Clear session and logout user
        session.pop('access_token', None)
        logout_user()
        flash('You have been logged out.', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash('An error occurred during logout.', 'danger')
    
    return redirect(url_for('main.home'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            success, response = cognito.forgot_password(email)
            if success:
                flash('Password reset instructions have been sent to your email.', 'success')
                return redirect(url_for('auth.reset_password'))
            else:
                flash(f'Error: {str(response)}', 'danger')
    
    return render_template('auth/forgot_password.html', now=datetime.utcnow())

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        
        if email and code and new_password:
            success, response = cognito.confirm_forgot_password(
                email=email,
                confirmation_code=code,
                new_password=new_password
            )
            
            if success:
                flash('Password has been reset successfully. Please login with your new password.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash(f'Error: {str(response)}', 'danger')
    
    return render_template('auth/reset_password.html', now=datetime.utcnow())
