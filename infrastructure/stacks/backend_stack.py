from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_servicediscovery as servicediscovery,
    Duration,
    CfnOutput,
)
from constructs import Construct
import os

class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        self.vpc = ec2.Vpc(self, "MovieRecommendationVPC",
            max_azs=int(os.getenv("VPC_MAX_AZS", "2")),
            nat_gateways=int(os.getenv("VPC_NAT_GATEWAYS", "1"))
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(self, "MovieRecommendationCluster",
            vpc=self.vpc,
            container_insights=True
        )

        # Get Docker image configuration from environment variables
        docker_registry = os.getenv("DOCKER_REGISTRY", "jensonchang/movies")
        backend_tag = os.getenv("BACKEND_IMAGE_TAG", "backend-latest")
        backend_image = f"{docker_registry}:{backend_tag}"

        # Create Fargate Service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "MovieRecommendationBackendService",
            cluster=cluster,
            cpu=int(os.getenv("BACKEND_CPU", "256")),
            memory_limit_mib=int(os.getenv("BACKEND_MEMORY", "512")),
            desired_count=int(os.getenv("DESIRED_COUNT", "2")),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(backend_image),
                container_port=int(os.getenv("BACKEND_PORT", "8000")),
                environment={
                    "AWS_REGION": os.getenv("CDK_DEFAULT_REGION"),
                }
            ),
            public_load_balancer=True,
            assign_public_ip=True,
            health_check_grace_period=Duration.seconds(int(os.getenv("HEALTH_CHECK_GRACE_PERIOD", "60"))),
        )

        # Store the ALB DNS name as a property
        self.backend_alb_dns = fargate_service.load_balancer.load_balancer_dns_name

        # Output the ALB DNS name
        CfnOutput(self, "BackendLoadBalancerDNS",
            value=self.backend_alb_dns,
            description="Backend Load Balancer DNS Name"
        )

        # Add auto scaling
        scaling = fargate_service.service.auto_scale_task_count(
            max_capacity=int(os.getenv("MAX_CAPACITY", "4")),
            min_capacity=int(os.getenv("MIN_CAPACITY", "1"))
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=int(os.getenv("SCALE_THRESHOLD", "70")),
            scale_in_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60"))),
            scale_out_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60")))
        ) 