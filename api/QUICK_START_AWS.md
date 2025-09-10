# 🚀 Quick Start: Deploy Django Spotify App to AWS

## 📋 Prerequisites

1. **AWS Account** - Sign up at [aws.amazon.com](https://aws.amazon.com)
2. **AWS CLI** - Install from [aws.amazon.com/cli](https://aws.amazon.com/cli)
3. **Git** - For version control
4. **Python 3.11+** - Already installed

## 🎯 Recommended Approach: AWS RDS + Elastic Beanstalk

### **Step 1: Create RDS Database**

1. **Go to AWS RDS Console**
   - Visit: https://console.aws.amazon.com/rds/
   - Click "Create database"

2. **Choose Configuration**
   - **Engine**: PostgreSQL (recommended) or MySQL
   - **Template**: Free tier (for development)
   - **DB instance identifier**: `spotify-app-db`
   - **Master username**: `postgres`
   - **Master password**: Create a strong password

3. **Instance Configuration**
   - **Instance class**: db.t3.micro (free tier)
   - **Storage**: 20 GB
   - **Public access**: Yes (for development)

4. **Connectivity**
   - **VPC**: Default VPC
   - **Security group**: Create new
   - **Database port**: 5432 (PostgreSQL) or 3306 (MySQL)

5. **Additional Configuration**
   - **Initial database name**: `spotify_app`
   - **Backup retention**: 7 days

6. **Create Database**
   - Click "Create database"
   - Wait for status to become "Available"

### **Step 2: Get Database Endpoint**

1. **Copy the endpoint**
   - Go to your RDS instance
   - Copy the endpoint (e.g., `spotify-app-db.abc123.us-east-1.rds.amazonaws.com`)

### **Step 3: Update Environment Variables**

1. **Edit `.env.production`**
   ```bash
   # Replace these values:
   DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
   DB_PASSWORD=your_actual_password
   SECRET_KEY=generate_a_new_secret_key
   ```

2. **Generate Secret Key**
   ```bash
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

### **Step 4: Deploy with Elastic Beanstalk**

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB Project**
   ```bash
   cd api/myproject
   eb init
   # Follow the prompts:
   # - Select your region
   # - Create new application: spotify-app
   # - Platform: Python
   # - Python version: 3.11
   # - Setup SSH: No (for now)
   ```

3. **Create Environment**
   ```bash
   eb create spotify-app-env
   # This will take 5-10 minutes
   ```

4. **Set Environment Variables**
   ```bash
   eb setenv DB_HOST=your-rds-endpoint
   eb setenv DB_PASSWORD=your_password
   eb setenv SECRET_KEY=your_secret_key
   eb setenv SPOTIFY_CLIENT_ID=your_spotify_client_id
   eb setenv SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   eb setenv SPOTIFY_REDIRECT_URI=https://your-eb-url.elasticbeanstalk.com/api/spotify/callback
   ```

5. **Deploy**
   ```bash
   eb deploy
   ```

### **Step 5: Configure Security Groups**

1. **RDS Security Group**
   - Go to RDS → Databases → Your DB → Security
   - Edit the security group
   - Add rule: PostgreSQL (5432) from Elastic Beanstalk security group

2. **Elastic Beanstalk Security Group**
   - Go to EC2 → Security Groups
   - Find the EB security group
   - Add rule: HTTP (80) from anywhere
   - Add rule: HTTPS (443) from anywhere

### **Step 6: Test Your Deployment**

1. **Get your EB URL**
   ```bash
   eb status
   # Copy the CNAME URL
   ```

2. **Test the API**
   ```bash
   curl https://your-app.elasticbeanstalk.com/api/spotify/login
   ```

3. **Update Flutter App**
   - Change the API base URL in Flutter to your EB URL
   - Test the authentication flow

## 🔧 Alternative Deployment Options

### **Option A: AWS App Runner (Easiest)**

1. **Go to App Runner Console**
   - Visit: https://console.aws.amazon.com/apprunner/
   - Click "Create service"

2. **Connect Repository**
   - Connect your GitHub repository
   - Select the main branch

3. **Configure Build**
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `gunicorn myproject.wsgi:application --bind 0.0.0.0:8000`

4. **Environment Variables**
   - Add all variables from `.env.production`

### **Option B: EC2 Instance (Manual)**

1. **Launch EC2 Instance**
   - Choose Ubuntu Server 22.04
   - Instance type: t3.micro (free tier)
   - Configure security groups for HTTP/HTTPS

2. **Connect and Setup**
   ```bash
   # SSH into your instance
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Install dependencies
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   
   # Clone your repository
   git clone your-repo-url
   cd your-repo/api/myproject
   
   # Setup virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Run migrations
   python manage.py migrate --settings=myproject.production_settings
   
   # Start with Gunicorn
   gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
   ```

## 💰 Cost Estimation

### **Free Tier (12 months)**
- **RDS**: 750 hours/month db.t3.micro
- **EC2/EB**: 750 hours/month t3.micro
- **Total**: ~$0/month

### **Production (small scale)**
- **RDS**: db.t3.small (~$15/month)
- **EB**: t3.small (~$15/month)
- **Total**: ~$30/month

## 🔒 Security Checklist

- [ ] Use strong passwords
- [ ] Enable SSL/TLS
- [ ] Configure security groups properly
- [ ] Use IAM roles instead of access keys
- [ ] Enable automated backups
- [ ] Set up monitoring and alerts
- [ ] Regular security updates

## 🚨 Troubleshooting

### **Common Issues:**

1. **Database Connection Failed**
   - Check security group rules
   - Verify endpoint and credentials
   - Ensure RDS is in same VPC

2. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check STATIC_ROOT configuration

3. **Environment Variables Not Working**
   - Use `eb setenv` for Elastic Beanstalk
   - Check variable names match exactly

4. **SSL Certificate Issues**
   - Use AWS Certificate Manager
   - Configure HTTPS redirect

## 📞 Support

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Django Documentation**: https://docs.djangoproject.com/
- **Elastic Beanstalk Guide**: https://docs.aws.amazon.com/elasticbeanstalk/

## 🎉 Next Steps

1. **Monitor your application**
   - Set up CloudWatch alarms
   - Monitor RDS performance

2. **Scale as needed**
   - Increase instance sizes
   - Add load balancers
   - Implement caching

3. **Set up CI/CD**
   - GitHub Actions
   - AWS CodePipeline
   - Automated deployments

Your Django Spotify app is now ready for production on AWS! 🚀 