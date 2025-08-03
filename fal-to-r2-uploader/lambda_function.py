import json
import logging
import boto3
import requests
from botocore.exceptions import ClientError
import uuid
from urllib.parse import urlparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_r2_credentials():
    """Retrieve R2 credentials from AWS Secrets Manager"""
    secrets_client = boto3.client('secretsmanager', region_name='ap-northeast-1')
    
    try:
        endpoint_response = secrets_client.get_secret_value(SecretId='r2_endpoint_url')
        access_key_response = secrets_client.get_secret_value(SecretId='r2_access_key_id')
        secret_key_response = secrets_client.get_secret_value(SecretId='r2_secret_access_key')
        
        return {
            'endpoint_url': endpoint_response['SecretString'],
            'access_key_id': access_key_response['SecretString'],
            'secret_access_key': secret_key_response['SecretString']
        }
    except ClientError as e:
        logger.error(f"Failed to retrieve R2 credentials: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    AWS Lambda handler for fal-to-r2-uploader
    
    Expects POST request with JSON body containing:
    - video_url: URL from fal.ai
    
    Returns:
    - r2_url: URL of uploaded video in R2
    - success: boolean
    - error: error message if failed
    """
    
    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        video_url = body.get('video_url')
        if not video_url:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'video_url is required'
                })
            }
        
        logger.info(f"Processing video upload from URL: {video_url}")
        
        r2_credentials = get_r2_credentials()
        
        s3_client = boto3.client(
            's3',
            endpoint_url=r2_credentials['endpoint_url'],
            aws_access_key_id=r2_credentials['access_key_id'],
            aws_secret_access_key=r2_credentials['secret_access_key'],
            region_name='auto'
        )
        
        parsed_url = urlparse(video_url)
        file_extension = parsed_url.path.split('.')[-1] if '.' in parsed_url.path else 'mp4'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        logger.info(f"Downloading video from {video_url}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        content_length = response.headers.get('content-length')
        if content_length:
            logger.info(f"Video size: {content_length} bytes")
        
        logger.info(f"Uploading to R2 bucket: my-tiktok-videos/{unique_filename}")
        s3_client.upload_fileobj(
            response.raw,
            'my-tiktok-videos',
            unique_filename,
            ExtraArgs={
                'ContentType': 'video/mp4',
                'ACL': 'public-read'
            }
        )
        
        r2_url = f"{r2_credentials['endpoint_url']}/my-tiktok-videos/{unique_filename}"
        
        logger.info(f"Successfully uploaded video to R2: {r2_url}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'r2_url': r2_url,
                'filename': unique_filename
            })
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to download video: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Failed to download video: {str(e)}'
            })
        }
        
    except ClientError as e:
        logger.error(f"AWS S3/R2 error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Failed to upload to R2: {str(e)}'
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }
