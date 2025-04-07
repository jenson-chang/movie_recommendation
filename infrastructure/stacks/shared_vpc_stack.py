from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
import os

class SharedVPCStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a shared VPC for all portfolio apps
        self.vpc = ec2.Vpc(self, "SharedVPC",
            max_azs=2,
            nat_gateways=0,  # Disable NAT Gateways as we'll use a NAT instance
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ],
            gateway_endpoints={
                "S3": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.S3
                ),
                "DynamoDB": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
                )
            }
        )

        # Create interface endpoints with optimized AZ configuration
        ec2.InterfaceVpcEndpoint(self, "ECREndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.ECR,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                availability_zones=[self.vpc.availability_zones[0]]  # Use only first AZ
            )
        )

        # Only create Secrets Manager endpoint if needed
        if os.getenv("USE_SECRETS_MANAGER", "true").lower() == "true":
            ec2.InterfaceVpcEndpoint(self, "SecretsManagerEndpoint",
                vpc=self.vpc,
                service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
                private_dns_enabled=True,
                subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    availability_zones=[self.vpc.availability_zones[0]]  # Use only first AZ
                )
            )

        # Only create CloudWatch Logs endpoint if needed
        if os.getenv("USE_CLOUDWATCH_LOGS", "true").lower() == "true":
            ec2.InterfaceVpcEndpoint(self, "CloudWatchLogsEndpoint",
                vpc=self.vpc,
                service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
                private_dns_enabled=True,
                subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    availability_zones=[self.vpc.availability_zones[0]]  # Use only first AZ
                )
            )

        # Create a security group for the NAT instance
        nat_sg = ec2.SecurityGroup(self, "NATInstanceSecurityGroup",
            vpc=self.vpc,
            description="Security group for NAT instance",
            allow_all_outbound=True
        )

        # Allow inbound traffic from private subnets
        nat_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.all_traffic()
        )

        # Create the NAT instance in the first AZ
        nat_instance = ec2.Instance(self, "NATInstance",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
                availability_zones=[self.vpc.availability_zones[0]]  # Use first AZ only
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.NANO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            security_group=nat_sg,
            source_dest_check=False,  # Required for NAT instance
            require_imdsv2=True,  # Use IMDSv2 for better security
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=8,  # Minimum size for cost savings
                        volume_type=ec2.EbsDeviceVolumeType.GP3
                    )
                )
            ]
        )

        # Add user data to configure NAT
        nat_instance.user_data.add_commands(
            "yum update -y",
            "yum install -y iptables-services",
            "systemctl enable iptables",
            "systemctl start iptables",
            "iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
            "iptables-save > /etc/sysconfig/iptables"
        )

        # Create route tables for private subnets to route through NAT instance
        for i, subnet in enumerate(self.vpc.private_subnets):
            route_table = subnet.node.find_child("RouteTable")
            ec2.CfnRoute(self, f"PrivateSubnetRoute{i}",
                route_table_id=route_table.ref,
                destination_cidr_block="0.0.0.0/0",
                instance_id=nat_instance.instance_id
            )

        # Output the VPC ID and NAT instance ID
        CfnOutput(self, "SharedVPCId",
            value=self.vpc.vpc_id,
            description="Shared VPC ID"
        )
        CfnOutput(self, "NATInstanceId",
            value=nat_instance.instance_id,
            description="NAT Instance ID"
        ) 