from aws_cdk import (
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_ecs as ecs,
    Duration,
)
from constructs import Construct
import os

class MonitoringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, backend_service: ecs.FargateService, frontend_service: ecs.FargateService, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create EventBridge rule for DockerHub webhooks
        dockerhub_rule = events.Rule(
            self, "DockerHubWebhookRule",
            event_pattern=events.EventPattern(
                source=["aws.events"],
                detail_type=["DockerHub Webhook"]
            ),
            targets=[
                targets.LambdaFunction(
                    handler=lambda_.Function(
                        self, "DockerHubWebhookHandler",
                        runtime=lambda_.Runtime.PYTHON_3_9,
                        handler="index.handler",
                        code=lambda_.Code.from_inline("""
import json
import boto3
import os

def handler(event, context):
    ecs = boto3.client('ecs')
    
    # Parse the webhook payload
    payload = json.loads(event['detail']['body'])
    
    # Get the repository and tag from the webhook
    repository = payload.get('repository', {}).get('repo_name', '')
    tag = payload.get('push_data', {}).get('tag', '')
    
    # Define which service to update based on the repository
    if 'backend' in repository:
        service_name = os.environ['BACKEND_SERVICE_NAME']
        cluster_name = os.environ['BACKEND_CLUSTER_NAME']
    elif 'frontend' in repository:
        service_name = os.environ['FRONTEND_SERVICE_NAME']
        cluster_name = os.environ['FRONTEND_CLUSTER_NAME']
    else:
        return {
            'statusCode': 400,
            'body': 'Unknown repository'
        }
    
    # Update the ECS service to force a new deployment
    try:
        response = ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            forceNewDeployment=True
        )
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
"""),
                        environment={
                            'BACKEND_SERVICE_NAME': backend_service.service_name,
                            'BACKEND_CLUSTER_NAME': backend_service.cluster.cluster_name,
                            'FRONTEND_SERVICE_NAME': frontend_service.service_name,
                            'FRONTEND_CLUSTER_NAME': frontend_service.cluster.cluster_name,
                        },
                        timeout=Duration.seconds(30),
                        initial_policy=[
                            iam.PolicyStatement(
                                actions=['ecs:UpdateService'],
                                resources=['*']
                            )
                        ]
                    )
                )
            ]
        )