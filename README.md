# Movie Recommendation System
This system provides personalized movie recommendations based on user preferences and viewing history. It features a modern web interface, scalable backend API, and cloud-native infrastructure deployment.

## Features

- 🎬 Movie recommendations using collaborative filtering and content-based filtering
- 🌐 Modern, responsive web interface with Streamlit
- 🔒 Secure API endpoints with FastAPI
- 🚀 Cloud-native deployment on AWS
- 📊 Interactive data visualization
- 🔄 Auto-scaling infrastructure
- 🛡️ Secure VPC architecture
- 📝 Comprehensive logging and monitoring

## Architecture

The system consists of three main components:

1. **Frontend (Streamlit)**
   - User interface for movie recommendations
   - Interactive data visualization
   - Docker containerized application
   - Deployed on AWS ECS Fargate
   - Public-facing with Application Load Balancer

2. **Backend (FastAPI)**
   - API for movie recommendations
   - Single endpoint for personalized recommendations
   - Collaborative filtering and content-based filtering model
   - Docker containerized application
   - Deployed on AWS ECS Fargate
   - Internal VPC with Application Load Balancer

3. **Infrastructure (AWS CDK)**
   - Infrastructure as Code using AWS CDK
   - ECS Fargate clusters for container orchestration
   - VPC with public and private subnets
   - Auto-scaling configuration
   - Application Load Balancers

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- Python 3.8 or later
- Docker installed locally (for development)
- Node.js and npm (for CDK)

## Project Structure

```
movie_recommendation/
├── backend/               # FastAPI backend service
│   ├── app/              # Application code
│   ├── Dockerfile        # Container definition
│   └── requirements.txt  # Python dependencies
├── frontend/             # Streamlit frontend application
│   ├── src/              # Source code
│   ├── Dockerfile        # Container definition
│   └── requirements.txt  # Python dependencies
├── infrastructure/       # AWS CDK infrastructure code
│   ├── stacks/          # CDK stack definitions
│   ├── app.py           # CDK app entry point
│   └── requirements.txt # Python dependencies
├── scripts/             # Deployment and utility scripts
├── .env                 # Environment variables
└── docker-compose.yml   # Local development setup
```

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/jenson-chang/movie_recommendation.git
   cd movie_recommendation
   ```

2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

3. Access the applications:
   - Frontend (Streamlit): http://localhost:8501
   - Backend (FastAPI): http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Deployment
Create a `.env` file in the root directory with the following variables:

```env
# AWS Configuration
AWS_PROFILE=your-profile
CDK_DEFAULT_REGION=your-region
CDK_DEFAULT_ACCOUNT=your-account-id

# Application Configuration
APP_NAME=movie-recommendation
ENVIRONMENT=development

# Container Configuration
FRONTEND_PORT=8501  # Default Streamlit port
BACKEND_PORT=8000
BACKEND_CPU=256
BACKEND_MEMORY=512
FRONTEND_CPU=256
FRONTEND_MEMORY=512

# Scaling Configuration
MIN_CAPACITY=1
MAX_CAPACITY=4
DESIRED_COUNT=2
SCALE_THRESHOLD=70
SCALE_COOLDOWN=60

# VPC Configuration
VPC_MAX_AZS=2
VPC_NAT_GATEWAYS=1

# Health Check Configuration
HEALTH_CHECK_GRACE_PERIOD=60
```

1. Configure AWS credentials:
   ```bash
   aws configure
   ```

2. Deploy the infrastructure using AWS CDK:
   ```bash
   cd infrastructure
   cdk deploy --all
   ```

This will:
- Create the VPC and networking components
- Deploy the ECS Fargate clusters
- Set up the Application Load Balancers
- Deploy the frontend and backend containers
- Configure auto-scaling and monitoring

## Infrastructure Details

### VPC Configuration
- 2 Availability Zones
- Public and private subnets
- NAT Gateway for private subnet internet access

### ECS Fargate
- Separate clusters for frontend and backend
- Auto-scaling based on CPU and memory utilization
- Health checks and grace periods

### Security
- Security groups for container communication
- Internal VPC for backend service
- Public-facing ALB for frontend

## Monitoring and Maintenance

- CloudWatch logs for container monitoring
- Auto-scaling based on resource utilization
- Health checks for container status

## Cleanup

To destroy the infrastructure:
```bash
cd infrastructure
cdk destroy --all
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
