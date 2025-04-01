from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_servicediscovery as servicediscovery,
    aws_logs as logs,
    Duration,
    CfnOutput,
)
from constructs import Construct
import os

class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, shared_vpc_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use the shared VPC
        self.vpc = shared_vpc_stack.vpc

        # Create ECS Cluster with container insights disabled for cost savings
        cluster = ecs.Cluster(self, "MovieRecommendationCluster",
            vpc=self.vpc,
            container_insights=False  # Disable container insights for cost savings
        )

        # Create CloudWatch Log Group for ECS tasks
        log_group = logs.LogGroup(self, "BackendLogGroup",
            log_group_name=f"/ecs/{construct_id}",
            retention=logs.RetentionDays.ONE_WEEK  # Reduced retention for cost savings
        )

        # Get Docker image configuration from environment variables
        docker_registry = os.getenv("DOCKER_REGISTRY", "jensonchang/movies")
        backend_tag = os.getenv("BACKEND_IMAGE_TAG", "backend-latest")
        backend_image = f"{docker_registry}:{backend_tag}"

        # Create Fargate Service with cost-optimized settings
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "MovieRecommendationBackendService",
            cluster=cluster,
            cpu=int(os.getenv("BACKEND_CPU", "256")),
            memory_limit_mib=int(os.getenv("BACKEND_MEMORY", "512")),
            desired_count=int(os.getenv("DESIRED_COUNT", "1")),  # Reduced default desired count
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(backend_image),
                container_port=int(os.getenv("BACKEND_PORT", "8000")),
                environment={
                    "AWS_REGION": os.getenv("CDK_DEFAULT_REGION"),
                },
                log_driver=ecs.LogDriver.aws_logs(
                    stream_prefix="backend",
                    log_group=log_group
                )
            ),
            public_load_balancer=True,
            assign_public_ip=True,
            health_check_grace_period=Duration.seconds(int(os.getenv("HEALTH_CHECK_GRACE_PERIOD", "60"))),
            circuit_breaker=ecs.DeploymentCircuitBreaker(
                rollback=True  # Enable automatic rollback on deployment failures
            )
        )

        # Store the ALB DNS name as a property
        self.backend_alb_dns = fargate_service.load_balancer.load_balancer_dns_name

        # Output the ALB DNS name
        CfnOutput(self, "BackendLoadBalancerDNS",
            value=self.backend_alb_dns,
            description="Backend Load Balancer DNS Name"
        )

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