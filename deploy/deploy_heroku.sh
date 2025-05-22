#!/bin/bash
# Heroku Deployment Script for DigitalClone IITG

# Load deployment configuration
source .env.deploy

echo "Starting Heroku deployment..."

# Check if the Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "Heroku CLI is not installed. Please install it first."
    exit 1
fi

# Check login status
if ! heroku auth:whoami &> /dev/null; then
    echo "Not logged in to Heroku. Please log in."
    heroku login
fi

# Create or use existing Heroku app
if ! heroku apps:info --app $HEROKU_APP_NAME &> /dev/null; then
    echo "Creating Heroku app $HEROKU_APP_NAME..."
    heroku create $HEROKU_APP_NAME
else
    echo "Using existing Heroku app $HEROKU_APP_NAME..."
fi

# Add necessary buildpacks
echo "Adding buildpacks..."
heroku buildpacks:clear --app $HEROKU_APP_NAME
heroku buildpacks:add heroku/python --app $HEROKU_APP_NAME
heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git --app $HEROKU_APP_NAME

# Set environment variables
echo "Setting environment variables..."
# Read the .env file and set each variable in Heroku
while IFS='=' read -r key value
do
    # Skip empty lines and comments
    if [ -z "$key" ] || [[ $key == \#* ]]; then
        continue
    fi
    
    echo "Setting $key"
    heroku config:set "$key=$value" --app $HEROKU_APP_NAME
done < .env

# Set additional Heroku-specific config
heroku config:set WEB_CONCURRENCY=2 --app $HEROKU_APP_NAME

# Add a database if specified
if [ "$HEROKU_ADD_DATABASE" = "true" ]; then
    echo "Adding PostgreSQL database..."
    heroku addons:create heroku-postgresql:hobby-dev --app $HEROKU_APP_NAME
fi

# Deploy using container registry
echo "Logging in to Heroku Container Registry..."
heroku container:login

echo "Building and pushing container..."
heroku container:push web --app $HEROKU_APP_NAME

echo "Releasing container..."
heroku container:release web --app $HEROKU_APP_NAME

# Open the app in browser
echo "Deployment successful!"
echo "Your application is available at: https://$HEROKU_APP_NAME.herokuapp.com"
heroku open --app $HEROKU_APP_NAME
