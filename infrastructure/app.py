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

# Create the frontend stack with explicit dependency on backend stack
frontend_stack = FrontendStack(app, "MovieRecommendationFrontendStack",
    backend_stack=backend_stack,  # Pass the entire backend stack
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

# Add explicit dependency
frontend_stack.add_dependency(backend_stack)

app.synth() 