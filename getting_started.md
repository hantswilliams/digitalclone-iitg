# Getting Started with DigitalClone IITG

This document provides instructions for setting up and running the DigitalClone IITG application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your machine
- AWS S3 account for media storage
- PlayHT account for voice synthesis
- Hugging Face account for SadTalker API access
- (Optional) Google OAuth credentials for authentication

## Environment Variables Setup

Create a `.env` file in the root directory of the project with the following variables:

```
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# PlayHT API Configuration
PLAYHT_USERID=your_playht_user_id
PLAYHT_SECRET=your_playht_api_key

# Hugging Face API
HUGGING=your_huggingface_api_key

# Google OAuth (Optional)
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

# Flask Secret Key (generate a random one for security)
FLASK_SECRET_KEY=your_random_secret_key
```

### How to Obtain API Keys

1. **AWS S3 Keys**:
   - Log in to your AWS Management Console
   - Go to IAM > Users > Create User
   - Attach policies for S3 access
   - Generate access key and secret key

2. **PlayHT API Keys**:
   - Create an account at [Play.ht](https://play.ht/)
   - Navigate to your account settings
   - Generate API keys under the API section

3. **Hugging Face API Key**:
   - Create an account at [Hugging Face](https://huggingface.co/)
   - Go to Settings > Access Tokens
   - Create a new token with write permissions

4. **Google OAuth Credentials** (Optional):
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google+ API
   - Configure the OAuth consent screen
   - Create OAuth Client ID credentials
   - Set authorized redirect URIs (e.g., http://localhost:5000/auth/google/callback)

## S3 Bucket Configuration

1. Create an S3 bucket named `iitg-mvp` (or change the bucket name in the code)
2. Configure the bucket for public read access (for media files)
3. Set up CORS configuration if needed

## Running the Application

1. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

2. **Access the application**:
   Open your browser and navigate to `http://localhost:5000`

## Development Mode

For development purposes, you can modify the environment to development mode:

```bash
# In docker-compose.yml
environment:
  - FLASK_ENV=development
```

## Continuous Integration / Continuous Deployment

This project includes a GitHub Actions workflow for automated CI/CD. To use it:

1. **Push your repository to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/digitalclone-iitg.git
   git push -u origin main
   ```

2. **Set up GitHub Secrets**:
   Navigate to your GitHub repository → Settings → Secrets and variables → Actions, and add the following secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `PLAYHT_USERID`
   - `PLAYHT_SECRET`
   - `HUGGING`
   - `FLASK_SECRET_KEY`
   - `GCP_PROJECT_ID` (if using Google Cloud)
   - `GCP_SA_KEY` (if using Google Cloud)

3. **Trigger Deployments**:
   - **Automatic**: Push to the `main` branch to trigger the production deployment
   - **Manual**: Go to Actions → Deploy to Cloud → Run workflow, and select your target environment

The workflow is configured to deploy to AWS Elastic Beanstalk for production and Google Cloud Run for staging environments.

For more detailed deployment options, see the `cloud_deployment.md` file and the scripts in the `deploy/` directory.

## Troubleshooting

- **Permission Issues**: Ensure the temp_outputs directory has write permissions
- **API Rate Limits**: Be aware of rate limits on the external APIs (PlayHT, Hugging Face)
- **S3 Access Issues**: Verify your AWS credentials and bucket permissions

## Technical Architecture

The application consists of several components:
- Flask web application (app.py)
- Database models (db_model/db.py)
- Utility services:
  - PlayHT voice synthesis (utils/playht.py)
  - SadTalker video generation (utils/sadtalker.py)
  - S3 storage integration (utils/s3.py)

Each component is accessed through the Flask routes defined in app.py, allowing for a complete workflow from text input to video output with synthesized speech.
