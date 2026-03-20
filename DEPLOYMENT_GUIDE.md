# Cloud Deployment Guide — AWS

This guide covers deploying the Prime Number Generator API on AWS using ECS Fargate, RDS PostgreSQL, and AWS Client VPN.

---

## Architecture Overview

### AWS Cloud Architecture

![AWS Cloud Architecture](diagrams/architecture.png)

### Local Docker Architecture

![Local Docker Architecture](diagrams/local_architecture.png)

**Key security principles:**
- ECS and RDS are in **private subnets** — no public internet access
- API is accessible **only through VPN**
- Database accepts connections **only from the app security group**
- All credentials are passed via environment variables, never hardcoded
- RDS storage is encrypted at rest

---

## Prerequisites

- AWS CLI installed and configured (`aws configure`)
- Terraform >= 1.5.0
- Docker installed
- Valid AWS account with permissions for: VPC, ECS, ECR, RDS, Client VPN, IAM, CloudWatch

---

## Step 1: Configure Variables

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your credentials:
```hcl
aws_region      = "eu-central-1"
project_name    = "prime-api"
db_username     = "your_db_user"
db_password     = "your_secure_password"
db_name         = "your_db_name"
```

> **Important:** Never commit `terraform.tfvars` — it contains sensitive values.

---

## Step 2: Generate VPN Certificates

AWS Client VPN uses mutual TLS authentication. Generate the certificates:

```bash
# Clone the easy-rsa tool
git clone https://github.com/OpenVPN/easy-rsa.git /tmp/easy-rsa
cd /tmp/easy-rsa/easyrsa3

# Initialize PKI
./easyrsa init-pki
./easyrsa build-ca nopass

# Generate server certificate
./easyrsa build-server-full server nopass

# Generate client certificate
./easyrsa build-client-full client1 nopass
```

Upload certificates to AWS ACM:

```bash
aws acm import-certificate \
  --certificate fileb://pki/issued/server.crt \
  --private-key fileb://pki/private/server.key \
  --certificate-chain fileb://pki/ca.crt \
  --region eu-central-1

aws acm import-certificate \
  --certificate fileb://pki/issued/client1.crt \
  --private-key fileb://pki/private/client1.key \
  --certificate-chain fileb://pki/ca.crt \
  --region eu-central-1
```

Note the ARN values returned — you will need them for the Terraform config.

---

## Step 3: Deploy Infrastructure

```bash
cd deploy/terraform

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Save the outputs:
```bash
terraform output
```

---

## Step 4: Build and Push Docker Image

```bash
# Get ECR login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com

# Build the image
docker build -t prime-api .

# Tag for ECR
docker tag prime-api:latest <ECR_REPOSITORY_URL>:latest

# Push
docker push <ECR_REPOSITORY_URL>:latest
```

Replace `<ECR_REPOSITORY_URL>` with the value from `terraform output ecr_repository_url`.

---

## Step 5: Deploy ECS Service

After pushing the image, force a new deployment:

```bash
aws ecs update-service \
  --cluster prime-api-cluster \
  --service prime-api-service \
  --force-new-deployment \
  --region eu-central-1
```

Verify the service is running:

```bash
aws ecs describe-services \
  --cluster prime-api-cluster \
  --services prime-api-service \
  --region eu-central-1 \
  --query 'services[0].{status:status,running:runningCount,desired:desiredCount}'
```

---

## Step 6: Connect via VPN

Download the Client VPN configuration:

```bash
aws ec2 export-client-vpn-client-configuration \
  --client-vpn-endpoint-id <VPN_ENDPOINT_ID> \
  --output text > vpn-client-config.ovpn
```

Append the client certificate and key to the `.ovpn` file:

```bash
echo "<cert>" >> vpn-client-config.ovpn
cat /tmp/easy-rsa/easyrsa3/pki/issued/client1.crt >> vpn-client-config.ovpn
echo "</cert>" >> vpn-client-config.ovpn
echo "<key>" >> vpn-client-config.ovpn
cat /tmp/easy-rsa/easyrsa3/pki/private/client1.key >> vpn-client-config.ovpn
echo "</key>" >> vpn-client-config.ovpn
```

Connect using any OpenVPN client:

```bash
sudo openvpn --config vpn-client-config.ovpn
```

---

## Step 7: Test the API

Once connected to the VPN:

```bash
# Health check
curl http://<ECS_PRIVATE_IP>:8000/api/v1/health

# Generate primes
curl -X POST http://<ECS_PRIVATE_IP>:8000/api/v1/primes \
  -H "Content-Type: application/json" \
  -d '{"start": 1, "end": 100}'

# View history
curl http://<ECS_PRIVATE_IP>:8000/api/v1/primes/history
```

---

## IAM Access Control

### Roles and Permissions

| Role | Purpose | Permissions |
|------|---------|-------------|
| ECS Task Execution Role | Allows ECS to pull images and write logs | `AmazonECSTaskExecutionRolePolicy` |
| Developer | Deploy updates, view logs | `ecr:PushImage`, `ecs:UpdateService`, `logs:GetLogEvents` |
| Admin | Full infrastructure management | Full access to VPC, ECS, RDS, VPN, IAM |
| Read-Only | View resources and logs | `ecs:Describe*`, `rds:Describe*`, `logs:Get*` |

### Creating a Developer User

```bash
# Create IAM group
aws iam create-group --group-name prime-api-developers

# Attach deployment policy
aws iam put-group-policy \
  --group-name prime-api-developers \
  --policy-name deploy-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "logs:GetLogEvents",
          "logs:DescribeLogStreams"
        ],
        "Resource": "*"
      }
    ]
  }'

# Add user to group
aws iam add-user-to-group \
  --group-name prime-api-developers \
  --user-name <USERNAME>
```

---

## Cleanup

To destroy all resources:

```bash
cd deploy/terraform
terraform destroy
```

> **Warning:** This will delete the RDS database and all data. Create a snapshot first if needed.
