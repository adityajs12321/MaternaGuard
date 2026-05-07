#!/usr/bin/env bash
# Build and deploy the MaternaGuard ML Lambda function using Docker container image.
#
# Prerequisites:
#   1. AWS CLI v2 installed and configured (aws configure)
#   2. Docker installed and running
#   3. ECR repository created:
#      aws ecr create-repository --repository-name maternaguard-ml --region us-east-1
#
# Usage:
#   chmod +x deploy_lambda.sh
#   ./deploy_lambda.sh

set -euo pipefail

# -----------------------------------------------------------------------
# Configuration — update these for your AWS account
# -----------------------------------------------------------------------
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID env var}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO_NAME="maternaguard-ml"
LAMBDA_FUNCTION_NAME="maternaguard-predict"
IMAGE_TAG="latest"

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
FULL_IMAGE="${ECR_URI}:${IMAGE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAMBDA_DIR="${SCRIPT_DIR}/lambda_ml"
MODELS_DIR="${SCRIPT_DIR}/ml_new/models"

echo "=== MaternaGuard ML Lambda Deploy ==="

# 1. Copy model artifacts into the Lambda build context
echo "[1/5] Copying model artifacts..."
mkdir -p "${LAMBDA_DIR}/models"
cp "${MODELS_DIR}/model_rf_v1.pkl" "${LAMBDA_DIR}/models/"
cp "${MODELS_DIR}/model_svm.pkl" "${LAMBDA_DIR}/models/"
cp "${MODELS_DIR}/model_xgb.pkl" "${LAMBDA_DIR}/models/"
cp "${MODELS_DIR}/model_ann.keras" "${LAMBDA_DIR}/models/"
cp "${MODELS_DIR}/scaler.pkl" "${LAMBDA_DIR}/models/"
# GBT is optional
cp "${MODELS_DIR}/model_gbt.pkl" "${LAMBDA_DIR}/models/" 2>/dev/null || true

# 2. Build Docker image
echo "[2/5] Building Docker image (native arm64 for Apple Silicon)..."
docker build --platform linux/arm64 --provenance=false -t "${ECR_REPO_NAME}:${IMAGE_TAG}" "${LAMBDA_DIR}"

# 3. Login to ECR
echo "[3/5] Logging into ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# 4. Tag and push
echo "[4/5] Pushing image to ECR..."
docker tag "${ECR_REPO_NAME}:${IMAGE_TAG}" "${FULL_IMAGE}"
docker push "${FULL_IMAGE}"

# 5. Update Lambda function code and architecture
echo "[5/5] Updating Lambda function..."
aws lambda update-function-configuration \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --architectures arm64 \
  --region "${AWS_REGION}" > /dev/null 2>&1 || true

aws lambda update-function-code \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --image-uri "${FULL_IMAGE}" \
  --region "${AWS_REGION}"

echo ""
echo "✅ Lambda function updated successfully!"
echo ""
echo "If this is your first deployment, create the function with:"
echo "  aws lambda create-function \\"
echo "    --function-name ${LAMBDA_FUNCTION_NAME} \\"
echo "    --package-type Image \\"
echo "    --code ImageUri=${FULL_IMAGE} \\"
echo "    --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-execution-role \\"
echo "    --timeout 60 \\"
echo "    --memory-size 1024 \\"
echo "    --architectures arm64 \\"
echo "    --region ${AWS_REGION}"
echo ""
echo "Then create a Function URL:"
echo "  aws lambda create-function-url-config \\"
echo "    --function-name ${LAMBDA_FUNCTION_NAME} \\"
echo "    --auth-type NONE \\"
echo "    --region ${AWS_REGION}"

# Clean up copied models from build context
rm -rf "${LAMBDA_DIR}/models"
