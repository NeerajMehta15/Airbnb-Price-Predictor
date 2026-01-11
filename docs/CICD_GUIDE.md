# CI/CD Pipeline Guide - Airbnb Price Predictor

## 🎯 Overview

This guide explains the complete CI/CD (Continuous Integration/Continuous Deployment) pipeline for the Airbnb Price Predictor ML application. This pipeline automates the process from code commit to production deployment on AWS.

## 📚 Table of Contents

1. [CI/CD Architecture](#cicd-architecture)
2. [CI Pipeline - Continuous Integration](#ci-pipeline)
3. [CD Pipeline - Continuous Deployment](#cd-pipeline)
4. [AWS Infrastructure](#aws-infrastructure)
5. [Setup Instructions](#setup-instructions)
6. [Deployment Workflow](#deployment-workflow)
7. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
8. [Best Practices](#best-practices)

---

## 🏗️ CI/CD Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DEVELOPER                                │
│                             ↓                                    │
│                    Git Push to GitHub                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   CONTINUOUS INTEGRATION (CI)                    │
├─────────────────────────────────────────────────────────────────┤
│  1. Code Quality Check (Black, Flake8, isort)                  │
│  2. Unit Tests (pytest on multiple Python versions)             │
│  3. Security Scanning (Safety, Bandit)                          │
│  4. Docker Image Build                                          │
│  5. Integration Tests (docker-compose)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  CONTINUOUS DEPLOYMENT (CD)                      │
├─────────────────────────────────────────────────────────────────┤
│  1. Build Docker Image                                          │
│  2. Push to Amazon ECR                                          │
│  3. Update ECS Task Definition                                  │
│  4. Deploy to ECS Fargate                                       │
│  5. Health Check                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AWS PRODUCTION ENVIRONMENT                    │
├─────────────────────────────────────────────────────────────────┤
│  • Application Load Balancer (ALB)                              │
│  • ECS Fargate Cluster                                          │
│  • ECR Container Registry                                       │
│  • CloudWatch Logs & Monitoring                                 │
│  • S3 for Model Storage                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 CI Pipeline - Continuous Integration

### Purpose
The CI pipeline ensures code quality, runs automated tests, and validates that the application can be built successfully before deployment.

### Workflow File
`.github/workflows/ci.yml`

### Pipeline Stages

#### 1. **Code Quality & Linting**
- **Tools**: Black, Flake8, isort
- **Purpose**: Enforce code style and catch common errors
- **Impact**: Maintains consistent code quality across the team

```yaml
# Checks:
- Black: Code formatting (PEP 8 compliance)
- isort: Import statement organization
- Flake8: Linting for Python best practices
```

**Learning Point**: Code quality checks prevent bugs and make code easier to maintain. They run BEFORE tests to fail fast on obvious issues.

#### 2. **Unit Tests**
- **Tool**: pytest
- **Versions**: Python 3.9, 3.10, 3.11
- **Purpose**: Verify individual components work correctly
- **Impact**: Catches bugs early in development

```yaml
# Tests run on multiple Python versions to ensure compatibility
Strategy Matrix:
  - Python 3.9
  - Python 3.10
  - Python 3.11
```

**Learning Point**: Testing on multiple versions ensures your code works across different environments. This is crucial for libraries and production applications.

#### 3. **Security Scanning**
- **Tools**: Safety (dependency vulnerabilities), Bandit (code security)
- **Purpose**: Identify security vulnerabilities
- **Impact**: Prevents deployment of insecure code

```yaml
# Security checks:
- Safety: Scans dependencies for known vulnerabilities
- Bandit: Analyzes code for security issues
```

**Learning Point**: Security scanning is essential for production systems. It finds vulnerabilities BEFORE they reach production.

#### 4. **Docker Build**
- **Tool**: Docker Buildx
- **Purpose**: Ensure the application can be containerized
- **Impact**: Validates Docker configuration

```yaml
# Build verification:
- Multi-stage Docker build
- Layer caching for faster builds
- Image size optimization
```

**Learning Point**: Building Docker images in CI ensures the Dockerfile works correctly and catches configuration issues early.

#### 5. **Integration Tests**
- **Tool**: docker-compose
- **Purpose**: Test the entire application stack
- **Impact**: Validates API endpoints work correctly

```yaml
# Integration testing:
- Start services with docker-compose
- Health check API endpoints
- Verify container networking
```

**Learning Point**: Integration tests verify that all components work together correctly, not just in isolation.

### CI Pipeline Triggers

```yaml
on:
  push:
    branches: [ main, develop, 'claude/**' ]
  pull_request:
    branches: [ main, develop ]
```

**Impact**:
- Every push and PR triggers the CI pipeline
- Provides immediate feedback on code changes
- Prevents broken code from reaching main branch

---

## 🚀 CD Pipeline - Continuous Deployment

### Purpose
The CD pipeline automatically deploys validated code to AWS production environment.

### Workflow File
`.github/workflows/cd.yml`

### Pipeline Stages

#### 1. **Build & Push to ECR**
```yaml
Steps:
  1. Configure AWS credentials
  2. Login to Amazon ECR
  3. Build Docker image
  4. Tag image with commit SHA
  5. Push to ECR repository
  6. Scan image for vulnerabilities
```

**Learning Point**: ECR (Elastic Container Registry) is AWS's Docker registry. Images are tagged with commit SHA for traceability.

**Impact**:
- Every deployment is traceable to a specific code commit
- Automated image scanning finds vulnerabilities
- Immutable image tags prevent deployment confusion

#### 2. **Deploy to ECS**
```yaml
Steps:
  1. Download current task definition
  2. Update task definition with new image
  3. Deploy new task definition
  4. Wait for service stability
  5. Verify deployment
```

**Learning Point**: ECS (Elastic Container Service) manages containerized applications. Task definitions describe how to run containers.

**Impact**:
- Zero-downtime deployments (rolling updates)
- Automatic rollback on failure
- Service stability checks ensure successful deployment

#### 3. **Health Check**
```yaml
Steps:
  1. Get service endpoint
  2. Test /health endpoint
  3. Verify API responds correctly
```

**Learning Point**: Health checks validate that the deployed application is actually working, not just that deployment succeeded.

**Impact**:
- Catches deployment issues immediately
- Provides confidence that users can access the service
- Enables automated rollback decisions

### CD Pipeline Triggers

```yaml
on:
  push:
    branches: [ main ]
  workflow_dispatch:  # Manual trigger
```

**Impact**:
- Only main branch pushes trigger deployment (production safety)
- Manual trigger allows controlled deployments
- Separates code validation (CI) from deployment (CD)

---

## ☁️ AWS Infrastructure

### Infrastructure as Code
We use AWS CloudFormation to define all infrastructure as code.

**File**: `deployment/aws/cloudformation-infrastructure.yaml`

### Components

#### 1. **Networking (VPC)**
```
- VPC with CIDR 10.0.0.0/16
- 2 Public Subnets (Multi-AZ for high availability)
- Internet Gateway
- Route Tables
```

**Learning Point**: Multi-AZ deployment ensures high availability. If one availability zone fails, the other continues serving traffic.

#### 2. **Load Balancing (ALB)**
```
- Application Load Balancer
- Target Group with health checks
- HTTP listener on port 80
```

**Learning Point**: ALB distributes traffic across multiple containers and performs health checks to route traffic only to healthy instances.

#### 3. **Container Orchestration (ECS)**
```
- ECS Cluster with Fargate
- Task Definition (CPU: 512, Memory: 1024)
- ECS Service (Desired count: 2)
```

**Learning Point**: Fargate is serverless compute for containers - no EC2 management needed. ECS handles scaling, health checks, and deployments.

#### 4. **Container Registry (ECR)**
```
- Private Docker repository
- Image scanning on push
- Lifecycle policy (keep last 10 images)
```

**Learning Point**: ECR integrates seamlessly with ECS and provides security scanning and image management.

#### 5. **Storage (S3)**
```
- S3 bucket for ML models
- Versioning enabled
- Private access only
```

**Learning Point**: S3 provides scalable storage for ML models, with versioning to track model changes over time.

#### 6. **Monitoring (CloudWatch)**
```
- Log groups for ECS tasks
- Container insights
- 7-day log retention
```

**Learning Point**: CloudWatch centralizes logs from all containers, making debugging and monitoring easier.

### Infrastructure Deployment

```bash
# Deploy infrastructure
./deployment/aws/deploy-infrastructure.sh

# This creates:
# ✓ VPC and networking
# ✓ Load balancer
# ✓ ECS cluster
# ✓ ECR repository
# ✓ S3 bucket
# ✓ IAM roles
# ✓ Security groups
```

---

## 🛠️ Setup Instructions

### Prerequisites

1. **AWS Account**
   - Active AWS account
   - AWS CLI installed and configured
   - Appropriate IAM permissions

2. **GitHub Repository**
   - Repository with code
   - GitHub Actions enabled

3. **Local Development**
   - Docker installed
   - Python 3.10+
   - Git

### Step 1: Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (us-east-1)
# - Default output format (json)
```

### Step 2: Deploy AWS Infrastructure

```bash
# Clone repository
git clone https://github.com/NeerajMehta15/Airbnb-Price-Predictor.git
cd Airbnb-Price-Predictor

# Deploy infrastructure
./deployment/aws/deploy-infrastructure.sh

# Wait for completion (~10 minutes)
# Note the outputs, especially ALB DNS name
```

### Step 3: Configure GitHub Secrets

Add these secrets to your GitHub repository:

```
Settings → Secrets and variables → Actions → New repository secret
```

Required secrets:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### Step 4: Build and Push Initial Image

```bash
# Build and push Docker image to ECR
./deployment/aws/build-and-push.sh

# This creates the first image in ECR
```

### Step 5: Deploy Application

```bash
# Deploy to ECS
./deployment/aws/deploy-service.sh

# Wait for service to stabilize
```

### Step 6: Test the Deployment

```bash
# Get ALB endpoint
ALB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name airbnb-price-predictor-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ALBEndpoint`].OutputValue' \
  --output text)

# Test health endpoint
curl http://$ALB_ENDPOINT/health

# Test API documentation
curl http://$ALB_ENDPOINT/docs
```

---

## 🔄 Deployment Workflow

### Typical Development Workflow

```
1. Developer writes code
   ↓
2. Create feature branch
   git checkout -b feature/my-feature
   ↓
3. Make changes and commit
   git add .
   git commit -m "Add feature"
   ↓
4. Push to GitHub
   git push origin feature/my-feature
   ↓
5. CI Pipeline runs automatically
   - Code quality checks
   - Unit tests
   - Security scans
   - Docker build
   ↓
6. Create Pull Request
   ↓
7. Code review
   ↓
8. Merge to main
   ↓
9. CD Pipeline runs automatically
   - Build Docker image
   - Push to ECR
   - Deploy to ECS
   - Health check
   ↓
10. Application live in production!
```

### What Happens on Each Git Push

#### Push to Feature Branch
```
✓ Code quality checks
✓ Unit tests run
✓ Security scanning
✓ Docker build validation
✗ NO deployment (safe for development)
```

#### Push to Main Branch
```
✓ Full CI pipeline
✓ Build Docker image
✓ Push to ECR
✓ Deploy to ECS
✓ Health checks
✓ Application updated in production
```

---

## 📊 Monitoring and Troubleshooting

### Viewing CI/CD Pipeline Status

1. **GitHub Actions Tab**
   ```
   Repository → Actions → View workflow runs
   ```

2. **Check Pipeline Status**
   - Green checkmark: Success
   - Red X: Failure
   - Yellow dot: In progress

### Viewing Application Logs

```bash
# View ECS service logs
aws logs tail /ecs/airbnb-price-predictor --follow

# View specific task logs
aws ecs list-tasks --cluster airbnb-price-predictor-cluster
aws logs get-log-events --log-group-name /ecs/airbnb-price-predictor --log-stream-name <stream-name>
```

### Common Issues and Solutions

#### Issue: CI Pipeline Fails on Tests
```
Solution:
1. Check test output in GitHub Actions
2. Run tests locally: pytest tests/
3. Fix failing tests
4. Commit and push again
```

#### Issue: Docker Build Fails
```
Solution:
1. Check Dockerfile syntax
2. Test build locally: docker build -t test .
3. Verify all files are present
4. Check .dockerignore isn't excluding needed files
```

#### Issue: ECS Deployment Fails
```
Solution:
1. Check ECS service events:
   aws ecs describe-services --cluster <cluster> --services <service>
2. Check task stopped reason:
   aws ecs describe-tasks --cluster <cluster> --tasks <task-arn>
3. Check CloudWatch logs for errors
4. Verify task definition is correct
```

#### Issue: Health Check Fails
```
Solution:
1. Check if containers are running:
   aws ecs list-tasks --cluster <cluster> --service-name <service>
2. Test health endpoint directly:
   curl http://<alb-endpoint>/health
3. Check CloudWatch logs for startup errors
4. Verify security group allows traffic on port 8000
```

### AWS Console Monitoring

1. **ECS Dashboard**
   - View cluster status
   - Check service health
   - Monitor task count
   - View deployments

2. **CloudWatch Dashboard**
   - View logs
   - Set up alarms
   - Monitor metrics
   - Track errors

3. **ECR Repository**
   - View images
   - Check vulnerability scans
   - Manage image lifecycle

---

## ✅ Best Practices

### CI/CD Best Practices

1. **Keep Pipelines Fast**
   - Use caching for dependencies
   - Run tests in parallel
   - Optimize Docker builds
   - Target: CI < 10 minutes

2. **Fail Fast**
   - Run quick checks first (linting)
   - Stop pipeline on first failure
   - Provide clear error messages

3. **Security First**
   - Scan dependencies regularly
   - Never commit secrets
   - Use AWS Secrets Manager
   - Rotate credentials regularly

4. **Monitoring**
   - Set up CloudWatch alarms
   - Monitor deployment success rate
   - Track application metrics
   - Review logs regularly

5. **Testing**
   - Write tests for all new code
   - Maintain >80% code coverage
   - Include integration tests
   - Test failure scenarios

### Infrastructure Best Practices

1. **High Availability**
   - Multi-AZ deployment
   - Minimum 2 tasks running
   - Health checks configured
   - Auto-scaling enabled

2. **Security**
   - Private subnets for data
   - Security groups properly configured
   - IAM roles with least privilege
   - Encryption at rest and in transit

3. **Cost Optimization**
   - Use Fargate Spot for development
   - Clean up old ECR images
   - Right-size container resources
   - Monitor AWS costs

4. **Documentation**
   - Document infrastructure changes
   - Keep README updated
   - Document deployment procedures
   - Maintain runbooks

---

## 🎓 Learning Outcomes

After implementing this CI/CD pipeline, you've learned:

### CI/CD Concepts
✅ Continuous Integration principles
✅ Continuous Deployment automation
✅ Pipeline stages and dependencies
✅ Automated testing strategies
✅ Security scanning integration

### AWS Services
✅ ECS (Elastic Container Service)
✅ ECR (Elastic Container Registry)
✅ ALB (Application Load Balancer)
✅ CloudFormation (Infrastructure as Code)
✅ IAM (Identity and Access Management)
✅ CloudWatch (Logging and Monitoring)

### DevOps Practices
✅ Infrastructure as Code
✅ Containerization with Docker
✅ GitOps workflow
✅ Automated testing
✅ Monitoring and alerting

### Best Practices
✅ Code quality enforcement
✅ Security scanning
✅ High availability architecture
✅ Zero-downtime deployments
✅ Rollback strategies

---

## 📚 Additional Resources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Tutorials
- [AWS ECS Tutorial](https://aws.amazon.com/ecs/getting-started/)
- [CI/CD with GitHub Actions](https://github.com/skills/continuous-integration)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Create a pull request
6. CI pipeline will run automatically
7. Address any feedback
8. Merge when approved

---

## 📝 Conclusion

This CI/CD pipeline provides a complete, production-ready deployment system for ML applications. It automates everything from code validation to production deployment, ensuring high quality and reliability.

The pipeline demonstrates industry best practices for:
- Automated testing
- Security scanning
- Infrastructure as Code
- Containerized deployments
- Monitoring and observability

Use this as a foundation for your own ML projects and continue learning by experimenting with additional features like:
- Blue/green deployments
- Canary releases
- A/B testing infrastructure
- Model versioning and serving
- Real-time monitoring dashboards
