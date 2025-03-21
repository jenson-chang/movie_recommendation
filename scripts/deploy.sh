#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    print_message "Error: .env file not found in the root directory." "$RED"
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_message "Error: AWS CLI is not installed. Please install it first." "$RED"
    exit 1
fi

# Check if AWS credentials are configured using the profile
if ! aws sts get-caller-identity --profile $AWS_PROFILE &> /dev/null; then
    print_message "Error: AWS credentials not configured for profile '$AWS_PROFILE'. Please check your ~/.aws/credentials file." "$RED"
    exit 1
fi

# Check if CDK CLI is installed
if ! command -v cdk &> /dev/null; then
    print_message "Error: AWS CDK CLI is not installed. Installing..." "$YELLOW"
    npm install -g aws-cdk
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "infrastructure/.venv" ]; then
    print_message "Creating virtual environment..." "$YELLOW"
    cd infrastructure
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    print_message "Using existing virtual environment..." "$YELLOW"
    cd infrastructure
    source .venv/bin/activate
    cd ..
fi

# Bootstrap CDK (if not already bootstrapped)
print_message "Checking CDK bootstrap status..." "$YELLOW"
cd infrastructure
if ! cdk ls --profile $AWS_PROFILE &> /dev/null; then
    print_message "Bootstrapping CDK..." "$YELLOW"
    cdk bootstrap --profile $AWS_PROFILE
else
    print_message "CDK already bootstrapped." "$GREEN"
fi

# Deploy the stacks
print_message "Deploying stacks..." "$YELLOW"
cdk deploy --all --require-approval never --profile $AWS_PROFILE

print_message "Deployment completed successfully!" "$GREEN"

# Print important information
print_message "\nImportant Information:" "$YELLOW"
print_message "1. Frontend URL: Check the CloudFormation outputs for the FrontendLoadBalancerDNS" "$GREEN"
print_message "2. Backend API: The backend service is internal to the VPC" "$GREEN"
print_message "3. To destroy the infrastructure: Run 'cdk destroy --all --profile $AWS_PROFILE' in the infrastructure directory" "$GREEN" 