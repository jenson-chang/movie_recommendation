# Movie Recommendation System

A full-stack movie recommendation system built with FastAPI, Streamlit, and AWS CDK for infrastructure deployment.

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
   - Collaborative filtering model
   - Docker containerized application
   - Deployed on AWS ECS Fargate
   - Internal VPC with Application Load Balancer

3. **Infrastructure (AWS CDK)**
   - Infrastructure as Code using AWS CDK
   - ECS Fargate clusters for container orchestration
   - VPC with public and private subnets
   - Auto-scaling configuration
   - Application Load Balancers

## API Endpoints

### POST /predict/
Get personalized movie recommendations for a user.

**Request Body:**
```json
{
    "user_id": 123
}
```

**Response:**
```json
{
    "recommendations": [
        [movie_id, score],
        ...
    ]
}
```

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
├── frontend/              # Streamlit frontend application
├── infrastructure/        # AWS CDK infrastructure code
│   ├── stacks/            # CDK stack definitions
│   ├── app.py             # CDK app entry point
│   └── requirements.txt   # Python dependencies
├── scripts/               # Deployment and utility scripts
├── .env                   # Environment variables
└── docker-compose.yml     # Local development setup
```

## Environment Variables

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

## Deployment

1. Configure AWS credentials:
   ```bash
   aws configure
   ```

2. Deploy the infrastructure:
   ```bash
   ./scripts/deploy.sh
   ```

The script will:
- Create necessary AWS resources
- Deploy the frontend and backend containers
- Set up networking and security groups
- Configure auto-scaling

## Local Development

1. Start the development environment:
   ```bash
   docker-compose up
   ```

2. Access the applications:
   - Frontend (Streamlit): http://localhost:8501
   - Backend (FastAPI): http://localhost:8000

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