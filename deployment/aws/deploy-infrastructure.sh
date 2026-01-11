#!/bin/bash
################################################################################
# AWS Infrastructure Deployment Script
# This script deploys the CloudFormation stack for Airbnb Price Predictor
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="airbnb-price-predictor-stack"
TEMPLATE_FILE="deployment/aws/cloudformation-infrastructure.yaml"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AWS Infrastructure Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${GREEN}✓ AWS Region: ${AWS_REGION}${NC}"

# Check if stack exists
echo -e "${YELLOW}Checking if stack exists...${NC}"
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo -e "${YELLOW}Stack exists. Updating...${NC}"
    OPERATION="update-stack"
else
    echo -e "${YELLOW}Stack does not exist. Creating...${NC}"
    OPERATION="create-stack"
fi

# Deploy stack
echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"
aws cloudformation "$OPERATION" \
    --stack-name "$STACK_NAME" \
    --template-body "file://$TEMPLATE_FILE" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION" \
    --parameters \
        ParameterKey=ProjectName,ParameterValue=airbnb-price-predictor \
        ParameterKey=Environment,ParameterValue=production \
    || {
        if [ "$OPERATION" == "update-stack" ]; then
            echo -e "${YELLOW}No updates to perform${NC}"
        else
            echo -e "${RED}Deployment failed${NC}"
            exit 1
        fi
    }

# Wait for stack operation to complete
if [ "$OPERATION" == "create-stack" ]; then
    echo -e "${YELLOW}Waiting for stack creation to complete...${NC}"
    aws cloudformation wait stack-create-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
else
    echo -e "${YELLOW}Waiting for stack update to complete...${NC}"
    aws cloudformation wait stack-update-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" 2>/dev/null || true
fi

# Get stack outputs
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "${YELLOW}Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Save outputs to file
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output json > deployment/aws/stack-outputs.json

echo -e "${GREEN}✓ Outputs saved to deployment/aws/stack-outputs.json${NC}"

# Display next steps
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${GREEN}========================================${NC}"
echo "1. Build and push Docker image to ECR:"
echo "   ./deployment/aws/build-and-push.sh"
echo ""
echo "2. Update ECS service to deploy new image:"
echo "   ./deployment/aws/deploy-service.sh"
echo ""
echo "3. Test the API endpoint:"
echo "   ALB_ENDPOINT=\$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==\`ALBEndpoint\`].OutputValue' --output text)"
echo "   curl http://\$ALB_ENDPOINT/health"
echo -e "${GREEN}========================================${NC}"
