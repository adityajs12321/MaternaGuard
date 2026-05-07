# AWS Lambda container image for MaternaGuard ML inference
# Build native arm64 for Apple Silicon compatibility
FROM public.ecr.aws/lambda/python:3.12

# Upgrade pip first to get better wheel resolution
RUN pip install --upgrade pip

# Install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy model artifacts
COPY models/ /opt/ml/models/

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

# Set the handler
CMD ["lambda_function.lambda_handler"]
