import sys
import os
# 相対パスで dependencies ディレクトリを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dependencies'))

import json
import logging
import boto3
import requests
import uuid
from urllib.parse import urlparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_r2_credentials():
    """Retrieve R2 credentials from environment variables"""
    try:
        return {
            'endpoint_url': os.environ['R2_ENDPOINT_URL'],
            'access_key_id': os.environ['R2_ACCESS_KEY_ID'],
            'secret_access_key': os.environ['R2_SECRET_ACCESS_KEY']
        }
    except KeyError as e:
        logger.error(f"Missing required environment variable: {str(e)}")
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

    except Exception as s3_error:
        logger.error(f"AWS S3/R2 error: {str(s3_error)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Failed to upload to R2: {str(s3_error)}'
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
