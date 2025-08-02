import json
import logging
import requests
import time
from typing import Optional, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_access_token(open_id: str) -> Optional[str]:
    """Get access token from existing token API"""
    token_api_url = f"https://6kg6mdmiz6.execute-api.ap-northeast-1.amazonaws.com/prod/token/{open_id}"
    
    try:
        response = requests.get(token_api_url)
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting access token: {str(e)}")
        return None

def make_tiktok_api_request(endpoint: str, data: Dict[str, Any], access_token: str) -> Dict[str, Any]:
    """Make authenticated API request to TikTok"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    
    api_base_url = "https://open.tiktokapis.com"
    logger.info(f"Making API request to {api_base_url}{endpoint}")
    
    response = requests.post(f"{api_base_url}{endpoint}", headers=headers, json=data)
    
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    response_data = response.json()
    
    if response_data.get("error", {}).get("code") != "ok":
        error_msg = response_data.get("error", {}).get("message", "Unknown error")
        raise Exception(f"API error: {error_msg}")
    
    return response_data

def prepare_video_source(video_path: str) -> Dict[str, str]:
    """Prepare video source information for TikTok API"""
    return {"source": "PULL_FROM_URL", "video_url": video_path}

def post_video_to_tiktok(
    access_token: str,
    title: str,
    video_path: str,
    privacy_level: str = "PUBLIC_TO_EVERYONE",
    disable_duet: bool = False,
    disable_comment: bool = False,
    disable_stitch: bool = False,
    video_cover_timestamp_ms: Optional[int] = None
) -> str:
    """
    Post a video to TikTok following official API best practices
    
    Args:
        access_token: TikTok access token
        title: Video title/caption
        video_path: URL to video file
        privacy_level: Privacy setting
        disable_duet: Whether to disable duet feature
        disable_comment: Whether to disable comments
        disable_stitch: Whether to disable stitch feature
        video_cover_timestamp_ms: Timestamp for video cover
    
    Returns:
        str: publish_id for tracking the post status
    """
    
    video_info = prepare_video_source(video_path)
    
    post_info = {
        "title": title,
        "privacy_level": privacy_level,
        "disable_duet": disable_duet,
        "disable_comment": disable_comment,
        "disable_stitch": disable_stitch,
    }
    
    if video_cover_timestamp_ms is not None:
        post_info["video_cover_timestamp_ms"] = video_cover_timestamp_ms
    
    data = {
        "post_info": post_info,
        "source_info": video_info,
    }
    
    response_data = make_tiktok_api_request("/v2/post/publish/video/init/", data, access_token)
    
    return response_data["data"]["publish_id"]

def get_post_status(access_token: str, publish_id: str) -> Dict[str, Any]:
    """
    Check the status of a post using its publish_id
    
    Args:
        access_token: TikTok access token
        publish_id: The publish_id returned from post_video
    
    Returns:
        Dict containing post status information
    """
    data = {"publish_id": publish_id}
    
    response_data = make_tiktok_api_request("/v2/post/publish/status/fetch/", data, access_token)
    
    return response_data["data"]

def lambda_handler(event, context):
    """
    AWS Lambda handler for r2-to-tiktok-poster
    
    Expects POST request with JSON body containing:
    - r2_video_url: URL of video in R2
    - open_id: TikTok user's open_id
    - title: Video title/caption
    - privacy_level: Privacy setting (optional, defaults to PUBLIC_TO_EVERYONE)
    - disable_duet: Whether to disable duet (optional, defaults to False)
    - disable_comment: Whether to disable comments (optional, defaults to False)
    - disable_stitch: Whether to disable stitch (optional, defaults to False)
    - video_cover_timestamp_ms: Timestamp for video cover (optional)
    
    Returns:
    - publish_id: TikTok publish ID for tracking
    - status: Post status
    - success: boolean
    - error: error message if failed
    """
    
    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        r2_video_url = body.get('r2_video_url')
        open_id = body.get('open_id')
        title = body.get('title')
        
        if not r2_video_url or not open_id or not title:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'r2_video_url, open_id, and title are required'
                })
            }
        
        privacy_level = body.get('privacy_level', 'PUBLIC_TO_EVERYONE')
        disable_duet = body.get('disable_duet', False)
        disable_comment = body.get('disable_comment', False)
        disable_stitch = body.get('disable_stitch', False)
        video_cover_timestamp_ms = body.get('video_cover_timestamp_ms')
        
        logger.info(f"Posting video to TikTok for open_id: {open_id}")
        
        access_token = get_access_token(open_id)
        if not access_token:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Failed to get access token for the specified open_id'
                })
            }
        
        publish_id = post_video_to_tiktok(
            access_token=access_token,
            title=title,
            video_path=r2_video_url,
            privacy_level=privacy_level,
            disable_duet=disable_duet,
            disable_comment=disable_comment,
            disable_stitch=disable_stitch,
            video_cover_timestamp_ms=video_cover_timestamp_ms
        )
        
        logger.info(f"Video posted successfully with publish_id: {publish_id}")
        
        time.sleep(2)
        status = get_post_status(access_token, publish_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'publish_id': publish_id,
                'status': status.get('status'),
                'fail_reason': status.get('fail_reason'),
                'uploaded_at': status.get('uploaded_at')
            })
        }
        
    except Exception as e:
        logger.error(f"Error posting video to TikTok: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Failed to post video to TikTok: {str(e)}'
            })
        }
