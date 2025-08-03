#!/bin/bash

# This script creates a deployment package for AWS Lambda

set -e

echo "🚀 Building fal-to-r2-uploader Lambda deployment package..."

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

# Create zip file excluding unnecessary files
zip -r lambda-deployment.zip . \
  -x "tests/*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x ".git/*" \
  -x "build.sh" \
  -x "*.md"

echo "✅ Deployment package created: lambda-deployment.zip"
echo "📊 Package size: $(du -h lambda-deployment.zip | cut -f1)"

echo "🎉 Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Deploy using AWS CLI:"
echo "   aws lambda update-function-code --function-name fal-to-r2-uploader --zip-file fileb://lambda-deployment.zip"
echo ""
echo "2. Or use GitHub Actions by pushing to main branch"
