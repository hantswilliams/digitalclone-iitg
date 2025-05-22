# DigitalClone IITG - Quick Deploy

A set of scripts and configuration files to quickly deploy the DigitalClone IITG application to various cloud providers.

## Available Deployment Scripts

- `deploy_aws.sh` - Deploy to AWS Elastic Beanstalk
- `deploy_gcp.sh` - Deploy to Google Cloud Run
- `deploy_heroku.sh` - Deploy to Heroku
- `deploy_digitalocean.sh` - Deploy to DigitalOcean App Platform

## Usage

1. Make sure you have the necessary credentials and CLI tools installed for your chosen cloud provider
2. Configure your credentials and project details in `.env.deploy`
3. Make the script executable: `chmod +x deploy_[provider].sh`
4. Run the script: `./deploy_[provider].sh`

See individual scripts for provider-specific configuration options.

## Common Requirements

- Docker installed and running
- Git repository initialized
- `.env` file with all required application environment variables
- `.env.deploy` file with deployment-specific variables (see example below)

## Documentation

For detailed deployment instructions and considerations, see `cloud_deployment.md`
