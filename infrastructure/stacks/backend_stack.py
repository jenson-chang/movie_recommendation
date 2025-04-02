from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_servicediscovery as servicediscovery,
    aws_logs as logs,
    Duration,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct
import os

class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, shared_vpc_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use the shared VPC
        self.vpc = shared_vpc_stack.vpc

        # Create security group for the ALB and Fargate tasks
        service_sg = ec2.SecurityGroup(self, "BackendServiceSecurityGroup",
            vpc=self.vpc,
            description="Security group for backend service",
            allow_all_outbound=True
        )
        
        # Allow inbound HTTP traffic from anywhere
        service_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80)
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(self, "MovieRecommendationCluster",
            vpc=self.vpc
        )

        # Create CloudWatch Log Group for ECS tasks with unique name
        log_group = logs.LogGroup(self, "BackendLogGroup",
            log_group_name=f"/ecs/{construct_id}-{self.account}-{self.region}",
            retention=logs.RetentionDays.ONE_WEEK,  # Reduced retention for cost savings
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
            ),
            security_groups=[service_sg],  # Use the shared security group
            load_balancer_name="movie-backend-alb"  # Shortened name for the ALB
        )

        # Add security group to the ALB
        fargate_service.load_balancer.add_security_group(service_sg)

        # Add removal policy to the load balancer
        fargate_service.load_balancer.apply_removal_policy(RemovalPolicy.DESTROY)

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