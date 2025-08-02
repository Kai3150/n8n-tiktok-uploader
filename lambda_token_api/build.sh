#!/bin/bash

# Build script for TikTok Lambda Token API
# This script creates a deployment package for AWS Lambda

set -e

echo "🚀 Building TikTok Lambda Token API deployment package..."

# Clean up previous builds
echo "🧹 Cleaning up previous builds..."
rm -rf dependencies/
rm -f lambda-deployment.zip

# Create dependencies directory
echo "📦 Installing dependencies..."
mkdir -p dependencies
pip install -r requirements.txt -t dependencies/

# Create deployment package
echo "📁 Creating deployment package..."
# Copy source files to root for Lambda
cp -r src/* .

# Create zip file excluding unnecessary files
zip -r lambda-deployment.zip . \
  -x "src/*" \
  -x "tests/*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x ".git/*" \
  -x "build.sh" \
  -x "*.md"

echo "✅ Deployment package created: lambda-deployment.zip"
echo "📊 Package size: $(du -h lambda-deployment.zip | cut -f1)"

# Cleanup temporary files
echo "🧹 Cleaning up temporary files..."
rm -f lambda_function.py token_store.py __init__.py

echo "🎉 Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Deploy using AWS CLI:"
echo "   aws lambda update-function-code --function-name tiktok-token-api --zip-file fileb://lambda-deployment.zip"
echo ""
echo "2. Or use GitHub Actions by pushing to main branch"