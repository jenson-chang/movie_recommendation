from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    aws_secretsmanager as secretsmanager,
    Duration,
    CfnOutput,
)
from constructs import Construct
import os

class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, backend_alb_dns: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC (reuse the same VPC as backend if needed)
        vpc = ec2.Vpc(self, "MovieRecommendationFrontendVPC",
            max_azs=int(os.getenv("VPC_MAX_AZS", "2")),
            nat_gateways=int(os.getenv("VPC_NAT_GATEWAYS", "1"))
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(self, "MovieRecommendationFrontendCluster",
            vpc=vpc,
            container_insights=True
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

        # Create Fargate Service
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "MovieRecommendationFrontendService",
            cluster=cluster,
            cpu=int(os.getenv("FRONTEND_CPU", "256")),
            memory_limit_mib=int(os.getenv("FRONTEND_MEMORY", "512")),
            desired_count=int(os.getenv("DESIRED_COUNT", "2")),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(frontend_image),
                container_port=int(os.getenv("FRONTEND_PORT", "8501")),
                environment={
                    "AWS_REGION": os.getenv("CDK_DEFAULT_REGION"),
                    "REACT_APP_API_URL": f"http://{backend_alb_dns}",  # Use backend ALB DNS name
                },
                secrets={
                    "TMDB_API_KEY": ecs.Secret.from_secrets_manager(tmdb_secret, field="TMDB_API_KEY")
                }
            ),
            public_load_balancer=True,  # Make the ALB public-facing
            assign_public_ip=True,  # Allow tasks to have public IPs
            health_check_grace_period=Duration.seconds(int(os.getenv("HEALTH_CHECK_GRACE_PERIOD", "60"))),
        )

        # Grant the task role permission to access the secret
        tmdb_secret.grant_read(self.fargate_service.task_definition.task_role)

        # Add auto scaling
        scaling = self.fargate_service.service.auto_scale_task_count(
            max_capacity=int(os.getenv("MAX_CAPACITY", "4")),
            min_capacity=int(os.getenv("MIN_CAPACITY", "1"))
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=int(os.getenv("SCALE_THRESHOLD", "70")),
            scale_in_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60"))),
            scale_out_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60")))
        )

        # Add memory-based scaling
        scaling.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=int(os.getenv("SCALE_THRESHOLD", "70")),
            scale_in_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60"))),
            scale_out_cooldown=Duration.seconds(int(os.getenv("SCALE_COOLDOWN", "60")))
        )

        # Output the ALB DNS name
        CfnOutput(self, "FrontendLoadBalancerDNS",
            value=self.fargate_service.load_balancer.load_balancer_dns_name,
            description="Frontend Load Balancer DNS Name"
        )