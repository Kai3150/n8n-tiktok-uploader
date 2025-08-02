import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lambda_function import lambda_handler, get_access_token, make_tiktok_api_request, query_creator_info, prepare_video_source


class TestR2ToTikTokPoster:
    
    @patch('lambda_function.get_access_token')
    @patch('lambda_function.make_tiktok_api_request')
    def test_lambda_handler_success(self, mock_make_api_request, mock_get_access_token):
        mock_get_access_token.return_value = 'test-access-token'
        
        mock_make_api_request.side_effect = [
            {'data': {'privacy_level_options': ['PUBLIC_TO_EVERYONE', 'SELF_ONLY']}},  # creator_info response
            {'data': {'publish_id': 'test-publish-id'}},  # post_video response
            {'data': {'status': 'PROCESSING_UPLOAD', 'uploaded_at': '2023-01-01T00:00:00Z'}}  # status response
        ]
        
        event = {
            'body': json.dumps({
                'r2_video_url': 'https://r2-endpoint.com/my-tiktok-videos/test.mp4',
                'open_id': 'test-open-id',
                'title': 'Test video title #test'
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['success'] is True
        assert response_body['publish_id'] == 'test-publish-id'
        assert response_body['status'] == 'PROCESSING_UPLOAD'
    
    def test_lambda_handler_missing_required_fields(self):
        event = {
            'body': json.dumps({
                'r2_video_url': 'https://r2-endpoint.com/test.mp4'
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert response_body['success'] is False
        assert 'r2_video_url, open_id, and title are required' in response_body['error']
    
    @patch('lambda_function.requests.get')
    def test_get_access_token_success(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'test-token'}
        mock_requests_get.return_value = mock_response
        
        token = get_access_token('test-open-id')
        
        assert token == 'test-token'
        mock_requests_get.assert_called_once_with(
            'https://6kg6mdmiz6.execute-api.ap-northeast-1.amazonaws.com/prod/token/test-open-id'
        )
    
    @patch('lambda_function.requests.post')
    def test_make_tiktok_api_request_success(self, mock_requests_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': {'code': 'ok'},
            'data': {'publish_id': 'test-id'}
        }
        mock_requests_post.return_value = mock_response
        
        result = make_tiktok_api_request('/test/endpoint', {'test': 'data'}, 'test-token')
        
        assert result['data']['publish_id'] == 'test-id'
        mock_requests_post.assert_called_once()
    
    @patch('lambda_function.make_tiktok_api_request')
    def test_query_creator_info_success(self, mock_make_api_request):
        mock_make_api_request.return_value = {
            'data': {
                'privacy_level_options': ['PUBLIC_TO_EVERYONE', 'SELF_ONLY'],
                'creator_username': 'test_user'
            }
        }
        
        result = query_creator_info('test-token')
        
        assert result['privacy_level_options'] == ['PUBLIC_TO_EVERYONE', 'SELF_ONLY']
        assert result['creator_username'] == 'test_user'
        mock_make_api_request.assert_called_once_with('/v2/post/publish/creator_info/query/', {}, 'test-token')
    
    def test_prepare_video_source_valid_url(self):
        result = prepare_video_source('https://example.com/video.mp4')
        
        assert result == {'source': 'PULL_FROM_URL', 'video_url': 'https://example.com/video.mp4'}
    
    def test_prepare_video_source_invalid_url(self):
        with pytest.raises(ValueError, match="Only URL sources are supported"):
            prepare_video_source('/local/path/video.mp4')
    
    @patch('lambda_function.get_access_token')
    @patch('lambda_function.make_tiktok_api_request')
    def test_lambda_handler_invalid_privacy_level(self, mock_make_api_request, mock_get_access_token):
        mock_get_access_token.return_value = 'test-access-token'
        
        mock_make_api_request.side_effect = [
            {'data': {'privacy_level_options': ['PUBLIC_TO_EVERYONE', 'SELF_ONLY']}},  # creator_info response
        ]
        
        event = {
            'body': json.dumps({
                'r2_video_url': 'https://r2-endpoint.com/my-tiktok-videos/test.mp4',
                'open_id': 'test-open-id',
                'title': 'Test video title #test',
                'privacy_level': 'INVALID_LEVEL'
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert response_body['success'] is False
        assert 'Privacy level' in response_body['error']
        assert 'not available' in response_body['error']
    
    @patch('lambda_function.get_access_token')
    def test_lambda_handler_invalid_video_url(self, mock_get_access_token):
        mock_get_access_token.return_value = 'test-access-token'
        
        event = {
            'body': json.dumps({
                'r2_video_url': '/local/path/video.mp4',
                'open_id': 'test-open-id',
                'title': 'Test video title #test'
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert response_body['success'] is False
        assert 'Only URL sources are supported' in response_body['error']


if __name__ == '__main__':
    pytest.main([__file__])
