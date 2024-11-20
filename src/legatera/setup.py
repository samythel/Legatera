from setuptools import setup, find_packages

setup(
    name="legatera",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Login',
        'Flask-Mail',
        'Flask-WTF',
        'boto3',
        'python-dotenv',
        'email-validator',
        'python-jose',
        'requests',
        'gunicorn',
        'cryptography',
        'PyJWT'
    ],
)
