#!/bin/bash
# AWS Elastic Beanstalk Deployment Script for DigitalClone IITG

# Load deployment configuration
source .env.deploy

echo "Starting AWS Elastic Beanstalk deployment..."

# Check if the AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if the EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo "EB CLI is not installed. Installing now..."
    pip install awsebcli
fi

# Initialize EB if not already done
if [ ! -d .elasticbeanstalk ]; then
    echo "Initializing Elastic Beanstalk application..."
    eb init -p docker $AWS_EB_APP_NAME --region $AWS_REGION
else
    echo "Elastic Beanstalk already initialized."
fi

# Check if the environment exists, create if not
if ! eb status $AWS_EB_ENV_NAME &> /dev/null; then
    echo "Creating Elastic Beanstalk environment..."
    eb create $AWS_EB_ENV_NAME --instance-type $AWS_INSTANCE_TYPE --single
else
    echo "Elastic Beanstalk environment already exists. Deploying..."
fi

# Set environment variables
echo "Setting environment variables..."
# Read the .env file and set each variable in EB
while IFS='=' read -r key value
do
    # Skip empty lines and comments
    if [ -z "$key" ] || [[ $key == \#* ]]; then
        continue
    fi
    
    # Remove quotes from the value
    value=$(echo $value | sed -e 's/^"//' -e 's/"$//')
    
    echo "Setting $key"
    aws elasticbeanstalk update-environment \
        --application-name $AWS_EB_APP_NAME \
        --environment-name $AWS_EB_ENV_NAME \
        --option-settings Namespace=aws:elasticbeanstalk:application:environment,OptionName=$key,Value="$value"
done < .env

# Deploy the application
echo "Deploying application to Elastic Beanstalk..."
eb deploy $AWS_EB_ENV_NAME

# Check deployment status
if eb status $AWS_EB_ENV_NAME | grep -q "Status: Ready"; then
    echo "Deployment successful!"
    echo "Your application is available at:"
    eb status $AWS_EB_ENV_NAME | grep CNAME
else
    echo "Deployment may have encountered issues. Check the EB logs for more details."
    eb logs $AWS_EB_ENV_NAME
fi
