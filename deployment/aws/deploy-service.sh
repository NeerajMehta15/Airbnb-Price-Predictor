#!/bin/bash
################################################################################
# Deploy/Update ECS Service
# This script forces a new deployment of the ECS service
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="airbnb-price-predictor-cluster"
SERVICE_NAME="airbnb-price-predictor-service"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploy ECS Service${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ AWS credentials configured${NC}"

# Check if cluster exists
echo -e "${YELLOW}Checking if ECS cluster exists...${NC}"
if ! aws ecs describe-clusters \
    --clusters "$CLUSTER_NAME" \
    --region "$AWS_REGION" \
    --query 'clusters[0].status' \
    --output text | grep -q "ACTIVE"; then
    echo -e "${RED}Error: ECS cluster '$CLUSTER_NAME' not found or not active${NC}"
    echo "Run: ./deployment/aws/deploy-infrastructure.sh"
    exit 1
fi

echo -e "${GREEN}✓ Cluster exists and is active${NC}"

# Check if service exists
echo -e "${YELLOW}Checking if ECS service exists...${NC}"
if ! aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$AWS_REGION" \
    --query 'services[0].status' \
    --output text | grep -q "ACTIVE"; then
    echo -e "${RED}Error: ECS service '$SERVICE_NAME' not found or not active${NC}"
    echo "Run: ./deployment/aws/deploy-infrastructure.sh"
    exit 1
fi

echo -e "${GREEN}✓ Service exists and is active${NC}"

# Force new deployment
echo -e "${YELLOW}Forcing new deployment...${NC}"
aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --force-new-deployment \
    --region "$AWS_REGION" \
    > /dev/null

echo -e "${GREEN}✓ New deployment initiated${NC}"

# Wait for service to stabilize
echo -e "${YELLOW}Waiting for service to stabilize (this may take a few minutes)...${NC}"
aws ecs wait services-stable \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$AWS_REGION"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Get service details
echo -e "${YELLOW}Service Status:${NC}"
aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$AWS_REGION" \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
    --output table

# Get ALB endpoint
ALB_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "airbnb-price-predictor-stack" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "Not found")

if [ "$ALB_ENDPOINT" != "Not found" ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}API Endpoint: http://${ALB_ENDPOINT}${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}Test the API:${NC}"
    echo "  curl http://${ALB_ENDPOINT}/health"
    echo "  curl http://${ALB_ENDPOINT}/"
fi

echo -e "${GREEN}========================================${NC}"
