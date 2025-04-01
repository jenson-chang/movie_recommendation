from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    Duration,
    CfnOutput,
)
from constructs import Construct
import os

class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, backend_stack: Stack, shared_vpc_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the backend ALB DNS name from the backend stack
        backend_alb_dns = backend_stack.backend_alb_dns

        # Use the shared VPC
        vpc = shared_vpc_stack.vpc

        # Create ECS Cluster with container insights disabled for cost savings
        cluster = ecs.Cluster(self, "MovieRecommendationFrontendCluster",
            vpc=vpc,
            container_insights=False  # Disable container insights for cost savings
        )

        # Create CloudWatch Log Group for ECS tasks
        log_group = logs.LogGroup(self, "FrontendLogGroup",
            log_group_name=f"/ecs/{construct_id}",
            retention=logs.RetentionDays.ONE_WEEK  # Reduced retention for cost savings
        )

        # Create Secrets Manager secret for TMDB API key
        tmdb_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "TMDBAPISecret",
            secret_name="movie-recommendation/tmdb-api-key"
        )

        # Get Docker image configuration from environment variables
        docker_registry = os.getenv("DOCKER_REGISTRY", "jensonchang/movies")
        frontend_tag = os.getenv("FRONTEND_IMAGE_TAG", "frontend-latest")
        frontend_image = f"{docker_registry}:{frontend_tag}"

        # Create Fargate Service with cost-optimized settings
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "MovieRecommendationFrontendService",
            cluster=cluster,
            cpu=int(os.getenv("FRONTEND_CPU", "256")),
            memory_limit_mib=int(os.getenv("FRONTEND_MEMORY", "512")),
            desired_count=int(os.getenv("DESIRED_COUNT", "1")),  # Reduced default desired count
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(frontend_image),
                container_port=int(os.getenv("FRONTEND_PORT", "8501")),
                environment={
                    "AWS_REGION": os.getenv("CDK_DEFAULT_REGION"),
                    "REACT_APP_API_URL": f"http://{backend_alb_dns}",  # Use backend ALB DNS name
                },
                secrets={
                    "TMDB_API_KEY": ecs.Secret.from_secrets_manager(tmdb_secret, field="TMDB_API_KEY")
                },
                log_driver=ecs.LogDriver.aws_logs(
                    stream_prefix="frontend",
                    log_group=log_group
                )
            ),
            public_load_balancer=True,  # Make the ALB public-facing
            assign_public_ip=True,  # Allow tasks to have public IPs
            health_check_grace_period=Duration.seconds(int(os.getenv("HEALTH_CHECK_GRACE_PERIOD", "60"))),
            circuit_breaker=ecs.DeploymentCircuitBreaker(
                rollback=True  # Enable automatic rollback on deployment failures
            )
        )

        # Grant the task role permission to access the secret
        tmdb_secret.grant_read(fargate_service.task_definition.task_role)

        # Add auto scaling with conservative settings
        scaling = fargate_service.service.auto_scale_task_count(
            max_capacity=int(os.getenv("MAX_CAPACITY", "2")),  # Reduced max capacity
            min_capacity=int(os.getenv("MIN_CAPACITY", "1"))
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=int(os.getenv("SCALE_THRESHOLD", "80")),  # Increased threshold
            scale_in_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "300"))),  # Increased cooldown
            scale_out_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60")))
        )

        # Add memory-based scaling with conservative settings
        scaling.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=int(os.getenv("SCALE_THRESHOLD", "80")),  # Increased threshold
            scale_in_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "300"))),  # Increased cooldown
            scale_out_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60")))
        )

        # Output the ALB DNS name
        CfnOutput(self, "FrontendLoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name,
            description="Frontend Load Balancer DNS Name"
        ) 