#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.backend_stack import BackendStack
from stacks.frontend_stack import FrontendStack
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = cdk.App()

# Create the backend stack
backend_stack = BackendStack(app, "MovieRecommendationBackendStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

# Create the frontend stack
FrontendStack(app, "MovieRecommendationFrontendStack",
    backend_alb_dns=backend_stack.backend_alb_dns,  # Pass the backend ALB DNS name
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

app.synth() 