import boto3
import hmac
import hashlib
import base64
import re
from datetime import datetime
from botocore.exceptions import ClientError
from ..config import AWSConfig
from .utils import validate_password, rate_limit
from .exceptions import ValidationError, AuthenticationError, RegistrationError

class CognitoClient:
    def __init__(self):
        """Initialize the Cognito client with AWS configuration."""
        self.client = boto3.client('cognito-idp', region_name=AWSConfig.AWS_REGION)
        self.user_pool_id = AWSConfig.COGNITO_USER_POOL_ID
        self.client_id = AWSConfig.COGNITO_APP_CLIENT_ID
        self.client_secret = AWSConfig.COGNITO_APP_CLIENT_SECRET

    def get_secret_hash(self, username):
        """
        Calculate the secret hash for Cognito API calls.
        
        Args:
            username (str): The username (email) of the user
            
        Returns:
            str: The calculated secret hash
        """
        msg = username + self.client_id
        dig = hmac.new(
            str(self.client_secret).encode('utf-8'),
            msg=str(msg).encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()

    def validate_phone_number(self, phone):
        """
        Validate US phone number format.
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            str: Validated phone number
            
        Raises:
            ValueError: If phone number is invalid
        """
        pattern = r'^\+1[2-9]\d{9}$'
        if not re.match(pattern, phone):
            raise ValueError("Phone number must be in format +1XXXXXXXXXX and be a valid US number")
        return phone

    def validate_date_of_birth(self, dob):
        """
        Validate date of birth and check if user is at least 18.
        
        Args:
            dob (str): Date of birth in YYYY-MM-DD format
            
        Returns:
            str: Validated date of birth
            
        Raises:
            ValueError: If date is invalid or user is under 18
        """
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            if age < 18:
                raise ValueError("Must be at least 18 years old")
                
            return dob
        except ValueError as e:
            if "Must be at least 18 years old" in str(e):
                raise
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

    def validate_email(self, email):
        """
        Validate email format.
        
        Args:
            email (str): Email to validate
            
        Returns:
            str: Validated email
            
        Raises:
            ValueError: If email format is invalid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        return email

    def validate_name(self, name, field):
        """
        Validate name fields.
        
        Args:
            name (str): Name to validate
            field (str): Field name for error messages
            
        Returns:
            str: Validated name
            
        Raises:
            ValueError: If name format is invalid
        """
        if not name or len(name) < 2 or len(name) > 50:
            raise ValueError(f"{field} must be between 2 and 50 characters")
        if not re.match(r'^[a-zA-Z\s\-\']+$', name):
            raise ValueError(f"{field} can only contain letters, spaces, hyphens, and apostrophes")
        return name

    @rate_limit(max_requests=5, window_seconds=60)
    def sign_up(self, email, password, first_name, last_name, phone_number, date_of_birth):
        """
        Register a new user with AWS Cognito.
        
        Args:
            email (str): User's email address
            password (str): User's password
            first_name (str): User's first name
            last_name (str): User's last name
            phone_number (str): User's phone number
            date_of_birth (str): User's date of birth (YYYY-MM-DD)
            
        Returns:
            dict: Cognito sign-up response
            
        Raises:
            ValidationError: If any input validation fails
            RegistrationError: If registration fails
            ClientError: If AWS Cognito API call fails
        """
        try:
            # Validate all fields
            email = self.validate_email(email)
            first_name = self.validate_name(first_name, "First name")
            last_name = self.validate_name(last_name, "Last name")
            phone_number = self.validate_phone_number(phone_number)
            date_of_birth = self.validate_date_of_birth(date_of_birth)
            
            # Validate password
            is_valid, message = validate_password(password)
            if not is_valid:
                raise ValidationError(message)

            # Register user in Cognito
            response = self.client.sign_up(
                ClientId=self.client_id,
                SecretHash=self.get_secret_hash(email),
                Username=email,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'given_name', 'Value': first_name},
                    {'Name': 'family_name', 'Value': last_name},
                    {'Name': 'phone_number', 'Value': phone_number},
                    {'Name': 'birthdate', 'Value': date_of_birth},
                    {'Name': 'custom:user_type', 'Value': 'user'}
                ]
            )
            return response
            
        except ValueError as e:
            raise ValidationError(str(e))
        except ClientError as e:
            if e.response['Error']['Code'] == 'UsernameExistsException':
                raise RegistrationError("Email already registered")
            raise RegistrationError(f"Registration failed: {str(e)}")

    @rate_limit(max_requests=5, window_seconds=60)
    def confirm_sign_up(self, email, confirmation_code):
        """
        Confirm user registration with verification code.
        
        Args:
            email (str): User's email address
            confirmation_code (str): Verification code sent to user's email
            
        Returns:
            dict: Cognito confirmation response
            
        Raises:
            ValidationError: If email is invalid
            AuthenticationError: If confirmation fails
        """
        try:
            email = self.validate_email(email)
            
            response = self.client.confirm_sign_up(
                ClientId=self.client_id,
                SecretHash=self.get_secret_hash(email),
                Username=email,
                ConfirmationCode=confirmation_code
            )
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'CodeMismatchException':
                raise AuthenticationError("Invalid verification code")
            if e.response['Error']['Code'] == 'ExpiredCodeException':
                raise AuthenticationError("Verification code has expired")
            raise AuthenticationError(f"Confirmation failed: {str(e)}")

    @rate_limit(max_requests=5, window_seconds=60)
    def resend_confirmation_code(self, email):
        """
        Resend confirmation code to user's email.
        
        Args:
            email (str): User's email address
            
        Returns:
            dict: Cognito response
            
        Raises:
            ValidationError: If email is invalid
            AuthenticationError: If resend fails
        """
        try:
            email = self.validate_email(email)
            
            response = self.client.resend_confirmation_code(
                ClientId=self.client_id,
                SecretHash=self.get_secret_hash(email),
                Username=email
            )
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'LimitExceededException':
                raise AuthenticationError("Too many attempts. Please try again later")
            raise AuthenticationError(f"Failed to resend code: {str(e)}")
