import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from ..aws.cognito import CognitoClient
from ..aws.utils import validate_password
from ..aws.exceptions import ValidationError
from botocore.exceptions import ClientError

class TestCognitoClient(unittest.TestCase):
    def setUp(self):
        self.cognito = CognitoClient()
        
    def test_validate_phone_number(self):
        # Valid phone numbers
        self.assertEqual(self.cognito.validate_phone_number('+12125551234'), '+12125551234')
        self.assertEqual(self.cognito.validate_phone_number('+19995551234'), '+19995551234')
        
        # Invalid phone numbers
        with self.assertRaises(ValueError):
            self.cognito.validate_phone_number('+1212555123')  # Too short
        with self.assertRaises(ValueError):
            self.cognito.validate_phone_number('2125551234')   # Missing +1
        with self.assertRaises(ValueError):
            self.cognito.validate_phone_number('+11234567890') # Starts with 1
            
    def test_validate_email(self):
        # Valid emails
        self.assertEqual(self.cognito.validate_email('test@example.com'), 'test@example.com')
        self.assertEqual(self.cognito.validate_email('user.name+tag@example.co.uk'), 'user.name+tag@example.co.uk')
        
        # Invalid emails
        with self.assertRaises(ValueError):
            self.cognito.validate_email('invalid.email')
        with self.assertRaises(ValueError):
            self.cognito.validate_email('@example.com')
            
    def test_validate_name(self):
        # Valid names
        self.assertEqual(self.cognito.validate_name('John', 'First name'), 'John')
        self.assertEqual(self.cognito.validate_name("O'Connor", 'Last name'), "O'Connor")
        self.assertEqual(self.cognito.validate_name('Mary-Jane', 'First name'), 'Mary-Jane')
        
        # Invalid names
        with self.assertRaises(ValueError):
            self.cognito.validate_name('J', 'First name')  # Too short
        with self.assertRaises(ValueError):
            self.cognito.validate_name('John123', 'First name')  # Contains numbers
            
    def test_validate_date_of_birth(self):
        # Valid dates (assuming current year is 2023)
        self.assertEqual(self.cognito.validate_date_of_birth('1990-01-01'), '1990-01-01')
        self.assertEqual(self.cognito.validate_date_of_birth('2000-12-31'), '2000-12-31')
        
        # Invalid dates
        with self.assertRaises(ValueError):
            self.cognito.validate_date_of_birth('2020-01-01')  # Under 18
        with self.assertRaises(ValueError):
            self.cognito.validate_date_of_birth('invalid-date')
            
    @patch('boto3.client')
    def test_sign_up_success(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # Mock successful response
        mock_client.sign_up.return_value = {'UserSub': 'test-user-id'}
        
        response = self.cognito.sign_up(
            email='test@example.com',
            password='ValidP@ssw0rd',
            first_name='John',
            last_name='Doe',
            phone_number='+12125551234',
            date_of_birth='1990-01-01'
        )
        
        self.assertEqual(response['UserSub'], 'test-user-id')
        mock_client.sign_up.assert_called_once()
        
    @patch('boto3.client')
    def test_sign_up_failure(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # Mock error response
        error_response = {
            'Error': {
                'Code': 'UsernameExistsException',
                'Message': 'User already exists'
            }
        }
        mock_client.sign_up.side_effect = ClientError(error_response, 'sign_up')
        
        with self.assertRaises(ClientError):
            self.cognito.sign_up(
                email='test@example.com',
                password='ValidP@ssw0rd',
                first_name='John',
                last_name='Doe',
                phone_number='+12125551234',
                date_of_birth='1990-01-01'
            )

class TestPasswordValidation(unittest.TestCase):
    def test_valid_password(self):
        valid_passwords = [
            'ValidP@ssw0rd',
            'Str0ng!Pass',
            'C0mplex#123',
        ]
        
        for password in valid_passwords:
            is_valid, message = validate_password(password)
            self.assertTrue(is_valid, f"Password {password} should be valid")
            
    def test_invalid_password(self):
        invalid_passwords = [
            ('short1', 'at least 8 characters'),
            ('lowercase123!', 'uppercase letter'),
            ('UPPERCASE123!', 'lowercase letter'),
            ('ValidPassword!', 'number'),
            ('ValidPassword1', 'special character'),
        ]
        
        for password, expected_error in invalid_passwords:
            is_valid, message = validate_password(password)
            self.assertFalse(is_valid, f"Password {password} should be invalid")
            self.assertIn(expected_error, message.lower())

if __name__ == '__main__':
    unittest.main()
