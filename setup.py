from setuptools import setup, find_packages

setup(
    name="legatera",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        'Flask==2.3.3',
        'Flask-Login==0.6.2',
        'Flask-Mail==0.9.1',
        'Flask-WTF==1.1.1',
        'boto3==1.28.36',
        'botocore==1.31.36',
        'python-dotenv==1.0.0',
        'Werkzeug==2.3.7',
        'WTForms==3.0.1',
        'email-validator==2.0.0.post2',
        'python-jose==3.3.0',
        'requests==2.31.0',
        'gunicorn==21.2.0',
        'cryptography==41.0.3',
        'PyJWT==2.8.0'
    ],
    python_requires='>=3.9',
)
