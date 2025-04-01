#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.backend_stack import BackendStack
from stacks.frontend_stack import FrontendStack
from stacks.shared_vpc_stack import SharedVPCStack
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = cdk.App()

# Create the shared VPC stack
shared_vpc_stack = SharedVPCStack(app, "PortfolioSharedVPCStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

# Create the backend stack with dependency on shared VPC
backend_stack = BackendStack(app, "MovieRecommendationBackendStack",
    shared_vpc_stack=shared_vpc_stack,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

# Create the frontend stack with dependencies on both backend and shared VPC
frontend_stack = FrontendStack(app, "MovieRecommendationFrontendStack",
    backend_stack=backend_stack,
    shared_vpc_stack=shared_vpc_stack,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

# Add explicit dependencies
backend_stack.add_dependency(shared_vpc_stack)
frontend_stack.add_dependency(backend_stack)
frontend_stack.add_dependency(shared_vpc_stack)

app.synth() 