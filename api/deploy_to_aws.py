#!/usr/bin/env python3
"""
AWS Deployment Helper Script for Django Spotify App
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_step(step_num, title, description=""):
    """Print a formatted step"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*60}")
    if description:
        print(description)
    print()

def check_prerequisites():
    """Check if required tools are installed"""
    print_step(1, "Checking Prerequisites")
    
    tools = {
        'aws': 'AWS CLI - Install from https://aws.amazon.com/cli/',
        'git': 'Git - Install from https://git-scm.com/',
        'python3': 'Python 3 - Should already be installed',
        'pip3': 'Pip - Should already be installed',
    }
    
    missing_tools = []
    
    for tool, description in tools.items():
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
            print(f"✅ {tool} - Found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool} - Missing")
            print(f"   {description}")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n⚠️  Please install missing tools: {', '.join(missing_tools)}")
        return False
    
    return True

def create_production_env():
    """Create production environment file"""
    print_step(2, "Creating Production Environment File")
    
    env_file = Path('.env.production')
    
    if env_file.exists():
        print("⚠️  .env.production already exists. Skipping...")
        return
    
    env_template = """# Production Environment Variables
# Replace these values with your actual AWS RDS credentials

# Database Configuration
DB_NAME=spotify_app
DB_USER=postgres
DB_PASSWORD=your_strong_password_here
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432

# Django Configuration
SECRET_KEY=your_production_secret_key_here
DEBUG=False

# Spotify Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=https://your-domain.com/api/spotify/callback

# AWS Configuration (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Optional: S3 for static files
USE_S3=False
AWS_STORAGE_BUCKET_NAME=your-bucket-name
"""
    
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env.production file")
    print("📝 Please update the values with your actual credentials")

def install_dependencies():
    """Install production dependencies"""
    print_step(3, "Installing Production Dependencies")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print_step(4, "Testing Database Connection")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.production')
    
    db_host = os.getenv('DB_HOST')
    if not db_host or db_host == 'your-rds-endpoint.region.rds.amazonaws.com':
        print("⚠️  Database host not configured. Please update .env.production")
        return False
    
    try:
        # Test with production settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.production_settings')
        import django
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("📝 Make sure your RDS instance is running and credentials are correct")
        return False

def run_migrations():
    """Run database migrations"""
    print_step(5, "Running Database Migrations")
    
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'migrate',
            '--settings=myproject.production_settings'
        ], check=True)
        print("✅ Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        return False

def collect_static_files():
    """Collect static files"""
    print_step(6, "Collecting Static Files")
    
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'collectstatic',
            '--settings=myproject.production_settings',
            '--noinput'
        ], check=True)
        print("✅ Static files collected successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Static file collection failed: {e}")
        return False

def create_deployment_files():
    """Create deployment configuration files"""
    print_step(7, "Creating Deployment Files")
    
    # Create Procfile for Heroku/App Runner
    procfile = Path('Procfile')
    if not procfile.exists():
        with open(procfile, 'w') as f:
            f.write("web: gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT\n")
        print("✅ Created Procfile")
    
    # Create .ebextensions for Elastic Beanstalk
    eb_dir = Path('.ebextensions')
    eb_dir.mkdir(exist_ok=True)
    
    eb_config = eb_dir / 'django.config'
    if not eb_config.exists():
        config_content = """option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: myproject.wsgi:application
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: staticfiles
"""
        with open(eb_config, 'w') as f:
            f.write(config_content)
        print("✅ Created Elastic Beanstalk configuration")
    
    # Create Dockerfile for container deployment
    dockerfile = Path('Dockerfile')
    if not dockerfile.exists():
        docker_content = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --settings=myproject.production_settings --noinput

EXPOSE 8000

CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
"""
        with open(dockerfile, 'w') as f:
            f.write(docker_content)
        print("✅ Created Dockerfile")

def print_next_steps():
    """Print next steps for deployment"""
    print_step(8, "Next Steps for AWS Deployment")
    
    print("🚀 Choose your deployment method:")
    print()
    print("1. AWS Elastic Beanstalk (Recommended for beginners):")
    print("   - Install EB CLI: pip install awsebcli")
    print("   - Initialize: eb init")
    print("   - Create environment: eb create spotify-app-env")
    print("   - Deploy: eb deploy")
    print()
    print("2. AWS App Runner (Serverless):")
    print("   - Go to AWS App Runner console")
    print("   - Connect your GitHub repository")
    print("   - Configure environment variables")
    print()
    print("3. EC2 Instance (Manual):")
    print("   - Launch EC2 instance")
    print("   - Install dependencies")
    print("   - Run: gunicorn myproject.wsgi:application --bind 0.0.0.0:8000")
    print()
    print("4. AWS Lambda (Serverless):")
    print("   - Package application")
    print("   - Create Lambda function")
    print("   - Configure API Gateway")
    print()
    print("📋 Before deploying:")
    print("   - Update .env.production with real credentials")
    print("   - Create RDS database instance")
    print("   - Configure security groups")
    print("   - Set up domain and SSL certificate")
    print()
    print("🔗 Useful AWS Console Links:")
    print("   - RDS: https://console.aws.amazon.com/rds/")
    print("   - EC2: https://console.aws.amazon.com/ec2/")
    print("   - Elastic Beanstalk: https://console.aws.amazon.com/elasticbeanstalk/")
    print("   - App Runner: https://console.aws.amazon.com/apprunner/")

def main():
    """Main deployment process"""
    print("🚀 AWS Deployment Helper for Django Spotify App")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path('manage.py').exists():
        print("❌ Please run this script from the Django project root directory")
        sys.exit(1)
    
    # Run deployment steps
    steps = [
        check_prerequisites,
        create_production_env,
        install_dependencies,
        test_database_connection,
        run_migrations,
        collect_static_files,
        create_deployment_files,
        print_next_steps,
    ]
    
    for step in steps:
        try:
            if not step():
                print(f"\n⚠️  Step failed. Please fix the issue and run again.")
                break
        except KeyboardInterrupt:
            print("\n\n⚠️  Deployment cancelled by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            break
    
    print("\n🎉 Deployment helper completed!")
    print("📖 Check aws_setup_guide.md for detailed instructions")

if __name__ == "__main__":
    main() 