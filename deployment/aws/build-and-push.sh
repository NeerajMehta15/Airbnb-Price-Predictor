#!/bin/bash
################################################################################
# Build and Push Docker Image to AWS ECR
# This script builds the Docker image and pushes it to Amazon ECR
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="airbnb-price-predictor"
AWS_REGION="${AWS_REGION:-us-east-1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build and Push to AWS ECR${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Get AWS account ID
echo -e "${YELLOW}Getting AWS account information...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPOSITORY="${PROJECT_NAME}"
FULL_IMAGE_NAME="${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

echo -e "${GREEN}✓ AWS Account: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${GREEN}✓ ECR Registry: ${ECR_REGISTRY}${NC}"
echo -e "${GREEN}✓ Image: ${FULL_IMAGE_NAME}${NC}"

# Login to ECR
echo -e "${YELLOW}Logging in to Amazon ECR...${NC}"
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ECR_REGISTRY"
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t "$PROJECT_NAME:$IMAGE_TAG" .
echo -e "${GREEN}✓ Image built successfully${NC}"

# Tag image for ECR
echo -e "${YELLOW}Tagging image for ECR...${NC}"
docker tag "$PROJECT_NAME:$IMAGE_TAG" "$FULL_IMAGE_NAME"
docker tag "$PROJECT_NAME:$IMAGE_TAG" "${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"
echo -e "${GREEN}✓ Image tagged${NC}"

# Push image to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push "$FULL_IMAGE_NAME"
docker push "${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"
echo -e "${GREEN}✓ Image pushed successfully${NC}"

# Get image digest
IMAGE_DIGEST=$(aws ecr describe-images \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids imageTag="$IMAGE_TAG" \
    --region "$AWS_REGION" \
    --query 'imageDetails[0].imageDigest' \
    --output text)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build and Push Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Image: ${FULL_IMAGE_NAME}"
echo -e "Digest: ${IMAGE_DIGEST}"
echo -e "${GREEN}========================================${NC}"

# Display next steps
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Deploy to ECS:"
echo "   ./deployment/aws/deploy-service.sh"
echo ""
echo "2. Or trigger GitHub Actions CD workflow to deploy automatically"
echo -e "${GREEN}========================================${NC}"
