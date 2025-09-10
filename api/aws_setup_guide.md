# AWS Database Hosting Guide

## 🚀 Hosting Django Database on AWS

### **Option 1: Amazon RDS (Recommended)**

Amazon RDS provides managed database services with automatic backups, scaling, and maintenance.

#### **Step 1: Create RDS Instance**

1. **Login to AWS Console**
   - Go to [AWS Console](https://console.aws.amazon.com/)
   - Navigate to RDS service

2. **Create Database**
   - Click "Create database"
   - Choose "Standard create"
   - Select "PostgreSQL" (recommended) or "MySQL"
   - Choose "Free tier" for development or "Production" for production

3. **Configure Settings**
   ```
   DB instance identifier: spotify-app-db
   Master username: postgres (or your choice)
   Master password: [create a strong password]
   ```

4. **Instance Configuration**
   - **Free tier**: db.t3.micro (1 vCPU, 1 GB RAM)
   - **Production**: db.t3.small or larger based on needs

5. **Storage**
   - **Free tier**: 20 GB
   - **Production**: Start with 100 GB, enable auto-scaling

6. **Connectivity**
   - **VPC**: Default VPC
   - **Public access**: Yes (for development)
   - **VPC security group**: Create new or use default
   - **Availability Zone**: No preference
   - **Database port**: 5432 (PostgreSQL) or 3306 (MySQL)

7. **Database Authentication**
   - Choose "Password authentication"

8. **Additional Configuration**
   - **Initial database name**: spotify_app
   - **Backup retention**: 7 days (free tier) or 30 days (production)
   - **Enable monitoring**: Yes

#### **Step 2: Update Django Settings**

Create a new settings file for production:

```python
# api/myproject/myproject/production_settings.py

import os
from pathlib import Path
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Update allowed hosts
ALLOWED_HOSTS = [
    'your-domain.com',
    'your-ec2-instance-ip',
    'localhost',
    '127.0.0.1',
]

# Database configuration for RDS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # or 'django.db.backends.mysql'
        'NAME': os.getenv('DB_NAME', 'spotify_app'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),  # or '3306' for MySQL
        'OPTIONS': {
            'sslmode': 'require',  # Enable SSL
        },
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### **Step 3: Update Requirements**

Add database adapter to requirements:

```txt
# api/requirements.txt

# Add these lines:
psycopg2-binary==2.9.9  # For PostgreSQL
# OR
mysqlclient==2.2.0      # For MySQL
```

#### **Step 4: Environment Variables**

Create production environment file:

```bash
# api/.env.production

# Database
DB_NAME=spotify_app
DB_USER=postgres
DB_PASSWORD=your_strong_password_here
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432

# Django
SECRET_KEY=your_production_secret_key_here
DEBUG=False

# Spotify
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=https://your-domain.com/api/spotify/callback
```

#### **Step 5: Run Migrations**

```bash
# Install database adapter
pip install psycopg2-binary  # or mysqlclient

# Run migrations
python manage.py migrate --settings=myproject.production_settings
```

### **Option 2: Amazon DynamoDB (NoSQL Alternative)**

For a serverless, NoSQL approach:

#### **Step 1: Create DynamoDB Tables**

```python
# api/myproject/app/dynamodb_models.py

import boto3
from botocore.exceptions import ClientError

def create_tables():
    dynamodb = boto3.resource('dynamodb')
    
    # Users table
    users_table = dynamodb.create_table(
        TableName='spotify_users',
        KeySchema=[
            {
                'AttributeName': 'spotify_id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'spotify_id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    
    # Song posts table
    songs_table = dynamodb.create_table(
        TableName='song_posts',
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'posted_date',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'posted_date',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    
    return users_table, songs_table
```

### **Option 3: AWS Lambda + RDS (Serverless)**

For a completely serverless approach:

#### **Step 1: Create Lambda Function**

```python
# api/lambda_function.py

import json
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.production_settings')
django.setup()

from django.http import HttpRequest
from django.core.handlers.wsgi import WSGIHandler
from django.urls import resolve

def lambda_handler(event, context):
    """AWS Lambda handler for Django application"""
    
    # Create Django request from API Gateway event
    request = HttpRequest()
    request.method = event['httpMethod']
    request.path = event['path']
    request.META = event['headers']
    
    # Handle Django routing
    try:
        resolver_match = resolve(request.path)
        view_func = resolver_match.func
        response = view_func(request, *resolver_match.args, **resolver_match.kwargs)
        
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.content.decode('utf-8')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### **Deployment Options**

#### **Option A: EC2 Instance**

1. **Launch EC2 Instance**
   - Choose Ubuntu or Amazon Linux
   - Configure security groups for HTTP/HTTPS
   - Install Python, pip, and dependencies

2. **Deploy Application**
   ```bash
   # On EC2 instance
   git clone your-repo
   cd api
   pip install -r requirements.txt
   python manage.py migrate --settings=myproject.production_settings
   python manage.py collectstatic --settings=myproject.production_settings
   
   # Run with Gunicorn
   gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
   ```

#### **Option B: AWS Elastic Beanstalk**

1. **Create Application**
   - Go to Elastic Beanstalk console
   - Create new application
   - Choose Python platform

2. **Deploy**
   ```bash
   # Install EB CLI
   pip install awsebcli
   
   # Initialize EB project
   eb init
   eb create spotify-app-env
   eb deploy
   ```

#### **Option C: AWS App Runner**

1. **Create App Runner Service**
   - Go to App Runner console
   - Connect to your GitHub repository
   - Configure build settings

2. **Environment Variables**
   - Add all environment variables from `.env.production`
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn myproject.wsgi:application --bind 0.0.0.0:8000`

### **Security Best Practices**

1. **Use IAM Roles** instead of access keys
2. **Enable VPC** for database isolation
3. **Use SSL/TLS** for all connections
4. **Regular backups** and monitoring
5. **Security groups** with minimal required access
6. **Secrets Manager** for sensitive data

### **Cost Estimation**

#### **Free Tier (12 months)**
- RDS: 750 hours/month of db.t3.micro
- EC2: 750 hours/month of t2.micro
- **Total: ~$0/month**

#### **Production (small scale)**
- RDS: db.t3.small (~$15/month)
- EC2: t3.small (~$15/month)
- **Total: ~$30/month**

### **Monitoring and Maintenance**

1. **CloudWatch** for monitoring
2. **RDS Performance Insights**
3. **Automated backups**
4. **Security patches**
5. **Scaling policies**

### **Next Steps**

1. Choose your preferred option (RDS recommended)
2. Follow the setup guide
3. Test locally with production settings
4. Deploy to AWS
5. Configure monitoring and alerts
6. Set up CI/CD pipeline

Would you like me to help you with any specific part of this setup? 