#!/bin/bash

# Exit on error
set -e

# Check if AWS credentials are configured
if ! aws sts get-caller-identity --profile movies &> /dev/null; then
    echo "Error: AWS credentials not configured. Please configure your AWS credentials first."
    exit 1
fi

# Install CDK dependencies
echo "Installing CDK dependencies..."
cd infrastructure
python3 -m pip install -r requirements.txt

# Bootstrap CDK (if not already bootstrapped)
echo "Bootstrapping CDK..."
AWS_PROFILE=movies cdk bootstrap

# Deploy the stacks
echo "Deploying stacks..."
AWS_PROFILE=movies cdk deploy --all --require-approval never

echo "Deployment completed successfully!" 