import sys
import os
# 相対パスで dependencies ディレクトリを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dependencies'))

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
    - GET /accounts - Get list of all open_ids
    - GET /accounts/full - Get all token data (full JSON)
    """

    try:
        http_method = event.get('httpMethod', '')
        path_parameters = event.get('pathParameters', {})
        path = event.get('resource', '')

        if http_method == 'GET' and path == '/accounts':
            # GET /accounts - Return list of all open_ids
            accounts = TokenStore.list_accounts()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'accounts': accounts,
                    'total': len(accounts)
                })
            }

        elif http_method == 'GET' and path == '/accounts/full':
            # GET /accounts/full - Return all token data (full JSON)
            raw_tokens = TokenStore._load_raw_tokens()
            if not raw_tokens:
                raw_tokens = {}

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'tokens': raw_tokens,
                    'total': len(raw_tokens)
                })
            }

        elif http_method == 'GET' and path_parameters and path_parameters.get('open_id'):
            # GET /token/{open_id} - Get access token for specified open_id
            open_id = path_parameters.get('open_id')

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
