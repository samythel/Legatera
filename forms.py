from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField, DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import boto3
from .config import Config

def validate_file_extension(form, field):
    if field.data:
        filename = field.data.filename
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
        if '.' not in filename or \
           filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            raise ValidationError('Invalid file extension. Allowed extensions are: png, jpg, jpeg, gif, pdf, doc, docx')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    submit = SubmitField('Sign Up')

    def validate_email(self, field):
        # Check if email exists in Cognito user pool
        client = Config.get_cognito_client()
        try:
            response = client.list_users(
                UserPoolId=Config.COGNITO_USER_POOL_ID,
                Filter=f'email = "{field.data}"'
            )
            if response.get('Users'):
                raise ValidationError('Email already registered.')
        except Exception as e:
            # Log the error but don't expose AWS-specific errors to user
            print(f"Error checking Cognito user pool: {str(e)}")

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class TrusteeForm(FlaskForm):
    email = StringField('Trustee Email', validators=[
        DataRequired(),
        Email()
    ])
    submit = SubmitField('Add Trustee')

class RecipientForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(max=128)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    phone = StringField('Phone', validators=[Length(max=20)])
    relationship = StringField('Relationship', validators=[Length(max=64)])
    submit = SubmitField('Add Recipient')

class MessageForm(FlaskForm):
    recipient = SelectField('Recipient', coerce=str)
    content = TextAreaField('Message', validators=[DataRequired()])
    media = FileField('Add Media', validators=[validate_file_extension])
    delay_days = SelectField('Delay Days',
                           choices=[
                               ('0', 'No delay'),
                               ('7', '1 week'),
                               ('30', '1 month'),
                               ('90', '3 months'),
                               ('180', '6 months'),
                               ('365', '1 year')
                           ],
                           coerce=int)
    submit = SubmitField('Save Message')

class LastWishesForm(FlaskForm):
    funeral_preferences = TextAreaField('Funeral Preferences')
    special_requests = TextAreaField('Special Requests')
    personal_message = TextAreaField('Personal Message')
    submit = SubmitField('Save Wishes')

class AssetForm(FlaskForm):
    name = StringField('Asset Name', validators=[
        DataRequired(),
        Length(max=128)
    ])
    description = TextAreaField('Description')
    type = SelectField('Type', choices=[
        ('real_estate', 'Real Estate'),
        ('financial', 'Financial'),
        ('personal', 'Personal'),
        ('digital', 'Digital Asset'),
        ('other', 'Other')
    ])
    value = DecimalField('Estimated Value', places=2, default=0.0)
    location = StringField('Location', validators=[Length(max=256)])
    documents = FileField('Related Documents', validators=[validate_file_extension])
    submit = SubmitField('Add Asset')

class DocumentForm(FlaskForm):
    name = StringField('Document Name', validators=[
        DataRequired(),
        Length(max=128)
    ])
    file = FileField('File', validators=[
        DataRequired(),
        validate_file_extension
    ])
    submit = SubmitField('Upload Document')
