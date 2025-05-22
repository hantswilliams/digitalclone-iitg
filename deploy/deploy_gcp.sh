#!/bin/bash
# Google Cloud Run Deployment Script for DigitalClone IITG

# Load deployment configuration
source .env.deploy

echo "Starting Google Cloud Run deployment..."

# Check if the Google Cloud SDK is installed
if ! command -v gcloud &> /dev/null; then
    echo "Google Cloud SDK is not installed. Please install it first."
    exit 1
fi

# Authenticate with Google Cloud (if needed)
if [ "$GCP_SERVICE_ACCOUNT_KEY" != "" ]; then
    echo "Authenticating with service account..."
    echo $GCP_SERVICE_ACCOUNT_KEY > /tmp/service-account.json
    gcloud auth activate-service-account --key-file=/tmp/service-account.json
    rm /tmp/service-account.json
fi

# Set the project
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable artifactregistry.googleapis.com run.googleapis.com secretmanager.googleapis.com

# Build and tag the Docker image
echo "Building Docker image..."
docker build -t gcr.io/$GCP_PROJECT_ID/$GCP_SERVICE_NAME:latest .

# Configure Docker to use Google Cloud credentials
gcloud auth configure-docker gcr.io

# Push the image to Google Container Registry
echo "Pushing Docker image to Google Container Registry..."
docker push gcr.io/$GCP_PROJECT_ID/$GCP_SERVICE_NAME:latest

# Create a secret for environment variables
echo "Creating secret for environment variables..."
gcloud secrets create $GCP_SECRET_NAME --data-file=.env --replication-policy="automatic"

# Grant the Cloud Run service account access to the secret
echo "Setting up secret access permissions..."
SERVICE_ACCOUNT="$(gcloud run services describe $GCP_SERVICE_NAME --platform managed --region $GCP_REGION --format='value(serviceAccount)' 2>/dev/null || echo $GCP_PROJECT_ID-compute@developer.gserviceaccount.com)"
gcloud secrets add-iam-policy-binding $GCP_SECRET_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $GCP_SERVICE_NAME \
  --image gcr.io/$GCP_PROJECT_ID/$GCP_SERVICE_NAME:latest \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --memory $GCP_MEMORY \
  --cpu $GCP_CPU \
  --set-secrets="/app/.env=$GCP_SECRET_NAME:latest"

# Get the URL of the deployed service
URL=$(gcloud run services describe $GCP_SERVICE_NAME \
  --platform managed \
  --region $GCP_REGION \
  --format="value(status.url)")

echo "Deployment successful!"
echo "Your application is available at: $URL"
