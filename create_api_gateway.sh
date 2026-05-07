#!/usr/bin/env bash
# Creates an HTTP API Gateway to expose the Lambda function publicly
# This is used as an alternative to Lambda Function URLs for regions that don't support them.

set -euo pipefail

REGION="${AWS_REGION:-ap-south-2}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID env var}"
FUNCTION_NAME="maternaguard-predict"

echo "1. Creating HTTP API..."
API_ID=$(aws apigatewayv2 create-api \
  --name maternaguard-api \
  --protocol-type HTTP \
  --region "${REGION}" \
  --cors-configuration 'AllowOrigins="*",AllowMethods="POST",AllowHeaders="Content-Type"' \
  --query 'ApiId' \
  --output text)

echo "API ID: ${API_ID}"

echo "2. Creating Lambda Integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "${API_ID}" \
  --integration-type AWS_PROXY \
  --integration-method POST \
  --integration-uri "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}" \
  --payload-format-version 2.0 \
  --region "${REGION}" \
  --query 'IntegrationId' \
  --output text)

echo "Integration ID: ${INTEGRATION_ID}"

echo "3. Creating Route..."
aws apigatewayv2 create-route \
  --api-id "${API_ID}" \
  --route-key "POST /predict" \
  --target "integrations/${INTEGRATION_ID}" \
  --region "${REGION}" > /dev/null

echo "4. Granting API Gateway permission to invoke Lambda..."
# We use || true in case the permission already exists
aws lambda add-permission \
  --function-name "${FUNCTION_NAME}" \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*/predict" \
  --region "${REGION}" > /dev/null 2>&1 || true

# API Gateway HTTP APIs have a default stage ($default) created automatically.
INVOKE_URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/predict"

echo ""
echo "✅ API Gateway created successfully!"
echo "Your public Lambda endpoint is:"
echo ""
echo "   ${INVOKE_URL}"
echo ""
echo "Please use this URL for your LAMBDA_PREDICT_URL environment variable in Render!"
