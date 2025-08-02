import json
import logging
from token_store import TokenStore

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler for TikTok token API
    
    Supports:
    - GET /token/{open_id} - Get access token for specified open_id
    """
    
    try:
        http_method = event.get('httpMethod', '')
        path_parameters = event.get('pathParameters', {})
        
        if http_method == 'GET' and path_parameters:
            open_id = path_parameters.get('open_id')
            if not open_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Missing open_id parameter'
                    })
                }
            
            # Get access token (with automatic refresh if needed)
            access_token = TokenStore.get_access_token(open_id)
            
            if not access_token:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'No valid token found for open_id: {open_id}'
                    })
                }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'access_token': access_token,
                    'open_id': open_id
                })
            }
        
        # Handle unsupported methods or paths
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Method not allowed'
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }