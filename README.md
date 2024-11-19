# Legatera - Digital Legacy Management System

Legatera is a secure platform for managing and preserving your digital legacy. It allows users to store important messages, documents, and final wishes that can be accessed by designated trustees when the time comes.

## Features

- **Secure Authentication**: AWS Cognito-powered user authentication system
- **Message Storage**: Store personal messages for loved ones with timed release options
- **Asset Management**: Document and manage digital and physical assets
- **Trustee System**: Designate trusted individuals to manage your digital legacy
- **Last Wishes**: Record and store final arrangements and special requests
- **Secure Storage**: AWS S3-powered secure file storage
- **Database**: AWS DynamoDB for reliable data persistence

## Prerequisites

- Python 3.8 or higher
- AWS Account with appropriate permissions
- AWS CLI configured with credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/legatera.git
cd legatera
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with the following variables:
```
FLASK_APP=legatera
FLASK_ENV=development
SECRET_KEY=your-secret-key

# AWS Configuration
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_APP_CLIENT_ID=your-app-client-id
S3_BUCKET=your-s3-bucket-name
DYNAMODB_TABLE=your-dynamodb-table-name

# Optional Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

5. Initialize the database:
```bash
flask db-init
```

## AWS Setup

1. Create a Cognito User Pool:
   - Go to AWS Console > Cognito
   - Create a new User Pool
   - Configure sign-in options (email, password requirements)
   - Create an app client
   - Note down the User Pool ID and App Client ID

2. Create an S3 Bucket:
   - Go to AWS Console > S3
   - Create a new bucket
   - Configure appropriate CORS settings
   - Set up bucket policies for secure access

3. Create a DynamoDB Table:
   - Go to AWS Console > DynamoDB
   - Create a new table
   - Set up the partition key (PK) and sort key (SK)
   - Configure appropriate capacity settings

4. Set up IAM Roles:
   - Create appropriate IAM roles with necessary permissions
   - Attach policies for Cognito, S3, and DynamoDB access

## Running the Application

1. Start the development server:
```bash
flask run
```

2. Access the application at `http://localhost:5000`

## Project Structure

```
legatera/
├── __init__.py           # Application factory
├── config.py            # Configuration settings
├── models.py            # Data models
├── routes.py            # Route handlers
├── forms.py             # Form definitions
├── static/              # Static files
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
└── templates/           # HTML templates
    ├── base.html
    ├── home.html
    ├── auth/
    │   ├── login.html
    │   ├── register.html
    │   └── trustee_login.html
    └── dashboard/
        ├── user.html
        └── trustee.html
```

## Security Considerations

- All sensitive data is encrypted at rest using AWS KMS
- Files are stored securely in S3 with appropriate access controls
- User authentication is handled by AWS Cognito
- Passwords are never stored directly in the database
- HTTPS is required for all communications
- Session management is secure by default
- CSRF protection is enabled for all forms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact support@legatera.com.

## Acknowledgments

- Flask framework and its extensions
- AWS Services (Cognito, S3, DynamoDB)
- Tailwind CSS for styling
- All contributors and users of the platform
