# AWS Cognito Authentication Setup Guide

## 1. AWS Configuration Prerequisites

### 1.1 Create AWS IAM User
1. Go to AWS Console → IAM
2. Create a new IAM user with programmatic access
3. Attach the following policies:
   - AmazonCognitoPowerUser
   - AmazonCognitoIdpFullAccess

### 1.2 Configure AWS Credentials
```bash
aws configure
```
Enter the following information:
- AWS Access Key ID: [Your Access Key]
- AWS Secret Access Key: [Your Secret Key]
- Default region name: us-east-1
- Default output format: json

## 2. Create Cognito Resources

### 2.1 Create User Pool
```bash
aws cognito-idp create-user-pool \
--region us-east-1 \
--pool-name Legatera-UserPool \
--policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":true}}' \
--username-attributes email \
--auto-verified-attributes email \
--schema '[{"Name":"email","Required":true,"Mutable":true},{"Name":"name","Required":true,"Mutable":true}]' \
--mfa-configuration OFF
```

### 2.2 Create App Client
After creating the user pool, note the User Pool ID and run:
```bash
aws cognito-idp create-user-pool-client \
--user-pool-id [YOUR_USER_POOL_ID] \
--client-name legatera-app-client \
--no-generate-secret \
--explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
--supported-identity-providers COGNITO
```

### 2.3 Update Environment Variables
Update the following variables in your .env file:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_APP_CLIENT_ID=your-app-client-id
```

## 3. Code Integration

### 3.1 Create Cognito Utility Class
Create a new file `auth/cognito.py` with the following content:
```python
import boto3
import botocore
from flask import current_app
import os

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
```

### 3.2 Update Routes
Update your authentication routes to use the Cognito client:
```python
from auth.cognito import CognitoClient

cognito = CognitoClient()

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    
    success, response = cognito.sign_up(email, password, name)
    if success:
        return jsonify({'message': 'Registration successful'}), 200
    return jsonify({'error': response}), 400

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    success, response = cognito.initiate_auth(email, password)
    if success:
        access_token = response['AuthenticationResult']['AccessToken']
        # Store token in session or return to client
        return jsonify({'token': access_token}), 200
    return jsonify({'error': response}), 401
```

### 3.3 Protect Routes
Create a decorator to protect routes:
```python
from functools import wraps
from flask import session, redirect, url_for

def cognito_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('access_token')
        if not token:
            return redirect(url_for('login'))
        
        success, user = cognito.verify_token(token)
        if not success:
            return redirect(url_for('login'))
            
        return f(*args, **kwargs)
    return decorated_function

# Use the decorator
@app.route('/protected')
@cognito_auth_required
def protected_route():
    return 'Protected content'
```

## 4. Testing

### 4.1 Test Registration
```bash
curl -X POST http://localhost:5000/register \
-H "Content-Type: application/json" \
-d '{"email":"test@example.com","password":"Test123!","name":"Test User"}'
```

### 4.2 Test Login
```bash
curl -X POST http://localhost:5000/login \
-H "Content-Type: application/json" \
-d '{"email":"test@example.com","password":"Test123!"}'
```

## 5. Security Considerations

1. Always use HTTPS in production
2. Implement proper token storage and management
3. Set up proper CORS configuration
4. Implement rate limiting
5. Set up proper error handling
6. Configure password policies
7. Enable MFA if required
8. Set up proper logging and monitoring

## 6. Next Steps

1. Implement password reset flow
2. Add social identity providers if needed
3. Set up user groups and roles
4. Implement token refresh mechanism
5. Add user profile management
6. Set up proper error pages
7. Implement remember me functionality
8. Add logout functionality
